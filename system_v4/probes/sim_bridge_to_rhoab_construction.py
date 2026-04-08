#!/usr/bin/env python3
"""
SIM LEGO: Bridge candidates -> bipartite density matrices rho_AB
===============================================================
Pure math. Standalone construction of bipartite density matrices from
simple bridge candidates.

What this sim checks
--------------------
1. Product bridge packets produce product rho_AB.
2. Correlated separable bridge packets produce valid separable rho_AB.
3. Entangled bridge packets produce valid entangled rho_AB when justified.
4. rho_A and rho_B are consistent with partial traces of rho_AB.
5. Invalid bridge packets are rejected.
6. Counterfeit couplings fail positivity or marginal-consistency checks.

Bridge candidates are intentionally simple:
  - product packet
  - separable correlated packet
  - Bell packet
  - Werner packet
  - invalid/counterfeit packets for negative tests

Classification: canonical
"""

import json
import math
import os
import time
import traceback

import torch

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": "not needed -- no graph layer in this bridge constructor"},
    "z3":        {"tried": False, "used": False, "reason": "not needed -- this sim uses exact matrix checks, not satisfiability search"},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed -- no synthesis or SMT constraints are required"},
    "sympy":     {"tried": False, "used": False, "reason": "not needed -- no symbolic derivation beyond exact matrix formulas"},
    "clifford":  {"tried": False, "used": False, "reason": "not needed -- no geometric algebra layer in this lego"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed -- no manifold geometry or statistics here"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed -- no equivariant neural network layer here"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed -- no dependency graph or lattice graph computation here"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed -- no hypergraph or simplicial complex layer here"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed -- no cell complex or filtration layer here"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed -- no persistent homology or filtration computation here"},
}

TOOL_MANIFEST["pytorch"]["tried"] = True
TOOL_MANIFEST["pytorch"]["used"] = True
TOOL_MANIFEST["pytorch"]["reason"] = (
    "Core numeric substrate: density matrices, partial traces, and eigenvalue checks"
)

# =====================================================================
# CONSTANTS
# =====================================================================

TOL = 1e-12
I2 = torch.eye(2, dtype=torch.complex128)
I4 = torch.eye(4, dtype=torch.complex128)
PHI_PLUS = torch.tensor([1.0, 0.0, 0.0, 1.0], dtype=torch.complex128) / math.sqrt(2.0)
PHI_PLUS_DM = torch.outer(PHI_PLUS, PHI_PLUS.conj())


# =====================================================================
# BASIC OPERATORS
# =====================================================================

def normalize_density(rho):
    rho = (rho + rho.conj().T) / 2.0
    tr = torch.trace(rho)
    if abs(tr.item()) <= TOL:
        raise ValueError("zero-trace density matrix")
    return rho / tr


def is_psd(rho, tol=1e-10):
    evals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2.0).real
    return bool(torch.min(evals).item() >= -tol), float(torch.min(evals).item())


def partial_trace_2q(rho_ab, keep):
    rho = rho_ab.reshape(2, 2, 2, 2)
    if keep == 0:
        return torch.einsum("abcb->ac", rho)
    if keep == 1:
        return torch.einsum("abad->bd", rho)
    raise ValueError("keep must be 0 or 1")


def state_validity(rho_ab):
    herm_err = float(torch.max(torch.abs(rho_ab - rho_ab.conj().T)).item())
    tr = float(torch.trace(rho_ab).real.item())
    psd, min_eig = is_psd(rho_ab)
    return {
        "hermitian_error": herm_err,
        "trace": tr,
        "trace_error": abs(tr - 1.0),
        "psd": psd,
        "min_eigenvalue": min_eig,
        "valid": herm_err < 1e-10 and abs(tr - 1.0) < 1e-10 and psd,
    }


def reduced_states(rho_ab):
    return partial_trace_2q(rho_ab, 0), partial_trace_2q(rho_ab, 1)


def reduced_state_consistency(rho_ab, rho_a, rho_b):
    got_a, got_b = reduced_states(rho_ab)
    return {
        "rho_a_max_error": float(torch.max(torch.abs(got_a - rho_a)).item()),
        "rho_b_max_error": float(torch.max(torch.abs(got_b - rho_b)).item()),
        "consistent": (
            torch.max(torch.abs(got_a - rho_a)).item() < 1e-10
            and torch.max(torch.abs(got_b - rho_b)).item() < 1e-10
        ),
    }


def von_neumann_entropy(rho):
    evals = torch.linalg.eigvalsh(normalize_density(rho)).real
    evals = evals[evals > TOL]
    if evals.numel() == 0:
        return 0.0
    return float((-torch.sum(evals * torch.log2(evals))).item())


def mutual_information(rho_ab):
    rho_a, rho_b = reduced_states(rho_ab)
    return von_neumann_entropy(rho_a) + von_neumann_entropy(rho_b) - von_neumann_entropy(rho_ab)


