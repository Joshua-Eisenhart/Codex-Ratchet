"""
witness_memory_retriever.py

Bounded EverMem witness-memory retrieval probe for Ratchet.

This slice stays on the already-proven witness seam, derives one bounded query,
attempts retrieval through the EverMem adapter, and emits repo-held report
surfaces. It does not claim startup bootstrap, durable memory law, pi-mono
integration, or A2 replacement.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from system_v4.skills.evermem_adapter import DEFAULT_TIMEOUT_SECONDS, EVERMEM_URL, EverMemClient


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WITNESS_PATH = "system_v4/a2_state/witness_corpus_v1.json"
DEFAULT_SYNC_REPORT_PATH = "system_v4/a2_state/audit_logs/EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.json"
DEFAULT_REPORT_JSON = "system_v4/a2_state/audit_logs/WITNESS_MEMORY_RETRIEVER_REPORT__CURRENT__v1.json"
DEFAULT_REPORT_MD = "system_v4/a2_state/audit_logs/WITNESS_MEMORY_RETRIEVER_REPORT__CURRENT__v1.md"
DEFAULT_PACKET_JSON = "system_v4/a2_state/audit_logs/WITNESS_MEMORY_RETRIEVER_PACKET__CURRENT__v1.json"

CLUSTER_ID = "SKILL_CLUSTER::evermem-witness-memory"
SLICE_ID = "witness-memory-retriever"
DEFAULT_NON_GOALS = [
    "Do not claim startup boot restore or A2 bootstrap.",
    "Do not claim pi-mono integration or outside-control-shell integration.",
    "Do not claim durable memory law or general context recovery.",
    "Do not claim semantic quality guarantees beyond attempted bounded retrieval.",
    "Do not mutate canonical A2 state, witness state, or EverMem sync state from this slice.",
]


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _resolve_output_path(root: Path, raw: Any, default_rel: str) -> Path:
    if not raw:
        return root / default_rel
    path = Path(str(raw))
    return path if path.is_absolute() else root / path


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _safe_load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_witness_entries(path: Path) -> list[dict[str, Any]]:
    raw = _safe_load_json(path)
    if raw:
        entries = raw.get("entries", [])
        if isinstance(entries, list):
            return [entry for entry in entries if isinstance(entry, dict)]
        return []
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if isinstance(payload, list):
        return [entry for entry in payload if isinstance(entry, dict)]
    return []


def _trim(text: str, limit: int = 240) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _derive_query(entry: dict[str, Any]) -> tuple[str, str]:
    tags = entry.get("tags", {}) if isinstance(entry.get("tags"), dict) else {}
    witness = entry.get("witness", {}) if isinstance(entry.get("witness"), dict) else {}
    trace = witness.get("trace", []) if isinstance(witness.get("trace"), list) else []
    trace_notes: list[str] = []
    for item in trace:
        if isinstance(item, dict):
            notes = item.get("notes", [])
            if isinstance(notes, list):
                trace_notes.extend(str(note) for note in notes if str(note).strip())

    preferred_tag_keys = ["intent", "context", "topic", "phase", "priority", "source"]
    tag_parts = [str(tags[key]).strip() for key in preferred_tag_keys if str(tags.get(key, "")).strip()]
    if trace_notes:
        return _trim(trace_notes[0]), "latest_witness_trace"
    if tag_parts:
        return _trim(" | ".join(tag_parts)), "latest_witness_tags"
    return "latest witness retrieval probe", "default_probe"


def _summarize_memories(memories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for item in memories[:3]:
        if not isinstance(item, dict):
            continue
        picked: dict[str, Any] = {}
        for key in ("id", "memory_id", "score", "sender", "create_time", "memory_type"):
            if key in item:
                picked[key] = item[key]
        content = str(item.get("content", "")).strip()
        if content:
            picked["content_preview"] = _trim(content, limit=180)
        summary.append(picked or {"raw_keys": sorted(item.keys())[:8]})
    return summary


def build_witness_memory_retriever_report(
    repo_root: str | Path,
    ctx: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = ctx or {}
    root = Path(repo_root).resolve()
    witness_path = _resolve_output_path(root, ctx.get("witness_path"), DEFAULT_WITNESS_PATH)
    sync_report_path = _resolve_output_path(root, ctx.get("sync_report_path"), DEFAULT_SYNC_REPORT_PATH)
    evermem_url = str(ctx.get("evermem_url", EVERMEM_URL))
    timeout_seconds = float(ctx.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS))
    entries = _load_witness_entries(witness_path)
    sync_report = _safe_load_json(sync_report_path)

    explicit_query = str(ctx.get("query", "")).strip()
    latest_entry = entries[-1] if entries else {}
    if explicit_query:
        query = explicit_query
        query_source = "explicit_query"
    else:
        query, query_source = _derive_query(latest_entry)

    client = EverMemClient(base_url=evermem_url, timeout_seconds=timeout_seconds)
    retrieval_result = client.search_result(
        query=query,
        user_id=str(ctx.get("user_id", "system_ratchet")),
        method=str(ctx.get("retrieve_method", "hybrid")),
    )
    success = bool(retrieval_result.get("success"))
    memories = retrieval_result.get("memories", [])
    memory_count = len(memories) if isinstance(memories, list) else 0

    issues: list[str] = []
    sync_status = str(sync_report.get("status", "missing_sync_report")).strip() or "missing_sync_report"
    if not witness_path.exists():
        issues.append("witness corpus path is missing")
    if sync_status in {"sync_failed", "partial_failure", "missing_sync_report"}:
        issues.append(f"current witness sync status is {sync_status}")
    if not success:
        error = str(retrieval_result.get("error", "")).strip() or "unknown_error"
        issues.append(f"retrieval probe failed: {error}")

    status = "ok" if success else "attention_required"
    recommended_next_step = "evaluate_bootstrap_unresolved" if success else "hold_at_retrieval_probe"
    report = {
        "schema": "WITNESS_MEMORY_RETRIEVER_REPORT_v1",
        "generated_utc": _utc_iso(),
        "repo_root": str(root),
        "status": status,
        "audit_only": True,
        "observer_only": True,
        "do_not_promote": True,
        "cluster_id": CLUSTER_ID,
        "slice_id": SLICE_ID,
        "source_family": "EverMemOS witness seam",
        "witness_path": str(witness_path.relative_to(root)) if witness_path.is_relative_to(root) else str(witness_path),
        "sync_report_path": str(sync_report_path.relative_to(root)) if sync_report_path.is_relative_to(root) else str(sync_report_path),
        "sync_status": sync_status,
        "query": query,
        "query_source": query_source,
        "entry_count": len(entries),
        "latest_witness_recorded_at": latest_entry.get("recorded_at", ""),
        "evermem_url": evermem_url,
        "timeout_seconds": timeout_seconds,
        "retrieval": {
            "success": success,
            "status_code": retrieval_result.get("status_code"),
            "error": retrieval_result.get("error", ""),
            "memory_count": memory_count,
            "memory_samples": _summarize_memories(memories if isinstance(memories, list) else []),
        },
        "gate": {
            "allow_runtime_claims": False,
            "allow_bootstrap_claims": False,
            "allow_pimono_memory_claims": False,
            "allow_a2_replacement_claims": False,
            "recommended_next_step": recommended_next_step,
            "reason": (
                "bounded witness-seam retrieval succeeded without admitting startup bootstrap or broader memory claims"
                if success
                else "bounded witness-seam retrieval did not succeed, so broader EverMem claims remain unearned"
            ),
        },
        "recommended_next_actions": [
            "Keep this slice bounded to witness-seam retrieval and repo-held reporting only.",
            "Do not widen this result into startup bootstrap, pi-mono memory, or A2 replacement claims.",
            "Use this report as evidence for later EverMem planning only after the retrieval result is explicit.",
        ],
        "non_goals": list(DEFAULT_NON_GOALS),
        "issues": issues,
    }
    packet = {
        "schema": "WITNESS_MEMORY_RETRIEVER_PACKET_v1",
        "generated_utc": report["generated_utc"],
        "status": report["status"],
        "cluster_id": report["cluster_id"],
        "slice_id": report["slice_id"],
        "query": query,
        "query_source": query_source,
        "sync_status": sync_status,
        "retrieval_success": success,
        "memory_count": memory_count,
        "allow_runtime_claims": False,
        "allow_bootstrap_claims": False,
        "allow_pimono_memory_claims": False,
        "allow_a2_replacement_claims": False,
        "next_step": recommended_next_step,
        "recommended_next_step": recommended_next_step,
        "issues": issues,
    }
    return report, packet


def _render_markdown(report: dict[str, Any], packet: dict[str, Any]) -> str:
    retrieval = report.get("retrieval", {})
    lines = [
        "# Witness Memory Retriever Report",
        "",
        f"- generated_utc: `{report.get('generated_utc', '')}`",
        f"- status: `{report.get('status', '')}`",
        f"- cluster_id: `{report.get('cluster_id', '')}`",
        f"- slice_id: `{report.get('slice_id', '')}`",
        f"- sync_status: `{report.get('sync_status', '')}`",
        f"- query_source: `{report.get('query_source', '')}`",
        f"- query: `{report.get('query', '')}`",
        f"- retrieval_success: `{retrieval.get('success', False)}`",
        f"- memory_count: `{retrieval.get('memory_count', 0)}`",
        "",
        "## Retrieval Summary",
        f"- status_code: `{retrieval.get('status_code', '')}`",
        f"- error: `{retrieval.get('error', '')}`",
        "",
        "## Memory Samples",
    ]
    samples = retrieval.get("memory_samples", [])
    if samples:
        for sample in samples:
            lines.append(f"- `{json.dumps(sample, sort_keys=True)}`")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Recommended Actions",
            *[f"- {item}" for item in report.get("recommended_next_actions", [])],
            "",
            "## Non-Goals",
            *[f"- {item}" for item in report.get("non_goals", [])],
            "",
            "## Issues",
        ]
    )
    issues = report.get("issues", [])
    if issues:
        lines.extend(f"- {item}" for item in issues)
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Packet",
            f"- next_step: `{packet.get('next_step', '')}`",
            f"- allow_bootstrap_claims: `{packet.get('allow_bootstrap_claims', False)}`",
            f"- allow_pimono_memory_claims: `{packet.get('allow_pimono_memory_claims', False)}`",
        ]
    )
    return "\n".join(lines) + "\n"


def run_witness_memory_retriever(ctx: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = ctx or {}
    root = Path(ctx.get("repo_root") or ctx.get("repo") or REPO_ROOT).resolve()
    report_path = _resolve_output_path(root, ctx.get("report_json_path"), DEFAULT_REPORT_JSON)
    markdown_path = _resolve_output_path(root, ctx.get("report_md_path"), DEFAULT_REPORT_MD)
    packet_path = _resolve_output_path(root, ctx.get("packet_path"), DEFAULT_PACKET_JSON)

    report, packet = build_witness_memory_retriever_report(root, ctx)
    _write_json(report_path, report)
    _write_text(markdown_path, _render_markdown(report, packet))
    _write_json(packet_path, packet)

    emitted = dict(report)
    emitted["report_json_path"] = str(report_path)
    emitted["report_md_path"] = str(markdown_path)
    emitted["packet_path"] = str(packet_path)
    emitted["packet"] = packet
    return emitted


if __name__ == "__main__":
    result = run_witness_memory_retriever({"repo_root": str(REPO_ROOT)})
    print(
        "PASS:",
        result["status"],
        result["query_source"],
        result["retrieval"]["memory_count"],
    )
