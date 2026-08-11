from __future__ import annotations

import copy
import importlib
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
LIGHT_SOURCE = ROOT / "light_runtime" / "src"
PACKAGE_NAME = "_cb_light_premortem_contracts"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_contracts():
    if PACKAGE_NAME not in sys.modules:
        init_py = LIGHT_SOURCE / "constraintbox" / "__init__.py"
        spec = importlib.util.spec_from_file_location(
            PACKAGE_NAME,
            init_py,
            submodule_search_locations=[str(init_py.parent)],
        )
        assert spec is not None and spec.loader is not None
        package = importlib.util.module_from_spec(spec)
        sys.modules[PACKAGE_NAME] = package
        spec.loader.exec_module(package)
    return importlib.import_module(f"{PACKAGE_NAME}.premortem_contracts")


contracts = _load_contracts()


def _digest(char: str) -> str:
    return char * 64


def _gate(gate_id: str, digest: str) -> dict[str, str]:
    return {
        "gate_id": gate_id,
        "executor_kind": "deterministic_callable",
        "executable_ref": f"constraintbox.gates.{gate_id}",
        "definition_sha256": _digest(digest),
    }


def _policy() -> dict[str, object]:
    return {
        "schema": contracts.RUN_POLICY_SCHEMA,
        "run_policy_id": "premortem-policy-alpha",
        "completion_gate": _gate("completion-gate-alpha", "a"),
        "required_regression_gates": [],
        "scope_paths": [
            "constraint_box/tests",
            "constraint_box/light_runtime/src/constraintbox",
        ],
        "diff_bound": 3,
        "promotion_rule_id": "first-receipt-verified-canonical-order",
        "iteration_bound": None,
        "time_bound_seconds": None,
        "progress_measure": {
            "measure_id": "remaining-admissible-candidate-frontier",
            "measure_domain": "natural_nonnegative_integer",
            "terminal_value": 0,
            "strict_per_retry_decrease": True,
        },
        "output_surfaces": [],
        "claim_ceiling": "local typed remediation contract only",
    }


def _concern() -> dict[str, object]:
    return {
        "schema": contracts.CONCERN_RECORD_SCHEMA,
        "concern_id": "concern-alpha",
        "source": "premortem-skill",
        "locator": "constraint_box/tests/test_target.py:12",
        "description": "The deterministic gate can be bypassed by a missing field.",
        "discovered_at": "2026-08-11T08:00:00Z",
        "source_sha256": _digest("b"),
    }


def _issue() -> dict[str, object]:
    return {
        "schema": contracts.ISSUE_SCHEMA,
        "issue_id": "issue-alpha",
        "concern_id": "concern-alpha",
        "classification_gate": _gate("classify-concern-alpha", "c"),
        "disposition": "OPEN",
        "reason_code": "GATE_CONFIRMED_BYPASS",
        "classification_receipt_sha256": _digest("d"),
    }


def _binding() -> dict[str, object]:
    return {
        "schema": contracts.PRODUCER_BINDING_SCHEMA,
        "binding_id": "binding-alpha",
        "producer_id": "premortem-remediation",
        "issue_id": "issue-alpha",
        "binding_history": [
            "declared",
            "bound_reference",
            "invoked",
            "receipt_verified",
        ],
        "binding_state": "receipt_verified",
        "binding_evidence_sha256s": [_digest(char) for char in "ef12"],
        "producer_receipt_sha256": _digest("3"),
        "updated_at": "2026-08-11T08:01:00Z",
    }


def _candidate() -> dict[str, object]:
    return {
        "schema": contracts.REPAIR_CANDIDATE_SCHEMA,
        "candidate_id": "candidate-alpha",
        "issue_id": "issue-alpha",
        "producer_type": "skill",
        "producer_id": "premortem-remediation",
        "proposed_action": {
            "action_type": "remove-forbidden-field",
            "scope_paths": ["constraint_box/light_runtime/src/constraintbox"],
            "diff_bound": 1,
            "evidence_effect": "non_evidence_increasing",
            "target_sha256": _digest("4"),
        },
        "evidence_refs": ["gate:failure-alpha", "receipt:premortem-alpha"],
        "produced_at": "2026-08-11T08:02:00Z",
    }


def _objects():
    policy = contracts.validate_run_policy(_policy()).value
    issue = contracts.validate_issue(_issue()).value
    binding = contracts.validate_producer_binding(_binding()).value
    candidate = contracts.validate_repair_candidate(_candidate(), policy).value
    assert policy is not None and issue is not None and binding is not None and candidate is not None
    return policy, issue, binding, candidate


