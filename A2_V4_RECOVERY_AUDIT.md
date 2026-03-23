# A2 V4 Recovery Audit

Last updated: 2026-03-21

## What This Is

This is the simple root-level reality check for:

- what `A2` is supposed to do
- what `system_v4` has actually built so far
- what the graphs are doing well
- what the graphs are not doing
- what has to be repaired before we can honestly say the system understands itself

This is not a spec.
This is not a graph dump.
This is the easy-to-find recovery surface for this problem.

## What You Have Been Asking For

- keep referenced repos, docs, methods, and candidate skills from getting lost
- use the real `A2` persistent brain instead of just building more graph artifacts
- process `system_v3` first so `system_v4` stays grounded in the previous system
- graph all skills and integrate them so they do not sit as forgotten orphans
- turn repo and method families into real skills over time
- stop claiming things are saved or understood when they are only partially staged

## What A2 Is Supposed To Do

The owner law is here:

- [01_REQUIREMENTS_LEDGER.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/specs/01_REQUIREMENTS_LEDGER.md)
- [02_OWNERSHIP_MAP.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/specs/02_OWNERSHIP_MAP.md)
- [07_A2_OPERATIONS_SPEC.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md)
- [19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md)

`A2` is not just a graph.
It is supposed to be the persistent debug, orchestration, memory, and context layer for the system.

That means:

- active brain/control surfaces
- append-safe memory
- indexed owner docs
- fuel / rosetta / constraint surfaces
- autosave and snapshot coverage
- bounded boot order
- enough continuity that repeated user intent does not keep disappearing

## What Is Actually True Right Now

Some useful repairs are real:

- [A2_KEY_CONTEXT_APPEND_LOG__v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md) now exists
- [A2_BOOT_READ_ORDER__CURRENT__v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_BOOT_READ_ORDER__CURRENT__v1.md) now exists
- [REPO_SKILL_INTEGRATION_TRACKER.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/REPO_SKILL_INTEGRATION_TRACKER.md) now exists
- [SKILL_CANDIDATES_BACKLOG.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/SKILL_CANDIDATES_BACKLOG.md) now exists

But the deeper failure is still real:

- `system_v3/a2_state` is still sprawl-heavy
- standing A2 brain content is still stale relative to current work
- autosave and persistent-state files are only partially aligned with the A2 contract
- `system_v4` graph growth has outrun actual system understanding
- graph presence audits are now refreshed against live registry truth, but runtime-depth claims and standing A2 surfaces still need continued refresh
- first imported-cluster work is now materially real as a bounded A2 intake slice, but the broader imported-cluster loop is still only partial

## A2 Failure Audit

### 1. The owner law was missing from the canonical A2 index and is now repaired

[doc_index.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/doc_index.json) now indexes the core owner docs:

- [01_REQUIREMENTS_LEDGER.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/specs/01_REQUIREMENTS_LEDGER.md)
- [02_OWNERSHIP_MAP.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/specs/02_OWNERSHIP_MAP.md)
- [07_A2_OPERATIONS_SPEC.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/specs/07_A2_OPERATIONS_SPEC.md)
- [19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md)

The remaining problem is no longer absence from the index.
The remaining problem is using that repaired index to refresh the actual standing A2 brain surfaces.

### 2. The standing A2 brain surfaces are stale

These active A2 surfaces are materially older than the current `v4` work:

- [INTENT_SUMMARY.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/INTENT_SUMMARY.md)
- [A2_BRAIN_SLICE__v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_BRAIN_SLICE__v1.md)
- [A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md)
- [A2_TERM_CONFLICT_MAP__v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md)
- [A2_TO_A1_DISTILLATION_INPUTS__v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md)

The new repair surfaces exist, but the old standing brain has not yet been refreshed around them.

### 3. The persistent-state files only partially match the A2 contract

The current A2 persistent-state layer is mixed:

- [memory.jsonl](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/memory.jsonl) is still mostly compatibility-style autosave, not the full `19` memory-entry shape
- [fuel_queue.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/fuel_queue.json) is legacy-shaped and missing the fuller contract fields
- [rosetta.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/rosetta.json) is legacy-shaped and missing current schema/version framing
- [constraint_surface.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/constraint_surface.json) is a narrow derived summary, not a richer declared canonical surface

This is not one clean problem.
Part of it is compatibility autosave.
Part of it is older writer logic still emitting older shapes.

### 4. Autosave/snapshot coverage was too thin and is now improved

The autosave/snapshot path was missing parts of the active A2 brain/control set required by the owner docs.
That coverage has now been expanded through the shared watched-surface helper.

The remaining problem is schema and content coherence, not the exact same watch-list omission as before.

- canonical persistent-state files still need stronger contract alignment
- standing brain content still needs refresh against the repaired foundation

### 5. A2 state is still too large and noisy to function as a usable brain by directory reading

`system_v3/a2_state` currently contains hundreds of files and too many one-off note families.

The important problem is not that those files exist.
The problem is that the active owner/read path has been too weak relative to the pile.

Current measured shape:

- `414` top-level files in `system_v3/a2_state`
- `11` standing A2 brain/control surfaces by file count
- `12` canonical A2 state-data files
- `391` support/spillover files

The smallest bounded working set is much smaller:

- `4` owner-law specs outside `a2_state`
- `10` human A2 boot files inside `a2_state`
- `15` total controller-grade files if the canonical state-data files are included

That is why raw directory browsing keeps failing.

### 6. The live skill registry path and graph coverage are now repaired enough to trust the counts, but depth is still partial

The raw registry file at [skill_registry_v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a1_state/skill_registry_v1.json) now has `109` rows with `109` `active` statuses, and the live registry loader now successfully loads them.

Verified current behavior:

- `SkillRegistry('.')` now loads `109` skills
- `health_pass()` now reports `0` stale skills
- the live graph now has `109` `SKILL` nodes with `0` missing relative to the registry
- the front-door corpus docs are now directly indexed in [doc_index.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/doc_index.json)

The remaining problem is no longer loader failure or missing graph coverage.
The remaining problem is integration depth and keeping the audit surfaces current.

So raw registry presence is not the same thing as live usable registry integration.

## V4 Graph Reality Audit

### 1. The graph is not empty

The live `v4` refinery graph at [system_graph_a2_refinery.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/graphs/system_graph_a2_refinery.json) is real and large:

- `19898` nodes
- `40506` edges

It does include key `system_v3` owner docs as source nodes.

### 2. But the graph is much stronger as accumulation than as understanding

Current node mix is dominated by accumulation layers:

- `10099` `SOURCE_DOCUMENT`
- `5895` `EXTRACTED_CONCEPT`
- `1287` `REFINED_CONCEPT`
- `842` `KERNEL_CONCEPT`

That means the graph is good at storing that many things were ingested.
It does not mean the system has built a bounded owner-law understanding model.

### 3. The newest A2 repair surfaces are not even in the live v4 graph yet

These new recovery surfaces do not currently appear in the live `v4` graph:

- [A2_KEY_CONTEXT_APPEND_LOG__v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md)
- [A2_BOOT_READ_ORDER__CURRENT__v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_BOOT_READ_ORDER__CURRENT__v1.md)

So even the recovery work is not yet represented there.

### 4. Graph presence is not the same thing as runtime semantic steering

Skill dispatch in [run_real_ratchet.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/skills/run_real_ratchet.py) is still primarily driven by registry metadata through [skill_registry.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/skills/skill_registry.py), not by graph-edge semantics.

So the graph is not currently the main thing that understands the system and routes the work.

### 5. The graph skill audit is now refreshed against the live registry

The current graph capability audit at [GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.json) now reports:

- `91` active skills
- `91` graphed skill nodes
- `0` missing
- `0` stale
- `0` isolated

