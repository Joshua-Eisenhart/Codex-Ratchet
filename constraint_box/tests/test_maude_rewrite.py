from __future__ import annotations

import ast
import builtins
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from constraintbox import _maude_worker
from constraintbox import maude_rewrite
from constraintbox.contracts import Disposition, TaskRequest
from constraintbox.controller import ConstraintBoxController
from constraintbox.intake import canonical_json
from constraintbox.maude_rewrite import MaudeTransitionProfile


def request(
    from_state: object,
    action: object,
    to_state: object,
    **extra: object,
) -> bytes:
    body: dict[str, object] = {
        "from_state": from_state,
        "action": action,
        "to_state": to_state,
    }
    body.update(extra)
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode()


def worker_job(
    profile: MaudeTransitionProfile,
    *,
    source_term: str | None = None,
    rule_label: str | None = None,
) -> bytes:
    rendered = profile._render()
    row = rendered["semantic_table"][0]
    runtime_identity = maude_rewrite._controller_runtime_identity()
    resource_limits = maude_rewrite._worker_resource_limits(
        float(profile.timeout_seconds)
    )
    return canonical_json(
        {
            "schema": "constraintbox.maude-worker.request.v1",
            "module_name": rendered["module_name"],
            "module_source": rendered["module_source"],
            "module_source_sha256": rendered["module_source_sha256"],
            "source_term": source_term or row["encoded_from"],
            "rule_label": rule_label or row["rule_label"],
            "max_applications": profile.max_applications,
            "max_rules": len(rendered["expected_rule_inventory"]),
            "max_equations": 0,
            "cpu_limit_seconds": resource_limits.cpu_seconds,
            "memory_limit_bytes": resource_limits.memory_limit_bytes,
            "memory_limit_mebibytes": (
                resource_limits.memory_limit_mebibytes
            ),
            "memory_limit_mechanism": (
                resource_limits.memory_limit_mechanism
            ),
            "required_maude_version": profile.required_maude_version,
            "required_maude_core_version": (
                profile.required_maude_core_version
            ),
            "expected_maude_wrapper_path": (
                runtime_identity["wrapper"]["path"]
            ),
            "expected_maude_wrapper_sha256": (
                runtime_identity["wrapper"]["sha256"]
            ),
            "expected_maude_native_extension_path": (
                runtime_identity["native_extension"]["path"]
            ),
            "expected_maude_native_extension_sha256": (
                runtime_identity["native_extension"]["sha256"]
            ),
            "expected_maude_core_library_path": (
                runtime_identity["core_library"]["path"]
            ),
            "expected_maude_core_library_sha256": (
                runtime_identity["core_library"]["sha256"]
            ),
        }
    )


def resource_limits_for_job(
    job: bytes,
) -> maude_rewrite._WorkerResourceLimits:
    decoded = json.loads(job)
    return maude_rewrite._WorkerResourceLimits(
        cpu_seconds=decoded["cpu_limit_seconds"],
        memory_limit_bytes=decoded["memory_limit_bytes"],
        memory_limit_mebibytes=decoded["memory_limit_mebibytes"],
        memory_limit_mechanism=decoded["memory_limit_mechanism"],
    )


def completed(
    observation: dict[str, object],
    *,
    returncode: int = 0,
    stderr: bytes = b"",
) -> maude_rewrite._WorkerProcessResult:
    return maude_rewrite._WorkerProcessResult(
        returncode=returncode,
        stdout=canonical_json(observation) + b"\n",
        stderr=stderr,
        stdout_overflow=False,
        stderr_overflow=False,
    )


