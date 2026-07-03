last_updated: 2026-04-17

# Grammar — Sentence-Level Patterns

Verb discipline (see `03_language_discipline.md`) is necessary but leaky. Classical framing slips back in at the sentence level even when every verb is clean. This page fixes sentence patterns.

## Claim pattern (canonical)

> Under probe family **M** and constraint set **C**, candidate **X** [survived | was excluded | remains indistinguishable from Y]. Status: [exists | runs | passes local rerun | canonical by process]. Surviving alternatives: [...].

Every substantive claim should reduce to this shape. If a sentence will not reduce, it is smuggling.

## Subject discipline

- Subjects should be candidates, probes, constraints, or quotients — not bare objects
- `the Hopf torus` → `the Hopf torus candidate` or `the equivalence class under M_Hopf`
- `the state` → `the admissible state under C` or `the survivor in S/~_M`

## Predicate discipline

- Predicates should be relational and probe-scoped
- `is` → `survived / was admitted / remains indistinguishable from` (choose one with a probe reference)
- `equals` → `is indistinguishable from under M`
- `has property P` → `returns P under probe p ∈ M`

## Quantifier discipline

- `all X` → `all X surviving C so far` (open, not closed)
- `no X` → `no X admissible under C` (scope to constraint set)
- `exists X` → `candidate X is admissible under C` (never raw existence)
- `the X` → `the admissible X under C and M` (never bare definite article over ontology)

## Status phrasing

Every earned status must be cited with the check that earned it.

| Label | Phrasing |
|---|---|
| exists | "the file `path` is present in the repo" |
| runs | "the sim at `path` executed with exit 0 on `date`" |
| passes local rerun | "fresh rerun of `path` on `date` produced `result.json` with all-pass" |
| canonical by process | "`path` satisfies SIM_TEMPLATE + tool manifest + classification + non-empty reasons; result at `result.json`" |

Never write "verified", "confirmed", "28/28 pass", or "all pass" without specifying which criteria were checked and citing the result file path.

## "I don't know" — admissible forms

Classical framing treats ignorance as failure; the harness treats it as a legitimate result.

- "The probe family is not yet defined for this claim"
- "Constraint set C does not narrow the branch set here"
- "Candidate X survived; candidate Y survived; no probe in M distinguishes them"
- "Exclusion evidence is incomplete; branch remains open"

Never write "we don't know yet but probably X". The "probably" is closure without earned status.

## Forward vs backward

Separate forward-evolution claims from backward-admissibility claims explicitly.

- forward: "under dynamics D from state s_0, configuration s_1 is reachable"
- backward: "configuration s_1 is admissible under constraint set C applied to all reachable endpoints"

Do not collapse them. Forward reachability does not imply backward admissibility, and vice versa.

## Negation pattern

- `X is wrong` → `X was excluded under probe p` or `X is inconsistent with C under M`
- `X failed` → `X was excluded` or `X did not survive probe p`
- `X is impossible` → `X is UNSAT under C` (if z3 / cvc5 verified) or `no probe in M admits X`

UNSAT is stronger than SAT. Prefer impossibility evidence over existence evidence when both are available.

## Connective discipline

- `because` → `consistent with`, `coupled with`, or `co-varies under` (causality banned; correlation kept)
- `therefore` → `narrows the branch set to`, or `the surviving candidates under C are`
- `so` → same as `therefore`
- `if...then` is admissible IF both clauses are probe-scoped; otherwise rewrite

## Tense discipline

- past tense (survived, was excluded) is the default for earned results
- present tense (is admissible, remains indistinguishable) is reserved for the active constraint frame
- future tense (will pass, will exclude) is almost always wrong — rewrite as "candidate under current constraints" or as an explicit hypothesis

## Sentence-level pre-emit test

Before emitting a paragraph, ask:

1. does every subject name a candidate / probe / constraint / quotient?
2. does every predicate reference a probe or a constraint set?
3. is the status label earned or smuggled?
4. is "don't know" phrased admissibly or hidden under "probably"?

If any answer is no, rewrite.

## See also

- `SALIENCE_LOADER.md`
- `03_language_discipline.md` (verb list)
- `20_phrasebook.md` (clause-level rewrites)
- `17_pre_emit_audit.md`
