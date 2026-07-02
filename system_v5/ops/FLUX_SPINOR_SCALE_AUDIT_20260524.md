# Flux / Spinor / Scale Audit

Status: hard correction audit after user stop request.

This audit answers one question:

> Do the current flux/system sims satisfy the required modeling surface:
> 8+ qubits/sites first, PyTorch-native, explicit spinor-network state, bounded
> geometry/manifold layers, and no toy 2/3-qubit flux substitution?

Initial audit answer: **no pre-existing row fully satisfied that whole gate**.

Repair rung added after this audit:

- `system_v5/ops/formal_scouts/sim_eight_node_spinor_network_flux_current_gate_probe.py`
- `system_v5/ops/formal_scouts/results/eight_node_spinor_network_flux_current_gate_probe_results.json`
- `system_v5/ops/formal_scouts/sim_explicit_spinor_entanglement_engine_manifold_8q_probe.py`
- `system_v5/ops/formal_scouts/results/explicit_spinor_entanglement_engine_manifold_8q_probe_results.json`
- `system_v5/ops/formal_scouts/sim_explicit_spinor_full_igt_64_substage_engine_cycle_probe.py`
- `system_v5/ops/formal_scouts/results/explicit_spinor_full_igt_64_substage_engine_cycle_probe_results.json`
- `system_v5/ops/formal_scouts/sim_explicit_spinor_full_igt_schedule_mps_peps_peps3d_portability_probe.py`
- `system_v5/ops/formal_scouts/results/explicit_spinor_full_igt_schedule_mps_peps_peps3d_portability_probe_results.json`
- `system_v5/ops/formal_scouts/sim_geometric_constraint_manifold_ijk_flux_shell_fuzz_engine_probe.py`
- `system_v5/ops/formal_scouts/results/geometric_constraint_manifold_ijk_flux_shell_fuzz_engine_probe_results.json`
- `system_v5/ops/formal_scouts/sim_explicit_spinor_mps_8_16_32_64_flux_scaling_probe.py`
- `system_v5/ops/formal_scouts/results/explicit_spinor_mps_8_16_32_64_flux_scaling_probe_results.json`
- `system_v5/ops/formal_scouts/sim_two_root_constraint_spinor_entanglement_8_16_32_64_basin_boundary_carrier_probe.py`
- `system_v5/ops/formal_scouts/results/two_root_constraint_spinor_entanglement_8_16_32_64_basin_boundary_carrier_probe_results.json`
- `system_v5/ops/formal_scouts/sim_explicit_spinor_peps3d_64_site_geometry_flux_probe.py`
- `system_v5/ops/formal_scouts/results/explicit_spinor_peps3d_64_site_geometry_flux_probe_results.json`
- `system_v5/ops/formal_scouts/run_flux_spinor_full_suite_20260524.py`
- `system_v5/ops/formal_scouts/results/flux_spinor_full_suite_20260524_results.json`

This new row is the first current **8-node, PyTorch-native, explicit Hopf
spinor-network flux-current formal scout**. It is still only a first-rung
formal scout and does not admit final flux, Axis0, Xi, physics, PEPS3D closure,
or attractor-basin convergence.

After the first repair receipt, this row was hardened with independent
edge-registry variants and adversarial near-degenerate spinor fixtures. Those
controls are now part of the current receipt.

A second scale row now carries explicit Hopf spinor source states through
torch-native MPS compression at 8, 16, 32, and 64 sites. This is scale evidence
for explicit-spinor MPS transport only; it is not PEPS3D closure and not final
flux.

A stricter 8-qubit density-matrix engine row now runs explicit Hopf spinors
through bounded manifold-layer U/E blocks under T1/T2 engine schedules. Its
first version correctly failed because local dephasing erased the entanglement
signature; the repaired version keeps E load-bearing without wiping out the cut
signal. Current receipt:

- T1/T2 noncommuting signature gap: `0.08291116426978302`
- commuting-only T1/T2 gap: `1.4602703977091186e-15`
- zero-current signature gap: `4.331727886191228`
- reversed-current signature gap: `0.24014531261206776`
- shuffled-edge signature gap: `15.999974478732026`
- gauge signature gap: `3.961178668390469e-15`
- T1 cut mutual information: `0.47078111661227595`
- T1 log-negativity: `0.45050287118477933`

This is the first current row in this audit that combines explicit spinors, an
8-qubit density carrier, noncommuting engine-order separation, bounded
manifold-layer current, and entanglement readouts. It is still a formal scout
and does not admit Axis0, Xi, final flux, PEPS3D closure, or physics.

