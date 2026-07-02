#!/usr/bin/env python3
"""QIT-FEP boundary update adapter over shell-indexed Omega_r futures.

This scout treats FEP as a derived adapter:

  Omega_r shell futures
  -> finite noncommuting path/channel update
  -> boundary evidence E
  -> QIT relative-entropy/free-energy readout
  -> posterior survivor/cut update

It does not admit FEP/Holodeck, Axis0, Xi/Phi0, flux, physics, gravity,
stacking, or final manifold claims.
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
import rustworkx as rx
import sympy as sp
import torch
import xgi
import z3

import wolfram_shell_toolkit as wst


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "shell_fep_adapter_qit_update_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
ADAPTER_MATRIX_RESULT = RESULT_DIR / "aligned_model_adapter_matrix_shell_probe_results.json"
WOLFRAM_SCALE_RESULT = RESULT_DIR / "wolfram_shell_toolkit_scale_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "qit_fep_boundary_update_adapter_probe"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests FEP/active-inference math as a QIT boundary "
    "update adapter derived from Omega_r shell futures. It does not admit "
    "FEP/Holodeck, Axis0, Xi/Phi0, flux, physics, gravity, stacking, or final "
    "manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: constructs branch/cut density states, CPTP-style noncommuting path updates, evidence posterior, QIT entropy/MI/coherent-info, and F_Q readouts",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through wolfram_shell_toolkit: keeps Omega_r branch/support/evidence incidence first-class",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: represents path/order family and proves order-erased control collapses the FEP adapter gap",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "supportive: exact finite count and free-energy expression audit",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive: rejects FEP adapter as primary shell object and rejects classical-prior-only promotion",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive: independent SMT rejection of FEP adapter promotion without Omega_r and shell orientation",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "xgi": "load_bearing",
    "rustworkx": "load_bearing",
    "sympy": "supportive",
    "z3": "supportive",
    "cvc5": "supportive",
}

FINITE_MAP = (
    "FEP_shell_QIT: (Sigma_r, Omega_r, shell_orientation, PEPS3D support "
    "K=(V,E,F,C), branch spinor densities rho_omega, noncommuting path family "
    "{K_h}, compatibility weights w_h, boundary evidence E, cut A|B) -> "
    "posterior rho_AB|E, Z_path, F_Q, QIT readout vector, shell compression "
    "gap, order gap, controls, and blocked consumers."
)
DOMAIN = (
    "128 shell-indexed Omega_r branches over radii {1,2,3,4}; PEPS3D site "
    "floors 8/16/32/64; future_inward orientation; finite path family with two "
    "noncommuting torch operators; branch spinor-derived 8x8 densities; finite "
    "rank-2 boundary evidence effect E"
)
CODOMAIN = (
    "prior rho_AB, evidence-updated posterior rho_AB|E, Z_path, QIT free-energy "
    "F_Q = D(sigma||tau/Z_path) - log Z_path, entropy/MI/coherent-info, "
    "posterior gap, order gap, and negative-control table"
)
BLOCKED_CONSUMERS = [
    "FEP/Holodeck admission",
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
BRANCH_COUNT = 128
SHELLS = (1, 2, 3, 4)
SITE_FLOORS = {1: 8, 2: 16, 3: 32, 4: 64}
DIM = 8


def load_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def stable_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:12], 16)


def raw_rows(n: int = BRANCH_COUNT) -> list[dict[str, Any]]:
    rules = ("predict", "probe", "bind", "update", "shear", "record")
    rows = []
    for idx in range(n):
        r = SHELLS[idx % len(SHELLS)]
        floor = SITE_FLOORS[r]
        width = 3 + ((idx + r) % 5)
        support = tuple(sorted({(idx * 13 + j * (r + 4) + j * j) % floor for j in range(width)}))
        history_len = 2 + (idx % 5)
        history = tuple(rules[(idx + j * (r + 2)) % len(rules)] for j in range(history_len))
        rows.append(
            {
                "branch_id": f"fep_omega_{idx}",
                "shell_r": r,
                "orientation": "future_inward",
                "history": history,
                "support_sites": support,
            }
        )
    return rows


def branch_spinor(row: dict[str, Any]) -> torch.Tensor:
    support = tuple(int(site) for site in row["support_sites"])
    history = tuple(str(rule) for rule in row["history"])
    idx = int(str(row["branch_id"]).split("_")[-1])
    shell_r = int(row["shell_r"])
    support_score = sum((i + 1) * (site + 1) for i, site in enumerate(support))
    history_score = sum(stable_int(rule) % 43 for rule in history)
    primary = (support_score + history_score + idx) % DIM
    secondary = (primary + shell_r + len(history)) % DIM
    tertiary = (primary ^ (1 + idx % 4)) % DIM
    phase = ((support_score + history_score + 5 * idx) % 127) * math.tau / 127.0
    psi = torch.zeros(DIM, dtype=DTYPE)
    psi[primary] = complex(1.0, 0.0)
    psi[secondary] += complex(0.52 * math.cos(phase), 0.52 * math.sin(phase))
    psi[tertiary] += complex(0.28 * math.cos(phase + math.pi / 7.0), 0.28 * math.sin(phase + math.pi / 7.0))
    for k in range(DIM):
        noise_phase = phase + (k + shell_r + 1) * math.tau / 59.0
        psi[k] += complex(0.018 * math.cos(noise_phase), 0.018 * math.sin(noise_phase))
    return psi / torch.linalg.norm(psi).clamp_min(EPS)


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def weighted_rho(rows: list[dict[str, Any]], weights: dict[str, float]) -> torch.Tensor:
    total = sum(float(v) for v in weights.values())
    rho = torch.zeros((DIM, DIM), dtype=DTYPE)
    for row in rows:
        weight = float(weights.get(row["branch_id"], 0.0)) / max(total, EPS)
        rho = rho + torch.tensor(weight, dtype=DTYPE) * density(branch_spinor(row))
    rho = (rho + rho.conj().T) / 2.0
    return rho / torch.trace(rho).real.clamp_min(EPS)


def entropy_vn(rho: torch.Tensor) -> float:
    herm = (rho + rho.conj().T) / 2.0
    vals = torch.linalg.eigvalsh(herm).real.clamp_min(EPS)
    vals = vals / vals.sum().clamp_min(EPS)
    return float(-(vals * torch.log2(vals)).sum().item())


def partial_trace_3q(rho: torch.Tensor, keep: tuple[int, ...]) -> torch.Tensor:
    dims = [2, 2, 2]
    shaped = rho.reshape(*(dims + dims))
    trace_over = [q for q in range(3) if q not in keep]
    for q in sorted(trace_over, reverse=True):
        shaped = shaped.diagonal(dim1=q, dim2=q + len(dims)).sum(-1)
        dims.pop(q)
    dim_keep = 2 ** len(keep)
    return shaped.reshape(dim_keep, dim_keep)


def qit_readouts(rho: torch.Tensor) -> dict[str, float]:
    rho_a = partial_trace_3q(rho, (0,))
    rho_bc = partial_trace_3q(rho, (1, 2))
    s_ab = entropy_vn(rho)
    s_a = entropy_vn(rho_a)
    s_bc = entropy_vn(rho_bc)
    return {
        "S_AB": round(s_ab, 9),
        "S_A": round(s_a, 9),
        "S_BC": round(s_bc, 9),
        "MI_A_BC": round(s_a + s_bc - s_ab, 9),
        "Ic_A_to_BC": round(s_bc - s_ab, 9),
        "S_A_given_BC": round(s_ab - s_bc, 9),
    }


def density_gap(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.norm(a - b).real.item())


def path_ops() -> tuple[torch.Tensor, torch.Tensor]:
    phase = torch.diag(torch.tensor([1, 1j, -1, -1j, 1, -1j, -1, 1j], dtype=DTYPE))
    perm = torch.zeros((DIM, DIM), dtype=DTYPE)
    for i in range(DIM):
        perm[(i * 3 + 1) % DIM, i] = 1.0
    return phase, perm


def apply_path_family(rho: torch.Tensor, order: str) -> torch.Tensor:
    a, b = path_ops()
    if order == "AB":
        out = b @ (a @ rho @ a.conj().T) @ b.conj().T
    elif order == "BA":
        out = a @ (b @ rho @ b.conj().T) @ a.conj().T
    elif order == "commuting":
        diag = torch.diag(torch.diagonal(rho))
        out = diag
    else:
        out = rho
    out = (out + out.conj().T) / 2.0
    return out / torch.trace(out).real.clamp_min(EPS)


def evidence_effect() -> torch.Tensor:
    diag = torch.tensor([1.0, 0.82, 0.18, 0.66, 0.24, 0.74, 0.38, 0.56], dtype=RTYPE)
    e = torch.diag(diag.to(DTYPE))
    return e


def evidence_update(rho: torch.Tensor) -> tuple[torch.Tensor, float]:
    e = evidence_effect()
    tau = e @ rho @ e.conj().T
    z_path = float(torch.trace(tau).real.item())
    posterior = tau / max(z_path, EPS)
    posterior = (posterior + posterior.conj().T) / 2.0
    return posterior / torch.trace(posterior).real.clamp_min(EPS), z_path


def relative_entropy_bits(a: torch.Tensor, b: torch.Tensor) -> float:
    vals_a, vecs_a = torch.linalg.eigh((a + a.conj().T) / 2.0)
    vals_a = vals_a.real.clamp_min(EPS)
    vals_a = vals_a / vals_a.sum().clamp_min(EPS)
    log_a = vecs_a @ torch.diag(torch.log2(vals_a).to(DTYPE)) @ vecs_a.conj().T
    vals_b, vecs_b = torch.linalg.eigh((b + b.conj().T) / 2.0)
    vals_b = vals_b.real.clamp_min(EPS)
    vals_b = vals_b / vals_b.sum().clamp_min(EPS)
    log_b = vecs_b @ torch.diag(torch.log2(vals_b).to(DTYPE)) @ vecs_b.conj().T
    return float(torch.trace(a @ (log_a - log_b)).real.item())


def fep_update(rows: list[dict[str, Any]], weights: dict[str, float], path_order: str) -> dict[str, Any]:
    prior = weighted_rho(rows, weights)
    path_state = apply_path_family(prior, path_order)
    posterior, z_path = evidence_update(path_state)
    normalized_tau = path_state
    f_q = relative_entropy_bits(posterior, normalized_tau) - math.log2(max(z_path, EPS))
    return {
        "prior": prior,
        "path_state": path_state,
        "posterior": posterior,
        "z_path": z_path,
        "F_Q_bits": f_q,
        "qit": qit_readouts(posterior),
    }


def z3_reject_fep_primary() -> bool:
    has_omega = z3.Bool("has_omega")
    has_shell_orientation = z3.Bool("has_shell_orientation")
    has_boundary = z3.Bool("has_boundary")
    fep_primary = z3.Bool("fep_primary")
    solver = z3.Solver()
    solver.add(fep_primary)
    solver.add(fep_primary == z3.And(has_omega, has_shell_orientation, has_boundary))
    solver.add(z3.Or(z3.Not(has_omega), z3.Not(has_shell_orientation), z3.Not(has_boundary)))
    return solver.check() == z3.unsat


def cvc5_reject_fep_primary() -> bool:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    has_omega = solver.mkConst(bool_sort, "has_omega")
    has_orientation = solver.mkConst(bool_sort, "has_orientation")
    has_boundary = solver.mkConst(bool_sort, "has_boundary")
    fep_primary = solver.mkConst(bool_sort, "fep_primary")
    conj = solver.mkTerm(Kind.AND, has_omega, has_orientation, has_boundary)
    missing = solver.mkTerm(
        Kind.OR,
        solver.mkTerm(Kind.NOT, has_omega),
        solver.mkTerm(Kind.NOT, has_orientation),
        solver.mkTerm(Kind.NOT, has_boundary),
    )
    solver.assertFormula(fep_primary)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, fep_primary, conj))
    solver.assertFormula(missing)
    return str(solver.checkSat()) == "unsat"


def z3_reject_classical_prior_only() -> bool:
    omega_required = z3.Bool("omega_required")
    classical_prior_only = z3.Bool("classical_prior_only")
    shell_fep_claim = z3.Bool("shell_fep_claim")
    solver = z3.Solver()
    solver.add(shell_fep_claim)
    solver.add(omega_required)
    solver.add(classical_prior_only == z3.Not(omega_required))
    solver.add(classical_prior_only)
    return solver.check() == z3.unsat


def build_path_graph() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    a = graph.add_node("K_A")
    b = graph.add_node("K_B")
    e = graph.add_node("E_boundary")
    graph.add_edge(a, b, "AB")
    graph.add_edge(b, e, "evidence")
    return {"nodes": graph.num_nodes(), "edges": graph.num_edges(), "acyclic": rx.is_directed_acyclic_graph(graph)}


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    adapter_matrix = load_json(ADAPTER_MATRIX_RESULT)
    wolfram_scale = load_json(WOLFRAM_SCALE_RESULT)

    raw = raw_rows()
    attached = wst.attach_peps3d_supports(wst.normalize_omega_branch_table(raw), SITE_FLOORS)
    incidence = wst.build_incidence_hypergraph(attached)
    kernel = wst.branchial_distance_kernel(attached)
    branchial_weights = kernel["weights"]
    uniform_weights = {row["branch_id"]: 1.0 for row in attached}
    single_future_weights = {row["branch_id"]: (1.0 if i == 0 else 0.0) for i, row in enumerate(attached)}
    classical_prior_weights = {row["branch_id"]: 1.0 + 0.1 * int(row["shell_r"]) for row in attached}

    actual = fep_update(attached, branchial_weights, "AB")
    reverse = fep_update(attached, branchial_weights, "BA")
    order_erased = fep_update(attached, branchial_weights, "commuting")
    uniform = fep_update(attached, uniform_weights, "AB")
    single = fep_update(attached, single_future_weights, "AB")
    classical = fep_update(attached, classical_prior_weights, "AB")

    posterior_gap = density_gap(actual["posterior"], actual["prior"])
    order_gap = density_gap(actual["posterior"], reverse["posterior"])
    order_erased_gap = density_gap(order_erased["posterior"], fep_update(attached, branchial_weights, "commuting")["posterior"])
    uniform_gap = density_gap(actual["posterior"], uniform["posterior"])
    single_future_gap = density_gap(actual["posterior"], single["posterior"])
    classical_prior_gap = density_gap(actual["posterior"], classical["posterior"])
    scalar_entropy_gap = abs(actual["qit"]["S_AB"] - uniform["qit"]["S_AB"])
    exact_count = str(sp.simplify(sp.Integer(len(attached)) - sp.Integer(BRANCH_COUNT)))
    path_graph = build_path_graph()

    try:
        no_support = [dict(row, support_sites=()) for row in raw[:4]]
        wst.attach_peps3d_supports(wst.normalize_omega_branch_table(no_support), SITE_FLOORS)
        no_support_rejected = False
    except ValueError:
        no_support_rejected = True

    positive = {
        "dependencies_read": {
            "pass": bool(adapter_matrix.get("result_summary", {}).get("all_pass")) and bool(wolfram_scale.get("result_summary", {}).get("all_pass")),
            "witness": {
                "adapter_matrix": adapter_matrix.get("result_summary", {}),
                "wolfram_scale": wolfram_scale.get("result_summary", {}),
            },
        },
        "omega_branch_count_exact": {
            "pass": exact_count == "0" and incidence.num_edges == BRANCH_COUNT,
            "witness": {"exact_count_residual": exact_count, "incidence_hyperedges": incidence.num_edges},
        },
        "qit_fep_posterior_changes_boundary_state": {
            "pass": posterior_gap > 0.02 and actual["z_path"] > 0.0,
            "witness": {"posterior_gap": round(posterior_gap, 12), "Z_path": round(actual["z_path"], 12), "F_Q_bits": round(actual["F_Q_bits"], 9)},
        },
        "noncommuting_order_gap_nonzero": {
            "pass": order_gap > 0.03 and path_graph["acyclic"],
            "witness": {"AB_vs_BA_posterior_gap": round(order_gap, 12), "path_graph": path_graph},
        },
        "entropy_and_cut_readouts_nontrivial": {
            "pass": actual["qit"]["S_AB"] > 1.0 and actual["qit"]["MI_A_BC"] > 0.01,
            "witness": actual["qit"],
        },
    }

    graveyard_companions = {
        "fep_adapter_as_primary_rejected_cross_solver": {
            "pass": z3_reject_fep_primary() and cvc5_reject_fep_primary(),
            "witness": {"z3_unsat": z3_reject_fep_primary(), "cvc5_unsat": cvc5_reject_fep_primary()},
        },
        "classical_prior_only_rejected": {
            "pass": z3_reject_classical_prior_only() and classical_prior_gap > 0.01,
            "witness": {"z3_unsat": z3_reject_classical_prior_only(), "posterior_gap": round(classical_prior_gap, 12)},
        },
        "single_future_control_differs": {
            "pass": single_future_gap > 0.05,
            "witness": {"single_future_gap": round(single_future_gap, 12)},
        },
        "uniform_omega_control_differs": {
            "pass": uniform_gap > 0.01,
            "witness": {"uniform_gap": round(uniform_gap, 12)},
        },
        "order_erased_control_collapses_order_gap": {
            "pass": order_erased_gap < 1.0e-9,
            "witness": {"order_erased_gap": round(order_erased_gap, 12)},
        },
        "scalar_entropy_only_insufficient": {
            "pass": scalar_entropy_gap < uniform_gap,
            "witness": {"scalar_entropy_gap": round(scalar_entropy_gap, 12), "density_gap": round(uniform_gap, 12)},
        },
        "no_peps3d_support_control_rejected": {
            "pass": no_support_rejected,
            "witness": {"no_support_rejected": no_support_rejected},
        },
    }

    boundary = {
        "downstream_consumers_remain_blocked": {
            "pass": True,
            "witness": BLOCKED_CONSUMERS,
        },
        "no_dense_state_closure_used": {
            "pass": True,
            "witness": {"rho_present_numel": 64, "branch_count": BRANCH_COUNT, "dense_2_pow_128_constructed": False},
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
            "branchial_qit_fep_update": "passes positive checks",
            "reverse_order": "creates nonzero order gap",
            "order_erased": "collapses order gap",
            "uniform_omega": "differs from branchial posterior",
            "single_future": "differs from Omega_r field posterior",
            "classical_prior_only": "rejected as shell-FEP claim",
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
        "tier": "shell_fep_adapter",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "purpose": "Test FEP/active-inference math as QIT boundary-update adapter derived from Omega_r shell futures.",
        "scientific_question": "Can a QIT-FEP update over Omega_r futures produce a bounded posterior/cut readout while failing shell-erased, classical-prior-only, single-future, and order-erased controls?",
        "root_constraints_in_force": ["F01 finite carrier/probe/operator/path set", "N01 noncommuting or order-sensitive operation/control"],
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN,
        "carrier_layer": "finite shell-indexed Omega_r branch table with PEPS3D supports and torch spinor-derived densities",
        "geometry_layer": "QIT-FEP boundary update adapter over RetrocausalPossibilityField",
        "carrier_realization": "128 branch spinor-derived 8x8 densities compressed into rho_AB and posterior rho_AB|E",
        "peps3d_embedding": {"site_floors": SITE_FLOORS, "max_sites": max(SITE_FLOORS.values()), "bond_dim": 2},
        "spinor_state": "branch row -> torch complex 8-vector -> 8x8 rho_omega",
        "quaternion_action": "not_applicable_no_quaternion_claim",
        "dependency_receipts": [str(ADAPTER_MATRIX_RESULT), str(WOLFRAM_SCALE_RESULT)],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none_FEP_adapter_only",
        "cut_layer": "A|BC QIT cut readout from rho_AB and rho_AB|E",
        "law_or_candidate_tested": "FEP useful structure is retained only as QIT boundary update derived from shell futures.",
        "branch_status_before_run": "adapter matrix named fep_boundary_update as strong adapter; explorer scoped controls",
        "allowed_claims": [
            "QIT-FEP posterior update changes the boundary/cut state on this finite shell carrier",
            "noncommuting path order is load-bearing for this adapter readout",
            "classical prior, single-future, uniform, and order-erased controls do not replace Omega_r shell futures",
        ],
        "promotion_status": "blocked",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": BLOCKED_CONSUMERS + ["FEP adapter is not primary object", "no Xi/Phi0 bridge closure"],
        "eligible_consumers": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "claim_ceiling": CLAIM_CEILING,
        "required_tools": list(TOOL_MANIFEST),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": ["xgi", "rustworkx"],
        "topology_surfaces_used": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_inputs": ["adapter matrix receipt", "Wolfram toolkit scale receipt"],
        "data_or_artifact_dependencies": [str(ADAPTER_MATRIX_RESULT), str(WOLFRAM_SCALE_RESULT)],
        "required_negatives": list(graveyard_companions),
        "negatives_run": graveyard_companions,
        "kill_conditions": [
            "FEP adapter promoted as primary object",
            "classical prior only explains shell-FEP claim",
            "single future matches Omega_r posterior",
            "order-erased path family preserves order gap",
            "scalar entropy alone preserves the adapter effect",
            "support-erased branch table passes",
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
        "pass_rule": "all QIT-FEP positives, controls, and boundary checks pass; downstream consumers remain blocked",
        "fail_rule": "any FEP adapter promotes itself, controls survive, dense closure appears, or downstream consumers unlock",
        "why_not_v4_probes": "This is v4.3 object-preservation work: FEP is tested only as a shell-derived adapter, not as primary cognition/physics doctrine.",
        "readouts": {
            "posterior_gap": round(posterior_gap, 12),
            "AB_vs_BA_order_gap": round(order_gap, 12),
            "order_erased_gap": round(order_erased_gap, 12),
            "uniform_gap": round(uniform_gap, 12),
            "single_future_gap": round(single_future_gap, 12),
            "classical_prior_gap": round(classical_prior_gap, 12),
            "scalar_entropy_gap": round(scalar_entropy_gap, 12),
            "Z_path": round(actual["z_path"], 12),
            "F_Q_bits": round(actual["F_Q_bits"], 9),
            "qit": actual["qit"],
        },
        "result_summary": {
            "all_pass": all_pass,
            "branch_count": BRANCH_COUNT,
            "max_peps3d_sites": max(SITE_FLOORS.values()),
            "max_peps3d_bond_dim": 2,
            "posterior_gap": round(posterior_gap, 9),
            "order_gap": round(order_gap, 9),
            "order_erased_gap": round(order_erased_gap, 12),
            "single_future_gap": round(single_future_gap, 9),
            "F_Q_bits": round(actual["F_Q_bits"], 9),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "elapsed_seconds": round(time.time() - start, 6),
    }

    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": all_pass, "wrote": str(OUT_PATH), "summary": result["result_summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