That repaired the graph-presence drift.
The remaining issue is that many skills are still shallowly integrated, with `36` single-edge skill nodes.

### 6. The graph is not the thing currently driving skill understanding anyway

Even where the graph is populated, the runtime path is still mostly driven by:

- registry metadata filtering
- packet JSON loading
- plain `name` / `description` / `tags` text scoring

So the graph is currently much more of an observational accumulation surface than an authoritative understanding surface.

### 7. The skill-integration story is weaker than some recent trackers claimed

The current honest split is:

- `Z3`: partly real in runtime, with `z3-constraint-checker` directly used as a live hardness gate
- `autoresearch` and `llm-council`: live registry-mediated discovery and dispatch binding are now verified
- `EverMem`: thin adapter files exist, `witness-evermem-sync` now has one honest post-batch runtime seam plus durable cursor/error/report handling, but the broader memory family is still partial
- `pi-mono`: source ingestion exists, but runtime integration is still shallow
- `lev-os`: tracked as source families, not yet real integrated skill families
- `Retooled External Methods`: real as a saved source family through [29 thing.txt](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/v4%20upgrades/29%20thing.txt), still partial as method-by-method integrated skill conversion

## What Was Actually Accomplished

These things are real and should not be erased:

- intent/context/witness/control work was built in `system_v4`
- the skill graph sync work improved real graph coverage
- the root trackers now exist
- the A2 append log now exists
- the A2 boot-read order now exists
- the Retooled External Methods referent was corrected back to the real source doc [29 thing.txt](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/v4%20upgrades/29%20thing.txt)
- the EverMem lane now has one durable repo-held state/report seam:
  - [EVERMEM_WITNESS_SYNC_STATE__CURRENT__v1.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/EVERMEM_WITNESS_SYNC_STATE__CURRENT__v1.json)
  - [EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/EVERMEM_WITNESS_SYNC_REPORT__CURRENT__v1.md)

So this is not a story of literally nothing being done.

It is a story of real work being built on top of an A2 understanding layer that is still too weak.

## What Is Still Not Done

- `system_v3` owner law has not been properly recovered into the active A2 brain
- A2 does not yet provide reliable durable context retention for all the repos/docs/method bundles you keep feeding it
- `v4` graph growth still overstates actual system understanding
- many repo/method families are still only partially converted into real integrated skills
- the graph/audit/read surfaces are drifting out of sync with the live registry and recent repair work

## Repair Order

1. Maintain [doc_index.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/doc_index.json) coverage so it indexes the owner law, active A2 brain surfaces, and the root front-door corpus docs.
2. Expand autosave/snapshot coverage to include the full required A2 brain/control set.
3. Bring [fuel_queue.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/fuel_queue.json), [rosetta.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/rosetta.json), and [constraint_surface.json](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/constraint_surface.json) up to at least a declared compatible schema/version layer.
4. Decide what the live truth for [memory.jsonl](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/memory.jsonl) is supposed to be, instead of letting `07`, `19`, and compatibility autosave all silently disagree.
5. Keep [skill_registry.py](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/skills/skill_registry.py) metadata and dispatch bindings aligned so newer corpus-derived skill records stay discoverable.
6. Refresh the standing A2 brain surfaces from the owner law and the current repo state.
7. Re-ingest the new A2 repair surfaces into `v4`.
8. Keep the `v4` graph capability audit refreshed against the real live skill state instead of letting it drift again.
9. Only after that, keep promoting repo/method families into real skills and deeper runtime integration.

## Working Rule From Here

Before claiming any repo, method bundle, or skill family is truly saved:

1. append it to [REPO_SKILL_INTEGRATION_TRACKER.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/REPO_SKILL_INTEGRATION_TRACKER.md)
2. append the durable context impact to [A2_KEY_CONTEXT_APPEND_LOG__v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md)
3. only then claim it is retained

That is the minimum bar until the deeper A2 recovery work is actually done.
