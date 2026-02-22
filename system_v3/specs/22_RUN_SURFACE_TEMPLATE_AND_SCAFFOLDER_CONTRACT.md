# Run Surface Template and Scaffolder Contract
Status: DRAFT / NONCANON
Date: 2026-02-20
Owner: `RQ-133..RQ-138`

## Scope
This document defines deterministic run-surface scaffolding for implementation and test runs.

## Normative Clauses
- `RQ-133` MUST: run surface scaffolding is deterministic from `(run_id, baseline_state_hash, strategy_hash)` and emits identical file tree and template contents for identical inputs.
- `RQ-134` MUST: scaffolder pre-emits required gate report templates before run start.
- `RQ-135` MUST: scaffolder pre-emits tape/log placeholders using deterministic shard suffixes.
- `RQ-136` MUST: run manifest includes immutable source references and hashes for the active spec set and bootpack files used.
- `RQ-137` MUST: scaffolder fails closed when target run directory already exists and is non-empty.
- `RQ-138` MUST: template set changes are versioned under new template directory/version token; existing template versions are immutable.

## Template Root
Template root:
- `system_v3/runs/_run_templates_v1/`

Required template assets:
- `README.md`
- `RUN_MANIFEST_v1.template.json`
- `reports/spec_lock_report.template.json`
- `reports/artifact_grammar_report.template.json`
- `reports/phase_transition_report.template.json`
- `reports/conformance_report.template.json`
- `reports/a0_compile_report.template.json`
- `reports/replay_pass_1.template.json`
- `reports/replay_pass_2.template.json`
- `reports/replay_pair_report.template.json`
- `reports/evidence_ingest_report.template.json`
- `reports/graveyard_integrity_report.template.json`
- `reports/long_run_write_guard_report.template.json`
- `reports/loop_health_diagnostic.template.json`
- `reports/release_checklist_v1.template.json`
- `tapes/export_tape.000.template.jsonl`
- `tapes/campaign_tape.000.template.jsonl`
- `logs/events.000.template.jsonl`

## Scaffolder Tool Contract
Tool path:
- `system_v3/tools/init_run_surface.py`

CLI contract:
```text
python3 system_v3/tools/init_run_surface.py \
  --run-id <RUN_ID> \
  --baseline-state-hash <sha256hex> \
  --strategy-hash <sha256hex> \
  --spec-hash <sha256hex> \
  --bootpack-b-hash <sha256hex> \
  --bootpack-a-hash <sha256hex>
```

Behavior:
- creates `system_v3/runs/<RUN_ID>/`
- copies template-derived files into deterministic directory structure
- materializes `RUN_MANIFEST_v1.json` with provided hash values
- refuses to overwrite existing non-empty run directory

## Phase Gate Tool Contract
Tool path:
- `system_v3/tools/advance_phase_gate.py`

CLI contract:
```text
python3 system_v3/tools/advance_phase_gate.py \
  --run-dir system_v3/runs/<RUN_ID> \
  [--require-phase P<N>_<NAME>]
```

Behavior:
- evaluates phase gate conditions from run report artifacts
- updates `reports/phase_transition_report.json`
- synchronizes `reports/release_checklist_v1.json` phase status map
- optional `--require-phase` returns non-zero unless that phase is `PASS`

## Phase Report Producer Tools
`P0_SPEC_LOCK` producer:
- `system_v3/tools/run_spec_lock_gate.py`

`P1_ARTIFACT_GRAMMAR` producer:
- `system_v3/tools/run_artifact_grammar_gate.py`

`P3_A0_COMPILER` producer:
- `system_v3/tools/run_a0_compile_gate.py`

`P4_A1_TO_B_SMOKE` producer:
- `system_v3/tools/run_replay_pair_gate.py`

`P5_SIM_EVIDENCE_LOOP` producers:
- `system_v3/tools/run_evidence_ingest_gate.py`
- `system_v3/tools/run_graveyard_integrity_gate.py`

`P6_LONG_RUN_DISCIPLINE` producer:
- `system_v3/tools/run_long_run_write_guard_gate.py`

`P7_RELEASE_CANDIDATE` producer:
- `system_v3/tools/run_release_candidate_gate.py`

All producer tools:
- read current workspace state
- write deterministic report JSON into the target run's `reports/` directory

`P3_A0_COMPILER` CLI contract:
```text
python3 system_v3/tools/run_a0_compile_gate.py \
  --run-dir system_v3/runs/<RUN_ID> \
  [--min-export-blocks <N>]
```

`P4_A1_TO_B_SMOKE` CLI contract:
```text
python3 system_v3/tools/run_replay_pair_gate.py \
  --run-dir system_v3/runs/<RUN_ID> \
  [--min-cycles 50]
```

`P5_SIM_EVIDENCE_LOOP` CLI contracts:
```text
python3 system_v3/tools/run_evidence_ingest_gate.py \
  --run-dir system_v3/runs/<RUN_ID> \
  [--min-positive-signals 1] \
  [--min-negative-signals 1] \
  [--min-kill-signals 1]

python3 system_v3/tools/run_graveyard_integrity_gate.py \
  --run-dir system_v3/runs/<RUN_ID> \
  [--min-graveyard-records 1]

python3 system_v3/tools/run_long_run_write_guard_gate.py \
  --run-dir system_v3/runs/<RUN_ID> \
  [--max-shard-bytes 5000000] \
  [--max-shard-lines 200000] \
  [--max-run-bytes 200000000] \
  [--max-run-files 5000]

python3 system_v3/tools/run_release_candidate_gate.py \
  --run-dir system_v3/runs/<RUN_ID>
```

