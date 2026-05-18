# One-Thread Pro → Thinking Handoff — 20260518

Status: temporary coordination doc
Scope: Issue #2 follow-up after commit `0836e3306 docs: checkpoint sim lane authority`
Cleanup: remove this doc after its instructions are consumed into a committed repair-batch result or Issue #2 status comment.

## Purpose

Use one Pro thread for maximum useful reasoning/work selection, then one Thinking/write-capable follow-up to post the handoff result to Issue #2. Avoid multi-tab fanout unless the task is truly separable.

The prior A-F fanout was useful for authority scaffolding, but too much overhead. This protocol uses one thread to pick the next small foundation-level repair batch.

## Inputs to Read

The Pro worker should read:

- Issue #2: `v5 sim cleanup and integration: lane authority, receipts, and macro-attractor spine`
- `system_v5/ops/queue_cleanup/sim_lane_blocker_report_20260518.md`
- `system_v5/ops/queue_cleanup/sim_lane_authority_manifest_20260518.md`
- `system_v5/docs/plans/v5_macro_attractor_spine_20260518.md`
- `system_v5/ops/queue_cleanup/small_repair_batch_candidates_20260518.md`
- `system_v5/legos/README.md`
- Any relevant committed files named by the small repair batch candidates.

## Hard Boundaries

- Do not run sims in the Pro browser thread.
- Do not edit sim source.
- Do not edit result JSON.
- Do not edit queues.
- Do not move/delete files.
- Do not promote Grok output.
- Do not treat NumPy as load-bearing nonclassical substrate.
- Do not claim macro-attractor convergence.
- Keep this as a small foundation-level repair-batch selector and local-Codex handoff.

## Desired Output

The Pro worker should produce exactly one fenced handoff block. It should select one small, useful local-Codex job, not another fanout.

The selected job should contain 3–4 tightly scoped fixes:

1. one lane-authority fix;
2. one NumPy quarantine / tool-role fix;
3. one v5 nonclassical PyTorch confirmation;
4. one Grok quarantine row, only if safe.

The Pro worker may decide that only 2–3 are safe. It must prefer fewer safe fixes over a broader ambiguous batch.

## Required Pro Output Format

The Pro response must end with exactly one fenced block:

```text
PRO_HANDOFF_RESULT_BEGIN
THREAD_ID: PRO_SINGLE_REPAIR_BATCH_SELECTOR_20260518
ROLE: one-thread repair-batch selector
STATUS: complete|blocked
INSPECTED_PATHS:
- <repo path or Issue #2>
PROPOSED_OUTPUT_PATH: Issue #2 comment
CONFLICTS: <none-or-list>
STOP_CONDITIONS: <none-or-list>

## Local Codex job

<one concrete local Codex/TUI job, including exact read paths, exact candidate rows if known, exact write targets, exact validators, stop conditions, and commit rules>

## Expected changed files

- <path or none>

## Explicit non-goals

- <non-goals>

PRO_HANDOFF_RESULT_END
```

If the Pro worker cannot form a safe job from committed evidence, it must output the same fenced block with `STATUS: blocked` and a concise reason.

## Thinking Relay Prompt

After Pro finishes, switch to Thinking/write-capable mode in the same tab if possible and paste:

```text
You are the Thinking/write-capable relay for the immediately preceding Pro handoff.

Task:
Find the fenced block between `PRO_HANDOFF_RESULT_BEGIN` and `PRO_HANDOFF_RESULT_END`. Do not reinterpret it except to remove the fences. Post it directly to GitHub Issue #2 in Joshua-Eisenhart/Codex-Ratchet as a top-level comment with header:

THREAD_RESULT: PRO_SINGLE_REPAIR_BATCH_SELECTOR_20260518
ROLE: one-thread repair-batch selector
STATUS: <status from handoff>
WRITE_TARGET: issue-comment
OUTPUT_DOC_PATH: none

Rules:
- Do not edit sim source.
- Do not edit result JSON.
- Do not edit queues.
- Do not promote Grok output.
- Do not create repo files unless explicitly assigned.
- If you cannot write to Issue #2, output only `BLOCKED_BY_NO_REPO_WRITE_TOOL`.
- If the Pro handoff block is missing, output only `BLOCKED_BY_MISSING_PRO_OUTPUT`.
```

## One Short Pro Prompt to Paste

```text
You are Pro working in one thread only for Codex-Ratchet Issue #2.

Read and follow this repo handoff doc:
`system_v5/ops/queue_cleanup/one_thread_pro_then_thinking_handoff_20260518.md`

Task:
Use the committed authority docs from commit `0836e3306` to choose one tiny foundation-level local-Codex repair batch. Do not run sims, do not edit files, and do not broaden into fanout. Prefer a 3–4 item batch: lane-authority fix, NumPy/tool-role fix, v5 nonclassical PyTorch confirmation, and Grok quarantine row only if safe.

End with exactly one fenced block between `PRO_HANDOFF_RESULT_BEGIN` and `PRO_HANDOFF_RESULT_END` using the format required by the handoff doc. Nothing after the end fence.
```

## Local Codex Cleanup Rule

After the selected repair batch is completed and committed, local Codex should remove this temporary coordination doc unless it is still actively needed:

```bash
git rm system_v5/ops/queue_cleanup/one_thread_pro_then_thinking_handoff_20260518.md
git commit -m "chore: remove consumed one-thread handoff"
```

Do not delete it before the repair-batch result has been posted to Issue #2 or committed in a durable doc.