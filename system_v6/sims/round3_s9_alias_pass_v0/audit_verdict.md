# Audit verdict - round3_s9_alias_pass_v0

Bottom line: VERDICT `GENUINE-WITH-CAVEATS` as a bounded S9
`scratch_diagnostic` light-symbolic phase-1 alias pass. Cite it only for the
S9 anchor self-classification, the exact gauge-reparameterization alias
control, the round-2 flat far-control dying on the curvature-density first
teeth row, the four pin-relative light-symbolic S9 exclusions under the pinned
`phi` holonomy convention, and the preserved S9 phase-2
`open + queued-heavy-local` row. Do not cite it as intrinsic S9 uniqueness,
path-ordered transport evidence, known co-survivor evidence, PyTorch evidence,
or numeric-closeness alias evidence.

## Verdict

- Repo vocabulary: `GENUINE-WITH-CAVEATS`.
- Classification: `scratch_diagnostic`.
- `promotion_allowed=false`; `formal_admission_allowed=false`.
- Engine mode: `julia_canon_plus_jax_diagnostic`.
- Honest mode legitimacy: accepted. The packet scopes exact connection
  coefficient, curvature, leaf holonomy, annular flux, and SMT finite-witness
  rows. No tensor, graph, autograd, message-passing, or PyTorch claim path is
  present.
- Convention pin discipline: accepted only after audit-side citation repair.
  Packet result strings say `excluded-by-...`; citable S9 wording must be
  `excluded-under-pinned-phi-holonomy-convention` plus the registry-named teeth
  row, because S9 is a connection/holonomy layer and the S2 lifted-holonomy
  precedent is directly load-bearing here.
- Heavy fence: accepted. Path-ordered transport loops did not run; S9.R3.5 is
  `open + queued-heavy-local`.

## Named Caveats

- C1 - Convention-pin vocabulary: S9.R3.1-R3.4 have exact separating witnesses,
  but their citable status is pin-relative and reopenable. Do not cite packet
  `excluded-by-*` strings as intrinsic kills.
- C2 - SMT depth: z3, cvc5, and Julia Z3 bind finite rational nonzero witnesses
  with SAT flip controls. They do not prove the full connection canonical tuple
  or the CAS/surd rows.
- C3 - Julia lane depth: Julia rebuilds exact f/F forms with Symbolics and
  carries exact leaf substitutions plus Z3.jl polarity. It is verdict-provenance
  and reference parity, not an independent full symbolic derivation of every
  SymPy tuple field.
- C4 - Packet-local validator freshness: I did not rerun
  `validate_round3_s9_alias_pass_v0.py` because it rewrites
  `results/round3_s9_alias_pass_v0_validator_results.json`; the existing
  packet-local validator on disk is green. Fresh read-only generic validators
  are listed below.
- C5 - On-disk state: `system_v6/sims/round3_s9_alias_pass_v0/` is currently
  untracked in this checkout. This verdict accepts current on-disk evidence
  only; it does not make the packet committed repo truth.

## Exact Recompute

Read-only scratch recomputation over exact SymPy expressions confirmed the
claim path. No float tolerance, `isclose`, `allclose`, or numeric threshold is
on the accepted alias/exclusion path.

| Row | Exact recompute result |
| --- | --- |
| `S9.R3.1_c1_small_density_bump`, epsilon `1/20` | Anchor curvature coefficient `-2*sin(2*eta)`; candidate `(cos(2*eta) - 10)*sin(2*eta)/5`; exact gap `sin(4*eta)/10`. |
| `S9.R3.2_one_leaf_match_pi6`, epsilon `1/10` | Holonomy vector anchor `{0:1, pi/6:1/2, pi/4:0, pi/3:-1/2, pi/2:-1}`; candidate `{0:21/20, pi/6:1/2, pi/4:-1/20, pi/3:-3/5, pi/2:-23/20}`; off-anchor gap at `0` is `1/20`, while the pinned `pi/6` leaf gap is `0`. |
| `S9.R3.4_two_leaf_match_pi6_pi4`, epsilon `1/10` | Annular flux `0->pi/6`: anchor `-1/2`, candidate `-11/20`, exact gap `-1/20`; off-anchor holonomy at `pi/3` differs by `1/20`. |
| deliberate gauge-reparameterization control | `1 - 2*sin(eta)^2 - cos(2*eta)` simplifies exactly to `0`; leaf vector and `c1=1` match. |
| round-2 flat far-control | Anchor curvature coefficient `-2*sin(2*eta)` versus flat `0`; dies on the curvature-density first teeth row. |

