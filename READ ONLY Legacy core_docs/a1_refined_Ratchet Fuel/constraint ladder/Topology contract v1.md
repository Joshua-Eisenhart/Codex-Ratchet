**Topology contract v1 **  
  
**ID: T1_01**  
**STATEMENT: It is forbidden to assume compatibility as global-by-default; any compatibility relation must be explicitly declared and domain-scoped over finitely encoded objects or paths.**  
**FORBIDS: global compatibility-by-default, unscoped compatibility claims, compatibility over implicit domains**  
**PERMITS: explicitly declared compatibility relations, domain-scoped compatibility claims**  
**OPEN: minimal admissible schemas for compatibility declarations**  
  
**ID: T1_02**  
**STATEMENT: It is forbidden to assume symmetry or transitivity of compatibility; any symmetry or transitivity claim must be explicitly declared and scoped.**  
**FORBIDS: symmetric-by-default compatibility, transitive-by-default compatibility, equivalence-by-fiat**  
**PERMITS: explicit symmetry claims, explicit transitivity claims, non-equivalence compatibility**  
**OPEN: admissible premise schemas for symmetry/transitivity**  
  
**ID: T1_03**  
**STATEMENT: It is forbidden to assume compatibility is preserved under arbitrary composition of descriptions or paths; preservation must be explicitly declared for each admitted composition form.**  
**FORBIDS: compatibility closure-by-default, preservation-by-fiat under composition, implicit compositional compatibility**  
**PERMITS: explicitly premised preservation under declared compositions**  
**OPEN: admissible preservation schemas for composition forms**  
  
**ID: T2_01**  
**STATEMENT: It is forbidden to treat adjacency as implying direction, precedence, or temporal ordering; adjacency is a structural relation without time semantics.**  
**FORBIDS: directional adjacency by default, precedence semantics, temporal adjacency semantics**  
**PERMITS: atemporal adjacency relations, structural adjacency claims**  
**OPEN: admissible schemas for directed adjacency (if any)**  
  
**ID: T2_02**  
**STATEMENT: It is forbidden to interpret adjacency as implying metric distance, magnitude of separation, or quantitative closeness.**  
**FORBIDS: distance semantics, metric interpretation, quantitative closeness inference**  
**PERMITS: non-metric adjacency only**  
**OPEN: later admission conditions for metric interpretations (if any)**  
  
**ID: T2_03**  
**STATEMENT: It is forbidden to assume transitive closure of adjacency or to equate adjacency with reachability; adjacency need not extend beyond explicitly declared pairs.**  
**FORBIDS: transitive closure-by-default, reachability-by-fiat, adjacency-as-connectivity assumption**  
**PERMITS: local adjacency without closure assumptions**  
**OPEN: admissible conditions for closure operations on adjacency**  
  
**ID: T3_01**  
**STATEMENT: It is forbidden to assume neighborhoods exist by default; any neighborhood assignment must be explicitly declared and domain-scoped.**  
**FORBIDS: neighborhood existence-by-default, unscoped neighborhood claims, global neighborhood structure**  
**PERMITS: explicit neighborhood assignments, domain-scoped neighborhood collections**  
**OPEN: minimal admissible schemas for neighborhood declarations**  
  
**ID: T3_02**  
**STATEMENT: It is forbidden to assume neighborhoods satisfy openness axioms, limit behavior, or convergence behavior; no such structure is admitted by default.**  
**FORBIDS: open-set axioms by default, limit semantics, convergence semantics**  
**PERMITS: neighborhood collections without openness/limit/convergence commitments**  
**OPEN: later admission conditions for openness/limit/convergence notions**  
  
**ID: T3_03**  
**STATEMENT: It is forbidden to assume closure properties for neighborhood collections (union, intersection, complement) unless explicitly declared and scoped.**  
**FORBIDS: closure-by-default, implicit neighborhood algebra, implicit lattice structure**  
**PERMITS: explicitly declared closure properties only**  
**OPEN: admissible closure schemas for neighborhood collections**  
  
**ID: T4_01**  
**STATEMENT: It is forbidden to treat a path as compatibility-valid by default; any compatibility-valid path claim must be explicitly certified relative to a declared compatibility relation.**  
**FORBIDS: compatibility-valid-by-default paths, implicit certification, semantic path validity**  
**PERMITS: explicitly certified compatibility validity, relation-relative path validity**  
**OPEN: admissible certification schemas for compatibility-valid paths**  
  
**ID: T4_02**  
**STATEMENT: It is forbidden to assume compatibility validity is preserved under path concatenation; any preservation claim must be explicitly declared and scoped.**  
**FORBIDS: preservation-by-default under concatenation, implicit compositional validity**  
**PERMITS: explicitly premised preservation under declared concatenation forms**  
**OPEN: admissible premises for preservation under concatenation**  
  
**ID: T4_03**  
**STATEMENT: It is forbidden to collapse compatibility validity into path equivalence or endpoint-only semantics; compatibility validity does not imply interchangeability.**  
**FORBIDS: compatibility-implies-equivalence, endpoint-only collapse, interchangeability-by-validity**  
**PERMITS: compatibility validity without equivalence consequences**  
**OPEN: later admission conditions for compatibility-based equivalence (if any)**  
  
