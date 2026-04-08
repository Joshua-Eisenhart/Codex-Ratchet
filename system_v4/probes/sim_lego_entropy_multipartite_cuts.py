#!/usr/bin/env python3
"""
PURE LEGO: Multipartite Cut Entropy on 3-Qubit States
=====================================================
Pure-math lego for 3-qubit entropy structure.

Targets:
  - Reduced entropies on all single-qubit and two-qubit cuts
  - Cut entanglement entropy for pure states across A|BC, B|AC, C|AB
  - Schmidt/entanglement spectrum on pure cuts
  - Tripartite mutual-information style quantity
  - Negativity and log-negativity for multipartite noisy examples
  - GHZ / W / Bell-pair / product examples
  - GHZ + white-noise threshold check across bipartite cuts

The noisy example is a simple multipartite Werner-like family:
  rho(p) = p |GHZ><GHZ| + (1-p) I/8
For this family, the cut negativity across each 1|23 bipartition
is checked against the exact closed form max(0, (5p - 1)/8).
"""

import json
import os
import time

import numpy as np

np.random.seed(42)
EPS = 1e-12

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pure-math numpy baseline"},
    "pyg": {"tried": False, "used": False, "reason": "pure-math numpy baseline"},
    "z3": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "clifford": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for this lego"},
}


# =====================================================================
# HELPERS
# =====================================================================

def normalize_rho(rho):
    rho = 0.5 * (rho + rho.conj().T)
    tr = np.trace(rho)
    if abs(tr) < EPS:
        raise ValueError("trace too small")
    return rho / tr


def rho_from_psi(psi):
    psi = np.asarray(psi, dtype=complex).reshape(8, 1)
    return normalize_rho(psi @ psi.conj().T)


def pure_state(label):
    if label == "product_000":
        psi = np.zeros(8, dtype=complex)
        psi[0] = 1.0
    elif label == "ghz":
        psi = np.zeros(8, dtype=complex)
        psi[0] = 1.0 / np.sqrt(2)
        psi[7] = 1.0 / np.sqrt(2)
    elif label == "w":
        psi = np.zeros(8, dtype=complex)
        psi[1] = psi[2] = psi[4] = 1.0 / np.sqrt(3)
    elif label == "bell_ab_tensor_0":
        psi = np.zeros(8, dtype=complex)
        psi[0] = 1.0 / np.sqrt(2)
        psi[6] = 1.0 / np.sqrt(2)
    else:
        raise ValueError(label)
    return psi


def ghz_white_noise(p):
    ghz = rho_from_psi(pure_state("ghz"))
    return normalize_rho(p * ghz + (1.0 - p) * np.eye(8, dtype=complex) / 8.0)


def reduced_density(rho, keep):
    """Reduced density matrix for a 3-qubit state keeping qubits in `keep`."""
    keep = list(keep)
    bra = ["a", "b", "c"]
    ket = ["d", "e", "f"]
    for q in range(3):
        if q not in keep:
            ket[q] = bra[q]
    subs_in = "".join(bra + ket)
    subs_out = "".join([bra[q] for q in keep] + [ket[q] for q in keep])
    red = np.einsum(f"{subs_in}->{subs_out}", rho.reshape(2, 2, 2, 2, 2, 2))
    dim = 2 ** len(keep)
    return normalize_rho(red.reshape(dim, dim))


def von_neumann_entropy(rho):
    evals = np.clip(np.linalg.eigvalsh(normalize_rho(rho)), 0.0, None)
    nz = evals[evals > EPS]
    return float(-np.sum(nz * np.log2(nz))) if len(nz) else 0.0


def single_qubit_reduced_entropies(rho):
    return {
        "A": von_neumann_entropy(reduced_density(rho, [0])),
        "B": von_neumann_entropy(reduced_density(rho, [1])),
        "C": von_neumann_entropy(reduced_density(rho, [2])),
    }


def pair_reduced_entropies(rho):
    return {
        "AB": von_neumann_entropy(reduced_density(rho, [0, 1])),
        "AC": von_neumann_entropy(reduced_density(rho, [0, 2])),
        "BC": von_neumann_entropy(reduced_density(rho, [1, 2])),
    }


def entanglement_spectrum_cut(rho, keep):
    evals = np.real(np.linalg.eigvalsh(reduced_density(rho, keep)))
    evals = np.clip(evals, 0.0, None)
    evals = np.sort(evals)[::-1]
    return [float(x) for x in evals]


