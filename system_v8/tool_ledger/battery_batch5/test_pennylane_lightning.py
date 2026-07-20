#!/usr/bin/env python3
"""pennylane-lightning: run the real two-sheet stage circuit (same KAK
gate list) on the lightning.qubit C++ state-vector simulator and check
final-state agreement against pennylane's own default.qubit reference on
the same representative pure state used in tools_qit_referee.py (dominant
eigenvector of the real rho0)."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent
from _stage_circuit import build_H_and_U, build_rho0, pennylane_weyl_ops, QIT_RECEIPT

OUT = Path(__file__).parent / 'results' / 'pennylane_lightning.json'


def main():
    r = {'tool': 'pennylane-lightning', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'real two-sheet unitary stage circuit + real rho0 dominant eigenvector (qit_referee)',
         'inputs': {'qit_referee_receipt': str(QIT_RECEIPT)}}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import pennylane as qml

        H, U_target = build_H_and_U()
        weyl_ops = pennylane_weyl_ops(U_target)

        rho0 = build_rho0()
        w0, V0 = np.linalg.eigh(rho0)
        psi0 = V0[:, -1] / np.linalg.norm(V0[:, -1])

        def circuit():
            qml.StatePrep(psi0, wires=[0, 1])
            for op in weyl_ops:
                qml.apply(op)
            return qml.state()

        dev_default = qml.device('default.qubit', wires=2)
        dev_light = qml.device('lightning.qubit', wires=2)

        psi_default = np.asarray(qml.QNode(circuit, dev_default)())
        psi_light = np.asarray(qml.QNode(circuit, dev_light)())

        ph = np.vdot(psi_light, psi_default)
        ph = ph / abs(ph)
        max_abs_diff = float(np.max(np.abs(psi_light * ph - psi_default)))

        pl_reference = json.loads(QIT_RECEIPT.read_text())['data']['pl_state_max_abs_diff']
        ok = max_abs_diff < 1e-9

        r.update(state='INTEGRATED' if ok else 'BLOCKED', verdict='INTEGRATED' if ok else 'BLOCKED',
                 computed_number=max_abs_diff,
                 checks={'gate_count': len(weyl_ops),
                         'lightning_vs_default_state_max_abs_diff_phase_aligned': max_abs_diff,
                         'agreement_gate_lt_1e-9': ok,
                         'default_qubit_receipt_reference_vs_matrix': pl_reference},
                 reason=f'pennylane lightning.qubit (C++ state-vector backend) runs the identical real two-sheet '
                        f'stage circuit as default.qubit on the same real representative pure state (dominant '
                        f'eigenvector of the real rho0); the two backends agree to {max_abs_diff:.3e}, well below '
                        f'the 1e-9 gate (qit_referee\'s own default.qubit-vs-matrix reference: {pl_reference:.3e}).')
    except Exception as e:
        r['exact_error'] = f'{type(e).__name__}: {e}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
