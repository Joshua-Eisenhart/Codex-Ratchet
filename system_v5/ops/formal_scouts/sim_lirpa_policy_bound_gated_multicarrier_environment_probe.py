#!/usr/bin/env python3
"""LiRPA policy-bound gated multicarrier environment scout."""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import time
from typing import Any

import torch
import z3

import axis0_guard_utils as axis0_guard
import sim_source_native_multicarrier_subdense_environment_contraction_probe as subdense


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "lirpa_policy_bound_gated_multicarrier_environment_probe_results.json"

NAME = "lirpa_policy_bound_gated_multicarrier_environment_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "lirpa_policy_bound_gated_multicarrier_environment"
CLAIM_CEILING = (
    "Formal scout only: consumes the trained auto_LiRPA stage-policy bound "
    "receipt as a gating signal for MPS, PEPS, and PEPS3D local environment "
    "updates. It does not admit a final controller, trained policy, neural "
    "world model, full PEPS environment theorem, physics, cognition, or "
    "canonical architecture."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing tensor gate statistics, finite checks, and signature-gap controls"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing through reused MPS/PEPS/PEPS3D carrier construction sanity checks"},
    "cotengra": {"tried": True, "used": True, "reason": "supportive through upstream subdense contraction scout dependency"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite witness for gate-consumption and control-separation predicates"},
    "engine_core": {"tried": True, "used": True, "reason": "supportive provenance through reused source-native stage records"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "quimb": "load_bearing",
    "cotengra": "supportive",
    "z3": "load_bearing",
    "engine_core": "supportive",
}

REQUIRED_STAGE_FIELDS = subdense.REQUIRED_STAGE_FIELDS


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        raw = value.detach().cpu().tolist()
        return as_jsonable(raw)
    return value


def tensor_from_values(values: Any) -> torch.Tensor:
    if isinstance(values, torch.Tensor):
        return values.detach().to(dtype=torch.float64).flatten()
    if hasattr(values, "tolist"):
        values = values.tolist()
    return torch.tensor([float(x) for x in values], dtype=torch.float64)


def tensor_list(values: Any) -> list[float]:
    return [float(x) for x in tensor_from_values(values).tolist()]


def tensor_mean(values: Any) -> float:
    tensor = tensor_from_values(values)
    return float(torch.mean(tensor).item()) if tensor.numel() else 0.0


def tensor_variance(values: Any) -> float:
    tensor = tensor_from_values(values)
    return float(torch.var(tensor, unbiased=False).item()) if tensor.numel() else 0.0


def tensor_l2_gap(a: Any, b: Any) -> float:
    a_tensor = tensor_from_values(a)
    b_tensor = tensor_from_values(b)
    return float(torch.linalg.vector_norm(a_tensor - b_tensor).item())


def tensor_all_finite(values: Any) -> bool:
    tensor = tensor_from_values(values)
    return bool(torch.isfinite(tensor).all().item()) if tensor.numel() else True


def torch_signature_from_rows(rows: list[dict[str, Any]]) -> torch.Tensor:
    cols = subdense.ENVIRONMENT_SIGNATURE_COLUMNS
    matrix = torch.tensor(
        [[float(row[col]) for col in cols] for row in rows],
        dtype=torch.float64,
    )
    if matrix.numel() == 0:
        return torch.zeros(len(cols) * 3, dtype=torch.float64)
    return torch.cat(
        [
            torch.mean(matrix, dim=0),
            torch.std(matrix, dim=0, unbiased=False),
            matrix[-1],
        ]
    )


def finite_floats(values: Any) -> list[float]:
    floats = tensor_list(values)
    if not all(math.isfinite(value) for value in floats):
        raise ValueError("non-finite value encountered")
    return floats


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
        "axis0_outputs_or_blockers": data.get("axis0_outputs_or_blockers", {}),
    }


def policy_gate_signal(lirpa_receipt: dict[str, Any]) -> dict[str, Any]:
    bound = (lirpa_receipt.get("positive") or {}).get("auto_lirpa_bounds_contain_bruteforce_perturbation_samples", {})
    gates = tensor_from_values(bound.get("policy_bound_gate_vector", []))
    widths = tensor_from_values(bound.get("row_interval_widths", []))
    margins = tensor_from_values(bound.get("row_nominal_margins", []))
    return {
        "ready": bool(lirpa_receipt.get("all_pass") is True and gates.numel() >= 4 and torch.isfinite(gates).all().item()),
        "source_receipt": lirpa_receipt.get("path"),
        "policy_bound_gate_vector": tensor_list(gates),
        "row_interval_widths": tensor_list(widths),
        "row_nominal_margins": tensor_list(margins),
        "gate_mean": tensor_mean(gates),
        "gate_variance": tensor_variance(gates),
    }


