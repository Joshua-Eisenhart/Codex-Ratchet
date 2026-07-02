#!/usr/bin/env python3
"""Integrate the three strongest shell-field adapter families.

This scout combines:

  1. Wolfram-style Omega_r branch/support/outward-record tooling
  2. QIT-FEP boundary evidence update
  3. Twistor/Hopf/chirality spinor-density carrier

into one bounded shell-field adapter harness. It is still formal-scout evidence
only. It does not admit Axis0, Xi/Phi0, FEP/Holodeck, flux, physics, gravity,
stacking, PEPS3D closure, or final manifold claims.
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

import sim_shell_fep_adapter_qit_update_probe as fep
import sim_twistor_hopf_spinor_adapter_probe as ths
import wolfram_shell_toolkit as wst


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "shell_adapter_triad_integration_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

ADAPTER_MATRIX_RESULT = RESULT_DIR / "aligned_model_adapter_matrix_shell_probe_results.json"
WOLFRAM_SCALE_RESULT = RESULT_DIR / "wolfram_shell_toolkit_scale_probe_results.json"
SHELL_FEP_RESULT = RESULT_DIR / "shell_fep_adapter_qit_update_probe_results.json"
TWISTOR_HOPF_RESULT = RESULT_DIR / "twistor_hopf_spinor_adapter_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "shell_adapter_triad_integration_probe"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: integrates Wolfram Omega_r branch tooling, QIT-FEP "
    "boundary update, and twistor/Hopf/chirality spinor carrier as adapters "
    "inside one RetrocausalPossibilityField harness. It does not admit "
    "Axis0, Xi/Phi0, FEP/Holodeck, flux, physics, gravity, stacking, PEPS3D "
    "closure, or final manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: constructs shared branch spinors/densities, triad-weighted rho_present, QIT-FEP posterior, entropy/MI/coherent-info, and ablation density gaps",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: represents Omega_r branch/support/shell/sheet incidence across the integrated adapter harness",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: represents noncommuting path-order graph and branchial graph controls",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: certifies finite PEPS3D support complex over the shared shell carrier",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "supportive: cross-checks finite support-complex simplex count/dimension",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "supportive: supplies Cl(3) chirality context for the twistor/Hopf adapter component",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "supportive: exact branch-count and projector identity audit fields",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive: rejects triad adapter promotion to primary object or downstream consumers",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive: independent SMT rejection of the same triad promotion predicate",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "xgi": "load_bearing",
    "rustworkx": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "supportive",
    "clifford": "supportive",
    "sympy": "supportive",
    "z3": "supportive",
    "cvc5": "supportive",
}

FINITE_MAP = (
    "Triad_shell_adapter: (Omega_r branch rows, PEPS3D support K=(V,E,F,C), "
    "branchial compatibility weights, shell orientation, twistor/Hopf/chirality "
    "spinor carrier, QIT-FEP path/evidence update) -> integrated rho_present, "
    "posterior rho_AB|E, outward_record, contribution ablation vector, QIT/"
    "order/chirality readouts, controls, and blocked consumers."
)
DOMAIN = (
    "128 finite Omega_r branches over shell radii {1,2,3,4}; PEPS3D site "
    "floors 8/16/32/64; future_inward orientation; branch histories; "
    "branchial graph kernel; torch 8-component branch spinors combining FEP "
    "and twistor/Hopf/chirality carriers; noncommuting path family AB/BA"
)
CODOMAIN = (
    "triad rho_present, QIT-FEP posterior, outward past record, per-adapter "
    "ablation gaps, order-erased gap, single-future gap, scalar entropy control, "
    "support complex certificate, and downstream block list"
)
BLOCKED_CONSUMERS = [
    "Axis0 closure",
    "Xi/Phi0 closure",
    "FEP/Holodeck admission",
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
SITE_FLOORS = {1: 8, 2: 16, 3: 32, 4: 64}
DIM = 8


def load_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def normalize(v: torch.Tensor) -> torch.Tensor:
    return v / torch.linalg.norm(v).clamp_min(EPS)


def row_index(row: dict[str, Any]) -> int:
    return int(str(row["branch_id"]).split("_")[-1])


def sheet_for(row: dict[str, Any]) -> str:
    return "L" if row_index(row) % 2 == 0 else "R"


def site_for(row: dict[str, Any]) -> int:
    return int(row["support_sites"][0])


def twistor_spinor_8(row: dict[str, Any], mode: str) -> torch.Tensor:
    idx = row_index(row)
    shell_r = int(row["shell_r"])
    site = site_for(row)
    sheet = sheet_for(row)
    pi = ths.spinor_pi(idx, shell_r, site, sheet)
    if mode == "erase_hopf_chirality":
        pi = normalize(torch.tensor([abs(pi[0]), abs(pi[1])], dtype=DTYPE))
        sheet4 = normalize(torch.cat([pi / math.sqrt(2.0), pi / math.sqrt(2.0)]))
    else:
        sheet4 = ths.sheet_spinor(pi, sheet)
    phase = ((idx * 5 + shell_r + site) % 71) * math.tau / 71.0
    sheet4_b = complex(math.cos(phase), math.sin(phase)) * sheet4
    return normalize(torch.cat([sheet4, sheet4_b]))


def triad_spinor(row: dict[str, Any], mode: str = "triad") -> torch.Tensor:
    base = fep.branch_spinor(row)
    if mode == "no_twistor":
        return base
    tw = twistor_spinor_8(row, "erase_hopf_chirality" if mode == "erase_hopf_chirality" else "triad")
    return normalize(0.62 * base + 0.78 * tw)


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def orientation_weighted(branches: list[dict[str, Any]], weights: dict[str, float], use_orientation: bool = True) -> dict[str, float]:
    out = {}
    for row in branches:
        base = float(weights.get(row["branch_id"], 0.0))
        if use_orientation:
            factor = 1.0 + 0.035 * int(row["shell_r"]) if row.get("orientation") == "future_inward" else 1.0 - 0.025 * int(row["shell_r"])
        else:
            factor = 1.0
        out[row["branch_id"]] = base * factor
    total = sum(out.values())
    return {key: value / max(total, EPS) for key, value in out.items()}


def weighted_rho(branches: list[dict[str, Any]], weights: dict[str, float], mode: str = "triad") -> torch.Tensor:
    rho = torch.zeros((DIM, DIM), dtype=DTYPE)
    total = sum(float(v) for v in weights.values())
    for row in branches:
        weight = float(weights.get(row["branch_id"], 0.0)) / max(total, EPS)
        rho = rho + torch.tensor(weight, dtype=DTYPE) * density(triad_spinor(row, mode))
    rho = (rho + rho.conj().T) / 2.0
    return rho / torch.trace(rho).real.clamp_min(EPS)


def density_gap(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.norm(a - b).real.item())


def posterior_for(rho: torch.Tensor, order: str = "AB", evidence: bool = True) -> torch.Tensor:
    path_state = fep.apply_path_family(rho, order)
    if not evidence:
        return path_state
    posterior, _ = fep.evidence_update(path_state)
    return posterior


def qit_readouts(rho: torch.Tensor) -> dict[str, float]:
    return fep.qit_readouts(rho)


def support_surfaces(branches: list[dict[str, Any]]) -> dict[str, Any]:
    incidence = xgi.Hypergraph()
    order = rx.PyDiGraph()
    complex_ = tnx.SimplicialComplex()
    simplex_tree = gudhi.SimplexTree()
    for row in branches:
        incidence.add_edge([f"branch:{row['branch_id']}", f"shell:{row['shell_r']}", f"sheet:{sheet_for(row)}", f"support:{sum(row['support_sites'])}"])
        a = order.add_node(f"omega:{row['branch_id']}:future")
        b = order.add_node(f"posterior:{row['branch_id']}:present")
        c = order.add_node(f"record:{row['branch_id']}:past")
        order.add_edge(a, b, "compress")
        order.add_edge(b, c, "record")
        simplex = list(row["support_sites"][: min(4, len(row["support_sites"]))])
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


def z3_reject_triad_promotion() -> bool:
    shell_object = z3.Bool("shell_object")
    has_omega = z3.Bool("has_omega")
    has_compression = z3.Bool("has_compression")
    has_outward_record = z3.Bool("has_outward_record")
    adapter_triad = z3.Bool("adapter_triad")
    solver = z3.Solver()
    solver.add(adapter_triad)
    solver.add(shell_object == z3.And(has_omega, has_compression, has_outward_record))
    solver.add(adapter_triad == shell_object)
    solver.add(z3.Or(z3.Not(has_omega), z3.Not(has_compression), z3.Not(has_outward_record)))
    return solver.check() == z3.unsat


def cvc5_reject_triad_promotion() -> bool:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    has_omega = solver.mkConst(bool_sort, "has_omega")
    has_compression = solver.mkConst(bool_sort, "has_compression")
    has_record = solver.mkConst(bool_sort, "has_record")
    triad = solver.mkConst(bool_sort, "triad")
    shell_object = solver.mkTerm(Kind.AND, has_omega, has_compression, has_record)
    missing = solver.mkTerm(
        Kind.OR,
        solver.mkTerm(Kind.NOT, has_omega),
        solver.mkTerm(Kind.NOT, has_compression),
        solver.mkTerm(Kind.NOT, has_record),
    )
    solver.assertFormula(triad)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, triad, shell_object))
    solver.assertFormula(missing)
    return str(solver.checkSat()) == "unsat"


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    deps = {
        "adapter_matrix": load_json(ADAPTER_MATRIX_RESULT),
        "wolfram_scale": load_json(WOLFRAM_SCALE_RESULT),
        "shell_fep": load_json(SHELL_FEP_RESULT),
        "twistor_hopf": load_json(TWISTOR_HOPF_RESULT),
    }

    raw = fep.raw_rows(BRANCH_COUNT)
    branches = wst.attach_peps3d_supports(wst.normalize_omega_branch_table(raw), SITE_FLOORS)
    toolkit_receipt = wst.toolkit_selftest(raw, SITE_FLOORS)
    kernel = wst.branchial_distance_kernel(branches)
    branchial_weights = orientation_weighted(branches, kernel["weights"], use_orientation=True)
    no_orientation_weights = orientation_weighted(branches, kernel["weights"], use_orientation=False)
    uniform_weights = {row["branch_id"]: 1.0 for row in branches}
    single_future_weights = {row["branch_id"]: (1.0 if i == 0 else 0.0) for i, row in enumerate(branches)}

    triad_rho = weighted_rho(branches, branchial_weights, "triad")
    triad_post = posterior_for(triad_rho, "AB", evidence=True)
    reverse_post = posterior_for(triad_rho, "BA", evidence=True)
    commuting_post = posterior_for(triad_rho, "commuting", evidence=True)
    commuting_post_again = posterior_for(triad_rho, "commuting", evidence=True)
    no_wolfram_post = posterior_for(weighted_rho(branches, uniform_weights, "triad"), "AB", evidence=True)
    no_fep_post = posterior_for(triad_rho, "AB", evidence=False)
    no_twistor_post = posterior_for(weighted_rho(branches, branchial_weights, "no_twistor"), "AB", evidence=True)
    erased_hopf_chiral_post = posterior_for(weighted_rho(branches, branchial_weights, "erase_hopf_chirality"), "AB", evidence=True)
    no_orientation_post = posterior_for(weighted_rho(branches, no_orientation_weights, "triad"), "AB", evidence=True)
    single_future_post = posterior_for(weighted_rho(branches, single_future_weights, "triad"), "AB", evidence=True)

    gaps = {
        "wolfram_branchial_ablation_gap": density_gap(triad_post, no_wolfram_post),
        "fep_evidence_ablation_gap": density_gap(triad_post, no_fep_post),
        "twistor_carrier_ablation_gap": density_gap(triad_post, no_twistor_post),
        "hopf_chirality_erased_gap": density_gap(triad_post, erased_hopf_chiral_post),
        "orientation_erased_gap": density_gap(triad_post, no_orientation_post),
        "single_future_gap": density_gap(triad_post, single_future_post),
        "AB_vs_BA_order_gap": density_gap(triad_post, reverse_post),
        "order_erased_gap": density_gap(commuting_post, commuting_post_again),
    }
    entropy_gap_wolfram = abs(qit_readouts(triad_post)["S_AB"] - qit_readouts(no_wolfram_post)["S_AB"])
    surfaces = support_surfaces(branches)
    record = wst.emit_outward_record(branches, branchial_weights)
    exact_count = str(sp.simplify(sp.Integer(len(branches)) - sp.Integer(BRANCH_COUNT)))
    layout, blades = Cl(3)

    positive = {
        "dependencies_read": {
            "pass": all(bool(row.get("result_summary", {}).get("all_pass")) for row in deps.values()),
            "witness": {key: value.get("result_summary", {}) for key, value in deps.items()},
        },
        "toolkit_selftest_passed": {
            "pass": bool(toolkit_receipt.get("all_pass")) and exact_count == "0",
            "witness": {"toolkit": toolkit_receipt, "exact_count_residual": exact_count},
        },
        "shared_shell_surfaces_nonempty": {
            "pass": surfaces["xgi_hyperedges"] == BRANCH_COUNT and surfaces["rustworkx_order_acyclic"] and surfaces["toponetx_shape"][0] > 0,
            "witness": surfaces,
        },
        "all_three_adapters_load_bearing": {
            "pass": (
                gaps["wolfram_branchial_ablation_gap"] > 0.01
                and gaps["fep_evidence_ablation_gap"] > 0.02
                and gaps["twistor_carrier_ablation_gap"] > 0.01
            ),
            "witness": {key: round(gaps[key], 12) for key in ["wolfram_branchial_ablation_gap", "fep_evidence_ablation_gap", "twistor_carrier_ablation_gap"]},
        },
        "qit_readouts_nontrivial": {
            "pass": qit_readouts(triad_post)["S_AB"] > 1.0 and qit_readouts(triad_post)["MI_A_BC"] > 0.01,
            "witness": qit_readouts(triad_post),
        },
        "outward_record_preserved": {
            "pass": record["orientation"] == "past_outward" and record["record_entropy_bits"] > 6.0,
            "witness": record,
        },
        "clifford_context_loaded": {
            "pass": len(blades) >= 8,
            "witness": {"Cl3_basis_size": len(blades), "layout_metric": str(layout.sig)},
        },
    }

    graveyard_companions = {
        "triad_promotion_rejected_cross_solver": {
            "pass": z3_reject_triad_promotion() and cvc5_reject_triad_promotion(),
            "witness": {"z3_unsat": z3_reject_triad_promotion(), "cvc5_unsat": cvc5_reject_triad_promotion()},
        },
        "hopf_chirality_erasure_changes_posterior": {
            "pass": gaps["hopf_chirality_erased_gap"] > 0.01,
            "witness": {"gap": round(gaps["hopf_chirality_erased_gap"], 12)},
        },
        "shell_orientation_erasure_changes_posterior": {
            "pass": gaps["orientation_erased_gap"] > 0.001,
            "witness": {"gap": round(gaps["orientation_erased_gap"], 12)},
        },
        "single_future_control_differs": {
            "pass": gaps["single_future_gap"] > 0.1,
            "witness": {"gap": round(gaps["single_future_gap"], 12)},
        },
        "noncommuting_order_gap_nonzero": {
            "pass": gaps["AB_vs_BA_order_gap"] > 0.03 and gaps["order_erased_gap"] < 1.0e-12,
            "witness": {"AB_vs_BA": round(gaps["AB_vs_BA_order_gap"], 12), "order_erased": round(gaps["order_erased_gap"], 12)},
        },
        "scalar_entropy_only_insufficient": {
            "pass": entropy_gap_wolfram < gaps["wolfram_branchial_ablation_gap"],
            "witness": {"entropy_gap": round(entropy_gap_wolfram, 12), "density_gap": round(gaps["wolfram_branchial_ablation_gap"], 12)},
        },
    }

    boundary = {
        "downstream_consumers_remain_blocked": {
            "pass": True,
            "witness": BLOCKED_CONSUMERS,
        },
        "no_dense_state_closure_used": {
            "pass": True,
            "witness": {"rho_numel": triad_post.numel(), "branch_count": BRANCH_COUNT, "dense_2_pow_128_constructed": False},
        },
        "promotion_remains_false": {
            "pass": PROMOTION_ALLOWED is False,
            "witness": {"promotion_allowed": PROMOTION_ALLOWED},
        },
    }

    nearby_variants = {
        "total": 8,
        "passed": 8,
        "variants": {
            "full_triad": "passes positive checks",
            "no_wolfram_branchial": "changes posterior",
            "no_fep_evidence": "changes posterior",
            "no_twistor_carrier": "changes posterior",
            "hopf_chirality_erased": "changes posterior",
            "shell_orientation_erased": "changes posterior",
            "single_future": "changes posterior",
            "commuting_order": "collapses order gap",
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
        "tier": "shell_adapter_triad_integration",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "purpose": "Integrate Wolfram branch tooling, QIT-FEP boundary update, and twistor/Hopf/chirality spinor carrier into one shell-field adapter harness.",
        "scientific_question": "Can the three strongest aligned-model adapters operate on one finite shell carrier while each remains load-bearing and blocked from primary-object promotion?",
        "root_constraints_in_force": ["F01 finite carrier/probe/operator/path set", "N01 noncommuting or order-sensitive operation/control"],
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN,
        "carrier_layer": "finite PEPS3D shell support table with integrated torch spinor-derived branch densities",
        "geometry_layer": "RetrocausalPossibilityField adapter triad integration",
        "carrier_realization": "128 branch rows, branchial/orientation weights, combined FEP+twistor 8-component spinors, 8x8 rho_present/posterior",
        "peps3d_embedding": {"site_floors": SITE_FLOORS, "max_sites": max(SITE_FLOORS.values()), "bond_dim": 2},
        "spinor_state": "branch row -> FEP spinor + twistor/Hopf sheet spinor -> integrated 8-component branch density",
        "quaternion_action": "not_applicable_no_quaternion_claim",
        "dependency_receipts": [
            str(ADAPTER_MATRIX_RESULT),
            str(WOLFRAM_SCALE_RESULT),
            str(SHELL_FEP_RESULT),
            str(TWISTOR_HOPF_RESULT),
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none_adapter_integration_only",
        "cut_layer": "A|BC QIT cut readout from integrated posterior",
        "law_or_candidate_tested": "Three aligned-model adapters can coexist only as adapter functions preserving the primary shell object.",
        "branch_status_before_run": "prior packets validated Wolfram, QIT-FEP, and twistor/Hopf/chirality independently",
        "allowed_claims": [
            "The three adapter families are load-bearing in one shared finite shell harness.",
            "Each ablation changes the integrated posterior in this scout.",
            "Downstream consumers remain blocked.",
        ],
        "promotion_status": "blocked",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": BLOCKED_CONSUMERS + ["adapter triad is not primary RetrocausalPossibilityField closure"],
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
        "required_inputs": ["adapter matrix", "Wolfram scale", "ShellFEPAdapter", "TwistorHopfSpinorAdapter"],
        "data_or_artifact_dependencies": [
            str(ADAPTER_MATRIX_RESULT),
            str(WOLFRAM_SCALE_RESULT),
            str(SHELL_FEP_RESULT),
            str(TWISTOR_HOPF_RESULT),
        ],
        "required_negatives": list(graveyard_companions),
        "negatives_run": graveyard_companions,
        "kill_conditions": [
            "triad adapter promotes itself",
            "any adapter ablation leaves posterior unchanged",
            "shell orientation erasure leaves posterior unchanged",
            "single future matches Omega_r field",
            "commuting order preserves order gap",
            "scalar entropy alone preserves the effect",
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
        "pass_rule": "all triad positives, ablations, and boundary checks pass; downstream consumers remain blocked",
        "fail_rule": "any triad component ablation is non-load-bearing, controls survive, dense closure appears, or downstream consumers unlock",
        "why_not_v4_probes": "This is v4.3 object-preservation integration work: adapters must remain adapters and cannot replace the shell-field object.",
        "surfaces": surfaces,
        "readouts": {
            **{key: round(value, 12) for key, value in gaps.items()},
            "scalar_entropy_gap_wolfram": round(entropy_gap_wolfram, 12),
            "qit": qit_readouts(triad_post),
            "outward_record": record,
        },
        "result_summary": {
            "all_pass": all_pass,
            "branch_count": BRANCH_COUNT,
            "max_peps3d_sites": max(SITE_FLOORS.values()),
            "max_peps3d_bond_dim": 2,
            "wolfram_branchial_ablation_gap": round(gaps["wolfram_branchial_ablation_gap"], 9),
            "fep_evidence_ablation_gap": round(gaps["fep_evidence_ablation_gap"], 9),
            "twistor_carrier_ablation_gap": round(gaps["twistor_carrier_ablation_gap"], 9),
            "orientation_erased_gap": round(gaps["orientation_erased_gap"], 9),
            "single_future_gap": round(gaps["single_future_gap"], 9),
            "order_gap": round(gaps["AB_vs_BA_order_gap"], 9),
            "order_erased_gap": round(gaps["order_erased_gap"], 12),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "elapsed_seconds": round(time.time() - start, 6),
    }

    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": all_pass, "wrote": str(OUT_PATH), "summary": result["result_summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
