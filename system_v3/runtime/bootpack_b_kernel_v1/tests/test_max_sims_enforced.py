import json
import shutil
import sys
import unittest
import uuid
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from a1_a0_b_sim_runner import run_loop
from a1_strategy import validate_strategy
from zip_protocol_v2_writer import write_zip_protocol_v2


class TestMaxSimsEnforced(unittest.TestCase):
    def test_runner_enforces_budget_max_sims_packet_mode(self) -> None:
        """
        Packet mode uses raw A1_STRATEGY_v1 without replay coercion, so we can
        validate that the runner caps SIM execution to budget.max_sims.
        """
        run_id = f"TEST_MAX_SIMS_PACKET_{uuid.uuid4().hex[:8]}"
        bootpack_root = BASE
        system_v3_root = bootpack_root.parents[1]
        runs_root = system_v3_root / "runs"
        run_dir = runs_root / run_id
        inbox = run_dir / "a1_inbox"

        # Ensure a fresh start without relying on run_loop(clean=True), because
        # packet mode requires us to stage an inbox capsule before running.
        shutil.rmtree(run_dir, ignore_errors=True)
        current_state = runs_root / "_CURRENT_STATE"
        (current_state / "state.json").unlink(missing_ok=True)
        (current_state / "sequence_state.json").unlink(missing_ok=True)

        inbox.mkdir(parents=True, exist_ok=True)

        max_sims = 2
        candidates: list[dict] = []

        def sim_candidate(*, cid: str, probe: str, evidence: str, tier: str, family: str, tc: str, negative_class: str = "") -> dict:
            def_fields = [
                {"field_id": "F_EVID", "name": "REQUIRES_EVIDENCE", "value_kind": "TOKEN", "value": evidence},
                {"field_id": "F_SIMID", "name": "SIM_ID", "value_kind": "TOKEN", "value": cid},
                {"field_id": "F_TIER", "name": "TIER", "value_kind": "TOKEN", "value": tier},
                {"field_id": "F_FAM", "name": "FAMILY", "value_kind": "TOKEN", "value": family},
                {"field_id": "F_TC", "name": "TARGET_CLASS", "value_kind": "TOKEN", "value": tc},
                {"field_id": "F_PK", "name": "PROBE_KIND", "value_kind": "TOKEN", "value": "A1_GENERATED"},
                {"field_id": "F_TRACK", "name": "BRANCH_TRACK", "value_kind": "TOKEN", "value": f"TRACK_{cid}"},
            ]
            if negative_class:
                def_fields.append({"field_id": "F_NEG", "name": "NEGATIVE_CLASS", "value_kind": "TOKEN", "value": negative_class})
                # Marker for deterministic negative kill semantics.
                if negative_class == "COMMUTATIVE_ASSUMPTION":
                    def_fields.append({"field_id": "F_MARK", "name": "ASSUME_COMMUTATIVE", "value_kind": "TOKEN", "value": "TRUE"})
            return {
                "item_class": "SPEC_HYP",
                "id": cid,
                "kind": "SIM_SPEC",
                "requires": [probe],
                "def_fields": def_fields,
                "asserts": [
                    {"assert_id": "A_PROBE", "token_class": "PROBE_TOKEN", "token": f"PT_{probe}"},
                    {"assert_id": "A_EVID", "token_class": "EVIDENCE_TOKEN", "token": evidence},
                ],
                "operator_id": "OP_BIND_SIM",
            }

        # Use a known term key in IDs so probes pass and emit evidence deterministically.
        base = "S_DM_MAX_SIMS_DENSITY_MATRIX"
        candidates.append(sim_candidate(cid=f"{base}_TGT", probe="P_DM_MAX_01", evidence="E_DM_MAX_01", tier="T0_ATOM", family="BASELINE", tc="TC_MAX_SIMS"))
        candidates.append(sim_candidate(cid=f"{base}_ALT_B", probe="P_DM_MAX_02", evidence="E_DM_MAX_02", tier="T1_COMPOUND", family="BOUNDARY_SWEEP", tc="TC_MAX_SIMS"))
        candidates.append(sim_candidate(cid=f"{base}_ALT_P", probe="P_DM_MAX_03", evidence="E_DM_MAX_03", tier="T1_COMPOUND", family="PERTURBATION", tc="TC_MAX_SIMS"))
        candidates.append(sim_candidate(cid=f"{base}_ALT_S", probe="P_DM_MAX_04", evidence="E_DM_MAX_04", tier="T2_OPERATOR", family="COMPOSITION_STRESS", tc="TC_MAX_SIMS"))
        candidates.append(
            sim_candidate(
                cid=f"{base}_ALT_NEG",
                probe="P_DM_MAX_05",
                evidence="E_DM_MAX_05",
                tier="T2_OPERATOR",
                family="ADVERSARIAL_NEG",
                tc="TC_MAX_SIMS",
                negative_class="COMMUTATIVE_ASSUMPTION",
            )
        )

        strategy = {
            "schema": "A1_STRATEGY_v1",
            "strategy_id": "STRAT_MAX_SIMS_PACKET",
            "inputs": {
                "state_hash": "0" * 64,
                "fuel_slice_hashes": [],
                "bootpack_rules_hash": "1" * 64,
                "pinned_ruleset_sha256": None,
                "pinned_megaboot_sha256": None,
            },
            "budget": {"max_items": 64, "max_sims": max_sims},
            "policy": {
                "forbid_fields": ["confidence", "probability", "embedding", "hidden_prompt", "raw_text"],
                "overlay_ban_terms": [],
                "require_try_to_fail": True,
            },
            "targets": [candidates[0]],
            "alternatives": candidates[1:],
            "sims": {"positive": [{"sim_id": "SIM_POS_MAX", "binds_to": candidates[0]["id"]}], "negative": []},
            "self_audit": {
                "strategy_hash": "",
                "compile_lane_digest": "",
                "candidate_count": 1,
                "alternative_count": 4,
                "operator_ids_used": ["OP_BIND_SIM"],
            },
        }
        errors = validate_strategy(strategy)
        self.assertEqual([], errors)

        packet_path = inbox / "000001_A1_TO_A0_STRATEGY_ZIP.zip"
        write_zip_protocol_v2(
            out_path=packet_path,
            header={
                "zip_type": "A1_TO_A0_STRATEGY_ZIP",
                "direction": "FORWARD",
                "source_layer": "A1",
                "target_layer": "A0",
                "run_id": run_id,
                "sequence": 1,
                "created_utc": "1980-01-01T00:00:00Z",
                # Per ZIP_PROTOCOL_v2 validator policy: compiler_version is only
                # populated for A0-emitted capsules. Other layers must emit "".
                "compiler_version": "",
            },
            payload_json={"A1_STRATEGY_v1.json": strategy},
        )

        # Run exactly one step; max_sims must cap SIM execution.
        run_loop(
            strategy_path=bootpack_root / "a1_strategies" / "sample_strategy.json",
            steps=1,
            run_id=run_id,
            a1_source="packet",
            a1_model="",
            a1_timeout_sec=1,
            clean=False,
            retain_diagnostics=False,
        )

        state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        sim_registry_count = len(state.get("sim_registry", {}) or {})
        sim_results_count = len(state.get("sim_results", {}) or {})
        evidence_pending_count = len(state.get("evidence_pending", {}) or {})

        self.assertGreaterEqual(sim_registry_count, max_sims + 1)
        self.assertEqual(max_sims, sim_results_count)
        self.assertEqual(sim_registry_count - max_sims, evidence_pending_count)

        shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
