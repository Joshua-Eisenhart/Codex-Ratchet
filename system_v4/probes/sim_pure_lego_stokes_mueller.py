"""
Pure Lego: Stokes Parameters & Mueller Matrix Formalism
========================================================
No engine. numpy only.

Stokes vector S = (S0, S1, S2, S3) with S0=1 (normalized),
(S1, S2, S3) = Bloch vector.

Mueller matrix M: 4x4 real matrix mapping Stokes -> Stokes.
Every single-qubit quantum channel has a Mueller representation.

Channels built:
  - Z-rotation, X-rotation
  - Z-dephasing, X-dephasing
  - Depolarizing, Amplitude damping

Verifications:
  - M maps valid Stokes vectors to valid Stokes vectors
  - Mueller == real representation of density-matrix + Pauli algebra
  - Sufficiency analysis: all single-qubit channels; failure for multi-qubit
"""

import numpy as np
import json
import os
from datetime import datetime, UTC
classification = "classical_baseline"  # auto-backfill

# ---------------------------------------------------------------------------
# Pauli matrices
# ---------------------------------------------------------------------------
I2 = np.eye(2, dtype=complex)
sigma_x = np.array([[0, 1], [1, 0]], dtype=complex)
sigma_y = np.array([[0, -1j], [1j, 0]], dtype=complex)
sigma_z = np.array([[1, 0], [0, -1]], dtype=complex)
PAULIS = [I2, sigma_x, sigma_y, sigma_z]


# ---------------------------------------------------------------------------
# Stokes <-> density matrix conversions
# ---------------------------------------------------------------------------
def density_to_stokes(rho):
    """Convert 2x2 density matrix to Stokes vector (S0, S1, S2, S3)."""
    s = np.array([np.real(np.trace(rho @ P)) for P in PAULIS])
    return s


def stokes_to_density(s):
    """Convert Stokes vector to 2x2 density matrix: rho = (1/2) sum_i s_i sigma_i."""
    return 0.5 * sum(s[i] * PAULIS[i] for i in range(4))


def is_valid_stokes(s, tol=1e-10):
    """Check physicality: S0 >= 0, |bloch| <= S0."""
    bloch_norm = np.linalg.norm(s[1:])
    return s[0] >= -tol and bloch_norm <= s[0] + tol


# ---------------------------------------------------------------------------
# Mueller matrix from Kraus operators
# ---------------------------------------------------------------------------
def kraus_to_mueller(kraus_ops):
    """
    Compute 4x4 real Mueller matrix from a list of Kraus operators.

    M_ij = (1/2) Tr[ sigma_i * sum_k ( K_k sigma_j K_k^dag ) ]

    This IS the real representation of the channel: density matrix algebra
    with Paulis, but all complex phases cancel in the Stokes picture.
    """
    M = np.zeros((4, 4))
    for i in range(4):
        for j in range(4):
            val = 0.0
            for K in kraus_ops:
                val += np.real(np.trace(PAULIS[i] @ K @ PAULIS[j] @ K.conj().T))
            M[i, j] = val / 2.0
    return M


# ---------------------------------------------------------------------------
# Channel definitions (Kraus form)
# ---------------------------------------------------------------------------
def z_rotation_kraus(theta):
    """R_z(theta) = exp(-i theta/2 sigma_z)."""
    U = np.array([
        [np.exp(-1j * theta / 2), 0],
        [0, np.exp(1j * theta / 2)]
    ], dtype=complex)
    return [U]


def x_rotation_kraus(theta):
    """R_x(theta) = exp(-i theta/2 sigma_x)."""
    c, s = np.cos(theta / 2), np.sin(theta / 2)
    U = np.array([
        [c, -1j * s],
        [-1j * s, c]
    ], dtype=complex)
    return [U]


def z_dephasing_kraus(p):
    """Z-dephasing: Kraus ops K0 = sqrt(1-p/2) I, K1 = sqrt(p/2) Z."""
    K0 = np.sqrt(1 - p / 2) * I2
    K1 = np.sqrt(p / 2) * sigma_z
    return [K0, K1]


def x_dephasing_kraus(p):
    """X-dephasing: Kraus ops K0 = sqrt(1-p/2) I, K1 = sqrt(p/2) X."""
    K0 = np.sqrt(1 - p / 2) * I2
    K1 = np.sqrt(p / 2) * sigma_x
    return [K0, K1]


def depolarizing_kraus(p):
    """Depolarizing channel: rho -> (1-p) rho + (p/3)(X rho X + Y rho Y + Z rho Z)."""
    K0 = np.sqrt(1 - 3 * p / 4) * I2
    K1 = np.sqrt(p / 4) * sigma_x
    K2 = np.sqrt(p / 4) * sigma_y
    K3 = np.sqrt(p / 4) * sigma_z
    return [K0, K1, K2, K3]


def amplitude_damping_kraus(gamma):
    """Amplitude damping: |1> decays to |0> with probability gamma."""
    K0 = np.array([
        [1, 0],
        [0, np.sqrt(1 - gamma)]
    ], dtype=complex)
    K1 = np.array([
        [0, np.sqrt(gamma)],
        [0, 0]
    ], dtype=complex)
    return [K0, K1]


