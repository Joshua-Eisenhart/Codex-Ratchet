**Entropy contract v1**  
  
**ID: E1_01**  
**STATEMENT: It is forbidden to assume a primitive scalar domain with completed infinitary structure; any scalar domain admitted for functionals must be finitely representable and must not be assumed complete or continuous.**  
**FORBIDS: completed scalar continua, completeness-by-fiat, continuity-by-fiat, infinitary scalar primitives**  
**PERMITS: finitely representable scalar encodings, discrete scalar domains**  
**OPEN: minimal admissible scalar-domain axioms at this layer**  
  
**ID: E1_02**  
**STATEMENT: It is forbidden to assume a primitive equality relation on scalar values beyond admissible equivalence on encodings; scalar “sameness” must be encoding-relative unless strengthened by later contracts.**  
**FORBIDS: primitive scalar equality, unrestricted scalar substitutability**  
**PERMITS: encoding-relative scalar equivalence, later strengthening by explicit prerequisites**  
**OPEN: admissible scalar equivalence schemas**  
  
**ID: E1_03**  
**STATEMENT: It is forbidden to assume total comparability of scalar values; any scalar comparison relation need not compare all pairs and must be explicitly declared.**  
**FORBIDS: total order-by-default, universal comparability, scalar ranking assumptions**  
**PERMITS: explicitly declared partial comparisons, non-total comparability**  
**OPEN: admissible comparison relations and their minimal axioms**  
  
**ID: E2_01**  
**STATEMENT: It is forbidden to introduce any scalar functional without explicit declaration of its domain of application as a finite-scope class of admissible refinement-derived objects.**  
**FORBIDS: unscoped functionals, functionals over implicit domains, functionals over global domains**  
**PERMITS: domain-scoped scalar functionals, explicit domain declarations**  
**OPEN: minimal admissible domain declaration schema for functional domains**  
  
**ID: E2_02**  
**STATEMENT: It is forbidden to treat scalar functionals as defining identity, equality, or unrestricted substitutability of refinement-derived objects.**  
**FORBIDS: value-equality implies object identity, functional collapse to equality, substitutability from matching values**  
**PERMITS: scalar-valued abstraction without identity consequences**  
**OPEN: admissible context-scoped substitution principles (if any)**  
  
**ID: E2_03**  
**STATEMENT: It is forbidden to assume that scalar functionals are invariant under arbitrary relabelings or rewrites unless invariance premises are explicitly declared.**  
**FORBIDS: invariance-by-default, rewrite-invariant-by-fiat, label-invariant-by-fiat**  
**PERMITS: explicitly premised invariance claims**  
**OPEN: admissible invariance premises and minimal schemas**  
  
**ID: E3_01**  
**STATEMENT: It is forbidden to assume monotonicity of any scalar functional with respect to refinement-derived ordering unless monotonicity is explicitly declared and scoped.**  
**FORBIDS: monotonicity-by-default, implicit order-consistency assumptions**  
**PERMITS: explicitly declared monotonicity under declared refinement relations**  
**OPEN: admissible monotonicity conditions and their minimal axioms**  
  
**ID: E3_02**  
**STATEMENT: It is forbidden to assume antisymmetry, additivity, or subadditivity properties for scalar functionals unless explicitly declared; no such algebraic law holds by default at this layer.**  
**FORBIDS: additivity-by-default, subadditivity-by-default, antisymmetry-by-default, algebraic law smuggling**  
**PERMITS: explicit law declarations only under stated prerequisites**  
**OPEN: admissible law families and prerequisite conditions**  
  
**ID: E3_03**  
**STATEMENT: It is forbidden to require non-negativity of scalar functionals by fiat; scalar values may be signed or unsigned only under explicit declaration of the comparison structure.**  
**FORBIDS: forced non-negativity, implicit absolute-value semantics**  
**PERMITS: signed or unsigned scalar conventions under explicit comparison declarations**  
**OPEN: admissible signedness conventions consistent with base constraints**  
  
**ID: E4_01**  
**STATEMENT: It is forbidden to interpret scalar values as probabilities, frequencies, likelihoods, or expectation-like quantities at this layer.**  
**FORBIDS: probabilistic interpretation, distribution semantics, expectation semantics**  
**PERMITS: non-probabilistic scalar abstraction only**  
**OPEN: later admission conditions for probabilistic overlays**  
  
