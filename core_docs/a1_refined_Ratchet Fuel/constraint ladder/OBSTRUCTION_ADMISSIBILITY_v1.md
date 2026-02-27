**OBSTRUCTION_ADMISSIBILITY_v1**  
  
**[ASSUME] OBA01 FINITUDE: Any admissible obstruction specification is given by a finite description over a finite alphabet.**  
  
**[ASSUME] OBA02 DEPENDENCY: Any admissible obstruction specification presupposes frozen state abstraction and transport layers and ranges only over declared transport-related relation instances.**  
  
**[DERIVE] OBA03 OBSTRUCTION_SYMBOL_ADMISSIBILITY: An obstruction notion is admissible only as an explicitly declared binary relation symbol Obs(τ,κ), where τ and κ are transport-related relation instances over state tokens.**  
  
**[DERIVE] OBA04 OBSTRUCTION_WELLTYPEDNESS: Any asserted Obs(τ,κ) is admissible only if τ and κ are explicitly declared transport-related relation instances formed from symbols admitted in the transport layer.**  
  
**[DERIVE] OBA05 NONTRIVIALIZATION_FAILURE_FORM: A failure of transport trivialization is admissible only as a finite witnessed claim that two transport-related composites are distinguishable by the frozen state distinguishability relation.**  
  
**[DERIVE] OBA06 COMPOSITE_TRANSPORT_INSTANCE: If transport composition is used in an obstruction claim, it must be represented only via explicitly declared instances of TrC(·,·,·) over state tokens; no implicit composite formation is admissible.**  
  
**[DERIVE] OBA07 FAILURE_WITNESS_PATTERN: Any admissible obstruction witness must have the finite pattern TrC(a,b,u), TrC(c,d,v), DistS(u,v), together with admissible transport-witness bindings supporting the involved transport assertions; no other obstruction witness pattern is admissible at this layer.**  
  
**[DERIVE] OBA08 NO_GEOMETRIC_READING: No admissible obstruction specification may introduce any geometric, metric, coordinate, neighborhood, or embedding interpretation for Obs or its witnesses.**  
  
**[DERIVE] OBA09 OBSTRUCTION_WITNESSING_BINDING: Any assertion of Obs(τ,κ) is admissible only if accompanied by a finite witness binding WObs(τ,κ,w), where w is a token serving solely as a syntactic witness carrier.**  
  
**[DERIVE] OBA10 WITNESS_NONSEMANTIC: No admissible obstruction specification may treat witness tokens as semantic evidence, valuation, score, or truth-bearer; WObs binds only syntactic admissibility support.**  
  
**[DERIVE] OBA11 NONIDENTITY_FROM_OBSTRUCTION: No admissible obstruction specification may assert that Obs(τ,κ) implies identity or equality of any involved state tokens or transport instances.**  
  
**[DERIVE] OBA12 NO_SUBSTITUTION_FROM_OBSTRUCTION: No admissible obstruction specification may introduce any schema permitting replacement of any state token or transport instance on the basis of Obs(τ,κ).**  
  
**[DERIVE] OBA13 OBSTRUCTION_PARTIALITY_DEFAULT: No admissible obstruction specification may assume Obs(τ,κ) holds for all transport-related instance pairs.**  
  
**[DERIVE] OBA14 OBSTRUCTION_NONREFLEXIVE_DEFAULT: No admissible obstruction specification may assume Obs(τ,τ) holds for all transport-related instances τ.**  
  
**[DERIVE] OBA15 OBSTRUCTION_NONSYMMETRIC_DEFAULT: No admissible obstruction specification may assume Obs(τ,κ) implies Obs(κ,τ).**  
  
**[DERIVE] OBA16 OBSTRUCTION_NONTRANSITIVE_DEFAULT: No admissible obstruction specification may assume Obs(τ,κ) and Obs(κ,λ) imply Obs(τ,λ).**  
  
**[DERIVE] OBA17 FORBIDDEN_GLOBAL_FLATNESS_AXIOM: No admissible obstruction specification may include a universal axiom schema forcing absence of obstruction for all transport-related instance pairs.**  
  
**[DERIVE] OBA18 FORBIDDEN_GLOBAL_OBSTRUCTION_AXIOM: No admissible obstruction specification may include a universal axiom schema forcing obstruction for all transport-related instance pairs.**  
  
**[DERIVE] OBA19 FORBIDDEN_CANONICAL_OBSTRUCTION: No admissible obstruction specification may assert uniqueness or canonicity of obstruction witnesses beyond explicitly declared finite witnesses.**  
  
**[OPEN] OBA20 CURVATURE_LIKE_RELATIONS: Admissibility of explicitly declared higher-arity relations aggregating multiple obstruction instances is open, provided no geometric, metric, temporal, or motion semantics are introduced.**  
  
**[OPEN] OBA21 HOLONOMY_CLASS_TOKENS: Admissibility of class tokens representing families of obstruction-witness patterns is open, provided no primitive equality or substitution schema is introduced.**  
  
**[OPEN] OBA22 TRIVIALIZATION_SCHEMES: Admissibility of explicitly declared local trivialization schemes (restricted collections of transport instances where obstruction is absent) is open, provided no geometry, neighborhood, or metric language is introduced.**  
