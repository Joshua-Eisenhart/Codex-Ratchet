# system_v3/a2_derived_indices_noncanonical/
Status: DRAFT / NONCANON
Date: 2026-02-20

Fixed-interface persistent memory for A2 (miner + system-debug layer).

Contract:
- Canonical A2 state lives under `system_v3/a2_state/` (fixed file interface).
- `system_v3/a2_derived_indices_noncanonical/` is optional derived indices and seal logs only (regenerable).
- Append-only logs (JSONL) shard by size; never rewrite closed shards.
