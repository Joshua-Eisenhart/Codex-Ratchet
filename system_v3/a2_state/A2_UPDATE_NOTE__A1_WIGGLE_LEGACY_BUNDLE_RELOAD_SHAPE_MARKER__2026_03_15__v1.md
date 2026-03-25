# A2_UPDATE_NOTE__A1_WIGGLE_LEGACY_BUNDLE_RELOAD_SHAPE_MARKER__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve that the retained wiggle-soak worker launch bundle is now explicitly marked as pre-`a1_reload_artifacts` legacy shape, so it cannot be mistaken for the current clean A1 worker packet pattern

## Scope

Patched note:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_WIGGLE_CONTROLLER_LAUNCH_NOTE__2026_03_15__v1.md`

## What changed

The `Legacy launch bundle` section now says plainly that the retained historical worker-launch packet/bundle:
- is not the preferred execution path
- predates the newer `a1_reload_artifacts` routing
- should not be copied forward as the current clean A1 worker packet shape unless refreshed through the current launch tools

## Why this matters

The repo now has:
- a cleaned worker launch packet shape with `a1_reload_artifacts`
- a retained historical wiggle worker bundle that still reflects the older wrapper era

Without this note, the historical bundle could still be mistaken for the current recommended launch-packet pattern.

## Verification

Grounded check:
- `rg -n "predate the newer `a1_reload_artifacts` launch-packet routing|historical bundle" system_v3/a2_state/A1_WIGGLE_CONTROLLER_LAUNCH_NOTE__2026_03_15__v1.md`

## Next seam

If the historical wiggle worker bundle ever needs to be retained as an actually runnable example again, it should be regenerated from the current launch tools instead of being left in older wrapper shape.
