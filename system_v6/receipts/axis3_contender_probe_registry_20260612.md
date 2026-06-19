# Axis-3 Contender-Probe Registry - 2026-06-12

Purpose: register the alternative Axis-3 placement readout-probe space before
any readout is citable as THE Axis-3 readout.

Scope: registry receipt only. No sims were run. No result JSON was rewritten.
This file defines finite candidate representatives, alias-class detection,
expected teeth rows, closeness grades, and cost classes for a later contender
sweep packet.

Evidence ceiling: `scratch_diagnostic` planning/registry receipt.
`promotion_allowed: false`
`formal_admission_allowed: false`

## Source Hash Ledger

- Doctrine anchor: `owner_doctrine_axes_as_existence_probes_20260612.md`, commit
  `fcf1b3858`, which requires a contender registry per axis before "the readout"
  language.
- Registry-format template: `axis0_contender_probe_registry_20260612.md`, commit
  `31dfd11b6`.
- Boundary audit standard: `axis0_contender_heavy_v0/audit_verdict.md`, commit
  `c27d3dd39`; the distinction-boundary predicate must be computable and able
  to admit true contenders, not merely exclude alternatives.
- Axis-3 anchor packet: `discrete_axis3_placement_v0`, commit `ce8c77355`.
- Section-phase estate alternative: `hopf_base_section_phase_recovery_v0`, commit
  `7e78f3829`.
- Work-order source: `axis_work_order_20260612.md`, which names Axis-3 as
  placement `(fiber/base)` and preserves Type1/2 inversion, L/R chirality, and
  flux in-out as live alternatives.
- Scaffold source: `working_math_scaffold_20260609.md`, which records
  `gamma_f`/`gamma_b`, density-stationary versus density-visible loops, and
  Axis-3 alternatives.

## Axis-3 Distinction Boundary

Contenders must read the same distinction: placement of a Hopf loop as
fiber/phase/density-stationary versus base/density-visible/horizontal. A probe
that primarily reads Axis-0 response polarity, Axis-6 operator/terrain
precedence, Axis-4 loop-order composition, terrain family, or flux geometry
without recovering the placement split is not an Axis-3 contender; it is a
different-axis or geometry probe.

Pinned distinction:

- `gamma_in`: fiber/inner loop, density-stationary.
- `gamma_out`: outer/base loop, density-traversing, with computed horizontal
  condition `A(dot gamma)=0`.
- anchor vocabulary: `axis3_minus_fiber_placed_gamma_in`,
  `axis3_plus_base_placed_gamma_out`, and
  `axis3_neutral_placement_degenerate`.

## Positive Boundary Predicate

A candidate reads the Axis-3 distinction only if all of the following are
computed on a finite pinned representative:

1. `loop_family_pin`: every row names the loop formula, carrier row or anchor,
   section/gauge convention, sheet/chirality convention, and adapter rule before
   classification.
2. `placement_reachability`: the candidate emits at least one admitted
   fiber/inner or density-stationary row and at least one admitted base/outer or
   density-visible row, or a declared neutral boundary control that is separate
   from the main representative.
3. `fiber_base_erasure_changes_vector`: erasing, swapping, or mutating the
   fiber/base loop predicate changes the candidate vector or demotes it to
   neutral/failed conditions.
4. `connection_or_density_control_fires`: at least one of the horizontal
   connection mutation, density-stationarity erasure, loop-family swap, or
   degenerate-pole control changes the row result.
5. `not_axis0_or_axis6_recoverable`: Axis-0 response and Axis-6 precedence keys
   do not deterministically recover the candidate vector under the declared
   shared rows or projection.
6. `not_constant_or_single_sign_vector`: the candidate is not all one sign
   except where the candidate is a named neutral control.

This predicate is intentionally positive: the anchor passes it, and a genuine
Type1/2, L/R, flux, holonomy, section-phase, or traversal-rate contender can
pass if it computes the same placement split under pinned adapters. The
predicate must not kill a candidate merely because it uses a different local
observable.

## Registry Contract

Every future sweep packet generated from this registry must predeclare:

1. `alternative_space_bound`: the finite candidate ids below, with no extra
   candidates added after results are inspected.
2. `carrier_pin`: the candidate carrier and row order, including whether the row
   lives on Family B Hopf anchors, a section-phase loop, or an adapter into a
   shared carrier.
