from __future__ import annotations

import ast
import copy
import importlib
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
LIGHT_SOURCE = ROOT / "light_runtime" / "src"
PACKAGE_NAME = "_cb_light_premortem_remediation"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_controller():
    if PACKAGE_NAME not in sys.modules:
        init_py = LIGHT_SOURCE / "constraintbox" / "__init__.py"
        spec = importlib.util.spec_from_file_location(
            PACKAGE_NAME, init_py, submodule_search_locations=[str(init_py.parent)]
        )
        assert spec is not None and spec.loader is not None
        package = importlib.util.module_from_spec(spec)
        sys.modules[PACKAGE_NAME] = package
        spec.loader.exec_module(package)
    return importlib.import_module(f"{PACKAGE_NAME}.premortem_remediation")


controller = _load_controller()
contracts = importlib.import_module(f"{PACKAGE_NAME}.premortem_contracts")


def _digest(char: str) -> str:
    return char * 64


def _policy(iteration_bound: int | None = 3) -> dict[str, object]:
    return {
        "schema": contracts.RUN_POLICY_SCHEMA,
        "run_policy_id": "premortem-profile-remediation",
        "completion_gate": {
            "gate_id": "control-plane-profile-completion",
            "executor_kind": "deterministic_command",
            "executable_ref": "constraintbox.verify_control_plane_profile",
            "definition_sha256": _digest("a"),
        },
        "required_regression_gates": [
            {
                "gate_id": "control-plane-profile-import",
                "executor_kind": "deterministic_command",
                "executable_ref": "constraintbox.verify_control_plane_profile_import",
                "definition_sha256": _digest("b"),
            }
        ],
        "scope_paths": ["constraint_box/control_plane_profile"],
        "diff_bound": 1,
        "promotion_rule_id": "first-receipt-verified-canonical-order",
        "iteration_bound": iteration_bound,
        "time_bound_seconds": None,
        "progress_measure": {
            "measure_id": controller.REMAINING_CANDIDATE_FRONTIER_MEASURE,
            "measure_domain": "natural_nonnegative_integer",
            "terminal_value": 0,
            "strict_per_retry_decrease": True,
        },
        "output_surfaces": ["structured_json", "typed_receipt"],
        "claim_ceiling": "receipt-bound control-plane profile repair only",
    }


def _concern() -> dict[str, object]:
    return {
        "schema": contracts.CONCERN_RECORD_SCHEMA,
        "concern_id": "concern-profile-alpha",
        "source": "premortem-remediation-skill",
        "locator": "constraint_box/control_plane_profile:missing-provider",
        "description": "The bounded profile is missing a required provider.",
        "discovered_at": "2026-08-11T09:00:00Z",
        "source_sha256": _digest("c"),
    }


def _issue(concern: dict[str, object]) -> tuple[dict[str, object], dict[str, object]]:
    receipt = {
        "schema": controller.CLASSIFICATION_RECEIPT_SCHEMA,
        "issue_id": "issue-profile-alpha",
        "concern_id": concern["concern_id"],
        "gate_id": "classify-control-plane-profile",
        "gate_definition_sha256": _digest("d"),
        "disposition": "OPEN",
        "reason_code": "PROFILE_PROVIDER_MISSING",
        "captured_at": "2026-08-11T09:01:00Z",
    }
    return (
        {
            "schema": contracts.ISSUE_SCHEMA,
            "issue_id": "issue-profile-alpha",
            "concern_id": concern["concern_id"],
            "classification_gate": {
                "gate_id": "classify-control-plane-profile",
                "executor_kind": "deterministic_command",
                "executable_ref": "constraintbox.classify_control_plane_profile",
                "definition_sha256": _digest("d"),
            },
            "disposition": "OPEN",
            "reason_code": "PROFILE_PROVIDER_MISSING",
            "classification_receipt_sha256": contracts.canonical_sha256(receipt),
        },
        receipt,
    )


