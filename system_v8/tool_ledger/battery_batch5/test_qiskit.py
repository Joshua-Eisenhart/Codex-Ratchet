#!/usr/bin/env python3
"""qiskit: rebuild the same real two-sheet stage circuit as cirq/pennylane
(identical KAK-decomposed RY/RZ/CNOT gate list, receipt reference
pl_unitary_max_abs_diff=8.713286527709283e-15) and check unitary agreement
against U_target = expm(-i H_joint * 0.4)."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent
from _stage_circuit import build_H_and_U, pennylane_weyl_ops, gate_list, QIT_RECEIPT

OUT = Path(__file__).parent / 'results' / 'qiskit.json'


def main():
    r = {'tool': 'qiskit', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'real two-sheet unitary stage exp(-i H_joint 0.4), gate list KAK-decomposed by pennylane',
         'inputs': {'qit_referee_receipt': str(QIT_RECEIPT)}}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        from qiskit import QuantumCircuit
        from qiskit.quantum_info import Operator

        H, U_target = build_H_and_U()
        weyl_ops = pennylane_weyl_ops(U_target)
        gl = gate_list(weyl_ops)

        # pennylane wire 0 is the "top" qubit in its little-endian tensor
        # convention matching np.kron(H_L, I2); qiskit's Operator() uses the
        # same little-endian qubit-0-is-least-significant convention as
        # qiskit's own kron ordering, so wire index maps straight across.
        qc = QuantumCircuit(2)
        for name, w, param in gl:
            if name == 'CNOT':
                a, b = w
                qc.cx(a, b)
            elif name == 'RY':
                qc.ry(param, w)
            elif name == 'RZ':
                qc.rz(param, w)
        U_circ = Operator(qc).data  # qiskit little-endian: qubit0 = LSB

        # qiskit's tensor convention is reversed vs pennylane's ([0,1] order
        # = q0 (x) q1 in pennylane, q1 (x) q0 in qiskit's default Operator
        # ordering) -- reorder qiskit's matrix to match pennylane/cirq's
        # [0,1]-major convention via a swap, then compare.
        SWAP = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=complex)
        U_circ_matched = SWAP @ U_circ @ SWAP

        ph = np.vdot(U_circ_matched.flatten(), U_target.flatten())
        ph = ph / abs(ph)
        max_abs_diff = float(np.max(np.abs(U_circ_matched * ph - U_target)))

        pl_reference = json.loads(QIT_RECEIPT.read_text())['data']['pl_unitary_max_abs_diff']
        ok = max_abs_diff < 1e-9

        r.update(state='INTEGRATED' if ok else 'BLOCKED', verdict='INTEGRATED' if ok else 'BLOCKED',
                 computed_number=max_abs_diff,
                 checks={'gate_count': len(gl),
                         'qiskit_unitary_vs_expm_max_abs_diff_phase_aligned_wire_swap_corrected': max_abs_diff,
                         'agreement_gate_lt_1e-9': ok,
                         'pennylane_kak_receipt_reference': pl_reference},
                 reason=f'qiskit QuantumCircuit built from the same real KAK/ZYZ gate list pennylane/cirq use; '
                        f'after correcting for qiskit\'s reversed tensor-wire convention (SWAP-conjugation), '
                        f'the qiskit unitary agrees with the analytic expm(-i H_joint 0.4) to {max_abs_diff:.3e} '
                        f'(pennylane receipt reference {pl_reference:.3e}) — a third independent circuit engine '
                        f'on the same real two-sheet stage matrix.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
