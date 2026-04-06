# System Skill Build Plan

Last updated: 2026-03-21

## Purpose

This is the current non-ad-hoc build plan for:

- canonical A2 repair
- broad skill-source corpus retention
- external skill corpus ingestion
- live skill integration
- graph truthfulness
- meta-skill / maintenance-skill buildout

This plan exists because too much work was happening as:

- thread-local memory
- scattered audits
- recent mentions only
- graph-first activity without stable build order

## Scope

This plan covers five connected layers:

1. owner-law and canonical A2
2. broad skill-source corpus retention
3. external skill corpus extraction
4. live skill registry / graph / runtime integration
5. meta-skill and skill-cluster architecture

## Audited Facts

### A2 / Spec Foundation

- `system_v3/specs` still owns the law.
- `system_v3/a2_state` is still the canonical persistent brain.
- `system_v4` is the active build layer, not the replacement for either of those.
- `system_v3/a2_state/doc_index.json` now includes owner-law and new A2 bridge surfaces.
- autosave/snapshot coverage was repaired.
- the standing A2 brain surfaces were materially stale and have now been partially refreshed, but they still need continued consolidation and conformance work.

### Broad Skill-Source Corpus

- human-facing front-door docs now exist:
  - `SKILL_SOURCE_CORPUS.md`
  - `REPO_SKILL_INTEGRATION_TRACKER.md`
  - `SKILL_CANDIDATES_BACKLOG.md`
  - `LOCAL_SOURCE_REPO_INVENTORY.md`
- these are now directly indexed in canonical A2 `doc_index.json`.
- no single source document is the umbrella for the whole corpus.
- the umbrella is the broad referenced corpus itself.
- the umbrella doc is now materially stronger, with a structured master registry, but it still needs continued growth as new source families appear.

### Local External Repo Reality

- the canonical local repo tree is `work/reference_repos/`
- referenced repo families already local there include:
  - `lev-os/agents`
  - `lev-os/leviathan`
  - `pi-mono`
  - `EverMemOS`
  - `MSA`
  - `z3`
  - Karpathy repos
  - other reference repos

### lev-os/agents Skill Corpus

- local audit confirms a very large skill corpus exists there.
- current direct count of `SKILL.md` files under `work/reference_repos/lev-os/agents` is:
  - `635`
- current structural split is:
  - `61` curated/runtime-tree skills
  - `574` library/pattern skills
- `lev-skills.sh` exposes a `26`-item active keep surface
- that count includes mixed classes:
  - active-looking skills
  - workshop/fetched material
  - archive material
  - todo material
- therefore the right job is not “import all.”
- the right job is:
  - inventory
  - classify
  - keep/adapt/mine/skip
  - cluster
  - integrate selectively

### Live Skill Integration Truth

- `SkillRegistry('.')` now loads `110` skills with `0` load issues.
- current live graph reality is:
  - `110` active registry skills
  - `110` graphed skill nodes
  - `0` missing graph nodes
  - `0` stale graph nodes
- current live graph audit is refreshed and agrees on presence counts
- this is coverage truth, not the full graph target
- the target graph is an evolving nested control substrate, not a flat skill picture
- the graph family should eventually reflect constraints, witnesses, transitions, intents, source families, and skills together
- important remaining truth gap is depth:
  - many skills are still shallowly integrated
  - `36` skill nodes still have only one edge
- current verified runner-discoverable corpus-derived skills include:
  - `autoresearch-operator`
  - `llm-council-operator`
  - `witness-evermem-sync`
  - `witness-memory-retriever`
  - `a2-research-deliberation-operator`
  - `a2-brain-surface-refresher`
  - `a2-skill-improver-readiness-operator`
- `witness-evermem-sync` now has durable cursor/error/report handling plus repo-held current state/report surfaces
- `witness-memory-retriever` is now the second bounded EverMem slice, with current repo-held result `attention_required` / `hold_at_retrieval_probe`
- `a2-evermem-backend-reachability-audit-operator` is now the third bounded EverMem side slice, with current repo-held result `attention_required` / `start_docker_daemon`
- the EverMem adapter search contract is repaired to match local repo reality: `GET /api/v1/memories/search`
- broader EverMem, pi-mono, `lev-os`, and imported-cluster use is still only partial.
- EverMem is useful, but it is now explicitly a side project rather than the main-line build focus.

