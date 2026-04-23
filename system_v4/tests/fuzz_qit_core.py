import sys
import os
import math
import numpy as np

# Graceful import of atheris
try:
    import atheris
except ImportError:
    atheris = None

# Add root folder to sys.path to resolve imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from system_v4.probes.proto_ratchet_sim_runner import ensure_valid, von_neumann_entropy
    from system_v4.probes.axis_orthogonality_suite import build_choi
except ImportError as e:
    print(f"Warning: Could not import qit core methods. {e}")
    sys.exit(0)

def generate_fuzzed_matrix(fdp, d):
    """Generate random bytes -> convert to matrix"""
    # Consume elements to form a complex matrix
    length = d * d
    real_parts = fdp.ConsumeFloatListInRange(length, -100.0, 100.0)
    imag_parts = fdp.ConsumeFloatListInRange(length, -100.0, 100.0)
    
    if len(real_parts) < length or len(imag_parts) < length:
        return None
        
    A = np.array(real_parts, dtype=np.float64) + 1j * np.array(imag_parts, dtype=np.float64)
    return A.reshape((d, d))

def test_ensure_valid(fdp):
    A = generate_fuzzed_matrix(fdp, d=4)
    if A is None: return
    
    # Make it positive semi-definite-ish
    rho = A @ A.conj().T
    
    # Introduce some arbitrary scaling
    scale = fdp.ConsumeFloatInRange(-1e4, 1e4)
    rho *= scale
    
    try:
        out = ensure_valid(rho)
        # Assert no crash/NaN
        if np.isnan(out).any() or np.isinf(out).any():
            if not (np.isnan(rho).any() or np.isinf(rho).any()):
                raise AssertionError(f"ensure_valid produced NaN/Inf from finite input: {out}")
    except np.linalg.LinAlgError:
        pass

def test_von_neumann_entropy(fdp):
    A = generate_fuzzed_matrix(fdp, d=4)
    if A is None: return
    
    # Construct a valid density matrix
    rho = A @ A.conj().T
    tr = np.real(np.trace(rho))
    if np.isnan(tr) or np.isinf(tr) or abs(tr) < 1e-12:
        return
    rho /= tr
    
    try:
        val = von_neumann_entropy(rho)
        # Assert no crash/NaN
        if math.isnan(val) or math.isinf(val):
            if not (np.isnan(rho).any() or np.isinf(rho).any()):
                raise AssertionError(f"von_neumann_entropy produced NaN/Inf from finite input: {val}")
    except np.linalg.LinAlgError:
        pass

def test_build_choi(fdp):
    A = generate_fuzzed_matrix(fdp, d=4)
    if A is None: return
    
    # Fuzzed channel application
    def fuzzed_channel(rho_in, dim):
        return A @ rho_in @ A.conj().T
        
    try:
        choi = build_choi(fuzzed_channel, 4)
        # Assert no crash/NaN
        if np.isnan(choi).any() or np.isinf(choi).any():
            if not (np.isnan(A).any() or np.isinf(A).any()):
                raise AssertionError("build_choi produced NaN/Inf from finite input.")
    except np.linalg.LinAlgError:
        pass

def TestOneInput(data):
    if not atheris:
        return
    if len(data) < 128:
        return
        
    fdp = atheris.FuzzedDataProvider(data)
    choice = fdp.ConsumeIntInRange(0, 2)
    
    if choice == 0:
        test_ensure_valid(fdp)
    elif choice == 1:
        test_von_neumann_entropy(fdp)
    elif choice == 2:
        test_build_choi(fdp)

if __name__ == "__main__":
    if atheris:
        atheris.Setup(sys.argv, TestOneInput)
        atheris.Fuzz()
    else:
        print("Atheris not installed. Skipping fuzzing (graceful skip).")
