# Axis-0 Contender-Probe Registry - 2026-06-12

Purpose: register the alternative Axis-0 readout-probe space before any
readout is citable as THE Axis-0 readout.

Scope: registry receipt only. No sims were run. No result JSON was rewritten.
This file defines finite candidate representatives, alias-class detection,
expected teeth rows, closeness grades, and cost classes for the later contender
sweep packet.

Evidence ceiling: `scratch_diagnostic` planning/registry receipt.
`promotion_allowed: false`
`formal_admission_allowed: false`

## Source Hash Ledger

- Current checkout HEAD observed while authoring: `fcf1b3858ee37ca414030d26a0c046fa0378a13e`.
- Owner doctrine read-first: `system_v6/receipts/owner_doctrine_axes_as_existence_probes_20260612.md`, commit `fcf1b3858`.
- Committed first candidate: `discrete_axis0_field_v0`, commit `5d330b427`.
- Registry-format template: `system_v6/receipts/round3_discriminator_registry_20260611.md`, commit `de44219ed`.
- Candidate implementation anchor: `system_v6/sims/discrete_axis0_field_v0/discrete_axis0_field_v0_common.py`.
- Owner-source router: `/Users/joshuaeisenhart/wiki/concepts/igt-axes-terrain-source-extraction-2026-06-04.md`.
- Current doctrine mirror: `/Users/joshuaeisenhart/wiki/concepts/axis0-current-doctrine-state-card.md`.
- Correlation-polarity option pages:
  `/Users/joshuaeisenhart/wiki/concepts/axis-0-correlation-polarity.md` and
  `/Users/joshuaeisenhart/wiki/concepts/axis-0-spec-options.md`.
- Flux/current estate anchors:
  `system_v6/receipts/weld_feedstock_inventory_20260611.md`,
  `system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md`,
  `system_v6/sims/terrain_spinor_flux_nest_n3_v0/`,
  `system_v6/sims/terrain_spinor_flux_nest_n4_v0/`.

## Axis-0 Distinction Boundary

Contenders must read the same distinction. A probe that primarily reads
placement, order, flux-as-geometry, terrain family, or carrier topology without
recovering feedback polarity is not an Axis-0 contender; it is a different-axis
or geometry probe.

Pinned distinction:

- owner-source router: Axis 0 splits white/yang `Ne, Ni` from black/yin
  `Se, Si`; math candidates include `b_0=sign(cos(2 eta))`, entropy, and later
  `Phi_0(rho_AB)` (`igt-axes-terrain-source-extraction-2026-06-04.md:204-206`).
- current doctrine mirror: `Ne/Ni = positive feedback / allostasis` and
  `Se/Si = negative feedback / homeostasis`
  (`axis0-current-doctrine-state-card.md:31-36`).
- correlation-polarity page: Axis 0 asks whether correlation diversity
  "spreads or gets damped" under disturbance
  (`axis-0-correlation-polarity.md:15-21`).
- spec-options page: the operational question is measuring finite correlation
  spread or damping (`axis-0-spec-options.md:21-26`).

## Registry Contract

Every future sweep packet generated from this registry must predeclare:

1. `alternative_space_bound`: the finite candidate ids below, with no extra
   candidates added after results are inspected.
2. `carrier_pin`: the 33-cell Family A carrier from `discrete_axis0_field_v0`,
   including ordered `cell_id=0..32`, generator-labelled directed edges, and the
   source carrier hash.
3. `candidate_vector`: a 33-entry vector over the same cell ids, with raw values
   plus signs in `{-1,0,+1}` where `+1=allo/positive feedback` and
   `-1=homeostatic/negative feedback` after the candidate's declared
   orientation convention.
4. `canonical_alias_form`: computed before any teeth row. The MUB lesson binds:
   exact aliases do not inflate the tested count.
5. `representative_selection_rule`: one representative per exact alias class;
   aliases are reported but not tested as independent contenders.
6. `classification_rule`: each candidate becomes exactly one of `alias`,
   `co_survivor`, `excluded`, `wrong_distinction`, or `open`.
