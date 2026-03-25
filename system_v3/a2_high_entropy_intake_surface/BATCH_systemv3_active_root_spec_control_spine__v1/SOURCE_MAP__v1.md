# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_systemv3_active_root_spec_control_spine__v1`
Extraction mode: `ACTIVE_CONTROL_SPINE_PASS`
Batch scope: first bounded pass over prioritized active low-entropy `system_v3` source surfaces: top-level system docs, `specs/00..19`, and `specs/ZIP_PROTOCOL_v2.md`
Date: 2026-03-09

## 1) Folder-Order Selection
- fresh thread bootstrapped from repo files only
- excluded from this assignment and not processed here:
  - `system_v3/runs/`
  - `system_v3/a2_high_entropy_intake_surface/`
  - `system_v3/run_anchor_surface/`
- prioritized source families for this worker lane:
  - `system_v3/specs/`
  - top-level system docs under `system_v3/`
  - active A2/A1/control-plane/public/conformance surfaces later
- first bounded batch selected:
  - top-level active docs:
    - `00_CANONICAL_ENTRYPOINTS_v1.md`
    - `01_OPERATIONS_RUNBOOK_v1.md`
    - `02_SAFE_DELETE_SURFACE_v1.md`
    - `03_EXPLICIT_NAME_ALIAS_SURFACE_v1.md`
    - `WORKSPACE_LAYOUT_v1.md`
  - `system_v3/specs/00..19`
  - `system_v3/specs/ZIP_PROTOCOL_v2.md`
- bundling reason:
  - these files collectively define the active repo-shape map, layer-role contract spine, transport boundary, persistence contract, and promotion/audit governance packet
  - they are low-entropy enough to compress together without losing source lineage
  - `ZIP_PROTOCOL_v2.md` is included now because the intake process names it as a governing input and the early specs repeatedly lean on its exact transport contract
- deferred next docs in folder order:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/20_CONTROLLED_TUNING_AND_UPGRADE_CONTRACT.md`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/21_IMPLEMENTATION_BUILD_SEQUENCE_AND_ACCEPTANCE_MATRIX.md`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/22_RUN_SURFACE_TEMPLATE_AND_SCAFFOLDER_CONTRACT.md`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/23_BOOTPACK_CONFORMANCE_FIXTURE_MATRIX_CONTRACT.md`

## 2) Source Membership By Family
- root active docs:
  - entrypoints, runbook, safe-delete policy, alias mapping, workspace layout
- spec spine seed:
  - spec manifest, requirements ledger, ownership map
- owner-layer contract set:
  - B owner spec
  - A0 owner spec
  - A1 owner spec
  - SIM owner spec
  - A2 owner spec
- flow and governance set:
  - pipeline/state flow
  - conformance gates
  - initial audit report
  - migration handoff
  - bootpack sync audit
  - redundancy lint
  - A-thread projection
  - rosetta/mining artifact shapes
- transport and persistence companions:
  - ZIP/save/tapes operational contract
  - bootpack-B enforceable extract
  - A1 wiggle micro-contract
  - A2 persistence/seal micro-contract
  - exact `ZIP_PROTOCOL_v2` transport contract
- full hashes, sizes, and line counts are preserved in `MANIFEST.json`

## 3) Root Active Docs
- entrypoint and runbook packet:
  - `00_CANONICAL_ENTRYPOINTS_v1.md:8-36`
  - `01_OPERATIONS_RUNBOOK_v1.md:5-62`
  - defines canonical runtime executables, canonical state/spec surfaces, guard scripts, save builders, and expected run outputs
- repo-shape and mutation-hygiene packet:
  - `02_SAFE_DELETE_SURFACE_v1.md:8-52`
  - `03_EXPLICIT_NAME_ALIAS_SURFACE_v1.md:1-34`
  - `WORKSPACE_LAYOUT_v1.md:9-37`
  - defines demotion-before-delete, explicit alias semantics, no-new-roots discipline, and default write-surface policy
- source-class read:
  - active operator docs
  - not the full owner-model spec spine by themselves
  - useful for repo-shape classification and mutation restraint

