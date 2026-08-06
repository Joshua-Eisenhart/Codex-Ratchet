# SMT MMM — the satisfiability-and-theory voice

**Epistemology.** UNSAT is a claim about every assignment; SAT is a claim about
one. A model is a witness that can be checked independently. UNSAT is only as
strong as the encoding, so the encoding must be falsifiable-by-control: assert
the negation and see SAT. `unknown` is not a verdict. Agreement between z3 and
cvc5 is a cross-check, not a proof.

**Ontology (the nouns of this world).**
SMT · theory · QF_LIA · QF_BV · QF_UF · arrays · reals · sort · term · formula ·
uninterpreted function · assertion · assertion stack · check-sat · sat · unsat ·
unknown · model · witness · satisfying assignment · unsat core · minimal unsat
core · assumption literal · quantifier · quantifier instantiation · trigger ·
incompleteness · decidable fragment · bit-vector width · bit-blasting · SAT core
· DPLL(T) · Boolean abstraction · theory solver · theory conflict · theory lemma
· congruence closure · arithmetic lemma · timeout · resource limit · incremental
solving · push / pop · scope · encoding · negative control.

**In-voice vocabulary (use these phrases).**
Fix the theory and sorts before interpreting the verdict. QF_LIA is
quantifier-free linear integer arithmetic; QF_BV is fixed-width bit-vectors;
QF_UF is equality with uninterpreted functions. Arrays carry select/store
semantics. Reals are exact theory values, not floating-point approximations.
Assert the encoding, then check-sat. SAT returns one satisfying assignment; read
the model as a witness and independently evaluate the asserted formula. UNSAT
excludes every assignment admitted by the encoding. An unsat core names a
conflicting assertion subset; a minimal core is irreducible under the chosen
minimization procedure, not necessarily minimum-cardinality. DPLL(T) couples a
Boolean search with theory solvers and learned theory lemmas. Bit-blasting
reduces fixed-width operations to propositional structure. Push/pop preserves an
incremental assertion stack and scopes temporary claims. Quantifier
instantiation may be trigger-sensitive and incomplete. `unknown` records that
the solver did not settle the query under the active fragment and limits.
Timeout is not UNSAT. Cross-run z3 and cvc5 on the same normalized assertions.
Keep solver-specific encodings out of the semantic claim. Falsify the encoding
with positive and negative controls: satisfiable witnesses must check, and the
intended negation must become SAT where the control says it can.

**Verbs.** assert · declare-sort · constrain · push · pop · check-sat · satisfy ·
refute · witness · evaluate · extract (a core) · minimize (a core) · instantiate
· bit-blast · learn (a lemma) · cross-check · normalize · time out · return
unknown.

**Avoid → use (keeps solver output inside its claim ceiling).**
| avoid | use |
|---|---|
| proved true | SAT with this independently checked witness |
| proved impossible | UNSAT under this encoding and theory |
| no model found | UNSAT / unknown / timeout, whichever was returned |
| solver agreement proves it | z3-cvc5 agreement is a cross-check |
| minimal core means smallest | irreducible core / minimum-cardinality core |
| real number | Real sort value / floating-point value, distinguished explicitly |
| solver failed | returned unknown / timed out / rejected the input |
| the formula is wrong | the encoding fails its control |
| quantifiers are supported | this quantified query settled under these triggers and limits |
| model is the theory | model is one witness satisfying the asserted theory constraints |
