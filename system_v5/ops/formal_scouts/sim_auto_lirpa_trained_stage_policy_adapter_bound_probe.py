#!/usr/bin/env python3
"""Trained auto_LiRPA stage-policy adapter bound scout.

This repairs the next weak link after the fixed-weight LiRPA consumer: the
verifier must bound a trained source-native policy adapter, and the bounds must
be checked against brute-force perturbation samples.

Formal scout only. The target is a bounded context-conditioned next-operator
policy class derived from existing EngineCore stage records, FEP fields,
Axis0 plural candidates, and Holodeck memory verification margin. This is not
a trained production policy, not a world model, and not a final verifier.
"""

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

import torch
import torch.nn as nn
import torch.optim as optim
import z3

AUTO_LIRPA_ROOT = pathlib.Path("/Users/joshuaeisenhart/GitHub/auto_LiRPA")
sys.path.insert(0, str(AUTO_LIRPA_ROOT))
from auto_LiRPA import BoundedModule, BoundedTensor, PerturbationLpNorm  # noqa: E402

import axis0_guard_utils as axis0_guard
from engine_core import EngineCore, generate_initial_density


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "auto_lirpa_trained_stage_policy_adapter_bound_probe_results.json"

NAME = "auto_lirpa_trained_stage_policy_adapter_bound_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "auto_lirpa_trained_stage_policy_adapter_bounds"
CLAIM_CEILING = (
    "Formal scout only: trains a tiny source-native, context-conditioned "
    "stage-policy adapter and checks auto_LiRPA interval bounds against "
    "brute-force perturbation samples. It does not admit a production policy, "
    "neural world model, final verifier, final FEP system, physics, cognition, "
    "or canonical architecture."
)

TOOL_MANIFEST = {
    "auto_LiRPA": {"tried": True, "used": True, "reason": "load-bearing certified interval bounds for the trained stage-policy adapter"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing trained adapter, shuffled-label control, and brute-force perturbation samples"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite witness for trained accuracy plus bound containment predicates"},
    "engine_core": {"tried": True, "used": True, "reason": "supportive source-native stage records and policy fields consumed by the trained adapter fixture"},
}
TOOL_INTEGRATION_DEPTH = {
    "auto_LiRPA": "load_bearing",
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "engine_core": "supportive",
}

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
OPERATORS = ["Ti", "Te", "Fi", "Fe"]
PERCEPTIONS = ["Se", "Ne", "Ni", "Si"]


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
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


HASH_FEATURE_NAMES = [
    "holodeck_semantic_hash_bucket",
    "holodeck_graveyard_hash_bucket",
    "holodeck_survivor_hash_bucket",
]
HASH_CONTROL_THRESHOLDS = {
    "zero_hash_table_interval_center_shift_min": 0.005,
    "shuffle_hash_identity_interval_center_shift_min": 0.005,
    "drop_graveyard_hash_interval_center_shift_min": 0.003,
}


