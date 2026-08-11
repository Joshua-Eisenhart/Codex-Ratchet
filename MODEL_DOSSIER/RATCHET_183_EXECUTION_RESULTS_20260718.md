# Execution results

## Active Pack 183 lane

- source packets: 7 base packets and 2 nested-evolution packets;
- base candidates: 16;
- base simulations: 112 candidate-packet evaluations;
- base frontier: 2;
- nesting candidates: 22 complete base/nesting combinations;
- nesting frontier: 4;
- whole feedback candidates: 528;
- whole shared simulation kernels: 33;
- whole frontier: 6;
- whole recomputations: 5, including revision, restoration, and idle continuation;
- semantic verification checks: 53 passing;
- adversarial mutations: 22 of 22 rejected;
- deterministic full replays: 2 of 2 exact.

Active result digests:

| Result | Digest |
|---|---|
| source packets | `sha256:897fa962039529d76f6dba8bdafc76d6f937213ea40f40b7fe99d7618b55d704` |
| base census | `sha256:c30696abc401297bfe099f2463938f42c45ab848dfc769832aa2e0dcdf577e80` |
| nesting Ratchet | `sha256:389d759c534fec8586328b6d982397c9cf7848e112ab736d7abec66822ba4bac` |
| whole feedback Ratchet | `sha256:3354b9735bd7573406703419d5f0f2cbe1a2343953d5f969507bdba74e1abae1` |
| semantic verification | `sha256:7f6ea256d9f2713a68dccac19bef39e860295a213a409570f3d6750392060219` |
| deterministic replay | `sha256:23c0030a6f44163c20889cfcfb9afa24cd83158c5ca81ed570a86fb0b9aadc0c` |

## Preserved Pack 182 regression

The complete inherited lane ran successfully:

- six source evidence events;
- optional historical simulation outcomes: one pass and one honest
  `SKIP_OPTIONAL` because Z3 is unavailable;
- 18-requirement finite whole-manifold probe;
- 51-candidate, 24-recomputation whole-manifold campaign;
- four order schedules and a two-candidate meta-frontier;
- 18 adversarial controls;
- seven deterministic replay lanes;
- eight older inherited-regression markers.

This environment has Python and NumPy.  It does not have Julia, JAX, PyTorch,
Z3, or cvc5.  No unavailable lane is reported as freshly passing.
