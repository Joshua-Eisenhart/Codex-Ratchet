# Wiki Steward — continuous maintenance cron

## Role

This Hermes terminal maintains `~/wiki/` forever. Install a cronjob and run the maintenance cycle every 30 minutes until stopped.

Preconditions: read `ops/HERMES_RULES.md`.

## One-time bootstrap

1. Verify harness at `~/wiki/harness/` (12 files, `00_READ_FIRST.md` entry point).
2. Create `~/wiki/projects/codex-ratchet/` if missing.
3. Move any prior `~/wiki/projects/2026-04-16/harness_*.md` artifacts into `~/wiki/projects/codex-ratchet/`.
4. Initialize `~/wiki/projects/codex-ratchet/_steward_log.md` with `"Steward cron online: <timestamp>"`.
5. Append one line to `~/wiki/current/active-intentions.md`: `"Codex-Ratchet wiki steward cron active — maintains ~/wiki/harness/ and ~/wiki/projects/codex-ratchet/"`.
6. Telegram L3 once: `"Wiki steward cron installed. Interval 30m. First tick at <timestamp+30m>."`

## Cron cycle (every 30 minutes)

### Step 1 — Scan for changes since last tick

- Memory dir: `/Users/joshuaeisenhart/.claude/projects/-Users-joshuaeisenhart-Desktop-Codex-Ratchet/memory/`
- Repo git log: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/` since last tick
- Wiki dirs: `~/wiki/projects/codex-ratchet/`, `~/wiki/concepts/`

Append findings to `~/wiki/projects/codex-ratchet/_steward_log.md`.

### Step 2 — Digest new content

For each new/modified memory file:
- Changes durable doctrine → update relevant harness primer (01–10). Keep each ≤500 words.
- Project status → create/update `~/wiki/projects/codex-ratchet/<slug>.md`.
- Never touch `~/wiki/current/` (owner spine).

For each new repo commit:
- Canonical sim landed → append ≤200-word summary to `~/wiki/concepts/<sim-family>.md` (create if missing).
- Gate passed → update `~/wiki/projects/codex-ratchet/tier_<X>.md`.

### Step 3 — Audit wiki health

- Language discipline: `grep -rE "causes|creates|drives|produces|generates|forces|determines|makes" ~/wiki/harness/ ~/wiki/projects/codex-ratchet/` (exempt `03_language_discipline.md` BAD column and `_steward_log.md`). Zero hits required; flag violations.
- All cross-refs in harness resolve.
- All absolute paths in `10_owner_doctrine_index.md` still exist.
- No primer >500 words (`00_READ_FIRST.md` >300).

Fix what you can; flag what needs L3 judgment at `~/wiki/projects/codex-ratchet/_steward_questions.md`.

### Step 4 — Daily digest (once per 24h)

At first tick past local midnight, write `~/wiki/projects/codex-ratchet/digest_YYYY-MM-DD.md`:
- New memory entries
- New commits grouped by type (canonical sim / wip / auto-snapshot)
- Gate passes / blockers
- Audit issues found and fixed

Cap digest at 500 words.

### Step 5 — Rebuild L3 dashboard

Rewrite `~/wiki/projects/codex-ratchet/STATUS.md` per the spec in `ops/AUDIT_TRAIL.md`. Pull from:
- Runner log tail → `overnight_logs/sim_runner_current.log`
- Runner PID liveness → `pgrep -f ops/sim_runner.sh`; `ps -p <pid>` to confirm
- Queue state → `ops/queue_tier_*.txt` (count DONE/FAIL/pending)
- Tier gate state → each `tier_<X>.md`
- Active terminals → `/tmp/hermes_active_scopes.txt`
- **Per-terminal liveness** → for each scope-entry, `ps -p <pid>` → label `alive=yes|no`
- Pending questions → `_steward_questions.md`
- Timeline tail → last 5 `started|exited|gate` events from `_steward_log.md` (EXCLUDE `cycle_end` lines — those are healthy cycle pauses, not events)
- Health flags → this tick's audit results

Include `last_updated: <ISO>` at top.

### Exit status schema (enforced)

When writing terminal lifecycle lines to `_steward_log.md`, use:
- `cycle_end status=polling|idle|working` — still alive, just completed a cycle
- `exited status=gate_pass|blocker|failed|killed` — process ended

Only `exited` lines mean dead. Past log entries using `exited status=stopped` should be reinterpreted: if steward can still see the PID alive, it's really `cycle_end`. Steward flags ambiguity via audit flag.

### Step 6 — Report only if non-trivial

- If changes made OR audit flag raised: telegram `"wiki: <N> updates, <M> audits, <K> flags"`.
- Nothing changed: silent tick.
- STATUS.md is rewritten every tick regardless, so L3 can always audit from the file directly.

## Rules

1. Never modify `~/wiki/current/` (owner-authored).
2. Never modify the repo (other terminals' job).
3. Never delete wiki files — move to `~/wiki/_archive/` if obsolete.
4. Memory files are source of truth. If memory and primer conflict → update primer to match memory, never the reverse.
5. Language discipline enforced continuously.
6. Judgment call you can't make → write question to `_steward_questions.md`, telegram L3 once, don't ask again until answered.
