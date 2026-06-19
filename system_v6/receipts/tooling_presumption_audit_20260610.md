# Tooling/Presumption Audit: Geometry-Stage Packets

Date: 2026-06-10

Scope: committed `system_v6/sims/geo_s1_*`, `geo_s2_*` through `geo_s7_*`, `bloch_root_admissibility_discriminator_v0`, and `mct_nonassoc_weld_packet_v0`.

Bottom line: the owner challenge is materially correct. The packets are not "full tooling" packets. They are mostly scratch-diagnostic envelopes with good ceilings, current source hashes, and many SMT/symbolic checks, but several geometry/state/channel/flow claim paths are still hand-built `jnp`/`torch`/`LinearAlgebra`/stdlib loops. Solver or symbolic gates often check consequences of a hand-built model rather than replacing the model with an aligned domain package.

## Evidence Checked

- `git status --short`: clean before writing this receipt.
- `git ls-tree -r --name-only HEAD system_v6/sims | rg 'geo_s[1-7]|bloch_root_admissibility_discriminator_v0|mct_nonassoc_weld_packet_v0'`: 19 committed packet directories in scope.
- `scripts/verify_load_bearing_has_capability_probe.py --sim <packet-python-file>` with `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`: 58 Python sim/envelope files checked, 33 pass, 23 fail, 2 no-depth.
- Result `source_sha256` check against current committed source files: all audited result JSONs with `source_sha256` matched their source file.
- Source grep for aligned packages: `QuantumOptics`, `diffrax`, `torch_geometric`, and `OrdinaryDiffEq` are absent from audited packet sources; `DifferentialEquations` appears only in `geo_s2_connection_flux_foliation_v0_julia.jl`; `IntervalArithmetic` is genuinely imported only in `geo_s1_exact_closure_v0_julia.jl`; `Symbolics`/`sympy` appear widely; `CliffordAlgebras` appears in selected qubit-ladder Julia legs.

Classification legend:

- `aligned-load-bearing`: an aligned package API output gates `all_pass`, a proof/control, a quotient/classification, or a demotion condition.
- `aligned-supportive`: aligned package is imported or used for a side calculation, mirror, or simplification, but the claim survives through another hand-built route.
- `bare-array`: claim-path computation is primarily handwritten arrays, matrices, loops, finite grids, label scans, or host numeric operations where a domain package should be load-bearing.

## T1 Per-Packet Claim-Path Table

