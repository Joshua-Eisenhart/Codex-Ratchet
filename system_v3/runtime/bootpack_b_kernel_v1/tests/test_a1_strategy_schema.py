import json
import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from a1_strategy import validate_strategy


class TestA1StrategySchema(unittest.TestCase):
    def test_sample_strategy_valid(self):
        strategy = json.loads((BASE / "a1_strategies" / "sample_strategy.json").read_text(encoding="utf-8"))
        self.assertEqual([], validate_strategy(strategy))

    def test_missing_required_root_field_rejected(self):
        strategy = json.loads((BASE / "a1_strategies" / "sample_strategy.json").read_text(encoding="utf-8"))
        strategy.pop("targets")
        errors = validate_strategy(strategy)
        self.assertTrue(any("missing root field: targets" in row for row in errors))

    def test_forbidden_field_rejected(self):
        strategy = json.loads((BASE / "a1_strategies" / "sample_strategy.json").read_text(encoding="utf-8"))
        strategy["targets"][0]["raw_text"] = "forbidden"
        errors = validate_strategy(strategy)
        self.assertTrue(any("forbidden field present" in row for row in errors))

    def test_selector_optional_root_fields_allowed(self):
        strategy = json.loads((BASE / "a1_strategies" / "sample_strategy.json").read_text(encoding="utf-8"))
        strategy["target_terms"] = ["density_entropy"]
        strategy["family_terms"] = ["density_entropy", "partial_trace"]
        strategy["admissibility"] = {
            "executable_head": ["density_entropy"],
            "process_audit": {"warnings": []},
        }
        self.assertEqual([], validate_strategy(strategy))

    def test_legacy_shape_rejected(self):
        legacy = {
            "strategy_id": "LEGACY",
            "version": "A1_STRATEGY_v1",
            "candidate_families": [],
        }
        errors = validate_strategy(legacy)
        self.assertTrue(any("missing root field: schema" in row for row in errors))

    def _minimal_v2_strategy(self):
        return {
            "schema": "A1_STRATEGY_v2",
            "strategy_id": "STRAT_V2",
            "inputs": {
                "state_hash": "0" * 64,
                "fuel_slice_hashes": ["1" * 64],
                "bootpack_rules_hash": "2" * 64,
                "pinned_ruleset_sha256": None,
                "pinned_megaboot_sha256": None,
            },
            "budget": {"max_items": 2, "max_sims": 4},
            "policy": {
                "forbid_fields": ["confidence", "probability", "embedding", "hidden_prompt", "raw_text"],
                "overlay_ban_terms": [],
                "require_try_to_fail": True,
            },
            "targets": [
                {
                    "item_class": "SPEC_HYP",
                    "id": "S_CANON",
                    "kind": "SIM_SPEC",
                    "requires": ["P_CANON"],
                    "def_fields": [
                        {"field_id": "F_EVID", "name": "REQUIRES_EVIDENCE", "value_kind": "TOKEN", "value": "E_CANON"},
                        {"field_id": "F_SIMID", "name": "SIM_ID", "value_kind": "TOKEN", "value": "SIM_POS_CANON"},
                        {"field_id": "F_TIER", "name": "TIER", "value_kind": "TOKEN", "value": "T0_ATOM"},
                        {"field_id": "F_FAMILY", "name": "FAMILY", "value_kind": "TOKEN", "value": "BASELINE"},
                        {"field_id": "F_TC", "name": "TARGET_CLASS", "value_kind": "TOKEN", "value": "TC_QIT_FOUNDATION"},
                        {"field_id": "F_PTERM", "name": "PROBE_TERM", "value_kind": "TOKEN", "value": "finite_dimensional_hilbert_space"},
                    ],
                    "asserts": [{"assert_id": "A1", "token_class": "EVIDENCE_TOKEN", "token": "E_CANON"}],
                    "operator_id": "OP_BIND_SIM",
                }
            ],
            "alternatives": [
                {
                    "item_class": "SPEC_HYP",
                    "id": "S_ALT",
                    "kind": "SIM_SPEC",
                    "requires": ["P_ALT"],
                    "def_fields": [
                        {"field_id": "F_EVID_ALT", "name": "REQUIRES_EVIDENCE", "value_kind": "TOKEN", "value": "E_ALT"},
                        {"field_id": "F_SIMID_ALT", "name": "SIM_ID", "value_kind": "TOKEN", "value": "SIM_NEG_ALT"},
                        {"field_id": "F_TIER_ALT", "name": "TIER", "value_kind": "TOKEN", "value": "T0_ATOM"},
                        {"field_id": "F_FAMILY_ALT", "name": "FAMILY", "value_kind": "TOKEN", "value": "ADVERSARIAL_NEG"},
                        {"field_id": "F_TC_ALT", "name": "TARGET_CLASS", "value_kind": "TOKEN", "value": "TC_QIT_FOUNDATION"},
                        {"field_id": "F_PTERM_ALT", "name": "PROBE_TERM", "value_kind": "TOKEN", "value": "finite_dimensional_hilbert_space"},
                    ],
                    "asserts": [{"assert_id": "A2", "token_class": "EVIDENCE_TOKEN", "token": "E_ALT"}],
                    "operator_id": "OP_NEG_SIM_EXPAND",
                }
            ],
            "sim_program": {
                "program_id": "QIT_FOUNDATION_LADDER_V1",
                "mode": "staged",
                "replay_source": "NONE",
                "mega_gate_policy": "all_lower_tiers_closed",
                "stages": [
                    {
                        "stage_id": "S0_FOUNDATION",
                        "tier": "T0_ATOM",
                        "suite_kind": "micro_suite",
                        "families": ["BASELINE", "ADVERSARIAL_NEG"],
                        "depends_on": [],
                        "target_classes": ["TC_QIT_FOUNDATION"],
                        "max_sims": 4,
                        "failure_policy": "bisect_on_fail",
                    }
                ],
            },
            "sims": {
                "positive": [{"sim_id": "SIM_POS_CANON", "binds_to": "S_CANON", "stage_id": "S0_FOUNDATION"}],
                "negative": [{"sim_id": "SIM_NEG_ALT", "binds_to": "S_ALT", "stage_id": "S0_FOUNDATION"}],
            },
            "self_audit": {
                "strategy_hash": "",
                "compile_lane_digest": "",
                "candidate_count": 1,
                "alternative_count": 1,
                "operator_ids_used": ["OP_BIND_SIM", "OP_NEG_SIM_EXPAND"],
            },
        }

    def test_minimal_v2_strategy_valid(self):
        self.assertEqual([], validate_strategy(self._minimal_v2_strategy()))

    def test_v2_missing_sim_program_rejected(self):
        strategy = self._minimal_v2_strategy()
        strategy.pop("sim_program")
        errors = validate_strategy(strategy)
        self.assertTrue(any("missing root field: sim_program" in row for row in errors))

    def test_v2_missing_stage_id_rejected(self):
        strategy = self._minimal_v2_strategy()
        strategy["sims"]["positive"][0].pop("stage_id")
        errors = validate_strategy(strategy)
        self.assertTrue(any("sims.positive[0] missing field: stage_id" in row for row in errors))


if __name__ == "__main__":
    unittest.main()
