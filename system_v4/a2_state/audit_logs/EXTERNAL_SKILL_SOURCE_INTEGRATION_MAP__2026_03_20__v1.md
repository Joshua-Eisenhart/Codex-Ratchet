# EXTERNAL_SKILL_SOURCE_INTEGRATION_MAP__2026_03_20__v1

generated_utc: 2026-03-20T21:30:00Z
status: bounded_source_integration_audit
scope: lev_nonclassical_runtime_design + lev-os/agents + lev-os/leviathan/workshop + karpathy + sat/smt/z3

## Purpose

Turn the current "use these too" intent into a concrete integration map for `system_v4`, without pretending the external sources are already wired into the live runner.

This audit treats the external materials as:

1. source surfaces for new skills
2. source surfaces for new workflow/admission machinery
3. source surfaces for new runtime operators and validation passes

It does **not** treat them as drop-in doctrine.

## Verified Source Surfaces

### Local Lev Runtime Audit

- source: `/home/ratchet/Desktop/Codex Ratchet/core_docs/v4 upgrades/lev_nonclassical_runtime_design_audited.md`
- key value:
  - explicit retool rule: keep useful process, identify flattening assumption, retool for finitude + non-commutation
  - strong alignment with Lev's `Topology -> Orchestration -> Dispatch` split
  - direct sections for:
    - Karpathy design philosophy
    - nanochat
    - autoresearch
    - llm-council
    - SAT / SMT
    - model checking
    - abstract interpretation
    - fuzzing
    - constrained decoding
    - build / reproducibility systems

### lev-os/agents

- source repo: `https://github.com/lev-os/agents`
- inspected clone: `/tmp/lev_os_agents`
- observed shape:
  - `47` skill folders under `/tmp/lev_os_agents/skills`
  - a runtime helper at `/tmp/lev_os_agents/lev-skills.sh`
  - notable workflow skills:
    - `/tmp/lev_os_agents/skills/lev-workshop/SKILL.md`
    - `/tmp/lev_os_agents/skills/skill-builder/SKILL.md`
    - `/tmp/lev_os_agents/skills/lev-builder/SKILL.md`
    - `/tmp/lev_os_agents/skills/lev-align/SKILL.md`
- import-worthy patterns:
  - workshop lifecycle: intake -> analysis -> POC -> poly integration
  - repo/doc/PDF-to-skill codification workflow
  - explicit placement/migration workflow from POC to production path
  - validation-gates-based alignment checks

### lev-os/leviathan

- source repo: `https://github.com/lev-os/leviathan`
- inspected clone: `/tmp/lev_os_leviathan`
- observed shape:
  - large host runtime with `core`, `plugins`, `context`, `.lev`, `crates`, and `workshop`
  - workshop surface at `/tmp/lev_os_leviathan/workshop`
  - analysis surfaces at `/tmp/lev_os_leviathan/workshop/analysis`
- especially relevant files:
  - `/tmp/lev_os_leviathan/workshop/analysis/IMPLEMENTATION_ROADMAP.md`
  - `/tmp/lev_os_leviathan/workshop/analysis/jp-lev-vision/vision.md`
  - `/tmp/lev_os_leviathan/workshop/analysis/agent-skills-context/analysis.md`
- import-worthy patterns:
  - workshop as capability factory
  - star-based skill model (`lev` core + `lev-*` companion skills)
  - capability inheritance per node
  - ephemeral task container -> static promoted node model
  - context engineering / agent skills intake and extraction patterns

### Karpathy Surfaces

- source anchor:
  - `https://github.com/karpathy`
  - local design interpretation in `/home/ratchet/Desktop/Codex Ratchet/core_docs/v4 upgrades/lev_nonclassical_runtime_design_audited.md`
- import-worthy pattern:
  - small core
  - visible loop
  - bounded mutation
  - explicit evaluation
  - minimal abstraction overhead

### SAT / SMT / Z3

- source anchor:
  - local SAT / SMT section in `/home/ratchet/Desktop/Codex Ratchet/core_docs/v4 upgrades/lev_nonclassical_runtime_design_audited.md`
- import-worthy pattern:
  - local hard incompatibility detection
  - minimal failure-set extraction
  - compile/gate checks, not worldview replacement

## Current system_v4 Extension Seams

These are the real places where the above sources would have to enter the live stack.

### 1. Canonical Skill Inventory

- file: `/home/ratchet/Desktop/Codex Ratchet/system_v4/a1_state/skill_registry_v1.json`
- role:
  - declares repo-derived skills and external Codex-backed skills
  - binds trust zones, graph families, capabilities, adapters, and execution paths
- current truth:
  - external Codex skill paths are already admitted here
  - this means admission is partially open, but mostly manual

### 2. Skill Discovery / Admission Logic

- file: `/home/ratchet/Desktop/Codex Ratchet/system_v4/skills/skill_registry.py`
- role:
  - loads the registry snapshot
  - filters by zone/capability via `find_relevant()`
  - resolves adapters via `resolve_adapter()`
  - enforces metadata hygiene via `health_pass()`
- current truth:
  - discovery is static JSON based
  - there is no workshop-style doc/repo-to-skill intake pipeline yet

### 3. Live Runtime Binding

