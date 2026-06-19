# Source-Locked Operator Base Packet Audit Verdict

VERDICT: GENUINE-WITH-CAVEATS

The packet is substantively genuine: the four operator forms match the locked reference, the requested commutator cells independently recompute to the reported values, the zero cells have structural explanations, SMT is deriving equality/inequality inside solvers from bound matrix entries, the wrong-basis negative control exists and differs, and the envelope holds the `scratch_diagnostic` ceiling with like-for-like engine comparison.

The caveats are hardening-level, not breakage-level: the unitary generator representation reuses the same `unitary_x` / `unitary_z` constructors as the Kraus/source path, so it is a real separate code path but not a fully independent generator-exponential implementation; and the SMT proofs bind hardcoded scaled channel matrices rather than deriving those matrices from the source functions at runtime.

## 1. Source-Lock Fidelity

Reference exact lock says the only intrinsic families are `O_1..O_4` with side labels `Ti`, `Te`, `Fi`, `Fe` at `system_v5/READ ONLY Reference Docs/operator math explicit.md:794-810`.

`Ti` matches:
- Reference: exact channel `(1-q_1)rho + q_1(P_0 rho P_0 + P_1 rho P_1)` at `operator math explicit.md:102-109`; Kraus form at `operator math explicit.md:190-215`; generator at `operator math explicit.md:227-230`.
- JAX: projectors and Kraus at `source_locked_operator_base_packet_jax.py:47-50` and `:177-180`; Bloch/generator at `:212-229`; result form at `source_locked_operator_base_packet_jax_results.json:242-245`.
- Julia: projectors and Kraus at `source_locked_operator_base_packet_julia.jl:33-36` and `:100-103`; Bloch/generator at `:129-148`; result form at `source_locked_operator_base_packet_julia_results.json:230-233`.
- PyTorch: projectors and Kraus at `source_locked_operator_base_packet_pytorch.py:42-45` and `:181-184`; Bloch/generator at `:216-233`; result form at `source_locked_operator_base_packet_pytorch_results.json:224-227`.

`Te` matches:
- Reference: exact channel `(1-q_2)rho + q_2(Q_+ rho Q_+ + Q_- rho Q_-)` at `operator math explicit.md:279-286`; expanded output at `:386-391`; Kraus at `:394-425`; generator at `:435-438`.
- JAX: `QP/QM` and Kraus at `source_locked_operator_base_packet_jax.py:49-50` and `:180-182`; Bloch/generator at `:216-233`; result form at `source_locked_operator_base_packet_jax_results.json:237-240`.
- Julia: `QP/QM` and Kraus at `source_locked_operator_base_packet_julia.jl:35-36` and `:103-105`; Bloch/generator at `:133-151`; result form at `source_locked_operator_base_packet_julia_results.json:225-228`.
- PyTorch: `QP/QM` and Kraus at `source_locked_operator_base_packet_pytorch.py:44-45` and `:184-186`; Bloch/generator at `:220-237`; result form at `source_locked_operator_base_packet_pytorch_results.json:219-222`.

`Fi` matches:
- Reference: exact channel `U_x(theta) rho U_x(theta)^dagger` at `operator math explicit.md:488-505`; expanded output at `:568-581`; generator at `:584-587`.
- JAX: `unitary_x` and Kraus at `source_locked_operator_base_packet_jax.py:167-170` and `:182-184`; Bloch/generator at `:218-235`; result form at `source_locked_operator_base_packet_jax_results.json:232-235`.
- Julia: `unitary_x` and Kraus at `source_locked_operator_base_packet_julia.jl:92-96` and `:105-107`; Bloch/generator at `:135-154`; result form at `source_locked_operator_base_packet_julia_results.json:220-223`.
- PyTorch: `unitary_x` and Kraus at `source_locked_operator_base_packet_pytorch.py:171-175` and `:186-188`; Bloch/generator at `:222-240`; result form at `source_locked_operator_base_packet_pytorch_results.json:214-217`.

