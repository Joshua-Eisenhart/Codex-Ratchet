#!/usr/bin/env python3
"""
SIM LEGO: Bipartite cut entropies on rho_AB
===========================================
Pure math. Core cut-state entropy families for bipartite density matrices.

Families tested:
  - von Neumann joint entropy S(AB)
  - reduced entropies S(A), S(B)
  - conditional entropy S(A|B)
  - mutual information I(A:B)
  - coherent information I_c(A>B)

Test states:
  - product pure state |01><01|
  - Bell state |Phi+><Phi+|
  - maximally mixed state I/4
  - Werner sweep p in [0, 1]

This sim keeps to standard QIT notation only.
Classification: canonical
"""

import json
import math
import os
import time
import traceback

import torch
classification = "classical_baseline"  # auto-backfill

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": "not needed -- no graph layer in this cut-entropy lego"},
    "z3":        {"tried": False, "used": False, "reason": "not needed -- this sim uses exact spectral identities, not satisfiability search"},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed -- no synthesis or SMT constraints are required"},
    "sympy":     {"tried": False, "used": False, "reason": "not needed -- no symbolic derivation beyond closed-form spectral evaluation"},
    "clifford":  {"tried": False, "used": False, "reason": "not needed -- no geometric algebra layer in this lego"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed -- no manifold geometry or statistics here"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed -- no equivariant learning layer here"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed -- no dependency graph or lattice graph computation here"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed -- no hypergraph or simplicial complex layer here"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed -- no cell complex or filtration layer here"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed -- no persistent homology or filtration computation here"},
}

TOOL_MANIFEST["pytorch"]["tried"] = True
TOOL_MANIFEST["pytorch"]["used"] = True
TOOL_MANIFEST["pytorch"]["reason"] = (
    "Core numeric substrate: density matrices, partial trace, eigenspectra, and exact entropy evaluation"
)

# =====================================================================
# CONSTANTS
# =====================================================================

TOL = 1e-12
LN2 = math.log(2.0)
I2 = torch.eye(2, dtype=torch.complex128)
I4 = torch.eye(4, dtype=torch.complex128)
PHI_PLUS = torch.tensor([1.0, 0.0, 0.0, 1.0], dtype=torch.complex128) / math.sqrt(2.0)
PHI_PLUS_DM = torch.outer(PHI_PLUS, PHI_PLUS.conj())


# =====================================================================
# DENSITY MATRIX HELPERS
# =====================================================================

def normalize_density(rho):
    rho = (rho + rho.conj().T) / 2.0
    tr = torch.trace(rho)
    if abs(tr.item()) <= TOL:
        raise ValueError("zero-trace density matrix")
    return rho / tr


def spectrum(rho):
    herm = normalize_density(rho)
    evals = torch.linalg.eigvalsh(herm).real
    evals = torch.clamp(evals, min=0.0)
    total = torch.sum(evals)
    if float(total) <= TOL:
        raise ValueError("non-positive trace after spectrum cleanup")
    return evals / total


def ket01_density():
    psi = torch.tensor([0.0, 1.0, 0.0, 0.0], dtype=torch.complex128)
    return torch.outer(psi, psi.conj())


def bell_density():
    return PHI_PLUS_DM.clone()


def maximally_mixed_density():
    return I4 / 4.0


def werner_density(p):
    p = float(p)
    return p * PHI_PLUS_DM + (1.0 - p) * I4 / 4.0


def partial_trace_2q(rho_ab, keep):
    """
    Partial trace over one qubit of a 4x4 bipartite density matrix.
    keep = 0 keeps subsystem A, keep = 1 keeps subsystem B.
    """
    rho = rho_ab.reshape(2, 2, 2, 2)
    if keep == 0:
        return torch.einsum("abcb->ac", rho)
    if keep == 1:
        return torch.einsum("abad->bd", rho)
    raise ValueError("keep must be 0 or 1")


def entropy_from_spectrum(evals):
    nz = evals[evals > TOL]
    if nz.numel() == 0:
        return 0.0
    return float((-torch.sum(nz * torch.log2(nz))).item())


def von_neumann_entropy(rho):
    return entropy_from_spectrum(spectrum(rho))


def reduced_entropies(rho_ab):
    rho_a = partial_trace_2q(rho_ab, 0)
    rho_b = partial_trace_2q(rho_ab, 1)
    return von_neumann_entropy(rho_a), von_neumann_entropy(rho_b)


def conditional_entropy_a_given_b(rho_ab):
    s_ab = von_neumann_entropy(rho_ab)
    _, s_b = reduced_entropies(rho_ab)
    return s_ab - s_b


def mutual_information(rho_ab):
    s_a, s_b = reduced_entropies(rho_ab)
    s_ab = von_neumann_entropy(rho_ab)
    return s_a + s_b - s_ab


