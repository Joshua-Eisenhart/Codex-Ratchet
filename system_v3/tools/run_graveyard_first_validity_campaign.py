#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from a1_selector_warning_snapshot import (
    extract_selector_provenance_fields,
    extract_selector_warning_fields,
    selector_stop_summary,
)

REPO = Path(__file__).resolve().parents[1]
DRIVER = REPO / "tools" / "a1_external_memo_batch_driver.py"
SERIAL = REPO / "tools" / "a1_exchange_serial_runner.py"
BOOTSTRAP = REPO / "tools" / "bootstrap_seeded_continuation_run.py"
RUNS_ROOT = REPO / "runs"
A2_STATE = REPO / "a2_state"

PROFILE_MAP = {
    "substrate_base": {
        "concept_target_terms": "finite_dimensional_hilbert_space,density_matrix,probe_operator,cptp_channel,partial_trace",
        "goal_min_graveyard_count": "16",
        "goal_min_sim_registry_count": "220",
        "focus_term_mode": "concept_plus_rescue",
        "fill_until_fuel_coverage": True,
        "fill_fuel_coverage_target": "0.85",
        "campaign_graveyard_fill_policy": "fuel_full_load",
    },
    "substrate_base_concept_local": {
        "concept_target_terms": "finite_dimensional_hilbert_space,density_matrix,probe_operator,cptp_channel,partial_trace",
        "goal_min_graveyard_count": "12",
        "goal_min_sim_registry_count": "160",
        "focus_term_mode": "concept_local_rescue",
        "fill_until_fuel_coverage": False,
        "fill_fuel_coverage_target": "0.00",
        "campaign_graveyard_fill_policy": "anchor_replay",
    },
    "substrate_enrichment": {
        "concept_target_terms": "unitary_operator,commutator_operator,hamiltonian_operator,lindblad_generator",
        "goal_min_graveyard_count": "18",
        "goal_min_sim_registry_count": "260",
        "focus_term_mode": "concept_plus_rescue",
        "fill_until_fuel_coverage": True,
        "fill_fuel_coverage_target": "0.85",
        "campaign_graveyard_fill_policy": "fuel_full_load",
    },
    "substrate_enrichment_concept_local": {
        "concept_target_terms": "unitary_operator,commutator_operator,hamiltonian_operator,lindblad_generator",
        "goal_min_graveyard_count": "14",
        "goal_min_sim_registry_count": "180",
        "focus_term_mode": "concept_local_rescue",
        "fill_until_fuel_coverage": False,
        "fill_fuel_coverage_target": "0.00",
        "campaign_graveyard_fill_policy": "anchor_replay",
    },
    "substrate_enrichment_dynamics_local": {
        "concept_target_terms": "hamiltonian_operator,lindblad_generator",
        "goal_min_graveyard_count": "10",
        "goal_min_sim_registry_count": "120",
        "focus_term_mode": "concept_local_rescue",
        "fill_until_fuel_coverage": False,
        "fill_fuel_coverage_target": "0.00",
        "campaign_graveyard_fill_policy": "anchor_replay",
    },
    "substrate_enrichment_dynamics_bridge": {
        "concept_target_terms": "hamiltonian_operator,lindblad_generator",
        "goal_min_graveyard_count": "14",
        "goal_min_sim_registry_count": "140",
        "focus_term_mode": "concept_plus_rescue",
        "fill_until_fuel_coverage": False,
        "fill_fuel_coverage_target": "0.00",
        "campaign_graveyard_fill_policy": "anchor_replay",
    },
    "substrate_enrichment_dynamics_cluster_clamp_broad": {
        "concept_target_terms": "hamiltonian_operator,lindblad_generator",
        "seed_target_terms": "hamiltonian_operator,lindblad_generator",
        "priority_terms": "unitary_operator,commutator_operator",
        "path_build_allowed_terms": "unitary_operator,commutator_operator,hamiltonian_operator,lindblad_generator",
        "rescue_allowed_terms": "unitary_operator,commutator_operator,hamiltonian_operator,lindblad_generator",
        "priority_negative_classes": "CLASSICAL_TIME,COMMUTATIVE_ASSUMPTION,PRIMITIVE_EQUALS,INFINITE_SET,KERNEL_VALID_BUT_MODEL_EMPTY",
        "priority_claims": "Use the seeded dynamics-local pair as the admissible floor, then widen only inside the four-term enrichment family.||Do not allow non-family bridge terms or helper residue to become later-phase heads.||Treat unitary_operator and commutator_operator as family witnesses that support hamiltonian_operator and lindblad_generator, not as a new broad bridge lane.||Keep explicit classical-time and commutative-assumption negatives active for the dynamics pair.",
        "primary_expected_terms": "hamiltonian_operator,lindblad_generator",
        "witness_only_terms": "unitary_operator,commutator_operator",
        "bridge_witness_terms": "unitary_operator,commutator_operator",
        "goal_min_graveyard_count": "14",
        "goal_min_sim_registry_count": "140",
        "focus_term_mode": "phase_seed_broad_then_priority",
        "target_executed_per_call": "1",
        "seed_max_terms_per_cycle": "8",
        "path_max_terms_per_cycle": "8",
        "rescue_max_terms_per_cycle": "6",
        "fill_until_fuel_coverage": False,
        "fill_fuel_coverage_target": "0.00",
        "campaign_graveyard_fill_policy": "anchor_replay",
        "track": "SUBSTRATE_ENRICHMENT__DYNAMICS_CLUSTER_CLAMP",
    },
    "entropy_bridge_local": {
        "concept_target_terms": "correlation_polarity,entropy_production_rate",
        "goal_min_graveyard_count": "10",
        "goal_min_sim_registry_count": "120",
        "focus_term_mode": "concept_local_rescue",
        "fill_until_fuel_coverage": False,
        "fill_fuel_coverage_target": "0.00",
        "campaign_graveyard_fill_policy": "anchor_replay",
    },
    "entropy_bridge_broad": {
        "concept_target_terms": "correlation_polarity,entropy_production_rate",
        "goal_min_graveyard_count": "18",
        "goal_min_sim_registry_count": "180",
        "focus_term_mode": "phase_seed_broad_then_priority",
        "fill_until_fuel_coverage": True,
        "fill_fuel_coverage_target": "0.85",
        "campaign_graveyard_fill_policy": "fuel_full_load",
    },
    "entropy_bridge_residue_broad": {
        "concept_target_terms": "correlation_polarity,entropy_production_rate",
        "priority_terms": "information_work_extraction_bound,erasure_channel_entropy_cost_lower_bound,probe_induced_partition_boundary,correlation_diversity_functional",
        "priority_negative_classes": "CLASSICAL_TEMPERATURE,CLASSICAL_TIME,CONTINUOUS_BATH,COMMUTATIVE_ASSUMPTION,EUCLIDEAN_METRIC,INFINITE_SET,INFINITE_RESOLUTION,PRIMITIVE_EQUALS",
        "goal_min_graveyard_count": "18",
        "goal_min_sim_registry_count": "180",
        "focus_term_mode": "phase_seed_broad_then_priority",
        "fill_until_fuel_coverage": True,
        "fill_fuel_coverage_target": "0.85",
        "campaign_graveyard_fill_policy": "fuel_full_load",
        "graveyard_library_terms": "carnot_engine,szilard_engine,maxwell_demon",
        "track": "ENGINE_ENTROPY_EXPLORATION__CARNOT_SZILARD_MAXWELL_RESIDUE",
    },
    "entropy_bridge_thermal_time_broad": {
        "concept_target_terms": "correlation_polarity,entropy_production_rate",
        "priority_terms": "information_work_extraction_bound,erasure_channel_entropy_cost_lower_bound,probe_induced_partition_boundary,correlation_diversity_functional",
        "priority_negative_classes": "CLASSICAL_TEMPERATURE,CLASSICAL_TIME,CONTINUOUS_BATH,COMMUTATIVE_ASSUMPTION",
        "goal_min_graveyard_count": "18",
        "goal_min_sim_registry_count": "180",
        "focus_term_mode": "phase_seed_broad_then_priority",
        "fill_until_fuel_coverage": True,
        "fill_fuel_coverage_target": "0.85",
        "campaign_graveyard_fill_policy": "fuel_full_load",
        "graveyard_library_terms": "carnot_engine,szilard_engine,maxwell_demon",
        "track": "ENGINE_ENTROPY_EXPLORATION__THERMAL_TIME_RESIDUE",
    },
    "entropy_bridge_reformulation_broad": {
        "concept_target_terms": "correlation_polarity,entropy_production_rate",
        "priority_terms": "information_work_extraction_bound,erasure_channel_entropy_cost_lower_bound,probe_induced_partition_boundary,correlation_diversity_functional",
        "priority_negative_classes": "CLASSICAL_TEMPERATURE,CLASSICAL_TIME,CONTINUOUS_BATH,COMMUTATIVE_ASSUMPTION",
        "priority_claims": "Build bridge_bound_only branches using colder witnesses before any machine naming.||Build partition_correlation_only branches with no time or cycle narration.||Build hybrid_bridge_partition branches combining one cold witness with one partition/correlation witness.||Keep classical_residue_negative branches explicit and expected to fail.",
        "goal_min_graveyard_count": "18",
        "goal_min_sim_registry_count": "180",
        "focus_term_mode": "phase_seed_broad_then_priority",
        "fill_until_fuel_coverage": True,
        "fill_fuel_coverage_target": "0.85",
        "campaign_graveyard_fill_policy": "fuel_full_load",
        "graveyard_library_terms": "carnot_engine,szilard_engine,maxwell_demon",
        "track": "ENGINE_ENTROPY_EXPLORATION__REFORMULATION",
    },
    "entropy_bridge_colder_witness_broad": {
        "concept_target_terms": "correlation_polarity,entropy_production_rate",
        "priority_terms": "information_work_extraction_bound,erasure_channel_entropy_cost_lower_bound,density_entropy,probe_induced_partition_boundary,correlation_diversity_functional,correlation",
        "priority_negative_classes": "CLASSICAL_TEMPERATURE,CLASSICAL_TIME,CONTINUOUS_BATH,COMMUTATIVE_ASSUMPTION",
        "priority_claims": "Build bound_witness_floor branches with colder witnesses only and no direct entropy-rate naming.||Build partition_correlation_floor branches with partition, boundary, and correlation structure only.||Introduce correlation_polarity and entropy_production_rate only as late alias bridge terms after a colder or partition witness survives.||Keep classical_residue_negative branches explicit and expected to fail.",
        "goal_min_graveyard_count": "18",
        "goal_min_sim_registry_count": "180",
        "focus_term_mode": "phase_seed_broad_then_priority",
        "fill_until_fuel_coverage": True,
        "fill_fuel_coverage_target": "0.85",
        "campaign_graveyard_fill_policy": "fuel_full_load",
        "graveyard_library_terms": "carnot_engine,szilard_engine,maxwell_demon",
        "track": "ENGINE_ENTROPY_EXPLORATION__COLDER_WITNESS",
    },
    "entropy_bridge_helper_lift_broad": {
        "concept_target_terms": "correlation_polarity,entropy_production_rate",
        "priority_terms": "information_work_extraction_bound,erasure_channel_entropy_cost_lower_bound,density_entropy,probe_induced_partition_boundary,correlation_diversity_functional,correlation",
        "priority_negative_classes": "CLASSICAL_TEMPERATURE,CLASSICAL_TIME,CONTINUOUS_BATH,COMMUTATIVE_ASSUMPTION",
        "priority_claims": "Do not emit lone density_entropy branches.||Every primary branch must include one colder helper, one partition-or-correlation witness, and one late alias bridge term.||Build helper_partition_alias branches before any helper-only branch.||Keep helper_only_negative branches explicit and expected to fail.",
        "goal_min_graveyard_count": "18",
        "goal_min_sim_registry_count": "180",
        "focus_term_mode": "phase_seed_broad_then_priority",
        "fill_until_fuel_coverage": True,
        "fill_fuel_coverage_target": "0.85",
        "campaign_graveyard_fill_policy": "fuel_full_load",
        "graveyard_library_terms": "carnot_engine,szilard_engine,maxwell_demon",
        "track": "ENGINE_ENTROPY_EXPLORATION__HELPER_LIFT",
    },
    "entropy_bridge_cluster_rescue_broad": {
        "concept_target_terms": "correlation_polarity,entropy_production_rate",
        "seed_target_terms": "density_entropy,correlation,erasure_channel_entropy_cost_lower_bound",
        "seed_force_transition_min_executed": "1",
        "seed_force_transition_min_graveyard": "45",
        "seed_force_transition_min_kill_diversity": "8",
        "priority_terms": "probe_induced_partition_boundary,correlation_diversity_functional,erasure_channel_entropy_cost_lower_bound,density_entropy,entropy_production_rate",
        "path_build_allowed_terms": "probe_induced_partition_boundary,correlation_diversity_functional,erasure_channel_entropy_cost_lower_bound,density_entropy,entropy_production_rate",
        "rescue_allowed_terms": "correlation,correlation_polarity,probe_induced_partition_boundary,correlation_diversity_functional,density_entropy",
        "priority_negative_classes": "CLASSICAL_TEMPERATURE,CLASSICAL_TIME,CONTINUOUS_BATH,COMMUTATIVE_ASSUMPTION,EUCLIDEAN_METRIC,INFINITE_SET,INFINITE_RESOLUTION,PRIMITIVE_EQUALS",
        "priority_claims": "Keep probe_induced_partition_boundary and correlation_diversity_functional in the primary post-seed path_build floor as structure-side proposal/control targets, not as current executable heads.||Use erasure_channel_entropy_cost_lower_bound only as colder witness support below the live correlation-side executable floor.||Keep information_work_extraction_bound as proposal/control only outside the active executable floor until helper decomposition is solved.||Use density_entropy as a witness and entropy_production_rate as a late bookkeeping passenger once the live executable floor is already in place.||Keep helper fragments subordinate and expected to fail if they try to retake head status.||Keep cluster_negative branches explicit and expected to reproduce Cluster A/B/C failure basins.",
        "goal_min_graveyard_count": "18",
        "goal_min_sim_registry_count": "180",
        "focus_term_mode": "phase_seed_broad_then_priority",
        "target_executed_per_call": "12",
        "seed_max_terms_per_cycle": "18",
        "path_max_terms_per_cycle": "12",
        "rescue_max_terms_per_cycle": "8",
        "campaign_recovery_min_rescue_from_fields": "2",
        "fill_until_fuel_coverage": True,
        "fill_fuel_coverage_target": "0.85",
        "campaign_graveyard_fill_policy": "fuel_full_load",
        "graveyard_library_terms": "carnot_engine,szilard_engine,maxwell_demon",
        "track": "ENGINE_ENTROPY_EXPLORATION__CLUSTER_RESCUE",
    },
    "entropy_bridge_helper_strip_broad": {
        "concept_target_terms": "correlation_polarity,entropy_production_rate",
        "priority_terms": "density_entropy,correlation,probe_induced_partition_boundary,correlation_diversity_functional,information_work_extraction_bound,erasure_channel_entropy_cost_lower_bound",
        "priority_negative_classes": "CLASSICAL_TEMPERATURE,CLASSICAL_TIME,CONTINUOUS_BATH,COMMUTATIVE_ASSUMPTION,EUCLIDEAN_METRIC,INFINITE_SET,INFINITE_RESOLUTION,PRIMITIVE_EQUALS",
        "priority_claims": "Do not emit lone information, bound, or polarity heads.||Build bound_attached_bridge branches with one bound witness and one correlation-side witness.||Build polarity_attached_bridge branches with correlation_polarity plus one correlation or density witness and one colder bound witness if available.||Keep helper_fragment_negative branches explicit and expected to split into information, bound, or polarity and fail.",
        "goal_min_graveyard_count": "18",
        "goal_min_sim_registry_count": "180",
        "focus_term_mode": "phase_seed_broad_then_priority",
        "fill_until_fuel_coverage": True,
        "fill_fuel_coverage_target": "0.85",
        "campaign_graveyard_fill_policy": "fuel_full_load",
        "graveyard_library_terms": "carnot_engine,szilard_engine,maxwell_demon",
        "track": "ENGINE_ENTROPY_EXPLORATION__HELPER_STRIP",
    },
    "entropy_bridge_rate_lift_broad": {
        "concept_target_terms": "correlation_polarity,entropy_production_rate",
        "priority_terms": "density_entropy,correlation,information_work_extraction_bound,erasure_channel_entropy_cost_lower_bound",
        "priority_negative_classes": "CLASSICAL_TEMPERATURE,CLASSICAL_TIME,CONTINUOUS_BATH,COMMUTATIVE_ASSUMPTION,EUCLIDEAN_METRIC,INFINITE_SET,INFINITE_RESOLUTION,PRIMITIVE_EQUALS",
        "priority_claims": "Do not emit lone entropy_production_rate branches.||Build rate_from_polarity_bound branches with correlation_polarity, one bound witness, and late entropy_production_rate.||Build rate_from_density_bound branches with density_entropy or correlation, one bound witness, and late entropy_production_rate.||Keep rate_cluster_negative branches explicit and expected to fail by time or bath leakage.",
        "goal_min_graveyard_count": "18",
        "goal_min_sim_registry_count": "180",
        "focus_term_mode": "phase_seed_broad_then_priority",
        "fill_until_fuel_coverage": True,
        "fill_fuel_coverage_target": "0.85",
        "campaign_graveyard_fill_policy": "fuel_full_load",
        "graveyard_library_terms": "carnot_engine,szilard_engine,maxwell_demon",
        "track": "ENGINE_ENTROPY_EXPLORATION__RATE_LIFT",
    },
    "entropy_bridge_rate_alias_broad": {
        "concept_target_terms": "correlation_polarity,entropy_production_rate,pairwise_correlation_spread_functional",
        "priority_terms": "density_entropy,correlation,information_work_extraction_bound,erasure_channel_entropy_cost_lower_bound",
        "priority_negative_classes": "CLASSICAL_TEMPERATURE,CLASSICAL_TIME,CONTINUOUS_BATH,COMMUTATIVE_ASSUMPTION,EUCLIDEAN_METRIC,INFINITE_SET,INFINITE_RESOLUTION,PRIMITIVE_EQUALS",
        "priority_claims": "Do not emit lone pairwise_correlation_spread_functional branches.||Build alias_from_rate_bound branches with correlation_polarity, entropy_production_rate, one colder witness, and only then pairwise_correlation_spread_functional as a witness-side alias candidate.||Build alias_from_density_bound branches with density_entropy or correlation, one bound witness, and pairwise_correlation_spread_functional as a witness-side alias candidate.||Keep helper_alias_negative branches explicit and expected to fail if pairwise, spread, or functional try to lead alone.",
        "goal_min_graveyard_count": "18",
        "goal_min_sim_registry_count": "180",
        "focus_term_mode": "phase_seed_broad_then_priority",
        "fill_until_fuel_coverage": True,
        "fill_fuel_coverage_target": "0.85",
        "campaign_graveyard_fill_policy": "fuel_full_load",
        "graveyard_library_terms": "carnot_engine,szilard_engine,maxwell_demon",
        "track": "ENGINE_ENTROPY_EXPLORATION__RATE_ALIAS_LIFT",
    },
    "entropy_structure_local": {
        "concept_target_terms": "probe_induced_partition_boundary,correlation_diversity_functional",
        "priority_terms": "density_entropy,correlation",
        "priority_negative_classes": "CLASSICAL_TEMPERATURE,CLASSICAL_TIME,CONTINUOUS_BATH,COMMUTATIVE_ASSUMPTION,EUCLIDEAN_METRIC,INFINITE_SET,INFINITE_RESOLUTION,PRIMITIVE_EQUALS",
        "priority_claims": "Do not reopen bridge floor terms as primary targets.||Every primary branch in this local profile should center pressure on probe_induced_partition_boundary or correlation_diversity_functional as structure targets, not as pre-cleared executable heads.||Omitting correlation_polarity from this local support floor does not demote it from the live broad executable head split.||Use density_entropy or correlation only as colder/partition witness support, never as lone heads.||Keep direct Carnot, Szilard, and Maxwell-demon naming on the negative/residue side.",
        "goal_min_graveyard_count": "10",
        "goal_min_sim_registry_count": "120",
        "focus_term_mode": "concept_local_rescue",
        "target_executed_per_call": "1",
        "fill_until_fuel_coverage": False,
        "fill_fuel_coverage_target": "0.00",
        "campaign_graveyard_fill_policy": "anchor_replay",
        "track": "ENGINE_ENTROPY_EXPLORATION__STRUCTURE_LOCAL",
    },
    "entropy_structure_diversity_broad": {
        "concept_target_terms": "correlation_diversity_functional",
        "priority_terms": "correlation_polarity,density_entropy,correlation,information_work_extraction_bound,erasure_channel_entropy_cost_lower_bound",
        "priority_negative_classes": "CLASSICAL_TEMPERATURE,CLASSICAL_TIME,CONTINUOUS_BATH,COMMUTATIVE_ASSUMPTION,EUCLIDEAN_METRIC,INFINITE_SET,INFINITE_RESOLUTION,PRIMITIVE_EQUALS",
        "priority_claims": "Build diversity_from_polarity branches with correlation_polarity as the sponsoring head and correlation_diversity_functional as a late passenger.||Build diversity_from_density branches with density_entropy or correlation as support and correlation_diversity_functional as a late passenger.||Use bound witnesses only as support, not as lone heads.||Keep partition_only_negative branches explicit and expected to fail until a colder partition witness exists.",
        "goal_min_graveyard_count": "18",
        "goal_min_sim_registry_count": "180",
        "focus_term_mode": "phase_seed_broad_then_priority",
        "fill_until_fuel_coverage": True,
        "fill_fuel_coverage_target": "0.85",
        "campaign_graveyard_fill_policy": "fuel_full_load",
        "graveyard_library_terms": "carnot_engine,szilard_engine,maxwell_demon",
        "track": "ENGINE_ENTROPY_EXPLORATION__STRUCTURE_DIVERSITY_LIFT",
    },
    "entropy_structure_diversity_alias_broad": {
        "concept_target_terms": "pairwise_correlation_spread_functional",
        "priority_terms": "correlation_polarity,density_entropy,correlation,information_work_extraction_bound,erasure_channel_entropy_cost_lower_bound",
        "priority_negative_classes": "CLASSICAL_TEMPERATURE,CLASSICAL_TIME,CONTINUOUS_BATH,COMMUTATIVE_ASSUMPTION,EUCLIDEAN_METRIC,INFINITE_SET,INFINITE_RESOLUTION,PRIMITIVE_EQUALS",
        "priority_claims": "Build alias_from_polarity branches with correlation_polarity as the sponsoring head and pairwise_correlation_spread_functional as a witness-side alias candidate.||Build alias_from_density branches with density_entropy or correlation as support and pairwise_correlation_spread_functional as a witness-side alias candidate.||Use bound witnesses only as support, not as lone heads.||Keep helper_alias_negative branches explicit and expected to fail if pairwise, spread, or functional try to lead alone.",
        "goal_min_graveyard_count": "18",
        "goal_min_sim_registry_count": "180",
        "focus_term_mode": "phase_seed_broad_then_priority",
        "fill_until_fuel_coverage": True,
        "fill_fuel_coverage_target": "0.85",
        "campaign_graveyard_fill_policy": "fuel_full_load",
        "graveyard_library_terms": "carnot_engine,szilard_engine,maxwell_demon",
        "track": "ENGINE_ENTROPY_EXPLORATION__STRUCTURE_DIVERSITY_ALIAS_LIFT",
    },
    "correlation_polarity_local": {
        "concept_target_terms": "correlation_polarity",
        "goal_min_graveyard_count": "10",
        "goal_min_sim_registry_count": "120",
        "focus_term_mode": "concept_local_rescue",
        "fill_until_fuel_coverage": False,
        "fill_fuel_coverage_target": "0.00",
        "campaign_graveyard_fill_policy": "anchor_replay",
    },
    "entropy_correlation_executable_broad": {
        "concept_target_terms": "correlation_polarity",
        "priority_terms": "correlation,density_entropy,information_work_extraction_bound,erasure_channel_entropy_cost_lower_bound",
        "priority_negative_classes": "CLASSICAL_TEMPERATURE,CLASSICAL_TIME,CONTINUOUS_BATH,COMMUTATIVE_ASSUMPTION,EUCLIDEAN_METRIC,INFINITE_SET,INFINITE_RESOLUTION,PRIMITIVE_EQUALS",
        "priority_claims": "Do not treat information or bound as successful bridge landing.||Build correlation_head branches with correlation_polarity as the executable head and correlation as the companion executable floor.||Use density_entropy only as a colder witness, not a head.||Keep information_work_extraction_bound and erasure_channel_entropy_cost_lower_bound as proposal/control witnesses only.||Keep structure-side bridge terms and alias-first routes out of the primary executable lane.",
        "primary_expected_terms": "correlation,correlation_polarity",
        "witness_only_terms": "polarity,information,bound,probe,work",
        "bridge_witness_terms": "polarity",
        "non_bridge_residue_terms": "information,bound,work,entropy,cost,erasure,lower",
        "substrate_companion_terms": "probe",
        "goal_min_graveyard_count": "18",
        "goal_min_sim_registry_count": "180",
        "focus_term_mode": "phase_seed_broad_then_priority",
        "fill_until_fuel_coverage": True,
        "fill_fuel_coverage_target": "0.85",
        "campaign_graveyard_fill_policy": "fuel_full_load",
        "graveyard_library_terms": "carnot_engine,szilard_engine,maxwell_demon",
        "track": "ENGINE_ENTROPY_EXPLORATION__CORRELATION_EXECUTABLE",
    },
    "entropy_correlation_executable_work_strip_broad": {
        "concept_target_terms": "correlation_polarity",
        "priority_terms": "correlation,density_entropy,erasure_channel_entropy_cost_lower_bound",
        "path_build_allowed_terms": "correlation,correlation_polarity,density_entropy,erasure_channel_entropy_cost_lower_bound",
        "priority_negative_classes": "CLASSICAL_TEMPERATURE,CLASSICAL_TIME,CONTINUOUS_BATH,COMMUTATIVE_ASSUMPTION,EUCLIDEAN_METRIC,INFINITE_SET,INFINITE_RESOLUTION,PRIMITIVE_EQUALS",
        "priority_claims": "Do not treat bound as successful bridge landing.||Build correlation_head branches with correlation_polarity as the executable head and correlation as the companion executable floor.||Use density_entropy only as a colder witness, not a head.||Keep information_work_extraction_bound out of this executable probe entirely.||Allow at most one colder bound witness while keeping structure-side bridge terms and alias-first routes out of the primary executable lane.",
        "primary_expected_terms": "correlation,correlation_polarity",
        "witness_only_terms": "polarity,bound,probe",
        "bridge_witness_terms": "polarity",
        "non_bridge_residue_terms": "bound,entropy,cost,erasure,lower",
        "substrate_companion_terms": "probe",
        "goal_min_graveyard_count": "18",
        "goal_min_sim_registry_count": "180",
        "focus_term_mode": "phase_seed_broad_then_priority",
        "fill_until_fuel_coverage": True,
        "fill_fuel_coverage_target": "0.85",
        "campaign_graveyard_fill_policy": "fuel_full_load",
        "graveyard_library_terms": "carnot_engine,szilard_engine,maxwell_demon",
        "track": "ENGINE_ENTROPY_EXPLORATION__CORRELATION_EXECUTABLE_WORK_STRIP",
    },
    "entropy_correlation_executable_seed_clamped_broad": {
        "concept_target_terms": "correlation_polarity",
        "priority_terms": "correlation,density_entropy,information_work_extraction_bound,erasure_channel_entropy_cost_lower_bound",
        "seed_allowed_terms": "finite_dimensional_hilbert_space,density_matrix,probe_operator,cptp_channel,partial_trace,correlation,correlation_polarity,density_entropy,erasure_channel_entropy_cost_lower_bound",
        "priority_negative_classes": "CLASSICAL_TEMPERATURE,CLASSICAL_TIME,CONTINUOUS_BATH,COMMUTATIVE_ASSUMPTION,EUCLIDEAN_METRIC,INFINITE_SET,INFINITE_RESOLUTION,PRIMITIVE_EQUALS",
        "priority_claims": "Clamp broad seed away from information_work_extraction_bound while preserving the proven correlation executable route.||Build correlation_head branches with correlation_polarity as the executable head and correlation as the companion executable floor.||Use density_entropy only as a colder witness, not a head.||Keep information_work_extraction_bound as proposal/control only unless explicitly reintroduced after seed.||Keep structure-side bridge terms and alias-first routes out of the primary executable lane.",
        "primary_expected_terms": "correlation,correlation_polarity",
        "witness_only_terms": "polarity,information,bound,probe,work",
        "bridge_witness_terms": "polarity",
        "non_bridge_residue_terms": "information,bound,work,entropy,cost,erasure,lower",
        "substrate_companion_terms": "probe",
        "goal_min_graveyard_count": "18",
        "goal_min_sim_registry_count": "180",
        "focus_term_mode": "phase_seed_broad_then_priority",
        "fill_until_fuel_coverage": True,
        "fill_fuel_coverage_target": "0.85",
        "campaign_graveyard_fill_policy": "fuel_full_load",
        "graveyard_library_terms": "carnot_engine,szilard_engine,maxwell_demon",
        "track": "ENGINE_ENTROPY_EXPLORATION__CORRELATION_EXECUTABLE_SEED_CLAMP",
    },
    "entropy_correlation_executable_cluster_clamp_broad": {
        "concept_target_terms": "correlation_polarity",
        "priority_terms": "correlation,density_entropy,information_work_extraction_bound,erasure_channel_entropy_cost_lower_bound",
        "seed_target_terms": "correlation,density_entropy,erasure_channel_entropy_cost_lower_bound",
        "seed_force_transition_min_executed": "1",
        "seed_force_transition_min_graveyard": "45",
        "seed_force_transition_min_kill_diversity": "8",
        "path_build_allowed_terms": "correlation,correlation_polarity,density_entropy",
        "rescue_allowed_terms": "correlation,correlation_polarity,density_entropy,probe",
        "priority_negative_classes": "CLASSICAL_TEMPERATURE,CLASSICAL_TIME,CONTINUOUS_BATH,COMMUTATIVE_ASSUMPTION,EUCLIDEAN_METRIC,INFINITE_SET,INFINITE_RESOLUTION,PRIMITIVE_EQUALS",
        "priority_claims": "Allow one broad executed seed cycle to establish live correlation pressure, then clamp path_build and rescue into the correlation executable family.||Do not let information_work_extraction_bound or erasure_channel_entropy_cost_lower_bound become later-phase executable heads.||Keep density_entropy as the only colder witness inside the active executable family.||Allow probe only as a substrate companion in rescue.||Treat information, bound, and work as non-bridge residue that should not survive the later-phase clamp.",
        "primary_expected_terms": "correlation,correlation_polarity",
        "witness_only_terms": "polarity,density_entropy,probe",
        "bridge_witness_terms": "polarity,density_entropy",
        "probe_companion_terms": "unitary_operator,qit_master_conjunction",
        "non_bridge_residue_terms": "information,bound,work,entropy,cost,erasure,lower",
        "substrate_companion_terms": "probe",
        "goal_min_graveyard_count": "18",
        "goal_min_sim_registry_count": "180",
        "focus_term_mode": "phase_seed_broad_then_priority",
        "fill_until_fuel_coverage": True,
        "fill_fuel_coverage_target": "0.85",
        "campaign_graveyard_fill_policy": "fuel_full_load",
        "graveyard_library_terms": "carnot_engine,szilard_engine,maxwell_demon",
        "track": "ENGINE_ENTROPY_EXPLORATION__CORRELATION_EXECUTABLE_CLUSTER_CLAMP",
    },
    "entropy_rate_local": {
        "concept_target_terms": "entropy_production_rate",
        "goal_min_graveyard_count": "10",
        "goal_min_sim_registry_count": "120",
        "focus_term_mode": "concept_local_rescue",
        "fill_until_fuel_coverage": False,
        "fill_fuel_coverage_target": "0.00",
        "campaign_graveyard_fill_policy": "anchor_replay",
    },
    "entropy_bookkeeping_pair_local": {
        "concept_target_terms": "entropy_production_rate,erasure_channel_entropy_cost_lower_bound",
        "goal_min_graveyard_count": "10",
        "goal_min_sim_registry_count": "120",
        "focus_term_mode": "concept_local_rescue",
        "fill_until_fuel_coverage": False,
        "fill_fuel_coverage_target": "0.00",
        "campaign_graveyard_fill_policy": "anchor_replay",
    },
}


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _all_target_terms_allowed(*, state: dict | None, concept_target_terms: list[str]) -> bool:
    if not state:
        return False
    registry = state.get("term_registry", {})
    for term in concept_target_terms:
        entry = registry.get(term)
        if not isinstance(entry, dict):
            return False
        if str(entry.get("state", "")).strip() != "CANONICAL_ALLOWED":
            return False
    return True


