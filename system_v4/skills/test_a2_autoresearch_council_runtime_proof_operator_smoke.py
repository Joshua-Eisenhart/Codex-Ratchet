"""Smoke test for the autoresearch/council runtime proof operator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills import run_real_ratchet as rr
from system_v4.skills.a2_autoresearch_council_runtime_proof_operator import (
    build_a2_autoresearch_council_runtime_proof_report,
    run_a2_autoresearch_council_runtime_proof,
)
from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report, packet = build_a2_autoresearch_council_runtime_proof_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected status: {report['status']}")
    _assert(report["audit_only"] is True, "slice must stay audit-only")
    _assert(report["proof_only"] is True, "slice must stay proof-only")
    _assert(report["do_not_promote"] is True, "slice must stay do_not_promote")
    _assert(
        report["cluster_id"] == "SKILL_CLUSTER::karpathy-meta-research-runtime",
        f"unexpected cluster id: {report['cluster_id']}",
    )
    _assert(
        report["slice_id"] == "a2-autoresearch-council-runtime-proof-operator",
        f"unexpected slice id: {report['slice_id']}",
    )
    runtime = report["runtime_proof"]
    _assert(runtime["route"] == "local-autoresearch-then-council", f"unexpected route: {runtime['route']}")
    _assert(runtime["used_autoresearch"] is True, "autoresearch seam not exercised")
    _assert(runtime["used_llm_council"] is True, "llm-council seam not exercised")
    _assert(int(runtime["candidate_count"]) > 0, "proof must produce candidates")
    _assert(
        packet["recommended_next_step"] == "hold_first_slice_as_runtime_proof_only",
        f"unexpected next step: {packet['recommended_next_step']}",
    )
    _assert(packet["allow_external_runtime_import"] is False, "external runtime import must stay disabled")
    _assert(packet["allow_training"] is False, "training must stay disabled")
    _assert(packet["allow_service_bootstrap"] is False, "service bootstrap must stay disabled")
    _assert(packet["allow_branch_experiment_loop"] is False, "branch experiment loop must stay disabled")
    _assert(packet["allow_git_mutation"] is False, "git mutation must stay disabled")
    _assert(packet["allow_runtime_live_claims"] is False, "runtime live claims must stay disabled")

    blocked_report, blocked_packet = build_a2_autoresearch_council_runtime_proof_report(
        REPO_ROOT,
        {"proof_mode": "overnight_training_loop"},
    )
    _assert(blocked_report["status"] == "attention_required", "widened proof mode should fail closed")
    _assert(blocked_packet["recommended_next_step"] == "", "blocked proof should not recommend next step")

    with tempfile.TemporaryDirectory() as tmpdir:
        report_json = Path(tmpdir) / "proof.json"
        report_md = Path(tmpdir) / "proof.md"
        packet_json = Path(tmpdir) / "proof.packet.json"
        emitted = run_a2_autoresearch_council_runtime_proof(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(report_json),
                "report_md_path": str(report_md),
                "packet_path": str(packet_json),
            }
        )
        _assert(report_json.exists(), "report json missing")
        _assert(report_md.exists(), "report markdown missing")
        _assert(packet_json.exists(), "packet json missing")
        _assert(emitted["report_json_path"] == str(report_json), "unexpected report json path")
        _assert(emitted["report_md_path"] == str(report_md), "unexpected report md path")
        _assert(emitted["packet_path"] == str(packet_json), "unexpected packet path")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_autoresearch_council_runtime_proof_operator.py": (
                lambda ctx: "a2-autoresearch-council-runtime-proof-operator-dispatch"
            ),
        }
    )
    skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["karpathy-meta-research"],
    )
    _assert(
        any(skill.skill_id == "a2-autoresearch-council-runtime-proof-operator" for skill in skills),
        "karpathy runtime proof slice was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        skills,
        ["a2-autoresearch-council-runtime-proof-operator"],
        runtime_model="shell",
    )
    _assert(selected == "a2-autoresearch-council-runtime-proof-operator", f"unexpected selection: {selected}")
    _assert(not fallback, "slice unexpectedly fell back")
    _assert(dispatch is not None, "dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected dispatch reason: {reason}")

    print("PASS: a2 autoresearch council runtime proof operator smoke")


if __name__ == "__main__":
    main()