A carrier-adapter row now ports explicit Hopf spinor entanglement into the
two-root basin-boundary 8/16/32/64 scaling line. It is edge-factorized QIT cut
evidence, not a full 64-qubit dense global state and not full MPS/PEPS/PEPS3D
environment closure. Current receipt:

- site counts: `8, 16, 32, 64`
- minimum cut log-negativity sum: `2.22944253016638`
- minimum mean edge coherent information: `0.18740774079108838`
- minimum noncommuting gap: `0.14427718424311364`
- maximum gauge signature gap: `3.972442522218699e-15`
- product ablation minimum gap: `2.7357486537563647`
- commuting-only ablation minimum gap: `2.1899465344439464`
- erased-cut ablation minimum gap: `2.1673975506845102`
- shuffled-topology ablation minimum gap: `1.211124823260623`

This closes one audit gap: a two-root 8/16/32/64 basin-boundary row can now
consume an explicit spinor-entanglement carrier. It does not prove real
attractor-basin convergence.

A corrected full-IGT engine-cycle row now encodes the owner-specified stage
grammar directly:

- two engine types;
- eight macro stages per engine;
- four operator substages per macro stage;
- all four substages inherit the macro-stage Axis6 sign;
- 32 substages per engine and 64 total across the paired cycle;
- eight terrain variants, four topologies, and four operators are present.

Current receipt:

- engine count: `2`
- macro-stage count: `16`
- total substage count: `64`
- substages per engine: `32`
- terrain variant count: `8`
- topology count: `4`
- operator count: `4`
- outer/inner loop-pair count: `8`
- same-sign macro-stage count: `16`
- mixed-Axis6 control signature gap: `16.000034217983046`
- native-only substage-collapse gap: `48.05258398058603`
- one-engine-only collapse gap: `34.2004402602469`
- gauge signature gap: `1.213671854215944e-15`
- left/right mutual information: `0.07276723568834065`
- left/right log-negativity: `0.016885011223859086`

This repairs the specific "eight stages times four operators" IGT grammar
failure. It is still an 8-qubit explicit-spinor density carrier formal scout,
not MPS/PEPS/PEPS3D closure for the corrected 64-substage schedule and not a
physics claim.

A follow-on portability row now drives the corrected 64-substage schedule
through three bounded carrier families:

- MPS explicit-spinor carriers at `8`, `16`, `32`, and `64` sites;
- a local PEPS carrier at `4x4 = 16` sites;
- a local PEPS3D carrier at `4x4x4 = 64` sites.

Current receipt:

- total substage count: `64`
- MPS site counts: `[8, 16, 32, 64]`
- PEPS site count: `16`
- PEPS3D site count: `64`
- mixed-Axis6 control signature gap: `0.07459654112447972`
- native-only substage-collapse gap: `127.48967847638824`
- one-engine-only collapse gap: `84.7864669185643`
- shuffled tensor-topology gap: `0.2552088814055256`
- gauge signature gap: `1.7086909144292183e-05`

The gauge tolerance is `1e-4` because the repo-local MPS helper uses complex64
SVD; the measured gauge gap is far below the adversarial control gaps. This row
is schedule/carrier portability evidence only. It still does not perform full
PEPS/PEPS3D environment contraction, terrain-law GKSL updates for every
substage, Axis0/FEP attachment, final flux, or physics.

A source-layout IJK flux row now repairs a deeper naming failure: `i,j,k` are
literal quaternion units, not invented labels and not arbitrary readout axes.
The running row lays out the source-backed axes, terrains, operators, and engine
schedule, then computes a bounded 3-component flux quaternion from local
spinors. The `j,k` components are shell-fuzz components. The quaternion units
are pure quaternion coefficients, and the law is:
`local spinor -> unit quaternion -> relative quaternion product`.

Current receipt:

- row count: `64`
- terrain variant count: `8`
- flux component count: `3`
- IJK flux magnitude: `0.27279499189739354`
- i-component magnitude: `0.2640943185163973`
- j/k shell-fuzz magnitude: `0.06834689847870694`
- scalar-only signature gap: `0.058627466735911495`
- j/k-erased signature gap: `0.058627466735911495`
- shell-shuffle signature gap: `0.021155387173642407`
- i-coefficient erasure gap: `0.3351997592227368`
- missing-axis-layout gap: `1.0004236184025221`
- quaternion algebra gate: `Q_I^2=Q_J^2=Q_K^2=-1`, `Q_I Q_J=Q_K`,
  `Q_J Q_K=Q_I`, `Q_K Q_I=Q_J`, with anticommuting reverse products.
