# V4_SKILL_CLUSTER_SPEC__CURRENT

Status: ACTIVE / CURRENT WORKING OVERLAY
Date: 2026-03-21
Role: explicit working spec for `SKILL_CLUSTER` and nested skill relationships in `system_v4`

## 0. Authority And Scope

This file is:

- a `system_v4` working overlay
- subordinate to `system_v3` owner-law and canonical A2
- the current explicit spec for cluster-shaped skill organization

This file is not:

- owner-law
- canonical A2 memory
- proof that every named cluster is already live

## 1. Why This Exists

The system now has:

- source families
- imported skill corpora
- live skills
- maintenance skills
- runtime substrates

But it still needs an explicit model for:

- groups of related skills
- imported clusters versus Ratchet-native clusters
- nested roles such as `maintains`, `improves`, `audits`, and `orchestrates`

Without that model, the graph and trackers drift back toward flat lists.

## 2. Definitions

### Skill

A single executable or spec-backed capability with:

- code or executable behavior
- a registry identity
- optional graph identity
- optional runtime use

### Skill Cluster

A bounded group of skills that together form one higher-order capability.

A `SKILL_CLUSTER` may include:

- imported source skills
- Ratchet-native skills
- adapters
- maintenance skills
- audit skills
- orchestration skills

### Nested Skill Relationship

A typed relation between one skill or cluster and another, such as:

- `MEMBER_OF`
- `DERIVED_FROM_SOURCE_FAMILY`
- `IMPLEMENTS_CLUSTER_ROLE`
- `MAINTAINS`
- `AUDITS`
- `IMPROVES`
- `ORCHESTRATES`
- `USES_ADAPTER`

## 3. Minimum Cluster Schema

Every `SKILL_CLUSTER` should carry at least:

- `cluster_id`
- `name`
- `description`
- `cluster_type`
- `source_family`
- `status`
- `integration_state`
- `member_skill_ids`
- `member_source_refs`
- `cluster_roles`
- `related_clusters`
- `target_trust_zones`
- `target_graphs`
- `acceptance_gates`
- `first_live_slice`

Recommended value families:

- `cluster_type`:
  - `imported_skill_corpus_cluster`
  - `ratchet_native_cluster`
  - `meta_skill_cluster`
  - `maintenance_cluster`
  - `adapter_cluster`
- `status`:
  - `planned`
  - `staged`
  - `partial`
  - `live`
- `integration_state`:
  - `tracked_only`
  - `registry_partial`
  - `graphed_partial`
  - `runtime_partial`
  - `live`

## 4. Repo-Held Surfaces

The current repo-held cluster surfaces should be:

- this file for the working overlay and cluster-family priorities
- [SKILL_CLUSTER_SCHEMA__v1.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/skill_specs/SKILL_CLUSTER_SCHEMA__v1.md) for the shared schema
- [V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md) for the concrete imported-cluster map
- [SKILL_SOURCE_CORPUS.md](/home/ratchet/Desktop/Codex%20Ratchet/SKILL_SOURCE_CORPUS.md) for umbrella corpus membership
- [REPO_SKILL_INTEGRATION_TRACKER.md](/home/ratchet/Desktop/Codex%20Ratchet/REPO_SKILL_INTEGRATION_TRACKER.md) for current integration truth
- [SKILL_CANDIDATES_BACKLOG.md](/home/ratchet/Desktop/Codex%20Ratchet/SKILL_CANDIDATES_BACKLOG.md) for candidate and next-build tracking

## 5. First Required Cluster Families

The first cluster families are:

1. `skill-source intake`
2. `tracked work / planning`
3. `research / deliberation`
4. `skill maintenance`
5. `formal verification`
6. `outside memory / control`

These can mix imported and Ratchet-native skills.

## 6. Imported Cluster Progression

The imported-cluster progression is currently:

- `lev-os/agents` intake/discovery/build cluster

Its imported members come from:

- `lev-intake`
- `skill-discovery`
- `skill-builder`

Its first Ratchet-native implementation slice is:

- `a2-skill-source-intake-operator`

That slice is intentionally smaller than the whole imported cluster.

The next bounded imported/corpus-derived slices now also exist:

- `a2-tracked-work-operator`
- `a2-research-deliberation-operator`
- `a2-workshop-analysis-gate-operator`
- `outer-session-ledger`
- `outside-control-shell-operator`

The current imported pressure rule after those slices is:

- broader `pi-mono` host/control claims remain unproven
- prefer native A2 truth maintenance unless a new imported slice has bounded live evidence

## 6A. Native Maintenance Cluster

The first explicit native maintenance cluster is now:

- `SKILL_CLUSTER::a2-skill-truth-maintenance`

Current working shape:

- cluster_type: `maintenance_cluster`
- source_family: `Ratchet-native A2 truth maintenance`
- status: `partial`
- integration_state: `runtime_partial`
- member_skill_ids:
  - `a2-brain-surface-refresher`
  - `a2-skill-improver-readiness-operator`
  - `a2-skill-improver-target-selector-operator`
  - `a2-skill-improver-first-target-proof-operator`
  - `a2-brain-refresh`
  - `graph-capability-auditor`
  - `runtime-context-snapshot`
- first_live_slice:
  - `a2-brain-surface-refresher`
  - status: audit-only / nonoperative / repo-held report + packet
  - `a2-skill-improver-readiness-operator`
  - status: audit-only / nonoperative / repo-held report + packet / `do_not_promote`
  - `a2-skill-improver-target-selector-operator`
  - status: audit-only / nonoperative / repo-held report + packet / first-target-selection only
  - `a2-skill-improver-first-target-proof-operator`
  - status: bounded proof / exact restore / repo-held report + packet / one-target-only

Current rule:

- this cluster exists to keep standing A2 truth aligned with current repo truth
- it does not yet have permission to mutate canonical A2 directly
- the first live slice no longer suffers from the self-evidence freshness bug, and the latest direct repo run is now back to `0` freshness lag
- the second live slice now keeps `skill-improver-operator` behind an explicit readiness gate
- the third live slice turns that readiness gate into one explicit selected first target
- the fourth live slice proves one selected first target without widening to general mutation
- keep rerunning it as current-truth slices land so standing A2 drift is caught early

## 7. Graph Semantics

The graph should represent clusters explicitly when they become stable enough to matter.

Minimum graph expectations:

- `SKILL` nodes remain the canonical individual skill identities
- `SKILL_CLUSTER` nodes may group related skills
- cluster edges should be typed and auditable

The graph is still derived organization.
Cluster truth must stay anchored in repo-held docs and registry truth first.

## 8. Integration Rules

Do not call a cluster `live` unless:

1. the cluster is named in repo-held docs
2. member skills are explicit
3. the first live slice exists as real code and registry truth
4. graph representation is either present or explicitly deferred
5. runtime use is directly verified or clearly marked partial

## 9. Current Working Rule

Use clusters to reduce three failure modes:

- flat source-family sprawl
- flat skill-list sprawl
- graph growth without functional grouping

Clusters should make the system easier to build, not more decorative.
