# V4_SYSTEM_SPEC__CURRENT

Status: ACTIVE / CURRENT WORKING OVERLAY
Date: 2026-03-21
Role: simple current working overlay for building `system_v4` without losing the `system_v3` owner-law and A2 foundation

## 0. Status And Authority

This file is:

- a current `system_v4` working overlay
- subordinate to the owner-law in `system_v3/specs`
- subordinate to canonical A2 state in `system_v3/a2_state`

This file is not:

- owner-law
- canonical A2 memory
- sufficient authority by itself to override `system_v3`

## 1. What `system_v4` Is

`system_v4` is the next build layer for:

- skillized runtime work
- graph-assisted organization, retrieval, and control-substrate shaping
- source-to-skill conversion
- runtime integration of validated method families
- bounded external wrapper and memory adapters

It is not a replacement for the `system_v3` owner-law or canonical A2 persistent brain.

## 2. What Still Owns The System

These still govern the build:

1. `system_v3/specs/01_REQUIREMENTS_LEDGER.md`
2. `system_v3/specs/02_OWNERSHIP_MAP.md`
3. `system_v3/specs/07_A2_OPERATIONS_SPEC.md`
4. `system_v3/specs/19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md`

And these still define the live canonical A2 boot set:

1. `system_v3/a2_state/A2_BOOT_READ_ORDER__CURRENT__v1.md`
2. `system_v3/a2_state/INTENT_SUMMARY.md`
3. `system_v3/a2_state/A2_BRAIN_SLICE__v1.md`
4. `system_v3/a2_state/A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md`
5. `system_v3/a2_state/A2_TERM_CONFLICT_MAP__v1.md`
6. `system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md`
7. `system_v3/a2_state/OPEN_UNRESOLVED__v1.md`
8. `system_v3/a2_state/A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md`
9. `system_v3/a2_state/SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1.md`
10. `system_v3/a2_state/MODEL_CONTEXT.md`
11. `system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md`
12. `system_v3/a2_state/A2_SKILL_SOURCE_INTAKE_PROCEDURE__CURRENT__v1.md`

Canonical persistent-state companions also remain part of live A2 reality:

- `system_v3/a2_state/memory.jsonl`
- `system_v3/a2_state/doc_index.json`
- `system_v3/a2_state/fuel_queue.json`
- `system_v3/a2_state/rosetta.json`
- `system_v3/a2_state/constraint_surface.json`

## 3. Layer Stack

### Layer 0: Owner Law

- `system_v3/specs`
- owns requirement truth, ownership, A2 contract, and build constraints

### Layer 1: Canonical A2 Persistent Brain

- `system_v3/a2_state`
- owns persistent context, append logs, boot surfaces, doc index, and controller memory
- currently operates on a mixed reality:
  - explicit full-contract target in `19_A2_PERSISTENT_BRAIN_AND_CONTEXT_SEAL_CONTRACT.md`
  - narrower live compatibility profile still used by some autosave/snapshot tooling

### Layer 2: Source Corpus And Intake

- root source/corpus trackers
- local reference repo inventory
- skill-source intake procedure
- candidate-skill backlog

### Layer 3: Skills And Runtime Substrates

- `system_v4/skills`
- registry records
- executable operators, adapters, builders, and runtime helpers
- shared cluster schema and imported-cluster maps

### Layer 4: Graph And Refinery Layer

- `system_v4/a2_state/graphs`
- graph builders, bridge layers, refinery layers, and graph audits

### Layer 5: Runtime Orchestration

- `run_real_ratchet.py`
- live skill discovery and dispatch
- witness capture
- intent/control policy

### Layer 6: Outside Wrappers And Sidecars

- `pi-mono` style claws and host shells
- `lev-os/leviathan` style orchestration wrappers
- `EverMemOS` style outside memory/context backends

## 4. Graph Rules

The graph is allowed to do these things:

- represent source docs, concepts, constraints, skills, witnesses, intents, and relationships
- help retrieve, cluster, and refine
- expose auditable organization and integration state
- carry multiple connected graph layers rather than one flat skill map when the layer split is explicit and auditable
- act as part of the control substrate only when it stays bounded by owner-law, canonical A2, and explicit admission rules

The graph is not allowed to silently become:

- one flat graph that pretends coverage is the target architecture
- the canonical A2 persistent brain
- the owner-law
- proof that the system understands itself
- proof that a skill is operationally integrated
- topology rhetoric standing in for implemented graph contracts

Current graph-design pressure:

- the target is not a decorative picture layer
- the target is an evolving nested graph family or graph-of-graphs
- the graph family should reflect control relations, constraint eliminations, witness structure, and runtime transitions
- `axis0` and nested Hopf-tori are source-bound shaping pressure for this graph family
- `axis0` correlation-entropy / JK-fuzz compression pressure should remain visible in graph design where it can be made explicit without overclaim
- the system is intended to ratchet itself, so the graph may increasingly reflect the attractor basin the system is seeking
- that self-recursive pressure is only acceptable when bounded by base constraints, their natural extensions, and explicit auditability
- later graph upgrades should introduce degrees of freedom through practical orthogonality, not through flat graph mass or loosely coupled feature growth
- graph edges may eventually need richer semantics than classical lines, including elastic stretch/compress behavior under entropy pressure, but this remains an open design question rather than implemented truth
- the current `pydantic + NetworkX + JSON` stack should remain the auditable human-readable carrier, with GraphML treated as a lossy export rather than the long-term owner of richer graph semantics
- likely next graph-tool pressure is layered rather than replacement-based:
  - higher-order / non-flat topology via `TopoNetX`-class tools
  - tensor-valued edge dynamics via `PyG` or `DGL`
  - geometric-algebra math via `clifford`-class or `kingdon`-class tools, with quaternion tooling as the lighter early probe
  - sheaf-style consistency / obstruction tooling as an experimental transport-curvature sidecar rather than an assumed base substrate
