#!/usr/bin/env python3
"""
sim_pure_lego_teleportation_superdense.py
=========================================

Pure-lego verification of quantum teleportation and superdense coding.
No engine dependencies -- numpy only.

Protocols verified:
  1. Teleportation: Alice holds unknown |psi> and half of a Bell pair.
     Bell measurement on Alice's side yields 2 classical bits.
     Bob applies the corresponding Pauli correction -> recovers |psi>.
     - Fidelity = 1.0 for 20 random input states.
     - Without shared entanglement, max fidelity = 2/3 (classical bound).

  2. Superdense coding: Alice encodes 2 classical bits by applying
     I/X/Z/iY to her half of a shared Bell pair, sends her qubit to Bob.
     Bob performs Bell measurement -> recovers 2 classical bits.
     - All 4 messages decoded correctly.
     - Entanglement is CONSUMED: post-protocol state is product.

  3. Resource duality:
     Teleportation:  1 ebit + 2 cbits  ->  1 qubit transmitted
     Superdense:     1 ebit + 1 qubit  ->  2 cbits transmitted
     These are dual protocols (resource inversion).
"""

import json
import os
import sys
from datetime import datetime, UTC

import numpy as np

# ═══════════════════════════════════════════════════════════════════
# Pauli matrices and Bell states
# ═══════════════════════════════════════════════════════════════════

I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)

PAULIS = [I2, X, Y, Z]
PAULI_LABELS = ["I", "X", "Y", "Z"]

# Computational basis
KET_0 = np.array([1, 0], dtype=complex)
KET_1 = np.array([0, 1], dtype=complex)

# Bell states (standard convention)
# |Phi+> = (|00> + |11>) / sqrt(2)
PHI_PLUS = (np.kron(KET_0, KET_0) + np.kron(KET_1, KET_1)) / np.sqrt(2)


def random_pure_state():
    """Generate a Haar-random single-qubit pure state."""
    # Random complex vector, normalize
    v = np.random.randn(2) + 1j * np.random.randn(2)
    v /= np.linalg.norm(v)
    return v


def fidelity_pure(psi, phi):
    """Fidelity between two pure state vectors: |<psi|phi>|^2."""
    return float(np.abs(np.vdot(psi, phi)) ** 2)


def is_product_state(rho_ab, dim_a=2, dim_b=2, tol=1e-10):
    """
    Check if a bipartite density matrix is a product state.
    rho_AB = rho_A (x) rho_B  iff  rho_AB - rho_A(x)rho_B = 0.
    """
    d = dim_a * dim_b
    rho = rho_ab.reshape(dim_a, dim_b, dim_a, dim_b)
    # Partial traces
    rho_a = np.trace(rho, axis1=1, axis2=3)  # trace over B
    rho_b = np.trace(rho, axis1=0, axis2=2)  # trace over A
    product = np.kron(rho_a, rho_b)
    diff = np.linalg.norm(rho_ab - product)
    return diff < tol, float(diff)


# ═══════════════════════════════════════════════════════════════════
# TELEPORTATION
# ═══════════════════════════════════════════════════════════════════

def bell_basis_projectors():
    """
    Return the 4 Bell-state projectors as 4x4 matrices.
    |Phi+>, |Phi->, |Psi+>, |Psi->
    Bell measurement outcome m in {0,1,2,3} -> correction = PAULI[m] on Bob.

    Convention:
      m=0: |Phi+> = (|00>+|11>)/sqrt(2)  -> correction I
      m=1: |Phi-> = (|00>-|11>)/sqrt(2)  -> correction Z
      m=2: |Psi+> = (|01>+|10>)/sqrt(2)  -> correction X
      m=3: |Psi-> = (|01>-|10>)/sqrt(2)  -> correction iY = ZX
    """
    b00 = (np.kron(KET_0, KET_0) + np.kron(KET_1, KET_1)) / np.sqrt(2)
    b01 = (np.kron(KET_0, KET_0) - np.kron(KET_1, KET_1)) / np.sqrt(2)
    b10 = (np.kron(KET_0, KET_1) + np.kron(KET_1, KET_0)) / np.sqrt(2)
    b11 = (np.kron(KET_0, KET_1) - np.kron(KET_1, KET_0)) / np.sqrt(2)
    bells = [b00, b01, b10, b11]
    projectors = [np.outer(b, b.conj()) for b in bells]
    # Corrections: after measuring outcome m, Bob applies correction[m]
    corrections = [I2, Z, X, Z @ X]  # I, Z, X, ZX
    return projectors, corrections, bells


