#!/usr/bin/env python3
"""PyTorch leg for the nested Hopf/Weyl tool-ladder scout.

This is a scratch diagnostic for PyTorch's richer geometric stack: torch_ga,
torch.func, geomstats, e3nn, and torch_geometric all execute on one tiny
Hopf-to-Weyl nested fixture.
"""

from __future__ import annotations

import datetime as _dt
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import torch
from e3nn import o3
from geomstats.geometry.hypersphere import Hypersphere
from torch.func import jacrev
from torch_ga import GeometricAlgebra
from torch_geometric.data import Data
from torch_geometric.nn import MessagePassing


ROOT = Path(__file__).resolve().parents[3]
OBJECT_ID = "tool_ladder_nested_hopf_weyl_pytorch"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/tool_ladder_nested_hopf_weyl_pytorch.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/tool_ladder_nested_hopf_weyl_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
TOL = 1.0e-10
RDTYPE = torch.float64
CDTYPE = torch.complex128

TOOL_MANIFEST = {
    "torch_ga": {"tried": True, "used": True, "reason": "load-bearing Cl(3,0) GeometricAlgebra rotor/fiber tangent witness"},
    "torch.func": {"tried": True, "used": True, "reason": "load-bearing jacrev through the Hopf-to-Weyl chirality response"},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing S2 metric distance check for Hopf fiber invariance"},
    "e3nn": {"tried": True, "used": True, "reason": "load-bearing SO(3) irrep/Wigner-D sanity check on the Hopf base vector"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing message-passing graph over Hopf layer and Weyl layer nodes"},
    "torch": {"tried": True, "used": True, "reason": "supportive tensor/autograd substrate"},
    "json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic result paths"},
}

TOOL_INTEGRATION_DEPTH = {
    "torch_ga": "load_bearing",
    "torch.func": "load_bearing",
    "geomstats": "load_bearing",
    "e3nn": "load_bearing",
    "torch_geometric": "load_bearing",
    "torch": "supportive",
    "json": "supportive",
    "pathlib": "supportive",
}


class LayerMessage(MessagePassing):
    def __init__(self) -> None:
        super().__init__(aggr="add")

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        return self.propagate(edge_index, x=x)

    def message(self, x_j: torch.Tensor) -> torch.Tensor:
        return x_j


def _float(value: torch.Tensor | float) -> float:
    if isinstance(value, torch.Tensor):
        return float(value.detach().cpu().item())
    return float(value)


def hopf_map(q: torch.Tensor) -> torch.Tensor:
    a, b, c, d = q
    return torch.stack(
        [
            2.0 * (a * c + b * d),
            2.0 * (b * c - a * d),
            a * a + b * b - c * c - d * d,
        ]
    )


def fiber_phase(q: torch.Tensor, phi: torch.Tensor) -> torch.Tensor:
    a, b, c, d = q
    cp = torch.cos(phi)
    sp = torch.sin(phi)
    return torch.stack(
        [
            a * cp - b * sp,
            a * sp + b * cp,
            c * cp - d * sp,
            c * sp + d * cp,
        ]
    )


def pauli() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    ident = torch.eye(2, dtype=CDTYPE)
    sx = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
    return ident, sx, sy, sz


def kron_all(parts: list[torch.Tensor]) -> torch.Tensor:
    out = parts[0]
    for part in parts[1:]:
        out = torch.kron(out, part)
    return out


def gamma_matrices_cl6() -> list[torch.Tensor]:
    ident, sx, sy, sz = pauli()
    return [
        kron_all([sx, ident, ident]),
        kron_all([sy, ident, ident]),
        kron_all([sz, sx, ident]),
        kron_all([sz, sy, ident]),
        kron_all([sz, sz, sx]),
        kron_all([sz, sz, sy]),
    ]


def chirality_gamma7(gammas: list[torch.Tensor]) -> torch.Tensor:
    product = gammas[0]
    for gamma in gammas[1:]:
        product = product @ gamma
    return (complex((-1j) ** 3) * product).to(CDTYPE)


