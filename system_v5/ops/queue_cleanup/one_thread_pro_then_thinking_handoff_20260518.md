# One-Thread Pro → Thinking Relay Handoff — 20260518

Status: temporary coordination doc
Scope: Issue #2 follow-up after commit `0836e3306 docs: checkpoint sim lane authority`
Cleanup: remove this doc after its instructions are consumed into a committed repair-batch result or Issue #2 status comment.

## Purpose

Use exactly one Pro thread for reasoning and exactly one Thinking/write-capable follow-up for repo posting.

The Pro output must contain all payload needed for the Thinking relay. The Thinking relay must not need to understand the repo, infer missing fields, choose paths, or rewrite the work. It only posts the prebuilt relay payload.

This replaces the A-F fanout pattern.

## Inputs Pro Must Read

- Issue #2: `v5 sim cleanup and integration: lane authority, receipts, and macro-attractor spine`
- `system_v5/ops/queue_cleanup/sim_lane_blocker_report_20260518.md`
- `system_v5/ops/queue_cleanup/sim_lane_authority_manifest_20260518.md`
- `system_v5/docs/plans/v5_macro_attractor_spine_20260518.md`
- `system_v5/ops/queue_cleanup/small_repair_batch_candidates_20260518.md`
- `system_v5/legos/README.md`
- Any relevant committed files named by the small repair batch candidates.

## Hard Boundaries

- Pro browser thread does not run sims.
- Pro browser thread does not edit files.
- Do not edit sim source.
- Do not edit result JSON.
- Do not edit queues.
- Do not move/delete files.
- Do not promote Grok output.
- Do not treat NumPy as load-bearing nonclassical substrate.
- Do not claim macro-attractor convergence.
- Prefer fewer safe fixes over broad ambiguous work.

## What Pro Must Produce

Pro must produce exactly one fenced relay payload and nothing after the end fence.

The payload itself must already be a complete Issue #2 comment. It must include:

1. `THREAD_RESULT` header;
2. status;
3. inspected paths;
4. one concrete local-Codex job;
5. exact read paths;
6. exact allowed write paths;
7. exact validator commands;
8. stop conditions;
9. commit rules;
10. explicit non-goals.

The selected local-Codex job should contain 2–4 tightly scoped fixes:

1. one lane-authority fix;
2. one NumPy quarantine / tool-role fix;
3. one v5 nonclassical PyTorch confirmation;
4. one Grok quarantine row, only if safe.

If 3–4 are not safe, choose fewer. If none are safe, return `STATUS: blocked` with the reason.

## Required Pro Output Format

```text
ISSUE_COMMENT_PAYLOAD_BEGIN
THREAD_RESULT: PRO_SINGLE_REPAIR_BATCH_SELECTOR_20260518
ROLE: one-thread repair-batch selector
STATUS: complete|blocked
WRITE_TARGET: issue-comment
OUTPUT_DOC_PATH: none
INSPECTED_PATHS:
- Issue #2
- system_v5/ops/queue_cleanup/sim_lane_blocker_report_20260518.md
- system_v5/ops/queue_cleanup/sim_lane_authority_manifest_20260518.md
- system_v5/docs/plans/v5_macro_attractor_spine_20260518.md
- system_v5/ops/queue_cleanup/small_repair_batch_candidates_20260518.md
- system_v5/legos/README.md
CHANGED_PATHS:
- none
NEXT_CONSUMER: Codex App/TUI

## Local Codex job

<complete local Codex/TUI handoff; no missing fields>

## Exact read paths

- <paths>

## Allowed write paths

- <paths or none>

## Validators / commands to run

```bash
<commands>
```

## Stop conditions

- <conditions>

## Commit rules

- <rules>

## Explicit non-goals

- <non-goals>

ISSUE_COMMENT_PAYLOAD_END
```

Important: the output is not a Pro handoff block anymore. It is the exact Issue #2 comment payload.

## One Short Pro Prompt to Paste

```text
You are Pro working in one thread only for Codex-Ratchet Issue #2.

Read and follow this repo handoff doc:
`system_v5/ops/queue_cleanup/one_thread_pro_then_thinking_handoff_20260518.md`

Task:
Use the committed authority docs from commit `0836e3306` to choose one tiny foundation-level local-Codex repair batch. Do not run sims, do not edit files, and do not broaden into fanout. Prefer a 2–4 item batch: lane-authority fix, NumPy/tool-role fix, v5 nonclassical PyTorch confirmation, and Grok quarantine row only if safe.

Output exactly one fenced block between `ISSUE_COMMENT_PAYLOAD_BEGIN` and `ISSUE_COMMENT_PAYLOAD_END`. The block must already be the complete Issue #2 comment payload. Nothing before or after the block except a single sentence saying whether the payload is complete or blocked.
```

## Tiny Thinking Relay Prompt

After Pro finishes, switch to Thinking/write-capable mode and paste only this:

```text
Post the immediately preceding `ISSUE_COMMENT_PAYLOAD_BEGIN` / `ISSUE_COMMENT_PAYLOAD_END` block to GitHub Issue #2 in Joshua-Eisenhart/Codex-Ratchet as a top-level comment. Remove the begin/end fence lines only. Do not rewrite, summarize, interpret, or add content. If the block is missing, output only `BLOCKED_BY_MISSING_ISSUE_COMMENT_PAYLOAD`. If repo write is unavailable, output only `BLOCKED_BY_NO_REPO_WRITE_TOOL`.
```

That is the entire Thinking prompt. All substantive content must already be inside the Pro-produced payload.

## Local Codex Cleanup Rule

After the selected repair batch is completed and committed, local Codex should remove this temporary coordination doc unless it is still actively needed:

```bash
git rm system_v5/ops/queue_cleanup/one_thread_pro_then_thinking_handoff_20260518.md
git commit -m "chore: remove consumed one-thread handoff"
```

Do not delete it before the repair-batch result has been posted to Issue #2 or committed in a durable doc.
