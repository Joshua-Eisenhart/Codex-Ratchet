# JAX Geometry Reality Audit - 2026-05-30

## Claim Correction

The phrase "8-128 depth" was wrong.

The JAX geometry wave tested a scale ladder:

```text
n = 8, 16, 32, 64, 128 finite carrier sites / samples / graph nodes
```

That is scale, not depth.

It does not mean:

- 8-128 qubits.
- 8-128 PEPS/PEPS3D tensor-network sites with contraction.
- bond dimension depth.
- layer depth.
- proof depth.
- dynamics depth.
- full spinor-network depth.

The correct status is:

```text
24 standalone geometry/math targets ran as finite JAX-native execution scouts.
Their per-target invariant checks are real and useful coverage.
They are not deep proper sims.
```

## Claude Audit Reconciliation

Accepted correction:

- The 24-target JAX wave is not fake label churn. It contains distinct,
  geometry-specific invariant functions and finite maps.
- The target-specific invariant checks are real evidence at the finite-scout
  level.
- The same wave is still shallow relative to the intended deep-sim standard,
  because the carrier, dynamics, controls, proof/topology integration, and
  parity surface are mostly shared/generic.

Examples of real target-specific invariant work:

| Target family | Real invariant/function present |
|---|---|
| Clifford / Cl3 / Cl6 | Gamma anticommutation residual. |
| G2 | Standard real G2 3-form / cross-product norm identity residual. |
| Spin7 | Cayley 4-form table / antisymmetry and norm readout. |
| Finite cell complex | Boundary-of-boundary zero check. |
| Symplectic | Canonical symplectic J antisymmetry / nondegeneracy. |
| CP1 / Fubini-Study | Phase-invariant projective spinor distance. |
| Twistor incidence | `omega = i X pi` incidence row. |
| SU2 / Spin3 | `q` and `-q` double-cover check against SO3. |

Rejected overclaim:

- These invariant checks do not make the 24-target wave deep.
- They do not establish a real spinor-network, MPS, PEPS2D, or PEPS3D
  contraction per geometry.
- They do not provide geometry-specific dynamics for each target.
- They do not make z3/cvc5/SymPy/GUDHI/TopoNetX/rustworkx load-bearing for
  each target.
- They do not provide torch/JAX parity for the 24 geometry targets.
- The `8, 16, 32, 64, 128` ladder is finite site/sample/node scale, not
  Hilbert-dimension depth, qubit count, bond depth, or network depth.

## What The JAX Wave Actually Did

Shared execution pattern:

- Built finite spinor/geometry samples.
- Built finite directed graph edges over those samples.
- Computed one target-specific finite invariant or residual.
- Ran a generic JAX compatibility-weight pipeline:
  - Flax edge scorer.
  - Equinox phase twist.
  - Optax optimization.
  - Diffrax finite weight dynamics.
  - Jraph graph aggregation.
  - Lineax finite potential solve.
  - OTT transport between pre/post weights.
  - JAXLie SO3 frame checks.
  - Qutip-JAX density trace check.
  - BlackJAX/NumPyro sampler readout.
  - NetKet Hilbert boundary check.
  - Orbax checkpoint roundtrip.
- Ran scramble controls and order-gap checks.
- Wrote formal-scout style receipts with promotion locked.

This is not enough for the user's intended "deep sim" standard.

Concrete reading:

```text
The invariant layer is real.
The deep carrier/dynamics/tool/parity layer is not yet built for these 24.
```

## What A Proper Deep Sim Still Requires

A proper deep sim should be judged on multiple independent axes, not on one
scale number:

1. Mathematical object depth:
   - The actual geometry object must be represented, not just a residual or
     label-adjacent formula.
2. Carrier depth:
   - Real spinor network carrier.
   - MPS / PEPS2D / PEPS3D or suitable equivalent where relevant.
   - No dense closure as the claim path.
3. Dynamic depth:
   - Geometry-specific dynamics, not one shared generic compatibility dynamic.
4. Entanglement/QIT depth:
   - Entanglement information carried by the spinor network.
   - Multiple entropy readouts where meaningful, not scalar entropy as object.