def collect_training_rows(
    axis0: dict[str, Any],
    memory: float,
    hash_cells: list[dict[str, Any]],
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, list[str], list[dict[str, Any]]]:
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
        "prediction_observation_delta_0",
        "prediction_observation_delta_1",
        "prediction_observation_delta_2",
        *[f"current_operator_{op}" for op in OPERATORS],
        *[f"perception_{perception}" for perception in PERCEPTIONS],
        *[f"axis0_{name}" for name in axis0_names],
        "holodeck_memory_phase",
        *HASH_FEATURE_NAMES,
    ]
    rows: list[list[float]] = []
    labels: list[int] = []
    seeds: list[int] = []
    records: list[dict[str, Any]] = []
    for seed_idx in range(8):
        for engine_type in (0, 1):
            engine = EngineCore(engine_type, manifold_enabled=True)
            rho = generate_initial_density(66000 + 100 * seed_idx + engine_type)
            for main_idx, (perception, loop_class) in enumerate(engine.schedule):
                for substage_idx in range(4):
                    rho, record = engine.run_substage(rho, perception, loop_class, main_idx, substage_idx)
                    idx = len(records)
                    model = record["model_after"]
                    fep = record["fep_efe_score"]
                    repair = record["update_repair"]
                    pred = torch.tensor(record["prediction"]["observation_distribution"], dtype=torch.float64)
                    obs = torch.tensor(record["observation"]["observation_distribution"], dtype=torch.float64)
                    axis_values = [
                        float(axis0[name][idx % len(axis0[name])]) if len(axis0[name]) else 0.0
                        for name in axis0_names
                    ]
                    semantic_hash_bucket, graveyard_hash_bucket, survivor_hash_bucket = hash_cell_features(hash_cells, idx)
                    memory_phase = float(memory * (1.0 if idx % 2 == 0 else -0.5))
                    hash_identity_signal = semantic_hash_bucket - graveyard_hash_bucket + survivor_hash_bucket
                    context_score = float(
                        sum(axis_values)
                        + 0.15 * memory_phase
                        + 0.35 * hash_identity_signal
                        + 0.10 * fep["prediction_error_l2"]
                    )
                    context_shift = 1 if context_score > 0.15 else 0
                    base_label = OPERATORS.index(record["next_policy"]["operator"])
                    labels.append((base_label + context_shift) % len(OPERATORS))
                    rows.append(
                        [
                            *[float(x) for x in model["bloch"]],
                            float(model["entropy"]),
                            float(model["purity"]),
                            float(fep["prediction_error_l2"]),
                            float(fep["surprise_kl"]),
                            float(fep["expected_free_energy_proxy"]),
                            float(repair["manifold_projection_delta_norm"]),
                            *[float(x.item()) for x in (pred - obs)[:3]],
                            *[1.0 if record["operator"] == op else 0.0 for op in OPERATORS],
                            *[1.0 if perception == item else 0.0 for item in PERCEPTIONS],
                            *axis_values,
                            memory_phase,
                            semantic_hash_bucket,
                            graveyard_hash_bucket,
                            survivor_hash_bucket,
                        ]
                    )
                    seeds.append(seed_idx)
                    records.append(record)
    x = torch.tensor(rows, dtype=torch.float32)
    y = torch.tensor(labels, dtype=torch.long)
    seed_arr = torch.tensor(seeds, dtype=torch.long)
    train = seed_arr < 6
    mean = torch.mean(x[train], dim=0, keepdim=True)
    std = torch.std(x[train], dim=0, keepdim=True, unbiased=False)
    std = torch.where(std < 1e-6, torch.ones_like(std), std)
    return ((x - mean) / std).to(torch.float32), y, seed_arr, names, records


class PolicyNet(nn.Module):
    def __init__(self, feature_dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(feature_dim, 32), nn.ReLU(), nn.Linear(32, len(OPERATORS)))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def train_model(x: torch.Tensor, y: torch.Tensor, seeds: torch.Tensor, *, shuffle_labels: bool = False) -> tuple[PolicyNet, dict[str, Any]]:
    train = seeds < 6
    test = ~train
    x_train = x[train].to(torch.float32)
    y_train = y[train].clone()
    if shuffle_labels:
        rng = torch.Generator().manual_seed(8128)
        y_train = y_train[torch.randperm(len(y_train), generator=rng)]
    x_test = x[test].to(torch.float32)
    y_test = y[test].to(torch.long)
    torch.manual_seed(8128 if shuffle_labels else 2)
    model = PolicyNet(int(x.shape[1]))
    opt = optim.Adam(model.parameters(), lr=0.02, weight_decay=1e-4)
    loss_fn = nn.CrossEntropyLoss()
    for _ in range(360):
        opt.zero_grad()
        loss = loss_fn(model(x_train), y_train)
        loss.backward()
        opt.step()
    with torch.no_grad():
        train_acc = float((model(x_train).argmax(dim=1) == y_train).float().mean().item())
        test_acc = float((model(x_test).argmax(dim=1) == y_test).float().mean().item())
    return model, {
        "train_accuracy": train_acc,
        "test_accuracy": test_acc,
        "shuffle_labels": shuffle_labels,
        "train_rows": int(train.sum().item()),
        "test_rows": int(test.sum().item()),
    }


