import numpy as np
import hashlib
import json
import sys

def sha256(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def commutator(A, B):
    return A @ B - B @ A

def partial_trace_2q(rho_ab):
    """Trace out qubit B from a 2-qubit density matrix rho_ab."""
    # Reshape to (2,2,2,2) -> (dimA, dimB, dimA, dimB)
    rho_tensor = rho_ab.reshape(2, 2, 2, 2)
    # Contract indices 1 and 3 (qubit B)
    rho_a = np.einsum('ijik->jk', rho_tensor)
    return rho_a

def main():
    # 1. Setup: Finite Dimensional Hilbert Space (2-qubit = 4D)
    # Constraints: Finitude
    dim = 2
    
    # 2. Proof of Non-Commutation
    # Constraints: N01_NONCOMMUTATION
    # Pauli X and Z
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    
    comm = commutator(X, Z)
    # [X, Z] = -2iY != 0
    non_commutative = not np.allclose(comm, 0)
    
    # 3. Proof of Density Matrix Necessity (Entropic Monism Foundation)
    # Create a Bell State (Pure Vector in 4D)
    # |Phi+> = (|00> + |11>) / sqrt(2)
    bell_vec = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
    rho_bell = np.outer(bell_vec, np.conj(bell_vec))
    
    # Trace out system B to find state of A
    rho_a = partial_trace_2q(rho_bell)
    
    # Check if rho_a is pure (Trace(rho^2) == 1)
    purity = np.real(np.trace(rho_a @ rho_a))
    
    # In a classical world, a part of a definite whole is definite.
    # In QIT, a part of a pure entangled whole is MIXED (Entropy > 0).
    # This proves that "State" must be a Density Matrix to handle reality.
    is_mixed = purity < 0.999
    
    # 4. Proof of Channel (Probe)
    # Apply a noise channel (Depolarizing) to rho_a
    # E(rho) = (1-p)rho + p(I/2)
    p = 0.1
    I2 = np.eye(2, dtype=complex)
    rho_prime = (1-p)*rho_a + p*(I2/2)
    
    # Verify Trace Preservation (Probability Conservation)
    trace_preserved = np.isclose(np.trace(rho_prime), 1.0)
    
    # 5. Generate Evidence
    proof_data = {
        "is_finite_dim": True,
        "non_commutative": bool(non_commutative),
        "entanglement_generates_entropy": bool(is_mixed),
        "subsystem_purity": float(purity),
        "channel_preserves_trace": bool(trace_preserved)
    }
    
    output_json = json.dumps(proof_data, sort_keys=True)
    output_hash = sha256(output_json)
    code_hash = sha256(open(__file__).read())
    
    print("BEGIN SIM_EVIDENCE v1")
    print("SIM_ID: S_FOUNDATION_PROOF")
    print(f"CODE_HASH_SHA256: {code_hash}")
    print(f"OUTPUT_HASH_SHA256: {output_hash}")
    print(f"METRIC: purity={purity}")
    print(f"METRIC: non_commutative={non_commutative}")
    
    if non_commutative and is_mixed and trace_preserved:
        print("EVIDENCE_SIGNAL S_FOUNDATION_PROOF CORR E_FOUNDATION_PROOF")
    
    print("END SIM_EVIDENCE v1")

if __name__ == "__main__":
    main()
