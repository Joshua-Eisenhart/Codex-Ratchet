# SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1
Status: PROPOSED / NONCANONICAL / ACTIVE CONTROL SURFACE
Date: 2026-03-21
Role: Keep A2/A1 memory surfaces from drifting into fake truth

## 1) Purpose
This file defines:
- surface classes
- source precedence
- A2/A1 write permissions
- memory admission checks
- active-surface pressure rules

It is an upper-layer guard.
It does not replace the lower-loop truth path.

March 21, 2026 maintenance note:
- selector-only lev post-skeleton reports and packets stay `DERIVED_A2`
- disposition-only lev post-skeleton reports and packets stay `DERIVED_A2`
- future-lane-existence lev post-skeleton reports and packets stay `DERIVED_A2`
- they do not become `PROPOSAL_A1`, `PACKAGED_A0`, `EARNED_STATE`, or runtime proof just because a selector slice is landed

March 22, 2026 reselection note:
- source-family lane-selection reports and packets stay `DERIVED_A2`
- landed first-slice runtime-proof reports and packets for the Karpathy family also stay `DERIVED_A2`
- they do not become runtime-live, `PROPOSAL_A1`, or controller permission for automatic widening just because the proof report is `ok`
- the selector recommendation does not become `PROPOSAL_A1` or `A2_TO_A1` consequence by itself
- if `A1` remains `NO_WORK`, do not mint a fresh `A2_TO_A1` impact note just because controller routing became more explicit
- freshness anchor:
  - `A2_UPDATE_NOTE__CONTEXT_SPEC_WORKFLOW_LANDING_AND_RESELECTION__2026_03_22__v1.md`

## 2) Surface Classes
- `SOURCE_CORPUS`
  - immutable source documents and source evidence surfaces
- `DERIVED_A2`
  - A2 understanding, maps, summaries, conflict records
- `PROPOSAL_A1`
  - A1 branch families, rescue plans, negative-class maps, strategy memory
- `PACKAGED_A0`
  - compile-ready A0 packaging artifacts
- `EVIDENCE_SIM`
  - SIM evidence and associated replayable results
- `EARNED_STATE`
  - lower-loop-earned state only
- `RUNTIME_ONLY`
  - transient run-local surfaces, prompts, temporary indexes, live scratch outputs
- `ARCHIVE_ONLY`
  - historical or archived surfaces kept for provenance, not active reload

## 3) Hard Interpretation Rules
- `EARNED_STATE` is not the same thing as `SOURCE_CORPUS`
- document-local authority labels do not elevate a surface out of its class
- derived surfaces do not become source corpus just because they are useful
- validated lower-loop state outranks all upper-loop summaries

## 4) Source Precedence
Conflict resolution order:
1. `EARNED_STATE`
2. `EVIDENCE_SIM`
3. `SOURCE_CORPUS`
4. `PACKAGED_A0`
5. `PROPOSAL_A1`
6. `DERIVED_A2`
7. `RUNTIME_ONLY`
8. `ARCHIVE_ONLY`

Interpretation rule:
- if a derived or proposal surface conflicts with source corpus or earned lower-loop state, the higher-precedence surface wins automatically

## 5) Layer Read / Write Permissions
### A2
- may read: `SOURCE_CORPUS`, `DERIVED_A2`, `PROPOSAL_A1`, `EVIDENCE_SIM`, `EARNED_STATE`, `RUNTIME_ONLY`, `ARCHIVE_ONLY`
- may write: `DERIVED_A2`

### A1
- may read: `SOURCE_CORPUS`, `DERIVED_A2`, `PROPOSAL_A1`, `EVIDENCE_SIM`, `EARNED_STATE`
- may write: `PROPOSAL_A1`

### A0
- may read: `SOURCE_CORPUS`, `PROPOSAL_A1`
- may write: `PACKAGED_A0`

### B
- may read: `PACKAGED_A0`, `EVIDENCE_SIM`
- may write: `EARNED_STATE`