def _candidate(candidate_id: str = "candidate-profile-alpha", target: str = "e", action: str | None = None) -> dict[str, object]:
    return {
        "schema": contracts.REPAIR_CANDIDATE_SCHEMA,
        "candidate_id": candidate_id,
        "issue_id": "issue-profile-alpha",
        "producer_type": "skill",
        "producer_id": f"premortem-skill-{candidate_id[-5:]}",
        "proposed_action": {
            "action_type": action or controller.CONTROL_PLANE_PROFILE_REPAIR_ACTION,
            "scope_paths": ["constraint_box/control_plane_profile"],
            "diff_bound": 1,
            "evidence_effect": "non_evidence_increasing",
            "target_sha256": _digest(target),
        },
        "evidence_refs": ["receipt:premortem-alpha"],
        "produced_at": "2026-08-11T09:02:00Z",
    }


def _binding(candidate: dict[str, object]) -> tuple[dict[str, object], list[dict[str, object]]]:
    binding_id = f"binding-{candidate['candidate_id'][-5:]}"
    records = [
        {
            "schema": controller.PRODUCER_BINDING_EVIDENCE_SCHEMA,
            "binding_id": binding_id,
            "producer_id": candidate["producer_id"],
            "issue_id": candidate["issue_id"],
            "candidate_id": candidate["candidate_id"],
            "binding_state": state,
            "captured_at": f"2026-08-11T09:0{index + 3}:00Z",
        }
        for index, state in enumerate(contracts.BINDING_STATES)
    ]
    digests = [contracts.canonical_sha256(record) for record in records]
    return (
        {
            "schema": contracts.PRODUCER_BINDING_SCHEMA,
            "binding_id": binding_id,
            "producer_id": candidate["producer_id"],
            "issue_id": candidate["issue_id"],
            "binding_history": list(contracts.BINDING_STATES),
            "binding_state": "receipt_verified",
            "binding_evidence_sha256s": digests,
            "producer_receipt_sha256": digests[-1],
            "updated_at": "2026-08-11T09:07:00Z",
        },
        records,
    )


def _planned_action(
    policy_raw: dict[str, object], issue_raw: dict[str, object], binding_raw: dict[str, object], candidate_raw: dict[str, object], *, parent: dict[str, object] | None = None
):
    policy = contracts.validate_run_policy(policy_raw).value
    issue = contracts.validate_issue(issue_raw).value
    binding = contracts.validate_producer_binding(binding_raw).value
    candidate = contracts.validate_repair_candidate(candidate_raw, policy).value
    assert policy is not None and issue is not None and binding is not None and candidate is not None
    if parent is None:
        action = contracts.admit_repair_candidate(candidate, binding, issue, policy, round_index=0).value
    else:
        previous_action = controller._action_from_raw(parent["action"])
        assert previous_action is not None
        previous_gate = contracts.validate_gate_run(parent["gate_run"], policy, previous_action).value
        assert previous_gate is not None
        action = contracts.admit_repair_candidate(
            candidate,
            binding,
            issue,
            policy,
            round_index=previous_action.round_index + 1,
            excluded_repair_action_fingerprints=(parent["excluded_repair_action_fingerprint"],),
            parent_gate_run=previous_gate,
        ).value
    assert action is not None
    return policy, candidate, action


def _execution_artifacts(policy, candidate, action, *, result: str = "PASS", measure: int = 0, input_state: str = "1", output_state: str = "2"):
    application_at = "2026-08-11T09:08:00Z"
    receipt = {
        "schema": controller.EXTERNAL_ACTION_RECEIPT_SCHEMA,
        "executor_asset_id": "control-plane-profile-external-adapter",
        "action_type": controller.CONTROL_PLANE_PROFILE_REPAIR_ACTION,
        "action_id": action.action_id,
        "action_sha256": action.sha256,
        "candidate_id": candidate.candidate_id,
        "candidate_sha256": candidate.sha256,
        "run_policy_sha256": policy.sha256,
        "target_sha256": candidate.proposed_action.target_sha256,
        "input_state_sha256": _digest(input_state),
        "output_state_sha256": _digest(output_state),
        "executed_at": application_at,
        "execution_claim_ceiling": "test-only deterministic external receipt; no production repair claimed",
    }
    application = {
        "schema": contracts.ACTION_APPLICATION_SCHEMA,
        "application_id": f"application-{action.round_index}",
        "action_id": action.action_id,
        "action_sha256": action.sha256,
        "executor_asset_id": receipt["executor_asset_id"],
        "execution_receipt_sha256": contracts.canonical_sha256(receipt),
        "input_state_sha256": receipt["input_state_sha256"],
        "output_state_sha256": receipt["output_state_sha256"],
        "applied_at": application_at,
    }
    gate = {
        "schema": contracts.GATE_RUN_SCHEMA,
        "gate_run_id": f"gate-{action.round_index}",
        "action_id": action.action_id,
        "action_sha256": action.sha256,
        "run_policy_sha256": policy.sha256,
        "round_index": action.round_index,
        "aggregate_gate_id": policy.completion_gate.gate_id,
        "aggregate_gate_definition_sha256": policy.completion_gate.definition_sha256,
        "aggregate_result": result,
        "required_gate_results": [
            {"gate_id": item.gate_id, "definition_sha256": item.definition_sha256, "result": result}
            for item in policy.required_regression_gates
        ],
        "input_state_sha256": receipt["output_state_sha256"],
        "current_state_sha256": receipt["output_state_sha256"],
        "measure_value": measure,
        "executed_at": "2026-08-11T09:09:00Z",
    }
    return {"execution_receipt_sha256": contracts.canonical_sha256(receipt), "receipt": receipt}, application, gate


