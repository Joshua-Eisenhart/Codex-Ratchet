# Old Sims Axis Variant Sweep - 2026-06-12

```yaml
receipt_kind: old_sims_axis_variant_inventory
created_for: "DEEP-READ LANE - old sims axis-variant code, all axes"
repo: "/Users/joshuaeisenhart/Codex-Ratchet"
write_scope: "exactly this receipt file"
git_action: "none"
promotion_allowed: false
registry_mutation_performed: false
claim_ceiling: "inventory plus proposed registry amendments only"
```

## Fence

```text
This receipt is not a canonical axis registry update.
This receipt does not promote any formal scout, classical baseline, scratch diagnostic, or tool-lego probe.
This receipt does not claim layer completion, manifold admission, bridge admission, physics, FEP, consciousness, gravity, holography, ER=EPR, or final Xi/Phi0.
It only records what the old sim estate computes, which axis each result bears on, and how each candidate could be adapted into a 33-cell or Hopf carrier.
```

## Sweep Accounting

```yaml
scoped_directories:
  - system_v4/probes/
  - system_v5/ops/formal_scouts/
  - system_v5/julia_carrier/
search_basis:
  - "file names containing axis0..axis6, ax0..ax6, Phi0, Xi, terrain, hexagram, entropy_monotone"
  - "content grep for axis/axis0..axis6"
  - "headers, constants, claim ceilings, result JSONs, and declared verdict fields"
raw_axis_content_hits:
  system_v4_probes: 952
  system_v5_ops_formal_scouts: 405
  system_v5_julia_carrier: 300
handling:
  - "expanded distinct math families below"
  - "kept repeated boilerplate/classical coupling rows fenced as estate families when they do not add a new axis distinction"
  - "treated result JSON claim_ceiling fields as binding ceilings"
```

## Per-Find Records

```yaml
- find: "system_v5/julia_carrier/axis0_entropy_monotone.jl"
  result_file: "system_v5/julia_carrier/results/axis0_entropy_monotone_results.json"
  computes: >
    A finite Julia LinearAlgebra map over L/R Weyl spinor density matrices on a nested shell torus
    with 2 shells x 6 phi x 6 chi x 4 eta = 288 sites. It builds rho_joint as the uniform
    mixture of rhoL_i tensor rhoR_i, computes von Neumann entropies, mutual/coherent information,
    trace-norm correlation monotone, and an N01 order witness using z-dephase Ti against x-rotation Fi.
  recorded_result: >
    candidate; promotion_allowed=false; axis0_split_real=true; corr_mono_full=0.46758304760144603;
    n_allostasis=2; n_homeostasis=6; n01_comm_norm=0.2214721729181199;
    n01_diff_MI=0.017160538797660996; n01_sensitive=true.
  axis_bearing:
    axis: 0
    role: "anchor realization / candidate anchor"
  carrier: "Julia ComplexF64 L/R Weyl spinor density matrices on nested torus cells"
  adapter_sketch: >
    Hopf adapter is direct: map each 33-cell row to a deterministic shell/phi/chi/eta sample or
    aggregate bucket; store S_L, S_R, MI_LR, CI_LR, corr_mono, and N01 order deltas. A strict
    33-cell adapter should downsample the 288 lattice without changing the readout definitions.
```

```yaml
- find: "system_v5/julia_carrier/eng_axes12_julia.jl"
  result_file: "system_v5/julia_carrier/results/eng_axes12_julia_results.json"
  computes: >
    Axis1 and Axis2 finite channel maps. Axis1 uses expand/compress Bloch-volume channels over
    spinor density matrices: anti-amplitude damping lengthens the Bloch vector and amplitude damping
    contracts toward |0>. Axis2 uses open/closed entropy exchange: an isothermal Lindblad-like map
    changes entropy while an adiabatic unitary preserves it. QIT and Szilard variants are also present.
    N01 checks compare expand after compress versus compress after expand, and open after closed versus
    closed after open, with wrong-channel controls.
  recorded_result: >
    classification=tool_lego_fit_probe; promotion_allowed=false; all_pass=true; claim ceiling is
    candidate only. Result records Axis1/Axis2 distinctness from Axis5 across sizes.
  axis_bearing:
    axes: [1, 2]
    role: "committed anchor realization candidates"
  carrier: "Julia ComplexF64 L/R Weyl spinor 2x2 density matrices"
  adapter_sketch: >
    A 33-cell/Hopf adapter assigns each cell an expand/compress bit and open/closed bit, then records
    delta Bloch radius, delta entropy, and N01 order gap. It must keep Axis1 radial channel effects
    separated from Axis2 entropy-exchange boundary effects.
```