def run_bootstrapped_worker_source(
    source: bytes,
    limits: maude_rewrite._WorkerResourceLimits,
    *,
    input_bytes: bytes,
    environment: dict[str, str],
    arguments: tuple[str, ...] = (),
    isolated: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    status_read, status_write = os.pipe()
    try:
        os.set_inheritable(status_write, True)
        command = [sys.executable]
        if isolated:
            command.append("-I")
        command.extend(
            (
                "-c",
                maude_rewrite._worker_bootstrap_source(
                    source,
                    limits,
                    status_fd=status_write,
                ),
                *arguments,
            )
        )
        if limits.memory_limit_mechanism == "darwin_taskpolicy":
            command = [
                str(maude_rewrite._DARWIN_TASKPOLICY_PATH),
                "-m",
                str(limits.memory_limit_mebibytes),
                *command,
            ]
        process = subprocess.run(
            command,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=5.0,
            env=environment,
            pass_fds=(status_write,),
        )
        os.set_blocking(status_read, False)
        try:
            bootstrap_status = os.read(status_read, 1)
        except BlockingIOError:
            bootstrap_status = b""
    finally:
        for descriptor in (status_read, status_write):
            try:
                os.close(descriptor)
            except OSError:
                pass
    if bootstrap_status:
        raise RuntimeError("worker resource-limit bootstrap failed")
    return process


def actual_worker_observation(job: bytes) -> dict[str, object]:
    resource_limits = resource_limits_for_job(job)
    environment = os.environ.copy()
    environment["CONSTRAINTBOX_MAUDE_MEMORY_LIMIT_MEBIBYTES"] = str(
        resource_limits.memory_limit_mebibytes
    )
    environment["CONSTRAINTBOX_MAUDE_MEMORY_LIMIT_MECHANISM"] = (
        resource_limits.memory_limit_mechanism
    )
    process = run_bootstrapped_worker_source(
        Path(_maude_worker.__file__).read_bytes(),
        resource_limits,
        input_bytes=job,
        environment=environment,
    )
    if process.returncode != 0 or process.stderr:
        raise RuntimeError(
            f"worker failed: returncode={process.returncode}, "
            f"stderr={process.stderr!r}"
        )
    return json.loads(process.stdout)


def severed_worker_observation(
    job: bytes,
    owner_name: str,
    attribute: str,
    *,
    noncallable: bool = False,
) -> dict[str, object]:
    script = """
import json
import sys
from unittest import mock
import maude
from constraintbox import _maude_worker

owners = {
    "maude": maude,
    "Module": maude.Module,
    "Rule": maude.Rule,
    "Term": maude.Term,
    "Substitution": maude.Substitution,
}
owner = owners[sys.argv[1]]
replacement = None if sys.argv[3] == "none" else mock.DEFAULT
patcher = (
    mock.patch.object(owner, sys.argv[2], None)
    if replacement is None
    else mock.patch.object(
        owner,
        sys.argv[2],
        side_effect=RuntimeError("severed"),
    )
)
with patcher:
    observation = _maude_worker.observe(sys.stdin.buffer.read())
sys.stdout.write(json.dumps(
    observation,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
))
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(
        Path(maude_rewrite.__file__).resolve().parents[1]
    )
    limits = resource_limits_for_job(job)
    environment["CONSTRAINTBOX_MAUDE_MEMORY_LIMIT_MEBIBYTES"] = str(
        limits.memory_limit_mebibytes
    )
    environment["CONSTRAINTBOX_MAUDE_MEMORY_LIMIT_MECHANISM"] = (
        limits.memory_limit_mechanism
    )
    process = run_bootstrapped_worker_source(
        script.encode("utf-8"),
        limits,
        input_bytes=job,
        environment=environment,
        arguments=(
            owner_name,
            attribute,
            "none" if noncallable else "raise",
        ),
        isolated=False,
    )
    if process.returncode != 0 or process.stderr:
        raise RuntimeError(
            f"severance worker failed: returncode={process.returncode}, "
            f"stderr={process.stderr!r}"
        )
    return json.loads(process.stdout)


class MaudeTransitionProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = MaudeTransitionProfile(
            states=("received", "released", "validated"),
            transitions=(
                ("received", "validate", "validated"),
                ("validated", "release", "released"),
            ),
        )

    def evaluate(self, raw: bytes, profile: MaudeTransitionProfile | None = None):
        return (profile or self.profile).evaluate(raw, Path("/unused"))

    def test_positive_exact_transition_uses_real_isolated_worker(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            controller = ConstraintBoxController(
                {"maude-transition": self.profile},
                Path(directory),
            )
            decision = controller.run(
                TaskRequest(
                    task_kind="maude-transition",
                    payload=request("received", "validate", "validated"),
                    request_id="maude-positive",
                )
            )

        self.assertEqual(decision.disposition, Disposition.ELIGIBLE)
        self.assertEqual(decision.reason, "maude_transition_observed")
        self.assertEqual(
            decision.profile_id,
            "constraintbox.formal.maude-transition.v1",
        )
        self.assertFalse(decision.promotion_allowed)
        self.assertTrue(decision.evidence["controller_table_agrees"])
        observation = decision.evidence["worker_observation"]
        self.assertEqual(observation["maude_version"], "1.6.0")
        self.assertEqual(observation["maude_core_version"], "3.5.1+smc")
        self.assertEqual(
            observation["runtime_identity"],
            decision.evidence["tool"]["controller_runtime_identity"],
        )
        self.assertFalse(
            decision.evidence["tool"]["artifact_sha256_is_policy_input"]
        )
        self.assertEqual(observation["application_count"], 1)
        self.assertFalse(observation["rule_inventory_overflow"])
        self.assertFalse(observation["equation_inventory_overflow"])
        self.assertEqual(
            observation["applications"],
            [
                {
                    "term": "s2",
                    "rule_label": "r0",
                    "rule_metadata": "constraintbox-transition-v1:r0",
                    "substitution_size": 0,
                    "matched_portion": None,
                    "context_callable": True,
                }
            ],
        )
        self.assertEqual(
            observation["rule_inventory"],
            self.profile._render()["expected_rule_inventory"],
        )
        self.assertEqual(observation["equation_count"], 0)
        self.assertTrue(
            decision.evidence["tool"]["worker_process_boundary"].endswith(
                "subprocess"
            )
        )
        self.assertFalse(decision.evidence["tool"]["worker_os_sandboxed"])
        self.assertFalse(
            decision.evidence["tool"]["worker_has_disposition_authority"]
        )
        self.assertIn("no truth", decision.claim_ceiling)

    def test_wrong_target_and_unavailable_action_block_before_worker(self) -> None:
        with mock.patch.object(maude_rewrite, "_run_worker") as run_worker:
            wrong_target = self.evaluate(
                request("received", "validate", "released")
            )
            unavailable_action = self.evaluate(
                request("received", "approve", "validated")
            )
            unavailable_transition = self.evaluate(
                request("released", "release", "released")
            )

        self.assertEqual(wrong_target.disposition, Disposition.BLOCKED)
        self.assertEqual(
            wrong_target.reason, "maude_transition_target_mismatch"
        )
        self.assertEqual(
            unavailable_action.reason,
            "maude_transition_action_unavailable",
        )
        self.assertEqual(
            unavailable_transition.reason, "maude_transition_unavailable"
        )
        run_worker.assert_not_called()

    def test_malformed_json_and_wrong_field_types_block_before_worker(
        self,
    ) -> None:
        with mock.patch.object(maude_rewrite, "_run_worker") as run_worker:
            malformed = self.evaluate(b'{"from_state":')
            wrong_type = self.evaluate(
                request("received", ["validate"], "validated")
            )
        self.assertEqual(malformed.disposition, Disposition.BLOCKED)
        self.assertEqual(malformed.reason, "strict_intake_failed")
        self.assertEqual(wrong_type.disposition, Disposition.BLOCKED)
        self.assertEqual(
            wrong_type.reason, "maude_transition_contract_type_mismatch"
        )
        run_worker.assert_not_called()

    def test_authority_fields_and_injection_are_rejected_before_worker(
        self,
    ) -> None:
        authority_fields = (
            "module",
            "rule",
            "strategy",
            "bounds",
            "profile",
            "verdict",
            "command",
            "promotion",
        )
        with mock.patch.object(maude_rewrite, "_run_worker") as run_worker:
            for field in authority_fields:
                with self.subTest(field=field):
                    outcome = self.evaluate(
                        request(
                            "received",
                            "validate",
                            "validated",
                            **{field: "attacker-controlled"},
                        )
                    )
                    self.assertEqual(
                        outcome.reason,
                        "maude_transition_contract_keys_mismatch",
                    )
            injection = self.evaluate(
                request(
                    'received") . rl [owned] : s0 => s0 .',
                    "validate",
                    "validated",
                )
            )

        self.assertEqual(injection.disposition, Disposition.BLOCKED)
        self.assertEqual(injection.reason, "maude_transition_state_unknown")
        run_worker.assert_not_called()

        rendered = self.profile._render()
        for raw_name in (
            *self.profile.states,
            *(action for _source, action, _target in self.profile.transitions),
        ):
            self.assertNotIn(raw_name, rendered["module_source"])

    def test_oversized_request_is_rejected_before_json_parsing_or_worker(
        self,
    ) -> None:
        oversized = request(
            "received",
            "validate",
            "x" * 5_000,
        )
        with mock.patch.object(
            maude_rewrite, "parse_json_object"
        ) as parse_json, mock.patch.object(
            maude_rewrite, "_run_worker"
        ) as run_worker:
            outcome = self.evaluate(oversized)
        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(
            outcome.reason, "maude_transition_request_too_large"
        )
        parse_json.assert_not_called()
        run_worker.assert_not_called()

    def test_exact_configuration_caps_and_plus_one_rejections(self) -> None:
        states = tuple(f"n{index:03d}" for index in range(256))
        transitions = tuple(
            ("n000", f"a{index:04d}", "n001")
            for index in range(4_096)
        )
        boundary = MaudeTransitionProfile(
            states=states,
            transitions=transitions,
            max_states=256,
            max_rules=4_096,
            max_applications=16,
            timeout_seconds=30.0,
        )
        self.assertEqual(len(boundary.states), 256)
        self.assertEqual(len(boundary.transitions), 4_096)

        with self.assertRaisesRegex(ValueError, "max_states"):
            MaudeTransitionProfile(max_states=257)
        with self.assertRaisesRegex(ValueError, "max_rules"):
            MaudeTransitionProfile(max_rules=4_097)
        with self.assertRaisesRegex(ValueError, "max_applications"):
            MaudeTransitionProfile(max_applications=17)
        with self.assertRaisesRegex(ValueError, "timeout_seconds"):
            MaudeTransitionProfile(timeout_seconds=30.01)

    def test_worker_inventory_bounds_are_exact_controller_rendered_bounds(
        self,
    ) -> None:
        limits = maude_rewrite._WorkerResourceLimits(
            cpu_seconds=2,
            memory_limit_bytes=maude_rewrite._WORKER_MEMORY_LIMIT_BYTES,
            memory_limit_mebibytes=(
                maude_rewrite._WORKER_MEMORY_LIMIT_BYTES // (1024 * 1024)
            ),
            memory_limit_mechanism="rlimit_as",
        )
        with mock.patch.object(
            maude_rewrite,
            "_controller_runtime_identity",
            return_value=maude_rewrite._controller_runtime_identity(),
        ), mock.patch.object(
            maude_rewrite,
            "_worker_resource_limits",
            return_value=limits,
        ), mock.patch.object(
            maude_rewrite,
            "_run_worker",
            side_effect=RuntimeError("inspect controller job only"),
        ) as run_worker:
            outcome = self.evaluate(
                request("received", "validate", "validated")
            )

        self.assertEqual(
            outcome.reason,
            "maude_worker_execution_error",
        )
        worker_job_payload = json.loads(run_worker.call_args.args[1])
        self.assertEqual(
            worker_job_payload["max_rules"],
            len(self.profile._render()["expected_rule_inventory"]),
        )
        self.assertLess(
            worker_job_payload["max_rules"],
            self.profile.max_rules,
        )
        self.assertEqual(worker_job_payload["max_equations"], 0)

    def test_two_step_path_cannot_pass_as_one_step(self) -> None:
        profile = MaudeTransitionProfile(
            states=("a", "b", "c"),
            transitions=(
                ("a", "advance", "b"),
                ("b", "advance", "c"),
            ),
        )
        with mock.patch.object(maude_rewrite, "_run_worker") as run_worker:
            outcome = self.evaluate(
                request("a", "advance", "c"),
                profile,
            )

        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(
            outcome.reason, "maude_transition_target_mismatch"
        )
        run_worker.assert_not_called()

    def test_terminal_state_has_zero_direct_rule_applications(self) -> None:
        profile = MaudeTransitionProfile(
            states=("active", "terminal"),
            transitions=(("active", "finish", "terminal"),),
        )
        rendered = profile._render()
        observation = actual_worker_observation(
            worker_job(
                profile,
                source_term=rendered["state_tokens"]["terminal"],
            )
        )
        self.assertEqual(observation["status"], "ok")
        self.assertEqual(observation["parsed_term"], "s1")
        self.assertEqual(observation["application_count"], 0)
        self.assertEqual(observation["applications"], [])

        with mock.patch.object(maude_rewrite, "_run_worker") as run_worker:
            outcome = self.evaluate(
                request("terminal", "finish", "terminal"),
                profile,
            )
        self.assertEqual(outcome.reason, "maude_transition_unavailable")
        run_worker.assert_not_called()

    def test_nondeterministic_or_noncanonical_controller_config_is_rejected(
        self,
    ) -> None:
        with self.assertRaisesRegex(ValueError, "deterministic"):
            MaudeTransitionProfile(
                states=("a", "b", "c"),
                transitions=(
                    ("a", "advance", "b"),
                    ("a", "advance", "c"),
                ),
            )
        with self.assertRaisesRegex(ValueError, "canonically sorted"):
            MaudeTransitionProfile(
                states=("b", "a"),
                transitions=(("a", "advance", "b"),),
            )
        with self.assertRaisesRegex(ValueError, "canonically sorted"):
            MaudeTransitionProfile(
                states=("a", "b", "c"),
                transitions=(
                    ("b", "advance", "c"),
                    ("a", "advance", "b"),
                ),
            )

    def test_missing_dependency_observation_is_typed_parked(self) -> None:
        real_import = builtins.__import__
        job = worker_job(self.profile)

        def no_maude(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "maude" or name.startswith("maude."):
                raise ModuleNotFoundError("maude unavailable")
            return real_import(name, globals, locals, fromlist, level)

        with mock.patch(
            "builtins.__import__", side_effect=no_maude
        ), mock.patch.object(
            _maude_worker,
            "_verify_worker_resource_limits",
            return_value=maude_rewrite._worker_resource_limits(
                float(self.profile.timeout_seconds)
            ).as_dict(),
        ):
            observation = _maude_worker.observe(job)
        self.assertEqual(observation["status"], "dependency_unavailable")
        self.assertNotIn("disposition", observation)
        self.assertNotIn("verdict", observation)

        with mock.patch.object(
            maude_rewrite,
            "_run_worker",
            return_value=completed(observation),
        ):
            outcome = self.evaluate(
                request("received", "validate", "validated")
            )
        self.assertEqual(outcome.disposition, Disposition.PARKED)
        self.assertEqual(outcome.reason, "maude_runtime_unavailable")

    def test_timeout_is_typed_parked(self) -> None:
        with mock.patch.object(
            maude_rewrite,
            "_run_worker",
            side_effect=subprocess.TimeoutExpired(
                cmd=["maude-worker"],
                timeout=self.profile.timeout_seconds,
            ),
        ):
            outcome = self.evaluate(
                request("received", "validate", "validated")
            )
        self.assertEqual(outcome.disposition, Disposition.PARKED)
        self.assertEqual(outcome.reason, "maude_worker_timeout")

    def test_each_named_api_severance_is_an_executed_block(self) -> None:
        severances = (
            ("maude", "init", "maude.init"),
            ("maude", "input", "maude.input"),
            ("maude", "getModule", "maude.getModule"),
            ("Module", "getRules", "Module.getRules"),
            ("Module", "getEquations", "Module.getEquations"),
            ("Rule", "getLabel", "Rule.getLabel"),
            ("Rule", "getMetadata", "Rule.getMetadata"),
            ("Rule", "getLhs", "Rule.getLhs"),
            ("Rule", "getRhs", "Rule.getRhs"),
            ("Rule", "hasCondition", "Rule.hasCondition"),
            ("Module", "parseTerm", "Module.parseTerm"),
            ("Term", "apply", "Term.apply"),
            ("Substitution", "size", "Substitution.size"),
            (
                "Substitution",
                "matchedPortion",
                "Substitution.matchedPortion",
            ),
        )
        for owner_name, attribute, expected_operation in severances:
            with self.subTest(api=expected_operation):
                observation = severed_worker_observation(
                    worker_job(self.profile),
                    owner_name,
                    attribute,
                )
            self.assertEqual(observation["status"], "operation_error")
            self.assertEqual(
                observation["operation"], expected_operation
            )
            with mock.patch.object(
                maude_rewrite,
                "_run_worker",
                return_value=completed(observation),
            ):
                outcome = self.evaluate(
                    request("received", "validate", "validated")
                )
            self.assertEqual(outcome.disposition, Disposition.BLOCKED)
            self.assertEqual(outcome.reason, "maude_operation_error")

    def test_noncallable_init_after_import_is_blocked_not_parked(self) -> None:
        observation = severed_worker_observation(
            worker_job(self.profile),
            "maude",
            "init",
            noncallable=True,
        )
        self.assertEqual(observation["status"], "operation_error")
        self.assertEqual(observation["operation"], "maude.init")
        with mock.patch.object(
            maude_rewrite,
            "_run_worker",
            return_value=completed(observation),
        ):
            outcome = self.evaluate(
                request("received", "validate", "validated")
            )
        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "maude_operation_error")

    def test_runtime_artifact_binding_and_worker_report_are_load_bearing(
        self,
    ) -> None:
        expected_identity = maude_rewrite._controller_runtime_identity()
        self.assertEqual(set(expected_identity), {
            "wrapper",
            "native_extension",
            "core_library",
        })
        for artifact in expected_identity.values():
            self.assertTrue(Path(artifact["path"]).is_file())
            self.assertRegex(artifact["sha256"], r"^[0-9a-f]{64}$")

        observation = actual_worker_observation(worker_job(self.profile))
        forged = json.loads(json.dumps(observation))
        forged["runtime_identity"]["core_library"]["sha256"] = "0" * 64
        with mock.patch.object(
            maude_rewrite,
            "_run_worker",
            return_value=completed(forged),
        ):
            outcome = self.evaluate(
                request("received", "validate", "validated")
            )
        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "maude_runtime_identity_mismatch")

        with mock.patch.object(
            maude_rewrite,
            "_controller_runtime_identity",
            side_effect=maude_rewrite._RuntimePinDrift("drift"),
        ), mock.patch.object(maude_rewrite, "_run_worker") as run_worker:
            drifted = self.evaluate(
                request("received", "validate", "validated")
            )
        self.assertEqual(drifted.disposition, Disposition.BLOCKED)
        self.assertEqual(drifted.reason, "maude_runtime_identity_drift")
        run_worker.assert_not_called()

        with mock.patch.object(
            maude_rewrite,
            "_controller_runtime_identity",
            side_effect=maude_rewrite._RuntimePinMissing("missing"),
        ), mock.patch.object(maude_rewrite, "_run_worker") as run_worker:
            missing = self.evaluate(
                request("received", "validate", "validated")
            )
        self.assertEqual(missing.disposition, Disposition.PARKED)
        self.assertEqual(missing.reason, "maude_runtime_unavailable")
        run_worker.assert_not_called()

    def test_worker_stdout_and_stderr_are_hard_bounded(self) -> None:
        stdout_result = maude_rewrite._run_worker(
            (
                b"import sys\n"
                b"sys.stdout.buffer.write(b'x' * 1100000)\n"
                b"sys.stdout.buffer.flush()\n"
            ),
            b"",
            5.0,
        )
        stderr_result = maude_rewrite._run_worker(
            (
                b"import sys\n"
                b"sys.stderr.buffer.write(b'x' * 70000)\n"
                b"sys.stderr.buffer.flush()\n"
            ),
            b"",
            5.0,
        )
        self.assertTrue(stdout_result.stdout_overflow)
        self.assertLessEqual(
            len(stdout_result.stdout),
            maude_rewrite._MAX_WORKER_STDOUT_BYTES,
        )
        self.assertTrue(stderr_result.stderr_overflow)
        self.assertLessEqual(
            len(stderr_result.stderr),
            maude_rewrite._MAX_WORKER_STDERR_BYTES,
        )

        overflow = maude_rewrite._WorkerProcessResult(
            returncode=-9,
            stdout=b"x" * (maude_rewrite._MAX_WORKER_STDOUT_BYTES + 1),
            stderr=b"",
            stdout_overflow=True,
            stderr_overflow=False,
        )
        with mock.patch.object(
            maude_rewrite,
            "_run_worker",
            return_value=overflow,
        ):
            outcome = self.evaluate(
                request("received", "validate", "validated")
            )
        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "maude_worker_output_overflow")

    def test_worker_applies_cpu_limit_and_receives_memory_policy(self) -> None:
        limits = maude_rewrite._worker_resource_limits(5.0)
        real_popen = maude_rewrite.subprocess.Popen
        with mock.patch.object(
            maude_rewrite.subprocess,
            "Popen",
            wraps=real_popen,
        ) as popen:
            result = maude_rewrite._run_worker(
                (
                    b"import json\n"
                    b"import os\n"
                    b"import resource\n"
                    b"print(json.dumps({\n"
                    b"  'cpu': resource.getrlimit(resource.RLIMIT_CPU),\n"
                    b"  'memory_mebibytes': os.environ[\n"
                    b"      'CONSTRAINTBOX_MAUDE_MEMORY_LIMIT_MEBIBYTES'\n"
                    b"  ],\n"
                    b"  'memory_mechanism': os.environ[\n"
                    b"      'CONSTRAINTBOX_MAUDE_MEMORY_LIMIT_MECHANISM'\n"
                    b"  ],\n"
                    b"}))\n"
                ),
                b"",
                5.0,
                resource_limits=limits,
            )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, b"")
        self.assertNotIn("preexec_fn", popen.call_args.kwargs)
        report = json.loads(result.stdout)
        self.assertEqual(
            report["cpu"],
            [limits.cpu_seconds, limits.cpu_seconds],
        )
        self.assertEqual(
            report["memory_mebibytes"],
            str(limits.memory_limit_mebibytes),
        )
        self.assertEqual(
            report["memory_mechanism"],
            limits.memory_limit_mechanism,
        )

    def test_bootstrap_limit_failure_remains_typed_and_fail_closed(
        self,
    ) -> None:
        def failing_bootstrap(
            _worker_source: bytes,
            _limits: maude_rewrite._WorkerResourceLimits,
            *,
            status_fd: int,
        ) -> str:
            return (
                "import os\n"
                f"os.write({status_fd}, b'\\x01')\n"
                f"os.close({status_fd})\n"
                f"raise SystemExit("
                f"{maude_rewrite._WORKER_BOOTSTRAP_FAILURE_EXIT_CODE})\n"
            )

        with mock.patch.object(
            maude_rewrite,
            "_worker_bootstrap_source",
            side_effect=failing_bootstrap,
        ):
            with self.assertRaises(
                maude_rewrite._WorkerResourceLimitUnavailable
            ):
                maude_rewrite._run_worker(
                    b"raise RuntimeError('worker source must not run')\n",
                    b"",
                    5.0,
                )

    def test_missing_resource_limit_capability_parks_before_worker(self) -> None:
        with mock.patch.object(
            maude_rewrite,
            "_worker_resource_limits",
            side_effect=maude_rewrite._WorkerResourceLimitUnavailable(
                "unavailable"
            ),
        ), mock.patch.object(maude_rewrite, "_run_worker") as run_worker:
            outcome = self.evaluate(
                request("received", "validate", "validated")
            )
        self.assertEqual(outcome.disposition, Disposition.PARKED)
        self.assertEqual(
            outcome.reason,
            "maude_worker_resource_limits_unavailable",
        )
        run_worker.assert_not_called()

    def test_bounded_enumeration_rejects_before_overlimit_serialization(self) -> None:
        enumeration = _maude_worker._bounded_enumeration(
            iter(("first", "second", "third")),
            maximum=2,
            operation="adversarial-enumeration",
        )
        self.assertEqual(next(enumeration), "first")
        self.assertEqual(next(enumeration), "second")
        with self.assertRaisesRegex(
            _maude_worker._BoundExceeded,
            "exceeds controller maximum of 2",
        ):
            next(enumeration)

    def test_worker_timeout_uses_an_isolated_process_group(self) -> None:
        started = time.monotonic()
        with mock.patch.object(
            maude_rewrite.os,
            "killpg",
            wraps=maude_rewrite.os.killpg,
        ) as killpg:
            with self.assertRaises(subprocess.TimeoutExpired):
                maude_rewrite._run_worker(
                    b"import time\ntime.sleep(5)\n",
                    b"",
                    0.1,
                )
        self.assertLess(time.monotonic() - started, 2.0)
        self.assertTrue(killpg.called)
        for call in killpg.call_args_list:
            self.assertEqual(call.args[1], maude_rewrite.signal.SIGKILL)

    def test_wall_timeout_includes_nonreading_worker_stdin(self) -> None:
        started = time.monotonic()
        with self.assertRaises(subprocess.TimeoutExpired):
            maude_rewrite._run_worker(
                b"import time\ntime.sleep(0.8)\n",
                b"x" * 524_288,
                0.05,
            )
        self.assertLess(time.monotonic() - started, 1.0)

    def test_timeout_kills_descendant_in_the_worker_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "escaped-descendant"
            child_source = (
                "import pathlib\n"
                "import time\n"
                "time.sleep(0.5)\n"
                f"pathlib.Path({str(marker)!r}).write_text('escaped')\n"
            )
            worker_source = (
                "import subprocess\n"
                "import sys\n"
                "import time\n"
                f"subprocess.Popen([sys.executable, '-c', {child_source!r}])\n"
                "time.sleep(5)\n"
            ).encode("utf-8")
            with self.assertRaises(subprocess.TimeoutExpired):
                maude_rewrite._run_worker(worker_source, b"", 0.1)
            time.sleep(0.8)
            self.assertFalse(marker.exists())

    def test_type_correct_wrong_result_and_multiple_results_cannot_green(
        self,
    ) -> None:
        observation = actual_worker_observation(worker_job(self.profile))
        self.assertEqual(observation["status"], "ok")

        wrong_result = dict(observation)
        wrong_result["applications"] = [
            {
                **observation["applications"][0],
                "term": "s1",
            }
        ]
        with mock.patch.object(
            maude_rewrite,
            "_run_worker",
            return_value=completed(wrong_result),
        ):
            wrong = self.evaluate(
                request("received", "validate", "validated")
            )
        self.assertEqual(wrong.disposition, Disposition.BLOCKED)
        self.assertEqual(wrong.reason, "maude_worker_table_disagreement")

        multiple = dict(observation)
        multiple["applications"] = [
            observation["applications"][0],
            observation["applications"][0],
        ]
        multiple["application_count"] = 2
        with mock.patch.object(
            maude_rewrite,
            "_run_worker",
            return_value=completed(multiple),
        ):
            many = self.evaluate(
                request("received", "validate", "validated")
            )
        self.assertEqual(many.disposition, Disposition.BLOCKED)
        self.assertEqual(
            many.reason, "maude_application_cardinality_mismatch"
        )

    def test_worker_source_hash_drift_blocks_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            drifted_worker = Path(directory) / "_maude_worker.py"
            drifted_worker.write_bytes(
                Path(_maude_worker.__file__).read_bytes()
                + b"\n# source drift\n"
            )
            with mock.patch.object(
                maude_rewrite,
                "_worker_path",
                return_value=drifted_worker,
            ), mock.patch.object(
                maude_rewrite, "_run_worker"
            ) as run_worker:
                outcome = self.evaluate(
                    request("received", "validate", "validated"),
                    MaudeTransitionProfile(),
                )
        self.assertEqual(outcome.disposition, Disposition.BLOCKED)
        self.assertEqual(outcome.reason, "maude_worker_source_drift")
        run_worker.assert_not_called()

    def test_semantic_replay_is_byte_stable_at_the_evidence_surface(self) -> None:
        first = self.evaluate(
            request("received", "validate", "validated")
        )
        second = self.evaluate(
            request("received", "validate", "validated")
        )
        self.assertEqual(first.disposition, Disposition.ELIGIBLE)
        self.assertEqual(second.disposition, Disposition.ELIGIBLE)
        self.assertEqual(first.reason, second.reason)
        self.assertEqual(first.evidence, second.evidence)
        self.assertEqual(
            canonical_json(first.evidence),
            canonical_json(second.evidence),
        )

    def test_production_admission_logic_contains_no_assert_statement(
        self,
    ) -> None:
        for module_path in (
            Path(maude_rewrite.__file__),
            Path(_maude_worker.__file__),
        ):
            tree = ast.parse(module_path.read_text(encoding="utf-8"))
            assertion_lines = [
                node.lineno
                for node in ast.walk(tree)
                if isinstance(node, ast.Assert)
            ]
            self.assertEqual(
                assertion_lines,
                [],
                f"{module_path} has optimization-sensitive assert logic",
            )

    def test_worker_bound_validation_runs_normally_and_under_optimization(
        self,
    ) -> None:
        invalid_job = json.loads(worker_job(self.profile))
        invalid_job["max_equations"] = 1
        worker_source_root = str(
            Path(_maude_worker.__file__).resolve().parents[1]
        )
        script = """
import sys

sys.path.insert(0, sys.argv[1])
from constraintbox import _maude_worker

observation = _maude_worker.observe(sys.stdin.buffer.read())
if observation["status"] != "invalid_job":
    raise SystemExit("expected invalid_job")
if observation["operation"] != "job_validation":
    raise SystemExit("expected job_validation")
if not observation["error_type"]:
    raise SystemExit("expected typed validation error")
"""
        for flags in ((), ("-O",)):
            with self.subTest(flags=flags):
                process = subprocess.run(
                    [
                        sys.executable,
                        "-I",
                        *flags,
                        "-c",
                        script,
                        worker_source_root,
                    ],
                    input=canonical_json(invalid_job),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                    timeout=5.0,
                )
                self.assertEqual(
                    process.returncode,
                    0,
                    process.stderr.decode("utf-8", errors="replace"),
                )


if __name__ == "__main__":
    unittest.main()
