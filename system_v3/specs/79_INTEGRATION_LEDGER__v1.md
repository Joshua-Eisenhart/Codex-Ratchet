# 79_INTEGRATION_LEDGER__v1
Status: SUPPORTING / NONCANON LEDGER
Date: 2026-03-21

## Purpose

This file is a supporting detailed ledger for:

- referenced repos
- referenced source docs and method bundles
- requested skills/operators/adapters
- graph placement and runtime integration status
- known mismatches, broken stubs, and stale audits

Primary append surfaces now live at repo root:

- `/home/ratchet/Desktop/Codex Ratchet/REPO_SKILL_INTEGRATION_TRACKER.md`
- `/home/ratchet/Desktop/Codex Ratchet/SKILL_CANDIDATES_BACKLOG.md`

If a repo, method bundle, external source, or requested skill family is mentioned in work on this repo, it should be appended to those root trackers first.

This file remains as a deeper supporting ledger and should not be the first human-facing append target.

Current warning:

- parts of this ledger are already behind the live repo state
- use [A2_V4_RECOVERY_AUDIT.md](/home/ratchet/Desktop/Codex%20Ratchet/A2_V4_RECOVERY_AUDIT.md) plus the two root trackers for the current reality check before trusting older integration claims here

## Status Legend

- `LOCAL_SOURCE_VERIFIED`: local source document or repo path exists
- `URL_STAGED`: external URL is durably staged but not source-local
- `GRAPH_INGESTED`: source is already represented in graph/session surfaces
- `REGISTRY_PRESENT`: skill/operator is present in `skill_registry_v1.json`
- `HOT_PATH_REFERENCED`: explicitly referenced in `run_real_ratchet.py`
- `PATTERN_ONLY`: concept is described but not yet implemented as a real skill/operator
- `FILE_MISSING`: registry entry exists but source file is missing
- `UNVERIFIED_MAP`: a derived mapping note exists but overclaims or still needs verification
- `STALE_AUDIT_MISMATCH`: a saved audit surface is behind the current repo state

## Canonical Source And Planning Surfaces

### Primary owner and source docs

- `system_v3/specs/79_INTEGRATION_LEDGER__v1.md`
  - role: canonical durable ledger for this concern
- `/home/ratchet/Desktop/Codex Ratchet/core_docs/v4 upgrades/29 thing.txt`
  - status: `LOCAL_SOURCE_VERIFIED`, `GRAPH_INGESTED`
  - role: canonical local referent for the repeatedly referenced 29-method source family
- `/home/ratchet/Desktop/Codex Ratchet/core_docs/v4 upgrades/lev_nonclassical_runtime_design_audited.md`
  - status: `LOCAL_SOURCE_VERIFIED`
  - role: main Lev runtime design source, widened to include repo family integration and skillization intent
- `/home/ratchet/Desktop/Codex Ratchet/core_docs/v4 upgrades/jp graph asuggestions.txt`
  - status: `LOCAL_SOURCE_VERIFIED`
  - role: JP graph suggestions source
- `/home/ratchet/Desktop/Codex Ratchet/core_docs/upgrade docs/jp graph prompt!!.txt`
  - status: `LOCAL_SOURCE_VERIFIED`
  - role: JP graph prompt source

### Supporting derived surfaces

- `/home/ratchet/Desktop/Codex Ratchet/system_v4/a1_state/external_skill_admission_staging_v1.json`
  - status: durable staging surface
- `/home/ratchet/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/MASTER_INTEGRATION_AND_SKILLIZATION_MAP__2026_03_20__v1.md`
  - status: derived planning surface
- `/home/ratchet/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/SYSTEMIC_INTEGRATION_FAILURE_AUDIT__2026_03_20__v1.md`
  - status: derived failure audit
- `/home/ratchet/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/SYSTEM_INVENTORY__29_METHOD_SOURCE_CROSS_REFERENCE__2026_03_21__v1.md`
  - status: `UNVERIFIED_MAP`
  - note: source identification is useful, but live-skill and hot-path claims still need verification and some rows currently overclaim

## Current Repo / Method Bundle Inventory

### 1. The 29-method source bundle

- canonical source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/v4 upgrades/29 thing.txt`
  - surface class: `SOURCE_CORPUS`
- graph/session support:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v4/a2_state/session_logs/OPUS_DEEP_READ_29_THING.md`
  - best treatment: `RUNTIME_ONLY`
