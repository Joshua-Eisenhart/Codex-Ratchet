#!/usr/bin/env python3
"""
SIM LEGO: Phi0 candidate disqualification battery
=================================================
Pure math. Negative battery for bad Phi0 candidates.

What gets disqualified
----------------------
1. Unsigned-only metrics pretending to be signed primitives
2. Local-entropy-only kernels
3. Normalization artifacts on invalid packets
4. Shell-weighting with arbitrary gain
5. Kernels that fail to separate product vs entangled / correlated bridge states

This battery is intentionally conservative: a candidate is only allowed if
it respects the sign structure, state validity, and separation behavior of
bridge-built density matrices.

Classification: canonical
"""

import json
import math
import os
import time
import traceback

import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "not needed -- exact finite-dimensional numpy checks are sufficient"},
    "pyg":       {"tried": False, "used": False, "reason": "not needed -- no graph layer in this disqualification battery"},
    "z3":        {"tried": False, "used": False, "reason": "not needed -- this battery is exact numeric and constructive"},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed -- no synthesis or SMT constraints are required"},
    "sympy":     {"tried": False, "used": False, "reason": "not needed -- no symbolic derivation beyond exact matrix formulas"},
    "clifford":  {"tried": False, "used": False, "reason": "not needed -- no geometric algebra layer here"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed -- no manifold geometry or statistics here"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed -- no equivariant learning layer here"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed -- no dependency graph or lattice graph computation here"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed -- no hypergraph or simplicial complex layer here"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed -- no cell complex or filtration layer here"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed -- no persistent homology or filtration computation here"},
}

# =====================================================================
# CONSTANTS / HELPERS
# =====================================================================

EPS = 1e-12
I2 = np.eye(2, dtype=np.complex128)
I4 = np.eye(4, dtype=np.complex128)
PHI_PLUS = np.array([1.0, 0.0, 0.0, 1.0], dtype=np.complex128) / math.sqrt(2.0)
PHI_PLUS_DM = np.outer(PHI_PLUS, PHI_PLUS.conj())


def hermitian(rho):
    return 0.5 * (rho + rho.conj().T)


def normalize_density(rho):
    rho = hermitian(rho)
    tr = np.real(np.trace(rho))
    if abs(tr) <= EPS:
        raise ValueError("zero-trace density matrix")
    return rho / tr


def validate_density(rho):
    rho = hermitian(rho)
    evals = np.linalg.eigvalsh(rho).real
    tr = float(np.real(np.trace(rho)))
    return {
        "trace": tr,
        "trace_error": abs(tr - 1.0),
        "min_eigenvalue": float(np.min(evals)),
        "psd": bool(np.min(evals) >= -1e-10),
        "hermitian": bool(np.max(np.abs(rho - rho.conj().T)) < 1e-10),
        "valid": bool(abs(tr - 1.0) < 1e-10 and np.min(evals) >= -1e-10 and np.max(np.abs(rho - rho.conj().T)) < 1e-10),
    }


def entropy(rho):
    rho = normalize_density(rho)
    evals = np.linalg.eigvalsh(rho).real
    evals = np.clip(evals, 0.0, None)
    nz = evals[evals > EPS]
    if nz.size == 0:
        return 0.0
    return float(-np.sum(nz * np.log2(nz)))


def partial_trace(rho, dims, keep):
    dims = list(dims)
    keep = list(keep)
    rho_t = rho.reshape(dims + dims)
    trace_over = [i for i in range(len(dims)) if i not in keep]
    for ax in sorted(trace_over, reverse=True):
        rho_t = np.trace(rho_t, axis1=ax, axis2=ax + len(dims))
        dims.pop(ax)
    d_keep = int(np.prod(dims))
    return rho_t.reshape(d_keep, d_keep)


def reduced_states(rho_ab):
    return partial_trace(rho_ab, [2, 2], [0]), partial_trace(rho_ab, [2, 2], [1])


def mutual_information(rho_ab):
    rho_a, rho_b = reduced_states(rho_ab)
    return entropy(rho_a) + entropy(rho_b) - entropy(rho_ab)


def coherent_information_a_to_b(rho_ab):
    _, rho_b = reduced_states(rho_ab)
    return entropy(rho_b) - entropy(rho_ab)


