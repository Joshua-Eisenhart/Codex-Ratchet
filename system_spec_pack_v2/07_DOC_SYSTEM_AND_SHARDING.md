# Doc System + Sharding (System Spec Pack v2)
Status: DRAFT / NONCANON
Date: 2026-02-20

## Hard Policy
- Do not modify `core_docs/`.
- Avoid file-per-batch explosions.
- Prefer append-only logs with size-based sharding.

## Run Directory (self-contained)
Recommended fixed surface per run:

- `state.json`
- `events.###.jsonl` (append-only; shard by bytes)
- `outbox/export_blocks.###.txt` (append-only; shard by bytes)
- `sim_manifests/*.json` (content-addressed manifests)
- `zips/` (optional trace artifacts; content-addressed)
- `a2_feedback_state/` (run-local noncanon feedback outputs)

## Archive Discipline
- Experiments live under `next_run/sandbox/runs/`.
- Anything noisy or obsolete gets moved under `next_run/_archive/` (never deleted during iteration).

