# Claude Batch Handoff Process

Status: working process
Purpose: define how to prepare multiple bounded handoffs for fresh Claude Code terminals without losing safety or creating prompt sprawl

## 1. Core rule

A batch is a queue of independent bounded handoffs, not a single mega-prompt.

Each Claude terminal should receive exactly one active handoff file at a time.

## 2. Batch directory convention

Use:
- `.agent/handoffs/active/` for ready tasks
- `.agent/handoffs/completed/` for finished tasks
- `.agent/reviews/active/` for returned review notes

Optional naming pattern:
- `claude__NN__short_task_name.md`

## 3. Batch eligibility rules

Only batch tasks that are:
- bounded
- mostly independent
- low-conflict in touched files
- reviewable separately

Do not batch together tasks that:
- mutate the same files heavily
- depend on unresolved outputs from each other
- are broad cleanup/refactor tasks

## 4. Per-task requirements

Every task in a batch must include:
- exact interpreter/command paths for validation
- allowed changes
- non-goals
- stop rule
- required review note path

## 5. Launch pattern

For each fresh Claude terminal:
- start Claude in the repo
- give only a tiny prompt such as:
  - `Read .agent/handoffs/active/<file>.md and execute it conservatively.`

Do not paste long context if the repo handoff file already contains it.

## 6. Safety rule for dangerous mode

If Claude is running with dangerous mode or broad permissions:
- use one handoff per terminal
- do not give stacked tasks in one prompt
- prefer minimal-change tasks
- require review note output for every task

## 7. Hermes role

Hermes should:
- write the batch files
- ensure tasks are independent enough
- track which terminal got which task
- inspect the review notes and repo diff afterward
- move completed handoffs out of active

## 8. Minimal batch tracker format

A lightweight tracker can be kept in chat or later in repo state with:
- task file
- target Claude terminal
- status
- touched files
- follow-up needed

## 9. Current best summary

The safest way to use fresh Claude terminals in batches is:
- one bounded handoff file per terminal
- minimal launcher prompt
- explicit validation paths
- explicit review note requirement
- Hermes remains the coordinator