def lirpa_bruteforce_report(model: PolicyNet, x: torch.Tensor, seeds: torch.Tensor, names: list[str]) -> dict[str, Any]:
    test_rows = torch.where(seeds >= 6)[0]
    sample = x[test_rows].to(torch.float32)
    eps = 0.005
    bounded = BoundedModule(model, sample)
    bx = BoundedTensor(sample, PerturbationLpNorm(norm=float("inf"), eps=eps))
    nominal = bounded(bx)
    lb, ub = bounded.compute_bounds(x=(bx,), method="IBP")
    row_widths = torch.mean(ub - lb, dim=1)
    top2 = torch.topk(nominal, k=2, dim=1).values
    nominal_margins = top2[:, 0] - top2[:, 1]
    policy_bound_gates = torch.sigmoid(nominal_margins / (row_widths + 1e-6))
    rng = torch.Generator().manual_seed(144)
    contains = True
    min_lower_slack = float("inf")
    min_upper_slack = float("inf")
    for _ in range(96):
        delta = (torch.rand(sample.shape, generator=rng) * 2.0 - 1.0) * eps
        out = model(sample + delta)
        min_lower_slack = min(min_lower_slack, float((out - lb).min().detach().item()))
        min_upper_slack = min(min_upper_slack, float((ub - out).min().detach().item()))
        contains = contains and bool(torch.all(out >= lb - 1e-5) and torch.all(out <= ub + 1e-5))
    context_zero = sample.clone()
    for field in [
        "axis0_fep_gradient_polarity",
        "axis0_correlation_diversity_derivative",
        "axis0_retrocausal_many_futures_policy_scoring",
        "holodeck_memory_phase",
    ]:
        if field in names:
            context_zero[:, names.index(field)] = 0.0
    with torch.no_grad():
        context_shift = float(torch.mean(torch.abs(model(sample) - model(context_zero))).item())
    hash_zero = sample.clone()
    for field in HASH_FEATURE_NAMES:
        if field in names:
            hash_zero[:, names.index(field)] = 0.0
    bounded_hash_zero = BoundedModule(model, hash_zero)
    hash_zero_bx = BoundedTensor(hash_zero, PerturbationLpNorm(norm=float("inf"), eps=eps))
    hash_zero_lb, hash_zero_ub = bounded_hash_zero.compute_bounds(x=(hash_zero_bx,), method="IBP")
    hash_zero_shift = torch.mean(torch.abs((ub + lb) / 2 - (hash_zero_ub + hash_zero_lb) / 2)).item()

    hash_shuffle = sample.clone()
    for field in HASH_FEATURE_NAMES:
        if field in names:
            col = names.index(field)
            hash_shuffle[:, col] = torch.roll(hash_shuffle[:, col], shifts=7)
    bounded_hash_shuffle = BoundedModule(model, hash_shuffle)
    hash_shuffle_bx = BoundedTensor(hash_shuffle, PerturbationLpNorm(norm=float("inf"), eps=eps))
    hash_shuffle_lb, hash_shuffle_ub = bounded_hash_shuffle.compute_bounds(x=(hash_shuffle_bx,), method="IBP")
    hash_shuffle_shift = torch.mean(torch.abs((ub + lb) / 2 - (hash_shuffle_ub + hash_shuffle_lb) / 2)).item()

    drop_graveyard = sample.clone()
    if "holodeck_graveyard_hash_bucket" in names:
        drop_graveyard[:, names.index("holodeck_graveyard_hash_bucket")] = 0.0
    bounded_drop_graveyard = BoundedModule(model, drop_graveyard)
    drop_graveyard_bx = BoundedTensor(drop_graveyard, PerturbationLpNorm(norm=float("inf"), eps=eps))
    drop_graveyard_lb, drop_graveyard_ub = bounded_drop_graveyard.compute_bounds(x=(drop_graveyard_bx,), method="IBP")
    drop_graveyard_shift = torch.mean(torch.abs((ub + lb) / 2 - (drop_graveyard_ub + drop_graveyard_lb) / 2)).item()

    hash_identity_pass = (
        all(field in names for field in HASH_FEATURE_NAMES)
        and hash_zero_shift > HASH_CONTROL_THRESHOLDS["zero_hash_table_interval_center_shift_min"]
        and hash_shuffle_shift > HASH_CONTROL_THRESHOLDS["shuffle_hash_identity_interval_center_shift_min"]
        and drop_graveyard_shift > HASH_CONTROL_THRESHOLDS["drop_graveyard_hash_interval_center_shift_min"]
    )
    return {
        "pass": bool(
            torch.all(lb <= nominal)
            and torch.all(nominal <= ub)
            and contains
            and float((ub - lb).mean().detach().item()) > 0.0
            and context_shift > 0.25
            and hash_identity_pass
        ),
        "test_rows_bounded": int(sample.shape[0]),
        "eps_linf": eps,
        "interval_mean_width": float((ub - lb).mean().detach().item()),
        "row_interval_widths": [float(x) for x in row_widths.detach().tolist()],
        "row_nominal_margins": [float(x) for x in nominal_margins.detach().tolist()],
        "policy_bound_gate_vector": [float(x) for x in policy_bound_gates.detach().tolist()],
        "nominal_contained": bool(torch.all(lb <= nominal) and torch.all(nominal <= ub)),
        "bruteforce_samples_per_row": 96,
        "bruteforce_samples_contained": bool(contains),
        "min_lower_slack": min_lower_slack,
        "min_upper_slack": min_upper_slack,
        "context_zero_logit_mean_abs_shift": context_shift,
        "hash_identity_bound_controls": {
            "pass": bool(hash_identity_pass),
            "hash_feature_names": HASH_FEATURE_NAMES,
            "thresholds": HASH_CONTROL_THRESHOLDS,
            "zero_hash_table_interval_center_shift": float(hash_zero_shift),
            "shuffle_hash_identity_interval_center_shift": float(hash_shuffle_shift),
            "drop_graveyard_hash_interval_center_shift": float(drop_graveyard_shift),
        },
    }


