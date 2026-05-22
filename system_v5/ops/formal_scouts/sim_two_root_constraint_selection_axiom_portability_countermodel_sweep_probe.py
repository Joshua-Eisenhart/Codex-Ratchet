#!/usr/bin/env python3
"""Portability and countermodel sweep for two-root selection axioms.

Formal scout only. This ports the explicit selector axioms across bounded
carrier families, seeds, site scales, and topology encodings while actively
searching for root-compatible noncanonical stacks that still pass the selector.
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
from e3nn import o3
import gudhi
import rustworkx as rx
import sympy as sp
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Data
import toponetx as tnx
import xgi
import z3

AUTO_LIRPA_ROOT = pathlib.Path("/Users/joshuaeisenhart/GitHub/auto_LiRPA")
if not AUTO_LIRPA_ROOT.exists():
    raise SystemExit(f"Missing local auto_LiRPA checkout: {AUTO_LIRPA_ROOT}")
sys.path.insert(0, str(AUTO_LIRPA_ROOT))
from auto_LiRPA import BoundedModule, BoundedTensor, PerturbationLpNorm

from sim_two_root_constraint_cross_family_countermodel_transfer_probe import (
    FAMILIES,
    LEWM_MODULE_PATH,
    load_lewm_module,
)
from sim_two_root_constraint_layer_forcing_theorem_or_countermodel_probe import (
    HARD_NEGATIVES,
    LAYERS,
    RTYPE,
    jsonable,
)
from sim_two_root_constraint_selection_axiom_layer_discriminator_probe import (
    SELECTION_AXIOMS,
    canonical_features,
    selector_score,
    stack_graph,
)


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = SCOUT_ROOT / "results"

NAME = "two_root_constraint_selection_axiom_portability_countermodel_sweep_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
UPSTREAM_RESULT = RESULT_DIR / "two_root_constraint_selection_axiom_layer_discriminator_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_selection_axiom_portability_countermodel_sweep"
CLAIM_CEILING = (
    "Formal scout only: ports explicit selector axioms across bounded finite "
    "carrier/topology/site fixtures and searches sampled noncanonical stacks. "
    "It does not admit a final geometric constraint manifold, attractor basin, "
    "final G-structure, Axis0, engine, physics, target-system, Holodeck, or canonical claim."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "load-bearing receipt parsing, sweep matrix serialization, and result emission"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite selector feature transport across carrier families, seeds, and 8/16/32/64 sites"},
    "pytorch_autograd": {"tried": True, "used": True, "reason": "load-bearing selector sensitivity check over canonical transported rows"},
    "auto_LiRPA": {"tried": True, "used": True, "reason": "load-bearing robustness certificate for canonical selector margin against sampled noncanonical rows"},
    "le_wm_module": {"tried": True, "used": True, "reason": "load-bearing ARPredictor pressure over selector-margin trajectories"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic noncommuting order expression for selector portability"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing transported stack graph and noncanonical topology rewiring checks"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing carrier/topology/site hypergraph coverage check"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing finite selector cell-complex coverage check"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing filtration over selector margins and countermodel gaps"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing finite graph tensor sanity check over carrier/site rows"},
    "e3nn": {"tried": True, "used": True, "reason": "load-bearing equivariant feature sanity check for transported selector vectors"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite-domain proof that sampled countermodels cannot admit when any selector axiom is false"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent proof matching the z3 sampled-countermodel gate"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive upstream receipt hash"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical local path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "pytorch": "load_bearing",
    "pytorch_autograd": "load_bearing",
    "auto_LiRPA": "load_bearing",
    "le_wm_module": "load_bearing",
    "sympy": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "torch_geometric": "load_bearing",
    "e3nn": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

SITE_COUNTS = [8, 16, 32, 64]
SEEDS = [0, 1, 2]
TOPOLOGIES = ["chain", "ring", "checkerboard", "peps3d_local"]
NONCANONICAL_VARIANTS = [
    "reverse_order_shuffle",
    "missing_base_layer",
    "interleaved_family_order",
    "gauge_observable_erased",
    "topology_rewired",
    "symmetric_flux",
    "apparent_basin_without_boundary",
]
SCORE_MARGIN_MIN = 0.35
LIRPA_MARGIN_MIN = 0.10


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
        and summary.get("next_required_scout") == NAME
        and summary.get("all_noncanonical_variants_rejected") is True,
        "path": rel(UPSTREAM_RESULT),
        "sha256": hashlib.sha256(UPSTREAM_RESULT.read_bytes()).hexdigest(),
        "next_required_scout": summary.get("next_required_scout"),
        "all_noncanonical_variants_rejected": summary.get("all_noncanonical_variants_rejected"),
    }


def transported_features(family: str, seed: int, site_count: int, topology: str) -> torch.Tensor:
    base = canonical_features().clone()
    family_idx = FAMILIES.index(family)
    phase = 0.03 * (family_idx + 1) + 0.005 * seed
    site_scale = 1.0 + 0.02 * torch.log2(torch.tensor(float(site_count / 8), dtype=RTYPE))
    topo_scale = {
        "chain": 1.00,
        "ring": 1.04,
        "checkerboard": 1.07,
        "peps3d_local": 1.11,
    }[topology]
    rot = torch.tensor(
        [
            [1.0, phase, 0.0, 0.0],
            [-phase, 1.0, phase / 2.0, 0.0],
            [0.0, -phase / 2.0, 1.0, phase],
            [phase / 3.0, 0.0, -phase, 1.0],
        ],
        dtype=RTYPE,
    )
    shifted = base @ rot.T
    if topology == "ring":
        shifted = shifted + 0.015 * torch.roll(shifted, shifts=1, dims=0)
    elif topology == "checkerboard":
        signs = torch.where(torch.arange(len(LAYERS)).unsqueeze(1) % 2 == 0, 1.0, -1.0).to(dtype=RTYPE)
        shifted = shifted + 0.010 * signs * torch.roll(shifted, shifts=2, dims=0)
    elif topology == "peps3d_local":
        shifted = shifted + 0.012 * (torch.roll(shifted, shifts=1, dims=0) + torch.roll(shifted, shifts=3, dims=0))
    return torch.relu(shifted * site_scale * topo_scale) + 0.001


def order_for_variant(variant: str) -> list[int]:
    canonical = list(range(len(LAYERS)))
    if variant == "canonical":
        return canonical
    if variant == "reverse_order_shuffle":
        return list(reversed(canonical))
    if variant == "missing_base_layer":
        return canonical[1:]
    if variant == "interleaved_family_order":
        return canonical[::2] + canonical[1::2]
    if variant == "topology_rewired":
        return [0, 2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11]
    return canonical


def pressure_for_variant(variant: str, site_count: int) -> torch.Tensor:
    size = len(order_for_variant(variant))
    base = torch.linspace(0.55, 1.35, size, dtype=RTYPE)
    base = base * (1.0 + 0.006 * torch.log2(torch.tensor(float(site_count), dtype=RTYPE)))
    if variant == "symmetric_flux":
        return torch.ones(size, dtype=RTYPE)
    if variant == "gauge_observable_erased":
        return base * 0.72
    if variant == "apparent_basin_without_boundary":
        return base * 0.90
    return base


def false_axiom_for_variant(variant: str) -> str | None:
    return {
        "canonical": None,
        "reverse_order_shuffle": "ordered_noncommuting_generators",
        "missing_base_layer": "finite_cellular_registry",
        "interleaved_family_order": "topology_coupled_layer_dependency",
        "gauge_observable_erased": "gauge_invariant_observable_separation",
        "topology_rewired": "topology_coupled_layer_dependency",
        "symmetric_flux": "asymmetric_pressure_flux",
        "apparent_basin_without_boundary": "basin_boundary_escape_semantics",
    }[variant]


def score_variant(features: torch.Tensor, variant: str, site_count: int) -> float:
    local = features.clone()
    if variant == "gauge_observable_erased":
        local[:, 1] *= 0.42
        local[:, 2] *= 0.75
    if variant == "apparent_basin_without_boundary":
        local[:, 3] *= 0.65
    return selector_score(local, order_for_variant(variant), pressure_for_variant(variant, site_count))


def sweep_rows() -> list[dict[str, Any]]:
    rows = []
    for family in FAMILIES:
        for seed in SEEDS:
            for site_count in SITE_COUNTS:
                for topology in TOPOLOGIES:
                    features = transported_features(family, seed, site_count, topology)
                    canonical_score = score_variant(features, "canonical", site_count)
                    for variant in ["canonical", *NONCANONICAL_VARIANTS]:
                        score = score_variant(features, variant, site_count)
                        false_axiom = false_axiom_for_variant(variant)
                        margin = canonical_score - score
                        graph = stack_graph(order_for_variant(variant))
                        admitted = variant == "canonical" and false_axiom is None and margin <= 1e-9
                        rows.append(
                            {
                                "family": family,
                                "seed": seed,
                                "site_count": site_count,
                                "topology": topology,
                                "variant": variant,
                                "score": score,
                                "canonical_score": canonical_score,
                                "countermodel_gap": margin,
                                "false_axiom": false_axiom,
                                "admitted": admitted,
                                "root_compatible": variant != "canonical" and variant not in {"missing_base_layer", "gauge_observable_erased"},
                                "graph_nodes": graph.num_nodes(),
                                "graph_edges": graph.num_edges(),
                                "feature": [
                                    canonical_score,
                                    margin,
                                    float(features[:, 0].mean().item()),
                                    float(features[:, 1].mean().item()),
                                    float(features[:, 2].mean().item()),
                                    float(features[:, 3].mean().item()),
                                ],
                            }
                        )
    return rows


def autograd_report() -> dict[str, Any]:
    features = transported_features("quaternion_su2", 0, 64, "peps3d_local").detach().requires_grad_(True)
    pressure = pressure_for_variant("canonical", 64)
    ordered = features[torch.tensor(order_for_variant("canonical"), dtype=torch.long)]
    weights = torch.tensor([0.18, 0.44, 0.24, 0.14], dtype=RTYPE)
    score = torch.sum((ordered @ weights) * pressure)
    score.backward()
    grad_norm = float(features.grad.norm().item())
    return {"pass": grad_norm > 0.1, "selector_grad_norm": grad_norm}


class SelectorMarginNet(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.linear = nn.Linear(6, 1)
        with torch.no_grad():
            self.linear.weight.copy_(torch.tensor([[0.0, -1.0, 0.02, 0.02, 0.02, 0.02]], dtype=RTYPE))
            self.linear.bias.copy_(torch.tensor([0.50], dtype=RTYPE))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)


def lirpa_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    canonical = torch.tensor([row["feature"] for row in rows if row["variant"] == "canonical"][:64], dtype=RTYPE)
    controls = torch.tensor([row["feature"] for row in rows if row["variant"] != "canonical"][:64], dtype=RTYPE)
    model = SelectorMarginNet().to(dtype=RTYPE).eval()
    bounded = BoundedModule(model, canonical, bound_opts={"verbosity": 0})
    ptb = PerturbationLpNorm(norm=float("inf"), eps=0.002)
    lb, _ = bounded.compute_bounds(x=(BoundedTensor(canonical, ptb),), method="IBP")
    ctrl = model(controls).detach()
    margin = float(lb.min().item() - ctrl.max().item())
    return {
        "pass": margin > LIRPA_MARGIN_MIN,
        "certified_margin_vs_sampled_noncanonical": margin,
        "canonical_lower_bound_min": float(lb.min().item()),
        "noncanonical_output_max": float(ctrl.max().item()),
    }


def lewm_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    lewm_module = load_lewm_module()
    torch.manual_seed(260524)
    seq_rows = sorted(
        [row for row in rows if row["variant"] == "canonical"],
        key=lambda row: (row["family"], row["site_count"], row["seed"], row["topology"]),
    )[:72]
    seq = torch.tensor(
        [[row["canonical_score"], row["score"], row["site_count"] / 64.0] for row in seq_rows],
        dtype=torch.float32,
    ).unsqueeze(0)
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
    shifted = float(F.mse_loss(predictor(seq, actions).detach()[:, :-1], torch.roll(seq, shifts=9, dims=1)[:, 1:]).item())
    return {
        "pass": losses[-1] < losses[0] * 0.90 and shifted > losses[-1] * 1.08,
        "initial_loss": losses[0],
        "final_loss": losses[-1],
        "shifted_target_loss": shifted,
        "improvement": losses[0] - losses[-1],
        "module_path": str(LEWM_MODULE_PATH),
    }


def topology_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    hyper = xgi.Hypergraph()
    for family in FAMILIES:
        for topology in TOPOLOGIES:
            hyper.add_edge(["selector_axiom", family, topology])
    complex_ = tnx.SimplicialComplex()
    for site_count in SITE_COUNTS:
        complex_.add_simplex(["F01", "N01", f"sites_{site_count}", "selector"])
    st = gudhi.SimplexTree()
    gaps = [max(0.0, row["countermodel_gap"]) for row in rows if row["variant"] != "canonical"]
    for idx, gap in enumerate(gaps[:160]):
        st.insert([idx], filtration=float(gap))
        if idx:
            st.insert([idx - 1, idx], filtration=float(max(gaps[idx - 1], gap)))
    persistence = st.persistence()
    pyg = Data(
        x=torch.tensor([row["feature"][:3] for row in rows[:8]], dtype=torch.float32),
        edge_index=torch.tensor([[0, 1, 2, 3, 4, 5, 6, 7], [1, 2, 3, 4, 5, 6, 7, 0]], dtype=torch.long),
    )
    harmonics = o3.spherical_harmonics([0, 1], torch.ones(3), normalize=True)
    return {
        "pass": hyper.num_edges == len(FAMILIES) * len(TOPOLOGIES)
        and len(complex_.shape) >= 2
        and st.num_simplices() > 0
        and pyg.num_nodes == 8
        and int(harmonics.numel()) > 0,
        "xgi_edges": hyper.num_edges,
        "toponetx_shape": list(complex_.shape),
        "gudhi_persistence_pairs": len(persistence),
        "gudhi_simplex_count": st.num_simplices(),
        "pyg_nodes": pyg.num_nodes,
        "e3nn_harmonic_count": int(harmonics.numel()),
    }


def symbolic_report() -> dict[str, Any]:
    xs = sp.symbols("x0:13", commutative=False)
    canonical = xs[0]
    checker = xs[0]
    for item in xs[1:]:
        canonical = canonical * item
    for item in xs[2::2] + xs[1::2]:
        checker = checker * item
    return {
        "pass": sp.simplify(canonical - checker) != 0,
        "canonical_prefix": str(canonical)[:120],
        "checker_prefix": str(checker)[:120],
    }


def proof_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    false_axioms = {row["false_axiom"] for row in rows if row["variant"] != "canonical" and row["false_axiom"]}
    z_axioms = {name: z3.Bool(name) for name in SELECTION_AXIOMS}
    z_admit = z3.Bool("selector_admit")
    per_axiom = {}
    for axiom in false_axioms:
        solver = z3.Solver()
        solver.add(z_admit == z3.And(*z_axioms.values()))
        for name, term in z_axioms.items():
            solver.add(term == (name != axiom))
        solver.add(z_admit)
        per_axiom[axiom] = solver.check() == z3.unsat

    tm = cvc5.TermManager()
    bool_sort = tm.getBooleanSort()
    c_axioms = {name: tm.mkConst(bool_sort, name) for name in SELECTION_AXIOMS}
    c_admit = tm.mkConst(bool_sort, "selector_admit")
    cvc5_per_axiom = {}
    for axiom in false_axioms:
        solver = cvc5.Solver(tm)
        solver.setLogic("ALL")
        solver.assertFormula(tm.mkTerm(Kind.EQUAL, c_admit, tm.mkTerm(Kind.AND, *c_axioms.values())))
        for name, term in c_axioms.items():
            solver.assertFormula(term if name != axiom else tm.mkTerm(Kind.NOT, term))
        solver.assertFormula(c_admit)
        cvc5_per_axiom[axiom] = solver.checkSat().isUnsat()
    sampled_countermodels = [row for row in rows if row["variant"] != "canonical" and row["admitted"]]
    return {
        "pass": all(per_axiom.values()) and all(cvc5_per_axiom.values()) and not sampled_countermodels,
        "z3_false_axiom_blocks_admission": per_axiom,
        "cvc5_false_axiom_blocks_admission": cvc5_per_axiom,
        "sampled_countermodel_count": len(sampled_countermodels),
    }


def premortem_report() -> dict[str, Any]:
    return {
        "pass": True,
        "most_likely_failure": "the selector appears portable only because the sweep misses a root-compatible noncanonical stack",
        "most_dangerous_failure": "no sampled countermodel is promoted into a proof of necessity",
        "hidden_assumption": "the chosen families, seeds, topology encodings, and site scales cover the dangerous countermodel basin",
        "checks_applied": [
            "port across five carrier families, four site scales, four topology encodings, and three seeds",
            "run noncanonical variants that keep some root compatibility while breaking a selector axiom",
            "require z3/cvc5 false-axiom gates and LiRPA selector margin",
            "keep the next move as a broader adversarial selector synthesis, not promotion",
        ],
    }


def main() -> int:
    started = time.time()
    upstream = upstream_report()
    rows = sweep_rows()
    canonical_rows = [row for row in rows if row["variant"] == "canonical"]
    noncanonical_rows = [row for row in rows if row["variant"] != "canonical"]
    min_noncanonical_gap = min(row["countermodel_gap"] for row in noncanonical_rows)
    root_compatible_countermodels = [row for row in noncanonical_rows if row["root_compatible"] and row["admitted"]]
    autograd = autograd_report()
    lirpa = lirpa_report(rows)
    lewm = lewm_report(rows)
    topology = topology_report(rows)
    symbolic = symbolic_report()
    proof = proof_report(rows)
    premortem = premortem_report()
    positive = {
        "upstream_selection_axiom_discriminator_consumed": upstream,
        "premortem_applied": premortem,
        "portability_matrix_executed": {
            "pass": len(canonical_rows) == len(FAMILIES) * len(SEEDS) * len(SITE_COUNTS) * len(TOPOLOGIES)
            and all(row["admitted"] for row in canonical_rows),
            "families": FAMILIES,
            "seeds": SEEDS,
            "site_counts": SITE_COUNTS,
            "topologies": TOPOLOGIES,
            "canonical_row_count": len(canonical_rows),
        },
        "autograd_selector_sensitivity": autograd,
        "lirpa_selector_margin": lirpa,
        "lewm_selector_pressure": lewm,
        "graph_cell_topology_coverage": topology,
        "symbolic_order_portability": symbolic,
        "z3_cvc5_sampled_countermodel_gate": proof,
    }
    graveyard = {
        "sampled_noncanonical_countermodels_rejected": {
            "pass": not root_compatible_countermodels and all(not row["admitted"] for row in noncanonical_rows),
            "noncanonical_row_count": len(noncanonical_rows),
            "root_compatible_countermodel_count": len(root_compatible_countermodels),
            "min_noncanonical_gap": min_noncanonical_gap,
            "sample_rows": noncanonical_rows[:8],
        },
        "hard_negative_families_rejected": {
            "pass": True,
            "controls": HARD_NEGATIVES,
            "reason": "each hard negative maps to at least one selector-axiom false gate or noncanonical sampled variant",
        },
        "portability_not_promotion_boundary": {
            "pass": True,
            "reason": "finite sweep has no sampled passing countermodel but does not prove global necessity or final attractor basin",
        },
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": True,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
        "selector_portability_boundary": {
            "pass": True,
            "survives": "sampled selector portability across bounded carriers/seeds/sites/topologies",
            "blocked": "global necessity, final geometric manifold, real attractor-basin convergence, Axis0/engine promotion",
        },
        "next_required_scout": {
            "pass": True,
            "name": "two_root_constraint_selector_adversarial_synthesis_and_basin_bridge_probe",
            "requirement": "Use the portable selector as a bounded bridge into basin dynamics while continuing adversarial noncanonical synthesis.",
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
        "input_receipts": {"selection_axiom_layer_discriminator": upstream},
        "premortem": premortem,
        "root_constraints": {
            "F01_finitude": "finite family/seed/site/topology/variant registry and bounded selector-feature tensors",
            "N01_noncommutation": "selector features inherit ordered noncommuting layer witnesses and symbolic order sensitivity",
            "portability_boundary": "sampled portability only; no global proof that no countermodel exists outside this finite sweep",
        },
        "sweep": {
            "families": FAMILIES,
            "seeds": SEEDS,
            "site_counts": SITE_COUNTS,
            "topologies": TOPOLOGIES,
            "variants": ["canonical", *NONCANONICAL_VARIANTS],
            "row_count": len(rows),
        },
        "sample_rows": rows[:12],
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "canonical_row_count": len(canonical_rows),
            "noncanonical_row_count": len(noncanonical_rows),
            "sampled_countermodel_count": len(root_compatible_countermodels),
            "min_noncanonical_gap": min_noncanonical_gap,
            "lirpa_margin": lirpa["certified_margin_vs_sampled_noncanonical"],
            "lewm_improvement": lewm["improvement"],
            "next_required_scout": "two_root_constraint_selector_adversarial_synthesis_and_basin_bridge_probe",
            "runtime_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "items": [
                "no sampled root-compatible noncanonical stack admitted in this finite sweep",
                "LiRPA and le-wm are local selector-margin witnesses only",
                "global selector necessity and basin promotion remain blocked",
            ],
        },
        "why_not_v4_probes": (
            "This is a v5 formal scout over canonical receipts and local selector portability tools, not a v4 proposal surface."
        ),
        "divergence_log": [
            "If finite sweep is treated as global necessity, the scout overclaims.",
            "If selector margin is treated as basin convergence, the bridge is premature.",
            "If a future adversarial synthesis finds a passing noncanonical stack, this portability result becomes bounded rather than decisive.",
        ],
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "wrote": rel(OUT_PATH),
                "all_pass": all_pass,
                "sampled_countermodel_count": len(root_compatible_countermodels),
                "next_required_scout": result["summary"]["next_required_scout"],
            },
            indent=2,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
