"""Smoke test for the bounded tracked-work operator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.a2_tracked_work_operator import (
    build_a2_tracked_work_report,
    run_a2_tracked_work,
)
from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report = build_a2_tracked_work_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected tracked work status: {report['status']}")
    _assert(
        report["current_cluster"] == "SKILL_CLUSTER::tracked-work-planning",
        "unexpected current cluster",
    )
    _assert(
        report["current_first_slice"] == "a2-tracked-work-operator",
        "unexpected current first slice",
    )
    _assert(
        report["next_cluster_candidate"] == "",
        "unexpected next cluster candidate",
    )
    _assert(
        report["next_first_slice"] == "",
        "unexpected next first slice",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "tracked.json"
        md_path = Path(tmpdir) / "tracked.md"
        emitted = run_a2_tracked_work(
            {
                "repo": str(REPO_ROOT),
                "report_path": str(json_path),
                "markdown_path": str(md_path),
            }
        )
        _assert(json_path.exists(), "tracked-work json was not written")
        _assert(md_path.exists(), "tracked-work markdown was not written")
        _assert(emitted["report_path"] == str(json_path), "unexpected tracked-work json path")
        _assert(emitted["markdown_path"] == str(md_path), "unexpected tracked-work markdown path")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_tracked_work_operator.py": lambda ctx: "a2-tracked-work-operator-dispatch",
        }
    )
    tracked_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["tracked-work"],
    )
    _assert(
        any(skill.skill_id == "a2-tracked-work-operator" for skill in tracked_skills),
        "a2-tracked-work-operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        tracked_skills,
        ["a2-tracked-work-operator"],
        runtime_model="shell",
    )
    _assert(selected == "a2-tracked-work-operator", f"unexpected tracked-work selection: {selected}")
    _assert(not fallback, "a2-tracked-work-operator unexpectedly fell back")
    _assert(dispatch is not None, "a2-tracked-work-operator dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected tracked-work reason: {reason}")

    print("PASS: a2 tracked work operator smoke")


if __name__ == "__main__":
    main()