# ---------------------------------------------------------------------------
# Verification: Mueller maps valid Stokes to valid Stokes
# ---------------------------------------------------------------------------
def verify_mueller_physicality(M, name, n_samples=5000):
    """
    Sample random valid Stokes vectors, apply M, check output is valid.
    Returns (pass_count, fail_count, failures_list).
    """
    fails = []
    for _ in range(n_samples):
        # Random Stokes: S0=1, Bloch vector inside unit ball
        direction = np.random.randn(3)
        norm = np.linalg.norm(direction)
        if norm > 0:
            direction /= norm
        r = np.random.uniform(0, 1) ** (1.0 / 3.0)  # uniform in ball
        s_in = np.array([1.0, r * direction[0], r * direction[1], r * direction[2]])

        s_out = M @ s_in

        if not is_valid_stokes(s_out, tol=1e-8):
            fails.append({
                "s_in": s_in.tolist(),
                "s_out": s_out.tolist(),
                "bloch_norm_out": float(np.linalg.norm(s_out[1:])),
                "s0_out": float(s_out[0]),
            })

    return n_samples - len(fails), len(fails), fails


# ---------------------------------------------------------------------------
# Verification: Mueller output matches direct density-matrix channel
# ---------------------------------------------------------------------------
def verify_mueller_vs_density(M, kraus_ops, name, n_samples=500):
    """
    For random input states, compare:
      (a) Stokes-domain: s_out = M @ s_in
      (b) Density-domain: rho_out = sum K rho K^dag, then convert to Stokes
    Max discrepancy should be ~machine epsilon.
    """
    max_err = 0.0
    for _ in range(n_samples):
        direction = np.random.randn(3)
        norm = np.linalg.norm(direction)
        if norm > 0:
            direction /= norm
        r = np.random.uniform(0, 1) ** (1.0 / 3.0)
        s_in = np.array([1.0, r * direction[0], r * direction[1], r * direction[2]])

        # Mueller path
        s_mueller = M @ s_in

        # Density matrix path
        rho_in = stokes_to_density(s_in)
        rho_out = sum(K @ rho_in @ K.conj().T for K in kraus_ops)
        s_density = density_to_stokes(rho_out)

        err = np.max(np.abs(s_mueller - s_density))
        max_err = max(max_err, err)

    return max_err


