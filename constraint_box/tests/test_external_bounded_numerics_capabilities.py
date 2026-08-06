from __future__ import annotations

import copy
import hashlib
import inspect
import os
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

import constraintbox.external_bounded_numerics as bounded_numerics_module
import constraintbox.external_diffrax_capability_flow as diffrax_flow_module
import constraintbox.external_scipy_capability_flow as scipy_flow_module
from constraintbox.external_bounded_numerics import (
    BoundedNumericsBinding,
    BoundedNumericsCapabilityBroker,
    SEVERED_EXIT_CODE,
    SEVERED_PREFIX,
    bounded_numerics_binding_from_dict,
    worker_path,
)
from constraintbox.external_diffrax_capability import (
    CAPABILITY_CLAIM_CEILING as DIFFRAX_CLAIM_CEILING,
    DIFFRAX_TSIT5_PROFILE,
    derive_diffrax_tsit5_challenge_case,
    validate_diffrax_tsit5_receipt,
)
from constraintbox.external_diffrax_capability_flow import (
    run_diffrax_tsit5_capability_flow,
)
from constraintbox.external_scipy_capability import (
    CAPABILITY_CLAIM_CEILING as SCIPY_CLAIM_CEILING,
    SCIPY_EXPM_PROFILE,
    derive_scipy_expm_challenge_case,
    validate_scipy_expm_receipt,
)
from constraintbox.external_scipy_capability_flow import (
    run_scipy_expm_capability_flow,
)
from constraintbox.external_runtime_profiles import (
    inspect_external_runtime,
    runtime_profile_dict,
)
from constraintbox.intake import canonical_json, parse_json_object


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rehash_receipt(receipt: dict[str, object]) -> str:
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    receipt_sha256 = hashlib.sha256(canonical_json(body)).hexdigest()
    receipt["receipt_sha256"] = receipt_sha256
    return receipt_sha256


class ExternalBoundedNumericsCapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary_directory = tempfile.TemporaryDirectory(dir="/private/tmp")
        cls.root = Path(cls._temporary_directory.name).resolve()
        cls.scipy_result = run_scipy_expm_capability_flow(
            request_id="fresh-scipy-profile",
            run_root=cls.root / "scipy",
        )
        cls.diffrax_result = run_diffrax_tsit5_capability_flow(
            request_id="fresh-diffrax-profile",
            run_root=cls.root / "diffrax",
        )
        cls.scipy_receipt = parse_json_object(
            Path(cls.scipy_result["artifacts"]["capability_receipt"]).read_bytes()
        )
        cls.diffrax_receipt = parse_json_object(
            Path(cls.diffrax_result["artifacts"]["capability_receipt"]).read_bytes()
        )
        cls.scipy_flow = parse_json_object(
            Path(cls.scipy_result["artifacts"]["flow_receipt"]).read_bytes()
        )
        cls.diffrax_flow = parse_json_object(
            Path(cls.diffrax_result["artifacts"]["flow_receipt"]).read_bytes()
        )
        cls.scipy_binding = bounded_numerics_binding_from_dict(
            SCIPY_EXPM_PROFILE, cls.scipy_receipt["binding"]
        )
        cls.diffrax_binding = bounded_numerics_binding_from_dict(
            DIFFRAX_TSIT5_PROFILE, cls.diffrax_receipt["binding"]
        )
        cls.scipy_replay_failure_receipt = cls._run_real_scipy_replay_poison()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary_directory.cleanup()

    def _validate_scipy(
        self,
        receipt: dict[str, object],
        *,
        receipt_sha256: str | None = None,
        require_pass: bool = True,
    ) -> tuple[str, ...]:
        return validate_scipy_expm_receipt(
            receipt,
            expected_binding=self.scipy_binding,
            expected_receipt_sha256=receipt_sha256 or receipt["receipt_sha256"],
            require_pass=require_pass,
        )

    def _validate_diffrax(
        self,
        receipt: dict[str, object],
        *,
        receipt_sha256: str | None = None,
        require_pass: bool = True,
    ) -> tuple[str, ...]:
        return validate_diffrax_tsit5_receipt(
            receipt,
            expected_binding=self.diffrax_binding,
            expected_receipt_sha256=receipt_sha256 or receipt["receipt_sha256"],
            require_pass=require_pass,
        )

    @classmethod
    def _run_real_scipy_replay_poison(cls) -> dict[str, object]:
        """Produce one controller-recomputed failure from the real worker.

        The broker has no caller-facing fault switch.  This test-only seam
        changes only its second normal worker invocation into the existing
        controller-selected operation poison: normal is a real successful
        SciPy call, replay is a real operation-severed process, and the third
        call remains the ordinary severance control.
        """

        original_run_worker = bounded_numerics_module._run_worker
        ordinary_runs = 0

        def poison_only_the_real_replay(
            profile: object,
            case: object,
            binding: object,
            *,
            poisoned_operation: str | None = None,
        ) -> dict[str, object]:
            nonlocal ordinary_runs
            if poisoned_operation is None:
                ordinary_runs += 1
                if ordinary_runs == 2:
                    # The worker itself replaces scipy.linalg.expm before it
                    # is called.  No witness/receipt is fabricated here.
                    return original_run_worker(
                        profile,
                        case,
                        binding,
                        poisoned_operation=profile.exact_api[-1],
                    )
            return original_run_worker(
                profile,
                case,
                binding,
                poisoned_operation=poisoned_operation,
            )

        with mock.patch.object(
            bounded_numerics_module,
            "_run_worker",
            side_effect=poison_only_the_real_replay,
        ):
            return BoundedNumericsCapabilityBroker(SCIPY_EXPM_PROFILE).run(
                cls.scipy_binding
            )

    def test_fixed_controller_challenges_are_deterministic_and_nontrivial(self) -> None:
        scipy_case = derive_scipy_expm_challenge_case("00" * 32)
        self.assertEqual(scipy_case, derive_scipy_expm_challenge_case("00" * 32))
        self.assertNotEqual(scipy_case, derive_scipy_expm_challenge_case("01" * 32))
        self.assertNotEqual(scipy_case["angular_rate"], 0.0)
        self.assertNotEqual(scipy_case["duration"], 0.0)
        self.assertNotEqual(scipy_case["angular_rate"], scipy_case["wrong_angular_rate"])
        self.assertEqual(scipy_case["boundary_duration"], 0.0)

        diffrax_case = derive_diffrax_tsit5_challenge_case("00" * 32)
        self.assertEqual(diffrax_case, derive_diffrax_tsit5_challenge_case("00" * 32))
        self.assertNotEqual(diffrax_case, derive_diffrax_tsit5_challenge_case("01" * 32))
        self.assertLess(diffrax_case["rate"], 0.0)
        self.assertNotEqual(diffrax_case["rate"], diffrax_case["wrong_rate"])
        self.assertEqual(diffrax_case["boundary_rate"], 0.0)
        self.assertGreater(diffrax_case["boundary_duration"], 0.0)

    def test_real_scipy_and_diffrax_flows_are_fixed_two_node_minilev_paths(self) -> None:
        cases = (
            (
                "scipy",
                self.scipy_result,
                self.scipy_receipt,
                self.scipy_flow,
                ["scipy-expm-capability-tool", "scipy-expm-capability-gate"],
                ["scipy.linalg.expm"],
                self._validate_scipy,
            ),
            (
                "diffrax",
                self.diffrax_result,
                self.diffrax_receipt,
                self.diffrax_flow,
                ["diffrax-tsit5-capability-tool", "diffrax-tsit5-capability-gate"],
                [
                    "diffrax.ODETerm",
                    "diffrax.Tsit5",
                    "diffrax.PIDController",
                    "diffrax.diffeqsolve",
                ],
                self._validate_diffrax,
            ),
        )
        for label, result, receipt, flow, nodes, api, validator in cases:
            with self.subTest(profile=label):
                self.assertEqual(result["disposition"], "ELIGIBLE")
                self.assertNotEqual(result["disposition"], "RELEASED")
                self.assertEqual(receipt["status"], "PASS")
                self.assertEqual(receipt["reason"], "exact_operation_controls_passed")
                self.assertEqual(validator(receipt), ())
                self.assertEqual(flow["terminal"], "ELIGIBLE")
                self.assertEqual(flow["steps"], 2)
                self.assertEqual([node["node_id"] for node in flow["policy"]["nodes"]], nodes)
                self.assertEqual(receipt["normal"]["witness"]["exact_api"], api)
                self.assertEqual(
                    receipt["controls"],
                    {
                        "positive": True,
                        "targeted_negative": True,
                        "boundary": True,
                        "replay": True,
                        "severance": True,
                    },
                )
                ledger_rows = [
                    parse_json_object(line.encode("utf-8"))["record"]
                    for line in Path(result["artifacts"]["flow_ledger"])
                    .read_text(encoding="utf-8")
                    .splitlines()
                ]
                self.assertEqual(
                    [
                        (row["node_id"], row["typed_signal"], row["controller_selected_next"])
                        for row in ledger_rows
                    ],
                    [
                        (nodes[0], "OBSERVED", nodes[1]),
                        (nodes[1], "PASS", "ELIGIBLE"),
                    ],
                )

    def test_receipts_bind_portable_runtime_profile_worker_sources_and_artifacts(self) -> None:
        cases = (
            (self.scipy_receipt, SCIPY_EXPM_PROFILE),
            (self.diffrax_receipt, DIFFRAX_TSIT5_PROFILE),
        )
        runtime = inspect_external_runtime("python")
        self.assertTrue(runtime["eligible"])
        self.assertEqual(runtime["runtime_pin"], runtime_profile_dict("python"))
        self.assertFalse(runtime["runtime_pin"]["artifact_sha256_is_policy_input"])
        self.assertFalse(runtime["executable_sha256_is_policy_input"])
        for receipt, profile in cases:
            with self.subTest(profile=profile.capability_id):
                self.assertEqual(receipt["runtime"], runtime)
                self.assertEqual(receipt["worker_source_sha256"], _digest(worker_path()))
                self.assertEqual(
                    receipt["worker_source_sha256_expected"], _digest(worker_path())
                )
                self.assertEqual(_digest(Path(profile.profile_source_path)), receipt["profile_source_sha256"])
                self.assertEqual(_digest(worker_path()), receipt["worker_source_sha256"])
                artifacts = receipt["package_artifacts_after"]
                self.assertEqual(artifacts["status"], "PASS")
                self.assertEqual(artifacts["runtime"], runtime)
                self.assertEqual(
                    [row["distribution"] for row in artifacts["artifacts"]],
                    [requirement[0] for requirement in profile.python_distribution_requirements],
                )
                for artifact in artifacts["artifacts"]:
                    self.assertTrue(artifact["observed"])
                    self.assertEqual(artifact["reason"], "distribution_profile_matched")
                    self.assertFalse(artifact["artifact_sha256_is_policy_input"])
                self.assertEqual(receipt["package_artifacts_before"], artifacts)

    def test_severance_and_replay_are_separate_real_worker_controls(self) -> None:
        worker_source = worker_path().read_text(encoding="utf-8")
        # The poisoned process has to replace the named callable; an early
        # environment-only exit would not discriminate a decorative import.
        self.assertIn(
            'scipy.linalg.expm = _operation_poison_wrapper("scipy.linalg.expm")',
            worker_source,
        )
        self.assertIn(
            'diffrax.diffeqsolve = _operation_poison_wrapper("diffrax.diffeqsolve")',
            worker_source,
        )
        for receipt, profile in (
            (self.scipy_receipt, SCIPY_EXPM_PROFILE),
            (self.diffrax_receipt, DIFFRAX_TSIT5_PROFILE),
        ):
            with self.subTest(profile=profile.capability_id):
                normal = receipt["normal"]
                replay = receipt["replay"]
                severance = receipt["severance"]
                self.assertNotEqual(normal["witness"]["pid"], os.getpid())
                self.assertNotEqual(replay["witness"]["pid"], os.getpid())
                self.assertNotEqual(normal["witness"]["pid"], replay["witness"]["pid"])
                self.assertEqual(severance["returncode"], SEVERED_EXIT_CODE)
                self.assertEqual(severance["stdout_sha256"], hashlib.sha256(b"").hexdigest())
                marker = SEVERED_PREFIX + profile.exact_api[-1].encode("utf-8") + b"\n"
                self.assertEqual(severance["stderr_sha256"], hashlib.sha256(marker).hexdigest())

    def test_ambient_severance_selector_cannot_poison_a_normal_real_worker_run(self) -> None:
        """Only the controller may select an operation-severance control.

        This runs the real isolated SciPy worker, rather than merely checking
        a dictionary.  It catches the former failure mode where a caller's
        environment could make the normal path look blocked before CB had
        selected a negative control itself.
        """

        with tempfile.TemporaryDirectory(dir="/private/tmp") as directory:
            root = Path(directory).resolve() / "ambient-severance-scrub"
            with mock.patch.dict(
                os.environ,
                {"CONSTRAINTBOX_SEVER_OPERATION": "scipy.linalg.expm"},
            ):
                result = run_scipy_expm_capability_flow(
                    request_id="ambient-severance-scrub-v1",
                    run_root=root,
                )
            receipt = parse_json_object(
                Path(result["artifacts"]["capability_receipt"]).read_bytes()
            )
        self.assertEqual(result["disposition"], "ELIGIBLE")
        self.assertEqual(receipt["status"], "PASS")
        self.assertTrue(receipt["controls"]["severance"])

    def test_wrong_analytic_value_and_substituted_api_are_rejected_after_rehash(self) -> None:
        scipy_wrong = copy.deepcopy(self.scipy_receipt)
        scipy_wrong["normal"]["witness"]["observed"]["matrix"] = scipy_wrong["expectations"]["wrong_expected"]["matrix"]
        witness = scipy_wrong["normal"]["witness"]
        scipy_wrong["normal"]["stdout_sha256"] = hashlib.sha256(canonical_json(witness) + b"\n").hexdigest()
        scipy_root = _rehash_receipt(scipy_wrong)
        self.assertTrue(any("$.controls" in error for error in self._validate_scipy(scipy_wrong, receipt_sha256=scipy_root)))

        diffrax_api = copy.deepcopy(self.diffrax_receipt)
        diffrax_api["normal"]["witness"]["exact_api"] = ["diffrax.Euler"]
        witness = diffrax_api["normal"]["witness"]
        diffrax_api["normal"]["stdout_sha256"] = hashlib.sha256(canonical_json(witness) + b"\n").hexdigest()
        diffrax_root = _rehash_receipt(diffrax_api)
        self.assertTrue(any("exact_api_mismatch" in error for error in self._validate_diffrax(diffrax_api, receipt_sha256=diffrax_root)))

    def test_real_controller_recomputed_scipy_failure_is_self_validating(self) -> None:
        """A genuine replay failure remains an auditable non-pass receipt.

        This is deliberately not a success result: it proves the narrow
        `require_pass=False` path validates all available real worker evidence
        rather than merely accepting a receipt root and failure string.
        """

        receipt = self.scipy_replay_failure_receipt
        self.assertEqual(receipt["status"], "FAIL")
        self.assertEqual(receipt["reason"], "controller_recomputed_check_failed")
        self.assertEqual(receipt["normal"]["returncode"], 0)
        self.assertIsInstance(receipt["normal"]["witness"], dict)
        self.assertEqual(receipt["replay"]["returncode"], SEVERED_EXIT_CODE)
        self.assertIsNone(receipt["replay"]["witness"])
        self.assertEqual(receipt["severance"]["returncode"], SEVERED_EXIT_CODE)
        self.assertIsNone(receipt["severance"]["witness"])
        self.assertIn(False, receipt["controls"].values())
        self.assertEqual(self._validate_scipy(receipt, require_pass=False), ())

    def test_rehashed_controller_failure_tampering_cannot_pass_replay(self) -> None:
        """The failure branch binds each public row, binding, and controls."""

        def mutate_normal_input(receipt: dict[str, object]) -> None:
            receipt["normal"]["input_sha256"] = "0" * 64

        def mutate_replay_input(receipt: dict[str, object]) -> None:
            receipt["replay"]["input_sha256"] = "0" * 64

        def mutate_severance_input(receipt: dict[str, object]) -> None:
            receipt["severance"]["input_sha256"] = "0" * 64

        def mutate_controller_binding(receipt: dict[str, object]) -> None:
            receipt["binding"]["run_id"] = "tampered-controller-binding"
            receipt["binding_sha256"] = hashlib.sha256(
                canonical_json(receipt["binding"])
            ).hexdigest()

        def mutate_controls(receipt: dict[str, object]) -> None:
            receipt["controls"]["replay"] = True

        cases = (
            ("normal_input", mutate_normal_input, "$.normal.input_sha256:mismatch"),
            ("replay_input", mutate_replay_input, "$.replay.input_sha256:mismatch"),
            (
                "severance_input",
                mutate_severance_input,
                "$.severance.input_sha256:mismatch",
            ),
            ("controller_binding", mutate_controller_binding, "$.binding:mismatch"),
            ("controls", mutate_controls, "$.controls:mismatch"),
        )
        for label, mutate, expected_error in cases:
            with self.subTest(tamper=label):
                candidate = copy.deepcopy(self.scipy_replay_failure_receipt)
                mutate(candidate)
                root = _rehash_receipt(candidate)
                errors = self._validate_scipy(
                    candidate,
                    receipt_sha256=root,
                    require_pass=False,
                )
                self.assertIn(expected_error, errors)

    def test_unsupported_package_profile_parks_before_worker_execution(self) -> None:
        """A nonmatching compatible-version policy never enters the worker path."""

        altered_profile = replace(
            SCIPY_EXPM_PROFILE,
            python_distribution_requirements=(
                ("scipy", ("scipy",), (9, 0, 0), (10, 0, 0)),
            ),
        )
        receipt = BoundedNumericsCapabilityBroker(altered_profile).run(
            self.scipy_binding
        )
        self.assertEqual(receipt["status"], "PARKED")
        self.assertEqual(receipt["reason"], "python_distribution_version_unsupported")
        self.assertIsNone(receipt["normal"])
        self.assertIsNone(receipt["replay"])
        self.assertIsNone(receipt["severance"])
        self.assertFalse(any(receipt["controls"].values()))

    def test_unsupported_package_profile_cannot_be_called_passing(self) -> None:
        altered_profile = replace(
            SCIPY_EXPM_PROFILE,
            python_distribution_requirements=(
                ("scipy", ("scipy",), (9, 0, 0), (10, 0, 0)),
            ),
        )
        receipt = BoundedNumericsCapabilityBroker(altered_profile).run(self.scipy_binding)
        self.assertEqual(receipt["status"], "PARKED")
        self.assertEqual(receipt["reason"], "python_distribution_version_unsupported")
        self.assertFalse(any(receipt["controls"].values()))

    def test_callers_cannot_supply_runtime_seed_or_release_knobs(self) -> None:
        for function, prefix in (
            (run_scipy_expm_capability_flow, "scipy"),
            (run_diffrax_tsit5_capability_flow, "diffrax"),
        ):
            with self.subTest(function=function.__name__):
                signature = inspect.signature(function)
                self.assertEqual(list(signature.parameters), ["request_id", "run_root"])
                self.assertTrue(all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in signature.parameters.values()))
                for field, value in {
                    "executable": "/usr/bin/python3",
                    "seed": "0" * 64,
                    "profile": "anything",
                    "transition": "RELEASED",
                }.items():
                    with self.subTest(field=field), self.assertRaises(TypeError):
                        function(
                            request_id=f"authority-{prefix}",
                            run_root=self.root / f"forbidden-{prefix}-{field}",
                            **{field: value},
                        )

    def test_rebound_profile_runner_is_rejected_before_worker_execution(self) -> None:
        with mock.patch.object(scipy_flow_module, "run_scipy_expm_capability", object()):
            with self.assertRaisesRegex(Exception, "dependency binding drift"):
                run_scipy_expm_capability_flow(
                    request_id="scipy-rebound",
                    run_root=self.root / "scipy-rebound",
                )
        with mock.patch.object(diffrax_flow_module, "run_diffrax_tsit5_capability", object()):
            with self.assertRaisesRegex(Exception, "dependency binding drift"):
                run_diffrax_tsit5_capability_flow(
                    request_id="diffrax-rebound",
                    run_root=self.root / "diffrax-rebound",
                )

    def test_passes_stay_external_and_non_promoting(self) -> None:
        for result, receipt, ceiling in (
            (self.scipy_result, self.scipy_receipt, SCIPY_CLAIM_CEILING),
            (self.diffrax_result, self.diffrax_receipt, DIFFRAX_CLAIM_CEILING),
        ):
            with self.subTest(capability=receipt["capability_id"]):
                self.assertTrue(result["external_system"])
                self.assertEqual(result["kernel_membership"], "EXTERNAL_NOT_CB_KERNEL")
                self.assertEqual(result["claim_ceiling"], ceiling)
                for key in (
                    "release_allowed",
                    "engine_readiness_claim",
                    "cr_truth_claim",
                    "promotion_allowed",
                ):
                    self.assertIs(result[key], False)
                    self.assertIs(receipt[key], False)
                for forbidden in (
                    "readiness",
                    "CR truth",
                    "scientific proof",
                    "hostile-code containment",
                    "canonical promotion",
                ):
                    self.assertIn(forbidden, ceiling)


if __name__ == "__main__":
    unittest.main()
