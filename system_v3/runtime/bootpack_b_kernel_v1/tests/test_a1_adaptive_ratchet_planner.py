import json
import subprocess
import sys
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
sys.path.insert(0, str(BASE / "tools"))

from tools.a1_adaptive_ratchet_planner import (
    CORE_GOALS,
    ENTROPY_BOOKKEEPING_BRIDGE_GOALS,
    ENTROPY_BRIDGE_GOALS,
    EXTENDED_GOALS,
    _compatibility_goals_for_profile,
    _goal_for_term,
    _goals_from_family_slice,
    _validate_family_slice_semantics,
    build_strategy_from_state,
)


class TestA1AdaptiveRatchetPlanner(unittest.TestCase):
    def test_compatibility_goals_for_profile_use_reduced_refined_fuel_scaffold(self) -> None:
        goal_terms = [goal.term for goal in _compatibility_goals_for_profile("refined_fuel")]
        self.assertIn("density_matrix", goal_terms)
        self.assertIn("probe_operator", goal_terms)
        self.assertNotIn("qit_master_conjunction", goal_terms)

    def test_compatibility_goals_for_profile_keep_entropy_bridge_scaffold_narrow(self) -> None:
        goal_terms = [goal.term for goal in _compatibility_goals_for_profile("entropy_bridge")]
        self.assertEqual(["correlation_polarity"], goal_terms)

    def test_family_slice_goals_do_not_inherit_old_known_goal_tracks(self) -> None:
        family_slice = self._family_slice()
        family_slice["family_id"] = "entropy_bridge_family"
        family_slice["family_kind"] = "ENTROPY_BRIDGE"
        family_slice["primary_target_terms"] = ["correlation_polarity", "entropy_production_rate"]
        family_slice["companion_terms"] = []
        family_slice["admissibility"]["active_companion_floor"] = []
        family_slice["admissibility"]["executable_head"] = ["correlation_polarity"]
        family_slice["family_admissibility_hints"]["strategy_head_terms"] = ["correlation_polarity"]
        family_slice["family_admissibility_hints"]["late_passenger_terms"] = ["entropy_production_rate"]
        goals = _goals_from_family_slice(family_slice)
        self.assertEqual("FAMILY_SLICE_ENTROPY_BRIDGE_FAMILY_CORRELATION_POLARITY", goals[0].track)
        self.assertEqual("FAMILY_SLICE_ENTROPY_BRIDGE_FAMILY_ENTROPY_PRODUCTION_RATE", goals[1].track)

    def test_family_slice_goals_prioritize_family_negative_emphasis(self) -> None:
        goals = _goals_from_family_slice(self._family_slice())
        self.assertEqual("PRIMITIVE_EQUALS", goals[0].negative_class)

    def test_family_slice_semantics_require_lane_minimums_for_required_lanes(self) -> None:
        family_slice = self._family_slice()
        del family_slice["lane_minimums"]["RESCUER"]
        with self.assertRaisesRegex(ValueError, "family_slice_missing_lane_minimums:RESCUER"):
            _validate_family_slice_semantics(family_slice)

    def _family_slice(self) -> dict:
        return {
            "schema": "A2_TO_A1_FAMILY_SLICE_v1",
            "slice_id": "A2_TO_A1_FAMILY_SLICE__TEST_SUBSTRATE_BASE__2026_03_15__v1",
            "dispatch_id": "DRAFT_ONLY__NO_DISPATCH",
            "target_a1_role": "A1_PROPOSAL",
            "run_mode": "SCAFFOLD_PROOF",
            "bounded_scope": "test",
            "stop_rule": "test",
            "source_a2_artifacts": ["/tmp/a2.md"],
            "source_refs": ["/tmp/a1.md#L1"],
            "contradiction_refs": [],
            "residue_cluster_refs": [],
            "family_hint_refs": [],
            "generated_from_update_note": "/tmp/note.md",
            "family_id": "substrate_base_family",
            "family_label": "test family",
            "family_kind": "SUBSTRATE_BASE",
            "primary_target_terms": [
                "finite_dimensional_hilbert_space",
                "density_matrix",
                "probe_operator",
                "cptp_channel",
                "partial_trace",
                "probe",
            ],
            "companion_terms": [
                "finite_dimensional_hilbert_space",
                "density_matrix",
                "cptp_channel",
                "partial_trace",
            ],
            "deferred_terms": [],
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
            "primary_branch_requirement": "test",
            "alternative_branch_requirement": "test",
            "negative_branch_requirement": "test",
            "rescue_branch_requirement": "test",
            "expected_failure_modes": ["helper_bootstrap_debt_on_probe"],
            "lineage_requirements": [
                "branch_id",
                "parent_branch_id",
                "feedback_refs",
                "rescue_linkage",
            ],
            "graveyard_policy": "ACTIVE_WORKSPACE",
            "graveyard_fill_policy": "minimal_scaffold_pressure",
            "rescue_start_conditions": {
                "min_graveyard_count": 1,
                "min_kill_diversity": 1,
                "min_canonical_count": 0,
                "max_rescue_sources": 6,
                "graveyard_negative_expansion_limit": 3,
            },
            "graveyard_library_terms": ["primitive_equals"],
            "rescue_lineage_required": True,
            "required_negative_classes": [
                "PRIMITIVE_EQUALS",
                "CLASSICAL_TIME",
                "COMMUTATIVE_ASSUMPTION",
            ],
            "negative_emphasis_classes": ["PRIMITIVE_EQUALS"],
            "blocked_smuggles": ["primitive_equals"],
            "admissibility": {
                "executable_head": ["probe_operator"],
                "active_companion_floor": [
                    "finite_dimensional_hilbert_space",
                    "density_matrix",
                    "cptp_channel",
                    "partial_trace",
                ],
                "late_passengers": [],
                "witness_only_terms": ["probe"],
                "residue_terms": [],
                "landing_blockers": {"probe": "witness only"},
                "witness_floor": [
                    "finite_dimensional_hilbert_space",
                    "density_matrix",
                    "cptp_channel",
                    "partial_trace",
                ],
                "current_readiness_status": "PROPOSAL_ONLY",
            },
            "family_admissibility_hints": {
                "strategy_head_terms": ["probe_operator"],
                "forbid_strategy_head_terms": [],
                "late_passenger_terms": [],
                "witness_only_terms": ["probe"],
                "residue_only_terms": [],
                "landing_blocker_overrides": {"probe": "witness only"},
            },
            "term_math_surfaces": {
                "finite_dimensional_hilbert_space": {
                    "objects": "finite dimensional hilbert space",
                    "operations": "tensor unitary partial trace cptp channel",
                    "invariants": "finite dimensional",
                    "domain": "finite dimensional hilbert space",
                    "codomain": "operator space",
                },
                "density_matrix": {
                    "objects": "finite dimensional hilbert space density matrix",
                    "operations": "partial trace tensor cptp channel unitary",
                    "invariants": "trace finite dimensional",
                    "domain": "finite dimensional hilbert space",
                    "codomain": "density matrix",
                },
                "probe_operator": {
                    "objects": "density matrix operator",
                    "operations": "partial trace tensor unitary",
                    "invariants": "finite operator",
                    "domain": "density matrix",
                    "codomain": "operator space",
                },
                "cptp_channel": {
                    "objects": "density matrix cptp channel",
                    "operations": "partial trace tensor cptp channel",
                    "invariants": "trace finite",
                    "domain": "density matrix",
                    "codomain": "density matrix",
                },
                "partial_trace": {
                    "objects": "density matrix partial trace",
                    "operations": "partial trace tensor",
                    "invariants": "trace finite",
                    "domain": "finite dimensional hilbert space",
                    "codomain": "density matrix",
                },
            },
            "sim_hooks": {
                "required_sim_families": [
                    "BASELINE",
                    "BOUNDARY_SWEEP",
                    "PERTURBATION",
                    "ADVERSARIAL_NEG",
                    "COMPOSITION_STRESS",
                ],
                "required_probe_terms": [
                    "finite_dimensional_hilbert_space",
                    "density_matrix",
                    "probe_operator",
                    "cptp_channel",
                    "partial_trace",
                ],
                "probe_term_overrides": {
                    "finite_dimensional_hilbert_space": "finite_dimensional_hilbert_space",
                    "density_matrix": "density_matrix",
                    "probe_operator": "probe_operator",
                    "cptp_channel": "cptp_channel",
                    "partial_trace": "partial_trace",
                },
                "term_sim_tiers": {
                    "finite_dimensional_hilbert_space": "T0_ATOM",
                    "density_matrix": "T0_ATOM",
                    "probe_operator": "T2_OPERATOR",
                    "cptp_channel": "T1_COMPOUND",
                    "partial_trace": "T1_COMPOUND",
                },
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
                "promotion_contract_refs": ["/tmp/contract.md#L1"],
            },
            "evidence_obligations": {
                "structural_ladder_required": True,
                "sim_ladder_required": True,
                "family_specific_contract_required": True,
            },
            "planner_guardrails": {
                "forbid_direct_repo_reload": True,
                "forbid_goal_ladder_substitution": True,
                "forbid_unlisted_head_promotion": True,
                "forbid_family_collapse": True,
                "forbid_missing_context_fabrication": True,
                "forbid_rescue_during_fill": False,
            },
        }

    def _field_map(self, item: dict) -> dict[str, str]:
        return {str(row["name"]): str(row["value"]) for row in item.get("def_fields", [])}

    def _math_item(self, strategy: dict, suffix: str) -> dict:
        return next(
            item
            for item in strategy["targets"]
            if item["kind"] == "MATH_DEF" and str(item["id"]).endswith(suffix)
        )

    def _read_strategy_zip(self, zip_path: Path) -> dict:
        with zipfile.ZipFile(zip_path) as zf:
            return json.loads(zf.read("A1_STRATEGY_v1.json").decode("utf-8"))

    def test_first_substrate_goal_avoids_superoperator_injection(self) -> None:
        strategy = build_strategy_from_state(
            state={"term_registry": {}, "l0_lexeme_set": []},
            run_id="TEST_SUBSTRATE",
            sequence=1,
            goals=CORE_GOALS,
        )
        first_math = self._math_item(strategy, "_MATH_FINITE_DIMENSIONAL_HILBERT_SPACE")
        fields = self._field_map(first_math)
        self.assertEqual("S000001_Z_MATH_FINITE_DIMENSIONAL_HILBERT_SPACE", first_math["id"])
        self.assertNotIn("left_action_superoperator", fields["OPERATIONS"])
        self.assertNotIn("right_action_superoperator", fields["OPERATIONS"])
        self.assertEqual("finite dimensional hilbert space", fields["DOMAIN"])
        self.assertEqual("operator space", fields["CODOMAIN"])

    def test_density_matrix_goal_stays_minimal_after_hilbert_space(self) -> None:
        state = {
            "term_registry": {
                "finite_dimensional_hilbert_space": {
                    "state": "CANONICAL_ALLOWED",
                    "bound_math_def": "S000000_Z_MATH_FINITE_DIMENSIONAL_HILBERT_SPACE",
                }
            },
            "l0_lexeme_set": [],
        }
        strategy = build_strategy_from_state(
            state=state,
            run_id="TEST_SUBSTRATE",
            sequence=2,
            goals=CORE_GOALS,
            goal_selection="closure_first",
        )
        first_nonprereq_math = self._math_item(strategy, "_MATH_DENSITY_MATRIX")
        fields = self._field_map(first_nonprereq_math)
        self.assertEqual("S000002_Z_MATH_DENSITY_MATRIX", first_nonprereq_math["id"])
        self.assertNotIn("left_action_superoperator", fields["OPERATIONS"])
        self.assertNotIn("right_action_superoperator", fields["OPERATIONS"])
        self.assertEqual("finite dimensional hilbert space", fields["DOMAIN"])
        self.assertEqual("density matrix", fields["CODOMAIN"])

    def test_probe_operator_goal_avoids_undefined_probe_lexeme(self) -> None:
        state = {
            "term_registry": {
                "finite_dimensional_hilbert_space": {
                    "state": "CANONICAL_ALLOWED",
                    "bound_math_def": "S000000_Z_MATH_FINITE_DIMENSIONAL_HILBERT_SPACE",
                },
                "density_matrix": {
                    "state": "CANONICAL_ALLOWED",
                    "bound_math_def": "S000000_Z_MATH_DENSITY_MATRIX",
                },
            },
            "l0_lexeme_set": [],
        }
        strategy = build_strategy_from_state(
            state=state,
            run_id="TEST_SUBSTRATE",
            sequence=3,
            goals=CORE_GOALS,
            goal_selection="closure_first",
        )
        probe_math = self._math_item(strategy, "_MATH_PROBE_OPERATOR")
        fields = self._field_map(probe_math)
        self.assertEqual("density matrix operator", fields["OBJECTS"])
        self.assertEqual("operator space", fields["CODOMAIN"])
        self.assertNotIn("probe", fields["OBJECTS"])
        self.assertNotIn("probe", fields["CODOMAIN"])

    def test_unitary_operator_goal_stays_minimal_after_base_family(self) -> None:
        state = {
            "term_registry": {
                "finite_dimensional_hilbert_space": {"state": "CANONICAL_ALLOWED"},
                "density_matrix": {"state": "CANONICAL_ALLOWED"},
                "probe_operator": {"state": "CANONICAL_ALLOWED"},
                "cptp_channel": {"state": "CANONICAL_ALLOWED"},
                "partial_trace": {"state": "CANONICAL_ALLOWED"},
            },
            "l0_lexeme_set": [],
        }
        unitary_goal = next(goal for goal in EXTENDED_GOALS if goal.term == "unitary_operator")
        strategy = build_strategy_from_state(
            state=state,
            run_id="TEST_SUBSTRATE",
            sequence=6,
            goals=(unitary_goal,),
            goal_selection="closure_first",
        )
        unitary_math = self._math_item(strategy, "_MATH_UNITARY_OPERATOR")
        fields = self._field_map(unitary_math)
        self.assertEqual("finite dimensional hilbert space unitary operator", fields["OBJECTS"])
        self.assertEqual("tensor unitary", fields["OPERATIONS"])
        self.assertEqual("operator space", fields["CODOMAIN"])
        self.assertNotIn("left_action_superoperator", fields["OPERATIONS"])
        self.assertNotIn("right_action_superoperator", fields["OPERATIONS"])

    def test_compatibility_mode_can_still_promote_qit_master_when_prereqs_are_canonical(self) -> None:
        state = {
            "term_registry": {
                "density_matrix": {"state": "CANONICAL_ALLOWED"},
                "cptp_channel": {"state": "CANONICAL_ALLOWED"},
                "partial_trace": {"state": "CANONICAL_ALLOWED"},
                "unitary_operator": {"state": "CANONICAL_ALLOWED"},
                "correlation_polarity": {"state": "CANONICAL_ALLOWED"},
            },
            "l0_lexeme_set": [],
        }
        unitary_goal = next(goal for goal in EXTENDED_GOALS if goal.term == "unitary_operator")
        master_goal = _goal_for_term("qit_master_conjunction")
        strategy = build_strategy_from_state(
            state=state,
            run_id="TEST_MASTER_OVERRIDE",
            sequence=7,
            goals=(unitary_goal, master_goal),
            goal_selection="closure_first",
        )
        self.assertEqual("qit_master_conjunction", strategy["self_audit"]["goal_term"])
        self.assertEqual("compatibility_master_override", strategy["self_audit"]["goal_priority_source"])

    def test_family_slice_mode_does_not_inherit_qit_master_priority_override(self) -> None:
        family_slice = self._family_slice()
        family_slice["family_id"] = "custom_family_without_master_override"
        family_slice["family_kind"] = "CUSTOM_PROBE_DECLARED"
        family_slice["primary_target_terms"] = ["custom_bridge_segment", "qit_master_conjunction"]
        family_slice["companion_terms"] = []
        family_slice["admissibility"]["active_companion_floor"] = []
        family_slice["admissibility"]["executable_head"] = ["custom_bridge_segment"]
        family_slice["family_admissibility_hints"]["strategy_head_terms"] = ["custom_bridge_segment"]
        family_slice["family_admissibility_hints"]["witness_only_terms"] = []
        family_slice["sim_hooks"]["required_probe_terms"] = ["density_matrix"]
        family_slice["sim_hooks"]["probe_term_overrides"] = {}
        family_slice["sim_hooks"]["term_sim_tiers"] = {
            "custom_bridge_segment": "T3_STRUCTURE",
            "qit_master_conjunction": "T6_WHOLE_SYSTEM",
        }
        state = {
            "term_registry": {
                "density_matrix": {"state": "CANONICAL_ALLOWED"},
                "cptp_channel": {"state": "CANONICAL_ALLOWED"},
                "partial_trace": {"state": "CANONICAL_ALLOWED"},
                "unitary_operator": {"state": "CANONICAL_ALLOWED"},
                "correlation_polarity": {"state": "CANONICAL_ALLOWED"},
            },
            "l0_lexeme_set": [],
        }
        strategy = build_strategy_from_state(
            state=state,
            run_id="TEST_FAMILY_MASTER_OVERRIDE",
            sequence=8,
            goals=_goals_from_family_slice(family_slice),
            goal_selection="closure_first",
            family_slice=family_slice,
        )
        self.assertEqual("custom_bridge_segment", strategy["self_audit"]["goal_term"])
        self.assertEqual("next_goal", strategy["self_audit"]["goal_priority_source"])

    def test_family_slice_honors_forbid_rescue_during_fill_guardrail(self) -> None:
        family_slice = self._family_slice()
        family_slice["planner_guardrails"]["forbid_rescue_during_fill"] = True
        strategy = build_strategy_from_state(
            state={"term_registry": {}, "l0_lexeme_set": []},
            run_id="TEST_FAMILY_NO_RESCUE_DURING_FILL",
            sequence=1,
            goals=_goals_from_family_slice(family_slice),
            goal_selection="closure_first",
            debate_mode="graveyard_first",
            family_slice=family_slice,
        )
        rescue_items = [
            item
            for item in strategy["alternatives"]
            if any(
                str(field.get("name", "")).strip().startswith("RESCUE_")
                for field in item.get("def_fields", [])
                if isinstance(field, dict)
            )
        ]
        self.assertEqual([], rescue_items)

    def test_entropy_bridge_profile_starts_with_correlation_polarity(self) -> None:
        strategy = build_strategy_from_state(
            state={"term_registry": {}, "l0_lexeme_set": []},
            run_id="TEST_ENTROPY",
            sequence=1,
            goals=ENTROPY_BRIDGE_GOALS,
            goal_selection="closure_first",
        )
        first_math = self._math_item(strategy, "_MATH_CORRELATION_POLARITY")
        fields = self._field_map(first_math)
        self.assertEqual("S000001_Z_MATH_CORRELATION_POLARITY", first_math["id"])
        self.assertEqual("finite dimensional hilbert space", fields["OBJECTS"])
        self.assertEqual("partial_trace tensor cptp_channel unitary", fields["OPERATIONS"])

    def test_entropy_bookkeeping_bridge_profile_starts_with_density_entropy(self) -> None:
        strategy = build_strategy_from_state(
            state={"term_registry": {}, "l0_lexeme_set": []},
            run_id="TEST_ENTROPY_BOOKKEEPING",
            sequence=1,
            goals=ENTROPY_BOOKKEEPING_BRIDGE_GOALS,
            goal_selection="closure_first",
        )
        first_math = self._math_item(strategy, "_MATH_DENSITY_ENTROPY")
        fields = self._field_map(first_math)
        self.assertEqual("S000001_Z_MATH_DENSITY_ENTROPY", first_math["id"])
        self.assertEqual("density matrix", fields["OBJECTS"])
        self.assertEqual("partial trace cptp channel unitary", fields["OPERATIONS"])
        self.assertEqual("operator space", fields["CODOMAIN"])
        self.assertNotIn("left_action_superoperator", fields["OPERATIONS"])
        self.assertNotIn("right_action_superoperator", fields["OPERATIONS"])

    def test_information_work_extraction_bound_stays_minimal_after_density_entropy(self) -> None:
        state = {
            "term_registry": {
                "density_entropy": {"state": "CANONICAL_ALLOWED"},
            },
            "l0_lexeme_set": [],
        }
        rate_goal = next(
            goal for goal in ENTROPY_BOOKKEEPING_BRIDGE_GOALS if goal.term == "information_work_extraction_bound"
        )
        strategy = build_strategy_from_state(
            state=state,
            run_id="TEST_ENTROPY_BOOKKEEPING",
            sequence=2,
            goals=(rate_goal,),
            goal_selection="closure_first",
        )
        rate_math = self._math_item(strategy, "_MATH_INFORMATION_WORK_EXTRACTION_BOUND")
        fields = self._field_map(rate_math)
        self.assertEqual("density matrix cptp channel unitary operator", fields["OBJECTS"])
        self.assertEqual("cptp channel partial trace unitary", fields["OPERATIONS"])
        self.assertEqual("density matrix", fields["CODOMAIN"])
        self.assertNotIn("left_action_superoperator", fields["OPERATIONS"])
        self.assertNotIn("right_action_superoperator", fields["OPERATIONS"])

    def test_entropy_bookkeeping_bridge_profile_second_goal_is_information_work_bound(self) -> None:
        strategy = build_strategy_from_state(
            state={"term_registry": {"density_entropy": {"state": "CANONICAL_ALLOWED"}}, "l0_lexeme_set": []},
            run_id="TEST_ENTROPY_BOOKKEEPING",
            sequence=2,
            goals=ENTROPY_BOOKKEEPING_BRIDGE_GOALS,
            goal_selection="closure_first",
        )
        second_math = self._math_item(strategy, "_MATH_INFORMATION_WORK_EXTRACTION_BOUND")
        fields = self._field_map(second_math)
        self.assertEqual("S000002_Z_MATH_INFORMATION_WORK_EXTRACTION_BOUND", second_math["id"])
        self.assertEqual("density matrix cptp channel unitary operator", fields["OBJECTS"])

    def test_family_slice_goal_order_uses_companion_floor_then_head(self) -> None:
        goals = _goals_from_family_slice(self._family_slice())
        self.assertEqual(
            [
                "finite_dimensional_hilbert_space",
                "density_matrix",
                "cptp_channel",
                "partial_trace",
                "probe_operator",
            ],
            [goal.term for goal in goals],
        )

    def test_family_slice_rejects_blocked_strategy_head(self) -> None:
        family_slice = self._family_slice()
        family_slice["family_admissibility_hints"]["forbid_strategy_head_terms"] = ["probe_operator"]
        with self.assertRaises(ValueError):
            _validate_family_slice_semantics(family_slice)

    def test_family_slice_rejects_missing_required_sim_family(self) -> None:
        family_slice = self._family_slice()
        family_slice["sim_hooks"]["required_sim_families"] = [
            "BASELINE",
            "BOUNDARY_SWEEP",
            "PERTURBATION",
            "ADVERSARIAL_NEG",
        ]
        with self.assertRaisesRegex(ValueError, "family_slice_missing_required_sim_families:COMPOSITION_STRESS"):
            _validate_family_slice_semantics(family_slice)

    def test_family_slice_requires_explicit_recovery_sim_families(self) -> None:
        family_slice = self._family_slice()
        del family_slice["sim_hooks"]["recovery_sim_families"]
        with self.assertRaisesRegex(ValueError, "family_slice_missing_recovery_sim_families"):
            _validate_family_slice_semantics(family_slice)

    def test_family_slice_cli_outranks_goal_profile(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            out_zip = tmp_path / "planner.zip"
            state_json = tmp_path / "state.json"
            family_slice_json = tmp_path / "family_slice.json"
            state_json.write_text(json.dumps({"term_registry": {}, "l0_lexeme_set": []}), encoding="utf-8")
            family_slice_json.write_text(json.dumps(self._family_slice()), encoding="utf-8")
            script = BASE / "tools" / "a1_adaptive_ratchet_planner.py"
            proc = subprocess.run(
                [
                    "python3",
                    str(script),
                    "--out",
                    str(out_zip),
                    "--run-id",
                    "TEST_SLICE",
                    "--sequence",
                    "1",
                    "--state-json",
                    str(state_json),
                    "--goal-profile",
                    "entropy_bridge",
                    "--family-slice-json",
                    str(family_slice_json),
                ],
                cwd=str(BASE),
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, proc.returncode, msg=proc.stderr or proc.stdout)
            strategy = self._read_strategy_zip(out_zip)
            first_math = self._math_item(strategy, "_MATH_FINITE_DIMENSIONAL_HILBERT_SPACE")
            self.assertEqual(
                "A2_TO_A1_FAMILY_SLICE__TEST_SUBSTRATE_BASE__2026_03_15__v1",
                strategy["inputs"]["family_slice_id"],
            )
            self.assertEqual("SCAFFOLD_PROOF", strategy["inputs"]["family_slice_run_mode"])
            self.assertEqual("S000001_Z_MATH_FINITE_DIMENSIONAL_HILBERT_SPACE", first_math["id"])

    def test_family_slice_math_surface_terms_are_visible_in_self_audit(self) -> None:
        strategy = build_strategy_from_state(
            state={"term_registry": {}, "l0_lexeme_set": []},
            run_id="TEST_SLICE",
            sequence=1,
            goals=_goals_from_family_slice(self._family_slice()),
            family_slice=self._family_slice(),
        )
        self.assertIn("probe_operator", strategy["self_audit"]["family_slice_math_surface_terms"])

    def test_family_slice_math_surface_override_outranks_global_minimal_surface(self) -> None:
        family_slice = self._family_slice()
        family_slice["term_math_surfaces"]["probe_operator"]["operations"] = "family_slice_specific_probe_path"
        strategy = build_strategy_from_state(
            state={
                "term_registry": {
                    "finite_dimensional_hilbert_space": {"state": "CANONICAL_ALLOWED"},
                    "density_matrix": {"state": "CANONICAL_ALLOWED"},
                    "cptp_channel": {"state": "CANONICAL_ALLOWED"},
                    "partial_trace": {"state": "CANONICAL_ALLOWED"},
                },
                "l0_lexeme_set": [],
            },
            run_id="TEST_SLICE",
            sequence=3,
            goals=_goals_from_family_slice(family_slice),
            goal_selection="closure_first",
            family_slice=family_slice,
        )
        probe_math = self._math_item(strategy, "_MATH_PROBE_OPERATOR")
        fields = self._field_map(probe_math)
        self.assertEqual("family_slice_specific_probe_path", fields["OPERATIONS"])

    def test_family_slice_strategy_target_class_uses_family_prefix(self) -> None:
        family_slice = self._family_slice()
        strategy = build_strategy_from_state(
            state={"term_registry": {}, "l0_lexeme_set": []},
            run_id="TEST_SLICE",
            sequence=1,
            goals=_goals_from_family_slice(family_slice),
            family_slice=family_slice,
        )
        self.assertEqual(
            "TC_FAMILY_SUBSTRATE_BASE_FAMILY",
            strategy["self_audit"]["family_slice_target_class_prefix"],
        )
        self.assertTrue(
            strategy["self_audit"]["strategy_target_class"].startswith("TC_FAMILY_SUBSTRATE_BASE_FAMILY_")
        )

    def test_family_slice_sim_hooks_are_visible_in_self_audit(self) -> None:
        family_slice = self._family_slice()
        strategy = build_strategy_from_state(
            state={"term_registry": {}, "l0_lexeme_set": []},
            run_id="TEST_SLICE",
            sequence=1,
            goals=_goals_from_family_slice(family_slice),
            family_slice=family_slice,
        )
        self.assertEqual("finite_dimensional_hilbert_space", strategy["self_audit"]["goal_term"])
        self.assertEqual("finite_dimensional_hilbert_space", strategy["self_audit"]["goal_probe_term"])
        self.assertEqual("family_slice_override", strategy["self_audit"]["goal_probe_source"])
        self.assertEqual("T0_ATOM", strategy["self_audit"]["goal_sim_tier"])
        self.assertIn("probe_operator", strategy["self_audit"]["family_slice_declared_probe_terms"])
        self.assertEqual(
            [
                "BASELINE",
                "BOUNDARY_SWEEP",
                "PERTURBATION",
                "ADVERSARIAL_NEG",
                "COMPOSITION_STRESS",
            ],
            strategy["self_audit"]["family_slice_required_sim_families"],
        )
        self.assertIn("ADVERSARIAL_NEG", strategy["self_audit"]["family_slice_required_sim_families"])
        self.assertEqual(
            {
                "BOUNDARY_SWEEP": "T1_COMPOUND",
                "PERTURBATION": "T2_OPERATOR",
                "ADVERSARIAL_NEG": "T1_COMPOUND",
                "COMPOSITION_STRESS": "T3_STRUCTURE",
            },
            strategy["self_audit"]["family_slice_sim_family_tiers"],
        )
        self.assertEqual(
            ["BOUNDARY_SWEEP", "PERTURBATION", "COMPOSITION_STRESS"],
            strategy["self_audit"]["family_slice_recovery_sim_families"],
        )
        self.assertEqual(6, strategy["self_audit"]["family_slice_rescue_source_limit"])
        self.assertIn("probe_operator", strategy["self_audit"]["family_slice_term_sim_tier_terms"])
        self.assertEqual(
            [
                "BASELINE",
                "BOUNDARY_SWEEP",
                "PERTURBATION",
                "ADVERSARIAL_NEG",
                "COMPOSITION_STRESS",
            ],
            strategy["self_audit"]["sim_families_used"],
        )
        self.assertEqual(
            {
                "ADVERSARIAL_NEG": ["T1_COMPOUND"],
                "BASELINE": ["T0_ATOM"],
                "BOUNDARY_SWEEP": ["T1_COMPOUND"],
                "COMPOSITION_STRESS": ["T3_STRUCTURE"],
                "PERTURBATION": ["T2_OPERATOR"],
            },
            strategy["self_audit"]["sim_family_tier_map"],
        )
        self.assertEqual(["BOUNDARY_SWEEP"], strategy["self_audit"]["rescue_sim_families_used"])
        self.assertEqual(0, strategy["self_audit"]["rescue_source_count"])
        self.assertEqual(
            {
                "BASELINE": ["OP_BIND_SIM"],
                "BOUNDARY_SWEEP": ["OP_REPAIR_DEF_FIELD"],
                "PERTURBATION": ["OP_MUTATE_LEXEME"],
                "ADVERSARIAL_NEG": ["OP_NEG_SIM_EXPAND"],
                "COMPOSITION_STRESS": ["OP_REORDER_DEPENDENCIES"],
            },
            strategy["self_audit"]["sim_family_operator_map"],
        )
        self.assertEqual(
            ["ENUM_REGISTRY_v1", "A1_REPAIR_OPERATOR_MAPPING_v1"],
            strategy["self_audit"]["operator_policy_sources"],
        )
        self.assertEqual(
            {
                "STEELMAN": 5,
                "ALT_FORMALISM": 2,
                "BOUNDARY_REPAIR": 1,
                "ADVERSARIAL_NEG": 1,
                "RESCUER": 1,
            },
            strategy["self_audit"]["lane_branch_counts"],
        )
        self.assertEqual(
            {
                "STEELMAN": 1,
                "ALT_FORMALISM": 1,
                "BOUNDARY_REPAIR": 1,
                "ADVERSARIAL_NEG": 1,
                "RESCUER": 1,
            },
            strategy["self_audit"]["family_slice_lane_minimums"],
        )
        self.assertEqual(
            {
                "primary": "test",
                "alternative": "test",
                "negative": "test",
                "rescue": "test",
            },
            strategy["self_audit"]["family_slice_branch_requirements"],
        )
        self.assertEqual(
            ["branch_id", "parent_branch_id", "feedback_refs", "rescue_linkage"],
            strategy["self_audit"]["family_slice_lineage_requirements"],
        )
        self.assertTrue(strategy["self_audit"]["family_slice_rescue_lineage_required"])
        self.assertEqual(
            ["branch_id", "feedback_refs", "parent_branch_id"],
            strategy["self_audit"]["branch_lineage_fields_used"],
        )
        main_root = "S000001_Z_SIM_CANON_FINITE_DIMENSIONAL_HILBERT_SPACE"
        self.assertEqual(
            main_root,
            strategy["self_audit"]["branch_parentage_map"]["S000001_Z_SIM_ALT_BOUNDARY_FINITE_DIMENSIONAL_HILBERT_SPACE"],
        )
        self.assertEqual([main_root], strategy["self_audit"]["root_branch_ids"])
        self.assertEqual(8, strategy["self_audit"]["branch_child_counts"][main_root])
        self.assertEqual(1, len(strategy["self_audit"]["rescue_linkages_used"]))
        self.assertTrue(strategy["self_audit"]["rescue_linkages_used"][0].startswith("SCAFFOLD::BOUNDARY_SWEEP::"))
        self.assertEqual(
            ["branch_id", "feedback_refs", "parent_branch_id", "rescue_linkage"],
            strategy["self_audit"]["rescue_lineage_fields_used"],
        )
        expected_branch_group = "BG_FAMILY_SUBSTRATE_BASE_FAMILY_FINITE_DIMENSIONAL_HILBERT_SPACE"
        self.assertEqual([expected_branch_group], strategy["self_audit"]["branch_groups_used"])
        self.assertIn(
            "FAMILY_SLICE_SUBSTRATE_BASE_FAMILY_FINITE_DIMENSIONAL_HILBERT_SPACE",
            strategy["self_audit"]["branch_tracks_used"],
        )
        self.assertIn("ATOMIC_TERM_BOOTSTRAP", strategy["self_audit"]["branch_tracks_used"])
        baseline_item = next(
            item
            for item in (strategy["targets"] + strategy["alternatives"])
            if item["kind"] == "SIM_SPEC"
            and self._field_map(item).get("FAMILY") == "BASELINE"
            and self._field_map(item).get("GOAL_TERM") == "finite_dimensional_hilbert_space"
        )
        baseline_fields = self._field_map(baseline_item)
        self.assertEqual(baseline_item["id"], baseline_fields["BRANCH_ID"])
        self.assertEqual("NONE", baseline_fields["PARENT_BRANCH_ID"])
        self.assertEqual(expected_branch_group, baseline_fields["BRANCH_GROUP"])
        self.assertEqual(
            "FAMILY_SLICE_SUBSTRATE_BASE_FAMILY_FINITE_DIMENSIONAL_HILBERT_SPACE",
            baseline_fields["BRANCH_TRACK"],
        )
        self.assertEqual([baseline_fields["REQUIRES_EVIDENCE"]], json.loads(baseline_fields["FEEDBACK_REFS"]))
        atomic_baseline_item = next(
            item
            for item in strategy["targets"]
            if item["kind"] == "SIM_SPEC"
            and self._field_map(item).get("FAMILY") == "BASELINE"
            and self._field_map(item).get("GOAL_TERM", "") == ""
        )
        atomic_fields = self._field_map(atomic_baseline_item)
        self.assertEqual(main_root, atomic_fields["PARENT_BRANCH_ID"])
        self.assertEqual(expected_branch_group, atomic_fields["BRANCH_GROUP"])
        self.assertEqual("ATOMIC_TERM_BOOTSTRAP", atomic_fields["BRANCH_TRACK"])

    def test_family_slice_probe_override_can_replace_global_probe_default(self) -> None:
        family_slice = self._family_slice()
        family_slice["family_id"] = "custom_probe_override_family"
        family_slice["family_kind"] = "CUSTOM_PROBE_OVERRIDE"
        family_slice["primary_target_terms"] = ["custom_bridge_segment"]
        family_slice["companion_terms"] = []
        family_slice["admissibility"]["active_companion_floor"] = []
        family_slice["admissibility"]["executable_head"] = ["custom_bridge_segment"]
        family_slice["family_admissibility_hints"]["strategy_head_terms"] = ["custom_bridge_segment"]
        family_slice["family_admissibility_hints"]["witness_only_terms"] = []
        family_slice["sim_hooks"]["required_probe_terms"] = ["density_matrix"]
        family_slice["sim_hooks"]["probe_term_overrides"] = {"custom_bridge_segment": "density_matrix"}
        family_slice["sim_hooks"]["term_sim_tiers"] = {"custom_bridge_segment": "T3_STRUCTURE"}
        strategy = build_strategy_from_state(
            state={"term_registry": {}, "l0_lexeme_set": []},
            run_id="TEST_SLICE",
            sequence=1,
            goals=_goals_from_family_slice(family_slice),
            family_slice=family_slice,
        )
        self.assertEqual("custom_bridge_segment", strategy["self_audit"]["goal_term"])
        self.assertEqual("density_matrix", strategy["self_audit"]["goal_probe_term"])
        self.assertEqual("family_slice_override", strategy["self_audit"]["goal_probe_source"])
        self.assertEqual("T3_STRUCTURE", strategy["self_audit"]["goal_sim_tier"])
        sim_spec = next(
            item
            for item in strategy["targets"]
            if item["kind"] == "SIM_SPEC" and self._field_map(item).get("GOAL_TERM") == "custom_bridge_segment"
        )
        fields = self._field_map(sim_spec)
        self.assertEqual("density_matrix", fields["PROBE_TERM"])
        self.assertEqual("T3_STRUCTURE", fields["TIER"])

    def test_family_slice_declared_probe_terms_replace_global_fallback_without_override(self) -> None:
        family_slice = self._family_slice()
        family_slice["family_id"] = "custom_probe_declared_family"
        family_slice["family_kind"] = "CUSTOM_PROBE_DECLARED"
        family_slice["primary_target_terms"] = ["custom_bridge_segment"]
        family_slice["companion_terms"] = []
        family_slice["admissibility"]["active_companion_floor"] = []
        family_slice["admissibility"]["executable_head"] = ["custom_bridge_segment"]
        family_slice["family_admissibility_hints"]["strategy_head_terms"] = ["custom_bridge_segment"]
        family_slice["family_admissibility_hints"]["witness_only_terms"] = []
        family_slice["sim_hooks"]["required_probe_terms"] = ["density_matrix"]
        family_slice["sim_hooks"]["probe_term_overrides"] = {}
        family_slice["sim_hooks"]["term_sim_tiers"] = {"custom_bridge_segment": "T3_STRUCTURE"}
        strategy = build_strategy_from_state(
            state={"term_registry": {}, "l0_lexeme_set": []},
            run_id="TEST_SLICE",
            sequence=1,
            goals=_goals_from_family_slice(family_slice),
            family_slice=family_slice,
        )
        self.assertEqual("custom_bridge_segment", strategy["self_audit"]["goal_term"])
        self.assertEqual("density_matrix", strategy["self_audit"]["goal_probe_term"])
        self.assertEqual("family_slice_declared_fallback", strategy["self_audit"]["goal_probe_source"])
        self.assertEqual("T3_STRUCTURE", strategy["self_audit"]["goal_sim_tier"])

    def test_family_slice_sim_family_tiers_can_override_branch_tiers(self) -> None:
        family_slice = self._family_slice()
        family_slice["sim_hooks"]["sim_family_tiers"] = {
            "BOUNDARY_SWEEP": "T4_SYSTEM_SEGMENT",
            "PERTURBATION": "T4_SYSTEM_SEGMENT",
            "ADVERSARIAL_NEG": "T4_SYSTEM_SEGMENT",
            "COMPOSITION_STRESS": "T4_SYSTEM_SEGMENT",
        }
        strategy = build_strategy_from_state(
            state={"term_registry": {}, "l0_lexeme_set": []},
            run_id="TEST_SLICE",
            sequence=1,
            goals=_goals_from_family_slice(family_slice),
            family_slice=family_slice,
        )
        self.assertEqual(
            {
                "ADVERSARIAL_NEG": ["T4_SYSTEM_SEGMENT"],
                "BASELINE": ["T0_ATOM"],
                "BOUNDARY_SWEEP": ["T4_SYSTEM_SEGMENT"],
                "COMPOSITION_STRESS": ["T4_SYSTEM_SEGMENT"],
                "PERTURBATION": ["T4_SYSTEM_SEGMENT"],
            },
            strategy["self_audit"]["sim_family_tier_map"],
        )

    def test_graveyard_first_uses_family_slice_negative_classes(self) -> None:
        family_slice = self._family_slice()
        strategy = build_strategy_from_state(
            state={"term_registry": {}, "l0_lexeme_set": []},
            run_id="TEST_SLICE",
            sequence=1,
            goals=_goals_from_family_slice(family_slice),
            family_slice=family_slice,
            debate_mode="graveyard_first",
        )
        self.assertEqual(
            [
                "PRIMITIVE_EQUALS",
                "CLASSICAL_TIME",
                "COMMUTATIVE_ASSUMPTION",
            ],
            strategy["self_audit"]["graveyard_negative_classes_used"],
        )

    def test_graveyard_first_can_limit_family_slice_negative_expansion(self) -> None:
        family_slice = self._family_slice()
        family_slice["rescue_start_conditions"]["graveyard_negative_expansion_limit"] = 1
        strategy = build_strategy_from_state(
            state={"term_registry": {}, "l0_lexeme_set": []},
            run_id="TEST_SLICE",
            sequence=1,
            goals=_goals_from_family_slice(family_slice),
            family_slice=family_slice,
            debate_mode="graveyard_first",
        )
        self.assertEqual(1, strategy["self_audit"]["family_slice_graveyard_negative_expansion_limit"])
        self.assertEqual(["PRIMITIVE_EQUALS"], strategy["self_audit"]["graveyard_negative_classes_used"])

    def test_graveyard_first_budget_can_be_owned_by_family_slice(self) -> None:
        family_slice = self._family_slice()
        family_slice["rescue_start_conditions"]["graveyard_first_max_items"] = 20
        family_slice["rescue_start_conditions"]["graveyard_first_max_sims"] = 28
        strategy = build_strategy_from_state(
            state={"term_registry": {}, "l0_lexeme_set": []},
            run_id="TEST_SLICE",
            sequence=1,
            goals=_goals_from_family_slice(family_slice),
            family_slice=family_slice,
            debate_mode="graveyard_first",
        )
        self.assertEqual({"max_items": 20, "max_sims": 28}, strategy["budget"])
        self.assertEqual("graveyard_first", strategy["self_audit"]["debate_mode"])
        self.assertEqual(20, strategy["self_audit"]["family_slice_budget_max_items"])
        self.assertEqual(28, strategy["self_audit"]["family_slice_budget_max_sims"])
        self.assertEqual("family_slice_override", strategy["self_audit"]["family_slice_budget_source"])

    def test_balanced_budget_can_be_owned_by_family_slice(self) -> None:
        family_slice = self._family_slice()
        family_slice["rescue_start_conditions"]["balanced_max_items"] = 18
        family_slice["rescue_start_conditions"]["balanced_max_sims"] = 22
        strategy = build_strategy_from_state(
            state={"term_registry": {}, "l0_lexeme_set": []},
            run_id="TEST_SLICE",
            sequence=1,
            goals=_goals_from_family_slice(family_slice),
            family_slice=family_slice,
            debate_mode="balanced",
        )
        self.assertEqual({"max_items": 18, "max_sims": 22}, strategy["budget"])
        self.assertEqual("balanced", strategy["self_audit"]["debate_mode"])
        self.assertEqual(18, strategy["self_audit"]["family_slice_budget_max_items"])
        self.assertEqual(22, strategy["self_audit"]["family_slice_budget_max_sims"])
        self.assertEqual("family_slice_override", strategy["self_audit"]["family_slice_budget_source"])

    def test_family_slice_recovery_shape_can_override_rescue_family_set_and_limit(self) -> None:
        family_slice = self._family_slice()
        family_slice["sim_hooks"]["recovery_sim_families"] = ["BOUNDARY_SWEEP"]
        family_slice["rescue_start_conditions"]["max_rescue_sources"] = 2
        state = {
            "term_registry": {},
            "l0_lexeme_set": [],
            "kill_log": [
                {"tag": "KILL_SIGNAL", "id": "SIM_A", "token": "tok_a"},
                {"tag": "KILL_SIGNAL", "id": "SIM_B", "token": "tok_b"},
                {"tag": "KILL_SIGNAL", "id": "SIM_C", "token": "tok_c"},
            ],
            "spec_meta": {
                "SIM_A": {"target_class": "TC_A", "negative_class": "CLASSICAL_TIME"},
                "SIM_B": {"target_class": "TC_B", "negative_class": "PRIMITIVE_EQUALS"},
                "SIM_C": {"target_class": "TC_C", "negative_class": "COMMUTATIVE_ASSUMPTION"},
            },
        }
        strategy = build_strategy_from_state(
            state=state,
            run_id="TEST_RECOVERY",
            sequence=5,
            goals=_goals_from_family_slice(family_slice),
            family_slice=family_slice,
            debate_mode="graveyard_recovery",
        )
        self.assertEqual(["BOUNDARY_SWEEP"], strategy["self_audit"]["family_slice_recovery_sim_families"])
        self.assertEqual(2, strategy["self_audit"]["family_slice_rescue_source_limit"])
        self.assertEqual(["BOUNDARY_SWEEP"], strategy["self_audit"]["rescue_sim_families_used"])
        self.assertEqual(2, strategy["self_audit"]["rescue_source_count"])
        self.assertEqual(2, len(strategy["self_audit"]["rescue_linkages_used"]))
        rescue_items = [
            item
            for item in strategy["alternatives"]
            if item["kind"] == "SIM_SPEC" and self._field_map(item).get("RESCUE_MODE") == "GRAVEYARD_RECOVERY"
        ]
        self.assertEqual(2, len(rescue_items))
        first_fields = self._field_map(rescue_items[0])
        self.assertEqual(
            {
                "BRANCH_ID",
                "PARENT_BRANCH_ID",
                "FEEDBACK_REFS",
                "RESCUE_LINKAGE",
            },
            {"BRANCH_ID", "PARENT_BRANCH_ID", "FEEDBACK_REFS", "RESCUE_LINKAGE"}.intersection(first_fields.keys()),
        )
        self.assertEqual(rescue_items[0]["id"], first_fields["BRANCH_ID"])

    def test_family_slice_balanced_mode_emits_scaffold_rescue_lane(self) -> None:
        family_slice = self._family_slice()
        strategy = build_strategy_from_state(
            state={"term_registry": {}, "l0_lexeme_set": []},
            run_id="TEST_SCAFFOLD_RESCUE",
            sequence=7,
            goals=_goals_from_family_slice(family_slice),
            family_slice=family_slice,
            debate_mode="balanced",
        )
        rescue_items = [
            item
            for item in strategy["alternatives"]
            if item["kind"] == "SIM_SPEC" and self._field_map(item).get("RESCUE_MODE") == "SCAFFOLD_ATTACHMENT"
        ]
        self.assertEqual(1, len(rescue_items))
        fields = self._field_map(rescue_items[0])
        self.assertEqual("BOUNDARY_SWEEP", fields["FAMILY"])
        self.assertEqual("helper_bootstrap_debt_on_probe", fields["RESCUE_FAILURE_MODE"])
        self.assertEqual("primitive_equals", fields["RESCUE_LIBRARY_TERM"])
        self.assertEqual("SCAFFOLD_ATTACHMENT", fields["RESCUE_MODE"])
        self.assertTrue(fields["RESCUE_LINKAGE"].startswith("SCAFFOLD::BOUNDARY_SWEEP::helper_bootstrap_debt_on_probe::"))
        self.assertEqual(rescue_items[0]["id"], fields["BRANCH_ID"])
        self.assertTrue(fields["PARENT_BRANCH_ID"].startswith("S000007_Z_SIM_CANON_"))
        self.assertEqual(
            [fields["REQUIRES_EVIDENCE"]],
            json.loads(fields["FEEDBACK_REFS"]),
        )
        boundary_item = next(
            item
            for item in strategy["alternatives"]
            if item["kind"] == "SIM_SPEC" and self._field_map(item).get("FAMILY") == "BOUNDARY_SWEEP"
            and self._field_map(item).get("RESCUE_MODE", "") == ""
        )
        boundary_fields = self._field_map(boundary_item)
        self.assertEqual(boundary_item["id"], boundary_fields["BRANCH_ID"])
        self.assertTrue(boundary_fields["PARENT_BRANCH_ID"].startswith("S000007_Z_SIM_CANON_"))
        self.assertEqual([boundary_fields["REQUIRES_EVIDENCE"]], json.loads(boundary_fields["FEEDBACK_REFS"]))

    def test_family_slice_rescuer_lane_minimum_can_expand_scaffold_rescue_count(self) -> None:
        family_slice = self._family_slice()
        family_slice["lane_minimums"]["RESCUER"]["min_branches"] = 2
        strategy = build_strategy_from_state(
            state={"term_registry": {}, "l0_lexeme_set": []},
            run_id="TEST_SCAFFOLD_RESCUE_MULTI",
            sequence=8,
            goals=_goals_from_family_slice(family_slice),
            family_slice=family_slice,
            debate_mode="balanced",
        )
        rescue_items = [
            item
            for item in strategy["alternatives"]
            if item["kind"] == "SIM_SPEC" and self._field_map(item).get("RESCUE_MODE") == "SCAFFOLD_ATTACHMENT"
        ]
        self.assertEqual(2, len(rescue_items))
        self.assertEqual(2, strategy["self_audit"]["lane_branch_counts"]["RESCUER"])
        self.assertEqual(
            ["BOUNDARY_SWEEP", "PERTURBATION"],
            strategy["self_audit"]["rescue_sim_families_used"],
        )

    def test_cli_requires_family_slice_json_unless_legacy_goal_profile_override(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            out_zip = tmp_path / "planner.zip"
            state_json = tmp_path / "state.json"
            state_json.write_text(json.dumps({"term_registry": {}, "l0_lexeme_set": []}), encoding="utf-8")
            script = BASE / "tools" / "a1_adaptive_ratchet_planner.py"
            proc = subprocess.run(
                [
                    "python3",
                    str(script),
                    "--out",
                    str(out_zip),
                    "--run-id",
                    "TEST_SLICE",
                    "--sequence",
                    "1",
                    "--state-json",
                    str(state_json),
                    "--goal-profile",
                    "entropy_bridge",
                ],
                cwd=str(BASE),
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, proc.returncode)
            self.assertIn(
                "family_slice_json_required_unless_allow_legacy_goal_profile_mode",
                proc.stderr + proc.stdout,
            )


if __name__ == "__main__":
    unittest.main()
