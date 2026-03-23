import json
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
BOOTPACK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BOOTPACK))
sys.path.insert(0, str(BASE / "tools"))

import a1_cold_core_strip as cold_core_strip
import a1_pack_selector
from a1_strategy import validate_strategy


class TestA1PackSelector(unittest.TestCase):
    def test_main_carries_mining_witness_fields_into_process_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            runs_root = tmp / "runs"
            run_id = "TMP_PACK_SELECTOR_MINING_001"
            run_dir = runs_root / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "state.json").write_text(
                json.dumps(
                    {
                        "term_registry": {},
                        "l0_lexeme_set": [],
                        "graveyard": {},
                    }
                ),
                encoding="utf-8",
            )

            cold_core_path = tmp / "000007_A1_COLD_CORE_PROPOSALS_v1.json"
            cold_core_path.write_text(
                json.dumps(
                    {
                        "schema": "A1_COLD_CORE_PROPOSALS_v1",
                        "sequence": 7,
                        "admissible_term_candidates": ["density_entropy"],
                        "support_term_candidates": ["partial_trace"],
                        "graveyard_rescue_targets": [],
                        "proposed_negative_classes": ["COMMUTATIVE_ASSUMPTION"],
                        "need_atomic_bootstrap": [],
                        "mining_support_terms": ["correlation_polarity", "partial_trace"],
                        "mining_artifact_inputs": [
                            "EXPORT_CANDIDATE_PACK_v1:/tmp/export_candidate_pack.json",
                            "FUEL_DIGEST_v1:/tmp/fuel_digest.json",
                        ],
                        "mining_negative_pressure_witnesses": [
                            {
                                "pressure_id": "FC_1",
                                "text": "must not overwrite canon",
                                "source_pointer": "/tmp/export_candidate_pack.json#L9",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with io.StringIO() as buf, redirect_stdout(buf):
                rc = a1_pack_selector.main(
                    [
                        "--run-id",
                        run_id,
                        "--runs-root",
                        str(runs_root),
                        "--cold-core",
                        str(cold_core_path),
                        "--sequence",
                        "7",
                    ]
                )
                selector_result = json.loads(buf.getvalue().strip())
            self.assertEqual(0, rc)

            out_path = run_dir / "a1_sandbox" / "outgoing" / "000007_A1_STRATEGY_v1__PACK_SELECTOR.json"
            payload = json.loads(out_path.read_text(encoding="utf-8"))
            process_audit = payload["admissibility"]["process_audit"]

            self.assertEqual(
                ["correlation_polarity", "partial_trace"],
                process_audit["mining_support_terms"],
            )
            self.assertEqual(
                [
                    "EXPORT_CANDIDATE_PACK_v1:/tmp/export_candidate_pack.json",
                    "FUEL_DIGEST_v1:/tmp/fuel_digest.json",
                ],
                process_audit["mining_artifact_inputs"],
            )
            self.assertEqual(1, process_audit["mining_negative_pressure_count"])
            self.assertIn(
                "noncanon mining witnesses are present; keep them support-side and do not treat them as executable head authority",
                process_audit["warnings"],
            )
            self.assertGreaterEqual(int(process_audit["warning_count"]), 1)
            self.assertIn("noncanon_mining_support_only", process_audit["warning_codes"])
            self.assertIn("support_boundary", process_audit["warning_categories"])
            self.assertTrue(process_audit["support_warning_present"])
            self.assertIn(
                "noncanon mining witnesses are present; keep them support-side and do not treat them as executable head authority",
                process_audit["warning_examples"],
            )
            self.assertTrue(
                any(
                    row == {
                        "message": "noncanon mining witnesses are present; keep them support-side and do not treat them as executable head authority",
                        "code": "noncanon_mining_support_only",
                        "category": "support_boundary",
                    }
                    for row in process_audit["warning_details"]
                )
            )
            self.assertEqual(["density_entropy"], payload["target_terms"])
            self.assertGreaterEqual(int(selector_result["selector_warning_count"]), 1)
            self.assertIn("noncanon_mining_support_only", selector_result["selector_warning_codes"])
            self.assertIn("support_boundary", selector_result["selector_warning_categories"])
            self.assertTrue(selector_result["selector_support_warning_present"])
            self.assertEqual([], validate_strategy(payload))

    def test_cold_core_to_pack_selector_preserves_mining_witness_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            runs_root = tmp / "runs"
            run_id = "TMP_COLD_CORE_TO_SELECTOR_001"
            run_dir = runs_root / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "state.json").write_text(
                json.dumps(
                    {
                        "term_registry": {},
                        "l0_lexeme_set": [],
                        "kill_log": [],
                        "graveyard": {},
                    }
                ),
                encoding="utf-8",
            )

            lawyer_root = tmp / "lawyer"
            cold_root = tmp / "cold"
            memos_dir = lawyer_root / run_id / "lawyer_memos"
            memos_dir.mkdir(parents=True, exist_ok=True)
            (memos_dir / "000001_MEMO_TEST.json").write_text(
                json.dumps(
                    {
                        "schema": "A1_LAWYER_MEMO_v1",
                        "role": "STEELMAN",
                        "proposed_terms": ["density_entropy"],
                        "support_terms": [],
                        "graveyard_rescue_targets": [],
                        "proposed_negative_classes": ["COMMUTATIVE_ASSUMPTION"],
                    }
                ),
                encoding="utf-8",
            )

            export_pack = tmp / "export_candidate_pack.json"
            export_pack.write_text(
                json.dumps(
                    {
                        "schema": "EXPORT_CANDIDATE_PACK_v1",
                        "candidate_items": [
                            {
                                "candidate_id": "ECP_00001",
                                "kernel_anchor": "correlation_polarity",
                                "anchor_type": "TERM",
                                "source_term": "correlation_polarity",
                                "source_pointers": ["x#L1"],
                            }
                        ],
                        "required_dependencies": [],
                        "negative_pressure": [
                            {"pressure_id": "FC_1", "text": "must not overwrite canon", "source_pointer": "x#L9"}
                        ],
                        "source_pointers": ["/tmp/source.json"],
                    }
                ),
                encoding="utf-8",
            )

            fuel_digest = tmp / "fuel_digest.json"
            fuel_digest.write_text(
                json.dumps(
                    {
                        "schema": "FUEL_DIGEST_v1",
                        "kernel_candidate_suggestions": [
                            {
                                "candidate_id": "KC_1",
                                "kernel_candidate": "partial_trace",
                                "candidate_type": "TERM",
                                "source_pointer": "x#L1",
                            }
                        ],
                        "overlay_mapping_suggestions": [],
                    }
                ),
                encoding="utf-8",
            )

            orig_lawyer_root = cold_core_strip.TRANSIENT_A1_LAWYER_ROOT
            orig_cold_root = cold_core_strip.TRANSIENT_A1_COLD_CORE_ROOT
            try:
                cold_core_strip.TRANSIENT_A1_LAWYER_ROOT = lawyer_root
                cold_core_strip.TRANSIENT_A1_COLD_CORE_ROOT = cold_root
                cold_rc = cold_core_strip.main(
                    [
                        "--run-id",
                        run_id,
                        "--runs-root",
                        str(runs_root),
                        "--sequence",
                        "1",
                        "--min-corroboration",
                        "1",
                        "--export-candidate-pack",
                        str(export_pack),
                        "--fuel-digest-json",
                        str(fuel_digest),
                    ]
                )
            finally:
                cold_core_strip.TRANSIENT_A1_LAWYER_ROOT = orig_lawyer_root
                cold_core_strip.TRANSIENT_A1_COLD_CORE_ROOT = orig_cold_root

            self.assertEqual(0, cold_rc)
            cold_core_path = cold_root / run_id / "cold_core" / "000001_A1_COLD_CORE_PROPOSALS_v1.json"

            with io.StringIO() as buf, redirect_stdout(buf):
                selector_rc = a1_pack_selector.main(
                    [
                        "--run-id",
                        run_id,
                        "--runs-root",
                        str(runs_root),
                        "--cold-core",
                        str(cold_core_path),
                        "--sequence",
                        "1",
                    ]
                )
                selector_result = json.loads(buf.getvalue().strip())
            self.assertEqual(0, selector_rc)

            out_path = run_dir / "a1_sandbox" / "outgoing" / "000001_A1_STRATEGY_v1__PACK_SELECTOR.json"
            payload = json.loads(out_path.read_text(encoding="utf-8"))
            process_audit = payload["admissibility"]["process_audit"]

            self.assertEqual(
                ["correlation_polarity", "partial_trace"],
                process_audit["mining_support_terms"],
            )
            self.assertEqual(
                [
                    str(export_pack.resolve()),
                    str(fuel_digest.resolve()),
                ],
                [str(Path(raw).resolve()) for raw in process_audit["mining_artifact_inputs"]],
            )
            self.assertEqual(1, process_audit["mining_negative_pressure_count"])
            self.assertIn(
                "noncanon mining witnesses are present; keep them support-side and do not treat them as executable head authority",
                process_audit["warnings"],
            )
            self.assertGreaterEqual(int(process_audit["warning_count"]), 1)
            self.assertIn("noncanon_mining_support_only", process_audit["warning_codes"])
            self.assertIn("support_boundary", process_audit["warning_categories"])
            self.assertTrue(process_audit["support_warning_present"])
            self.assertEqual(["density_entropy"], payload["target_terms"])
            self.assertNotIn("partial_trace", payload["target_terms"])
            self.assertGreaterEqual(int(selector_result["selector_warning_count"]), 1)
            self.assertIn("noncanon_mining_support_only", selector_result["selector_warning_codes"])
            self.assertIn("support_boundary", selector_result["selector_warning_categories"])
            self.assertTrue(selector_result["selector_support_warning_present"])
            self.assertEqual([], validate_strategy(payload))


if __name__ == "__main__":
    unittest.main()
