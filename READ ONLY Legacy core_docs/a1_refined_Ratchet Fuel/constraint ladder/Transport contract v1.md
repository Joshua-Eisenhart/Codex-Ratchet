**Transport contract v1**  
  
**ID: X1_01**  
**STATEMENT: It is forbidden to assume transport is global-by-default; any transport relation must be explicitly declared and domain-scoped over finitely encoded objects, paths, or neighborhood assignments.**  
**FORBIDS: global transport-by-default, unscoped transport claims, transport over implicit domains**  
**PERMITS: explicitly declared transport relations, domain-scoped transport claims**  
**OPEN: minimal admissible schemas for transport declarations**  
  
**ID: X1_02**  
**STATEMENT: It is forbidden to treat transport as time evolution or motion; transport is a structural mapping between declared compatible items with no temporal semantics.**  
**FORBIDS: temporal transport semantics, motion semantics, dynamics interpretation**  
**PERMITS: atemporal structural transport mappings**  
**OPEN: admissible schemas for transport directionality (if any)**  
  
**ID: X1_03**  
**STATEMENT: It is forbidden to assume identity transport by default; a transport mapping need not act as identity even when source and target encodings coincide under admissible equivalence.**  
**FORBIDS: identity transport-by-default, reflexive identity mapping assumption**  
**PERMITS: non-identity self-transport, explicit identity claims under premises**  
**OPEN: admissible premises for identity transport**  
  
**ID: X2_01**  
**STATEMENT: It is forbidden to assume transport is invertible or symmetric; any invertibility or symmetry property must be explicitly declared and scoped.**  
**FORBIDS: invertibility-by-default, symmetric transport-by-default, automatic two-way transport**  
**PERMITS: one-way transport, explicitly premised invertible transport**  
**OPEN: admissible premise schemas for invertibility/symmetry**  
  
**ID: X2_02**  
**STATEMENT: It is forbidden to assume transport composes by default; composition of transport mappings is admitted only under explicit certification of well-formedness and scope.**  
**FORBIDS: compositional closure-by-default, implicit well-formed transport composition**  
**PERMITS: guarded transport composition, certified compositional well-formedness**  
**OPEN: admissible certification schemas for transport composition**  
  
**ID: X2_03**  
**STATEMENT: It is forbidden to assume associativity of transport composition by default; associativity may hold only under explicitly declared premises.**  
**FORBIDS: associativity-by-fiat, implicit reassociation rewrites for transport**  
**PERMITS: explicit reassociation under declared premises**  
**OPEN: admissible premises for associativity of transport composition**  
  
**ID: X3_01**  
**STATEMENT: It is forbidden to assume transport preserves refinement relations, equivalences, compatibility, adjacency, or neighborhood structure by default; any preservation claim must be explicitly declared per relation family.**  
**FORBIDS: preservation-by-default, invariant-by-fiat transport, structure-preserving assumption**  
**PERMITS: explicitly premised preservation claims, relation-scoped invariance**  
**OPEN: admissible invariance schemas for each relation family**  
  
**ID: X3_02**  
**STATEMENT: It is forbidden to assume transport induces equivalence or identity between source and target; transport does not imply sameness without an explicitly declared equivalence criterion.**  
**FORBIDS: transport-implies-identity, transport-implies-equality, sameness-by-transport**  
**PERMITS: transport without sameness consequences**  
**OPEN: admissible equivalence criteria compatible with prior layers**  
  
**ID: X3_03**  
**STATEMENT: It is forbidden to assume transport is determined solely by endpoints; two transports with identical source and target need not be equivalent or interchangeable.**  
**FORBIDS: endpoint-determined transport, canonical transport by endpoints, interchangeability-by-endpoints**  
**PERMITS: multiple distinct transports between same endpoints**  
**OPEN: later admission conditions for endpoint-determined transport (if any)**  
  
**ID: X4_01**  
**STATEMENT: It is forbidden to assume a global trivialization of transport; no global choice of consistent representatives is admitted by default.**  
**FORBIDS: global trivialization-by-default, global gauge fixing by fiat, global representative choice**  
**PERMITS: local transport structure only, nontrivial bundle-like organization**  
**OPEN: admissible conditions for trivialization claims**  
  
**ID: X4_02**  
**STATEMENT: It is forbidden to assume transport admits a canonical normal form; no normalization discipline is admitted by default.**  
**FORBIDS: canonical normal forms, implicit normalization of transport mappings**  
**PERMITS: multiple representations of transport mappings**  
**OPEN: later admission conditions for normal forms**  
  
