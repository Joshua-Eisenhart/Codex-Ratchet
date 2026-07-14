# Final report — finite-roster deep-stack stress

Ladder: **L0** absent or not executed · **L1** installed but unused · **L2** probed · **L3** operational chain receipt · **L4** verdict-bearing operational evidence.

| # | Item | What it is | State | Level | Receipt | Skill |
|---:|---|---|---|---|---|---|
| 1 | Finite roster | The current bounded system roster, not every repository surface | **GREEN:** 139/139 classified; 95 operational rows green (86 current-required + 9 legacy/unclassified); 44 policy-only rows green | L3 | `deep_stack_estate_lev.json` | `codex-ratchet-deep-stack-stress` |
| 2 | Function-level tool stress | Real APIs with positive, negative, boundary, stress, and demotion cases | **GREEN:** 95/95 deep-stress tools; exact raw case/call/demotion hashes; no import-only credit | L3 | `deep_stack_estate_lev.json` + `deep_stack_estate_lev_verdict.json` | parent + runtime family routes |
| 3 | Raw producer chain | Seven fresh run-scoped producer roles with output clearing, source, command, path, and hash binding | **GREEN:** 7/7 roles; no raw reuse; 52/52 recorded commands exit zero without timeout | L3 | `results/raw/deep-stack-lev-856acb1a5/` | `codex-ratchet-deep-stack-stress` |
| 4 | Representative consumers | Existing and new representative sims/controllers bound to exact output contracts and structured package identity | **GREEN:** 86 execution receipts cover 95 tools through 48 unique sources (42 disposable projections + 6 direct/controller sources) | L3 | representative section of `deep_stack_estate_lev.json` | `jax-sim`, `pytorch-sim`, `julia-sim`, `three-engine-sim` |
| 5 | Adjacency witnesses | Neighbor co-health, independent cross-checks, and one direct value handoff; these are not all integrations | **GREEN:** 25 member co-health compatibility witnesses + 3 independent shared cross-checks + 1 direct value handoff | L3 | edge section of `deep_stack_estate_lev.json` | family routes in parent skill |
| 6 | Nested skill layer | One parent plus five runtime/maintenance skills across repo, Codex home, and second Codex home | **GREEN:** 6 skills × 3 homes; 18/18 structural validations; 6/6 parent-script syntax checks; installed overlays preserved | L2 | `skill_home_reconciliation.json` | six named skills |
| 7 | Lev OS execution seam | Pinned, non-model Lev executor runs the real parent, validator, exact-coverage gate, and a deliberately empty twin | **GREEN:** 9/9 cases behave as specified; main suite passes; zero-execution twin blocks on `suite.execution.none`; release remains false | L4 | Lev run and scorecards under `results/lev_eval_runs/` and `results/lev_zero_runs/` | `lev` + parent skill |
| 8 | Runtime shakedown | Independent environment and compatibility check outside the main estate | **GREEN:** 29 pass, 0 fail, 0 warning-status checks, 3 explicit skips (Julia↔Python DLPack and two Claude reference-only surfaces); the mapping audit retains 62 non-blocking historical warnings, and installer-process scanning was unavailable because `ps` was denied | L2 | `codex_runtime_capability_shakedown_results.json` | `sim-stack-maintenance` |
| 9 | QIT/Ratchet engine state | Design target and proposed next experiment, separate from the tool estate | **NOT EXECUTED / NOT PROVEN:** pack says `proposed_not_executed` and `current_derivation: not_earned`; supplied sources disagree on the terrain cycle; no pinned push-button Ratchet runtime exists | L0 | `qit_pack_intake_boundary_20260714.json` | future three-engine science rung, not this campaign |
| 10 | Grok 4.5 cross-check | Bounded external critique of the compact final evidence, advisory only | **SERIOUS ADVISORY, NO NEW OPERATIONAL BLOCKER:** it correctly tightened adjacency/replay language; it could not inspect the full estate and incorrectly equated Lev `projection_only` with zero execution | — | `grok45_final_advisory.json` | none |

The implementation source is commit `576229471147f038696b1e6c109be31ce28aa9d1`, tree `c249f58d144f49bfc73150e4bfc84539723ee904`. Lev is pinned to commit `856acb1a5de42528a9a54272435d98a9fe226186`, tree `3f3488781d48a64b22c43c08ccfaa2b503d49524`, binary SHA-256 `f258ae313d515cae4ff848a45df78cfcc6a2d48c9ce1ade9c316276b00ef0c61`.

The independent validator replay is byte-identical to Lev's saved verdict (`74a12fef90ea86ac80bb1389995bdf7281a7de2d3615a38d0b007d121845fb8f`): `receipt_valid=true`, `operational_pass=true`, zero findings. The focused validator suite is 19/19 green, including its 14/14 internal fail-closed mutation selftest. The replay command, pinned inputs, hashes, exit code, and comparison are recorded in `independent_validator_replay_20260714.json`.

Here, L4 means verdict-bearing operational evidence in this report's ladder. Lev's `projection_only=true` is the explicit no-release/no-promotion boundary; it does not mean zero execution—the main scorecard records nine executed cases, while the separate empty twin records zero and blocks.

Claim ceiling: this is L3 operational tool/library chain evidence plus explicitly typed adjacency witnesses, with an L4 Lev verdict over that bounded evidence. It does **not** establish release eligibility, a complete Ratchet, a QIT engine, the terrain schedule, exceptional-math flux, cosmogenesis, or any scientific result.

## Where to go

1. Make this pinned no-install harness the regression gate for changes to the finite roster, runtimes, representative sims, or nested skills.
2. Resolve the terrain-cycle authority conflict before coding the pack's `octonionic_left_right_nested_flux_rung_001`; then execute the preregistered Julia/JAX/PyTorch lanes with z3/cvc5 gates and no NumPy on the claim-bearing path.
3. Specify the missing pinned Ratchet runtime manifest and execution/adjudication semantics before calling the estate one push-button Ratchet.
