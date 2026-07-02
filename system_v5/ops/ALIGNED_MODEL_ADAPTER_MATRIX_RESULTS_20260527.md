# Aligned Model Adapter Matrix Results - 2026-05-27

## Status

This packet does **not** prove Joshua Eisenhart's TOE, gravity model, Axis0,
FEP, stacking, flux, or final manifold admission.

It does one bounded thing: it tests whether outside aligned-model math can be
made useful as finite adapters into the repo's v4.3 primary object:

```text
RetrocausalPossibilityField:
  shell-indexed future possibilities
  -> compatibility-weighted inward compression
  -> present survivor
  -> outward past record
```

The scout passes with promotion blocked:

```text
result: system_v5/ops/formal_scouts/results/aligned_model_adapter_matrix_shell_probe_results.json
script: system_v5/ops/formal_scouts/sim_aligned_model_adapter_matrix_shell_probe.py
toolkit: system_v5/ops/formal_scouts/wolfram_shell_toolkit.py
models_tested: 9
strong_adapters: 9
max_peps3d_sites: 64
max_peps3d_bond_dim: 2
promotion_allowed: false
```

A second Wolfram-tooling packet now deepens the strongest branch-machinery
adapter:

```text
result: system_v5/ops/formal_scouts/results/wolfram_shell_toolkit_scale_probe_results.json
script: system_v5/ops/formal_scouts/sim_wolfram_shell_toolkit_scale_probe.py
scales_tested: 64, 128, 256 branches
branchial_graph_edges_at_256: 20076
record_entropy_bits_at_256: 7.943566920
min_crisp_rule_gap: 0.069127541
min_uniform_gap: 0.014615734
promotion_allowed: false
```

A third packet now tests FEP/active-inference math as a QIT boundary-update
adapter derived from the same shell-future object:

```text
result: system_v5/ops/formal_scouts/results/shell_fep_adapter_qit_update_probe_results.json
script: system_v5/ops/formal_scouts/sim_shell_fep_adapter_qit_update_probe.py
branch_count: 128
posterior_gap: 0.358968557
order_gap: 0.085419685
order_erased_gap: 0.0
single_future_gap: 1.034469919
F_Q_bits: 1.688119466
promotion_allowed: false
```

A fourth packet now tests twistor/Hopf/chirality math as finite spinor-density
adapter evidence over PEPS3D shell anchors:

```text
result: system_v5/ops/formal_scouts/results/twistor_hopf_spinor_adapter_probe_results.json
script: system_v5/ops/formal_scouts/sim_twistor_hopf_spinor_adapter_probe.py
rows: 64
LR_density_gap: 0.097571182
chirality_erased_gap: 0.0
hopf_erased_gap: 0.783258775
component_phase_gap_mean: 0.878245201
order_gap: 0.035878182
promotion_allowed: false
```

A fifth packet integrates the three strongest adapter families into one shared
shell-field harness:

```text
result: system_v5/ops/formal_scouts/results/shell_adapter_triad_integration_probe_results.json
script: system_v5/ops/formal_scouts/sim_shell_adapter_triad_integration_probe.py
branch_count: 128
wolfram_branchial_ablation_gap: 0.022200087
fep_evidence_ablation_gap: 0.212588688
twistor_carrier_ablation_gap: 0.190114143
orientation_erased_gap: 0.003568945
single_future_gap: 0.914111213
order_gap: 0.074541829
order_erased_gap: 0.0
promotion_allowed: false
```

## What Worked

All tested model families produced nontrivial adapter effects on the same
finite shell carrier, with controls still blocking model-as-primary promotion.

| Model family | Use kept | Density gap | Control gap | Verdict |
|---|---:|---:|---:|---|
| Wolfram multiway / ruliad | Omega branch and branchial support generator | 0.2393 | 0.2482 | strong adapter |
| FEP / active inference | boundary update and posterior survivor form | 0.0729 | 0.0715 | strong adapter |
| Holography / Bekenstein / entropic gravity | shell-area/boundary capacity pressure | 0.0641 | 0.0769 | strong adapter |
| Twistor / Hopf / chirality | spinor phase and L/R chirality carrier cue | 0.1106 | 0.1029 | strong adapter |
| Causal set / causal dynamics | finite partial-order past-record structure | 0.1678 | 0.1633 | strong adapter |
| Constructor theory | possible/impossible transform grammar | 0.0677 | 0.0677 | strong adapter |
| Path integral / transactional | finite sum over histories and boundary consistency | 0.1343 | 0.2499 | strong adapter |
| Relational QM / operational QIT | probe-relative quotient of distinguishability | 0.1006 | 0.0986 | strong adapter |
| Szilard / Carnot / Landauer | information/accounting cycle with reset cost | 0.1188 | 0.1147 | strong adapter |

