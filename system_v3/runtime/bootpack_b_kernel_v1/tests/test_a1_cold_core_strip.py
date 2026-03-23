import json
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE / "tools"))

import a1_cold_core_strip as cold_core_strip

from a1_cold_core_strip import (
    _collect_export_pack_support_terms,
    _collect_fuel_digest_support_terms,
    _filter_rescue_targets,
)


class TestA1ColdCoreStrip(unittest.TestCase):
    def test_filter_rescue_targets_uses_goal_term_from_item_text(self) -> None:
        state = {
            "graveyard": {
                "S_BAD_PARTIAL_TRACE": {
                    "item_text": "DEF_FIELD X CORR GOAL_TERM partial_trace\nDEF_FIELD X CORR PROBE_TERM partial_trace"
                },
                "S_GOOD_CORRELATION_POLARITY": {
                    "item_text": "DEF_FIELD X CORR GOAL_TERM correlation_polarity\nDEF_FIELD X CORR PROBE_TERM correlation_polarity"
                },
            }
        }
        filtered = _filter_rescue_targets(
            state,
            ["S_BAD_PARTIAL_TRACE", "S_GOOD_CORRELATION_POLARITY"],
            allowed_terms={"correlation", "correlation_polarity", "density_entropy"},
        )
        self.assertEqual(["S_GOOD_CORRELATION_POLARITY"], filtered)

    def test_filter_rescue_targets_uses_bound_math_refs_when_goal_term_missing(self) -> None:
        state = {
            "graveyard": {
                "S_BAD_PARTIAL_TRACE": {
                    "item_text": "REQUIRES X CORR S000005_Z_MATH_PARTIAL_TRACE\nDEF_FIELD X CORR SIM_ID S000005_Z_SIM_ALT_NEG_EXTRA3_PARTIAL_TRACE"
                },
                "S_GOOD_CORRELATION_POLARITY": {
                    "item_text": "REQUIRES X CORR S000007_Z_MATH_CORRELATION_POLARITY\nDEF_FIELD X CORR SIM_ID S000007_Z_SIM_ALT_NEG_CORRELATION_POLARITY"
                },
            }
        }
        filtered = _filter_rescue_targets(
            state,
            ["S_BAD_PARTIAL_TRACE", "S_GOOD_CORRELATION_POLARITY"],
            allowed_terms={"correlation", "correlation_polarity", "density_entropy"},
        )
        self.assertEqual(["S_GOOD_CORRELATION_POLARITY"], filtered)

    def test_export_candidate_pack_support_terms_only_accept_term_anchors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "export_candidate_pack.json"
            path.write_text(
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
                            },
                            {
                                "candidate_id": "ECP_00002",
                                "kernel_anchor": "SIM_EVIDENCE_PACK",
                                "anchor_type": "SPEC_ID",
                                "source_term": "sim_evidence_pack",
                                "source_pointers": ["x#L2"],
                            },
                            {
                                "candidate_id": "ECP_00003",
                                "kernel_anchor": "a2",
                                "anchor_type": "TERM",
                                "source_term": "a2",
                                "source_pointers": ["x#L3"],
                            },
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
            terms, negative_pressure = _collect_export_pack_support_terms(path)
            self.assertEqual(["correlation_polarity"], terms)
            self.assertEqual("FC_1", negative_pressure[0]["pressure_id"])

    def test_fuel_digest_support_terms_only_accept_term_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "fuel_digest.json"
            path.write_text(
                json.dumps(
                    {
                        "schema": "FUEL_DIGEST_v1",
                        "kernel_candidate_suggestions": [
                            {"candidate_id": "KC_1", "kernel_candidate": "density_entropy", "candidate_type": "TERM", "source_pointer": "x#L1"},
                            {"candidate_id": "KC_2", "kernel_candidate": "EXPORT_BLOCK", "candidate_type": "SPEC_ID", "source_pointer": "x#L2"},
                        ],
                        "overlay_mapping_suggestions": [
                            {"mapping_id": "OM_1", "source_term": "partial_trace", "kernel_anchor_candidate": "partial_trace", "anchor_type": "TERM", "source_pointer": "x#L3"},
                            {"mapping_id": "OM_2", "source_term": "sim", "kernel_anchor_candidate": "sim", "anchor_type": "TERM", "source_pointer": "x#L4"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            terms = _collect_fuel_digest_support_terms(path)
            self.assertEqual(["density_entropy", "partial_trace"], terms)

    def test_main_merges_mining_terms_into_support_candidates_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            runs_root = tmp / "runs"
            run_id = "TMP_COLD_CORE_MINING_001"
            run_dir = runs_root / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "state.json").write_text(
                json.dumps(
                    {
                        "term_registry": {},
                        "l0_lexeme_set": [],
                        "kill_log": [],
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
                        "proposed_terms": ["entropy_bridge"],
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
                            {"candidate_id": "KC_1", "kernel_candidate": "density_entropy", "candidate_type": "TERM", "source_pointer": "x#L1"}
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
                rc = cold_core_strip.main(
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

            self.assertEqual(0, rc)
            out_path = cold_root / run_id / "cold_core" / "000001_A1_COLD_CORE_PROPOSALS_v1.json"
            payload = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(["entropy_bridge"], payload["admissible_term_candidates"])
            self.assertEqual(["correlation_polarity", "density_entropy"], payload["mining_support_terms"])
            self.assertIn("correlation_polarity", payload["support_term_candidates"])
            self.assertIn("density_entropy", payload["support_term_candidates"])
            self.assertNotIn("density_entropy", payload["admissible_term_candidates"])
            self.assertEqual("FC_1", payload["mining_negative_pressure_witnesses"][0]["pressure_id"])


if __name__ == "__main__":
    unittest.main()
