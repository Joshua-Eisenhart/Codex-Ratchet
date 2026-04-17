# Overnight autonomous operation

Rules for all Hermes terminals while owner sleeps.

## Laptop will stay awake

`caffeinate -di` is running — laptop will not sleep, display may.

## Pre-approved default decisions (no L3 block)

These are answered in advance so no terminal freezes overnight waiting for owner:

1. **Orphan canonical results (80 files, no probe source match)** → DOWNGRADE to `classification: "classical_baseline"` with reason `"orphan_no_source_2026-04-17"`. Do not delete.

2. **iMessage daemon `/tmp/lev_imessage_daemon.py` missing** → use Hermes native telegram transport as primary reporter. Do not retry the daemon path.

3. **New capability-sim gaps identified** (gudhi, torch_ga, qutip, pennylane, cirq, networkx) → author Haiku capability sims for each and enqueue to `ops/queue_tier_a.txt`. One probe per tool. Use `SIM_TEMPLATE.py` pattern.

4. **Sim runner consecutive FAIL > 5** → runner auto-pauses 30 min, then resumes (already configured). No owner action needed.

5. **Hermes terminal exits unexpectedly** → the tier_b/tier_d pollers auto-respawn via cronjob. If gateway dies, runner keeps draining; wiki steward keeps ticking.

6. **Tier A gate passes** → Tier B poller auto-launches workers per `ops/TIER_B.md`. No prompt needed.

7. **Tier B gate passes** → Tier D poller auto-launches boundary workers per `ops/TIER_D.md`.

8. **If a worker can't decide**: append question to `_steward_questions.md`, continue with default-action OR skip that sub-task and log deferred. Never block the whole tier.

## Work queue priorities through the night

Per active reality (2026-04-17 00:45 PDT):

**Tier A remaining work:**
- Write `tool_integration_cvc5_sympy.py` (A4.6)
- Write `tool_integration_toponetx_pyg.py` (A4.5)
- **Extension:** Add 6 capability sims per item 3 above (gudhi, torch_ga, qutip, pennylane, cirq, networkx)
- Audit and declare Tier A gate status
- Update `~/wiki/projects/codex-ratchet/tier_a.md`

**Tier B on A gate pass:**
- Spawn 5 layer workers (B1 gtower, B2 hopf, B3 weyl, B4 flux, B5 clifford)
- Each enqueues probes to `ops/queue_tier_b.txt`
- Target minimum N per layer per `ops/TIER_B.md`

**Tier D on B gate pass:**
- Spawn 4 boundary workers
- Target 2+ UNSAT certificates each
- Enqueue to `ops/queue_tier_d.txt`

**Runner autonomous:**
- Keep draining queues in priority order A > B > D > default
- 2614 default-queue probes remaining (never-run pile)
- Regenerate default queue when empty

## Morning briefing for owner

At first steward tick after 06:00 local time, the wiki steward writes `~/wiki/projects/codex-ratchet/morning_briefing_YYYY-MM-DD.md` with:
- Total sims executed overnight (runner log count)
- Tier gate transitions (A→B, B→D if any)
- Any entries in `_steward_questions.md` that are truly blocking (not pre-approved)
- Any runner 5-fail pause events
- Health flags

Owner reads that file first thing. Single location, no hunting.

## What owner does at wake-up

1. Open this chat, say `audit`.
2. L3 reads STATUS.md + morning_briefing_YYYY-MM-DD.md. Summarizes in <10 lines.
3. Any blocked L3 questions → owner answers, next tier proceeds.

## Emergency unblock

If something is truly stuck and owner needs to act urgently:
- Check `_steward_questions.md` for the blocking question
- Or kill stuck terminal: `pkill -f hermes-main` and re-launch per `ops/HERMES_RULES.md`
- Runner is independent; won't be affected

## Commit this doc

Part of `ops/`, should be committed so terminals read it consistently.
