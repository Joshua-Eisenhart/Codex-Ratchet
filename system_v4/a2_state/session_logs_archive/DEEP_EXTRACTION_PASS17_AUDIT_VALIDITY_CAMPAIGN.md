# Pass 17 — Autoratchet Cycle Audit + Graveyard Validity Campaign

**Files read this pass:**
- `run_a1_autoratchet_cycle_audit.py` (1286 lines, fully read)
- `run_graveyard_first_validity_campaign.py` (931 lines, fully read)

---

## 1. Autoratchet Cycle Audit — Post-Run Structural Verifier

### Role
Runs after a campaign completes. Opens the latest ZIP packet strategy payload and cross-checks **every structural invariant** against the family slice schema and state. This is pure deterministic verification — no LLM, no inference.

### 40+ Checks (PASS/FAIL with detail strings)

**Core checks (always run):**
- SUMMARY_PRESENT, CAMPAIGN_SUMMARY_PRESENT
- STEPS_EXECUTED ≥ 1, STEP_COUNTS_CONSISTENT (summary vs campaign)
- ZIP_PACKETS_PRESENT ≥ 1
- BRANCH_PRESSURE_VISIBLE (sim_registry_count ≥ 1)
- GRAVEYARD_FILL_VISIBLE (graveyard_count ≥ min threshold)

**Family slice checks (only when goal_source = "family_slice"):**
- FAMILY_SLICE_JSON_PRESENT, ID_PRESENT, ID_MATCH
- STRATEGY_FAMILY_SLICE_ID_MATCH
- LANES_VISIBLE (expected ⊆ visible)
- HEAD_VISIBLE (expected ⊆ visible)
- NEGATIVE_CLASSES_VISIBLE (expected ⊆ visible)
- GOAL_NEGATIVE_CLASS_VISIBLE
- MATH_SURFACES_VISIBLE
- TARGET_CLASS_VISIBLE (prefix match)
- GRAVEYARD_NEGATIVE_CLASSES_VISIBLE, LIMIT_VISIBLE
- PROBE_TERMS_DECLARED
- LANE_MINIMUMS_VISIBLE + _SATISFIED (per-lane min_branches)
- BRANCH_REQUIREMENTS_VISIBLE (primary/alternative/negative/rescue)
- LINEAGE_REQUIREMENTS_VISIBLE
- BRANCH_LINEAGE_VISIBLE (complete + fields match)
- BRANCH_PARENTAGE_VISIBLE (internal DAG consistency)
- BRANCH_GROUPS_VISIBLE (complete + map match)
- BRANCH_TRACKS_VISIBLE (complete + map match)
- RESCUE_LINEAGE_VISIBLE (linkages ≥ rescuer lanes)
- REQUIRED_SIM_FAMILIES_VISIBLE
- SIM_FAMILY_TIERS_VISIBLE
- RECOVERY_SIM_FAMILIES_VISIBLE
- RESCUE_SOURCE_LIMIT_VISIBLE
- BUDGET_VISIBLE (max_items, max_sims match debate mode)
- SIM_FAMILY_OPERATOR_MAP_VISIBLE + _CANONICAL
- OPERATOR_POLICY_SOURCES_VISIBLE + _CANONICAL
- GOAL_PROBE_TERM_VISIBLE, PROBE_SOURCE_OWNED
- GOAL_SIM_TIER_VISIBLE

### SIM Tier Hierarchy (T0→T6)
T0_ATOM → T1_COMPOUND → T2_OPERATOR → T3_STRUCTURE → T4_SYSTEM_SEGMENT → T5_ENGINE → T6_WHOLE_SYSTEM

### SIM Family → Operator Defaults
| Family | Default Operator |
|--------|-----------------|
| BASELINE | OP_BIND_SIM |
| BOUNDARY_SWEEP | OP_REPAIR_DEF_FIELD |
| PERTURBATION | OP_MUTATE_LEXEME |
| COMPOSITION_STRESS | OP_REORDER_DEPENDENCIES |
| ADVERSARIAL_NEG | OP_NEG_SIM_EXPAND |

---

## 2. Graveyard Validity Campaign — Preconfigured Campaign Recipes

### Role
Top-level orchestrator that wraps the memo batch driver or serial runner with predefined campaign profiles. Each profile specifies exactly which terms to target, what negative classes to use, which terms to exclude, and what success thresholds to enforce.

