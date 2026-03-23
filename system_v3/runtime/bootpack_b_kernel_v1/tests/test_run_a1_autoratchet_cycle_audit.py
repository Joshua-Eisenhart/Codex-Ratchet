from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE / "tools"))

from run_a1_autoratchet_cycle_audit import build_report


class TestRunA1AutoratchetCycleAudit(unittest.TestCase):
    def _write_strategy_zip(self, zip_path: Path, payload: dict) -> None:
        zip_path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("A1_STRATEGY_v1.json", json.dumps(payload))

    def test_build_report_passes_for_minimal_valid_surface(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)
            (run_dir / "zip_packets").mkdir(parents=True, exist_ok=True)
            (run_dir / "zip_packets" / "000001_A1_TO_A0_STRATEGY_ZIP.zip").write_text("zip", encoding="utf-8")
            (run_dir / "summary.json").write_text(json.dumps({"steps_completed": 2}), encoding="utf-8")
            (run_dir / "campaign_summary.json").write_text(
                json.dumps(
                    {
                        "steps_executed": 2,
                        "planning_mode": "compatibility_profile_scaffold",
                        "compatibility_goal_profile": "core",
                        "state_metrics": {
                            "killed_unique_count": 5,
                            "sim_registry_count": 12,
                            "canonical_term_count": 3,
                        },
                        "a1_semantic_gate": {"status": "FAIL"},
                    }
                ),
                encoding="utf-8",
            )

            report = build_report(run_dir=run_dir, min_graveyard_count=1)
            self.assertEqual("PASS", report["status"])
            self.assertEqual("compatibility_profile_scaffold", report["planning_mode"])
            self.assertEqual("core", report["compatibility_goal_profile"])
            self.assertTrue(report["legacy_goal_profile_mode"])

    def test_build_report_fails_when_family_slice_strategy_metadata_mismatches(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)
            (run_dir / "zip_packets").mkdir(parents=True, exist_ok=True)
            family_slice_path = run_dir / "family_slice.json"
            family_slice_path.write_text(
                json.dumps(
                    {
                        "slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1",
                        "family_id": "substrate_base_family",
                        "run_mode": "SCAFFOLD_PROOF",
                        "required_lanes": [
                            "STEELMAN",
                            "ALT_FORMALISM",
                            "BOUNDARY_REPAIR",
                            "ADVERSARIAL_NEG",
                            "RESCUER",
                        ],
                        "family_admissibility_hints": {"strategy_head_terms": ["probe_operator"]},
                        "negative_emphasis_classes": ["PRIMITIVE_EQUALS"],
                        "required_negative_classes": ["PRIMITIVE_EQUALS", "COMMUTATIVE_ASSUMPTION"],
                        "term_math_surfaces": {
                            "probe_operator": {
                                "objects": "density matrix operator",
                                "operations": "partial trace tensor unitary",
                                "invariants": "finite operator",
                                "domain": "density matrix",
                                "codomain": "operator space",
                            }
                        },
                        "sim_hooks": {
                            "required_sim_families": [
                                "BASELINE",
                                "BOUNDARY_SWEEP",
                                "PERTURBATION",
                                "ADVERSARIAL_NEG",
                                "COMPOSITION_STRESS",
                            ],
                            "required_probe_terms": ["density_matrix", "probe_operator"],
                            "probe_term_overrides": {"probe_operator": "probe_operator"},
                            "term_sim_tiers": {"probe_operator": "T2_OPERATOR"},
                            "sim_family_tiers": {
                                "BOUNDARY_SWEEP": "T1_COMPOUND",
                                "PERTURBATION": "T2_OPERATOR",
                                "ADVERSARIAL_NEG": "T1_COMPOUND",
                                "COMPOSITION_STRESS": "T3_STRUCTURE",
                            },
                            "recovery_sim_families": [
                                "BOUNDARY_SWEEP",
                                "PERTURBATION",
                                "COMPOSITION_STRESS",
                            ],
                            "expected_tier_floor": "T0_ATOM",
                        },
                    }
                ),
                encoding="utf-8",
            )
            self._write_strategy_zip(
                run_dir / "zip_packets" / "000001_A1_TO_A0_STRATEGY_ZIP.zip",
                {
                    "schema": "A1_STRATEGY_v1",
                    "inputs": {"family_slice_id": "WRONG_SLICE_ID"},
                    "self_audit": {
                        "family_slice_required_lanes": ["STEELMAN"],
                        "family_slice_strategy_head_terms": ["density_matrix"],
                        "family_slice_required_negative_classes": ["COMMUTATIVE_ASSUMPTION"],
                        "family_slice_math_surface_terms": [],
                        "family_slice_target_class_prefix": "TC_WRONG_PREFIX",
                        "strategy_target_class": "TC_WRONG_PREFIX_DENSITY_MATRIX",
                        "graveyard_negative_classes_used": ["COMMUTATIVE_ASSUMPTION"],
                        "goal_term": "probe_operator",
                        "goal_probe_term": "density_matrix",
                        "goal_probe_source": "global_default",
                        "goal_sim_tier": "T1_COMPOUND",
                        "family_slice_recovery_sim_families": [
                            "BOUNDARY_SWEEP",
                            "PERTURBATION",
                            "COMPOSITION_STRESS",
                        ],
                        "family_slice_rescue_source_limit": 6,
                        "sim_families_used": ["BASELINE"],
                        "sim_family_tier_map": {"BASELINE": ["T0_ATOM"]},
                        "rescue_sim_families_used": [],
                        "rescue_source_count": 0,
                        "sim_family_operator_map": {"BASELINE": ["OP_BIND_SIM"]},
                        "operator_policy_sources": ["ENUM_REGISTRY_v1"],
                        "goal_negative_class": "CLASSICAL_TIME",
                    },
                },
            )
            (run_dir / "summary.json").write_text(json.dumps({"steps_completed": 2}), encoding="utf-8")
            (run_dir / "campaign_summary.json").write_text(
                json.dumps(
                    {
                        "steps_executed": 2,
                        "goal_source": "family_slice",
                        "planning_mode": "family_slice_controlled",
                        "family_slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1",
                        "family_slice_json": str(family_slice_path),
                        "state_metrics": {
                            "killed_unique_count": 5,
                            "sim_registry_count": 12,
                            "canonical_term_count": 3,
                        },
                        "a1_semantic_gate": {"status": "PASS"},
                    }
                ),
                encoding="utf-8",
            )

            report = build_report(run_dir=run_dir, min_graveyard_count=1)
            self.assertEqual("FAIL", report["status"])
            self.assertTrue(report["family_slice_expected"])
            self.assertEqual("family_slice_controlled", report["planning_mode"])
            self.assertFalse(report["legacy_goal_profile_mode"])
            self.assertEqual("FAIL", report["family_slice_obligations_status"])

    def test_build_report_passes_when_family_slice_negative_metadata_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)
            (run_dir / "zip_packets").mkdir(parents=True, exist_ok=True)
            family_slice_path = run_dir / "family_slice.json"
            family_slice_path.write_text(
                json.dumps(
                    {
                        "slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1",
                        "family_id": "substrate_base_family",
                        "run_mode": "SCAFFOLD_PROOF",
                        "required_lanes": [
                            "STEELMAN",
                            "ALT_FORMALISM",
                            "BOUNDARY_REPAIR",
                            "ADVERSARIAL_NEG",
                            "RESCUER",
                        ],
                        "family_admissibility_hints": {"strategy_head_terms": ["probe_operator"]},
                        "negative_emphasis_classes": ["PRIMITIVE_EQUALS"],
                        "required_negative_classes": ["PRIMITIVE_EQUALS", "COMMUTATIVE_ASSUMPTION"],
                        "term_math_surfaces": {
                            "probe_operator": {
                                "objects": "density matrix operator",
                                "operations": "partial trace tensor unitary",
                                "invariants": "finite operator",
                                "domain": "density matrix",
                                "codomain": "operator space",
                            }
                        },
                        "sim_hooks": {
                            "required_sim_families": [
                                "BASELINE",
                                "BOUNDARY_SWEEP",
                                "PERTURBATION",
                                "ADVERSARIAL_NEG",
                                "COMPOSITION_STRESS",
                            ],
                            "required_probe_terms": ["density_matrix", "probe_operator"],
                            "probe_term_overrides": {"probe_operator": "probe_operator"},
                            "term_sim_tiers": {"probe_operator": "T2_OPERATOR"},
                            "sim_family_tiers": {
                                "BOUNDARY_SWEEP": "T1_COMPOUND",
                                "PERTURBATION": "T2_OPERATOR",
                                "ADVERSARIAL_NEG": "T1_COMPOUND",
                                "COMPOSITION_STRESS": "T3_STRUCTURE",
                            },
                            "recovery_sim_families": [
                                "BOUNDARY_SWEEP",
                                "PERTURBATION",
                                "COMPOSITION_STRESS",
                            ],
                            "expected_tier_floor": "T0_ATOM",
                        },
                    }
                ),
                encoding="utf-8",
            )
            self._write_strategy_zip(
                run_dir / "zip_packets" / "000001_A1_TO_A0_STRATEGY_ZIP.zip",
                {
                    "schema": "A1_STRATEGY_v1",
                    "inputs": {"family_slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1"},
                    "self_audit": {
                        "family_slice_required_lanes": [
                            "STEELMAN",
                            "ALT_FORMALISM",
                            "BOUNDARY_REPAIR",
                            "ADVERSARIAL_NEG",
                            "RESCUER",
                        ],
                        "family_slice_strategy_head_terms": ["probe_operator"],
                        "family_slice_required_negative_classes": [
                            "PRIMITIVE_EQUALS",
                            "COMMUTATIVE_ASSUMPTION",
                        ],
                        "family_slice_math_surface_terms": ["probe_operator"],
                        "family_slice_target_class_prefix": "TC_FAMILY_SUBSTRATE_BASE_FAMILY",
                        "strategy_target_class": "TC_FAMILY_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                        "graveyard_negative_classes_used": [],
                        "goal_term": "probe_operator",
                        "goal_probe_term": "probe_operator",
                        "goal_probe_source": "family_slice_override",
                        "goal_sim_tier": "T2_OPERATOR",
                        "family_slice_recovery_sim_families": [
                            "BOUNDARY_SWEEP",
                            "PERTURBATION",
                            "COMPOSITION_STRESS",
                        ],
                        "family_slice_rescue_source_limit": 6,
                        "sim_families_used": [
                            "BASELINE",
                            "BOUNDARY_SWEEP",
                            "PERTURBATION",
                            "COMPOSITION_STRESS",
                            "ADVERSARIAL_NEG",
                        ],
                        "sim_family_tier_map": {
                            "BASELINE": ["T0_ATOM"],
                            "BOUNDARY_SWEEP": ["T1_COMPOUND"],
                            "PERTURBATION": ["T2_OPERATOR"],
                            "COMPOSITION_STRESS": ["T3_STRUCTURE"],
                            "ADVERSARIAL_NEG": ["T1_COMPOUND"],
                        },
                        "rescue_sim_families_used": [],
                        "rescue_source_count": 0,
                        "sim_family_operator_map": {
                            "BASELINE": ["OP_BIND_SIM"],
                            "BOUNDARY_SWEEP": ["OP_REPAIR_DEF_FIELD"],
                            "PERTURBATION": ["OP_MUTATE_LEXEME"],
                            "COMPOSITION_STRESS": ["OP_REORDER_DEPENDENCIES"],
                            "ADVERSARIAL_NEG": ["OP_NEG_SIM_EXPAND"],
                        },
                        "operator_policy_sources": [
                            "ENUM_REGISTRY_v1",
                            "A1_REPAIR_OPERATOR_MAPPING_v1",
                        ],
                        "goal_negative_class": "PRIMITIVE_EQUALS",
                    },
                },
            )
            (run_dir / "summary.json").write_text(json.dumps({"steps_completed": 2}), encoding="utf-8")
            (run_dir / "campaign_summary.json").write_text(
                json.dumps(
                    {
                        "steps_executed": 2,
                        "goal_source": "family_slice",
                        "planning_mode": "family_slice_controlled",
                        "family_slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1",
                        "family_slice_json": str(family_slice_path),
                        "state_metrics": {
                            "killed_unique_count": 5,
                            "sim_registry_count": 12,
                            "canonical_term_count": 3,
                        },
                        "a1_semantic_gate": {"status": "PASS"},
                    }
                ),
                encoding="utf-8",
            )

            report = build_report(run_dir=run_dir, min_graveyard_count=1)
            self.assertEqual("PASS", report["status"])
            self.assertEqual("PASS", report["family_slice_obligations_status"])

    def test_build_report_rejects_global_default_probe_source_for_family_slice(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)
            (run_dir / "zip_packets").mkdir(parents=True, exist_ok=True)
            family_slice_path = run_dir / "family_slice.json"
            family_slice_path.write_text(
                json.dumps(
                    {
                        "slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1",
                        "family_id": "substrate_base_family",
                        "run_mode": "SCAFFOLD_PROOF",
                        "required_lanes": [
                            "STEELMAN",
                            "ALT_FORMALISM",
                            "BOUNDARY_REPAIR",
                            "ADVERSARIAL_NEG",
                            "RESCUER",
                        ],
                        "family_admissibility_hints": {"strategy_head_terms": ["probe_operator"]},
                        "negative_emphasis_classes": ["PRIMITIVE_EQUALS"],
                        "required_negative_classes": ["PRIMITIVE_EQUALS", "COMMUTATIVE_ASSUMPTION"],
                        "sim_hooks": {
                            "required_sim_families": [
                                "BASELINE",
                                "BOUNDARY_SWEEP",
                                "PERTURBATION",
                                "ADVERSARIAL_NEG",
                                "COMPOSITION_STRESS",
                            ],
                            "required_probe_terms": ["density_matrix", "probe_operator"],
                            "probe_term_overrides": {"probe_operator": "probe_operator"},
                            "term_sim_tiers": {"probe_operator": "T2_OPERATOR"},
                            "sim_family_tiers": {
                                "BOUNDARY_SWEEP": "T1_COMPOUND",
                                "PERTURBATION": "T2_OPERATOR",
                                "ADVERSARIAL_NEG": "T1_COMPOUND",
                                "COMPOSITION_STRESS": "T3_STRUCTURE",
                            },
                            "recovery_sim_families": [
                                "BOUNDARY_SWEEP",
                                "PERTURBATION",
                                "COMPOSITION_STRESS",
                            ],
                            "expected_tier_floor": "T0_ATOM",
                        },
                    }
                ),
                encoding="utf-8",
            )
            self._write_strategy_zip(
                run_dir / "zip_packets" / "000001_A1_TO_A0_STRATEGY_ZIP.zip",
                {
                    "schema": "A1_STRATEGY_v1",
                    "inputs": {"family_slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1"},
                    "self_audit": {
                        "family_slice_required_lanes": [
                            "STEELMAN",
                            "ALT_FORMALISM",
                            "BOUNDARY_REPAIR",
                            "ADVERSARIAL_NEG",
                            "RESCUER",
                        ],
                        "family_slice_strategy_head_terms": ["probe_operator"],
                        "family_slice_required_negative_classes": [
                            "PRIMITIVE_EQUALS",
                            "COMMUTATIVE_ASSUMPTION",
                        ],
                        "family_slice_target_class_prefix": "TC_FAMILY_SUBSTRATE_BASE_FAMILY",
                        "strategy_target_class": "TC_FAMILY_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                        "graveyard_negative_classes_used": [],
                        "goal_term": "probe_operator",
                        "goal_probe_term": "probe_operator",
                        "goal_probe_source": "global_default",
                        "goal_sim_tier": "T2_OPERATOR",
                        "family_slice_recovery_sim_families": [
                            "BOUNDARY_SWEEP",
                            "PERTURBATION",
                            "COMPOSITION_STRESS",
                        ],
                        "family_slice_rescue_source_limit": 6,
                        "sim_families_used": [
                            "BASELINE",
                            "BOUNDARY_SWEEP",
                            "PERTURBATION",
                            "COMPOSITION_STRESS",
                            "ADVERSARIAL_NEG",
                        ],
                        "sim_family_tier_map": {
                            "BASELINE": ["T0_ATOM"],
                            "BOUNDARY_SWEEP": ["T1_COMPOUND"],
                            "PERTURBATION": ["T2_OPERATOR"],
                            "COMPOSITION_STRESS": ["T3_STRUCTURE"],
                            "ADVERSARIAL_NEG": ["T1_COMPOUND"],
                        },
                        "rescue_sim_families_used": [],
                        "rescue_source_count": 0,
                        "sim_family_operator_map": {
                            "BASELINE": ["OP_BIND_SIM"],
                            "BOUNDARY_SWEEP": ["OP_REPAIR_DEF_FIELD"],
                            "PERTURBATION": ["OP_MUTATE_LEXEME"],
                            "COMPOSITION_STRESS": ["OP_REORDER_DEPENDENCIES"],
                            "ADVERSARIAL_NEG": ["OP_NEG_SIM_EXPAND"],
                        },
                        "operator_policy_sources": [
                            "ENUM_REGISTRY_v1",
                            "A1_REPAIR_OPERATOR_MAPPING_v1",
                        ],
                        "goal_negative_class": "PRIMITIVE_EQUALS",
                    },
                },
            )
            (run_dir / "summary.json").write_text(json.dumps({"steps_completed": 2}), encoding="utf-8")
            (run_dir / "campaign_summary.json").write_text(
                json.dumps(
                    {
                        "steps_executed": 2,
                        "goal_source": "family_slice",
                        "planning_mode": "family_slice_controlled",
                        "family_slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1",
                        "family_slice_json": str(family_slice_path),
                        "state_metrics": {
                            "killed_unique_count": 5,
                            "sim_registry_count": 12,
                            "canonical_term_count": 3,
                        },
                        "a1_semantic_gate": {"status": "PASS"},
                    }
                ),
                encoding="utf-8",
            )

            report = build_report(run_dir=run_dir, min_graveyard_count=1)
            self.assertEqual("FAIL", report["status"])
            self.assertEqual("FAIL", report["family_slice_obligations_status"])
            check = next(
                item
                for item in report["checks"]
                if item["check_id"] == "AUTORATCHET_FAMILY_SLICE_GOAL_PROBE_SOURCE_OWNED"
            )
            self.assertEqual("FAIL", check["status"])

    def test_build_report_requires_graveyard_negative_classes_for_graveyard_validity_slice(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)
            (run_dir / "zip_packets").mkdir(parents=True, exist_ok=True)
            family_slice_path = run_dir / "family_slice.json"
            family_slice_path.write_text(
                json.dumps(
                    {
                        "slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1",
                        "family_id": "entropy_bridge_family",
                        "run_mode": "GRAVEYARD_VALIDITY",
                        "required_lanes": [
                            "STEELMAN",
                            "ALT_FORMALISM",
                            "BOUNDARY_REPAIR",
                            "ADVERSARIAL_NEG",
                            "RESCUER",
                        ],
                        "family_admissibility_hints": {"strategy_head_terms": ["correlation_polarity"]},
                        "negative_emphasis_classes": ["CLASSICAL_TIME"],
                        "required_negative_classes": ["CLASSICAL_TIME", "COMMUTATIVE_ASSUMPTION"],
                        "sim_hooks": {
                            "required_sim_families": [
                                "BASELINE",
                                "BOUNDARY_SWEEP",
                                "PERTURBATION",
                                "ADVERSARIAL_NEG",
                                "COMPOSITION_STRESS",
                            ],
                            "required_probe_terms": ["correlation_polarity"],
                            "probe_term_overrides": {"correlation_polarity": "correlation_polarity"},
                            "term_sim_tiers": {"correlation_polarity": "T3_STRUCTURE"},
                            "sim_family_tiers": {
                                "BOUNDARY_SWEEP": "T1_COMPOUND",
                                "PERTURBATION": "T2_OPERATOR",
                                "ADVERSARIAL_NEG": "T1_COMPOUND",
                                "COMPOSITION_STRESS": "T3_STRUCTURE",
                            },
                            "recovery_sim_families": [
                                "BOUNDARY_SWEEP",
                                "PERTURBATION",
                                "COMPOSITION_STRESS",
                            ],
                            "expected_tier_floor": "T0_ATOM",
                        },
                    }
                ),
                encoding="utf-8",
            )
            self._write_strategy_zip(
                run_dir / "zip_packets" / "000001_A1_TO_A0_STRATEGY_ZIP.zip",
                {
                    "schema": "A1_STRATEGY_v1",
                    "inputs": {"family_slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1"},
                    "self_audit": {
                        "family_slice_required_lanes": [
                            "STEELMAN",
                            "ALT_FORMALISM",
                            "BOUNDARY_REPAIR",
                            "ADVERSARIAL_NEG",
                            "RESCUER",
                        ],
                        "family_slice_strategy_head_terms": ["correlation_polarity"],
                        "family_slice_required_negative_classes": [
                            "CLASSICAL_TIME",
                            "COMMUTATIVE_ASSUMPTION",
                        ],
                        "family_slice_target_class_prefix": "TC_FAMILY_ENTROPY_BRIDGE_FAMILY",
                        "strategy_target_class": "TC_FAMILY_ENTROPY_BRIDGE_FAMILY_CORRELATION_POLARITY",
                        "graveyard_negative_classes_used": ["CLASSICAL_TIME"],
                        "goal_term": "correlation_polarity",
                        "goal_probe_term": "correlation_polarity",
                        "goal_probe_source": "family_slice_override",
                        "goal_sim_tier": "T3_STRUCTURE",
                        "family_slice_recovery_sim_families": [
                            "BOUNDARY_SWEEP",
                            "PERTURBATION",
                            "COMPOSITION_STRESS",
                        ],
                        "family_slice_rescue_source_limit": 6,
                        "sim_families_used": [
                            "BASELINE",
                            "BOUNDARY_SWEEP",
                            "PERTURBATION",
                            "COMPOSITION_STRESS",
                            "ADVERSARIAL_NEG",
                        ],
                        "sim_family_tier_map": {
                            "BASELINE": ["T3_STRUCTURE"],
                            "BOUNDARY_SWEEP": ["T1_COMPOUND"],
                            "PERTURBATION": ["T2_OPERATOR"],
                            "COMPOSITION_STRESS": ["T3_STRUCTURE"],
                            "ADVERSARIAL_NEG": ["T1_COMPOUND"],
                        },
                        "rescue_sim_families_used": [],
                        "rescue_source_count": 0,
                        "sim_family_operator_map": {
                            "BASELINE": ["OP_BIND_SIM"],
                            "BOUNDARY_SWEEP": ["OP_REPAIR_DEF_FIELD"],
                            "PERTURBATION": ["OP_MUTATE_LEXEME"],
                            "COMPOSITION_STRESS": ["OP_REORDER_DEPENDENCIES"],
                            "ADVERSARIAL_NEG": ["OP_NEG_SIM_EXPAND"],
                        },
                        "operator_policy_sources": [
                            "ENUM_REGISTRY_v1",
                            "A1_REPAIR_OPERATOR_MAPPING_v1",
                        ],
                        "goal_negative_class": "CLASSICAL_TIME",
                    },
                },
            )
            (run_dir / "summary.json").write_text(json.dumps({"steps_completed": 2}), encoding="utf-8")
            (run_dir / "campaign_summary.json").write_text(
                json.dumps(
                    {
                        "steps_executed": 2,
                        "goal_source": "family_slice",
                        "planning_mode": "family_slice_controlled",
                        "family_slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1",
                        "family_slice_json": str(family_slice_path),
                        "state_metrics": {
                            "killed_unique_count": 5,
                            "sim_registry_count": 12,
                            "canonical_term_count": 3,
                        },
                        "a1_semantic_gate": {"status": "PASS"},
                    }
                ),
                encoding="utf-8",
            )

            report = build_report(run_dir=run_dir, min_graveyard_count=1)
            self.assertEqual("FAIL", report["status"])
            self.assertEqual("FAIL", report["family_slice_obligations_status"])

    def test_build_report_accepts_visible_graveyard_negative_expansion_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)
            (run_dir / "zip_packets").mkdir(parents=True, exist_ok=True)
            family_slice_path = run_dir / "family_slice.json"
            family_slice_path.write_text(
                json.dumps(
                    {
                        "slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1",
                        "family_id": "entropy_bridge_family",
                        "run_mode": "GRAVEYARD_VALIDITY",
                        "required_lanes": [
                            "STEELMAN",
                            "ALT_FORMALISM",
                            "BOUNDARY_REPAIR",
                            "ADVERSARIAL_NEG",
                            "RESCUER",
                        ],
                        "family_admissibility_hints": {"strategy_head_terms": ["correlation_polarity"]},
                        "negative_emphasis_classes": ["CLASSICAL_TIME"],
                        "required_negative_classes": ["CLASSICAL_TIME", "COMMUTATIVE_ASSUMPTION"],
                        "rescue_start_conditions": {
                            "graveyard_negative_expansion_limit": 1,
                            "graveyard_first_max_items": 20,
                            "graveyard_first_max_sims": 28,
                        },
                        "sim_hooks": {
                            "required_sim_families": [
                                "BASELINE",
                                "BOUNDARY_SWEEP",
                                "PERTURBATION",
                                "ADVERSARIAL_NEG",
                                "COMPOSITION_STRESS",
                            ],
                            "required_probe_terms": ["correlation_polarity"],
                            "probe_term_overrides": {"correlation_polarity": "correlation_polarity"},
                            "term_sim_tiers": {"correlation_polarity": "T3_STRUCTURE"},
                            "sim_family_tiers": {
                                "BOUNDARY_SWEEP": "T1_COMPOUND",
                                "PERTURBATION": "T2_OPERATOR",
                                "ADVERSARIAL_NEG": "T1_COMPOUND",
                                "COMPOSITION_STRESS": "T3_STRUCTURE",
                            },
                            "recovery_sim_families": [
                                "BOUNDARY_SWEEP",
                                "PERTURBATION",
                                "COMPOSITION_STRESS",
                            ],
                            "expected_tier_floor": "T0_ATOM",
                        },
                    }
                ),
                encoding="utf-8",
            )
            self._write_strategy_zip(
                run_dir / "zip_packets" / "000001_A1_TO_A0_STRATEGY_ZIP.zip",
                {
                    "schema": "A1_STRATEGY_v1",
                    "inputs": {"family_slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1"},
                    "budget": {"max_items": 20, "max_sims": 28},
                    "self_audit": {
                        "debate_mode": "graveyard_first",
                        "family_slice_required_lanes": [
                            "STEELMAN",
                            "ALT_FORMALISM",
                            "BOUNDARY_REPAIR",
                            "ADVERSARIAL_NEG",
                            "RESCUER",
                        ],
                        "family_slice_strategy_head_terms": ["correlation_polarity"],
                        "family_slice_required_negative_classes": [
                            "CLASSICAL_TIME",
                            "COMMUTATIVE_ASSUMPTION",
                        ],
                        "family_slice_target_class_prefix": "TC_FAMILY_ENTROPY_BRIDGE_FAMILY",
                        "strategy_target_class": "TC_FAMILY_ENTROPY_BRIDGE_FAMILY_CORRELATION_POLARITY",
                        "graveyard_negative_classes_used": ["CLASSICAL_TIME"],
                        "family_slice_graveyard_negative_expansion_limit": 1,
                        "goal_term": "correlation_polarity",
                        "goal_probe_term": "correlation_polarity",
                        "goal_probe_source": "family_slice_override",
                        "goal_sim_tier": "T3_STRUCTURE",
                        "family_slice_recovery_sim_families": [
                            "BOUNDARY_SWEEP",
                            "PERTURBATION",
                            "COMPOSITION_STRESS",
                        ],
                        "family_slice_rescue_source_limit": 6,
                        "family_slice_budget_max_items": 20,
                        "family_slice_budget_max_sims": 28,
                        "family_slice_budget_source": "family_slice_override",
                        "sim_families_used": [
                            "BASELINE",
                            "BOUNDARY_SWEEP",
                            "PERTURBATION",
                            "COMPOSITION_STRESS",
                            "ADVERSARIAL_NEG",
                        ],
                        "sim_family_tier_map": {
                            "BASELINE": ["T3_STRUCTURE"],
                            "BOUNDARY_SWEEP": ["T1_COMPOUND"],
                            "PERTURBATION": ["T2_OPERATOR"],
                            "COMPOSITION_STRESS": ["T3_STRUCTURE"],
                            "ADVERSARIAL_NEG": ["T1_COMPOUND"],
                        },
                        "rescue_sim_families_used": [],
                        "rescue_source_count": 0,
                        "sim_family_operator_map": {
                            "BASELINE": ["OP_BIND_SIM"],
                            "BOUNDARY_SWEEP": ["OP_REPAIR_DEF_FIELD"],
                            "PERTURBATION": ["OP_MUTATE_LEXEME"],
                            "COMPOSITION_STRESS": ["OP_REORDER_DEPENDENCIES"],
                            "ADVERSARIAL_NEG": ["OP_NEG_SIM_EXPAND"],
                        },
                        "operator_policy_sources": [
                            "ENUM_REGISTRY_v1",
                            "A1_REPAIR_OPERATOR_MAPPING_v1",
                        ],
                        "goal_negative_class": "CLASSICAL_TIME",
                    },
                },
            )
            (run_dir / "summary.json").write_text(json.dumps({"steps_completed": 2}), encoding="utf-8")
            (run_dir / "campaign_summary.json").write_text(
                json.dumps(
                    {
                        "steps_executed": 2,
                        "goal_source": "family_slice",
                        "planning_mode": "family_slice_controlled",
                        "family_slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1",
                        "family_slice_json": str(family_slice_path),
                        "state_metrics": {
                            "killed_unique_count": 5,
                            "sim_registry_count": 12,
                            "canonical_term_count": 3,
                        },
                        "a1_semantic_gate": {"status": "PASS"},
                    }
                ),
                encoding="utf-8",
            )

            report = build_report(run_dir=run_dir, min_graveyard_count=1)
            self.assertEqual("PASS", report["status"])

    def test_build_report_accepts_visible_lane_minimums_and_branch_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)
            (run_dir / "zip_packets").mkdir(parents=True, exist_ok=True)
            family_slice_path = run_dir / "family_slice.json"
            family_slice_path.write_text(
                json.dumps(
                    {
                        "slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1",
                        "family_id": "substrate_base_family",
                        "run_mode": "SCAFFOLD_PROOF",
                        "required_lanes": [
                            "STEELMAN",
                            "ALT_FORMALISM",
                            "BOUNDARY_REPAIR",
                            "ADVERSARIAL_NEG",
                            "RESCUER",
                        ],
                        "lane_minimums": {
                            "STEELMAN": {"min_branches": 1},
                            "ALT_FORMALISM": {"min_branches": 1},
                            "BOUNDARY_REPAIR": {"min_branches": 1},
                            "ADVERSARIAL_NEG": {"min_branches": 1},
                            "RESCUER": {"min_branches": 1},
                        },
                        "primary_branch_requirement": "steelman branch required",
                        "alternative_branch_requirement": "alt branch required",
                        "negative_branch_requirement": "negative branch required",
                        "rescue_branch_requirement": "rescue branch required",
                        "lineage_requirements": [
                            "branch_id",
                            "parent_branch_id",
                            "feedback_refs",
                            "rescue_linkage",
                        ],
                        "rescue_lineage_required": True,
                        "family_admissibility_hints": {"strategy_head_terms": ["probe_operator"]},
                        "negative_emphasis_classes": ["PRIMITIVE_EQUALS"],
                        "required_negative_classes": ["PRIMITIVE_EQUALS", "COMMUTATIVE_ASSUMPTION"],
                        "sim_hooks": {
                            "required_sim_families": [
                                "BASELINE",
                                "BOUNDARY_SWEEP",
                                "PERTURBATION",
                                "ADVERSARIAL_NEG",
                                "COMPOSITION_STRESS",
                            ],
                            "required_probe_terms": ["density_matrix", "probe_operator"],
                            "probe_term_overrides": {"probe_operator": "probe_operator"},
                            "term_sim_tiers": {"probe_operator": "T2_OPERATOR"},
                            "sim_family_tiers": {
                                "BOUNDARY_SWEEP": "T1_COMPOUND",
                                "PERTURBATION": "T2_OPERATOR",
                                "ADVERSARIAL_NEG": "T1_COMPOUND",
                                "COMPOSITION_STRESS": "T3_STRUCTURE",
                            },
                            "recovery_sim_families": [
                                "BOUNDARY_SWEEP",
                                "PERTURBATION",
                                "COMPOSITION_STRESS",
                            ],
                            "expected_tier_floor": "T0_ATOM",
                        },
                    }
                ),
                encoding="utf-8",
            )
            self._write_strategy_zip(
                run_dir / "zip_packets" / "000001_A1_TO_A0_STRATEGY_ZIP.zip",
                {
                    "schema": "A1_STRATEGY_v1",
                    "inputs": {"family_slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1"},
                    "budget": {"max_items": 32, "max_sims": 48},
                    "targets": [
                        {
                            "id": "SIM_PRIMARY_PROBE_OPERATOR",
                            "kind": "SIM_SPEC",
                            "def_fields": [
                                {"name": "FAMILY", "value": "BASELINE"},
                                {"name": "REQUIRES_EVIDENCE", "value": "E_CANON_PROBE_OPERATOR"},
                                {"name": "BRANCH_ID", "value": "SIM_PRIMARY_PROBE_OPERATOR"},
                                {
                                    "name": "BRANCH_GROUP",
                                    "value": "BG_FAMILY_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                                },
                                {
                                    "name": "BRANCH_TRACK",
                                    "value": "FAMILY_SLICE_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                                },
                                {"name": "PARENT_BRANCH_ID", "value": "NONE"},
                                {"name": "FEEDBACK_REFS", "value": "[\"E_CANON_PROBE_OPERATOR\"]"},
                            ],
                        }
                    ],
                    "alternatives": [
                        {
                            "id": "SIM_RESCUE_SCAFFOLD_0001",
                            "kind": "SIM_SPEC",
                            "def_fields": [
                                {"name": "FAMILY", "value": "BOUNDARY_SWEEP"},
                                {"name": "RESCUE_MODE", "value": "SCAFFOLD_ATTACHMENT"},
                                {
                                    "name": "RESCUE_LINKAGE",
                                    "value": "SCAFFOLD::BOUNDARY_SWEEP::helper_bootstrap_debt_on_probe::1",
                                },
                                {"name": "BRANCH_ID", "value": "SIM_RESCUE_SCAFFOLD_0001"},
                                {
                                    "name": "BRANCH_GROUP",
                                    "value": "BG_FAMILY_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                                },
                                {
                                    "name": "BRANCH_TRACK",
                                    "value": "FAMILY_SLICE_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR_RESCUE_SCAFFOLD_BOUNDARY_SWEEP_1",
                                },
                                {"name": "PARENT_BRANCH_ID", "value": "SIM_POS_PROBE_OPERATOR"},
                                {
                                    "name": "FEEDBACK_REFS",
                                    "value": "[\"E_RESCUE_SCAFFOLD_1_BOUNDARY_SWEEP_PROBE_OPERATOR\"]",
                                },
                                {"name": "RESCUE_FAILURE_MODE", "value": "helper_bootstrap_debt_on_probe"},
                            ],
                        }
                    ],
                    "self_audit": {
                        "family_slice_required_lanes": [
                            "STEELMAN",
                            "ALT_FORMALISM",
                            "BOUNDARY_REPAIR",
                            "ADVERSARIAL_NEG",
                            "RESCUER",
                        ],
                        "family_slice_lane_minimums": {
                            "STEELMAN": 1,
                            "ALT_FORMALISM": 1,
                            "BOUNDARY_REPAIR": 1,
                            "ADVERSARIAL_NEG": 1,
                            "RESCUER": 1,
                        },
                        "family_slice_branch_requirements": {
                            "primary": "steelman branch required",
                            "alternative": "alt branch required",
                            "negative": "negative branch required",
                            "rescue": "rescue branch required",
                        },
                        "family_slice_lineage_requirements": [
                            "branch_id",
                            "parent_branch_id",
                            "feedback_refs",
                            "rescue_linkage",
                        ],
                        "family_slice_rescue_lineage_required": True,
                        "branch_parentage_map": {
                            "SIM_PRIMARY_PROBE_OPERATOR": "NONE",
                        },
                        "branch_group_map": {
                            "SIM_PRIMARY_PROBE_OPERATOR": "BG_FAMILY_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                            "SIM_RESCUE_SCAFFOLD_0001": "BG_FAMILY_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                        },
                        "branch_groups_used": ["BG_FAMILY_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR"],
                        "branch_track_map": {
                            "SIM_PRIMARY_PROBE_OPERATOR": "FAMILY_SLICE_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                            "SIM_RESCUE_SCAFFOLD_0001": "FAMILY_SLICE_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR_RESCUE_SCAFFOLD_BOUNDARY_SWEEP_1",
                        },
                        "branch_tracks_used": [
                            "FAMILY_SLICE_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                            "FAMILY_SLICE_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR_RESCUE_SCAFFOLD_BOUNDARY_SWEEP_1",
                        ],
                        "root_branch_ids": ["SIM_PRIMARY_PROBE_OPERATOR"],
                        "branch_child_counts": {"NONE": 1},
                        "lane_branch_counts": {
                            "STEELMAN": 1,
                            "ALT_FORMALISM": 2,
                            "BOUNDARY_REPAIR": 1,
                            "ADVERSARIAL_NEG": 1,
                            "RESCUER": 1,
                        },
                        "family_slice_strategy_head_terms": ["probe_operator"],
                        "family_slice_required_negative_classes": [
                            "PRIMITIVE_EQUALS",
                            "COMMUTATIVE_ASSUMPTION",
                        ],
                        "family_slice_math_surface_terms": [],
                        "family_slice_target_class_prefix": "TC_FAMILY_SUBSTRATE_BASE_FAMILY",
                        "strategy_target_class": "TC_FAMILY_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                        "graveyard_negative_classes_used": [],
                        "goal_term": "probe_operator",
                        "goal_probe_term": "probe_operator",
                        "goal_probe_source": "family_slice_override",
                        "goal_sim_tier": "T2_OPERATOR",
                        "family_slice_recovery_sim_families": [
                            "BOUNDARY_SWEEP",
                            "PERTURBATION",
                            "COMPOSITION_STRESS",
                        ],
                        "family_slice_rescue_source_limit": 6,
                        "sim_families_used": [
                            "BASELINE",
                            "BOUNDARY_SWEEP",
                            "PERTURBATION",
                            "ADVERSARIAL_NEG",
                            "COMPOSITION_STRESS",
                        ],
                        "sim_family_tier_map": {
                            "BASELINE": ["T0_ATOM"],
                            "BOUNDARY_SWEEP": ["T1_COMPOUND"],
                            "PERTURBATION": ["T2_OPERATOR"],
                            "ADVERSARIAL_NEG": ["T1_COMPOUND"],
                            "COMPOSITION_STRESS": ["T3_STRUCTURE"],
                        },
                        "rescue_sim_families_used": ["BOUNDARY_SWEEP"],
                        "rescue_linkages_used": [
                            "SCAFFOLD::BOUNDARY_SWEEP::helper_bootstrap_debt_on_probe::1"
                        ],
                        "rescue_source_count": 0,
                        "sim_family_operator_map": {
                            "BASELINE": ["OP_BIND_SIM"],
                            "BOUNDARY_SWEEP": ["OP_REPAIR_DEF_FIELD"],
                            "PERTURBATION": ["OP_MUTATE_LEXEME"],
                            "ADVERSARIAL_NEG": ["OP_NEG_SIM_EXPAND"],
                            "COMPOSITION_STRESS": ["OP_REORDER_DEPENDENCIES"],
                        },
                        "operator_policy_sources": ["ENUM_REGISTRY_v1", "A1_REPAIR_OPERATOR_MAPPING_v1"],
                        "goal_negative_class": "PRIMITIVE_EQUALS",
                        "debate_mode": "balanced",
                        "family_slice_budget_max_items": 32,
                        "family_slice_budget_max_sims": 48,
                        "family_slice_budget_source": "planner_default",
                    },
                },
            )
            (run_dir / "summary.json").write_text(json.dumps({"steps_completed": 2}), encoding="utf-8")
            (run_dir / "campaign_summary.json").write_text(
                json.dumps(
                    {
                        "steps_executed": 2,
                        "goal_source": "family_slice",
                        "planning_mode": "family_slice_controlled",
                        "family_slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1",
                        "family_slice_json": str(family_slice_path),
                        "state_metrics": {
                            "killed_unique_count": 5,
                            "sim_registry_count": 12,
                            "canonical_term_count": 3,
                        },
                        "a1_semantic_gate": {"status": "PASS"},
                    }
                ),
                encoding="utf-8",
            )

            report = build_report(run_dir=run_dir, min_graveyard_count=1)
            self.assertEqual("PASS", report["status"])
            self.assertEqual("PASS", report["family_slice_obligations_status"])
            check = next(
                item
                for item in report["checks"]
                if item["check_id"] == "AUTORATCHET_FAMILY_SLICE_BRANCH_LINEAGE_VISIBLE"
            )
            self.assertEqual("PASS", check["status"])
            check = next(
                item
                for item in report["checks"]
                if item["check_id"] == "AUTORATCHET_FAMILY_SLICE_BRANCH_PARENTAGE_VISIBLE"
            )
            self.assertEqual("PASS", check["status"])
            check = next(
                item
                for item in report["checks"]
                if item["check_id"] == "AUTORATCHET_FAMILY_SLICE_BRANCH_GROUPS_VISIBLE"
            )
            self.assertEqual("PASS", check["status"])
            check = next(
                item
                for item in report["checks"]
                if item["check_id"] == "AUTORATCHET_FAMILY_SLICE_BRANCH_TRACKS_VISIBLE"
            )
            self.assertEqual("PASS", check["status"])
            check = next(
                item
                for item in report["checks"]
                if item["check_id"] == "AUTORATCHET_FAMILY_SLICE_BUDGET_VISIBLE"
            )
            self.assertEqual("PASS", check["status"])

    def test_build_report_fails_when_lane_minimum_is_visible_but_not_satisfied(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)
            (run_dir / "zip_packets").mkdir(parents=True, exist_ok=True)
            family_slice_path = run_dir / "family_slice.json"
            family_slice_path.write_text(
                json.dumps(
                    {
                        "slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1",
                        "family_id": "substrate_base_family",
                        "run_mode": "SCAFFOLD_PROOF",
                        "required_lanes": [
                            "STEELMAN",
                            "ALT_FORMALISM",
                            "BOUNDARY_REPAIR",
                            "ADVERSARIAL_NEG",
                            "RESCUER",
                        ],
                        "lane_minimums": {
                            "STEELMAN": {"min_branches": 1},
                            "ALT_FORMALISM": {"min_branches": 1},
                            "BOUNDARY_REPAIR": {"min_branches": 1},
                            "ADVERSARIAL_NEG": {"min_branches": 1},
                            "RESCUER": {"min_branches": 1},
                        },
                        "family_admissibility_hints": {"strategy_head_terms": ["probe_operator"]},
                        "negative_emphasis_classes": ["PRIMITIVE_EQUALS"],
                        "required_negative_classes": ["PRIMITIVE_EQUALS", "COMMUTATIVE_ASSUMPTION"],
                        "sim_hooks": {
                            "required_sim_families": [
                                "BASELINE",
                                "BOUNDARY_SWEEP",
                                "PERTURBATION",
                                "ADVERSARIAL_NEG",
                                "COMPOSITION_STRESS",
                            ],
                            "required_probe_terms": ["density_matrix", "probe_operator"],
                            "probe_term_overrides": {"probe_operator": "probe_operator"},
                            "term_sim_tiers": {"probe_operator": "T2_OPERATOR"},
                            "sim_family_tiers": {
                                "BOUNDARY_SWEEP": "T1_COMPOUND",
                                "PERTURBATION": "T2_OPERATOR",
                                "ADVERSARIAL_NEG": "T1_COMPOUND",
                                "COMPOSITION_STRESS": "T3_STRUCTURE",
                            },
                            "recovery_sim_families": [
                                "BOUNDARY_SWEEP",
                                "PERTURBATION",
                                "COMPOSITION_STRESS",
                            ],
                            "expected_tier_floor": "T0_ATOM",
                        },
                    }
                ),
                encoding="utf-8",
            )
            self._write_strategy_zip(
                run_dir / "zip_packets" / "000001_A1_TO_A0_STRATEGY_ZIP.zip",
                {
                    "schema": "A1_STRATEGY_v1",
                    "inputs": {"family_slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1"},
                    "budget": {"max_items": 32, "max_sims": 48},
                    "targets": [
                        {
                            "id": "SIM_PRIMARY_PROBE_OPERATOR",
                            "kind": "SIM_SPEC",
                            "def_fields": [
                                {"name": "FAMILY", "value": "BASELINE"},
                                {"name": "REQUIRES_EVIDENCE", "value": "E_CANON_PROBE_OPERATOR"},
                                {"name": "BRANCH_ID", "value": "SIM_PRIMARY_PROBE_OPERATOR"},
                                {
                                    "name": "BRANCH_GROUP",
                                    "value": "BG_FAMILY_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                                },
                                {
                                    "name": "BRANCH_TRACK",
                                    "value": "FAMILY_SLICE_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                                },
                                {"name": "PARENT_BRANCH_ID", "value": "NONE"},
                                {"name": "FEEDBACK_REFS", "value": "[\"E_CANON_PROBE_OPERATOR\"]"},
                            ],
                        }
                    ],
                    "self_audit": {
                        "debate_mode": "balanced",
                        "family_slice_required_lanes": [
                            "STEELMAN",
                            "ALT_FORMALISM",
                            "BOUNDARY_REPAIR",
                            "ADVERSARIAL_NEG",
                            "RESCUER",
                        ],
                        "family_slice_lane_minimums": {
                            "STEELMAN": 1,
                            "ALT_FORMALISM": 1,
                            "BOUNDARY_REPAIR": 1,
                            "ADVERSARIAL_NEG": 1,
                            "RESCUER": 1,
                        },
                        "family_slice_branch_requirements": {
                            "primary": "steelman branch required",
                            "alternative": "alt branch required",
                            "negative": "negative branch required",
                            "rescue": "rescue branch required",
                        },
                        "lane_branch_counts": {
                            "STEELMAN": 1,
                            "ALT_FORMALISM": 2,
                            "BOUNDARY_REPAIR": 1,
                            "ADVERSARIAL_NEG": 1,
                            "RESCUER": 0,
                        },
                        "family_slice_strategy_head_terms": ["probe_operator"],
                        "family_slice_required_negative_classes": [
                            "PRIMITIVE_EQUALS",
                            "COMMUTATIVE_ASSUMPTION",
                        ],
                        "family_slice_math_surface_terms": [],
                        "family_slice_target_class_prefix": "TC_FAMILY_SUBSTRATE_BASE_FAMILY",
                        "strategy_target_class": "TC_FAMILY_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                        "graveyard_negative_classes_used": [],
                        "goal_term": "probe_operator",
                        "goal_probe_term": "probe_operator",
                        "goal_probe_source": "family_slice_override",
                        "goal_sim_tier": "T2_OPERATOR",
                        "family_slice_recovery_sim_families": [
                            "BOUNDARY_SWEEP",
                            "PERTURBATION",
                            "COMPOSITION_STRESS",
                        ],
                        "family_slice_rescue_source_limit": 6,
                        "family_slice_budget_max_items": 32,
                        "family_slice_budget_max_sims": 48,
                        "family_slice_budget_source": "planner_default",
                        "sim_families_used": [
                            "BASELINE",
                            "BOUNDARY_SWEEP",
                            "PERTURBATION",
                            "ADVERSARIAL_NEG",
                            "COMPOSITION_STRESS",
                        ],
                        "sim_family_tier_map": {
                            "BASELINE": ["T0_ATOM"],
                            "BOUNDARY_SWEEP": ["T1_COMPOUND"],
                            "PERTURBATION": ["T2_OPERATOR"],
                            "ADVERSARIAL_NEG": ["T1_COMPOUND"],
                            "COMPOSITION_STRESS": ["T3_STRUCTURE"],
                        },
                        "rescue_sim_families_used": [],
                        "rescue_source_count": 0,
                        "branch_track_map": {
                            "SIM_PRIMARY_PROBE_OPERATOR": "FAMILY_SLICE_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                        },
                        "branch_tracks_used": [
                            "FAMILY_SLICE_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                        ],
                        "sim_family_operator_map": {
                            "BASELINE": ["OP_BIND_SIM"],
                            "BOUNDARY_SWEEP": ["OP_REPAIR_DEF_FIELD"],
                            "PERTURBATION": ["OP_MUTATE_LEXEME"],
                            "ADVERSARIAL_NEG": ["OP_NEG_SIM_EXPAND"],
                            "COMPOSITION_STRESS": ["OP_REORDER_DEPENDENCIES"],
                        },
                        "operator_policy_sources": ["ENUM_REGISTRY_v1", "A1_REPAIR_OPERATOR_MAPPING_v1"],
                        "goal_negative_class": "PRIMITIVE_EQUALS",
                    },
                },
            )
            (run_dir / "summary.json").write_text(json.dumps({"steps_completed": 2}), encoding="utf-8")
            (run_dir / "campaign_summary.json").write_text(
                json.dumps(
                    {
                        "steps_executed": 2,
                        "goal_source": "family_slice",
                        "planning_mode": "family_slice_controlled",
                        "family_slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1",
                        "family_slice_json": str(family_slice_path),
                        "state_metrics": {
                            "killed_unique_count": 5,
                            "sim_registry_count": 12,
                            "canonical_term_count": 3,
                        },
                        "a1_semantic_gate": {"status": "PASS"},
                    }
                ),
                encoding="utf-8",
            )

            report = build_report(run_dir=run_dir, min_graveyard_count=1)
            self.assertEqual("FAIL", report["status"])
            check = next(
                item
                for item in report["checks"]
                if item["check_id"] == "AUTORATCHET_FAMILY_SLICE_LANE_MINIMUMS_SATISFIED"
            )
            self.assertEqual("FAIL", check["status"])

    def test_build_report_accepts_visible_balanced_budget_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)
            (run_dir / "zip_packets").mkdir(parents=True, exist_ok=True)
            family_slice_path = run_dir / "family_slice.json"
            family_slice_path.write_text(
                json.dumps(
                    {
                        "slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1",
                        "family_id": "substrate_base_family",
                        "run_mode": "SCAFFOLD_PROOF",
                        "required_lanes": [
                            "STEELMAN",
                            "ALT_FORMALISM",
                            "BOUNDARY_REPAIR",
                            "ADVERSARIAL_NEG",
                            "RESCUER",
                        ],
                        "family_admissibility_hints": {"strategy_head_terms": ["probe_operator"]},
                        "negative_emphasis_classes": ["PRIMITIVE_EQUALS"],
                        "required_negative_classes": ["PRIMITIVE_EQUALS", "COMMUTATIVE_ASSUMPTION"],
                        "rescue_start_conditions": {
                            "balanced_max_items": 18,
                            "balanced_max_sims": 22,
                        },
                        "sim_hooks": {
                            "required_sim_families": [
                                "BASELINE",
                                "BOUNDARY_SWEEP",
                                "PERTURBATION",
                                "ADVERSARIAL_NEG",
                                "COMPOSITION_STRESS",
                            ],
                            "required_probe_terms": ["density_matrix", "probe_operator"],
                            "probe_term_overrides": {"probe_operator": "probe_operator"},
                            "term_sim_tiers": {"probe_operator": "T2_OPERATOR"},
                            "sim_family_tiers": {
                                "BOUNDARY_SWEEP": "T1_COMPOUND",
                                "PERTURBATION": "T2_OPERATOR",
                                "ADVERSARIAL_NEG": "T1_COMPOUND",
                                "COMPOSITION_STRESS": "T3_STRUCTURE",
                            },
                            "recovery_sim_families": [
                                "BOUNDARY_SWEEP",
                                "PERTURBATION",
                                "COMPOSITION_STRESS",
                            ],
                            "expected_tier_floor": "T0_ATOM",
                        },
                    }
                ),
                encoding="utf-8",
            )
            self._write_strategy_zip(
                run_dir / "zip_packets" / "000001_A1_TO_A0_STRATEGY_ZIP.zip",
                {
                    "schema": "A1_STRATEGY_v1",
                    "inputs": {"family_slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1"},
                    "budget": {"max_items": 18, "max_sims": 22},
                    "self_audit": {
                        "debate_mode": "balanced",
                        "family_slice_required_lanes": [
                            "STEELMAN",
                            "ALT_FORMALISM",
                            "BOUNDARY_REPAIR",
                            "ADVERSARIAL_NEG",
                            "RESCUER",
                        ],
                        "family_slice_strategy_head_terms": ["probe_operator"],
                        "family_slice_required_negative_classes": [
                            "PRIMITIVE_EQUALS",
                            "COMMUTATIVE_ASSUMPTION",
                        ],
                        "family_slice_math_surface_terms": [],
                        "family_slice_target_class_prefix": "TC_FAMILY_SUBSTRATE_BASE_FAMILY",
                        "strategy_target_class": "TC_FAMILY_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                        "graveyard_negative_classes_used": [],
                        "goal_term": "probe_operator",
                        "goal_probe_term": "probe_operator",
                        "goal_probe_source": "family_slice_override",
                        "goal_sim_tier": "T2_OPERATOR",
                        "family_slice_recovery_sim_families": [
                            "BOUNDARY_SWEEP",
                            "PERTURBATION",
                            "COMPOSITION_STRESS",
                        ],
                        "family_slice_rescue_source_limit": 6,
                        "family_slice_budget_max_items": 18,
                        "family_slice_budget_max_sims": 22,
                        "family_slice_budget_source": "family_slice_override",
                        "sim_families_used": [
                            "BASELINE",
                            "BOUNDARY_SWEEP",
                            "PERTURBATION",
                            "COMPOSITION_STRESS",
                            "ADVERSARIAL_NEG",
                        ],
                        "sim_family_tier_map": {
                            "BASELINE": ["T0_ATOM"],
                            "BOUNDARY_SWEEP": ["T1_COMPOUND"],
                            "PERTURBATION": ["T2_OPERATOR"],
                            "COMPOSITION_STRESS": ["T3_STRUCTURE"],
                            "ADVERSARIAL_NEG": ["T1_COMPOUND"],
                        },
                        "rescue_sim_families_used": [],
                        "rescue_source_count": 0,
                        "sim_family_operator_map": {
                            "BASELINE": ["OP_BIND_SIM"],
                            "BOUNDARY_SWEEP": ["OP_REPAIR_DEF_FIELD"],
                            "PERTURBATION": ["OP_MUTATE_LEXEME"],
                            "COMPOSITION_STRESS": ["OP_REORDER_DEPENDENCIES"],
                            "ADVERSARIAL_NEG": ["OP_NEG_SIM_EXPAND"],
                        },
                        "operator_policy_sources": [
                            "ENUM_REGISTRY_v1",
                            "A1_REPAIR_OPERATOR_MAPPING_v1",
                        ],
                        "goal_negative_class": "PRIMITIVE_EQUALS",
                    },
                },
            )
            (run_dir / "summary.json").write_text(json.dumps({"steps_completed": 2}), encoding="utf-8")
            (run_dir / "campaign_summary.json").write_text(
                json.dumps(
                    {
                        "steps_executed": 2,
                        "goal_source": "family_slice",
                        "planning_mode": "family_slice_controlled",
                        "family_slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1",
                        "family_slice_json": str(family_slice_path),
                        "state_metrics": {
                            "killed_unique_count": 5,
                            "sim_registry_count": 12,
                            "canonical_term_count": 3,
                        },
                        "a1_semantic_gate": {"status": "PASS"},
                    }
                ),
                encoding="utf-8",
            )

            report = build_report(run_dir=run_dir, min_graveyard_count=1)
            self.assertEqual("PASS", report["status"])

    def test_build_report_fails_when_rescue_lineage_required_but_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)
            (run_dir / "zip_packets").mkdir(parents=True, exist_ok=True)
            family_slice_path = run_dir / "family_slice.json"
            family_slice_path.write_text(
                json.dumps(
                    {
                        "slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1",
                        "family_id": "substrate_base_family",
                        "run_mode": "SCAFFOLD_PROOF",
                        "required_lanes": [
                            "STEELMAN",
                            "ALT_FORMALISM",
                            "BOUNDARY_REPAIR",
                            "ADVERSARIAL_NEG",
                            "RESCUER",
                        ],
                        "lane_minimums": {
                            "STEELMAN": {"min_branches": 1},
                            "ALT_FORMALISM": {"min_branches": 1},
                            "BOUNDARY_REPAIR": {"min_branches": 1},
                            "ADVERSARIAL_NEG": {"min_branches": 1},
                            "RESCUER": {"min_branches": 1},
                        },
                        "lineage_requirements": [
                            "branch_id",
                            "parent_branch_id",
                            "feedback_refs",
                            "rescue_linkage",
                        ],
                        "rescue_lineage_required": True,
                        "family_admissibility_hints": {"strategy_head_terms": ["probe_operator"]},
                        "negative_emphasis_classes": ["PRIMITIVE_EQUALS"],
                        "required_negative_classes": ["PRIMITIVE_EQUALS", "COMMUTATIVE_ASSUMPTION"],
                        "sim_hooks": {
                            "required_sim_families": [
                                "BASELINE",
                                "BOUNDARY_SWEEP",
                                "PERTURBATION",
                                "ADVERSARIAL_NEG",
                                "COMPOSITION_STRESS",
                            ],
                            "required_probe_terms": ["density_matrix", "probe_operator"],
                            "probe_term_overrides": {"probe_operator": "probe_operator"},
                            "term_sim_tiers": {"probe_operator": "T2_OPERATOR"},
                            "sim_family_tiers": {
                                "BOUNDARY_SWEEP": "T1_COMPOUND",
                                "PERTURBATION": "T2_OPERATOR",
                                "ADVERSARIAL_NEG": "T1_COMPOUND",
                                "COMPOSITION_STRESS": "T3_STRUCTURE",
                            },
                            "recovery_sim_families": [
                                "BOUNDARY_SWEEP",
                                "PERTURBATION",
                                "COMPOSITION_STRESS",
                            ],
                            "expected_tier_floor": "T0_ATOM",
                        },
                    }
                ),
                encoding="utf-8",
            )
            self._write_strategy_zip(
                run_dir / "zip_packets" / "000001_A1_TO_A0_STRATEGY_ZIP.zip",
                {
                    "schema": "A1_STRATEGY_v1",
                    "inputs": {"family_slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1"},
                    "budget": {"max_items": 32, "max_sims": 48},
                    "targets": [
                        {
                            "id": "SIM_PRIMARY_PROBE_OPERATOR",
                            "kind": "SIM_SPEC",
                            "def_fields": [
                                {"name": "FAMILY", "value": "BASELINE"},
                                {"name": "REQUIRES_EVIDENCE", "value": "E_CANON_PROBE_OPERATOR"},
                                {"name": "BRANCH_ID", "value": "SIM_PRIMARY_PROBE_OPERATOR"},
                                {
                                    "name": "BRANCH_TRACK",
                                    "value": "FAMILY_SLICE_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                                },
                                {"name": "PARENT_BRANCH_ID", "value": "NONE"},
                                {"name": "FEEDBACK_REFS", "value": "[\"E_CANON_PROBE_OPERATOR\"]"},
                            ],
                        }
                    ],
                    "self_audit": {
                        "debate_mode": "balanced",
                        "family_slice_required_lanes": [
                            "STEELMAN",
                            "ALT_FORMALISM",
                            "BOUNDARY_REPAIR",
                            "ADVERSARIAL_NEG",
                            "RESCUER",
                        ],
                        "family_slice_lane_minimums": {
                            "STEELMAN": 1,
                            "ALT_FORMALISM": 1,
                            "BOUNDARY_REPAIR": 1,
                            "ADVERSARIAL_NEG": 1,
                            "RESCUER": 1,
                        },
                        "family_slice_branch_requirements": {
                            "primary": "steelman branch required",
                            "alternative": "alt branch required",
                            "negative": "negative branch required",
                            "rescue": "rescue branch required",
                        },
                        "family_slice_lineage_requirements": [
                            "branch_id",
                            "parent_branch_id",
                            "feedback_refs",
                            "rescue_linkage",
                        ],
                        "family_slice_rescue_lineage_required": True,
                        "branch_parentage_map": {
                            "SIM_PRIMARY_PROBE_OPERATOR": "NONE",
                        },
                        "root_branch_ids": ["SIM_PRIMARY_PROBE_OPERATOR"],
                        "branch_child_counts": {"NONE": 1},
                        "lane_branch_counts": {
                            "STEELMAN": 1,
                            "ALT_FORMALISM": 2,
                            "BOUNDARY_REPAIR": 1,
                            "ADVERSARIAL_NEG": 1,
                            "RESCUER": 1,
                        },
                        "family_slice_strategy_head_terms": ["probe_operator"],
                        "family_slice_required_negative_classes": [
                            "PRIMITIVE_EQUALS",
                            "COMMUTATIVE_ASSUMPTION",
                        ],
                        "family_slice_math_surface_terms": [],
                        "family_slice_target_class_prefix": "TC_FAMILY_SUBSTRATE_BASE_FAMILY",
                        "strategy_target_class": "TC_FAMILY_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                        "graveyard_negative_classes_used": [],
                        "goal_term": "probe_operator",
                        "goal_probe_term": "probe_operator",
                        "goal_probe_source": "family_slice_override",
                        "goal_sim_tier": "T2_OPERATOR",
                        "family_slice_recovery_sim_families": [
                            "BOUNDARY_SWEEP",
                            "PERTURBATION",
                            "COMPOSITION_STRESS",
                        ],
                        "family_slice_rescue_source_limit": 6,
                        "family_slice_budget_max_items": 32,
                        "family_slice_budget_max_sims": 48,
                        "family_slice_budget_source": "planner_default",
                        "sim_families_used": [
                            "BASELINE",
                            "BOUNDARY_SWEEP",
                            "PERTURBATION",
                            "ADVERSARIAL_NEG",
                            "COMPOSITION_STRESS",
                        ],
                        "sim_family_tier_map": {
                            "BASELINE": ["T0_ATOM"],
                            "BOUNDARY_SWEEP": ["T1_COMPOUND"],
                            "PERTURBATION": ["T2_OPERATOR"],
                            "ADVERSARIAL_NEG": ["T1_COMPOUND"],
                            "COMPOSITION_STRESS": ["T3_STRUCTURE"],
                        },
                        "rescue_sim_families_used": ["BOUNDARY_SWEEP"],
                        "rescue_linkages_used": [],
                        "rescue_source_count": 0,
                        "branch_track_map": {
                            "SIM_PRIMARY_PROBE_OPERATOR": "FAMILY_SLICE_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                        },
                        "branch_tracks_used": [
                            "FAMILY_SLICE_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                        ],
                        "sim_family_operator_map": {
                            "BASELINE": ["OP_BIND_SIM"],
                            "BOUNDARY_SWEEP": ["OP_REPAIR_DEF_FIELD"],
                            "PERTURBATION": ["OP_MUTATE_LEXEME"],
                            "ADVERSARIAL_NEG": ["OP_NEG_SIM_EXPAND"],
                            "COMPOSITION_STRESS": ["OP_REORDER_DEPENDENCIES"],
                        },
                        "operator_policy_sources": ["ENUM_REGISTRY_v1", "A1_REPAIR_OPERATOR_MAPPING_v1"],
                        "goal_negative_class": "PRIMITIVE_EQUALS",
                    },
                },
            )
            (run_dir / "summary.json").write_text(json.dumps({"steps_completed": 2}), encoding="utf-8")
            (run_dir / "campaign_summary.json").write_text(
                json.dumps(
                    {
                        "steps_executed": 2,
                        "goal_source": "family_slice",
                        "planning_mode": "family_slice_controlled",
                        "family_slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1",
                        "family_slice_json": str(family_slice_path),
                        "state_metrics": {
                            "killed_unique_count": 5,
                            "sim_registry_count": 12,
                            "canonical_term_count": 3,
                        },
                        "a1_semantic_gate": {"status": "PASS"},
                    }
                ),
                encoding="utf-8",
            )

            report = build_report(run_dir=run_dir, min_graveyard_count=1)
            self.assertEqual("FAIL", report["status"])
            check = next(
                item
                for item in report["checks"]
                if item["check_id"] == "AUTORATCHET_FAMILY_SLICE_RESCUE_LINEAGE_VISIBLE"
            )
            self.assertEqual("FAIL", check["status"])
            check = next(
                item
                for item in report["checks"]
                if item["check_id"] == "AUTORATCHET_FAMILY_SLICE_BRANCH_LINEAGE_VISIBLE"
            )
            self.assertEqual("PASS", check["status"])
            check = next(
                item
                for item in report["checks"]
                if item["check_id"] == "AUTORATCHET_FAMILY_SLICE_BRANCH_PARENTAGE_VISIBLE"
            )
            self.assertEqual("PASS", check["status"])
            check = next(
                item
                for item in report["checks"]
                if item["check_id"] == "AUTORATCHET_FAMILY_SLICE_BUDGET_VISIBLE"
            )
            self.assertEqual("PASS", check["status"])

    def test_build_report_fails_when_branch_parentage_visibility_is_incoherent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)
            (run_dir / "zip_packets").mkdir(parents=True, exist_ok=True)
            family_slice_path = run_dir / "family_slice.json"
            family_slice_path.write_text(
                json.dumps(
                    {
                        "slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1",
                        "family_id": "substrate_base_family",
                        "run_mode": "SCAFFOLD_PROOF",
                        "required_lanes": [
                            "STEELMAN",
                            "ALT_FORMALISM",
                            "BOUNDARY_REPAIR",
                            "ADVERSARIAL_NEG",
                            "RESCUER",
                        ],
                        "lane_minimums": {
                            "STEELMAN": {"min_branches": 1},
                            "ALT_FORMALISM": {"min_branches": 1},
                            "BOUNDARY_REPAIR": {"min_branches": 1},
                            "ADVERSARIAL_NEG": {"min_branches": 1},
                            "RESCUER": {"min_branches": 1},
                        },
                        "lineage_requirements": [
                            "branch_id",
                            "parent_branch_id",
                            "feedback_refs",
                            "rescue_linkage",
                        ],
                        "rescue_lineage_required": False,
                        "family_admissibility_hints": {"strategy_head_terms": ["probe_operator"]},
                        "negative_emphasis_classes": ["PRIMITIVE_EQUALS"],
                        "required_negative_classes": ["PRIMITIVE_EQUALS", "COMMUTATIVE_ASSUMPTION"],
                        "sim_hooks": {
                            "required_sim_families": [
                                "BASELINE",
                                "BOUNDARY_SWEEP",
                                "PERTURBATION",
                                "ADVERSARIAL_NEG",
                                "COMPOSITION_STRESS",
                            ]
                        },
                    }
                ),
                encoding="utf-8",
            )
            self._write_strategy_zip(
                run_dir / "zip_packets" / "000001_A1_TO_A0_STRATEGY_ZIP.zip",
                {
                    "schema": "A1_STRATEGY_v1",
                    "inputs": {"family_slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1"},
                    "budget": {"max_items": 32, "max_sims": 48},
                    "targets": [
                        {
                            "id": "SIM_PRIMARY_PROBE_OPERATOR",
                            "kind": "SIM_SPEC",
                            "def_fields": [
                                {"name": "FAMILY", "value": "BASELINE"},
                                {"name": "REQUIRES_EVIDENCE", "value": "E_CANON_PROBE_OPERATOR"},
                                {"name": "BRANCH_ID", "value": "SIM_PRIMARY_PROBE_OPERATOR"},
                                {"name": "PARENT_BRANCH_ID", "value": "NONE"},
                                {"name": "FEEDBACK_REFS", "value": "[\"E_CANON_PROBE_OPERATOR\"]"},
                            ],
                        }
                    ],
                    "self_audit": {
                        "debate_mode": "balanced",
                        "family_slice_required_lanes": [
                            "STEELMAN",
                            "ALT_FORMALISM",
                            "BOUNDARY_REPAIR",
                            "ADVERSARIAL_NEG",
                            "RESCUER",
                        ],
                        "family_slice_lane_minimums": {
                            "STEELMAN": 1,
                            "ALT_FORMALISM": 1,
                            "BOUNDARY_REPAIR": 1,
                            "ADVERSARIAL_NEG": 1,
                            "RESCUER": 1,
                        },
                        "family_slice_lineage_requirements": [
                            "branch_id",
                            "parent_branch_id",
                            "feedback_refs",
                            "rescue_linkage",
                        ],
                        "family_slice_rescue_lineage_required": False,
                        "lane_branch_counts": {
                            "STEELMAN": 1,
                            "ALT_FORMALISM": 0,
                            "BOUNDARY_REPAIR": 0,
                            "ADVERSARIAL_NEG": 0,
                            "RESCUER": 0,
                        },
                        "branch_parentage_map": {
                            "SIM_PRIMARY_PROBE_OPERATOR": "SIM_NONEXISTENT_PARENT",
                        },
                        "branch_group_map": {
                            "SIM_PRIMARY_PROBE_OPERATOR": "BG_FAMILY_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                        },
                        "branch_groups_used": ["BG_FAMILY_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR"],
                        "branch_track_map": {
                            "SIM_PRIMARY_PROBE_OPERATOR": "FAMILY_SLICE_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                        },
                        "branch_tracks_used": [
                            "FAMILY_SLICE_SUBSTRATE_BASE_FAMILY_PROBE_OPERATOR",
                        ],
                        "root_branch_ids": [],
                        "branch_child_counts": {"SIM_NONEXISTENT_PARENT": 1},
                    },
                },
            )
            (run_dir / "summary.json").write_text(json.dumps({"steps_completed": 1}), encoding="utf-8")
            (run_dir / "campaign_summary.json").write_text(
                json.dumps(
                    {
                        "steps_executed": 1,
                        "goal_source": "family_slice",
                        "planning_mode": "family_slice_controlled",
                        "family_slice_id": "A2_TO_A1_FAMILY_SLICE__TEST__v1",
                        "family_slice_json": str(family_slice_path),
                        "state_metrics": {
                            "killed_unique_count": 0,
                            "sim_registry_count": 1,
                            "canonical_term_count": 1,
                        },
                        "a1_semantic_gate": {"status": "PASS"},
                    }
                ),
                encoding="utf-8",
            )

            report = build_report(run_dir=run_dir, min_graveyard_count=0)
            self.assertEqual("FAIL", report["status"])
            check = next(
                item
                for item in report["checks"]
                if item["check_id"] == "AUTORATCHET_FAMILY_SLICE_BRANCH_PARENTAGE_VISIBLE"
            )
            self.assertEqual("FAIL", check["status"])


if __name__ == "__main__":
    unittest.main()