## Build Tracks

### Track 1: Canonical A2 Conformance

Goal:

- make A2 a reliable canonical brain instead of a pile with some repaired edges

Tasks:

1. keep owner-law and boot surfaces indexed and current
2. continue refreshing standing A2 brain surfaces
3. normalize canonical persistent-state files toward an explicit target
4. keep compatibility-profile versus full-contract target explicit
5. define a real per-family A2 sink beyond append prose where needed

Acceptance gates:

- owner-law visible in `doc_index.json`
- active boot surfaces visible in `doc_index.json`
- active A2 brain surfaces reflect current architecture
- persistence profile status is explicit, not implied

### Track 2: Broad Skill-Source Corpus Retention

Goal:

- stop losing referenced repos, docs, method bundles, and skill families

Tasks:

1. keep the broad umbrella corpus current
2. upgrade `SKILL_SOURCE_CORPUS.md` into the real umbrella meta doc with:
   - per-source rows
   - imported-skill-corpus sections
   - method-corpus sections
   - unclassified/newly referenced bucket
   - truth-state columns
3. keep concrete state mirrored in tracker/backlog/inventory
4. decide whether root corpus docs should be directly indexed in canonical A2 or mirrored into A2-owned companions
5. add explicit A2 queue/work items for corpus-retention hardening

Acceptance gates:

- new referenced source families stop depending on recent thread memory
- the umbrella corpus doc can hold the broad referenced set, not just family-level summaries
- locally present important sources are promoted into the umbrella corpus itself
- root tracker state and A2 state do not drift silently
- “saved” versus “tracked” is explicit

### Track 3: lev-os/agents Skill Corpus Ingestion

Goal:

- treat `lev-os/agents` as a real imported skill corpus instead of a vague inspiration repo

Tasks:

1. inventory active-looking skills separately from archive/todo/workshop skills
2. classify clusters/categories
3. mark skills as:
   - keep
   - adapt
   - mine
   - skip
4. map likely Ratchet-native clusters
5. record extracted clusters in the umbrella corpus and backlog
6. choose one first imported cluster for actual implementation/integration, not just inventory

Acceptance gates:

- real inventory exists
- clusters/categories exist
- keep/adapt/mine/skip policy exists
- first selected imported cluster is written into the umbrella corpus and ready for integration work

### Track 4: Live Skill Integration Truth

Goal:

- make “skill exists” mean something real

Tasks:

1. refresh graph capability audit from live state
2. sync missing graph skill nodes or explicitly exclude them by policy
3. repair metadata for live skill discovery
4. verify runtime selection and use
5. correct stale overclaiming docs
6. make at least one selected imported or corpus-derived skill cluster genuinely live

Acceptance gates:

- registry count, graph count, and audit count agree or their differences are explicitly justified
- selected target skills are discoverable by the runner
- runtime claims are based on direct verification
- at least one first selected corpus-derived cluster is more than tracked: it is actually wired into live selection/use

### Track 5: Meta-Skills And Skill Clusters

Goal:

- build systems of skills that maintain, improve, diagnose, audit, and generate other skills
- keep that ecosystem tied to a graph-aware persistent brain and append-safe continuity, not a pile of isolated skill wins

Tasks:

1. define `SKILL_CLUSTER` and nested skill relationships
2. define maintenance/audit/improvement meta-skills
3. define first cluster families:
   - skill maintenance
   - source intake
   - meta-skill improvement
   - outside control shell
   - formal verification
