# Queue Safety Audit

Date: 2026-04-29

## Readout

`system_v5/ops/stage_gate.json` says:

- active stage: `lego`
- `allow_default_queue_late_stage`: `false`
- `allow_tier_d_launch`: `false`

`system_v5/ops/queue_default.txt` is the fallback queue. It says it should contain only tool sims, tool-integration sims, and local lego-stage work, excluding pairwise/coexistence/bridge/axis/engine-style probes.

Current queue state from read-only inspection:

- Tier A: 0 pending
- Tier B: 0 pending
- Tier D: blocked by stage gate
- Default: pending work remains

## Safety Rule

Do not relaunch the whole default queue while sim contract lint is red. Build and run a small batch only after the selected entries are checked against the stage gate.

## Small Safe Batch Policy

For the next runner batch:

1. Select 5-10 pending `queue_default.txt` entries.
2. Exclude names containing coupling, coexistence, bridge, axis, engine, topology-variant, emergence, or pairwise unless the stage gate changes.
3. Prefer tool, tool-integration, and lego-local entries.
4. Run the batch.
5. Re-run `scripts/lint_sim_contract.py`.
6. Commit source and generated results separately.

## Current Recommendation

Hold broad relaunch. First repair one sim-contract family, then run a small queue batch under the policy above.

