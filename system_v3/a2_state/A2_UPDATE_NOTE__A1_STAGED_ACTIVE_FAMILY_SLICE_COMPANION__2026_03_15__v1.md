# A2_UPDATE_NOTE__A1_STAGED_ACTIVE_FAMILY_SLICE_COMPANION__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the step where one bounded family-slice companion was promoted from draft space into `a2_state` as an active staged A2->A1 surface, while the live queue registry intentionally remained empty

## Scope

Promoted active staged companion:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json`

Active current queue companions:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.json`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_STATUS_PACKET__CURRENT__2026_03_15__v1.json`

Patched active read surfaces:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A1_QUEUE_STATUS__CURRENT__2026_03_16__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/32_A1_QUEUE_STATUS_SURFACE__v1.md`

## Admission/class read

The promoted family-slice companion should be read as:
- `DERIVED_A2`

It is:
- a bounded A2->A1 structured handoff object
- repo-held in active `a2_state`
- usable by launch/queue tooling

It is not yet:
- an admitted live queue candidate
- an earned state surface
- a proposal truth surface

## What changed

Before this step:
- the active current registry and queue packet existed in `a2_state`
- but the only concrete family-slice sample still lived under `work/audit_tmp/spec_object_drafts`

After this step:
- one bounded family-slice companion now also exists under `a2_state`
- the live current registry still remains empty
- the live current queue packet still remains `NO_WORK`

That means:
- the repo has one stable active family-slice companion path available for future admission
- but queue readiness still depends on explicit registry admission, not mere existence

## Verification

The promoted companion compiled cleanly through the live launch compiler:
- `python3 system_v3/tools/build_a1_worker_launch_packet_from_family_slice.py --family-slice-json '/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_FAMILY_SLICE__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json' --family-slice-schema-json '/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1.schema.json' --model 'GPT-5.4 Medium' --dispatch-id 'A1_DISPATCH__PROMOTED_SLICE_VERIFY__2026_03_15__v1' --out-json '/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/spec_object_drafts/A1_WORKER_LAUNCH_PACKET__PROMOTED_SLICE_VERIFY__2026_03_15__v1.json'`

Observed result:
- the promoted active family-slice companion compiles into a valid `A1_WORKER_LAUNCH_PACKET_v1`
- source paths now point at the `a2_state` family-slice companion instead of only the draft-space path

## Current control interpretation

Current live queue state should still be read as:
- `A1_QUEUE_STATUS: NO_WORK`

because:
- `A1_QUEUE_CANDIDATE_REGISTRY__CURRENT__2026_03_15__v1.json` is still empty
- staged companions do not affect live queue state until registry admission happens

## Next seam

The next real controller decision is whether to:
- keep the promoted family-slice companion staged-only
- or admit it into the live current candidate registry and deliberately move the current queue answer from `NO_WORK` to one ready path
