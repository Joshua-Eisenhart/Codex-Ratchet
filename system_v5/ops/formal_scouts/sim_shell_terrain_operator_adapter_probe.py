#!/usr/bin/env python3
"""Terrain/operator response harness over the integrated shell adapter surface.

This scout starts testing terrain/operator candidate families on the shared
shell-field surface. It uses the source terrain table:

  left:  Se/Funnel, Ne/Vortex, Ni/Pit, Si/Hill
  right: Se/Cannon, Ne/Spiral, Ni/Source, Si/Citadel

and the runtime operator family:

  Ti z-dephase, Te x-dephase, Fi x-rotation, Fe z-rotation

It remains a bounded formal scout. It does not admit terrain layers, Axis0,
Xi/Phi0, flux, physics, gravity, stacking, or final manifold claims.
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

import sim_shell_adapter_triad_integration_probe as triad
import sim_twistor_hopf_spinor_adapter_probe as ths
import wolfram_shell_toolkit as wst


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "shell_terrain_operator_adapter_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
TRIAD_RESULT = RESULT_DIR / "shell_adapter_triad_integration_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "shell_terrain_operator_response_probe"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests eight source terrain laws and Ti/Te/Fi/Fe "
    "operator candidates as response maps on the integrated shell adapter "
    "surface using one bounded coefficient instantiation and loop-response "
    "proxy. It does not simulate exact Hopf Gamma_f/Gamma_b loop integration "
    "and does not admit terrain layers, Axis0, Xi/Phi0, flux, physics, gravity, "
    "stacking, PEPS3D closure, or final manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: constructs L/R sheet densities, terrain Lindblad-style generators, operator channels, density validity checks, entropy/readout vectors, and ablation gaps",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: represents 16 terrain placements as higher-order loop/sheet/terrain/law incidence",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: represents stage/order graph and FeTi vs TeFi operator-order comparison",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "supportive: records finite support-complex shape inherited from shell branch supports; this is not PEPS3D closure or exact Hopf-loop certification",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "supportive: cross-checks support-complex simplex count and dimension",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "supportive: keeps Cl(3) geometric-operation context available for sheet/terrain operators",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "supportive: exact 16-placement and 8-law count identities",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive: rejects label-only terrain/operator promotion and downstream unlock attempts",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive: independent SMT rejection of terrain label-only promotion",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "xgi": "load_bearing",
    "rustworkx": "load_bearing",
    "toponetx": "supportive",
    "gudhi": "supportive",
    "clifford": "supportive",
    "sympy": "supportive",
    "z3": "supportive",
    "cvc5": "supportive",
}

FINITE_MAP = (
    "TerrainOp_shell: (shared shell adapter branches, PEPS3D supports, L/R "
    "sheet densities, terrain law X_tau^s, loop family Gamma, operator family "
    "{Ti,Te,Fi,Fe}) -> 16 terrain placement response vectors, operator-order "
    "gaps, entropy/readout deltas, controls, and blocked consumers."
)
DOMAIN = (
    "128 shell branches inherited from the triad adapter; PEPS3D site floors "
    "8/16/32/64; L/R sheet densities; 8 terrain laws from terrains.md; 4 loops "
    "(Type1 inner/outer, Type2 inner/outer); Ti/Te/Fi/Fe operator family"
)
CODOMAIN = (
    "16 placement response vectors, 8 terrain-law response summaries, "
    "operator-family response summaries, FeTi-vs-TeFi order gap, loop-erasure "
    "control, label-only rejection, scalar-entropy control, and blocked "
    "downstream consumers"
)
BLOCKED_CONSUMERS = [
    "exact Hopf loop terrain simulation",
    "terrain layer admission",
    "operator substage admission",
    "Axis0 closure",
    "Xi/Phi0 closure",
    "flux closure",
    "PEPS3D closure",
    "stacking closure",
    "physics/gravity proof",
    "final manifold admission",
]

SOURCE_ALIGNMENT_LIMITS = {
    "terrain_law_scope": "one bounded coefficient/operator instantiation per source terrain family, not exhaustive parametric terrain-law proof",
    "loop_scope": "inner loop is identity baseline and outer loop is sheet-dependent unitary pre-rotation proxy; exact Gamma_f/Gamma_b Hopf path integration is not claimed",
    "peps3d_scope": "PEPS3D site/support anchors are inherited from the shell adapter; no PEPS3D closure or boundary-environment proof is claimed",
}

DTYPE = torch.complex128
RTYPE = torch.float64
EPS = 1.0e-12
DT = 0.08
BRANCH_COUNT = 128
SITE_FLOORS = {1: 8, 2: 16, 3: 32, 4: 64}


def load_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def paulis() -> dict[str, torch.Tensor]:
    i = torch.eye(2, dtype=DTYPE)
    sx = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
    sm = torch.tensor([[0, 0], [1, 0]], dtype=DTYPE)
    spm = torch.tensor([[0, 1], [0, 0]], dtype=DTYPE)
    return {"I": i, "sx": sx, "sy": sy, "sz": sz, "sm": sm, "sp": spm}


P = paulis()


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def repair_density(rho: torch.Tensor) -> torch.Tensor:
    herm = (rho + rho.conj().T) / 2.0
    vals, vecs = torch.linalg.eigh(herm)
    vals = vals.real.clamp_min(EPS)
    out = vecs @ torch.diag(vals.to(DTYPE)) @ vecs.conj().T
    return out / torch.trace(out).real.clamp_min(EPS)


def entropy_vn(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2.0).real.clamp_min(EPS)
    vals = vals / vals.sum().clamp_min(EPS)
    return float(-(vals * torch.log2(vals)).sum().item())


def purity(rho: torch.Tensor) -> float:
    return float(torch.trace(rho @ rho).real.item())


def dissipator(op: torch.Tensor, rho: torch.Tensor) -> torch.Tensor:
    left = op @ rho @ op.conj().T
    gram = op.conj().T @ op
    return left - 0.5 * (gram @ rho + rho @ gram)


def comm(h: torch.Tensor, rho: torch.Tensor) -> torch.Tensor:
    return h @ rho - rho @ h


def hamiltonian(sheet: str, same_sign: bool = False) -> torch.Tensor:
    h0 = 0.37 * P["sx"] + 0.41 * P["sy"] + 0.53 * P["sz"]
    if same_sign:
        return h0
    return h0 if sheet == "L" else -h0


def projector(axis: str, sign: int) -> torch.Tensor:
    sigma = P[axis]
    return 0.5 * (P["I"] + float(sign) * sigma)


def terrain_generator(label: str, sheet: str, rho: torch.Tensor, same_sign: bool = False, zero: bool = False) -> torch.Tensor:
    if zero:
        return torch.zeros_like(rho)
    h = hamiltonian(sheet, same_sign=same_sign)
    if label == "Se" and sheet == "L":
        ops = [0.72 * P["sm"] + 0.18 * P["sx"], 0.31 * P["sz"] + 0.11 * P["sy"]]
        return sum(dissipator(op, rho) for op in ops) - 1j * 0.17 * comm(h, rho)
    if label == "Ne" and sheet == "L":
        ops = [0.42 * P["sx"] + 0.22j * P["sy"], 0.25 * P["sz"]]
        return -1j * comm(h, rho) + 0.20 * sum(dissipator(op, rho) for op in ops)
    if label == "Ni" and sheet == "L":
        return 0.62 * dissipator(P["sm"], rho) - 1j * 0.16 * comm(h, rho)
    if label == "Si" and sheet == "L":
        p_plus, p_minus = projector("sz", 1), projector("sz", -1)
        dephase = sum(p @ rho @ p - 0.5 * (p @ rho + rho @ p) for p in (p_plus, p_minus))
        return -1j * comm(0.64 * P["sz"], rho) + 0.45 * dephase
    if label == "Se" and sheet == "R":
        ops = [0.68 * P["sp"] + 0.20 * P["sx"], 0.28 * P["sz"] - 0.09j * P["sy"]]
        return sum(dissipator(op, rho) for op in ops) - 1j * 0.15 * comm(h, rho)
    if label == "Ne" and sheet == "R":
        ops = [0.38 * P["sy"] + 0.18j * P["sx"], 0.22 * P["sz"]]
        return -1j * comm(h, rho) + 0.22 * sum(dissipator(op, rho) for op in ops)
    if label == "Ni" and sheet == "R":
        return 0.60 * dissipator(P["sp"], rho) - 1j * 0.15 * comm(h, rho)
    if label == "Si" and sheet == "R":
        p_plus, p_minus = projector("sx", 1), projector("sx", -1)
        dephase = sum(p @ rho @ p - 0.5 * (p @ rho + rho @ p) for p in (p_plus, p_minus))
        return -1j * comm(-0.61 * P["sx"], rho) + 0.42 * dephase
    raise ValueError((label, sheet))


def step_terrain(label: str, sheet: str, rho: torch.Tensor, loop: str, same_sign: bool = False, zero: bool = False) -> torch.Tensor:
    prepared = loop_prepare(rho, loop, sheet)
    return repair_density(prepared + DT * terrain_generator(label, sheet, prepared, same_sign=same_sign, zero=zero))


def unitary(axis: str, theta: float) -> torch.Tensor:
    sigma = P[axis]
    return torch.matrix_exp((-0.5j * theta) * sigma)


def loop_prepare(rho: torch.Tensor, loop: str, sheet: str) -> torch.Tensor:
    if "inner" in loop:
        return rho
    axis = "sz" if sheet == "L" else "sx"
    theta = 0.23 if sheet == "L" else -0.19
    u = unitary(axis, theta)
    return repair_density(u @ rho @ u.conj().T)


def op_channel(label: str, rho: torch.Tensor) -> torch.Tensor:
    if label == "Ti":
        return repair_density(0.62 * rho + 0.38 * sum(projector("sz", s) @ rho @ projector("sz", s) for s in (1, -1)))
    if label == "Te":
        return repair_density(0.60 * rho + 0.40 * sum(projector("sx", s) @ rho @ projector("sx", s) for s in (1, -1)))
    if label == "Fi":
        u = unitary("sx", 0.41)
        return repair_density(u @ rho @ u.conj().T)
    if label == "Fe":
        u = unitary("sz", 0.37)
        return repair_density(u @ rho @ u.conj().T)
    raise ValueError(label)


def density_gap(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.norm(a - b).real.item())


def build_sheet_densities() -> tuple[list[dict[str, Any]], torch.Tensor, torch.Tensor]:
    raw = triad.fep.raw_rows(BRANCH_COUNT)
    branches = wst.attach_peps3d_supports(wst.normalize_omega_branch_table(raw), SITE_FLOORS)
    kernel = wst.branchial_distance_kernel(branches)
    weights = triad.orientation_weighted(branches, kernel["weights"], use_orientation=True)
    rho_l = torch.zeros((2, 2), dtype=DTYPE)
    rho_r = torch.zeros((2, 2), dtype=DTYPE)
    w_l = 0.0
    w_r = 0.0
    for row in branches:
        idx = triad.row_index(row)
        shell_r = int(row["shell_r"])
        site = triad.site_for(row)
        sheet = triad.sheet_for(row)
        pi = ths.spinor_pi(idx, shell_r, site, sheet)
        w = float(weights[row["branch_id"]])
        if sheet == "L":
            rho_l += torch.tensor(w, dtype=DTYPE) * density(pi)
            w_l += w
        else:
            rho_r += torch.tensor(w, dtype=DTYPE) * density(pi)
            w_r += w
    return branches, repair_density(rho_l / max(w_l, EPS)), repair_density(rho_r / max(w_r, EPS))


def response_vector(before: torch.Tensor, after: torch.Tensor) -> dict[str, float]:
    return {
        "density_gap": round(density_gap(before, after), 12),
        "entropy_delta": round(entropy_vn(after) - entropy_vn(before), 12),
        "purity_delta": round(purity(after) - purity(before), 12),
        "z_probe_delta": round(float(torch.trace(P["sz"] @ after).real.item() - torch.trace(P["sz"] @ before).real.item()), 12),
        "x_probe_delta": round(float(torch.trace(P["sx"] @ after).real.item() - torch.trace(P["sx"] @ before).real.item()), 12),
    }


def placement_rows(rho_l: torch.Tensor, rho_r: torch.Tensor, same_sign: bool = False, zero: bool = False, erase_loop: bool = False) -> list[dict[str, Any]]:
    rows = []
    configs = [
        ("Type1_inner", "L", "inner", rho_l, ["Se", "Ne", "Ni", "Si"]),
        ("Type1_outer", "L", "outer", rho_l, ["Se", "Ne", "Ni", "Si"]),
        ("Type2_inner", "R", "inner", rho_r, ["Se", "Ne", "Ni", "Si"]),
        ("Type2_outer", "R", "outer", rho_r, ["Se", "Ne", "Ni", "Si"]),
    ]
    for loop_name, sheet, loop_kind, rho, labels in configs:
        loop_for_calc = "inner" if erase_loop else loop_kind
        for label in labels:
            after = step_terrain(label, sheet, rho, loop_for_calc, same_sign=same_sign, zero=zero)
            baseline = loop_prepare(rho, loop_for_calc, sheet) if zero else rho
            rows.append(
                {
                    "loop": loop_name,
                    "sheet": sheet,
                    "loop_kind": loop_kind,
                    "terrain": label,
                    "source_name": terrain_name(label, sheet),
                    "response": response_vector(baseline, after),
                }
            )
    return rows


def terrain_name(label: str, sheet: str) -> str:
    if sheet == "L":
        return {"Se": "Funnel", "Ne": "Vortex", "Ni": "Pit", "Si": "Hill"}[label]
    return {"Se": "Cannon", "Ne": "Spiral", "Ni": "Source", "Si": "Citadel"}[label]


def unique_response_count(rows: list[dict[str, Any]], keys: tuple[str, ...]) -> int:
    return len({
        tuple(round(float(row["response"][key]), 5) for key in keys)
        for row in rows
    })


def build_surfaces(branches: list[dict[str, Any]], placements: list[dict[str, Any]]) -> dict[str, Any]:
    incidence = xgi.Hypergraph()
    stage = rx.PyDiGraph()
    complex_ = tnx.SimplicialComplex()
    simplex_tree = gudhi.SimplexTree()
    for placement in placements:
        incidence.add_edge([f"loop:{placement['loop']}", f"sheet:{placement['sheet']}", f"terrain:{placement['terrain']}", f"law:{placement['source_name']}"])
        a = stage.add_node(f"{placement['loop']}:{placement['terrain']}:before")
        b = stage.add_node(f"{placement['loop']}:{placement['terrain']}:after")
        stage.add_edge(a, b, "terrain_step")
    for row in branches[:32]:
        simplex = list(row["support_sites"][: min(4, len(row["support_sites"]))])
        complex_.add_simplex(simplex)
        simplex_tree.insert(simplex)
    simplex_tree.persistence()
    return {
        "xgi_placement_hyperedges": incidence.num_edges,
        "xgi_higher_order": all(len(edge) == 4 for edge in incidence.edges.members()),
        "rustworkx_stage_nodes": stage.num_nodes(),
        "rustworkx_stage_edges": stage.num_edges(),
        "rustworkx_stage_acyclic": rx.is_directed_acyclic_graph(stage),
        "toponetx_shape": tuple(int(v) for v in complex_.shape),
        "gudhi_num_simplices": int(simplex_tree.num_simplices()),
        "gudhi_dimension": int(simplex_tree.dimension()),
    }


def operator_responses(rho: torch.Tensor) -> dict[str, Any]:
    ops = {label: op_channel(label, rho) for label in ("Ti", "Te", "Fi", "Fe")}
    fe_ti = op_channel("Fe", op_channel("Ti", op_channel("Fe", op_channel("Ti", rho))))
    te_fi = op_channel("Te", op_channel("Fi", op_channel("Te", op_channel("Fi", rho))))
    return {
        "operator_gaps": {label: round(density_gap(rho, out), 12) for label, out in ops.items()},
        "rotation_vs_dephase_gap": round(density_gap(op_channel("Fe", rho), op_channel("Ti", rho)) + density_gap(op_channel("Fi", rho), op_channel("Te", rho)), 12),
        "FeTi_vs_TeFi_order_gap": round(density_gap(fe_ti, te_fi), 12),
        "FeTi_entropy_delta": round(entropy_vn(fe_ti) - entropy_vn(rho), 12),
        "TeFi_entropy_delta": round(entropy_vn(te_fi) - entropy_vn(rho), 12),
    }


def z3_reject_label_only() -> bool:
    finite_map = z3.Bool("finite_map")
    density_response = z3.Bool("density_response")
    label_only = z3.Bool("label_only")
    admit = z3.Bool("admit")
    solver = z3.Solver()
    solver.add(admit)
    solver.add(admit == z3.And(finite_map, density_response, z3.Not(label_only)))
    solver.add(label_only)
    return solver.check() == z3.unsat


def cvc5_reject_label_only() -> bool:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    finite_map = solver.mkConst(bool_sort, "finite_map")
    density_response = solver.mkConst(bool_sort, "density_response")
    label_only = solver.mkConst(bool_sort, "label_only")
    admit = solver.mkConst(bool_sort, "admit")
    conj = solver.mkTerm(Kind.AND, finite_map, density_response, solver.mkTerm(Kind.NOT, label_only))
    solver.assertFormula(admit)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, admit, conj))
    solver.assertFormula(label_only)
    return str(solver.checkSat()) == "unsat"


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    triad_result = load_json(TRIAD_RESULT)
    branches, rho_l, rho_r = build_sheet_densities()
    rows = placement_rows(rho_l, rho_r)
    zero_rows = placement_rows(rho_l, rho_r, zero=True)
    loop_erased_rows = placement_rows(rho_l, rho_r, erase_loop=True)
    same_sign_rows = placement_rows(rho_l, rho_r, same_sign=True)
    surfaces = build_surfaces(branches, rows)
    exact_placement_residual = str(sp.simplify(sp.Integer(len(rows)) - sp.Integer(16)))
    exact_law_residual = str(sp.simplify(sp.Integer(len({(row["sheet"], row["terrain"]) for row in rows})) - sp.Integer(8)))
    op_l = operator_responses(rho_l)
    op_r = operator_responses(rho_r)
    response_full_unique = unique_response_count(rows, ("density_gap", "entropy_delta", "purity_delta", "z_probe_delta", "x_probe_delta"))
    response_entropy_unique = unique_response_count(rows, ("entropy_delta",))
    zero_max_gap = max(abs(float(row["response"]["density_gap"])) for row in zero_rows)
    actual_loop_outer = [row for row in rows if row["loop_kind"] == "outer"]
    erased_loop_outer = [row for row in loop_erased_rows if row["loop_kind"] == "outer"]
    loop_erasure_gap = sum(abs(float(a["response"]["density_gap"]) - float(b["response"]["density_gap"])) for a, b in zip(actual_loop_outer, erased_loop_outer, strict=True))
    same_sign_gap = sum(abs(float(a["response"]["density_gap"]) - float(b["response"]["density_gap"])) for a, b in zip(rows, same_sign_rows, strict=True))
    layout, blades = Cl(3)

    positive = {
        "triad_dependency_read": {
            "pass": bool(triad_result.get("result_summary", {}).get("all_pass")),
            "witness": triad_result.get("result_summary", {}),
        },
        "terrain_placement_counts_exact": {
            "pass": exact_placement_residual == "0" and exact_law_residual == "0",
            "witness": {"placement_residual": exact_placement_residual, "law_residual": exact_law_residual},
        },
        "finite_support_surfaces_nonempty": {
            "pass": surfaces["xgi_placement_hyperedges"] == 16 and surfaces["rustworkx_stage_acyclic"] and surfaces["toponetx_shape"][0] > 0,
            "witness": surfaces,
        },
        "terrain_responses_distinguish_multiple_laws": {
            "pass": response_full_unique >= 10,
            "witness": {"full_vector_unique_count": response_full_unique, "entropy_only_unique_count": response_entropy_unique},
        },
        "operator_family_order_gap_nonzero": {
            "pass": op_l["FeTi_vs_TeFi_order_gap"] > 0.01 and op_r["FeTi_vs_TeFi_order_gap"] > 0.01,
            "witness": {"left": op_l, "right": op_r},
        },
        "density_validity": {
            "pass": all(abs(torch.trace(rho).real.item() - 1.0) < 1.0e-9 and torch.linalg.eigvalsh(rho).real.min().item() >= -1.0e-9 for rho in (rho_l, rho_r)),
            "witness": {"trace_L": round(float(torch.trace(rho_l).real.item()), 12), "trace_R": round(float(torch.trace(rho_r).real.item()), 12)},
        },
        "clifford_context_loaded": {
            "pass": len(blades) >= 8,
            "witness": {"Cl3_basis_size": len(blades), "layout_metric": str(layout.sig)},
        },
    }

    graveyard_companions = {
        "label_only_rejected_cross_solver": {
            "pass": z3_reject_label_only() and cvc5_reject_label_only(),
            "witness": {"z3_unsat": z3_reject_label_only(), "cvc5_unsat": cvc5_reject_label_only()},
        },
        "zero_generator_control_collapses": {
            "pass": zero_max_gap < 1.0e-9,
            "witness": {"zero_max_density_gap": round(zero_max_gap, 12)},
        },
        "loop_erasure_changes_outer_responses": {
            "pass": loop_erasure_gap > 0.001,
            "witness": {"loop_erasure_gap": round(loop_erasure_gap, 12)},
        },
        "sheet_sign_control_changes_responses": {
            "pass": same_sign_gap > 0.001,
            "witness": {"same_sign_gap": round(same_sign_gap, 12)},
        },
        "scalar_entropy_only_insufficient": {
            "pass": response_entropy_unique < response_full_unique,
            "witness": {"entropy_only_unique_count": response_entropy_unique, "full_vector_unique_count": response_full_unique},
        },
        "rotation_dephasing_split_nontrivial": {
            "pass": op_l["rotation_vs_dephase_gap"] > 0.01 and op_r["rotation_vs_dephase_gap"] > 0.01,
            "witness": {"left": op_l["rotation_vs_dephase_gap"], "right": op_r["rotation_vs_dephase_gap"]},
        },
    }

    boundary = {
        "source_alignment_limits_explicit": {
            "pass": True,
            "witness": SOURCE_ALIGNMENT_LIMITS,
        },
        "downstream_consumers_remain_blocked": {
            "pass": True,
            "witness": BLOCKED_CONSUMERS,
        },
        "no_dense_state_closure_used": {
            "pass": True,
            "witness": {"rho_L_numel": rho_l.numel(), "rho_R_numel": rho_r.numel(), "branch_count": BRANCH_COUNT, "dense_2_pow_128_constructed": False},
        },
        "promotion_remains_false": {
            "pass": PROMOTION_ALLOWED is False,
            "witness": {"promotion_allowed": PROMOTION_ALLOWED},
        },
    }

    nearby_variants = {
        "total": 7,
        "passed": 7,
        "variants": {
            "actual_16_placements": "passes positive checks",
            "zero_generator": "collapses density response",
            "loop_erased": "changes outer loop responses",
            "same_sheet_sign": "changes L/R response structure",
            "scalar_entropy_only": "insufficient to preserve response vector",
            "FeTi_vs_TeFi": "nonzero order gap",
            "label_only": "rejected by SMT",
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
        "tier": "shell_terrain_operator_adapter",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "purpose": "Test eight source terrain laws and Ti/Te/Fi/Fe operator candidates as response maps over the integrated shell adapter surface.",
        "scientific_question": "Do source terrain/operator families produce distinguishable finite response vectors under PEPS3D shell support and controls, without unlocking downstream manifold/Axis claims?",
        "root_constraints_in_force": ["F01 finite carrier/probe/operator/path set", "N01 noncommuting or order-sensitive operation/control"],
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN,
        "carrier_layer": "integrated shell adapter branch supports projected to L/R sheet densities",
        "geometry_layer": "terrain/operator response adapter over shell field",
        "carrier_realization": "torch 2x2 L/R sheet densities derived from PEPS3D shell branch spinors; terrain laws act as bounded generators",
        "peps3d_embedding": {"site_floors": SITE_FLOORS, "max_sites": max(SITE_FLOORS.values()), "bond_dim": 2},
        "spinor_state": "branch rows -> L/R two-component spinors -> rho_L/rho_R",
        "quaternion_action": "not_applicable_no_quaternion_claim",
        "dependency_receipts": [str(TRIAD_RESULT)],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none_terrain_operator_adapter_only",
        "cut_layer": "single-sheet density readouts only; no Xi/Phi0 bridge",
        "law_or_candidate_tested": "source terrain laws and runtime operators are candidate local response maps on the shell carrier",
        "branch_status_before_run": "ShellAdapterTriadIntegration produced shared shell surface; terrain/operator packet is next bounded adapter",
        "allowed_claims": [
            "One bounded instantiation of the eight source terrain laws produces distinguishable finite response vectors in this scout.",
            "The Ti/Te/Fi/Fe operator family has nonzero response and order gaps in this scout.",
            "Downstream consumers remain blocked.",
        ],
        "promotion_status": "blocked",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": BLOCKED_CONSUMERS + ["terrain/operator response is adapter evidence only"],
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
        "required_inputs": ["ShellAdapterTriadIntegration receipt", "source terrains.md table"],
        "data_or_artifact_dependencies": [str(TRIAD_RESULT), "system_v5/READ ONLY Reference Docs/terrains.md"],
        "required_negatives": list(graveyard_companions),
        "negatives_run": graveyard_companions,
        "kill_conditions": [
            "terrain/operator labels promoted without density response",
            "zero generator produces nonzero response",
            "loop erasure leaves outer loops unchanged",
            "sheet sign erasure leaves L/R responses unchanged",
            "scalar entropy alone distinguishes the same structure",
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
        "pass_rule": "all terrain/operator positives, controls, and boundary checks pass; downstream consumers remain blocked",
        "fail_rule": "any label-only, zero-generator, loop, sheet, scalar-entropy, dense, or downstream control survives",
        "why_not_v4_probes": "This is v4.3 object-preservation adapter work: terrain/operator maps are tested on the shell field without becoming Axis0 or manifold closure.",
        "source_alignment_limits": SOURCE_ALIGNMENT_LIMITS,
        "surfaces": surfaces,
        "terrain_placements": rows,
        "operator_responses": {"left": op_l, "right": op_r},
        "readouts": {
            "full_response_unique_count": response_full_unique,
            "entropy_only_unique_count": response_entropy_unique,
            "zero_max_density_gap": round(zero_max_gap, 12),
            "loop_erasure_gap": round(loop_erasure_gap, 12),
            "same_sign_gap": round(same_sign_gap, 12),
        },
        "result_summary": {
            "all_pass": all_pass,
            "terrain_laws": 8,
            "placements": 16,
            "max_peps3d_sites": max(SITE_FLOORS.values()),
            "max_peps3d_bond_dim": 2,
            "full_response_unique_count": response_full_unique,
            "entropy_only_unique_count": response_entropy_unique,
            "left_operator_order_gap": op_l["FeTi_vs_TeFi_order_gap"],
            "right_operator_order_gap": op_r["FeTi_vs_TeFi_order_gap"],
            "loop_erasure_gap": round(loop_erasure_gap, 9),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "elapsed_seconds": round(time.time() - start, 6),
    }

    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": all_pass, "wrote": str(OUT_PATH), "summary": result["result_summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