The useful interpretation is not "all models are true." It is:

```text
outside model math can provide reusable adapter maps,
but every adapter loses primary shell-field fields if promoted alone.
```

## What Does Not Work

These are explicitly rejected as primary replacements:

- Wolfram crisp rule-time replacing shell-time.
- FEP replacing the shell future-possibility field with cognitive metaphor.
- scalar entropy replacing shell compression provenance.
- holographic screen/temperature replacing literal shell bookkeeping.
- causal order replacing retrocausal future-field compression.
- twistor/Hopf labels replacing actual spinor/density carrier states.
- constructor tasks replacing finite admissible branch transforms.
- path integral language replacing finite Omega_r histories.
- Szilard/Carnot language replacing QIT/accounting checks.

The cross-solver control rejects adapter-as-primary promotion. Downstream
consumers stay blocked: stacking, flux, Xi/Phi0, Axis0, FEP admission, physics,
gravity proof, and final manifold.

## Wolfram Tools Extracted

The prior Wolfram work is now more useful because it has an executable toolkit:

```text
system_v5/ops/formal_scouts/wolfram_shell_toolkit.py
```

Toolkit functions:

- `normalize_omega_branch_table`: turns Wolfram/multiway branches into explicit
  shell-indexed Omega rows.
- `attach_peps3d_supports`: attaches each branch to finite PEPS3D
  site/edge/face/cell support summaries.
- `build_incidence_hypergraph`: builds higher-order branch/support/history
  incidence through XGI.
- `branchial_distance_kernel`: turns branchial graph structure into bounded
  compatibility weights.
- `shell_shear_stress`: compares branch-weight fields without dropping branch
  identity.
- `emit_outward_record`: emits past-facing shell/history provenance after
  compression.

Toolkit self-test in the scout:

```text
attached_rows: 64
incidence_hyperedges: 64
branchial_graph_nodes: 64
branchial_graph_edges: 1118
kernel_weight_sum: 1.0
outward_record.orientation: past_outward
record_entropy_bits: 5.957965195
```

Scale packet self-test:

```text
N = 64, 128, 256
normalized_rows == N
attached_rows == N
incidence_hyperedges == N
branchial weights sum to 1.0
outward_record.orientation == past_outward
record entropy increases with branch count
crisp Wolfram rule-time differs from branchial Omega_r kernel
uniform weights differ from branchial Omega_r kernel
support-erased branches are rejected
```

## Simulation Consequence

The sim process should now use this pattern:

```text
aligned model -> finite adapter -> shell-field object -> controls
```

not:

```text
aligned model -> analogy -> Axis0/FEP/gravity/manifold claim
```

Wolfram is especially useful as branch machinery:

```text
hypergraph/multiway branch generation
branchial distance weighting
causal graph as outward record
observer coarse graining as finite probe quotient
```

but Wolfram rule-time remains a control unless it is replaced by:

```text
shell-indexed noncommuting Omega_r histories
compatibility-weighted inward compression
present survivor
outward past record
```

## Validation

Fresh checks passed:

```text
python3 scripts/lint_sim_contract.py system_v5/ops/formal_scouts/sim_aligned_model_adapter_matrix_shell_probe.py
python3 system_v5/ops/formal_scouts/validate_formal_scout_results.py --fresh-rerun system_v5/ops/formal_scouts/results/aligned_model_adapter_matrix_shell_probe_results.json
git diff --check -- system_v5/ops/formal_scouts/sim_aligned_model_adapter_matrix_shell_probe.py system_v5/ops/formal_scouts/wolfram_shell_toolkit.py system_v5/ops/formal_scouts/results/aligned_model_adapter_matrix_shell_probe_results.json
```

## Next Useful Packet

The next packet should not compare more theories in prose. It should pick the
highest-value adapters and run them deeper:

```text
1. WolframBranchToolingScale:
   scale OmegaBranchTable + BranchialDistanceKernel from 64 to 128/256 branches,
   preserve shell orientation, PEPS3D support, and outward record.

   Status: complete as a bounded formal scout. Result:
   `wolfram_shell_toolkit_scale_probe_results.json`.

2. ShellFEPAdapter:
   run QIT-FEP posterior update over the same Omega_r field and require
   failure when Omega_r or shell orientation is removed.

3. TwistorHopfSpinorAdapter:
   replace supportive Cl(3) context with a real spinor/Hopf/chirality carrier
   row and require density-level entropy/cut changes.
```