def coherent_information_a_to_b(rho_ab):
    s_ab = von_neumann_entropy(rho_ab)
    _, s_b = reduced_entropies(rho_ab)
    return s_b - s_ab


def sweep_werner(p_values):
    sweep = []
    for p in p_values:
        rho = werner_density(p)
        s_ab = von_neumann_entropy(rho)
        s_a, s_b = reduced_entropies(rho)
        s_agb = conditional_entropy_a_given_b(rho)
        mi = mutual_information(rho)
        ic = coherent_information_a_to_b(rho)
        sweep.append({
            "p": float(p),
            "S_AB": s_ab,
            "S_A": s_a,
            "S_B": s_b,
            "S_A_given_B": s_agb,
            "I_AB": mi,
            "I_c_A_to_B": ic,
        })
    return sweep


# =====================================================================
# TEST HELPERS
# =====================================================================

def close(a, b, tol=1e-10):
    return abs(float(a) - float(b)) <= tol


def monotone_nonincreasing(values, tol=1e-10):
    return all(values[i + 1] <= values[i] + tol for i in range(len(values) - 1))


def monotone_nondecreasing(values, tol=1e-10):
    return all(values[i + 1] >= values[i] - tol for i in range(len(values) - 1))


def validate_state(rho):
    herm = torch.max(torch.abs(rho - rho.conj().T)).item()
    tr = torch.trace(rho).real.item()
    evals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2.0).real
    return {
        "hermitian_error": float(herm),
        "trace": float(tr),
        "min_eigenvalue": float(torch.min(evals).item()),
        "valid": herm < 1e-12 and abs(tr - 1.0) < 1e-12 and torch.min(evals).item() >= -1e-10,
    }


# =====================================================================
# TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    product = ket01_density()
    bell = bell_density()
    mixed = maximally_mixed_density()
    p_values = [0.0, 0.25, 1.0 / 3.0, 0.5, 0.75, 1.0]
    sweep = sweep_werner(p_values)

    prod_va = validate_state(product)
    bell_va = validate_state(bell)
    mixed_va = validate_state(mixed)

    s_ab_prod = von_neumann_entropy(product)
    s_a_prod, s_b_prod = reduced_entropies(product)
    mi_prod = mutual_information(product)
    sa_gb_prod = conditional_entropy_a_given_b(product)
    ic_prod = coherent_information_a_to_b(product)

    results["product_state_zero_correlations"] = {
        "pass": (
            prod_va["valid"]
            and close(s_ab_prod, 0.0)
            and close(s_a_prod, 0.0)
            and close(s_b_prod, 0.0)
            and close(mi_prod, 0.0)
            and close(sa_gb_prod, 0.0)
            and close(ic_prod, 0.0)
        ),
        "state": "product |01><01|",
        "details": {
            **prod_va,
            "S_AB": s_ab_prod,
            "S_A": s_a_prod,
            "S_B": s_b_prod,
            "S_A_given_B": sa_gb_prod,
            "I_AB": mi_prod,
            "I_c_A_to_B": ic_prod,
        },
    }

    s_ab_bell = von_neumann_entropy(bell)
    s_a_bell, s_b_bell = reduced_entropies(bell)
    mi_bell = mutual_information(bell)
    sa_gb_bell = conditional_entropy_a_given_b(bell)
    ic_bell = coherent_information_a_to_b(bell)

    results["bell_state_maximal_cut_entropy_structure"] = {
        "pass": (
            bell_va["valid"]
            and close(s_ab_bell, 0.0)
            and close(s_a_bell, 1.0)
            and close(s_b_bell, 1.0)
            and close(mi_bell, 2.0)
            and close(sa_gb_bell, -1.0)
            and close(ic_bell, 1.0)
        ),
        "state": "Bell |Phi+><Phi+|",
        "details": {
            **bell_va,
            "S_AB": s_ab_bell,
            "S_A": s_a_bell,
            "S_B": s_b_bell,
            "S_A_given_B": sa_gb_bell,
            "I_AB": mi_bell,
            "I_c_A_to_B": ic_bell,
        },
    }

    s_ab_mix = von_neumann_entropy(mixed)
    s_a_mix, s_b_mix = reduced_entropies(mixed)
    mi_mix = mutual_information(mixed)
    sa_gb_mix = conditional_entropy_a_given_b(mixed)
    ic_mix = coherent_information_a_to_b(mixed)

    results["maximally_mixed_state_boundary"] = {
        "pass": (
            mixed_va["valid"]
            and close(s_ab_mix, 2.0)
            and close(s_a_mix, 1.0)
            and close(s_b_mix, 1.0)
            and close(mi_mix, 0.0)
            and close(sa_gb_mix, 1.0)
            and close(ic_mix, -1.0)
        ),
        "state": "I/4",
        "details": {
            **mixed_va,
            "S_AB": s_ab_mix,
            "S_A": s_a_mix,
            "S_B": s_b_mix,
            "S_A_given_B": sa_gb_mix,
            "I_AB": mi_mix,
            "I_c_A_to_B": ic_mix,
        },
    }

    renyi_s_a = [s["S_A"] for s in sweep]
    cond_sweep = [s["S_A_given_B"] for s in sweep]
    mi_sweep = [s["I_AB"] for s in sweep]
    ic_sweep = [s["I_c_A_to_B"] for s in sweep]
    s_ab_sweep = [s["S_AB"] for s in sweep]

    results["werner_sweep_spectral_monotonicity"] = {
        "pass": (
            monotone_nonincreasing(s_ab_sweep)
            and monotone_nondecreasing(mi_sweep)
            and monotone_nonincreasing(cond_sweep)
            and monotone_nondecreasing(ic_sweep)
        ),
        "p_values": p_values,
        "sweep": sweep,
    }

    results["werner_marginals_are_maximally_mixed"] = {
        "pass": all(close(s["S_A"], 1.0) and close(s["S_B"], 1.0) for s in sweep),
        "details": [{"p": s["p"], "S_A": s["S_A"], "S_B": s["S_B"]} for s in sweep],
    }

    return results