**ID: E4_02**  
**STATEMENT: It is forbidden to interpret scalar values as temporal rates, durations, or causal strengths.**  
**FORBIDS: time/rate semantics, causal strength semantics, dynamical interpretations**  
**PERMITS: atemporal scalar abstraction only**  
**OPEN: later admission conditions for temporal/dynamical overlays**  
  
**ID: E4_03**  
**STATEMENT: It is forbidden to interpret scalar values as utilities, preferences, or optimization objectives.**  
**FORBIDS: utility semantics, preference semantics, objective semantics**  
**PERMITS: non-optimizing scalar abstraction only**  
**OPEN: later admission conditions for selection principles (if any)**  
  
**ID: E5_01**  
**STATEMENT: It is forbidden to introduce scalar accumulation rules over sequences, compositions, or concatenations; no accumulation law is admitted at this layer.**  
**FORBIDS: accumulation-by-default, additivity across sequences, subadditivity across sequences**  
**PERMITS: pointwise scalar assignments only**  
**OPEN: later contract interfaces for accumulation laws**  
  
**ID: E5_02**  
**STATEMENT: It is forbidden to treat scalar differences as distances or metrics between refinement-derived objects.**  
**FORBIDS: metric-from-scalars, distance semantics, norm semantics**  
**PERMITS: scalar-valued abstractions without metric interpretation**  
**OPEN: later admission conditions for metric derivations**  
  
**ID: E5_03**  
**STATEMENT: It is forbidden to assume completeness, convergence, or limit behavior of scalar functionals under iterative refinement or extension.**  
**FORBIDS: convergence-by-default, limit assumptions, completeness assumptions**  
**PERMITS: finite-scope scalar assignments only**  
**OPEN: later admission conditions for convergence/limit claims**  
  
**ID: E6_01**  
**STATEMENT: It is forbidden to treat scalar functionals as canonical or unique; multiple non-equivalent scalar functionals may coexist unless uniqueness is explicitly admitted.**  
**FORBIDS: uniqueness-by-fiat, canonical functional assumptions**  
**PERMITS: plurality of scalar functionals, coexistence of distinct functionals**  
**OPEN: conditions under which uniqueness could be admitted**  
  
**ID: E6_02**  
**STATEMENT: It is forbidden to collapse multiple scalar functionals into one by implicit identification of their codomains or value encodings; any inter-functional comparison must be explicitly declared.**  
**FORBIDS: codomain collapse, implicit cross-functional comparison, implicit common scale**  
**PERMITS: explicit inter-functional comparison declarations**  
**OPEN: admissible inter-functional comparison schemas**  
  
**ID: E7_01**  
**STATEMENT: It is forbidden to use scalar functionals to define or enforce admissibility; admissibility remains governed by BC01–BC12 and R1–R8, not by scalar values.**  
**FORBIDS: scalar-gated admissibility, value-based admission rules, scalar-based rejection rules**  
**PERMITS: scalars as descriptive abstractions only**  
**OPEN: later admission conditions for value-gated rules (if any)**  
  
**ID: E7_02**  
**STATEMENT: It is forbidden to use scalar functionals to select a unique refinement outcome or to enforce canonical refinement choices.**  
**FORBIDS: scalar-driven selection, canonicalization by scalar minimization/maximization, forced unique outcome by scalar value**  
**PERMITS: multiple admissible outcomes independent of scalar assignments**  
**OPEN: later admission conditions for selection mechanisms (if any)**  
  
**ID: E8_01**  
**STATEMENT: This contract introduces no path-level or composition-level scalar laws; any such laws must be introduced only by a later contract with explicit prerequisites.**  
**FORBIDS: path laws introduced here, composition laws introduced here, sequence laws introduced here**  
**PERMITS: pointwise scalar abstractions only**  
**OPEN: later contract layers that may admit path/composition scalar laws**  
  
**ID: E8_02**  
**STATEMENT: This contract introduces no topological, geometric, or metric structure derived from scalars; any such structure must be introduced only by later contracts with explicit prerequisites.**  
**FORBIDS: topology-from-scalars at this layer, geometry-from-scalars at this layer, metric-from-scalars at this layer**  
**PERMITS: scalars without geometric interpretation**  
**OPEN: later contract layers that may admit topology/geometry/metric derivations**  
  
**ID: E8_03**  
**STATEMENT: It is forbidden to treat the introduction of scalar functionals as completing the theory’s semantics; scalar functionals do not grant implicit meanings beyond those explicitly declared.**  
**FORBIDS: semantic completion by scalars, implicit meaning inflation, smuggled interpretation**  
**PERMITS: explicitly declared meanings only**  
**OPEN: admissible semantic declaration schemas**  
