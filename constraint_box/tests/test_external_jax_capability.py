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

import constraintbox.external_engine_packet as packet_module
import constraintbox.external_jax_capability as capability_module
from constraintbox.external_engine_packet import (
    EXACT_APIS,
    FIXTURE_SHA256,
    INPUT_SCHEMA,
    WORKER_SHA256,
    ExternalEnginePacketBroker,
    evaluate_worker_output,
)
from constraintbox.external_jax_capability import (
    BINDING_SCHEMA,
    CAPABILITY_CLAIM_CEILING,
    CAPABILITY_ID,
    CAPABILITY_SCHEMA,
    JAX_PACKAGE_VERSION,
    JAX_RUNTIME_REQUIREMENTS,
    STEP_ID,
    JaxAutodiffCapabilityBroker,
    JaxCapabilityBinding,
    derive_jax_challenge_case,
    jax_capability_binding_from_dict,
    validate_jax_capability_receipt,
)
from constraintbox.external_runtime_profiles import runtime_profile_dict
from constraintbox.external_jax_capability_flow import (
    CAPABILITY_RECEIPT_NAME,
    FLOW_LEDGER_NAME,
    FLOW_RECEIPT_NAME,
    ExternalJaxCapabilityFlowError,
    run_jax_capability_flow,
)
from constraintbox.intake import canonical_json, parse_json_object


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recompute_receipt_root(receipt: dict[str, object]) -> str:
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    receipt_sha256 = hashlib.sha256(canonical_json(body)).hexdigest()
    receipt["receipt_sha256"] = receipt_sha256
    return receipt_sha256


def binding_from_receipt(receipt: dict[str, object]) -> JaxCapabilityBinding:
    return jax_capability_binding_from_dict(receipt["binding"])


class ExternalJaxCapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary_directory = tempfile.TemporaryDirectory(dir="/private/tmp")
        cls.root = Path(cls._temporary_directory.name).resolve()
        cls.first_result = run_jax_capability_flow(
            request_id="fresh-jax-a",
            run_root=cls.root / "fresh-jax-a",
        )
        cls.second_result = run_jax_capability_flow(
            request_id="fresh-jax-b",
            run_root=cls.root / "fresh-jax-b",
        )
        cls.first_capability_receipt = parse_json_object(
            Path(cls.first_result["artifacts"]["capability_receipt"]).read_bytes()
        )
        cls.second_capability_receipt = parse_json_object(
            Path(cls.second_result["artifacts"]["capability_receipt"]).read_bytes()
        )
        cls.first_flow_receipt = parse_json_object(
            Path(cls.first_result["artifacts"]["flow_receipt"]).read_bytes()
        )
        cls.first_binding = binding_from_receipt(cls.first_capability_receipt)
        cls.second_binding = binding_from_receipt(cls.second_capability_receipt)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary_directory.cleanup()

    def _validate(
        self,
        receipt: dict[str, object],
        *,
        binding: JaxCapabilityBinding | None = None,
        receipt_sha256: str | None = None,
        require_pass: bool = True,
    ) -> tuple[str, ...]:
        return validate_jax_capability_receipt(
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
            "cubic": 1.406017965493,
            "linear": -0.46428649242,
            "points": [0.413297173321, 0.794855996165, 1.115207339925],
            "wrong_derivatives": [0.506218500441, 2.460663317632, 5.051654037646],
            "boundary_point": 0.0,
        }
        self.assertEqual(derive_jax_challenge_case(seed), expected)
        self.assertEqual(derive_jax_challenge_case(seed), expected)
        self.assertNotEqual(derive_jax_challenge_case("01" * 32), expected)

    def test_fresh_real_jax_flow_passes_two_node_mini_levos(self) -> None:
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
            ["jax-capability-gate", "jax-capability-tool"],
        )
        self.assertEqual(
            [node["node_id"] for node in flow["policy"]["nodes"]],
            ["jax-capability-tool", "jax-capability-gate"],
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
                    "jax-capability-tool",
                    "OBSERVED",
                    "jax-capability-gate",
                ),
                ("jax-capability-gate", "PASS", "ELIGIBLE"),
            ],
        )
        self.assertEqual(
            receipt["row"]["exact_api"],
            ["jax.grad", "jax.vmap", "jax.jit"],
        )
        self.assertEqual(
            receipt["row"]["controls"],
            {"positive": True, "targeted_negative": True, "boundary": True},
        )

    def test_fresh_controller_challenge_changes_per_run(self) -> None:
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

    def test_receipt_binds_source_runtime_and_jax_distribution_profile(self) -> None:
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
        self.assertEqual(receipt["worker_source_sha256"], WORKER_SHA256["python"])
        self.assertEqual(
            receipt["worker_source_sha256_expected"], WORKER_SHA256["python"]
        )

        self.assertEqual(
            receipt["jax_artifacts_before"], receipt["jax_artifacts_after"]
        )
        self.assertEqual(receipt["jax_artifacts_after"]["status"], "PASS")
        artifacts = receipt["jax_artifacts_after"]["artifacts"]
        self.assertEqual(len(artifacts), len(JAX_RUNTIME_REQUIREMENTS))
        self.assertEqual(
            [artifact["distribution"] for artifact in artifacts],
            ["jax", "jaxlib"],
        )
        for observed in artifacts:
            self.assertFalse(observed["artifact_sha256_is_policy_input"])
            self.assertTrue(observed["observed"])
            self.assertEqual(observed["reason"], "distribution_profile_matched")
            self.assertTrue(observed["module_origins"][0]["matches_distribution"])
            module = observed["module_origins"][0]
            self.assertEqual(
                digest(Path(module["resolved_origin"])), module["sha256"]
            )

        self.assertTrue(row["runtime"]["package_version"].startswith("0.10."))
        self.assertIs(row["runtime"]["x64"], True)
        self.assertEqual(row["runtime"]["platform"], "cpu")
        self.assertEqual(row["runtime_pin"], runtime_profile_dict("python"))
        self.assertFalse(row["executable_sha256_is_policy_input"])
        self.assertEqual(row["command"], packet_broker._command("jax_autodiff")[0])
        self.assertEqual(row["command"][1], "-I")
        self.assertEqual(digest(Path(row["executable_resolved_path"])), row["executable_sha256"])
        self.assertNotEqual(row["worker_pid"], os.getpid())

        transport = {
            "schema": INPUT_SCHEMA,
            "engine_id": "jax_autodiff",
            "case": case,
            "execution_binding": binding,
        }
        self.assertEqual(
            row["input_sha256"],
            hashlib.sha256(canonical_json(transport)).hexdigest(),
        )

    def test_binding_and_challenge_tampering_are_rejected_after_rehash(self) -> None:
        binding_tampered = copy.deepcopy(self.first_capability_receipt)
        binding_tampered["binding"]["run_id"] = "forged-jax-run"
        binding_tampered["binding_sha256"] = hashlib.sha256(
            canonical_json(binding_tampered["binding"])
        ).hexdigest()
        binding_root = recompute_receipt_root(binding_tampered)
        binding_errors = self._validate(
            binding_tampered,
            receipt_sha256=binding_root,
        )
        self.assertTrue(any("$.binding" in error for error in binding_errors))

        challenge_tampered = copy.deepcopy(self.first_capability_receipt)
        challenge_tampered["challenge_case"]["cubic"] += 0.125
        challenge_tampered["challenge_case_sha256"] = hashlib.sha256(
            canonical_json(challenge_tampered["challenge_case"])
        ).hexdigest()
        challenge_root = recompute_receipt_root(challenge_tampered)
        challenge_errors = self._validate(
            challenge_tampered,
            receipt_sha256=challenge_root,
        )
        self.assertTrue(
            any("$.challenge_case:" in error for error in challenge_errors)
        )

    def test_wrong_analytic_values_fail_controller_recomputation(self) -> None:
        receipt = self.first_capability_receipt
        row = receipt["row"]
        wrong_witness = {
            "schema": "constraintbox.external-engine-witness.v1",
            "engine_id": "jax_autodiff",
            "exact_api": EXACT_APIS["jax_autodiff"],
            "observed": {
                "derivatives": receipt["challenge_case"]["wrong_derivatives"],
                "boundary_derivative": row["observed"]["boundary_derivative"],
            },
            "runtime": row["runtime"],
            "pid": os.getpid() + 10_000,
            "execution_binding": receipt["binding"],
        }
        fixture, _canonical, _fixture_sha256 = (
            ExternalEnginePacketBroker()._load_fixture()
        )
        challenged_fixture = {**fixture, "jax": receipt["challenge_case"]}
        evaluation = evaluate_worker_output(
            "jax_autodiff",
            challenged_fixture,
            wrong_witness,
            controller_pid=os.getpid(),
            expected_execution_binding=receipt["binding"],
        )

        self.assertFalse(evaluation["controls"]["positive"])
        self.assertFalse(evaluation["controls"]["targeted_negative"])
        self.assertTrue(evaluation["controls"]["boundary"])
        self.assertEqual(evaluation["errors"], [])

    def test_substituted_or_missing_jax_api_cannot_pass(self) -> None:
        binding = self.first_binding

        def substituted_run(
            command: list[str],
            **kwargs: object,
        ) -> subprocess.CompletedProcess[bytes]:
            transport = parse_json_object(kwargs["input"])
            case = transport["case"]
            cubic = float(case["cubic"])
            linear = float(case["linear"])
            derivatives = [
                3.0 * cubic * float(point) ** 2 + linear
                for point in case["points"]
            ]
            boundary_derivative = (
                3.0 * cubic * float(case["boundary_point"]) ** 2 + linear
            )
            witness = {
                "schema": "constraintbox.external-engine-witness.v1",
                "engine_id": "jax_autodiff",
                "exact_api": ["jax.jacfwd"],
                "observed": {
                    "derivatives": derivatives,
                    "boundary_derivative": boundary_derivative,
                },
                "runtime": {
                    "package_version": JAX_PACKAGE_VERSION,
                    "x64": True,
                    "device": "cpu:0",
                    "platform": "cpu",
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
            substituted = JaxAutodiffCapabilityBroker().run(binding)
        self.assertEqual(substituted["status"], "FAIL")
        self.assertEqual(
            substituted["reason"], "controller_recomputed_check_failed"
        )
        self.assertIn(
            "exact_api_mismatch",
            substituted["row"]["controller_evaluation"]["errors"],
        )
        self.assertFalse(any(substituted["row"]["controls"].values()))

    def test_alternate_runtime_and_request_controls_never_pass(self) -> None:
        alternate = Path("/usr/bin/python3")
        self.assertTrue(alternate.is_file())
        alternate_receipt = JaxAutodiffCapabilityBroker(
            ExternalEnginePacketBroker(
                python_executable=alternate,
                timeout_seconds=1.0,
            )
        ).run(self.first_binding)
        self.assertEqual(alternate_receipt["status"], "FAIL")
        self.assertEqual(
            alternate_receipt["reason"], "runtime_selection_override_rejected"
        )

        signature = inspect.signature(run_jax_capability_flow)
        self.assertEqual(list(signature.parameters), ["request_id", "run_root"])
        for parameter in signature.parameters.values():
            self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
        for field, value in {
            "executable": "/usr/bin/python3",
            "fixture": "/tmp/fixture.json",
            "tolerance": 1.0,
            "seed": "0" * 64,
            "transition": "RELEASED",
        }.items():
            with self.subTest(field=field), self.assertRaises(TypeError):
                run_jax_capability_flow(
                    request_id="request-authority",
                    run_root=self.root / f"forbidden-{field}",
                    **{field: value},
                )

    def test_existing_run_root_and_live_dependency_rebinding_are_rejected(self) -> None:
        existing = self.root / "already-exists"
        existing.mkdir()
        with self.assertRaisesRegex(
            ExternalJaxCapabilityFlowError,
            "run directory must be new",
        ):
            run_jax_capability_flow(request_id="existing-run", run_root=existing)

        with mock.patch(
            "constraintbox.external_jax_capability_flow.JaxAutodiffCapabilityBroker",
            object(),
        ):
            with self.assertRaises(ExternalJaxCapabilityFlowError):
                run_jax_capability_flow(
                    request_id="dependency-drift",
                    run_root=self.root / "dependency-drift",
                )

    def test_pass_stays_external_and_non_promoting(self) -> None:
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
            receipt["release_allowed"],
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
        self.assertEqual(result["kernel_membership"], "EXTERNAL_NOT_CB_KERNEL")
        self.assertEqual(result["claim_ceiling"], CAPABILITY_CLAIM_CEILING)
        self.assertEqual(receipt["claim_ceiling"], CAPABILITY_CLAIM_CEILING)
        for forbidden in (
            "JAX readiness",
            "sim-stack readiness",
            "CR truth",
            "scientific proof",
            "canonical promotion",
        ):
            self.assertIn(forbidden, CAPABILITY_CLAIM_CEILING)
        self.assertEqual(
            Path(result["artifacts"]["capability_receipt"]).name,
            CAPABILITY_RECEIPT_NAME,
        )
        self.assertEqual(
            Path(result["artifacts"]["flow_receipt"]).name,
            FLOW_RECEIPT_NAME,
        )
        self.assertEqual(
            Path(result["artifacts"]["flow_ledger"]).name,
            FLOW_LEDGER_NAME,
        )


if __name__ == "__main__":
    unittest.main()
