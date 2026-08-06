from __future__ import annotations

import copy
import hashlib
import inspect
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import constraintbox
import constraintbox.external_capability as capability_module
import constraintbox.external_capability_flow as capability_flow_module
import constraintbox.external_engine_packet as packet_module
from constraintbox.external_capability import (
    BINDING_SCHEMA,
    CAPABILITY_CLAIM_CEILING,
    CAPABILITY_ID,
    CAPABILITY_SCHEMA,
    STEP_ID,
    TORCH_RUNTIME_REQUIREMENTS,
    CapabilityBinding,
    PytorchJacobianCapabilityBroker,
    capability_binding_from_dict,
    derive_pytorch_challenge_case,
    validate_pytorch_capability_receipt,
)
from constraintbox.external_capability_flow import (
    CAPABILITY_RECEIPT_NAME,
    FLOW_RECEIPT_NAME,
    ExternalCapabilityFlowError,
    run_pytorch_capability_flow,
)
from constraintbox.external_engine_packet import (
    EXACT_APIS,
    EXTERNAL_BOUNDARY,
    FIXTURE_SHA256,
    INPUT_SCHEMA,
    WORKER_SHA256,
    ExternalEnginePacketBroker,
    evaluate_worker_output,
)
from constraintbox.external_runtime_profiles import runtime_profile_dict
from constraintbox.intake import canonical_json, parse_json_object


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recompute_receipt_root(receipt: dict[str, object]) -> str:
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    receipt_sha256 = hashlib.sha256(canonical_json(body)).hexdigest()
    receipt["receipt_sha256"] = receipt_sha256
    return receipt_sha256


def binding_from_receipt(receipt: dict[str, object]) -> CapabilityBinding:
    return capability_binding_from_dict(receipt["binding"])


class ExternalCapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary_directory = tempfile.TemporaryDirectory()
        cls.root = Path(cls._temporary_directory.name).resolve()
        cls.first_result = run_pytorch_capability_flow(
            request_id="fresh-real-a",
            run_root=cls.root / "fresh-real-a",
        )
        cls.second_result = run_pytorch_capability_flow(
            request_id="fresh-real-b",
            run_root=cls.root / "fresh-real-b",
        )
        cls.first_capability_receipt = parse_json_object(
            Path(
                cls.first_result["artifacts"]["capability_receipt"]
            ).read_bytes()
        )
        cls.second_capability_receipt = parse_json_object(
            Path(
                cls.second_result["artifacts"]["capability_receipt"]
            ).read_bytes()
        )
        cls.first_flow_receipt = parse_json_object(
            Path(cls.first_result["artifacts"]["flow_receipt"]).read_bytes()
        )
        cls.second_flow_receipt = parse_json_object(
            Path(cls.second_result["artifacts"]["flow_receipt"]).read_bytes()
        )
        cls.first_binding = binding_from_receipt(
            cls.first_capability_receipt
        )
        cls.second_binding = binding_from_receipt(
            cls.second_capability_receipt
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary_directory.cleanup()

    def _validate(
        self,
        receipt: dict[str, object],
        *,
        binding: CapabilityBinding | None = None,
        receipt_sha256: str | None = None,
        require_pass: bool = True,
    ) -> tuple[str, ...]:
        return validate_pytorch_capability_receipt(
            receipt,
            expected_binding=binding or self.first_binding,
            expected_receipt_sha256=(
                receipt_sha256
                if receipt_sha256 is not None
                else receipt["receipt_sha256"]
            ),
            require_pass=require_pass,
        )

    def test_fixed_seed_challenge_derivation_is_deterministic(self) -> None:
        seed = "00" * 32
        expected = {
            "alpha": 0.855052070453,
            "beta": -1.335978980078,
            "point": [1.463774399993, 0.493358894171],
            "wrong_jacobian": [[1.0, 0.0], [0.0, 1.0]],
            "boundary_point": [0.0, 0.0],
        }
        self.assertEqual(derive_pytorch_challenge_case(seed), expected)
        self.assertEqual(derive_pytorch_challenge_case(seed), expected)
        self.assertNotEqual(
            derive_pytorch_challenge_case("01" * 32),
            expected,
        )

    def test_fresh_real_torch_flow_passes_two_node_mini_levos(self) -> None:
        result = self.first_result
        receipt = self.first_capability_receipt
        flow = self.first_flow_receipt

        self.assertEqual(result["disposition"], "ELIGIBLE")
        self.assertEqual(receipt["schema"], CAPABILITY_SCHEMA)
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(receipt["reason"], "exact_operation_controls_passed")
        self.assertEqual(self._validate(receipt), ())
        self.assertEqual(flow["terminal"], "ELIGIBLE")
        self.assertEqual(flow["steps"], 2)
        self.assertEqual(
            flow["completed_nodes"],
            ["pytorch-capability-gate", "pytorch-capability-tool"],
        )
        self.assertEqual(
            [node["node_id"] for node in flow["policy"]["nodes"]],
            ["pytorch-capability-tool", "pytorch-capability-gate"],
        )
        self.assertEqual(
            [
                hook["kind"]
                for hook in flow["policy"]["hooks"]
            ],
            ["gate", "tool"],
        )
        rows = [
            parse_json_object(line.encode("utf-8"))["record"]
            for line in Path(result["artifacts"]["flow_ledger"])
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertEqual(
            [
                (
                    row["node_id"],
                    row["typed_signal"],
                    row["controller_selected_next"],
                )
                for row in rows
            ],
            [
                (
                    "pytorch-capability-tool",
                    "OBSERVED",
                    "pytorch-capability-gate",
                ),
                ("pytorch-capability-gate", "PASS", "ELIGIBLE"),
            ],
        )

    def test_controller_challenge_differs_across_fresh_runs(self) -> None:
        first = self.first_capability_receipt
        second = self.second_capability_receipt

        self.assertNotEqual(
            first["binding"]["challenge_seed_hex"],
            second["binding"]["challenge_seed_hex"],
        )
        self.assertNotEqual(
            first["challenge_case_sha256"],
            second["challenge_case_sha256"],
        )
        self.assertNotEqual(first["challenge_case"], second["challenge_case"])
        self.assertNotEqual(first["binding_sha256"], second["binding_sha256"])
        self.assertNotEqual(self.first_result["run_id"], self.second_result["run_id"])

    def test_pass_receipt_binds_exact_sources_runtime_and_streams(self) -> None:
        receipt = self.first_capability_receipt
        binding = receipt["binding"]
        case = receipt["challenge_case"]
        row = receipt["row"]
        packet_broker = ExternalEnginePacketBroker()

        self.assertEqual(binding["schema"], BINDING_SCHEMA)
        self.assertEqual(binding, row["execution_binding"])
        self.assertEqual(
            receipt["binding_sha256"],
            hashlib.sha256(canonical_json(binding)).hexdigest(),
        )
        self.assertEqual(
            receipt["challenge_case_sha256"],
            hashlib.sha256(canonical_json(case)).hexdigest(),
        )
        self.assertEqual(receipt["fixture_sha256"], FIXTURE_SHA256)
        self.assertEqual(
            receipt["capability_source_sha256"],
            digest(Path(capability_module.__file__).resolve()),
        )
        self.assertEqual(
            receipt["packet_controller_source_sha256"],
            digest(Path(packet_module.__file__).resolve()),
        )
        self.assertEqual(
            receipt["worker_source_sha256"],
            digest(packet_broker.python_worker),
        )
        self.assertEqual(
            receipt["worker_source_sha256"],
            WORKER_SHA256["python"],
        )
        self.assertEqual(
            receipt["worker_source_sha256_expected"],
            WORKER_SHA256["python"],
        )

        self.assertEqual(
            receipt["torch_artifacts_before"],
            receipt["torch_artifacts_after"],
        )
        self.assertEqual(receipt["torch_artifacts_after"]["status"], "PASS")
        artifacts = receipt["torch_artifacts_after"]["artifacts"]
        self.assertEqual(len(artifacts), len(TORCH_RUNTIME_REQUIREMENTS))
        observed = artifacts[0]
        self.assertEqual(observed["distribution"], "torch")
        self.assertEqual(
            observed["required_version_window"],
            {"minimum_inclusive": "2.11.0", "maximum_exclusive": "2.12.0"},
        )
        self.assertFalse(observed["artifact_sha256_is_policy_input"])
        self.assertTrue(observed["observed"])
        self.assertEqual(observed["reason"], "distribution_profile_matched")
        self.assertEqual(len(observed["module_origins"]), 1)
        module = observed["module_origins"][0]
        self.assertEqual(module["module"], "torch")
        self.assertTrue(module["matches_distribution"])
        self.assertEqual(digest(Path(module["resolved_origin"])), module["sha256"])

        self.assertEqual(row["exact_api"], ["torch.func.jacrev"])
        self.assertTrue(row["runtime"]["package_version"].startswith("2.11."))
        self.assertEqual(row["runtime"]["dtype"], "torch.float64")
        self.assertEqual(row["runtime"]["device"], "cpu")
        self.assertEqual(row["runtime_pin"], runtime_profile_dict("python"))
        self.assertFalse(row["executable_sha256_is_policy_input"])
        self.assertEqual(row["command"], packet_broker._command("pytorch_jacobian")[0])
        self.assertEqual(row["command"][1], "-I")
        self.assertEqual(
            digest(Path(row["executable_resolved_path"])),
            row["executable_sha256"],
        )
        self.assertEqual(row["worker_source_sha256"], WORKER_SHA256["python"])
        self.assertNotEqual(row["worker_pid"], os.getpid())

        transport = {
            "schema": INPUT_SCHEMA,
            "engine_id": "pytorch_jacobian",
            "case": case,
            "execution_binding": binding,
        }
        self.assertEqual(
            row["input_sha256"],
            hashlib.sha256(canonical_json(transport)).hexdigest(),
        )
        witness = {
            "schema": "constraintbox.external-engine-witness.v1",
            "engine_id": "pytorch_jacobian",
            "exact_api": EXACT_APIS["pytorch_jacobian"],
            "observed": row["observed"],
            "runtime": row["runtime"],
            "pid": row["worker_pid"],
            "execution_binding": binding,
        }
        witness_bytes = canonical_json(witness)
        self.assertEqual(
            row["output_sha256"],
            hashlib.sha256(witness_bytes).hexdigest(),
        )
        self.assertEqual(
            row["stdout_sha256"],
            hashlib.sha256(witness_bytes + b"\n").hexdigest(),
        )
        self.assertEqual(
            row["stderr_sha256"],
            hashlib.sha256(b"").hexdigest(),
        )

    def test_binding_tamper_is_rejected_after_rehash(self) -> None:
        tampered = copy.deepcopy(self.first_capability_receipt)
        tampered["binding"]["run_id"] = "forged-run"
        tampered["binding_sha256"] = hashlib.sha256(
            canonical_json(tampered["binding"])
        ).hexdigest()
        root = recompute_receipt_root(tampered)

        errors = self._validate(tampered, receipt_sha256=root)

        self.assertTrue(errors)
        self.assertTrue(any("$.binding" in error for error in errors))

    def test_receipt_digest_tamper_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.first_capability_receipt)
        tampered["receipt_sha256"] = "0" * 64

        errors = self._validate(
            tampered,
            receipt_sha256=self.first_capability_receipt["receipt_sha256"],
        )

        self.assertTrue(errors)
        self.assertTrue(
            any(
                path in error
                for error in errors
                for path in ("$.receipt_root", "$.receipt_sha256")
            )
        )

    def test_challenge_case_tamper_is_rejected_after_rehash(self) -> None:
        tampered = copy.deepcopy(self.first_capability_receipt)
        tampered["challenge_case"]["alpha"] += 0.125
        tampered["challenge_case_sha256"] = hashlib.sha256(
            canonical_json(tampered["challenge_case"])
        ).hexdigest()
        root = recompute_receipt_root(tampered)

        errors = self._validate(tampered, receipt_sha256=root)

        self.assertTrue(errors)
        self.assertTrue(any("$.challenge_case:" in error for error in errors))

    def test_observed_tamper_is_rejected_even_when_streams_are_rehashed(
        self,
    ) -> None:
        tampered = copy.deepcopy(self.first_capability_receipt)
        row = tampered["row"]
        row["observed"]["jacobian"] = tampered["challenge_case"][
            "wrong_jacobian"
        ]
        forged_witness = {
            "schema": "constraintbox.external-engine-witness.v1",
            "engine_id": "pytorch_jacobian",
            "exact_api": row["exact_api"],
            "observed": row["observed"],
            "runtime": row["runtime"],
            "pid": row["worker_pid"],
            "execution_binding": row["execution_binding"],
        }
        forged_bytes = canonical_json(forged_witness)
        row["output_sha256"] = hashlib.sha256(forged_bytes).hexdigest()
        row["stdout_sha256"] = hashlib.sha256(forged_bytes + b"\n").hexdigest()
        root = recompute_receipt_root(tampered)

        errors = self._validate(tampered, receipt_sha256=root)

        self.assertTrue(errors)
        self.assertTrue(
            any("$.row.controller_evaluation" in error for error in errors)
        )

    def test_control_tamper_is_rejected_after_rehash(self) -> None:
        tampered = copy.deepcopy(self.first_capability_receipt)
        tampered["row"]["controls"]["positive"] = False
        tampered["row"]["controller_evaluation"]["controls"]["positive"] = False
        root = recompute_receipt_root(tampered)

        errors = self._validate(tampered, receipt_sha256=root)

        self.assertTrue(errors)
        self.assertTrue(
            any("$.row.controller_evaluation" in error for error in errors)
        )

    def test_copied_receipt_is_rejected_under_another_binding(self) -> None:
        errors = self._validate(
            self.first_capability_receipt,
            binding=self.second_binding,
            receipt_sha256=self.first_capability_receipt["receipt_sha256"],
        )

        self.assertTrue(errors)
        self.assertTrue(any("$.binding" in error for error in errors))
        self.assertTrue(any("$.challenge_case" in error for error in errors))

    def test_minimal_fabricated_pass_receipt_is_rejected(self) -> None:
        fabricated = {
            "schema": CAPABILITY_SCHEMA,
            "capability_id": CAPABILITY_ID,
            "status": "PASS",
            "reason": "exact_operation_controls_passed",
            "receipt_sha256": hashlib.sha256(b"fabricated").hexdigest(),
        }

        errors = self._validate(fabricated)

        self.assertEqual(errors, ("$:receipt_keys_mismatch",))

    def test_wrong_analytic_values_fail_controller_recomputation(self) -> None:
        receipt = self.first_capability_receipt
        row = receipt["row"]
        wrong_witness = {
            "schema": "constraintbox.external-engine-witness.v1",
            "engine_id": "pytorch_jacobian",
            "exact_api": EXACT_APIS["pytorch_jacobian"],
            "observed": {
                "jacobian": receipt["challenge_case"]["wrong_jacobian"],
                "boundary_jacobian": row["observed"]["boundary_jacobian"],
            },
            "runtime": row["runtime"],
            "pid": os.getpid() + 10_000,
            "execution_binding": receipt["binding"],
        }
        fixture, _canonical, _fixture_sha256 = (
            ExternalEnginePacketBroker()._load_fixture()
        )
        challenged_fixture = {
            **fixture,
            "pytorch": receipt["challenge_case"],
        }

        evaluation = evaluate_worker_output(
            "pytorch_jacobian",
            challenged_fixture,
            wrong_witness,
            controller_pid=os.getpid(),
            expected_execution_binding=receipt["binding"],
        )

        self.assertFalse(evaluation["controls"]["positive"])
        self.assertFalse(evaluation["controls"]["targeted_negative"])
        self.assertTrue(evaluation["controls"]["boundary"])
        self.assertEqual(evaluation["errors"], [])

    def test_missing_or_substituted_jacrev_cannot_pass(self) -> None:
        binding = self.first_binding

        def substituted_run(
            command: list[str],
            **kwargs: object,
        ) -> subprocess.CompletedProcess[bytes]:
            transport = parse_json_object(kwargs["input"])
            case = transport["case"]
            alpha = float(case["alpha"])
            beta = float(case["beta"])
            x0, x1 = (float(value) for value in case["point"])
            bx0, bx1 = (float(value) for value in case["boundary_point"])
            witness = {
                "schema": "constraintbox.external-engine-witness.v1",
                "engine_id": "pytorch_jacobian",
                "exact_api": ["torch.autograd.functional.jacobian"],
                "observed": {
                    "jacobian": [[2.0 * alpha * x0, beta], [x1, x0]],
                    "boundary_jacobian": [
                        [2.0 * alpha * bx0, beta],
                        [bx1, bx0],
                    ],
                },
                "runtime": {
                    "package_version": "2.11.0",
                    "dtype": "torch.float64",
                    "device": "cpu",
                },
                "pid": os.getpid() + 20_000,
                "execution_binding": transport["execution_binding"],
            }
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=canonical_json(witness) + b"\n",
                stderr=b"",
            )

        with mock.patch(
            "constraintbox.external_engine_packet.subprocess.run",
            side_effect=substituted_run,
        ):
            substituted = PytorchJacobianCapabilityBroker().run(binding)
        self.assertEqual(substituted["status"], "FAIL")
        self.assertEqual(
            substituted["reason"],
            "controller_recomputed_check_failed",
        )
        self.assertIn(
            "exact_api_mismatch",
            substituted["row"]["controller_evaluation"]["errors"],
        )
        self.assertFalse(any(substituted["row"]["controls"].values()))

        def unavailable_run(
            command: list[str],
            **kwargs: object,
        ) -> subprocess.CompletedProcess[bytes]:
            transport = parse_json_object(kwargs["input"])
            witness = {
                "schema": "constraintbox.external-engine-unavailable.v1",
                "engine_id": "pytorch_jacobian",
                "exact_api": EXACT_APIS["pytorch_jacobian"],
                "reason": "torch.func.jacrev unavailable",
                "pid": os.getpid() + 30_000,
                "execution_binding": transport["execution_binding"],
            }
            return subprocess.CompletedProcess(
                command,
                3,
                stdout=canonical_json(witness) + b"\n",
                stderr=b"",
            )

        with mock.patch(
            "constraintbox.external_engine_packet.subprocess.run",
            side_effect=unavailable_run,
        ):
            unavailable = PytorchJacobianCapabilityBroker().run(binding)
        self.assertEqual(unavailable["status"], "PARKED")
        self.assertEqual(unavailable["reason"], "exact_function_unavailable")

    def test_alternate_and_missing_runtime_never_pass(self) -> None:
        alternate = Path("/usr/bin/python3")
        self.assertTrue(alternate.is_file())
        alternate_receipt = PytorchJacobianCapabilityBroker(
            ExternalEnginePacketBroker(
                python_executable=alternate,
                timeout_seconds=1.0,
            )
        ).run(self.first_binding)
        self.assertEqual(alternate_receipt["status"], "FAIL")
        self.assertEqual(
            alternate_receipt["reason"],
            "runtime_selection_override_rejected",
        )

        missing = Path("/private/tmp/constraintbox-no-such-python-runtime")
        missing_receipt = PytorchJacobianCapabilityBroker(
            ExternalEnginePacketBroker(
                python_executable=missing,
                timeout_seconds=1.0,
            )
        ).run(self.first_binding)
        self.assertEqual(missing_receipt["status"], "FAIL")
        self.assertEqual(
            missing_receipt["reason"],
            "runtime_selection_override_rejected",
        )

    def test_existing_run_directory_is_rejected_before_execution(self) -> None:
        existing = self.root / "already-exists"
        existing.mkdir()

        with self.assertRaisesRegex(
            ExternalCapabilityFlowError,
            "run directory must be new",
        ):
            run_pytorch_capability_flow(
                request_id="existing-run",
                run_root=existing,
            )

    def test_request_cannot_select_controller_owned_mechanism(self) -> None:
        signature = inspect.signature(run_pytorch_capability_flow)
        self.assertEqual(list(signature.parameters), ["request_id", "run_root"])
        for parameter in signature.parameters.values():
            self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)

        forbidden = {
            "executable": "/usr/bin/python3",
            "fixture": "/tmp/fixture.json",
            "tolerance": 1.0,
            "seed": "0" * 64,
            "transition": "RELEASED",
        }
        for field, value in forbidden.items():
            with self.subTest(field=field), self.assertRaises(TypeError):
                run_pytorch_capability_flow(
                    request_id="request-authority",
                    run_root=self.root / f"forbidden-{field}",
                    **{field: value},
                )

    def test_raw_flow_builder_is_not_a_public_package_surface(self) -> None:
        self.assertFalse(
            hasattr(constraintbox, "build_pytorch_capability_flow")
        )

    def test_live_dependency_rebinding_cannot_reach_eligibility(self) -> None:
        with mock.patch(
            "constraintbox.external_capability_flow."
            "PytorchJacobianCapabilityBroker",
            object(),
        ):
            with self.assertRaises(ExternalCapabilityFlowError):
                run_pytorch_capability_flow(
                    request_id="dependency-drift",
                    run_root=self.root / "dependency-drift",
                )

    def test_raw_runtime_rejects_binding_for_another_run_and_policy(self) -> None:
        runtime = capability_flow_module._build_pytorch_capability_flow(
            run_id="actual-capability-runtime",
            ledger_path=self.root / "forged-binding-events.jsonl",
        )
        forged = CapabilityBinding(
            capability_id=CAPABILITY_ID,
            run_id="different-capability-runtime",
            flow_policy_sha256="f" * 64,
            request_sha256="a" * 64,
            step_id=STEP_ID,
            challenge_seed_hex="0" * 64,
        )

        receipt = runtime.run(
            {
                "capability_binding_json": canonical_json(
                    forged.to_dict()
                ).decode("utf-8")
            }
        )

        self.assertEqual(receipt["terminal"], "HOLD")
        self.assertNotIn(
            "capability_receipt_json",
            receipt["final_context"],
        )

    def test_pass_does_not_claim_release_readiness_cr_or_promotion(self) -> None:
        result = self.first_result
        receipt = self.first_capability_receipt
        flow = self.first_flow_receipt

        self.assertEqual(result["disposition"], "ELIGIBLE")
        self.assertNotEqual(result["disposition"], "RELEASED")
        for value in (
            result["release_allowed"],
            result["engine_readiness_claim"],
            result["cr_truth_claim"],
            result["promotion_allowed"],
            receipt["engine_readiness_claim"],
            receipt["cr_truth_claim"],
            receipt["promotion_allowed"],
            receipt["row"]["engine_readiness_claim"],
            receipt["row"]["cr_truth_claim"],
            receipt["row"]["promotion_allowed"],
            flow["promotion_allowed"],
            flow["policy"]["promotion_allowed"],
        ):
            self.assertIs(value, False)
        self.assertTrue(result["external_system"])
        self.assertEqual(
            result["kernel_membership"],
            "EXTERNAL_NOT_CB_KERNEL",
        )
        self.assertEqual(result["claim_ceiling"], CAPABILITY_CLAIM_CEILING)
        self.assertEqual(receipt["claim_ceiling"], CAPABILITY_CLAIM_CEILING)
        self.assertEqual(receipt["row"]["claim_ceiling"], EXTERNAL_BOUNDARY)
        for forbidden in (
            "PyTorch readiness",
            "sim-stack readiness",
            "CR truth",
            "scientific proof",
            "canonical promotion",
        ):
            self.assertIn(forbidden, CAPABILITY_CLAIM_CEILING)
        self.assertTrue(
            Path(result["artifacts"]["capability_receipt"]).name
            == CAPABILITY_RECEIPT_NAME
        )
        self.assertTrue(
            Path(result["artifacts"]["flow_receipt"]).name
            == FLOW_RECEIPT_NAME
        )


if __name__ == "__main__":
    unittest.main()
