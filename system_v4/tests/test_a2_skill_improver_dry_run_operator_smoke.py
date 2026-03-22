"""Smoke test for the bounded skill improver dry-run operator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.a2_skill_improver_dry_run_operator import (
    ALLOWED_TARGETS,
    build_skill_improver_dry_run_report,
    run_a2_skill_improver_dry_run,
)
from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    target_path = REPO_ROOT / ALLOWED_TARGETS["a2-skill-improver-readiness-operator"]["path"]
    original_code = target_path.read_text(encoding="utf-8")
    candidate_code = original_code + "\n# dry-run candidate marker\n"

    report, packet = build_skill_improver_dry_run_report(
        REPO_ROOT,
        {
            "target_skill_id": "a2-skill-improver-readiness-operator",
            "candidate_code": candidate_code,
        },
    )
    _assert(report["status"] == "ok", f"unexpected dry-run status: {report['status']}")
    _assert(
        report["cluster_id"] == "SKILL_CLUSTER::a2-skill-truth-maintenance",
        "unexpected cluster id",
    )
    _assert(report["dry_run_only"] is True, "dry-run slice should remain dry-run only")
    _assert(report["do_not_promote"] is True, "dry-run slice should remain non-promotable")
    _assert(
        report["selector_recommended_target_id"] == "a2-skill-improver-readiness-operator",
        "dry-run slice did not pick up the selector recommendation",
    )
    _assert(
        report["selected_target"]["selected_target_id"] == "a2-skill-improver-readiness-operator",
        "unexpected selected target",
    )
    _assert(report["improver_result"]["compile_ok"] is True, "candidate should compile")
    _assert(
        report["improver_result"]["tests_state"] == "passed",
        "candidate-aware first-target smoke should pass",
    )
    _assert(
        report["improver_result"]["write_permitted"] is False,
        "dry-run slice must not permit writeback",
    )
    _assert(
        target_path.read_text(encoding="utf-8") == original_code,
        "dry-run slice mutated the target skill",
    )
    _assert(packet["allow_live_repo_mutation"] is False, "packet should deny live mutation")

    with tempfile.TemporaryDirectory() as td:
        temp_root = Path(td)
        json_path = temp_root / "dry_run.json"
        md_path = temp_root / "dry_run.md"
        packet_path = temp_root / "dry_run.packet.json"
        emitted = run_a2_skill_improver_dry_run(
            {
                "repo": str(REPO_ROOT),
                "target_skill_id": "a2-skill-improver-readiness-operator",
                "candidate_code": candidate_code,
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "dry-run json was not written")
        _assert(md_path.exists(), "dry-run markdown was not written")
        _assert(packet_path.exists(), "dry-run packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected report json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected report md path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected packet path")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_skill_improver_dry_run_operator.py": (
                lambda ctx: "a2-skill-improver-dry-run-operator-dispatch"
            ),
        }
    )
    dry_run_skills = reg.find_relevant(
        trust_zone="A2_LOW_CONTROL",
        graph_family="runtime",
        tags_any=["skill-improver-dry-run"],
    )
    _assert(
        any(skill.skill_id == "a2-skill-improver-dry-run-operator" for skill in dry_run_skills),
        "a2-skill-improver-dry-run-operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        dry_run_skills,
        ["a2-skill-improver-dry-run-operator"],
        runtime_model="shell",
    )
    _assert(
        selected == "a2-skill-improver-dry-run-operator",
        f"unexpected dry-run selection: {selected}",
    )
    _assert(not fallback, "a2-skill-improver-dry-run-operator unexpectedly fell back")
    _assert(dispatch is not None, "a2-skill-improver-dry-run-operator dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected dry-run reason: {reason}")

    print("PASS: a2 skill improver dry run operator smoke")


if __name__ == "__main__":
    main()
