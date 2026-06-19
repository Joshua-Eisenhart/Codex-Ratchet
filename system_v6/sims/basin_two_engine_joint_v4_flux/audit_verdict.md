# Fresh audit verdict: basin_two_engine_joint_v4_flux

Bottom line: VERDICT = GENUINE-WITH-CAVEATS.

This packet genuinely adjudicates the owner flux refinement at `scratch_diagnostic` ceiling. Stage 1 is a scoped positive: the signed flux sector is live in the update law, changes the within-engine terminal cores relative to the corrected v3 flux-blind baselines, and the `D_matrix64_b_order_overlay` row produces a real L/R difference under the declared terminal-structure probe. Stage 2 is a scoped negative for the pre-registered joint 64: no source-valid primary coupling row in this bounded table realizes 64.

Prediction-adjudication sentence:

`Under the basin_two_engine_joint_v4_flux signed-holonomy-sector realization, Stage 1 is positively adjudicated in the realization-relative sense: flux changes the within-engine terminal cores versus the corrected v3 baselines (A=28, D=24), and D_matrix64_b_order_overlay is L/R-different under the declared probe (L: one terminal class of size 48; R: two terminal classes of size 24 and 24), with sign-flip mirroring. Stage 2 is negatively adjudicated for the owner pre-registered joint 64 in this bounded source-table sweep: source-valid primary rows yield A counts 16/1/3/28/12 and D counts 12/2/2/24/12, so source_valid_primary_64_level_count=0. This is not a canonical confirmation or canonical disproof of the owner prediction family.`

Future-citation rule:

`Cite basin_two_engine_joint_v4_flux only as a local uncommitted scratch diagnostic that passes local rerun for this declared signed flux-bit realization: Stage 1 shows a live flux-coupled terminal-core effect and a sign-mirrored D-row L/R difference; Stage 2 shows no source-valid primary 64 in the bounded C1/C2/O6/C5 sweep. Do not cite it as canonical flux doctrine, a canonical disproof of 64, proof that all source-faithful couplings are exhausted, or proof that core-size doubling alone creates new subsubbasins.`

## What I Checked

Read-first surfaces:

- `system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md`
- `system_v6/receipts/coupling_law_family_table_20260611.md`
- `system_v6/sims/basin_two_engine_joint_v4_flux/build_card.md`
- all v4 source files, all v4 result JSONs, the v3 convention-sweep envelope, and the relevant flux parent result objects.

Fresh commands:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/basin_two_engine_joint_v4_flux/validate_basin_two_engine_joint_v4_flux.py
```

Result: `ok=true`, `errors=[]`.

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/basin_two_engine_joint_v4_flux/results/basin_two_engine_joint_v4_flux_envelope_results.json
```

Result: `ok=true`.

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/basin_two_engine_joint_v4_flux/results/basin_two_engine_joint_v4_flux_envelope_results.json
```

Result: `ok=true`.

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/basin_two_engine_joint_v4_flux/tests/test_basin_two_engine_joint_v4_flux.py
```

Result: `5 passed in 101.44s`.

Audit hygiene note: the packet-local validator writes its validator result JSON. I ran it before noticing that it is not read-only. I removed only pytest/import `__pycache__` artifacts afterward. I did not run `git add`, commit, or stage anything.

## Stage 1

The stage-1 reality check passes with caveats.

Independent recomputation of the finite dynamics found:

| row | engine | flux-erased terminal core | flux-carried terminal core |
|---|---:|---:|---:|
| A_readout_transition_dwell | L | 1 x 28 | 1 x 56 |
| A_readout_transition_dwell | R | 1 x 28 | 1 x 56 |
| D_matrix64_b_order_overlay | L | 1 x 24 | 1 x 48 |
| D_matrix64_b_order_overlay | R | 1 x 24 | 2 x 24 |

