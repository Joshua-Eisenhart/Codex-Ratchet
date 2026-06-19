VERDICT: GENUINE-WITH-CAVEATS

Scope: read-only audit of `system_v6/sims/flux_emergence_discriminator/`.
Repository writes: none.
Only audit output written: `/tmp/found/flux_audit_verdict.md`.

Bottom line:

The core flux-emergence discriminator is a genuine transport/curvature diagnostic, not a closed-form-only decoration. Holonomy is computed by stepwise horizontal transport along `gamma_b`, inter-shell flux is checked by an independent curvature quadrature route, SMT additivity is derived inside solvers from bound values, and the saved all-three envelope passes the repo validator including `--require-pytorch`.

The main caveat is ablation strength: the bare-spinor ablation is a hand-authored flat result dictionary, not an actual `A=0` carrier run through the same transport/flux pipeline. Also, the load-bearing tool claims do not include function-level `tool_calls` receipts, so the capability evidence is acceptable for this bounded scratch diagnostic but should be hardened before stronger use.

Checks:

1. Holonomy by transport: PASS.
   - Source loop reads sampled connection coefficients each step and accumulates `phi += -(A_chi / A_phi) * dchi` while advancing `chi`.
   - Closed form `-2*pi*cos(2*eta)` is used afterward as `closed_form_target` and error comparison, not as the holonomy source.
   - Evidence locations:
     - Julia: `connection_coefficients` and `horizontal_transport`, lines 82-124.
     - PyTorch: `connection_coefficients` and `horizontal_transport`, lines 121-161.
     - JAX mirrors the same structure.

2. Independent pure-Python recomputation: PASS.
   - I recomputed shell 0 holonomy with separate Python complex arithmetic and finite-difference connection coefficients, without importing the sim modules.
   - Independent `h0`: `-4.442882938252719`.
   - Saved Julia `h0`: `-4.44288293825857`.
   - Absolute difference: `5.851319428984425e-12`.
   - I recomputed pair `(0,1)` transport flux and curvature-quadrature flux.
   - Independent transport `Phi01`: `3.459976205905704`.
   - Saved Julia `Phi01`: `3.459976205908977`.
   - Absolute difference: `3.2729374765949615e-12`.
   - Independent quadrature `Phi01`: `3.45997620672917`.
   - Saved quadrature `Phi01`: `3.4599762067291784`.
   - Absolute difference: `8.43769498715119e-15`.

3. Stokes two-route independence: PASS.
   - Transport route: `pair_flux` uses `hj - hi` from prior horizontal-transport loop outputs.
   - Curvature route: `stokes_oriented_flux` integrates `F_eta_chi = -2*sin(2*eta)` over the eta/chi grid and reverses orientation for boundary comparison.
   - These are two independent computations in code. The closed-form pair target is a third comparison field and is not used to generate either the transport difference or quadrature.

4. Chern total quadrature: PASS.
   - Quadrature spans `eta` from `0` to `pi/2` with midpoint cells: `(r + 0.5) * deta`, `deta = (pi/2)/8192`.
   - There is no endpoint substitution or endpoint fudge; endpoints are excluded by an honest midpoint rule covering the full interval.
   - Error is order-consistent for midpoint quadrature:
     - `N=1024`: `4.928316286623158e-06`
     - `N=2048`: `1.2320788407294003e-06`
     - `N=4096`: `3.0801969153060327e-07`
     - `N=8192`: `7.700494819573578e-08`
     - `N=16384`: `1.9251260141572857e-08`
   - The reported `~7.7e-8` error is consistent with the expected quartering when `N` doubles.

5. Ablations: PARTIAL.
   - Bare spinor: CAVEAT. The output says `trivial A=0`, zero holonomy, and zero flux, but source constructs a literal dictionary with `pass: True`. It does not run an actual flat carrier through the same transport and flux code path.
   - Single shell: PASS. It uses a real transported shell holonomy (`h != 0`) while reporting `flux_defined: false` and `Phi_reported: 0.0`, preserving the distinction between shell holonomy and inter-shell flux.
   - Scramble: PASS. It recomputes adjacent pair fluxes on reversed order, changes the pairwise signs/pattern, and leaves total Chern invariant.

6. Cocycle SMT: PASS, bounded.
   - Z3, cvc5, and Julia Z3 bind measured/scaled connection values as solver variables.
   - They define `Phi(0,1)=c0-c1`, `Phi(1,2)=c1-c2`, `Phi(0,2)=c0-c2`, assert the negation of additivity, and return `unsat`.
   - This proves the integer-scaled algebraic additivity over the bound values. It does not prove a stronger continuous theorem, and the artifact does not claim one.

7. Signed-cut co-variation: PASS.
   - Report label is `CANDIDATE_J_AB_co_variation`.
   - Admission is explicitly `no_admission_candidate_only`.
   - Envelope keeps promotion/formal admission false.

8. Pin/envelope/ceiling/capability: PASS-WITH-CAVEATS.
   - `scripts/validate_three_engine_sim_result.py system_v6/sims/flux_emergence_discriminator/results/flux_emergence_discriminator_envelope_results.json` returned `{"ok": true}`.
   - `scripts/validate_three_engine_sim_result.py --require-pytorch ...` also returned `{"ok": true}`.
   - All engines report `classification: scratch_diagnostic`, `promotion_allowed: false`, `formal_admission_allowed: false`, `reads_peer_result: false`.
   - Envelope claim ceiling says this tests only the curvature member's emergence conditions and does not select a family winner or close an axis/bridge.
   - Caveat: exact wording is "curvature member's emergence conditions", not the literal token `curvature-member-only`.
   - Caveat: load-bearing tool claims are present, but function-level `tool_calls` receipts are absent.

Hardening list:

1. Replace the bare-spinor ablation dictionary with an actual flat-carrier pipeline path that calls the same transport/flux interfaces with `A=0` and records the resulting coefficients, holonomy, and flux outputs.
2. Add function-level `tool_calls` receipts for each load-bearing tool claim: Z3, cvc5, Julia Z3, and `torch.func.jacrev`.
3. Add an explicit `curvature_member_only: true` or exact ceiling phrase if future admission gates key on that wording.
4. Add a small independent recomputation receipt in the result envelope for one shell and one pair, or keep it as an external audit receipt, so future reviewers do not have to infer transport-vs-closed-form separation from source.
5. Keep the current ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, curvature-member-only candidate evidence, no family selection.