def cut_entropy_pure(rho, keep):
    return von_neumann_entropy(reduced_density(rho, keep))


def tripartite_mutual_information(rho):
    sA = von_neumann_entropy(reduced_density(rho, [0]))
    sB = von_neumann_entropy(reduced_density(rho, [1]))
    sC = von_neumann_entropy(reduced_density(rho, [2]))
    sAB = von_neumann_entropy(reduced_density(rho, [0, 1]))
    sAC = von_neumann_entropy(reduced_density(rho, [0, 2]))
    sBC = von_neumann_entropy(reduced_density(rho, [1, 2]))
    sABC = von_neumann_entropy(rho)
    return float(sA + sB + sC - sAB - sAC - sBC + sABC)


def partial_transpose(rho, sys):
    """Partial transpose on qubit sys in a 3-qubit state."""
    t = rho.reshape(2, 2, 2, 2, 2, 2)
    if sys == 0:
        pt = t.transpose(3, 1, 2, 0, 4, 5)
    elif sys == 1:
        pt = t.transpose(0, 4, 2, 3, 1, 5)
    elif sys == 2:
        pt = t.transpose(0, 1, 5, 3, 4, 2)
    else:
        raise ValueError(sys)
    return normalize_rho(pt.reshape(8, 8))


def negativity_cut(rho, sys):
    pt = partial_transpose(rho, sys)
    evals = np.linalg.eigvalsh(pt)
    return float(max(0.0, (np.sum(np.abs(evals)) - 1.0) / 2.0))


def log_negativity_cut(rho, sys):
    pt = partial_transpose(rho, sys)
    evals = np.linalg.eigvalsh(pt)
    trace_norm = max(np.sum(np.abs(evals)), 1.0)
    return float(np.log2(trace_norm))


def ghz_white_noise_negativity_expected(p):
    return max(0.0, (5.0 * p - 1.0) / 8.0)


def ghz_white_noise_logneg_expected(p):
    n = ghz_white_noise_negativity_expected(p)
    return float(np.log2(1.0 + 2.0 * n))


