"""
graveyard_lawyer.py — Report-only graveyard review

Shell-backed execution surface for the graveyard-lawyer skill. This module
inspects live graveyard records and emits bounded rescue/reclassify proposals
without reopening concepts automatically.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any


_DERIVED_TERM_RE = re.compile(r"Derived-only term '([^']+)'")


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def _proposal_for_record(record: Any, admitted_terms: set[str]) -> dict[str, Any]:
    reason_tag = getattr(record, "reason_tag", "")
    detail = getattr(record, "detail", "") or ""
    target_ref = getattr(record, "target_ref", None)
    primary_candidate_id = getattr(record, "primary_candidate_id", None) or target_ref
    source_concept_id = getattr(record, "source_concept_id", None) or target_ref
    proposed_action = "KEEP_DEAD"
    confidence = "LOW"
    new_evidence = ""

    if reason_tag == "DERIVED_ONLY_NOT_PERMITTED":
        match = _DERIVED_TERM_RE.search(detail)
        derived_term = match.group(1) if match else ""
        if derived_term and derived_term in admitted_terms:
            proposed_action = "REOPEN"
            confidence = "MEDIUM"
            new_evidence = f"Term '{derived_term}' is now admitted in the term registry."
        else:
            new_evidence = "Derived-only term is still not admitted."
    elif reason_tag == "UNDEFINED_TERM_USE":
        proposed_action = "KEEP_DEAD"
        confidence = "LOW"
        new_evidence = "Undefined-term failures need term admission before reopen."
    elif reason_tag == "SCHEMA_FAIL" and "probe_target" in detail:
        proposed_action = "RECLASSIFY"
        confidence = "LOW"
        new_evidence = "SIM_SPEC failure is schema-shaped and may need probe-target reconstruction."
    else:
        new_evidence = "No new evidence found in current runtime surfaces."

    return {
        "candidate_id": getattr(record, "candidate_id", ""),
        "reason_tag": reason_tag,
        "failure_class": getattr(record, "failure_class", ""),
        "stage": getattr(record, "stage", ""),
        "source_concept_id": source_concept_id,
        "primary_candidate_id": primary_candidate_id,
        "target_ref": target_ref,
        "proposed_action": proposed_action,
        "confidence": confidence,
        "new_evidence": new_evidence,
    }


def build_rescue_report(
    repo: str,
    batch_id: str,
    kernel: Any,
    brain: Any,
    limit: int = 10,
    apply_reopens: bool = False,
) -> dict[str, Any]:
    runtime_dir = Path(repo) / "system_v4" / "runtime_state"
    report_path = runtime_dir / "graveyard_lawyer_reports.jsonl"
    admitted_terms = set(getattr(brain, "term_registry", {}).keys())

    records = list(getattr(kernel, "graveyard", []))
    recent_records = records[-limit:]
    proposals = [_proposal_for_record(rec, admitted_terms) for rec in recent_records]
    reopened_source_concept_ids: list[str] = []

    if apply_reopens:
        from system_v4.skills.a1_routing_state import A1RoutingState

        routing = A1RoutingState(repo)
        for proposal in proposals:
            source_concept_id = proposal.get("source_concept_id")
            if proposal["proposed_action"] != "REOPEN" or not source_concept_id:
                continue
            reason = (
                f"graveyard_lawyer:{proposal['reason_tag']}: "
                f"{proposal['new_evidence']}"
            )
            if routing.mark_reopen(source_concept_id, reason=reason):
                reopened_source_concept_ids.append(source_concept_id)
        if reopened_source_concept_ids:
            routing.save()

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "batch_id": batch_id,
        "graveyard_size": len(records),
        "reviewed_count": len(recent_records),
        "proposal_count": len(proposals),
        "reopen_proposal_count": sum(1 for p in proposals if p["proposed_action"] == "REOPEN"),
        "reopen_count": len(reopened_source_concept_ids),
        "reopened_source_concept_ids": reopened_source_concept_ids,
        "reclassify_count": sum(1 for p in proposals if p["proposed_action"] == "RECLASSIFY"),
        "proposals": proposals,
    }
    _append_jsonl(report_path, report)
    return report
