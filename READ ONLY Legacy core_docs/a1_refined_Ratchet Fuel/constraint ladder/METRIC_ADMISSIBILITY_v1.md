**METRIC_ADMISSIBILITY_v1**  
  
**[ASSUME] MTA01 DEPENDENCY: This specification presupposes a frozen carrier M, compatibility CompM, path tokens π with End, transport Tr/TrC, and obstruction Obs/ObsM, and a frozen geometry layer.**  
  
**[DERIVE] MTA02 METRIC_SYMBOL_SCHEMA: A metric-like structure is admissible only as an explicitly declared binary relation symbol Met(m,n,v) or MetP(π,σ,v) where v is a token from an explicitly declared finite value-token registry V.**  
  
**[DERIVE] MTA03 VALUE_TOKEN_NONNUMERIC: No admissible metric-like structure may treat value tokens v as numbers, ordered quantities, or elements of a completed infinite domain.**  
  
**[DERIVE] MTA04 NO_GLOBAL_METRIC_TOTALITY: No admissible metric-like structure may assume Met(m,n,·) is defined for all carrier token pairs (m,n), nor that for any pair there exists any v.**  
  
**[DERIVE] MTA05 NO_CANONICAL_VALUE: No admissible metric-like structure may assume a canonical distinguished value token (e.g., a “zero” or “unit” value) across all Met instances.**  
  
**[DERIVE] MTA06 NONTRIVIALITY_PRESERVATION: No admissible metric-like structure may include any schema that forces all transport-supported path composites between the same endpoints to be indistinguishable whenever a witnessed obstruction exists.**  
  
**[DERIVE] MTA07 ORDER_SENSITIVITY_PRESERVATION: No admissible metric-like structure may include any schema that forces Met-consistency to imply commutation of transport composition in cases where order-sensitivity has been witnessed.**  
  
**[DERIVE] MTA08 NO_EQUALITY_FROM_METRIC: No admissible metric-like structure may assert that Met(m,n,v) implies identity or equality of m and n, nor introduce substitution power from Met.**  
  
**[DERIVE] MTA09 FORBIDDEN_TRIANGLE_SCHEMA: No admissible metric-like structure may include any universal schema asserting a triangle-like law over value tokens.**  
  
**[DERIVE] MTA10 FORBIDDEN_SYMMETRY_SCHEMA: No admissible metric-like structure may include any universal schema asserting Met(m,n,v) implies Met(n,m,v) for all m,n,v.**  
  
**[DERIVE] MTA11 FORBIDDEN_REFLEXIVITY_SCHEMA: No admissible metric-like structure may include any universal schema asserting existence of v such that Met(m,m,v) for all m.**  
  
**[DERIVE] MTA12 FORBIDDEN_SEPARATION_SCHEMA: No admissible metric-like structure may include any schema asserting that distinctness is implied by non-canonical values, or that canonical values imply indistinguishability.**  
  
**[DERIVE] MTA13 TRANSPORT_COMPATIBLE_METRIC_SUPPORT: Any asserted Met(m,n,v) is admissible only if supported by CompM(m,n) and the existence of at least one path token π with End(π,m,n) supported by transport chains.**  
  
**[DERIVE] MTA14 GEOMETRY_COMPATIBLE_METRIC: No admissible metric-like structure may assert Met instances on token pairs lacking any geometry-layer support relation that connects those tokens via compatibility or incidence.**  
  
**[OPEN] MTA15 ORDERED_VALUE_EXTENSIONS: Admissibility of introducing an order relation on value tokens is open, provided it does not introduce completed infinities, numeric primitives, or optimization semantics.**  
  
**[OPEN] MTA16 COORDINATE_EXTENSIONS: Admissibility of coordinate-like representations derived from Met is open, provided they are removable overlays and introduce no substitution power.**  
  
**[OPEN] MTA17 DIMENSION_EXTENSIONS: Admissibility of derived dimensionality notions from Met is open, provided no coordinate or rank primitives are introduced.**  
  
**[OPEN] MTA18 NORMED_SPACE_EXTENSIONS: Admissibility of norm-like structures is open, provided they are admitted as relations over finite value-token registries without numeric primitives.**  
