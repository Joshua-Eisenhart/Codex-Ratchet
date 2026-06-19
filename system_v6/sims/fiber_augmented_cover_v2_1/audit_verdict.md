# Independent audit verdict - fiber_augmented_cover_v2_1

Bottom line: `fiber_augmented_cover_v2_1` is `GENUINE-WITH-CAVEATS`, not strict green. The decisive re-pin is honest as a new pinned construction: seam steps `[1,0,0,0]` recompute to integer lift `1` and mod-3 holonomy `1`, while the old v2 regression row preserves integer lift `3`, old winding `1`, and finite mod-3 holonomy `0`. The blocking caveat is the guard-v3 control family: the packet stores four different `chain_sha256` values, but only two pure boundary-matrix chain complexes exist after metadata is stripped.

Verdict: `GENUINE-WITH-CAVEATS`.

Claim ceiling: `scratch_diagnostic`; `claim_ceiling=axis_readout_candidate_only + decisive_repair_cover_no_admission`; `promotion_allowed=false`; `formal_admission_allowed=false`; no Betti computation, homology certificate, lens-space certificate, SECOND certificate, formal admission, canonical-process claim, bridge, physics, manifold, axis closure, or global b6 disproof is earned.

Freshness tier: `TIER-3 annotation-verify`. The prompt exposed the builder claims, guard-v2 verdict, and decisive teeth. I recomputed the load-bearing rows from source/result artifacts in this turn.

Read/write boundary: read-only audit except this file. I did not run result writers, validator `main()`, `git add`, commit, or any command expected to rewrite packet result JSON.

## What Was Checked

Authority and repair contract:

- `system_v6/receipts/audit_standards_codex_v1.md`, especially G.2a.
- `system_v6/sims/topology_parity_guard_v2/audit_verdict.md` at the `2137ae3e8` repair contract.
- `system_v6/receipts/axis_work_order_20260612.md`, section `b6 CARRIER STATUS UPDATE 3`.
- `system_v6/sims/fiber_augmented_cover_v2_1/build_card.md`.

Packet surfaces:

- `system_v6/sims/fiber_augmented_cover_v2_1/fiber_augmented_cover_v2_1_common.py`.
- `system_v6/sims/fiber_augmented_cover_v2_1/fiber_augmented_cover_v2_1_boundary.py`.
- `system_v6/sims/fiber_augmented_cover_v2_1/validate_fiber_augmented_cover_v2_1.py`.
- `system_v6/sims/fiber_augmented_cover_v2_1/tests/test_fiber_augmented_cover_v2_1.py`.
- `system_v6/sims/fiber_augmented_cover_v2_1/results/fiber_augmented_cover_v2_1_results.json`.
- `system_v6/sims/fiber_augmented_cover_v2_1/results/fiber_augmented_cover_v2_1_envelope_results.json`.

## Re-Pin Honesty

The in-card framing passes. The build card states that v2.1 is a different pinned construction, not a reinterpretation of old v1/v2. The result carries the same boundary in `central_math_adjudication.not_a_reinterpretation_of_old_construction=true`.

The old facts are preserved rather than erased. The old-v2 regression row records:

| row | value |
|---|---:|
| old seam steps | `[1,1,1,0]` |
| integer lift sum | `3` |
| old integer lift winding | `1` |
| mod-3 holonomy | `0` |
| finite witness gate | `false` |

That reproduces the old finite triviality as data. It does not relabel the old construction as finite-nontrivial.

The v2 base lock also passes. The rebuilt base hash and live result hash both equal:

```text
9d6655a51782305f80409cce0bd42a57329fb14ea19b05c32b95ec36016b883c
```

with counts `C0=33`, `C1=92`, `C2=61`, and `chi=2`.

## Generator Gate

The source gate is the right gate. `holonomy_witness(...)` computes the integer sum of the seam steps and then `mod_fiber_holonomy = integer_sum % 3`; the positive finite witness passes only when `mod_holonomy == 1`.

Fresh recompute from the emitted rows:

| complex | seam steps | integer lift | mod-3 holonomy | generator gate |
|---|---:|---:|---:|---|
| `v2_1_shifted_degree_one_mod3` | `[1,0,0,0]` | `1` | `1` | pass |
| `zero_shift_product_control` | `[0,0,0,0]` | `0` | `0` | refuse |
| `wrong_gluing_generator_not_threaded_control` | `[1,0,0,0]` | `1` | `1` | seam generator present, threading refused |
| `old_v2_regression_coboundary_control` | `[1,1,1,0]` | `3` | `0` | refuse |

The cover transition rows also contain the re-pin. Because the v2 base edge orientation is reverse on the first seam leg, the single nonzero transition row appears as `17 -> 20` with shift `2`, which is the reverse of seam step `20 -> 17` with shift `1 mod 3`.

## Control-Family Separability

This is the caveat that blocks strict green.

The stored packet hashes make four rows look distinct:

| complex | stored `chain_sha256` | pure boundary class |
|---|---|---|
| `v2_1_shifted_degree_one_mod3` | `6afe8ea8f778ae9f470354a641a8989e40868df5efa8c9792fcdd2eb25c3c75a` | `d2=[3]` |
| `zero_shift_product_control` | `5315bd250363ab44ed209f9102f9f00f8a7aad72105fdb95452d9b1a5ae5bd76` | zero boundaries |
| `wrong_gluing_generator_not_threaded_control` | `856ae6b070b7227dfff272c7e587f08d63cf06563d0a8394084baef782f64b8d` | zero boundaries |
| `old_v2_regression_coboundary_control` | `151c47084f246e24665e80728a6c5492fdbe7feaecd96cbcdb6e94242b68d0d5` | zero boundaries |

