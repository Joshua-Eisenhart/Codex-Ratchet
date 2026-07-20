# How the sim engines and code run the ratchet and MSS

Grounded in `system_v7/constraint_core/ratchet/ratchet_engine.py` (self-test PASS),
function names cited so every claim is checkable. Marks what EXISTS and RAN vs the GAPS.
Not canon — a spec. The ratchet is CODE; LLMs make and vet fuel, they do not ratchet.

## Part A — the ratchet logic is plain finite code (exists, ran)
MSS is combinatorics on partitions. No LLM, no heavy engine required:

1. **Observation surface X + demand set D.** `generate_observations()` builds finite rows;
   `build_demand_families()` builds D = families of pairs (x,y) that MUST stay distinguished.
2. **Candidate -> partition π.** `_candidate_assignment()` maps a candidate to a partition of
   X (block labels via `_normalise_partition`). π IS the candidate's presentation as a
   probe-relative quotient S/~_M.
3. **L_D(π) = `collapsed_demand_edges`** (per family): counts how many demanded pairs π merges.
   THE ENTROPY-GEOMETRY COFACE — "quotient geometry collapses demanded edges exactly when
   distinguishability information is unresolved." One number.
4. **Survivors** = candidates with L_D = 0 on all active families (preserve every demanded
   distinction).
5. **MSS frontier** = the ⪯-minimal survivors. `_partition_coarser(left,right)` is the
   weakness relation: left is weaker iff it is a coarsening of right. `compute_frontier_cache()`
   keeps the COARSEST survivors (weakest that still separate D). ANTICHAIN — incomparable
   survivors both kept. Never chosen by taste.
6. **Compare two candidates A,B** (the ratchet's only act): compile both to partitions; both
   must survive; `_partition_coarser(π_A,π_B)` — is A a coarsening of B? Yes => A more MSS.
   Neither => incomparable, both stay. RELATIVE only; no absolute MSS.
7. **Drive / tooth.** `_gradient_receipt()`: `coface_collapsed_demand_edge_mass` = the
   load-bearing drive (DRIVE_SURVIVOR when a prior merge is repaired). `quotient_cell_count`
   (size), `raw_outcome_shannon_entropy`, and `label_code_score` are explicitly KILLED_AS_DRIVE
   BY THE CODE — the code itself rejects ornamental gradients.
8. **Aliases collapse.** `explore_candidate_population()` dedups by `partition_digest`:
   32,400 parameter proposals -> 3,147 behavioural classes. "100 near-identical proposals = 1
   effective candidate" is literally implemented, not a slogan.
9. **Admission law (SMT, separate):** SAT_B(C) ∧ UNSAT_B(C ∧ ¬φ), z3 + cvc5, replayed in
   executable semantics = canon-by-process.

## Part B — where the sim engines run (the TARGET; currently a gap)
The Part-A logic is engine-agnostic finite code. The ENGINES produce the BEHAVIORS that induce
the partitions π at step 2. For a REAL candidate manifold (spinor/QIT, classical, octonion), the
engine runs it over the probe set; two observations share a block iff they behave identically
under all probes; that behavior table IS π.
- **JAX:** batched/mass behavior — candidates over large probe/parameter populations, partitions
  at scale (the 32,400->3,147 pattern). "jax can run much of the ratchet."
- **Julia:** authoritative/canon behavior — deep claims (exceptional-algebra conventions,
  high-precision GKSL, octonion/Albert). "needs julia for the deep-level canon claims."
- **PyTorch:** learned-component behavior (JEPA / holodeck candidates).
- **SMT (z3/cvc5):** the admission law + structural-impossibility (UNSAT) proofs.

## Part C — the honest gaps (what does NOT exist yet)
1. The current `ratchet_engine.py` runs on COMBINATORIAL FIXTURES, not real manifolds — it does
   not yet call Julia/JAX/PyTorch. The bridge "engine behavior -> partition -> ratchet input" is
   the key missing engineering.
2. Candidates are PROSE, not executable — nothing compiles to π yet. Fuel-adequacy HOLD.
3. The demand set D must be THICK enough to separate carriers. `base_campaign` ran this exact
   pipeline on 9 base carriers and got `restricting_outer_changes_inner: false` — D too thin.
   (The judge-council is generating thicker rival D families.)
4. NOMINALIST metric as a code question: the code's ⪯ (partition refinement) PLAUSIBLY already
   captures "installed primitive identity" — a candidate that installs A=A imposes the DISCRETE
   (finest) base partition = maximal presumption; a QIT candidate distinguishes only what probes
   force = coarser = less. IF SO, the LLM auditor's error was counting named machinery instead of
   COMPUTING the partition, and the code — run properly — ranks correctly. This is a HYPOTHESIS
   THE CODE DECIDES BY BEING RUN, not an LLM verdict, and not yet run (needs executable
   candidates + a thick enough D).

## The boundary
LLMs / councils PRODUCE and VET fuel (candidates, demand sets D, rival weakness relations).
CODE RATCHETS (Part A). Any LLM output of a ranking or "more MSS" is void (see
RANKING_VOID_llm_did_ratchets_job.md). The ratchet's verdict is a computed partition-order
result — or HOLD.
