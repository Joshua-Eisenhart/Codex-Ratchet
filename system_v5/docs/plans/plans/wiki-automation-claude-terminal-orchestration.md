# Wiki Automation Claude Terminal Orchestration

Status: WIKI-BUILDER WORKER ORCHESTRATION SPEC

Purpose: define how Claude Code terminals should be used for the separate wiki-builder lane so independent concepts stay separate instead of being smoothed together.

## 1. Controller / worker split
Controller:
- Hermes only
- chooses the tranche
- checks file isolation
- verifies outputs
- reconciles shared routing pages

Workers:
- Claude Code CLI terminals
- one bounded independent concept cluster per terminal
- no worker owns final routing reconciliation or system-wide wording decisions

## 2. Worker mode
Preferred worker mode:
- `claude -p` print-mode tasks for bounded concept-local passes

Why:
- clean bounded execution
- reproducible
- no interactive prompt handling required
- easy to constrain to one concept cluster and one file set

## 3. When to split into parallel terminals
Parallel terminals are justified only when the concepts are genuinely independent.

Required conditions:
- non-overlapping target files
- separate authority bundles
- no shared `index.md` / `topic-map.md` / `current-research-overlays.md` / `log.md` edits during the worker phase
- Hermes has enough context to reconcile afterward

If those conditions are not met, do a single Hermes-controlled pass instead.

## 4. Good worker packet shapes
Each Claude terminal gets exactly one of:
- one bounded concept deepening pass
- one bounded provenance cleanup cluster
- one bounded role-clarification cluster
- one bounded source-path repair cluster
- one bounded support-layer enrichment cluster

## 5. Bad worker packet shapes
Do not give one Claude terminal:
- the whole wiki
- multiple unrelated concepts because they “feel connected”
- both concept-local edits and shared-route reconciliation together
- a vague instruction like “improve the wiki”

## 6. Shared pages rule
These are shared reconciliation surfaces and should normally be Hermes-only after worker completion:
- `/Users/joshuaeisenhart/wiki/index.md`
- `/Users/joshuaeisenhart/wiki/log.md`
- `/Users/joshuaeisenhart/wiki/concepts/topic-map.md`
- `/Users/joshuaeisenhart/wiki/concepts/current-research-overlays.md`

Workers may propose changes indirectly by changing concept-local pages, but Hermes should usually land the final shared-surface edits.

## 7. Worker prompt contract
Every worker prompt must contain:
1. exact concept cluster
2. exact target file set
3. exact read order
4. exact non-goals / forbidden widening
5. exact stop rule
6. exact verification expectations

Required wording:
- do not widen to neighboring concept clusters
- do not touch shared routing pages unless explicitly assigned
- stop after the bounded file set is complete

## 8. Example valid split
Terminal A:
- cluster: controller/contract concept pages
- files: `wiki-automation-contract.md`, `controller-state-transition-model.md`

Terminal B:
- cluster: geometry-support concept pages
- files: one support cluster only

Terminal C:
- cluster: provenance cleanup for one legacy book/source family
- files: only that family’s pages

Then Hermes reconciles:
- `index.md`
- `log.md`
- `topic-map.md`
- `current-research-overlays.md`

## 9. Example invalid split
Invalid:
- Terminal A edits `actual-lego-registry.md`
- Terminal B edits `lego-build-catalog.md`
- Terminal C edits `aligned-sim-backlog-and-build-order.md`
- all three also touch `topic-map.md`

Why invalid:
- file overlap on shared routing surfaces
- broad synthesis pressure
- strong risk of concept smoothing and route drift

## 10. Verification after worker completion
After each worker exits, Hermes should:
1. reread the touched files
2. verify file-set isolation held
3. reconcile only the necessary shared routing/log surfaces
4. run `/Users/joshuaeisenhart/wiki/tools/wiki_probe.py`
5. log the kept changes

## 11. One-sentence summary
Use parallel independent Claude Code terminals only to preserve genuinely independent concept clusters; Hermes remains the controller and reconciler so the wiki does not collapse into one smoothed pass.
