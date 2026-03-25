# A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK__v1

STATUS: NONCANONICAL
ROLE: A1_CONTROL_PACK
DOMAIN: ENTROPY_LANE

## 1) Purpose
Prepare a colder executable alias for the diversity side of the entropy structure lane.

Current blocker:
- `correlation_diversity_functional` has real runtime probe machinery behind it
- but it still fails to land as a direct term under current term-surface pressure

## 2) Source Runtime Anchor
Runtime comment and probe surface:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/sim_engine.py`

Key wording already present there:
- `pairwise correlation-spread functional`
- `pairwise_mutual_information_diversity_delta_under_perturbation`

## 3) Alias Rule
Do not mutate the ontology yet.
Treat this as a colder executable alias exploration pack only.

Working colder alias candidate:
- `pairwise_correlation_spread_functional`

Reason:
- closer to the actual runtime probe
- less overloaded than `correlation_diversity_functional`
- still avoids primitive time language

## 4) Required Witness Floor
Every alias-lift branch should include:
- `correlation_polarity`
- `correlation`
- optional:
  - `density_entropy`

Do not include:
- `probe_induced_partition_boundary`
as a required co-target yet

## 5) Negative Rule
Keep active:
- `CLASSICAL_TEMPERATURE`
- `CLASSICAL_TIME`
- `CONTINUOUS_BATH`
- `COMMUTATIVE_ASSUMPTION`
- `EUCLIDEAN_METRIC`
- `INFINITE_SET`
- `INFINITE_RESOLUTION`
- `PRIMITIVE_EQUALS`

## 6) Bottom Line
The next entropy structure move should not keep forcing the warmer term:
- `correlation_diversity_functional`

It should first test whether a colder executable alias like:
- `pairwise_correlation_spread_functional`

can land cleanly from the already-earned correlation-side bridge floor.

## 7) Alias Audit
Runs:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_DIVERSITY_FAMILY__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_DIVERSITY_FAMILY__v1.md`

Observed:
- `pairwise_correlation_spread_functional` enters cold-core admissible candidates
- but it still carries enough atomic bootstrap debt that it does not become a productive strategy head
- standalone alias broad executes only on the existing broad helper frontier
- bridge-plus-alias broad stalls at memo/prepack handoff before a lower-loop executed cycle

Current read:
- the alias is real and worth keeping
- the alias is not yet a justified executable lead term

Decision:
- keep `pairwise_correlation_spread_functional` as:
  - colder candidate
  - witness-side alias candidate
  - future structure witness
- do not keep spending budget on alias-first executable profiles right now

## 8) Default Admissibility Block
- `executable_head`
  - `correlation_polarity`

- `active_companion_floor`
  - `correlation`

- `late_passengers`
  - `correlation_diversity_functional`

- `witness_only_terms`
  - `pairwise_correlation_spread_functional`
  - `density_entropy`
  - `polarity`

- `residue_terms`
  - none

- `landing_blockers`
  - `correlation_diversity_functional` still fails executable landing and remains passenger-side until alias, decomposition, and witness floors improve
  - `pairwise_correlation_spread_functional` is a real colder alias candidate but still too bootstrap-heavy for clean head promotion

- `witness_floor`
  - `correlation_polarity`
  - `correlation`
  - optional:
    - `density_entropy`

- `current_readiness_status`
  - `correlation_polarity = HEAD_READY`
  - `correlation_diversity_functional = PASSENGER_ONLY`
  - `pairwise_correlation_spread_functional = WITNESS_ONLY`
  - `correlation = WITNESS_ONLY`
  - `density_entropy = WITNESS_ONLY`
  - `polarity = WITNESS_ONLY`

```json
{
  "schema": "A1_ADMISSIBILITY_HINTS_v1",
  "family_label": "entropy_diversity_alias_lift",
  "activation_terms": [
    "correlation_polarity",
    "correlation_diversity_functional",
    "pairwise_correlation_spread_functional",
    "correlation",
    "density_entropy",
    "polarity"
  ],
  "strategy_head_terms": [
    "correlation_polarity"
  ],
  "forbid_strategy_head_terms": [
    "correlation_diversity_functional",
    "pairwise_correlation_spread_functional"
  ],
  "late_passenger_terms": [
    "correlation_diversity_functional"
  ],
  "witness_only_terms": [
    "pairwise_correlation_spread_functional",
    "correlation",
    "density_entropy",
    "polarity"
  ],
  "landing_blocker_overrides": {
    "correlation_diversity_functional": "real structure target but still fails executable landing; keep as late passenger until alias/decomposition/witness floors are stronger",
    "pairwise_correlation_spread_functional": "colder alias candidate but still too bootstrap-heavy to act as strategy head; keep witness-side until a cleaner landing path exists"
  }
}
```

## 9) Integration Companions
Use these with this pack when emitting family-level judgment:
- `system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_DIVERSITY_FAMILY__v1.md`
- `system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_DIVERSITY_FAMILY__v1.md`
- `system_v3/a1_state/A1_INTEGRATION_BATCH__LIVE_FAMILY_HINT_COVERAGE__v1.md`
- `system_v3/a1_state/A1_INTEGRATION_BATCH__ANCHOR_WITNESS_WORKFLOW__v1.md`
