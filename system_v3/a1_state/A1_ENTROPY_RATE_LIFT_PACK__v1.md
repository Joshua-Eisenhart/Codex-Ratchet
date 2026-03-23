# A1_ENTROPY_RATE_LIFT_PACK__v1

STATUS: NONCANONICAL
ROLE: A1_CONTROL_PACK
DOMAIN: ENTROPY_LANE

## 1) Purpose
Lift `entropy_production_rate` from the tighter cluster-rescue frontier that now admits `correlation_polarity`.

Do not reopen the old broad plateau.
Start from the already-tightened cluster-aware frontier.

## 2) Source Frontier
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_BRIDGE_RESCUE_CONTINUATION_CLUSTER__v1.md`

Observed surviving bridge-side terms:
- `correlation_polarity`
- `information`
- `bound`

Observed missing target:
- `entropy_production_rate`

## 3) Lift Rule
Do not let `entropy_production_rate` appear as a lone head.

Every primary branch that tries to lift it must include:
- one already-surviving polarity witness:
  - `correlation_polarity`
- one colder/helper witness:
  - `density_entropy`
  - or `correlation`
- one bound-side witness:
  - `information_work_extraction_bound`
  - or `erasure_channel_entropy_cost_lower_bound`

## 4) Negatives To Keep Active
- `CLASSICAL_TEMPERATURE`
- `CLASSICAL_TIME`
- `CONTINUOUS_BATH`
- `COMMUTATIVE_ASSUMPTION`
- `EUCLIDEAN_METRIC`
- `INFINITE_SET`
- `INFINITE_RESOLUTION`
- `PRIMITIVE_EQUALS`

## 5) Required Branch Families

### A) rate_from_polarity_bound
- `correlation_polarity`
- one bound witness
- late `entropy_production_rate`

### B) rate_from_density_bound
- `density_entropy`
- one bound witness
- late `entropy_production_rate`

### C) rate_cluster_negative
- explicit branch expected to fail by time/bath leakage

## 6) Operational Rule
Do not spend budget on lone `rate`, `production`, or `entropy_production_rate` branches.

If this pack fails:
- treat `entropy_production_rate` as still too alias-heavy for direct execution
- keep it proposal-side until a colder executable decomposition exists

## 7) Bottom Line
This pack tries to lift `entropy_production_rate` from the first tight broad frontier that already admits `correlation_polarity`.

## 8) Rate-Lift Broad Result
Anchor:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_RATE_FAMILY__v1.md`

Normalized regeneration witness:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_RATE_FAMILY__v1.md`

Observed:
- wrapper status:
  - `PASS__EXECUTED_CYCLE`
- the direct target pair is now admitted under broad rate-lift pressure:
  - `correlation_polarity`
  - `entropy_production_rate`
- colder/bound witnesses also survive in the same state:
  - `density_entropy`
  - `information_work_extraction_bound`
  - `erasure_channel_entropy_cost_lower_bound`
- broad counts move back to the large saturation surface:
  - `canonical_term_count = 40`
  - `graveyard_count = 153`
  - `kill_log_count = 153`
  - `sim_registry_count = 245`
- dominant kill basin remains the same family:
  - `CLASSICAL_TEMPERATURE`
  - `CLASSICAL_TIME`
  - `COMMUTATIVE_ASSUMPTION`
  - `CONTINUOUS_BATH`
  - `EUCLIDEAN_METRIC`
  - `INFINITE_SET`
  - `INFINITE_RESOLUTION`
  - `PRIMITIVE_EQUALS`

Operational read:
- this pack succeeds in lifting `entropy_production_rate`
- it does not produce a tighter frontier than the cluster-rescue route
- it is therefore a successful broad executable entropy bridge, not a strict local-validity bridge

## 9) Role Classification
Apply the landing/admissibility rule explicitly:

- active strategy head on the current entropy lane:
  - `correlation_polarity`

- late bookkeeping passenger on this lift:
  - `entropy_production_rate`

- required support / witness floor:
  - one already-surviving polarity witness:
    - `correlation_polarity`
  - one colder/helper witness:
    - `density_entropy`
    - or `correlation`
  - one bound-side witness:
    - `information_work_extraction_bound`
    - or `erasure_channel_entropy_cost_lower_bound`

Current read:
- `entropy_production_rate` is not yet a clean standalone executable head
- it can survive as a late bookkeeping passenger inside the broader executable bridge
- it should not be promoted as the leading head until local lexeme/landing pressure is materially cleaner

## 9b) Default Admissibility Block
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
  - `rate`
  - `production`

- `landing_blockers`
  - `entropy_production_rate` survives in broad executable mode but still fails narrow standalone landing
  - bookkeeping witnesses must stay subordinate to the correlation-side executable head
  - do not treat rate-lift survival as a license to reopen a standalone bookkeeping-head lane

- `witness_floor`
  - `correlation_polarity`
  - one of:
    - `density_entropy`
    - `correlation`
  - one of:
    - `information_work_extraction_bound`
    - `erasure_channel_entropy_cost_lower_bound`

- `current_readiness_status`
  - `correlation_polarity = HEAD_READY`
  - `entropy_production_rate = PASSENGER_ONLY`
  - `density_entropy = WITNESS_ONLY`
  - `correlation = WITNESS_ONLY`
  - `information_work_extraction_bound = WITNESS_ONLY`
  - `erasure_channel_entropy_cost_lower_bound = WITNESS_ONLY`
  - `rate = RESIDUE_ONLY`
  - `production = RESIDUE_ONLY`

## 10) Machine-Readable Admissibility Hints
```json
{
  "schema": "A1_ADMISSIBILITY_HINTS_v1",
  "family": "entropy_rate_lift",
  "activation_terms": [
    "correlation_polarity",
    "entropy_production_rate",
    "density_entropy",
    "correlation",
    "information_work_extraction_bound",
    "erasure_channel_entropy_cost_lower_bound"
  ],
  "strategy_head_terms": ["correlation_polarity"],
  "forbid_strategy_head_terms": ["entropy_production_rate"],
  "late_passenger_terms": ["entropy_production_rate"],
  "witness_only_terms": [
    "density_entropy",
    "correlation",
    "information_work_extraction_bound",
    "erasure_channel_entropy_cost_lower_bound"
  ],
  "residue_only_terms": ["rate", "production"],
  "landing_blocker_overrides": {
    "entropy_production_rate": "broad executable survivor but still alias-heavy and not a clean standalone bookkeeping head"
  }
}
```

## 11) Integration Companions
Use these with this pack when emitting family-level judgment:
- `system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_RATE_FAMILY__v1.md`
- `system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_RATE_FAMILY__v1.md`
- `system_v3/a1_state/A1_INTEGRATION_BATCH__LIVE_FAMILY_HINT_COVERAGE__v1.md`
- `system_v3/a1_state/A1_INTEGRATION_BATCH__ANCHOR_WITNESS_WORKFLOW__v1.md`
