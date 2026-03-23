# A1_INTEGRATION_BATCH__LIVE_FAMILY_HINT_COVERAGE__v1
Status: PROPOSED / NONCANONICAL / BOUNDED A1 INTEGRATION BATCH
Date: 2026-03-09
Role: Fill the remaining live-family admissibility and hint gaps without changing runtime or ontology

## 1) Purpose
This batch normalizes the remaining live A1 family surfaces into the doctrine that is already explicit in:
- default admissibility output
- family-aware admissibility hints
- anchor / regeneration-witness-aware family judgment

This batch:
- works only on already-active families
- does not add runtime work
- does not create a new ontology
- keeps stronger family-local judgment available for selector-side emission

## 2) Scope
Covered here:
- `A1_INTEGRATION_BATCH__ITEM__SUBSTRATE_ENRICHMENT_T2_OPERATOR__v1`
- `A1_INTEGRATION_BATCH__ITEM__ENTROPY_CORRELATION_EXECUTABLE__v1`
- `A1_INTEGRATION_BATCH__ITEM__ENTROPY_DIVERSITY_PASSENGER__v1`
- `A1_INTEGRATION_BATCH__ITEM__ENTROPY_RATE_PASSENGER__v1`

Explicitly not repeated here:
- `probe_operator` first substrate-family hints already exist in
  `system_v3/a1_state/A1_FIRST_SUBSTRATE_FAMILY_CAMPAIGN__v1.md`

## 3) A1_INTEGRATION_BATCH__ITEM__SUBSTRATE_ENRICHMENT_T2_OPERATOR__v1
Source-bound read:
- `system_v3/a1_state/A1_SECOND_SUBSTRATE_ENRICHMENT_FAMILY__v1.md`
- `system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`

Live role read:
- executable heads:
  - `hamiltonian_operator`
  - `lindblad_generator`
- witness-only enrichment companions:
  - `unitary_operator`
  - `commutator_operator`
- active caution:
  - do not reopen the compound capstone or superoperator family from this lane

Default admissibility block:
- `executable_head`
  - `hamiltonian_operator`
  - `lindblad_generator`
- `active_companion_floor`
  - none beyond the two active heads on the current `T2_OPERATOR` lane
- `late_passengers`
  - none
- `witness_only_terms`
  - `unitary_operator`
  - `commutator_operator`
- `residue_terms`
  - none
- `landing_blockers`
  - do not treat broader bridge-style widening as the next move for this family
  - do not reopen compound-capstone or superoperator inflation from a locally saturated dynamics lane
- `witness_floor`
  - `unitary_operator`
  - `commutator_operator`
- `current_readiness_status`
  - `hamiltonian_operator = HEAD_READY`
  - `lindblad_generator = HEAD_READY`
  - `unitary_operator = WITNESS_ONLY`
  - `commutator_operator = WITNESS_ONLY`

Family-aware admissibility hints:
```json
{
  "schema": "A1_ADMISSIBILITY_HINTS_v1",
  "family": "substrate_enrichment_t2_operator",
  "activation_terms": [
    "unitary_operator",
    "commutator_operator",
    "hamiltonian_operator",
    "lindblad_generator"
  ],
  "strategy_head_terms": [
    "hamiltonian_operator",
    "lindblad_generator"
  ],
  "forbid_strategy_head_terms": [
    "unitary_operator",
    "commutator_operator"
  ],
  "late_passenger_terms": [],
  "witness_only_terms": [
    "unitary_operator",
    "commutator_operator"
  ],
  "residue_only_terms": [],
  "landing_blocker_overrides": {
    "unitary_operator": "Earlier rung survivor; retain as a witness-only enrichment companion inside the active T2_OPERATOR lane.",
    "commutator_operator": "Earlier rung survivor; retain as a witness-only enrichment companion inside the active T2_OPERATOR lane."
  }
}
```