```yaml
- find: "system_v5/julia_carrier/wb_axis3_terrains_julia.jl"
  result_file: "system_v5/julia_carrier/results/wb_axis3_terrains_results.json"
  computes: >
    Four CP terrain channels over deterministic pseudo-Haar 2x2 spinor density matrices at sizes
    n=8,16,32,64. Se, Ne, Ni, and Si are implemented as Kraus maps resembling bit flip, y flip,
    amplitude damping, and z dephasing. It checks Choi PSD, Kraus completeness, trace distance from
    flat control, purity/entropy deltas, superoperator distances, and Se/Ni order sensitivity.
  recorded_result: >
    classification=tool_lego_fit_probe; all_pass=false because the requested |0><0| positive
    control is false for fixed/eigen channels Ni and Si; finite_map_checks_pass=true;
    all_choi_psd=true; all_kraus_complete=true; n01_satisfied=true;
    n01_channel_commutator_norm=0.18; claim ceiling is candidate finite-map probe only.
  axis_bearing:
    axes: [1, 2, 3]
    role: "Axis3 anchor/variant candidate with Axis1/Axis2 support"
  carrier: "Julia ComplexF64 2-component spinor density matrices and CP channels"
  adapter_sketch: >
    33-cell adapter maps terrain labels Se/Ne/Ni/Si to per-cell CP channels and stores Choi PSD,
    trace preservation, purity/entropy delta, trace distance, and Se/Ni order gap. Hopf adapter
    attaches the terrain channel to each shell/phi/chi/eta cell. The purity-direction issue must
    remain an explicit fence.
```

```yaml
- find: "system_v5/julia_carrier/ax4_julia.jl"
  result_file: "system_v5/julia_carrier/results/ax4_julia_results.json"
  computes: >
    Axis4 variance-order split over L/R Weyl spinor-derived 2x2 density matrices. Strokes are
    Fi x-rotation, Fe z-rotation, Ti z-dephase, and Te x-dephase. It compares deductive U.E.U.E
    sequences against inductive E.U.E.U sequences and uses commuting z-rotation/z-dephase controls.
    The readout is variance trajectory 1-Tr(rho^2), final density, trajectory distance, and
    Frobenius order gap.
  recorded_result: >
    object_id=ax4_variance_order_split_v1; promotion_allowed=false; claim ceiling is Axis4
    variance-order split finite map only. Pure-state boundary trajectory distance is 0.5,
    mixed-state distance is near zero, and commuting control is zero. Several endpoint gaps are
    near numerical zero, so the live signal is trajectory/process, not endpoint alone.
  axis_bearing:
    axis: 4
    role: "committed anchor realization candidate"
  carrier: "Julia ComplexF64 L/R Weyl spinor 2x2 density matrices"
  adapter_sketch: >
    33-cell/Hopf adapter must store the whole four-stroke trajectory, not just the final state.
    Acceptance should require trajectory/process distance plus commuting controls; endpoint-only
    A after B versus B after A is an older insufficient variant.
```

```yaml
- find: "system_v5/julia_carrier/wb_axis5_spectral_gradient_julia.jl"
  result_file: "system_v5/julia_carrier/results/wb_axis5_spectral_gradient_results.json"
  computes: >
    Axis5 spectral/gradient finite map over L/R Weyl spinor 2x2 densities. Spectral operators Ti/Te
    dephase/project in an eigenbasis and raise entropy; gradient operators Fi/Fe are unitary rotations
    and preserve entropy. N01 compares spectral-then-gradient against gradient-then-spectral with a
    commuting z-basis control.
  recorded_result: >
    classification=tool_lego_fit_probe; promotion_allowed=false; all_pass=true; blocked consumers
    include layer-completion, manifold admission, coupling, bridge, Phi0, Xi, Axis0, flux, and physics.
  axis_bearing:
    axis: 5
    role: "committed anchor realization candidate"
  carrier: "Julia ComplexF64 L/R Weyl spinor density matrices"
  adapter_sketch: >
    33-cell/Hopf adapter records entropy gain under spectral operations, near-zero entropy gain under
    gradient unitary operations, and the spectral-gradient N01 order gap. It must be stress-tested
    against Axis1 because older v4 probes found Ax1/Ax5 degeneracy risk.
```