- spinor/quaternion representation guard: `pass`, blocked-surface leak count
  `0`

This row is evidence that the corrected terrain/axis/operator schedule can
carry a non-scalar literal-quaternion IJK flux candidate on an 8-qubit explicit
spinor carrier. It is not final flux, not a final source-derived coefficient
law, not PEPS/PEPS3D environment closure, not terrain-law GKSL closure across
all substages, and not physics.

A third row now builds a pure-torch 64-site `4x4x4` PEPS3D local tensor carrier
from explicit Hopf spinor source states and bounded geometry-current layers. It
does not use quimb/cotengra as the substrate, does not construct a dense
`2**64` state, and still blocks full PEPS3D environment contraction.

The current mixed full-suite runner now reruns the bounded flux/spinor/scale/
Axis0/Holodeck/IGT/science formal-scout rows under writable numba/matplotlib
caches and serial cotengra contraction planning. The repaired suite result is
green:

- script count: `29`
- passed scripts: `29`
- failed or missing scripts: `[]`
- formal-scout validation: `true`
- static sim-contract lint: `true`
- elapsed seconds: `309.9772002696991`

The suite is an orchestration receipt only. It does not promote final flux,
Axis0, Xi, PEPS3D closure, Standard Model, gravity, Yang-Mills, Riemann, or any
physics claim.

Separate slow-path PEPS ladder rows also passed after the MPS path:

- `sim_mps_peps_sheet_topology_entropy_deformation_comparison_probe.py`
  / `mps_peps_sheet_topology_entropy_deformation_comparison_probe_results.json`
  — MPS chain versus 2D PEPS sheet.
- `sim_mps_peps_peps3d_entropy_deformation_volume_comparison_probe.py`
  / `mps_peps_peps3d_entropy_deformation_volume_comparison_probe_results.json`
  — MPS chain, PEPS sheet, and 3D PEPS volume comparison.
- `sim_source_native_peps3d_32_64_site_capacity_probe.py`
  / `source_native_peps3d_32_64_site_capacity_probe_results.json`
  — source-native 32-site and 64-site PEPS3D capacity carrier.
- `sim_source_native_peps3d_64_site_bond_dimension_slot_dynamics_probe.py`
  / `source_native_peps3d_64_site_bond_dimension_slot_dynamics_probe_results.json`
  — 64-site PEPS3D operator-slot updates at bond dimensions `2`, `3`, and `4`.

Those four PEPS-ladder receipts validated cleanly and the patched source files
passed static sim-contract lint. They are still formal scouts, not final
environment contraction, not long-horizon engine convergence, and not physics.

Additional environment and PEPS3D boundary rows were then rerun:

- `sim_source_native_multicarrier_subdense_environment_contraction_probe.py`
  / `source_native_multicarrier_subdense_environment_contraction_probe_results.json`
  — MPS/PEPS/PEPS3D local tensor updates with nearest-neighbor subdense
  local-environment contractions across MPS16, PEPS16, PEPS3D32, and PEPS3D64.
- `sim_lirpa_peps3d_size_normalized_environment_scaling_probe.py`
  / `lirpa_peps3d_size_normalized_environment_scaling_probe_results.json`
  — PEPS3D32/PEPS3D64 local environment signal survives edge-count and
  sampled-edge normalization checks.
- `sim_two_root_constraint_peps3d_contraction_order_boundary_probe.py`
  / `two_root_constraint_peps3d_contraction_order_boundary_probe_results.json`
  — local PEPS3D contraction-order boundary/escape witness, with
  `contraction_order_gap = 0.5537587404251099`, `control_count = 15`, and
  all controls rejected.
- `sim_peps3d_substrate_quotient_distinguishability_probe.py`
  / `peps3d_substrate_quotient_distinguishability_probe_results.json`
  — tiny `2x2x2` PEPS3D substrate distinguishability check against flattened,
  wrong-adjacency, scalar-projection, and zero-tensor controls.

These environment/boundary receipts also validated cleanly and their sources
passed static sim-contract lint. They are stronger PEPS3D environment-adjacent
evidence than the carrier-only rows, but they still do not prove a full
PEPS/PEPS3D environment theorem, gauge-invariant finite-size geometry, real
attractor-basin convergence, final Axis0, or physics.

The repo has real 8/16/32/64-site tensor evidence, including MPS, PEPS, and
PEPS3D formal scouts. The repo also has real spinor/twistor formal scouts. The
gap is that these are mostly disjoint:

