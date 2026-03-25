# A2_SKILL_SOURCE_INTAKE_PROCEDURE__CURRENT__v1
Status: ACTIVE / DERIVED_A2 / INTAKE COMPANION
Date: 2026-03-21
Role: bounded A2 procedure for admitting new repo/doc/method families into the skill source corpus without losing them or overstating integration

## Why This Exists

The system now has useful human-facing corpus trackers at repo root, but canonical A2 persistence still lives under `system_v3/a2_state`.

This file defines the bridge.

It exists to stop these failures:

- a repeatedly referenced repo or doc never gets durably remembered
- root trackers are mistaken for the canonical A2 brain
- graph presence is mistaken for runtime truth
- source families are mentioned, but never turned into candidate skills or A2 work

## Owner Law

Use with:

- `system_v3/specs/07_A2_OPERATIONS_SPEC.md`
- `system_v3/specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md`
- `system_v3/a2_state/SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1.md`
- `system_v3/a2_state/A2_BOOT_READ_ORDER__CURRENT__v1.md`

## Surface Split

### Front-Door SOURCE_CORPUS Surfaces

These are the easy human-facing append surfaces:

- `/home/ratchet/Desktop/Codex Ratchet/SKILL_SOURCE_CORPUS.md`
- `/home/ratchet/Desktop/Codex Ratchet/REPO_SKILL_INTEGRATION_TRACKER.md`
- `/home/ratchet/Desktop/Codex Ratchet/SKILL_CANDIDATES_BACKLOG.md`
- `/home/ratchet/Desktop/Codex Ratchet/LOCAL_SOURCE_REPO_INVENTORY.md`

They are `SOURCE_CORPUS` helpers.
They are not the canonical A2 brain by themselves.

Current decision:

- these front-door `SOURCE_CORPUS` docs should be indexed directly in `system_v3/a2_state/doc_index.json`
- do not create duplicate shadow A2 mirrors just to make them index-visible
- keep A2-owned companion surfaces for interpretation, routing, and append-safe consequence tracking
- this indexing is now landed fact, not future intent
- current source-family reselection truth is now explicit:
  - `SKILL_CLUSTER::context-spec-workflow-memory` now has four bounded landed slices through the post-shell selector:
    - `a2-context-spec-workflow-pattern-audit-operator`
    - `a2-context-spec-workflow-follow-on-selector-operator`
    - `a2-append-safe-context-shell-audit-operator`
    - `a2-context-spec-workflow-post-shell-selector-operator`
    - current next step: `hold_cluster_after_append_safe_shell`
    - first standby follow-on if explicitly reopened later: `a2-executable-spec-coupling-audit-operator`
  - `SKILL_CLUSTER::karpathy-meta-research-runtime` now also has a first bounded landed slice:
    - `a2-autoresearch-council-runtime-proof-operator`
    - current next step: `hold_first_slice_as_runtime_proof_only`
  - current selector result is now an explicit hold:
    - `selection_state = hold_no_eligible_lane`
    - no bounded source-family lane is currently eligible for explicit reselection
    - `recommended_next_step = hold_all_non_lev_lanes_until_explicit_reopen`
- freshness anchor:
  - `A2_UPDATE_NOTE__AUTORESEARCH_COUNCIL_RUNTIME_PROOF_LANDING_AND_RESELECTION__2026_03_22__v1.md`

### Canonical A2 Representation

These are where A2 should also carry the relevant truth:

- `system_v3/a2_state/doc_index.json`
- `system_v3/a2_state/fuel_queue.json`
- `system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md`
- `system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
- `system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md`
- `system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`

Only promote into the last three when the new source changes understanding, introduces a conflict, or creates a real downstream A1 implication.

Current emitted evidence surfaces that now matter for this lane:

- `system_v4/a2_state/audit_logs/A2_SKILL_SOURCE_INTAKE_REPORT__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/A2_TRACKED_WORK_STATE__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/A2_RESEARCH_DELIBERATION_REPORT__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.json`
- `system_v4/a2_state/audit_logs/A2_BRAIN_SURFACE_REFRESH_REPORT__CURRENT__v1.json`

## Intake Loop

When a new repo, source doc, method family, or architecture family appears:

1. Classify the thing.
   - `SOURCE_CORPUS` family
   - live skill/runtime fact
   - both
2. Append the family to `/home/ratchet/Desktop/Codex Ratchet/SKILL_SOURCE_CORPUS.md`.
3. Record local presence in `/home/ratchet/Desktop/Codex Ratchet/LOCAL_SOURCE_REPO_INVENTORY.md`.
4. Record integration reality in `/home/ratchet/Desktop/Codex Ratchet/REPO_SKILL_INTEGRATION_TRACKER.md`.
5. Record candidate skills in `/home/ratchet/Desktop/Codex Ratchet/SKILL_CANDIDATES_BACKLOG.md`.
6. Append recurring significance and controller consequences to `system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md`.
7. Refresh `doc_index.json` if the source should become visible to canonical A2 indexing.
8. Add a `fuel_queue.json` item if the source creates real A2 work.
9. Distill into source-bound A2 understanding surfaces only if meaning or routing changed.
10. Only then call it `saved`.

## Local Presence Tiers

Keep these explicit:

- `repo_local`
- `home_local`
- `tmp_local`
- `doc_only`
- `url_only`

Do not conflate them.

## Live-Skill Proof Rule

For any claim that something is a real live skill, verify these separately:

1. source tracked
2. raw registry row exists
3. graph identity exists
4. live runtime discovery or dispatch is proven

Do not collapse these into one word like `integrated`.

## Current High-Signal Families

The current intake pressure is highest around:

- `Retooled External Methods`
- `lev-os/agents`
- `lev-os/leviathan`
- local `Leviathan v3.2` source material
- `pi-mono`
- Karpathy family
- Z3 / formal verification family
- EverMem / EverMind / MSA

## Current Practical Rule

If a family is repeatedly referenced and still getting lost, the failure is not “the graph is too small.”

The failure is that the intake loop was not completed.

Run this loop first.
Only after that should graph growth or runtime integration be treated as meaningful progress.

## Current March 21, 2026 Follow-On Rule

The intake loop is no longer the only missing piece.

Current live state:

- front-door corpus docs are directly indexed in canonical A2
- current live skill/graph presence truth is:
  - `113` registry skills
  - `113` graphed `SKILL` nodes
  - `0` missing
  - `0` stale
- native maintenance now has real bounded slices:
  - `a2-brain-surface-refresher`
  - `a2-skill-improver-readiness-operator`
  - `a2-skill-improver-target-selector-operator`
  - `a2-skill-improver-dry-run-operator`
  - `a2-skill-improver-first-target-proof-operator`
  - `a2-lev-agents-promotion-operator`
  - current readiness verdict:
    - `skill-improver-operator` is `bounded_ready_for_first_target`
  - current bounded proof truth:
    - one selected first target is now proven
  - current EverMem truth:
    - `witness-evermem-sync` remains the durable sync seam
    - `witness-memory-retriever` is now landed as the bounded retrieval seam
    - `a2-evermem-backend-reachability-audit-operator` is now landed as the bounded backend-reachability seam
    - current retrieval result is `attention_required`
    - bounded next step is `hold_at_retrieval_probe`
    - current backend-reachability result is `attention_required`
    - bounded next step there is `start_docker_daemon`
    - keep EverMem as a side project unless local backend reachability is actually earned
  - current lev-os/agents promotion truth:
    - `SKILL_CLUSTER::lev-formalization-placement` now has seven bounded landed slices:
      - `a2-lev-builder-placement-audit-operator`
      - `a2-lev-builder-formalization-proposal-operator`
      - `a2-lev-builder-formalization-skeleton-operator`
      - `a2-lev-builder-post-skeleton-readiness-operator`
      - `a2-lev-builder-post-skeleton-follow-on-selector-operator`
      - `a2-lev-builder-post-skeleton-disposition-audit-operator`
      - `a2-lev-builder-post-skeleton-future-lane-existence-audit-operator`
    - refreshed selector truth now treats that cluster as landed and parked
    - `SKILL_CLUSTER::lev-autodev-exec-validation` now has its first bounded landed slice:
      - `a2-lev-autodev-loop-audit-operator`
    - keep that autodev slice audit-only / nonoperative / non-runtime-live
    - `SKILL_CLUSTER::lev-architecture-fitness-review` now has its first bounded landed slice:
      - `a2-lev-architecture-fitness-operator`
    - current lev selector state is:
      - `landed_lev_cluster_count = 7`
      - `parked_lev_cluster_count = 1`
      - `has_current_unopened_cluster = False`
  - tracked-work truth is now normalized:
    - `a2-tracked-work-operator` reports the tracked-work slice as current instead of recursively naming itself as next
  - the lev selector refresh is now landed
  - if imported work continues next, admit a new bounded lev candidate explicitly or route a different audited lane rather than inferring a default lev continuation
  - current next-state source-family truth:
    - `SKILL_CLUSTER::next-state-signal-adaptation` now has a second bounded landed slice:
      - `a2-next-state-directive-signal-probe-operator`
    - current probe result is `attention_required`
    - current next step there is `record_real_post_action_witnesses_first`
    - the proposal slice remains proposal-only and non-migratory
    - the skeleton slice remains scaffold-only and non-migratory
    - the readiness slice remains selector-admission-only, non-migratory, and non-runtime-live
    - current admission decision: `admit_for_selector_only`
    - the selector slice remains selector-only, non-migratory, and non-runtime-live
    - current selected follow-on branch: `post_skeleton_follow_on_unresolved`
    - the disposition slice remains branch-governance-only, non-migratory, and non-runtime-live
    - current disposition: `retain_unresolved_branch`
    - the future-lane existence slice remains branch-governance-only, non-migratory, and non-runtime-live
    - current future-lane existence decision: `future_lane_exists_as_governance_artifact`
    - current bounded outcome: `hold_at_disposition`
    - any migration/runtime/imported-runtime-ownership follow-on remains separately gated and unresolved

Operational consequence:

- after intake/indexing truth is in place, the next repair is to keep the standing A2 brain aligned with that truth
- do not treat successful intake alone as proof that the standing A2 surfaces are current
- if `a2-brain-surface-refresher` still flags a standing A2 surface as older than latest evidence, patch that standing surface before widening intake claims or calling the lane current
- current direct repo refresh truth is `attention_required` on freshness lag only
- explicit stale-claim count is `0`
- the workshop-analysis imported continuation is now landed:
  - `SKILL_CLUSTER::workshop-analysis-gating`
  - landed first honest slice:
    - `a2-workshop-analysis-gate-operator`
- the Leviathan-derived continuity continuation is now landed:
  - `SKILL_CLUSTER::outer-session-durability`
  - landed first honest slice:
    - `outer-session-ledger`
- the first bounded `pi-mono` imported continuation is now landed:
  - `SKILL_CLUSTER::outside-control-shell-session-host`
  - landed first bounded slice:
    - `outside-control-shell-operator`
  - keep broader host/control claims report-only until a later bounded slice has live evidence
- do not confuse successful intake plus one bounded proof with general live mutation permission
- do not confuse a promotion recommendation with imported/runtime-live status
## 2026-03-22 Maintenance Intake Refresh

- Native maintenance intake now includes the bounded follow-on `a2-skill-improver-second-target-admission-audit-operator`.
- Current intake consequence is conservative:
  - one proven target class remains admitted
  - no second target class has yet earned admission
- Keep this lane in audit/proof gating mode rather than widening it into general maintenance mutation.
- Front-door corpus wording now matches the same intake-side hold.
- The next-state source-family lane now also has enough real witness material for a bounded follow-on bridge audit, but still not for runtime or learning claims.
## 2026-03-22 Next-State Bridge Intake Refresh

- The next-state source-family lane now includes the landed bounded follow-on `a2-next-state-improver-context-bridge-audit-operator`.
- Current intake consequence is still conservative:
  - first-target context bridge is admissible
  - second-target admission, runtime import, live learning, and graph backfill remain blocked
- Keep this lane in audit-only bridge mode rather than widening it into a live adaptation claim.

## 2026-03-22 Next-State Consumer Intake Refresh

- The next-state source-family lane now also includes the landed bounded follow-on `a2-next-state-first-target-context-consumer-admission-audit-operator`.
- Current intake consequence remains conservative:
  - `skill-improver-operator` now exposes an explicit first-target context contract
  - current result is `candidate_first_target_context_consumer_admissible`
  - current next step is `hold_consumer_as_audit_only`
- Keep this lane in bounded intake mode rather than widening it into live adaptation or consumer ownership by momentum.

## 2026-03-22 Edge Payload Probe Intake Refresh

- The graph-side intake line now also includes the landed bounded follow-on `edge-payload-schema-probe`.
- The broader graph/control tranche remains repo-held intake/support work, but it is still intentionally outside the active admitted skill registry.
- Current intake consequence remains conservative:
  - current relation is `STRUCTURALLY_RELATED`
  - current payload preview count is `3`
  - current next step is `hold_probe_as_sidecar_only`
- Keep this lane in sidecar-only intake mode rather than widening it into canonical graph ownership by momentum.

## 2026-03-22 Next-State Consumer Proof Intake Refresh

- The next-state source-family lane now also includes the landed bounded follow-on `a2-next-state-first-target-context-consumer-proof-operator`.
- Current intake consequence remains conservative:
  - proof result is `ok`
  - `context_contract_status = metadata_only_context_loaded`
  - `write_permitted = false`
  - current next step is `hold_consumer_proof_as_metadata_only`
- Keep this lane in bounded intake mode rather than widening it into live adaptation, write authority, or consumer ownership by momentum.

## 2026-03-22 Context Spec Follow-On Selector Intake Refresh

- The context/spec/workflow source-family lane now also includes the landed bounded follow-on `a2-context-spec-workflow-follow-on-selector-operator`.
- The same lane now also includes the landed bounded continuity-shell slice `a2-append-safe-context-shell-audit-operator`.
- The same lane now also includes the landed bounded post-shell selector `a2-context-spec-workflow-post-shell-selector-operator`.
- Current intake consequence remains conservative:
  - post-shell selector result is `ok`
  - current next step is `hold_cluster_after_append_safe_shell`
  - first standby follow-on if explicitly reopened later is `a2-executable-spec-coupling-audit-operator`
  - `scoped_memory_sidecar` remains blocked behind EverMem/backend reachability
- Keep this lane in bounded intake mode rather than widening it into multi-pattern substrate or memory claims by momentum.
