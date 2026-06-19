# Fresh Audit Verdict: dual_stack_carnot_szilard_hopf_weyl_probe

Verdict: DECORATIVE.

Bottom line: the artifact is not execution-broken. The envelope validates, all three engine legs report `all_pass=true`, scalar spreads are within tolerance, and the headline is not merely the stroke-level `U/E` gap. But the positive QIT dual-stack witness is not genuine under the pre-audit target because the Szilard measurement object is destructive/classical rather than the pinned coherent joint object, `M` is not a 4x4 joint CPTP channel, the reported MI is the wrong object for the pinned fixture, the sign/chirality control is a sign-flip comparison rather than `H_L=H_R` erasure, and the work ledger is defined from mutual information.

## Commands/checks run

- `scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json` -> `ok: true`.
- Independent Python recomputation of pinned `rho`, source `M`, coherent CNOT-style fixture `M`, source `D_loop`, source `I_loop`, source one-stroke `D`, MI/Ic, Landauer lower bound, and source `M` Choi shape.
- Direct source reads of PyTorch/JAX/Julia/envelope files and result JSONs.

## Overseer question 1: loop-level witness

Answer: the build does compute a source-defined loop-level `D(I(rho_L))` vs `I(D(rho_L))` witness, not only the stroke-level `U/E` gap. This is not pre-audit failure mode E in the narrow "headline is just U/E" sense.

Source evidence:

- `D_loop` applies `E,U,E,U` in `dual_stack_carnot_szilard_hopf_weyl_probe_pytorch.py:182-188`.
- `I_loop_with_ledger` applies `M`, `F`, `R`, then reduces back to the system in `dual_stack_carnot_szilard_hopf_weyl_probe_pytorch.py:249-319`.
- The headline computes `d_after_i_l = D_loop(i_l,+1.0)`, `i_after_d_l = I_loop_with_ledger(d_l)`, and `headline_delta = trace_norm(d_after_i_l - i_after_d_l)` in `dual_stack_carnot_szilard_hopf_weyl_probe_pytorch.py:422-426`.
- The separate stroke-level `ax6_order_gap` is computed independently in `dual_stack_carnot_szilard_hopf_weyl_probe_pytorch.py:436-440`.
- Result label records `left: D(I(rho_L))`, `right: I(D(rho_L))`, `Delta_trace_norm` in `dual_stack_carnot_szilard_hopf_weyl_probe_pytorch.py:555-560`.

Recomputed numbers:

- Source full-loop `||D_loop(I_source(rho)) - I_source(D_loop(rho))||_1 = 1.3490341265562846`.
- Reported `headline_delta_trace_norm = 1.3490341265562846`.
- Source single-stroke `||D_stroke(I_source(rho)) - I_source(D_stroke(rho))||_1 = 0.7828986261595305`.
- Reported `ax6_order_gap_U_E_trace_norm = 0.04955968349315783`; that is the `U/E` commutator readout, not the headline D/I loop witness.

Caveat to harden: section 15 defines the inductive loop as `E o U o E o U` with Szilard insertion, while the current `I_loop` is only the Szilard `M/F/R` reduction. If the literal section-15 inductive loop is required, the current loop is reduced/incomplete even though it is not merely a stroke-level `U/E` gap.

## Overseer question 2: MI naming/object

Answer: wrong-object.

The source computes `mutual_info = S(S)+S(M)-S(SM)` on `rho_m = apply_kraus(rho, M_kraus())`, so the formula name is locally MI. The problem is that `M_kraus()` is two destructive `4x2` Kraus maps, not the coherent CNOT-style pinned fixture. It erases the `|00><11|` coherence, so the object is the classical measured joint state.

Source evidence:

- `M_kraus` creates `k0` and `k1` with shape `(4,2)` and returns them as separate Kraus maps in `dual_stack_carnot_szilard_hopf_weyl_probe_pytorch.py:200-205`.
- `rho_m = apply_kraus(rho, M_kraus())` and `mutual_info = s_s + s_m - s_after_m` in `dual_stack_carnot_szilard_hopf_weyl_probe_pytorch.py:249-258`.
- The result stores `mutual_information_after_M` from that `M_measure_record` in `dual_stack_carnot_szilard_hopf_weyl_probe_pytorch.py:513-514`.
- Recorded `rho_AB_after_M` is diagonal, with `0.853553390593...` and `0.146446609406...`, not the expected coherent off-diagonal joint state.

Recomputed numbers:

- Source after-M offdiag `abs(rho[00,11]) = 0.0`.
- Coherent fixture after-M offdiag `abs(rho[00,11]) = 0.3535533905932738`.
- Source MI `I(S:M) = 0.4164955306996874`.
- Source coherent information `I_c = 0.0`.
- Coherent pinned fixture quantum MI `I(S:M) = 0.8329910613993748`.
- Coherent pinned fixture `I_c = 0.4164955306996874`.
- Reported `mutual_information_after_M = 0.4164955306996874`.
- Reported `coherent_information_after_M = 0.0`.

Adjudication: not correct-object-wrong-name. It is the wrong object for the intended QIT/CNOT-style measurement fixture.

## Checklist A-G

A. Landauer ledger fakery: FAIL.

- Good: `p_memory_excited`, `landauer_lower`, `reset_cost`, and reset gap are computed from the post-feedback memory state in `dual_stack_carnot_szilard_hopf_weyl_probe_pytorch.py:268-275`.
- Bad: `work_extracted = 0.95 * mutual_info` in `dual_stack_carnot_szilard_hopf_weyl_probe_pytorch.py:265`, and `bound_lhs = work_extracted - LN2 * info_bits` in line 266. Because `LN2 * info_bits == mutual_info`, the bound margin is forced to `-0.05 * MI`.
- Recomputed: `landauer_lower_from_p_excited = 0.10150905441283585`; source `memory_entropy_before_reset = reset_cost = 0.4164955306996874`; `work_extracted = 0.39567075416470304`; `bound_lhs = -0.02082477653498438`.

B. Measurement channel honesty: FAIL.

- Source `M` is `2 -> 4`, not `4 -> 4`: `M_kraus` uses `(4,2)` Kraus maps at `dual_stack_carnot_szilard_hopf_weyl_probe_pytorch.py:200-205`.
- Source CPTP check calls `cptp_check("M", M_kraus(), 2, 4)` at `dual_stack_carnot_szilard_hopf_weyl_probe_pytorch.py:451`.
- Recomputed source Choi shape is `8x8`, not required `16x16`; TP residual for the 2-to-4 map is `0.0`.
- It destroys coherence and yields classical MI `0.4164955306996874`, not the pinned quantum MI `0.8329910613993748`.

C. Feedback conditioning: PASS for the source state, but downstream of failed M.

- `feedback_unitary()` is one 4x4 joint operator in `dual_stack_carnot_szilard_hopf_weyl_probe_pytorch.py:208-212`.
- `rho_f = f @ rho_m @ f.conj().T` in `dual_stack_carnot_szilard_hopf_weyl_probe_pytorch.py:262-264`.
- No hidden branch variable controls the density update. This does not rescue the measurement-object failure.

D. Classical control same pipeline: PASS source-level, schema incomplete.

- Source forms `rho_l_diag` at `dual_stack_carnot_szilard_hopf_weyl_probe_pytorch.py:420`.
- It runs the same `I_loop_with_ledger(rho_l_diag)` at line 442.
- Results show `qit_coherence_work_term = 0.0` and `work_extracted = 0.39567075416470304`.
- Caveat: the envelope does not expose the pre-audit's expected `same_pipeline`, input coherence, or `W_qit_coherence/W_classical` field names.

E. Order witness inflated by trivial noncommutation: PASS in narrow sense, CAVEAT on inductive-loop definition.

- Headline is `D_loop(I_loop(rho_L))` versus `I_loop(D_loop(rho_L))`, not the `U/E` stroke gap.
- Recomputed headline `1.3490341265562846`; reported `ax6_order_gap_U_E_trace_norm = 0.04955968349315783` is separate.
- Commuting loop control is `0.0` in the envelope.
- Caveat: current `I_loop` is Szilard `M/F/R`, not the section-15 literal `E o U o E o U` inductive loop with insertion.

F. Memory reset partial-trace leak / stage labels: FAIL.

- The natural cut is reported at after-M (`axis0_cut.rho_AB_stage = "after M_measure_record"`), which is good.
- But the result does not provide an after-R joint cut value or stage-by-stage `after_M`/`after_R` Axis0 table required by the pre-audit.
- Because the after-M object itself is dephased/classical, the reported `Phi0_Ic_S_to_M = 0.0` is also the wrong-object value for the pinned coherent fixture.

G. SMT binding actual 4x4 objects: FAIL strict target, PASS anti-scalar-fake.

