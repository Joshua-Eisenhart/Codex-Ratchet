**REFINEMENT_CONTRACT_v1.1**  
  
**ID: R1_01**  
**STATEMENT: It is forbidden to assert a refinement relation as globally applicable by default; any refinement claim must be explicitly scoped to a declared admissible domain of finitely encoded descriptions.**  
**FORBIDS: global refinement-by-default, unscoped refinement claims, refinement over implicit domains**  
**PERMITS: domain-scoped refinement claims, explicit admissible domains**  
**OPEN: minimal admissible domain declaration schema, domain membership evolution under refinement (preserve/mutate/generate)**  
  
**ID: R1_02**  
**STATEMENT: It is forbidden to use refinement as a substitute for sameness; no refinement claim may be treated as implying identity or unrestricted substitutability.**  
**FORBIDS: refinement-as-sameness, refinement-implies-identity, refinement-implies-unrestricted-substitution**  
**PERMITS: refinement distinct from equivalence, substitution only under explicit invariance obligations**  
**OPEN: minimal invariance obligations sufficient for scoped substitution**  
  
**ID: R1_03**  
**STATEMENT: No refinement claim is admitted unless the claim includes an explicit finite witness token that binds the claim to the declared admissible domain; the witness is purely syntactic/declarative binding and carries no semantic, evidentiary, or evaluative force.**  
**FORBIDS: witness-free refinement claims, implicit refinement assertions, refinement claims detached from domain, semantic witnesses, evidentiary witnesses, evaluative witnesses**  
**PERMITS: explicit witness-bound refinement claims, syntactic binding tokens**  
**OPEN: admissible witness token schemas**  
  
**ID: R2_01**  
**STATEMENT: It is forbidden to assume commutation of refinement operators; no rule may reorder two refinement operators in a composite expression unless explicit premises grant that reordering.**  
**FORBIDS: commutation-by-default, unconditional operator swap, implicit reordering**  
**PERMITS: order-sensitive refinement operator expressions, conditional reordering under explicit premises**  
**OPEN: admissible premises for reordering**  
  
**ID: R2_02**  
**STATEMENT: It is forbidden to assume idempotence of refinement operators; repeated application is not interchangeable with single application unless explicitly admitted.**  
**FORBIDS: idempotence-by-default, projection-only refinement assumption**  
**PERMITS: repeated refinement as distinct expression, idempotence only by explicit admission**  
**OPEN: conditions under which idempotence may be admitted**  
  
**ID: R2_03**  
**STATEMENT: It is forbidden to assume invertibility of refinement operators; no refinement operator is paired with an undo operator by default.**  
**FORBIDS: invertibility-by-default, universal undo operators, implicit reversibility**  
**PERMITS: one-way refinement operators, local reversibility only by explicit admission**  
**OPEN: admissible local reversibility schemas**  
  
**ID: R3_01**  
**STATEMENT: No equivalence relation induced by refinement is admitted unless it is induced by a finite discriminator family that induces a finite partition of the declared admissible domain.**  
**FORBIDS: semantic equivalence primitives, equivalence without finite discriminator family, infinite discriminator families**  
**PERMITS: discriminator-induced equivalence, finite partitions**  
**OPEN: whether discriminator tokens are primitive or derived forms**  
  
**ID: R3_02**  
**STATEMENT: It is forbidden to promote discriminator-induced equivalence to global equality or unrestricted substitution; any substitution must remain explicitly scoped to the discriminator family and declared contexts.**  
**FORBIDS: global equality from relative equivalence, unrestricted substitution from equivalence, collapsing equivalence to identity**  
**PERMITS: scoped substitution within explicitly declared contexts**  
**OPEN: admissible context declaration schemas for substitution**  
  
**ID: R3_03**  
**STATEMENT: It is forbidden to assume discriminator-induced equivalence is preserved under arbitrary extension of discriminator families; any preservation property must be stated explicitly.**  
**FORBIDS: preservation-by-default under extension, stability-by-assumption, implicit monotonicity of equivalence**  
**PERMITS: explicit statements of how equivalence behaves under extension**  
**OPEN: optional preservation conditions that may be admitted later**  
  
**ID: R4_01**  
**STATEMENT: It is forbidden to assert a global ranking derived from refinement; any ordering derived from refinement must be explicitly domain-scoped and need not compare all pairs, even within a declared admissible domain.**  
**FORBIDS: global ranking, total comparability, refinement-based linearization**  
**PERMITS: domain-scoped partial ordering derived from refinement claims**  
**OPEN: minimal ordering axioms admissible for derived orderings**  
  
**ID: R4_02**  
**STATEMENT: It is forbidden to treat antisymmetry of any derived refinement ordering as identity; any antisymmetry condition must be stated relative to an explicitly declared equivalence relation.**  
**FORBIDS: antisymmetry-implies-identity, identity-by-order**  
**PERMITS: antisymmetry relative to a declared equivalence**  
**OPEN: admissible equivalence relations for antisymmetry**  
  