4. start with a small first cluster set, not a total conversion
5. connect imported skill corpora and Ratchet-native skills through the same cluster model
6. keep the broader target explicit: append-safe A2/A1 richness, live spec coupling, and nested graph/cluster structure for thread continuity
7. make the graph target explicit: nested graph layers or graph-of-graphs under constraints, not a flat skill map
8. carry `axis0` and nested Hopf-tori as source-bound graph-shaping pressure while keeping them fenced from overclaim as earned runtime truth
9. mine external context/spec/workflow/memory repos for patterns that strengthen persistent brain and spec coupling without replacing owner-law
10. preserve the self-ratcheting design intent explicitly: the system, its graph, and the thing being ratcheted may recursively shape one another so long as the recursion stays constraint-bound and auditable
11. define a layered graph-tool stack that keeps the current auditable carrier while adding honest paths for higher-order topology, tensor-edge dynamics, and richer relation algebra
12. treat `clifford`-class geometric algebra as the likely long-lived math sidecar for nested Hopf / graded edge semantics, with quaternion tooling as a bounded earlier probe and `kingdon` as the bridge candidate if tensor-backend coupling becomes necessary

Acceptance gates:

- cluster model is explicit
- first meta-skill cluster is recorded in corpus/backlog/spec surfaces
- first maintenance cluster is tied to actual live skill repair work
- imported skill corpora and Ratchet-native clusters share one model instead of separate ad hoc lists
- graph work is framed as control-substrate work, not just graph coverage work
- graph upgrades are introduced as orthogonal added degrees of freedom where possible, not as flat accretion
- tranche-level skill work still reads as a probe into the broader ecosystem / persistent-brain goal, not as the goal itself

## Ordered Execution

1. canonical A2 conformance
2. broad corpus retention hardening
3. `lev-os/agents` skill corpus inventory and classification
4. live skill integration truth repair
5. first imported/live skill-cluster implementation tranche
6. first meta-skill / cluster implementation tranche

## Immediate Next Tranche

0. use the new source-family reselection slice as the current controller input:
   - `SKILL_CLUSTER::context-spec-workflow-memory` now has a first bounded landed slice:
     - `a2-context-spec-workflow-pattern-audit-operator`
   - keep that landed slice audit-only with next step `hold_first_slice_as_audit_only`
   - `SKILL_CLUSTER::karpathy-meta-research-runtime` now also has a first bounded landed slice:
     - `a2-autoresearch-council-runtime-proof-operator`
   - keep that landed slice proof-only with next step `hold_first_slice_as_runtime_proof_only`
   - current selector state is now fail-closed:
     - no bounded source-family lane is currently eligible for explicit reselection
   - there is no current bounded fallback while the other non-lev lanes remain held
1. keep the landed imported/corpus-derived slices coherent across schema, map, corpus, tracker, backlog, registry, and audit surfaces
2. refresh the small standing A2 truth slice so controller surfaces stop lagging the repaired repo truth
3. keep the EverMem side-project slices coherent across registry, corpus, tracker, A2, and emitted current-report surfaces
4. do not let EverMem drive the main-line build order while local backend reachability is still unearned
5. only revisit startup retrieval/bootstrap or outside-control memory work after local reachability is actually earned
6. keep the new lev-os/agents promotion audit slice honest and bounded while using it to choose the next imported cluster
7. keep the new OpenClaw-RL paper-derived next-state slice coherent across corpus, tracker, backlog, registry, dispatch, and emitted report surfaces
8. keep the broader objective explicit: better nested graph / persistent-brain / low-bloat continuity, not isolated skill wins
9. mine `Context-Engineering`, `spec-kit`, `superpowers`, and `mem0` into append-safe context, live spec coupling, workflow-discipline, and scoped memory-sidecar patterns through existing front-door surfaces
10. keep `mem0` fenced as a source for scoped memory/history/export-import patterns, not as canonical A2/A1 brain or as the graph substrate itself
11. push the graph plan toward nested connected graph layers under the base constraints and their natural extensions, not more flat graph mass
12. keep `axis0` and nested Hopf-tori explicit as graph-design pressure from the source corpus, but do not claim them as implemented graph semantics until there is bounded live evidence
13. treat the self-ratcheting / attractor-basin relation as live design pressure for graph architecture, while keeping it clearly separate from earned runtime claims
14. select the next graph-tool seam explicitly:
    - keep `pydantic + NetworkX + JSON/GraphML` as the auditable carrier/export layer
    - evaluate `TopoNetX` first for non-flat topological structure
    - evaluate `PyG` or `DGL` for tensor-valued edge dynamics
    - treat `clifford`-class geometric algebra as the primary math sidecar, with quaternion tooling as the smaller early probe
    - treat sheaf tooling as an experimental transport/obstruction layer
