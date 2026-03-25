# A1_ENTROPY_DIVERSITY_STRUCTURE_LIFT_PACK__v1

STATUS: NONCANONICAL
ROLE: A1_CONTROL_PACK
DOMAIN: ENTROPY_LANE

## 1) Purpose
Lift `correlation_diversity_functional` as the first direct entropy-structure target after the broad entropy bridge floor has already been earned.

This pack exists because:
- `correlation_diversity_functional` has real runtime probe evidence behind it
- `probe_induced_partition_boundary` does not yet have equally direct runtime support

## 2) Runtime Justification
Direct runtime evidence already exists for the diversity side:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/sim_engine.py`
  - `pairwise_mutual_information_diversity_delta_under_perturbation`
  - `mi2_pair_diversity_base`
  - `mi2_pair_diversity_delta`

So the first executable structure-side lift should favor:
- `correlation_diversity_functional`

before:
- `probe_induced_partition_boundary`

## 3) Main Rule
Do not require `probe_induced_partition_boundary` in the same primary branch.

Every primary branch that tries to lift `correlation_diversity_functional` must include:
- one bridge-side survivor:
  - `correlation_polarity`
- one colder/helper witness:
  - `density_entropy`
  - or `correlation`
- optional bound-side support:
  - `information_work_extraction_bound`
  - or `erasure_channel_entropy_cost_lower_bound`

## 4) Required Branch Families

### A) diversity_from_polarity
- `correlation_polarity`
- late `correlation_diversity_functional`

### B) diversity_from_density
- `density_entropy`
- `correlation`
- late `correlation_diversity_functional`

### C) diversity_bound_support
- one bridge-side survivor
- one bound-side witness
- late `correlation_diversity_functional`

### D) partition_only_negative
- `probe_induced_partition_boundary` without diversity support
- expected to fail as under-supported / too metaphorical

### E) helper_only_negative
- helper-led branch with no diversity target
- expected to fail as incomplete

## 5) Negative Pressure
Keep active:
- `CLASSICAL_TEMPERATURE`
- `CLASSICAL_TIME`
- `CONTINUOUS_BATH`
- `COMMUTATIVE_ASSUMPTION`
- `EUCLIDEAN_METRIC`
- `INFINITE_SET`
- `INFINITE_RESOLUTION`
- `PRIMITIVE_EQUALS`

## 6) Deferral Rule
Keep `probe_induced_partition_boundary` proposal-side until:
- `correlation_diversity_functional` lands under executable pressure
or
- a colder partition witness exists with direct runtime support

## 7) Bottom Line
This pack makes the structure-side entropy split explicit:
- executable-first target:
  - `correlation_diversity_functional`
- deferred second target:
  - `probe_induced_partition_boundary`

## 8) Diversity-Lift Broad Result
Run:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_DIVERSITY_FAMILY__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_DIVERSITY_FAMILY__v1.md`

Observed:
- wrapper status:
  - `PASS__EXECUTED_CYCLE`
- direct target still does not land:
  - `correlation_diversity_functional`
- the run collapses back onto the already-earned correlation-side helper floor:
  - `correlation_polarity`
  - `correlation`
- counts remain the tighter broad frontier:
  - `canonical_term_count = 9`
  - `graveyard_count = 45`
  - `kill_log_count = 45`
  - `sim_registry_count = 69`

Operational read:
- runtime diversity probes exist, but the direct structure term is still too alias-heavy to land under current term surfaces
- the next move should be a colder executable alias/decomposition for the diversity side
- do not treat this pack as the active executable entropy route

## 9) Default Admissibility Block
- `executable_head`
  - `correlation_polarity`

- `active_companion_floor`
  - `correlation`

- `late_passengers`
  - `correlation_diversity_functional`

- `witness_only_terms`
  - `probe_induced_partition_boundary`
  - `density_entropy`
  - `polarity`

- `residue_terms`
  - none

- `landing_blockers`
  - `correlation_diversity_functional` passes rosetta, cartridge, and diversity pressure but still fails executable landing
  - `probe_induced_partition_boundary` remains under-supported and witness-side under the current colder-structure read

- `witness_floor`
  - `correlation_polarity`
  - one of:
    - `density_entropy`
    - `correlation`

- `current_readiness_status`
  - `correlation_polarity = HEAD_READY`
  - `correlation_diversity_functional = PASSENGER_ONLY`
  - `probe_induced_partition_boundary = WITNESS_ONLY`
  - `correlation = WITNESS_ONLY`
  - `density_entropy = WITNESS_ONLY`
  - `polarity = WITNESS_ONLY`

```json
{
  "schema": "A1_ADMISSIBILITY_HINTS_v1",
  "family_label": "entropy_diversity_structure_lift",
  "activation_terms": [
    "correlation_polarity",
    "correlation_diversity_functional",
    "probe_induced_partition_boundary",
    "correlation",
    "density_entropy",
    "polarity"
  ],
  "strategy_head_terms": [
    "correlation_polarity"
  ],
  "forbid_strategy_head_terms": [
    "correlation_diversity_functional",
    "probe_induced_partition_boundary"
  ],
  "late_passenger_terms": [
    "correlation_diversity_functional"
  ],
  "witness_only_terms": [
    "probe_induced_partition_boundary",
    "correlation",
    "density_entropy",
    "polarity"
  ],
  "landing_blocker_overrides": {
    "correlation_diversity_functional": "passes rosetta/cartridge/diversity but still fails executable landing; keep correlation_polarity as head until colder alias/decomposition support is stronger",
    "probe_induced_partition_boundary": "deferred second target; keep proposal-side or witness-only until a colder partition witness with direct runtime support exists"
  }
}
```

## 10) Integration Companions
Use these with this pack when emitting family-level judgment:
- `system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_DIVERSITY_FAMILY__v1.md`
- `system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_DIVERSITY_FAMILY__v1.md`
- `system_v3/a1_state/A1_INTEGRATION_BATCH__LIVE_FAMILY_HINT_COVERAGE__v1.md`
- `system_v3/a1_state/A1_INTEGRATION_BATCH__ANCHOR_WITNESS_WORKFLOW__v1.md`
