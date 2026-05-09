"""Wizard v4.2 topology: councils are stages, parents are work routes, voices are children."""

from __future__ import annotations


FORMAL_CHILDREN: dict[str, list[str]] = {
    "decision.context_strategy": ["voice.strategy", "voice.systems", "voice.hume", "voice.feynman"],
    "decision.move_selection": ["voice.factory", "voice.orwell", "voice.hume", "lane.direct", "lane.alternative"],
    "decision.evidence_boundary": ["voice.hume", "voice.popper", "voice.feynman", "guard.receipt_audit"],
    "failure.premortem": ["skill.premortem", "voice.hume", "voice.factory", "voice.systems"],
    "failure.falsifier": ["voice.popper", "voice.pushback", "voice.feynman", "guard.boundary_check"],
    "failure.loophole_auditor": ["skill.loophole_auditor", "voice.strategy", "voice.systems", "voice.hume"],
    "follow_up.next_move_selector": ["voice.strategy", "voice.factory", "voice.orwell", "voice.hume"],
    "follow_up.lane_builder": ["lane.direct", "lane.reframe", "lane.back", "lane.wildcard", "lane.all_of_the_above"],
    "follow_up.compile_gate": [
        "compile_gate.target",
        "compile_gate.action",
        "compile_gate.owner",
        "compile_gate.success_check",
        "compile_gate.stop_condition",
        "compile_gate.artifact_surface",
        "compile_gate.status",
    ],
    "manager.run_controller": ["manager.sequence_gate", "manager.wave_boundary", "manager.stop_resume"],
    "manager.child_health": ["manager.liveness_table", "manager.reroute_plan", "manager.capacity_pressure"],
    "manager.route_truth": ["manager.lineage_audit", "manager.full_claim_gate", "manager.missing_obligation"],
    "manager.output_compiler": ["manager.no_log_answer", "manager.section_gate", "manager.human_density"],
    "manager.strategy_memory": ["manager.context_carry", "manager.strategy_state", "manager.overoptimization_risk"],
}

MANAGEMENT_PARENTS: tuple[str, ...] = (
    "manager.run_controller",
    "manager.child_health",
    "manager.route_truth",
    "manager.output_compiler",
    "manager.strategy_memory",
)

COUNCIL_ROUTES: tuple[str, ...] = tuple(route for route in FORMAL_CHILDREN if not route.startswith("manager."))
ROUTES: tuple[str, ...] = tuple(FORMAL_CHILDREN)
EXPECTED_COUNCIL_PARENTS = 9
EXPECTED_MANAGEMENT_PARENTS = 5
EXPECTED_TOTAL_PARENTS = EXPECTED_COUNCIL_PARENTS + EXPECTED_MANAGEMENT_PARENTS

COUNCIL_ORDER = {
    "decision.context_strategy": ("Decision", "Context + Strategy"),
    "decision.move_selection": ("Decision", "Move Selection"),
    "decision.evidence_boundary": ("Decision", "Evidence Boundary"),
    "failure.premortem": ("Failure", "Premortem"),
    "failure.falsifier": ("Failure", "Falsifier"),
    "failure.loophole_auditor": ("Failure", "Loophole Auditor"),
    "follow_up.next_move_selector": ("Follow-Up", "Next-Move Selector"),
    "follow_up.lane_builder": ("Follow-Up", "Lane Builder"),
    "follow_up.compile_gate": ("Follow-Up", "Compile Gate"),
    "manager.run_controller": ("Management", "Run Controller"),
    "manager.child_health": ("Management", "Child Health"),
    "manager.route_truth": ("Management", "Route Truth"),
    "manager.output_compiler": ("Management", "Output Compiler"),
    "manager.strategy_memory": ("Management", "Strategy Memory"),
}

assert len(COUNCIL_ROUTES) == EXPECTED_COUNCIL_PARENTS
assert len(MANAGEMENT_PARENTS) == EXPECTED_MANAGEMENT_PARENTS
assert len(ROUTES) == EXPECTED_TOTAL_PARENTS
assert set(COUNCIL_ORDER) == set(ROUTES)
