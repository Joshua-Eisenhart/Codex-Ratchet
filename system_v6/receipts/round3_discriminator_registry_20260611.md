# Round-3 Discriminator Registry - 2026-06-11

Purpose: satisfy the committed round-3 premortem precondition before any
round-3 discriminator launches.

Scope: derivation and finite registry only. No sims were run. No result JSON was
rewritten. This receipt defines bounded alternative spaces, alias/cosurvivor
handling, expected teeth rows, closeness grades, and cost classes for the
round-3 discriminator queue.

Evidence ceiling: `scratch_diagnostic` planning receipt. This does not promote
any layer, prove global uniqueness, or authorize a broad queue launch.

## Source Hash Ledger

- Current checkout HEAD observed while authoring: `c8dbf04a753dc0fdc5c818fe985cb9edcb3e4116`.
- Round-2 closure addendum: `f7c076f67`, `system_v6/receipts/stack_uniqueness_map_20260611.md`.
- Stack uniqueness base map: `7bc1af811`; S4/S5 addendum: `0d766bb40`; S3/S6-S7 addendum: `8f4fef471`.
- Program status anchor: `4bd575c08`; closeout patch: `9fb6907cc`.
- Canonical geometry program: `0194deb03`; wording patch: `86fc3cb71`.
- S2 positive and negative anchors: `5d8a6f1de`, `f023ebe16`; S2/S5 sweep: `6ba8b7d6c`.
- S3 round-2 probe-family discriminator: `608bbd763`.
- S4 round-2 operator-set discriminator: `fc95e969f`.
- S5 round-2 flow-family discriminator: `629deafb0`.
- S6/S7 round-2 topology discriminator: `053498875`.
- S9 round-2 connection discriminator: `9de3f3633`.
- Ratchet-order round-2 breadth discriminator: `6d0d4bf3`.

## Registry Contract

Every round-3 packet generated from this registry must predeclare:

1. `alternative_space_bound`: the finite candidate ids below, with no extra
   candidates added after results are inspected.
2. `canonical_alias_form`: the layer-specific form below, computed before the
   battery rows.
3. `representative_selection_rule`: one representative per exact alias class;
   all exact aliases are reported but not counted as independent tested
   alternatives.
4. `classification_rule`: each candidate becomes exactly one of `alias`,
   `co_survivor`, `excluded`, or `open`.
5. `expected_teeth_row`: the first row expected to kill the null or split the
   co-survivor.
6. `cost_guard`: heavy-local rows run only after the light-symbolic alias pass
   and only on non-alias representatives.

The MUB lesson is binding: numerically identical effect/generator sets are
detected before the battery runs. Alias rows cannot inflate the tested count.

## S2 - Connection/Flux/Foliation

Round-1/2 basis: positive S2 packet `5d8a6f1de`, negative selectivity
`f023ebe16`, S2/S5 sweep `6ba8b7d6c`.

Round-3 finite space: six committed-adjacent connection/convention families over
the S2 Hopf torus, all expressed as `A = dphi + f(eta)dchi + g_phi dphi +
g_chi dchi` on the pinned chart and checked against the canonical accumulated
`phi` holonomy convention.

