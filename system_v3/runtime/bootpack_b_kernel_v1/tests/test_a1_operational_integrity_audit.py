from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE / "tools"))

from run_a1_operational_integrity_audit import main as audit_main


class TestA1OperationalIntegrityAudit(unittest.TestCase):
    def test_audit_derives_selector_support_metadata_from_legacy_raw_warning_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "RUN_AUDIT_SELECTOR_SUPPORT_LEGACY_001"
            (run_dir / "a1_sandbox" / "outgoing").mkdir(parents=True, exist_ok=True)
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)

            state = {
                "term_registry": {},
                "graveyard": {},
                "kill_log": [],
                "sim_results": {},
                "sim_registry": {
                    "SIM_T0": {"tier": "T0_ATOM"},
                    "SIM_T1": {"tier": "T1_COMPOUND"},
                    "SIM_T2": {"tier": "T2_OPERATOR"},
                    "SIM_T3": {"tier": "T3_STRUCTURE"},
                    "SIM_T6": {"tier": "T6_WHOLE_SYSTEM"},
                },
            }
            (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

            strategy = {
                "schema": "A1_STRATEGY_v1",
                "strategy_id": "STRAT_AUDIT_SUPPORT_LEGACY",
                "inputs": {
                    "state_hash": "0" * 64,
                    "fuel_slice_hashes": [],
                    "bootpack_rules_hash": "1" * 64,
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
                        "def_fields": [
                            {"field_id": "F1", "name": "REQUIRES_EVIDENCE", "value_kind": "TOKEN", "value": "E_BIND_ALPHA"},
                            {"field_id": "F2", "name": "PROBE_TERM", "value_kind": "TOKEN", "value": "density_entropy"},
                        ],
                        "asserts": [{"assert_id": "A1", "token_class": "EVIDENCE_TOKEN", "token": "E_BIND_ALPHA"}],
                        "operator_id": "OP_BIND_SIM",
                    }
                ],
                "alternatives": [],
                "sims": {"positive": [], "negative": []},
                "self_audit": {
                    "strategy_hash": "",
                    "compile_lane_digest": "",
                    "candidate_count": 1,
                    "alternative_count": 0,
                    "operator_ids_used": ["OP_BIND_SIM"],
                },
                "target_terms": ["density_entropy"],
                "family_terms": ["density_entropy", "partial_trace"],
                "admissibility": {
                    "executable_head": ["density_entropy"],
                    "process_audit": {
                        "warnings": [
                            "noncanon mining witnesses are present; keep them support-side and do not treat them as executable head authority"
                        ],
                        "mining_support_terms": ["correlation_polarity"],
                        "mining_artifact_inputs": ["/tmp/export_candidate_pack.json"],
                        "mining_negative_pressure_count": 1,
                    },
                },
            }
            strategy_path = run_dir / "a1_sandbox" / "outgoing" / "000001_A1_STRATEGY_v1__PACK_SELECTOR.json"
            strategy_path.write_text(json.dumps(strategy), encoding="utf-8")

            rc = audit_main(
                [
                    "--run-dir",
                    str(run_dir),
                    "--min-canonical-terms",
                    "0",
                    "--min-graveyard-count",
                    "0",
                    "--min-kill-token-diversity",
                    "0",
                    "--min-avg-unique-rescue-from",
                    "0",
                ]
            )
            self.assertEqual(0, rc)

            report = json.loads((run_dir / "reports" / "a1_operational_integrity_audit_report.json").read_text(encoding="utf-8"))
            metrics = report["metrics"]
            self.assertEqual(["noncanon_mining_support_only"], metrics["selector_warning_codes"])
            self.assertEqual(["support_boundary"], metrics["selector_warning_categories"])
            self.assertEqual(1, metrics["selector_warning_count"])
            self.assertTrue(metrics["selector_support_warning_present"])

    def test_audit_reports_selector_support_metadata_without_promoting_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "RUN_AUDIT_SELECTOR_SUPPORT_001"
            (run_dir / "a1_sandbox" / "outgoing").mkdir(parents=True, exist_ok=True)
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)

            state = {
                "term_registry": {},
                "graveyard": {},
                "kill_log": [],
                "sim_results": {},
                "sim_registry": {
                    "SIM_T0": {"tier": "T0_ATOM"},
                    "SIM_T1": {"tier": "T1_COMPOUND"},
                    "SIM_T2": {"tier": "T2_OPERATOR"},
                    "SIM_T3": {"tier": "T3_STRUCTURE"},
                    "SIM_T6": {"tier": "T6_WHOLE_SYSTEM"},
                },
            }
            (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

            strategy = {
                "schema": "A1_STRATEGY_v1",
                "strategy_id": "STRAT_AUDIT_SUPPORT",
                "inputs": {
                    "state_hash": "0" * 64,
                    "fuel_slice_hashes": [],
                    "bootpack_rules_hash": "1" * 64,
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
                        "def_fields": [
                            {"field_id": "F1", "name": "REQUIRES_EVIDENCE", "value_kind": "TOKEN", "value": "E_BIND_ALPHA"},
                            {"field_id": "F2", "name": "PROBE_TERM", "value_kind": "TOKEN", "value": "density_entropy"},
                        ],
                        "asserts": [{"assert_id": "A1", "token_class": "EVIDENCE_TOKEN", "token": "E_BIND_ALPHA"}],
                        "operator_id": "OP_BIND_SIM",
                    }
                ],
                "alternatives": [],
                "sims": {"positive": [], "negative": []},
                "self_audit": {
                    "strategy_hash": "",
                    "compile_lane_digest": "",
                    "candidate_count": 1,
                    "alternative_count": 0,
                    "operator_ids_used": ["OP_BIND_SIM"],
                },
                "target_terms": ["density_entropy"],
                "family_terms": ["density_entropy", "partial_trace"],
                "admissibility": {
                    "executable_head": ["density_entropy"],
                    "process_audit": {
                        "warnings": [
                            "selector used external cold-core path; run-local regeneration provenance is bypassed"
                        ],
                        "warning_count": 2,
                        "warning_codes": ["external_cold_core_path", "noncanon_mining_support_only"],
                        "warning_categories": ["cold_core_provenance", "support_boundary"],
                        "support_warning_present": True,
                        "mining_support_terms": ["correlation_polarity", "partial_trace"],
                        "mining_artifact_inputs": ["/tmp/export_candidate_pack.json", "/tmp/fuel_digest.json"],
                        "mining_negative_pressure_count": 1,
                    },
                },
            }
            strategy_path = run_dir / "a1_sandbox" / "outgoing" / "000001_A1_STRATEGY_v1__PACK_SELECTOR.json"
            strategy_path.write_text(json.dumps(strategy), encoding="utf-8")

            rc = audit_main(
                [
                    "--run-dir",
                    str(run_dir),
                    "--min-canonical-terms",
                    "0",
                    "--min-graveyard-count",
                    "0",
                    "--min-kill-token-diversity",
                    "0",
                    "--min-avg-unique-rescue-from",
                    "0",
                ]
            )
            self.assertEqual(0, rc)

            report_path = run_dir / "reports" / "a1_operational_integrity_audit_report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))
            metrics = report["metrics"]

            self.assertEqual("PASS", report["status"])
            self.assertEqual(1, metrics["selector_support_strategy_count"])
            self.assertEqual("a1_sandbox_outgoing", metrics["selector_support_source_surface"])
            self.assertEqual(2, metrics["selector_warning_count"])
            self.assertEqual(
                ["external_cold_core_path", "noncanon_mining_support_only"],
                metrics["selector_warning_codes"],
            )
            self.assertEqual(
                ["cold_core_provenance", "support_boundary"],
                metrics["selector_warning_categories"],
            )
            self.assertEqual(["correlation_polarity", "partial_trace"], metrics["selector_mining_support_terms"])
            self.assertEqual(2, metrics["selector_mining_artifact_input_count"])
            self.assertEqual(1, metrics["selector_max_mining_negative_pressure_count"])
            self.assertTrue(metrics["selector_support_warning_present"])


if __name__ == "__main__":
    unittest.main()
