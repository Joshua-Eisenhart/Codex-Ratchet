# Audit verdict - stage_lifted_spinor_shell_n4_v0

Fresh audit date: 2026-06-10.

Scope: read-only audit of `system_v6/sims/stage_lifted_spinor_shell_n4_v0/`, except this `audit_verdict.md`.

Verdict: **GENUINE-WITH-CAVEATS**.

Ceiling remains: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. Do not use this packet as stage closure, canonical geometry, bridge/axis admission, physics, formal admission, completed constraint manifold, or ladder-trend evidence.

## Inputs and standard

Inputs read:

- Sim folder: `system_v6/sims/stage_lifted_spinor_shell_n4_v0/`
- Calibrated bar: `system_v6/receipts/audit_bar_calibration_20260610.md`
- Template: committed `system_v6/sims/stage_lifted_spinor_shell_n3_v0/audit_verdict.md`, including the hardening addendum.

Binding calibration: exactness-class stability replaces blanket byte-stability; blind-method mismatch is a finding to reconcile, not an automatic fail; strength tokens are never verdict-bearing; two-CAS proof is preferred, not required.

Fresh checks run:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/stage_lifted_spinor_shell_n4_v0/results/stage_lifted_spinor_shell_n4_v0_envelope_results.json
```

Result: `{"ok": true}`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n4_v0/stage_lifted_spinor_shell_n4_v0_jax.py
```

Result: no violations.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n4_v0/stage_lifted_spinor_shell_n4_v0_pytorch.py
```

Result: no violations.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n4_v0/stage_lifted_spinor_shell_n4_v0_julia.jl
```

Result: no violations.

## Q1 - lift genuine

Status: **PASS-WITH-CAVEAT**.

This is a real four-site support construction, not a label join. The builder records "4 nodes, 5 tensor/path edges, and 2 filled shell faces" (`build_card.md:30`). The JAX source constructs site rows with `eta`, `theta`, `loop_phase`, `z`, `psi_L`, and `psi_R` (`stage_lifted_spinor_shell_n4_v0_jax.py:225-243`), then builds nodes, edges, faces, TopoNetX/GUDHI topology, rustworkx connectivity, and XGI hyperedges (`stage_lifted_spinor_shell_n4_v0_jax.py:293-349`).

The lifted rows consume shell coordinates where the claim requires them. The S5/S6 lineage row substitutes each site's `eta` and `theta` into exported S5 `A,b` fields and emits `z_dot_from_exported_A_b`, `purity_derivative_from_exported_A_b`, and `s6_class` per site (`stage_lifted_spinor_shell_n4_v0_jax.py:352-406`). The shell leakage row computes `z=cos(2 eta)`, per-site leakage, aggregate leakage, wrong-shell controls, and hardcoded-zero controls (`stage_lifted_spinor_shell_n4_v0_jax.py:664-712`).

Caveat: the GHZ/W density and entropy rows are standard carrier-state rows placed on the shell-supported carrier, not coordinate-parameterized GHZ/W state families. The entropy row labels this as `density_only_value_with_shell_placement_receipt` (`stage_lifted_spinor_shell_n4_v0_jax.py:461`). That limits the lift claim to real support placement plus lifted support/leakage/path rows.

## Q2 - exact anchors

Status: **PASS**.

Hand recomputation:

```text
ln(2) = 0.6931471805599453
W4 single-site entropy
  = -(3/4)ln(3/4) - (1/4)ln(1/4)
  = 0.5623351446188083
d = 16, d^2 = 256
```

The packet computes GHZ/W entropy with `qutip.ptrace` and `qutip.entropy_vn` (`stage_lifted_spinor_shell_n4_v0_jax.py:432-480`). The result reports `GHZ_4_ln2_all_bipartitions=true`, `W_4_single_site_entropy=0.562335144619`, and `W_4_expected=0.562335144619` at JSON path `rows.P5_entropy.computed_anchors`.

The IC frame constructs 16 diagonal effects plus symmetric/antisymmetric off-diagonal effects, stacks vectorized effects, and checks matrix rank (`stage_lifted_spinor_shell_n4_v0_jax.py:484-512`). The result reports `d=16`, `effect_count=256`, `expected_d_squared=256`, `frame_rank=256`, and `pass=true` at JSON path `rows.P3_density_quotient.ic_povm_separation`.

## Q3 - nesting law

Status: **PASS**.

GHZ non-nesting is computed, not asserted. The source traces out one qubit, compares to pure `GHZ_3`, records the reduced spectrum, and requires distance from pure GHZ3 (`stage_lifted_spinor_shell_n4_v0_jax.py:715-731`). The result reports spectrum `[0.5, 0.5, 0, ...]`, `distance_to_pure_GHZ3=0.707106781187`, and `pass=true`.