- derived cross-reference:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/SYSTEM_INVENTORY__29_METHOD_SOURCE_CROSS_REFERENCE__2026_03_21__v1.md`
  - best treatment: `DERIVED_A2`, `UNVERIFIED_MAP`
- current truth:
  - `29 thing.txt` is the canonical local source
  - `29 thing.txt` is a source design/method document only; it does not by itself prove any skill is live
  - `OPUS_DEEP_READ_29_THING.md` proves only that the source doc was graph-ingested on 2026-03-18 as one batch with 9 nodes and 8 edges
  - the `29 sources / 29 batches` graph cluster is separate and must not be substituted for this doc

### 2. Lev nonclassical runtime family

- source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/v4 upgrades/lev_nonclassical_runtime_design_audited.md`
- status:
  - `LOCAL_SOURCE_VERIFIED`
- current truth:
  - already materially expressed in runtime kernel, witness, intent, Z3, and bounded-improve families

### 3. lev-os family

- org root:
  - `https://github.com/lev-os`
  - status: `URL_STAGED`
- child repos:
  - `https://github.com/lev-os/agents`
  - `https://github.com/lev-os/leviathan`
  - status: `URL_STAGED`
- current truth:
  - durably staged
  - still not a fully realized integration family in the hot path

### 4. Karpathy family

- staged sources:
  - `https://github.com/karpathy`
  - `https://github.com/karpathy/nanoGPT`
  - `https://github.com/karpathy/nanochat`
  - `https://github.com/karpathy/autoresearch`
  - `https://github.com/karpathy/llm-council`
- current truth:
  - no longer purely pattern-only
  - `autoresearch` and `llm-council` now exist as real registry skills and are referenced in the live runner

### 5. Z3 / formal verification family

- staged source:
  - `https://github.com/Z3Prover/z3`
- current truth:
  - strongest external method family currently operationalized in system_v4

### 6. pi-mono family

- repo:
  - `https://github.com/badlogic/pi-mono`
- graph/session support:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v4/a2_state/session_logs/DEEP_FUEL_PIMONO_SESSION.md`
- current truth:
  - source family is graph-ingested
  - pi-mono adapter skillization is incomplete and partly malformed

### 7. EverMem / EverMind / MSA family

- requested/staged sources:
  - EverMemOS / EverMind-style memory backend family
  - MSA / Memory Sparse Attention family
- current truth:
  - adapter skills now exist in the registry for EverMem sync/adaptation
  - source-local verification is still incomplete
  - MSA is still staged as a backend candidate, not a live runtime family

## Skill / Operator Inventory

### A. Verified registry-present and hot-path-referenced in `run_real_ratchet.py`

- `autoresearch-operator`
  - source: `/home/ratchet/Desktop/Codex Ratchet/system_v4/skills/autoresearch_operator.py`
  - status: `REGISTRY_PRESENT`, `HOT_PATH_REFERENCED`
- `llm-council-operator`
  - source: `/home/ratchet/Desktop/Codex Ratchet/system_v4/skills/llm_council_operator.py`
  - status: `REGISTRY_PRESENT`, `HOT_PATH_REFERENCED`
- `z3-constraint-checker`
  - source: `/home/ratchet/Desktop/Codex Ratchet/system_v4/skills/z3_constraint_checker.py`
  - status: `REGISTRY_PRESENT`, `HOT_PATH_REFERENCED`
- `bounded-improve-operator`
  - source: `/home/ratchet/Desktop/Codex Ratchet/system_v4/skills/bounded_improve_operator.py`
  - status: `REGISTRY_PRESENT`, `HOT_PATH_REFERENCED`
- `intent-control-surface-builder`
  - source: `/home/ratchet/Desktop/Codex Ratchet/system_v4/skills/intent_control_surface_builder.py`
  - status: `REGISTRY_PRESENT`, `HOT_PATH_REFERENCED`

### B. Registry-present, source-present, but not hot-path-verified in this pass

- `z3-cegis-refiner`
- `property-pressure-tester`
- `differential-tester`
- `structured-fuzzer`
- `model-checker`
- `fep-regulation-operator`
- `frontier-search-operator`
- `evermem-memory-backend-adapter`
- `witness-evermem-sync`

Current truth for this block:

- all are present in `/home/ratchet/Desktop/Codex Ratchet/system_v4/a1_state/skill_registry_v1.json`
- all have source files present on disk except where separately called out below
- this ledger is not claiming hot-path runtime use for them without direct verification

### C. Registry-present but structurally broken or incomplete

- `pimono-evermem-adapter`
  - registry entry exists in `/home/ratchet/Desktop/Codex Ratchet/system_v4/a1_state/skill_registry_v1.json`
  - expected source path:
    - `/home/ratchet/Desktop/Codex Ratchet/system_v4/skills/pimono_evermem_adapter.py`
  - current status: `REGISTRY_PRESENT`, `FILE_MISSING`

### D. Runtime substrate files that matter even when not phase-dispatched by skill id

- `/home/ratchet/Desktop/Codex Ratchet/system_v4/skills/runtime_state_kernel.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v4/skills/witness_recorder.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v4/skills/runtime_graph_bridge.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v4/skills/a2_graph_refinery.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v4/skills/intent_refinement_graph_builder.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v4/skills/intent_runtime_policy.py`

## Graph / Registry State

- current registry file:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v4/a1_state/skill_registry_v1.json`
- counted directly from JSON in this pass:
  - `88` total skill records
  - `82` records explicitly marked `status: active`
  - `6` records missing `status`