| Candidate id | Finite representative | Closeness | Expected teeth row | Cost |
| --- | --- | --- | --- | --- |
| `S2.R3.0_committed` | `f=cos(2eta)`, `g_phi=0`, `g_chi=0` | control | none; anchor | light-symbolic |
| `S2.R3.1_large_gauge_chi_shift` | `f=cos(2eta)`, `g_chi in {1/2, -1/2}` | near-alias / convention-neighbor | lifted holonomy convention pin; Stokes boundary gap | light-symbolic |
| `S2.R3.2_same_curvature_shifted_holonomy` | `f=cos(2eta)+c`, `c in {1/4, -1/4}` | closer than wrong-sign; same `F`, shifted lifted leaves | leaf holonomy spectrum before Chern | light-symbolic |
| `S2.R3.3_endpoint_chern_preserving_bump` | `f=cos(2eta)+epsilon*sin(2eta)^2`, `epsilon in {1/10, -1/10}` | same endpoint `c1`, different density | curvature density and annular Stokes | light-symbolic |
| `S2.R3.4_two_leaf_holonomy_match` | `f=cos(2eta)+epsilon*cos(2eta)*(cos(2eta)-1/2)`, `epsilon in {1/5, -1/5}` | matches `eta=pi/6` and `eta=pi/4`, differs elsewhere | expanded leaf holonomy vector | light-symbolic |
| `S2.R3.5_boundary_conditioning_variant` | finite leaf unions `{pi/12,pi/6}`, `{pi/6,pi/4}`, `{pi/4,pi/3}` with canonical disintegration rule | close leaf-family neighbor | cover/conditioning validity before flux comparison | heavy-local |

Alias-detection rule: reduce each candidate to the canonical tuple
`(F=dA, c1, lifted_holonomy_vector[pi/12,pi/6,pi/4,pi/3,5pi/12],
annular_flux_vector for adjacent listed leaves, cover_period_pin)`. Exact tuple
equality under the documented S2 convention map is `alias`. Equality of `c1`
alone is `co_survivor`, not alias. Same `F` but shifted lifted holonomy is a
convention/gauge-neighbor requiring explicit classification before the battery.

Nearest nontrivial neighbors: the gauge/convention-shifted and same-curvature
families are the closest; the endpoint-preserving bump is the topology-sharing
neighbor; finite leaf-union variants are heavier because conditioning and cover
validity must be checked before Stokes rows.

## S3 - Density/Observable Probe Families

Round-2 basis: `geo_s3_alternative_probe_families_v0` at `608bbd763`.
Accepted lesson: `SIC` is a genuine IC co-survivor; `MUB-XYZ` is an exact alias
of the committed Pauli/probe effect rows.

Round-3 finite space: a finer `d=2` POVM registry with fixed axis conventions
and no continuous scan.

| Candidate id | Finite representative | Closeness | Expected teeth row | Cost |
| --- | --- | --- | --- | --- |
| `S3.R3.0_committed_pauli_xyz` | six Pauli projectors `X/Y/Z`, parent axis order pinned | control | none; anchor | light-symbolic |
| `S3.R3.1_mub_xyz_alias_probe` | three MUB bases in the same `X/Y/Z` order | exact alias calibrator | alias gate before battery | light-symbolic |
| `S3.R3.2_sic_tetrahedron` | four tetrahedral effects with Bloch dot `-1/3` | genuine IC co-survivor | projective-order / N01 nonparallel count | light-symbolic |
| `S3.R3.3_noisy_pauli_ic` | Pauli effects shrunk by `lambda in {2/3, 1/2}` with weights fixed to preserve POVM normalization | near committed IC, softer projective row | projective sharpness and N01/order row | light-symbolic |
| `S3.R3.4_z_refined_equatorial_trine` | Z pair plus equatorial trine frame, normalized as one finite POVM family | between SIC and z-coarse family | z-coarsening plus six-state separation | light-symbolic |
| `S3.R3.5_rank4_random_null_fixed` | one deterministic rational Bloch frame with rank 4 but non-projective asymmetry | closer than old rank-deficient null | composite IC+z+order row | light-symbolic |

Alias-detection rule: convert every POVM to a sorted canonical multiset of exact
effect rows `(weight, Bloch_x, Bloch_y, Bloch_z)` after only the allowed parent
axis-label permutation and effect-order permutation. Then compare the full Gram
matrix of weighted Bloch vectors plus the exact effect multiset. Identical
effect multisets are `alias` before any separation, rank, or N01 rows run.
Equal frame rank or equal six-state separation without identical effects is
`co_survivor` or `open`, not alias.

Nearest nontrivial neighbors: noisy Pauli IC is closest to the committed
alphabet but should lose projective/order teeth; SIC remains the known IC
co-survivor; z-refined trine probes whether the committed stack identity is
really composite rather than row-local.

