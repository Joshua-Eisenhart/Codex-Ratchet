#!/usr/bin/env python3
"""Adversarial hardening audit for the 2026-06-06 Rosetta and Xi scouts.

This probe preserves the original formal-scout receipts, but records the
stronger adversarial ceiling:

- Rosetta survives only as a bounded table-consistency scout.
- Xi-shell coherent-information gradient is explained by the monotone lambda
  entanglement schedule, so the geometry/cut-specific bridge reading is killed.
"""

from __future__ import annotations

import itertools
import json
import math
import time
from pathlib import Path
from typing import Any

import torch

import sim_rosetta_igt_qit_four_element_structure_probe as rosetta
import sim_xi_shell_coherent_information_gradient_bridge_probe as xi


ROOT = Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "rosetta_xi_adversarial_hardening_audit_probe_results.json"

NAME = "rosetta_xi_adversarial_hardening_audit_probe"
SCHEMA = "FORMAL_SCOUT_RESULT_v1"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "adversarial_hardening_audit"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

CLAIM_CEILING = (
    "Formal scout audit only: records adversarial demotion of the 2026-06-06 "
    "Rosetta/Xi tranche. It does not admit a QIT engine, final IGT, final Xi, "
    "final Phi0, Axis0, gravity, physics, bridge promotion, consciousness, "
    "perception, FTL, or formal admission."
)

BLOCKED_CONSUMERS = [
    "QIT_engine_admission",
    "final_IGT",
    "final_Xi",
    "final_Phi0",
    "Axis0",
    "gravity",
    "physics",
    "bridge_promotion",
    "consciousness",
    "perception",
    "FTL",
    "promotion",
    "formal_admission",
]

TOOL_MANIFEST = {
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing row-atomic permutation enumeration, JSON result writing, and audit aggregation",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing fixed-basis lambda-only density construction and finite QIT readout checks",
    },
    "prior_rosetta_scout": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source of current Rosetta rows and score functions under adversarial feature-drop controls",
    },
    "prior_xi_scout": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source of current Xi-shell density family and coherent-information readouts under lambda-only control",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "python_stdlib": "load_bearing",
    "pytorch": "load_bearing",
    "prior_rosetta_scout": "load_bearing",
    "prior_xi_scout": "load_bearing",
}


def grouped(rows: list[dict[str, Any]]) -> dict[tuple[int, str], list[dict[str, Any]]]:
    out: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for row in rows:
        out.setdefault((int(row["engine_type"]), str(row["loop_class"])), []).append(row)
    return out


def full_row_permutation_score(
    expected: list[dict[str, Any]],
    observed: list[dict[str, Any]],
    features: list[str],
) -> dict[str, Any]:
    exp_by = grouped(expected)
    obs_by = grouped(observed)
    groups: dict[str, Any] = {}
    natural_unique_all = True
    worst_best_nonnatural = 0.0
    for key in sorted(exp_by):
        rows = []
        natural = tuple(range(len(obs_by[key])))
        for perm in itertools.permutations(range(len(obs_by[key]))):
            permuted = [obs_by[key][i] for i in perm]
            score = rosetta.score_rows(exp_by[key], permuted, features)
            rows.append(
                {
                    "perm": list(perm),
                    "is_natural": perm == natural,
                    "ratio": score["ratio"],
                    "matches": score["matches"],
                    "denominator": score["denominator"],
                }
            )
        best = max(row["matches"] for row in rows)
        best_perms = [row["perm"] for row in rows if row["matches"] == best]
        best_nonnatural = max(row["ratio"] for row in rows if not row["is_natural"])
        natural_unique = best_perms == [list(natural)]
        natural_unique_all = natural_unique_all and natural_unique
        worst_best_nonnatural = max(worst_best_nonnatural, best_nonnatural)
        groups[f"{key[0]}:{key[1]}"] = {
            "natural_unique": natural_unique,
            "best_nonnatural_ratio": best_nonnatural,
            "best_perms": best_perms,
        }
    return {
        "natural_unique_all": natural_unique_all,
        "worst_best_nonnatural_ratio": worst_best_nonnatural,
        "groups": groups,
        "feature_count": len(features),
    }


