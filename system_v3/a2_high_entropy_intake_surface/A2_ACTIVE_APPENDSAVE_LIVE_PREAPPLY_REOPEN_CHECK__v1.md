# A2_ACTIVE_APPENDSAVE_LIVE_PREAPPLY_REOPEN_CHECK__v1
Status: PROPOSED / NONCANONICAL / REOPEN CHECK ONLY
Date: 2026-03-09
Role: Live pre-apply reopen check across the four active-A2 target surfaces immediately before any authorized mutation pass
Reopen-check batch id: `BATCH_A2MID_PROMOTION_active_a2_live_preapply_reopen_check_01__v1`

## 1) Scope
This note does not mutate active A2.

It re-opens the current live targets for:
- `A2_ACTIVE_APPENDSAVE_STEP1_PATCH_PREVIEW__v1.md`
- `A2_ACTIVE_APPENDSAVE_STEP2_PATCH_PREVIEW__v1.md`
- `A2_ACTIVE_APPENDSAVE_STEP3_PATCH_PREVIEW__v1.md`
- `A2_ACTIVE_APPENDSAVE_STEP4_PATCH_PREVIEW__v1.md`
- `A2_ACTIVE_APPENDSAVE_STEP5_PATCH_PREVIEW__v1.md`
- `A2_ACTIVE_APPENDSAVE_STEP6_PATCH_PREVIEW__v1.md`
- `A2_ACTIVE_APPENDSAVE_STEP7_PATCH_PREVIEW__v1.md`

against the current live shapes of:
- `system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
- `system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md`
- `system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
- `system_v3/a2_state/OPEN_UNRESOLVED__v1.md`

This is not an authorization and not an apply pass.

## 2) Current Live Hashes
- `system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
  - `cc7ecf1dc4a35c59fbf17730248b30f4cac698792a615b62432f7c97f3c603e3`
- `system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md`
  - `4072819a7bb564490ad0b489f0c0561a9b6c47493773231e3c406be4daed9097`
- `system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
  - `9d5c6d8e03cc51cd70a6b6538fe4de4320fb5f5056b8f58869166153b108abd4`
- `system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
  - `01689f78861e46601bc57dd1f136f5a791473da46c17a17c56080352bc427704`

## 3) Current Live Anchor Confirmation

### Step 1
Target:
- `system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`

Live confirmation:
- terminal section `## 2026-03-09 archive demotion after witness normalization` is still present
- the terminal line `local retention should now prefer a small active/anchor set rather than keeping every cited family run locally` is still present

Status:
- `READY_ON_CURRENT_LIVE_SHAPE`

### Step 2
Target:
- `system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md`

Live confirmation:
- terminal section `## 13) Thread weighting vs recency` is still present
- terminal `Main source:` block still ends with `/home/ratchet/Desktop/codex thread save.txt`

Status:
- `READY_ON_CURRENT_LIVE_SHAPE`

### Step 3
Target:
- `system_v3/a2_state/OPEN_UNRESOLVED__v1.md`

Live confirmation:
- worldview-pressure local anchor still appears as:
  - `the A2-2 -> A2-1 boundary rule is now explicit, but the current kernel surfaces still leak too much worldview/overlay pressure downward and need gradual tightening rather than wholesale rewrite`
  - followed immediately by:
    `scaffold-mode/runtime-debug work still needs recurring audit so it does not outrun the corrected A2-first sequence`

Status:
- `READY_ON_CURRENT_LIVE_SHAPE`

### Step 5
Target:
- `system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`

Live confirmation:
- terminal section `## Landing-Pressure Rule For Richer Terms (2026-03-08)` is still present
- the two tail control-implication lines still match the current preview anchor

Status:
- `READY_ON_CURRENT_LIVE_SHAPE`

### Step 7
Target:
- `system_v3/a2_state/OPEN_UNRESOLVED__v1.md`

Live confirmation:
- sims/interface predecessor cluster is still present exactly as previewed:
  - `SIDECAR_EVIDENCE_RECONCILIATION_DEFERRED`
  - `THREAD_B_DEPENDENT_CONTRACT_REMAINDER`
  - `PARTIAL_EVIDENCE_PACK_COVERAGE`
  - thread-local command vocabulary, filename/runbook theory overreach, leading-space/cache hygiene residue, and cross-axis causal overread remain quarantined

Status:
- `READY_ON_CURRENT_LIVE_SHAPE`

## 4) Dependency-Bound Step Confirmation

### Step 4
Target:
- `system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`

Current condition:
- the current pre-Step-1 hash still matches the Step 1 / Step 4 / Step 6 preview family
- the required Step 4 predecessor block does not yet exist on the live file because Step 1 has not been applied

Status:
- `DEPENDENCY_READY_NOT_DIRECTLY_APPLICABLE_YET`

Meaning:
- if Step 1 is applied exactly, Step 4 should then be re-opened against the new predecessor block before apply

### Step 6
Target:
- `system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`

Current condition:
- the current pre-Step-1 hash still matches the Step 1 / Step 4 / Step 6 preview family
- the required Step 6 predecessor block does not yet exist on the live file because Steps 1 and 4 have not been applied

Status:
- `DEPENDENCY_READY_NOT_DIRECTLY_APPLICABLE_YET`

Meaning:
- if Steps 1 and 4 are applied exactly, Step 6 should then be re-opened against the new predecessor block before apply

## 5) Pre-Apply Verdict
Current verdict:
- `SAFE_TO_BEGIN_AUTHORIZED_SEQUENCE_IF_EXECUTED_IMMEDIATELY`

Reason:
- all current-hash-bound previews still match their live targets
- the dependency-bound previews remain consistent with the unchanged pre-Step-1 understanding file
- no new anchor loss or hash drift was observed during this reopen check

## 6) Apply Discipline If Authorization Is Later Given
If an authorized mutation pass begins later:
1. start with Step 1 and follow the existing execution-map order exactly
2. re-open each target immediately before each step lands
3. for Steps 4 and 6, require the exact predecessor block, not just the old pre-apply hash
4. stop immediately if any hash or local anchor drifts from these reopened assumptions
