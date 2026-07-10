Audit only the facts below. They are the complete evidence packet; do not claim local file access.

MEASURED INPUT FACTS

- Source semantics: 16 macro slots total, eight per engine type. Every slot is provisionally expanded across Ti, Te, Fi, Fe, all sharing that slot's one Axis-6 sign. Type-1/Type-2 chirality is separate from Axis-6 sign.
- The free-length packet was preregistered before results. It searched all 87,376 rooted words of lengths 2..8, quotienting cyclic rotation only into 11,586 oriented cycles. Repetition and omission were allowed; reversal stayed distinct; all cyclic phases were averaged. No authored target trajectory or desired length entered the score.
- Free-length main exposure was fixed-total: each beat had weight 1/L. The score was max(geometry_loss, Umegaki_entropy_loss) plus a small monotone MDL penalty that weakly favors shorter descriptions and has no length-four special case.
- There were 36 scenarios per engine. Physical preconditions and all preregistered destructive controls passed.
- Free-length winners: Type 1 winners were Fi>Fi, Te>Fi, and Ti>Fi>Fi. Type 2 winner was Fi>Fi in all main scenarios. No primitive length-four all-four-once cycle qualified for either engine. Required success was 35/36 per engine; qualifying counts were empty. Scientific verdict was RED.
- The free-length rerun was byte-identical. An independent validator that does not import the producer reconstructed all candidates, decoded raw arrays, recomputed winners/controls/verdict, and passed 11 mutation tests.
- Separate Z3 4.16.0 and cvc5 1.3.3 implementations queried a nine-state Z3xZ3 carrier for every length 2..8 under count-free baseline properties: both anonymous work kinds used, maps distinct and noncommuting somewhere, geometry and entropy progress witnessed, closed ordered trace, one shared sign. Both solvers admitted every length 2..8.
- Ten additional count-free axioms tested one at a time did not force four. Four prohibited controls that explicitly encoded cardinality four admitted only length four. Z3 and cvc5 agreed on all 105 queries each; a solver-free validator replayed 78 SAT models per solver; deterministic reruns matched.
- Both packets are scratch diagnostics. They forbid promotion, admission, Axis0, perception, object, MMM, ontology, mesh, or physics claims. The SMT result is bounded to one nine-state carrier and L=2..8.

Audit for hidden cardinality assumptions, objective-induced bias, finite-carrier artifacts, decorative solver use, and overstatement. State the strongest literal conclusion and the smallest next count-free experiment that could overturn it.

Your response MUST contain these exact section markers, each once, in this order:

MEASURED
INFERRED
REJECTED_OR_BLOCKED
NEXT_KILLABLE_TEST
CLAIM_CEILING
END_OF_AUDIT
