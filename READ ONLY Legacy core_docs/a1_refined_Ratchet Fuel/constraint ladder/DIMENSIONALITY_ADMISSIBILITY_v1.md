**DIMENSIONALITY_ADMISSIBILITY_v1**  
  
**[ASSUME] DMA01 DEPENDENCY: This specification presupposes frozen carrier M with compatibility CompM, transport Tr/TrC, obstruction Obs/ObsM, geometry relations, and optional removable coordinate relations Coord.**  
  
**[DERIVE] DMA02 DIMENSION_SYMBOL_SCHEMA: A dimensionality-like claim is admissible only as an explicitly declared relation Dim(A,d) where A is a token denoting a finite declared family of relation instances or representation instances, and d is a token in an explicitly declared finite dimension-token registry D.**  
  
**[DERIVE] DMA03 DIMENSION_TOKEN_NONNUMERIC: No admissible dimensionality-like structure may treat dimension tokens d as numbers, ordered quantities, or elements of a completed infinite domain.**  
  
**[DERIVE] DMA04 NO_PRIMITIVE_RANK: No admissible dimensionality-like structure may introduce rank primitives, basis primitives, or coordinate-length primitives as part of Dim.**  
  
**[DERIVE] DMA05 NO_GLOBAL_DIMENSIONALITY: No admissible dimensionality-like structure may assume that Dim(A,d) is defined for all admissible families A, nor that any canonical d exists for any A.**  
  
**[DERIVE] DMA06 NO_IDENTITY_FROM_DIM: No admissible dimensionality-like structure may assert that equality of dimension tokens implies identity, equality, or substitution among carrier tokens, paths, or relations.**  
  
**[DERIVE] DMA07 NO_SUBSTITUTION_FROM_DIM: No admissible dimensionality-like structure may introduce any schema permitting replacement of any token or relation instance on the basis of Dim.**  
  
**[DERIVE] DMA08 TRANSPORT_ORDER_SENSITIVITY_PRESERVATION: No admissible dimensionality-like structure may include any schema forcing transport composition order-sensitivity witnesses to vanish or become indistinguishable solely due to Dim declarations.**  
  
**[DERIVE] DMA09 OBSTRUCTION_PRESERVATION: No admissible dimensionality-like structure may include any schema forcing obstruction witnesses to vanish or become indistinguishable solely due to Dim declarations.**  
  
**[DERIVE] DMA10 PARTIALITY_DEFAULT: No admissible dimensionality-like structure may assume dimensionality claims exist for all compatibility components of M.**  
  
**[DERIVE] DMA11 FORBIDDEN_AXIS_SYSTEM: No admissible dimensionality-like structure may introduce any axis system, axis basis, coordinate rank, or vector-space basis structure at this layer.**  
  
**[DERIVE] DMA12 FORBIDDEN_CANONICAL_DIMENSION: No admissible dimensionality-like structure may assert that any family A has a unique canonical dimension token d independent of admissible representation choices.**  
  
**[DERIVE] DMA13 FORBIDDEN_DIMENSION_ADDITIVITY_SCHEMA: No admissible dimensionality-like structure may assert any universal additivity or product-like rule for Dim over composition of families A.**  
  
**[OPEN] DMA14 AXIS_EXTENSIONS: Admissibility of axis-system notions derived from Dim is open, provided they are removable representations and introduce no substitution power.**  
  
**[OPEN] DMA15 COORDINATE_RANK_EXTENSIONS: Admissibility of coordinate-rank notions is open, provided rank is not treated as primitive and dimensionality remains nonnumeric and non-authoritative.**  
  
**[OPEN] DMA16 VECTOR_SPACE_EXTENSIONS: Admissibility of vector-space-like structures is open, provided they are introduced without assuming completed infinities and without binding kernel admissibility.**  
