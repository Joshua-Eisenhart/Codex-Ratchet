"""Smoke test for the shared dispatch bootstrap helper."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills import run_real_ratchet as rr
from system_v4.skills.skill_registry import SkillRegistry


EXPECTED_EXECUTION_PATHS = [
    "system_v4/skills/a1_brain.py",
    "system_v4/skills/b_kernel.py",
    "system_v4/skills/runtime_graph_bridge.py",
    "system_v4/skills/a2_source_family_lane_selector_operator.py",
    "system_v4/skills/a2_append_safe_context_shell_audit_operator.py",
    "system_v4/skills/a2_context_spec_workflow_post_shell_selector_operator.py",
    "system_v4/skills/a2_next_state_first_target_context_consumer_proof_operator.py",
    "system_v4/skills/a2_autoresearch_council_runtime_proof_operator.py",
]


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    rr.SKILL_DISPATCH.clear()
    rr._register_dispatch()
    first_count = len(rr.SKILL_DISPATCH)
    _assert(first_count > 0, "dispatch bootstrap produced an empty table")

    for path in EXPECTED_EXECUTION_PATHS:
        _assert(path in rr.SKILL_DISPATCH, f"expected dispatch path missing: {path}")

    reg = SkillRegistry(str(REPO_ROOT))
    for skill_id in [
        "a2-source-family-lane-selector-operator",
        "a2-append-safe-context-shell-audit-operator",
        "a2-context-spec-workflow-post-shell-selector-operator",
        "a2-next-state-first-target-context-consumer-proof-operator",
        "a2-autoresearch-council-runtime-proof-operator",
    ]:
        adapter_info = reg.export_for_model(skill_id, model="shell")
        _assert(adapter_info is not None, f"adapter export missing for {skill_id}")
        execution_path = adapter_info["execution_path"]
        _assert(execution_path in rr.SKILL_DISPATCH, f"bootstrap missing execution path for {skill_id}")

    rr.SKILL_DISPATCH.clear()
    selector_skills = reg.find_relevant(
        trust_zone="A2_MID_REFINEMENT",
        graph_family="runtime",
        tags_any=["source-family-selector"],
    )
    selected, fallback, _, dispatch, reason = rr.resolve_phase_binding(
        reg,
        selector_skills,
        ["a2-source-family-lane-selector-operator"],
        runtime_model="shell",
    )
    _assert(selected == "a2-source-family-lane-selector-operator", "lazy bootstrap selected wrong skill")
    _assert(not fallback, "lazy bootstrap unexpectedly fell back")
    _assert(dispatch is not None, "lazy bootstrap did not resolve dispatch binding")
    _assert(reason == "dispatch-table", f"unexpected lazy bootstrap reason: {reason}")
    _assert(rr.SKILL_DISPATCH, "lazy bootstrap left dispatch table empty")

    # Idempotence matters for maintenance tooling and repeated audits.
    rr._register_dispatch()
    second_count = len(rr.SKILL_DISPATCH)
    _assert(second_count == first_count, "dispatch bootstrap is not idempotent")

    print("PASS: dispatch bootstrap helper smoke")


if __name__ == "__main__":
    main()