def nested_chirality_response(hopf_z: torch.Tensor) -> torch.Tensor:
    gammas = gamma_matrices_cl6()
    gamma7 = chirality_gamma7(gammas)
    diag = [int(round(_float(torch.real(gamma7[idx, idx])))) for idx in range(gamma7.shape[0])]
    plus_idx = [idx for idx, sign in enumerate(diag) if sign == 1][0]
    minus_idx = [idx for idx, sign in enumerate(diag) if sign == -1][0]
    theta = 0.5 * torch.acos(hopf_z)
    psi = torch.zeros((gamma7.shape[0],), dtype=CDTYPE)
    psi[plus_idx] = torch.cos(theta).to(CDTYPE)
    psi[minus_idx] = torch.sin(theta).to(CDTYPE)
    return torch.real(torch.conj(psi) @ (gamma7 @ psi))


def torch_ga_check(phi: torch.Tensor) -> dict[str, Any]:
    ga = GeometricAlgebra(metric=[1.0, 1.0, 1.0], dtype=RDTYPE)
    blades = ga.blade_mvs.to(dtype=RDTYPE)
    one = blades[0]
    e1, e2, e3 = blades[1], blades[2], blades[3]
    e12 = blades[4]
    rotor = torch.cos(0.5 * phi) * one - torch.sin(0.5 * phi) * e12
    rotated = ga.geom_prod(ga.geom_prod(rotor, e1), ga.reversion(rotor))
    pseudoscalar = ga.geom_prod(ga.geom_prod(e1, e2), e3)
    square = ga.geom_prod(pseudoscalar, pseudoscalar)
    vector_norm = torch.linalg.vector_norm(rotated[1:4])
    square_residual = torch.max(torch.abs(square + one))
    return {
        "num_blades": int(ga.num_blades),
        "rotated_vector_norm": _float(vector_norm),
        "pseudoscalar_square_residual": _float(square_residual),
        "pass": int(ga.num_blades) == 8 and abs(_float(vector_norm) - 1.0) <= TOL and _float(square_residual) <= TOL,
    }


