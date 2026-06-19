# Route genuineness audit - 2026-06-10

Scope: fresh read of the rebuilt route sources for `geo_s3_*`, `geo_s4_*`,
`geo_s5_*`, `geo_s6_*`, `geo_s7_*`, and the five rebuilt ladder packets:
`geo_s1_two_qubit_boundary_exact_v0`, `geo_s1_three_qubit_floor_exact_v0`,
`geo_s1_four_qubit_support_exact_v0`,
`geo_s1_five_qubit_safety_margin_exact_v0`, and
`geo_s1_scaling_stress_678q_exact_v0`.

Method: source audit plus fresh local checks. This audit did not perform the
remediation. The only write is this receipt.

## Bottom line

No S3/S4/S5/S6 wrapper pattern was found. Those claim paths use the aligned
packages to compute the values: qutip/QuantumOptics for state/operator routes
and diffrax/DifferentialEquations for flow routes.

The ladder graph routes are genuine rustworkx searches. The five-qubit packet
is genuine at its stated ceiling: it checks the constructed 11-family graph and
explicitly does not claim a full 1023-vertex arbitrary clique enumeration.

Two routes need demotion/repair language:

- `geo_s7_discrete_refinement_v0`: TopoNetX/GUDHI is genuine, and the
  IntervalArithmetic source is a real interval route, but the currently tracked
  IntervalArithmetic capability receipt fails under `system_v5/julia_carrier`.
  R3 is not clean until the passing optional-project receipt is restored or
  separately cited.
- `geo_s1_scaling_stress_678q_exact_v0`: the rustworkx extension search is
  genuine, and CliffordAlgebras genuinely tests Cl12/Cl14 and small-product
  capability. Cl16 is not materialized through CliffordAlgebras; it is an
  explicit formula artifact gated by Cl12/Cl14 package checks. Any wording that
  says "CliffordAlgebras computed Cl16 directly" should be demoted.

## Checks run

- `scripts/verify_load_bearing_has_capability_probe.py --sim ...` on S3/S4
  qutip files: both passed with no violations.
- `scripts/verify_load_bearing_has_capability_probe.py --sim ...` on S5/S6
  diffrax files: both passed with no violations.
- `scripts/verify_load_bearing_has_capability_probe.py --sim ...` on S3/S4/S5/S6
  Julia files: all passed with no violations for QuantumOptics,
  DifferentialEquations, Symbolics, and Z3.
- `scripts/verify_load_bearing_has_capability_probe.py --sim ...` on
  `geo_s7_discrete_refinement_v0_jax.py`: passed for TopoNetX/GUDHI.
- `scripts/verify_load_bearing_has_capability_probe.py --sim ...` on
  `geo_s7_discrete_refinement_v0_interval.jl`: failed with
  `IntervalArithmetic` status `missing_probe`.
- `scripts/verify_load_bearing_has_capability_probe.py --sim ...` on the five
  ladder JAX graph files: all passed for rustworkx/Z3/cvc5/Symbolics.
- `geo_s3`, `geo_s4`, `geo_s5`, `geo_s6`, `geo_s7`, `geo_s1_four_qubit`, and
  `geo_s1_scaling` exact-strength validators present in-tree all returned
  `ok: true`.

## Per-packet verdicts

### `geo_s3_density_observable_v0` - GENUINE-ROUTE

R1: genuine. The Python route constructs qutip Pauli operators, density
operators, projectors, and qutip superoperators, then applies those objects for
Born and channel rows (`geo_s3_density_observable_v0_pytorch.py:112-180`).
The Julia leg likewise declares QuantumOptics load-bearing and gates it to
state/operator rows.

R2: mirrors are off the claim path. The retained tensor/torch material is
supportive/mirror material; qutip/QuantumOptics owns the audited claim path.

R3: capability gate passed for qutip and QuantumOptics in the source files.

R4 spot recompute: direct qutip route
`qutip_born_plus([0.5,0,0],[1,0,0]) = 0.75`.

Demotion: none.

### `geo_s4_operator_stage_v0` - GENUINE-ROUTE

R1: genuine. The route builds qutip superoperators with `qutip.sprepost`,
applies them to qutip density matrices, and derives affine rows from qutip
expectation components (`geo_s4_operator_stage_v0_pytorch.py:122-190`).

R2: mirrors are off the claim path.

R3: capability gate passed for qutip and QuantumOptics/Symbolics/Z3.

R4 spot recompute: direct qutip affine row for `D_z` returned
`[[7/10,0,0],[0,7/10,0],[0,0,1]]`, with row pass `true`.

