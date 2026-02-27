**Path contract v1**  
  
**ID: P1_01**  
**STATEMENT: It is forbidden to treat “path” as primitive temporal evolution; a path is an explicitly encoded finite sequence of admissible tokens with no intrinsic time semantics.**  
**FORBIDS: temporal interpretation of paths, time-ordered evolution semantics, implicit dynamics**  
**PERMITS: finite encoded sequences, atemporal path objects**  
**OPEN: admissible token classes for path positions**  
  
**ID: P1_02**  
**STATEMENT: It is forbidden to admit paths over implicit global domains; each path must be explicitly scoped to a declared admissible domain of refinement-derived objects.**  
**FORBIDS: unscoped paths, global path spaces, paths over implicit domains**  
**PERMITS: domain-scoped paths, explicit domain declarations for paths**  
**OPEN: minimal admissible domain declaration schema for path domains**  
  
**ID: P1_03**  
**STATEMENT: It is forbidden to assume uniqueness or canonicity of paths between any two descriptions; multiple non-equivalent paths may coexist unless uniqueness is explicitly admitted.**  
**FORBIDS: canonical paths by default, uniqueness-by-fiat**  
**PERMITS: plurality of paths, coexistence of distinct paths**  
**OPEN: conditions under which uniqueness may be admitted**  
  
**ID: P2_01**  
**STATEMENT: It is forbidden to assume closure of path concatenation by default; concatenation of two paths is admitted only when explicit premises certify the concatenation is well-formed within the declared domain scope.**  
**FORBIDS: concatenation closure-by-default, implicit well-formedness of concatenation**  
**PERMITS: guarded concatenation, certified well-formed concatenation**  
**OPEN: admissible certification schemas for well-formed concatenation**  
  
**ID: P2_02**  
**STATEMENT: It is forbidden to assume associativity of path concatenation by default; associativity may hold only under explicitly declared premises.**  
**FORBIDS: associativity-by-fiat, implicit reassociation rewrites**  
**PERMITS: explicit reassociation under declared premises**  
**OPEN: admissible premises for associativity**  
  
**ID: P2_03**  
**STATEMENT: It is forbidden to assume an identity or empty-path element for concatenation by default.**  
**FORBIDS: empty path primitives, identity-by-default for concatenation**  
**PERMITS: concatenation without identity element**  
**OPEN: conditions under which an identity element may be admitted**  
  
**ID: P3_01**  
**STATEMENT: It is forbidden to assume any equivalence relation on paths beyond explicitly declared rewrite rules; no path equivalence is admitted by default.**  
**FORBIDS: path equivalence-by-default, endpoint-only equivalence, semantic equivalence of paths**  
**PERMITS: explicit path rewrite rules, explicitly declared path equivalence relations**  
**OPEN: admissible rewrite rule schemas for paths**  
  
**ID: P3_02**  
**STATEMENT: It is forbidden to treat two paths as interchangeable solely because they share the same multiset of tokens; order is part of the path encoding.**  
**FORBIDS: bag-of-tokens path semantics, order-erasure rewrites**  
**PERMITS: order-respecting paths**  
**OPEN: limited order-erasure rules under explicit premises**  
  
**ID: P3_03**  
**STATEMENT: It is forbidden to assume reversibility of paths; no path is paired with an inverse path by default.**  
**FORBIDS: path inverses by default, reversibility-by-fiat**  
**PERMITS: one-way paths, local reversibility only by explicit admission**  
**OPEN: admissible local reversibility schemas**  
  
**ID: P4_01**  
**STATEMENT: It is forbidden to define scalar accumulation along paths by default; any accumulation rule must be explicitly declared and scoped.**  
**FORBIDS: default accumulation, implicit additivity, implicit subadditivity**  
**PERMITS: explicitly declared accumulation rules, scoped accumulation**  
**OPEN: minimal admissible accumulation-rule schemas**  
  
**ID: P4_02**  
**STATEMENT: It is forbidden to assume additivity of any scalar functional across concatenation of paths; additivity may hold only under explicitly declared premises.**  
**FORBIDS: additivity-by-default, concatenation-additivity assumptions**  
**PERMITS: explicitly premised additivity claims**  
**OPEN: admissible premises for additivity**  
  
**ID: P4_03**  
**STATEMENT: It is forbidden to assume non-negativity or monotonicity of accumulated scalar values unless explicitly declared; no sign or monotone convention holds by default.**  
**FORBIDS: forced non-negativity, monotonicity-by-default, implicit magnitude semantics**  
**PERMITS: explicitly declared signedness and monotonicity conventions**  
**OPEN: admissible conventions consistent with E1–E8**  
  