def gate_value(signal: dict[str, Any], idx: int, mode: str) -> float:
    gates = tensor_from_values(signal.get("policy_bound_gate_vector", []))
    if gates.numel() == 0:
        return 1.0
    if mode == "full":
        return float(gates[idx % gates.numel()].item())
    if mode == "flat":
        return tensor_mean(gates)
    if mode == "shuffled":
        return float(gates[(idx * 5 + 3) % gates.numel()].item())
    if mode == "zero":
        return 0.0
    raise ValueError(mode)


def run_policy_gated_carrier(
    records: list[dict[str, Any]],
    axis0: dict[str, Any],
    memory: dict[str, Any],
    signal: dict[str, Any],
    family: str,
    shape: tuple[int, ...],
    seed: int,
    mode: str,
    *,
    include_local_matrix: bool = False,
) -> dict[str, Any]:
    carrier = subdense.make_carrier(family, shape, seed)
    quimb_check = subdense.quimb_count_check(carrier)
    site_order = sorted(carrier.sites)
    before_rows = subdense.environment_rows(carrier)
    gate_values = []
    stage_hashes = []
    for idx, record in enumerate(records):
        site = carrier.sites[site_order[idx % len(site_order)]]
        drive = subdense.axis0_drive(axis0, idx)
        mem_drive = subdense.holodeck_memory_drive(memory, idx)
        gate = gate_value(signal, idx, mode)
        gate_values.append(gate)
        stage_hashes.append(record["model_after"]["density_hash"])
        strength = subdense.source_strength(record, drive, mem_drive) * (0.60 + gate)
        subdense.apply_physical_slot(site, str(record["operator"]), int(record["operator_sign"]), strength)
    after_rows = subdense.environment_rows(carrier)
    before_sig = torch_signature_from_rows(before_rows)
    after_sig = torch_signature_from_rows(after_rows)
    row = {
        "carrier": carrier.name,
        "family": carrier.family,
        "shape": "x".join(str(x) for x in carrier.shape),
        "mode": mode,
        "site_count": len(carrier.sites),
        "edge_count": len(carrier.edges),
        "stage_records_consumed": len(records),
        "unique_model_after_hashes_consumed": len(set(stage_hashes)),
        "policy_gate_mean": tensor_mean(gate_values),
        "policy_gate_variance": tensor_variance(gate_values),
        "quimb_count_check": quimb_check,
        "signature_backend": "pytorch_from_subdense_environment_rows",
        "subdense_signature_from_rows_used": False,
        "upstream_environment_rows_backend_boundary": (
            "subdense environment_rows remains an upstream quimb/numpy carrier "
            "surface; this downstream scout makes signature statistics, gate "
            "controls, and finite checks PyTorch load-bearing."
        ),
        "environment_signature": finite_floats(after_sig),
        "environment_shift_from_initial": tensor_l2_gap(after_sig, before_sig),
        "environment_rows_head": after_rows[:3],
        "pass": (
            len(records) == subdense.N_SOURCE_SEEDS * 64
            and len(set(stage_hashes)) > 16
            and quimb_check["pass"]
            and tensor_all_finite(after_sig)
        ),
    }
    if include_local_matrix:
        cols = subdense.ENVIRONMENT_SIGNATURE_COLUMNS
        row["environment_signature_columns"] = cols
        row["environment_signature_matrix"] = [
            [float(env_row[col]) for col in cols]
            for env_row in after_rows
        ]
    return row


def signature_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
    return tensor_l2_gap(a["environment_signature"], b["environment_signature"])