### SIM
- may read: `PACKAGED_A0`, `EARNED_STATE` as needed for replay/support
- may write: `EVIDENCE_SIM`

## 6) A2/A1 Memory Admission Checks
Before a surface enters active A2/A1 memory, require:
1. schema / shape validity
2. explicit surface class
3. layer permission validity
4. source references or explicit runtime provenance
5. append-only / provenance-safe write path
6. semantic hygiene:
   - no fake canon labels
   - no truth-sounding A1 proposal naming
   - no source/derived class confusion

If any check fails:
- reject from active memory
- or demote to `RUNTIME_ONLY` / `ARCHIVE_ONLY`

## 6.1) Current Report And Packet Rule

Recent `system_v4` maintenance skills now emit repo-held current reports and packets, including:

- `A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1`
- `A2_TRACKED_WORK_STATE__CURRENT__v1`
- `A2_RESEARCH_DELIBERATION_REPORT__CURRENT__v1`
- `A2_WORKSHOP_ANALYSIS_GATE_REPORT__CURRENT__v1`
- `A2_PIMONO_OUTSIDE_SESSION_HOST_REPORT__CURRENT__v1`
- `EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1`
- `SKILL_IMPROVER_READINESS_REPORT__CURRENT__v1`
- `SKILL_IMPROVER_DRY_RUN_REPORT__CURRENT__v1`
- `SKILL_IMPROVER_FIRST_TARGET_PROOF_REPORT__CURRENT__v1`
- `WITNESS_MEMORY_RETRIEVER_REPORT__CURRENT__v1`
- `A2_LEV_AGENTS_PROMOTION_REPORT__CURRENT__v1`

Working rule:

- these are useful current-truth companions
- they are not canonical A2 owner surfaces by default
- they should be treated as `DERIVED_A2` or `RUNTIME_ONLY` companions depending on role
- they may steer maintenance and refresh work
- they may not auto-promote themselves into standing A2 truth without explicit patching/distillation

Current companion-surface clarification:

- directly indexed root corpus docs remain easy human-facing `SOURCE_CORPUS` helpers
- repo-held current audit reports are not a permission slip to mutate canonical A2
- `a2-brain-surface-refresher` is the current explicit example:
  - real skill
  - real repo-held report
  - still audit-only
- `a2-workshop-analysis-gate-operator` now joins that companion class:
  - real skill
  - real repo-held report + packet
- `outside-control-shell-operator` now joins that companion class:
  - real skill
  - real repo-held report + packet
  - still read-only and non-promotional
  - still audit-only and non-promotional
- `a2-skill-improver-readiness-operator` now joins that companion class:
  - real skill
  - real repo-held report + packet
  - still audit-only and non-promotional
  - a readiness gate, not a live mutator
- `a2-skill-improver-dry-run-operator` now joins that companion class:
  - real skill
  - real repo-held report + packet
  - still dry-run-only and non-promotional
- `witness-memory-retriever` now joins that companion class:
  - real skill
  - real repo-held report + packet
  - still bounded witness retrieval only
  - not a startup/bootstrap or broader memory permission slip
  - current gate truth for this lane is `hold_at_retrieval_probe`
- `a2-evermem-backend-reachability-audit-operator` now joins that companion class:
  - real skill
  - real repo-held report + packet
  - still bounded backend-reachability audit only
  - current gate truth for this lane is `start_docker_daemon`
  - neither EverMem lane authorizes startup/bootstrap, pi-mono memory, or A2 replacement claims
- `A2_TRACKED_WORK_STATE__CURRENT__v1` is also a companion surface:
  - it should report the tracked-work slice as current
  - it should not recursively nominate `a2-tracked-work-operator` as the next first slice inside the same cluster
- `A2_LEV_AGENTS_PROMOTION_REPORT__CURRENT__v1` is also a companion surface:
  - it may mark `SKILL_CLUSTER::lev-formalization-placement` as landed and parked at disposition
  - it may nominate `a2-lev-autodev-loop-audit-operator` as the next bounded candidate
  - it still does not authorize runtime-live import, migration, or imported ownership claims
