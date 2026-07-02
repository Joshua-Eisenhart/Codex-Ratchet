# Geometry Alternatives Sim Audit - 2026-05-28

Status: active gap audit for geometry alternatives. This is not final manifold
admission, official G-structure selection, layer embedding, stacking, flux,
Xi/Phi0, Axis0, FEP/Holodeck, physics/gravity, or PEPS3D closure.

## Current Truth

Terminology correction: the current 12-row packet does not contain completed
G-structures. It contains standalone geometry, carrier, fibration, bundle,
spinor, Hopf, twistor, Clifford, and reduction-graph scout receipts. Those rows
are things to sim and compare before a true G-structure is selected or built.

The current individual geometry-scout packet covers this explicit candidate
set:

- `S3_spinor_carrier`
- `S2_Hopf_base_surface`
- `Hopf_fibration_S3_to_S2`
- `Nested_Hopf_tori`
- `Clifford_torus_T2_in_S3`
- `Twistor_incidence_spinor_geometry`
- `U1_Hopf_principal_bundle`
- `SU2_Spin3_unit_quaternion_double_cover`
- `SO3_orientation_frame_reduction`
- `Pin3_Spin3_chirality_split`
- `Clifford_geometries_Cl3_Cl6`
- `Hybrid_Hopf_Spin_Twistor_Clifford_reduction_graph`

The corrected status file is:

```text
system_v5/ops/formal_scouts/layer_g_structure_entropy_individual_sim_status_20260528.json
```

It records 9/9 layer rows with full spinor-network receipts, bond-4 receipts,
and MPS/PEPS2D/PEPS3D depth receipts, plus 12/12 individual geometry-scout
receipts.

That is real bounded scout coverage. It is not exhaustive geometry coverage.
It is not full layer completion. It is not completed G-structure evidence.

## The Main Gap

The 12 geometry-scout candidates are mostly spinor/Hopf/Clifford/twistor/
fibration families. They do not exhaust the geometry space already named in repo
docs and formal scouts, and they do not by themselves define the true
G-structure for the layered ratchet.

Several geometry families already exist as root-adjacent or adapter scouts but
were not lifted into the individual geometry-scout matrix. Other
families appear in legacy/proposal surfaces and should be rebuilt under the
current source-native standard before being trusted.

## Alternatives That Should Be Simmed Or Promoted Into Candidate Rows

### 1. Finite Probe / Effect / Weyl-Heisenberg Geometry

Why it matters:

This is the lowest currently admitted geometry after the two root constraints:
finite effects/probes, finite response assignments, and noncommuting
Weyl-Heisenberg shift/phase order. It is more root-adjacent than Hopf or
twistor geometry.

Existing evidence:

```text
system_v5/ops/formal_scouts/results/finite_effect_sic_weyl_substrate_admission_probe_results.json
system_v5/ops/formal_scouts/results/sic_mub_probe_family_comparison_probe_results.json
```

Current status:

Has bounded scout receipts. It is not yet represented as an individual
geometry alternative with the same 8/16/32/64 spinor-network, MPS, PEPS2D,
PEPS3D, entropy, and control coverage as the 12 candidates.

Recommended next sim:

```text
sim_finite_probe_effect_weyl_geometry_candidate_probe.py
```

Required controls:

- SIC erased
- MUB overcomplete-only control
- Weyl order erased
- commuting probe family
- dense state closure
- scalar entropy primary

### 2. Finite Contextuality / Sheaf / Presheaf Geometry

Why it matters:

The manifold is a constraint survivor surface. Contextual sheaf geometry is a
natural way to test whether local assignments fail to glue into a global
section, which is close to the root noncommutation/compatibility problem.

Existing evidence:

```text
system_v5/ops/formal_scouts/results/finite_contextuality_sheaf_event_gate_probe_results.json
```

Current status:

Runs as root-adjacent finite event/context evidence. It is not yet a full
source-native spinor-network geometry candidate.

Recommended next sim:

