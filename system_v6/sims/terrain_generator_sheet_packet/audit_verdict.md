# Terrain Generator Sheet Packet Audit Verdict

Verdict: GENUINE-WITH-CAVEATS.

Bottom line: `system_v6/sims/terrain_generator_sheet_packet/` is not decorative. The packet has three independently shaped engine legs plus an envelope, direct source-line locks, live pair/placement computations, negative controls through the same channel pipeline, and a passing three-engine envelope validator. The caveats are real: Se/Ne `L_k` coefficient sets are present but not explicitly labeled per-set as `PINNED-CHOICE`, and the SMT binds scaled generator entries computed outside the solver rather than deriving the generator formulas symbolically inside the solver.

## Checked Artifacts

- Sources:
  - `system_v5/READ ONLY Reference Docs/terrain math.md` lines 78-83 and 122-137.
  - `system_v5/READ ONLY Reference Docs/terrain rosetta strong math.md` lines 57-58, 71, 151-183.
- Packet:
  - `terrain_generator_sheet_packet_jax.py`
  - `terrain_generator_sheet_packet_pytorch.py`
  - `terrain_generator_sheet_packet_julia.jl`
  - `terrain_generator_sheet_packet_envelope.py`
  - all four JSON results under `system_v6/sims/terrain_generator_sheet_packet/results/`
- Validator:
  - `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/terrain_generator_sheet_packet/results/terrain_generator_sheet_packet_envelope_results.json`
  - Result: `{"ok": true, "result_json": "...terrain_generator_sheet_packet_envelope_results.json"}`

## Source-Lock Fidelity

Pass for the three checked generator families, with one pin-label caveat.

1. `Ni / Pit`
   - Source side: `terrain math.md:80` says `Ni / Pit` is `X_{Ni,L}(rho)=gamma_{Ni,L}D[sigma_-](rho)-i epsilon_{Ni,L}[H_L,rho]`.
   - Packet side: `terrain_generator_sheet_packet_jax.py:313-323` selects `SIGMA_MINUS` and `h_l` for `terrain == "Pit"` unless a control flag is active, then returns `GAMMA_NI * dissipator(jump, rho) - 1j * EPS * comm(h, rho)`.
   - Result side: all three engine JSONs record `source_jump: "sigma_-"`; fixed-point notes say the label policy follows the locked sigma convention.

2. `Ni / Source`
   - Source side: `terrain math.md:81` says `Ni / Source` is `X_{Ni,R}(rho)=gamma_{Ni,R}D[sigma_+](rho)-i epsilon_{Ni,R}[H_R,rho]`.
   - Packet side: `terrain_generator_sheet_packet_jax.py:324-325` returns `GAMMA_NI * dissipator(SIGMA_PLUS, rho) - 1j * EPS * comm(h_r, rho)`.
   - Result side: all three engine JSONs record `source_jump: "sigma_+"`.

3. `Si / Hill` and `Si / Citadel`
   - Source side: `terrain math.md:82-83` defines left/right `Si` laws as Hamiltonian commutator plus projector dephasing in `P_+^L/P_-^L` and `P_+^R/P_-^R`.
   - Rosetta side: `terrain rosetta strong math.md:57-58` requires left/right projectors to be orthogonal, sum to identity, and commute with `K_L/K_R`.
   - Packet side: `terrain_generator_sheet_packet_jax.py:326-331` uses z-axis projectors for `Hill`, x-axis projectors for `Citadel`, and has a commuting-frame control for `Citadel`.
   - Caveat: the chosen axes are honestly marked as `PINNED-CHOICE not source-forced` in `pin_spec`, which is correct because the cited source requires projector structure but does not force those specific axes.

Placement source-lock also passes: `terrain rosetta strong math.md:151-183` locks 16 placements over 4 loops and 8 laws; packet placement tables instantiate 16 rows with line refs to `terrain math.md:122-137`.

## Numeric Recomputes

Pass.

1. Pair-separation cell
   - Target: `Funnel_vs_Cannon trace_distance_rho_0 = 0.016169408011912884`.
   - Live recompute using the repo-pinned interpreter and the JAX source functions gave `0.016169408011912894`.
   - JAX JSON has `0.016169408011912894`; PyTorch has `0.01616940801191288`; Julia has `0.016169408011912884`.
   - Recomputed singular values of the output difference were both `0.016169408011912894`, so trace distance `0.5 * (s1 + s2)` matches the saved cell.

2. Placement loop-coordinate residual
   - Recomputed `Se / Funnel / inner` `loop_coordinate_density_delta_max = 1.763348180982605e-16`, matching JSON exactly.
   - Recomputed `Se / Funnel / outer` `loop_coordinate_density_delta_max = 0.7071067811865475`, matching JSON exactly.
   - This supports the fiber-stationary vs base-visible placement split.

## Pinned-Choice Labeling

Partial pass.