- `a2-skill-improver-target-selector-operator` now joins that companion class:
  - real skill
  - real repo-held report + packet
  - still audit-only and non-promotional
  - owns first-target selection only
- latest refresher-read nuance:
  - the current refresher report may still legitimately be `attention_required` on freshness only
  - that means standing A2 surfaces lag the latest evidence
  - it does not mean the report auto-promotes itself into canonical A2
- refresher-loop hygiene rule:
  - the refresher's own current report and packet are `DERIVED_A2` audit companions
  - they should not be treated as self-justifying "latest evidence" for freshness grading of standing A2 surfaces

## 7) Active-Surface Pressure Rules
Negative pressure here does not mean authority “decay” by vibe.
It means structural demotion from active reload surfaces.

Apply these rules:
- `RUNTIME_ONLY` surfaces do not persist into standing A2/A1 understanding unless explicitly distilled
- `DERIVED_A2` surfaces do not auto-reload unless selected by active indices or source refs
- stale derived surfaces should point forward to newer owner surfaces or be demoted
- `ARCHIVE_ONLY` surfaces remain readable but are excluded from active default reload
- summaries and indexes must not outrank their source refs

## 8) Graveyard Topology Interaction
Graveyard cluster maps are `DERIVED_A2` / `PROPOSAL_A1` control surfaces.
They may:
- organize failure classes
- steer pruning
- steer negative-sim reuse
- highlight sparse frontier regions

They may not:
- promote truth
- rewrite earned state
- replace lower-loop evidence

## 8.1) Holodeck Surface Rule
Holodeck-derived surfaces are outer memory/world-model surfaces.

Default class:
- `DERIVED_A2` when distilled into active understanding
- otherwise `RUNTIME_ONLY` or `ARCHIVE_ONLY`

They must not:
- directly promote ontology
- bypass A2 into A1/A0/B/SIM
- be treated as source corpus unless independently re-authored as source-bound active docs

## 8.2) SIM-Ladder Surface Rule
Tiered SIM surfaces are evidence-construction surfaces.

They may:
- bind executable pressure to B-admitted structure
- provide positive and negative evidence
- support promotion through explicit tier contracts

They may not:
- independently elevate ontology without the structural ladder
- replace source corpus
- bypass earned-state rules by simulation rhetoric alone

## 9) Purpose
This file exists to prevent:
- semantic elevation drift
- source/derived confusion
- A2/A1 self-summary recursion
- active-surface creep

It keeps upper memory disciplined while preserving the lower loop as the only earning path.

## Update — March 21, 2026

- `OUTER_SESSION_LEDGER_STATE__CURRENT__v1.json`, `OUTER_SESSION_LEDGER_EVENTS__APPEND_ONLY__v1.jsonl`, and the paired report surfaces are derived continuity/audit surfaces.
- They are admissible as repo-held observer outputs, not as canonical owner-law replacement surfaces.
- `SKILL_IMPROVER_FIRST_TARGET_PROOF_REPORT__CURRENT__v1` and its packet are derived proof surfaces.
- They show one bounded proven target, not general permission for live repo mutation.
- `A2_LEV_AGENTS_PROMOTION_REPORT__CURRENT__v1` and its packet are derived promotion-audit surfaces.
- They recommend one next lev-os/agents cluster; they do not imply that cluster is already imported or runtime-live.
- `A2_LEV_BUILDER_PLACEMENT_AUDIT_REPORT__CURRENT__v1` and its packet are derived placement-audit surfaces.
- They show one bounded landed audit slice inside `SKILL_CLUSTER::lev-formalization-placement`; they do not imply migration, formalization completion, or imported runtime ownership.
- `A2_LEV_BUILDER_FORMALIZATION_PROPOSAL_REPORT__CURRENT__v1` and its packet are derived proposal surfaces.
- They show one bounded landed proposal slice inside `SKILL_CLUSTER::lev-formalization-placement`; they do not imply formalization completion, migration permission, or imported runtime ownership.
- `A2_LEV_BUILDER_FORMALIZATION_SKELETON_REPORT__CURRENT__v1` and its packet are derived scaffold-proof surfaces.
- They show one bounded landed scaffold slice inside `SKILL_CLUSTER::lev-formalization-placement`; they do not imply runtime-live status, migration permission, formalization completion, or imported runtime ownership.