# ---------------------------------------------------------------------------
# Main simulation
# ---------------------------------------------------------------------------
def run_stokes_mueller_sim():
    print("\n" + "=" * 70)
    print("PURE LEGO: STOKES PARAMETERS & MUELLER MATRIX FORMALISM")
    print("=" * 70)

    np.random.seed(42)

    # Channel catalog: (name, kraus_factory, parameter, param_label)
    channels = [
        ("Z-rotation (pi/4)",        z_rotation_kraus,      np.pi / 4,  "theta"),
        ("Z-rotation (pi/2)",        z_rotation_kraus,      np.pi / 2,  "theta"),
        ("X-rotation (pi/3)",        x_rotation_kraus,      np.pi / 3,  "theta"),
        ("Z-dephasing (p=0.3)",      z_dephasing_kraus,     0.3,        "p"),
        ("Z-dephasing (p=1.0)",      z_dephasing_kraus,     1.0,        "p"),
        ("X-dephasing (p=0.5)",      x_dephasing_kraus,     0.5,        "p"),
        ("Depolarizing (p=0.2)",     depolarizing_kraus,    0.2,        "p"),
        ("Depolarizing (p=1.0)",     depolarizing_kraus,    1.0,        "p"),
        ("Amplitude damping (g=0.1)", amplitude_damping_kraus, 0.1,     "gamma"),
        ("Amplitude damping (g=0.5)", amplitude_damping_kraus, 0.5,     "gamma"),
        ("Amplitude damping (g=1.0)", amplitude_damping_kraus, 1.0,     "gamma"),
    ]

    results = []
    all_pass = True

    for name, factory, param, plabel in channels:
        print(f"\n--- {name} ({plabel}={param}) ---")

        kraus = factory(param)
        M = kraus_to_mueller(kraus)

        print(f"  Mueller matrix M:\n{np.array2string(M, precision=6, suppress_small=True)}")

        # Physicality check
        n_pass, n_fail, failures = verify_mueller_physicality(M, name)
        phys_ok = n_fail == 0
        print(f"  Physicality: {n_pass}/{n_pass + n_fail} passed  {'PASS' if phys_ok else 'FAIL'}")

        # Equivalence check
        max_err = verify_mueller_vs_density(M, kraus, name)
        equiv_ok = max_err < 1e-12
        print(f"  Mueller vs density-matrix max error: {max_err:.2e}  {'PASS' if equiv_ok else 'FAIL'}")

        # Trace preservation: M[0,0] should be 1 for trace-preserving channels
        tp = abs(M[0, 0] - 1.0) < 1e-10 and all(abs(M[0, j]) < 1e-10 for j in range(1, 4))
        print(f"  Trace-preserving (M[0,:] = [1,0,0,0]): {'PASS' if tp else 'FAIL'}  actual={M[0,:].tolist()}")

        # Unital check: M @ [1,0,0,0]^T = [1,0,0,0]^T ?
        s_max_mixed = np.array([1, 0, 0, 0], dtype=float)
        s_out_mm = M @ s_max_mixed
        unital = np.allclose(s_out_mm, s_max_mixed, atol=1e-10)
        print(f"  Unital (preserves max-mixed): {'YES' if unital else 'NO'}  M|I/2> = {s_out_mm.tolist()}")

        # For unitaries: check M is orthogonal in the 3x3 Bloch block
        bloch_block = M[1:, 1:]
        is_unitary_channel = len(kraus) == 1
        ortho = None
        if is_unitary_channel:
            orth_check = bloch_block @ bloch_block.T
            ortho = np.allclose(orth_check, np.eye(3), atol=1e-10)
            print(f"  Bloch block orthogonal (unitary channel): {'PASS' if ortho else 'FAIL'}")

        channel_pass = phys_ok and equiv_ok
        if not channel_pass:
            all_pass = False

        results.append({
            "channel": name,
            "parameter_label": plabel,
            "parameter_value": float(param),
            "mueller_matrix": M.tolist(),
            "physicality_pass": bool(phys_ok),
            "physicality_samples": int(n_pass + n_fail),
            "physicality_failures": int(n_fail),
            "equivalence_max_error": float(max_err),
            "equivalence_pass": bool(equiv_ok),
            "trace_preserving": bool(tp),
            "unital": bool(unital),
            "bloch_block_orthogonal": bool(ortho) if ortho is not None else None,
            "overall_pass": bool(channel_pass),
        })

    # ------------------------------------------------------------------
    # Sufficiency analysis
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("SUFFICIENCY ANALYSIS")
    print("=" * 70)

    sufficiency = {
        "single_qubit": {
            "mueller_sufficient": True,
            "reason": (
                "Every single-qubit quantum channel (CPTP map on C^2) has a "
                "unique 4x4 real Mueller matrix. The Stokes-Mueller picture is "
                "isomorphic to the density-matrix+Pauli picture for d=2. "
                "No information is lost: the 4x4 real entries encode exactly "
                "the same 12 real parameters as the Choi matrix (trace-preserving "
                "fixes row 0 to [1,0,0,0], leaving 12 free)."
            ),
        },
        "multi_qubit": {
            "mueller_sufficient": False,
            "reason": (
                "For n qubits the generalized Stokes vector has 4^n components "
                "and the Mueller matrix is 4^n x 4^n. While formally possible, "
                "this loses the tensor-product structure that makes multi-qubit "
                "physics tractable. Entangling channels (CNOT, etc.) cannot be "
                "written as M_A (x) M_B; the full 4^n x 4^n Mueller is needed. "
                "For n>=2 the Choi/Kraus/Stinespring representations are strictly "
                "more practical. Mueller formalism remains a single-qubit tool."
            ),
        },
        "key_insight": (
            "Mueller matrices ARE the real representation of what density matrices "
            "and Pauli algebra do with complex numbers. Every complex phase in the "
            "channel cancels when projected onto the Hermitian Pauli basis, leaving "
            "a purely real 4x4 matrix. This is not an approximation -- it is exact "
            "for single-qubit channels. The Bloch sphere IS the Mueller picture."
        ),
    }

    print(f"\n  Single-qubit: Mueller sufficient = {sufficiency['single_qubit']['mueller_sufficient']}")
    print(f"    {sufficiency['single_qubit']['reason'][:120]}...")
    print(f"\n  Multi-qubit:  Mueller sufficient = {sufficiency['multi_qubit']['mueller_sufficient']}")
    print(f"    {sufficiency['multi_qubit']['reason'][:120]}...")
    print(f"\n  Key insight: {sufficiency['key_insight'][:120]}...")

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    summary = "ALL CHANNELS PASS" if all_pass else "SOME CHANNELS FAILED"
    print(f"RESULT: {summary}")
    print(f"  Channels tested: {len(results)}")
    print(f"  All physicality: {'PASS' if all(r['physicality_pass'] for r in results) else 'FAIL'}")
    print(f"  All equivalence: {'PASS' if all(r['equivalence_pass'] for r in results) else 'FAIL'}")
    print("=" * 70)

    # ------------------------------------------------------------------
    # Write results
    # ------------------------------------------------------------------
    output = {
        "sim": "pure_lego_stokes_mueller",
        "timestamp": datetime.now(UTC).isoformat(),
        "description": (
            "Stokes-Mueller formalism for single-qubit quantum channels. "
            "Mueller matrix = real 4x4 representation of density-matrix + Pauli algebra."
        ),
        "overall_pass": all_pass,
        "channels": results,
        "sufficiency_analysis": sufficiency,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "pure_lego_stokes_mueller_results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults written to {out_path}")

    return output


if __name__ == "__main__":
    run_stokes_mueller_sim()
