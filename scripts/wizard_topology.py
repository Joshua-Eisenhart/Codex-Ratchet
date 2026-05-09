"""Canonical Wizard v4.1 current topology for local harness scripts."""

from __future__ import annotations


FORMAL_CHILDREN: dict[str, list[str]] = {
    "decision.voices_council": ["voice.strategy", "voice.systems", "voice.factory", "voice.feynman", "voice.hume"],
    "decision.six_hats_council": ["six_hat.blue", "six_hat.white", "six_hat.red", "six_hat.black", "six_hat.yellow", "six_hat.green"],
    "decision.experts_council": ["expert.domain_specialist", "expert.operator", "expert.outside_evaluator", "expert.adversarial_reviewer", "expert.standard_checker"],
    "failure.premortem_council": ["premortem.likely_failure", "premortem.dangerous_failure", "premortem.hidden_assumption", "premortem.early_warning", "premortem.revised_plan", "premortem.sim_evidence_corruption"],
    "failure.falsifier_council": ["voice.popper", "voice.pushback", "guard.receipt_audit", "guard.boundary_check", "failure.calibration"],
    "failure.loophole_auditor_council": ["loophole.strategy_under_test", "loophole.evidence_standard", "loophole.find_all", "loophole.fix_plan", "loophole.verify_fixes", "loophole.confidence_status"],
    "follow_up.prompt_voice_council": ["voice.orwell", "voice.strategy", "voice.factory", "voice.hume"],
    "follow_up.lane_council": ["lane.direct", "lane.alternative", "lane.reframe", "lane.back", "lane.wildcard", "lane.all_of_the_above"],
    "follow_up.compile_gate_council": ["compile_gate.target", "compile_gate.action", "compile_gate.owner", "compile_gate.success_check", "compile_gate.stop_condition", "compile_gate.artifact_surface", "compile_gate.status"],
}

ROUTES: tuple[str, ...] = tuple(FORMAL_CHILDREN)
EXPECTED_CURRENT_TOPOLOGY_MEMBERS = 9
assert len(ROUTES) == EXPECTED_CURRENT_TOPOLOGY_MEMBERS

COUNCIL_ORDER = {
    "decision.voices_council": ("Decision", "Voices"),
    "decision.six_hats_council": ("Decision", "Six Hats"),
    "decision.experts_council": ("Decision", "Experts"),
    "failure.premortem_council": ("Failure", "Premortem"),
    "failure.falsifier_council": ("Failure", "Falsifiers"),
    "failure.loophole_auditor_council": ("Failure", "Loophole Auditor"),
    "follow_up.prompt_voice_council": ("Follow-Up", "Prompt Voices"),
    "follow_up.lane_council": ("Follow-Up", "Lanes"),
    "follow_up.compile_gate_council": ("Follow-Up", "Compile Gate"),
}

OBSOLETE_ROUTES = {
    "failure.six_hats_risk_council": "replaced by failure.loophole_auditor_council",
}

assert set(COUNCIL_ORDER) == set(ROUTES)