## Controls

| Control | Builder verdict | Audit adjudication |
| --- | --- | --- |
| `control.anchor_self` | `anchor` | Accepted. Exact f/F/holonomy/annular-flux canonical tuple self-classifies. |
| `control.alias_reparameterized_committed` | `alias` | Accepted. Gauge reparameterization reduces by exact symbolic identity, not closeness. |
| `control.round2_flat_far_connection` | `excluded-by-curvature-density-row` | Accepted as first-teeth control exclusion under the pinned S9 chart. |

## Citable Per-Candidate Table

| Candidate | Registry cost | Citable verdict | Citable witness / disposition |
| --- | --- | --- | --- |
| `S9.R3.0_committed_hopf` | light-symbolic | `anchor` | Exact canonical tuple for `f=cos(2eta)` self-classifies. |
| `S9.R3.1_c1_small_density_bump` | light-symbolic | `excluded-under-pinned-phi-holonomy-convention` via `curvature density before holonomy` | Exact curvature coefficient gap `sin(4*eta)/10` for epsilon `1/20`; same `c1` alone is not alias. Reopen if the pinned S2/S9 holonomy/convention map changes. |
| `S9.R3.2_one_leaf_match_pi6` | light-symbolic | `excluded-under-pinned-phi-holonomy-convention` via `expanded holonomy spectrum` | Matches the pinned `pi/6` leaf but differs at `0` by exact `1/20` for epsilon `1/10`; reopenable under convention change. |
| `S9.R3.3_one_leaf_match_pi4` | light-symbolic | `excluded-under-pinned-phi-holonomy-convention` via `expanded holonomy spectrum` | Matches the pinned `pi/4` leaf but differs at `0` by exact `1/10` for epsilon `1/10`; reopenable under convention change. |
| `S9.R3.4_two_leaf_match_pi6_pi4` | light-symbolic | `excluded-under-pinned-phi-holonomy-convention` via `annular flux plus off-anchor holonomy` | Matches the pinned `pi/6` and `pi/4` leaves but the `0->pi/6` annular flux differs by exact `-1/20`; reopenable under convention change. |
| `S9.R3.5_path_ordered_loop_neighbor` | heavy-local | `open + queued-heavy-local` | Path-ordered holonomy commutator row is heavy-local and not run; no cited prior co-survivor receipt. |

Known S9 R3 co-survivor classes: none.

## Heavy Fence

The packet preserves the registry cost boundary:

```text
S9.R3.5_path_ordered_loop_neighbor - path-ordered holonomy commutator
```

This row is queued only. The result boundary says path-ordered transport loops
are `not run; queued-heavy-local`, and source/result search found only queued
signature strings, not a path-ordered loop computation or commutator execution.

## Provenance And Schema Checks

Inspected artifacts:

- `build_card.md` imports S2 exact canonical-form discipline, the S2
  pin-relative vocabulary rule, the S3 known-co-survivor citation rule, and the
  S4/S5/S6S7 heavy-local queue correction.
- `provenance.md` quotes the S9 registry table and the resource guard.
- `round3_s9_alias_pass_v0_envelope_results.json` reports
  `schema_version=three_engine_sim_result_v1`, `all_pass=true`,
  `scratch_diagnostic`, `promotion_allowed=false`,
  `formal_admission_allowed=false`, `julia_canon_plus_jax_diagnostic`, explicit
  PyTorch omission, and S9.R3.5 in the heavy-local queue.
- `round3_s9_alias_pass_v0_jax_results.json` carries load-bearing SymPy, z3,
  and cvc5 rows.
- `round3_s9_alias_pass_v0_julia_results.json` carries Symbolics and Z3.jl
  reference rows; Julia/JAX verdict maps match.
- `round3_s9_alias_pass_v0_validator_results.json` reports `ok=true`,
  `validator_ok=true`, and `errors=[]`.

Fresh read-only validators:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/round3_s9_alias_pass_v0/results/round3_s9_alias_pass_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s9_alias_pass_v0/results/round3_s9_alias_pass_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-source-backed system_v6/sims/round3_s9_alias_pass_v0/results/round3_s9_alias_pass_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s9_alias_pass_v0/results/round3_s9_alias_pass_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --strict-source-backed system_v6/sims/round3_s9_alias_pass_v0/results/round3_s9_alias_pass_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s9_alias_pass_v0/results/round3_s9_alias_pass_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-tool-intent system_v6/sims/round3_s9_alias_pass_v0/results/round3_s9_alias_pass_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s9_alias_pass_v0/results/round3_s9_alias_pass_v0_envelope_results.json"}
```

Expected PyTorch-scoped negative:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/round3_s9_alias_pass_v0/results/round3_s9_alias_pass_v0_envelope_results.json
-> {"ok": false, "errors": ["engines.pytorch must be an object"]}
```

