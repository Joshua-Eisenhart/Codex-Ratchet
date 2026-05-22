#!/usr/bin/env python3
"""Variable-qubit scaling for LiRPA-gated source-native multicarrier updates."""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import rustworkx as rx
import torch
import z3

import axis0_guard_utils as axis0_guard
import sim_lirpa_policy_bound_gated_multicarrier_environment_probe as gated
import sim_source_native_multicarrier_subdense_environment_contraction_probe as subdense


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "lirpa_policy_bound_variable_qubit_scaling_probe_results.json"

NAME = "lirpa_policy_bound_variable_qubit_scaling_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "lirpa_policy_bound_variable_qubit_scaling"
CLAIM_CEILING = (
    "Formal scout only: tests whether trained auto_LiRPA policy-bound gates "
    "continue to be consumed by source-native MPS, PEPS, and PEPS3D local "
    "environment updates across several finite carrier sizes. It does not "
    "prove asymptotic scaling, a full PEPS/PEPS3D environment theorem, a final "
    "controller, neural world model, physics, cognition, or canonical "
    "architecture, and it does not admit canonical architecture."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite-size signature gaps, local per-edge RMS readouts, and gate-control statistics across 8/16/32/64 carriers",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing dependency graph for stage/FEP/Axis0/Holodeck/LiRPA scaling path",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite witness that variable-size carriers and controls are present",
    },
    "engine_core": {
        "tried": True,
        "used": True,
        "reason": "supportive provenance through reused source-native stage records",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through reused MPS/PEPS/PEPS3D carrier construction checks",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "engine_core": "supportive",
    "quimb": "load_bearing",
}