def local_entropy_sum(rho_ab):
    rho_a, rho_b = reduced_states(rho_ab)
    return entropy(rho_a) + entropy(rho_b)


def joint_entropy_only(rho_ab):
    return entropy(rho_ab)


def unsigned_signed_primitive(rho_ab):
    return abs(coherent_information_a_to_b(rho_ab))


def normalization_artifact_kernel(rho_ab):
    # This is intentionally bad: it rescales any Hermitian input into a density matrix.
    return entropy(normalize_density(rho_ab))


def shell_weight_affine_gain(profile, weights):
    weights = np.asarray(weights, dtype=np.float64)
    profile = np.asarray(profile, dtype=np.float64)
    norm = weights / weights.sum()
    return float(np.dot(norm, profile) + 0.25 * weights.sum())


def weighted_shell_average(profile, weights):
    weights = np.asarray(weights, dtype=np.float64)
    profile = np.asarray(profile, dtype=np.float64)
    return float(np.dot(weights / weights.sum(), profile))


def product_bridge_state():
    rho_a = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=np.complex128)
    rho_b = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=np.complex128)
    rho_ab = np.kron(rho_a, rho_b)
    return {"kind": "product", "rho_a": rho_a, "rho_b": rho_b, "rho_ab": rho_ab}


def classical_correlated_bridge_state():
    rho_ab = 0.5 * np.array(
        [
            [1, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 1],
        ],
        dtype=np.complex128,
    )
    rho_a = np.eye(2, dtype=np.complex128) / 2.0
    rho_b = np.eye(2, dtype=np.complex128) / 2.0
    return {"kind": "classically_correlated", "rho_a": rho_a, "rho_b": rho_b, "rho_ab": rho_ab}


def bell_bridge_state():
    rho_ab = PHI_PLUS_DM.copy()
    rho_a = np.eye(2, dtype=np.complex128) / 2.0
    rho_b = np.eye(2, dtype=np.complex128) / 2.0
    return {"kind": "entangled", "rho_a": rho_a, "rho_b": rho_b, "rho_ab": rho_ab}


def maximally_mixed_bridge_state():
    rho_ab = I4 / 4.0
    rho_a = np.eye(2, dtype=np.complex128) / 2.0
    rho_b = np.eye(2, dtype=np.complex128) / 2.0
    return {"kind": "maximally_mixed", "rho_a": rho_a, "rho_b": rho_b, "rho_ab": rho_ab}


def invalid_bridge_state():
    rho_ab = np.array(
        [
            [0.7, 0.3, 0.0, 0.0],
            [0.3, 0.4, 0.0, 0.0],
            [0.0, 0.0, -0.1, 0.0],
            [0.0, 0.0, 0.0, 0.0],
        ],
        dtype=np.complex128,
    )
    rho_a = np.eye(2, dtype=np.complex128) / 2.0
    rho_b = np.eye(2, dtype=np.complex128) / 2.0
    return {"kind": "invalid", "rho_a": rho_a, "rho_b": rho_b, "rho_ab": rho_ab}


def counterfeit_bridge_state():
    rho_a = np.array([[0.7, 0.0], [0.0, 0.3]], dtype=np.complex128)
    rho_b = np.array([[0.4, 0.0], [0.0, 0.6]], dtype=np.complex128)
    rho_ab = np.kron(rho_a, rho_b).copy()
    rho_ab[0, 3] = 0.35
    rho_ab[3, 0] = 0.35
    return {"kind": "counterfeit", "rho_a": rho_a, "rho_b": rho_b, "rho_ab": rho_ab}


def bridge_validity(packet):
    rho_ab = packet["rho_ab"]
    rho_a = packet["rho_a"]
    rho_b = packet["rho_b"]
    rho_ab_val = validate_density(rho_ab)
    got_a, got_b = reduced_states(rho_ab)
    err_a = float(np.max(np.abs(got_a - rho_a)))
    err_b = float(np.max(np.abs(got_b - rho_b)))
    return {
        **rho_ab_val,
        "rho_a_max_error": err_a,
        "rho_b_max_error": err_b,
        "marginals_consistent": bool(err_a < 1e-10 and err_b < 1e-10),
        "S_AB": entropy(rho_ab) if rho_ab_val["valid"] else None,
        "S_A": entropy(rho_a) if rho_ab_val["valid"] else None,
        "S_B": entropy(rho_b) if rho_ab_val["valid"] else None,
        "I_AB": mutual_information(rho_ab) if rho_ab_val["valid"] else None,
        "Ic_A_to_B": coherent_information_a_to_b(rho_ab) if rho_ab_val["valid"] else None,
    }


