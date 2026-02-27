from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
RUNS_ROOT = BASE.parents[1] / "runs"
sys.path.insert(0, str(BASE))

from a1_a0_b_sim_runner import run_loop
from zip_protocol_v2_writer import write_zip_protocol_v2
from zip_protocol_v2_validator import validate_zip_protocol_v2


class TestA1PacketSource(unittest.TestCase):
    def test_packet_source_emits_request_when_inbox_empty(self) -> None:
        strategy_path = BASE / "a1_strategies" / "sample_strategy.json"
        run_id = "TEST_A1_PACKET_EMPTY"
        run_dir, _ = run_loop(
            strategy_path=strategy_path,
            steps=3,
            run_id=run_id,
            a1_source="packet",
            a1_model="",
            a1_timeout_sec=1,
            clean=True,
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
        run_dir = RUNS_ROOT / run_id
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
        )
        summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
        self.assertNotEqual("A1_NEEDS_EXTERNAL_STRATEGY", summary["stop_reason"])


if __name__ == "__main__":
    unittest.main()
