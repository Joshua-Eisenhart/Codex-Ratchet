# ratchet_standing_process_v0

This is a scratch diagnostic ops-ratchet over the repo estate. It treats the feed
as recomputable disagreements on disk, not as physics evidence.

Boundary:
- classification: `scratch_diagnostic`
- promotion_allowed: `false`
- no three-engine ceremony is claimed
- numeric demands only use `parity-recompute-numpy` when that checker is locked

Entry point:

```bash
$(make -pn | awk -F' = ' '/^PYTHON = / {print $2; exit}') system_v7/sims/ratchet_standing_process_v0/run_tick.py --ticks 3 --tick-start 2026-07-03T00:00:00Z
```

Persistent outputs:
- `ledger.jsonl`: append-only event ledger
- `state.json`: current locked checkers and demand frontier
- `run_summary.json`: latest bounded run summary