| Packet | Claim path(s) audited | Actual compute route | Classification | Bare-array flag / aligned route |
|---|---|---|---|---|
| `bloch_root_admissibility_discriminator_v0` | Bloch sphere/ball discriminator; division-algebra Hopf ladder; alternativity/sedenion checks | JAX `jnp` sampling/PCA/rank and hand Cayley-Dickson tables; PyTorch rank/Jacobian probes; Julia `LinearAlgebra`; Z3/cvc5 bind integer/rank consequences | `bare-array` with `aligned-load-bearing` SMT checks | Bare for Bloch/ladder mechanics. Use QuantumOptics/Qutip-like state/channel objects for Bloch/density path and a canon algebra artifact/package route for division-algebra multiplication before solver binding. |
| `geo_s1_exact_closure_v0` | Bloch-Hopf identity, metric/volume/area, linking/double-cover, Haar/commuting square, crossing closure | JAX leg is mostly `sympy` exact derivation plus Z3/cvc5; Julia uses `Symbolics`, `IntervalArithmetic`, Z3; PyTorch mirrors crossing with `sympy` | Mostly `aligned-load-bearing` | This is the strongest tooling packet. Residual JAX/PyTorch arrays are supportive. Keep as reference pattern: exact symbolic/interval path first, numeric lanes only mirrors. |
| `geo_s1_finite_phase_lens_v0` | finite phase quotient tower `S3/Z_N`, orbit counts, volume comparison, non-free control | JAX/PyTorch enumerate phase labels and density with handwritten arrays/sets; Julia uses integer quotient count plus Z3; no topology package | `bare-array` plus solver checks | Use a topology/algebraic route for lens-space quotient invariants, for example GUDHI/TopoNetX/Sage/Oscar-style homology or explicit group-action package, then use SMT only to bind finite count consequences. |
| `geo_s1_five_qubit_safety_margin_exact_v0` | 5Q support: `C^32`, `CP31`, density dimension, `Cl10`, chirality split, max anticommuting family | Julia uses `CliffordAlgebras`, `Symbolics`, Z3; JAX/PyTorch use `sympy`, `torch`, hand Pauli/Jordan-Wigner matrices and solver checks | Mixed `aligned-load-bearing` and `bare-array` | Clifford/Symbolics/SMT path is real in Julia. PyTorch/JAX density/state and max-family scans are still handwritten; use QuantumOptics for state/density paths and graph/clique tooling for max anticommuting family scans. |
| `geo_s1_four_qubit_support_exact_v0` | 4Q support: `Cl8`, chirality/triality pressure, extension scan, support controls | Julia `Symbolics`/Z3 with hand matrices; JAX `sympy`/Z3/cvc5; PyTorch exact integer-pair tensors and `torch.func` | `bare-array` for Clifford/triality graph; `aligned-load-bearing` for SMT/symbolic consequences | Add load-bearing `CliffordAlgebras` for the gamma/chirality path and graph tooling (`rustworkx`/NetworkX/torch_geometric Data only if PyTorch graph route is claimed) for extension scans. |
| `geo_s1_negative_models_v0` | S1 negative controls: no-conjugate Hopf, grid collapse, classical-bit/positive controls | JAX/PyTorch handwritten spinor/Hopf/grid arrays; Julia `LinearAlgebra` plus Z3; common adapter math | `bare-array` | Good as negative suite, but not full tooling. Use same aligned S1 route as positive S1: QuantumOptics/Manifolds for states/maps and exact symbolic/SMT for controls. |
| `geo_s1_quaternion_model_v0` | unit-quaternion Hopf model, complex-pair agreement, linking, volume, double cover | Julia imports `Quaternions` but marks it supportive; JAX/PyTorch/numpy hand `qmul`, Hopf, curves, Monte Carlo/integrals; Z3/cvc5 check disagreement bounds | `bare-array` with `aligned-supportive` Quaternions and solver checks | Make `Quaternions`/Manifolds-style quaternion operations load-bearing, and use QuantumOptics/Manifolds for spinor-to-Bloch/SU2-SO3 geometry. Numpy lane is a control only. |
| `geo_s1_scaling_stress_678q_exact_v0` | 6/7/8Q ladder: dimensions, `Cl_(2n)`, chirality splits, max anticommuting family | Julia `Symbolics`/Z3 and `CliffordAlgebras` supportive; JAX/PyTorch hand label arithmetic, density sparsity, Pauli/JW combinatorics, `sympy`, Z3/cvc5 | Mixed; `bare-array` for scaling/graph scans | Promote `CliffordAlgebras` from supportive to load-bearing for Clifford claims. Use graph/clique tooling for max anticommuting family and QuantumOptics for density/state claims. |
| `geo_s1_spinor_hopf_free_v0` | normalized spinors, Hopf map, fibers/linking, density quotient, `S2` base, `S3` metric/volume | JAX/PyTorch/Julia hand Pauli matrices, spinors, Hopf maps, lattice/Monte Carlo/linking methods; Z3/cvc5 only bounded controls | `bare-array` | Use QuantumOptics states/density matrices and Manifolds/geometry packages for `S3 -> S2` geometry; keep solvers for can-fail controls. |
| `geo_s1_three_qubit_floor_exact_v0` | 3Q floor: reduced densities, tangle, `Cl6`, chirality, support/floor boundary | Julia `Symbolics`/Z3 with hand gamma tables; JAX `sympy`/SMT; PyTorch exact tensor mirror | Mixed; symbolic/SMT `aligned-load-bearing`, Clifford/density `bare-array` | Add load-bearing `CliffordAlgebras` for `Cl6` and QuantumOptics for density/reduced-state paths. |
| `geo_s1_two_qubit_boundary_exact_v0` | 2Q boundary/control: `CP3`, Bell/concurrence, `Cl4`, max family 5, failure of 3-slot floor | Julia imports `CliffordAlgebras` but result marks it supportive; `Symbolics`/Z3 load-bearing; PyTorch/sympy/Z3/cvc5 hand state/matrix route | Mixed; `bare-array` for quantum-state and Clifford mechanics | Promote `CliffordAlgebras` to load-bearing for `Cl4`; use QuantumOptics for Bell/concurrence/density path. |
| `geo_s2_connection_flux_foliation_v0` | S2 connection, flux/Stokes, foliation, double-cover grid accounting | Julia uses `DifferentialEquations.ODEProblem/solve(Tsit5)` plus Z3; JAX uses `sympy` derivations and Euler/grid rows; PyTorch uses `torch.func`/grid checks | Julia `aligned-load-bearing`; mirrors partly `bare-array` | This is the only audited packet with a real flow package. Add `diffrax` for JAX flow mirrors or keep JAX explicitly supportive. |
| `geo_s2_negative_models_v0` | wrong connection, broken Stokes pairing, naive torus cover negative controls | Common handwritten formulas; JAX/PyTorch vector/grid rows; Julia Z3 only | `bare-array` plus SMT controls | Use same DifferentialEquations/diffrax path as S2 positive for negative controls if flow failure magnitude is claim-bearing. |
| `geo_s3_density_observable_v0` | one-qubit density/observable geometry, Born fields, projective updates, probe quotients, CPTP contractions | JAX `sympy`/Z3/cvc5 hand Pauli/Bloch density matrices; Julia `LinearAlgebra`/Z3 hand trace tables; PyTorch hand density/channel tensors and `torch.func` | `bare-array` for quantum states/channels; `aligned-load-bearing` for symbolic/SMT consequences | Use QuantumOptics.jl or equivalent for states, projectors, observables, channels, trace distance/fidelity before SMT binding. |
| `geo_s4_operator_stage_v0` | one-qubit operator-channel geometry for `D_z`, `D_x`, `R_x`, `R_z`, pinned-y conversion | Julia `Symbolics`/Z3 derive affine rows from hand density/channel forms; JAX `sympy` mirror; PyTorch pinned tensor commutator checks | Mixed; domain mechanics `bare-array` | Use QuantumOptics channel/superoperator objects as load-bearing, with Symbolics/SMT checking derived affine consequences. |
| `geo_s5_terrain_flows_v0` | terrain-generator flows, exact `A,b`, fixed/basin receipts, GKSL/CPTP boundary, purity/unitality | Julia `Symbolics`/Z3 derives generator rows; JAX uses `sympy` and `jax.scipy.linalg.expm` supportive Choi fixtures; PyTorch hand tensor flow mirrors | Symbolic/SMT `aligned-load-bearing`; flow/channel evolution `bare-array` | Use OrdinaryDiffEq/DifferentialEquations or diffrax for continuous flows and QuantumOptics/Lindblad tooling for GKSL/CPTP channel claims. |
| `geo_s6_stacked_flows_hopf_v0` | stacked/restricted Hopf-shell leakage, placement, Matrix64 overlay, loop-order gap from exported S5 `A,b` | JAX parses S5 JSON, uses `sympy`, `jax.scipy.linalg.expm`; Julia `LinearAlgebra`/Z3; PyTorch `torch.linalg.matrix_exp`; solvers check loop gap | `bare-array` for finite-time flow/stacked geometry; SMT only consequence checks | Use a real ODE/flow solver route (`diffrax`, OrdinaryDiffEq/DifferentialEquations) and explicit source-lock normalization for imported S5/Matrix64 rows. |
| `geo_s7_discrete_refinement_v0` | finite Hopf-torus grids, quotient/parity cover, row locations, area/holonomy/flux/Stokes convergence curves | Shared Python core loops over grids/cells; JAX/PyTorch transport probes; Julia `LinearAlgebra`/Z3; CSV curve export | `bare-array` for grid/refinement geometry; SMT for parity counts | Use GUDHI/TopoNetX/rustworkx or a geometry/mesh package for grid/cell topology and interval/error certificates for convergence curves. |
| `mct_nonassoc_weld_packet_v0` | finite `M(C,t)` nonassociative weld, bracketing-sensitive associator, support/quotient counts, derivation summary | JAX/PyTorch/Julia hand table transforms and associator loops over exported artifact values; Z3/cvc5 bind residuals; Julia `LinearAlgebra` declared load-bearing | `bare-array` with `aligned-load-bearing` solver checks | Keep artifact verification, but move algebra operations into a canon algebra API/package or a dedicated checked artifact consumer. `LinearAlgebra` is not enough for nonassociative algebra semantics. |

