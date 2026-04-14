# Telegram Sprint Automation

Status: OPTIONAL SCHEDULED MODE — only use if explicitly enabled later. Default Telegram mode is on-demand as defined in `docs/plans/on-demand-telegram-runner.md`.

Goal: run bounded 1-3 hour autonomous maintenance/research sprints under Hermes control, deliver progress/results to Telegram, and keep the system aligned across the required lanes.

## Sprint shape
Each sprint should be bounded and self-contained. No recursive scheduling from inside the run.

## Lane mix per sprint
Every sprint should cover only bounded work, but may include multiple lanes:
1. geometry-manifold lane
2. classical engine lane
3. maintenance/control lane
4. skills/tooling improvement lane
5. wiki/lego ingest lane

## Mandatory controller duties each sprint
- keep truth labels honest
- keep geometry-before-axis discipline
- keep tool-maintenance active
- keep docs/wiki/lego surfaces synchronized when materially changed
- keep the repo healthy: no stale classifications, no drifting maintenance surfaces, no unbounded scope expansion

## Good sprint outputs
- one or more bounded reruns or audits
- updated maintenance docs or skills
- Telegram-delivered compact progress/results summary
- explicit blockers if the sprint cannot proceed safely

## Cron-job constraints
- prompt must be fully self-contained
- no user interaction during runs
- no recursive scheduling from inside cron jobs
- deliver to Telegram target directly

## Good duration policy
- short sprint: 60 minutes
- medium sprint: 120 minutes
- long sprint: 180 minutes

## Good default scope policy
Prefer one primary lane plus one maintenance lane per sprint, not all lanes equally every run. Rotate emphasis across runs while always including maintenance closure.
