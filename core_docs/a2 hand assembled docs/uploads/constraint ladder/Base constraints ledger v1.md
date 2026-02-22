# Base constraints ledger v1  
  
**ID: BC01**  
**STATEMENT: No primitive object is admitted unless it has a finite explicit encoding over a finite symbol set.**  
**FORBIDS: infinite primitive encodings, implicit primitives, unbounded alphabets**  
**PERMITS: finite encodings, explicit token domains**  
**OPEN: admissible encoding normal forms**  
  
**ID: BC02**  
**STATEMENT: No domain is admitted as containing an actually infinite set of mutually distinguishable elements; distinguishability must be bounded by some finite ceiling under admissible differentiation.**  
**FORBIDS: completed infinities of distinguishable elements, infinite-resolution primitives**  
**PERMITS: finite-bounded distinguishability regimes**  
**OPEN: whether the ceiling is uniform across all admissible regimes**  
  
**ID: BC03**  
**STATEMENT: It is forbidden to assume commutation-by-default for composition; there exist admissible composed expressions whose swapped order is not interchangeable under the system’s admissibility discipline.**  
**FORBIDS: universal commutation, swap-by-default, interchangeability assumptions**  
**PERMITS: order-sensitive composition**  
**OPEN: minimal witnessing conditions for non-interchangeability**  
  
**ID: BC04**  
**STATEMENT: No primitive identity predicate on state-tokens is admitted; any “sameness” claim must be derived from an admissible indistinguishability criterion rather than asserted.**  
**FORBIDS: primitive identity, object-permanence axioms, self-identity schemas**  
**PERMITS: derived indistinguishability-based identification**  
**OPEN: whether derived reflexivity must hold in all regimes**  
  
**ID: BC05**  
**STATEMENT: No primitive equality-as-substitutability rule is admitted; substitutability across contexts must be earned by explicit invariance conditions, not assumed.**  
**FORBIDS: equality primitives, unrestricted substitution, congruence-by-fiat**  
**PERMITS: context-scoped substitution after invariance is established**  
**OPEN: minimal invariance obligations for substitution**  
  
**ID: BC06**  
**STATEMENT: No global total order over state-tokens or operator-tokens is admitted; only explicit finite sequencing inside written compositions is allowed.**  
**FORBIDS: global ordering primitives, built-in precedence relations**  
**PERMITS: explicit sequence order within composed expressions**  
**OPEN: whether derived partial orders may be admitted later and under what conditions**  
  
**ID: BC07**  
**STATEMENT: No closure property is admitted by default; admissibility of parts does not imply admissibility of any composite unless closure is explicitly granted for that composite form.**  
**FORBIDS: closure-by-default, implicit composability, implicit union/aggregation closure**  
**PERMITS: guarded composition, explicitly scoped closure**  
**OPEN: admissible closure schemas (if any)**  
  
**ID: BC08**  
**STATEMENT: No identification of state-tokens is permitted except via finite probe families: each admissible probe induces a finite partition of state-tokens into outcome-classes, and indistinguishability is membership in the same classes for a chosen finite probe family.**  
**FORBIDS: semantic identification, label-based equivalence, infinite-outcome probing**  
**PERMITS: finite partitions induced by probes, probe-relative indistinguishability**  
**OPEN: whether probes are primitive tokens or derived from operators**  
  
**ID: BC09**  
**STATEMENT: No probabilistic primitives are admitted; no claims may rely on probabilities, distributions, likelihoods, or expectation-style quantities at the base layer.**  
**FORBIDS: probability primitives, distributional assumptions, expectation primitives**  
**PERMITS: non-probabilistic structural distinctions only**  
**OPEN: later admission conditions for probabilistic overlays**  
  
**ID: BC10**  
**STATEMENT: No metric, distance, norm, or coordinate chart is admitted as primitive structure on state-tokens; any such structure must be derived in a later layer.**  
**FORBIDS: metric primitives, coordinate primitives, distance-first foundations**  
**PERMITS: later representational structure after derivation**  
**OPEN: admissible adequacy criteria for later representations**  
  
**ID: BC11**  
**STATEMENT: No optimization or utility primitives are admitted; no acceptance rule may be justified by maximizing, minimizing, or otherwise optimizing any quantity at the base layer.**  
**FORBIDS: optimization primitives, utility primitives, extremization rules**  
**PERMITS: constraint-only admission**  
**OPEN: later admission conditions for selection principles**  
  
**ID: BC12**  
**STATEMENT: No semantic smuggling is admitted: forbidden primitives may not be reintroduced by synonym or informal paraphrase; any new term must be given an explicit admissible definition or remain unresolved.**  
**FORBIDS: synonym smuggling, informal reintroduction of forbidden primitives, implicit meanings**  
**PERMITS: explicit definitions, unresolved placeholders**  
**OPEN: admissible definition schemas for new terms**  
