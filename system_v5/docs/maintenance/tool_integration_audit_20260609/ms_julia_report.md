# Julia Full-Stack Tool-Integration Audit

Bottom line: the Julia leg is strict-carrier runnable and several calls are genuinely load-bearing, but the receipt overclaims `load_bearing` for `CliffordAlgebras`, `Attractors+DynamicalSystems`, `Manifolds`, `ITensors`, and `Yao`. Those are emitted as observables or smoke checks, but they do not materially feed the pass criterion or the quotient/coarsening decision.

## Scope Checked

- Source found: `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/foundation_spinor_network_full_stack_layer_julia.jl`
- Requested result path missing: `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_julia_results.json`
- Actual matching result audited: `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/results/foundation_spinor_network_full_stack_layer_julia_results.json`
- Source SHA in result matches current source: `cb02c47fa2f300491e0f4a426d101ecc5448047f4f7f174bd9bfbc23abe5c805`
- Result says `all_pass=true`, `classification=scratch_diagnostic`, `reads_peer_result=false`, `julia_project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml`.
- Runtime doctor was clean: strict carrier project active, `JULIA_LOAD_PATH=@:@stdlib`, selected packages import under carrier, no repo pollution found.

## Load-Bearing Definition Used

`genuine_load_bearing`: the package call produces a value that feeds an emitted result object and materially feeds a control, quotient/coarsening decision, SMT verdict, or `all_pass`.

`decorative_or_weak`: the package call runs and may emit a field, but removal would not change `all_pass` or the core quotient/coarsening decision, or the call is not tied to the claimed carrier object.

## Per-Tool Verdicts

