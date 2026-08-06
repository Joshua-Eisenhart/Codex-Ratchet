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
import constraintbox.external_julia_capability as capability_module
import constraintbox.external_julia_capability_flow as capability_flow_module
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
from constraintbox.external_julia_capability import (
    BINDING_SCHEMA,
    CAPABILITY_CLAIM_CEILING,
    CAPABILITY_ID,
    CAPABILITY_SCHEMA,
    DIFFERENTIALEQUATIONS_VERSION_PIN,
    JULIA_CARRIER_PROJECT_SHA256,
    JULIA_VERSION_PIN,
    STEP_ID,
    STRICT_LOAD_PATH,
    JuliaCapabilityBinding,
    JuliaDifferentialEquationsCapabilityBroker,
    derive_julia_challenge_case,
    julia_capability_binding_from_dict,
    validate_julia_capability_receipt,
)
from constraintbox.external_julia_capability_flow import (
    CAPABILITY_RECEIPT_NAME,
    FLOW_LEDGER_NAME,
    FLOW_RECEIPT_NAME,
    ExternalJuliaCapabilityFlowError,
    run_julia_capability_flow,
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


def binding_from_receipt(receipt: dict[str, object]) -> JuliaCapabilityBinding:
    return julia_capability_binding_from_dict(receipt["binding"])


class ExternalJuliaCapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary_directory = tempfile.TemporaryDirectory()
        cls.root = Path(cls._temporary_directory.name).resolve()
        cls.first_result = run_julia_capability_flow(
            request_id="fresh-real-julia-a",
            run_root=cls.root / "fresh-real-julia-a",
        )
        cls.second_result = run_julia_capability_flow(
            request_id="fresh-real-julia-b",
            run_root=cls.root / "fresh-real-julia-b",
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
        binding: JuliaCapabilityBinding | None = None,
        receipt_sha256: str | None = None,
        require_pass: bool = True,
    ) -> tuple[str, ...]:
        return validate_julia_capability_receipt(
            receipt,
            expected_binding=binding or self.first_binding,
            expected_receipt_sha256=(
                receipt_sha256
                if receipt_sha256 is not None
                else receipt["receipt_sha256"]
            ),
            require_pass=require_pass,
        )

    def test_fixed_seed_challenge_derivation_is_deterministic_and_bounded(
        self,
    ) -> None:
        seed = "00" * 32
        expected = derive_julia_challenge_case(seed)

        self.assertEqual(derive_julia_challenge_case(seed), expected)
        self.assertNotEqual(derive_julia_challenge_case("01" * 32), expected)
        self.assertEqual(
            set(expected),
            {
                "rate",
                "initial",
                "duration",
                "wrong_rate",
                "boundary_rate",
                "boundary_initial",
                "boundary_duration",
            },
        )
        self.assertGreater(expected["initial"], 0.0)
        self.assertGreater(expected["duration"], 0.0)
        self.assertGreater(expected["boundary_initial"], 0.0)
        self.assertGreater(expected["boundary_duration"], 0.0)
        self.assertNotEqual(expected["rate"], expected["wrong_rate"])

    def test_fresh_real_julia_flow_passes_two_node_mini_levos(self) -> None:
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
            ["julia-capability-gate", "julia-capability-tool"],
        )
        self.assertEqual(
            [node["node_id"] for node in flow["policy"]["nodes"]],
            ["julia-capability-tool", "julia-capability-gate"],
        )
        self.assertEqual(
            [hook["kind"] for hook in flow["policy"]["hooks"]],
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
                    "julia-capability-tool",
                    "OBSERVED",
                    "julia-capability-gate",
                ),
                ("julia-capability-gate", "PASS", "ELIGIBLE"),
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
        self.assertNotEqual(
            self.first_result["run_id"], self.second_result["run_id"]
        )

    def test_pass_receipt_binds_strict_carrier_sources_runtime_and_streams(
        self,
    ) -> None:
        receipt = self.first_capability_receipt
        binding = receipt["binding"]
        case = receipt["challenge_case"]
        row = receipt["row"]
        packet_broker = ExternalEnginePacketBroker()
        project_path = (packet_broker.julia_project / "Project.toml").resolve()

        self.assertEqual(binding["schema"], BINDING_SCHEMA)
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
            digest(packet_broker.julia_worker),
        )
        self.assertEqual(receipt["worker_source_sha256"], WORKER_SHA256["julia"])
        self.assertEqual(
            receipt["worker_source_sha256_expected"], WORKER_SHA256["julia"]
        )
        self.assertEqual(receipt["strict_carrier_project_path"], str(project_path))
        self.assertEqual(
            receipt["strict_carrier_project_sha256"],
            JULIA_CARRIER_PROJECT_SHA256,
        )
        self.assertEqual(
            digest(project_path), JULIA_CARRIER_PROJECT_SHA256
        )
        self.assertEqual(
            receipt["strict_carrier_project_sha256_expected"],
            JULIA_CARRIER_PROJECT_SHA256,
        )
        self.assertEqual(receipt["strict_load_path"], STRICT_LOAD_PATH)
        self.assertEqual(receipt["julia_runtime_pin"], runtime_profile_dict("julia"))
        self.assertEqual(
            row["exact_api"],
            [
                "DifferentialEquations.ODEProblem",
                "DifferentialEquations.solve",
                "DifferentialEquations.Tsit5",
            ],
        )
        self.assertEqual(row["runtime"]["julia_version"], JULIA_VERSION_PIN)
        self.assertEqual(
            row["runtime"]["package_version"],
            DIFFERENTIALEQUATIONS_VERSION_PIN,
        )
        self.assertEqual(row["runtime"]["active_project"], str(project_path))
        self.assertEqual(row["runtime"]["load_path"], STRICT_LOAD_PATH)
        self.assertEqual(row["runtime_pin"], runtime_profile_dict("julia"))
        self.assertFalse(row["executable_sha256_is_policy_input"])
        self.assertEqual(row["command"], packet_broker._command("julia_diffeq")[0])
        self.assertEqual(row["command"][1], "--startup-file=no")
        self.assertEqual(
            digest(Path(row["executable_resolved_path"])),
            row["executable_sha256"],
        )
        self.assertEqual(row["worker_source_sha256"], WORKER_SHA256["julia"])
        self.assertNotEqual(row["worker_pid"], os.getpid())
        self.assertNotIn("execution_binding", row)

        transport = {
            "schema": INPUT_SCHEMA,
            "engine_id": "julia_diffeq",
            "case": case,
        }
        self.assertEqual(
            row["input_sha256"],
            hashlib.sha256(canonical_json(transport)).hexdigest(),
        )
        witness = {
            "schema": "constraintbox.external-engine-witness.v1",
            "engine_id": "julia_diffeq",
            "exact_api": EXACT_APIS["julia_diffeq"],
            "observed": row["observed"],
            "runtime": row["runtime"],
            "pid": row["worker_pid"],
        }
        witness_bytes = canonical_json(witness)
        self.assertEqual(
            row["output_sha256"],
            hashlib.sha256(witness_bytes).hexdigest(),
        )
        self.assertRegex(row["stdout_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            row["stderr_sha256"], hashlib.sha256(b"").hexdigest()
        )
        self.assertEqual(
            set(row["controls"]),
            {"positive", "targeted_negative", "boundary", "strict_carrier"},
        )
        self.assertTrue(all(row["controls"].values()))

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

    def test_challenge_case_tamper_is_rejected_after_rehash(self) -> None:
        tampered = copy.deepcopy(self.first_capability_receipt)
        tampered["challenge_case"]["rate"] -= 0.125
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
        row["observed"]["terminal"] = 0.0
        forged_witness = {
            "schema": "constraintbox.external-engine-witness.v1",
            "engine_id": "julia_diffeq",
            "exact_api": row["exact_api"],
            "observed": row["observed"],
            "runtime": row["runtime"],
            "pid": row["worker_pid"],
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
        tampered["row"]["controls"]["strict_carrier"] = False
        tampered["row"]["controller_evaluation"]["controls"][
            "strict_carrier"
        ] = False
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
        case = receipt["challenge_case"]
        wrong_terminal = float(case["initial"]) * pow(
            2.718281828459045,
            float(case["wrong_rate"]) * float(case["duration"]),
        )
        wrong_witness = {
            "schema": "constraintbox.external-engine-witness.v1",
            "engine_id": "julia_diffeq",
            "exact_api": EXACT_APIS["julia_diffeq"],
            "observed": {
                "terminal": wrong_terminal,
                "boundary_terminal": row["observed"]["boundary_terminal"],
            },
            "runtime": row["runtime"],
            "pid": os.getpid() + 10_000,
        }
        fixture, _canonical, _fixture_sha256 = (
            ExternalEnginePacketBroker()._load_fixture()
        )
        challenged_fixture = {**fixture, "julia": case}

        evaluation = evaluate_worker_output(
            "julia_diffeq",
            challenged_fixture,
            wrong_witness,
            julia_project=ExternalEnginePacketBroker().julia_project,
            controller_pid=os.getpid(),
        )

        self.assertFalse(evaluation["controls"]["positive"])
        self.assertFalse(evaluation["controls"]["targeted_negative"])
        self.assertTrue(evaluation["controls"]["boundary"])
        self.assertTrue(evaluation["controls"]["strict_carrier"])
        self.assertEqual(evaluation["errors"], [])

    def test_substituted_or_missing_diffeq_api_cannot_pass(self) -> None:
        binding = self.first_binding
        packet_broker = ExternalEnginePacketBroker()
        project_path = str((packet_broker.julia_project / "Project.toml").resolve())

        def substituted_run(
            command: list[str],
            **kwargs: object,
        ) -> subprocess.CompletedProcess[bytes]:
            transport = parse_json_object(kwargs["input"])
            case = transport["case"]
            terminal = float(case["initial"]) * pow(
                2.718281828459045,
                float(case["rate"]) * float(case["duration"]),
            )
            boundary_terminal = float(case["boundary_initial"]) * pow(
                2.718281828459045,
                float(case["boundary_rate"])
                * float(case["boundary_duration"]),
            )
            witness = {
                "schema": "constraintbox.external-engine-witness.v1",
                "engine_id": "julia_diffeq",
                "exact_api": ["DifferentialEquations.Euler"],
                "observed": {
                    "terminal": terminal,
                    "boundary_terminal": boundary_terminal,
                },
                "runtime": {
                    "julia_version": JULIA_VERSION_PIN,
                    "package_version": DIFFERENTIALEQUATIONS_VERSION_PIN,
                    "active_project": project_path,
                    "load_path": STRICT_LOAD_PATH,
                },
                "pid": os.getpid() + 20_000,
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
            substituted = JuliaDifferentialEquationsCapabilityBroker().run(binding)
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
            witness = {
                "schema": "constraintbox.external-engine-unavailable.v1",
                "engine_id": "julia_diffeq",
                "exact_api": EXACT_APIS["julia_diffeq"],
                "reason": "DifferentialEquations.Tsit5 unavailable",
                "pid": os.getpid() + 30_000,
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
            unavailable = JuliaDifferentialEquationsCapabilityBroker().run(binding)
        self.assertEqual(unavailable["status"], "PARKED")
        self.assertEqual(unavailable["reason"], "exact_function_unavailable")

    def test_alternate_and_missing_runtime_never_pass(self) -> None:
        alternate = Path("/bin/sh")
        self.assertTrue(alternate.is_file())
        alternate_receipt = JuliaDifferentialEquationsCapabilityBroker(
            ExternalEnginePacketBroker(
                julia_executable=alternate,
                timeout_seconds=1.0,
            )
        ).run(self.first_binding)
        self.assertEqual(alternate_receipt["status"], "FAIL")
        self.assertEqual(
            alternate_receipt["reason"], "runtime_selection_override_rejected"
        )

        missing = Path("/private/tmp/constraintbox-no-such-julia-runtime")
        missing_receipt = JuliaDifferentialEquationsCapabilityBroker(
            ExternalEnginePacketBroker(
                julia_executable=missing,
                timeout_seconds=1.0,
            )
        ).run(self.first_binding)
        self.assertEqual(missing_receipt["status"], "FAIL")
        self.assertEqual(
            missing_receipt["reason"], "runtime_selection_override_rejected"
        )

    def test_existing_run_directory_is_rejected_before_execution(self) -> None:
        existing = self.root / "already-exists"
        existing.mkdir()

        with self.assertRaisesRegex(
            ExternalJuliaCapabilityFlowError,
            "run directory must be new",
        ):
            run_julia_capability_flow(
                request_id="existing-run",
                run_root=existing,
            )

    def test_request_cannot_select_controller_owned_mechanism(self) -> None:
        signature = inspect.signature(run_julia_capability_flow)
        self.assertEqual(list(signature.parameters), ["request_id", "run_root"])
        for parameter in signature.parameters.values():
            self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)

        forbidden = {
            "executable": "/bin/sh",
            "fixture": "/tmp/fixture.json",
            "tolerance": 1.0,
            "seed": "0" * 64,
            "transition": "RELEASED",
        }
        for field, value in forbidden.items():
            with self.subTest(field=field), self.assertRaises(TypeError):
                run_julia_capability_flow(
                    request_id="request-authority",
                    run_root=self.root / f"forbidden-{field}",
                    **{field: value},
                )

    def test_live_dependency_rebinding_cannot_reach_eligibility(self) -> None:
        with mock.patch(
            "constraintbox.external_julia_capability_flow."
            "JuliaDifferentialEquationsCapabilityBroker",
            object(),
        ):
            with self.assertRaises(ExternalJuliaCapabilityFlowError):
                run_julia_capability_flow(
                    request_id="dependency-drift",
                    run_root=self.root / "dependency-drift",
                )

    def test_raw_runtime_rejects_binding_for_another_run_and_policy(self) -> None:
        runtime = capability_flow_module._build_julia_capability_flow(
            run_id="actual-julia-capability-runtime",
            ledger_path=self.root / "forged-binding-events.jsonl",
        )
        forged = JuliaCapabilityBinding(
            capability_id=CAPABILITY_ID,
            run_id="different-julia-capability-runtime",
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
        self.assertEqual(
            result["kernel_membership"],
            "EXTERNAL_NOT_CB_KERNEL",
        )
        self.assertEqual(result["claim_ceiling"], CAPABILITY_CLAIM_CEILING)
        self.assertEqual(receipt["claim_ceiling"], CAPABILITY_CLAIM_CEILING)
        self.assertEqual(receipt["row"]["claim_ceiling"], EXTERNAL_BOUNDARY)
        for forbidden in (
            "Julia readiness",
            "sim-stack readiness",
            "release",
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
