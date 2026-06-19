# Audit verdict - round3_s5_heavy_discriminator_v0

Bottom line: VERDICT `GENUINE-WITH-CAVEATS` as a bounded S5 phase-2
heavy-local `scratch_diagnostic` discriminator packet. The packet answers all
eight S5 rows normalized by `round3_s5_alias_pass_v0/audit_verdict.md`: every
queued S5 candidate is excluded by its registry-named heavy row, no
co-survivor is minted, and the scope is only the registered S5 queued rows.

This audit was read-only except for writing this file. I did not `git add` or
commit.

## Verdict

Accepted:

- `classification=scratch_diagnostic`.
- `promotion_allowed=false` and `formal_admission_allowed=false`.
- Engine mode `julia_canon_jax_with_pytorch_graph`.
- Registry binding to `de44219ed` is present and green in the envelope gates.
- All three lane verdict maps match the expected eight S5 heavy exclusions.
- N01 "full signature" is actually full in the packet: every candidate table
  row carries 8 terrain rows under
  `n01_full_signature_comparison.rows`, with `all_equal=false`.
- Basin/graph rows are on the 33-cell grid, carry the
  `CHART_RELATIVE_33_CELL_GRID_FE3754782_RULE` label, and the source emits
  absent-exit proofs for terminal classes.
- No row is marked `pin_relative`; no convention-pinned exclusion is hidden.
- No `GENUINE CO-SURVIVOR` label is minted.

Rejected or not promoted:

- S5 uniqueness.
- Any closure beyond the eight registered S5 queued rows.
- Canonical or formal admission.
- Chart-independent basin language.
- A raw transition-graph alias claim for R3.5.
- Any claim that SMT proves the full symbolic terrain canonical tuple.

## Exact-Witness Recompute

Fresh scratch recomputation imported only the packet source functions and
rebuilt the exact forms/33-cell graphs from the committed S5 anchor result. It
did not read the packet result JSON for the quoted witness values.

### R3.1 alpha row

For `S5.R3.1_alpha_mix_rotation_contraction__alpha_1_4`:

```text
registry row      = mirror structure and N01 full signature
verdict           = excluded-by-mirror-structure-and-N01-full-signature
anchor mirror Ne  = S1_continuum_pure_rotation_axis_flip
candidate mirror  = empty_or_noncommitted
N01 row count     = 8 terrain rows
N01 all equal     = false
first N01 split   = n01_full_signature.Ne_Spiral_R.delta[0]
anchor value      = -2*sin(theta)
candidate value   = -sin(theta)/2
```

This confirms the R3.1 row is not a one-pair N01 relabel: the full 8-row
signature is present, and the mirror-frame row also separates.

### R3.5 two-stage row

For `S5.R3.5_basin_preserving_null`:

```text
registry row      = quotient survival plus time-flow/N01 row
verdict           = excluded-by-time-flow-N01-row-after-quotient-survival
quotient row      = 56 ordered off-diagonal pairs, 56 distinguished, 0 collapsed
quotient survives = true
fixed row         = equal
N01 row count     = 8 terrain rows
N01 all equal     = false
first N01 split   = n01_full_signature.Se_Funnel_L.delta[0]
anchor value      = 2*sin(theta)/5
candidate value   = (5*sqrt(3)*sin(theta) + 28*sin(theta) + 5)/70
```

The time-flow row also separates:

```text
anchor charpoly    = (5*mu + 4)*(5*mu**2 + 8*mu + 4)/25
candidate charpoly = (5*mu + 4)*(735*mu**2 + 1176*mu + 28*sqrt(3) + 603)/3675
```

Adjudication: R3.5 genuinely survives the packet's quotient row before dying
on time-flow/N01. That is the registry's expected-teeth design working. Caveat:
the 33-cell raw transition graph hash differs from the anchor even though the
coarse terminal/may/must sizes match, so cite R3.5 as quotient/fixed-row
survival followed by time-flow/N01 exclusion, not as a full graph alias.

### R3.3 quotient row

The registry/build definition used by the packet is quoted in the result:

```text
ordered off-diagonal pairs among the eight terrain A,b row signatures; 56/56
means every ordered left/right pair is distinguishable
```

Scratch recomputation for `S5.R3.3_nonunital_weak_shift__plus_1_20`:

```text
ordered_pairs       = 56
distinguished_pairs = 56
collapsed_pairs     = []
survival_56_of_56   = true
invalid row         = Ni_Source_R
fixed split field   = fixed.Ni_Pit_L.fixed_point[0]
anchor              = -8*(8 + 5*sqrt(3))/203
candidate           = -36*(8 + 5*sqrt(3))/1015
```

For the minus row, the validity invalid row is `Ni_Pit_L`; the fixed-point and
N01 rows also separate. The quotient computation is the packet's narrow
registered quotient row, not a global quotient theorem.

