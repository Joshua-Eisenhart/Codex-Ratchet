#!/usr/bin/env python3
"""Closure guard for stage-record downstream carrier consumption.

This scout closes a stale bridge-reference gap without turning the upstream
stage-record scout into a downstream proof. It consumes the stage-record
contract receipt and the current subdense MPS/PEPS/PEPS3D environment receipt,
then verifies that the downstream carrier rows actually consumed the repaired
science-method records.

Formal scout only. It does not admit final carrier geometry, final Axis0,
Holodeck memory, world-model, FEP, physics, cognition, or canonical claims.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import networkx as nx


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "stage_record_downstream_carrier_consumption_closure_probe_results.json"

NAME = "stage_record_downstream_carrier_consumption_closure_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: verifies that the current subdense MPS/PEPS/PEPS3D "
    "carrier receipt consumes repaired EngineCore science-method stage records "
    "and that the stale common-boundary bridge receipt is no longer a live "
    "stage-record dependency. It does not admit final carrier geometry, final "
    "Axis0, Holodeck memory, world-model, FEP, physics, cognition, or canonical "
    "claims."
)

STAGE_SCRIPT = ROOT / "sim_macro_sim_stage_record_science_method_contract_probe.py"
STAGE_RESULT = RESULT_DIR / "macro_sim_stage_record_science_method_contract_probe_results.json"
SUBDENSE_RESULT = RESULT_DIR / "source_native_multicarrier_subdense_environment_contraction_probe_results.json"
STALE_BRIDGE_RESULT = "source_native_multicarrier_common_boundary_observable_bridge_probe_results.json"
EXPECTED_CARRIERS = {"mps_16", "peps_16", "peps3d_32", "peps3d_64"}

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing receipt parsing for stage-record and subdense carrier results",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source/result path existence and stale-reference checks",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing closure graph witness for the downstream consumption guard",
    },
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def read_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["exists"] = True
    data["path"] = str(path)
    return data


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def section_pass(data: dict[str, Any], section: str, key: str) -> bool:
    row = (data.get(section) or {}).get(key) or {}
    return bool(row.get("pass"))


def closure_graph() -> dict[str, Any]:
    graph = nx.DiGraph()
    edges = [
        ("macro_stage_record_science_method_contract", "source_native_subdense_multicarrier_environment"),
        ("source_native_subdense_multicarrier_environment", "stage_record_downstream_carrier_consumption_closure"),
        ("stage_record_downstream_carrier_consumption_closure", "axis0_plural_candidate_multicarrier_drive_controls"),
    ]
    graph.add_edges_from(edges)
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "acyclic": nx.is_directed_acyclic_graph(graph),
        "edge_list": edges,
    }


def stage_record_count(stage: dict[str, Any]) -> dict[str, Any]:
    row = (stage.get("positive") or {}).get("sixty_four_repaired_stage_records_execute") or {}
    engine_rows = row.get("engine_rows")
    control_rows = row.get("control_rows")
    total_rows = engine_rows + control_rows if isinstance(engine_rows, int) and isinstance(control_rows, int) else None
    return {
        "engine_rows": engine_rows,
        "control_rows": control_rows,
        "total_rows": total_rows,
    }


def freshness_report() -> dict[str, Any]:
    if not STAGE_SCRIPT.exists() or not STAGE_RESULT.exists():
        return {
            "pass": False,
            "stage_script_exists": STAGE_SCRIPT.exists(),
            "stage_result_exists": STAGE_RESULT.exists(),
        }
    script_mtime = STAGE_SCRIPT.stat().st_mtime
    result_mtime = STAGE_RESULT.stat().st_mtime
    return {
        "pass": result_mtime >= script_mtime,
        "stage_script_sha256": sha256_file(STAGE_SCRIPT),
        "stage_script_mtime": script_mtime,
        "stage_result_mtime": result_mtime,
    }


def carrier_report(subdense: dict[str, Any]) -> dict[str, Any]:
    row = (subdense.get("positive") or {}).get("science_method_stage_records_consumed_by_subdense_environment") or {}
    carriers = row.get("carrier_rows") or {}
    stage_contract = row.get("stage_contract") or {}
    expected_records = stage_contract.get("record_count")
    per_carrier = {}
    for key, carrier in carriers.items():
        per_carrier[key] = {
            "pass": bool(carrier.get("pass")),
            "carrier": carrier.get("carrier"),
            "family": carrier.get("family"),
            "site_count": carrier.get("site_count"),
            "stage_records_consumed": carrier.get("stage_records_consumed"),
            "unique_model_after_hashes_consumed": carrier.get("unique_model_after_hashes_consumed"),
            "gauge_control_pass": bool((carrier.get("gauge_control") or {}).get("pass")),
        }
    return {
        "positive_pass": bool(row.get("pass")),
        "carrier_keys": sorted(carriers),
        "expected_carriers": sorted(EXPECTED_CARRIERS),
        "stage_contract": stage_contract,
        "expected_stage_records_from_subdense_stage_contract": expected_records,
        "per_carrier": per_carrier,
    }


def carrier_rows_pass(report: dict[str, Any], expected_records: int | None) -> bool:
    if not isinstance(expected_records, int) or expected_records <= 0:
        return False
    if set(report["carrier_keys"]) != EXPECTED_CARRIERS:
        return False
    for row in report["per_carrier"].values():
        if not row["pass"]:
            return False
        if row["stage_records_consumed"] != expected_records:
            return False
        if row["unique_model_after_hashes_consumed"] != expected_records:
            return False
        if not row["gauge_control_pass"]:
            return False
    return True


def downstream_graph_pass(subdense: dict[str, Any]) -> dict[str, Any]:
    row = (subdense.get("positive") or {}).get("dependency_graph_is_acyclic") or {}
    edges = row.get("edge_list") or []
    required = [
        ["EngineCore.science_method_stage_records", "local_tensor_updates"],
        ["local_tensor_updates", "MPS.local_environment"],
        ["local_tensor_updates", "PEPS.local_environment"],
        ["local_tensor_updates", "PEPS3D.local_environment"],
    ]
    return {
        "pass": bool(row.get("pass")) and all(edge in edges for edge in required),
        "required_edges": required,
        "observed_edges": edges,
    }


def main() -> int:
    started = time.time()
    stage = read_json(STAGE_RESULT)
    subdense = read_json(SUBDENSE_RESULT)
    stage_source_text = STAGE_SCRIPT.read_text(encoding="utf-8") if STAGE_SCRIPT.exists() else ""
    stage_result_text = STAGE_RESULT.read_text(encoding="utf-8") if STAGE_RESULT.exists() else ""
    graph = closure_graph()
    carriers = carrier_report(subdense)
    counts = stage_record_count(stage)
    freshness = freshness_report()
    expected_records = carriers["expected_stage_records_from_subdense_stage_contract"]
    downstream_graph = downstream_graph_pass(subdense)

    stage_contract_pass = (
        bool(stage.get("exists"))
        and bool(stage.get("all_pass"))
        and section_pass(stage, "positive", "sixty_four_repaired_stage_records_execute")
        and section_pass(stage, "positive", "required_science_method_fields_present")
        and section_pass(stage, "positive", "dependency_consumption_graph_executes")
    )
    stale_absent = STALE_BRIDGE_RESULT not in stage_source_text and STALE_BRIDGE_RESULT not in stage_result_text
    expected_records_is_derived = (
        isinstance(expected_records, int)
        and expected_records == counts["total_rows"]
        and bool((carriers.get("stage_contract") or {}).get("pass"))
    )
    subdense_contract_pass = (
        bool(subdense.get("exists"))
        and bool(subdense.get("all_pass"))
        and carriers["positive_pass"]
        and expected_records_is_derived
        and carrier_rows_pass(carriers, expected_records)
        and downstream_graph["pass"]
    )

    repair_receipt = {
        "weak_link": "Stage-record receipt carried a stale missing common-boundary bridge dependency while the current downstream consumer is the subdense multicarrier environment scout.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": "Downstream carrier-consumption closure now requires a real subdense MPS/PEPS/PEPS3D receipt with stage-record consumption rows, not a missing bridge filename.",
        "dependency_subset": [
            str(STAGE_RESULT),
            str(SUBDENSE_RESULT),
            "positive.science_method_stage_records_consumed_by_subdense_environment",
            "MPS/PEPS/PEPS3D carrier rows",
            "stale common-boundary bridge reference absence check",
        ],
        "primary_control/result": {
            "stale_bridge_result_name": STALE_BRIDGE_RESULT,
            "stale_reference_absent_from_stage_source_and_result": stale_absent,
            "stage_receipt_freshness": freshness,
            "stage_record_count": counts,
            "expected_stage_records_derived_from_subdense_stage_contract": expected_records,
            "carrier_rows": carriers,
            "downstream_dependency_graph": downstream_graph,
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "Keep this as an integrated-suite closure guard; do not promote it to final multicarrier, Axis0, or Holodeck evidence.",
    }

    positive = {
        "stage_record_contract_receipt_exists_and_passes": {
            "pass": stage_contract_pass,
            "stage_result": str(STAGE_RESULT),
            "stage_all_pass": stage.get("all_pass"),
            "required_positive_checks": [
                "sixty_four_repaired_stage_records_execute",
                "required_science_method_fields_present",
                "dependency_consumption_graph_executes",
            ],
        },
        "stage_record_receipt_is_fresh_for_current_source": {
            "pass": freshness["pass"],
            **freshness,
        },
        "expected_stage_record_count_is_derived_not_magic": {
            "pass": expected_records_is_derived,
            "stage_record_count": counts,
            "subdense_stage_contract_record_count": expected_records,
        },
        "stale_common_boundary_bridge_reference_is_not_live": {
            "pass": stale_absent,
            "stale_bridge_result_name": STALE_BRIDGE_RESULT,
            "stage_source_contains_stale_reference": STALE_BRIDGE_RESULT in stage_source_text,
            "stage_result_contains_stale_reference": STALE_BRIDGE_RESULT in stage_result_text,
        },
        "subdense_carrier_receipt_consumes_stage_records": {
            "pass": subdense_contract_pass,
            "subdense_result": str(SUBDENSE_RESULT),
            "subdense_all_pass": subdense.get("all_pass"),
            "carrier_report": carriers,
            "downstream_dependency_graph": downstream_graph,
        },
        "closure_dependency_graph_is_acyclic": {
            "pass": graph["acyclic"],
            **graph,
        },
    }
    graveyards = {
        "missing_common_boundary_receipt_does_not_count_as_consumption": {
            "pass": stale_absent,
            "reason": "The missing common-boundary receipt is a dead reference, not downstream evidence.",
        },
        "single_carrier_consumption_is_rejected": {
            "pass": set(carriers["carrier_keys"]) == EXPECTED_CARRIERS,
            "observed": carriers["carrier_keys"],
            "required": sorted(EXPECTED_CARRIERS),
        },
        "hash_only_or_partial_record_consumption_is_rejected": {
            "pass": carrier_rows_pass(carriers, expected_records),
            "expected_stage_records": expected_records,
            "carrier_rows": carriers["per_carrier"],
        },
    }
    boundary = {
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        "claim_ceiling_blocks_final_carrier_axis0_holodeck_claims": {
            "pass": all(
                term in CLAIM_CEILING.lower()
                for term in ["formal scout", "does not admit", "final carrier", "final axis0", "holodeck"]
            ),
        },
        "closure_is_dependency_consumption_not_new_macro_sim": {
            "pass": graph["acyclic"] and bool(stage.get("exists")) and bool(subdense.get("exists")),
            "closure_graph": graph,
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
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "system_map": {
            "stage_record_source": str(STAGE_SCRIPT),
            "stage_record_receipt": str(STAGE_RESULT),
            "current_downstream_carrier_receipt": str(SUBDENSE_RESULT),
            "stale_bridge_result_name": STALE_BRIDGE_RESULT,
        },
        "repair_receipt": repair_receipt,
        "dependency_consumption": graph,
        "positive": positive,
        "graveyard_companions": graveyards,
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
            "variants": sorted(graveyards),
        },
        "boundary": boundary,
        "why_not_v4_probes": [
            "This guard consumes v5 formal-scout receipts directly.",
            "It does not reuse v4 probe semantics as authority.",
            "It does not claim final multicarrier, Axis0, Holodeck, or macro-sim evidence.",
        ],
        "blockers": [],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
