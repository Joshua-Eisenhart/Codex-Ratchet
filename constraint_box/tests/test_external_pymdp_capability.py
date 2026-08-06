from __future__ import annotations

import copy
import hashlib
import inspect
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import constraintbox.external_s3_capability as raw
from constraintbox.external_pymdp_capability import (
    CAPABILITY_CLAIM_CEILING,
    CAPABILITY_ID,
    CAPABILITY_SCHEMA,
    EXACT_APIS,
    PYMDP_PROFILE,
    RUNTIME_POLICY,
    PyMDPCapabilityBinding,
    derive_pymdp_challenge_case,
    evaluate_pymdp_output,
    pymdp_capability_binding_from_dict,
    validate_pymdp_capability_receipt,
)
from constraintbox.external_runtime_profiles import selected_runtime_executable
from constraintbox.external_pymdp_capability_flow import (
    CAPABILITY_RECEIPT_NAME,
    FLOW_LEDGER_NAME,
    FLOW_RECEIPT_NAME,
    ExternalPyMDPCapabilityFlowError,
    run_pymdp_capability_flow,
)
from constraintbox.intake import canonical_json, parse_json_object


def _recompute_receipt_root(receipt: dict[str, object]) -> str:
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    digest = hashlib.sha256(canonical_json(body)).hexdigest()
    receipt["receipt_sha256"] = digest
    return digest


def _binding(receipt: dict[str, object]) -> PyMDPCapabilityBinding:
    return pymdp_capability_binding_from_dict(receipt["binding"])


def _transport(binding: PyMDPCapabilityBinding) -> dict[str, object]:
    source = Path(raw.__file__).resolve()
    return {
        "schema": raw.WORKER_TRANSPORT_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "exact_api": list(EXACT_APIS),
        "execution_binding": binding.to_dict(),
        "challenge_case": derive_pymdp_challenge_case(binding.challenge_seed_hex),
        "capability_source_path": str(source),
        "capability_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "runtime_pin": RUNTIME_POLICY,
    }


class ExternalPyMDPCapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary_directory = tempfile.TemporaryDirectory()
        cls.root = Path(cls._temporary_directory.name).resolve()
        cls.first_result = run_pymdp_capability_flow(
            request_id="pymdp-fresh-a",
            run_root=cls.root / "pymdp-fresh-a",
        )
        cls.second_result = run_pymdp_capability_flow(
            request_id="pymdp-fresh-b",
            run_root=cls.root / "pymdp-fresh-b",
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
        binding: PyMDPCapabilityBinding | None = None,
        receipt_sha256: str | None = None,
    ) -> tuple[str, ...]:
        return validate_pymdp_capability_receipt(
            receipt,
            expected_binding=binding or self.first_binding,
            expected_receipt_sha256=(
                receipt_sha256
                if receipt_sha256 is not None
                else receipt["receipt_sha256"]
            ),
        )

    def test_challenge_derivation_is_fixed_and_has_alternate_observation_boundary(self) -> None:
        first = derive_pymdp_challenge_case("00" * 32)
        self.assertEqual(first, derive_pymdp_challenge_case("00" * 32))
        self.assertNotEqual(first, derive_pymdp_challenge_case("01" * 32))
        self.assertEqual(first["primary_observation"], 0)
        self.assertEqual(first["boundary_observation"], 1)
        self.assertEqual(len(first["preferences"]), 2)

    def test_fresh_real_flow_runs_state_and_policy_inference_and_replays(self) -> None:
        receipt = self.first_receipt
        row = receipt["row"]
        flow = self.first_flow

        self.assertEqual(self.first_result["disposition"], "ELIGIBLE")
        self.assertEqual(receipt["schema"], CAPABILITY_SCHEMA)
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(receipt["reason"], "exact_operation_controls_passed")
        self.assertEqual(self._validate(receipt), ())
        self.assertEqual(
            validate_pymdp_capability_receipt(
                self.second_receipt,
                expected_binding=self.second_binding,
                expected_receipt_sha256=self.second_receipt["receipt_sha256"],
            ),
            (),
        )
        self.assertEqual(flow["terminal"], "ELIGIBLE")
        self.assertEqual(flow["steps"], 2)
        self.assertEqual(
            set(flow["completed_nodes"]),
            {"pymdp-capability-tool", "pymdp-capability-gate"},
        )
        self.assertEqual(row["exact_api"], list(EXACT_APIS))
        self.assertEqual(
            row["controls"],
            {"positive": True, "targeted_negative": True, "boundary": True},
        )
        self.assertNotEqual(row["worker_pid"], os.getpid())
        self.assertTrue(raw._runtime_witness_matches_profile(PYMDP_PROFILE, row["runtime"]))
        self.assertNotEqual(
            row["observed"]["primary"]["posterior"],
            row["observed"]["boundary"]["posterior"],
        )

    def test_fresh_binding_and_challenge_cannot_be_reused(self) -> None:
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

    def test_portable_runtime_policy_and_claim_ceiling_remain_external(self) -> None:
        receipt = self.first_receipt
        row = receipt["row"]
        self.assertEqual(receipt["kernel_membership"], "EXTERNAL_NOT_CB_KERNEL")
        self.assertTrue(receipt["external_system"])
        self.assertEqual(receipt["runtime_pin"], RUNTIME_POLICY)
        self.assertEqual(row["runtime_pin"], RUNTIME_POLICY)
        self.assertEqual(row["command"][0], str(selected_runtime_executable("python")))
        self.assertEqual(row["command"][1], "-B")
        self.assertFalse(receipt["runtime_pin"]["artifact_sha256_is_policy_input"])
        self.assertEqual(
            receipt["capability_source_sha256"],
            hashlib.sha256(Path(raw.__file__).read_bytes()).hexdigest(),
        )
        self.assertEqual(row["worker_source_sha256"], receipt["capability_source_sha256"])
        for field in (
            "release_allowed",
            "engine_readiness_claim",
            "cr_truth_claim",
            "promotion_allowed",
        ):
            self.assertIs(self.first_result[field], False)
            self.assertIs(receipt[field], False)
            self.assertIs(row[field], False)
        self.assertIn("not PyMDP readiness", CAPABILITY_CLAIM_CEILING)
        self.assertIn("not sim-stack readiness", CAPABILITY_CLAIM_CEILING)
        self.assertIn("not CR truth", CAPABILITY_CLAIM_CEILING)
        self.assertIn("not scientific proof", CAPABILITY_CLAIM_CEILING)
        self.assertIn("not canonical promotion", CAPABILITY_CLAIM_CEILING)
        self.assertEqual(Path(self.first_result["artifacts"]["capability_receipt"]).name, CAPABILITY_RECEIPT_NAME)
        self.assertEqual(Path(self.first_result["artifacts"]["flow_receipt"]).name, FLOW_RECEIPT_NAME)
        self.assertEqual(Path(self.first_result["artifacts"]["flow_ledger"]).name, FLOW_LEDGER_NAME)
        self.assertNotIn("/Users/", Path(raw.__file__).read_text())

    def test_forged_policy_fails_controller_recomputation(self) -> None:
        tampered = copy.deepcopy(self.first_receipt)
        row = tampered["row"]
        row["observed"]["primary"]["policy"] = list(
            reversed(row["observed"]["primary"]["policy"])
        )
        witness = {
            "schema": raw.WORKER_WITNESS_SCHEMA,
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

    def test_malformed_worker_shape_is_fail_closed_without_controller_exception(self) -> None:
        evaluation = evaluate_pymdp_output(
            derive_pymdp_challenge_case("55" * 32),
            {"primary": {"policy": []}, "boundary": {}},
        )
        self.assertEqual(
            evaluation["controls"],
            {"positive": False, "targeted_negative": False, "boundary": False},
        )
        self.assertTrue(evaluation["errors"])

    def test_operation_poison_proves_worker_calls_infer_states(self) -> None:
        from pymdp.agent import Agent

        with mock.patch.object(
            Agent, "infer_states", side_effect=RuntimeError("poisoned-state-inference")
        ):
            with self.assertRaisesRegex(RuntimeError, "poisoned-state-inference"):
                raw._worker_witness(PYMDP_PROFILE, _transport(self.first_binding))

    def test_operation_poison_proves_worker_calls_infer_policies(self) -> None:
        from pymdp.agent import Agent

        with mock.patch.object(
            Agent, "infer_policies", side_effect=RuntimeError("poisoned-policy-inference")
        ):
            with self.assertRaisesRegex(RuntimeError, "poisoned-policy-inference"):
                raw._worker_witness(PYMDP_PROFILE, _transport(self.first_binding))

    def test_request_cannot_select_controller_owned_mechanism(self) -> None:
        signature = inspect.signature(run_pymdp_capability_flow)
        self.assertEqual(list(signature.parameters), ["request_id", "run_root"])
        for parameter in signature.parameters.values():
            self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
        for field, value in {
            "executable": "/usr/bin/python3",
            "source": "/tmp/pymdp.py",
            "tolerance": 1.0,
            "seed": "0" * 64,
            "transition": "RELEASED",
        }.items():
            with self.subTest(field=field), self.assertRaises(TypeError):
                run_pymdp_capability_flow(
                    request_id="request-authority",
                    run_root=self.root / f"forbidden-{field}",
                    **{field: value},
                )

    def test_existing_run_directory_is_rejected_before_operation(self) -> None:
        existing = self.root / "already-exists"
        existing.mkdir()
        with self.assertRaisesRegex(
            ExternalPyMDPCapabilityFlowError,
            "run directory must be new",
        ):
            run_pymdp_capability_flow(request_id="existing-run", run_root=existing)


if __name__ == "__main__":
    unittest.main()