```yaml
- find: "system_v5/julia_carrier/ax6_julia.jl"
  result_file: "system_v5/julia_carrier/results/ax6_julia_results.json"
  computes: >
    Axis6 noncommutation-pressure map over L/R Weyl spinor density matrices on the 2 x 6 x 6 x 4
    nested torus. Operators Ti=Z, Te=X, Fi=Rx, Fe=Rz and terrain channels TerrainZ/TerrainX are
    paired to compute commutator pressure and density-channel composition order gaps.
  recorded_result: >
    object_id=ax6_noncommutation_pressure_julia; promotion_allowed=false; n01_pass=true;
    high-pressure keys include Fi_Fe, Te_Fe, Ti_Fi, Ti_Te, TerrainX_Fe, TerrainX_Ti,
    TerrainZ_Fi, TerrainZ_Te; per-site split has high_pressure_count=164,
    low_pressure_count=412, split_nontrivial=true; claim ceiling is bounded finite-map receipt.
  axis_bearing:
    axis: 6
    role: "committed anchor realization candidate"
  carrier: "Julia ComplexF64 L/R Weyl spinor density matrices plus finite operators/terrain channels"
  adapter_sketch: >
    33-cell adapter computes operator-pair and terrain-operator order-gap vectors per cell.
    Hopf adapter binds those vectors to shell/phi/chi/eta cells and records high/low pressure classes.
```

```yaml
- find: "system_v5/julia_carrier/eng_64_hexagram_julia.jl"
  result_file: "system_v5/julia_carrier/results/eng_64_hexagram_julia_results.json"
  computes: >
    A 64-stage engine scaffold from the 2^6 binary choices of axes 1 through 6. Axis0 is treated as
    entropy/readout, not as a stage bit. The map assigns axis1 expand/compress, axis2 open/closed,
    axis3 Carnot/Szilard family selector, axis4 CW/CCW direction, axis5 hot/cold spectral-gradient,
    and axis6 order_AB/order_BA, then fingerprints channel words on representative L-Weyl densities.
  recorded_result: >
    classification=tool_lego_fit_probe; promotion_allowed=false; claim ceiling is candidate 64
    hexagram stage assembly only. It is a scaffold and axis map, not proof that all axes are complete.
  axis_bearing:
    axes: [0, 1, 2, 3, 4, 5, 6]
    role: "cross-axis engine scaffold / different distinction from individual axis proof"
  carrier: "Julia ComplexF64 2x2 L-Weyl density and finite channel composition"
  adapter_sketch: >
    33-cell adapter either selects 33 representative hexagram rows or adds an explicit 33-row
    projection table. Hopf adapter applies each channel word to a Hopf-derived density cell and
    keeps axis0 as a readout layer.
```

```yaml
- find: "system_v5/julia_carrier/eng_carnot_axiswired_julia.jl"
  result_file: "system_v5/julia_carrier/results/eng_carnot_axiswired_julia_results.json"
  computes: >
    A Carnot-half engine with all six binary axes wired. Axis3 is fixed to Carnot and Axis0 is a
    Clausius/readout layer. It uses 4 strokes from axis1 x axis2, 4 substages from axis5 x axis6,
    and 2 directions from axis4, then computes eta, W_net, cycle entropy, per-stroke rho, per-stroke
    von Neumann entropy, and N01 gaps.
  recorded_result: >
    classification=tool_lego_fit_probe; promotion_allowed=false; all_pass=true; claim ceiling is
    candidate finite-map probe only. Cold-gradient/open-isothermal is noncommuting, hot-spectral/open
    isothermal commutes by z-diagonal degeneracy, and same-channel control commutes.
  axis_bearing:
    axes: [0, 1, 2, 3, 4, 5, 6]
    role: "cross-axis Carnot realization candidate"
  carrier: "Julia ComplexF64 L/R Weyl spinor density matrices"
  adapter_sketch: >
    Direct 33-cell adapter can allocate 32 substages plus one summary/control cell. Hopf adapter
    assigns each cell a stroke/substage channel word and records work, entropy, direction, and order gaps.
```

