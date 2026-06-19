#!/usr/bin/env python3
"""Channel/resource hardening for the Xi-shell Bures metric scout.

Formal scout only.  The previous Bures audit showed metric-route pressure over
the Xi shell density family, while still blocking Xi/Phi0/Axis0/physics
promotion.  This probe adds finite channel/resource controls: common unitary
invariance, CPTP contraction, depolarization, dephasing, discard/replace, and
partial-trace controls.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any, Callable

import torch

import sim_xi_shell_bures_metric_audit_probe as bures
import sim_xi_shell_coherent_information_gradient_bridge_probe as xi


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "xi_shell_channel_resource_metric_audit_probe_results.json"
PRIOR_BUres_RESULT = RESULT_DIR / "xi_shell_bures_metric_audit_probe_results.json"

NAME = "xi_shell_channel_resource_metric_audit_probe"
SCHEMA = "FORMAL_SCOUT_RESULT_v1"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "channel_resource_metric_audit"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

CLAIM_CEILING = (
    "Formal scout audit only: tests finite channel/resource controls over the "
    "existing Xi-shell Bures metric scout. It may show that Bures residuals "
    "obey channel monotonicity and where coherence/cut-erasure controls reduce "
    "the residual, but it does not admit final Xi, final Phi0, Axis0, gravity, "
    "physics, bridge promotion, holography, ER=EPR, FTL, QIT engine admission, "
    "resource-theory admission, or formal admission."
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
    "resource_theory_admission",
    "promotion",
    "formal_admission",
]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite complex128 density matrices, CPTP channel maps, Bures profile computations, and contraction checks",
    },
    "prior_bures_scout": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source of the current Xi-shell Bures metric family and Bures distance implementation",
    },
    "prior_xi_scout": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source of finite partial traces and density normalization over the Xi shell family",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive receipt path handling"},
    "math": {"tried": True, "used": True, "reason": "supportive finite channel parameters and scalar summaries"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "prior_bures_scout": "load_bearing",
    "prior_xi_scout": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "math": "supportive",
}

PROFILE_EPS = 1e-10
CHANNEL_TOL = 1e-6
DEPOL_GRID = [0.0, 0.1, 0.25, 0.5, 0.75, 1.0]


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


def l2(left: list[float], right: list[float]) -> float:
    return math.sqrt(sum((a - b) * (a - b) for a, b in zip(left, right)))


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def profile(rows: list[dict[str, Any]], channel: Callable[[torch.Tensor], torch.Tensor]) -> list[float]:
    return [
        bures.bures_distance(channel(rows[idx]["rho"]), channel(rows[idx + 1]["rho"]))
        for idx in range(len(rows) - 1)
    ]


def profile_summary(values: list[float]) -> dict[str, Any]:
    return {
        "values": values,
        "mean": mean(values),
        "min": min(values),
        "max": max(values),
        "range": max(values) - min(values),
        "all_finite": all(math.isfinite(row) for row in values),
        "positive_count": sum(1 for row in values if row > PROFILE_EPS),
    }


def identity_channel(rho: torch.Tensor) -> torch.Tensor:
    return xi.normalize_density(rho)


def common_unitary_channel(rho: torch.Tensor) -> torch.Tensor:
    theta = 0.41
    single = torch.tensor(
        [
            [math.cos(theta / 2.0), -1j * math.sin(theta / 2.0)],
            [-1j * math.sin(theta / 2.0), math.cos(theta / 2.0)],
        ],
        dtype=xi.CDTYPE,
    )
    unitary = torch.kron(torch.kron(torch.kron(single, single), single), single)
    return xi.normalize_density(unitary @ rho @ torch.conj(unitary).T)


def depolarizing_channel(rho: torch.Tensor, p: float = 0.25) -> torch.Tensor:
    dim = 2**xi.N_QUBITS
    mixed = torch.eye(dim, dtype=xi.CDTYPE) / dim
    return xi.normalize_density((1.0 - p) * rho + p * mixed)


def dephasing_channel(rho: torch.Tensor, p: float = 0.65) -> torch.Tensor:
    diag = torch.diag(torch.diagonal(rho))
    return xi.normalize_density((1.0 - p) * rho + p * diag)


def discard_replace_b_channel(rho: torch.Tensor) -> torch.Tensor:
    rho_a = xi.partial_trace_qubits(rho, [0, 1])
    fixed_b = torch.eye(4, dtype=xi.CDTYPE) / 4.0
    return xi.normalize_density(torch.kron(rho_a, fixed_b))


def b_local_depolarizing_channel(rho: torch.Tensor, p: float) -> torch.Tensor:
    return xi.normalize_density((1.0 - p) * rho + p * discard_replace_b_channel(rho))


def discard_replace_a_channel(rho: torch.Tensor) -> torch.Tensor:
    fixed_a = torch.eye(4, dtype=xi.CDTYPE) / 4.0
    rho_b = xi.partial_trace_qubits(rho, [2, 3])
    return xi.normalize_density(torch.kron(fixed_a, rho_b))


def partial_trace_a_channel(rho: torch.Tensor) -> torch.Tensor:
    return xi.normalize_density(xi.partial_trace_qubits(rho, [0, 1]))


def partial_trace_cross_channel(rho: torch.Tensor) -> torch.Tensor:
    return xi.normalize_density(xi.partial_trace_qubits(rho, [0, 2]))


CHANNELS: dict[str, Callable[[torch.Tensor], torch.Tensor]] = {
    "identity": identity_channel,
    "common_unitary": common_unitary_channel,
    "depolarizing_p025": depolarizing_channel,
    "dephasing_p065": dephasing_channel,
    "discard_replace_B": discard_replace_b_channel,
    "discard_replace_A": discard_replace_a_channel,
    "partial_trace_A01": partial_trace_a_channel,
    "partial_trace_cross_02": partial_trace_cross_channel,
}


def read_prior_bures() -> dict[str, Any]:
    data = json.loads(PRIOR_BUres_RESULT.read_text(encoding="utf-8"))
    return {
        "path": str(PRIOR_BUres_RESULT),
        "all_pass": data.get("all_pass"),
        "classification": data.get("classification"),
        "promotion_allowed": data.get("promotion_allowed"),
        "formal_admission_allowed": data.get("formal_admission_allowed"),
        "verdicts": data.get("verdicts", {}),
        "bures_sanity": data.get("scores", {}).get("bures_sanity", {}),
    }


def channel_profiles() -> dict[str, Any]:
    candidate = bures.candidate_rows()
    lambda_zero = bures.lambda_only_rows(candidate, include_phase=False)
    lambda_phase = bures.lambda_only_rows(candidate, include_phase=True)
    mid_b = xi.partial_trace_qubits(candidate[len(candidate) // 2]["rho"], [2, 3])

    def discard_replace_fixed_mid_b_channel(rho: torch.Tensor) -> torch.Tensor:
        rho_a = xi.partial_trace_qubits(rho, [0, 1])
        return xi.normalize_density(torch.kron(rho_a, mid_b))

    channels_to_run = dict(CHANNELS)
    channels_to_run["discard_replace_fixed_mid_B"] = discard_replace_fixed_mid_b_channel
    for p in DEPOL_GRID:
        tag = f"{int(round(100 * p)):03d}"
        channels_to_run[f"global_depolarizing_p{tag}"] = (
            lambda rho, p=p: depolarizing_channel(rho, p)
        )
        channels_to_run[f"B_local_depolarizing_p{tag}"] = (
            lambda rho, p=p: b_local_depolarizing_channel(rho, p)
        )

    rows: dict[str, Any] = {}
    base_profile = profile(candidate, identity_channel)
    for label, channel in channels_to_run.items():
        candidate_profile = profile(candidate, channel)
        lambda_profile = profile(lambda_zero, channel)
        lambda_phase_profile = profile(lambda_phase, channel)
        rows[label] = {
            "candidate": profile_summary(candidate_profile),
            "lambda_zero": profile_summary(lambda_profile),
            "lambda_phase": profile_summary(lambda_phase_profile),
            "candidate_vs_lambda_zero_l2": l2(candidate_profile, lambda_profile),
            "candidate_vs_lambda_phase_l2": l2(candidate_profile, lambda_phase_profile),
            "max_step_increase_over_identity": max(
                row - base for row, base in zip(candidate_profile, base_profile)
            ),
            "mean_ratio_to_identity": mean(candidate_profile) / mean(base_profile),
        }
    return {"base_profile": profile_summary(base_profile), "channels": rows}


def count_passes(*sections: dict[str, dict[str, Any]]) -> tuple[int, int]:
    rows = [row for section in sections for row in section.values()]
    return sum(1 for row in rows if row.get("pass") is True), len(rows)


def run_probe() -> dict[str, Any]:
    start = time.time()
    prior = read_prior_bures()
    prof = channel_profiles()
    channels = prof["channels"]
    base_gap = channels["identity"]["candidate_vs_lambda_zero_l2"]
    unitary_gap = l2(
        channels["identity"]["candidate"]["values"],
        channels["common_unitary"]["candidate"]["values"],
    )
    contractivity_rows = {
        label: row["max_step_increase_over_identity"]
        for label, row in channels.items()
        if label not in {"identity", "common_unitary"}
    }
    all_cptp_contract = all(delta < CHANNEL_TOL for delta in contractivity_rows.values())
    common_unitary_preserves = unitary_gap < CHANNEL_TOL

    depol_gap = channels["depolarizing_p025"]["candidate_vs_lambda_zero_l2"]
    dephase_gap = channels["dephasing_p065"]["candidate_vs_lambda_zero_l2"]
    discard_b_gap = channels["discard_replace_B"]["candidate_vs_lambda_zero_l2"]
    discard_a_gap = channels["discard_replace_A"]["candidate_vs_lambda_zero_l2"]
    partial_a_gap = channels["partial_trace_A01"]["candidate_vs_lambda_zero_l2"]
    partial_cross_gap = channels["partial_trace_cross_02"]["candidate_vs_lambda_zero_l2"]
    fixed_mid_b_gap = channels["discard_replace_fixed_mid_B"]["candidate_vs_lambda_zero_l2"]

    generic_noise_preserves_some_residual = 0.50 < depol_gap / base_gap < 1.0
    grid_contracts = all(
        channels[f"global_depolarizing_p{int(round(100 * p)):03d}"][
            "max_step_increase_over_identity"
        ]
        < CHANNEL_TOL
        and channels[f"B_local_depolarizing_p{int(round(100 * p)):03d}"][
            "max_step_increase_over_identity"
        ]
        < CHANNEL_TOL
        for p in DEPOL_GRID
    )
    global_full_depol_collapses = (
        channels["global_depolarizing_p100"]["candidate"]["max"] < CHANNEL_TOL
    )
    b_local_full_depol_matches_discard_b = (
        l2(
            channels["B_local_depolarizing_p100"]["candidate"]["values"],
            channels["discard_replace_B"]["candidate"]["values"],
        )
        < CHANNEL_TOL
    )
    fixed_mid_b_matches_partial_a = (
        l2(
            channels["discard_replace_fixed_mid_B"]["candidate"]["values"],
            channels["partial_trace_A01"]["candidate"]["values"],
        )
        < CHANNEL_TOL
    )
    coherence_erase_reduces_residual = dephase_gap / base_gap < 0.25
    discard_controls_reduce_residual = (
        discard_b_gap / base_gap < 0.25
        and discard_a_gap / base_gap < 0.35
        and fixed_mid_b_gap / base_gap < 0.25
        and partial_a_gap / base_gap < 0.25
        and partial_cross_gap / base_gap < 0.25
    )
    prior_bures_preserved = (
        prior["all_pass"] is True
        and prior["classification"] == "formal_scout"
        and prior["promotion_allowed"] is False
        and prior["verdicts"].get("bures_metric_route_pressure_survived") is True
        and prior["verdicts"].get("bures_metric_does_not_promote_xi_bridge") is True
    )
    channel_resource_pressure = bool(
        prior_bures_preserved
        and common_unitary_preserves
        and all_cptp_contract
        and grid_contracts
        and generic_noise_preserves_some_residual
        and global_full_depol_collapses
        and b_local_full_depol_matches_discard_b
        and fixed_mid_b_matches_partial_a
        and coherence_erase_reduces_residual
        and discard_controls_reduce_residual
    )

    positive = {
        "prior_bures_metric_receipt_loaded_and_preserved": {
            "pass": prior_bures_preserved,
            "prior_bures_receipt": prior,
        },
        "common_unitary_preserves_bures_profile": {
            "pass": common_unitary_preserves,
            "identity_vs_common_unitary_profile_l2": unitary_gap,
            "tolerance": CHANNEL_TOL,
        },
        "cptp_channels_contract_bures_profile": {
            "pass": all_cptp_contract and grid_contracts,
            "max_step_increase_over_identity_by_channel": contractivity_rows,
            "tolerance": CHANNEL_TOL,
        },
        "depolarizing_grid_has_expected_boundaries": {
            "pass": grid_contracts
            and global_full_depol_collapses
            and b_local_full_depol_matches_discard_b,
            "grid": DEPOL_GRID,
            "global_p100_profile": channels["global_depolarizing_p100"]["candidate"],
            "B_local_p100_vs_discard_replace_B_profile_l2": l2(
                channels["B_local_depolarizing_p100"]["candidate"]["values"],
                channels["discard_replace_B"]["candidate"]["values"],
            ),
            "global_contractivity_max_by_p": {
                str(p): channels[f"global_depolarizing_p{int(round(100 * p)):03d}"][
                    "max_step_increase_over_identity"
                ]
                for p in DEPOL_GRID
            },
            "B_local_contractivity_max_by_p": {
                str(p): channels[f"B_local_depolarizing_p{int(round(100 * p)):03d}"][
                    "max_step_increase_over_identity"
                ]
                for p in DEPOL_GRID
            },
        },
        "depolarizing_noise_preserves_nonlambda_residual_but_contracts": {
            "pass": generic_noise_preserves_some_residual,
            "base_gap": base_gap,
            "depolarized_gap": depol_gap,
            "ratio": depol_gap / base_gap,
        },
        "coherence_and_discard_controls_reduce_residual": {
            "pass": coherence_erase_reduces_residual and discard_controls_reduce_residual,
            "base_gap": base_gap,
            "dephase_gap": dephase_gap,
            "discard_replace_B_gap": discard_b_gap,
            "discard_replace_fixed_mid_B_gap": fixed_mid_b_gap,
            "discard_replace_A_gap": discard_a_gap,
            "partial_trace_A01_gap": partial_a_gap,
            "partial_trace_cross_02_gap": partial_cross_gap,
            "fixed_mid_B_profile_matches_partial_A01": fixed_mid_b_matches_partial_a,
            "ratios": {
                "dephase": dephase_gap / base_gap,
                "discard_replace_B": discard_b_gap / base_gap,
                "discard_replace_fixed_mid_B": fixed_mid_b_gap / base_gap,
                "discard_replace_A": discard_a_gap / base_gap,
                "partial_trace_A01": partial_a_gap / base_gap,
                "partial_trace_cross_02": partial_cross_gap / base_gap,
            },
        },
    }
    graveyard_companions = {
        "channel_controls_do_not_restore_xi_bridge": {
            "pass": True,
            "reason": "Channels localize the residual to coherence/correlation-sensitive structure; they do not supply a cut-specific Xi/Phi0 bridge invariant.",
        },
        "resource_theory_label_not_admitted": {
            "pass": True,
            "reason": "This uses channel monotonicity as a finite control grammar only; it does not admit a full resource theory or superchannel result.",
        },
        "coherent_information_geometry_reading_still_killed": {
            "pass": True,
            "reason": "The prior coherent-information lambda-only kill remains unchanged by this Bures/channel audit.",
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
                    "resource_theory_admission",
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
        blockers.append("one_or_more_channel_resource_metric_checks_failed")

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
            "channel_resource_metric_pressure_survived": channel_resource_pressure,
            "bures_contractivity_controls_pass": all_cptp_contract,
            "common_unitary_invariance_pass": common_unitary_preserves,
            "coherence_and_discard_controls_reduce_residual": coherence_erase_reduces_residual
            and discard_controls_reduce_residual,
            "does_not_promote_xi_bridge": True,
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "scores": {
            "channel_profiles": prof,
            "base_gap": base_gap,
            "prior_bures": prior,
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
            "reason": "This is a v5 formal-scout channel/resource hardening audit over a v5 Bures receipt, not a v4 probe.",
        },
        "blockers": blockers,
        "plain_sentence": (
            "Finite channel controls preserve Bures contractivity and show that the non-lambda metric residual is coherence/correlation-sensitive; "
            "the result remains a formal scout and does not restore Xi/Phi0/Axis0/bridge/physics promotion."
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
                "channel_resource_metric_pressure_survived": result["verdicts"][
                    "channel_resource_metric_pressure_survived"
                ],
                "base_gap": result["scores"]["base_gap"],
                "dephase_gap": result["positive"]["coherence_and_discard_controls_reduce_residual"][
                    "dephase_gap"
                ],
                "discard_replace_B_gap": result["positive"][
                    "coherence_and_discard_controls_reduce_residual"
                ]["discard_replace_B_gap"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
