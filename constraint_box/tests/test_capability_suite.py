from __future__ import annotations

import hashlib
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import constraintbox.external_bounded_numerics as bounded_numerics_module
from constraintbox.capability_dispatch import run_capability_flow
from constraintbox.capability_suite import (
    ComponentProcessError,
    RECEIPT_NAME,
    REPLAY_RESULT_NAME,
    _RUNTIME_CONTRACT_BY_CAPABILITY,
    _verify_fixed_component,
    run_capability_suite,
)
from constraintbox.external_scipy_capability import SCIPY_EXPM_PROFILE
from constraintbox.intake import canonical_json, parse_json_object
from constraintbox.repair_outcome import REPAIR_OUTCOME_NAME, verify_fresh_rerun_outcome


CAPABILITY_IDS = (
    "pytorch-jacobian-v1",
    "jax-autodiff-v1",
    "pysindy-affine-generator-v1",
    "julia-diffeq-v1",
    "scipy-expm-rotation-v1",
    "diffrax-tsit5-affine-flow-v1",
    "graph-topology-crosscheck-v1",
    "pydmd-discrete-rate-v1",
    "pymdp-two-state-inference-v1",
    "pykoopman-identity-edmd-v1",
    "quimb-cotengra-bounded-suite-v1",
    "multiengine-dlpack-diffeq-v1",
    "basic-packet-cross-engine-v1",
    "e3nn-wigner-crosscheck-v1",
)


def result_for(capability_id: str, request_id: str, root: Path) -> dict:
    artifacts = {
        "capability_receipt": root / "capability_receipt.json",
        "flow_receipt": root / "flow_receipt.json",
        "flow_ledger": root / "flow_events.jsonl",
        "flow_ledger_head": root / "flow_events.jsonl.head",
    }
    for path in artifacts.values():
        path.write_text("receipt", encoding="utf-8")
    return {
        "schema": "constraintbox.external-capability-flow-result.v1",
        "capability_id": capability_id,
        "request_id": request_id,
        "request_sha256": "1" * 64,
        "run_id": f"run-{capability_id}",
        "flow_policy_sha256": "2" * 64,
        "disposition": "ELIGIBLE",
        "reason": "fixture",
        "capability_receipt_sha256": "3" * 64,
        "flow_receipt_sha256": "4" * 64,
        "artifacts": {name: str(path) for name, path in artifacts.items()},
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": "fixture only",
    }