5. Tool depth:
   - JAX where requested.
   - PyTorch parity where useful.
   - Quimb/cotengra/autoray or equivalent network contraction where relevant.
   - SymPy/z3/cvc5 proof checks where relevant.
   - Topology tools where relevant: GUDHI, TopoNetX, rustworkx, XGI.
   - Equivariance/group tools where relevant: e3nn_jax/e3nn, JAXLie.
6. Controls:
   - Label erase.
   - Invariant erase.
   - Orientation erase where relevant.
   - Fiber/base scramble where relevant.
   - Product/no-entanglement carrier where relevant.
   - Dense-closure control where relevant.
7. Resource frontier:
   - Scale ladder is only one axis.
   - Bond dimension, contraction complexity, site geometry, shell count,
     dynamics steps, and parity all need separate stress.
8. Composition boundary:
   - No order-composition claims until individual sims are actually strong.

## Per-Target Reality List

| Target | What actually ran | What is still missing for a proper deep sim |
|---|---|---|
| `s3_spinor_carrier` | Normalized finite C2 spinor samples; S3 norm residual; graph/dynamics wrapper. | Real spinor-network carrier; MPS/PEPS2D/PEPS3D contraction; entanglement carried across network; parity; proof/control battery. |
| `s2_hopf_base_surface` | Hopf map from finite S3 spinor samples to finite S2 base vectors; base norm residual. | Full Hopf fiber/base network; fiber-preserving dynamics; topology/degree checks; network entanglement across base/fiber cuts. |
| `hopf_fibration_s3_to_s2` | U1 phase orbit on finite spinors; checked base drift under phase action. | Bundle-level connection/holonomy; fiber transport; Chern/winding checks; PEPS/PEPS3D carrier with fiber/base cuts. |
| `nested_hopf_tori` | Finite amplitude leaves and torus-like leaf signal over samples. | Actual nested torus family with shell/leaf indexing; spinor network on leaves; leaf-to-leaf transport; embedding into candidate layer order. |
| `clifford_torus_t2_in_s3` | Equal-amplitude finite S3 spinors; T2 residual. | Full Clifford torus parameter sweep; geodesic/curvature checks; PEPS carrier on torus graph; relation to Hopf fibers and spinor sheets. |
| `twistor_incidence_spinor_geometry` | Finite spinor pi and Hermitian event matrix X; incidence row `omega = i X pi`. | Actual twistor incidence geometry across events; null/geometric constraints; spinor-network propagation; symbolic/proof checks. |
| `u1_hopf_principal_bundle` | U1 phase action; base-invariance residual. | Principal bundle transition functions; connection one-form; holonomy; bundle-compatible network carrier. |
| `su2_spin3_unit_quaternion_double_cover` | Unit quaternion samples; q and -q mapped to same SO3 frame. | Full SU2/Spin3 action on spinor network; quaternion rotor dynamics; Clifford/SymPy proof checks; chirality interaction. |
| `so3_orientation_frame_reduction` | JAXLie SO3 frames; determinant and orthogonality checks. | Frame-bundle reduction over manifold carrier; equivariant dynamics; e3nn_jax/e3nn checks; integration with spinor sheets. |
| `pin3_spin3_chirality_split` | Reflection control and chirality sign flip signal. | Proper Pin/Spin chirality cover; gamma/chirality operators; left/right Weyl network separation; orientation-erasure controls. |
| `clifford_geometries_cl3_cl6` | Finite Pauli/Kronecker gamma matrices; Cl3/Cl6 anticommutation residual. | Clifford module action on the carrier; geometric products along network edges; Clifford/SymPy/z3/cvc5 triangulation; relation to quaternion/Hopf layers. |
| `symplectic_structure` | Canonical finite symplectic matrix J; antisymmetry and nondegeneracy residuals. | Symplectic flow; Hamiltonian dynamics; Darboux/Sp checks; interaction with spinor network and shell cuts. |
| `almost_complex_structure` | Canonical complex structure J; `J^2 = -I` residual. | Almost-complex structure over the actual carrier; integrability/Nijenhuis-style finite test; relation to SU3/Calabi-Yau candidates. |
| `spin_c_structure` | Spinor samples with U1 phase twist; norm preservation. | Spin-c bundle construction; determinant line/U1 coupling; Dirac operator relation; proof/tool checks. |
| `su3_calabi_yau_structure` | Finite diagonal SU3 phase frames; determinant-one residual. | Full SU3 structure; holomorphic volume form; Kahler/symplectic compatibility; Calabi-Yau-specific dynamics/topology. |
| `g2_structure` | Standard finite G2 3-form; cross-product norm identity. | Full positive 3-form dynamics; metric extraction; torsion classes; relation to nested shell/Spin7 alternatives; topology/proof checks. |
| `spin7_structure` | Finite Cayley 4-form table; antisymmetry/norm readout. | Full Spin7 structure; Cayley-form dynamics; relation to G2 reductions; 8D carrier and topology/proof checks. |
| `seiberg_witten_8d` | Finite U1-curvature surrogate plus spinor density residual optimized by Optax. | Actual 8D Seiberg-Witten formulation; Dirac operator; gauge field; PDE/discrete dynamics; proof of what the residual means. |
| `dirac_monopole_u1` | Finite equatorial phase loop; U1 winding/Chern readout. | Proper monopole bundle patches; Berry connection; Chern class over finite surface; network and topology checks. |
| `spectral_triple` | Finite algebra element and Dirac cycle operator; commutator norm. | Spectral triple over actual geometry carrier; Connes distance tests; algebra/Dirac/action coupling; proof and scaling checks. |
| `finite_cell_complex_boundary` | Finite fan triangulation; boundary-of-boundary zero. | Real cell complex for each geometry/layer; homology/persistence with GUDHI/TopoNetX; coupling to carrier states. |
| `contact_sasakian_s3` | Finite S3 spinor loop; contact phase one-form readout. | Contact distribution; Reeb flow; Sasakian metric compatibility; dynamics and network embedding. |
| `cp1_fubini_study` | Finite projective spinor rays; phase-invariant Fubini-Study distance checks. | CP1 geometry with metric/curvature; relation to Hopf base; network cuts and parity/tool checks. |
| `higher_hopf_s7_to_s4` | Normalized C4 spinors; finite S4 base residual. | Actual higher Hopf fibration; quaternionic fiber structure; S7/S4 bundle transport; network carrier and topology checks. |

