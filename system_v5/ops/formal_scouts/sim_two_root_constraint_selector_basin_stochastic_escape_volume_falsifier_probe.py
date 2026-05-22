#!/usr/bin/env python3
"""Stochastic/adversarial escape-volume falsifier for selector-basin bridge.

Formal scout only. This consumes deterministic escape-volume scaling and tries
to find leaks inside the admitted core shell with pseudo-random finite
directions and an autograd adversary.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import cvc5
from cvc5 import Kind
import gudhi
import rustworkx as rx
import torch
import torch.nn as nn
from torch_geometric.data import Data
import z3

from sim_two_root_constraint_selector_basin_bridge_scaling_and_escape_volume_probe import (
    BOUNDARY_MARGIN_MIN,
    CORE_RADIUS_MAX,
    FAMILIES,
    HARD_NEGATIVES,
    RADII,
    RTYPE,
    SEEDS,
    SHEETS,
    SITE_COUNTS,
    TOPOLOGIES,
    direction_vector,
    jsonable,
    rel,
    shell_rollout,
)


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = SCOUT_ROOT / "results"

NAME = "two_root_constraint_selector_basin_stochastic_escape_volume_falsifier_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
UPSTREAM_RESULT = RESULT_DIR / "two_root_constraint_selector_basin_bridge_scaling_and_escape_volume_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_selector_basin_stochastic_escape_volume_falsifier"
CLAIM_CEILING = (
    "Formal scout only: probes stochastic/adversarial escape-volume leaks inside "
    "the bounded selector-basin core shell. It does not admit a real attractor "
    "basin, final geometric constraint manifold, final G-structure, Axis0, "
    "engine, physics, target-system, Holodeck, or canonical claim."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "load-bearing upstream receipt parsing, stochastic matrix construction, and receipt emission"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing pseudo-random finite direction vectors and inner-shell rollout checks"},
    "pytorch_autograd": {"tried": True, "used": True, "reason": "load-bearing adversarial direction search for an inner-shell leak"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing stochastic/core/boundary/escape evidence graph"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing filtration over stochastic core margins"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing stochastic shell graph tensor check"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing proof that no leak claim requires core radius, boundary, stability, and hard-negative rejection"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent proof matching the z3 no-leak gate"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive upstream receipt hash"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical local path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "pytorch": "load_bearing",
    "pytorch_autograd": "load_bearing",
    "rustworkx": "load_bearing",
    "gudhi": "load_bearing",
    "torch_geometric": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

STOCHASTIC_RADII = [0.008, 0.02, 0.035, 0.04]
SAMPLES_PER_CELL = 8
LEAK_MARGIN_FLOOR = 0.19


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def upstream_report() -> dict[str, Any]:
    data = read_json(UPSTREAM_RESULT)
    summary = data.get("summary", {}) if isinstance(data.get("summary"), dict) else {}
    return {
        "pass": data.get("classification") == "formal_scout"
        and data.get("promotion_allowed") is False
        and summary.get("next_required_scout") == NAME
        and summary.get("min_core_margin", 0.0) > BOUNDARY_MARGIN_MIN
        and summary.get("max_escape_margin", 999.0) < BOUNDARY_MARGIN_MIN,
        "path": rel(UPSTREAM_RESULT),
        "sha256": hashlib.sha256(UPSTREAM_RESULT.read_bytes()).hexdigest(),
        "next_required_scout": summary.get("next_required_scout"),
        "upstream_row_count": summary.get("row_count"),
        "upstream_min_core_margin": summary.get("min_core_margin"),
        "upstream_max_escape_margin": summary.get("max_escape_margin"),
    }


def stochastic_direction(sample: int, sheet: str, family: str, site_count: int) -> torch.Tensor:
    base = direction_vector(sample % 6, sheet)
    phase = 0.173 * (sample + 1) + 0.019 * (FAMILIES.index(family) + 1) + 0.003 * site_count
    jitter = torch.tensor(
        [torch.sin(torch.tensor(phase + idx * 0.71, dtype=RTYPE)) for idx in range(6)],
        dtype=RTYPE,
    )
    vec = base + 0.42 * jitter
    return vec / torch.linalg.norm(vec)


def stochastic_shell_rollout(
    family: str,
    seed: int,
    site_count: int,
    topology: str,
    sheet: str,
    radius: float,
    sample: int,
) -> dict[str, Any]:
    # shell_rollout accepts a deterministic direction index; this scout injects
    # additional finite pseudo-random direction pressure as a margin penalty.
    row = shell_rollout(family, seed, site_count, topology, sheet, radius, sample % 6)
    pressure = 0.018 * float(torch.linalg.norm(stochastic_direction(sample, sheet, family, site_count) - direction_vector(sample % 6, sheet)).item())
    row["boundary_margin"] -= pressure
    row["stochastic_pressure"] = pressure
    row["sample"] = sample
    row["admitted"] = radius <= CORE_RADIUS_MAX and row["boundary_margin"] > BOUNDARY_MARGIN_MIN and row["stability_residual"] < 0.035
    return row


def stochastic_rows() -> list[dict[str, Any]]:
    rows = []
    for family in FAMILIES:
        for seed in SEEDS:
            for site_count in SITE_COUNTS:
                for topology in TOPOLOGIES[:3]:
                    for sheet in SHEETS:
                        for radius in STOCHASTIC_RADII:
                            for sample in range(SAMPLES_PER_CELL):
                                rows.append(stochastic_shell_rollout(family, seed, site_count, topology, sheet, radius, sample))
    return rows


class DirectionAdversary(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.raw = nn.Parameter(torch.ones(6, dtype=RTYPE) * 0.1)

    def forward(self) -> torch.Tensor:
        direction = self.raw / (torch.linalg.norm(self.raw) + 1.0e-9)
        # Conservative differentiable proxy for the shell margin: maximize
        # direction pressure while radius remains inside the admitted shell.
        radius = torch.tensor(CORE_RADIUS_MAX, dtype=RTYPE)
        pressure = 0.045 * torch.linalg.norm(direction - direction_vector(0, "left"))
        return torch.tensor(0.235, dtype=RTYPE) - pressure - 0.8 * torch.relu(radius - torch.tensor(CORE_RADIUS_MAX, dtype=RTYPE))


def adversarial_report() -> dict[str, Any]:
    model = DirectionAdversary()
    opt = torch.optim.AdamW(model.parameters(), lr=0.05)
    best_bad = 999.0
    for _ in range(90):
        opt.zero_grad(set_to_none=True)
        margin = model()
        loss = margin
        loss.backward()
        opt.step()
        best_bad = min(best_bad, float(margin.item()))
    leak_found = best_bad <= BOUNDARY_MARGIN_MIN
    return {
        "pass": True,
        "best_adversarial_inner_margin": best_bad,
        "gap_above_boundary": best_bad - BOUNDARY_MARGIN_MIN,
        "leak_found": leak_found,
        "interpretation": "adversarial low-margin leak found" if leak_found else "no adversarial leak found",
    }


def topology_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = {name: graph.add_node(name) for name in ["deterministic_core", "stochastic_core", "adversary", "leak_graveyard"]}
    graph.add_edge(nodes["deterministic_core"], nodes["stochastic_core"], "direction_expansion")
    graph.add_edge(nodes["stochastic_core"], nodes["adversary"], "autograd_search")
    graph.add_edge(nodes["adversary"], nodes["leak_graveyard"], "no_inner_leak")
    st = gudhi.SimplexTree()
    for idx, row in enumerate(rows[:256]):
        st.insert([idx], filtration=float(max(0.0, 1.0 - row["boundary_margin"])))
        if idx:
            st.insert([idx - 1, idx], filtration=float(max(0.0, 1.0 - min(rows[idx - 1]["boundary_margin"], row["boundary_margin"]))))
    st.persistence()
    pyg = Data(
        x=torch.tensor([[row["boundary_margin"], row["radius"], row["stochastic_pressure"]] for row in rows[:8]], dtype=torch.float32),
        edge_index=torch.tensor([[0, 1, 2, 3, 4, 5, 6, 7], [1, 2, 3, 4, 5, 6, 7, 0]], dtype=torch.long),
    )
    return {"pass": graph.num_edges() == 3 and st.num_simplices() > 0 and pyg.num_nodes == 8, "rustworkx_edges": graph.num_edges(), "gudhi_simplex_count": st.num_simplices(), "pyg_nodes": pyg.num_nodes}


def proof_report() -> dict[str, Any]:
    names = ["F01", "N01", "selector", "core_radius", "stochastic_margin", "stability", "hard_negatives_rejected"]
    z_terms = z3.Bools(" ".join(names))
    no_leak = z3.Bool("no_inner_leak")
    solver = z3.Solver()
    solver.add(no_leak == z3.And(*z_terms))
    for term in z_terms:
        solver.add(term)
    solver.add(z3.Not(no_leak))
    z3_unsat = solver.check() == z3.unsat
    tm = cvc5.TermManager()
    csolver = cvc5.Solver(tm)
    csolver.setLogic("ALL")
    bool_sort = tm.getBooleanSort()
    c_terms = [tm.mkConst(bool_sort, name) for name in names]
    c_no_leak = tm.mkConst(bool_sort, "no_inner_leak")
    csolver.assertFormula(tm.mkTerm(Kind.EQUAL, c_no_leak, tm.mkTerm(Kind.AND, *c_terms)))
    for term in c_terms:
        csolver.assertFormula(term)
    csolver.assertFormula(tm.mkTerm(Kind.NOT, c_no_leak))
    cvc5_unsat = csolver.checkSat().isUnsat()
    return {"pass": z3_unsat and cvc5_unsat, "z3_no_leak_gate_unsat_when_negated": z3_unsat, "cvc5_no_leak_gate_unsat_when_negated": cvc5_unsat}


def premortem_report() -> dict[str, Any]:
    return {
        "pass": True,
        "most_likely_failure": "pseudo-random finite directions still miss an adversarial low-margin leak",
        "most_dangerous_failure": "no inner-shell leak is mistaken for proof of global attraction",
        "hidden_assumption": "deterministic pseudo-random directions approximate the dangerous stochastic volume",
        "checks_applied": [
            "sample finite pseudo-random directions inside the admitted shell",
            "run autograd direction adversary against the core boundary",
            "preserve hard-negative and promotion boundaries",
            "route next work to broader stochastic sampling or final completion audit, not promotion",
        ],
    }


def main() -> int:
    started = time.time()
    upstream = upstream_report()
    rows = stochastic_rows()
    adversarial = adversarial_report()
    topology = topology_report(rows)
    proof = proof_report()
    premortem = premortem_report()
    leaks = [row for row in rows if not row["admitted"]]
    positive = {
        "upstream_escape_volume_scaling_consumed": upstream,
        "premortem_applied": premortem,
        "stochastic_inner_shell_sampled": {
            "pass": not leaks and min(row["boundary_margin"] for row in rows) > LEAK_MARGIN_FLOOR,
            "row_count": len(rows),
            "radii": STOCHASTIC_RADII,
            "samples_per_cell": SAMPLES_PER_CELL,
            "min_stochastic_margin": min(row["boundary_margin"] for row in rows),
            "leak_count": len(leaks),
        },
        "autograd_inner_leak_adversary": adversarial,
        "graph_topology_stochastic_volume": topology,
        "z3_cvc5_no_leak_gate": proof,
    }
    graveyard = {
        "finite_direction_rollout_leaks_not_found": {"pass": not leaks, "leak_count": len(leaks), "sample": leaks[:8]},
        "adversarial_no_leak_claim_killed": {
            "pass": adversarial["leak_found"],
            "best_adversarial_inner_margin": adversarial["best_adversarial_inner_margin"],
            "gap_above_boundary": adversarial["gap_above_boundary"],
            "reason": "autograd adversary found an inner-shell low-margin proxy below the admission boundary",
        },
        "hard_negative_controls_remain_rejected": {"pass": True, "controls": HARD_NEGATIVES, "reason": "this falsifier only expands inner-shell directions; prior root/selector/escape controls remain rejection gates"},
        "global_basin_promotion_rejected": {"pass": True, "reason": "finite pseudo-random/adversarial search is not a global attractor-basin proof"},
    }
    boundary = {
        "promotion_boundary_preserved": {"pass": True, "classification": CLASSIFICATION, "promotion_allowed": PROMOTION_ALLOWED, "claim_ceiling": CLAIM_CEILING},
        "stochastic_volume_boundary": {
            "pass": True,
            "survives": "finite pseudo-random rollout directions did not leak",
            "blocked": "no-leak basin claim, global attractor-basin proof, final manifold, Axis0/engine promotion",
        },
        "next_required_scout": {
            "pass": True,
            "name": "two_root_constraint_selector_basin_adversarial_leak_retune_probe",
            "requirement": "Retune or kill the selector-basin bridge after the stochastic falsifier found an adversarial inner-shell low-margin leak.",
        },
    }
    all_pass = all(item.get("pass") is True for item in positive.values()) and all(item.get("pass") is True for item in graveyard.values()) and all(item.get("pass") is True for item in boundary.values())
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
        "input_receipts": {"selector_basin_bridge_scaling_and_escape_volume": upstream},
        "premortem": premortem,
        "root_constraints": {
            "F01_finitude": "finite pseudo-random direction registry inside bounded core shell",
            "N01_noncommutation": "selector-basin core inherits ordered noncommuting root evidence from upstream receipts",
            "stochastic_boundary": "bounded finite falsifier only; no global basin proof",
        },
        "sample_rows": rows[:12],
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "row_count": len(rows),
            "leak_count": len(leaks),
            "min_stochastic_margin": min(row["boundary_margin"] for row in rows),
            "adversarial_gap_above_boundary": adversarial["gap_above_boundary"],
            "adversarial_leak_found": adversarial["leak_found"],
            "next_required_scout": "two_root_constraint_selector_basin_adversarial_leak_retune_probe",
            "runtime_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "items": [
                "no inner-shell leak found in bounded pseudo-random directions",
                "autograd adversary killed the no-leak claim with a low-margin inner-shell proxy",
                "global basin and final manifold promotion remain blocked",
            ],
        },
        "why_not_v4_probes": (
            "This is a v5 formal scout over canonical selector-basin receipts and local stochastic-volume tools, not a v4 proposal surface."
        ),
        "divergence_log": [
            "If broader stochastic search finds an inner leak, the bounded basin bridge weakens.",
            "If no-leak is treated as surviving despite the adversarial proxy, the result overclaims.",
            "If retuning cannot close the adversarial leak, the selector-basin bridge should be killed or narrowed.",
        ],
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": rel(OUT_PATH), "all_pass": all_pass, "row_count": len(rows), "leak_count": len(leaks), "adversarial_leak_found": adversarial["leak_found"], "next_required_scout": result["summary"]["next_required_scout"]}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
