# RUN_ANCHOR__ENTROPY_RATE_FAMILY__v1

## Status

- Surface class: noncanonical anchor surface
- Purpose: replace repeated direct local entropy-rate / bookkeeping / thin correlation-head run citations with one compact family anchor
- Scope: entropy-rate lift, bookkeeping-passenger controls, and thin local correlation-head controls

## Anchor Runs

- `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_09__20260309T070408Z/RUN_GRAVEYARD_VALIDITY_ENTROPY_RATE_LOCAL_0001`
- `/home/ratchet/Desktop/Codex_Ratchet__archive/HEAT_DUMPS/SYSTEM_V3__RUN_DEMOTION_BATCH_09__20260309T070408Z/RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_RATE_LIFT_BROAD_0001`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_BOOKKEEPING_PAIR_LOCAL_0001`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_CORRELATION_POLARITY_LOCAL_0003`

## What This Family Carries

- narrow and broad executable entropy-rate lift evidence
- thin bookkeeping-pair local control evidence
- thin single-term `correlation_polarity` local control evidence
- the stable head/passenger split:
  - `correlation_polarity` as head
  - `entropy_production_rate` as late bookkeeping passenger
- the current witness-floor requirement for rate-family lifting

## Family Contributions

### RUN_GRAVEYARD_VALIDITY_ENTROPY_RATE_LOCAL_0001

- compact local regeneration witness for the entropy-rate family
- carries the memo report, cold-core proposals, and emitted strategy chain
- supports the live selector audit that keeps `entropy_production_rate` out of head position

Key cited surfaces:
- `reports/a1_external_memo_batch_driver_report.json`
- `a1_sandbox/cold_core/000002_A1_COLD_CORE_PROPOSALS_v1.json`
- `a1_sandbox/outgoing/000001_A1_STRATEGY_v1__PACK_SELECTOR.json`
- `reports/graveyard_first_validity_wrapper_report.json`

### RUN_GRAVEYARD_VALIDITY_ENTROPY_BOOKKEEPING_PAIR_LOCAL_0001

- focused bookkeeping-pair local control for:
  - `entropy_production_rate`
  - `erasure_channel_entropy_cost_lower_bound`
- cold-core and selector both form the narrow bookkeeping pair
- retained memo-side state stays extremely thin at:
  - `canonical_term_count = 3`
  - `graveyard_count = 0`
  - `kill_log_count = 0`
  - `sim_registry_count = 3`
- wrapper reports:
  - `PASS__EXECUTED_CYCLE`
  - `executed_cycles = 1`
  - `all_target_terms_allowed = false`
- preserved doctrine mismatch:
  - downstream A1/A2 docs often paraphrase this run as effectively “no executed cycle”
  - the retained run surfaces show one cycle did execute, but it produced no real graveyard pressure and no useful negative frontier

Key cited surfaces:
- `reports/graveyard_first_validity_wrapper_report.json`
- `reports/a1_external_memo_batch_driver_report.json`
- `a1_sandbox/cold_core/000024_A1_COLD_CORE_PROPOSALS_v1.json`
- `a1_sandbox/outgoing/000024_A1_STRATEGY_v1__PACK_SELECTOR.json`

### RUN_GRAVEYARD_VALIDITY_CORRELATION_POLARITY_LOCAL_0003

- thin single-term local control for the intended head:
  - `correlation_polarity`
- cold-core and selector still shape the atomic ladder:
  - `correlation`
  - `polarity`
  - `correlation_polarity`
- retained run result is:
  - `FAIL__SUBPROCESS`
  - `executed_cycles = 0`
  - `stop_reason = WAITING_FOR_MEMOS`
  - state remains `0 / 0 / 0 / 0`
- this run is family-level negative evidence that isolated local head pressure is still thinner than the broad executable bridge lane

Key cited surfaces:
- `reports/graveyard_first_validity_wrapper_report.json`
- `reports/a1_external_memo_batch_driver_report.json`
- `a1_sandbox/cold_core/000002_A1_COLD_CORE_PROPOSALS_v1.json`
- `a1_sandbox/outgoing/000002_A1_STRATEGY_v1__PACK_SELECTOR.json`

### RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_RATE_LIFT_BROAD_0001

- broad executable lift proof anchor
- supports the claim that `entropy_production_rate` can survive in broad executable mode
- does not support promoting it to standalone head status

## Current Family Read

- active strategy head:
  - `correlation_polarity`
- late bookkeeping passenger:
  - `entropy_production_rate`
- isolated bookkeeping-pair local pressure is still too thin to count as a standalone local-validity win
- isolated local `correlation_polarity` pressure is still memo-path thin and should not outrank the broader executable bridge evidence
- witness floor:
  - `density_entropy`
  - or `correlation`
  - plus one bound-side witness:
    - `information_work_extraction_bound`
    - or `erasure_channel_entropy_cost_lower_bound`

## Citation Rule

- Prefer citing this anchor doc when the active doc is making a family-level point about:
  - entropy-rate lift status
  - passenger-only placement of `entropy_production_rate`
  - bookkeeping-pair local thinness
  - thin local `correlation_polarity` failure
  - broad executable survival versus narrow landing failure
  - required witness floor for rate-family lifting
- Only cite raw run paths directly when the exact file artifact matters more than the family-level result

## Regeneration Witness Companion

- `/home/ratchet/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_RATE_FAMILY__v1.md`
