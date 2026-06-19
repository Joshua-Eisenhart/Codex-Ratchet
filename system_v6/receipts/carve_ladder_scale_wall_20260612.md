# Carve-Ladder Scale Wall — the State-Artifacted Count-Fixture Pattern Caps at ~6Q (2026-06-12)

```yaml
receipt_kind: process_finding
trigger: gcm_constraint_carve_7q_v0 v0 produced a 1.1 GB result JSON (full 128x128 rho per
  ~558 candidates) — non-committable (repo-bloat), non-reviewable; the untracked blob was
  removed from the working tree (regenerable, never staged)
```

## The finding

The breadth carve ladder's discipline (store EVERY candidate's full rho_{A...} under content
ids — the 3Q-v1 anti-first-failed-label fix) was right through 6Q (64x64 states, ~MB packets)
but does NOT scale: at 7Q the 128x128 complex matrices x ~558 candidates = ~1.1 GB in one
JSON. Committed through 6Q (1Q-6Q all audited count fixtures). 7Q+ requires a LEAN storage
model.

## The lean rebuild (7Q+ going forward)

Store: (a) a content HASH per candidate's rho (the id, mutation-sensitive — preserves the
anti-relabel discipline w/o the matrix); (b) the FULL C1/C2/C3 matrix (the audit's core — it
is small: 3 bits x candidates); (c) a SMALL REPRESENTATIVE SAMPLE of full matrices stored
(GHZ7/W7/cluster + a few survivors + a few kills — enough for the audit to recompute spot
rows); (d) the cut/entropy/MI summary rows (small). NOT every full matrix. Packet stays
under a few MB; the audit recomputes from the sample + the hashes.

## Status

The carve ladder is committed + audited 1Q->6Q. 7Q rebuilds lean (in flight); 8Q follows
lean. The math pattern (each rung +1 candidate, 9 classes, regression holds) is established;
the lean rebuild preserves the auditable core without the blob.