class CapabilitySuiteTests(unittest.TestCase):
    def test_replay_child_refuses_an_unissued_shape_correct_component_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "component"
            root.mkdir()
            result = result_for("pytorch-jacobian-v1", "suite-replay-1", root)
            (root / "capability_flow_result.json").write_bytes(
                canonical_json(result) + b"\n"
            )

            with self.assertRaises(ComponentProcessError):
                _verify_fixed_component(result=result, run_root=root)

    def test_runs_fixed_profiles_once_in_controller_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "suite"

            def fake_run(*, capability_id: str, request_id: str, run_root: Path):
                run_root.mkdir(parents=True, exist_ok=False)
                return result_for(capability_id, request_id, run_root)

            with patch(
                "constraintbox.capability_suite._run_fixed_component",
                side_effect=fake_run,
            ) as run, patch(
                "constraintbox.capability_suite._verify_fixed_component",
                side_effect=lambda **_kwargs: {"repair_plan": None},
            ) as verify:
                receipt, code = run_capability_suite(
                    request_id="suite-1",
                    run_root=root,
                )

            self.assertEqual(code, 0)
            self.assertEqual(receipt["disposition"], "ELIGIBLE")
            self.assertEqual(receipt["capability_ids"], list(CAPABILITY_IDS))
            portability = receipt["runtime_contract_report"]
            self.assertEqual(
                portability["schema"],
                "constraintbox.capability-runtime-contract-report.v1",
            )
            self.assertEqual(portability["runtime_profile_migration_state"], "PARTIAL")
            self.assertFalse(portability["full_external_suite_clean_install_verified"])
            self.assertFalse(portability["full_external_suite_profile_implemented"])
            self.assertFalse(portability["full_external_suite_portable_install_claim"])
            self.assertEqual(portability["clean_external_install_verified_capability_ids"], [])
            self.assertEqual(
                portability["profile_implemented_unverified_capability_ids"],
                [
                    capability_id
                    for capability_id in CAPABILITY_IDS
                    if _RUNTIME_CONTRACT_BY_CAPABILITY[capability_id][
                        "profile_implemented"
                    ]
                    is True
                ],
            )
            self.assertEqual(
                portability["legacy_host_bound_capability_ids"],
                [
                    "pykoopman-identity-edmd-v1",
                    "quimb-cotengra-bounded-suite-v1",
                    "multiengine-dlpack-diffeq-v1",
                    "basic-packet-cross-engine-v1",
                ],
            )
            self.assertTrue(receipt["sequential_execution"])
            self.assertTrue(receipt["controller_selected_order"])
            self.assertFalse(receipt["release_allowed"])
            self.assertFalse(receipt["promotion_allowed"])
            self.assertTrue((root / RECEIPT_NAME).is_file())
            for index, component in enumerate(receipt["components"], start=1):
                replay_relative_path = (
                    f"{index:02d}_{component['capability_id']}/{REPLAY_RESULT_NAME}"
                )
                self.assertEqual(
                    component["independent_replay_artifact"], replay_relative_path
                )
                replay_path = root / replay_relative_path
                self.assertTrue(replay_path.is_file())
                self.assertEqual(
                    component["independent_replay_sha256"],
                    hashlib.sha256(canonical_json(component["independent_replay"])).hexdigest(),
                )
                self.assertEqual(
                    component["runtime_contract"]["profile_implemented"],
                    component["capability_id"]
                    not in portability["legacy_host_bound_capability_ids"],
                )
                self.assertFalse(component["runtime_contract"]["clean_install_verified"])
            self.assertEqual(
                [call.kwargs["capability_id"] for call in run.call_args_list],
                list(CAPABILITY_IDS),
            )
            self.assertEqual(verify.call_count, len(CAPABILITY_IDS))

    def test_runtime_contract_documentation_is_exactly_aligned_with_controller_table(self) -> None:
        """A green run cannot hide a source/doc portability-boundary disagreement."""

        documentation = (
            Path(__file__).resolve().parents[1]
            / "docs"
            / "EXTERNAL_SIM_RUNTIME_CONTRACT.md"
        ).read_text(encoding="utf-8")
        self.assertEqual(set(_RUNTIME_CONTRACT_BY_CAPABILITY), set(CAPABILITY_IDS))
        for capability_id, contract in _RUNTIME_CONTRACT_BY_CAPABILITY.items():
            pattern = re.compile(
                rf"^\\| `{re.escape(capability_id)}` \\| .* \\| "
                rf"`{re.escape(str(contract['state']))}` \\|",
                re.MULTILINE,
            )
            self.assertRegex(documentation, pattern)
            self.assertFalse(contract["clean_install_verified"])

    def test_unverified_component_artifacts_cannot_make_the_suite_eligible(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "suite"

            def fake_run(*, capability_id: str, request_id: str, run_root: Path):
                run_root.mkdir(parents=True, exist_ok=False)
                if capability_id == "jax-autodiff-v1":
                    return {"fabricated": True}
                return result_for(capability_id, request_id, run_root)

            with patch(
                "constraintbox.capability_suite._run_fixed_component",
                side_effect=fake_run,
            ), patch(
                "constraintbox.capability_suite._verify_fixed_component",
                side_effect=lambda **_kwargs: {"repair_plan": None},
            ):
                receipt, code = run_capability_suite(
                    request_id="suite-2",
                    run_root=root,
                )

        self.assertEqual(code, 5)
        self.assertEqual(receipt["disposition"], "EVALUATION_ERROR")
        self.assertEqual(receipt["components"][1]["state"], "EVALUATION_ERROR")
        self.assertEqual(receipt["components"][1]["reason"], "component_exception")

    def test_nonpass_component_is_consumed_by_the_repair_contract_hook(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "suite"

            def fake_run(*, capability_id: str, request_id: str, run_root: Path):
                run_root.mkdir(parents=True, exist_ok=False)
                result = result_for(capability_id, request_id, run_root)
                if capability_id == "jax-autodiff-v1":
                    result["disposition"] = "PARKED"
                    result["reason"] = "canonical_runtime_unavailable"
                return result

            repair_plan = {
                "path": "/tmp/verified-repair-plan.json",
                "repair_plan_sha256": "9" * 64,
                "selected_action": "environment_repair_request",
                "execution_authorized": False,
            }
            with patch(
                "constraintbox.capability_suite._run_fixed_component",
                side_effect=fake_run,
            ), patch(
                "constraintbox.capability_suite._verify_fixed_component",
                side_effect=lambda *, result, **_kwargs: {
                    "repair_plan": repair_plan
                    if result["disposition"] == "PARKED"
                    else None
                },
            ) as verify, patch(
                "constraintbox.capability_suite._run_capability_suite_fresh_rerun_outcome"
            ) as rerun:
                receipt, code = run_capability_suite(
                    request_id="suite-repair-1",
                    run_root=root,
                )

        self.assertEqual(code, 4)
        self.assertEqual(receipt["disposition"], "PARKED")
        self.assertEqual(verify.call_count, len(CAPABILITY_IDS))
        component = receipt["components"][1]
        self.assertEqual(component["state"], "PARKED")
        self.assertEqual(
            component["repair_plan"]["selected_action"],
            "environment_repair_request",
        )
        self.assertFalse(component["repair_plan"]["execution_authorized"])
        self.assertEqual(component["controller_repair_hook"]["state"], "NOT_EXECUTED")
        self.assertEqual(
            component["controller_repair_hook"]["selected_action"],
            "environment_repair_request",
        )
        self.assertEqual(receipt["repair_hook"]["attempts"], 0)
        rerun.assert_not_called()

    def test_first_fresh_failure_reaches_one_fixed_controller_rerun(self) -> None:
        """Only the first controller-selected fresh action reaches the hook."""

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "suite"

            def fake_run(*, capability_id: str, request_id: str, run_root: Path):
                run_root.mkdir(parents=True, exist_ok=False)
                result = result_for(capability_id, request_id, run_root)
                if capability_id in {"jax-autodiff-v1", "scipy-expm-rotation-v1"}:
                    result["disposition"] = "BLOCKED"
                    result["reason"] = "controller_recomputed_check_failed"
                return result

            def fake_verify(*, result: dict, run_root: Path, **_kwargs: object) -> dict:
                return {
                    "repair_plan": {
                        "path": str(run_root / "repair_plan.json"),
                        "repair_plan_sha256": "9" * 64,
                        "selected_action": "fresh_rerun",
                        "execution_authorized": False,
                    }
                    if result["disposition"] == "BLOCKED" else None
                }

            def fake_rerun(*, capability_run_root: Path, run_root: Path) -> dict:
                run_root.mkdir(parents=True, exist_ok=False)
                outcome = {
                    "outcome_sha256": "a" * 64,
                    "outcome_state": "FRESH_RERUN_ELIGIBLE_REVIEW_REQUIRED",
                    "disposition": "PARKED",
                    "repair_resolved": False,
                    "promotion_allowed": False,
                    "release_allowed": False,
                    "execution": {
                        "invocation_kind": "controller_selected_capability_suite_hook",
                        "execution_authority": "fixed_capability_suite_hook",
                        "automatic_fixed_replay": True,
                        "automatic_tuning": False,
                        "llm_decision_authority": False,
                    },
                }
                (run_root / REPAIR_OUTCOME_NAME).write_bytes(
                    canonical_json(outcome) + b"\n"
                )
                return outcome

            with patch(
                "constraintbox.capability_suite._run_fixed_component",
                side_effect=fake_run,
            ), patch(
                "constraintbox.capability_suite._verify_fixed_component",
                side_effect=fake_verify,
            ), patch(
                "constraintbox.capability_suite.load_verified_repair_contract_for_run",
                return_value={
                    "contract": {
                        "repair_plan": {
                            "selected_action": "fresh_rerun",
                            "execution_authorized": False,
                        },
                        "repair_plan_sha256": "9" * 64,
                    }
                },
            ), patch(
                "constraintbox.capability_suite._run_capability_suite_fresh_rerun_outcome",
                side_effect=fake_rerun,
            ) as rerun:
                receipt, code = run_capability_suite(
                    request_id="suite-fresh-rerun-1",
                    run_root=root,
                )

        self.assertEqual(code, 1)
        self.assertEqual(receipt["disposition"], "BLOCKED")
        rerun.assert_called_once()
        self.assertEqual(
            set(rerun.call_args.kwargs), {"capability_run_root", "run_root"}
        )
        self.assertEqual(
            rerun.call_args.kwargs["capability_run_root"],
            root / "02_jax-autodiff-v1",
        )
        self.assertEqual(
            rerun.call_args.kwargs["run_root"],
            root / "controller_fresh_reruns" / "02_jax-autodiff-v1_9999999999999999",
        )
        hook = receipt["repair_hook"]
        self.assertTrue(hook["decision_made"])
        self.assertEqual(hook["selected_component_index"], 2)
        self.assertEqual(hook["selected_capability_id"], "jax-autodiff-v1")
        self.assertEqual(hook["state"], "VERIFIED")
        self.assertEqual(hook["attempts"], 1)
        self.assertTrue(hook["automatic_fixed_replay"])
        self.assertFalse(hook["automatic_tuning"])
        self.assertFalse(hook["llm_decision_authority"])
        self.assertNotIn("controller_repair_hook", receipt["components"][4])

    def test_live_suite_hook_replays_a_real_scipy_operation_failure(self) -> None:
        """The suite reaches the real contract-bound outcome runner.

        The test restricts the fixed suite to the registered SciPy profile and
        injects only its existing replay-operation severance control into the
        parent process.  Both the parent and the fresh follow-up execute real
        isolated ``scipy.linalg.expm`` workers; the follow-up is not mocked.
        """

        with tempfile.TemporaryDirectory(dir="/private/tmp") as directory:
            root = Path(directory).resolve() / "suite"
            original_worker = bounded_numerics_module._run_worker
            invocations: list[dict[str, object]] = []

            def replay_only_poison(
                profile: object,
                case: object,
                binding: object,
                *,
                poisoned_operation: str | None = None,
            ) -> dict[str, object]:
                effective_poison = poisoned_operation
                if len(invocations) == 1:
                    effective_poison = "scipy.linalg.expm"
                row = original_worker(
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
                    }
                )
                return row

            def run_real_blocked_parent(
                *, capability_id: str, request_id: str, run_root: Path
            ) -> dict:
                self.assertEqual(capability_id, SCIPY_EXPM_PROFILE.capability_id)
                return run_capability_flow(
                    capability_id=capability_id,
                    request_id=request_id,
                    run_root=run_root,
                )

            with patch.object(
                bounded_numerics_module,
                "_run_worker",
                side_effect=replay_only_poison,
            ), patch(
                "constraintbox.capability_suite._CAPABILITY_IDS",
                (SCIPY_EXPM_PROFILE.capability_id,),
            ), patch(
                "constraintbox.capability_suite._run_fixed_component",
                side_effect=run_real_blocked_parent,
            ):
                receipt, code = run_capability_suite(
                    request_id="suite-live-scipy-hook-1",
                    run_root=root,
                )

            self.assertEqual(code, 1)
            self.assertEqual(receipt["disposition"], "BLOCKED")
            self.assertEqual(
                [entry["effective_poison"] for entry in invocations],
                [
                    None,
                    "scipy.linalg.expm",
                    "scipy.linalg.expm",
                    None,
                    None,
                    "scipy.linalg.expm",
                ],
            )
            component = receipt["components"][0]
            self.assertEqual(component["state"], "BLOCKED")
            self.assertEqual(
                component["repair_plan"]["selected_action"], "fresh_rerun"
            )
            hook = component["controller_repair_hook"]
            self.assertEqual(hook["state"], "VERIFIED")
            self.assertEqual(hook["attempts"], 1)
            self.assertTrue(hook["automatic_fixed_replay"])
            self.assertFalse(hook["automatic_retry_loop"])
            self.assertFalse(hook["automatic_tuning"])
            self.assertFalse(hook["llm_decision_authority"])
            self.assertEqual(receipt["repair_hook"]["outcome_sha256"], hook["outcome_sha256"])
            outcome_path = root / hook["outcome_artifact"]
            self.assertTrue(outcome_path.is_file())
            outcome = parse_json_object(outcome_path.read_bytes())
            verified = verify_fresh_rerun_outcome(
                outcome,
                expected_run_root=root / hook["rerun_root"],
            )
            self.assertEqual(verified["outcome"], outcome)
            self.assertEqual(verified["rerun_disposition"], "ELIGIBLE")