## S4 - Operator/Channel Alphabets

Round-2 basis: `geo_s4_alternative_operator_sets_v0` at `fc95e969f`.
Round-2 killed `A_y_frame`, `B_depolarizing`, `C_amplitude_damping`, and
`D_random_hermitian` under shell, quotient, N01, fixed-axis, and CPTP rows.

Round-3 finite space: committed-adjacent non-unital and mixed channel alphabets.

| Candidate id | Finite representative | Closeness | Expected teeth row | Cost |
| --- | --- | --- | --- | --- |
| `S4.R3.0_committed_DzDxRxRz` | pinned committed `D_z,D_x,R_x,R_z` affine maps | control | none; anchor | light-symbolic |
| `S4.R3.1_z_amplitude_damping_pair` | `AD_z(gamma)` with `gamma in {1/5,3/10}` plus committed rotations | closer non-unital neighbor | N01/commutator and fixed-axis rows | heavy-local |
| `S4.R3.2_x_amplitude_damping_pair` | `AD_x(gamma)` with `gamma in {1/5,3/10}` plus committed z maps | close frame-shifted non-unital neighbor | z-probe quotient descent/mortality | heavy-local |
| `S4.R3.3_dephase_rotate_hybrid` | `D_z(lambda) o R_x(theta)` with `(lambda,theta) in {(7/10,pi/2),(1/2,pi/2)}` | mixed contraction-rotation | shell preservation/leakage then N01 | heavy-local |
| `S4.R3.4_axis_permuted_committed` | cyclic axis relabels `x->y->z` that preserve CPTP but move probe roles | convention-neighbor, not automatically alias | z-probe quotient row | light-symbolic |
| `S4.R3.5_weak_nonunital_pauli_channel` | affine Pauli channel with small shift `c in {(0,0,1/10),(1/10,0,0)}` and diagonal contraction from committed rows | very close non-unital perturbation | fixed-axis plus Choi positivity | heavy-local |

Alias-detection rule: canonicalize each alphabet as an ordered role tuple
`[(role_id, M_exact, c_exact, CPTP_choi_spectrum_class, fixed_axis_set)]` after
the documented S1/S4 convention map only. Role-preserving equality is `alias`.
Axis relabels are alias only when the relabel preserves the parent z-probe and
N01 row; otherwise they are distinct near-neighbors.

Nearest nontrivial neighbors: non-unital amplitude damping and weak affine
shifts are closer than the old depolarizing/random alternatives because they
preserve more shell/CPTP structure. The expected teeth should come from N01,
z-probe descent, and fixed-axis rows, not from easy invalidity.

## S5 - Terrain Flow Families

Round-2 basis: `geo_s5_alternative_flow_families_v0` at `629deafb0`.
Round-2 killed four broad alternatives while preserving
`B_hamiltonian_only` as a quotient-level co-survivor that dies at mirror/N01.

Round-3 finite space: committed-adjacent contraction-rotation mixtures and
coefficient perturbations over the eight terrain ids.

| Candidate id | Finite representative | Closeness | Expected teeth row | Cost |
| --- | --- | --- | --- | --- |
| `S5.R3.0_committed_8` | eight committed terrain generators with source-locked `A,b` rows | control | none; anchor | light-symbolic |
| `S5.R3.1_alpha_mix_rotation_contraction` | convex generator mix `alpha*H + (1-alpha)*D` for `alpha in {1/4,1/2,3/4}` on the four L/R pairs | close mixed contraction-rotation neighbor | mirror structure and N01 full signature | heavy-local |
| `S5.R3.2_committed_coeff_epsilon` | exact coefficient perturbation `epsilon in {1/20,-1/20}` on one load-bearing off-diagonal slot per family | nearest coefficient neighbor | fixed-point/basin and N01 gap | heavy-local |
| `S5.R3.3_nonunital_weak_shift` | committed `A` with `b_z` shift in `{1/20,-1/20}` where validity survives | close non-unital neighbor | validity, fixed point, quotient 56/56 | heavy-local |
| `S5.R3.4_pairwise_LR_mirror_preserver` | finite rows chosen to preserve Se/Ne mirror continuum but perturb Ni/Si frames | mirror-law co-survivor stress | Ni/Si mirror classification | light-symbolic |
| `S5.R3.5_basin_preserving_null` | one deterministic affine family with same fixed point for `Se_Funnel_L` but altered transient rotation | near basin co-survivor | quotient survival plus time-flow/N01 row | heavy-local |

