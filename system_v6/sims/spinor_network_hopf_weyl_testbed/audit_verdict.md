# spinor_network_hopf_weyl_testbed fresh audit verdict

Verdict: GENUINE-WITH-CAVEATS.

Status ceiling: scratch_diagnostic only. The pinned spinor-loop nonclosure headline is real and numerically matches the blind derivation, but several support claims are too weak for promotion: density/classical SO3 defects are assigned as zeros, SO3 equivariance is a self-comparison with no wrong-transform negative control, coherent information is a two-site entangled chord construction rather than a six-node carrier joint state, and the `betti1=4` complex is produced by simplex closure adding extra edges beyond "hexagon + chord + one 3-way relation."

Checks executed

- Read `/tmp/found/sn_preaudit.md`, `/tmp/found/sn_expected_values.md`, and all four target sources plus JSON results under `system_v6/sims/spinor_network_hopf_weyl_testbed/`.
- Ran the generic validator: `python3 scripts/validate_three_engine_sim_result.py system_v6/sims/spinor_network_hopf_weyl_testbed/results/spinor_network_hopf_weyl_testbed_envelope_results.json` -> `ok: true`.
- Ran the stricter local validator path from the checklist with `--require-pytorch --require-source-backed` -> PASS.
- Ran adapted preaudit source/result checks for pin equality, torch_ga absence, kingdon presence, spinor formulas, density/source transport, TN source backing, PyG message, topology shuffle, terrain sign naming, and per-node 720 honesty.

1. Headline spinor defect

Source evidence:

- Pin literal is identical across envelope and legs; envelope checks `pin_sha256_equal` and `pin_spec_literal_equal` at `spinor_network_hopf_weyl_testbed_envelope.py:128-135`, then gates `pin_spec_match` at `spinor_network_hopf_weyl_testbed_envelope.py:136-152`.
- The source pin in each leg sets `eta_i = pi/8 + i*pi/20`, `phi_i = 0.3i`, `chi_i = 0.2i`, graph, q values, terrain schedule, and `H_L=+H_0`, `H_R=-H_0` in `spinor_network_hopf_weyl_testbed_julia.jl:15`, `spinor_network_hopf_weyl_testbed_jax.py:29`, and `spinor_network_hopf_weyl_testbed_pytorch.py:27`.
- The spinor coordinate map implements fiber as `p += u` and base as `p -= cos(2eta)u; c += u` in Julia `spinor_network_hopf_weyl_testbed_julia.jl:105-119`, JAX `spinor_network_hopf_weyl_testbed_jax.py:175-190`, and PyTorch `spinor_network_hopf_weyl_testbed_pytorch.py:171-186`.
- The dual-stack readout computes `phase = wrap_phase(-2pi*cos(2eta(i)))`, then `defect = |exp(i phase)-1|`, and writes both single and dual defects equal to that value: Julia `spinor_network_hopf_weyl_testbed_julia.jl:287-312`, JAX `spinor_network_hopf_weyl_testbed_jax.py:379-408`, PyTorch `spinor_network_hopf_weyl_testbed_pytorch.py:363-391`.
- Envelope exposes the six per-node single-loop values that were absent from a quick headline read: nodes 0..5 at `spinor_network_hopf_weyl_testbed_envelope_results.json:58-160`.

Independent recomputation:

- Blind formula: component shifts are `Delta_1=2pi(1-cos(2eta))`, `Delta_2=-2pi(1+cos(2eta))`, both equivalent to multiplier `exp(-i 2pi cos(2eta))`.
- Per-node defects recomputed: `[1.591386403134962, 1.979143640047024, 0.943815486748603, 0.943815486748603, 1.979143640047024, 1.591386403134962]`.
- Mean recomputed: `1.5047818433101963`, matching JSON `spinor_dual_stack_return_defect_mean` and `spinor_single_loop_return_defect_mean` at JAX results `spinor_network_hopf_weyl_testbed_jax_results.json:524-525`, Julia results `spinor_network_hopf_weyl_testbed_julia_results.json:394-395`, PyTorch results `spinor_network_hopf_weyl_testbed_pytorch_results.json:440-441`.
- Node 0 by hand: `eta=pi/8`, `c=sqrt(2)/2`, multiplier `exp(-i 2pi c)=(-0.26625534204141565 + 0.9639025328498773i)`, defect `|m-1|=1.5913864031349618`; density is invariant because `m*conj(m)=1` up to `2.3e-17`.