```yaml
- find: "system_v5/ops/formal_scouts/sim_disc_axis6_order_gap_jax.py"
  result_file: "system_v5/ops/formal_scouts/results/disc_axis6_order_gap_results.json"
  computes: >
    JAX density-matrix Axis6 order-gap discriminator for T after O versus O after T under eight
    bounded operator-terrain couplings. It separates noncommuting order gaps from commuting controls.
  recorded_result: >
    classification=scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false;
    all_pass=true; layer verdict REAL_LAYER but all-16-cells-live is PARTIAL and sparse_only_3of8=true.
  axis_bearing:
    axis: 6
    role: "variant candidate / sparse mechanism witness"
  carrier: "JAX finite density matrices"
  adapter_sketch: >
    Use as an Axis6 33-cell sparse-control adapter: only cells whose operator-terrain pair passes the
    order-gap and commute-control checks become live. Do not inflate sparse 3-of-8 evidence into all-cell coverage.
```

## Xi And Phi0 Bridge/Readout Families

```yaml
- family: "system_v4/probes/axis0_xi_bakeoff_sim.py"
  computes: >
    Hopf/Weyl engine candidate bakeoff over S3/nested Hopf-torus geometry, L/R Weyl spinors,
    fiber/base loop structure, and candidate Xi bridges into cut states. Candidates include
    Xi_shell pointwise shell-label qubit times Weyl-pair state, Xi_hist history-window label
    qubit times Weyl-pair state, and Xi_LR_control.
  recorded_ceiling: "strong executable candidate only; not canon-locked"
  axis_bearing: "Axis0 bridge/adapter variant candidate, not Axis0 admission"
  carrier: "Python/Numpy old engine_core Hopf/Weyl state machinery"
  adapter_sketch: "33-cell adapter would attach Xi label registers to each cell/cut; Hopf adapter is native."
```

```yaml
- family: "system_v4/probes/axis0_xi_strict_bakeoff_sim.py and axis0_xi_law_fingerprint.py"
  computes: >
    Strict CQ Xi bakeoff with Xi_LR_direct as guardrail/control, Xi_shell_cq as a classical shell-label
    register over pair states, and Xi_hist_cq as a classical history register over live engine microstates.
    The law fingerprint normalizes placement labels including 8_23, 16_31, 8_15, canonical prefix drop
    8_15, canonical early width 0_7, and comparison width 0_3.
  recorded_ceiling: "strict candidate law/fingerprint; not final Xi, not Axis0 admission"
  axis_bearing: "Axis0 Xi-history variant candidate and adapter law"
  carrier: "Python/Numpy Hopf/Weyl engine packets"
  adapter_sketch: "Use 33 cells as the finite history/register surface; keep Xi_shell_cq, Xi_hist_cq, and control rows separate."
```

```yaml
- family: "system_v4/probes/sim_bridge_family_xi_point.py, sim_bridge_family_xi_shell.py, sim_bridge_family_xi_history.py"
  computes: >
    Classical finite bridge-family baselines comparing point, shell, and history Xi bridge rows on bounded
    packet families. These distinguish bridge shape but do not carry nonclassical or final-axis admission.
  recorded_ceiling: "classification=classical_baseline; no bridge, GStack, axis, QIT, or nonclassical admission"
  axis_bearing: "Axis0 bridge variants / different distinction from the Axis0 entropy anchor"
  carrier: "Python/Numpy classical finite packets"
  adapter_sketch: "Convert each bridge family into explicit 33-cell rows with one bridge family per row group."
```