## Citable Per-Candidate Table

| Candidate | Registry heavy row | Citable verdict | Citable witness / caveat |
| --- | --- | --- | --- |
| `S5.R3.1_alpha_mix_rotation_contraction__alpha_1_4` | mirror structure and N01 full signature | `excluded-by-mirror-structure-and-N01-full-signature` | Ne mirror changes from `S1_continuum_pure_rotation_axis_flip` to `empty_or_noncommitted`; full 8-row N01 first split `Ne_Spiral_R.delta[0]`: anchor `-2*sin(theta)`, candidate `-sin(theta)/2`. |
| `S5.R3.1_alpha_mix_rotation_contraction__alpha_1_2` | mirror structure and N01 full signature | `excluded-by-mirror-structure-and-N01-full-signature` | Same mirror-class split; full 8-row N01 first split at `Ne_Spiral_R.delta[0]`: candidate `-sin(theta)`. |
| `S5.R3.1_alpha_mix_rotation_contraction__alpha_3_4` | mirror structure and N01 full signature | `excluded-by-mirror-structure-and-N01-full-signature` | Same mirror-class split; full 8-row N01 first split at `Ne_Spiral_R.delta[0]`: candidate `-3*sin(theta)/2`. |
| `S5.R3.2_committed_coeff_epsilon__plus_1_20` | fixed-point/basin and N01 gap | `excluded-by-fixed-point-basin-and-N01-gap` | Fixed-point row changes; chart-relative 33-cell transition graph hash separates; full N01 signature separates. |
| `S5.R3.2_committed_coeff_epsilon__minus_1_20` | fixed-point/basin and N01 gap | `excluded-by-fixed-point-basin-and-N01-gap` | Fixed-point row changes and full N01 signature separates. Coarse terminal summary survives, but the registry row is still answered by fixed/N01 witnesses. |
| `S5.R3.3_nonunital_weak_shift__plus_1_20` | validity, fixed point, quotient 56/56 | `excluded-by-validity-fixed-point-and-quotient-row` | `Ni_Source_R` invalid; quotient row computed as `56/56`; fixed point separates at `Ni_Pit_L.fixed_point[0]`. |
| `S5.R3.3_nonunital_weak_shift__minus_1_20` | validity, fixed point, quotient 56/56 | `excluded-by-validity-fixed-point-and-quotient-row` | `Ni_Pit_L` invalid; quotient row computed as `56/56`; fixed point and N01 separate. |
| `S5.R3.5_basin_preserving_null` | quotient survival plus time-flow/N01 row | `excluded-by-time-flow-N01-row-after-quotient-survival` | Quotient survives `56/56` and fixed row is equal; time-flow charpoly and full N01 row separate. Do not cite as raw graph alias; transition graph hash differs. |

Known S5 R3 co-survivor classes after this packet: none.

## PyTorch Honesty

Accepted with a bounded claim path. PyTorch is not decorative here:

- `round3_s5_heavy_discriminator_v0_pytorch.py` builds 33-cell tensors,
  applies affine flows through `torch.func.vmap`, and constructs
  `torch_geometric.data.Data(edge_index=..., num_nodes=33)`.
- The PyTorch result reports `aligned_packages_load_bearing` as
  `["torch.func", "torch_geometric", "z3", "cvc5"]`.
- `package_observables` names the actual work:
  `torch.func` materializes all 33 cell images per terrain generator, and
  `torch_geometric` carries the finite transition graph for basin rows.
- Fresh `--require-pytorch --strict-source-backed --require-tool-intent`
  validation returned `ok=true`.

Boundary: PyTorch is load-bearing only for the finite graph/basin carrier row.
The exact mirror, fixed-point, quotient, N01, and time-flow symbolic witnesses
remain Julia/Python exact-symbolic/SMT surfaces.

## Controls And SMT

Controls accepted:

- Anchor self-passes scoped heavy rows.
- Deliberate reparameterized anchor remains an exact alias.
- S5 light-pass `R3.4_pairwise_LR_mirror_preserver` regression remains
  excluded by the Ni/Si mirror-frame row; scratch recomputation saw the split
  at `row_signatures.Ni_Pit_L.A[0][1]`, anchor `-2*sqrt(3)/15`, candidate
  `-(-1 + 4*sqrt(3))/30`.

SMT accepted as finite witness binding:

```text
excluded_candidate_count = 8
r3_1_alpha_values_sum_times_2 = 3
r3_2_plus_coeff_gap_times_20 = 1
r3_2_minus_coeff_gap_times_20 = -1
r3_3_plus_bz_gap_times_20 = 1
r3_3_minus_bz_gap_times_20 = -1
r3_5_se_funnel_A01_gap_times_7 = -1
```

