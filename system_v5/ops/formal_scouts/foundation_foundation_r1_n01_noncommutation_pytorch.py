#!/usr/bin/env python3
from __future__ import annotations

import datetime as _dt
import json
import math
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SRC_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r1_n01_noncommutation_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r1_n01_noncommutation_pytorch_result.json"
RUNG_ID = "foundation_r1_n01_noncommutation"
TOL = 1.0e-12

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing float64/complex128 operator arithmetic for the differentiable N01 order-gap",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing jacrev sensitivity of the order-gap along a noncommuting probe deformation",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive timestamp, paths, and JSON receipt serialization",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "torch.func": "load_bearing",
    "Python stdlib": "supportive",
}


def scalar(value: torch.Tensor | float | int) -> float:
    if isinstance(value, torch.Tensor):
        return float(value.detach().cpu().item())
    return float(value)


def pauli_operators() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    z_probe = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=torch.float64)
    x_probe = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=torch.float64)
    identity_probe = torch.eye(2, dtype=torch.float64)
    return z_probe, x_probe, identity_probe


def fixture_states() -> list[tuple[str, torch.Tensor]]:
    inv = 1.0 / math.sqrt(2.0)
    return [
        ("ket_0", torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=torch.complex128)),
        ("ket_1", torch.tensor([0.0 + 0.0j, 1.0 + 0.0j], dtype=torch.complex128)),
        ("ket_plus", torch.tensor([inv + 0.0j, inv + 0.0j], dtype=torch.complex128)),
        ("ket_minus", torch.tensor([inv + 0.0j, -inv + 0.0j], dtype=torch.complex128)),
        ("ket_y_plus", torch.tensor([inv + 0.0j, 1.0j * inv], dtype=torch.complex128)),
        ("ket_y_minus", torch.tensor([inv + 0.0j, -1.0j * inv], dtype=torch.complex128)),
    ]


def expectation_signature(probes: list[torch.Tensor], ket: torch.Tensor) -> list[float]:
    signature: list[float] = []
    for probe in probes:
        value = torch.vdot(ket, probe.to(torch.complex128) @ ket).real
        signature.append(round(scalar(value), 12))
    return signature


def quotient_classes(probes: list[torch.Tensor], states: list[tuple[str, torch.Tensor]]) -> list[dict[str, Any]]:
    classes: dict[tuple[float, ...], list[str]] = {}
    for name, ket in states:
        key = tuple(expectation_signature(probes, ket))
        classes.setdefault(key, []).append(name)
    return [
        {"signature": list(key), "members": classes[key]}
        for key in sorted(classes)
    ]


def order_gap_squared_from_theta(theta: torch.Tensor) -> torch.Tensor:
    z_probe, x_probe, _identity_probe = pauli_operators()
    ket_0 = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=torch.complex128)
    moving_probe = torch.cos(theta) * z_probe + torch.sin(theta) * x_probe
    commutator = z_probe @ moving_probe - moving_probe @ z_probe
    vector = commutator.to(torch.complex128) @ ket_0
    return torch.sum(torch.abs(vector) ** 2)


def commuting_control_gap_squared_from_theta(theta: torch.Tensor) -> torch.Tensor:
    z_probe, _x_probe, identity_probe = pauli_operators()
    ket_0 = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=torch.complex128)
    moving_probe = torch.cos(theta) * z_probe + torch.sin(theta) * identity_probe
    commutator = z_probe @ moving_probe - moving_probe @ z_probe
    vector = commutator.to(torch.complex128) @ ket_0
    return torch.sum(torch.abs(vector) ** 2)