- the 8+ tensor rows are generally generic qubit/tensor/density carriers, not
  explicit Hopf/spinor networks;
- the explicit spinor/twistor rows are small, mostly 3-spinor or 4-node
  fixtures;
- tiny 2-qubit/3-qubit cut-current or spinor diagnostics must not be counted as
  flux evidence.

## Hard Gates Going Forward

A sim may be called flux-system evidence only if it passes all required gates:

1. **Scale gate:** primary positive fixture is at least 8 qubits/sites. Two- and
   three-qubit rows can only be negative controls, analytic baselines, or
   debugging diagnostics.
2. **Torch gate:** core nonclassical math is PyTorch-native. NumPy may not be the
   source substrate for nonclassical state evolution.
3. **Spinor-network gate:** state is explicitly built as a finite spinor network:
   local `psi_i in C^2`, `rho_i = psi_i psi_i^dagger`, named edges/cuts, and
   network-level readouts. Generic 2**n amplitudes or random PEPS tensors do
   not satisfy this by themselves.
4. **Spinor/quaternion representation gate:** manifold flux coefficient laws
   must be spinor/quaternion-native. The current IJK row has a source-text guard
   that fails if forbidden non-spinor representation surfaces re-enter it.
5. **Bounded-geometry gate:** bounded manifold/geometric layers are live and
   constrain downstream layers. A label called `flux` is not enough.
6. **Flux gate:** flux is a derived current/binding observable with controls:
   zero-flux, shuffled topology, wrong flux, erased flux, and gauge/basis
   controls where relevant. It is not a root, not Axis3, and not a scalar label.
7. **Contract gate:** canonical result JSON has `classification`,
   `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`, claim ceiling, graveyard controls,
   and `promotion_allowed=false` unless a separate admission process exists.
8. **Twistor gate, if claimed:** twistor-like structure must include explicit
   finite incidence variables and tests. Otherwise it is not twistor evidence.

## Evidence Classification

