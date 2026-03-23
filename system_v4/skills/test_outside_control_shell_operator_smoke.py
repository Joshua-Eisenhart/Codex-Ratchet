"""Smoke test for the bounded pi-mono outside control shell operator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills import run_real_ratchet as rr
from system_v4.skills.outside_control_shell_operator import (
    build_outside_control_shell_report,
    run_outside_control_shell_operator,
)
from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report, packet = build_outside_control_shell_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected outside shell status: {report['status']}")
    _assert(
        report["cluster_id"] == "SKILL_CLUSTER::outside-control-shell-session-host",
        "unexpected cluster id",
    )
    _assert(
        report["first_slice"] == "outside-control-shell-operator",
        "unexpected first slice id",
    )
    _assert(report["audit_only"] is True, "outside control shell slice should stay audit-only")
    _assert(report["observer_only"] is True, "outside control shell slice should stay observer-only")
    _assert(report["do_not_promote"] is True, "outside control shell slice should stay non-promotable")
    _assert(
        report["source_ref_status"]["session_doc"]["exists"] is True,
        "session doc should exist",
    )
    _assert(
        report["interactive_shell_capability"]["interactive_shell_example_present"] is True,
        "interactive shell example should exist",
    )
    _assert(
        report["mom_workspace_boundary"]["boundary_only"] is True,
        "mom boundary should stay boundary-only",
    )
    _assert(
        report["message_counts"].get("assistant", 0) > 0,
        "assistant messages were not counted",
    )
    _assert(
        packet["allow_read_only_slice"] is True,
        "outside control shell packet should allow the bounded read-only slice",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "outside_shell.json"
        md_path = Path(tmpdir) / "outside_shell.md"
        packet_path = Path(tmpdir) / "outside_shell.packet.json"
        emitted = run_outside_control_shell_operator(
            {
                "repo": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "outside shell json was not written")
        _assert(md_path.exists(), "outside shell markdown was not written")
        _assert(packet_path.exists(), "outside shell packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected report json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected report md path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected packet path")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/outside_control_shell_operator.py": (
                lambda ctx: "outside-control-shell-operator-dispatch"
            ),
        }
    )
    outside_shell_skills = reg.find_relevant(
        trust_zone="A2_LOW_CONTROL",
        graph_family="runtime",
        tags_any=["outside-control-shell"],
    )
    _assert(
        any(skill.skill_id == "outside-control-shell-operator" for skill in outside_shell_skills),
        "outside-control-shell-operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        outside_shell_skills,
        ["outside-control-shell-operator"],
        runtime_model="shell",
    )
    _assert(
        selected == "outside-control-shell-operator",
        f"unexpected outside control shell selection: {selected}",
    )
    _assert(not fallback, "outside-control-shell-operator unexpectedly fell back")
    _assert(dispatch is not None, "outside-control-shell-operator dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected outside control shell reason: {reason}")

    print("PASS: outside control shell operator smoke")


if __name__ == "__main__":
    main()
