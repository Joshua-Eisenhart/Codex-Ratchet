**RELATIONAL_TRANSPORT_ADMISSIBILITY_v1**  
  
**[ASSUME] RTA01 FINITUDE: Any admissible transport specification is given by a finite description over a finite alphabet.**  
  
**[ASSUME] RTA02 DEPENDENCY: Any admissible transport specification presupposes a frozen state abstraction layer and ranges only over declared state tokens.**  
  
**[DERIVE] RTA03 TRANSPORT_SYMBOL_ADMISSIBILITY: A transport notion is admissible only as an explicitly declared binary relation symbol Tr(s,t) over the finite state-token registry.**  
  
**[DERIVE] RTA04 TRANSPORT_WELLTYPEDNESS: Any asserted Tr(s,t) is admissible only if both s and t are declared state tokens in the state-token registry.**  
  
**[DERIVE] RTA05 NO_IDENTITY_FROM_TRANSPORT: No admissible transport specification may assert that Tr(s,t) implies identity or equality of s and t.**  
  
**[DERIVE] RTA06 NO_SUBSTITUTION_FROM_TRANSPORT: No admissible transport specification may introduce any schema permitting replacement of s by t (or t by s) in arbitrary relations on the basis of Tr(s,t).**  
  
**[DERIVE] RTA07 TRANSPORT_PARTIALITY_DEFAULT: No admissible transport specification may assume Tr(s,t) holds for all ordered pairs of state tokens.**  
  
**[DERIVE] RTA08 TRANSPORT_NONREFLEXIVE_DEFAULT: No admissible transport specification may assume Tr(s,s) holds for all state tokens s.**  
  
**[DERIVE] RTA09 TRANSPORT_NONSYMMETRIC_DEFAULT: No admissible transport specification may assume Tr(s,t) implies Tr(t,s).**  
  
**[DERIVE] RTA10 TRANSPORT_NONTRANSITIVE_DEFAULT: No admissible transport specification may assume Tr(s,t) and Tr(t,u) imply Tr(s,u).**  
  
**[DERIVE] RTA11 TRANSPORT_COMPOSITION_SYMBOL: If a composition of transport is admitted, it is admissible only as an explicitly declared ternary relation symbol TrC(s,t,u) with no closure, associativity, commutativity, identity, or invertibility implied.**  
  
**[DERIVE] RTA12 ORDER_SENSITIVITY_WITNESS: Any claim that transport composition is order-sensitive is admissible only via finite witnesses of the form TrC(a,b,u), TrC(b,a,v), DistS(u,v), where DistS is an admissible distinguishability relation on state tokens.**  
  
**[DERIVE] RTA13 NO_GLOBAL_COMMUTATION_OF_TRANSPORT: No admissible transport specification may include a universal axiom schema forcing TrC(a,b,·) to be indistinguishable from TrC(b,a,·) for all a,b.**  
  
**[DERIVE] RTA14 TRANSPORT_WITNESSING_BINDING: Any assertion of Tr(s,t) is admissible only if accompanied by a finite witness binding WTr(s,t,w), where w is a token serving solely as a syntactic witness carrier.**  
  
**[DERIVE] RTA15 WITNESS_NONSEMANTIC: No admissible transport specification may treat witness tokens as semantic evidence, valuation, score, or truth-bearers; WTr binds only syntactic admissibility support.**  
  
**[DERIVE] RTA16 WITNESS_SUPPORT_REQUIREMENT: Any admissible WTr(s,t,w) must be supported by finite declared bindings Abs(s,Σs), Abs(t,Σt) and declared representatives Rep(s,x), Rep(t,y) such that a declared relation instance R(x,y) exists in at least one of Σs or Σt.**  
  
**[DERIVE] RTA17 FORBIDDEN_GLOBAL_TRIVIALIZATION: No admissible transport specification may assert that transport trivializes globally by forcing Tr(s,t) for all state-token pairs.**  
  
**[DERIVE] RTA18 FORBIDDEN_GLOBAL_IDENTITY_TRANSPORT: No admissible transport specification may assert the existence of a universal transport identity law making Tr(s,s) hold for all s.**  
  
**[DERIVE] RTA19 FORBIDDEN_CANONICAL_TRANSPORT: No admissible transport specification may assert uniqueness or canonicity of transport between any ordered pair (s,t) without explicit finite witness declarations.**  
  
**[OPEN] RTA20 INVERTIBLE_TRANSPORT: Admissibility of an explicitly declared inverse-like relation InvTr(t,s) associated to Tr(s,t) is open, provided no substitution schema or identity/equality is introduced.**  
  
**[OPEN] RTA21 TRANSPORT_EQUIVALENCE_CLASSES: Admissibility of derived equivalence-like quotients induced by transport relations is open, provided no primitive equality or universal substitution is introduced.**  
  
**[OPEN] RTA22 TRANSPORT_LOOP_EFFECTS: Admissibility of explicitly declared loop-composition effects (nontrivial composites of transport around declared cycles) is open, provided no geometric, metric, temporal, or motion semantics are introduced.**  
