# MASTER_INTEGRATION_AND_SKILLIZATION_MAP__2026_03_20__v1

Corrective note 2026-03-21:

- the live skill/graph counts in this historical planning note are now stale
- current live state is `88` active registry skills, `88` graphed `SKILL` nodes, `0` missing, `0` stale
- use [GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/a2_state/audit_logs/GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.md) and the front-door corpus docs for current truth

generated_utc: 2026-03-20T23:59:00Z
surface_class: DERIVED_A2
status: integration_planning_map
scope: skills + repos + staged external sources + pi-mono + EverMem/EverMind request + Z3 + Karpathy patterns + nested graph placement

## Purpose

Turn the current "use all of these too" intent into one repo-held map that says:

1. what is already live
2. what is only staged or partially integrated
3. what should become first-class skills
4. where each integration belongs in the layered system
5. what order to build next

This note is a planning and placement surface, not doctrine and not earned runtime truth.

Canonical durable owner surface for this concern:

- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/REPO_SKILL_INTEGRATION_TRACKER.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/SKILL_CANDIDATES_BACKLOG.md`

## Current Live State

### Graph / Layer State

- live nested graph currently projects `11` layers in `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/graphs/nested_graph_v1.json`
  - `INDEX`
  - `A2_HIGH_INTAKE`
  - `A2_MID_REFINEMENT`
  - `A2_LOW_CONTROL`
  - `A1_JARGONED`
  - `A1_STRIPPED`
  - `A1_CARTRIDGE`
  - `A0_COMPILED`
  - `B_ADJUDICATED`
  - `SIM_EVIDENCED`
  - `GRAVEYARD`
- current nested build program is paused with `NO_CURRENT_WORK__DIRECT_ENTROPY_EXECUTABLE_PAUSED` in `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/NESTED_GRAPH_BUILD_PROGRAM__2026_03_20__v1.json`

### Skill State

- `82` active skills in `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a1_state/skill_registry_v1.json`
- skill graph coverage is now complete in `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/GRAPH_CAPABILITY_AUDIT__2026_03_20__v1.json`
  - `82` active skills
  - `82` graphed `SKILL` nodes
  - `0` missing
  - `0` stale
  - `0` isolated
- remaining integration weakness is depth, not presence
  - `37` skill nodes still have only one graph edge
  - this means they are graph-native, but many are still shallowly integrated

### Runtime / Verification State

- the nonclassical runtime / Z3 family is real on disk
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/skills/runtime_state_kernel.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/skills/witness_recorder.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/skills/z3_constraint_checker.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/skills/z3_cegis_refiner.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/skills/property_pressure_tester.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/skills/differential_tester.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/skills/structured_fuzzer.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/skills/model_checker.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/skills/bounded_improve_operator.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/skills/fep_regulation_operator.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/skills/frontier_search_operator.py`
- intent is first-class across witness -> graph -> control
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/skills/intent_refinement_graph_builder.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/skills/intent_control_surface_builder.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/skills/intent_runtime_policy.py`

## Source Bundles And Their Real Status

### 1. Lev Nonclassical Runtime Design

- source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/v4 upgrades/lev_nonclassical_runtime_design_audited.md`
- status:
  - partially landed
- already expressed as real skills:
  - runtime kernel
  - witness recorder
  - Z3 / checking / fuzzing / model checking family
  - bounded improve
  - FEP regulation
  - frontier search
- key note:
  - this source is already shaping the runtime; it is not just staged

### 2. lev-os/agents

- mapped in:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/EXTERNAL_SKILL_SOURCE_INTEGRATION_MAP__2026_03_20__v1.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a1_state/external_skill_admission_staging_v1.json`
- status:
  - staged only
- current best use:
  - workshop lifecycle
  - skill-builder patterns
  - alignment / validation gates
- not yet true:
  - no live workshop-style repo/doc -> skill intake loop exists yet

### 3. lev-os/leviathan + JP Vision

- mapped in:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/EXTERNAL_SKILL_SOURCE_INTEGRATION_MAP__2026_03_20__v1.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a1_state/external_skill_admission_staging_v1.json`
- status:
  - staged only
- current best use:
  - workshop-to-production promotion model
  - star-style companion-skill packaging
  - node capability inheritance thinking

### 4. Karpathy Bundle