| Artifact | Scale | Torch | Explicit Spinor Network | Twistor | Evidence Status |
|---|---:|---|---|---|---|
| `sim_geometric_constraint_manifold_stage_flux_8qubit_pytorch_topology_probe.py` / `geometric_constraint_manifold_stage_flux_8qubit_pytorch_topology_probe_results.json` | 8 qubits | yes | no | no | Valid 8-qubit topology/flux diagnostic only. It blocks 2-qubit collapse but is not spinor-network flux evidence. |
| `sim_peps3d_64_site_no_dense_environment_topology_flux_probe.py` / `peps3d_64_site_no_dense_environment_topology_flux_probe_results.json` | 64-site PEPS3D | yes | no | no | Valid 64-site PEPS3D local topology-flux infrastructure. Not full environment contraction, not spinor-network evidence. |
| `sim_source_native_peps3d_64_site_slot_dynamics_closeout_probe.py` / `source_native_peps3d_64_site_slot_dynamics_closeout_probe_results.json` | 64-site PEPS3D | yes | no | no | Weak/provisional 64-site slot dynamics. Not long horizon, not EngineCore dynamics, not spinor-network evidence. |
| `sim_two_root_constraint_8_16_32_64_site_basin_boundary_scaling_probe.py` / `two_root_constraint_8_16_32_64_site_basin_boundary_scaling_probe_results.json` | 8/16/32/64 tensor signatures | yes | no | no | Strong bounded formal scout for F01/N01 site-scaled basin-boundary fixtures. Not real attractor basin, not final manifold, not spinor-network flux. |
| `sim_single_chiral_thirty_two_substage_site_width_mps_topology_flux_probe.py` / `single_chiral_thirty_two_substage_site_width_mps_topology_flux_probe_results.json` | 32-site MPS | yes | no/partial | no | Valid 32-site MPS topology/flux diagnostic. Still not explicit spinor network and not final flux. |
| `sim_mps_local_boundary_path_fep_scaling_8_16_32_engine_transport_probe.py` / `mps_local_boundary_path_fep_scaling_8_16_32_engine_transport_probe_results.json` | 8/16/32 MPS | yes | no/unclear | no | Useful MPS transport/FEP formal scout. Not global entangled FEP, not PEPS3D, not spinor-network flux. |
| `sim_source_native_multicarrier_8_16_32_site_scaling_probe.py` / `source_native_multicarrier_8_16_32_site_scaling_probe_results.json` | 8/16/32 carriers | yes | no | no | Cross-carrier infrastructure evidence only. |
| `sim_two_root_constraint_l64_doubled_mps_lindblad_pilot_probe.py` / `two_root_constraint_l64_doubled_mps_lindblad_pilot_probe_results.json` | L32/L64 doubled MPS | yes | local ket/rho only | no | Tensor-runtime advance, still first-rung and 1D MPS. Not PEPS3D, not spinor-network flux. |
| `sim_finite_spinor_tensor_network_channel_order_noncommutation_probe.py` / `finite_spinor_tensor_network_channel_order_noncommutation_probe_results.json` | 3-spinor / 3 qubits | yes | yes | no | Real spinor-network formal scout, below required 8+ scale. Not flux evidence. |
| `sim_spinor_twistor_network_clifford_tensor_boundary_next_wave_probe.py` / `spinor_twistor_network_clifford_tensor_boundary_next_wave_probe_results.json` | 4 nodes | yes | yes | yes, finite incidence | Real spinor/twistor-like formal scout, below required 8+ scale. Not full twistor theory and not flux evidence. |
| `sim_runtime_trajectory_receipt_coupling_probe.py` / `runtime_trajectory_receipt_coupling_probe_results.json` | effectively 2-qubit cut pair | yes | no | no | Tiny source-runtime cut-current diagnostic. Must not be cited as flux evidence. |
| `sim_eight_node_spinor_network_flux_current_gate_probe.py` / `eight_node_spinor_network_flux_current_gate_probe_results.json` | 8 nodes / 8 qubits | yes | yes | no | New valid first-rung 8-node spinor-network flux-current formal scout. Not final flux, not PEPS3D, not twistor. |
| `sim_explicit_spinor_entanglement_engine_manifold_8q_probe.py` / `explicit_spinor_entanglement_engine_manifold_8q_probe_results.json` | 8 qubits / spinor cut carrier | yes | yes, source spinors + entangling engine | no | New explicit-spinor entanglement engine formal scout. T1/T2 order is load-bearing and cut log-negativity is nonzero. Not Axis0, Xi, final flux, PEPS3D closure, or physics. |
| `sim_explicit_spinor_full_igt_64_substage_engine_cycle_probe.py` / `explicit_spinor_full_igt_64_substage_engine_cycle_probe_results.json` | 8 qubits / 64 substages | yes | yes, source spinors + corrected full IGT cycle | no | New explicit-spinor full-IGT cycle formal scout. Encodes 2 engines, 8 macro stages per engine, 4 same-sign operator substages per macro stage, 64 total substages, and rejects mixed-Axis6/native-only/one-engine collapses. Not MPS/PEPS/PEPS3D closure or physics. |
| `sim_explicit_spinor_full_igt_schedule_mps_peps_peps3d_portability_probe.py` / `explicit_spinor_full_igt_schedule_mps_peps_peps3d_portability_probe_results.json` | MPS 8/16/32/64 + PEPS16 + PEPS3D64 | yes | yes, source spinors + corrected full IGT schedule | no | New corrected-schedule portability scout. Runs the 64-substage grammar through MPS, local PEPS, and local PEPS3D carriers, rejecting mixed-Axis6/native-only/one-engine/shuffled-topology controls. Not full environment contraction, not terrain-law GKSL closure, not physics. |
| `sim_geometric_constraint_manifold_ijk_flux_shell_fuzz_engine_probe.py` / `geometric_constraint_manifold_ijk_flux_shell_fuzz_engine_probe_results.json` | 8 qubits / 64 substages | yes | yes, source spinors + source terrain layout | no | New source-layout IJK flux scout. Runs all eight terrain variants and all 64 substages, keeps flux as non-scalar literal quaternion `(i,j,k)`, treats `j,k` as shell-fuzz components, gates the quaternion multiplication table with pure quaternion coefficients, and has a spinor/quaternion-only representation guard. Not final flux, not final source-derived coefficient law, not PEPS3D closure, not physics. |
| `sim_explicit_spinor_mps_8_16_32_64_flux_scaling_probe.py` / `explicit_spinor_mps_8_16_32_64_flux_scaling_probe_results.json` | 8/16/32/64 MPS sites | yes | yes, source spinors | no | New explicit-spinor MPS scale formal scout. Not dense 64-qubit state, not PEPS3D closure, not final flux. |
| `sim_two_root_constraint_spinor_entanglement_8_16_32_64_basin_boundary_carrier_probe.py` / `two_root_constraint_spinor_entanglement_8_16_32_64_basin_boundary_carrier_probe_results.json` | 8/16/32/64 edge-factorized QIT cuts | yes | yes, source spinors + edge entanglement | no | New two-root basin-boundary carrier-adapter row. Proves this scaling line can consume explicit spinor-entanglement carriers. Not real basin convergence and not full global 64-qubit evolution. |
| `sim_explicit_spinor_peps3d_64_site_geometry_flux_probe.py` / `explicit_spinor_peps3d_64_site_geometry_flux_probe_results.json` | 64-site `4x4x4` PEPS3D local tensor carrier | yes | yes, source spinors | no | New explicit-spinor PEPS3D local tensor formal scout. Not full PEPS3D environment contraction, not final flux. |
| `sim_mps_peps_sheet_topology_entropy_deformation_comparison_probe.py` / `mps_peps_sheet_topology_entropy_deformation_comparison_probe_results.json` | 8-site MPS and 2x4 PEPS | yes | no | no | MPS-to-PEPS ladder comparison passed. Formal scout only; not source-native Weyl density history on PEPS sheets. |
| `sim_mps_peps_peps3d_entropy_deformation_volume_comparison_probe.py` / `mps_peps_peps3d_entropy_deformation_volume_comparison_probe_results.json` | 8-site MPS, PEPS, PEPS3D comparison | yes | no | no | Chain/sheet/volume tensor-network comparison passed. Formal scout only; not final manifold or source-native PEPS3D engine. |
| `sim_source_native_peps3d_32_64_site_capacity_probe.py` / `source_native_peps3d_32_64_site_capacity_probe_results.json` | 32/64-site PEPS3D capacity | yes | no | no | Source-native stage records seed 32/64 PEPS3D carrier capacity. Does not run full 32/64-site source-native engine. |
| `sim_source_native_peps3d_64_site_bond_dimension_slot_dynamics_probe.py` / `source_native_peps3d_64_site_bond_dimension_slot_dynamics_probe_results.json` | 64-site PEPS3D, D=2/3/4 | yes | no | no | 64-site PEPS3D bond-dimension slot dynamics passed. Does not prove long-horizon convergence or optimal bond dimension. |
| `sim_source_native_multicarrier_subdense_environment_contraction_probe.py` / `source_native_multicarrier_subdense_environment_contraction_probe_results.json` | MPS16 / PEPS16 / PEPS3D32 / PEPS3D64 | yes | no | no | Subdense local-environment contraction scout passed. Not a full PEPS/PEPS3D environment theorem and not gauge-invariant finite-size geometry. |
| `sim_lirpa_peps3d_size_normalized_environment_scaling_probe.py` / `lirpa_peps3d_size_normalized_environment_scaling_probe_results.json` | PEPS3D32 / PEPS3D64 | receipt audit | no | no | Size-normalized PEPS3D local-environment scaling passed. Preserves upstream Axis0 blockers and does not prove asymptotic/full environment scaling. |
| `sim_two_root_constraint_peps3d_contraction_order_boundary_probe.py` / `two_root_constraint_peps3d_contraction_order_boundary_probe_results.json` | 8-site PEPS3D cube fixture | yes | no | no | PEPS3D contraction-order boundary witness passed. Tiny boundary fixture only; next required scout is layer-stack portability. |
| `sim_peps3d_substrate_quotient_distinguishability_probe.py` / `peps3d_substrate_quotient_distinguishability_probe_results.json` | 8-site PEPS3D-style cube | yes | no | no | PEPS3D substrate distinguishability passed. Tiny quotient/substrate fixture only, not environment closure. |