Alias-detection rule: canonicalize each terrain family as the sorted eight-row
tuple `(terrain_id, A_exact, b_exact, validity_class, fixed_point_exact,
mirror_class, N01_signature)` using the source-approved Bloch convention. Exact
row equality after the documented L/R mirror/convention map is `alias`. Matching
only quotient `56/56` or a fixed point is `co_survivor`, not alias.

Nearest nontrivial neighbors: epsilon coefficient perturbations are nearest to
the committed family; alpha mixed contraction-rotation families test whether the
full signature depends on both contraction and rotation; mirror-preserving rows
test whether the previous mirror caveats hide a closer family.

## S6/S7 - Support Graphs, Covers, And Lens Topologies

Round-2 basis: `geo_s67_alternative_topologies_v0` at `053498875`.
Round-2 killed path, star, complete, and Mobius-full-battery. The Mobius lesson:
`2:1` cover counting survives the twist, but the `Z4` lens descent does not.

Round-3 finite space: twisted-cover and support-graph variants beyond Mobius.
Use grid sizes `N in {8,16,32}` only.

| Candidate id | Finite representative | Closeness | Expected teeth row | Cost |
| --- | --- | --- | --- | --- |
| `S67.R3.0_committed_torus_ring` | untwisted torus cover, cycle graph, Z4 lens shift | control | none; anchor | light-symbolic |
| `S67.R3.1_mobius_reflection_shifted` | cover relation `(a,b)~(a+N/2,-b+c)` for `c in {0,N/4,N/2}` | closest known twist family | lens quotient commensurability | heavy-local |
| `S67.R3.2_klein_double_twist` | two-direction orientation reversal on the rectangular chart with the same Z4 shift | close cover-neighbor | cover-orbit well-definedness then lens row | heavy-local |
| `S67.R3.3_shear_torus` | untwisted cover plus shear `(a,b)->(a+N/2,b+a mod N)` on representatives | near untwisted but altered lens action | lens descent and S6 leakage taxonomy | heavy-local |
| `S67.R3.4_cycle_with_one_chord` | ring graph plus one antipodal chord at each `N` | close support graph neighbor | bounded word cost and cycle holonomy | heavy-local |
| `S67.R3.5_ladder_prism_graph` | two-ring ladder/prism local graph with degree 3 | graph topology neighbor between ring and complete | locality cost plus leakage class row | heavy-local |

Alias-detection rule: canonicalize as
`(graph_isomorphism_class_under_dihedral_lens_preserving_maps,
cover_equivalence_relation_classes, Z4_action_well_defined_boolean,
orbit_size_multiset, cost_profile[N=8,16,32], S6_leakage_class_signature)`.
Exact equality of this tuple is `alias`. Same `2:1` cover count alone is
`co_survivor`; it is not alias, as Mobius already proved.

Nearest nontrivial neighbors: shifted Mobius variants are closest because they
preserve cover cardinality and local cost while stressing lens descent. Shear
torus tests whether untwisted cover identity is stronger than simple cover
counting. Chord/prism graphs are support-near without collapsing to path/star or
complete.

## S9 - Connection/Transport Families

Round-2 basis: `geo_s9_alternative_connections_v0` at `9de3f3633`.
Round-2 split topology from geometry: `C_same_c1_non_hopf_density` co-survives
the `c1=1` topological row and dies at curvature density, holonomy spectrum, and
annular flux.

