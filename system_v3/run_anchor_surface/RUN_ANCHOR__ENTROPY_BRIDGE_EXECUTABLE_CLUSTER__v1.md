# RUN_ANCHOR__ENTROPY_BRIDGE_EXECUTABLE_CLUSTER__v1

## Status

- surface class: noncanonical anchor surface
- purpose: replace repeated direct local run-path citations with one compact family anchor
- scope: entropy correlation executable family plus its cleaner cluster-clamped continuation and negative boundary probes

## Anchor runs

- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_CORRELATION_EXECUTABLE_BROAD_0002`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_CORRELATION_EXECUTABLE_WORK_STRIP_BROAD_0001`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_CORRELATION_EXECUTABLE_SEED_CLAMPED_BROAD_0001`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_CORRELATION_EXECUTABLE_CLUSTER_CLAMP_BROAD_0002`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_CORRELATION_EXECUTABLE_CLUSTER_CLAMP_BROAD_CONT_0006`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runs/RUN_GRAVEYARD_VALIDITY_ENTROPY_CORRELATION_EXECUTABLE_CLUSTER_CLAMP_BROAD_PROBE_COMPANION_0001`

## What this family carries

- the first real executable correlation-side floor on the entropy lane
- the negative boundary probes showing helper stripping currently costs the executed cycle
- the cleaner cluster-clamped continuation that keeps the same executable heads while reducing helper spread
- the seeded continuation saturation proof showing the current `path_build` floor is already canonical
- the probe-companion follow-up showing witness-only probe injection does not widen the lane

## Run contributions

### Broad executable proof: `RUN_GRAVEYARD_VALIDITY_ENTROPY_CORRELATION_EXECUTABLE_BROAD_0002`

- first real executable correlation-side floor
- wrapper result is `PASS__EXECUTED_CYCLE`
- primary admitted terms are `correlation` and `correlation_polarity`
- `polarity` is bridge witness only
- `information`, `bound`, and `work` are non-bridge residue
- `probe` is substrate companionship, not entropy landing
- state counts are `12 / 54 / 54 / 84`

Key retained surfaces:
- `reports/graveyard_first_validity_wrapper_report.json`
- `state.json`

### Negative boundary probes: `...WORK_STRIP_BROAD_0001`, `...SEED_CLAMPED_BROAD_0001`

- both runs return `PASS__NO_EXECUTED_CYCLE`
- both stop at `STOPPED__LOWER_LOOP_PACKET_FAILED`
- `work_strip_broad` is the cleaner negative boundary probe because it drops `work` and `probe` but still leaves `bound`
- `seed_clamped_broad` adds no executable value beyond that failure

Key retained surfaces:
- `...WORK_STRIP_BROAD_0001/reports/graveyard_first_validity_wrapper_report.json`
- `...SEED_CLAMPED_BROAD_0001/reports/graveyard_first_validity_wrapper_report.json`

### Cleaner active continuation: `RUN_GRAVEYARD_VALIDITY_ENTROPY_CORRELATION_EXECUTABLE_CLUSTER_CLAMP_BROAD_0002`

- this is the cleaner active executable continuation for the same correlation-side floor
- retained wrapper says:
  - `wrapper_status = PASS__PATH_BUILD_SATURATED`
  - `executed_cycles = 8`
  - `stop_reason = STOPPED__PACK_SELECTOR_FAILED`
- primary admitted terms remain `correlation` and `correlation_polarity`
- accepted bridge witnesses are `polarity` and `density_entropy`
- wrapper-level non-bridge residue is reduced to `entropy`
- counts move to `11 / 63 / 63 / 95`

Key retained surfaces:
- `reports/graveyard_first_validity_wrapper_report.json`
- `reports/a1_external_memo_batch_driver_report.json`
- `a1_sandbox/cold_core/000009_A1_COLD_CORE_PROPOSALS_v1.json`
- `a1_sandbox/outgoing/000008_A1_STRATEGY_v1__PACK_SELECTOR.json`

### Saturated seeded continuation: `RUN_GRAVEYARD_VALIDITY_ENTROPY_CORRELATION_EXECUTABLE_CLUSTER_CLAMP_BROAD_CONT_0006`

- wrapper result is `PASS__PATH_BUILD_SATURATED`
- the sequence-2 `path_build` allowlist is `correlation`, `correlation_polarity`, `density_entropy`
- all three are already canonical in the seeded state
- `partial_trace` bleed is gone at cold-core
- this lane is locally saturated under its current family fence

Key retained surfaces:
- `reports/graveyard_first_validity_wrapper_report.json`
- `a1_sandbox/cold_core/000002_A1_COLD_CORE_PROPOSALS_v1.json`

### Probe-companion follow-up: `RUN_GRAVEYARD_VALIDITY_ENTROPY_CORRELATION_EXECUTABLE_CLUSTER_CLAMP_BROAD_PROBE_COMPANION_0001`

- retained wrapper says:
  - `wrapper_status = PASS__PATH_BUILD_SATURATED`
  - `executed_cycles = 0`
- primary executable heads stay `correlation` and `correlation_polarity`
- witness-only probe coverage does not widen the lane

Key retained surfaces:
- `reports/graveyard_first_validity_wrapper_report.json`

## Current family read

- broad `_0002` is the first honest executable proof for the entropy correlation lane
- `work_strip_broad` and `seed_clamped_broad` are negative boundary probes, not replacements
- cluster-clamp `_0002` is the cleaner active executable continuation
- seeded continuation `_0006` is locally saturated under the current family fence
- probe-companion `_0001` does not currently advance the branch
- preserved contradictions:
  - some doctrine paraphrases cluster-clamp `_0002` as `PASS__EXECUTED_CYCLE`, but the retained wrapper says `PASS__PATH_BUILD_SATURATED` with `executed_cycles = 8`
  - some doctrine paraphrases probe-companion `_0001` as `PASS__EXECUTED_CYCLE` with `executed_cycles = 2`, but the retained wrapper says `PASS__PATH_BUILD_SATURATED` with `executed_cycles = 0`

## Citation rule

- prefer citing this anchor surface when the active doc is making a family-level point about:
  - executable entropy entry
  - correlation-side head landing
  - negative helper-strip boundary probes
  - cluster-clamped continuation
  - local saturation under the current family fence
- cite raw run paths directly only when the exact file artifact is itself the point

## Regeneration witness

See:

- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_BRIDGE_EXECUTABLE_CLUSTER__v1.md`
