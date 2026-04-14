# Controller Maintenance Checklist

Status: PRIMARY LIVE RUN-OPERATIONS SURFACE

Goal: keep each on-demand Hermes-controlled run healthy, bounded, and aligned while using Claude Code/Codex CLI as workers when helpful. The controller exists to manage careful engine construction through validated legos; sim execution is one instrument in that process, not the product.

## Before a run
- identify the primary lane
- identify the maintenance lane
- identify whether the primary lane is a tool-capability lane or a scientific lane
- define the bounded objective
- name the exact lego/build prerequisite or engine-readiness gate the run is supposed to advance
- define expected outputs
- define verify/audit step
- if the run uses autoresearch-style maintenance or tool-capability hardening, define the actual loop contract explicitly before launch:
  - one measurable objective
  - one verify command
  - one guard command when regressions matter
  - one focused change per iteration
  - keep/discard logging before the next iteration
- confirm whether the bounded packet is supplying a baseline, a canonical tool-native counterpart, or an explicit comparison note
- confirm geometry-before-axis if the run touches sim scope
- confirm no destructive/unbounded actions are implied
- confirm worker file sets do not overlap if parallel workstreams will be used
- confirm the exact worker command(s) and interpreter(s) that will be used
- confirm at least one real execution path exists before announcing the run as active
- confirm that any examples named in chat or a handoff note are being treated as seed examples rather than an exhaustive list if broader live surfaces indicate a better bounded nearby move

## Launch
- send launch acknowledgement
- state current lane and primary task
- if a worker is launched, record exact command/session being used
- if Telegram reporting is active, send initial run status
- if Telegram reporting is active, use the same lane/task/health/changed-files schema described in `docs/plans/on-demand-telegram-runner.md`
- only call the run `running` after verifying the real worker/process is actually active
- if Claude Code is useful for a bounded non-overlapping subtask, launch it explicitly and record its session too

## During a run
### Heartbeat contents
- current lane
- current construction task
- last successful command/build-validation step completed
- current health state: healthy / blocked / degraded
- files/results changed so far
- next bounded step

### Heartbeat cadence
- send an immediate first heartbeat after confirming the real worker is active
- default: every 5 minutes during active Telegram-controlled runs
- keep the message short if there is little change
- the minimum useful payload is: still running, current task, current health
- include whether the checked process is the main worker, a bounded Claude worker, or both

### Health checks
- worker/process still active
- no repeated crash loop
- no stale waiting state
- no scope drift beyond the declared batch
- truth/maintenance closure still planned
- if background process is used, progress polling is still live
- if Telegram reporting is active, the latest heartbeat still matches the actual worker state and has not gone stale
- do not confuse a reporting/heartbeat helper with the actual work process
- if the main worker exited, report that explicitly and switch to blocked or closeout mode

### Scope discipline
- do not widen from geometry into axis work
- do not widen from baseline engine work into broad bridge closure
- do not treat running more sims as success unless they advanced lego completion, validation, or engine-readiness gates
- do not accept vague worker claims without file/result grounding
- if prose and result JSON disagree, trust the newer result file first and mark prose stale

## After a run
- run the bounded audit/verification pass
- classify outputs with explicit truth labels
- state what build prerequisite, lego state, or engine-readiness gate actually moved
- update touched maintenance surfaces or explicitly queue them
- record blockers and next bounded move
- if docs/wiki/ledgers were made stale, update or queue the update before closing
- send compact closeout report
- if Telegram reporting was active, include truth-label deltas and maintenance-surface updates/queues in the closeout
- if the run failed mid-batch, include which exact step failed and which steps did complete

## Maintenance closure surfaces
Check whether this run requires updates to:
- `docs/plans/sim_backlog_matrix.md`
- `docs/plans/sim_truth_audit.md`
- `docs/plans/tool_integration_maintenance_matrix.md`
- `docs/plans/controller_maintenance_checklist.md`
- `docs/plans/on-demand-telegram-runner.md`
- `new docs/16_lego_build_catalog.md`
- `new docs/17_actual_lego_registry.md`
- wiki concept pages under `/Users/joshuaeisenhart/wiki/concepts/`

## Anti-patterns
- silent long-running work with no heartbeat
- worker becomes truth authority
- scheduled autonomy when the user wants on-demand control
- overlapping workers on the same file set
- final summary without audit/verification
- heartbeat loop exists but no real work process is active
- claiming a run is healthy because a helper process is alive while the main work already exited
