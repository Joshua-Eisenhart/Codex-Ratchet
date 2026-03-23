---
name: automation-controller
description: Design, review, or update safe recurring recurring automations for repo-grounded controller tasks such as return audits, queue checks, archive-first maintenance, Pro packet prep, monitoring, and inbox summaries. Use when the user asks to create an automation, schedule recurring work, reduce repeated "go on" operator steps, evaluate whether a task is suitable for unattended automation, or define safety rules, allowlists, deny-lists, stop rules, quarantine paths, and model-routing for recurring controller loops.
---

# Codex Automation Controller

## Overview

Design lean, safe recurring automation loops. Prefer controller, maintenance, audit, and packaging tasks over broad autonomous reasoning or destructive mutation.

## Workflow

### 1. Decide if the task is automation-suitable

Good fit:
- recurring controller checks
- quarantine-first return audits
- queue checks
- archive-first maintenance
- bounded packet preparation
- inbox summaries
- monitoring and classification

Bad fit:
- broad high-entropy refinery
- direct mutation of active brain/state surfaces
- deletion
- open-ended "keep going until it seems done"
- external `Pro` browser continuation by default

If the task is not a good fit, say so directly and recommend manual, live Codex, or bounded `Pro` work instead.

### 2. Choose one loop class only

Prefer one bounded loop per automation.

Current recommended loop classes:
- `RETURN_AUDIT_LOOP`
- `SAFE_MAINTENANCE_LOOP`
- `PRO_PACKET_PREP_LOOP`
- `QUEUE_CHECK_LOOP`
- `RUN_MONITOR_LOOP`
- `DISPATCH_RECOMMENDER_LOOP`

Do not combine several large loops into one automation unless the user explicitly wants a bundled controller job and the safety rules remain clear.

### 3. Define the safety contract before the schedule

For every automation, define:
- allowed input paths
- allowed output paths
- explicit denylist
- whether it is read-only, move-only, or write-limited
- stop rule
- fail-closed conditions

Hard defaults:
- archive-first, not delete-first
- quarantine-first for unattended `Pro` returns
- no direct unattended writes into active `system_v3/a2_state` or `system_v3/a1_state`
- no broad repo scans when a bounded path list exists
- always emit an inbox item or equivalent user-visible summary

### 4. Make the task self-contained

The automation prompt should describe only the task itself.
Do not put the schedule or workspace paths inside the prompt if the automation system already captures them separately.

Good prompt properties:
- one bounded role
- one bounded path set
- explicit output expectations
- explicit blockers
- explicit stop condition

Bad prompt properties:
- hidden context
- "read whatever seems relevant"
- "clean up the repo"
- "keep refining"

### 5. Prefer quarantine and staging paths

When unattended automation interacts with `Pro`, use:
- request staging
- return quarantine
- audit outputs
- staged-admission paths

If the repo is Codex Ratchet, prefer these working surfaces:
- `work/INBOX/GENERAL_TASK_PLAN__AUTOMATION_SKILLS_PRO_REFINERY__2026_03_13__v1.md`
- `work/INBOX/SAFE_MAINTENANCE_ALLOWLIST_DENYLIST__2026_03_13__v1.md`
- `work/INBOX/PRO_THREAD_PACKET_STANDARD__2026_03_13__v1.md`
- `work/INBOX/QUARANTINE_FOLDER_CONTRACT__2026_03_13__v1.md`
- `work/INBOX/RETURN_AUDIT_LOOP__DESIGN__2026_03_13__v1.md`
- `work/INBOX/SAFE_MAINTENANCE_LOOP__DESIGN__2026_03_13__v1.md`

### 6. Use a lean keep/retool/reject gate

Before proposing a new automation, ask:
- does it reduce operator burden?
- does it reduce drift?
- does it reduce risk?
- does it avoid adding new active surfaces?
- is it more reliable than handling this manually?

If not, reject or retool the automation idea rather than adding another loop.

## Output Requirements

When designing an automation, provide:
- loop class
- what it reads
- what it writes
- safety rules
- schedule recommendation
- stop rule
- user-visible result shape
- real blockers or reasons not to automate

If the user asked to create or update an app automation, emit the correct automation directive only after the task is safely specified.

## Scheduling Guidance

Prefer:
- every few hours for monitoring/audit/maintenance
- weekly for slower hygiene/reporting loops

Do not over-schedule first-wave automations.
Start slower and tighten later after the loop proves reliable.

## Guardrails

- Do not automate destructive actions by default.
- Do not automate direct active-memory writes by default.
- Do not use automation as a substitute for bounded packet design.
- Do not hide ambiguous ownership or path uncertainty behind generic summaries.
- Do not let one automation become a vague swarm controller.

## References

Read only what is needed:
- `references/loop-classes.md`
- `references/ratchet-safe-defaults.md`

## Resources

Use `references/` for loop classes and ratchet-safe defaults. Keep the core skill lean.