## T1 Bare-Array Claim Paths And Aligned Alternatives

Severity order here is based on how close the bare route is to the claimed object.

1. `geo_s3_density_observable_v0` and `geo_s4_operator_stage_v0`: one-qubit density, observable, projector, CPTP/channel, trace/fidelity, and superoperator mechanics are hand Pauli/Bloch matrices. Aligned route: QuantumOptics.jl or equivalent state/channel/observable APIs as the load-bearing route, then Symbolics/SMT to check derived affine/Born consequences.
2. `geo_s5_terrain_flows_v0` and `geo_s6_stacked_flows_hopf_v0`: flow claims use symbolic `A,b` plus `jax.scipy.linalg.expm`/`torch.linalg.matrix_exp`/Julia `LinearAlgebra`, not a real ODE/reachability route. Aligned route: OrdinaryDiffEq/DifferentialEquations in Julia and diffrax in JAX for flow evolution, with exact/symbolic and SMT checks only as guards.
3. `geo_s1_spinor_hopf_free_v0`, `geo_s1_quaternion_model_v0`, and S1 negative models: spinor, Hopf, quaternion, volume, and linking computations are mostly hand arrays/lattices/integrals. Aligned route: QuantumOptics for spinor/density quotient; Manifolds/geometry/quaternion packages for Hopf/quaternion geometry; solvers for can-fail controls.
4. S1 qubit ladder graph/family scans (`geo_s1_four_qubit_support_exact_v0`, `geo_s1_scaling_stress_678q_exact_v0`, parts of `geo_s1_three_qubit_floor_exact_v0` and `geo_s1_two_qubit_boundary_exact_v0`): Pauli/JW labels, max anticommuting family, and extension scans are handwritten combinatorics. Aligned route: `CliffordAlgebras` load-bearing for Clifford structure plus graph/clique tooling (`rustworkx`, NetworkX, or torch_geometric when a PyTorch graph route is explicitly claimed).
5. `bloch_root_admissibility_discriminator_v0`: Bloch geometry and division-algebra ladder use hand JAX/PyTorch/Julia arrays. Aligned route: QuantumOptics state/Bloch APIs for the Bloch path and canon algebra artifact/package APIs for multiplication/alternativity before SMT.
6. `geo_s7_discrete_refinement_v0`: grid/cell topology and convergence curves are Python loops plus CSV output. Aligned route: GUDHI/TopoNetX/rustworkx/mesh tooling plus interval/error-bound checks.
7. `mct_nonassoc_weld_packet_v0`: artifact values are consumed, but associator and derivation operations are array/table loops. Aligned route: checked canon algebra consumer API with exact table provenance and fixed bracketing semantics.