`Fe` matches:
- Reference: exact channel `U_z(phi) rho U_z(phi)^dagger` at `operator math explicit.md:646-663`; expanded output at `:717-729`; generator at `:732-735`.
- JAX: `unitary_z` and Kraus at `source_locked_operator_base_packet_jax.py:173-175` and `:184-186`; Bloch/generator at `:220-237`; result form at `source_locked_operator_base_packet_jax_results.json:227-230`.
- Julia: `unitary_z` and Kraus at `source_locked_operator_base_packet_julia.jl:98-108`; Bloch/generator at `:137-157`; result form at `source_locked_operator_base_packet_julia_results.json:215-218`.
- PyTorch: `unitary_z` and Kraus at `source_locked_operator_base_packet_pytorch.py:177-189`; Bloch/generator at `:224-243`; result form at `source_locked_operator_base_packet_pytorch_results.json:209-212`.

## 2. Independent Hand Recompute

Pinned state used: `rho_0 = |psi(0.3,0.2,pi/8)><...|`, `q=0.3`, `theta=phi=pi/2`.

Independent high-precision recompute, using only the reference formulas:
- `||[Ti,Fi](rho_0)||_1 = 0.22764906992932955540799884153758366633814450426978`
- Reported Julia/envelope value: `0.22764906992932943` at `source_locked_operator_base_packet_julia_results.json:67-69` and `source_locked_operator_base_packet_envelope_results.json:65-68`.
- `||[Fi,Fe](rho_0)||_1 = 1.7000943200728587729004629224801562192712601313207`
- Reported Julia/envelope value: `1.7000943200728584` at `source_locked_operator_base_packet_julia_results.json:48-55` and `source_locked_operator_base_packet_envelope_results.json:47-55`.

The independent recompute agrees to more than 10 digits.

## 3. Structural Zero Cells

The three zero cells are structural, not numeric accidents:
- `Ti-Te`: In Bloch coordinates, `Ti = diag(1-q,1-q,1)` and `Te = diag(1,1-q,1-q)` on `(r_x,r_y,r_z)`, so their channel matrices are diagonal and commute.
- `Ti-Fe`: `Ti` is z-axis dephasing, damping the x-y plane by the scalar `1-q`; `Fe` is z-axis rotation in that same x-y plane. Scalar damping commutes with rotation.
- `Te-Fi`: `Te` is x-axis dephasing, damping the y-z plane by the scalar `1-q`; `Fi` is x-axis rotation in that same y-z plane. Scalar damping commutes with rotation.

The packet reports those cells at roundoff scale: Julia `Ti-Te = 2.288783399261118e-16`, `Ti-Fe = 1.5944364291470363e-16`, `Te-Fi = 1.6883057536160649e-16` at `source_locked_operator_base_packet_julia_results.json:39-44`; envelope carries the same at `source_locked_operator_base_packet_envelope_results.json:41-45`.

## 4. Representation Consistency

This is a real check. Each engine computes `source_channel` via Kraus application, `bloch_channel` via Bloch-coordinate formulas, and `generator_channel` via generator/flow formulas, then compares all three paths:
- JAX definitions and comparisons: `source_locked_operator_base_packet_jax.py:177-197`, `:212-238`, `:283-298`; result max residuals are around `5.55e-17` to `1.12e-16` at `source_locked_operator_base_packet_jax_results.json:391-463`.
- Julia definitions and comparisons: `source_locked_operator_base_packet_julia.jl:100-121`, `:129-160`, `:198-215`; result max residuals are around `5.55e-17` to `1.11e-16` at `source_locked_operator_base_packet_julia_results.json:378-450`.
- PyTorch definitions and comparisons: `source_locked_operator_base_packet_pytorch.py:181-201`, `:216-244`, `:289-304`; result max residuals are around `5.55e-17` to `1.11e-16` at `source_locked_operator_base_packet_pytorch_results.json:371-443`.

Caveat: for `Fi` and `Fe`, the generator path uses the same `unitary_x` / `unitary_z` helper as the source/Kraus path. It is still a separate comparison path, but hardening should add an independent generator-exponential or fully expanded matrix implementation for those two unitary flows.

