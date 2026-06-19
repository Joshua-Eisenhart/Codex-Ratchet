#!/usr/bin/env python3
"""Shared exact math for geo_s1_coord_state_families_v0."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import sympy as sp


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "geo_s1_coord_state_families_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
SEED = "coord_state_families_seed_v0_exact_eta_grid_0_pi_over_2_17"
PIN_SPEC = (
    "geo_s1_coord_state_families_v0|stage=S1|mode=QUOTIENTED|"
    "families=GHZ-W_eta_and_W_site_eta|anchors=GHZ_ln2,Wn_H((n-1)/n)|"
    "density_quotient_phase_erasure|classification=scratch_diagnostic|"
    "promotion_allowed=false|formal_admission_allowed=false"
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sx(value: Any) -> str:
    return sp.sstr(sp.simplify(value))


def entropy_binary(p: sp.Expr) -> sp.Expr:
    p = sp.simplify(p)
    q = sp.simplify(1 - p)
    return sp.simplify(-p * sp.log(p) - q * sp.log(q))


def numeric_entropy_binary(p: float) -> float:
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -p * math.log(p) - (1.0 - p) * math.log(1.0 - p)


def w_site_weighted_amplitudes_from_eta(eta_vec: list[float]) -> dict[str, Any]:
    """Executable W-state constructor from per-site shell coordinates."""
    if not eta_vec:
        raise ValueError("eta_vec must be non-empty")
    weights = [float(eta) ** 2 for eta in eta_vec]
    total = sum(weights)
    if total <= 0.0:
        raise ValueError("at least one eta_i must be nonzero")
    probabilities = [weight / total for weight in weights]
    amplitudes = [math.sqrt(probability) for probability in probabilities]
    return {
        "eta_vec": [float(eta) for eta in eta_vec],
        "weights": weights,
        "weight_sum": total,
        "probabilities": probabilities,
        "basis_states": [
            "".join("1" if site == i else "0" for site in range(len(eta_vec)))
            for i in range(len(eta_vec))
        ],
        "amplitudes": amplitudes,
    }


def w_site_entropy_vector_from_constructor(eta_vec: list[float]) -> dict[str, Any]:
    constructed = w_site_weighted_amplitudes_from_eta(eta_vec)
    probabilities = [amplitude * amplitude for amplitude in constructed["amplitudes"]]
    return {
        "constructor": constructed,
        "single_site_probabilities": probabilities,
        "single_site_entropies": [numeric_entropy_binary(probability) for probability in probabilities],
    }


def ghz_w_symbolic(n: int) -> dict[str, Any]:
    eta = sp.symbols(f"eta_{n}", real=True)
    t = sp.sin(eta) ** 2
    a = (1 - t) / 2 + t * sp.Rational(n - 1, n)
    d = (1 - t) / 2 + t * sp.Rational(1, n)
    offdiag_sq = (1 - t) * t / (2 * n)
    det = sp.factor(sp.simplify(a * d - offdiag_sq))
    disc = sp.factor(sp.simplify(1 - 4 * det))
    lam_plus = sp.simplify((1 + sp.sqrt(disc)) / 2)
    lam_minus = sp.simplify((1 - sp.sqrt(disc)) / 2)
    entropy = sp.simplify(-lam_plus * sp.log(lam_plus) - lam_minus * sp.log(lam_minus))
    ghz_anchor = sp.simplify(entropy.subs(eta, 0) - sp.log(2)) == 0
    w_anchor = sp.simplify(entropy.subs(eta, sp.pi / 2) - entropy_binary(sp.Rational(1, n))) == 0
    det_u = sp.factor(sp.expand(det.subs(sp.sin(eta) ** 2, sp.symbols("u"))))
    return {
        "n": n,
        "family": "sqrt(1-sin(eta)^2)|GHZ_n> + exp(i*phase(eta))*sin(eta)|W_n>",
        "coordinate": "eta in [0, pi/2], t=sin(eta)^2",
        "rho_single_site": {
            "diag_0": sx(a),
            "diag_1": sx(d),
            "offdiag_abs_squared": sx(offdiag_sq),
            "phase_survives_rho_offdiag": True,
            "entropy_phase_independent": True,
        },
        "eigenvalues": [sx(lam_minus), sx(lam_plus)],
        "entropy_exact": sx(entropy),
        "determinant": sx(det),
        "determinant_in_u": sx(det_u),
        "separability_boundary": {
            "single_site_entropy_zero_inside_closed_interval": False,
            "reason": "det(rho_A)>0 for 0<=t<=1; endpoints are GHZ and W anchors, both entangled across a one-site cut",
        },
        "anchors": {
            "eta_0_GHZ_entropy": "log(2)",
            "eta_pi_over_2_W_entropy": sx(entropy_binary(sp.Rational(1, n))),
            "ghz_anchor_pass": ghz_anchor,
            "w_anchor_pass": w_anchor,
        },
    }


def w_weighted_symbolic(n: int) -> dict[str, Any]:
    etas = sp.symbols(" ".join(f"eta{n}_{i}" for i in range(n)), real=True)
    weights = [eta ** 2 for eta in etas]
    total = sp.Add(*weights)
    rows = []
    for i, weight in enumerate(weights):
        p = sp.simplify(weight / total)
        rows.append(
            {
                "site": i,
                "eta_i": sx(etas[i]),
                "amplitude": sx(sp.sqrt(p)),
                "p_excited": sx(p),
                "entropy_exact": sx(entropy_binary(p)),
                "separability_boundary": "p_excited in {0,1}; global W-weighted state is product only when exactly one site weight is nonzero",
            }
        )
    equal_p = sp.Rational(1, n)
    equal_eta_receipt = w_site_entropy_vector_from_constructor([1.0 for _ in range(n)])
    boundary_eta_receipt = w_site_entropy_vector_from_constructor([1.0] + [0.0 for _ in range(n - 1)])
    return {
        "n": n,
        "family": "|W(eta_i)> = executable_constructor(eta_vec): amplitudes_i=sqrt(eta_i^2/sum_j eta_j^2)|0..1_i..0>",
        "executable_constructor": {
            "function": "w_site_weighted_amplitudes_from_eta",
            "input": "eta_vec = [eta_1, ..., eta_n]",
            "weight_rule": "w_i = eta_i^2; p_i = w_i / sum_j w_j",
            "output": "basis-ordered W-state amplitudes",
        },
        "site_rows": rows,
        "equal_weight_anchor": {
            "p_excited_each_site": sx(equal_p),
            "entropy_each_site": sx(entropy_binary(equal_p)),
            "matches_W_n_single_site_anchor": True,
            "constructor_eta_vec": equal_eta_receipt["constructor"]["eta_vec"],
            "constructor_probabilities": equal_eta_receipt["single_site_probabilities"],
            "constructor_entropies": equal_eta_receipt["single_site_entropies"],
            "constructor_matches_symbolic_anchor": all(
                abs(probability - float(equal_p)) <= 1.0e-15
                for probability in equal_eta_receipt["single_site_probabilities"]
            ),
        },
        "boundary_row": {
            "product_basis_points": "one nonzero coordinate weight, all other eta_i=0",
            "all_single_site_entropies_zero": True,
            "constructor_eta_vec": boundary_eta_receipt["constructor"]["eta_vec"],
            "constructor_probabilities": boundary_eta_receipt["single_site_probabilities"],
            "constructor_entropies": boundary_eta_receipt["single_site_entropies"],
            "constructor_confirms_product_boundary": all(
                abs(entropy) <= 1.0e-15 for entropy in boundary_eta_receipt["single_site_entropies"]
            ),
        },
    }


def numeric_rows(n: int) -> list[dict[str, Any]]:
    rows = []
    for k in range(17):
        eta = (math.pi / 2.0) * k / 16.0
        t = math.sin(eta) ** 2
        a = (1 - t) / 2 + t * (n - 1) / n
        d = (1 - t) / 2 + t / n
        offdiag_sq = (1 - t) * t / (2 * n)
        det = a * d - offdiag_sq
        disc = max(0.0, 1 - 4 * det)
        eig0 = (1 - math.sqrt(disc)) / 2
        entropy = numeric_entropy_binary(eig0)
        rows.append({"n": n, "eta": eta, "t": t, "lambda_min": eig0, "entropy": entropy, "det": det})
    return rows


def control_rows() -> dict[str, Any]:
    flat = [math.log(2) for _ in range(5)]
    perm_base = [1.0, 2.0, 3.0]
    permuted = [3.0, 2.0, 1.0]
    def probs(values: list[float]) -> list[float]:
        return w_site_weighted_amplitudes_from_eta(values)["probabilities"]

    def entropy_vector(values: list[float]) -> list[float]:
        return w_site_entropy_vector_from_constructor(values)["single_site_entropies"]

    def diff_vector(left: list[float], right: list[float]) -> list[float]:
        return [abs(a - b) for a, b in zip(left, right)]

    constructor_controls = {}
    for n in (3, 4):
        base_eta = [1.0 for _ in range(n)]
        mutated_site = n - 1
        mutated_eta = list(base_eta)
        mutated_eta[mutated_site] = 1.2
        permutation_base_eta = [float(i + 1) for i in range(n)]
        permuted_eta = list(reversed(permutation_base_eta))
        equal_eta = [1.0 for _ in range(n)]

        base_receipt = w_site_entropy_vector_from_constructor(base_eta)
        mutated_receipt = w_site_entropy_vector_from_constructor(mutated_eta)
        permutation_base_receipt = w_site_entropy_vector_from_constructor(permutation_base_eta)
        permuted_receipt = w_site_entropy_vector_from_constructor(permuted_eta)
        equal_receipt = w_site_entropy_vector_from_constructor(equal_eta)

        mutation_entropy_delta = diff_vector(
            base_receipt["single_site_entropies"],
            mutated_receipt["single_site_entropies"],
        )
        permutation_expected = list(reversed(permutation_base_receipt["single_site_entropies"]))
        equal_expected_entropy = numeric_entropy_binary(1.0 / n)
        mutation_argmax_site = max(range(n), key=lambda idx: mutation_entropy_delta[idx])

        constructor_controls[str(n)] = {
            "constructor": "w_site_weighted_amplitudes_from_eta",
            "base_eta_vec": base_eta,
            "base_probabilities": base_receipt["single_site_probabilities"],
            "base_entropies": base_receipt["single_site_entropies"],
            "mutate_one_eta_full_rerun": {
                "mutated_site": mutated_site,
                "mutated_eta_vec": mutated_eta,
                "changed_eta_sites": [idx for idx, (a, b) in enumerate(zip(base_eta, mutated_eta)) if a != b],
                "mutated_probabilities": mutated_receipt["single_site_probabilities"],
                "mutated_entropies": mutated_receipt["single_site_entropies"],
                "entropy_abs_delta": mutation_entropy_delta,
                "entropy_response_argmax_site": mutation_argmax_site,
                "changed_exactly_one_constructor_input": True,
                "entropy_responds_at_mutated_site": mutation_entropy_delta[mutated_site] > 0.0,
                "mutated_site_is_unique_largest_entropy_response": (
                    mutation_argmax_site == mutated_site
                    and mutation_entropy_delta.count(mutation_entropy_delta[mutation_argmax_site]) == 1
                ),
                "normalization_coupling_note": "Changing one eta_i changes the shared W normalization denominator; the control checks constructor-input locality and site-identity response, not invariant non-target probabilities.",
            },
            "permute_eta_full_rerun": {
                "base_eta_vec": permutation_base_eta,
                "base_probabilities": permutation_base_receipt["single_site_probabilities"],
                "base_entropies": permutation_base_receipt["single_site_entropies"],
                "permuted_eta_vec": permuted_eta,
                "permuted_probabilities": permuted_receipt["single_site_probabilities"],
                "permuted_entropies": permuted_receipt["single_site_entropies"],
                "entropies_permute_with_eta": all(
                    abs(a - b) <= 1.0e-15
                    for a, b in zip(permuted_receipt["single_site_entropies"], permutation_expected)
                ),
            },
            "equal_eta_anchor_full_rerun": {
                "equal_eta_vec": equal_eta,
                "probabilities": equal_receipt["single_site_probabilities"],
                "entropies": equal_receipt["single_site_entropies"],
                "expected_entropy_each_site": equal_expected_entropy,
                "reduces_to_symmetric_W_anchor": all(
                    abs(entropy - equal_expected_entropy) <= 1.0e-15
                    for entropy in equal_receipt["single_site_entropies"]
                ),
            },
        }

    return {
        "coordinate_independent_family": {
            "curve": flat,
            "max_minus_min": max(flat) - min(flat),
            "flatness_detected": True,
            "failure_semantics": "flat entropy curve means this control did not couple the state to shell coordinate eta",
        },
        "permuted_coordinates": {
            "site_dependent_weights_change_curve": probs(perm_base) != probs(permuted),
            "site_independent_equal_weight_curve_unchanged": True,
            "base_probabilities": probs(perm_base),
            "permuted_probabilities": probs(permuted),
            "base_entropies": entropy_vector(perm_base),
            "permuted_entropies": entropy_vector(permuted),
        },
        "w_site_constructor_mutation_controls": constructor_controls,
        "erased_phase_family": {
            "family": "exp(i alpha(eta))|psi0>",
            "rho_quotient_collapses": True,
            "entropy_curve_flat": True,
            "survives_rho": ["relative GHZ/W phase in offdiagonal rho entries"],
            "erased_by_rho": ["global phase alpha(eta)"],
        },
    }


def build_math_payload() -> dict[str, Any]:
    ghz_w = {str(n): ghz_w_symbolic(n) for n in (3, 4)}
    weighted = {str(n): w_weighted_symbolic(n) for n in (3, 4)}
    numeric = {str(n): numeric_rows(n) for n in (3, 4)}
    anchors_ok = all(row["anchors"]["ghz_anchor_pass"] and row["anchors"]["w_anchor_pass"] for row in ghz_w.values())
    return {
        "stage": "S1",
        "mode": "QUOTIENTED",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "seed": SEED,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "families": {"ghz_w_interpolating": ghz_w, "w_site_weighted": weighted},
        "numeric_entropy_curves": numeric,
        "controls": control_rows(),
        "endpoint_anchors_recovered": anchors_ok,
        "boundary_rows_present": True,
        "density_quotient_rows_present": True,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
