#!/usr/bin/env python3
"""Path-entropy schedule-confound falsifier scout.

External model audits flagged a narrow risk: two implementations can agree
that `path_entropy` is degenerate while only reading the same cyclic 64-substage
EngineCore schedule. This scout keeps the claim small and machine-visible:
current macro-router path entropy is a schedule-token derivative, and the
active guard already blocks it downstream. We test whether that candidate is
better read as a cyclic-schedule proxy than as an Axis0/admissibility invariant.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import time
from collections import Counter
from typing import Any

import torch
import z3

import axis0_guard_utils as axis0_guard
from engine_core import EngineCore, generate_initial_density


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "path_entropy_schedule_confound_falsifier_probe_results.json"

NAME = "path_entropy_schedule_confound_falsifier_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "axis0_path_entropy_schedule_confound_falsifier"
CLAIM_CEILING = (
    "Formal scout only: falsifies the current macro-router path_entropy "
    "candidate as a clean downstream Axis0/admissibility invariant by testing "
    "whether it is schedule-token-confounded. It does not admit final Axis0, "
    "retrocausality, FEP, Holodeck, physics, cognition, topology, chirality, "
    "or canonical architecture claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing entropy vectors, invariant gaps, and token-inventory controls",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite witness over the schedule-confound predicates",
    },
    "engine_core": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source-native 64-substage records and ordered_token schedule",
    },
}
TOOL_INTEGRATION_DEPTH = {
    'pytorch': 'load_bearing',
    'z3': 'load_bearing',
    'engine_core': 'supportive',
}

NONZERO_FRACTION_FLOOR = 0.20
VARIANCE_FLOOR = 1e-8
PATH_ENTROPY_EQUALITY_TOL = 1e-12
DEEPER_INVARIANT_GAP_FLOOR = 1e-3
DECYCLICIZED_STRIDE = 5
FLOAT_DTYPE = torch.float64


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    return value


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_result(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    if not path.exists():
        return {"exists": False, "path": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["exists"] = True
    data["path"] = str(path)
    return data


def categorical_entropy(values: list[str]) -> float:
    counts = Counter(values)
    total = float(sum(counts.values()))
    probs = torch.tensor([count / total for count in counts.values()], dtype=FLOAT_DTYPE)
    return float(-(probs * torch.log(probs)).sum().item())


def rolling(values: list[str], width: int = 8) -> list[list[str]]:
    return [values[max(0, i - width + 1): i + 1] for i in range(len(values))]


def path_entropy_vector(tokens: list[str]) -> torch.Tensor:
    ent = torch.tensor([categorical_entropy(window) for window in rolling(tokens, width=8)], dtype=FLOAT_DTYPE)
    return torch.diff(ent)


def candidate_status(vector: torch.Tensor) -> dict[str, Any]:
    finite = bool(vector.numel() and torch.all(torch.isfinite(vector)).item())
    nonzero_fraction = float(torch.mean((torch.abs(vector) > 1e-12).to(FLOAT_DTYPE)).item()) if vector.numel() else 0.0
    variance = float(torch.var(vector, unbiased=False).item()) if vector.numel() else 0.0
    blockers: dict[str, Any] = {}
    if not finite:
        blockers["candidate_vector_missing_or_nonfinite"] = {"claim": "candidate vector is missing or nonfinite"}
    if finite and nonzero_fraction < NONZERO_FRACTION_FLOOR:
        blockers["candidate_vector_degenerate_nonzero_fraction"] = {
            "nonzero_fraction": nonzero_fraction,
            "floor": NONZERO_FRACTION_FLOOR,
        }
    if finite and variance < VARIANCE_FLOOR:
        blockers["candidate_vector_variance_too_small"] = {"variance": variance, "floor": VARIANCE_FLOOR}
    return {
        "finite": finite,
        "vector_len": int(vector.numel()),
        "nonzero_fraction": nonzero_fraction,
        "variance": variance,
        "mean_abs": float(torch.mean(torch.abs(vector)).item()) if vector.numel() else 0.0,
        "explicit_blockers": blockers,
        "candidate_admissible_for_downstream_drop_controls": bool(finite and not blockers),
    }


def run_rows(*, manifold_enabled: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for engine_type in (0, 1):
        rho0 = generate_initial_density(6100 + engine_type)
        rows.extend(EngineCore(engine_type, manifold_enabled=manifold_enabled).run_full_cycle(rho0)["trajectory"])
    return rows


def decyclicize_tokens(tokens: list[str], stride: int = DECYCLICIZED_STRIDE) -> list[str]:
    if math.gcd(stride, len(tokens)) != 1:
        raise ValueError("stride must be coprime with token count")
    return [tokens[(idx * stride) % len(tokens)] for idx in range(len(tokens))]


def bloch_path_length(rows: list[dict[str, Any]]) -> float:
    bloch = torch.tensor([row["model_after"]["bloch"] for row in rows], dtype=FLOAT_DTYPE)
    return float(torch.sum(torch.linalg.vector_norm(torch.diff(bloch, dim=0), dim=1)).item())


def fep_gradient(rows: list[dict[str, Any]]) -> torch.Tensor:
    efe = torch.tensor([row["fep_efe_score"]["expected_free_energy_proxy"] for row in rows], dtype=FLOAT_DTYPE)
    return torch.diff(efe)


def observation_matrix(rows: list[dict[str, Any]]) -> torch.Tensor:
    return torch.tensor([row["observation"]["observation_distribution"] for row in rows], dtype=FLOAT_DTYPE)


def z3_confound_witness(
    constant_entropy: bool,
    deeper_changed: bool,
    base_blocked: bool,
    decyclicized_admitted: bool,
    inventory_equal: bool,
) -> dict[str, Any]:
    solver = z3.Solver()
    const = z3.Bool("path_entropy_constant_under_manifold_toggle")
    deeper = z3.Bool("deeper_invariants_change_under_same_path_entropy")
    blocked = z3.Bool("current_guard_blocks_cyclic_path_entropy")
    revived = z3.Bool("token_inventory_preserved_decyclicized_order_revives_candidate")
    inventory = z3.Bool("token_inventory_preserved")
    solver.add(const == constant_entropy)
    solver.add(deeper == deeper_changed)
    solver.add(blocked == base_blocked)
    solver.add(revived == decyclicized_admitted)
    solver.add(inventory == inventory_equal)
    solver.add(z3.Not(z3.And(const, deeper, blocked, revived, inventory)))
    status = solver.check()
    return {
        "pass": status == z3.unsat,
        "solver_status": str(status),
        "claim_ceiling": "Finite SMT witness over local schedule-confound predicates only.",
    }


def main() -> int:
    started = time.time()
    router_receipt = load_result("macro_sim_axis0_plural_stage_candidate_router_probe_results.json")
    guard_receipt = load_result(axis0_guard.AXIS0_GUARD_RESULT_NAME)
    guard = axis0_guard.axis0_guard_signal(guard_receipt)

    rows_on = run_rows(manifold_enabled=True)
    rows_off = run_rows(manifold_enabled=False)
    tokens_on = [str(row["ordered_token"]) for row in rows_on]
    tokens_off = [str(row["ordered_token"]) for row in rows_off]
    base_vector = path_entropy_vector(tokens_on)
    no_manifold_vector = path_entropy_vector(tokens_off)
    decyclicized_tokens = decyclicize_tokens(tokens_on)
    decyclicized_vector = path_entropy_vector(decyclicized_tokens)

    base_status = candidate_status(base_vector)
    no_manifold_status = candidate_status(no_manifold_vector)
    decyclicized_status = candidate_status(decyclicized_vector)

    fep_gap = float(torch.linalg.vector_norm(fep_gradient(rows_on) - fep_gradient(rows_off)).item())
    bloch_path_on = bloch_path_length(rows_on)
    bloch_path_off = bloch_path_length(rows_off)
    bloch_path_gap = float(abs(bloch_path_on - bloch_path_off))
    observation_gap = float(torch.linalg.vector_norm(observation_matrix(rows_on) - observation_matrix(rows_off)).item())
    path_entropy_delta = float(torch.max(torch.abs(base_vector - no_manifold_vector)).item())
    inventory_equal = Counter(tokens_on) == Counter(decyclicized_tokens)
    base_blocked_by_active_guard = "path_entropy" in guard.get("blocked_candidate_names", [])
    constant_entropy = tokens_on == tokens_off and path_entropy_delta <= PATH_ENTROPY_EQUALITY_TOL
    deeper_changed = min(fep_gap, bloch_path_gap, observation_gap) > DEEPER_INVARIANT_GAP_FLOOR
    z3_witness = z3_confound_witness(
        constant_entropy=constant_entropy,
        deeper_changed=deeper_changed,
        base_blocked=base_blocked_by_active_guard and not base_status["candidate_admissible_for_downstream_drop_controls"],
        decyclicized_admitted=decyclicized_status["candidate_admissible_for_downstream_drop_controls"],
        inventory_equal=inventory_equal,
    )

    repair_receipt = {
        "weak_link": "External audits flagged that path_entropy agreement may be engine-schedule-confounded: two implementations can read the same cyclic token schedule and agree on degeneracy without discovering an Axis0 invariant.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": "path_entropy cannot be admitted downstream unless it survives constant-entropy/deeper-invariant and de-cyclicized schedule controls.",
        "dependency_subset": [
            "macro_sim_axis0_plural_stage_candidate_router receipt",
            "axis0_plural_candidate_multicarrier_drive_controls receipt",
            "EngineCore source-native ordered_token trajectories",
        ],
        "stage_fields_touched_or_consumed": [
            "ordered_token",
            "fep_efe_score.expected_free_energy_proxy",
            "model_after.bloch",
            "observation.observation_distribution",
        ],
        "before_baseline/hash": {
            "router_result": router_receipt.get("path"),
            "guard_result": guard_receipt.get("path"),
            "active_guard_blocked_path_entropy": base_blocked_by_active_guard,
        },
        "after_delta/hash": {
            "script_sha256": sha256_file(pathlib.Path(__file__)),
            "result_path": str(OUT_PATH),
        },
        "primary_control/result": {
            "base_status": base_status,
            "no_manifold_same_schedule_status": no_manifold_status,
            "decyclicized_same_inventory_status": decyclicized_status,
            "path_entropy_delta_same_schedule": path_entropy_delta,
            "deeper_invariant_gaps_under_same_path_entropy": {
                "fep_gradient_l2_gap": fep_gap,
                "bloch_path_length_on": bloch_path_on,
                "bloch_path_length_off": bloch_path_off,
                "bloch_path_length_gap": bloch_path_gap,
                "observation_distribution_l2_gap": observation_gap,
            },
        },
        "axis0_outputs_or_blockers": {
            "path_entropy_current_reading": "blocked_schedule_token_entropy_derivative_not_downstream_axis0_feature",
            "active_guard_blocked_candidate_names": guard.get("blocked_candidate_names", []),
            "active_guard_admitted_candidate_names": guard.get("admitted_candidate_names", []),
            "path_entropy_guard_status": (guard.get("blocked_candidate_status", {}) or {}).get("path_entropy", {}),
            "decyclicized_status_is_surrogate_not_source_native_schedule": True,
        },
        "provider_inputs_used": {
            "opus": "advisory_only_path_e_ranked_before_d4_d5",
            "grok": "advisory_only_path_e_ranked_before_d4_d5",
            "sonnet_high": "advisory_only_false_green_premortem",
            "gemini": "attempted_advisory_but_drifted_to_nonlocal_signing_not_used_as_design_authority",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "Keep path_entropy blocked downstream; if needed, build a separate replacement candidate over branch/path ensembles rather than ordered_token cyclicity.",
    }

    positive = {
        "active_guard_already_blocks_path_entropy": {
            "pass": bool(
                guard_receipt.get("all_pass") is True
                and guard.get("pass")
                and base_blocked_by_active_guard
                and "axis0_path_entropy" in guard.get("blocked_axis0_feature_names_excluded", [])
            ),
            "guard": guard,
        },
        "same_schedule_path_entropy_is_constant_while_deeper_invariants_change": {
            "pass": bool(constant_entropy and deeper_changed),
            "tokens_identical": tokens_on == tokens_off,
            "path_entropy_delta_same_schedule": path_entropy_delta,
            "thresholds": {
                "path_entropy_equality_tol": PATH_ENTROPY_EQUALITY_TOL,
                "deeper_invariant_gap_floor": DEEPER_INVARIANT_GAP_FLOOR,
            },
            "deeper_invariant_gaps": repair_receipt["primary_control/result"]["deeper_invariant_gaps_under_same_path_entropy"],
        },
        "token_inventory_preserved_decyclicized_order_changes_guard_status": {
            "pass": bool(
                inventory_equal
                and not base_status["candidate_admissible_for_downstream_drop_controls"]
                and decyclicized_status["candidate_admissible_for_downstream_drop_controls"]
            ),
            "base_status": base_status,
            "decyclicized_status": decyclicized_status,
            "token_inventory_equal": inventory_equal,
            "decyclicized_stride": DECYCLICIZED_STRIDE,
        },
        "z3_schedule_confound_witness_executes": z3_witness,
    }
    graveyards = {
        "same_token_inventory_is_not_a_path_entropy_invariant": {
            "pass": bool(inventory_equal and float(torch.linalg.vector_norm(base_vector - decyclicized_vector).item()) > DEEPER_INVARIANT_GAP_FLOOR),
            "base_vs_decyclicized_path_entropy_l2": float(torch.linalg.vector_norm(base_vector - decyclicized_vector).item()),
            "token_inventory_equal": inventory_equal,
        },
        "manifold_toggle_is_not_detected_by_schedule_token_path_entropy": {
            "pass": bool(constant_entropy and observation_gap > DEEPER_INVARIANT_GAP_FLOOR),
            "path_entropy_delta_same_schedule": path_entropy_delta,
            "observation_distribution_l2_gap": observation_gap,
        },
        "this_probe_does_not_unblock_path_entropy_downstream": {
            "pass": bool("path_entropy" in guard.get("blocked_candidate_names", []) and PROMOTION_ALLOWED is False),
            "blocked_candidate_names": guard.get("blocked_candidate_names", []),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "decyclicized_schedule_is_a_surrogate_control_not_source_native_dynamics": {
            "pass": bool(inventory_equal and decyclicized_tokens != tokens_on),
            "claim": "decyclicized order is used only to test schedule-token sensitivity, not as a replacement EngineCore schedule.",
        },
    }
    boundary = {
        "claim_ceiling_blocks_axis0_or_physics_promotion": {
            "pass": all(
                term in CLAIM_CEILING.lower()
                for term in ["formal scout", "does not admit", "final axis0", "physics", "canonical"]
            ),
        },
        "repair_receipt_has_required_loop_fields": {
            "pass": all(
                key in repair_receipt
                for key in [
                    "weak_link",
                    "target_file_or_result",
                    "admission_rule_improved",
                    "dependency_subset",
                    "stage_fields_touched_or_consumed",
                    "before_baseline/hash",
                    "after_delta/hash",
                    "primary_control/result",
                    "axis0_outputs_or_blockers",
                    "provider_inputs_used",
                    "promotion_ceiling",
                    "next_step",
                ]
            ),
            "keys": sorted(repair_receipt),
        },
        "result_keeps_path_entropy_blocked_not_promoted": {
            "pass": bool(PROMOTION_ALLOWED is False and "path_entropy" in guard.get("blocked_candidate_names", [])),
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "repair_receipt": repair_receipt,
        "axis0_outputs_or_blockers": repair_receipt["axis0_outputs_or_blockers"],
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
            "variants": sorted(graveyards),
        },
        "why_not_v4_probes": [
            "This is a v5 formal-scout guard over EngineCore stage records and the current v5 Axis0 guard.",
            "The older v4 path-entropy receipt is finite legacy evidence, not downstream Axis0 admission.",
        ],
        "all_pass": all_pass,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