def concurrence_two_qubit(rho):
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
    yy = torch.kron(sy, sy)
    rho_tilde = yy @ rho.conj() @ yy
    eigs = torch.linalg.eigvals(rho @ rho_tilde)
    vals = torch.sort(torch.sqrt(torch.clamp(eigs.real, min=0.0)), descending=True).values
    c = float(max(0.0, (vals[0] - vals[1] - vals[2] - vals[3]).item()))
    return c


# =====================================================================
# BRIDGE PACKETS
# =====================================================================

def product_bridge_packet():
    rho_a = torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=torch.complex128)
    rho_b = torch.tensor([[0.0, 0.0], [0.0, 1.0]], dtype=torch.complex128)
    rho_ab = torch.kron(rho_a, rho_b)
    return {
        "kind": "product",
        "rho_a": rho_a,
        "rho_b": rho_b,
        "rho_ab": rho_ab,
        "bridge_scale": 0.0,
    }


def correlated_separable_packet():
    rho_ab = 0.6 * torch.kron(
        torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=torch.complex128),
        torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=torch.complex128),
    ) + 0.4 * torch.kron(
        torch.tensor([[0.0, 0.0], [0.0, 1.0]], dtype=torch.complex128),
        torch.tensor([[0.0, 0.0], [0.0, 1.0]], dtype=torch.complex128),
    )
    rho_a = torch.tensor([[0.6, 0.0], [0.0, 0.4]], dtype=torch.complex128)
    rho_b = torch.tensor([[0.6, 0.0], [0.0, 0.4]], dtype=torch.complex128)
    return {
        "kind": "correlated_separable",
        "rho_a": rho_a,
        "rho_b": rho_b,
        "rho_ab": rho_ab,
        "bridge_scale": 0.6,
    }


def bell_bridge_packet():
    rho_ab = PHI_PLUS_DM.clone()
    rho_a = I2 / 2.0
    rho_b = I2 / 2.0
    return {
        "kind": "entangled",
        "rho_a": rho_a,
        "rho_b": rho_b,
        "rho_ab": rho_ab,
        "bridge_scale": 1.0,
    }


def werner_bridge_packet(p):
    rho_ab = p * PHI_PLUS_DM + (1.0 - p) * I4 / 4.0
    rho_a = I2 / 2.0
    rho_b = I2 / 2.0
    return {
        "kind": "werner",
        "p": float(p),
        "rho_a": rho_a,
        "rho_b": rho_b,
        "rho_ab": rho_ab,
        "bridge_scale": float(p),
    }


def invalid_bridge_packet():
    rho_ab = torch.tensor(
        [
            [0.7, 0.3, 0.0, 0.0],
            [0.3, 0.4, 0.0, 0.0],
            [0.0, 0.0, -0.1, 0.0],
            [0.0, 0.0, 0.0, 0.0],
        ],
        dtype=torch.complex128,
    )
    rho_a = torch.eye(2, dtype=torch.complex128) / 2.0
    rho_b = torch.eye(2, dtype=torch.complex128) / 2.0
    return {
        "kind": "invalid",
        "rho_a": rho_a,
        "rho_b": rho_b,
        "rho_ab": rho_ab,
        "bridge_scale": None,
    }


def counterfeit_coupling_packet():
    rho_a = torch.tensor([[0.7, 0.0], [0.0, 0.3]], dtype=torch.complex128)
    rho_b = torch.tensor([[0.4, 0.0], [0.0, 0.6]], dtype=torch.complex128)
    # Off-diagonal couplings are inserted without a valid convex decomposition.
    rho_ab = torch.kron(rho_a, rho_b).clone()
    rho_ab[0, 3] = 0.35
    rho_ab[3, 0] = 0.35
    return {
        "kind": "counterfeit",
        "rho_a": rho_a,
        "rho_b": rho_b,
        "rho_ab": rho_ab,
        "bridge_scale": 0.35,
    }


def validate_packet(packet):
    rho_ab = packet["rho_ab"]
    rho_a = packet["rho_a"]
    rho_b = packet["rho_b"]
    validity = state_validity(rho_ab)
    consistency = reduced_state_consistency(rho_ab, rho_a, rho_b)
    return {
        **validity,
        **consistency,
        "rho_ab": rho_ab,
        "rho_a": rho_a,
        "rho_b": rho_b,
        "S_AB": von_neumann_entropy(rho_ab) if validity["valid"] else None,
        "S_A": von_neumann_entropy(rho_a) if validity["valid"] else None,
        "S_B": von_neumann_entropy(rho_b) if validity["valid"] else None,
        "I_AB": mutual_information(rho_ab) if validity["valid"] else None,
        "concurrence": concurrence_two_qubit(rho_ab) if validity["valid"] else None,
    }


# =====================================================================
# TESTS
# =====================================================================

def close(a, b, tol=1e-10):
    return abs(float(a) - float(b)) <= tol