```text
sim_contextual_sheaf_presheaf_geometry_candidate_probe.py
```

Required controls:

- local sections only
- forced global section
- context graph commuted
- sheaf label only
- product/no-entanglement carrier
- no PEPS3D support

### 3. Process POVM / Quantum Comb / History Geometry

Why it matters:

The retrocausal shell model is not just state geometry; it is path/history and
order-sensitive compatibility geometry. Process POVMs and quantum combs are
good finite objects for noncommuting histories without jumping to Axis0.

Existing evidence:

```text
system_v5/ops/formal_scouts/results/process_povm_quantum_comb_history_gate_probe_results.json
```

Current status:

Has a bounded process-history receipt. It is not yet stressed as an individual
geometry candidate across spinor-network carriers and PEPS2D/PEPS3D views.

Recommended next sim:

```text
sim_process_povm_quantum_comb_geometry_candidate_probe.py
```

Required controls:

- history order reversed
- commuting instrument family
- history effects not complete
- branch weights uniformized
- shell orientation erased
- entropy-only proxy

### 4. Finite Projective Design / Spectral Triple Geometry

Why it matters:

Projective designs give finite projective-state geometry without using Bloch
sphere primitives. Spectral triples give a noncommutative geometry handle via a
finite algebra/module/Dirac operator and bounded commutators.

Existing evidence:

```text
system_v5/ops/formal_scouts/results/finite_projective_design_spectral_triple_gate_probe_results.json
```

Current status:

Has finite projective and spectral-triple evidence. It lacks the same
source-native spinor-network geometry-candidate treatment as Hopf or Clifford
rows.

Recommended next sims:

```text
sim_projective_design_geometry_candidate_probe.py
sim_spectral_triple_dirac_geometry_candidate_probe.py
```

Required controls:

- projective incidence erased
- global phase mishandled
- Dirac commutator flattened
- finite algebra made commutative
- no PEPS3D locality
- dense Hilbert closure

### 5. Lorentzian / Conformal / Causal-Shell Spin Geometry

Why it matters:

The shell model has literal inward future compression and outward past record
orientation. A purely Riemannian or compact spin geometry may miss causal
orientation. A Lorentzian/conformal spin geometry candidate should be tested as
an alternative, especially for shell-time and gravity-model alignment.

Existing evidence:

Current v5 has twistor-like and shell adapters, but no full standalone
Lorentzian/conformal shell-spin candidate in the individual geometry-scout
matrix.

Related evidence:

```text
system_v5/ops/formal_scouts/results/twistor_hopf_spinor_adapter_probe_results.json
system_v5/docs/JOSHUA_EISENHART_AXIS0_PHYSICS_MODEL_CORE_20260526.md
system_v5/docs/RETROCAUSAL_POSSIBILITY_FIELD_SIM_AND_WIZARD_METHOD_20260526.md
```

Recommended next sim:

```text
sim_lorentzian_conformal_shell_spin_geometry_candidate_probe.py
```

Required controls:

- shell orientation erased
- null/conformal structure erased
- time radius collapsed
- forward-only causal shadow
- twistor label only
- scalar entropy primary

### 6. Symplectic / Contact / Kahler / Berry-Holonomy Geometry

Why it matters:

If terrains and operator stages include phase flow, loops, hysteresis, Berry
phase, or action-like path geometry, then symplectic/contact/Kahler-style
geometries are relevant alternatives. They should not remain old v4 bridge
labels.

Existing evidence:

Legacy/proposal surfaces mention contact, symplectic, Kahler, Berry, holographic,
and Dirac bridge candidates, but those are not current source-native individual
geometry receipts.

Related legacy/proposal handles:

```text
system_v5/ops/c4_divergence_log_proposals.json
system_v5/ops/formal_scouts/results/two_root_constraint_cross_family_countermodel_transfer_probe_results.json
```

Recommended next sims:

```text
sim_symplectic_contact_phase_flow_geometry_candidate_probe.py
sim_kahler_projective_spinor_geometry_candidate_probe.py
sim_berry_holonomy_shell_loop_geometry_candidate_probe.py
```