7. `expected_teeth_row`: the first computed comparison expected to separate the
   candidate from `A0.CP.0_committed_signed_outgoing_gradient_flux`.
8. `cost_guard`: heavy-local rows run only after the light-symbolic alias pass
   and only on non-alias representatives.

## Shared Alias Detection

For each candidate `R`, compute over the pinned 33 cells:

- `raw_value[c]`: exact rational, algebraic, integer, or interval-tagged scalar.
- `sign_value[c] in {-1,0,+1}` after the candidate's declared orientation.
- `zero_set = {c | sign_value[c] = 0}`.
- `positive_set`, `negative_set`.
- `rank_partition`: cells partitioned by exact raw value order, after reducing
  candidate-specific gauge/phase choices to the documented convention.
- `generator_stability_signature`: for each committed generator, counts of
  edges where source/destination signs match or differ.
- `source_convention_tuple`: provenance path, formula id, gauge/sign convention,
  entropy base if any, and carrier projection rule.

Two readouts are the same Axis-0 probe iff all of the following hold:

1. Same carrier and same cell ordering.
2. Same `zero_set`.
3. `positive_set` and `negative_set` are identical after either no sign flip or
   a documented global sign-convention flip. A sign flip is allowed only when
   the provenance explicitly says which side is allo/positive-feedback versus
   homeostatic/negative-feedback.
4. `rank_partition` is identical up to a strictly monotone reparameterization
   of the raw scalar and up to candidate-declared gauge/phase choice.
5. `generator_stability_signature` is identical.

Equal aggregate counts alone are not alias. Equal entropy/flux total alone is
not alias. Equal `c1`, holonomy, or path-count metadata alone is not alias.
Matching only `axis3_style_placement_key`, `axis6_style_order_key`, degree, or
successor count is evidence for `wrong_distinction` unless the Axis-0 vector
still cross-cuts those rows.

Pair procedure: for every unordered pair `(Ri,Rj)`, compute both orientations
`(+Rj,-Rj)` where source-permitted, reduce gauge/monotone forms, compare the
canonical tuples above exactly, then classify. No battery row may run before
this pair table exists.

## Registered Candidate Space

