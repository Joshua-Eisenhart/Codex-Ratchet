"""Smoke test for the bounded next-state/directive signal probe operator."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.a2_next_state_directive_signal_probe_operator import (
    build_a2_next_state_directive_signal_probe_report,
    run_a2_next_state_directive_signal_probe,
)
from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        next_state_audit_path = root / "next_state_audit.json"
        witness_path = root / "witness.json"
        readiness_path = root / "readiness.json"

        _write_json(next_state_audit_path, {"status": "ok"})
        _write_json(readiness_path, {"status": "ok"})
        _write_json(
            witness_path,
            [
                {
                    "recorded_at": "2026-03-21T20:00:00Z",
                    "witness": {
                        "kind": "negative",
                        "passed": False,
                        "violations": ["BAD_TRANSITION"],
                        "touched_boundaries": ["frontier"],
                        "trace": [
                            {
                                "at": "2026-03-21T20:00:00Z",
                                "op": "apply_probe",
                                "before_hash": "aaa",
                                "after_hash": "bbb",
                                "notes": ["Should keep the witness note but replace the stale dispatch path."],
                            }
                        ],
                    },
                    "tags": {"source": "system"},
                }
            ],
        )

        report, packet = build_a2_next_state_directive_signal_probe_report(
            root,
            {
                "next_state_audit_path": str(next_state_audit_path),
                "witness_path": str(witness_path),
                "readiness_report_path": str(readiness_path),
            },
        )
        _assert(report["status"] == "ok", f"unexpected probe status: {report['status']}")
        _assert(
            report["cluster_id"] == "SKILL_CLUSTER::next-state-signal-adaptation",
            "unexpected cluster id",
        )
        _assert(
            report["signal_counts"]["next_state_candidate_count"] == 1,
            "expected one next-state candidate",
        )
        _assert(
            report["signal_counts"]["directive_signal_count"] == 1,
            "expected one directive signal",
        )
        _assert(
            packet["allow_improver_follow_on"] is True,
            "synthetic probe should allow bounded improver follow-on",
        )

    repo_report, _ = build_a2_next_state_directive_signal_probe_report(REPO_ROOT)
    _assert(
        repo_report["status"] == "attention_required",
        "live repo should currently stay attention_required until richer witness signals exist",
    )
    _assert(
        repo_report["gate"]["recommended_next_step"] == "record_real_post_action_witnesses_first",
        "unexpected live repo next step",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        next_state_audit_path = root / "next_state_audit.json"
        witness_path = root / "witness.json"
        readiness_path = root / "readiness.json"
        _write_json(next_state_audit_path, {"status": "ok"})
        _write_json(readiness_path, {"status": "ok"})
        _write_json(
            witness_path,
            [
                {
                    "recorded_at": "2026-03-21T20:00:00Z",
                    "witness": {
                        "kind": "negative",
                        "passed": False,
                        "violations": ["BAD_TRANSITION"],
                        "touched_boundaries": ["frontier"],
                        "trace": [
                            {
                                "at": "2026-03-21T20:00:00Z",
                                "op": "apply_probe",
                                "before_hash": "aaa",
                                "after_hash": "bbb",
                                "notes": ["Should keep the witness note but replace the stale dispatch path."],
                            }
                        ],
                    },
                    "tags": {"source": "system"},
                }
            ],
        )
        json_path = root / "probe.json"
        md_path = root / "probe.md"
        packet_path = root / "probe.packet.json"
        emitted = run_a2_next_state_directive_signal_probe(
            {
                "repo": str(root),
                "next_state_audit_path": str(next_state_audit_path),
                "witness_path": str(witness_path),
                "readiness_report_path": str(readiness_path),
                "report_path": str(json_path),
                "markdown_path": str(md_path),
                "packet_path": str(packet_path),
            }
        )
        _assert(json_path.exists(), "probe json was not written")
        _assert(md_path.exists(), "probe markdown was not written")
        _assert(packet_path.exists(), "probe packet was not written")
        _assert(emitted["report_path"] == str(json_path), "unexpected probe json path")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_next_state_directive_signal_probe_operator.py": (
                lambda ctx: "a2-next-state-directive-signal-probe-operator-dispatch"
            ),
        }
    )
    probe_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["next-state-signal-probe"],
    )
    _assert(
        any(skill.skill_id == "a2-next-state-directive-signal-probe-operator" for skill in probe_skills),
        "a2-next-state-directive-signal-probe-operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        probe_skills,
        ["a2-next-state-directive-signal-probe-operator"],
        runtime_model="shell",
    )
    _assert(
        selected == "a2-next-state-directive-signal-probe-operator",
        f"unexpected probe selection: {selected}",
    )
    _assert(not fallback, "probe operator unexpectedly fell back")
    _assert(dispatch is not None, "probe dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected probe reason: {reason}")

    print("PASS: a2 next-state directive signal probe operator smoke")


if __name__ == "__main__":
    main()
