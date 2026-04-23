"""Smoke test for the bounded first-target proof slice of the skill improver."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.a2_skill_improver_first_target_proof_operator import (
    build_skill_improver_first_target_proof_report,
    run_a2_skill_improver_first_target_proof,
)
from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    report, packet = build_skill_improver_first_target_proof_report(REPO_ROOT)
    _assert(report["status"] == "ok", f"unexpected proof status: {report['status']}")
    _assert(
        report["slice_id"] == "a2-skill-improver-first-target-proof-operator",
        "unexpected proof slice id",
    )
    _assert(
        report["target_skill_id"] == "a2-skill-improver-readiness-operator",
        "unexpected proof target",
    )
    _assert(report["proof_completed"] is True, "bounded proof did not complete")
    _assert(
        report["restore_status"]["final_hash_matches_original"] is True,
        "target file was not restored to the original hash",
    )
    _assert(
        report["post_commit_smoke"]["status"] == "passed",
        "target smoke did not pass after gated commit",
    )
    _assert(
        report["post_restore_smoke"]["status"] == "passed",
        "target smoke did not pass after restore",
    )
    _assert(packet["bounded_proof_completed"] is True, "proof packet did not record completion")
    _assert(packet["allow_general_live_mutation"] is False, "proof packet must retain the general gate")

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "proof.json"
        md_path = Path(tmpdir) / "proof.md"
        packet_path = Path(tmpdir) / "proof.packet.json"
        emitted = run_a2_skill_improver_first_target_proof(
            {
                "repo_root": str(REPO_ROOT),
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "proof json was not written")
        _assert(md_path.exists(), "proof markdown was not written")
        _assert(packet_path.exists(), "proof packet was not written")
        _assert(emitted["report_json_path"] == str(json_path), "unexpected proof json path")
        _assert(emitted["report_md_path"] == str(md_path), "unexpected proof md path")
        _assert(emitted["packet_path"] == str(packet_path), "unexpected proof packet path")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_skill_improver_first_target_proof_operator.py": (
                lambda ctx: "a2-skill-improver-first-target-proof-operator-dispatch"
            ),
        }
    )
    proof_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["skill-improver-first-target-proof"],
    )
    _assert(
        any(skill.skill_id == "a2-skill-improver-first-target-proof-operator" for skill in proof_skills),
        "proof operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        proof_skills,
        ["a2-skill-improver-first-target-proof-operator"],
        runtime_model="shell",
    )
    _assert(
        selected == "a2-skill-improver-first-target-proof-operator",
        f"unexpected proof selection: {selected}",
    )
    _assert(not fallback, "proof operator unexpectedly fell back")
    _assert(dispatch is not None, "proof operator dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected proof reason: {reason}")

    print("PASS: a2 skill improver first target proof operator smoke")


if __name__ == "__main__":
    main()