| Tool | Genuine or decorative | API correctness | Evidence and footgun |
|---|---|---|---|
| `QuantumOptics` | Genuine load-bearing. `coherent_information` and erased coherent information feed `carrier_erasure.flips`; `coherent_information != erased_coherent_information` also feeds `drop_probe_strictly_coarsens`. | Correct. Uses top-level import and qualified calls: `QuantumOptics.tensor`, `SpinBasis`, `Ket`, `dm`, `Operator`, `ptrace`, `liouvillian`, `sigmax`, `sigmam`, `entropy_vn`. Strict-carrier available. | Footgun: `liouvillian_shape` is only a boundary smoke check; the claim-bearing QIT path is entropy/coherent-information, not the Liouvillian itself. Keep `QuantumOptics.entropy_vn` qualified. |
| `Octonions` | Genuine load-bearing. Package-derived octonion multiplication produces `octonion_associator_norm=2.0`; it feeds `associative_control.flips`, `drop_probe_strictly_coarsens`, and Z3 table construction. | Correct. Uses top-level import and qualified constructor `Octonions.Octonion`. Strict-carrier available. | Footgun: `coeffs_oct` uses `getfield(o, idx)` positional extraction. That is brittle against package internals. Prefer a documented coefficient accessor if available, or isolate and test the positional layout in a small API probe. |
| `Quaternions` | Genuine load-bearing as a control. `quaternion_order_gap=2.0` and `quaternion_associator_control_norm=0.0` feed `commuting_control.flips`, `associative_control.flips`, and Z3 quaternion control. | Correct. Uses top-level import and qualified constructor `Quaternions.Quaternion`. Strict-carrier available. | Footgun: `coeffs_quat` also uses positional `getfield`. Same recommendation as Octonions: add a tiny coefficient-layout guard if no public accessor exists. |
| `CliffordAlgebras` | Decorative / weak, despite manifest claiming `load_bearing`. The code emits `clifford_dimension_cl3=8` and `clifford_e1e2_anticommutes=true`, but there is no `tool_calls` entry for `CliffordAlgebras`, and these fields do not feed `controls`, `drop_probe_strictly_coarsens`, or `all_pass`. | Mostly works but qualification is incomplete. `CliffordAlgebras.dimension(cl3)` is correctly qualified, but `CliffordAlgebra(3)`, `basevector`, and `MultiVector` are unqualified. Strict-carrier available. | Footgun: this is a sanity check, not a claim-bearing Clifford path. Either demote `CliffordAlgebras` to supportive/decorative or make it feed a named control and add a `tool_calls` entry. Qualify `CliffordAlgebras.CliffordAlgebra`, `CliffordAlgebras.basevector`, and `CliffordAlgebras.MultiVector` if exported names are available that way. |
| `DifferentialEquations` | Genuine load-bearing. `ODEProblem/solve/Tsit5` generates `final_excited_population` and `final_trace`; `final_trace` is directly checked by `all_pass`. | Correct. Top-level import, qualified `DifferentialEquations.ODEProblem`, `solve`, and `Tsit5`. Strict-carrier available. | Footgun: the ODE path is independent of the `QuantumOptics.liouvillian` object. If claiming a single QIT/dynamics carrier, add an equivalence/consistency check or derive both from the same Hamiltonian/jump object explicitly. |
| `Attractors+DynamicalSystems` | Decorative / weak. It emits `attractors_package_basin.attractor_count=2` and appears in `tool_calls`, but `all_pass` and `drop_probe_strictly_coarsens` use the hand-coded finite basin counts, not the package basin result. The package ODE `u-u^3` is not tied to `TARGET`, `GRAPH_EDGES`, QIT state, or spinor-network update. | Runs under strict carrier, but namespace discipline is incomplete. `CoupledODEs`, `StateSpaceSet`, `AttractorsViaProximity`, and `basins_of_attraction` are unqualified despite the namespace-collision lesson. Strict-carrier available for both packages. | Footgun: the receipt string says `Attractors.basins_of_attraction with DynamicalSystems.CoupledODEs`, but the code calls all four APIs unqualified. Also, this package basin is not the basin that gates `all_pass`. Either wire the package basin into the finite update/control path or demote it. |
| `Manifolds` | Decorative / weak. `Manifolds.distance` emits `s3_distance_to_erased_reference`, but `all_pass` does not use it. `quotient_readout.M` names Hopf/S3 readout, but `drop_probe_strictly_coarsens` ignores geometry. | Mostly correct but qualification is partial. Uses `Manifolds.distance`, but `Sphere(3)` is unqualified. Strict-carrier available. | Footgun: `TARGET ./ norm(TARGET)` is a unit vector in `R^4`, so it is admissible for `Sphere(3)`, but no explicit `Manifolds.is_point`/membership guard is recorded. Add one if this remains claim-bearing. |
| `Graphs` | Genuine load-bearing. `Graphs.SimpleGraph/add_edge!` produces `cycle_rank=2`; `cycle_rank > 0` feeds `drop_probe_strictly_coarsens`, which feeds `all_pass`. | Correct. Top-level import and qualified `Graphs.SimpleGraph`, `add_edge!`, `nv`, `ne`, `connected_components`. Strict-carrier available. | Footgun: negative control is textual only: "edge-erasure would reduce rank". To harden, compute the erased/control graph rank and make it a control field. |
| `ITensors` | Decorative / weak. It emits `contraction_norm=1.0` and a `tool_calls` entry, but it does not feed `controls`, `drop_probe_strictly_coarsens`, or `all_pass`. The tensor product has separate indices for all four nodes and does not encode graph edges. | Correct API use for the smoke path. Uses top-level import and qualified `ITensors.Index`, `ITensors.ITensor`, `ITensors.dag`, `ITensors.scalar`. Strict-carrier available. | Footgun: `contraction_norm=1.0` is close to tautological for one-hot node tensors with disjoint indices. It is not a network contraction over graph structure. Demote or add edge/shared-index contractions tied to `GRAPH_EDGES` and a real erasure control. |
| `Yao` | Decorative / weak. `unitary_xh_commutator_norm` is emitted in `dynamics` and `tool_calls`, but does not feed any control, quotient, or `all_pass`. It is not connected to the ODE or QIT state. | Correctly qualified for the namespace lesson: `Yao.mat(Yao.X)` and `Yao.mat(Yao.H)`. Strict-carrier available. | Footgun: the manifest says "node unitary control", but it is just an isolated X/H commutator. Make it act on the node state or demote it. |
| `Z3` | Genuine load-bearing. Solver outputs feed `z3_derive_flip.flips`, which feeds `all_pass`; the expressions are derived from bound multiplication tables and finite state update, not just scalar restatement. | Correct for the known namespace lesson: top-level import and qualified `Z3.add`, `Z3.check`, `Z3.Expr`, `Z3.Libz3`, `Z3.IntVal`, `Z3.IntVar`, `Z3.And`, `Z3.Or`, `Z3.Not`, `Z3.If`. Strict-carrier available. | Footgun: custom wrappers call low-level `Z3.Libz3.Z3_mk_add/mul/ge`. That is acceptable but brittle: arity and AST-vector handling should stay in a micro-guard because wrapper API drift can fail silently or segfault rather than produce a Julia exception. |

## Cross-Cutting Findings

