# A2_UPDATE_NOTE__A1_RELOAD_HYGIENE_MANIFEST_PATCH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the manifest-level reload hygiene patch that keeps mixed A1 draft specs from being misread as the live operator law during future read passes

## Scope

Patched manifest:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/00_MANIFEST.md`

Directly related surfaces:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/ENUM_REGISTRY_v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_REPAIR_OPERATOR_MAPPING_v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_STRATEGY_v1.md`

## Problem

Even after retargeting the mixed A1 draft specs themselves, the main read spine still listed:
- `05_A1_STRATEGY_AND_REPAIR_SPEC.md`
- `18_A1_WIGGLE_EXECUTION_CONTRACT.md`

with no warning that parts of those docs are historical/legacy branch doctrine rather than live runtime/control law.

That meant a reload could still get tripped before even opening the files.

## What changed

`/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/00_MANIFEST.md`

Added a new section:
- `A1 Reload Hygiene`

It says:
- `05` and `18` remain in the read spine because they own requirement ranges
- sections explicitly labeled `Legacy` inside those files are historical draft doctrine
- the live A1 operator enum/mapping for the current runtime/control path comes from:
  - `ENUM_REGISTRY_v1.md`
  - `A1_REPAIR_OPERATOR_MAPPING_v1.md`
  - `A1_STRATEGY_v1.md`

## Meaning

This is not a new doctrine.

It is a read-order guard so future A2/A1 refreshes do not have to rediscover the same operator split by accident.

The manifest now helps enforce the correct interpretation earlier:
- requirement ownership still matters
- but ownership does not mean every subsection in a mixed draft spec is live runtime law

## Verification

Grounded check:
- `rg -n "A1 Reload Hygiene|ENUM_REGISTRY_v1|A1_REPAIR_OPERATOR_MAPPING_v1|A1_STRATEGY_v1" system_v3/specs/00_MANIFEST.md`

Result:
- the new manifest-level hygiene marker is present
- the live control-plane operator-law references are present

No runtime code changed in this step.

## Next seam

Best next move is to decide whether the repo should keep:
- one mixed `05_A1_STRATEGY_AND_REPAIR_SPEC.md`

or move to:
- one clearer live packet/profile owner surface
- plus one explicitly historical branch/wiggle draft surface
