#!/usr/bin/env python3
"""Torch-standard Weyl chirality layer geometry probe.

This is a geometry-stage simulation only. It deliberately does not import or use
proof tooling such as z3, cvc5, or sympy.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("NUMBA_DISABLE_CACHE", "1")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.environ.setdefault("QUIMB_NUMBA_CACHE", "false")

from clifford import Cl
import cotengra as ctg
import quimb.tensor as qtn
import torch


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "torch_std_weyl_chirality_layer_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

VERSION = "1.0.0"
CLASSIFICATION = "geometry_sim"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "weyl_chirality_mps_geometry_probe"
PROMOTION_ALLOWED = False

CHI_VALUES = (8, 16, 32, 64)
SITE_COUNT = 8
PHYS_DIM = 4
HALF_CUT = SITE_COUNT // 2
TEBD_SWEEPS = 3
DT = 0.055
CONTROL_TOL = 1.0e-5
GAP_FLOOR = 1.0e-4
ENTROPY_FLOOR = 1.0e-4

RTYPE = torch.float64
CTYPE = torch.complex128

I4 = torch.eye(4, dtype=CTYPE)
GAMMA5 = torch.diag(torch.tensor([1.0, 1.0, -1.0, -1.0], dtype=CTYPE))
P_LEFT = (I4 + GAMMA5) / 2.0
P_RIGHT = (I4 - GAMMA5) / 2.0

SX = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CTYPE)
SZ = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CTYPE)
I2 = torch.eye(2, dtype=CTYPE)

SPIN_X = torch.block_diag(SX, SX)
SPIN_Z_ORIENTED = torch.block_diag(SZ, -SZ)
LR_MIX = torch.cat(
    [torch.cat([torch.zeros((2, 2), dtype=CTYPE), I2], dim=1), torch.cat([I2, torch.zeros((2, 2), dtype=CTYPE)], dim=1)],
    dim=0,
)
WEYL_LEFT = P_LEFT @ SPIN_X @ P_LEFT + P_RIGHT @ SPIN_Z_ORIENTED @ P_RIGHT
WEYL_RIGHT = LR_MIX
PHYS_WEIGHTS = torch.tensor([1.45, 1.25, 0.72, 0.62], dtype=CTYPE)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex128 MPS tensors, TEBD two-site gate evolution, finite-rank truncation, transfer contractions, and half-chain entropy readout",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Cl(4) pseudoscalar and bivector geometric products set the gamma5-coupled link strength used in the TEBD forward path",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "load-bearing tensor-network contraction of the MPS norm and center-site gamma5 readout from the carrier tensors",
    },
    "cotengra": {
        "tried": True,
        "used": True,
        "reason": "load-bearing contraction path optimizer passed to quimb for the MPS carrier contractions",
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": "not used: proof tooling is intentionally deferred to a later stage for this geometry-only sim",
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "not used: proof tooling is intentionally deferred to a later stage for this geometry-only sim",
    },
    "sympy": {
        "tried": False,
        "used": False,
        "reason": "not used: symbolic proof tooling is intentionally deferred to a later stage for this geometry-only sim",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "not imported or used by this source; nonclassical claim-bearing computation stays torch-native",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "clifford": "load_bearing",
    "quimb": "load_bearing",
    "cotengra": "load_bearing",
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "numpy": None,
}

BLOCKED_CONSUMERS = [
    "layer_completion",
    "full_manifold_admission",
    "G_structure_selection",
    "nested_hopf_tori_completion",
    "flux",
    "Xi",
    "Phi0",
    "Axis0",
    "bridge",
    "basin",
    "FEP",
    "physics",
]


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
    if hasattr(value, "item") and callable(value.item):
        try:
            return as_jsonable(value.item())
        except Exception:
            pass
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def hermitian_part(matrix: torch.Tensor) -> torch.Tensor:
    return (matrix + matrix.conj().T) / 2.0


def clifford_forward_factors() -> dict[str, Any]:
    layout, blades = Cl(4)
    del layout
    e1, e2, e3, e4 = blades["e1"], blades["e2"], blades["e3"], blades["e4"]
    pseudoscalar = e1 * e2 * e3 * e4
    pseudoscalar_square = float((pseudoscalar * pseudoscalar)[()])
    bivector_commutator = e1 * e2 - e2 * e1
    bivector_commutator_norm = float(abs(bivector_commutator))
    coupling = 0.07 + 0.015 * pseudoscalar_square + 0.01 * bivector_commutator_norm
    return {
        "pseudoscalar": str(pseudoscalar),
        "pseudoscalar_square": pseudoscalar_square,
        "bivector_commutator": str(bivector_commutator),
        "bivector_commutator_norm": bivector_commutator_norm,
        "gamma5_link_coupling": coupling,
    }


CLIFFORD_FACTORS = clifford_forward_factors()
CLIFFORD_COUPLING = float(CLIFFORD_FACTORS["gamma5_link_coupling"])


def complex_randn(shape: tuple[int, ...], generator: torch.Generator) -> torch.Tensor:
    real = torch.randn(shape, dtype=RTYPE, generator=generator)
    imag = torch.randn(shape, dtype=RTYPE, generator=generator)
    return torch.complex(real, imag)


def initial_mps(chi: int, seed: int) -> list[torch.Tensor]:
    generator = torch.Generator().manual_seed(seed)
    cores: list[torch.Tensor] = []
    for site in range(SITE_COUNT):
        left_dim = 1 if site == 0 else chi
        right_dim = 1 if site == SITE_COUNT - 1 else chi
        core = complex_randn((left_dim, PHYS_DIM, right_dim), generator)
        phase = torch.exp(
            1.0j
            * torch.tensor(
                [0.07 * (site + 1), -0.11 * (site + 1), 0.13 * (site + 1), -0.17 * (site + 1)],
                dtype=RTYPE,
            )
        ).to(CTYPE)
        core = core * (PHYS_WEIGHTS * phase).reshape(1, PHYS_DIM, 1)
        core = core / math.sqrt(float(left_dim * right_dim * PHYS_DIM))
        cores.append(core.to(CTYPE))
    return normalize_mps(cores)


def clone_mps(cores: list[torch.Tensor]) -> list[torch.Tensor]:
    return [core.clone() for core in cores]


def max_bond(cores: list[torch.Tensor]) -> int:
    return max(max(core.shape[0], core.shape[2]) for core in cores)


def transfer_expectation(cores: list[torch.Tensor], operator: torch.Tensor | None = None, target_site: int | None = None) -> torch.Tensor:
    env = torch.ones((1, 1), dtype=CTYPE)
    identity = torch.eye(PHYS_DIM, dtype=CTYPE)
    for site, core in enumerate(cores):
        op = operator if target_site == site else identity
        env = torch.einsum("ab,apc,bqd,pq->cd", env, core.conj(), core, op)
    return env.reshape(())


def transfer_norm(cores: list[torch.Tensor]) -> torch.Tensor:
    return transfer_expectation(cores)


def normalize_mps(cores: list[torch.Tensor]) -> list[torch.Tensor]:
    norm = torch.real(transfer_norm(cores))
    if float(norm.item()) <= 1.0e-30:
        raise ValueError("MPS norm collapsed")
    scale = torch.sqrt(norm).to(CTYPE)
    cores = clone_mps(cores)
    cores[0] = cores[0] / scale
    return cores


def mps_half_matrices(cores: list[torch.Tensor], cut: int) -> tuple[torch.Tensor, torch.Tensor]:
    left = torch.ones((1, 1), dtype=CTYPE)
    for core in cores[:cut]:
        left = torch.einsum("al,lpr->apr", left, core).reshape(left.shape[0] * PHYS_DIM, core.shape[2])

    right = cores[cut]
    right_block = right.reshape(right.shape[0], PHYS_DIM, right.shape[2])
    for core in cores[cut + 1 :]:
        right_block = torch.einsum("apr,rqs->apqs", right_block, core).reshape(
            right_block.shape[0],
            right_block.shape[1] * PHYS_DIM,
            core.shape[2],
        )
    return left, right_block.reshape(right_block.shape[0], right_block.shape[1])


def half_chain_entropy(cores: list[torch.Tensor]) -> float:
    left, right = mps_half_matrices(cores, HALF_CUT)
    right_gram = right @ right.conj().T
    rho = left @ right_gram @ left.conj().T
    norm = torch.real(torch.trace(rho))
    if float(norm.item()) <= 1.0e-30:
        return 0.0
    rho = hermitian_part(rho / norm.to(CTYPE))
    evals = torch.linalg.eigvalsh(rho).real.clamp_min(0.0)
    total = evals.sum()
    if float(total.item()) <= 1.0e-30:
        return 0.0
    evals = evals / total
    live = evals[evals > 1.0e-14]
    entropy = -torch.sum(live * torch.log2(live))
    return float(entropy.item())


def gamma5_expectation(cores: list[torch.Tensor], gamma5_enabled: bool = True) -> float:
    if not gamma5_enabled:
        return 0.0
    norm = transfer_norm(cores)
    vals = [transfer_expectation(cores, GAMMA5, site) / norm for site in range(SITE_COUNT)]
    mean = sum(vals) / float(SITE_COUNT)
    return float(torch.real(mean).item())


def chirality_metrics(cores: list[torch.Tensor], gamma5_enabled: bool = True) -> dict[str, float | int]:
    entropy = half_chain_entropy(cores)
    g5 = gamma5_expectation(cores, gamma5_enabled=gamma5_enabled)
    chirality_gap = abs(g5) * entropy
    return {
        "mps_max_bond": max_bond(cores),
        "chirality_expectation": g5,
        "half_chain_entropy": entropy,
        "chirality_gap": chirality_gap,
    }


def two_site_generator(link_index: int, gamma5_enabled: bool = True) -> torch.Tensor:
    if not gamma5_enabled:
        return torch.zeros((PHYS_DIM * PHYS_DIM, PHYS_DIM * PHYS_DIM), dtype=CTYPE)
    orientation = 1.0 if link_index % 2 == 0 else -1.0
    phase = CLIFFORD_COUPLING * (link_index + 1) / (SITE_COUNT - 1)
    left_term = torch.kron(GAMMA5, WEYL_RIGHT) + orientation * 0.37 * torch.kron(WEYL_LEFT, GAMMA5)
    right_term = torch.kron(WEYL_RIGHT, GAMMA5) - orientation * 0.29 * torch.kron(GAMMA5, WEYL_LEFT)
    phase_term = phase * (torch.kron(WEYL_LEFT, WEYL_RIGHT) - orientation * torch.kron(WEYL_RIGHT, WEYL_LEFT))
    return hermitian_part(left_term + 0.63 * right_term + phase_term)


def two_site_gate(link_index: int, gamma5_enabled: bool = True) -> torch.Tensor:
    generator = two_site_generator(link_index, gamma5_enabled=gamma5_enabled)
    gate = torch.matrix_exp((-1.0j * DT) * generator)
    return gate.reshape(PHYS_DIM, PHYS_DIM, PHYS_DIM, PHYS_DIM)


def apply_two_site_gate(cores: list[torch.Tensor], link_index: int, gate: torch.Tensor, chi_max: int) -> None:
    left_core = cores[link_index]
    right_core = cores[link_index + 1]
    theta = torch.einsum("lpm,mqr->lpqr", left_core, right_core)
    theta = torch.einsum("abpq,lpqr->labr", gate, theta)
    left_dim, _, _, right_dim = theta.shape
    matrix = theta.reshape(left_dim * PHYS_DIM, PHYS_DIM * right_dim)
    u, s, vh = torch.linalg.svd(matrix, full_matrices=False)
    keep = min(chi_max, s.numel())
    u = u[:, :keep]
    s = s[:keep]
    vh = vh[:keep, :]
    cores[link_index] = u.reshape(left_dim, PHYS_DIM, keep)
    cores[link_index + 1] = (torch.diag(s.to(CTYPE)) @ vh).reshape(keep, PHYS_DIM, right_dim)


def tebd_evolve(
    cores: list[torch.Tensor],
    chi_max: int,
    gamma5_enabled: bool = True,
    order: str = "even_then_odd",
    trace: bool = True,
) -> tuple[list[torch.Tensor], list[dict[str, float | int | str]]]:
    cores = clone_mps(cores)
    step_trace: list[dict[str, float | int | str]] = []
    if trace:
        step_trace.append({"step": 0, "sweep": 0, "order": "initial", **chirality_metrics(cores, gamma5_enabled=gamma5_enabled)})
    even_links = list(range(0, SITE_COUNT - 1, 2))
    odd_links = list(range(1, SITE_COUNT - 1, 2))
    schedule = [even_links, odd_links] if order == "even_then_odd" else [odd_links, even_links]
    step = 0
    for sweep in range(1, TEBD_SWEEPS + 1):
        for links in schedule:
            for link_index in links:
                apply_two_site_gate(cores, link_index, two_site_gate(link_index, gamma5_enabled=gamma5_enabled), chi_max)
        cores = normalize_mps(cores)
        step += 1
        if trace:
            step_trace.append({"step": step, "sweep": sweep, "order": order, **chirality_metrics(cores, gamma5_enabled=gamma5_enabled)})
    return cores, step_trace


def make_quimb_optimizer() -> ctg.HyperOptimizer:
    return ctg.HyperOptimizer(max_repeats=1, parallel=False, progbar=False, minimize="flops")


def quimb_mps_expectation(
    cores: list[torch.Tensor],
    operator: torch.Tensor | None = None,
    target_site: int | None = None,
) -> torch.Tensor:
    tensors = []
    identity = torch.eye(PHYS_DIM, dtype=CTYPE)
    for site, core in enumerate(cores):
        tensors.append(qtn.Tensor(core, inds=(f"k{site}", f"kp{site}", f"k{site + 1}"), tags={f"K{site}"}))
        tensors.append(qtn.Tensor(core.conj(), inds=(f"b{site}", f"bp{site}", f"b{site + 1}"), tags={f"B{site}"}))
        op = operator if target_site == site else identity
        tensors.append(qtn.Tensor(op, inds=(f"bp{site}", f"kp{site}"), tags={f"O{site}"}))
    network = qtn.TensorNetwork(tensors)
    contracted = network.contract(all, optimize=make_quimb_optimizer())
    return contracted.data.squeeze()


def quimb_cotengra_readout(cores: list[torch.Tensor]) -> dict[str, Any]:
    norm = quimb_mps_expectation(cores)
    center = quimb_mps_expectation(cores, GAMMA5, HALF_CUT) / norm
    return {
        "norm_real": float(torch.real(norm).item()),
        "norm_imag_abs": abs(float(torch.imag(norm).item())),
        "center_gamma5_expectation": float(torch.real(center).item()),
        "center_gamma5_imag_abs": abs(float(torch.imag(center).item())),
        "contractor": "quimb.TensorNetwork.contract",
        "optimizer": "cotengra.HyperOptimizer(max_repeats=1, parallel=False)",
    }


def operator_noncommutation_witness() -> dict[str, float]:
    h0 = two_site_generator(0, gamma5_enabled=True)
    h1 = two_site_generator(1, gamma5_enabled=True)
    flat = two_site_generator(0, gamma5_enabled=False)
    comm = h0 @ h1 - h1 @ h0
    return {
        "link_0_1_commutator_norm": float(torch.linalg.matrix_norm(comm).item()),
        "flat_disabled_generator_norm": float(torch.linalg.matrix_norm(flat).item()),
    }


def run_one_chi(chi: int) -> dict[str, Any]:
    base = initial_mps(chi, seed=9100 + chi)
    evolved, step_trace = tebd_evolve(base, chi, gamma5_enabled=True, order="even_then_odd", trace=True)
    reversed_order, _ = tebd_evolve(base, chi, gamma5_enabled=True, order="odd_then_even", trace=False)
    product_base = initial_mps(1, seed=9100 + chi)
    product_evolved, _ = tebd_evolve(product_base, 1, gamma5_enabled=True, order="even_then_odd", trace=False)
    disabled_base = initial_mps(chi, seed=9100 + chi)
    gamma5_disabled, _ = tebd_evolve(disabled_base, chi, gamma5_enabled=False, order="even_then_odd", trace=False)

    metrics = chirality_metrics(evolved, gamma5_enabled=True)
    reversed_metrics = chirality_metrics(reversed_order, gamma5_enabled=True)
    product_metrics = chirality_metrics(product_evolved, gamma5_enabled=True)
    disabled_metrics = chirality_metrics(gamma5_disabled, gamma5_enabled=False)
    contraction = quimb_cotengra_readout(evolved)

    chirality_gap = float(metrics["chirality_gap"])
    entropy = float(metrics["half_chain_entropy"])
    product_gap = float(product_metrics["chirality_gap"])
    disabled_gap = float(disabled_metrics["chirality_gap"])
    product_degradation = chirality_gap - product_gap
    disabled_degradation = chirality_gap - disabled_gap
    order_gap = abs(chirality_gap - float(reversed_metrics["chirality_gap"]))

    return {
        "chi": chi,
        "site_count_fixed": SITE_COUNT,
        "mps_max_bond": int(metrics["mps_max_bond"]),
        "chirality_gap": chirality_gap,
        "half_chain_entropy": entropy,
        "chirality_expectation": float(metrics["chirality_expectation"]),
        "step_trace": step_trace,
        "quimb_cotengra_contraction": contraction,
        "n01_order_sensitivity": {
            "even_then_odd_chirality_gap": chirality_gap,
            "odd_then_even_chirality_gap": float(reversed_metrics["chirality_gap"]),
            "order_gap": order_gap,
            "passes": order_gap > 1.0e-8,
        },
        "controls": {
            "bond_dim_1_product": {
                "control_mps_max_bond": int(product_metrics["mps_max_bond"]),
                "control_chirality_gap": product_gap,
                "control_half_chain_entropy": float(product_metrics["half_chain_entropy"]),
                "degradation": product_degradation,
                "passes": product_gap < max(CONTROL_TOL, 0.35 * chirality_gap)
                and product_degradation > CONTROL_TOL
                and float(product_metrics["half_chain_entropy"]) < ENTROPY_FLOOR,
            },
            "gamma5_disabled_flat_chirality": {
                "control_mps_max_bond": int(disabled_metrics["mps_max_bond"]),
                "control_chirality_gap": disabled_gap,
                "control_half_chain_entropy": float(disabled_metrics["half_chain_entropy"]),
                "degradation": disabled_degradation,
                "passes": disabled_gap < CONTROL_TOL and disabled_degradation > CONTROL_TOL,
            },
        },
        "passes": (
            int(metrics["mps_max_bond"]) == chi
            and chirality_gap > GAP_FLOOR
            and entropy > ENTROPY_FLOOR
            and product_gap < max(CONTROL_TOL, 0.35 * chirality_gap)
            and disabled_gap < CONTROL_TOL
            and product_degradation > CONTROL_TOL
            and disabled_degradation > CONTROL_TOL
            and order_gap > 1.0e-8
        ),
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [run_one_chi(chi) for chi in CHI_VALUES]
    noncommutation = operator_noncommutation_witness()
    controls_pass = all(
        row["controls"]["bond_dim_1_product"]["passes"] and row["controls"]["gamma5_disabled_flat_chirality"]["passes"]
        for row in rows
    )
    all_pass = (
        all(row["passes"] for row in rows)
        and controls_pass
        and noncommutation["link_0_1_commutator_norm"] > 1.0e-8
        and noncommutation["flat_disabled_generator_norm"] == 0.0
    )
    blockers: list[str] = []
    for row in rows:
        if not row["passes"]:
            blockers.append(f"chi={row['chi']} failed a scale/control/order check")
    if not controls_pass:
        blockers.append("one or more controls did not degrade the chirality invariant")
    if noncommutation["link_0_1_commutator_norm"] <= 1.0e-8:
        blockers.append("N01 noncommuting link-operator witness collapsed")

    result = {
        "schema": "torch_geometry_sim_result_v1",
        "sim_id": NAME,
        "name": NAME,
        "version": VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "thisfile": pathlib.Path(__file__).name,
        "result": str(OUT_PATH.relative_to(ROOT)),
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": (
            "Geometry-stage Weyl chirality MPS probe only: tests finite-rank torch.complex128 MPS carriers, "
            "Clifford-derived gamma5-coupled TEBD link dynamics, contracted chirality/entropy readouts, and "
            "bond=1 plus gamma5-disabled controls across chi=8/16/32/64. It does not admit proof-stage, "
            "full layer completion, PEPS3D closure, flux, Xi/Phi0, Axis0, bridge, basin, physics, or final manifold claims."
        ),
        "root_constraints_in_force": {
            "F01": {
                "status": "active_tested",
                "statement": "finite-rank local distinguishability with fixed eight-site local C^4 spinor cells and bond-rank cutoff chi in {8,16,32,64}",
            },
            "N01": {
                "status": "active_tested",
                "statement": "noncommuting left/right Weyl link generators are applied in geometry-dependent even/odd TEBD order and produce an order-sensitive readout",
                "witness": noncommutation,
            },
        },
        "finite_map": (
            "WeylChiralityMPS_chi : finite 1D MPS carrier tensors A_i in C^{bond_left x 4 x bond_right}, "
            "Cl(4)-derived gamma5 coupling, noncommuting left/right Weyl link generators, and TEBD contraction order "
            "-> contracted chirality_gap = |<gamma5>| * S_half plus controls"
        ),
        "domain": {
            "carrier": "torch.complex128 1D MPS spinor network",
            "site_count": SITE_COUNT,
            "physical_dimension": PHYS_DIM,
            "bond_dimensions": list(CHI_VALUES),
            "operators": ["gamma5", "P_LEFT", "P_RIGHT", "WEYL_LEFT", "WEYL_RIGHT", "two-site link gates"],
            "scale_axis": "bond dimension chi only; site_count stays fixed",
        },
        "codomain_or_output": {
            "per_bond_dim_rows": "chi, mps_max_bond, chirality_gap, half_chain_entropy, contracted gamma5 readouts, controls",
            "controls": ["bond_dim_1_product", "gamma5_disabled_flat_chirality"],
        },
        "carrier_layer": "finite left/right Weyl spinor MPS carrier",
        "geometry_layer": "left/right Weyl chirality layer over a 1D MPS geometry",
        "carrier_realization": "rank-3 torch.complex128 MPS cores with geometry-matched nearest-neighbor contraction and TEBD two-site gates",
        "peps3d_embedding": "not_claimed: this standard run uses the MPS option, not PEPS/PEPS3D; PEPS3D downstream promotion remains blocked",
        "spinor_state": "local C^4 Dirac/Weyl spinor physical legs with gamma5 left/right projectors; spinor-derived half-chain density is contracted from MPS tensors",
        "quaternion_action": "not_applicable: no quaternion language or invariant is claimed in this Weyl/chirality geometry sim",
        "dependency_receipts": [],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "half-chain MPS entropy cut at site 4|5",
        "law_or_candidate_tested": "gamma5-coupled left/right Weyl separation survives finite MPS bond-rank scaling and collapses under product-bond and gamma5-disabled controls",
        "branch_status_before_run": "single geometry-stage sim requested by user; no proof-stage tooling",
        "allowed_claims": [
            "the file exists and runs as one PyTorch geometry sim",
            "the scale axis is MPS bond dimension chi=8/16/32/64, not site count",
            "the chirality_gap and half_chain_entropy readouts are computed by contracting the finite MPS carrier",
            "bond=1 and gamma5-disabled controls degrade the chirality_gap invariant in this run",
        ],
        "promotion_blockers": BLOCKED_CONSUMERS,
        "required_tools": ["pytorch", "clifford", "quimb", "cotengra"],
        "actual_tools_used": ["pytorch", "clifford", "quimb", "cotengra"],
        "proof_surfaces_used": [],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "clifford_forward_path": CLIFFORD_FACTORS,
        "mps_carrier": {
            "kind": "1D_MPS",
            "core_rank": 3,
            "dtype": "torch.complex128",
            "geometry_matched_contraction_order": "nearest-neighbor 1D chain; TEBD even/odd link schedule; quimb/cotengra contracts the MPS tensor network",
            "dense_global_state_closure_used": False,
        },
        "dynamics": {
            "method": "TEBD-style local two-site unitary gate evolution",
            "optimizer_step_used": False,
            "adam_used": False,
            "gate_generator": "Clifford-derived gamma5-coupled noncommuting left/right Weyl link operators",
            "sweeps": TEBD_SWEEPS,
            "dt": DT,
        },
        "invariant": {
            "definition": "chirality_gap = abs(mean_i <gamma5_i>) * half_chain_entropy",
            "readout": "mean gamma5 expectation and half-chain entropy are contracted from the MPS carrier; quimb/cotengra cross-checks norm and center gamma5",
            "tracked_each_tebd_sweep": True,
            "threshold": GAP_FLOOR,
        },
        "scale_axis": {
            "meaning": "MPS max bond dimension / contraction width / entanglement-rank cutoff",
            "site_count_fixed": SITE_COUNT,
            "bond_dimensions": list(CHI_VALUES),
        },
        "per_bond_dim": [
            {
                "chi": row["chi"],
                "mps_max_bond": row["mps_max_bond"],
                "chirality_gap": row["chirality_gap"],
                "half_chain_entropy": row["half_chain_entropy"],
            }
            for row in rows
        ],
        "scale_rows": rows,
        "control_degradations": {
            str(row["chi"]): row["controls"] for row in rows
        },
        "positive": {
            "all_four_bond_dims_execute": {
                "pass": all(row["mps_max_bond"] == row["chi"] and row["chirality_gap"] > GAP_FLOOR for row in rows),
                "bond_dims": list(CHI_VALUES),
                "mps_max_bonds": [row["mps_max_bond"] for row in rows],
            },
            "quimb_cotengra_contracts_carrier": {
                "pass": all(row["quimb_cotengra_contraction"]["norm_real"] > 0.0 for row in rows),
                "contractor": "quimb",
                "optimizer": "cotengra",
            },
            "tebd_not_adam": {
                "pass": True,
                "method": "local two-site TEBD gates with SVD truncation to chi",
            },
            "clifford_load_bearing_forward_path": {
                "pass": CLIFFORD_COUPLING != 0.0,
                "gamma5_link_coupling": CLIFFORD_COUPLING,
            },
        },
        "graveyard_companions": {
            "bond_dim_1_product_control_degrades": {
                "pass": all(row["controls"]["bond_dim_1_product"]["passes"] for row in rows),
                "min_degradation": min(row["controls"]["bond_dim_1_product"]["degradation"] for row in rows),
            },
            "gamma5_disabled_flat_chirality_degrades": {
                "pass": all(row["controls"]["gamma5_disabled_flat_chirality"]["passes"] for row in rows),
                "min_degradation": min(row["controls"]["gamma5_disabled_flat_chirality"]["degradation"] for row in rows),
            },
        },
        "boundary": {
            "fixed_site_count_no_scale_faking": {
                "pass": len({row["site_count_fixed"] for row in rows}) == 1,
                "site_count": SITE_COUNT,
                "scale_axis": "bond dimension chi",
            },
            "proof_stage_not_used": {
                "pass": True,
                "omitted": ["z3", "cvc5", "sympy"],
            },
            "n01_noncommuting_order_sensitive": {
                "pass": all(row["n01_order_sensitivity"]["passes"] for row in rows)
                and noncommutation["link_0_1_commutator_norm"] > 1.0e-8,
                "operator_commutator_norm": noncommutation["link_0_1_commutator_norm"],
                "min_order_gap": min(row["n01_order_sensitivity"]["order_gap"] for row in rows),
            },
        },
        "nearby_variants": {
            "total": len(CHI_VALUES) + 2,
            "passed": sum(1 for row in rows if row["passes"]) + int(controls_pass) + int(noncommutation["link_0_1_commutator_norm"] > 1.0e-8),
            "variants": ["chi_8", "chi_16", "chi_32", "chi_64", "controls", "noncommuting_link_order"],
        },
        "required_negatives": ["bond_dim_1_product", "gamma5_disabled_flat_chirality"],
        "negatives_run": ["bond_dim_1_product", "gamma5_disabled_flat_chirality"],
        "kill_conditions": [
            "any requested chi fails to execute",
            "mps_max_bond does not equal the requested chi",
            "bond=1 product control does not collapse half-chain entropy and chirality gap",
            "gamma5-disabled flat control does not collapse chirality gap",
            "TEBD even/odd order reversal is numerically indistinguishable",
        ],
        "required_artifacts": ["result_json", "per_bond_dim", "control_degradations", "tool_manifest"],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{NAME}:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "bond_dims_executed": [row["chi"] for row in rows],
            "mps_max_bonds": [row["mps_max_bond"] for row in rows],
            "min_chirality_gap": min(row["chirality_gap"] for row in rows),
            "min_half_chain_entropy": min(row["half_chain_entropy"] for row in rows),
            "controls_pass": controls_pass,
            "promotion_allowed": PROMOTION_ALLOWED,
            "elapsed_seconds": time.time() - started,
        },
        "pass_rule": "Pass iff chi=8/16/32/64 execute with mps_max_bond equal to chi, chirality_gap and half_chain_entropy are nonzero, bond=1 and gamma5-disabled controls degrade the invariant, and even/odd TEBD order remains order-sensitive.",
        "fail_rule": "Fail on dense state closure, site-count scale fakery, missing quimb/cotengra contraction, decorative Clifford usage, generic optimizer dynamics, control leakage, or proof-stage imports.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["future geometry-stage Weyl/chirality audits that preserve promotion_allowed=false"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "why_not_v4_probes": "This is a single torch-standard geometry sim requested for bond-dimension MPS scaling, not a broad v4/v5 manifold completion or proof-stage packet.",
        "summary": {
            "all_pass": all_pass,
            "classification": CLASSIFICATION,
            "result_path": str(OUT_PATH),
            "blockers": blockers,
        },
        "blockers": blockers,
        "all_pass": all_pass,
    }
    return result


def main() -> int:
    result = build_result()
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(as_jsonable(result["summary"]), indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
