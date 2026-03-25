# SIM_PROCESS_GAP_AUDIT__2026_03_14__v1
Status: NONCANON / AUDIT
Date: 2026-03-14

## Scope

Audit current SIM process implementation against:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/72_SIM_CAMPAIGN_AND_SUITE_MODES__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/06_SIM_EVIDENCE_AND_TIERS_SPEC.md`

Audited files:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/sim_dispatcher.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/a1_a0_b_sim_runner.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_evidence_ingest_gate.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_replay_pair_gate.py`

## Findings

### 1. Dispatcher is stage-aware but not suite-aware

Current dispatcher blocks stages whose dependency stages still have pending work, which is real progress, but it does not schedule or distinguish:
- `micro_suite`
- `mid_suite`
- `segment_suite`
- `engine_suite`
- `mega_suite`
- `failure_isolation`
- `graveyard_rescue`
- `replay_from_tape`

Witness:
- [sim_dispatcher.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/runtime/bootpack_b_kernel_v1/sim_dispatcher.py#L8)
- [sim_dispatcher.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/runtime/bootpack_b_kernel_v1/sim_dispatcher.py#L12)
- [sim_dispatcher.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/runtime/bootpack_b_kernel_v1/sim_dispatcher.py#L49)

Gap:
- stage dependency exists
- suite-mode process law does not

### 2. Runner still executes a flat pending-task slice

Current runner asks the dispatcher for tasks, truncates by `max_sims`, then runs each task in a flat loop. It does not run by stage group or suite mode, and it has no first-class path for:
- failure isolation
- graveyard rescue
- replay from tape/save lineage

Witness:
- [a1_a0_b_sim_runner.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/runtime/bootpack_b_kernel_v1/a1_a0_b_sim_runner.py#L731)
- [a1_a0_b_sim_runner.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/runtime/bootpack_b_kernel_v1/a1_a0_b_sim_runner.py#L739)
- [a1_a0_b_sim_runner.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/runtime/bootpack_b_kernel_v1/a1_a0_b_sim_runner.py#L742)

Gap:
- budget enforcement exists
- campaign-mode execution does not

### 3. Evidence ingest gate is token-count based, not campaign-aware

Current evidence gate only counts:
- evidence blocks
- positive signals
- negative signals
- kill signals

It does not check:
- stage closure
- family coverage by target class
- mega-gate legality
- failure-isolation requirement after fail
- graveyard-rescue coverage

Witness:
- [run_evidence_ingest_gate.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/run_evidence_ingest_gate.py#L46)
- [run_evidence_ingest_gate.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/run_evidence_ingest_gate.py#L71)
- [run_evidence_ingest_gate.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/run_evidence_ingest_gate.py#L94)

Gap:
- signal presence is checked
- campaign sufficiency is not

### 4. Replay pair gate checks determinism, not campaign replay semantics

Current replay gate compares pass reports and hashes. It does not validate that replay preserved:
- stage order
- suite kinds
- replay source binding
- campaign reconstruction from tape/save surfaces

Witness:
- [run_replay_pair_gate.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/run_replay_pair_gate.py#L44)
- [run_replay_pair_gate.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/run_replay_pair_gate.py#L70)
- [run_replay_pair_gate.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/run_replay_pair_gate.py#L114)

Gap:
- deterministic replay equality exists
- replayed campaign semantics do not

## Exact patch targets

1. `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/sim_dispatcher.py`
- add suite-kind aware planning
- block `engine_suite` and `mega_suite` by explicit closure rules, not just pending dependency stages
- surface `failure_isolation` and `graveyard_rescue` dispatch entries

2. `/home/ratchet/Desktop/Codex Ratchet/system_v3/runtime/bootpack_b_kernel_v1/a1_a0_b_sim_runner.py`
- execute by stage/suite group instead of flat task slice
- add replay-from-lineage mode
- add failure-isolation branch mode
- add graveyard-rescue mode

3. `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_evidence_ingest_gate.py`
- replace raw token-count sufficiency with campaign sufficiency reporting
- include stage/family/mega-gate checks

4. `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/run_replay_pair_gate.py`
- add campaign replay equivalence checks
- require explicit replay source class