Finding:

- The nonclosure at pinned etas is geometry-derived, not a bug.
- The dual-stack composition is effectively base then fiber because the code uses the base-loop multiplier and the blind derivation says the fiber contributes final multiplier `1`. The source does not explicitly execute a two-step base-then-fiber transport; it collapses the composition to the closed-form base result. This is acceptable for the scalar readout, but should be made explicit in a hardening pass.
- The result is not a clean `-1/+1` 720 pattern: every node's clean-pattern test is false. The artifact honestly reports raw phases/defects but lacks explicit fields like `clean_minus_plus_pattern=false` and `honest_geometry_divergence=true`.

2. `betti1=4`

Source evidence:

- JAX/PyTorch insert graph edges for C6 plus chord `(0,3)`, then insert simplex `[0,2,4]`: JAX `spinor_network_hopf_weyl_testbed_jax.py:450-464`, PyTorch `spinor_network_hopf_weyl_testbed_pytorch.py:420-432`.
- GUDHI reports `betti_numbers: [1,4]` in JAX results `spinor_network_hopf_weyl_testbed_jax_results.json:374-378` and PyTorch results `spinor_network_hopf_weyl_testbed_pytorch_results.json:362-366`.
- Julia hardcodes the topology result rather than computing it: `topology_betti1 => 4.0` at `spinor_network_hopf_weyl_testbed_julia.jl:351-368`.
- Envelope compares all three as equal at `spinor_network_hopf_weyl_testbed_envelope_results.json:612-619`.

Independent derivation:

- Bare graph C6 plus chord: `V=6`, `E=7`, connected, so `beta1=E-V+1=2`.
- Adding a 2-simplex `[0,2,4]` in a simplicial complex forces its missing boundary edges `(0,2)`, `(2,4)`, `(0,4)` into the complex. Then `V=6`, `E=10`, `F=1`, connected, no 2-cycle, so `beta1=10-6+1-1=4`.

Finding:

- `betti1=4` is honest for the actual GUDHI/TopoNetX simplicial complex that was built.
- It is constructed wrong if the intended object is "hexagon + chord graph plus one 3-way XGI relation" without extra pairwise closure edges. The report needs to name the closure-induced edges, otherwise the topology claim is misleading.

3. `so3_equivariance_residual = 0.0`

Source evidence:

- JAX computes `lhs = (rot @ vectors.T).T` and `rhs = einsum("ij,nj->ni", rot, vectors)`, which are algebraically the same operation: `spinor_network_hopf_weyl_testbed_jax.py:486-492`.
- PyTorch computes `lhs = vectors @ rot.T` and `rhs = einsum("ij,nj->ni", rot, vectors)`, again the same operation: `spinor_network_hopf_weyl_testbed_pytorch.py:450-456`.
- Julia does not use an SO3 package; it writes `shared["so3_equivariance_residual"] = 0.0` and readout `"closed-form SO(3) vector transport check"` at `spinor_network_hopf_weyl_testbed_julia.jl:448-499`.
- Results show exact zero in all legs: JAX `spinor_network_hopf_weyl_testbed_jax_results.json:366-368`, PyTorch `spinor_network_hopf_weyl_testbed_pytorch_results.json:354-356`, Julia `spinor_network_hopf_weyl_testbed_julia_results.json:307-309`.

Finding:

- This is zero by construction/self-comparison, not a meaningful floating equivariance residual.
- No wrong-transform negative control exists in the JSON. This should be hardened with a deliberately permuted/axis-swapped transform that fails above tolerance.

4. `coherent_information_chord_0_3 = +0.9299770054431931`

Source evidence:

- Julia constructs a two-index ITensor with only `|00>` and `|11>` amplitudes from `theta = 0.5*(eta(0)+eta(3))` and `phase = chi(0)-chi(3)`: `spinor_network_hopf_weyl_testbed_julia.jl:337-348`.
- JAX constructs a two-qubit ket `[cos(theta), 0, 0, exp(i phase) sin(theta)]` and computes `S(B)-S(AB)` with quimb: `spinor_network_hopf_weyl_testbed_jax.py:432-447`.
- PyTorch does not build the state; it returns the same entropy formula: `spinor_network_hopf_weyl_testbed_pytorch.py:413-417`.
- Results record the value and formula match: Julia results `spinor_network_hopf_weyl_testbed_julia_results.json:125-132`, JAX results `spinor_network_hopf_weyl_testbed_jax_results.json:184-191`, PyTorch results `spinor_network_hopf_weyl_testbed_pytorch_results.json:157-163`.

Independent recomputation:

- `theta=(eta_0+eta_3)/2=0.6283185307179586`.
- `p=sin(theta)^2=0.3454915028125263`.
- `H2(p)=0.9299770054431931`, so the reported `+0.9299770054431931` is plausible for that two-qubit pure entangled chord state.

Finding:

- The number is mathematically plausible for the state the code constructs.
- It is not yet backed as a six-node network coherent information readout. The state is a synthetic two-site chord entangled ansatz derived from node `eta/chi`, not a joint six-node state generated from all carrier variables, edge couplings, and schedule evolution. This is the scaffold 10.5 risk: carrier-tied, but not network-carrier-complete.

5. PyG message and kingdon

Source evidence:

- PyTorch imports `kingdon.Algebra` and `MessagePassing`: `spinor_network_hopf_weyl_testbed_pytorch.py:16-23`.
- The PyG message is `torch.einsum("eab,eb->ea", edge_attr, x_j)`, so edge matrices left-multiply source node features: `spinor_network_hopf_weyl_testbed_pytorch.py:459-468`.
- Quaternion left-multiplication matrices are defined at `spinor_network_hopf_weyl_testbed_pytorch.py:470-483`; graph edge attributes use those matrices at `spinor_network_hopf_weyl_testbed_pytorch.py:491-504`.
- The negative/positive quaternion gap is computed as `||i(jx)-j(ix)||` versus `||i(ix)-i(ix)||`: `spinor_network_hopf_weyl_testbed_pytorch.py:505-511`.
- kingdon checks `e1*e2 + e2*e1` and records anticommutator norm: `spinor_network_hopf_weyl_testbed_pytorch.py:514-525`.
- Results show `noncommutative_message_gap=2.0`, `commuting_edge_control_gap=0.0`, and kingdon anticommutator norm `0.0`: `spinor_network_hopf_weyl_testbed_pytorch_results.json:277-320`.
- `torch_ga` is absent and the envelope/leg lists `kingdon`, not `torch_ga`: PyTorch result package/tool lines `spinor_network_hopf_weyl_testbed_pytorch_results.json:108-120` and envelope tool map `spinor_network_hopf_weyl_testbed_envelope_results.json:1238-1251`.

Finding:

- PyG is not a stub. It carries quaternion edge products order-sensitively through matrix edge attributes.
- Caveat: the order-sensitive negative control is computed adjacent to the message pass rather than as a second PyG propagation with swapped edge order. Good enough for scratch diagnostic; not enough for a load-bearing graph-message claim.
- kingdon is on the claim path; `torch_ga` is not.

6. Pin hash, like-for-like envelope, load-bearing receipts

Source/result evidence:

- Envelope pin equality is checked from all three leg hashes at `spinor_network_hopf_weyl_testbed_envelope.py:128-135` and gated by `pin_spec_match` at `spinor_network_hopf_weyl_testbed_envelope.py:136-152`.
- Envelope requires same named observable sets and shared scalar tolerance at `spinor_network_hopf_weyl_testbed_envelope.py:80-103` and records the pass at results `spinor_network_hopf_weyl_testbed_envelope_results.json:194-204`.
- `reads_peer_result` is set false in the engine records from source `spinor_network_hopf_weyl_testbed_envelope.py:62-77` and engine contract `spinor_network_hopf_weyl_testbed_envelope.py:154-161`.
- Capability receipt paths are present for all claimed tool rows in the envelope tool map at `spinor_network_hopf_weyl_testbed_envelope_results.json:1152-1254`.

Finding:

- Like-for-like envelope and pin identity pass.
- Load-bearing labels are backed by capability receipt paths, but some labels overclaim because the local tool call does not gate a strong enough control: SO3 is self-comparison, topology label-shuffle changes weights but does not recompute a failing topology, coherent info is a two-site ansatz, and Julia topology is hardcoded.

Hardening list

1. Add explicit `clean_minus_plus_pattern=false`, `honest_geometry_divergence=true`, and `headline_claim="pattern_not_clean_from_pinned_geometry"` to the envelope when pinned phases are not clean `-1/+1`.
2. Replace hardcoded density and classical SO3 defect zeros with computed per-node/per-step arrays; keep the current zeros only if they arise from the same transport pipeline.
3. Add a wrong-transform SO3 negative control that fails above tolerance; do not count self-comparison residuals as load-bearing.
4. For topology, either relabel the object as a simplicial closure complex with added boundary edges `(0,2),(2,4),(0,4)`, or compute the intended hypergraph homology without simplex-closure edge injection.
5. Replace Julia hardcoded topology with an actual Julia-side topology computation or mark Julia topology as a mirrored scalar, not an independent leg result.
6. Rebuild coherent information from a real six-node carrier state with edge/chord coupling and schedule-derived state, or demote the current value to "two-site chord ansatz entropy."
7. Run PyG negative control as an alternate propagation with reversed/swapped edge order, not only an adjacent quaternion algebra calculation.
8. Make terrain law result fields explicit (`Ni_Pit`/`Ni_Source`, `sigma_minus`/`sigma_plus`) or rename the implementation to the actual L/R `SM`/`SP` convention.
9. Add a source-backed check that the dual-stack closed form is base-then-fiber, not just a collapsed phase formula, or document the algebraic collapse.

Rubric

- Same carrier ran: PARTIAL PASS. Same pin and same scalar observable set across legs; coherent information and topology are not fully same-carrier network computations.
- Loops ran: PASS for spinor loop formulas and terrain density schedule; CAVEAT that dual-stack is closed-form collapsed.
- Readouts real: PARTIAL PASS. Spinor defects, order gaps, schedule density deltas, PyG/kingdon, and GUDHI/PyTorch/JAX topology are real; density/classical defects and Julia topology are assigned/hardcoded.
- Controls flip: PARTIAL FAIL. Solver noncommutation controls and PyG algebra controls exist; SO3, density/classical, topology label-shuffle, and coherent-info controls are not falsifier-grade.
- Tools computed real objects: PARTIAL PASS. Tools import and compute objects, but several `load_bearing` labels exceed the actual gate strength.
- Three engines agree: PASS numerically, with independence caveat. Agreement is exact/near-exact by shared formulas and scalar comparison; Julia topology and SO3 are not independent computations.

Bottom line

The core spinor nonclosure headline is genuine at the pinned etas and matches the blind formulas exactly. The packet should not be promoted beyond `scratch_diagnostic` until the hardening list is addressed, because several surrounding claims are decorative or under-falsified even though the envelope validator passes.
