# System Meta Plan — Repos, Python, Skills, Hermes

Status: broad umbrella planning surface
Purpose: provide one broad planning surface for the whole system setup before mass installing, testing, patching, deleting, or cleanup work

Use discipline:
- this document is an umbrella map only
- narrower docs should outrank it when they are more specific
- if a narrower doc exists for tools, Hermes, bounded ingestion, QIT proto, lego sims, or skills, that narrower doc should be treated as more authoritative for that topic

This document is intentionally broader than the nonclassical tool-plan doc.
It is meant to hold the high-level map of:
- what the system is trying to become
- what major stacks exist
- what belongs where
- what should be installed and used
- what should be treated as reference-only
- how to proceed slowly and properly

It is not the final truth. It is the master planning surface to audit and improve.

---

## 1. Governing principles

1. Do planning before mass installs, mass tests, or mass deletions.
2. Do not ask Hermes to read the whole system at once.
3. Feed Hermes bounded packs, slowly, with explicit roles.
4. Do not let underpowered sims or green validators count as real closure.
5. Do not delete old environments or folders until replacements are installed, tested, and patched in.
6. Keep Git repos in `~/GitHub`.
7. Keep the main repo on Desktop for now.
8. Standardize Python/tooling first, then clean up redundancy.
9. Only keep a tool if it has a named job in the pipeline.
10. Hermes is not just a tool: Hermes is part of the architecture.

---

## 2. Core strategic direction

### 2.1 Immediate scientific priority
The immediate priority is not “finish all of v5.”
The immediate priority is:
- get the QIT engine prototype ratcheted properly
- get real pre-Axis sims working
- make those sims honest, rich, and scientifically respectable
- use those sims to build a legitimate substrate for the broader system

### 2.2 Broader system priority
The larger system should eventually inherit the shape of the QIT engines.
The system graphs and architecture should reflect the engine and its constraints.
The broader system should later help ratchet the engines even further.

### 2.3 Hermes priority
Hermes is effectively the A2 high-entropy ingestion plane.
So Hermes itself, its add-ons, and its improvement surfaces are first-class planning objects.

---

## 3. Main stack categories

This meta doc tracks five major stacks:

1. QIT engine / pre-Axis sim stack
2. Proof / graph / geometry / witness tooling stack
3. Python/environment/install stack
4. Skills stack
5. Hermes stack

These stacks overlap, but they should not be collapsed into one blur.

---

## 4. QIT engine / pre-Axis sim stack

### 4.1 Central method
The sim method is:
- start from root constraints
- constraints restrict admissible math and geometry
- build small sims as legos
- prove/pressure-test lower structure first
- compose upward only from admitted or clearly fenced pieces
- finish the pre-Axis ladder before real Axis-entry work

### 4.2 Why this comes first
The QIT engine prototype is the immediate scientific substrate.
It needs to be legitimate enough to:
- support real scientific work
- attract collaborators
- justify funding
- narrow branches honestly
- support later system architecture

### 4.3 Pre-Axis emphasis
Before Axis 0, the system needs real work on:
- root constraints
- carrier ladder
- nested geometry
- transport law
- differential / chirality / flux surfaces
- negatives
- placement
- witness/provenance

### 4.4 Standard
The standard is not “did a script run?”
The standard is:
- is it rich enough?
- is it constrained enough?
- did it use the required tools?
- did it emit the required artifacts?
- did it survive negatives?

### 4.5 Current style rule
No toy-flat sims may support geometry or Axis claims.
All underpowered sims are `diagnostic_only`.

---

## 5. Proof / graph / geometry / witness stack

This stack exists to stop:
- classical smoothing
- prose-normalization
- fake closure
- scalar reduction of rich geometry
- graphless “state” claims
- proofless promotion

### 5.1 Owner stack
Canonical owner stack:
- `pydantic`
- `jsonschema`
- `networkx`
- `GraphML`
- witness/event recording
- `pytest`
- `hypothesis`
- `z3`