def z3_training_witness(train: dict[str, Any], bound: dict[str, Any], shuffled: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    learned = z3.Bool("learned")
    bounded = z3.Bool("bounded")
    shuffled_fails = z3.Bool("shuffled_fails")
    solver.add(learned == (train["test_accuracy"] >= 0.70))
    solver.add(bounded == bool(bound["pass"]))
    solver.add(shuffled_fails == (shuffled["test_accuracy"] <= 0.45))
    solver.add(z3.Not(z3.And(learned, bounded, shuffled_fails)))
    status = solver.check()
    return {
        "pass": status == z3.unsat,
        "solver_status": str(status),
        "claim_ceiling": "Finite witness over trained-accuracy, LiRPA-containment, and shuffled-label-control predicates only.",
    }


def main() -> int:
    started = time.time()
    repo_receipt = load_result("world_model_repo_admission_gap_adapter_probe_results.json")
    fixed_lirpa_receipt = load_result("auto_lirpa_stage_policy_bound_consumption_probe_results.json")
    stage_receipt = load_result("macro_sim_stage_record_science_method_contract_probe_results.json")
    axis0_receipt = load_result("macro_sim_axis0_plural_stage_candidate_router_probe_results.json")
    axis0_guard_receipt = load_result(axis0_guard.AXIS0_GUARD_RESULT_NAME)
    memory_receipt = load_result("source_native_holodeck_hash_memory_placeholder_probe_results.json")

    guard = axis0_guard.axis0_guard_signal(axis0_guard_receipt)
    axis0 = axis0_guard.guarded_router_vectors(axis0_receipt, guard)
    memory = memory_margin(memory_receipt)
    hash_cells = holodeck_hash_cells(memory_receipt)
    x, y, seeds, names, records = collect_training_rows(axis0, memory, hash_cells)
    model, train_report = train_model(x, y, seeds, shuffle_labels=False)
    shuffled_model, shuffled_report = train_model(x, y, seeds, shuffle_labels=True)
    bound_report = lirpa_bruteforce_report(model, x, seeds, names)
    z3_witness = z3_training_witness(train_report, bound_report, shuffled_report)
    auto_row = ((repo_receipt.get("repo_admission_matrix") or {}).get("rows") or {}).get("auto_LiRPA", {})

    repair_receipt = {
        "weak_link": "The auto_LiRPA downstream consumer used fixed weights; it did not prove a trained source-native policy adapter could be bounded or checked against sampled perturbations.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": "A trained stage-policy adapter must show held-out accuracy, LiRPA interval containment, brute-force perturbation containment, and shuffled-label control before stronger neural-policy claims.",
        "dependency_subset": [
            "world_model_repo_admission_gap_adapter receipt",
            "auto_lirpa_stage_policy_bound_consumption receipt",
            "macro_sim_stage_record_science_method_contract receipt",
            "macro_sim_axis0_plural_stage_candidate_router receipt",
            "axis0_plural_candidate_multicarrier_drive_controls receipt",
            "source_native_holodeck_hash_memory_placeholder receipt",
            "local auto_LiRPA BoundedModule",
        ],
        "stage_fields_touched_or_consumed": REQUIRED_STAGE_FIELDS,
        "before_baseline/hash": {
            "fixed_lirpa_result": fixed_lirpa_receipt.get("path"),
            "auto_lirpa_decision": auto_row.get("decision"),
        },
        "after_delta/hash": {
            "script_sha256": sha256_file(pathlib.Path(__file__)),
            "result_path": str(OUT_PATH),
        },
        "primary_control/result": {
            "trained_adapter": train_report,
            "lirpa_bruteforce_bounds": bound_report,
            "shuffled_label_control": shuffled_report,
            "hash_identity_bound_controls": bound_report["hash_identity_bound_controls"],
        },
        "axis0_outputs_or_blockers": {
            "raw_router_candidate_names": axis0_guard.AXIS0_CANDIDATE_NAMES,
            "admitted_candidate_names": guard["admitted_candidate_names"],
            "blocked_candidate_names": guard["blocked_candidate_names"],
            "adapter_active_axis0_feature_names": guard["adapter_active_axis0_feature_names"],
            "blocked_axis0_feature_names_excluded": guard["blocked_axis0_feature_names_excluded"],
            "axis0_vectors_nonempty": all(len(v) > 0 for v in axis0.values()),
            "blocked_axis0_candidates_not_feature_columns": all(
                f"axis0_{name}" not in names for name in guard["blocked_candidate_names"]
            ),
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
        "next_step": "Use this trained bounded adapter as a verifier subroutine in a carrier bridge: policy-bound widths should modulate or gate MPS/PEPS/PEPS3D local updates under matched controls.",
    }

    positive = {
        "admitted_auto_lirpa_and_fixed_lirpa_receipts_are_consumed": {
            "pass": repo_receipt.get("all_pass") is True
            and fixed_lirpa_receipt.get("all_pass") is True
            and auto_row.get("admitted") is True,
            "auto_lirpa_row": auto_row,
            "fixed_lirpa_receipt": fixed_lirpa_receipt,
        },
        "axis0_guard_receipt_blocks_unadmitted_candidates_before_trained_lirpa_adapter": {
            "pass": bool(
                guard["pass"]
                and axis0_guard_receipt.get("all_pass") is True
                and all(f"axis0_{name}" not in names for name in guard["blocked_candidate_names"])
                and all(f"axis0_{name}" in names for name in guard["admitted_candidate_names"])
            ),
            "axis0_guard": guard,
            "feature_names": names,
        },
        "trained_context_conditioned_stage_policy_adapter_learns": {
            "pass": train_report["test_accuracy"] >= 0.70 and train_report["train_accuracy"] >= 0.95,
            "target": "context_conditioned_next_operator_class",
            "class_counts": torch.bincount(y, minlength=len(OPERATORS)).tolist(),
            **train_report,
        },
        "auto_lirpa_bounds_contain_bruteforce_perturbation_samples": bound_report,
        "holodeck_hash_cells_are_consumed_as_trained_policy_identity_features": {
            "pass": bool(
                hash_cells
                and all(name in names for name in HASH_FEATURE_NAMES)
                and bound_report["hash_identity_bound_controls"]["pass"]
            ),
            "hash_cell_count": len(hash_cells),
            "hash_feature_names": HASH_FEATURE_NAMES,
            "hash_identity_bound_controls": bound_report["hash_identity_bound_controls"],
        },
        "z3_training_and_bound_witness_executes": z3_witness,
    }
    graveyards = {
        "shuffled_label_control_fails_to_generalize": {
            "pass": shuffled_report["test_accuracy"] <= 0.45,
            **shuffled_report,
        },
        "context_zero_control_changes_trained_logits": {
            "pass": bound_report["context_zero_logit_mean_abs_shift"] > 0.25,
            "context_zero_logit_mean_abs_shift": bound_report["context_zero_logit_mean_abs_shift"],
        },
        "hash_identity_zero_shuffle_drop_controls_change_trained_bounds": {
            "pass": bound_report["hash_identity_bound_controls"]["pass"],
            **bound_report["hash_identity_bound_controls"],
        },
        "blocked_axis0_candidates_not_used_as_trained_lirpa_feature_columns": {
            "pass": all(f"axis0_{name}" not in names for name in guard["blocked_candidate_names"]),
            "blocked_candidate_names": guard["blocked_candidate_names"],
            "feature_names": names,
        },
        "nominal_training_accuracy_is_not_a_certificate": {
            "pass": bound_report["interval_mean_width"] > 0.0 and bound_report["bruteforce_samples_contained"],
            "interval_mean_width": bound_report["interval_mean_width"],
            "bruteforce_samples_contained": bound_report["bruteforce_samples_contained"],
        },
    }
    boundary = {
        "claim_ceiling_blocks_production_policy_or_world_model": {
            "pass": all(term in CLAIM_CEILING.lower() for term in ["formal scout", "does not admit", "production policy", "neural world model"]),
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
        "source_stage_contract_receipts_remain_consumed_not_replaced": {
            "pass": stage_receipt.get("all_pass") is True
            and axis0_receipt.get("all_pass") is True
            and axis0_guard_receipt.get("all_pass") is True
            and memory_receipt.get("all_pass") is True
            and len(records) == 512,
            "record_count": len(records),
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
            "This is a v5 downstream consumption scout for the repaired auto_LiRPA verifier-adapter branch.",
            "It consumes source-native stage, Axis0, Holodeck memory, repo-admission, and fixed LiRPA receipts.",
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