1. The result `TOOL_INTEGRATION_DEPTH` is too generous. It marks every requested package as `load_bearing`, but only `QuantumOptics`, `Octonions`, `Quaternions`, `DifferentialEquations`, `Graphs`, and `Z3` materially feed the current pass/coarsening logic.
2. `CliffordAlgebras` is especially misclassified: it is in `aligned_packages_load_bearing`, but absent from `tool_calls` and absent from the final acceptance path.
3. `Attractors+DynamicalSystems`, `Manifolds`, `ITensors`, and `Yao` are valid strict-carrier API calls, but currently behave as smoke/observable sidecars, not claim-bearing integration.
4. Namespace discipline is good for `QuantumOptics`, `Graphs`, `ITensors`, `Yao`, `Z3`, `Octonions`, and `Quaternions`. It is incomplete for `CliffordAlgebras`, `Attractors+DynamicalSystems`, and `Manifolds`.
5. The code uses only strict-carrier-available packages among the requested set. The doctor confirmed the carrier project imports `Attractors`, `CliffordAlgebras`, `DifferentialEquations`, `DynamicalSystems`, `Graphs`, `ITensors`, `Manifolds`, `Octonions`, `QuantumOptics`, `Quaternions`, `Yao`, and `Z3` with `JULIA_LOAD_PATH=@:@stdlib`.
6. Top-level imports are respected. There is no `using` inside functions.

## Concrete `julia-sim` Skill Patch Recommendations

Add these lessons to the `Strict-Carrier Truth + Namespace Discipline` or `Step 2: Choose A Load-Bearing Package` section:

1. `TOOL_INTEGRATION_DEPTH="load_bearing"` requires more than a successful package call or emitted scalar. The package-derived value must feed a named control, quotient/coarsening decision, SMT verdict, acceptance predicate, or other claim-bearing observable. Otherwise mark it `supportive` or `decorative`.
2. `aligned_packages_load_bearing` must be a subset of packages with a corresponding `tool_calls` entry and a traceable path into `controls`, `M_C_quotient`, `all_pass`, or the named acceptance observable. Do not list a package there for a sanity check only.
3. For `CliffordAlgebras`, qualify collision-prone and exported APIs, not just `dimension`: prefer `CliffordAlgebras.dimension`, and verify whether `CliffordAlgebras.CliffordAlgebra`, `CliffordAlgebras.basevector`, and `CliffordAlgebras.MultiVector` are valid in the current package before using them in carrier sims. If any must remain unqualified, record why.
4. For `Attractors` and `DynamicalSystems`, qualify APIs in mixed-package carrier files: `DynamicalSystems.CoupledODEs`, `DynamicalSystems.StateSpaceSet`, `Attractors.AttractorsViaProximity`, and `Attractors.basins_of_attraction` if exported under those modules in the current version. If the actual exported owner differs, record the verified owner in the skill.
5. For `Manifolds`, qualify constructors/functions when possible and record a point-membership guard for manifold claims: create the manifold, normalize or construct points, then check/record an admissibility predicate before using distance/geodesic values as claim-bearing.
6. For `ITensors`, a tensor smoke check is not a network claim. Load-bearing ITensors use should encode the graph or carrier coupling in shared indices, contractions, MPS/MPO structure, or explicit edge tensors, and should include an erasure/control contraction.
7. For `Yao`, `Yao.mat(Yao.X)` and `Yao.mat(Yao.H)` are namespace-correct, but a gate-matrix commutator is only decorative unless it acts on the carrier state or feeds a control/acceptance predicate.
8. For `QuantumOptics` plus manual `DifferentialEquations` Lindblad paths, do not imply they are the same dynamics unless the Hamiltonian/jump operators are shared or an explicit consistency check connects `QuantumOptics.liouvillian` to the ODE RHS.
9. For `Octonions` and `Quaternions`, package-derived basis coefficients extracted with positional `getfield` need a micro-guard or a documented accessor. Positional field layout is a package-internal dependency unless the package documents it.
10. For `Z3.jl`, using low-level `Z3.Libz3` constructors is acceptable for missing high-level helpers, but every custom wrapper (`mk_add`, `mk_mul`, `mk_ge`) should have a strict-carrier micro-probe covering arity, context identity, SAT/UNSAT expectation, and failure behavior.

## Recommended Reclassification For This Result

Keep as `load_bearing`:

- `QuantumOptics`
- `Octonions`
- `Quaternions`
- `DifferentialEquations`
- `Graphs`
- `Z3`

Demote to `supportive` or `decorative` until wired into the acceptance path:

- `CliffordAlgebras`
- `Attractors`
- `DynamicalSystems`
- `Manifolds`
- `ITensors`
- `Yao`

Suggested report note: keep the overall result ceiling at `scratch_diagnostic`; do not promote it as a full-stack load-bearing integration receipt until the demoted tools either feed the result logic or are honestly marked supportive/decorative.