**ID: R4_03**  
**STATEMENT: No mapping from refinement-derived ordering to a scalar-valued rank is admitted at this layer.**  
**FORBIDS: scalar ranks, numeric grading, rank-function primitives**  
**PERMITS: non-scalar ordering only**  
**OPEN: later admission conditions for rank maps (if any)**  
  
**ID: R5_01**  
**STATEMENT: It is forbidden to admit arbitrarily long strict refinement chains within a fixed declared admissible domain; strict refinement depth must be finitely bounded per domain.**  
**FORBIDS: unbounded strict refinement chains, infinite strict chains within a fixed domain**  
**PERMITS: finitely bounded strict refinement depth per domain**  
**OPEN: whether a uniform bound across domains exists**  
  
**ID: R5_02**  
**STATEMENT: It is forbidden to introduce refinement by an infinite succession of nontrivial micro-steps; each nontrivial strict refinement step must be explicit and finite.**  
**FORBIDS: Zeno-style refinement, implicit infinite micro-steps, non-explicit strict steps**  
**PERMITS: explicit finite refinement steps only**  
**OPEN: admissible step-granularity conventions**  
  
**ID: R6_01**  
**STATEMENT: It is forbidden to require commutation of refinement operators as a prerequisite for forming composite refinement expressions; composite refinement expressions may be order-sensitive.**  
**FORBIDS: commutation-required well-formedness, rejecting order-sensitive composites**  
**PERMITS: order-sensitive composite refinement expressions**  
**OPEN: admissible syntactic normal forms for composites**  
  
**ID: R6_02**  
**STATEMENT: It is forbidden to treat two refinement operator sequences as interchangeable solely because they share the same multiset of operator tokens; order is part of the expression.**  
**FORBIDS: bag-of-operators semantics, order-erasure rewrites, multiset-based interchangeability**  
**PERMITS: order-respecting refinement expressions**  
**OPEN: limited order-erasure rules under explicit premises**  
  
**ID: R6_03**  
**STATEMENT: It is forbidden to force interchangeability of non-interchangeable refinement expressions by relabeling alone; relabeling cannot create commutation by fiat.**  
**FORBIDS: relabeling-induced commutation, commutation by renaming, interchangeability-by-relabeling**  
**PERMITS: invariance of non-interchangeability under admissible relabelings**  
**OPEN: admissible relabeling classes**  
  
**ID: R7_01**  
**STATEMENT: It is forbidden to assume refinement preserves admission by default; admission of refined descriptions must be explicit.**  
**FORBIDS: refinement-preserves-admission-by-default, closure-by-refinement**  
**PERMITS: guarded refinement application, explicit admission of refined descriptions**  
**OPEN: admissible admission schemas for refined descriptions, domain membership effect of refinement (preserve/mutate/generate)**  
  
**ID: R7_02**  
**STATEMENT: It is forbidden to assume compositional closure of refinement steps; admission of each composite refinement expression must be explicit even if each component step is admitted.**  
**FORBIDS: composite closure-by-default, implicit composite admission**  
**PERMITS: explicit admission per composite refinement expression**  
**OPEN: admissible composite admission schemas**  
  
**ID: R7_03**  
**STATEMENT: It is forbidden to treat discriminator-induced equivalence as preserved under arbitrary refinement operators; preservation must be stated explicitly per operator family.**  
**FORBIDS: equivalence preservation-by-default, invariant-by-assumption under operators**  
**PERMITS: explicit preservation claims, operator-scoped invariance**  
**OPEN: admissible invariance schemas**  
  
**ID: R8_01**  
**STATEMENT: This contract introduces no primitive scalar-valued functionals; any scalar-valued functional must be introduced only by a later contract with explicit prerequisites.**  
**FORBIDS: scalar functional primitives introduced here, grading functionals, scalar evaluation primitives**  
**PERMITS: refinement-only primitives (relations/operators/equivalences)**  
**OPEN: later contract interfaces for scalar functionals**  
  
**ID: R8_02**  
**STATEMENT: This contract introduces no global structural schema beyond domain-scoped relations and operators; any additional primitives must be introduced only by later contracts with explicit prerequisites.**  
**FORBIDS: global schema injection, implicit additional primitives, hidden structure imports**  
**PERMITS: domain-scoped relations and operators only**  
**OPEN: explicit list of later contract layers**  
  
**ID: R8_03**  
**STATEMENT: It is forbidden to treat refinement as yielding a unique canonical outcome by default; multiple non-interchangeable refined descriptions may coexist unless uniqueness is explicitly admitted.**  
**FORBIDS: uniqueness-by-fiat, canonical refinement outcome by default, forced single outcome**  
**PERMITS: multiple admissible refinement outcomes**  
**OPEN: conditions under which uniqueness may be admitted**  
