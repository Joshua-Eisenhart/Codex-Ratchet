# Controller + Harness Integration Status

Status: current live snapshot
Date: 2026-04-20
Purpose: keep the control-plane state visible so bounded sim work does not silently outrun truth, hygiene, contract, or worker/harness reality.

## Checked live facts
- canonical interpreter: `~/.local/share/codex-ratchet/envs/main/bin/python3`
- `claude` present: `/usr/local/bin/claude` (`2.1.112`)
- `codex` present: `/usr/local/bin/codex` (`0.118.0`)
- `tmux` absent on PATH
- `mngr` absent on PATH
- `omc` absent on PATH
- `omx` absent on PATH
- logical CPU count: `10`

## Lane consequence checked now
- `scripts/claim_lane.py` was patched from the stale `docs/plans/lanes.md` path to the live `system_v5/docs/plans/lanes.md` path.
- claim/release smoke passed for `T-01`.
- live-surface selector repair now passes at controller level:
  - `system_v4/probes/live_queue_controller.py` now reads the first open `T` row from `system_v5/docs/plans/lanes.md` when audits are red instead of hardcoding `batch1`
  - current live selection is `T-01` → `z3_capability` + `truth_audit` + `controller_alignment`
  - targeted proof: `pytest system_v4/tests/test_live_queue_controller.py -q` → `6 passed`
- attempted `TI-03` (`TopoNetX × torch`) then hit the cleanup-first guard before sim execution.
- blocker artifact: `system_v4/probes/a2_state/sim_results/system_hygiene_supervisor_results.json`

## Maintenance overlay state

| row | surface | status | evidence | checked state |
|---|---|---|---|---|
| M-01 | truth / integrity verification | blocked | `system_v4/probes/a2_state/sim_results/probe_truth_audit_results.json` | `hard_finding_count=226`, `warning_finding_count=47` |
| M-02 | hygiene / repository maintenance | blocked | `system_v4/probes/a2_state/sim_results/repo_hygiene_audit_results.json` | `source_dirty_count=146`, `dirty_worktree_count=203`, duplicate basename `lego_pauli_algebra_results.json`, secondary result dir populated |
| M-03 | controller / harness contract governance | blocked | `system_v4/probes/a2_state/sim_results/controller_alignment_audit_results.json` | `controller_contract_current=false`, `docs_current=true`, `code_process_green=false` |
| M-04 | runtime / CLI worker prerequisites | passes local rerun | `system_v4/probes/a2_state/sim_results/runtime_hygiene_audit_results.json` | `blocker_count=0`, `ok=true` |
| M-05 | subagent + wiki harness integration | runs | `system_v5/docs/plans/plans/subagent-wiki-harness-integration-contract.md` | contract exists; direct Claude `10/10` read-only scale proved; one bounded write-producing Claude maintenance packet now proved (`live_queue_controller.py` + tests); Gemini `3/3` smoke proved; wiki-cluster parity still remains |

## Source-dirty control surface
- supervisor: `overall_green=false`, `repair_queue_count=5`
- active actionable lane: `probe_source__sim_family_axis0`
- active actionable source file: `system_v4/probes/sim_axis0_gtower_gradient_cascade 2.py`
- direct result companion: `system_v4/probes/a2_state/sim_results/axis0_gtower_gradient_cascade 2_results.json`
- docs lane also exists but is opt-in only right now: `docs_and_specs__docs_and_specs` with `CLAUDE.md`
- evidence:
  - `system_v4/probes/a2_state/sim_results/system_hygiene_supervisor_results.json`
  - `system_v4/probes/a2_state/sim_results/source_dirty_lane_manifest.json`
  - `system_v4/probes/a2_state/sim_results/source_dirty_stage_plan.json`

## Admitted worker model now
- Hermes remains the controller.
- Bounded non-overlapping CLI workers are the admitted execution shape.
- Claude print-mode workers are the fully specified default launch model in the current launch docs.
- Codex CLI is installed and usable on this machine, but launch-ready contract parity with Claude is still missing.
- No tmux/manager swarm layer is installed on this machine, so direct Hermes-tracked processes remain the honest default.
- Claude CLI capability is checked live as an authenticated Claude session.
- direct `claude -p` print-mode workers are now the proved Claude execution path; see `system_v5/docs/plans/plans/claude-worker-utilization-receipt.md`.
- Hermes `delegate_task` ACP did not prove a Claude-routed child in the bounded 2026-04-20 read test; the returned child reported local GPT-5.4 tooling instead, so direct `claude -p` remains the only proved Claude path in this runtime.
- Gemini CLI is also installed and headless-usable; a 3-worker read-only smoke is now proved in `system_v5/docs/plans/plans/gemini-worker-utilization-receipt.md`.

