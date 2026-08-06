from __future__ import annotations

import hashlib
import inspect
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import constraintbox.external_quimb_cotengra_capability_flow as flow_module
from constraintbox.capability_suite import _REQUIRED_RESULT_FIELDS
from constraintbox.external_quimb_cotengra_capability import (
    CAPABILITY_ID,
    CLAIM_CEILING,
    STEP_ID,
    capability_binding_from_dict,
    validate_quimb_cotengra_capability_receipt,
)
from constraintbox.external_quimb_cotengra_capability_flow import (
    CAPABILITY_RECEIPT_NAME,
    FLOW_LEDGER_NAME,
    FLOW_RECEIPT_NAME,
    FLOW_RESULT_SCHEMA,
    ExternalQuimbCotengraCapabilityFlowError,
    run_quimb_cotengra_capability_flow,
)
from constraintbox.intake import parse_json_object
from constraintbox.mini_levos import verify_flow_receipt


class ExternalQuimbCotengraCapabilityFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary_directory = tempfile.TemporaryDirectory(dir="/private/tmp")
        cls.root = Path(cls._temporary_directory.name).resolve()
        cls.first_result = run_quimb_cotengra_capability_flow(
            request_id="fresh-quimb-cotengra-flow-a",
            run_root=cls.root / "fresh-a",
        )
        cls.second_result = run_quimb_cotengra_capability_flow(
            request_id="fresh-quimb-cotengra-flow-b",
            run_root=cls.root / "fresh-b",
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

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary_directory.cleanup()

    def test_fresh_real_broker_runs_in_a_fixed_two_node_minilev_flow(self) -> None:
        result = self.first_result
        flow = self.first_flow_receipt
        receipt = self.first_capability_receipt

        self.assertEqual(result["schema"], FLOW_RESULT_SCHEMA)
        self.assertEqual(result["disposition"], "ELIGIBLE")
        self.assertEqual(result["reason"], "exact_operation_controls_passed")
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(flow["terminal"], "ELIGIBLE")
        self.assertEqual(flow["steps"], 2)
        self.assertEqual(
            flow["completed_nodes"],
            ["quimb-cotengra-capability-gate", "quimb-cotengra-capability-tool"],
        )
        self.assertEqual(
            [node["node_id"] for node in flow["policy"]["nodes"]],
            ["quimb-cotengra-capability-tool", "quimb-cotengra-capability-gate"],
        )
        self.assertEqual(flow["policy"]["entry_node"], "quimb-cotengra-capability-tool")
        self.assertEqual(flow["policy"]["bounds"]["max_steps"], 2)
        self.assertEqual(flow["policy"]["bounds"]["max_retries"], 0)
        self.assertNotIn("RELEASED", flow["policy"]["terminal_nodes"])

        records = [
            parse_json_object(line.encode("utf-8"))["record"]
            for line in Path(result["artifacts"]["flow_ledger"])
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertEqual(
            [
                (record["node_id"], record["typed_signal"], record["controller_selected_next"])
                for record in records
            ],
            [
                ("quimb-cotengra-capability-tool", "OBSERVED", "quimb-cotengra-capability-gate"),
                ("quimb-cotengra-capability-gate", "PASS", "ELIGIBLE"),
            ],
        )

    def test_flow_and_external_receipts_are_independently_replayed(self) -> None:
        result = self.first_result
        flow = self.first_flow_receipt
        receipt = self.first_capability_receipt
        binding = capability_binding_from_dict(receipt["binding"])

        valid, reason = verify_flow_receipt(
            flow,
            expected_run_id=result["run_id"],
            expected_policy_sha256=result["flow_policy_sha256"],
            expected_ledger_path=Path(result["artifacts"]["flow_ledger"]),
            expected_retained_head_sha256=Path(
                result["artifacts"]["flow_ledger_head"]
            ).read_text(encoding="utf-8").strip(),
            expected_receipt_sha256=result["flow_receipt_sha256"],
        )
        self.assertTrue(valid, reason)
        self.assertEqual(
            validate_quimb_cotengra_capability_receipt(
                receipt,
                expected_binding=binding,
                expected_receipt_sha256=result["capability_receipt_sha256"],
            ),
            (),
        )
        self.assertEqual(binding.run_id, result["run_id"])
        self.assertEqual(binding.flow_policy_sha256, result["flow_policy_sha256"])
        self.assertEqual(binding.step_id, STEP_ID)

    def test_each_run_gets_a_fresh_controller_challenge_and_binding(self) -> None:
        first = self.first_capability_receipt
        second = self.second_capability_receipt

        self.assertNotEqual(first["binding"]["challenge_seed_hex"], second["binding"]["challenge_seed_hex"])
        self.assertNotEqual(first["binding_sha256"], second["binding_sha256"])
        self.assertNotEqual(self.first_result["run_id"], self.second_result["run_id"])
        self.assertNotEqual(
            first["rows"][0]["challenge_case_sha256"],
            second["rows"][0]["challenge_case_sha256"],
        )

    def test_result_exactly_has_the_common_capability_suite_shape(self) -> None:
        result = self.first_result

        self.assertEqual(set(result), _REQUIRED_RESULT_FIELDS)
        self.assertEqual(result["capability_id"], CAPABILITY_ID)
        self.assertTrue(result["request_sha256"])
        self.assertTrue(result["flow_policy_sha256"])
        self.assertTrue(result["capability_receipt_sha256"])
        self.assertTrue(result["flow_receipt_sha256"])
        self.assertEqual(
            set(result["artifacts"]),
            {"capability_receipt", "flow_receipt", "flow_ledger", "flow_ledger_head"},
        )
        self.assertEqual(Path(result["artifacts"]["capability_receipt"]).name, CAPABILITY_RECEIPT_NAME)
        self.assertEqual(Path(result["artifacts"]["flow_receipt"]).name, FLOW_RECEIPT_NAME)
        self.assertEqual(Path(result["artifacts"]["flow_ledger"]).name, FLOW_LEDGER_NAME)

    def test_pass_remains_external_non_releasing_and_non_promoting(self) -> None:
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
            flow["promotion_allowed"],
            flow["policy"]["promotion_allowed"],
        ):
            self.assertIs(value, False)
        self.assertTrue(result["external_system"])
        self.assertEqual(result["kernel_membership"], "EXTERNAL_NOT_CB_KERNEL")
        self.assertEqual(result["claim_ceiling"], CLAIM_CEILING)
        self.assertEqual(receipt["claim_ceiling"], CLAIM_CEILING)
        self.assertEqual(flow["policy"]["claim_ceiling"], CLAIM_CEILING)

    def test_public_function_only_accepts_request_id_and_run_root(self) -> None:
        signature = inspect.signature(run_quimb_cotengra_capability_flow)
        self.assertEqual(list(signature.parameters), ["request_id", "run_root"])
        for parameter in signature.parameters.values():
            self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
        for field, value in {
            "executable": "/usr/bin/python3",
            "profile": "all-engines",
            "seed": "0" * 64,
            "transition": "RELEASED",
            "release": True,
        }.items():
            with self.subTest(field=field), self.assertRaises(TypeError):
                run_quimb_cotengra_capability_flow(
                    request_id="request-authority",
                    run_root=self.root / f"forbidden-{field}",
                    **{field: value},
                )

    def test_existing_run_root_and_dependency_rebinding_are_rejected(self) -> None:
        existing = self.root / "already-exists"
        existing.mkdir()
        with self.assertRaisesRegex(
            ExternalQuimbCotengraCapabilityFlowError,
            "run directory must be new",
        ):
            run_quimb_cotengra_capability_flow(
                request_id="existing-run",
                run_root=existing,
            )

        with mock.patch.object(flow_module, "QuimbCotengraCapabilityBroker", object()):
            with self.assertRaises(ExternalQuimbCotengraCapabilityFlowError):
                run_quimb_cotengra_capability_flow(
                    request_id="dependency-drift",
                    run_root=self.root / "dependency-drift",
                )

    def test_result_request_digest_is_controller_constructed(self) -> None:
        result = self.first_result
        expected_request = {
            "schema": "constraintbox.external-capability-request.v1",
            "capability_id": CAPABILITY_ID,
            "request_id": result["request_id"],
        }
        self.assertEqual(
            result["request_sha256"],
            hashlib.sha256(
                flow_module.canonical_json(expected_request)
            ).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
