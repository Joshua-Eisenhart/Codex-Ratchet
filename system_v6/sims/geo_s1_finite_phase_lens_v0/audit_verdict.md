# Fresh Audit: geo_s1_finite_phase_lens_v0

Audit date: 2026-06-10

VERDICT: GENUINE-WITH-CAVEATS for the finite-phase lens tower scratch diagnostic.

The packet is an executable three-engine scratch diagnostic. The strict validator passes, L1-L6 receipts pass, the N-ladder is coherent, the loop-lift order is counted by distinct endpoints, the factoring chain is checked pointwise through density invariance and phase-residue classes, the finite-probe class counts match the intended orbit counts, the mismatch control fires, and independent hand recomputations at N=4 and N=3 match the packet.

The caveats are specific: L2 is not actually Monte Carlo volume estimation in the source, despite the build card wording; it uses the closed-form `2*pi^2/N` plus exact orbit ratios. L1 also constructs finite orbits and checks sample separation, but it does not perform a general symbolic freeness proof beyond the finite action formula and the non-free control.

Ceiling remains: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. The lens tower is an F01-admissible alternative family under test. It does not replace the Hopf quotient and does not promote to formal admission.

## Evidence Boundary

Sources read:

- `system_v6/sims/geo_s1_finite_phase_lens_v0/build_card.md`
- `system_v6/sims/geo_s1_finite_phase_lens_v0/geo_s1_finite_phase_lens_v0_jax.py`
- `system_v6/sims/geo_s1_finite_phase_lens_v0/geo_s1_finite_phase_lens_v0_pytorch.py`
- `system_v6/sims/geo_s1_finite_phase_lens_v0/geo_s1_finite_phase_lens_v0_julia.jl`
- `system_v6/sims/geo_s1_finite_phase_lens_v0/geo_s1_finite_phase_lens_v0_envelope.py`
- `system_v6/sims/geo_s1_finite_phase_lens_v0/results/geo_s1_finite_phase_lens_v0_jax_results.json`
- `system_v6/sims/geo_s1_finite_phase_lens_v0/results/geo_s1_finite_phase_lens_v0_pytorch_results.json`
- `system_v6/sims/geo_s1_finite_phase_lens_v0/results/geo_s1_finite_phase_lens_v0_julia_results.json`
- `system_v6/sims/geo_s1_finite_phase_lens_v0/results/geo_s1_finite_phase_lens_v0_envelope_results.json`
- R3 comparison pattern: `system_v6/sims/axis_independence_discriminators_036/audit_verdict.md`

Fresh commands/checks:

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s1_finite_phase_lens_v0/results/geo_s1_finite_phase_lens_v0_envelope_results.json` returned `ok:true`.
- Source import recomputed `build_rows()` without calling `main()` or rewriting result JSON.
- Audit-side hand recomputation checked one N=4 orbit identification, one N=4 volume Monte Carlo spot check, and one N=3 lift count.
- `git status --short -- system_v6/sims/geo_s1_finite_phase_lens_v0` reports the packet directory as untracked in this checkout.

## Manual Recompute Packet

Source-import recompute values:

| Check | Recomputed value |
|---|---|
| L1 orbit sizes | `N=1,2,3,4,8,16,64` all pass; JAX `sample_count = 128*N`, `orbit_count = 128`, `orbit_size = N` |
| L2 N=4 source volume | `4.934802200544679`, equal to `2*pi^2/4` |
| L3 N=3 source lift order | `3` endpoint classes |
| L4 N=4 density chain | `rho_zN_invariance_max_deviation = 1.203566243736227e-16`, `phase_residue_unique_values = 48` |
| L5 N=4 probe classes | `336`, equal to expected `7*192/4` |
| L5 N=4 mismatch control | `M=3`, mismatch count `448` vs target `336`, control fired |
| L6 distances | `1.0, 0.5, 0.3333333333333333, 0.25, 0.125, 0.0625, 0.015625` |

Hand recomputations:

| Hand check | Result |
|---|---|
| N=4 orbit identification | one explicit normalized spinor produced 4 distinct phase images; minimum orbit separation `1.414213562373095`; density max deviation across the orbit `1.1208188977828797e-16` |
| N=4 volume MC spot check | Haar-sector fraction `0.250555`; estimate `4.9457574614298885`; target `4.934802200544679`; absolute error `0.010955260885209483` |
| N=3 lift count | endpoint set `{(1,0), (-0.5,0.866025403784), (-0.5,-0.866025403784)}` has order `3` |

## L1. Z_N Action Freeness And Orbit Sizes

Decision: PASS WITH CAVEAT.

Quoted source:

```python
orbit = phases[:, None, None] * samples[None, :, :]
sample_count = int(orbit.reshape((-1, 2)).shape[0])
orbit_count = sample_count // n
```

Cites: `geo_s1_finite_phase_lens_v0_jax.py:207-239`; non-free control at `geo_s1_finite_phase_lens_v0_jax.py:314-320`; envelope gate at `geo_s1_finite_phase_lens_v0_envelope.py:149-155`.

The source constructs N phase images per Haar sample, records `orbit_size=N`, computes sample separation for nontrivial phases, and carries a non-free-action control. Recompute matches all N rows. Caveat: `orbit_count = sample_count // n` is arithmetic after construction, not a quotient grouping algorithm; freeness is supported by finite-orbit separation and the formula string, not by a symbolic proof.

