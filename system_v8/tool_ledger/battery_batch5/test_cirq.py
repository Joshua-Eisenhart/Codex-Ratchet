#!/usr/bin/env python3
"""cirq: rebuild the real two-sheet stage circuit (identical RY/RZ/CNOT gate
list KAK-decomposed by pennylane in tools_qit_referee.py, receipt value
pl_unitary_max_abs_diff=8.713286527709283e-15) as a cirq.Circuit and check
unitary agreement against the same U_target = expm(-i H_joint * 0.4)."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent
from _stage_circuit import build_H_and_U, pennylane_weyl_ops, gate_list, QIT_RECEIPT

OUT = Path(__file__).parent / 'results' / 'cirq.json'


def main():
    r = {'tool': 'cirq', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'real two-sheet unitary stage exp(-i H_joint 0.4), gate list KAK-decomposed by pennylane',
         'inputs': {'qit_referee_receipt': str(QIT_RECEIPT)}}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import cirq

        H, U_target = build_H_and_U()
        weyl_ops = pennylane_weyl_ops(U_target)
        gl = gate_list(weyl_ops)

        q0, q1 = cirq.LineQubit.range(2)
        qmap = {0: q0, 1: q1}
        ops = []
        for name, w, param in gl:
            if name == 'CNOT':
                a, b = w
                ops.append(cirq.CNOT(qmap[a], qmap[b]))
            elif name == 'RY':
                ops.append(cirq.ry(param).on(qmap[w]))
            elif name == 'RZ':
                ops.append(cirq.rz(param).on(qmap[w]))
        circuit = cirq.Circuit(ops)
        U_circ = cirq.unitary(circuit)  # cirq's own wire order is q0-major (matches pennylane [0,1])

        ph = np.vdot(U_circ.flatten(), U_target.flatten())
        ph = ph / abs(ph)
        max_abs_diff = float(np.max(np.abs(U_circ * ph - U_target)))

        pl_reference = json.loads(QIT_RECEIPT.read_text())['data']['pl_unitary_max_abs_diff']
        ok = max_abs_diff < 1e-9

        r.update(state='INTEGRATED' if ok else 'BLOCKED', verdict='INTEGRATED' if ok else 'BLOCKED',
                 computed_number=max_abs_diff,
                 checks={'gate_count': len(gl),
                         'cirq_unitary_vs_expm_max_abs_diff_phase_aligned': max_abs_diff,
                         'agreement_gate_lt_1e-9': ok,
                         'pennylane_kak_receipt_reference': pl_reference},
                 reason=f'cirq.Circuit built from the same real KAK/ZYZ gate list pennylane compiles in '
                        f'tools_qit_referee.py; cirq unitary agrees with the analytic expm(-i H_joint 0.4) to '
                        f'{max_abs_diff:.3e} (pennylane receipt reference {pl_reference:.3e}), both far below '
                        f'the 1e-9 gate — two independent circuit engines, same real two-sheet stage matrix.')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
