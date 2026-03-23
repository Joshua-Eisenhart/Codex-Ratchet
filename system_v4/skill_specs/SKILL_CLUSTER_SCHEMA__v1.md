# SKILL_CLUSTER_SCHEMA__v1

Status: ACTIVE / WORKING SHARED SCHEMA
Date: 2026-03-21
Role: shared schema for `system_v4` skill clusters and nested skill relationships

## Authority

This file is:

- a shared `system_v4` working schema
- subordinate to `system_v3` owner-law and canonical A2
- the current repo-held contract for cluster-shaped skill grouping

This file is not:

- a top-level registry object
- proof that every named cluster is already live
- permission to bypass per-skill registry truth

## Why This Exists

`system_v4` now has:

- source families
- imported skill corpora
- real registry skills
- maintenance and meta-skill families

But cluster truth was still split across:

- ad hoc notes
- tracker bullets
- graph hopes

This schema gives one shared contract for grouping skills without pretending the
live registry already supports top-level cluster rows.

## Working Rule

For now:

- cluster truth lives in repo-held docs first
- per-skill truth still lives in `skill_registry_v1.json`
- graph cluster nodes are allowed only as derived organization

Do not add a top-level `skill_clusters` object to
`system_v4/a1_state/skill_registry_v1.json` yet.

## Minimum Cluster Fields

Every cluster should carry:

- `cluster_id`
- `name`
- `description`
- `cluster_role`
- `source_family`
- `status`
- `integration_state`
- `members`
- `graph_semantics`
- `tracker_ref`
- `first_slice`

Recommended value families:

- `cluster_role`
  - `intake_stack`
  - `build_stack`
  - `audit_stack`
  - `maintenance_stack`
  - `correction_stack`
  - `outside_control_stack`
- `status`
  - `planned`
  - `staged`
  - `partial`
  - `live`
- `integration_state.registry_state`
  - `no_rows`
  - `partial`
  - `materialized`
- `integration_state.graph_state`
  - `not_projected`
  - `partial`
  - `materialized`
- `integration_state.tracker_state`
  - `NO_WORK`
  - `QUEUED`
  - `BLOCKED`
  - `MATERIALIZED`

## Members

`members` should be an array of objects with:

- `skill_id`
- `member_role`
- `member_origin`
- `member_state`
- `notes`

Recommended `member_origin` values:

- `imported`
- `ratchet_native`
- `mined_pattern`

Recommended `member_state` values:

- `kept`
- `adapted`
- `mined`
- `deferred`

## Graph Semantics

Clusters should use graph-native semantics only when the repo-held cluster truth
is already explicit.

The current intended graph semantics are:

- cluster node type: `SKILL_CLUSTER`
- membership relation: `MEMBER_OF`
- nesting relation: `PART_OF`

These relations are observational.
They do not replace per-skill registry truth or repo-held tracker truth.

## Repo-Held Surfaces

Use these surfaces together:

- [V4_SKILL_CLUSTER_SPEC__CURRENT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/V4_SKILL_CLUSTER_SPEC__CURRENT.md)
- [V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md)
- [SKILL_SOURCE_CORPUS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/SKILL_SOURCE_CORPUS.md)
- [REPO_SKILL_INTEGRATION_TRACKER.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/REPO_SKILL_INTEGRATION_TRACKER.md)
- [SKILL_CANDIDATES_BACKLOG.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/SKILL_CANDIDATES_BACKLOG.md)

## Example Cluster

```yaml
cluster_id: SKILL_CLUSTER::skill-source-intake
name: skill-source intake
description: First imported intake/discovery/build cluster adapted from lev-os/agents.
cluster_role: intake_stack
source_family: lev_os_agents_curated
status: partial
integration_state:
  registry_state: partial
  graph_state: not_projected
  tracker_state: MATERIALIZED
tracker_ref: system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md
first_slice: a2-skill-source-intake-operator
members:
  - skill_id: lev-intake
    member_role: imported intake analyst
    member_origin: imported
    member_state: adapted
  - skill_id: skill-discovery
    member_role: imported local-first discovery pattern
    member_origin: imported
    member_state: adapted
  - skill_id: skill-builder
    member_role: imported staged build/admission pattern
    member_origin: imported
    member_state: adapted
  - skill_id: a2-skill-source-intake-operator
    member_role: first Ratchet-native intake slice
    member_origin: ratchet_native
    member_state: kept
graph_semantics:
  cluster_node_type: SKILL_CLUSTER
  membership_relation: MEMBER_OF
  nesting_relation: PART_OF
  parent_cluster_id: null
```

## Explicit Non-Claims

- This schema does not claim clusters are already projected into the live graph.
- This schema does not claim imported skills become live by naming them.
- This schema does not let cluster docs outrank canonical A2 or owner-law.