## Update — March 22, 2026

- `A2_UPDATE_NOTE__LEV_AUTODEV_LANDING_AND_NEXT_CLUSTER_SHIFT__2026_03_22__v1` is admitted as `DERIVED_A2`.
- `A2_TO_A1_IMPACT_NOTE__LEV_AUTODEV_LANDING_AND_NEXT_CLUSTER_SHIFT__2026_03_22__v1` is admitted as `DERIVED_A2` support for the current A2->A1 boundary, not as direct queue-opening permission.
- current refresher-loop consequence:
  - when standing A2 is behind newer repo-held evidence, patch the standing owner surfaces directly
  - do not treat the latest audit report alone as canonical-A2 convergence

## Update — March 22, 2026 (architecture-fitness landing and selector hold)

- `A2_UPDATE_NOTE__LEV_ARCHITECTURE_FITNESS_LANDING_AND_SELECTOR_HOLD__2026_03_22__v1` is admitted as `DERIVED_A2`.
- `A2_TO_A1_IMPACT_NOTE__LEV_ARCHITECTURE_FITNESS_LANDING_AND_SELECTOR_HOLD__2026_03_22__v1` is admitted as `DERIVED_A2` support for the current A2->A1 boundary, not as direct queue-opening permission.
- current refresher-loop consequence:
  - when a newly landed imported slice eliminates the current unopened lev candidate, patch the standing owner surfaces directly
  - do not treat `has_current_unopened_cluster = False` as permission to invent a default replacement next move

## Update — March 22, 2026 (next-state directive probe landing)

- `A2_UPDATE_NOTE__NEXT_STATE_DIRECTIVE_PROBE_LANDING__2026_03_22__v1` is admitted as `DERIVED_A2`.
- `A2_TO_A1_IMPACT_NOTE__NEXT_STATE_DIRECTIVE_PROBE_LANDING__2026_03_22__v1` is admitted as `DERIVED_A2` support for the current A2->A1 boundary, not as direct queue-opening permission.
- current refresher-loop consequence:
  - when a newly landed source-family probe reveals weak witness quality, patch the standing owner surfaces directly
  - do not treat a landed probe as proof that the deeper live-learning seam is already earned
## 2026-03-22 Admission Reminder

- The `skill-improver` second-target landing is admissible as `DERIVED_A2` maintenance truth because it is source-bound to live repo-held reports and remains fail-closed.
- The correct memory consequence is to preserve the current hold result, not to imply broader live mutation permission.
- Front-door corpus wording now matches the same fail-closed admission consequence.
- The next-state witness-batch advance is likewise admissible as `DERIVED_A2` because it is grounded in repo-held witness entries and probe outputs, while still remaining audit-only.
## 2026-03-22 Next-State Bridge Admission Reminder

- `A2_UPDATE_NOTE__NEXT_STATE_CONTEXT_BRIDGE_LANDING__2026_03_22__v1` is admitted as `DERIVED_A2`.
- `A2_TO_A1_IMPACT_NOTE__NEXT_STATE_CONTEXT_BRIDGE_LANDING__2026_03_22__v1` is admitted as `DERIVED_A2` support for the current A2->A1 boundary, not as queue-opening permission.
- The landed bridge packet remains audit-only and first-target-context-only; it does not change lower-loop truth class or authorize mutation by wording alone.

## 2026-03-22 Next-State Consumer Admission Reminder

