"""Smoke test for the bounded outer session ledger operator."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills import run_real_ratchet as rr
from system_v4.skills.outer_session_ledger import build_outer_session_ledger, run_outer_session_ledger
from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    state, report, event = build_outer_session_ledger(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected ledger status: {report['status']}")
    _assert(
        report["cluster_id"] == "SKILL_CLUSTER::outer-session-durability",
        "unexpected cluster id",
    )
    _assert(report["first_slice"] == "outer-session-ledger", "unexpected first slice id")
    _assert(report["observer_only"] is True, "ledger should stay observer-only")
    _assert(state["session_id"], "ledger should identify a current session")
    _assert(state["resume_supported"] is True, "current prompt-stack session should be resumable")
    _assert(event["session_id"] == state["session_id"], "event should mirror state session_id")

    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "outer_session_ledger.state.json"
        events_path = Path(tmpdir) / "outer_session_ledger.events.jsonl"
        report_json_path = Path(tmpdir) / "outer_session_ledger.report.json"
        report_md_path = Path(tmpdir) / "outer_session_ledger.report.md"
        emitted = run_outer_session_ledger(
            {
                "repo": str(REPO_ROOT),
                "state_path": str(state_path),
                "events_path": str(events_path),
                "report_json_path": str(report_json_path),
                "report_md_path": str(report_md_path),
            }
        )
        _assert(state_path.exists(), "outer session ledger state was not written")
        _assert(events_path.exists(), "outer session ledger event log was not written")
        _assert(report_json_path.exists(), "outer session ledger json report was not written")
        _assert(report_md_path.exists(), "outer session ledger markdown report was not written")
        _assert(emitted["state_path"] == str(state_path), "unexpected state path")
        _assert(emitted["events_path"] == str(events_path), "unexpected events path")
        event_lines = [line for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        _assert(len(event_lines) == 1, "expected exactly one appended event line")
        event_payload = json.loads(event_lines[0])
        _assert(
            event_payload["first_slice"] == "outer-session-ledger",
            "unexpected event slice id",
        )

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/outer_session_ledger.py": lambda ctx: "outer-session-ledger-dispatch",
        }
    )
    ledger_skills = reg.find_relevant(
        trust_zone="A2_LOW_CONTROL",
        graph_family="runtime",
        tags_any=["session-ledger"],
    )
    _assert(
        any(skill.skill_id == "outer-session-ledger" for skill in ledger_skills),
        "outer-session-ledger was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        ledger_skills,
        ["outer-session-ledger"],
        runtime_model="shell",
    )
    _assert(selected == "outer-session-ledger", f"unexpected selection: {selected}")
    _assert(not fallback, "outer-session-ledger unexpectedly fell back")
    _assert(dispatch is not None, "outer-session-ledger dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected selection reason: {reason}")

    print("PASS: outer session ledger smoke")


if __name__ == "__main__":
    main()
