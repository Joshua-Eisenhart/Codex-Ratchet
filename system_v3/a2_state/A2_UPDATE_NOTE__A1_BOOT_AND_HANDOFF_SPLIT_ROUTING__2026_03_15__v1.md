# A2_UPDATE_NOTE__A1_BOOT_AND_HANDOFF_SPLIT_ROUTING__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the boot/handoff routing patch that makes new A1/controller starts point at the clean live/historical split instead of discovering it late

## Scope

Patched active procedure surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/30_A2_TO_A1_HANDOFF_CONTRACT__v1.md`

Supporting split surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md`

## Problem

The repo already had the cleaner split surfaces `77` and `78`, but the actual A1 start surfaces still did not point to them.

That meant a future A1 or controller boot could still start from:
- mixed owner docs
- mixed historical/live interpretation

and only discover the better split later.

## What changed

### 1) `31_A1_THREAD_BOOT__v1.md`

Added:
- `Reload hygiene` section near the top

It now says explicitly:
- use `77` for the current live A1 packet/profile path
- use `78` for historical branch/wiggle doctrine
- read mixed owner docs like `05` and `18` through that split

Also added both `77` and `78` to the companion surfaces list.

### 2) `30_A2_TO_A1_HANDOFF_CONTRACT__v1.md`

Updated required A1 boot binding / working context so it now includes:
- `77` as current live packet/profile context
- `78` as historical branch/wiggle context when needed

## Meaning

This makes the split operational, not just archival.

The main A1 launch/handoff surfaces now route readers toward:
- one clean live A1 read
- one clean historical A1 read

instead of leaving that as an implicit lesson hidden deeper in the repo.

## Verification

Grounded checks:
- `rg -n "77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1|78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1|Reload hygiene|Historical branch/wiggle context" system_v3/specs/31_A1_THREAD_BOOT__v1.md system_v3/specs/30_A2_TO_A1_HANDOFF_CONTRACT__v1.md`
- `sed -n '1,70p' system_v3/specs/31_A1_THREAD_BOOT__v1.md`
- `sed -n '86,110p' system_v3/specs/30_A2_TO_A1_HANDOFF_CONTRACT__v1.md`

These confirmed:
- both boot/handoff surfaces now point to the split directly
- the new routing is visible near the start of those active procedure docs

No runtime code changed in this step.

## Next seam

At this point the A1 read-side reset is in a noticeably better shape:
- mixed owner docs still exist
- but the repo now offers and routes to cleaner live/historical split reads

The next good move is probably not more split scaffolding.
It is to pause and assess whether this read architecture is now good enough before taking on riskier ownership re-homing.