Demotion: none.

### `geo_s5_terrain_flows_v0` - GENUINE-ROUTE

R1: genuine. The JAX route calls `diffrax.ODETerm`, `diffrax.diffeqsolve`, and
`diffrax.Tsit5`; the matrix exponential is explicitly labeled as the exact
special-case parity check, not the primary route
(`geo_s5_terrain_flows_v0_jax.py:802-850`).

R2: mirrors are honestly labeled. `jax.scipy.linalg.expm` is retained only as
`exact_special_case_check_not_primary_solver_route`.

R3: capability gates passed for diffrax and DifferentialEquations.

R4 spot recompute: direct diffrax `flow_solver_route` returned `all_pass: true`
with max error vs exact special-case check `2.1105006631216838e-11`.

Demotion: none.

### `geo_s6_stacked_flows_hopf_v0` - GENUINE-ROUTE

R1: genuine. The JAX route calls `diffrax.ODETerm`, `diffrax.diffeqsolve`, and
`diffrax.Tsit5` over batched affine ODE state rows
(`geo_s6_stacked_flows_hopf_v0_jax.py:306-330`).

R2: mirrors are honestly labeled. The exact affine flow remains a comparison
path, while the solver route reports its own diffrax value.

R3: capability gates passed for diffrax and DifferentialEquations.

R4 spot recompute: direct diffrax `loop_order_gap.flow_solver_route` returned
`pass: true` and `max_g_DI_scaled_1e9_diffrax: 363413167`.

Demotion: none.

### `geo_s7_discrete_refinement_v0` - MIXED

R1: topology route genuine. The route builds a TopoNetX simplicial complex,
computes rank-2 incidence, builds a GUDHI simplex tree, runs persistence, and
reads Betti numbers (`geo_s7_discrete_refinement_v0_jax.py:235-286`).

R1 interval route source genuine but receipt-gated problem remains. The Julia
source explicitly runs under `--project=@codex-ratchet-tensorkit-v1.12`, imports
`IntervalArithmetic`, declares it load-bearing, and propagates interval values
through area/holonomy/flux-style functions
(`geo_s7_discrete_refinement_v0_interval.jl:4-8`,
`geo_s7_discrete_refinement_v0_interval.jl:46-61`,
`geo_s7_discrete_refinement_v0_interval.jl:166-175`).

R2: CSV/endpoint mirrors are not the interval claim path in the source.

R3: mixed. TopoNetX/GUDHI capability gates passed. The current
`system_v6/probes/julia/results/intervalarithmetic_capability_results.json`
fails with `package_available: false` under
`system_v5/julia_carrier/Project.toml`, and the generic verifier reports
`missing_probe` for the IntervalArithmetic source file.

R4 spot recompute: TopoNetX/GUDHI `topology_mesh_certificate()` returned
`N=8` shape `[32,96,64]`, Betti `[1,2]`, and all claim rows pass.

Demotion required: do not count the checked-out IntervalArithmetic capability
receipt as passing R3 evidence. Restore/regenerate a passing optional-project
receipt or cite a separate optional-project capability artifact before calling
the IntervalArithmetic leg fully admitted.

### `geo_s1_two_qubit_boundary_exact_v0` - GENUINE-ROUTE

R1: genuine. The route builds a rustworkx graph over nonidentity Pauli strings
and performs a branch-and-bound clique search; the hand matrix scan is retained
as a mirror field (`geo_s1_two_qubit_boundary_exact_v0_jax.py:605-665`).

R2: mirror is labeled as `hand_matrix_scan_mirror_max_clique_size`.

R3: capability gate passed for rustworkx/Z3/cvc5/Symbolics.

R4 spot recompute: direct rustworkx route returned `max_clique_size: 5`.

Demotion: none.

### `geo_s1_three_qubit_floor_exact_v0` - GENUINE-ROUTE

R1: genuine. The route builds rustworkx graphs over Pauli labels and performs
the clique expansion for each checked qubit count
(`geo_s1_three_qubit_floor_exact_v0_jax.py:472-542`).

R2: mirror is labeled as `hand_label_recursion_mirror`.

R3: capability gate passed for rustworkx/Z3/cvc5/Symbolics.

R4 spot recompute: direct rustworkx route
`exhaustive_max_anticommuting_clique(3)` returned `max_clique_size: 7`.

Demotion: none.

### `geo_s1_four_qubit_support_exact_v0` - GENUINE-ROUTE

