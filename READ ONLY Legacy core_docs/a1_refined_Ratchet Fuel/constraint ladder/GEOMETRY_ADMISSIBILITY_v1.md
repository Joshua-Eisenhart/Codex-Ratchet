**GEOMETRY_ADMISSIBILITY_v1**  
  
**[ASSUME] GEA01 DEPENDENCY: This specification presupposes a frozen global carrier M with compatibility CompM, transport Tr/TrC, and obstruction Obs/ObsM as previously admitted.**  
  
**[DERIVE] GEA02 GEOMETRIC_STRUCTURE_SCHEMA: A geometric structure on M is admissible only as a finite collection of explicitly declared relation symbols over carrier tokens and path tokens, together with finite relation-instances, and with no additional primitives.**  
  
**[DERIVE] GEA03 INCIDENCE_RELATION_ADMISSIBILITY: An incidence notion is admissible only as an explicitly declared relation Inc(m,π,n) supported by End(π,m,n) and compatibility CompM(m,n).**  
  
**[DERIVE] GEA04 LOCALITY_RELATION_ADMISSIBILITY: A locality notion is admissible only as an explicitly declared binary relation Loc(m,n) whose instances are supported by CompM(m,n); no symmetry, reflexivity, or transitivity is implied.**  
  
**[DERIVE] GEA05 NO_METRIC_PRIMITIVES: No admissible geometric structure may introduce any numeric-valued or ordered distance-like, norm-like, or length-like primitive on carrier tokens or paths.**  
  
**[DERIVE] GEA06 NO_METRIC_DERIVATION_SCHEMA: No admissible geometric structure may include a universal schema deriving a distance-like ordering from compatibility, transport, or obstruction.**  
  
**[DERIVE] GEA07 NO_COORDINATE_ASSIGNMENT: No admissible geometric structure may introduce any coordinate assignment, chart, tuple-labeling, or coordinate-valued function on carrier tokens.**  
  
**[DERIVE] GEA08 NO_DIMENSION_ASSERTION: No admissible geometric structure may assert any dimensionality property of M or any coordinate-rank property.**  
  
**[DERIVE] GEA09 TRANSPORT_COMPATIBLE_GEOMETRY: Any admissible geometric relation that references paths must be supported by declared transport chains witnessing End(π,m,n); no independent path semantics is admissible.**  
  
**[DERIVE] GEA10 TRANSPORT_COMPOSITION_COMPATIBILITY: Any admissible geometric relation that references concatenation must be supported by explicitly declared Cat(π1,π2,π3) instances and must not assume associativity or identity of concatenation.**  
  
**[DERIVE] GEA11 OBSTRUCTION_RESPECT: No admissible geometric structure may include any schema forcing all transport-supported path composites between the same endpoints to be indistinguishable whenever a witnessed obstruction instance exists.**  
  
**[DERIVE] GEA12 FORBIDDEN_GLOBAL_FLAT_GEOMETRY_SCHEMA: No admissible geometric structure may include a universal schema asserting global flattenability of transport-supported path composites across all compatible endpoints.**  
  
**[DERIVE] GEA13 FORBIDDEN_EMBEDDING_ASSERTION: No admissible geometric structure may assert existence of an embedding of M into any coordinate-bearing or metric-bearing ambient structure.**  
  
**[DERIVE] GEA14 FORBIDDEN_CONTINUITY_ASSUMPTION: No admissible geometric structure may assume continuity, limits, convergence, or openness properties of any relation on M.**  
  
**[OPEN] GEA15 METRIC_EXTENSIONS: Admissibility of metric-like structures is open, provided they are derived without introducing metric primitives and do not trivialize obstruction.**  
  
**[OPEN] GEA16 DIMENSION_EXTENSIONS: Admissibility of derived dimensionality notions is open, provided no coordinate or rank primitives are introduced.**  
  
**[OPEN] GEA17 COORDINATE_EXTENSIONS: Admissibility of coordinate-like representations is open, provided they are treated as removable overlays and introduce no substitution power.**  