| Candidate id | Finite representative | Closeness | Expected teeth row | Cost |
|---|---|---|---|---|
| `A0.CP.0_committed_signed_outgoing_gradient_flux` | Control. On the 33-cell carrier, scalar field `phi=(2x-5y+7z+3xy-z^2+4r2+11shell)/97`; edge gradient `phi(dst)-phi(src)` over the committed generator adjacency; cell polarity is `sign(sum_outgoing gradients)`. | control | none; anchor | light-symbolic |
| `A0.CP.1_unweighted_edge_gradient_count_balance` | Same edge table as the committed candidate, but raw value per cell is `#positive_outgoing_edges - #negative_outgoing_edges`; magnitudes discarded, zero edges ignored. | nearest nontrivial same-carrier neighbor | Hamming disagreement from committed sign vector; first separating cells are those where one large edge outweighs several small opposite edges or where magnitudes create a nonzero net while counts tie. | light-symbolic |
| `A0.CP.2_incoming_vs_outgoing_gradient_current` | Same `phi` and same edges, but compare `sign(sum_incoming gradients)` and `sign(sum_outgoing gradients)` as a directed-current convention family; representative pins the orientation pair rather than choosing one silently. | convention-neighbor / possible alias after global sign flip | Alias gate: if incoming is exactly global sign-reversal of outgoing with same zero set and stability signature, merge; otherwise teeth are cells whose source/sink imbalance changes polarity. | light-symbolic |
| `A0.CP.3_entropy_gradient_sign` | Per cell, compute the signed change of a committed entropy/readout scalar under each outgoing generator update, then sum outgoing signed entropy deltas. Representative must pin entropy kind: local system entropy, bath-exchange/production, feedback-polarity entropy, conditional entropy, or coherent information. | close doctrine neighbor, not automatically alias | Which-entropy teeth: compare all registered entropy kinds separately against committed polarity; exclude entropy kinds whose sign pattern matches `trace_norm` or other known non-doctrine patterns instead of `Ne/Ni` vs `Se/Si`. | heavy-local |
| `A0.CP.4_pauli_participation_feedback_polarity` | Project the current terrain-generator sheet packet's Pauli participation ratio perturbation-spread functional onto the 33-cell carrier: `+` for generator/family rows matching `Ne/Ni` positive-feedback/allostasis; `-` for `Se/Si` negative-feedback/homeostasis; neutral where no mapped terrain row exists. | doctrine-near but carrier-adapter-dependent | Adapter teeth: rows must prove the 33-cell projection is not just terrain label lookup, then compute disagreement cells versus committed flux polarity and stability under each committed generator. | heavy-local |
| `A0.CP.5_flux_direction_annular_or_edge_current` | Flux/current sign readout. Representative family includes Hopf annular flux direction where shell data exists and graph edge current `J_ij` where n3/n4 terrain-spinor-flux rows project to the 33-cell carrier. The 33-cell vector is the sign of net outgoing projected flux/current per cell. | close geometric-current neighbor, high alias risk with committed gradient flux | Flux teeth: separate curvature/transport current from scalar-gradient flux by cells where holonomy/annular sign or projected `J_ij` disagrees with `sum_out Δphi`; require chirality/seat controls before classifying co-survivor. | heavy-local |
| `A0.CP.6_flux_continuity_n3_n4_current_sign` | Specific n3/n4 continuity representative: use `terrain_spinor_flux_nest_n3_v0` and `terrain_spinor_flux_nest_n4_v0` edge coupling/current formula `J_ij=g_ij*(p_i-p_j)`, with `p_i=(1-z_i)/2`, then project site/current signs onto the Family A cell labels by the declared chart adapter. | nearby if adapter recovers same feedback polarity; otherwise different carrier | Continuity teeth: compare n3 and n4 signs before projection, then projected 33-cell vector; fail if n3/n4 agree internally but projection is label-only or if continuity rows do not survive the committed generator updates. | heavy-local |
| `A0.CP.7_lyapunov_descent_direction` | Choose a finite Lyapunov functional `L(c)` over the carrier or over a projected state row; cell sign is `sign(-sum_outgoing ΔL)`, where descent is positive feedback/allostatic only if source convention says descent corresponds to adaptive spread rather than damping. | medium; likely splits by chosen functional | Functional teeth: recompute with at least two pinned Lyapunov candidates and classify candidates reading stability/damping only as `wrong_distinction` unless they match the positive/negative feedback doctrine. | heavy-local |
| `A0.CP.8_hopfield_energy_gradient_sign` | Hopfield-style energy representative `V(rho)` from the finite spinor/Hopfield estate; cell sign is the projected energy-gradient force or `-ΔV` under the local update. Must pin Hermitian coupling, state projection, and retrieval map before evaluation. | medium/far until same-carrier adapter exists | Retrieval teeth: cells in spurious-attractor or retrieval-basin regions should separate from committed scalar-gradient polarity; exclude if the sign reads basin membership rather than feedback polarity. | heavy-local |
| `A0.CP.9_holonomy_spectrum_sign` | Spectral/holonomy representative: reduce the relevant connection or loop transport to a signed spectral row, then project per-cell sign from local shell/loop/transport data. | far-to-medium; high wrong-axis risk | Holonomy teeth: prove the sign is not Axis-3 loop placement or Axis-6 precedence by repeating the committed three-polarities independence rows; compare cells where holonomy phase sign disagrees with scalar-gradient flux. | heavy-local |
| `A0.CP.10_transition_graph_in_out_degree_imbalance` | Pure graph baseline on the same 33-cell carrier: raw value `out_degree(c)-in_degree(c)` or, if all rows have fixed outdegree, `distinct_successor_count(c)-distinct_predecessor_count(c)`. | far structural/null neighbor | Degree teeth: expected to be killed or marked `wrong_distinction` if recoverable from Axis-6-style order/successor-count rows; survives only if it cross-cuts Axis3/Axis6 and matches feedback polarity under controls. | light-symbolic |

