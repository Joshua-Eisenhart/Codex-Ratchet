# A2_UPDATE_NOTE__A1_STRATEGY_SPEC_SECTION_STATUS_MAP__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the in-file section-status map added to `05_A1_STRATEGY_AND_REPAIR_SPEC.md` so future reloads can distinguish its live/profile-facing parts from its legacy branch-model parts without re-auditing the whole file

## Scope

Patched spec:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`

Related reset surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_OPERATOR_DOCTRINE_SPLIT_AND_POLICY_SOURCE__2026_03_15__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_LEGACY_OPERATOR_SPEC_RETARGET__2026_03_15__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__A1_RELOAD_HYGIENE_MANIFEST_PATCH__2026_03_15__v1.md`

## Problem

Even after adding legacy labels, `05_A1_STRATEGY_AND_REPAIR_SPEC.md` was still a mixed surface.

That meant a reader still had to infer:
- which parts were useful live packet/profile guidance
- which parts were historical branch/wiggle draft doctrine

That is exactly the kind of reload ambiguity that has been hurting this seam.

## What changed

Added `Section Status Map` near the top of:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`

It now explicitly classifies:

### Still-useful live/profile-facing sections
- `Role`
- `Anti-Classical Leakage`
- `Rosetta Function`
- `Rosetta: Cold-Core Extraction + Reattachment Dictionaries`
- `Mandatory Output`
- `Strategy Container Shape`
- `A1_STRATEGY_v1 Minimal Schema (Implementation-Facing)`
- `Strategy Contents`
- `Canon Boundary`
- `Fix-Intent Schema`

### Preserved historical branch/wiggle sections
- `Legacy Wiggle Model`
- `Legacy Branch Scheduler`
- `Legacy Novelty Floor`
- `Legacy Repair Loop Vocabulary`
- `Legacy Branch Lifecycle`
- `Legacy Stall Behavior`

## Meaning

This does not resolve the deeper structural choice yet.

It does make the mixed status of `05` visible inside the file itself, which is a meaningful reload improvement:
- readers can still use `05` for live packet/profile guidance
- without accidentally taking the branch/repair legacy sections as live runtime law

## Verification

Grounded checks:
- `rg -n "Section Status Map|Legacy Wiggle Model|Legacy Repair Loop Vocabulary|A1_STRATEGY_v1 Minimal Schema" system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`
- `sed -n '1,60p' system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`

These confirmed:
- the section-status map is present near the top
- the classified live/profile and legacy sections are visible in the file

No runtime code changed in this step.

## Next seam

The real structural decision still remains:
- keep `05` as a mixed owner doc with explicit status markers
- or split it into:
  - one cleaner live packet/profile owner surface
  - one explicitly historical branch/wiggle draft surface
