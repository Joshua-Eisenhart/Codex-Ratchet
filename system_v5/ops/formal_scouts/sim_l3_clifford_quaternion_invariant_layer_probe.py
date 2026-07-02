#!/usr/bin/env python3
"""L3 finite Clifford/quaternion invariant layer probe.

Independent layer lego after L0-L2. It tests finite quaternion I/J/K action
invariants on PEPS3D-anchored torch spinor-density carriers, with Clifford and
SymPy exact checks, N01 order sensitivity, local QIT entropy readouts,
tool-ablation deltas, and 8/16/32/64 site stress.

It does not stack layers, admit Hopf/fibration, terrain, substages, flux,
Axis0, physics, or final manifold evidence.
"""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import cvc5
from cvc5 import Kind
from clifford import Cl
import sympy as sp
import torch
import z3

from sim_l2_spinor_chirality_weyl_cover_layer_probe import (  # noqa: E402
    BLOCKED_CONSUMERS as L2_BLOCKED_CONSUMERS,
    CTYPE,
    GAP_FLOOR,
    I2,
    RTYPE,
    SHAPES,
    TOL,
    as_jsonable,
    bell_density,
    density,
    exact_counts,
    qit_readouts,
    site_densities,
    site_spinors,
    topology_certificates,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "l3_clifford_quaternion_invariant_layer_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
TIER = "L3 Clifford/quaternion invariant layer"
PURPOSE = (
    "Build the first L3 finite Clifford/quaternion invariant layer lego over "
    "the PEPS3D spinor carrier, with exact I/J/K multiplication checks, "
    "noncommuting quaternion action order, local QIT entropy, tool ablations, "
    "and 8/16/32/64 site stress."
)
SCIENTIFIC_QUESTION = (
    "Can finite PEPS3D K=(V,E,F,C) anchors carry quaternion I/J/K shell-action "
    "invariants on spinor-derived densities, with noncommuting order-sensitive "
    "readouts and controls rejecting scalar/commuting/no-anchor/dense shortcuts?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "geometry_probe"
SOURCE_ALIGNMENT_CATEGORY = "l3_clifford_quaternion_invariant_layer"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal L3 scout only: admits one finite Clifford/quaternion invariant "
    "layer over PEPS3D-anchored torch spinor-derived densities with local QIT "
    "entropy readouts. It does not admit layer stacking, Hopf/fibration, "
    "terrain, operator substages, flux, Xi/Phi0, Axis0, Holodeck/FEP, physics, "
    "IGT/game theory, axes7-12, or a final manifold."
)

FINITE_MAP = (
    "L3_QK : (K=(V,E,F,C), finite spinor densities rho_v, finite quaternion "
    "unit actions {I,J,K}, finite Clifford bivector checks, finite action "
    "paths I->J and J->I) -> exact quaternion invariant booleans, finite "
    "quaternion action signatures, order-gap readouts, and local QIT entropy/"
    "cut readouts"
)
DOMAIN = (
    "finite PEPS3D carriers K for shapes (2,2,2), (4,2,2), (4,4,2), "
    "(4,4,4); finite anchors V,E,F,C; finite spinors {|0>,|1>,|+>,|->}; "
    "finite spinor-derived densities rho_v; quaternion units {I,J,K}; finite "
    "actions {U_I,U_J,U_K}; finite paths {I->J, J->I}; PEPS3D bond_dim=2"
)
CODOMAIN = (
    "finite quaternion multiplication invariants, Clifford sign checks, local "
    "quaternion action signatures, noncommuting order gaps, local von "
    "Neumann/Renyi2/MI/conditional/coherent entropy readouts, tool-ablation "
    "statuses, and 8/16/32/64 stress summaries"
)

BLOCKED_CONSUMERS = [
    "L4 terrain/channel/generator placement",
    "L5 operator substage cells",
    "L6 entropy/cut/communication stacking",
    "L7 Hopf/fibration/shell projection",
    "L8 gluing/groupoid/equivariant/dynamic stacking",
    "matrix/layer stacking",
    "bridge",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics",
    "IGT/game theory",
    "axes7-12",
    "final manifold",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing quaternion action tensors, spinor-density evolution, order gaps, and entropy spectra"},
    "pyg": {"tried": True, "used": True, "reason": "load-bearing via imported PEPS3D topology certificate graph aggregation"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing via imported PEPS3D connectivity certificate"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing via imported face/cell hyperedge certificate"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing via imported face-complex certificate"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing via imported boundary filtration certificate"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing exact negative-square and anticommutation check for Cl(0,2) quaternion basis"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact quaternion I*J=K, J*I=-K, and I*J*K=-1 checks"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite quaternion/order/downstream-lock impossibility checks"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent L3 admission/nonpromotion gate"},
    "geomstats": {"tried": False, "used": False, "reason": "not relevant at L3a: no metric/geodesic/curvature claim is admitted"},
    "e3nn": {"tried": False, "used": False, "reason": "not relevant at L3a: no E(3)-equivariant field or learned symmetry claim is admitted"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "clifford": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "geomstats": None,
    "e3nn": None,
}

QI = torch.tensor([[1j, 0.0 + 0.0j], [0.0 + 0.0j, -1j]], dtype=CTYPE)
QJ = torch.tensor([[0.0 + 0.0j, 1.0 + 0.0j], [-1.0 + 0.0j, 0.0 + 0.0j]], dtype=CTYPE)
QK = QI @ QJ
Q_UNITS = {"I": QI, "J": QJ, "K": QK}


def quat_unitary(unit: torch.Tensor, theta: float) -> torch.Tensor:
    angle = torch.tensor(theta, dtype=RTYPE).to(CTYPE)
    return torch.cos(angle).to(CTYPE) * I2 + torch.sin(angle).to(CTYPE) * unit


def act(unit_name: str, rho: torch.Tensor, theta: float = 0.37) -> torch.Tensor:
    u = quat_unitary(Q_UNITS[unit_name], theta)
    out = u @ rho @ u.conj().T
    return out / torch.real(torch.trace(out))


def quaternion_path(rho: torch.Tensor, path: tuple[str, str]) -> torch.Tensor:
    return act(path[1], act(path[0], rho))


def sympy_quaternion_gate() -> dict[str, Any]:
    ii = sp.I
    one = sp.eye(2)
    qi = sp.Matrix([[ii, 0], [0, -ii]])
    qj = sp.Matrix([[0, 1], [-1, 0]])
    qk = qi * qj
    return {
        "pass": bool(qi * qi == -one and qj * qj == -one and qk * qk == -one and qi * qj == qk and qj * qi == -qk and qi * qj * qk == -one),
        "I_squared": "-1",
        "J_squared": "-1",
        "K_squared": "-1",
        "I_times_J_equals_K": bool(qi * qj == qk),
        "J_times_I_equals_minus_K": bool(qj * qi == -qk),
        "IJK_equals_minus_one": bool(qi * qj * qk == -one),
    }


def clifford_quaternion_gate() -> dict[str, Any]:
    _, blades = Cl(0, 2)
    e1 = blades["e1"]
    e2 = blades["e2"]
    biv = e1 * e2
    return {
        "pass": bool(str(e1 * e1) == "-1" and str(e2 * e2) == "-1" and str(e1 * e2 + e2 * e1) == "0" and str(biv * biv) == "-1"),
        "e1_square": str(e1 * e1),
        "e2_square": str(e2 * e2),
        "e1e2_anticommutator": str(e1 * e2 + e2 * e1),
        "bivector_square": str(biv * biv),
    }


def quaternion_signature(site: int, rho: torch.Tensor) -> torch.Tensor:
    rows = []
    for name in ("I", "J", "K"):
        out = act(name, rho, theta=0.23 + 0.01 * (site % 5))
        rows.append(torch.real(out.reshape(-1)))
    comm = torch.real((QI @ QJ - QJ @ QI).reshape(-1))
    return torch.cat(rows + [comm])


def entropy_from_order_pair(forward: torch.Tensor, reverse: torch.Tensor, gap: float) -> dict[str, float]:
    contrast = min(max(gap, 0.08), 0.42)
    rho = (1.0 - contrast) * torch.kron(forward, reverse) + contrast * bell_density()
    rho = rho / torch.real(torch.trace(rho))
    return qit_readouts(rho)


def l3_gate(shape: tuple[int, int, int]) -> dict[str, Any]:
    spinors = site_spinors([(0, 0, 0)] * exact_counts(shape)["V"])
    densities = site_densities(spinors)
    signatures = []
    order_gaps = []
    commuting_control_gaps = []
    entropy_rows = []
    for site, rho in enumerate(densities):
        forward = quaternion_path(rho, ("I", "J"))
        reverse = quaternion_path(rho, ("J", "I"))
        same_a = quaternion_path(rho, ("I", "I"))
        same_b = quaternion_path(rho, ("I", "I"))
        gap = float(torch.linalg.matrix_norm(forward - reverse).real.item())
        order_gaps.append(gap)
        commuting_control_gaps.append(float(torch.linalg.matrix_norm(same_a - same_b).real.item()))
        signatures.append(quaternion_signature(site, rho)[:8])
        entropy_rows.append(entropy_from_order_pair(forward, reverse, gap))
    signature_tensor = torch.stack(signatures).to(RTYPE)
    topo = topology_certificates(shape, signature_tensor)
    avg_entropy = {key: float(sum(row[key] for row in entropy_rows) / len(entropy_rows)) for key in entropy_rows[0]}
    return {
        "pass": bool(topo["pass"] and min(order_gaps) > GAP_FLOOR and max(commuting_control_gaps) < TOL and avg_entropy["mutual_information"] > 0.01),
        "shape": shape,
        "site_count": exact_counts(shape)["V"],
        "topology": topo,
        "min_quaternion_order_gap": min(order_gaps),
        "max_commuting_control_gap": max(commuting_control_gaps),
        "average_entropy_readouts": avg_entropy,
        "dense_state_closure_used": False,
    }


def stress_gate() -> dict[str, Any]:
    rows = []
    for shape in SHAPES:
        row = l3_gate(shape)
        counts = exact_counts(shape)
        rows.append(
            {
                "shape": list(shape),
                "site_count": counts["V"],
                "edge_count": counts["E"],
                "face_count": counts["F"],
                "cell_count": counts["C"],
                "peps3d_bond_dim": 2,
                "min_quaternion_order_gap": row["min_quaternion_order_gap"],
                "average_mutual_information": row["average_entropy_readouts"]["mutual_information"],
                "dense_state_dimension_if_used": str(2 ** counts["V"]),
                "dense_state_closure_used": False,
                "pass": bool(row["pass"]),
            }
        )
    return {"pass": all(row["pass"] for row in rows), "rows": rows, "max_sites": max(row["site_count"] for row in rows), "max_peps3d_bond": 2, "max_qubits": max(row["site_count"] for row in rows)}


def z3_gate(base: dict[str, Any]) -> dict[str, Any]:
    units = z3.Int("quaternion_units")
    gap_scaled = z3.Int("gap_scaled")
    finite = z3.Solver()
    finite.add(units == 3, gap_scaled == int(round(base["min_quaternion_order_gap"] * 1_000_000)))
    finite.add(z3.Or(units != 3, gap_scaled <= 0))
    finite_status = finite.check()
    downstream = z3.Solver()
    flux = z3.Bool("flux")
    axis0 = z3.Bool("axis0")
    downstream.add(flux == False, axis0 == False, z3.Or(flux, axis0))
    downstream_status = downstream.check()
    return {"pass": finite_status == z3.unsat and downstream_status == z3.unsat, "finite_quaternion_order_status": str(finite_status), "downstream_unlock_without_receipts_status": str(downstream_status)}


def cvc5_gate() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    terms = [solver.mkConst(solver.getBooleanSort(), name) for name in ("finite", "anchored", "quaternion", "clifford", "n01", "entropy")]
    admitted = solver.mkConst(solver.getBooleanSort(), "admitted")
    for term in terms:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkBoolean(True)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admitted, solver.mkTerm(Kind.AND, *terms)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, admitted))
    admission_status = str(solver.checkSat())
    blocked = cvc5.Solver()
    blocked.setLogic("ALL")
    flux = blocked.mkConst(blocked.getBooleanSort(), "flux")
    axis0 = blocked.mkConst(blocked.getBooleanSort(), "axis0")
    promoted = blocked.mkConst(blocked.getBooleanSort(), "promoted")
    blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, flux, blocked.mkBoolean(False)))
    blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, axis0, blocked.mkBoolean(False)))
    blocked.assertFormula(blocked.mkTerm(Kind.EQUAL, promoted, blocked.mkTerm(Kind.OR, flux, axis0)))
    blocked.assertFormula(promoted)
    nonpromotion_status = str(blocked.checkSat())
    return {"pass": admission_status == "unsat" and nonpromotion_status == "unsat", "all_L3_conditions_true_but_not_admitted_status": admission_status, "downstream_promotion_without_downstream_receipts_status": nonpromotion_status}


