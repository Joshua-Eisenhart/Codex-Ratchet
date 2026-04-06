#!/usr/bin/env python3
"""
sim_c1_entanglement_object_search.py
====================================

Entanglement-Capable Structure [Band C1]
-----------------------------------------
1. Positive Witness: Identifying the first clean nonclassical binding objects 
   that survive on the admitted substrate (Hopf/Weyl + Pauli basis).
2. Negative Controls: 
   - Fake Coupling: Attempting to generate Axis 0 signals using classical correlations.
   - LOCC Ablation: Proving that Local Operations and Classical Communication 
     cannot reproduce the joint state entropy structure.
   - Mispair Controls: Testing if the wrong entanglement pairing (e.g. cross-torus) 
     collapses the signal.

Math Source: Improved Dependency Chain (Order 7)
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
    SIGMA_X, SIGMA_Y, SIGMA_Z, I2, _ensure_valid_density, negentropy
)
from stage_matrix_neg_lib import (
    all_stage_rows, init_stage, baseline_controls, axes_delta
)

# ═══════════════════════════════════════════════════════════════════
# ENTANGLEMENT OBJECT DEFINITIONS (C1 CANDIDATES)
# ═══════════════════════════════════════════════════════════════════

def get_concurrence(rho: np.ndarray) -> float:
    """
    Wootters concurrence for a 4x4 two-qubit density matrix.
    C(rho) = max(0, lambda1 - lambda2 - lambda3 - lambda4)
    where lambda_i are the square roots of eigenvalues of R = rho * rho_tilde,
    sorted in decreasing order.
    rho_tilde = (sigma_y x sigma_y) rho* (sigma_y x sigma_y)
    C = 0 iff rho is separable (exact for 2-qubit systems).
    """
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sysy = np.kron(sy, sy)
    rho_tilde = sysy @ rho.conj() @ sysy
    R = rho @ rho_tilde
    # eigenvalues of R — may be slightly negative due to numerics, clip to 0
    evals = np.linalg.eigvals(R)
    evals_sqrt = np.sqrt(np.maximum(evals.real, 0.0))
    evals_sqrt = np.sort(evals_sqrt)[::-1]
    c = float(np.maximum(0.0, evals_sqrt[0] - evals_sqrt[1] - evals_sqrt[2] - evals_sqrt[3]))
    return c


def get_negativity(rho: np.ndarray) -> float:
    """
    Negativity via partial transpose on subsystem B.
    N(rho) = (||rho^{T_B}||_1 - 1) / 2 = sum of |negative eigenvalues| of rho^{T_B}.
    N > 0 iff rho is entangled (exact for 2-qubit systems via PPT criterion).
    """
    # Partial transpose on B: reshape to (i_A, i_B, j_A, j_B), transpose i_B <-> j_B
    rho_pt = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    evals = np.linalg.eigvalsh(rho_pt)
    neg_evals = evals[evals < 0]
    return float(-np.sum(neg_evals))


def get_mutual_information(rho_AB: np.ndarray) -> float:
    """I(A:B) = S(rho_A) + S(rho_B) - S(rho_AB)"""
    from geometric_operators import partial_trace_A, partial_trace_B
    from hopf_manifold import von_neumann_entropy_2x2
    
    rho_A = _ensure_valid_density(partial_trace_B(rho_AB))
    rho_B = _ensure_valid_density(partial_trace_A(rho_AB))
    
    # S(rho) = -Tr(rho log2 rho)
    def s_vn(rho):
        evals = np.linalg.eigvalsh(rho)
        evals = evals[evals > 1e-15]
        return -np.sum(evals * np.log2(evals))
    
    # S(rho_AB) for 4x4
    evals_AB = np.linalg.eigvalsh(rho_AB)
    evals_AB = evals_AB[evals_AB > 1e-15]
    s_AB = -np.sum(evals_AB * np.log2(evals_AB))
    
    return float(s_vn(rho_A) + s_vn(rho_B) - s_AB)

# ═══════════════════════════════════════════════════════════════════
# NEGATIVE: FAKE COUPLING CONTROL
# ═══════════════════════════════════════════════════════════════════

def apply_fake_coupling_step(op_fn_joint, meta: Dict) -> np.ndarray:
    """
    Fake coupling control: replace the quantum initial state with a maximally
    classically correlated separable state (diagonal in the computational basis,
    no quantum coherence), then apply the same joint 4x4 operator.

    Control state: rho_cc = 0.5*|00><00| + 0.5*|11><11|
    This is separable (no entanglement), but maximally classically correlated.
    Killing criterion: mi_fake < 1e-5 — if classical correlations + the joint
    operator were sufficient to generate MI, this control would NOT be killed.
    """
    rho_cc = np.zeros((4, 4), dtype=complex)
    rho_cc[0, 0] = 0.5  # |00>
    rho_cc[3, 3] = 0.5  # |11>
    rho_cc = _ensure_valid_density(rho_cc)
    return op_fn_joint(rho_cc, polarity_up=meta["axis6_up"], strength=0.8)


# ═══════════════════════════════════════════════════════════════════
# NEGATIVE: MISPAIR CONTROL
# ═══════════════════════════════════════════════════════════════════

def build_mispair_state(rho_L_current: np.ndarray, engine_type_other: int,
                        row: tuple, seed_other: int) -> np.ndarray:
    """
    Mispair control: cross-pair rho_L from the current stage with rho_R from the
    chirality-inverted engine type (Type1 <-> Type2) at the same row geometry.
    This violates the structural L/R Weyl pairing that the carrier requires.

    Killing criterion: mi_mispair < 1e-5 — if the wrong pairing still produced
    the entanglement signal, the pairing structure would not be load-bearing.
    """
    from stage_matrix_neg_lib import init_stage as _init_stage
    _, state_other, _ = _init_stage(engine_type_other, row, seed_other)
    rho_R_wrong = state_other.rho_R
    return _ensure_valid_density(np.kron(rho_L_current, rho_R_wrong))


# ═══════════════════════════════════════════════════════════════════
# NEGATIVE: LOCC-ONLY EVOLUTION
# ═══════════════════════════════════════════════════════════════════

def apply_locc_step(rho_AB: np.ndarray, op_name: str, meta: Dict) -> np.ndarray:
    """
    Simulates LOCC (Local Operations + Classical Communication).
    The operators act on L and R independently. 
    NO joint interaction (XX, ZZ, etc.) is allowed.
    """
    from geometric_operators import partial_trace_A, partial_trace_B, OPERATOR_MAP
    
    rho_L = _ensure_valid_density(partial_trace_B(rho_AB))
    rho_R = _ensure_valid_density(partial_trace_A(rho_AB))
    
    op_fn = OPERATOR_MAP[op_name]
    
    # Local application only
    new_rho_L = op_fn(rho_L, polarity_up=meta["axis6_up"], strength=0.8)
    new_rho_R = op_fn(rho_R, polarity_up=meta["axis6_up"], strength=0.8)
    
    # Classical recombination (Product State)
    return np.kron(new_rho_L, new_rho_R)

# ═══════════════════════════════════════════════════════════════════
# SIMULATION CORE
# ═══════════════════════════════════════════════════════════════════

def run_c1_search():
    results = []
    
    # Interaction Map for Admitted Substrate (from Tier 7)
    joint_ops = {
        "Ti": apply_Ti_4x4, # ZZ dephasing
        "Fe": apply_Fe_4x4, # XX rotation
        "Te": apply_Te_4x4, # YY dephasing
        "Fi": apply_Fi_4x4  # XZ rotation
    }
    
    for engine_type, row in all_stage_rows():
        seed = 11000 + engine_type * 10 + row[0]
        engine, state, meta = init_stage(engine_type, row, seed)

        # Start from pure product state (honest initialization)
        rho_AB_init = state.rho_AB.copy()

        # 1. POSITIVE WITNESS: Joint 4x4 Evolution
        op_name = meta["native_operator"]
        op_fn_joint = joint_ops[op_name]
        rho_AB_joint = op_fn_joint(rho_AB_init, polarity_up=meta["axis6_up"], strength=0.8)

        mi_joint = get_mutual_information(rho_AB_joint)
        concurrence_joint = get_concurrence(rho_AB_joint)
        negativity_joint = get_negativity(rho_AB_joint)

        # 2. NEGATIVE: LOCC-ONLY
        rho_AB_locc = apply_locc_step(rho_AB_init, op_name, meta)
        mi_locc = get_mutual_information(rho_AB_locc)

        # Check: Does LOCC collapse the entanglement signal?
        # mi_locc should be ~0 because local ops on a product state
        # cannot generate Mutual Information (LOCC Theorem).

        # 3. NEGATIVE: FAKE COUPLING CONTROL
        # Replace quantum initial state with maximally classically correlated
        # separable state (0.5|00><00| + 0.5|11><11|). Should not generate MI.
        rho_AB_fake = apply_fake_coupling_step(op_fn_joint, meta)
        mi_fake = get_mutual_information(rho_AB_fake)
        fake_coupling_killed = mi_fake < 1e-5
        concurrence_fake = get_concurrence(rho_AB_fake)
        negativity_fake = get_negativity(rho_AB_fake)
        fake_coupling_concurrence_killed = concurrence_fake < 1e-5
        fake_coupling_negativity_killed = negativity_fake < 1e-5

        # 4. NEGATIVE: MISPAIR CONTROL
        # Cross-pair rho_L from current chirality with rho_R from the
        # opposite engine type (Type1<->Type2). Structural pairing is wrong.
        other_engine_type = 3 - engine_type  # 1->2, 2->1
        seed_mispair = 21000 + engine_type * 10 + row[0]
        rho_AB_mispair = build_mispair_state(state.rho_L, other_engine_type, row, seed_mispair)
        rho_AB_mispair_evolved = op_fn_joint(rho_AB_mispair, polarity_up=meta["axis6_up"], strength=0.8)
        mi_mispair = get_mutual_information(rho_AB_mispair_evolved)
        mispair_killed = mi_mispair < 1e-5
        concurrence_mispair = get_concurrence(rho_AB_mispair_evolved)
        negativity_mispair = get_negativity(rho_AB_mispair_evolved)
        mispair_concurrence_killed = concurrence_mispair < 1e-5
        mispair_negativity_killed = negativity_mispair < 1e-5

        results.append({
            "stage": row[3],
            "op": op_name,
            "mi_joint": mi_joint,
            "mi_locc": mi_locc,
            "gap": mi_joint - mi_locc,
            "is_witnessed": mi_joint > 1e-5 and mi_locc < 1e-10,
            "mi_fake_coupling": mi_fake,
            "fake_coupling_killed": fake_coupling_killed,
            "mi_mispair": mi_mispair,
            "mispair_killed": mispair_killed,
            "concurrence_joint": concurrence_joint,
            "negativity_joint": negativity_joint,
            "concurrence_fake": concurrence_fake,
            "negativity_fake": negativity_fake,
            "fake_coupling_concurrence_killed": fake_coupling_concurrence_killed,
            "fake_coupling_negativity_killed": fake_coupling_negativity_killed,
            "concurrence_mispair": concurrence_mispair,
            "negativity_mispair": negativity_mispair,
            "mispair_concurrence_killed": mispair_concurrence_killed,
            "mispair_negativity_killed": mispair_negativity_killed,
        })

    # Admission Verdict
    witnessed_count = sum(1 for r in results if r["is_witnessed"])
    fake_coupling_kills = sum(1 for r in results if r["fake_coupling_killed"])
    mispair_kills = sum(1 for r in results if r["mispair_killed"])
    fake_coupling_concurrence_kills = sum(1 for r in results if r["fake_coupling_concurrence_killed"])
    fake_coupling_negativity_kills = sum(1 for r in results if r["fake_coupling_negativity_killed"])
    mispair_concurrence_kills = sum(1 for r in results if r["mispair_concurrence_killed"])
    mispair_negativity_kills = sum(1 for r in results if r["mispair_negativity_killed"])
    total = len(results)

    negatives_clean = (fake_coupling_kills == total and mispair_kills == total)
    quantum_specific = (fake_coupling_concurrence_kills == total or fake_coupling_negativity_kills == total)
    if witnessed_count > 0 and negatives_clean and quantum_specific:
        c1_status = "PASS — entanglement witnessed, all negative controls killed, quantum-specific confirmed"
    elif witnessed_count > 0 and negatives_clean:
        c1_status = "PARTIAL — entanglement witnessed and MI controls killed, but quantum-specificity not confirmed"
    elif witnessed_count > 0:
        c1_status = "PARTIAL — entanglement witnessed but not all negative controls killed"
    else:
        c1_status = "FAIL — no non-classical binding"

    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "C1_status": c1_status,
        "summary": {
            "entanglement_witnessed_stages": witnessed_count,
            "total_stages": total,
            "locc_theorem_verified": all(r["mi_locc"] < 1e-10 for r in results),
            "fake_coupling_kill_count": fake_coupling_kills,
            "fake_coupling_all_killed": fake_coupling_kills == total,
            "mispair_kill_count": mispair_kills,
            "mispair_all_killed": mispair_kills == total,
            "fake_coupling_concurrence_kill_count": fake_coupling_concurrence_kills,
            "fake_coupling_concurrence_all_killed": fake_coupling_concurrence_kills == total,
            "fake_coupling_negativity_kill_count": fake_coupling_negativity_kills,
            "fake_coupling_negativity_all_killed": fake_coupling_negativity_kills == total,
            "mispair_concurrence_kill_count": mispair_concurrence_kills,
            "mispair_concurrence_all_killed": mispair_concurrence_kills == total,
            "mispair_negativity_kill_count": mispair_negativity_kills,
            "mispair_negativity_all_killed": mispair_negativity_kills == total,
        },
        "results": results
    }
    
    out_dir = "a2_state/sim_results"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "c1_entanglement_object_search_results.json")
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    run_c1_search()