```yaml
- family: "system_v5/julia_carrier/xi_shell_bridge_probe.jl and system_v5/ops/formal_scouts Xi-shell audits"
  computes: >
    Finite Xi_shell bridge object with nested Hopf frames and flat S2 product kill controls. Readouts include
    bipartite density diagnostics, nested-vs-flat deltas, branch diagnostics, scrambled Omega control,
    FTL message-capacity checks, one-future controls, coherent-information gradients, Bures metric profiles,
    channel/resource controls, and real Hopf geometry latitude gradients.
  recorded_ceiling: >
    classification=scratch_diagnostic or formal_scout; promotion_allowed=false; formal_admission_allowed=false.
    The coherent-information gradient bridge passed locally, its adversarial audit failed, Bures/channel
    resource audits passed as scout pressure, and all block final Xi, final Phi0, Axis0, physics, bridge promotion,
    and formal admission.
  axis_bearing: "Axis0 Xi/Phi0 bridge candidate pressure, not admitted Axis0"
  carrier: "Julia and JAX finite nested-Hopf density families"
  adapter_sketch: "33-cell/Hopf adapter should treat Xi_shell metric routes as separate candidate readouts with adversarial audit status attached."
```

```yaml
- family: "system_v4/probes/sim_phi0_integrated_bakeoff.py and related Phi0 v4 probes"
  computes: >
    PyTorch candidate comparison over bridge-built bipartite cut states. Candidates include coherent information,
    conditional entropy, mutual information companion, weighted shell-cut coherent information, and a simple
    finite-blocklength proxy D_max(rho_AB || rho_A tensor rho_B). Disqualification rules reject unsigned-only
    primitives for signed Phi0 and reject arbitrary weights when perturbations scramble the ranking.
  recorded_ceiling: "candidate bakeoff / no final Phi0"
  axis_bearing: "Axis0/Phi0 cut-readout variants, not an Axis0 anchor"
  carrier: "PyTorch bipartite density cut states"
  adapter_sketch: "Compute MI, I_c, conditional entropy, weighted shell-cut I_c, and D_max per 33-cell cut-state."
```

```yaml
- family: "system_v5/ops/formal_scouts/sim_two_root_constraint_*_phi0_*.py and sim_spinor_twistor_xi_cut_phi0_bridge_candidate_probe.py"
  computes: >
    Formal-scout Phi0 candidate variants under the two-root constraint frame: coupled E=16 bridge,
    stress controls, L7 Xi-history to Phi0 bridge, Petz recovery, oriented recovery asymmetry,
    process-signature vector, QIT-FEP free-energy, quantum conditional information, spinor/twistor Xi cut,
    boundary-capacity cut, path-weighted cut, MPS bridge rescue/falsifier, coherent recovery, and slow-mode
    terrain repair.
  recorded_ceiling: "classification=formal_scout; promotion_allowed=false; nonpromotion fences present"
  axis_bearing: "Axis0/Phi0 alternative-space variants and falsifiers"
  carrier: "Python/Numpy/PyTorch/JAX depending on scout; finite bridge/cut states"
  adapter_sketch: "Register as Phi0 alternative rows linked to Axis0 only through an explicit Xi->rho_AB->Phi0 adapter, never as direct Axis0 anchors."
```

## Old v4 Wide Axis Variant Estate

```yaml
- estate: "system_v4/probes/sim_wiggle_exploration.py"
  computes: >
    A no-canon exploratory grid of candidate axis wiggles. Ax0 tests dephasing diagonal versus full,
    partial-trace-left embedded versus rho, and eigenvalue truncation. Ax1 tests amplitude damping
    versus unitary, Lindblad dissipator versus Hamiltonian, and depolarizing versus identity. Ax2 tests
    lossy projection versus unitary, partial trace discard versus full keep, and block-diagonal boundary
    versus full open. Ax3 tests U versus U*, parity L/R swap, CP swap+conjugate, and gamma5 chirality
    commutator. Ax4 tests A after B versus B after A, CW versus CCW path integral/process tensor, and
    commutator direction. Ax5 starts curvature/trajectory-bending style variants. Ax6 continues the
    action-side/order theme.
  recorded_ceiling: "classical exploratory baseline; no canon"
  use: "variant quarry only"
```

