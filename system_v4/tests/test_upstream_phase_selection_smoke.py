"""
Smoke test for generic upstream phase candidate selection.

This guards the registry contract that generic phase zones should expose the
main builder/operator pair for A1 upstream phases, not correction lanes that
belong to queue-driven side paths.
"""

from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.skill_registry import SkillRegistry
from system_v4.runners.run_real_ratchet import resolve_skill


def _assert_equal(actual, expected, message: str) -> None:
    if actual != expected:
        raise AssertionError(f"{message}: expected {expected!r}, got {actual!r}")


def main() -> None:
    reg = SkillRegistry(".")
    health = reg.health_pass()

    expected = {
        "PHASE_A2_3_INTAKE": ["a2-high-intake-graph-builder"],
        "PHASE_A2_2_CONTRADICTION": ["a2-mid-refinement-graph-builder"],
        "PHASE_A2_1_PROMOTION": ["a2-low-control-graph-builder"],
        "PHASE_A1_ROSETTA": ["a1-jargoned-graph-builder", "a1-rosetta-mapper"],
        "PHASE_A1_STRIPPER": ["a1-rosetta-stripper", "a1-stripped-graph-builder"],
        "PHASE_A1_CARTRIDGE": ["a1-cartridge-assembler"],
    }
    owner_expected = {
        "PHASE_A2_3_INTAKE": ["a2-high-intake-graph-builder"],
        "PHASE_A2_2_CONTRADICTION": ["a2-mid-refinement-graph-builder"],
        "PHASE_A2_1_PROMOTION": ["a2-low-control-graph-builder"],
        "PHASE_A1_ROSETTA": ["a1-jargoned-graph-builder"],
        "PHASE_A1_STRIPPER": ["a1-stripped-graph-builder"],
        "PHASE_A1_CARTRIDGE": [],
    }

    print("Upstream phase selection smoke")
    _assert_equal(
        health["phase_zone_non_runner"],
        [],
        "phase zones should not be assigned to non-runners",
    )
    _assert_equal(
        health["phase_runner_missing_exec"],
        [],
        "phase runners should resolve to a Python execution target",
    )
    _assert_equal(
        health["phase_handler_missing_generic_flag"],
        [],
        "generic phase handlers should carry is_generic_phase_handler",
    )
    _assert_equal(
        health["generic_phase_handler_missing_zone"],
        [],
        "generic phase handlers should remain bound to at least one PHASE_* zone",
    )
    _assert_equal(
        health["owner_graph_builder_missing_output"],
        [],
        "owner graph builders should declare graph outputs",
    )
    _assert_equal(
        health["owner_graph_builder_non_writer"],
        [],
        "owner graph builders should be repo writers",
    )
    _assert_equal(
        health["phase_graph_builder_missing_builder_flag"],
        [],
        "phase graph builders should carry is_owner_graph_builder",
    )
    for phase, expected_ids in expected.items():
        candidates = reg.find_relevant(
            layer_id=phase,
            capabilities_all=["is_phase_runner", "is_generic_phase_handler"],
        )
        actual_ids = [
            skill.skill_id
            for skill in candidates
        ]
        _assert_equal(actual_ids, expected_ids, f"candidate set mismatch for {phase}")
        print(f"PASS {phase}: {actual_ids}")

    for phase, expected_ids in owner_expected.items():
        owner_ids = [
            skill.skill_id
            for skill in reg.find_relevant(
                layer_id=phase,
                capabilities_all=[
                    "is_phase_runner",
                    "is_generic_phase_handler",
                    "is_owner_graph_builder",
                ],
            )
        ]
        _assert_equal(
            owner_ids,
            expected_ids,
            f"owner graph builder mismatch for {phase}",
        )
        print(f"PASS {phase} owner builders: {owner_ids}")

    rosetta_selected, rosetta_fallback = resolve_skill(
        reg.find_relevant(
            layer_id="PHASE_A1_ROSETTA",
            capabilities_all=["is_phase_runner", "is_generic_phase_handler"],
        ),
        ["a1-jargoned-graph-builder", "a1-rosetta-mapper"],
    )
    _assert_equal(
        (rosetta_selected, rosetta_fallback),
        ("a1-jargoned-graph-builder", False),
        "PHASE_A1_ROSETTA should prefer the jargoned graph builder",
    )

    stripper_selected, stripper_fallback = resolve_skill(
        reg.find_relevant(
            layer_id="PHASE_A1_STRIPPER",
            capabilities_all=["is_phase_runner", "is_generic_phase_handler"],
        ),
        ["a1-stripped-graph-builder", "a1-rosetta-stripper"],
    )
    _assert_equal(
        (stripper_selected, stripper_fallback),
        ("a1-stripped-graph-builder", False),
        "PHASE_A1_STRIPPER should prefer the stripped graph builder",
    )
    cartridge_selected, cartridge_fallback = resolve_skill(
        reg.find_relevant(
            layer_id="PHASE_A1_CARTRIDGE",
            capabilities_all=["is_phase_runner", "is_generic_phase_handler"],
        ),
        ["a1-cartridge-graph-builder", "a1-cartridge-assembler", "a1-brain"],
    )
    _assert_equal(
        (cartridge_selected, cartridge_fallback),
        ("a1-cartridge-assembler", False),
        "PHASE_A1_CARTRIDGE should currently prefer the assembler until a phase-bound owner builder exists",
    )
    print(f"PASS PHASE_A1_ROSETTA selection: {rosetta_selected}")
    print(f"PASS PHASE_A1_STRIPPER selection: {stripper_selected}")
    print(f"PASS PHASE_A1_CARTRIDGE selection: {cartridge_selected}")


if __name__ == "__main__":
    main()