def _request(
    *,
    policy: dict[str, object] | None = None,
    candidate: dict[str, object] | None = None,
    frontier: list[str] | None = None,
    parent: dict[str, object] | None = None,
    result: str = "PASS",
    measure: int = 0,
    external: bool = True,
) -> dict[str, object]:
    policy = policy or _policy()
    concern = _concern()
    issue, classification = _issue(concern)
    candidate = candidate or _candidate()
    binding, evidence = _binding(candidate)
    policy_value, candidate_value, action = _planned_action(policy, issue, binding, candidate, parent=parent)
    receipt, application, gate = _execution_artifacts(policy_value, candidate_value, action, result=result, measure=measure)
    fingerprint = contracts.repair_action_fingerprint(candidate_value)
    return {
        "schema": controller.REMEDIATION_REQUEST_SCHEMA,
        "run_id": "premortem-profile-run",
        "captured_at": "2026-08-11T09:10:00Z",
        "run_policy": policy,
        "concern": concern,
        "issue": issue,
        "classification_receipt": classification,
        "producer_binding": binding,
        "binding_evidence": evidence,
        "repair_candidate": candidate,
        "candidate_frontier": frontier or [fingerprint],
        "execution_receipt": receipt if external else None,
        "action_application": application if external else None,
        "gate_run": gate if external else None,
        "parent": parent,
    }


def test_external_pass_receipt_holds_until_a_trusted_gate_runs(tmp_path: Path) -> None:
    result = controller.run_remediation(_request(), db_path=tmp_path / "state.sqlite3")

    assert result["terminal"] == "HOLD"
    assert result["state_outcome"] == "HOLD"
    assert result["reason_code"] == "HOLD_RECEIPT_VALIDATED_AWAITING_TRUSTED_GATE"
    assert result["issue_scope"] == "single_issue_run"
    assert "single-issue" in result["claim_ceiling"]
    assert result["attempt"]["fixture_mode"] is False
    assert result["attempt"]["binding_states"] == list(contracts.BINDING_STATES)
    assert result["external_action_execution"] == "receipt_bound_external_action_only"
    assert result["state_verification"]["independent_external_execution_proof"] == "not_claimed"


def test_missing_external_application_holds_without_invocation(tmp_path: Path) -> None:
    result = controller.run_remediation(_request(external=False), db_path=tmp_path / "state.sqlite3")

    assert result["terminal"] == "HOLD"
    assert result["reason_code"] == "HOLD_EXTERNAL_ACTION_APPLICATION_REQUIRED"
    assert result["attempt"]["binding_states"] == ["declared", "bound_reference"]
    assert result["external_action_execution"] == "not_claimed"


def test_unknown_action_is_proposed_for_owner_without_execution(tmp_path: Path) -> None:
    candidate = _candidate(action="rewrite_everything")
    result = controller.run_remediation(_request(candidate=candidate, external=False), db_path=tmp_path / "state.sqlite3")

    assert result["terminal"] == "PROPOSED_FOR_OWNER"
    assert result["state_outcome"] == "HOLD"
    assert result["reason_code"] == "ACTION_NOT_IN_CLOSED_REGISTRY"