```yaml
- estate: "system_v4/probes/sim_corrected_axes.py"
  computes: >
    Corrects older Ax3 and Ax4 readings. Ax3 becomes CP inverted mirror psi_L <-> psi_R* instead of
    mere U versus U*. Ax4 becomes Berry phase/path direction instead of endpoint composition alone.
  recorded_ceiling: "correction note/probe; not final canon"
  use: "important killed/redirected variant record"
```

```yaml
- estate: "system_v4/probes/sim_definitive_7axis.py"
  computes: >
    A seven-axis exploratory validation over mixed normalized 4x4 Dirac states: Ax0 coarse/fine
    partition/coarsegraining, Ax1 dissipation/open versus closed, Ax2 boundary concentrated versus spread,
    Ax3 CP mirror, Ax4 process direction CW versus CCW, Ax5 curvature/trajectory bending, and Ax6
    action side A rho versus rho A.
  recorded_ceiling: "classical_baseline; not canonical despite the filename"
  use: "wide historical axis-variant table"
```

```yaml
- estate: "system_v4/probes/sim_broad_axis_search.py and sim_missing_axis_search.py"
  computes: >
    Broad QIT searches for candidate missing axes and independence failures. Candidate variants include
    measurement basis, squeezing, purity gradient, transposition, time reversal, Renyi order, random basis
    rotation, depolarization asymmetry, rank change, off-diagonal phase, conditional entropy, swap symmetry,
    entanglement structure, operator strength/coupling constant, coherence class, Berry phase sign, and
    spectral gap. The missing-axis search explicitly notes Ax1/Ax5 merge risk when overlap is about 0.9997.
  recorded_ceiling: "exploratory search; variant/falsifier source only"
  use: "unbuilt owner-alternative quarry and Axis1/Axis5 degeneracy fence"
```

```yaml
- estate: "system_v4/probes/axis_orthogonality_suite.py, axis_compositional_structure_sim.py, axis_relations_sim.py"
  computes: >
    Older axis relation machinery using representative operator classes, Choi/superoperator matrices,
    Hilbert-Schmidt inner products, commutator grids, k-tuple compositions, a natural order
    6->5->3->4->1->2, pairings/trigrams, and Axis0 moderator interactions.
  recorded_ceiling: >
    Historical benchmark only. PHASE_2_ORTHOGONALITY_NOTES.md overclaims absolute irreducible
    orthogonality and should not be promoted without current gates.
  use: "relation/order/falsifier source, not final orthogonality proof"
```

```yaml
- estate: "system_v4/probes/qit_complete_math_reference.py"
  computes: >
    Reference math for F01/N01 and candidate Axis0 mechanisms: Hopf fiber coarse-graining, partial
    trace over environment, twirling channel, and amplitude-dependent GA0=f(|r|). It is reference
    doctrine, not a result receipt.
  recorded_ceiling: "reference"
  use: "owner-alternative source for Axis0 adapter definitions"
```

```yaml
- estate: "system_v4/probes/levratchet_legacy/*axis* and run_*axis* families"
  computes: >
    Legacy runner suite for full-axis runs, axis0 entropy/fiber checks, axis12 checks, axis4 checks,
    engine32 axis0-axis6 attacks, stage16 axis6 mix checks, terrain8 sign suite, and related older
    engine experiments.
  recorded_ceiling: "legacy runner estate; mixed old contracts; not promoted here"
  use: "implementation history and regression quarry; requires per-run receipt validation before reuse"
```

## Cross-Axis Variant Map