def run_positive_tests():
    results = {}

    product = validate_packet(product_bridge_packet())
    separable = validate_packet(correlated_separable_packet())
    bell = validate_packet(bell_bridge_packet())
    werner = [validate_packet(werner_bridge_packet(p)) for p in [0.0, 0.25, 1.0 / 3.0, 0.6, 1.0]]

    results["product_bridge_constructs_product_state"] = {
        "pass": (
            product["valid"]
            and product["consistent"]
            and close(product["S_AB"], 0.0)
            and close(product["S_A"], 0.0)
            and close(product["S_B"], 0.0)
            and close(product["I_AB"], 0.0)
            and close(product["concurrence"], 0.0)
        ),
        "details": product,
    }

    results["correlated_separable_bridge_constructs_separable_state"] = {
        "pass": (
            separable["valid"]
            and separable["consistent"]
            and close(separable["S_AB"], 0.9709505944546686)
            and close(separable["S_A"], separable["S_B"])
            and close(separable["concurrence"], 0.0)
            and separable["I_AB"] > 0.0
        ),
        "details": separable,
    }

    results["bell_bridge_constructs_entangled_state"] = {
        "pass": (
            bell["valid"]
            and bell["consistent"]
            and close(bell["S_AB"], 0.0)
            and close(bell["S_A"], 1.0)
            and close(bell["S_B"], 1.0)
            and close(bell["I_AB"], 2.0)
            and bell["concurrence"] > 0.99
        ),
        "details": bell,
    }

    results["werner_sweep_has_expected_endpoints"] = {
        "pass": (
            close(werner[0]["S_AB"], 2.0)
            and close(werner[-1]["S_AB"], 0.0)
            and close(werner[0]["S_A"], 1.0)
            and close(werner[-1]["S_A"], 1.0)
            and close(werner[0]["S_B"], 1.0)
            and close(werner[-1]["S_B"], 1.0)
        ),
        "details": werner,
    }

    results["werner_mutual_information_monotone_in_p"] = {
        "pass": all(
            werner[i + 1]["I_AB"] >= werner[i]["I_AB"] - 1e-10
            for i in range(len(werner) - 1)
        ),
        "I_AB_trace": [w["I_AB"] for w in werner],
    }

    return results


def run_negative_tests():
    results = {}

    invalid = validate_packet(invalid_bridge_packet())
    counterfeit = validate_packet(counterfeit_coupling_packet())

    results["invalid_bridge_packet_rejected"] = {
        "pass": not invalid["valid"] or not invalid["consistent"],
        "details": invalid,
        "note": "Invalid packet has negative eigenvalue and broken trace consistency.",
    }

    results["counterfeit_coupling_rejected"] = {
        "pass": not counterfeit["valid"] or not counterfeit["consistent"],
        "details": counterfeit,
        "note": "Counterfeit coupling should fail PSD or reduced-state consistency.",
    }

    results["product_bridge_not_entangled"] = {
        "pass": close(validate_packet(product_bridge_packet())["concurrence"], 0.0),
        "note": "Product bridge must not produce entanglement.",
    }

    results["separable_bridge_not_pure"] = {
        "pass": validate_packet(correlated_separable_packet())["S_AB"] > 0.0,
        "note": "Classically correlated separable bridge has nonzero joint entropy.",
    }

    return results


def run_boundary_tests():
    results = {}

    p0 = validate_packet(werner_bridge_packet(0.0))
    pthird = validate_packet(werner_bridge_packet(1.0 / 3.0))
    pone = validate_packet(werner_bridge_packet(1.0))

    results["werner_p_zero_boundary"] = {
        "pass": close(p0["S_AB"], 2.0) and close(p0["I_AB"], 0.0),
        "details": p0,
    }
    results["werner_p_third_boundary"] = {
        "pass": close(pthird["S_A"], 1.0) and close(pthird["S_B"], 1.0) and pthird["concurrence"] <= 1e-10,
        "details": pthird,
    }
    results["werner_p_one_boundary"] = {
        "pass": close(pone["S_AB"], 0.0) and pone["concurrence"] > 0.99,
        "details": pone,
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("Running bridge -> rho_AB construction sim...")
    t_start = time.time()

    try:
        positive = run_positive_tests()
        negative = run_negative_tests()
        boundary = run_boundary_tests()
        error = None
    except Exception as exc:
        positive = {}
        negative = {}
        boundary = {}
        error = {"error": str(exc), "traceback": traceback.format_exc()}

    def count_passes(section):
        total = sum(1 for v in section.values() if isinstance(v, dict) and "pass" in v)
        passed = sum(1 for v in section.values() if isinstance(v, dict) and v.get("pass"))
        return passed, total

    p_pass, p_total = count_passes(positive)
    n_pass, n_total = count_passes(negative)
    b_pass, b_total = count_passes(boundary)

    results = {
        "name": "Bridge to rho_AB Construction",
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
            "all_pass": error is None and p_pass == p_total and n_pass == n_total and b_pass == b_total,
            "total_time_s": time.time() - t_start,
        },
    }
    if error is not None:
        results["error"] = error

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "bridge_to_rhoab_construction_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults written to {out_path}")
    print(f"Positive: {p_pass}/{p_total}  Negative: {n_pass}/{n_total}  Boundary: {b_pass}/{b_total}")
    if results["summary"]["all_pass"]:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED -- check results JSON")
