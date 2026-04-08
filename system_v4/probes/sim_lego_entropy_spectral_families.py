#!/usr/bin/env python3
"""
SIM LEGO: Spectral entropy families on density matrices
=======================================================
Pure math. Foundational intrinsic entropies derived only from the spectrum of
density matrices.

Families tested:
  - von Neumann entropy
  - Rényi entropy (alpha sweep)
  - Tsallis entropy (q sweep)
  - Linear entropy
  - Hartley entropy
  - Collision entropy

Core claims:
  1. Pure states have zero spectral entropy across all families.
  2. Maximally mixed qubit states saturate the one-bit upper bound.
  3. Rényi entropies decrease with alpha on a nontrivial spectrum.
  4. Tsallis entropy matches the von Neumann limit at q -> 1.
  5. Collision entropy equals Rényi entropy at alpha = 2.
  6. Hartley entropy equals log2(rank).

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
    "pytorch":    {"tried": False, "used": False, "reason": ""},
    "pyg":        {"tried": False, "used": False, "reason": "not needed -- no graph layer in this spectral entropy lego"},
    "z3":         {"tried": False, "used": False, "reason": "not needed -- all claims are exact spectral evaluations, no satisfiability search required"},
    "cvc5":       {"tried": False, "used": False, "reason": "not needed -- no synthesis or SMT constraint search required"},
    "sympy":      {"tried": False, "used": False, "reason": "not needed -- closed-form spectral formulas are evaluated directly"},
    "clifford":   {"tried": False, "used": False, "reason": "not needed -- no geometric algebra structure is part of this lego"},
    "geomstats":  {"tried": False, "used": False, "reason": "not needed -- no manifold geometry or geodesic computation here"},
    "e3nn":       {"tried": False, "used": False, "reason": "not needed -- no equivariant neural network layer here"},
    "rustworkx":  {"tried": False, "used": False, "reason": "not needed -- no dependency graph or lattice graph computation here"},
    "xgi":        {"tried": False, "used": False, "reason": "not needed -- no hypergraph or simplicial complex layer here"},
    "toponetx":   {"tried": False, "used": False, "reason": "not needed -- no cell complex or topological filtration in this lego"},
    "gudhi":      {"tried": False, "used": False, "reason": "not needed -- no persistent homology or filtration computation here"},
}

TOOL_MANIFEST["pytorch"]["tried"] = True
TOOL_MANIFEST["pytorch"]["used"] = True
TOOL_MANIFEST["pytorch"]["reason"] = (
    "Core numeric substrate: density matrices, eigenspectra, and exact spectral entropy evaluation"
)

# =====================================================================
# CONSTANTS
# =====================================================================

TOL = 1e-12
LN2 = math.log(2.0)
I2 = torch.eye(2, dtype=torch.complex128)


# =====================================================================
# STATE CONSTRUCTION
# =====================================================================

def pure_state_density(ket):
    ket = ket.to(torch.complex128)
    ket = ket / torch.linalg.norm(ket)
    return torch.outer(ket, ket.conj())


def diagonal_density(probs):
    probs = torch.tensor(probs, dtype=torch.float64)
    probs = probs / torch.sum(probs)
    return torch.diag(probs.to(torch.complex128))


def maximally_mixed_density(dim=2):
    return torch.eye(dim, dtype=torch.complex128) / float(dim)


def spectrum(rho):
    herm = (rho + rho.conj().T) / 2.0
    evals = torch.linalg.eigvalsh(herm).real
    evals = torch.clamp(evals, min=0.0)
    total = torch.sum(evals)
    if float(total) <= TOL:
        raise ValueError("density matrix has zero trace after symmetrization")
    return evals / total


def rank_from_spectrum(evals, tol=TOL):
    return int(torch.sum(evals > tol).item())


# =====================================================================
# ENTROPY FAMILIES
# =====================================================================

def von_neumann_entropy(rho):
    evals = spectrum(rho)
    nz = evals[evals > TOL]
    if nz.numel() == 0:
        return 0.0
    return float((-torch.sum(nz * torch.log2(nz))).item())


def renyi_entropy(rho, alpha):
    evals = spectrum(rho)
    if abs(alpha - 1.0) < 1e-12:
        return von_neumann_entropy(rho)
    if abs(alpha) < 1e-12:
        return float(math.log2(rank_from_spectrum(evals)))
    moment = torch.sum(evals.pow(alpha))
    return float((torch.log2(moment) / (1.0 - alpha)).item())


def tsallis_entropy(rho, q):
    evals = spectrum(rho)
    if abs(q - 1.0) < 1e-12:
        return von_neumann_entropy(rho)
    moment = torch.sum(evals.pow(q))
    return float(((1.0 - moment) / ((q - 1.0) * LN2)).item())


def linear_entropy(rho):
    evals = spectrum(rho)
    return float((1.0 - torch.sum(evals * evals)).item())


def hartley_entropy(rho):
    evals = spectrum(rho)
    return float(math.log2(rank_from_spectrum(evals)))


def collision_entropy(rho):
    evals = spectrum(rho)
    moment2 = torch.sum(evals * evals)
    return float((-torch.log2(moment2)).item())


def entropy_family_report(rho, alpha_sweep, q_sweep):
    return {
        "von_neumann": von_neumann_entropy(rho),
        "renyi": {str(a): renyi_entropy(rho, a) for a in alpha_sweep},
        "tsallis": {str(q): tsallis_entropy(rho, q) for q in q_sweep},
        "linear": linear_entropy(rho),
        "hartley": hartley_entropy(rho),
        "collision": collision_entropy(rho),
        "rank": rank_from_spectrum(spectrum(rho)),
    }


# =====================================================================
# TEST HELPERS
# =====================================================================

def close(a, b, tol=1e-10):
    return abs(float(a) - float(b)) <= tol


def monotone_nonincreasing(values, tol=1e-10):
    return all(values[i + 1] <= values[i] + tol for i in range(len(values) - 1))


def run_positive_tests():
    results = {}

    pure = pure_state_density(torch.tensor([1.0, 0.0], dtype=torch.complex128))
    alpha_sweep = [0.0, 0.5, 1.0, 2.0, 3.0]
    q_sweep = [0.5, 1.0, 2.0, 3.0]
    pure_report = entropy_family_report(pure, alpha_sweep, q_sweep)
    results["pure_state_zero_entropy"] = {
        "pass": (
            close(pure_report["von_neumann"], 0.0)
            and all(close(v, 0.0) for v in pure_report["renyi"].values())
            and all(close(v, 0.0) for v in pure_report["tsallis"].values())
            and close(pure_report["linear"], 0.0)
            and close(pure_report["hartley"], 0.0)
            and close(pure_report["collision"], 0.0)
        ),
        "details": pure_report,
    }

    mixed = maximally_mixed_density(2)
    mixed_report = entropy_family_report(mixed, alpha_sweep, q_sweep)
    results["maximally_mixed_qubit_saturates_one_bit"] = {
        "pass": (
            close(mixed_report["von_neumann"], 1.0)
            and all(close(v, 1.0) for v in mixed_report["renyi"].values())
            and close(mixed_report["hartley"], 1.0)
            and close(mixed_report["collision"], 1.0)
            and close(mixed_report["linear"], 0.5)
        ),
        "details": mixed_report,
    }

    diag = diagonal_density([0.8, 0.2])
    diag_report = entropy_family_report(diag, alpha_sweep, q_sweep)
    renyi_trace = [diag_report["renyi"][str(a)] for a in alpha_sweep]
    tsallis_trace = [diag_report["tsallis"][str(q)] for q in q_sweep]
    results["renyi_sweep_is_nonincreasing"] = {
        "pass": monotone_nonincreasing(renyi_trace),
        "alpha_sweep": alpha_sweep,
        "renyi_trace": renyi_trace,
    }
    results["tsallis_q1_matches_von_neumann"] = {
        "pass": close(diag_report["tsallis"]["1.0"], diag_report["von_neumann"]),
        "tsallis_q1": diag_report["tsallis"]["1.0"],
        "von_neumann": diag_report["von_neumann"],
    }
    results["collision_equals_renyi_two"] = {
        "pass": close(diag_report["collision"], diag_report["renyi"]["2.0"]),
        "collision": diag_report["collision"],
        "renyi_alpha_2": diag_report["renyi"]["2.0"],
    }

    results["hartley_equals_log_rank"] = {
        "pass": close(diag_report["hartley"], math.log2(diag_report["rank"])),
        "hartley": diag_report["hartley"],
        "rank": diag_report["rank"],
    }

    return results


def run_negative_tests():
    results = {}

    pure = pure_state_density(torch.tensor([1.0, 0.0], dtype=torch.complex128))
    mixed = diagonal_density([0.8, 0.2])

    results["pure_state_not_positive_entropy"] = {
        "pass": not (von_neumann_entropy(pure) > 1e-9),
        "von_neumann": von_neumann_entropy(pure),
    }
    results["mixed_state_not_zero_entropy"] = {
        "pass": not close(von_neumann_entropy(mixed), 0.0),
        "von_neumann": von_neumann_entropy(mixed),
    }
    results["reversed_renyi_order_is_false"] = {
        "pass": not (renyi_entropy(mixed, 0.5) < renyi_entropy(mixed, 2.0)),
        "renyi_alpha_05": renyi_entropy(mixed, 0.5),
        "renyi_alpha_2": renyi_entropy(mixed, 2.0),
    }
    results["collision_is_not_linear_entropy"] = {
        "pass": not close(collision_entropy(mixed), linear_entropy(mixed)),
        "collision": collision_entropy(mixed),
        "linear": linear_entropy(mixed),
    }

    return results


def run_boundary_tests():
    results = {}

    mixed = diagonal_density([0.7, 0.3])
    results["alpha_one_limit"] = {
        "pass": close(renyi_entropy(mixed, 1.0), von_neumann_entropy(mixed)),
        "renyi_alpha_1": renyi_entropy(mixed, 1.0),
        "von_neumann": von_neumann_entropy(mixed),
    }
    results["alpha_zero_limit"] = {
        "pass": close(renyi_entropy(mixed, 0.0), hartley_entropy(mixed)),
        "renyi_alpha_0": renyi_entropy(mixed, 0.0),
        "hartley": hartley_entropy(mixed),
    }
    results["q_one_limit"] = {
        "pass": close(tsallis_entropy(mixed, 1.0), von_neumann_entropy(mixed)),
        "tsallis_q_1": tsallis_entropy(mixed, 1.0),
        "von_neumann": von_neumann_entropy(mixed),
    }
    results["q_two_linear_relation"] = {
        "pass": close(tsallis_entropy(mixed, 2.0) * LN2, linear_entropy(mixed)),
        "tsallis_q_2": tsallis_entropy(mixed, 2.0),
        "linear": linear_entropy(mixed),
        "scaled_tsallis_q_2": tsallis_entropy(mixed, 2.0) * LN2,
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("Running spectral entropy family sim...")
    t_start = time.time()

    try:
        positive = run_positive_tests()
        negative = run_negative_tests()
        boundary = run_boundary_tests()
        ok = True
        err = None
    except Exception as exc:
        positive = {}
        negative = {}
        boundary = {}
        ok = False
        err = {"error": str(exc), "traceback": traceback.format_exc()}

    def count_passes(section):
        total = sum(1 for v in section.values() if isinstance(v, dict) and "pass" in v)
        passed = sum(1 for v in section.values() if isinstance(v, dict) and v.get("pass"))
        return passed, total

    p_pass, p_total = count_passes(positive)
    n_pass, n_total = count_passes(negative)
    b_pass, b_total = count_passes(boundary)

    results = {
        "name": "Spectral Entropy Families on Density Matrices",
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
            "all_pass": ok and p_pass == p_total and n_pass == n_total and b_pass == b_total,
            "total_time_s": time.time() - t_start,
        },
    }
    if err is not None:
        results["error"] = err

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "lego_entropy_spectral_families_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults written to {out_path}")
    print(f"Positive: {p_pass}/{p_total}  Negative: {n_pass}/{n_total}  Boundary: {b_pass}/{b_total}")
    if results["summary"]["all_pass"]:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED -- check results JSON")
