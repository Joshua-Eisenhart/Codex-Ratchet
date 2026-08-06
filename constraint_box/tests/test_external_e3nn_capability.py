from __future__ import annotations

import copy
import hashlib
import inspect
import math
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import constraintbox.external_e3nn_capability as raw
from constraintbox.external_e3nn_capability import (
    CAPABILITY_CLAIM_CEILING,
    CAPABILITY_ID,
    E3NN_WIGNER_PROFILE,
    EXACT_APIS,
    RUNTIME_POLICY,
    E3nnCapabilityBinding,
    derive_e3nn_challenge_case,
    e3nn_capability_binding_from_dict,
    validate_e3nn_capability_receipt,
)
from constraintbox.external_e3nn_capability_flow import (
    CAPABILITY_RECEIPT_NAME,
    FLOW_LEDGER_NAME,
    FLOW_RECEIPT_NAME,
    ExternalE3nnCapabilityFlowError,
    run_e3nn_capability_flow,
)
from constraintbox.external_runtime_profiles import selected_runtime_executable
from constraintbox.intake import canonical_json, parse_json_object


def _recompute_receipt_root(receipt: dict[str, object]) -> str:
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    digest = hashlib.sha256(canonical_json(body)).hexdigest()
    receipt["receipt_sha256"] = digest
    return digest


def _binding(receipt: dict[str, object]) -> E3nnCapabilityBinding:
    return e3nn_capability_binding_from_dict(receipt["binding"])


def _transport(binding: E3nnCapabilityBinding) -> dict[str, object]:
    source = Path(raw.__file__).resolve()
    return {
        "schema": raw.WORKER_TRANSPORT_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "exact_api": list(EXACT_APIS),
        "execution_binding": binding.to_dict(),
        "challenge_case": derive_e3nn_challenge_case(binding.challenge_seed_hex),
        "capability_source_path": str(source),
        "capability_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "runtime_pin": RUNTIME_POLICY,
    }


