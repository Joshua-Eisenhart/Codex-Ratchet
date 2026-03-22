"""
Direct regression smoke for A1 stripped fail-closed reporting completeness.

This guards the stripped builder's honest fail-closed posture: selected family
terms that are missing upstream and present terms that remain doctrine-blocked
must be reported explicitly without pretending a stripped owner node landed.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.a1_stripped_graph_builder import write_a1_stripped_graph


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_jargoned_graph(root: Path) -> None:
    payload = {
        "schema": "A1_JARGONED_GRAPH_v1",
        "nodes": {
            "A1_JARGONED::correlation_diversity_functional": {
                "id": "A1_JARGONED::correlation_diversity_functional",
                "name": "correlation_diversity_functional",
                "properties": {},
            },
            "A1_JARGONED::probe_induced_partition_boundary": {
                "id": "A1_JARGONED::probe_induced_partition_boundary",
                "name": "probe_induced_partition_boundary",
                "properties": {},
            },
        },
        "edges": [],
    }
    _write_json(root / "system_v4" / "a1_state" / "a1_jargoned_graph_v1.json", payload)


def _seed_family_slice(root: Path) -> None:
    payload = {
        "target_families": [
            "probe_induced_partition_boundary",
            "correlation_diversity_functional",
            "left_weyl_spinor_engine",
            "right_weyl_spinor_engine",
        ]
    }
    _write_json(
        root / "system_v3" / "a2_state" / "A2_TO_A1_FAMILY_SLICE__DUAL_STACKED_ENGINE_2026_03_17__v1.json",
        payload,
    )


def main() -> None:
    temp_root = Path(tempfile.mkdtemp(prefix="a1_stripped_fail_closed_reporting_"))
    try:
        _seed_jargoned_graph(temp_root)
        _seed_family_slice(temp_root)

        result = write_a1_stripped_graph(str(temp_root))
        json_path = Path(result["json_path"])
        audit_note_path = Path(result["audit_note_path"])

        report = json.loads(json_path.read_text(encoding="utf-8"))
        audit_text = audit_note_path.read_text(encoding="utf-8")
        diagnostics = report.get("selection_diagnostics", {})

        _assert(report.get("build_status") == "FAIL_CLOSED", "expected stripped builder to remain fail-closed")
        _assert(report.get("materialized") is False, "expected stripped builder to remain non-materialized")
        _assert(
            diagnostics.get("selected_terms_present_in_a1_jargoned")
            == ["probe_induced_partition_boundary", "correlation_diversity_functional"],
            "expected present selected terms to preserve family-slice order",
        )
        _assert(
            diagnostics.get("selected_terms_missing_from_a1_jargoned")
            == ["left_weyl_spinor_engine", "right_weyl_spinor_engine"],
            "expected missing selected terms to be reported explicitly",
        )
        _assert(
            diagnostics.get("materializable_terms") == [],
            "expected no materializable stripped terms under current doctrine",
        )
        _assert(
            diagnostics.get("present_terms_without_doctrine_plan") == [],
            "expected no present terms without a doctrine plan in this smoke",
        )

        blocked_by_term = {
            item["term"]: item for item in diagnostics.get("present_terms_blocked_by_doctrine", [])
        }
        _assert(
            set(blocked_by_term) == {
                "probe_induced_partition_boundary",
                "correlation_diversity_functional",
            },
            "expected both present selected terms to remain doctrine-blocked",
        )
        _assert(
            blocked_by_term["correlation_diversity_functional"].get("doctrine_status")
            == "PASSENGER_ONLY_WITHOUT_EXACT_STRIPPED_LANDING",
            "expected correlation term to expose its exact-landing blocker status",
        )
        _assert(
            blocked_by_term["probe_induced_partition_boundary"].get("doctrine_status")
            == "WITNESS_ONLY_DEFERRED",
            "expected probe term to expose its witness-only deferred status",
        )
        _assert(
            blocked_by_term["correlation_diversity_functional"].get("matching_jargoned_ids")
            == ["A1_JARGONED::correlation_diversity_functional"],
            "expected correlation diagnostics to preserve matching jargoned node ids",
        )
        _assert(
            blocked_by_term["probe_induced_partition_boundary"].get("matching_jargoned_ids")
            == ["A1_JARGONED::probe_induced_partition_boundary"],
            "expected probe diagnostics to preserve matching jargoned node ids",
        )
        _assert(
            any(
                ref.endswith(
                    "A1_STRIPPED_TERM_PLAN_ALIGNMENT__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.md"
                )
                for ref in blocked_by_term["correlation_diversity_functional"].get("supporting_audit_refs", [])
            ),
            "expected correlation diagnostics to expose the term-plan audit ref",
        )
        _assert(
            any(
                ref.endswith("A1_ENTROPY_EXECUTABLE_ENTRYPOINT__v1.md")
                for ref in blocked_by_term["probe_induced_partition_boundary"].get("supporting_source_refs", [])
            ),
            "expected probe diagnostics to expose a source-side doctrine ref",
        )
        _assert(
            "selected family terms missing from current A1_JARGONED: left_weyl_spinor_engine, right_weyl_spinor_engine"
            in report.get("blockers", []),
            "expected blockers to name missing upstream family terms",
        )
        _assert(
            "present selected terms remain doctrine-blocked: probe_induced_partition_boundary, correlation_diversity_functional"
            in report.get("blockers", []),
            "expected blockers to name doctrine-blocked present terms",
        )
        _assert(
            "## Fail-Closed Analysis" in audit_text,
            "expected audit note to render the fail-closed analysis section",
        )
        _assert(
            "left_weyl_spinor_engine" in audit_text and "right_weyl_spinor_engine" in audit_text,
            "expected audit note to name the missing selected family terms",
        )
        _assert(
            "supporting_audit_refs:" in audit_text and "supporting_source_refs:" in audit_text,
            "expected audit note to surface doctrine refs for blocked present terms",
        )
        print("A1 stripped graph fail-closed reporting smoke")
        print("PASS: stripped fail-closed report distinguishes missing upstream terms from doctrine-blocked present terms")
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    main()
