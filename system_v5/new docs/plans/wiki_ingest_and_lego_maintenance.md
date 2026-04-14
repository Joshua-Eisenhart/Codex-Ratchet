# Wiki Ingest and Lego Maintenance

Goal: keep the repo docs, lego ledgers, sim results, and wiki synchronized as an active working system rather than a one-way archive.

## Authority surfaces
- `new docs/16_lego_build_catalog.md`
- `new docs/17_actual_lego_registry.md`
- `new docs/07_model_math_geometry_sim_plan.md`
- `new docs/ANOMALOUS_COMPUTER_SCIENCE_TRANSLATION.md`
- `new docs/08_aligned_sim_backlog_and_build_order.md`
- `new docs/ENFORCEMENT_AND_PROCESS_RULES.md`
- `/Users/joshuaeisenhart/wiki`

## Wiki automation execution primitives
Use these as the live execution surfaces for wiki automation:
- `/Users/joshuaeisenhart/wiki/tools/wiki_probe.py` — structural verification against the live filesystem
- `/Users/joshuaeisenhart/wiki/config/wiki_automation_surface_map.json` — explicit repo-surface to wiki-target mapping for maintenance ticks
- `system_v5/new docs/plans/wiki-automation-run-contract.md` — launch/runtime contract for the separate wiki-builder lane
- `system_v5/new docs/plans/wiki-automation-claude-terminal-orchestration.md` — worker split and parallel Claude terminal rules
- `system_v5/new docs/plans/local-launch-checklist-wiki-automation.md` — prelaunch go/no-go checklist

## Core rule
When a new doc appears, an existing doc changes materially, or a sim result changes the honest state of a lego, update all three surfaces together:
1. repo execution docs
2. lego ledger/registry
3. wiki summary/ingest pages

## Maintenance loop

### A. New or updated docs
For each new or updated file under `new docs/`:
- classify it as current / legacy / supporting / archive
- decide whether it changes:
  - build order
  - lego inventory
  - tool-role expectations
  - bridge/axis embargoes
- if yes, patch:
  - `16_lego_build_catalog.md`
  - `17_actual_lego_registry.md`
  - matching wiki concept/summary pages

### B. New or rerun sims
For each sim that newly exists, newly runs, passes local rerun, or becomes canonical by process:
- update the truth audit/controller surfaces
- update the relevant lego row in `16` and/or `17`
- update the wiki summary note for the affected concept family
- if the sim changes claim scope, update the wiki framing from current vs legacy accordingly

### C. Research while executing
While running batches:
- use the wiki to search for upstream references, legacy framing, and missing dependency chains
- extract useful source-grounded summaries into current wiki concept pages
- do not leave important discoveries trapped only in result jsons or chat transcripts

## Worker model for concept-local wiki passes
- Hermes is the controller and final reconciler
- use separate parallel Claude Code terminals only for genuinely independent concept clusters
- independent means non-overlapping file sets and separate authority bundles
- each Claude terminal must stay inside one bounded concept cluster with its own stop rule
- only after those concept-local passes finish should Hermes reconcile shared routing surfaces like `index.md`, `topic-map.md`, `current-research-overlays.md`, and `log.md`
- do not collapse unrelated concepts into one smoothing pass just because they feel thematically adjacent

## Wiki targets to keep current
Minimum pages to maintain whenever relevant changes happen:
- `/Users/joshuaeisenhart/wiki/concepts/actual-lego-registry.md`
- `/Users/joshuaeisenhart/wiki/concepts/lego-build-catalog.md`
- `/Users/joshuaeisenhart/wiki/concepts/aligned-sim-backlog-and-build-order.md`
- `/Users/joshuaeisenhart/wiki/concepts/anomalous-computer-science-translation.md`
- additional geometry/chirality/flux pages touched by the current batch

Raw-source pages that should remain ingest sources, not final summaries:
- `/Users/joshuaeisenhart/wiki/raw/articles/new-docs/16_lego_build_catalog.md`
- `/Users/joshuaeisenhart/wiki/raw/articles/new-docs/17_actual_lego_registry.md`
- `/Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/Weyl Flux.md`

## Lego-ledger upkeep rules
- `16_lego_build_catalog.md` is the grouped controller ledger
- `17_actual_lego_registry.md` is the one-row-per-lego exhaustive registry
- if a grouped row in `16` hides distinct concrete math objects discovered in docs or sims, split or reference them explicitly in `17`
- if a sim lands and changes the honest coverage state, update the row instead of leaving stale status text

## External research support
Potential support surfaces:
- `https://github.com/NousResearch/hermes-agent-self-evolution`
- `https://lev.here.now/constraints/`
- `https://github.com/lev-os/leviathan`

Use them only as support/reference surfaces for:
- Hermes workflow ideas
- maintenance/process patterns
- self-improving controller habits
- controller/runtime architecture ideas
- health/reporting/constraint-discipline ideas

Do not let them override repo-local authority. Local authority remains the current repo docs plus the current wiki framing.

## Batch-close checklist
At the end of any meaningful batch:
- were any current docs changed or newly created?
- were any lego rows made stale by new results?
- were any wiki concept pages left behind relative to repo-current docs?
- did any new tool usage change the honest tool-maintenance picture?
- did any research discovery belong in a wiki concept page or ingest page?

If yes, update before closing the batch.