def _all_terms_canonical(*, state: dict | None, terms: list[str]) -> bool:
    if not isinstance(state, dict):
        return False
    registry = state.get("term_registry", {})
    if not isinstance(registry, dict):
        return False
    cleaned = [str(term).strip() for term in terms if str(term).strip()]
    if not cleaned:
        return False
    for term in cleaned:
        entry = registry.get(term)
        if not isinstance(entry, dict):
            return False
        if str(entry.get("state", "")).strip() != "CANONICAL_ALLOWED":
            return False
    return True


def _selector_stop_summary(row: dict) -> str:
    return selector_stop_summary(row)


def _emit_wrapper_report(*, run_id: str, profile: str, provider: str, subprocess_rc: int) -> Path:
    run_dir = RUNS_ROOT / run_id
    report_path = run_dir / "reports" / "graveyard_first_validity_wrapper_report.json"
    driver_report = _read_json(run_dir / "reports" / "a1_external_memo_batch_driver_report.json") or {}
    serial_report = _read_json(run_dir / "reports" / "a1_exchange_serial_runner_report.json") or {}
    state = _read_json(run_dir / "state.json") or {}
    profile_cfg = PROFILE_MAP.get(profile, {})
    concept_target_terms = [part.strip() for part in str(profile_cfg.get("concept_target_terms", "")).split(",") if part.strip()]
    primary_expected_terms = [part.strip() for part in str(profile_cfg.get("primary_expected_terms", "")).split(",") if part.strip()]
    witness_only_terms = [part.strip() for part in str(profile_cfg.get("witness_only_terms", "")).split(",") if part.strip()]
    bridge_witness_terms = [part.strip() for part in str(profile_cfg.get("bridge_witness_terms", "")).split(",") if part.strip()]
    non_bridge_residue_terms = [part.strip() for part in str(profile_cfg.get("non_bridge_residue_terms", "")).split(",") if part.strip()]
    substrate_companion_terms = [part.strip() for part in str(profile_cfg.get("substrate_companion_terms", "")).split(",") if part.strip()]
    term_registry = state.get("term_registry", {}) if isinstance(state, dict) else {}
    canonical_allowed_terms = sorted(
        term
        for term, entry in term_registry.items()
        if isinstance(entry, dict) and str(entry.get("state", "")).strip() == "CANONICAL_ALLOWED"
    )
    primary_admitted_terms = [term for term in primary_expected_terms if term in canonical_allowed_terms]
    witness_only_terms_present = [term for term in witness_only_terms if term in canonical_allowed_terms]
    bridge_witness_terms_present = [term for term in bridge_witness_terms if term in canonical_allowed_terms]
    non_bridge_residue_terms_present = [term for term in non_bridge_residue_terms if term in canonical_allowed_terms]
    substrate_companion_terms_present = [term for term in substrate_companion_terms if term in canonical_allowed_terms]
    state_counts = driver_report.get("state_counts", {}) if isinstance(driver_report, dict) else {}
    driver_timeline = driver_report.get("timeline", []) if isinstance(driver_report, dict) else []
    serial_timeline = serial_report.get("timeline", []) if isinstance(serial_report, dict) else []
    use_serial_aggregate = (
        str(provider).strip() == "local_stub"
        and isinstance(serial_report, dict)
        and str(serial_report.get("schema", "")).strip() == "A1_EXCHANGE_SERIAL_RUNNER_REPORT_v1"
    )
    stop_reason = ""
    stop_reason_sequence = 0
    stop_reason_surface = ""
    stop_reason_summary = ""
    stop_reason_cold_core_sequence = 0
    stop_reason_cold_core_sequence_mismatch_stage = ""
    selector_warning_count = 0
    selector_warning_codes: list[str] = []
    selector_warning_categories: list[str] = []
    selector_support_warning_present = False
    selector_warning_examples: list[str] = []
    if use_serial_aggregate:
        stop_reason = str(serial_report.get("last_stop_reason", "")).strip()
        stop_reason_sequence = int(serial_report.get("last_first_failure_sequence", 0) or 0)
        stop_reason_surface = str(serial_report.get("last_first_failure_surface", "")).strip()
        stop_reason_summary = str(serial_report.get("last_first_failure_summary", "")).strip()
        selector_provenance_fields = extract_selector_provenance_fields(
            {
                "selector_cold_core_sequence": serial_report.get("last_selector_cold_core_sequence", 0),
                "cold_core_sequence_mismatch_stage": serial_report.get("last_cold_core_sequence_mismatch_stage", ""),
            }
        )
        stop_reason_cold_core_sequence = int(selector_provenance_fields.get("selector_cold_core_sequence", 0) or 0)
        stop_reason_cold_core_sequence_mismatch_stage = str(selector_provenance_fields.get("cold_core_sequence_mismatch_stage", "")).strip()
        selector_warning_fields = extract_selector_warning_fields(
            {
                "selector_warning_count": serial_report.get("last_selector_warning_count", 0),
                "selector_warning_codes": serial_report.get("last_selector_warning_codes", []),
                "selector_warning_categories": serial_report.get("last_selector_warning_categories", []),
                "selector_support_warning_present": serial_report.get("last_selector_support_warning_present", False),
                "selector_warning_examples": serial_report.get("last_selector_warning_examples", []),
            }
        )
        selector_warning_count = int(selector_warning_fields.get("selector_warning_count", 0) or 0)
        selector_warning_codes = list(selector_warning_fields.get("selector_warning_codes", []) or [])
        selector_warning_categories = list(selector_warning_fields.get("selector_warning_categories", []) or [])
        selector_support_warning_present = bool(selector_warning_fields.get("selector_support_warning_present", False))
        selector_warning_examples = list(selector_warning_fields.get("selector_warning_examples", []) or [])
        if not stop_reason:
            stop_reason = str(serial_report.get("last_status", "")).strip()
    if not stop_reason and isinstance(driver_timeline, list) and driver_timeline:
        last_driver_row = driver_timeline[-1] or {}
        stop_reason = str(last_driver_row.get("run_stop_reason", "")).strip()
        if not stop_reason_sequence:
            stop_reason_sequence = int(last_driver_row.get("first_failure_sequence", 0) or 0)
        if not stop_reason_surface:
            stop_reason_surface = str(last_driver_row.get("first_failure_surface", "")).strip()
        if not stop_reason_summary:
            stop_reason_summary = str(last_driver_row.get("first_failure_summary", "")).strip()
        if not stop_reason_summary and stop_reason == "STOPPED__PACK_SELECTOR_FAILED":
            stop_reason_summary = _selector_stop_summary(last_driver_row if isinstance(last_driver_row, dict) else {})
        if not stop_reason_cold_core_sequence:
            selector_provenance_fields = extract_selector_provenance_fields(last_driver_row if isinstance(last_driver_row, dict) else {})
            stop_reason_cold_core_sequence = int(selector_provenance_fields.get("selector_cold_core_sequence", 0) or 0)
        if not stop_reason_cold_core_sequence_mismatch_stage:
            selector_provenance_fields = extract_selector_provenance_fields(last_driver_row if isinstance(last_driver_row, dict) else {})
            stop_reason_cold_core_sequence_mismatch_stage = str(selector_provenance_fields.get("cold_core_sequence_mismatch_stage", "")).strip()
        if selector_warning_count <= 0:
            selector_warning_fields = extract_selector_warning_fields(last_driver_row if isinstance(last_driver_row, dict) else {})
            selector_warning_count = int(selector_warning_fields.get("selector_warning_count", 0) or 0)
            selector_warning_codes = list(selector_warning_fields.get("selector_warning_codes", []) or [])
            selector_warning_categories = list(selector_warning_fields.get("selector_warning_categories", []) or [])
            selector_support_warning_present = bool(selector_warning_fields.get("selector_support_warning_present", False))
            selector_warning_examples = list(selector_warning_fields.get("selector_warning_examples", []) or [])
    if not stop_reason:
        stop_reason = str(driver_report.get("status", "")).strip()
    all_terms_allowed = _all_target_terms_allowed(state=state, concept_target_terms=concept_target_terms)
    graveyard_count = int(state_counts.get("graveyard_count", 0) or 0)
    kill_log_count = int(state_counts.get("kill_log_count", 0) or 0)
    executed_cycles = int(driver_report.get("executed_cycles", 0) or 0)
    wait_cycles = int(driver_report.get("wait_cycles", 0) or 0)
    if use_serial_aggregate:
        executed_cycles = int(serial_report.get("executed_cycles_total", executed_cycles) or 0)
        wait_cycles = int(serial_report.get("wait_cycles_total", wait_cycles) or 0)
    wrapper_status = "FAIL__SUBPROCESS"
    interpretation = "subprocess_failed"
    if int(subprocess_rc) == 0:
        wrapper_status = "PASS__EXECUTED_CYCLE" if executed_cycles > 0 else "PASS__NO_EXECUTED_CYCLE"
        interpretation = "executed_cycle" if executed_cycles > 0 else "no_executed_cycle"
        if stop_reason == "STOPPED__COLD_CORE_SEQUENCE_MISMATCH":
            wrapper_status = "FAIL__COLD_CORE_SEQUENCE_MISMATCH"
            interpretation = "cold_core_sequence_mismatch"
        if executed_cycles > 0 and primary_admitted_terms and non_bridge_residue_terms_present:
            interpretation = "executed_cycle_with_non_bridge_residue"
        elif executed_cycles > 0 and primary_admitted_terms and witness_only_terms_present:
            interpretation = "executed_cycle_with_helper_residue"
        elif executed_cycles > 0 and primary_admitted_terms and (bridge_witness_terms_present or substrate_companion_terms_present):
            interpretation = "executed_cycle_with_expected_companions"
        if (
            str(profile_cfg.get("focus_term_mode", "")).strip() == "concept_local_rescue"
            and stop_reason == "STOPPED__PACK_SELECTOR_FAILED"
            and all_terms_allowed
            and graveyard_count > 0
            and kill_log_count > 0
        ):
            wrapper_status = "PASS__CONCEPT_LOCAL_SEED_SATURATED"
            interpretation = "concept_local_seed_saturated"
        if stop_reason == "STOPPED__PACK_SELECTOR_FAILED" and isinstance(driver_timeline, list) and driver_timeline:
            last_row = driver_timeline[-1] or {}
            fill_status = last_row.get("fill_status", {}) if isinstance(last_row, dict) else {}
            path_build_allowed_terms = []
            if isinstance(fill_status, dict):
                raw_allowed = fill_status.get("path_build_allowed_terms_active", [])
                if isinstance(raw_allowed, list):
                    path_build_allowed_terms = [str(term).strip() for term in raw_allowed if str(term).strip()]
            if (
                path_build_allowed_terms
                and _all_terms_canonical(state=state, terms=path_build_allowed_terms)
                and graveyard_count > 0
                and kill_log_count > 0
            ):
                wrapper_status = "PASS__PATH_BUILD_SATURATED"
                interpretation = "path_build_saturated_after_seed"
        if (
            stop_reason == "STOPPED__RESCUE_NOVELTY_STALL"
            and executed_cycles > 0
            and graveyard_count > 0
            and kill_log_count > 0
        ):
            wrapper_status = "PASS__RESCUE_NOVELTY_STALLED"
            interpretation = "rescue_novelty_stalled_after_executed_cycle"
    payload = {
        "schema": "GRAVEYARD_FIRST_VALIDITY_WRAPPER_REPORT_v1",
        "run_id": run_id,
        "profile": profile,
        "provider": provider,
        "subprocess_returncode": int(subprocess_rc),
        "wrapper_status": wrapper_status,
        "interpretation": interpretation,
        "stop_reason": stop_reason,
        "stop_reason_sequence": int(stop_reason_sequence),
        "stop_reason_surface": stop_reason_surface,
        "stop_reason_summary": stop_reason_summary,
        "executed_cycles": executed_cycles,
        "wait_cycles": wait_cycles,
        "concept_target_terms": concept_target_terms,
        "primary_expected_terms": primary_expected_terms,
        "primary_admitted_terms": primary_admitted_terms,
        "witness_only_terms": witness_only_terms,
        "witness_only_terms_present": witness_only_terms_present,
        "bridge_witness_terms": bridge_witness_terms,
        "bridge_witness_terms_present": bridge_witness_terms_present,
        "non_bridge_residue_terms": non_bridge_residue_terms,
        "non_bridge_residue_terms_present": non_bridge_residue_terms_present,
        "substrate_companion_terms": substrate_companion_terms,
        "substrate_companion_terms_present": substrate_companion_terms_present,
        "canonical_allowed_terms": canonical_allowed_terms,
        "all_target_terms_allowed": all_terms_allowed,
        "state_counts": state_counts,
        "driver_report_path": str(run_dir / "reports" / "a1_external_memo_batch_driver_report.json"),
        "serial_report_path": str(run_dir / "reports" / "a1_exchange_serial_runner_report.json"),
        "serial_aggregate_used": use_serial_aggregate,
        "serial_timeline": serial_timeline if use_serial_aggregate else [],
        "state_path": str(run_dir / "state.json"),
    }
    if stop_reason_cold_core_sequence > 0:
        payload["stop_reason_cold_core_sequence"] = int(stop_reason_cold_core_sequence)
    if stop_reason_cold_core_sequence_mismatch_stage:
        payload["stop_reason_cold_core_sequence_mismatch_stage"] = stop_reason_cold_core_sequence_mismatch_stage
    if selector_warning_count > 0:
        payload["selector_warning_count"] = int(selector_warning_count)
        payload["selector_support_warning_present"] = bool(selector_support_warning_present)
    if selector_warning_codes:
        payload["selector_warning_codes"] = list(selector_warning_codes)
    if selector_warning_categories:
        payload["selector_warning_categories"] = list(selector_warning_categories)
    if selector_warning_examples:
        payload["selector_warning_examples"] = list(selector_warning_examples)
    _write_json(report_path, payload)
    return report_path


