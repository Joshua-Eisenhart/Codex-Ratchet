#!/usr/bin/env python3
"""Finite density-carrier closure across torch, QuTiP, and Qiskit.

This packet closes a narrow carrier question for the lego queue: can the same
finite one-qubit density carrier and channel action be represented consistently
by torch tensors, QuTiP Qobj, Qiskit DensityMatrix/Kraus, and numpy matrices
while invalid carrier counterexamples are rejected?

This is lego-stage evidence only. It does not admit QIT, GStack, axes, bridge,
or nonclassical claims.
"""

from __future__ import annotations

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
classification = 'classical_baseline'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import qutip
import torch
from qiskit.quantum_info import DensityMatrix, Kraus

from receipt_boundary import apply_default_receipt_boundary


SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
PARENT_RESULT_NAMES = [
    "density_hopf_geometry_results.json",
    "integrated_dependency_chain_results.json",
    "channel_space_geometry_results.json",
]
OUT_PATH = RESULTS_DIR / "density_carrier_qutip_qiskit_closure_results.json"
TOL = 1e-9

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "load-bearing reference density/channel matrices and validity checks"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing Hermitian eigenspectrum and entropy cross-checks"},
    "qutip": {"tried": True, "used": True, "reason": "load-bearing Qobj density carrier and entropy/channel witness"},
    "qiskit": {"tried": True, "used": True, "reason": "load-bearing DensityMatrix/Kraus representation of the same finite carrier"},
    "scipy": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed; invalid carriers are direct finite matrix counterexamples"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "pyg": {"tried": False, "used": False, "reason": "not needed; no graph message-passing"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": False, "used": False, "reason": "not needed; parent density/Hopf receipt carries Clifford geometry"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed; parent density/Hopf receipt carries manifold checks"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "pytorch": "load_bearing",
    "qutip": "load_bearing",
    "qiskit": "load_bearing",
    "scipy": None,
    "sympy": None,
    "z3": None,
    "cvc5": None,
    "pyg": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
    "clifford": None,
    "geomstats": None,
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parent_receipts() -> list[dict]:
    rows = []
    for name in PARENT_RESULT_NAMES:
        path = RESULTS_DIR / name
        payload = read_json(path) if path.exists() else {}
        rows.append(
            {
                "name": name,
                "path": str(path),
                "exists": path.exists(),
                "classification": payload.get("classification"),
                "all_pass": bool(payload.get("all_pass") or payload.get("summary", {}).get("all_pass")),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None,
            }
        )
    return rows


def density_from_bloch(vec: np.ndarray) -> np.ndarray:
    sx = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    sy = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
    sz = np.array([[1, 0], [0, -1]], dtype=np.complex128)
    return (np.eye(2, dtype=np.complex128) + vec[0] * sx + vec[1] * sy + vec[2] * sz) / 2.0


def carrier_validity(rho: np.ndarray) -> dict:
    hermitian_error = float(np.max(np.abs(rho - rho.conj().T)))
    trace_error = float(abs(np.trace(rho) - 1.0))
    eig_np = np.linalg.eigvalsh((rho + rho.conj().T) / 2.0)
    eig_torch = torch.linalg.eigvalsh(torch.tensor(rho, dtype=torch.complex128)).real.numpy()
    return {
        "hermitian_error": hermitian_error,
        "trace_error": trace_error,
        "min_eig_numpy": float(np.min(eig_np)),
        "min_eig_torch": float(np.min(eig_torch)),
        "pass": hermitian_error < TOL and trace_error < TOL and np.min(eig_np) > -TOL and np.min(eig_torch) > -TOL,
    }