Round-3 finite space: connection functions matching the committed holonomy at
some leaves or matching topology more tightly than the round-2 alternatives.
Every candidate is represented as `A = dphi + f(eta)dchi`.

| Candidate id | Finite representative | Closeness | Expected teeth row | Cost |
| --- | --- | --- | --- | --- |
| `S9.R3.0_committed_hopf` | `f=cos(2eta)` | control | none; anchor | light-symbolic |
| `S9.R3.1_c1_small_density_bump` | `f=cos(2eta)+epsilon*sin(2eta)^2`, `epsilon in {1/20,-1/20}` | closest same-`c1` density neighbor | curvature density before holonomy | light-symbolic |
| `S9.R3.2_one_leaf_match_pi6` | `f=cos(2eta)+epsilon*(cos(2eta)-1/2)`, `epsilon in {1/10,-1/10}` | matches holonomy at `pi/6` only | expanded holonomy spectrum | light-symbolic |
| `S9.R3.3_one_leaf_match_pi4` | `f=cos(2eta)+epsilon*cos(2eta)`, `epsilon in {1/10,-1/10}` | matches holonomy at `pi/4` only | expanded holonomy spectrum | light-symbolic |
| `S9.R3.4_two_leaf_match_pi6_pi4` | `f=cos(2eta)+epsilon*cos(2eta)*(cos(2eta)-1/2)`, `epsilon in {1/10,-1/10}` | very close leaf-anchor neighbor | annular flux plus off-anchor holonomy | light-symbolic |
| `S9.R3.5_path_ordered_loop_neighbor` | same local `c1` row plus two named quaternionic loop families from the committed transport closure | closest heavy transport neighbor | path-ordered holonomy commutator | heavy-local |

Alias-detection rule: reduce each connection to
`(f_simplified, F=f'(eta), c1, leaf_holonomy_vector
[0,pi/6,pi/4,pi/3,pi/2], annular_flux_vector, validity_class,
path_ordered_loop_signature when scoped)`. For ordinary one-form candidates,
alias requires equality of curvature density and the full leaf-holonomy vector
under the S2/S9 convention map. Equal `c1` is `co_survivor`. Matching one or two
leaf holonomies is `open` until the expanded spectrum and annular flux rows run.

Nearest nontrivial neighbors: small same-`c1` bumps and one/two-leaf matching
families are closer than the round-2 flat/half/random alternatives. The
path-ordered loop neighbor is heavy because it tests transport identity rather
than coefficient identity.

## Resource Guard

The round-3 queue must run in two phases per layer:

1. Light-symbolic alias pass: compute canonical forms, alias classes,
   co-survivor labels, and representative selection. This phase may include
   exact symbolic simplification, rational/surd row comparison, graph
   isomorphism on the finite listed graphs, and source-hash checks.
2. Heavy-local discriminator pass: run only for non-alias representatives that
   remain open after the light pass. Heavy-local rows include channel Choi
   spectra, terrain time-flow/fixed-point recomputation, graph/cost sweeps over
   `N in {8,16,32}`, finite disintegration/conditioning checks, and
   path-ordered transport loops.

Stop rule: if all representatives in a layer are aliases or already classified
as known co-survivors by the light pass, do not run a heavy battery for count
inflation. Write the classification receipt and stop.

## Launch-Card Requirements

Any future builder card using this registry must include:

- the layer id and candidate ids copied from this receipt;
- the exact alias canonicalizer fields for that layer;
- a count of raw candidates, alias classes, co-survivor classes, and non-alias
  representatives;
- the expected-teeth row for every non-alias representative;
- a resource declaration: `light-symbolic` or `heavy-local`;
- explicit statement that round-3 alternatives are closer to the committed row
  than round-1/2 alternatives and therefore may produce aliases or
  co-survivors rather than kills.

No row from this registry authorizes global uniqueness language.
