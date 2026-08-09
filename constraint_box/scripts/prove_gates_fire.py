#!/usr/bin/env python3
"""Prove every CB gate is real: positive control (targeted refusal with the
expected reason code) AND negative control (clean input stays silent).

A gate is proven real only if BOTH controls hold.  A gate that never refuses
is decorative; a gate that refuses everything is equally useless.  Either way
it is reported, never smoothed.

Run:
    PYTHONPATH=constraint_box/src \
      /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
      constraint_box/scripts/prove_gates_fire.py

Everything here only ADDS controls.  No gate, check, bound, assertion or test
in the package is modified.  Fixtures are materialized deterministically under
constraint_box/fixtures/gate_controls/ so they are inspectable; scratch output
(ledgers, run dirs, consumer outputs) goes to a temp dir, never the repo.

Claim ceiling: control outcomes about gate refusal behavior on fixture inputs
only.  promotion_allowed: false.  No scientific, canonical, or release claim.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace

BOX_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = BOX_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from constraintbox import agentrun  # noqa: E402
from constraintbox import gate_operations as gops  # noqa: E402
from constraintbox.contracts import Disposition, TaskRequest  # noqa: E402
from constraintbox.controller import (  # noqa: E402
    AgentProposalProfile,
    ConstraintBoxController,
)
from constraintbox.discharge import Observation, PASS, discharge  # noqa: E402
from constraintbox.flow_termination import spinning_control_policy  # noqa: E402
from constraintbox.gate import run_gate  # noqa: E402
from constraintbox.intake import IntakeError, parse_json_object  # noqa: E402
from constraintbox.model_tier_budget import (  # noqa: E402
    model_tier_reasons,
    tier_for_slug,
)
from constraintbox.mini_levos import (  # noqa: E402
    FlowNode,
    FlowPolicy,
    FlowTransition,
    HookKind,
    HookRegistration,
    HookResult,
    HookSignal,
    MiniLevError,
    MiniLevRuntime,
    handler_code_sha256,
)
from constraintbox.proposal_minilev_flow import reference_flow_policy  # noqa: E402
from constraintbox.user_request import assess_user_request  # noqa: E402

FIXTURES = BOX_ROOT / "fixtures" / "gate_controls"
RECEIPT_PATH = BOX_ROOT / "receipts" / "gate_fire_proof_v1.json"
SCRATCH = Path(tempfile.mkdtemp(prefix="prove_gates_fire_"))
MODEL_REQUESTED = "gpt-5.6-luna"

_counter = [0]


def _fresh_dir(label: str) -> Path:
    _counter[0] += 1
    path = SCRATCH / f"{label}-{_counter[0]}"
    path.mkdir(parents=True)
    return path


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _write_fixture(name: str, body) -> Path:
    path = FIXTURES / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(body, bytes):
        path.write_bytes(body)
    else:
        path.write_text(json.dumps(body, indent=1, sort_keys=True) + "\n")
    return path


# ---------------------------------------------------------------------------
# Mini-Lev hooks for construction-invariant controls.  Module-level functions
# with this file as their pinned source, exactly as the kernel requires.
# ---------------------------------------------------------------------------

def control_pass_gate(_context):
    return HookResult(HookSignal.PASS, {"status": "pass"})


def control_pass_blocked_gate(_context):
    return HookResult(HookSignal.PASS, {"status": "pass"})


def _registration(hook_id, handler, allowed_signals):
    source_path = Path(__file__).resolve()
    return HookRegistration(
        hook_id=hook_id,
        kind=HookKind.GATE,
        handler=handler,
        source_path=source_path,
        source_sha256=_sha256_bytes(source_path.read_bytes()),
        code_sha256=handler_code_sha256(handler),
        allowed_signals=allowed_signals,
        allowed_update_keys=(),
        max_output_bytes=65_536,
    )


def _policy(nodes, transitions, terminals, *, entry, required):
    return FlowPolicy(
        flow_id="gate-control-flow",
        entry_node=entry,
        nodes=nodes,
        transitions=transitions,
        terminal_nodes=terminals,
        required_nodes=required,
        max_steps=8,
        max_visits_per_node=8,
        max_retries=2,
        max_context_bytes=8_192,
        max_event_bytes=16_384,
        max_receipt_bytes=262_144,
        claim_ceiling="bounded gate-control construction test only",
    )


def _construct(policy, registrations, label):
    """Attempt MiniLevRuntime construction; return (raised, message)."""
    try:
        MiniLevRuntime(
            policy,
            registrations,
            run_id=f"gate-control-{label}",
            ledger_path=_fresh_dir("minilev") / "ledger.jsonl",
        )
    except MiniLevError as exc:
        return True, str(exc)
    return False, "constructed without refusal"


# ---------------------------------------------------------------------------
# Proposal-gate pipeline: the REAL agentrun functions, end to end, with one
# targeted mutation per control.  Nothing is stubbed except the provider
# receipt object, whose fields are exactly what the run path reads from it.
# ---------------------------------------------------------------------------

def _clean_proposal(evidence_ref: str) -> dict:
    return {
        "proposal_id": "gate-control-proposal-1",
        "candidate": {
            "requested_claim": agentrun.ALLOWED_CLAIM,
            "evidence_ref": evidence_ref,
        },
        "falsifiers": ["the tool receipt digest changes on a fresh rerun"],
    }


def run_proposal_pipeline(
    raw: bytes,
    *,
    evidence_ref: str,
    receipt_status: str = "success",
    model_resolved="gpt-5.6-luna",
    has_tool_calls: bool = False,
    provider_admitted: bool = True,
    tool_errors=(),
    observation_age_seconds: float = 0.0,
) -> dict:
    """Recompute the proposal-gate verdict from raw parts with the real code."""

    receipt = SimpleNamespace(
        status=receipt_status,
        model_resolved=model_resolved,
        has_tool_calls=has_tool_calls,
        content=raw.decode("utf-8", errors="replace"),
    )
    extracted_raw, tool_use, extraction_errors, _warnings = (
        agentrun._extract_proposal(receipt, SCRATCH / "unused-events.jsonl")
    )
    try:
        proposal = parse_json_object(extracted_raw)
    except IntakeError:
        proposal = None
    shape_errors = agentrun._proposal_shape_errors(proposal)
    controller = ConstraintBoxController(
        {agentrun.PROPOSAL_TASK_KIND: AgentProposalProfile()},
        _fresh_dir("controller"),
    )
    decision = controller.run(
        TaskRequest(
            agentrun.PROPOSAL_TASK_KIND,
            extracted_raw,
            "gate-control-attempt-1",
        )
    )
    # Everything below mirrors proposal_gate_callback line for line.  The
    # real callback performs candidate.get(...) BEFORE _reason_codes runs, so
    # a proposal whose candidate is not a dict crashes the run path instead
    # of emitting PROPOSAL_CANDIDATE_INVALID.  A crash here is recorded as
    # RUN_PATH_CRASH, never smoothed into a reason code the path cannot emit.
    try:
        return _pipeline_tail(
            proposal, shape_errors, decision, receipt, extracted_raw,
            tool_use, extraction_errors,
            evidence_ref=evidence_ref,
            provider_admitted=provider_admitted,
            tool_errors=tool_errors,
            observation_age_seconds=observation_age_seconds,
            model_resolved=model_resolved,
        )
    except Exception as exc:  # noqa: BLE001 - measured, reported, not smoothed
        return {
            "reasons": [f"RUN_PATH_CRASH:{type(exc).__name__}:{exc}"],
            "discharge_status": "NOT_REACHED",
            "release_safety": None,
            "smt_settled": None,
            "smt_admitted": None,
            "decision": decision.disposition.value,
        }


def _pipeline_tail(
    proposal, shape_errors, decision, receipt, extracted_raw, tool_use,
    extraction_errors, *, evidence_ref, provider_admitted, tool_errors,
    observation_age_seconds, model_resolved,
) -> dict:
    candidate = proposal.get("candidate", {}) if proposal else {}
    observed = {
        "provider_receipt_admitted": provider_admitted,
        "provider_tool_free": not tool_use,
        "strict_intake_eligible": decision.disposition is Disposition.ELIGIBLE,
        "proposal_schema_valid": not shape_errors,
        "evidence_ref_matches": candidate.get("evidence_ref") == evidence_ref,
        "falsifier_present": bool(
            proposal
            and isinstance(proposal.get("falsifiers"), list)
            and proposal["falsifiers"]
        ),
        "tool_profile_ready": True,
        "tool_controls_complete": True,
        "tool_operation_bound": True,
        "requested_claim": candidate.get("requested_claim", ""),
    }
    smt = agentrun._smt_gate(observed)
    observed["smt_settled"] = smt["settled"]
    observed["smt_proposal_admitted"] = smt["proposal_admitted"]
    now = time.time()
    decided_at = now - float(observation_age_seconds)
    settlement = discharge(
        agentrun._policy(),
        {
            name: Observation(value, decided_at, "prove-gates-fire")
            for name, value in observed.items()
        },
        now=now,
    )
    release_safety = agentrun._release_safety(
        raw=extracted_raw,
        provider_admitted=provider_admitted,
        tool_use=tool_use,
        decision=decision,
        evidence_ref=evidence_ref,
        tool_errors=list(tool_errors),
        smt=smt,
        model_requested=MODEL_REQUESTED,
        model_resolved=model_resolved,
    )
    reasons = agentrun._reason_codes(
        receipt=receipt,
        provider_admitted=provider_admitted,
        tool_use=tool_use,
        extraction_errors=extraction_errors,
        decision=decision,
        shape_errors=shape_errors,
        proposal=proposal,
        evidence_ref=evidence_ref,
        smt=smt,
        discharge_status=settlement.status,
        release_safety=release_safety,
        model_requested=MODEL_REQUESTED,
    )
    return {
        "reasons": reasons,
        "discharge_status": settlement.status,
        "release_safety": release_safety,
        "smt_settled": smt["settled"],
        "smt_admitted": smt["proposal_admitted"],
        "decision": decision.disposition.value,
    }


def _probe_smt_unavailable(evidence_ref: str) -> None:
    """Subprocess mode: run the clean pipeline with cvc5 genuinely absent."""
    raw = json.dumps(_clean_proposal(evidence_ref)).encode("utf-8")
    outcome = run_proposal_pipeline(raw, evidence_ref=evidence_ref)
    print(json.dumps(outcome))


# ---------------------------------------------------------------------------
# Control harness
# ---------------------------------------------------------------------------

RESULTS: list[dict] = []


def record(gate_id, kind, positive_marker, positive_fired, positive_observed,
           negative_fired, negative_observed, note=""):
    if negative_fired:
        classification = "always_fires"
    elif not positive_fired:
        classification = "never_fires"
    else:
        classification = "proven_real"
    RESULTS.append(
        {
            "gate": gate_id,
            "kind": kind,
            "positive_marker": positive_marker,
            "positive_fired": positive_fired,
            "positive_observed": positive_observed,
            "negative_fired": negative_fired,
            "negative_observed": negative_observed,
            "classification": classification,
            "note": note,
        }
    )


def main() -> int:
    if "--probe-smt-unavailable" in sys.argv:
        _probe_smt_unavailable(sys.argv[sys.argv.index("--probe-smt-unavailable") + 1])
        return 0

    FIXTURES.mkdir(parents=True, exist_ok=True)
    findings: list[str] = []

    # =====================================================================
    # SECTION 0: model-tier budget gate
    # =====================================================================
    model_tier_policy = json.loads(
        (BOX_ROOT / "config" / "model_tier_policy.json").read_text()
    )
    tier_clean = {"cheap": {"dispatches": 0, "output_tokens": 0}}
    task_id = "prove-gates-fire-task"
    tier_cases = (
        (
            "cb:model-tier-unknown",
            "MODEL_TIER_UNKNOWN",
            dict(
                model_requested="gpt-5.6-luna",
                model_resolved="model-not-listed",
                role="swarm",
                spend={},
                task_id=task_id,
            ),
        ),
        (
            "cb:model-tier-role",
            "MODEL_TIER_ROLE_FORBIDDEN",
            dict(
                model_requested="gpt-5.6-sol",
                model_resolved="gpt-5.6-sol",
                role="swarm",
                spend={},
                task_id=task_id,
            ),
        ),
        (
            "cb:model-tier-ceiling",
            "MODEL_TIER_CEILING_EXHAUSTED",
            dict(
                model_requested="gpt-5.6-sol",
                model_resolved="gpt-5.6-sol",
                role="audit",
                spend={"premium": {"dispatches": 250, "output_tokens": 0}},
                task_id=task_id,
            ),
        ),
        (
            "cb:model-tier-unjustified",
            "MODEL_TIER_ESCALATION_UNJUSTIFIED",
            dict(
                model_requested="gpt-5.6-terra",
                model_resolved="gpt-5.6-terra",
                role="build",
                spend={},
                task_id=task_id,
            ),
        ),
        (
            "cb:model-tier-skips-rung",
            "MODEL_TIER_ESCALATION_SKIPS_RUNG",
            dict(
                model_requested="gpt-5.6-sol",
                model_resolved="gpt-5.6-sol",
                role="audit",
                spend={"_attempts": [{"task_id": task_id, "tier": "cheap", "outcome": "failed"}]},
                task_id=task_id,
            ),
        ),
    )
    for gate_id, expected, kwargs in tier_cases:
        positive = model_tier_reasons(policy=model_tier_policy, **kwargs)
        if expected == "MODEL_TIER_ESCALATION_UNJUSTIFIED":
            negative = model_tier_reasons(
                "gpt-5.6-terra", "gpt-5.6-terra", "build", model_tier_policy,
                {"_attempts": [{"task_id": task_id, "tier": "cheap", "outcome": "failed"}]}, task_id=task_id,
            )
        elif expected == "MODEL_TIER_ESCALATION_SKIPS_RUNG":
            negative = model_tier_reasons(
                "gpt-5.6-sol", "gpt-5.6-sol", "audit", model_tier_policy,
                {"_attempts": [{"task_id": task_id, "tier": "standard", "outcome": "failed"}]}, task_id=task_id,
            )
        elif expected == "MODEL_TIER_CEILING_EXHAUSTED":
            negative = model_tier_reasons(
                "gpt-5.6-sol", "gpt-5.6-sol", "audit", model_tier_policy,
                {"premium": {"dispatches": 249, "output_tokens": 0},
                 "_attempts": [{"task_id": task_id, "tier": "standard", "outcome": "failed"}]}, task_id=task_id,
            )
        elif expected == "MODEL_TIER_ROLE_FORBIDDEN":
            negative = model_tier_reasons(
                "gpt-5.6-luna", "gpt-5.6-luna", "swarm", model_tier_policy,
                tier_clean, task_id=task_id,
            )
        else:
            negative = model_tier_reasons(
                "gpt-5.6-luna", "gpt-5.6-luna", "swarm", model_tier_policy,
                tier_clean, task_id=task_id,
            )
        record(
            gate_id,
            "model_tier_budget",
            expected,
            positive == [expected],
            positive,
            negative != [],
            negative,
            note=(
                f"tier_for_slug(gpt-5.6-luna)={tier_for_slug('gpt-5.6-luna', model_tier_policy)}"
            ),
        )

    # =====================================================================
    # SECTION A: gate_operations cb:* gates
    # =====================================================================

    # --- cb:z3-request-gate / cb:cvc5-request-gate ------------------------
    def eq(var, const):
        return {"op": "eq", "left": {"var": var}, "right": {"const": const}}

    unsat_spec = {
        "variables": {"x": [False, True]},
        "constraints": [eq("x", True), eq("x", False)],
    }
    sat_spec = {
        "variables": {"x": [False, True]},
        "constraints": [eq("x", True)],
    }
    _write_fixture("smt/unsat_spec.json", unsat_spec)
    _write_fixture("smt/sat_spec.json", sat_spec)
    from constraintbox.dualsolve import dual_solve as _dual_solve

    schema_probe = _dual_solve(sat_spec, max_states=100_000)
    for name, fn, key, lines in (
        ("cb:z3-request-gate", gops.gate_z3_request, "z3", "69-77"),
        ("cb:cvc5-request-gate", gops.gate_cvc5_request, "cvc5", "108-116"),
    ):
        pos = fn(json.loads((FIXTURES / "smt/unsat_spec.json").read_text()))
        neg = fn(json.loads((FIXTURES / "smt/sat_spec.json").read_text()))
        note = (
            f"fixed binding at gate_operations.py:{lines}: before type "
            f"dual_solve()['{key}']={type(schema_probe[key]).__name__}; "
            f"after type backend_results['{key}']="
            f"{type(schema_probe['backend_results'][key]).__name__}; "
            f"controls now produce unsat={pos.verdict}/{pos.reason}, "
            f"sat={neg.verdict}/{neg.reason}."
        )
        record(
            name,
            "gate_operations",
            "verdict=BOUNDED_UNSAT",
            pos.verdict == "BOUNDED_UNSAT",
            f"{pos.verdict}/{pos.reason}",
            neg.verdict != "BOUNDED_SAT",
            f"{neg.verdict}/{neg.reason}",
            note=note,
        )

    # --- cb:rustworkx-workflow-gate ---------------------------------------
    good_policy = _policy(
        (FlowNode("gate", "control-pass"), FlowNode("terminal", "control-pass")),
        (FlowTransition("gate", HookSignal.PASS, "terminal"),
         FlowTransition("terminal", HookSignal.PASS, "HOLD")),
        ("HOLD",),
        entry="gate",
        required=(),
    )
    valid = gops.gate_rustworkx_workflow(good_policy)
    bad_entry_policy = _policy(
        (FlowNode("gate", "control-pass"),),
        (FlowTransition("gate", HookSignal.PASS, "RELEASED"),
         FlowTransition("gate", HookSignal.HOLD, "HOLD")),
        ("HOLD", "RELEASED"),
        entry="missing-node",
        required=(),
    )
    bad_entry = gops.gate_rustworkx_workflow(bad_entry_policy)
    invalid = gops.gate_rustworkx_workflow({"not": "a policy"})
    cyclic_policy = _policy(
        (FlowNode("a", "control-pass"), FlowNode("b", "control-pass")),
        (FlowTransition("a", HookSignal.PASS, "b"),
         FlowTransition("b", HookSignal.PASS, "a")),
        ("HOLD",),
        entry="a",
        required=(),
    )
    cyc = gops.gate_rustworkx_workflow(cyclic_policy)
    unreachable_policy = _policy(
        (FlowNode("a", "control-pass"), FlowNode("b", "control-pass")),
        (FlowTransition("a", HookSignal.PASS, "HOLD"),),
        ("HOLD",),
        entry="a",
        required=(),
    )
    unr = gops.gate_rustworkx_workflow(unreachable_policy)
    cyc_note = (
        f"fixed former stub: rustworkx controls valid={valid.verdict}/{valid.reason}, "
        f"cycle={cyc.verdict}/{cyc.reason}, unreachable={unr.verdict}/{unr.reason}; "
        f"malformed controls={bad_entry.verdict}/{bad_entry.reason} and "
        f"{invalid.verdict}/{invalid.reason}."
    )
    record(
        "cb:rustworkx-workflow-gate",
        "gate_operations",
        "verdict=CYCLIC reason=cycle_detected",
        cyc.verdict == "CYCLIC" and cyc.reason == "cycle_detected",
        f"{cyc.verdict}/{cyc.reason}",
        valid.verdict != "ACYCLIC_REACHABLE",
        f"{valid.verdict}/{valid.reason}; unreachable {unr.verdict}/{unr.reason}",
        note=cyc_note,
    )

    # --- cb:sympy-exact-gate (run-path binding) ---------------------------
    cyclic_nonretry = _policy(
        (FlowNode("a", "control-pass"), FlowNode("b", "control-pass")),
        (FlowTransition("a", HookSignal.PASS, "b"),
         FlowTransition("b", HookSignal.PASS, "a")),
        ("HOLD",),
        entry="a",
        required=(),
    )
    pos = gops.gate_sympy_flow_budgets(cyclic_nonretry)
    neg = gops.gate_sympy_flow_budgets(reference_flow_policy())
    record(
        "cb:sympy-exact-gate",
        "gate_operations",
        "verdict=MISMATCH reason=nonretry_edges_are_not_acyclic",
        pos.verdict == "MISMATCH"
        and pos.reason == "nonretry_edges_are_not_acyclic",
        f"{pos.verdict}/{pos.reason}",
        neg.verdict != "VERIFIED",
        f"{neg.verdict}/{neg.reason}",
    )

    # --- cb:maude-transition-gate (run-path binding) ----------------------
    dead_end_policy = _policy(
        (FlowNode("a", "control-pass"), FlowNode("b", "control-pass")),
        (FlowTransition("a", HookSignal.OBSERVED, "b"),),
        ("BLOCKED",),
        entry="a",
        required=(),
    )
    pos = gops.gate_maude_flow_transitions(dead_end_policy)
    neg = gops.gate_maude_flow_transitions(reference_flow_policy())
    record(
        "cb:maude-transition-gate",
        "gate_operations",
        "verdict=MISMATCH reason=confirmed_rewrite_relation_has_unreachable_terminal",
        pos.verdict == "MISMATCH"
        and pos.reason == "confirmed_rewrite_relation_has_unreachable_terminal",
        f"{pos.verdict}/{pos.reason}",
        neg.verdict != "VERIFIED",
        f"{neg.verdict}/{neg.reason}",
    )

    # --- cb:boundary-contract-gate ----------------------------------------
    from constraintbox.boundary_contract import (
        CB_EXTERNAL_ADAPTER_IDS,
        CB_FORMAL_GATE_IDS,
        CB_MINILEV_IDS,
        CB_RUNTIME_IDS,
        EXTERNAL_FORMAL_RUNTIME_IDS,
        EXTERNAL_SIM_PROFILE_IDS,
    )

    clean_contract = {
        "schema": "constraintbox.boundary-contract.v1",
        "report_kind": "constraintbox.product-evidence-status.v1",
        "cb_runtime_ids": sorted(CB_RUNTIME_IDS),
        "cb_formal_gate_ids": sorted(CB_FORMAL_GATE_IDS),
        "cb_minilev_ids": sorted(CB_MINILEV_IDS),
        "cb_external_adapter_ids": sorted(CB_EXTERNAL_ADAPTER_IDS),
        "external_formal_runtime_ids": sorted(EXTERNAL_FORMAL_RUNTIME_IDS),
        "external_sim_profile_ids": sorted(EXTERNAL_SIM_PROFILE_IDS),
        "evidence_receipt_ids": ["evidence:gate-control-receipt-1"],
        "bundle_contains_external_sim_engines": False,
        "external_sim_profiles_are_cb_core": False,
        "evidence_receipts_are_cb_core_components": False,
        "untrusted_llm_role": "proposal_or_advisory_only",
    }
    conflated = dict(clean_contract)
    conflated["external_sim_profiles_are_cb_core"] = True
    clean_path = _write_fixture("boundary/clean_contract.json", clean_contract)
    conflated_path = _write_fixture("boundary/conflated_contract.json", conflated)
    pos = gops.gate_boundary_contract(conflated_path.read_bytes())
    neg = gops.gate_boundary_contract(clean_path.read_bytes())
    boundary_note = (
        "fixed ProfileOutcome binding: before fields were classification/detail; "
        "after fields are reason/evidence. Controls now produce clean "
        f"{neg.verdict}/{neg.reason}, conflated {pos.verdict}/{pos.reason}."
    )
    record(
        "cb:boundary-contract-gate",
        "gate_operations",
        "verdict=FAIL reason=boundary_role_conflation",
        pos.verdict == "FAIL" and pos.reason == "boundary_role_conflation",
        f"{pos.verdict}/{pos.reason}",
        neg.verdict != "PASS",
        f"{neg.verdict}/{neg.reason}",
        note=boundary_note,
    )

    # --- cb:flow-termination-gate -----------------------------------------
    pos = gops.gate_flow_termination(spinning_control_policy())
    neg = gops.gate_flow_termination(reference_flow_policy())
    record(
        "cb:flow-termination-gate",
        "gate_operations",
        "verdict=FAIL reason=budget_free_cycle_detected",
        pos.verdict == "FAIL" and pos.reason == "budget_free_cycle_detected",
        f"{pos.verdict}/{pos.reason}",
        neg.verdict != "PASS",
        f"{neg.verdict}/{neg.reason}",
    )

    # --- cb:false-green-check-gate ----------------------------------------
    clean_receipt = {"schema": "gate-control-false-green.v1", "status": "accepted"}
    risky_receipt = {
        "schema": "gate-control-false-green.v1",
        "status": "accepted",
        "input_sha256": "a" * 64,
        "output_sha256": "b" * 64,
        "output": {"error": "gate output missing"},
    }
    clean_path = _write_fixture("false_green/clean_receipt.json", clean_receipt)
    risky_path = _write_fixture("false_green/empty_output_receipt.json", risky_receipt)
    pos = gops.gate_false_green_check(str(risky_path))
    neg = gops.gate_false_green_check(str(clean_path))
    record(
        "cb:false-green-check-gate",
        "gate_operations",
        "verdict=FAIL reason startswith false_green_risk",
        pos.verdict == "FAIL" and pos.reason.startswith("false_green"),
        f"{pos.verdict}/{pos.reason}",
        neg.verdict != "PASS",
        f"{neg.verdict}/{neg.reason}",
    )

    # --- cb:gate-weakening-detection --------------------------------------
    prev_ledger = {
        "gates": [
            {
                "gate_id": "cb:demo-gate",
                "verdict": "PASS",
                "min_evidence_count": 5,
                "input_sha256": "a" * 64,
                "output_sha256": "b" * 64,
            }
        ]
    }
    weakened_ledger = json.loads(json.dumps(prev_ledger))
    weakened_ledger["gates"][0]["min_evidence_count"] = 1
    nofield_ledger = {
        "gates": [
            {
                "gate_id": "cb:demo-gate",
                "verdict": "PASS",
                "input_sha256": "a" * 64,
                "output_sha256": "b" * 64,
            }
        ]
    }
    prev_path = _write_fixture("weakening/prev_ledger.json", prev_ledger)
    curr_clean_path = _write_fixture("weakening/curr_identical_ledger.json", prev_ledger)
    curr_weak_path = _write_fixture("weakening/curr_weakened_ledger.json", weakened_ledger)
    nofield_prev = _write_fixture("weakening/prev_nofield_ledger.json", nofield_ledger)
    nofield_curr = _write_fixture("weakening/curr_nofield_ledger.json", nofield_ledger)
    pos = gops.gate_weakening_detection(str(curr_weak_path), str(prev_path))
    neg = gops.gate_weakening_detection(str(curr_clean_path), str(prev_path))
    defect = gops.gate_weakening_detection(str(nofield_curr), str(nofield_prev))
    defect_note = ""
    if defect.verdict != "PASS":
        defect_note = (
            "FINDING (measured): identical ledgers WITHOUT min_evidence_count "
            f"are refused ({defect.verdict}/{defect.reason}) — the 999->0 "
            "default pair in gate_weakening_detector.py:153-154 fires a false "
            "evidence_threshold_lowered finding whenever the field is absent; "
            "any realistic ledger lacking that optional field is always refused"
        )
        findings.append(f"cb:gate-weakening-detection: {defect_note}")
    record(
        "cb:gate-weakening-detection",
        "gate_operations",
        "verdict=FAIL reason=gate_weakening_detected:*",
        pos.verdict == "FAIL" and pos.reason.startswith("gate_weakening_detected"),
        f"{pos.verdict}/{pos.reason}",
        neg.verdict != "PASS",
        f"{neg.verdict}/{neg.reason}",
        note=defect_note,
    )

    # --- cb:strict-receipt-consumer-gate ----------------------------------
    clean_root = FIXTURES / "strict_consumer" / "clean_root"
    tampered_root = FIXTURES / "strict_consumer" / "tampered_root"
    for root in (clean_root, tampered_root):
        (root / "evidence").mkdir(parents=True, exist_ok=True)
    (clean_root / "evidence" / "artifact.txt").write_text("strict consumer control artifact\n")
    (tampered_root / "evidence" / "artifact.txt").write_text("TAMPERED artifact bytes\n")
    declared_sha = _sha256_bytes((clean_root / "evidence" / "artifact.txt").read_bytes())
    consumer_receipt = {
        "schema": "gate-control-consumer-fixture.v1",
        "artifacts": [{"path": "evidence/artifact.txt", "sha256": declared_sha}],
    }
    consumer_receipt_path = _write_fixture("strict_consumer/receipt.json", consumer_receipt)
    pos = gops.gate_strict_receipt_consumer(str(consumer_receipt_path), str(tampered_root))
    neg = gops.gate_strict_receipt_consumer(str(consumer_receipt_path), str(clean_root))
    # Direct-CLI cross-check with the pinned interpreter and full argument set,
    # to separate "the tool is broken" from "the gate binding is broken".
    receipt_sha = _sha256_bytes(consumer_receipt_path.read_bytes())
    def _direct_consumer(root, out_name):
        return subprocess.run(
            [
                sys.executable, "-m", "constraintbox.strict_receipt_consumer_v2",
                "--artifact-root", str(root),
                "--receipt", str(consumer_receipt_path),
                "--expected-receipt-sha256", receipt_sha,
                "--output", str(SCRATCH / out_name),
            ],
            capture_output=True, text=True, timeout=120,
            env={**os.environ, "PYTHONPATH": str(SRC_ROOT)},
        ).returncode
    direct_clean = _direct_consumer(clean_root, "consumer_clean.json")
    direct_tampered = _direct_consumer(tampered_root, "consumer_tampered.json")
    binding_note = (
        f"gate binding: positive {pos.verdict}/{pos.reason}; negative "
        f"{neg.verdict}/{neg.reason}. Direct CLI with correct args: clean "
        f"exit={direct_clean}, tampered exit={direct_tampered}."
    )
    binding_note += (
        " fixed: gate_operations.py now uses sys.executable, supplies the "
        "receipt digest and output arguments, and inspects returncode."
    )
    record(
        "cb:strict-receipt-consumer-gate",
        "gate_operations",
        "verdict=FAIL on tampered artifact tree",
        pos.verdict == "FAIL",
        f"{pos.verdict}/{pos.reason[:80]}",
        neg.verdict != "PASS",
        f"{neg.verdict}/{neg.reason[:80]}",
        note=binding_note,
    )

    # --- cb:release-gate --------------------------------------------------
    release_root = _fresh_dir("release-run")
    (release_root / "receipt.json").write_text("{}\n")
    pos = gops.gate_release(
        str(release_root), str(release_root), str(SCRATCH / "release_out_pos.json")
    )
    neg = gops.gate_release(
        str(BOX_ROOT / "receipts" / "first_released_run_20260809"),
        str(BOX_ROOT),
        str(SCRATCH / "release_out_neg.json"),
    )
    release_note = (
        f"positive {pos.verdict}/{pos.reason[:60]}; negative (live RELEASED "
        f"run) {neg.verdict}/{neg.reason[:60]}."
    )
    release_note += (
        " fixed: gate_operations.py now uses sys.executable, supplies the "
        "legacy strict consumer path, and inspects returncode."
    )
    record(
        "cb:release-gate",
        "gate_operations",
        "verdict=FAIL on empty run root",
        pos.verdict == "FAIL",
        f"{pos.verdict}/{pos.reason[:80]}",
        neg.verdict != "PASS",
        f"{neg.verdict}/{neg.reason[:80]}",
        note=release_note,
    )

    # =====================================================================
    # SECTION B: agentrun proposal-gate reason codes
    # =====================================================================

    tool_stub_path = _write_fixture(
        "proposals/tool_receipt_stub.json",
        {
            "schema": "gate-control-tool-receipt-stub.v1",
            "note": "its sha256 is the pinned evidence_ref for proposal controls",
        },
    )
    evidence_ref = _sha256_bytes(tool_stub_path.read_bytes())
    clean = _clean_proposal(evidence_ref)
    _write_fixture("proposals/clean_proposal.json", clean)

    clean_out = run_proposal_pipeline(
        json.dumps(clean).encode(), evidence_ref=evidence_ref
    )
    clean_reasons = clean_out["reasons"]
    clean_is_silent = (
        clean_reasons == []
        and clean_out["discharge_status"] == PASS
        and clean_out["release_safety"] is True
    )

    def reason_control(code, marker_prefix, mutated_raw=None, fixture_name=None,
                       note="", **pipeline_kwargs):
        raw = (
            mutated_raw
            if mutated_raw is not None
            else json.dumps(clean).encode()
        )
        if fixture_name and mutated_raw is not None:
            _write_fixture(f"proposals/{fixture_name}", mutated_raw)
        out = run_proposal_pipeline(raw, evidence_ref=evidence_ref, **pipeline_kwargs)
        fired = any(r.startswith(marker_prefix) for r in out["reasons"])
        crash = [r for r in out["reasons"] if r.startswith("RUN_PATH_CRASH")]
        if crash and not note:
            note = (
                "FINDING (measured): the run path crashes before _reason_codes "
                f"can emit {code}: {crash[0][:160]} — agentrun.py:1375-1383 "
                "reads candidate.get(...) before the reason-code gate runs"
            )
            findings.append(f"agentrun:{code}: {note}")
        neg_fired = any(r.startswith(marker_prefix) for r in clean_reasons)
        record(
            f"agentrun:{code}",
            "proposal_reason_code",
            marker_prefix,
            fired,
            ",".join(out["reasons"]) or "(no reasons)",
            neg_fired or not clean_is_silent,
            ",".join(clean_reasons) or "(no reasons; discharge PASS; release_safety True)",
            note=note,
        )

    def mutate(**changes):
        body = json.loads(json.dumps(clean))
        for key, value in changes.items():
            if key == "candidate_update":
                body["candidate"].update(value)
            elif key == "candidate_del":
                for name in value:
                    body["candidate"].pop(name, None)
            elif key == "candidate_set":
                body["candidate"] = value
            else:
                body[key] = value
        return json.dumps(body).encode()

    reason_control(
        "PROPOSAL_NOT_STRICT_JSON_OBJECT", "PROPOSAL_NOT_STRICT_JSON_OBJECT",
        mutated_raw=b"this is not a JSON object",
        fixture_name="not_json.txt",
    )
    reason_control(
        "PROPOSAL_ROOT_FIELDS", "PROPOSAL_ROOT_FIELDS",
        mutated_raw=mutate(extra_root_note="unexpected root field"),
        fixture_name="root_fields_extra_key.json",
    )
    reason_control(
        "PROPOSAL_ID_INVALID", "PROPOSAL_ID_INVALID",
        mutated_raw=mutate(proposal_id=""),
        fixture_name="proposal_id_empty.json",
    )
    reason_control(
        "PROPOSAL_CANDIDATE_INVALID", "PROPOSAL_CANDIDATE_INVALID",
        mutated_raw=mutate(candidate_set="not-a-dict"),
        fixture_name="candidate_not_dict.json",
    )
    reason_control(
        "PROPOSAL_CANDIDATE_FIELDS", "PROPOSAL_CANDIDATE_FIELDS",
        mutated_raw=mutate(candidate_update={"confidence": "high"}),
        fixture_name="candidate_extra_field.json",
    )
    reason_control(
        "PROPOSAL_CLAIM_ENUM", "PROPOSAL_CLAIM_ENUM",
        mutated_raw=mutate(candidate_update={"requested_claim": "novel_claim_kind"}),
        fixture_name="claim_outside_enum.json",
    )
    reason_control(
        "PROPOSAL_EVIDENCE_REF_INVALID", "PROPOSAL_EVIDENCE_REF_INVALID",
        mutated_raw=mutate(candidate_update={"evidence_ref": "not-a-sha256"}),
        fixture_name="evidence_ref_not_hex.json",
    )
    reason_control(
        "PROPOSAL_FALSIFIERS_INVALID", "PROPOSAL_FALSIFIERS_INVALID",
        mutated_raw=mutate(falsifiers=[]),
        fixture_name="falsifiers_empty.json",
    )
    reason_control(
        "EVIDENCE_REF_MISMATCH", "EVIDENCE_REF_MISMATCH",
        mutated_raw=mutate(candidate_update={"evidence_ref": "0" * 64}),
        fixture_name="evidence_ref_wrong_sha.json",
    )
    reason_control(
        "EVIDENCE_REF_MISSING", "EVIDENCE_REF_MISSING",
        mutated_raw=mutate(candidate_del=["evidence_ref"]),
        fixture_name="evidence_ref_missing.json",
    )
    reason_control(
        "PROPOSAL_CLAIM_MISSING", "PROPOSAL_CLAIM_MISSING",
        mutated_raw=mutate(candidate_del=["requested_claim"]),
        fixture_name="claim_missing.json",
    )
    ceiling_raw = mutate(candidate_update={"requested_claim": "scientific_result"})
    reason_control(
        "CLAIM_CEILING_EXCEEDED", "CLAIM_CEILING_EXCEEDED",
        mutated_raw=ceiling_raw,
        fixture_name="claim_ceiling_scientific_result.json",
    )
    reason_control(
        "SMT_PROPOSAL_UNSAT", "SMT_PROPOSAL_UNSAT",
        mutated_raw=ceiling_raw,
        note=(
            "same fixture as CLAIM_CEILING_EXCEEDED by design: the SMT gate "
            "is the independent z3+cvc5+enumeration recomputation of the same "
            "admission fact and must co-fire"
        ),
    )
    reason_control(
        "DISCHARGE_NOT_PASS", "DISCHARGE_NOT_PASS",
        observation_age_seconds=3600.0,
        note="single violation: observations older than the 60s policy window",
    )
    reason_control(
        "RELEASE_SAFETY_VETO", "RELEASE_SAFETY_VETO",
        tool_errors=["TOOL_CONTROL_FAILED"],
        note="single violation: tool control errors present at release recheck",
    )
    reason_control(
        "PROVIDER_TOOL_USE", "PROVIDER_TOOL_USE",
        has_tool_calls=True,
    )
    reason_control(
        "PROVIDER_RECEIPT_REJECTED", "PROVIDER_RECEIPT_REJECTED",
        provider_admitted=False,
    )
    reason_control(
        "PROVIDER_STATUS_<status>", "PROVIDER_STATUS_error",
        receipt_status="error",
    )
    reason_control(
        "CONTROLLER_<blocked-reason>", "CONTROLLER_PROPOSAL_ATTEMPTED_CONTROLLER_AUTHORITY",
        mutated_raw=mutate(verdict="PASS"),
        fixture_name="authority_field_verdict.json",
        note="proposal carrying an authority-bearing root field ('verdict')",
    )
    reason_control(
        "MODEL_RESOLVED_MISMATCH", "MODEL_RESOLVED_MISMATCH",
        model_resolved="gpt-5.6-sol",
        note="the measured 2026-08-08 substitution shape: luna requested, sol answered",
    )
    reason_control(
        "MODEL_RESOLVED_UNAVAILABLE", "MODEL_RESOLVED_UNAVAILABLE",
        model_resolved=None,
    )
    # Lenient-direction negative control for the model binding rule itself.
    refinement = agentrun._model_binding_reasons(
        "x-ai/grok-4.3", "x-ai/grok-4.3-20260430"
    )
    if refinement:
        findings.append(
            "agentrun:_model_binding_reasons rejects a dated refinement "
            "(x-ai/grok-4.3 -> x-ai/grok-4.3-20260430); documented lenient "
            "direction broken"
        )

    # --- SMT_UNAVAILABLE_OR_DIVERGENT: genuine dependency-absence probe ---
    shadow_dir = _fresh_dir("cvc5-shadow")
    (shadow_dir / "cvc5.py").write_text(
        "raise ModuleNotFoundError('cvc5 blocked for gate control', name='cvc5')\n"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(shadow_dir), str(SRC_ROOT)])
    probe = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()),
         "--probe-smt-unavailable", evidence_ref],
        capture_output=True, text=True, timeout=600, env=env,
    )
    try:
        probe_out = json.loads(probe.stdout.strip().splitlines()[-1])
        probe_reasons = probe_out["reasons"]
    except Exception:
        probe_reasons = [f"PROBE_FAILED rc={probe.returncode}: {probe.stderr[-300:]}"]
    record(
        "agentrun:SMT_UNAVAILABLE_OR_DIVERGENT",
        "proposal_reason_code",
        "SMT_UNAVAILABLE_OR_DIVERGENT",
        any(r.startswith("SMT_UNAVAILABLE_OR_DIVERGENT") for r in probe_reasons),
        ",".join(probe_reasons),
        any(r.startswith("SMT_UNAVAILABLE_OR_DIVERGENT") for r in clean_reasons)
        or not clean_is_silent,
        ",".join(clean_reasons) or "(no reasons)",
        note=(
            "positive control ran the identical clean pipeline in a subprocess "
            "whose PYTHONPATH shadows cvc5 with a module raising "
            "ModuleNotFoundError — genuine dependency absence, no gate patched"
        ),
    )

    # --- extraction-stage reason codes ------------------------------------
    def extraction_errors_for(content=None, event_lines=None, has_tool_calls=False,
                              fixture_name=None, missing_file=False):
        receipt = SimpleNamespace(
            status="success", model_resolved="gpt-5.6-luna",
            has_tool_calls=has_tool_calls, content=content,
        )
        if missing_file:
            path = SCRATCH / "definitely-missing-events.jsonl"
        elif fixture_name:
            body = "\n".join(json.dumps(line) for line in (event_lines or [])) + "\n"
            path = _write_fixture(f"provider_events/{fixture_name}", body.encode())
        else:
            path = SCRATCH / "unused-events.jsonl"
        _raw, tool_use, errors, _w = agentrun._extract_proposal(receipt, path)
        return errors, tool_use

    clean_events = [
        {"type": "item.completed",
         "item": {"type": "agent_message", "text": json.dumps(clean)}},
    ]
    neg_errors, neg_tool_use = extraction_errors_for(
        event_lines=clean_events, fixture_name="events_clean.jsonl"
    )
    extraction_neg_silent = neg_errors == [] and neg_tool_use is False

    extraction_cases = [
        ("PROVIDER_OUTPUT_MISSING", "PROVIDER_OUTPUT_MISSING",
         dict(missing_file=True)),
        ("PROVIDER_OUTPUT_EXCEEDS_BOUND", "PROVIDER_OUTPUT_EXCEEDS_BOUND",
         dict(content="x" * (agentrun.MAX_PROVIDER_OUTPUT_BYTES + 1))),
        ("PROVIDER_EVENT_INVALID", "PROVIDER_EVENT_INVALID",
         None),  # handled specially below (raw bytes line)
        ("PROVIDER_EVENT_TYPE_FORBIDDEN", "PROVIDER_EVENT_TYPE_FORBIDDEN",
         dict(event_lines=[{"type": "tool.begin"}, *clean_events],
              fixture_name="events_forbidden_type.jsonl")),
        ("PROVIDER_ITEM_TYPE_FORBIDDEN", "PROVIDER_ITEM_TYPE_FORBIDDEN",
         dict(event_lines=[
             {"type": "item.completed",
              "item": {"type": "command_execution", "command": "rm -rf /"}},
             *clean_events],
             fixture_name="events_forbidden_item.jsonl")),
        ("PROVIDER_AGENT_MESSAGE_COUNT", "PROVIDER_AGENT_MESSAGE_COUNT",
         dict(event_lines=[*clean_events, *clean_events],
              fixture_name="events_two_messages.jsonl")),
    ]
    for code, prefix, kwargs in extraction_cases:
        if kwargs is None:
            bad_path = _write_fixture(
                "provider_events/events_invalid_line.jsonl",
                b"{this line is not JSON}\n",
            )
            receipt = SimpleNamespace(
                status="success", model_resolved="gpt-5.6-luna",
                has_tool_calls=False, content=None,
            )
            _raw, _tu, errors, _w = agentrun._extract_proposal(receipt, bad_path)
        else:
            errors, _tu = extraction_errors_for(**kwargs)
        record(
            f"agentrun:{code}",
            "provider_extraction",
            prefix,
            any(e.startswith(prefix) for e in errors),
            ",".join(errors) or "(no errors)",
            any(e.startswith(prefix) for e in neg_errors)
            or not extraction_neg_silent,
            ",".join(neg_errors) or "(no errors; exactly one agent message)",
        )

    # =====================================================================
    # SECTION C: user_request preflight clauses
    # =====================================================================

    base_request = {
        "schema": "constraintbox.user-request.v1",
        "request_id": "gate-control-request-1",
        "goal": "Prove each CB gate refuses its targeted violation and stays silent on clean input.",
        "deliverable": "A control receipt listing every gate with both control outcomes.",
        "in_scope": ["run existing gate code on inspectable fixture inputs"],
        "out_of_scope": ["promotion of any claim beyond control outcomes"],
        "assumption_state": "none_stated",
        "assumptions": [],
        "evidence_required": ["gate refusal reason codes observed on targeted fixtures"],
        "allowed_actions": ["read", "execute_tests", "write_receipts"],
        "requested_external_tests": [],
        "claim_boundary": "control outcomes about gate behavior only; no scientific claim",
        "unknowns": [],
        "communication_needs": [],
    }
    _write_fixture("requests/clean_request.json", base_request)
    neg_assessment = assess_user_request(
        json.dumps(base_request).encode("utf-8")
    )
    request_neg_silent = (
        neg_assessment.disposition == "ELIGIBLE_FOR_PROPOSAL"
        and neg_assessment.failed_clauses == ()
    )

    clause_breakers = {
        "goal_explicit": {"goal": ""},
        "deliverable_explicit": {"deliverable": ""},
        "scope_explicit": {"in_scope": []},
        "assumptions_explicit": {"assumption_state": "unknown"},
        "evidence_explicit": {"evidence_required": []},
        "actions_explicit": {"allowed_actions": []},
        "external_tests_explicit": {
            "allowed_actions": ["read", "run_external_tools"],
            "requested_external_tests": [],
        },
        "claim_boundary_explicit": {"claim_boundary": ""},
    }
    for clause, changes in clause_breakers.items():
        body = json.loads(json.dumps(base_request))
        body.update(changes)
        _write_fixture(f"requests/break_{clause}.json", body)
        assessment = assess_user_request(json.dumps(body).encode("utf-8"))
        fired = (
            assessment.disposition == "PARKED"
            and clause in assessment.failed_clauses
        )
        record(
            f"user_request:{clause}",
            "request_preflight_clause",
            f"disposition=PARKED failed_clauses contains {clause}",
            fired,
            f"{assessment.disposition} failed={list(assessment.failed_clauses)}",
            (clause in neg_assessment.failed_clauses) or not request_neg_silent,
            f"{neg_assessment.disposition} failed={list(neg_assessment.failed_clauses)}",
        )

    authority_body = json.loads(json.dumps(base_request))
    authority_body["disposition"] = "RELEASED"
    _write_fixture("requests/authority_field_disposition.json", authority_body)
    authority = assess_user_request(json.dumps(authority_body).encode("utf-8"))
    record(
        "user_request:authority_field_rejection",
        "request_preflight_intake",
        "disposition=BLOCKED reason=request_attempted_controller_authority",
        authority.disposition == "BLOCKED"
        and authority.reason == "request_attempted_controller_authority",
        f"{authority.disposition}/{authority.reason}",
        not request_neg_silent,
        f"{neg_assessment.disposition}/{neg_assessment.reason}",
    )
    shape_body = json.loads(json.dumps(base_request))
    del shape_body["claim_boundary"]
    _write_fixture("requests/schema_missing_root_field.json", shape_body)
    shape = assess_user_request(json.dumps(shape_body).encode("utf-8"))
    record(
        "user_request:schema_shape_rejection",
        "request_preflight_intake",
        "disposition=BLOCKED reason=request_schema_invalid",
        shape.disposition == "BLOCKED"
        and shape.reason == "request_schema_invalid",
        f"{shape.disposition}/{shape.reason}",
        not request_neg_silent,
        f"{neg_assessment.disposition}/{neg_assessment.reason}",
    )

    # =====================================================================
    # SECTION D: mini_levos construction-time invariants
    # =====================================================================

    pass_reg = _registration(
        "control-pass", control_pass_gate, (HookSignal.PASS,)
    )
    pass_blocked_reg = _registration(
        "control-pass-blocked", control_pass_blocked_gate,
        (HookSignal.PASS, HookSignal.BLOCKED),
    )

    # Shared negative control: a valid single-gate policy constructs.
    valid_policy = _policy(
        (FlowNode("gate", "control-pass"),),
        (FlowTransition("gate", HookSignal.PASS, "RELEASED"),
         FlowTransition("gate", HookSignal.HOLD, "HOLD")),
        ("HOLD", "RELEASED"),
        entry="gate",
        required=("gate",),
    )
    neg_raised, neg_message = _construct(valid_policy, (pass_reg,), "valid")

    def invariant_control(gate_id, marker, policy, registrations, note=""):
        raised, message = _construct(policy, registrations, gate_id.split(":")[-1])
        record(
            f"minilev:{gate_id}",
            "construction_invariant",
            marker,
            raised and marker in message,
            message,
            neg_raised,
            neg_message if neg_raised else "valid policy constructed silently",
            note=note,
        )

    invariant_control(
        "duplicate_node_signal_transition",
        "duplicate transition for node and signal",
        _policy(
            (FlowNode("gate", "control-pass"),),
            (FlowTransition("gate", HookSignal.PASS, "RELEASED"),
             FlowTransition("gate", HookSignal.PASS, "BLOCKED"),
             FlowTransition("gate", HookSignal.HOLD, "HOLD")),
            ("BLOCKED", "HOLD", "RELEASED"),
            entry="gate",
            required=(),
        ),
        (pass_reg,),
    )
    invariant_control(
        "signal_terminal_mapping",
        "BLOCKED must map to its matching terminal",
        _policy(
            (FlowNode("gate", "control-pass-blocked"),),
            (FlowTransition("gate", HookSignal.PASS, "RELEASED"),
             FlowTransition("gate", HookSignal.BLOCKED, "PARKED"),
             FlowTransition("gate", HookSignal.HOLD, "HOLD")),
            ("HOLD", "PARKED", "RELEASED"),
            entry="gate",
            required=(),
        ),
        (pass_blocked_reg,),
    )
    invariant_control(
        "all_nodes_reachable",
        "all flow and required nodes must be reachable",
        _policy(
            (FlowNode("gate", "control-pass"), FlowNode("orphan", "control-pass")),
            (FlowTransition("gate", HookSignal.PASS, "RELEASED"),
             FlowTransition("gate", HookSignal.HOLD, "HOLD"),
             FlowTransition("orphan", HookSignal.PASS, "BLOCKED"),
             FlowTransition("orphan", HookSignal.HOLD, "HOLD")),
            ("BLOCKED", "HOLD", "RELEASED"),
            entry="gate",
            required=("gate",),
        ),
        (pass_reg,),
    )
    invariant_control(
        "nonretry_edges_dag",
        "non-retry flow edges must form a DAG",
        _policy(
            (FlowNode("g1", "control-pass"), FlowNode("g2", "control-pass")),
            (FlowTransition("g1", HookSignal.PASS, "g2"),
             FlowTransition("g1", HookSignal.HOLD, "HOLD"),
             FlowTransition("g2", HookSignal.PASS, "g1"),
             FlowTransition("g2", HookSignal.HOLD, "HOLD")),
            ("HOLD",),
            entry="g1",
            required=(),
        ),
        (pass_reg,),
    )

    # every-node-reaches-a-terminal: honestly unfireable via the public
    # constructor.  Every node MUST carry a HOLD transition (exhaustive map)
    # and HOLD MUST map to the HOLD terminal, so every node always has a
    # direct terminal edge.  Both guarding refusals are measured here.
    guard_a_raised, guard_a_msg = _construct(
        _policy(
            (FlowNode("gate", "control-pass"),),
            (FlowTransition("gate", HookSignal.PASS, "RELEASED"),),
            ("RELEASED",),
            entry="gate",
            required=(),
        ),
        (pass_reg,),
        "no-hold-edge",
    )
    guard_b_raised, guard_b_msg = _construct(
        _policy(
            (FlowNode("gate", "control-pass"),),
            (FlowTransition("gate", HookSignal.PASS, "RELEASED"),
             FlowTransition("gate", HookSignal.HOLD, "BLOCKED")),
            ("BLOCKED", "RELEASED"),
            entry="gate",
            required=(),
        ),
        (pass_reg,),
        "hold-to-wrong-terminal",
    )
    record(
        "minilev:every_node_reaches_terminal",
        "construction_invariant",
        "node cannot reach a terminal",
        False,
        (
            "UNFIREABLE via the public constructor: omitting the HOLD edge is "
            f"refused first ('{guard_a_msg}'), and pointing HOLD at a "
            f"non-HOLD terminal is refused first ('{guard_b_msg}'); the "
            "check at mini_levos.py:1017-1019 is a defense-in-depth backstop "
            "shadowed by the exhaustive-map + HOLD-terminal invariants"
        ),
        neg_raised,
        neg_message if neg_raised else "valid policy constructed silently",
        note=(
            "honest negative: not hallucinated code, but unreachable through "
            "any FlowPolicy the constructor admits; only reachable if the "
            "stronger invariants above it were ever removed"
        ),
    )

    # =====================================================================
    # SECTION E: ClaimGate chain verdict path
    # =====================================================================

    chain_clean = {
        "classification": "scratch_diagnostic",
        "claim_kind": "field_only",
        "produced_by": "gate-control-fixture-builder",
    }
    chain_inflated = dict(chain_clean)
    chain_inflated["tools"] = [
        {"tool": "widget", "verdict": "INTEGRATED", "pass": False}
    ]
    chain_clean_path = _write_fixture("chain/clean_receipt.json", chain_clean)
    chain_inflated_path = _write_fixture("chain/inflated_receipt.json", chain_inflated)
    pos = run_gate(chain_inflated_path)
    neg = run_gate(chain_clean_path)
    pos_fired = (
        pos["disposition"] == "REFUSED"
        and pos["chain_exit_code"] == 1
        and pos["chain_verdict"] == "REJECTED"
        and agentrun._claim_gate_is_strong(pos) is False
    )
    neg_silent = (
        neg["disposition"] == "ADMITTED"
        and neg["chain_exit_code"] == 0
        and neg["chain_verdict"] == "VERIFIED"
        and agentrun._claim_gate_is_strong(neg) is True
    )
    record(
        "claimgate:chain-verdict-path",
        "claimgate_chain",
        "disposition=REFUSED exit=1 verdict=REJECTED strong=False",
        pos_fired,
        f"{pos['disposition']}/exit={pos['chain_exit_code']}/{pos['chain_verdict']}",
        not neg_silent,
        f"{neg['disposition']}/exit={neg['chain_exit_code']}/{neg['chain_verdict']}"
        f"/strong={agentrun._claim_gate_is_strong(neg)}",
        note="claim inflated to INTEGRATED with pass=false vs untouched clean receipt",
    )

    # =====================================================================
    # Report
    # =====================================================================

    proven = [r["gate"] for r in RESULTS if r["classification"] == "proven_real"]
    never = [r["gate"] for r in RESULTS if r["classification"] == "never_fires"]
    always = [r["gate"] for r in RESULTS if r["classification"] == "always_fires"]

    print("=" * 98)
    print("PROVE GATES FIRE — positive control (targeted refusal) + negative control (clean silence)")
    print(f"interpreter: {sys.executable}")
    print(f"fixtures:    {FIXTURES}")
    print(f"scratch:     {SCRATCH}")
    print("=" * 98)
    width = max(len(r["gate"]) for r in RESULTS) + 2
    print(f"{'GATE':<{width}}{'POS FIRED':<11}{'NEG SILENT':<12}CLASSIFICATION")
    print("-" * 98)
    for row in RESULTS:
        print(
            f"{row['gate']:<{width}}"
            f"{('YES' if row['positive_fired'] else 'NO'):<11}"
            f"{('YES' if not row['negative_fired'] else 'NO'):<12}"
            f"{row['classification']}"
        )
    print("-" * 98)
    print(f"gates_total={len(RESULTS)} proven_real={len(proven)} "
          f"never_fires={len(never)} always_fires={len(always)}")
    if never:
        print("\nNEVER_FIRES (no fixture could make it refuse):")
        for row in RESULTS:
            if row["classification"] == "never_fires":
                print(f"  - {row['gate']}: {row['positive_observed']}")
    if always:
        print("\nALWAYS_FIRES (refuses even clean input — equally useless):")
        for row in RESULTS:
            if row["classification"] == "always_fires":
                print(f"  - {row['gate']}: negative observed {row['negative_observed']}")
                if row["note"]:
                    print(f"    {row['note']}")
    if findings:
        print("\nFINDINGS (reported, not edited — gates are never weakened or 'fixed' here):")
        for finding in findings:
            print(f"  * {finding}")

    receipt = {
        "schema": "constraintbox.gate-fire-proof.v1",
        "interpreter": sys.executable,
        "fixtures_root": str(FIXTURES),
        "gates_total": len(RESULTS),
        "proven_real": proven,
        "never_fires": never,
        "always_fires": always,
        "results": RESULTS,
        "findings": findings,
        "claim_ceiling": (
            "control outcomes about gate refusal behavior on fixture inputs "
            "only; no promotion"
        ),
        "promotion_allowed": False,
    }
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n")
    print(f"\nreceipt: {RECEIPT_PATH}")
    return 0 if len(proven) == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
