# Fresh Audit Verdict - basin_grid_refinement_control_v0

Auditor: codex1 cross-backend audit.
Scope: read-only audit of codex2 builder packet, except this verdict file.
Standard: calibrated bar, basin contract, committed parent sweep `ba1bfc4d1`, and CAVEAT C1 adjudication.

## Bottom Line

VERDICT: EARNED AS FINITE-CHART STRUCTURE; KILLED AS INVARIANT GEOMETRY.

The packet genuinely closes CAVEAT C1 for `G1`: the three committed rotation terminal classes persist under the declared deterministic 2x and 3x child-grid refinements, but they do not survive a pinned non-axis chart rotation. Under the rotated 33-cell-density grid, committed classes `0` and `1` merge into one terminal class and committed class `2` (origin) remains separate. The correct reading is therefore not "the three rotation sub-basins" as invariant geometry. It is "three terminal classes in the original finite grid-frame probe family."

Classification by the earn-the-term ladder:

- KILLED as invariant continuum or frame-independent basin geometry.
- EARNED as finite-resolution, chart-relative terminal communicating classes at the F01-privileged finite scale, for the declared original grid-frame and its deterministic 2x/3x containment refinements.
- NOT promoted beyond `scratch_diagnostic`; `promotion_allowed=false`, `formal_admission_allowed=false`.

Future citations should say: "The `ba1bfc4d1` G1 rotation split stands as finite chart-relative terminal structure: 3 classes in the original 33-cell chart, persisting under the declared 66/99 child grids, but changing to 2 terminal classes under the pinned non-axis rotated chart. It must not be cited as invariant geometric sub-basins or as THE rotation sub-basins."

## Commands And Recomputations

No `git add` or `git commit` was run. No packet result JSON was overwritten.

I avoided running packet entrypoints that write result JSONs. Fresh recomputation used import/build functions and stdout summaries only:

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY' ... import basin_grid_refinement_control_v0_jax; build_result() ... PY`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY' ... import basin_grid_refinement_control_v0_pytorch; build_result() ... PY`
- `julia --project=system_v5/julia_carrier - <<'JL' ... include_string(... without exit(main())) ; build_result() ... JL`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY' ... import validate_basin_grid_refinement_control_v0; validate_leg/validate_envelope/scan ... PY`
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v6/sims/basin_grid_refinement_control_v0/results/basin_grid_refinement_control_v0_envelope_results.json`

Fresh stdout recomputes:

```text
jax:     all_pass=true, classification=scratch_diagnostic
pytorch: all_pass=true, classification=scratch_diagnostic
julia:   all_pass=true, classification=scratch_diagnostic
```

The imported packet validator returned:

```text
ok=true
errors=[]
mode=imported_validator_no_write
```

The generic source-backed validator returned:

```text
ok=true
result_json=system_v6/sims/basin_grid_refinement_control_v0/results/basin_grid_refinement_control_v0_envelope_results.json
```

## Check 1 - Persistence Under 2x/3x Refinement

PASS for the declared finite containment map.

The anchor is byte-exact against the committed parent sweep:

```text
parent path: system_v6/sims/basin_generating_set_sweep_v0/results/basin_generating_set_sweep_v0_envelope_results.json
parent commit hint: ba1bfc4d1
state_count: 33
parent/local terminal_class_count: 3
parent transition_graph_sha256: 38388af4497894e6e88f11de6f9ec633235f26753d2c657ff8f360b3ce15871d
exact rederived transition_graph_sha256: same
```

Fresh recomputed refinement fates:

```text
2x_density_refined_grid:
  state_count=66
  terminal_class_count=3
  terminal_class_sizes=[1,24,28]
  overall_fate=PERSIST
  class_fates={0:PERSIST, 1:PERSIST, 2:PERSIST}
  terminal_to_committed_class_overlap={0:[0], 2:[1], 6:[2]}

3x_density_refined_grid:
  state_count=99
  terminal_class_count=3
  terminal_class_sizes=[1,40,53]
  overall_fate=PERSIST
  class_fates={0:PERSIST, 1:PERSIST, 2:PERSIST}
  terminal_to_committed_class_overlap={0:[0], 2:[1], 5:[2]}