def _gate_run_raw(policy, action, *, aggregate_result="PASS", regressions=None) -> dict[str, object]:
    return {
        "schema": contracts.GATE_RUN_SCHEMA,
        "gate_run_id": "gate-run-alpha",
        "action_id": action.action_id,
        "action_sha256": action.sha256,
        "run_policy_sha256": policy.sha256,
        "round_index": action.round_index,
        "aggregate_gate_id": policy.completion_gate.gate_id,
        "aggregate_gate_definition_sha256": policy.completion_gate.definition_sha256,
        "aggregate_result": aggregate_result,
        "required_gate_results": [] if regressions is None else regressions,
        "input_state_sha256": _digest("1"),
        "current_state_sha256": _digest("2"),
        "measure_value": 0,
        "executed_at": "2026-08-11T08:03:00Z",
    }


def test_policy_requires_aggregate_regressions_and_well_founded_stop_rule() -> None:
    valid = contracts.validate_run_policy(_policy())
    assert valid.disposition == "VALIDATED"
    assert valid.value is not None
    assert valid.value.progress_measure.strict_per_retry_decrease is True
    assert valid.value.required_regression_gates == ()

    missing_gate = _policy()
    missing_gate["completion_gate"] = None
    assert contracts.validate_run_policy(missing_gate).reason_code == "NO_DECLARED_COMPLETION_GATE"

    missing_regressions = _policy()
    del missing_regressions["required_regression_gates"]
    assert contracts.validate_run_policy(missing_regressions).reason_code == "NO_DECLARED_REGRESSION_AGGREGATE"

    no_measure = _policy()
    no_measure["progress_measure"] = None
    no_measure["iteration_bound"] = 2
    assert contracts.validate_run_policy(no_measure).reason_code == "NO_DECLARED_STOP_CRITERION"

    output_first = _policy()
    output_first["completion_gate"] = None
    output_first["output_surfaces"] = ["html"]
    result = contracts.validate_run_policy(output_first)
    assert result.disposition == "REFUSE"
    assert result.reason_code == "PROHIBITED_OUTPUT_SURFACE"

    authority_first = _policy()
    authority_first["completion_gate"] = None
    authority_first["unknown_policy_extension"] = {"score": 99}
    result = contracts.validate_run_policy(authority_first)
    assert result.disposition == "REFUSE"
    assert result.reason_code == "NONDETERMINISTIC_AUTHORITY"

    nested_output_first = _policy()
    nested_output_first["completion_gate"] = {"output_surfaces": ["browser"]}
    result = contracts.validate_run_policy(nested_output_first)
    assert result.disposition == "REFUSE"
    assert result.reason_code == "PROHIBITED_OUTPUT_SURFACE"


def test_structured_concern_and_immutable_issue_require_deterministic_gate() -> None:
    concern = contracts.validate_concern_record(_concern())
    assert concern.disposition == "VALIDATED"
    assert concern.value is not None
    assert concern.value.sha256 == contracts.canonical_sha256(concern.value)

    unlocated = _concern()
    unlocated["locator"] = ""
    assert contracts.validate_concern_record(unlocated).reason_code == "CONCERN_NOT_STRUCTURED"

    issue = contracts.validate_issue(_issue())
    assert issue.disposition == "VALIDATED"
    assert issue.value is not None
    ungated = _issue()
    ungated["classification_gate"] = None
    assert contracts.validate_issue(ungated).reason_code == "ISSUE_CLASSIFICATION_GATE_REQUIRED"


def test_producer_binding_is_separate_and_authority_or_skips_refuse() -> None:
    binding = contracts.validate_producer_binding(_binding())
    assert binding.disposition == "VALIDATED"
    assert binding.value is not None
    assert binding.value.binding_state == "receipt_verified"

    skipped = _binding()
    skipped["binding_history"] = ["declared", "invoked"]
    skipped["binding_state"] = "invoked"
    assert contracts.validate_producer_binding(skipped).reason_code == "BINDING_STATE_SKIPPED"

    authority = _candidate()
    authority["proposed_action"]["confidence"] = 0.99
    assert contracts.validate_repair_candidate(authority, _policy()).reason_code == "NONDETERMINISTIC_AUTHORITY"

    conflated = _candidate()
    conflated["binding_state"] = "receipt_verified"
    assert contracts.validate_repair_candidate(conflated, _policy()).reason_code == "REFUSE_CANDIDATE_CONTAINS_BINDING_STATE"


