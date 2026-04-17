# Wiki Automation Run Contract

Status: SEPARATE WIKI-BUILDER RUN CONTRACT

Purpose: make the wiki-builder lane explicit as its own automation path, distinct from the automated sim runner.

## 1. Separation rule
This contract is for wiki automation only.

Do not use it for:
- sim batch execution
- overnight probe runners
- controller heartbeats for sim work
- sim closeout contracts

The two lanes are separate:
- sim runner: builds/reruns probes, batches, and controller audits
- wiki builder: ingests repo/doc/result changes into ledgers, concept pages, routing pages, and log surfaces in `/Users/joshuaeisenhart/wiki`

## 2. Controller and workers
Controller:
- Hermes only
- owns tranche selection
- owns final verification
- owns final wording and reconciliation on shared routing surfaces

Workers:
- Claude Code terminals only when a wiki pass can be split into genuinely independent concept clusters
- one terminal per bounded concept cluster
- non-overlapping file sets only
- workers do not own final route reconciliation or truth-language harmonization across shared pages

## 3. Required read order before any automation tick
Every wiki automation run should begin by reading:
1. `/Users/joshuaeisenhart/wiki/index.md`
2. `/Users/joshuaeisenhart/wiki/concepts/topic-map.md`
3. `/Users/joshuaeisenhart/wiki/concepts/current-research-overlays.md`
4. `/Users/joshuaeisenhart/wiki/log.md`
5. `system_v5/new docs/plans/wiki_ingest_and_lego_maintenance.md`
6. `system_v5/new docs/plans/sim_backlog_matrix.md`
7. `system_v5/new docs/plans/sim_truth_audit.md`
8. `/Users/joshuaeisenhart/wiki/concepts/wiki-automation-contract.md`
9. `/Users/joshuaeisenhart/wiki/concepts/wiki-automation-tick-template.md`
10. `/Users/joshuaeisenhart/wiki/config/wiki_automation_surface_map.json`

Then read any tranche-specific authority pages before editing.

## 4. Verification gate before tranche choice
Before choosing a tranche, run:
- `/Users/joshuaeisenhart/wiki/tools/wiki_probe.py`

Required outputs to inspect:
- page count
- index header count
- missing-from-index pages
- broken links
- orphan pages

Use the live filesystem as authority.

## 5. Ordered tranche model
Choose exactly one tranche per run:
1. structural integrity
2. routing coherence
3. role clarification
4. bounded content deepening
5. support-layer enrichment
6. handoff polish

Do not skip upward in the order because a later cluster is more salient.

## 6. Independent-concept parallelism rule
Parallel Claude terminals are allowed only when:
- concept clusters do not share target files
- each cluster has its own authority/read-order bundle
- the file sets do not overlap
- Hermes can reconcile shared pages afterward

Examples of valid parallel split:
- terminal A: one geometry-support concept cluster
- terminal B: one controller/contract concept cluster
- terminal C: one legacy-provenance cleanup cluster

Examples of invalid parallel split:
- two terminals editing `index.md`
- two terminals editing `topic-map.md`
- one terminal editing a concept page while another edits its role-clarification companion page in the same cluster
- one terminal doing content deepening while another edits the same cluster’s routing pages

## 7. Shared-surface reconciliation rule
These surfaces are Hermes-only reconciliation surfaces unless the run is a single-worker pass:
- `/Users/joshuaeisenhart/wiki/index.md`
- `/Users/joshuaeisenhart/wiki/log.md`
- `/Users/joshuaeisenhart/wiki/concepts/topic-map.md`
- `/Users/joshuaeisenhart/wiki/concepts/current-research-overlays.md`

Independent Claude workers should usually not patch them directly.
They patch concept-local pages first; Hermes reconciles the shared routing/log pages after the workers finish.

## 8. Required run declaration
Every wiki automation run should declare:
- tranche
- why this tranche is next
- target files
- read order
- allowed edits
- forbidden widening
- verification steps
- stop rule

## 9. Stop rules
Stop the run immediately if:
- `wiki_probe.py` is not green enough for the chosen tranche
- two planned workers overlap on the same file set
- the run starts drifting into the sim-runner lane
- a worker creates out-of-scope pages outside its bounded concept cluster
- shared routing surfaces are patched before concept-local work is reconciled

## 10. Required closeout
Every wiki automation closeout must report:
- tranche run
- pages changed
- verification result from `wiki_probe.py`
- whether shared routing surfaces were reconciled
- next bounded tranche suggestion

## 11. Current execution primitives
- verifier: `/Users/joshuaeisenhart/wiki/tools/wiki_probe.py`
- mapping file: `/Users/joshuaeisenhart/wiki/config/wiki_automation_surface_map.json`
- contract mirror: `/Users/joshuaeisenhart/wiki/concepts/wiki-automation-contract.md`
- tick template mirror: `/Users/joshuaeisenhart/wiki/concepts/wiki-automation-tick-template.md`

## 12. One-sentence summary
Wiki automation should be a Hermes-controlled, tranche-based, filesystem-verified maintenance lane that may use parallel independent Claude Code terminals for concept-local work, but only with non-overlapping file sets and post-pass reconciliation by Hermes.