R1: genuine. The route builds a rustworkx candidate-to-family extension graph
against the constructed 9-family, and separately records a hand-label mirror
(`geo_s1_four_qubit_support_exact_v0_jax.py:457-494`).

R2: mirror is labeled as `hand_label_scan_mirror_candidates`.

R3: capability gate passed for rustworkx/Z3/cvc5/Symbolics. The exact-strength
validator returned `ok: true`.

R4 spot recompute: direct route through `z4_max_anticommuting_family()` returned
`candidate_vertices: 255`, `extension_candidate_count: 0`,
`size_10_extension_exists: false`, and `pass: true`.

Demotion: none.

### `geo_s1_five_qubit_safety_margin_exact_v0` - GENUINE-ROUTE at stated ceiling

R1: genuine for the admitted claim path. The route builds a rustworkx graph for
the constructed family and checks complete pairwise anticommutation
(`geo_s1_five_qubit_safety_margin_exact_v0_jax.py:394-416`).

R2: honest ceiling. The source explicitly labels full 1023-vertex arbitrary
clique enumeration as `not_run` and gives the reason.

R3: capability gate passed for rustworkx/Z3/cvc5/Symbolics.

R4 spot recompute: direct constructed-family graph receipt returned
`graph_nodes: 11`, `graph_edges: 55`, `expected_complete_graph_edges: 55`,
`full_nonidentity_clique_enumeration: not_run`, and `pass: true`.

Demotion: none if the claim remains the constructed-family/theorem-bound claim.
Demote any downstream wording that says a full 1023-vertex clique enumeration
was run.

### `geo_s1_scaling_stress_678q_exact_v0` - MIXED

R1: rustworkx route genuine. The route scans all nonidentity Pauli strings for
extension candidates using a rustworkx graph, and keeps the JAX vectorized scan
as a mirror (`geo_s1_scaling_stress_678q_exact_v0_jax.py:325-364`).

R1 CliffordAlgebras route mixed at the Cl16 boundary. The Julia source declares
CliffordAlgebras load-bearing
(`geo_s1_scaling_stress_678q_exact_v0_julia.jl:50-60`), and the capability
probe genuinely multiplies small Clifford basis vectors and checks Cl12/Cl14
dimensions with CliffordAlgebras APIs
(`julia_load_bearing_capability_probes.jl:198-255`). But the same probe
explicitly records Cl16 as
`canon_positive_complex_clifford_formula_without_materializing_CliffordAlgebra(16,0)`.

R2: mirrors are honestly labeled for the rustworkx/JAX side. The Cl16 formula
artifact is labeled, but it must not be described as direct package
materialization.

R3: rustworkx capability gate passed. CliffordAlgebras capability exists and is
load-bearing for small products and Cl12/Cl14 dimensions, but Cl16 is only a
checked formula artifact.

R4 spot recompute: direct rustworkx `extension_scan(6, family)` searched `4095`
nonidentity Pauli strings and returned `candidate_count: 0`; the JAX mirror
agreed.

Demotion required: keep Cl16 language at "formula artifact gated by Cl12/Cl14
package checks"; do not promote it to "CliffordAlgebras materialized/computed
Cl16 directly."

## R5 - IntervalArithmetic diagnosis

The current checked-out capability receipt fails because it was generated under
`/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml`,
where `IntervalArithmetic` is not installed. Fresh local check:

- `julia --startup-file=no --project=system_v5/julia_carrier -e 'using IntervalArithmetic'`
  fails with `Package IntervalArithmetic not found in current path`.
- `julia --startup-file=no --project=@codex-ratchet-tensorkit-v1.12 -e 'using IntervalArithmetic; ...'`
  succeeds and returns interval bounds `sin([0,pi]) -> [-0.0, 1.0]` and
  `sqrt([4,9]) -> [2.0, 3.0]`.

Historical commit check:

- `git show 7367b25dd:system_v6/probes/julia/results/intervalarithmetic_capability_results.json`
  shows a passing receipt under the optional
  `~/.julia/environments/codex-ratchet-tensorkit-v1.12/Project.toml` project.
- `git show 6aa75cc96:system_v6/probes/julia/results/intervalarithmetic_capability_results.json`
  shows the current failing strict-carrier receipt.

Diagnosis: project-scope/probe-output regression, not a package bug and not a
math gap. The package works in the project named by the S7 interval source. The
tracked capability receipt was later overwritten under a carrier that does not
include IntervalArithmetic. Until repaired, the S7 IntervalArithmetic capability
receipt is not valid passing R3 evidence.