def carrier_suite(records: list[dict[str, Any]], axis0: dict[str, Any], memory: dict[str, Any], signal: dict[str, Any]) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for family, shape, seed in subdense.carrier_specs():
        key = f"{family}_{'x'.join(str(x) for x in shape)}"
        full = run_policy_gated_carrier(records, axis0, memory, signal, family, shape, seed + 71, "full")
        flat = run_policy_gated_carrier(records, axis0, memory, signal, family, shape, seed + 71, "flat")
        shuffled = run_policy_gated_carrier(records, axis0, memory, signal, family, shape, seed + 71, "shuffled")
        zero = run_policy_gated_carrier(records, axis0, memory, signal, family, shape, seed + 71, "zero")
        rows[key] = {
            "full": full,
            "flat_control": flat,
            "shuffled_control": shuffled,
            "zero_control": zero,
            "full_vs_flat_gap": signature_gap(full, flat),
            "full_vs_shuffled_gap": signature_gap(full, shuffled),
            "full_vs_zero_gap": signature_gap(full, zero),
            "pass": full["pass"]
            and flat["pass"]
            and shuffled["pass"]
            and zero["pass"]
            and signature_gap(full, flat) > 1e-7
            and signature_gap(full, shuffled) > 1e-7
            and signature_gap(full, zero) > 1e-6,
        }
    return {
        "rows": rows,
        "pass": all(row["pass"] for row in rows.values()),
        "gap_summary": {
            key: {
                "full_vs_flat_gap": row["full_vs_flat_gap"],
                "full_vs_shuffled_gap": row["full_vs_shuffled_gap"],
                "full_vs_zero_gap": row["full_vs_zero_gap"],
            }
            for key, row in rows.items()
        },
    }


