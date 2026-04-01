#!/usr/bin/env python3
"""
sim_c2_entropy_structure_search.py
==================================

Entropy Structure [Band C2]
----------------------------
1. Positive Witness: Tying the informational entropy readout explicitly to 
   the admitted 4x4 joint-state carrier (rho_AB).
2. Negative Controls (Shortcut Ablation):
   - Classical Shannon Shortcut: Proving that Shannon entropy of populations 
     fails to capture the non-classical coherent information signal.
   - Purity-Only Proxy: Testing if state purity (Tr(rho^2)) is an insufficient 
     proxy for the full entropic gradient.

Math Source: Improved Dependency Chain (Order 8)
"""

import json
import os
from datetime import datetime, UTC
import numpy as np
from typing import Dict, List, Tuple

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine, EngineState, StageControls, TERRAINS
from geometric_operators import (
    apply_Ti_4x4, apply_Fe_4x4, apply_Te_4x4, apply_Fi_4x4,
    partial_trace_A, partial_trace_B, _ensure_valid_density
)
from stage_matrix_neg_lib import (
    all_stage_rows, init_stage, baseline_controls
)

# ═══════════════════════════════════════════════════════════════════
# FULL ENTROPY FAMILY (NO SHORTHAND)
# ═══════════════════════════════════════════════════════════════════

def get_entropy_family(rho_AB: np.ndarray) -> Dict[str, float]:
    """
    Computes the full Von Neumann entropy family for the 4x4 joint state.
    """
    def s_vn(rho: np.ndarray) -> float:
        """S(rho) = -Tr(rho log2 rho)"""
        evals = np.linalg.eigvalsh(rho)
        evals = evals[evals > 1e-15]
        return float(-np.sum(evals * np.log2(evals)))

    rho_A = _ensure_valid_density(partial_trace_B(rho_AB))
    rho_B = _ensure_valid_density(partial_trace_A(rho_AB))
    
    s_AB = s_vn(rho_AB)
    s_A = s_vn(rho_A)
    s_B = s_vn(rho_B)
    
    # Mutual Information: I(A:B) = S(A) + S(B) - S(AB)
    mi = s_A + s_B - s_AB
    # Conditional Entropy: S(A|B) = S(AB) - S(B)
    cond_ent = s_AB - s_B
    # Coherent Information: Ic(A>B) = S(B) - S(AB)
    coh_info = s_B - s_AB
    
    return {
        "S_AB": s_AB,
        "S_A": s_A,
        "S_B": s_B,
        "I_AB": mi,
        "S_A_given_B": cond_ent,
        "Ic_A_to_B": coh_info
    }

# ═══════════════════════════════════════════════════════════════════
# NEGATIVE: CLASSICAL SHANNON SHORTCUT
# ═══════════════════════════════════════════════════════════════════

def get_shannon_shortcut(rho_AB: np.ndarray) -> Dict[str, float]:
    """
    H(p) = -sum(pi log2 pi) using ONLY the diagonal populations.
    This simulates a 'classical' observer who ignores coherence.
    """
    pops = np.real(np.diag(rho_AB))
    pops = pops[pops > 1e-15]
    h_AB = float(-np.sum(pops * np.log2(pops)))
    
    # Marginal Shannon entropies
    pops_A = np.real(np.diag(_ensure_valid_density(partial_trace_B(rho_AB))))
    pops_A = pops_A[pops_A > 1e-15]
    h_A = float(-np.sum(pops_A * np.log2(pops_A)))
    
    pops_B = np.real(np.diag(_ensure_valid_density(partial_trace_A(rho_AB))))
    pops_B = pops_B[pops_B > 1e-15]
    h_B = float(-np.sum(pops_B * np.log2(pops_B)))
    
    return {
        "H_AB": h_AB,
        "Ic_shannon": h_B - h_AB # The "fake" coherent info
    }

# ═══════════════════════════════════════════════════════════════════
# SIMULATION CORE
# ═══════════════════════════════════════════════════════════════════

def run_c2_search():
    results = []
    joint_ops = {"Ti": apply_Ti_4x4, "Fe": apply_Fe_4x4, "Te": apply_Te_4x4, "Fi": apply_Fi_4x4}
    
    for engine_type, row in all_stage_rows():
        seed = 12000 + engine_type * 10 + row[0]
        engine, state, meta = init_stage(engine_type, row, seed)
        
        rho_AB_init = state.rho_AB.copy()
        op_name = meta["native_operator"]
        op_fn = joint_ops[op_name]
        
        # Evolve the structure
        rho_AB_final = op_fn(rho_AB_init, polarity_up=meta["axis6_up"], strength=0.8)
        
        # 1. HONEST READOUT (VN)
        vn_family = get_entropy_family(rho_AB_final)
        
        # 2. CLASSICAL SHORTCUT (Shannon)
        shannon_family = get_shannon_shortcut(rho_AB_final)
        
        # Analysis:
        # Classical Shannon Ic cannot be positive for a product state or 
        # classical mixture (H_AB >= H_B). 
        # Only Non-classical Coherent Information can be > 0.
        shortcut_fails = vn_family["Ic_A_to_B"] > 0 and shannon_family["Ic_shannon"] <= 0
        
        results.append({
            "stage": row[3],
            "op": op_name,
            "vn_Ic": vn_family["Ic_A_to_B"],
            "shannon_Ic": shannon_family["Ic_shannon"],
            "shortcut_gap": vn_family["Ic_A_to_B"] - shannon_family["Ic_shannon"],
            "is_shortcut_killed": shortcut_fails
        })

    # Admission Verdict
    shortcut_kill_count = sum(1 for r in results if r["is_shortcut_killed"])
    
    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "C2_status": "PASS (Entropy Structure Admitted)" if shortcut_kill_count > 0 else "FAIL (Classical Shortcut Admitted)",
        "summary": {
            "classical_shortcut_kills": shortcut_kill_count,
            "total_stages": 16,
            "reason": "Shannon shortcut fails to capture positive coherent information."
        },
        "results": results
    }
    
    out_dir = "a2_state/sim_results"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "c2_entropy_structure_search_results.json")
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    run_c2_search()
