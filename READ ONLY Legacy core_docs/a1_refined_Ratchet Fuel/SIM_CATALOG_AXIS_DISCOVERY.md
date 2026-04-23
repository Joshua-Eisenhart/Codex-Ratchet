# SIM CATALOG: AXIS DISCOVERY (0-12)

DATE_UTC: 2026-03-25T00:00:00Z
PURPOSE: To enumerate and formally map the QIT simulations responsible for exploring, falsifying, and securing the constraint manifold degrees of freedom.

## 1) Foundation Slices (Axes 0-6)
The pairwise and triplet orthogonality suites that guarantee the fundamental physical dimensions are mathematically distinct.

| SIM Name | Purpose | Expected Result | Result File |
| :--- | :--- | :--- | :--- |
| `axis_orthogonality_suite.py` | Pairwise independence check $C(6,2)$ | 15 `PASS` | `axis_orthogonality_v3_results.json` |
| `axis_triplet_orthogonality_sim.py` | Triplet independence check $C(6,3)$ | 20 `PASS` | `axis_triplet_orthogonality_results.json` |
| `axis_6_precedence_sim.py` | Proves bounded noncommutativity | 1 `PASS` | `axis_6_precedence_results.json` |

## 2) The Upper Manifold (Axes 7-12)
Exploratory SIMs testing the operator-level / Choi mirror geometry of the base axes.

| SIM Name | Purpose | Expected Result | Result File |
| :--- | :--- | :--- | :--- |
| `axis_7_12_orthogonality_suite.py` | Tests whether higher-order superoperators remain orthogonal to each other and their base pairs. | `PASS` / `KILL` mixes reflecting manifold bounds. | `axis_7_12_ortho_results.json` |
| `axis_lie_closure_expansion_sim.py` | Generates nested commutator algebra from Axes 0-6 to check if the generator span requires Axes 7-12 for closure. | Dynamic Rank Detection | `axis_lie_closure_rank_results.json` |
| `hopf_torus_meta_sim.py` | Tests whether iterative descent from Axis-12 to Axis-0 preserves topological invariants. | Continuous invariant | `hopf_torus_meta_results.json` |

## 3) Falsification / Subspace Discovery
SIMs designed to intentionally search for "missing" axes or flag artificial constraints.

| SIM Name | Purpose | Expected Result | Result File |
| :--- | :--- | :--- | :--- |
| `axis_residual_subspace_discovery_sim.py` | Projects random Lindbladian generators onto the span of Axes 0-6. High unresolvable residual indicates a missing degree of freedom. | Identify residual candidates or confirm closure. | `axis_residual_candidates.json` |
| `axis3_alt_impedance_negative_sim.py` | Swaps the Axis-3 engine split constraint with a naive loop impedance overlay to deliberately falsify incomplete physics models. | Massive correlation (1 `PASS`, N `KILL`) | `axis3_alt_impedance_results.json` |
