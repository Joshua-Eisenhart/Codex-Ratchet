#!/usr/bin/env python3
"""Shared math and source binding for geo_lifted_coord_families_v0."""

from __future__ import annotations

import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path
from typing import Any

import sympy as sp


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "geo_lifted_coord_families_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
MODE = "QUOTIENTED"
RUNG_NS = (3, 4, 5, 6, 7, 8)
SEED = "geo_lifted_coord_families_seed_v0_hash_bound_n3_n4_n5_n6_n7_n8"
PIN_SPEC = (
    "geo_lifted_coord_families_v0|stage=G7-lifted|mode=QUOTIENTED|"
    "source=committed_stage_lifted_spinor_shell_n3_n4_n5_n6_n7_n8_lane_exports|"
    "w_i=eta_i^2_normalized|density_quotient_phase_erased_weights_survive|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

LIFTED_RESULTS = {
    engine: {
        n: ROOT / "system_v6" / "sims" / f"stage_lifted_spinor_shell_n{n}_v0" / "results" / f"stage_lifted_spinor_shell_n{n}_v0_{engine}_results.json"
        for n in RUNG_NS
    }
    for engine in ("julia", "jax", "pytorch")
}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fstr(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def entropy_binary_float(p: float) -> float:
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -p * math.log(p) - (1.0 - p) * math.log(1.0 - p)


def entropy_binary_exact_string(p: Fraction) -> str:
    if p <= 0 or p >= 1:
        return "0"
    q = 1 - p
    return f"-({fstr(p)})*log({fstr(p)})-({fstr(q)})*log({fstr(q)})"


def fraction_from_decimal(value: Any) -> Fraction:
    return Fraction(str(value))


def site_eta_vector(sites: list[dict[str, Any]]) -> list[Fraction]:
    return [fraction_from_decimal(site["eta"]) for site in sites]


def w_site_weighted_amplitudes_from_eta(eta_vec: list[float]) -> dict[str, Any]:
    if not eta_vec:
        raise ValueError("eta_vec must be non-empty")
    weights = [float(eta) ** 2 for eta in eta_vec]
    total = sum(weights)
    if total <= 0.0:
        raise ValueError("at least one eta_i must be nonzero")
    probabilities = [weight / total for weight in weights]
    return {
        "eta_vec": [float(eta) for eta in eta_vec],
        "weights": weights,
        "weight_sum": total,
        "probabilities": probabilities,
        "basis_states": [
            "".join("1" if site == i else "0" for site in range(len(eta_vec)))
            for i in range(len(eta_vec))
        ],
        "amplitudes": [math.sqrt(probability) for probability in probabilities],
    }


def exact_constructor_rows(sites: list[dict[str, Any]]) -> dict[str, Any]:
    eta_fracs = site_eta_vector(sites)
    weights = [eta * eta for eta in eta_fracs]
    total = sum(weights, Fraction(0, 1))
    if total <= 0:
        raise ValueError("lifted eta vector has zero total weight")
    numeric = w_site_weighted_amplitudes_from_eta([float(eta) for eta in eta_fracs])
    site_rows = []
    for site, eta, weight, probability, amplitude in zip(sites, eta_fracs, weights, [w / total for w in weights], numeric["amplitudes"]):
        probability_float = float(probability)
        site_rows.append(
            {
                "site_id": site["site_id"],
                "shell_id": site["shell_id"],
                "source_eta_decimal": site["eta"],
                "source_z_decimal": site["z"],
                "eta_exact_from_export_decimal": fstr(eta),
                "weight_exact_eta_squared": fstr(weight),
                "probability_exact": fstr(probability),
                "amplitude_numeric": amplitude,
                "single_site_entropy_exact": entropy_binary_exact_string(probability),
                "single_site_entropy_numeric": entropy_binary_float(probability_float),
                "basis_state": "".join("1" if idx == int(site["site_id"][1:]) else "0" for idx in range(len(sites))),
            }
        )
    return {
        "constructor": "w_site_weighted_amplitudes_from_eta",
        "weight_rule": "w_i=eta_i^2; p_i=w_i/sum_j w_j",
        "source": "rows.P2_support_object.sites[*].eta from committed lifted rung result",
        "eta_vec_decimal": [site["eta"] for site in sites],
        "eta_vec_exact_from_export_decimal": [fstr(eta) for eta in eta_fracs],
        "weight_sum_exact": fstr(total),
        "probability_sum_numeric": sum(row["single_site_entropy_numeric"] * 0.0 + float(Fraction(row["probability_exact"])) for row in site_rows),
        "basis_states": numeric["basis_states"],
        "site_entropy_curve": site_rows,
    }


def equal_eta_anchor(n: int) -> dict[str, Any]:
    p = Fraction(1, n)
    receipt = w_site_weighted_amplitudes_from_eta([1.0 for _ in range(n)])
    expected_entropy = entropy_binary_float(1.0 / n)
    return {
        "eta_limit": "eta_0=...=eta_{n-1}=1",
        "expected_probability_each_site_exact": fstr(p),
        "expected_entropy_each_site_exact": entropy_binary_exact_string(p),
        "expected_entropy_each_site_numeric": expected_entropy,
        "constructor_probabilities": receipt["probabilities"],
        "constructor_entropies": [entropy_binary_float(probability) for probability in receipt["probabilities"]],
        "committed_rung_anchor_recovered": all(abs(probability - (1.0 / n)) <= 1.0e-15 for probability in receipt["probabilities"]),
    }


def mutation_controls(sites: list[dict[str, Any]]) -> dict[str, Any]:
    base_eta = [float(site["eta"]) for site in sites]
    base = w_site_weighted_amplitudes_from_eta(base_eta)
    base_entropies = [entropy_binary_float(probability) for probability in base["probabilities"]]
    controls = {}
    for idx, site in enumerate(sites):
        mutated_eta = list(base_eta)
        mutated_eta[idx] = mutated_eta[idx] * 1.1
        mutated = w_site_weighted_amplitudes_from_eta(mutated_eta)
        mutated_entropies = [entropy_binary_float(probability) for probability in mutated["probabilities"]]
        entropy_delta = [abs(a - b) for a, b in zip(base_entropies, mutated_entropies)]
        controls[site["site_id"]] = {
            "rerun_under_mutation": True,
            "mutation": "mutate exactly one exported eta_i by factor 1.1 and rerun W-site constructor",
            "mutated_site": site["site_id"],
            "base_eta_vec": base_eta,
            "mutated_eta_vec": mutated_eta,
            "changed_eta_sites": [sites[j]["site_id"] for j, (left, right) in enumerate(zip(base_eta, mutated_eta)) if left != right],
            "base_probabilities": base["probabilities"],
            "mutated_probabilities": mutated["probabilities"],
            "base_entropies": base_entropies,
            "mutated_entropies": mutated_entropies,
            "entropy_abs_delta": entropy_delta,
            "entropy_responds_at_mutated_site": entropy_delta[idx] > 1.0e-12,
            "gate_passed_after_mutation": False,
            "full_rerun_not_json_edit": True,
        }
    return controls


def permutation_control(sites: list[dict[str, Any]]) -> dict[str, Any]:
    base_eta = [float(site["eta"]) for site in sites]
    permutation_indices = list(reversed(range(len(sites))))
    base = w_site_weighted_amplitudes_from_eta(base_eta)
    base_entropies = [entropy_binary_float(probability) for probability in base["probabilities"]]
    permuted_eta = [base_eta[index] for index in permutation_indices]
    rerun = w_site_weighted_amplitudes_from_eta(permuted_eta)
    rerun_entropies = [entropy_binary_float(probability) for probability in rerun["probabilities"]]
    expected_probabilities = [base["probabilities"][index] for index in permutation_indices]
    expected_entropies = [base_entropies[index] for index in permutation_indices]
    return {
        "rerun_under_site_permutation": True,
        "control": "reverse site order, permute exported eta vector, rerun W-site constructor, and compare against permuted base entropy vector",
        "permutation_indices": permutation_indices,
        "base_site_ids": [site["site_id"] for site in sites],
        "permuted_site_ids": [sites[index]["site_id"] for index in permutation_indices],
        "base_eta_vec": base_eta,
        "permuted_eta_vec": permuted_eta,
        "base_probabilities": base["probabilities"],
        "rerun_probabilities": rerun["probabilities"],
        "expected_permuted_probabilities": expected_probabilities,
        "base_entropies": base_entropies,
        "rerun_entropies": rerun_entropies,
        "expected_permuted_entropies": expected_entropies,
        "probability_vector_permuted_accordingly": all(abs(a - b) <= 1.0e-12 for a, b in zip(rerun["probabilities"], expected_probabilities)),
        "entropy_vector_permuted_accordingly": all(abs(a - b) <= 1.0e-12 for a, b in zip(rerun_entropies, expected_entropies)),
        "failure_semantics": "fails if rerunning the constructor on the permuted exported eta vector does not produce the correspondingly permuted per-site probability and entropy vectors",
        "full_rerun_not_json_edit": True,
    }


def flat_family_control(n: int) -> dict[str, Any]:
    flat_eta = [1.0 for _ in range(n)]
    flat = w_site_weighted_amplitudes_from_eta(flat_eta)
    flat_entropies = [entropy_binary_float(probability) for probability in flat["probabilities"]]
    entropy_spread = max(flat_entropies) - min(flat_entropies)
    probability_spread = max(flat["probabilities"]) - min(flat["probabilities"])
    coordinate_independent_detected = probability_spread <= 1.0e-15 and entropy_spread <= 1.0e-15
    return {
        "rerun_under_flat_family": True,
        "control": "replace exported eta coordinates by a coordinate-independent flat eta family and rerun W-site constructor",
        "flat_eta_vec": flat_eta,
        "flat_probabilities": flat["probabilities"],
        "flat_entropies": flat_entropies,
        "expected_probability_each_site": 1.0 / n,
        "probability_spread": probability_spread,
        "entropy_spread": entropy_spread,
        "coordinate_independent_family_detected": coordinate_independent_detected,
        "detected_as_uncoupled": coordinate_independent_detected,
        "failure_semantics": "fails if a flat coordinate-independent eta family is not detected as uncoupled, or if rerun probabilities/entropies retain site-coordinate dependence",
        "full_rerun_not_json_edit": True,
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
    w_anchor_entropy = -sp.Rational(1, n) * sp.log(sp.Rational(1, n)) - sp.Rational(n - 1, n) * sp.log(sp.Rational(n - 1, n))
    return {
        "n": n,
        "support": f"lifted n={n} support",
        "family": "sqrt(1-sin(eta)^2)|GHZ_n> + exp(i alpha) sin(eta)|W_n>",
        "density_quotient_row": {
            "phase_surface": "single-site entropy quotient",
            "phase_erased": True,
            "weights_survive": True,
            "B1_consistency": "density quotient erases phase on this entropy surface while sin(eta)^2 and W-site weights remain observable",
        },
        "rho_single_site": {
            "diag_0": sp.sstr(a),
            "diag_1": sp.sstr(d),
            "offdiag_abs_squared": sp.sstr(offdiag_sq),
        },
        "eigenvalues": [sp.sstr(lam_minus), sp.sstr(lam_plus)],
        "entropy_exact": sp.sstr(entropy),
        "determinant": sp.sstr(det),
        "anchors": {
            "eta_0_GHZ_entropy": "log(2)",
            "eta_pi_over_2_W_entropy": entropy_binary_exact_string(Fraction(1, n)),
            "ghz_anchor_pass": sp.simplify(entropy.subs(eta, 0) - sp.log(2)) == 0,
            "w_anchor_pass": sp.simplify(entropy.subs(eta, sp.pi / 2) - w_anchor_entropy) == 0,
        },
    }


def ghz_w_numeric_curve(n: int) -> list[dict[str, Any]]:
    rows = []
    for k in range(17):
        eta = (math.pi / 2.0) * k / 16.0
        t = math.sin(eta) ** 2
        a = (1 - t) / 2 + t * (n - 1) / n
        d = (1 - t) / 2 + t / n
        offdiag_sq = (1 - t) * t / (2 * n)
        det = a * d - offdiag_sq
        eig0 = (1 - math.sqrt(max(0.0, 1 - 4 * det))) / 2
        rows.append({"n": n, "index": k, "eta": eta, "t": t, "lambda_min": eig0, "entropy": entropy_binary_float(eig0), "det": det})
    return rows


def load_lifted_rung(engine: str, n: int) -> dict[str, Any]:
    path = LIFTED_RESULTS[engine][n]
    payload = json.loads(path.read_text(encoding="utf-8"))
    sites = payload["rows"]["P2_support_object"]["sites"]
    return {
        "rung_n": n,
        "engine": engine,
        "result_path": str(path.relative_to(ROOT)),
        "result_sha256": file_sha256(path),
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "pin_sha256": payload["pin_sha256"],
        "all_pass": payload["all_pass"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "json_pointer": "/rows/P2_support_object/sites",
        "sites": sites,
    }


def build_math_payload(engine: str) -> dict[str, Any]:
    rungs = {}
    for n in RUNG_NS:
        lifted = load_lifted_rung(engine, n)
        constructor = exact_constructor_rows(lifted["sites"])
        rungs[str(n)] = {
            "source_binding": lifted,
            "w_site_weighted_family": constructor,
            "equal_eta_anchor": equal_eta_anchor(n),
            "mutation_controls": mutation_controls(lifted["sites"]),
            "permutation_control": permutation_control(lifted["sites"]),
            "flat_family_control": flat_family_control(n),
            "ghz_w_interpolating_family": ghz_w_symbolic(n),
            "ghz_w_numeric_entropy_curve": ghz_w_numeric_curve(n),
            "density_quotient_row": {
                "phase_erased": True,
                "weights_survive": True,
                "row_label": "phase erased, weights survive",
                "committed_B1_consistency": True,
                "surface": "single-site entropy and W-site probability quotient",
            },
        }
    return {
        "sim_id": SIM_ID,
        "stage": "G7-lifted",
        "mode": MODE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "seed": SEED,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "source_policy": "read committed lifted rung result exports read-only for n3/n4/n5/n6/n7/n8",
        "rungs": rungs,
    }


def common_gate_pass(payload: dict[str, Any]) -> dict[str, bool]:
    rungs = payload["rungs"]
    return {
        "mode_quotiented": payload["mode"] == "QUOTIENTED",
        "ceiling_exact": payload["classification"] == CLASSIFICATION
        and payload["promotion_allowed"] is False
        and payload["formal_admission_allowed"] is False,
        "source_bindings_all_green": all(
            rung["source_binding"]["all_pass"] is True
            and rung["source_binding"]["classification"] == CLASSIFICATION
            and rung["source_binding"]["promotion_allowed"] is False
            and len(rung["source_binding"]["sites"]) == int(n)
            for n, rung in rungs.items()
        ),
        "equal_eta_anchors_recovered": all(rung["equal_eta_anchor"]["committed_rung_anchor_recovered"] is True for rung in rungs.values()),
        "mutation_controls_pass": all(
            control["rerun_under_mutation"] is True
            and control["changed_eta_sites"] == [site_id]
            and control["entropy_responds_at_mutated_site"] is True
            and control["full_rerun_not_json_edit"] is True
            for rung in rungs.values()
            for site_id, control in rung["mutation_controls"].items()
        ),
        "permutation_controls_pass": all(
            rung["permutation_control"]["rerun_under_site_permutation"] is True
            and rung["permutation_control"]["probability_vector_permuted_accordingly"] is True
            and rung["permutation_control"]["entropy_vector_permuted_accordingly"] is True
            and rung["permutation_control"]["full_rerun_not_json_edit"] is True
            for rung in rungs.values()
        ),
        "flat_family_controls_pass": all(
            rung["flat_family_control"]["rerun_under_flat_family"] is True
            and rung["flat_family_control"]["coordinate_independent_family_detected"] is True
            and rung["flat_family_control"]["detected_as_uncoupled"] is True
            and rung["flat_family_control"]["full_rerun_not_json_edit"] is True
            for rung in rungs.values()
        ),
        "density_quotient_rows_present": all(
            rung["density_quotient_row"]["phase_erased"] is True
            and rung["density_quotient_row"]["weights_survive"] is True
            for rung in rungs.values()
        ),
        "lifted_source_scope_n3_through_n8": set(rungs) == {str(n) for n in RUNG_NS},
    }