def test_tampered_receipt_and_severed_gate_refuse(tmp_path: Path) -> None:
    tampered = _request()
    tampered["execution_receipt"]["receipt"]["output_state_sha256"] = _digest("9")
    first = controller.run_remediation(tampered, db_path=tmp_path / "tampered.sqlite3")
    assert first["terminal"] == "REFUSE"
    assert first["reason_code"] == "REFUSE_EXECUTION_RECEIPT_HASH_MISMATCH"

    severed = _request()
    severed["gate_run"]["input_state_sha256"] = _digest("9")
    second = controller.run_remediation(severed, db_path=tmp_path / "severed.sqlite3")
    assert second["terminal"] == "REFUSE"
    assert second["reason_code"] == "REFUSE_GATE_APPLICATION_SEVERED"

    severed_application = _request()
    severed_application["action_application"]["execution_receipt_sha256"] = _digest("f")
    third = controller.run_remediation(
        severed_application, db_path=tmp_path / "severed-application.sqlite3"
    )
    assert third["terminal"] == "REFUSE"
    assert third["reason_code"] == "REFUSE_ACTION_APPLICATION_RECEIPT_HASH_MISMATCH"


def test_parent_must_be_a_retained_hold_attempt(tmp_path: Path) -> None:
    alpha = _candidate("candidate-profile-alpha", "e")
    beta = _candidate("candidate-profile-beta", "f")
    alpha_value = contracts.validate_repair_candidate(alpha, _policy()).value
    beta_value = contracts.validate_repair_candidate(beta, _policy()).value
    assert alpha_value is not None and beta_value is not None

    held_root = controller.run_remediation(
        _request(
            candidate=alpha,
            frontier=[
                contracts.repair_action_fingerprint(alpha_value),
                contracts.repair_action_fingerprint(beta_value),
            ],
            result="FAIL",
            measure=1,
        ),
        db_path=tmp_path / "missing-parent.sqlite3",
    )
    missing_parent = copy.deepcopy(held_root["continuation"])
    missing_parent["attempt_id"] = "not-a-retained-attempt"
    missing = controller.run_remediation(
        _request(
            candidate=beta,
            frontier=[contracts.repair_action_fingerprint(beta_value)],
            parent=missing_parent,
        ),
        db_path=tmp_path / "missing-parent.sqlite3",
    )
    assert missing["terminal"] == "REFUSE"
    assert missing["reason_code"] == "REFUSE_PARENT_ATTEMPT_UNVERIFIED"

    policy_raw = _policy()
    concern = _concern()
    issue, _ = _issue(concern)
    binding, _ = _binding(alpha)
    policy, alpha_value, action = _planned_action(policy_raw, issue, binding, alpha)
    _, _, failed_gate = _execution_artifacts(policy, alpha_value, action, result="FAIL", measure=1)
    settled = controller.run_remediation(
        _request(policy=policy_raw, candidate=alpha),
        db_path=tmp_path / "settled-parent.sqlite3",
    )
    assert settled["terminal"] == "HOLD"
    non_hold_parent = {
        "attempt_id": settled["attempt_id"],
        "issue_id": issue["issue_id"],
        "action": action.as_dict(),
        "gate_run": failed_gate,
        "excluded_repair_action_fingerprint": contracts.repair_action_fingerprint(alpha_value),
    }
    non_hold = controller.run_remediation(
        _request(
            policy=policy_raw,
            candidate=beta,
            frontier=[contracts.repair_action_fingerprint(beta_value)],
            parent=non_hold_parent,
        ),
        db_path=tmp_path / "settled-parent.sqlite3",
    )
    assert non_hold["terminal"] == "REFUSE"
    assert non_hold["reason_code"] == "REFUSE_PARENT_GATE_ARTIFACT_MISMATCH"


def test_failed_fresh_gate_at_declared_bound_expires(tmp_path: Path) -> None:
    result = controller.run_remediation(
        _request(policy=_policy(iteration_bound=1), result="FAIL", measure=0),
        db_path=tmp_path / "bound.sqlite3",
    )

    assert result["terminal"] == "EXHAUSTED"
    assert result["state_outcome"] == "EXPIRED"
    assert result["reason_code"] == "ITERATION_BOUND_REACHED"


