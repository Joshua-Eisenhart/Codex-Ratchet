# A2_3_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_signal_0004__v1`
Date: 2026-03-09

## Distillate 1
`RUN_SIGNAL_0004` is a hybrid signal-plus-audit run, not a plain direct signal run like `RUN_SIGNAL_0002` or `RUN_SIGNAL_0003`.

## Distillate 2
Its main historical contradiction is compressed accounting over a larger retained transport surface: `summary.json` reports forty steps and six hundred forty accepted items, while retained event/state/sequence surfaces preserve sixty A1 passes and nine hundred sixty accepted items across duplicated early steps.

## Distillate 3
Transport cleanliness does not eliminate semantic debt. Final state still carries sixty pending canonical evidence items and three hundred sixty `PARKED` sim promotion states despite zero parked and zero rejected packet counters.

## Distillate 4
Replay audit adds a second historical truth surface: it is internally deterministic, but its replay final hash does not match either the final run snapshot hash or the last event-lattice hash.

## Distillate 5
Packet lineage is split across renamed lanes and audit overlays. Embedded strategy packets are `000001`-style while consumed packets are `400001`-style, only the first pair is byte-identical, and the audit layer keeps a one-for-one replay inventory that mostly parks instead of replaying cleanly.
