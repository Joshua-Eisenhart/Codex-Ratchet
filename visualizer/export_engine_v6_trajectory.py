"""Export engine_v6 per-substage trajectories for the v6 visualizer.

Runs TrainableEngineV6 (type-1 = L, type-2 = R) from a fixed seeded initial
state and records, at each of the 32 substages: terrain/op metadata, full-state
von Neumann entropy, purity, per-qubit Bloch vectors, half-chain bipartite MI,
and the full pairwise qubit MI matrix.

Source of truth: system_v5/ops/formal_scouts/engine_v6_proper_multiqubit_reference.py
Output: visualizer/engine-v6-trajectory-data.js  (window.ENGINE_V6_TRAJECTORY)

No values are invented; everything is computed by the canonical engine module.
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SCOUTS = REPO / "system_v5" / "ops" / "formal_scouts"
sys.path.insert(0, str(SCOUTS))

from engine_v6_proper_multiqubit_reference import (  # noqa: E402
    TrainableEngineV6,
    make_paulis,
    normalize_density,
    random_pure_nqubit_state,
)

N_QUBITS = 4
SEED = 20260609
DTYPE = torch.complex64

TERRAIN_NAMES = ["funnel", "vortex", "ladder", "strata"]
OP_NAMES = ["Z0", "X0", "X0", "Y0"]


def reduced_rho(rho, n_qubits, keep):
    """Partial trace keeping qubit indices in `keep` (sorted tuple)."""
    dims = [2] * n_qubits
    t = rho.reshape(*dims, *dims)
    traced = [q for q in range(n_qubits) if q not in keep]
    # trace out highest indices first to keep axis bookkeeping simple
    for q in sorted(traced, reverse=True):
        t = torch.diagonal(t, dim1=q, dim2=q + (t.dim() // 2)).sum(-1)
        # after diagonal+sum, remaining dims shrink by one ket and one bra axis
    d = 2 ** len(keep)
    return t.reshape(d, d)


def vn_entropy_m(rho):
    ev = torch.linalg.eigvalsh(rho)
    ev = ev.clamp(min=1e-12)
    return float(-(ev * ev.log()).sum().real)


def purity_m(rho):
    return float((rho @ rho).diagonal().sum().real)


def bloch_of_qubit(rho, n_qubits, q, P):
    r1 = reduced_rho(rho, n_qubits, (q,))
    return [float((r1 @ P[k]).diagonal().sum().real) for k in ("X", "Y", "Z")]


def pairwise_mi(rho, n_qubits):
    s1 = [vn_entropy_m(reduced_rho(rho, n_qubits, (q,))) for q in range(n_qubits)]
    out = []
    for i in range(n_qubits):
        for j in range(i + 1, n_qubits):
            sij = vn_entropy_m(reduced_rho(rho, n_qubits, (i, j)))
            out.append({"i": i, "j": j, "mi": s1[i] + s1[j] - sij})
    return out, s1


def halfchain_mi(rho, n_qubits):
    half = tuple(range(n_qubits // 2))
    rest = tuple(range(n_qubits // 2, n_qubits))
    return (
        vn_entropy_m(reduced_rho(rho, n_qubits, half))
        + vn_entropy_m(reduced_rho(rho, n_qubits, rest))
        - vn_entropy_m(rho)
    )


def run_engine(engine_type, rho0):
    eng = TrainableEngineV6(engine_type=engine_type, n_qubits=N_QUBITS)
    eng.eval()
    P = make_paulis()
    rho = normalize_density(rho0.clone())
    frames = []
    k = 0
    with torch.no_grad():
        for stage_pos, terrain_idx in enumerate(eng.stage_sequence()):
            for op_idx, sign in eng.stage_substages(terrain_idx):
                rho = eng.run_substage(rho, terrain_idx, op_idx, sign)
                r = rho.squeeze(0) if rho.dim() == 3 else rho
                pmi, s1 = pairwise_mi(r, N_QUBITS)
                frames.append({
                    "substage": k,
                    "stage_pos": stage_pos,
                    "terrain": int(terrain_idx),
                    "terrain_name": TERRAIN_NAMES[terrain_idx],
                    "op": OP_NAMES[op_idx],
                    "op_sign": int(sign),
                    "entropy": vn_entropy_m(r),
                    "purity": purity_m(r),
                    "bloch": [bloch_of_qubit(r, N_QUBITS, q, P) for q in range(N_QUBITS)],
                    "qubit_entropy": s1,
                    "mi_halfchain": halfchain_mi(r, N_QUBITS),
                    "mi_pairs": pmi,
                })
                k += 1
    return frames


def main():
    g = torch.Generator().manual_seed(SEED)
    psi = torch.randn(2 ** N_QUBITS, 2, generator=g)
    psi = (psi[:, 0] + 1j * psi[:, 1]).to(DTYPE)
    psi = psi / psi.norm()
    rho0 = torch.outer(psi, psi.conj())

    data = {
        "meta": {
            "exported_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source_module": "system_v5/ops/formal_scouts/engine_v6_proper_multiqubit_reference.py",
            "exporter": "visualizer/export_engine_v6_trajectory.py",
            "n_qubits": N_QUBITS,
            "seed": SEED,
            "initial_state": "seeded Haar-like random pure state (torch.randn, normalized)",
            "n_substages": 32,
            "engine_params": "module defaults (untrained init): dt=0.06, n_steps_per_substage=2, nn_coupling=0.3",
            "claim_note": "Trajectory of the UNTRAINED reference engine at default init params. Display-only; implies no proof or basin claim.",
        },
        "engines": {
            "L": {"engine_type": 1, "frames": run_engine(1, rho0)},
            "R": {"engine_type": 2, "frames": run_engine(2, rho0)},
        },
    }
    out = HERE / "engine-v6-trajectory-data.js"
    out.write_text(
        "// generated by export_engine_v6_trajectory.py — do not hand-edit\n"
        "window.ENGINE_V6_TRAJECTORY = " + json.dumps(data) + ";\n"
    )
    print(f"wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