def classical_pair_same_marginals():
    # Same local states as Bell, but separable.
    return bell_state_correlation().copy()


def bell_state_correlation():
    return classical_correlated_bridge_state()["rho_ab"]


# =====================================================================
# TESTS
# =====================================================================

def close(a, b, tol=1e-10):
    return abs(float(a) - float(b)) <= tol


def run_positive_tests():
    results = {}

    product = bridge_validity(product_bridge_state())
    correlated = bridge_validity(classical_correlated_bridge_state())
    bell = bridge_validity(bell_bridge_state())
    mixed = bridge_validity(maximally_mixed_bridge_state())
    werners = [bridge_validity({"kind": "werner", "rho_a": np.eye(2) / 2.0, "rho_b": np.eye(2) / 2.0, "rho_ab": (p * PHI_PLUS_DM + (1.0 - p) * I4 / 4.0)}) for p in [0.0, 0.25, 1.0 / 3.0, 0.6, 1.0]]

    results["signed_primitives_have_correct_sign_structure"] = {
        "pass": (
            close(product["Ic_A_to_B"], 0.0)
            and close(bell["Ic_A_to_B"], 1.0)
            and close(mixed["Ic_A_to_B"], -1.0)
            and bell["I_AB"] > correlated["I_AB"] > product["I_AB"]
        ),
        "details": {
            "product": product["Ic_A_to_B"],
            "bell": bell["Ic_A_to_B"],
            "mixed": mixed["Ic_A_to_B"],
            "I_product": product["I_AB"],
            "I_correlated": correlated["I_AB"],
            "I_bell": bell["I_AB"],
        },
    }

    results["bridge_states_are_valid_density_matrices"] = {
        "pass": product["valid"] and correlated["valid"] and bell["valid"] and mixed["valid"],
        "details": {
            "product": product,
            "correlated": correlated,
            "bell": bell,
            "mixed": mixed,
        },
    }

    results["werner_sweep_obeys_basic_bounds"] = {
        "pass": all(
            w["valid"]
            and w["marginals_consistent"]
            and 0.0 <= w["S_AB"] <= 2.0 + 1e-10
            and w["I_AB"] >= -1e-10
            for w in werners
        ),
        "details": werners,
    }

    return results


