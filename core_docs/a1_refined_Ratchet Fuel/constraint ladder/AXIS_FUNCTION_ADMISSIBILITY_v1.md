**AXIS_FUNCTION_ADMISSIBILITY_v1**  
  
**[ASSUME] AFA01 DEPENDENCY: This specification presupposes frozen carrier M, state tokens, compatibility CompM, transport Tr/TrC, obstruction Obs/ObsM, and optional value-token registries used by prior metric and dimensionality layers.**  
  
**[DERIVE] AFA02 FUNCTION_SYMBOL_SCHEMA: A function-like assignment is admissible only as an explicitly declared binary relation F(x,v) where x is a carrier token or state token and v is a token in an explicitly declared finite value-token registry V.**  
  
**[DERIVE] AFA03 FUNCTION_PARTIALITY_DEFAULT: No admissible function-like assignment may assume F(x,v) exists for all x, nor uniqueness of v for any x.**  
  
**[DERIVE] AFA04 NONAXIS_GUARANTEE: No admissible function-like assignment may assert that F induces an axis, coordinate system, basis, parameterization, or ordering of the carrier.**  
  
**[DERIVE] AFA05 NO_GLOBAL_PARAMETERIZATION_SCHEMA: No admissible function-like assignment may include any universal schema asserting that carrier tokens are exhaustively represented or enumerated via F-values.**  
  
**[DERIVE] AFA06 NO_IDENTITY_FROM_FUNCTION_VALUES: No admissible function-like assignment may assert that shared function values imply identity, equality, or indistinguishability of tokens.**  
  
**[DERIVE] AFA07 NO_SUBSTITUTION_FROM_FUNCTION_VALUES: No admissible function-like assignment may introduce any schema permitting replacement of one token by another on the basis of F.**  
  
**[DERIVE] AFA08 TRANSPORT_COMPATIBILITY: Any assertion of F(x,v) that is used jointly with transport must not include any schema forcing transport composition order-sensitivity witnesses to vanish or become indistinguishable solely due to F-values.**  
  
**[DERIVE] AFA09 OBSTRUCTION_COMPATIBILITY: Any assertion of F(x,v) that is used jointly with obstruction must not include any schema forcing obstruction witnesses to vanish or become indistinguishable solely due to F-values.**  
  
**[DERIVE] AFA10 NO_TOTAL_FUNCTION_BY_DEFAULT: No admissible function-like assignment may assert existence of a total function over all carrier tokens or all state tokens.**  
  
**[DERIVE] AFA11 FORBIDDEN_ORDER_SCHEMA: No admissible function-like assignment may introduce any order relation on V and then assert a universal induced order on carrier or state tokens from F.**  
  
**[DERIVE] AFA12 FORBIDDEN_ADDITIVITY_SCHEMA: No admissible function-like assignment may assert any universal additivity, linearity, or homomorphism-like schema for combining F-values across transport composition or path concatenation.**  
  
**[OPEN] AFA13 AXIS_EXTENSIONS: Admissibility of promoting certain families of function-like assignments into true axes or coordinate systems is open, provided this introduces no substitution power and remains removable.**  
  
**[OPEN] AFA14 OPTIMIZATION_EXTENSIONS: Admissibility of using function values in optimization-like selection is open, provided time, probability, and utility semantics are not introduced as primitives.**  
  
**[OPEN] AFA15 ORDERED_VALUE_EXTENSIONS: Admissibility of introducing order on value tokens is open, provided it does not induce global ordering or parameterization of the carrier by default.**  
