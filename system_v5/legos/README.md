# V5 Primitive Legos

Status: clean primitive shelf, not a scout surface.

Rules:

- One file per mathematical primitive.
- Names describe the math directly.
- Each result uses `classification: lego`.
- Each result has positive checks, graveyard companions, a boundary check, tool
  manifest, and claim ceiling.
- No target-system labels, no provider prose, no writes to `system_v4/probes`.

Current legos:

| Lego | Result | Tool |
|---|---|---|
| `finite_density_matrix_carrier_trace_psd_pytorch_sympy_z3.py` | `results/finite_density_matrix_carrier_trace_psd_pytorch_sympy_z3_results.json` | pytorch, sympy, z3 |
| `unit_spinor_hopf_projection_phase_invariance_geomstats_pytorch_sympy.py` | `results/unit_spinor_hopf_projection_phase_invariance_geomstats_pytorch_sympy_results.json` | geomstats, pytorch, sympy |
| `hopf_fibration_s3_s2_spinor_network_peps3d_entropy_pytorch_jax_quimb_sympy_z3.py` | `results/hopf_fibration_s3_s2_spinor_network_peps3d_entropy_pytorch_jax_quimb_sympy_z3_results.json` | pytorch, jax, quimb, cotengra, opt_einsum, sympy, z3, cvc5, rustworkx, xgi, toponetx, gudhi |
| `weyl_spinor_chirality_hamiltonian_sign_expectation_clifford_pytorch_z3.py` | `results/weyl_spinor_chirality_hamiltonian_sign_expectation_clifford_pytorch_z3_results.json` | clifford, pytorch, z3 |
| `pauli_clifford_commutator_representation_gap_clifford_sympy_z3.py` | `results/pauli_clifford_commutator_representation_gap_clifford_sympy_z3_results.json` | clifford, sympy, z3 |
| `density_operator_cptp_amplitude_damping_trace_psd_pytorch_sympy_z3.py` | `results/density_operator_cptp_amplitude_damping_trace_psd_pytorch_sympy_z3_results.json` | pytorch, sympy, z3 |
| `finite_simplicial_cycle_boundary_homology_gudhi_toponetx_xgi.py` | `results/finite_simplicial_cycle_boundary_homology_gudhi_toponetx_xgi_results.json` | gudhi, toponetx, xgi |
| `two_point_spectral_triple_dirac_commutator_distance_pytorch_sympy_z3.py` | `results/two_point_spectral_triple_dirac_commutator_distance_pytorch_sympy_z3_results.json` | pytorch, sympy, z3 |
| `spectral_entropy_family_density_state_pytorch_sympy_z3.py` | `results/spectral_entropy_family_density_state_pytorch_sympy_z3_results.json` | pytorch, sympy, z3 |
| `bipartite_cut_mutual_conditional_coherent_information_pytorch_sympy_z3.py` | `results/bipartite_cut_mutual_conditional_coherent_information_pytorch_sympy_z3_results.json` | pytorch, sympy, z3 |
| `finite_support_topology_entropy_witness_pyg_gudhi_xgi_z3.py` | `results/finite_support_topology_entropy_witness_pyg_gudhi_xgi_z3_results.json` | pyg, gudhi, xgi, pytorch, z3 |
| `signed_conditional_and_coherent_information_negative_entropy_pytorch_sympy_z3.py` | `results/signed_conditional_and_coherent_information_negative_entropy_pytorch_sympy_z3_results.json` | pytorch, opt_einsum, sympy, z3 |
| `coherent_information_parameter_gradient_two_qubit_mixture_pytorch_autograd_z3.py` | `results/coherent_information_parameter_gradient_two_qubit_mixture_pytorch_autograd_z3_results.json` | pytorch, opt_einsum, z3 |

Baseline-support files:

| File | Result | Reason |
|---|---|---|
| `density_matrix_trace_positive_semidefinite.py` | `results/density_matrix_trace_positive_semidefinite_results.json` | NumPy-only finite linear-algebra baseline; not a load-bearing nonclassical lego |

Validate:

`/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/legos/validate_lego_results.py`
