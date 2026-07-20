# Spinor-JEPA tournament v0 — scorer verdict

Fresh-context scorer, card applied as frozen law, no threshold edits. Full data: `verdict.json`.

## Budget compliance
All 7 lanes meet 16-DOF / <=60000-param / <=300-step. No disqualifications.
Flags recorded, not disqualifying: lane4 memory-gate breach (23.8% free vs
25% threshold, proceeded anyway); lane5 admits a self-authored ARI gate
would fail; lane6 lacks the occluded-accuracy shuffled-id control every
other lane reports; lane7 self-reports `all_pass:false` (G_occ_acc, G_ari).

## Tournament table (full per-probe scores in `verdict.json.tournament_table`)
| lane | P5 occ-acc | P6 binding | Holevo>null | ARI>null | params |
|---|---|---|---|---|---|
| 1 vector scout (control) | 0.520 | 0.538 | no | no | 1432 |
| 2 vector JEPA | 0.549 | 0.531 | no | no | 13304 |
| 3 projective ray | 0.632 | 0.014 | no | no | 18312 |
| 4 quaternion | 0.538 | **0.338 (neg)** | thin yes | no | 13436 |
| 5 multivector (control) | 0.560 | 0.538 | yes | thin/self-fail | 35264 |
| 6 spinor ideal | 0.570 | 0.141 | thin yes | thin yes | 3232 |
| 7 purified density | 0.588 | **0.0 (neg)** | yes | no | 880 |

## Frozen falsifier applied exactly as written
"Vector or quaternion + cheap sign/phase register passes all P1–P10 more
economically" — **not triggered**. Lane 2 (vector) cannot even define P1
and fails its own Holevo null. Lane 4 (quaternion) fails P6, an
amendment-primary probe: the learned rotor transport is ray-*worse* than
doing nothing (0.338 < 0.5). Neither passes everything.

"Spinor carrier wins across ALL probes" — **also not triggered**. Lane 6
combines a real P1 interference witness, positive P6 binding, and
simultaneous above-null Holevo+ARI — the best all-around balance, cheapest
budget among structured carriers — but every margin is thin and P5 lacks a
shuffled-id control. Lane 7 has the richest charge set and the tournament's
only formally proved (z3 UNSAT) order witness, but self-fails two of its
own gates and shows a decorative-dynamics honest negative on P6.

## Verdict
**Spinor status: OPEN — neither earned nor killed by this run.**
Retained frontier, not collapsed: lane3 (best raw accuracy, shallow
binding), lane5 (best non-spinor Holevo margin, engineering control per
card, zero attractor formation), lane6 (best balance, cheapest, thin
margins), lane7 (richest structure + only proof-grade witness, self-failing
gates). Every lane keeps `promotion_allowed: false` regardless.

**Clearest single kill witness**: lane4 (quaternion) on P6 — the exact
carrier the falsifier names, failing the probe that would need to pass for
spinors to be disqualified. Not a full-lane kill; lane4 clears budget and
shows a genuine, task-decoupled P1 lift-capacity witness.
