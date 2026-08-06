from __future__ import annotations

import copy
import hashlib
import inspect
import tempfile
import unittest
from pathlib import Path

from constraintbox.capability_suite import _validate_component_result
from constraintbox.external_engine_packet import PACKET_SCHEMA, validate_pass_receipt
from constraintbox.external_packet_integration_capability import (
    CAPABILITY_CLAIM_CEILING,
    CAPABILITY_ID,
    CAPABILITY_SCHEMA,
    PacketIntegrationBinding,
    packet_integration_binding_from_dict,
    validate_packet_integration_capability_receipt,
)
from constraintbox.external_packet_integration_capability_flow import (
    CAPABILITY_RECEIPT_NAME,
    FLOW_LEDGER_NAME,
    FLOW_RECEIPT_NAME,
    ExternalPacketIntegrationCapabilityFlowError,
    run_basic_packet_cross_engine_capability_flow,
)
from constraintbox.intake import canonical_json, parse_json_object
from constraintbox.mini_levos import verify_flow_receipt


RESULT_FIELDS = {
    "schema",
    "capability_id",
    "request_id",
    "request_sha256",
    "run_id",
    "flow_policy_sha256",
    "disposition",
    "reason",
    "capability_receipt_sha256",
    "flow_receipt_sha256",
    "artifacts",
    "external_system",
    "kernel_membership",
    "release_allowed",
    "engine_readiness_claim",
    "cr_truth_claim",
    "promotion_allowed",
    "claim_ceiling",
}


def _receipt_root(receipt: dict[str, object]) -> str:
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    return hashlib.sha256(canonical_json(body)).hexdigest()


class ExternalPacketIntegrationCapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary_directory = tempfile.TemporaryDirectory()
        cls.root = Path(cls._temporary_directory.name).resolve()
        cls.result = run_basic_packet_cross_engine_capability_flow(
            request_id="packet-cross-engine-real",
            run_root=cls.root / "real",
        )
        cls.capability_receipt = parse_json_object(
            Path(cls.result["artifacts"]["capability_receipt"]).read_bytes()
        )
        cls.flow_receipt = parse_json_object(
            Path(cls.result["artifacts"]["flow_receipt"]).read_bytes()
        )
        cls.binding = packet_integration_binding_from_dict(
            cls.capability_receipt["binding"]
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary_directory.cleanup()

    def test_real_broker_runs_fixed_cross_engine_packet_through_two_nodes(self) -> None:
        self.assertEqual(set(self.result), RESULT_FIELDS)
        self.assertEqual(self.result["capability_id"], CAPABILITY_ID)
        self.assertIs(
            _validate_component_result(
                self.result,
                capability_id=CAPABILITY_ID,
                request_id="packet-cross-engine-real",
                run_root=self.root / "real",
            ),
            self.result,
        )
        self.assertEqual(self.result["disposition"], "ELIGIBLE")
        self.assertEqual(
            self.result["reason"], "legacy_packet_pass_receipt_validated"
        )
        self.assertEqual(self.capability_receipt["schema"], CAPABILITY_SCHEMA)
        self.assertEqual(self.capability_receipt["status"], "PASS")
        self.assertEqual(
            validate_packet_integration_capability_receipt(
                self.capability_receipt,
                expected_binding=self.binding,
                expected_receipt_sha256=self.capability_receipt["receipt_sha256"],
            ),
            (),
        )
        packet = self.capability_receipt["packet_receipt"]
        self.assertEqual(packet["schema"], PACKET_SCHEMA)
        self.assertEqual(packet["status"], "PASS")
        self.assertEqual(validate_pass_receipt(packet), ())
        self.assertEqual(
            {row["engine_id"] for row in packet["rows"]},
            {
                "jax_autodiff",
                "pytorch_jacobian",
                "pysindy_identification",
                "julia_diffeq",
            },
        )
        self.assertEqual(packet["integration"]["status"], "PASS")
        self.assertEqual(
            packet["integration"]["reason"], "pysindy_artifact_consumed_by_julia"
        )
        self.assertEqual(self.flow_receipt["terminal"], "ELIGIBLE")
        self.assertEqual(self.flow_receipt["steps"], 2)
        self.assertEqual(
            [node["node_id"] for node in self.flow_receipt["policy"]["nodes"]],
            ["basic-packet-cross-engine-tool", "basic-packet-cross-engine-gate"],
        )
        ledger_rows = [
            parse_json_object(line.encode("utf-8"))["record"]
            for line in Path(self.result["artifacts"]["flow_ledger"])
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertEqual(
            [
                (row["node_id"], row["typed_signal"], row["controller_selected_next"])
                for row in ledger_rows
            ],
            [
                (
                    "basic-packet-cross-engine-tool",
                    "OBSERVED",
                    "basic-packet-cross-engine-gate",
                ),
                ("basic-packet-cross-engine-gate", "PASS", "ELIGIBLE"),
            ],
        )
        valid, reason = verify_flow_receipt(
            self.flow_receipt,
            expected_run_id=self.result["run_id"],
            expected_policy_sha256=self.result["flow_policy_sha256"],
            expected_ledger_path=Path(self.result["artifacts"]["flow_ledger"]),
            expected_retained_head_sha256=Path(
                self.result["artifacts"]["flow_ledger_head"]
            ).read_text(encoding="utf-8").strip(),
            expected_receipt_sha256=self.result["flow_receipt_sha256"],
        )
        self.assertTrue(valid, reason)

    def test_receipt_binds_request_policy_sources_and_immutable_artifacts(self) -> None:
        receipt = self.capability_receipt
        immutable = receipt["immutable_artifacts"]
        self.assertEqual(
            set(immutable),
            {
                "capability_source",
                "packet_controller",
                "packet_fixture",
                "python_worker",
                "julia_worker",
                "julia_project",
            },
        )
        for artifact in immutable.values():
            path = Path(artifact["path"])
            self.assertTrue(path.is_file())
            self.assertEqual(
                artifact["sha256"], hashlib.sha256(path.read_bytes()).hexdigest()
            )
        self.assertEqual(receipt["binding"]["run_id"], self.result["run_id"])
        self.assertEqual(
            receipt["binding"]["request_sha256"], self.result["request_sha256"]
        )
        self.assertEqual(
            receipt["binding"]["flow_policy_sha256"],
            self.result["flow_policy_sha256"],
        )
        self.assertIn("legacy fixed-fixture", CAPABILITY_CLAIM_CEILING)
        self.assertIn("JSON handoff is a legacy diagnostic", CAPABILITY_CLAIM_CEILING)
        self.assertIn("not a scientific DLPack bridge", CAPABILITY_CLAIM_CEILING)
        for field in (
            "release_allowed",
            "engine_readiness_claim",
            "cr_truth_claim",
            "promotion_allowed",
        ):
            self.assertIs(self.result[field], False)
            self.assertIs(receipt[field], False)

    def test_tampering_or_rebinding_the_packet_receipt_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.capability_receipt)
        packet = tampered["packet_receipt"]
        packet["reason"] = "substituted-packet-reason"
        tampered["packet_receipt_sha256"] = hashlib.sha256(
            canonical_json(packet)
        ).hexdigest()
        tampered["receipt_sha256"] = _receipt_root(tampered)
        errors = validate_packet_integration_capability_receipt(
            tampered,
            expected_binding=self.binding,
            expected_receipt_sha256=tampered["receipt_sha256"],
        )
        self.assertTrue(errors)
        self.assertTrue(any(error.startswith("$.packet_receipt:") for error in errors))

        wrong_binding = PacketIntegrationBinding(
            capability_id=CAPABILITY_ID,
            run_id="other-packet-run",
            flow_policy_sha256=self.binding.flow_policy_sha256,
            request_sha256=self.binding.request_sha256,
            step_id=self.binding.step_id,
        )
        copied_errors = validate_packet_integration_capability_receipt(
            self.capability_receipt,
            expected_binding=wrong_binding,
            expected_receipt_sha256=self.capability_receipt["receipt_sha256"],
        )
        self.assertTrue(copied_errors)
        self.assertTrue(any(error.startswith("$.binding:") for error in copied_errors))

    def test_public_entrypoint_has_no_mechanism_or_claim_overrides(self) -> None:
        signature = inspect.signature(run_basic_packet_cross_engine_capability_flow)
        self.assertEqual(list(signature.parameters), ["request_id", "run_root"])
        for parameter in signature.parameters.values():
            self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(TypeError):
                run_basic_packet_cross_engine_capability_flow(
                    request_id="forbidden-override",
                    run_root=Path(directory) / "new-run",
                    executable="/tmp/untrusted-runtime",
                )

    def test_existing_run_directory_is_rejected_before_workloads_start(self) -> None:
        existing = self.root / "already-exists"
        existing.mkdir()
        with self.assertRaises(ExternalPacketIntegrationCapabilityFlowError):
            run_basic_packet_cross_engine_capability_flow(
                request_id="existing-run", run_root=existing
            )

        self.assertEqual(
            Path(self.result["artifacts"]["capability_receipt"]).name,
            CAPABILITY_RECEIPT_NAME,
        )
        self.assertEqual(
            Path(self.result["artifacts"]["flow_receipt"]).name,
            FLOW_RECEIPT_NAME,
        )
        self.assertEqual(
            Path(self.result["artifacts"]["flow_ledger"]).name,
            FLOW_LEDGER_NAME,
        )


if __name__ == "__main__":
    unittest.main()
