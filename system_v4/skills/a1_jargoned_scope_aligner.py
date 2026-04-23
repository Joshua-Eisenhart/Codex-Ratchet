"""
a1_jargoned_scope_aligner.py

Correction-first pass for A1_JARGONED when the queued family slice and the
current Rosetta packet inventory do not align. This pass only mints
packet-backed Rosetta terms that have live A2 anchors in the authoritative
master graph and rewrites the A1_JARGONED handoff to the selected family slice.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from system_v4.skills.graph_store import load_graph_json


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


MASTER_GRAPH = "system_v4/a2_state/graphs/system_graph_a2_refinery.json"
ROSETTA_V2 = "system_v4/a1_state/rosetta_v2.json"
QUEUE_REGISTRY = "system_v3/a2_state/A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.json"
SELECTED_FAMILY_SLICE = "system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__DUAL_STACKED_ENGINE_2026_03_17__v1.json"
JARGONED_HANDOFF = (
    "system_v4/a2_state/launch_bundles/nested_graph_build_a1_jargoned/"
    "NESTED_GRAPH_BUILD_WORKER_LAUNCH_HANDOFF__A1_JARGONED__2026_03_20__v1.json"
)
AUDIT_NOTE = "system_v4/a2_state/audit_logs/A1_JARGONED_SCOPE_ALIGNMENT_AUDIT__2026_03_20__v1.md"


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _resolve(root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (root / path)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        path.relative_to(REPO_ROOT / "system_v4" / "a2_state" / "graphs")
        return load_graph_json(REPO_ROOT, str(path.relative_to(REPO_ROOT)), default={})
    except ValueError:
        pass
    except FileNotFoundError:
        return {}
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _clean_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


TERM_MINT_PLAN = {
    "correlation_diversity_functional": {
        "packet_id": "RST_SENSE_DUAL_STACKED_ENGINE__CORRELATION_DIVERSITY_FUNCTIONAL__v1",
        "candidate_sense_id": "correlation_diversity_functional::dual_stacked_engine",
        "source_concept_id": "A2_2::REFINED::entropy_engine_campaign_state::dcf4faef21fd41a4",
        "support_refs": [
            "A2_3::SOURCE_MAP_PASS::dual_stacked_engine_grounding::1cfb82291e65f487",
            "A2_3::SOURCE_MAP_PASS::a1_state_a1_rosetta_batch__correlation_diversity_::6cc1dfed433d9c86",
            "A2_3::SOURCE_MAP_PASS::a1_state_a1_entropy_diversity_structure_lift_pack::0ae3760cd2e0173e",
        ],
        "object_class": "SENSE_CANDIDATE",
        "status": "PARKED",
        "confidence_mode": "structural",
        "source_context": (
            "Dual-stacked-engine correction lane: witness for whether correlation is "
            "spread across multiple pair relations rather than collapsing into one "
            "narrow pattern; grounded to Axis-0 allostatic diversity increase under "
            "left/right loop inequality, but still passenger-only and not current "
            "executable head."
        ),
        "routing_reason": "dual_stacked_engine_scope_alignment",
        "source_tags": ["ENGINE", "ENTROPY", "CORRELATION", "DUAL_STACKED_ENGINE"],
        "mintable": True,
        "why": "live refined anchor plus explicit rosetta restatement and diversity-lift doctrine",
    },
    "probe_induced_partition_boundary": {
        "packet_id": "RST_SENSE_DUAL_STACKED_ENGINE__PROBE_INDUCED_PARTITION_BOUNDARY__v1",
        "candidate_sense_id": "probe_induced_partition_boundary::dual_stacked_engine",
        "source_concept_id": "A2_3::SOURCE_MAP_PASS::dual_stacked_engine_grounding::1cfb82291e65f487",
        "support_refs": [
            "A2_3::SOURCE_MAP_PASS::a2_to_a1_impact_note__dual_stacked_engine_topology::98ce696098904345",
            "A2_3::SOURCE_MAP_PASS::a2_to_a1_family_slice__dual_stacked_engine_2026_03::f842e59304947cfe",
        ],
        "object_class": "SENSE_CANDIDATE",
        "status": "PARKED",
        "confidence_mode": "structural",
        "source_context": (
            "Stage-1 DUAL_STACKED_ENGINE grounding: unavoidable structural split "
            "(C04_IRREDUCIBLE_DISTINCTIONS) in refinement cost when an admissible "
            "probe acts; witness-side target only, not current executable head."
        ),
        "routing_reason": "dual_stacked_engine_scope_alignment",
        "source_tags": ["ENGINE", "BOUNDARY", "WITNESS", "DUAL_STACKED_ENGINE"],
        "mintable": True,
        "why": "explicit grounded read exists, but doctrine still keeps it witness-side only",
    },
    "left_weyl_spinor_engine": {
        "mintable": False,
        "why": "no exact packet-backed live A2 anchor for the term; only broader dual_szilard/impact-note context exists",
    },
    "right_weyl_spinor_engine": {
        "mintable": False,
        "why": "no exact packet-backed live A2 anchor for the term; only broader dual_szilard/impact-note context exists",
    },
}


def _upsert_packet(packets: dict[str, Any], packet_payload: dict[str, Any]) -> str:
    packet_id = packet_payload["packet_id"]
    packets[packet_id] = packet_payload
    return packet_id


def run_a1_jargoned_scope_alignment(workspace_root: str) -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    master = _load_json(_resolve(root, MASTER_GRAPH))
    rosetta_path = _resolve(root, ROSETTA_V2)
    rosetta = _load_json(rosetta_path)
    queue_registry = _load_json(_resolve(root, QUEUE_REGISTRY))
    family_slice_path = _resolve(root, SELECTED_FAMILY_SLICE)
    family_slice = _load_json(family_slice_path)
    handoff_path = _resolve(root, JARGONED_HANDOFF)
    handoff = _load_json(handoff_path)

    packets = rosetta.setdefault("packets", {})
    master_nodes = master.get("nodes", {})

    minted_terms: list[str] = []
    blocked_terms: list[dict[str, str]] = []

    for term, plan in TERM_MINT_PLAN.items():
        if not plan.get("mintable", False):
            blocked_terms.append({"term": term, "reason": plan["why"]})
            continue
        source_concept_id = plan["source_concept_id"]
        source_node = master_nodes.get(source_concept_id)
        if not source_node:
            blocked_terms.append({"term": term, "reason": f"missing source_concept_id {source_concept_id}"})
            continue
        payload = {
            "packet_id": plan["packet_id"],
            "source_term": term,
            "source_context": plan["source_context"],
            "object_class": plan["object_class"],
            "candidate_sense_id": plan["candidate_sense_id"],
            "source_concept_id": source_concept_id,
            "source_node_type": _clean_str(source_node.get("node_type", "")),
            "source_tags": list(plan.get("source_tags", [])),
            "source_batch_id": "",
            "confidence_mode": plan["confidence_mode"],
            "kernel_targets": [],
            "dependency_targets": [],
            "orthogonality_claims": [],
            "invariant_claims": [],
            "probe_suggestions": [],
            "conflict_set": [],
            "status": plan["status"],
            "legacy_imported": False,
            "routing_reason": plan["routing_reason"],
            "updated_utc": _utc_iso(),
            "support_refs": list(plan.get("support_refs", [])),
        }
        _upsert_packet(packets, payload)
        minted_terms.append(term)

    rosetta_path.write_text(json.dumps(rosetta, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    handoff["queue_status"] = "READY_FROM_SCOPE_ALIGNED_FUEL"
    handoff["source_artifacts"] = [
        str(_resolve(root, ROSETTA_V2)),
        str(_resolve(root, "system_v4/a1_state/A1_GRAPH_PROJECTION.json")),
        str(_resolve(root, QUEUE_REGISTRY)),
        str(family_slice_path),
    ]
    handoff["scope_alignment_status"] = "PARTIAL_PACKET_BACKED_ALIGNMENT"
    handoff["aligned_scope_terms"] = minted_terms
    handoff["blocked_scope_terms"] = blocked_terms
    handoff["prompt_to_send"] = (
        "Run one bounded A1_JARGONED nested-graph build pass using the aligned "
        "DUAL_STACKED_ENGINE family scope. Materialize only packet-backed Rosetta "
        "nodes now available and preserve blocked Weyl-engine labels as explicit "
        "scope residue."
    )
    handoff_path.write_text(json.dumps(handoff, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    report = {
        "schema": "A1_JARGONED_SCOPE_ALIGNMENT_AUDIT_v1",
        "generated_utc": _utc_iso(),
        "family_slice_path": str(family_slice_path),
        "queue_selected_family_slice": _clean_str(queue_registry.get("selected_family_slice_json", "")),
        "family_terms": list(family_slice.get("target_families", [])),
        "minted_terms": minted_terms,
        "blocked_terms": blocked_terms,
        "result": "PARTIAL_ALIGNMENT" if minted_terms else "FAIL_CLOSED",
        "handoff_path": str(handoff_path),
        "rosetta_path": str(rosetta_path),
    }

    audit_path = _resolve(root, AUDIT_NOTE)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# A1_JARGONED_SCOPE_ALIGNMENT_AUDIT__2026_03_20__v1",
        "",
        f"generated_utc: {report['generated_utc']}",
        f"result: {report['result']}",
        f"family_slice_path: {report['family_slice_path']}",
        f"queue_selected_family_slice: {report['queue_selected_family_slice']}",
        "",
        "## Minted Terms",
    ]
    if minted_terms:
        for term in minted_terms:
            plan = TERM_MINT_PLAN[term]
            lines.append(f"- {term}: source_concept_id={plan['source_concept_id']}")
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Blocked Terms",
    ])
    if blocked_terms:
        for item in blocked_terms:
            lines.append(f"- {item['term']}: {item['reason']}")
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Non-Claims",
        "- This pass does not mint left/right Weyl engine labels without exact live packet-backed anchors.",
        "- This pass does not claim executable landing for any minted term.",
        "- This pass only aligns A1_JARGONED scope; it does not build A1_STRIPPED or A1_CARTRIDGE.",
        "",
    ])
    audit_path.write_text("\n".join(lines), encoding="utf-8")
    report["audit_note_path"] = str(audit_path)
    return report


if __name__ == "__main__":
    result = run_a1_jargoned_scope_alignment(str(REPO_ROOT))
    print(json.dumps(result, indent=2, sort_keys=True))