### 25+ Campaign Profiles (PROFILE_MAP keys)

**Substrate family profiles:**
- `substrate_base` / `substrate_base_concept_local` — hilbert_space, density_matrix, probe_operator, cptp_channel, partial_trace
- `substrate_enrichment` / multiple `_concept_local` / `_dynamics_*` variants — unitary_operator, commutator_operator, hamiltonian_operator, lindblad_generator

**Entropy bridge profiles (extensive):**
- `entropy_bridge_local` / `_broad` — correlation_polarity, entropy_production_rate
- `_residue_broad`, `_thermal_time_broad`, `_reformulation_broad`, `_colder_witness_broad`, `_helper_lift_broad`, `_cluster_rescue_broad`, `_helper_strip_broad`, `_rate_lift_broad`, `_rate_alias_broad` — all with specific priority_claims directing term interaction patterns

**Entropy structure profiles:**
- `entropy_structure_local` / `_diversity_broad` / `_diversity_alias_broad` — probe_induced_partition_boundary, correlation_diversity_functional, pairwise_correlation_spread_functional

**Correlation executable profiles:**
- `entropy_correlation_executable_broad` / `_work_strip_broad` / `_seed_clamped_broad` / `_cluster_clamp_broad` — correlation_polarity as executable head

**Other profiles:**
- `correlation_polarity_local`, `entropy_rate_local`, `entropy_bookkeeping_pair_local`

### Profile Configuration Fields
Each profile specifies: `concept_target_terms`, `goal_min_graveyard_count`, `goal_min_sim_registry_count`, `focus_term_mode`, `fill_until_fuel_coverage`, `fill_fuel_coverage_target`, `campaign_graveyard_fill_policy`, and optionally `priority_terms`, `priority_negative_classes`, `priority_claims`, `graveyard_library_terms`, `seed_target_terms`, `path_build_allowed_terms`, `rescue_allowed_terms`, `track`.

### Wrapper Report Interpretation
The campaign emits a `GRAVEYARD_FIRST_VALIDITY_WRAPPER_REPORT_v1` with status interpretations:
- PASS__EXECUTED_CYCLE — at least one cycle ran
- PASS__CONCEPT_LOCAL_SEED_SATURATED — all target terms canonical, graveyard present
- PASS__PATH_BUILD_SATURATED — path_build_allowed_terms all canonical
- PASS__RESCUE_NOVELTY_STALLED — rescue stalled but ran
- FAIL__SUBPROCESS, FAIL__COLD_CORE_SEQUENCE_MISMATCH

---

## 3. JP Determinism Principle Assessment

Both tools are **100% deterministic, zero LLM**:
- The audit runs 40+ structural checks with no inference — pure field comparisons
- The campaign profiles are hand-tuned parameter sets — the priority_claims are string templates passed to the deterministic planner, not LLM prompts
- The wrapper report interpretation is a flat if/elif chain

### What v4 should carry forward
- **The 40-check audit pattern**: every structural invariant explicitly verified = perfect for v4's deterministic graph
- **Profile-based campaign recipes**: preconfigured parameter sets for different concept families = reusable templates
- **The SIM tier hierarchy (T0→T6)** and family→operator defaults should be runtime constants, not LLM-generated
- **priority_claims** are the only field where natural language enters — in v4, these could become deterministic constraint nodes in the graph rather than string templates

---

## Concepts Extracted

| ID | Concept | Source |
|----|---------|--------|
| P17_01 | 40+ structural checks in autoratchet audit | audit L749-1228 |
| P17_02 | SIM tier hierarchy T0_ATOM→T6_WHOLE_SYSTEM | audit L414-422 |
| P17_03 | SIM family→operator defaults (BASELINE→OP_BIND_SIM, etc.) | audit L388-394 |
| P17_04 | Branch lineage/parentage DAG integrity checks | audit L92-208 |
| P17_05 | Family slice budget per debate mode | audit L433-459 |
| P17_06 | 25+ preconfigured campaign profiles by concept family | validity L23-408 |
| P17_07 | Profile fields: concept_target_terms, priority_claims, graveyard_library_terms, fill policies | validity passim |
| P17_08 | Wrapper report interpretation (PASS/FAIL statuses) | validity L563-609 |
| P17_09 | Seed-from-run-id bootstrap for incremental campaigns | validity L858-877 |
| P17_10 | priority_claims as string templates → future deterministic constraint nodes | validity profiles |
