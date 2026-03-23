from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
REPO = BASE.parents[2]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(REPO / "system_v3" / "tools"))

import a1_cold_core_strip as cold_core_strip
import a1_pack_selector
from a1_a0_b_sim_runner import run_loop
from codex_json_to_a1_strategy_packet_zip import main as packetize_main
from zip_protocol_v2_writer import write_zip_protocol_v2
from zip_protocol_v2_validator import validate_zip_protocol_v2


class TestA1PacketSource(unittest.TestCase):
    def test_packet_source_emits_request_when_inbox_empty(self) -> None:
        strategy_path = BASE / "a1_strategies" / "sample_strategy.json"
        run_id = "TEST_A1_PACKET_EMPTY"
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir, _ = run_loop(
                strategy_path=strategy_path,
                steps=3,
                run_id=run_id,
                a1_source="packet",
                a1_model="",
                a1_timeout_sec=1,
                clean=True,
                runs_root_override=tmpdir,
            )
            summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual("A1_NEEDS_EXTERNAL_STRATEGY", summary["stop_reason"])
            zips = sorted((run_dir / "zip_packets").glob("*_A0_TO_A1_SAVE_ZIP.zip"))
            self.assertTrue(zips)
            # Validate capsule structure; content semantics are handled by external A1.
            result = validate_zip_protocol_v2(str(zips[0]), {})
            self.assertEqual("OK", result["outcome"])

    def test_packet_source_consumes_strategy_zip(self) -> None:
        strategy_path = BASE / "a1_strategies" / "sample_strategy.json"
        run_id = "TEST_A1_PACKET_ZIP"
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / run_id
            (run_dir / "a1_inbox").mkdir(parents=True, exist_ok=True)
            # Drop a valid strategy capsule into the inbox before starting the run (clean=False).
            inbox_zip = run_dir / "a1_inbox" / "000001_A1_TO_A0_STRATEGY_ZIP.zip"
            write_zip_protocol_v2(
                out_path=inbox_zip,
                header={
                    "zip_type": "A1_TO_A0_STRATEGY_ZIP",
                    "direction": "FORWARD",
                    "source_layer": "A1",
                    "target_layer": "A0",
                    "run_id": run_id,
                    "sequence": 1,
                    "created_utc": "1980-01-01T00:00:00Z",
                    "compiler_version": "",
                },
                payload_json={
                    "A1_STRATEGY_v1.json": {
                        "schema": "A1_STRATEGY_v1",
                        "strategy_id": "STRAT_TEST",
                        "inputs": {
                            "state_hash": "0" * 64,
                            "fuel_slice_hashes": ["1" * 64],
                            "bootpack_rules_hash": "2" * 64,
                            "pinned_ruleset_sha256": None,
                            "pinned_megaboot_sha256": None,
                        },
                        "budget": {"max_items": 1, "max_sims": 1},
                        "policy": {
                            "forbid_fields": ["confidence", "probability", "embedding", "hidden_prompt", "raw_text"],
                            "overlay_ban_terms": [],
                            "require_try_to_fail": True,
                        },
                        "targets": [
                            {
                                "item_class": "SPEC_HYP",
                                "id": "S_BIND_ALPHA",
                                "kind": "SIM_SPEC",
                                "requires": ["P_BIND_ALPHA"],
                                "def_fields": [{"field_id": "F1", "name": "REQUIRES_EVIDENCE", "value_kind": "TOKEN", "value": "E_BIND_ALPHA"}],
                                "asserts": [{"assert_id": "A1", "token_class": "EVIDENCE_TOKEN", "token": "E_BIND_ALPHA"}],
                                "operator_id": "OP_BIND_SIM",
                            }
                        ],
                        "alternatives": [],
                        "sims": {"positive": [], "negative": []},
                        "self_audit": {"strategy_hash": "", "compile_lane_digest": "", "candidate_count": 0, "alternative_count": 0, "operator_ids_used": []},
                    }
                },
            )
            result = validate_zip_protocol_v2(str(inbox_zip), {})
            self.assertEqual("OK", result["outcome"])

            out_dir, _ = run_loop(
                strategy_path=strategy_path,
                steps=1,
                run_id=run_id,
                a1_source="packet",
                a1_model="",
                a1_timeout_sec=1,
                clean=False,
                runs_root_override=tmpdir,
            )
            summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
            self.assertNotEqual("A1_NEEDS_EXTERNAL_STRATEGY", summary["stop_reason"])

    def test_packet_source_consumes_selector_strategy_zip_with_support_metadata(self) -> None:
        strategy_path = BASE / "a1_strategies" / "sample_strategy.json"
        run_id = "TEST_A1_PACKET_SELECTOR_ZIP"
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            run_dir = tmp / run_id
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
                        str(tmp),
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
            selector_rc = a1_pack_selector.main(
                [
                    "--run-id",
                    run_id,
                    "--runs-root",
                    str(tmp),
                    "--cold-core",
                    str(cold_core_path),
                    "--sequence",
                    "1",
                ]
            )
            self.assertEqual(0, selector_rc)

            selector_strategy = run_dir / "a1_sandbox" / "outgoing" / "000001_A1_STRATEGY_v1__PACK_SELECTOR.json"
            packet_rc = packetize_main(
                [
                    "--run-id",
                    run_id,
                    "--runs-root",
                    str(tmp),
                    "--strategy-json",
                    str(selector_strategy),
                    "--sequence",
                    "1",
                    "--created-utc",
                    "1980-01-01T00:00:00Z",
                ]
            )
            self.assertEqual(0, packet_rc)

            inbox_zip = run_dir / "a1_inbox" / "000001_A1_TO_A0_STRATEGY_ZIP.zip"
            result = validate_zip_protocol_v2(str(inbox_zip.resolve()), {})
            self.assertEqual("OK", result["outcome"])

            out_dir, _ = run_loop(
                strategy_path=strategy_path,
                steps=1,
                run_id=run_id,
                a1_source="packet",
                a1_model="",
                a1_timeout_sec=1,
                clean=False,
                runs_root_override=tmpdir,
            )
            summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
            self.assertNotEqual("A1_NEEDS_EXTERNAL_STRATEGY", summary["stop_reason"])

            self.assertFalse(inbox_zip.exists())


if __name__ == "__main__":
    unittest.main()
