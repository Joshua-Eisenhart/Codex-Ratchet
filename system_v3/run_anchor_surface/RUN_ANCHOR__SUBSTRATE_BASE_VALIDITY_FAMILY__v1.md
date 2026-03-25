# RUN_ANCHOR__SUBSTRATE_BASE_VALIDITY_FAMILY__v1

## Status

- surface class: noncanonical anchor surface
- purpose: replace repeated direct local substrate-base graveyard-validity run citations with one compact family anchor
- scope: broad-fuel substrate-base graveyard saturation plus tighter concept-local same-family validity

## Anchor runs

- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_SUBSTRATE_BASE_0003`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_SUBSTRATE_BASE_LOCAL_0002`

## What this family carries

- first fresh local-stub proof that graveyard-first validity really executes on the substrate-base lane
- broad-fuel graveyard saturation proof at the large exploratory frontier
- tighter concept-local same-family validity proof at a materially narrower frontier
- semantic/math gate pass in graveyard-fill mode for both broad and concept-local base pressure
- the current base-family selector collapse onto:
  - `one`
  - `trace_one`

## Run contributions

### RUN_GRAVEYARD_VALIDITY_SUBSTRATE_BASE_0003

- broad-fuel graveyard saturation proof for the substrate-base family
- retains one executed graveyard-first cycle under:
  - `focus_term_mode = concept_plus_rescue`
- leaves the exploratory broad state:
  - `canonical_term_count = 39`
  - `graveyard_count = 153`
  - `kill_log_count = 153`
  - `sim_registry_count = 247`
- semantic/math substance gate passes in graveyard-fill phase
- operational-integrity audit still fails final closure only on missing `T6_WHOLE_SYSTEM`

Key cited surfaces:
- `reports/a1_external_memo_batch_driver_report.json`
- `reports/a1_semantic_and_math_substance_gate_report.json`
- `a1_sandbox/cold_core/000024_A1_COLD_CORE_PROPOSALS_v1.json`
- `a1_sandbox/outgoing/000024_A1_STRATEGY_v1__PACK_SELECTOR.json`

### RUN_GRAVEYARD_VALIDITY_SUBSTRATE_BASE_LOCAL_0002

- tighter concept-local same-family validity proof for the substrate-base lane
- retains one executed graveyard-first cycle under:
  - `focus_term_mode = concept_local_rescue`
- leaves the narrower validity state:
  - `canonical_term_count = 9`
  - `graveyard_count = 53`
  - `kill_log_count = 53`
  - `sim_registry_count = 80`
- semantic/math substance gate also passes in graveyard-fill phase
- operational-integrity audit again fails only on missing `T6_WHOLE_SYSTEM`

Key cited surfaces:
- `reports/a1_external_memo_batch_driver_report.json`
- `a1_sandbox/cold_core/000024_A1_COLD_CORE_PROPOSALS_v1.json`
- `a1_sandbox/outgoing/000024_A1_STRATEGY_v1__PACK_SELECTOR.json`

## Current family read

- the broad-fuel profile is best read as exploratory graveyard saturation mode for the substrate-base family
- the concept-local profile is best read as same-family validity mode
- both runs prove graveyard-first execution is real on this lane, not just configured
- both runs still collapse the retained selector surface to:
  - `one`
  - `trace_one`
- the family therefore proves execution reality and pressure shape, not final higher-tier closure

## Citation rule

- cite this anchor surface for family-level claims about:
  - substrate-base graveyard-first execution reality
  - broad-fuel saturation mode
  - concept-local same-family validity mode
  - the shared `one` / `trace_one` selector collapse
  - the remaining `T6_WHOLE_SYSTEM` closure gap
- cite raw run paths directly only when the exact report, cold-core file, or selector file is itself the point

## Regeneration witness

See:

- `/home/ratchet/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__SUBSTRATE_BASE_VALIDITY_FAMILY__v1.md`
