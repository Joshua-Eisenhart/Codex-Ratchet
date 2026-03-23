# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_archive_surface_deep_archive_run_foundation_batch_0001__v1`
Extraction mode: `ARCHIVE_DEEP_RUN_FOUNDATION_BATCH_PASS`

## C1) Summary and hardmode metrics surface
- members:
  - `summary.json`
  - `HARDMODE_METRICS.json`
- retained read:
  - the run is remembered both as a clean top-line summary and as a cumulative metrics ledger, and those two layers do not tell the same story about rejections and parked outcomes

## C2) Hash-bound terminal state surface
- members:
  - `state.json`
  - `state.json.sha256`
  - `sequence_state.json`
- retained read:
  - the archive keeps one large final state body with detached integrity and a tiny source-sequence map, but leaves the live megaboot and ruleset identifiers empty

## C3) Packet lattice surface
- members:
  - `zip_packets/000001_A0_TO_A1_SAVE_ZIP.zip`
  - `zip_packets/000001_A1_TO_A0_STRATEGY_ZIP.zip`
  - `zip_packets/000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
  - `zip_packets/000001_SIM_TO_A0_SIM_RESULT_ZIP.zip`
  - continuing through packet index `001571`
- retained read:
  - transport structure is the clearest preserved skeleton of the run: many SIM returns, slightly fewer strategy requests, fewer B returns, and only two save points

## C4) Event-ledger surface
- members:
  - `events.jsonl`
  - first `a1_strategy_request_emitted` event
  - subsequent per-step packet/digest/result events
- retained read:
  - the run’s ledger is explicit enough to show digest evolution and per-step blockers, even where underlying evidence bodies were not retained

## C5) Human-readable soak surface
- members:
  - `soak_report.md`
- retained read:
  - the archive preserves a prose-facing report layer that compresses the run into cycle counts, top failure tags, and the tail of the event stream

## C6) A1 inbox residue surface
- members:
  - `a1_inbox/consumed/`
  - `267` retained consumed strategy zips
- retained read:
  - the run keeps an extra residue copy-line of A1 strategy traffic with phase-like numbering blocks that do not map cleanly onto the normalized packet lattice

## C7) Missing sim evidence surface
- members:
  - runtime-path references to `sim/sim_evidence_*` inside `events.jsonl` and `soak_report.md`
  - absent archived `sim/` subtree
- retained read:
  - the archive kept references to evidence bodies more faithfully than the bodies themselves

## C8) Deferred next family
- next bounded target:
  - `RUN_FOUNDATION_BATCH_0001_PROGRESS_BUNDLE`
- reason:
  - it is the closest derived export of this exact parent run and should reveal what the historical system chose to surface when compressing the parent campaign