def _shared_flags(
    *,
    run_id: str,
    profile: str,
    path_build_novelty_stall_max_override: int | None = None,
    rescue_novelty_stall_max_override: int | None = None,
) -> list[str]:
    if profile not in PROFILE_MAP:
        raise ValueError(f"unknown profile: {profile}")
    profile_cfg = PROFILE_MAP[profile]
    out = [
        "--preset",
        "graveyard13",
        "--process-mode",
        "concept_path_rescue",
        "--concept-target-terms",
        str(profile_cfg["concept_target_terms"]),
        "--seed-target-terms",
        str(profile_cfg.get("seed_target_terms", "")),
        "--priority-terms",
        str(profile_cfg.get("priority_terms", "")),
        "--path-build-allowed-terms",
        str(profile_cfg.get("path_build_allowed_terms", "")),
        "--rescue-allowed-terms",
        str(profile_cfg.get("rescue_allowed_terms", "")),
        "--seed-allowed-terms",
        str(profile_cfg.get("seed_allowed_terms", "")),
        "--priority-negative-classes",
        str(profile_cfg.get("priority_negative_classes", "")),
        "--priority-claims",
        str(profile_cfg.get("priority_claims", "")),
        "--focus-term-mode",
        str(profile_cfg.get("focus_term_mode", "concept_plus_rescue")),
        "--debate-strategy",
        "graveyard_then_recovery",
        "--debate-mode",
        "graveyard_first",
        "--fill-until-graveyard-dominates",
        "--fill-graveyard-minus-canonical-min",
        "8",
        "--fill-min-graveyard-term-count",
        "8",
        "--graveyard-fill-cycles",
        "10",
        "--graveyard-fill-max-stall-cycles",
        "2",
        "--path-build-min-cycles",
        "8",
        "--path-build-max-cycles",
        "24",
        "--path-build-novelty-stall-max",
        str(int(path_build_novelty_stall_max_override) if path_build_novelty_stall_max_override is not None else 6),
        "--seed-force-transition-min-executed",
        str(profile_cfg.get("seed_force_transition_min_executed", "-1")),
        "--seed-force-transition-min-graveyard",
        str(profile_cfg.get("seed_force_transition_min_graveyard", "0")),
        "--seed-force-transition-min-kill-diversity",
        str(profile_cfg.get("seed_force_transition_min_kill_diversity", "0")),
        "--rescue-start-min-canonical",
        "0",
        "--rescue-start-min-graveyard",
        "12",
        "--rescue-start-min-kill-diversity",
        "6",
        "--rescue-novelty-stall-max",
        str(int(rescue_novelty_stall_max_override) if rescue_novelty_stall_max_override is not None else 6),
        "--seed-max-terms-per-cycle",
        str(profile_cfg.get("seed_max_terms_per_cycle", "24")),
        "--path-max-terms-per-cycle",
        str(profile_cfg.get("path_max_terms_per_cycle", "18")),
        "--rescue-max-terms-per-cycle",
        str(profile_cfg.get("rescue_max_terms_per_cycle", "16")),
        "--campaign-graveyard-fill-policy",
        str(profile_cfg.get("campaign_graveyard_fill_policy", "fuel_full_load")),
        "--campaign-forbid-rescue-during-graveyard-fill",
        "--campaign-recovery-min-rescue-from-fields",
        str(profile_cfg.get("campaign_recovery_min_rescue_from_fields", "1")),
        "--min-executed-cycles-before-goal",
        "12",
        "--goal-min-graveyard-count",
        str(profile_cfg["goal_min_graveyard_count"]),
        "--goal-min-sim-registry-count",
        str(profile_cfg["goal_min_sim_registry_count"]),
        "--track",
        str(profile_cfg.get("track", "ENGINE_ENTROPY_EXPLORATION")),
    ]
    if bool(profile_cfg.get("fill_until_fuel_coverage", True)):
        out.extend(
            [
                "--fill-until-fuel-coverage",
                "--fill-fuel-coverage-target",
                str(profile_cfg.get("fill_fuel_coverage_target", "0.85")),
            ]
        )
    graveyard_library_terms = str(profile_cfg.get("graveyard_library_terms", "")).strip()
    if graveyard_library_terms:
        out.extend(["--graveyard-library-terms", graveyard_library_terms])
    probe_companion_terms = str(profile_cfg.get("probe_companion_terms", "")).strip()
    if probe_companion_terms:
        out.extend(["--probe-companion-terms", probe_companion_terms])
    if bool(profile_cfg.get("fill_until_library_coverage", False)):
        out.extend(
            [
                "--fill-until-library-coverage",
                "--fill-library-coverage-target",
                str(profile_cfg.get("fill_library_coverage_target", "1.0")),
            ]
        )
    return out