## Full Gate Pipeline Tool Contract
Tool path:
- `system_v3/tools/run_phase_gate_pipeline.py`

CLI contract:
```text
python3 system_v3/tools/run_phase_gate_pipeline.py \
  --run-dir system_v3/runs/<RUN_ID> \
  --fixture-pack system_v3/conformance/fixtures_v1 \
  --bootpack-hash <sha256hex> \
  [--use-expected-as-observed] \
  [--run-loop-health] \
  [--enforce-loop-health] \
  [--allow-loop-health-warn] \
  [--no-pending-stall-threshold 5] \
  [--max-shard-bytes 5000000] \
  [--max-shard-lines 200000] \
  [--max-run-bytes 200000000] \
  [--max-run-files 5000]
```

## Real Loop Tool Contract (Non-Normative Helper)
Tool path:
- `system_v3/tools/run_real_loop.py`

Purpose:
- runs `system_v3/runtime/ratchet_core/runner.py` inside a run-scoped surface
- materializes required gate artifacts (`export_block_*.txt`, compile/dependency/preflight reports, replay reports, evidence pack, graveyard records, tapes)
- executes full gate pipeline after run materialization

CLI contract:
```text
python3 system_v3/tools/run_real_loop.py \
  --run-id <RUN_ID> \
  [--loops 1] \
  [--max-entries 20] \
  [--max-items 1000] \
  [--sim-cap 3] \
  [--adaptive-sim-cap] \
  [--sim-cap-min 8] \
  [--sim-cap-max 200] \
  [--sim-cap-headroom 16] \
  [--min-cycles 50] \
  [--max-shard-bytes 5000000] \
  [--max-shard-lines 200000] \
  [--max-run-bytes 200000000] \
  [--max-run-files 5000] \
  [--max-runs-total-bytes 2000000000] \
  [--max-runs-count 200] \
  [--top-n-largest-runs 10] \
  [--clean-existing-run]
```

Determinism-pair helper:
- `system_v3/tools/run_bridge_determinism_pair.py`

```text
python3 system_v3/tools/run_bridge_determinism_pair.py \
  --run-id-a <RUN_ID_A> \
  --run-id-b <RUN_ID_B> \
  [--loops 15] \
  [--max-entries 20] \
  [--max-items 600] \
  [--sim-cap 8] \
  [--adaptive-sim-cap] \
  [--sim-cap-min 8] \
  [--sim-cap-max 200] \
  [--sim-cap-headroom 16] \
  [--min-cycles 50]
```

Loop-health diagnostic helper:
- `system_v3/tools/run_loop_health_diagnostic.py`

```text
python3 system_v3/tools/run_loop_health_diagnostic.py \
  --run-dir system_v3/runs/<RUN_ID> \
  [--no-pending-stall-threshold 5]
```

## Run Directory Structure (Minimum)
Required dirs:
- `outbox/`
- `b_reports/`
- `snapshots/`
- `sim/`
- `tapes/`
- `logs/`
- `reports/`
- `tuning/`

Required bootstrap files:
- `RUN_MANIFEST_v1.json`
- `reports/spec_lock_report.json`
- `reports/artifact_grammar_report.json`
- `reports/phase_transition_report.json`
- `reports/conformance_report.json`
- `reports/a0_compile_report.json`
- `reports/replay_pass_1.json`
- `reports/replay_pass_2.json`
- `reports/replay_pair_report.json`
- `reports/evidence_ingest_report.json`
- `reports/graveyard_integrity_report.json`
- `reports/long_run_write_guard_report.json`
- `reports/loop_health_diagnostic.json`
- `reports/release_checklist_v1.json`
- `tapes/export_tape.000.jsonl`
- `tapes/campaign_tape.000.jsonl`
- `logs/events.000.jsonl`

Optional helper report files:
- `reports/adaptive_sim_cap_report.json`

## Manifest Schema
Required keys:
- `schema`: `RUN_MANIFEST_v1`
- `run_id`
- `created_utc`
- `baseline_state_hash`
- `strategy_hash`
- `spec_hash`
- `bootpack_hashes`:
  - `thread_b_bootpack_sha256`
  - `thread_a_bootpack_sha256`
- `template_version`
- `source_refs[]`

`source_refs[]` entry:
- `path`
- `sha256`
- `role`

## Determinism Rules
- all JSON files use sorted keys, ASCII-only output
- `.jsonl` placeholders are created as empty files (zero bytes)
- shard naming starts at `.000`
- no timestamp-derived randomness in file names

## Fail-Closed Conditions
Initialization fails when:
- any required hash arg is missing or non-hex
- run id contains invalid path characters
- target run path exists and has any content
- required template asset is missing

## Versioning Rule
Template version upgrades:
- new version path: `system_v3/runs/_run_templates_v<N>/`
- older versions remain untouched
- manifest field `template_version` pins run to exact template version
