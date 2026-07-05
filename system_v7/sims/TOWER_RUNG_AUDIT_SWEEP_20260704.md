# Fresh-context audit sweep — tower rungs built 2026-07-04

| rung | verdict | strongest defect |
|---|---|---|
| G5 density floor | GENUINE-W-CAVEATS | closure-demand/expressibility facts asserted not tested; z3/cvc5 control is toy constants; shuffle is invariance not kill |
| G6/G7 spinor-Hopf | GENUINE-W-CAVEATS | Hopf side: closed=measured self-plant, horizontal residual hardcoded 0.0; flat-S2 kill weak |
| G8 two sheets | BY-CONSTRUCTION | expected = same formula path as measurement; all four controls hardcoded true (jax.py:55-58, pytorch.py:33, julia.jl:44-47) |
| G10 terrain flows | BY-CONSTRUCTION | torch/julia legs rerun JAX and rewrite the manifest; label-shuffle control is sorted(x)==sorted(x) tautology |

Chain-run admission at scratch ceiling: G5 + G6/G7 ONLY (caveats carried). G8 and G10 EXCLUDED from chain evidence — known-bad diagnostic fixtures until repaired. Repairs pre-registered: G8 — expected orientation from an independent path (trajectory integration vs separately-computed analytic prediction), controls computed; G10 — native julia/torch reimplementations, computed relabel/shuffle kills. Prior commit messages for G8 (507a65ea1) and G10 (c0b9390b5) OVERSTATE control status; this receipt supersedes their prose.

## Round 2 (same day): G0 + the two repairs

| rung | verdict | strongest defect |
|---|---|---|
| G8 (repaired) | GENUINE-W-CAVEATS — chain-admissible | relabel subcontrol recomputes sheet(1.0) instead of transforming the measured right sheet (jax.py:70) |
| G10 (repaired) | GENUINE-W-CAVEATS — chain-admissible | fixture-authored terrain pairing; stale wrapper text in envelope (check_agreement.py:59) |
| G0 (new) | BY-CONSTRUCTION — NOT chain-admissible | z3 unsat is toy n>=0 && n<0 unbound to the family; julia hardcodes UNSAT; envelope claims cvc5 with no code path; TYPED_REFUSAL emitted as data, never exercised |

G0 repair pre-registered: unsat must bind to the CONSTRUCTED carrier (e.g. pigeonhole: injective map from a (k+1)-index set into the size-k carrier, k computed from the run); refusal branch exercised live (constructor called with the unbounded spec, typed refusal object caught); julia calls a real solver or honestly records none; envelope claims only what ran. Commit a9c2346af's prose overstates; this receipt supersedes it.
