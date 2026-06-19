# Owner doctrine — the Carnot/Szilard connection: same mechanics, different basis math and geometry (pre-registered 2026-06-12)

Owner (verbatim intent): "the carnot and szilard engines might be helpful to connect here. they
have lots of similar mechanics. just different basis math and geometry."

## The thesis

The Carnot and Szilard engines share MECHANICS — cycles built of typed strokes, per-stroke
ledgers (work/heat vs measurement/record/erasure), legality constraints (second-law fence vs
Landauer fence), and the ratchet pattern — while differing in BASIS: Carnot runs on thermodynamic
state geometry (isotherms/adiabats), Szilard on information geometry (record/syndrome structure).
"Connecting them HERE" = the current frontier carries the same mechanics on a third basis:

| shared mechanic | Carnot basis (committed) | Szilard basis (committed) | the basin/axis basis (the frontier) |
|---|---|---|---|
| the cycle | 4 strokes (the ledger v1 d79d71a0d) | measure-feedback-erase (same packet) | perturb -> relax -> return (the DoF rows f41d4c311) |
| per-stroke ledger | heat/work/entropy exact entries | record bits + erasure cost kTln2 | the typed-information ledger along the cycle (the entropy machinery) |
| the legality fence | super-Carnot UNSAT from the ledger | below-Landauer/unpaid-erasure UNSAT | THE BASIN-LANDAUER FLOOR (to be earned): relaxation that merges m states erases >= ln(m) |
| the two loop forms | deductive D = U∘E∘U∘E (the Carnot-like alternation) | inductive I = E∘U∘E∘U (the Szilard-like block) | alternating vs paired phases (the ring floor fe06d49bd); axis-4's Phi_D vs Phi_I |
| the legality axis | adiabatic-vs-isothermal stroke gating | measurement-before-feedback (N01) | axis 1 (bath-gating legality, per the work order) |

## Pre-registered expectations (falsifiable)
1. THE BASIN-CYCLE LEDGER: each committed RETURN DoF row supports a computed per-cycle typed
   ledger (perturbation cost in, dissipation out, record retained) whose conservation account
   closes under the z4 state-plus-record convention — a cycle whose ledger does not close = a
   finding.
2. THE BASIN-LANDAUER FLOOR: relaxation merging m perturbed states into one terminal orbit
   dissipates >= ln(m) (typed counting); a computed cycle beating the floor KILLS the connection
   (or exposes an unledgered record — adjudicated, not smoothed). The committed classical fences
   (e10273983 + d79d71a0d) bind as the legality anchors: no basin cycle may beat what the
   classical fence already excludes.
3. THE STRUCTURE MAP: an explicit stroke-to-stroke correspondence (Carnot ledger rows <-> basin
   cycle phases <-> Szilard ledger rows) that PRESERVES the mechanic columns while the basis
   columns differ — computed as a typed table, not asserted (the "same mechanics, different
   basis" claim made falsifiable: a mechanic with no basin counterpart is reported as the map's
   honest boundary).

Gate order: the blind panel pre-registers the floor arithmetic FIRST; the mapping mine grounds
the stroke correspondence in the committed rows; then ONE bounded packet
(carnot_szilard_basin_cycle_v0). Ceiling: doctrine registration; packets earn rows.

---

## Adjudication entry — v0 (2026-06-12, audit GENUINE-WITH-CAVEATS)

`carnot_szilard_basin_cycle_v0` EARNS all three pre-registered expectations at scratch strength:
the per-cycle typed ledger closes (defect 0 under a packet-local state-plus-record table), THE
BASIN-LANDAUER FLOOR holds with m earned from the actual trajectory/graph structure (ln 9 sampled
/ ln 33 full-carrier, matching panel 7's blind arithmetic exactly), the Szilard honesty clause is
a live computed gate (reset charges ln m; the less-than-floor falsifier flips), and the
stroke-to-stroke structure map is emitted with the six honest boundaries carried. The owner's
"same mechanics, different basis math and geometry" now has its first computed witness on the
basin basis. Open per the map's boundaries: heat/work variables, bath-gating, and any physics
reading — the connection is typed-counting mechanics, earned exactly that far.