Role:
- schemas, artifacts, graphs, contracts, proofs, witnesses, gates

### 5.2 Rich augmentation stack
Rich geometry/graph stack:
- `torch`
- `PyG`
- `TopoNetX`
- `clifford`
- `pyquaternion`
- `kingdon`
- `hypernetx`
- `xgi`

Role:
- tensors, heterographs, higher-order topology, noncommutative/orientation-aware structure, spinor/quaternion layer

### 5.3 Fresh additions now considered important
Fresh additions with named jobs:
- `cvc5`
- `sympy`
- `gudhi`
- `ripser.py`
- `egglog`

Role:
- synthesis/refinement
- exact symbolic pressure
- topology-pressure on the geometry ratchet
- rewrite/equivalence pressure

### 5.4 Lower-priority later formalization
Later, not first-line:
- `Lean + mathlib`

Reason:
- useful for stable exact lemmas later
- not the main engine right now

---

## 6. Python / environment / install stack

### 6.1 Main repo location
Main repo remains:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet`

### 6.2 Git repo location
Git repos remain:
- `/Users/joshuaeisenhart/GitHub`

### 6.3 Python/tooling cleanup principle
Do not literally “move everything” first.
Instead:
- choose the canonical Python base
- install and test there
- patch the repo to use it
- delete redundant old environments later

### 6.4 Current likely canonical base
Current evidence points to Homebrew Python as the natural canonical base.
That means the interpreter family under `/opt/homebrew` should likely be treated as canonical.

### 6.5 Clean folder for Python-related organization
Chosen clean external folder:
- `/Users/joshuaeisenhart/python`

This is a planning/organization target.
It does not mean everything must be physically moved there immediately.

### 6.6 Repo-local venv cleanup target
Main obvious cleanup target inside the repo:
- `.venv_spec_graph`

But it is not deletable yet because:
- repo files still reference it
- replacement path must be documented and tested first

### 6.7 Main Python rule
No cleanup by deletion until:
- canonical path is documented
- required tools are installed and tested there
- repo hardcoded references are patched
- critical probes/runners pass

---

## 7. Skills stack

### 7.1 Why skills matter
Skills are part of how the system becomes operational instead of just documented.
They matter for:
- recurring audits
- recurring install tasks
- recurring sim workflows
- recurring proof/graph workflows
- bounded Hermes ingestion workflows

### 7.2 Skill categories that matter now
Current important skill categories:
- QIT/sim audit skills
- graph tooling skills
- proof tooling skills
- bounded-ingestion skills
- cleanup/inventory skills
- Hermes-improvement skills

### 7.3 Skills must be tied to real workflow
A skill should only be kept or built if it has a real recurring job.
No decorative skills.
No stale skills.

### 7.4 Immediate skill priorities
Immediate skill work should focus on:
- bounded intake / audit procedures
- graph/proof/sim setup procedures
- Hermes stack setup/improvement procedures
- pre-Axis sim contract procedures

### 7.5 Longer-term skill direction
Later, skills can help:
- build the broader v5 system
- improve Hermes behavior
- automate more of the QIT engine workflow

---

## 8. Hermes stack

### 8.1 Hermes is first-class
Hermes is not just a convenience CLI.
Hermes is effectively the A2 high-entropy ingestion plane.
That makes Hermes part of the architecture.

### 8.2 What “Hermes extensions” means
Hermes extensions means:
- Hermes itself
- repos built around Hermes
- tools and layers built to make Hermes better
- stacking/planning work for Hermes
- Hermes self-improvement and ingestion support surfaces

This does NOT just mean random plugins.

### 8.3 Hermes-related repo surfaces
Important Hermes-related surfaces include at least:
- Hermes core repo(s)
- `hermes-agent-self-evolution`
- curated Hermes ecosystem material like `awesome-hermes-agent`
- local Hermes skill directories / Hermes-adjacent tooling

### 8.4 Hermes planning priority
Hermes install/use planning should include:
- core Hermes setup
- Hermes add-ons/improvements
- Hermes self-evolution / self-improvement research inputs
- Hermes skill ecosystem inputs
- bounded ingestion workflow for Hermes

### 8.5 Hermes role in this system
Hermes should be used to:
- process bounded high-entropy doc packs
- support planning and audits
- help construct the broader system
- help refine the QIT engine work

Hermes should NOT be asked to:
- ingest the whole system at once
- smooth over ambiguity
- narrate false closure

### 8.6 Hermes feed rule
Feed Hermes slowly.
Bounded packs only.
Explicit task and role only.
No “understand the whole repo” prompts.

---

## 9. External/reference repo stack

### 9.1 Why this exists
Reference repos matter because they contain:
- proof/search methods
- agent-improvement ideas
- graph methods
- scientific method ideas
- implementation patterns

### 9.2 Important known reference surfaces
Known important surfaces include things like:
- `alphageometry`
- `z3`
- `dreamcoder-ec`
- `autoresearch`
- `llm-council`
- Hermes-related repos
- Leviathan-related repos
- `pi-mono`

### 9.3 Use rule for reference repos
A reference repo should be marked as one of:
- active dependency
- reference only
- method mine
- later integration candidate
- ignore / stale

No repo should just exist in the plan as a vague inspiration blob.

---

## 10. Documents already created that feed into this meta doc

This meta doc sits above several narrower documents.
Currently important feeder docs include:
- `NONCLASSICAL_SYSTEM_TOOL_PLAN.md`
- `PYTHON_REPO_SKILLS_INVENTORY_AND_CLEANUP_PLAN.md`
- `FULL_MACHINE_PYTHON_REPO_SKILLS_INVENTORY.md`

Those docs remain useful.
This document is the broader umbrella planning surface.

---

## 11. What should happen first

### 11.1 Immediate install/use priorities
Before mass cleanup or broad refactors:
1. stabilize Hermes + Hermes improvements/add-ons
2. stabilize graph/proof/geometry tool stack
3. define bounded Hermes ingestion workflow
4. refine skills plan
5. push the QIT engine proto sims forward using the proper stack

### 11.2 Immediate scientific priority
The first real scientific substrate should be:
- a bounded, rich, honest pre-Axis QIT-engine sim program
- small sims as legos
- compose upward slowly
- get this legitimate before broader system inflation

### 11.3 Immediate cleanup priority
Cleanup starts with:
- Python/tooling standardization
- not mass deletion
- not moving repos around
- not deleting `.venv_spec_graph` yet

---

## 12. What not to do yet

Do not:
- mass install everything because it sounds useful
- mass delete old folders/environments
- ask Hermes to ingest the whole system
- treat green validators as enough without substrate compliance
- move Git repos out of `~/GitHub`
- try to finish all of v5 before the QIT engine proto sim substrate is real

---

## 13. Next documents that should exist after this one

Likely next formal documents:
- `CURRENT_TOOL_STATUS__INSTALLED_VS_MISSING_VS_NOT_WIRED.md`
- `HERMES_STACK_AND_ADDONS_PLAN.md`
- `SKILLS_PLAN__KEEP_BUILD_PATCH_RETIRE.md`
- `QIT_ENGINE_PROTO_RATCHET_AND_SIM_PLAN.md`
- `LEGO_SIM_CONTRACT.md`

---

## 14. Current best summary

The system should be built in this order:
- get Hermes itself and its add-ons/improvement surfaces solid
- get graph/proof/geometry tooling solid
- feed Hermes bounded packs slowly
- work on skills in the same disciplined way
- get the QIT engine proto sims legitimate from the root constraints upward
- let the larger v5 system grow out of that scientific substrate

This meta doc exists so installs, tests, cleanup, and planning can all be judged against one broad system picture.