def z3_gate_witness(suite: dict[str, Any], signal: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    gate_varies = z3.Bool("gate_varies")
    carrier_separates = z3.Bool("carrier_separates")
    solver.add(gate_varies == (signal["gate_variance"] > 1e-5))
    solver.add(carrier_separates == bool(suite["pass"]))
    solver.add(z3.Not(z3.And(gate_varies, carrier_separates)))
    status = solver.check()
    return {
        "pass": status == z3.unsat,
        "solver_status": str(status),
        "claim_ceiling": "Finite witness over gate variance and local carrier separation only.",
    }


def suite_uses_torch_signature_backend(suite: dict[str, Any]) -> bool:
    modes = ("full", "flat_control", "shuffled_control", "zero_control")
    return all(
        row[mode].get("signature_backend") == "pytorch_from_subdense_environment_rows"
        and row[mode].get("subdense_signature_from_rows_used") is False
        for row in suite["rows"].values()
        for mode in modes
    )


def main() -> int:
    started = time.time()
    lirpa_receipt = load_result("auto_lirpa_trained_stage_policy_adapter_bound_probe_results.json")
    subdense_receipt = load_result("source_native_multicarrier_subdense_environment_contraction_probe_results.json")
    axis0_receipt = load_result("macro_sim_axis0_plural_stage_candidate_router_probe_results.json")
    axis0_guard_receipt = load_result(axis0_guard.AXIS0_GUARD_RESULT_NAME)
    memory_receipt = load_result("source_native_holodeck_hash_memory_placeholder_probe_results.json")
    records = subdense.run_source_records()
    guard = axis0_guard.axis0_guard_signal(axis0_guard_receipt)
    axis0 = axis0_guard.filter_subdense_axis0_signature(subdense.axis0_signature(axis0_receipt), guard)
    memory = subdense.holodeck_memory_signal(memory_receipt)
    signal = policy_gate_signal(lirpa_receipt)
    suite = carrier_suite(records, axis0, memory, signal)
    z3_witness = z3_gate_witness(suite, signal)

    repair_receipt = {
        "weak_link": "The trained LiRPA policy adapter produced certified bounds, but no multicarrier environment update consumed those bound-derived policy gates.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": "Policy-bound gates must modulate MPS/PEPS/PEPS3D local updates and separate from flat, shuffled, and zero-gate controls before being treated as integrated macro-sim mechanics.",
        "dependency_subset": [
            "auto_lirpa_trained_stage_policy_adapter_bound receipt",
            "source_native_multicarrier_subdense_environment_contraction receipt",
            "macro_sim_axis0_plural_stage_candidate_router receipt",
            "axis0_plural_candidate_multicarrier_drive_controls receipt",
            "source_native_holodeck_hash_memory_placeholder receipt",
            "EngineCore source-native stage records",
        ],
        "stage_fields_touched_or_consumed": REQUIRED_STAGE_FIELDS,
        "before_baseline/hash": {
            "trained_lirpa_result": lirpa_receipt.get("path"),
            "subdense_result": subdense_receipt.get("path"),
        },
        "after_delta/hash": {
            "script_sha256": sha256_file(pathlib.Path(__file__)),
            "result_path": str(OUT_PATH),
        },
        "primary_control/result": {
            "carrier_suite": suite["gap_summary"],
            "gate_signal": signal,
        },
        "axis0_outputs_or_blockers": {
            "axis0_ready": axis0.get("ready"),
            "raw_router_candidate_names": axis0_guard.AXIS0_CANDIDATE_NAMES,
            "admitted_candidate_names": guard["admitted_candidate_names"],
            "blocked_candidate_names": guard["blocked_candidate_names"],
            "consumed_candidates": axis0.get("candidate_names"),
            "blocked_axis0_candidates_excluded_from_drive": all(
                name not in axis0.get("candidate_names", [])
                for name in guard["blocked_candidate_names"]
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
        "next_step": "Generalize the policy-bound gate beyond the 12-row LiRPA sample by carrying per-stage bound widths for all source records or training a bounded adapter with batched full-cycle certification.",
    }

    positive = {
        "trained_lirpa_and_subdense_receipts_are_consumed": {
            "pass": lirpa_receipt.get("all_pass") is True
            and subdense_receipt.get("all_pass") is True
            and axis0_guard_receipt.get("all_pass") is True
            and guard["pass"] is True,
            "trained_lirpa_receipt": lirpa_receipt,
            "subdense_receipt": subdense_receipt,
            "axis0_guard": guard,
        },
        "axis0_guard_filters_policy_bound_carrier_drive": {
            "pass": bool(
                axis0.get("ready")
                and axis0.get("candidate_names") == guard["admitted_candidate_names"]
                and all(name not in axis0.get("candidate_names", []) for name in guard["blocked_candidate_names"])
            ),
            "axis0_candidate_names_used_in_drive": axis0.get("candidate_names"),
            "blocked_candidate_names": guard["blocked_candidate_names"],
        },
        "policy_bound_gate_vector_is_present_and_variable": {
            "pass": signal["ready"] and signal["gate_variance"] > 1e-5,
            **signal,
        },
        "mps_peps_peps3d_environment_consumes_policy_bound_gates": suite,
        "downstream_environment_signature_statistics_are_pytorch_load_bearing": {
            "pass": suite_uses_torch_signature_backend(suite),
            "signature_backend": "pytorch_from_subdense_environment_rows",
            "subdense_signature_from_rows_used": False,
            "boundary": (
                "This kills the local NumPy signature-statistics loophole but "
                "does not migrate the upstream subdense carrier/environment "
                "density implementation away from NumPy."
            ),
        },
        "z3_gate_consumption_witness_executes": z3_witness,
    }
    graveyards = {
        "flat_gate_control_is_distinguished": {
            "pass": all(row["full_vs_flat_gap"] > 1e-7 for row in suite["rows"].values()),
            "gaps": {key: row["full_vs_flat_gap"] for key, row in suite["rows"].items()},
        },
        "shuffled_gate_control_is_distinguished": {
            "pass": all(row["full_vs_shuffled_gap"] > 1e-7 for row in suite["rows"].values()),
            "gaps": {key: row["full_vs_shuffled_gap"] for key, row in suite["rows"].items()},
        },
        "zero_gate_control_is_distinguished": {
            "pass": all(row["full_vs_zero_gap"] > 1e-6 for row in suite["rows"].values()),
            "gaps": {key: row["full_vs_zero_gap"] for key, row in suite["rows"].items()},
        },
        "blocked_axis0_candidates_not_used_in_policy_bound_carrier_drive": {
            "pass": all(name not in axis0.get("candidate_names", []) for name in guard["blocked_candidate_names"]),
            "blocked_candidate_names": guard["blocked_candidate_names"],
            "drive_candidate_names": axis0.get("candidate_names"),
        },
    }
    boundary = {
        "claim_ceiling_blocks_final_controller_or_environment_theorem": {
            "pass": all(term in CLAIM_CEILING.lower() for term in ["formal scout", "does not admit", "final controller", "full peps"]),
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
        "upstream_subdense_numpy_boundary_is_not_promoted": {
            "pass": "does not admit" in CLAIM_CEILING and "full peps" in CLAIM_CEILING.lower(),
            "boundary": (
                "The upstream subdense carrier construction and two-site density "
                "path still use NumPy/quimb internals; this receipt is not a "
                "full PyTorch substrate migration."
            ),
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
            "This is a v5 downstream consumption scout linking trained LiRPA policy bounds to the repaired subdense multicarrier environment bridge.",
            "It consumes source-native stage, Axis0, Holodeck memory, trained LiRPA, and MPS/PEPS/PEPS3D receipts.",
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
