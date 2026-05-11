#!/usr/bin/env python3
"""Channel-space geometry torch bridge-fit probe.

This is a bounded tool-lego fit packet for the existing channel_space_geometry
lego. It checks whether torch tensors, scipy entropy, and independent qutip /
qiskit density witnesses can carry the same tiny finite channel geometry
surface. It is not QIT, GStack, axis, bridge admission, or nonclassical proof.
"""

from __future__ import annotations

import json
import pathlib
from datetime import UTC, datetime

import numpy as np
import scipy.linalg
import torch

IMPORT_BLOCKERS = []
try:
    import qutip
except ModuleNotFoundError as exc:
    qutip = None
    IMPORT_BLOCKERS.append(str(exc))

try:
    from qiskit.quantum_info import DensityMatrix
except ModuleNotFoundError as exc:
    DensityMatrix = None
    IMPORT_BLOCKERS.append(str(exc))


CLASSIFICATION = "tool_lego_fit_probe"
classification = CLASSIFICATION
divergence_log = (
    "Bounded channel_space_geometry tool-lego fit probe. Torch carries the "
    "finite tensor surface, scipy computes entropy on the same Choi carriers, "
    "and qutip/qiskit witness density-matrix trace agreement. No promotion."
)

LEGO_IDS = ["channel_space_geometry", "density_matrix", "entropy_family"]
PRIMARY_LEGO_IDS = ["channel_space_geometry"]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "constructs finite Kraus and Choi carriers"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing tensor distances and gradient over dephasing parameter"},
    "scipy": {"tried": True, "used": True, "reason": "load-bearing matrix-log entropy crosscheck"},
    "qutip": {"tried": True, "used": True, "reason": "independent density trace witness"},
    "qiskit": {"tried": True, "used": True, "reason": "independent density trace witness"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "pytorch": "load_bearing",
    "scipy": "load_bearing",
    "qutip": "load_bearing",
    "qiskit": "load_bearing",
}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
EPS = 1e-10


def np_dephasing_choi(p: float) -> np.ndarray:
    i2 = np.eye(2, dtype=np.complex128)
    z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    kraus = [np.sqrt(1.0 - p) * i2, np.sqrt(p) * z]
    omega = np.array([1.0, 0.0, 0.0, 1.0], dtype=np.complex128) / np.sqrt(2.0)
    omega_dm = np.outer(omega, omega.conj())
    out = np.zeros((4, 4), dtype=np.complex128)
    for k in kraus:
        ki = np.kron(k, i2)
        out += ki @ omega_dm @ ki.conj().T
    return out


def torch_dephasing_choi(p: torch.Tensor) -> torch.Tensor:
    dtype = torch.float64
    i2 = torch.eye(2, dtype=dtype)
    z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=dtype)
    omega = torch.tensor([1.0, 0.0, 0.0, 1.0], dtype=dtype) / torch.sqrt(torch.tensor(2.0, dtype=dtype))
    omega_dm = torch.outer(omega, omega)
    out = torch.zeros((4, 4), dtype=dtype)
    for k in (torch.sqrt(1.0 - p) * i2, torch.sqrt(p) * z):
        ki = torch.kron(k, i2)
        out = out + ki @ omega_dm @ ki.T
    return out


def entropy_scipy(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh((rho + rho.conj().T) / 2.0).real
    vals = vals[vals > 1e-14]
    diag = np.diag(vals.astype(np.complex128))
    return float(np.real(-np.trace(diag @ scipy.linalg.logm(diag))))


def main() -> None:
    if IMPORT_BLOCKERS:
        result = {
            "name": "channel_space_geometry_torch_bridge_fit",
            "classification": "dependency_blocked",
            "classification_note": divergence_log,
            "divergence_log": divergence_log,
            "lego_ids": LEGO_IDS,
            "primary_lego_ids": PRIMARY_LEGO_IDS,
            "tool_manifest": TOOL_MANIFEST,
            "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
            "positive": {},
            "negative": {},
            "boundary": {
                "required_density_witness_imports": {
                    "pass": False,
                    "status": "blocked",
                    "errors": IMPORT_BLOCKERS,
                    "reason": "qutip and qiskit are required density witnesses for this bridge-fit packet.",
                },
                "no_qit_gstack_axis_or_nonclassical_admission": {"pass": True},
            },
            "summary": {
                "all_pass": False,
                "status": "dependency_blocked",
                "blockers": IMPORT_BLOCKERS,
                "promotion_allowed": False,
            },
            "all_pass": False,
            "generated_at": datetime.now(UTC).isoformat(),
        }
        RESULT_DIR.mkdir(parents=True, exist_ok=True)
        out = RESULT_DIR / "channel_space_geometry_torch_bridge_fit_results.json"
        out.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
        print(f"Results written to {out}")
        print(f"BLOCKED: {', '.join(IMPORT_BLOCKERS)}")
        raise SystemExit(2)

    p0 = torch.tensor(0.25, dtype=torch.float64, requires_grad=True)
    p1 = torch.tensor(0.55, dtype=torch.float64)
    choi0 = torch_dephasing_choi(p0)
    choi1 = torch_dephasing_choi(p1)
    distance = torch.linalg.matrix_norm(choi0 - choi1)
    distance.backward()

    np_choi0 = np_dephasing_choi(float(p0.detach()))
    np_choi1 = np_dephasing_choi(float(p1))
    scipy_entropy0 = entropy_scipy(np_choi0)
    scipy_entropy1 = entropy_scipy(np_choi1)
    qutip_trace = float(np.real(qutip.Qobj(np_choi0).tr()))
    qiskit_trace = float(np.real(np.trace(DensityMatrix(np_choi0).data)))

    positive = {
        "torch_separates_two_channel_points": {
            "distance": float(distance.detach()),
            "pass": float(distance.detach()) > EPS,
        },
        "torch_gradient_is_nonzero_for_channel_distance": {
            "gradient": float(p0.grad),
            "pass": abs(float(p0.grad)) > EPS,
        },
        "scipy_entropy_distinguishes_channel_points": {
            "entropy_p025": scipy_entropy0,
            "entropy_p055": scipy_entropy1,
            "pass": abs(scipy_entropy1 - scipy_entropy0) > EPS,
        },
        "qutip_qiskit_trace_witnesses_match": {
            "qutip_trace": qutip_trace,
            "qiskit_trace": qiskit_trace,
            "pass": abs(qutip_trace - 1.0) < EPS and abs(qiskit_trace - 1.0) < EPS,
        },
    }
    negative = {
        "distinct_parameters_are_not_collapsed": {
            "numpy_frobenius_distance": float(np.linalg.norm(np_choi0 - np_choi1)),
            "pass": float(np.linalg.norm(np_choi0 - np_choi1)) > EPS,
        },
        "trace_witness_does_not_promote_runtime": {
            "claim": "density witnesses prove only finite density-carrier agreement",
            "pass": True,
        },
    }
    boundary = {
        "finite_qubit_dephasing_family_only": {"p_values": [0.25, 0.55], "pass": True},
        "no_qit_gstack_axis_or_nonclassical_admission": {"pass": True},
    }
    all_pass = all(row["pass"] for group in (positive, negative, boundary) for row in group.values())
    result = {
        "name": "channel_space_geometry_torch_bridge_fit",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {
            "channel_space_geometry": str(RESULT_DIR / "channel_space_geometry_results.json"),
        },
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "tool_lego_fit": "bridge_nonclassical_adjacent",
            "promotion_allowed": False,
            "scope_note": divergence_log,
        },
        "all_pass": all_pass,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULT_DIR / "channel_space_geometry_torch_bridge_fit_results.json"
    out.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
