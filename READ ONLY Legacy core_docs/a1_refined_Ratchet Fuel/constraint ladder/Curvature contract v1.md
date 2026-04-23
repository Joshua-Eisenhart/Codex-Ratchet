# Curvature contract v1  
  
**ID: C1_01**  
**STATEMENT: It is forbidden to assume obstruction vanishes by default; nontrivial obstruction is permitted unless triviality is explicitly admitted under declared premises.**  
**FORBIDS: obstruction-vanishes-by-default, flatness-by-fiat, trivialization-guarantee assumptions**  
**PERMITS: nontrivial obstruction tokens, explicit triviality claims under premises**  
**OPEN: admissible premise schemas for triviality of obstruction**  
  
**ID: C1_02**  
**STATEMENT: It is forbidden to treat obstruction as globally defined by default; any obstruction notion must be explicitly declared and scoped to a declared domain of finitely encoded transport and compatibility data.**  
**FORBIDS: global obstruction-by-default, unscoped obstruction claims, obstruction over implicit domains**  
**PERMITS: domain-scoped obstruction notions, explicit obstruction declarations**  
**OPEN: minimal admissible schemas for obstruction declarations**  
  
**ID: C1_03**  
**STATEMENT: It is forbidden to assume uniqueness or canonicity of obstruction; multiple non-equivalent obstruction notions may coexist unless uniqueness is explicitly admitted.**  
**FORBIDS: canonical obstruction by default, uniqueness-by-fiat, forced single obstruction notion**  
**PERMITS: plurality of obstruction notions, coexistence of distinct obstruction notions**  
**OPEN: admissible premises for uniqueness claims**  
  
**ID: C2_01**  
**STATEMENT: It is forbidden to assume transport is path-independent by default; any path-independence claim must be explicitly declared and scoped.**  
**FORBIDS: path-independence-by-default, flatness-by-default, endpoint-determined transport assumptions**  
**PERMITS: explicit path-independence claims under premises, path-dependent transport**  
**OPEN: admissible premise schemas for path-independence**  
  
**ID: C2_02**  
**STATEMENT: It is forbidden to compare or identify transport outcomes across distinct paths without an explicitly declared transport-comparison criterion; no such criterion is admitted by default.**  
**FORBIDS: default transport comparability, implicit equality of transport outcomes, semantic comparison rules**  
**PERMITS: explicitly declared transport-comparison criteria, scoped comparability**  
**OPEN: admissible transport-comparison schemas (e.g., discriminator-induced)**  
  
**ID: C2_03**  
**STATEMENT: It is forbidden to infer obstruction solely from endpoint coincidence or endpoint equivalence; obstruction claims require explicit transport-comparison evidence under declared criteria.**  
**FORBIDS: endpoint-only obstruction inference, obstruction-by-endpoints, equivalence-collapse obstruction**  
**PERMITS: obstruction witnessed by declared comparison criteria on transport outcomes**  
**OPEN: admissible evidence schemas for obstruction witnesses**  
  
**ID: C3_01**  
**STATEMENT: It is forbidden to assume loop-transport is identity by default; transport along a finitely encoded closed path may yield a non-identity self-transport unless identity is explicitly admitted.**  
**FORBIDS: identity loop-transport by default, trivial loop effects by fiat**  
**PERMITS: non-identity loop-transport effects, explicit identity claims under premises**  
**OPEN: admissible premises for identity loop-transport**  
  
**ID: C3_02**  
**STATEMENT: It is forbidden to treat closed-path transport effects as temporal cycles or recurrence; closed-path structure is purely compositional within the path/transport encodings.**  
**FORBIDS: temporal-cycle semantics, recurrence semantics, dynamical cycle interpretation**  
**PERMITS: atemporal closed-path transport effects**  
**OPEN: later admission conditions for any temporal reinterpretation (if any)**  
  
**ID: C3_03**  
**STATEMENT: It is forbidden to assume equivalence of closed-path transport effects under arbitrary path rewrites; any rewrite-invariance must be explicitly declared and scoped.**  
**FORBIDS: rewrite-invariant loop effects by default, path-rewrite invariance by fiat**  
**PERMITS: explicitly premised invariance claims for closed-path effects**  
**OPEN: admissible invariance schemas for closed-path transport effects**  
  
**ID: C4_01**  
**STATEMENT: It is forbidden to assume existence of a global consistent representative choice for transport data; globally consistent choice may fail unless existence is explicitly admitted.**  
**FORBIDS: global representative choice by default, guaranteed global trivialization, global gauge fixing by fiat**  
**PERMITS: nontrivial bundle-like organization, explicit existence claims under premises**  
**OPEN: admissible premise schemas for global representative existence**  
  
**ID: C4_02**  
**STATEMENT: It is forbidden to assume compatibility of locally declared representative choices across jointly scoped neighborhood assignments by default; any such compatibility must be explicitly declared.**  
**FORBIDS: automatic gluing of local choices, compatibility-on-overlaps by default, implicit joint-scope closure**  
**PERMITS: explicitly declared local compatibility conditions, explicit joint-scope declarations**  
**OPEN: admissible schemas for joint-scope declarations and compatibility conditions**  
  
