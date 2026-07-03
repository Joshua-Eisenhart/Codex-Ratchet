# Ratchet Definition and Emergence Spec — DRAFT

ASSISTANT-GLOSS: status: DRAFT-FOR-OWNER-TUNING. claim_ceiling: **doctrine draft, no admission**. This is exact-wording candidate material plus a sim spec, vetted by a 14-model fleet (13 returned, 1 hard-failed) with codex2 at four reasoning efforts held as the arbiter lane. It is NOT canon, NOT a proof surface, and admits no object — not the ratchet, not the manifold, not the bridge. Ceiling: `scratch_diagnostic`, `promotion_allowed: false`, `formal_admission_allowed: false`.

ASSISTANT-GLOSS: Scope. This doc names (1) a canonical ratchet definition, (2) the emergence derivation `F01 + exclusion-first + N01 => ratchet` with its honest gaps, (3) the lexical<->geometric bridge stated at the WEAKEST defensible strength, (4) the two entropies, (5) the earning-sim spec `finite_ordered_survivor_ratchet_emergence_v0`, and (6) the honest ceiling. Source axioms are cited to `system_v6/foundations/root_axioms_v0_1_DRAFT.md` (hereafter `root_axioms`). The ratchet object is downstream of the root primitive; it does not replace it.

ASSISTANT-GLOSS: Anti-collapse notice. Three forks are LIVE and held open inside this doc, by design, because the evidence has not excluded any: (A) bridge status iso/homomorphism/analogy; (B) the attractor object — one object with cycles-only-in-readouts vs. three distinct regimes (strict / revivable / branching); (C) the severity of the derivation — "essentially sound, only omits memory" vs. "not sound as stated, N01 overclaims." Do not collapse these. The earning sim's job is to decide (A); the others stay open pending owner tuning.

---

## 0. Provenance — root axioms this object stands on

The ratchet object is NOT a new root. It is a downstream construction over the existing root primitive. The three root expressions it consumes (all from `root_axioms`):

- **F01 / finitude.** Finite carriers, finite probe families, finite admissibility predicates, finite composition/bracketing witnesses, no completed infinities as root furniture. Source: `root_axioms:53`.
- **Exclusion-first.** Constraints do not create ontology. They kill inadmissible distinctions/compositions/carriers/readouts. What remains is provisional survivor structure under named constraints. Source: `root_axioms:41`; `root_axioms:39` ("Constraints eliminate what cannot persist; they do not deterministically generate what must exist"); `root_axioms:37` ("There is no 'driving.' There is only: which constraints are active, and which structures survive").
- **N01 / noncommutation.** "One root relation appears at three levels: elements as quotient identity (`S/~_M`), **order as noncommutation (sequence matters; swapping is not free)**, and grouping as nonassociativity." Source: `root_axioms:51`; and the geometry-stack doctrine quote `root_axioms:49`: "Stacked geometries are a candidate ratcheting constraint layer when the stack is non-commutative (`A o B != B o A` on some probe state). If you can freely swap order, it is not a ratchet — just independent filters."
- **Root primitive (above all three).** The constraint on distinguishability, formalized locally as probe-relative indistinguishability `~_M` under an active finite probe family; `a = a iff a ~ b` reads as the attack on primitive identity. Source: `root_axioms:17`, `root_axioms:31`.
- **M(C) tuple.** `M(C) = (S, C, P, ~_P, Adm_C, composition/bracketing, local readouts, controls, receipts)`. Source: `root_axioms:65`.

ASSISTANT-GLOSS: The phrase `root_axioms:49` already calls a non-commutative geometry stack a *candidate ratcheting* layer. The ratchet object below is the formalization of that owner doctrine, vetted by the fleet — it is owner-rooted, not model-invented.

---

## 1. THE CANONICAL RATCHET DEFINITION

### 1.1 What the fleet corrected before this was writable

The originally-proposed 6-property definition was (1) F01/finitude, (2) exclusion-first, (3) noncommutation, (4) irreversibility, (5) memory, (6) termination + cycle-class. The fleet — 13 working models plus codex2 at all four efforts, with codex2 NOT dissenting from the consensus — converged on the same edits:

- **(4) irreversibility is NOT a primitive.** It is a *consequence* of exclusion-first + memory + a no-resurrection operator. Demote it; promote in its place an explicit **no-implicit-re-introduction** primitive. (grok-4.3, grok-build, gemini, qwen, glm, minimax, deepseek, kimi-k2.6, codex2-all.)
- **(6) termination is a THEOREM, not an axiom.** Finitude + monotone descent ⇒ stabilizes in ≤ |X_0| strict deletions. Near-unanimous. Do not axiomatize it.
- **(6) "cycle class" must be CUT from the survivor layer.** A strictly contracting sequence of subsets of a finite set CANNOT cycle — only fixed point or empty. Cycles may live ONLY in auxiliary readouts `H/G/E` under a declared finite quotient. (qwen, glm, kimi-k2.6, codex2-all, minimax, grok-build.)
- **(3) noncommutation is too verbal.** Sharpen to an existential witness on the full-state update operator. (all.)
- **(2) exclusion-first = strict contraction.** Rename for precision; separate the inclusion fact from the history-dependent mechanism. (glm, grok-build.)
- **MISSING PRIMITIVE — state/history-dependence.** The tests must read the history. Without it the tests are static set-predicates that commute, and the whole object collapses to a commuting filter stack. This is the engine of the ratchet. (gemini, qwen, glm, deepseek, kimi-k2.6, minimax, codex2-all.)
- **Trivalent status.** ACCEPT/PARK/REJECT cannot be encoded by a binary `X_{k+1} ⊆ X_k`; it needs a status map. (minimax, kimi both, codex2_high/xhigh.)
- **Typed tests** so a domain-mismatch cannot masquerade as noncommutation. (codex2_xhigh, uniquely.)
- **Probe family `M_k` and probe-relative quotient `~_k`** carried in the object — identity is through the quotient, not raw equality. (codex2_xhigh alone, repo-grounded; NO external model surfaced this.)

### 1.2 The corrected primitives (the canonical 6, fleet-applied)

A finite ordered survivor ratchet is a process satisfying these **six primitives** (renumbered; irreversibility and termination removed from the primitive layer and re-derived in §2):

1. **R1 — Finitude (F01).** The carrier `S` is finite; each probe family `M_k` is finite; each admissibility predicate `Adm` is decidable and terminates on finite input (test well-foundedness: finite `X_k` does not guarantee finite runtime unless each `C_k` halts). Source: `root_axioms:53`. (Test-well-foundedness flagged by minimax, glm, codex2_low.)
2. **R2 — Strict contraction / exclusion-first.** Each step deletes by construction: `X_{k+1} = { x ∈ X_k : x admissible under C_{k+1} }`, so `X_{k+1} ⊆ X_k`. Monotone descent (formally order-reversing / anti-monotone / a descending filtration — kimi-k2.6). Source: `root_axioms:41`, `root_axioms:39`.
3. **R3 — State/history-dependence (the engine; new explicit primitive).** Admissibility reads the history (and the induced geometry): `Adm(C, x, H, G)`, not `Adm(C, x)`. The test at step `k+1` depends on what step `k` recorded. Without R3 the tests commute and there is no ratchet. (gemini "noncommutation proves C_k reads from H_k"; qwen, glm, deepseek, kimi-k2.6, minimax, codex2-all.)
4. **R4 — Noncommuting full-state update (typed N01 witness).** ∃ typed `C_i, C_j` and an initial state `S_0` with `U_i ∘ U_j (S_0) ≠ U_j ∘ U_i (S_0)`, where the difference survives an observable quotient `~` (not inert ledger-order noise, not domain-mismatch). The family `{U_i}` generates a non-abelian submonoid of endofunctions on `(X, H, G)`. Source: `root_axioms:51`, `root_axioms:49`. (Typed: codex2_xhigh. Witness-on-maps: all. Observable-quotient guard: codex2_xhigh.)
5. **R5 — Append-only receipt memory + no implicit re-introduction (the demoted (4)+(5), merged).** History `H` is append-only; the graveyard of deleted items is recorded. There is NO unreceipted re-entry: a deleted `x` may return ONLY via an explicitly logged replay receipt, and that return is modeled as a FRESH token opening a new run/branch/identity — not the same `x`. ("Same-x return" without a receipt VIOLATES R2; flagged by codex2_low, minimax, kimi.)
6. **R6 — Trivalent status with a progress measure.** Each item carries status ACCEPT/PARK/REJECT (a status map, not a bare set membership). A progress measure `μ` forbids stalls: a step that filters nothing (non-strict `⊆`, idempotent stall) must either reduce `μ` via status change or be rejected as a non-step. (Trivalence: minimax, kimi, codex2_high/xhigh. `μ`: kimi-k2.6, minimax.)