3. `candidate_vector`: a finite vector over the pinned rows, with raw values and
   signs in `{-1,0,+1}` where `-1=fiber/inner/density-stationary`,
   `+1=base/outer/density-visible`, and `0=degenerate/neutral/failed`.
4. `canonical_alias_form`: computed before any teeth row. Exact aliases do not
   inflate the tested count.
5. `representative_selection_rule`: one representative per exact alias class;
   aliases are reported but not tested as independent contenders.
6. `classification_rule`: each candidate becomes exactly one of `alias`,
   `co_survivor`, `excluded`, `wrong_distinction`, or `open`.
7. `positive_boundary_result`: the computed predicate above, including at least
   one candidate or control that proves the predicate can admit.
8. `expected_teeth_row`: the first computed comparison expected to separate the
   candidate from `A3.CP.0_committed_gamma_in_gamma_out_placement`.
9. `cost_guard`: heavy-local rows run only after the light-symbolic alias pass
   and only on non-alias representatives.
10. `adapter_pin`: the G7 rule is binding. Every adapter realization must be
    pinned by rule, source path, convention tuple, and hash or finite row list
    before evaluation.

## Shared Alias Detection

For each candidate `R`, compute over its pinned finite rows:

- `raw_value[row]`: exact symbolic, rational, integer, floating-with-tolerance,
  or interval-tagged scalar.
- `sign_value[row] in {-1,0,+1}` after the candidate's declared orientation.
- `zero_set`, `positive_set`, and `negative_set`.
- `rank_partition`: rows partitioned by exact raw value order after reducing
  gauge, section, loop-orientation, and phase conventions.
- `placement_control_signature`: result under fiber/base erasure or swap,
  connection mutation, density-stationarity erasure, and degenerate controls.
- `axis_boundary_signature`: recovery/nonrecovery rows against Axis-0 response,
  Axis-6 precedence, and Axis-4 loop-order keys where computable.
- `source_convention_tuple`: provenance path, formula id, gauge/section
  convention, loop-count convention, sheet/chirality convention, flux or
  holonomy convention if any, and adapter rule.

Two readouts are the same Axis-3 probe iff all of the following hold:

1. Same finite carrier rows, or a declared adapter proves a row-preserving
   bijection before results are inspected.
2. Same `zero_set`.
3. `positive_set` and `negative_set` are identical after either no sign flip or
   a documented global orientation flip. A sign flip is allowed only when the
   provenance explicitly says which side is fiber/inner versus base/outer.
4. `rank_partition` is identical up to a strictly monotone reparameterization of
   the raw scalar and up to candidate-declared gauge/section/phase choice.
5. `placement_control_signature` is identical.
6. `axis_boundary_signature` is identical.

Equal aggregate counts alone are not alias. Equal holonomy total, phase total,
flux total, chirality label, sheet label, or density movement magnitude alone is
not alias. Matching only Axis-0 response or Axis-6 precedence metadata is
evidence for `wrong_distinction` unless the Axis-3 vector still cross-cuts those
rows.

## Registered Candidate Space