| Axis | Committed anchor now visible in estate | Estate variants found | Unbuilt owner alternatives / adapter work |
| --- | --- | --- | --- |
| 0 | `axis0_entropy_monotone` L/R Weyl entropy/correlation monotone; Axis0 as readout in `eng_64_hexagram`; Xi/Phi0 bridge pressure remains candidate-only. | Hopf fiber coarse-grain/twirling, dephasing diagonal vs full, partial trace, eigen truncation, scalar projection repair, path entropy, holographic boundary, FEP/free-energy, vector bundle/13-shell PEPS/LiRPA, operator-local vector actuator, Xi point/shell/history, Phi0 signed cut candidates, two-root Phi0 recovery/process/free-energy/conditional-information variants. | Build a 33-cell finite Xi/Phi0 adapter with separate shell/history/control rows; basis-invariant Axis0 admission bakeoff; registry `alternative_space_bound` so Axis0 cannot collapse to one scalar. |
| 1 | `eng_axes12` expand/compress CP-channel anchor. | Amplitude damping vs unitary, Lindblad dissipator vs Hamiltonian, depolarizing vs identity, old open/closed/dissipation readings, Ax1/Ax5 merge risk, Stinespring/dilation ambiguity. | Hopf 33-cell expand/compress local-channel table with Stinespring controls; explicit separation stress against Axis5 spectral-gradient entropy changes. |
| 2 | `eng_axes12` open/closed entropy-exchange anchor. | Projection lossy vs unitary lossless, partial trace discard vs full keep, block-diagonal boundary vs full open, frame/boundary representations, concentrated vs spread boundary. | 33-cell boundary operator adapter over Hopf cells; distinguish boundary openness from Axis1 radial dissipation using same carrier and controls. |
| 3 | `wb_axis3_terrains` terrain CP-channel candidate; `eng_64_hexagram` Carnot/Szilard selector. | Carnot/Szilard family, Se/Ne/Ni/Si terrains, CP mirror, parity L/R swap, gamma5 chirality commutator, Hopf phase e+/-i theta, off-diagonal phase; older U vs U* was corrected/demoted. | 33-cell engine-family split using terrain CP channels plus CP/gamma5 controls; repair or fence the purity-direction positive-control failure. |
| 4 | `ax4_julia` variance-order trajectory anchor. | U.E.U.E vs E.U.E.U trajectories, CW/CCW Berry/process direction, A after B vs B after A endpoint composition, commutator direction, process tensor/path-integral direction. | Hopf path-integral or process-trajectory adapter with full per-cell stroke history; endpoint-only variants must remain killed/insufficient unless trajectory evidence survives. |
| 5 | `wb_axis5_spectral_gradient` spectral/gradient anchor. | Spectral vs gradient, FGA/FSA or generator algebra, curvature/trajectory bending, hot/cold Carnot substages, torus/hysteresis-style candidates, Ax1/Ax5 degeneracy search. | 33-cell spectral-gradient entropy-gain matrix separated from Axis1 CP radial changes; dedicated Ax1/Ax5 noncollapse suite on identical carriers. |
| 6 | `ax6_julia` noncommutation-pressure anchor; `disc_axis6_order_gap` sparse JAX witness. | A rho vs rho A, left/right action side, order_AB/order_BA, terrain/operator pressure, action handedness/orientation, stage16 axis6 mix, engine32 axis0-axis6 attacks. | 33-cell noncommutation-pressure matrix over all stage operators and terrain generators; Hopf per-cell high/low action-precedence split with sparse-live counts fenced. |

## What Memory Missed

```text
The committed-memory anchors named axis0_entropy_monotone, wb_axis3_terrains, ax4, ax6, eng_64_hexagram, Xi families, and dual-stack Phi0 rows.
The sweep adds at least these load-bearing estate families: eng_axes12 for Ax1/Ax2, wb_axis5_spectral_gradient for Ax5, eng_carnot_axiswired as a cross-axis Carnot half, disc_axis6_order_gap as sparse JAX Axis6 witness, old v4 wiggle/corrected/definitive/broad/missing axis searches, axis relation/composition/orthogonality suites, Axis0 formal-scout branch closures, and the large two-root Phi0 recovery/process/free-energy/conditional-information family.
```

## Proposed Registry Amendments