ASSISTANT-GLOSS: Irreversibility (old #4) and termination (old #6) are NOT in this list. They are theorems derived in §2 from R1+R2+R5 (irreversibility) and R1+R2+R6 (termination). Promoting them to primitives is the conflation the fleet flagged.

### 1.3 The object `(X, H, C, π, E, G)` — corrected

The ratchet object is the finite tuple, evolved over discrete steps `k`:

| Component | Reading | Layer | Notes |
|---|---|---|---|
| `X_k` | finite survivor set ⊆ `S`, with status map `π_k : X_k -> {ACCEPT, PARK, REJECT}` | **core** | strictly contracts under R2; cannot cycle |
| `H_k` | append-only history / receipt ledger / graveyard | **core (engine)** | read by R3; grows monotonically; the source of N01 |
| `C_k` | the step's typed admissibility constraints `Adm(C, x, H, G)` | **core** | history-dependent (R3); typed (R4) |
| `π_k` | status map (trivalent) — **promoted into the tuple** | **core** | was implicit; needed for ACCEPT/PARK/REJECT |
| `M_k` | active finite probe family + probe-relative quotient `~_k` | **core (repo-native)** | identity-through-quotient (codex2_xhigh); external models omitted this |
| `E_k` | entropy readout (see §4) | **derived readout** | NOT a core ratchet axiom |
| `G_k` | induced geometry (carrier cells, adjacency) | **derived readout** | NOT a core ratchet axiom |

ASSISTANT-GLOSS: A lexical ratchet is valid with a trivial `G` and a trivial `E` — geometry and entropy are derived readouts, not ratchet axioms (codex2-all, grok-build, kimi-k2.6, minimax). The earlier formulations had a **signature bug** (minimax): the property form used `Adm(x, H)` [2-arg] while the object form used `Adm(C, x, H, G)` [4-arg] — these were not the same object. Fixed here by giving every register a (possibly trivial) `G`, so the lexical register carries a `G^lex` and the signatures match.

ASSISTANT-GLOSS: cycle-class — RESOLVED on the core layer (no cycles possible on a strictly contracting finite set), HELD-OPEN as fork (B) on the readout layer: minimax splits the whole object into THREE regimes — **strict** (no re-entry, no cycles), **revivable** (replay receipts admit a bounded revival regime where readout cycles can appear), **branching** (replay opens new branches). Do not collapse these three; collapsing loses falsifiability. Cycles, where they exist, live only in `H/G/E` under a declared finite quotient.

---

## 2. THE EMERGENCE DERIVATION — `F01 + exclusion-first + N01 => ratchet`

### 2.1 Headline status (honest)

The headline `F01 + exclusion-first + N01 => ratchet` is **NOT sound as stated**. The arbiter (codex2 all four efforts) and the fleet agree it earns only a **SKELETON**. The corrected chain, on which the fleet converges:

```
F01 + exclusion-first                       =>  finite monotone survivor DESCENT   (skeleton only)
  + typed/full-state N01 witness (R4)       =>  ORDER-SENSITIVE survivor process
  + append-only receipt memory + R5         =>  IRREVERSIBLE ratchet
  + finite observable quotient / bounded (H,G,E) =>  TERMINATING ratchet (whole object)
```

ASSISTANT-GLOSS: severity fork (C) HELD OPEN — deepseek is mildest ("essentially sound, only omits memory as explicit"); minimax / kimi / codex2 are harshest ("not sound as stated; N01 alone overclaims; the headline is near-tautological as a re-description"). Do not collapse to one severity. Both readings survive the evidence.

### 2.2 The three holes (stated honestly — do NOT paper over)

**HOLE 1 — does exclusion-first alone give monotonicity?** YES, unanimous, uncontested. `X_{k+1} = {x ∈ X_k : ...}` ⇒ `X_{k+1} ⊆ X_k` by construction. This is definitional. Refinement (kimi-k2.6): it is formally order-reversing / anti-monotone / a descending filtration; "monotone descent" is intuition-language for a ⊥-preserving contraction.

**HOLE 2 — does the chain provably TERMINATE vs. cycle?**
- The **survivor set** provably terminates and CANNOT cycle: finite + `⊆` ⇒ stabilizes in ≤ |X_0| steps; well-founded. Unanimous.
- BUT the **full object `(X, H, G, E)` does NOT terminate** as stated. `H` is append-only and grows forever; `G/E` can keep changing. "Survivor stabilization" ≠ "process halting" unless `H/G/E` are finite, quotiented, or the test stream is finite. (gemini "memory-leak"; kimi-k2.6, minimax, deepseek, codex2_medium/high/xhigh.) **This hole is NOT papered over: termination of the survivor set does not imply termination of the whole object.**
- Secondary: if `⊆` is non-strict you can STALL — a test that excludes nothing. Needs the strict-progress measure `μ` (R6) or an effective-test requirement. (grok-4.3, kimi-k2.6, minimax.)

**HOLE 3 — does noncommutation of the update MAPS imply noncommuting CONSTRAINTS/tests?** NO. This is the central flaw, unanimous.
- Static/extensional predicates ("is even", "is >5") COMMUTE, because set-intersection is commutative: `A ∩ B = B ∩ A`. Map-noncommutation arises ONLY from state/history-dependence: applying `C_i` mutates `H`, which changes how `C_j` evaluates.
- So the correct, WEAKER statement: **N01 requires noncommutativity of the HISTORY-DEPENDENT update** (the family `{U_i}` generates a non-abelian submonoid of endofunctions on `(X, H)`), NOT noncommutativity of the bare constraints. **This hole is NOT papered over: map-noncommutation ≠ constraint-noncommutation.**
- minimax enumerates three sources of map-noncommutation: (i) bare-function noncommute, (ii) history-append order, (iii) `Adm`-wrapper via `G`; source (ii) dominates real systems. gemini's cleanest framing: "noncommutation PROVES that `C_k` reads from `H_k`" — i.e. an observed N01 witness is *evidence for R3*. codex2_xhigh adds: map-noncommutation can be a spurious artifact of domain-mismatch or geometry-recompute, so the witness must compare the SAME typed constraints on the SAME initial state and show the difference survives an observable quotient.

ASSISTANT-GLOSS: near-tautology warning (kimi, minimax). The headline is close to circular as a re-description — to truly *earn* EMERGENCE you must derive the ratchet from lower-level LOCAL rules (e.g. QCA neighborhood rules + topology), not just rename the defining properties. This is exactly the gap the earning sim (§5) is built to close, and the reason §5 proposes renaming the sim away from "emergence" until the lower-level derivation exists.

---

## 3. THE LEXICAL <-> GEOMETRIC BRIDGE — weakest defensible claim

### 3.1 Verdict: HOMOMORPHISM CANDIDATE, NOT isomorphism; currently no-stronger-than analogy until Φ is built

**ZERO models claim isomorphism.** The entire fleet lands between homomorphism and analogy. Stated at the weakest defensible strength the fleet supports:

> Φ is a STRUCTURE-PRESERVING MAP candidate between two realizations of one abstract ratchet signature. It is asserted as a specification, NOT yet proven as a map. Until the earning sim CONSTRUCTS Φ and verifies the commuting square `Φ ∘ Update_lex = Update_geo ∘ Φ`, the bridge is **homomorphism-if-earned / analogy-until-then**.

**Why not isomorphism (unanimous):** lexical → geometric is many-to-one / forgetful. Aliasing in both directions: distinct lexical claims map to the same geometric cut; geometric cells exist with no clean lexical name. Lost information forbids a bijection. (gemini, glm, qwen, minimax, codex2_high/xhigh — all give this exact aliasing argument.)

**Two wings — HELD OPEN as fork (A):**
- **HOMOMORPHISM-if-earned** (modal; grok-4.3, grok-build, gemini, qwen, glm, codex2-all, kimi-k2.6, minimax): Φ preserves survivor partial-order, status (ACCEPT/PARK/REJECT), order-witness, history-append, projection. It does NOT preserve geometric metric/topology or lexical syntax/semantics.
- **NOT-YET-EVEN-HOMOMORPHISM / currently ANALOGY** (skeptical wing; deepseek, minimax, grok-build, codex2_low): as written Φ is a dictionary/specification, not a proven map; no Φ is exhibited and the commuting square is unproven. minimax: it is "more than analogy only IF (i) well-defined on states, (ii) commutes with both updates, (iii) inj/surj as claimed — none shown." grok-build: "the QCA side feels like an implementation choice rather than a natural dual."

ASSISTANT-GLOSS: fork (A) is LIVE and load-bearing, not decorative. It turns entirely on whether the earning sim CONSTRUCTS Φ and checks the commuting square. Do not collapse it. Deciding it is the sim's job (§5).

### 3.2 The correspondence map Φ (the candidate, with shared structure)

The shared abstract object both registers forget down to (notably convergent vocabulary, independently arrived at by separate models):

- **Bounded meet-semilattice with path-dependent valuation** (gemini + qwen): the rigorous homomorphism condition is `Φ(A ∧ B) = Φ(A) ∩ Φ(B)` — logical conjunction (lexical) ↔ geometric intersection. gemini specifically frames it as a **Galois connection / adjunction**.
- **Category / functor framing** (glm, kimi-k2.6, minimax): a partial-order monoid (objects = survivor sets, morphisms = admissibility maps, composition = sequential application); Φ is a **functor / natural transformation / realization-morphism** between two objects in the category of realizations, both forgetting (via a forgetful functor `U`) to the SAME abstract ratchet. kimi-k2.6: it is a "filtration with retraction"; it becomes ISO only when EARNED by proving identical automorphism groups on the fixed survivor set `X_∞` (geometric kernel = lexical kernel).
- **Typed simulation relation** (codex2_xhigh, repo-native): until earned, Φ is a typed simulation relation; the shared signature explicitly includes the probe-relative quotient `~` and a commutation matrix.

The candidate component map Φ:

| Lexical register | --Φ--> | Geometric register | Preserved? |
|---|---|---|---|
| admissible-claim token `x` | --> | carrier cell / region | many-to-one (alias) |
| logical conjunction `A ∧ B` | --> | geometric intersection `∩` | YES (the homomorphism condition) |
| survivor set `X_k` | --> | live cell set | partial-order: YES |
| status `π_k(x)` | --> | cell ACCEPT/PARK/REJECT | YES |
| history append `H_k -> H_{k+1}` | --> | ledger append | YES |
| sequential application `U_i ∘ U_j` | --> | geometric update composition | order-witness: YES |
| lexical syntax / semantics | --> | (no image) | NO (forgotten) |
| (no preimage) | <-- | geometric metric / topology | NO (not in lexical) |

ASSISTANT-GLOSS: the map is `forgetful both ways` — that two-way forgetting is exactly why iso is excluded and why fork (A) survives until Φ + the commuting square are built and tested.

---

## 4. THE TWO ENTROPIES

`E_k` is a **derived readout**, not a core ratchet axiom (§1.3). There are two distinct entropies, one per register; they are NOT automatically equal, and that inequality is itself a falsifiable prediction.

- **Lexical entropy (lexical ambiguity).** A measure of ambiguity / branch-multiplicity over the surviving lexical claims — e.g. Shannon entropy of the survivor status distribution, or branch entropy of the constraint DAG (how many admissible continuations remain at each support cell). Falls as the ratchet excludes ambiguity; can SPIKE when a single survivor splits into many admissible sub-readings.
- **Geometric entropy (geometric quotient).** A measure over the geometric quotient — e.g. Shannon of the survivor cells, or a quotient-cut entropy `S(ρ_A)` over a bipartition of the induced carrier `G_k`, the narrow cut quantity the root docs reserve for any Axis-0-adjacent reading. Source for the cut-entropy framing: `root_axioms:99` ("the narrow map from geometry/history into a bipartite density object whose cut quantities can support Axis 0").

ASSISTANT-GLOSS: entropy is NOT automatically cardinality (kimi-k2.6). Conditional / branch entropy can RISE while `|X_k|` falls. The two registers will generally trace DIFFERENT `E_k` trajectories (minimax, kimi-k2.6) — a prediction the earning sim must measure, not assume away. Per `root_axioms:103`, entropy is admissible only as a derived measure over quotient / cut / refinement / branch-history structures; it is never the master organizing variable, consistent with `root_axioms:97` ("The system does not want entropy as a master variable").

---

## 5. THE EARNING SIM SPEC — `finite_ordered_survivor_ratchet_emergence_v0`

### 5.1 Naming and ceiling

ASSISTANT-GLOSS: codex2_xhigh recommends RENAMING away from "emergence" to `finite_ordered_survivor_ratchet_definition_witness_v0` — it witnesses the *definition*; it does NOT yet prove emergence from lower-level rules (the near-tautology gap, §2.2). Both names are recorded; the owner picks. Claim ceiling for whichever name is used: *"finite ordered survivor ratchet skeleton realized lexically AND geometrically with a TESTED homomorphic bridge"* — NOT "the ratchet/manifold is proven." Ceiling: `scratch_diagnostic`, `promotion_allowed: false`.

### 5.2 Objects the sim must build

- A lexical register: a small WORKING ratchet with a receipt-by-receipt trace (minimax, sharply — the sim must show a concrete working ratchet, not just "things that look like ratchets"). Candidate: a tiny type-checker, or a 3x3 QCA with conflicting parity/domino rules, shown to be order-sensitive.
- A geometric register: the **ring-checkerboard QCA** as the geometric realization (the owner's pre-AI geometric substrate; ties this sim into the existing geometry program). The brickwork/checkerboard local rules supply the lower-level neighborhood dynamics whose induced survivor process is checked against the abstract ratchet signature.
- The shared abstract schema both project to (§3.2): survivor partial-order + status + order-witness + history-append + probe-quotient `~`.
- The map Φ, CONSTRUCTED explicitly (not asserted), plus the commuting-square test `Φ ∘ Update_lex = Update_geo ∘ Φ`.
- Explicitly DEFINED black boxes (minimax, kimi-k2.6): `InduceGeometry` (quotient / reachable-states recompute) and `EntropyReadout` (Shannon of survivors / branch entropy of the constraint DAG / quotient-cut entropy). Note the two registers will give DIFFERENT `E_k` trajectories — a recorded, falsifiable prediction.

### 5.3 Positive tests

- Build a concrete order-sensitive ratchet and exhibit `U_i ∘ U_j (S_0) ≠ U_j ∘ U_i (S_0)` from IDENTICAL `S_0`, over the FULL order-witness matrix across ALL pairs (not one cherry-picked pair) — no precomputed booleans, no hand-ranked verdicts, no handpicked sequences (codex2_high adversarial-tautology check, repo-native).
- A QUANTITATIVE noncommutation score, not binary: `δ(C_i, C_j) = | Surv(...C_i C_j...) △ Surv(...C_j C_i...) |` (symmetric difference of survivor sets) — a commutator witness (minimax, kimi).
- Survivor stabilization in ≤ |X_0| steps (HOLE-2 survivor-layer check).
- The commuting square holds step-by-step on matched inputs across both registers (the bridge positive test — decides fork A).

### 5.4 The control-falsifiers

The four originally-proposed controls are KEPT and judged good by the fleet:

| Control | Mechanism | Pass means |
|---|---|---|
| **commuting -> filter-stack** | make all `C_k` history-INDEPENDENT (`C_k(x,H) ≡ C_k(x)`) | all permutations give identical `(X_n, H_n)` ⇒ NOT a ratchet, just commuting filters |
| **non-finite -> no-termination** | drop F01 (unbounded carrier / test stream) | survivor set fails to stabilize ⇒ termination needed F01 |
| **no-memory -> re-entry** | drop R5 (no receipt ledger) | deleted items re-enter ⇒ irreversibility needed memory |
| **generation-first -> not-a-ratchet** | replace exclusion with generation (add items) | descent fails ⇒ exclusion-first is load-bearing |

Fleet ADDITIONS (the stronger battery — these distinguish the claims, not just decorate):

- **AMNESIC / memory-ablation** (near-unanimous; strongest single addition — qwen, glm, deepseek, codex2-all): set `C_k(x,H) ≡ C_k(x)`; ALL permutations give identical `(X_n, H_n)` ⇒ proves memory is the engine of N01 (directly tests R3 / HOLE 3).
- **History-only noncommutation** (codex2-all, minimax): same final `X` but different `H` — DECIDE and LABEL whether that counts (weak vs. strong order-sensitivity).
- **Inert-ledger-order reject** (codex2_high/xhigh): an order difference that does NOT affect future admissibility must be REJECTED as not-ratchet-bearing (guards against decorative noncommutation).
- **Domain-mismatch reject** (codex2_xhigh): noncommutation from a typing mismatch is not real noncommutation — reject it.
- **Stagnation / idempotent-stall** (kimi-k2.6, minimax): a test filtering nothing on non-strict `⊆` ⇒ requires `μ` / effective-test; otherwise a non-trivial non-empty terminal attractor must be declared.
- **Empty/blocked-set robustness** (gemini "total annihilation", qwen, kimi-k2.6, codex2-all): drive `X_k -> ∅`; geometry-update must not divide-by-zero / null-pointer on an empty manifold; restart WITHOUT a replay receipt must LOCK (no spontaneous regeneration).
- **Explicit-replay +control** (minimax regime taxonomy, codex2-all): a rejected item returns ONLY via a logged replay receipt that opens a NEW run/branch/identity ⇒ enters the revivable regime (fork B).
- **Geometry-is-not-automatically-a-ratchet** (kimi-k2.6, sharp): let `InduceGeometry` GROW cells (buffer zones) as `X` shrinks; verify `G_{k+1} ⊄ G_k` ⇒ Φ must map to a geometric survivor SUBSTRUCTURE, not the whole geometry. Plus a geometry-relabel/shuffle control: same ledger + randomized adjacency must BREAK geometric claims (codex2-all).
- **Φ-fidelity / cross-register controls** (the bridge test — minimax +Φ, kimi-k2.6 "Φ-inverse fidelity", codex2-all, deepseek): run both registers on matched inputs, project both to the abstract schema, check the commuting square; PLUS adversarial Φ controls — many-to-one lexical aliases, one-to-many geometric splits, unmapped killed cells, and a `Φ^{-1}` kernel-size measure. **Without the positive instance AND the cross-register check you earn AT MOST an analogy** (minimax).
- **Scale sweep** `|X_0| = 4, 16, 64, 256` (minimax): termination time, noncommutation-score stability, geometry-induction doesn't blow up. **Grid sweep** over the 4 axes finite / strict / memory / commuting (kimi-k2.6).

### 5.5 Tie to the ring-checkerboard QCA geometric realization

ASSISTANT-GLOSS: the geometric register IS the ring-checkerboard QCA — the owner's pre-AI geometric substrate, already present in the v6 geometry program. Its brickwork/checkerboard local neighborhood rules are the lower-level rules whose induced survivor descent the sim checks against the abstract ratchet signature. This is what would let the sim address the near-tautology gap (§2.2): if the survivor ratchet provably FALLS OUT of the local QCA rules + ring topology (not just gets renamed), that is the difference between *witnessing the definition* and *earning emergence*. Until that derivation is exhibited, the sim earns the definition-witness, not emergence.

---

## 6. HONEST CEILING

- **Doctrine: strong.** The definition is multi-model-vetted (13 working models + codex2 at 4 efforts, codex2 inside the consensus not dissenting). The corrections are convergent, not one outlier's opinion.
- **Lexical ratchet: RUNS.** The b_kernel allow-list / derived-only accept-reject is a working lexical survivor process today (`exists`, `runs`). It is the lexical register's existence proof.
- **Geometric pieces: EXIST.** The ring-checkerboard QCA and the v6 geometry program provide the geometric register's raw material (`exists`). `gcm_ratchet_order_matrix_v1` measured the order-witness matrix (SELF=7 / COMMUTE=2 / DIRECTIONAL=12 / NOT_COMPARABLE=28, six forced edges) but is **scratch-diagnostic only** — its `audit_verdict.md:12` reads GENUINE-WITH-CAVEATS, scratch, with a source-hash drift and two weak controls (`audit_verdict.md:21-24`). It does NOT admit the ratchet object.
- **Unified emergence: NOT YET EARNED.** The headline derivation earns a skeleton, with HOLE 2 (whole-object termination) and HOLE 3 (map-vs-constraint noncommutation) open and unpapered. The bridge is homomorphism-if-earned / analogy-until-Φ-is-built. No Φ has been constructed; no commuting square has been verified.
- **This document is the SPEC to earn it,** not the earning. Status ladder for the unified object: `exists` (this spec) < `runs` < `passes local rerun` < `canonical by process`. Nothing here is above `exists` for the unified emergence claim. No promotion implied. Ceiling: `scratch_diagnostic`, `promotion_allowed: false`, `formal_admission_allowed: false`.

### 6.1 Forks held open (do not collapse)

- **(A) Bridge:** HOMOMORPHISM-if-earned vs. NOT-YET-EVEN-HOMOMORPHISM/analogy-until-Φ-built. Decided by whether the sim constructs Φ and verifies the commuting square. The sim's job, not pre-decided here.
- **(B) Attractor object:** ONE object with cycles-only-in-readouts vs. minimax's THREE distinct objects (strict / revivable / branching). Collapsing loses falsifiability.
- **(C) Derivation severity:** deepseek "essentially sound, only omits memory" (mild) vs. minimax/kimi/codex2 "not sound as stated, N01 overclaims, near-tautological" (harsh).

### 6.2 Fleet run record

14 models dispatched in parallel; 13 returned OK, 1 hard-failed. codex2 at low/medium/high/xhigh held as the ARBITER lane (read-only, no vote per instruction) and sat inside the consensus. External fleet: grok-4.3, grok-build-0.1, gemini-3.1-pro-preview, openrouter/qwen3.7-max, openrouter/z-ai/glm-5.1, openrouter/minimax-m3, openrouter/deepseek-v4-pro, openrouter/moonshotai/kimi-k2.6, openrouter/moonshotai/kimi-k2.7-code.

- **FAILED:** `openrouter/fusion` — provider HTTP 500 Internal Server Error on both the driver call and a direct probe. NOT a 404 (the slug routes; upstream errored). Owner flagged it as possibly-smartest; unreachable this run; worth a retry (transient/upstream fault).
- **CAVEAT:** `kimi-k2.7-code` returned 39KB of RAW CHAIN-OF-THOUGHT (leaked internal scratch) and truncated mid-definition at the 9000-token cap. Substantive but reasoning-in-progress, not a finalized peer verdict; weighted accordingly.
- **Repo-native lane:** codex2_xhigh ALONE anchored to the actual root axioms (`root_axioms:17`, `:65`) and the scratch-only status of `gcm_ratchet_order_matrix_v1` (`audit_verdict.md:10`), adding typed tests + the probe-relative quotient `~_k` + the `M_k`/`~_k` components — structure the 9 external models did not surface.

ASSISTANT-GLOSS: next (owner's call, not done here): retry `openrouter/fusion` (likely transient 500). The convergent refined-definition core to adopt = "finite TYPED admissibility updates over a probe-relative quotient `~`, with monotone graveyard, append-only receipt memory, history-dependent tests, and ≥1 observable noncommuting update pair" (codex2_xhigh's clean core, absorbing the external fleet's edits + the repo-native probe quotient). No promotion implied — fleet-advisory critique, ceiling `scratch_diagnostic`.
