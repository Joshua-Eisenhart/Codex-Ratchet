# Morning Briefing Spec

Wiki steward writes this at first tick past 06:00 local time to `~/wiki/projects/codex-ratchet/morning_briefing_YYYY-MM-DD.md`.

## Required sections (in order)

```
# Morning Briefing — <YYYY-MM-DD>
last_updated: <ISO>
owner_greeting: "Overnight summary below. Say `audit` to L3 for live details."

## Executive summary (≤5 bullets)
- Runner uptime: <start_time> → now, <N> sims executed
- Tier gate transitions: <A green time>, <B green time>, <D green time if reached>
- Blocking questions: <count from _steward_questions.md>
- Health flags: <from meta_audit.md>
- Hot files: <top 3 commit counts by prefix in last 8h>

## Runner stats
- total executed: <N>
- success rate: <done / (done+fail)>
- failed: <list top 10 FAILs with basename>
- skipped (hang-prone or utility): <count>
- avg duration per sim: <seconds>
- longest sim: <basename, duration>

## Tier progress
- Tier A: <gate state> — <sims done>
- Tier B: <gate state> — <sims done per layer>
- Tier D: <gate state> — <UNSAT certificates produced>
- Tier VIZ: <slice N complete> — <tests passing>
- Tier META: <flags total: info/warn/critical>

## Blocking L3 questions
Copy section verbatim from `_steward_questions.md`. These need owner decision.

## Non-blocking observations
- Canonical conformance: <conformant>/<total> — link canonical_conformance_audit.md
- Overnight drift: any major doc/memory/harness changes worth flagging
- Fleet health: any Hermes terminal that hasn't ticked in >2h
- Runner thermal: count of cooldown pauses overnight

## What wakes the owner
Three-level urgency:
- 🔴 URGENT (telegram sent): runner died, >20 consecutive FAILs, harness corruption, canonical abuse critical from META
- 🟡 NEEDS DECISION (in _steward_questions.md): orphan policy, ambiguous library issues, tier gate ambiguity
- 🟢 FYI (in this briefing): routine progress, gate transitions, slice completions

## Recommended morning actions
Auto-suggested based on state:
- If blocking questions present: answer them
- If next tier ready to launch: say `go` to L3
- If canonical conformance dropped: triage systematic violation patterns
- If runner paused >1h thermal: investigate ambient heat source

## Full fleet snapshot
(compressed paste from STATUS.md for completeness)
```

## Steward rules for briefing generation

1. Compute from actual runner log, queue files, commit history, and `_steward_log.md` — never from speculation.
2. Keep total briefing ≤500 words unless content requires more.
3. If nothing notable overnight, say "Steady progress; no decisions needed" and list stats only.
4. Never duplicate information L3 would read from STATUS.md; this briefing is for owner, not Opus.
5. Briefing is append-only: write once per morning, don't overwrite later same-day ticks.
6. On weekends, include a compact 7-day trend if recent past briefings exist.

## Generation cadence

- Triggered by first wiki-steward tick after 06:00 local
- One briefing per calendar day
- If steward has been down, catch up by generating yesterday's retroactively from logs