**ID: T5_01**  
**STATEMENT: It is forbidden to assume neighborhood membership implies compatibility or adjacency; any such implication must be explicitly declared and scoped.**  
**FORBIDS: neighbor-implies-compatible by default, neighbor-implies-adjacent by default, implicit implication rules**  
**PERMITS: explicit implication declarations between neighborhood, compatibility, adjacency**  
**OPEN: admissible implication schemas and prerequisites**  
  
**ID: T5_02**  
**STATEMENT: It is forbidden to assume compatibility implies neighborhood membership or adjacency; compatibility does not generate neighborhoods by default.**  
**FORBIDS: compatibility-generates-neighborhoods, compatibility-implies-adjacency by default, derived neighborhoods-by-fiat**  
**PERMITS: compatibility relations independent of neighborhood assignments**  
**OPEN: later admission conditions for neighborhood generation rules**  
  
**ID: T5_03**  
**STATEMENT: It is forbidden to assume neighborhood structure is preserved under arbitrary refinement operators or path rewrites; preservation must be explicitly declared per operator or rewrite family.**  
**FORBIDS: invariance-by-default, preservation-by-fiat under refinement, rewrite-invariant neighborhoods by default**  
**PERMITS: explicitly premised preservation claims**  
**OPEN: admissible invariance schemas for neighborhood structure**  
  
**ID: T6_01**  
**STATEMENT: It is forbidden to use compatibility or adjacency to assert identity or equality of objects or paths; no sameness claim follows without an explicitly declared equivalence criterion.**  
**FORBIDS: identity from compatibility, equality from adjacency, sameness-by-relation**  
**PERMITS: relations without identity consequences, explicit equivalence criteria only**  
**OPEN: admissible equivalence criteria compatible with prior layers**  
  
**ID: T6_02**  
**STATEMENT: It is forbidden to treat matching neighborhood assignments as implying equivalence or substitutability; neighborhood coincidence has no equality force by default.**  
**FORBIDS: neighborhood-equality collapse, substitutability from neighborhood coincidence, equality-by-neighborhood**  
**PERMITS: neighborhood coincidence without equivalence consequences**  
**OPEN: later admission conditions for neighborhood-induced equivalence (if any)**  
  
**ID: T6_03**  
**STATEMENT: It is forbidden to map compatibility, adjacency, or neighborhood structure to scalar ranks or scalar distances by default; any such mapping must be introduced only by later contracts.**  
**FORBIDS: scalar ranking from relations, scalar distance from neighborhoods, implicit grading maps**  
**PERMITS: non-scalar relational structure only**  
**OPEN: later admission conditions for scalar mapping interfaces**  
  
**ID: T7_01**  
**STATEMENT: It is forbidden to assume global connectedness of the domain under adjacency or compatibility; multiple disconnected components are permitted unless connectedness is explicitly admitted.**  
**FORBIDS: global connectedness-by-default, single-component assumption, reachability-by-fiat**  
**PERMITS: multiple components, local structure without global connectivity**  
**OPEN: admissible conditions for connectedness claims**  
  
**ID: T7_02**  
**STATEMENT: It is forbidden to assume compatibility is total within any declared domain; incompatibility between some pairs is permitted unless totality is explicitly admitted.**  
**FORBIDS: total compatibility-by-default, universal pairwise compatibility, saturation assumptions**  
**PERMITS: partial compatibility, explicit totality claims under premises**  
**OPEN: admissible premises for total compatibility**  
  
**ID: T7_03**  
**STATEMENT: It is forbidden to assume a canonical neighborhood system for a domain; multiple neighborhood systems may coexist unless uniqueness is explicitly admitted.**  
**FORBIDS: canonical neighborhoods by default, uniqueness-by-fiat, single-system enforcement**  
**PERMITS: plural neighborhood systems, coexistence of distinct systems**  
**OPEN: conditions under which uniqueness may be admitted**  
  
**ID: T8_01**  
**STATEMENT: This contract introduces no geometric, metric, or coordinate structure; compatibility, adjacency, and neighborhoods are not to be interpreted as distances or embeddings at this layer.**  
**FORBIDS: geometry imports, metric imports, coordinate imports, embedding semantics**  
**PERMITS: purely relational/topological structure only**  
**OPEN: later admission conditions for geometric interpretations (if any)**  
  
**ID: T8_02**  
**STATEMENT: This contract introduces no continuity, differentiability, or smoothness assumptions; no such analytic structure is admitted by default.**  
**FORBIDS: continuity-by-default, differentiability-by-default, smoothness-by-default**  
**PERMITS: non-analytic relational structure only**  
**OPEN: later admission conditions for analytic structure (if any)**  
  
**ID: T8_03**  
**STATEMENT: It is forbidden to treat compatibility, adjacency, or neighborhoods as completing the theory’s semantics or enforcing canonical meaning; only explicitly declared interpretations are permitted.**  
**FORBIDS: semantic completion by topology, implicit meaning inflation, canonical interpretation by default**  
**PERMITS: explicitly declared interpretations only**  
**OPEN: admissible semantic declaration schemas**  
