import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from a0_compiler import compile_export_block
from state import KernelState


def _sim_candidate(
    item_id: str,
    probe_id: str,
    evidence_token: str,
    sim_id: str,
    target_class: str,
    tier: str = "T0_ATOM",
    family: str = "BASELINE",
) -> dict:
    return {
        "item_class": "SPEC_HYP",
        "id": item_id,
        "kind": "SIM_SPEC",
        "requires": [probe_id],
        "def_fields": [
            {"field_id": "F1", "name": "REQUIRES_EVIDENCE", "value_kind": "TOKEN", "value": evidence_token},
            {"field_id": "F2", "name": "SIM_ID", "value_kind": "TOKEN", "value": sim_id},
            {"field_id": "F3", "name": "TIER", "value_kind": "TOKEN", "value": tier},
            {"field_id": "F4", "name": "FAMILY", "value_kind": "TOKEN", "value": family},
            {"field_id": "F5", "name": "TARGET_CLASS", "value_kind": "TOKEN", "value": target_class},
        ],
        "asserts": [
            {"assert_id": "A1", "token_class": "PROBE_TOKEN", "token": f"PT_{probe_id}"},
            {"assert_id": "A2", "token_class": "EVIDENCE_TOKEN", "token": evidence_token},
        ],
        "operator_id": "OP_BIND_SIM",
    }


def _strategy(targets: list[dict], alternatives: list[dict]) -> dict:
    return {
        "schema": "A1_STRATEGY_v1",
        "strategy_id": "STRAT_DIGEST_TEST",
        "inputs": {
            "state_hash": "0" * 64,
            "fuel_slice_hashes": ["1" * 64],
            "bootpack_rules_hash": "2" * 64,
            "pinned_ruleset_sha256": None,
            "pinned_megaboot_sha256": None,
        },
        "budget": {"max_items": 10, "max_sims": 5},
        "policy": {
            "forbid_fields": ["confidence", "probability", "embedding", "hidden_prompt", "raw_text"],
            "overlay_ban_terms": [],
            "require_try_to_fail": False,
        },
        "targets": targets,
        "alternatives": alternatives,
        "sims": {"positive": [], "negative": []},
        "self_audit": {
            "strategy_hash": "",
            "compile_lane_digest": "",
            "candidate_count": len(targets),
            "alternative_count": len(alternatives),
            "operator_ids_used": ["OP_BIND_SIM"],
        },
    }


def _existing_survivor_spec(item_id: str, probe_id: str, evidence_token: str, sim_id: str, target_class: str) -> str:
    return "\n".join(
        [
            f"SPEC_HYP {item_id}",
            f"SPEC_KIND {item_id} CORR SIM_SPEC",
            f"REQUIRES {item_id} CORR {probe_id}",
            f"DEF_FIELD {item_id} CORR REQUIRES_EVIDENCE {evidence_token}",
            f"DEF_FIELD {item_id} CORR SIM_ID {sim_id}",
            f"DEF_FIELD {item_id} CORR TIER T0_ATOM",
            f"DEF_FIELD {item_id} CORR FAMILY BASELINE",
            f"DEF_FIELD {item_id} CORR TARGET_CLASS {target_class}",
            f"ASSERT {item_id} CORR EXISTS PROBE_TOKEN PT_{probe_id}",
            f"ASSERT {item_id} CORR EXISTS EVIDENCE_TOKEN {evidence_token}",
        ]
    )


