import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

import json
import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from a1_adapter import _coerce_strategy, parse_strategy_output_text, validate_strategy_schema


def _minimal_strategy_json() -> str:
    obj = {
        "strategy_id": "STRAT_MIN",
        "version": "A1_STRATEGY_v1",
        "input_doc_refs": [{"path": "core_docs/BOOTPACK_THREAD_B_v3.9.13.md", "sha256": "a" * 64}],
        "intent": "minimal",
        "candidate_families": [
            {
                "family_id": "F1",
                "purpose": "p",
                "required_terms": [],
                "forbidden_terms": [],
                "expected_b_fences": [],
                "sim_hooks": [{"sim_spec_id": "S1", "sim_id": "S1"}],
                "candidate_templates": [
                    {
                        "spec_id": "S1",
                        "expected_kind": "SIM_SPEC",
                        "probe_id": "P1",
                        "probe_kind": "K1",
                        "probe_token": "PT_P1",
                        "requires_probe": "P1",
                        "evidence_token": "E1",
                    }
                ],
            }
        ],
        "repair_rules": {},
        "stop_conditions": {
            "max_repair_attempts_per_step": 1,
            "repeated_noop_limit": 1,
            "repeated_schema_fail_limit": 1,
        },
        "budget": {
            "max_new_terms_per_batch": 0,
            "max_new_specs_per_batch": 1,
            "max_graveyard_growth_per_n_cycles": 1,
            "n_cycles": 1,
            "probe_pressure_ratio": 0.1,
        },
    }
    return json.dumps(obj, sort_keys=True)


class TestA1AdapterParsing(unittest.TestCase):
    def test_parse_direct_json(self):
        raw = _minimal_strategy_json()
        parsed = parse_strategy_output_text(raw)
        self.assertEqual("A1_STRATEGY_v1", parsed["version"])

    def test_parse_fenced_json(self):
        raw = "notes\n```json\n" + _minimal_strategy_json() + "\n```\nextra"
        parsed = parse_strategy_output_text(raw)
        self.assertEqual("STRAT_MIN", parsed["strategy_id"])

    def test_parse_json_with_extra_trailing_text(self):
        raw = _minimal_strategy_json() + "\n\nNON_JSON_TRAILER"
        parsed = parse_strategy_output_text(raw)
        self.assertEqual("A1_STRATEGY_v1", parsed["version"])

    def test_coerce_partial_strategy_to_valid_schema(self):
        base = json.loads(_minimal_strategy_json())
        partial = {
            "strategy_id": "X",
            "candidate_families": [{"candidate_templates": [{"spec_id": "S2", "probe_id": "P2", "evidence_token": "E2"}]}],
        }
        coerced = _coerce_strategy(partial, base, step=7)
        errors = validate_strategy_schema(coerced)
        self.assertEqual([], errors)
        template = coerced["candidate_families"][0]["candidate_templates"][0]
        self.assertIn("_S0007", template["spec_id"])
        self.assertIn("_S0007", template["probe_id"])


if __name__ == "__main__":
    unittest.main()
