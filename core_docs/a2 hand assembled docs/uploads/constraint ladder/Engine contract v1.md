# Engine contract v1  
  
**ID: E1_01**  
**STATEMENT: It is forbidden to treat a cycle as primitive; a cycle is admitted only as a finitely encoded path equipped with an explicit closure witness under a declared closure predicate.**  
**FORBIDS: primitive cycles, closure-by-default, closure claims without explicit witness, closure predicates assumed implicit**  
**PERMITS: witness-bound closure declarations, cycles as derived path objects**  
**OPEN: admissible closure predicate schemas**  
  
**ID: E1_02**  
**STATEMENT: It is forbidden to admit cycles over implicit global domains; each admitted cycle must be explicitly scoped to a declared admissible domain of finitely encoded descriptions and paths.**  
**FORBIDS: unscoped cycles, global cycle spaces by default, cycles over implicit domains**  
**PERMITS: domain-scoped cycles, explicit domain declarations for cycles**  
**OPEN: minimal admissible domain declaration schemas for cycle domains**  
  
**ID: E1_03**  
**STATEMENT: It is forbidden to assume uniqueness or canonicity of cycles under a declared closure predicate; multiple non-equivalent cycles may coexist unless uniqueness is explicitly admitted.**  
**FORBIDS: canonical cycles by default, uniqueness-by-fiat, forced single-cycle representatives**  
**PERMITS: plural cycles, coexistence of distinct cycles under the same closure predicate**  
**OPEN: admissible premises for uniqueness claims**  
  
**ID: E2_01**  
**STATEMENT: It is forbidden to assume any equivalence relation on cycles by default; any cycle equivalence or comparability criterion must be explicitly declared and scoped and need not compare all pairs.**  
**FORBIDS: cycle equivalence-by-default, universal cycle comparability, total comparability assumptions**  
**PERMITS: explicitly declared cycle equivalence criteria, partial comparability relations**  
**OPEN: admissible schemas for cycle comparison criteria**  
  
**ID: E2_02**  
**STATEMENT: It is forbidden to collapse distinct cycles into the same class by relabeling or rewrite alone; any class identification must be justified by an explicitly declared cycle comparison criterion.**  
**FORBIDS: class collapse by renaming, equivalence by relabeling, rewrite-implies-equivalence by default**  
**PERMITS: criterion-grounded class identification, explicitly premised rewrite invariance**  
**OPEN: admissible invariance premises for cycle rewrites**  
  
**ID: E2_03**  
**STATEMENT: It is forbidden to treat matching values of any scalar functional as sufficient for cycle equivalence or interchangeability; value agreement does not imply sameness without an explicit equivalence criterion.**  
**FORBIDS: value-equality implies cycle equivalence, interchangeability-by-value, equivalence-by-scalar-only**  
**PERMITS: scalar functionals without equivalence consequences, explicit coupling rules under premises**  
**OPEN: admissible coupling schemas between scalar values and cycle equivalence (if any)**  
  
**ID: E3_01**  
**STATEMENT: It is forbidden to assume closure of cycle composition by default; composing two cycles yields an admitted cycle only under explicit certification of well-formedness and closure preservation under the declared closure predicate.**  
**FORBIDS: composition closure-by-default, implicit well-formedness of cycle composition, closure preservation-by-fiat**  
**PERMITS: guarded cycle composition, certified closure preservation**  
**OPEN: admissible certification schemas for composed-cycle admission**  
  
**ID: E3_02**  
**STATEMENT: It is forbidden to assume associativity of cycle composition by default; reassociation of composed cycles is permitted only under explicitly declared premises.**  
**FORBIDS: associativity-by-fiat, implicit reassociation rewrites, automatic bracketing erasure**  
**PERMITS: explicit reassociation under declared premises**  
**OPEN: admissible premises for associativity of cycle composition**  
  
**ID: E3_03**  
**STATEMENT: It is forbidden to admit unbounded repetition of a cycle by default; any repetition claim must be explicitly certified as a finite encoding and must not rely on an unbounded construction.**  
**FORBIDS: repetition-by-default, unbounded iteration assumptions, non-finite repetition encodings**  
**PERMITS: explicitly certified finite repetitions**  
**OPEN: admissible repetition certification schemas**  
  
**ID: E4_01**  
**STATEMENT: It is forbidden to assume stability predicates for cycles exist by default; any stability predicate must be explicitly declared and scoped to a declared finite perturbation family.**  
**FORBIDS: stability-by-default, implicit robustness claims, unstated perturbation families**  
**PERMITS: explicitly declared stability predicates, finite perturbation families**  
**OPEN: admissible schemas for perturbation families and stability predicates**  
  
**ID: E4_02**  
**STATEMENT: It is forbidden to use stability predicates to define or enforce admissibility or equivalence of cycles by default; stability has no admission or sameness force unless explicitly declared.**  
**FORBIDS: stability-gated admissibility, stability-implies-equivalence, canonicalization by stability**  
**PERMITS: stability as descriptive structure, explicit stability-to-admission or stability-to-equivalence rules under premises**  
**OPEN: admissible premises for any stability-to-admission or stability-to-equivalence rule**  
  
**ID: E4_03**  
**STATEMENT: It is forbidden to assume a unique stability notion for cycles; multiple non-equivalent stability predicates may coexist unless uniqueness is explicitly admitted.**  
**FORBIDS: canonical stability by default, uniqueness-by-fiat for stability predicates**  
**PERMITS: plural stability predicates, coexistence of distinct stability notions**  
**OPEN: admissible premises for uniqueness of stability notions**  
  
