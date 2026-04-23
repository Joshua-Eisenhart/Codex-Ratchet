#!/usr/bin/env python3
"""
qit_runtime_evidence_bridge.py

Persist a small, read-only QIT runtime/evidence bridge artifact.

This is intentionally not a runtime-state graph or history graph. It builds a
repo-held audit packet from:
  - sample runtime slices emitted by qit_runtime_state_history_adapter.py
  - selected SIM_EVIDENCE result files that map cleanly onto stable QIT ids

The bridge is observational. It does not mutate owner truth and does not claim
that runtime/history promotion has happened.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "probes"))

from engine_core import GeometricEngine
from qit_runtime_state_history_adapter import build_runtime_slice


REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = REPO_ROOT / "system_v4" / "a2_state" / "audit_logs"
GRAPH_PATH = REPO_ROOT / "system_v4" / "a2_state" / "graphs" / "qit_engine_graph_v1.json"
OUT_JSON = AUDIT_DIR / "QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.json"
OUT_MD = AUDIT_DIR / "QIT_RUNTIME_EVIDENCE_BRIDGE__CURRENT__v1.md"
SIM_RESULTS_DIR = REPO_ROOT / "system_v4" / "probes" / "a2_state" / "sim_results"

SIM_RESULT_MAPPINGS: list[dict[str, Any]] = [
    {
        "result_file": "neg_axis6_shared_stage_matrix_results.json",
        "neg_witness_public_id": "qit::NEG_WITNESS::neg_axis6_shared",
        "target_public_ids": ["qit::AXIS::axis_6"],
        "summary_keys": ["control_equivalence", "closest_mixed_axis6"],
    },
    {
        "result_file": "neg_missing_fe_stage_matrix_results.json",
        "neg_witness_public_id": "qit::NEG_WITNESS::neg_missing_fe",
        "target_public_ids": ["qit::OPERATOR::Fe"],
        "summary_keys": ["overall", "by_native_operator"],
    },
    {
        "result_file": "neg_missing_operator_stage_matrix_results.json",
        "neg_witness_public_id": "qit::NEG_WITNESS::neg_missing_operator",
        "target_public_ids": [
            "qit::OPERATOR::Ti",
            "qit::OPERATOR::Fe",
            "qit::OPERATOR::Te",
            "qit::OPERATOR::Fi",
        ],
        "summary_keys": ["closest_missing_operator", "missing_operator_sweep"],
    },
    {
        "result_file": "neg_native_only_stage_matrix_results.json",
        "neg_witness_public_id": "qit::NEG_WITNESS::neg_native_only",
        "target_public_ids": [],
        "summary_keys": ["native_only_collapse"],
    },
    {
        "result_file": "neg_type_flatten_stage_matrix_results.json",
        "neg_witness_public_id": "qit::NEG_WITNESS::neg_type_flatten",
        "target_public_ids": [
            "qit::ENGINE::type1_left_weyl",
            "qit::ENGINE::type2_right_weyl",
        ],
        "summary_keys": ["flat_type_weighting"],
    },
]


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
        output = subprocess.check_output(
            cmd,
            cwd=str(REPO_ROOT),
            text=True,
        )
    except Exception:
        return []
    return [line.rstrip() for line in output.splitlines() if line.strip()]


def _owner_snapshot() -> tuple[dict[str, Any], dict[str, str], dict[str, dict[str, Any]]]:
    payload = _load_json(GRAPH_PATH)
    nodes = payload.get("nodes", {})
    public_id_index = payload.get("public_id_index", {})
    return payload, public_id_index, nodes


def _build_runtime_samples() -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for engine_type in (1, 2):
        engine = GeometricEngine(engine_type=engine_type)
        state = engine.init_state()
        state = engine.run_cycle(state)
        engine_name = "type1_left_weyl" if engine_type == 1 else "type2_right_weyl"
        run_id = f"qit_runtime_cycle_sample::{engine_name}::deterministic_full_cycle"
        runtime_slice = build_runtime_slice(state, run_id=run_id)
        overlay = runtime_slice["state_overlay"]
        history = runtime_slice["history_packet"]
        axis0_bridge_snapshot = runtime_slice["axis0_bridge_snapshot"]
        axis0_history_window_snapshot = runtime_slice["axis0_history_window_snapshot"]
        samples.append(
            {
                "run_id": history["run_id"],
                "engine_public_id": history["engine_public_id"],
                "engine_type": history["engine_type"],
                "sample_kind": "deterministic_full_cycle",
                "runtime_slice_schema": runtime_slice["schema"],
                "persistence_policy": runtime_slice["persistence_policy"],
                "overlay": overlay,
                "axis0_bridge_snapshot": axis0_bridge_snapshot,
                "axis0_history_window_snapshot": axis0_history_window_snapshot,
                "history_summary": {
                    "total_steps": history["total_steps"],
                    "macro_stages_completed": history["macro_stages_completed"],
                    "first_step_public_id": history["step_records"][0]["step_public_id"] if history["step_records"] else None,
                    "last_step_public_id": history["step_records"][-1]["step_public_id"] if history["step_records"] else None,
                },
                "history_packet": history,
            }
        )
    return samples


def _resolve_links(
    public_ids: list[str],
    public_id_index: dict[str, str],
    nodes: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    resolved: list[dict[str, Any]] = []
    unresolved: list[str] = []
    for public_id in public_ids:
        node_id = public_id_index.get(public_id)
        if not node_id or node_id not in nodes:
            unresolved.append(public_id)
            continue
        node = nodes[node_id]
        resolved.append(
            {
                "public_id": public_id,
                "node_id": node_id,
                "node_type": node.get("node_type", ""),
                "label": node.get("label", ""),
            }
        )
    return resolved, unresolved


def _extract_summary(payload: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    return {key: payload.get(key) for key in keys if key in payload}


def _build_sim_evidence_packets(
    public_id_index: dict[str, str],
    nodes: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    for mapping in SIM_RESULT_MAPPINGS:
        result_path = SIM_RESULTS_DIR / mapping["result_file"]
        if not result_path.exists():
            packets.append(
                {
                    "result_file": mapping["result_file"],
                    "status": "missing_result_file",
                    "result_path": str(result_path),
                }
            )
            continue

        payload = _load_json(result_path)
        link_ids = [mapping["neg_witness_public_id"], *mapping["target_public_ids"]]
        resolved_links, unresolved_links = _resolve_links(link_ids, public_id_index, nodes)
        mapping_status = "complete"
        if unresolved_links:
            mapping_status = "partial"
        elif not mapping["target_public_ids"]:
            mapping_status = "witness_only"

        packets.append(
            {
                "result_file": mapping["result_file"],
                "result_path": str(result_path),
                "status": mapping_status,
                "schema": payload.get("schema", ""),
                "timestamp": payload.get("timestamp", ""),
                "neg_witness_public_id": mapping["neg_witness_public_id"],
                "target_public_ids": list(mapping["target_public_ids"]),
                "resolved_links": resolved_links,
                "unresolved_links": unresolved_links,
                "evidence_ledger": payload.get("evidence_ledger", []),
                "summary_excerpt": _extract_summary(payload, mapping["summary_keys"]),
            }
        )
    return packets


def _axis0_control_plane_summary(runtime_samples: list[dict[str, Any]]) -> dict[str, Any]:
    direct_families = sorted(
        {
            str(sample.get("axis0_bridge_snapshot", {}).get("bridge_family", ""))
            for sample in runtime_samples
            if sample.get("axis0_bridge_snapshot")
        }
    )
    history_window_families = sorted(
        {
            str(sample.get("axis0_history_window_snapshot", {}).get("bridge_family", ""))
            for sample in runtime_samples
            if sample.get("axis0_history_window_snapshot")
        }
    )
    history_window_sample_counts = sorted(
        {
            int(sample.get("axis0_history_window_snapshot", {}).get("n_samples", 0))
            for sample in runtime_samples
            if sample.get("axis0_history_window_snapshot")
        }
    )
    return {
        "surface_status": "read_only_control_plane_summary_only",
        "runtime_sample_count": len(runtime_samples),
        "direct_bridge_families": [family for family in direct_families if family],
        "history_window_bridge_families": [family for family in history_window_families if family],
        "history_window_sample_counts": history_window_sample_counts,
    }


def build_qit_runtime_evidence_bridge() -> dict[str, Any]:
    script_path = Path(__file__).resolve()
    owner_payload, public_id_index, nodes = _owner_snapshot()
    runtime_samples = _build_runtime_samples()
    sim_packets = _build_sim_evidence_packets(public_id_index, nodes)

    complete = sum(1 for packet in sim_packets if packet.get("status") == "complete")
    partial = sum(1 for packet in sim_packets if packet.get("status") in {"partial", "witness_only"})
    missing = sum(1 for packet in sim_packets if packet.get("status") == "missing_result_file")
    resolved_links = sum(len(packet.get("resolved_links", [])) for packet in sim_packets)
    unresolved_links = sum(len(packet.get("unresolved_links", [])) for packet in sim_packets)

    return {
        "schema": "QIT_RUNTIME_EVIDENCE_BRIDGE_v1",
        "generated_utc": _utc_iso(),
        "audit_only": True,
        "nonoperative": True,
        "do_not_promote": True,
        "owner_graph_role": "read_only_reference_only",
        "persistence_policy": "persisted_audit_log_packet",
        "runtime_capture_mode": "deterministic_sample_replay",
        "live_runtime_capture": False,
        "report_surface": {
            "surface_class": "tracked_current_workspace_report",
            "represents": (
                "current workspace runtime/evidence bridge state at generation time; may differ from the last "
                "committed snapshot until tracked CURRENT artifacts are committed"
            ),
            "tracked_report_files": [
                str(OUT_JSON),
                str(OUT_MD),
            ],
            "tracked_report_files_dirty_before_generation": _git_status_porcelain([OUT_JSON, OUT_MD]),
            "script_path": str(script_path),
            "script_sha256": _sha256_path(script_path),
            "git_sha": _git_sha(),
        },
        "derived_from": {
            "builder_program": str(Path(__file__).resolve()),
            "runtime_adapter": str((REPO_ROOT / "system_v4" / "skills" / "qit_runtime_state_history_adapter.py").resolve()),
            "owner_graph": str(GRAPH_PATH),
            "sim_results_dir": str(SIM_RESULTS_DIR),
        },
        "owner_snapshot": {
            "qit_graph_json": str(GRAPH_PATH),
            "qit_graph_content_hash": owner_payload.get("content_hash", ""),
            "node_count": len(nodes),
            "edge_count": len(owner_payload.get("edges", [])),
            "public_id_index_size": len(public_id_index),
        },
        "axis0_control_plane_summary": _axis0_control_plane_summary(runtime_samples),
        "runtime_samples": runtime_samples,
        "sim_evidence_packets": sim_packets,
        "summary": {
            "runtime_sample_count": len(runtime_samples),
            "sim_packet_count": len(sim_packets),
            "complete_mappings": complete,
            "partial_mappings": partial,
            "missing_packets": missing,
            "resolved_owner_links": resolved_links,
            "unresolved_owner_links": unresolved_links,
        },
    }


def _render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    surface = payload["report_surface"]
    axis0_summary = payload["axis0_control_plane_summary"]
    sample_lines = "\n".join(
        f"- {sample['engine_public_id']}: `{sample['history_summary']['total_steps']}` steps, "
        f"last step `{sample['history_summary']['last_step_public_id']}`, "
        f"`axis0_bridge_snapshot` `{sample['axis0_bridge_snapshot']['bridge_family']}`, "
        f"`axis0_history_window_snapshot` `{sample['axis0_history_window_snapshot']['bridge_family']}` "
        f"({sample['axis0_history_window_snapshot']['n_samples']} samples)"
        for sample in payload["runtime_samples"]
    )
    packet_lines = "\n".join(
        f"- {packet['result_file']}: `{packet['status']}` "
        f"(resolved_links={len(packet.get('resolved_links', []))}, unresolved_links={len(packet.get('unresolved_links', []))})"
        for packet in payload["sim_evidence_packets"]
    )
    return "\n".join(
        [
            "# QIT Runtime Evidence Bridge",
            "",
            f"- generated_utc: `{payload['generated_utc']}`",
            f"- audit_only: `{payload['audit_only']}`",
            f"- nonoperative: `{payload['nonoperative']}`",
            f"- do_not_promote: `{payload['do_not_promote']}`",
            f"- persistence_policy: `{payload['persistence_policy']}`",
            f"- owner_graph_role: `{payload['owner_graph_role']}`",
            f"- runtime_capture_mode: `{payload['runtime_capture_mode']}`",
            f"- live_runtime_capture: `{payload['live_runtime_capture']}`",
            f"- owner_content_hash: `{payload['owner_snapshot']['qit_graph_content_hash']}`",
            "",
            "## Report Surface",
            f"- surface_class: `{surface['surface_class']}`",
            f"- represents: `{surface['represents']}`",
            f"- git_sha: `{surface['git_sha']}`",
            "",
            "## Axis0 Control-Plane Summary",
            f"- surface_status: `{axis0_summary['surface_status']}`",
            f"- runtime_sample_count: `{axis0_summary['runtime_sample_count']}`",
            f"- direct_bridge_families: `{', '.join(axis0_summary['direct_bridge_families']) or 'none'}`",
            f"- history_window_bridge_families: `{', '.join(axis0_summary['history_window_bridge_families']) or 'none'}`",
            f"- history_window_sample_counts: `{', '.join(str(v) for v in axis0_summary['history_window_sample_counts']) or 'none'}`",
            "",
            "## Runtime Samples",
            sample_lines or "- none",
            "",
            "## SIM Evidence Packets",
            packet_lines or "- none",
            "",
            "## Summary",
            f"- runtime_sample_count: `{summary['runtime_sample_count']}`",
            f"- sim_packet_count: `{summary['sim_packet_count']}`",
            f"- complete_mappings: `{summary['complete_mappings']}`",
            f"- partial_mappings: `{summary['partial_mappings']}`",
            f"- missing_packets: `{summary['missing_packets']}`",
            f"- resolved_owner_links: `{summary['resolved_owner_links']}`",
            f"- unresolved_owner_links: `{summary['unresolved_owner_links']}`",
            "",
            "## Boundary",
            "- This is a read-only audit-log packet/report surface.",
            "- It is not a promoted runtime-state graph.",
            "- It is not a promoted history graph.",
            "- The tracked __CURRENT__ files represent the current workspace after generation, not automatically the last committed snapshot.",
        ]
    )


def write_qit_runtime_evidence_bridge() -> dict[str, Any]:
    payload = build_qit_runtime_evidence_bridge()
    _write_json(OUT_JSON, payload)
    _write_text(OUT_MD, _render_markdown(payload))
    return payload


def main() -> None:
    payload = write_qit_runtime_evidence_bridge()
    print("QIT runtime evidence bridge written:")
    print(f"  JSON: {OUT_JSON}")
    print(f"  MD:   {OUT_MD}")
    print(f"  Runtime samples: {payload['summary']['runtime_sample_count']}")
    print(f"  SIM packets:     {payload['summary']['sim_packet_count']}")
    print(f"  Resolved links:  {payload['summary']['resolved_owner_links']}")


if __name__ == "__main__":
    main()
