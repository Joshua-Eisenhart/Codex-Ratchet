# Claude Code Dangerous Mode Policy

Status: working policy
Purpose: define a formal policy for using Claude Code when dangerous mode / broad permissions are enabled

This is not a casual note.
This is a required operating policy.

If Claude Code is running with dangerous mode or broad permissions, then every handoff must be treated as a high-risk execution contract.

---

## 1. Core rule

If Claude Code has dangerous permissions, the handoff prompt is part of the safety boundary.

That means:
- vague prompts are unsafe
- broad prompts are unsafe
- open-ended cleanup prompts are unsafe
- repo-wide mutation prompts are unsafe
- exploratory prompts without stop rules are unsafe

A dangerous-mode handoff must be bounded, explicit, conservative, and auditable.

---

## 2. Why this matters

Dangerous mode increases the risk of:
- broad unintended file changes
- destructive cleanup
- overreach outside task scope
- changing architecture when only a local fix was intended
- silently mutating configs, paths, or docs
- deleting things that should only be archived
- replacing open scientific questions with implementation shortcuts

So dangerous mode raises the required quality of the handoff.

---

## 3. Default operating stance

When using Claude Code in dangerous mode, assume:
- it may do too much unless constrained
- it may infer permission you did not intend
- it may optimize for completion rather than minimal safe change
- it may broaden scope unless explicitly fenced

Therefore the correct default is:
- bounded task only
- conservative mode
- minimal change bias
- explicit non-goals
- explicit stop rule
- explicit validation rule

---

## 4. Required sections for every dangerous-mode handoff

Every dangerous-mode handoff must include all of the following:

1. `Goal`
- one bounded objective only

2. `Context`
- only the context needed for that bounded objective

3. `Inspect first`
- exact files/modules to read before acting

4. `Allowed changes`
- exact classes of changes that are permitted

5. `Non-goals`
- explicit list of what must not be touched

6. `Required validation`
- exact tests/commands/checks to run
- use exact interpreter path (e.g. `/opt/homebrew/bin/python3`) when the repo has multiple Python environments; never use bare `python` or `python3`

7. `Required outputs`
- what file(s) or note(s) it must leave behind

8. `Stop rule`
- when to stop instead of continuing or widening scope

Without these sections, the handoff is incomplete.

---

## 5. Mandatory dangerous-mode restrictions

A dangerous-mode handoff must explicitly forbid broad unsafe actions unless the task specifically requires them.

Default forbidden actions:
- no repo-wide cleanup
- no mass file moves
- no mass deletions
- no dependency churn
- no renaming broad directory structures
- no replacing one architecture with another
- no speculative simplification of scientific structure
- no changing active doctrine docs unless directly asked
- no deleting historical material instead of flagging it

If one of these actions is actually needed, it must be named explicitly as allowed.

---

## 6. Dangerous-mode handoff quality rules

### 6.1 One task only
A dangerous-mode handoff should not bundle multiple unrelated goals.

### 6.2 Conservative by default
The handoff should instruct Claude to prefer the smallest bounded fix.

### 6.3 No hidden authority
Claude Code must not be allowed to decide doctrine, promotion, or scientific closure on its own.

### 6.4 Respect open structure
If bridge/cut/kernel or other scientific layers are open, the handoff must not allow Claude to close them narratively or structurally without explicit evidence.

### 6.5 Auditability required
The work must leave enough evidence in the repo to be reviewed by Hermes later.

---

## 7. Safe language patterns for handoffs

Good phrases:
- "execute conservatively"
- "implement the smallest bounded fix"
- "do not broad-refactor unrelated modules"
- "preserve current architecture as much as possible"
- "if blocked, stop and report the blocker"
- "do not overreach beyond the files listed"
- "do not convert this into a cleanup or redesign task"

Bad phrases:
- "clean this up"
- "make it better"
- "fix the repo"
- "refactor as needed"
- "organize this whole area"
- "improve the architecture"
- "handle anything related while you're there"

---

## 8. Review requirement

Every dangerous-mode handoff should require a short review note in the repo after execution.

The review note should say:
- what changed
- which files changed
- what validation ran
- what remains broken or open
- whether the task is complete or needs a follow-up handoff

This is mandatory because dangerous mode needs post-execution auditability.

---

## 9. Relation to repo-mediated workflow

This policy extends the repo-mediated multi-agent workflow.

Repo-mediated handoffs are useful in general.
Dangerous-mode handoffs are the stricter subclass.

So the handoff system should assume:
- normal handoffs exist
- dangerous-mode handoffs require tighter bounds and stronger explicit fences

---

## 10. Relation to Hermes

Hermes should remain the boss/orchestrator.

Hermes should:
- write dangerous-mode handoffs carefully
- keep them bounded
- review repo state afterward
- decide whether another bounded handoff is needed

Claude Code should not become the authority layer just because it has dangerous permissions.

---

## 11. Minimal dangerous-mode handoff template

A dangerous-mode handoff must include at least:

```md
# Task ID: ...
Date: ...
Issued by: Hermes
Target worker: Claude Code
Status: active
Mode: dangerous

## Goal
<one bounded objective>

## Context
<only relevant context>

## Inspect first
- ...
- ...

## Allowed changes
- ...
- ...

## Non-goals
- ...
- ...

## Required validation
- <exact command with full interpreter path when Python environment matters>
- do not use bare `python` or `python3` when the repo has multiple relevant interpreters

## Required outputs
- code changes in repo
- short review note in `.agent/reviews/active/...`

## Stop rule
Stop when the bounded task is complete or when a blocker requires a new handoff.
```

---

## 12. Current best summary

If Claude Code is in dangerous mode, handoffs are part of the safety system.

So they must be:
- explicit
- narrow
- conservative
- reviewable
- self-limiting

Dangerous mode is acceptable only if the handoff quality rises to match the risk.
