# Tier META — Cross-Tier Drift Detector

Runs in parallel with A, B, D, VIZ. Does not produce sims or code. Reads tier reports + commits + wiki content and flags drift.

Preconditions: read `ops/HERMES_RULES.md`, `~/wiki/harness/00_READ_FIRST.md`, `~/wiki/harness/03_language_discipline.md`, `~/wiki/harness/04_status_labels.md`, `~/wiki/harness/08_anti_patterns.md`.

## Role

One Hermes terminal. Cron every 20 min. Read-only across repo + wiki. Writes ONLY to `~/wiki/projects/codex-ratchet/meta_audit.md` (append) and `_steward_questions.md` (blocker class).

Never touches code. Never runs tests. Never enqueues probes. Audits and flags.

## What to detect (drift classes)

### 1. Language violations
- grep banned verbs (`causes, creates, drives, produces, generates, forces, determines, makes`) across:
  - `system_v4/probes/*.py` (new ones since last meta-audit tick)
  - `~/wiki/projects/codex-ratchet/*.md` (except `_steward_log.md` and `harness/03*`)
  - Commit messages from last 20 min
- Flag each hit with file + line.

### 2. Status label collapse
- Search for phrases: `"ALL PASS"`, `"verified"`, `"confirmed"`, `"fully tested"`, `"everything passes"` in tier reports or new commits.
- Confirm each usage specifies which of the four labels (`exists / runs / passes local rerun / canonical by process`). Flag any that don't.

### 3. Scope creep
- Check each terminal's active scope in `/tmp/hermes_active_scopes.txt`.
- Flag commits that touch files outside the declaring terminal's scope.
- Example: Tier A commit modifying `system_v4/visualization/*` → flag.

### 4. Premature collapse of surviving candidates
- Scan tier reports for single-survivor language when multiple candidates are still live (e.g., "the canonical axis 0 is X" when axes 1-6 are still under investigation).
- Flag as "collapse risk" with excerpt.

### 5. Canonical-label abuse
- For any new result JSON with `classification: "canonical"` committed since last tick:
  - Verify `TOOL_INTEGRATION_DEPTH` present with ≥1 `load_bearing` ladder tool (z3/cvc5/sympy/PyG/TopoNetX/Clifford/torch/torch_ga/gudhi)
  - Flag if `load_bearing` is missing or only classical-substrate tools (numpy/scipy/sklearn)

### 6. Lane-skipping
- Per harness/06, coupling program is ordered: shell-local → pairwise → multi-shell → topology-variant → emergence → bridge.
- If a commit introduces a coupling sim that references layers without shell-local coverage in `~/wiki/projects/codex-ratchet/tier_b_<layer>.md`, flag as lane-skip.

### 7. Forward-evolution vs backward-admissibility conflation
- Grep reports for "causes X to emerge" vs "X is admitted under Y" shape collisions. Flag mixing.

### 8. RLHF-style agreement
- Search reports for phrases like "you're right!", "exactly!", "great question" (LLM voice tics). Flag in reports.

## Tick cycle

1. Record tick start ISO to `meta_audit.md`.
2. Pull last tick's timestamp from same file; process only new material since then.
3. Run all 8 detectors.
4. Summarize findings:
   - `flags_total: N`
   - per-class counts
   - top 5 specific excerpts with file paths
5. Append summary to `meta_audit.md` with ISO timestamp.
6. If any flag is CRITICAL (e.g., canonical-label abuse, lane-skip, banned verb in harness/ itself), also write to `_steward_questions.md` as a blocker for L3.
7. Telegram only if CRITICAL (silent otherwise).

## Severity

| Level | Criteria | Action |
|---|---|---|
| info | language violation in draft doc, LLM voice tic | log only |
| warning | status label collapse in tier report, scope creep in commit | log + include in daily digest |
| critical | canonical-label abuse, lane-skip, banned verb inside `~/wiki/harness/` | log + `_steward_questions.md` + telegram L3 |

## Reporting format (per tick)

```
## Meta-audit <ISO>
- flags_total: N (info=x, warning=y, critical=z)
- banned_verbs: [{file, line, excerpt}]
- status_collapse: [{file, phrase}]
- scope_creep: [{commit_sha, terminal, out_of_scope_files}]
- premature_collapse: [{file, excerpt}]
- canonical_abuse: [{result_json, missing}]
- lane_skip: [{commit_sha, probe, missing_layer}]
- forward_backward_mix: [{file, excerpt}]
- rlhf_tics: [{file, excerpt}]
```

## Rules

1. Read-only repo + wiki. Never modify anything except `meta_audit.md` and `_steward_questions.md`.
2. Never flag false positives aggressively — prefer false negatives to noise.
3. If a detector can't parse a file, log once per file per day.
4. Never execute sims or tests.
5. Use harness language in own reports (practice what you audit).
6. Progress chatter: zero. Only summaries appended to `meta_audit.md`.

## Cron spec

- Cadence: every 20 min
- Model: `gpt-5.4-low`
- Provider: `openai-codex`
- Repeat: indefinite
- First tick: immediate

## Where META fits

Wiki steward adds a `## Meta track` section to STATUS.md pulling from `meta_audit.md` last tick:
- flags_total
- critical count (if >0, STATUS.md shows 🔴)
- last tick timestamp

This is the single integrity check that watches the watchers.