def run_negative_tests():
    results = {}

    product = bridge_validity(product_bridge_state())
    correlated = bridge_validity(classical_correlated_bridge_state())
    bell = bridge_validity(bell_bridge_state())
    mixed = bridge_validity(maximally_mixed_bridge_state())
    invalid = bridge_validity(invalid_bridge_state())
    counterfeit = bridge_validity(counterfeit_bridge_state())

    unsigned_bell = unsigned_signed_primitive(bell_bridge_state()["rho_ab"])
    unsigned_mixed = unsigned_signed_primitive(maximally_mixed_bridge_state()["rho_ab"])

    results["unsigned_only_signed_primitive_disqualified"] = {
        "pass": close(unsigned_bell, unsigned_mixed) and not close(bell["Ic_A_to_B"], mixed["Ic_A_to_B"]),
        "unsigned_bell": unsigned_bell,
        "unsigned_mixed": unsigned_mixed,
        "signed_bell": bell["Ic_A_to_B"],
        "signed_mixed": mixed["Ic_A_to_B"],
        "note": "Absolute-value kernel loses the sign information and is therefore disqualified.",
    }

    local_only_bell = local_entropy_sum(bell_bridge_state()["rho_ab"])
    local_only_corr = local_entropy_sum(classical_correlated_bridge_state()["rho_ab"])
    results["local_entropy_only_kernel_disqualified"] = {
        "pass": close(local_only_bell, local_only_corr),
        "bell_local_sum": local_only_bell,
        "correlated_local_sum": local_only_corr,
        "note": "Local-entropy-only kernel cannot separate Bell from classically correlated bridge states with the same marginals.",
    }

    joint_only_product = joint_entropy_only(product_bridge_state()["rho_ab"])
    joint_only_bell = joint_entropy_only(bell_bridge_state()["rho_ab"])
    results["joint_entropy_only_kernel_disqualified"] = {
        "pass": close(joint_only_product, joint_only_bell),
        "product_joint": joint_only_product,
        "bell_joint": joint_only_bell,
        "note": "Joint entropy alone cannot separate product from entangled pure bridge states.",
    }

    artifact_score = normalization_artifact_kernel(invalid_bridge_state()["rho_ab"])
    results["normalization_artifact_disqualified"] = {
        "pass": artifact_score > 0.0 and not invalid["valid"],
        "artifact_score": artifact_score,
        "invalid_valid": invalid["valid"],
        "note": "A kernel that normalizes invalid packets instead of rejecting them is disqualified.",
    }

    shell_profile = [0.1, 0.4, 0.7, 1.0]
    weights = [1.0, 2.0, 3.0, 4.0]
    scaled = [10.0, 20.0, 30.0, 40.0]
    shell_gain = shell_weight_affine_gain(shell_profile, weights)
    shell_gain_scaled = shell_weight_affine_gain(shell_profile, scaled)
    results["shell_weight_affine_gain_disqualified"] = {
        "pass": not close(shell_gain, shell_gain_scaled) and shell_gain != 0.0,
        "gain": shell_gain,
        "gain_scaled": shell_gain_scaled,
        "note": "Affine gain makes the score depend on arbitrary weight scaling.",
    }

    results["counterfeit_bridge_not_accepted_as_trusted"] = {
        "pass": (not counterfeit["valid"]) or (not counterfeit["marginals_consistent"]),
        "details": counterfeit,
        "note": "Counterfeit coupling fails positivity or marginal consistency and must be rejected.",
    }

    return results


def run_boundary_tests():
    results = {}

    product = bridge_validity(product_bridge_state())
    bell = bridge_validity(bell_bridge_state())
    mixed = bridge_validity(maximally_mixed_bridge_state())
    correlated = bridge_validity(classical_correlated_bridge_state())

    results["product_joint_entropy_zero_boundary"] = {
        "pass": close(product["S_AB"], 0.0),
        "S_AB": product["S_AB"],
    }
    results["bell_signed_coherent_info_boundary"] = {
        "pass": close(bell["Ic_A_to_B"], 1.0),
        "Ic_A_to_B": bell["Ic_A_to_B"],
    }
    results["maximally_mixed_signed_lower_boundary"] = {
        "pass": close(mixed["Ic_A_to_B"], -1.0),
        "Ic_A_to_B": mixed["Ic_A_to_B"],
    }
    results["correlated_bridge_same_marginals_boundary"] = {
        "pass": close(correlated["S_A"], bell["S_A"]) and close(correlated["S_B"], bell["S_B"]),
        "S_A_corr": correlated["S_A"],
        "S_A_bell": bell["S_A"],
        "S_B_corr": correlated["S_B"],
        "S_B_bell": bell["S_B"],
    }

    return results


def count_passes(section):
    total = sum(1 for v in section.values() if isinstance(v, dict) and "pass" in v)
    passed = sum(1 for v in section.values() if isinstance(v, dict) and v.get("pass") is True)
    return passed, total


def main():
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    p_pass, p_total = count_passes(positive)
    n_pass, n_total = count_passes(negative)
    b_pass, b_total = count_passes(boundary)

    results = {
        "name": "Phi0 Candidate Disqualification Battery",
        "schema_version": "1.0",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "positive": f"{p_pass}/{p_total}",
            "negative": f"{n_pass}/{n_total}",
            "boundary": f"{b_pass}/{b_total}",
            "all_pass": p_pass == p_total and n_pass == n_total and b_pass == b_total,
            "total_time_s": 0.0,
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "negative_phi0_candidate_disqualifiers_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Results written to {out_path}")
    print(results["summary"])


if __name__ == "__main__":
    try:
        t0 = time.time()
        main()
    except Exception as exc:
        print("FAILED:", exc)
        print(traceback.format_exc())
        raise