def test_failed_gate_with_no_candidate_remainder_exhausts(tmp_path: Path) -> None:
    result = controller.run_remediation(
        _request(result="FAIL", measure=0), db_path=tmp_path / "frontier-exhausted.sqlite3"
    )

    assert result["terminal"] == "EXHAUSTED"
    assert result["reason_code"] == "CANDIDATE_FRONTIER_EXHAUSTED"
    assert result["continuation"] is None


def test_stale_gate_timestamp_is_severed_from_application(tmp_path: Path) -> None:
    request = _request()
    request["gate_run"]["executed_at"] = request["action_application"]["applied_at"]

    result = controller.run_remediation(request, db_path=tmp_path / "stale-gate.sqlite3")

    assert result["terminal"] == "REFUSE"
    assert result["reason_code"] == "REFUSE_GATE_APPLICATION_SEVERED"


def test_gate_measure_must_match_declared_frontier_transition(tmp_path: Path) -> None:
    result = controller.run_remediation(
        _request(result="FAIL", measure=1), db_path=tmp_path / "frontier-mismatch.sqlite3"
    )

    assert result["terminal"] == "REFUSE"
    assert result["reason_code"] == "REFUSE_GATE_FRONTIER_MEASURE_MISMATCH"


def test_parent_linked_next_round_requires_new_semantic_action_and_lower_measure(tmp_path: Path) -> None:
    alpha = _candidate("candidate-profile-alpha", "e")
    beta = _candidate("candidate-profile-beta", "f")
    alpha_value = contracts.validate_repair_candidate(alpha, _policy()).value
    beta_value = contracts.validate_repair_candidate(beta, _policy()).value
    assert alpha_value is not None and beta_value is not None
    root = _request(
        candidate=alpha,
        frontier=[contracts.repair_action_fingerprint(alpha_value), contracts.repair_action_fingerprint(beta_value)],
        result="FAIL",
        measure=1,
    )
    first = controller.run_remediation(root, db_path=tmp_path / "state.sqlite3")
    assert first["terminal"] == "HOLD"
    assert first["reason_code"] == "AWAITING_NEXT_RECEIPT_VERIFIED_CANDIDATE"

    child = _request(
        candidate=beta,
        frontier=[contracts.repair_action_fingerprint(beta_value)],
        parent=first["continuation"],
        result="PASS",
        measure=0,
    )
    second = controller.run_remediation(child, db_path=tmp_path / "state.sqlite3")
    assert second["terminal"] == "HOLD"
    assert second["reason_code"] == "HOLD_RECEIPT_VALIDATED_AWAITING_TRUSTED_GATE"
    assert second["attempt"]["parent_attempt_id"] == first["attempt_id"]
    assert second["attempt"]["frontier_before"] == 1
    assert second["attempt"]["frontier_after"] == 0

    repeated_root = controller.run_remediation(
        copy.deepcopy(root), db_path=tmp_path / "nondecreasing.sqlite3"
    )
    nondecreasing = _request(
        candidate=beta,
        frontier=[contracts.repair_action_fingerprint(beta_value)],
        parent=repeated_root["continuation"],
        result="FAIL",
        measure=1,
    )
    blocked = controller.run_remediation(nondecreasing, db_path=tmp_path / "nondecreasing.sqlite3")
    assert blocked["terminal"] == "HOLD"
    assert blocked["reason_code"] == "NONDECREASING_RETRY_MEASURE"

    forged_parent = copy.deepcopy(first["continuation"])
    forged_parent["gate_run"]["gate_run_id"] = "forged-parent-gate"
    forged = _request(
        candidate=beta,
        frontier=[contracts.repair_action_fingerprint(beta_value)],
        parent=forged_parent,
        result="PASS",
        measure=0,
    )
    rejected = controller.run_remediation(forged, db_path=tmp_path / "state.sqlite3")
    assert rejected["terminal"] == "REFUSE"
    assert rejected["reason_code"] == "REFUSE_PARENT_GATE_ARTIFACT_MISMATCH"


