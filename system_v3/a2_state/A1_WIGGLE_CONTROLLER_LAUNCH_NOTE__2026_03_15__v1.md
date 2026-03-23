# A1_WIGGLE_CONTROLLER_LAUNCH_NOTE__2026_03_15__v1
Status: ACTIVE CONTROL NOTE / NONCANON
Date: 2026-03-15
Role: controller-facing launch memo for the bounded direct A1 graveyard-first control lane

## Current rule

The correct execution path is direct runtime control from this controller thread.

Do not treat the wiggle lane as a separate chat-authored `A1` worker by default.
The old launch packet / send-text / handoff bundle remains as a legacy wrapper surface only.

Primary executor:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_a1_wiggle_control_cycle.py`

## Legacy launch bundle

- launch packet:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A1_WORKER_LAUNCH_PACKET__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1.json`
- send text:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/launch_bundles/a1_wiggle_soak_controllerled/A1_WORKER_LAUNCH_PACKET__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1__SEND_TEXT.md`
- handoff:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/launch_bundles/a1_wiggle_soak_controllerled/A1_WORKER_LAUNCH_PACKET__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1__HANDOFF.json`

These are no longer the preferred execution path.
They are retained only as a repo-held historical bundle for the earlier chat-thread launch method.
They have been refreshed into the newer `a1_reload_artifacts` launch-packet envelope for reload hygiene, but they should still not be copied forward as the preferred current A1 execution path.

## Direct runtime commands

Initial run:

```bash
python3 /Users/joshuaeisenhart/Desktop/Codex\ Ratchet/system_v3/tools/run_a1_wiggle_control_cycle.py \
  --dispatch-id A1_DISPATCH__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1 \
  --run-id RUN_A1_WIGGLE_CONTROLLERLED_20260315_01 \
  --runs-root /Users/joshuaeisenhart/Desktop/Codex\ Ratchet/work/audit_tmp/a1_wiggle_controllerled_runs \
  --controller-result-json /Users/joshuaeisenhart/Desktop/Codex\ Ratchet/work/audit_tmp/thread_launch_returns/A1_DISPATCH__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1__A1_PROPOSAL__controller_result.json \
  --family-slice-json /Users/joshuaeisenhart/Desktop/Codex\ Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json \
  --go-on-budget 6 \
  --cycles 8 \
  --goal-profile refined_fuel \
  --goal-selection interleaved \
  --debate-strategy graveyard_first_then_recovery \
  --graveyard-fill-steps 8 \
  --clean
```

Continuation:

```bash
python3 /Users/joshuaeisenhart/Desktop/Codex\ Ratchet/system_v3/tools/run_a1_wiggle_control_cycle.py \
  --dispatch-id A1_DISPATCH__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1 \
  --run-id RUN_A1_WIGGLE_CONTROLLERLED_20260315_01 \
  --runs-root /Users/joshuaeisenhart/Desktop/Codex\ Ratchet/work/audit_tmp/a1_wiggle_controllerled_runs \
  --controller-result-json /Users/joshuaeisenhart/Desktop/Codex\ Ratchet/work/audit_tmp/thread_launch_returns/A1_DISPATCH__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1__A1_PROPOSAL__controller_result.json \
  --family-slice-json /Users/joshuaeisenhart/Desktop/Codex\ Ratchet/work/audit_tmp/spec_object_drafts/A2_TO_A1_FAMILY_SLICE_v1__SUBSTRATE_BASE_SCAFFOLD__2026_03_15__v1.json \
  --go-on-budget 6 \
  --cycles 8 \
  --goal-profile refined_fuel \
  --goal-selection interleaved \
  --debate-strategy graveyard_first_then_recovery \
  --graveyard-fill-steps 8 \
  --continue-run
```

## Fixed lane identity

- `dispatch_id: A1_DISPATCH__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1`
- `thread_class: A1_WORKER`
- `role_type: A1_PROPOSAL`
- `run_id: RUN_A1_WIGGLE_CONTROLLERLED_20260315_01`
- `runs_root: /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/a1_wiggle_controllerled_runs`
- `run_dir: /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/a1_wiggle_controllerled_runs/RUN_A1_WIGGLE_CONTROLLERLED_20260315_01`

## Repo-held result surfaces

- controller result packet:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_launch_returns/A1_DISPATCH__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1__A1_PROPOSAL__controller_result.json`
- cycle audit report:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/a1_wiggle_controllerled_runs/RUN_A1_WIGGLE_CONTROLLERLED_20260315_01/reports/a1_autoratchet_cycle_audit_report.json`
- campaign summary:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/a1_wiggle_controllerled_runs/RUN_A1_WIGGLE_CONTROLLERLED_20260315_01/campaign_summary.json`
- run summary:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/a1_wiggle_controllerled_runs/RUN_A1_WIGGLE_CONTROLLERLED_20260315_01/summary.json`

## Controller rule

The worker thread must treat the repo-held controller result packet as the authoritative return surface.
It should not paste long logs or summaries back into chat.

This controller thread can decide the next action by reading:
- the controller result packet first
- then the cycle audit report and campaign summary if needed

## Family-slice rule

The direct control path now expects:
- `--family-slice-json`

as the normal bounded A2-derived controller input.

Legacy profile-only control is compatibility mode only.
If it is intentionally used, it must be explicit:
- `--allow-legacy-goal-profile-mode`

and the resulting controller surface is expected to demote that run to manual review.

## Bare `go on` contract

If the controller decides to continue, run the continuation command above.

Operationally, bare `go on` now means:
- reuse the same `run_id`
- reuse the same `runs_root`
- do not use `--clean`
- extend the graveyard-first campaign by one more bounded tranche with the same knobs
- rerun the cycle audit
- rewrite the same controller result packet with incremented `go_on_count`

## No-copy-paste rule

There is no required manual copy-paste of results between controller and runtime.
The only shared surface needed for controller reading is the repo-held controller result packet above.