W4 nesting is computed, not asserted. The source traces out one qubit and compares to `0.75 * |W3><W3| + 0.25 * |000><000|` (`stage_lifted_spinor_shell_n4_v0_jax.py:734-749`). The result reports weights `W3=0.75`, `vacuum=0.25`, spectrum `[0.75, 0.25, 0, ...]`, `distance_to_expected_weighted_state=0.0`, and `pass=true`.

Controls flip. The support mutation controls record `rerun_under_mutation=true`, `gate_passed_after_mutation=false`, and concrete failing values for `global_shell_only`, `no_face`, `duplicate_eta`, and `collapsed_shell` (`stage_lifted_spinor_shell_n4_v0_jax.py:252-290`). The SMT density-erasure controls flip from main `unsat` to control `sat` (`stage_lifted_spinor_shell_n4_v0_jax.py:770-854`). The result also carries GHZ and W nesting tripwires in `rows.P11_negative_controls`.

## Q4 - Cl(8)

Status: **PASS for construction and independent recomputation; CAVEAT for stored artifact standard**.

The source constructs eight Jordan-Wigner gamma matrices plus chirality on the `C^16` carrier, checks pairwise anticommutators and squares, and computes chirality eigenvalue split (`stage_lifted_spinor_shell_n4_v0_jax.py:592-625`). The three engine results agree: `constructive_family_size=9`, `max_anticommutator_norm=0.0`, `squares_to_identity=true`, `chirality_split={plus:8, minus:8}`, and `pass=true`.

Independent recomputation on the finite 4-qubit Pauli surface found maximum clique size 9 across all 255 nonidentity Pauli strings modulo phase; no 10-clique exists on that surface. A separate rebuilt gamma-family check gave `max_anticommutator_norm=0.0` and chirality eigenvalues `+1` eight times and `-1` eight times.

Caveat: the committed result's maximality receipt is prose/dimension-bound text: "a 10-generator complex Clifford family would require irreducible dimension 2^5=32" (`stage_lifted_spinor_shell_n4_v0_jax.py:620`). That is mathematically aligned with the recomputation, but it is not a stored certified/exhaustive search receipt inside the artifact.

## Q5 - G1-G3 held at n=4

Status: **PASS, with one receipt-coverage note**.

G1 is closed at n=4. The packet derives leakage lineage from exported S5 `A,b`, cites the S5 result path/hash/pin, cites the committed S6 result path/hash, emits S6 class taxonomy, and keeps the current `z=cos(2 eta)` mirror (`stage_lifted_spinor_shell_n4_v0_jax.py:352-406`). The envelope gates `s5_s6_generator_lineage` across all three legs (`stage_lifted_spinor_shell_n4_v0_envelope.py:120-139`, `172-193`).

G2 is closed at validator level. The fresh capability-probe checks for JAX, PyTorch, and Julia all returned no violations. Declared load-bearing tools include the relevant topology, QIT, solver, geometric, and tensor packages in each leg; the envelope collects them under `claim_path_tools` and `TOOL_INTEGRATION_DEPTH`.

Receipt-coverage note: the JSON `tool_calls` entries are bundled and not one-to-one with every declared load-bearing package. This is not a current validator failure, but it remains weaker than a fully function-level receipt for each load-bearing tool.

G3 is closed. The n=4 support mutation controls use rerun-style records with failing values and `gate_passed_after_mutation=false` (`stage_lifted_spinor_shell_n4_v0_jax.py:252-290`). The envelope explicitly gates `mutation_controls_rerun_with_failing_values=true` across all legs (`stage_lifted_spinor_shell_n4_v0_envelope.py:107-117`, `172-193`).

## Q6 - carry-forward checks

G4: **OPEN**. n=4 emits real per-site static shell coordinates and aggregate leakage, and it has stronger support topology than n=3. I did not find a separately named static network-level shell coordinate. The closed claim is per-site `z=cos(2 eta)` plus aggregate leakage/support, not a distinct network coordinate.

G5: **OPEN**. z3/cvc5 raw-value SMT exists for density/support erasure (`stage_lifted_spinor_shell_n4_v0_jax.py:770-854`) and the envelope gates z3/cvc5 agreement (`stage_lifted_spinor_shell_n4_v0_envelope.py:189-191`). Bracketing remains numeric/symbolic: `matrix_associator_norm=0.0` and `lifted_path_grouping_gap=1.0` (`stage_lifted_spinor_shell_n4_v0_jax.py:628-661`). I found no z3/cvc5 raw-object bracketing proof at n=4.

## Q7 - standard

Status: **PASS-WITH-CAVEATS**.

The declared mode is honest: the envelope uses `engine_contract.mode=all_three_full_sims`, with Julia, JAX, and PyTorch lanes (`stage_lifted_spinor_shell_n4_v0_envelope.py:226-231`). Seeds are declared and gated identical across legs (`stage_lifted_spinor_shell_n4_v0_envelope.py:167-176`). The envelope gates source hashes, no peer-result reads, required rows, acceptance, negative controls, mutation controls, S5/S6 lineage, solver agreement, and zero cross-engine divergence (`stage_lifted_spinor_shell_n4_v0_envelope.py:172-193`).