## T2 TOOL_MANIFEST / INTEGRATION_DEPTH Honesty

The Python capability-probe gate was run with:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim <file>
```

Summary:

| Result | Count | Meaning |
|---|---:|---|
| PASS | 33 | All declared Python load-bearing tools had a passing legacy capability probe, or no load-bearing tools were declared. |
| FAIL | 23 | At least one declared load-bearing Python tool had no matching passing capability probe. |
| NO_DEPTH | 2 | Python file has no `TOOL_INTEGRATION_DEPTH` for the script to parse. |

Failures:

| Packet | Failing Python file(s) | Failed declared load-bearing tool(s) |
|---|---|---|
| `bloch_root_admissibility_discriminator_v0` | `*_jax.py`, `*_pytorch.py` | `jax:missing_probe`, `jax.numpy:missing_probe`, `torch.func:missing_probe` |
| `geo_s1_exact_closure_v0` | `*_pytorch.py` | `torch.func:missing_probe` |
| `geo_s1_finite_phase_lens_v0` | `*_jax.py`, `*_pytorch.py` | `jax:missing_probe`, `torch.func:missing_probe` |
| `geo_s1_four_qubit_support_exact_v0` | `*_pytorch.py` | `torch.func:missing_probe` |
| `geo_s1_negative_models_v0` | `*_jax.py`, `*_pytorch.py` | `jax:missing_probe`, `torch.func:missing_probe` |
| `geo_s1_quaternion_model_v0` | `*_jax.py`, `*_pytorch.py` | `jax:missing_probe`, `torch.func:missing_probe` |
| `geo_s1_scaling_stress_678q_exact_v0` | `*_jax.py` | `jax:missing_probe`, `jax.numpy:missing_probe` |
| `geo_s1_spinor_hopf_free_v0` | `*_jax.py`, `*_pytorch.py` | `jax:missing_probe`, `torch.func:missing_probe` |
| `geo_s1_three_qubit_floor_exact_v0` | `*_pytorch.py` | `torch.func:missing_probe` |
| `geo_s2_connection_flux_foliation_v0` | `*_pytorch.py` | `torch.func:missing_probe` |
| `geo_s2_negative_models_v0` | `*_jax.py`, `*_pytorch.py` | `jax:missing_probe`, `torch.func:missing_probe` |
| `geo_s3_density_observable_v0` | `*_pytorch.py` | `torch.func:missing_probe` |
| `geo_s4_operator_stage_v0` | `*_pytorch.py` | `torch.func:missing_probe` |
| `geo_s5_terrain_flows_v0` | `*_pytorch.py` | `torch.func:missing_probe` |
| `geo_s6_stacked_flows_hopf_v0` | `*_pytorch.py` | `torch.func:missing_probe` |
| `geo_s7_discrete_refinement_v0` | `*_pytorch.py` | `torch.func:missing_probe` |
| `mct_nonassoc_weld_packet_v0` | `*_jax.py` | `jax:missing_probe`, `jax.numpy:missing_probe` |

Important caveats:

- This script only parses Python. Julia declarations such as `Symbolics`, `IntervalArithmetic`, `DifferentialEquations`, `CliffordAlgebras`, `Quaternions`, `LinearAlgebra`, and `Z3` were inspected from source/result fields, not accepted through this Python gate.
- `torch` itself often passes, but `torch.func` repeatedly fails because no canonical `torch.func` capability probe exists under the script's alias table.
- `jax` and `jax.numpy` should generally not be declared `load_bearing` under the current gate unless a passing capability probe exists and the JAX API genuinely gates the claim. Several packets should demote JAX/JAX.numpy to supportive or add a proper capability receipt.
- `LinearAlgebra` is over-claimed in Julia for some algebra/geometry packets. It can support numerics, but it is not a domain-aligned proof of quantum, flow, topology, or nonassociative-algebra semantics.

## T3 Numpy Boundary

No audited committed source uses `.numpy()` or `np.asarray` as a hidden cross-engine claim path. The `np.asarray` hits in envelopes are mostly forbidden-exchange strings; the actual JAX sources use `jnp.asarray`.

The one explicit numpy lane is:

- `geo_s1_quaternion_model_v0_numpy_control.py`: `numpy_control`, no `TOOL_INTEGRATION_DEPTH`, `claim_path_tools: []`.

Boundary finding:

- No claim-bearing value was found whose only path is the numpy control lane.
- However, `geo_s1_quaternion_model_v0_envelope.py` includes the numpy control in `legs_exit_0_by_receipt`, `pin_identical`, `ceiling_exact`, `Q2_receipts_pass`, `wrong_convention`, and `single_method` gates. That is acceptable only if it remains labeled `control lane only`; it must not be promoted into `claim_path_tools`.

## T4 Missed-Gaps Sweep

1. Source/result staleness was not the issue. All result `source_sha256` values checked against their source files matched.
2. Domain package absence is systematic. `QuantumOptics`, `diffrax`, `torch_geometric`, and `OrdinaryDiffEq` do not appear in the audited packet sources. This directly supports the owner concern that aligned package coverage was missed.
3. Flow semantics drift across stages. S2 positive uses a real Julia ODE package (`DifferentialEquations.ODEProblem/solve(Tsit5)`), while S5/S6 flow language mostly means symbolic `A,b` plus matrix exponential, and S7 means discrete grid refinement. Those are different claims and should not be summarized as one "flow tooling" standard.
4. Quantum state/channel semantics are mostly hand matrices. S3/S4/S5 use Pauli/Bloch and channel matrices directly. SMT and Symbolics check derived rows, but they do not make QuantumOptics-style state/channel APIs load-bearing.
5. Qubit-ladder exactness is uneven. The 5Q packet has the strongest Julia `CliffordAlgebras` usage. 2Q/3Q/4Q/scaling packets still contain substantial hand gamma/Pauli/JW scans and graph-like extension logic.
6. S6 imports upstream canonical/promoted rows inside a top-level scratch-diagnostic packet. The top-level envelope remains `classification: scratch_diagnostic`, `promotion_allowed: false`, but embedded Matrix64/source rows include `classification: canonical`, `formal_admission_allowed: true`, and `promotion_allowed: true`. Future packet audits should normalize or quarantine imported ceiling fields so scratch envelopes cannot visually inherit stronger upstream status.
7. `mct_nonassoc_weld_packet_v0` envelope has `claim: None` even though the engine legs contain the finite `M(C,t)` claim. This is a receipt hygiene gap and makes downstream audit/search weaker.
8. Result envelopes correctly include forbidden exchange strings, but repeated `np.asarray` forbidden strings can cause noisy scans. Future audits should distinguish forbidden-policy text from actual data-exchange calls.
9. The Python capability-probe gate is not enough for Julia. A Julia analog is needed for `Symbolics`, `IntervalArithmetic`, `DifferentialEquations`, `CliffordAlgebras`, `Quaternions`, and Julia `Z3`.

## Bounded Remediation Queue

1. Repair manifest honesty first. Demote `jax`, `jax.numpy`, and `torch.func` from `load_bearing` to `supportive` wherever the current capability-probe gate fails, unless a real capability receipt is added. Do not change scientific claims in the same patch.
2. Add Julia load-bearing capability probes. Minimal probes should cover `Symbolics`, `IntervalArithmetic`, `DifferentialEquations`, `CliffordAlgebras`, `Quaternions`, and Julia `Z3`, with positive, negative/erased, boundary, and demotion cases.
3. Rebuild S3/S4 state/channel paths with QuantumOptics or an equivalent quantum-state/channel API. Treat the existing hand Pauli/Bloch matrices as controls or mirrors.
4. Rebuild S5/S6 flow paths with a real flow solver route: DifferentialEquations/OrdinaryDiffEq in Julia and diffrax in JAX. Keep matrix exponentials as exact/supportive special-case checks, not the full flow tool story.
5. Promote Clifford tooling consistently across the qubit ladder. For `Cl4`, `Cl6`, `Cl8`, `Cl10`, and scaling rungs, make `CliffordAlgebras` or a checked canon Clifford artifact the route that computes/gates the Clifford claim.
6. Add graph tooling for max anticommuting-family and extension scans. Use `rustworkx`/NetworkX for exact graph search, or `torch_geometric` only when the packet explicitly claims a PyTorch graph route.
7. Rework S7 grid/refinement evidence with topology/mesh tooling and interval/error certificates. CSV curves should remain output artifacts, not proof surfaces.
8. Fix `mct_nonassoc_weld_packet_v0` envelope hygiene by lifting the engine claim into the envelope and separating artifact verification from handwritten table operations.
9. Normalize imported ceilings in S6. Embedded canonical/promoted upstream rows should be carried as upstream metadata, not as local packet status.
10. After each remediation, rerun `scripts/verify_load_bearing_has_capability_probe.py --sim` on changed Python files and add the Julia analog once available.

## Audit Verdict

The committed packet estate is useful scratch diagnostic evidence, not a full aligned-tooling geometry stage. The strongest accepted pieces are exact symbolic/SMT and the S2 Julia ODE lane. The weakest pieces are quantum state/channel paths, flow evolution beyond S2, topology/grid refinement, graph/family scans, and nonassociative algebra operations that still run through hand arrays or loops.