## Phase-2 Disposition For S9

S9 phase 2 is exactly:

```text
S9.R3.5_path_ordered_loop_neighbor - path-ordered holonomy commutator
```

Do not run a broad S9 heavy battery for count inflation. The next admissible S9
work is a narrow heavy-local packet over the queued path-ordered transport row,
with explicit loop family, path-ordering convention, commutator observable,
wrong-loop/control, and no S9 uniqueness promotion.

## Consolidated Round-3 Heavy Queue On Disk

The S9 verdict completes the round-3 LIGHT program across S2/S3/S4/S5/S6S7/S9
as represented by the current on-disk validator/audit surfaces. Consolidated
phase-2 heavy queue:

```text
S2.R3.5_boundary_conditioning_variant - cover/conditioning validity before flux comparison

S3 - no heavy-local row queued; SIC is prior-receipt known co-survivor, not heavy-queued

S4.R3.1_z_amplitude_damping_pair - N01/commutator and fixed-axis rows
S4.R3.2_x_amplitude_damping_pair - z-probe quotient descent/mortality
S4.R3.3_dephase_rotate_hybrid - shell preservation/leakage then N01
S4.R3.5_weak_nonunital_pauli_channel - fixed-axis plus Choi positivity

S5.R3.1_alpha_mix_rotation_contraction__alpha_1_4 - mirror structure and N01 full signature
S5.R3.1_alpha_mix_rotation_contraction__alpha_1_2 - mirror structure and N01 full signature
S5.R3.1_alpha_mix_rotation_contraction__alpha_3_4 - mirror structure and N01 full signature
S5.R3.2_committed_coeff_epsilon__plus_1_20 - fixed-point/basin and N01 gap
S5.R3.2_committed_coeff_epsilon__minus_1_20 - fixed-point/basin and N01 gap
S5.R3.3_nonunital_weak_shift__plus_1_20 - validity, fixed point, quotient 56/56
S5.R3.3_nonunital_weak_shift__minus_1_20 - validity, fixed point, quotient 56/56
S5.R3.5_basin_preserving_null - quotient survival plus time-flow/N01 row

S67.R3.1_mobius_reflection_shifted - lens quotient commensurability
S67.R3.2_klein_double_twist - cover-orbit well-definedness then lens row
S67.R3.3_shear_torus - lens descent and S6 leakage taxonomy
S67.R3.4_cycle_with_one_chord - bounded word cost and cycle holonomy
S67.R3.5_ladder_prism_graph - locality cost plus leakage class row

S9.R3.5_path_ordered_loop_neighbor - path-ordered holonomy commutator
```

All listed rows remain `open + queued-heavy-local` unless a later receipt runs
the registry-named heavy teeth or cites an applicable prior known-co-survivor
receipt.

## Future-Citation Rule

Future citations may say:

> `round3_s9_alias_pass_v0` is a bounded S9 phase-1 `scratch_diagnostic`:
> anchor self-classifies; the deliberate gauge-reparameterization is an exact
> symbolic alias; the round-2 flat far-control dies on curvature density;
> S9.R3.1-R3.4 are excluded only under the pinned S2/S9 `phi` holonomy
> convention by registry-named exact light-symbolic teeth and are reopenable if
> that convention changes; S9.R3.5 remains `open + queued-heavy-local`.

Future citations must not say:

> S9 uniqueness was proved; S9.R3.1-R3.4 are intrinsically killed independent
> of convention; path-ordered transport loops ran; S9.R3.5 is a co-survivor;
> PyTorch evidence exists; SMT proved the full connection canonical tuple;
> Julia independently proved all SymPy rows; numeric closeness established
> alias status; the S9 packet is committed repo truth.

## Route-Truth Note

Wizard v4.2 Max Assembly was partial in this session: no Codex-native
`spawn_agent` tool was exposed, so no full nine-parent/child topology or worker
plurality is claimed. Evidence for this verdict is direct repo inspection,
fresh exact scratch recomputation, existing packet result files, and fresh
read-only generic validator reruns.
