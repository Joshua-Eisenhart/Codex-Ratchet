# A2_UPDATE_NOTE__A1_LIVE_PACKET_PROFILE_EXTRACT__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the first safe structural split step for `05` by adding a non-owner live packet/profile extract instead of immediately changing requirement ownership

## Scope

New non-owner extract:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md`

Supporting read surfaces updated:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/00_MANIFEST.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/02_OWNERSHIP_MAP.md`

Authority anchors:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_STRATEGY_v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/ENUM_REGISTRY_v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_REPAIR_OPERATOR_MAPPING_v1.md`

## Why this step

The repo had good reload guards now, but it still did not have one compact A1 read surface for:
- current live packet/profile shape
- live operator-law pointers
- the interpretation rule for mixed `05` / `18`

So future reads still had to bounce across several docs just to reconstruct the basic current A1 packet/profile path.

## What changed

### 1) Added a non-owner live packet/profile extract

Created:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md`

It is explicitly:
- `DRAFT / NONCANON`
- extract only
- non-owner

It provides a compact current read for:
- live operator law
- current A1 output surface
- current packet/profile highlights
- current summary/adjacency surfaces
- family/selector reading rule
- conflict resolution order

### 2) Wired it into the read surfaces

Updated:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/00_MANIFEST.md`
  - `A1 Reload Hygiene` now points to the new extract
  - `Active Process Supplements` now includes the extract
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/02_OWNERSHIP_MAP.md`
  - `Extract/Reference Docs (Non-Owners)` now includes the extract and clarifies authority stays in `05` plus the control-plane A1 strategy/operator specs

## Why this is the safe structural move

It improves the repo’s practical read shape without:
- moving requirement ownership
- pretending `05` is no longer the owner
- inventing a new operator doctrine
- flattening historical branch doctrine into the live packet path

So it is a real structural improvement, but still conservative about authority.

## Verification

Grounded checks:
- `rg -n "77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1|A1 Reload Hygiene|Extract/Reference Docs" system_v3/specs/00_MANIFEST.md system_v3/specs/02_OWNERSHIP_MAP.md system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md`
- `sed -n '1,220p' system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md`

These confirmed:
- the new extract exists
- manifest points to it
- ownership map classifies it as a non-owner reference surface

No runtime code changed in this step.

## Next seam

The structural decision is narrower now:
- keep `05` as owner and keep using `77` as the compact live extract
- or later promote a cleaner dedicated live packet/profile owner surface and re-home the relevant requirement text
