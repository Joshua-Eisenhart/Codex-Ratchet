# WORK_SYSTEM_V3_QUARANTINE_REVIEW__2026_03_10__v1

Status: DRAFT / NONCANON / A2 CONTROL NOTE
Date: 2026-03-10
Role: bounded quarantine-prep review of `work/system_v3`

## 1) Current shape

Current size:
- `136M` total

Main concentration:
- `117M` `work/system_v3/runs`
- `11M` `work/system_v3/runtime`

Largest run subtargets:
- `93M` `WIGGLE_AUTO_001`
- `12M` `TEST_REFINED_050`
- `6.2M` `TEST_REFINED_001`
- `4.4M` `_CURRENT_STATE`

## 2) Structural classification

`work/system_v3` is not an active owner path.

Best current read:
- shadow / mirrored `system_v3` tree
- legacy/test/prototype spillover
- migration-debt evidence
- useful as archaeology/reference, not as current authority

This aligns with existing A2 intake/controller surfaces that already treat:
- `work/system_v3`
- its alias duplicates
- its runtime/tool mirrors
as shadow-system residue rather than active control law

## 3) Why no direct mutation now

No direct quarantine/archive move is justified yet.

Reason:
- many existing archaeology/source-map batch artifacts still point at exact `work/system_v3/...` paths
- moving the subtree now would break path continuity for those already-recorded source families
- the path is conceptually quarantinable, but operationally still serves as readable evidence

## 4) Exact keep vs quarantine read

### Keep-in-place for now
- the whole `work/system_v3` subtree as readable archaeology/reference

### Quarantine-read classification
- treat the subtree as:
  - non-owner
  - non-runtime-authority
  - migration/shadow residue

This is a semantic quarantine now, not a filesystem move yet.

## 5) Strongest next safe move

Do not move `work/system_v3` yet.

Instead, if further cleanup is needed, run one narrower nonbreaking investigation of:
- `work/system_v3/runs/WIGGLE_AUTO_001`
- `work/system_v3/runs/TEST_REFINED_050`
- `work/system_v3/runs/TEST_REFINED_001`

Goal:
- determine whether those specific mirrored run surfaces can be archived with preserved path evidence elsewhere

## 6) Decision

Decision: `CORRECT_LANE_LATER`

Meaning:
- the subtree is correctly classified as shadow residue now
- but direct filesystem quarantine should wait for a path-preserving strategy or a narrower mirrored-run sublane