The next best packet is now `ShellFEPAdapter`, because the Wolfram branch
tooling has an executable branch/support/outward-record path. FEP should be
tested as a QIT boundary-update adapter derived from the same Omega_r field,
not as a cognitive metaphor or primary replacement.

Status: complete as a bounded formal scout. Result:
`shell_fep_adapter_qit_update_probe_results.json`.

The next best packet is now `TwistorHopfSpinorAdapter`, because the shell branch
machinery and QIT-FEP boundary update both have validated adapter receipts. The
twistor/Hopf packet should make chirality and Hopf projection live on
torch-native spinor-derived densities over PEPS3D anchors, with global phase,
chirality-erased, Hopf-erased, order-erased, and anchor-erased controls.

Status: complete as a bounded formal scout. Result:
`twistor_hopf_spinor_adapter_probe_results.json`.

The next best packet is now an integration packet, not another analogy-mining
packet:

```text
ShellAdapterTriadIntegration:
  Wolfram Omega_r branch/support/outward-record tooling
  + QIT-FEP boundary update
  + twistor/Hopf/chirality spinor-density carrier
  ->
  one shared shell-field adapter harness with controls proving each adapter is
  load-bearing but none replaces the primary RetrocausalPossibilityField.
```

Required controls for that next packet:

- remove Wolfram branchial weights;
- remove QIT-FEP evidence update;
- erase Hopf/chirality carrier;
- erase shell orientation;
- collapse to one future;
- replace noncommuting order with commuting order;
- scalar-entropy-only;
- downstream unlock attempt.

Status: complete as a bounded formal scout. Result:
`shell_adapter_triad_integration_probe_results.json`.

The next best packet should move from aligned-model adapter integration to the
first terrain/operator candidate harness over the same shared shell surface:

```text
ShellTerrainOperatorAdapter:
  shared shell adapter triad posterior
  + finite terrain/operator candidate families
  + PEPS3D local support actions
  ->
  per-terrain/order response vector, controls, killed/kept candidates, and
  downstream locks.
```

This next packet must still block Axis0, Xi/Phi0, flux, physics, stacking, and
final manifold. Its purpose is to start testing allowed local operator/terrain
DoFs on the shell carrier, not to claim the full manifold.

Status: complete as a bounded formal scout. Result:
`shell_terrain_operator_adapter_probe_results.json`.

```text
terrain_laws: 8
placements: 16
full_response_unique_count: 16
entropy_only_unique_count: 14
left_operator_order_gap: 0.274956489088
right_operator_order_gap: 0.308384659818
loop_erasure_gap: 0.255445875
zero_generator_control: collapsed
promotion_allowed: false
```

The scout repaired one harness bug before validation: the zero-generator
control originally included outer-loop preparation, so it measured loop
placement rather than terrain-generator collapse. The final control compares
zero-generator output against the loop-prepared baseline; the loop-erasure
control separately proves that outer-loop preparation remains load-bearing.

The next useful packet is exact Hopf-loop terrain realization, not Axis0 or
flux and not immediate scale testing. Scale testing a loop proxy would amplify
the wrong object.

```text
ShellTerrainExactHopfLoopHarness:
  shell_terrain_operator_adapter
  + explicit Gamma_f^L, Gamma_b^L, Gamma_f^R, Gamma_b^R samples on S3
  + terrain generators integrated along those sampled loops
  + loop-erased / sheet-erased / param-erased / zero-generator controls
  ->
  exact-source-loop response vectors and named blocked consumers.
```

Required outcome:

- preserve the eight terrain laws and sixteen placements from `terrains.md`;
- replace the current outer-loop unitary proxy with sampled Hopf fiber/base
  loops;
- keep the current terrain/operator adapter receipt as a dependency, not as
  terrain-layer admission;
- record which coefficient/operator choices were instantiated and which remain
  untested;
- keep scalar entropy as a companion readout, not the whole object;
- keep terrain admission, Axis0, Xi/Phi0, flux, physics, stacking, and final
  manifold blocked.

After exact Hopf-loop response exists, the following packet can scale branch
counts and run a larger negative battery:

Status: complete as a bounded formal scout. Result:
`shell_terrain_exact_hopf_loop_harness_probe_results.json`.

```text
exact_hopf_loops: 4
samples: 64
terrain_laws: 8
placements: 16
full_response_unique_count: 16
density_only_unique_count: 16
entropy_only_unique_count: 15
fiber_density_variance_max: 0.000000000001
fiber_raw_spinor_path_length_min: 6.242890304516
fiber_projective_spinor_path_length_max: 0.000000029802
base_density_variance_min: 0.476793554784
operator_order_gap: 0.460708868125
promotion_allowed: false
```

