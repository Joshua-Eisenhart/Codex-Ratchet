# Small Repair Batch Candidates — 20260518

## Boundary

This file is optional and candidate-only. It does not repair, run, edit, admit, or promote anything.

## PRO_F Intake Status

`PRO_F_REPAIR_BATCH_PICKER_20260518` is `MISSING_OR_MALFORMED` for this pass because it was not posted as a top-level comment beginning with `THREAD_RESULT:`.

A raw `PRO_HANDOFF_RESULT_BEGIN` comment exists, but the user asked to collect comments beginning with `THREAD_RESULT:`. Therefore the raw PRO_F body is not treated as an accepted thread result here.

## Consequence

No concrete repair batch is accepted from PRO_F in this pass.

The next valid small-batch picker should be reposted as:

```text
THREAD_RESULT: PRO_F_REPAIR_BATCH_PICKER_20260518
ROLE: Small repair batch picker
STATUS: complete
WRITE_TARGET: issue-comment
OUTPUT_DOC_PATH: none

<full usable body>
```

## Candidate Classes Still Allowed Later

When a valid `THREAD_RESULT` body exists, small repair candidates should be limited to:

1. `KEEP_CLASSICAL_BASELINE` rows where NumPy is baseline-only.
2. `KEEP_SEMICLASSICAL_BRIDGE` rows only if both bridge sides are explicit.
3. `KEEP_NONCLASSICAL` rows with local load-bearing PyTorch or other appropriate nonclassical core tool and no load-bearing NumPy.
4. `QUARANTINE_GROK_PROPOSAL` rows under `system_v5/grok_sim`.
5. `REPAIR_RESULT_LINK` rows where source/result stem and contract shape are exact enough to inspect without editing result JSON.

## Stop Conditions

- Do not use raw handoff comments as authority when the requested `THREAD_RESULT:` envelope is missing.
- Do not run sims.
- Do not edit sim source.
- Do not edit result JSON.
- Do not edit queues.
- Do not promote Grok/proposal material.