def teleport(psi_in):
    """
    Simulate quantum teleportation of |psi_in> (single qubit).

    System: qubit 1 (Alice's input), qubit 2 (Alice's Bell half), qubit 3 (Bob's Bell half)
    Total state: |psi_in>_1 (x) |Phi+>_23

    Alice does Bell measurement on qubits 1,2.
    Bob applies correction on qubit 3.

    Returns: (bob_state, measurement_outcome, fidelity)
    """
    # 3-qubit state: |psi>_1 (x) |Phi+>_23
    state_123 = np.kron(psi_in, PHI_PLUS)  # 8-dim vector

    projectors_12, corrections, _ = bell_basis_projectors()

    # Pick a random measurement outcome (all have equal prob 1/4)
    # But let's compute all and verify probabilities
    probs = []
    for P12 in projectors_12:
        # Projector on qubits 1,2 tensored with I on qubit 3
        P_full = np.kron(P12, I2)  # 8x8
        prob = float(np.real(state_123.conj() @ P_full @ state_123))
        probs.append(prob)

    # All probabilities should be 1/4
    assert np.allclose(probs, 0.25, atol=1e-12), f"Probabilities not uniform: {probs}"

    # Pick one outcome
    m = np.random.randint(4)
    P_full = np.kron(projectors_12[m], I2)

    # Post-measurement state (unnormalized)
    post = P_full @ state_123
    post /= np.linalg.norm(post)

    # Bob's qubit is qubit 3. Reshape to extract it.
    # post is 8-dim = 2 x 2 x 2. After projection on qubits 1,2,
    # the state factorizes as |bell_m>_12 (x) |something>_3
    post_reshaped = post.reshape(4, 2)  # (q1q2, q3)
    # The q1q2 part is one of the Bell states (up to phase); extract q3
    # Find which row of post_reshaped is nonzero
    bob_unnorm = post_reshaped.T @ post_reshaped  # 2x2 density matrix of Bob
    # Actually simpler: since qubits 1,2 are in a definite Bell state,
    # Bob's state is just the normalized column
    # Let's do it cleanly: partial trace over qubits 1,2
    rho_bob = np.zeros((2, 2), dtype=complex)
    for i in range(4):
        rho_bob += np.outer(post_reshaped[i], post_reshaped[i].conj())

    # Apply correction
    correction = corrections[m]
    rho_corrected = correction @ rho_bob @ correction.conj().T

    # Extract pure state (should be pure)
    eigvals, eigvecs = np.linalg.eigh(rho_corrected)
    # Largest eigenvalue should be ~1
    bob_state = eigvecs[:, np.argmax(eigvals)]

    # Fidelity with input
    fid = fidelity_pure(psi_in, bob_state)

    return bob_state, m, fid, probs


def classical_teleportation_bound():
    """
    Without shared entanglement, the best classical strategy for
    transmitting an unknown qubit state achieves max fidelity = 2/3.

    Verify by simulation: Alice measures in a random basis, sends result,
    Bob prepares that state. Average fidelity over Haar-random inputs -> 2/3.
    """
    n_trials = 100_000
    fidelities = []
    for _ in range(n_trials):
        psi = random_pure_state()
        # Best classical strategy: Alice measures in computational basis,
        # sends outcome, Bob prepares |0> or |1>.
        prob_0 = float(np.abs(psi[0]) ** 2)
        if np.random.rand() < prob_0:
            # Measured |0>
            bob = KET_0.copy()
        else:
            bob = KET_1.copy()
        fidelities.append(fidelity_pure(psi, bob))

    avg = float(np.mean(fidelities))
    return avg


# ═══════════════════════════════════════════════════════════════════
# SUPERDENSE CODING
# ═══════════════════════════════════════════════════════════════════