- `Si_frames` pass: all three engines and the envelope show `m_L: z-axis`, `m_R: x-axis`, `status: PINNED-CHOICE not source-forced`.
- `Se` scalar pass: `se_lambda` is marked `PINNED-CHOICE` with the reason that source gives a Se dissipator family but no numeric lambda in the requested refs.
- Caveat: `Se_Funnel_L`, `Se_Cannon_R`, `Ne_Vortex_L`, and `Ne_Spiral_R` coefficient rows are emitted under `pauli_expansion_families`, but the coefficient sets themselves are not explicitly marked `PINNED-CHOICE not source-forced`. The packet includes a family note, but this is weaker than the requested per-set pin labeling.

## Ne Variants

Pass, with labeling caveat.

- Both Ne variants are genuinely computed, not derived by copying one result into the other.
- Code evidence: channels instantiate `Vortex:pure_hamiltonian`, `Vortex:weak_dissipator`, `Spiral:pure_hamiltonian`, and `Spiral:weak_dissipator` separately.
- Computed result evidence:
  - pure pair trace distance: `0.08447356601104442` in Julia, `0.0844735660110443/4` in JAX/PyTorch.
  - weak pair trace distance: `0.0780114314540225` in Julia, `0.07801143145402245` in JAX/PyTorch.
  - envelope `ne_variants_divergence.live_alternatives_distinct` is `true`.
- Caveat: source lines 78-79 define Ne as pure Hamiltonian laws. The weak dissipator variant is a live exploratory pinned variant and should be labeled that way per coefficient set.

## Sigma-Swap SMT

Partial pass.

- Pass: SMT is not just asserting a precomputed boolean. It binds 16 scaled generator-entry real/imag pairs and proves:
  - unsat for forced equality of full Pit and Source generator entries;
  - sat for equality of sigma-swapped Pit-to-Source convention entries;
  - unsat for inequality of the sigma-swapped convention entries.
- Cross-engine evidence:
  - JAX: z3 and cvc5 both pass with `binds_generator_entries: 16`, equality `sat`, inequality `unsat`.
  - PyTorch: z3 and cvc5 same.
  - Julia: Z3.jl same.
- Caveat: this is generator-entry binding after numeric generator construction. It does not symbolically derive the dissipator/commutator entries inside SMT from sigma, H, gamma, and epsilon primitives. If "derive-in-solver" is strict, this needs hardening.

## Erasure Controls

Pass.

- The erasure controls run through the same pipeline: the code builds `erased_channels` with the same `channel_from_generator(generator_fn(...))` path used for ordinary channels.
- Result evidence:
  - `erased_weyl_sign_collapses_Funnel_Cannon: true`
  - `erased_weyl_sign_collapses_Vortex_Spiral_pure: true`
  - `erased_weyl_sign_collapses_Vortex_Spiral_weak: true`
  - `commuting_frame_Si_control_collapses_Hill_Citadel: true`
  - `sigma_swapped_pit_source_convention_equals_source: true`

## Standard Checks

Pass.

- Envelope validator returned `ok: true`.
- Envelope classification is `scratch_diagnostic`.
- `promotion_allowed` is `false`.
- `formal_admission_allowed` is `false`.
- Envelope claim ceiling says: `scratch diagnostic only; no formal admission, canonical terrain claim, or source doctrine promotion`.
- Engine contract says `mode: all_three_full_sims`, lanes `julia`, `jax`, `pytorch`, and `reads_peer_result: false`.
- Three engine legs agree on the checked shared scalars within tolerance.
- Engine-level tool manifests include load-bearing numerical/tool use:
  - Julia: `QuantumOptics`, `LinearAlgebra`, `Z3`.
  - JAX: `jax`, `jax.numpy`, `jax.scipy.linalg`, `z3`, `cvc5`.
  - PyTorch: `torch`, `torch.func`, `z3`, `cvc5`.

## Hardening List

Required next hardening:

1. Add explicit per-family `PINNED-CHOICE not source-forced` metadata for `Se_Funnel_L`, `Se_Cannon_R`, `Ne_Vortex_L`, and `Ne_Spiral_R` coefficient sets, not only `se_lambda` and the generic family note.
2. Strengthen sigma-swap SMT from "bind scaled generator entries" to a symbolic derivation path inside the solver, or explicitly label the current proof as entry-binding SMT rather than derive-in-solver SMT.
3. Add a freshness/source-lock check for the exact requested source line ranges so result JSON cannot stay green if `terrain math.md` or Rosetta source lines change.
4. Add unitality column `E(I)=I` per generator.
5. Add Axis-0 correlation-diversity response per family, with the `(+,+,-,-)` prediction for `(Ne,Ni,Se,Si)` tested as a falsifiable sign pattern.
6. Add entropy columns `Delta-S_system`, `bath-exchange`, and `Delta-S(A|B)` per generator.

Final classification: GENUINE-WITH-CAVEATS.