## Whole-process integration table

| surface | role | current state | main evidence |
|---|---|---|---|
| build-stage lanes | sim/tool work (`T`/`TI`/`C`/`NC`/`B`/`S`) | mixed; `TI-03` currently blocked before execution | `system_v5/docs/plans/lanes.md` |
| maintenance overlay | truth / hygiene / contract / runtime / M-05 | mostly red except runtime | `system_v4/probes/a2_state/sim_results/system_hygiene_supervisor_results.json` |
| execution surface | Hermes + bounded CLI workers | working for bounded read-only probes; direct `claude -p` now proved through `10/10`, Gemini headless smoke proved, Codex parity still incomplete | this file + runtime hygiene + worker receipts |
| wiki-builder surface | separate tranche-based wiki maintenance | drafted contract exists; not merged into sim runner | `system_v5/docs/plans/plans/wiki-automation-run-contract.md` |
| shared reconciliation surfaces | Hermes-only joins for shared status/routing pages | present, but still dependent on controller discipline | launch docs + wiki automation docs |
| lens-audit surface | plurality-preserving audits (`🦉` / `🧨` / `🦋`) | now proved as a usable audit family for process questions | this file + `subagent-wiki-harness-integration-contract.md` |

## Voice-lens audit summary
- `🦉 Hume` result:
  - some prerequisites really work now
  - bounded direct CLI worker execution is now proved at a stronger level than before: Claude `10/10` read-only scale passed, Gemini `3/3` read-only smoke passed
  - the end-to-end process is still not honestly green because truth/hygiene/contract remain red
- `🧨 Popper` result:
  - likely breakpoints are selector drift, closure writeback drift, status/heartbeat optimism, global red audits overriding local wins, and entrypoint drift
  - current Claude scaling receipts suggest at least one apparent "cap" symptom is really `max_turns` mis-tuning, not a proved rate wall
- `🦋 Zhuangzi` result:
  - keep build, maintenance, execution, wiki, reconciliation, and provenance/routing surfaces separate rather than smoothing them into one story

## M-05 contract surface
- drafted contract:
  - `system_v5/docs/plans/plans/subagent-wiki-harness-integration-contract.md`
- current M-05 state:
  - status now `runs`
  - contract exists
  - direct Claude read-only scaling is proved through `10/10`
  - one bounded write-producing Claude maintenance packet is now proved: `claude -p` patched `system_v4/probes/live_queue_controller.py` + `system_v4/tests/test_live_queue_controller.py`, and Hermes reread the diff plus reran `pytest system_v4/tests/test_live_queue_controller.py -q` → `6 passed`
  - Gemini read-only smoke is proved at `3/3`
  - wiki-cluster parity testing still remains

## What changed in repo control surfaces this pass
- added `M` maintenance overlay rows to `system_v5/docs/plans/lanes.md`
- corrected `plans/plans/` path drift in:
  - `system_v5/docs/plans/plans/local-launch-checklist-bounded-geometry-first-run.md`
  - `system_v5/docs/plans/plans/launch-prompt-bounded-geometry-first-automated-run.md`
  - `system_v5/docs/plans/plans/on-demand-telegram-runner.md`
- updated launch/checklist concurrency wording to use live machine facts + file isolation instead of a hard-coded `3`
- added bounded controller-process test plan:
  - `system_v5/docs/plans/plans/new-process-smoke-test-plan.md`
- added Claude worker utilization receipt:
  - `system_v5/docs/plans/plans/claude-worker-utilization-receipt.md`
- added Gemini worker utilization receipt:
  - `system_v5/docs/plans/plans/gemini-worker-utilization-receipt.md`
- added reusable CLI worker scale probe:
  - `system_v5/ops/cli_worker_scale_probe.py`
- repaired live-surface selector routing in:
  - `system_v4/probes/live_queue_controller.py`
  - `system_v4/tests/test_live_queue_controller.py`

## Next bounded moves
1. M-02: reduce repo-hygiene pressure with one bounded checkpoint/routing move from the active actionable lane.
2. M-01: triage truth-audit blocker classes instead of trying new sim packets under a red truth surface.
3. M-03: bring controller contract current after truth/hygiene blockers stop invalidating closeout claims.
4. M-05: the contract now runs at `runs`; checked this pass:
   - live-surface selector test now passes for the `T` lane
   - one bounded write-producing Claude maintenance packet succeeded under Hermes reread + pytest verification
5. Remaining M-05 falsifiers:
   - closure writeback test
   - heartbeat truth test
   - worker parity test
   - wiki shared-surface isolation test
   - wider write-producing Claude parallelism test

## Non-goal reminder
This status surface does not admit `NC`, `B`, or `S` work. It exists to keep the control plane honest while the build-stage lanes stay bounded.