def run_negative_tests():
    results = {}

    product = ket01_density()
    bell = bell_density()
    mixed = maximally_mixed_density()

    results["product_state_not_negative_conditional_entropy"] = {
        "pass": not (conditional_entropy_a_given_b(product) < -1e-10),
        "S_A_given_B": conditional_entropy_a_given_b(product),
    }
    results["product_state_not_positive_mutual_information"] = {
        "pass": not (mutual_information(product) > 1e-10),
        "I_AB": mutual_information(product),
    }
    results["bell_state_not_maximally_mixed_joint_entropy"] = {
        "pass": not close(von_neumann_entropy(bell), 2.0),
        "S_AB": von_neumann_entropy(bell),
    }
    results["maximally_mixed_state_not_negative_coherent_info"] = {
        "pass": not (coherent_information_a_to_b(mixed) > -1e-10),
        "I_c_A_to_B": coherent_information_a_to_b(mixed),
    }

    return results


def run_boundary_tests():
    results = {}

    p0 = werner_density(0.0)
    p_third = werner_density(1.0 / 3.0)
    p_one = werner_density(1.0)

    results["werner_p_zero_boundary"] = {
        "pass": (
            close(von_neumann_entropy(p0), 2.0)
            and close(mutual_information(p0), 0.0)
            and close(conditional_entropy_a_given_b(p0), 1.0)
            and close(coherent_information_a_to_b(p0), -1.0)
        ),
        "details": {
            "S_AB": von_neumann_entropy(p0),
            "I_AB": mutual_information(p0),
            "S_A_given_B": conditional_entropy_a_given_b(p0),
            "I_c_A_to_B": coherent_information_a_to_b(p0),
        },
    }

    results["werner_p_third_boundary"] = {
        "pass": (
            close(reduced_entropies(p_third)[0], 1.0)
            and close(reduced_entropies(p_third)[1], 1.0)
            and close(conditional_entropy_a_given_b(p_third), von_neumann_entropy(p_third) - 1.0)
            and close(coherent_information_a_to_b(p_third), 1.0 - von_neumann_entropy(p_third))
        ),
        "details": {
            "p": 1.0 / 3.0,
            "S_AB": von_neumann_entropy(p_third),
            "S_A": reduced_entropies(p_third)[0],
            "S_B": reduced_entropies(p_third)[1],
            "S_A_given_B": conditional_entropy_a_given_b(p_third),
            "I_c_A_to_B": coherent_information_a_to_b(p_third),
        },
    }

    results["werner_p_one_boundary"] = {
        "pass": (
            close(von_neumann_entropy(p_one), 0.0)
            and close(reduced_entropies(p_one)[0], 1.0)
            and close(reduced_entropies(p_one)[1], 1.0)
            and close(mutual_information(p_one), 2.0)
            and close(conditional_entropy_a_given_b(p_one), -1.0)
            and close(coherent_information_a_to_b(p_one), 1.0)
        ),
        "details": {
            "S_AB": von_neumann_entropy(p_one),
            "S_A": reduced_entropies(p_one)[0],
            "S_B": reduced_entropies(p_one)[1],
            "I_AB": mutual_information(p_one),
            "S_A_given_B": conditional_entropy_a_given_b(p_one),
            "I_c_A_to_B": coherent_information_a_to_b(p_one),
        },
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("Running bipartite cut entropy sim...")
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
        "name": "Bipartite Cut-State Entropies",
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
    out_path = os.path.join(out_dir, "lego_entropy_bipartite_cut_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults written to {out_path}")
    print(f"Positive: {p_pass}/{p_total}  Negative: {n_pass}/{n_total}  Boundary: {b_pass}/{b_total}")
    if results["summary"]["all_pass"]:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED -- check results JSON")
