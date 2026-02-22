import json
import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from a0_compiler import compile_export_block
from state import KernelState


def _load_strategy() -> dict:
    return json.loads((BASE / "a1_strategies" / "sample_strategy.json").read_text(encoding="utf-8"))


class TestRepairLoopTags(unittest.TestCase):
    def test_probe_pressure_maps_to_inject_probe(self):
        strategy = _load_strategy()
        strategy["targets"][0]["requires"] = []
        state = KernelState()
        compiled = compile_export_block(state, strategy, canonical_state_hash=state.hash(), step=1, prior_tags=["PROBE_PRESSURE"])
        operators = [row["operator_id"] for row in compiled["report"]["repair_actions"]]
        self.assertIn("OP_INJECT_PROBE", operators)
        self.assertIn("PROBE_HYP", compiled["export_text"])

    def test_schema_fail_maps_to_repair_def_field(self):
        strategy = _load_strategy()
        strategy["targets"][0]["def_fields"] = []
        strategy["targets"][0]["asserts"] = []
        state = KernelState()
        compiled = compile_export_block(state, strategy, canonical_state_hash=state.hash(), step=2, prior_tags=["SCHEMA_FAIL"])
        operators = [row["operator_id"] for row in compiled["report"]["repair_actions"]]
        self.assertIn("OP_REPAIR_DEF_FIELD", operators)
        self.assertIn("REQUIRES_EVIDENCE", compiled["export_text"])

    def test_sim_fail_kill_maps_to_negative_expansion(self):
        strategy = _load_strategy()
        strategy["policy"]["require_try_to_fail"] = False
        strategy["alternatives"] = []
        strategy["budget"]["max_items"] = 5
        state = KernelState()
        compiled = compile_export_block(state, strategy, canonical_state_hash=state.hash(), step=3, prior_tags=["SIM_FAIL_KILL"])
        operators = [row["operator_id"] for row in compiled["report"]["repair_actions"]]
        self.assertIn("OP_NEG_SIM_EXPAND", operators)
        self.assertGreaterEqual(compiled["report"]["spec_count"], 2)

    def test_unknown_reject_tag_marks_operator_exhausted(self):
        strategy = _load_strategy()
        state = KernelState()
        compiled = compile_export_block(state, strategy, canonical_state_hash=state.hash(), step=4, prior_tags=["UNKNOWN_TAG"])
        self.assertIn("UNKNOWN_TAG", compiled["report"]["operator_exhausted_tags"])

    def test_derived_only_maps_to_mutate_lexeme(self):
        strategy = _load_strategy()
        strategy["targets"][0]["def_fields"].append(
            {"field_id": "F99", "name": "LABEL", "value_kind": "TOKEN", "value": "Mixed Value"}
        )
        state = KernelState()
        compiled = compile_export_block(state, strategy, canonical_state_hash=state.hash(), step=5, prior_tags=["DERIVED_ONLY"])
        operators = [row["operator_id"] for row in compiled["report"]["repair_actions"]]
        self.assertIn("OP_MUTATE_LEXEME", operators)


if __name__ == "__main__":
    unittest.main()
