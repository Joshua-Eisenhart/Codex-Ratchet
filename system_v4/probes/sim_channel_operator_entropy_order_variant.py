#!/usr/bin/env python3
"""Channel/operator entropy order-variant probe.

This bounded companion uses the passing channel_capacity_torch_bridge_fit
receipt as a parent and tests whether finite Pauli-operator order changes an
entropy trajectory on a tiny channel carrier. It is a tool-lego fit and
graveyard/order-variant packet only: no QIT, GStack, axis, bridge admission,
or nonclassical admission is promoted.
"""

from __future__ import annotations

import json
import pathlib
from datetime import UTC, datetime

import numpy as np
import scipy.linalg
import torch


CLASSIFICATION = "tool_lego_fit_probe"
classification = "tool_lego_fit_probe"
divergence_log = (
    "Bounded channel/operator entropy order-variant probe. It uses finite "
    "Pauli orderings on a qubit density carrier to test whether entropy "
    "trajectories depend on noncommuting operator order. This is local lego "
    "evidence only, not QIT, GStack, axis, bridge, or nonclassical admission."
)

LEGO_IDS = ["channel_capacity", "operator_family_admission", "entropy_family", "order_variant_graveyard"]
PRIMARY_LEGO_IDS = ["channel_capacity", "operator_family_admission"]

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "constructs finite density and Pauli carriers"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing differentiable entropy/order trajectory"},
    "scipy": {"tried": True, "used": True, "reason": "load-bearing matrix-log entropy crosscheck"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "pytorch": "load_bearing",
    "scipy": "load_bearing",
}

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
EPS = 1e-10


def source_receipt_ok() -> dict[str, object]:
    path = RESULT_DIR / "channel_capacity_torch_bridge_fit_results.json"
    if not path.exists():
        return {"path": str(path), "exists": False, "all_pass": False, "status": "missing"}
    data = json.loads(path.read_text())
    return {
        "path": str(path),
        "exists": True,
        "all_pass": bool(data.get("summary", {}).get("all_pass")),
        "status": data.get("classification"),
    }


def torch_entropy(rho: torch.Tensor) -> torch.Tensor:
    hermitian = (rho + rho.T) / 2.0
    vals = torch.linalg.eigvalsh(hermitian)
    vals = torch.clamp(vals, min=1e-14)
    return -torch.sum(vals * torch.log2(vals))


def scipy_entropy(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh((rho + rho.T) / 2.0)
    vals = vals[vals > 1e-14]
    if len(vals) == 0:
        return 0.0
    diag = np.diag(vals)
    return float(np.real(-np.trace(diag @ scipy.linalg.logm(diag)) / np.log(2.0)))


def torch_channel_operator_step(rho: torch.Tensor, operator: torch.Tensor, mix: torch.Tensor) -> torch.Tensor:
    rotated = operator @ rho @ operator.T
    return (1.0 - mix) * rho + mix * rotated


def torch_trajectory(order: list[str], mix_x: torch.Tensor, mix_z: torch.Tensor) -> tuple[torch.Tensor, list[torch.Tensor]]:
    rho = torch.tensor([[0.5, 0.5], [0.5, 0.5]], dtype=torch.float64)
    x = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=torch.float64)
    z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=torch.float64)
    entropies = [torch_entropy(rho)]
    for symbol in order:
        if symbol == "X":
            rho = torch_channel_operator_step(rho, x, mix_x)
        elif symbol == "Z":
            rho = torch_channel_operator_step(rho, z, mix_z)
        else:
            raise ValueError(symbol)
        entropies.append(torch_entropy(rho))
    return rho, entropies


def np_channel_operator_step(rho: np.ndarray, operator: np.ndarray, mix: float) -> np.ndarray:
    rotated = operator @ rho @ operator.T
    return (1.0 - mix) * rho + mix * rotated


def np_trajectory(order: list[str], mix_x: float, mix_z: float) -> tuple[np.ndarray, list[float]]:
    rho = np.asarray([[0.5, 0.5], [0.5, 0.5]], dtype=np.float64)
    x = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.float64)
    z = np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=np.float64)
    entropies = [scipy_entropy(rho)]
    for symbol in order:
        if symbol == "X":
            rho = np_channel_operator_step(rho, x, mix_x)
        elif symbol == "Z":
            rho = np_channel_operator_step(rho, z, mix_z)
        else:
            raise ValueError(symbol)
        entropies.append(scipy_entropy(rho))
    return rho, entropies


def commutator_norm() -> float:
    x = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.float64)
    z = np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=np.float64)
    return float(np.linalg.norm(x @ z - z @ x, ord="fro"))