The ceiling is explicit: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false` (`stage_lifted_spinor_shell_n4_v0_envelope.py:20-22`). Allowed claims are limited to scratch existence, three-engine agreement on named finite scalar rows, and controls catching named errors. Disallowed claims include stage closure, canonical geometry, bridge/axis admission, ladder trend, and promotion beyond scratch (`stage_lifted_spinor_shell_n4_v0_envelope.py:207-218`).

No cross-run parity claim is needed for this verdict. Fixture isolation is acceptable at scratch scope because the envelope uses source hashes, result hashes, no peer-result reads, and exact PIN/seed gates. SMT is raw-value for density/support erasure, not a derived-boolean-only solver wrapper. The remaining solver caveat is scope: it does not cover bracketing raw objects.

## Named caveats

G4. Static network-level shell coordinate gap remains open: n=4 has per-site shell coordinates, support topology, and aggregate leakage, but no separately named static network-level shell coordinate.

G5. Bracketing SMT gap remains open: bracketing/order rows are computed on the shared `C^16` carrier, but no z3/cvc5 raw-object bracketing proof is present.

G6. Cl(8) maximality artifact gap: construction and independent finite-surface recomputation support maximal family size 9, but the committed artifact stores a dimension-bound prose certificate rather than a certified/exhaustive search receipt.

G7. Coordinate-coupled state-family gap: support/leakage/path rows consume shell coordinates, but GHZ/W density and entropy rows are standard carrier-state rows with shell-placement receipts, not coordinate-parameterized state families.

G8. Function-level tool-call granularity gap: capability-probe validators are green for all declared load-bearing tools, but the result JSON bundles some tool calls instead of emitting a one-to-one function-level call record for every load-bearing package.

## Builder-hardening addendum - 2026-06-10

Fresh rerun scope: one bounded hardening batch for G6 and G8 only. G4, G5, and G7 remain open by design. The fresh audit verdict stands as **GENUINE-WITH-CAVEATS**.

Closed caveats:

- G6 closed. Each rerun leg now stores `rows.P6_order_gaps.Cl8_anchor.maximality_receipt`, an exact deterministic max-clique search over the 255 nonidentity n=4 Pauli strings modulo phase. The receipt records the search space, edge rule, method, stats, witness clique, `max_clique_size=9`, `target_excluded=10`, and `no_10_element_family_exists=true`; the committed `maximal_anticommuting_family=9` comes from that stored search.
- G8 closed. Each rerun leg now emits one `tool_calls` record per declared load-bearing package, using the function-level `{tool, qualified_api, input_object, output_object, positive_case, negative_control, boundary_case, demotion_condition, gates}` shape.

Fresh checks:

```text
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/stage_lifted_spinor_shell_n4_v0/stage_lifted_spinor_shell_n4_v0_julia.jl
```

Result: `stage_lifted_spinor_shell_n4_v0_julia_DONE all_pass=true`.

```text
env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/stage_lifted_spinor_shell_n4_v0/stage_lifted_spinor_shell_n4_v0_jax.py
```

Result: `stage_lifted_spinor_shell_n4_v0_jax_DONE all_pass=true`.

```text
env GEOMSTATS_BACKEND=pytorch NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/stage_lifted_spinor_shell_n4_v0/stage_lifted_spinor_shell_n4_v0_pytorch.py
```

Result: `stage_lifted_spinor_shell_n4_v0_pytorch_DONE all_pass=true`.

```text
env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/stage_lifted_spinor_shell_n4_v0/stage_lifted_spinor_shell_n4_v0_envelope.py
```

Result: `stage_lifted_spinor_shell_n4_v0_ENVELOPE_DONE all_pass=true max_divergence=0.0`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/stage_lifted_spinor_shell_n4_v0/results/stage_lifted_spinor_shell_n4_v0_envelope_results.json
```

Result: `{"ok": true}`.

Additional direct JSON checks: G6 certificate present and valid in all three legs; G8 one-to-one tool-call shape present for all load-bearing packages in all three legs; exact scalar rows and envelope engine-value rows are stable against the pre-hardening `HEAD` result values.

Ceiling unchanged: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Final verdict

**GENUINE-WITH-CAVEATS**.

Accept as:

- a real n=4 lifted spinor-shell scratch diagnostic;
- a four-site support object with explicit shell coordinates, path edges, shell faces, topology receipts, and shell-coordinate leakage rows;
- correct exact GHZ4, W4, IC-POVM, nesting-law, Cl(8) construction, chirality, mutation-control, S5/S6 lineage, and three-engine agreement checks at scratch scope;
- a packet with G1-G3 hardening baked in from the start.

Reject as:

- closure of G4 or G5;
- a stored exhaustive Cl(8) maximality certificate;
- a coordinate-parameterized GHZ/W state-family construction;
- stage closure, canonical geometry, bridge/axis admission, formal admission, physics, or ladder-trend evidence.

Ceiling restated: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