- those topology terms are not yet earned runtime truth and must not be overclaimed as implemented substrate
- current graph-source truth is still asymmetric:
  - witness/evidence families carry partial kernel trace through `B_SURVIVOR.properties.source_concept_id` and `SIM_EVIDENCE_FOR` chains
  - skill families still do not carry owner-bound kernel concept identity, so `SKILL -> KERNEL_CONCEPT` bridges remain proposal-only under current surfaces
- the first bounded `TopoNetX` sidecar now exists, but it stays kernel-only and read-only:
  - bounded probe surface: `a2_low_control_graph_v1.json`
  - admitted topological relations: `DEPENDS_ON`, `EXCLUDES`, `STRUCTURALLY_RELATED`, `RELATED_TO`
  - `OVERLAPS` remains quarantined out of equal-weight topology
  - candidate higher-order motifs are audit observations only, not canonical 2-cells
- the first bounded edge-payload schema slice now also exists, but it stays sidecar-only over admitted low-control relations:
  - deferred GA fields are explicit: `entropy_state`, `correlation_entropy`, `orientation_basis`, `clifford_grade`, `obstruction_score`
  - canonical graph storage is unchanged
  - `OVERLAPS` and `SKILL` edges remain outside the admitted GA payload scope

## 5. Skill Rules

A skill is only meaningfully integrated when all of these are true:

1. source family is durably tracked
2. skill exists as code
3. registry row is valid and loadable
4. graph identity is present if applicable
5. runtime use is explicitly verified

File existence alone is not integration.
Graph presence alone is not integration.
Registry presence alone is not integration.

## 6. Source Corpus Rules

The growing source families for skill creation live in:

- `SKILL_SOURCE_CORPUS.md`
- `REPO_SKILL_INTEGRATION_TRACKER.md`
- `SKILL_CANDIDATES_BACKLOG.md`
- `LOCAL_SOURCE_REPO_INVENTORY.md`
- `system_v4/V4_IMPORTED_SKILL_CLUSTER_MAP__CURRENT.md`

These are front-door working surfaces.
They do not replace canonical A2 memory.

Important rule:

- there is no single file that should be treated as the umbrella for all referenced external repos, method bundles, and skill families
- `lev_nonclassical_runtime_design_audited.md` is one source among many in the broader skill-source corpus
- trackers and backlogs should retain the whole referenced set, not collapse it into one document

Recurring system significance from those surfaces must still route into:

- `system_v3/a2_state/A2_KEY_CONTEXT_APPEND_LOG__v1.md`
- `system_v3/a2_state/doc_index.json` when appropriate
- other active A2 brain surfaces when meaning or routing changes

## 6.1. Intake And Admission Path

The required path is:

1. source family appears in root corpus trackers
2. local presence and repo inventory are recorded
3. recurring significance is appended into canonical A2 context surfaces
4. if needed, indexing and queue surfaces are refreshed
5. candidate skill claims are recorded
6. only then may code, registry, graph, and runtime claims be made

Working A2 routing rule:

- recurring context and user correction -> `A2_KEY_CONTEXT_APPEND_LOG__v1.md`
- boot/read-path significance -> `A2_BOOT_READ_ORDER__CURRENT__v1.md` or companion brain surfaces
- source/index visibility -> `doc_index.json`
- pending work -> `fuel_queue.json`
- source-to-skill candidate tracking -> root corpus trackers plus later A2 distillation when the meaning changes

## 7. Current External Family Roles

### Retooled External Methods

- method conversion family
- source for many future operators

### lev-os/agents

- intake, admission, workflow, and packaging pattern mine
- first promoted imported cluster is now the `skill-source intake` cluster
- first bounded Ratchet-native slice is `a2-skill-source-intake-operator`

### lev-os/leviathan

- outside wrapper, orchestration, prompt-stack, session-ledger, and memory-support mine

### pi-mono

- outside claw/control shell and session-host pattern mine

### EverMemOS

- outside witness/context memory backend candidate

### MSA

- later backend/model-context candidate, not first-line A2 repair

### Z3

- strongest current formal/runtime family already partially operationalized

## 8. Required Invariants

1. Build specs before claiming architecture.
2. Repair canonical A2 before claiming graph understanding.
3. Do not let `system_v4` shadow or replace canonical `system_v3` A2.
4. Do not call a source family "saved" unless it is in durable trackers and routed into A2 where needed.
5. Do not call a skill "integrated" unless runtime use or an explicit non-runtime status is verified.
6. Keep outside wrappers outside A2 unless formally admitted.

## 9. Write Barrier

Outside wrappers, sidecars, and external memory backends may:

- host sessions
- keep sidecar logs
- store retrieval memory
- supply candidate context
- propose deltas

They may not directly mutate canonical A2 truth by informal side effect.

Canonical A2 mutation must stay on the A2 intake/admission path and remain auditable through repo-held surfaces.

## 10. Minimal Acceptance Gates

Do not claim `v4` progress in these areas unless the corresponding gate is met:

- `A2 persistence`:
  - canonical files exist
  - boot/index paths are current
  - live compatibility profile or full-contract target is explicitly stated
- `skill registry`:
  - rows are valid enough to load
  - loader behavior is verified
- `graph coverage`:
  - graph audit is refreshed against the live registry and current source set
- `runtime integration`:
  - dispatch/use is directly verified or clearly marked partial/non-live