z3, cvc5, and Julia Z3 report UNSAT for the negated/erased witness assertion
and SAT under the flip controls. This is load-bearing finite witness binding,
not a proof of every full symbolic tuple field.

## Verification Commands

Fresh read-only validators run by this audit:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/round3_s5_heavy_discriminator_v0/results/round3_s5_heavy_discriminator_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s5_heavy_discriminator_v0/results/round3_s5_heavy_discriminator_v0_envelope_results.json"}
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/round3_s5_heavy_discriminator_v0/results/round3_s5_heavy_discriminator_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s5_heavy_discriminator_v0/results/round3_s5_heavy_discriminator_v0_envelope_results.json"}
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/round3_s5_heavy_discriminator_v0/results/round3_s5_heavy_discriminator_v0_envelope_results.json
-> {"ok": true, "result_json": "system_v6/sims/round3_s5_heavy_discriminator_v0/results/round3_s5_heavy_discriminator_v0_envelope_results.json"}
```

I did not rerun `validate_round3_s5_heavy_discriminator_v0.py` in place
because it writes
`results/round3_s5_heavy_discriminator_v0_validator_results.json`, and this
audit was allowed to write only `audit_verdict.md`. The existing on-disk
packet-local validator result reports `ok=true`, `validator_ok=true`, and
`errors=[]`.

## Remaining Cross-Layer Heavy Queue

With S4-heavy committed and this S5-heavy packet accepted, the remaining
round-3 phase-2 heavy queue is:

```text
S2.R3.5_boundary_conditioning_variant - cover/conditioning validity before flux comparison

S67.R3.1_mobius_reflection_shifted - lens quotient commensurability
S67.R3.2_klein_double_twist - cover-orbit well-definedness then lens row
S67.R3.3_shear_torus - lens descent and S6 leakage taxonomy
S67.R3.4_cycle_with_one_chord - bounded word cost and cycle holonomy
S67.R3.5_ladder_prism_graph - locality cost plus leakage class row

S9.R3.5_path_ordered_loop_neighbor - path-ordered holonomy commutator
```

Do not cite the S5 result as closing S2, S6/S7, or S9.

## Named Caveats

C1 - On-disk state:
`system_v6/sims/round3_s5_heavy_discriminator_v0/` is currently untracked in
this checkout. This verdict accepts current on-disk evidence only; it does not
make the packet committed repo truth.

C2 - Wizard route truth:
Wizard v4.2 Max Assembly was partial in this audit. No Codex-native
`spawn_agent` tool was exposed, so no full parent/child council topology or
worker plurality is claimed. Evidence is direct repo inspection, scratch
recomputation, result inspection, and fresh read-only generic validators.

C3 - R3.5 basin language:
R3.5 survives quotient `56/56` and fixed-row equality before dying on
time-flow/N01. Its raw 33-cell transition graph hash differs from the anchor,
so future citations must not call it a full graph/basin alias. Basin language
is chart-relative only.

C4 - Packet-local validator freshness:
The packet-local validator was not rerun in place due to the write restriction.
Existing validator evidence is green; fresh generic validators including
`--require-pytorch` were rerun and green.

C5 - Quotient row scope:
The `56/56` row is exactly the packet's registered ordered off-diagonal
`A,b`-signature quotient. It is not global uniqueness or a chart-independent
quotient theorem.

C6 - PyTorch scope:
PyTorch/PyG is genuinely load-bearing for the finite graph carrier, not for the
exact symbolic terrain witnesses.

C7 - SMT depth:
SMT binds computed integer witnesses with flip controls. Surd expressions,
time-flow charpolys, fixed-point forms, and N01 formulas remain CAS/source
computed, not solver-derived from first principles.

## Future-Citation Rule

Future citations may say:

```text
round3_s5_heavy_discriminator_v0 is accepted as a bounded S5 phase-2
heavy-local scratch_diagnostic: all eight queued S5 rows from the S5 light
verdict were run under the registry de44219ed teeth; R3.1 alpha rows were
excluded by mirror-structure plus full 8-row N01 signatures; R3.2 rows by
fixed-point/basin and N01 gap; R3.3 rows by validity/fixed-point/quotient
56/56; R3.5 by time-flow/N01 after genuine quotient survival; PyTorch/PyG is
load-bearing for the finite 33-cell graph rows; no S5 R3 co-survivor was
minted; S5 phase-2 is closed only for the registered queued rows.
```

Future citations must not say:

```text
S5 uniqueness is proved; the S5 registry alternative space is exhaustive beyond
its finite declaration; R3.5 is a raw graph alias; basin labels are
chart-independent; PyTorch proved the symbolic terrain witnesses; SMT proved
the full terrain canonical tuple; the packet is canonical by process; the
remaining S2/S6-S7/S9 heavy queue is closed.
```
