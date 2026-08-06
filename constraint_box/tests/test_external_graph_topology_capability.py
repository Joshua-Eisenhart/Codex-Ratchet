from __future__ import annotations

import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from constraintbox.capability_receipt_replay import verify_external_capability_receipt
from constraintbox.external_graph_topology_capability import (
    CAPABILITY_ID,
    EXACT_APIS,
    GraphTopologyCapabilityBinding,
    graph_topology_binding_from_dict,
    run_graph_topology_capability_flow,
    validate_graph_topology_receipt,
)
from constraintbox.intake import canonical_json, parse_json_object


class ExternalGraphTopologyCapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary_directory = tempfile.TemporaryDirectory()
        cls.root = Path(cls._temporary_directory.name)
        cls.result = run_graph_topology_capability_flow(
            request_id="graph-topology-capability-tests",
            run_root=cls.root / "profile",
        )
        cls.receipt = parse_json_object(
            Path(cls.result["artifacts"]["capability_receipt"]).read_bytes()
        )
        cls.binding = graph_topology_binding_from_dict(cls.receipt["binding"])

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary_directory.cleanup()

    def _validate(self, receipt: dict) -> tuple[str, ...]:
        return validate_graph_topology_receipt(
            receipt,
            expected_binding=self.binding,
            expected_receipt_sha256=receipt["receipt_sha256"],
        )

    def test_actual_profile_replays_and_severs_every_named_api(self) -> None:
        self.assertEqual(self.result["capability_id"], CAPABILITY_ID)
        self.assertEqual(self.result["disposition"], "ELIGIBLE")
        self.assertEqual(self.receipt["status"], "PASS")
        self.assertTrue(all(self.receipt["controls"].values()))
        self.assertEqual(set(self.receipt["severance"]), set(EXACT_APIS))
        self.assertEqual(
            self.receipt["normal"]["observed"], self.receipt["replay"]["observed"]
        )
        self.assertEqual(
            self.receipt["normal"]["observed"]["topology"]["cycle"],
            {"gudhi_b1": 1, "toponetx_b1": 1, "xgi_edge_sizes": [2, 2, 2]},
        )
        self.assertEqual(
            self.receipt["normal"]["observed"]["topology"]["filled"],
            {"gudhi_b1": 0, "toponetx_b1": 0, "xgi_edge_sizes": [2, 2, 2, 3]},
        )
        self.assertEqual(self._validate(self.receipt), ())

    def test_capability_suite_replay_registry_revalidates_this_receipt(self) -> None:
        verify_external_capability_receipt(
            capability_id=CAPABILITY_ID,
            receipt=self.receipt,
            expected_receipt_sha256=self.receipt["receipt_sha256"],
            require_pass=True,
        )

    def test_rehashed_forged_tool_value_still_fails_controller_recomputation(self) -> None:
        forged = copy.deepcopy(self.receipt)
        forged["normal"]["observed"]["topology"]["filled"]["gudhi_b1"] = 1
        body = dict(forged)
        body.pop("receipt_sha256")
        forged["receipt_sha256"] = hashlib.sha256(canonical_json(body)).hexdigest()

        errors = self._validate(forged)

        self.assertTrue(errors)
        self.assertTrue(
            any("controls differ" in error or "failed controller control" in error for error in errors)
        )

    def test_binding_has_no_static_machine_or_python_version_acceptance_pin(self) -> None:
        self.assertIsInstance(self.binding, GraphTopologyCapabilityBinding)
        source = Path(__file__).resolve().parents[1] / "src" / "constraintbox" / "external_graph_topology_capability.py"
        text = source.read_text(encoding="utf-8")
        self.assertNotIn("/Users/", text)
        self.assertNotIn("RUNTIME_PIN", text)
        self.assertFalse(self.result["engine_readiness_claim"])
        self.assertFalse(self.result["promotion_allowed"])