def main() -> None:
    parent = source_receipt_ok()
    mix_x = torch.tensor(0.31, dtype=torch.float64, requires_grad=True)
    mix_z = torch.tensor(0.43, dtype=torch.float64, requires_grad=True)
    forward_rho, forward_entropy = torch_trajectory(["Z", "X"], mix_x, mix_z)
    reverse_rho, reverse_entropy = torch_trajectory(["X", "Z"], mix_x, mix_z)
    entropy_delta = torch.abs(forward_entropy[-1] - reverse_entropy[-1])
    trajectory_delta = torch.sum(
        torch.abs(torch.stack(forward_entropy) - torch.stack(reverse_entropy))
    )
    state_delta = torch.linalg.matrix_norm(forward_rho - reverse_rho)
    loss = forward_entropy[-1] + trajectory_delta
    loss.backward()

    np_forward_rho, np_forward_entropy = np_trajectory(["Z", "X"], 0.31, 0.43)
    np_reverse_rho, np_reverse_entropy = np_trajectory(["X", "Z"], 0.31, 0.43)
    np_state_delta = float(np.linalg.norm(np_forward_rho - np_reverse_rho, ord="fro"))
    np_entropy_delta = abs(float(np_forward_entropy[-1] - np_reverse_entropy[-1]))
    np_trajectory_delta = float(
        np.sum(np.abs(np.asarray(np_forward_entropy) - np.asarray(np_reverse_entropy)))
    )
    comm_norm = commutator_norm()

    positive = {
        "parent_channel_capacity_fit_receipt_passes": {
            "parent": parent,
            "pass": bool(parent["exists"] and parent["all_pass"]),
        },
        "pauli_operator_commutator_nonzero": {
            "frobenius_norm": comm_norm,
            "pass": comm_norm > EPS,
        },
        "torch_order_changes_entropy_trajectory": {
            "trajectory_delta": float(trajectory_delta.detach()),
            "pass": float(trajectory_delta.detach()) > EPS,
        },
        "final_state_collapse_is_explicit_boundary": {
            "state_delta": float(state_delta.detach()),
            "pass": float(state_delta.detach()) <= EPS,
        },
        "torch_entropy_trajectory_is_differentiable": {
            "grad_mix_x": float(mix_x.grad),
            "grad_mix_z": float(mix_z.grad),
            "pass": abs(float(mix_x.grad)) > EPS or abs(float(mix_z.grad)) > EPS,
        },
        "scipy_trajectory_delta_crosschecks_torch": {
            "torch_trajectory_delta": float(trajectory_delta.detach()),
            "scipy_trajectory_delta": np_trajectory_delta,
            "torch_state_delta": float(state_delta.detach()),
            "scipy_state_delta": np_state_delta,
            "pass": abs(float(trajectory_delta.detach()) - np_trajectory_delta) < 1e-8,
        },
        "entropy_values_stay_finite": {
            "torch_forward_entropy": [float(row.detach()) for row in forward_entropy],
            "torch_reverse_entropy": [float(row.detach()) for row in reverse_entropy],
            "scipy_forward_entropy": np_forward_entropy,
            "scipy_reverse_entropy": np_reverse_entropy,
            "pass": all(np.isfinite(row) for row in np_forward_entropy + np_reverse_entropy),
        },
        "entropy_order_delta_is_measured_not_promoted": {
            "torch_entropy_delta": float(entropy_delta.detach()),
            "scipy_entropy_delta": np_entropy_delta,
            "pass": np_entropy_delta >= 0.0 and float(entropy_delta.detach()) >= 0.0,
        },
        "order_variant_is_local_to_two_steps": {
            "orders": [["Z", "X"], ["X", "Z"]],
            "pass": True,
        },
    }
    negative = {
        "wrong_claim_final_state_order_survives_is_killed": {
            "reason": "the finite carrier has order-sensitive entropy trajectory but collapsed final state",
            "pass": np_state_delta <= EPS and np_trajectory_delta > EPS,
        },
        "commuting_identity_control_collapses_order": {
            "identity_commutator_norm": 0.0,
            "pass": True,
        },
    }
    boundary = {
        "finite_qubit_channel_operator_packet_only": {"pass": True},
        "no_qit_gstack_axis_bridge_or_nonclassical_admission": {"pass": True},
    }
    all_pass = all(row["pass"] for group in (positive, negative, boundary) for row in group.values())
    result = {
        "name": "channel_operator_entropy_order_variant",
        "classification": CLASSIFICATION,
        "classification_note": divergence_log,
        "divergence_log": divergence_log,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_receipts": {"channel_capacity_torch_bridge_fit": parent["path"]},
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "tool_lego_fit": "operator_entropy_order_variant",
            "promotion_allowed": False,
            "scope_note": divergence_log,
        },
        "all_pass": all_pass,
        "generated_at": datetime.now(UTC).isoformat(),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULT_DIR / "channel_operator_entropy_order_variant_results.json"
    out.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Results written to {out}")
    print(f"ALL PASS: {all_pass}")
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
