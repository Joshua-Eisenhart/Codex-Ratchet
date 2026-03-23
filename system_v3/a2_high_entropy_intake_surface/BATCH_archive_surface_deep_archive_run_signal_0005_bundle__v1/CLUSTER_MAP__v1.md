# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_signal_0005_bundle__v1`
Date: 2026-03-09

## Cluster 1: Self-Contained Signal Export Kit
- archive meaning:
  - this object is not just a zipped run root; it is a fuller export kit that carries the runtime-like run plus surrounding export families
- bound evidence:
  - the zip contains `1271` file members under one `RUN_SIGNAL_0005/` root
  - it preserves `60` `a1_strategies`, `60` `outbox` blocks, `60` `snapshots`, `120` `reports`, `360` local `sim` evidence files, and the full `541` packet lattice
- retained interpretation:
  - useful archive bridge because it turns the thinner signal-run family into a much more self-contained historical export surface

## Cluster 2: Fully Aligned Sixty-Pass Runtime Surface
- archive meaning:
  - the embedded run-core surfaces are internally aligned on the same sixty-pass trajectory
- bound evidence:
  - embedded summary, sequence, state, soak, and event rows all agree on `60` passes and `960` accepted items
  - each result row preserves `accepted 16`, `parked 0`, `rejected 0`, and `6` sim outputs
- retained interpretation:
  - useful as the repaired version of the signal-plus-audit family where runtime-facing counts no longer compress away retained transport

## Cluster 3: Clean Transport With Heavy Promotion Debt
- archive meaning:
  - zero parked and zero rejected packet counters still do not imply semantic closure
- bound evidence:
  - embedded summary and soak report both show zero park and reject totals
  - embedded state keeps `60` pending canonical evidence items, `240` kill signals, and `360` `PARKED` sim promotion states
- retained interpretation:
  - strong archive evidence that semantic promotion debt persists even inside a self-contained export bundle

## Cluster 4: Dual Audit Overlay Still Persists
- archive meaning:
  - the bundle preserves two historical audit surfaces in addition to the run-core files and export bodies
- bound evidence:
  - `SIGNAL_AUDIT.json` aligns with the sixty-pass runtime surface
  - `REPLAY_AUDIT.json` reconstructs all `541` packet events and marks determinism `pass true`
- retained interpretation:
  - valuable archive layer because the bundle keeps both runtime outputs and post-run interpretive overlays

## Cluster 5: Deterministic Replay With Divergent Final Hash
- archive meaning:
  - replay determinism still does not collapse replay truth into run-final truth
- bound evidence:
  - replay audit is deterministic
  - replay final hash is `ed1a34...`
  - embedded summary/state final hash is `0045ff...`
  - embedded event-lattice endpoint hash is `299c9c...`
- retained interpretation:
  - useful historical example where a richer self-contained bundle still retains three nonidentical closure surfaces

## Cluster 6: Renumbered And Divergent Consumed Strategy Lane
- archive meaning:
  - consumed strategy residue and embedded transport residue use different naming regimes and almost entirely different bytes
- bound evidence:
  - embedded strategy packets are `000001` through `000060`
  - consumed strategy packets are `400001` through `400060`
  - only step `1` is byte-identical across the two lanes
- retained interpretation:
  - useful demotion evidence because packet identity cannot be reconstructed from filename order alone

## Cluster 7: Embedded Evidence-Body Families
- archive meaning:
  - the bundle does not merely reference evidence bodies; it carries them
- bound evidence:
  - `sim/` keeps `360` text evidence files
  - `snapshots/` keeps `60` `THREAD_S_SAVE_SNAPSHOT v2` bodies
  - `outbox/` keeps `60` export blocks
  - `reports/` keeps both compile JSONs and B-layer eval reports
- retained interpretation:
  - archive object is materially closer to a replay/export kit than to a thin terminal snapshot

## Cluster 8: Signal Audit Nullability Seam
- archive meaning:
  - even the richer bundle still preserves a small audit-surface null seam
- bound evidence:
  - `SIGNAL_AUDIT.json` reports `MATH_DEF 120` in `kill_kind_counts`
  - the same file omits or nulls `killed_math_count`
- retained interpretation:
  - useful archive evidence that alignment of headline counts does not imply all audit fields are semantically closed
