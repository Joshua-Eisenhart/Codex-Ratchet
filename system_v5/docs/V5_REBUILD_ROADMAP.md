# V5 Rebuild Roadmap

Status: active roadmap
Scope: clean SIM/QIT rebuild after freezing v4 as reference

## Purpose

The v5 rebuild is not one batch. It is an ongoing transfer and cleanup program:

- keep `system_v4/probes` as reference and evidence mine;
- build clean executable surfaces in `system_v5`;
- preserve exploratory speed through formal scouts;
- use Grok/Gemini/Sonnet as proposal and audit pressure;
- keep gates strong enough to reject fake evidence without freezing rough tower
  exploration.

Bounded does not mean conservative. It means maximum exploration under maximum
constraints, like actual evolution: branch hard, prune hard, preserve deaths,
and let strong gates select from many attempts without pretending the survivors
are canonical.

## Current State

Completed first checkpoint:

- v5 clean rebuild charter;
- formal-scout contract;
- provider split doc;
- two passing formal-scout harnesses;
- formal-scout validator;
- initial probe-folder inventory;
- read-only v4 probe classifier;
- provider record with Grok completed, Sonnet audit completed, Gemini CLI
  blocked.

This is a foundation checkpoint, not completion of the rebuild.

## Workstreams

### 1. V4 Reference Transfer

Goal: mine useful v4 callables and receipts into clean v5 wrappers or scouts.

Next actions:

1. Build a `v4_callable_registry_*.json` from selected families.
2. For each selected v4 file, record callable names, import status, claim
   ceiling, result path, and graveyard families.
3. Create v5 wrappers only for active reuse.
4. Do not copy v4 files into v5 as authority.

Done when:

- selected family has a callable registry;
- every promoted reuse has a v5 wrapper or formal-scout harness;
- every wrapper has a receipt and claim ceiling.

### 2. Probe Corpus Cleanup

Goal: make the v4 probe folder navigable without broad deletion.

Current evidence:

- 10,986 direct files in `system_v4/probes`;
- 6,588 generated survivor-class files classified as
  `quarantine_by_manifest_candidate`;
- 252 naming-contamination review files;
- 52 result-linkage review files.
- v4 probe dirty-state baseline:
  `system_v5/ops/queue_cleanup/v4_probe_status_baseline_20260514.json`.

Next actions:

1. Write a quarantine move manifest for one generated family.
2. Dry-run the manifest.
3. Verify no admitted/reference file is selected.
4. Only then move by manifest, if approved.

Done when:

- v4 write policy is enforced by preflight drift detection;
- generated families are either quarantined or indexed;
- naming-contaminated reuse goes through v5 wrappers or manifest renames.

### 3. Formal-Scout Tower Building

Goal: explore geometric constraint manifold layers without claiming canon.

Current passing scouts:

- `sim_nested_finite_geometry_holonomy_noncommutation_probe.py`
- `sim_entropy_reduction_before_hopf_projection_order_probe.py`

Next scouts:

1. `sim_su2_unit_quaternion_hopf_holonomy_order_probe.py`
2. `sim_nested_hopf_weyl_connection_transport_order_probe.py`
3. `sim_spinor_clifford_pauli_projection_order_probe.py`
4. `sim_topology_cycle_hopf_projection_order_probe.py`

Each must include:

- `classification: formal_scout`;
- `promotion_allowed: false`;
- `claim_ceiling`;
- exact callable paths;
- positive checks;
- boundary checks;
- graveyards;
- nearby-variant count/pass summary;
- `why_not_v4_probes`.

Done when:

- multiple layer orders have receipts;
- at least one order comparison kills adjacent alternatives;
- rough tower work remains fenced from canonical claims.

### 4. Provider Proposal Lanes

Goal: use external model diversity without letting proposals become evidence.

Current status:

- Grok direct xAI API works.
- Sonnet via Claude Bridge works.
- Gemini CLI is blocked by interactive browser auth.
- Provider proposal receipts now have a schema and validator.

Next actions:

1. Build direct Gemini API route or keep Gemini CLI disabled until fixed.
2. Run provider receipt validation after each provider batch.
3. Run Grok and Sonnet on the same bounded scout target and compare.
4. Translate only repo-grounded proposals into v5 formal scouts.

Done when:

- provider outputs are machine-recorded;
- blocked providers have closure criteria;
- every translated proposal cites real callable paths.

### 5. Gate Quality

Goal: detect gates that are too weak, too strict, stale, or decorative.

Known gate issues:

- v4 write fence now checks staged v4 changes and v4/probes dirty-state drift.
- provider receipts now have schema validation.
- large generated inventories can accidentally enter commits.
- formal-scout validator can rerun harnesses with `--fresh-rerun`.

Next actions:

1. Add a gate-quality report under `system_v5/ops/queue_cleanup/`.
2. Add a manifest-approved v4 quarantine dry-run.
3. Keep provider receipt validation in every provider batch.

Done when:

- gates catch bad evidence and bad placement automatically;
- gates do not block formal-scout exploration when receipts are honest.

## Immediate Next Batch

Best next batch:

1. Add direct Gemini or blocked-provider receipt.
2. Build SU(2)-Hopf formal scout from already-importable v4 targets.
3. Add a gate-quality report for over-strict vs weak/decorative gates.
4. Commit as the next small v5 checkpoint.

## Stop Conditions

Stop expansion and clean/audit when:

- new files appear in `system_v4/probes`;
- generated JSON over 1 MB is staged without explicit evidence-snapshot intent;
- provider output is used without a proposal receipt;
- formal scout lacks boundary/graveyard/claim-ceiling fields;
- `__pycache__` or runtime byproducts remain under v5 ops;
- git status counts grow without explanation.
