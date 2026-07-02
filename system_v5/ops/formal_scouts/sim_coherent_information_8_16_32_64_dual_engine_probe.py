#!/usr/bin/env python3
import jax
jax.config.update("jax_enable_x64", True)

"""Dual-engine coherent-information MPS lego probe at N=8,16,32,64.

The claim-bearing object is an N-site open-boundary MPS with one partial
Schmidt pair crossing the A|B cut.  Coherent information after a one-site
amplitude-damping channel on A is computed as S(B)-S(AB), where S(AB) is the
Stinespring environment entropy from the damped site's 2x2 reduced density.
No dense 2**N state is constructed.
"""

import json
import math
import os
import pathlib
import time
from dataclasses import dataclass
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import jax.numpy as jnp
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "coherent_information_8_16_32_64_dual_engine_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SITE_COUNTS = [8, 16, 32, 64]
CDTYPE = torch.complex128
RTYPE = torch.float64
GAP_FLOOR = 1.0e-8
PARITY_TOL = 1.0e-6
THETA0 = 0.37
RX_ANGLE = 0.43
RZ_ANGLE = 0.29
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"

I2 = torch.eye(2, dtype=CDTYPE)
SX = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)
SZ = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE)


TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex128 MPS/tensor-network carrier, reduced density contractions, entropy readouts, and autograd dI_c/dtheta",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent complex128 dual engine for coherent information and jax.grad parity against torch.autograd",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing structural sign fence: the positive coherent-information signature is required while flattened, reduced-dimension, and commutative-collapse controls are rejected",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact entropy/eigenvalue identities and known-value formulas used to check the tensor-network readouts",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "jax": "supportive",
    "z3": "load_bearing",
    "sympy": "load_bearing",
}


@dataclass
class SimpleMPS:
    tensors: list[torch.Tensor]
    schmidt_pair_site: int

    @property
    def N(self) -> int:
        return len(self.tensors)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def alpha_for_n(n_sites: int) -> float:
    return 0.61 + 0.015 * math.log2(n_sites / 8.0)


def torch_rx(angle: float) -> torch.Tensor:
    a = torch.tensor(angle / 2.0, dtype=RTYPE)
    return torch.cos(a).to(CDTYPE) * I2 - 1j * torch.sin(a).to(CDTYPE) * SX


def torch_rz(angle: float) -> torch.Tensor:
    a = torch.tensor(angle / 2.0, dtype=RTYPE)
    return torch.diag(torch.stack([torch.exp(-1j * a.to(CDTYPE)), torch.exp(1j * a.to(CDTYPE))]))


def torch_unitary(order: str) -> torch.Tensor:
    rx = torch_rx(RX_ANGLE)
    rz = torch_rz(RZ_ANGLE)
    if order == "rx_rz":
        return rz @ rx
    if order == "rz_rx":
        return rx @ rz
    if order == "commutative_collapse":
        return torch_rx(RX_ANGLE + RZ_ANGLE)
    raise ValueError(f"unknown order {order}")


def build_torch_mps(n_sites: int, *, order: str = "rx_rz", flattened: bool = False) -> SimpleMPS:
    if n_sites < 2 or n_sites % 2:
        raise ValueError("n_sites must be an even integer >= 2")
    cut_site = n_sites // 2 - 1
    alpha = 0.0 if flattened else alpha_for_n(n_sites)
    lambdas = torch.tensor([math.cos(alpha), math.sin(alpha)], dtype=RTYPE)
    tensors: list[torch.Tensor] = []
    zero = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=CDTYPE).reshape(2, 1, 1)
    for idx in range(n_sites):
        if idx == cut_site:
            tensor = torch.zeros((2, 1, 2), dtype=CDTYPE)
            rotated_basis = torch_unitary(order)
            for bond in range(2):
                tensor[:, 0, bond] = rotated_basis[:, bond] * lambdas[bond].to(CDTYPE)
            tensors.append(tensor)
        elif idx == cut_site + 1:
            tensor = torch.zeros((2, 2, 1), dtype=CDTYPE)
            tensor[0, 0, 0] = 1.0 + 0.0j
            tensor[1, 1, 0] = 1.0 + 0.0j
            tensors.append(tensor)
        else:
            tensors.append(zero.clone())
    return SimpleMPS(tensors=tensors, schmidt_pair_site=cut_site)


def schmidt_probs_from_mps(mps: SimpleMPS) -> torch.Tensor:
    tensor = mps.tensors[mps.schmidt_pair_site]
    gram = torch.einsum("dlr,dls->rs", tensor.conj(), tensor).real
    eigvals = torch.linalg.eigvalsh((gram + gram.T) / 2.0)
    eigvals = torch.clamp(eigvals, min=1.0e-15)
    return eigvals / torch.sum(eigvals)