## What Went Wrong

1. **Scale and representation were conflated.** An 8+ tensor result was treated
   as if it satisfied the spinor-network requirement. It does not unless the
   state is explicitly built and audited as a spinor network.
2. **Toy diagnostics leaked into flux language.** Two-qubit cut-current and
   small Hopf/Weyl sign probes were correctly useful as diagnostics, but any
   language implying they tested flux was wrong.
3. **`all_pass=true` was overread.** In these receipts, `all_pass=true` means the
   formal scout's local predicate passed. It does not mean flux, Axis0, Xi,
   physics, PEPS3D closure, or attractor-basin convergence is admitted.
4. **Flux current, topology flux, and spinor/twistor incidence were not kept
   separate.** These are different candidate surfaces until a factoring law
   relates them.
5. **Literal quaternion units were under-enforced.** The IJK row now represents
   `i,j,k` as literal quaternion units and gates their multiplication table,
   while keeping only the coefficient law candidate.
6. **The explicit spinor/twistor route did not get scaled first.** The current
   spinor/twistor fixtures are small and should have been lifted to 8+ before
   being discussed as system-level flux candidates.

## Current Truth State

Admitted before the repair rung:

- 8+ tensor formal scouts exist.
- 64-site PEPS3D local carrier/topology-flux infrastructure exists.
- L64 MPS/doubled-MPS formal scouts exist.
- Explicit spinor-network formal scouts exist at small scale.
- Explicit finite twistor-like incidence tests exist at small scale.