## Layer Sims Reality List

The JAX L0-L8 layer run is separate from the geometry wave.

It reached:

```text
n = 8, 16, 32, 64 finite carrier sites
```

It did not reach 128.
It did not establish protected layer admission.

| Layer | What actually ran | What is still missing |
|---|---|---|
| L0 response/effect/path quotient | Finite probes/effects/path weights over spinor-shell edges. | Stronger response quotient over a stricter future carrier gate; richer effects; proof checks; PEPS/PEPS3D carrier. |
| L1 boundary/environment | Boundary potential and environment-conditioned weights. | Real boundary contraction; shell boundary bookkeeping; PEPS/PEPS3D environment contraction. |
| L2 Weyl spinor/chirality | Chirality-sensitive edge signal over left/right spinors. | Full left and right Weyl spinor networks; independent L/R attractor basins; MPS/PEPS/PEPS3D carrier; gamma/chirality proof checks. |
| L3 quaternion/Clifford orientation | Quaternion/rotor-style orientation signal. | Real quaternion/Clifford action on the spinor network; nontrivial Clifford module; proof/tool triangulation. |
| L4 terrain/channel generator | Generic terrain-channel mixture signal. | Actual terrain mathematics; each terrain as its own dynamics/attractor basin; left/right Weyl coupling; not just a shared signal. |
| L5 operator/substage cell | Finite operator-cell slot signal. | Actual allowed operator degrees of freedom; each operator row as geometric constraint action; composition controls. |
| L6 entropy/cut communication | Cut-sensitive entropy/correlation weight signal. | Full QIT entropy families over spinor-network cuts; coherent info, negativity, relative entropy, Renyi, shell possibility entropy. |
| L7 Hopf shell projection | Fiber/base phase projection signal. | Full Hopf shell projection over nested shells/tori; connection/holonomy; carrier cuts. |
| L8 gluing/groupoid | Finite arrow/inverse/composition signal. | Real groupoid/gluing structure over local charts/cells; functorial consistency; topology/proof checks. |