def rosetta_audit() -> dict[str, Any]:
    expected = rosetta.build_igt_rows()
    observed = rosetta.ordered_like_expected(rosetta.build_qit_rows())
    all_features = list(rosetta.FEATURES)
    full = full_row_permutation_score(expected, observed, all_features)
    core_features = ["perception", "ordered_token", "operator", "precedence", "result", "sign"]
    non_token_features = [
        "chirality_sign",
        "h_sign",
        "realization",
        "dynamics_family",
        "projector_axis",
        "rate",
        "operator_family",
    ]
    core = full_row_permutation_score(expected, observed, core_features)
    non_token = full_row_permutation_score(expected, observed, non_token_features)
    singleton_unique = [
        feature
        for feature in all_features
        if full_row_permutation_score(expected, observed, [feature])["natural_unique_all"]
    ]
    return {
        "full_all_features": full,
        "core_claim_features": core,
        "non_token_surface_features": non_token,
        "singleton_features_that_uniquely_bind": singleton_unique,
        "table_consistency_survived": bool(full["natural_unique_all"] and core["natural_unique_all"]),
        "feature_denominator_independence_killed": bool(singleton_unique),
    }


def readouts_for_keep(rho: torch.Tensor, keep_a: list[int], keep_b: list[int]) -> dict[str, float]:
    rho = xi.normalize_density(rho)
    rho_a = xi.partial_trace_qubits(rho, keep_a)
    rho_b = xi.partial_trace_qubits(rho, keep_b)
    s_a = xi.entropy(rho_a)
    s_b = xi.entropy(rho_b)
    s_ab = xi.entropy(rho)
    return {
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "I_c_A_to_B": s_b - s_ab,
        "I_c_B_to_A": s_a - s_ab,
        "I_A_B": s_a + s_b - s_ab,
    }


def profile_for_cut(rows: list[dict[str, Any]], keep_a: list[int], keep_b: list[int]) -> dict[str, Any]:
    radii = [row["params"]["radius"] for row in rows]
    twists = [row["params"].get("twist", row["params"].get("designed_twist", 0.0)) for row in rows]
    reads = [readouts_for_keep(row["rho"], keep_a, keep_b) for row in rows]
    a_to_b = [row["I_c_A_to_B"] for row in reads]
    b_to_a = [row["I_c_B_to_A"] for row in reads]
    g_ab = xi.finite_difference(a_to_b, radii)
    g_ba = xi.finite_difference(b_to_a, radii)
    return {
        "cut": {"A": keep_a, "B": keep_b},
        "A_to_B": xi.gradient_metrics(a_to_b, radii, twists, g_ab),
        "B_to_A": xi.gradient_metrics(b_to_a, radii, twists, g_ba),
    }