def test_replay_is_exact_and_round_zero_cannot_be_reintroduced_with_changed_input(tmp_path: Path) -> None:
    request = _request()
    first = controller.run_remediation(copy.deepcopy(request), db_path=tmp_path / "state.sqlite3")
    second = controller.run_remediation(copy.deepcopy(request), db_path=tmp_path / "state.sqlite3")
    assert second["terminal"] == "HOLD"
    assert second["attempt_id"] == first["attempt_id"]
    assert second["selection_sha256"] == first["selection_sha256"]

    changed = _request(candidate=_candidate(target="f"))
    third = controller.run_remediation(changed, db_path=tmp_path / "state.sqlite3")
    assert third["terminal"] == "REFUSE"


def test_external_receipt_cannot_be_reused_under_a_new_run_id(tmp_path: Path) -> None:
    first_request = _request()
    first = controller.run_remediation(first_request, db_path=tmp_path / "state.sqlite3")
    assert first["terminal"] == "HOLD"

    replayed = copy.deepcopy(first_request)
    replayed["run_id"] = "different-run-id"
    reused = controller.run_remediation(replayed, db_path=tmp_path / "state.sqlite3")

    assert reused["terminal"] == "REFUSE"
    assert reused["reason_code"] == "REFUSE_EXECUTION_RECEIPT_REUSED"


def test_next_round_frontier_must_be_exact_parent_remainder(tmp_path: Path) -> None:
    alpha = _candidate("candidate-profile-alpha", "e")
    beta = _candidate("candidate-profile-beta", "f")
    gamma = _candidate("candidate-profile-gamma", "9")
    alpha_value = contracts.validate_repair_candidate(alpha, _policy()).value
    beta_value = contracts.validate_repair_candidate(beta, _policy()).value
    gamma_value = contracts.validate_repair_candidate(gamma, _policy()).value
    assert alpha_value is not None and beta_value is not None and gamma_value is not None

    first = controller.run_remediation(
        _request(
            candidate=alpha,
            frontier=[
                contracts.repair_action_fingerprint(alpha_value),
                contracts.repair_action_fingerprint(beta_value),
            ],
            result="FAIL",
            measure=1,
        ),
        db_path=tmp_path / "state.sqlite3",
    )
    assert first["terminal"] == "HOLD"

    substituted = controller.run_remediation(
        _request(
            candidate=gamma,
            frontier=[contracts.repair_action_fingerprint(gamma_value)],
            parent=first["continuation"],
            result="PASS",
            measure=0,
        ),
        db_path=tmp_path / "state.sqlite3",
    )
    assert substituted["terminal"] == "REFUSE"
    assert substituted["reason_code"] == "REFUSE_CONTINUATION_FRONTIER_SUBTRACTION_MISMATCH"


def test_declared_time_bound_holds_without_a_prepared_run_start(tmp_path: Path) -> None:
    policy = _policy()
    policy["time_bound_seconds"] = 60

    result = controller.run_remediation(
        _request(policy=policy, external=False), db_path=tmp_path / "state.sqlite3"
    )

    assert result["terminal"] == "HOLD"
    assert result["reason_code"] == "HOLD_TIME_BOUND_REQUIRES_PREPARED_ATTEMPT"
    assert result["external_action_execution"] == "not_claimed"


def test_terminal_mapping_and_no_presentation_execution_surface() -> None:
    expected = {
        "VERIFIED_DONE": "SETTLED",
        "HOLD": "HOLD",
        "REFUSE": "REFUSE",
        "EXHAUSTED": "EXPIRED",
        "PROPOSED_FOR_OWNER": "HOLD",
    }
    for terminal, outcome in expected.items():
        assert controller._output(terminal, "TEST", "test")["state_outcome"] == outcome

    source = (LIGHT_SOURCE / "constraintbox" / "premortem_remediation.py").read_text()
    tree = ast.parse(source)
    forbidden_import_roots = {"subprocess", "webbrowser", "http", "os", "importlib"}
    observed_import_roots = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert not (observed_import_roots & forbidden_import_roots)

    prohibited_calls = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if not isinstance(node.func.value, ast.Name):
            continue
        base, attribute = node.func.value.id, node.func.attr
        if (
            (base == "os" and attribute in {"system", "popen"})
            or base == "subprocess"
            or (base == "webbrowser" and attribute == "open")
        ):
            prohibited_calls.append(f"{base}.{attribute}")
    assert not prohibited_calls

    assert ".html" not in source
    assert "http.server" not in source
