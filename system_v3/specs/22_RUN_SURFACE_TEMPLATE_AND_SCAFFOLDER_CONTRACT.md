# Run Surface Template and Scaffolder Contract
Status: DRAFT / NONCANON
Date: 2026-02-20
Owner: `RQ-133..RQ-138`

## Scope
This document defines deterministic run-surface scaffolding for implementation and test runs.

## Normative Clauses
- `RQ-133` MUST: run surface scaffolding is deterministic from `(run_id, baseline_state_hash, strategy_hash, spec_hash, bootpack_b_hash, bootpack_a_hash)` and emits identical file tree/bootstrap contents for identical inputs.
- `RQ-134` MUST: scaffolder pre-emits required gate report templates before run start.
- `RQ-135` MUST: scaffolder pre-emits tape/log placeholders using deterministic shard suffixes.
- `RQ-136` MUST: run manifest includes immutable active spec/bootpack hashes; template-backed paths may additionally include source references.
- `RQ-137` MUST: scaffolder fails closed when target run directory already exists and is non-empty.
- `RQ-138` MUST: template set changes are versioned under new template directory/version token; existing template versions are immutable.

## Template Root
Template root:
- `system_v3/runs/_run_templates_v1/`

Current live behavior:
- if `system_v3/runs/_run_templates_v1/` exists, the scaffolder may load template-backed manifest/report assets from it
- if that template root is absent, the live scaffolder falls back to built-in deterministic defaults for manifest/report/tape/log bootstrap surfaces

Template-backed assets when the template root exists:
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
- creates deterministic directory structure
- uses template-derived files when the template root is present; otherwise uses built-in deterministic defaults
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

`P2_B_CONFORMANCE` producer:
- `system_v3/tools/run_conformance_fixture_matrix.py`

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

`P2_B_CONFORMANCE` output rule:
- primary detailed result: `reports/conformance_results.json`
- summary companion: `reports/conformance_report.json`

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
Strict/default tool path:
- `system_v3/tools/run_real_loop.py`

Explicit recovery tool path:
- `system_v3/tools/run_real_loop_recovery_cycle.py`

Purpose:
- runs `system_v3/runtime/ratchet_core/runner.py` inside a run-scoped surface
- materializes required gate artifacts from authoritative packet/tape lineage (compile/dependency/preflight reports, replay reports, evidence pack, graveyard records, tapes)
- may materialize `export_block_*.txt` only as a fallback/diagnostic surface when authoritative packet lineage is insufficient
- executes full gate pipeline after run materialization
- default strict mode fails closed on missing canonical runtime artifacts such as canonical events and canonical graveyard records
- recovery mode is operator-explicit and should use the dedicated recovery entrypoint rather than treating recovery as the normal runtime path

Strict/default CLI contract:
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

Recovery CLI contract:
```text
python3 system_v3/tools/run_real_loop_recovery_cycle.py \
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

Recovery note:
- `run_real_loop_recovery_cycle.py` forces recovery mode and is the preferred operator entrypoint when reconstructed artifacts are intentionally allowed
- `run_real_loop.py --allow-reconstructed-artifacts` remains a lower-level compatibility path, not the preferred operator surface
- compatibility-path recovery on the strict runner now emits a controller-facing manual-review signal; preferred recovery entrypoints do not share that legacy-path marker

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
- `b_reports/`
- `sim/`
- `tapes/`
- `logs/`
- `reports/`
- `tuning/`
- `zip_packets/`
- `a1_inbox/`

Optional fallback/diagnostic dirs:
- `outbox/`
- `snapshots/`

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
- `reports/a1_semantic_and_math_substance_gate_report.json`
- `reports/long_run_write_guard_report.json`
- `reports/loop_health_diagnostic.json`
- `reports/release_checklist_v1.json`
- `tapes/export_tape.000.jsonl`
- `tapes/campaign_tape.000.jsonl`
- `logs/events.000.jsonl`
- `state.json`
- `state.heavy.json` (when heavy sidecar content exists for the run)

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
- `bootpack_b_hash`
- `bootpack_a_hash`

Optional template-backed extensions:
- `template_version`
- `source_refs[]`

`source_refs[]` entry when present:
- `path`
- `sha256`
- `role`

## Determinism Rules
- all JSON files use sorted keys
- current live tooling writes UTF-8 JSON text; ASCII-only JSON is not required by the scaffolder path
- `.jsonl` placeholders are created as empty files (zero bytes)
- shard naming starts at `.000`
- no timestamp-derived randomness in file names
- `outbox/` must not be treated as authoritative lineage when ZIP packets and tapes are present
- helper materialization should prefer packet/tape sources over regenerating duplicate export files

## Fail-Closed Conditions
Initialization fails when:
- any required hash arg is missing or non-hex
- run id contains invalid path characters
- target run path exists and has any content

Template-backed note:
- current live scaffolder does not fail merely because `_run_templates_v1/` is absent; it falls back to built-in deterministic defaults

## Versioning Rule
Template version upgrades:
- new version path: `system_v3/runs/_run_templates_v<N>/`
- older versions remain untouched
- when template-backed mode is used, manifest field `template_version` should pin run to exact template version
- the current built-in fallback mode does not emit `template_version`
