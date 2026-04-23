"""Smoke test for edge payload schema probe."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.edge_payload_schema_probe import (
    build_edge_payload_schema_probe_report,
    run_edge_payload_schema_probe,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _write_json(
            root / "system_v4/a2_state/graphs/a2_low_control_graph_v1.json",
            {
                "edges": [
                    {
                        "relation": "STRUCTURALLY_RELATED",
                        "source_id": "KERNEL_CONCEPT::A",
                        "target_id": "KERNEL_CONCEPT::B",
                        "attributes": {
                            "shared_components": 2,
                            "link_type": "structural",
                            "nested_layer": "Topology4",
                            "reasoning": "synthetic",
                        },
                    }
                ]
            },
        )
        _write_json(
            root / "system_v4/a2_state/audit_logs/EDGE_PAYLOAD_SCHEMA_AUDIT__CURRENT__v1.json",
            {
                "status": "ok",
                "schema_rows": [
                    {
                        "relation": "STRUCTURALLY_RELATED",
                        "required_carriers": ["relation", "source_id", "target_id"],
                        "optional_scalar_carriers": ["shared_components"],
                        "optional_string_carriers": ["link_type", "nested_layer", "reasoning"],
                    }
                ],
            },
        )
        _write_json(
            root / "system_v4/a2_state/audit_logs/EDGE_PAYLOAD_SCHEMA_PACKET__CURRENT__v1.json",
            {
                "status": "ok",
                "admitted_relations": ["STRUCTURALLY_RELATED"],
                "deferred_ga_fields": [
                    "entropy_state",
                    "correlation_entropy",
                    "orientation_basis",
                    "clifford_grade",
                    "obstruction_score",
                ],
            },
        )

        report, packet = build_edge_payload_schema_probe_report(root, {"relation": "STRUCTURALLY_RELATED"})
        _assert(report["status"] == "ok", f"unexpected probe status: {report['status']}")
        _assert(report["payload_preview_count"] == 1, "expected one payload preview")
        preview = report["payload_previews"][0]
        _assert(preview["carrier_snapshot"]["scalar_carriers"] == {"shared_components": 2}, "unexpected scalar snapshot")
        _assert(preview["deferred_ga_slots"]["entropy_state"] is None, "deferred slots should remain empty")
        _assert(packet["allow_sidecar_payload_preview_only"] is True, "probe must remain sidecar-only")

    live_report, live_packet = build_edge_payload_schema_probe_report(REPO_ROOT)
    _assert(live_report["status"] == "ok", f"unexpected live probe status: {live_report['status']}")
    _assert(live_report["relation"] == "STRUCTURALLY_RELATED", "unexpected live default relation")
    _assert(live_report["payload_preview_count"] >= 1, "expected at least one live payload preview")
    _assert(live_packet["allow_canonical_graph_write"] is False, "live probe must not allow canonical writes")

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        _write_json(
            root / "system_v4/a2_state/graphs/a2_low_control_graph_v1.json",
            {
                "edges": [
                    {
                        "relation": "STRUCTURALLY_RELATED",
                        "source_id": "KERNEL_CONCEPT::A",
                        "target_id": "KERNEL_CONCEPT::B",
                        "attributes": {
                            "shared_components": 2,
                            "link_type": "structural",
                            "nested_layer": "Topology4",
                            "reasoning": "synthetic",
                        },
                    }
                ]
            },
        )
        _write_json(
            root / "system_v4/a2_state/audit_logs/EDGE_PAYLOAD_SCHEMA_AUDIT__CURRENT__v1.json",
            {
                "status": "ok",
                "schema_rows": [
                    {
                        "relation": "STRUCTURALLY_RELATED",
                        "required_carriers": ["relation", "source_id", "target_id"],
                        "optional_scalar_carriers": ["shared_components"],
                        "optional_string_carriers": ["link_type", "nested_layer", "reasoning"],
                    }
                ],
            },
        )
        _write_json(
            root / "system_v4/a2_state/audit_logs/EDGE_PAYLOAD_SCHEMA_PACKET__CURRENT__v1.json",
            {
                "status": "ok",
                "admitted_relations": ["STRUCTURALLY_RELATED"],
                "deferred_ga_fields": [
                    "entropy_state",
                    "correlation_entropy",
                    "orientation_basis",
                    "clifford_grade",
                    "obstruction_score",
                ],
            },
        )

        json_path = root / "probe.json"
        md_path = root / "probe.md"
        packet_path = root / "probe.packet.json"
        emitted = run_edge_payload_schema_probe(
            {
                "repo_root": str(root),
                "relation": "STRUCTURALLY_RELATED",
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "probe json was not written")
        _assert(md_path.exists(), "probe markdown was not written")
        _assert(packet_path.exists(), "probe packet was not written")
        _assert(emitted["recommended_next_step"] == "hold_probe_as_sidecar_only", "unexpected probe next step")

    print("PASS: edge payload schema probe smoke")


if __name__ == "__main__":
    main()
