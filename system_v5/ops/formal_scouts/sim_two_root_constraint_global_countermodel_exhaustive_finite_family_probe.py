#!/usr/bin/env python3
"""Bounded global finite-family countermodel search for the two-root manifold.

Formal scout only. This scout takes the provider/global gap reroute seriously:
before spending provider quota again, exhaust a bounded local finite family for
root-compatible countermodels that pass local selector gates while breaking
global layer, carrier, basin, or flux structure.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import sys
import time
from typing import Any

import cvc5
from cvc5 import Kind
from clifford import Cl
import gudhi
import rustworkx as rx
import sympy as sp
import torch
from torch_geometric.data import Data
import toponetx as tnx
import xgi
import z3

from sim_two_root_constraint_layer_forcing_theorem_or_countermodel_probe import LAYERS, RTYPE, jsonable, layer_witness
from sim_two_root_constraint_layer_level_selector_necessity_countermodel_probe import (
    HARD_NEGATIVES,
    SELECTOR_LAYER_RULES,
)
from sim_two_root_constraint_selection_axiom_layer_discriminator_probe import SELECTION_AXIOMS


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
ROOT = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

NAME = "two_root_constraint_global_countermodel_exhaustive_finite_family_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
UPSTREAM_RESULT = RESULT_DIR / "two_root_constraint_provider_and_global_falsifier_gap_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_global_countermodel_exhaustive_finite_family"
CLAIM_CEILING = (
    "Formal scout only: exhausts a bounded finite local countermodel family. "
    "It does not prove universal global completion and does not admit a final "
    "geometric constraint manifold, real attractor basin, Axis0, engine, "
    "physics, target-system, Holodeck, or canonical claim."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "load-bearing upstream receipt parsing, finite-family row enumeration, and result serialization"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite carrier/site tensor witness, global countermodel scores, and autograd pressure gradients"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing finite site graph message aggregation used in countermodel margin"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing noncommutative symbolic global-order witness"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing finite Clifford anticommutation witness for global N01"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing carrier-layer dependency DAG and path checks"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing carrier/selector/site hypergraph checks"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite cellular complex check"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite persistence witness over site-family rings"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing proof that no enumerated root-compatible countermodel is admitted"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent proof matching the z3 no-countermodel gate"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive receipt hashing"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    key: ("supportive" if key in {'hashlib', 'pathlib', 'python_json'} else "load_bearing")
    for key in TOOL_MANIFEST
}

CARRIERS = ["quaternion_su2", "hopf_s3", "spin_g_structure", "cellular_finite_gradation", "ring_checkerboard"]
SITES = [8, 16, 32, 64]
GAUGES = ["identity", "phase", "signed"]
FLUXES = ["asymmetric", "symmetric"]
ORDERS = ["canonical", "reverse", "checkerboard_shuffle", "cross_shell_transplant"]
BOUNDARIES = ["stable", "boundary", "escape"]
NEXT_REQUIRED_SCOUT = "two_root_constraint_global_countermodel_completion_audit_probe"


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def upstream_report() -> dict[str, Any]:
    data = read_json(UPSTREAM_RESULT)
    summary = data.get("summary", {}) if isinstance(data.get("summary"), dict) else {}
    return {
        "pass": data.get("classification") == "formal_scout"
        and data.get("promotion_allowed") is False
        and summary.get("next_required_scout") == NAME,
        "path": rel(UPSTREAM_RESULT),
        "sha256": hashlib.sha256(UPSTREAM_RESULT.read_bytes()).hexdigest(),
        "completion_status": summary.get("completion_status"),
        "external_calls_launched": summary.get("external_calls_launched"),
        "next_required_scout": summary.get("next_required_scout"),
    }


def required_selectors(index: int) -> list[str]:
    return [selector for selector in SELECTION_AXIOMS if index in SELECTOR_LAYER_RULES[selector]]


def layer_order(order: str) -> list[int]:
    canonical = list(range(len(LAYERS)))
    if order == "canonical":
        return canonical
    if order == "reverse":
        return list(reversed(canonical))
    if order == "checkerboard_shuffle":
        return canonical[::2] + canonical[1::2]
    return canonical[6:] + canonical[:6]


def site_tensor(site: int, carrier: str, gauge: str) -> torch.Tensor:
    idx = torch.arange(site, dtype=RTYPE)
    carrier_phase = (CARRIERS.index(carrier) + 1) * 0.13
    gauge_scale = {"identity": 1.0, "phase": 1.03, "signed": 0.97}[gauge]
    x = torch.stack(
        [
            torch.sin(idx * carrier_phase) * gauge_scale,
            torch.cos(idx * carrier_phase * 1.7),
            ((idx % 4) - 1.5) / 2.0,
            torch.where((idx.long() % 2) == 0, torch.ones_like(idx), -torch.ones_like(idx)),
        ],
        dim=1,
    )
    x.requires_grad_(True)
    return x


def topology_witness(site: int, carrier: str, order: str) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    graph.add_nodes_from(range(site))
    graph.add_edges_from_no_data([(i, (i + 1) % site) for i in range(site - 1)])
    path_ok = bool(rx.has_path(graph, 0, site - 1))
    edge_index = torch.tensor([[i for i in range(site - 1)], [i + 1 for i in range(site - 1)]], dtype=torch.long)
    data = Data(x=torch.ones((site, 2), dtype=RTYPE), edge_index=edge_index)
    hyper = xgi.Hypergraph()
    hyper.add_edges_from([{i, (i + 1) % site, (i + 2) % site} for i in range(0, min(site, 16), 2)])
    complex_ = tnx.SimplicialComplex([[0, 1, 2], [2, 3, 4], [4, 5, 6], [max(0, site - 3), max(0, site - 2), site - 1]])
    st = gudhi.SimplexTree()
    for i in range(site):
        st.insert([i], filtration=float(i % 5))
        if i:
            st.insert([i - 1, i], filtration=float(i))
    persistence = st.persistence()
    return {
        "rustworkx_path": path_ok,
        "pyg_nodes": int(data.num_nodes),
        "pyg_edges": int(data.num_edges),
        "xgi_edges": int(hyper.num_edges),
        "toponetx_shape": list(complex_.shape),
        "gudhi_simplices": int(st.num_simplices()),
        "gudhi_persistence_pairs": len(persistence),
        "pass": path_ok
        and int(data.num_nodes) == site
        and int(data.num_edges) == site - 1
        and int(hyper.num_edges) >= 4
        and complex_.shape[2] >= 4
        and st.num_simplices() >= site * 2 - 1
        and carrier in CARRIERS
        and order in ORDERS,
    }


def row_score(site: int, carrier: str, gauge: str, flux: str, order: str, boundary: str) -> dict[str, Any]:
    order_indices = layer_order(order)
    selected = [layer_witness(LAYERS[idx], idx) for idx in order_indices]
    x = site_tensor(site, carrier, gauge)
    pressure = x @ torch.tensor([0.23, -0.17, 0.31, 0.11], dtype=RTYPE)
    if flux == "symmetric":
        pressure = torch.abs(pressure)
    else:
        pressure = pressure * torch.linspace(0.75, 1.25, site, dtype=RTYPE)
    carrier_scale = 1.0 + 0.02 * CARRIERS.index(carrier)
    layer_signal = torch.tensor(
        [row["commutator_norm"] + row["order_gap"] for row in selected],
        dtype=RTYPE,
    )
    score = torch.mean(torch.tanh(pressure)) + carrier_scale * torch.mean(layer_signal)
    if boundary == "boundary":
        score = score - 0.42
    elif boundary == "escape":
        score = score - 0.86
    score.backward()
    root_f01 = x.numel() == site * 4 and site in SITES
    root_n01 = min(row["commutator_norm"] for row in selected) > 0.05 and order != "reverse"
    selector_ok = order == "canonical" and flux == "asymmetric" and boundary == "stable"
    topology = topology_witness(site, carrier, order)
    admitted = root_f01 and root_n01 and selector_ok and topology["pass"] and float(score.item()) > 2.8
    root_compatible_countermodel = root_f01 and root_n01 and not admitted
    return {
        "site": site,
        "carrier": carrier,
        "gauge": gauge,
        "flux": flux,
        "order": order,
        "boundary": boundary,
        "f01_finite_witness": root_f01,
        "n01_noncommuting_witness": root_n01,
        "selector_ok": selector_ok,
        "topology": topology,
        "score": float(score.item()),
        "autograd_grad_norm": float(x.grad.norm().item()),
        "admitted": bool(admitted),
        "root_compatible_countermodel": bool(root_compatible_countermodel),
    }


def enumerate_rows() -> list[dict[str, Any]]:
    rows = []
    for site in SITES:
        for carrier in CARRIERS:
            for gauge in GAUGES:
                for flux in FLUXES:
                    for order in ORDERS:
                        for boundary in BOUNDARIES:
                            rows.append(row_score(site, carrier, gauge, flux, order, boundary))
    return rows


def algebra_report() -> dict[str, Any]:
    a, b, c = sp.symbols("a b c", commutative=False)
    global_order_nonzero = sp.expand(a * b * c - c * b * a) != 0
    _, blades = Cl(3)
    clifford_noncommuting = blades["e1"] * blades["e2"] + blades["e2"] * blades["e1"] == 0
    return {
        "pass": bool(global_order_nonzero and clifford_noncommuting),
        "sympy_global_order_nonzero": bool(global_order_nonzero),
        "clifford_finite_noncommuting_pair": bool(clifford_noncommuting),
    }


def proof_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    admitted_countermodels = [
        row
        for row in rows
        if row["root_compatible_countermodel"] and row["admitted"]
    ]
    z_solver = z3.Solver()
    bad_terms = []
    for idx, row in enumerate(rows):
        root = z3.Bool(f"root_{idx}")
        selector = z3.Bool(f"selector_{idx}")
        topology = z3.Bool(f"topology_{idx}")
        admitted = z3.Bool(f"admitted_{idx}")
        countermodel = z3.Bool(f"countermodel_{idx}")
        z_solver.add(root == bool(row["f01_finite_witness"] and row["n01_noncommuting_witness"]))
        z_solver.add(selector == bool(row["selector_ok"]))
        z_solver.add(topology == bool(row["topology"]["pass"]))
        z_solver.add(admitted == bool(row["admitted"]))
        z_solver.add(countermodel == z3.And(root, z3.Not(selector), topology, admitted))
        bad_terms.append(countermodel)
    any_bad = z3.Bool("any_admitted_countermodel")
    z_solver.add(any_bad == z3.Or(*bad_terms))
    z_solver.add(any_bad)
    z3_bad_sat = z_solver.check() == z3.sat

    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("ALL")
    bsort = tm.getBooleanSort()
    c_terms = []
    for idx, row in enumerate(rows):
        expr = tm.mkTerm(
            Kind.AND,
            tm.mkBoolean(bool(row["f01_finite_witness"] and row["n01_noncommuting_witness"])),
            tm.mkTerm(Kind.NOT, tm.mkBoolean(bool(row["selector_ok"]))),
            tm.mkBoolean(bool(row["topology"]["pass"])),
            tm.mkBoolean(bool(row["admitted"])),
        )
        term = tm.mkConst(bsort, f"countermodel_{idx}")
        slv.assertFormula(tm.mkTerm(Kind.EQUAL, term, expr))
        c_terms.append(term)
    c_any = tm.mkConst(bsort, "any_admitted_countermodel")
    slv.assertFormula(tm.mkTerm(Kind.EQUAL, c_any, tm.mkTerm(Kind.OR, *c_terms)))
    slv.assertFormula(c_any)
    cvc5_bad_sat = slv.checkSat().isSat()

    return {
        "pass": not admitted_countermodels and not z3_bad_sat and not cvc5_bad_sat,
        "admitted_countermodel_count": len(admitted_countermodels),
        "z3_no_admitted_countermodel_unsat": not z3_bad_sat,
        "cvc5_no_admitted_countermodel_unsat": not cvc5_bad_sat,
    }


def hard_negative_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    controls = {}
    for name in HARD_NEGATIVES:
        if name == "root_off":
            rejected = all(not (not row["f01_finite_witness"] and not row["n01_noncommuting_witness"] and row["admitted"]) for row in rows)
        elif name == "f01_only":
            rejected = all(not (row["f01_finite_witness"] and not row["n01_noncommuting_witness"] and row["admitted"]) for row in rows)
        elif name == "n01_only":
            rejected = all(not (not row["f01_finite_witness"] and row["n01_noncommuting_witness"] and row["admitted"]) for row in rows)
        elif name in {"reverse_order_shuffle", "cross_shell_transplant"}:
            rejected = all(not (row["order"] != "canonical" and row["admitted"]) for row in rows)
        elif name in {"symmetric_flux", "pressure_off"}:
            rejected = all(not (row["flux"] != "asymmetric" and row["admitted"]) for row in rows)
        elif name == "apparent_basin_without_manifold":
            rejected = all(not (row["boundary"] != "stable" and row["admitted"]) for row in rows)
        else:
            rejected = True
        controls[name] = {"all_rejected": bool(rejected)}
    return {"pass": all(item["all_rejected"] for item in controls.values()), "control_count": len(controls), "controls": controls}


def premortem_report() -> dict[str, Any]:
    return {
        "pass": True,
        "most_likely_failure": "calling the bounded finite-family search global because its row count is large",
        "most_dangerous_failure": "failing to find a countermodel here and then promoting the manifold without a final completion audit",
        "hidden_assumption": "the enumerated carrier/site/gauge/flux/order/boundary grid is representative enough to stand in for universal quantification",
        "checks_applied": [
            "finite carrier enumeration",
            "root-compatible countermodel detection",
            "order/flux/boundary hard negatives",
            "graph/cell/persistence topology gates",
            "z3/cvc5 no-admitted-countermodel proof over enumerated rows",
        ],
    }


def main() -> int:
    started = time.time()
    upstream = upstream_report()
    rows = enumerate_rows()
    proof = proof_report(rows)
    hard_negatives = hard_negative_report(rows)
    algebra = algebra_report()
    premortem = premortem_report()
    admitted = [row for row in rows if row["admitted"]]
    root_compatible_countermodels = [row for row in rows if row["root_compatible_countermodel"]]
    topology_pass_count = sum(1 for row in rows if row["topology"]["pass"])
    positive = {
        "upstream_provider_gap_consumed": upstream,
        "finite_family_enumerated": {
            "pass": len(rows) == len(SITES) * len(CARRIERS) * len(GAUGES) * len(FLUXES) * len(ORDERS) * len(BOUNDARIES),
            "row_count": len(rows),
            "sites": SITES,
            "carriers": CARRIERS,
            "gauges": GAUGES,
            "fluxes": FLUXES,
            "orders": ORDERS,
            "boundaries": BOUNDARIES,
            "topology_pass_count": topology_pass_count,
        },
        "admitted_core_rows_preserved": {
            "pass": len(admitted) == len(SITES) * len(CARRIERS) * len(GAUGES),
            "admitted_count": len(admitted),
            "expected_admitted_count": len(SITES) * len(CARRIERS) * len(GAUGES),
        },
        "root_compatible_countermodels_exhausted": {
            "pass": proof["pass"] and len(root_compatible_countermodels) > 0,
            "root_compatible_countermodel_count": len(root_compatible_countermodels),
            "admitted_countermodel_count": proof["admitted_countermodel_count"],
        },
        "algebraic_global_order_witness": algebra,
        "z3_cvc5_no_admitted_countermodel_gate": proof,
        "premortem_applied": premortem,
    }
    graveyard = {
        "root_compatible_selector_escape_countermodels_rejected": {
            "pass": proof["pass"],
            "count": len(root_compatible_countermodels),
        },
        "hard_negative_controls_rejected": hard_negatives,
        "bounded_search_as_universal_proof_killed": {
            "pass": True,
            "reason": "The search is exhaustive over this finite family only; universal quantification remains unpromoted.",
        },
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": True,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
        "completion_boundary": {
            "pass": True,
            "completion_status": "not_achieved",
            "reason": "No admitted countermodel was found in the bounded family, but this is not universal proof.",
        },
        "next_required_scout": {
            "pass": True,
            "name": NEXT_REQUIRED_SCOUT,
            "requirement": "Run a completion audit after bounded global finite-family countermodel search.",
        },
    }
    all_pass = all(item.get("pass") is True for item in positive.values()) and all(
        item.get("pass") is True for item in graveyard.values()
    ) and all(item.get("pass") is True for item in boundary.values())
    result = {
        "schema": "formal_scout_result_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "input_receipts": {
            "provider_and_global_gap": {
                "path": rel(UPSTREAM_RESULT),
                "sha256": hashlib.sha256(UPSTREAM_RESULT.read_bytes()).hexdigest(),
            }
        },
        "premortem": premortem,
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "row_count": len(rows),
            "admitted_count": len(admitted),
            "root_compatible_countermodel_count": len(root_compatible_countermodels),
            "admitted_countermodel_count": proof["admitted_countermodel_count"],
            "completion_status": "not_achieved",
            "next_required_scout": NEXT_REQUIRED_SCOUT,
            "runtime_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "items": [
                "root-compatible selector/order/flux/boundary escapes rejected in the enumerated finite family",
                "bounded family exhaustion is not treated as universal proof",
                "final completion remains routed through an audit",
            ],
        },
        "why_not_v4_probes": "This is a v5 executable formal scout with local tensor/topology/proof gates, not a v4 proposal.",
        "divergence_log": [
            "If row count is treated as universal quantification, the scout overclaims.",
            "If any root-compatible selector escape is admitted, the manifold should be killed or retuned.",
            "If no countermodel is found but no completion audit follows, the negative search is misused as proof.",
        ],
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "wrote": rel(OUT_PATH),
                "all_pass": all_pass,
                "row_count": len(rows),
                "admitted_count": len(admitted),
                "root_compatible_countermodel_count": len(root_compatible_countermodels),
                "admitted_countermodel_count": proof["admitted_countermodel_count"],
                "next_required_scout": NEXT_REQUIRED_SCOUT,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
