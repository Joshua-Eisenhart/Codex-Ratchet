Use Ratchet A2/A1.

You are an A1 Codex thread.

Read first:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md

Launch packet:
MODEL: GPT-5.4 Medium
THREAD_CLASS: A1_WORKER
MODE: PROPOSAL_ONLY
A1_QUEUE_STATUS: READY_FROM_EXISTING_FUEL
dispatch_id: A1_DISPATCH__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1
target_a1_role: A1_PROPOSAL
required_a1_boot: /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md
a1_reload_artifacts:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md
source_a2_artifacts:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_BRAIN_SLICE__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md
bounded_scope: One bounded A1_PROPOSAL wiggle tranche on one fixed run_id that keeps all authoritative outputs in repo-held files and supports exact bare go on continuation on the same run.
stop_rule: Stop after one bounded wiggle tranche, one soak audit, and one rewritten controller result packet.
go_on_count: 0
go_on_budget: 6

Prompt to execute:
Use the current A1 boot:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/31_A1_THREAD_BOOT__v1.md

Read these A1 reload artifacts before acting:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md

Read these companion wiggle surfaces before acting:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/26_BOOTPACK_A1_WIGGLE__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a1_wiggle_autopilot.py
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/run_a1_wiggle_soak_audit.py
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_a1_wiggle_controller_result.py

Run one bounded A1_PROPOSAL wiggle tranche only.

Use only these A2 fuel surfaces:
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_BRAIN_SLICE__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/OPEN_UNRESOLVED__v1.md
- /Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md

Fixed lane constants:
- dispatch_id: A1_DISPATCH__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1
- run_id: RUN_A1_WIGGLE_CONTROLLERLED_20260315_01
- runs_root: /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/a1_wiggle_controllerled_runs
- run_dir: /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/a1_wiggle_controllerled_runs/RUN_A1_WIGGLE_CONTROLLERLED_20260315_01
- controller_result_json: /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_launch_returns/A1_DISPATCH__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1__A1_PROPOSAL__controller_result.json
- soak_audit_report_json: /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/a1_wiggle_controllerled_runs/RUN_A1_WIGGLE_CONTROLLERLED_20260315_01/reports/a1_wiggle_soak_audit_report.json
- go_on_budget: 6

Task:
- keep authoritative outputs in repo-held files, not in chat
- use the deterministic wiggle/autopilot path, not manual theory prose
- on initial launch:
  - if run_dir does not exist yet, run:
    - python3 system_v3/tools/a1_wiggle_autopilot.py --run-id RUN_A1_WIGGLE_CONTROLLERLED_20260315_01 --runs-root /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/a1_wiggle_controllerled_runs --cycles 8 --goal-profile refined_fuel --goal-selection interleaved --debate-mode graveyard_recovery --stall-limit-cycles 6 --max-run-bytes 250000000 --project-save-every-cycles 5 --clean
  - if run_dir already exists, do not clean it; rerun the same command without --clean
  - then run:
    - python3 system_v3/tools/run_a1_wiggle_soak_audit.py --run-dir /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/a1_wiggle_controllerled_runs/RUN_A1_WIGGLE_CONTROLLERLED_20260315_01 --max-cycles-without-progress 6 --out-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/a1_wiggle_controllerled_runs/RUN_A1_WIGGLE_CONTROLLERLED_20260315_01/reports/a1_wiggle_soak_audit_report.json
  - then run:
    - python3 system_v3/tools/build_a1_wiggle_controller_result.py --dispatch-id A1_DISPATCH__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1 --role-type A1_PROPOSAL --run-dir /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/a1_wiggle_controllerled_runs/RUN_A1_WIGGLE_CONTROLLERLED_20260315_01 --go-on-budget 6 --out-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_launch_returns/A1_DISPATCH__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1__A1_PROPOSAL__controller_result.json

Continuation contract:
- if the controller later sends exactly: go on
- do one more bounded tranche on the same run_id and same runs_root
- do not widen scope
- do not change knobs
- do not use --clean
- rerun the same soak audit command
- rebuild the same controller result JSON with:
  - python3 system_v3/tools/build_a1_wiggle_controller_result.py --dispatch-id A1_DISPATCH__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1 --role-type A1_PROPOSAL --run-dir /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/a1_wiggle_controllerled_runs/RUN_A1_WIGGLE_CONTROLLERLED_20260315_01 --go-on-budget 6 --previous-result-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_launch_returns/A1_DISPATCH__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1__A1_PROPOSAL__controller_result.json --increment-go-on-count --out-json /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_launch_returns/A1_DISPATCH__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1__A1_PROPOSAL__controller_result.json

Rules:
- no A2 refinery
- no canon claims
- no lower-loop claims
- no broad prose recap in chat
- no hidden-memory continuation
- exact stop_rule: Stop after one bounded wiggle tranche, one soak audit, and one rewritten controller result packet.
- stop after one bounded tranche, one soak audit, and one rewritten controller result packet

Required chat response:
Reply in 3 short lines only:
1. controller_result_json: /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/thread_launch_returns/A1_DISPATCH__WIGGLE_SOAK_CONTROLLERLED__2026_03_15__v1__A1_PROPOSAL__controller_result.json
2. controller_decision: <STOP | CONTINUE_ONE_BOUNDED_STEP | MANUAL_REVIEW_REQUIRED>
3. run_dir: /Users/joshuaeisenhart/Desktop/Codex Ratchet/work/audit_tmp/a1_wiggle_controllerled_runs/RUN_A1_WIGGLE_CONTROLLERLED_20260315_01