Admitted after the repair rung:

- One 8-node PyTorch Hopf spinor-network first-rung formal scout exists.
- It constructs 8 explicit local spinors, `rho_i = psi_i psi_i^dagger`, a
  256-dimensional global state, a finite 12-edge registry, 13 bounded recurrence
  layers, and a derived current-through-cut readout.
- Nominal controls passed:
  - zero-flux signature gap: `0.9092670142836412`
  - reversed-flux signature gap: `1.6929832573781418`
  - shuffled-edge signature gap: `1.1571876817332034`
  - gauge signature gap: `1.0023760032975755e-15`
- Multi-seed stress controls passed across 8 deterministic spinor/phase seeds:
  - minimum zero-flux signature gap: `0.4667076713084033`
  - minimum reversed-flux signature gap: `0.2514504408415865`
  - minimum shuffled-edge signature gap: `0.3704079276622084`
  - maximum gauge signature gap: `8.203463115157585e-16`
- Independent edge-family controls passed:
  - edge-family variant count: `3`
  - minimum edge-family signature gap: `0.05943378359667463`
- Adversarial spinor fixture controls passed:
  - adversarial fixture count: `3`
  - minimum zero-flux signature gap: `0.18180004291164154`
  - minimum reversed-flux signature gap: `0.10231087136246322`
  - minimum shuffled-edge signature gap: `0.27090003431767706`
  - minimum edge-family signature gap: `0.13309341373228603`
  - maximum gauge signature gap: `8.703420767246306e-16`
- Formal-scout validation passed and static sim-contract lint passed.
- One explicit-spinor MPS scale formal scout exists.
- It constructs explicit Hopf spinor source states at 8, 16, 32, and 64 sites,
  enters a torch-native MPS carrier, applies bounded adjacent-edge current gates,
  and avoids dense `2**64` state construction.
- Scale controls passed:
  - site counts: `[8, 16, 32, 64]`
  - maximum site count: `64`
  - minimum zero-current signature gap: `0.3201822374511969`
  - minimum reversed-current signature gap: `0.3583041476902282`
  - minimum edge-family signature gap: `0.02411265614844813`
  - maximum gauge signature gap: `6.627866487720195e-07`
  - maximum MPS bond seen: `2`
- The scale row also passed formal-scout validation and static sim-contract lint.
- One source-layout IJK flux row exists.
- It constructs an 8-qubit explicit-spinor carrier, runs the corrected
  two-engine 64-substage terrain/axis/operator schedule, computes a 3-component
  literal-quaternion `i,j,k` flux, and keeps `j,k` as shell-fuzz components.
- Its quaternion units are pure quaternion coefficients and pass the quaternion
  multiplication table. Its coefficient law uses local spinors mapped to
  quaternions and relative quaternion products.
- IJK controls passed:
  - flux component count: `3`
  - IJK flux magnitude: `0.27279499189739354`
  - j/k shell-fuzz magnitude: `0.06834689847870694`
  - scalar-only signature gap: `0.058627466735911495`
  - j/k-erased signature gap: `0.058627466735911495`
  - i-coefficient erasure gap: `0.3351997592227368`
  - missing-axis-layout gap: `1.0004236184025221`
  - quaternion algebra gate: `pass`
  - spinor/quaternion representation guard: `pass`, blocked-surface leak count
    `0`
- The IJK row passed formal-scout validation and static sim-contract lint.
- One explicit-spinor PEPS3D local tensor formal scout exists.
- It constructs explicit Hopf spinor source states across a 64-site `4x4x4`
  local PEPS3D tensor carrier, applies bounded geometry-current layers, and
  avoids dense `2**64` state construction and full environment contraction.
- PEPS3D-local controls passed:
  - site count: `64`
  - grid shape: `[4, 4, 4]`
  - tensor count: `64`
  - edge count: `144`
  - parameter count: `3456`
  - zero-current signature gap: `3.6624791651844673`
  - reversed-current signature gap: `0.004486131944187638`
  - minimum topology signature gap: `3.8999916303057836`
  - gauge signature gap: `1.452086860819199e-15`
