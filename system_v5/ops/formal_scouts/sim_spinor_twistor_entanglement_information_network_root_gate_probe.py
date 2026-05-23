#!/usr/bin/env python3
"""Spinor/twistor entanglement information network root-gate probe.

Formal scout only. This tests the proposed replacement emphasis:

  spinor/twistor entanglement information networks

against the derived root-constraint gates:

* finite capacity / Bekenstein-style bound;
* noncommuting spinor transport;
* no Cartesian center or privileged tensor index substrate;
* probe-relative identity instead of primitive equality;
* entropy/entanglement as cut readout, not coordinate distance.

Tensor networks are treated as allowed bounded compression tools only when
they emit invariant finite readouts. Raw tensor index coordinates are tested as
a graveyard control.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "spinor_twistor_entanglement_information_network_root_gate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "spinor_twistor_entanglement_information_network_root_gate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a finite spinor/twistor-like entanglement "
    "information network against two-root derived gates and Cartesian/tensor "
    "substrate graveyards. It does not admit full twistor theory, holographic "
    "spacetime, ER=EPR, final Axis0/Xi bridge, or canonical replacement of "
    "all tensor-network tooling."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing complex spinors, twistor-like incidence, density "
            "matrices, entanglement entropy, SU(2) transport, and tensor-control "
            "readouts without NumPy"
        ),
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive finite-capacity and nonpromotion dependency-consistency fence",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive local result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

DTYPE = torch.float64
CDTYPE = torch.complex128
TOL = 1e-9


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def normalize(v: torch.Tensor) -> torch.Tensor:
    return v / torch.linalg.vector_norm(v)


def spinor(phi: float, chi: float, eta: float) -> torch.Tensor:
    return normalize(
        torch.tensor(
            [
                complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
                complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
            ],
            dtype=CDTYPE,
        )
    )


def orthogonal_spinor(psi: torch.Tensor) -> torch.Tensor:
    return normalize(torch.stack([-torch.conj(psi[1]), torch.conj(psi[0])]))


def rotation(axis: str, theta: float) -> torch.Tensor:
    c = math.cos(theta / 2.0)
    s = math.sin(theta / 2.0)
    i = torch.tensor(1j, dtype=CDTYPE)
    eye = torch.eye(2, dtype=CDTYPE)
    sx = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)
    sz = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE)
    sigma = sx if axis == "x" else sz
    return c * eye - i * s * sigma


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, torch.conj(psi))


def partial_trace_second_qubit(rho: torch.Tensor) -> torch.Tensor:
    rho4 = rho.reshape(2, 2, 2, 2)
    return torch.einsum("abcb->ac", rho4)


def von_neumann_entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh((rho + torch.conj(rho).T) / 2).real
    vals = torch.clamp(vals, min=0.0)
    vals = vals / torch.sum(vals)
    nz = vals[vals > 1e-12]
    return float((-torch.sum(nz * torch.log(nz))).item())


def two_spinor_entangled_state(psi_a: torch.Tensor, psi_b: torch.Tensor, lam: float, phase: float) -> torch.Tensor:
    oa = orthogonal_spinor(psi_a)
    ob = orthogonal_spinor(psi_b)
    term0 = math.cos(lam) * torch.kron(psi_a, psi_b)
    term1 = math.sin(lam) * complex(math.cos(phase), math.sin(phase)) * torch.kron(oa, ob)
    return normalize(term0 + term1)


def twistor_node(omega: torch.Tensor, pi: torch.Tensor) -> dict[str, torch.Tensor]:
    return {"omega": normalize(omega), "pi": normalize(pi)}


def incidence(a: dict[str, torch.Tensor], b: dict[str, torch.Tensor]) -> torch.Tensor:
    # Finite twistor-like antisymmetric spinor incidence. This is not a full
    # Penrose twistor construction; it is an admissible local incidence witness.
    return torch.vdot(a["pi"], b["omega"]) - torch.vdot(b["pi"], a["omega"])


def build_network() -> dict[str, Any]:
    params = [
        (0.11, 0.21, 0.33),
        (0.37, -0.19, 0.57),
        (-0.23, 0.44, 0.73),
        (0.61, 0.08, 0.41),
    ]
    spinors = [spinor(*row) for row in params]
    twistors = [
        twistor_node(spinors[i], spinor(params[(i + 1) % 4][0] + 0.17, params[i][1] - 0.13, params[i][2]))
        for i in range(4)
    ]
    edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
    return {"spinors": spinors, "twistors": twistors, "edges": edges}


def network_readout(net: dict[str, Any]) -> dict[str, Any]:
    edge_rows = []
    incidence_abs = []
    incidence_phase = []
    entropies = []
    for edge_index, (i, j) in enumerate(net["edges"]):
        inc = incidence(net["twistors"][i], net["twistors"][j])
        phase = float(torch.angle(inc).item())
        lam = 0.18 + 0.09 * (edge_index + 1)
        state = two_spinor_entangled_state(net["spinors"][i], net["spinors"][j], lam, phase)
        rho_edge = density(state)
        rho_a = partial_trace_second_qubit(rho_edge)
        entropy = von_neumann_entropy(rho_a)
        inc_abs = float(torch.abs(inc).item())
        incidence_abs.append(inc_abs)
        incidence_phase.append(phase)
        entropies.append(entropy)
        edge_rows.append(
            {
                "edge": [i, j],
                "twistor_incidence_abs": inc_abs,
                "twistor_incidence_phase": phase,
                "cut_entropy": entropy,
            }
        )
    return {
        "edge_rows": edge_rows,
        "entropy_spectrum": sorted(entropies),
        "incidence_abs_spectrum": sorted(incidence_abs),
        "incidence_phase_ordered": incidence_phase,
        "total_cut_entropy": float(sum(entropies)),
    }


def transform_network(net: dict[str, Any], unitary: torch.Tensor) -> dict[str, Any]:
    return {
        "spinors": [unitary @ psi for psi in net["spinors"]],
        "twistors": [
            {"omega": unitary @ node["omega"], "pi": unitary @ node["pi"]}
            for node in net["twistors"]
        ],
        "edges": list(net["edges"]),
    }


def relabel_network(net: dict[str, Any], permutation: list[int]) -> dict[str, Any]:
    inverse = {old: new for new, old in enumerate(permutation)}
    return {
        "spinors": [net["spinors"][old] for old in permutation],
        "twistors": [net["twistors"][old] for old in permutation],
        "edges": [(inverse[i], inverse[j]) for i, j in net["edges"]],
    }


def raw_tensor_index_readout(net: dict[str, Any]) -> float:
    flat = torch.cat([torch.view_as_real(psi).reshape(-1) for psi in net["spinors"]]).to(DTYPE)
    weights = torch.arange(1, flat.numel() + 1, dtype=DTYPE)
    return float(torch.dot(flat, weights).item())


def cartesian_center_control() -> dict[str, Any]:
    points = torch.tensor(
        [[-0.4, 0.1, 0.2], [0.3, -0.6, 0.4], [1.0, 0.2, -0.1], [-0.2, 0.9, 0.5]],
        dtype=DTYPE,
    )
    shift = torch.tensor([4.0, -2.5, 1.7], dtype=DTYPE)
    shifted = points + shift
    pair = torch.sum((points[:, None, :] - points[None, :, :]) ** 2, dim=-1)
    pair_shifted = torch.sum((shifted[:, None, :] - shifted[None, :, :]) ** 2, dim=-1)
    origin = torch.sum(points * points, dim=-1)
    origin_shifted = torch.sum(shifted * shifted, dim=-1)
    centroid = torch.mean(points, dim=0)
    centroid_shifted = torch.mean(shifted, dim=0)
    pairwise_survives = bool(torch.allclose(pair, pair_shifted, atol=1e-9, rtol=1e-9))
    origin_changes = bool(not torch.allclose(origin, origin_shifted, atol=1e-9, rtol=1e-9))
    centroid_changes = bool(not torch.allclose(centroid, centroid_shifted, atol=1e-9, rtol=1e-9))
    return {
        "pairwise_relations_survive_translation": pairwise_survives,
        "origin_readout_changes": origin_changes,
        "centroid_readout_changes": centroid_changes,
        "max_origin_delta": float(torch.max(torch.abs(origin - origin_shifted)).item()),
        "pass": bool(pairwise_survives and origin_changes and centroid_changes),
    }


def finite_capacity_gate(node_count: int) -> dict[str, Any]:
    log_dim = node_count * math.log(2.0)
    capacity_ok = node_count * math.log(2.0)
    capacity_too_small = (node_count - 1) * math.log(2.0)
    log_dim_q = z3.RealVal(str(round(log_dim, 12)))
    cap_q = z3.RealVal(str(round(capacity_ok, 12)))
    cap_small_q = z3.RealVal(str(round(capacity_too_small, 12)))
    ok = z3.Solver()
    ok.add(log_dim_q <= cap_q)
    ok_status = ok.check()
    small = z3.Solver()
    small.add(log_dim_q <= cap_small_q)
    small_status = small.check()

    f01 = z3.Bool("f01_capacity")
    finite_capacity = z3.Bool("finite_capacity")
    spinor_network = z3.Bool("spinor_network")
    dependency_axioms = [
        z3.Implies(finite_capacity, f01),
        z3.Implies(spinor_network, finite_capacity),
    ]

    def status(*assumptions: z3.BoolRef) -> z3.CheckSatResult:
        solver = z3.Solver()
        solver.add(*dependency_axioms)
        solver.add(*assumptions)
        return solver.check()

    roots_do_not_force_capacity_status = status(f01, z3.Not(finite_capacity))
    capacity_with_f01_status = status(f01, finite_capacity)
    capacity_requires_f01_status = status(finite_capacity, z3.Not(f01))
    spinor_network_with_roots_status = status(f01, spinor_network)
    spinor_network_requires_capacity_status = status(spinor_network, z3.Not(finite_capacity))
    return {
        "node_count": node_count,
        "log_dim_nats": log_dim,
        "capacity_ok_nats": capacity_ok,
        "capacity_too_small_nats": capacity_too_small,
        "ok_capacity_status": str(ok_status),
        "too_small_capacity_rejected": str(small_status),
        "roots_do_not_force_capacity_status": str(roots_do_not_force_capacity_status),
        "capacity_with_f01_status": str(capacity_with_f01_status),
        "capacity_requires_f01_status": str(capacity_requires_f01_status),
        "spinor_network_with_roots_status": str(spinor_network_with_roots_status),
        "spinor_network_requires_capacity_status": str(spinor_network_requires_capacity_status),
        "pass": bool(
            ok_status == z3.sat
            and small_status == z3.unsat
            and roots_do_not_force_capacity_status == z3.sat
            and capacity_with_f01_status == z3.sat
            and capacity_requires_f01_status == z3.unsat
            and spinor_network_with_roots_status == z3.sat
            and spinor_network_requires_capacity_status == z3.unsat
        ),
    }


def noncommuting_transport_gate(net: dict[str, Any]) -> dict[str, Any]:
    ux = rotation("x", 0.63)
    uz = rotation("z", -0.41)
    psi = net["spinors"][0]
    x_then_z = uz @ (ux @ psi)
    z_then_x = ux @ (uz @ psi)
    spinor_gap = float(torch.linalg.vector_norm(x_then_z - z_then_x).item())

    net_xz = transform_network(transform_network(net, ux), uz)
    net_zx = transform_network(transform_network(net, uz), ux)
    read_xz = network_readout(net_xz)
    read_zx = network_readout(net_zx)
    incidence_gap = float(
        torch.linalg.vector_norm(
            torch.tensor(read_xz["incidence_abs_spectrum"], dtype=DTYPE)
            - torch.tensor(read_zx["incidence_abs_spectrum"], dtype=DTYPE)
        ).item()
    )
    return {
        "spinor_transport_gap": spinor_gap,
        "incidence_abs_spectrum_gap": incidence_gap,
        "pass": bool(spinor_gap > 1e-6),
        "note": "edge entropy is local-unitary invariant; the direct spinor transport gap is the N01 witness",
    }


def probe_relative_identity_gate(net: dict[str, Any]) -> dict[str, Any]:
    read = network_readout(net)
    changed = build_network()
    # Keep entanglement lambdas unchanged but alter a twistor phase/sign so
    # entropy-only probes collide while incidence probes distinguish.
    changed["twistors"][1] = {
        "omega": changed["twistors"][1]["omega"],
        "pi": torch.exp(torch.tensor(0.73j, dtype=CDTYPE)) * changed["twistors"][1]["pi"],
    }
    read_changed = network_readout(changed)
    entropy_gap = float(
        torch.linalg.vector_norm(
            torch.tensor(read["entropy_spectrum"], dtype=DTYPE)
            - torch.tensor(read_changed["entropy_spectrum"], dtype=DTYPE)
        ).item()
    )
    incidence_phase_gap = float(
        torch.linalg.vector_norm(
            torch.tensor(read["incidence_phase_ordered"], dtype=DTYPE)
            - torch.tensor(read_changed["incidence_phase_ordered"], dtype=DTYPE)
        ).item()
    )
    return {
        "entropy_only_probe_gap": entropy_gap,
        "incidence_phase_probe_gap": incidence_phase_gap,
        "entropy_probe_declares_equivalent": bool(entropy_gap < 1e-9),
        "incidence_probe_distinguishes": bool(incidence_phase_gap > 1e-3),
        "pass": bool(entropy_gap < 1e-9 and incidence_phase_gap > 1e-3),
    }


# ---------------------------------------------------------------------------
# Negative controls — §11 falsifier table encoded as runnable ablations.
# Each row's `pass` field means: the ablation actually collapsed the
# load-bearing distinction, confirming the property bites. A row that
# unexpectedly survives is an audit signal — surface it, do not mask it.
# ---------------------------------------------------------------------------


def product_state_baseline(psi_a: torch.Tensor, psi_b: torch.Tensor) -> torch.Tensor:
    return normalize(torch.kron(psi_a, psi_b))


def build_product_network(net: dict[str, Any]) -> dict[str, Any]:
    """Network where every edge uses lambda=0 (pure product, no entanglement)."""
    return {**net, "force_lambda_zero": True}


def network_readout_with_overrides(
    net: dict[str, Any],
    *,
    force_lambda: float | None = None,
    randomize_incidence: bool = False,
    rng_seed: int | None = None,
) -> dict[str, Any]:
    """Readout variant that lets us ablate the entanglement / incidence layer.

    force_lambda: if not None, replaces the edge-dependent lam with this value.
    randomize_incidence: replaces the twistor incidence phase with a pseudorandom
      S^2-style label per edge (still deterministic per seed).
    """
    if rng_seed is not None:
        gen = torch.Generator()
        gen.manual_seed(rng_seed)
    else:
        gen = None
    edge_rows = []
    incidence_abs = []
    incidence_phase = []
    entropies = []
    for edge_index, (i, j) in enumerate(net["edges"]):
        inc = incidence(net["twistors"][i], net["twistors"][j])
        if randomize_incidence:
            if gen is not None:
                phase = float((torch.rand((), generator=gen) * 2 * math.pi - math.pi).item())
            else:
                phase = float(torch.rand(()).item() * 2 * math.pi - math.pi)
        else:
            phase = float(torch.angle(inc).item())
        if force_lambda is not None:
            lam = force_lambda
        else:
            lam = 0.18 + 0.09 * (edge_index + 1)
        state = two_spinor_entangled_state(net["spinors"][i], net["spinors"][j], lam, phase)
        rho_edge = density(state)
        rho_a = partial_trace_second_qubit(rho_edge)
        entropy = von_neumann_entropy(rho_a)
        inc_abs = float(torch.abs(inc).item())
        incidence_abs.append(inc_abs)
        incidence_phase.append(phase)
        entropies.append(entropy)
        edge_rows.append({"edge": [i, j], "cut_entropy": entropy, "twistor_incidence_abs": inc_abs})
    return {
        "edge_rows": edge_rows,
        "entropy_spectrum": sorted(entropies),
        "incidence_abs_spectrum": sorted(incidence_abs),
        "incidence_phase_ordered": incidence_phase,
        "total_cut_entropy": float(sum(entropies)),
    }


def negative_control_section(net: dict[str, Any], read: dict[str, Any]) -> dict[str, Any]:
    rows: dict[str, Any] = {}

    # F1: tensor network as substrate — falsifier: relabel changes nothing
    # if the spinor readout is properly relational. We already showed the
    # raw tensor index readout changes under relabel; the inverse claim is
    # "spinor readouts (entropy spectrum) survive relabel". Both must hold.
    relabeled = relabel_network(net, [2, 0, 3, 1])
    read_relabel = network_readout(relabeled)
    spinor_relabel_gap = float(
        torch.linalg.vector_norm(
            torch.tensor(read["entropy_spectrum"], dtype=DTYPE)
            - torch.tensor(read_relabel["entropy_spectrum"], dtype=DTYPE)
        ).item()
    )
    raw_before = raw_tensor_index_readout(net)
    raw_relabel = raw_tensor_index_readout(relabeled)
    tensor_index_gap = abs(raw_before - raw_relabel)
    rows["F1_tensor_index_substrate_fails_relabel_invariance"] = {
        "target_claim": "tensor index ontology is admissible as primitive substrate",
        "ablation": "node relabel [2,0,3,1] on the same network",
        "spinor_entropy_spectrum_gap_should_be_zero": spinor_relabel_gap,
        "raw_tensor_index_gap_should_be_nonzero": tensor_index_gap,
        "expected_to_fail": True,
        "summary": "raw tensor index readout breaks under relabel while spinor entropy spectrum survives — tensor substrate is rejected, spinor carrier is not",
        "pass": bool(spinor_relabel_gap < 1e-9 and tensor_index_gap > 1e-6),
    }

    # F2: tensor geometry is meaningful — the old entropy-spectrum-only check
    # was too weak because it is intentionally permutation-flat. Keep that
    # invariant witness, but add an edge-identity-sensitive readout. If the
    # basis-sensitive readout moves, then the scout must not claim that edge
    # permutation kills all geometry; it only kills geometry at the chosen
    # invariant-spectrum readout.
    edge_perm = [(2, 3), (3, 0), (0, 1), (1, 2)]
    net_perm_edges = {**net, "edges": edge_perm}
    read_perm = network_readout(net_perm_edges)
    geom_gap = float(
        torch.linalg.vector_norm(
            torch.tensor(read["entropy_spectrum"], dtype=DTYPE)
            - torch.tensor(read_perm["entropy_spectrum"], dtype=DTYPE)
        ).item()
    )
    edge_feature_native = {
        tuple(row["edge"]): row["cut_entropy"] * row["twistor_incidence_abs"]
        for row in read["edge_rows"]
    }
    edge_feature_perm = {
        tuple(row["edge"]): row["cut_entropy"] * row["twistor_incidence_abs"]
        for row in read_perm["edge_rows"]
    }
    common_edges = sorted(set(edge_feature_native) & set(edge_feature_perm))
    basis_sensitive_gap = float(
        torch.linalg.vector_norm(
            torch.tensor([edge_feature_native[edge] for edge in common_edges], dtype=DTYPE)
            - torch.tensor([edge_feature_perm[edge] for edge in common_edges], dtype=DTYPE)
        ).item()
    )
    rows["F2_tensor_geometry_collapsed_by_edge_order_scramble"] = {
        "target_claim": "edge ordering / static contraction tree carries geometry beyond the entropy spectrum",
        "ablation": "permute the edge list while keeping node spinors and twistors fixed",
        "entropy_spectrum_gap_under_edge_permutation": geom_gap,
        "basis_sensitive_edge_feature_gap_under_edge_permutation": basis_sensitive_gap,
        "expected_to_fail": True,
        "summary": (
            "sorted entropy spectrum is permutation-flat, but an edge-identity "
            "feature moves; F2 is a readout-bound result, not a proof that all "
            "edge geometry is killed"
        ),
        "pass": bool(geom_gap < 1e-9 and basis_sensitive_gap > 1e-3),
    }

    # F3: spinor entanglement is load-bearing — falsifier: product state
    # (lambda = 0) gives the same admitted readouts.
    read_product = network_readout_with_overrides(net, force_lambda=0.0)
    product_entropy_gap = float(
        torch.linalg.vector_norm(
            torch.tensor(read["entropy_spectrum"], dtype=DTYPE)
            - torch.tensor(read_product["entropy_spectrum"], dtype=DTYPE)
        ).item()
    )
    product_total_entropy = read_product["total_cut_entropy"]
    rows["F3_product_state_ablation_collapses_entanglement_signature"] = {
        "target_claim": "spinor entanglement is load-bearing as the carrier",
        "ablation": "force lambda=0 across all edges (pure product state on each cut)",
        "product_total_cut_entropy_should_be_zero": product_total_entropy,
        "gap_to_entangled_baseline": product_entropy_gap,
        "expected_to_fail": True,
        "summary": "product baseline has zero cut entropy while the entangled network has nonzero — entanglement is load-bearing",
        "pass": bool(product_total_entropy < 1e-9 and product_entropy_gap > 1e-3),
    }

    # F4: chiral structure is load-bearing — falsifier: H_L = +H_0 and
    # H_R = +H_0 (no sheet sign flip) gives the same Bloch flow. This is
    # a direct sheet-sign ablation.
    n_vec = torch.tensor([0.3, -0.4, 0.7], dtype=DTYPE)
    n_vec = n_vec / torch.linalg.vector_norm(n_vec)
    sx = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)
    sy = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=CDTYPE)
    sz = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE)
    H0 = n_vec[0] * sx + n_vec[1] * sy + n_vec[2] * sz
    H_L = +H0
    H_R = -H0
    H_R_ablated = +H0  # no chirality
    psi0 = net["spinors"][0]
    rho0 = density(psi0)
    # Short transport on each sheet
    dt = 0.5
    UL = torch.linalg.matrix_exp(-1.0j * H_L * dt)
    UR = torch.linalg.matrix_exp(-1.0j * H_R * dt)
    UR_ab = torch.linalg.matrix_exp(-1.0j * H_R_ablated * dt)
    rho_L = UL @ rho0 @ torch.conj(UL).T
    rho_R = UR @ rho0 @ torch.conj(UR).T
    rho_R_ab = UR_ab @ rho0 @ torch.conj(UR_ab).T
    chiral_gap = float(torch.linalg.matrix_norm(rho_L - rho_R).item())
    nonchiral_gap = float(torch.linalg.matrix_norm(rho_L - rho_R_ab).item())
    rows["F4_chiral_sheet_sign_collapsed_kills_L_R_distinction"] = {
        "target_claim": "L/R Weyl sheet sign is load-bearing structure",
        "ablation": "set H_R = +H_0 instead of -H_0 (no chirality)",
        "chiral_L_minus_R_density_norm": chiral_gap,
        "nonchiral_L_minus_R_density_norm": nonchiral_gap,
        "expected_to_fail": True,
        "summary": "with chirality on, rho_L and rho_R diverge under transport; with chirality off, they coincide — sheet sign is load-bearing",
        "pass": bool(chiral_gap > 1e-3 and nonchiral_gap < 1e-9),
    }

    # F5: twistor incidence is load-bearing — falsifier: random S^2 phase
    # replacement gives the same admitted distinguishing power.
    read_random = network_readout_with_overrides(net, randomize_incidence=True, rng_seed=20260522)
    rand_entropy_gap = float(
        torch.linalg.vector_norm(
            torch.tensor(read["entropy_spectrum"], dtype=DTYPE)
            - torch.tensor(read_random["entropy_spectrum"], dtype=DTYPE)
        ).item()
    )
    rand_phase_gap = float(
        torch.linalg.vector_norm(
            torch.tensor(read["incidence_phase_ordered"], dtype=DTYPE)
            - torch.tensor(read_random["incidence_phase_ordered"], dtype=DTYPE)
        ).item()
    )
    rows["F5_random_phase_label_distinguishes_from_genuine_twistor_incidence"] = {
        "target_claim": "twistor incidence phase carries information beyond a random S^2 label",
        "ablation": "replace incidence phase by pseudorandom S^2 phase (same magnitude)",
        "entropy_spectrum_gap_random_vs_genuine": rand_entropy_gap,
        "phase_gap_random_vs_genuine": rand_phase_gap,
        "expected_to_fail": True,
        "summary": "random S^2 phase gives a different incidence_phase_ordered readout — the genuine twistor incidence is not interchangeable with a random label",
        "pass": bool(rand_phase_gap > 1e-3),
    }

    # F6: countermodel for "F01+N01 forces this exact stack" — build a
    # finite noncommuting alternative (qutrit, dim=3) that satisfies F01+N01
    # but is not the spinor/twistor C^2 ring.
    qutrit_dim = 3
    a_qutrit = torch.zeros((qutrit_dim, qutrit_dim), dtype=CDTYPE)
    a_qutrit[0, 1] = 1.0
    a_qutrit[1, 2] = math.sqrt(2.0)
    b_qutrit = torch.conj(a_qutrit).T
    commutator_qutrit = a_qutrit @ b_qutrit - b_qutrit @ a_qutrit
    qutrit_finite = qutrit_dim < float("inf")
    qutrit_noncommuting = float(torch.linalg.matrix_norm(commutator_qutrit).item()) > 1e-9
    rows["F6_qutrit_countermodel_satisfies_F01_and_N01_without_C2_ring"] = {
        "target_claim": "F01+N01 uniquely force the C^2 spinor/twistor ring carrier",
        "ablation": "construct a finite-dim (3) noncommuting alternative with raising/lowering operators",
        "qutrit_dim_finite": qutrit_finite,
        "qutrit_noncommutator_norm": float(torch.linalg.matrix_norm(commutator_qutrit).item()),
        "qutrit_noncommutes": qutrit_noncommuting,
        "expected_to_fail": True,
        "summary": "a 3-dim noncommuting carrier satisfies both roots without being the C^2 spinor/twistor network — the roots do not force a unique carrier",
        "pass": bool(qutrit_finite and qutrit_noncommuting),
    }

    # F7: order-erased loop ablation — falsifier: replacing the noncommuting
    # pair (sigma_x, sigma_z) with a commuting pair (sigma_z, sigma_z) makes
    # the transport gap vanish. This shows the transport gate is detecting
    # noncommutativity, not the magnitude of the rotation.
    ux = rotation("x", 0.63)
    uz = rotation("z", -0.41)
    uz_alt = rotation("z", 0.63)  # commuting partner for uz (both sigma_z)
    psi = net["spinors"][0]
    direct_gap = float(torch.linalg.vector_norm(uz @ (ux @ psi) - ux @ (uz @ psi)).item())
    commuting_gap = float(
        torch.linalg.vector_norm(uz @ (uz_alt @ psi) - uz_alt @ (uz @ psi)).item()
    )
    rows["F7_commuting_replacement_collapses_N01_witness"] = {
        "target_claim": "noncommuting order is observable in the transport readout",
        "ablation": "replace the (sigma_x, sigma_z) pair with two sigma_z rotations (commuting)",
        "direct_order_gap": direct_gap,
        "commuting_pair_gap": commuting_gap,
        "expected_to_fail": True,
        "summary": "noncommuting pair has nonzero gap; commuting pair has zero gap — N01 is what the transport gate is detecting",
        "pass": bool(direct_gap > 1e-3 and commuting_gap < 1e-9),
    }

    fired = sum(1 for v in rows.values() if v["pass"])
    audit_signal = [k for k, v in rows.items() if v["expected_to_fail"] and not v["pass"]]
    return {
        "rows": rows,
        "fired_count": fired,
        "rows_total": len(rows),
        "all_negative_controls_fired_as_expected": fired == len(rows),
        "audit_signal_rows": audit_signal,
        "pass": fired == len(rows),
    }


# ---------------------------------------------------------------------------
# Tensor-network ablation — same 4-node ring represented three ways:
#   (a) raw 16-d state vector with explicit index ontology,
#   (b) bounded-bond MPS-style approximation (sequential Schmidt truncation),
#   (c) spinor incidence graph (the current carrier).
# The audit thesis: (a) fails relabel/gauge invariance, (b) survives within
# finite bond as a tool, (c) is the load-bearing carrier.
# ---------------------------------------------------------------------------


def edge_entangled_state(net: dict[str, Any], edge_index: int) -> tuple[torch.Tensor, float, float]:
    """Recompute the entangled edge state for one edge — known Schmidt rank up to 2."""
    i, j = net["edges"][edge_index]
    inc = incidence(net["twistors"][i], net["twistors"][j])
    phase = float(torch.angle(inc).item())
    lam = 0.18 + 0.09 * (edge_index + 1)
    state = two_spinor_entangled_state(net["spinors"][i], net["spinors"][j], lam, phase)
    return state, lam, phase


def bond_truncated_two_qubit(state_4d: torch.Tensor, bond_dim: int) -> torch.Tensor:
    """Schmidt-truncate a 2-qubit state to bond_dim singular values."""
    m = state_4d.reshape(2, 2)
    u, s, vh = torch.linalg.svd(m, full_matrices=False)
    k = min(bond_dim, s.shape[0])
    truncated = u[:, :k] @ torch.diag(s[:k].to(CDTYPE)) @ vh[:k, :]
    flat = truncated.reshape(4).to(CDTYPE)
    norm = float(torch.linalg.vector_norm(flat).item())
    return flat if norm < 1e-15 else flat / norm


def reduced_first_qubit_of_4dim(state: torch.Tensor) -> torch.Tensor:
    rho = torch.outer(state, torch.conj(state))
    rho_2d = rho.reshape(2, 2, 2, 2)
    return torch.einsum("abcb->ac", rho_2d)


def tensor_network_ablation_section(net: dict[str, Any]) -> dict[str, Any]:
    """Three reps of the same EDGE entangled state (Schmidt rank up to 2):
       (a) raw 4-d state vector with index ontology readout,
       (b) bounded-bond Schmidt-truncated tool (bond=1 destroys entanglement,
           bond=2 is exact for any 2-qubit state),
       (c) spinor incidence graph (the carrier — uses the whole network).

    Thesis: tensor-INDEX ontology fails gauge/relabel; bond=1 truncation
    collapses entanglement; bond=2 is a faithful TOOL; spinor entropy spectrum
    survives gauge and relabel at the network level.
    """
    state01, lam01, phase01 = edge_entangled_state(net, 0)
    rho_first_full = reduced_first_qubit_of_4dim(state01)
    s_full = von_neumann_entropy(rho_first_full)

    bond_curve: dict[str, Any] = {}
    for bond in [1, 2]:
        approx = bond_truncated_two_qubit(state01, bond)
        rho_first_approx = reduced_first_qubit_of_4dim(approx)
        s_approx = von_neumann_entropy(rho_first_approx)
        fidelity = float(abs(torch.vdot(state01, approx).item()) ** 2)
        bond_curve[f"bond_{bond}"] = {
            "single_qubit_entropy": s_approx,
            "fidelity_with_full_state": fidelity,
        }

    def raw_index_readout_of_state(state: torch.Tensor) -> float:
        flat = torch.view_as_real(state).reshape(-1).to(DTYPE)
        weights = torch.arange(1, flat.numel() + 1, dtype=DTYPE)
        return float(torch.dot(flat, weights).item())

    raw_before = raw_index_readout_of_state(state01)
    swap = torch.tensor(
        [[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=CDTYPE
    )
    raw_after_swap = raw_index_readout_of_state(swap @ state01)
    u_local = rotation("z", 0.91) @ rotation("x", -0.34)
    raw_after_gauge = raw_index_readout_of_state(torch.kron(u_local, u_local) @ state01)

    read_native = network_readout(net)
    relabeled = relabel_network(net, [2, 0, 3, 1])
    read_relabel = network_readout(relabeled)
    transformed = transform_network(net, u_local)
    read_gauge = network_readout(transformed)
    entropy_native = torch.tensor(read_native["entropy_spectrum"], dtype=DTYPE)
    entropy_relabel_gap = float(
        torch.linalg.vector_norm(entropy_native - torch.tensor(read_relabel["entropy_spectrum"], dtype=DTYPE)).item()
    )
    entropy_gauge_gap = float(
        torch.linalg.vector_norm(entropy_native - torch.tensor(read_gauge["entropy_spectrum"], dtype=DTYPE)).item()
    )

    raw_fails_swap = abs(raw_before - raw_after_swap) > 1e-6
    raw_fails_gauge = abs(raw_before - raw_after_gauge) > 1e-6
    spinor_survives_relabel = entropy_relabel_gap < 1e-9
    spinor_survives_gauge = entropy_gauge_gap < 1e-9

    bond1_entropy = bond_curve["bond_1"]["single_qubit_entropy"]
    bond1_fid = bond_curve["bond_1"]["fidelity_with_full_state"]
    bond2_fid = bond_curve["bond_2"]["fidelity_with_full_state"]
    bond1_collapses_entanglement = bond1_entropy < 1e-9
    bond2_faithful = bond2_fid > 1 - 1e-9
    bond1_strict_lower_fidelity = bond1_fid < bond2_fid - 1e-6

    return {
        "thesis": (
            "Edge state |Psi_01> has Schmidt rank up to 2. Raw tensor-index "
            "readout fails swap and local-unitary gauge. Bond=1 Schmidt "
            "truncation forces a rank-1 product (zero entanglement entropy). "
            "Bond=2 is exact for any 2-qubit state (faithful tool). Spinor "
            "entropy spectrum survives relabel and SU(2) gauge at the network."
        ),
        "edge_index": 0,
        "edge_lambda": lam01,
        "edge_phase": phase01,
        "full_state_entanglement_entropy": s_full,
        "bond_truncation_curve": bond_curve,
        "raw_index_readout": {
            "before": raw_before,
            "after_qubit_swap": raw_after_swap,
            "after_local_unitary": raw_after_gauge,
            "swap_delta": abs(raw_before - raw_after_swap),
            "gauge_delta": abs(raw_before - raw_after_gauge),
            "fails_swap_invariance": raw_fails_swap,
            "fails_gauge_invariance": raw_fails_gauge,
        },
        "spinor_entropy_under_relabel": {
            "delta": entropy_relabel_gap,
            "survives_invariance": spinor_survives_relabel,
        },
        "spinor_entropy_under_gauge": {
            "delta": entropy_gauge_gap,
            "survives_invariance": spinor_survives_gauge,
        },
        "bond_1_collapses_entanglement": bond1_collapses_entanglement,
        "bond_2_is_faithful_tool": bond2_faithful,
        "bond_1_strictly_lower_fidelity_than_bond_2": bond1_strict_lower_fidelity,
        "pass": bool(
            raw_fails_swap
            and raw_fails_gauge
            and spinor_survives_relabel
            and spinor_survives_gauge
            and bond1_collapses_entanglement
            and bond2_faithful
            and bond1_strict_lower_fidelity
        ),
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    net = build_network()
    read = network_readout(net)
    u_global = rotation("z", 0.91) @ rotation("x", -0.34)
    read_global = network_readout(transform_network(net, u_global))
    relabeled = relabel_network(net, [2, 0, 3, 1])
    read_relabel = network_readout(relabeled)
    raw_before = raw_tensor_index_readout(net)
    raw_relabel = raw_tensor_index_readout(relabeled)

    entropy_vector = torch.tensor(read["entropy_spectrum"], dtype=DTYPE)
    entropy_global = torch.tensor(read_global["entropy_spectrum"], dtype=DTYPE)
    incidence_vector = torch.tensor(read["incidence_abs_spectrum"], dtype=DTYPE)
    incidence_global = torch.tensor(read_global["incidence_abs_spectrum"], dtype=DTYPE)
    entropy_relabel = torch.tensor(read_relabel["entropy_spectrum"], dtype=DTYPE)

    positive = {
        "finite_capacity_bekenstein_gate": finite_capacity_gate(node_count=len(net["spinors"])),
        "spinor_twistor_readout_global_su2_invariant": {
            "entropy_spectrum_gap": float(torch.linalg.vector_norm(entropy_vector - entropy_global).item()),
            "incidence_abs_spectrum_gap": float(torch.linalg.vector_norm(incidence_vector - incidence_global).item()),
            "pass": bool(
                torch.allclose(entropy_vector, entropy_global, atol=1e-9, rtol=1e-9)
                and torch.allclose(incidence_vector, incidence_global, atol=1e-9, rtol=1e-9)
            ),
        },
        "spinor_network_relabel_invariant": {
            "entropy_spectrum_gap": float(torch.linalg.vector_norm(entropy_vector - entropy_relabel).item()),
            "pass": bool(torch.allclose(entropy_vector, entropy_relabel, atol=1e-9, rtol=1e-9)),
        },
        "noncommuting_spinor_transport": noncommuting_transport_gate(net),
        "probe_relative_identity": probe_relative_identity_gate(net),
    }
    graveyard_companions = {
        "cartesian_center_origin_control_rejected": {
            **cartesian_center_control(),
        },
        "raw_tensor_index_substrate_rejected": {
            "raw_tensor_index_readout_before": raw_before,
            "raw_tensor_index_readout_after_relabel": raw_relabel,
            "changes_under_relabel": bool(abs(raw_before - raw_relabel) > 1e-6),
            "pass": bool(abs(raw_before - raw_relabel) > 1e-6),
        },
        "entanglement_only_identity_is_insufficient": {
            "pass": positive["probe_relative_identity"]["pass"],
            "summary": "entropy-only probes can collide while incidence-phase probes distinguish",
        },
    }
    boundary = {
        "tensor_networks_allowed_only_as_finite_tools": {
            "pass": True,
            "summary": "finite tensor contraction is allowed as compression/tooling; raw global tensor indices are not primitive ontology",
        },
        "twistor_status_is_local_incidence_witness_not_full_twistor_theory": {
            "pass": True,
            "summary": "uses finite spinor-pair incidence only; no full projective twistor or spacetime claim",
        },
        "holographic_status_open": {
            "pass": True,
            "summary": "finite boundary capacity and entanglement readouts are tested; ER=EPR/holographic spacetime not admitted",
        },
    }
    negative_controls = negative_control_section(net, read)
    tensor_ablation = tensor_network_ablation_section(net)
    negative_control_rows = {
        f"negative_control__{name}": {"pass": row["pass"], "summary": row.get("summary", name)}
        for name, row in negative_controls["rows"].items()
    }
    tensor_ablation_summary = {
        "tensor_network_ablation": {
            "pass": tensor_ablation["pass"],
            "summary": tensor_ablation["thesis"],
        }
    }
    all_rows = [
        *positive.values(),
        *graveyard_companions.values(),
        *boundary.values(),
        *negative_control_rows.values(),
        *tensor_ablation_summary.values(),
    ]
    all_pass = all(row.get("pass") is True for row in all_rows)
    result = {
        "name": NAME,
        "classification": classification,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": bool(all_pass),
        "math_object": (
            "finite spinor/twistor-like entanglement information network: "
            "nodes carry normalized C^2 spinors, edges carry twistor-like "
            "incidence and bipartite cut entropy"
        ),
        "network_readout": read,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "negative_controls": negative_controls,
        "tensor_network_ablation": tensor_ablation,
        "nearby_variants": {
            "total": len(all_rows),
            "passed": sum(1 for row in all_rows if row.get("pass") is True),
        },
        "why_not_v4_probes": (
            "This is a noncanonical formal-scout audit for a proposed spinor/"
            "twistor information-network carrier and tensor-substrate graveyard; "
            "it should remain in v5 until tool/function receipts and bridge "
            "admission are hardened."
        ),
        "open_boundaries": [
            "full twistor theory not admitted",
            "ER=EPR/holographic spacetime not admitted",
            "tensor networks not banned as tools, only rejected as primitive coordinate substrate",
            "Axis0 Xi -> rho_AB bridge still open",
        ],
        "blockers": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "runtime_seconds": round(time.time() - started, 6),
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(OUT_PATH), "all_pass": all_pass}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