## 4) A1_INTEGRATION_BATCH__ITEM__ENTROPY_CORRELATION_EXECUTABLE__v1
Source-bound read:
- `system_v3/a1_state/A1_ENTROPY_CORRELATION_EXECUTABLE_PACK__v1.md`
- `system_v3/a1_state/A1_ENTROPY_EXECUTABLE_ENTRYPOINT__v1.md`
- `system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_BRIDGE_EXECUTABLE_CLUSTER__v1.md`
- `system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_BRIDGE_EXECUTABLE_CLUSTER__v1.md`

Live role read:
- active strategy head:
  - `correlation_polarity`
- active companion executable floor:
  - `correlation`
- accepted bridge witnesses:
  - `polarity`
  - `density_entropy`
- this family supports executable bridge entry, not richer-term landing closure

Default admissibility block:
- `executable_head`
  - `correlation_polarity`
- `active_companion_floor`
  - `correlation`
- `late_passengers`
  - `correlation_diversity_functional`
  - `entropy_production_rate`
- `witness_only_terms`
  - `polarity`
  - `density_entropy`
- `residue_terms`
  - `information`
  - `bound`
  - `work`
  - `entropy`
- `landing_blockers`
  - `correlation_diversity_functional` still lacks a clean alias / decomposition / witness floor strong enough for head landing
  - `entropy_production_rate` survives in broad executable mode but still fails clean standalone head landing
  - `information_work_extraction_bound` remains proposal/control witness material until lower helper decomposition is solved
  - `probe_induced_partition_boundary` remains deferred / witness-side rather than a landed executable term
- `witness_floor`
  - `correlation`
  - `polarity`
- `current_readiness_status`
  - `correlation_polarity = HEAD_READY`
  - `correlation_diversity_functional = PASSENGER_ONLY`
  - `entropy_production_rate = PASSENGER_ONLY`
  - `polarity = WITNESS_ONLY`
  - `density_entropy = WITNESS_ONLY`
  - `information = RESIDUE_ONLY`
  - `bound = RESIDUE_ONLY`
  - `work = RESIDUE_ONLY`
  - `entropy = RESIDUE_ONLY`

Family-aware admissibility hints:
```json
{
  "schema": "A1_ADMISSIBILITY_HINTS_v1",
  "family": "entropy_correlation_executable",
  "activation_terms": [
    "correlation_polarity",
    "correlation",
    "correlation_diversity_functional",
    "entropy_production_rate",
    "polarity",
    "density_entropy"
  ],
  "strategy_head_terms": [
    "correlation_polarity"
  ],
  "forbid_strategy_head_terms": [
    "correlation_diversity_functional",
    "entropy_production_rate",
    "pairwise_correlation_spread_functional",
    "probe_induced_partition_boundary",
    "information_work_extraction_bound"
  ],
  "late_passenger_terms": [
    "correlation_diversity_functional",
    "entropy_production_rate"
  ],
  "witness_only_terms": [
    "polarity",
    "density_entropy"
  ],
  "residue_only_terms": [
    "information",
    "bound",
    "work",
    "entropy"
  ],
  "landing_blocker_overrides": {
    "correlation_diversity_functional": "Keep as a late passenger / witness-seeking target while correlation_polarity carries executable pressure.",
    "entropy_production_rate": "Broad executable survival does not support promotion to standalone head status.",
    "pairwise_correlation_spread_functional": "Colder alias candidate only; do not let selector output upgrade it into an active head.",
    "probe_induced_partition_boundary": "Deferred witness-side target; do not count it as current executable landing."
  }
}
```

## 5) A1_INTEGRATION_BATCH__ITEM__ENTROPY_DIVERSITY_PASSENGER__v1
Source-bound read:
- `system_v3/a1_state/A1_CARTRIDGE_REVIEW__ACTIVE_FAMILY_CROSS_JUDGMENT__v1.md`
- `system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_DIVERSITY_FAMILY__v1.md`
- `system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_DIVERSITY_FAMILY__v1.md`

