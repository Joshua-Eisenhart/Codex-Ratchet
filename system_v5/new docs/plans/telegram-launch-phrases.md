# Telegram Launch Phrases

Goal: define short on-demand Telegram commands/prompts that Hermes can follow to start bounded runs without widening scope or bloating the system.

Core rule:
- the queue decides the work by default
- not the Telegram message
- the Telegram message should usually only specify duration, run intent, and optional mode hints

Default mode:
- on-demand only
- Hermes is controller
- progress/health reports during the run
- closeout audit at the end

## Minimal launch phrases

Preferred defaults:
- "Run for 1 hour from the live queue. Report progress and health."
- "Run for 60 minutes. Use the plan. Report progress and health."
- "Do a 1-hour bounded run from the live queue."
- "Run 1 hour and report progress."

Interpretation:
- Hermes reads the live control surfaces first
- Hermes chooses the next bounded task from the live queue
- Hermes keeps one primary lane plus one maintenance lane
- Hermes updates the same surfaces at closeout

### 1. Short default run
"Run for 30 minutes from the live queue. Report progress and health."

### 2. One-hour default run
"Run for 1 hour from the live queue. Report progress and health."

### 3. Geometry-first default run
"Run for 1 hour from the live queue. Geometry-first. Report progress and health."

### 4. Maintenance-heavy default run
"Run for 1 hour from the live queue. Maintenance-heavy. Report progress and health."

### 5. Claude-if-useful default run
"Run for 1 hour from the live queue. Use Claude Code if useful. Report progress and health."

## Optional modifiers
Add one or more only when you want to bias the queue, not replace it:
- "Geometry-first."
- "Maintenance-heavy."
- "Use Claude Code if useful."
- "Do not edit sims, audit only."
- "Do one rerun if needed."
- "Do wiki sync if docs/results changed materially."

## Expected persistence behavior
Runs should preserve continuity through repo-local maintenance surfaces, not through vague memory alone:
- `docs/plans/sim_backlog_matrix.md`
- `docs/plans/sim_truth_audit.md`
- `docs/plans/tool_integration_maintenance_matrix.md`
- `docs/plans/controller_maintenance_checklist.md`
- `docs/plans/sim_process_gap_log.md`
- `new docs/16_lego_build_catalog.md`
- `new docs/17_actual_lego_registry.md`
- `/Users/joshuaeisenhart/wiki`

## Rule against system bloat
Runs should improve and maintain the system at the same time, but only in bounded ways:
- one primary lane plus one maintenance lane by default
- no broad scope expansion
- no new control surfaces unless clearly needed
- no duplicate trackers when an existing one can be updated
- no scheduled mode unless explicitly enabled later