This packet corrected the proxy issue found by audit. It now samples the source
Hopf loops directly:

```text
Gamma_f^L, Gamma_b^L, Gamma_f^R, Gamma_b^R
```

The key result is not "density sees the full S3 loop." The key result is the
opposite and is useful: density terrain laws see projected/base behavior, while
fiber-loop global phase is invisible at the density level. The receipt records
raw spinor movement on fiber loops, density flatness on fiber loops, global
phase alias collapse, and SMT rejection of density-only full-S3 promotion.

The next packet can now be scale/negative battery because the loop object is no
longer a unitary proxy:

```text
ShellTerrainOperatorScaleBattery:
  exact Hopf-loop terrain response
  + branch scales 64/128/256
  + PEPS3D support erasure / sheet swap / loop swap / commuting-order controls
  ->
  robustness table for terrain/operator response vectors and named rejected
  variants.
```

Status: complete as a bounded formal scout. Result:
`shell_terrain_operator_scale_battery_probe_results.json`.

```text
sample_scales: 64, 128, 256
terrain_laws: 8
placements: 16
max_total_samples: 256
max_peps3d_sites: 64
max_peps3d_bond_dim: 2
same_sign_delta: 0.145317063
loop_erased_delta: 1.389575735
operator_order_gap: 0.460708868125
promotion_allowed: false
```

The scale battery keeps the exact Hopf-loop object from the previous packet
and adds controls:

- zero-generator collapse across all scales;
- support-erased rejection;
- same-sign sheet control changes response;
- loop-erased control changes response;
- commuting operator-order control collapses;
- SMT rejects treating scale success as terrain/Axis/flux admission.

The next useful packet is parametric terrain-family pressure, not a downstream
claim:

```text
ShellTerrainParametricFamilySweep:
  exact Hopf-loop terrain harness
  + bounded coefficient sweeps for each source terrain family
  + continuous-time step-count sweep
  ->
  stability/falsifier table for which terrain response features survive
  coefficient and integration-step variation.
```

Required outcome:

- keep all eight source terrain laws and sixteen placements;
- distinguish "one coefficient instantiation worked" from "family response is
  stable";
- include failed/falsified coefficient regions as useful evidence;
- keep density-only S3 overclaim, PEPS3D closure, Axis0, Xi/Phi0, flux,
  physics, stacking, and final manifold blocked.

Status: complete as a bounded formal scout. Result:
`shell_terrain_parametric_family_sweep_probe_results.json`.

```text
strengths: 0.25, 0.5, 1.0, 1.5, 2.0
step_counts: 1, 2, 4, 8
variants: 20
terrain_laws: 8
placements_per_variant: 16
full_response_count_min/max: 16 / 16
entropy_only_count_min/max: 15 / 16
promotion_allowed: false
```

This packet closed the immediate "one coefficient instantiation only" risk in
a bounded way. It does not exhaust the source parametric terrain families and
does not solve continuous-time terrain flow. It shows that the full response
vector survives the tested strength/step variants, while scalar entropy alone
is not stable enough to replace the terrain response object.

The next useful packet is an integrator/method check:

```text
ShellTerrainIntegratorComparison:
  exact Hopf-loop terrain response
  + Euler vs midpoint/RK-style bounded integrator comparison
  + step-refinement h, h/2, h/4
  ->
  numerical-method stability table and failed regions, still with downstream
  locks.
```

Required outcome:

- show whether terrain response features are numerical-method artifacts;
- preserve exact Hopf loop sampling and density-vs-spinor visibility limits;
- keep parametric-family exhaustion, terrain admission, Axis0, Xi/Phi0, flux,
  physics, stacking, and final manifold blocked.

Status: complete as a bounded formal scout. Result:
`shell_terrain_integrator_comparison_probe_results.json`.

```text
methods: euler, midpoint, rk4
substeps: 1, 2, 4, 8
method_runs: 12
terrain_laws: 8
placements_per_method: 16
response_count_min/max: 16 / 16
euler_rk4_delta_start: 0.015228647
euler_rk4_delta_end: 0.002005381
promotion_allowed: false
```

This packet reduces the "Euler artifact" risk. The terrain response distinctions
survive Euler, midpoint, and RK4-style bounded updates, and step refinement
reduces the Euler-vs-RK4 delta. It still does not solve continuous flow or
admit the terrain layer.

The next useful packet is terrain/operator composition order, still local:

```text
ShellTerrainOperatorCompositionOrder:
  exact Hopf-loop terrain response
  + Ti/Te/Fi/Fe before-vs-after terrain generator actions
  + commuting/order-erased controls
  ->
  local terrain/operator noncommutation table with blocked downstream
  consumers.
```