## Direct Answer

Most of what was requested has not been done at the proper depth.

What now exists:

- A JAX finite-scale standalone geometry execution wave.
- A JAX finite-scale L0-L8 layer execution wave.
- Validator-clean receipts with promotion blocked.
- Distinct target-specific invariant evidence for the 24 JAX geometry rows.
- A follow-up 24-target full-network strengthening batch with per-target
  subreceipts, MPS/PEPS2D/PEPS3D carrier views, target-specific transport,
  JAX/PyTorch parity, QIT readouts, and controls.

What does not yet exist:

- Protected geometry-choice consumer evidence.
- Noncommutative order tests based on strong independently validated individual sims.
- Terminal downstream admission from these scouts.

## Next Concrete Deepening Target

The next move should not be another all-target generic wrapper. It should choose
one central geometry and build it as a real deep sim.

Recommended first target:

```text
nested_hopf_tori
```

Reason:

- It is central to the intended geometric constraint manifold language.
- It already has a JAX invariant scout and a separate bounded spinor-network
  candidate receipt, so the missing work is clear rather than vague.
- It directly pressures the shell/leaf/fiber/base structure that later layer
  work keeps leaning on.

Minimum deep target for `nested_hopf_tori`:

```text
finite map:
  nested Hopf torus leaf family with shell/leaf indices
  -> spinor-network state over leaves
  -> leaf-to-leaf transport and fiber/base cut readouts

carrier:
  spinor network with MPS plus PEPS2D/PEPS3D or documented equivalent
  bond dimension stress separate from site-count stress

dynamics:
  geometry-specific leaf/fiber/base transport
  not the shared generic compatibility-weight optimizer alone

QIT:
  mutual information
  coherent information where meaningful
  conditional entropy
  logarithmic negativity or equivalent entanglement readout
  cut entropy across leaf/fiber/base partitions

tools:
  JAX x64 primary or mirror for this target
  PyTorch parity or explicit blocked reason
  quimb/cotengra/autoray or equivalent contraction path
  SymPy exact checks for the known formulas
  z3/cvc5 for at least one finite structural exclusion/minimality check
  GUDHI/TopoNetX/rustworkx/XGI where topology/graph claims are made

controls:
  label erase
  invariant erase
  fiber/base scramble
  shell/leaf order scramble
  product/no-entanglement carrier
  dense-closure control
  generic-dynamics-only control
```

## Execution Addendum: 24-Target Full-Network Batch

After the one-target `nested_hopf_tori` correction, the remaining JAX geometry
target set was run through an aggregate full-network strengthening batch:

```text
source:
  system_v5/ops/formal_scouts/sim_jax_geometry_full_network_targets_probe.py

aggregate result:
  system_v5/ops/formal_scouts/results/jax_geometry_full_network_targets_probe_results.json

per-target subreceipts:
  system_v5/ops/formal_scouts/results/jax_geometry_full_network_targets_20260530/
```

Fresh validator status:

```text
targets_total = 24
targets_passed = 24
targets_failed = 0
site_counts = 8, 16, 32, 64
bond_dims = 2, 4
max_jax_torch_delta = 2.6645352591003757e-15
min_order_gap = 0.030740976485093868
min_mutual_information = 0.00030874578251566194
min_log_negativity = 0.008356669068900065
```

What this addendum changes:

- the target set is no longer only a shallow finite-sample JAX wave;
- every target now has a per-target network subreceipt under the aggregate
  formal-scout result;
- the batch still remains scout evidence only.

What this addendum does not change:

- protected geometry-choice consumers remain blocked;
- protected layer consumers remain blocked;
- protected order-composition consumers remain blocked;
- protected downstream consumers remain blocked.
