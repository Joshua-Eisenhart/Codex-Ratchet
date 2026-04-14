# On-Demand Telegram Runner

Status: DERIVED OPERATING MODE NOTE — DEFAULT TELEGRAM MODE. Scheduled sprint mode is opt-in only and subordinate to this default.

Goal: launch bounded Hermes-controlled construction work only when the user requests it, while sending progress/status reports during the run so the user can tell it is alive, healthy, and advancing the engine-building process. The run should treat sims as build/validation steps toward lego completion and engine assembly, not as the goal by themselves.

## Launch rule
The Telegram trigger should be minimal by default:
- duration
- run command
- optional mode hint

The user should not need to hand-specify the task each time.
Hermes should choose the next bounded task from the live control surfaces unless the user explicitly overrides that behavior.

## Model
No scheduled autonomy by default.
The user explicitly launches each run.

Default interpretation of a minimal launch such as:
- "Run for 1 hour."
- "Run for 60 minutes."
- "Do a 1-hour bounded run."
- "Run 1 hour and report progress."

is:
1. read the live control surfaces first
2. choose the next bounded construction/validation step from the live queue
3. keep one primary lane plus one maintenance lane
4. report progress and health during the run
5. close with audit
6. update the same continuity surfaces for the next run

Primary live control surfaces:
- `docs/plans/sim_backlog_matrix.md`
- `docs/plans/sim_truth_audit.md`
- `docs/plans/tool_integration_maintenance_matrix.md`
- `docs/plans/controller_maintenance_checklist.md`

Derived diagnostic surface (consult when needed, not as the primary live queue):
- `docs/plans/sim_process_gap_log.md`

## Required run behavior
Every live run should provide:
1. launch acknowledgement
2. current primary task
3. periodic progress/heartbeat updates during the run
4. health/status checks during the run
5. compact closeout report at the end

Required startup checks before saying the run is active:
- identify the exact real worker command(s)
- verify the command/interpreter exists in the current environment
- start the real worker first
- confirm the worker/process is actually running before claiming the run has started
- do not treat a heartbeat loop by itself as the run

Default heartbeat cadence:
- send an immediate first heartbeat right after the real worker is confirmed alive
- send a short heartbeat every 5 minutes during an active run
- if nothing major changed, the heartbeat should still say the run is alive, what it is currently doing, and whether health is healthy / blocked / degraded
- do not wait for a major milestone before proving the run is still active

Heartbeat truth rule:
- each heartbeat must refer to a real worker/process or a real foreground task in progress
- distinguish clearly between controller alive, worker alive, and work completed
- never let "heartbeat alive" imply "real task still running" unless a real task/process check confirms it

## Good progress report contents
- current lane
- current construction task
- last successful command/build-validation step completed
- whether the run is blocked or healthy
- files/results changed so far
- next bounded step
- whether truth/maintenance closure is still on track

## Good health checks
- process still active
- no repeated crash loop
- no stale waiting state
- bounded scope still being respected
- truth/maintenance closure still in plan
- actual work process still active, not merely a reporting helper
- if the main worker exited, say so immediately and switch the run state to blocked/completed rather than pretending it is still live

## Controller rule
Hermes should remain the controller and may use Claude Code CLI or Codex CLI as bounded workers, but the controller owns:
- truth labels
- progress reporting
- health reporting
- final audit/closeout

The Telegram-facing status format should stay aligned with `docs/plans/controller_maintenance_checklist.md` so launch, heartbeat, and closeout messages match the same control surface.

## Preferred execution shape
- user triggers a run manually
- Hermes reads the live queue/control surfaces and chooses the next bounded construction step unless the user gave an explicit override
- Hermes starts a bounded background process or bounded worker session
- Hermes may also start one bounded Claude Code Sonnet/low worker on a non-overlapping maintenance subtask if useful
- Hermes monitors it and reports progress to Telegram during execution
- Hermes closes with an audit-style summary

Failure handling:
- the controller should fail soft when one bounded step fails
- record the blocker, report it, and continue with bounded diagnosis/closeout when safe
- do not let the whole run silently disappear just because one audit command exited nonzero

## Required closeout contents
- final health state
- explicit truth-label outcome for touched result files: `exists`, `runs`, `passes local rerun`, or `canonical by process`
- maintenance surfaces updated or explicitly queued before closure, especially `sim_truth_audit.md` and `tool_integration_maintenance_matrix.md`
- blockers and next bounded build move toward lego completion or engine readiness

## Avoid
- scheduled jobs unless explicitly requested later
- silent long-running work with no heartbeat
- unbounded overnight runs before shorter runs prove healthy
