import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from a1_bridge import _coerce_strategy, _parse_strategy_output_text


class TestA1BridgeParsing(unittest.TestCase):
    def test_parse_direct_json(self):
        raw = '{"schema":"A1_STRATEGY_v1","strategy_id":"X"}'
        parsed = _parse_strategy_output_text(raw)
        self.assertEqual("X", parsed["strategy_id"])

    def test_parse_fenced_json(self):
        raw = """response
```json
{"schema":"A1_STRATEGY_v1","strategy_id":"X2"}
```
"""
        parsed = _parse_strategy_output_text(raw)
        self.assertEqual("X2", parsed["strategy_id"])

    def test_parse_json_inside_text(self):
        raw = "analysis...\n{ \"schema\": \"A1_STRATEGY_v1\", \"strategy_id\": \"X3\" }\nextra text"
        parsed = _parse_strategy_output_text(raw)
        self.assertEqual("X3", parsed["strategy_id"])

    def test_parse_fail_on_missing_object(self):
        with self.assertRaises(ValueError):
            _parse_strategy_output_text("no json here")

    def test_coerce_partial_strategy(self):
        base = {
            "schema": "A1_STRATEGY_v1",
            "strategy_id": "BASE",
            "inputs": {
                "state_hash": "0" * 64,
                "fuel_slice_hashes": ["1" * 64],
                "bootpack_rules_hash": "2" * 64,
                "pinned_ruleset_sha256": None,
                "pinned_megaboot_sha256": None,
            },
            "budget": {"max_items": 2, "max_sims": 2},
            "policy": {
                "forbid_fields": ["confidence", "probability", "embedding", "hidden_prompt", "raw_text"],
                "overlay_ban_terms": [],
                "require_try_to_fail": True,
            },
            "targets": [
                {
                    "item_class": "SPEC_HYP",
                    "id": "S_ALPHA",
                    "kind": "SIM_SPEC",
                    "requires": ["P_ALPHA"],
                    "def_fields": [
                        {"field_id": "F1", "name": "REQUIRES_EVIDENCE", "value_kind": "TOKEN", "value": "E_ALPHA"}
                    ],
                    "asserts": [{"assert_id": "A1", "token_class": "EVIDENCE_TOKEN", "token": "E_ALPHA"}],
                    "operator_id": "OP_BIND_SIM",
                }
            ],
            "alternatives": [],
            "sims": {"positive": [], "negative": []},
            "self_audit": {
                "strategy_hash": "3" * 64,
                "compile_lane_digest": "4" * 64,
                "candidate_count": 1,
                "alternative_count": 0,
                "operator_ids_used": ["OP_BIND_SIM"],
            },
        }
        candidate = {"strategy_id": "NEW", "targets": [{"id": "S_BETA"}], "confidence": 0.9}
        out = _coerce_strategy(candidate, base, step=7)
        self.assertEqual("NEW", out["strategy_id"])
        self.assertEqual("A1_STRATEGY_v1", out["schema"])
        self.assertNotIn("confidence", out)
        self.assertTrue(out["targets"][0]["id"].startswith("S_BETA_S0007"))
        self.assertIn("operator_ids_used", out["self_audit"])


if __name__ == "__main__":
    unittest.main()
