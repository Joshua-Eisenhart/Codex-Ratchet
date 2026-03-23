# New Thread Handoff — System v4 Skill Build

Last updated: 2026-03-21

## Purpose

This doc is the cold-start support surface for opening a fresh Codex thread when
the current thread is too hot.

Use this instead of relying on hidden thread memory.

## Current Repo Truth

- `system_v4` is the active build layer.
- `system_v3/specs` still owns the law.
- `system_v3/a2_state` is still the canonical persistent brain.
- the broad source umbrella is the corpus itself, not one source document.
- current live graph truth is:
  - `110` active registry skills
  - `110` graphed `SKILL` nodes
  - `0` missing
  - `0` stale
- current graph truth source:
  - [GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.json)
- current A2 freshness truth:
  - [A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json)
  - current state is `attention_required` because standing A2 owner surfaces still lag latest evidence
  - this is a real maintenance issue, but it does not erase the live graph/registry truth above

## Hard Corrections To Preserve

- EverMem is a side project, not the main-line build focus.
- `OpenClaw-RL` is the source paper/repo family only.
- the system-facing skill/lane name is `next-state-signal-adaptation`, not `openclaw`.
- the `lev-formalization-placement` lane is landed and parked at disposition.
- do not reopen the lev builder/formalization lane unless new bounded evidence earns it.
- the next unopened lev cluster is:
  - `SKILL_CLUSTER::lev-autodev-exec-validation`
- the first bounded next slice for that cluster is:
  - `a2-lev-autodev-loop-audit-operator`

## Main-Line Next Move

If the fresh thread is continuing the main line, the next bounded move should be:

- build `a2-lev-autodev-loop-audit-operator`

Keep it:

- audit-only
- non-runtime-live
- non-migratory
- repo-held report + packet

Do not widen it into:

- imported runtime ownership
- autonomous execution claims
- cron/background loop claims
- lev stack replacement claims

## Current Secondary Lane

The new paper-derived lane now exists, but it is not the main-line next move:

- source family:
  - `OpenClaw-RL`
- system-facing cluster:
  - `SKILL_CLUSTER::next-state-signal-adaptation`
- current landed slice:
  - `a2-next-state-signal-adaptation-audit-operator`
- current truth source:
  - [A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_NEXT_STATE_SIGNAL_ADAPTATION_AUDIT_REPORT__CURRENT__v1.json)

Important rule:

- keep this lane audit-only and source-bound
- do not call it `openclaw` inside the system
- do not widen it into online RL or runtime import claims

## Boot Files For A Fresh Thread

Read these first:

1. [NEW_THREAD_HANDOFF__SYSTEM_V4_SKILL_BUILD__2026_03_21__v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/NEW_THREAD_HANDOFF__SYSTEM_V4_SKILL_BUILD__2026_03_21__v1.md)
2. [NEW_THREAD_PROMPT__SYSTEM_V4_SKILL_BUILD__2026_03_21__v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/NEW_THREAD_PROMPT__SYSTEM_V4_SKILL_BUILD__2026_03_21__v1.md)
3. [SYSTEM_SKILL_BUILD_PLAN.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/SYSTEM_SKILL_BUILD_PLAN.md)
4. [REPO_SKILL_INTEGRATION_TRACKER.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/REPO_SKILL_INTEGRATION_TRACKER.md)
5. [SKILL_SOURCE_CORPUS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/SKILL_SOURCE_CORPUS.md)
6. [SKILL_CANDIDATES_BACKLOG.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/SKILL_CANDIDATES_BACKLOG.md)
7. [INTENT_SUMMARY.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/INTENT_SUMMARY.md)
8. [A2_BRAIN_SLICE__v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_BRAIN_SLICE__v1.md)
9. [A2_KEY_CONTEXT_APPEND_LOG__v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md)
10. [A2_LEV_AGENTS_PROMOTION_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_LEV_AGENTS_PROMOTION_REPORT__CURRENT__v1.json)
11. [GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.json)
12. [A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json)

## Start-of-Thread Verification

Before building anything new, verify:

1. `SkillRegistry('.')` still loads `110` skills or record the changed number explicitly.
2. graph audit still shows:
   - active `110`
   - graphed `110`
   - missing `0`
   - stale `0`
3. the next lev cluster still points to `SKILL_CLUSTER::lev-autodev-exec-validation`
4. the next-state lane still uses `next-state-signal-adaptation`, not `openclaw`

If any of those drifted, update the front-door docs and standing A2 truth before pushing further.

## Recommended Agent Split

Use bounded helper lanes early instead of keeping all verification in one hot thread.

Recommended split:

1. live-truth audit lane
   - verify registry count, graph count, stale/missing state, and current report dates
2. lev continuity lane
   - verify that `SKILL_CLUSTER::lev-autodev-exec-validation` is still the honest next lev cluster
   - verify that `a2-lev-autodev-loop-audit-operator` is still the honest first bounded slice
3. A2 freshness lane
   - verify whether the current `attention_required` refresher result changes the main-line task or is only a maintenance lag signal

Rule:

- use the agent lanes to audit and bound the start
- do not let them invent new main-line priorities

## Expected Outputs From The Fresh Thread

If the thread continues the main line, the first useful outputs should be:

- a new bounded skill spec for `a2-lev-autodev-loop-audit-operator`
- the new skill module
- registry row
- dispatch binding
- smoke test
- repo-held report + packet
- synchronized updates to:
  - front-door corpus/tracker/backlog/plan surfaces
  - standing A2 truth surfaces if the landing changes control truth
  - graph audit if live skill count changes

## Stop Conditions

Stop and report instead of widening claims if:

- the new slice needs imported runtime ownership to make sense
- the new slice depends on cron/background automation claims
- the new slice would force lev runtime import instead of bounded audit
- graph/registry/A2 truth drifts during the tranche

## Non-Goals

- do not restart EverMem as a main-line build
- do not reopen the lev builder/formalization lane
- do not widen the next-state lane into online learning
- do not rely on hidden thread memory
