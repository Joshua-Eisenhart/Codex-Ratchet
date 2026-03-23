# A2_UPDATE_NOTE__A1_FAMILY_SLICE_TO_LAUNCH_BUNDLE_WRAPPER__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the first one-shot wrapper that takes a bounded A2 family slice all the way to a ready A1 launch bundle

## Scope

New wrapper:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/prepare_a1_launch_bundle_from_family_slice.py`

Focused regression:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_launch_bundle_from_family_slice.py`

Companion doc touch-ups:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/34_A1_READY_PACKET__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md`

Concrete generated bundle:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/launch_bundle__substrate_base_scaffold__2026_03_15__v1/A1_WORKER_LAUNCH_PACKET__A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE__2026_03_15__v1.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/launch_bundle__substrate_base_scaffold__2026_03_15__v1/A1_WORKER_LAUNCH_PACKET__A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE__2026_03_15__v1__GATE_RESULT.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/launch_bundle__substrate_base_scaffold__2026_03_15__v1/A1_WORKER_LAUNCH_PACKET__A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE__2026_03_15__v1__SEND_TEXT.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/launch_bundle__substrate_base_scaffold__2026_03_15__v1/A1_WORKER_LAUNCH_PACKET__A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE__2026_03_15__v1__HANDOFF.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/launch_bundle__substrate_base_scaffold__2026_03_15__v1/A1_WORKER_LAUNCH_PACKET__A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE__2026_03_15__v1__BUNDLE_RESULT.json`

## Problem

After the family-slice compiler landed, the stack was still:
- family slice
- compiler command
- packet
- separate bundle preparation command

That was already better than ad hoc assembly, but it still left the common object-to-bundle path split across multiple commands.

## What changed

`prepare_a1_launch_bundle_from_family_slice.py` now:
- takes one family-slice JSON
- calls the family-slice compiler
- writes a deterministic packet JSON inside one output directory
- runs the standard Codex launch-bundle preparer on that compiled packet
- returns one small summary result with:
  - `packet_json`
  - `bundle_result_json`
  - `out_dir`
  - `status`

It does **not** invent a new launch format.
It is just a wrapper over:
- `build_a1_worker_launch_packet_from_family_slice.py`
- `prepare_codex_launch_bundle.py`

## Meaning

This is the first repo-held one-shot path for:
- bounded family slice
- ready A1 launch packet
- ready gate/send-text/handoff bundle

So the structured object path now reaches the same operational endpoint as the older manually assembled launch-packet path.

## Verification

Focused regression:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_worker_launch_packet_from_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_launch_bundle_from_family_slice.py`

Result:
- `Ran 3 tests ... OK`

Syntax:
- `python3 -m py_compile system_v3/tools/build_a1_worker_launch_packet_from_family_slice.py system_v3/tools/prepare_a1_launch_bundle_from_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_worker_launch_packet_from_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_prepare_a1_launch_bundle_from_family_slice.py`

Concrete sample bundle:
- `python3 system_v3/tools/prepare_a1_launch_bundle_from_family_slice.py --family-slice-json '/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json' --family-slice-schema-json '/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1.schema.json' --model 'GPT-5.4 Medium' --dispatch-id 'A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD_BUNDLE__2026_03_15__v1' --out-dir '/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/launch_bundle__substrate_base_scaffold__2026_03_15__v1'`

Observed result:
- wrapper returned `status: READY`
- bundle directory contains:
  - packet JSON
  - gate result
  - send text
  - handoff
  - bundle result
- bundle result status is `READY`

## Next seam

The next interesting question is policy, not plumbing:
- should family-slice-driven launch-bundle preparation now become the preferred controller path whenever a valid family slice exists

If yes, the next step is probably to retarget one active controller-facing launch note or workflow surface toward this object-driven path.
