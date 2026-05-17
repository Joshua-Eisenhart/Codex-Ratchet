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

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import z3

AUTO_LIRPA_ROOT = pathlib.Path("/Users/joshuaeisenhart/GitHub/auto_LiRPA")
sys.path.insert(0, str(AUTO_LIRPA_ROOT))
from auto_LiRPA import BoundedModule, BoundedTensor, PerturbationLpNorm  # noqa: E402

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
    "numpy": {"tried": True, "used": True, "reason": "load-bearing feature assembly, split, normalization, and summary metrics"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite witness for trained accuracy plus bound containment predicates"},
    "engine_core": {"tried": True, "used": True, "reason": "load-bearing source-native stage records and policy fields"},
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
OPERATORS = ["Ti", "Te", "Fi", "Fe"]
PERCEPTIONS = ["Se", "Ne", "Ni", "Si"]


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
        "claim_ceiling": data.get("claim_ceiling", "")[:240],
        "positive": data.get("positive", {}),
        "repo_admission_matrix": data.get("repo_admission_matrix", {}),
        "axis0_outputs_or_blockers": data.get("axis0_outputs_or_blockers", {}),
    }


def axis0_vectors(router: dict[str, Any]) -> dict[str, np.ndarray]:
    outputs = router.get("axis0_outputs_or_blockers") or {}
    vectors = {}
    for name in ["fep_gradient_polarity", "path_entropy", "correlation_diversity_derivative"]:
        arr = np.asarray(outputs.get(name, {}).get("values", []), dtype=float)
        arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
        scale = float(np.max(np.abs(arr))) if arr.size else 0.0
        if scale > 0.0:
            arr = arr / scale
        vectors[name] = arr
    return vectors


def memory_margin(memory_receipt: dict[str, Any]) -> float:
    recall = ((memory_receipt.get("positive") or {}).get("predictive_model_verifies_contextual_recall") or {})
    return float(recall.get("mean_target_verification_score", 0.0)) - float(
        recall.get("mean_wrong_model_target_score", 0.0)
    )


def collect_training_rows(axis0: dict[str, np.ndarray], memory: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str], list[dict[str, Any]]]:
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
        "axis0_fep_gradient_polarity",
        "axis0_path_entropy",
        "axis0_correlation_diversity_derivative",
        "holodeck_memory_phase",
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
                    pred = np.asarray(record["prediction"]["observation_distribution"], dtype=float)
                    obs = np.asarray(record["observation"]["observation_distribution"], dtype=float)
                    axis_values = [
                        float(axis0[name][idx % len(axis0[name])]) if len(axis0[name]) else 0.0
                        for name in ["fep_gradient_polarity", "path_entropy", "correlation_diversity_derivative"]
                    ]
                    memory_phase = float(memory * (1.0 if idx % 2 == 0 else -0.5))
                    context_score = float(sum(axis_values) + 0.15 * memory_phase + 0.10 * fep["prediction_error_l2"])
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
                            *[float(x) for x in (pred - obs)[:3]],
                            *[1.0 if record["operator"] == op else 0.0 for op in OPERATORS],
                            *[1.0 if perception == item else 0.0 for item in PERCEPTIONS],
                            *axis_values,
                            memory_phase,
                        ]
                    )
                    seeds.append(seed_idx)
                    records.append(record)
    x = np.asarray(rows, dtype=np.float32)
    y = np.asarray(labels, dtype=np.int64)
    seed_arr = np.asarray(seeds, dtype=np.int64)
    train = seed_arr < 6
    mean = x[train].mean(axis=0, keepdims=True)
    std = x[train].std(axis=0, keepdims=True)
    std[std < 1e-6] = 1.0
    return ((x - mean) / std).astype(np.float32), y, seed_arr, names, records


class PolicyNet(nn.Module):
    def __init__(self, feature_dim: int) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(feature_dim, 32), nn.ReLU(), nn.Linear(32, len(OPERATORS)))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def train_model(x: np.ndarray, y: np.ndarray, seeds: np.ndarray, *, shuffle_labels: bool = False) -> tuple[PolicyNet, dict[str, Any]]:
    train = seeds < 6
    test = ~train
    x_train = torch.tensor(x[train], dtype=torch.float32)
    y_train_np = y[train].copy()
    if shuffle_labels:
        rng = np.random.default_rng(8128)
        rng.shuffle(y_train_np)
    y_train = torch.tensor(y_train_np, dtype=torch.long)
    x_test = torch.tensor(x[test], dtype=torch.float32)
    y_test = torch.tensor(y[test], dtype=torch.long)
    torch.manual_seed(8128 if shuffle_labels else 2)
    model = PolicyNet(x.shape[1])
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
        "train_rows": int(train.sum()),
        "test_rows": int(test.sum()),
    }


def lirpa_bruteforce_report(model: PolicyNet, x: np.ndarray, seeds: np.ndarray, names: list[str]) -> dict[str, Any]:
    test_rows = np.where(seeds >= 6)[0]
    sample = torch.tensor(x[test_rows], dtype=torch.float32)
    eps = 0.005
    bounded = BoundedModule(model, sample)
    bx = BoundedTensor(sample, PerturbationLpNorm(norm=np.inf, eps=eps))
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
        "axis0_path_entropy",
        "axis0_correlation_diversity_derivative",
        "holodeck_memory_phase",
    ]:
        context_zero[:, names.index(field)] = 0.0
    with torch.no_grad():
        context_shift = float(torch.mean(torch.abs(model(sample) - model(context_zero))).item())
    return {
        "pass": bool(
            torch.all(lb <= nominal)
            and torch.all(nominal <= ub)
            and contains
            and float((ub - lb).mean().detach().item()) > 0.0
            and context_shift > 0.25
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
    memory_receipt = load_result("source_native_holodeck_hash_memory_placeholder_probe_results.json")

    axis0 = axis0_vectors(axis0_receipt)
    memory = memory_margin(memory_receipt)
    x, y, seeds, names, records = collect_training_rows(axis0, memory)
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
        },
        "axis0_outputs_or_blockers": {
            "consumed_candidates": sorted(axis0),
            "axis0_vectors_nonempty": all(len(v) > 0 for v in axis0.values()),
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
        "trained_context_conditioned_stage_policy_adapter_learns": {
            "pass": train_report["test_accuracy"] >= 0.70 and train_report["train_accuracy"] >= 0.95,
            "target": "context_conditioned_next_operator_class",
            "class_counts": np.bincount(y, minlength=len(OPERATORS)).tolist(),
            **train_report,
        },
        "auto_lirpa_bounds_contain_bruteforce_perturbation_samples": bound_report,
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