class ExternalE3nnCapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary_directory = tempfile.TemporaryDirectory()
        cls.root = Path(cls._temporary_directory.name).resolve()
        cls.first_result = run_e3nn_capability_flow(
            request_id="e3nn-fresh-a",
            run_root=cls.root / "e3nn-fresh-a",
        )
        cls.second_result = run_e3nn_capability_flow(
            request_id="e3nn-fresh-b",
            run_root=cls.root / "e3nn-fresh-b",
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
        binding: E3nnCapabilityBinding | None = None,
        receipt_sha256: str | None = None,
    ) -> tuple[str, ...]:
        return validate_e3nn_capability_receipt(
            receipt,
            expected_binding=binding or self.first_binding,
            expected_receipt_sha256=(
                receipt_sha256
                if receipt_sha256 is not None
                else receipt["receipt_sha256"]
            ),
        )

    def test_challenge_derivation_is_fixed_per_seed_with_both_triples(self) -> None:
        first = derive_e3nn_challenge_case("00" * 32)
        self.assertEqual(first, derive_e3nn_challenge_case("00" * 32))
        self.assertNotEqual(first, derive_e3nn_challenge_case("01" * 32))
        self.assertEqual(first["triples"], [[1, 1, 0], [1, 1, 2]])
        self.assertEqual(first["boundary_triple"], [1, 1, 2])
        self.assertTrue(1.25 <= first["scale"] <= 1.75)

    def test_fresh_real_flow_runs_separate_e3nn_operation_and_replays(self) -> None:
        receipt = self.first_receipt
        row = receipt["row"]
        flow = self.first_flow

        self.assertEqual(self.first_result["disposition"], "ELIGIBLE")
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(receipt["reason"], "exact_operation_controls_passed")
        self.assertEqual(self._validate(receipt), ())
        self.assertEqual(
            validate_e3nn_capability_receipt(
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
            {"e3nn-capability-tool", "e3nn-capability-gate"},
        )
        self.assertEqual(row["exact_api"], ["e3nn.o3.wigner_3j"])
        self.assertEqual(
            row["controls"],
            {"positive": True, "targeted_negative": True, "boundary": True},
        )
        self.assertNotEqual(row["worker_pid"], os.getpid())
        self.assertTrue(
            raw._runtime_witness_matches_profile(E3NN_WIGNER_PROFILE, row["runtime"])
        )
        observed = row["observed"]
        diagonal = 1.0 / math.sqrt(3.0)
        for index in range(3):
            self.assertAlmostEqual(
                observed["wigner_110"][index][index][0], diagonal, places=10
            )
        self.assertEqual(len(observed["wigner_112"]), 3)
        self.assertEqual(len(observed["wigner_112"][0][0]), 5)

    def test_fresh_binding_and_challenge_cannot_be_reused(self) -> None:
        self.assertNotEqual(
            self.first_receipt["binding"]["challenge_seed_hex"],
            self.second_receipt["binding"]["challenge_seed_hex"],
        )
        errors = self._validate(
            self.first_receipt,
            binding=self.second_binding,
            receipt_sha256=self.first_receipt["receipt_sha256"],
        )
        self.assertTrue(errors)
        self.assertTrue(any("$.binding" in error for error in errors))

    def test_portable_runtime_policy_and_claim_ceiling_remain_external(self) -> None:
        receipt = self.first_receipt
        row = receipt["row"]
        self.assertEqual(receipt["kernel_membership"], "EXTERNAL_NOT_CB_KERNEL")
        self.assertTrue(receipt["external_system"])
        self.assertEqual(receipt["runtime_pin"], RUNTIME_POLICY)
        self.assertEqual(row["command"][0], str(selected_runtime_executable("python")))
        self.assertEqual(row["command"][1], "-B")
        self.assertFalse(receipt["runtime_pin"]["artifact_sha256_is_policy_input"])
        for field in (
            "release_allowed",
            "engine_readiness_claim",
            "cr_truth_claim",
            "promotion_allowed",
        ):
            self.assertIs(self.first_result[field], False)
            self.assertIs(receipt[field], False)
            self.assertIs(row[field], False)
        self.assertIn("not e3nn readiness", CAPABILITY_CLAIM_CEILING)
        self.assertIn("not sim-stack readiness", CAPABILITY_CLAIM_CEILING)
        self.assertIn("not CR truth", CAPABILITY_CLAIM_CEILING)
        self.assertIn("not canonical promotion", CAPABILITY_CLAIM_CEILING)
        self.assertEqual(
            Path(self.first_result["artifacts"]["capability_receipt"]).name,
            CAPABILITY_RECEIPT_NAME,
        )
        self.assertEqual(
            Path(self.first_result["artifacts"]["flow_receipt"]).name, FLOW_RECEIPT_NAME
        )
        self.assertEqual(
            Path(self.first_result["artifacts"]["flow_ledger"]).name, FLOW_LEDGER_NAME
        )
        self.assertNotIn("/Users/", Path(raw.__file__).read_text())

    def test_forged_diagonal_fails_controller_recomputation(self) -> None:
        tampered = copy.deepcopy(self.first_receipt)
        row = tampered["row"]
        for index in range(3):
            row["observed"]["wigner_110"][index][index][0] = tampered["challenge_case"][
                "wrong_diagonal"
            ]
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

    def test_operation_poison_proves_worker_calls_wigner_3j(self) -> None:
        from e3nn import o3

        with mock.patch.object(
            o3, "wigner_3j", side_effect=RuntimeError("poisoned-wigner")
        ):
            with self.assertRaisesRegex(RuntimeError, "poisoned-wigner"):
                raw._worker_witness(E3NN_WIGNER_PROFILE, _transport(self.first_binding))

    def test_request_cannot_select_controller_owned_mechanism(self) -> None:
        signature = inspect.signature(run_e3nn_capability_flow)
        self.assertEqual(list(signature.parameters), ["request_id", "run_root"])
        for parameter in signature.parameters.values():
            self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
        for field, value in {
            "executable": "/usr/bin/python3",
            "source": "/tmp/e3nn.py",
            "tolerance": 1.0,
            "seed": "0" * 64,
            "transition": "RELEASED",
        }.items():
            with self.subTest(field=field), self.assertRaises(TypeError):
                run_e3nn_capability_flow(
                    request_id="request-authority",
                    run_root=self.root / f"forbidden-{field}",
                    **{field: value},
                )

    def test_existing_run_directory_is_rejected_before_operation(self) -> None:
        existing = self.root / "already-exists"
        existing.mkdir()
        with self.assertRaisesRegex(
            ExternalE3nnCapabilityFlowError,
            "run directory must be new",
        ):
            run_e3nn_capability_flow(request_id="existing-run", run_root=existing)


if __name__ == "__main__":
    unittest.main()
