"""
Direct regression smoke for graph capability preserved-overlap treatment summary.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.graph_capability_auditor import (
    build_graph_capability_report,
    render_graph_capability_note,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_workspace(root: Path) -> None:
    graphs = root / "system_v4" / "a2_state" / "graphs"
    _write_json(
        graphs / "system_graph_a2_refinery.json",
        {"schema": "V4_SYSTEM_GRAPH_v1", "nodes": {}, "edges": []},
    )
    _write_json(
        graphs / "identity_registry_v1.json",
        {"schema": "IDENTITY_REGISTRY_v1", "nodes": {}, "edges": []},
    )
    _write_json(
        graphs / "a2_high_intake_graph_v1.json",
        {
            "schema": "A2_HIGH_INTAKE_GRAPH_v1",
            "build_status": "MATERIALIZED",
            "materialized": True,
            "summary": {"node_count": 1, "edge_count": 0},
            "nodes": {},
            "edges": [],
        },
    )
    _write_json(
        graphs / "a2_mid_refinement_graph_v1.json",
        {
            "schema": "A2_MID_REFINEMENT_GRAPH_v1",
            "build_status": "MATERIALIZED",
            "materialized": True,
            "preserve_diagnostics": {
                "preserved_only_edge_count": 7,
                "preserved_only_overlaps_hygiene": {
                    "preserved_only_overlap_edge_count": 5,
                },
                "preserved_only_overlaps_treatment": {
                    "current_runtime_effect": "none_observed_in_live_consumers",
                    "equal_runtime_weight_admissible_now": False,
                    "recommended_future_handling": "quarantine_or_downrank_before_equal_runtime_use",
                    "reason_flags": ["mid_reason"],
                },
            },
            "nodes": {},
            "edges": [],
        },
    )
    _write_json(
        graphs / "a2_low_control_graph_v1.json",
        {
            "schema": "A2_LOW_CONTROL_GRAPH_v1",
            "build_status": "MATERIALIZED",
            "materialized": True,
            "preserve_diagnostics": {
                "preserved_only_edge_count": 11,
                "preserved_only_overlaps_hygiene": {
                    "preserved_only_overlap_edge_count": 9,
                },
                "preserved_only_overlaps_treatment": {
                    "current_runtime_effect": "none_observed_in_live_consumers",
                    "equal_runtime_weight_admissible_now": False,
                    "recommended_future_handling": "quarantine_or_downrank_before_equal_runtime_use",
                    "reason_flags": ["low_reason"],
                },
            },
            "nodes": {},
            "edges": [],
        },
    )


def main() -> None:
    temp_root = Path(tempfile.mkdtemp(prefix="graph_capability_overlap_smoke_"))
    try:
        _seed_workspace(temp_root)
        report = build_graph_capability_report(str(temp_root))
        note = render_graph_capability_note(report)
        summary = report.get("preserved_overlap_treatment_summary", {})

        high = summary.get("A2_HIGH_INTAKE", {})
        mid = summary.get("A2_MID_REFINEMENT", {})
        low = summary.get("A2_LOW_CONTROL", {})

        _assert(
            high.get("treatment_state") == "no_preserve_diagnostics_present",
            "expected A2_HIGH to report no preserve diagnostics",
        )
        _assert(
            high.get("preserved_only_edge_count") == 0 and high.get("preserved_only_overlap_edge_count") == 0,
            "expected A2_HIGH preserved-only counts to default to zero",
        )
        _assert(
            mid.get("treatment_state") == "treatment_reported",
            "expected A2_MID to report preserved-overlap treatment",
        )
        _assert(
            mid.get("preserved_only_edge_count") == 7 and mid.get("preserved_only_overlap_edge_count") == 5,
            "expected A2_MID counts to be mirrored",
        )
        _assert(
            mid.get("equal_runtime_weight_admissible_now") is False,
            "expected A2_MID treatment admissibility to be mirrored",
        )
        _assert(
            low.get("treatment_state") == "treatment_reported",
            "expected A2_LOW to report preserved-overlap treatment",
        )
        _assert(
            low.get("preserved_only_edge_count") == 11 and low.get("preserved_only_overlap_edge_count") == 9,
            "expected A2_LOW counts to be mirrored",
        )
        _assert(
            "## Preserved Overlap Treatment" in note,
            "expected capability note to render the preserved overlap treatment section",
        )
        _assert(
            "A2_HIGH_INTAKE: state=no_preserve_diagnostics_present preserved_only_edges=0 preserved_only_overlaps=0" in note,
            "expected note to surface the A2_HIGH treatment summary",
        )
        _assert(
            "A2_MID_REFINEMENT: state=treatment_reported preserved_only_edges=7 preserved_only_overlaps=5" in note,
            "expected note to surface the A2_MID treatment summary",
        )
        _assert(
            "A2_LOW_CONTROL: state=treatment_reported preserved_only_edges=11 preserved_only_overlaps=9" in note,
            "expected note to surface the A2_LOW treatment summary",
        )
        print("Graph capability preserved-overlap summary smoke")
        print("PASS: graph capability audit now surfaces cross-layer preserved-overlap treatment state")
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    main()
