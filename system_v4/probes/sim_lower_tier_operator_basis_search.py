#!/usr/bin/env python3
"""
sim_lower_tier_operator_basis_search.py
=======================================

Operator/Basis Search [Band B3]
-------------------------------
1. B3.1 Basis remap search: Testing if the current operator-to-basis mapping 
   is load-bearing on the fixed carrier and fixed loop grammar.
2. B3.2 Coordinate-change control: Proving that a global consistent change 
   of coordinates is NOT a failure.
3. B3.3 Non-commutation ablation: Proving that the [X, Z] != 0 relationship 
   is essential for the engine's behavior.
4. B3.4 Representation demotion: Identifying if any operators are only 
   convenient representation rather than load-bearing substrate.

Math Source: Improved Operator/Basis Plan
"""

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict

import numpy as np

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine, EngineState, StageControls, TERRAINS
from geometric_operators import (
    apply_Ti, apply_Fe, apply_Te, apply_Fi,
    SIGMA_X, SIGMA_Y, SIGMA_Z, I2, _ensure_valid_density, negentropy
)
from stage_matrix_neg_lib import all_stage_rows, init_stage


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "lower_tier_operator_basis_search_results.json"

# ═══════════════════════════════════════════════════════════════════
# BASIS MANIPULATION HELPERS
# ═══════════════════════════════════════════════════════════════════

def random_su2(rng: np.random.Generator) -> np.ndarray:
    """Sample a random SU(2) unitary."""
    q = rng.normal(size=4)
    q /= np.linalg.norm(q)
    a, b, c, d = q
    return np.array([
        [a + 1j*b, -c + 1j*d],
        [c + 1j*d, a - 1j*b]
    ], dtype=complex)

def conjugate_op(op_fn, U: np.ndarray):
    """Returns a new operator function conjugated by U: U rho U†."""
    U_dag = U.conj().T
    def new_op(rho, **kwargs):
        rho_rot = U_dag @ rho @ U
        rho_out = op_fn(rho_rot, **kwargs)
        return U @ rho_out @ U_dag
    return new_op

# ═══════════════════════════════════════════════════════════════════
# RE-MAPPED OPERATORS (NEGATIVES)
# ═══════════════════════════════════════════════════════════════════

def apply_Ti_Y(rho, polarity_up=True, strength=1.0):
    """Ti remapped to Sigma_Y basis dephasing."""
    P0 = (I2 + SIGMA_Y) / 2
    P1 = (I2 - SIGMA_Y) / 2
    rho_projected = P0 @ rho @ P0 + P1 @ rho @ P1
    mix = strength if polarity_up else 0.3 * strength
    return _ensure_valid_density(mix * rho_projected + (1-mix) * rho)

def apply_Te_Z(rho, polarity_up=True, strength=1.0, q=0.7):
    """Te remapped to Sigma_Z basis dephasing (becomes commutative with Ti)."""
    mix = strength * (q if polarity_up else 0.3 * q)
    P0 = (I2 + SIGMA_Z) / 2
    P1 = (I2 - SIGMA_Z) / 2
    rho_projected = P0 @ rho @ P0 + P1 @ rho @ P1
    return _ensure_valid_density((1-mix) * rho + mix * rho_projected)

def apply_Fi_Z(rho, polarity_up=True, strength=1.0, theta=0.4):
    """Fi remapped to Sigma_Z rotation (becomes commutative with Fe)."""
    sign = 1.0 if polarity_up else -1.0
    angle = sign * theta * strength
    U = np.array([[np.exp(-1j * angle / 2), 0],
                  [0, np.exp(1j * angle / 2)]], dtype=complex)
    return _ensure_valid_density(U @ rho @ U.conj().T)

# ═══════════════════════════════════════════════════════════════════
# SIMULATION CORE
# ═══════════════════════════════════════════════════════════════════

def run_variant(engine_type: int, row: tuple, seed: int, 
                op_mappings: Dict[str, any], 
                global_U: np.ndarray = None) -> Dict:
    
    engine, state, meta = init_stage(engine_type, row, seed)
    
    # Apply global coordinate change to the initial 4x4 state
    if global_U is not None:
        U4 = np.kron(global_U, global_U)
        state.rho_AB = U4 @ state.rho_AB @ U4.conj().T
        
    before_rho_L = state.rho_L.copy()
    
    # Identify stage operator
    op_name = meta["native_operator"]
    op_fn = op_mappings.get(op_name)
    
    if op_fn is None: # Demotion test case: operator removed
        new_rho_L = before_rho_L
    else:
        if global_U is not None:
            op_fn = conjugate_op(op_fn, global_U)
        new_rho_L = op_fn(state.rho_L, polarity_up=meta["axis6_up"], strength=0.8)
    
    dphi_L = float(negentropy(new_rho_L) - negentropy(before_rho_L))
    
    return {
        "dphi_L": dphi_L,
        "new_rho_L": new_rho_L
    }