Required outcome:

- test terrain-before-operator versus operator-before-terrain on exact Hopf
  loop samples;
- keep response at finite local action level;
- reject route if controls show the order gap is a label artifact;
- keep Axis0, Xi/Phi0, flux, physics, stacking, PEPS3D closure, and final
  manifold blocked.

Status: complete as a bounded formal scout. Result:
`shell_terrain_operator_composition_order_probe_results.json`.

```text
composition_pairs: 64
noncommuting_pairs: 56
structured_commuting_pairs: 8
max_order_gap: 0.029262609
mean_order_gap: 0.013045440
full_response_unique_count: 57
entropy_only_unique_count: 57
scalar_entropy_confound_present: true
same_sign_delta: 0.718506936
loop_erased_delta: 1.428995002
promotion_allowed: false
```

This packet found useful local order sensitivity, but it also found an entropy
confound. Scalar entropy distinguishes the same number of rows as the full
composition response in this finite packet. That does **not** make entropy the
object; it blocks any Axis/FEP/flux interpretation until the confound is
discriminated.

The next useful packet is an entropy-confound discriminator:

```text
ShellCompositionEntropyConfoundDiscriminator:
  terrain/operator composition-order rows
  + x/z probe sign, purity, loop, sheet, and support readouts
  + entropy-preserving perturbation controls
  ->
  table showing which distinctions entropy alone cannot preserve, or an
  honest blocker if entropy remains fully confounded.
```

Required outcome:

- preserve the 64 finite composition pairs;
- test whether entropy-only ranking survives probe-sign, loop, sheet, and
  support controls;
- if entropy remains enough at this finite scale, write that as a blocker, not
  as Axis0/FEP evidence;
- keep Axis0, Xi/Phi0, flux, physics, stacking, PEPS3D closure, and final
  manifold blocked.

Status: complete as a bounded formal scout. Result:
`shell_composition_entropy_confound_discriminator_probe_results.json`.

```text
composition_rows: 64
probe_rotations: (sz, 0.73), (sx, 0.61)
min_rows_changed_probe_frame: 53
max_entropy_gap_delta: 0.000000000000003
max_density_gap_delta: 0.0
support_rows_changed: 64
promotion_allowed: false
```

The discriminator repairs the entropy confound from the composition-order
packet. Scalar entropy could distinguish the same number of rows, but it cannot
preserve probe-frame or support distinctions: entropy and density-gap values
stay invariant under the probe-frame rotations while x/z probe responses change
for most rows. Entropy remains a companion readout, not an Axis/FEP/flux object.

The next useful packet is support-boundary localization for the composition
rows:

```text
ShellCompositionSupportBoundaryStress:
  terrain/operator composition rows
  + finite PEPS3D support summaries
  + support-erased / support-shifted / boundary-flattened controls
  ->
  local support-boundary stress signatures for composition rows, with PEPS3D
  closure still blocked.
```

Required outcome:

- tie composition-order gaps to finite support neighborhoods instead of scalar
  PEPS3D labels;
- reject support-erased and flattened-boundary controls;
- keep PEPS3D closure, Axis0, Xi/Phi0, flux, physics, stacking, and final
  manifold blocked.

Status: complete as a bounded formal scout. Result:
`shell_composition_support_boundary_stress_probe_results.json`.

```text
composition_rows: 64
support_signature_unique_count: 3
support_erased_unique_count: 1
boundary_flattened_unique_count: 1
support_shift_delta: 24.0
max_boundary_weighted_gap: 0.014754299
max_peps3d_sites: 64
max_peps3d_bond_dim: 2
promotion_allowed: false
```

This packet localizes composition rows to finite support-boundary signatures.
It does not prove PEPS3D closure or a boundary environment. It only shows that
finite support signatures are non-vacuous: support erasure collapses the
signature, boundary flattening collapses it, and support shifting changes the
boundary signature. The local stress calculation is torch-native after lint
repair.

The next useful packet is boundary-environment approximation, still not
closure:

```text
ShellCompositionBoundaryEnvironmentApprox:
  support-boundary stress rows
  + bounded local boundary neighborhood contraction proxy
  + dense-environment / flattened-environment / support-erased controls
  ->
  first approximation to local boundary-environment sensitivity, with PEPS3D
  closure still blocked.
```

Required outcome:

- build a finite local boundary-neighborhood response, not a dense global
  environment;
- show dense/flattened/support-erased controls fail or weaken as expected;
- keep PEPS3D closure, Axis0, Xi/Phi0, flux, physics, stacking, and final
  manifold blocked.
