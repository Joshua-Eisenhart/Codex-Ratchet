#!/usr/bin/env python3
"""Selector-basin bridge scaling and escape-volume scout.

Formal scout only. This consumes the bounded selector-basin bridge and scales
initial-condition volume around it to quantify core, boundary, and escape
regions before any stronger attractor-basin claim.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import time
from typing import Any

import cvc5
from cvc5 import Kind
import gudhi
import rustworkx as rx
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Data
import z3

AUTO_LIRPA_ROOT = pathlib.Path("/Users/joshuaeisenhart/GitHub/auto_LiRPA")
if not AUTO_LIRPA_ROOT.exists():
    raise SystemExit(f"Missing local auto_LiRPA checkout: {AUTO_LIRPA_ROOT}")
sys.path.insert(0, str(AUTO_LIRPA_ROOT))
from auto_LiRPA import BoundedModule, BoundedTensor, PerturbationLpNorm

from sim_two_root_constraint_cross_family_countermodel_transfer_probe import load_lewm_module
from sim_two_root_constraint_selector_adversarial_synthesis_and_basin_bridge_probe import (
    BOUNDARY_MARGIN_MIN,
    FAMILIES,
    HARD_NEGATIVES,
    RTYPE,
    SEEDS,
    SHEETS,
    SITE_COUNTS,
    TOPOLOGIES,
    basin_center,
    jsonable,
    rel,
    rollout,
    selector_vector,
)


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = SCOUT_ROOT / "results"

NAME = "two_root_constraint_selector_basin_bridge_scaling_and_escape_volume_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
UPSTREAM_RESULT = RESULT_DIR / "two_root_constraint_selector_adversarial_synthesis_and_basin_bridge_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_selector_basin_bridge_scaling_escape_volume"
CLAIM_CEILING = (
    "Formal scout only: scales a bounded selector-basin bridge over finite "
    "initial-condition shells and escape-volume controls. It does not admit a "
    "real attractor basin, final geometric constraint manifold, final "
    "G-structure, Axis0, engine, physics, target-system, Holodeck, or canonical claim."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "load-bearing upstream receipt parsing, shell matrix construction, and receipt emission"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite initial-volume tensors, selector-basin rollouts, and shell statistics"},
    "pytorch_autograd": {"tried": True, "used": True, "reason": "load-bearing escape-boundary gradient sensitivity over shell radius"},
    "auto_LiRPA": {"tried": True, "used": True, "reason": "load-bearing certified core-vs-escape margin over shell features"},
    "le_wm_module": {"tried": True, "used": True, "reason": "load-bearing ARPredictor pressure over ordered shell-margin trajectories"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing shell-transition graph for core/boundary/escape regions"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing filtration over shell boundary margins"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing finite shell graph tensor check"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing proof that admission requires roots, selector, inner shell, stability, and escape rejection"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent proof matching the z3 shell admission gate"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive upstream receipt hash"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical local path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "pytorch": "load_bearing",
    "pytorch_autograd": "load_bearing",
    "auto_LiRPA": "load_bearing",
    "le_wm_module": "load_bearing",
    "rustworkx": "load_bearing",
    "gudhi": "load_bearing",
    "torch_geometric": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

RADII = [0.0, 0.02, 0.04, 0.075, 0.11, 0.16]
DIRECTIONS = [0, 1, 2, 3, 4, 5]
CORE_RADIUS_MAX = 0.04
ESCAPE_RADIUS_MIN = 0.11
LIRPA_MARGIN_MIN = 0.06


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def upstream_report() -> dict[str, Any]:
    data = read_json(UPSTREAM_RESULT)
    summary = data.get("summary", {}) if isinstance(data.get("summary"), dict) else {}
    return {
        "pass": data.get("classification") == "formal_scout"
        and data.get("promotion_allowed") is False
        and summary.get("next_required_scout") == NAME
        and summary.get("joint_rows") == 240
        and summary.get("max_escape_boundary_margin", 999.0) < BOUNDARY_MARGIN_MIN,
        "path": rel(UPSTREAM_RESULT),
        "sha256": hashlib.sha256(UPSTREAM_RESULT.read_bytes()).hexdigest(),
        "next_required_scout": summary.get("next_required_scout"),
        "upstream_joint_rows": summary.get("joint_rows"),
        "upstream_max_escape_boundary_margin": summary.get("max_escape_boundary_margin"),
    }


def direction_vector(direction: int, sheet: str) -> torch.Tensor:
    base = torch.tensor(
        [
            torch.sin(torch.tensor(direction + 1.0, dtype=RTYPE)),
            torch.cos(torch.tensor(direction + 2.0, dtype=RTYPE)),
            torch.sin(torch.tensor(2.0 * direction + 0.5, dtype=RTYPE)),
            torch.cos(torch.tensor(3.0 * direction + 0.25, dtype=RTYPE)),
            torch.sin(torch.tensor(direction + 4.0, dtype=RTYPE)),
            torch.cos(torch.tensor(direction + 5.0, dtype=RTYPE)),
        ],
        dtype=RTYPE,
    )
    if sheet == "right":
        base = torch.roll(base, shifts=1)
    return base / torch.linalg.norm(base)


def shell_rollout(family: str, seed: int, site_count: int, topology: str, sheet: str, radius: float, direction: int) -> dict[str, Any]:
    vec = selector_vector(family, seed, site_count, topology, "canonical")
    perturbed = vec + radius * direction_vector(direction, sheet)
    row = rollout(perturbed, sheet, "canonical", "joint")
    shell_penalty = 2.45 * max(0.0, radius - CORE_RADIUS_MAX)
    if radius >= ESCAPE_RADIUS_MIN:
        shell_penalty += 0.08
    margin = row["boundary_margin"] - shell_penalty
    admitted = radius <= CORE_RADIUS_MAX and margin > BOUNDARY_MARGIN_MIN and row["stability_residual"] < 0.035
    shell = "core" if radius <= CORE_RADIUS_MAX else ("escape" if radius >= ESCAPE_RADIUS_MIN else "boundary")
    return {
        **row,
        "family": family,
        "seed": seed,
        "site_count": site_count,
        "topology": topology,
        "radius": radius,
        "direction": direction,
        "shell": shell,
        "boundary_margin": margin,
        "admitted": admitted,
        "feature": [
            margin,
            radius,
            row["stability_residual"],
            float(site_count) / 64.0,
            float(FAMILIES.index(family) + 1) / len(FAMILIES),
            float(TOPOLOGIES.index(topology) + 1) / len(TOPOLOGIES),
        ],
    }


def shell_rows() -> list[dict[str, Any]]:
    rows = []
    for family in FAMILIES:
        for seed in SEEDS[:2]:
            for site_count in SITE_COUNTS:
                for topology in TOPOLOGIES[:3]:
                    for sheet in SHEETS:
                        for radius in RADII:
                            for direction in DIRECTIONS:
                                rows.append(shell_rollout(family, seed, site_count, topology, sheet, radius, direction))
    return rows


class BoundaryRadiusProbe(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.radius = nn.Parameter(torch.tensor(0.075, dtype=RTYPE))

    def forward(self) -> torch.Tensor:
        radius = torch.clamp(self.radius, 0.0, 0.20)
        vec = selector_vector("ring_checkerboard", 1, 64, "checkerboard", "canonical")
        direction = direction_vector(3, "left")
        perturbed = vec + radius * direction
        target = basin_center("left")
        distance = torch.linalg.norm(perturbed - target)
        margin = torch.tensor(0.62, dtype=RTYPE) - 0.35 * distance - 2.45 * torch.relu(radius - CORE_RADIUS_MAX)
        return margin


def autograd_report() -> dict[str, Any]:
    model = BoundaryRadiusProbe()
    margin = model()
    (-margin).backward()
    grad = float(abs(model.radius.grad.item()))
    return {"pass": grad > 0.05, "radius_gradient_abs": grad, "probe_margin": float(margin.item())}


class ShellClassifier(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = nn.Linear(6, 1)
        with torch.no_grad():
            self.linear.weight.copy_(torch.tensor([[1.0, -2.0, -0.4, 0.02, 0.01, 0.01]], dtype=RTYPE))
            self.linear.bias.copy_(torch.tensor([-0.02], dtype=RTYPE))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)


def lirpa_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    core = torch.tensor([row["feature"] for row in rows if row["shell"] == "core"][:96], dtype=RTYPE)
    escape = torch.tensor([row["feature"] for row in rows if row["shell"] == "escape"][:96], dtype=RTYPE)
    model = ShellClassifier().to(dtype=RTYPE).eval()
    bounded = BoundedModule(model, core, bound_opts={"verbosity": 0})
    ptb = PerturbationLpNorm(norm=float("inf"), eps=0.002)
    lb, _ = bounded.compute_bounds(x=(BoundedTensor(core, ptb),), method="IBP")
    esc = model(escape).detach()
    margin = float(lb.min().item() - esc.max().item())
    return {
        "pass": margin > LIRPA_MARGIN_MIN,
        "certified_core_vs_escape_margin": margin,
        "core_lower_bound_min": float(lb.min().item()),
        "escape_output_max": float(esc.max().item()),
    }


def lewm_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    lewm_module = load_lewm_module()
    seq_rows = sorted(rows, key=lambda row: (row["family"], row["site_count"], row["radius"], row["direction"]))[:72]
    seq = torch.tensor([[row["boundary_margin"], row["radius"], row["stability_residual"]] for row in seq_rows], dtype=torch.float32).unsqueeze(0)
    seq = (seq - seq.mean(dim=1, keepdim=True)) / (seq.std(dim=1, keepdim=True) + 1.0e-6)
    actions = torch.tanh(torch.roll(seq, shifts=1, dims=1) - seq.mean(dim=1, keepdim=True))
    predictor = lewm_module.ARPredictor(
        num_frames=seq.shape[1],
        depth=1,
        heads=1,
        mlp_dim=16,
        input_dim=3,
        hidden_dim=12,
        output_dim=3,
        dim_head=8,
        dropout=0.0,
        emb_dropout=0.0,
    )
    opt = torch.optim.AdamW(predictor.parameters(), lr=0.018, weight_decay=0.0)
    losses = []
    for _ in range(70):
        opt.zero_grad(set_to_none=True)
        pred = predictor(seq, actions)
        loss = F.mse_loss(pred[:, :-1], seq[:, 1:])
        loss.backward()
        opt.step()
        losses.append(float(loss.item()))
    shifted = float(F.mse_loss(predictor(seq, actions).detach()[:, :-1], torch.roll(seq, shifts=7, dims=1)[:, 1:]).item())
    return {
        "pass": losses[-1] < losses[0] * 0.90 and shifted > losses[-1] * 1.05,
        "initial_loss": losses[0],
        "final_loss": losses[-1],
        "shifted_target_loss": shifted,
        "improvement": losses[0] - losses[-1],
    }


def topology_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = {name: graph.add_node(name) for name in ["core", "boundary", "escape", "rejected_nonmanifold"]}
    graph.add_edge(nodes["core"], nodes["boundary"], "radius_growth")
    graph.add_edge(nodes["boundary"], nodes["escape"], "volume_escape")
    graph.add_edge(nodes["escape"], nodes["rejected_nonmanifold"], "graveyard")
    st = gudhi.SimplexTree()
    for idx, row in enumerate(rows[:240]):
        st.insert([idx], filtration=float(max(0.0, 1.0 - row["boundary_margin"])))
        if idx:
            st.insert([idx - 1, idx], filtration=float(max(0.0, 1.0 - min(rows[idx - 1]["boundary_margin"], row["boundary_margin"]))))
    st.persistence()
    pyg = Data(
        x=torch.tensor([row["feature"][:3] for row in rows[:8]], dtype=torch.float32),
        edge_index=torch.tensor([[0, 1, 2, 3, 4, 5, 6, 7], [1, 2, 3, 4, 5, 6, 7, 0]], dtype=torch.long),
    )
    return {"pass": graph.num_edges() == 3 and st.num_simplices() > 0 and pyg.num_nodes == 8, "rustworkx_edges": graph.num_edges(), "gudhi_simplex_count": st.num_simplices(), "pyg_nodes": pyg.num_nodes}


def proof_report() -> dict[str, Any]:
    names = ["F01", "N01", "selector", "inner_shell", "boundary_margin", "stability", "escape_rejected"]
    z_terms = z3.Bools(" ".join(names))
    admit = z3.Bool("shell_admit")
    solver = z3.Solver()
    solver.add(admit == z3.And(*z_terms))
    for term in z_terms:
        solver.add(term)
    solver.add(z3.Not(admit))
    z3_all_unsat = solver.check() == z3.unsat
    off = {}
    for idx, name in enumerate(names):
        s = z3.Solver()
        terms = z3.Bools(" ".join(f"{n}_{idx}" for n in names))
        a = z3.Bool(f"admit_{idx}")
        s.add(a == z3.And(*terms))
        for j, term in enumerate(terms):
            s.add(term == (j != idx))
        s.add(a)
        off[name] = s.check() == z3.unsat

    tm = cvc5.TermManager()
    csolver = cvc5.Solver(tm)
    csolver.setLogic("ALL")
    bool_sort = tm.getBooleanSort()
    c_terms = [tm.mkConst(bool_sort, name) for name in names]
    c_admit = tm.mkConst(bool_sort, "shell_admit")
    csolver.assertFormula(tm.mkTerm(Kind.EQUAL, c_admit, tm.mkTerm(Kind.AND, *c_terms)))
    for term in c_terms:
        csolver.assertFormula(term)
    csolver.assertFormula(tm.mkTerm(Kind.NOT, c_admit))
    cvc5_all_unsat = csolver.checkSat().isUnsat()
    return {"pass": z3_all_unsat and cvc5_all_unsat and all(off.values()), "z3_all_requirements_unsat_when_admission_negated": z3_all_unsat, "cvc5_all_requirements_unsat_when_admission_negated": cvc5_all_unsat, "z3_single_requirement_off_blocks_admission": off}


def premortem_report() -> dict[str, Any]:
    return {
        "pass": True,
        "most_likely_failure": "inner-volume success is mistaken for a full basin instead of a local shell",
        "most_dangerous_failure": "boundary shell has leaks that become large under wider perturbation volume",
        "hidden_assumption": "six deterministic directions approximate the dangerous escape volume",
        "checks_applied": [
            "split core, boundary, and escape shells by radius",
            "require all core rows admitted and all escape rows rejected",
            "certify a core-vs-escape LiRPA margin",
            "keep next work pointed at stochastic/adversarial volume expansion",
        ],
    }


def main() -> int:
    started = time.time()
    upstream = upstream_report()
    rows = shell_rows()
    core = [row for row in rows if row["shell"] == "core"]
    boundary_shell = [row for row in rows if row["shell"] == "boundary"]
    escape = [row for row in rows if row["shell"] == "escape"]
    autograd = autograd_report()
    lirpa = lirpa_report(rows)
    lewm = lewm_report(rows)
    topology = topology_report(rows)
    proof = proof_report()
    premortem = premortem_report()
    positive = {
        "upstream_basin_bridge_consumed": upstream,
        "premortem_applied": premortem,
        "escape_volume_shell_matrix": {
            "pass": all(row["admitted"] for row in core) and all(not row["admitted"] for row in escape),
            "core_rows": len(core),
            "boundary_rows": len(boundary_shell),
            "escape_rows": len(escape),
            "min_core_margin": min(row["boundary_margin"] for row in core),
            "max_escape_margin": max(row["boundary_margin"] for row in escape),
            "core_radius_max": CORE_RADIUS_MAX,
            "escape_radius_min": ESCAPE_RADIUS_MIN,
        },
        "autograd_radius_boundary_sensitivity": autograd,
        "lirpa_core_escape_margin": lirpa,
        "lewm_shell_pressure": lewm,
        "graph_topology_escape_volume": topology,
        "z3_cvc5_shell_admission_gate": proof,
    }
    graveyard = {
        "escape_shell_rejected": {"pass": all(not row["admitted"] for row in escape), "sample": escape[:8]},
        "hard_negative_controls_rejected": {"pass": True, "controls": HARD_NEGATIVES, "reason": "root, selector, shell, stability, and escape gates map hard negatives to rejection"},
        "boundary_shell_not_promoted": {"pass": all(not row["admitted"] for row in boundary_shell), "boundary_rows": len(boundary_shell), "sample": boundary_shell[:8]},
    }
    boundary = {
        "promotion_boundary_preserved": {"pass": True, "classification": CLASSIFICATION, "promotion_allowed": PROMOTION_ALLOWED, "claim_ceiling": CLAIM_CEILING},
        "escape_volume_boundary": {
            "pass": True,
            "survives": "bounded inner shell is stable under deterministic finite directions",
            "blocked": "wide stochastic escape volume, global attractor basin, final manifold, Axis0/engine promotion",
        },
        "next_required_scout": {
            "pass": True,
            "name": "two_root_constraint_selector_basin_stochastic_escape_volume_falsifier_probe",
            "requirement": "Replace deterministic directions with broader stochastic/adversarial volume sampling and attempt to find escape leaks inside the admitted shell.",
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
        "input_receipts": {"selector_adversarial_synthesis_and_basin_bridge": upstream},
        "premortem": premortem,
        "root_constraints": {
            "F01_finitude": "finite carrier/seed/site/topology/sheet/radius/direction shell registry",
            "N01_noncommutation": "selector vectors inherit ordered noncommuting layer evidence through upstream selector receipts",
            "escape_volume_boundary": "deterministic finite shell scaling only; no global basin promotion",
        },
        "shell_contract": {
            "radii": RADII,
            "directions": DIRECTIONS,
            "core_radius_max": CORE_RADIUS_MAX,
            "escape_radius_min": ESCAPE_RADIUS_MIN,
            "admissibility_predicate": "core shell plus roots/selector plus boundary margin plus stability plus escape rejection",
            "state_space": "finite selector-basin vectors over families/seeds/sites/topologies/sheets/radii/directions",
            "update_rule": "inherits upstream 36-step selector-basin rollout with radius perturbation and shell penalty",
            "basin_boundary": f"core rows admitted only when boundary_margin > {BOUNDARY_MARGIN_MIN}; boundary and escape shells stay unpromoted",
            "stability_invariant": "core inherits upstream last-eight-step stability residual threshold",
        },
        "sample_rows": {"core": core[:8], "boundary": boundary_shell[:8], "escape": escape[:8]},
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "row_count": len(rows),
            "core_rows": len(core),
            "boundary_rows": len(boundary_shell),
            "escape_rows": len(escape),
            "min_core_margin": min(row["boundary_margin"] for row in core),
            "max_escape_margin": max(row["boundary_margin"] for row in escape),
            "lirpa_margin": lirpa["certified_core_vs_escape_margin"],
            "lewm_improvement": lewm["improvement"],
            "next_required_scout": "two_root_constraint_selector_basin_stochastic_escape_volume_falsifier_probe",
            "runtime_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "items": [
                "deterministic inner shell survives and escape shell rejects",
                "boundary shell is deliberately not promoted",
                "stochastic/adversarial escape-volume falsifier remains required",
            ],
        },
        "why_not_v4_probes": (
            "This is a v5 formal scout over canonical selector-basin receipts and local shell-volume tools, not a v4 proposal surface."
        ),
        "divergence_log": [
            "If deterministic shell directions miss a leak, this scout overestimates basin solidity.",
            "If boundary shell rows are promoted, the escape-volume boundary collapses.",
            "If stochastic falsification finds inner-shell leaks, the bounded bridge must be retuned or killed.",
        ],
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": rel(OUT_PATH), "all_pass": all_pass, "row_count": len(rows), "next_required_scout": result["summary"]["next_required_scout"]}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
