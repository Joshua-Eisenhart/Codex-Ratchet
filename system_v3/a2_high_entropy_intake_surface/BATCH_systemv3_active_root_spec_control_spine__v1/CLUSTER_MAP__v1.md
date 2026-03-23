# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_systemv3_active_root_spec_control_spine__v1`
Extraction mode: `ACTIVE_CONTROL_SPINE_PASS`
Date: 2026-03-09

## Cluster A: `SURFACE_ENTRYPOINT_AND_REPO_SHAPE`
- source members:
  - `00_CANONICAL_ENTRYPOINTS_v1.md`
  - `01_OPERATIONS_RUNBOOK_v1.md`
  - `02_SAFE_DELETE_SURFACE_v1.md`
  - `03_EXPLICIT_NAME_ALIAS_SURFACE_v1.md`
  - `WORKSPACE_LAYOUT_v1.md`
- reusable payload:
  - explicit runtime entrypoints and guard scripts
  - canonical-vs-derived-vs-archive surface placement
  - demotion-first cleanup discipline
  - alias compatibility semantics
  - no-new-roots and default write-surface rules
- quarantine note:
  - this cluster is operational guidance, not full contract authority by itself
  - write-surface policy appears older than the now-active intake workflow
- possible downstream consequence:
  - useful as the first repo-shape classifier packet before any cleanup, archive, or runtime mutation task

## Cluster B: `OWNER_MODEL_LAYER_STACK`
- source members:
  - `specs/00_MANIFEST.md`
  - `specs/01_REQUIREMENTS_LEDGER.md`
  - `specs/02_OWNERSHIP_MAP.md`
  - `specs/03_B_KERNEL_SPEC.md`
  - `specs/04_A0_COMPILER_SPEC.md`
  - `specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`
  - `specs/06_SIM_EVIDENCE_AND_TIERS_SPEC.md`
  - `specs/07_A2_OPERATIONS_SPEC.md`
- reusable payload:
  - one-owner requirement discipline
  - layer contract map `A2 -> A1 -> A0 -> B` plus `SIM`
  - single mutation path and evidence obligations
  - explicit A2-first upstream control role
- quarantine note:
  - nearly every doc here still self-labels as draft/noncanon even while clearly acting as the active contract spine
  - the owner-model layer stack is strong but not semantically flattened
- possible downstream consequence:
  - best seed packet for later A2-mid control-spine reduction

## Cluster C: `FLOW_GOVERNANCE_AND_MIGRATION`
- source members:
  - `specs/08_PIPELINE_AND_STATE_FLOW_SPEC.md`
  - `specs/09_CONFORMANCE_AND_REDUNDANCY_GATES.md`
  - `specs/10_INITIAL_AUDIT_REPORT.md`
  - `specs/11_MIGRATION_HANDOFF_SPEC.md`
  - `specs/12_BOOTPACK_SYNC_AUDIT_SPEC.md`
  - `specs/13_CONTENT_REDUNDANCY_LINT_SPEC.md`
  - `specs/14_A_THREAD_BOOTPACK_PROJECTION.md`
  - `specs/15_ROSETTA_AND_MINING_ARTIFACTS.md`
- reusable payload:
  - end-to-end loop description
  - promotion gate stack and anti-paperclip controls
  - legacy migration rules
  - bootpack drift audit requirements
  - helper projection of A-thread discipline
  - explicit A2-miner / A1-rosetta helper artifact families
- quarantine note:
  - `10_INITIAL_AUDIT_REPORT.md` is a self-report, not independent evidence
  - `14` and `15` are helper projections/artifact-shape docs, not owner-law replacements
- possible downstream consequence:
  - later passes should compare this governance packet against actual tools, fixtures, and runtime tests rather than promoting it by rhetoric alone

## Cluster D: `TRANSPORT_AND_PERSISTENCE_HARDENING`
- source members:
  - `specs/16_ZIP_SAVE_AND_TAPES_SPEC.md`
  - `specs/17_BOOTPACK_THREAD_B_v3.9.13_ENFORCEABLE_CONTRACT_EXTRACT_FOR_IMPLEMENTATION_v1.md`
  - `specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md`
  - `specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md`
  - `specs/ZIP_PROTOCOL_v2.md`
- reusable payload:
  - exact ZIP transport rules
  - broad save/tape and witness/compaction doctrine
  - detailed A1 wiggle operator micro-contract
  - detailed A2 schema/seal/shard micro-contract
  - bootpack-B helper extract for implementation-facing enforcement
- quarantine note:
  - `ZIP_PROTOCOL_v2.md` is the strictest transport surface in this cluster
  - `16` broadens into operational packaging language
  - `17` remains a non-owner helper extract
- possible downstream consequence:
  - high-value comparison target for `runtime/`, `control_plane_bundle_work/`, and active `a2_state/` files in later passes

## Cross-Cluster Couplings
- Cluster A places surfaces; Cluster B assigns layer roles and owner rules.
- Cluster C governs when Cluster B material is safe to promote or audit.
- Cluster D defines how Cluster B outputs cross boundaries and how A2/A1 persistence should be recorded.
- current best read:
  - active system understanding is spread across these clusters rather than localized in one small spec file
  - that spread is productive but also one of the main drift risks preserved in this batch