```

Adjudication: the containment map is genuine for this packet because the refined terminal classes are recomputed from transition edges, then matched back to committed classes through explicit `parent_cell_id` containment overlap. It is not a dense-limit theorem. The build card and result both name the refinement rule as deterministic child cells inside each committed cell containment region, with no dense carrier.

Named caveat C1A - finite containment only: this proves persistence for the declared 2x/3x child grids, not arbitrary refinements, random refinements, or a continuum grid limit.

## Check 2 - Frame Dependence / Rotated Grid

PASS. The rotated grid gives 2 terminal classes, not 3, and the change is structural.

Pinned frame:

```text
axis=[1.0,1.0,1.0]
angle=pi*(sqrt(2)-1)
angle_radians=1.3012902845685732
cell_count=33
```

The axis is genuinely non-axis relative to the coordinate frame used by the original grid. The rotated control keeps the same 33-cell density, so the `3 -> 2` change is not explained by a larger or smaller cell count.

Fresh recomputed rotated fate:

```text
rotated_33_cell_density_grid:
  state_count=33
  terminal_class_count=2
  terminal_class_sizes=[1,32]
  overall_fate=CHANGED
  class_fates={0:MERGE, 1:MERGE, 2:PERSIST}
  terminal_to_committed_class_overlap={0:[0,1], 1:[2]}
```

Adjudication: this is a class-structural frame-dependence result. In the rotated chart, committed classes `0` and `1` share the same terminal class. The origin class persists separately. Because 66/99 refinements preserve 3 classes while the same-density rotated grid gives 2, the decisive variable is the grid-frame probe, not cell count.

Named caveat C1B - chart relativity: by probe-relative identity discipline (`a=a iff a~b`), the original three classes are identical only relative to the original grid-frame probe family. A probe-frame change changes the object, so the object must be labeled chart-relative.

## Check 3 - Continuum Derivation

PASS as packet derivation; NOT mechanically proved as a density theorem.

The packet's continuous cross-check records:

```text
continuous_generator_family=rotations only; offsets are zero for R_x/R_z/Ne_Spiral_R/Ne_Vortex_L
closure_result=SO(3)
h_time_step_role=Ne terrain rotations enter as exp(hA) with h=1/2; the observed Ne rotation angle is 1 radian, not a grid angle.
```

Generator angles:

```text
R_x:         angle_radians=1.570796326795, angle_over_pi=0.5
R_z:         angle_radians=1.570796326795, angle_over_pi=0.5
Ne_Spiral_R: angle_radians=1.0, angle_over_pi=0.318309886184
Ne_Vortex_L: angle_radians=1.0, angle_over_pi=0.318309886184
```

The packet's derivation says:

```text
R_x and R_z generate the cube rotation subgroup. The Ne rotations are about the non-axis (1,1,1) family with angle 1 radian; this is not one of the finite SO(3) subgroup angles. Conjugating that circle by the cube rotations supplies nonparallel axes whose Lie algebra spans so(3).
```

Continuum invariant conclusion:

```text
one recurrent orbit class per radius sphere, plus the fixed origin; with radius erased, the admitted ball is one continuum recurrent basin under SO(3) closure
```

Adjudication: the continuum side supports killing the invariant-geometry reading of the three finite classes. It also keeps the correct caveat: SO(3) recurrence preserves radius, so "one continuum basin" is only after radius erasure. Without radius erasure, the continuum decomposition is per-radius-shell plus the fixed origin.

Named caveat C1C - derivation, not formal closure proof: the SO(3) closure and irrational-angle argument are recorded as a source derivation and recomputed numeric/symbolic rows, not as a dedicated symbolic density theorem or SMT proof over SO(3).

Named caveat C1D - radius erasure: the packet is honest that shell radii are erased before claiming one continuum recurrent basin. Future wording must not claim one radius-preserving continuum basin.

## Check 4 - Knock-On To `ba1bfc4d1` G1/G3 Splits

CAVEAT C1 is resolved by relabeling, not by deleting the finite split rows.

The committed sweep's split rows stand as finite chart structures. They are demoted only if future prose had been treating them as invariant geometry. The corrected vocabulary is:

```text
Allowed:
  finite chart-relative terminal classes
  finite grid-frame split row
  original 33-cell chart G1 terminal classes
  G1 3-class split in the original chart, persistent under declared 2x/3x containment refinements
  rotated-chart G1 2-class merge result

Forbidden:
  invariant rotation sub-basins
  THE rotation sub-basins
  continuum geometric sub-basins
  frame-independent G1 basin geometry