## 4) Foundational Owner Spine
- manifest / ledger / ownership packet:
  - `specs/00_MANIFEST.md:15-48` sets deterministic read order and one-owner intent
  - `specs/01_REQUIREMENTS_LEDGER.md:5-161` enumerates `RQ-*` across root constraints, layers, governance, tuning, run templates, conformance, and ZIP/save/tape
  - `specs/02_OWNERSHIP_MAP.md:9-40` binds most `RQ-*` ranges to owner docs and demotes `specs/17...` to non-owner helper status
- owner-layer packet:
  - `specs/03_B_KERNEL_SPEC.md:16-171` defines allowed containers, tag fence, grammar, deterministic stage order, graveyard write contract, and state invariants
  - `specs/04_A0_COMPILER_SPEC.md:23-221` defines canonicalization, compile preflight, deterministic ordering, truncation, header gates, and packet-first persistence
  - `specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md:17-281` defines strategy-only output, cold-core plus reattachment rosetta split, compile-ready candidate objects, branch scheduler, repair loop, and fix-intent schema
  - `specs/06_SIM_EVIDENCE_AND_TIERS_SPEC.md:30-126` defines the evidence bar, tier/stress families, negative sim shape, and promotion-deficit reporting
  - `specs/07_A2_OPERATIONS_SPEC.md:21-308` defines persistent brain interfaces, contradiction handling, active update/audit/gating loop, fresh-thread controller/worker pattern, and append-first safety

## 5) Governance, Migration, And Projection Cluster
- `specs/08_PIPELINE_AND_STATE_FLOW_SPEC.md:5-92`
  - end-to-end loop and suggested run-surface contract
- `specs/09_CONFORMANCE_AND_REDUNDANCY_GATES.md:6-78`
  - authority coverage, owner/orphan lint, root-constraint protection, drift hash, and promotion-package gates
- `specs/10_INITIAL_AUDIT_REPORT.md:5-65`
  - self-report of what the first spec pass claims to have closed and what still blocks promotion
- `specs/11_MIGRATION_HANDOFF_SPEC.md:16-46`
  - deterministic v2/legacy to v3 migration phases and required artifacts
- `specs/12_BOOTPACK_SYNC_AUDIT_SPEC.md:15-39`
  - required drift check against bootpack authority text
- `specs/13_CONTENT_REDUNDANCY_LINT_SPEC.md:11-31`
  - near-duplicate lint beyond owner-collision checking
- `specs/14_A_THREAD_BOOTPACK_PROJECTION.md:11-52`
  - projects A-thread artifact/tone/glyph discipline into v3 without changing B authority
- `specs/15_ROSETTA_AND_MINING_ARTIFACTS.md:18-79`
  - makes A2-miner and A1-rosetta artifact families explicit as noncanon helper shapes

## 6) Transport And Persistence Companion Cluster
- `specs/16_ZIP_SAVE_AND_TAPES_SPEC.md:17-173`
  - broad operational ZIP carrier framing, save levels, lean resume surfaces, regeneration witness retention, packet compaction, archive demotion, and tape contracts
- `specs/17_BOOTPACK_THREAD_B_v3.9.13_ENFORCEABLE_CONTRACT_EXTRACT_FOR_IMPLEMENTATION_v1.md:26-606`
  - compact bootpack-B helper extract with explicit record of known internal inconsistencies
- `specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md:9-132`
  - detailed operator IDs, quota table, ranking comparator, stall rebalance, and A1 output packet contract
- `specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md:9-176`
  - schema/version gates, seal records, provenance-bearing fuel queue, contradiction registry, and A2 sharding order
- `specs/ZIP_PROTOCOL_v2.md:5-282`
  - exact ZIP header/manifest/hashes/ordering/sequence/allowlist/reject-tag rules with strict no-implicit-defaults and no policy/routing creep

## 7) Source-Class Read
- best classification:
  - active low-entropy source corpus plus adjacent draft helper/governance docs
- strongest direct value:
  - layer-role and mutation-boundary map
  - active A2-first control and persistence packet
  - transport/save/tape law packet
  - promotion, drift, migration, and redundancy governance map
- caution:
  - many files still self-label as `DRAFT / NONCANON`
  - helper extracts and projections are intentionally non-owner surfaces
  - some repo-shape and run-surface guidance is clearly older than the later A2 control refresh already visible elsewhere in `system_v3`
- possible downstream consequence only:
  - later A2-mid reduction can selectively promote boundary rules and drift signatures from this packet
  - this batch must not be treated as permission to rewrite active A2 memory directly