**ID: C4_03**  
**STATEMENT: It is forbidden to assume obstruction data composes or satisfies algebraic laws by default; any composition or law must be explicitly declared and scoped.**  
**FORBIDS: obstruction composition-by-default, cocycle-law assumptions, algebraic law smuggling**  
**PERMITS: explicitly declared obstruction composition laws under premises**  
**OPEN: admissible law families for obstruction composition (if any)**  
  
**ID: C5_01**  
**STATEMENT: It is forbidden to assume curvature-like data is numeric or scalar-valued by default; any mapping from curvature-like data to scalar encodings must be explicitly declared and scoped.**  
**FORBIDS: numeric curvature by default, scalar curvature-by-fiat, implicit scalarization**  
**PERMITS: non-scalar curvature-like tokens, explicit scalarization maps under premises**  
**OPEN: admissible scalarization schemas and prerequisites**  
  
**ID: C5_02**  
**STATEMENT: It is forbidden to assume additivity, subadditivity, or monotonicity properties for curvature-like data by default.**  
**FORBIDS: additive curvature by default, subadditive curvature by default, monotone curvature by default**  
**PERMITS: explicitly declared law properties under premises**  
**OPEN: admissible law premises consistent with earlier contracts**  
  
**ID: C5_03**  
**STATEMENT: It is forbidden to treat curvature-like data as inducing metric distance, geometric displacement, or embedding structure.**  
**FORBIDS: metric-from-curvature, geometric displacement semantics, embedding semantics**  
**PERMITS: curvature-like structure as transport-incompatibility data only**  
**OPEN: later admission conditions for geometric reinterpretations (if any)**  
  
**ID: C6_01**  
**STATEMENT: It is forbidden to assume curvature-like data is invariant under arbitrary relabelings, refinements, or path rewrites; invariance must be explicitly declared per transformation family.**  
**FORBIDS: invariance-by-default, relabeling invariance by fiat, refinement invariance by fiat, rewrite invariance by fiat**  
**PERMITS: explicitly premised invariance claims**  
**OPEN: admissible invariance schemas per transformation family**  
  
**ID: C6_02**  
**STATEMENT: It is forbidden to collapse curvature-like data into compatibility, adjacency, or neighborhood structure by default; curvature-like data is an additional relation layer not reducible by default.**  
**FORBIDS: curvature-as-compatibility, curvature-as-adjacency, curvature-as-neighborhood by default**  
**PERMITS: curvature-like layer distinct from prior relations**  
**OPEN: later admission conditions for reductions (if any)**  
  
**ID: C6_03**  
**STATEMENT: It is forbidden to infer curvature-like data from scalar functionals alone; curvature-like data must be grounded in declared transport-comparison criteria and transport incompatibility evidence.**  
**FORBIDS: scalar-only curvature inference, curvature-by-scalar collapse, functional-only obstruction claims**  
**PERMITS: curvature-like data grounded in transport comparison evidence**  
**OPEN: admissible coupling schemas between scalars and transport evidence (if any)**  
  
**ID: C7_01**  
**STATEMENT: It is forbidden to use curvature-like data to define or enforce admissibility; admissibility remains governed by BC01–BC12 and earlier contracts.**  
**FORBIDS: curvature-gated admissibility, obstruction-based admission rules, curvature-based rejection rules**  
**PERMITS: curvature-like data as descriptive structure only**  
**OPEN: later admission conditions for curvature-gated rules (if any)**  
  
**ID: C7_02**  
**STATEMENT: It is forbidden to use curvature-like data to select canonical paths, canonical transports, or canonical representatives by default.**  
**FORBIDS: curvature-driven selection, canonicalization by obstruction minimization/maximization, forced canonical choices**  
**PERMITS: multiple admissible paths/transports/representatives independent of curvature-like data**  
**OPEN: later admission conditions for selection mechanisms (if any)**  
  
**ID: C7_03**  
**STATEMENT: It is forbidden to assume scalar functionals are curvature-invariant or curvature-determined by default; any such relation must be explicitly declared and scoped.**  
**FORBIDS: scalar-curvature coupling by default, curvature-determines-scalars by fiat, scalar-invariance-by-fiat under curvature**  
**PERMITS: explicitly premised coupling or invariance claims**  
**OPEN: admissible coupling/invariance schemas and prerequisites**  
  
**ID: C8_01**  
**STATEMENT: This contract introduces no geometric, metric, coordinate, or embedding structure; curvature-like notions are defined only through transport incompatibility under declared comparison criteria.**  
**FORBIDS: geometry imports, metric imports, coordinate imports, embedding semantics**  
**PERMITS: transport-incompatibility-based curvature-like structure only**  
**OPEN: later admission conditions for geometric reinterpretation (if any)**  
  
**ID: C8_02**  
**STATEMENT: This contract introduces no analytic structure (continuity, differentiability, smoothness) on any declared objects, paths, transports, or curvature-like data.**  
**FORBIDS: continuity-by-default, differentiability-by-default, smoothness-by-default**  
**PERMITS: non-analytic structure only**  
**OPEN: later admission conditions for analytic structure (if any)**  
  
**ID: C8_03**  
**STATEMENT: It is forbidden to treat curvature/obstruction structure as completing the theory’s semantics or enforcing canonical meaning; only explicitly declared interpretations are permitted.**  
**FORBIDS: semantic completion by curvature, implicit meaning inflation, canonical interpretation by default**  
**PERMITS: explicitly declared interpretations only**  
**OPEN: admissible semantic declaration schemas**  
