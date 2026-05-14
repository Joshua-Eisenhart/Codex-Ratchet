# Multi-Model Proposal Split

Status: working support doc
Scope: geometric-constraint-manifold and nested-tower exploration

## Boundary

`system_v5/grok_sim` is a separate informal experiment. It is not the formal sim
surface and not the source of truth for the current formal workstream.

Use it as:

- a proposal mine;
- a failure-pattern lab;
- a source of alternate constructions to audit;
- a way to make Grok/Gemini attack the gates from different angles.

Do not use it as:

- canonical evidence;
- a formal sim substrate;
- a source file copied into `system_v4/probes`;
- proof that a bridge, cycle, axis, or target-system claim has been admitted.

## Role Split

Grok and Gemini propose. Codex verifies.

Grok/Gemini should produce:

- divergent nested-geometry orders;
- alternate layer couplings;
- noncommutation and finitude observables;
- graveyard variants;
- failure attacks against the current tower;
- recipes that say which formal legos should be called.

Grok/Gemini should not:

- hardcode values that formal legos should compute;
- write into `system_v4/probes`;
- claim promotion;
- use nickname labels in executable identifiers;
- collapse open choices into doctrine.

Codex should:

- check proposals against repo docs and current receipts;
- verify callable imports from formal legos;
- reject hardcoded or decorative outputs;
- translate useful proposals into clean formal-scout harnesses;
- keep names literal and math-first;
- write receipts that fence claim ceilings.

## Required Proposal Fields

Every tower proposal must name:

1. nested layer order;
2. formal lego paths it would call;
3. callable names or explicit `NOT_YET_TESTED` if unknown;
4. observable;
5. pass/fail predicate;
6. graveyard variants;
7. finite-state or finite-truncation witness;
8. claim ceiling;
9. promotion blockers;
10. next smallest formal-scout harness.

Missing any field blocks translation into formal-scout code.

## Acceptance Rule

A proposal can enter formal-scout work only if it can be translated into code
that:

- lives outside `system_v4/probes`;
- imports or calls existing formal legos where available;
- returns explicit `lego_load_error` instead of substituting constants;
- carries `promotion_allowed: false`;
- writes a result receipt;
- includes immediate negative controls.

Formal promotion remains a separate later decision.