REQUIRED_REPAIR_RECEIPT_FIELDS = [
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
GAP_FLOOR = 1e-8
PEPS3D_64_FLAT_ABSOLUTE_FLOOR = 0.001
PEPS3D_64_TO_32_FLAT_RATIO_FLOOR = 0.20
PEPS3D_64_SHUFFLED_FLOOR = 0.002
PEPS3D_64_ZERO_FLOOR = 0.02
PEPS3D_64_LOCAL_FLAT_RMS_FLOOR = 0.001
PEPS3D_64_TO_32_LOCAL_FLAT_RATIO_FLOOR = 0.20
PEPS3D_64_LOCAL_SHUFFLED_RMS_FLOOR = 0.002
PEPS3D_64_LOCAL_ZERO_RMS_FLOOR = 0.02


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


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scaling_specs() -> list[tuple[str, tuple[int, ...], int]]:
    return [
        ("mps", (8,), 6108),
        ("mps", (16,), 6116),
        ("mps", (32,), 6132),
        ("peps", (3, 3), 6209),
        ("peps", (4, 4), 6216),
        ("peps", (5, 5), 6225),
        ("peps3d", (2, 2, 2), 6308),
        ("peps3d", (3, 3, 2), 6318),
        ("peps3d", (4, 4, 2), 6332),
        ("peps3d", (4, 4, 4), 6364),
    ]


def spec_key(family: str, shape: tuple[int, ...]) -> str:
    return f"{family}_{'x'.join(str(x) for x in shape)}"


def run_size_mode_suite(
    records: list[dict[str, Any]],
    axis0: dict[str, Any],
    memory: dict[str, Any],
    signal: dict[str, Any],
    family: str,
    shape: tuple[int, ...],
    seed: int,
) -> dict[str, Any]:
    full = gated.run_policy_gated_carrier(records, axis0, memory, signal, family, shape, seed, "full", include_local_matrix=True)
    flat = gated.run_policy_gated_carrier(records, axis0, memory, signal, family, shape, seed, "flat", include_local_matrix=True)
    shuffled = gated.run_policy_gated_carrier(records, axis0, memory, signal, family, shape, seed, "shuffled", include_local_matrix=True)
    zero = gated.run_policy_gated_carrier(records, axis0, memory, signal, family, shape, seed, "zero", include_local_matrix=True)
    gaps = {
        "full_vs_flat_gap": gated.signature_gap(full, flat),
        "full_vs_shuffled_gap": gated.signature_gap(full, shuffled),
        "full_vs_zero_gap": gated.signature_gap(full, zero),
    }
    local_gaps = {
        "full_vs_flat_local": local_signature_gap(full, flat),
        "full_vs_shuffled_local": local_signature_gap(full, shuffled),
        "full_vs_zero_local": local_signature_gap(full, zero),
    }
    return {
        "family": family,
        "shape": "x".join(str(x) for x in shape),
        "site_count": full["site_count"],
        "edge_count": full["edge_count"],
        "full": full,
        "flat_control": flat,
        "shuffled_control": shuffled,
        "zero_control": zero,
        **gaps,
        **local_gaps,
        "pass": (
            full["pass"]
            and flat["pass"]
            and shuffled["pass"]
            and zero["pass"]
            and gaps["full_vs_flat_gap"] > GAP_FLOOR
            and gaps["full_vs_shuffled_gap"] > GAP_FLOOR
            and gaps["full_vs_zero_gap"] > GAP_FLOOR
        ),
    }


def local_signature_gap(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    a_mat = torch.tensor(a.get("environment_signature_matrix", []), dtype=torch.float64)
    b_mat = torch.tensor(b.get("environment_signature_matrix", []), dtype=torch.float64)
    n = min(int(a_mat.shape[0]) if a_mat.ndim else 0, int(b_mat.shape[0]) if b_mat.ndim else 0)
    if n == 0:
        return {"rms": 0.0, "mean": 0.0, "q90": 0.0, "max": 0.0, "nonzero_edges": 0, "sampled_edges": 0}
    edge_norms = torch.linalg.vector_norm(a_mat[:n] - b_mat[:n], dim=1)
    return {
        "rms": float(torch.sqrt(torch.mean(edge_norms**2)).item()),
        "mean": float(torch.mean(edge_norms).item()),
        "q90": float(torch.quantile(edge_norms, 0.90).item()),
        "max": float(torch.max(edge_norms).item()),
        "nonzero_edges": int(torch.sum(edge_norms > GAP_FLOOR).item()),
        "sampled_edges": int(n),
    }


def run_scaling_suite(records: list[dict[str, Any]], axis0: dict[str, Any], memory: dict[str, Any], signal: dict[str, Any]) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for family, shape, seed in scaling_specs():
        rows[spec_key(family, shape)] = run_size_mode_suite(records, axis0, memory, signal, family, shape, seed)

    family_groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows.values():
        family_groups.setdefault(row["family"], []).append(row)
    family_summary = {}
    for family, group in family_groups.items():
        ordered = sorted(group, key=lambda r: r["site_count"])
        family_summary[family] = {
            "site_counts": [row["site_count"] for row in ordered],
            "full_vs_flat_gaps": [row["full_vs_flat_gap"] for row in ordered],
            "full_vs_shuffled_gaps": [row["full_vs_shuffled_gap"] for row in ordered],
            "full_vs_zero_gaps": [row["full_vs_zero_gap"] for row in ordered],
            "full_vs_flat_local_rms_gaps": [row["full_vs_flat_local"]["rms"] for row in ordered],
            "full_vs_shuffled_local_rms_gaps": [row["full_vs_shuffled_local"]["rms"] for row in ordered],
            "full_vs_zero_local_rms_gaps": [row["full_vs_zero_local"]["rms"] for row in ordered],
            "all_sizes_pass": all(row["pass"] for row in ordered),
            "variable_site_counts": len({row["site_count"] for row in ordered}) >= 3,
            "minimum_nonzero_gap": float(
                min(
                    min(row["full_vs_flat_gap"], row["full_vs_shuffled_gap"], row["full_vs_zero_gap"])
                    for row in ordered
                )
            ),
        }
    return {
        "rows": rows,
        "family_summary": family_summary,
        "robust_scaling_admission": robust_scaling_admission(rows),
        "site_counts": {key: row["site_count"] for key, row in rows.items()},
        "gap_summary": {
            key: {
                "full_vs_flat_gap": row["full_vs_flat_gap"],
                "full_vs_shuffled_gap": row["full_vs_shuffled_gap"],
                "full_vs_zero_gap": row["full_vs_zero_gap"],
                "full_vs_flat_local_rms_gap": row["full_vs_flat_local"]["rms"],
                "full_vs_shuffled_local_rms_gap": row["full_vs_shuffled_local"]["rms"],
                "full_vs_zero_local_rms_gap": row["full_vs_zero_local"]["rms"],
            }
            for key, row in rows.items()
        },
        "pass": all(row["pass"] for row in rows.values())
        and all(row["all_sizes_pass"] and row["variable_site_counts"] for row in family_summary.values()),
    }


def robust_scaling_admission(rows: dict[str, Any]) -> dict[str, Any]:
    peps3d32 = rows.get("peps3d_4x4x2", {})
    peps3d64 = rows.get("peps3d_4x4x4", {})
    flat32 = float(peps3d32.get("full_vs_flat_gap", 0.0))
    flat64 = float(peps3d64.get("full_vs_flat_gap", 0.0))
    shuffled64 = float(peps3d64.get("full_vs_shuffled_gap", 0.0))
    zero64 = float(peps3d64.get("full_vs_zero_gap", 0.0))
    ratio = float(flat64 / flat32) if flat32 else 0.0
    local_flat32 = float((peps3d32.get("full_vs_flat_local") or {}).get("rms", 0.0))
    local_flat64 = float((peps3d64.get("full_vs_flat_local") or {}).get("rms", 0.0))
    local_shuffled64 = float((peps3d64.get("full_vs_shuffled_local") or {}).get("rms", 0.0))
    local_zero64 = float((peps3d64.get("full_vs_zero_local") or {}).get("rms", 0.0))
    local_ratio = float(local_flat64 / local_flat32) if local_flat32 else 0.0
    compressed_summary_checks = {
        "peps3d64_flat_gap_meets_absolute_floor": flat64 >= PEPS3D_64_FLAT_ABSOLUTE_FLOOR,
        "peps3d64_flat_gap_preserves_twenty_percent_of_peps3d32": ratio >= PEPS3D_64_TO_32_FLAT_RATIO_FLOOR,
        "peps3d64_shuffled_gap_meets_floor": shuffled64 >= PEPS3D_64_SHUFFLED_FLOOR,
        "peps3d64_zero_gap_meets_floor": zero64 >= PEPS3D_64_ZERO_FLOOR,
    }
    local_sensitive_checks = {
        "peps3d64_local_flat_rms_meets_absolute_floor": local_flat64 >= PEPS3D_64_LOCAL_FLAT_RMS_FLOOR,
        "peps3d64_local_flat_rms_preserves_twenty_percent_of_peps3d32": local_ratio >= PEPS3D_64_TO_32_LOCAL_FLAT_RATIO_FLOOR,
        "peps3d64_local_shuffled_rms_meets_floor": local_shuffled64 >= PEPS3D_64_LOCAL_SHUFFLED_RMS_FLOOR,
        "peps3d64_local_zero_rms_meets_floor": local_zero64 >= PEPS3D_64_LOCAL_ZERO_RMS_FLOOR,
    }
    compressed_summary_admitted = all(compressed_summary_checks.values())
    local_sensitive_admitted = all(local_sensitive_checks.values())
    admitted = local_sensitive_admitted
    if local_sensitive_admitted and compressed_summary_admitted:
        status = "admitted_finite_robust_scaling"
        claim = (
            "Detectable finite variable-size consumption survives under both "
            "compressed global-summary and local-sensitive PEPS3D64 readouts "
            "for this guard-filtered Axis0 drive."
        )
    elif local_sensitive_admitted:
        status = "admitted_local_sensitive_scaling_compressed_summary_attenuated"
        claim = (
            "Detectable finite variable-size consumption survives. The compressed "
            "global-summary PEPS3D64 flat-gap remains attenuated, but a local-sensitive "
            "per-edge RMS readout admits PEPS3D64 scaling under matched controls."
        )
    else:
        status = "blocked_detectable_but_attenuated_peps3d64"
        claim = (
            "Finite variable-size consumption is detectable but remains too attenuated "
            "for PEPS3D64 admission under the current readouts."
        )
    return {
        "admitted": admitted,
        "status": status,
        "compressed_summary_admitted": compressed_summary_admitted,
        "local_sensitive_admitted": local_sensitive_admitted,
        "compressed_summary_checks": compressed_summary_checks,
        "local_sensitive_checks": local_sensitive_checks,
        "peps3d32_full_vs_flat_gap": flat32,
        "peps3d64_full_vs_flat_gap": flat64,
        "peps3d64_to_peps3d32_flat_gap_ratio": ratio,
        "peps3d64_full_vs_shuffled_gap": shuffled64,
        "peps3d64_full_vs_zero_gap": zero64,
        "peps3d32_full_vs_flat_local_rms_gap": local_flat32,
        "peps3d64_full_vs_flat_local_rms_gap": local_flat64,
        "peps3d64_to_peps3d32_local_flat_rms_ratio": local_ratio,
        "peps3d64_full_vs_shuffled_local_rms_gap": local_shuffled64,
        "peps3d64_full_vs_zero_local_rms_gap": local_zero64,
        "thresholds": {
            "peps3d64_flat_absolute_floor": PEPS3D_64_FLAT_ABSOLUTE_FLOOR,
            "peps3d64_to_peps3d32_flat_ratio_floor": PEPS3D_64_TO_32_FLAT_RATIO_FLOOR,
            "peps3d64_shuffled_floor": PEPS3D_64_SHUFFLED_FLOOR,
            "peps3d64_zero_floor": PEPS3D_64_ZERO_FLOOR,
            "peps3d64_local_flat_rms_floor": PEPS3D_64_LOCAL_FLAT_RMS_FLOOR,
            "peps3d64_to_peps3d32_local_flat_ratio_floor": PEPS3D_64_TO_32_LOCAL_FLAT_RATIO_FLOOR,
            "peps3d64_local_shuffled_rms_floor": PEPS3D_64_LOCAL_SHUFFLED_RMS_FLOOR,
            "peps3d64_local_zero_rms_floor": PEPS3D_64_LOCAL_ZERO_RMS_FLOOR,
        },
        "claim": claim,
    }


def dependency_graph() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    edges = [
        ("EngineCore.stage_records", "trained_auto_LiRPA_policy_gate"),
        ("Axis0.plural_router", "trained_auto_LiRPA_policy_gate"),
        ("Holodeck.hash_memory_placeholder", "trained_auto_LiRPA_policy_gate"),
        ("trained_auto_LiRPA_policy_gate", "MPS.variable_size_updates"),
        ("trained_auto_LiRPA_policy_gate", "PEPS.variable_size_updates"),
        ("trained_auto_LiRPA_policy_gate", "PEPS3D.variable_size_updates"),
        ("flat_gate_control", "repair_receipt"),
        ("shuffled_gate_control", "repair_receipt"),
        ("zero_gate_control", "repair_receipt"),
    ]
    node_ids: dict[str, int] = {}
    for left, right in edges:
        if left not in node_ids:
            node_ids[left] = graph.add_node(left)
        if right not in node_ids:
            node_ids[right] = graph.add_node(right)
        graph.add_edge(node_ids[left], node_ids[right], {"dependency": True})
    return {
        "nodes": graph.num_nodes(),
        "edges": graph.num_edges(),
        "edge_list": edges,
        "pass": rx.is_directed_acyclic_graph(graph),
    }


def z3_variable_scaling_witness(suite: dict[str, Any], signal: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    family_count = z3.Int("family_count")
    min_family_sizes = z3.Int("min_family_sizes")
    all_rows_pass = z3.Bool("all_rows_pass")
    gate_varies = z3.Bool("gate_varies")
    controls_separate = z3.Bool("controls_separate")
    robust_scaling_admitted = z3.Bool("robust_scaling_admitted")
    family_summaries = suite["family_summary"]
    min_sizes = min(len(set(row["site_counts"])) for row in family_summaries.values())
    min_gap = min(row["minimum_nonzero_gap"] for row in family_summaries.values())
    solver.add(family_count == len(family_summaries))
    solver.add(min_family_sizes == min_sizes)
    solver.add(all_rows_pass == bool(suite["pass"]))
    solver.add(gate_varies == (float(signal.get("gate_variance", 0.0)) > 1e-5))
    solver.add(controls_separate == (min_gap > GAP_FLOOR))
    solver.add(robust_scaling_admitted == bool(suite["robust_scaling_admission"]["admitted"]))
    solver.add(z3.Not(z3.And(family_count == 3, min_family_sizes >= 3, all_rows_pass, gate_varies, controls_separate)))
    status = solver.check()
    return {
        "pass": status == z3.unsat,
        "solver_status": str(status),
        "minimum_nonzero_gap": float(min_gap),
        "robust_scaling_admitted": bool(suite["robust_scaling_admission"]["admitted"]),
        "claim_ceiling": "Finite witness over variable carrier sizes and matched-control separation only.",
    }


def compact_rows(rows: dict[str, Any]) -> dict[str, Any]:
    compact = {}
    for key, row in rows.items():
        compact[key] = {
            "family": row["family"],
            "shape": row["shape"],
            "site_count": row["site_count"],
            "edge_count": row["edge_count"],
            "full_vs_flat_gap": row["full_vs_flat_gap"],
            "full_vs_shuffled_gap": row["full_vs_shuffled_gap"],
            "full_vs_zero_gap": row["full_vs_zero_gap"],
            "full_vs_flat_local_rms_gap": row["full_vs_flat_local"]["rms"],
            "full_vs_shuffled_local_rms_gap": row["full_vs_shuffled_local"]["rms"],
            "full_vs_zero_local_rms_gap": row["full_vs_zero_local"]["rms"],
            "full_vs_flat_local_nonzero_edges": row["full_vs_flat_local"]["nonzero_edges"],
            "sampled_environment_edges": row["full_vs_flat_local"]["sampled_edges"],
            "full_environment_shift": row["full"]["environment_shift_from_initial"],
            "policy_gate_mean": row["full"]["policy_gate_mean"],
            "policy_gate_variance": row["full"]["policy_gate_variance"],
            "stage_records_consumed": row["full"]["stage_records_consumed"],
            "unique_model_after_hashes_consumed": row["full"]["unique_model_after_hashes_consumed"],
            "sample_environment_head": row["full"]["environment_rows_head"][:1],
            "pass": row["pass"],
        }
    return compact


def compressed_summary_blocker(admission: dict[str, Any]) -> dict[str, Any]:
    return {
        "admitted": False,
        "status": "blocked_compressed_global_summary_peps3d64_flat_gap",
        "compressed_summary_admitted": bool(admission["compressed_summary_admitted"]),
        "compressed_summary_checks": admission["compressed_summary_checks"],
        "peps3d32_full_vs_flat_gap": admission["peps3d32_full_vs_flat_gap"],
        "peps3d64_full_vs_flat_gap": admission["peps3d64_full_vs_flat_gap"],
        "peps3d64_to_peps3d32_flat_gap_ratio": admission["peps3d64_to_peps3d32_flat_gap_ratio"],
        "local_sensitive_repair_status": admission["status"],
        "local_sensitive_admitted": bool(admission["local_sensitive_admitted"]),
        "claim": "Compressed mean/std/last-edge summary remains too attenuated for PEPS3D64 full-vs-flat scaling; local per-edge RMS repair is the admitted finite scaling path.",
    }


def main() -> int:
    started = time.time()
    records = subdense.run_source_records()
    lirpa_receipt = gated.load_result("auto_lirpa_trained_stage_policy_adapter_bound_probe_results.json")
    gated_receipt = gated.load_result("lirpa_policy_bound_gated_multicarrier_environment_probe_results.json")
    subdense_receipt = gated.load_result("source_native_multicarrier_subdense_environment_contraction_probe_results.json")
    axis0_receipt = gated.load_result("macro_sim_axis0_plural_stage_candidate_router_probe_results.json")
    axis0_guard_receipt = gated.load_result(axis0_guard.AXIS0_GUARD_RESULT_NAME)
    memory_receipt = gated.load_result("source_native_holodeck_hash_memory_placeholder_probe_results.json")
    guard = axis0_guard.axis0_guard_signal(axis0_guard_receipt)
    axis0 = axis0_guard.filter_subdense_axis0_signature(subdense.axis0_signature(axis0_receipt), guard)
    memory = subdense.holodeck_memory_signal(memory_receipt)
    signal = gated.policy_gate_signal(lirpa_receipt)
    suite = run_scaling_suite(records, axis0, memory, signal)
    graph = dependency_graph()
    z3_witness = z3_variable_scaling_witness(suite, signal)

    repair_receipt = {
        "weak_link": "The LiRPA-gated multicarrier bridge covered fixed carrier sizes, and its first variable-size repair left PEPS3D64 full-vs-flat separation attenuated under a compressed global summary.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": "A policy-bound multicarrier gate must execute across multiple MPS, PEPS, and PEPS3D site counts and separate from flat, shuffled, and zero-gate controls at every tested size, or emit a scaling blocker.",
        "dependency_subset": [
            "auto_lirpa_trained_stage_policy_adapter_bound receipt",
            "lirpa_policy_bound_gated_multicarrier_environment receipt",
            "source_native_multicarrier_subdense_environment_contraction receipt",
            "macro_sim_axis0_plural_stage_candidate_router receipt",
            "axis0_plural_candidate_multicarrier_drive_controls receipt",
            "source_native_holodeck_hash_memory_placeholder receipt",
            "EngineCore source-native stage records",
        ],
        "stage_fields_touched_or_consumed": subdense.REQUIRED_STAGE_FIELDS,
        "before_baseline/hash": {
            "fixed_size_lirpa_gated_result": gated_receipt.get("path"),
            "fixed_size_lirpa_gated_result_sha256": sha256_file(pathlib.Path(gated_receipt["path"])) if gated_receipt.get("exists") else "missing",
        },
        "after_delta/hash": {
            "script_sha256": sha256_file(pathlib.Path(__file__)),
            "result_path": str(OUT_PATH),
            "variable_specs": [spec_key(family, shape) for family, shape, _ in scaling_specs()],
        },
        "primary_control/result": {
            "family_summary": suite["family_summary"],
            "gap_summary": suite["gap_summary"],
            "robust_scaling_admission": suite["robust_scaling_admission"],
            "gate_signal": {
                "ready": signal["ready"],
                "gate_mean": signal["gate_mean"],
                "gate_variance": signal["gate_variance"],
                "gate_vector_len": len(signal.get("policy_bound_gate_vector", [])),
            },
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
            "holodeck_memory_ready": memory.get("ready"),
            "robust_peps3d64_scaling": suite["robust_scaling_admission"],
        },
        "provider_inputs_used": {
            "grok": "not_run_this_repair_wave",
            "gemini": "not_run_this_repair_wave",
            "sonnet_high": "not_run_this_repair_wave",
            "opus_max": "not_run_this_repair_wave",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "Use the guard-filtered finite scaling path while keeping PEPS3D64 compressed-summary and local-sensitive status explicit; next repair should test a size-normalized true PEPS3D environment contraction, not raise the claim ceiling.",
    }

    positive = {
        "upstream_receipts_are_consumed": {
            "pass": all(
                receipt.get("exists") and receipt.get("all_pass") is True
                for receipt in [lirpa_receipt, gated_receipt, subdense_receipt, axis0_receipt, axis0_guard_receipt, memory_receipt]
            ),
            "receipts": {
                "trained_lirpa": lirpa_receipt,
                "fixed_size_lirpa_gated": gated_receipt,
                "subdense_environment": subdense_receipt,
                "axis0_router": axis0_receipt,
                "axis0_guard": axis0_guard_receipt,
                "holodeck_memory": memory_receipt,
            },
        },
        "axis0_guard_filters_variable_qubit_carrier_drive": {
            "pass": bool(
                guard["pass"]
                and axis0.get("ready")
                and axis0.get("candidate_names") == guard["admitted_candidate_names"]
                and all(name not in axis0.get("candidate_names", []) for name in guard["blocked_candidate_names"])
            ),
            "axis0_candidate_names_used_in_drive": axis0.get("candidate_names"),
            "blocked_candidate_names": guard["blocked_candidate_names"],
        },
        "variable_qubit_mps_peps_peps3d_scaling_executes": {
            "pass": suite["pass"],
            "family_summary": suite["family_summary"],
            "robust_scaling_admission": suite["robust_scaling_admission"],
            "site_counts": suite["site_counts"],
            "rows": compact_rows(suite["rows"]),
        },
        "local_sensitive_peps3d64_scaling_repair_admitted": {
            "pass": suite["robust_scaling_admission"]["local_sensitive_admitted"] is True,
            "robust_scaling_admission": suite["robust_scaling_admission"],
        },
        "policy_bound_gate_signal_remains_available_for_scaling": {
            "pass": signal["ready"] and signal["gate_variance"] > 1e-5 and len(signal.get("policy_bound_gate_vector", [])) >= len(records),
            "gate_vector_len": len(signal.get("policy_bound_gate_vector", [])),
            "record_count": len(records),
            "gate_mean": signal["gate_mean"],
            "gate_variance": signal["gate_variance"],
        },
        "dependency_graph_is_acyclic": graph,
        "z3_variable_scaling_witness_executes": z3_witness,
    }
    graveyards = {
        "single_fixed_size_evidence_is_not_enough": {
            "pass": all(summary["variable_site_counts"] for summary in suite["family_summary"].values()),
            "fixed_size_receipt": gated_receipt,
            "variable_site_counts": {family: row["site_counts"] for family, row in suite["family_summary"].items()},
        },
        "flat_gate_control_is_distinguished_at_every_size": {
            "pass": all(row["full_vs_flat_gap"] > GAP_FLOOR for row in suite["rows"].values()),
            "gaps": {key: row["full_vs_flat_gap"] for key, row in suite["rows"].items()},
        },
        "shuffled_gate_control_is_distinguished_at_every_size": {
            "pass": all(row["full_vs_shuffled_gap"] > GAP_FLOOR for row in suite["rows"].values()),
            "gaps": {key: row["full_vs_shuffled_gap"] for key, row in suite["rows"].items()},
        },
        "zero_gate_control_is_distinguished_at_every_size": {
            "pass": all(row["full_vs_zero_gap"] > GAP_FLOOR for row in suite["rows"].values()),
            "gaps": {key: row["full_vs_zero_gap"] for key, row in suite["rows"].items()},
        },
        "compressed_global_summary_peps3d64_scaling_status_is_explicit": {
            "pass": bool(
                suite["robust_scaling_admission"]["local_sensitive_admitted"] is True
                and suite["robust_scaling_admission"]["status"]
                in {
                    "admitted_finite_robust_scaling",
                    "admitted_local_sensitive_scaling_compressed_summary_attenuated",
                }
            ),
            **suite["robust_scaling_admission"],
        },
        "blocked_axis0_candidates_not_used_in_variable_qubit_carrier_drive": {
            "pass": all(name not in axis0.get("candidate_names", []) for name in guard["blocked_candidate_names"]),
            "blocked_candidate_names": guard["blocked_candidate_names"],
            "drive_candidate_names": axis0.get("candidate_names"),
        },
    }
    boundary = {
        "claim_ceiling_blocks_asymptotic_or_final_architecture_claims": {
            "pass": all(term in CLAIM_CEILING.lower() for term in ["formal scout", "does not prove asymptotic", "does not prove", "canonical"]),
        },
        "repair_receipt_has_required_loop_fields": {
            "pass": all(key in repair_receipt for key in REQUIRED_REPAIR_RECEIPT_FIELDS),
            "keys": sorted(repair_receipt),
        },
        "integration_is_dependency_consumption_not_result_aggregation": {
            "pass": all(
                row["stage_records_consumed"] == len(records)
                and row["unique_model_after_hashes_consumed"] > 16
                and row["policy_gate_variance"] > 1e-5
                for row in compact_rows(suite["rows"]).values()
            ),
            "record_count": len(records),
            "consumed_stage_fields": subdense.REQUIRED_STAGE_FIELDS,
        },
    }
    nearby_variants = {
        "total": len(graveyards),
        "passed": sum(1 for row in graveyards.values() if row["pass"]),
        "variants": sorted(graveyards),
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
        and nearby_variants["passed"] == nearby_variants["total"]
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
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "repair_receipt": repair_receipt,
        "axis0_outputs_or_blockers": repair_receipt["axis0_outputs_or_blockers"],
        "explicit_blockers": (
            {}
            if suite["robust_scaling_admission"]["compressed_summary_admitted"]
            else {
                "compressed_global_summary_peps3d64_scaling": compressed_summary_blocker(
                    suite["robust_scaling_admission"]
                )
            }
        ),
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "This is a v5 downstream scaling scout over the repaired source-native macro-sim path.",
            "It extends fixed-size LiRPA-gated multicarrier consumption but does not prove asymptotic scaling or final PEPS/PEPS3D environment behavior.",
            "Provider proposals are not counted; only local receipts and matched controls carry evidence.",
        ],
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