- JAX SMT builds `d_super = channel_super(D_kraus(+1.0), 2, 2)` and `i_super = channel_super(I_system_kraus(), 2, 2)`, then compares `d_super @ i_super` vs `i_super @ d_super` in `dual_stack_carnot_szilard_hopf_weyl_probe_jax.py:494-507`.
- Result says `entries_bound = 32`, `derived_from_entrywise_bindings = true`, noncommuting equality `unsat`, commuting equality `sat`.
- This is not just a precomputed scalar/boolean proof, but it is a reduced 2x2 system-channel proof, not the required actual 4x4 joint system-memory object.

## Specific extra checks

Sign control semantics: FAIL.

- `sign_control_type1_trace_norm` is `trace_norm(type1_l - type1_on_hr)` where `type1_l = D_loop(I_loop(rho_l), +1)` and `type1_on_hr = D_loop(I_loop(rho_l), -1)` in `dual_stack_carnot_szilard_hopf_weyl_probe_pytorch.py:428-434`.
- This is a sign-flip/erasure-difference between `H_L` and `H_R`, not the required `H_L=H_R` chirality erasure control.
- Recomputed/result: `gamma5_odd_L = 0.7478644707138538`, `gamma5_odd_HR_control = -0.7478644707138538`, `sign_control_type1_trace_norm = 1.4957289414277075`.
- The chirality readout flips sign. It does not die.

Second-law tolerance: PASS.

- JAX min gap `-2.014013955609073e-15`, PyTorch `-1.3149203947904198e-15`, Julia `-5.741934705483231e-16`.
- `all_pass` threshold is `min_second_law_gap >= -1e-9` in `dual_stack_carnot_szilard_hopf_weyl_probe_pytorch.py:478-483` and JAX lines `617-623`.
- Treat as numerical zero, not a thermodynamic violation.

Pin identity across legs: PASS.

- Envelope: `schema_version=three_engine_sim_result_v1`, `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, `engine_contract.mode=all_three_full_sims`, `all_pass=true`.
- Julia/JAX/PyTorch all report `all_pass=true`, `reads_peer_result=false`, and distinct source files.
- Envelope scalar `max_divergence = 1.4398204850607499e-15`; `out_of_tolerance_shared_scalars = {}`.

## Rubric points 1-7

1. Same finite carrier runs: PASS.
2. Both loops run: PASS for source-defined `D_loop` and Szilard `I_loop`; FAIL if section-15 literal inductive `E o U o E o U` with insertion is required.
3. Both legality grammars represented: FAIL as positive witness. Carnot bookkeeping exists; Szilard measurement legality uses the wrong measurement channel/object.
4. Measurable N01 order gap between D o I and I o D: PASS for reduced source loops, with caveat above.
5. Controls kill the gap where expected: FAIL. Commuting control kills D/I gap, but chirality erasure is not `H_L=H_R` and does not kill the readout.
6. Several rich tools compute real intermediate objects: PASS with caveat. Julia/JAX/PyTorch and SMT run real reduced objects; SMT is not bound to the required 4x4 joint object.
7. Julia/JAX/PyTorch independently reproduce core scalars or explain divergence: PASS.

Overall rubric: not a genuine positive dual-stack QIT witness. It is a real reduced numeric diagnostic with a decorative promotion path around the key Szilard/QIT semantics.

## Hardening list

1. Replace `M_kraus` with a coherent joint measurement/isometry representation that preserves the pinned `|00><11|` coherence when that is the target, or explicitly label the current destructive/dephased measurement as a classical control lane.
2. Add a true `4x4 -> 4x4` joint `M` channel with 16x16 Choi/Kraus evidence, or write an explicit, audited reason why a `2 -> 4` Stinespring-style map is the admitted object.
3. Rename/report MI fields by object: `classical_measured_MI`, `quantum_coherent_fixture_MI`, and `I_c`, and gate against `0.832991061399...` for the coherent pinned fixture.
4. Stop deriving `work_extracted` as a fixed fraction of MI. Compute it from an energy/free-energy/feedback state change, or label it a placeholder and fail the positive ledger.
5. Implement the literal section-15 inductive loop if required: `E o U o E o U` with Szilard insertion, not only `M/F/R`.
6. Replace sign-control semantics with the required `H_L=H_R` chirality-erasure control and require the chirality readout to vanish/die, not merely flip.
7. Add after-M, before-R/after-F, and after-R joint states and recomputed Axis0 cut values under explicit stage labels.
8. Bind SMT to the actual admitted object: either 4x4 joint channel/state entries or a documented reduced-object proof with claim text downgraded accordingly.
9. Keep the current ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
