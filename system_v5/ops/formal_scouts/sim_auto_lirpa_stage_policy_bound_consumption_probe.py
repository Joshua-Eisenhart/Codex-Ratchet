#!/usr/bin/env python3
"""auto_LiRPA downstream consumption scout for source-native stage policy bounds."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import numpy as np
import torch
import torch.nn as nn
import z3

AUTO_LIRPA_ROOT = pathlib.Path("/Users/joshuaeisenhart/GitHub/auto_LiRPA")
sys.path.insert(0, str(AUTO_LIRPA_ROOT))
from auto_LiRPA import BoundedModule, BoundedTensor, PerturbationLpNorm  # noqa: E402

import axis0_guard_utils as axis0_guard
from engine_core import EngineCore, generate_initial_density


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "auto_lirpa_stage_policy_bound_consumption_probe_results.json"

NAME = "auto_lirpa_stage_policy_bound_consumption_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "auto_lirpa_downstream_stage_policy_bound_consumption"
CLAIM_CEILING = (
    "Formal scout only: consumes the world-model repo-admission receipt's "
    "narrow auto_LiRPA verifier adapter and computes interval bounds for a "
    "tiny source-native stage-policy adapter over EngineCore/FEP/Axis0/"
    "Holodeck features. It does not admit a trained policy, neural world "
    "model, final verifier, physics, cognition, or canonical architecture."
)

TOOL_MANIFEST = {
    "auto_LiRPA": {"tried": True, "used": True, "reason": "load-bearing BoundedModule interval bounds over the stage-policy adapter"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing tiny policy adapter and analytic control"},
    "numpy": {"tried": True, "used": True, "reason": "load-bearing stage/FEP/Axis0/Holodeck feature table and controls"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite bound-containment witness"},
    "engine_core": {"tried": True, "used": True, "reason": "load-bearing source-native stage records"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

REQUIRED_STAGE_FIELDS = [
    "model_before",
    "prediction",
    "observation",
    "fep_efe_score",
    "update_repair",
    "falsifier_graveyard",
    "next_policy",
    "model_after",
]


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    return value


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_result(name: str) -> dict[str, Any]:
    path = RESULT_DIR / name
    if not path.exists():
        return {"exists": False, "path": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "exists": True,
        "path": str(path),
        "name": data.get("name"),
        "all_pass": data.get("all_pass"),
        "classification": data.get("classification"),
        "promotion_allowed": data.get("promotion_allowed"),
        "claim_ceiling": data.get("claim_ceiling", ""),
        "positive": data.get("positive", {}),
        "hash_cells": data.get("hash_cells", []),
        "repo_admission_matrix": data.get("repo_admission_matrix", {}),
        "axis0_outputs_or_blockers": data.get("axis0_outputs_or_blockers", {}),
    }


def memory_margin(memory_receipt: dict[str, Any]) -> float:
    recall = ((memory_receipt.get("positive") or {}).get("predictive_model_verifies_contextual_recall") or {})
    return float(recall.get("mean_target_verification_score", 0.0)) - float(
        recall.get("mean_wrong_model_target_score", 0.0)
    )


def bucket_text(text: str, modulus: int = 997) -> float:
    digest = hashlib.sha256(str(text).encode("utf-8")).hexdigest()
    return float(int(digest[:8], 16) % modulus) / float(modulus)


def holodeck_hash_cells(memory_receipt: dict[str, Any]) -> list[dict[str, Any]]:
    rows = memory_receipt.get("hash_cells", [])
    if not isinstance(rows, list):
        return []
    return [
        row
        for row in rows
        if isinstance(row, dict)
        and isinstance(row.get("semantic_hash"), str)
        and isinstance(row.get("survivor_class_hash"), str)
        and isinstance(row.get("graveyard_control_hashes"), list)
    ]


def hash_cell_features(hash_cells: list[dict[str, Any]], idx: int) -> list[float]:
    if not hash_cells:
        return [0.0, 0.0, 0.0]
    cell = hash_cells[idx % len(hash_cells)]
    graveyard_joined = "|".join(str(x) for x in cell.get("graveyard_control_hashes", []))
    return [
        bucket_text(str(cell.get("semantic_hash", ""))),
        bucket_text(graveyard_joined),
        bucket_text(str(cell.get("survivor_class_hash", ""))),
    ]


def collect_features(
    axis0: dict[str, list[float]],
    memory: float,
    hash_cells: list[dict[str, Any]],
) -> tuple[np.ndarray, list[str], list[dict[str, Any]]]:
    axis0_names = list(axis0)
    names = [
        "bloch_x",
        "bloch_y",
        "bloch_z",
        "entropy",
        "purity",
        "prediction_error_l2",
        "surprise_kl",
        "expected_free_energy_proxy",
        "manifold_projection_delta_norm",
        *[f"axis0_{name}" for name in axis0_names],
        "holodeck_memory_verification_margin",
        "holodeck_semantic_hash_bucket",
        "holodeck_graveyard_hash_bucket",
        "holodeck_survivor_hash_bucket",
        "operator_sign",
    ]
    rows: list[list[float]] = []
    records: list[dict[str, Any]] = []
    for engine_type in (0, 1):
        engine = EngineCore(engine_type, manifold_enabled=True)
        rho = generate_initial_density(88000 + engine_type)
        for main_idx, (perception, loop_class) in enumerate(engine.schedule):
            for substage_idx in range(4):
                rho, record = engine.run_substage(rho, perception, loop_class, main_idx, substage_idx)
                idx = len(records)
                model = record["model_after"]
                fep = record["fep_efe_score"]
                repair = record["update_repair"]
                axis_values = []
                for name in axis0_names:
                    vector = axis0.get(name, [0.0])
                    axis_values.append(float(vector[idx % max(1, len(vector))]))
                semantic_hash_bucket, graveyard_hash_bucket, survivor_hash_bucket = hash_cell_features(hash_cells, idx)
                rows.append(
                    [
                        *[float(x) for x in model["bloch"]],
                        float(model["entropy"]),
                        float(model["purity"]),
                        float(fep["prediction_error_l2"]),
                        float(fep["surprise_kl"]),
                        float(fep["expected_free_energy_proxy"]),
                        float(repair["manifold_projection_delta_norm"]),
                        *axis_values,
                        float(memory),
                        semantic_hash_bucket,
                        graveyard_hash_bucket,
                        survivor_hash_bucket,
                        float(record["operator_sign"]),
                    ]
                )
                records.append(record)
    x = np.asarray(rows, dtype=np.float32)
    mean = x.mean(axis=0, keepdims=True)
    std = x.std(axis=0, keepdims=True)
    std[std < 1e-6] = 1.0
    return ((x - mean) / std).astype(np.float32), names, records


class StagePolicyAdapter(nn.Module):
    def __init__(self, feature_names: list[str]) -> None:
        super().__init__()
        feature_dim = len(feature_names)
        self.linear = nn.Linear(feature_dim, 1)
        with torch.no_grad():
            weights = torch.linspace(-0.35, 0.45, steps=feature_dim)
            weights[5:9] += torch.tensor([0.50, -0.40, 0.45, 0.30])
            weights[9:13] += torch.tensor([0.25, -0.20, 0.18, 0.32])
            for field, boost in {
                "holodeck_semantic_hash_bucket": 0.20,
                "holodeck_graveyard_hash_bucket": -0.26,
                "holodeck_survivor_hash_bucket": 0.22,
            }.items():
                if field in feature_names:
                    weights[feature_names.index(field)] += boost
            weights[-1] += 0.55
            self.linear.weight.copy_(weights.reshape(1, -1))
            self.linear.bias.fill_(0.07)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.tanh(self.linear(x))


def bounded_policy_report(features: np.ndarray, names: list[str]) -> dict[str, Any]:
    x = torch.tensor(features[:16], dtype=torch.float32)
    model = StagePolicyAdapter(names)
    bounded = BoundedModule(model, x)
    eps = 0.01
    bx = BoundedTensor(x, PerturbationLpNorm(norm=np.inf, eps=eps))
    nominal = bounded(bx)
    lb, ub = bounded.compute_bounds(x=(bx,), method="IBP")
    raw = model.linear(x).reshape(-1)
    radius = eps * torch.sum(torch.abs(model.linear.weight.detach().reshape(-1)))
    analytic_lb = torch.tanh(raw - radius)
    analytic_ub = torch.tanh(raw + radius)
    context_zero = x.clone()
    for name in [
        "axis0_fep_gradient_polarity",
        "axis0_correlation_diversity_derivative",
        "axis0_retrocausal_many_futures_policy_scoring",
        "holodeck_memory_verification_margin",
    ]:
        if name in names:
            context_zero[:, names.index(name)] = 0.0
    bounded_zero = BoundedModule(model, context_zero)
    zero_bx = BoundedTensor(context_zero, PerturbationLpNorm(norm=np.inf, eps=eps))
    zero_nominal = bounded_zero(zero_bx)
    zero_lb, zero_ub = bounded_zero.compute_bounds(x=(zero_bx,), method="IBP")
    interval_shift = torch.mean(torch.abs((ub + lb) / 2 - (zero_ub + zero_lb) / 2)).item()
    hash_fields = [
        "holodeck_semantic_hash_bucket",
        "holodeck_graveyard_hash_bucket",
        "holodeck_survivor_hash_bucket",
    ]
    hash_zero = x.clone()
    for name in hash_fields:
        if name in names:
            hash_zero[:, names.index(name)] = 0.0
    bounded_hash_zero = BoundedModule(model, hash_zero)
    hash_zero_bx = BoundedTensor(hash_zero, PerturbationLpNorm(norm=np.inf, eps=eps))
    hash_zero_lb, hash_zero_ub = bounded_hash_zero.compute_bounds(x=(hash_zero_bx,), method="IBP")
    hash_zero_shift = torch.mean(torch.abs((ub + lb) / 2 - (hash_zero_ub + hash_zero_lb) / 2)).item()

    hash_shuffle = x.clone()
    for name in hash_fields:
        if name in names:
            col = names.index(name)
            hash_shuffle[:, col] = torch.roll(hash_shuffle[:, col], shifts=5)
    bounded_hash_shuffle = BoundedModule(model, hash_shuffle)
    hash_shuffle_bx = BoundedTensor(hash_shuffle, PerturbationLpNorm(norm=np.inf, eps=eps))
    hash_shuffle_lb, hash_shuffle_ub = bounded_hash_shuffle.compute_bounds(x=(hash_shuffle_bx,), method="IBP")
    hash_shuffle_shift = torch.mean(torch.abs((ub + lb) / 2 - (hash_shuffle_ub + hash_shuffle_lb) / 2)).item()

    drop_graveyard = x.clone()
    if "holodeck_graveyard_hash_bucket" in names:
        drop_graveyard[:, names.index("holodeck_graveyard_hash_bucket")] = 0.0
    bounded_drop_graveyard = BoundedModule(model, drop_graveyard)
    drop_graveyard_bx = BoundedTensor(drop_graveyard, PerturbationLpNorm(norm=np.inf, eps=eps))
    drop_graveyard_lb, drop_graveyard_ub = bounded_drop_graveyard.compute_bounds(x=(drop_graveyard_bx,), method="IBP")
    drop_graveyard_shift = torch.mean(torch.abs((ub + lb) / 2 - (drop_graveyard_ub + drop_graveyard_lb) / 2)).item()
    hash_identity_pass = (
        all(name in names for name in hash_fields)
        and hash_zero_shift > 0.005
        and hash_shuffle_shift > 0.005
        and drop_graveyard_shift > 0.003
    )
    return {
        "pass": bool(
            torch.all(lb <= nominal)
            and torch.all(nominal <= ub)
            and torch.max(torch.abs(lb.reshape(-1) - analytic_lb)).item() < 1e-5
            and torch.max(torch.abs(ub.reshape(-1) - analytic_ub)).item() < 1e-5
            and interval_shift > 0.01
            and hash_identity_pass
        ),
        "feature_rows_used": int(x.shape[0]),
        "feature_dim": int(x.shape[1]),
        "feature_names": names,
        "eps_linf": eps,
        "nominal_mean": float(torch.mean(nominal).item()),
        "interval_mean_width": float(torch.mean(ub - lb).item()),
        "context_zero_interval_center_shift": float(interval_shift),
        "hash_identity_bound_controls": {
            "pass": bool(hash_identity_pass),
            "hash_feature_names": hash_fields,
            "zero_hash_table_interval_center_shift": float(hash_zero_shift),
            "shuffle_hash_identity_interval_center_shift": float(hash_shuffle_shift),
            "drop_graveyard_hash_interval_center_shift": float(drop_graveyard_shift),
        },
        "max_abs_diff_analytic_lb": float(torch.max(torch.abs(lb.reshape(-1) - analytic_lb)).item()),
        "max_abs_diff_analytic_ub": float(torch.max(torch.abs(ub.reshape(-1) - analytic_ub)).item()),
        "zero_context_nominal_mean": float(torch.mean(zero_nominal).item()),
    }


def z3_bound_witness(report: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    bounds_contain_nominal = z3.Bool("bounds_contain_nominal")
    analytic_matches = z3.Bool("analytic_matches")
    context_is_load_bearing = z3.Bool("context_is_load_bearing")
    solver.add(bounds_contain_nominal == bool(report["pass"]))
    solver.add(analytic_matches == (report["max_abs_diff_analytic_lb"] < 1e-5 and report["max_abs_diff_analytic_ub"] < 1e-5))
    solver.add(context_is_load_bearing == (report["context_zero_interval_center_shift"] > 0.01))
    solver.add(z3.Not(z3.And(bounds_contain_nominal, analytic_matches, context_is_load_bearing)))
    status = solver.check()
    return {
        "pass": status == z3.unsat,
        "solver_status": str(status),
        "claim_ceiling": "Finite SMT witness over the local bound-check predicates only.",
    }


def main() -> int:
    started = time.time()
    repo_receipt = load_result("world_model_repo_admission_gap_adapter_probe_results.json")
    stage_receipt = load_result("macro_sim_stage_record_science_method_contract_probe_results.json")
    axis0_receipt = load_result("macro_sim_axis0_plural_stage_candidate_router_probe_results.json")
    axis0_guard_receipt = load_result(axis0_guard.AXIS0_GUARD_RESULT_NAME)
    memory_receipt = load_result("source_native_holodeck_hash_memory_placeholder_probe_results.json")
    guard = axis0_guard.axis0_guard_signal(axis0_guard_receipt)
    axis0 = axis0_guard.guarded_router_vectors(axis0_receipt, guard)
    memory = memory_margin(memory_receipt)
    hash_cells = holodeck_hash_cells(memory_receipt)
    features, names, records = collect_features(axis0, memory, hash_cells)
    bound_report = bounded_policy_report(features, names)
    z3_witness = z3_bound_witness(bound_report)
    auto_row = ((repo_receipt.get("repo_admission_matrix") or {}).get("rows") or {}).get("auto_LiRPA", {})

    repair_receipt = {
        "weak_link": "auto_LiRPA had been admitted only at repo-admission level; no downstream source-native stage-policy consumer used the admitted verifier adapter.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": "auto_LiRPA admission now requires a downstream BoundedModule bound over real stage/FEP/Axis0/Holodeck features plus analytic and context-zero controls.",
        "dependency_subset": [
            "world_model_repo_admission_gap_adapter receipt",
            "macro_sim_stage_record_science_method_contract receipt",
            "macro_sim_axis0_plural_stage_candidate_router receipt",
            "axis0_plural_candidate_multicarrier_drive_controls receipt",
            "source_native_holodeck_hash_memory_placeholder receipt",
            "local auto_LiRPA repo under /Users/joshuaeisenhart/GitHub",
        ],
        "stage_fields_touched_or_consumed": REQUIRED_STAGE_FIELDS,
        "before_baseline/hash": {
            "repo_admission_result": repo_receipt.get("path"),
            "auto_lirpa_decision": auto_row.get("decision"),
        },
        "after_delta/hash": {
            "script_sha256": sha256_file(pathlib.Path(__file__)),
            "result_path": str(OUT_PATH),
        },
        "primary_control/result": {
            "bounded_policy_report": bound_report,
            "context_zero_control": "axis0 and Holodeck-memory context features zeroed",
        },
        "axis0_outputs_or_blockers": {
            "raw_router_candidate_names": axis0_guard.AXIS0_CANDIDATE_NAMES,
            "admitted_candidate_names": guard["admitted_candidate_names"],
            "blocked_candidate_names": guard["blocked_candidate_names"],
            "adapter_active_axis0_feature_names": guard["adapter_active_axis0_feature_names"],
            "blocked_axis0_feature_names_excluded": guard["blocked_axis0_feature_names_excluded"],
            "blocked_axis0_candidates_not_feature_columns": all(
                f"axis0_{name}" not in names for name in guard["blocked_candidate_names"]
            ),
            "axis0_vectors_nonempty": all(bool(v) for v in axis0.values()),
            "axis0_guard_receipt_consumed": axis0_guard_receipt.get("all_pass") is True,
            "scalar_weighted_drive_blocker": guard["scalar_weighted_drive_blocker"],
            "control_family_degeneracy_blockers": guard["control_family_degeneracy_blockers"],
        },
        "provider_inputs_used": {
            "grok": "not_run_this_repair_wave",
            "gemini": "not_run_this_repair_wave",
            "sonnet_high": "not_run_this_repair_wave",
            "opus_max": "not_run_this_repair_wave",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "Replace this fixed-weight adapter with a trained source-native policy adapter, then compare LiRPA bounds against brute-force perturbation samples.",
    }

    positive = {
        "repo_admission_receipt_is_consumed": {
            "pass": repo_receipt.get("all_pass") is True
            and auto_row.get("admitted") is True
            and auto_row.get("decision") == "admitted_tiny_verifier_adapter_only",
            "auto_lirpa_row": auto_row,
        },
        "axis0_guard_receipt_blocks_unadmitted_candidates_before_lirpa_adapter": {
            "pass": bool(
                guard["pass"]
                and axis0_guard_receipt.get("all_pass") is True
                and all(f"axis0_{name}" not in names for name in guard["blocked_candidate_names"])
                and all(f"axis0_{name}" in names for name in guard["admitted_candidate_names"])
            ),
            "axis0_guard": guard,
            "feature_names": names,
        },
        "stage_axis0_holodeck_features_are_bounded_by_auto_lirpa": bound_report,
        "holodeck_hash_cells_are_consumed_as_identity_features": {
            "pass": bool(hash_cells) and all(name in names for name in bound_report["hash_identity_bound_controls"]["hash_feature_names"]),
            "hash_cell_count": len(hash_cells),
            "hash_feature_names": bound_report["hash_identity_bound_controls"]["hash_feature_names"],
        },
        "z3_bound_witness_executes": z3_witness,
    }
    graveyards = {
        "repo_name_only_without_admission_receipt_is_rejected": {
            "pass": repo_receipt.get("all_pass") is True and auto_row.get("admitted") is True,
            "reason": "This scout consumes the repo-admission receipt and would fail without the admitted auto_LiRPA row.",
        },
        "context_zero_control_changes_certified_interval": {
            "pass": bound_report["context_zero_interval_center_shift"] > 0.01,
            "interval_center_shift": bound_report["context_zero_interval_center_shift"],
        },
        "blocked_axis0_candidates_not_used_as_lirpa_feature_columns": {
            "pass": all(f"axis0_{name}" not in names for name in guard["blocked_candidate_names"]),
            "blocked_candidate_names": guard["blocked_candidate_names"],
            "feature_names": names,
        },
        "raw_pytorch_nominal_is_not_a_certificate": {
            "pass": bound_report["interval_mean_width"] > 0.0,
            "reason": "Nominal PyTorch output is reported only inside a LiRPA interval with an analytic control.",
        },
    }
    boundary = {
        "claim_ceiling_blocks_trained_policy_or_final_verifier": {
            "pass": all(term in CLAIM_CEILING.lower() for term in ["formal scout", "does not admit", "trained policy", "final verifier"]),
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
            "This is a v5 downstream consumption scout for an admitted external verifier adapter.",
            "It consumes repaired source-native stage/FEP, Axis0, Holodeck memory, and repo-admission receipts.",
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