- The PEPS3D-local row also passed formal-scout validation and static
  sim-contract lint.
- The mixed full-suite runner passed:
  - script count: `29`
  - passed scripts: `29`
  - validation pass: `true`
  - lint pass: `true`
- The separate PEPS-after-MPS slow ladder passed:
  - MPS-vs-PEPS sheet comparison: `all_pass=true`
  - MPS-vs-PEPS-vs-PEPS3D comparison: `all_pass=true`
  - source-native PEPS3D 32/64 capacity: `all_pass=true`
  - source-native PEPS3D 64-site bond-dimension slot dynamics: `all_pass=true`
  - validation pass for all four receipts: `true`
  - lint pass for the patched PEPS/MPS/runner sources: `true`
- Environment-adjacent and PEPS3D boundary rows passed:
  - subdense MPS/PEPS/PEPS3D local-environment contraction: `all_pass=true`
  - PEPS3D32/PEPS3D64 size-normalized environment scaling: `all_pass=true`
  - PEPS3D contraction-order boundary: `summary.all_pass=true`
  - PEPS3D substrate quotient distinguishability: `all_pass=true`
  - validation pass for these four receipts: `true`
  - static sim-contract lint for these sources: `true`

Not admitted:

- final flux;
- final source-derived I/J/K coefficient law;
- flux as root, Axis3, or engine law;
- final flux admission from the multi-scale explicit-spinor evidence;
- 8+ twistor-network evidence;
- full PEPS3D environment contraction;
- long-horizon 64-site engine dynamics;
- real attractor-basin convergence;
- Standard Model/gravity/Yang-Mills/physics claims.

## Required Repair Path

The immediate first repair rung has now been created. The remaining valid work
is not another 2-qubit or 3-qubit flux scout. It is to harden and scale the
8-node PyTorch spinor-network fixture:

1. Continue hardening the 8-node spinor network:
   - `psi_i = [exp(i(phi_i + chi_i)) cos eta_i, exp(i(phi_i - chi_i)) sin eta_i]`
   - `rho_i = psi_i psi_i^dagger`
   - finite edge/cut registry
   - bounded geometry layers applied as explicit updates
   - current receipt already includes 8 deterministic seeds, 3 independent
     edge-family variants, and 3 adversarial spinor fixtures
2. Add finite twistor-like variables only after the 8-node spinor fixture remains stable:
   - `omega_i`, `pi_i`
   - finite incidence `I_ij`
   - entropy-only collision control
   - random-phase control
3. Keep flux as derived current, not label:
   - current-through-cut / topology current / incidence-current candidates
   - zero-flux, wrong-flux, shuffled-edge, and gauge controls
4. Port explicit spinor source data into the existing 8/16/32/64
   basin-boundary runner and keep its richer tool/function witnesses honest.
5. Build torch PEPS/PEPS3D tensors seeded from explicit spinor geometry, with
   PEPS3D closure still blocked until a real contraction/environment gate exists.
   - current receipt now has the local tensor carrier but not the environment
     contraction.
6. Add a real PEPS3D local-environment contraction gate before calling any
   PEPS3D row closure evidence.
7. Result must be canonical formal-scout JSON and must explicitly state
   `promotion_allowed=false` until multi-scale controls survive.

## Immediate Audit Ruling

Any current answer saying "flux was tested" without qualifying the above is
incorrect. The accurate wording is:

> Current repo evidence now contains one first-rung 8-node PyTorch Hopf
> spinor-network flux-current formal scout, one explicit-spinor MPS 8/16/32/64
> scale formal scout, one explicit-spinor 64-site PEPS3D local tensor formal
> scout, one corrected explicit-spinor full-IGT 64-substage engine-cycle formal
> scout, one corrected-schedule MPS/PEPS/PEPS3D portability formal scout, one
> source-layout literal-quaternion IJK flux scout that keeps `j,k` as shell-fuzz
> and gates the quaternion multiplication table, a green 29-row bounded
> full-suite orchestration receipt, a green MPS-to-PEPS-to-PEPS3D slow ladder,
> green subdense PEPS3D environment-adjacent rows, older bounded tensor/topology
> diagnostics, and separate small twistor diagnostics.
> It does not contain final flux admission, corrected-schedule PEPS/PEPS3D
> environment closure, a final source-derived I/J/K coefficient law, 8+ twistor-
> network evidence, full PEPS3D environment theorem/closure, terrain-law GKSL
> closure across the corrected schedule, long-horizon 64-site engine convergence,
> or physics claims.
