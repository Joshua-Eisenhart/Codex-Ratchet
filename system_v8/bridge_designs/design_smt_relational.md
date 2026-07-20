# SMT-Relational Common Finite Observation Surface + Trace→Partition Bridge

**Status:** Conditional design proposal (fuel). Not executed. Not a claim.  
**Claim ceiling:** Packet-relative engineering sketch for one possible trace-to-partition bridge under the nominalist ratchet. No scientific, physical, or canonical status. `promotion_allowed: false`. `formal_admission_allowed: false`.  
**Date:** 2026-07-20  
**Assigned seed:** SMT-relational (encode candidate behaviour as finite relations over a shared vocabulary; z3+cvc5 decide distinguishability; partition induced from the SAT/UNSAT profile).  
**Scope:** Common observation surface X and the bridge that turns engine traces into partitions π that the existing ratchet kernel (L_D, frontier, refinement order) can consume. Does not design new candidates, new D families, or new engines.

## 1. The problem this bridge must solve

Rival carriers (classical relational, spinor/QIT density-matrix, octonion/nonassociative) must be comparable by one metric: partition coarseness on a shared finite observation surface.

Two observations belong in the same block of π_C for carrier C exactly when they are indistinguishable under every probe and every tracked continuation that C can express.

The ratchet kernel already implements the rest:
- L_D(π) counts how many demanded edges a partition collapses.
- Survivors carry all active D.
- Frontier = coarsest survivors under refinement (π ≼ ρ when every block of ρ sits inside a block of π).

The missing piece is step 4–5 in the operational wiring: engines emit finite behaviour traces; code must turn those traces into comparable partitions without giving any carrier a privileged probe language.

The base_campaign run already exhibited the failure mode: with a thin static D on two packets, all nine executable base carriers produced `restricting_outer_changes_inner: false`. Neutral surface + weak demands collapsed everything. Rich carrier-specific probes would beg the question.

The bridge must therefore:
- Use one finite alphabet and one probe/update vocabulary for all carriers.
- Span continuations (next-state behaviour, persistence, evolvability).
- Let structural differences appear as differences in which observations remain separable after admissible updates.
- Feed the resulting π directly into the existing L_D / refinement machinery.

## 2. Design principle: SMT-relational

Shared vocabulary V (sorts + relation symbols) is fixed and minimal.  
Each candidate carrier C, when executed on the finite surface, compiles to a finite theory (or ground model plus carrier-specific axioms) M_C over V.  
Two observations x, y are placed in the same block of π_C if and only if M_C makes them indistinguishable: no ground fact or entailed consequence over the common symbols separates them.

z3 and cvc5 are used to decide distinguishability:
- SAT for "there exists an interpretation consistent with C's rules in which x and y differ on at least one observable response or continuation image" → distinct blocks.
- UNSAT → they are forced indistinguishable under C → same block.

