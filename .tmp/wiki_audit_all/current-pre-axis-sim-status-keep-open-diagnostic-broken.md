---
title: Current Pre-Axis Sim Status Keep Open Diagnostic Broken
created: 2026-04-07
updated: 2026-04-08
type: summary
tags: [reference, research, simulation, status]
sources:
  - raw/articles/new-READ ONLY Reference Docs_old/CURRENT_PRE_AXIS_SIM_STATUS__KEEP_OPEN_DIAGNOSTIC_BROKEN.md
framing: current
---

# Current Pre-Axis Sim Status

## Overview
Full tier-by-tier status of pre-Axis simulations as of 2026-04-04. Source: system_v4/probes/a2_state/sim_results/*. Superseded by [[current-pre-axis-sim-status-wave1-refresh]] and [[current-preaxis-status-and-ordering-note]] for the latest snapshot.

## Tier Map
| Tier | Label | Description |
|---|---|---|
| 0 | Root constraints | Nonclassicality guards; what math is forbidden |
| 1 | Admissibility charter C | Rule set defining admissible structure |
| 2 | Admissible manifold M(C) | Geometry space consistent with charter C |
| 3 | Geometry/Operator basis | Operator selection, fiber/base grammar, load-bearing tests |
| 4 | Weyl working layer | Type1/Type2 engine Weyl chirality; CW/CCW handedness |
| 5 | Bridge family Xi | Xi/Xi_hist; causal bridge over engine sequence |
| 6 | Cut A|B / Entropy | VN entropy structure; entanglement object witnesses |
| 7 | Kernel Phi_0(rho_AB) | Coherent information kernel; entanglement identity |
| 8 | Edge writeback / Graph | STEP_SEQUENCE ring topology; edge constraints |

## Clean Passes
1. C2 Entropy Structure: PASS -- classical Shannon shortcut killed on 8/8 VN-positive stages; VN entropy is necessary
2. B3.2 Coord change preserves grammar: SymPy proof verified
3. B3.3 Noncomm ablation degrades grammar: [Ti,Fe]=0, [Ti,Fi]!=0 -- noncommutativity structurally necessary
4. B3.4 All 4 operators load-bearing: n=4, n_demotion=0
5. B3.1 Basis remap breaks grammar: gap_change_fraction=17.18, basis is non-arbitrary
6. C1 mispair characterization: operator-driven, not chirality-driven
7. Geometry crosscheck Type1: fully_matches=true
8. Kernel discriminator: K1_Ic (coherent information) wins 5/6
9. Hopf pointwise pullback: fiber loops density-stationary, base loops density-traversing

## Open Problems
1. In the 2026-04-04 snapshot this note records, tiers 0-2 were still open. Later passes added lower-tier transport/chirality probes and an admitted local tier-2 carrier, so treat this sentence as historical only.
2. Tier 3/4: Type2 Weyl inversion open. type2.fully_matches=false.
3. Tier 5 Bridge Xi: sims exist, not closed. Chiral wins composite (0.80), only family with I_c>0 everywhere. No winner selected.
4. Tier 6 C1 PARTIAL: MI-based negative controls not killed (0/16). Only concurrence/negativity kill fake coupling (16/16). Mispair: 8/16 killed.
5. Tier 7: Embargoed until Tiers 3-6 close.

## What This Does NOT Claim
Full pre-Axis ladder is NOT ratcheted. C1 PARTIAL is NOT collapsed to PASS. Type2 Weyl inversion NOT resolved. Bridge Xi NOT closed. Kernel discriminator does NOT unlock Tier 7.

## Related pages
- [[current-pre-axis-sim-status-wave1-refresh]]
- [[current-preaxis-status-and-ordering-note]]
- [[current-architecture-core]]
- [[constraint-on-distinguishability-full-math]]