```

For `G1`, future citations may say:

```text
The original `ba1bfc4d1` G1 row has three finite terminal communicating classes on the 33-cell chart. `basin_grid_refinement_control_v0` shows these three classes persist under declared 2x/3x containment refinements but merge to two terminal classes under a pinned non-axis rotated chart; therefore the split is finite chart-relative structure, not invariant continuum geometry.
```

For `G3L/G3R`, future citations should be slightly weaker unless a matching rotated/refined chirality control is run:

```text
The `ba1bfc4d1` G3L/G3R rows are finite 33-cell chart split rows from the committed sweep. They should inherit the chart-relative vocabulary discipline and should not be cited as invariant geometric sub-basins without their own frame/refinement controls.
```

## Check 5 - Standard Controls

PASS with named helper-drift caveat.

Observed and/or recomputed controls:

```text
G0 robustness anchor:
  G0_2x_density_refined_grid terminal_class_count=1, state_count=66
  G0_3x_density_refined_grid terminal_class_count=1, state_count=99

Designed-fail axis artifact:
  construction=axis-snapped fake class: cells with world-coordinate z exactly 1/2
  base_axis_grid member_count=9, closed_under_G1=false, escaping_edge_count=16
  rotated_grid member_count=1, closed_under_G1=false, escaping_edge_count=2
  dies_under_rotation=true

SMT/proof flips:
  z3 verdict=unsat, erased_flip_verdict=sat
  cvc5 verdict=unsat, erased_flip_verdict=sat
  julia_z3 verdict=unsat, erased_flip_verdict=sat

Engine agreement:
  lanes=[jax,julia,pytorch]
  rotated terminal counts={jax:2.0, julia:2.0, pytorch:2.0}
  max_divergence=0.0
  key_summary_agreement=true
```

Q5 packet fields present:

```text
classification=scratch_diagnostic
promotion_allowed=false
formal_admission_allowed=false
seed_ledger={rng:none, deterministic_tie_break:cell_id_ascending}
parent_lineage includes ba1bfc4d1, 631f1c3db, 000f48e71
capability_receipts present for jax/julia/pytorch
tool_calls present for jax/julia/pytorch
one_to_one_tool_calls.pass=true
existing packet validator result ok=true, errors=[]
generic source-backed validator ok=true
```

Named caveat C1E - helper API drift: the stored envelope records `build_helper_path=scripts/build_three_engine_envelope.py` and a helper hash, and the generic source-backed validator accepts the stored envelope. However, a fresh no-write call to the current packet envelope builder failed against the current dirty helper because `scripts/build_three_engine_envelope.py` now requires `lanes.<engine>.package_observables` for load-bearing packages. This is current helper/packet API drift, not evidence that the stored transition fates are false. It blocks a clean fresh envelope rebuild until the packet envelope lanes are updated with exact package observables or the helper drift is reconciled.

## Accepted Ceiling

Accepted status label: `passes local rerun` for the no-write recomputed backend summaries and validator checks in this audit; stored packet classification remains `scratch_diagnostic`.

Evidence paths:

- `system_v6/sims/basin_grid_refinement_control_v0/build_card.md`
- `system_v6/sims/basin_grid_refinement_control_v0/basin_grid_refinement_control_v0_common.py`
- `system_v6/sims/basin_grid_refinement_control_v0/basin_grid_refinement_control_v0_jax.py`
- `system_v6/sims/basin_grid_refinement_control_v0/basin_grid_refinement_control_v0_pytorch.py`
- `system_v6/sims/basin_grid_refinement_control_v0/basin_grid_refinement_control_v0_julia.jl`
- `system_v6/sims/basin_grid_refinement_control_v0/results/basin_grid_refinement_control_v0_envelope_results.json`
- `system_v6/sims/basin_grid_refinement_control_v0/results/basin_grid_refinement_control_v0_validator_results.json`

Blocked consumers:

- invariant basin geometry
- continuum sub-basin claims
- frame-independent G1/G3 language
- formal admission
- any citation that erases the radius-shell caveat

Next unblocked step:

Run a packet repair that adds current-helper `package_observables` to the envelope lane records, then rerun the envelope builder and both generic source-backed validators. Separately, if stronger continuum language is desired, build a dedicated symbolic closure proof for the SO(3)/irrational-angle argument and a radius-preserving vs radius-erased statement check.