def entropy_numpy(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh((rho + rho.conj().T) / 2.0)
    vals = np.clip(vals.real, 0.0, 1.0)
    vals = vals[vals > TOL]
    return float(-np.sum(vals * np.log2(vals))) if vals.size else 0.0


def entropy_torch(rho: np.ndarray) -> float:
    vals = torch.linalg.eigvalsh(torch.tensor(rho, dtype=torch.complex128)).real
    vals = torch.clamp(vals, min=0.0)
    vals = vals[vals > TOL]
    return float((-torch.sum(vals * torch.log2(vals))).item()) if vals.numel() else 0.0


def entropy_qutip(rho: np.ndarray) -> float:
    return float(qutip.entropy_vn(qutip.Qobj(rho, dims=[[2], [2]]), base=2))


def amplitude_damping_kraus(gamma: float) -> list[np.ndarray]:
    return [
        np.array([[1.0, 0.0], [0.0, math.sqrt(1.0 - gamma)]], dtype=np.complex128),
        np.array([[0.0, math.sqrt(gamma)], [0.0, 0.0]], dtype=np.complex128),
    ]


def apply_kraus_numpy(rho: np.ndarray, kraus_ops: list[np.ndarray]) -> np.ndarray:
    return sum(k @ rho @ k.conj().T for k in kraus_ops)


def apply_kraus_qutip(rho: np.ndarray, kraus_ops: list[np.ndarray]) -> np.ndarray:
    q_rho = qutip.Qobj(rho, dims=[[2], [2]])
    out = qutip.Qobj(np.zeros((2, 2), dtype=np.complex128), dims=[[2], [2]])
    for op in kraus_ops:
        q_op = qutip.Qobj(op, dims=[[2], [2]])
        out += q_op * q_rho * q_op.dag()
    return np.asarray(out.full(), dtype=np.complex128)


def apply_kraus_qiskit(rho: np.ndarray, kraus_ops: list[np.ndarray]) -> np.ndarray:
    return np.asarray(DensityMatrix(rho).evolve(Kraus(kraus_ops)).data, dtype=np.complex128)


def sample_states() -> list[dict]:
    bloch_rows = [
        ("mixed_z", np.array([0.0, 0.0, 0.35])),
        ("coherent_x", np.array([0.7, 0.0, 0.0])),
        ("coherent_xyz", np.array([0.25, -0.35, 0.45])),
        ("near_pure", np.array([0.2, 0.3, math.sqrt(0.86)])),
    ]
    return [{"label": label, "bloch": vec.tolist(), "rho": density_from_bloch(vec)} for label, vec in bloch_rows]


def invalid_counterexamples() -> dict:
    valid = density_from_bloch(np.array([0.2, 0.1, 0.3]))
    trace_bad = valid * 1.2
    non_hermitian = valid.copy()
    non_hermitian[0, 1] += 0.2j
    negative_eigen = np.array([[1.2, 0.0], [0.0, -0.2]], dtype=np.complex128)
    rows = {
        "trace_bad": carrier_validity(trace_bad),
        "non_hermitian": carrier_validity(non_hermitian),
        "negative_eigenvalue": carrier_validity(negative_eigen),
    }
    return {
        name: {**row, "pass": not bool(row["pass"])}
        for name, row in rows.items()
    }


def main() -> int:
    parents = parent_receipts()
    states = sample_states()
    gamma = 0.37
    kraus_ops = amplitude_damping_kraus(gamma)
    state_rows = []
    for row in states:
        rho = row["rho"]
        qutip_rho = np.asarray(qutip.Qobj(rho, dims=[[2], [2]]).full(), dtype=np.complex128)
        qiskit_rho = np.asarray(DensityMatrix(rho).data, dtype=np.complex128)
        out_np = apply_kraus_numpy(rho, kraus_ops)
        out_qutip = apply_kraus_qutip(rho, kraus_ops)
        out_qiskit = apply_kraus_qiskit(rho, kraus_ops)
        state_rows.append(
            {
                "label": row["label"],
                "validity": carrier_validity(rho),
                "qutip_gap": float(np.max(np.abs(qutip_rho - rho))),
                "qiskit_gap": float(np.max(np.abs(qiskit_rho - rho))),
                "channel_qutip_gap": float(np.max(np.abs(out_qutip - out_np))),
                "channel_qiskit_gap": float(np.max(np.abs(out_qiskit - out_np))),
                "channel_output_validity": carrier_validity(out_np),
                "entropy_numpy": entropy_numpy(rho),
                "entropy_torch": entropy_torch(rho),
                "entropy_qutip": entropy_qutip(rho),
            }
        )

    identity_kraus = amplitude_damping_kraus(0.0)
    full_damp_kraus = amplitude_damping_kraus(1.0)
    excited = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=np.complex128)
    ground = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=np.complex128)
    invalids = invalid_counterexamples()

    positive = {
        "parents_exist_and_pass": {"parents": parents, "pass": all(row["exists"] and row["all_pass"] for row in parents)},
        "same_carrier_roundtrips_across_qutip_qiskit": {
            "state_rows": state_rows,
            "pass": all(row["validity"]["pass"] and row["qutip_gap"] < 1e-12 and row["qiskit_gap"] < 1e-12 for row in state_rows),
        },
        "same_channel_action_agrees_across_numpy_qutip_qiskit": {
            "gamma": gamma,
            "max_qutip_gap": max(row["channel_qutip_gap"] for row in state_rows),
            "max_qiskit_gap": max(row["channel_qiskit_gap"] for row in state_rows),
            "pass": all(
                row["channel_qutip_gap"] < 1e-12
                and row["channel_qiskit_gap"] < 1e-12
                and row["channel_output_validity"]["pass"]
                for row in state_rows
            ),
        },
        "entropy_agrees_across_numpy_torch_qutip": {
            "max_numpy_torch_gap": max(abs(row["entropy_numpy"] - row["entropy_torch"]) for row in state_rows),
            "max_numpy_qutip_gap": max(abs(row["entropy_numpy"] - row["entropy_qutip"]) for row in state_rows),
            "pass": all(
                abs(row["entropy_numpy"] - row["entropy_torch"]) < 1e-9
                and abs(row["entropy_numpy"] - row["entropy_qutip"]) < 1e-9
                for row in state_rows
            ),
        },
    }
    negative = {
        "invalid_carriers_are_rejected_by_finite_checks": {
            "invalids": invalids,
            "pass": all(row["pass"] for row in invalids.values()),
        },
        "wrong_identity_for_damping_is_detected": {
            "gamma": gamma,
            "error": float(np.max(np.abs(apply_kraus_numpy(states[1]["rho"], kraus_ops) - states[1]["rho"]))),
            "pass": float(np.max(np.abs(apply_kraus_numpy(states[1]["rho"], kraus_ops) - states[1]["rho"]))) > 0.05,
        },
        "wrong_unitary_only_model_fails_dissipative_channel": {
            "error": float(np.max(np.abs(apply_kraus_numpy(excited, full_damp_kraus) - excited))),
            "pass": float(np.max(np.abs(apply_kraus_numpy(excited, full_damp_kraus) - excited))) > 0.9,
        },
    }
    boundary = {
        "finite_one_qubit_carrier_only": {"state_count": len(states), "dimension": 2, "pass": len(states) == 4},
        "zero_damping_is_identity": {
            "error": float(np.max(np.abs(apply_kraus_numpy(states[0]["rho"], identity_kraus) - states[0]["rho"]))),
            "pass": float(np.max(np.abs(apply_kraus_numpy(states[0]["rho"], identity_kraus) - states[0]["rho"]))) < 1e-12,
        },
        "full_damping_maps_excited_state_to_ground": {
            "error": float(np.max(np.abs(apply_kraus_numpy(excited, full_damp_kraus) - ground))),
            "pass": float(np.max(np.abs(apply_kraus_numpy(excited, full_damp_kraus) - ground))) < 1e-12,
        },
        "not_admission_or_promotion": {
            "classification": "classical_baseline",
            "promotion_allowed": False,
            "pass": True,
        },
        "no_qit_gstack_axis_bridge_or_nonclassical_promotion": {
            "claim_ceiling": "finite density-carrier tool closure only",
            "pass": True,
        },
    }

    all_pass = all(item["pass"] for group in (positive, negative, boundary) for item in group.values())
    result = {
        "name": "density_carrier_qutip_qiskit_closure",
        "classification": "classical_baseline",
        "classification_note": "Finite density-carrier closure across torch, QuTiP, Qiskit, and numpy; lego-stage evidence only.",
        "generated_at": datetime.now(UTC).isoformat(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "parents": parents,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "closure_candidate": all_pass,
            "promotion_allowed": False,
            "state_count": len(states),
            "max_channel_qutip_gap": positive["same_channel_action_agrees_across_numpy_qutip_qiskit"]["max_qutip_gap"],
            "max_channel_qiskit_gap": positive["same_channel_action_agrees_across_numpy_qutip_qiskit"]["max_qiskit_gap"],
            "scope_note": "One-qubit finite density carrier and channel action only; no stage promotion.",
        },
        "divergence_log": (
            "The same density carrier and amplitude-damping channel roundtrip across numpy, torch, "
            "QuTiP, and Qiskit; trace-bad, non-Hermitian, negative-spectrum, identity, and "
            "unitary-only controls prevent carrier overclaim."
        ),
        "all_pass": all_pass,
    }
    result = apply_default_receipt_boundary(
        result,
        source_name="sim_density_carrier_qutip_qiskit_closure",
        target="Use as bounded density-carrier tool-closure evidence before broader assembly.",
    )
    result["promotion_condition"] = "Requires downstream density-carrier assembly audit and explicit stage-gate admission."
    result["blocked_until"] = "density-carrier assembly audit and stage-gate admission"
    OUT_PATH.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {OUT_PATH}")
    print(f"ALL PASS: {all_pass}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