Required controls:

- symplectic form degenerate
- contact condition erased
- phase holonomy erased
- loop order commuted
- density-only carrier
- no PEPS3D support

### 7. Information-Metric Geometry

Why it matters:

Entropy is not the primary object, but the project needs actual geometry for
QIT readouts: Bures distance, quantum Fisher information, Fisher-Rao geometry,
relative entropy geometry, contractive metrics, and distinguishability
capacity. These are alternatives for readout geometry, not substitutes for the
shell object.

Existing evidence:

Docs discuss these, but this is not yet a standalone individual geometry
candidate row in the current matrix.

Related docs:

```text
system_v5/docs/new content/distance_metrics_state_space.md
system_v5/docs/new content/quantum_fisher_information_geometry.md
```

Recommended next sim:

```text
sim_qit_information_metric_geometry_candidate_probe.py
```

Required controls:

- noncontractive metric accepted
- CPTP monotonicity broken
- metric detached from shell/cut provenance
- scalar entropy replaces metric
- dense-state closure

### 8. Grassmannian / Flag / Projective Hilbert Geometry

Why it matters:

Spinor networks and projective classes should not collapse into Bloch spheres.
Grassmannian, flag, and projective Hilbert geometries can test subspace,
sheet, and projector structure without using Bloch as the primitive.

Existing evidence:

Projective-design and twistor-like scouts touch this area, but no full
Grassmannian/flag alternative exists in the current individual G-candidate
matrix.

Recommended next sim:

```text
sim_grassmann_flag_projective_spinor_geometry_candidate_probe.py
```

Required controls:

- projective equivalence erased
- subspace incidence erased
- Bloch adapter substitution
- global phase mishandled
- no MPS/PEPS2D/PEPS3D carrier

### 9. Topological / Stratified / Homology / Persistence Geometry

Why it matters:

Layer gluing, closure, terrain patches, and PEPS3D cell carriers may need
topology, stratification, homology, or persistence. Many Phase 2 artifacts
correctly blocked topology claims because lower evidence was missing. That does
not mean topology should be ignored; it means it needs its own bounded sims.

Existing evidence:

Multiple Phase 2 candidate/blocker artifacts explicitly reject premature
topology, sheaf, homology, persistence, and full-closure claims.

Recommended next sims:

```text
sim_stratified_cell_complex_geometry_candidate_probe.py
sim_persistence_homology_shell_support_geometry_candidate_probe.py
sim_sheaf_cosheaf_gluing_geometry_candidate_probe.py
```

Required controls:

- connected-components-only proxy
- topology label only
- persistence over random scalar cloud
- no cell provenance
- no PEPS3D face/cell support
- closure claim without gluing control

### 10. Hypergraph / Multiway / Branch-Space Geometry

Why it matters:

The useful part borrowed from Wolfram-style work is not the ontology. It is
finite branch generation, rewrite order, causal/multiway graph bookkeeping, and
provenance-preserving branch compression. That is directly relevant to
`Omega_r` future possibility sets.

Existing evidence:

```text
system_v5/ops/formal_scouts/results/wolfram_multiway_shell_usefulness_deep_probe_results.json
system_v5/ops/formal_scouts/results/wolfram_hypergraph_peps3d_support_fit_probe_results.json
```

Current status:

Useful as adapter geometry. It should be kept subordinate to the shell/spinor
carrier, not promoted to the model.

Recommended next sim:

```text
sim_multiway_branch_space_geometry_candidate_probe.py
```

Required controls:

- rewrite order erased
- branch provenance erased
- hypergraph label only
- no compatibility weights
- no shell orientation
- no spinor/PEPS3D support

### 11. Exceptional G2 / Spin(7) / Octonionic-Like Geometry

Why it matters:

These are plausible high-dimensional structure alternatives for special
holonomy, containment, and chirality/volume-form constraints. They should be
tested as alternatives/falsifiers, not assumed as the official G-structure.

