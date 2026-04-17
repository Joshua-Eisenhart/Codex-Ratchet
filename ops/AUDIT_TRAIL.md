# Audit Trail — canonical locations L3 (Opus) reads

Every terminal writes status to these paths. L3 reads them directly; never asks owner to paste.

## The dashboard (single-file L3 audit)

`~/wiki/projects/codex-ratchet/STATUS.md` — one-page live dashboard. Wiki steward cron rewrites every 30 min from source files below.

Required sections:

```
# Codex-Ratchet Status — <ISO timestamp>

## Runner
- PID: <pid or "stopped">  (liveness: `ps -p <pid>` verified)
- Thermal: cpu_speed_limit=<N>/100 (pause<85, resume>95)
- Current probe: <basename or "idle">
- Last 10 log lines: (tail)

## Queues
- tier_a: <pending>/<done>/<failed>  (<top 3 pending>)
- tier_b: <pending>/<done>/<failed>
- tier_d: <pending>/<done>/<failed>
- default: <pending>/<done>/<failed>

## Tiers
- Tier A: <state>   Gate: <red|yellow|green>   Evidence: tier_a.md
- Tier B: <state>   Gate: <red|yellow|green>   Evidence: tier_b.md
- Tier D: <state>   Gate: <red|yellow|green>   Evidence: tier_d.md

## Active terminals (liveness verified)
Each line: <terminal_id> pid=<pid> alive=<yes|no> brief=<brief> last_event=<cycle_end|exited|started> at=<ISO>

Source: /tmp/hermes_active_scopes.txt + `ps -p` liveness check per entry.

## Pending L3 judgment
<contents of _steward_questions.md or "(none)">

## Last 5 gate pass/blocker events
<tail from _steward_log.md filtered on "started|exited|gate"; exclude cycle_end lines>

## Health flags
<any audit flags from last steward tick, or "(clean)">
```

### Liveness check requirement

For every terminal in `/tmp/hermes_active_scopes.txt`, steward runs `ps -p <pid>` and records `alive=yes|no`. Dead terminals in STATUS.md are labeled clearly so L3 doesn't misinterpret a stale scope entry.

## Canonical status files (single source of truth per tier)

| File | Owner | Contains |
|---|---|---|
| `~/wiki/projects/codex-ratchet/STATUS.md` | wiki steward | the dashboard |
| `~/wiki/projects/codex-ratchet/tier_a.md` | Tier A Hermes | gate evidence, probe list, auditor log |
| `~/wiki/projects/codex-ratchet/tier_b.md` | Tier B Hermes | gate evidence, per-layer reports |
| `~/wiki/projects/codex-ratchet/tier_b_<layer>.md` | Tier B sub-worker | per-layer coverage detail |
| `~/wiki/projects/codex-ratchet/tier_d.md` | Tier D Hermes | gate evidence, UNSAT summary |
| `~/wiki/projects/codex-ratchet/tier_d_certificates.md` | Tier D | human-readable UNSAT list |
| `~/wiki/projects/codex-ratchet/_steward_log.md` | wiki steward | append-only timeline of events |
| `~/wiki/projects/codex-ratchet/_steward_questions.md` | wiki steward | pending L3 judgment calls |
| `~/wiki/projects/codex-ratchet/digest_<date>.md` | wiki steward | daily digest |
| `ops/queue_tier_*.txt` | Hermes + runner | queue state with DONE/FAIL markers |
| `overnight_logs/sim_runner_current.log` | runner | execution log (symlink to latest) |

## Writing discipline

1. One file per purpose. No scattering status across many files.
2. Every status file has a `last_updated: <ISO>` line at the top.
3. `_steward_log.md` is append-only; never rewritten, never deleted.
4. `tier_*.md` is rewritten by its owning Hermes at each meaningful state change.
5. `STATUS.md` is rewritten by wiki steward every 30 min from the files above.
6. No status lives in telegrams or terminal pastes. If a Hermes or worker produces output that needs to persist, it writes to a file listed above.

## L3 audit protocol

When owner asks "how's it going" or similar:
1. L3 reads `~/wiki/projects/codex-ratchet/STATUS.md` first (single file, whole picture).
2. If deeper detail needed, L3 reads the specific `tier_*.md` referenced.
3. If discrepancy suspected, L3 reads `_steward_log.md` tail and `overnight_logs/sim_runner_current.log` tail.
4. L3 never asks owner to paste. Always reads directly.

## Terminal check-in

Each Hermes terminal writes structured lines to `_steward_log.md`:

```
<ISO> <terminal_id> <brief> started scope=<list> pid=<pid>
<ISO> <terminal_id> <brief> cycle_end status=<polling|idle|working>     # healthy cycle pause (still alive)
<ISO> <terminal_id> <brief> exited status=<gate_pass|blocker|failed|killed>  # process ended
```

Distinctions:
- `cycle_end` — a poll loop or work batch completed; process still alive for next cycle
- `exited status=gate_pass` — clean completion, gate green
- `exited status=blocker` — stopped because brief declared blocker; needs L3
- `exited status=failed` — process crashed or unhandled exception
- `exited status=killed` — OS kill or owner-stop; not a failure

L3 interprets: only `exited` lines mean the terminal is dead. `cycle_end` does NOT mean dead.

Each worker Claude also logs one line per probe committed:

```
<ISO> <terminal_id> <worker_id> probe=<basename> commit=<sha> enqueued=<queue>
```

This gives L3 a single-file timeline across all agents.

## Dashboard regeneration

Wiki steward rebuilds `STATUS.md` from authoritative sources each tick. If steward is down, last-known state persists. L3 checks `last_updated` timestamp — if >1h old, flags staleness and reads source files directly.