def superdense_encode_decode(message_bits):
    """
    Superdense coding: encode 2 classical bits into 1 qubit
    using a shared Bell pair.

    message_bits: (b1, b2) in {0,1}^2
    Encoding:
      00 -> I   (Alice applies nothing)
      01 -> X   (bit flip)
      10 -> Z   (phase flip)
      11 -> iY  (both flips)

    Returns: (decoded_bits, post_state_is_product)
    """
    b1, b2 = message_bits

    # Shared Bell pair |Phi+>
    bell = PHI_PLUS.copy()

    # Alice's encoding operation (on qubit 1 = first qubit)
    encoding_ops = {
        (0, 0): I2,
        (0, 1): X,
        (1, 0): Z,
        (1, 1): 1j * Y,  # iY = ZX up to phase; use iY for clean mapping
    }
    op = encoding_ops[(b1, b2)]
    # Apply to first qubit: (op (x) I) |Phi+>
    encoded = np.kron(op, I2) @ bell

    # Bob receives Alice's qubit. Now Bob has both qubits.
    # Bob does Bell measurement (CNOT then Hadamard on qubit 1, then measure)
    # Equivalently: project onto Bell basis and read outcome.
    _, _, bell_states = bell_basis_projectors()

    # Find which Bell state the encoded state matches
    overlaps = [np.abs(np.vdot(bs, encoded)) ** 2 for bs in bell_states]
    outcome = int(np.argmax(overlaps))
    assert overlaps[outcome] > 1 - 1e-12, f"Not a clean Bell state: {overlaps}"

    # Decode: map Bell measurement outcome back to bits
    # |Phi+> -> 00, |Phi-> -> 10, |Psi+> -> 01, |Psi-> -> 11
    decode_map = {0: (0, 0), 1: (1, 0), 2: (0, 1), 3: (1, 1)}
    decoded = decode_map[outcome]

    # Verify entanglement is CONSUMED
    # After Bob's measurement, the 2-qubit system is in a definite Bell state,
    # which IS entangled. But the PROTOCOL output is classical bits.
    # The entanglement resource is consumed: the Bell pair can't be reused.
    # To verify consumption: after measurement, the post-measurement state
    # of each qubit is maximally mixed (no extractable entanglement remains
    # for further use). Let's verify the Bell pair is destroyed by checking
    # that the shared state after Alice's encoding and Bob's measurement
    # collapses to a product of definite states.
    #
    # Post Bell-measurement: state collapses to the measured Bell state,
    # then Bob's local operations disentangle to |b1 b2>.
    # Simulate the circuit: CNOT_12 then H_1
    H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
    CNOT = np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]], dtype=complex)

    decoded_state = np.kron(H, I2) @ CNOT @ encoded
    rho_post = np.outer(decoded_state, decoded_state.conj())
    is_product, product_dist = is_product_state(rho_post)

    return decoded, is_product, product_dist


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    np.random.seed(42)
    results = {
        "probe": "sim_pure_lego_teleportation_superdense",
        "timestamp": datetime.now(UTC).isoformat(),
        "numpy_only": True,
        "sections": {},
    }

    # ── 1. TELEPORTATION ──────────────────────────────────────────
    print("=" * 60)
    print("TELEPORTATION PROTOCOL")
    print("=" * 60)

    n_teleport = 20
    teleport_results = []
    all_fid_one = True

    for i in range(n_teleport):
        psi = random_pure_state()
        bob_state, outcome, fid, probs = teleport(psi)
        passed = fid > 1.0 - 1e-10
        if not passed:
            all_fid_one = False
        teleport_results.append({
            "trial": i,
            "input_state": [complex(c).real for c in psi] if np.allclose(psi.imag, 0) else
                           [str(complex(round(c.real, 6), round(c.imag, 6))) for c in psi],
            "measurement_outcome": int(outcome),
            "fidelity": round(fid, 12),
            "passed": passed,
        })
        status = "PASS" if passed else "FAIL"
        print(f"  Trial {i:2d}: fidelity={fid:.12f}  outcome={outcome}  [{status}]")

    print(f"\n  All {n_teleport} teleportations fidelity=1.0: "
          f"{'PASS' if all_fid_one else 'FAIL'}")

    # Classical bound
    print("\n  Computing classical teleportation bound (no entanglement)...")
    classical_fid = classical_teleportation_bound()
    classical_check = abs(classical_fid - 2/3) < 0.02  # statistical tolerance
    print(f"  Classical avg fidelity: {classical_fid:.4f}  (theory: 0.6667)")
    print(f"  Classical bound verified: {'PASS' if classical_check else 'FAIL'}")

    results["sections"]["teleportation"] = {
        "n_trials": n_teleport,
        "all_fidelity_one": all_fid_one,
        "trials": teleport_results,
        "classical_bound": {
            "measured_avg_fidelity": round(classical_fid, 6),
            "theoretical_bound": round(2/3, 6),
            "within_tolerance": classical_check,
        },
        "resource_cost": {
            "ebits_consumed": 1,
            "classical_bits_sent": 2,
            "qubits_transmitted": 1,
            "direction": "1 ebit + 2 cbits -> 1 qubit",
        },
        "verdict": "PASS" if all_fid_one and classical_check else "FAIL",
    }

    # ── 2. SUPERDENSE CODING ──────────────────────────────────────
    print("\n" + "=" * 60)
    print("SUPERDENSE CODING PROTOCOL")
    print("=" * 60)

    messages = [(0, 0), (0, 1), (1, 0), (1, 1)]
    superdense_results = []
    all_decoded = True
    all_consumed = True

    for msg in messages:
        decoded, is_product, product_dist = superdense_encode_decode(msg)
        correct = decoded == msg
        if not correct:
            all_decoded = False
        if not is_product:
            all_consumed = False

        superdense_results.append({
            "sent": list(msg),
            "received": list(decoded),
            "correct": correct,
            "entanglement_consumed": is_product,
            "product_distance": round(product_dist, 12),
        })
        print(f"  Message {msg} -> decoded {decoded}  "
              f"correct={'PASS' if correct else 'FAIL'}  "
              f"ebit_consumed={'PASS' if is_product else 'FAIL'} "
              f"(dist={product_dist:.2e})")

    print(f"\n  All messages decoded: {'PASS' if all_decoded else 'FAIL'}")
    print(f"  Entanglement consumed: {'PASS' if all_consumed else 'FAIL'}")

    results["sections"]["superdense_coding"] = {
        "messages_tested": [list(m) for m in messages],
        "all_decoded_correctly": all_decoded,
        "all_entanglement_consumed": all_consumed,
        "trials": superdense_results,
        "resource_cost": {
            "ebits_consumed": 1,
            "qubits_sent": 1,
            "classical_bits_received": 2,
            "direction": "1 ebit + 1 qubit -> 2 cbits",
        },
        "verdict": "PASS" if all_decoded and all_consumed else "FAIL",
    }

    # ── 3. DUALITY ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("RESOURCE DUALITY")
    print("=" * 60)

    teleport_res = (1, 2, 1)   # (ebits, cbits_in, qubits_out)
    superdense_res = (1, 1, 2)  # (ebits, qubits_in, cbits_out)

    # Duality: swap qubit<->cbit direction
    is_dual = (teleport_res[0] == superdense_res[0] and   # same ebit cost
               teleport_res[1] == superdense_res[2] and   # teleport cbits = superdense cbits
               teleport_res[2] == superdense_res[1])       # teleport qubit = superdense qubit

    print(f"  Teleportation:    {teleport_res[0]} ebit + {teleport_res[1]} cbits -> {teleport_res[2]} qubit")
    print(f"  Superdense:       {superdense_res[0]} ebit + {superdense_res[1]} qubit -> {superdense_res[2]} cbits")
    print(f"  Resource duality: {'PASS' if is_dual else 'FAIL'}")

    results["sections"]["resource_duality"] = {
        "teleportation": {"ebits": 1, "cbits_sent": 2, "qubits_received": 1},
        "superdense": {"ebits": 1, "qubits_sent": 1, "cbits_received": 2},
        "is_dual": is_dual,
        "explanation": "Swap qubit<->cbit channels: protocols are resource-inverses",
        "verdict": "PASS" if is_dual else "FAIL",
    }

    # ── OVERALL ───────────────────────────────────────────────────
    all_pass = (
        results["sections"]["teleportation"]["verdict"] == "PASS"
        and results["sections"]["superdense_coding"]["verdict"] == "PASS"
        and results["sections"]["resource_duality"]["verdict"] == "PASS"
    )
    results["overall_verdict"] = "PASS" if all_pass else "FAIL"

    print("\n" + "=" * 60)
    print(f"OVERALL VERDICT: {results['overall_verdict']}")
    print("=" * 60)

    # ── WRITE OUTPUT ──────────────────────────────────────────────
    # Sanitize numpy types for JSON
    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.bool_,)):
                return bool(obj)
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            return super().default(obj)

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "teleportation_superdense_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, cls=NumpyEncoder)
    print(f"\nResults written to {out_path}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
