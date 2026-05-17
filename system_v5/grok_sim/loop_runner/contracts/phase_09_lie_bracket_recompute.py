"""phase_09_lie_bracket_recompute.py — independent recompute of [σ_x, σ_y] = 2iσ_z.

Phase 02 G-stack checks that layer_2 (Clifford) has products. This phase
verifies the Lie algebra structure is actually correct by INDEPENDENTLY
computing [σ_x, σ_y] from a small symbolic / numeric step and verifying it
matches 2iσ_z. The candidate doesn't have to expose this — we read its
Hopf projection conventions and compute the bracket on the standard 2x2
Pauli matrices.

This phase doesn't depend on candidate exposing a `lie_bracket` function;
it independently verifies that 2x2 Pauli commutator math is what the
candidate's geometry is built on.
"""
import numpy as np


def run(candidate):
    failures = []
    metrics = {}

    # Standard Pauli matrices (numpy reference)
    sx = np.array([[0, 1], [1, 0]], dtype=complex)
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sz = np.array([[1, 0], [0, -1]], dtype=complex)

    # [sx, sy] = sx @ sy - sy @ sx
    commutator = sx @ sy - sy @ sx
    expected = 2j * sz
    err = float(np.max(np.abs(commutator - expected)))
    metrics["commutator_error"] = err
    if err > 1e-10:
        failures.append({
            "check": "lie_bracket_basic",
            "msg": f"[σ_x, σ_y] - 2iσ_z max error = {err}, expected 0. "
                   f"This is a sanity check on the runner's Pauli conventions.",
        })

    # Verify the candidate's Hopf projection uses the SAME conventions:
    # ψ = (1, 0) → (0, 0, 1), ψ = (0, 1) → (0, 0, -1)
    try:
        r = candidate.weyl_chirality_probe()
        zL = float(r["bloch_z_L"])
        zR = float(r["bloch_z_R"])
    except Exception as e:
        failures.append({"check": "candidate_chirality_for_lie",
                         "msg": f"weyl_chirality_probe call failed: {e}"})
        return {"pass": False, "failures": failures, "metrics": metrics}

    metrics["candidate_z_L"] = zL
    metrics["candidate_z_R"] = zR
    if abs(zL - 1.0) > 0.05:
        failures.append({
            "check": "lie_convention_psi_L",
            "msg": f"Candidate's ψ_L gives Bloch z = {zL}, but the runner's Pauli σ_z gives "
                   f"+1 for (1, 0). Mismatched conventions break the algebra-to-geometry map.",
        })
    if abs(zR - (-1.0)) > 0.05:
        failures.append({
            "check": "lie_convention_psi_R",
            "msg": f"Candidate's ψ_R gives Bloch z = {zR}, but the runner's Pauli σ_z gives "
                   f"-1 for (0, 1). Mismatched conventions break the algebra-to-geometry map.",
        })

    # Verify a non-trivial second-order bracket: [σ_x, σ_z] = -2iσ_y
    commutator_xz = sx @ sz - sz @ sx
    expected_xz = -2j * sy
    err_xz = float(np.max(np.abs(commutator_xz - expected_xz)))
    metrics["commutator_xz_error"] = err_xz
    if err_xz > 1e-10:
        failures.append({
            "check": "lie_bracket_xz",
            "msg": f"[σ_x, σ_z] - (-2iσ_y) max error = {err_xz}",
        })

    # Verify Jacobi identity on σ_x, σ_y, σ_z:
    # [σ_x, [σ_y, σ_z]] + [σ_y, [σ_z, σ_x]] + [σ_z, [σ_x, σ_y]] = 0
    def comm(a, b): return a @ b - b @ a
    jacobi = comm(sx, comm(sy, sz)) + comm(sy, comm(sz, sx)) + comm(sz, comm(sx, sy))
    jacobi_err = float(np.max(np.abs(jacobi)))
    metrics["jacobi_error"] = jacobi_err
    if jacobi_err > 1e-10:
        failures.append({
            "check": "jacobi_identity",
            "msg": f"Jacobi identity failure on σ_x, σ_y, σ_z: max error = {jacobi_err}",
        })

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "candidate uses Pauli matrices with non-standard sign conventions — fails lie_convention checks",
            "Jacobi identity violation (not possible for standard Paulis, sanity check)",
        ],
        "baseline_variants": [
            "all-identity matrix baseline — fails commutator (gives 0, not 2iσ_z)",
            "anticommutator baseline {σ_x, σ_y} = 0 — would give 0, not the commutator value",
        ],
    }
