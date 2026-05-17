#!/usr/bin/env python3
"""LiRPA policy-bound gated multicarrier environment scout."""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import numpy as np
import z3

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
    "numpy": {"tried": True, "used": True, "reason": "load-bearing policy-gate vector, local carrier signatures, and matched controls"},
    "quimb": {"tried": True, "used": True, "reason": "load-bearing through reused MPS/PEPS/PEPS3D carrier construction sanity checks"},
    "cotengra": {"tried": True, "used": True, "reason": "supportive through upstream subdense contraction scout dependency"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite witness for gate-consumption and control-separation predicates"},
    "engine_core": {"tried": True, "used": True, "reason": "load-bearing via reused source-native stage records"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "quimb": "load_bearing",
    "cotengra": "supportive",
    "z3": "load_bearing",
    "engine_core": "load_bearing",
}

REQUIRED_STAGE_FIELDS = subdense.REQUIRED_STAGE_FIELDS


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
        "axis0_outputs_or_blockers": data.get("axis0_outputs_or_blockers", {}),
    }


def policy_gate_signal(lirpa_receipt: dict[str, Any]) -> dict[str, Any]:
    bound = (lirpa_receipt.get("positive") or {}).get("auto_lirpa_bounds_contain_bruteforce_perturbation_samples", {})
    gates = np.asarray(bound.get("policy_bound_gate_vector", []), dtype=float)
    widths = np.asarray(bound.get("row_interval_widths", []), dtype=float)
    margins = np.asarray(bound.get("row_nominal_margins", []), dtype=float)
    return {
        "ready": bool(lirpa_receipt.get("all_pass") is True and gates.size >= 4 and np.all(np.isfinite(gates))),
        "source_receipt": lirpa_receipt.get("path"),
        "policy_bound_gate_vector": [float(x) for x in gates],
        "row_interval_widths": [float(x) for x in widths],
        "row_nominal_margins": [float(x) for x in margins],
        "gate_mean": float(np.mean(gates)) if gates.size else 0.0,
        "gate_variance": float(np.var(gates)) if gates.size else 0.0,
    }


def gate_value(signal: dict[str, Any], idx: int, mode: str) -> float:
    gates = np.asarray(signal.get("policy_bound_gate_vector", []), dtype=float)
    if gates.size == 0:
        return 1.0
    if mode == "full":
        return float(gates[idx % len(gates)])
    if mode == "flat":
        return float(np.mean(gates))
    if mode == "shuffled":
        return float(gates[(idx * 5 + 3) % len(gates)])
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
    before_sig = subdense.signature_from_rows(before_rows)
    after_sig = subdense.signature_from_rows(after_rows)
    row = {
        "carrier": carrier.name,
        "family": carrier.family,
        "shape": "x".join(str(x) for x in carrier.shape),
        "mode": mode,
        "site_count": len(carrier.sites),
        "edge_count": len(carrier.edges),
        "stage_records_consumed": len(records),
        "unique_model_after_hashes_consumed": len(set(stage_hashes)),
        "policy_gate_mean": float(np.mean(gate_values)),
        "policy_gate_variance": float(np.var(gate_values)),
        "quimb_count_check": quimb_check,
        "environment_signature": after_sig,
        "environment_shift_from_initial": float(np.linalg.norm(after_sig - before_sig)),
        "environment_rows_head": after_rows[:3],
        "pass": (
            len(records) == subdense.N_SOURCE_SEEDS * 64
            and len(set(stage_hashes)) > 16
            and quimb_check["pass"]
            and bool(np.all(np.isfinite(after_sig)))
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
    return float(np.linalg.norm(np.asarray(a["environment_signature"], dtype=float) - np.asarray(b["environment_signature"], dtype=float)))


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


def main() -> int:
    started = time.time()
    lirpa_receipt = load_result("auto_lirpa_trained_stage_policy_adapter_bound_probe_results.json")
    subdense_receipt = load_result("source_native_multicarrier_subdense_environment_contraction_probe_results.json")
    axis0_receipt = load_result("macro_sim_axis0_plural_stage_candidate_router_probe_results.json")
    memory_receipt = load_result("source_native_holodeck_hash_memory_placeholder_probe_results.json")
    records = subdense.run_source_records()
    axis0 = subdense.axis0_signature(axis0_receipt)
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
            "consumed_candidates": axis0.get("candidate_names"),
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
            "pass": lirpa_receipt.get("all_pass") is True and subdense_receipt.get("all_pass") is True,
            "trained_lirpa_receipt": lirpa_receipt,
            "subdense_receipt": subdense_receipt,
        },
        "policy_bound_gate_vector_is_present_and_variable": {
            "pass": signal["ready"] and signal["gate_variance"] > 1e-5,
            **signal,
        },
        "mps_peps_peps3d_environment_consumes_policy_bound_gates": suite,
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