## Per-Candidate Provenance Pins

### `A0.CP.0_committed_signed_outgoing_gradient_flux`

Provenance:

- `discrete_axis0_field_v0` commit message pins the first candidate as an
  exact rational scalar field with directed-gradient signed-flux polarity on
  the 33-cell Family A carrier.
- `discrete_axis0_field_v0_common.py:354-383` computes edge gradients and
  `net_flux_by_cell`.
- `discrete_axis0_field_v0_common.py:406-410` records
  `net_outgoing_gradient_flux`, `axis0_polarity`, and probe family.
- Audit verdict reports counts: homeostatic/minus `17`, allo/plus `15`,
  neutral `1`.

Alias note: this is the control representative. Other candidates can alias it
only by the shared alias rule above; matching its aggregate counts is not enough.

### `A0.CP.1_unweighted_edge_gradient_count_balance`

Provenance:

- Same committed edge-gradient table as CP.0.
- `discrete_axis0_field_v0_common.py:388-421` already emits per-cell counts of
  positive, negative, and zero outgoing gradient edges.

Why it reads the same distinction: it uses the same local directed response
data but asks whether polarity is sign-count or magnitude-weighted signed flux.

Alias detection: exact alias iff `sign(pos_count-neg_count)` has the same zero
set, polarity sets, rank partition, and generator-stability signature as CP.0
after the allowed global sign convention.

### `A0.CP.2_incoming_vs_outgoing_gradient_current`

Provenance:

- CP.0 uses outgoing sums only (`discrete_axis0_field_v0_common.py:361-383`).
- The edge table is directed and generator-labelled
  (`discrete_axis0_field_v0_common.py:363-380`).

Why it reads the same distinction: it preserves the same scalar field and graph
but varies source/sink orientation convention. This is a necessary alias test,
not a new doctrine claim.

Alias detection: compute incoming and outgoing vectors from the same edge table.
If incoming equals `-outgoing` globally after orientation pinning, register as
one alias class. If the graph's directed imbalance makes only some cells flip,
keep as non-alias until teeth rows classify it.

### `A0.CP.3_entropy_gradient_sign`

Provenance:

- Owner router says Axis 0 includes entropy `S(rho_bar(eta))` and later
  `Phi_0(rho_AB)` (`igt-axes-terrain-source-extraction-2026-06-04.md:204-206`).
- Current doctrine says three entropy columns never collapse and names local
  system entropy, bath exchange, and feedback polarity separately
  (`working_math_scaffold_20260609.md:303-309`).
- Current doctrine mirror warns not all entropy/norm measures realize the
  doctrine pattern; `trace_norm` and `observable_spread_entropy` do not
  (`axis0-current-doctrine-state-card.md:47`).

Why it reads the same distinction: entropy-gradient sign is a contender only
when the entropy kind is explicitly the feedback-polarity/correlation-spread
kind, not generic entropy.

Alias detection: candidate key includes entropy kind and entropy base. Two
entropy readouts alias only if the 33-cell sign vector and exact rank partition
match under monotone reparameterization. Equal monotonicity of total entropy is
not alias.

### `A0.CP.4_pauli_participation_feedback_polarity`

Provenance:

- Current doctrine mirror records the owner family row:
  `Ne/Ni = positive feedback / allostasis` and
  `Se/Si = negative feedback / homeostasis`.
- Same page says that pattern is matched under the Pauli participation ratio
  perturbation-spread functional and warns not to overstate it as all measures
  (`axis0-current-doctrine-state-card.md:31-47`).
- Terrain packet audit says Axis-0 correlation-diversity response per family
  with `(+,+,-,-)` for `(Ne,Ni,Se,Si)` is required next hardening, not closure.

Why it reads the same distinction: it is the cleanest currently named
positive-feedback/allostasis versus negative-feedback/homeostasis functional.