class TestA0StructuralDigest(unittest.TestCase):
    def test_rejects_monoculture_when_all_candidates_identical(self):
        state = KernelState()
        strategy = _strategy(
            targets=[
                _sim_candidate(
                    item_id="S_TARGET_ALPHA",
                    probe_id="P_BIND_ALPHA",
                    evidence_token="E_ALPHA",
                    sim_id="SIM_ALPHA",
                    target_class="TC_ALPHA",
                )
            ],
            alternatives=[
                _sim_candidate(
                    item_id="S_ALT_ALPHA_CLONE",
                    probe_id="P_BIND_ALPHA",
                    evidence_token="E_ALPHA",
                    sim_id="SIM_ALPHA",
                    target_class="TC_ALPHA",
                )
            ],
        )

        with self.assertRaisesRegex(ValueError, r"insufficient_structural_variance:all_candidates_identical"):
            compile_export_block(state=state, strategy=strategy, canonical_state_hash=state.hash(), step=1, prior_tags=[])

    def test_allows_distinct_alternative_cross_basin(self):
        state = KernelState()
        strategy = _strategy(
            targets=[
                _sim_candidate(
                    item_id="S_TARGET_ALPHA",
                    probe_id="P_BIND_ALPHA",
                    evidence_token="E_ALPHA",
                    sim_id="SIM_ALPHA",
                    target_class="TC_ALPHA",
                )
            ],
            alternatives=[
                _sim_candidate(
                    item_id="S_ALT_BETA",
                    probe_id="P_BIND_BETA",
                    evidence_token="E_BETA",
                    sim_id="SIM_BETA",
                    target_class="TC_BETA",
                    family="PERTURBATION",
                )
            ],
        )

        compiled = compile_export_block(state=state, strategy=strategy, canonical_state_hash=state.hash(), step=1, prior_tags=[])
        self.assertEqual("A0_COMPILER_v2", compiled["report"]["compiler_version"])
        digests = {row["digest"] for row in compiled["report"]["candidate_structural_digests"]}
        self.assertGreaterEqual(len(digests), 2)

    def test_rejects_target_with_survivor_structural_digest_duplicate(self):
        state = KernelState()
        state.survivor_ledger["S_EXISTING"] = {
            "class": "SPEC_HYP",
            "status": "ACTIVE",
            "metadata": {},
            "item_text": _existing_survivor_spec(
                item_id="S_EXISTING",
                probe_id="P_BIND_ALPHA",
                evidence_token="E_ALPHA",
                sim_id="SIM_ALPHA",
                target_class="TC_ALPHA",
            ),
        }

        strategy = _strategy(
            targets=[
                _sim_candidate(
                    item_id="S_TARGET_DUPLICATE",
                    probe_id="P_BIND_ALPHA",
                    evidence_token="E_ALPHA",
                    sim_id="SIM_ALPHA",
                    target_class="TC_ALPHA",
                )
            ],
            alternatives=[],
        )

        with self.assertRaisesRegex(ValueError, r"duplicate_target_structural_digest:S_TARGET_DUPLICATE"):
            compile_export_block(state=state, strategy=strategy, canonical_state_hash=state.hash(), step=1, prior_tags=[])

    def test_allows_survivor_duplicate_in_alternative_lane(self):
        state = KernelState()
        state.survivor_ledger["S_EXISTING"] = {
            "class": "SPEC_HYP",
            "status": "ACTIVE",
            "metadata": {},
            "item_text": _existing_survivor_spec(
                item_id="S_EXISTING",
                probe_id="P_BIND_ALPHA",
                evidence_token="E_ALPHA",
                sim_id="SIM_ALPHA",
                target_class="TC_ALPHA",
            ),
        }

        strategy = _strategy(
            targets=[
                _sim_candidate(
                    item_id="S_TARGET_UNIQUE",
                    probe_id="P_BIND_BETA",
                    evidence_token="E_BETA",
                    sim_id="SIM_BETA",
                    target_class="TC_BETA",
                )
            ],
            alternatives=[
                _sim_candidate(
                    item_id="S_ALT_DUPLICATE",
                    probe_id="P_BIND_ALPHA",
                    evidence_token="E_ALPHA",
                    sim_id="SIM_ALPHA",
                    target_class="TC_ALPHA",
                )
            ],
        )

        compiled = compile_export_block(state=state, strategy=strategy, canonical_state_hash=state.hash(), step=1, prior_tags=[])
        self.assertEqual("A0_COMPILER_v2", compiled["report"]["compiler_version"])
        self.assertEqual(2, len(compiled["report"]["candidate_structural_digests"]))


if __name__ == "__main__":
    unittest.main()
