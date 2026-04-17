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

Step 3 — IGNORE runtime-mutated files (expected drift, not blockers):

These files are mutated continuously by the 24/7 runner and other live processes. Do NOT treat them as dirty-tree blockers. Do NOT try to auto-commit them. Simply ignore in preflight:

- `ops/queue_*.txt` (runner rewrites DONE/FAIL markers in-place)
- `ops/sim_queue*.txt`
- `system_v4/**/sim_results/*.json` (runner writes on every probe)
- `system_v4/a2_state/**` (runtime audit/graph state)
- `system_v4/a2_state/audit_logs/**`
- `overnight_logs/**` (runtime logs)
- `/tmp/hermes_active_scopes.txt`

A preflight implementation should:
1. Get `git status --short`
2. Filter out any line whose path matches the ignore patterns above
3. ONLY apply safe-bucket / blocker classification to the remaining paths

Step 4 — BLOCK on unsafe buckets (report to L3, do not proceed):

After ignoring runtime-mutated files, BLOCK only on:
- Any change to: `.gitignore`, `Makefile`, `CLAUDE.md`, `pyproject.toml`, `requirements.txt`, `.github/`, `.claude/`, or files containing `secret|credential|.env`
- Deleted files not in buckets A–E
- New `.py` files >500 lines outside `*_shell_canonical.py` pattern
- Scopes owned by a current sibling Hermes terminal (check `/tmp/hermes_active_scopes.txt`)
- Untracked directories not named: `system_v4/`, `system_v5/`, `overnight_logs/`, `scripts/`, `tests/`, `tools/`, `ops/`

Step 5 — Verify: `git status --short | grep -vE "<ignore patterns from Step 3>"` empty → proceed. Non-empty → telegram L3 with specific items + category guess. Runtime-mutated files never count toward "dirty tree."

Step 6 — Record active scope: append to `/tmp/hermes_active_scopes.txt`:
`<terminal_id>:<session_start>:<brief_name>:<file_prefix_scopes>`

## 3. Worker spawning rules

- Use `hermes -w` for isolated worktrees per worker.
- Model tier: Haiku for mechanical work, Sonnet for math/reasoning work, Opus only for owner-level decisions (escalate, don't spawn).
- **Haiku is INSUFFICIENT for capstone-class probes** — any probe that imports from multiple existing `axis{N}_*.py`, applies a named schedule to state, or asserts `rho_stage2 != rho_stage1` REQUIRES Sonnet minimum. Haiku consistently fabricates (confirmed 2× 2026-04-17: Agent C + haiku capstone). See `memory/feedback_sub_agent_fabrication_incident.md`.
- Max 9 concurrent Claude terminals per tier (peak).
- Each worker prompt MUST include: path to `~/wiki/harness/00_READ_FIRST.md`, file-prefix scope, setup-only vs launch-authorized declaration, success criteria.
- Disjoint file-prefix scopes — no shared scope between workers.
- **Capstone probes MUST pass `ops/detect_capstone_fabrication.py`** before Hermes reports worker done. If fabrication tells found → quarantine + respawn with Sonnet.

## 3a. Capstone-probe prompt template (mandatory for multi-axis + schedule-applied work)

Any worker tasked with a capstone (combining multiple axis probes + applying named schedule) receives this additional clause:

```
MANDATORY REQUIREMENTS (violations = fabrication, will be rejected):

1. `from system_v4.probes.axis<N>_<name> import <primitive>` — ≥3 such imports from real existing probes
2. State (rho) is evolved across stages, NOT re-randomized. Must include this assertion:
     assert not np.allclose(rho_stage2, rho_stage1), "stage evolution required; state must differ"
3. Torch is load-bearing: at least one gradient or autograd-tracked operation applied to the evolved state, not just a proxy of trace/norm
4. z3/cvc5 assertions MUST reference the named schedule variables (not generic int bounds). Vacuous patterns like `BitVec != 0` or `Int >= -10 <= 10` = fabrication
5. sympy MUST prove a non-trivial identity; `sp.satisfiable(True)` = fabrication
6. Clifford blades MUST be applied to the state if imported; importing and not using = fabrication
7. No `random_unitary(seed=N)` substituting for a named schedule

BEFORE reporting done:
  python3 ops/detect_capstone_fabrication.py <probe_file>
must return exit 0. If exit 1, your work is rejected — revise and re-run.

DO NOT commit. Author file, report path + detector exit code to parent.
```

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
- All durable status goes to the canonical audit files — see `ops/AUDIT_TRAIL.md`. L3 reads those files directly; never ask owner to paste output.

## 10. Audit discipline (see ops/AUDIT_TRAIL.md)

- On terminal start: append `<ISO> <terminal_id> <brief> started scope=<list>` to `~/wiki/projects/codex-ratchet/_steward_log.md`.
- On terminal exit: append `<ISO> <terminal_id> <brief> exited status=<gate_pass|blocker|stopped>`.
- On every probe committed by a worker: append `<ISO> <terminal_id> <worker_id> probe=<basename> commit=<sha> enqueued=<queue>`.
- Tier gate evidence goes to `~/wiki/projects/codex-ratchet/tier_<X>.md` with `last_updated:` header line.
- Pending L3 judgment questions go to `~/wiki/projects/codex-ratchet/_steward_questions.md` (one question per section).
- Nothing important stays in terminal scrollback or telegram only.
