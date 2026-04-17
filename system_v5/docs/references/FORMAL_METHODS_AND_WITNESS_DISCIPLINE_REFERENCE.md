# Formal Methods and Witness Discipline: Formal Reference

Date: 2026-04-05
Status: Reference doc — actual formal frameworks, not the system's application

---

## Model Checking (Clarke, Emerson, Sifakis — 2007 Turing Award)

Algorithmic method: given finite-state model M and temporal logic formula φ,
determine whether M ⊨ φ. Exhaustively enumerates ALL reachable states.

A passed model check is a PROOF, not a sample. Differs from testing: testing
checks some executions, model checking checks all.

Temporal logics:
- CTL (branching-time): path quantifiers (A=all, E=some) + temporal operators
  (G=always, F=eventually, X=next, U=until). O(|M|·|φ|).
- LTL (linear-time): operators over individual traces. PSPACE-complete.

Tradeoff: state explosion — state spaces grow exponentially with concurrent
components.

---

## SAT/SMT Solving

### SAT (Boolean Satisfiability)

Given Boolean formula φ, does an assignment σ exist such that σ ⊨ φ?
Canonical NP-complete problem (Cook-Levin 1971).

### SMT (Satisfiability Modulo Theories)

Generalizes SAT to first-order formulas over background theories — linear
arithmetic, arrays, bit vectors, uninterpreted functions.

Key solvers: Z3 (Microsoft Research), CVC5 (Stanford/Iowa).

### Witnesses and Certificates

- SAT result → satisfying assignment (the witness). Checkable in O(|φ|).
- UNSAT result → proof of unsatisfiability (DRAT format). Checkable by
  verified tools.

The fundamental asymmetry: FINDING may be hard (NP). CHECKING is cheap (P).

---

## Proof-Carrying Code (Necula & Lee, 1996-97)

Untrusted code arrives with a machine-checkable proof that it satisfies a
safety policy. The consumer runs a proof checker — small, trusted, fast.

Architecture:
- Code producer (untrusted): generates code + proof. Correctness of
  generation process is irrelevant.
- Code consumer (trusted): runs proof checker. Only trusted component.
  Small enough to manually audit.
- Safety policy: expressed in first-order predicate logic.

The proof IS the witness. Checking is polynomial. No trust in network,
compiler, or producer required. Only checker and policy must be trusted.

Foundational PCC (Appel, Princeton): checker trusts only machine semantics
and logic, not even the type system.

---

## CEGAR (Counterexample-Guided Abstraction Refinement)

Clarke, Grumberg, Jha, Lu, Veith (2000/2003).

The loop:
1. Abstract — construct overapproximating finite model
2. Model-check — verify property on abstract model. If satisfied, done (VERIFIED)
3. Analyze counterexample — if property fails, check if counterexample is
   real (concrete trace exists) or spurious (no concrete counterpart)
4. Refine — if spurious, split abstract states to eliminate this trace. Repeat.

Key: only refine where needed. The counterexample tells you exactly which
part of the abstraction is too coarse. Lazy — minimal work.

---

## Witness / Certificate in Formal Verification

A witness is evidence that a property holds or fails:

- Satisfying assignment: witnesses satisfiability. Checkable in O(|φ|).
- UNSAT certificate (DRAT proof): witnesses unsatisfiability. Checkable
  by small verified checker.
- Counterexample trace: witnesses safety violation. Concrete execution
  reaching bad state.
- Inductive invariant: witnesses safety. Predicate I such that
  Init ⟹ I, I ∧ T ⟹ I', I ⟹ Safe.

The fundamental asymmetry: finding witnesses may be NP-hard, PSPACE-hard,
or undecidable. CHECKING witnesses is polynomial. This is the entire basis
of NP: hard to find, easy to verify.

---

## Bisimulation

Given labeled transition system (S, Act, →), relation R ⊆ S×S is a
bisimulation if whenever (p,q) ∈ R:

1. For every p --a→ p', there exists q' such that q --a→ q' and (p',q') ∈ R
2. For every q --a→ q', there exists p' such that p --a→ p' and (p',q') ∈ R

Bisimilarity (~) is the largest bisimulation. It is an equivalence relation.

Park (1981) gave formal definition. Milner developed it in CCS
(1991 Turing Award).

No external observer can distinguish bisimilar systems by any sequence
of interactions. Strictly stronger than trace equivalence.

Connection to operational equivalence and indistinguishability: bisimilarity
formalizes "indistinguishable under all possible interaction sequences."

---

## Trace Theory / Labeled Transition Systems

LTS: (S, Act, →) — states, actions, transition relation.

Trace: finite sequence of actions a₁, a₂, ..., aₙ with corresponding
state transitions. Records only observable actions, not intermediate states.

Trace equivalence: traces(p) = traces(q). Same observable sequences.

Trace equivalence vs bisimulation:
- Bisimulation ⟹ trace equivalence (but not reverse)
- For deterministic systems, they coincide
- Bisimulation preserves branching structure
- Trace equivalence only preserves sequential ordering

Order matters: traces are ordered sequences. Different orderings → different
traces → trace-inequivalent systems. Directly connects to N01.

---

## Refinement

System A refines system B (A ≤ B) if A satisfies all properties B satisfies.
A's behaviors ⊆ B's allowed behaviors.

In CSP (Hoare):
- Traces refinement: traces(Q) ⊆ traces(P). Safety properties.
- Failures refinement: adds refusal sets. Deadlock freedom, liveness.
- Failures-divergence: standard CSP refinement.

Lattice structure: specifications ordered by refinement form a lattice.
Top = most permissive. Bottom = most constrained.

Refinement is compositional: if A refines B, then C[A] refines C[B]
for any context C. Modular verification.

---

## Invariant Checking

Invariant: property I(s) holding at all reachable states.

Inductive invariant:
1. Initiation: Init(s) ⟹ I(s)
2. Consecution: I(s) ∧ T(s,s') ⟹ I(s')
3. Safety: I(s) ⟹ Safe(s)

Mirrors mathematical induction (base case + inductive step).

Connection to viability: viability kernel = set where system CAN stay
(existential — at least one path stays). Inductive invariant = set where
system MUST stay (universal — all paths stay). Viability is existential,
invariance is universal.

Finding inductive invariants is undecidable in general. Practical methods:
abstract interpretation, IC3/PDR, k-induction, interpolation, manual
annotation verified by SMT solvers.

---

## Fail-Closed / Fail-Safe Design

Fail-safe: upon failure, defaults to state that does not endanger.
Fail-closed (fail-secure): default on failure is DENY, REJECT, CLOSE, HALT.

Examples: firewall drops all traffic when rule engine crashes. Valve closes
on power loss (spring-return). Access control locks doors on system failure.

Formal property: for all failure states f ∈ F, Safe(f) holds. This is itself
an invariant — safety must hold in all reachable failure modes.

Connection to formal verification: fail-closed is the operational analog of
UNSAT-as-default. Cannot prove property holds → reject. System requires
evidence of safety (witness/certificate), not assumption of safety.

Design principle formalized: decide(w) = allow iff verify(w) = valid;
otherwise deny. Default (empty witness set) → deny. The closed-world
assumption applied to system authorization.

---

## Sources

Clarke, Emerson, Sifakis Turing Award paper. Cook-Levin (1971).
Necula (1997) Proof-Carrying Code. Appel, Foundational PCC.
Clarke et al. (2000/2003) CEGAR. Park (1981), Milner CCS.
DRAT-trim proof checker (Heule). Z3 (de Moura & Bjorner).
CVC5. IEC 61508, DO-178C safety standards.
