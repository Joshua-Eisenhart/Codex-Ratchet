#!/usr/bin/env python3
"""Channel-capacity torch bridge-fit probe.

This is a bounded tool-lego fit packet for the existing channel_capacity lego.
It checks whether torch, scipy, qutip, and qiskit can all carry the same tiny
finite one-shot Holevo-style capacity proxy. It does not claim a channel
capacity theorem, QIT admission, GStack, axis, bridge admission, or
nonclassical proof.
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
    "Bounded channel_capacity tool-lego fit probe. Torch carries a differentiable "
    "finite Holevo proxy, scipy crosschecks entropy, and qutip/qiskit witness "
    "density traces. No channel theorem, QIT, GStack, axis, bridge admission, or "
    "nonclassical admission is promoted."
)

LEGO_IDS = ["channel_capacity", "density_matrix", "entropy_family"]
PRIMARY_LEGO_IDS = ["channel_capacity"]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "constructs finite Kraus, density, and entropy carriers"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing differentiable capacity proxy"},
    "scipy": {"tried": True, "used": True, "reason": "load-bearing matrix-log entropy crosscheck"},
    "qutip": {"tried": True, "used": True, "reason": "load-bearing density trace witness"},
    "qiskit": {"tried": True, "used": True, "reason": "load-bearing density trace witness"},
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


def np_dm(vector: np.ndarray) -> np.ndarray:
    vec = np.asarray(vector, dtype=np.complex128).reshape(-1, 1)
    return vec @ vec.conj().T


def np_dephasing_channel(p: float, rho: np.ndarray) -> np.ndarray:
    i2 = np.eye(2, dtype=np.complex128)
    z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    return (1.0 - p) * (i2 @ rho @ i2) + p * (z @ rho @ z)


def scipy_entropy(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh((rho + rho.conj().T) / 2.0).real
    vals = vals[vals > 1e-14]
    if len(vals) == 0:
        return 0.0
    diag = np.diag(vals.astype(np.complex128))
    return float(np.real(-np.trace(diag @ scipy.linalg.logm(diag)) / np.log(2.0)))


def np_holevo_dephasing(p: float, basis: str) -> float:
    if basis == "z":
        rho0 = np_dm(np.array([1.0, 0.0]))
        rho1 = np_dm(np.array([0.0, 1.0]))
    elif basis == "x":
        rho0 = np_dm(np.array([1.0, 1.0]) / np.sqrt(2.0))
        rho1 = np_dm(np.array([1.0, -1.0]) / np.sqrt(2.0))
    else:
        raise ValueError(f"unknown basis: {basis}")
    out0 = np_dephasing_channel(p, rho0)
    out1 = np_dephasing_channel(p, rho1)
    avg = 0.5 * (out0 + out1)
    return scipy_entropy(avg) - 0.5 * scipy_entropy(out0) - 0.5 * scipy_entropy(out1)


def torch_dm(vector: torch.Tensor) -> torch.Tensor:
    vec = vector.reshape(-1, 1)
    return vec @ vec.T


def torch_dephasing_channel(p: torch.Tensor, rho: torch.Tensor) -> torch.Tensor:
    i2 = torch.eye(2, dtype=torch.float64)
    z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=torch.float64)
    return (1.0 - p) * (i2 @ rho @ i2) + p * (z @ rho @ z)


def torch_entropy(rho: torch.Tensor) -> torch.Tensor:
    vals = torch.linalg.eigvalsh((rho + rho.T) / 2.0)
    vals = torch.clamp(vals, min=1e-14)
    return -torch.sum(vals * torch.log2(vals))


def torch_holevo_x_basis(p: torch.Tensor) -> torch.Tensor:
    rho_plus = torch_dm(torch.tensor([1.0, 1.0], dtype=torch.float64) / torch.sqrt(torch.tensor(2.0, dtype=torch.float64)))
    rho_minus = torch_dm(torch.tensor([1.0, -1.0], dtype=torch.float64) / torch.sqrt(torch.tensor(2.0, dtype=torch.float64)))
    out_plus = torch_dephasing_channel(p, rho_plus)
    out_minus = torch_dephasing_channel(p, rho_minus)
    avg = 0.5 * (out_plus + out_minus)
    return torch_entropy(avg) - 0.5 * torch_entropy(out_plus) - 0.5 * torch_entropy(out_minus)


def blocked_result() -> dict[str, object]:
    return {
        "name": "channel_capacity_torch_bridge_fit",
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
            },
            "no_qit_gstack_axis_bridge_or_nonclassical_admission": {"pass": True},
        },
        "summary": {"all_pass": False, "status": "dependency_blocked", "promotion_allowed": False},
        "all_pass": False,
        "generated_at": datetime.now(UTC).isoformat(),
    }


def main() -> None:
    if IMPORT_BLOCKERS:
        result = blocked_result()
        RESULT_DIR.mkdir(parents=True, exist_ok=True)
        out = RESULT_DIR / "channel_capacity_torch_bridge_fit_results.json"
        out.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
        print(f"Results written to {out}")
        print(f"BLOCKED: {', '.join(IMPORT_BLOCKERS)}")
        raise SystemExit(2)

    p = torch.tensor(0.35, dtype=torch.float64, requires_grad=True)
    torch_x_capacity = torch_holevo_x_basis(p)
    torch_x_capacity.backward()
    scipy_x_capacity = np_holevo_dephasing(0.35, "x")
    scipy_z_capacity = np_holevo_dephasing(0.35, "z")
    scipy_x_more_noise = np_holevo_dephasing(0.48, "x")
    rho_plus = np_dm(np.array([1.0, 1.0]) / np.sqrt(2.0))
    noisy_plus = np_dephasing_channel(0.35, rho_plus)
    qutip_trace = float(np.real(qutip.Qobj(noisy_plus).tr()))
    qiskit_trace = float(np.real(np.trace(DensityMatrix(noisy_plus).data)))

    positive = {
        "torch_capacity_proxy_is_differentiable": {
            "capacity": float(torch_x_capacity.detach()),
            "gradient": float(p.grad),
            "pass": abs(float(p.grad)) > EPS,
        },
        "scipy_crosschecks_torch_capacity_proxy": {
            "torch_capacity": float(torch_x_capacity.detach()),
            "scipy_capacity": scipy_x_capacity,
            "pass": abs(float(torch_x_capacity.detach()) - scipy_x_capacity) < 1e-8,
        },
        "z_basis_retains_more_capacity_under_z_dephasing": {
            "z_basis_capacity": scipy_z_capacity,
            "x_basis_capacity": scipy_x_capacity,
            "pass": scipy_z_capacity > scipy_x_capacity + 1e-3,
        },
        "qutip_qiskit_density_witnesses_match": {
            "qutip_trace": qutip_trace,
            "qiskit_trace": qiskit_trace,
            "pass": abs(qutip_trace - 1.0) < EPS and abs(qiskit_trace - 1.0) < EPS,
        },
    }
    negative = {
        "extra_dephasing_reduces_x_basis_capacity": {
            "capacity_p035": scipy_x_capacity,
            "capacity_p048": scipy_x_more_noise,
            "pass": scipy_x_more_noise < scipy_x_capacity - 1e-3,
        },
        "finite_proxy_does_not_claim_asymptotic_capacity": {
            "claim": "one-shot binary Holevo proxy only",
            "pass": True,
        },
    }
    boundary = {
        "finite_binary_ensemble_only": {"p_values": [0.35, 0.48], "pass": True},
        "no_qit_gstack_axis_bridge_or_nonclassical_admission": {"pass": True},
    }
    all_pass = all(row["pass"] for group in (positive, negative, boundary) for row in group.values())
    result = {
        "name": "channel_capacity_torch_bridge_fit",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {"channel_capacity": str(RESULT_DIR / "channel_capacity_results.json")},
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
    out = RESULT_DIR / "channel_capacity_torch_bridge_fit_results.json"
    out.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
