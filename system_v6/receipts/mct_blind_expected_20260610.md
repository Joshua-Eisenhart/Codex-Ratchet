# BLIND expected values: mct_dynamic_admissibility_packet_v0

This file derives expected values only from `/tmp/mct_build_card_20260610.md` and the sources cited there. It makes no build claims.

## 1. Support counts

Prediction:

- `|S_0| = 384`.
- Sheets: `|S_0^L| = 192`, `|S_0^R| = 192`.
- Shells, all sheets: `128` samples per `eta_k`.
- Shells, per sheet: `64` samples per `(s, eta_k)`.
- Per `(s, eta_k, chi_j)`: `8` samples, one for each `phi_i`.
- Per `(s, eta_k, phi_i)`: `8` samples, one for each `chi_j`.

Derivation:

The PIN grid is `s in {L,R}`, `eta_k in {pi/8, pi/4, 3*pi/8}`, `phi_i = 2*pi*i/8`, `chi_j = 2*pi*j/8`, with `i,j=0..7`. Therefore `2*3*8*8 = 384`.

Source/PIN:

- Build card PIN block, `grid`: `|S_0| = 2*3*8*8 = 384 spinor samples`.
- Formal constraints and geometry, Hopf chart and Weyl sheet rows: `psi_s(phi,chi;eta)` with `s in {L,R}` and nested torus charts.

## 2. Density matrix, coordinate dependence, and fiber direction

Prediction:

For the pinned chart

```text
psi_s(phi_i, chi_j; eta_k)
  = ( e^{i(phi_i+chi_j)} cos(eta_k),
      e^{i(phi_i-chi_j)} sin(eta_k) )
```

write `c = cos(eta_k)` and `d = sin(eta_k)`. Then

```text
rho = psi psi^dagger
    = [[ c^2,                 e^{ 2 i chi_j} c d ],
       [ e^{-2 i chi_j} c d,  d^2               ]]
```

So `rho` depends on `eta_k` and `chi_j`, and does not depend on `phi_i`. The global-phase/fiber coordinate is `phi`.

Equivalent Bloch coordinates:

```text
r_x = sin(2 eta_k) cos(2 chi_j)
r_y = sin(2 eta_k) sin(2 chi_j)
r_z = cos(2 eta_k)
```

Derivation:

The common factor `e^{i phi_i}` multiplies both spinor components. It cancels in `psi psi^dagger`. The off-diagonal terms retain only the relative phase `2 chi_j`.

Source/PIN:

- Build card PIN block, `carrier_chart` and `rho = psi psi^dagger`.
- Formal constraints and geometry, spinor/Hopf chart and density reduction.
- `terrain rosetta strong math.md`, density reduction and fiber-blind reduction.
- `working_math_scaffold_20260609.md`, section 1.1, explicit density matrix and Bloch form.

## 3. Density-only quotient classes

Prediction:

- Per sheet, density-only quotient class count: `3 * 8 = 24`.
- Full support, density-only quotient class count from the source chart as written: `24`, because L/R have the same density rows in the cited chart and density-only probes do not include a sheet-separating row.
- If a sheet/chirality probe is included, or if the builder pins a sheet realization that changes computed probe rows, the full count becomes implementation-choice dependent. The build card requires at least one computed probe row to separate sheets, but that is not part of the density-only quotient unless explicitly included.

Identified sample pairs under density-only probes:

```text
(s, eta_k, phi_i, chi_j) ~ (s', eta_k, phi_i', chi_j)
```

for any `phi_i, phi_i'`, and, under the source chart as written, for either `s,s' in {L,R}`. Samples with different `eta_k` are not identified. Samples with different `chi_j` are not identified on the pinned `8`-point grid because `2 chi_j` has period `2pi` and `chi_j = j*pi/4` gives eight distinct `e^{2i chi_j}` values.

Per class size:

- Source-chart full-support density-only classes: `16` samples each: `2` sheets times `8` phi values.
- If sheets are kept separate by an active non-density row: `8` samples per class and `48` full-support classes.

Derivation:

Density depends only on `(eta_k, chi_j)`. There are `3` eta shells and `8` chi values. The `phi` coordinate is invisible to density.

Source/PIN:

- Build card G2: phi-blindness must emerge when `P_phase` is excluded.
- `terrain math.md:43-49`: fiber density path is stationary, base density path changes density.
- `mct_reconciled_spec_20260609.md`: quotient `x ~_t y iff` all active probes agree.

## 4. Global phase shift effects on pinned probe families

Prediction for `psi -> e^{i alpha} psi`, equivalently `phi -> phi + alpha`:

- `P_density`: invariant. `rho` and Bloch coordinates are unchanged.
- `P_shell`: invariant. `eta_k` is unchanged.
- `P_loop`: invariant for the row that records loop class/fiber-vs-base distinction. The shift itself is fiber/global phase motion; it does not turn a fiber row into a base row.
- `P_order`: invariant when computed from `rho`, Bloch rows, or committed density-channel/operator outputs, because the density input is unchanged.
- `Axis0-gradient` readout rows: invariant. `eta_k` and `b0` are unchanged.
- `P_phase`: separates in general. A phase-sensitive overlap with a fixed reference transforms by a factor depending on `alpha`, so bins may change.

Boundary on `P_phase`:

Exact separation depends on the pinned reference spinor and bin edges. `alpha = 0 mod 2pi`, and any bin collision induced by the builder's finite bins, will not separate. The card pins the existence of a phase-sensitive non-density probe, not its exact bin edges.

Derivation:

Global phase cancels in `psi psi^dagger`, but not in raw spinor overlaps against a fixed reference.

Source/PIN:

- Build card probe-family PIN: `P_phase` is the phase-sensitive non-density probe whose presence/absence makes phi-blindness emerge or not.
- Hopf/fiber source rows: density reduction is fiber-blind; inner/fiber loop is density-stationary.

## 5. Axis0-gradient readout `b0`

Prediction:

```text
eta = pi/8    -> cos(2 eta) = cos(pi/4)  =  sqrt(2)/2  -> b0 = +1
eta = pi/4    -> cos(2 eta) = cos(pi/2)  =  0          -> b0 = 0
eta = 3*pi/8  -> cos(2 eta) = cos(3pi/4) = -sqrt(2)/2  -> b0 = -1
```

Counts:

- All sheets: `128` samples for each `b0` value `+1`, `0`, `-1`.
- Per sheet: `64` samples for each `b0` value.

Derivation:

The PIN defines `b0 = sign(cos(2*eta_k))` with `0` at the boundary shell.

Source/PIN:

- Build card PIN block, `Axis0-gradient READOUT ROWS`.
- Formal constraints and geometry, Hopf connection `A = dphi + cos(2eta)dchi`.

## 6. Sidecar 8-state fixture expectations

Prediction for the reconciled sidecar fixture:

```text
S_0 = {0,1,2,3,4,5,6,7}
p1(x)=x mod 2
p2(x)=x mod 4
E_0={(x,(x+1) mod 8)}
```

Pinned table:

| t | operation | `|S_t|` | probes | `|Q_t|` | class sizes | `H_Q` | `A_Q` | `|E_t|` erase | `|E_t|` retain | `cc_weak` | `|Adm_t|` |
|---|---:|---:|---|---:|---|---:|---:|---:|---:|---:|---:|
| 0 | initial | 8 | `{p1,p2}` | 4 | `2,2,2,2` | 2.0 | 1.0 | 8 | 8 | 1 | 4 |
| 1 | drop `p2` | 8 | `{p1}` | 2 | `4,4` | 1.0 | 2.0 | 8 | 8 | 1 | 4 |
| 2 | add opposite edges | 8 | `{p1}` | 2 | `4,4` | 1.0 | 2.0 | 16 | 16 | 1 | 4 |
| 3 | fold `x mod 4` | 4 | `{p1'}` | 2 | `2,2` | 1.0 | 1.0 | 4 | 8 | 1 | 2 |

Required answer to the card's sidecar question:

- `|E_3| = 4` under `self_loop_policy = erase`.
- `|E_3| = 8` under `self_loop_policy = retain`.

Derivation:

The reconciled spec pins both folded self-loop policies and the t=3 edge counts.

Source/PIN:

- Build card choice points and G5: sidecar fixture must reproduce `|E_3| = 4 erase / 8 retain`.
- `mct_reconciled_spec_20260609.md`, sections 5.1-5.3.

## 7. Order-gap predictions from committed operator forms

Prediction, generically for nontrivial parameters:

Zero-gap / commuting controls:

- `Ti` with `Fe`: commute. `Ti` is Z-basis dephasing; `Fe` is Z-axis phase rotation.
- `Te` with `Fi`: commute. `Te` is X-basis dephasing; `Fi` is X-axis rotation.
- `Ti` with `Te`: commute as Bloch-axis diagonal contractions: `Ti` scales `(r_x,r_y)` and preserves `r_z`; `Te` preserves `r_x` and scales `(r_y,r_z)`, so the two diagonal scaling maps commute.
- Any operator with identity/trivial parameter settings commutes: `q=0`, rotation angle `0 mod 2pi`, or other degenerate choices.

