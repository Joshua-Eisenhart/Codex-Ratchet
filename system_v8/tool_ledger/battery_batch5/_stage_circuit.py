"""Shared real-object construction for the cirq/qiskit/pennylane-lightning
circuit trio: the same two-sheet unitary stage U = exp(-i H_joint * 0.4) and
KAK-decomposed RY/RZ/CNOT gate list that system_v8/deep_integration/
tools_qit_referee.py builds and receipts (data.pl_unitary_max_abs_diff =
8.713286527709283e-15 against expm), read directly from the qit_referee
receipt's declared H/rho0 construction (mirrored constants, not re-derived
parameters) so every engine in this trio operates on the identical real
matrix.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
from scipy.linalg import expm

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
QIT_RECEIPT = REPO / 'system_v8/deep_integration/results/qit_referee/receipt.json'

# mirrored from tools_qit_referee.py / julia_manifold_tick.jl law_runs()
N_TICKS = 30
TICK_DT = 0.4
OMEGA = 1.3
ALPHA = 0.7
J_XY = 0.35

I2 = np.eye(2, dtype=complex)
SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)


def build_H_and_U():
    nx, nz = np.sin(ALPHA), np.cos(ALPHA)
    H_L = 0.5 * OMEGA * (nx * SX + nz * SZ)
    H = (np.kron(H_L, I2) + np.kron(I2, -H_L)
         + J_XY * (np.kron(SX, SX) + np.kron(SY, SY)))
    U_target = expm(-1j * H * TICK_DT)
    return H, U_target


def build_rho0():
    rho0_L = 0.5 * (I2 + 0.5 * SX + 0.3 * SY - 0.4 * SZ)
    rho0 = np.kron(rho0_L, np.conj(rho0_L))
    return rho0


def pennylane_weyl_ops(U_target):
    """Reproduce the exact KAK/ZYZ gate decomposition tools_qit_referee.py
    builds, so the other two engines can rebuild the identical gate
    sequence."""
    import pennylane as qml
    from pennylane.ops import one_qubit_decomposition
    from pennylane.ops.op_math.decompositions import two_qubit_decomposition

    raw_ops = two_qubit_decomposition(U_target, wires=[0, 1])
    weyl_ops = []
    for op in raw_ops:
        if op.name in ("CNOT", "RY", "RZ", "GlobalPhase"):
            weyl_ops.append(op)
        elif op.name == "QubitUnitary":
            weyl_ops += one_qubit_decomposition(
                op.matrix(), op.wires[0], "ZYZ", return_global_phase=True)
        elif op.name == "Rot":
            a, b, c = op.parameters
            w = op.wires[0]
            weyl_ops += [qml.RZ(a, w), qml.RY(b, w), qml.RZ(c, w)]
        else:
            raise SystemExit(f"unexpected op in decomposition: {op.name}")
    return weyl_ops


def gate_list(weyl_ops):
    """Flatten to a portable (name, wire, param_or_None) list, RY/RZ/CNOT/
    GlobalPhase only, dropping GlobalPhase (a scalar phase both other
    engines can apply post-hoc, and the agreement check is phase-aligned
    anyway, matching tools_qit_referee.py's own convention)."""
    out = []
    for op in weyl_ops:
        if op.name == 'CNOT':
            out.append(('CNOT', tuple(int(w) for w in op.wires), None))
        elif op.name in ('RY', 'RZ'):
            out.append((op.name, int(op.wires[0]), float(op.parameters[0])))
        elif op.name == 'GlobalPhase':
            pass
        else:
            raise SystemExit(f'unexpected gate {op.name}')
    return out