The partition is the equivalence relation induced by these decisions (or, more practically, by extracting the committed response signature for every observation, including its continuation tree, and grouping identical signatures that are also consistent with C's constraints).

This keeps the comparison uniform (one decision procedure) while letting carrier structure do the work inside the compilation step.

## 3. Shared relational vocabulary (concrete, minimal)

All carriers answer the same symbols. No carrier receives a built-in "POVM element", "set membership test", or "eigenprojector".

Sorts (finite for any given packet):
- Observation — the rows of the surface X; named constants c0 … cN-1.
- Probe — shared finite set of probe names (e.g. p0, p1, … or the packet's probe symbols).
- Update — shared finite set of continuation actions or generator words (the "step" symbols engines actually simulated).
- Outcome — the common finite response alphabet (e.g. {0,1} or the packet's outcome tokens).

Core relations (the only ones that directly determine blocks):
- responds(Observation, Probe, Outcome) — holds when the candidate, presented with that observation row and that probe, produces that outcome.
- next(Observation, Update, Observation) — holds when applying the named update to the observation yields the target observation (may be nondeterministic for some carriers; a carrier that is deterministic simply produces functional facts).

Optional auxiliary machinery (private to the carrier, does not appear in the common surface):
- Carrier-specific sorts (HilbertVector, DensityElement, OctonionUnit, RelationTuple, …).
- Carrier-specific axioms or ground facts (positivity constraints, multiplication table, associator nonzero, admissible-set closure, …).

Only the projections onto responds and next affect the partition. Private structure is used only to justify which common facts are admissible.

The surface X can be extended with virtual observations representing "x after u" for each tracked finite continuation depth. This makes continuation distinctions first-class members of the surface rather than an afterthought.

## 4. How a candidate's behaviour compiles to relations

Compilation is carrier-specific and happens inside the engine run or a post-processing step. The output is a set of ground atoms for responds and next (plus any private axioms the SMT layer will conjoin).

### Classical relational carrier (example: unrestricted relation or probe-response incidence)
- For each observed row (history, probe, outcome) in the packet, assert the corresponding responds(c_i, p, o).
- For each admissible local rewrite or step the carrier supports, assert the next facts that its admissible-set lookup produces.
- No extra private axioms beyond "the set of asserted tuples is exactly the admissible set".
- If the carrier was the "pairwise_graph" variant, the compilation step would have over-admitted on the original packets; that over-admission appears as extra responds facts that a stricter joint-relation carrier would not emit.

### Spinor / QIT density-matrix carrier
- The engine (Julia/JAX) assigns or evolves a finite presentation (vector in minimal ideal, or density matrix on a small register) for each base observation.
- For each declared probe p, the carrier executes its chosen finite measurement map (Kraus, POVM element, or equivalent) and records the concrete outcome token in the shared alphabet. Assert responds(c_i, p, o).
- For each declared update u (channel, unitary word, jump operator application), the engine produces the image state and therefore the image observation constant; assert next(c_i, u, c_j).
- Private axioms the SMT layer may add (when doing consistency checks rather than pure trace replay):
  - The assigned matrices are positive semidefinite with trace 1 (or the finite analogue the engine actually used).
  - The measurement maps are completely positive / trace-preserving where claimed.
- The key point: the carrier does not get to name its POVM elements in the common vocabulary. It only gets to say, for the shared probe names, which outcome token it returned on each observation.

### Octonion / nonassociative carrier
- The engine assigns octonion (or sedenion-reduction) elements or matrices-over-octonions to base observations.
- Probes are interpreted as multiplication by named generators or evaluation of the associator on chosen triples. The resulting scalar or sign is mapped to one of the shared outcome tokens; assert responds.
- Updates are octonion multiplication by units or application of a chosen derivation / automorphism word. Assert next facts from the resulting elements.
- Private axioms include the multiplication table and the requirement that the associator α(x,y,z) is nonzero on at least one tested triple (if the candidate claims nonassociativity is load-bearing).
- Distinctions can appear on continuation paths precisely where grouping order affects the subsequent response: (x·u)·v versus x·(u·v) can land in different response classes even if the static probe on x did not separate them.

In all three cases the emitted responds and next facts are over the identical finite sets of constants and symbols. That is the common surface.

## 5. How z3 + cvc5 induce the partition

Two practical routes (both admissible; the design does not choose yet).

Route A — signature extraction with consistency filter (often sufficient for finite traces):
1. For each observation c (including virtual continuation observations), collect the full response vector: the tuple of outcomes for every (probe, continuation-depth, path-summary) that was actually executed.
2. For carriers with constraints, feed the collected facts plus the carrier's private axioms to the solver and ask whether any alternative assignment of outcomes to the undecided positions is still consistent. If the solver returns UNSAT for every attempt to flip a bit that would separate two observations, those observations are forced identical.
3. Group observations that have identical committed vectors (after consistency filtering). The resulting blocks are π_C.

Route B — explicit distinguishability queries (more directly "SMT decides"):
For every pair (or, at scale, via incremental congruence or union-find with SMT explanations):
- Assert the carrier's theory M_C (ground responds/next facts + private axioms).
- Assert the diagram of the surface.
- Assert the negation of "x and y agree on all responds and all next-images up to depth K".
- If SAT, a separating witness exists → different blocks.
- If UNSAT, they are indistinguishable under this carrier on the tested surface → same block.

Both routes produce a partition of the (possibly extended) observation surface. The partition is emitted in the same shape the ratchet kernel already consumes (block labels per row, or a map from row_id to block_id).

Because the decision procedure is the same for every carrier, the only source of difference between π_classical and π_qit is what each carrier's M_C forced or allowed on the shared symbols.

## 6. How continuation, persistence, and evolvability enter as relational constraints

Continuations are not an optional extra. They are part of the surface.

- The engine runs (or the trace records) finite unrollings: for each base observation and each admissible update word of length ≤ K, produce the image observation and its probe responses.
- These images become additional Observation constants (or are referenced via next facts).
- The partition algorithm of §5 is run on the whole set. Two base observations end in the same block only if their entire forward trees produce identical response sequences under the candidate's next relation.

Persistence demands become ordinary demand edges on this extended surface:
- A pair (x, y) is in D_persist if the packet requires that x and y remain separated after every admissible continuation sequence of length ≤ K.
- In relational terms: for every path u, the images x·u and y·u must not be placed in the same block (or, stronger, must differ on some probe response after u).
- The ratchet kernel already knows how to count collapsed edges; it does not need to know they came from continuations.

Evolvability demands are dual:
- A pair is in D_evolv if there exists at least one admissible path under which the candidate keeps (or creates) a separation that a static probe would have lost.
- In the SMT view: the solver is asked whether there exists a choice of updates such that the response vectors of the images differ. SAT for the "exists separating path" query contributes a demand edge that only carriers able to make the choice survive.

The base_campaign failure (restricting_outer_changes_inner false for all) is directly addressable by adding these continuation-derived demand pairs and re-running the same carriers on the extended surface. The SMT bridge gives a uniform way to compute the partitions once the traces include the next facts.

## 7. Answer to the neutrality-vs-discrimination tension

Neutrality is enforced at the vocabulary level. Every carrier receives the same finite set of probe names and the same finite outcome alphabet. There is no "quantum probe language" versus "classical membership test" at the comparison layer. The responds and next relations are the only observables that count for block membership.

Discrimination is not forbidden; it is required to come from structure. A carrier earns a finer partition only when its internal rules (positivity + complete positivity for density, nonzero associator + multiplication table for octonion, admissible-set closure for relation) make some response tables impossible and others forced. If two observations can be given different outcome sequences consistently with the carrier's rules, the SMT query returns SAT and they are separated. If every attempt to separate them violates the carrier's rules, they are identified.

This is the intended resolution:
- Richness lives inside the carrier's compilation step and its private axioms.
- Neutrality lives in the shared surface and the uniform decision procedure.
- A carrier that needs a special probe family to show its power must first compile that family down to answers in the common alphabet, or it earns no credit on the ratchet.

If the current shared Probes and Updates are too coarse to let genuine structural differences appear as response differences, the honest diagnosis is "the observation surface was still too thin", not "the SMT bridge collapsed the carriers". The bridge design makes that diagnosis checkable: add more shared update words or a modestly larger outcome alphabet, recompile the same carriers, and see whether the partitions diverge.

## 8. Honest limitations — where it can still privilege a carrier or go thin

1. Projection risk (thinness). If the shared outcome alphabet is binary and the only updates are single named generators, any carrier whose natural distinctions live in relative phase, in higher-arity grouping, or in non-projective measurements may be forced to emit identical 0/1 tables on every tested row. All carriers then produce the same coarse partition regardless of internal structure.

2. Private-symbol smuggling (privilege). A carrier is allowed private sorts and axioms. If the compilation step is permitted to introduce a large number of hidden variables or internal contexts and then map them arbitrarily onto the shared probes, a rich carrier can effectively buy discrimination by having more degrees of freedom to assign. The design must bound this (for example by requiring that every private symbol used to justify a responds fact must be witnessed by an actual engine execution trace, not invented at compilation time).

3. Ease of emitting ground facts. A pure relational carrier can emit its responds facts by direct lookup from its admissible set. A density-matrix or octonion carrier must run (or justify) a measurement or multiplication step and only then emit the fact. This is an asymmetry in engineering cost and in the number of opportunities for transcription error. It is arguably faithful to the carriers' different structures, but it is still an asymmetry the bridge does not remove.

4. Choice of shared Updates. Naming the continuation actions is itself a modelling decision. If the chosen update vocabulary aligns more naturally with one carrier's generators than another's, that carrier can exhibit more varied next facts without extra work. The vocabulary must be chosen from the packets and from what the engines can actually simulate across carriers, not from one carrier's preferred basis.

5. Quantifier depth and scale. Full "for all paths of length K" persistence can be expressed with quantifiers or by explicit unrolling. Explicit unrolling explodes the constant count. SMT is excellent at the quantifier-free fragments that result from grounding, but the design still requires a budgeted depth and a summarisation strategy (history summaries, rolling hashes, etc.) already present in the combinatorial ratchet. At large scale the bridge may fall back to direct signature comparison with only spot-check SMT consistency queries.

6. Nondeterminism representation. If one carrier is naturally nondeterministic (multiple admissible next images) and another is deterministic, the relational encoding must not silently turn the nondeterministic carrier's extra images into automatic extra distinctions. The partition groups observations, not their possible futures; futures are additional observations that may or may not be identified with others.

None of these limitations are hidden. They are the places where the concrete vocabulary, the depth budget, the private-axiom discipline, and the update naming still require packet-by-packet engineering judgment.

## 9. Integration with the ratchet kernel and Lev execution

The bridge produces, for each carrier, a partition of the (extended) observation surface in the same format the combinatorial ratchet already accepts:
- A mapping from row identifiers to block labels (normalised, stable under relabelling).
- Optionally the raw response signature table for audit.

The ratchet then:
- Computes L_D for each active demand family on that π.
- Identifies survivors (L_D = 0 on all families).
- Computes the refinement frontier among survivors.
- Records coface gradients exactly as before.

Because the input to this stage is now π_C derived from real engine traces rather than from a combinatorial generator, the same kernel code applies without modification.

On the Lev side the stages remain:
- lev exec engine job (Julia canon / JAX sweep / PyTorch learned) with a declared finite probe+update budget → produces traces.
- lev exec bridge step (the SMT-relational compiler + partition inducer) → produces π files.
- lev exec ratchet_kernel with the π files and the current D → produces frontier and receipts.
- ClaimGate and trace recording close the loop.

The bridge step itself can be guarded by an exit-code verifier that checks: every carrier emitted responds/next facts over the identical constant and symbol sets; the induced partitions are well-formed; continuation depth used is recorded.

## 10. Miniature concrete illustration (text only)

Surface (4 base observations + 1 update u):
- c0, c1, c2, c3
- One probe p
- Outcome alphabet {0,1}
- One continuation u

Traces (hypothetical):

Classical relational carrier (joint admissible set):
- responds(c0,p)=0, responds(c1,p)=0, responds(c2,p)=1, responds(c3,p)=1
- next(c0,u)=c2, next(c1,u)=c3, next(c2,u)=c0, next(c3,u)=c1
- After u the images swap the two pairs. If D contains a persistence edge (c0,c1), the classical carrier keeps them separated after u only if the images remain in different blocks. Here c2 and c3 are already in different static blocks, so the edge survives.

QIT carrier on the same surface:
- The engine assigned states such that the measurement for p returns 0 on both c0 and c1 (they look identical under p), but after channel u the images separate: responds(image(c0),p)=0, responds(image(c1),p)=1.
- Static probe alone would have merged c0 and c1. The continuation unrolling gives them different response vectors on the extended surface. The induced partition can now separate them where the static classical partition on the same probe would not.

Octonion carrier:
- Multiplication by the update generator flips a sign that the probe p reads as a different outcome only on certain grouping orders.
- If the associator is load-bearing, there exist triples where (x·u)·v and x·(u·v) produce different outcome tokens even though every static probe on x agreed. The next facts plus the responds facts on the images create a separating path that an associative matrix carrier on the same vocabulary cannot replicate without violating its own axioms.

All three carriers emitted facts using exactly the same four Observation constants, the same probe p, the same update u, and the same outcome tokens. The partitions differ only because the consistency constraints inside each M_C made different response tables admissible.

## 11. Open engineering questions (fuel, not resolved here)

- What is the minimal sufficient shared Update vocabulary and continuation depth for a given packet before additional depth stops splitting partitions?
- How to name Probes and Updates so they are "the same question" across carriers without smuggling a preferred measurement basis?
- Discipline on private symbols: every private symbol used to derive a responds fact must be backed by an actual engine execution record (state, channel, multiplication), not a free parameter introduced at bridge time.
- Caching and budget: full SMT on thousands of observations with depth-3 trees will be expensive; signature extraction plus targeted consistency queries is the likely practical path.
- How demand families that explicitly reference continuation paths (D_persist, D_evolv) are authored and versioned alongside the observation packets.
- Whether the bridge should also emit, for each block, a witness formula or ground fact that the SMT layer used to justify the identification — useful for audit even if not required for the ratchet kernel.

## 12. Relation to existing surfaces and receipts

- Reuses the row format already present in kernel_tick receipts and base_campaign packets (history, probe, outcome tuples become Observation constants).
- Compatible with the continuation traces JAX (diffrax), Julia (exact or MCWF), and PyTorch (rollouts) already produce.
- The dual-solver (z3 + cvc5) pattern is already exercised in system_v8/engine_native/jax_scale_lanes.py for kill-set proofs; the same import-and-assert discipline applies.
- The output partition shape is the same shape the combinatorial _candidate_assignment and _normalise_partition already produce, so the ratchet_engine.py frontier code can consume it unchanged.

## 13. Summary (conditional)

The SMT-relational bridge supplies one concrete answer to the shared-surface requirement:
- A deliberately minimal common vocabulary of responds and next over shared finite alphabets.
- Carrier-specific compilation of engine traces into ground facts plus private consistency axioms.
- Uniform z3/cvc5 decision of distinguishability on the common symbols.
- Explicit extension of the observation surface by finite continuation unrollings so that persistence and evolvability demands become ordinary edges on that surface.
- Direct feed into the existing partition-coarseness ratchet.

It does not remove the need for sufficiently rich packets and sufficiently thick D. It does give a uniform mechanical procedure that makes the claim "these two carriers are distinguishable on this surface" checkable by the same code for every rival, without installing a carrier's favourite probe language as the comparison language.

This is fuel. It is offered for engineering review, for implementation experiments, and for comparison against rival bridge designs. It carries no admission, no promotion, and no assertion that the resulting partitions will separate the carriers that the base_campaign run collapsed.

All further steps (concrete compiler implementations for the three carrier families, budgeted continuation depth studies, fresh packet construction with explicit D_persist families, Lev-wired execution of the full trace→bridge→ratchet sequence) remain to be done and to be receipted at the appropriate status ladder level.