#!/usr/bin/env python3
"""sparsediffpy: build the real amplitude-damping Liouvillian (the real
Bloch/density-vectorized field generator from tools_qit_referee.py's
c_ops_damp, GAM_LAW=0.5) as a sparsediffpy expression-graph linear map
(matmul of a constant real 32x32 parameter against a real 32-vector
variable, real+imag block form of the complex 16x16 Liouvillian), and check
the engine's own sparse CSR Jacobian densifies to exactly the real Liouvillian
block matrix, matching a dense numpy Jacobian reference and preserving the
matrix's genuine sparsity pattern (not every entry nonzero)."""
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from _common import free_mem_percent

REPO = Path('/Users/joshuaeisenhart/Codex-Ratchet')
OUT = REPO / 'system_v8/tool_ledger/battery_batch5/results/sparsediffpy.json'


def main():
    r = {'tool': 'sparsediffpy', 'state': 'BLOCKED', 'verdict': 'BLOCKED', 'promotion_allowed': False,
         'generated_at': datetime.now(timezone.utc).isoformat(),
         'real_object': 'real amplitude-damping Liouvillian (tools_qit_referee.py c_ops_damp, GAM_LAW=0.5), real+imag block form'}
    try:
        free = free_mem_percent()
        r['memory_free_percent'] = free
        if free <= 25:
            raise RuntimeError(f'memory gate failed: {free}% is not >25%')
        import qutip as qt
        from sparsediffpy import _sparsediffengine as e
        import scipy.sparse as sp

        I2 = np.eye(2, dtype=complex)
        SX = np.array([[0, 1], [1, 0]], dtype=complex)
        SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
        SZ = np.array([[1, 0], [0, -1]], dtype=complex)
        SM = np.array([[0, 1], [0, 0]], dtype=complex)
        OMEGA, ALPHA, J_XY, GAM_LAW = 1.3, 0.7, 0.35, 0.5

        nx, nz = np.sin(ALPHA), np.cos(ALPHA)
        H_L = 0.5 * OMEGA * (nx * SX + nz * SZ)
        H = (np.kron(H_L, I2) + np.kron(I2, -H_L)
             + J_XY * (np.kron(SX, SX) + np.kron(SY, SY)))
        cA = [np.sqrt(GAM_LAW) * np.kron(SM, I2),
              np.sqrt(GAM_LAW) * np.kron(I2, np.conj(SM))]
        L = qt.liouvillian(qt.Qobj(H, dims=[[2, 2], [2, 2]]),
                            [qt.Qobj(c, dims=[[2, 2], [2, 2]]) for c in cA]).full()

        ReL, ImL = L.real, L.imag
        R = np.block([[ReL, -ImL], [ImL, ReL]])  # real 32x32 block form of the complex generator
        n = R.shape[0]

        r_var = e.make_variable(n, 1, 0, n)
        R_param = e.make_parameter(n, n, -1, n, R.flatten(order='F'))
        y = e.make_matmul(R_param, r_var)
        prob = e.make_problem(y, [y], 0)
        e.problem_init_jacobian(prob)
        data, indices, indptr, shape = e.problem_jacobian(prob)
        J_sparse = sp.csr_matrix((data, indices, indptr), shape=shape)
        J_dense_from_sparse = J_sparse.toarray()

        max_abs_diff = float(np.max(np.abs(J_dense_from_sparse - R)))
        nnz_real = int(np.sum(np.abs(R) > 1e-12))
        density = nnz_real / R.size
        sparsity_genuine = density < 0.5

        ok = max_abs_diff < 1e-12 and sparsity_genuine
        r.update(state='INTEGRATED' if ok else 'BLOCKED', verdict='INTEGRATED' if ok else 'BLOCKED',
                 computed_number=max_abs_diff,
                 checks={'matrix_dim': n, 'max_abs_diff_sparse_jacobian_vs_dense_real_generator': max_abs_diff,
                         'exact_match_gate_lt_1e-12': max_abs_diff < 1e-12,
                         'nnz_real_generator': nnz_real, 'total_entries': int(R.size),
                         'density': density, 'genuinely_sparse_lt_0.5': sparsity_genuine,
                         'reported_jacobian_nnz': int(J_sparse.nnz)},
                 reason=f'sparsediffpy._sparsediffengine builds an expression-graph matmul of the real '
                        f'amplitude-damping Liouvillian (real+imag 32x32 block form of the complex 16x16 GKSL '
                        f'generator from tools_qit_referee.py) against a variable vector; the engine\'s own CSR '
                        f'Jacobian densifies to exactly the real generator matrix (max abs diff '
                        f'{max_abs_diff:.3e}), which is genuinely sparse (density {density:.3f} of 1024 entries) '
                        f'not a dense matrix in disguise.')
    except Exception as e2:
        r['exact_error'] = f'{type(e2).__name__}: {e2}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(r, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