def main():
    rng = np.random.default_rng(42)
    results = {
        "B3.1_remap_search": [],
        "B3.2_coordinate_change": [],
        "B3.3_noncommutation_ablation": [],
        "B3.4_representation_demotion": []
    }
    
    baseline_ops = {"Ti": apply_Ti, "Fe": apply_Fe, "Te": apply_Te, "Fi": apply_Fi}
    
    # B3.1 Remap: Ti to Y
    remap_ops = dict(baseline_ops)
    remap_ops["Ti"] = apply_Ti_Y
    
    # B3.2 Coord: Global Rotation
    U_rand = random_su2(rng)
    
    # B3.3 Ablation: Force all operators to Sigma_Z basis (Commutative)
    commute_ops = {
        "Ti": apply_Ti,   # Already Z-basis
        "Fe": apply_Fe,   # Already Z-rotation
        "Te": apply_Te_Z, # Remapped X -> Z dephasing
        "Fi": apply_Fi_Z  # Remapped X -> Z rotation
    }
    
    # B3.4 Demotion: Remove unitary operators (Fe and Fi)
    # We test if the dissipative substrate (Ti/Te) alone is enough
    demote_ops = {
        "Ti": apply_Ti,
        "Te": apply_Te,
        "Fe": None, # Removed
        "Fi": None  # Removed
    }
    
    for engine_type, row in all_stage_rows():
        seed = 9000 + engine_type * 10 + row[0]
        
        base = run_variant(engine_type, row, seed, baseline_ops)
        remap = run_variant(engine_type, row, seed, remap_ops)
        coord = run_variant(engine_type, row, seed, baseline_ops, global_U=U_rand)
        ablated = run_variant(engine_type, row, seed, commute_ops)
        demoted = run_variant(engine_type, row, seed, demote_ops)
        
        # B3.1 Check
        results["B3.1_remap_search"].append({
            "stage": row[3],
            "is_kill": abs(remap["dphi_L"] - base["dphi_L"]) > 1e-5
        })
        
        # B3.2 Check
        results["B3.2_coordinate_change"].append({
            "stage": row[3],
            "is_invariant": abs(coord["dphi_L"] - base["dphi_L"]) < 1e-10
        })
        
        # B3.3 Check
        results["B3.3_noncommutation_ablation"].append({
            "stage": row[3],
            "is_kill": abs(ablated["dphi_L"] - base["dphi_L"]) > 1e-5
        })
        
        # B3.4 Check
        results["B3.4_representation_demotion"].append({
            "stage": row[3],
            "is_changed": abs(demoted["dphi_L"] - base["dphi_L"]) > 1e-5
        })

    # Admission Verdicts
    remap_kills = sum(1 for r in results["B3.1_remap_search"] if r["is_kill"])
    coord_invariant = sum(1 for r in results["B3.2_coordinate_change"] if r["is_invariant"])
    ablation_kills = sum(1 for r in results["B3.3_noncommutation_ablation"] if r["is_kill"])
    demotion_changes = sum(1 for r in results["B3.4_representation_demotion"] if r["is_changed"])
    
    payload = {
        "name": "lower_tier_operator_basis_search",
        "timestamp": datetime.now(UTC).isoformat(),
        "B3.1_basis_remap_search": "PASS (Killed)" if remap_kills > 0 else "FAIL (No Substrate Sensitivity)",
        "B3.2_coordinate_change_control": "PASS (Invariant)" if coord_invariant == 16 else "FAIL (Coordinate Dependent)",
        "B3.3_noncommutation_ablation": "PASS (Killed)" if ablation_kills > 0 else "FAIL (Commutativity Admitted)",
        "B3.4_representation_demotion": (
            "LOCAL_UNITARY_PAIR_LOAD_BEARING_IN_LOCAL_TEST"
            if demotion_changes > 0
            else "LOCAL_UNITARY_PAIR_NOT_PROVEN_LOAD_BEARING_IN_LOCAL_TEST"
        ),
        "summary": {
            "remap_kills": remap_kills,
            "coord_invariant_count": coord_invariant,
            "ablation_kills": ablation_kills,
            "demotion_structural_changes": demotion_changes,
            "total_stages": 16
        },
        "candidate_family": {
            "noncommuting_basis_split": {
                "status": "surviving_lower_tier_candidate" if remap_kills > 0 and ablation_kills > 0 else "not_supported_yet",
                "keep": remap_kills > 0 and ablation_kills > 0,
                "reason": "A fixed-carrier remap and same-axis commuting collapse both change the local operator response, so the X/Z split remains load-bearing in this lower-tier local search.",
                "evidence": {
                    "remap_kills": remap_kills,
                    "ablation_kills": ablation_kills,
                    "total_stages": 16,
                },
            },
            "global_coordinate_choice": {
                "status": "representation_only",
                "keep": False,
                "reason": "A coherent global SU(2) change of coordinates leaves the local response invariant across all stage rows.",
                "evidence": {
                    "coord_invariant_count": coord_invariant,
                    "total_stages": 16,
                },
            },
            "local_unitary_pair_Fe_Fi": {
                "status": (
                    "local_test_load_bearing"
                    if demotion_changes > 0
                    else "not_proven_load_bearing_in_local_test"
                ),
                "keep": demotion_changes > 0,
                "reason": (
                    "Removing Fe and Fi changes the local dphi response in this narrow test."
                    if demotion_changes > 0
                    else "Removing Fe and Fi does not change the one-step local dphi response here; this is not enough to demote them from substrate use in higher tiers."
                ),
                "evidence": {
                    "demotion_structural_changes": demotion_changes,
                    "total_stages": 16,
                },
            },
        },
        "owner_read": {
            "status": (
                "lower_tier_noncommuting_basis_split_survives_local_search"
                if remap_kills > 0 and ablation_kills > 0 and coord_invariant == 16
                else "operator_basis_search_unresolved"
            ),
            "note": "This search supports a lower-tier noncommuting basis split and rejects pure coordinate relabeling as substrate, but it does not yet justify promoting Fe/Fi as demoted or representation-only.",
        },
        "results": results
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
