import numpy as np
import pytest
from hypothesis import given, settings, strategies as st

def make_psd_density(d: int, seed: int) -> np.ndarray:
    """Generate a valid trace-1 Positive Semi-Definite density matrix."""
    rng = np.random.default_rng(seed)
    A = rng.normal(size=(d, d)) + 1j * rng.normal(size=(d, d))
    rho = A @ A.conj().T
    rho = rho / np.trace(rho)
    return rho

@given(st.integers(min_value=2, max_value=16), st.integers(min_value=0, max_value=10_000))
@settings(max_examples=100)
def test_density_matrix_invariants(d, seed):
    """
    Invariant enforcement for QIT engine inputs. 
    State matrices MUST remain Hermitian, Trace=1, and Positive Smi-Definite.
    """
    rho = make_psd_density(d, seed)
    
    # Check Hermiticity
    assert np.allclose(rho, rho.conj().T, atol=1e-10), "Matrix is not Hermitian"
    
    # Check Trace = 1 (Conservation of probability)
    assert np.isclose(np.real(np.trace(rho)), 1.0, atol=1e-10), "Trace is not bounded to 1.0"
    
    # Check PSD (min eigenvalue is non-negative)
    evals = np.linalg.eigvalsh(rho)
    assert np.min(evals) >= -1e-10, "Density matrix eigenvalue went negative (violates PSD)"
