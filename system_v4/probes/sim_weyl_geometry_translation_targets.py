#!/usr/bin/env python3
"""
Weyl Geometry Translation Targets
=================================
Controller-facing translation-target surface for the Weyl/Hopf geometry lane.

This surface ranks the existing geometry rows into:
  - foundation
  - ready for stricter companion work
  - graph/proof bridge
  - sidecar

It is not a proof surface. It is a routing surface for the next geometry build
step.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any
classification = "canonical"


CLASSIFICATION = "canonical"
CLASSIFICATION_NOTE = (
    "Controller-facing translation-target surface for the Weyl/Hopf geometry "
    "lane. It ranks foundation rows, companion-ready rows, graph/proof bridges, "
    "and sidecars using the matrix, overlay, registry supplement, and audit "
    "surfaces."
)

LEGO_IDS = [
    "weyl_geometry_translation_targets",
    "nested_hopf_tori",
    "weyl_pauli_transport",
    "weyl_hopf_pauli_composed_stack",
    "weyl_geometry_protocol_dag",
    "weyl_geometry_graph_proof_alignment",
    "weyl_geometry_carrier_array",
    "weyl_geometry_carrier_compare",
    "weyl_geometry_ladder_audit",
]

PRIMARY_LEGO_IDS = [
    "weyl_geometry_translation_targets",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"

MATRIX_PATH = RESULT_DIR / "weyl_geometry_lab_matrix_results.json"
OVERLAY_PATH = RESULT_DIR / "weyl_geometry_alignment_overlay_results.json"
AUDIT_PATH = RESULT_DIR / "weyl_geometry_constraint_audit_results.json"
SUPPLEMENT_PATH = RESULT_DIR / "weyl_geometry_lego_registry_supplement_results.json"
REGISTRY_PATH = RESULT_DIR / "actual_lego_registry.json"

SUPPLEMENT_ROW_IDS = {
    "nested_hopf_tori": "nested_hopf_tori_geometry",
    "weyl_pauli_transport": "weyl_pauli_transport_geometry",
    "weyl_hopf_pauli_composed_stack": "weyl_hopf_pauli_composed_stack",
    "weyl_geometry_protocol_dag": "weyl_geometry_protocol_dag",
    "weyl_geometry_graph_proof_alignment": "weyl_geometry_graph_proof_alignment",
    "weyl_geometry_carrier_array": "weyl_geometry_carrier_array",
    "weyl_geometry_carrier_compare": "weyl_geometry_carrier_compare",
    "weyl_geometry_ladder_audit": "weyl_geometry_ladder_audit",
}

AUDIT_ALIAS_ROW_IDS = {
    "weyl_pauli_transport": "lego_weyl_pauli_transport",
}

FOUNDATION_ORDER = [
    "nested_hopf_tori",
    "weyl_pauli_transport",
    "hopf_torus_lego",
    "weyl_spinor_hopf",
]

COMPANION_READY_ORDER = [
    "weyl_hopf_pauli_composed_stack",
    "weyl_geometry_carrier_array",
    "weyl_geometry_carrier_compare",
]

GRAPH_PROOF_ORDER = [
    "weyl_geometry_graph_proof_alignment",
    "weyl_geometry_protocol_dag",
]

SIDECAR_ORDER = [
    "weyl_geometry_ladder_audit",
    "nested_torus_geometry",
    "foundation_hopf_torus_geomstats_clifford",
    "torch_hopf_connection",
    "weyl_nested_shell",
    "graph_shell_geometry",
    "toponetx_hopf_crosscheck",
]

ROW_ORDER = FOUNDATION_ORDER + COMPANION_READY_ORDER + GRAPH_PROOF_ORDER + SIDECAR_ORDER

BUCKET_ORDER = {
    "foundation": 0,
    "ready_for_stricter_companion_work": 1,
    "graph_proof_bridge": 2,
    "keep_as_sidecar": 3,
}

BUCKET_ACTION = {
    "foundation": "keep_as_foundation",
    "ready_for_stricter_companion_work": "tighten_for_stricter_companion",
    "graph_proof_bridge": "keep_as_graph_bridge",
    "keep_as_sidecar": "keep_as_sidecar",
}


def load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_optional_json(path: pathlib.Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return load_json(path)


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "pass", "passed", "yes", "sat"}
    return bool(value)


def registry_lookup() -> dict[str, dict[str, Any]]:
    registry = load_optional_json(REGISTRY_PATH)
    if not registry:
        return {}
    lookup: dict[str, dict[str, Any]] = {}
    for row in registry.get("rows", []):
        lego_id = row.get("lego_id")
        if isinstance(lego_id, str):
            lookup[lego_id] = row
    return lookup


def all_pass(result: dict[str, Any] | None) -> bool:
    if not result:
        return False
    summary = result.get("summary")
    if isinstance(summary, dict) and "all_pass" in summary:
        return truthy(summary["all_pass"])
    if "verdict" in result and isinstance(result["verdict"], dict):
        result_label = result["verdict"].get("result")
        if isinstance(result_label, str):
            return result_label.upper() == "PASS"
    if result.get("classification") == "canonical":
        return True
    positive = result.get("positive")
    if isinstance(positive, dict) and positive:
        return True
    return False


def load_sources() -> dict[str, dict[str, Any]]:
    return {
        "matrix": load_json(MATRIX_PATH),
        "overlay": load_json(OVERLAY_PATH),
        "audit": load_json(AUDIT_PATH),
        "supplement": load_json(SUPPLEMENT_PATH),
        "registry": load_optional_json(REGISTRY_PATH) or {"rows": []},
    }


def index_rows(source: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["id"] if "id" in row else row["row_id"] if "row_id" in row else row["lego_id"]: row for row in source["rows"]}


def index_registry_rows(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for row in registry.get("rows", []):
        lego_id = row.get("lego_id")
        if isinstance(lego_id, str):
            lookup[lego_id] = row
    return lookup


def pick_matrix_row(matrix_rows: dict[str, dict[str, Any]], row_id: str) -> dict[str, Any] | None:
    return matrix_rows.get(row_id)


def pick_overlay_row(overlay_rows: dict[str, dict[str, Any]], row_id: str) -> dict[str, Any] | None:
    return overlay_rows.get(row_id)


def pick_audit_row(audit_rows: dict[str, dict[str, Any]], row_id: str) -> dict[str, Any] | None:
    alias = AUDIT_ALIAS_ROW_IDS.get(row_id)
    if alias and alias in audit_rows:
        return audit_rows[alias]
    return audit_rows.get(row_id)


def pick_supplement_row(supplement_rows: dict[str, dict[str, Any]], row_id: str) -> dict[str, Any] | None:
    supplement_id = SUPPLEMENT_ROW_IDS.get(row_id)
    if supplement_id is None:
        return None
    return supplement_rows.get(supplement_id)


def extracted_metrics_from_matrix_row(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {}
    metrics = {}
    metrics.update(row.get("headline_metrics", {}) or {})
    metrics.update({f"result_{k}": v for k, v in (row.get("result_summary", {}) or {}).items() if k not in metrics})
    return metrics


def extracted_metrics_from_overlay_row(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {}
    return dict(row.get("key_metrics", {}) or {})


def extracted_metrics_from_audit_row(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {}
    metrics = dict(row.get("salient_metrics", {}) or {})
    if "all_pass" not in metrics and "all_pass" in row:
        metrics["all_pass"] = row["all_pass"]
    return metrics


def extracted_metrics_from_supplement_row(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {}
    return {
        "current_coverage": row.get("current_coverage"),
        "result_all_pass": row.get("result_all_pass"),
        "new_concept_normalized_in_actual_registry": row.get("new_concept_normalized_in_actual_registry"),
        "normalized_registry_concepts_count": len(row.get("normalized_registry_concepts", []) or []),
        "partial_registry_concepts_count": len(row.get("partial_registry_concepts", []) or []),
        "not_normalized_registry_concepts_count": len(row.get("not_normalized_registry_concepts", []) or []),
        "covered_registry_concepts_count": len(row.get("covered_registry_concepts", []) or []),
    }


def extract_spinor_hopf_metrics(result: dict[str, Any]) -> dict[str, Any]:
    positive = result.get("positive", {}) or {}
    boundary = result.get("boundary", {}) or {}
    clifford = positive.get("clifford_chirality_algebra", {}) or {}
    overlap = (positive.get("lr_spinor_overlap", {}) or {}).get("overlaps", {}) or {}
    z3_unsat = boundary.get("z3_unsat", {}) or {}
    gudhi = boundary.get("gudhi_combined_bundle", {}) or {}
    max_overlap = max((float(item.get("overlap_abs", 0.0)) for item in overlap.values()), default=0.0)
    return {
        "all_pass": bool(clifford.get("status") == "PASS" and z3_unsat.get("left_right_disjoint_fibers_proven")),
        "lr_cross_scalar": clifford.get("LR_cross_scalar"),
        "left_rotor_unit": clifford.get("left_rotor_unit"),
        "right_rotor_unit": clifford.get("right_rotor_unit"),
        "lr_rotors_differ": clifford.get("LR_rotors_differ"),
        "max_lr_overlap_abs": max_overlap,
        "left_right_disjoint_fibers_proven": z3_unsat.get("left_right_disjoint_fibers_proven"),
        "beta1_combined": gudhi.get("beta1_combined"),
        "beta0_combined": gudhi.get("beta0_combined"),
    }


def classify_row(row_id: str, matrix_row: dict[str, Any] | None, audit_row: dict[str, Any] | None, supplement_row: dict[str, Any] | None) -> tuple[str, int, str]:
    if row_id in FOUNDATION_ORDER:
        if row_id in {"nested_hopf_tori", "weyl_pauli_transport"}:
            return "foundation", BUCKET_ORDER["foundation"], BUCKET_ACTION["foundation"]
        if audit_row and audit_row.get("route") == "reusable base lego":
            return "foundation", BUCKET_ORDER["foundation"], BUCKET_ACTION["foundation"]
        return "foundation", BUCKET_ORDER["foundation"], BUCKET_ACTION["foundation"]

    if row_id in COMPANION_READY_ORDER:
        return (
            "ready_for_stricter_companion_work",
            BUCKET_ORDER["ready_for_stricter_companion_work"],
            BUCKET_ACTION["ready_for_stricter_companion_work"],
        )

    if row_id in GRAPH_PROOF_ORDER:
        return "graph_proof_bridge", BUCKET_ORDER["graph_proof_bridge"], BUCKET_ACTION["graph_proof_bridge"]

    return "keep_as_sidecar", BUCKET_ORDER["keep_as_sidecar"], BUCKET_ACTION["keep_as_sidecar"]


def row_priority_detail(row_id: str) -> int:
    if row_id in FOUNDATION_ORDER:
        return FOUNDATION_ORDER.index(row_id)
    if row_id in COMPANION_READY_ORDER:
        return 100 + COMPANION_READY_ORDER.index(row_id)
    if row_id in GRAPH_PROOF_ORDER:
        return 200 + GRAPH_PROOF_ORDER.index(row_id)
    if row_id in SIDECAR_ORDER:
        return 300 + SIDECAR_ORDER.index(row_id)
    return 999


def row_note(bucket: str, row_id: str, matrix_row: dict[str, Any] | None, audit_row: dict[str, Any] | None, supplement_row: dict[str, Any] | None) -> str:
    if bucket == "foundation":
        if row_id in {"nested_hopf_tori", "weyl_pauli_transport"}:
            return "Foundation geometry: reusable base lego already supports the composed stack and bridge rows."
        if row_id == "hopf_torus_lego":
            return "Legacy Hopf torus anchor is still a reusable base lego under the controller audit."
        if row_id == "weyl_spinor_hopf":
            return "Spinor geometry is a reusable base lego and should stay in the foundation lane."
        return "Reusable base geometry surface."

    if bucket == "ready_for_stricter_companion_work":
        if row_id == "weyl_hopf_pauli_composed_stack":
            return "Strong composed stack with a small remaining registry gap; best candidate for stricter companionization."
        if row_id == "weyl_geometry_carrier_array":
            return "Carrier array is informative and clean, but still needs a stricter companion surface."
        if row_id == "weyl_geometry_carrier_compare":
            return "Carrier comparison is clean and reusable, but should be tightened before companion promotion."
        return "Companion-ready geometry surface."

    if bucket == "graph_proof_bridge":
        if row_id == "weyl_geometry_graph_proof_alignment":
            return "Direct graph/proof bridge with solver-backed ordering and chirality checks."
        if row_id == "weyl_geometry_protocol_dag":
            return "Protocol DAG lego that validates layered geometry order and illegal back-edges."
        return "Graph/proof bridge surface."

    if row_id == "weyl_geometry_ladder_audit":
        return "Independent witness audit for the Weyl ambient rung; keep it as a sidecar diagnostic."
    return "Legacy geometry sidecar; keep separate from foundation and bridge rows."


def build_row(
    row_id: str,
    matrix_rows: dict[str, Any],
    overlay_rows: dict[str, Any],
    audit_rows: dict[str, Any],
    supplement_rows: dict[str, Any],
    registry_rows: dict[str, Any],
) -> dict[str, Any]:
    matrix_row = pick_matrix_row(matrix_rows, row_id)
    overlay_row = pick_overlay_row(overlay_rows, row_id)
    audit_row = pick_audit_row(audit_rows, row_id)
    supplement_row = pick_supplement_row(supplement_rows, row_id)
    registry_row = registry_rows.get("spinor_geometry") if row_id == "weyl_spinor_hopf" else None

    bucket, bucket_rank, action_label = classify_row(row_id, matrix_row, audit_row, supplement_row)

    source_surfaces = []
    if matrix_row:
        source_surfaces.append("matrix")
    if overlay_row:
        source_surfaces.append("overlay")
    if audit_row:
        source_surfaces.append("constraint_audit")
    if supplement_row:
        source_surfaces.append("registry_supplement")
    if registry_row and row_id == "weyl_spinor_hopf":
        source_surfaces.append("actual_registry")

    metrics = {}
    metrics.update(extracted_metrics_from_matrix_row(matrix_row))
    metrics.update({f"overlay_{k}": v for k, v in extracted_metrics_from_overlay_row(overlay_row).items() if f"overlay_{k}" not in metrics})
    metrics.update({f"audit_{k}": v for k, v in extracted_metrics_from_audit_row(audit_row).items() if f"audit_{k}" not in metrics})

    if row_id == "weyl_spinor_hopf" and not metrics:
        metrics = extract_spinor_hopf_metrics(load_json(REGISTRY_PATH.parent / "weyl_spinor_hopf_results.json"))

    registry_signal = {}
    if supplement_row:
        registry_signal = extracted_metrics_from_supplement_row(supplement_row)
        registry_signal["registry_lego_id"] = supplement_row.get("lego_id")
        registry_signal["registry_section"] = supplement_row.get("section")
    elif registry_row:
        registry_signal = {
            "registry_lego_id": registry_row.get("lego_id"),
            "current_coverage": registry_row.get("current_coverage"),
            "machine_current_coverage": registry_row.get("machine_current_coverage"),
            "best_existing_result": registry_row.get("best_existing_result"),
            "notes": registry_row.get("notes"),
        }

    result_file = None
    if matrix_row:
        result_file = matrix_row.get("result_file")
    elif audit_row:
        result_file = audit_row.get("result_file")

    result_pass = True
    if matrix_row:
        result_pass = bool(matrix_row.get("all_pass"))
    elif audit_row:
        result_pass = bool(audit_row.get("all_pass"))
    elif row_id == "weyl_spinor_hopf":
        result_pass = metrics.get("all_pass", False)

    label = None
    if matrix_row:
        label = matrix_row.get("label")
    else:
        label = row_id.replace("_", " ").title()

    return {
        "row_id": row_id,
        "label": label,
        "bucket": bucket,
        "priority_rank": bucket_rank * 100 + row_priority_detail(row_id),
        "action_label": action_label,
        "controller_route": matrix_row.get("controller_route") if matrix_row else None,
        "matrix_role": matrix_row.get("role") if matrix_row else None,
        "overlay_category": overlay_row.get("category") if overlay_row else None,
        "audit_route": audit_row.get("route") if audit_row else None,
        "registry_signal": registry_signal,
        "source_surfaces": source_surfaces,
        "result_file": str(result_file) if result_file else None,
        "all_pass": result_pass,
        "metrics": metrics,
        "note": row_note(bucket, row_id, matrix_row, audit_row, supplement_row),
    }


def main() -> None:
    sources = load_sources()
    matrix_rows = index_rows(sources["matrix"])
    overlay_rows = index_rows(sources["overlay"])
    audit_rows = index_rows(sources["audit"])
    supplement_rows = {row["lego_id"]: row for row in sources["supplement"]["rows"]}
    registry_rows = index_registry_rows(sources["registry"])

    rows = [build_row(row_id, matrix_rows, overlay_rows, audit_rows, supplement_rows, registry_rows) for row_id in ROW_ORDER]
    rows.sort(key=lambda row: (row["priority_rank"], row["row_id"]))

    foundation_rows = [row for row in rows if row["bucket"] == "foundation"]
    companion_rows = [row for row in rows if row["bucket"] == "ready_for_stricter_companion_work"]
    bridge_rows = [row for row in rows if row["bucket"] == "graph_proof_bridge"]
    sidecar_rows = [row for row in rows if row["bucket"] == "keep_as_sidecar"]

    out = {
        "name": "weyl_geometry_translation_targets",
        "classification": CLASSIFICATION,
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": all(row["all_pass"] for row in rows),
            "row_count": len(rows),
            "foundation_count": len(foundation_rows),
            "companion_ready_count": len(companion_rows),
            "graph_proof_bridge_count": len(bridge_rows),
            "sidecar_count": len(sidecar_rows),
            "top_foundation_row": foundation_rows[0]["row_id"] if foundation_rows else None,
            "top_companion_row": companion_rows[0]["row_id"] if companion_rows else None,
            "top_bridge_row": bridge_rows[0]["row_id"] if bridge_rows else None,
            "top_sidecar_row": sidecar_rows[0]["row_id"] if sidecar_rows else None,
            "matrix_row_count": len(matrix_rows),
            "overlay_row_count": len(overlay_rows),
            "audit_row_count": len(audit_rows),
            "supplement_row_count": len(supplement_rows),
            "registry_gap_concept_count": len(sources["supplement"]["summary"].get("existing_registry_gaps", [])),
            "registry_new_concept_count": len(sources["supplement"]["summary"].get("new_concepts_not_in_actual_registry", [])),
            "scope_note": (
                "Translation-target surface for the Weyl/Hopf lane. Foundation rows stay reusable, companion-ready rows are the next strict-companion targets, "
                "graph/proof rows stay bridge-only, and sidecars stay diagnostic or legacy."
            ),
        },
        "rows": rows,
    }

    out_path = RESULT_DIR / "weyl_geometry_translation_targets_results.json"
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
