# Maude rewrite card v0 — frozen bracket/history semantics (2026-07-13)

Status: the card the wiki demands before Maude counts as wired ("needs a frozen bracket/history rewrite card").
Maude 1.6 installed in sim-stack 2026-07-13; T01 flip probe green (stress_battery receipt).

## Object (frozen)
Finite terms over sort Elt with one binary op `_*_` and generators a,b,c,d. Histories = ground terms
(bracketing preserved). No numbers, no probability, no carrier. Labels are bookkeeping.

## Rewrite semantics (frozen)
- Mode N (bare): `op _*_ : Elt Elt -> Elt .` — bracketings and orders are DISTINCT normal forms.
- Mode A (assoc): attribute `[assoc]` — bracketings identified, order preserved (N01 still visible).
- Mode AC: `[assoc comm]` — order also identified (the erased-everything control).

## Claims this card licenses (each z3/cvc5 cross-checkable on exported finite term sets)
1. T01 witness: a term pair distinct in N, identified in A. (Demonstrated: probe maude_t01_bracketing_flip.)
2. N01 witness: a term pair distinct in A, identified in AC.
3. History rewriting: a rule set R rewrites histories; `search` enumerates reachable normal forms =
   the finite basin of a term under R. Recurrence via search to =>! (terminal) states.

## Controls (must fire)
- Axiom-toggle flip: every claim must reverse under the corresponding axiom change (N<->A<->AC).
- Relabel: permuting generator names commutes with rewriting.
- Empty-rule control: with R empty, every term is its own terminal state.

## Acceptance
One sim: exports the finite term set + normal-form partition per mode as JSON; z3 AND cvc5 certify the
partition refinement N > A > AC (strict, with witness pairs); erased control flips. Runs via sim-stack
python maude bindings. Ceiling: tool-integration probe, promotion_allowed=false, admits nothing.

## Out of scope
Cosmogenesis claims, carrier claims, CA competition, any physical N01/T01 admission. Order/bracket
sensitivity here is fixture-relative to this term grammar.
