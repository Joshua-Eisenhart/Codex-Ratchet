**CONSTRAINT_MANIFOLD_DERIVATION_v1**  
  
**[ASSUME] CMD01 DEPENDENCY: This derivation presupposes frozen admissibility of state tokens, transport relations, and obstruction relations.**  
  
**[DERIVE] CMD02 GLOBAL_CARRIER_SYMBOL: A minimal global carrier is admissible only as an explicitly declared token registry M whose elements are carrier tokens m.**  
  
**[DERIVE] CMD03 STATE_INDEXING_MAP: Any admissible global carrier M must admit an explicitly declared indexing relation Ind(s,m) binding each declared state token s to at least one carrier token m in M; no uniqueness is implied.**  
  
**[DERIVE] CMD04 NO_CANONICAL_POINTS: No admissible derivation may assume a canonical distinguished carrier token in M.**  
  
**[DERIVE] CMD05 COMPATIBILITY_RELATION: Compatibility induced by transport is admissible only as an explicitly declared binary relation CompM(m,n) over carrier tokens, supported by the existence of at least one admissible transport instance Tr(s,t) with Ind(s,m) and Ind(t,n).**  
  
**[DERIVE] CMD06 NO_TOTAL_COMPATIBILITY: No admissible derivation may assume CompM(m,n) holds for all carrier token pairs (m,n).**  
  
**[DERIVE] CMD07 NO_CONNECTEDNESS_ASSUMPTION: No admissible derivation may assume that the carrier tokens of M form a single compatibility component under CompM.**  
  
**[DERIVE] CMD08 OBSTRUCTION_LIFTING_RELATION: Obstruction is admissible on the carrier only via an explicitly declared relation ObsM((m,n),(p,q)) whose instances are supported by underlying obstruction instances Obs(τ,κ) together with compatibility support of the involved carrier pairs.**  
  
**[DERIVE] CMD09 OBSTRUCTION_INDUCED_NONTRIVIALITY: If there exists any admissible obstruction instance Obs(τ,κ), then admissibility requires that the global carrier structure include at least one nontrivial obstruction-lift instance ObsM((m,n),(p,q)) for some carrier tokens supporting τ and κ.**  
  
**[DERIVE] CMD10 PATH_TOKEN_ADMISSIBILITY: Path organization is admissible only via explicitly declared finite path tokens π and an endpoint relation End(π,m,n) over carrier tokens.**  
  
**[DERIVE] CMD11 PATH_SUPPORT_BY_TRANSPORT: Any asserted End(π,m,n) is admissible only if supported by a finite chain of admissible transport instances Tr(s0,s1),…,Tr(sk-1,sk) together with indexing Ind(si,mi) such that m0=m and mk=n are carrier tokens appearing in the chain; no equality predicate is introduced.**  
  
**[DERIVE] CMD12 PATH_CONCATENATION_SYMBOL: If a concatenation notion is admitted on paths, it is admissible only as an explicitly declared ternary relation Cat(π1,π2,π3) with no associativity, identity, or totality implied.**  
  
**[DERIVE] CMD13 NONFLATTENABILITY_CONDITION: Global trivialization of transport is forbidden whenever there exists a witnessed obstruction instance such that two path tokens with the same declared endpoints are supported by transport chains whose induced composites are distinguishable under DistS.**  
  
**[DERIVE] CMD14 NO_UNIVERSAL_TRIVIALIZATION_SCHEMA: No admissible derivation may include a universal schema asserting that for all carrier tokens m,n there exists a path token π with End(π,m,n) supported by transport and producing indistinguishable composites independent of path token choice.**  
  
**[DERIVE] CMD15 FORBIDDEN_METRIC_STRUCTURE: No admissible derivation may introduce any numeric or ordered distance-like relation on carrier tokens.**  
  
**[DERIVE] CMD16 FORBIDDEN_COORDINATE_STRUCTURE: No admissible derivation may introduce any coordinate assignment, chart, or tuple-valued labeling of carrier tokens that carries substitution power.**  
  
**[DERIVE] CMD17 FORBIDDEN_DIMENSION_ASSERTION: No admissible derivation may assert any dimensionality property of M.**  
  
**[OPEN] CMD18 GEOMETRY_AS_EXTENSION: Admissibility of introducing geometry-like structure on M is open, provided it is derived from CompM, path organization, and obstruction-lift relations and does not assume metric primitives.**  
  
**[OPEN] CMD19 CURVATURE_AS_EXTENSION: Admissibility of curvature-like invariants defined purely from obstruction-lift behavior and transport composition is open.**  
  
**[OPEN] CMD20 DIMENSIONALITY_AS_EXTENSION: Admissibility of derived dimensionality notions from purely relational properties of M is open, provided no coordinate or metric assumptions are introduced.**  