## L2. Volume Tower

Decision: PASS FOR EXACT VALUES, CAVEAT FOR MONTE CARLO CLAIM.

Quoted source:

```python
lens_volume = 2.0 * math.pi**2 / n
unidentified = 2.0 * math.pi**2
```

Cites: `geo_s1_finite_phase_lens_v0_jax.py:224-252`; Julia mirror at `geo_s1_finite_phase_lens_v0_julia.jl:88-109`; envelope known-values gate at `geo_s1_finite_phase_lens_v0_envelope.py:156-160`.

The source reproduces `2*pi^2/N` exactly for every N and emits the wrong-unidentified ratio N. It does not perform a stochastic Monte Carlo integration per N, even though the build card requests MC. My audit-side N=4 MC spot check estimates `4.9457574614298885` against target `4.934802200544679`, within expected sampling error for `200000` Haar spinors.

## L3. Loop-Lift Group Order

Decision: PASS.

Quoted source:

```python
endpoints = [(round(math.cos(2.0 * math.pi * k / n), 12), round(math.sin(2.0 * math.pi * k / n), 12)) for k in range(n)]
...
"computed_fundamental_group_order": len(set(endpoints)),
```

Cites: `geo_s1_finite_phase_lens_v0_jax.py:254-265`; Julia mirror at `geo_s1_finite_phase_lens_v0_julia.jl:111-119`.

The group order is counted from distinct lift endpoints, not merely copied from the known order. Hand recompute at N=3 gives three endpoint classes, matching the source row and the known Z_3 order.

## L4. Factoring Chain S3 -> L(N,1) -> S2

Decision: PASS.

Quoted source:

```python
z_deviation = as_float(jnp.max(jnp.abs(density(orbit) - density(samples)[None, :, :, :])))
...
"phase_residue_unique_values_on_192_phase_grid": residue_unique,
```

Cites: `geo_s1_finite_phase_lens_v0_jax.py:216-219`; chain row at `geo_s1_finite_phase_lens_v0_jax.py:266-279`.

The packet checks density invariance under each Z_N orbit and full S1 phase sweeps, then records the finite phase residue retained by L(N,1). For N=4, recompute gives density deviation `1.203566243736227e-16` and 48 phase-residue classes on the 192-point phase grid. My explicit N=4 orbit hand check also produced density deviation `1.1208188977828797e-16`.

## L5. Probe Resolution

Decision: PASS.

Quoted source:

```python
return [(base, phase_index % period) for base in range(base_count) for phase_index in range(PHASE_GRID)]
...
"computed_probe_quotient_class_count": f01_count,
```

Cites: label construction at `geo_s1_finite_phase_lens_v0_jax.py:174-180`; probe row at `geo_s1_finite_phase_lens_v0_jax.py:280-293`; mismatch control at `geo_s1_finite_phase_lens_v0_jax.py:304-312`.

The class counts match the intended orbit counts. At N=4, `7*192/4 = 336`, and the source recompute returns `computed_probe_quotient_class_count=336`. The mismatch control fires: using M=3 gives `448`, not the target `336`.

## L6. N-Ladder Convergence

Decision: PASS WITH CAVEAT.

Quoted source:

```python
"normalized_distance_to_density_quotient": 1.0 / n,
...
convergence_rows[i]["normalized_distance_to_density_quotient"] > convergence_rows[i + 1]["normalized_distance_to_density_quotient"]
```

Cites: row construction at `geo_s1_finite_phase_lens_v0_jax.py:295-303`; pass rule at `geo_s1_finite_phase_lens_v0_jax.py:347-354`; envelope divergence at `geo_s1_finite_phase_lens_v0_envelope.py:281-286`.

