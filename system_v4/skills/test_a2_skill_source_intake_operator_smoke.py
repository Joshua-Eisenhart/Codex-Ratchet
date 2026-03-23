"""Smoke test for the first A2 skill-source intake operator slice."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills import run_real_ratchet as rr
from system_v4.skills.a2_skill_source_intake_operator import (
    build_a2_skill_source_intake_report,
    run_a2_skill_source_intake,
)
from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report = build_a2_skill_source_intake_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected intake report status: {report['status']}")
    counts = report["lev_os_agents"]["skill_doc_counts"]
    _assert(counts["total"] == 635, f"unexpected total lev-os/agents count: {counts['total']}")
    _assert(counts["curated"] == 61, f"unexpected curated lev-os/agents count: {counts['curated']}")
    _assert(counts["library"] == 574, f"unexpected library lev-os/agents count: {counts['library']}")

    front_door = report["front_door"]
    for key in (
        "skill_source_corpus",
        "repo_skill_integration_tracker",
        "skill_candidates_backlog",
        "local_source_repo_inventory",
    ):
        _assert(front_door[key]["exists"], f"missing front-door doc: {key}")
        _assert(front_door[key]["indexed_in_a2"], f"front-door doc not indexed in A2: {key}")
    _assert(
        report["lev_os_agents"]["member_classification"]["lev-intake"]["classification"] == "adapt",
        "lev-intake classification missing or incorrect",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "intake.json"
        md_path = Path(tmpdir) / "intake.md"
        emitted = run_a2_skill_source_intake(
            {
                "repo": str(REPO_ROOT),
                "report_path": str(json_path),
                "markdown_path": str(md_path),
            }
        )
        _assert(json_path.exists(), "json intake report was not written")
        _assert(md_path.exists(), "markdown intake report was not written")
        _assert(emitted["report_path"] == str(json_path), "unexpected json report path")
        _assert(emitted["markdown_path"] == str(md_path), "unexpected markdown report path")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_skill_source_intake_operator.py": lambda ctx: "a2-skill-source-intake-operator-dispatch",
        }
    )

    intake_skills = reg.find_relevant(
        trust_zone="A2_HIGH_INTAKE",
        graph_family="runtime",
        tags_any=["source-intake"],
    )
    _assert(
        any(skill.skill_id == "a2-skill-source-intake-operator" for skill in intake_skills),
        "a2-skill-source-intake-operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        intake_skills,
        ["a2-skill-source-intake-operator"],
        runtime_model="shell",
    )
    _assert(selected == "a2-skill-source-intake-operator", f"unexpected intake selection: {selected}")
    _assert(not fallback, "a2-skill-source-intake-operator unexpectedly fell back")
    _assert(dispatch is not None, "a2-skill-source-intake-operator dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected intake reason: {reason}")

    print("PASS: a2 skill source intake operator smoke")


if __name__ == "__main__":
    main()