**ID: E5_01**  
**STATEMENT: It is forbidden to admit an engine-like object without explicit obstruction witness relative to a declared transport-comparison criterion on at least one admitted cycle.**  
**FORBIDS: engine admission without obstruction witness, obstruction-free engines by default, implicit transport outcome comparison criteria**  
**PERMITS: engine-like objects as cycle-plus-obstruction-witness structure, explicitly declared transport-comparison criteria**  
**OPEN: admissible schemas for obstruction witnesses and transport-comparison criteria**  
  
**ID: E5_02**  
**STATEMENT: It is forbidden to assume obstruction witnesses are trivial by default; nontrivial obstruction witnesses are permitted unless triviality is explicitly admitted under declared premises.**  
**FORBIDS: obstruction-trivial-by-default, flatness-by-fiat, automatic trivialization assumptions**  
**PERMITS: nontrivial obstruction witnesses, explicit triviality claims under premises**  
**OPEN: admissible premise schemas for triviality claims**  
  
**ID: E5_03**  
**STATEMENT: It is forbidden to identify or equate engine-like objects solely by their underlying cycles; any engine equivalence criterion must account for the obstruction witness and the declared comparison criterion.**  
**FORBIDS: engine equivalence-by-cycle-only, obstruction-ignorant identification, equivalence without declared criteria**  
**PERMITS: engine equivalence criteria that include cycle and obstruction structure**  
**OPEN: admissible schemas for engine equivalence criteria**  
  
**ID: E6_01**  
**STATEMENT: It is forbidden to assume a single engine class by default; multiple non-equivalent engine classes may coexist unless uniqueness is explicitly admitted.**  
**FORBIDS: single-engine-class assumption, canonical engine class by default, uniqueness-by-fiat**  
**PERMITS: plural engine classes, coexistence of distinct engine classes**  
**OPEN: admissible premises for uniqueness of engine classes**  
  
**ID: E6_02**  
**STATEMENT: It is forbidden to impose any global ranking, preference ordering, or forced best-choice rule over cycles or engine-like objects by default.**  
**FORBIDS: global ranking-by-default, preference ordering by fiat, forced best-choice rules**  
**PERMITS: absence of global ranking, explicit ranking relations only under later-layer premises**  
**OPEN: later admission conditions for ranking or preference relations (if any)**  
  
**ID: E6_03**  
**STATEMENT: It is forbidden to infer engine-like existence from the existence of cycles alone; engine-like admission requires explicit obstruction witness under a declared comparison criterion.**  
**FORBIDS: engines-from-cycles inference, obstruction-free engine inference, implicit evidence assumptions**  
**PERMITS: evidence-based engine admission via declared criteria**  
**OPEN: admissible evidence schemas for engine admission**  
  
**ID: E7_01**  
**STATEMENT: It is forbidden to assume any default rule for scalar functional accumulation along cycles; any cycle-accumulation rule must be explicitly declared, scoped, and certified as well-formed for the admitted cycle encodings.**  
**FORBIDS: default accumulation, implicit additivity, implicit law inheritance across cycles**  
**PERMITS: explicitly declared cycle-accumulation rules, certified well-formed accumulation**  
**OPEN: admissible schemas for cycle-accumulation rules and their certification**  
  
**ID: E7_02**  
**STATEMENT: It is forbidden to use scalar accumulation or scalar values to select a canonical cycle or canonical engine-like object by default.**  
**FORBIDS: scalar-driven canonicalization, selection-by-scalar-value, forced unique choice rules**  
**PERMITS: multiple admissible cycles/engines independent of scalar assignments**  
**OPEN: later admission conditions for selection mechanisms (if any)**  
  
**ID: E7_03**  
**STATEMENT: It is forbidden to assume scalar functionals or accumulated scalars are invariant under cycle rewrites or transport comparisons by default; any invariance claim must be explicitly declared and scoped.**  
**FORBIDS: invariance-by-default, rewrite-invariant scalars by fiat, transport-invariant scalars by fiat**  
**PERMITS: explicitly premised invariance claims**  
**OPEN: admissible invariance schemas for scalar functionals under rewrites and transport comparisons**  
  
**ID: E8_01**  
**STATEMENT: This contract introduces no representational primitives beyond finitely encoded cycles, explicitly declared comparison criteria, and explicit obstruction witnesses; no hidden structure is admitted by default.**  
**FORBIDS: hidden structure imports, additional primitives by default, schema injection by fiat**  
**PERMITS: explicit later-layer extensions under explicit prerequisites**  
**OPEN: explicit list of later-layer extension interfaces**  
  
**ID: E8_02**  
**STATEMENT: It is forbidden to assume canonical normal forms for cycles or engine-like objects by default; any normalization discipline must be explicitly declared and scoped.**  
**FORBIDS: canonical normal forms by default, implicit normalization, normalization-by-fiat**  
**PERMITS: multiple representations, explicitly declared normalization rules under premises**  
**OPEN: admissible normalization schemas**  
  
**ID: E8_03**  
**STATEMENT: It is forbidden to treat cycles or engine-like structure as completing the system’s semantics or enforcing canonical meaning; only explicitly declared interpretations are permitted.**  
**FORBIDS: semantic completion by engines, implicit meaning inflation, canonical interpretation by default**  
**PERMITS: explicitly declared interpretations only**  
**OPEN: admissible semantic declaration schemas**  