- `A2_UPDATE_NOTE__NEXT_STATE_CONSUMER_CONTRACT_LANDING__2026_03_22__v1` is admitted as `DERIVED_A2`.
- `A2_TO_A1_IMPACT_NOTE__NEXT_STATE_CONSUMER_CONTRACT_LANDING__2026_03_22__v1` is admitted as `DERIVED_A2` support for the current A2->A1 boundary, not as queue-opening permission.
- The landed consumer-audit packet now confirms an explicit owner contract, but it still does not authorize a runtime-live consumer path by wording alone.

## 2026-03-22 Edge Payload Probe Admission Reminder

- `A2_UPDATE_NOTE__EDGE_PAYLOAD_SCHEMA_PROBE_LANDING__2026_03_22__v1` is admitted as `DERIVED_A2`.
- `A2_UPDATE_NOTE__GRAPH_CONTROL_TRANCHE_HOLD__2026_03_22__v1` is likewise admissible as `DERIVED_A2`.
- The landed graph-side probe remains sidecar-only and does not authorize canonical graph writes, training, or runtime mutation by wording alone.
- A repo-held graph/control sidecar tranche does not become active runtime skill truth until it is explicitly admitted into the live registry/dispatch path.

## 2026-03-22 Next-State Consumer Proof Admission Reminder

- `A2_UPDATE_NOTE__NEXT_STATE_CONTEXT_CONSUMER_PROOF_LANDING__2026_03_22__v1` is admitted as `DERIVED_A2`.
- `A2_TO_A1_IMPACT_NOTE__NEXT_STATE_CONTEXT_CONSUMER_PROOF_LANDING__2026_03_22__v1` is admitted as `DERIVED_A2` support for the current A2->A1 boundary, not as queue-opening permission.
- The landed proof packet remains metadata-only / dry-run / no-write and does not authorize a runtime-live consumer path or broader mutation authority by wording alone.

## 2026-03-22 Context Spec Follow-On Selector Admission Reminder

- `A2_UPDATE_NOTE__CONTEXT_SPEC_FOLLOW_ON_SELECTOR_LANDING__2026_03_22__v1` is admitted as `DERIVED_A2`.
- `A2_TO_A1_IMPACT_NOTE__CONTEXT_SPEC_FOLLOW_ON_SELECTOR_LANDING__2026_03_22__v1` is admitted as `DERIVED_A2` support for the current A2->A1 boundary, not as queue-opening permission.
- The landed selector packet does not authorize a landed append-safe audit, multi-pattern widening, canonical brain replacement, or graph-substrate replacement by wording alone.

## 2026-03-22 Append Safe Context Shell Audit Admission Reminder

- `A2_UPDATE_NOTE__APPEND_SAFE_CONTEXT_SHELL_AUDIT_LANDING__2026_03_22__v1` is admitted as `DERIVED_A2`.
- `A2_TO_A1_IMPACT_NOTE__APPEND_SAFE_CONTEXT_SHELL_AUDIT_LANDING__2026_03_22__v1` is admitted as `DERIVED_A2` support for the current A2->A1 boundary, not as queue-opening permission.
- The landed append-safe audit packet does not authorize canonical brain replacement, new owner-surface family creation, memory-platform ownership, or background session-manager authority by wording alone.

## 2026-03-22 Context Spec Post-Shell Selector Admission Reminder

- `A2_UPDATE_NOTE__CONTEXT_SPEC_POST_SHELL_SELECTOR_LANDING__2026_03_22__v1` is admitted as `DERIVED_A2`.
- `A2_TO_A1_IMPACT_NOTE__CONTEXT_SPEC_POST_SHELL_SELECTOR_LANDING__2026_03_22__v1` is admitted as `DERIVED_A2` support for the current A2->A1 boundary, not as queue-opening permission.
- The landed post-shell selector packet does not authorize automatic progression to executable-spec-coupling, multi-pattern widening, canonical brain replacement, or memory-platform ownership by wording alone.