- file: `/home/ratchet/Desktop/Codex Ratchet/system_v4/skills/run_real_ratchet.py`
- role:
  - selects candidate phase skills
  - resolves execution adapters
  - requires actual `SKILL_DISPATCH` bindings for execution
- current truth:
  - registry can know about many skills
  - runner execution is still mostly hard-wired in `SKILL_DISPATCH`

### 4. Graph Reflection of Skills

- file: `/home/ratchet/Desktop/Codex Ratchet/system_v4/skills/runtime_graph_bridge.py`
- role:
  - projects skills into graph form
  - prunes stale skills
  - anchors isolated skills via hub mapping
- current truth:
  - if external skill families are admitted more broadly, this bridge will need additional anchoring rules

### 5. Extension Safety Tests

- files:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v4/skills/test_upstream_phase_selection_smoke.py`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v4/skills/test_phase4_skill_dispatch_smoke.py`
- role:
  - protect phase-runner metadata
  - protect adapter-to-dispatch binding expectations
- current truth:
  - these are the right tests to extend when new external/repo-derived skills become executable

## Integration Reading

### What lev-os/agents contributes best

- skill catalog shape
- skill discovery / codification workflow
- workshop lifecycle pattern
- alignment/validation gate pattern

This is most useful for:

- skill admission
- skill authoring
- workshop routing
- migration from POC/prototype to production paths

### What leviathan/workshop contributes best

- large-scale intake/analysis/POC workflow
- comparative repository analysis culture
- star-based `lev-*` capability model
- node capability inheritance and promotion thinking

This is most useful for:

- skill family taxonomy
- companion-skill packaging
- workshop-to-production promotion
- static-vs-ephemeral execution model design

### What the local Lev runtime audit contributes best

- the retool filter
- the nonclassical runtime model
- the implementation posture for Karpathy / SAT / model checking / synthesis methods

This is most useful for:

- deciding what should become a real runtime operator vs just a helpful document
- preventing framework import drift

## Recommended Next Lanes

These are ordered to create real progress without pretending the full external import is already done.

### Lane 1: External Skill Admission Inventory

goal:
- admit externally sourced skill surfaces in a workshop-like staging layer before they touch the live registry

why first:
- `system_v4` already knows how to store external skill paths
- it does **not** yet have a truthful intake/staging/admission path for them

concrete target:
- add a repo-held inventory/admission surface for:
  - local doc-derived candidate skills
  - repo-derived candidate skills
  - status: staged / approved / rejected / promoted

insertion points:
- `/home/ratchet/Desktop/Codex Ratchet/system_v4/skills/skill_registry.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v4/a1_state/skill_registry_v1.json`

### Lane 2: Workshop Lifecycle Import

goal:
- mirror the `lev-workshop` four-phase lifecycle inside the Codex Ratchet controller as a bounded workflow

why:
- this is the cleanest way to turn "build skills from docs/repos" into repeatable work

concrete target:
- create a bounded workshop intake/integration audit surface for:
  - intake
  - analysis
  - POC
  - promotion

source surfaces:
- `/tmp/lev_os_agents/skills/lev-workshop/SKILL.md`
- `/tmp/lev_os_agents/skills/lev-builder/SKILL.md`
- `/tmp/lev_os_agents/skills/lev-align/SKILL.md`

### Lane 3: SAT/SMT/Z3 Local Gate Skill

goal:
- introduce a minimal local hard-incompatibility checker skill rather than vague “use z3 more”

why:
- the local runtime audit already frames SAT/SMT the right way: local contradiction/gate extraction only

concrete target:
- bounded skill for:
  - local incompatibility detection
  - failure-set reporting
  - gate-only use, not global ontology enforcement

source surface:
- `/home/ratchet/Desktop/Codex Ratchet/core_docs/v4 upgrades/lev_nonclassical_runtime_design_audited.md`

### Lane 4: Karpathy Minimal-Core Audit

goal:
- audit the growing control plane against “small core, visible loop, bounded mutation”

why:
- this is a real counterweight to registry/runner bloat

concrete target:
- a repo-held audit against:
  - unnecessary abstraction layers
  - hidden mutation
  - unclear loop boundaries
  - non-minimal dispatch plumbing

### Lane 5: JP / Star-Skill Packaging Map

goal:
- map current skill families to a `lev core + lev-* companions` style packaging surface

why:
- JP's star-based vision is directly relevant to how our skills are proliferating

source surface:
- `/tmp/lev_os_leviathan/workshop/analysis/jp-lev-vision/vision.md`

concrete target:
- classify current families into:
  - core runtime skill
  - companion workflow skills
  - optional operator packs

## Honest Constraints

- The external repos are rich source material, but they are not yet integrated into live `system_v4` execution.
- The current runner is still manual-dispatch heavy.
- `system_v4` does not yet have a truthful external skill workshop/admission pipeline.
- Z3/SAT integration should begin as a narrow gate operator, not a broad substrate rewrite.

## Recommended Immediate Next Step

Build **Lane 1** first:

`EXTERNAL_SKILL_ADMISSION_STAGING`

Reason:
- it is the cleanest bridge between the external source surfaces and the current registry/runner architecture
- it makes later Karpathy/Z3/workshop imports tractable instead of ad hoc