Live role read:
- sponsoring executable head:
  - `correlation_polarity`
- active late passenger / structure target:
  - `correlation_diversity_functional`
- colder alias candidate:
  - `pairwise_correlation_spread_functional`
- deferred witness-side target:
  - `probe_induced_partition_boundary`

Preserved tension:
- some older surfaces describe `pairwise_correlation_spread_functional` as a late passenger / alias candidate
- the stricter live anchor and witness read keeps it below active head status
- this batch preserves that stricter read for selector anchoring without deleting the alias-candidate history

Default admissibility block:
- `executable_head`
  - `correlation_polarity`
- `active_companion_floor`
  - `correlation`
- `late_passengers`
  - `correlation_diversity_functional`
- `witness_only_terms`
  - `pairwise_correlation_spread_functional`
  - `probe_induced_partition_boundary`
  - `functional`
- `residue_terms`
  - none beyond family-local decomposition residue already tracked elsewhere
- `landing_blockers`
  - `correlation_diversity_functional` remains landing-thin on alias, decomposition, and witness floors
  - `pairwise_correlation_spread_functional` improves cold-core shape but still does not justify head promotion
  - `probe_induced_partition_boundary` remains deferred / witness-side rather than a landed executable term
- `witness_floor`
  - `correlation`
  - `polarity`
- `current_readiness_status`
  - `correlation_diversity_functional = PASSENGER_ONLY`
  - `pairwise_correlation_spread_functional = WITNESS_ONLY`
  - `probe_induced_partition_boundary = WITNESS_ONLY`
  - `functional = WITNESS_ONLY`

Family-aware admissibility hints:
```json
{
  "schema": "A1_ADMISSIBILITY_HINTS_v1",
  "family": "entropy_diversity_passenger",
  "activation_terms": [
    "correlation_polarity",
    "correlation_diversity_functional",
    "pairwise_correlation_spread_functional",
    "probe_induced_partition_boundary",
    "functional"
  ],
  "strategy_head_terms": [
    "correlation_polarity"
  ],
  "forbid_strategy_head_terms": [
    "correlation_diversity_functional",
    "pairwise_correlation_spread_functional",
    "probe_induced_partition_boundary"
  ],
  "late_passenger_terms": [
    "correlation_diversity_functional"
  ],
  "witness_only_terms": [
    "pairwise_correlation_spread_functional",
    "probe_induced_partition_boundary",
    "functional"
  ],
  "residue_only_terms": [],
  "landing_blocker_overrides": {
    "correlation_diversity_functional": "Real structure target, but keep it passenger-side until alias, decomposition, and witness floors become explicit enough for landing.",
    "pairwise_correlation_spread_functional": "Colder alias candidate only; alias help is real but still not strong enough for clean head promotion.",
    "probe_induced_partition_boundary": "Deferred witness-side target; do not promote it ahead of the current executable bridge head."
  }
}
```

## 6) A1_INTEGRATION_BATCH__ITEM__ENTROPY_RATE_PASSENGER__v1
Source-bound read:
- `system_v3/a1_state/A1_CARTRIDGE_REVIEW__ACTIVE_FAMILY_CROSS_JUDGMENT__v1.md`
- `system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_RATE_FAMILY__v1.md`
- `system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_RATE_FAMILY__v1.md`

Live role read:
- active strategy head:
  - `correlation_polarity`
- late bookkeeping passenger:
  - `entropy_production_rate`
- witness floor:
  - `density_entropy`
  - or `correlation`
  - plus one bound-side witness:
    - `information_work_extraction_bound`
    - or `erasure_channel_entropy_cost_lower_bound`

Default admissibility block:
- `executable_head`
  - `correlation_polarity`
- `active_companion_floor`
  - `correlation`
- `late_passengers`
  - `entropy_production_rate`
- `witness_only_terms`
  - `density_entropy`
  - `information_work_extraction_bound`
  - `erasure_channel_entropy_cost_lower_bound`
