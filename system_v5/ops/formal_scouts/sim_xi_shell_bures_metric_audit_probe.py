#!/usr/bin/env python3
"""Bures-distance audit over the Xi shell scout family.

Formal scout only.  The prior coherent-information gradient scout was demoted
because a fixed-basis lambda-only control reproduced the gradient.  This probe
asks a narrower metric question: does a density-matrix distinguishability
metric see additional carrier motion beyond that lambda schedule, and if so
does that remain below Xi/Phi0/Axis0/physics promotion?
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any, Callable

import torch

import sim_xi_shell_coherent_information_gradient_bridge_probe as xi


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "xi_shell_bures_metric_audit_probe_results.json"
PRIOR_HARDENING_RESULT = RESULT_DIR / "rosetta_xi_adversarial_hardening_audit_probe_results.json"

NAME = "xi_shell_bures_metric_audit_probe"
SCHEMA = "FORMAL_SCOUT_RESULT_v1"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "adversarial_metric_audit"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

CLAIM_CEILING = (
    "Formal scout audit only: tests Bures-distance profiles on the existing "
    "Xi-shell density family after the coherent-information gradient was "
    "demoted by lambda-only control. It may show metric-route pressure, but it "
    "does not admit final Xi, final Phi0, Axis0, gravity, physics, bridge "
    "promotion, holography, ER=EPR, FTL, QIT engine admission, or formal "
    "admission."
)

BLOCKED_CONSUMERS = [
    "final_Xi",
    "final_Phi0",
    "Axis0",
    "gravity",
    "physics",
    "bridge_promotion",
    "holography",
    "ER_EPR",
    "FTL",
    "QIT_engine_admission",
    "promotion",
    "formal_admission",
]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex128 density matrices, eigendecompositions, partial traces, Bures distances, and rank/support controls",
    },
    "prior_xi_scout": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source of the existing Xi-shell finite density family and controls",
    },
    "prior_hardening_receipt": {
        "tried": True,
        "used": True,
        "reason": "load-bearing receipt preserving the coherent-information gradient demotion boundary",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling for receipts"},
    "math": {"tried": True, "used": True, "reason": "supportive finite metric summaries"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "prior_xi_scout": "load_bearing",
    "prior_hardening_receipt": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "math": "supportive",
}

PROFILE_EPS = 1e-10
SEPARATION_EPS = 1e-2
SANITY_EPS = 1e-6


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): jsonable(row) for key, row in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(row) for row in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return jsonable(value.detach().cpu().item())
        return jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def sqrt_psd(rho: torch.Tensor) -> torch.Tensor:
    vals, vecs = torch.linalg.eigh(xi.hermitize(rho))
    vals = torch.clamp(vals.real, min=0.0)
    return (vecs * torch.sqrt(vals).to(xi.CDTYPE)) @ torch.conj(vecs).T


def fidelity(rho: torch.Tensor, sigma: torch.Tensor) -> float:
    rho = xi.normalize_density(rho)
    sigma = xi.normalize_density(sigma)
    sqrt_rho = sqrt_psd(rho)
    inner = sqrt_psd(xi.hermitize(sqrt_rho @ sigma @ sqrt_rho))
    trace = float(torch.real(torch.trace(inner)).item())
    return max(0.0, min(1.0, trace * trace))


def bures_distance(rho: torch.Tensor, sigma: torch.Tensor) -> float:
    f = fidelity(rho, sigma)
    return math.sqrt(max(0.0, 2.0 * (1.0 - math.sqrt(f))))


def l2(left: list[float], right: list[float]) -> float:
    return math.sqrt(sum((a - b) * (a - b) for a, b in zip(left, right)))


def profile_summary(values: list[float]) -> dict[str, Any]:
    return {
        "values": values,
        "mean": sum(values) / len(values),
        "min": min(values),
        "max": max(values),
        "range": max(values) - min(values),
        "all_finite": all(math.isfinite(row) for row in values),
        "positive_count": sum(1 for row in values if row > PROFILE_EPS),
    }


def rank_summary(rho: torch.Tensor) -> dict[str, Any]:
    vals = torch.linalg.eigvalsh(xi.hermitize(xi.normalize_density(rho))).real
    vals = torch.clamp(vals, min=0.0)
    return {
        "rank_gt_1e_10": int(torch.sum(vals > 1e-10).item()),
        "rank_gt_1e_8": int(torch.sum(vals > 1e-8).item()),
        "max_eigenvalue": float(torch.max(vals).item()),
        "min_eigenvalue": float(torch.min(vals).item()),
        "support_trace_gt_1e_10": float(torch.sum(vals[vals > 1e-10]).item()),
    }


def state_from_spinors(spinors: list[torch.Tensor], lam: float, phase: float) -> torch.Tensor:
    a0 = xi.normalize(torch.kron(spinors[0], spinors[1]))
    b0 = xi.normalize(torch.kron(spinors[2], spinors[3]))
    a1 = xi.normalize(torch.kron(xi.orthogonal_spinor(spinors[0]), xi.orthogonal_spinor(spinors[1])))
    b1 = xi.normalize(torch.kron(xi.orthogonal_spinor(spinors[2]), xi.orthogonal_spinor(spinors[3])))
    return xi.normalize(
        math.cos(lam) * torch.kron(a0, b0)
        + math.sin(lam) * xi.cexp(phase) * torch.kron(a1, b1)
    )


def fixed_basis_state(lam: float, phase: float) -> torch.Tensor:
    basis_zero = torch.zeros(2**xi.N_QUBITS, dtype=xi.CDTYPE)
    basis_one = torch.zeros_like(basis_zero)
    basis_zero[0] = 1.0 + 0.0j
    basis_one[-1] = 1.0 + 0.0j
    return xi.normalize(math.cos(lam) * basis_zero + math.sin(lam) * xi.cexp(phase) * basis_one)


def row_from_state(state: torch.Tensor, params: dict[str, Any], control: str) -> dict[str, Any]:
    row_params = dict(params)
    row_params["control"] = control
    return {"rho": xi.density(state), "params": row_params}


def candidate_rows() -> list[dict[str, Any]]:
    return [xi.shell_density(k, "candidate") for k in range(xi.N_SHELLS)]


def lambda_only_rows(rows: list[dict[str, Any]], *, include_phase: bool) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        phase = row["params"]["phase"] if include_phase else 0.0
        out.append(
            row_from_state(
                fixed_basis_state(row["params"]["lambda"], phase),
                row["params"],
                "fixed computational basis with candidate lambda"
                + (" and candidate phase" if include_phase else " and zero phase"),
            )
        )
    return out


def local_frame_rows(rows: list[dict[str, Any]], *, zero_phase: bool, constant_lambda: bool) -> list[dict[str, Any]]:
    mid_lam = rows[len(rows) // 2]["params"]["lambda"]
    out = []
    for row in rows:
        params = xi.xi_shell_parameters(int(row["params"]["k"]), "candidate")
        lam = mid_lam if constant_lambda else row["params"]["lambda"]
        phase = 0.0 if zero_phase else row["params"]["phase"]
        state = state_from_spinors(params["spinors"], lam, phase)
        control = "candidate local spinor frame"
        if zero_phase:
            control += " with zero phase"
        if constant_lambda:
            control += " with constant midpoint lambda"
        out.append(row_from_state(state, row["params"], control))
    return out


def product_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "rho": xi.productize_cut(row["rho"]),
            "params": {**dict(row["params"]), "control": "productized A|B cut"},
        }
        for row in rows
    ]


def flat_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mid = rows[len(rows) // 2]
    return [
        {"rho": mid["rho"].clone(), "params": {**dict(row["params"]), "control": "flat midpoint rho"}}
        for row in rows
    ]


def scrambled_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    perm = [0, 8, 1, 7, 2, 6, 3, 5, 4]
    return [
        {
            "rho": rows[source]["rho"].clone(),
            "params": {
                **dict(radius_row["params"]),
                "source_shell_after_scramble": source,
                "control": "shell order scramble",
            },
        }
        for radius_row, source in zip(rows, perm, strict=True)
    ]


def profile(
    rows: list[dict[str, Any]],
    transform: Callable[[dict[str, Any]], torch.Tensor] | None = None,
) -> list[float]:
    if transform is None:
        transform = lambda row: row["rho"]
    return [bures_distance(transform(rows[idx]), transform(rows[idx + 1])) for idx in range(len(rows) - 1)]


def profiles_for_variants(variants: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    cuts = {
        "cut_01_vs_23_A": [0, 1],
        "cut_02_vs_13_A": [0, 2],
        "cut_03_vs_12_A": [0, 3],
    }
    for label, rows in variants.items():
        entry = {"global": profile_summary(profile(rows))}
        for cut_label, keep in cuts.items():
            entry[cut_label] = profile_summary(
                profile(rows, lambda row, keep=keep: xi.partial_trace_qubits(row["rho"], keep))
            )
        out[label] = entry
    return out


def profile_l2_table(profiles: dict[str, Any], reference: str = "candidate") -> dict[str, Any]:
    ref = profiles[reference]["global"]["values"]
    return {
        label: {
            "global_l2_from_candidate": l2(ref, row["global"]["values"]),
            "global_mean_ratio_to_candidate": (
                row["global"]["mean"] / profiles[reference]["global"]["mean"]
                if profiles[reference]["global"]["mean"] > PROFILE_EPS
                else None
            ),
        }
        for label, row in profiles.items()
        if label != reference
    }


def cut_l2_table(profiles: dict[str, Any]) -> dict[str, Any]:
    cuts = ["cut_01_vs_23_A", "cut_02_vs_13_A", "cut_03_vs_12_A"]
    table: dict[str, Any] = {}
    for cut in cuts:
        table[cut] = {
            "candidate_vs_lambda_zero_phase_l2": l2(
                profiles["candidate"][cut]["values"],
                profiles["lambda_only_fixed_basis_zero_phase"][cut]["values"],
            ),
            "candidate_vs_lambda_phase_l2": l2(
                profiles["candidate"][cut]["values"],
                profiles["lambda_phase_fixed_basis"][cut]["values"],
            ),
        }
    pairwise = {}
    for idx, left in enumerate(cuts):
        for right in cuts[idx + 1 :]:
            pairwise[f"{left}__vs__{right}"] = l2(
                profiles["candidate"][left]["values"],
                profiles["candidate"][right]["values"],
            )
    return {"per_cut": table, "candidate_cut_pairwise_l2": pairwise}


def kron4(unitary: torch.Tensor) -> torch.Tensor:
    return torch.kron(torch.kron(torch.kron(unitary, unitary), unitary), unitary)


def bures_sanity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    first = rows[0]["rho"]
    second = rows[1]["rho"]
    mid = rows[len(rows) // 2]["rho"]
    theta = 0.37
    single = torch.tensor(
        [
            [math.cos(theta / 2.0), -1j * math.sin(theta / 2.0)],
            [-1j * math.sin(theta / 2.0), math.cos(theta / 2.0)],
        ],
        dtype=xi.CDTYPE,
    )
    unitary = kron4(single)
    first_u = xi.normalize_density(unitary @ first @ torch.conj(unitary).T)
    second_u = xi.normalize_density(unitary @ second @ torch.conj(unitary).T)
    identity_gap = bures_distance(mid, mid)
    symmetry_gap = abs(bures_distance(first, second) - bures_distance(second, first))
    common_unitary_gap = abs(bures_distance(first, second) - bures_distance(first_u, second_u))
    monotonicity_gaps = []
    for idx in range(len(rows) - 1):
        global_d = bures_distance(rows[idx]["rho"], rows[idx + 1]["rho"])
        for keep in ([0, 1], [0, 2], [0, 3]):
            reduced_d = bures_distance(
                xi.partial_trace_qubits(rows[idx]["rho"], keep),
                xi.partial_trace_qubits(rows[idx + 1]["rho"], keep),
            )
            monotonicity_gaps.append(reduced_d - global_d)
    max_monotonicity_violation = max(monotonicity_gaps)
    return {
        "identity_gap": identity_gap,
        "symmetry_gap": symmetry_gap,
        "common_unitary_gap": common_unitary_gap,
        "max_partial_trace_monotonicity_violation": max_monotonicity_violation,
        "pass": bool(
            identity_gap < SANITY_EPS
            and symmetry_gap < SANITY_EPS
            and common_unitary_gap < SANITY_EPS
            and max_monotonicity_violation < SANITY_EPS
        ),
        "tolerance": SANITY_EPS,
    }


def support_table(variants: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    out = {}
    for label, rows in variants.items():
        mid = rows[len(rows) // 2]["rho"]
        out[label] = {
            "global": rank_summary(mid),
            "rho_A_01": rank_summary(xi.partial_trace_qubits(mid, [0, 1])),
            "rho_A_02": rank_summary(xi.partial_trace_qubits(mid, [0, 2])),
            "rho_A_03": rank_summary(xi.partial_trace_qubits(mid, [0, 3])),
        }
    return out


def read_prior_hardening() -> dict[str, Any]:
    data = json.loads(PRIOR_HARDENING_RESULT.read_text(encoding="utf-8"))
    return {
        "path": str(PRIOR_HARDENING_RESULT),
        "all_pass": data.get("all_pass"),
        "classification": data.get("classification"),
        "promotion_allowed": data.get("promotion_allowed"),
        "verdicts": data.get("verdicts", {}),
        "xi_lambda_only_gradient_profile_l2_gap": data.get("scores", {})
        .get("xi", {})
        .get("lambda_only_gradient_profile_l2_gap"),
    }


def count_passes(*sections: dict[str, dict[str, Any]]) -> tuple[int, int]:
    rows = [row for section in sections for row in section.values()]
    return sum(1 for row in rows if row.get("pass") is True), len(rows)


def run_probe() -> dict[str, Any]:
    start = time.time()
    base = candidate_rows()
    variants = {
        "candidate": base,
        "lambda_only_fixed_basis_zero_phase": lambda_only_rows(base, include_phase=False),
        "lambda_phase_fixed_basis": lambda_only_rows(base, include_phase=True),
        "local_frame_zero_phase": local_frame_rows(base, zero_phase=True, constant_lambda=False),
        "local_frame_constant_lambda": local_frame_rows(base, zero_phase=False, constant_lambda=True),
        "product_cut_control": product_rows(base),
        "flat_shell_control": flat_rows(base),
        "shell_order_scramble_control": scrambled_rows(base),
    }
    profiles = profiles_for_variants(variants)
    l2s = profile_l2_table(profiles)
    cut_l2s = cut_l2_table(profiles)
    support = support_table(variants)
    sanity = bures_sanity(base)
    prior = read_prior_hardening()

    candidate_profile = profiles["candidate"]["global"]
    lambda_gap = l2s["lambda_only_fixed_basis_zero_phase"]["global_l2_from_candidate"]
    lambda_phase_gap = l2s["lambda_phase_fixed_basis"]["global_l2_from_candidate"]
    product_gap = l2s["product_cut_control"]["global_l2_from_candidate"]
    flat_gap = l2s["flat_shell_control"]["global_l2_from_candidate"]
    scramble_gap = l2s["shell_order_scramble_control"]["global_l2_from_candidate"]
    product_ratio = l2s["product_cut_control"]["global_mean_ratio_to_candidate"]

    all_profiles_finite = all(
        section["all_finite"]
        for variant in profiles.values()
        for section in variant.values()
        if isinstance(section, dict) and "all_finite" in section
    )
    all_candidate_steps_positive = candidate_profile["positive_count"] == xi.N_SHELLS - 1
    lambda_does_not_explain_bures = lambda_gap > SEPARATION_EPS and lambda_phase_gap > SEPARATION_EPS
    scramble_is_order_sensitive = scramble_gap > 0.5
    flat_control_collapses_profile = (
        profiles["flat_shell_control"]["global"]["max"] < PROFILE_EPS and flat_gap > 0.15
    )
    product_same_order_blocks_boundary_specificity = (
        product_ratio is not None and 0.5 < product_ratio < 2.0 and product_gap < 0.08
    )
    support_boundary_recorded = (
        support["candidate"]["global"]["rank_gt_1e_10"] == 1
        and support["lambda_only_fixed_basis_zero_phase"]["global"]["rank_gt_1e_10"] == 1
        and support["product_cut_control"]["global"]["rank_gt_1e_10"] > 1
        and support["candidate"]["rho_A_01"]["rank_gt_1e_10"] > 1
    )
    reduced_cut_nonlambda_residuals_recorded = (
        min(
            row["candidate_vs_lambda_zero_phase_l2"]
            for row in cut_l2s["per_cut"].values()
        )
        > 1e-3
        and max(cut_l2s["candidate_cut_pairwise_l2"].values()) > 5e-4
    )
    prior_kill_preserved = (
        prior["all_pass"] is True
        and prior["classification"] == "formal_scout"
        and prior["promotion_allowed"] is False
        and prior["verdicts"].get("xi_lambda_schedule_explains_gradient") is True
        and prior["verdicts"].get("xi_shell_geometry_specific_reading_killed") is True
    )

    metric_route_pressure = bool(
        all_profiles_finite
        and all_candidate_steps_positive
        and lambda_does_not_explain_bures
        and scramble_is_order_sensitive
        and flat_control_collapses_profile
        and support_boundary_recorded
        and sanity["pass"]
    )

    positive = {
        "bures_profiles_execute_and_are_finite": {
            "pass": all_profiles_finite,
            "candidate_global_profile": candidate_profile,
        },
        "bures_candidate_not_reproduced_by_lambda_only_base_control": {
            "pass": lambda_does_not_explain_bures,
            "candidate_vs_lambda_zero_phase_global_l2": lambda_gap,
            "candidate_vs_lambda_phase_global_l2": lambda_phase_gap,
            "interpretation": "Bures distance sees carrier-frame/phase motion beyond the lambda-only entanglement schedule.",
        },
        "shell_order_load_bearing_for_metric_profile": {
            "pass": scramble_is_order_sensitive and flat_control_collapses_profile,
            "scramble_global_l2_from_candidate": scramble_gap,
            "flat_global_l2_from_candidate": flat_gap,
        },
        "bures_metric_sanity_checks_pass": sanity,
        "rank_and_support_boundary_recorded": {
            "pass": support_boundary_recorded,
            "support_mid_shell": support,
        },
        "reduced_cut_profiles_record_nonlambda_residuals": {
            "pass": reduced_cut_nonlambda_residuals_recorded,
            "cut_l2_table": cut_l2s,
            "interpretation": "Reduced cuts keep small but nonzero non-lambda residuals; this records pressure only, not cut-specific bridge promotion.",
        },
    }
    graveyard_companions = {
        "coherent_information_geometry_reading_remains_killed": {
            "pass": prior_kill_preserved,
            "prior_hardening_receipt": prior,
            "reason": "This metric audit does not rewrite the prior coherent-information demotion: lambda-only still explains the Phi0 gradient.",
        },
        "bures_metric_does_not_promote_xi_bridge": {
            "pass": product_same_order_blocks_boundary_specificity,
            "candidate_global_mean": candidate_profile["mean"],
            "product_global_mean": profiles["product_cut_control"]["global"]["mean"],
            "product_mean_ratio_to_candidate": product_ratio,
            "candidate_vs_product_global_l2": product_gap,
            "reason": "A productized cut has same-order Bures motion, so the metric is carrier-distance pressure, not a cut-specific bridge invariant.",
        },
        "single_metric_family_not_axis0_or_physics": {
            "pass": True,
            "reason": "One Bures profile family cannot admit Xi, Phi0, Axis0, gravity, physics, holography, or FTL consumers.",
        },
    }
    boundary = {
        "formal_scout_only": {
            "pass": CLASSIFICATION == "formal_scout"
            and PROMOTION_ALLOWED is False
            and FORMAL_ADMISSION_ALLOWED is False,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        },
        "blocked_consumers_complete": {
            "pass": all(
                token in BLOCKED_CONSUMERS
                for token in [
                    "final_Xi",
                    "final_Phi0",
                    "Axis0",
                    "gravity",
                    "physics",
                    "bridge_promotion",
                    "QIT_engine_admission",
                    "promotion",
                    "formal_admission",
                ]
            ),
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
        "claim_ceiling_blocks_promotion_language": {
            "pass": all(
                phrase in CLAIM_CEILING
                for phrase in [
                    "does not admit final Xi",
                    "final Phi0",
                    "Axis0",
                    "gravity",
                    "physics",
                    "formal admission",
                ]
            ),
            "claim_ceiling": CLAIM_CEILING,
        },
    }

    passed, total = count_passes(positive, graveyard_companions, boundary)
    blockers = []
    if passed != total:
        blockers.append("one_or_more_metric_audit_checks_failed")

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
            "bures_metric_route_pressure_survived": metric_route_pressure,
            "bures_lambda_only_does_not_explain_metric_profile": lambda_does_not_explain_bures,
            "bures_metric_does_not_promote_xi_bridge": product_same_order_blocks_boundary_specificity,
            "coherent_information_geometry_reading_remains_killed": prior_kill_preserved,
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "scores": {
            "profiles": profiles,
            "profile_l2_table": l2s,
            "cut_l2_table": cut_l2s,
            "bures_sanity": sanity,
            "support": support,
            "prior_hardening": prior,
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
            "reason": "This is a v5 formal-scout metric audit over existing v5 Xi receipts, not a v4 probe.",
        },
        "blockers": blockers,
        "plain_sentence": (
            "Bures distance sees non-lambda carrier-frame motion in the Xi-shell density family, but product/rank/cut controls keep it "
            "below bridge, Axis0, gravity, physics, or QIT-engine promotion; the prior coherent-information gradient demotion remains in force."
        ),
        "elapsed_seconds": time.time() - start,
    }
    return jsonable(result)


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = run_probe()
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "name": NAME,
                "result_path": str(OUT_PATH),
                "bures_metric_route_pressure_survived": result["verdicts"][
                    "bures_metric_route_pressure_survived"
                ],
                "bures_lambda_only_l2": result["positive"][
                    "bures_candidate_not_reproduced_by_lambda_only_base_control"
                ]["candidate_vs_lambda_zero_phase_global_l2"],
                "candidate_vs_product_l2": result["graveyard_companions"][
                    "bures_metric_does_not_promote_xi_bridge"
                ]["candidate_vs_product_global_l2"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
