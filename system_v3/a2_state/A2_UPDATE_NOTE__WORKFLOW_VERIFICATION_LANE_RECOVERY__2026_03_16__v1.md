# A2_UPDATE_NOTE__WORKFLOW_VERIFICATION_LANE_RECOVERY__2026_03_16__v1

Status: ACTIVE OPERATOR SURFACE / DERIVED_A2
Date: 2026-03-16
Owner: current `A2` controller
Purpose: preserve the workflow-verification upgrade lane that was discussed in-thread but not retained as an active, source-bearing upgrade surface

## Trigger

- The operator restated a first-principles workflow-verification proposal centered on:
  - `TLA+`
  - `Apalache`
  - `Z3`
  - `Z3Py`
  - agent-workflow state-machine verification
- The current system had implied or claimed retooling toward those methods without preserving the actual proposal shape or an active implementation surface.

## Source anchors

- `/home/ratchet/Desktop/29 thing.txt`
- live operator correction in the current controller thread on 2026-03-16
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/A2_UPDATE_NOTE__THREAD_CONTEXT_SALVAGE_AND_FAILURE_RECORD__2026_03_16__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_state/NEXT_PRO_BOOT_SOURCE_ADDITIONS__ENTROPY_CARNOT_SZILARD__2026_03_11__v1.md`

## Recovered proposal shape

The preserved proposal is not "use formal methods" in the abstract.

It is:

- treat agent orchestration workflows as explicit state machines
- model gates, loops, retries, and parallel branches as nondeterministic transitions
- verify:
  - safety invariants
  - liveness / eventual termination properties
  - invalid-state reachability
  - deadlock
  - infinite-loop risk
- use three concrete verification lanes:
  - explicit model checking (`TLA+` / `TLC`)
  - symbolic bounded checking (`Apalache` -> `Z3`)
  - direct constraint solving (`Z3Py`)

## First-principles content that must not be lost

### 1. Universal abstraction

- The target workflows are graph-shaped at the orchestration layer, but verification should reason about them as state machines.
- State includes:
  - current node / cursor
  - loop visit counts
  - branch selections
  - relevant workflow variables
- Actions are transition updates over that state.
- Nondeterminism is first-class rather than something hidden inside testing or LLM behavior.

### 2. Why this lane matters

- Testing checks some execution paths.
- Formal verification checks all reachable paths or all paths within a declared bound.
- The value is highest where the workflow contains:
  - gates
  - retries
  - loops
  - parallel branches
  - tool failure branches
  - human review branches
  - LLM-driven branch choice

### 3. Verification split

#### `TLA+` / `TLC`

- explicit state exploration
- strongest for:
  - reachable-state coverage
  - counterexample traces
  - deadlock checks
- limited by state-space explosion

#### `Apalache` / `Z3`

- symbolic / SMT-backed bounded checking
- strongest for:
  - larger state spaces
  - algebraic reasoning over bounded-depth transition systems
  - checking "does any violating trace exist up to depth k?"

#### `Z3Py`

- direct encoding of focused properties
- strongest for:
  - structural graph constraints
  - bounded policy questions
  - proving impossibility or finding witnesses for narrow properties

### 4. Property split

#### Safety invariants

- cursor always references a valid node
- transition target always exists
- total visits remain bounded
- dependency graph remains acyclic where required
- parallel join preconditions are well-formed
- no undeclared nondeterminism enters execution

#### Liveness / temporal properties

- execution eventually reaches `done` or `fail`
- retries eventually exhaust into a terminal branch
- claims requiring terminal truth state do not remain permanently suspended

### 5. Lev-targeted framing that was supposed to be active

From the recovered proposal:

- Lev's `start()` / `next()` execution contract was being treated as a good verification target because it is already close to a pure transition function.
- The desired loop was:
  - agent writes workflow
  - workflow compiles to graph/state representation
  - verification spec or constraints are generated
  - counterexample traces are produced when invalid
  - the workflow is repaired against those traces
  - repeat until the declared properties pass

### 6. State-space discipline

The recovered proposal was not naive about explosion.

It explicitly relied on boundedness controls such as:

- total visit caps
- bounded loop iterations
- declared branch sets
- bounded-depth symbolic checking
- simulation/sampling when exhaustive exploration is too expensive

## Current repo reality

What is present:

- salvage-level mention that this workflow-verification lane existed
- placeholder packet planning for solver / model-checking / fuzzing imports
- strong existing concern in refined-fuel and simulation-protocol surfaces about declared versus hidden nondeterminism

What is not present as an active implemented lane:

- no active `TLA+` spec set
- no active `Apalache` pipeline
- no active `Z3` or `Z3Py` workflow-verification toolchain for orchestration graphs
- no source-bearing current packet dedicated to this method family
- no active controller/A1 surfaces that truthfully say this lane has already been integrated

## Drift / failure record

- The system appears to have spoken as if this lane were already being retooled in a concrete way.
- The repo currently supports only a much weaker statement:
  - the lane was discussed
  - part of it was remembered in salvage form
  - implementation and source-bearing packetization were not actually completed

## Admissible next move

- Treat this lane as a real outstanding upgrade input.
- Do not claim it is integrated until one of the following exists:
  - a source-bearing external-method packet for workflow verification
  - a bounded `TLA+` workflow spec for one real orchestration surface
  - a bounded `Z3Py` property checker for one real orchestration surface
  - an A2-to-A1 handoff that names the exact first target and proof obligations

## Minimal recovery target

First bounded implementation target should be one real workflow surface with:

- finite node set
- explicit branch declarations
- loop bounds
- terminal states
- invariants:
  - valid cursor
  - bounded total visits
  - no dead terminal-without-status shape
- liveness target:
  - eventually `done` or `fail` under the declared bound

This should be treated as a pilot lane, not as proof that the full workflow-verification architecture is complete.
