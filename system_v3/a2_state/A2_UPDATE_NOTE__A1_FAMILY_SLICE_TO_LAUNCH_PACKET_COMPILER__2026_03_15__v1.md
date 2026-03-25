# A2_UPDATE_NOTE__A1_FAMILY_SLICE_TO_LAUNCH_PACKET_COMPILER__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the first concrete structured-object compiler seam where one bounded `A2_TO_A1_FAMILY_SLICE_v1` can now be compiled into one valid `A1_WORKER_LAUNCH_PACKET_v1`

## Scope

New compiler:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_a1_worker_launch_packet_from_family_slice.py`

Focused regression:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_worker_launch_packet_from_family_slice.py`

Companion doc touch-ups:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/32_A1_QUEUE_STATUS_SURFACE__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/34_A1_READY_PACKET__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md`

Concrete compiled sample artifacts:
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_PACKET__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_GATE_RESULT__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_SEND_TEXT__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.md`

Source structured object:
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1.schema.json`
- `/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`

## Problem

The repo already had:
- a bounded `A2_TO_A1_FAMILY_SLICE_v1` schema and sample
- a cleaned A1 worker launch packet path

But there was still no concrete compiler step between them.

That meant the family slice existed as doctrine/control structure, while actual A1 launch packets still depended on ad hoc packet assembly.

## What changed

### 1) New compiler

`build_a1_worker_launch_packet_from_family_slice.py` now:
- loads one family-slice JSON
- validates it against the draft family-slice schema
- requires a real dispatch id if the slice still carries `DRAFT_ONLY__NO_DISPATCH`
- compiles one normal `A1_WORKER_LAUNCH_PACKET_v1`

The compiled packet:
- uses the slice as the bounded campaign object
- carries default A1 reload artifacts:
  - `77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md`
  - `78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md`
- prepends the family-slice JSON itself into `source_a2_artifacts`
- builds a self-contained bounded prompt that includes:
  - boot
  - reload artifacts
  - family-slice path
  - source A2 artifacts
  - slice identity
  - required lanes
  - required negative classes
  - stop rule

Then it validates the compiled packet through the existing A1 packet validator and fails closed if the packet is not valid.

### 2) Launch-shape docs

`32_A1_QUEUE_STATUS_SURFACE__v1.md` now explicitly allows:
- bounded `A2_TO_A1_FAMILY_SLICE_v1` objects

inside `source_a2_artifacts`.

`34_A1_READY_PACKET__v1.md` now lists the new family-slice compiler among the current executable helpers.

`77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md` now says the live reset direction should prefer:
- explicit bounded A2 -> A1 family slices
- launch packets compiled directly from those family slices where available

## Meaning

This is the first real object-to-launch compiler seam on the A1 side.

It does **not** replace the launch packet path.
It replaces one layer of manual packet assembly above it.

So the stack is now more like:
- bounded family slice object
- compiler
- standard A1 worker launch packet
- standard gate/send-text/handoff tools

instead of:
- bounded family slice object
- manual repackaging by controller/operator memory
- standard A1 worker launch packet

## Verification

Focused regression:
- `python3 -m unittest system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_worker_launch_packet_from_family_slice.py`

Result:
- `Ran 2 tests ... OK`

The test locks:
- successful compilation from the draft substrate family slice when a real dispatch id is supplied
- default insertion of `77` / `78`
- family-slice path inclusion in `source_a2_artifacts`
- prompt visibility of the family-slice path and family constraints
- successful validation by the existing A1 packet validator
- failure when no real dispatch id is supplied for a draft-only slice

Syntax:
- `python3 -m py_compile system_v3/tools/build_a1_worker_launch_packet_from_family_slice.py system_v3/runtime/bootpack_b_kernel_v1/tests/test_build_a1_worker_launch_packet_from_family_slice.py`

Concrete sample generation:
- `python3 system_v3/tools/build_a1_worker_launch_packet_from_family_slice.py --family-slice-json '/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json' --family-slice-schema-json '/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1.schema.json' --model 'GPT-5.4 Medium' --dispatch-id 'A1_DISPATCH__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1' --out-json '/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_PACKET__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json'`
- `python3 system_v3/tools/run_a1_worker_launch_from_packet.py --packet-json '/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_PACKET__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json' --out-json '/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_GATE_RESULT__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json'`
- `python3 system_v3/tools/build_a1_worker_send_text_from_packet.py --packet-json '/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_PACKET__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json' --out-text '/home/ratchet/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_SEND_TEXT__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.md'`

Observed result:
- compiled packet is valid
- gate result is `LAUNCH_READY`
- send text exists and carries both reload artifacts plus the family-slice path

## Next seam

The next better move is not more launch-packet polishing.
It is deciding whether:
- this compiler should become the preferred path for new A1 ready packets whenever a family slice exists

and if yes:
- where the upstream controller-side object that feeds it should live
- whether a small `A1_READY_PACKET_FROM_FAMILY_SLICE` wrapper spec should be added, or whether the current family-slice + compiler + packet stack is already enough
