# Card — adaptive_observation_policy_v0

Lane: adaptive relation-directed observation policy (external review immediate item 2).
Claim ceiling: scratch_diagnostic, promotion_allowed=false. No git commits.

## Gap this card answers
Fixed global observation subsets already FAILED (prior gate red — see
`system_v7/sims/eca_relation_directed_observation_design_v1` lineage). The open
question: does a SEQUENTIAL policy that picks the next observation from the
CURRENT surviving version space identify objects with fewer observations than a
fixed pre-chosen subset — and does it degrade honestly to the fixed baseline
when no observation is more informative than another?

## Object
Finite object-identification game. Ground truth = one of K finite relational
structures. Structures are ECA-like: elementary cellular automaton rules
(transition tables on 3-bit neighborhoods, structural indices only — rule
numbers, cell indices, step indices; no continuous state, no floats in the
object definition).

- Object set: seeded sample (rng seed 0) of ECA rules plus an exhaustive small
  transition-table family (all functions f: {0,1}^2 -> {0,1}, K=16) as a second
  fully exhaustive arena.
- Observation = a query: (initial configuration index, cell index, time step)
  -> observed bit. Finite query pool, enumerated up front.
- Version space V_t = set of candidate objects consistent with all observations
  so far.

## Policies
- Policy A (baseline, known-failed shape): fixed pre-chosen observation subset,
  chosen ONCE before play from the full candidate set (max marginal split on the
  prior, no adaptation). Executes the same queries regardless of answers.
- Policy B (candidate): at each step choose the query that maximally splits the
  CURRENT version space V_t (greedy: minimize the size of the largest answer
  class; ties broken by lowest query index — deterministic).

## Measures (structural indices only)
For each ground-truth object, run A and B with the same query budget:
1. identification rate: fraction of objects driven to |V|=1 within budget.
2. observations-to-identification: number of queries until |V|=1 (budget+1 if
   never identified) — report mean and max per policy.
3. NULL CASE (mandatory negative): an arena where all queries are equally
   informative (symmetric candidate family where every query splits every
   reachable version space into equal classes). B must NOT show an advantage
   over A there; measure and report the gap honestly (expected ~0).
4. Degeneracy check: when B's greedy scores are all equal at every step, B's
   trajectory must reduce to a fixed order — verify and report.

## Constraints
- Pure Python + stdlib only (no torch/jax needed — this is a finite counting
  game). Deterministic: rng seed 0 everywhere, sorted iteration, no set-order
  dependence in output.
- Standalone single script `run.py` in this directory; writes
  `result_v0.json` (append-only: never overwrite — version if rerun) and prints
  headline invariants.
- Positive section (B beats A where structure exists), negative section (null
  arena, no fabricated advantage), boundary section (K=1 trivial, budget=0).

## Pass/fail readouts (printed)
- headline: mean/max queries-to-ID for A vs B in the structured arena.
- null arena: A-vs-B gap (must be ~0; any B advantage there = red flag printed).
- determinism: rerun-stable hash of the result payload (exclude timestamps).

## STOP conditions
- Do not touch anything outside this directory.
- Do not rebuild fixed-global-subset search (that gate is red).
- Do not import from constraint_core.