Nonzero-gap / noncommuting pairs:

- `Fi` with `Fe`: nonzero in general. Rotations about X and Z do not commute except at degenerate angles or special states on invariant axes.
- `Ti` with `Fi`: nonzero in general. Z-dephasing and X-rotation do not commute because X-rotation mixes `r_y/r_z` while Z-dephasing scales `r_y` but not `r_z`.
- `Te` with `Fe`: nonzero in general. X-dephasing and Z-rotation do not commute because Z-rotation mixes `r_x/r_y` while X-dephasing preserves `r_x` and scales `r_y`.
- `Ti` with generic terrain maps whose density generator mixes Z populations/coherences: nonzero unless the terrain map is Z-covariant for the chosen observable/state.
- `Te` with generic terrain maps that mix X-axis components: nonzero unless X-covariant for the chosen observable/state.

Implementation-dependent part:

The exact nonzero norm depends on the builder's pinned parameters (`q_1`, `q_2`, rotation angles, terrain-generator coefficients), the selected observable `O`, and the order-gap norm bins. The sign classification above follows from the committed operator forms; exact magnitudes do not follow from the build card alone.

Derivation:

In Bloch form, `Ti` is a Z-dephasing contraction, `Te` is an X-dephasing contraction, `Fi` is an X rotation, and `Fe` is a Z rotation. Same-axis dephase/rotation commute; different-axis rotation/dephase pairs generically do not. X and Z rotations generically do not commute.

Source/PIN:

- Build card G4 requires committed `Ti/Te/Fi/Fe` forms and a commuting control pair plus a noncommuting pair.
- `operator math explicit.md`: `Ti` Z-basis dephasing, `Te` X-basis dephasing, `Fi` `U_x(theta)`, `Fe` `U_z(phi)`.

## 8. Five operation predictions on the pinned geometric support

### Compression: drop `P_phase`

Prediction:

- Carrier-retained mode: raw `|S_t|` stays `384`.
- Density-only quotient after dropping `P_phase`: `24` full-support classes under the source chart as written, or `48` if an active sheet-separating row is retained.
- `A_Q` rises relative to a phase-resolving active family because each class contains more raw spinor samples.
- `H_Q` should be reported by name. For uniform many-to-one merging, `H_Q` over quotient classes decreases when the number of equally weighted classes drops.
- `support_size` must be named separately from quotient count. In `quotient_materialized` side branch, materialized support size drops to the quotient class count.
- `possibility_mass` direction is not determined by the card unless the builder pins `Poss_t(x)` semantics for the geometric support.

Derivation:

Dropping probes coarsens the equivalence relation. Here dropping phase removes the only row that can see global `phi`.

Source/PIN:

- Build card G5 compression row: dropping `P_phase` makes `support_size of Q_t` drop and `A_Q` rise.
- `mct_reconciled_spec_20260609.md`, choice points: name `H_Q`, `A_Q`, `support_size`, `possibility_mass` separately.

### Expansion: add a probe, especially `P_phase`

Prediction:

- Classes split or stay the same; they cannot merge under ordinary probe addition.
- Adding `P_phase` to density-only rows separates at least some samples that differ only by `phi`, subject to bin/reference collisions.
- `A_Q` falls when phase distinctions split formerly merged classes.
- `H_Q` rises for uniform splits, but exact value depends on phase binning.
- Raw carrier `support_size` stays `384` in carrier-retained mode.
- `possibility_mass` may increase if the expansion is modeled as represented-resolution growth; not pinned by the card for the geometric support.

Derivation:

Adding a probe refines the key used for `~_t`.

Source/PIN:

- Build card probe-family PIN and G5 expansion row.
- Field-wide compression contract, compression/expansion finite quantities.

### Warping: finite delta update on `E_t`

Prediction:

- `E_t` relation rows change.
- Local density quotient counts do not change unless the warp also changes active probes, which is not pinned here.
- Relation-dependent readouts must change under at least one ablation/control.
- In the sidecar fixture, t=1 to t=2 adds opposite edges and `|E|` changes `8 -> 16`.

Derivation:

Warping is pinned as finite relation update `(E union Delta+) \ Delta-`.

Source/PIN:

- Build card choice points and G5 warping row.
- `mct_reconciled_spec_20260609.md`, relation update and t=2 sidecar fixture.
- Field-wide contract: relation ablation must affect at least one load-bearing readout.

### Folding: equivalence-respecting quotient/gluing

Prediction:

- Legal default fold must satisfy `ker(pi) subset ~_t`.
- For the sidecar `pi(x)=x mod 4`, the fold is valid at t=2 and gives `|S_3|=4`, `|Q_3|=2`, class sizes `2,2`, `H_Q=1.0`, `A_Q=1.0`.
- `|E_3|=4` if self-loops are erased; `|E_3|=8` if self-loops are retained.
- On the geometric support, exact folded support count is not pinned unless the builder pins the fold map. The expected invariant is nonincrease of support under fold and explicit loop policy for relation pushforward.

Derivation:

The reconciled spec pins equivalence-respecting folding as the default and the sidecar fold table.

Source/PIN:

- Build card choice points and G5 folding row.
- `mct_reconciled_spec_20260609.md`, sections 3 and 5.2-5.3.

### Reindexing: label permutation

Prediction:

- Declared invariants are byte-stable: `|S|`, density rows as multisets, quotient class multiset, `H_Q`, `A_Q`, `support_size`, `possibility_mass` if computed label-independently, `|Adm|`, and relation isomorphism class.
- Raw labels and label-specific rows change.
- A label-shuffle null should kill label-specific claims that are not transported through the permutation.

Derivation:

Reindexing is a bijective relabeling/transport control.

Source/PIN:

- Build card G5 reindexing row and controls.
- `mct_reconciled_spec_20260609.md`, label shuffle/reindex control.

## 9. Additional tightly pinned expectations

### Entropy bases

Prediction:

- Main geometric packet entropies use base `e`, because the build card pins `entropies base e`.
- The sidecar fixture table in the reconciled spec uses base `2`, because its table explicitly lists `H_Q=2.0` for four equal classes and `H_Q=1.0` for two equal classes.

Source/PIN:

- Build card PIN block, `entropies base e`.
- `mct_reconciled_spec_20260609.md`, section 5.3: `Entropy base: log2`.

### Density-only entropy if full-support source-chart quotient is used

Prediction:

- Full source-chart density-only quotient: `24` classes of equal size `16`.
- With base `e`, `H_Q = ln(24)`.
- `A_Q = ln(16)` if ambiguity is computed as average natural log class size to match the build-card entropy base.
- If sheet-separating rows are retained: `48` classes of equal size `8`, so `H_Q = ln(48)` and `A_Q = ln(8)`.

Implementation-dependent part:

If `A_Q` remains log2 by implementation convention while main entropies use base `e`, the numeric ambiguity values become `4` for class size `16` and `3` for class size `8`. The build card only pins entropy base `e`; it does not explicitly restate the ambiguity log base for the geometric packet.

### SMT phi-blindness obligation

Prediction:

- With only density/fiber-blind rows active, a solver query asking for a density-probe separator of same-`eta`, same-`chi`, different-`phi` samples should be `UNSAT`.
- With `P_phase` injected, or rows scrambled as an erased control, a separator can be `SAT`, subject to the exact pinned phase bins.

Source/PIN:

- Build card G7: z3 and cvc5 must derive phi-blindness separation from computed rows.

### Controls

Predictions:

- `phase-probe-included control`: phi-blindness must not appear; at least some same-density/different-phase samples split.
- `fiber-coordinate erasure`: kills phase-sensitive separation and should collapse global-phase distinctions under density rows.
- `shell-nesting erasure`: kills shell/eta gradient rows; it should prevent reproducing per-shell `b0` counts.
- `wrong-order update`: for fold/warp sidecar, strict policy makes `warp(0,4)` after fold invalid; permissive policy makes it self-loop/redundant.
- `relation-ablation`: relation readouts change, local density quotient and admissibility counts do not.
- `local-only baseline`: cannot reproduce a claimed field-wide readout if the readout is load-bearing on `E_t`.

Source/PIN:

- Build card controls list.
- `mct_reconciled_spec_20260609.md`, controls table.
- Field-wide compression contract, local-only kill condition and relation-ablation controls.

### Three-presentation consistency

Prediction:

For the same pinned support, flat-grid, spherical-shell, and nested-ring/Hopf-torus presentations should agree on:

- finite support counts: `384`;
- per-shell counts: `128` all sheets, `64` per sheet;
- eta-gradient rows: `b0` counts `128/128/128` over `+1/0/-1`;
- density-only quotient count: `24` full-support classes under source-chart density-only rows, unless an active sheet-separating row is included;
- phi-blindness under density probes.

Disagreement controls:

- Erasing shell nesting should break eta-gradient/shell agreement.
- Dropping the fiber coordinate should break phase-probe separation.
- Flattening to a board should remain a control/baseline, not a nonclassical claim path.

Source/PIN:

- Build card G8.
- Ring-checkerboard runbook, three presentations and candidate-equivalence warning.
- `system_v6/README.md`: NumPy is baseline/control only.