15. make the first graph-tool move a read-only adapter matrix over bounded live surfaces, not a migration of canonical ownership or a speculative substrate swap
16. do the next graph tranche as an adapter matrix over bounded live surfaces:
    - use `system_v4/a2_state/graphs/a2_low_control_graph_v1.json` as the first bounded owner-surface probe
    - keep `system_v4/a2_state/graphs/system_graph_a2_refinery.json` as the canonical live graph store
    - define one `TopoNetX` projection path for higher-order / non-flat structure
    - define one `PyG` projection path for tensor-valued or GA-carried edge payloads
    - define one `clifford` / `kingdon` sidecar path for graded / noncommutative edge algebra
    - keep all projections read-only until they prove honest value
17. do not widen imported-cluster build claims or runtime-live graph claims until the adapter tranche shows a real gain over the current flat coverage graph
18. the first bounded PyG projection contract now exists as `pyg-heterograph-projection-audit`, and it should stay read-only until a separate bridge audit proves richer cross-family links than the current skill/kernel/witness split
19. the first bounded bridge-gap slice now exists as `control-graph-bridge-gap-auditor`, and it currently shows 7 missing bridge families, 1 weak signal, and only 2 materially present cross-family links inside the control-facing graph
20. the first bounded bridge-source slice now also exists as `control-graph-bridge-source-auditor`, and it shows the bridge-source asymmetry explicitly:
    - `SKILL -> KERNEL_CONCEPT` remains `heuristic_only` under current owner surfaces
    - `B_SURVIVOR -> KERNEL_CONCEPT` is only `partial_property_trace`
    - `SIM_EVIDENCED -> KERNEL_CONCEPT` is only `chain_partial`
    - `B_OUTCOME` and `EXECUTION_BLOCK` remain `not_derivable_now`
    - the next graph-side follow-on should be `toponetx-projection-adapter-audit`, with bridge-source limits carried forward
21. the first bounded `TopoNetX` sidecar now also exists as `toponetx-projection-adapter-audit`, and it proves a smallest honest kernel-only topological projection:
    - bounded probe surface: `a2_low_control_graph_v1.json`
    - `419` node cells
    - `244` admitted relation entries collapsed into `200` unique 1-cells
    - `0` canonical 2-cells
    - `160` candidate triangle motifs kept as audit-only observations
    - `OVERLAPS` remains quarantined, so the next bounded moves should return to bridge strengthening and edge semantics rather than widening topology claims
22. the first bounded survivor-kernel backfill slice now also exists as `survivor-kernel-bridge-backfill-audit`, and it closes the immediate witness-side question cleanly:
    - `0` honest new direct survivor-to-kernel backfill candidates exist right now
    - `1` survivor is already directly linked to a live kernel concept
    - `46` survivors already resolve to live non-kernel concept classes instead (`34` extracted, `12` refined)
    - `31` survivors still have blank `source_concept_id`
    - the next bounded graph move should therefore shift to `skill-kernel-link-seeding-policy-audit`, not more direct survivor backfill attempts
23. the first bounded skill-kernel seeding policy slice now also exists as `skill-kernel-link-seeding-policy-audit`, and it closes the skill-island question cleanly:
    - auto-seeding remains fail-closed under current repo truth
    - `110` registry rows and `110` graphed skill nodes still carry `0` owner-bound concept fields
    - current skill edge families are still only `RELATED_TO::SKILL` and `SKILL_FOLLOWS::SKILL`
    - source path, tags, descriptions, layers, related skills, and inferred skill-to-skill edges are all explicitly insufficient for kernel seeding
    - the next bounded graph move should now shift to `clifford-edge-semantics-audit`
