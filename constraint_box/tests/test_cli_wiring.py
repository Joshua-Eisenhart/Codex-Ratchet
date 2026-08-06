from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from constraintbox import DecisionRecord, Disposition, cli
from constraintbox.formal_registry import (
    FORMAL_MAX_PAYLOAD_BYTES,
    TASK_SYMBOLIC_POLYNOMIAL,
    TASK_WORKFLOW_GRAPH,
)
from constraintbox.ledger import HashChainLedger


class CliWiringTests(unittest.TestCase):
    def invoke(self, *arguments: str) -> tuple[int, dict]:
        output = io.StringIO()
        code = 0
        with patch.object(sys, "argv", ["constraintbox", *arguments]):
            with contextlib.redirect_stdout(output):
                try:
                    cli.main()
                except SystemExit as exc:
                    code = int(exc.code)
        return code, json.loads(output.getvalue())

    def test_all_subcommands_are_registered(self):
        parser = cli.build_parser()
        subparsers = next(
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        self.assertEqual(
            set(subparsers.choices),
            {
                "demo",
                "doctor",
                "runtime",
                "run",
                "solve",
                "sim",
                "ratchet",
                "estate",
                "estate-parity",
                "preflight",
                "lease",
                "discharge",
                "evidence",
                "applicability",
                "gate",
                "deps",
                "mmm",
                "crosscheck",
                "request",
                "engine-test",
                "box",
                "capability-box",
                "capability-suite",
                "integrated-workload",
                "admit-sim-evidence",
                "shared-affine-parity",
                "repair-plan",
                "repair-outcome",
                "observe-lev-eval",
                "advise",
                "formal",
                "cr-slice",
                "manifold-foundation",
                "exploratory-ijk",
                "candidate-world",
            },
        )

    def test_runtime_surface_has_no_executable_override_and_reaches_profile_registry(self):
        parser = cli.build_parser()
        parsed = parser.parse_args(["runtime", "inspect"])
        self.assertEqual(parsed.command, "runtime")
        self.assertEqual(parsed.runtime_command, "inspect")
        outer = next(
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        runtime = outer.choices["runtime"]
        nested = next(
            action
            for action in runtime._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        for name in ("list", "inspect", "verify"):
            options = {
                option
                for action in nested.choices[name]._actions
                for option in action.option_strings
            }
            self.assertEqual(options, {"-h", "--help", "--output"})
            self.assertNotIn("--python", options)
            self.assertNotIn("--runtime", options)

        reported = {
            "schema": "constraintbox.runtime-inspection.v1",
            "state": "ELIGIBLE",
            "promotion_allowed": False,
        }
        with patch.object(cli, "inspect_active_runtime", return_value=reported) as inspect:
            code, body = self.invoke("runtime", "inspect")
        self.assertEqual(code, 0)
        self.assertEqual(body, reported)
        inspect.assert_called_once_with()

    def test_lev_eval_observation_surface_has_only_fixed_binding_and_run_inputs(self):
        parser = cli.build_parser()
        parsed = parser.parse_args(
            [
                "observe-lev-eval",
                "--request-id",
                "historical-lev-eval-1",
                "--source-run-dir",
                "/tmp/foreign-lev-run",
                "--expected-execution-id",
                "foreign-run-1",
                "--expected-suite-id",
                "foreign-suite-1",
                "--run-dir",
                "/tmp/cb-observation",
            ]
        )
        self.assertEqual(parsed.command, "observe-lev-eval")
        outer = next(
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        options = {
            option
            for action in outer.choices["observe-lev-eval"]._actions
            for option in action.option_strings
        }
        self.assertEqual(
            options,
            {
                "-h",
                "--help",
                "--request-id",
                "--source-run-dir",
                "--expected-execution-id",
                "--expected-suite-id",
                "--run-dir",
                "--output",
            },
        )

    def test_lev_eval_observation_reaches_only_the_fixed_minilev_flow(self):
        returned = {
            "schema": "constraintbox.lev-eval-observation-flow-result.v1",
            "promotion_allowed": False,
        }
        with patch.object(
            cli,
            "run_lev_eval_observation_flow",
            return_value=SimpleNamespace(terminal="PARKED", as_dict=lambda: returned),
        ) as flow:
            code, value = self.invoke(
                "observe-lev-eval",
                "--request-id",
                "historical-lev-eval-1",
                "--source-run-dir",
                "/tmp/foreign-lev-run",
                "--expected-execution-id",
                "foreign-run-1",
                "--expected-suite-id",
                "foreign-suite-1",
                "--run-dir",
                "/tmp/cb-observation",
            )
        self.assertEqual(code, 4)
        self.assertEqual(value, returned)
        flow.assert_called_once_with(
            request_id="historical-lev-eval-1",
            source_run_dir=Path("/tmp/foreign-lev-run").resolve(),
            expected_execution_id="foreign-run-1",
            expected_suite_id="foreign-suite-1",
            run_root=Path("/tmp/cb-observation").resolve(),
        )

    def test_capability_box_surface_has_no_tool_or_transition_override(self):
        parser = cli.build_parser()
        parsed = parser.parse_args(
            [
                "capability-box",
                "--request",
                "/tmp/constraintbox-request.json",
                "--run-dir",
                "/tmp/constraintbox-capability-box",
            ]
        )
        self.assertEqual(parsed.command, "capability-box")
        outer = next(
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        options = {
            option
            for action in outer.choices["capability-box"]._actions
            for option in action.option_strings
        }
        self.assertEqual(
            options,
            {"-h", "--help", "--request", "--run-dir", "--output"},
        )
        for forbidden in (
            "--capability",
            "--tool",
            "--worker",
            "--gate",
            "--transition",
            "--release",
        ):
            self.assertNotIn(forbidden, options)

    def test_capability_box_reaches_fixed_controller_flow(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = root / "request.json"
            request.write_text("{}", encoding="utf-8")
            run_dir = root / "capability-box"
            returned = {
                "schema": "constraintbox.capability-box-run.v1",
                "capability_id": "pytorch-jacobian-v1",
                "disposition": "VERIFIED_EXTERNAL_CAPABILITY",
                "release_allowed": False,
                "promotion_allowed": False,
            }
            with patch.object(
                cli,
                "run_pytorch_capability_box",
                return_value=(returned, 0),
            ) as run:
                code, body = self.invoke(
                    "capability-box",
                    "--request",
                    str(request),
                    "--run-dir",
                    str(run_dir),
                )
        self.assertEqual(code, 0)
        self.assertEqual(body, returned)
        run.assert_called_once_with(b"{}", run_dir)

    def test_capability_box_output_cannot_enter_immutable_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = root / "request.json"
            request.write_text("{}", encoding="utf-8")
            run_dir = root / "capability-box"
            with patch.object(cli, "run_pytorch_capability_box") as run:
                code, body = self.invoke(
                    "capability-box",
                    "--request",
                    str(request),
                    "--run-dir",
                    str(run_dir),
                    "--output",
                    str(run_dir / "receipt.json"),
                )
        self.assertEqual(code, 5)
        self.assertEqual(body["disposition"], "EVALUATION_ERROR")
        self.assertEqual(body["reason"], "capability_box_configuration_error")
        self.assertFalse(body["release_allowed"])
        self.assertFalse(body["promotion_allowed"])
        run.assert_not_called()

    def test_capability_suite_surface_has_no_component_override(self):
        parser = cli.build_parser()
        parsed = parser.parse_args(
            [
                "capability-suite",
                "--request-id",
                "suite-1",
                "--run-dir",
                "/tmp/constraintbox-capability-suite",
            ]
        )
        self.assertEqual(parsed.command, "capability-suite")
        outer = next(
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        options = {
            option
            for action in outer.choices["capability-suite"]._actions
            for option in action.option_strings
        }
        self.assertEqual(
            options,
            {"-h", "--help", "--request-id", "--run-dir", "--output"},
        )
        self.assertNotIn("--capability", options)
        self.assertNotIn("--parallel", options)

    def test_capability_suite_reaches_fixed_controller_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_dir = root / "capability-suite"
            returned = {
                "schema": "constraintbox.capability-suite-receipt.v1",
                "disposition": "ELIGIBLE",
                "release_allowed": False,
                "promotion_allowed": False,
            }
            with patch.object(
                cli,
                "run_capability_suite",
                return_value=(returned, 0),
            ) as run:
                code, body = self.invoke(
                    "capability-suite",
                    "--request-id",
                    "suite-1",
                    "--run-dir",
                    str(run_dir),
                )
        self.assertEqual(code, 0)
        self.assertEqual(body, returned)
        run.assert_called_once_with(request_id="suite-1", run_root=run_dir.resolve())

    def test_repair_plan_surface_accepts_only_one_existing_capability_run(self):
        parser = cli.build_parser()
        parsed = parser.parse_args(
            [
                "repair-plan",
                "--capability-run-dir",
                "/tmp/constraintbox-capability-run",
            ]
        )
        self.assertEqual(parsed.command, "repair-plan")
        self.assertEqual(
            parsed.capability_run_dir,
            Path("/tmp/constraintbox-capability-run"),
        )
        outer = next(
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        options = {
            option
            for action in outer.choices["repair-plan"]._actions
            for option in action.option_strings
        }
        self.assertEqual(options, {"-h", "--help", "--capability-run-dir"})

    def test_repair_outcome_surface_is_explicit_and_has_no_semantic_overrides(self):
        parser = cli.build_parser()
        parsed = parser.parse_args(
            [
                "repair-outcome",
                "--capability-run-dir",
                "/tmp/constraintbox-parent-run",
                "--run-dir",
                "/tmp/constraintbox-rerun",
                "--execute-fresh-rerun",
            ]
        )
        self.assertEqual(parsed.command, "repair-outcome")
        self.assertTrue(parsed.execute_fresh_rerun)
        outer = next(
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        options = {
            option
            for action in outer.choices["repair-outcome"]._actions
            for option in action.option_strings
        }
        self.assertEqual(
            options,
            {
                "-h",
                "--help",
                "--capability-run-dir",
                "--run-dir",
                "--execute-fresh-rerun",
            },
        )
        for forbidden in (
            "--capability",
            "--request-id",
            "--action",
            "--worker",
            "--command",
            "--profile",
            "--verifier",
            "--tolerance",
            "--retry",
            "--output",
        ):
            self.assertNotIn(forbidden, options)
        with self.assertRaises(SystemExit):
            parser.parse_args(
                [
                    "repair-outcome",
                    "--capability-run-dir",
                    "/tmp/constraintbox-parent-run",
                    "--run-dir",
                    "/tmp/constraintbox-rerun",
                ]
            )

    def test_repair_outcome_reaches_only_fixed_acknowledged_controller_path(self):
        returned = {
            "schema": "constraintbox.capability-repair-outcome.v1",
            "rerun": {"disposition": "ELIGIBLE"},
            "release_allowed": False,
            "promotion_allowed": False,
        }
        with patch.object(
            cli,
            "run_fresh_rerun_outcome",
            return_value=returned,
        ) as run:
            code, body = self.invoke(
                "repair-outcome",
                "--capability-run-dir",
                "/tmp/constraintbox-parent-run",
                "--run-dir",
                "/tmp/constraintbox-rerun",
                "--execute-fresh-rerun",
            )
        self.assertEqual(code, 0)
        self.assertEqual(body, returned)
        run.assert_called_once_with(
            capability_run_root=Path("/tmp/constraintbox-parent-run"),
            run_root=Path("/tmp/constraintbox-rerun"),
            execute_fresh_rerun=True,
        )

    def test_advise_surface_is_advisory_only_and_controller_bounded(self):
        parser = cli.build_parser()
        parsed = parser.parse_args(
            [
                "advise",
                "--box-run",
                "/tmp/constraintbox-box-run",
                "--provider",
                "openrouter",
                "--run-dir",
                "/tmp/constraintbox-advice-run",
            ]
        )
        self.assertEqual(parsed.command, "advise")
        self.assertEqual(parsed.provider, "openrouter")
        outer = next(
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        options = {
            option
            for action in outer.choices["advise"]._actions
            for option in action.option_strings
        }
        self.assertEqual(
            options,
            {
                "-h",
                "--help",
                "--box-run",
                "--provider",
                "--run-dir",
                "--output",
            },
        )
        for forbidden in (
            "--endpoint",
            "--model",
            "--temperature",
            "--gate",
            "--release",
            "--retry",
        ):
            self.assertNotIn(forbidden, options)

    def test_advise_reaches_separate_sidecar_and_preserves_exit_state(self):
        for provider, state, expected_code in (
            ("nvidia", "ADVICE_ACCEPTED", 0),
            ("openrouter", "REJECTED", 1),
            ("openrouter", "PARKED", 4),
        ):
            with self.subTest(provider=provider, state=state):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    box_run = root / "box"
                    sidecar_run = root / "advice"
                    returned = {
                        "schema": "constraintbox.advisory-sidecar-receipt.v1",
                        "provider": provider,
                        "provider_state": state,
                        "advisory_only": True,
                        "changes_box_decision": False,
                        "decision_authority": False,
                        "release_allowed": False,
                        "promotion_allowed": False,
                    }
                    with patch.object(
                        cli,
                        "run_advisory_sidecar",
                        return_value=(returned, expected_code),
                    ) as run:
                        code, body = self.invoke(
                            "advise",
                            "--box-run",
                            str(box_run),
                            "--provider",
                            provider,
                            "--run-dir",
                            str(sidecar_run),
                        )
                self.assertEqual(code, expected_code)
                self.assertEqual(body, returned)
                run.assert_called_once_with(
                    box_run,
                    provider,
                    sidecar_run,
                )

    def test_advise_output_cannot_enter_box_or_sidecar_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            box_run = root / "box"
            sidecar_run = root / "advice"
            for case, output in (
                ("box", box_run / "result.json"),
                ("sidecar", sidecar_run / "result.json"),
            ):
                with self.subTest(case=case):
                    with patch.object(
                        cli,
                        "run_advisory_sidecar",
                    ) as run:
                        code, body = self.invoke(
                            "advise",
                            "--box-run",
                            str(box_run),
                            "--provider",
                            "nvidia",
                            "--run-dir",
                            str(sidecar_run),
                            "--output",
                            str(output),
                        )
                    self.assertEqual(code, 5)
                    self.assertEqual(body["disposition"], "HOLD")
                    self.assertEqual(
                        body["reason"],
                        "advisory_sidecar_configuration_error",
                    )
                    self.assertFalse(body["decision_authority"])
                    self.assertFalse(body["release_allowed"])
                    self.assertFalse(body["promotion_allowed"])
                    run.assert_not_called()
                    self.assertFalse(output.exists())

    def test_engine_test_capability_surface_accepts_fixed_arguments(self):
        parser = cli.build_parser()
        parsed = parser.parse_args(
            [
                "engine-test",
                "--capability",
                "pytorch-jacobian-v1",
                "--request-id",
                "request-1",
                "--run-dir",
                "/tmp/constraintbox-capability-run",
            ]
        )
        self.assertEqual(parsed.command, "engine-test")
        self.assertEqual(parsed.capability, "pytorch-jacobian-v1")
        self.assertEqual(parsed.request_id, "request-1")
        self.assertEqual(
            parsed.run_dir,
            Path("/tmp/constraintbox-capability-run"),
        )
        self.assertEqual(
            set(
                next(
                    action
                    for action in cli.build_parser()._actions
                    if isinstance(action, argparse._SubParsersAction)
                ).choices["engine-test"]._option_string_actions[
                    "--capability"
                ].choices
            ),
            {
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
            },
        )

    def test_engine_test_capability_requires_request_and_run_directory(self):
        cases = (
            ("missing-both", ()),
            ("missing-request", ("--run-dir", "/tmp/capability-run")),
            ("missing-run", ("--request-id", "request-1")),
        )
        for case, additional_arguments in cases:
            with self.subTest(case=case):
                with patch(
                    "constraintbox.cli.run_capability_flow"
                ) as run:
                    code, body = self.invoke(
                        "engine-test",
                        "--capability",
                        "pytorch-jacobian-v1",
                        *additional_arguments,
                    )
                self.assertEqual(code, 5)
                self.assertEqual(
                    body["schema"],
                    "constraintbox.external-capability-flow-error.v1",
                )
                self.assertEqual(body["capability_id"], "pytorch-jacobian-v1")
                self.assertEqual(body["disposition"], "HOLD")
                self.assertEqual(
                    body["reason"],
                    "external_capability_configuration_error",
                )
                self.assertIn(
                    "requires --request-id and --run-dir",
                    body["error"],
                )
                self.assertFalse(body["release_allowed"])
                self.assertFalse(body["promotion_allowed"])
                run.assert_not_called()

    def test_engine_test_capability_reaches_flow_and_maps_disposition(self):
        for disposition, expected_code in (
            ("ELIGIBLE", 0),
            ("BLOCKED", 1),
            ("PARKED", 4),
            ("HOLD", 5),
        ):
            with self.subTest(disposition=disposition):
                with tempfile.TemporaryDirectory() as directory:
                    run_dir = Path(directory) / "capability-run"
                    returned = {
                        "schema": "constraintbox.external-capability-flow-result.v1",
                        "capability_id": "pytorch-jacobian-v1",
                        "disposition": disposition,
                        "release_allowed": False,
                        "promotion_allowed": False,
                    }
                    with patch(
                        "constraintbox.cli.run_capability_flow",
                        return_value=returned,
                    ) as run, patch(
                        "constraintbox.cli.write_repair_plan_for_run"
                    ) as repair:
                        code, body = self.invoke(
                            "engine-test",
                            "--capability",
                            "pytorch-jacobian-v1",
                            "--request-id",
                            "request-1",
                            "--run-dir",
                            str(run_dir),
                        )
                self.assertEqual(code, expected_code)
                self.assertEqual(body, returned)
                run.assert_called_once_with(
                    capability_id="pytorch-jacobian-v1",
                    request_id="request-1",
                    run_root=run_dir.resolve(),
                )
                if disposition in {"BLOCKED", "PARKED"}:
                    repair.assert_called_once_with(run_dir.resolve())
                else:
                    repair.assert_not_called()

    def test_engine_test_capability_output_cannot_enter_immutable_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for case, output_suffix in (
                ("exact", ()),
                ("nested", ("receipts", "result.json")),
            ):
                with self.subTest(case=case):
                    run_dir = root / f"capability-run-{case}"
                    output = run_dir.joinpath(*output_suffix)
                    with patch(
                        "constraintbox.cli.run_capability_flow"
                    ) as run:
                        code, body = self.invoke(
                            "engine-test",
                            "--capability",
                            "pytorch-jacobian-v1",
                            "--request-id",
                            "request-1",
                            "--run-dir",
                            str(run_dir),
                            "--output",
                            str(output),
                        )
                    self.assertEqual(code, 5)
                    self.assertEqual(body["disposition"], "HOLD")
                    self.assertEqual(
                        body["reason"],
                        "external_capability_configuration_error",
                    )
                    self.assertIn(
                        "outside the capability receipt directory",
                        body["error"],
                    )
                    run.assert_not_called()
                    self.assertFalse(run_dir.exists())
                    self.assertFalse(output.exists())

    def test_formal_surface_is_controller_owned(self):
        parser = cli.build_parser()
        outer = next(
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        formal = outer.choices["formal"]
        inner = next(
            action
            for action in formal._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        self.assertEqual(set(inner.choices), {"list", "run", "temporal"})

        run_options = {
            option
            for action in inner.choices["run"]._actions
            for option in action.option_strings
        }
        self.assertEqual(
            run_options,
            {
                "-h",
                "--help",
                "--task",
                "--request-id",
                "--payload",
                "--run-dir",
                "--output",
            },
        )
        self.assertEqual(
            {
                option
                for action in inner.choices["temporal"]._actions
                for option in action.option_strings
            },
            {"-h", "--help", "--output"},
        )
        for forbidden in (
            "--backend",
            "--tool",
            "--solver",
            "--bounds",
            "--tolerance",
            "--runtime",
            "--timeout",
            "--python",
        ):
            self.assertNotIn(forbidden, run_options)
            with self.subTest(forbidden=forbidden):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        parser.parse_args(
                            ["formal", "temporal", forbidden, "untrusted"]
                        )

    def test_formal_list_reports_tools_and_internal_reference_separately(self):
        code, body = self.invoke("formal", "list")
        self.assertEqual(code, 0)
        self.assertEqual(body["schema"], "constraintbox.formal-catalog.v1")
        self.assertEqual(
            body["internal_reference_methods"][0]["name"],
            "bounded exhaustive enumeration",
        )
        self.assertFalse(
            body["internal_reference_methods"][0]["external_tool"]
        )
        self.assertEqual(body["optional_not_default"][0]["name"], "NumPy")

    def test_formal_run_reaches_registry_and_maps_every_disposition(self):
        task = cli.formal_task_kinds()[0]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / "payload.json"
            payload.write_bytes(b'{"typed": true}')
            run_dir = root / "formal-run"
            for disposition, expected_code in (
                (Disposition.ELIGIBLE, 0),
                (Disposition.BLOCKED, 1),
                (Disposition.PARKED, 4),
                (Disposition.HOLD, 5),
            ):
                with self.subTest(disposition=disposition.value):
                    decision = DecisionRecord(
                        schema="constraintbox.decision.v1",
                        request_id="request-1",
                        task_kind=task,
                        profile_id="fixed-profile",
                        policy_sha256="a" * 64,
                        input_sha256="b" * 64,
                        disposition=disposition,
                        reason="fixture",
                        evidence={},
                        claim_ceiling="bounded fixture only",
                    )
                    with patch.object(
                        cli,
                        "run_formal_task",
                        return_value=decision,
                    ) as run:
                        code, body = self.invoke(
                            "formal",
                            "run",
                            "--task",
                            task,
                            "--request-id",
                            "request-1",
                            "--payload",
                            str(payload),
                            "--run-dir",
                            str(run_dir),
                        )
                self.assertEqual(code, expected_code)
                self.assertEqual(body["disposition"], disposition.value)
                run.assert_called_once_with(
                    task_kind=task,
                    request_id="request-1",
                    payload=b'{"typed": true}',
                    run_root=run_dir.resolve(),
                )

    def test_second_formal_run_is_a_typed_hold_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / "payload.json"
            payload.write_bytes(
                b'{"edges":[["intake","proposal_ready"]],'
                b'"nodes":["intake","proposal_ready"]}'
            )
            run_dir = root / "formal-run"
            first_code, first_body = self.invoke(
                "formal",
                "run",
                "--task",
                TASK_WORKFLOW_GRAPH,
                "--request-id",
                "same-request",
                "--payload",
                str(payload),
                "--run-dir",
                str(run_dir),
            )
            second_code, second_body = self.invoke(
                "formal",
                "run",
                "--task",
                TASK_WORKFLOW_GRAPH,
                "--request-id",
                "same-request",
                "--payload",
                str(payload),
                "--run-dir",
                str(run_dir),
            )
        self.assertEqual(first_code, 0)
        self.assertEqual(first_body["disposition"], "ELIGIBLE")
        self.assertEqual(second_code, 5)
        self.assertEqual(second_body["disposition"], "HOLD")
        self.assertEqual(second_body["reason"], "formal_task_configuration_error")

    def test_formal_output_cannot_overlap_ledger_or_retained_head(self):
        task = cli.formal_task_kinds()[0]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / "payload.json"
            payload.write_bytes(b'{"typed": true}')
            for artifact_name in (
                "formal_decisions.jsonl",
                "formal_decisions.jsonl.head",
            ):
                with self.subTest(artifact_name=artifact_name):
                    run_dir = root / artifact_name.replace(".", "-")
                    output = run_dir / artifact_name
                    with patch.object(cli, "run_formal_task") as run:
                        code, body = self.invoke(
                            "formal",
                            "run",
                            "--task",
                            task,
                            "--request-id",
                            "request-1",
                            "--payload",
                            str(payload),
                            "--run-dir",
                            str(run_dir),
                            "--output",
                            str(output),
                        )
                    self.assertEqual(code, 5)
                    self.assertEqual(body["disposition"], "HOLD")
                    self.assertEqual(
                        body["reason"],
                        "formal_task_configuration_error",
                    )
                    self.assertIn(
                        "outside the formal run directory",
                        body["error"],
                    )
                    run.assert_not_called()
                    self.assertFalse(run_dir.exists())
                    self.assertFalse(output.exists())

    def test_formal_output_cannot_target_run_directory_or_subtree(self):
        task = cli.formal_task_kinds()[0]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / "payload.json"
            payload.write_bytes(b'{"typed": true}')
            for case, relative_output in (
                ("exact", None),
                ("nested", Path("request-1/nested/receipt.json")),
            ):
                with self.subTest(case=case):
                    run_dir = root / f"formal-run-{case}"
                    output = (
                        run_dir
                        if relative_output is None
                        else run_dir / relative_output
                    )
                    with patch.object(cli, "run_formal_task") as run:
                        code, body = self.invoke(
                            "formal",
                            "run",
                            "--task",
                            task,
                            "--request-id",
                            "request-1",
                            "--payload",
                            str(payload),
                            "--run-dir",
                            str(run_dir),
                            "--output",
                            str(output),
                        )
                    self.assertEqual(code, 5)
                    self.assertEqual(body["disposition"], "HOLD")
                    self.assertIn(
                        "outside the formal run directory",
                        body["error"],
                    )
                    run.assert_not_called()
                    self.assertFalse(run_dir.exists())
                    self.assertFalse(output.exists())

    def test_formal_output_outside_run_directory_is_written(self):
        task = cli.formal_task_kinds()[0]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / "payload.json"
            payload.write_bytes(b'{"typed": true}')
            run_dir = root / "formal-run"
            output = root / "receipts" / "decision.json"
            decision = DecisionRecord(
                schema="constraintbox.decision.v1",
                request_id="request-1",
                task_kind=task,
                profile_id="fixed-profile",
                policy_sha256="a" * 64,
                input_sha256="b" * 64,
                disposition=Disposition.ELIGIBLE,
                reason="fixture",
                evidence={},
                claim_ceiling="bounded fixture only",
            )
            with patch.object(
                cli,
                "run_formal_task",
                return_value=decision,
            ) as run:
                code, body = self.invoke(
                    "formal",
                    "run",
                    "--task",
                    task,
                    "--request-id",
                    "request-1",
                    "--payload",
                    str(payload),
                    "--run-dir",
                    str(run_dir),
                    "--output",
                    str(output),
                )
            self.assertEqual(code, 0)
            self.assertEqual(body["disposition"], "ELIGIBLE")
            self.assertEqual(
                json.loads(output.read_text(encoding="utf-8")),
                body,
            )
            run.assert_called_once_with(
                task_kind=task,
                request_id="request-1",
                payload=b'{"typed": true}',
                run_root=run_dir.resolve(),
            )

    def test_formal_payload_read_is_capped_before_the_controller(self):
        task = cli.formal_task_kinds()[0]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / "oversized.json"
            payload.write_bytes(b"x" * (FORMAL_MAX_PAYLOAD_BYTES * 4))
            run_dir = root / "formal-run"
            code, body = self.invoke(
                "formal",
                "run",
                "--task",
                task,
                "--request-id",
                "oversized-1",
                "--payload",
                str(payload),
                "--run-dir",
                str(run_dir),
            )
        self.assertEqual(code, 1)
        self.assertEqual(body["disposition"], "BLOCKED")
        self.assertEqual(body["reason"], "payload_exceeds_controller_bound")
        self.assertIsNone(body["input_sha256"])
        inspected = b"x" * (FORMAL_MAX_PAYLOAD_BYTES + 1)
        expected_evidence = {
            "observed_bytes": FORMAL_MAX_PAYLOAD_BYTES + 1,
            "maximum_bytes": FORMAL_MAX_PAYLOAD_BYTES,
            "inspected_prefix_bytes": FORMAL_MAX_PAYLOAD_BYTES + 1,
            "bounded_prefix_sha256": hashlib.sha256(inspected).hexdigest(),
            "input_digest_complete": False,
        }
        for key, value in expected_evidence.items():
            self.assertEqual(body["evidence"][key], value)
        self.assertTrue(body["evidence"]["python_runtime"]["stable"])

    def test_formal_payload_fifo_is_rejected_without_open_blocking(self):
        task = cli.formal_task_kinds()[0]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = root / "payload.fifo"
            os.mkfifo(payload)
            run_dir = root / "formal-run"
            with patch.object(cli, "run_formal_task") as run:
                code, body = self.invoke(
                    "formal",
                    "run",
                    "--task",
                    task,
                    "--request-id",
                    "fifo-1",
                    "--payload",
                    str(payload),
                    "--run-dir",
                    str(run_dir),
                )
        self.assertEqual(code, 5)
        self.assertEqual(body["disposition"], "HOLD")
        self.assertEqual(body["reason"], "formal_task_configuration_error")
        self.assertIn("regular file", body["error"])
        run.assert_not_called()
        self.assertFalse(run_dir.exists())

    def test_formal_json_resource_faults_are_typed_blocked_decisions(self):
        integer_digit_limit = sys.get_int_max_str_digits()
        cases = [
            (
                TASK_WORKFLOW_GRAPH,
                b'{"nodes":'
                + (b"[" * (sys.getrecursionlimit() + 100))
                + b'"node"'
                + (b"]" * (sys.getrecursionlimit() + 100))
                + b',"edges":[]}',
            )
        ]
        if integer_digit_limit:
            cases.append(
                (
                    TASK_SYMBOLIC_POLYNOMIAL,
                    (
                        b'{"coefficients":[{"degree":0,"numerator":'
                        + (b"9" * (integer_digit_limit + 100))
                        + b',"denominator":1}],"claimed_canonical":[]}'
                    ),
                )
            )
        for index, (task, raw) in enumerate(cases):
            with self.subTest(task=task):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    payload = root / "payload.json"
                    payload.write_bytes(raw)
                    run_dir = root / "formal-run"
                    code, body = self.invoke(
                        "formal",
                        "run",
                        "--task",
                        task,
                        "--request-id",
                        f"resource-fault-{index}",
                        "--payload",
                        str(payload),
                        "--run-dir",
                        str(run_dir),
                    )
                    verified = HashChainLedger(
                        run_dir / "formal_decisions.jsonl"
                    ).verify()
                self.assertEqual(code, 1)
                self.assertEqual(body["disposition"], "BLOCKED")
                self.assertEqual(body["reason"], "strict_intake_failed")
                self.assertEqual(verified, (True, "1 record(s)"))

    def test_formal_temporal_runs_required_pair_and_maps_disposition(self):
        for disposition, expected_code in (
            ("ELIGIBLE", 0),
            ("BLOCKED", 1),
            ("PARKED", 4),
        ):
            with self.subTest(disposition=disposition):
                receipt = {
                    "schema": "constraintbox.formal-pair-receipt.v1",
                    "disposition": disposition,
                    "promotion_allowed": False,
                }
                with patch.object(
                    cli,
                    "run_temporal_pair",
                    return_value=receipt,
                ) as pair:
                    code, body = self.invoke("formal", "temporal")
                self.assertEqual(code, expected_code)
                self.assertEqual(body, receipt)
                pair.assert_called_once_with()

    def test_run_surface_does_not_expose_controller_authority(self):
        parser = cli.build_parser()
        subparsers = next(
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        run = subparsers.choices["run"]
        option_strings = {
            option
            for action in run._actions
            for option in action.option_strings
        }
        self.assertEqual(
            option_strings,
            {
                "-h",
                "--help",
                "--box-run-dir",
                "--run-dir",
            },
        )
        for option in option_strings:
            self.assertFalse(
                any(
                    word in option
                    for word in (
                        "command",
                        "profile",
                        "claim",
                        "gate",
                        "sim",
                        "retry",
                        "model",
                    )
                )
            )

    def test_run_reaches_agent_only_through_a_box_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            box_run = root / "box"
            agent_run = root / "agent"
            returned = {
                "schema": "constraintbox.agent-run.v1",
                "disposition": "PARKED",
                "release": None,
                "release_allowed": False,
                "promotion_allowed": False,
            }
            with patch.object(
                cli.agentrun,
                "run_agent",
                return_value=(returned, 4),
            ) as run:
                code, body = self.invoke(
                    "run",
                    "--box-run-dir",
                    str(box_run),
                    "--run-dir",
                    str(agent_run),
                )
        self.assertEqual(code, 4)
        self.assertEqual(body, returned)
        run.assert_called_once_with(
            box_run,
            agent_run,
        )

    def test_run_handoff_failure_is_typed_and_cannot_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(
                cli.agentrun,
                "run_agent",
                side_effect=cli.agentrun.AgentRunError(
                    "box snapshot invalid"
                ),
            ):
                code, body = self.invoke(
                    "run",
                    "--box-run-dir",
                    str(root / "box"),
                    "--run-dir",
                    str(root / "agent"),
                )
        self.assertEqual(code, 5)
        self.assertEqual(body["disposition"], "EVALUATION_ERROR")
        self.assertIn("box snapshot invalid", body["error"])
        self.assertFalse(body["release_allowed"])
        self.assertFalse(body["promotion_allowed"])

    def test_request_front_door_runs_three_solver_preflight(self):
        box_root = Path(__file__).resolve().parents[1]
        request = (
            box_root
            / "fixtures"
            / "requests"
            / "assemble_constraintbox_v1.json"
        )
        code, body = self.invoke(
            "request",
            "--request",
            str(request),
        )
        self.assertEqual(code, 0)
        decision = body["decision"]
        self.assertEqual(
            decision["disposition"],
            "ELIGIBLE_FOR_PROPOSAL",
        )
        self.assertEqual(decision["solver"]["z3"], "BOUNDED_SAT")
        self.assertEqual(decision["solver"]["cvc5"], "BOUNDED_SAT")
        self.assertEqual(
            decision["solver"]["enumeration"],
            "BOUNDED_SAT",
        )
        self.assertNotIn("context_text", body["user_context"])
        self.assertTrue(body["external_audit_brief"]["advisory_only"])

    def test_request_front_door_parks_unresolved_assumptions(self):
        box_root = Path(__file__).resolve().parents[1]
        original = json.loads(
            (
                box_root
                / "fixtures"
                / "requests"
                / "assemble_constraintbox_v1.json"
            ).read_text(encoding="utf-8")
        )
        original["assumption_state"] = "unknown"
        original["assumptions"] = []
        with tempfile.TemporaryDirectory() as directory:
            request = Path(directory) / "request.json"
            request.write_text(json.dumps(original), encoding="utf-8")
            code, body = self.invoke(
                "request",
                "--request",
                str(request),
            )
        self.assertEqual(code, 4)
        self.assertEqual(body["decision"]["disposition"], "PARKED")
        self.assertEqual(body["next_step"], "user_resubmission")
        self.assertTrue(body["decision"]["questions"])

    def test_box_command_reaches_composed_front_door(self):
        box_root = Path(__file__).resolve().parents[1]
        request = (
            box_root
            / "fixtures"
            / "requests"
            / "assemble_constraintbox_v1.json"
        )
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory) / "run"
            returned = {
                "schema": "constraintbox.first-box-run.v1",
                "disposition": "READY_FOR_UNTRUSTED_PROPOSAL",
                "release_allowed": False,
                "promotion_allowed": False,
            }
            with patch.object(
                cli,
                "run_first_box",
                return_value=(returned, 0),
            ) as composed:
                code, body = self.invoke(
                    "box",
                    "--request",
                    str(request),
                    "--run-dir",
                    str(run_dir),
                )
        self.assertEqual(code, 0)
        self.assertEqual(
            body["disposition"],
            "READY_FOR_UNTRUSTED_PROPOSAL",
        )
        self.assertFalse(body["release_allowed"])
        composed.assert_called_once()

    def test_box_surface_exposes_no_profile_runtime_or_budget_authority(self):
        parser = cli.build_parser()
        subparsers = next(
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        option_strings = {
            option
            for action in subparsers.choices["box"]._actions
            for option in action.option_strings
        }
        self.assertEqual(
            option_strings,
            {"-h", "--help", "--request", "--run-dir", "--output"},
        )

    def test_box_output_cannot_overwrite_a_run_artifact(self):
        box_root = Path(__file__).resolve().parents[1]
        request = (
            box_root
            / "fixtures"
            / "requests"
            / "assemble_constraintbox_v1.json"
        )
        with tempfile.TemporaryDirectory() as directory:
            run_dir = Path(directory) / "run"
            output = run_dir / "request_assessment.json"
            with patch.object(cli, "run_first_box") as composed:
                code, body = self.invoke(
                    "box",
                    "--request",
                    str(request),
                    "--run-dir",
                    str(run_dir),
                    "--output",
                    str(output),
                )
        self.assertEqual(code, 5)
        self.assertEqual(body["reason"], "first_box_configuration_error")
        self.assertIn("outside the box receipt directory", body["error"])
        composed.assert_not_called()

    def test_lease_issue_verify_and_denial_dispatch(self):
        repo = Path(__file__).resolve().parents[2]
        interpreter = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
        with tempfile.TemporaryDirectory() as directory:
            index = Path(directory) / "index"
            shutil.copyfile(repo / ".git" / "index", index)
            objects = Path(directory) / "objects"
            objects.mkdir()
            environment = {
                "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(repo / ".git" / "objects"),
                "GIT_INDEX_FILE": str(index),
                "GIT_OBJECT_DIRECTORY": str(objects),
            }
            with patch.dict(os.environ, environment):
                code, body = self.invoke(
                    "lease",
                    "issue",
                    "--repo",
                    str(repo),
                    "--runner",
                    f"{interpreter} -c 'raise SystemExit(0)'",
                    "--ttl-seconds",
                    "60",
                )
                self.assertEqual(code, 0)
                self.assertEqual(body["schema"], "constraintbox.tree-lease.v1")

            lease = Path(directory) / "lease.json"
            lease.write_text(json.dumps(body), encoding="utf-8")
            with patch.dict(os.environ, environment):
                code, verified = self.invoke(
                    "lease",
                    "verify",
                    "--lease",
                    str(lease),
                    "--repo",
                    str(repo),
                )
                self.assertEqual(code, 0)
                self.assertEqual(verified["status"], "VALID")

                code, verified = self.invoke(
                    "lease",
                    "verify",
                    "--lease",
                    str(Path(directory) / "absent.json"),
                    "--repo",
                    str(repo),
                )
                self.assertEqual(code, 1)
                self.assertEqual(verified["status"], "ABSENT")

                code, body = self.invoke(
                    "lease",
                    "issue",
                    "--repo",
                    str(repo),
                    "--runner",
                    f"{interpreter} -c 'raise SystemExit(7)'",
                    "--ttl-seconds",
                    "60",
                )
                self.assertEqual(code, 1)
                self.assertEqual(body["runs"][0]["exit_code"], 7)

    def test_discharge_pass_and_failure_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = root / "policy.json"
            observations = root / "observations.json"
            policy.write_text(
                json.dumps(
                    {
                        "policy_id": "p1",
                        "max_age_seconds": 60,
                        "requirements": [
                            {
                                "variable": "score",
                                "comparator": "gte",
                                "threshold": 0.5,
                                "optional": False,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            observations.write_text(
                json.dumps(
                    {
                        "score": {
                            "value": 0.75,
                            "observed_at": 100.0,
                            "source": "fixture",
                        }
                    }
                ),
                encoding="utf-8",
            )
            code, body = self.invoke(
                "discharge",
                "--policy",
                str(policy),
                "--observations",
                str(observations),
                "--now",
                "120",
            )
            self.assertEqual(code, 0)
            self.assertEqual(body["status"], "PASS")

            observations.write_text("{}", encoding="utf-8")
            code, body = self.invoke(
                "discharge",
                "--policy",
                str(policy),
                "--observations",
                str(observations),
                "--now",
                "120",
            )
            self.assertEqual(code, 1)
            self.assertEqual(body["status"], "EVALUATION_ERROR")

    def test_evidence_seal_verify_and_failure_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence_root = root / "evidence"
            evidence_root.mkdir()
            target = evidence_root / "receipt.json"
            target.write_text('{"ok": true}', encoding="utf-8")
            refs = root / "refs.json"
            seal = root / "seal.json"
            required_manifest = root / "required-manifest.json"
            refs.write_text(
                json.dumps(
                    [{"kind": "receipt", "ref": "receipt.json", "route": "file"}]
                ),
                encoding="utf-8",
            )
            code, body = self.invoke(
                "evidence",
                "seal",
                "--run-id",
                "run-1",
                "--manifest-id",
                "required-run-1",
                "--refs",
                str(refs),
                "--manifest-output",
                str(required_manifest),
                "--file-root",
                str(evidence_root),
                "--output",
                str(seal),
            )
            self.assertEqual(code, 0)
            self.assertEqual(body["run_id"], "run-1")

            missing_refs = root / "missing-refs.json"
            missing_refs.write_text(
                json.dumps(
                    [{"kind": "receipt", "ref": "missing.json", "route": "file"}]
                ),
                encoding="utf-8",
            )
            code, body = self.invoke(
                "evidence",
                "seal",
                "--run-id",
                "run-missing",
                "--manifest-id",
                "required-run-missing",
                "--refs",
                str(missing_refs),
                "--manifest-output",
                str(root / "missing-required-manifest.json"),
                "--file-root",
                str(evidence_root),
            )
            self.assertEqual(code, 1)
            self.assertIn("not observed", body["error"])

            code, body = self.invoke(
                "evidence",
                "verify",
                "--seal",
                str(seal),
                "--required-manifest",
                str(required_manifest),
                "--file-root",
                str(evidence_root),
            )
            self.assertEqual(code, 0)
            self.assertEqual(body["verdict"], "SEALED")

            target.unlink()
            code, body = self.invoke(
                "evidence",
                "verify",
                "--seal",
                str(seal),
                "--required-manifest",
                str(required_manifest),
                "--file-root",
                str(evidence_root),
            )
            self.assertEqual(code, 1)
            self.assertEqual(body["verdict"], "REF_MISSING")

    def test_applicability_eligible_and_parked_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = Path(directory) / "registry.json"
            registry.write_text(
                json.dumps(
                    {
                        "schema": "constraintbox.applicability-registry.v1",
                        "registry_id": "r1",
                        "claim_types": {
                            "bounded": {
                                "required_capabilities": ["z3"],
                                "optional_capabilities": [],
                                "claim_ceiling": "bounded only",
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            code, body = self.invoke(
                "applicability",
                "--registry",
                str(registry),
                "--claim-type",
                "bounded",
                "--capability",
                "z3=READY",
            )
            self.assertEqual(code, 0)
            self.assertEqual(body["disposition"], "ELIGIBLE_FOR_CHECKS")

            code, body = self.invoke(
                "applicability",
                "--registry",
                str(registry),
                "--claim-type",
                "bounded",
            )
            self.assertEqual(code, 1)
            self.assertEqual(body["disposition"], "PARKED")


if __name__ == "__main__":
    unittest.main()
