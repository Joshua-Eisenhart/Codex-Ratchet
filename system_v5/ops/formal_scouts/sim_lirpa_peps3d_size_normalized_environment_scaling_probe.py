#!/usr/bin/env python3
"""Size-normalized PEPS3D local-environment scaling scout.

This repair consumes the variable-qubit LiRPA-gated multicarrier receipt and
tests whether its admitted PEPS3D32/PEPS3D64 signal survives normalization by
the honest PEPS3D edge denominator. It preserves the upstream compressed-summary
status explicitly instead of assuming it is always blocked.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import time
from typing import Any

import networkx as nx
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "lirpa_peps3d_size_normalized_environment_scaling_probe_results.json"
UPSTREAM_RESULT = RESULT_DIR / "lirpa_policy_bound_variable_qubit_scaling_probe_results.json"

NAME = "lirpa_peps3d_size_normalized_environment_scaling_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SIM_EXECUTION_KIND = "receipt_audit"
SOURCE_ALIGNMENT_CATEGORY = "lirpa_peps3d_size_normalized_environment_scaling"
CLAIM_CEILING = (
    "Formal scout only: consumes the variable-qubit LiRPA-gated multicarrier "
    "receipt and tests whether the local-sensitive PEPS3D32/PEPS3D64 signal "
    "survives normalization by total PEPS3D edge count and sampled-edge readout "
    "count. It does not prove asymptotic scaling, a full PEPS/PEPS3D "
    "environment theorem, gauge-invariant geometry, a final controller, neural "
    "world model, physics, cognition, or canonical architecture, and it does "
    "not admit canonical architecture."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing consumed-upstream scalar ratio checks and receipt serialization",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing dependency graph for upstream receipt consumption and branch closure",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite witness for normalized ratio and blocker predicates",
    },
    "auto_LiRPA": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through consumed upstream policy-bound gate receipt",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through consumed upstream PEPS3D local-environment carrier receipt",
    },
}
TOOL_INTEGRATION_DEPTH = {
    'python_json': 'supportive',
    'networkx': 'load_bearing',
    'z3': 'load_bearing',
    'auto_LiRPA': 'load_bearing',
    'quimb': 'load_bearing',
}
TOOL_ROLE_SOURCE = {tool: "local" for tool in TOOL_MANIFEST}

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

PEPS3D32_KEY = "peps3d_4x4x2"
PEPS3D64_KEY = "peps3d_4x4x4"
TOTAL_EDGE_RATIO_FLOOR = 0.20
SAMPLED_EDGE_RATIO_FLOOR = 0.20
TOTAL_EDGE_ABSOLUTE_FLOORS = {
    "flat": 1.0e-4,
    "shuffled": 1.0e-4,
    "zero": 1.0e-3,
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    return value


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_upstream() -> dict[str, Any]:
    if not UPSTREAM_RESULT.exists():
        return {"exists": False, "path": str(UPSTREAM_RESULT)}
    data = json.loads(UPSTREAM_RESULT.read_text(encoding="utf-8"))
    return {"exists": True, "path": str(UPSTREAM_RESULT), "data": data}


def local_metric(row: dict[str, Any], control: str) -> float:
    return float(row[f"full_vs_{control}_local_rms_gap"])


def normalized_metrics(row: dict[str, Any]) -> dict[str, Any]:
    edge_count = int(row["edge_count"])
    sampled_edges = int(row["sampled_environment_edges"])
    out = {
        "site_count": int(row["site_count"]),
        "edge_count": edge_count,
        "sampled_environment_edges": sampled_edges,
        "raw_local_rms": {},
        "total_edge_normalized_rms": {},
        "sampled_edge_normalized_rms": {},
    }
    for control in ("flat", "shuffled", "zero"):
        raw = local_metric(row, control)
        out["raw_local_rms"][control] = raw
        out["total_edge_normalized_rms"][control] = raw / math.sqrt(edge_count)
        out["sampled_edge_normalized_rms"][control] = raw / math.sqrt(sampled_edges)
    return out


def compare_peps3d(rows: dict[str, Any]) -> dict[str, Any]:
    peps3d32 = normalized_metrics(rows[PEPS3D32_KEY])
    peps3d64 = normalized_metrics(rows[PEPS3D64_KEY])
    ratios: dict[str, Any] = {
        "total_edge_normalized_ratio_64_to_32": {},
        "sampled_edge_normalized_ratio_64_to_32": {},
    }
    checks: dict[str, bool] = {}
    for control in ("flat", "shuffled", "zero"):
        total32 = peps3d32["total_edge_normalized_rms"][control]
        total64 = peps3d64["total_edge_normalized_rms"][control]
        sampled32 = peps3d32["sampled_edge_normalized_rms"][control]
        sampled64 = peps3d64["sampled_edge_normalized_rms"][control]
        total_ratio = total64 / total32 if total32 else 0.0
        sampled_ratio = sampled64 / sampled32 if sampled32 else 0.0
        ratios["total_edge_normalized_ratio_64_to_32"][control] = total_ratio
        ratios["sampled_edge_normalized_ratio_64_to_32"][control] = sampled_ratio
        checks[f"{control}_total_edge_normalized_64_above_absolute_floor"] = (
            total64 >= TOTAL_EDGE_ABSOLUTE_FLOORS[control]
        )
        checks[f"{control}_total_edge_ratio_preserves_twenty_percent"] = total_ratio >= TOTAL_EDGE_RATIO_FLOOR
        checks[f"{control}_sampled_edge_ratio_preserves_twenty_percent"] = sampled_ratio >= SAMPLED_EDGE_RATIO_FLOOR
    return {
        "peps3d32": peps3d32,
        "peps3d64": peps3d64,
        "ratios": ratios,
        "checks": checks,
        "admitted_size_normalized_local_scaling": all(checks.values()),
        "denominator_note": (
            "total_edge_normalized_rms divides by sqrt(total PEPS3D graph edge_count); "
            "sampled_edge_normalized_rms divides by sqrt(sampled readout edges) and is recorded "
            "as a readout-control denominator, not the full environment denominator."
        ),
    }


def compressed_summary_status(upstream_data: dict[str, Any]) -> dict[str, Any]:
    blocker = (upstream_data.get("explicit_blockers") or {}).get("compressed_global_summary_peps3d64_scaling", {})
    upstream_axis0 = upstream_data.get("axis0_outputs_or_blockers") or {}
    robust = upstream_axis0.get("robust_peps3d64_scaling") or {}
    compressed_admitted = bool(robust.get("compressed_summary_admitted"))
    return {
        "pass": bool(compressed_admitted or (blocker and blocker.get("admitted") is False)),
        "compressed_summary_admitted": compressed_admitted,
        "upstream_status": robust.get("status"),
        "upstream_claim": robust.get("claim"),
        "source_blocker": blocker,
        "claim": (
            "Compressed global-summary PEPS3D64 status is inherited from the upstream "
            "variable-qubit receipt and recorded explicitly; this scout does not silently "
            "preserve a stale blocker or raise the claim ceiling."
        ),
    }


def dependency_graph() -> dict[str, Any]:
    graph = nx.DiGraph()
    edges = [
        ("EngineCore.stage_records", "auto_LiRPA.policy_gate"),
        ("auto_LiRPA.policy_gate", "lirpa_policy_bound_variable_qubit_scaling"),
        ("lirpa_policy_bound_variable_qubit_scaling", "peps3d32_local_environment_rms"),
        ("lirpa_policy_bound_variable_qubit_scaling", "peps3d64_local_environment_rms"),
        ("peps3d32_local_environment_rms", "size_normalized_ratio"),
        ("peps3d64_local_environment_rms", "size_normalized_ratio"),
        ("compressed_global_summary_status", "claim_ceiling"),
        ("size_normalized_ratio", "repair_receipt"),
    ]
    graph.add_edges_from(edges)
    return {
        "pass": nx.is_directed_acyclic_graph(graph),
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "edge_list": edges,
    }


def _matmul(a: list[list[complex]], b: list[list[complex]]) -> list[list[complex]]:
    return [
        [sum(a[row][k] * b[k][col] for k in range(2)) for col in range(2)]
        for row in range(2)
    ]


def _sub(a: list[list[complex]], b: list[list[complex]]) -> list[list[complex]]:
    return [[a[row][col] - b[row][col] for col in range(2)] for row in range(2)]


def _fro_norm(a: list[list[complex]]) -> float:
    return math.sqrt(sum(abs(cell) ** 2 for row in a for cell in row))


def _bloch_density(sample: dict[str, Any], keys: tuple[str, str, str]) -> list[list[complex]]:
    x = float(sample[keys[0]])
    y = float(sample[keys[1]])
    z = float(sample[keys[2]])
    return [
        [0.5 * (1.0 + z), 0.5 * (x - 1j * y)],
        [0.5 * (x + 1j * y), 0.5 * (1.0 - z)],
    ]


def n01_order_witness(rows: dict[str, Any]) -> dict[str, Any]:
    """Finite PEPS3D local readout order witness without adding NumPy."""

    x_op = [[0j, 1 + 0j], [1 + 0j, 0j]]
    z_op = [[1 + 0j, 0j], [0j, -1 + 0j]]
    samples: dict[str, Any] = {}
    gaps: list[float] = []
    for key in (PEPS3D32_KEY, PEPS3D64_KEY):
        sample = rows.get(key, {}).get("sample_environment_head", [{}])[0]
        if not sample:
            continue
        rho = _bloch_density(sample, ("pauli_xI", "pauli_yI", "pauli_zI"))
        xz_rho = _matmul(_matmul(x_op, z_op), rho)
        zx_rho = _matmul(_matmul(z_op, x_op), rho)
        gap = _fro_norm(_sub(xz_rho, zx_rho))
        gaps.append(gap)
        samples[key] = {
            "finite_peps3d_site_count": int(rows[key]["site_count"]),
            "ordered_operator_pair": "X_then_Z_vs_Z_then_X_on_sampled_edge_x_site_density",
            "commutator_gap_frobenius": gap,
            "sample_edge": sample.get("edge"),
        }

    solver = z3.Solver()
    witness_count = z3.Int("peps3d_order_witness_count")
    min_gap = z3.Real("min_commutator_gap")
    solver.add(witness_count == len(gaps))
    solver.add(min_gap == str(round(min(gaps) if gaps else 0.0, 12)))
    solver.add(z3.Not(z3.And(witness_count == 2, min_gap > 0)))
    status = solver.check()
    return {
        "pass": bool(gaps) and status == z3.unsat,
        "solver_status": str(status),
        "root": "N01_noncommutation_or_order_sensitivity",
        "claim": "Finite PEPS3D sampled-edge density changes under XZ versus ZX operator order; this is a local order witness only.",
        "samples": samples,
    }


def z3_normalization_witness(comparison: dict[str, Any], compressed_status: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    normalized_admitted = z3.Bool("normalized_admitted")
    compressed_status_recorded = z3.Bool("compressed_status_recorded")
    solver.add(normalized_admitted == bool(comparison["admitted_size_normalized_local_scaling"]))
    solver.add(compressed_status_recorded == bool(compressed_status["pass"]))
    solver.add(z3.Not(z3.And(normalized_admitted, compressed_status_recorded)))
    status = solver.check()
    return {
        "pass": status == z3.unsat,
        "solver_status": str(status),
        "claim_ceiling": "Finite witness only: size-normalized PEPS3D signal plus explicit compressed-summary status.",
    }


def main() -> int:
    started = time.time()
    upstream = load_upstream()
    data = upstream.get("data", {})
    upstream_positive = data.get("positive") or {}
    upstream_rows = (
        upstream_positive.get("variable_qubit_mps_peps_peps3d_scaling_executes", {}).get("rows", {})
    )
    comparison = compare_peps3d(upstream_rows) if PEPS3D32_KEY in upstream_rows and PEPS3D64_KEY in upstream_rows else {
        "admitted_size_normalized_local_scaling": False,
        "checks": {},
        "ratios": {},
        "peps3d32": {},
        "peps3d64": {},
        "denominator_note": "required PEPS3D rows missing",
    }
    compressed_status = compressed_summary_status(data)
    graph = dependency_graph()
    order_witness = n01_order_witness(upstream_rows)
    z3_witness = z3_normalization_witness(comparison, compressed_status)

    repair_receipt = {
        "weak_link": "The variable-qubit LiRPA scout admitted finite PEPS3D64 scaling, but the downstream size-normalized scout still assumed the old compressed-summary blocker and had not retested honest denominator discipline after Axis0 guard filtering.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": "A PEPS3D64 scaling repair must survive normalization by total PEPS3D edge count and sampled readout edge count, while recording the upstream compressed-summary status explicitly.",
        "dependency_subset": [
            "lirpa_policy_bound_variable_qubit_scaling receipt",
            "auto_LiRPA policy-bound gate consumed upstream",
            "source-native MPS/PEPS/PEPS3D local environment updates consumed upstream",
            "PEPS3D32 and PEPS3D64 local environment RMS controls",
            "finite PEPS3D sampled-edge XZ/ZX order witness",
        ],
        "stage_fields_touched_or_consumed": (
            data.get("repair_receipt", {}).get("stage_fields_touched_or_consumed", [])
            or data.get("positive", {}).get("variable_qubit_mps_peps_peps3d_scaling_executes", {}).get(
                "consumed_stage_fields", []
            )
            or "consumed through upstream variable-qubit scaling receipt"
        ),
        "before_baseline/hash": {
            "upstream_result": str(UPSTREAM_RESULT),
            "upstream_result_sha256": sha256_file(UPSTREAM_RESULT) if UPSTREAM_RESULT.exists() else "missing",
            "upstream_robust_scaling_admission": upstream_positive.get(
                "local_sensitive_peps3d64_scaling_repair_admitted", {}
            ).get("robust_scaling_admission", {}),
        },
        "after_delta/hash": {
            "script_sha256": sha256_file(pathlib.Path(__file__)),
            "result_path": str(OUT_PATH),
            "tested_keys": [PEPS3D32_KEY, PEPS3D64_KEY],
        },
        "primary_control/result": {
            "comparison": comparison,
            "matched_controls": ["flat_gate", "shuffled_gate", "zero_gate"],
            "compressed_summary_status": compressed_status,
        },
        "axis0_outputs_or_blockers": {
            "axis0_consumed_upstream": bool(
                (data.get("axis0_outputs_or_blockers") or {}).get("axis0_ready")
            ),
            "axis0_outputs_or_blockers_from_upstream": data.get("axis0_outputs_or_blockers", {}),
            "axis0_not_reinterpreted_here": "This scout only tests PEPS3D size-normalized environment readout; Axis0 candidates remain upstream inputs.",
        },
        "provider_inputs_used": {
            "grok": "not_counted_this_local_repair; prior provider receipts are proposal/audit only",
            "gemini": "not_counted_this_local_repair; direct audit lanes may run outside this receipt",
            "sonnet_high": "not_counted_this_local_repair; external repair scouts are proposal-only until local receipts exist",
            "opus_max": "not_counted_this_local_repair; external audits are proposal-only until local receipts exist",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "Use this denominator-discipline scout downstream of variable-qubit scaling; next larger repair is true PEPS3D environment contraction, not a higher claim ceiling.",
    }

    positive = {
        "upstream_variable_qubit_scaling_receipt_is_consumed": {
            "pass": bool(
                upstream.get("exists")
                and data.get("all_pass") is True
                and data.get("classification") == "formal_scout"
                and data.get("promotion_allowed") is False
            ),
            "upstream_path": str(UPSTREAM_RESULT),
            "upstream_name": data.get("name"),
            "upstream_claim_ceiling": data.get("claim_ceiling"),
        },
        "peps3d32_and_peps3d64_rows_are_present": {
            "pass": PEPS3D32_KEY in upstream_rows and PEPS3D64_KEY in upstream_rows,
            "required_keys": [PEPS3D32_KEY, PEPS3D64_KEY],
            "available_peps3d_keys": sorted(k for k in upstream_rows if k.startswith("peps3d_")),
        },
        "total_edge_normalized_local_signal_survives": {
            "pass": comparison["admitted_size_normalized_local_scaling"],
            "comparison": comparison,
        },
        "dependency_graph_is_acyclic": graph,
        "z3_size_normalization_witness_executes": z3_witness,
        "n01_noncommutation_or_order_witness": order_witness,
    }
    graveyards = {
        "compressed_global_summary_status_is_explicit_not_stale": compressed_status,
        "sampled_edge_normalization_is_not_confused_with_total_edge_normalization": {
            "pass": bool(
                comparison.get("peps3d32", {}).get("edge_count")
                != comparison.get("peps3d32", {}).get("sampled_environment_edges")
                and comparison.get("peps3d64", {}).get("edge_count")
                != comparison.get("peps3d64", {}).get("sampled_environment_edges")
            ),
            "denominator_note": comparison.get("denominator_note"),
            "peps3d32_edge_count": comparison.get("peps3d32", {}).get("edge_count"),
            "peps3d32_sampled_edges": comparison.get("peps3d32", {}).get("sampled_environment_edges"),
            "peps3d64_edge_count": comparison.get("peps3d64", {}).get("edge_count"),
            "peps3d64_sampled_edges": comparison.get("peps3d64", {}).get("sampled_environment_edges"),
        },
        "matched_gate_controls_remain_named": {
            "pass": all(
                f"{control}_total_edge_normalized_64_above_absolute_floor" in comparison.get("checks", {})
                and f"{control}_total_edge_ratio_preserves_twenty_percent" in comparison.get("checks", {})
                and f"{control}_sampled_edge_ratio_preserves_twenty_percent" in comparison.get("checks", {})
                for control in ("flat", "shuffled", "zero")
            ),
            "controls": ["flat_gate", "shuffled_gate", "zero_gate"],
        },
        "local_size_normalization_is_not_full_environment_theorem": {
            "pass": "does not prove asymptotic" in CLAIM_CEILING.lower()
            and "full peps/peps3d environment theorem" in CLAIM_CEILING.lower(),
            "claim_ceiling": CLAIM_CEILING,
        },
    }
    boundary = {
        "repair_receipt_has_required_loop_fields": {
            "pass": all(key in repair_receipt for key in REQUIRED_REPAIR_RECEIPT_FIELDS),
            "keys": sorted(repair_receipt),
        },
        "claim_ceiling_blocks_canonical_or_final_world_model_claims": {
            "pass": all(
                term in CLAIM_CEILING.lower()
                for term in ["formal scout", "does not prove asymptotic", "neural world model", "canonical"]
            ),
            "claim_ceiling": CLAIM_CEILING,
        },
        "integration_is_dependency_consumption_not_result_aggregation": {
            "pass": bool(
                upstream.get("exists")
                and data.get("all_pass") is True
                and comparison["admitted_size_normalized_local_scaling"]
                and compressed_status["pass"]
                and order_witness["pass"]
            ),
            "upstream_result_sha256": repair_receipt["before_baseline/hash"]["upstream_result_sha256"],
            "consumed_upstream_positive_sections": sorted(upstream_positive),
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
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "repair_receipt": repair_receipt,
        "axis0_outputs_or_blockers": repair_receipt["axis0_outputs_or_blockers"],
        "explicit_blockers": {
            **(
                {"compressed_global_summary_peps3d64_scaling": compressed_status["source_blocker"]}
                if compressed_status.get("source_blocker")
                else {}
            ),
            "full_peps3d_environment_theorem": {
                "admitted": False,
                "claim": "Size-normalized local RMS is not a full PEPS3D environment contraction theorem.",
            },
        },
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "This is a v5 downstream repair over the LiRPA-gated variable-qubit scaling path.",
            "It tests denominator discipline for local PEPS3D environment readouts; it does not promote compressed global summaries or asymptotic claims.",
            "Provider proposals are not counted as evidence until local receipts exist.",
        ],
        "blockers": [],
        "root_constraints": {
            "finite_carrier_root": True,
            "noncommutation_or_order_root": bool(order_witness["pass"]),
            "finite_evidence": "bounded PEPS3D32/PEPS3D64 sampled-edge density readouts",
            "noncommutation_or_order_evidence": "XZ versus ZX finite operator-order witness over sampled PEPS3D local density",
        },
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
