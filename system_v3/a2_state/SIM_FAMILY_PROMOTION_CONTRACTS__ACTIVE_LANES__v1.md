# SIM_FAMILY_PROMOTION_CONTRACTS__ACTIVE_LANES__v1
Status: PROPOSED / NONCANONICAL / ACTIVE EXECUTION CONTROL
Date: 2026-03-06
Role: Family-specific SIM promotion contracts for the currently active substrate and entropy lanes

## 1) Purpose
This document makes the active SIM ladder more explicit for the lanes that are already being run.

It does not invent a new SIM system.
It tightens the family-specific promotion obligations that sit on top of:
- `system_v3/specs/06_SIM_EVIDENCE_AND_TIERS_SPEC.md`
- `system_v3/specs/01_REQUIREMENTS_LEDGER.md`
- `system_v3/specs/08_PIPELINE_AND_STATE_FLOW_SPEC.md`

The goal is to prevent:
- vague tier promotion
- family drift
- untraceable evidence
- helper residue being mistaken for family advancement

## 2) Global Rules Inherited By Every Family
- no tier-skip promotion
- meaningful survivors require:
  - positive evidence
  - negative evidence
  - graveyard-linked alternatives
- every tier report must remain replayable and hash-bound
- higher-tier evidence must reduce to lower-tier evidence surfaces

These rules come from:
- `system_v3/specs/06_SIM_EVIDENCE_AND_TIERS_SPEC.md`
- `system_v3/specs/01_REQUIREMENTS_LEDGER.md`

## 3) Active Family Classes
The active lanes are:

### A) Substrate Base Family
- `finite_dimensional_hilbert_space`
- `density_matrix`
- `probe_operator`
- `cptp_channel`
- `partial_trace`

### B) Substrate Enrichment Family
- `unitary_operator`
- `commutator_operator`
- `hamiltonian_operator`
- `lindblad_generator`

### C) Entropy Correlation Executable Branch
- `correlation`
- `correlation_polarity`

### D) Entropy Broad Rescue Route
- broad graveyard / rescue / negative-pressure surface for the entropy lane
- not a direct ontology-promotion lane by itself

## 4) Substrate Base Family Contract
### 4.1) T0_ATOM obligation
The base family may be treated as `T0_ATOM` closed only if the five target terms each have:
- direct local probe pass
- required adversarial negatives attached
- graveyard-linked alternatives attached
- no helper term counted as part of the primary family target

Current operational reading:
- the five-step ladder is execution-proven
- `probe` may appear as an auxiliary helper bootstrap term
- `probe` does not count as part of the primary five-term family target

### 4.2) T1_COMPOUND obligation
The base family may be treated as `T1_COMPOUND` only if:
- the family composes into a single compound witness
- lower subprobes remain passing
- helper bootstrap terms do not become silent ontology
- composition stress and adversarial negatives remain closed

Current compound witness candidate:
- `finite_dimensional_density_matrix_partial_trace_cptp_channel_unitary_operator`

Current status:
- `T0_ATOM` is active and proven
- `T1_COMPOUND` remains pending / proposal-controlled

## 5) Substrate Enrichment Family Contract
### 5.1) T0_ATOM obligation
Each enrichment term must pass its direct local/operator probe:
- `unitary_operator`
- `commutator_operator`
- `hamiltonian_operator`
- `lindblad_generator`

Additional pair-specific requirement:
- `hamiltonian_operator`
- `lindblad_generator`
must carry explicit negative pressure on:
- `CLASSICAL_TIME`
- `COMMUTATIVE_ASSUMPTION`
- `PRIMITIVE_EQUALS`

### 5.2) T1_COMPOUND obligation
The enrichment family may be treated as `T1_COMPOUND` only if:
- the exact four-term enrichment family saturates concept-local graveyard pressure
- no broad-fuel spillover terms are admitted as family terms
- the local selector saturates on the exact family

Current status:
- concept-local enrichment seed saturation is proven

### 5.3) T2_OPERATOR obligation
The enrichment family may be treated as `T2_OPERATOR` only if:
- it survives an executed-cycle dynamics-focused run
- target specificity for `hamiltonian_operator` and `lindblad_generator` is preserved
- bridge widening does not dissolve the family into generic operator residue

Current status:
- active / execution-proven under the seeded cluster-clamp route
- broad bridge dynamics route remains negative evidence because it loses target specificity
- current seeded cluster-clamp continuation is locally saturated under the same family fence

