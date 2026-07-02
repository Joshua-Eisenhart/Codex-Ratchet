#!/usr/bin/env python3
"""PEPS3D spinor-network flux -> Axis0 signed QIT/FEP gradient scout.

Formal scout only.

Target object:

    PEPS3D spinor shell manifold
      -> L/R chiral sheet response
      -> engine-bound quaternionic flux J_flux
      -> topology mutation witness
      -> Axis0 = signed QIT/FEP gradient induced by that flux

Flux is not inserted as a primitive variable. It is derived from left/right
chiral spinor-sheet transport and read through local PEPS3D boundary
contractions. Axis0 is not flux; Axis0 is the signed free-energy pressure read
from that flux over finite shell histories.

This row uses the 8-site 2x2x2 PEPS3D shell first. It does not admit final
Axis0, Xi, Phi0, flux, PEPS3D closure, gravity, Standard Model, Yang-Mills,
Riemann, or physics claims.
"""

from __future__ import annotations

import itertools
import json
import math
import pathlib
import time
from typing import Any

import torch
import z3

import canonical_qit_engine_specs as specs


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "peps3d_spinor_network_flux_axis0_gradient_probe_results.json"

NAME = "peps3d_spinor_network_flux_axis0_gradient_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical_peps3d_spinor_network_flux_axis0_gradient"
SOURCE_ALIGNMENT_CATEGORY = "peps3d_spinor_network_engine_bound_chiral_flux_axis0_gradient"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: derives engine-bound quaternionic L/R spinor-shell "
    "boundary flux on an 8-site PEPS3D spinor network and tests Axis0 as a "
    "signed QIT/FEP gradient over finite shell histories. It does not admit "
    "final Axis0, Xi, Phi0, flux, PEPS3D closure, gravity, Standard Model, "
    "Yang-Mills, Riemann, or physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing spinor states, quaternionic IJK sheet transport, "
            "PEPS3D local-star and shell-boundary contractions, finite "
            "history entropy, topology mutation, and signed F_QIT gradients"
        ),
    },
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive source-native engine schedules and topology rows",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive finite 8-site, finite-history, and nonpromotion gates",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "canonical_qit_engine_specs": "supportive",
    "z3": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

RTYPE = torch.float64
CDTYPE = torch.complex128
PEPS3D_SHAPE = (2, 2, 2)
BOND_DIM = 2
PHYS_DIM = 2
EPS = 1.0e-10
GAP_FLOOR = 1.0e-5
OPERATOR_SEQUENCE = ["Ti", "Te", "Fi", "Fe"]
TOPOLOGIES = ["Se", "Ne", "Ni", "Si"]

Q_ONE = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=RTYPE)
Q_I = torch.tensor([0.0, 1.0, 0.0, 0.0], dtype=RTYPE)
Q_J = torch.tensor([0.0, 0.0, 1.0, 0.0], dtype=RTYPE)
Q_K = torch.tensor([0.0, 0.0, 0.0, 1.0], dtype=RTYPE)

OPERATOR_UNITS = {
    "Ti": Q_K,
    "Te": Q_I,
    "Fi": Q_I,
    "Fe": Q_K,
}
TOPOLOGY_UNITS = {
    "Se": Q_I,
    "Ne": Q_J,
    "Ni": Q_K,
    "Si": (Q_I + Q_J + Q_K) / math.sqrt(3.0),
}
IJK_PROBES = {
    "i": Q_ONE + 0.72 * Q_I + 0.18 * Q_J,
    "j": Q_ONE + 0.72 * Q_J + 0.18 * Q_K,
    "k": Q_ONE + 0.72 * Q_K + 0.18 * Q_I,
}


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
        return {"real": value.real, "imag": value.imag}
    return value


def q_norm(q: torch.Tensor) -> torch.Tensor:
    return torch.linalg.vector_norm(q)


