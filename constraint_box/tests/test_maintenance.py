from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from constraintbox.maintenance import (
    ReceiptTrustError,
    load_trusted_receipt_set,
    major_run_preflight,
)


class MaintenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.now = datetime(2026, 7, 25, 20, 0, tzinfo=timezone.utc)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def receipt(
        self,
        tier: str,
        *,
        state: str = "READY",
        age_hours: float = 1,
        required_state: str = "READY",
        name: str | None = None,
    ) -> Path:
        path = self.root / (name or f"{tier}.json")
        fixture_sha256 = "1" * 64
        path.write_text(
            json.dumps(
                {
                    "schema": "constraintbox.sim-tier-receipt.v2",
                    "layer_id": tier,
                    "layer_name": f"test-{tier}",
                    "mode": "acceptance",
                    "state": state,
                    "manifest_sha256": "2" * 64,
                    "fixture_sha256": fixture_sha256,
                    "controller_sha256": "3" * 64,
                    "python_executable": sys.executable,
                    "python_version": (
                        f"{sys.version_info.major}.{sys.version_info.minor}"
                    ),
                    "environment": {"state": "TEST"},
                    "elapsed_seconds": 0.01,
                    "generated_at_utc": (
                        self.now - timedelta(hours=age_hours)
                    ).isoformat(),
                    "capabilities": [
                        {
                            "capability_id": "required_fixture",
                            "required": True,
                            "state": required_state,
                            "reason": "test_fixture",
                            "expected_version": "test",
                            "observed_version": "test",
                            "elapsed_seconds": 0.01,
                            "worker_sha256": "4" * 64,
                            "fixture_sha256": fixture_sha256,
                            "controls": {"positive": True},
                            "evidence": {},
                        },
                        {
                            "capability_id": "optional_fixture",
                            "required": False,
                            "state": "UNAVAILABLE",
                            "reason": "optional_test_fixture",
                            "expected_version": None,
                            "observed_version": None,
                            "elapsed_seconds": 0.0,
                            "worker_sha256": None,
                            "fixture_sha256": fixture_sha256,
                            "controls": {},
                            "evidence": {},
                        },
                    ],
                    "promotion_allowed": False,
                }
            ),
            encoding="utf-8",
        )
        return path

    def trust_receipts(self, paths: list[Path]):
        trust_path = self.root / "trusted-receipts.json"
        trust_path.write_text(
            json.dumps(
                {
                    "schema": "constraintbox.trusted-receipt-set.v1",
                    "trust_set_id": "maintenance-test-controller-pin",
                    "receipt_bindings": [
                        {
                            "receipt_sha256": hashlib.sha256(
                                path.read_bytes()
                            ).hexdigest(),
                            "receipt_schema": "constraintbox.sim-tier-receipt.v2",
                            "layer_id": json.loads(
                                path.read_text(encoding="utf-8")
                            )["layer_id"],
                        }
                        for path in paths
                    ],
                    "promotion_allowed": False,
                }
            ),
            encoding="utf-8",
        )
        return load_trusted_receipt_set(
            trust_path,
            expected_manifest_sha256=hashlib.sha256(
                trust_path.read_bytes()
            ).hexdigest(),
        )

    def test_ready_and_degraded_with_required_controls_ready_pass(self) -> None:
        paths = [self.receipt("S1"), self.receipt("S2", state="DEGRADED")]
        result = major_run_preflight(
            paths,
            ["S1", "S2"],
            24,
            trusted_receipts=self.trust_receipts(paths),
            now=self.now,
        )
        self.assertEqual(result["disposition"], "READY")
        self.assertTrue(result["receipt_checks_performed"])
        self.assertEqual(result["trust_binding"]["status"], "BOUND")

    def test_missing_stale_or_required_failure_parks(self) -> None:
        paths = [
            self.receipt("S1", age_hours=30),
            self.receipt("S2", state="DEGRADED", required_state="FAILED"),
        ]
        result = major_run_preflight(
            paths,
            ["S1", "S2", "S3"],
            24,
            trusted_receipts=self.trust_receipts(paths),
            now=self.now,
        )
        self.assertEqual(result["disposition"], "PARKED")
        reasons = {row["reason"].split(":")[0] for row in result["problems"]}
        self.assertEqual(
            reasons, {"receipt_stale", "tier_not_ready", "receipt_missing"}
        )

    def test_duplicate_tier_parks(self) -> None:
        first = self.receipt("S1", name="S1-first.json")
        second = self.receipt("S1", age_hours=2, name="S1-second.json")
        paths = [first, second]
        result = major_run_preflight(
            paths,
            ["S1"],
            24,
            trusted_receipts=self.trust_receipts(paths),
            now=self.now,
        )
        self.assertEqual(result["disposition"], "PARKED")

    def test_hand_authored_ready_tier_without_trust_is_parked(self) -> None:
        path = self.root / "hostile-ready.json"
        path.write_text(
            json.dumps(
                {
                    "schema": "constraintbox.sim-tier-receipt.v2",
                    "layer_id": "S1",
                    "state": "READY",
                    "generated_at_utc": self.now.isoformat(),
                    "capabilities": [
                        {
                            "capability_id": "fake",
                            "required": True,
                            "state": "READY",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        result = major_run_preflight([path], ["S1"], 24, now=self.now)
        self.assertEqual(result["disposition"], "PARKED")
        self.assertFalse(result["receipt_checks_performed"])
        self.assertEqual(
            result["problems"], [{"reason": "trusted_receipt_set_missing"}]
        )

    def test_pinned_minimal_ready_tier_still_fails_typed_provenance(self) -> None:
        path = self.root / "pinned-hostile-ready.json"
        path.write_text(
            json.dumps(
                {
                    "schema": "constraintbox.sim-tier-receipt.v2",
                    "layer_id": "S1",
                    "state": "READY",
                    "generated_at_utc": self.now.isoformat(),
                    "capabilities": [],
                }
            ),
            encoding="utf-8",
        )
        result = major_run_preflight(
            [path],
            ["S1"],
            24,
            trusted_receipts=self.trust_receipts([path]),
            now=self.now,
        )
        self.assertEqual(result["disposition"], "PARKED")
        self.assertFalse(result["receipt_checks_performed"])
        self.assertEqual(result["problems"][0]["reason"], "receipt_type_invalid")

    def test_receipt_changed_after_binding_is_parked(self) -> None:
        path = self.receipt("S1")
        trusted = self.trust_receipts([path])
        body = json.loads(path.read_text(encoding="utf-8"))
        body["state"] = "READY"
        body["generated_at_utc"] = (
            self.now + timedelta(minutes=1)
        ).isoformat()
        path.write_text(json.dumps(body), encoding="utf-8")
        result = major_run_preflight(
            [path],
            ["S1"],
            24,
            trusted_receipts=trusted,
            now=self.now,
        )
        self.assertEqual(result["disposition"], "PARKED")
        self.assertEqual(
            result["problems"][0]["reason"], "receipt_digest_not_trusted"
        )

    def test_trust_manifest_requires_an_external_digest_pin(self) -> None:
        path = self.receipt("S1")
        with self.assertRaisesRegex(
            ReceiptTrustError, "does not match external pin"
        ):
            load_trusted_receipt_set(
                path,
                expected_manifest_sha256="0" * 64,
            )


if __name__ == "__main__":
    unittest.main()
