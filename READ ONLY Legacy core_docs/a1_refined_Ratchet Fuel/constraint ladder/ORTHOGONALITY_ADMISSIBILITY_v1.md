**ORTHOGONALITY_ADMISSIBILITY_v1**  
  
**[ASSUME] ORA01 DEPENDENCY: This specification presupposes admitted axis-like function symbols F,G,… and admitted finite axis-sets Σ with membership Mem(Σ,F), under frozen carrier/transport/obstruction structure.**  
  
**[DERIVE] ORA02 ORTHOGONALITY_SYMBOL_SCHEMA: An orthogonality-like relation is admissible only as an explicitly declared binary relation symbol Orth(F,G) ranging over admitted axis-like function relation symbols.**  
  
**[DERIVE] ORA03 ORTH_PARTIALITY_DEFAULT: No admissible orthogonality-like relation may assume Orth(F,G) is defined for all pairs of function symbols, nor assume uniqueness or completeness of Orth structure.**  
  
**[DERIVE] ORA04 NONMETRIC_GUARANTEE: No admissible orthogonality-like relation may assert or imply any metric, norm, distance, or inner product structure on carrier tokens, state tokens, path tokens, or value-token registries.**  
  
**[DERIVE] ORA05 NOBASIS_NORANK_GUARANTEE: No admissible orthogonality-like relation may assert or imply bases, coordinate frames, rank, completeness, dimensionality, or spanning properties for any axis-set or family of functions.**  
  
**[DERIVE] ORA06 NO_IDENTITY_FROM_ORTH: No admissible orthogonality-like relation may assert that Orth(F,G) implies identity, equality, or substitutability of function symbols or any tokens they reference.**  
  
**[DERIVE] ORA07 NO_SUBSTITUTION_FROM_ORTH: No admissible orthogonality-like relation may introduce any schema permitting replacement of tokens or function symbols on the basis of Orth.**  
  
**[DERIVE] ORA08 TRANSPORT_ORDER_SENSITIVITY_PRESERVATION: No admissible orthogonality-like relation may include any schema that forces transport composition order-sensitivity witnesses to vanish or become indistinguishable solely due to Orth declarations.**  
  
**[DERIVE] ORA09 OBSTRUCTION_PRESERVATION: No admissible orthogonality-like relation may include any schema that forces obstruction witnesses to vanish or become indistinguishable solely due to Orth declarations.**  
  
**[DERIVE] ORA10 FORBIDDEN_SYMMETRY_SCHEMA: No admissible orthogonality-like relation may include any universal schema asserting Orth(F,G) implies Orth(G,F) for all F,G.**  
  
**[DERIVE] ORA11 FORBIDDEN_REFLEXIVITY_SCHEMA: No admissible orthogonality-like relation may include any universal schema asserting Orth(F,F) for all F.**  
  
**[DERIVE] ORA12 FORBIDDEN_TRANSITIVITY_SCHEMA: No admissible orthogonality-like relation may include any universal schema asserting Orth(F,G) and Orth(G,H) implies Orth(F,H).**  
  
**[DERIVE] ORA13 FORBIDDEN_GLOBAL_ORTHOGONAL_SET: No admissible orthogonality-like relation may assert existence of a global orthogonal family or global orthogonalization procedure over all admitted functions.**  
  
**[OPEN] ORA14 INNER_PRODUCT_EXTENSIONS: Admissibility of inner-product-like structures is open, provided they are introduced without assuming metrics, bases, rank, or dimensionality as primitives.**  
  
**[OPEN] ORA15 NORMED_SPACE_EXTENSIONS: Admissibility of normed-space-like structure is open, provided it does not introduce completed infinities and does not bind kernel admissibility.**  
  
**[OPEN] ORA16 HILBERT_LIKE_EXTENSIONS: Admissibility of Hilbert-like structures is open, provided they remain removable overlays and introduce no substitution power.**  