Alias detection: the adapter must emit the 33-cell vector without using the
target labels as the proof. Alias requires exact vector equality to CP.0 after
orientation; matching only the four terrain-family signs is not alias.

### `A0.CP.5_flux_direction_annular_or_edge_current`

Provenance:

- Standing doctrine says terrains and flux are geometry/ratchet dynamics on
  `M(C,t)` and axes are readouts (`working_math_scaffold_20260609.md:303-309`).
- Flux is a candidate current family on that geometry, not axis content
  (`working_math_scaffold_20260609.md:284-289`).
- Flux curvature member is pinned as
  `A=dphi+cos(2eta)dchi`, `F=dA=-2sin(2eta)deta^dchi`
  (`working_math_scaffold_20260609.md:311`).

Why it reads the same distinction: only the sign readout of a flux/current
family can contend with Axis-0 polarity. The flux object itself remains
geometry, not the axis.

Alias detection: reduce annular flux or edge current to a 33-cell signed vector.
Gauge/connection aliases are removed before comparison. Equal total Chern row,
total flux, or holonomy alone is not alias.

### `A0.CP.6_flux_continuity_n3_n4_current_sign`

Provenance:

- n3 common builder pins `current=J_ij=g_ij*(p_i-p_j), p_i=(1-z_i)/2`
  (`terrain_spinor_flux_nest_n3_v0_common.py:33-43`).
- n4 common builder pins the same formula and C16 support
  (`terrain_spinor_flux_nest_n4_v0_common.py:37-47`).
- Feedstock inventory says n3 has flux/current continuity rows and n4 has
  target-row continuity/saturation (`weld_feedstock_inventory_20260611.md:23-24`).
- Owner prediction names `terrain_spinor_flux_nest_n3/n4` as "in-solver flux
  continuity" (`owner_prediction_64_subsubbasins_20260611.md:150-154`).

Why it reads the same distinction: it supplies a signed current/readout family
that may compete with scalar-gradient flux after same-carrier projection.

Alias detection: n3 and n4 must first agree under their own continuity schema.
Then the projected 33-cell vector is compared to CP.0. If projection is
label-only or fails source-backed carrier mapping, classify as `wrong_distinction`
or `open`, not alias.

### `A0.CP.7_lyapunov_descent_direction`

Provenance:

- Axis0 option pages preserve response under perturbation as a finite
  operational question (`axis-0-spec-options.md:21-26`).
- QIT engine math packet gives Lyapunov-style distances `D_z=(x^2+y^2)/2`
  and `D_x=(y^2+z^2)/2`, then warns that any "gradient descent" claim must
  state the functional (`QIT_ENGINE_FULL_EXPLICIT_MATH_PACKET_20260522.md:979-1008`).
- The same packet's role-word table says gradient descent requires the same
  named functional with negative delta
  (`QIT_ENGINE_FULL_EXPLICIT_MATH_PACKET_20260522.md:1251-1259`).

Why it reads the same distinction: Lyapunov descent can read damping versus
adaptive spread only if the functional is pinned and mapped to feedback
polarity.

Alias detection: functional id is part of the canonical tuple. Two Lyapunov
readouts with different functionals cannot alias unless their raw 33-cell
rank partitions and sign vectors are exactly monotone-equivalent.

### `A0.CP.8_hopfield_energy_gradient_sign`

Provenance:

- Spinor-network estate identifies `basin3_hopfield_chiral_quaternion_network`
  as the closest existing Hopfield/retrieval packet and says it has Hopfield-like
  retrieval dynamics and multistability probes
  (`spinor_network_surface_estate_20260611.md:39`).
- Same estate says a strict quantum-Hopfield carrier still needs Hermitian
  coupling, energy/Lyapunov functional, and admissible retrieval dynamics.
- The estate's quantum-Hopfield basin row pins the missing strict object as a
  terminal-state quotient with energy/Lyapunov function, retrieval map, basin
  partition, and controls (`spinor_network_surface_estate_20260611.md:80-82`).

