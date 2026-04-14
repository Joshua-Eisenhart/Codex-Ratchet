#!/usr/bin/env python3
"""
sim_c1_mispair_probe.py
=======================

Targeted probe: Why is the C1 mispair control NOT killed for Fe/Fi operators?

Hypothesis: The mispair survival is operator-driven, not state-driven.
Fe (XX unitary) and Fi (XZ unitary) are entangling gates that generate
entanglement from ANY product state input, regardless of the chirality pairing.
Ti (ZZ dephasing) and Te (YY dephasing) destroy coherences and cannot
generate entanglement from product states.

This probe:
  1. Measures trace distance and fidelity between Type1 vs Type2 initial states
     (rho_L and rho_R) to check if they are structurally distinguishable.
  2. Tests whether each joint operator generates entanglement from ANY
     separable product state (maximally mixed, computational basis, etc.)
  3. Emits a characterization verdict per operator family.
"""

import json
import os
import sys
from datetime import datetime, UTC

import numpy as np
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_core import GeometricEngine, EngineState, TERRAINS
from geometric_operators import (
    apply_Ti_4x4, apply_Fe_4x4, apply_Te_4x4, apply_Fi_4x4,
    SIGMA_X, SIGMA_Y, SIGMA_Z, I2, _ensure_valid_density,
    partial_trace_A, partial_trace_B,
)
from stage_matrix_neg_lib import all_stage_rows, init_stage


# ═══════════════════════════════════════════════════════════════════
# ENTANGLEMENT WITNESSES (reused from c1 search)
# ═══════════════════════════════════════════════════════════════════

def get_concurrence(rho: np.ndarray) -> float:
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sysy = np.kron(sy, sy)
    rho_tilde = sysy @ rho.conj() @ sysy
    R = rho @ rho_tilde
    evals = np.linalg.eigvals(R)
    evals_sqrt = np.sqrt(np.maximum(evals.real, 0.0))
    evals_sqrt = np.sort(evals_sqrt)[::-1]
    return float(np.maximum(0.0, evals_sqrt[0] - evals_sqrt[1] - evals_sqrt[2] - evals_sqrt[3]))


def get_negativity(rho: np.ndarray) -> float:
    rho_pt = rho.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    evals = np.linalg.eigvalsh(rho_pt)
    return float(-np.sum(evals[evals < 0]))


# ═══════════════════════════════════════════════════════════════════
# STATE DISTINGUISHABILITY METRICS
# ═══════════════════════════════════════════════════════════════════

def trace_distance_2x2(rho1: np.ndarray, rho2: np.ndarray) -> float:
    """TD = 0.5 * Tr|rho1 - rho2|."""
    diff = rho1 - rho2
    evals = np.linalg.eigvalsh(diff)
    return float(0.5 * np.sum(np.abs(evals)))


def fidelity_2x2(rho1: np.ndarray, rho2: np.ndarray) -> float:
    """F(rho1, rho2) = Tr(sqrt(sqrt(rho1) rho2 sqrt(rho1)))^2."""
    # sqrt via eigendecomposition
    evals1, evecs1 = np.linalg.eigh(rho1)
    evals1 = np.maximum(evals1, 0.0)
    sqrt_rho1 = evecs1 @ np.diag(np.sqrt(evals1)) @ evecs1.conj().T
    M = sqrt_rho1 @ rho2 @ sqrt_rho1
    evals_M = np.linalg.eigvalsh(M)
    evals_M = np.maximum(evals_M, 0.0)
    return float(np.sum(np.sqrt(evals_M)) ** 2)


# ═══════════════════════════════════════════════════════════════════
# OPERATOR ENTANGLING POWER TEST
# Tests whether each operator can generate entanglement from a separable
# product state. Uses diverse test states to cover the product state space.
# ═══════════════════════════════════════════════════════════════════