| Candidate id | Finite representative | Closeness | Expected teeth row | Cost |
|---|---|---|---|---|
| `A3.CP.0_committed_gamma_in_gamma_out_placement` | Control. The `discrete_axis3_placement_v0` 48-row nondegenerate Family B Hopf sample: sheets `{L,R}` x eta `{pi/8,pi/4,3*pi/8}` x phi indices `{0,2}` x chi indices `{0,1}` x loop family `{gamma_in,gamma_out}`. `gamma_in` is `phi=phi0+u, chi=chi0, eta=eta0`; `gamma_out` is `phi=phi0-cos(2eta)u, chi=chi0+u, eta=eta0`. | control | none; anchor | light-symbolic |
| `A3.CP.1_type1_type2_inversion_overlay` | Use the anchor 48 rows, but add the staged Type1/Type2 chart-role overlay as a second field. Representative holds raw fiber/base formulas fixed while swapping chart role inner/outer by engine type. | close overlay; possible co-survivor or orthogonal overlay | Type teeth: fiber/base sign should remain stable if this is only overlay; if chart-role swap changes placement sign, candidate may be a co-survivor. | heavy-local |
| `A3.CP.2_l_r_chirality_overlay` | Use the anchor 48 rows with sheet sign `H_L=+H0/H_R=-H0` preserved. Candidate sign is the sheet/chirality-sensitive placement readout after erasing or retaining chirality. | close sheet/chirality neighbor | Chirality teeth: erase L/R sheet sign. Chirality should collapse while fiber/base horizontal/stationary rows remain computed; if the full candidate vector remains identical to CP.0, alias. | heavy-local |
| `A3.CP.3_flux_in_out_overlay` | Use the anchor 48 rows and reverse loop orientation or current convention to obtain a flux in/out sign over the same loop anchors. | close geometry-current neighbor; high wrong-axis risk | Flux teeth: reverse loop orientation/current convention. Flux sign may flip while fiber/base placement remains horizontal versus stationary; classify as Axis-3 only if placement predicate still passes. | heavy-local |
| `A3.CP.4_holonomy_based_placement_readout` | Holonomy representative over the same Hopf loop family: finite rows use pinned accumulated `phi`, endpoint spinor phase, or Berry/holonomy convention with one declared loop-count and orientation. | medium; estate neighbor | Holonomy teeth: distinguish fiber loop phase/holonomy from base traversal while preserving gauge-invariant class. Fail if it reads only total holonomy, Chern row, or section convention without placement split. | heavy-local |
| `A3.CP.5_section_phase_sign_7e78f3829` | Section-phase estate row from `hopf_base_section_phase_recovery_v0`: north-section loop at `eta=pi/6`, `beta:0->2pi`, recovered U(1) phase matching enclosed-area/Hopf holonomy, plus changed-section gauge shift and contractible-loop controls. Adapter must expand this single section-phase row to a finite placement vector before sweep, or remain `open_adapter_required`. | medium; phase/section neighbor | Section teeth: compare north-section phase sign, changed-section gauge term, wrong-gauge flip, and contractible-loop zero against fiber/base placement. Fail if the row is only a convention/phase packet and cannot produce a placement vector. | heavy-local |
| `A3.CP.6_density_traversal_rate_readout` | Same Family B Hopf loop anchors as CP.0, but raw value is density traversal rate or max density distance from start over the sampled loop; sign is `-1` for stationary/below threshold and `+1` for traversing/above threshold under a predeclared threshold or exact-zero rule. | nearest scalar reformulation of anchor | Rate teeth: threshold and exact-zero controls. Alias if exact stationary/traversing sign vector and control signature match CP.0; co-survivor only if rate ranks add stable non-alias teeth. | light-symbolic |

## Per-Candidate Provenance Pins

### `A3.CP.0_committed_gamma_in_gamma_out_placement`

Provenance:

- `discrete_axis3_placement_v0` commit message pins `gamma_in` as base
  stationary and `gamma_out` as horizontal with `A(dot gamma)=0`.
- `build_card.md` declares `gamma_in` and `gamma_out`, the three-polarities
  discipline, controls, and staged overlays.
- `audit_verdict.md` reports 24 fiber/gamma_in rows and 24 base/gamma_out rows
  over the code-pinned 48-row family.

Alias note: this is the control representative. Other candidates can alias it
only by the shared alias rule above; matching 24/24 counts is not enough.

### `A3.CP.1_type1_type2_inversion_overlay`

Provenance:

- `discrete_axis3_placement_v0` stored overlay registry row:
  `Type1_Type2_inversion`, `staged_not_run`, discriminator "hold raw
  fiber/base fixed while swapping chart role inner/outer by engine type; raw
  placement must stay while chart role flips".
- `axis_work_order_20260612.md` preserves Type1/2 inversion as a live Axis-3
  alternative.

Why it reads the same distinction: it tests whether placement is raw
fiber/base geometry or chart-role inversion layered on top.

Alias detection: alias only if the Type1/2 field is inert after the pinned
chart-role swap and the CP.0 sign vector, rank partition, and controls match.

### `A3.CP.2_l_r_chirality_overlay`

Provenance:

- `discrete_axis3_placement_v0` stored overlay registry row:
  `L_R_chirality`, `staged_not_run`, discriminator "erase
  H_L=+H0/H_R=-H0 sheet sign; chirality should collapse while fiber/base
  horizontal/stationary rows stay computed".
- Scaffold alternatives preserve L/R chirality as an Axis-3 live overlay.

Why it reads the same distinction: it may refine placement by sheet/chirality
without replacing the fiber/base predicate.

