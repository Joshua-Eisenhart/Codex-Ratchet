# V4_SPEC_AUDIT__CURRENT

Status: ACTIVE / CURRENT AUDIT
Date: 2026-03-21
Role: simple audit of what `system_v4` currently has as real specifications versus what was previously only implied or scattered

## What Was Missing

Before this pass, `system_v4` had:

- one architecture reference
- many session logs
- many graph and skill artifacts
- no small current spec set saying what `v4` is, what A2 still owns, and what the required build order is

That made it too easy to:

- overclaim graph understanding
- overclaim skill integration
- drift away from the `system_v3` owner-law
- treat recent thread work as the current architecture

## What Is Now Explicit

The current explicit `v4` front door is:

1. `system_v4/README.md`
2. `system_v4/V4_SYSTEM_SPEC__CURRENT.md`
3. `system_v4/V4_BUILD_ORDER__CURRENT.md`
4. `system_v4/V4_SPEC_AUDIT__CURRENT.md`
5. `system_v4/V4_SKILL_CLUSTER_SPEC__CURRENT.md`
6. `system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md`
7. `system_v4/PIPELINE_ARCHITECTURE_REFERENCE.md`

## What Is Now Specified Clearly

- `system_v4` is a build layer on top of `system_v3`, not a replacement for it
- canonical A2 still lives in `system_v3/a2_state`
- owner-law still lives in `system_v3/specs`
- the `v4` docs are working overlays, not owner-law
- the graph is derived organization, not the canonical brain
- a skill is not integrated just because its file exists
- source corpus trackers are working surfaces, not the canonical brain
- cluster schema and imported-cluster maps are now explicit repo-held overlays instead of thread residue
- outside wrappers such as `pi-mono`, `leviathan`, and `EverMemOS` should stay outside canonical A2 unless formally admitted

## What Was Repaired In The Foundation

- `system_v3/a2_state/doc_index.json` now includes owner-law and active A2 boot surfaces
- the rebuild tool for that index now skips self-indexing
- A2 autosave/snapshot coverage was expanded and centralized through shared watched-surface logic
- the live skill registry loader now fail-soft loads valid rows instead of collapsing to zero on malformed input

## What Is Still Not Good Enough

- the standing A2 brain surfaces still need a real content refresh against the repaired foundation
- canonical A2 persistent-state files still have mixed legacy/new schema shapes
- graph coverage presence is now refreshed against the live registry, but runtime-integration depth still needs continued audit
- external source families are tracked much better, but only a small part of the candidate-skill backlog is truly integrated

## Still Required Next

- refresh the standing A2 brain surfaces so they actually absorb the repaired foundation
- keep the A2 compatibility-profile versus full-contract target explicit
- keep graph and runtime truth audits current as counts and imported-cluster slices change

## Current Rule

If a future `system_v4` change conflicts with:

- `system_v3/specs`
- canonical A2 memory in `system_v3/a2_state`
- `system_v4/V4_SYSTEM_SPEC__CURRENT.md`
- `system_v4/V4_BUILD_ORDER__CURRENT.md`

then the change should be treated as suspicious until audited.
