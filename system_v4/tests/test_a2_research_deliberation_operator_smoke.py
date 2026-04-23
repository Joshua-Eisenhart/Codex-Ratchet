"""Smoke test for the bounded research/deliberation operator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.runners import run_real_ratchet as rr
from system_v4.skills.a2_research_deliberation_operator import (
    build_a2_research_deliberation_report,
    run_a2_research_deliberation,
)
from system_v4.skills.runtime_state_kernel import RuntimeState
from system_v4.skills.skill_registry import SkillRegistry


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _generator(state: RuntimeState) -> list[RuntimeState]:
    value = float(state.dof.get("val", 0.0))
    return [
        RuntimeState(region=f"cand_{value + 0.2:.2f}", dof={"val": value + 0.2}),
        RuntimeState(region=f"cand_{value + 0.1:.2f}", dof={"val": value + 0.1}),
        RuntimeState(region=f"cand_{value - 0.1:.2f}", dof={"val": value - 0.1}),
    ]


def main() -> None:
    seed = RuntimeState(region="seed", dof={"val": 0.4})
    report = build_a2_research_deliberation_report(
        REPO_ROOT,
        {
            "question": "choose a stable motif",
            "state": seed,
            "generator": _generator,
            "evaluator": lambda state: float(state.dof.get("val", 0.0)),
            "random_seed": 42,
            "consensus_threshold": 0.34,
        },
    )
    _assert(report["status"] == "ok", f"unexpected report status: {report['status']}")
    _assert(
        report["cluster_id"] == "SKILL_CLUSTER::research-deliberation",
        "unexpected cluster id",
    )
    _assert(report["execution"]["used_autoresearch"], "autoresearch was not used")
    _assert(report["execution"]["used_llm_council"], "llm council was not used")
    _assert(report["execution"]["candidate_count"] >= 1, "no candidates were produced")

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "research_deliberation.json"
        md_path = Path(tmpdir) / "research_deliberation.md"
        emitted = run_a2_research_deliberation(
            {
                "repo": str(REPO_ROOT),
                "question": "choose a stable motif",
                "state": seed,
                "generator": _generator,
                "evaluator": lambda state: float(state.dof.get("val", 0.0)),
                "random_seed": 42,
                "consensus_threshold": 0.34,
                "report_path": str(json_path),
                "markdown_path": str(md_path),
            }
        )
        _assert(json_path.exists(), "research/deliberation json was not written")
        _assert(md_path.exists(), "research/deliberation markdown was not written")
        _assert(emitted["report_path"] == str(json_path), "unexpected report path")
        _assert(emitted["markdown_path"] == str(md_path), "unexpected markdown path")

    reg = SkillRegistry(str(REPO_ROOT))
    rr.SKILL_DISPATCH.clear()
    rr.SKILL_DISPATCH.update(
        {
            "system_v4/skills/a2_research_deliberation_operator.py": (
                lambda ctx: "a2-research-deliberation-operator-dispatch"
            ),
        }
    )
    research_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["research-deliberation"],
    )
    _assert(
        any(skill.skill_id == "a2-research-deliberation-operator" for skill in research_skills),
        "a2-research-deliberation-operator was not discoverable by runtime query",
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        research_skills,
        ["a2-research-deliberation-operator"],
        runtime_model="shell",
    )
    _assert(
        selected == "a2-research-deliberation-operator",
        f"unexpected research/deliberation selection: {selected}",
    )
    _assert(not fallback, "a2-research-deliberation-operator unexpectedly fell back")
    _assert(dispatch is not None, "a2-research-deliberation-operator dispatch binding missing")
    _assert(reason == "dispatch-table", f"unexpected research/deliberation reason: {reason}")

    print("PASS: a2 research deliberation operator smoke")


if __name__ == "__main__":
    main()