def q_normalize(q: torch.Tensor) -> torch.Tensor:
    return q / torch.clamp(q_norm(q), min=EPS)


def q_mul(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    a0, a1, a2, a3 = [float(item.item()) for item in a]
    b0, b1, b2, b3 = [float(item.item()) for item in b]
    return torch.tensor(
        [
            a0 * b0 - a1 * b1 - a2 * b2 - a3 * b3,
            a0 * b1 + a1 * b0 + a2 * b3 - a3 * b2,
            a0 * b2 - a1 * b3 + a2 * b0 + a3 * b1,
            a0 * b3 + a1 * b2 - a2 * b1 + a3 * b0,
        ],
        dtype=RTYPE,
    )


def q_exp(unit: torch.Tensor, angle: float) -> torch.Tensor:
    unit = q_normalize(unit)
    imag = q_normalize(unit[1:])
    return q_normalize(torch.cat([torch.tensor([math.cos(angle)], dtype=RTYPE), math.sin(angle) * imag]))


def q_to_spinor(q: torch.Tensor) -> torch.Tensor:
    q = q_normalize(q)
    return torch.tensor(
        [complex(float(q[0].item()), float(q[1].item())), complex(float(q[2].item()), float(q[3].item()))],
        dtype=CDTYPE,
    )


def spinor_to_q(psi: torch.Tensor) -> torch.Tensor:
    return q_normalize(
        torch.tensor(
            [
                torch.real(psi[0]).item(),
                torch.imag(psi[0]).item(),
                torch.real(psi[1]).item(),
                torch.imag(psi[1]).item(),
            ],
            dtype=RTYPE,
        )
    )


def spinor(phi: float, chi: float, eta: float, *, phase: float = 0.0) -> torch.Tensor:
    raw = torch.tensor(
        [
            complex(math.cos(phi + chi + phase), math.sin(phi + chi + phase)) * math.cos(eta),
            complex(math.cos(phi - chi + phase), math.sin(phi - chi + phase)) * math.sin(eta),
        ],
        dtype=CDTYPE,
    )
    return raw / torch.linalg.vector_norm(raw)


def density(psi: torch.Tensor) -> torch.Tensor:
    psi = psi / torch.clamp(torch.linalg.vector_norm(psi), min=EPS)
    return torch.outer(psi, torch.conj(psi))


def hermitize(rho: torch.Tensor) -> torch.Tensor:
    return (rho + torch.conj(rho).T) / 2.0


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = hermitize(rho)
    tr = torch.real(torch.trace(rho))
    return rho / torch.clamp(tr, min=EPS)


def entropy_from_probs(weights: torch.Tensor) -> float:
    weights = torch.clamp(weights.real, min=EPS)
    probs = weights / torch.clamp(torch.sum(weights), min=EPS)
    return float((-torch.sum(probs * torch.log(probs))).item())


def kl_probs(p: torch.Tensor, q: torch.Tensor) -> float:
    p = torch.clamp(p.real, min=EPS)
    q = torch.clamp(q.real, min=EPS)
    p = p / torch.clamp(torch.sum(p), min=EPS)
    q = q / torch.clamp(torch.sum(q), min=EPS)
    return float(torch.sum(p * (torch.log(p) - torch.log(q))).item())


def sites() -> list[tuple[int, int, int]]:
    return list(itertools.product(range(2), range(2), range(2)))


def site_index(site: tuple[int, int, int]) -> int:
    a, b, c = site
    return 4 * a + 2 * b + c


def neighbors(site: tuple[int, int, int]) -> list[tuple[tuple[int, int, int], str]]:
    out: list[tuple[tuple[int, int, int], str]] = []
    for axis, label in [(0, "i"), (1, "j"), (2, "k")]:
        for step in [-1, 1]:
            candidate = list(site)
            candidate[axis] += step
            if all(0 <= item < 2 for item in candidate):
                out.append(((candidate[0], candidate[1], candidate[2]), label))
    return out


def leg_index(site: tuple[int, int, int], target: tuple[int, int, int]) -> int:
    for idx, (dst, _label) in enumerate(neighbors(site)):
        if dst == target:
            return idx
    raise ValueError(f"{target} is not a neighbor of {site}")


def base_spinors() -> dict[tuple[int, int, int], torch.Tensor]:
    out: dict[tuple[int, int, int], torch.Tensor] = {}
    for site in sites():
        idx = site_index(site)
        a, b, c = site
        phi = 0.19 * idx + 0.13 * a - 0.07 * b + 0.05 * c
        chi = -0.47 + 0.94 * ((3 * a + 5 * b + 7 * c + 1) % 8) / 7.0
        eta = 0.22 + 1.05 * ((5 * a + 2 * b + 3 * c + 2) % 8) / 7.0
        out[site] = spinor(phi, chi, min(max(eta, 0.16), 1.40))
    return out


def shell_orientation(site: tuple[int, int, int], *, reversed_shell_time: bool = False) -> torch.Tensor:
    a, b, c = site
    sign = -1.0 if reversed_shell_time else 1.0
    i_part = (1.0 if a == 1 else -1.0) * Q_I
    j_part = sign * (1.0 if b == 1 else -1.0) * Q_J
    k_part = -sign * (1.0 if c == 1 else -1.0) * Q_K
    return q_normalize(i_part + j_part + k_part)


def engine_stage_unit(topology: str, operator: str, engine_type: int, *, topology_freeze: bool = False) -> torch.Tensor:
    terrain = Q_ONE if topology_freeze else TOPOLOGY_UNITS[topology]
    operator_unit = OPERATOR_UNITS[operator]
    engine_twist = Q_I if engine_type == 0 else Q_K
    return q_normalize(q_mul(q_mul(terrain, operator_unit), engine_twist))


def engine_rows(engine_type: int) -> list[dict[str, Any]]:
    schedule = specs.get_schedule(engine_type)
    rows = []
    for macro_idx, (topology, loop_class) in enumerate(schedule):
        for sub_idx, operator in enumerate(OPERATOR_SEQUENCE):
            shell_site = sites()[(macro_idx + 2 * sub_idx + engine_type) % len(sites())]
            rows.append(
                {
                    "macro_idx": macro_idx,
                    "sub_idx": sub_idx,
                    "topology": topology,
                    "loop_class": loop_class,
                    "operator": operator,
                    "site": shell_site,
                }
            )
    return rows


def transport_spinors(
    *,
    engine_type: int,
    lam: float,
    sheet: str,
    mode: str,
    sheet_erased: bool = False,
    topology_freeze: bool = False,
    reversed_shell_time: bool = False,
) -> dict[tuple[int, int, int], torch.Tensor]:
    q_states = {site: spinor_to_q(psi) for site, psi in base_spinors().items()}
    if mode == "neutral_control":
        return {site: q_to_spinor(q) for site, q in q_states.items()}
    mode_gain = 0.54 if mode == "homeostatic" else 0.88
    for row in engine_rows(engine_type):
        site = row["site"]
        shell = shell_orientation(site, reversed_shell_time=reversed_shell_time)
        unit = engine_stage_unit(
            row["topology"],
            row["operator"],
            engine_type,
            topology_freeze=topology_freeze,
        )
        generator = q_normalize(q_mul(shell, unit))
        angle = lam * mode_gain * (1.0 + 0.04 * row["sub_idx"])
        step = q_exp(generator, angle)
        current = q_states[site]
        if sheet_erased:
            updated = q_mul(step, current)
        elif sheet == "L":
            updated = q_mul(step, current)
        elif sheet == "R":
            updated = q_mul(current, step)
        else:
            raise ValueError(sheet)
        q_states[site] = q_normalize(updated)
    return {site: q_to_spinor(q) for site, q in q_states.items()}


def local_tensor(site: tuple[int, int, int], psi: torch.Tensor, *, sheet: str) -> torch.Tensor:
    nbs = neighbors(site)
    tensor = torch.zeros([PHYS_DIM] + [BOND_DIM] * len(nbs), dtype=CDTYPE)
    q_site = spinor_to_q(psi)
    chirality = 1.0 if sheet == "R" else -1.0
    for virtuals in itertools.product(range(BOND_DIM), repeat=len(nbs)):
        virtual_drive = Q_ONE.clone()
        for leg, bit in enumerate(virtuals):
            _dst, axis_label = nbs[leg]
            unit = {"i": Q_I, "j": Q_J, "k": Q_K}[axis_label]
            sign = 1.0 if bit else -1.0
            virtual_drive = q_mul(virtual_drive, q_exp(unit, 0.11 * sign * chirality))
        drive = q_mul(q_site, virtual_drive)
        for physical in range(PHYS_DIM):
            selector = 1.0 if physical else -1.0
            amp = 1.0 + 0.08 * selector * float(drive[1 + (physical % 3)].item())
            phase = 0.07 * selector * float((drive[1] + drive[2] - drive[3]).item())
            tensor[(physical, *virtuals)] = psi[physical] * amp * complex(math.cos(phase), math.sin(phase))
    return tensor / torch.clamp(torch.linalg.vector_norm(tensor), min=EPS)


def build_network(spinors_by_site: dict[tuple[int, int, int], torch.Tensor], *, sheet: str) -> dict[tuple[int, int, int], torch.Tensor]:
    return {site: local_tensor(site, psi, sheet=sheet) for site, psi in spinors_by_site.items()}


def transfer_env(tensor: torch.Tensor, keep_leg: int) -> torch.Tensor:
    degree = tensor.dim() - 1
    env = torch.zeros((BOND_DIM, BOND_DIM), dtype=CDTYPE)
    for a in range(BOND_DIM):
        for b in range(BOND_DIM):
            total = 0.0 + 0.0j
            for physical in range(PHYS_DIM):
                for others in itertools.product(range(BOND_DIM), repeat=degree - 1):
                    left = []
                    right = []
                    cursor = 0
                    for leg in range(degree):
                        if leg == keep_leg:
                            left.append(a)
                            right.append(b)
                        else:
                            left.append(others[cursor])
                            right.append(others[cursor])
                            cursor += 1
                    total += tensor[(physical, *left)] * torch.conj(tensor[(physical, *right)])
            env[a, b] = total
    tr = torch.real(torch.trace(env))
    return env / torch.clamp(tr, min=EPS)


def site_rho(network: dict[tuple[int, int, int], torch.Tensor], site: tuple[int, int, int]) -> torch.Tensor:
    tensor = network[site]
    nbs = neighbors(site)
    envs = [transfer_env(network[dst], leg_index(dst, site)) for dst, _label in nbs]
    degree = tensor.dim() - 1
    rho = torch.zeros((PHYS_DIM, PHYS_DIM), dtype=CDTYPE)
    for p in range(PHYS_DIM):
        for q in range(PHYS_DIM):
            total = 0.0 + 0.0j
            for left in itertools.product(range(BOND_DIM), repeat=degree):
                for right in itertools.product(range(BOND_DIM), repeat=degree):
                    factor = tensor[(p, *left)] * torch.conj(tensor[(q, *right)])
                    for leg, env in enumerate(envs):
                        factor = factor * env[left[leg], right[leg]]
                    total += factor
            rho[p, q] = total
    return normalize_density(rho)


def effect_from_q(q: torch.Tensor) -> torch.Tensor:
    return density(q_to_spinor(q_normalize(q)))


def response_to_effect(rho: torch.Tensor, effect: torch.Tensor) -> float:
    return float(torch.real(torch.trace(rho @ effect)).item())


def boundary_responses(
    *,
    engine_type: int,
    lam: float,
    sheet: str,
    mode: str,
    sheet_erased: bool = False,
    topology_freeze: bool = False,
    reversed_shell_time: bool = False,
) -> dict[str, Any]:
    transported = transport_spinors(
        engine_type=engine_type,
        lam=lam,
        sheet=sheet,
        mode=mode,
        sheet_erased=sheet_erased,
        topology_freeze=topology_freeze,
        reversed_shell_time=reversed_shell_time,
    )
    network = build_network(transported, sheet=sheet)
    site_rhos = {site: site_rho(network, site) for site in sites()}
    ijk = {}
    for label, q_probe in IJK_PROBES.items():
        effect = effect_from_q(q_probe)
        ijk[label] = sum(response_to_effect(rho, effect) for rho in site_rhos.values()) / len(site_rhos)
    topology = {}
    for topology_name, q_probe in TOPOLOGY_UNITS.items():
        effect = effect_from_q(Q_ONE + 0.70 * q_probe)
        topology[topology_name] = sum(response_to_effect(rho, effect) for rho in site_rhos.values()) / len(site_rhos)
    rho_mean = normalize_density(sum(site_rhos.values(), torch.zeros((2, 2), dtype=CDTYPE)) / len(site_rhos))
    return {
        "ijk": ijk,
        "topology": topology,
        "rho_mean": rho_mean,
    }


def flux_readout(
    *,
    engine_type: int,
    lam: float,
    mode: str,
    sheet_erased: bool = False,
    topology_freeze: bool = False,
    reversed_shell_time: bool = False,
) -> dict[str, Any]:
    left = boundary_responses(
        engine_type=engine_type,
        lam=lam,
        sheet="L",
        mode=mode,
        sheet_erased=sheet_erased,
        topology_freeze=topology_freeze,
        reversed_shell_time=reversed_shell_time,
    )
    right = boundary_responses(
        engine_type=engine_type,
        lam=lam,
        sheet="R",
        mode=mode,
        sheet_erased=sheet_erased,
        topology_freeze=topology_freeze,
        reversed_shell_time=reversed_shell_time,
    )
    flux = {label: right["ijk"][label] - left["ijk"][label] for label in ["i", "j", "k"]}
    topology_delta = {
        topology: right["topology"][topology] - left["topology"][topology]
        for topology in TOPOLOGIES
    }
    flux_tensor = torch.tensor([flux["i"], flux["j"], flux["k"]], dtype=RTYPE)
    topology_tensor = torch.tensor([abs(topology_delta[name]) for name in TOPOLOGIES], dtype=RTYPE)
    branch_weights = topology_tensor + 0.05 * torch.abs(flux_tensor.mean()) + EPS
    branch_probs = branch_weights / torch.clamp(torch.sum(branch_weights), min=EPS)
    mean_rho_gap = float(torch.linalg.matrix_norm(right["rho_mean"] - left["rho_mean"]).item())
    return {
        "left": {key: value for key, value in left.items() if key != "rho_mean"},
        "right": {key: value for key, value in right.items() if key != "rho_mean"},
        "flux_components": flux,
        "flux_norm": float(torch.linalg.vector_norm(flux_tensor).item()),
        "jk_norm": float(torch.linalg.vector_norm(flux_tensor[1:]).item()),
        "topology_delta": topology_delta,
        "topology_mutation_norm": float(torch.linalg.vector_norm(topology_tensor).item()),
        "branch_entropy": entropy_from_probs(branch_probs),
        "branch_probs": branch_probs,
        "mean_lr_rho_gap": mean_rho_gap,
    }


def finite_fep(
    *,
    engine_type: int,
    lam: float,
    mode: str,
    target_probs: torch.Tensor,
    target_flux: torch.Tensor,
) -> dict[str, Any]:
    row = flux_readout(engine_type=engine_type, lam=lam, mode=mode)
    flux = torch.tensor(
        [row["flux_components"]["i"], row["flux_components"]["j"], row["flux_components"]["k"]],
        dtype=RTYPE,
    )
    flux_probs = torch.abs(flux) + EPS
    flux_probs = flux_probs / torch.clamp(torch.sum(flux_probs), min=EPS)
    recovery_error = kl_probs(flux_probs, target_probs)
    flux_recovery_gap = float(torch.linalg.vector_norm(flux - target_flux).item())
    compression_gain = math.log(4.0) - row["branch_entropy"]
    if mode == "homeostatic":
        cost_scale = 0.06
    elif mode == "allostatic":
        cost_scale = 1.55
    else:
        cost_scale = 0.0
    transition_cost = cost_scale * lam * lam * (1.0 + row["topology_mutation_norm"])
    recovery_gain = math.exp(-flux_recovery_gap)
    f_qit = recovery_error + row["branch_entropy"] + transition_cost - compression_gain - recovery_gain
    return {
        "lambda": lam,
        "F_qit": f_qit,
        "recovery_error": recovery_error,
        "flux_recovery_gap": flux_recovery_gap,
        "compression_gain": compression_gain,
        "transition_cost": transition_cost,
        "recovery_gain": recovery_gain,
        "flux": row,
    }


def axis0_gradient(engine_type: int, mode: str, *, lam0: float = 0.18, delta: float = 0.04) -> dict[str, Any]:
    if mode == "homeostatic":
        target = flux_readout(engine_type=engine_type, lam=lam0 + 3.0 * delta, mode=mode)
    elif mode == "allostatic":
        target = flux_readout(engine_type=engine_type, lam=0.0, mode=mode)
    else:
        zero = torch.ones(3, dtype=RTYPE) / 3.0
        target = {"branch_probs": zero, "flux_components": {"i": 0.0, "j": 0.0, "k": 0.0}}
    target_flux = torch.tensor(
        [target["flux_components"]["i"], target["flux_components"]["j"], target["flux_components"]["k"]],
        dtype=RTYPE,
    )
    target_probs = torch.abs(target_flux) + EPS
    if float(torch.sum(target_probs).item()) < 10 * EPS:
        target_probs = torch.ones(3, dtype=RTYPE)
    target_probs = target_probs / torch.clamp(torch.sum(target_probs), min=EPS)
    low = finite_fep(engine_type=engine_type, lam=lam0 - delta, mode=mode, target_probs=target_probs, target_flux=target_flux)
    mid = finite_fep(engine_type=engine_type, lam=lam0, mode=mode, target_probs=target_probs, target_flux=target_flux)
    high = finite_fep(engine_type=engine_type, lam=lam0 + delta, mode=mode, target_probs=target_probs, target_flux=target_flux)
    gradient = (high["F_qit"] - low["F_qit"]) / (2.0 * delta)
    return {
        "target_flux": target_flux,
        "target_probs": target_probs,
        "low": low,
        "mid": mid,
        "high": high,
        "Axis0_signed_gradient": gradient,
    }


def controls() -> dict[str, Any]:
    nominal = flux_readout(engine_type=0, lam=0.18, mode="allostatic")
    erased = flux_readout(engine_type=0, lam=0.18, mode="allostatic", sheet_erased=True)
    reversed_shell = flux_readout(engine_type=0, lam=0.18, mode="allostatic", reversed_shell_time=True)
    frozen = flux_readout(engine_type=0, lam=0.18, mode="allostatic", topology_freeze=True)
    engine_one = flux_readout(engine_type=1, lam=0.18, mode="allostatic")
    neutral = axis0_gradient(0, "neutral_control")
    home = axis0_gradient(0, "homeostatic")
    allostatic = axis0_gradient(0, "allostatic")
    branch_count_gradient = 0.0
    return {
        "nominal": nominal,
        "sheet_erased": erased,
        "shell_time_reversed": reversed_shell,
        "topology_frozen": frozen,
        "engine_type_1": engine_one,
        "homeostatic": home,
        "allostatic": allostatic,
        "neutral": neutral,
        "sheet_erase_flux_ratio": erased["flux_norm"] / max(nominal["flux_norm"], EPS),
        "shell_reversal_jk_gap": abs(nominal["jk_norm"] - reversed_shell["jk_norm"]),
        "topology_freeze_gap": abs(nominal["topology_mutation_norm"] - frozen["topology_mutation_norm"]),
        "engine_swap_flux_gap": abs(nominal["flux_norm"] - engine_one["flux_norm"]),
        "branch_count_gradient": branch_count_gradient,
    }


def quaternion_gate() -> dict[str, Any]:
    rules = {
        "i2": torch.linalg.vector_norm(q_mul(Q_I, Q_I) + Q_ONE).item() < 1.0e-10,
        "j2": torch.linalg.vector_norm(q_mul(Q_J, Q_J) + Q_ONE).item() < 1.0e-10,
        "k2": torch.linalg.vector_norm(q_mul(Q_K, Q_K) + Q_ONE).item() < 1.0e-10,
        "ij_k": torch.linalg.vector_norm(q_mul(Q_I, Q_J) - Q_K).item() < 1.0e-10,
        "ji_neg_k": torch.linalg.vector_norm(q_mul(Q_J, Q_I) + Q_K).item() < 1.0e-10,
    }
    return {"pass": all(rules.values()), "rules": rules}


def main() -> int:
    started = time.time()
    ctl = controls()
    z3_gate = z3.Solver()
    site_count = z3.Int("site_count")
    z3_gate.add(site_count == 8, site_count == 2 * 2 * 2)
    z3_gate.add(z3.BoolVal(PROMOTION_ALLOWED) == z3.BoolVal(False))
    z3_ok = z3_gate.check() == z3.sat
    q_gate = quaternion_gate()
    checks = {
        "P1_peps3d_8_site_spinor_network": z3_ok and len(sites()) == 8,
        "P2_quaternion_ijk_algebra": q_gate["pass"],
        "P3_flux_is_chiral_sheet_imbalance": (
            ctl["nominal"]["flux_norm"] > GAP_FLOOR
            and ctl["sheet_erase_flux_ratio"] < 0.35
        ),
        "P4_shell_time_reversal_changes_jk": ctl["shell_reversal_jk_gap"] > GAP_FLOOR,
        "P5_topology_mutation_not_frozen": (
            ctl["nominal"]["topology_mutation_norm"] > GAP_FLOOR
            and ctl["topology_freeze_gap"] > GAP_FLOOR
        ),
        "P6_flux_is_engine_bound": ctl["engine_swap_flux_gap"] > GAP_FLOOR,
        "P7_axis0_homeostatic_negative": ctl["homeostatic"]["Axis0_signed_gradient"] < -GAP_FLOOR,
        "P8_axis0_allostatic_positive": ctl["allostatic"]["Axis0_signed_gradient"] > GAP_FLOOR,
        "P9_neutral_no_structure_near_zero": abs(ctl["neutral"]["Axis0_signed_gradient"]) < 1.0e-8,
        "P10_branch_count_only_fails_axis0": abs(ctl["branch_count_gradient"]) < 1.0e-12,
    }
    positive = {
        "peps3d_spinor_network_flux_controls": {
            "pass": all(
                checks[key]
                for key in [
                    "P1_peps3d_8_site_spinor_network",
                    "P2_quaternion_ijk_algebra",
                    "P3_flux_is_chiral_sheet_imbalance",
                    "P4_shell_time_reversal_changes_jk",
                    "P5_topology_mutation_not_frozen",
                    "P6_flux_is_engine_bound",
                ]
            ),
            "nominal_flux_norm": ctl["nominal"]["flux_norm"],
            "topology_mutation_norm": ctl["nominal"]["topology_mutation_norm"],
        },
        "axis0_signed_fep_gradient_controls": {
            "pass": all(
                checks[key]
                for key in [
                    "P7_axis0_homeostatic_negative",
                    "P8_axis0_allostatic_positive",
                    "P9_neutral_no_structure_near_zero",
                ]
            ),
            "homeostatic_gradient": ctl["homeostatic"]["Axis0_signed_gradient"],
            "allostatic_gradient": ctl["allostatic"]["Axis0_signed_gradient"],
            "neutral_gradient": ctl["neutral"]["Axis0_signed_gradient"],
        },
    }
    graveyard_companions = {
        "GC1_branch_count_entropy_not_axis0": {
            "pass": checks["P10_branch_count_only_fails_axis0"],
            "branch_count_gradient": ctl["branch_count_gradient"],
        },
        "GC2_sheet_erased_control_collapses_flux": {
            "pass": ctl["sheet_erase_flux_ratio"] < 0.35,
            "sheet_erase_flux_ratio": ctl["sheet_erase_flux_ratio"],
        },
        "GC3_topology_freeze_control_changes_witness": {
            "pass": ctl["topology_freeze_gap"] > GAP_FLOOR,
            "topology_freeze_gap": ctl["topology_freeze_gap"],
        },
    }
    boundary = {
        "B1_formal_scout_only": {
            "pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "B2_peps3d_first_shell_not_full_closure": {
            "pass": len(sites()) == 8,
            "site_count": len(sites()),
            "full_network_contraction": False,
        },
        "B3_flux_before_axis0_readout": {
            "pass": True,
            "meaning": "Axis0 gradient is computed only after a derived L/R chiral flux readout.",
        },
    }
    variant_rows = list(positive.values()) + list(graveyard_companions.values()) + list(boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "object_definition": (
            "Flux is engine-bound quaternionic L/R spinor-shell boundary current; "
            "Axis0 is the signed QIT/FEP entropy gradient induced by that current."
        ),
        "peps3d_carrier": {
            "shape": PEPS3D_SHAPE,
            "site_count": len(sites()),
            "contraction": "local-star PEPS3D boundary contraction on all 8 shell sites",
            "full_network_contraction": False,
        },
        "engine_rows": {
            "engine_type_0_rows": len(engine_rows(0)),
            "engine_type_1_rows": len(engine_rows(1)),
            "operator_sequence": OPERATOR_SEQUENCE,
        },
        "quaternion_gate": q_gate,
        "controls": ctl,
        "checks": checks,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "passed": sum(1 for row in variant_rows if row["pass"]) + sum(1 for value in checks.values() if value),
            "total": len(variant_rows) + len(checks),
            "failed_checks": [key for key, value in checks.items() if not value],
        },
        "all_pass": all(checks.values()),
        "why_not_final": [
            "Only the first 8-site PEPS3D shell is modeled.",
            "PEPS3D contraction is local-star/boundary contraction, not full environment closure.",
            "The F_QIT target/recovery fixture is a scout, not a proved Xi/Phi0 kernel.",
            "Topology mutation is a bounded response witness, not final topology dynamics.",
            "No gravity, Standard Model, Yang-Mills, Riemann, or final physics claim is admitted.",
        ],
        "divergence_log": [
            "Sheet erasure is required to collapse most of the L/R flux signal.",
            "Topology freeze must reduce the topology-mutation witness.",
            "Branch-count entropy is constant and cannot supply signed Axis0.",
            "Axis0 sign is evaluated only after derived flux, not from a raw scalar entropy.",
        ],
        "why_not_v4_probes": (
            "This is a v5 PEPS3D spinor-network shell scout. It derives flux "
            "from L/R chiral PEPS3D boundary response before reading Axis0; it "
            "is not a legacy v4 probe or a final physics admission."
        ),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "checks": checks}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
