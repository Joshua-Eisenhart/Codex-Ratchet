# A2_UPDATE_NOTE__A1_FIRST_DISPATCH_EXAMPLE_RELOAD_REFRESH__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve that the first-dispatch A1 worker launch example family was refreshed from the new reload-artifact packet shape instead of being left as an old-shape contradictory example

## Scope

Patched source example packet:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A1_WORKER_LAUNCH_PACKET__FIRST_DISPATCH_EXAMPLE__2026_03_11__v1.json`

Regenerated example outputs:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A1_WORKER_SEND_TEXT__FIRST_DISPATCH_EXAMPLE__2026_03_11__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A1_WORKER_LAUNCH_GATE_RESULT__FIRST_DISPATCH_EXAMPLE__2026_03_11__v1.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A1_WORKER_LAUNCH_HANDOFF__FIRST_DISPATCH_EXAMPLE__2026_03_11__v1.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A1_WORKER_SEND_TEXT__FIRST_DISPATCH_EXAMPLE__2026_03_11__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A1_WORKER_LAUNCH_GATE_RESULT__FIRST_DISPATCH_EXAMPLE__2026_03_11__v1.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/launch_bundles/a1_first_dispatch_example/A1_WORKER_LAUNCH_PACKET__FIRST_DISPATCH_EXAMPLE__2026_03_11__v1__HANDOFF.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/launch_bundles/a1_first_dispatch_example/A1_WORKER_LAUNCH_PACKET__FIRST_DISPATCH_EXAMPLE__2026_03_11__v1__BUNDLE_RESULT.json`

## What changed

The first-dispatch example packet now includes:
- `a1_reload_artifacts`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md`

Its `prompt_to_send` now explicitly names those reload artifacts too.

Then the downstream example outputs were regenerated from the real tools, so the example send text, gate result, handoff, and bundle copies all reflect the same new shape.

## Why this matters

Without this refresh, the repo would have:
- new A1 worker launch tooling that expects/propagates reload artifacts
- old example surfaces that still teach the pre-patch packet shape

That kind of example drift is exactly how future reloads get misrouted.

## Verification

Regeneration commands:
- `python3 system_v3/tools/build_a1_worker_send_text_from_packet.py --packet-json '/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A1_WORKER_LAUNCH_PACKET__FIRST_DISPATCH_EXAMPLE__2026_03_11__v1.json' --out-text '/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A1_WORKER_SEND_TEXT__FIRST_DISPATCH_EXAMPLE__2026_03_11__v1.md'`
- `python3 system_v3/tools/run_a1_worker_launch_from_packet.py --packet-json '/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A1_WORKER_LAUNCH_PACKET__FIRST_DISPATCH_EXAMPLE__2026_03_11__v1.json' --out-json '/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A1_WORKER_LAUNCH_GATE_RESULT__FIRST_DISPATCH_EXAMPLE__2026_03_11__v1.json'`
- `python3 system_v3/tools/build_a1_worker_launch_handoff.py --packet-json '/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A1_WORKER_LAUNCH_PACKET__FIRST_DISPATCH_EXAMPLE__2026_03_11__v1.json' --send-text '/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A1_WORKER_SEND_TEXT__FIRST_DISPATCH_EXAMPLE__2026_03_11__v1.md' --out-json '/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A1_WORKER_LAUNCH_HANDOFF__FIRST_DISPATCH_EXAMPLE__2026_03_11__v1.json'`
- `python3 system_v3/tools/prepare_codex_launch_bundle.py --packet-json '/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A1_WORKER_LAUNCH_PACKET__FIRST_DISPATCH_EXAMPLE__2026_03_11__v1.json' --out-dir '/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/launch_bundles/a1_first_dispatch_example'`

Grounded validation:
- `python3 system_v3/tools/validate_codex_thread_launch_handoff.py --launch-handoff-json '/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A1_WORKER_LAUNCH_HANDOFF__FIRST_DISPATCH_EXAMPLE__2026_03_11__v1.json'`

Result:
- handoff validation returned `valid: true`

## Next seam

If the repo still intends to retain the legacy wiggle-soak worker launch bundle as a historical surface, it should eventually be refreshed the same way or marked as pre-reload-artifact legacy shape so it cannot be mistaken for the current preferred launch packet shape.