- the `6` missing-status records are:
  - `autoresearch-operator`
  - `llm-council-operator`
  - `skill-improver-operator`
  - `evermem-memory-backend-adapter`
  - `witness-evermem-sync`
  - `pimono-evermem-adapter`

- last saved graph capability audit:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.json`
  - reports `82` active graphed skills and `37` single-edge skill nodes

Current truth:

- the graph capability audit is consistent with the `82` active subset
- the mismatch is between total registry rows and explicit active rows, not between the audit and the active subset
- the registry tail block with missing `status` metadata is the real drift source

## Layer / Placement Notes

- nested graph currently projects `11` layers in:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v4/a2_state/graphs/nested_graph_v1.json`
- broad intended placement:
  - `29 thing.txt` and Lev runtime design doc:
    - source/doc layer, then graph-mined into A2 families
  - Z3 / CEGIS / property / fuzz / model-check families:
    - verification and simulation lanes
  - `autoresearch`:
    - `A2_MID_REFINEMENT` exploration/improvement lane
  - `llm-council`:
    - `B_ADJUDICATED` ensemble/adjudication lane
  - EverMem sync/adapters:
    - witness, A2 memory, and low-control adapter lanes
  - pi-mono adapters:
    - external integration / agent-memory bridge lane
  - MSA:
    - later backend/model capability lane, not first integration target

## Immediate Repair Queue

1. Repair the `status` field on the 6 new registry entries so they stop drifting out of active-count surfaces.
2. Implement or remove the broken `pimono-evermem-adapter` registry stub.
3. Verify live runtime wiring for `evermem-memory-backend-adapter` and `witness-evermem-sync`.
4. Do a method-by-method verified pass for the 29 methods in `29 thing.txt`, replacing any aspirational cross-reference claims with checked registry/hot-path status.
5. Append every newly referenced repo or skill family here first, then update supporting surfaces second.

## Append Protocol

When a new repo, method bundle, or skill family is referenced:

1. append it to this file first
2. record the exact path or URL
3. record which category it belongs to:
   - source doc
   - external repo family
   - staged bundle
   - registry skill
   - runtime substrate
4. record only verified statuses
5. if there is uncertainty, mark it explicitly as `UNVERIFIED_MAP` or `STALE_AUDIT_MISMATCH`
6. only after that, update supporting staging/audit/planning surfaces

Never do these again:

- do not substitute a graph artifact for an explicit source doc
- do not call a pattern "saved" if it is not in this ledger
- do not call a skill "live" unless registry and runtime evidence support it
- do not let a derived cross-reference note outrank the source doc or this ledger

## Append Log

### 2026-03-21

- established this file as the canonical durable integration ledger
- corrected the canonical 29-method source referent to `29 thing.txt`
- recorded the registry tail-block mismatch (`88` total rows vs `82` explicitly active)
- recorded current EverMem/pi-mono adapter state, including the missing `pimono_evermem_adapter.py` file