But after stripping metadata and hashing only `cell_counts + boundary_matrices`, there are only two chain-complex classes:

```text
cc2a97848fc8a16853f159d11834e7ac3520a29cf7521b684681c76d80ba1205
  v2_1_shifted_degree_one_mod3

ccf0ea0f5bd81550e12ea7f8a0e64cecc4815bf2c972c40b7b34e7c861270ece
  zero_shift_product_control
  wrong_gluing_generator_not_threaded_control
  old_v2_regression_coboundary_control
```

So the builder's "four hash-pinned complexes" statement is true only when metadata is included in the hash. It is false as a statement about four genuinely different chain complexes. This matters because the guard-v2 trap was exactly "looks different, still not structurally separated enough."

The positive shifted complex is not chain-isomorphic to the zero-shift complex by the old phase-potential problem. In this emitted 1x1 integer complex, chain isomorphisms over `Z` can only multiply chain groups by units `+1` or `-1`; `d2=[3]` cannot be isomorphic to `d2=[0]`. So the positive re-pin escapes the old shifted-vs-zero product-equivalence defect.

The control side is weaker: zero-shift, wrong-gluing, and old-v2 regression are pairwise isomorphic as pure chain complexes. They differ by witness/control metadata, not by boundary maps.

## Law Row

Fresh source rebuild of the v2.1 law row returns:

| row | value |
|---|---:|
| agreement count | `46` |
| violation count | `53` |
| sample total | `99` |
| agreement fraction | `0.4646464646` |
| two-sided binomial p | `0.5467134836` |
| chance class | `at_chance` |

This is the same `46/99` at-chance row as the earlier two constructions. That is expected rather than suspicious: the law table is over the same 99 cover states and pinned axis realizations, while the law itself lives below the fiber-chain structure being re-pinned. The third replication is still data, not promotion evidence.

The faithfulness obligations recompute green for this v2.1 cover:

- Axis0 projects to committed Axis0 with mismatch count `0`.
- Axis3 is recomputed natively from the finite fiber predicates with predicate mismatch count `0`.
- Axis6 projects to committed Axis6 with mismatch count `0`.
- SMT rows keep `verdict=unsat` and `erased_flip_verdict=sat` for both solvers.

## Contract Checks

No-write packet validator call:

```text
validate_payload_errors=[]
rebuilt base hash match=true
rebuilt complex chain hashes match=true
rebuilt complex boundary hashes match=true
rebuilt relation sign vector hash match=true
live all_pass=true
```

No-write pytest:

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/fiber_augmented_cover_v2_1/tests
4 passed in 4.01s
```

No Betti/consumer fence:

- Top-level `betti_computed=false`.
- Top-level `homology_computed=false`.
- Recursive key scan found no key named `betti`.
- The result says guard v3 is the intended consumer and blocks Betti/homology/topology citations from this builder packet.

G.2a:

- Build card names G.2a from birth.
- Validator and boundary delegate audit-file handling through `scripts/builder_audit_boundary.py`.
- The result carries `no_builder_audit_verdict=true` and `no_builder_audit_verdict_envelope_gate=true`.
- This file has an independent/fresh/read-only audit header, so post-audit idempotency remains satisfiable.

Generic three-engine validator note:

```text
scripts/validate_three_engine_sim_result.py ..._envelope_results.json
-> schema_version must be three_engine_sim_result_v1
```

I do not use that as a failure for this packet, because the packet explicitly declares `engine_contract.mode=single_python_finite_clutching_chain_packet` and `three_engine_scoped=false`. The relevant check is the packet-local validator plus source-level recomputation above.

Current repo status observation:

```text
?? system_v6/sims/fiber_augmented_cover_v2_1/
```

So this audit reviewed the current working-tree packet; it did not verify an already committed v2.1 packet.

## Guard-V3 Handoff

Guard v3 must pre-register the homology/torsion expectations before computing:

| guard-v3 input | pre-registered expectation |
|---|---|
| `v2_1_shifted_degree_one_mod3` | Betti `[1,0,0,1]` plus `H1=Z/3` |
| `zero_shift_product_control` | Betti `[1,1,1,1]`, no torsion |
| `wrong_gluing_generator_not_threaded_control` | product/no-threading negative control; Betti `[1,1,1,1]`, no torsion, unless a future repair makes its boundary map structurally distinct |
| `old_v2_regression_coboundary_control` | old finite-trivial regression; Betti `[1,1,1,1]`, no torsion |

Guard v3 should also include a separability check that hashes only the mathematical chain complex, not metadata. Without that, it can mistake metadata-different controls for distinct chain-complex controls.

## Citation Rule

Future citations should say:

> `fiber_augmented_cover_v2_1` is a scratch-diagnostic decisive re-pin, not a reinterpretation of v2. The new seam `[1,0,0,0]` recomputes to integer lift `1` and mod-3 holonomy `1`; the old v2 regression row preserves integer lift `3`, old winding `1`, and finite holonomy `0`. The v2 base hash remains `9d6655a5...`, the law row recomputes `46/99`, `p=0.5467`, `at_chance`, and the packet keeps the consumer fence with no Betti in-packet. Caveat: it is not strict green as guard-v3 prep because the four stored `chain_sha256` rows collapse to only two pure boundary-matrix chain complexes: shifted `d2=[3]` and three zero-boundary controls. The shifted complex is not chain-isomorphic to zero shift, but the zero-shift, wrong-gluing, and old-v2 controls are mutually isomorphic as chain complexes. Ceiling: `scratch_diagnostic`; no Betti, homology, lens-space, SECOND, formal-admission, bridge, physics, manifold, axis-closure, or global b6 claim.