- `residue_terms`
  - `information`
  - `bound`
  - `entropy`
  - `production`
- `landing_blockers`
  - `entropy_production_rate` still fails narrow standalone landing even though broad executable survival exists
  - bookkeeping witnesses must stay subordinate to the correlation-side executable head
  - do not treat rate-lift survival as a license to reopen a standalone bookkeeping-head lane
- `witness_floor`
  - `density_entropy` or `correlation`
  - one of:
    - `information_work_extraction_bound`
    - `erasure_channel_entropy_cost_lower_bound`
- `current_readiness_status`
  - `entropy_production_rate = PASSENGER_ONLY`
  - `density_entropy = WITNESS_ONLY`
  - `information_work_extraction_bound = WITNESS_ONLY`
  - `erasure_channel_entropy_cost_lower_bound = WITNESS_ONLY`
  - `information = RESIDUE_ONLY`
  - `bound = RESIDUE_ONLY`
  - `entropy = RESIDUE_ONLY`
  - `production = RESIDUE_ONLY`

Family-aware admissibility hints:
```json
{
  "schema": "A1_ADMISSIBILITY_HINTS_v1",
  "family": "entropy_rate_passenger",
  "activation_terms": [
    "correlation_polarity",
    "correlation",
    "entropy_production_rate",
    "density_entropy",
    "information_work_extraction_bound",
    "erasure_channel_entropy_cost_lower_bound"
  ],
  "strategy_head_terms": [
    "correlation_polarity"
  ],
  "forbid_strategy_head_terms": [
    "entropy_production_rate",
    "density_entropy"
  ],
  "late_passenger_terms": [
    "entropy_production_rate"
  ],
  "witness_only_terms": [
    "density_entropy",
    "information_work_extraction_bound",
    "erasure_channel_entropy_cost_lower_bound"
  ],
  "residue_only_terms": [
    "information",
    "bound",
    "entropy",
    "production"
  ],
  "landing_blocker_overrides": {
    "entropy_production_rate": "Keep passenger-only until narrow landing is explicit; broad executable survival does not justify standalone head promotion.",
    "density_entropy": "Useful bookkeeping witness, but it must not become the whole lane.",
    "information_work_extraction_bound": "Bound-side witness only under the current rate-family floor.",
    "erasure_channel_entropy_cost_lower_bound": "Bound-side witness only under the current rate-family floor."
  }
}
```

## 7) Batch-Level Use Rule
Use these blocks only as:
- proposal-side selector anchors
- family-local admissibility compression
- a bridge from richer family judgment into deterministic `A1_STRATEGY_v1` emission

Do not use them to:
- bypass lower-loop evidence
- promote passengers into heads by wording cleanup
- erase contradictions already preserved in the source families
- treat anchor survival as closure

## 8) Source Anchors
- `system_v3/a1_state/A1_EXECUTABLE_DISTILLATION_UPDATE__SOURCE_BOUND_v2.md`
- `system_v3/a1_state/A1_TARGET_FAMILY_MODEL__v1.md`
- `system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`
- `system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
- `system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
- `system_v3/a1_state/A1_CARTRIDGE_REVIEW__ACTIVE_FAMILY_CROSS_JUDGMENT__v1.md`
- `system_v3/a1_state/A1_SECOND_SUBSTRATE_ENRICHMENT_FAMILY__v1.md`
- `system_v3/a1_state/A1_ENTROPY_CORRELATION_EXECUTABLE_PACK__v1.md`
- `system_v3/a1_state/A1_ENTROPY_EXECUTABLE_ENTRYPOINT__v1.md`
- `system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_BRIDGE_EXECUTABLE_CLUSTER__v1.md`
- `system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_BRIDGE_EXECUTABLE_CLUSTER__v1.md`
- `system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_DIVERSITY_FAMILY__v1.md`
- `system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_DIVERSITY_FAMILY__v1.md`
- `system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_RATE_FAMILY__v1.md`
- `system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_RATE_FAMILY__v1.md`