This is not merely "state space doubled, therefore claim proven." The transition law computes the next base state first, then flips the signed sector only on boundary crossings satisfying the chirality/readout condition. The terminal classes have absent-exit proofs and are earned as SCC terminal cores, not declared classes.

The definitional/product concern still matters. In A and D/L, the core-size doubling is weak evidence by itself because it can read as the terminal core traversing both flux sectors on the same base support. The strongest non-product stage-1 evidence is D/R: two terminal classes over the same 24-base-state support, split by flux phase. That is a discovered terminal-structure difference under the declared probe, not a frozen-factor count.

The sharp L/R claim is the D row:

- `D_matrix64_b_order_overlay`, original signs: L = one terminal class of size `48`; R = two terminal classes of sizes `24,24`.
- Sign-flip control: L becomes `2 x 24`; R becomes `1 x 48`.
- This exactly mirrors the L/R structure, so the observed difference is traceable to opposite flux signs in this realization, not merely to an unmirrored L/R implementation asymmetry.

A row is not L/R-different: both sides are `1 x 56`.

## Flux Provenance

The signed bit is not a completely free bit named "flux"; it is grounded as a finite signed holonomy-sector realization of committed flux objects:

- `flux_emergence_discriminator`: records `Chern=1`, bare-spinor kills flux, single-shell has holonomy but no second rung for relative flux, and ratchet scramble changes ordered adjacent fluxes while preserving absolute Chern.
- `geo_s9_alternative_connections_v0`: records that the committed Hopf connection is unique under the tested leaf holonomy spectrum and annular flux rows; same-`c1` alternatives die on geometric flux/holonomy rows.
- `ratchet_s2_two_shell_flux_v0`: records physical annular flux `pi/2`, boundary holonomy difference `pi/2`, and Z4 quotient survival of the flux row.

Caveat: the v4 signed variable does not numerically carry the full parent holonomy spectrum or `pi/2` annular flux value through the update law. It consumes the parent estate as a two-valued signed sector plus O1 chirality direction. That is admissible for a bounded realization-relative basin test, but future work must not cite it as direct full-geometry flux consumption.

## Stage 2

The stage-2 negative is real for this bounded table.

Independent recomputation of all primary rows matched the envelope:

| base row | C1 constrained fibered | C2 fibered | O6 double cover | C5 alternating | C5 paired |
|---|---:|---:|---:|---:|---:|
| A_readout_transition_dwell | 16 | 1 | 3 | 28 | 12 |
| D_matrix64_b_order_overlay | 12 | 2 | 2 | 24 | 12 |

No source-valid primary row realizes `64`; no near-64 row appears under the packet's `56/64/72` near-candidate rule.

O2 is respected in the table shape: bare sync and full-interleave are fenced as non-source-faithful contrasts, not primary rows. The product-coupling control is present and excluded:

- A product control: factor counts `L=1`, `R=1`, product count `1`, excluded.
- D product control: factor counts `L=1`, `R=2`, product count `2`, excluded.

The owner falsifier is mixed, not global. Most source-faithful flux-carrying rows do not repeat the v3 flux-blind sync counts. But `C5_strategy_alternating_period2` exactly repeats them: A gives `28` and D gives `24`. Therefore the flux-blindness explanation is killed for those C5 alternating rows, but not killed uniformly across the whole bounded sweep.

## Controls

Flux-erased continuity:

- The packet reports `flux_erased_reproduces_v3_counts=true`.
- I performed a normalized byte check on `D_matrix64_b_order_overlay/sync`: v3 and v4 flux-erased row objects over `terminal_class_count + terminal_sizes` both hash to `594929485ed356627412055d805e1ae3bb1e4fb3c235350402594f75f097bb0a`.

Order-shuffle:

- Every primary stage-2 row changed terminal structure under the B order-shuffle control in independent recomputation.
- Stage 1 has one caveat: A/R's stage-1 order-shuffle did not change terminal structure, while the stage-2 primary rows still changed under order-shuffle.

Label-permutation:

- Counts are label-invariant because the transition law consumes directed positions, active readout signs, and flux signs rather than literal stage-label strings.
- Caveat: the packet's label-permutation control is analytical/static; it returns the same signature rather than constructing a separately permuted graph. This is not load-bearing for the main result, but future validators should make it an executable permutation.

Frozen-factor projection:

- All four one-sided rows are fenced and detect frozen-factor echo.
- Observed echo counts: A L-only `64`, A R-only `64`, D L-only `64`, D R-only `128`.
- These rows are not primary evidence.

## SMT, Engines, Ceiling

SMT is honest for computed-count identity, not for deriving SCCs from first principles. z3 and cvc5 bind measured count rows, make negated mismatch UNSAT, and the flipped expected-count control SAT. Julia Z3 mirrors this. The `asserted_precomputed_boolean=false` row is present.

Cross-engine scope is adequate for `GENUINE-WITH-CAVEATS`:

- Julia recomputes terminal counts through Graphs.jl/Z3.jl and does not read peer result files.
- JAX/Python carries the full richer lattice and uses NetworkX plus z3/cvc5/sympy.
- PyTorch uses `torch.func` and `torch_geometric` for graph-carrier checks plus z3/cvc5/sympy.
- All three engines agree on the primary terminal-count map and `source_valid_primary_64_level_count=0`.

The envelope is correctly fenced:

- `schema_version=three_engine_sim_result_v1`
- `mode=all_three_full_sims`
- no omitted lanes
- `classification=scratch_diagnostic`
- `promotion_allowed=false`
- `formal_admission_allowed=false`

## Named Caveats

- G1 `core_size_not_class_creation`: A `28->56` and D/L `24->48` are terminal-core size changes, not new terminal-class creation. They should not be cited alone as flux-created subsubbasins.
- G2 `coarse_flux_realization`: the signed sector is grounded in committed flux/holonomy objects, but it is a coarse two-valued realization rather than direct numeric propagation of the full flux estate.
- G3 `C5_partial_falsifier`: C5 alternating repeats the flux-blind sync counts, so the flux-blindness explanation is killed for those rows even though other primary rows differ from v3.
- G4 `candidate_coupling_scope`: C1/C2/C5 are candidate rows from the coupling-law table, not owner-source binding laws. O6 is the owner-source concrete joint candidate. The negative is bounded to this table.
- G5 `label_control_static`: label permutation is not an independently rebuilt graph. It is not main load-bearing evidence, but it should be hardened.
- G6 `SMT_scope`: solver checks bind computed count identities and flipped expected-count controls; they do not independently prove graph reachability.
- G7 `untracked_artifact_scope`: the audited packet directory is currently untracked in this checkout, so cite as local artifact evidence unless and until committed.

Accepted status label: `passes local rerun` for the validator, strict three-engine validators, pytest, and targeted recomputation above; claim ceiling remains `scratch_diagnostic`.

## Sweep 3 Correction Annotation

G8 `D_R_IS_Z2_SECTOR_DECOMPOSITION_NOT_FLUX_MIXING`:
The D/R `24+24` terminal split is a `Z/2` sector decomposition under the global flux-sign symmetry of the R dynamics, not dynamically emergent flux-phase mixing. The two terminal classes are symmetry images under flipping all flux signs, and both terminals contain both flux values; the sector a transient R state reaches is determined by its initial flux sign. The stage-1 citation is therefore corrected to: D/R shows a symmetry-sector L/R difference for the declared probe, while A is the genuinely mixed case over both flux sectors in one terminal. Future citations must not call D/R `24+24` evidence that flux phases mix non-trivially between engine loops.

Registration/cross-citation note: this correction carries the Sonnet late-finding registration entry `40f010040` for the stage-1 wording change and cross-cites the panel-6 criterion `eba5fdca0`. It preserves the stage-2 negative: no source-valid primary coupling row realizes the pre-registered joint `64` in this bounded table.
