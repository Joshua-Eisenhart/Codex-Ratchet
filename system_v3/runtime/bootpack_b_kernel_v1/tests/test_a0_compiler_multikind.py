import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from a0_compiler import compile_export_block
from kernel import BootpackBKernel
from state import KernelState


class TestA0CompilerMultikind(unittest.TestCase):
    def test_compiles_multikind_chain_and_b_accepts(self):
        strategy = {
            "schema": "A1_STRATEGY_v1",
            "strategy_id": "STRAT_MULTIKIND_0001",
            "inputs": {
                "state_hash": "0" * 64,
                "fuel_slice_hashes": ["1" * 64],
                "bootpack_rules_hash": "2" * 64,
                "pinned_ruleset_sha256": None,
                "pinned_megaboot_sha256": None,
            },
            "budget": {"max_items": 4, "max_sims": 4},
            "policy": {
                "forbid_fields": ["confidence", "probability", "embedding", "hidden_prompt", "raw_text"],
                "overlay_ban_terms": [],
                "require_try_to_fail": False,
            },
            "targets": [
                {
                    "item_class": "SPEC_HYP",
                    "id": "S_MATH_QIT",
                    "kind": "MATH_DEF",
                    "requires": ["P_MATH_QIT"],
                    "def_fields": [
                        {"field_id": "F1", "name": "OBJECTS", "value_kind": "TOKEN", "value": "density matrix operator"},
                        {"field_id": "F2", "name": "OPERATIONS", "value_kind": "TOKEN", "value": "trace"},
                        {"field_id": "F3", "name": "INVARIANTS", "value_kind": "TOKEN", "value": "finite dimensional"},
                        {"field_id": "F4", "name": "DOMAIN", "value_kind": "TOKEN", "value": "hilbert space"},
                        {"field_id": "F5", "name": "CODOMAIN", "value_kind": "TOKEN", "value": "density matrix"},
                        {"field_id": "F6", "name": "SIM_CODE_HASH_SHA256", "value_kind": "TOKEN", "value": "a" * 64},
                        {"field_id": "F7", "name": "PROBE_KIND", "value_kind": "TOKEN", "value": "MATH_VALIDATION"},
                    ],
                    "asserts": [{"assert_id": "A1", "token_class": "MATH_TOKEN", "token": "MT_S_MATH_QIT"}],
                    "operator_id": "OP_BIND_SIM",
                },
                {
                    "item_class": "SPEC_HYP",
                    "id": "S_TERM_DENSITY_MATRIX",
                    "kind": "TERM_DEF",
                    "requires": ["S_MATH_QIT"],
                    "def_fields": [
                        {"field_id": "F1", "name": "TERM", "value_kind": "TERM_QUOTED", "value": "density_matrix"},
                        {"field_id": "F2", "name": "BINDS", "value_kind": "TOKEN", "value": "S_MATH_QIT"},
                    ],
                    "asserts": [{"assert_id": "A1", "token_class": "TERM_TOKEN", "token": "TT_DENSITY_MATRIX"}],
                    "operator_id": "OP_BIND_SIM",
                },
                {
                    "item_class": "SPEC_HYP",
                    "id": "S_LABEL_DENSITY_MATRIX",
                    "kind": "LABEL_DEF",
                    "requires": ["S_TERM_DENSITY_MATRIX"],
                    "def_fields": [
                        {"field_id": "F1", "name": "TERM", "value_kind": "TERM_QUOTED", "value": "density_matrix"},
                        {"field_id": "F2", "name": "LABEL", "value_kind": "LABEL_QUOTED", "value": "density matrix"},
                    ],
                    "asserts": [{"assert_id": "A1", "token_class": "LABEL_TOKEN", "token": "LT_DENSITY_MATRIX"}],
                    "operator_id": "OP_BIND_SIM",
                },
                {
                    "item_class": "SPEC_HYP",
                    "id": "S_CANON_DENSITY_MATRIX",
                    "kind": "CANON_PERMIT",
                    "requires": ["S_TERM_DENSITY_MATRIX"],
                    "def_fields": [
                        {"field_id": "F1", "name": "TERM", "value_kind": "TERM_QUOTED", "value": "density_matrix"},
                        {
                            "field_id": "F2",
                            "name": "REQUIRES_EVIDENCE",
                            "value_kind": "TOKEN",
                            "value": "E_CANON_DENSITY_MATRIX",
                        },
                    ],
                    "asserts": [{"assert_id": "A1", "token_class": "PERMIT_TOKEN", "token": "PT_DENSITY_MATRIX"}],
                    "operator_id": "OP_BIND_SIM",
                },
            ],
            "alternatives": [],
            "sims": {"positive": [], "negative": []},
            "self_audit": {
                "strategy_hash": "3" * 64,
                "compile_lane_digest": "4" * 64,
                "candidate_count": 4,
                "alternative_count": 0,
                "operator_ids_used": ["OP_BIND_SIM"],
            },
        }

        state = KernelState()
        compiled = compile_export_block(state=state, strategy=strategy, canonical_state_hash=state.hash(), step=1, prior_tags=[])
        report = compiled["report"]
        self.assertEqual(4, report["spec_count"])
        self.assertIn("MATH_DEF", report["spec_kind_counts"])
        self.assertIn("TERM_DEF", report["spec_kind_counts"])
        self.assertIn("LABEL_DEF", report["spec_kind_counts"])
        self.assertIn("CANON_PERMIT", report["spec_kind_counts"])

        kernel = BootpackBKernel()
        result = kernel.evaluate_export_block(compiled["export_text"], state, batch_id="MULTIKIND")
        self.assertEqual([], result["rejected"])
        self.assertEqual([], result["parked"])
        self.assertIn("density_matrix", state.term_registry)
        self.assertIn("S_CANON_DENSITY_MATRIX", state.evidence_pending)


if __name__ == "__main__":
    unittest.main()