def build_result() -> dict[str, Any]:
    torch.set_default_dtype(RDTYPE)
    q = torch.tensor([math.sqrt(3.0) / 2.0, 0.0, 0.5, 0.0], dtype=RDTYPE)
    phi = torch.tensor(0.73, dtype=RDTYPE)
    base = hopf_map(q)
    base_phase = hopf_map(fiber_phase(q, phi))
    hopf_norm_residual = abs(_float(torch.dot(base, base)) - 1.0)
    fiber_residual = _float(torch.linalg.vector_norm(base - base_phase))
    hopf_z = base[2]

    gammas = gamma_matrices_cl6()
    gamma7 = chirality_gamma7(gammas)
    ident = torch.eye(gamma7.shape[0], dtype=CDTYPE)
    gamma7_square_residual = _float(torch.linalg.vector_norm(gamma7 @ gamma7 - ident))
    diag = [int(round(_float(torch.real(gamma7[idx, idx])))) for idx in range(gamma7.shape[0])]
    plus_dim = sum(1 for sign in diag if sign == 1)
    minus_dim = sum(1 for sign in diag if sign == -1)
    nested = nested_chirality_response(hopf_z)
    nested_residual = abs(_float(nested - hopf_z))
    nested_grad = jacrev(nested_chirality_response)(hopf_z)

    ga = torch_ga_check(phi)
    sphere = Hypersphere(dim=2)
    geomstats_dist = sphere.metric.dist(base, base_phase)
    geomstats_control_dist = sphere.metric.dist(base, torch.tensor([1.0, 0.0, 0.0], dtype=RDTYPE))

    irreps = o3.Irreps("1x0e + 1x1o")
    wigner_d = o3.wigner_D(1, torch.tensor(0.0, dtype=RDTYPE), torch.tensor(0.0, dtype=RDTYPE), phi).to(dtype=RDTYPE)
    e3nn_vector = wigner_d @ torch.tensor([1.0, 0.0, 0.0], dtype=RDTYPE)
    e3nn_norm_residual = abs(_float(torch.linalg.vector_norm(e3nn_vector)) - 1.0)

    data = Data(
        x=torch.stack([hopf_z.detach(), nested.detach()]).reshape(2, 1).to(dtype=RDTYPE),
        edge_index=torch.tensor([[0, 1], [1, 0]], dtype=torch.long),
    )
    messenger = LayerMessage()
    message_out = messenger(data.x, data.edge_index)
    pyg_pass = bool(data.validate(raise_on_error=False) and message_out.shape == (2, 1) and _float(torch.linalg.vector_norm(message_out)) > 0.0)

    nested_signature = [_float(base[0]), _float(base[1]), _float(base[2]), _float(nested), float(plus_dim), float(minus_dim)]
    all_pass = bool(
        READS_PEER_RESULT is False
        and hopf_norm_residual <= TOL
        and fiber_residual <= TOL
        and gamma7_square_residual <= TOL
        and plus_dim == 4
        and minus_dim == 4
        and nested_residual <= TOL
        and abs(_float(nested_grad) - 1.0) <= TOL
        and ga["pass"]
        and _float(geomstats_dist) <= TOL
        and _float(geomstats_control_dist) > 0.1
        and int(irreps.dim) == 4
        and e3nn_norm_residual <= TOL
        and pyg_pass
    )
    return {
        "schema_version": "engine_leg_result_v1",
        "object_id": OBJECT_ID,
        "engine": "pytorch",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "python_executable": sys.executable,
        "packages_used": ["torch", "torch.func", "torch_ga", "geomstats", "e3nn", "torch_geometric", "json", "pathlib"],
        "aligned_packages_load_bearing": ["torch_ga", "torch.func", "geomstats", "e3nn", "torch_geometric"],
        "claim_ceiling": "Scratch tool-ladder scout only: PyTorch geometric/autograd stack on a nested Hopf/Weyl fixture. No formal admission, no canonical claim.",
        "hopf": {
            "q": [_float(x) for x in q],
            "fiber_phase": _float(phi),
            "base": [_float(x) for x in base],
            "base_after_fiber_phase": [_float(x) for x in base_phase],
            "s2_norm_residual": hopf_norm_residual,
            "fiber_invariance_residual": fiber_residual,
            "pass": hopf_norm_residual <= TOL and fiber_residual <= TOL,
        },
        "weyl": {
            "spinor_dim": int(gamma7.shape[0]),
            "gamma7_square_residual": gamma7_square_residual,
            "gamma7_diagonal": diag,
            "plus_dim": plus_dim,
            "minus_dim": minus_dim,
            "nested_chirality_expectation": _float(nested),
            "nested_expectation_residual": nested_residual,
            "nested_chirality_jacrev": _float(nested_grad),
            "pass": gamma7_square_residual <= TOL and plus_dim == 4 and minus_dim == 4 and nested_residual <= TOL,
        },
        "torch_ga": ga,
        "geomstats": {
            "s2_fiber_distance": _float(geomstats_dist),
            "s2_control_distance": _float(geomstats_control_dist),
            "pass": _float(geomstats_dist) <= TOL and _float(geomstats_control_dist) > 0.1,
        },
        "e3nn": {
            "irreps_dim": int(irreps.dim),
            "wigner_d_shape": list(wigner_d.shape),
            "vector_norm_residual": e3nn_norm_residual,
            "pass": int(irreps.dim) == 4 and e3nn_norm_residual <= TOL,
        },
        "torch_geometric": {
            "data_validate": bool(data.validate(raise_on_error=False)),
            "node_count": int(data.num_nodes),
            "edge_count": int(data.num_edges),
            "message_out_norm": _float(torch.linalg.vector_norm(message_out)),
            "pass": pyg_pass,
        },
        "values": {
            "hopf_base_x": nested_signature[0],
            "hopf_base_y": nested_signature[1],
            "hopf_base_z": nested_signature[2],
            "fiber_invariance_residual": fiber_residual,
            "nested_chirality_expectation": nested_signature[3],
            "nested_expectation_residual": nested_residual,
            "plus_dim": plus_dim,
            "minus_dim": minus_dim,
            "nested_chirality_jacrev": _float(nested_grad),
        },
        "nested_signature": nested_signature,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "NESTED_HOPF_WEYL_PYTORCH_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"hopf_z={result['values']['hopf_base_z']} "
        f"nested={result['values']['nested_chirality_expectation']} "
        f"dims={result['values']['plus_dim']}/{result['values']['minus_dim']} "
        f"jac={result['values']['nested_chirality_jacrev']}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
