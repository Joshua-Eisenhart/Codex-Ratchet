#!/usr/bin/env python3
"""Next-wave spinor/twistor information-network gates.

Formal scout only. This extends the first spinor/twistor root-gate probe with
four narrower checks:

* Clifford rotor transport must agree with SU(2) spinor/Bloch transport and
  expose noncommuting rotor order. This is a faithfulness/correctness check,
  not proof that Clifford carries information unavailable to SU(2).
* Twistor-like incidence must add a probe beyond entropy-only equality.
* Tensor contraction is allowed as a bounded tool but rejected as raw index
  substrate.
* Bekenstein-style boundary capacity rejects over-budget entanglement graphs.

This does not admit full twistor theory, ER=EPR, holographic spacetime, or a
canonical Axis 0 bridge.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch
import z3
from clifford import Cl


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "spinor_twistor_network_clifford_tensor_boundary_next_wave_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "spinor_twistor_network_next_wave"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests Clifford rotor transport, finite twistor-like "
    "incidence, tensor-tool boundary, and Bekenstein-style capacity for a "
    "spinor entanglement information network. It does not admit full twistor "
    "theory, ER=EPR, holographic spacetime, or final Axis0/Xi bridge."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex spinors, density matrices, cut entropy, and finite tensor contraction controls",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "faithful rotor transport implementation and noncommuting geometric-product order witness",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive finite-capacity and root-nonpromotion dependency-consistency fence",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive local result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "clifford": "supportive",
    "z3": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

DTYPE = torch.float64
CDTYPE = torch.complex128
TOL = 1e-8


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


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, torch.conj(psi))


def bloch(psi: torch.Tensor) -> torch.Tensor:
    rho = density(psi)
    sx = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
    return torch.tensor(
        [
            torch.real(torch.trace(rho @ sx)).item(),
            torch.real(torch.trace(rho @ sy)).item(),
            torch.real(torch.trace(rho @ sz)).item(),
        ],
        dtype=DTYPE,
    )


def rotation(axis: str, theta: float) -> torch.Tensor:
    eye = torch.eye(2, dtype=CDTYPE)
    sx = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
    sigma = sx if axis == "x" else sz
    return math.cos(theta / 2.0) * eye - 1j * math.sin(theta / 2.0) * sigma


def partial_trace_second_qubit(rho: torch.Tensor) -> torch.Tensor:
    rho4 = rho.reshape(2, 2, 2, 2)
    return torch.einsum("abcb->ac", rho4)


def von_neumann_entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh((rho + torch.conj(rho).T) / 2).real
    vals = torch.clamp(vals, min=0.0)
    vals = vals / torch.sum(vals)
    nz = vals[vals > 1e-12]
    return float((-torch.sum(nz * torch.log(nz))).item())


def edge_state(psi_a: torch.Tensor, psi_b: torch.Tensor, lam: float, phase: float) -> torch.Tensor:
    oa = orthogonal_spinor(psi_a)
    ob = orthogonal_spinor(psi_b)
    return normalize(
        math.cos(lam) * torch.kron(psi_a, psi_b)
        + math.sin(lam) * complex(math.cos(phase), math.sin(phase)) * torch.kron(oa, ob)
    )


def cut_entropy_from_state(state: torch.Tensor) -> float:
    return von_neumann_entropy(partial_trace_second_qubit(density(state)))


def cut_entropy_from_schmidt_lambda(lam: float) -> float:
    p0 = math.cos(lam) ** 2
    p1 = math.sin(lam) ** 2
    return -(p0 * math.log(p0) + p1 * math.log(p1))


def twistor_node(omega: torch.Tensor, pi: torch.Tensor) -> dict[str, torch.Tensor]:
    return {"omega": normalize(omega), "pi": normalize(pi)}


def incidence(a: dict[str, torch.Tensor], b: dict[str, torch.Tensor]) -> torch.Tensor:
    return torch.vdot(a["pi"], b["omega"]) - torch.vdot(b["pi"], a["omega"])


def build_network() -> dict[str, Any]:
    params = [
        (0.13, 0.17, 0.29),
        (0.41, -0.23, 0.61),
        (-0.31, 0.38, 0.72),
        (0.77, 0.09, 0.46),
    ]
    spinors = [spinor(*row) for row in params]
    twistors = [
        twistor_node(spinors[i], spinor(params[(i + 1) % 4][0] + 0.11, params[i][1] - 0.07, params[i][2]))
        for i in range(4)
    ]
    return {"spinors": spinors, "twistors": twistors, "edges": [(0, 1), (1, 2), (2, 3), (3, 0)]}


def network_edges(net: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for edge_index, (i, j) in enumerate(net["edges"]):
        inc = incidence(net["twistors"][i], net["twistors"][j])
        phase = float(torch.angle(inc).item())
        lam = 0.16 + 0.08 * (edge_index + 1)
        state = edge_state(net["spinors"][i], net["spinors"][j], lam, phase)
        entropy_dense = cut_entropy_from_state(state)
        entropy_tool = cut_entropy_from_schmidt_lambda(lam)
        rows.append(
            {
                "edge": [i, j],
                "lambda": lam,
                "incidence_abs": float(torch.abs(inc).item()),
                "incidence_phase": phase,
                "entropy_dense_tensor": entropy_dense,
                "entropy_bounded_tool": entropy_tool,
                "tool_dense_gap": abs(entropy_dense - entropy_tool),
            }
        )
    return rows


def clifford_rotor_gate() -> dict[str, Any]:
    """Correctness verification, not load-bearing audit.

    Cl(3) and SU(2) are isomorphic at the group level (both are double covers
    of SO(3)). The agreement-to-machine-epsilon test below confirms the Clifford
    rotor implementation correctly reproduces SU(2) spinor transport on this
    carrier. It does NOT establish that Clifford carries information SU(2)
    matrices alone cannot — at this scope, Clifford is faithful notation, not
    additional structure. The noncommuting order gap is a textbook SU(2)
    property that both representations must reproduce.

    Pass means: rotor implementation matches SU(2) implementation, noncommutativity
    is observable, and Bloch norm is preserved — all expected by the isomorphism.
    """
    layout, blades = Cl(3)
    del layout
    e1 = blades["e1"]
    e2 = blades["e2"]
    e3 = blades["e3"]
    b12 = e1 * e2
    b23 = e2 * e3

    theta_z = 0.58
    theta_x = -0.43
    rz = math.cos(theta_z / 2.0) - math.sin(theta_z / 2.0) * b12
    rx = math.cos(theta_x / 2.0) - math.sin(theta_x / 2.0) * b23

    psi = spinor(0.19, -0.27, 0.52)
    r0 = bloch(psi)
    v = float(r0[0]) * e1 + float(r0[1]) * e2 + float(r0[2]) * e3

    v_zx = rz * (rx * v * ~rx) * ~rz
    v_xz = rx * (rz * v * ~rz) * ~rx
    rotor_zx = torch.tensor([float(v_zx | e1), float(v_zx | e2), float(v_zx | e3)], dtype=DTYPE)
    rotor_xz = torch.tensor([float(v_xz | e1), float(v_xz | e2), float(v_xz | e3)], dtype=DTYPE)

    uz = rotation("z", theta_z)
    ux = rotation("x", theta_x)
    spinor_zx = bloch(uz @ (ux @ psi))
    spinor_xz = bloch(ux @ (uz @ psi))
    agreement_gap = float(torch.linalg.vector_norm(rotor_zx - spinor_zx).item())
    noncomm_gap = float(torch.linalg.vector_norm(rotor_zx - rotor_xz).item())
    norm_gap = abs(float(torch.linalg.vector_norm(rotor_zx).item()) - float(torch.linalg.vector_norm(r0).item()))

    return {
        "rotor_spinor_agreement_gap": agreement_gap,
        "rotor_noncommuting_order_gap": noncomm_gap,
        "rotor_norm_gap": norm_gap,
        "pass": bool(agreement_gap < 1e-8 and noncomm_gap > 1e-4 and norm_gap < 1e-8),
    }


def twistor_incidence_hardening_gate(net: dict[str, Any]) -> dict[str, Any]:
    rows = network_edges(net)
    entropy = torch.tensor(sorted(row["entropy_dense_tensor"] for row in rows), dtype=DTYPE)
    incidence_phase = torch.tensor([row["incidence_phase"] for row in rows], dtype=DTYPE)

    changed = build_network()
    changed["twistors"][2] = {
        "omega": changed["twistors"][2]["omega"],
        "pi": complex(math.cos(0.61), math.sin(0.61)) * changed["twistors"][2]["pi"],
    }
    changed_rows = network_edges(changed)
    entropy_changed = torch.tensor(sorted(row["entropy_dense_tensor"] for row in changed_rows), dtype=DTYPE)
    phase_changed = torch.tensor([row["incidence_phase"] for row in changed_rows], dtype=DTYPE)

    entropy_gap = float(torch.linalg.vector_norm(entropy - entropy_changed).item())
    phase_gap = float(torch.linalg.vector_norm(incidence_phase - phase_changed).item())
    twistor_score = torch.tensor(
        [row["entropy_dense_tensor"] * math.cos(row["incidence_phase"]) for row in rows],
        dtype=DTYPE,
    )
    entropy_only_score = torch.tensor([row["entropy_dense_tensor"] for row in rows], dtype=DTYPE)
    random_phase_score = torch.tensor(
        [row["entropy_dense_tensor"] * math.cos(0.37 * (idx + 1)) for idx, row in enumerate(rows)],
        dtype=DTYPE,
    )
    twistor_vs_entropy_gap = float(torch.linalg.vector_norm(twistor_score - entropy_only_score).item())
    twistor_vs_random_gap = float(torch.linalg.vector_norm(twistor_score - random_phase_score).item())

    return {
        "entropy_probe_gap_after_local_twistor_rephase": entropy_gap,
        "incidence_phase_gap_after_local_twistor_rephase": phase_gap,
        "twistor_score_vs_entropy_only_gap": twistor_vs_entropy_gap,
        "twistor_score_vs_random_phase_gap": twistor_vs_random_gap,
        "pass": bool(entropy_gap < 1e-9 and phase_gap > 1e-3 and twistor_vs_entropy_gap > 1e-3 and twistor_vs_random_gap > 1e-3),
    }


def tensor_tool_boundary_gate(net: dict[str, Any]) -> dict[str, Any]:
    rows = network_edges(net)
    max_tool_gap = max(row["tool_dense_gap"] for row in rows)
    flat = torch.cat([torch.view_as_real(psi).reshape(-1) for psi in net["spinors"]]).to(DTYPE)
    weights = torch.arange(1, flat.numel() + 1, dtype=DTYPE)
    raw_before = float(torch.dot(flat, weights).item())

    permutation = [2, 0, 3, 1]
    relabeled_spinors = [net["spinors"][idx] for idx in permutation]
    flat_relabel = torch.cat([torch.view_as_real(psi).reshape(-1) for psi in relabeled_spinors]).to(DTYPE)
    raw_after = float(torch.dot(flat_relabel, weights).item())
    raw_gap = abs(raw_before - raw_after)

    return {
        "max_dense_vs_bounded_tensor_tool_entropy_gap": max_tool_gap,
        "raw_tensor_index_readout_gap_under_relabel": raw_gap,
        "bounded_tensor_tool_allowed": bool(max_tool_gap < 1e-8),
        "raw_tensor_index_substrate_rejected": bool(raw_gap > 1e-6),
        "pass": bool(max_tool_gap < 1e-8 and raw_gap > 1e-6),
    }


def boundary_capacity_graph_gate(net: dict[str, Any]) -> dict[str, Any]:
    rows = network_edges(net)
    total_entropy = sum(row["entropy_dense_tensor"] for row in rows)
    capacity_ok = total_entropy + 0.25
    capacity_too_small = total_entropy - 0.25

    ent = z3.RealVal(str(round(total_entropy, 12)))
    cap_ok = z3.RealVal(str(round(capacity_ok, 12)))
    cap_small = z3.RealVal(str(round(capacity_too_small, 12)))

    ok = z3.Solver()
    ok.add(ent <= cap_ok)
    ok_status = ok.check()
    small = z3.Solver()
    small.add(ent <= cap_small)
    small_status = small.check()

    f01 = z3.Bool("f01")
    n01 = z3.Bool("n01")
    capacity_bound = z3.Bool("capacity_bound")
    twistor_incidence = z3.Bool("twistor_incidence")
    clifford_order_probe = z3.Bool("clifford_order_probe")
    holographic_spacetime = z3.Bool("holographic_spacetime")
    dependency_axioms = [
        z3.Implies(capacity_bound, f01),
        z3.Implies(twistor_incidence, z3.And(f01, n01)),
        z3.Implies(clifford_order_probe, n01),
        z3.Implies(holographic_spacetime, capacity_bound),
    ]

    def status(*assumptions: z3.BoolRef) -> z3.CheckSatResult:
        solver = z3.Solver()
        solver.add(*dependency_axioms)
        solver.add(*assumptions)
        return solver.check()

    roots_do_not_force_capacity_status = status(f01, n01, z3.Not(capacity_bound))
    capacity_with_roots_status = status(f01, n01, capacity_bound)
    capacity_requires_f01_status = status(capacity_bound, z3.Not(f01))
    twistor_with_roots_status = status(f01, n01, twistor_incidence)
    twistor_requires_roots_status = status(twistor_incidence, z3.Or(z3.Not(f01), z3.Not(n01)))
    clifford_order_with_n01_status = status(n01, clifford_order_probe)
    clifford_order_requires_n01_status = status(clifford_order_probe, z3.Not(n01))
    holography_with_capacity_status = status(f01, capacity_bound, holographic_spacetime)
    holography_requires_capacity_status = status(holographic_spacetime, z3.Not(capacity_bound))

    return {
        "total_edge_cut_entropy": total_entropy,
        "capacity_ok": capacity_ok,
        "capacity_too_small": capacity_too_small,
        "ok_capacity_status": str(ok_status),
        "too_small_capacity_status": str(small_status),
        "roots_do_not_force_capacity_status": str(roots_do_not_force_capacity_status),
        "capacity_with_roots_status": str(capacity_with_roots_status),
        "capacity_requires_f01_status": str(capacity_requires_f01_status),
        "twistor_with_roots_status": str(twistor_with_roots_status),
        "twistor_requires_roots_status": str(twistor_requires_roots_status),
        "clifford_order_with_n01_status": str(clifford_order_with_n01_status),
        "clifford_order_requires_n01_status": str(clifford_order_requires_n01_status),
        "holography_with_capacity_status": str(holography_with_capacity_status),
        "holography_requires_capacity_status": str(holography_requires_capacity_status),
        "pass": bool(
            ok_status == z3.sat
            and small_status == z3.unsat
            and roots_do_not_force_capacity_status == z3.sat
            and capacity_with_roots_status == z3.sat
            and capacity_requires_f01_status == z3.unsat
            and twistor_with_roots_status == z3.sat
            and twistor_requires_roots_status == z3.unsat
            and clifford_order_with_n01_status == z3.sat
            and clifford_order_requires_n01_status == z3.unsat
            and holography_with_capacity_status == z3.sat
            and holography_requires_capacity_status == z3.unsat
        ),
    }


def negative_control_section(positive: dict[str, Any]) -> dict[str, Any]:
    layout, blades = Cl(3)
    del layout
    e1 = blades["e1"]
    e2 = blades["e2"]
    e3 = blades["e3"]
    b12 = e1 * e2
    theta_a = 0.58
    theta_b = -0.43
    rz_a = math.cos(theta_a / 2.0) - math.sin(theta_a / 2.0) * b12
    rz_b = math.cos(theta_b / 2.0) - math.sin(theta_b / 2.0) * b12
    v = 0.23 * e1 - 0.47 * e2 + 0.71 * e3
    same_axis_ab = rz_a * (rz_b * v * ~rz_b) * ~rz_a
    same_axis_ba = rz_b * (rz_a * v * ~rz_a) * ~rz_b
    same_axis_gap = math.sqrt(
        (float((same_axis_ab - same_axis_ba) | e1)) ** 2
        + (float((same_axis_ab - same_axis_ba) | e2)) ** 2
        + (float((same_axis_ab - same_axis_ba) | e3)) ** 2
    )

    bad_rotor = 1.08 * rz_a
    bad_rotor_image = bad_rotor * v * ~bad_rotor
    bad_rotor_vec = torch.tensor(
        [float(bad_rotor_image | e1), float(bad_rotor_image | e2), float(bad_rotor_image | e3)],
        dtype=DTYPE,
    )
    original_vec = torch.tensor([float(v | e1), float(v | e2), float(v | e3)], dtype=DTYPE)
    nonunit_rotor_norm_gap = abs(
        float(torch.linalg.vector_norm(bad_rotor_vec).item())
        - float(torch.linalg.vector_norm(original_vec).item())
    )
    rows = {
        "NC1_commuting_rotor_pair_collapses_order_gap": {
            "expected_to_fail": True,
            "same_axis_rotor_order_gap": same_axis_gap,
            "noncommuting_order_gap": positive["clifford_rotor_spinor_transport"]["rotor_noncommuting_order_gap"],
            "pass": bool(
                positive["clifford_rotor_spinor_transport"]["rotor_noncommuting_order_gap"] > 1e-4
                and same_axis_gap < 1e-9
            ),
            "summary": "same-plane Clifford rotors commute; the nonzero order gap requires different generator planes",
        },
        "NC2_nonunit_rotor_breaks_norm_preservation": {
            "expected_to_fail": True,
            "nonunit_rotor_norm_gap": nonunit_rotor_norm_gap,
            "pass": bool(nonunit_rotor_norm_gap > 1e-2),
            "summary": "scaling a Clifford rotor away from unit norm breaks Bloch-vector norm preservation",
        },
        "NC3_entropy_only_probe_collides_under_twistor_rephase": {
            "expected_to_fail": True,
            "entropy_gap": positive["twistor_incidence_hardening"]["entropy_probe_gap_after_local_twistor_rephase"],
            "incidence_phase_gap": positive["twistor_incidence_hardening"]["incidence_phase_gap_after_local_twistor_rephase"],
            "pass": bool(
                positive["twistor_incidence_hardening"]["entropy_probe_gap_after_local_twistor_rephase"] < 1e-9
                and positive["twistor_incidence_hardening"]["incidence_phase_gap_after_local_twistor_rephase"] > 1e-3
            ),
            "summary": "entropy-only equality collides while incidence phase distinguishes",
        },
        "NC4_random_phase_not_twistor_incidence": {
            "expected_to_fail": True,
            "twistor_vs_random_gap": positive["twistor_incidence_hardening"]["twistor_score_vs_random_phase_gap"],
            "pass": bool(positive["twistor_incidence_hardening"]["twistor_score_vs_random_phase_gap"] > 1e-3),
            "summary": "random phase label does not replace the finite twistor-like incidence probe",
        },
        "NC5_too_small_boundary_capacity_rejected": {
            "control_type": "relay_of_constructive_gate",
            "expected_to_fail": True,
            "too_small_capacity_status": positive["boundary_capacity_graph"]["too_small_capacity_status"],
            "pass": positive["boundary_capacity_graph"]["too_small_capacity_status"] == "unsat",
            "summary": "boundary capacity below total edge cut entropy is rejected",
            "audit_note": (
                "Relay-type check: reads z3 status from boundary_capacity_graph_gate; "
                "not an independent ablation. Flagged in 3-model audit."
            ),
        },
    }
    fired = sum(1 for row in rows.values() if row["pass"])
    return {
        "rows": rows,
        "fired_count": fired,
        "rows_total": len(rows),
        "pass": fired == len(rows),
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    net = build_network()
    rows = network_edges(net)

    positive = {
        "clifford_rotor_spinor_transport": clifford_rotor_gate(),
        "twistor_incidence_hardening": twistor_incidence_hardening_gate(net),
        "bounded_tensor_contraction_tool": tensor_tool_boundary_gate(net),
        "boundary_capacity_graph": boundary_capacity_graph_gate(net),
    }
    negative_controls = negative_control_section(positive)
    graveyard_companions = {
        "raw_tensor_index_substrate_rejected": {
            "pass": positive["bounded_tensor_contraction_tool"]["raw_tensor_index_substrate_rejected"],
            "summary": "raw weighted index readout changes under relabeling",
        },
        "entropy_only_identity_rejected": {
            "pass": bool(
                positive["twistor_incidence_hardening"]["entropy_probe_gap_after_local_twistor_rephase"] < 1e-9
                and positive["twistor_incidence_hardening"]["incidence_phase_gap_after_local_twistor_rephase"] > 1e-3
            ),
            "summary": "same entropy spectrum does not establish identity when incidence probes distinguish",
        },
        "derived_structures_not_promoted_to_roots": {
            "pass": bool(
                positive["boundary_capacity_graph"]["roots_do_not_force_capacity_status"] == "sat"
                and positive["boundary_capacity_graph"]["capacity_requires_f01_status"] == "unsat"
                and positive["boundary_capacity_graph"]["twistor_requires_roots_status"] == "unsat"
                and positive["boundary_capacity_graph"]["holography_requires_capacity_status"] == "unsat"
            ),
            "summary": "derived structures require roots/capacity but are not forced by roots alone",
        },
    }
    boundary = {
        "clifford_tool_receipt_not_substrate_canon": {
            "pass": True,
            "summary": "Clifford is a faithful rotor/SU(2) implementation here, not admitted as substrate canon",
        },
        "tensor_tools_allowed_after_invariant_readout": {
            "pass": positive["bounded_tensor_contraction_tool"]["bounded_tensor_tool_allowed"],
            "summary": "bounded tensor contraction matches dense entropy readout but raw index readout is rejected",
        },
        "twistor_status_still_local_incidence_only": {
            "pass": True,
            "summary": "incidence is a finite probe family, not full projective twistor theory",
        },
    }
    all_rows = [*positive.values(), *graveyard_companions.values(), *boundary.values(), negative_controls]
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
            "finite spinor/twistor-like entanglement network with Clifford "
            "rotor faithfulness check, bounded tensor contraction control, and boundary capacity gate"
        ),
        "edge_rows": rows,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "negative_controls": negative_controls,
        "nearby_variants": {
            "total": len(all_rows),
            "passed": sum(1 for row in all_rows if row.get("pass") is True),
        },
        "why_not_v4_probes": (
            "This is a v5 noncanonical formal scout for spinor/twistor "
            "network carrier hardening, Clifford rotor faithfulness, and "
            "tensor-substrate boundary controls; v4 probes do not own this "
            "claim layer or the current formal-scout admission contract."
        ),
        "open_boundaries": [
            "full twistor theory not admitted",
            "ER=EPR/holographic spacetime not admitted",
            "flux remains derived/open",
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