**ID: P5_01**  
**STATEMENT: It is forbidden to use scalar accumulation to define or enforce admissibility of paths; path admissibility remains governed by BC01–BC12 and R1–R8, not by scalar values.**  
**FORBIDS: scalar-gated path admissibility, value-based path rejection rules**  
**PERMITS: scalars as descriptive abstractions only**  
**OPEN: later admission conditions for value-gated rules (if any)**  
  
**ID: P5_02**  
**STATEMENT: It is forbidden to use scalar accumulation to select a unique path or to enforce canonical path choices.**  
**FORBIDS: scalar-driven path selection, canonicalization by scalar minimization/maximization**  
**PERMITS: multiple admissible paths independent of scalar assignments**  
**OPEN: later admission conditions for selection mechanisms (if any)**  
  
**ID: P5_03**  
**STATEMENT: It is forbidden to interpret accumulated scalar values as probabilities, temporal rates, or utilities.**  
**FORBIDS: probabilistic interpretation, time/rate semantics, utility semantics**  
**PERMITS: non-probabilistic, atemporal, non-utility scalar accumulation only**  
**OPEN: later admission conditions for these interpretations**  
  
**ID: P6_01**  
**STATEMENT: It is forbidden to define endpoint-only semantics for paths by default; two paths with identical endpoints need not be equivalent or comparable.**  
**FORBIDS: endpoint-only collapse, endpoint-determined equivalence assumptions**  
**PERMITS: distinct paths sharing endpoints**  
**OPEN: later admission conditions for endpoint-based equivalence**  
  
**ID: P6_02**  
**STATEMENT: It is forbidden to assume existence of endpoints for all paths as primitive objects; endpoint notions, if used, must be explicitly declared and scoped.**  
**FORBIDS: primitive endpoint objects, global endpoint assignment**  
**PERMITS: explicitly declared endpoint notions**  
**OPEN: admissible endpoint schemas**  
  
**ID: P6_03**  
**STATEMENT: It is forbidden to assume that concatenation preserves any endpoint notion unless explicitly declared.**  
**FORBIDS: endpoint preservation-by-default, implicit endpoint laws**  
**PERMITS: explicit endpoint preservation claims under premises**  
**OPEN: admissible endpoint preservation premises**  
  
**ID: P7_01**  
**STATEMENT: It is forbidden to assume convergence, limits, or infinite extension of paths; all admitted paths are finite encodings and no limit process is admitted at this layer.**  
**FORBIDS: infinite paths, limit processes, convergence assumptions**  
**PERMITS: finite paths only**  
**OPEN: later admission conditions for infinite/limit constructions**  
  
**ID: P7_02**  
**STATEMENT: It is forbidden to assume indefinite repetition of a path is admissible; repetition is not admitted by default and must be explicitly certified when claimed.**  
**FORBIDS: repetition-by-default, implicit recurrence, unbounded iteration assumptions**  
**PERMITS: explicitly certified repetition claims**  
**OPEN: later admission conditions for repetition/recurrence notions**  
  
**ID: P7_03**  
**STATEMENT: It is forbidden to treat path repetition as introducing cycles or fixed points at this layer.**  
**FORBIDS: cycle semantics, fixed-point semantics**  
**PERMITS: repetition without cycle interpretation**  
**OPEN: later admission conditions for cycle/fixed-point notions**  
  
**ID: P8_01**  
**STATEMENT: This contract introduces no topological or geometric structure on the set of paths; any such structure must be introduced only by later contracts with explicit prerequisites.**  
**FORBIDS: topology-on-paths here, geometry-on-paths here, metric-on-paths here**  
**PERMITS: purely combinatorial/encoding-level path structure**  
**OPEN: later contract layers that may admit topology/geometry/metrics**  
  
**ID: P8_02**  
**STATEMENT: This contract introduces no canonical normal forms for paths; any normalization or rewriting discipline must be explicitly introduced later.**  
**FORBIDS: canonical normal forms by default, implicit normalization**  
**PERMITS: multiple representations allowed**  
**OPEN: later admission conditions for normal forms**  
  
**ID: P8_03**  
**STATEMENT: It is forbidden to treat introduction of paths as completing the theory’s semantics; paths do not grant implicit meanings beyond those explicitly declared.**  
**FORBIDS: semantic completion by paths, implicit meaning inflation**  
**PERMITS: explicitly declared meanings only**  
**OPEN: admissible semantic declaration schemas**  