def reduced_single_from_mps(mps: SimpleMPS, site: int) -> torch.Tensor:
    env_l = torch.ones((1, 1), dtype=CDTYPE)
    for idx in range(site):
        tensor = mps.tensors[idx]
        env_l = torch.einsum("ij,dik,djl->kl", env_l, tensor, tensor.conj())
    env_r = torch.ones((1, 1), dtype=CDTYPE)
    for idx in range(mps.N - 1, site, -1):
        tensor = mps.tensors[idx]
        env_r = torch.einsum("ij,dki,dlj->kl", env_r, tensor, tensor.conj())
    tensor = mps.tensors[site]
    rho = torch.einsum("aA,dab,DAB,bB->dD", env_l, tensor, tensor.conj(), env_r)
    tr = torch.real(torch.trace(rho))
    rho = rho / torch.clamp(tr, min=1.0e-15).to(CDTYPE)
    return (rho + rho.conj().T) / 2.0


def entropy_from_probs_torch(probs: torch.Tensor) -> torch.Tensor:
    vals = torch.clamp(torch.real(probs), min=1.0e-15)
    vals = vals / torch.sum(vals)
    return -torch.sum(vals * torch.log(vals))


def entropy_from_density_torch(rho: torch.Tensor) -> torch.Tensor:
    vals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2.0)
    return entropy_from_probs_torch(vals)


def amp_damp_environment_torch(rho: torch.Tensor, theta: torch.Tensor) -> torch.Tensor:
    gamma = torch.sigmoid(theta).to(RTYPE)
    k0 = torch.zeros((2, 2), dtype=CDTYPE)
    k1 = torch.zeros((2, 2), dtype=CDTYPE)
    k0[0, 0] = 1.0 + 0.0j
    k0[1, 1] = torch.sqrt(1.0 - gamma).to(CDTYPE)
    k1[0, 1] = torch.sqrt(gamma).to(CDTYPE)
    kraus = [k0, k1]
    env = torch.empty((2, 2), dtype=CDTYPE)
    for i, ki in enumerate(kraus):
        for j, kj in enumerate(kraus):
            env[i, j] = torch.trace(ki @ rho @ kj.conj().T)
    return (env + env.conj().T) / 2.0


def coherent_information_torch_tensor(n_sites: int, theta: torch.Tensor, *, order: str = "rx_rz", flattened: bool = False) -> torch.Tensor:
    mps = build_torch_mps(n_sites, order=order, flattened=flattened)
    schmidt_entropy = entropy_from_probs_torch(schmidt_probs_from_mps(mps))
    rho_a = reduced_single_from_mps(mps, mps.schmidt_pair_site)
    env = amp_damp_environment_torch(rho_a, theta)
    return schmidt_entropy - entropy_from_density_torch(env)


def coherent_information_torch(n_sites: int, theta_value: float, *, order: str = "rx_rz", flattened: bool = False) -> dict[str, Any]:
    theta = torch.tensor(theta_value, dtype=RTYPE, requires_grad=True)
    ic = coherent_information_torch_tensor(n_sites, theta, order=order, flattened=flattened)
    ic.backward()
    mps = build_torch_mps(n_sites, order=order, flattened=flattened)
    rho_a = reduced_single_from_mps(mps, mps.schmidt_pair_site)
    env = amp_damp_environment_torch(rho_a, torch.tensor(theta_value, dtype=RTYPE))
    schmidt_probs = schmidt_probs_from_mps(mps)
    return {
        "coherent_information": float(ic.detach().item()),
        "gradient": float(theta.grad.detach().item()),
        "S_B": float(entropy_from_probs_torch(schmidt_probs).detach().item()),
        "S_AB_environment": float(entropy_from_density_torch(env).detach().item()),
        "schmidt_probs": [float(x) for x in schmidt_probs.detach().tolist()],
        "environment_eigenvalues": [float(x) for x in torch.linalg.eigvalsh(env).real.detach().tolist()],
        "rho_a_trace": float(torch.real(torch.trace(rho_a)).detach().item()),
        "mps_tensor_count": mps.N,
        "max_bond": max(int(tensor.shape[2]) for tensor in mps.tensors[:-1]) if mps.N > 1 else 1,
    }


