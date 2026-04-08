#!/usr/bin/env python3
"""
PURE LEGO: Entropy Inequalities and Stability Bounds
====================================================
Core entropy inequalities for simple quantum states:
  - Subadditivity
  - Araki-Lieb
  - Strong subadditivity
  - Fannes/Audenaert-style continuity bound

The examples are simple 3-qubit and 2-qubit states:
  - product
  - Bell-pair tensor ancilla
  - GHZ
  - W
  - GHZ + white noise

Caveat:
  The continuity check uses the standard Audenaert bound
  |S(rho) - S(sigma)| <= T log2(d-1) + h2(T)
  where T = 1/2 ||rho - sigma||_1 and d is the Hilbert-space dimension.
  This is a finite-dimensional bound and is only asserted numerically
  on representative state pairs here.
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
# BASIC HELPERS
# =====================================================================

def normalize_rho(rho):
    rho = 0.5 * (rho + rho.conj().T)
    tr = np.trace(rho)
    if abs(tr) < EPS:
        raise ValueError("trace too small")
    return rho / tr


def psi_to_rho(psi):
    psi = np.asarray(psi, dtype=complex).reshape(8, 1)
    return normalize_rho(psi @ psi.conj().T)


def bits3(idx):
    return ((idx >> 2) & 1, (idx >> 1) & 1, idx & 1)


def idx_from_bits(bits):
    b0, b1, b2 = bits
    return (b0 << 2) | (b1 << 1) | b2


def reduced_density_3q(rho, keep):
    """Partial trace over the complement of `keep` for a 3-qubit rho."""
    keep = list(keep)
    trace_over = [q for q in (0, 1, 2) if q not in keep]
    dim = 2 ** len(keep)
    red = np.zeros((dim, dim), dtype=complex)
    for i in range(8):
        bi = bits3(i)
        for j in range(8):
            bj = bits3(j)
            if all(bi[q] == bj[q] for q in trace_over):
                oi = idx_from_bits([bi[q] for q in keep] + [0] * (3 - len(keep)))
                oj = idx_from_bits([bj[q] for q in keep] + [0] * (3 - len(keep)))
                # The helper above expects 3 bits; use the retained bits only.
                # Recompute compact indices directly for the retained subsystem.
                oi = 0
                oj = 0
                for bit in [bi[q] for q in keep]:
                    oi = (oi << 1) | int(bit)
                for bit in [bj[q] for q in keep]:
                    oj = (oj << 1) | int(bit)
                red[oi, oj] += rho[i, j]
    return normalize_rho(red)


def von_neumann_entropy(rho):
    evals = np.clip(np.linalg.eigvalsh(normalize_rho(rho)), 0.0, None)
    nz = evals[evals > EPS]
    return float(-np.sum(nz * np.log2(nz))) if len(nz) else 0.0


def shannon_entropy(p):
    p = np.asarray(p, dtype=float)
    p = p[p > EPS]
    return float(-np.sum(p * np.log2(p))) if len(p) else 0.0


def trace_distance(rho, sigma):
    delta = normalize_rho(rho) - normalize_rho(sigma)
    evals = np.linalg.eigvalsh(0.5 * (delta + delta.conj().T))
    return float(0.5 * np.sum(np.abs(evals)))


def audenaert_bound(delta, d):
    """Audenaert/Fannes-style entropy continuity bound in bits."""
    delta = float(max(0.0, min(delta, 1.0)))
    if d <= 1:
        return 0.0
    if d == 2:
        base = 0.0
    else:
        base = delta * np.log2(d - 1)
    if delta <= EPS or delta >= 1.0:
        return float(base)
    h2 = -delta * np.log2(delta) - (1.0 - delta) * np.log2(1.0 - delta)
    return float(base + h2)


def pure_state(label):
    psi = np.zeros(8, dtype=complex)
    if label == "product_000":
        psi[0] = 1.0
    elif label == "bell_ab_tensor_0":
        psi[0] = 1.0 / np.sqrt(2)
        psi[6] = 1.0 / np.sqrt(2)
    elif label == "ghz":
        psi[0] = 1.0 / np.sqrt(2)
        psi[7] = 1.0 / np.sqrt(2)
    elif label == "w":
        psi[1] = psi[2] = psi[4] = 1.0 / np.sqrt(3)
    else:
        raise ValueError(label)
    return psi


def ghz_white_noise(p):
    ghz = psi_to_rho(pure_state("ghz"))
    return normalize_rho(p * ghz + (1.0 - p) * np.eye(8, dtype=complex) / 8.0)


def two_qubit_bell_noise(p):
    psi = np.array([1.0, 0.0, 0.0, 1.0], dtype=complex) / np.sqrt(2)
    bell = np.outer(psi, psi.conj())
    return normalize_rho(p * bell + (1.0 - p) * np.eye(4, dtype=complex) / 4.0)


def bell_state_2q():
    psi = np.array([1.0, 0.0, 0.0, 1.0], dtype=complex) / np.sqrt(2)
    return np.outer(psi, psi.conj())


def entropies_3q(rho):
    sA = von_neumann_entropy(reduced_density_3q(rho, [0]))
    sB = von_neumann_entropy(reduced_density_3q(rho, [1]))
    sC = von_neumann_entropy(reduced_density_3q(rho, [2]))
    sAB = von_neumann_entropy(reduced_density_3q(rho, [0, 1]))
    sAC = von_neumann_entropy(reduced_density_3q(rho, [0, 2]))
    sBC = von_neumann_entropy(reduced_density_3q(rho, [1, 2]))
    sABC = von_neumann_entropy(rho)
    return {
        "A": sA,
        "B": sB,
        "C": sC,
        "AB": sAB,
        "AC": sAC,
        "BC": sBC,
        "ABC": sABC,
    }


def subadditivity_gap(rho, keep_left, keep_right):
    union = sorted(set(keep_left) | set(keep_right))
    s_left = von_neumann_entropy(reduced_density_3q(rho, keep_left))
    s_right = von_neumann_entropy(reduced_density_3q(rho, keep_right))
    s_union = von_neumann_entropy(reduced_density_3q(rho, union))
    return float(s_left + s_right - s_union)


def araki_lieb_gap(rho, keep_left, keep_right):
    union = sorted(set(keep_left) | set(keep_right))
    s_left = von_neumann_entropy(reduced_density_3q(rho, keep_left))
    s_right = von_neumann_entropy(reduced_density_3q(rho, keep_right))
    s_union = von_neumann_entropy(reduced_density_3q(rho, union))
    return float(s_union - abs(s_left - s_right))


def conditional_mutual_information(rho, a, b, c):
    s_ab = von_neumann_entropy(reduced_density_3q(rho, sorted([a, b])))
    s_bc = von_neumann_entropy(reduced_density_3q(rho, sorted([b, c])))
    s_b = von_neumann_entropy(reduced_density_3q(rho, [b]))
    s_abc = von_neumann_entropy(rho)
    return float(s_ab + s_bc - s_b - s_abc)


def three_party_information(rho):
    s = entropies_3q(rho)
    return float(s["A"] + s["B"] + s["C"] - s["AB"] - s["AC"] - s["BC"] + s["ABC"])


def single_qubit_entropy_pair(rho, a, b):
    return (
        von_neumann_entropy(reduced_density_3q(rho, [a])),
        von_neumann_entropy(reduced_density_3q(rho, [b])),
    )


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    t0 = time.time()
    results = {}

    states = {
        "product_000": psi_to_rho(pure_state("product_000")),
        "bell_ab_tensor_0": psi_to_rho(pure_state("bell_ab_tensor_0")),
        "ghz": psi_to_rho(pure_state("ghz")),
        "w": psi_to_rho(pure_state("w")),
        "ghz_noise_0p8": ghz_white_noise(0.8),
    }

    structure = {}
    for name, rho in states.items():
        s = entropies_3q(rho)
        structure[name] = {
            "entropies": s,
            "subadditivity_gaps": {
                "A|B": subadditivity_gap(rho, [0], [1]),
                "A|C": subadditivity_gap(rho, [0], [2]),
                "B|C": subadditivity_gap(rho, [1], [2]),
            },
            "araki_lieb_gaps": {
                "A|B": araki_lieb_gap(rho, [0], [1]),
                "A|C": araki_lieb_gap(rho, [0], [2]),
                "B|C": araki_lieb_gap(rho, [1], [2]),
            },
            "ssa_cmi": {
                "A|B|C": conditional_mutual_information(rho, 0, 1, 2),
                "A|C|B": conditional_mutual_information(rho, 0, 2, 1),
                "B|A|C": conditional_mutual_information(rho, 1, 0, 2),
            },
            "tripartite_information": three_party_information(rho),
        }

    results["state_structure"] = structure

    exact_checks = {
        "product_saturates_subadditivity": (
            np.isclose(structure["product_000"]["subadditivity_gaps"]["A|B"], 0.0, atol=1e-12)
            and np.isclose(structure["product_000"]["subadditivity_gaps"]["A|C"], 0.0, atol=1e-12)
            and np.isclose(structure["product_000"]["subadditivity_gaps"]["B|C"], 0.0, atol=1e-12)
        ),
        "product_saturates_araki_lieb": (
            np.isclose(structure["product_000"]["araki_lieb_gaps"]["A|B"], 0.0, atol=1e-12)
            and np.isclose(structure["product_000"]["araki_lieb_gaps"]["A|C"], 0.0, atol=1e-12)
            and np.isclose(structure["product_000"]["araki_lieb_gaps"]["B|C"], 0.0, atol=1e-12)
        ),
        "ghz_single_qubit_entropy_one": all(np.isclose(v, 1.0, atol=1e-12) for v in [structure["ghz"]["entropies"]["A"], structure["ghz"]["entropies"]["B"], structure["ghz"]["entropies"]["C"]]),
        "ghz_cut_entropy_one": all(np.isclose(v, 1.0, atol=1e-12) for v in [structure["ghz"]["entropies"]["AB"], structure["ghz"]["entropies"]["AC"], structure["ghz"]["entropies"]["BC"]]),
        "ghz_ssa_positive": all(v >= -1e-12 for v in structure["ghz"]["ssa_cmi"].values()),
        "w_symmetry": (
            np.allclose(
                [structure["w"]["entropies"]["A"], structure["w"]["entropies"]["B"], structure["w"]["entropies"]["C"]],
                structure["w"]["entropies"]["A"],
                atol=1e-12,
            )
            and np.allclose(
                [structure["w"]["ssa_cmi"]["A|B|C"], structure["w"]["ssa_cmi"]["A|C|B"], structure["w"]["ssa_cmi"]["B|A|C"]],
                structure["w"]["ssa_cmi"]["A|B|C"],
                atol=1e-12,
            )
        ),
    }

    results["exact_checks"] = exact_checks

    continuity_trace = []

    ghz_rho = states["ghz"]
    ghz_sigma = ghz_white_noise(0.98)
    delta_full = trace_distance(ghz_rho, ghz_sigma)
    gap_full = abs(von_neumann_entropy(ghz_rho) - von_neumann_entropy(ghz_sigma))
    bound_full = audenaert_bound(delta_full, 8)
    delta_red = trace_distance(reduced_density_3q(ghz_rho, [0]), reduced_density_3q(ghz_sigma, [0]))
    gap_red = abs(
        von_neumann_entropy(reduced_density_3q(ghz_rho, [0]))
        - von_neumann_entropy(reduced_density_3q(ghz_sigma, [0]))
    )
    bound_red = audenaert_bound(delta_red, 2)
    continuity_trace.append(
        {
            "label": "ghz_vs_ghz_noise_0p98",
            "full_delta": delta_full,
            "full_entropy_gap": gap_full,
            "full_bound": bound_full,
            "full_pass": gap_full <= bound_full + 1e-12,
            "reduced_delta": delta_red,
            "reduced_entropy_gap": gap_red,
            "reduced_bound": bound_red,
            "reduced_pass": gap_red <= bound_red + 1e-12,
        }
    )

    bell_rho = bell_state_2q()
    bell_sigma = two_qubit_bell_noise(0.92)
    delta_bell = trace_distance(bell_rho, bell_sigma)
    gap_bell = abs(von_neumann_entropy(bell_rho) - von_neumann_entropy(bell_sigma))
    bound_bell = audenaert_bound(delta_bell, 4)
    continuity_trace.append(
        {
            "label": "bell_vs_bell_noise_0p92",
            "full_delta": delta_bell,
            "full_entropy_gap": gap_bell,
            "full_bound": bound_bell,
            "full_pass": gap_bell <= bound_bell + 1e-12,
            "reduced_delta": None,
            "reduced_entropy_gap": None,
            "reduced_bound": None,
            "reduced_pass": True,
        }
    )

    results["continuity_trace"] = continuity_trace
    continuity_pass = all(item["full_pass"] and item["reduced_pass"] for item in continuity_trace)

    neg = {
        "subadditivity_strict_on_product": {
            "claim": "Product state must have a strict subadditivity gap.",
            "gap_A|B": structure["product_000"]["subadditivity_gaps"]["A|B"],
            "gap_A|C": structure["product_000"]["subadditivity_gaps"]["A|C"],
            "gap_B|C": structure["product_000"]["subadditivity_gaps"]["B|C"],
            "claim_holds": bool(
                structure["product_000"]["subadditivity_gaps"]["A|B"] > 1e-12
                and structure["product_000"]["subadditivity_gaps"]["A|C"] > 1e-12
                and structure["product_000"]["subadditivity_gaps"]["B|C"] > 1e-12
            ),
            "pass": bool(
                abs(structure["product_000"]["subadditivity_gaps"]["A|B"]) <= 1e-12
                and abs(structure["product_000"]["subadditivity_gaps"]["A|C"]) <= 1e-12
                and abs(structure["product_000"]["subadditivity_gaps"]["B|C"]) <= 1e-12
            ),
        },
        "ghz_violates_ssa": {
            "claim": "GHZ state has negative conditional mutual information.",
            "ssa_cmi": structure["ghz"]["ssa_cmi"],
            "claim_holds": bool(any(v < -1e-12 for v in structure["ghz"]["ssa_cmi"].values())),
            "pass": bool(all(v >= -1e-12 for v in structure["ghz"]["ssa_cmi"].values())),
        },
        "continuity_bound_fails_on_nearby_states": {
            "claim": "Audenaert-style continuity bound is violated by a nearby GHZ/noisy pair.",
            "trace_distance": continuity_trace[0]["full_delta"],
            "entropy_gap": continuity_trace[0]["full_entropy_gap"],
            "bound": continuity_trace[0]["full_bound"],
            "claim_holds": bool(continuity_trace[0]["full_entropy_gap"] > continuity_trace[0]["full_bound"] + 1e-12),
            "pass": bool(continuity_trace[0]["full_entropy_gap"] <= continuity_trace[0]["full_bound"] + 1e-12),
        },
    }
    results["negative"] = neg

    results["pass"] = bool(all(exact_checks.values()) and continuity_pass and all(v["pass"] for v in neg.values()))
    results["elapsed_s"] = time.time() - t0
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    product = psi_to_rho(pure_state("product_000"))
    bell = psi_to_rho(pure_state("bell_ab_tensor_0"))
    ghz = psi_to_rho(pure_state("ghz"))
    nearly_pure = ghz_white_noise(0.99)

    boundary = {
        "product_saturates_exactly": {
            "entropies": entropies_3q(product),
            "subadditivity_gaps": {
                "A|B": subadditivity_gap(product, [0], [1]),
                "A|C": subadditivity_gap(product, [0], [2]),
                "B|C": subadditivity_gap(product, [1], [2]),
            },
            "ssa_cmi": {
                "A|B|C": conditional_mutual_information(product, 0, 1, 2),
                "A|C|B": conditional_mutual_information(product, 0, 2, 1),
                "B|A|C": conditional_mutual_information(product, 1, 0, 2),
            },
            "pass": bool(
                all(np.isclose(v, 0.0, atol=1e-12) for v in entropies_3q(product).values())
                and all(np.isclose(v, 0.0, atol=1e-12) for v in [
                    subadditivity_gap(product, [0], [1]),
                    subadditivity_gap(product, [0], [2]),
                    subadditivity_gap(product, [1], [2]),
                    araki_lieb_gap(product, [0], [1]),
                    araki_lieb_gap(product, [0], [2]),
                    araki_lieb_gap(product, [1], [2]),
                    conditional_mutual_information(product, 0, 1, 2),
                ])
            ),
        },
        "bell_pair_tensor_ancilla_boundary": {
            "entropies": entropies_3q(bell),
            "cut_entropies": {
                "A|BC": von_neumann_entropy(reduced_density_3q(bell, [0])),
                "B|AC": von_neumann_entropy(reduced_density_3q(bell, [1])),
                "C|AB": von_neumann_entropy(reduced_density_3q(bell, [2])),
            },
            "negativities": {
                "A|BC": trace_distance(reduced_density_3q(bell, [0]), reduced_density_3q(bell, [0])),
                "B|AC": trace_distance(reduced_density_3q(bell, [1]), reduced_density_3q(bell, [1])),
                "C|AB": trace_distance(reduced_density_3q(bell, [2]), reduced_density_3q(bell, [2])),
            },
            "pass": bool(
                np.isclose(von_neumann_entropy(reduced_density_3q(bell, [2])), 0.0, atol=1e-12)
                and np.isclose(von_neumann_entropy(reduced_density_3q(bell, [0])), 1.0, atol=1e-12)
                and np.isclose(von_neumann_entropy(reduced_density_3q(bell, [1])), 1.0, atol=1e-12)
            ),
        },
        "ghz_maximally_balanced": {
            "entropies": entropies_3q(ghz),
            "tripartite_information": three_party_information(ghz),
            "pass": bool(
                all(np.isclose(v, 1.0, atol=1e-12) for v in [entropies_3q(ghz)["A"], entropies_3q(ghz)["B"], entropies_3q(ghz)["C"]])
                and all(np.isclose(v, 1.0, atol=1e-12) for v in [entropies_3q(ghz)["AB"], entropies_3q(ghz)["AC"], entropies_3q(ghz)["BC"]])
            ),
        },
        "near_identity_continuity": {
            "state_p": 0.99,
            "trace_distance": trace_distance(ghz, nearly_pure),
            "entropy_gap": abs(von_neumann_entropy(ghz) - von_neumann_entropy(nearly_pure)),
            "bound": audenaert_bound(trace_distance(ghz, nearly_pure), 8),
            "pass": bool(abs(von_neumann_entropy(ghz) - von_neumann_entropy(nearly_pure)) <= audenaert_bound(trace_distance(ghz, nearly_pure), 8) + 1e-12),
        },
    }
    boundary["pass"] = all(v["pass"] for v in boundary.values())
    return boundary


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = positive["negative"]
    boundary = run_boundary_tests()

    sections = (positive, negative, boundary)
    all_tests = {}
    for section in sections:
        for name, test in section.items():
            if isinstance(test, dict) and "pass" in test:
                all_tests[name] = bool(test["pass"])

    results = {
        "name": "lego_entropy_inequalities_stability",
        "schema": "lego_entropy_inequalities_stability/v1",
        "description": (
            "Pure-math entropy lego for subadditivity, Araki-Lieb, SSA, "
            "and Audenaert-style continuity bounds on simple quantum states."
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
    out_path = os.path.join(out_dir, "lego_entropy_inequalities_stability_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Results written to {out_path}")
    print(f"Tests: {results['summary']['passed']}/{results['summary']['total_tests']} passed")
    print("ALL PASS" if results["summary"]["all_pass"] else "FAILED")
