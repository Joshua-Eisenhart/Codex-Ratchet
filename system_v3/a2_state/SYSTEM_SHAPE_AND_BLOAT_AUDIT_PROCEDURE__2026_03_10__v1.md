# SYSTEM_SHAPE_AND_BLOAT_AUDIT_PROCEDURE__2026_03_10__v1

Status: DRAFT / NONCANON / A2 CONTROL NOTE
Date: 2026-03-10
Role: bounded operator procedure for system-shape classification, run-folder bloat mapping, and cleanup-candidate audit under caution

## 1) Purpose

This lane exists to:
- map the current system shape without flattening all surfaces into one cleanup class
- quantify the main local bloat zones
- produce a caution-classified cleanup candidate list
- avoid broad delete sweeps

This lane does **not** perform broad deletion.
It produces classification and mutation candidates only.

## 2) Current measured shape

Current local size map:
- `system_v3/runs`: `557M`
- `work`: `437M`
- `system_v3/a2_high_entropy_intake_surface`: `16M`
- `system_v3/a2_state`: `1.5M`

Current immediate directory counts:
- `system_v3/runs` immediate run dirs: `130`
- `work` immediate subdirs: `21`

Operational read:
- `runs/` and `work/` are the only currently material local bloat surfaces
- `a2_state/` is not the size problem
- the intake surface is moderate and should not be treated as generic bloat

## 3) Governing doctrine

Use the repo-shape classification rule already established in active surfaces:
- active system surface
- active low-touch/reference surface
- alias/migration scaffolding surface
- `work/` legacy/test/prototype spillover surface
- external archive/retention surface

And the cleanup-under-caution classes:
- active owner
- derived helper
- runtime evidence
- proposal only
- archive only
- unclear / investigate

Hard rules:
- classify before mutating
- archive or quarantine before delete when possible
- no deletion based only on age, annoyance, or size
- do not treat `work/`, aliases, active surfaces, and runtime evidence as interchangeable

## 4) Audit scope

Primary audit targets:
- `system_v3/runs/`
- `work/`
- active root classification references in `system_v3/`

Secondary references:
- `SYSTEM_V3_FULL_SURFACE_INTEGRATION_AUDIT__v1`
- `A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2`
- `07_A2_OPERATIONS_SPEC`
- `STAGED_EXECUTION_AND_CLEANUP_PLAN__2026_03_10__v1`

## 5) Required outputs

This lane must emit exactly:
- one `SYSTEM_SHAPE_OWNER_MAP`
- one `RUN_AND_WORK_BLOAT_MAP`
- one `CLEANUP_CANDIDATE_LIST__UNDER_CAUTION`
- one `NO_DELETE_WITHOUT_FOLLOWON` decision block

Every candidate must be classified as exactly one:
- keep
- archive
- quarantine
- investigate

No candidate should be marked `delete_now`.

## 6) Focus questions

1. Which current surfaces are active owners and must remain untouched except for bounded process/runtime reasons?
2. Which `runs/` subtrees are runtime evidence worth keeping versus legacy duplicate/helper spillover?
3. Which `work/` subtrees are still active ZIP/control/refinery authoring surfaces versus stale spillover?
4. Which surfaces are aliases or mirrors that should stop being treated like separate systems?
5. Which cleanup candidates can be safely prepared for archive/quarantine review later?

## 7) Initial high-suspicion zones

Review first:
- legacy thick run surfaces inside `system_v3/runs/`
- helper/duplicate save surfaces previously demoted in the lean save update
- stale `work/` spillover not tied to active ZIP/refinery/control use
- mirrored or duplicate descriptive surfaces competing with active owners

Do **not** infer from size alone that a surface is disposable.

## 8) Stop condition

Stop this lane after:
- one bounded owner map
- one bounded bloat map
- one caution-classified candidate list
- one explicit follow-on recommendation

Do not continue into archive mutation or deletion in the same pass.

## 9) Expected follow-on

If the audit is good, the next lane is:
- bounded archive/quarantine preparation for the clearest non-owner cleanup candidates

If the audit is unclear, the next lane is:
- narrower investigation of one ambiguous high-size surface