Why it reads the same distinction: a Hopfield energy gradient can read
homeostatic damping/retrieval versus allostatic spread only after the retrieval
map is admitted for the finite carrier.

Alias detection: energy functional, coupling matrix, state projection, and
update map are part of the canonical tuple. Basin membership or attractor class
alone is a different readout, not Axis-0 alias.

### `A0.CP.9_holonomy_spectrum_sign`

Provenance:

- Owner prediction lists the holonomy-spectrum identity as geometric data and
  the L/R-distinguishing kind (`owner_prediction_64_subsubbasins_20260611.md:150-154`).
- Working scaffold keeps sign/phase/holonomy as geometry/readout material, with
  axes as readouts over `M(C)` rather than primitive labels.

Why it reads the same distinction: it is a contender only if the spectral sign
tracks positive/negative feedback polarity and not merely loop placement,
precedence, or chirality.

Alias detection: canonicalize the spectrum under documented gauge/phase
convention, then compare the 33-cell sign vector. Equal holonomy spectrum with
different per-cell feedback polarity is not alias.

### `A0.CP.10_transition_graph_in_out_degree_imbalance`

Provenance:

- CP.0's carrier is a directed 33-cell generator graph with 198 edges.
- CP.0 audit and code already compute Axis-6-style order keys from component,
  terminal closure, and distinct successor count
  (`discrete_axis0_field_v0_common.py:331-335`).
- The committed candidate explicitly tests Axis-0 response polarity separately
  from Axis-3 placement and Axis-6 order.

Why it reads the same distinction: it is a cheap structural baseline for
expansion/damping. It is expected to fail as Axis-0 if it collapses to degree or
successor-count order.

Alias detection: exact degree vectors alias nothing unless the full 33-cell
polarity vector, rank partition, and stability signature match CP.0. If degree
predicts polarity through Axis-6 order keys, classify as `wrong_distinction`.

## Expected Sweep Phases

Phase 1: light-symbolic alias pass.

- Compute CP.0, CP.1, CP.2, and CP.10 directly from the existing 33-cell carrier
  and edge table.
- For CP.3-CP.9, verify whether a source-backed 33-cell adapter already exists.
  If not, mark `open_adapter_required` and do not run heavy batteries.
- Emit raw candidate count, alias-class count, non-alias representative count,
  and wrong-distinction count.

Phase 2: heavy-local representative pass.

- Run only candidates whose adapter exists and whose light-symbolic canonical
  form did not alias CP.0 or fail the same-distinction gate.
- Required teeth against CP.0:
  - exact Hamming disagreement cells by `cell_id`;
  - neutral-set disagreement cells;
  - per-generator stability deltas;
  - Axis3 and Axis6 nonrecoverability rows;
  - no-structure controls: constant/readout-erased, shuffled adjacency,
    orientation reversal, label shuffle, and degree-only baseline;
  - source-specific controls: entropy-kind swap, gauge/phase flip, chirality
    erase, terrain-label erase, retrieval-map erase.

## Stop Rule

Stop after the registry in this receipt. The sweep packet is a separate later
build.

No row from this registry authorizes:

- Axis-0 admission;
- "THE Axis-0 readout" language;
- bridge, physics, or manifold promotion;
- broad queue launch;
- treating co-survivors as merged.

`promotion_allowed: false`

## Sweep 3 Correction Annotation

Boundary operationalization caveat:
The registry's `reads the same distinction` boundary is strong as doctrine but still under-operationalized for candidate probes that can be framed either as feedback polarity or as terrain-family stability. Future sweep packets should add a positive computable predicate before classifying a candidate as reading Axis-0: for example, a probe reads the Axis-0 distinction only if its 33-cell sign vector changes when the terrain-family assignment is shuffled or erased, and does not change when only loop-class/Axis-3 assignment is shuffled. This prevents a candidate author from satisfying the boundary circularly by mapping the candidate output to `Ne/Ni` versus `Se/Si` after the fact.

This annotation does not alter the stop rule, candidate list, alias tuple, or ceiling. It does not touch the axis work order receipt.