def xi_audit() -> dict[str, Any]:
    candidate_rows = [xi.shell_density(k, "candidate") for k in range(xi.N_SHELLS)]
    candidate = xi.family_from_rows("candidate", candidate_rows)

    basis_zero = torch.zeros(2**xi.N_QUBITS, dtype=xi.CDTYPE)
    basis_one = torch.zeros(2**xi.N_QUBITS, dtype=xi.CDTYPE)
    basis_zero[0] = 1.0 + 0.0j
    basis_one[-1] = 1.0 + 0.0j
    lambda_only_rows = []
    for row in candidate_rows:
        lam = row["params"]["lambda"]
        state = xi.normalize(math.cos(lam) * basis_zero + math.sin(lam) * basis_one)
        params = dict(row["params"])
        params["phase"] = 0.0
        params["control"] = "candidate lambda sequence on fixed computational basis"
        lambda_only_rows.append({"rho": xi.density(state), "params": params})
    lambda_only = xi.family_from_rows("lambda_only_fixed_basis_no_boundary_control", lambda_only_rows)

    fake_radius_rows = []
    fake_radii = list(reversed([row["params"]["radius"] for row in candidate_rows]))
    for row, fake_r in zip(candidate_rows, fake_radii, strict=True):
        params = dict(row["params"])
        params["radius"] = fake_r
        params["control"] = "radius labels reversed while rho order preserved"
        fake_radius_rows.append({"rho": row["rho"], "params": params})
    radius_reverse = xi.family_from_rows("radius_label_reverse_control", fake_radius_rows)

    cuts = [
        ([0, 1], [2, 3]),
        ([0, 2], [1, 3]),
        ([0, 3], [1, 2]),
    ]
    cut_profiles = [profile_for_cut(candidate_rows, a, b) for a, b in cuts]

    candidate_reads = candidate["readouts"]
    max_s_ab = max(abs(row["S_AB"]) for row in candidate_reads)
    max_s_a_s_b_gap = max(abs(row["S_A"] - row["S_B"]) for row in candidate_reads)
    max_ic_equals_s_b_gap = max(abs(row["I_c_A_to_B"] - row["S_B"]) for row in candidate_reads)

    lambda_gap = xi.gradient_profile_l2(
        candidate["gradient_dPhi0_dr"], lambda_only["gradient_dPhi0_dr"]
    )
    candidate_score = candidate["metrics"]["positive_signal_score"]
    lambda_score = lambda_only["metrics"]["positive_signal_score"]
    cut_scores = [
        (row["A_to_B"]["positive_signal_score"], row["B_to_A"]["positive_signal_score"])
        for row in cut_profiles
    ]
    first_cut_score = cut_scores[0]
    all_cut_scores_identical = all(
        abs(a - first_cut_score[0]) < 1e-12 and abs(b - first_cut_score[1]) < 1e-12
        for a, b in cut_scores
    )
    return {
        "candidate_metrics": candidate["metrics"],
        "lambda_only_metrics": lambda_only["metrics"],
        "radius_label_reverse_metrics": radius_reverse["metrics"],
        "lambda_only_gradient_profile_l2_gap": lambda_gap,
        "lambda_only_score_gap": abs(candidate_score - lambda_score),
        "cut_profiles": cut_profiles,
        "pure_state_readout_collapse": {
            "max_S_AB": max_s_ab,
            "max_S_A_minus_S_B_gap": max_s_a_s_b_gap,
            "max_Ic_minus_S_B_gap": max_ic_equals_s_b_gap,
        },
        "lambda_schedule_explains_gradient": bool(
            abs(candidate_score - lambda_score) < 1e-12 and lambda_gap < 1e-10
        ),
        "cut_specificity_killed": bool(all_cut_scores_identical),
        "radius_labels_are_load_bearing": bool(radius_reverse["metrics"]["positive_signal_score"] == 0.0),
    }