## 5. SMT Derive-In-Solver

SMT is not just a precomputed boolean. The JAX leg creates solver variables for 4x4 channel matrices, binds 32 entries, computes `A*B` and `B*A` inside z3/cvc5, and asserts equality entrywise at `source_locked_operator_base_packet_jax.py:421-448` and `:451-494`. The Julia leg does the same with Z3.jl at `source_locked_operator_base_packet_julia.jl:342-381`.

Result receipts record `bound_entries: 32`, `derived_products: A*B and B*A entries are computed in solver`, and `asserted_precomputed_scalar: false` at `source_locked_operator_base_packet_jax_results.json:500-567` and `source_locked_operator_base_packet_julia_results.json:486-514`.

Caveat: the matrices bound into SMT are hardcoded scaled channel matrices at `source_locked_operator_base_packet_jax.py:497-504` and `source_locked_operator_base_packet_julia.jl:384-389`. Hardening should derive these scaled matrices from the same operator definitions before binding them to the solver.

## 6. Wrong-Basis Negative Control

The wrong-basis negative control exists and differs. It replaces z-basis `Ti` with y-basis dephasing:
- Code: `wrong_basis_ti_y` at `source_locked_operator_base_packet_jax.py:379-381`, `source_locked_operator_base_packet_julia.jl:298-300`, and `source_locked_operator_base_packet_pytorch.py:387-389`.
- Results: `rho_0` difference is `0.2276490699293295...` across engines at `source_locked_operator_base_packet_jax_results.json:151-157`, `source_locked_operator_base_packet_julia_results.json:139-145`, and `source_locked_operator_base_packet_pytorch_results.json:133-139`.

The swapped-parameter control is honestly marked degenerate at the requested pin because `q1=q2` and `theta=phi`, with an off-pin falsifier difference `0.315539353613981...` at `source_locked_operator_base_packet_jax_results.json:136-150`, `source_locked_operator_base_packet_julia_results.json:124-138`, and `source_locked_operator_base_packet_pytorch_results.json:118-132`.

## 7. Pin, Envelope, Depth Labels

The pin identity is equal across all engines and the envelope records `pin_identity_equal: true` and `pin_spec_equal: true` at `source_locked_operator_base_packet_envelope_results.json:73-84` and `:870`.

The like-for-like envelope is real: common scalar count is 25, max divergence is `4.440892098500626e-16`, and the divergence key is `commutator_Fi_Fe_rho0_trace_norm` at `source_locked_operator_base_packet_envelope_results.json:219-227` and `:381-427`.

Capability-backed depth labels are present:
- JAX: `z3` and `cvc5` are `load_bearing`; `jax` and `jax.numpy` are `supportive` at `source_locked_operator_base_packet_jax_results.json:1-7`; capability receipts are listed at `:593-618`.
- Julia: `Z3` is `load_bearing`; `JSON` and `LinearAlgebra` are `supportive` at `source_locked_operator_base_packet_julia_results.json:1-6`; capability receipt for Z3 is listed at `:540-556`.
- PyTorch: `torch.func` is `load_bearing`; `torch` is `supportive` at `source_locked_operator_base_packet_pytorch_results.json:1-5`; capability receipts are listed at `:492-501`.

The envelope also passes:
- `python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/source_locked_operator_base_packet/results/source_locked_operator_base_packet_envelope_results.json`
- `python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v6/sims/source_locked_operator_base_packet/results/source_locked_operator_base_packet_envelope_results.json`

Both returned `{"ok": true}`.

## Hardening List

1. Add independent generator exponentials for `Fi` and `Fe`, or fully expanded generator-flow matrices, instead of reusing the same unitary constructors as the source/Kraus path.
2. Generate the SMT-bound scaled channel matrices from the source operator definitions at runtime, then bind them into z3/cvc5/Z3.jl, so the SMT lane cannot drift from the operator code.
3. Add a small symbolic structural-zero receipt for `Ti-Te`, `Ti-Fe`, and `Te-Fi`, separate from the numeric commutator table, encoding the diagonal/scalar-damping-plus-rotation arguments directly.

