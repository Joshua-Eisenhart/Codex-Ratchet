# system_v5 — Docs Home

All human-readable docs for Codex Ratchet live here. Sim code stays in `system_v4/probes/`.

## Layout

| Folder | What |
|---|---|
| `new docs/` | Numbered research docs (00–17+), enforcement rules, contracts, agent workflow |
| `new docs/plans/` | Ignition / draft / audit plans |
| `docs/plans/` | Handoffs, coverage matrices, lane specs, runner scripts |
| `READ ONLY Reference Docs/` | Axes, entropic monism, engine schedules — do not edit |
| `tests/` | System-level test harness |

## Read first

1. `new docs/ENFORCEMENT_AND_PROCESS_RULES.md`
2. `new docs/LLM_CONTROLLER_CONTRACT.md`
3. `new docs/LEGO_SIM_CONTRACT.md`
4. `new docs/AGENT_WORKFLOW_AND_BOOT_ARCHITECTURE.md`

## Rules

- Do not create `docs/` or `new docs/` at repo root — they belong here.
- `READ ONLY Reference Docs/` is canonical reference; edits require explicit approval.
- New plans go under the appropriate `plans/` subdir, not at the top of v5.
