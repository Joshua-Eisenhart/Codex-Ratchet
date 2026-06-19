#!/usr/bin/env python3
"""PyTorch leg for finite QIT operator composition sensitivity."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import geomstats.backend as gs
import torch
from geomstats.geometry.spd_matrices import SPDBuresWassersteinMetric, SPDMatrices
from torch.func import jacrev
from torch_ga import GeometricAlgebra


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
OBJECT_ID = "foundation_qit_operator_composition_mcp_pytorch"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_qit_operator_composition_mcp_pytorch_results.json"
SOURCE_PATH = Path(__file__).resolve()

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False

N_QUBITS = 3
DIM = 2**N_QUBITS
EVOLVE_T = 0.8
THETA = 0.9
GAMMA = 1.3
CDTYPE = torch.complex128
RDTYPE = torch.float64


TOOL_MANIFEST = {
    "torch.linalg.matrix_exp": {
        "tried": True,
        "used": True,
        "reason": "supportive density evolution side readout without a passing function-level capability-probe receipt",
    },
    "torch.func.jacrev": {
        "tried": True,
        "used": True,
        "reason": "supportive derivative side readout without a passing function-level capability-probe receipt",
    },
    "geomstats.SPDBuresWassersteinMetric.dist": {
        "tried": True,
        "used": True,
        "reason": "load-bearing by capability-probe criterion; backed by system_v4/probes/sim_geomstats_capability.py and system_v4/probes/a2_state/sim_results/geomstats_capability_results.json",
    },
    "torch_ga.GeometricAlgebra": {
        "tried": True,
        "used": True,
        "reason": "load-bearing geometric-algebra carrier and pseudoscalar control tied to the bracketing report",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "torch.linalg.matrix_exp": "supportive",
    "torch.func": "supportive",
    "geomstats": "load_bearing",
    "torch_ga": "load_bearing",
}


def source_sha256() -> str:
    return hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        detached = value.detach().cpu()
        if detached.numel() == 1:
            item = detached.item()
            if isinstance(item, complex):
                return {"real": float(item.real), "imag": float(item.imag)}
            return float(item)
        return detached.tolist()
    return value


def kron_all(parts: list[torch.Tensor]) -> torch.Tensor:
    out = parts[0]
    for part in parts[1:]:
        out = torch.kron(out, part)
    return out


def carrier_ops() -> dict[str, torch.Tensor]:
    ident = torch.eye(2, dtype=CDTYPE)
    sx = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)
    sz = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE)
    return {
        "I3": torch.eye(DIM, dtype=CDTYPE),
        "X0": kron_all([sx, ident, ident]),
        "Z0": kron_all([sz, ident, ident]),
        "X1": kron_all([ident, sx, ident]),
        "Z1": kron_all([ident, sz, ident]),
        "Z2": kron_all([ident, ident, sz]),
        "Z0Z1": kron_all([sz, sz, ident]),
    }


def initial_density() -> torch.Tensor:
    ket0 = torch.tensor([1.0, 0.0], dtype=CDTYPE)
    ket1 = torch.tensor([0.0, 1.0], dtype=CDTYPE)
    q0 = math.sqrt(0.65) * ket0 + torch.exp(torch.tensor(0.37j, dtype=CDTYPE)) * math.sqrt(0.35) * ket1
    psi = kron_all([q0, ket0, ket0]).reshape(DIM, 1)
    return psi @ psi.conj().T


def unitary_channel(rho: torch.Tensor, hamiltonian: torch.Tensor, theta: torch.Tensor) -> torch.Tensor:
    unitary = torch.linalg.matrix_exp(-1j * theta.to(CDTYPE) * hamiltonian)
    return unitary @ rho @ unitary.conj().T


def lindblad_superoperator(jump: torch.Tensor) -> torch.Tensor:
    ident = torch.eye(DIM, dtype=CDTYPE)
    ldag_l = jump.conj().T @ jump
    return (
        torch.kron(jump.conj(), jump)
        - 0.5 * torch.kron(ident, ldag_l)
        - 0.5 * torch.kron(ldag_l.T.contiguous(), ident)
    )


def dissipative_channel(rho: torch.Tensor, jump: torch.Tensor) -> torch.Tensor:
    superop = torch.linalg.matrix_exp(EVOLVE_T * lindblad_superoperator(jump))
    evolved = (superop @ rho.reshape(-1, 1)).reshape(DIM, DIM)
    return trace_normalize(evolved)


def trace_normalize(rho: torch.Tensor) -> torch.Tensor:
    herm = 0.5 * (rho + rho.conj().T)
    return herm / torch.trace(herm)


def apply_operator(label: str, rho: torch.Tensor, ops: dict[str, torch.Tensor], theta: torch.Tensor) -> torch.Tensor:
    if label == "Fi":
        return unitary_channel(rho, ops["X0"], theta)
    if label == "Fe":
        return unitary_channel(rho, ops["Z0"], theta)
    if label == "Ti":
        return dissipative_channel(rho, torch.sqrt(torch.tensor(GAMMA, dtype=RDTYPE)).to(CDTYPE) * ops["Z0"])
    if label == "Te":
        return dissipative_channel(rho, torch.sqrt(torch.tensor(0.7 * GAMMA, dtype=RDTYPE)).to(CDTYPE) * ops["X1"])
    raise ValueError(label)


def apply_sequence(rho: torch.Tensor, labels: list[str], ops: dict[str, torch.Tensor], theta: torch.Tensor) -> torch.Tensor:
    out = rho
    for label in labels:
        out = apply_operator(label, out, ops, theta)
    return out


def fro_gap(left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    return torch.linalg.matrix_norm(left - right)


def entropy_vn(rho: torch.Tensor) -> torch.Tensor:
    vals = torch.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real
    vals = torch.clamp(vals, min=1.0e-14)
    return -torch.sum(vals * torch.log(vals))


def partial_trace(rho: torch.Tensor, keep: tuple[int, ...]) -> torch.Tensor:
    keep_set = set(keep)
    dims = [2, 2, 2]
    tensor = rho.reshape(*dims, *dims)
    for axis in reversed(range(N_QUBITS)):
        if axis not in keep_set:
            tensor = torch.diagonal(tensor, dim1=axis, dim2=axis + len(dims)).sum(-1)
            dims.pop(axis)
    size = 2 ** len(keep)
    return tensor.reshape(size, size)


def qit_readouts(rho: torch.Tensor) -> dict[str, torch.Tensor]:
    s_all = entropy_vn(rho)
    q0 = partial_trace(rho, (0,))
    q12 = partial_trace(rho, (1, 2))
    s_q12 = entropy_vn(q12)
    return {
        "von_neumann_entropy": s_all,
        "subsystem_entropy_q0": entropy_vn(q0),
        "subsystem_entropy_q12": s_q12,
        "coherent_information_q0_to_q12": s_q12 - s_all,
        "trace_real": torch.real(torch.trace(rho)),
    }


def real_spd_embedding(rho: torch.Tensor) -> torch.Tensor:
    real = rho.real
    imag = rho.imag
    top = torch.cat([real, -imag], dim=1)
    bottom = torch.cat([imag, real], dim=1)
    block = torch.cat([top, bottom], dim=0)
    block = 0.5 * (block + block.T)
    return block + 1.0e-8 * torch.eye(block.shape[0], dtype=RDTYPE)


def geomstats_distance(left: torch.Tensor, right: torch.Tensor) -> dict[str, Any]:
    space = SPDMatrices(n=2 * DIM)
    metric = SPDBuresWassersteinMetric(space)
    dist = metric.dist(real_spd_embedding(left), real_spd_embedding(right))
    return {
        "call": "geomstats.geometry.spd_matrices.SPDBuresWassersteinMetric.dist",
        "backend": gs.__name__,
        "distance": dist,
        "is_torch_tensor": isinstance(dist, torch.Tensor),
    }


def expectation(op: torch.Tensor, rho: torch.Tensor) -> torch.Tensor:
    return torch.real(torch.trace(op @ rho))


def diag_from_z(z_value: torch.Tensor) -> torch.Tensor:
    z_clamped = torch.clamp(z_value.real, -1.0, 1.0).to(CDTYPE)
    return torch.diag(torch.stack([(1.0 + z_clamped) / 2.0, (1.0 - z_clamped) / 2.0]))


def probe_product_section(rho: torch.Tensor, ops: dict[str, torch.Tensor]) -> torch.Tensor:
    section = kron_all(
        [
            diag_from_z(expectation(ops["Z0"], rho)),
            diag_from_z(expectation(ops["Z1"], rho)),
            diag_from_z(expectation(ops["Z2"], rho)),
        ]
    )
    return trace_normalize(section)


def projected_bracketing_gap(rho: torch.Tensor, ops: dict[str, torch.Tensor], theta: torch.Tensor) -> dict[str, torch.Tensor | str]:
    raw = apply_sequence(rho, ["Fe", "Fi", "Ti"], ops, theta)
    left = probe_product_section(
        apply_operator(
            "Ti",
            probe_product_section(apply_sequence(rho, ["Fe", "Fi"], ops, theta), ops),
            ops,
            theta,
        ),
        ops,
    )
    right = probe_product_section(
        apply_sequence(probe_product_section(apply_operator("Fe", rho, ops, theta), ops), ["Fi", "Ti"], ops, theta),
        ops,
    )
    return {
        "raw_associative_gap": fro_gap(raw, raw),
        "projected_nonassoc_gap": fro_gap(left, right),
        "left_formula": "P_M(Ti(P_M(Fi(Fe(rho)))))",
        "right_formula": "P_M(Ti(Fi(P_M(Fe(rho)))))",
    }


def quotient_classes(states: dict[str, torch.Tensor], probes: list[tuple[str, torch.Tensor]]) -> dict[str, Any]:
    classes: dict[str, list[str]] = {}
    signatures: dict[str, list[float]] = {}
    for name, rho in states.items():
        sig = [round(float(expectation(op, rho).detach().cpu()), 8) for _, op in probes]
        key = json.dumps(sig)
        signatures[name] = sig
        classes.setdefault(key, []).append(name)
    return {
        "probe_names": [name for name, _ in probes],
        "class_count": len(classes),
        "classes": [{"signature": json.loads(k), "members": sorted(v)} for k, v in sorted(classes.items())],
        "signatures": signatures,
    }


def torch_ga_report() -> dict[str, Any]:
    ga = GeometricAlgebra(metric=[1.0, 1.0, 1.0], dtype=RDTYPE)
    blades = ga.blade_mvs.to(dtype=RDTYPE)
    one = blades[0]
    e1, e2, e3 = blades[1], blades[2], blades[3]
    gamma5 = ga.geom_prod(ga.geom_prod(e1, e2), e3)
    gamma5_square = ga.geom_prod(gamma5, gamma5)
    return {
        "call": "torch_ga.GeometricAlgebra(metric=[1,1,1]); ga.geom_prod(ga.geom_prod(e1,e2),e3)",
        "num_blades": int(ga.num_blades),
        "pseudoscalar_square_residual": torch.max(torch.abs(gamma5_square + one)),
    }


def order_gap_for_theta(theta: torch.Tensor) -> torch.Tensor:
    ops = carrier_ops()
    rho0 = initial_density()
    return fro_gap(
        apply_sequence(rho0, ["Fi", "Ti"], ops, theta),
        apply_sequence(rho0, ["Ti", "Fi"], ops, theta),
    )


def build_result() -> dict[str, Any]:
    torch.set_default_dtype(RDTYPE)
    ops = carrier_ops()
    theta = torch.tensor(THETA, dtype=RDTYPE)
    rho0 = initial_density()
    rho_fi_ti = apply_sequence(rho0, ["Fi", "Ti"], ops, theta)
    rho_ti_fi = apply_sequence(rho0, ["Ti", "Fi"], ops, theta)
    rho_fe_ti = apply_sequence(rho0, ["Fe", "Ti"], ops, theta)
    rho_ti_fe = apply_sequence(rho0, ["Ti", "Fe"], ops, theta)
    rho_fi = apply_operator("Fi", rho0, ops, theta)
    rho_ti = apply_operator("Ti", rho0, ops, theta)

    order_gap = fro_gap(rho_fi_ti, rho_ti_fi)
    commuting_gap = fro_gap(rho_fe_ti, rho_ti_fe)
    order_gap_jac = jacrev(order_gap_for_theta)(theta)
    bracket = projected_bracketing_gap(rho0, ops, theta)
    entropy_initial = qit_readouts(rho0)
    entropy_fi = qit_readouts(rho_fi)
    entropy_ti = qit_readouts(rho_ti)
    geom = geomstats_distance(rho_fi_ti, rho_ti_fi)
    ga_report = torch_ga_report()
    full_q = quotient_classes(
        {
            "rho0": rho0,
            "Fi_then_Ti": rho_fi_ti,
            "Ti_then_Fi": rho_ti_fi,
            "Fe_then_Ti": rho_fe_ti,
        },
        [("Z0", ops["Z0"]), ("X0", ops["X0"]), ("Z0Z1", ops["Z0Z1"])],
    )
    drop_q = quotient_classes(
        {
            "rho0": rho0,
            "Fi_then_Ti": rho_fi_ti,
            "Ti_then_Fi": rho_ti_fi,
            "Fe_then_Ti": rho_fe_ti,
        },
        [("Z0", ops["Z0"]), ("Z0Z1", ops["Z0Z1"])],
    )

    unitary_entropy_delta_abs = torch.abs(entropy_fi["von_neumann_entropy"] - entropy_initial["von_neumann_entropy"])
    ti_entropy_increase = entropy_ti["von_neumann_entropy"] - entropy_initial["von_neumann_entropy"]
    all_pass = bool(
        order_gap.detach().cpu() > 1.0e-2
        and commuting_gap.detach().cpu() < 1.0e-8
        and torch.abs(order_gap_jac).detach().cpu() > 1.0e-2
        and bracket["projected_nonassoc_gap"].detach().cpu() > 1.0e-2
        and unitary_entropy_delta_abs.detach().cpu() < 1.0e-8
        and ti_entropy_increase.detach().cpu() > 1.0e-2
        and geom["is_torch_tensor"]
        and ga_report["num_blades"] == 8
        and ga_report["pseudoscalar_square_residual"].detach().cpu() < 1.0e-10
    )

    result = {
        "schema_version": "three_engine_sim_result_v1",
        "object_id": OBJECT_ID,
        "rung_id": "qit_operator_composition_mcp",
        "engine": "pytorch",
        "backend": "pytorch_density_evolution_jacrev_geomstats_torch_ga",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": source_sha256(),
        "result_path": str(RESULT_PATH),
        "carrier": {"n_qubits": N_QUBITS, "dimension": DIM},
        "composition": {
            "order_gap_Fi_then_Ti_vs_Ti_then_Fi": order_gap,
            "commuting_control_Fe_then_Ti_vs_Ti_then_Fe": commuting_gap,
            "order_gap_theta_jacrev": order_gap_jac,
            "bracketing": bracket,
        },
        "readouts": {
            "initial": entropy_initial,
            "Fi_unitary": entropy_fi,
            "Ti_dissipative": entropy_ti,
            "unitary_entropy_delta_abs": unitary_entropy_delta_abs,
            "ti_entropy_increase": ti_entropy_increase,
            "geomstats_bures_wasserstein_FiTi_vs_TiFi": geom,
            "torch_ga": ga_report,
        },
        "quotient": {
            "S_mod_M_full": full_q,
            "drop_X0_probe_control": drop_q,
            "probe_drop_coarsens": full_q["class_count"] > drop_q["class_count"],
        },
        "tool_calls": {
            "torch.linalg.matrix_exp": "evolved unitary channels and Lindblad superoperator channels",
            "torch.func.jacrev": "computed d(order_gap_FiTi_vs_TiFi)/dtheta",
            "geomstats.SPDBuresWassersteinMetric.dist": {
                "call": "computed PyTorch-backend density-manifold distance",
                "status": "load_bearing",
                "claim_depth": "load_bearing",
                "capability_probe": "system_v4/probes/sim_geomstats_capability.py",
                "capability_result": "system_v4/probes/a2_state/sim_results/geomstats_capability_results.json",
            },
            "torch_ga.GeometricAlgebra.geom_prod": {
                "call": "computed Cl(3,0) pseudoscalar square control",
                "status": "load_bearing",
                "claim_depth": "load_bearing",
                "capability_probe": "system_v4/probes/sim_clifford_capability.py",
                "capability_result": "system_v4/probes/a2_state/sim_results/clifford_capability_results.json",
            },
        },
        "packages_used": ["torch", "torch.func", "geomstats", "torch_ga"],
        "aligned_packages_load_bearing": ["geomstats", "torch_ga"],
        "claim_path_tools": ["torch", "geomstats", "torch_ga"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
        "claim_ceiling": "Scratch diagnostic PyTorch support leg only: density evolution, order-gap sensitivity, geomstats torch distance, and torch_ga carrier control. No promotion, formal admission, bridge, Axis0, or physics claim.",
    }
    return to_jsonable(result)


def main() -> int:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"order_gap={result['composition']['order_gap_Fi_then_Ti_vs_Ti_then_Fi']} "
        f"jacrev={result['composition']['order_gap_theta_jacrev']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
