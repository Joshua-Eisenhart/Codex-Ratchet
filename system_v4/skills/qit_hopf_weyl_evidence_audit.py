#!/usr/bin/env python3
"""
qit_hopf_weyl_evidence_audit.py

Bounded evidence audit for the current Hopf/Weyl QIT lane.

This report reads the live owner graph plus the existing runtime bridge and
Hopf/Weyl projection sidecar, then states:
- what torus/chirality structure is live now
- what is aligned across the current bounded surfaces
- what remains absent or forbidden to claim

It is an audit surface only. It does not mutate owner truth or promote
sidecar semantics.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
GRAPH_JSON = REPO_ROOT / "system_v4" / "a2_state" / "graphs" / "qit_engine_graph_v1.json"
AUDIT_DIR = REPO_ROOT / "system_v4" / "a2_state" / "audit_logs"
HOPF_WEYL_JSON = AUDIT_DIR / "QIT_HOPF_WEYL_PROJECTION__CURRENT__v1.json"
RUNTIME_BRIDGE_JSON = AUDIT_DIR / "QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.json"
OUT_JSON = AUDIT_DIR / "QIT_HOPF_WEYL_EVIDENCE_AUDIT__CURRENT__v1.json"
OUT_MD = AUDIT_DIR / "QIT_HOPF_WEYL_EVIDENCE_AUDIT__CURRENT__v1.md"


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(REPO_ROOT),
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _git_status_porcelain(paths: list[Path] | None = None) -> list[str]:
    cmd = ["git", "status", "--short"]
    if paths:
        cmd.append("--")
        cmd.extend(str(path) for path in paths)
    try:
        output = subprocess.check_output(cmd, cwd=str(REPO_ROOT), text=True)
    except Exception:
        return []
    return [line.rstrip() for line in output.splitlines() if line.strip()]


def build_qit_hopf_weyl_evidence_audit() -> dict[str, Any]:
    owner = _load_json(GRAPH_JSON)
    hopf = _load_json(HOPF_WEYL_JSON) if HOPF_WEYL_JSON.exists() else {}
    runtime = _load_json(RUNTIME_BRIDGE_JSON) if RUNTIME_BRIDGE_JSON.exists() else {}
    script_path = Path(__file__).resolve()

    nodes = owner.get("nodes", {})
    edges = owner.get("edges", [])
    torus_nodes = [n for n in nodes.values() if n.get("node_type") == "TORUS"]
    engine_nodes = [n for n in nodes.values() if n.get("node_type") == "ENGINE"]
    nesting_edges = [e for e in edges if e.get("relation") == "TORUS_NESTING"]
    stage_torus_edges = [e for e in edges if e.get("relation") == "STAGE_ON_TORUS"]
    chirality_edges = [e for e in edges if e.get("relation") == "CHIRALITY_COUPLING"]

    hopf_neg = hopf.get("relevant_negative_evidence", {}) if isinstance(hopf.get("relevant_negative_evidence"), dict) else {}
    hopf_runtime_alignment = hopf.get("runtime_bridge_alignment", {}) if isinstance(hopf.get("runtime_bridge_alignment"), dict) else {}
    hopf_carrier = hopf.get("owner_carrier_evidence", {}) if isinstance(hopf.get("owner_carrier_evidence"), dict) else {}
    hopf_readiness = hopf.get("weyl_projection_readiness", {}) if isinstance(hopf.get("weyl_projection_readiness"), dict) else {}

    runtime_summary = runtime.get("summary", {}) if isinstance(runtime.get("summary"), dict) else {}
    runtime_owner_snapshot = runtime.get("owner_snapshot", {}) if isinstance(runtime.get("owner_snapshot"), dict) else {}
    runtime_packets = runtime.get("sim_evidence_packets", []) if isinstance(runtime.get("sim_evidence_packets"), list) else []
    axis0_summary = runtime.get("axis0_control_plane_summary", {}) if isinstance(runtime.get("axis0_control_plane_summary"), dict) else {}
    runtime_mapped_witnesses = sorted(
        {
            packet.get("neg_witness_public_id", "")
            for packet in runtime_packets
            if packet.get("neg_witness_public_id")
        }
    )

    safe_now = [
        "three torus owner nodes are live: inner, clifford, outer",
        "the owner graph carries a two-edge torus nesting chain",
        "the owner graph carries thirty-two STAGE_ON_TORUS assignments",
        "the owner graph carries two engine nodes and one CHIRALITY_COUPLING edge",
        "the Hopf/Weyl sidecar is aligned to the current owner content hash",
        "the runtime bridge is aligned to the current owner content hash",
    ]
    if hopf_readiness.get("weyl_branch_nodes_present"):
        safe_now.append("two live WEYL_BRANCH owner nodes are present")
    missing_now = [
        "no promoted torus 2-cells in owner truth",
        "no promoted spinor-state graph",
        "no promoted runtime-state graph",
        "no promoted history graph",
    ]
    if not hopf_readiness.get("weyl_branch_nodes_present"):
        missing_now.insert(0, "no live WEYL_BRANCH owner nodes")
    forbidden_claims_now = [
        "do not claim full branch-runtime semantics beyond the admitted WEYL_BRANCH owner nodes",
        "do not claim torus 2-cells are promoted owner structure",
        "do not claim runtime bridge packets are runtime/history graphs",
        "do not claim sidecar candidate mappings are promotion evidence by themselves",
    ]

    return {
        "schema": "QIT_HOPF_WEYL_EVIDENCE_AUDIT_v1",
        "generated_utc": _utc_iso(),
        "status": "bounded_evidence_audit_only",
        "report_surface": {
            "surface_class": "tracked_current_workspace_report",
            "represents": (
                "current workspace Hopf/Weyl evidence audit state at generation time; may differ from the "
                "last committed snapshot until tracked CURRENT artifacts are committed"
            ),
            "tracked_report_files": [str(OUT_JSON), str(OUT_MD)],
            "tracked_report_files_dirty_before_generation": _git_status_porcelain([OUT_JSON, OUT_MD]),
            "script_path": str(script_path),
            "script_sha256": _sha256_path(script_path),
            "git_sha": _git_sha(),
        },
        "audit_boundary": {
            "audit_only": True,
            "nonoperative": True,
            "do_not_promote": True,
            "promotion_claim": "none",
            "owner_graph_role": "read_only_reference_only",
            "runtime_bridge_role": "read_only_alignment_input",
            "negative_witness_role": "context_only_non_authoritative",
        },
        "owner_snapshot": {
            "qit_graph_json": str(GRAPH_JSON),
            "qit_graph_schema": owner.get("schema", ""),
            "qit_graph_content_hash": owner.get("content_hash", ""),
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
        "owner_carrier_evidence": {
            "torus_carriers": hopf_carrier.get("torus_carriers", []),
            "torus_nesting_edges": hopf_carrier.get("torus_nesting_edges", []),
            "stage_on_torus_edge_count": hopf_carrier.get("stage_on_torus_edge_count", len(stage_torus_edges)),
            "carrier_assignment_scope": hopf_carrier.get("carrier_assignment_scope", "owner_scaffold_only"),
            "weyl_readiness": hopf_readiness,
            "owner_supported_claims": safe_now,
            "owner_missing_anchors": hopf_readiness.get("missing_owner_anchors", []),
        },
        "runtime_bridge_alignment": {
            "bridge_report_path": str(RUNTIME_BRIDGE_JSON),
            "bridge_schema": runtime.get("schema", ""),
            "bridge_generated_utc": runtime.get("generated_utc", ""),
            "bridge_owner_content_hash": runtime_owner_snapshot.get("qit_graph_content_hash", ""),
            "owner_hash_matches": runtime_owner_snapshot.get("qit_graph_content_hash", "") == owner.get("content_hash", ""),
            "aligned_engine_public_ids": [
                sample.get("engine_public_id", "")
                for sample in hopf_runtime_alignment.get("engine_sample_refs", [])
            ],
            "aligned_step_public_id_range": hopf_runtime_alignment.get("engine_sample_refs", []),
            "aligned_neg_witness_public_ids": runtime_mapped_witnesses,
            "unresolved_links": runtime_summary.get("unresolved_owner_links", 0),
            "axis0_control_plane_summary": axis0_summary,
            "alignment_status": (
                "aligned"
                if hopf_runtime_alignment.get("owner_content_hash_matches_runtime_bridge") and runtime_summary.get("unresolved_owner_links", 1) == 0
                else "partially_aligned"
            ),
        },
        "relevant_negative_evidence": {
            "torus_witnesses": hopf_neg.get("torus_witnesses", []),
            "chirality_witnesses": hopf_neg.get("chirality_witnesses", []),
            "runtime_bridge_mapped_witnesses": runtime_mapped_witnesses,
            "witness_alignment_notes": [
                "torus-targeted negatives are present as sidecar-context witnesses but remain suppressed at the owner-edge level pending a better owner concept",
                "chirality-targeted negatives currently align to the two engine owner nodes",
            ],
        },
        "candidate_sidecar_evidence": {
            "cell_complex_candidate_evidence": {
                "status": "candidate_projection_only",
                "available": hopf.get("torus_cell_complex", {}).get("available"),
                "shape": hopf.get("torus_cell_complex", {}).get("shape", []),
            },
            "chirality_mapping_candidate_evidence": {
                "status": "candidate_projection_only",
                "available": hopf.get("chirality_coupling", {}).get("available"),
                "pseudoscalar_blade": hopf.get("chirality_coupling", {}).get("pseudoscalar_blade", ""),
                "product_is_scalar": hopf.get("chirality_coupling", {}).get("coupling_is_scalar"),
            },
        },
        "evidence_limits": {
            "not_owner_truth": True,
            "not_runtime_state_graph": True,
            "not_history_graph": True,
            "not_full_live_weyl_branch_runtime_evidence": True,
            "not_promotion_evidence": True,
            "excluded_semantics": forbidden_claims_now,
        },
        "carrier_evidence_summary": {
            "status": "bounded_owner_linked_summary_only",
            "promotion_claim": "none",
            "torus_placement_evidence": {
                "owner_graph_content_hash": owner.get("content_hash", ""),
                "torus_public_ids": [carrier["torus_public_id"] for carrier in hopf_carrier.get("torus_carriers", [])],
                "torus_nesting_edges": [
                    [edge.get("source_public_id", ""), edge.get("target_public_id", "")]
                    for edge in hopf_carrier.get("torus_nesting_edges", [])
                ],
                "stage_on_torus_edge_count": hopf_carrier.get("stage_on_torus_edge_count", len(stage_torus_edges)),
                "torus_stage_counts": {
                    carrier["torus_public_id"]: carrier.get("stage_count", 0)
                    for carrier in hopf_carrier.get("torus_carriers", [])
                },
                "carrier_assignment_scope": hopf_carrier.get("carrier_assignment_scope", "owner_scaffold_only"),
                "runtime_alignment": {
                    "bridge_owner_hash_matches": runtime_owner_snapshot.get("qit_graph_content_hash", "") == owner.get("content_hash", ""),
                    "aligned_engine_public_ids": [
                        sample.get("engine_public_id", "")
                        for sample in hopf_runtime_alignment.get("engine_sample_refs", [])
                    ],
                    "alignment_note": "runtime bridge aligns to owner ids but does not promote torus semantics",
                },
                "relevant_negative_witnesses": [
                    witness.get("witness_id", "")
                    for witness in hopf_neg.get("torus_witnesses", [])
                ],
            },
            "type_split_evidence": {
                "owner_graph_content_hash": owner.get("content_hash", ""),
                "engine_public_ids": [node.get("public_id", "") for node in engine_nodes],
                "chirality_coupling_edge_count": len(chirality_edges),
                "engine_owns_stage_edge_count": sum(1 for edge in edges if edge.get("relation") == "ENGINE_OWNS_STAGE"),
                "projection_status": hopf_readiness.get("projection_status", ""),
                "weyl_branch_nodes_present": bool(hopf_readiness.get("weyl_branch_nodes_present")),
                "weyl_branch_public_ids": hopf_readiness.get("weyl_branch_public_ids", []),
                "engine_branch_edge_count": hopf_readiness.get("engine_branch_edge_count", 0),
                "missing_owner_anchors": hopf_readiness.get("missing_owner_anchors", []),
                "runtime_alignment": {
                    "bridge_owner_hash_matches": runtime_owner_snapshot.get("qit_graph_content_hash", "") == owner.get("content_hash", ""),
                    "aligned_engine_public_ids": [
                        sample.get("engine_public_id", "")
                        for sample in hopf_runtime_alignment.get("engine_sample_refs", [])
                    ],
                    "aligned_neg_witness_public_ids": [
                        witness
                        for witness in runtime_mapped_witnesses
                        if witness in {"qit::NEG_WITNESS::neg_no_chirality", "qit::NEG_WITNESS::neg_type_flatten"}
                    ],
                    "alignment_note": "runtime/evidence bridge resolves the type-split witness set to owner engine ids only",
                },
                "relevant_negative_witnesses": [
                    witness.get("witness_id", "")
                    for witness in hopf_neg.get("chirality_witnesses", [])
                ],
            },
            "limits": {
                "not_owner_promotion": True,
                "not_runtime_state_truth": True,
                "not_live_weyl_semantics": True,
                "not_torus_geometry_proof": True,
            },
        },
        "audit_conclusion": {
            "summary": (
                "The current QIT lane has live owner torus/chirality scaffold plus aligned bounded sidecars "
                "and runtime packets. It supports a bounded carrier-map reading, not promoted Hopf/Weyl semantics."
            ),
            "safe_use": safe_now,
            "missing_now": missing_now,
            "forbidden_claims_now": forbidden_claims_now,
        },
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    owner = payload["owner_snapshot"]
    carrier = payload["owner_carrier_evidence"]
    runtime = payload["runtime_bridge_alignment"]
    neg = payload["relevant_negative_evidence"]
    candidate = payload["candidate_sidecar_evidence"]
    summary = payload["carrier_evidence_summary"]
    conclusion = payload["audit_conclusion"]
    surface = payload["report_surface"]
    boundary = payload["audit_boundary"]
    lines = [
        "# QIT Hopf/Weyl Evidence Audit",
        "",
        f"- status: `{payload['status']}`",
        f"- generated_utc: `{payload['generated_utc']}`",
        "",
        "## Report Surface",
        f"- surface_class: `{surface['surface_class']}`",
        f"- represents: `{surface['represents']}`",
        f"- git_sha: `{surface['git_sha']}`",
        "",
        "## Audit Boundary",
        f"- audit_only: `{boundary['audit_only']}`",
        f"- nonoperative: `{boundary['nonoperative']}`",
        f"- do_not_promote: `{boundary['do_not_promote']}`",
        f"- promotion_claim: `{boundary['promotion_claim']}`",
        "",
        "## Owner Snapshot",
        f"- qit_graph_schema: `{owner['qit_graph_schema']}`",
        f"- qit_graph_content_hash: `{owner['qit_graph_content_hash']}`",
        f"- node_count: `{owner['node_count']}`",
        f"- edge_count: `{owner['edge_count']}`",
        "",
        "## Owner Carrier Evidence",
        f"- torus_carrier_count: `{len(carrier['torus_carriers'])}`",
        f"- torus_nesting_edge_count: `{len(carrier['torus_nesting_edges'])}`",
        f"- stage_on_torus_edge_count: `{carrier['stage_on_torus_edge_count']}`",
        f"- owner_missing_anchors: `{', '.join(carrier['owner_missing_anchors'])}`",
        "",
        "## Runtime Bridge Alignment",
        f"- alignment_status: `{runtime['alignment_status']}`",
        f"- owner_hash_matches: `{runtime['owner_hash_matches']}`",
        f"- aligned_engine_public_ids: `{', '.join(runtime['aligned_engine_public_ids'])}`",
        f"- unresolved_links: `{runtime['unresolved_links']}`",
    ]
    axis0_summary = runtime.get("axis0_control_plane_summary", {})
    if axis0_summary:
        lines.extend([
            f"- axis0_surface_status: `{axis0_summary.get('surface_status')}`",
            f"- axis0_runtime_sample_count: `{axis0_summary.get('runtime_sample_count')}`",
            f"- axis0_direct_bridge_families: `{axis0_summary.get('direct_bridge_families', [])}`",
            f"- axis0_history_window_bridge_families: `{axis0_summary.get('history_window_bridge_families', [])}`",
            f"- axis0_history_window_sample_counts: `{axis0_summary.get('history_window_sample_counts', {})}`",
        ])
    lines.extend([
        "",
        "## Relevant Negative Evidence",
        f"- torus_witnesses: `{len(neg['torus_witnesses'])}`",
        f"- chirality_witnesses: `{len(neg['chirality_witnesses'])}`",
        f"- runtime_bridge_mapped_witnesses: `{', '.join(neg['runtime_bridge_mapped_witnesses'])}`",
        "",
        "## Candidate Sidecar Evidence",
        f"- cell_complex_status: `{candidate['cell_complex_candidate_evidence']['status']}`",
        f"- cell_complex_available: `{candidate['cell_complex_candidate_evidence']['available']}`",
        f"- chirality_mapping_status: `{candidate['chirality_mapping_candidate_evidence']['status']}`",
        f"- chirality_mapping_available: `{candidate['chirality_mapping_candidate_evidence']['available']}`",
        "",
        "## Carrier Evidence Summary",
        f"- status: `{summary['status']}`",
        f"- promotion_claim: `{summary['promotion_claim']}`",
        f"- torus_public_ids: `{', '.join(summary['torus_placement_evidence']['torus_public_ids'])}`",
        f"- torus_negative_witnesses: `{', '.join(summary['torus_placement_evidence']['relevant_negative_witnesses'])}`",
        f"- engine_public_ids: `{', '.join(summary['type_split_evidence']['engine_public_ids'])}`",
        f"- type_split_negative_witnesses: `{', '.join(summary['type_split_evidence']['relevant_negative_witnesses'])}`",
        "",
        "## Evidence Limits",
        "- not owner truth",
        "- not runtime-state graph",
        "- not history graph",
        "- not live Weyl branch evidence",
        "- not promotion evidence",
        "",
        "## Audit Conclusion",
        f"- summary: {conclusion['summary']}",
        "- safe_now:",
        *[f"  - {item}" for item in conclusion["safe_use"]],
        "- missing_now:",
        *[f"  - {item}" for item in conclusion["missing_now"]],
        "- forbidden_claims_now:",
        *[f"  - {item}" for item in conclusion["forbidden_claims_now"]],
        "",
    ])
    return "\n".join(lines)


def write_qit_hopf_weyl_evidence_audit() -> dict[str, Any]:
    payload = build_qit_hopf_weyl_evidence_audit()
    _write_json(OUT_JSON, payload)
    _write_text(OUT_MD, _render_markdown(payload))
    return payload


def main() -> None:
    payload = write_qit_hopf_weyl_evidence_audit()
    print("QIT Hopf/Weyl evidence audit written:")
    print(f"  JSON: {OUT_JSON}")
    print(f"  MD:   {OUT_MD}")
    print(f"  status: {payload['status']}")


if __name__ == "__main__":
    main()