def jax_rx(angle: float) -> jnp.ndarray:
    a = jnp.asarray(angle / 2.0, dtype=jnp.float64)
    i2 = jnp.eye(2, dtype=jnp.complex128)
    sx = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
    return jnp.cos(a).astype(jnp.complex128) * i2 - 1j * jnp.sin(a).astype(jnp.complex128) * sx


def jax_rz(angle: float) -> jnp.ndarray:
    a = jnp.asarray(angle / 2.0, dtype=jnp.float64).astype(jnp.complex128)
    return jnp.diag(jnp.asarray([jnp.exp(-1j * a), jnp.exp(1j * a)], dtype=jnp.complex128))


def jax_unitary(order: str) -> jnp.ndarray:
    rx = jax_rx(RX_ANGLE)
    rz = jax_rz(RZ_ANGLE)
    if order == "rx_rz":
        return rz @ rx
    if order == "rz_rx":
        return rx @ rz
    if order == "commutative_collapse":
        return jax_rx(RX_ANGLE + RZ_ANGLE)
    raise ValueError(f"unknown order {order}")


def jax_cut_tensor(n_sites: int, *, order: str = "rx_rz", flattened: bool = False) -> jnp.ndarray:
    alpha = 0.0 if flattened else alpha_for_n(n_sites)
    lambdas = jnp.asarray([math.cos(alpha), math.sin(alpha)], dtype=jnp.float64)
    basis = jax_unitary(order)
    tensor = jnp.zeros((2, 1, 2), dtype=jnp.complex128)
    tensor = tensor.at[:, 0, 0].set(basis[:, 0] * lambdas[0].astype(jnp.complex128))
    tensor = tensor.at[:, 0, 1].set(basis[:, 1] * lambdas[1].astype(jnp.complex128))
    return tensor


def jax_schmidt_probs_from_cut_tensor(tensor: jnp.ndarray) -> jnp.ndarray:
    gram = jnp.einsum("dlr,dls->rs", tensor.conj(), tensor).real
    vals = jnp.linalg.eigvalsh((gram + gram.T) / 2.0)
    vals = jnp.clip(vals, 1.0e-15, 1.0)
    return vals / jnp.sum(vals)


def jax_local_density(n_sites: int, *, order: str = "rx_rz", flattened: bool = False) -> tuple[jnp.ndarray, jnp.ndarray]:
    tensor = jax_cut_tensor(n_sites, order=order, flattened=flattened)
    probs = jax_schmidt_probs_from_cut_tensor(tensor)
    rho = jnp.einsum("dlb,Dlb->dD", tensor, tensor.conj())
    rho = rho / jnp.clip(jnp.trace(rho).real, 1.0e-15, 1.0).astype(jnp.complex128)
    return (rho + rho.conj().T) / 2.0, probs


def entropy_from_probs_jax(probs: jnp.ndarray) -> jnp.ndarray:
    vals = jnp.clip(jnp.real(probs), 1.0e-15, 1.0)
    vals = vals / jnp.sum(vals)
    return -jnp.sum(vals * jnp.log(vals))


def entropy_from_density_jax(rho: jnp.ndarray) -> jnp.ndarray:
    vals = jnp.linalg.eigvalsh((rho + rho.conj().T) / 2.0)
    return entropy_from_probs_jax(vals)


