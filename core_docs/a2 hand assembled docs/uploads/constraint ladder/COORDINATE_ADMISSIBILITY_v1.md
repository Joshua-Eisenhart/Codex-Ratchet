**COORDINATE_ADMISSIBILITY_v1**  
  
**[ASSUME] COA01 DEPENDENCY: This specification presupposes frozen carrier M, compatibility CompM, path tokens with End and Cat, transport Tr/TrC, obstruction Obs/ObsM, and any admitted metric-like relations Met/MetP.**  
  
**[DERIVE] COA02 COORDINATE_SYMBOL_SCHEMA: A coordinate-like representation is admissible only as an explicitly declared relation Coord(x,c) where x is a carrier token or path token and c is a token in an explicitly declared finite coordinate-token registry C.**  
  
**[DERIVE] COA03 COORDINATE_MAP_PARTIALITY: No admissible coordinate-like representation may assume Coord(x,c) exists for all x, nor uniqueness of c for any x.**  
  
**[DERIVE] COA04 NO_IDENTITY_FROM_COORDINATES: No admissible coordinate-like representation may assert that sharing a coordinate token implies identity, equality, or indistinguishability of carrier or path tokens.**  
  
**[DERIVE] COA05 NO_SUBSTITUTION_FROM_COORDINATES: No admissible coordinate-like representation may introduce any schema permitting replacement of one token by another on the basis of Coord.**  
  
**[DERIVE] COA06 REPRESENTATION_ONLY: Any coordinate-like relation Coord is admissible only as a removable representation layer; no admissible specification may treat Coord as constraining or redefining carrier, transport, obstruction, geometry, or metric relations.**  
  
**[DERIVE] COA07 NO_CANONICAL_COORDINATIZATION: No admissible coordinate-like representation may assume a canonical or privileged coordinate assignment for any token or relation.**  
  
**[DERIVE] COA08 COMPATIBILITY_SUPPORT: Any asserted Coord(x,c) is admissible only if supported by at least one frozen relation instance involving x (e.g., CompM, End, Inc, Met), without introducing any new kernel constraint.**  
  
**[DERIVE] COA09 TRANSPORT_ORDER_SENSITIVITY_PRESERVATION: No admissible coordinate-like representation may include any schema that forces transport composition order-sensitivity witnesses to vanish or become indistinguishable solely due to Coord assignments.**  
  
**[DERIVE] COA10 OBSTRUCTION_PRESERVATION: No admissible coordinate-like representation may include any schema that forces obstruction witnesses to vanish or become indistinguishable solely due to Coord assignments.**  
  
**[DERIVE] COA11 NO_GLOBAL_COORDINATE_SYSTEM: No admissible coordinate-like representation may assert the existence of a global coordinate system covering all carrier tokens or all compatible pairs.**  
  
**[DERIVE] COA12 FORBIDDEN_DIMENSION_SCHEMA: No admissible coordinate-like representation may assert any dimensionality, rank, or coordinate-length property of C or of Coord assignments.**  
  
**[DERIVE] COA13 FORBIDDEN_CHART_ATLAS_SCHEMA: No admissible coordinate-like representation may introduce chart or atlas structures with overlap rules unless explicitly declared OPEN in a later extension.**  
  
**[OPEN] COA14 CHART_EXTENSIONS: Admissibility of chart-like collections of coordinate relations is open, provided no dimensionality, rank, or metric primitives are introduced and Coord remains removable.**  
  
**[OPEN] COA15 ATLAS_EXTENSIONS: Admissibility of atlas-like structures organizing multiple chart-like collections is open, provided Coord remains non-authoritative and introduces no substitution power.**  
  
**[OPEN] COA16 DIMENSIONALITY_EXTENSIONS: Admissibility of derived dimensionality notions from purely relational properties of coordinate-token registries is open, provided no rank primitives or completed infinities are introduced.**  
