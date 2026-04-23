"""Smoke test for the bounded workshop-analysis gate operator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.a2_workshop_analysis_gate_operator import (
    build_a2_workshop_analysis_gate_report,
    run_a2_workshop_analysis_gate,
)
from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report, packet = build_a2_workshop_analysis_gate_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected workshop gate status: {report['status']}")
    _assert(
        report["cluster_id"] == "SKILL_CLUSTER::workshop-analysis-gating",
        "unexpected cluster id",
    )
    _assert(
        report["first_slice"] == "a2-workshop-analysis-gate-operator",
        "unexpected first slice id",
    )
    _assert(report["audit_only"] is True, "workshop gate should stay audit-only")
    _assert(report["nonoperative"] is True, "workshop gate should stay nonoperative")
    _assert(report["do_not_promote"] is True, "workshop gate should stay non-promotable")
    _assert(
        packet["allow_bounded_workshop_analysis"] is True,
        "workshop gate should allow bounded analysis on the live repo",
    )

    blocked_report, _ = build_a2_workshop_analysis_gate_report(
        REPO_ROOT,
        {
            "candidate": {
                "id": "bad-candidate",
                "title": "too-wide candidate",
                "type": "pattern",
                "source": "test",
                "raw_input": "build a poc and integrate this to production",
                "stage_request": "integration",
            }
        },
    )
    _assert(
        blocked_report["status"] == "attention_required",
        "wide candidate should force attention_required status",
    )
    _assert(
        blocked_report["gate"]["allow_bounded_workshop_analysis"] is False,
        "wide candidate should not pass the workshop gate",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "workshop_gate.json"
        md_path = Path(tmpdir) / "workshop_gate.md"
        packet_path = Path(tmpdir) / "workshop_gate.packet.json"
        emitted = run_a2_workshop_analysis_gate(
            {
                "repo": str(REPO_ROOT),
                "report_path": str(json_path),
                "markdown_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "workshop gate json was not written")
        _assert(md_path.exists(), "workshop gate markdown was not written")
        _assert(packet_path.exists(), "workshop gate packet was not written")
        _assert(emitted["report_path"] == str(json_path), "unexpected workshop gate json path")
        _assert(emitted["markdown_path"] == str(md_path), "unexpected workshop gate markdown path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected workshop gate packet path")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_workshop_analysis_gate_operator.py": (
                lambda ctx: "a2-workshop-analysis-gate-operator-dispatch"
            ),
        }
    )
    workshop_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["workshop-analysis-gating"],
    )
    _assert(
        any(skill.skill_id == "a2-workshop-analysis-gate-operator" for skill in workshop_skills),
        "a2-workshop-analysis-gate-operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        workshop_skills,
        ["a2-workshop-analysis-gate-operator"],
        runtime_model="shell",
    )
    _assert(
        selected == "a2-workshop-analysis-gate-operator",
        f"unexpected workshop gate selection: {selected}",
    )
    _assert(not fallback, "a2-workshop-analysis-gate-operator unexpectedly fell back")
    _assert(dispatch is not None, "a2-workshop-analysis-gate-operator dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected workshop gate reason: {reason}")

    print("PASS: a2 workshop analysis gate operator smoke")


if __name__ == "__main__":
    main()
