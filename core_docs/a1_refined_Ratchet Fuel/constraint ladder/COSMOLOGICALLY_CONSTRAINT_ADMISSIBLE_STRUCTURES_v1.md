**COSMOLOGICALLY_CONSTRAINT_ADMISSIBLE_STRUCTURES_v1, **  
  
  
COSMOLOGICALLY_CONSTRAINT_ADMISSIBLE_STRUCTURES_v1  
  
[ASSUME] CAS01 FINITUDE: Any admissible specification has a finite description over a finite alphabet.  
  
[ASSUME] CAS02 FINITE_REGISTRY: Any admissible specification declares a finite registry of atomic tokens used as carriers for all subsequent relations.  
  
[ASSUME] CAS03 NONCOMMUTATION: Admissible composition is not globally commutative; at least one admissible specification contains an order-sensitivity witness as a relation-instance.  
  
[ASSUME] CAS04 NO_PRIMITIVE_IDENTITY: No admissible specification may designate a privileged token as an identity element for all admissible compositions.  
  
[ASSUME] CAS05 NO_PRIMITIVE_EQUALITY: No admissible specification may introduce a primitive substitutive equality predicate on tokens.  
  
[DERIVE] CAS06 ADMISSIBLE_SPEC_SCHEMA: An admissible specification consists of (i) a finite token registry, (ii) a finite set of relation symbols with declared arities, and (iii) finite relation-instances interpreting those symbols over the token registry.  
  
[DERIVE] CAS07 COMPOSITION_RELATION: If a composition notion is admitted, it is represented as a ternary relation Comp(x,y,z) over tokens, with no totality assumed.  
  
[DERIVE] CAS08 DISTINGUISHABILITY_RELATION: If a distinction notion is admitted, it is represented as a binary relation Dist(x,y) over tokens, with no symmetry assumed.  
  
[DERIVE] CAS09 ORDER_SENSITIVITY_WITNESS: Order sensitivity is admitted only via finite witnesses of the form Comp(a,b,u), Comp(b,a,v), Dist(u,v), where a,b,u,v are tokens.  
  
[DERIVE] CAS10 NO_GLOBAL_COMMUTATION_AXIOM: No admissible specification may include a universal commutation axiom schema that forces order insensitivity for all composable pairs.  
  
[DERIVE] CAS11 NO_SUBSTITUTION_SCHEMA: No admissible specification may include a universal substitution schema that permits replacing a token by another token across all relation-instances.  
  
[DERIVE] CAS12 NO_CANONICAL_IDENTITY_LAW: No admissible specification may include a universal identity-law schema asserting existence of a token e satisfying Comp(e,x,x) and Comp(x,e,x) for all tokens x.  
  
[DERIVE] CAS13 PARTIALITY_DEFAULT: Totality of Comp is not assumed; any closure or total-composability condition must be explicitly declared and is not implied by admissibility.  
  
[DERIVE] CAS14 ASSOCIATIVITY_NOT_ASSUMED: Associativity of composition is not assumed; any associativity claim must be explicitly declared and is not implied by admissibility.  
  
[DERIVE] CAS15 INVERTIBILITY_NOT_ASSUMED: Invertibility of composition is not assumed; any inverse-like claim must be explicitly declared and is not implied by admissibility.  
  
[DERIVE] CAS16 CONGRUENCE_NOT_ASSUMED: Compatibility of any equivalence-like relation with composition is not assumed; any congruence-like claim must be explicitly declared and is not implied by admissibility.  
  
[OPEN] CAS17 DERIVED_EQUIVALENCE: A derived equivalence-like relation may be introduced only as a definition from explicitly declared finite relation-instances; no global substitution power is implied.  
  
[OPEN] CAS18 COMMUTATIVE_SUBCLASS: Admissibility of explicitly declared commutative sub-specifications is open, provided no global commutation axiom is imposed on the overall admissible class.  
  
[OPEN] CAS19 IDENTITY_SURROGATE: Admissibility of identity-surrogate notions defined purely from declared relations is open, provided no universal identity law or substitution schema is introduced.  
  
[OPEN] CAS20 MINIMALITY_CRITERIA: Criteria for minimal admissible relation vocabularies sufficient to witness noncommutation without primitive equality are open.  