- mapped in:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/REFERENCE_REPOS.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a1_state/external_skill_admission_staging_v1.json`
- current local truth:
  - `autoresearch` and `llm-council` exist mainly as patterns, not yet as first-class live skills
  - bounded improve is the closest current runtime expression of the autoresearch loop
- recommendation:
  - promote `autoresearch` and `llm-council` into explicit skills/operators instead of continuing to reference them only conceptually

### 5. Z3 / SAT / SMT

- mapped in:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/REFERENCE_REPOS.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/audit_logs/EXTERNAL_SKILL_SOURCE_INTEGRATION_MAP__2026_03_20__v1.md`
- status:
  - landed as real runtime family
- strongest current expression:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/skills/z3_constraint_checker.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/skills/z3_cegis_refiner.py`
- note:
  - Z3 is the most integrated external method family so far

### 6. pi-mono

- local sources already ingested via:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/session_logs/DEEP_FUEL_PIMONO_SESSION.md`
- source paths already pulled into A2 mining:
  - `~/GitHub/pi-mono/packages/agent/README.md`
  - `~/GitHub/pi-mono/packages/ai/README.md`
  - `~/GitHub/pi-mono/packages/coding-agent/README.md`
  - `~/GitHub/pi-mono/packages/mom/README.md`
  - `~/GitHub/pi-mono/packages/pods/README.md`
  - `~/GitHub/pi-mono/packages/tui/README.md`
  - `~/GitHub/pi-mono/packages/web-ui/README.md`
  - `~/GitHub/pi-mono/AGENTS.md`
- status:
  - graph-ingested as source material
  - not yet skillized as a dedicated integration family
- key note:
  - pi-mono is already in the graph; it is not yet operationally bound into runtime skills

### 7. EverMemOS / EverMind-AI Bundle

- source status:
  - requested in current user intent and summarized in the current thread
  - not yet locally cloned or staged in repo-held external admission surfaces
- user-provided assessment says:
  - EverMemOS is useful as a memory service and semantic/episodic retrieval backend
  - MSA is useful later as a long-context model/backend layer
- current safest interpretation:
  - EverMemOS belongs first in the memory/witness integration lane
  - MSA belongs later in the model/backend audit lane
- important note:
  - these should not be treated as locally verified imports until repo-local source capture exists

### 8. The 29-Method Source Doc

- the canonical local referent is the source document:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/v4 upgrades/29 thing.txt`
- that document is already graph-ingested and session-tracked:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/a2_state/session_logs/OPUS_DEEP_READ_29_THING.md`
- the live cross-validation cluster is real, but it is separate and must not be substituted for the source doc:
  - `CROSS_VAL: 29 sources, 29 batches, 30 edges`
- corrected interpretation:
  - the intended referent is the external-method source doc `29 thing.txt`
  - the `29 sources / 29 batches` cluster is a separate graph artifact that may support downstream cross-validation work but is not the canonical referent

## What Should Become First-Class Skills

### A. Memory / Context Skills

These belong closest to witness, intent, A2 memory, and external memory backends.

- `evermem-memory-backend-adapter`
  - role:
    - adapter to EverMemOS REST memory service
  - layer:
    - runtime bridge / external backend adaptor
- `witness-evermem-sync`
  - role:
    - push append-only witness corpus entries into EverMemOS
  - layer:
    - post-witness / post-graph bridge
- `intent-memory-loader`
  - role:
    - pull relevant external memory into startup intent/context seeding
  - layer:
    - pre-A1 / pre-intent-control
- `pimono-evermem-adapter`
  - role:
    - connect pi-mono agent context retrieval to EverMemOS
  - layer:
    - external adaptor / pi-mono family

### B. Research / Deliberation Skills

These belong in A2 refinement and controller-style bounded improvement, not in earned runtime truth.

- `autoresearch-operator`
  - role:
    - explicit Karpathy-style bounded self-improvement loop
  - status now:
    - conceptually present, should become explicit
- `llm-council-operator`
  - role:
    - structured multi-view disagreement and synthesis
  - layer:
    - A2-2 contradiction / deliberation
- `repo-pattern-miner`
  - role:
    - mine external repos into candidate patterns / skill stubs
  - layer:
    - workshop intake
- `external-skill-admission-operator`
  - role:
    - turn staged external bundles into reviewed candidate skills
  - layer:
    - workshop / admission

### C. Workshop / Promotion Skills

These belong in the external-source-to-skill factory rather than the live runner.

- `workshop-intake-operator`
- `workshop-analysis-operator`
- `workshop-poc-operator`
- `workshop-promotion-operator`
- `skill-family-packager`
- `skill-alignment-gate`

These are the cleanest imports from `lev-os/agents` and `leviathan/workshop`.

### D. Model / Backend Audit Skills

These should exist before any heavy backend change is treated as runtime-ready.

