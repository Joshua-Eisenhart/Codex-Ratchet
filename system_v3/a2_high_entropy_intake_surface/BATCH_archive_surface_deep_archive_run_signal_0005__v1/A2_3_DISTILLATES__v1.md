# A2_3_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_run_signal_0005__v1`
Date: 2026-03-09

## Distillate 1
`RUN_SIGNAL_0005` is a hybrid signal-plus-audit run, but unlike `RUN_SIGNAL_0004` its runtime-facing counts are internally aligned.

## Distillate 2
Its main historical read is not summary compression but repaired runtime alignment with lingering audit divergence: summary, state, sequence, soak, and event rows all agree on a sixty-pass lattice and nine hundred sixty accepted items, while replay audit still lands on a different final hash.

## Distillate 3
Transport cleanliness does not eliminate semantic debt. Final state still carries sixty pending canonical evidence items and three hundred sixty `PARKED` sim promotion states despite zero parked and zero rejected packet counters.

## Distillate 4
Replay audit adds a second historical truth surface: it is internally deterministic, but its replay final hash does not match either the final run snapshot hash or the last event-lattice hash.

## Distillate 5
Packet lineage is still split across renamed lanes and an unresolved audit null seam. Embedded strategy packets are `000001`-style while consumed packets are `400001`-style, only the first pair is byte-identical, and `SIGNAL_AUDIT.json` leaves `killed_math_count` null despite nonzero `MATH_DEF` kill counts.
