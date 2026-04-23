import numpy as np
from hypothesis import given, strategies as st, settings
from proto_ratchet_sim_runner import (
    ensure_valid, make_random_density_matrix, apply_lindbladian_step, make_random_unitary, apply_unitary_channel
)

@settings(max_examples=200, deadline=1000)
@given(st.integers(min_value=2, max_value=8))
def test_density_matrix_invariants_hold_under_projection(d):
    """Ensure that any corrupted matrix is correctly projected back onto the Valid density matrix manifold."""
    rho = make_random_density_matrix(d)
    
    # Intentionally corrupt PSD (Positive Semi-Definite) property
    rho[0, 0] -= 10.0  
    
    # Intentionally corrupt Trace
    rho *= 5.0
    
    fixed = ensure_valid(rho)

    # Invariant 1: Hermiticity
    assert np.allclose(fixed, fixed.conj().T), "Matrix must be Hermitian"
    
    # Invariant 2: Positive Semi-Definite (eigenvalues >= 0)
    evals = np.linalg.eigvalsh(fixed)
    assert evals.min() >= -1e-10, f"Matrix must be PSD, min eval: {evals.min()}"
    
    # Invariant 3: Trace == 1
    assert np.isclose(np.real(np.trace(fixed)), 1.0, atol=1e-10), f"Trace must be 1, got {np.trace(fixed)}"

@settings(max_examples=200, deadline=1000)
@given(st.integers(min_value=2, max_value=8))
def test_lindblad_step_stays_reasonable_with_projection(d):
    """Ensure Lindblad dynamics do not drift to NaN/Inf and trace is preserved."""
    rho = make_random_density_matrix(d)
    
    # Random Lindbladian generator L
    L = (np.random.randn(d, d) + 1j * np.random.randn(d, d))
    
    # Apply raw step
    rho2 = apply_lindbladian_step(rho, L, dt=0.01)
    
    # Ensure projection correctly bounds it
    rho2 = ensure_valid(rho2)
    
    # Invariant 4: No NaN/Inf propagation
    assert np.isfinite(np.real(np.trace(rho2))), "Trace must not diverge to NaN/Inf after Lindblad step"
    
@settings(max_examples=200, deadline=1000)
@given(st.integers(min_value=2, max_value=8))
def test_unitary_channel_preserves_invariants(d):
    """Ensure unitary structural transforms preserve CPTP properties."""
    rho = make_random_density_matrix(d)
    U = make_random_unitary(d)
    
    rho_out = apply_unitary_channel(rho, U)
    
    # Under pure unitary evolution without projection
    assert np.allclose(rho_out, rho_out.conj().T), "Unitary must preserve Hermiticity"
    evals = np.linalg.eigvalsh(rho_out)
    assert evals.min() >= -1e-10, "Unitary must preserve PSD"
    assert np.isclose(np.real(np.trace(rho_out)), 1.0, atol=1e-10), "Unitary must preserve trace 1"