def test_candidate_dispositions_and_first_round_promotion_are_bounded() -> None:
    out_of_scope = _candidate()
    out_of_scope["proposed_action"]["scope_paths"] = ["outside/run"]
    assert contracts.validate_repair_candidate(out_of_scope, _policy()).disposition == "PROPOSED_FOR_OWNER"

    evidence_increasing = _candidate()
    evidence_increasing["proposed_action"]["evidence_effect"] = "evidence_increasing"
    assert contracts.validate_repair_candidate(evidence_increasing, _policy()).reason_code == "CANDIDATE_EVIDENCE_INCREASING"

    too_large = _candidate()
    too_large["proposed_action"]["diff_bound"] = 4
    assert contracts.validate_repair_candidate(too_large, _policy()).reason_code == "ACTION_EXCEEDS_BOUND"

    policy, issue, binding, candidate = _objects()
    promotion = contracts.admit_repair_candidate(candidate, binding, issue, policy, round_index=0)
    assert promotion.disposition == "VALIDATED"
    assert promotion.value is not None
    assert promotion.value.parent_gate_run_sha256 is None

    assert contracts.admit_repair_candidate(candidate, binding, issue, policy, round_index=1).reason_code == "SECOND_ACTION_WITHOUT_DECREASING_ROUND"
    fingerprint = contracts.repair_action_fingerprint(candidate)
    resubmitted_raw = _candidate()
    resubmitted_raw["candidate_id"] = "candidate-bravo"
    resubmitted_raw["produced_at"] = "2026-08-11T08:05:00Z"
    resubmitted = contracts.validate_repair_candidate(resubmitted_raw, policy).value
    assert resubmitted is not None
    assert resubmitted.sha256 != candidate.sha256
    assert contracts.repair_action_fingerprint(resubmitted) == fingerprint
    assert contracts.admit_repair_candidate(
        resubmitted,
        binding,
        issue,
        policy,
        round_index=0,
        excluded_repair_action_fingerprints=[fingerprint],
    ).reason_code == "REFUSE_CANDIDATE_EXCLUDED"


def test_action_application_binds_one_action_and_claims_no_terminal() -> None:
    policy, issue, binding, candidate = _objects()
    action = contracts.admit_repair_candidate(candidate, binding, issue, policy, round_index=0).value
    assert action is not None
    raw = {
        "schema": contracts.ACTION_APPLICATION_SCHEMA,
        "application_id": "application-alpha",
        "action_id": action.action_id,
        "action_sha256": action.sha256,
        "executor_asset_id": "control-plane-profile-installer",
        "execution_receipt_sha256": _digest("5"),
        "input_state_sha256": _digest("6"),
        "output_state_sha256": _digest("7"),
        "applied_at": "2026-08-11T08:03:00Z",
    }
    result = contracts.validate_action_application(raw, action)
    assert result.disposition == "VALIDATED"
    assert result.value is not None
    assert result.value.sha256 == contracts.canonical_sha256(result.value)

    wrong_action = copy.deepcopy(raw)
    wrong_action["action_id"] = "repair-action-other"
    assert contracts.validate_action_application(
        wrong_action, action
    ).reason_code == "REFUSE_ACTION_APPLICATION_BINDING_MISMATCH"

    authority = copy.deepcopy(raw)
    authority["terminal"] = "VERIFIED_DONE"
    assert contracts.validate_action_application(authority, action).reason_code == "ACTION_APPLICATION_INVALID"


def test_aggregate_gate_run_binds_every_regression_and_cannot_hide_failure() -> None:
    policy, issue, binding, candidate = _objects()
    action = contracts.admit_repair_candidate(candidate, binding, issue, policy, round_index=0).value
    assert action is not None
    valid = contracts.validate_gate_run(_gate_run_raw(policy, action), policy, action)
    assert valid.disposition == "VALIDATED"
    assert valid.value is not None
    assert valid.value.sha256 == contracts.canonical_sha256(valid.value)

    with_regression = _policy()
    regression = _gate("regression-gate-alpha", "5")
    with_regression["required_regression_gates"] = [regression]
    policy2 = contracts.validate_run_policy(with_regression).value
    candidate2 = contracts.validate_repair_candidate(_candidate(), policy2).value
    assert policy2 is not None and candidate2 is not None
    action2 = contracts.admit_repair_candidate(candidate2, binding, issue, policy2, round_index=0).value
    assert action2 is not None
    hidden = _gate_run_raw(policy2, action2, regressions=[{
        "gate_id": regression["gate_id"],
        "definition_sha256": regression["definition_sha256"],
        "result": "FAIL",
    }])
    assert contracts.validate_gate_run(hidden, policy2, action2).reason_code == "REFUSE_REGRESSION_GATE_HIDDEN"


def test_custody_carriers_are_hashable_but_do_not_claim_settlement() -> None:
    receipt = contracts.Receipt(
        contracts.RECEIPT_SCHEMA,
        "receipt-alpha",
        "run-alpha",
        "HOLD",
        None,
        "completion-gate-alpha",
        _digest("6"),
        _digest("7"),
        _digest("8"),
        "2026-08-11T08:04:00Z",
    )
    exclusion = contracts.CandidateExclusion(
        contracts.CANDIDATE_EXCLUSION_SCHEMA,
        "exclusion-alpha",
        "issue-alpha",
        _digest("9"),
        _digest("a"),
        0,
        "AGGREGATE_FAIL",
        "2026-08-11T08:04:00Z",
    )
    assert receipt.sha256 == contracts.canonical_sha256(receipt)
    assert exclusion.as_dict()["repair_action_fingerprint"] == _digest("9")
    assert "settlement" in contracts.CLAIM_CEILING