- `msa-capability-audit`
  - role:
    - evaluate whether MSA belongs in current system constraints
- `msa-backend-selector`
  - role:
    - choose long-context backend only when needed and supported
- `long-context-capability-probe`
  - role:
    - bounded test lane for extremely large context handling

## Where Each Family Belongs

### A2_HIGH_INTAKE

Use for:

- repo/doc intake
- workshop-source analysis
- external repo pattern mining
- pi-mono repo ingestion
- EverMem/MSA source capture once local

### A2_MID_REFINEMENT

Use for:

- Karpathy pattern refinement
- llm-council deliberation
- contradiction-preserving comparison of external source bundles
- external admission decisions

### A2_LOW_CONTROL

Use for:

- promotion gating
- quarantine / readiness decisions
- "staged / approved / rejected / promoted" state machines

### Witness / Runtime Bridge Layer

Use for:

- witness capture
- intent/context persistence
- EverMem sync
- external memory retrieval seeding

### A1_JARGONED / A1_STRIPPED

Use for:

- proposal-only distillation from refreshed A2
- not for source import itself

### B / SIM / Earned Runtime

Use for:

- Z3 / property testing / fuzzing / model checking
- fail-closed validation
- never for imported repo doctrine

### External Backend / Non-owner Adaptor Space

Use for:

- EverMemOS service binding
- pi-mono adaptor hooks
- MSA experiments

Keep these fail-closed and non-doctrinal until they prove value locally.

## Recommended Integration Order

### Phase 1. Finish Skillization Of Existing Pattern-Only Ideas

Promote these first:

- `autoresearch-operator`
- `llm-council-operator`
- workshop/admission family

Why:

- they already exist in local intent and source maps
- they do not require external service dependency first

### Phase 2. Wire EverMem Into Codex Ratchet First

Recommended first target:

- Codex Ratchet witness/intent system

Why first:

- local system is already append-only and graph-backed
- witness corpus has clear objects to sync
- startup intent/context loading is already a real seam
- easier to test than a cross-repo pi-mono hook first

Concrete sequence:

1. `evermem-memory-backend-adapter`
2. `witness-evermem-sync`
3. `intent-memory-loader`

### Phase 3. Then Add pi-mono Adaptor Skills

Recommended second target:

- pi-mono `packages/agent`
- pi-mono `packages/ai`

Why second:

- once EverMem semantics and payload shapes are stable in Ratchet, the same adaptor pattern can be reused for pi-mono
- keeps the first backend binding inside the repo we already control

Concrete sequence:

1. `pimono-evermem-adapter`
2. `pimono-agent-memory-loader`
3. `pimono-context-sync-audit`

### Phase 4. MSA Only After Memory And Skill Routing Are Working

Recommended posture:

- treat MSA as a later backend capability, not an immediate skill drop-in

Why later:

- it is model/backend architecture, not just a new control skill
- current bottleneck is memory/control integration, not 100M-token context

## Clear Recommendation On EverMem Target

Start with **Codex Ratchet witness system first**, then pi-mono.

Reason:

- Ratchet already has first-class intent, context, witness, and graph seams
- EverMem maps naturally onto those seams
- once that binding is proven, pi-mono can be attached as a second consumer

## Clear Recommendation On Deployment Posture

Start with **local Docker first**, not hosted.

Reason:

- witness corpus and maker-intent surfaces are sensitive
- local Docker is the cleanest fail-closed evaluation lane
- hosted memory should wait until payload boundaries, retention rules, and sync contracts are explicit

## Concrete Next Tranche

1. Create a repo-held `EverMem / pi-mono / MSA` admission staging bundle.
2. Create first-class skills:
   - `autoresearch-operator`
   - `llm-council-operator`
   - `evermem-memory-backend-adapter`
   - `witness-evermem-sync`
3. Add graph-native `SKILL` records for those skills on admission.
4. Add focused smokes:
   - witness -> EverMem sync smoke
   - EverMem retrieval -> startup context seed smoke
   - `autoresearch-operator` bounded loop smoke
   - `llm-council-operator` disagreement-preserving smoke
5. Only after that, add pi-mono-specific adaptor skills.

## Bottom Line

The system now has the right substrate for this:

- all active skills are graphed
- intent is first-class
- witness is append-only
- external source staging already exists
- pi-mono is already graph-ingested
- Z3 is already operational

The next move is not "talk about more repos." It is:

1. skillize the pattern-only families
2. stage EverMem properly
3. bind memory into witness/intent first
4. then bridge pi-mono
5. keep every new skill graph-native from day one
