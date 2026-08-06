from __future__ import annotations

import copy
import hashlib
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import constraintbox.external_bounded_numerics as bounded_numerics_module
from constraintbox.capability_dispatch import run_capability_flow
from constraintbox.external_bounded_numerics import (
    SEVERED_EXIT_CODE,
    bounded_numerics_binding_from_dict,
    worker_path,
)
from constraintbox.external_runtime_profiles import selected_runtime_executable
from constraintbox.external_scipy_capability import (
    SCIPY_EXPM_PROFILE,
    validate_scipy_expm_receipt,
)
from constraintbox.failure_repair import (
    CAPABILITY_FLOW_RESULT_NAME,
    REPAIR_PLAN_NAME,
    FailureRepairError,
    _selected_action,
    write_repair_plan_for_run,
)
from constraintbox.intake import canonical_json, parse_json_object
from constraintbox.repair_outcome import (
    REPAIR_OUTCOME_NAME,
    _run_capability_suite_fresh_rerun_outcome,
    verify_fresh_rerun_outcome,
)
from constraintbox.mini_levos import (
    FlowNode,
    FlowPolicy,
    FlowTransition,
    HookKind,
    HookRegistration,
    HookResult,
    HookSignal,
    MiniLevRuntime,
    handler_code_sha256,
)


_CURRENT_RECEIPT: dict[str, object] = {}


def _failure_gate(_context: dict[str, object]) -> HookResult:
    """Emit one controller-owned external receipt fixture into a Mini-Lev flow."""

    receipt = _CURRENT_RECEIPT
    status = receipt["status"]
    signal = {"FAIL": HookSignal.BLOCKED, "PARKED": HookSignal.PARKED}[status]
    encoded = canonical_json(receipt).decode("utf-8")
    return HookResult(
        signal,
        {
            "capability_state": status,
            "capability_receipt_sha256": receipt["receipt_sha256"],
        },
        {
            "capability_state": status,
            "capability_receipt_sha256": receipt["receipt_sha256"],
            "capability_receipt_json": encoded,
        },
    )


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _write_canonical(path: Path, value: dict) -> None:
    path.write_bytes(canonical_json(value) + b"\n")


class FailureRepairTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self._temporary_directory.name)

    def tearDown(self) -> None:
        self._temporary_directory.cleanup()

    def _make_run(
        self,
        *,
        status: str,
        reason: str,
        name: str,
        result_schema: str = "constraintbox.external-capability-flow-result.v1",
    ) -> tuple[Path, dict]:
        global _CURRENT_RECEIPT
        run_root = self.root / name
        run_root.mkdir()
        receipt_body = {
            "schema": "constraintbox.external-capability-test-receipt.v1",
            "capability_id": "failure-repair-fixture-v1",
            "status": status,
            "reason": reason,
            "external_system": True,
            "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
            "promotion_allowed": False,
        }
        _CURRENT_RECEIPT = {
            **receipt_body,
            "receipt_sha256": _sha256(canonical_json(receipt_body)),
        }
        registration = HookRegistration(
            hook_id="failure-repair-fixture-gate",
            kind=HookKind.GATE,
            handler=_failure_gate,
            source_path=Path(__file__).resolve(),
            source_sha256=_sha256(Path(__file__).read_bytes()),
            code_sha256=handler_code_sha256(_failure_gate),
            allowed_signals=(HookSignal.BLOCKED, HookSignal.PARKED),
            allowed_update_keys=(
                "capability_state",
                "capability_receipt_sha256",
                "capability_receipt_json",
            ),
            max_output_bytes=65_536,
        )
        policy = FlowPolicy(
            flow_id="constraintbox.failure-repair-test-flow.v1",
            entry_node="fixture-gate",
            nodes=(FlowNode("fixture-gate", registration.hook_id),),
            transitions=(
                FlowTransition("fixture-gate", HookSignal.BLOCKED, "BLOCKED"),
                FlowTransition("fixture-gate", HookSignal.PARKED, "PARKED"),
                FlowTransition("fixture-gate", HookSignal.HOLD, "HOLD"),
            ),
            terminal_nodes=("BLOCKED", "PARKED", "HOLD"),
            required_nodes=("fixture-gate",),
            max_steps=2,
            max_visits_per_node=1,
            max_retries=0,
            max_context_bytes=65_536,
            max_event_bytes=65_536,
            max_receipt_bytes=524_288,
            claim_ceiling="bounded failure-repair fixture only",
        )
        runtime = MiniLevRuntime(
            policy,
            (registration,),
            run_id=f"failure-repair-{name}",
            ledger_path=run_root / "fixture_flow_events.jsonl",
        )
        flow_receipt = runtime.run({})
        disposition = {"FAIL": "BLOCKED", "PARKED": "PARKED"}[status]
        capability_receipt_path = run_root / "fixture_capability_receipt.json"
        flow_receipt_path = run_root / "fixture_flow_receipt.json"
        _write_canonical(capability_receipt_path, _CURRENT_RECEIPT)
        _write_canonical(flow_receipt_path, flow_receipt)
        request = {
            "schema": "constraintbox.external-capability-request.v1",
            "capability_id": "failure-repair-fixture-v1",
            "request_id": "repair-fixture-request",
        }
        result = {
            "schema": result_schema,
            "capability_id": "failure-repair-fixture-v1",
            "request_id": "repair-fixture-request",
            "request_sha256": _sha256(canonical_json(request)),
            "run_id": runtime.run_id,
            "flow_policy_sha256": runtime.policy_sha256,
            "disposition": disposition,
            "reason": reason,
            "capability_receipt_sha256": _CURRENT_RECEIPT["receipt_sha256"],
            "flow_receipt_sha256": flow_receipt["receipt_sha256"],
            "artifacts": {
                "capability_receipt": str(capability_receipt_path),
                "flow_receipt": str(flow_receipt_path),
                "flow_ledger": str(runtime.ledger_path),
                "flow_ledger_head": str(runtime.ledger_path.with_name(runtime.ledger_path.name + ".head")),
            },
            "external_system": True,
            "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
            "release_allowed": False,
            "engine_readiness_claim": False,
            "cr_truth_claim": False,
            "promotion_allowed": False,
            "claim_ceiling": "bounded failure-repair fixture only",
        }
        _write_canonical(run_root / CAPABILITY_FLOW_RESULT_NAME, result)
        return run_root, result

    def test_self_consistent_synthetic_flow_is_not_a_controller_origin(self) -> None:
        run_root, _result = self._make_run(
            status="FAIL",
            reason="exact_operation_controls_failed",
            name="blocked",
        )

        with self.assertRaisesRegex(
            FailureRepairError, "capability id is not controller-registered"
        ):
            write_repair_plan_for_run(run_root)
        self.assertFalse((run_root / REPAIR_PLAN_NAME).exists())

    def test_unknown_reason_defaults_to_park(self) -> None:
        action, selection_reason = _selected_action(
            "PARKED", "future_unmapped_failure"
        )
        self.assertEqual(action, "park")
        self.assertEqual(
            selection_reason,
            "controller_mapping_unmatched_default_park",
        )

    def test_registered_capability_still_requires_dispatch_origin_attestation(self) -> None:
        run_root, result = self._make_run(
            status="PARKED",
            reason="canonical_runtime_unavailable",
            name="jax-shape",
            result_schema="constraintbox.external-jax-capability-flow-result.v1",
        )
        result["capability_id"] = "jax-autodiff-v1"
        _write_canonical(run_root / CAPABILITY_FLOW_RESULT_NAME, result)

        with self.assertRaisesRegex(FailureRepairError, "controller_origin_attestation"):
            write_repair_plan_for_run(run_root)
        self.assertFalse((run_root / REPAIR_PLAN_NAME).exists())

    def test_controller_fault_injection_enters_the_verified_nonexecution_loop(self) -> None:
        """A real registered flow can park and emit only a bounded plan.

        The patch is a controller-test fault injection for the artifact probe;
        it deliberately prevents the external torch operation from running.
        It is not presented as an engine-operation success.
        """

        run_root = self.root / "controller-fault"
        parked_artifacts = {
            "status": "PARKED",
            "reason": "torch_artifact_unavailable",
            "artifacts": [],
        }
        with patch(
            "constraintbox.external_capability._inspect_torch_artifacts",
            return_value=parked_artifacts,
        ):
            result = run_capability_flow(
                capability_id="pytorch-jacobian-v1",
                request_id="failure-repair-controller-fault-1",
                run_root=run_root,
            )
            contract = write_repair_plan_for_run(run_root)

        self.assertEqual(result["disposition"], "PARKED")
        self.assertEqual(result["reason"], "torch_artifact_unavailable")
        self.assertTrue((run_root / "controller_origin_attestation.json").is_file())
        self.assertTrue((run_root / REPAIR_PLAN_NAME).is_file())
        self.assertEqual(contract["repair_plan"]["selected_action"], "park")
        self.assertFalse(contract["repair_plan"]["execution_authorized"])
        self.assertFalse(contract["promotion_allowed"])

    def test_real_scipy_replay_operation_failure_enters_nonexecution_repair_loop(
        self,
    ) -> None:
        """A genuine isolated replay failure is consumed by the repair planner.

        The test changes only the second controller call to the existing
        worker wrapper: it delegates all three calls to the actual subprocess
        implementation, but asks the replay child to use its already-defined
        ``scipy.linalg.expm`` severance control.  It does not manufacture a
        witness, receipt, subprocess result, or repair input.
        """

        with tempfile.TemporaryDirectory(dir="/private/tmp") as directory:
            run_root = Path(directory).resolve() / "scipy-replay-operation-failure"
            real_run_worker = bounded_numerics_module._run_worker
            invocations: list[dict[str, object]] = []

            def replay_only_poison(
                profile: object,
                case: object,
                binding: object,
                *,
                poisoned_operation: str | None = None,
            ) -> dict[str, object]:
                call_index = len(invocations)
                effective_poison = poisoned_operation
                if call_index == 1:
                    self.assertIsNone(poisoned_operation)
                    effective_poison = "scipy.linalg.expm"
                row = real_run_worker(
                    profile,
                    case,
                    binding,
                    poisoned_operation=effective_poison,
                )
                invocations.append(
                    {
                        "received_poison": poisoned_operation,
                        "effective_poison": effective_poison,
                        "returncode": row.get("returncode"),
                        "timeout": row.get("timeout"),
                    }
                )
                return row

            with patch.object(
                bounded_numerics_module,
                "_run_worker",
                side_effect=replay_only_poison,
            ) as worker_call:
                result = run_capability_flow(
                    capability_id=SCIPY_EXPM_PROFILE.capability_id,
                    request_id="failure-repair-scipy-replay-operation-v1",
                    run_root=run_root,
                )
                contract = write_repair_plan_for_run(run_root)

            self.assertEqual(worker_call.call_count, 3)
            self.assertEqual(
                [entry["received_poison"] for entry in invocations],
                [None, None, "scipy.linalg.expm"],
            )
            self.assertEqual(
                [entry["effective_poison"] for entry in invocations],
                [None, "scipy.linalg.expm", "scipy.linalg.expm"],
            )
            self.assertEqual(
                [entry["returncode"] for entry in invocations],
                [0, SEVERED_EXIT_CODE, SEVERED_EXIT_CODE],
            )
            self.assertEqual(
                [entry["timeout"] for entry in invocations],
                [False, False, False],
            )

            self.assertEqual(result["disposition"], "BLOCKED")
            self.assertEqual(result["reason"], "controller_recomputed_check_failed")
            self.assertTrue((run_root / "controller_origin_attestation.json").is_file())
            self.assertTrue((run_root / REPAIR_PLAN_NAME).is_file())

            receipt = parse_json_object(
                Path(result["artifacts"]["capability_receipt"]).read_bytes()
            )
            binding = bounded_numerics_binding_from_dict(
                SCIPY_EXPM_PROFILE, receipt["binding"]
            )
            self.assertEqual(
                validate_scipy_expm_receipt(
                    receipt,
                    expected_binding=binding,
                    expected_receipt_sha256=receipt["receipt_sha256"],
                    require_pass=False,
                ),
                (),
            )
            executable = selected_runtime_executable("python")
            self.assertIsNotNone(executable)
            expected_command = [
                str(executable),
                "-I",
                str(worker_path()),
                SCIPY_EXPM_PROFILE.worker_selector,
            ]
            self.assertEqual(receipt["normal"]["command"], expected_command)
            self.assertEqual(receipt["normal"]["returncode"], 0)
            self.assertFalse(receipt["normal"]["timeout"])
            self.assertIsInstance(receipt["normal"]["witness"], dict)
            self.assertNotEqual(receipt["normal"]["witness"]["pid"], os.getpid())
            self.assertEqual(
                receipt["normal"]["witness"]["exact_api"],
                ["scipy.linalg.expm"],
            )
            self.assertEqual(receipt["replay"]["command"], expected_command)
            self.assertEqual(receipt["replay"]["returncode"], SEVERED_EXIT_CODE)
            self.assertFalse(receipt["replay"]["timeout"])
            self.assertIsNone(receipt["replay"]["witness"])
            self.assertEqual(receipt["severance"]["command"], expected_command)
            self.assertEqual(receipt["severance"]["returncode"], SEVERED_EXIT_CODE)
            self.assertFalse(receipt["severance"]["timeout"])
            self.assertFalse(receipt["controls"]["replay"])
            self.assertTrue(receipt["controls"]["severance"])

            self.assertEqual(contract["failure_event"]["disposition"], "BLOCKED")
            self.assertEqual(
                contract["failure_event"]["receipt_reason_code"],
                "controller_recomputed_check_failed",
            )
            self.assertEqual(contract["repair_plan"]["selected_action"], "fresh_rerun")
            self.assertFalse(contract["repair_plan"]["execution_authorized"])
            self.assertEqual(
                contract["repair_plan"]["retry_budget"]["authorized_attempts"], 0
            )
            self.assertFalse(contract["promotion_allowed"])

            # The fixed suite hook follows after the test-local poison has
            # been removed. It runs the same registered SciPy profile with its
            # controller-derived request identity; no capability, worker,
            # command, or tolerance is supplied here.
            parent_plan_bytes = (run_root / REPAIR_PLAN_NAME).read_bytes()
            rerun_root = Path(directory).resolve() / "scipy-unpatched-fresh-rerun"
            outcome = _run_capability_suite_fresh_rerun_outcome(
                capability_run_root=run_root,
                run_root=rerun_root,
            )

            self.assertTrue((rerun_root / REPAIR_OUTCOME_NAME).is_file())
            self.assertEqual(outcome["disposition"], "PARKED")
            self.assertEqual(
                outcome["outcome_state"],
                "FRESH_RERUN_ELIGIBLE_REVIEW_REQUIRED",
            )
            self.assertFalse(outcome["repair_resolved"])
            self.assertFalse(outcome["promotion_allowed"])
            self.assertFalse(outcome["release_allowed"])
            self.assertEqual(outcome["parent"]["capability_id"], result["capability_id"])
            self.assertEqual(
                outcome["parent"]["repair_plan_sha256"],
                contract["repair_plan_sha256"],
            )
            self.assertEqual(outcome["rerun"]["capability_id"], result["capability_id"])
            self.assertEqual(outcome["rerun"]["disposition"], "ELIGIBLE")
            self.assertEqual(
                outcome["rerun"]["flow_policy_sha256"],
                result["flow_policy_sha256"],
            )
            self.assertTrue(
                outcome["verification"]["fresh_child_replay"]["summary"][
                    "independent_replay"
                ]
            )
            self.assertTrue(
                outcome["verification"]["fresh_child_replay"]["process"][
                    "fresh_python_process"
                ]
            )
            self.assertEqual(
                outcome["execution"]["parent_plan_authorized_attempts"], 0
            )
            self.assertFalse(
                outcome["execution"]["parent_plan_execution_authorized"]
            )
            self.assertEqual(
                outcome["execution"]["invocation_kind"],
                "controller_selected_capability_suite_hook",
            )
            self.assertEqual(
                outcome["execution"]["execution_authority"],
                "fixed_capability_suite_hook",
            )
            self.assertTrue(outcome["execution"]["automatic_fixed_replay"])
            self.assertFalse(outcome["execution"]["automatic_retry_or_tuning"])
            self.assertFalse(outcome["execution"]["automatic_retry_loop"])
            self.assertFalse(outcome["execution"]["automatic_tuning"])
            self.assertFalse(outcome["execution"]["llm_decision_authority"])
            self.assertEqual(
                (run_root / REPAIR_PLAN_NAME).read_bytes(), parent_plan_bytes
            )

            fresh_result = parse_json_object(
                (rerun_root / CAPABILITY_FLOW_RESULT_NAME).read_bytes()
            )
            fresh_receipt = parse_json_object(
                Path(fresh_result["artifacts"]["capability_receipt"]).read_bytes()
            )
            self.assertEqual(fresh_result["disposition"], "ELIGIBLE")
            self.assertEqual(fresh_receipt["status"], "PASS")
            self.assertEqual(fresh_receipt["reason"], "exact_operation_controls_passed")
            self.assertTrue(fresh_receipt["controls"]["replay"])
            self.assertEqual(fresh_receipt["replay"]["returncode"], 0)
            self.assertIsInstance(fresh_receipt["replay"]["witness"], dict)
            self.assertEqual(
                fresh_receipt["replay"]["witness"]["exact_api"],
                ["scipy.linalg.expm"],
            )
            self.assertEqual(
                fresh_receipt["severance"]["returncode"], SEVERED_EXIT_CODE
            )
            verified = verify_fresh_rerun_outcome(
                outcome,
                expected_run_root=rerun_root,
            )
            self.assertEqual(verified["outcome"], outcome)
            self.assertEqual(verified["rerun_disposition"], "ELIGIBLE")

    def test_unregistered_result_schema_is_refused(self) -> None:
        run_root, result = self._make_run(
            status="FAIL",
            reason="exact_operation_controls_failed",
            name="unknown-schema",
        )
        result["capability_id"] = "pytorch-jacobian-v1"
        result["schema"] = "constraintbox.external-unknown-capability-flow-result.v1"
        _write_canonical(run_root / CAPABILITY_FLOW_RESULT_NAME, result)

        with self.assertRaisesRegex(FailureRepairError, "schema differs from controller origin"):
            write_repair_plan_for_run(run_root)

    def test_noncanonical_result_is_rejected_before_a_plan_exists(self) -> None:
        run_root, result = self._make_run(
            status="FAIL",
            reason="exact_operation_controls_failed",
            name="noncanonical",
        )
        (run_root / CAPABILITY_FLOW_RESULT_NAME).write_bytes(
            b" " + canonical_json(result) + b"\n"
        )

        with self.assertRaisesRegex(FailureRepairError, "not canonical JSON"):
            write_repair_plan_for_run(run_root)

        self.assertFalse((run_root / REPAIR_PLAN_NAME).exists())

    def test_tampered_sidecar_cannot_reenter_a_synthetic_flow(self) -> None:
        run_root, result = self._make_run(
            status="FAIL",
            reason="exact_operation_controls_failed",
            name="tampered",
        )
        altered = copy.deepcopy(_CURRENT_RECEIPT)
        altered["reason"] = "worker_timeout"
        body = dict(altered)
        body.pop("receipt_sha256")
        altered["receipt_sha256"] = _sha256(canonical_json(body))
        _write_canonical(Path(result["artifacts"]["capability_receipt"]), altered)
        result["capability_receipt_sha256"] = altered["receipt_sha256"]
        result["reason"] = altered["reason"]
        _write_canonical(run_root / CAPABILITY_FLOW_RESULT_NAME, result)

        with self.assertRaisesRegex(
            FailureRepairError, "capability id is not controller-registered"
        ):
            write_repair_plan_for_run(run_root)

    def test_pass_or_overwrite_cannot_be_laundered_into_repair(self) -> None:
        run_root, result = self._make_run(
            status="FAIL",
            reason="exact_operation_controls_failed",
            name="pass",
        )
        result["disposition"] = "ELIGIBLE"
        _write_canonical(run_root / CAPABILITY_FLOW_RESULT_NAME, result)
        with self.assertRaisesRegex(FailureRepairError, "only a verified BLOCKED or PARKED"):
            write_repair_plan_for_run(run_root)

        run_root, _result = self._make_run(
            status="FAIL",
            reason="exact_operation_controls_failed",
            name="synthetic-repeat",
        )
        with self.assertRaisesRegex(
            FailureRepairError, "capability id is not controller-registered"
        ):
            write_repair_plan_for_run(run_root)