**ID: X4_03**  
**STATEMENT: It is forbidden to assume transport mappings are unique given local compatibility or neighborhood data; multiple transports may coexist unless uniqueness is explicitly admitted.**  
**FORBIDS: uniqueness-by-fiat, determinism-from-local-data by default**  
**PERMITS: plural transports under same local data**  
**OPEN: admissible premises for uniqueness**  
  
**ID: X5_01**  
**STATEMENT: It is forbidden to map transport structure to geometric displacement, length, or distance; no metric or geometric interpretation is admitted at this layer.**  
**FORBIDS: geometric displacement semantics, distance semantics, metric-from-transport**  
**PERMITS: purely relational transport only**  
**OPEN: later admission conditions for geometric interpretations**  
  
**ID: X5_02**  
**STATEMENT: It is forbidden to interpret transport as probabilistic transition or stochastic mapping.**  
**FORBIDS: probabilistic transition semantics, stochastic interpretation**  
**PERMITS: non-probabilistic transport only**  
**OPEN: later admission conditions for probabilistic overlays**  
  
**ID: X5_03**  
**STATEMENT: It is forbidden to interpret transport as utility-driven selection, preference, or optimization.**  
**FORBIDS: utility semantics, preference semantics, optimization objectives**  
**PERMITS: non-optimizing transport only**  
**OPEN: later admission conditions for selection mechanisms (if any)**  
  
**ID: X6_01**  
**STATEMENT: It is forbidden to assume transport invariants exist by default; any invariant under transport must be explicitly declared and scoped.**  
**FORBIDS: invariants-by-default, implicit conserved quantities**  
**PERMITS: explicitly declared invariants, scoped invariance claims**  
**OPEN: admissible schemas for invariants**  
  
**ID: X6_02**  
**STATEMENT: It is forbidden to assume scalar functionals are transport-invariant by default; any such invariance claim must be explicitly declared and scoped.**  
**FORBIDS: scalar invariance-by-default, entropy-like conservation by fiat**  
**PERMITS: explicitly premised scalar invariance claims**  
**OPEN: admissible premises for scalar invariance**  
  
**ID: X6_03**  
**STATEMENT: It is forbidden to use transport invariants to define or enforce admissibility; admissibility remains governed by BC01–BC12 and earlier contracts.**  
**FORBIDS: invariant-gated admissibility, conservation-based admission rules**  
**PERMITS: invariants as descriptive abstractions only**  
**OPEN: later admission conditions for invariant-gated rules (if any)**  
  
**ID: X7_01**  
**STATEMENT: It is forbidden to assume transport yields global connectedness or reachability; disconnected transport components are permitted unless connectedness is explicitly admitted.**  
**FORBIDS: global reachability-by-default, connectedness-by-transport, single-component assumption**  
**PERMITS: multiple transport components, local transport without global reachability**  
**OPEN: admissible conditions for connectedness claims**  
  
**ID: X7_02**  
**STATEMENT: It is forbidden to assume closure of transport mappings under arbitrary refinement operators or path rewrites; any closure or invariance must be explicitly declared.**  
**FORBIDS: closure-by-default under refinement, rewrite-invariant transport by fiat**  
**PERMITS: explicitly premised closure/invariance claims**  
**OPEN: admissible closure schemas under refinement/rewrites**  
  
**ID: X7_03**  
**STATEMENT: It is forbidden to collapse transport structure into compatibility, adjacency, or neighborhood structure; transport is an additional relation layer not reducible by default.**  
**FORBIDS: transport-as-compatibility, transport-as-adjacency, transport-as-neighborhood mapping by default**  
**PERMITS: transport as distinct relational layer**  
**OPEN: later admission conditions for reductions (if any)**  
  
**ID: X8_01**  
**STATEMENT: This contract introduces no curvature, obstruction, or holonomy semantics; any such notions must be introduced only by later contracts with explicit prerequisites.**  
**FORBIDS: curvature semantics here, obstruction semantics here, holonomy semantics here**  
**PERMITS: pre-curvature transport structure only**  
**OPEN: later contract layers that may admit curvature/obstruction notions**  
  
**ID: X8_02**  
**STATEMENT: This contract introduces no analytic structure (continuity, differentiability, smoothness) on transport mappings.**  
**FORBIDS: continuity-by-default, differentiability-by-default, smoothness-by-default**  
**PERMITS: non-analytic transport structure only**  
**OPEN: later admission conditions for analytic structure**  
  
**ID: X8_03**  
**STATEMENT: It is forbidden to treat transport/bundle structure as completing the theory’s semantics or enforcing canonical meaning; only explicitly declared interpretations are permitted.**  
**FORBIDS: semantic completion by transport, implicit meaning inflation, canonical interpretation by default**  
**PERMITS: explicitly declared interpretations only**  
**OPEN: admissible semantic declaration schemas**  