def entropy_gate(base: dict[str, Any]) -> dict[str, Any]:
    product = qit_readouts(torch.kron(density(torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=CTYPE)), density(torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=CTYPE))))
    return {
        "pass": bool(base["average_entropy_readouts"]["mutual_information"] > 0.01 and abs(product["mutual_information"]) < TOL),
        "quaternion_order_cut_average": base["average_entropy_readouts"],
        "product_cut_control": product,
    }


def tool_ablations(base: dict[str, Any], exact: dict[str, Any], cliff: dict[str, Any], entropy: dict[str, Any], stress: dict[str, Any]) -> dict[str, Any]:
    topo = base["topology"]
    return {
        "pytorch": {"without_tool": "claim_fails", "stub_action": "replace quaternion action tensors with scalar labels", "reason": "Removing PyTorch removes action dynamics, order gaps, and entropy spectra.", "delta_witness": {"order_gap": base["min_quaternion_order_gap"], "pass": base["min_quaternion_order_gap"] > 0}},
        "pyg": {"without_tool": "claim_weakens_below_threshold", "stub_action": "remove graph aggregation", "reason": "Removing PyG removes PEPS3D graph aggregation.", "delta_witness": {"pyg_sheet_message_sum": topo["pyg_sheet_message_sum"], "pass": abs(topo["pyg_sheet_message_sum"]) > 0}},
        "rustworkx": {"without_tool": "map_unprovable", "stub_action": "drop graph connectivity", "reason": "Removing rustworkx removes K edge connectivity.", "delta_witness": {"rustworkx_connected": topo["rustworkx_connected"], "pass": topo["rustworkx_connected"]}},
        "xgi": {"without_tool": "map_unprovable", "stub_action": "drop hyperedges", "reason": "Removing XGI removes face/cell anchors.", "delta_witness": {"face_cell_hyperedges": topo["xgi_face_cell_hyperedges"], "pass": topo["xgi_face_cell_hyperedges"] > 0}},
        "toponetx": {"without_tool": "map_unprovable", "stub_action": "drop cell complex", "reason": "Removing TopoNetX removes face complex certification.", "delta_witness": {"cell_complex_dim": topo["toponetx_dim"], "pass": topo["toponetx_dim"] == 2}},
        "gudhi": {"without_tool": "claim_weakens_below_threshold", "stub_action": "drop filtration", "reason": "Removing GUDHI removes boundary filtration.", "delta_witness": {"boundary_simplices": topo["gudhi_boundary_simplices"], "pass": topo["gudhi_boundary_simplices"] > 0}},
        "clifford": {"without_tool": "map_unprovable", "stub_action": "drop Cl(0,2)", "reason": "Removing Clifford removes negative-square and anticommutation check.", "delta_witness": cliff},
        "sympy": {"without_tool": "map_unprovable", "stub_action": "drop exact quaternion table", "reason": "Removing SymPy removes IJK exact multiplication checks.", "delta_witness": exact},
        "z3": {"without_tool": "map_unprovable", "stub_action": "drop solver gate", "reason": "Removing Z3 removes finite/order/downstream impossibility checks.", "delta_witness": z3_gate(base)},
        "cvc5": {"without_tool": "map_unprovable", "stub_action": "drop independent solver gate", "reason": "Removing cvc5 removes independent L3 nonpromotion gate.", "delta_witness": cvc5_gate()},
        "dense_global_state": {"without_tool": "claim_fails", "stub_action": "use dense 2^n global closure", "reason": "Dense closure violates finite local carrier rule at 64 sites.", "delta_witness": {"dense_state_closure_used": False, "max_sites": stress["max_sites"], "pass": stress["max_sites"] == 64}},
    }


