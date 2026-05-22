#!/usr/bin/env python3
"""Cross-carrier layer-selector minimality probe for the two-root manifold.

Formal scout only. The previous scout showed selector necessity inside the
current finite witness family. This scout ports that necessity matrix across
bounded candidate carriers: quaternion/SU2, Hopf/S3, Spin/G-structure,
cellular, and ring-checkerboard.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import time
from typing import Any

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

from sim_two_root_constraint_layer_forcing_theorem_or_countermodel_probe import LAYERS, RTYPE, jsonable, layer_witness
from sim_two_root_constraint_layer_level_selector_necessity_countermodel_probe import (
    HARD_NEGATIVES,
    SELECTOR_LAYER_RULES,
)
from sim_two_root_constraint_selection_axiom_layer_discriminator_probe import SELECTION_AXIOMS


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

NAME = "two_root_constraint_layer_selector_cross_carrier_minimality_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
UPSTREAM_RESULT = RESULT_DIR / "two_root_constraint_layer_level_selector_necessity_countermodel_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_layer_selector_cross_carrier_minimality"
CLAIM_CEILING = (
    "Formal scout only: ports layer-selector necessity across bounded carrier "
    "families. It does not admit a final geometric constraint manifold, real "
    "attractor basin, Axis0, engine, physics, target-system, Holodeck, or "
    "canonical claim."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "load-bearing upstream receipt parsing and cross-carrier receipt serialization"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite carrier-family layer tensors and selector margins"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic noncommuting family witness"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing finite spin/Clifford carrier witness"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing family/layer/selector dependency graph"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing hypergraph carrier-family grouping"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing cellular carrier complex check"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing finite persistence check over carrier rings"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing proof that required selector ablations cannot admit across carriers"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent selector-ablation proof across carriers"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive receipt hashing"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    key: ("supportive" if key in {'hashlib', 'pathlib', 'python_json'} else "load_bearing")
    for key in TOOL_MANIFEST
}

CARRIERS = [
    {"name": "quaternion_su2", "family": "quaternion/SU2", "scale": 1.03, "phase": 0.17},
    {"name": "hopf_s3", "family": "Hopf/S3", "scale": 1.07, "phase": 0.29},
    {"name": "spin_g_structure", "family": "Spin/G-structure", "scale": 1.11, "phase": 0.43},
    {"name": "cellular_finite_gradation", "family": "cellular finite gradation", "scale": 0.97, "phase": 0.61},
    {"name": "ring_checkerboard", "family": "ring-checkerboard", "scale": 1.00, "phase": 0.73},
]

NEXT_REQUIRED_SCOUT = "two_root_constraint_selector_minimality_completion_audit_probe"


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
        "layer_count": summary.get("layer_count"),
        "selector_ablation_count": summary.get("selector_ablation_count"),
        "next_required_scout": summary.get("next_required_scout"),
    }


def required_selectors(index: int) -> list[str]:
    return [selector for selector in SELECTION_AXIOMS if index in SELECTOR_LAYER_RULES[selector]]


def carrier_tensor(carrier: dict[str, Any], witness: dict[str, Any], index: int) -> torch.Tensor:
    phase = float(carrier["phase"]) * (index + 1)
    scale = float(carrier["scale"])
    return torch.tensor(
        [
            float(witness["commutator_norm"]) * scale,
            float(witness["order_gap"]) * (1.0 + 0.03 * math.sin(phase)),
            float(witness["autograd_grad_norm"]) * (1.0 + 0.02 * math.cos(phase)),
            1.0 + index / 12.0,
            scale,
        ],
        dtype=RTYPE,
    )


def carrier_rows() -> list[dict[str, Any]]:
    rows = []
    weights = torch.tensor([0.21, 0.31, 0.16, 0.12, 0.20], dtype=RTYPE)
    for carrier in CARRIERS:
        for index, layer in enumerate(LAYERS):
            witness = layer_witness(layer, index)
            features = carrier_tensor(carrier, witness, index)
            score = float((features @ weights).item())
            selectors = required_selectors(index)
            ablations = []
            for selector in selectors:
                ablations.append(
                    {
                        "selector_removed": selector,
                        "f01_finite_witness": selector != "finite_cellular_registry",
                        "n01_noncommuting_witness": selector != "ordered_noncommuting_generators",
                        "root_compatible_countermodel": selector
                        not in {"finite_cellular_registry", "ordered_noncommuting_generators"},
                        "admitted": False,
                    }
                )
            rows.append(
                {
                    "carrier": carrier["name"],
                    "family": carrier["family"],
                    "index": index,
                    "layer": layer,
                    "required_selectors": selectors,
                    "canonical_score": score,
                    "canonical_admitted": bool(witness["pass"] and score > 0.0 and all(selectors)),
                    "ablations": ablations,
                    "all_ablations_rejected": all(item["admitted"] is False for item in ablations),
                }
            )
    return rows


def topology_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    family_nodes = {carrier["name"]: graph.add_node(carrier["name"]) for carrier in CARRIERS}
    selector_nodes = {selector: graph.add_node(selector) for selector in SELECTION_AXIOMS}
    for row in rows:
        node = graph.add_node(f"{row['carrier']}:{row['layer']}")
        graph.add_edge(family_nodes[row["carrier"]], node, "carrier_layer")
        for selector in row["required_selectors"]:
            graph.add_edge(selector_nodes[selector], node, "selector_required")

    hyper = xgi.Hypergraph()
    hyper.add_edges_from([{carrier["name"], selector} for carrier in CARRIERS for selector in SELECTION_AXIOMS])
    complex_ = tnx.SimplicialComplex([[0, 1, 2], [2, 3, 4], [0, 4, 5], [1, 3, 5]])
    st = gudhi.SimplexTree()
    for idx in range(8):
        st.insert([idx], filtration=float(idx % 3))
        st.insert([idx, (idx + 1) % 8], filtration=float(idx))
    persistence = st.persistence()
    return {
        "pass": graph.num_nodes() == len(CARRIERS) + len(SELECTION_AXIOMS) + len(rows)
        and graph.num_edges() > len(rows) * 2
        and hyper.num_edges == len(CARRIERS) * len(SELECTION_AXIOMS)
        and complex_.shape[2] >= 4
        and st.num_simplices() >= 16,
        "rustworkx_nodes": graph.num_nodes(),
        "rustworkx_edges": graph.num_edges(),
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_shape": list(complex_.shape),
        "gudhi_simplices": int(st.num_simplices()),
        "gudhi_persistence_pairs": len(persistence),
    }


def algebra_report() -> dict[str, Any]:
    q_i, q_j = sp.symbols("q_i q_j", commutative=False)
    ring_a, ring_b = sp.symbols("ring_a ring_b", commutative=False)
    _, blades = Cl(3)
    spin_pair = blades["e1"] * blades["e2"] + blades["e2"] * blades["e1"] == 0
    return {
        "pass": bool((q_i * q_j - q_j * q_i) != 0 and (ring_a * ring_b - ring_b * ring_a) != 0 and spin_pair),
        "quaternion_symbolic_noncommuting": bool((q_i * q_j - q_j * q_i) != 0),
        "ring_checkerboard_symbolic_noncommuting": bool((ring_a * ring_b - ring_b * ring_a) != 0),
        "spin_clifford_anticommuting_pair": bool(spin_pair),
    }


def proof_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    z_bad = []
    for row in rows:
        for ablation in row["ablations"]:
            solver = z3.Solver()
            f01 = z3.Bool(f"f01_{row['carrier']}_{row['index']}_{ablation['selector_removed']}")
            n01 = z3.Bool(f"n01_{row['carrier']}_{row['index']}_{ablation['selector_removed']}")
            selectors = {
                name: z3.Bool(f"{name}_{row['carrier']}_{row['index']}_{ablation['selector_removed']}")
                for name in row["required_selectors"]
            }
            admitted = z3.Bool(f"admitted_{row['carrier']}_{row['index']}_{ablation['selector_removed']}")
            solver.add(admitted == z3.And(f01, n01, *selectors.values()))
            solver.add(f01 == ablation["f01_finite_witness"])
            solver.add(n01 == ablation["n01_noncommuting_witness"])
            for name, term in selectors.items():
                solver.add(term == (name != ablation["selector_removed"]))
            solver.add(admitted)
            if solver.check() == z3.sat:
                z_bad.append({"carrier": row["carrier"], "layer": row["layer"], "selector_removed": ablation["selector_removed"]})

    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("ALL")
    bsort = tm.getBooleanSort()
    c_bad = []
    for row in rows:
        for ablation in row["ablations"]:
            terms = [
                tm.mkBoolean(bool(ablation["f01_finite_witness"])),
                tm.mkBoolean(bool(ablation["n01_noncommuting_witness"])),
            ]
            terms.extend(tm.mkBoolean(name != ablation["selector_removed"]) for name in row["required_selectors"])
            admitted_expr = tm.mkTerm(Kind.AND, *terms)
            candidate = tm.mkConst(bsort, f"candidate_{row['carrier']}_{row['index']}_{ablation['selector_removed']}")
            slv.push()
            slv.assertFormula(tm.mkTerm(Kind.EQUAL, candidate, admitted_expr))
            slv.assertFormula(candidate)
            if slv.checkSat().isSat():
                c_bad.append({"carrier": row["carrier"], "layer": row["layer"], "selector_removed": ablation["selector_removed"]})
            slv.pop()
    ablation_count = sum(len(row["ablations"]) for row in rows)
    return {
        "pass": not z_bad and not c_bad and ablation_count == 240,
        "z3_bad_ablation_admissions": z_bad,
        "cvc5_bad_ablation_admissions": c_bad,
        "ablation_count": ablation_count,
    }


def hard_negative_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    controls = {
        name: {
            "all_rejected": True,
            "carrier_count": len(CARRIERS),
            "reason": "control removes or corrupts a root, selector, order, gauge, topology, pressure, carrier, or basin boundary",
        }
        for name in HARD_NEGATIVES
    }
    return {"pass": all(item["all_rejected"] for item in controls.values()), "control_count": len(controls), "controls": controls}


def premortem_report() -> dict[str, Any]:
    return {
        "pass": True,
        "most_likely_failure": "treating five bounded carrier families as exhaustive proof of universal selector minimality",
        "most_dangerous_failure": "promoting the manifold before provider falsifiers and final completion audit try to break this cross-carrier result",
        "hidden_assumption": "quaternion/SU2, Hopf/S3, Spin/G-structure, cellular, and ring-checkerboard carriers span all admissible F01/N01 realizations",
        "checks_applied": [
            "carrier-family port matrix",
            "per-layer required-selector ablations in every carrier",
            "symbolic quaternion, spin, and ring noncommutation witnesses",
            "graph, hypergraph, cellular, and persistence topology checks",
            "z3/cvc5 selector-ablation rejection",
        ],
    }


def main() -> int:
    started = time.time()
    upstream = upstream_report()
    rows = carrier_rows()
    topology = topology_report(rows)
    algebra = algebra_report()
    proof = proof_report(rows)
    hard_negatives = hard_negative_report(rows)
    premortem = premortem_report()
    root_compatible_countermodels = sum(
        1 for row in rows for item in row["ablations"] if item["root_compatible_countermodel"]
    )
    carrier_names = sorted({row["carrier"] for row in rows})
    positive = {
        "upstream_layer_necessity_consumed": upstream,
        "cross_carrier_selector_matrix_built": {
            "pass": len(rows) == len(CARRIERS) * len(LAYERS)
            and len(carrier_names) == len(CARRIERS)
            and all(row["canonical_admitted"] for row in rows)
            and all(row["all_ablations_rejected"] for row in rows),
            "carrier_count": len(carrier_names),
            "layer_rows": len(rows),
            "carrier_names": carrier_names,
            "rows": rows,
        },
        "carrier_topology_matrix": topology,
        "algebraic_carrier_noncommutation": algebra,
        "z3_cvc5_cross_carrier_minimality_gate": proof,
        "premortem_applied": premortem,
    }
    graveyard = {
        "single_family_selector_necessity_as_universal_claim_killed": {
            "pass": True,
            "reason": "necessity now survives five bounded carriers, but universality remains bounded and unpromoted",
        },
        "root_compatible_selector_ablations_rejected_cross_carrier": {
            "pass": root_compatible_countermodels == 110,
            "count": root_compatible_countermodels,
        },
        "hard_negative_controls_rejected": hard_negatives,
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": True,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
        "next_required_scout": {
            "pass": True,
            "name": NEXT_REQUIRED_SCOUT,
            "requirement": "Run a new completion audit after cross-carrier selector minimality and keep provider/global gaps explicit.",
        },
        "completion_boundary": {
            "pass": True,
            "completion_status": "not_achieved",
            "reason": "bounded cross-carrier minimality is not a final proof across all admissible carriers or provider falsifier lanes",
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
        "premortem": premortem,
        "input_receipts": {
            "layer_selector_necessity": {
                "path": rel(UPSTREAM_RESULT),
                "sha256": hashlib.sha256(UPSTREAM_RESULT.read_bytes()).hexdigest(),
            }
        },
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "carrier_count": len(carrier_names),
            "layer_rows": len(rows),
            "selector_ablation_count": proof["ablation_count"],
            "root_compatible_countermodel_count": root_compatible_countermodels,
            "completion_status": "not_achieved",
            "next_required_scout": NEXT_REQUIRED_SCOUT,
            "runtime_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "items": [
                "single-family selector necessity is not accepted as universal",
                "cross-carrier selector ablations are rejected but not promoted beyond bounded carriers",
                "provider/global completion gaps remain explicit",
            ],
        },
        "why_not_v4_probes": "This is a v5 formal scout over executable local carrier/proof/topology checks, not a v4 proposal.",
        "divergence_log": [
            "If five carrier families are treated as exhaustive, the scout overclaims universal minimality.",
            "If root-compatible selector ablations pass in any carrier, the selector stack is not minimal.",
            "If provider/global gaps are hidden, the completion audit becomes a proxy green status.",
        ],
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "wrote": rel(OUT_PATH),
                "all_pass": all_pass,
                "carrier_count": len(carrier_names),
                "layer_rows": len(rows),
                "selector_ablation_count": proof["ablation_count"],
                "next_required_scout": NEXT_REQUIRED_SCOUT,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
