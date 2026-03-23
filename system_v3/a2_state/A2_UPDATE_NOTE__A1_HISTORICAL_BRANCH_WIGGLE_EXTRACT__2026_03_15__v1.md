# A2_UPDATE_NOTE__A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the paired historical extract step that gives the repo both a clean live A1 read and a clean historical A1 branch/wiggle read

## Scope

New non-owner historical extract:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md`

Supporting read surfaces updated:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/00_MANIFEST.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/02_OWNERSHIP_MAP.md`

Source surfaces for the extract:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`

## Why this step

After adding the live packet/profile extract, the repo still had only one clean side of the split.

That meant:
- current live A1 read was cleaner
- but historical branch/wiggle doctrine still had to be reconstructed from mixed owner docs

So the repo still lacked a clean paired read:
- one live view
- one historical view

## What changed

### 1) Added a non-owner historical extract

Created:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md`

It is explicitly:
- `DRAFT / NONCANON`
- extract only
- non-owner
- historical draft doctrine only

It provides one compact read for:
- historical branch states
- historical branch object ideas
- historical operator/quota model from `18`
- historical scheduler and repair vocabulary from the legacy sections of `05`
- historical novelty / rebalance / graveyard emphasis
- explicit contrast with the live A1 read surface `77`

### 2) Wired it into the read surfaces

Updated:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/00_MANIFEST.md`
  - `A1 Reload Hygiene` now points to `78` for the historical branch/wiggle read
  - `Active Process Supplements` now includes `78`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/02_OWNERSHIP_MAP.md`
  - `Extract/Reference Docs (Non-Owners)` now includes `78`

## Meaning

The repo now has the missing pair:
- live A1 packet/profile read:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md`
- historical A1 branch/wiggle read:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md`

That is a real structural improvement over the previous state, because it reduces pressure on the mixed owner docs to serve both purposes at once.

## Verification

Grounded checks:
- `rg -n "78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1|A1 Reload Hygiene|Extract/Reference Docs" system_v3/specs/00_MANIFEST.md system_v3/specs/02_OWNERSHIP_MAP.md system_v3/specs/78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md`
- `sed -n '1,220p' system_v3/specs/78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md`

These confirmed:
- the historical extract exists
- manifest points to it
- ownership map classifies it as a non-owner reference surface

No runtime code changed in this step.

## Next seam

This reduces the structural choice further.

Now the plausible near-term posture is:
- keep `05` and `18` as owners
- keep `77` as the clean live packet/profile read
- keep `78` as the clean historical branch/wiggle read

Only after living with that should the repo decide whether full ownership re-homing is worth the churn.
