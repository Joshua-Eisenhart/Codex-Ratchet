# Repo-Mediated Multi-Agent Workflow

Status: working workflow spec
Purpose: define a formal handoff system between Hermes, Claude Code, and other bounded workers using repo files as the shared medium instead of chat transcript replay

This workflow exists to:
- preserve main Hermes context
- let external agents do bounded work
- keep instructions versionable and inspectable
- avoid copy-paste loops as the primary coordination method
- keep the handoff system clean and self-pruning

---

## 1. Core rule

Agents coordinate through repo artifacts, not through long chat replay.

The repo is the handoff medium.
Chat is only for deciding what handoff artifact should be written next.

---

## 2. Roles

### Hermes
Primary role:
- planner
- bounded auditor
- handoff writer
- reviewer of repo state
- context-preserving orchestrator

Hermes should:
- create bounded task files
- define scope and non-goals
- specify acceptance criteria
- specify what artifacts should be emitted
- later inspect repo outputs and write the next handoff

### Claude Code
Primary role:
- bounded implementation worker
- deep code/editor pass
- conservative fixer/refactorer when told

Claude Code should:
- read a handoff file in the repo
- perform the bounded task
- leave results in the repo
- avoid broad overreach beyond the handoff

### Other workers/subagents
Primary role:
- bounded reconnaissance
- specific isolated task
- short-lived support work

---

## 3. Handoff directory layout

Use a stable structure inside the repo:

```text
.agent/
  handoffs/
    active/
    completed/
    archived/
  reviews/
    active/
    completed/
    archived/
  templates/
  state/
```

### Meaning
- `handoffs/active/` = tasks ready for another agent to execute now
- `handoffs/completed/` = completed handoffs with useful short summary still worth keeping nearby
- `handoffs/archived/` = old handoffs moved out of active circulation
- `reviews/` = follow-up review tasks or post-execution inspections
- `templates/` = reusable task templates
- `state/` = small current-state files if needed

---

## 4. Handoff lifecycle

A handoff should move through this lifecycle:

1. drafted
2. active
3. executed
4. reviewed
5. completed or archived

It should not remain in active indefinitely.

---

## 5. Cleanup rule

The handoff system should clean itself up after work is done.

That means:
- active handoffs are temporary
- completed handoffs are compacted or moved
- old handoffs are archived, not left in active folders
- no permanent giant transcript/log pile in the active repo surface

Important rule:
- do not preserve every ephemeral step forever
- preserve only what is needed for current continuity, audits, and important decision history
- if something is truly low-value and reproducible, it can be allowed to disappear after completion

This is a handoff system, not a museum of every keystroke.

---

## 6. Handoff file contract

Every handoff file should include:

- `Task ID`
- `Date`
- `Issued by`
- `Target worker`
- `Status`
- `Mode`
- `Goal`
- `Context`
- `Files to inspect first`
- `Allowed changes`
- `Required changes`
- `Non-goals`
- `Required validation`
- `Required outputs`
- `Stop rule`

Validation rule:
- handoffs should specify the exact interpreter/command path to use when the repo has multiple Python environments
- do not write ambiguous validation commands like bare `python3` when the canonical interpreter matters

Optional:
- `Related docs`
- `Known risks`
- `If blocked`

---

## 7. Minimal handoff template

```md
# Task ID: ...
Date: ...
Issued by: Hermes
Target worker: Claude Code
Status: active

## Goal
...

## Context
...

## Inspect first
- ...
- ...

## Required changes
- ...
- ...

## Non-goals
- ...
- ...

## Required validation
- ...

## Required outputs
- code changes in repo
- short summary note

## Stop rule
Stop when the bounded task is complete or when a blocker is reached that requires a new handoff.
```

---

## 8. Review file contract

A review file should include:
- what was attempted
- what changed
- what passed
- what failed
- whether the task is complete, blocked, or needs a follow-up handoff

Review files should be shorter than implementation handoffs.

---

## 9. What should be preserved vs cleaned up

### Preserve
- current active handoffs
- current active reviews
- important decision docs
- important continuity/handoff state
- final compact summaries of major completed tasks

### Do not preserve indefinitely in active area
- raw long transcripts
- every intermediate thought
- duplicate task files
- dead handoffs that were superseded
- low-value execution chatter

### Archive only when useful
- major completed handoffs
- historically important migration/fix tasks
- tasks whose outcome explains current architecture

---

## 10. Current recommended usage pattern

1. Hermes decides the next bounded task.
2. Hermes writes a handoff file into `.agent/handoffs/active/`.
3. Claude Code is told only to read and execute that file.
4. Claude works inside the repo and leaves changes/results in the repo.
5. Hermes later inspects repo state and writes either:
   - a review file
   - a follow-up handoff
   - or marks the handoff completed
6. Old handoffs get moved out of active.

---

## 11. Context-window preservation benefit

This workflow helps preserve main Hermes context because:
- the instruction state is stored in the repo
- execution results live in the repo
- Hermes does not need to carry long implementation context in chat memory
- only compact current state and next-task decisions need to stay in the live thread

---

## 12. Immediate rule for this repo

For now:
- use repo-mediated handoffs for Claude Code
- keep handoffs bounded
- avoid long raw work logs in active areas
- archive or discard low-value transient coordination after completion
- let Hermes inspect repo state directly instead of requiring full paste-back loops

---

## 13. Current best summary

The formal handoff system for this repo should be:
- file-based
- bounded
- versionable
- self-pruning
- light on permanent log accumulation
- strong on current task clarity

That is the cleanest way to coordinate Hermes, Claude Code, and later bounded workers without bloating context or the repo.