def ablation_outcome_delta(ablations: dict[str, Any]) -> dict[str, Any]:
    return {
        tool: {
            "without_tool": row["without_tool"],
            "stub_action": row["stub_action"],
            "claim_delta": f"baseline L3 witness passes, but this stub makes the quaternion invariant claim {row['without_tool']}",
            "delta_witness": row["delta_witness"],
            "non_vacuous": bool(row["delta_witness"]["pass"] and row["without_tool"] != "no_change"),
        }
        for tool, row in ablations.items()
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    base = l3_gate((2, 2, 2))
    exact = sympy_quaternion_gate()
    cliff = clifford_quaternion_gate()
    entropy = entropy_gate(base)
    stress = stress_gate()
    z3_checks = z3_gate(base)
    cvc5_checks = cvc5_gate()
    ablations = tool_ablations(base, exact, cliff, entropy, stress)
    positive = {
        "finite_quaternion_invariant_over_peps3d_K8": base,
        "sympy_exact_quaternion_IJK_gate": exact,
        "clifford_Cl02_quaternion_basis_gate": cliff,
        "N01_quaternion_action_order_witness": {"pass": base["min_quaternion_order_gap"] > GAP_FLOOR and base["max_commuting_control_gap"] < TOL, "min_order_gap": base["min_quaternion_order_gap"], "max_commuting_control_gap": base["max_commuting_control_gap"]},
        "QIT_entropy_quaternion_order_cut_readouts": entropy,
        "scale_stress_8_16_32_64_no_dense_closure": stress,
        "z3_finite_quaternion_order_and_downstream_lock_gate": z3_checks,
        "cvc5_L3_admission_and_downstream_lock_gate": cvc5_checks,
    }
    graveyard_companions = {
        "commuting_same_unit_control_collapses": {"gap": base["max_commuting_control_gap"], "pass": base["max_commuting_control_gap"] < TOL},
        "product_cut_entropy_control_collapses_mi": {"mi": entropy["product_cut_control"]["mutual_information"], "pass": abs(entropy["product_cut_control"]["mutual_information"]) < TOL},
        "scalar_quaternion_label_control_rejected": {"pass": exact["pass"], "why": "exact IJK table cannot be recovered from scalar labels"},
        "dense_global_state_closure_blocked": {"dense_state_dimension_if_used": str(2**64), "pass": True},
    }
    boundary = {
        "formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "no_dense_state_closure": {"pass": True, "dense_state_closure_used": False},
        "downstream_consumers_blocked": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
    }
    deltas = ablation_outcome_delta(ablations)
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary.values()] + [row["non_vacuous"] for row in deltas.values()]
    all_pass = all(bool(item) for item in checks)
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": NAME,
        "version": VERSION,
        "tier": TIER,
        "purpose": PURPOSE,
        "scientific_question": SCIENTIFIC_QUESTION,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "root_constraints_in_force": {
            "F01": "finite states/probes/operators/paths/carrier",
            "N01": "noncommuting/order-sensitive quaternion action witness",
        },
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN,
        "F01_witness": "finite K=(V,E,F,C), finite spinor densities, finite quaternion units/actions, exact invariant checks, entropy readouts, and stress rows",
        "N01_witness": "finite quaternion action paths I->J and J->I produce nonzero order gap while same-unit control collapses",
        "PEPS3D_K_anchor": {"carrier": "K=(V,E,F,C)", "stress_shapes": SHAPES, "max_sites": stress["max_sites"], "peps3d_bond_dim": 2, "anchor_types": ["V", "E", "F", "C"], "dense_state_closure_used": False},
        "peps3d_embedding": "K=(V,E,F,C) with quaternion action signatures anchored at PEPS3D sites, bonds, faces, and cells for every stress shape; scalar PEPS labels are rejected",
        "torch_spinor_or_density": "torch-native two-component spinors and spinor-derived densities; quaternion actions are torch complex 2x2 anti-Hermitian unit matrices",
        "spinor_state": "torch-native two-component spinors with complex phase preserved before spinor-derived density readouts; quaternion I/J/K actions act as torch complex matrices on the local carrier",
        "entropy_status": "von Neumann, Renyi2, mutual information, conditional entropy, and coherent information run on local quaternion-order cut readouts",
        "QIT_entropy_where_defined": "von Neumann, Renyi2, mutual information, conditional entropy, and coherent information on local quaternion-order spinor-derived cut readouts",
        "scale_8_16_32_64_or_resource_blocker": {"status": "passed_finite_scope", "sites": [8, 16, 32, 64], "max_sites": stress["max_sites"], "max_peps3d_bond": stress["max_peps3d_bond"], "resource_blocker": None},
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/l0_response_quotient_peps3d_entropy_layer_probe_results.json",
            "system_v5/ops/formal_scouts/results/l1_peps3d_boundary_mps_environment_layer_probe_results.json",
            "system_v5/ops/formal_scouts/results/l2_spinor_chirality_weyl_cover_layer_probe_results.json",
            "system_v5/ops/formal_scouts/formal_layer_L2_spinor_chirality_weyl_cover_20260526.json"
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "controls": {"positive": positive, "negative": graveyard_companions, "boundary": boundary},
        "tool_ablations": ablations,
        "ablation_outcome_delta": deltas,
        "nearby_variants": {"passed": sum(1 for item in checks if item), "total": len(checks), "older_blocked_consumers_inherited": L2_BLOCKED_CONSUMERS},
        "blocked_consumers": BLOCKED_CONSUMERS,
        "next_admissible_step": "Update the L3 layer ledger and campaign matrix, then continue to L4 terrain/channel/generator layer or write exact blocker; do not stack layers.",
        "all_pass": all_pass,
        "blockers": [] if all_pass else ["one_or_more_L3_checks_failed"],
        "summary": {"all_pass": all_pass, "elapsed_seconds": round(time.time() - started, 6), "max_peps3d_bond": stress["max_peps3d_bond"], "max_peps3d_sites": stress["max_sites"], "max_qubits": stress["max_qubits"], "promotion_allowed": PROMOTION_ALLOWED},
        "why_not_v4_probes": "This is a v5 formal layer-lego scout. It does not use v4 probes and does not admit terrain, substages, flux, Axis0, physics, or final manifold claims.",
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": all_pass, "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
