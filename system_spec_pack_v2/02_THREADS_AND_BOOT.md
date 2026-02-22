# Threads + Boot (System Spec Pack v2)
Status: DRAFT / NONCANON
Date: 2026-02-20

## Thread Topology (structural roles)
- `THREAD_B`
  - deterministic staged constraint adjudicator
  - owns canonical state (constraint surface)
  - accepts only B-grammar artifact containers

- `THREAD_A0`
  - deterministic orchestrator / compiler
  - packages batches into B-acceptable `EXPORT_BLOCK`
  - owns: run-directory structure, sharding, deterministic logs/outbox

- `THREAD_SIM`
  - deterministic sim executor
  - runs sims and emits `SIM_EVIDENCE` artifacts + run manifests

- `THREAD_A1`
  - nondeterministic planner ("wiggle room")
  - explores candidate space and proposes strategies (requires an LLM or stochastic search)
  - does not write canon directly; outputs are compiled by A0

- `THREAD_A2`
  - nondeterministic mining/drafting/indexing layer
  - produces fuel candidates, overlays, intent memory (noncanon)

## Entropy Layers (intent)
- A2: high entropy (drafting/mining)
- A1: medium entropy (exploration + proposal)
- A0: low entropy (deterministic packaging)
- B: ultra-low entropy (deterministic acceptance/rejection/parking)
- SIM: deterministic execution (evidence)

## Minimum Boot Spine (no ladder required)
1. Load authority corpus:
   - `core_docs/MEGABOOT*`
   - `core_docs/BOOTPACK_THREAD_A*`
   - `core_docs/BOOTPACK_THREAD_B*`
2. Initialize canonical state in B with root constraints:
   - `AXIOM_HYP F01_FINITUDE`
   - `AXIOM_HYP N01_NONCOMMUTATION`
3. Establish a minimal math anchor (a `MATH_DEF`) to bind early term admissions.
4. Start the loop (noncanon unless explicitly sealed):
   - A1 proposes strategy
   - A0 compiles to `EXPORT_BLOCK`
   - B evaluates (accept/reject/park)
   - SIM runs pending sims and emits `SIM_EVIDENCE`
   - B ingests evidence (updates pending + term states)
   - A2 records overlays/feedback (noncanon)

