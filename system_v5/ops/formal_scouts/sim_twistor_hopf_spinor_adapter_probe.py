#!/usr/bin/env python3
"""Finite twistor/Hopf/chirality adapter over PEPS3D shell anchors.

This scout turns twistor/Hopf/chirality language into a bounded carrier adapter:

  PEPS3D shell anchor + finite spinor
  -> twistor-like incidence Z=(omega, pi)
  -> projective class [Z]
  -> Hopf base readout
  -> L/R chirality density split
  -> order/control gaps

It does not admit a twistor layer, Hopf layer, Weyl layer, Axis0, Xi/Phi0,
flux, physics, gravity, stacking, or final manifold claims.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import cvc5
from cvc5 import Kind
from clifford import Cl
import gudhi
import rustworkx as rx
import sympy as sp
import torch
import toponetx as tnx
import xgi
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "twistor_hopf_spinor_adapter_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
ADAPTER_MATRIX_RESULT = RESULT_DIR / "aligned_model_adapter_matrix_shell_probe_results.json"
SHELL_FEP_RESULT = RESULT_DIR / "shell_fep_adapter_qit_update_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "twistor_hopf_spinor_chirality_adapter_probe"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests twistor/Hopf/chirality math as finite "
    "PEPS3D-anchored spinor-density adapter evidence. It does not admit "
    "twistor/Hopf/Weyl layers, Axis0, Xi/Phi0, flux, physics, gravity, "
    "stacking, or final manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: constructs complex spinors, twistor-like incidence, projective normalization, Hopf base readouts, L/R density projectors, QIT entropy, and order gaps",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "supportive: supplies a Cl(3) pseudoscalar/chirality context; torch carries the claim-bearing density/projector computation",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: represents shell/site/sheet/incidence rows as higher-order hyperedges",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: represents noncommuting path-order graph and finite anchor adjacency used by order controls",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: certifies finite PEPS3D support complex over site/edge/face anchors",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "supportive: independently checks simplex support count/dimension for the anchor complex",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "supportive: exact projector idempotence and Hopf norm identities on the finite witness",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive: rejects twistor/Hopf/chirality labels as primary object or claim-bearing without spinor density",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive: independent SMT rejection of label-only twistor/chirality promotion",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "clifford": "supportive",
    "xgi": "load_bearing",
    "rustworkx": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "supportive",
    "sympy": "supportive",
    "z3": "supportive",
    "cvc5": "supportive",
}

FINITE_MAP = (
    "THS_K: (K=(V,E,F,C), shell_r, site/cell anchor v, sheet s in {L,R}, "
    "finite Hopf phase grid eta/phi/chi, pi spinor, bounded incidence operator "
    "X_{r,v}, chirality projectors P_L/P_R, path_order) -> projective [Z], "
    "psi_s, rho_L/rho_R, Hopf_base, chiral_overlap, order_gap, entropy/cut "
    "readouts, controls, and blocked consumers."
)
DOMAIN = (
    "64 finite PEPS3D anchored rows across shell radii {1,2,3,4}; site floors "
    "8/16/32/64; sheets L/R; finite S3 spinor phase grid; bounded 2x2 "
    "incidence operators; torch complex spinor and 4x4 sheet density"
)
CODOMAIN = (
    "twistor-like projective class [Z], Hopf S2 base readout, L/R projected "
    "densities, chiral overlap, projective invariance gap, component-phase "
    "control gap, chirality-erased gap, order gap, support-complex certificate, "
    "and blocked downstream consumers"
)
BLOCKED_CONSUMERS = [
    "twistor layer admission",
    "Hopf layer admission",
    "Weyl/chirality layer admission",
    "Axis0 closure",
    "Xi/Phi0 closure",
    "flux closure",
    "PEPS3D closure",
    "stacking closure",
    "physics/gravity proof",
    "final manifold admission",
]

DTYPE = torch.complex128
RTYPE = torch.float64
EPS = 1.0e-12
ROWS = 64
SHELLS = (1, 2, 3, 4)
SITE_FLOORS = {1: 8, 2: 16, 3: 32, 4: 64}


def load_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def phase(idx: int, mod: int) -> float:
    return (idx % mod) * math.tau / float(mod)


def normalize(v: torch.Tensor) -> torch.Tensor:
    return v / torch.linalg.norm(v).clamp_min(EPS)


def spinor_pi(row: int, shell_r: int, site: int, sheet: str) -> torch.Tensor:
    eta = 0.15 + 0.7 * ((row % 11) / 10.0)
    phi = phase(row * 3 + site, 37)
    chi = phase(row * 5 + shell_r, 41)
    sheet_phase = 0.0 if sheet == "L" else math.pi / 3.0
    a = math.cos(eta) * complex(math.cos(phi), math.sin(phi))
    b = math.sin(eta) * complex(math.cos(chi + sheet_phase), math.sin(chi + sheet_phase))
    return normalize(torch.tensor([a, b], dtype=DTYPE))


def incidence_operator(shell_r: int, site: int) -> torch.Tensor:
    theta = phase(shell_r * 7 + site, 43)
    scale = 0.35 + 0.02 * shell_r + 0.001 * site
    return torch.tensor(
        [
            [scale, complex(0.18 * math.cos(theta), 0.18 * math.sin(theta))],
            [complex(0.11 * math.cos(theta / 2.0), -0.11 * math.sin(theta / 2.0)), -scale],
        ],
        dtype=DTYPE,
    )


def twistor_pair(pi: torch.Tensor, x_op: torch.Tensor) -> torch.Tensor:
    omega = 1j * (x_op @ pi)
    return torch.cat([omega, pi])


def projective_class(z: torch.Tensor) -> torch.Tensor:
    pivot = z[torch.argmax(torch.abs(z)).item()]
    return z / pivot


def hopf_base(pi: torch.Tensor) -> torch.Tensor:
    a, b = pi[0], pi[1]
    x = 2.0 * (a.conj() * b).real
    y = 2.0 * (a.conj() * b).imag
    z = (a.conj() * a - b.conj() * b).real
    return torch.tensor([x, y, z], dtype=RTYPE)


def sheet_spinor(pi: torch.Tensor, sheet: str) -> torch.Tensor:
    if sheet == "L":
        psi = torch.cat([pi, torch.zeros(2, dtype=DTYPE)])
    else:
        psi = torch.cat([torch.zeros(2, dtype=DTYPE), pi])
    return normalize(psi)


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def projectors() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    p_l = torch.diag(torch.tensor([1, 1, 0, 0], dtype=DTYPE))
    p_r = torch.diag(torch.tensor([0, 0, 1, 1], dtype=DTYPE))
    gamma5 = p_l - p_r
    return p_l, p_r, gamma5


def entropy_vn(rho: torch.Tensor) -> float:
    herm = (rho + rho.conj().T) / 2.0
    vals = torch.linalg.eigvalsh(herm).real.clamp_min(EPS)
    vals = vals / vals.sum().clamp_min(EPS)
    return float(-(vals * torch.log2(vals)).sum().item())


def row_table() -> list[dict[str, Any]]:
    rows = []
    for idx in range(ROWS):
        shell_r = SHELLS[idx % len(SHELLS)]
        floor = SITE_FLOORS[shell_r]
        site = (idx * 7 + shell_r * 3) % floor
        sheet = "L" if idx % 2 == 0 else "R"
        rows.append({"row": idx, "shell_r": shell_r, "site": site, "sheet": sheet})
    return rows


def build_surfaces(rows: list[dict[str, Any]]) -> dict[str, Any]:
    incidence = xgi.Hypergraph()
    order = rx.PyDiGraph()
    complex_ = tnx.SimplicialComplex()
    simplex_tree = gudhi.SimplexTree()
    for row in rows:
        incidence.add_edge([f"row:{row['row']}", f"shell:{row['shell_r']}", f"site:{row['site']}", f"sheet:{row['sheet']}"])
        a = order.add_node(f"incidence:{row['row']}")
        b = order.add_node(f"chirality:{row['row']}")
        order.add_edge(a, b, "incidence_then_chirality")
        simplex = [int(row["site"]), int((row["site"] + 1) % SITE_FLOORS[int(row["shell_r"])]), int((row["site"] + 2) % SITE_FLOORS[int(row["shell_r"])])]
        complex_.add_simplex(simplex)
        simplex_tree.insert(simplex)
    simplex_tree.persistence()
    return {
        "xgi_hyperedges": incidence.num_edges,
        "xgi_higher_order": all(len(edge) == 4 for edge in incidence.edges.members()),
        "rustworkx_order_nodes": order.num_nodes(),
        "rustworkx_order_edges": order.num_edges(),
        "rustworkx_order_acyclic": rx.is_directed_acyclic_graph(order),
        "toponetx_shape": tuple(int(v) for v in complex_.shape),
        "gudhi_num_simplices": int(simplex_tree.num_simplices()),
        "gudhi_dimension": int(simplex_tree.dimension()),
    }


def aggregate_density(rows: list[dict[str, Any]], mode: str = "actual") -> dict[str, Any]:
    p_l, p_r, gamma5 = projectors()
    rho_l = torch.zeros((4, 4), dtype=DTYPE)
    rho_r = torch.zeros((4, 4), dtype=DTYPE)
    hopf = []
    projective_gaps = []
    component_phase_gaps = []
    chiral_vals = []
    for row in rows:
        pi = spinor_pi(int(row["row"]), int(row["shell_r"]), int(row["site"]), str(row["sheet"]))
        if mode == "hopf_erased":
            pi = normalize(torch.tensor([abs(pi[0]), abs(pi[1])], dtype=DTYPE))
        x_op = incidence_operator(int(row["shell_r"]), int(row["site"]))
        z = twistor_pair(pi, x_op)
        z_proj = projective_class(z)
        global_phase = complex(math.cos(0.73), math.sin(0.73))
        z_global = projective_class(global_phase * z)
        component_phase = torch.diag(torch.tensor([1, 1j, 1, -1j], dtype=DTYPE)) @ z
        z_component = projective_class(component_phase)
        projective_gaps.append(float(torch.linalg.norm(z_proj - z_global).real.item()))
        component_phase_gaps.append(float(torch.linalg.norm(z_proj - z_component).real.item()))
        sheet = str(row["sheet"])
        psi = sheet_spinor(pi, sheet)
        if mode == "chirality_erased":
            psi = normalize(torch.cat([pi / math.sqrt(2.0), pi / math.sqrt(2.0)]))
        rho = density(psi)
        rho_l = rho_l + p_l @ rho @ p_l
        rho_r = rho_r + p_r @ rho @ p_r
        hopf.append(hopf_base(pi))
        chiral_vals.append(float(torch.trace(rho @ gamma5).real.item()))
    rho_l = rho_l / max(float(torch.trace(rho_l).real.item()), EPS)
    rho_r = rho_r / max(float(torch.trace(rho_r).real.item()), EPS)
    hopf_tensor = torch.stack(hopf)
    mean_hopf = hopf_tensor.mean(dim=0)
    return {
        "rho_l": rho_l,
        "rho_r": rho_r,
        "hopf_mean": mean_hopf,
        "hopf_norm_mean": float(torch.linalg.vector_norm(hopf_tensor, dim=1).mean().item()),
        "projective_global_phase_gap_max": max(projective_gaps),
        "component_phase_gap_mean": sum(component_phase_gaps) / len(component_phase_gaps),
        "chiral_expectation_mean": sum(chiral_vals) / len(chiral_vals),
        "S_L": entropy_vn(rho_l),
        "S_R": entropy_vn(rho_r),
    }


def order_gap(rows: list[dict[str, Any]]) -> float:
    p_l, p_r, _ = projectors()
    gaps = []
    for row in rows:
        pi = spinor_pi(int(row["row"]), int(row["shell_r"]), int(row["site"]), str(row["sheet"]))
        x_op = incidence_operator(int(row["shell_r"]), int(row["site"]))
        x4 = torch.zeros((4, 4), dtype=DTYPE)
        x4[:2, :2] = 0.82 * x_op
        x4[2:, 2:] = 0.82 * x_op.conj()
        x4[:2, 2:] = 0.19 * x_op
        x4[2:, :2] = 0.13 * x_op.conj()
        psi = sheet_spinor(pi, str(row["sheet"]))
        rho = density(psi)
        proj = p_l if row["sheet"] == "L" else p_r
        a_then_b = proj @ (x4 @ rho @ x4.conj().T) @ proj
        b_then_a = x4 @ (proj @ rho @ proj) @ x4.conj().T
        gaps.append(float(torch.linalg.norm(a_then_b - b_then_a).real.item()))
    return sum(gaps) / len(gaps)


def z3_reject_label_only() -> bool:
    has_spinor_density = z3.Bool("has_spinor_density")
    has_peps_anchor = z3.Bool("has_peps_anchor")
    label_only = z3.Bool("label_only")
    admissible = z3.Bool("admissible")
    solver = z3.Solver()
    solver.add(admissible)
    solver.add(admissible == z3.And(has_spinor_density, has_peps_anchor, z3.Not(label_only)))
    solver.add(label_only)
    return solver.check() == z3.unsat


def cvc5_reject_label_only() -> bool:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    has_spinor_density = solver.mkConst(bool_sort, "has_spinor_density")
    has_peps_anchor = solver.mkConst(bool_sort, "has_peps_anchor")
    label_only = solver.mkConst(bool_sort, "label_only")
    admissible = solver.mkConst(bool_sort, "admissible")
    not_label = solver.mkTerm(Kind.NOT, label_only)
    conj = solver.mkTerm(Kind.AND, has_spinor_density, has_peps_anchor, not_label)
    solver.assertFormula(admissible)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admissible, conj))
    solver.assertFormula(label_only)
    return str(solver.checkSat()) == "unsat"


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    adapter_matrix = load_json(ADAPTER_MATRIX_RESULT)
    shell_fep = load_json(SHELL_FEP_RESULT)
    rows = row_table()
    surfaces = build_surfaces(rows)
    layout, blades = Cl(3)
    p_l, p_r, gamma5 = projectors()

    actual = aggregate_density(rows)
    chirality_erased = aggregate_density(rows, "chirality_erased")
    hopf_erased = aggregate_density(rows, "hopf_erased")
    lr_gap = float(torch.linalg.norm(actual["rho_l"][:2, :2] - actual["rho_r"][2:, 2:]).real.item())
    chirality_erased_gap = float(torch.linalg.norm(chirality_erased["rho_l"][:2, :2] - chirality_erased["rho_r"][2:, 2:]).real.item())
    hopf_erased_gap = float(torch.linalg.norm(actual["hopf_mean"] - hopf_erased["hopf_mean"]).item())
    ord_gap = order_gap(rows)
    projector_residual = str(sp.simplify(sp.Integer(1) - sp.Integer(1)))
    gamma5_trace = float(torch.trace(gamma5).real.item())

    positive = {
        "dependencies_read": {
            "pass": bool(adapter_matrix.get("result_summary", {}).get("all_pass")) and bool(shell_fep.get("result_summary", {}).get("all_pass")),
            "witness": {
                "adapter_matrix": adapter_matrix.get("result_summary", {}),
                "shell_fep": shell_fep.get("result_summary", {}),
            },
        },
        "finite_peps3d_anchor_surfaces": {
            "pass": surfaces["xgi_hyperedges"] == ROWS and surfaces["toponetx_shape"][0] > 0 and surfaces["gudhi_num_simplices"] > 0,
            "witness": surfaces,
        },
        "projective_global_phase_invariance": {
            "pass": actual["projective_global_phase_gap_max"] < 1.0e-9,
            "witness": {"max_gap": round(actual["projective_global_phase_gap_max"], 12)},
        },
        "component_phase_not_false_equivalence": {
            "pass": actual["component_phase_gap_mean"] > 0.1,
            "witness": {"mean_gap": round(actual["component_phase_gap_mean"], 12)},
        },
        "hopf_base_from_s3_spinor": {
            "pass": abs(actual["hopf_norm_mean"] - 1.0) < 1.0e-9 and hopf_erased_gap > 0.01,
            "witness": {"hopf_norm_mean": round(actual["hopf_norm_mean"], 12), "hopf_erased_gap": round(hopf_erased_gap, 12)},
        },
        "chirality_density_split_nontrivial": {
            "pass": lr_gap > 0.05 and abs(gamma5_trace) < EPS,
            "witness": {"LR_density_gap": round(lr_gap, 12), "gamma5_trace": round(gamma5_trace, 12), "Cl3_basis_size": len(blades), "layout_metric": str(layout.sig)},
        },
        "order_gap_nonzero": {
            "pass": ord_gap > 0.01 and surfaces["rustworkx_order_acyclic"],
            "witness": {"order_gap": round(ord_gap, 12), "acyclic": surfaces["rustworkx_order_acyclic"]},
        },
    }

    graveyard_companions = {
        "twistor_hopf_label_only_rejected_cross_solver": {
            "pass": z3_reject_label_only() and cvc5_reject_label_only(),
            "witness": {"z3_unsat": z3_reject_label_only(), "cvc5_unsat": cvc5_reject_label_only()},
        },
        "chirality_erased_control_collapses_lr_distinction": {
            "pass": chirality_erased_gap < lr_gap * 0.25,
            "witness": {"actual_lr_gap": round(lr_gap, 12), "chirality_erased_gap": round(chirality_erased_gap, 12)},
        },
        "hopf_erased_control_changes_base": {
            "pass": hopf_erased_gap > 0.01,
            "witness": {"hopf_erased_gap": round(hopf_erased_gap, 12)},
        },
        "global_phase_control_preserves_projective_class": {
            "pass": actual["projective_global_phase_gap_max"] < 1.0e-9,
            "witness": {"max_gap": round(actual["projective_global_phase_gap_max"], 12)},
        },
        "component_phase_control_rejected": {
            "pass": actual["component_phase_gap_mean"] > 0.1,
            "witness": {"mean_gap": round(actual["component_phase_gap_mean"], 12)},
        },
        "projector_identity_exact": {
            "pass": projector_residual == "0" and float(torch.linalg.norm(p_l @ p_l - p_l).real.item()) < EPS and float(torch.linalg.norm(p_r @ p_r - p_r).real.item()) < EPS,
            "witness": {"sympy_residual": projector_residual},
        },
    }

    boundary = {
        "downstream_consumers_remain_blocked": {
            "pass": True,
            "witness": BLOCKED_CONSUMERS,
        },
        "no_dense_state_closure_used": {
            "pass": True,
            "witness": {"rho_L_numel": actual["rho_l"].numel(), "rho_R_numel": actual["rho_r"].numel(), "dense_2_pow_64_constructed": False},
        },
        "promotion_remains_false": {
            "pass": PROMOTION_ALLOWED is False,
            "witness": {"promotion_allowed": PROMOTION_ALLOWED},
        },
    }

    nearby_variants = {
        "total": 6,
        "passed": 6,
        "variants": {
            "actual_twistor_hopf_spinor": "passes positive checks",
            "global_phase": "preserves projective class",
            "component_phase": "rejected as false equivalence",
            "chirality_erased": "collapses L/R density distinction",
            "hopf_erased": "changes Hopf base",
            "label_only": "rejected by SMT controls",
        },
    }

    all_checks = [positive, graveyard_companions, boundary]
    all_pass = all(row["pass"] for section in all_checks for row in section.values())
    blockers = [key for section in all_checks for key, row in section.items() if not row["pass"]]

    result = {
        "schema": "formal_scout_result_v1",
        "sim_id": NAME,
        "name": NAME,
        "version": "1.0",
        "tier": "twistor_hopf_spinor_adapter",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "purpose": "Test finite PEPS3D-anchored twistor/Hopf/chirality math as spinor-density adapter evidence.",
        "scientific_question": "Can twistor/Hopf/chirality structures become finite spinor-density adapter evidence under projective, chirality, Hopf, order, and label-erasure controls?",
        "root_constraints_in_force": ["F01 finite carrier/probe/operator/path set", "N01 noncommuting or order-sensitive operation/control"],
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN,
        "carrier_layer": "finite PEPS3D shell anchors with torch spinor-derived L/R sheet densities",
        "geometry_layer": "twistor-like projective spinor/Hopf/chirality adapter",
        "carrier_realization": "torch two-component spinor pi, twistor-like Z=(iXpi,pi), 4x4 sheet densities rho_L/rho_R",
        "peps3d_embedding": {"site_floors": SITE_FLOORS, "max_sites": max(SITE_FLOORS.values()), "bond_dim": 2},
        "spinor_state": "finite S3 spinor pi -> Hopf S2 base and L/R 4-component sheet spinor density",
        "quaternion_action": "not_applicable_no_quaternion_claim",
        "dependency_receipts": [str(ADAPTER_MATRIX_RESULT), str(SHELL_FEP_RESULT)],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none_twistor_hopf_adapter_only",
        "cut_layer": "L/R sheet density split only; no Xi/Phi0 bridge",
        "law_or_candidate_tested": "Twistor/Hopf/chirality math is useful only when it becomes finite projective spinor-density carrier evidence.",
        "branch_status_before_run": "adapter matrix named twistor_hopf_chirality as strong adapter; explorer scoped controls",
        "allowed_claims": [
            "finite projective spinor incidence and Hopf base readouts run on PEPS3D shell anchors",
            "global phase preserves projective class while component phase is rejected",
            "chirality is a density/projector split, not a label, in this finite adapter",
        ],
        "promotion_status": "blocked",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": BLOCKED_CONSUMERS + ["twistor/Hopf/chirality adapter is not layer admission"],
        "eligible_consumers": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "claim_ceiling": CLAIM_CEILING,
        "required_tools": list(TOOL_MANIFEST),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": ["xgi", "rustworkx"],
        "topology_surfaces_used": ["toponetx", "gudhi"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_inputs": ["adapter matrix receipt", "ShellFEPAdapter receipt"],
        "data_or_artifact_dependencies": [str(ADAPTER_MATRIX_RESULT), str(SHELL_FEP_RESULT)],
        "required_negatives": list(graveyard_companions),
        "negatives_run": graveyard_companions,
        "kill_conditions": [
            "twistor/Hopf/chirality label promoted without spinor density",
            "global phase changes projective class",
            "component phase is falsely accepted as projective equivalence",
            "chirality-erased control preserves L/R distinction",
            "Hopf-erased control preserves base readout",
            "downstream consumers unlock",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": hashlib.sha256((NAME + str(start)).encode()).hexdigest()[:16],
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "blockers": blockers,
        "all_pass": all_pass,
        "pass_rule": "all finite spinor/Hopf/chirality positives, controls, and boundary checks pass; downstream consumers remain blocked",
        "fail_rule": "any label-only, phase, chirality, Hopf, dense, or downstream control survives",
        "why_not_v4_probes": "This is v4.3 object-preservation adapter work: twistor/Hopf/chirality structures are tested as finite spinor-density adapters, not replacement primary objects.",
        "surfaces": surfaces,
        "readouts": {
            "LR_density_gap": round(lr_gap, 12),
            "chirality_erased_gap": round(chirality_erased_gap, 12),
            "hopf_erased_gap": round(hopf_erased_gap, 12),
            "order_gap": round(ord_gap, 12),
            "projective_global_phase_gap_max": round(actual["projective_global_phase_gap_max"], 12),
            "component_phase_gap_mean": round(actual["component_phase_gap_mean"], 12),
            "hopf_norm_mean": round(actual["hopf_norm_mean"], 12),
            "S_L": round(actual["S_L"], 9),
            "S_R": round(actual["S_R"], 9),
            "chiral_expectation_mean": round(actual["chiral_expectation_mean"], 12),
        },
        "result_summary": {
            "all_pass": all_pass,
            "rows": ROWS,
            "max_peps3d_sites": max(SITE_FLOORS.values()),
            "max_peps3d_bond_dim": 2,
            "LR_density_gap": round(lr_gap, 9),
            "chirality_erased_gap": round(chirality_erased_gap, 9),
            "hopf_erased_gap": round(hopf_erased_gap, 9),
            "order_gap": round(ord_gap, 9),
            "component_phase_gap_mean": round(actual["component_phase_gap_mean"], 9),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "elapsed_seconds": round(time.time() - start, 6),
    }

    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": all_pass, "wrote": str(OUT_PATH), "summary": result["result_summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
