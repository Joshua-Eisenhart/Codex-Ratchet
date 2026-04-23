"""
Direct regression smoke for A2 low-control dependency reporting.

This guards the honest-reporting seam when the builder preserves a richer
existing owner surface: the written payload should keep the richer nodes/edges
while surfacing the thin attempted projection and the fact that A2_MID is only
an existence prerequisite, not a semantic source of preserved overlap carryover.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.a2_low_control_graph_builder import write_a2_low_control_graph


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _seed_prerequisites(root: Path) -> None:
    _write_json(
        root / "system_v4" / "a2_state" / "graphs" / "identity_registry_v1.json",
        {"schema": "IDENTITY_REGISTRY_v1", "nodes": {}, "edges": []},
    )
    _write_json(
        root / "system_v4" / "a2_state" / "graphs" / "a2_high_intake_graph_v1.json",
        {"schema": "A2_HIGH_INTAKE_GRAPH_v1", "nodes": {}, "edges": []},
    )
    _write_json(
        root / "system_v4" / "a2_state" / "graphs" / "a2_mid_refinement_graph_v1.json",
        {
            "schema": "A2_MID_REFINEMENT_GRAPH_v1",
            "materialized": True,
            "build_status": "MATERIALIZED",
            "preserve_diagnostics": {
                "preserved_only_edge_count": 7,
                "preserved_only_overlaps_hygiene": {
                    "preserved_only_overlap_edge_count": 5,
                },
            },
            "nodes": {},
            "edges": [],
        },
    )


def _seed_master_graph(root: Path) -> None:
    payload = {
        "schema": "V4_SYSTEM_GRAPH_v1",
        "nodes": {
            "A2_1::KERNEL::selected_a": {
                "id": "A2_1::KERNEL::selected_a",
                "node_type": "KERNEL_CONCEPT",
                "trust_zone": "A2_1_KERNEL",
                "layer": "A2_LOW_CONTROL",
                "name": "selected_a",
            },
            "A2_1::KERNEL::selected_b": {
                "id": "A2_1::KERNEL::selected_b",
                "node_type": "KERNEL_CONCEPT",
                "trust_zone": "A2_1_KERNEL",
                "layer": "A2_2_CANDIDATE",
                "name": "selected_b",
            },
            "A2_3::EXTRACTED::outside_c": {
                "id": "A2_3::EXTRACTED::outside_c",
                "node_type": "EXTRACTED_CONCEPT",
                "trust_zone": "A2_3",
                "layer": "A2_3_INTAKE",
                "name": "outside_c",
            },
            "A2_2::REFINED::outside_d": {
                "id": "A2_2::REFINED::outside_d",
                "node_type": "REFINED_CONCEPT",
                "trust_zone": "A2_2_CANDIDATE",
                "layer": "A2_MID_REFINEMENT",
                "name": "outside_d",
            },
            "A2_1::KERNEL::graveyard_e": {
                "id": "A2_1::KERNEL::graveyard_e",
                "node_type": "KERNEL_CONCEPT",
                "trust_zone": "A2_1_KERNEL",
                "layer": "A2_LOW_CONTROL",
                "status": "GRAVEYARD",
                "name": "graveyard_e",
            },
        },
        "edges": [
            {
                "source_id": "A2_1::KERNEL::selected_a",
                "target_id": "A2_1::KERNEL::selected_b",
                "relation": "STRUCTURALLY_RELATED",
                "attributes": {},
            },
            {
                "source_id": "A2_1::KERNEL::selected_a",
                "target_id": "A2_3::EXTRACTED::outside_c",
                "relation": "DEPENDS_ON",
                "attributes": {},
            },
            {
                "source_id": "A2_2::REFINED::outside_d",
                "target_id": "A2_1::KERNEL::selected_b",
                "relation": "RELATED_TO",
                "attributes": {},
            },
        ],
    }
    _write_json(root / "system_v4" / "a2_state" / "graphs" / "system_graph_a2_refinery.json", payload)


def _seed_existing_low_graph(root: Path) -> None:
    payload = {
        "schema": "A2_LOW_CONTROL_GRAPH_v1",
        "nodes": {
            "A2_1::KERNEL::selected_a": {
                "id": "A2_1::KERNEL::selected_a",
                "node_type": "KERNEL_CONCEPT",
                "trust_zone": "A2_1_KERNEL",
                "layer": "A2_LOW_CONTROL",
                "name": "selected_a",
            },
            "A2_1::KERNEL::selected_b": {
                "id": "A2_1::KERNEL::selected_b",
                "node_type": "KERNEL_CONCEPT",
                "trust_zone": "A2_1_KERNEL",
                "layer": "A2_2_CANDIDATE",
                "name": "selected_b",
            },
        },
        "edges": [
            {
                "source_id": "A2_1::KERNEL::selected_a",
                "target_id": "A2_1::KERNEL::selected_b",
                "relation": "STRUCTURALLY_RELATED",
                "attributes": {},
            },
            {
                "source_id": "A2_1::KERNEL::selected_a",
                "target_id": "A2_1::KERNEL::selected_b",
                "relation": "OVERLAPS",
                "attributes": {},
            },
        ],
    }
    _write_json(root / "system_v4" / "a2_state" / "graphs" / "a2_low_control_graph_v1.json", payload)


def main() -> None:
    temp_root = Path(tempfile.mkdtemp(prefix="a2_low_dependency_smoke_"))
    try:
        _seed_prerequisites(temp_root)
        _seed_master_graph(temp_root)
        _seed_existing_low_graph(temp_root)

        result = write_a2_low_control_graph(str(temp_root))
        json_path = Path(result["json_path"])
        audit_note_path = Path(result["audit_note_path"])

        report = json.loads(json_path.read_text(encoding="utf-8"))
        audit_text = audit_note_path.read_text(encoding="utf-8")
        projection = report.get("projection_diagnostics", {})
        preserve = report.get("preserve_diagnostics", {})
        upstream_mid = report.get("upstream_mid_dependency_diagnostics", {})

        _assert(
            report.get("build_status") == "MATERIALIZED",
            "expected preserved payload to expose materialized build status",
        )
        _assert(
            report.get("materialized") is True,
            "expected preserved payload to mark materialized true",
        )
        _assert(
            report.get("summary", {}).get("edge_count") == 2,
            "expected summary edge count to describe the preserved payload",
        )
        _assert(
            report.get("summary", {}).get("excluded_node_types", {}).get("KERNEL_CONCEPT") == 1,
            "expected graveyarded kernel concepts to stay excluded from low-control selection",
        )
        _assert(
            report.get("selection_contract", {}).get("upstream_dependency_mode", "").startswith("A2_MID is existence-gated only"),
            "expected selection contract to state the prerequisite-only A2_MID dependency mode",
        )
        _assert(
            projection.get("attempted_internal_edge_count") == 1,
            "expected one attempted internal edge",
        )
        _assert(
            projection.get("selected_boundary_edge_count") == 2,
            "expected two boundary-touching edges",
        )
        _assert(
            projection.get("internal_edge_retention_ratio") == 0.333333,
            "expected exact internal-retention ratio",
        )
        _assert(
            projection.get("selected_node_counts_by_trust_zone") == {"A2_1_KERNEL": 2},
            "expected trust-zone counts to stay explicit",
        )
        _assert(
            projection.get("selected_node_counts_by_status") == {"": 2},
            "expected status counts to reflect the seeded payload",
        )
        _assert(
            upstream_mid.get("a2_mid_dependency_mode") == "existence_prerequisite_only",
            "expected A2_MID dependency mode to stay explicit",
        )
        _assert(
            upstream_mid.get("a2_mid_build_status") == "MATERIALIZED",
            "expected the seeded A2_MID build status to be mirrored",
        )
        _assert(
            upstream_mid.get("a2_mid_materialized") is True,
            "expected the seeded A2_MID materialized flag to be mirrored",
        )
        _assert(
            upstream_mid.get("a2_mid_preserved_only_edge_count") == 7,
            "expected A2_MID preserved-only edge count to be mirrored",
        )
        _assert(
            upstream_mid.get("a2_mid_preserved_only_overlap_edge_count") == 5,
            "expected A2_MID preserved-only overlap edge count to be mirrored",
        )
        _assert(
            upstream_mid.get("a2_mid_overlap_edges_consumed_for_membership") == 0
            and upstream_mid.get("a2_mid_overlap_edges_consumed_for_edge_selection") == 0
            and upstream_mid.get("a2_mid_overlap_edges_consumed_for_runtime_policy") == 0,
            "expected A2_MID overlap consumption counters to stay at zero",
        )
        _assert(
            preserve.get("attempted_edge_count") == 1,
            "expected attempted edge count to stay explicit",
        )
        _assert(
            preserve.get("preserved_edge_count") == 2,
            "expected preserved edge count to stay explicit",
        )
        _assert(
            preserve.get("preserved_only_edge_count") == 1,
            "expected one preserved-only edge",
        )
        _assert(
            preserve.get("preserved_only_edge_ratio") == 0.5,
            "expected exact preserved-only edge ratio",
        )
        _assert(
            preserve.get("preserved_only_edge_counts_by_relation") == {"OVERLAPS": 1},
            "expected preserved-only relations to stay explicit",
        )
        overlap_hygiene = preserve.get("preserved_only_overlaps_hygiene", {})
        _assert(
            overlap_hygiene.get("preserved_only_overlap_edge_count") == 1,
            "expected one preserved-only overlap edge in the hygiene audit",
        )
        _assert(
            overlap_hygiene.get("preserved_only_overlap_ratio_within_preserved_only_edges") == 1.0,
            "expected overlap hygiene ratio to stay explicit",
        )
        _assert(
            overlap_hygiene.get("preserved_only_overlap_layer_pairs")
            == {"A2_LOW_CONTROL->A2_2_CANDIDATE": 1},
            "expected overlap hygiene to preserve layer-pair counts",
        )
        _assert(
            overlap_hygiene.get("preserved_only_overlap_trust_zone_pairs")
            == {"A2_1_KERNEL->A2_1_KERNEL": 1},
            "expected overlap hygiene to preserve trust-zone-pair counts",
        )
        _assert(
            overlap_hygiene.get("preserved_only_overlap_node_prefix_pairs")
            == {"A2_1::KERNEL->A2_1::KERNEL": 1},
            "expected overlap hygiene to preserve node-prefix-pair counts",
        )
        _assert(
            overlap_hygiene.get("blank_link_type_count") == 1
            and overlap_hygiene.get("zero_shared_count_count") == 1,
            "expected overlap hygiene to show empty-attribute overlap carryover",
        )
        overlap_treatment = preserve.get("preserved_only_overlaps_treatment", {})
        _assert(
            overlap_treatment.get("current_runtime_effect") == "none_observed_in_live_consumers",
            "expected overlap treatment to stay explicitly non-operative",
        )
        _assert(
            overlap_treatment.get("equal_runtime_weight_admissible_now") is False,
            "expected preserved-only overlaps to stay inadmissible as equal runtime weight",
        )
        _assert(
            overlap_treatment.get("recommended_future_handling")
            == "quarantine_or_downrank_before_equal_runtime_use",
            "expected overlap treatment to recommend quarantine/down-rank before equal use",
        )
        _assert(
            overlap_treatment.get("reason_flags")
            == [
                "preserved_only_carryover_not_in_current_master_graph",
                "overlap_dominant_carryover",
                "overlap_attribute_contract_mismatch",
                "no_direct_live_owner_edge_consumer_observed",
            ],
            "expected overlap treatment reasons to stay explicit",
        )
        _assert(
            audit_text.startswith("# NON_REGRESSION_PRESERVE"),
            "expected audit note to keep the preserve header when richer edges are retained",
        )
        _assert(
            "build_status: MATERIALIZED" in audit_text and "materialized: True" in audit_text,
            "expected audit note to surface the explicit materialized status",
        )
        _assert(
            "## Upstream A2_MID Dependency" in audit_text,
            "expected audit note to render the upstream A2_MID dependency section",
        )
        _assert(
            "a2_mid_dependency_mode: existence_prerequisite_only" in audit_text,
            "expected audit note to surface the prerequisite-only A2_MID dependency mode",
        )
        _assert(
            "a2_mid_overlap_edges_consumed_for_runtime_policy: 0" in audit_text,
            "expected audit note to surface the zero overlap-consumption claim",
        )
        _assert(
            "## Preserved-Only OVERLAPS Hygiene" in audit_text,
            "expected audit note to render the overlap hygiene section",
        )
        _assert(
            "## Preserved-Only OVERLAPS Treatment" in audit_text,
            "expected audit note to render the overlap treatment section",
        )
        print("A2 low control graph dependency smoke")
        print("PASS: preserved A2_LOW surface now reports prerequisite-only A2_MID dependence without semantic overlap carryover")
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    main()
