# BUILD CARD: twistor_incidence_finite_packet_v0 — finite projective spinor-incidence discriminator (alt-math lane)

One object, one claim, one card. CLAIM UNDER TEST: a finite twistor-style incidence geometry over F_2 — points and lines of PG(3,2) with the twistor dictionary (projective equivalence quotient, point<->line incidence, intersecting-line relation as the null-relation candidate) — yields at least one computed relation/readout that (a) survives its negative controls and (b) SEPARATES from the committed spinor/Hopf baseline (the mct packet's probe/quotient behavior on the same-size sample). Kill condition: no readout separates from baseline/controls -> the packet records the kill honestly and the candidate is parked.

HARD FENCES: never "twistors = the manifold"; no spacetime/GR/physics claim; no Penrose-validates language; alt math = discriminator packet, not canon. Ceiling: classification="scratch_diagnostic", promotion_allowed=false, formal_admission_allowed=false.

## Read first (binding)
1. system_v6/receipts/twistor_incidence_mine_20260610.md — THE SPEC (finitization translation §B-C, packet shape §D, fences)
2. system_v6/sims/pg32_sedenion_incidence/ — the committed PG(3,2) incidence precedent: reuse its construction pattern for points/lines/incidence tables (cite; adapt, don't blind-copy)
3. system_v6/sims/mct_dynamic_admissibility_packet_v0/ — the spinor/Hopf BASELINE (committed quotient/probe behavior; cite pin lineage)
4. system_v6/README.md engine-mode rule (:11) — this is a DIAGNOSTIC, not a claim-bearing spine rung

## PIN block (frozen; identical across legs)
- q=2 pinned: PG(3,2) = nonzero vectors of F_2^4 modulo nonzero scalars (trivial for q=2 but the quotient map is still computed explicitly, not skipped) -> 15 points, 35 lines (2D subspaces as member sets), 7 lines through each point — all three counts emitted as computed checks.
- twistor dictionary rows (from mine receipt §C): "event candidate" = projective line; alpha-star row = the 7-line pencil through a point; null-relation candidate = the line-intersection graph (35 vertices; two lines adjacent iff they meet in a point).
- probe families: P_proj (projective class id, computed from the scalar quotient), P_inc (incidence membership rows point x line), P_null (intersection-graph adjacency rows), P_pencil (pencil size/structure per point), P_chir (a pinned orientation/chirality row — PINNED-CHOICE with source note: e.g. a fixed symplectic/dual pairing sign), P_recon (reconstruction-from-incidence: recover the point set from line membership data alone).
- baseline comparison: a pinned 15-element and 35-element sample of the committed mct carrier rows with ITS committed probe families, same readout shapes (quotient class counts, relation-graph components, reconstruction behavior) — like-for-like named scalars only.
- engine mode DECLARED: mode="julia_canon_plus_jax_diagnostic" (README :11 — diagnostics may run Julia + one consumer); PyTorch omitted BY DECLARED MODE, not silently.

## Build gates
G1. PG(3,2) computed from scratch: 15/35/7 counts emitted as computed (not literals); incidence table full.
G2. The intersection-graph (null-relation candidate) computed with named graph invariants (degree sequence, components, clique structure); scramble-incidence control must change them.
G3. Reconstruction-from-incidence: recover all 15 points from line-membership data alone; mismatch count emitted; the random-bipartite-graph control must FAIL reconstruction or produce non-isomorphic invariants.
G4. Projective-quotient ablation: dropping the scalar quotient must change the named readouts (even at q=2, the map identity/structure is checked — if at q=2 ablation changes nothing, REPORT that honestly as a q=2 limitation, flagging q=3 as the discriminating case; do not fake a flip).
G5. SEPARATION TABLE: per readout (quotient classes, relation components, pencil structure, reconstruction behavior), the twistor object's value vs the spinor/Hopf baseline's value — separation = a named computed difference no control reproduces. If NO row separates, emit kill_condition_met=true and say so in the summary.
G6. Load-bearing proof (z3 AND cvc5): derive an incidence-structure fact from the computed tables (e.g. UNSAT that any two distinct lines meet in >= 2 points / the 7-pencil regularity), with a scrambled-incidence control flipping to SAT. Hardcoded literals = failure.
G7. Chirality row: computed from the pinned pairing, must flip under the orientation-reversal control and survive label shuffle.

## Controls
scramble-incidence, random bipartite graph (same degree profile), drop-projective-quotient, orientation reversal, label shuffle, baseline like-for-like comparison rows.

## Files to create (one folder, atomic)
system_v6/sims/twistor_incidence_finite_packet_v0/
  twistor_incidence_finite_packet_v0_julia.jl / _jax.py / _envelope.py
  build_card.md (verbatim copy)
  results/*.json
No pytorch leg (declared mode). No audit_verdict.md. No edits to existing files.

## Acceptance (re-run mechanically)
Legs exit 0 fresh; envelope validates with scripts/validate_three_engine_sim_result.py WITHOUT --require-pytorch if the envelope schema permits declared two-engine mode — if the validator requires three legs, emit the envelope with mode-declaration fields and record the validator outcome honestly (a schema mismatch is reported, not worked around); PIN identical across legs; G1-G7 receipt fields present; controls fired; separation table or kill condition emitted; ceiling exact.