```yaml
registry_amendments:
  - id: "alternative_space_bound"
    status: "proposed_only"
    applies_to:
      - "axis0"
      - "axis1"
      - "axis2"
      - "axis3"
      - "axis4"
      - "axis5"
      - "axis6"
    rule: >
      An axis registry row is not admissible unless it records the committed anchor, estate variants,
      rejected or killed variants, unbuilt owner alternatives, carrier, adapter kind, controls, claim ceiling,
      and blocked consumers. A single passed anchor receipt is not enough to erase surviving alternatives.
    required_fields:
      - "axis_id"
      - "committed_anchor"
      - "variant_space_bound"
      - "estate_variants"
      - "killed_or_demoted_variants"
      - "unbuilt_owner_alternatives"
      - "carrier"
      - "adapter_kind"
      - "required_controls"
      - "claim_ceiling"
      - "blocked_consumers"
      - "promotion_allowed"
    variant_roles:
      - "anchor_realization"
      - "variant_candidate"
      - "different_distinction"
      - "killed"
      - "unsupported"
    adapter_kinds:
      - "33_cell"
      - "Hopf"
      - "both"
      - "blocked"
    acceptance:
      - "every axis0..axis6 row has committed_anchor and variant_space_bound"
      - "every variant is assigned one variant_role"
      - "formal_scout, scratch_diagnostic, classical_baseline, and tool_lego_fit_probe rows cannot promote to canonical without an explicit gate result"
      - "Axis0 Xi/Phi0 variants are linked through an explicit Xi -> rho_AB -> Phi0 adapter and never treated as direct Axis0 admission"
      - "Axis1 and Axis5 rows must name a noncollapse check because old searches found degeneracy risk"
      - "Axis4 rows must distinguish trajectory/process evidence from endpoint-only composition evidence"
      - "Axis6 rows must report sparse-live versus all-cell-live status"
```

```yaml
proposed_axis_registry_rows:
  axis0:
    committed_anchor: "axis0_entropy_monotone"
    variant_space_bound:
      includes:
        - "Hopf fiber coarse-grain/twirling"
        - "partial trace"
        - "dephasing diagonal vs full"
        - "Xi shell/history/point"
        - "Phi0 coherent-information and recovery/process/free-energy variants"
        - "FEP/path/holographic/vector-bundle/operator-local scout branches"
      adapter_kind: "both"
      promotion_allowed: false
  axis1:
    committed_anchor: "eng_axes12 expand/compress"
    variant_space_bound:
      includes:
        - "amplitude damping vs unitary"
        - "Lindblad dissipator vs Hamiltonian"
        - "depolarizing vs identity"
        - "Stinespring/dilation controls"
      adapter_kind: "both"
      promotion_allowed: false
  axis2:
    committed_anchor: "eng_axes12 open/closed"
    variant_space_bound:
      includes:
        - "projection loss"
        - "partial trace discard"
        - "block boundary"
        - "frame/boundary representation"
      adapter_kind: "both"
      promotion_allowed: false
  axis3:
    committed_anchor: "wb_axis3_terrains plus eng_64 family selector"
    variant_space_bound:
      includes:
        - "Carnot/Szilard"
        - "terrain CP channels"
        - "CP mirror"
        - "gamma5 chirality"
        - "Hopf phase"
      adapter_kind: "both"
      promotion_allowed: false
  axis4:
    committed_anchor: "ax4 variance-order trajectory"
    variant_space_bound:
      includes:
        - "stroke trajectory"
        - "Berry/path direction"
        - "process tensor direction"
        - "endpoint composition as demoted/killed insufficient variant"
      adapter_kind: "both"
      promotion_allowed: false
  axis5:
    committed_anchor: "wb_axis5_spectral_gradient"
    variant_space_bound:
      includes:
        - "spectral vs gradient"
        - "generator algebra"
        - "curvature/trajectory bending"
        - "hot/cold substages"
        - "Axis1 degeneracy controls"
      adapter_kind: "both"
      promotion_allowed: false
  axis6:
    committed_anchor: "ax6 noncommutation pressure"
    variant_space_bound:
      includes:
        - "A rho vs rho A"
        - "order_AB/order_BA"
        - "terrain/operator pressure"
        - "action handedness"
        - "sparse JAX order-gap witness"
      adapter_kind: "both"
      promotion_allowed: false
```

## Open Checks

```text
1. This receipt did not mutate any registry file. The amendment block is proposal text only.
2. The raw grep estate is large; repeated old runner rows were grouped by math family. Any row selected for promotion still needs a fresh per-file receipt validation.
3. The v4 PHASE_2 orthogonality language is explicitly fenced as historical overclaim until current gates retest it.
4. Axis0 formal-scout branches are alternative-space pressure, not Axis0 admission.
5. Xi/Phi0 candidates remain bridge/readout candidates and must pass adapter-specific controls before any registry anchor change.
```
