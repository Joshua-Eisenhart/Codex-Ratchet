# PRO_THREAD_FIXED_LAUNCH_AND_ATTACHMENT_PROBE__2026_03_10__v1

Status: OPERATOR HANDOFF / NONCANON
Date: 2026-03-10
Role: corrected Pro-thread launch with hard attachment-access gate and explicit rebundle/download requirement

## Why the earlier launch failed

- The external thread did not actually gain readable access to the attached boot zip.
- Instead of stopping immediately on attachment failure, it generated a fail-closed shell package.
- That shell package is useful only as evidence of attachment failure, not as ratchet fuel.

## Corrected operating rule

Before any real extraction:
- the Pro thread must prove it can read the attached zip
- if it cannot, it must stop immediately with a short attachment failure report
- it must not generate the seven-file package on missing attachment access

After a successful read:
- it should produce the seven required `.out.md` files
- rebundle them into one downloadable zip
- provide the downloadable artifact link

## Exact file to attach

Attach this file only:

`/home/ratchet/Desktop/PRO_BOOT_JOB__ENTROPY_CARNOT_SZILARD__20260309_204341Z.zip`

## Exact launch text

```text
Use only the attached boot zip and the job's internal task contracts.

Hard preflight first:
1. Verify that you can actually read the attached zip.
2. If you cannot read it, stop immediately and return exactly:
   - ATTACHMENT_ACCESS_FAIL
   - one short reason
   - whether retrying the same upload is likely to help
3. If you can read it, first list the top-level files you can see inside the zip, then continue.

Do not generate a fail-closed seven-file package just because the attachment is missing or inaccessible.
Only generate the full output set if the zip is actually readable.

If readable, produce every required output file with exact file fences.
Preserve disagreements.
Keep citations/source locators.
Separate:
- process flow
- mathematical primitives
- ontology/worldview assumptions

Explicitly classify every major line as:
- usable now
- usable after retool
- reject / quarantine

Do not smooth.
Fail closed only on actual contract/content gaps inside the readable corpus, not on missing attachment access.

Required output files:
- SOURCE_AND_METHOD_MAP.out.md
- MATH_ASSUMPTION_AND_RETOOL_MAP.out.md
- RATCHET_FUEL_SELECTION_MATRIX.out.md
- PRO_THREAD_BOOT_AND_QUERY_PLAN.out.md
- INSTANT_AUDIT_BRIEF.out.md
- QUALITY_GATE_REPORT.out.md
- PORTABLE_OUTPUT_CONTRACT_AND_FAIL_CLOSED_VALIDATION.out.md

After creating those files:
1. rebundle them into one zip
2. provide the downloadable zip
3. briefly list the filenames contained in that returned zip
```

## Operator use

Recommended next step:
- run one corrected Pro thread first as an attachment-access proof
- only if that works, run the other bounded Pro lanes

## Summary

The immediate problem is attachment access, not domain reasoning quality.
Fix that first, then rerun the real lane.