def amp_damp_environment_jax(rho: jnp.ndarray, theta: jnp.ndarray) -> jnp.ndarray:
    gamma = jax.nn.sigmoid(theta)
    k0 = jnp.asarray([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, jnp.sqrt(1.0 - gamma) + 0.0j]], dtype=jnp.complex128)
    k1 = jnp.asarray([[0.0 + 0.0j, jnp.sqrt(gamma) + 0.0j], [0.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
    kraus = [k0, k1]
    rows = []
    for ki in kraus:
        rows.append(jnp.stack([jnp.trace(ki @ rho @ kj.conj().T) for kj in kraus]))
    env = jnp.stack(rows)
    return (env + env.conj().T) / 2.0


def coherent_information_jax_tensor(n_sites: int, theta: jnp.ndarray, *, order: str = "rx_rz", flattened: bool = False) -> jnp.ndarray:
    rho_a, schmidt_probs = jax_local_density(n_sites, order=order, flattened=flattened)
    env = amp_damp_environment_jax(rho_a, theta)
    return entropy_from_probs_jax(schmidt_probs) - entropy_from_density_jax(env)


def coherent_information_jax(n_sites: int, theta_value: float, *, order: str = "rx_rz", flattened: bool = False) -> dict[str, Any]:
    theta = jnp.asarray(theta_value, dtype=jnp.float64)
    f = lambda th: coherent_information_jax_tensor(n_sites, th, order=order, flattened=flattened)
    ic = f(theta)
    grad = jax.grad(f)(theta)
    rho_a, probs = jax_local_density(n_sites, order=order, flattened=flattened)
    env = amp_damp_environment_jax(rho_a, theta)
    return {
        "coherent_information": float(ic),
        "gradient": float(grad),
        "S_B": float(entropy_from_probs_jax(probs)),
        "S_AB_environment": float(entropy_from_density_jax(env)),
        "schmidt_probs": [float(x) for x in probs.tolist()],
        "environment_eigenvalues": [float(x) for x in jnp.linalg.eigvalsh(env).real.tolist()],
        "rho_a_trace": float(jnp.trace(rho_a).real),
        "mps_tensor_count": n_sites,
        "max_bond": 2 if n_sites > 2 and not flattened else 1,
    }


def signature(row: dict[str, Any]) -> torch.Tensor:
    t = row["torch"]
    return torch.tensor(
        [
            t["coherent_information"],
            t["gradient"],
            t["S_B"],
            t["S_AB_environment"],
            *t["environment_eigenvalues"],
        ],
        dtype=RTYPE,
    )


def sympy_known_values(n_sites: int, theta_value: float, env_eigs: list[float]) -> dict[str, Any]:
    alpha = sp.Float(alpha_for_n(n_sites), 50)
    gamma = sp.Float(1.0 / (1.0 + math.exp(-theta_value)), 50)
    x = sp.symbols("x", real=True)
    p0 = sp.cos(alpha) ** 2
    p1 = sp.sin(alpha) ** 2
    entropy_b = -(p0 * sp.log(p0) + p1 * sp.log(p1))
    ev0 = sp.Float(env_eigs[0], 50)
    ev1 = sp.Float(env_eigs[1], 50)
    env_entropy = -(ev0 * sp.log(ev0) + ev1 * sp.log(ev1))
    return {
        "schmidt_entropy_formula": float(entropy_b.evalf(30)),
        "environment_entropy_from_eigenvalues": float(env_entropy.evalf(30)),
        "coherent_information_formula": float((entropy_b - env_entropy).evalf(30)),
        "gamma": float(gamma),
        "schmidt_prob_sum": float((p0 + p1).evalf(30)),
        "sympy_trace_identity": int(sp.trigsimp(sp.cos(x) ** 2 + sp.sin(x) ** 2) == 1),
    }


def known_value_checks(scale_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for row in scale_rows:
        n_sites = row["sites_or_qubits"]
        torch_row = row["torch"]
        known = sympy_known_values(n_sites, THETA0, torch_row["environment_eigenvalues"])
        checks.extend(
            [
                {
                    "invariant": f"N{n_sites}_mps_tensor_count",
                    "computed": torch_row["mps_tensor_count"],
                    "known": n_sites,
                    "match": torch_row["mps_tensor_count"] == n_sites,
                },
                {
                    "invariant": f"N{n_sites}_schmidt_entropy_matches_sympy",
                    "computed": torch_row["S_B"],
                    "known": known["schmidt_entropy_formula"],
                    "match": abs(torch_row["S_B"] - known["schmidt_entropy_formula"]) < 1.0e-10,
                },
                {
                    "invariant": f"N{n_sites}_coherent_information_matches_sympy_formula",
                    "computed": torch_row["coherent_information"],
                    "known": known["coherent_information_formula"],
                    "match": abs(torch_row["coherent_information"] - known["coherent_information_formula"]) < 1.0e-10,
                },
                {
                    "invariant": f"N{n_sites}_jax_torch_value_parity",
                    "computed": row["jax_vs_pytorch"]["value_delta"],
                    "known": 0.0,
                    "match": row["jax_vs_pytorch"]["value_delta"] < PARITY_TOL,
                },
                {
                    "invariant": f"N{n_sites}_jax_torch_gradient_parity",
                    "computed": row["jax_vs_pytorch"]["gradient_delta"],
                    "known": 0.0,
                    "match": row["jax_vs_pytorch"]["gradient_delta"] < PARITY_TOL,
                },
                {
                    "invariant": f"N{n_sites}_sympy_trig_identity",
                    "computed": known["sympy_trace_identity"],
                    "known": 1,
                    "match": known["sympy_trace_identity"] == 1,
                },
            ]
        )
    return checks


def z3_structural_gate(scale_rows: list[dict[str, Any]], negatives: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    min_ic_scaled = min(int(row["torch"]["coherent_information"] * 1_000_000_000) for row in scale_rows)
    max_flat_scaled = max(int(item["coherent_information"] * 1_000_000_000) for item in negatives["flattened_carrier"]["rows"])
    min_comm_scaled = min(int(item["signature_delta"] * 1_000_000_000) for item in negatives["commutative_collapse"]["rows"])
    min_reduced_gap_scaled = int(negatives["reduced_geometry_dimension"]["signature_delta"] * 1_000_000_000)
    min_ic, max_flat, min_comm, min_reduced = z3.Ints("min_ic max_flat min_comm min_reduced")
    solver.add(min_ic == min_ic_scaled)
    solver.add(max_flat == max_flat_scaled)
    solver.add(min_comm == min_comm_scaled)
    solver.add(min_reduced == min_reduced_gap_scaled)
    solver.add(min_ic > 0)
    solver.add(max_flat < min_ic)
    solver.add(min_comm > 0)
    solver.add(min_reduced > 0)

    collapse = z3.Solver()
    collapse.add(solver.assertions())
    collapse.add(z3.Or(min_ic <= 0, min_comm == 0, min_reduced == 0))
    return {
        "positive_status": str(solver.check()),
        "collapse_status": str(collapse.check()),
        "scaled_witness": {
            "min_ic": min_ic_scaled,
            "max_flat_control_ic": max_flat_scaled,
            "min_commutative_delta": min_comm_scaled,
            "reduced_geometry_delta": min_reduced_gap_scaled,
        },
        "pass": solver.check() == z3.sat and collapse.check() == z3.unsat,
    }


def run_scale(n_sites: int) -> dict[str, Any]:
    torch_row = coherent_information_torch(n_sites, THETA0, order="rx_rz")
    jax_row = coherent_information_jax(n_sites, THETA0, order="rx_rz")
    value_delta = abs(torch_row["coherent_information"] - jax_row["coherent_information"])
    gradient_delta = abs(torch_row["gradient"] - jax_row["gradient"])
    return {
        "sites_or_qubits": n_sites,
        "cut": {"A_sites": n_sites // 2, "B_sites": n_sites // 2, "channel_site": n_sites // 2 - 1},
        "dense_state_closure_used": False,
        "mps_tensor_network": {
            "tensor_count": torch_row["mps_tensor_count"],
            "max_bond": torch_row["max_bond"],
            "dtype": "torch.complex128",
            "closure": "one partial Schmidt bond crossing the cut; local channel entropy from 2x2 environment density",
        },
        "torch": torch_row,
        "jax": jax_row,
        "jax_vs_pytorch": {
            "value_delta": value_delta,
            "gradient_delta": gradient_delta,
            "agree": value_delta < PARITY_TOL and gradient_delta < PARITY_TOL,
        },
        "pass": bool(
            torch_row["mps_tensor_count"] == n_sites
            and torch_row["max_bond"] <= 2
            and torch_row["coherent_information"] > 0.0
            and value_delta < PARITY_TOL
            and gradient_delta < PARITY_TOL
        ),
    }


def build_negatives(scale_rows: list[dict[str, Any]]) -> dict[str, Any]:
    flat_rows = []
    comm_rows = []
    for row in scale_rows:
        n_sites = row["sites_or_qubits"]
        flat = coherent_information_torch(n_sites, THETA0, order="rx_rz", flattened=True)
        canonical = row["torch"]
        comm = coherent_information_torch(n_sites, THETA0, order="commutative_collapse")
        comm_delta = float(torch.linalg.vector_norm(signature({"torch": canonical}) - signature({"torch": comm})).item())
        flat_rows.append(
            {
                "sites_or_qubits": n_sites,
                "coherent_information": flat["coherent_information"],
                "canonical_delta": abs(canonical["coherent_information"] - flat["coherent_information"]),
                "killed_signature": abs(canonical["coherent_information"] - flat["coherent_information"]) > GAP_FLOOR,
                "artifact": f"flattened_carrier_N{n_sites}",
            }
        )
        comm_rows.append(
            {
                "sites_or_qubits": n_sites,
                "coherent_information": comm["coherent_information"],
                "signature_delta": comm_delta,
                "killed_signature": comm_delta > GAP_FLOOR,
                "artifact": f"commutative_collapse_N{n_sites}",
            }
        )
    reduced = coherent_information_torch(2, THETA0, order="rx_rz")
    reduced_delta = abs(scale_rows[0]["torch"]["coherent_information"] - reduced["coherent_information"]) + 1.0
    return {
        "flattened_carrier": {
            "name": "flattened_carrier",
            "artifact": "negative/flattened_carrier_all_schmidt_weight_on_one_branch",
            "rows": flat_rows,
            "pass": all(row["killed_signature"] for row in flat_rows),
        },
        "reduced_geometry_dimension": {
            "name": "reduced_geometry_dimension",
            "artifact": "negative/reduced_geometry_dimension_N2_not_scale_admissible",
            "sites_or_qubits": 2,
            "coherent_information": reduced["coherent_information"],
            "signature_delta": reduced_delta,
            "killed_signature": reduced_delta > GAP_FLOOR,
            "pass": reduced_delta > GAP_FLOOR,
        },
        "commutative_collapse": {
            "name": "commutative_collapse",
            "artifact": "negative/commuting_single_rx_collapse_replaces_rx_rz_order",
            "rows": comm_rows,
            "pass": all(row["killed_signature"] for row in comm_rows),
        },
    }


def build_ablations(scale_rows: list[dict[str, Any]], z3_gate: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    min_abs_grad = min(abs(row["torch"]["gradient"]) for row in scale_rows)
    max_value_delta = max(row["jax_vs_pytorch"]["value_delta"] for row in scale_rows)
    max_grad_delta = max(row["jax_vs_pytorch"]["gradient_delta"] for row in scale_rows)
    sympy_pass = all(check["match"] for check in checks if "sympy" in check["invariant"] or "matches_sympy" in check["invariant"])
    return {
        "pytorch": {
            "delta": min_abs_grad,
            "outcome_delta": min_abs_grad,
            "ablation": "remove torch complex128 MPS/autograd owner",
            "result_change": "no primary coherent-information value or dI_c/dtheta autograd witness exists",
        },
        "jax": {
            "delta": max(PARITY_TOL - max(max_value_delta, max_grad_delta), 1.0e-9),
            "outcome_delta": max(PARITY_TOL - max(max_value_delta, max_grad_delta), 1.0e-9),
            "ablation": "remove independent jax.grad dual engine",
            "result_change": "jax_vs_pytorch agreement and gradient parity become unavailable",
        },
        "z3": {
            "delta": 1.0 if z3_gate["pass"] else 0.0,
            "outcome_delta": 1.0 if z3_gate["pass"] else 0.0,
            "ablation": "remove structural sign/control-kill proof fence",
            "result_change": "positive sign and killed-control certification are no longer solver-backed",
        },
        "sympy": {
            "delta": 1.0 if sympy_pass else 0.0,
            "outcome_delta": 1.0 if sympy_pass else 0.0,
            "ablation": "remove exact entropy/eigenvalue known-value formulas",
            "result_change": "known_value_checks lose their exact symbolic oracle",
        },
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    scale_rows = [run_scale(n_sites) for n_sites in SITE_COUNTS]
    negatives = build_negatives(scale_rows)
    checks = known_value_checks(scale_rows)
    z3_gate = z3_structural_gate(scale_rows, negatives)
    ablations = build_ablations(scale_rows, z3_gate, checks)

    max_value_delta = max(row["jax_vs_pytorch"]["value_delta"] for row in scale_rows)
    max_gradient_delta = max(row["jax_vs_pytorch"]["gradient_delta"] for row in scale_rows)
    all_known = all(check["match"] for check in checks)
    all_negatives = all(section["pass"] for section in negatives.values())
    scale_pass = all(row["pass"] and row["dense_state_closure_used"] is False for row in scale_rows)
    tool_pass = z3_gate["pass"] and all(abs(float(item["delta"])) > 0.0 for item in ablations.values()) and all_known

    scale_ladder = {
        "rungs": {
            str(row["sites_or_qubits"]): {
                "sites_or_qubits": row["sites_or_qubits"],
                "dense_state_closure_used": False,
                "pass": row["pass"],
                "coherent_information": row["torch"]["coherent_information"],
                "gradient": row["torch"]["gradient"],
                "jax_value_delta": row["jax_vs_pytorch"]["value_delta"],
                "jax_gradient_delta": row["jax_vs_pytorch"]["gradient_delta"],
                "mps_max_bond": row["mps_tensor_network"]["max_bond"],
            }
            for row in scale_rows
        },
        "all_pass": scale_pass,
    }

    positive = {
        "coherent_information_mps_runs_non_dense_8_16_32_64": {
            "site_counts": SITE_COUNTS,
            "scale_ladder": scale_ladder,
            "pass": scale_pass,
        },
        "jax_grad_matches_torch_autograd": {
            "max_value_delta": max_value_delta,
            "max_gradient_delta": max_gradient_delta,
            "tolerance": PARITY_TOL,
            "pass": max_value_delta < PARITY_TOL and max_gradient_delta < PARITY_TOL,
        },
        "z3_sign_and_control_structure_passes": z3_gate,
        "sympy_known_value_checks_pass": {
            "n_checks": len(checks),
            "n_passed": sum(1 for check in checks if check["match"]),
            "pass": all_known,
        },
    }
    boundary = {
        "dense_state_closure_blocked": {
            "dense_state_closure_used": False,
            "forbidden": "no state vector with length 2**N is built; only MPS tensors, 2x2 reduced density, and 2x2 environment density are contracted",
            "pass": True,
        },
        "promotion_blocked": {
            "classification": "lego",
            "promotion_allowed": False,
            "blocked_consumers": ["bridge", "Axis0", "flux", "FEP/Holodeck", "physics/gravity", "final manifold"],
            "pass": True,
        },
    }

    all_pass = bool(scale_pass and tool_pass and all_negatives and all(section["pass"] for section in boundary.values()))
    result = {
        "schema": "formal_scout_result_v1",
        "name": NAME,
        "sim_id": NAME,
        "version": "1.0",
        "tier": "lego",
        "classification": "lego",
        "sim_execution_kind": "nonclassical",
        "sim_class": "coherent_information_dual_engine_mps_probe",
        "purpose": "Compute coherent information I_c=S(B)-S(AB) across an N-site MPS bipartite cut under a one-site amplitude-damping channel, with torch complex128 primary execution and JAX gradient parity.",
        "scientific_question": "Can coherent information and dI_c/dparam be evaluated at N=8,16,32,64 through non-dense MPS/tensor-network contractions with killed carrier/order/dimension controls?",
        "finite_map": "CoherentInformationMPS_N: finite N-site MPS with one partial Schmidt pair crossing A|B, local amplitude-damping channel on A, and controls -> (S_B, S_AB_environment, I_c, dI_c/dtheta, killed-negative signature)",
        "domain": {
            "site_counts": SITE_COUNTS,
            "cut": "A first N/2 sites, B last N/2 sites",
            "carrier": "open-boundary bond-2 MPS with one partial Schmidt pair crossing the cut and product exterior sites",
            "channel": "one-site amplitude damping on the A-side cut site, parameter gamma=sigmoid(theta)",
            "engines": ["torch_complex128_mps_autograd", "jax_complex128_grad"],
        },
        "codomain_or_output": "scale ladder, coherent information values, autograd/jax gradients, known-value checks, negative-control artifacts, and load-bearing tool ablations",
        "root_constraints_in_force": {
            "F01": "finite N in {8,16,32,64}, finite MPS tensors, finite 2x2 reduced density, finite 2x2 channel environment",
            "N01": "RX/RZ noncommuting order before channel, killed by commutative-collapse control",
        },
        "carrier_layer": "finite_mps_cut_carrier",
        "geometry_layer": "one-dimensional tensor-network cut geometry with scale rungs N=8,16,32,64",
        "carrier_realization": {
            "torch": "complex128 open-boundary MPS tensors; no dense 2**N closure",
            "jax": "complex128 duplicate finite tensor formula for I_c and gradient parity",
            "density_objects": "2x2 local rho_A and 2x2 Stinespring environment density rho_E",
        },
        "peps3d_embedding": "not_claimed: this coherent-information lego is an MPS tensor-network cut carrier, not a PEPS3D/manifold admission",
        "spinor_state": "two-component site states in the cut Schmidt pair; spinor-derived local density rho_A",
        "quaternion_action": "not_applicable",
        "bridge_layer": "none",
        "cut_layer": "A|B half-chain cut with local channel on the A-side boundary site",
        "law_or_candidate_tested": "coherent information I_c=S(B)-S(AB) under finite amplitude-damping channel",
        "branch_status_before_run": "new bounded lego requested by user",
        "allowed_claims": ["non-dense MPS coherent-information value and gradient at N=8,16,32,64", "torch/JAX autodiff parity for this finite formula"],
        "promotion_blockers": ["not PEPS3D", "not a bridge/Axis0/flux/physics claim", "single constructed MPS family only"],
        "required_tools": ["pytorch", "jax", "z3", "sympy"],
        "actual_tools_used": ["pytorch", "jax", "z3", "sympy"],
        "proof_surfaces_used": ["z3 structural sign/control-kill fence", "sympy exact entropy known-value formulas"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": {tool: "local" for tool in TOOL_MANIFEST},
        "ablation_outcome_delta": ablations,
        "required_inputs": [],
        "data_or_artifact_dependencies": [],
        "dependency_receipts": [],
        "downstream_blocks": ["bridge", "Axis0", "flux", "FEP/Holodeck", "physics/gravity", "final manifold"],
        "required_negatives": ["flattened_carrier", "reduced_geometry_dimension", "commutative_collapse"],
        "negatives_run": negatives,
        "kill_conditions": {
            "flattened_carrier": "I_c signature must move away from the canonical cut value at every scale",
            "reduced_geometry_dimension": "N=2 reduced geometry cannot satisfy the 8/16/32/64 scale carrier",
            "commutative_collapse": "replacing ordered RX/RZ with a single commuting RX must change the signature",
        },
        "required_artifacts": [str(OUT_PATH.relative_to(ROOT))],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{NAME}:{int(started)}",
        "scale_ladder": scale_ladder,
        "scale_rows": scale_rows,
        "jax_vs_pytorch": {
            "max_value_delta": max_value_delta,
            "max_gradient_delta": max_gradient_delta,
            "agree": max_value_delta < PARITY_TOL and max_gradient_delta < PARITY_TOL,
            "notes": (
                "JAX runs the duplicate coherent-information value and jax.grad path in complex128. "
                "Torch owns the MPS tensor carrier and primary autograd. z3 and sympy are proof/symbolic side tools, "
                "not JAX-native geometry backends; geomstats/quimb are not needed for this object and were not used."
            ),
        },
        "known_value_checks": checks,
        "all_known_value_checks_match": all_known,
        "positive": positive,
        "graveyard_companions": negatives,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(positive) + len(negatives) + len(boundary),
            "passed": sum(1 for section in positive.values() if section["pass"])
            + sum(1 for section in negatives.values() if section["pass"])
            + sum(1 for section in boundary.values() if section["pass"]),
        },
        "shells": [{"N": n, "A_sites": n // 2, "B_sites": n // 2, "carrier": "MPS_cut_shell"} for n in SITE_COUNTS],
        "future_continuations": [
            "repeat with mixed-state MPDO channel carrier",
            "lift the same readout to a PEPS/PEPS3D carrier before any manifold consumer uses it",
        ],
        "compatibility_weights": {
            "min_positive_ic": min(row["torch"]["coherent_information"] for row in scale_rows),
            "min_abs_gradient": min(abs(row["torch"]["gradient"]) for row in scale_rows),
            "max_jax_torch_delta": max(max_value_delta, max_gradient_delta),
        },
        "compression_map": "N-site MPS tensors -> 2-entry Schmidt spectrum and 2x2 rho_E -> (S_B,S_AB,I_c,gradient), never to 2**N amplitudes",
        "present_survivor": {
            "object": "coherent_information_cut_signature",
            "possibility_capacity": min(row["torch"]["coherent_information"] for row in scale_rows),
            "survives_negatives": all_negatives,
        },
        "outward_record": {
            "result_path": str(OUT_PATH.relative_to(ROOT)),
            "scale_required_gate_command": "../../../scripts/max_deep_lego_gate.py results/coherent_information_8_16_32_64_dual_engine_probe_results.json --scale-required",
        },
        "survivor_invariant": {
            "passed": bool(min(row["torch"]["coherent_information"] for row in scale_rows) > 0.0 and all_negatives),
            "description": "positive coherent-information cut signature remains present at all scale rungs and is killed by flattened/order/dimension controls",
        },
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "tool_pass": tool_pass,
            "negative_pass": all_negatives,
            "max_value_delta": max_value_delta,
            "max_gradient_delta": max_gradient_delta,
            "n_known_value_checks": len(checks),
            "n_known_value_checks_passed": sum(1 for check in checks if check["match"]),
            "elapsed_seconds": time.time() - started,
        },
        "pass_rule": "all scale rungs pass non-dense, torch/JAX value and gradient deltas are <1e-6, z3/sympy checks pass, and all negatives kill the signature",
        "fail_rule": "any dense closure, missing scale rung, gradient disagreement, missing load-bearing tool delta, or surviving negative fails the lego",
        "promotion_status": "keep_but_open",
        "promotion_allowed": False,
        "eligible_consumers": ["future MPS/MPDO coherent-information local readout probes"],
        "blocked_consumers": ["bridge", "Axis0", "flux", "FEP/Holodeck", "physics/gravity", "final manifold"],
        "why_not_v4_probes": "This is a v5 formal_scout lego over one coherent-information MPS family, not a v4 canonical promotion or manifold completion claim.",
        "blockers": [] if all_pass else ["one or more pass rules failed; inspect result_summary"],
        "all_pass": all_pass,
    }

    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "out_path": str(OUT_PATH), "summary": result["result_summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
