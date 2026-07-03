last_updated: 2026-04-17

# Grammar — Sentence-Level Patterns

Extended pre-trim version lives at `wiki/_archive/harness_2026-04-17_steward_trim/19_grammar.md`. This live page keeps the sentence contract compact.

## Canonical claim shape

> Under probe family `M` and constraint set `C`, candidate `X` survived / was excluded / remains indistinguishable from `Y`. Status: [exists | runs | passes local rerun | canonical by process]. Surviving alternatives: [...].

If a sentence will not reduce to this form, demote it.

## Sentence rules

1. **Subject** — use candidate / probe / constraint / quotient language, not bare objects.
2. **Predicate** — state what a probe returned, what constraints admitted or excluded, or what remained indistinguishable.
3. **Status** — cite the earned label and the supporting path; never compress the ladder.
4. **Quantifiers** — scope every universal or existential phrase to the active `M` and `C`.
5. **Uncertainty** — keep branch-open wording when exclusion is incomplete.

## Structural rewrites

- bare identity -> probe-relative indistinguishability
- bare property talk -> probe output or invariant across named probes
- forward reachability -> keep separate from backward admissibility
- impossibility -> use `UNSAT under C` only when the formal surface earned it
- present-tense certainty -> replace with dated runner / result evidence
- primitive geometry -> constraint-admitted geometry with cited probe/support surface (added 2026-06-03)
- primitive time -> named forward evolution relation with backward admissibility kept separate (added 2026-06-03)
- primitive probability -> constraint-compatible measure or admissible weight, not bare probability (added 2026-06-03)
- support-last bridge/operator/axis/manifold -> carrier/support/coexistence first, or blocked claim (added 2026-06-03)

## Geometry / time / probability / support templates (added 2026-06-03)

Use these when a sentence would otherwise smuggle geometry, time, probability, or support as primitive.

> Under constraint set `C` and probe family `M`, the constraint set admits geometry `G`; support evidence: `R`. No primitive geometry is claimed.

> Under forward evolution relation `E` constrained by `C`, candidate `X` is reachable from `A`; backward admissibility remains [open | excluded under R | admitted under R].

> Under constraint-compatible measure `mu_C`, the admissible weight of candidate set `S` is `P`; no primitive probability is claimed.

> Given carrier `K` and support relation `S`, operator / bridge / axis / manifold claim `X` is [exists | runs | passes local rerun | canonical by process]. Without `S`, `X` is blocked.

## Pre-emit checks

- probe family named?
- constraint frame named?
- status label cited correctly?
- surviving alternatives preserved?
- wording aligned with `03_language_discipline.md` and `20_phrasebook.md`?
- geometry/time/probability downstream of constraints, or explicitly support-level? (added 2026-06-03)
- carrier/support/coexistence named before operator/bridge/axis/manifold claim? (added 2026-06-03)

## See also

- `03_language_discipline.md`
- `04_status_label_hierarchy.md`
- `17_pre_emit_audit.md`
- `20_phrasebook.md`
- `35_support_first_preflight.md` (added 2026-06-03)