## 6) Entropy Correlation Executable Branch Contract
### 6.1) T0_ATOM obligation
The executable entropy-adjacent branch may be treated as `T0_ATOM` only if:
- `correlation` survives
- `correlation_polarity` survives
- `polarity` is classified as a bridge witness only
- `information`, `bound`, and `work` are classified as non-bridge residue
- `probe` is classified as substrate companion, not entropy success

Current status:
- `T0_ATOM` is active and execution-proven under broad pressure

### 6.2) T1_COMPOUND obligation
The entropy executable branch may be treated as `T1_COMPOUND` only if:
- helper residue remains subordinate across repeated runs
- branch budgeting and merge fences prevent non-family residue from retaking head status
- the branch remains executable without reopening six-term bridge churn

Current status:
- active / executed under the cluster-clamped broad continuation
- not formally closed because helper residue and path-build saturation still dominate inside the current family fence

### 6.3) T2_OPERATOR / STRUCTURE obligation
The entropy lane may be promoted beyond the executable correlation branch only if:
- `probe_induced_partition_boundary`
- `correlation_diversity_functional`
become executable without alias/higher-helper collapse
- the six-term entropy bridge floor stops decomposing into helper fragments

Current status:
- pending
- still proposal/control only

## 7) Entropy Broad Rescue Route Contract
The broad entropy route is an evidence-support lane, not a direct structure-promotion lane.

Its obligations are:
- generate rich graveyard pressure
- generate clustered failure topology
- preserve rescue ordering
- feed executable entropy branches with better negatives and rescue transforms

It may justify:
- rescue pack updates
- branch-budget updates
- failure-basin priority shifts

It does not by itself justify:
- direct promotion of six-term bridge structure
- direct promotion of classical engine names

Current status:
- active
- execution-proven
- main role is rescue / negative-pressure support
- later-phase rescue execution is proven
- current blocker is rescue efficacy / novelty generation under helper-decomposition pressure, not route existence

## 8) Promotion Decision Table
### Substrate Base
- `T0_ATOM`: active / proven
- `T1_COMPOUND`: pending

### Substrate Enrichment
- `T0_ATOM`: active / proven per term
- `T1_COMPOUND`: concept-local seed saturation proven
- `T2_OPERATOR`: active / execution-proven under the seeded cluster-clamp route; locally saturated under the same family fence

### Entropy Correlation Branch
- `T0_ATOM`: active / proven
- `T1_COMPOUND`: active / executed / not closed
- `T2_OPERATOR/STRUCTURE`: pending

### Entropy Broad Rescue Route
- support lane only
- not a direct ontology promotion lane

## 9) Operational Rule
For active runs, promotion should be read like this:

1. prove the local floor honestly
2. preserve family specificity under stronger pressure
3. only then allow compound/structure promotion

Do not use:
- helper residue
- broad exploratory spillover
- bridge witnesses alone

as if they were family advancement.

## 9.1) Current Engineering Pressure
The current machine-defining pressure points are:
- substrate base:
  - `T1_COMPOUND` closure
- substrate enrichment:
  - broader rescue closure is deferred because `T2_OPERATOR` is already execution-proven and locally saturated
- entropy correlation branch:
  - helper-residue control and post-seed path-build saturation
- entropy broad rescue route:
  - rescue efficacy / novelty generation under helper-decomposition pressure

This means current work should stay on:
- entropy helper-residue control
- entropy rescue novelty / rescue efficacy

and should not reopen:
- broad enrichment-family rescue churn
- speculative outer-ladder execution

## 10) Source Anchors
- `system_v3/specs/06_SIM_EVIDENCE_AND_TIERS_SPEC.md`
- `system_v3/specs/01_REQUIREMENTS_LEDGER.md`
- `system_v3/specs/08_PIPELINE_AND_STATE_FLOW_SPEC.md`
- `system_v3/a1_state/A1_FIRST_SUBSTRATE_FAMILY_CAMPAIGN__v1.md`
- `system_v3/a1_state/A1_SECOND_SUBSTRATE_ENRICHMENT_FAMILY__v1.md`
- `system_v3/a1_state/A1_FIRST_ENTROPY_BRIDGE_CAMPAIGN__v1.md`
- `system_v3/a1_state/A1_ENTROPY_CORRELATION_EXECUTABLE_PACK__v1.md`