def build_driver_cmd(
    *,
    run_id: str,
    profile: str,
    clean: bool,
    path_build_novelty_stall_max_override: int | None = None,
    rescue_novelty_stall_max_override: int | None = None,
) -> list[str]:
    profile_cfg = PROFILE_MAP[profile]
    cmd = [
        "python3",
        str(DRIVER),
        "--run-id",
        str(run_id),
        "--runs-root",
        str(RUNS_ROOT),
        "--a2-state-dir",
        str(A2_STATE),
        "--memo-provider-mode",
        "exchange",
        *_shared_flags(
            run_id=run_id,
            profile=profile,
            path_build_novelty_stall_max_override=path_build_novelty_stall_max_override,
            rescue_novelty_stall_max_override=rescue_novelty_stall_max_override,
        ),
        "--target-executed-cycles",
        str(profile_cfg.get("target_executed_per_call", "24")),
        "--strict-local-gate-check",
    ]
    if clean:
        cmd.append("--clean")
    return cmd


def build_serial_cmd(
    *,
    run_id: str,
    profile: str,
    clean: bool,
    steps: int,
    path_build_novelty_stall_max_override: int | None = None,
    rescue_novelty_stall_max_override: int | None = None,
) -> list[str]:
    profile_cfg = PROFILE_MAP[profile]
    cmd = [
        "python3",
        str(SERIAL),
        "--run-id",
        str(run_id),
        "--runs-root",
        str(RUNS_ROOT),
        "--a2-state-dir",
        str(A2_STATE),
        "--steps",
        str(int(steps)),
        "--target-executed-per-call",
        str(profile_cfg.get("target_executed_per_call", "1")),
        "--max-wait-cycles",
        "1",
        "--strict-local-gate-check",
        *_shared_flags(
            run_id=run_id,
            profile=profile,
            path_build_novelty_stall_max_override=path_build_novelty_stall_max_override,
            rescue_novelty_stall_max_override=rescue_novelty_stall_max_override,
        ),
    ]
    if clean:
        cmd.append("--clean")
    return cmd


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Run a graveyard-first validity campaign for a named concept family.")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--profile", choices=sorted(PROFILE_MAP.keys()), default="substrate_base")
    ap.add_argument("--provider", choices=["local_stub", "exchange_only"], default="local_stub")
    ap.add_argument("--steps", type=int, default=24)
    ap.add_argument("--clean", action="store_true")
    ap.add_argument("--seed-from-run-id")
    ap.add_argument("--path-build-novelty-stall-max", type=int)
    ap.add_argument("--rescue-novelty-stall-max", type=int)
    ap.add_argument("--print-cmd", action="store_true")
    args = ap.parse_args(argv)

    seed_from_run_id = str(args.seed_from_run_id or "").strip()
    if seed_from_run_id:
        bootstrap_cmd = [
            "python3",
            str(BOOTSTRAP),
            "--source-run-id",
            seed_from_run_id,
            "--dest-run-id",
            str(args.run_id),
            "--runs-root",
            str(RUNS_ROOT),
        ]
        if bool(args.clean):
            bootstrap_cmd.append("--clean-dest")
        if bool(args.print_cmd):
            print(" ".join(bootstrap_cmd))
        else:
            bootstrap_proc = subprocess.run(bootstrap_cmd, cwd=str(REPO), check=False)
            if int(bootstrap_proc.returncode) != 0:
                return int(bootstrap_proc.returncode)

    if str(args.provider) == "local_stub":
        cmd = build_serial_cmd(
            run_id=str(args.run_id),
            profile=str(args.profile),
            clean=(bool(args.clean) and not seed_from_run_id),
            steps=int(args.steps),
            path_build_novelty_stall_max_override=args.path_build_novelty_stall_max,
            rescue_novelty_stall_max_override=args.rescue_novelty_stall_max,
        )
    else:
        cmd = build_driver_cmd(
            run_id=str(args.run_id),
            profile=str(args.profile),
            clean=(bool(args.clean) and not seed_from_run_id),
            path_build_novelty_stall_max_override=args.path_build_novelty_stall_max,
            rescue_novelty_stall_max_override=args.rescue_novelty_stall_max,
        )
    if bool(args.print_cmd):
        print(" ".join(cmd))
        return 0
    proc = subprocess.run(cmd, cwd=str(REPO), check=False)
    report_path = _emit_wrapper_report(
        run_id=str(args.run_id),
        profile=str(args.profile),
        provider=str(args.provider),
        subprocess_rc=int(proc.returncode),
    )
    report = _read_json(report_path)
    stdout_payload = {
        "wrapper_report_path": str(report_path),
        "wrapper_status": str(report.get("wrapper_status", "")).strip(),
        "stop_reason": str(report.get("stop_reason", "")).strip(),
        "stop_reason_sequence": int(report.get("stop_reason_sequence", 0) or 0),
        "stop_reason_surface": str(report.get("stop_reason_surface", "")).strip(),
        "stop_reason_summary": str(report.get("stop_reason_summary", "")).strip(),
    }
    stop_reason_cold_core_sequence = int(report.get("stop_reason_cold_core_sequence", 0) or 0)
    if stop_reason_cold_core_sequence > 0:
        stdout_payload["stop_reason_cold_core_sequence"] = stop_reason_cold_core_sequence
    stop_reason_cold_core_sequence_mismatch_stage = str(
        report.get("stop_reason_cold_core_sequence_mismatch_stage", "")
    ).strip()
    if stop_reason_cold_core_sequence_mismatch_stage:
        stdout_payload["stop_reason_cold_core_sequence_mismatch_stage"] = (
            stop_reason_cold_core_sequence_mismatch_stage
        )
    print(json.dumps(stdout_payload, sort_keys=True))
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
