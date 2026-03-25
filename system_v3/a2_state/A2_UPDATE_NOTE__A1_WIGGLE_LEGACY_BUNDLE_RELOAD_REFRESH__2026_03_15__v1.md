# A2_UPDATE_NOTE__A1_WIGGLE_LEGACY_BUNDLE_RELOAD_REFRESH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve that the retained wiggle-soak worker launch bundle was refreshed into the newer reload-artifact packet envelope while remaining a historical wrapper path

## Scope

Patched packet:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_WORKER_LAUNCH_PACKET__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1.json`

Regenerated bundle outputs:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/launch_bundles/a1_wiggle_soak_controllerled/A1_WORKER_LAUNCH_PACKET__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1__SEND_TEXT.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/launch_bundles/a1_wiggle_soak_controllerled/A1_WORKER_LAUNCH_PACKET__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1__GATE_RESULT.json`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/launch_bundles/a1_wiggle_soak_controllerled/A1_WORKER_LAUNCH_PACKET__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1__HANDOFF.json`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/launch_bundles/a1_wiggle_soak_controllerled/A1_WORKER_LAUNCH_PACKET__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1__BUNDLE_RESULT.json`

Patched note:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_WIGGLE_CONTROLLER_LAUNCH_NOTE__2026_03_15__v1.md`

## What changed

The retained historical wiggle worker packet now carries:
- `a1_reload_artifacts`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md`

Its `prompt_to_send` now names those reload artifacts before the older companion wiggle surfaces.

Then the legacy bundle outputs were regenerated from the live launch tools so the retained historical wrapper stays internally consistent with the newer packet envelope.

The controller note was updated too: the bundle is still historical/non-preferred, but it no longer claims to predate the `a1_reload_artifacts` routing.

## Why this matters

Before this refresh, the repo had:
- a cleaned A1 worker launch envelope
- a cleaned first-dispatch example
- but a retained wiggle worker historical bundle still in older packet shape

That left one more reload trap where the wrapper-era bundle could silently teach a different launch envelope than the rest of the repo.

## Verification

Regeneration command:
- `python3 system_v3/tools/prepare_codex_launch_bundle.py --packet-json '/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A1_WORKER_LAUNCH_PACKET__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1.json' --out-dir '/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/launch_bundles/a1_wiggle_soak_controllerled'`

Grounded validation:
- `python3 system_v3/tools/validate_codex_thread_launch_handoff.py --launch-handoff-json '/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/launch_bundles/a1_wiggle_soak_controllerled/A1_WORKER_LAUNCH_PACKET__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1__HANDOFF.json'`

Result:
- handoff validation returned `valid: true`

Grounded content check:
- regenerated send text contains `a1_reload_artifacts:` plus both `77` and `78`

## Next seam

The A1 launch/read routing seam is now much cleaner.
The next better target is probably not more worker-packet hygiene; it is the spec-object/compiler side, especially making A2/controller outputs able to generate these cleaner launch packets from structured bounded objects instead of ad hoc assembly.