Alias detection: alias if chirality erasure leaves the full placement vector
and controls identical to CP.0. Wrong distinction if the vector is recoverable
from sheet sign alone.

### `A3.CP.3_flux_in_out_overlay`

Provenance:

- `discrete_axis3_placement_v0` stored overlay registry row:
  `flux_in_out`, `staged_not_run`, discriminator "reverse loop orientation or
  current convention; flux sign may flip while fiber/base placement remains
  horizontal versus stationary".
- `working_math_scaffold_20260609.md` keeps flux as geometry/ratchet dynamics
  and as a candidate current family, not primitive axis content.

Why it reads the same distinction: only the placement-linked sign of flux
in/out can contend with Axis-3. The flux object itself remains geometry.

Alias detection: gauge/connection aliases are reduced first. Equal total flux
or orientation sign alone is not alias.

### `A3.CP.4_holonomy_based_placement_readout`

Provenance:

- `working_math_scaffold_20260609.md` distinguishes fiber loop
  density-stationary and base/lifted-base loop density-visible rows.
- `s2_build_spec_20260610.md` requires convention pins for holonomy quantity,
  Berry formula, phase domain, base loop count, and orientation/sign.
- `estate_value_reconciliation_v2_20260610.md` reconciles holonomy conventions
  across existing estate rows.

Why it reads the same distinction: holonomy can distinguish fiber/lift versus
base traversal only when the loop convention and gauge are pinned and the
result still separates the placement rows.

Alias detection: canonicalize holonomy under the five convention pins, then
compare the finite sign vector and placement controls. Equal holonomy class
with different placement vector is not alias.

### `A3.CP.5_section_phase_sign_7e78f3829`

Provenance:

- `hopf_base_section_phase_recovery_v0` audit reports a real north-section
  pullback/lift recomputation at `eta=pi/6`, with recovered phase matching the
  enclosed-area/Hopf holonomy prediction.
- The same audit warns the builder's own north-section rows are partially
  definitional and that the packet is convention-pinned, not a global section
  theorem.

Why it reads the same distinction: section-phase signs can contend only if they
become a finite placement vector over fiber/base loop rows, not if they remain
a single convention packet.

Alias detection: section choice, gauge shift, base-loop count, and lifted phase
domain are part of the canonical tuple. If no finite placement adapter is
source-backed, classify as `open_adapter_required`.

### `A3.CP.6_density_traversal_rate_readout`

Provenance:

- `discrete_axis3_placement_v0` result fields include density stationarity,
  density traversal, and max density distance from start.
- Audit verdict identifies `gamma_in` as density stationary and `gamma_out` as
  density traversing with exact horizontal condition.

Why it reads the same distinction: it is the scalar-rate version of the anchor
placement predicate.

Alias detection: the exact-zero/threshold rule is part of the canonical tuple.
If it produces the same sign vector and control signature as CP.0, it is an
alias, not a separate contender.

## Expected Sweep Phases

Phase 1: light-symbolic alias pass.

- Compute CP.0 and CP.6 directly from the existing 48-row anchor packet.
- For CP.1-CP.5, verify whether a source-backed finite adapter already exists.
  If not, mark `open_adapter_required` and do not run heavy batteries.
- Emit raw candidate count, alias-class count, non-alias representative count,
  wrong-distinction count, and positive-boundary pass count.

Phase 2: heavy-local representative pass.

- Run only candidates whose adapter exists and whose light-symbolic canonical
  form did not alias CP.0 or fail the same-distinction gate.
- Required teeth against CP.0:
  - exact Hamming disagreement rows by loop id;
  - neutral-set disagreement rows;
  - placement-control deltas under fiber/base erasure, connection mutation,
    density-stationarity erasure, and degenerate-pole controls;
  - Axis0, Axis6, and Axis4 nonrecoverability rows;
  - source-specific controls: Type1/2 swap, chirality erase, loop orientation
    reversal, gauge/section flip, wrong-holonomy convention, and traversal-rate
    threshold flip.

## Stop Rule

Stop after the registry in this receipt. The sweep packet is a separate later
build.

No row from this registry authorizes:

- Axis-3 admission;
- "THE Axis-3 readout" language;
- bridge, physics, or manifold promotion;
- broad queue launch;
- treating co-survivors as merged;
- using an unpinned adapter realization.

`promotion_allowed: false`