def max_abs_diff(a, b):
    return float(np.max(np.abs(np.asarray(a) - np.asarray(b))))


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}
    t0 = time.time()

    examples = {
        "product_000": rho_from_psi(pure_state("product_000")),
        "ghz": rho_from_psi(pure_state("ghz")),
        "w": rho_from_psi(pure_state("w")),
        "bell_ab_tensor_0": rho_from_psi(pure_state("bell_ab_tensor_0")),
    }

    pure_checks = {}
    for name, rho in examples.items():
        s1 = single_qubit_reduced_entropies(rho)
        s2 = pair_reduced_entropies(rho)
        tmi = tripartite_mutual_information(rho)
        cut_ent = {
            "A|BC": cut_entropy_pure(rho, [0]),
            "B|AC": cut_entropy_pure(rho, [1]),
            "C|AB": cut_entropy_pure(rho, [2]),
        }
        cut_neg = {
            "A|BC": negativity_cut(rho, 0),
            "B|AC": negativity_cut(rho, 1),
            "C|AB": negativity_cut(rho, 2),
        }
        cut_logn = {
            "A|BC": log_negativity_cut(rho, 0),
            "B|AC": log_negativity_cut(rho, 1),
            "C|AB": log_negativity_cut(rho, 2),
        }
        pure_checks[name] = {
            "single_qubit_entropies": s1,
            "pair_entropies": s2,
            "tripartite_mutual_information": tmi,
            "cut_entropies": cut_ent,
            "cut_negativities": cut_neg,
            "cut_log_negativities": cut_logn,
        }

    # Exact value checks
    ghz = pure_checks["ghz"]
    w = pure_checks["w"]
    prod = pure_checks["product_000"]
    bell0 = pure_checks["bell_ab_tensor_0"]

    exact_checks = {
        "ghz_single_entropies_one": all(np.isclose(v, 1.0, atol=1e-12) for v in ghz["single_qubit_entropies"].values()),
        "ghz_pair_entropies_one": all(np.isclose(v, 1.0, atol=1e-12) for v in ghz["pair_entropies"].values()),
        "ghz_cut_entropy_one": all(np.isclose(v, 1.0, atol=1e-12) for v in ghz["cut_entropies"].values()),
        "ghz_tmi_zero": np.isclose(ghz["tripartite_mutual_information"], 0.0, atol=1e-12),
        "ghz_negativity_half": all(np.isclose(v, 0.5, atol=1e-12) for v in ghz["cut_negativities"].values()),
        "ghz_logneg_one": all(np.isclose(v, 1.0, atol=1e-12) for v in ghz["cut_log_negativities"].values()),
        "w_single_equal": np.allclose(list(w["single_qubit_entropies"].values()), list(w["single_qubit_entropies"].values())[0], atol=1e-12),
        "w_pair_equal": np.allclose(list(w["pair_entropies"].values()), list(w["pair_entropies"].values())[0], atol=1e-12),
        "w_cut_equal": np.allclose(list(w["cut_entropies"].values()), list(w["cut_entropies"].values())[0], atol=1e-12),
        "product_zero_all": (
            all(np.isclose(v, 0.0, atol=1e-12) for v in prod["single_qubit_entropies"].values())
            and all(np.isclose(v, 0.0, atol=1e-12) for v in prod["pair_entropies"].values())
            and np.isclose(prod["tripartite_mutual_information"], 0.0, atol=1e-12)
            and all(np.isclose(v, 0.0, atol=1e-12) for v in prod["cut_negativities"].values())
        ),
        "bell0_asymmetric_cuts": (
            np.isclose(bell0["single_qubit_entropies"]["A"], 1.0, atol=1e-12)
            and np.isclose(bell0["single_qubit_entropies"]["B"], 1.0, atol=1e-12)
            and np.isclose(bell0["single_qubit_entropies"]["C"], 0.0, atol=1e-12)
            and np.isclose(bell0["cut_negativities"]["A|BC"], 0.5, atol=1e-12)
            and np.isclose(bell0["cut_negativities"]["B|AC"], 0.5, atol=1e-12)
            and np.isclose(bell0["cut_negativities"]["C|AB"], 0.0, atol=1e-12)
        ),
    }

    results["pure_state_checks"] = pure_checks
    results["exact_checks"] = exact_checks

    noisy_trace = []
    p_grid = [0.0, 0.1, 0.2, 0.25, 0.5, 1.0]
    for p in p_grid:
        rho = ghz_white_noise(p)
        noisy_trace.append(
            {
                "p": float(p),
                "single_qubit_entropies": single_qubit_reduced_entropies(rho),
                "tripartite_mutual_information": tripartite_mutual_information(rho),
                "negativities": {
                    "A|BC": negativity_cut(rho, 0),
                    "B|AC": negativity_cut(rho, 1),
                    "C|AB": negativity_cut(rho, 2),
                },
                "log_negativities": {
                    "A|BC": log_negativity_cut(rho, 0),
                    "B|AC": log_negativity_cut(rho, 1),
                    "C|AB": log_negativity_cut(rho, 2),
                },
                "expected_negativity": ghz_white_noise_negativity_expected(p),
                "expected_log_negativity": ghz_white_noise_logneg_expected(p),
            }
        )

    noisy_expected_match = all(
        np.isclose(item["negativities"]["A|BC"], item["expected_negativity"], atol=1e-12)
        and np.isclose(item["negativities"]["B|AC"], item["expected_negativity"], atol=1e-12)
        and np.isclose(item["negativities"]["C|AB"], item["expected_negativity"], atol=1e-12)
        and np.isclose(item["log_negativities"]["A|BC"], item["expected_log_negativity"], atol=1e-12)
        and np.isclose(item["log_negativities"]["B|AC"], item["expected_log_negativity"], atol=1e-12)
        and np.isclose(item["log_negativities"]["C|AB"], item["expected_log_negativity"], atol=1e-12)
        for item in noisy_trace
    )
    noisy_monotone = all(
        noisy_trace[i + 1]["negativities"]["A|BC"] >= noisy_trace[i]["negativities"]["A|BC"] - 1e-12
        for i in range(len(noisy_trace) - 1)
    )

    results["noisy_ghz_trace"] = noisy_trace
    results["noisy_ghz_pass"] = bool(noisy_expected_match and noisy_monotone)
    results["pass"] = bool(all(exact_checks.values()) and results["noisy_ghz_pass"])
    results["elapsed_s"] = time.time() - t0
    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    product = rho_from_psi(pure_state("product_000"))
    ghz = rho_from_psi(pure_state("ghz"))
    noisy = ghz_white_noise(0.5)

    return {
        "product_state_has_nonzero_cut_entropy": {
            "claim": "Product state has nonzero entanglement entropy and negativity across a cut",
            "cut_entropy_A|BC": cut_entropy_pure(product, [0]),
            "negativity_A|BC": negativity_cut(product, 0),
            "claim_holds": bool(cut_entropy_pure(product, [0]) > EPS or negativity_cut(product, 0) > EPS),
            "pass": bool(cut_entropy_pure(product, [0]) <= EPS and negativity_cut(product, 0) <= EPS),
        },
        "ghz_is_separable": {
            "claim": "GHZ state is separable across every bipartition",
            "cut_entropy_A|BC": cut_entropy_pure(ghz, [0]),
            "negativity_A|BC": negativity_cut(ghz, 0),
            "claim_holds": bool(
                cut_entropy_pure(ghz, [0]) <= EPS and negativity_cut(ghz, 0) <= EPS
            ),
            "pass": bool(
                cut_entropy_pure(ghz, [0]) > EPS and negativity_cut(ghz, 0) > EPS
            ),
        },
        "noisy_ghz_is_separable_at_p_half": {
            "claim": "GHZ white-noise mixture at p=0.5 is separable across all cuts",
            "negativity_A|BC": negativity_cut(noisy, 0),
            "negativity_B|AC": negativity_cut(noisy, 1),
            "negativity_C|AB": negativity_cut(noisy, 2),
            "claim_holds": bool(
                negativity_cut(noisy, 0) <= EPS
                and negativity_cut(noisy, 1) <= EPS
                and negativity_cut(noisy, 2) <= EPS
            ),
            "pass": bool(
                negativity_cut(noisy, 0) > EPS
                or negativity_cut(noisy, 1) > EPS
                or negativity_cut(noisy, 2) > EPS
            ),
        },
    }


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    product = rho_from_psi(pure_state("product_000"))
    ghz = rho_from_psi(pure_state("ghz"))
    w = rho_from_psi(pure_state("w"))
    bell0 = rho_from_psi(pure_state("bell_ab_tensor_0"))
    threshold = ghz_white_noise(1.0 / 5.0)
    nearly_pure = ghz_white_noise(0.95)

    boundary = {
        "product_zero_entanglement": {
            "single_qubit_entropies": single_qubit_reduced_entropies(product),
            "pair_entropies": pair_reduced_entropies(product),
            "tripartite_mutual_information": tripartite_mutual_information(product),
            "pass": bool(
                all(np.isclose(v, 0.0, atol=1e-12) for v in single_qubit_reduced_entropies(product).values())
                and all(np.isclose(v, 0.0, atol=1e-12) for v in pair_reduced_entropies(product).values())
            ),
        },
        "ghz_max_cut_entropy": {
            "cut_entropies": {
                "A|BC": cut_entropy_pure(ghz, [0]),
                "B|AC": cut_entropy_pure(ghz, [1]),
                "C|AB": cut_entropy_pure(ghz, [2]),
            },
            "negativities": {
                "A|BC": negativity_cut(ghz, 0),
                "B|AC": negativity_cut(ghz, 1),
                "C|AB": negativity_cut(ghz, 2),
            },
            "log_negativities": {
                "A|BC": log_negativity_cut(ghz, 0),
                "B|AC": log_negativity_cut(ghz, 1),
                "C|AB": log_negativity_cut(ghz, 2),
            },
            "tripartite_mutual_information": tripartite_mutual_information(ghz),
            "pass": bool(
                all(np.isclose(v, 1.0, atol=1e-12) for v in [cut_entropy_pure(ghz, [0]), cut_entropy_pure(ghz, [1]), cut_entropy_pure(ghz, [2])])
                and all(np.isclose(v, 0.5, atol=1e-12) for v in [negativity_cut(ghz, 0), negativity_cut(ghz, 1), negativity_cut(ghz, 2)])
                and all(np.isclose(v, 1.0, atol=1e-12) for v in [log_negativity_cut(ghz, 0), log_negativity_cut(ghz, 1), log_negativity_cut(ghz, 2)])
                and np.isclose(tripartite_mutual_information(ghz), 0.0, atol=1e-12)
            ),
        },
        "w_symmetric_cut_structure": {
            "single_qubit_entropies": single_qubit_reduced_entropies(w),
            "pair_entropies": pair_reduced_entropies(w),
            "cut_entropies": {
                "A|BC": cut_entropy_pure(w, [0]),
                "B|AC": cut_entropy_pure(w, [1]),
                "C|AB": cut_entropy_pure(w, [2]),
            },
            "negativities": {
                "A|BC": negativity_cut(w, 0),
                "B|AC": negativity_cut(w, 1),
                "C|AB": negativity_cut(w, 2),
            },
            "pass": bool(
                np.allclose(list(single_qubit_reduced_entropies(w).values()), list(single_qubit_reduced_entropies(w).values())[0], atol=1e-12)
                and np.allclose(list(pair_reduced_entropies(w).values()), list(pair_reduced_entropies(w).values())[0], atol=1e-12)
                and np.allclose(list({k: cut_entropy_pure(w, [i]) for i, k in enumerate(["A|BC", "B|AC", "C|AB"])}.values()), list({k: cut_entropy_pure(w, [i]) for i, k in enumerate(["A|BC", "B|AC", "C|AB"])}.values())[0], atol=1e-12)
            ),
        },
        "bell_pair_boundary_asymmetry": {
            "single_qubit_entropies": single_qubit_reduced_entropies(bell0),
            "pair_entropies": pair_reduced_entropies(bell0),
            "cut_entropies": {
                "A|BC": cut_entropy_pure(bell0, [0]),
                "B|AC": cut_entropy_pure(bell0, [1]),
                "C|AB": cut_entropy_pure(bell0, [2]),
            },
            "negativities": {
                "A|BC": negativity_cut(bell0, 0),
                "B|AC": negativity_cut(bell0, 1),
                "C|AB": negativity_cut(bell0, 2),
            },
            "pass": bool(
                np.isclose(cut_entropy_pure(bell0, [2]), 0.0, atol=1e-12)
                and np.isclose(negativity_cut(bell0, 2), 0.0, atol=1e-12)
                and np.isclose(cut_entropy_pure(bell0, [0]), 1.0, atol=1e-12)
                and np.isclose(cut_entropy_pure(bell0, [1]), 1.0, atol=1e-12)
            ),
        },
        "werner_threshold_p_one_fifth": {
            "p": 1.0 / 5.0,
            "negativities": {
                "A|BC": negativity_cut(threshold, 0),
                "B|AC": negativity_cut(threshold, 1),
                "C|AB": negativity_cut(threshold, 2),
            },
            "log_negativities": {
                "A|BC": log_negativity_cut(threshold, 0),
                "B|AC": log_negativity_cut(threshold, 1),
                "C|AB": log_negativity_cut(threshold, 2),
            },
            "pass": bool(
                all(np.isclose(v, 0.0, atol=1e-12) for v in [negativity_cut(threshold, 0), negativity_cut(threshold, 1), negativity_cut(threshold, 2)])
                and all(np.isclose(v, 0.0, atol=1e-12) for v in [log_negativity_cut(threshold, 0), log_negativity_cut(threshold, 1), log_negativity_cut(threshold, 2)])
            ),
        },
        "nearly_pure_noise_has_small_entropy_growth": {
            "p": 0.95,
            "single_qubit_entropies": single_qubit_reduced_entropies(nearly_pure),
            "negativities": {
                "A|BC": negativity_cut(nearly_pure, 0),
                "B|AC": negativity_cut(nearly_pure, 1),
                "C|AB": negativity_cut(nearly_pure, 2),
            },
            "pass": bool(
                all(v > 0.0 for v in single_qubit_reduced_entropies(nearly_pure).values())
                and all(v > 0.0 for v in [negativity_cut(nearly_pure, 0), negativity_cut(nearly_pure, 1), negativity_cut(nearly_pure, 2)])
            ),
        },
    }
    boundary["pass"] = all(v["pass"] for v in boundary.values())
    return boundary


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    all_tests = {}
    for section in (positive, negative, boundary):
        for name, test in section.items():
            if isinstance(test, dict) and "pass" in test:
                all_tests[name] = bool(test["pass"])

    results = {
        "name": "lego_entropy_multipartite_cuts",
        "schema": "lego_entropy_multipartite_cuts/v1",
        "description": (
            "Pure-math 3-qubit lego for reduced entropies, cut entanglement "
            "entropy, entanglement spectra, tripartite mutual information, "
            "and GHZ-white-noise thresholds."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
        "summary": {
            "total_tests": len(all_tests),
            "passed": sum(1 for ok in all_tests.values() if ok),
            "failed": sum(1 for ok in all_tests.values() if not ok),
            "all_pass": all(all_tests.values()) if all_tests else False,
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "lego_entropy_multipartite_cuts_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Results written to {out_path}")
    print(f"Tests: {results['summary']['passed']}/{results['summary']['total_tests']} passed")
    print("ALL PASS" if results["summary"]["all_pass"] else "FAILED")
