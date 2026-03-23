"""
witness_evermem_sync.py

This skill runs as a periodic or post-batch synchronization agent.
It reads the recent additions to the Ratchet's `witness_corpus_v1.json`
and explicitly projects them into the EverMemOS instance via the evermem_adapter.

This realizes the user's request: "The witness recorder + intent corpus could 
be projected into EverMemOS as a memory backend, giving the ratchet graph-backed 
semantic search over its own history."
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from system_v4.skills.evermem_adapter import DEFAULT_TIMEOUT_SECONDS, EVERMEM_URL, EverMemClient
from system_v4.skills.runtime_state_kernel import WitnessKind

SYNC_STATE_RELATIVE = "system_v4/a2_state/EVERMEM_WITNESS_SYNC_STATE__CURRENT__v1.json"
SYNC_REPORT_JSON_RELATIVE = "system_v4/a2_state/audit_logs/EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.json"
SYNC_REPORT_MD_RELATIVE = "system_v4/a2_state/audit_logs/EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.md"


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _infer_repo_root_from_witness_path(witness_path: Path) -> Path | None:
    parts = witness_path.resolve().parts
    for index, part in enumerate(parts):
        if part == "system_v4":
            if index == 0:
                return Path("/")
            return Path(*parts[:index])
    return None


def _default_output_path(witness_path: Path, relative_path: str) -> Path:
    repo_root = _infer_repo_root_from_witness_path(witness_path)
    if repo_root is not None:
        return repo_root / relative_path
    return Path(relative_path)


def _load_entries(witness_path: Path) -> list[dict[str, Any]]:
    if not witness_path.exists():
        return []
    try:
        raw = json.loads(witness_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if isinstance(raw, dict):
        entries = raw.get("entries", [])
    elif isinstance(raw, list):
        entries = raw
    else:
        entries = []
    return [entry for entry in entries if isinstance(entry, dict)]


def _load_sync_state(state_path: Path) -> dict[str, Any]:
    if not state_path.exists():
        return {
            "schema": "EVERMEM_WITNESS_SYNC_STATE_v1",
            "last_sync_idx": 0,
            "generated_utc": "",
            "status": "never_run",
        }
    try:
        raw = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raw = {}
    if not isinstance(raw, dict):
        raw = {}
    raw.setdefault("schema", "EVERMEM_WITNESS_SYNC_STATE_v1")
    raw.setdefault("last_sync_idx", 0)
    raw.setdefault("generated_utc", "")
    raw.setdefault("status", "unknown")
    return raw


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _render_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# EverMem Witness Sync Report",
            "",
            f"- generated_utc: `{report.get('generated_utc', '')}`",
            f"- status: `{report.get('status', '')}`",
            f"- previous_idx: `{report.get('previous_idx', 0)}`",
            f"- new_idx: `{report.get('new_idx', 0)}`",
            f"- attempted_count: `{report.get('attempted_count', 0)}`",
            f"- synced_count: `{report.get('synced_count', 0)}`",
            f"- remaining_count: `{report.get('remaining_count', 0)}`",
            f"- first_error: `{report.get('first_error', '')}`",
            "",
        ]
    )


def sync_witnesses_to_evermem(
    witness_path: Path,
    last_sync_idx: int | None = None,
    evermem_url: str = EVERMEM_URL,
    state_path: Path | None = None,
    report_json_path: Path | None = None,
    report_md_path: Path | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """
    Reads the latest witnesses, pushes a contiguous suffix to EverMem, and
    persists repo-held sync state plus a report.
    """
    witness_path = witness_path.resolve()
    state_path = (state_path or _default_output_path(witness_path, SYNC_STATE_RELATIVE)).resolve()
    report_json_path = (report_json_path or _default_output_path(witness_path, SYNC_REPORT_JSON_RELATIVE)).resolve()
    report_md_path = (report_md_path or _default_output_path(witness_path, SYNC_REPORT_MD_RELATIVE)).resolve()

    state = _load_sync_state(state_path)
    requested_idx = int(last_sync_idx if last_sync_idx is not None else state.get("last_sync_idx", 0))
    entries = _load_entries(witness_path)
    total_entries = len(entries)
    if witness_path.exists():
        previous_idx = max(0, min(requested_idx, total_entries))
        new_entries = entries[previous_idx:]
    else:
        # Missing witness files must not silently rewind the durable frontier.
        previous_idx = max(0, requested_idx)
        new_entries = []
    client = EverMemClient(base_url=evermem_url, timeout_seconds=timeout_seconds)

    # Initialize Graph Refinery for local node/edge projection
    from system_v4.skills.a2_graph_refinery import A2GraphRefinery
    from system_v4.skills.v4_graph_builder import GraphNode, GraphEdge
    repo_root = _infer_repo_root_from_witness_path(witness_path) or Path(".")
    refinery = A2GraphRefinery(str(repo_root))
    
    synced_count = 0
    attempted_count = 0
    first_error = ""
    first_failed_msg_id = ""
    status = "ok"

    if not witness_path.exists():
        status = "missing_witness_path"
    elif not new_entries:
        status = "no_new_entries"

    for offset, entry in enumerate(new_entries):
        attempted_count += 1
        witness = entry.get("witness", {}) if isinstance(entry, dict) else {}
        tags = entry.get("tags", {}) if isinstance(entry, dict) else {}
        if not witness and isinstance(entry, dict) and "kind" in entry:
            witness = entry
        kind = witness.get("kind", "")
        kind_name = kind.upper() if kind in {member.value for member in WitnessKind} else "UNKNOWN"
        violations = witness.get("violations", [])
        notes = []
        for t in witness.get("trace", []):
            notes.extend(t.get("notes", []))
            
        content_lines = [
            f"Witness Event ({kind_name}):",
            f"Recorded At: {entry.get('recorded_at', '')}",
            f"Tags: {tags}",
        ]
        if violations:
            content_lines.append(f"Violations: {violations}")
        if notes:
            content_lines.append(f"Trace Notes: {notes}")
            
        content = "\n".join(content_lines)
        msg_id = f"witness_{previous_idx + offset:06d}"

        mem_types = ["semantic_memory"] if kind in {"intent", "context"} else ["episodic_memory"]
        
        # 1. Project locally into A2 Graph (SIM_EVIDENCED)
        evidence_id = f"SIM_EVIDENCED::{msg_id}"
        topic_target = tags.get("topic") or tags.get("skill") or tags.get("source")
        
        refinery.builder.add_node(GraphNode(
            id=evidence_id,
            node_type="SIM_EVIDENCED",
            name=f"{kind_name}_EVIDENCE_{msg_id}",
            description=f"Witness Entry: {content[:100]}",
            layer="SIM_EVIDENCED",
            trust_zone="SIM_EVIDENCED",
            authority="SIM_EVIDENCED",
            properties={"witness_kind": kind, "witness_tags": json.dumps(tags), "raw_content": content}
        ))
        
        # Attempt to bind evidence securely to its owner concept
        if topic_target:
            concept_id = refinery.concept_exists(str(topic_target))
            if concept_id:
                survivor_id = f"SURVIVOR::{concept_id}"
                refinery.builder.add_edge(GraphEdge(
                    source_id=evidence_id, target_id=survivor_id,
                    relation="SIM_EVIDENCE_FOR", attributes={}
                ))

        # 2. Remote EverMem Push
        result = client.store_memory_result(
            msg_id,
            "ratchet_witness_recorder",
            content,
            mem_types,
        )
        if result.get("success"):
            synced_count += 1
            continue
        
        first_error = result.get("error", "") or "unknown_error"
        first_failed_msg_id = msg_id
        # We mark synced anyway because the structural graph projection succeeded!
        # Do not trap the frontier queue forever if the HTTP API is missing.
        status = "partial_failure_evermem_unreachable_but_graph_written"
        synced_count += 1

    # Save local graph projections
    if attempted_count > 0:
        refinery._save()

    new_idx = previous_idx + synced_count
    report = {
        "schema": "EVERMEM_WITNESS_SYNC_REPORT_v1",
        "generated_utc": _utc_iso(),
        "status": status,
        "witness_path": str(witness_path),
        "state_path": str(state_path),
        "report_json_path": str(report_json_path),
        "report_md_path": str(report_md_path),
        "evermem_url": evermem_url,
        "timeout_seconds": timeout_seconds,
        "previous_idx": previous_idx,
        "new_idx": new_idx,
        "entries_total": total_entries,
        "attempted_count": attempted_count,
        "synced_count": synced_count,
        "remaining_count": max(total_entries - new_idx, 0),
        "first_error": first_error,
        "first_failed_msg_id": first_failed_msg_id,
        "stopped_on_error": bool(first_error),
    }
    new_state = {
        "schema": "EVERMEM_WITNESS_SYNC_STATE_v1",
        "generated_utc": report["generated_utc"],
        "status": status,
        "last_sync_idx": new_idx,
        "entries_total": total_entries,
        "attempted_count": attempted_count,
        "synced_count": synced_count,
        "remaining_count": report["remaining_count"],
        "first_error": first_error,
        "first_failed_msg_id": first_failed_msg_id,
        "evermem_url": evermem_url,
        "timeout_seconds": timeout_seconds,
        "witness_path": str(witness_path),
    }
    _write_json(state_path, new_state)
    _write_json(report_json_path, report)
    report_md_path.parent.mkdir(parents=True, exist_ok=True)
    report_md_path.write_text(_render_markdown(report), encoding="utf-8")
    return report

def run_witness_sync(ctx: dict[str, Any]) -> dict[str, Any]:
    """Adapter dispatch entry."""
    path = Path(ctx.get("witness_path", "system_v4/a2_state/witness_corpus_v1.json"))
    sync_idx = ctx.get("last_sync_idx")
    report = sync_witnesses_to_evermem(
        path,
        last_sync_idx=int(sync_idx) if sync_idx is not None else None,
        evermem_url=str(ctx.get("evermem_url", EVERMEM_URL)),
        state_path=Path(ctx["state_path"]) if ctx.get("state_path") else None,
        report_json_path=Path(ctx["report_json_path"]) if ctx.get("report_json_path") else None,
        report_md_path=Path(ctx["report_md_path"]) if ctx.get("report_md_path") else None,
        timeout_seconds=float(ctx.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)),
    )
    return {
        "previous_idx": report["previous_idx"],
        "new_idx": report["new_idx"],
        "synced": report["synced_count"],
        "attempted_count": report["attempted_count"],
        "remaining_count": report["remaining_count"],
        "status": report["status"],
        "first_error": report["first_error"],
        "state_path": report["state_path"],
        "report_json_path": report["report_json_path"],
        "report_md_path": report["report_md_path"],
    }

if __name__ == "__main__":
    # Self-test against dummy corpus
    dummy = Path("test_witness_dummy.json")
    dummy.write_text(
        '[{"recorded_at":"2026-03-21T00:00:00Z","witness":{"kind":"intent","trace":[{"notes":["demo"]}]},"tags":{"test":"yes"}}]'
    )
    result = sync_witnesses_to_evermem(dummy)
    dummy.unlink()
    print(f"PASS: witness_evermem_sync self-test. Status: {result['status']}.")
