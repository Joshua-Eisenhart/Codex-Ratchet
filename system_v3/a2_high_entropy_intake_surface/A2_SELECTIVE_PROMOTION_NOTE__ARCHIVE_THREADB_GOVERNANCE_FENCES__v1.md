Status: PROPOSED / NONCANONICAL / BOUNDED SELECTIVE-PROMOTION NOTE
Date: 2026-03-09

# Scope

This note reduces the smallest safe governance-fence subset from:

- `BATCH_A2MID_archive_batch05_mint_boundary_fences__v1`
- `BATCH_A2MID_archive_batch06_upgrade_control_fences__v1`
- `BATCH_A2MID_archive_batch07_audit_gap_zip_taxonomy_fences__v1`
- `BATCH_A2MID_a2feed_thread_b_provenance_admission_fences__v1`

The goal is to extract only narrow process and boundary consequences for later A2 review.

# Smallest safe promotion candidates

## PROCESS_RULE

- `ARCHIVE_OUTPUT_PACKETS_ARE_HISTORY_GRADE_NOT_PRIMARY_AUTHORITY`
  Reason:
  output-only retained packages preserve useful result lineage, but absent payload, shard, meta-seed, and schema supports prevent them from acting as self-sufficient authority bundles.

- `VALIDATION_PASS_WITH_EXTERNAL_SCHEMAS_IS_WEAKER_THAN_BUNDLE_CONTAINED_VALIDATION`
  Reason:
  stage pass signals remain useful, but they must not be treated as equivalent to in-bundle schema closure.

- `AUDIT_ONLY_EXTRACTION_MUST_NOT_DRIFT_INTO_REDESIGN_AUTHORITY`
  Reason:
  archive audit material repeatedly shows that over-auditing can become redesign/smoothing drift unless kept explicitly history-grade.

## BOUNDARY_RULE

- `ZIP_TAXONOMY_GROWTH_DOES_NOT_EQUAL_OPERATIONAL_CLOSURE`
  Reason:
  named ZIP kinds and logistics vocabulary are useful, but confirmation semantics, invalidation rules, and artifact boundaries remain unresolved.

- `THREAD_B_CHANGE_REQUIRES_DECLARED_ADMISSION_GRAMMAR`
  Reason:
  Thread B forbids conversational inference and repair while still allowing controlled change through explicit staged admission.

- `THREAD_B_VOCABULARY_ACCESS_IS_CURRENTLY_GATED_NOT_PERMANENTLY_BANNED`
  Reason:
  the source rejects primitive use of selected terms until admission conditions are met, but does not support a permanent-word-ban reading.

- `THREAD_B_SIM_AUTHORITY_IS_EXTERNALIZED_NOT_REMOVED`
  Reason:
  Thread B does not run sims, but sim evidence and code-hash matching still govern activation and admission decisions.

- `MINIMAL_INTERFACE_REQUIRES_HEAVY_REPLAY_AND_EVIDENCE_DISCIPLINE`
  Reason:
  small visible interface grammar is only valid because substantial artifact, replay, snapshot, and evidence discipline sits behind it.

## UNRESOLVED_TENSION

- `THREAD_S_INSTABILITY_REMAINS_A_CENTRAL_ARCHITECTURE_CONTRADICTION`
  Reason:
  archive upgrade/control material still preserves unresolved drift between Thread S absorption and Thread S reintroduction.

- `DETERMINISM_BOUNDARY_VS_PROBABILISTIC_CONTROL_REMAINS_OPEN`
  Reason:
  A0/B/SIM are framed as deterministic while A1 confirmation/enforcement semantics remain incompletely settled.

- `SOLE_SOURCE_AUTHORITY_RHETORIC_VS_DISTRIBUTED_ARTIFACT_DEPENDENCE`
  Reason:
  Thread B claims sole-source authority while materially depending on replayable state, accepted snapshots, and adjacent evidence artifacts.

# Explicitly kept out

These remain out of active promotion in this pass:

- megaboot canon vs Thread B sole-source authority closure
- Thread S lane topology finalization
- Thread A no-choice vs option-boxing contradiction
- Jung/IGT/overlay-label synthesis residue
- holodeck uniqueness vs reproducibility conflict
- template/output sharding heuristics
- graveyard exploration vs bounded convergence policy
- version-family closure across `3.4.2`, `3.5.2`, and `3.9.13`

# Promotion discipline

This note is intentionally narrow.

It supports only:

- archive/history-grade package handling
- Thread B admission and provenance fences
- ZIP taxonomy caution
- replay/evidence burden clarity

It does not support:

- archive material as current kernel authority
- Thread B family closure
- new ontology
- controller-lane architecture closure