The recorded ladder is strictly decreasing: `1, 1/2, 1/3, 1/4, 1/8, 1/16, 1/64`. It matches across Julia, JAX, and PyTorch with envelope divergence `0.0`. Caveat: the distance is a defined analytic proxy `1/N`, not an independently measured metric on quotient spaces.

## Named Gaps

1. L2 should be renamed or hardened. As written, it is exact formula plus orbit-ratio accounting, not Monte Carlo volume estimation per N.
2. L1 would be stronger with explicit quotient-class grouping per sample orbit and a proof/check that no nonidentity phase fixes any nonzero spinor, rather than relying on construction plus sample separation.
3. L6 should keep its current ceiling unless the analytic `1/N` proxy is replaced or supplemented by an explicit metric computation against density quotient classes.

## Final Boundary

Keep: executable three-engine scratch diagnostic; finite Z_N lens-family receipts; loop-lift endpoint counting; density factoring checks; F01 finite-probe class counts; mismatch control; strict validator pass.

Audit further: true MC volume estimation and stronger quotient/freeness grouping.

Demote: any claim that the lens tower replaces the Hopf quotient, proves formal admission, or upgrades beyond F01-admissible alternative-family scratch evidence.

Broken/blocked: none found for the stated scratch-diagnostic packet.

Next build: add a real MC volume estimator or change the L2 claim text to exact volume accounting, and add explicit quotient-class grouping for L1.

## Post-Hardening Re-Audit Addendum — 2026-06-10

Scope: focused read-only re-audit of the prior §Named Gaps after hardening. I did not rebuild or harden this packet; I inspected source/result state and reran the validators.

Validator reruns:

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v6/sims/geo_s1_finite_phase_lens_v0/results/geo_s1_finite_phase_lens_v0_envelope_results.json` returned `{"ok": true}`.
- Extra strict check also returned `{"ok": true}` with `--require-pytorch --strict-source-backed`.

Named-gap closure check:

1. L2 is honestly labeled as `volume_route: exact formula + orbit-ratio accounting`, and each JAX L2 row now includes `monte_carlo_volume_comparison`. Spot check at `N=4`: exact `known_value_2pi2_over_N=4.934802200544679`; MC comparison computes `estimate=4.919997793943045`, `sector_hits=4985`, `sector_fraction=0.24925`, `abs_error=0.014804406601633957`, so it is computed independently rather than copied from the exact formula.
2. L1 now emits per-orbit grouping and freeness scan fields. Every JAX L1 row has `orbit_class_grouping`; nontrivial N rows emit `freeness_scan_min_fixed_point_distance`, with N=2 `1.9999999999999996`, N=4 `1.4142135623730947`, and N=64 `0.09813534865483586`. The non-free control is still caught with fixed-point deviation `0.0`.
3. L6 is explicitly labeled as a proxy and supplemented by finite-grid metric comparison. Every JAX L6 row has `proxy_label: analytic_1_over_N_proxy` and `explicit_density_quotient_metric`; the comparison field records finite-grid residual class diameter against density quotient classes.

Byte-stable fields checked:

- Known volumes remain `2pi^2/N`: N=1 `19.739208802178716`, N=2 `9.869604401089358`, N=3 `6.579736267392906`, N=4 `4.934802200544679`, N=8 `2.4674011002723395`, N=16 `1.2337005501361697`, N=64 `0.30842513753404244`.
- JAX orbit counts remain 128 for all N rows; Julia orbit counts remain 64; PyTorch orbit counts remain 96. Expected counts match in each engine row.
- Lift/fundamental-group orders remain N = `1, 2, 3, 4, 8, 16, 64` with Hopf S2 and S3 controls at order `1`.
- Solver polarity remains stable: z3/cvc5 `orbit_count_differs=unsat`, `commuting_chain_nonzero=unsat`, `non_free_control=sat`; Julia Z3 remains `unsat`.
- Engine comparison scalars remain stable: JAX/JULIA max volume abs error `0.0`, group order abs error `0`; JAX max chain deviation `3.3516982005219445e-16`; PyTorch max chain deviation `3.3628794013248684e-16`; N=64 convergence proxy `0.015625`.

Current ceiling: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. This remains an F01 finite-resolution alternative-family packet only; it does not replace the Hopf quotient and carries no formal-admission, bridge, axis, or promotion claim. Prior §Named Gaps are historically preserved above, but no stale open-gap surface remains for the three named hardening items checked here.

Final line: sustained.
