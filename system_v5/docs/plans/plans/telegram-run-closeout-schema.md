# Telegram Run Closeout Schema

Goal: keep Telegram run reports consistent, compact, and controller-grounded.

## Launch message
- duration bound
- primary lane
- maintenance lane
- bounded objective
- worker choice if any (`Claude Code`, `Codex`, or Hermes-only)
- confirmed active real worker/session IDs

## Heartbeat message
- lane
- current task
- last successful command/sim
- health state (`healthy`, `blocked`, `degraded`)
- files/results changed so far
- next bounded step
- closure state (`truth/maintenance on track` or brief blocker)
- checked real worker state (`main running`, `claude worker running`, `main exited`, etc.)

Cadence:
- default to a short heartbeat every 5 minutes so the user can tell the run is still alive even when progress is incremental

## Closeout message
1. Primary task chosen
2. Exact commands/sims run
3. Files/results changed
4. Truth-label outcome
5. Tool integration / maintenance findings
6. Blockers
7. Next bounded move
8. Which exact step failed or stopped the run, if any

## Compression rule
Keep Telegram messages short and operational. Detailed reasoning belongs in repo docs/wiki, not in the live Telegram thread.