def make_test_product_states() -> list:
    """Build a set of separable product states rho_A ⊗ rho_B."""
    states = []

    # |0><0| ⊗ |0><0|
    r0 = np.array([[1, 0], [0, 0]], dtype=complex)
    states.append(("00", np.kron(r0, r0)))

    # |1><1| ⊗ |1><1|
    r1 = np.array([[0, 0], [0, 1]], dtype=complex)
    states.append(("11", np.kron(r1, r1)))

    # |+><+| ⊗ |+><+|  (X eigenstates)
    rp = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
    states.append(("++", np.kron(rp, rp)))

    # |0><0| ⊗ |+><+|
    states.append(("0+", np.kron(r0, rp)))

    # maximally mixed ⊗ maximally mixed
    rmm = np.eye(2, dtype=complex) / 2
    states.append(("mm", np.kron(rmm, rmm)))

    # Y eigenstate ⊗ Y eigenstate  |i><i|
    ry = np.array([[0.5, -0.5j], [0.5j, 0.5]], dtype=complex)
    states.append(("yy", np.kron(ry, ry)))

    return states


def operator_entangling_power(op_fn, polarity_up: bool = True, strength: float = 0.8) -> dict:
    """
    Test whether op_fn generates entanglement (concurrence or negativity > 1e-5)
    from any of the test product states.
    """
    test_states = make_test_product_states()
    results = []
    max_concurrence = 0.0
    max_negativity = 0.0
    any_entangled = False

    for label, rho_sep in test_states:
        rho_sep = _ensure_valid_density(rho_sep)
        rho_out = op_fn(rho_sep, polarity_up=polarity_up, strength=strength)
        c = get_concurrence(rho_out)
        n = get_negativity(rho_out)
        entangled = c > 1e-5 or n > 1e-5
        if entangled:
            any_entangled = True
        max_concurrence = max(max_concurrence, c)
        max_negativity = max(max_negativity, n)
        results.append({
            "input_state": label,
            "concurrence_out": float(c),
            "negativity_out": float(n),
            "entangled": entangled,
        })

    return {
        "any_entangled_from_product_state": any_entangled,
        "max_concurrence": float(max_concurrence),
        "max_negativity": float(max_negativity),
        "per_input": results,
    }


# ═══════════════════════════════════════════════════════════════════
# MAIN PROBE
# ═══════════════════════════════════════════════════════════════════

def mutual_information_4x4(rho_AB: np.ndarray) -> float:
    """I(A:B) = S(rho_A) + S(rho_B) - S(rho_AB)"""
    def s_vn(rho):
        evals = np.linalg.eigvalsh(rho)
        evals = evals[evals > 1e-15]
        return float(-np.sum(evals * np.log2(evals))) if len(evals) > 0 else 0.0
    rho_A = _ensure_valid_density(partial_trace_B(rho_AB))
    rho_B = _ensure_valid_density(partial_trace_A(rho_AB))
    evals_AB = np.linalg.eigvalsh(rho_AB)
    evals_AB = evals_AB[evals_AB > 1e-15]
    s_AB = float(-np.sum(evals_AB * np.log2(evals_AB))) if len(evals_AB) > 0 else 0.0
    return float(s_vn(rho_A) + s_vn(rho_B) - s_AB)


