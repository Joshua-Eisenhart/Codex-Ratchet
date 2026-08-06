from __future__ import annotations

import copy
import hashlib
import inspect
import os
import tempfile
import unittest
from pathlib import Path

import constraintbox.external_pysindy_capability as capability_module
from constraintbox.external_pysindy_capability import (
    CAPABILITY_CLAIM_CEILING,
    CAPABILITY_ID,
    CAPABILITY_SCHEMA,
    EXACT_APIS,
    PYSINDY_RUNTIME_REQUIREMENTS,
    CapabilityBinding,
    capability_binding_from_dict,
    derive_pysindy_challenge_case,
    validate_pysindy_capability_receipt,
)
from constraintbox.external_runtime_profiles import runtime_profile_dict
from constraintbox.external_pysindy_capability_flow import (
    CAPABILITY_RECEIPT_NAME,
    FLOW_LEDGER_NAME,
    FLOW_RECEIPT_NAME,
    ExternalPySINDyCapabilityFlowError,
    run_pysindy_capability_flow,
)
from constraintbox.intake import canonical_json, parse_json_object


def _recompute_receipt_root(receipt: dict[str, object]) -> str:
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    digest = hashlib.sha256(canonical_json(body)).hexdigest()
    receipt["receipt_sha256"] = digest
    return digest


def _binding(receipt: dict[str, object]) -> CapabilityBinding:
    return capability_binding_from_dict(receipt["binding"])


class ExternalPySINDyCapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary_directory = tempfile.TemporaryDirectory()
        cls.root = Path(cls._temporary_directory.name).resolve()
        cls.first_result = run_pysindy_capability_flow(
            request_id="pysindy-fresh-a",
            run_root=cls.root / "pysindy-fresh-a",
        )
        cls.second_result = run_pysindy_capability_flow(
            request_id="pysindy-fresh-b",
            run_root=cls.root / "pysindy-fresh-b",
        )
        cls.first_receipt = parse_json_object(
            Path(cls.first_result["artifacts"]["capability_receipt"]).read_bytes()
        )
        cls.second_receipt = parse_json_object(
            Path(cls.second_result["artifacts"]["capability_receipt"]).read_bytes()
        )
        cls.first_flow = parse_json_object(
            Path(cls.first_result["artifacts"]["flow_receipt"]).read_bytes()
        )
        cls.first_binding = _binding(cls.first_receipt)
        cls.second_binding = _binding(cls.second_receipt)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary_directory.cleanup()

    def _validate(
        self,
        receipt: dict[str, object],
        *,
        binding: CapabilityBinding | None = None,
        receipt_sha256: str | None = None,
    ) -> tuple[str, ...]:
        return validate_pysindy_capability_receipt(
            receipt,
            expected_binding=binding or self.first_binding,
            expected_receipt_sha256=(
                receipt_sha256
                if receipt_sha256 is not None
                else receipt["receipt_sha256"]
            ),
        )

    def test_challenge_derivation_is_fixed_per_seed_and_changes_per_seed(self) -> None:
        first = derive_pysindy_challenge_case("00" * 32)
        second = derive_pysindy_challenge_case("00" * 32)

        self.assertEqual(first, second)
        self.assertNotEqual(first, derive_pysindy_challenge_case("01" * 32))
        self.assertEqual(len(first["train_states"]), 6)
        self.assertEqual(len(first["heldout_states"]), 3)
        self.assertEqual(first["boundary_state"], 0.0)
        self.assertNotEqual(first["wrong_coefficients"], [first["bias"], first["rate"]])

    def test_fresh_real_flow_runs_real_two_node_external_operation(self) -> None:
        receipt = self.first_receipt
        row = receipt["row"]
        flow = self.first_flow

        self.assertEqual(self.first_result["disposition"], "ELIGIBLE")
        self.assertEqual(receipt["schema"], CAPABILITY_SCHEMA)
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(receipt["reason"], "exact_operation_controls_passed")
        self.assertEqual(self._validate(receipt), ())
        self.assertEqual(flow["terminal"], "ELIGIBLE")
        self.assertEqual(flow["steps"], 2)
        self.assertEqual(
            flow["completed_nodes"],
            ["pysindy-capability-gate", "pysindy-capability-tool"],
        )
        self.assertEqual(row["exact_api"], list(EXACT_APIS))
        self.assertEqual(
            row["controls"],
            {"positive": True, "targeted_negative": True, "boundary": True},
        )
        self.assertNotEqual(row["worker_pid"], os.getpid())
        self.assertTrue(row["runtime"]["pysindy_version"].startswith("2.1."))
        self.assertTrue(row["runtime"]["numpy_version"].startswith("2.3."))

    def test_fresh_controller_challenge_and_binding_cannot_be_reused(self) -> None:
        self.assertNotEqual(
            self.first_receipt["binding"]["challenge_seed_hex"],
            self.second_receipt["binding"]["challenge_seed_hex"],
        )
        self.assertNotEqual(
            self.first_receipt["challenge_case_sha256"],
            self.second_receipt["challenge_case_sha256"],
        )
        errors = self._validate(
            self.first_receipt,
            binding=self.second_binding,
            receipt_sha256=self.first_receipt["receipt_sha256"],
        )
        self.assertTrue(errors)
        self.assertTrue(any("$.binding" in error for error in errors))
        self.assertTrue(any("$.challenge_case" in error for error in errors))

    def test_source_runtime_profile_and_claim_ceiling_remain_external(self) -> None:
        receipt = self.first_receipt
        row = receipt["row"]

        self.assertEqual(receipt["kernel_membership"], "EXTERNAL_NOT_CB_KERNEL")
        self.assertTrue(receipt["external_system"])
        self.assertEqual(receipt["runtime_pin"], runtime_profile_dict("python"))
        self.assertEqual(row["runtime_pin"], runtime_profile_dict("python"))
        self.assertEqual(Path(row["command"][0]).resolve(), Path(__import__("sys").executable).resolve())
        self.assertEqual(row["command"][1], "-B")
        self.assertEqual(row["worker_source_sha256"], receipt["capability_source_sha256"])
        self.assertEqual(
            receipt["capability_source_sha256"],
            hashlib.sha256(Path(capability_module.__file__).read_bytes()).hexdigest(),
        )
        artifacts = receipt["pysindy_sources_after"]["artifacts"]
        self.assertEqual(len(artifacts), len(PYSINDY_RUNTIME_REQUIREMENTS))
        self.assertEqual(
            [artifact["distribution"] for artifact in artifacts],
            ["pysindy", "numpy"],
        )
        for artifact in artifacts:
            self.assertFalse(artifact["artifact_sha256_is_policy_input"])
            self.assertTrue(artifact["observed"])
            self.assertTrue(artifact["module_origins"][0]["matches_distribution"])
        for field in (
            "release_allowed",
            "engine_readiness_claim",
            "cr_truth_claim",
            "promotion_allowed",
        ):
            self.assertIs(self.first_result[field], False)
            self.assertIs(receipt[field], False)
            self.assertIs(row[field], False)
        self.assertIn("not PySINDy readiness", CAPABILITY_CLAIM_CEILING)
        self.assertIn("not sim-stack readiness", CAPABILITY_CLAIM_CEILING)
        self.assertIn("not CR truth", CAPABILITY_CLAIM_CEILING)
        self.assertIn("not scientific proof", CAPABILITY_CLAIM_CEILING)
        self.assertIn("not canonical promotion", CAPABILITY_CLAIM_CEILING)
        self.assertEqual(
            Path(self.first_result["artifacts"]["capability_receipt"]).name,
            CAPABILITY_RECEIPT_NAME,
        )
        self.assertEqual(
            Path(self.first_result["artifacts"]["flow_receipt"]).name,
            FLOW_RECEIPT_NAME,
        )
        self.assertEqual(
            Path(self.first_result["artifacts"]["flow_ledger"]).name,
            FLOW_LEDGER_NAME,
        )

    def test_forged_observed_values_fail_controller_recomputation(self) -> None:
        tampered = copy.deepcopy(self.first_receipt)
        row = tampered["row"]
        row["observed"]["coefficients"] = tampered["challenge_case"][
            "wrong_coefficients"
        ]
        witness = {
            "schema": "constraintbox.external-pysindy-worker-witness.v1",
            "capability_id": CAPABILITY_ID,
            "exact_api": row["exact_api"],
            "execution_binding": row["execution_binding"],
            "capability_source_sha256": row["worker_source_sha256"],
            "runtime_pin": row["runtime_pin"],
            "observed": row["observed"],
            "runtime": row["runtime"],
            "pid": row["worker_pid"],
        }
        witness_bytes = canonical_json(witness)
        row["output_sha256"] = hashlib.sha256(witness_bytes).hexdigest()
        row["stdout_sha256"] = hashlib.sha256(witness_bytes + b"\n").hexdigest()
        root = _recompute_receipt_root(tampered)

        errors = self._validate(tampered, receipt_sha256=root)

        self.assertTrue(errors)
        self.assertTrue(
            any(
                "$.row.controller_evaluation" in error or "$.row.controls" in error
                for error in errors
            )
        )

    def test_request_cannot_select_controller_owned_mechanism(self) -> None:
        signature = inspect.signature(run_pysindy_capability_flow)
        self.assertEqual(list(signature.parameters), ["request_id", "run_root"])
        for parameter in signature.parameters.values():
            self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
        forbidden = {
            "executable": "/usr/bin/python3",
            "source": "/tmp/pysindy.py",
            "tolerance": 1.0,
            "seed": "0" * 64,
            "transition": "RELEASED",
        }
        for field, value in forbidden.items():
            with self.subTest(field=field), self.assertRaises(TypeError):
                run_pysindy_capability_flow(
                    request_id="request-authority",
                    run_root=self.root / f"forbidden-{field}",
                    **{field: value},
                )

    def test_existing_run_directory_is_rejected_before_operation(self) -> None:
        existing = self.root / "already-exists"
        existing.mkdir()

        with self.assertRaisesRegex(
            ExternalPySINDyCapabilityFlowError,
            "run directory must be new",
        ):
            run_pysindy_capability_flow(
                request_id="existing-run",
                run_root=existing,
            )


if __name__ == "__main__":
    unittest.main()
