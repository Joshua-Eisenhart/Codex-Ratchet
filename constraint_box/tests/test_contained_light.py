from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from constraintbox.contained_light import (
    build_surface,
    collapsed_seed_fixture,
    ContainedLightJournalError,
    journal_path,
    list_operations,
    main as contained_main,
    open_journal,
    record_receipt,
    seed_fixture,
    seed_receipt_for,
    status_receipt,
    verify_journal,
)
from constraintbox.manifold_foundation import validate_foundation_file


BOX = Path(__file__).resolve().parents[1]


class ContainedLightTests(unittest.TestCase):
    def test_seed_receipt_recomputes_capacity_and_static_supports(self) -> None:
        receipt = validate_foundation_file(seed_fixture(BOX))
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(receipt["operation"], "finite_time_first_seed_validation.v1")
        self.assertEqual(receipt["checks"]["capacity_bits_recomputed"], [1.0, 2.0, 3.0])
        self.assertEqual(receipt["checks"]["delta_capacity_bits_recomputed"], [1.0, 1.0])
        supports = receipt["surface"]["static_supports"]
        self.assertEqual([row["W"] for row in supports], [2, 4, 8])
        self.assertEqual(receipt["surface"]["kind"], "static_finite_supports")
        self.assertIn("attractor", receipt["surface"]["not"])

    def test_collapsed_seed_fixture_refuses(self) -> None:
        receipt = seed_receipt_for(collapsed_seed_fixture(BOX))
        self.assertEqual(receipt["status"], "REFUSE")
        self.assertIn("REFUSE_ORDER_GAP_COLLAPSED", receipt["reason"])

    def test_surface_lists_probes_and_constraints(self) -> None:
        surface = build_surface(BOX)
        self.assertEqual(surface["schema"], "constraintbox.contained-light-surface.v1")
        self.assertFalse(surface["promotion_allowed"])
        constraints = surface["seed"]["surface"]["constraints"]
        self.assertEqual(constraints[0]["id"], "C0_finitude")
        packet_names = {Path(item["path"]).name for item in surface["packets"]}
        self.assertIn("positive_distinguish.json", packet_names)
        positive = next(
            item
            for item in surface["packets"]
            if item["path"].endswith("positive_distinguish.json")
        )
        self.assertEqual(positive["probes"], ["color", "shape"])
        self.assertEqual(
            positive["honest_operation"],
            "finite_probe_assignment_feasibility.v1",
        )
        self.assertTrue(surface["bound_packets"])
        self.assertEqual(
            surface["bound_packets"][0]["honest_operation"],
            "bound_observation_quotient.v1",
        )

    def test_journal_records_a_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt = {"status": "PASS", "operation": "unit"}
            dest = root / "receipts" / "unit.json"
            record_receipt(root, "seed", receipt, dest)
            rows = list_operations(root)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["verb"], "seed")
            self.assertEqual(rows[0]["status"], "PASS")
            stored = json.loads(dest.read_text(encoding="utf-8"))
            self.assertEqual(stored["operation"], "unit")
            self.assertEqual(rows[0]["receipt_sha256"], stored["receipt_sha256"])
            self.assertEqual(verify_journal(root)["status"], "PASS")

    def test_journal_refuses_forged_caller_digest_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "receipts" / "forged.json"
            with self.assertRaisesRegex(
                ContainedLightJournalError,
                "REFUSE_CALLER_RECEIPT_DIGEST_MISMATCH",
            ):
                record_receipt(
                    root,
                    "seed",
                    {
                        "status": "PASS",
                        "operation": "forged",
                        "receipt_sha256": "0" * 64,
                    },
                    dest,
                )
            self.assertFalse(dest.exists())
            self.assertFalse(journal_path(root).exists())

    def test_journal_refuses_update_and_delete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            record_receipt(
                root,
                "seed",
                {"status": "PASS", "operation": "immutable"},
                root / "receipts" / "immutable.json",
            )
            con = sqlite3.connect(journal_path(root))
            try:
                with self.assertRaisesRegex(
                    sqlite3.IntegrityError,
                    "REFUSE_CONTAINED_LIGHT_APPEND_ONLY",
                ):
                    con.execute("UPDATE operations SET status = 'HOLD' WHERE id = 1")
                con.rollback()
                with self.assertRaisesRegex(
                    sqlite3.IntegrityError,
                    "REFUSE_CONTAINED_LIGHT_APPEND_ONLY",
                ):
                    con.execute("DELETE FROM operations WHERE id = 1")
                con.rollback()
            finally:
                con.close()
            self.assertEqual(verify_journal(root)["status"], "PASS")

    def test_status_holds_after_latest_output_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dest = root / "receipts" / "tamper.json"
            record_receipt(
                root,
                "seed",
                {"status": "PASS", "operation": "tamper"},
                dest,
            )
            dest.write_text('{"status":"PASS","operation":"changed"}\n')
            receipt = status_receipt(root)
            self.assertEqual(receipt["status"], "HOLD")
            self.assertTrue(
                any(
                    code.startswith("HOLD_JOURNAL_OUTPUT_MISMATCH")
                    for code in receipt["journal_integrity"]["reason_codes"]
                )
            )

    def test_cli_separates_fixture_root_from_dynamic_state_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_root = Path(tmp)
            returncode = contained_main(
                [
                    "--root",
                    str(BOX),
                    "--state-root",
                    str(state_root),
                    "seed",
                ]
            )
            self.assertEqual(returncode, 0)
            self.assertTrue((state_root / "receipts" / "seed.json").is_file())
            self.assertTrue(journal_path(state_root).is_file())


if __name__ == "__main__":
    unittest.main()