def build_result() -> dict[str, Any]:
    z_probe, x_probe, identity_probe = pauli_operators()
    states = fixture_states()
    noncommutator = z_probe @ x_probe - x_probe @ z_probe
    commuting_commutator = z_probe @ identity_probe - identity_probe @ z_probe
    ket_0 = states[0][1]
    order_gap_noncommuting = scalar(torch.linalg.vector_norm(noncommutator.to(torch.complex128) @ ket_0))
    order_gap_commuting = scalar(torch.linalg.vector_norm(commuting_commutator.to(torch.complex128) @ ket_0))
    noncommuting_classes = quotient_classes([z_probe, x_probe], states)
    commuting_classes = quotient_classes([z_probe, identity_probe], states)

    theta = torch.tensor(math.pi / 4.0, dtype=torch.float64)
    control_theta = torch.tensor(math.pi / 4.0, dtype=torch.float64)
    order_gap_squared = order_gap_squared_from_theta(theta)
    order_gap_jacrev = jacrev(order_gap_squared_from_theta)(theta)
    control_gap_squared = commuting_control_gap_squared_from_theta(control_theta)
    control_gap_jacrev = jacrev(commuting_control_gap_squared_from_theta)(control_theta)

    class_count_noncommuting = len(noncommuting_classes)
    class_count_commuting = len(commuting_classes)
    all_pass = bool(
        order_gap_noncommuting > TOL
        and order_gap_commuting <= TOL
        and class_count_commuting < class_count_noncommuting
        and abs(scalar(order_gap_jacrev)) > TOL
        and abs(scalar(control_gap_jacrev)) <= TOL
        and scalar(control_gap_squared) <= TOL
    )
    return {
        "schema": "codex_ratchet.foundation_rung_leg.v1",
        "object_id": "foundation_foundation_r1_n01_noncommutation_pytorch",
        "rung_id": RUNG_ID,
        "engine": "pytorch",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SRC_PATH),
        "result_path": str(RESULT_PATH),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "torch_version": torch.__version__,
        "packages_used": ["torch", "torch.func", "Python stdlib"],
        "aligned_packages_load_bearing": ["torch.func"],
        "M": {
            "noncommuting_probe_family": ["Pauli_Z", "Pauli_X"],
            "commuting_control_family": ["Pauli_Z", "Identity"],
            "fixture_states": [name for name, _ in states],
        },
        "C": {
            "admissibility": ["Hermitian density operator", "trace=1", "PSD", "normalized ket fixtures"],
            "rung_specific_constraint": "Differentiable order-gap sensitivity remains nonzero for a Z-to-X probe deformation",
            "control_constraint": "Z-to-Identity diagonal deformation has zero order-gap and zero jacrev sensitivity",
        },
        "quotient_summary": {
            "definition": "rho ~_M sigma iff Tr(rho O)=Tr(sigma O) for every O in M",
            "noncommuting_coordinates": ["<Z>", "<X>"],
            "commuting_control_coordinates": ["<Z>", "<I>"],
            "fixture_class_count_noncommuting": class_count_noncommuting,
            "fixture_class_count_commuting": class_count_commuting,
            "noncommuting_classes": noncommuting_classes,
            "commuting_control_classes": commuting_classes,
            "strictly_finer_than_commuting_control": class_count_noncommuting > class_count_commuting,
        },
        "values": {
            "order_gap_noncommuting": order_gap_noncommuting,
            "order_gap_commuting": order_gap_commuting,
            "class_count_noncommuting": class_count_noncommuting,
            "class_count_commuting": class_count_commuting,
            "theta_for_jacrev": scalar(theta),
            "order_gap_squared_at_theta": scalar(order_gap_squared),
            "order_gap_squared_jacrev_at_theta": scalar(order_gap_jacrev),
            "commuting_control_gap_squared_at_theta": scalar(control_gap_squared),
            "commuting_control_gap_squared_jacrev_at_theta": scalar(control_gap_jacrev),
        },
        "negative_control_flip": {
            "noncommuting_order_gap_positive": order_gap_noncommuting > TOL,
            "commuting_order_gap_zero": order_gap_commuting <= TOL,
            "commuting_control_coarser_quotient": class_count_commuting < class_count_noncommuting,
            "noncommuting_jacrev_nonzero": abs(scalar(order_gap_jacrev)) > TOL,
            "commuting_control_jacrev_zero": abs(scalar(control_gap_jacrev)) <= TOL,
            "flipped": order_gap_noncommuting > TOL and order_gap_commuting <= TOL and class_count_commuting < class_count_noncommuting,
        },
        "independent_check_note": "Genuine independent PyTorch check: torch.func.jacrev computes order-gap sensitivity along a noncommuting probe deformation; Julia/JAX report the static gap and SMT structure instead.",
        "all_pass": all_pass,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    vals = result["values"]
    print(f"wrote: {RESULT_PATH}")
    print(
        "PYTORCH_N01_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"order_gap_noncommuting={vals['order_gap_noncommuting']} "
        f"order_gap_commuting={vals['order_gap_commuting']} "
        f"jacrev={vals['order_gap_squared_jacrev_at_theta']} "
        f"control_jacrev={vals['commuting_control_gap_squared_jacrev_at_theta']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