24. the first bounded `clifford` sidecar and edge-payload schema slices now also exist:
    - `clifford-edge-semantics-audit` confirms `clifford` and `kingdon` are usable in the graph venv, but only as read-only sidecars
    - `edge-payload-schema-audit` turns deferred GA fields into an explicit admitted schema over `DEPENDS_ON`, `EXCLUDES`, `STRUCTURALLY_RELATED`, and `RELATED_TO`
    - canonical graph storage remains unchanged
    - `OVERLAPS` and all skill-edge families remain outside admitted GA payload scope
    - the next bounded graph move is now also landed as a read-only `edge-payload-schema-probe`
    - current probe relation is `STRUCTURALLY_RELATED`, with `3` live payload previews
    - current next step is `hold_probe_as_sidecar_only`, not runtime mutation or training
    - current controller hold: the graph/control sidecar tranche is repo-held support work, but it is not yet batch-admitted into the active runtime skill registry or dispatch table
    - if this line moves again, it should happen by explicit controller reselection, not by silent admission drift

Current audited next imported/corpus-derived cluster state:

- bounded source-family reselection now exists as its own controller support slice:
  - `a2-source-family-lane-selector-operator`
  - `SKILL_CLUSTER::context-spec-workflow-memory` now has its first bounded landed slice:
    - `a2-context-spec-workflow-pattern-audit-operator`
    - and a second bounded landed selector slice:
      - `a2-context-spec-workflow-follow-on-selector-operator`
    - and a third bounded landed continuity-shell slice:
      - `a2-append-safe-context-shell-audit-operator`
    - and a fourth bounded landed post-shell selector slice:
      - `a2-context-spec-workflow-post-shell-selector-operator`
      - current next step: `hold_cluster_after_append_safe_shell`
      - first standby follow-on if explicitly reopened later: `a2-executable-spec-coupling-audit-operator`
      - `scoped_memory_sidecar` is currently blocked behind EverMem reachability
  - `SKILL_CLUSTER::karpathy-meta-research-runtime` now also has its first bounded landed slice:
    - `a2-autoresearch-council-runtime-proof-operator`
    - current next step: `hold_first_slice_as_runtime_proof_only`
  - current selector result is now fail-closed:
    - no bounded source-family lane is currently eligible for explicit reselection
  - there is no current bounded fallback while the other non-lev lanes remain held
  - keep this selector audit-only and controller-facing
  - do not reopen lev, next-state, graph/control, or EverMem by inertia

- `tracked work / planning`
  - first bounded slice now exists: `a2-tracked-work-operator`
  - `work` = adapt, `lev-plan` = mine, `workflow` = skip
- `research / deliberation`
  - first bounded slice now exists: `a2-research-deliberation-operator`
  - `lev-research` = adapt, `cdo` = mine, workflow leaves = skip or mine later
- `next-state signal adaptation`
  - first bounded slice now exists: `a2-next-state-signal-adaptation-audit-operator`
  - source family is OpenClaw-RL paper/repo
  - keep it audit-only, proposal-only, and non-runtime-live
  - second bounded slice now exists: `a2-next-state-directive-signal-probe-operator`
  - current bounded result is `ok` after a small real post-action witness batch
  - current signal counts are `3` next-state candidates / `3` directive signals / `1` evaluative signal
  - third bounded slice now exists: `a2-next-state-improver-context-bridge-audit-operator`
  - current bridge result is `admissible_as_first_target_context_only`
  - fourth bounded slice now exists: `a2-next-state-first-target-context-consumer-admission-audit-operator`
  - `skill-improver-operator` now exposes an explicit first-target context contract
  - current consumer result is `candidate_first_target_context_consumer_admissible`
  - fifth bounded slice now exists: `a2-next-state-first-target-context-consumer-proof-operator`
  - current proof result is `ok`
  - current next step there is `hold_consumer_proof_as_metadata_only`
  - keep the lane audit-only and non-runtime-live despite the new witness signal
  - keep the bridge first-target-context-only; it is not second-target admission, live learning, runtime import, or graph backfill
  - keep the consumer proof metadata-only / dry-run / no-write even though the owner contract now exists