def run_mispair_probe():
    joint_ops = {
        "Ti": apply_Ti_4x4,
        "Fe": apply_Fe_4x4,
        "Te": apply_Te_4x4,
        "Fi": apply_Fi_4x4,
    }

    # ── 1. Per-row state distinguishability and mispair entanglement ──
    row_results = []
    for engine_type, row in all_stage_rows():
        seed = 11000 + engine_type * 10 + row[0]
        _, state, meta = init_stage(engine_type, row, seed)

        # Get the paired rho from the OTHER engine type at same row
        other_engine_type = 3 - engine_type  # 1→2, 2→1
        seed_other = 21000 + engine_type * 10 + row[0]
        _, state_other, _ = init_stage(other_engine_type, row, seed_other)

        rho_L_self = state.rho_L
        rho_R_self = state.rho_R
        rho_L_other = state_other.rho_L
        rho_R_other = state_other.rho_R

        # Distinguishability: how different are the initial states?
        td_rho_L = trace_distance_2x2(rho_L_self, rho_L_other)
        td_rho_R = trace_distance_2x2(rho_R_self, rho_R_other)
        fid_rho_L = fidelity_2x2(rho_L_self, rho_L_other)
        fid_rho_R = fidelity_2x2(rho_R_self, rho_R_other)

        # Native operator
        op_name = meta["native_operator"]
        op_fn = joint_ops[op_name]

        # Correct pairing: rho_L_self ⊗ rho_R_self (same engine)
        rho_correct = _ensure_valid_density(np.kron(rho_L_self, rho_R_self))
        rho_correct_evolved = op_fn(rho_correct, polarity_up=meta["axis6_up"], strength=0.8)
        c_correct = get_concurrence(rho_correct_evolved)
        n_correct = get_negativity(rho_correct_evolved)
        mi_correct = mutual_information_4x4(rho_correct_evolved)

        # Mispair product state: rho_L from self ⊗ rho_R from other (cross-chirality)
        rho_mispair = _ensure_valid_density(np.kron(rho_L_self, rho_R_other))
        rho_mispair_evolved = op_fn(rho_mispair, polarity_up=meta["axis6_up"], strength=0.8)
        c_mispair = get_concurrence(rho_mispair_evolved)
        n_mispair = get_negativity(rho_mispair_evolved)
        mi_mispair = mutual_information_4x4(rho_mispair_evolved)

        row_results.append({
            "engine_type": engine_type,
            "stage": meta["label"],
            "op": op_name,
            # Spec-required field names
            "trace_distance_L": float(td_rho_L),
            "trace_distance_R": float(td_rho_R),
            "mi_correct": float(mi_correct),
            "mi_mispair": float(mi_mispair),
            "concurrence_correct": float(c_correct),
            "concurrence_mispair": float(c_mispair),
            "negativity_correct": float(n_correct),
            "negativity_mispair": float(n_mispair),
            # Extra diagnostic fields
            "rho_L_fidelity_T1_vs_T2": float(fid_rho_L),
            "rho_R_fidelity_T1_vs_T2": float(fid_rho_R),
            "states_structurally_distinguishable": td_rho_L > 0.05 or td_rho_R > 0.05,
            "correct_entangled": c_correct > 1e-5 or n_correct > 1e-5,
            "mispair_entangled": c_mispair > 1e-5 or n_mispair > 1e-5,
        })

    # ── 2. Operator entangling power: does the op entangle ANY product state? ──
    op_power = {}
    for op_name, op_fn in joint_ops.items():
        # Test both polarities
        power_up = operator_entangling_power(op_fn, polarity_up=True, strength=0.8)
        power_dn = operator_entangling_power(op_fn, polarity_up=False, strength=0.8)
        op_power[op_name] = {
            "polarity_up": power_up,
            "polarity_down": power_dn,
            "universally_entangling": (
                power_up["any_entangled_from_product_state"] or
                power_dn["any_entangled_from_product_state"]
            ),
        }

    # ── 3. Characterization verdict ──
    # Operator-driven: the operator itself generates entanglement from any product state
    # State-driven: entanglement only emerges from structurally correct pairing
    universally_entangling_ops = [op for op, v in op_power.items() if v["universally_entangling"]]
    non_entangling_ops = [op for op, v in op_power.items() if not v["universally_entangling"]]

    # Check: do mispair-entangled rows correspond to universally-entangling ops?
    mispair_entangled_ops = set(r["op"] for r in row_results if r["mispair_entangled"])
    mispair_clean_ops = set(r["op"] for r in row_results if not r["mispair_entangled"])

    # Verdict logic
    ops_match_entangling = mispair_entangled_ops.issubset(set(universally_entangling_ops))
    ops_match_clean = mispair_clean_ops.issubset(set(non_entangling_ops))

    if ops_match_entangling and ops_match_clean:
        verdict = "operator-driven"
        verdict_explanation = (
            f"Mispair entanglement is fully explained by operator structure. "
            f"Universally-entangling operators {sorted(universally_entangling_ops)} "
            f"generate entanglement from ANY product state (regardless of chirality pairing). "
            f"Non-entangling operators {sorted(non_entangling_ops)} produce only dephasing "
            f"and cannot generate entanglement from product states. "
            f"The Weyl chirality difference between Type1/Type2 is REAL but IRRELEVANT "
            f"to whether entanglement survives: it is the operator family (unitary rotation "
            f"vs dephasing) that determines the outcome."
        )
    else:
        verdict = "mixed"
        verdict_explanation = (
            f"Mispair pattern does not fully resolve by operator family alone. "
            f"Universally-entangling: {sorted(universally_entangling_ops)}, "
            f"mispair-entangled ops: {sorted(mispair_entangled_ops)}, "
            f"mispair-clean ops: {sorted(mispair_clean_ops)}. "
            f"Further investigation needed."
        )

    # ── 4. State distinguishability summary ──
    all_td_L = [r["trace_distance_L"] for r in row_results if r["engine_type"] == 1]
    all_td_R = [r["trace_distance_R"] for r in row_results if r["engine_type"] == 1]
    avg_td_L = float(np.mean(all_td_L)) if all_td_L else 0.0
    avg_td_R = float(np.mean(all_td_R)) if all_td_R else 0.0
    states_distinguishable = avg_td_L > 0.05 or avg_td_R > 0.05

    # ── 5. Summary counts ──
    total_stages = len(row_results)
    correct_entangled_count = sum(1 for r in row_results if r["correct_entangled"])
    mispair_entangled_count = sum(1 for r in row_results if r["mispair_entangled"])
    mispair_killed_count = total_stages - mispair_entangled_count
    universally_entangling_op_count = len(universally_entangling_ops)

    payload = {
        "timestamp": datetime.now(UTC).isoformat(),
        "probe": "c1_mispair_targeted_probe",
        "characterization": verdict,
        "verdict": verdict,
        "verdict_explanation": verdict_explanation,
        "summary": {
            "total_stages": total_stages,
            "correct_entangled_count": correct_entangled_count,
            "mispair_entangled_count": mispair_entangled_count,
            "mispair_killed_count": mispair_killed_count,
            "universally_entangling_ops": sorted(universally_entangling_ops),
            "non_entangling_ops": sorted(non_entangling_ops),
            "universally_entangling_op_count": universally_entangling_op_count,
            "verdict_clean": ops_match_entangling and ops_match_clean,
        },
        "state_distinguishability_summary": {
            "avg_trace_distance_rho_L_T1_vs_T2": avg_td_L,
            "avg_trace_distance_rho_R_T1_vs_T2": avg_td_R,
            "states_structurally_distinguishable": states_distinguishable,
            "note": (
                "Type1 and Type2 initial states ARE structurally distinguishable "
                "if trace distance > 0.05, meaning the chirality difference is real. "
                "But entanglement survival depends on operator family, not this difference."
            ),
        },
        "operator_entangling_power": op_power,
        "row_results": row_results,
    }

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "c1_mispair_probe_results.json")
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"\n{'='*70}")
    print(f"CHARACTERIZATION VERDICT: {verdict.upper()}")
    print(f"{'='*70}")
    print(f"{verdict_explanation}")
    print(f"\nState distinguishability (Type1 vs Type2 initial states):")
    print(f"  avg trace distance rho_L: {avg_td_L:.4f}")
    print(f"  avg trace distance rho_R: {avg_td_R:.4f}")
    print(f"  structurally distinguishable: {states_distinguishable}")
    print(f"\nOperator entangling power (universally entangling = yes/no):")
    for op, v in op_power.items():
        power = v["polarity_up"]
        print(f"  {op}: universally_entangling={v['universally_entangling']}, "
              f"max_C={power['max_concurrence']:.4f}, max_N={power['max_negativity']:.4f}")
    print(f"\nFile written: {out_path}")
    print(f"{'='*70}\n")

    return out_path


if __name__ == "__main__":
    run_mispair_probe()