def pass_count(*sections: dict[str, dict[str, Any]]) -> tuple[int, int]:
    rows = [row for section in sections for row in section.values()]
    return sum(1 for row in rows if row.get("pass") is True), len(rows)


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    ros = rosetta_audit()
    xia = xi_audit()

    positive = {
        "rosetta_table_consistency_survives_row_atomic_control": {
            "pass": ros["table_consistency_survived"],
            "full_best_nonnatural_ratio": ros["full_all_features"]["worst_best_nonnatural_ratio"],
            "core_best_nonnatural_ratio": ros["core_claim_features"]["worst_best_nonnatural_ratio"],
        },
        "xi_lambda_only_control_reproduces_gradient": {
            "pass": xia["lambda_schedule_explains_gradient"],
            "lambda_only_gradient_profile_l2_gap": xia["lambda_only_gradient_profile_l2_gap"],
            "lambda_only_score_gap": xia["lambda_only_score_gap"],
        },
        "xi_radius_reversal_control_still_fails": {
            "pass": xia["radius_labels_are_load_bearing"],
            "radius_reverse_score": xia["radius_label_reverse_metrics"]["positive_signal_score"],
            "radius_reverse_correlation": xia["radius_label_reverse_metrics"]["radius_phi0_correlation"],
        },
    }
    graveyard_companions = {
        "rosetta_224_denominator_as_independent_evidence_killed": {
            "pass": ros["feature_denominator_independence_killed"],
            "singleton_features_that_uniquely_bind": ros["singleton_features_that_uniquely_bind"],
            "reason": "Several single features uniquely bind row order, so the 224 exact-stage denominator is correlated evidence.",
        },
        "xi_shell_geometry_specific_gradient_reading_killed": {
            "pass": xia["lambda_schedule_explains_gradient"],
            "reason": "Fixed-basis zero-phase lambda-only control reproduces the candidate gradient to numerical precision.",
        },
        "xi_cut_specificity_reading_killed": {
            "pass": xia["cut_specificity_killed"],
            "cut_profiles": xia["cut_profiles"],
        },
        "xi_coherent_information_collapses_to_subsystem_entropy_for_pure_state": {
            "pass": (
                xia["pure_state_readout_collapse"]["max_S_AB"] < 1e-10
                and xia["pure_state_readout_collapse"]["max_S_A_minus_S_B_gap"] < 1e-10
                and xia["pure_state_readout_collapse"]["max_Ic_minus_S_B_gap"] < 1e-10
            ),
            **xia["pure_state_readout_collapse"],
        },
    }
    boundary = {
        "formal_scout_audit_only": {
            "pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        },
        "blocked_consumers_complete": {
            "pass": all(
                token in BLOCKED_CONSUMERS
                for token in [
                    "QIT_engine_admission",
                    "final_Xi",
                    "final_Phi0",
                    "Axis0",
                    "gravity",
                    "physics",
                    "bridge_promotion",
                    "promotion",
                    "formal_admission",
                ]
            ),
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
        "original_result_receipts_preserved": {
            "pass": True,
            "rosetta_result": str(rosetta.OUT_PATH),
            "xi_result": str(xi.OUT_PATH),
            "note": "This audit writes a new result and does not rewrite the prior formal-scout receipts.",
        },
    }
    passed, total = pass_count(positive, graveyard_companions, boundary)
    blockers = []
    if passed != total:
        blockers.append("one_or_more_audit_checks_failed")

    result = {
        "schema": SCHEMA,
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "all_pass": not blockers,
        "verdicts": {
            "rosetta_table_consistency_survived": ros["table_consistency_survived"],
            "rosetta_independent_invariant_not_admitted": True,
            "xi_lambda_schedule_explains_gradient": xia["lambda_schedule_explains_gradient"],
            "xi_shell_geometry_specific_reading_killed": xia["lambda_schedule_explains_gradient"],
            "xi_cut_specificity_reading_killed": xia["cut_specificity_killed"],
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "scores": {
            "rosetta": ros,
            "xi": xia,
        },
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "passed": passed,
            "total": total,
            "variants": sorted(list(positive) + list(graveyard_companions) + list(boundary)),
        },
        "why_not_v4_probes": {
            "pass": True,
            "reason": "This is a v5 formal-scout adversarial audit over two v5 scout receipts, not a v4 probe.",
        },
        "blockers": blockers,
        "plain_sentence": (
            "Rosetta remains a bounded table-consistency formal scout, but not an independently admitted IGT/QIT invariant. "
            "Xi-shell coherent-information gradient is demoted: the current positive gradient is reproduced by a fixed-basis "
            "lambda-only entanglement schedule, killing the geometry/cut-specific bridge reading."
        ),
        "elapsed_seconds": time.time() - start,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "name": NAME,
                "result_path": str(OUT_PATH),
                "rosetta_table_consistency_survived": result["verdicts"][
                    "rosetta_table_consistency_survived"
                ],
                "xi_shell_geometry_specific_reading_killed": result["verdicts"][
                    "xi_shell_geometry_specific_reading_killed"
                ],
                "xi_lambda_only_gradient_l2_gap": xia["lambda_only_gradient_profile_l2_gap"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