- outside-memory / EverMem control
  - first two bounded slices are now real:
    - durable/auditable `witness-evermem-sync`
    - bounded `witness-memory-retriever`
  - broader memory claims still remain partial:
    - startup retrieval/bootstrap
    - pi-mono memory bridge
    - live-service proof against a reachable EverMem backend
  - current retrieval outcome is held at `hold_at_retrieval_probe`, not widened into a broader memory claim
- lev-os/agents promotion audit
  - first bounded slice now exists:
    - `a2-lev-agents-promotion-operator`
  - `SKILL_CLUSTER::lev-formalization-placement` now has seven bounded landed slices:
    - `a2-lev-builder-placement-audit-operator`
    - `a2-lev-builder-formalization-proposal-operator`
    - `a2-lev-builder-formalization-skeleton-operator`
    - `a2-lev-builder-post-skeleton-readiness-operator`
    - `a2-lev-builder-post-skeleton-follow-on-selector-operator`
    - `a2-lev-builder-post-skeleton-disposition-audit-operator`
    - `a2-lev-builder-post-skeleton-future-lane-existence-audit-operator`
  - current live graph truth:
    - `110` active registry skills
    - `110` graphed `SKILL` nodes
    - `0` missing
    - `0` stale
  - the separately gated skeleton follow-on is now landed as the first bounded scaffold/build slice:
    - `a2-lev-builder-formalization-skeleton-operator`
  - it remains scaffold-only and non-migratory
  - landing the skeleton slice does not mean formalization is complete
  - landing the skeleton slice does not imply migration permission, runtime-live status, or imported runtime ownership
  - the post-skeleton readiness slice is now landed as the first bounded admission gate after scaffold:
    - `a2-lev-builder-post-skeleton-readiness-operator`
  - it remains selector-admission-only, non-migratory, and non-runtime-live
  - current admission decision: `admit_for_selector_only`
  - the post-skeleton follow-on selector slice is now landed as the first selector-only downstream branch:
    - `a2-lev-builder-post-skeleton-follow-on-selector-operator`
  - it remains selector-only, non-migratory, and non-runtime-live
  - current selected follow-on branch: `post_skeleton_follow_on_unresolved`
  - the post-skeleton disposition slice is now landed as the branch-governance follow-on:
    - `a2-lev-builder-post-skeleton-disposition-audit-operator`
  - it remains branch-governance-only, non-migratory, and non-runtime-live
  - current disposition: `retain_unresolved_branch`
  - the post-skeleton future-lane existence slice is now landed as the next bounded governance-only follow-on:
    - `a2-lev-builder-post-skeleton-future-lane-existence-audit-operator`
  - it remains branch-governance-only, non-migratory, and non-runtime-live
  - current future-lane existence decision: `future_lane_exists_as_governance_artifact`
  - current bounded outcome: `hold_at_disposition`
  - any migration/runtime/imported-runtime-ownership follow-on remains separately gated and unresolved
  - refreshed selector truth now treats that cluster as landed and parked:
    - `landed_lev_cluster_count = 6`
    - `parked_lev_cluster_count = 1`
  - `SKILL_CLUSTER::lev-autodev-exec-validation` now has its first bounded landed slice:
    - `a2-lev-autodev-loop-audit-operator`
    - status: audit-only / nonoperative / non-migratory / non-runtime-live
  - `SKILL_CLUSTER::lev-architecture-fitness-review` now has its first bounded landed slice:
    - `a2-lev-architecture-fitness-operator`
    - status: audit-only / nonoperative / non-migratory / non-runtime-live
  - refreshed selector truth now reports:
    - `landed_lev_cluster_count = 7`
    - `parked_lev_cluster_count = 1`
    - `has_current_unopened_cluster = False`
    - `recommended_next_cluster = none`

Post-EverMem comparison result from the parallel audit lanes:

- native maintenance cluster now has its first honest slice landed:
  - `SKILL_CLUSTER::a2-skill-truth-maintenance`
  - landed first slice:
    - `a2-brain-surface-refresher`
    - status: audit-only / nonoperative / repo-held report + packet
- native maintenance cluster now has a second honest slice landed:
  - `SKILL_CLUSTER::a2-skill-truth-maintenance`
  - landed readiness slice:
    - `a2-skill-improver-readiness-operator`
    - status: audit-only / nonoperative / repo-held report + packet
    - current verdict: `skill-improver-operator` is `bounded_ready_for_first_target`
- native maintenance cluster now has a third honest slice landed:
  - `SKILL_CLUSTER::a2-skill-truth-maintenance`
  - landed target-selection slice:
    - `a2-skill-improver-target-selector-operator`
    - status: audit-only / nonoperative / repo-held report + packet
    - current selected first target: `a2-skill-improver-readiness-operator`
- native maintenance cluster now has a fourth honest slice landed:
  - `SKILL_CLUSTER::a2-skill-truth-maintenance`
  - landed first-target-proof slice:
    - `a2-skill-improver-first-target-proof-operator`
    - status: bounded proof / exact restore / repo-held report + packet
    - current proof result: one selected first target completed successfully without widening to general mutation
- native maintenance cluster now has a fifth follow-on admission slice landed:
  - `SKILL_CLUSTER::a2-skill-truth-maintenance`
  - landed second-target-admission slice:
    - `a2-skill-improver-second-target-admission-audit-operator`
    - status: audit-only / nonoperative / repo-held report + packet
    - current verdict: `hold_one_proven_target_only` with `0` honest second-target candidates admitted
- current native maintenance truth is now cleaner:
  - refresher bug is fixed, and the latest direct repo run is now `ok`
  - current freshness lag is now `0`
  - the self-evidence freshness bug is fixed
- the next imported slice has now landed:
  - `SKILL_CLUSTER::workshop-analysis-gating`
  - landed first honest slice:
    - `a2-workshop-analysis-gate-operator`
    - status: audit-only / nonoperative / repo-held report + packet
- the next Leviathan-derived imported slice has now landed:
  - `SKILL_CLUSTER::outer-session-durability`
  - import label:
    - `FlowMind Session Durability Bridge`
  - landed first honest slice:
    - `outer-session-ledger`
    - status: observer-only / repo-held state + append-only events + report
- the first bounded `pi-mono` imported slice has now landed:
  - `SKILL_CLUSTER::outside-control-shell-session-host`
  - first bounded slice:
    - `outside-control-shell-operator`
    - status: read-only / repo-held report + packet / no durable state

Current decision rule:

- do not widen memory claims next
- keep the native maintenance cluster converged as new current-truth slices land
- keep `skill-improver-operator` behind the readiness gate for general live mutation
- one selected first target is now proven under allowlist + approval-token control
- do not widen that into broader target classes or general live mutation
- standing A2 freshness lag is currently `0`
- the most recent maintenance-side fix was tracked-work truth normalization inside `a2-tracked-work-operator`
- the lev selector refresh is now landed
- the architecture-fitness slice is now landed
- the lev selector currently reports no current unopened lev candidate
- do not infer a default next lev continuation by absence of a recommendation
- open a different imported lane or admit a new bounded lev candidate only after explicit audit
- the next-state signal lane now has a landed second bounded slice
- keep it audit-only / non-runtime-live and do not widen it into learning claims while witness evidence remains too weak
- keep `outer-session-ledger` bounded to continuity witnessing only
- keep `outside-control-shell-operator` bounded to read-only session-host audit only
- do not claim a broader imported continuation until the next slice has live bounded evidence

## Do Not Regress To

- treating one remembered source doc as the whole umbrella corpus
- calling file existence “integration”
- calling graph presence “understanding”
- calling raw registry rows “runtime working”
- treating a flat graph as sufficient just because counts are repaired
- building more graph mass before the canonical/A2/corpus/integration truths are stable
