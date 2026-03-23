---
name: safe-run-maintenance
description: Perform archive-first, fail-closed maintenance for generated run and staging artifacts without deleting or touching active owner surfaces. Use when Codex needs to reduce workspace bloat, classify stale generated artifacts, move clearly safe items to archive or quarantine, enforce hard allowlists and denylists for unattended maintenance, or design/review safe maintenance automations for paths like system_v3/runs, work/to_send_to_pro, and mirrored non-owner work trees.
---

# Safe Run Maintenance

## Overview

Run bounded maintenance with hard safety gates. Prefer exact classification and move-only cleanup over broad temp sweeping or destructive deletion.

## Workflow

### 1. Confirm the task is maintenance-safe

Use this skill only for:
- archive-first cleanup
- stale generated-artifact reduction
- quarantine preparation
- maintenance automation design/review

Do not use this skill for:
- deletion
- active state mutation
- broad repo restructuring
- vague “clean up everything”

If the request is destructive, ambiguous, or touches active owner surfaces, stop and narrow the scope first.

### 2. Load the maintenance policy

Read:
- `references/allowlist-denylist.md`
- `references/loop-shape.md`

The maintenance policy outranks convenience.

### 3. Classify candidates exactly

For each candidate path, decide exactly one:
- `KEEP_ACTIVE`
- `MOVE_TO_ARCHIVE`
- `MOVE_TO_QUARANTINE`
- `BLOCKED_REQUIRES_PREP`

Never use freeform judgments like:
- “looks stale”
- “probably safe”
- “while we are here”

### 4. Respect hard defaults

Hard defaults:
- move-only, never delete
- no content rewrites during maintenance
- fail closed on ambiguity
- emit a report of every move
- do not infer stale from size alone
- do not touch active `system_v3/a2_state`, `system_v3/a1_state`, specs, runtime, or tools

### 5. Protect run state

Never move these from `system_v3/runs/`:
- `_CURRENT_STATE`
- `_CURRENT_RUN.txt`
- `_RUNS_REGISTRY.jsonl`

For run families:
- do not infer old/stale by name alone
- do not move anything unless a bounded prep note enumerates the exact set
- preserve anchor-dependent members that must remain live

### 6. Use freshness and activity blockers

Block maintenance when a candidate is:
- modified within the recent safety window
- explicitly referenced by a current control note
- clearly anchor-dependent
- named as active/current/live/latest
- part of a still-running or unresolved batch family
- drawn from a mixed path class without explicit prep

Default recent safety window:
- `72 hours`

### 7. Report clearly

Every maintenance pass should report:
- source path
- destination path
- exact decision
- reason
- blocked candidates
- intentionally kept items

### 8. Keep the loop bounded

For automation or live maintenance work:
- do one bounded sweep
- move only exact enumerated safe candidates
- emit one report
- stop

Do not chain maintenance waves automatically.

## References

Read only what is needed:
- `references/allowlist-denylist.md`
- `references/loop-shape.md`

## Resources

Use `references/` for the hard policy and the recommended loop shape. Keep the skill lean.
