# Hermes Rules — shared protocol for all briefs

Every Hermes brief invokes this file. Every worker spawned by Hermes also reads this.

## 1. Harness location (authoritative)

- Harness: `~/wiki/harness/`
- Entry point: `~/wiki/harness/00_READ_FIRST.md`
- Every Claude worker reads the entry point before any task.

## 2. Preflight protocol (run before any main work)

Step 1 — Inspect: `git status --short`

Step 2 — Auto-handle SAFE buckets (commit or delete, no questions asked):

| Bucket | Pattern | Action |
|---|---|---|
| A | `system_v4/**/sim_results/*.json` | `git add` + commit `"auto: sim-results snapshot <date>"` |
| B | `system_v5/new docs/*.json` | `git add` + commit `"auto: doc metadata snapshot <date>"` |
| C | `overnight_logs/*.json` (if NOT gitignored) | `git add` + commit `"auto: overnight log snapshot <date>"` |
| D | `**/.DS_Store`, `* 2.py` (space-number macOS dupes) | `rm` (no commit) |
| E | New `system_v4/probes/sim_flux_*.py`, `sim_u1_*.py`, `*_shell_canonical.py` (≤500 lines) | `git add` + commit `"auto: new shell-local sims <date>"` |

Step 3 — BLOCK on unsafe buckets (report to L3, do not proceed):

- Any change to: `.gitignore`, `Makefile`, `CLAUDE.md`, `pyproject.toml`, `requirements.txt`, `.github/`, `.claude/`, or files containing `secret|credential|.env`
- Deleted files not in buckets A–E
- New `.py` files >500 lines outside `*_shell_canonical.py` pattern
- Scopes owned by a current sibling Hermes terminal (check `/tmp/hermes_active_scopes.txt`)
- Untracked directories not named: `system_v4/`, `system_v5/`, `overnight_logs/`, `scripts/`, `tests/`, `tools/`, `ops/`

Step 4 — Verify: `git status --short` empty → proceed. Non-empty → telegram L3 with specific items + category guess.

Step 5 — Record active scope: append to `/tmp/hermes_active_scopes.txt`:
`<terminal_id>:<session_start>:<brief_name>:<file_prefix_scopes>`

## 3. Worker spawning rules

- Use `hermes -w` for isolated worktrees per worker.
- Model tier: Haiku for mechanical work, Sonnet for math/reasoning work, Opus only for owner-level decisions (escalate, don't spawn).
- Max 9 concurrent Claude terminals per tier (peak).
- Each worker prompt MUST include: path to `~/wiki/harness/00_READ_FIRST.md`, file-prefix scope, setup-only vs launch-authorized declaration, success criteria.
- Disjoint file-prefix scopes — no shared scope between workers.

## 4. GPT-5.4 (Hermes self) rules

- Parse brief → produce spawn plan at `~/wiki/projects/codex-ratchet/<brief>_spawn_plan.md`.
- Spawn in one batch where possible.
- Run audit-loop Haiku terminal continuously at 30-min cadence.
- Do NOT report progress to L3. Report gate pass OR blocker only.
- Verify completion claims before reporting gate pass (ps, git log, file read).

## 5. Failure modes

- Worker stalled >20 min with no file change → kill + respawn.
- 2+ workers conflict on scope → pause, report to L3.
- Boundary needs research judgment → stop, report to L3 with specific question. Never guess.

## 6. Artifact conventions

- All sims: repo per `REPO_LAYOUT.md` in `system_v5/new docs/`.
- Tier reports: `~/wiki/projects/codex-ratchet/tier_<X>.md`.
- Spawn plans: `~/wiki/projects/codex-ratchet/<brief>_spawn_plan.md`.
- New doctrine: propose at `~/wiki/harness/` — notify L3 before committing.
- Never modify `~/wiki/current/` (owner-authored spine).

## 7. Language discipline (enforced everywhere)

Banned verbs in all reports and worker output: `causes, creates, drives, produces, generates, forces, determines, makes`.
Preferred: `survived, admitted, excluded, coupled with, co-vary under, stable under, pulled back, UNSAT under, indistinguishable`.
Exception: `03_language_discipline.md` in the harness (BAD-examples column).

## 8. Status labels (never collapsed)

`exists` < `runs` < `passes local rerun` < `canonical by process`.
Never imply a higher label from a lower one. Never use "verified / confirmed / ALL PASS" without specifying which label.

## 9. Reporting to L3

- One telegram line on gate pass or blocker.
- No progress chatter.
- Telegram: `joshua.eisenhart@gmail.com` via iMessage daemon at `/tmp/lev_imessage_daemon.py`.