Existing evidence created in this audit:

```text
system_v5/ops/formal_scouts/results/g2_spin7_containment_direction_falsifier_probe_results.json
```

Current status:

The bounded scout passes locally and fresh-reruns. It shows a finite
G2-like-to-Spin(7)-like containment direction plus reverse-direction falsifier.
It does not select or complete a final G-structure.

Recommended next sim:

```text
sim_g2_spin7_octonionic_spinor_network_candidate_probe.py
```

Required controls:

- orientation erased
- normal-line erased
- reverse containment falsely accepted
- tensor form labels without spinor carrier
- no PEPS3D locality

### 12. Gauge / Bundle / Connection Geometry Beyond U(1) And SU(2)

Why it matters:

The current scout list includes U(1), SU(2), SO(3), Pin/Spin, and Clifford
families. It does not test broader bundle/connection families that may matter
for local operator actions, holonomy, or internal degrees of freedom, and it is
not itself the true G-structure.

Candidate families:

- principal bundle connection geometry
- Spin^c geometry
- SU(3) or SU(n) internal-gauge candidates
- gerbe / higher-bundle candidates
- finite holonomy groupoids

Recommended next sims:

```text
sim_principal_connection_holonomy_geometry_candidate_probe.py
sim_spinc_spinor_bundle_geometry_candidate_probe.py
sim_su3_internal_gauge_geometry_candidate_probe.py
sim_gerbe_higher_bundle_geometry_candidate_probe.py
```

Required controls:

- connection erased
- curvature/holonomy erased
- gauge label only
- bundle projection not finite
- no spinor payload
- no PEPS3D carrier support

## Do Not Promote These As Geometry Without New Controls

The following should remain controls or adapters unless a new finite map earns
them:

- Bloch sphere as primitive geometry
- Cartesian xyz coordinate primitives
- dense full-state Hilbert closure
- generic tensor network without spinor provenance
- entropy scalar as primary geometry
- FEP label without shell prediction/evidence/update fields
- Axis0 scalar without `A0_raw` shell-gradient provenance
- Wolfram/ruliad language without finite branch provenance and shell support

## Recommended Next Batch

The next geometry-alternative campaign should not rerun the already-green 12
geometry-scout candidates. It should add a new alternatives tranche:

```text
GA01 finite_probe_effect_weyl_geometry
GA02 contextual_sheaf_presheaf_geometry
GA03 process_povm_quantum_comb_geometry
GA04 projective_design_spectral_triple_geometry
GA05 lorentzian_conformal_shell_spin_geometry
GA06 symplectic_contact_kahler_holonomy_geometry
GA07 qit_information_metric_geometry
GA08 grassmann_flag_projective_spinor_geometry
GA09 stratified_cell_homology_persistence_geometry
GA10 multiway_branch_space_geometry
GA11 g2_spin7_exceptional_geometry
GA12 gauge_bundle_connection_geometry
```

Each row must follow the same admission surface as the current individual
geometry-scout rows:

```text
finite map
F01/N01 witnesses
torch-native spinor or spinor-derived density
MPS view
PEPS2D view
PEPS3D site/bond/face/cell support
8/16/32/64 scale where meaningful
QIT entropy/readout provenance
tool manifest and non-vacuous tool ablations
negative controls
blocked consumers
fresh result receipt
```

## Validation Performed During This Audit

The existing `G2/Spin(7)` source had no result receipt before this audit.
I ran and fresh-validated it:

```text
source:
system_v5/ops/formal_scouts/sim_g2_spin7_containment_direction_falsifier_probe.py

result:
system_v5/ops/formal_scouts/results/g2_spin7_containment_direction_falsifier_probe_results.json
```

Validation:

```text
scripts/lint_sim_contract.py ...sim_g2_spin7_containment_direction_falsifier_probe.py
  checked=1, violation_total=0

validate_formal_scout_results.py --fresh-rerun ...g2_spin7_containment_direction_falsifier_probe_results.json
  all_pass=true, fresh_rerun=true
```
