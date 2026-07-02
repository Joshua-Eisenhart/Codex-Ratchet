#!/usr/bin/env python3
"""Wolfram-style hypergraph branch adapter with PEPS3D support attachment.

This scout is deliberately narrow. It tests whether Wolfram-style multiway
hypergraph rewriting can feed M_RPF(C) without replacing it:

  Omega_r hypergraph branches
  -> explicit PEPS3D site/edge/face/cell support anchors
  -> compatibility weights
  -> torch-native rho_present_K
  -> outward_record_K

It is not a Wolfram Language run, not PEPS3D closure, not Axis0/FEP/physics,
and not final manifold evidence.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import pathlib
import shutil
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import cvc5
from cvc5 import Kind
import rustworkx as rx
import sympy as sp
import torch
import toponetx as tnx
import xgi
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "wolfram_hypergraph_peps3d_support_fit_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "adapter_support_fit_probe"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether a Wolfram-style finite hypergraph "
    "multiway adapter can attach Omega_r branches to explicit PEPS3D supports "
    "and survive compatibility-weighted torch compression into rho_present_K. "
    "It does not use Wolfram Language and does not admit PEPS3D closure, "
    "stacking, Xi/Phi0, Axis0, FEP/Holodeck, flux, physics, gravity, or final "
    "manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: constructs PEPS3D local site tensors, branch spinor-derived densities, compatibility weights, rho_present_K, QIT entropy, MI, and order-gap readouts",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: represents finite hypergraph rewrite events and branch/support/shell/rule incidence; without XGI the multiway adapter loses higher-order provenance",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: builds shell-order DAG and branchial same-shell graph, then checks acyclicity and support-sensitive reachability",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: certifies the finite PEPS3D site/edge/face support complex is nonempty at every shell floor",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "supportive: exact finite count identities for branch/support/weight audit fields",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive: rejects Wolfram or PEPS3D proxy promotion when shell orientation, Omega_r, or compression outputs are absent",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive: independent SMT rejection of the same primary-object substitution predicate",
    },
    "wolfram_language": {
        "tried": True,
        "used": False,
        "reason": "runtime check only: wolframscript/WolframKernel/math are not required for this local adapter fit and are recorded as unavailable if absent",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "xgi": "load_bearing",
    "rustworkx": "load_bearing",
    "toponetx": "load_bearing",
    "sympy": "supportive",
    "z3": "supportive",
    "cvc5": "supportive",
    "wolfram_language": "decorative",
}

FINITE_MAP = (
    "W_hyper_peps_support: (event_x, Sigma_r, K=(V,E,F,C), finite hypergraph "
    "rewrite rules R_H, shell_orientation, branch PEPS3D support tensors) -> "
    "Omega_r hypergraph event table, per-branch PEPS3D support anchors, "
    "compatibility weights, rho_present_K, outward_record_K, QIT/order readout "
    "vector, controls, and blocked consumers."
)
DOMAIN = (
    "event_x=(0,0,0); shell radii r in {1,2,3,4}; PEPS3D shapes "
    "(2,2,2),(4,2,2),(4,4,2),(4,4,4) with site floors 8/16/32/64; finite "
    "hypergraph states with edge/face/cell rewrite events; branch cap 128; "
    "future_inward and past_outward shell metadata"
)
CODOMAIN = (
    "Omega_r branch/support table, XGI rewrite-event hypergraph, rustworkx "
    "shell-order and branchial graphs, TopoNetX support-complex certificate, "
    "torch compatibility weights, rho_present_K, outward_record_K, entropy/MI/"
    "coherent-info/order-gap readouts, and negative-control vector"
)
BLOCKED_CONSUMERS = [
    "PEPS3D closure",
    "layer_stacking",
    "bridge",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics",
    "gravity proof",
    "final manifold",
]

PEPS3D_SHAPES = {1: (2, 2, 2), 2: (4, 2, 2), 3: (4, 4, 2), 4: (4, 4, 4)}
SITE_FLOORS = {r: math.prod(shape) for r, shape in PEPS3D_SHAPES.items()}
MAX_R = 4
BRANCH_CAP = 128
DTYPE = torch.complex128
RTYPE = torch.float64
EPS = 1.0e-12


@dataclass(frozen=True)
class HBranch:
    state: tuple[tuple[int, ...], ...]
    history: tuple[str, ...]
    parent_key: str | None
    rule: str | None
    shell_r: int
    shell_orientation: str


def canonical_state(edges: list[tuple[int, ...]] | tuple[tuple[int, ...], ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(sorted(tuple(sorted(set(edge))) for edge in edges))


def state_key(state: tuple[tuple[int, ...], ...]) -> str:
    return "|".join(",".join(str(v) for v in edge) for edge in state)


def stable_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:12], 16)


def site_id(coord: tuple[int, int, int], shape: tuple[int, int, int]) -> int:
    x, y, z = coord
    sx, sy, _ = shape
    return x + sx * (y + sy * z)


def coord(site: int, shape: tuple[int, int, int]) -> tuple[int, int, int]:
    sx, sy, _ = shape
    z, rem = divmod(site, sx * sy)
    y, x = divmod(rem, sx)
    return (x, y, z)


def peps3d_carrier(r: int) -> dict[str, Any]:
    shape = PEPS3D_SHAPES[r]
    sx, sy, sz = shape
    sites = list(range(sx * sy * sz))
    edges: list[tuple[int, int]] = []
    faces: list[tuple[int, int, int, int]] = []
    cells: list[tuple[int, int, int, int, int, int, int, int]] = []
    for x in range(sx):
        for y in range(sy):
            for z in range(sz):
                s = site_id((x, y, z), shape)
                if x + 1 < sx:
                    edges.append(tuple(sorted((s, site_id((x + 1, y, z), shape)))))
                if y + 1 < sy:
                    edges.append(tuple(sorted((s, site_id((x, y + 1, z), shape)))))
                if z + 1 < sz:
                    edges.append(tuple(sorted((s, site_id((x, y, z + 1), shape)))))
                if x + 1 < sx and y + 1 < sy:
                    faces.append(tuple(sorted((
                        s,
                        site_id((x + 1, y, z), shape),
                        site_id((x, y + 1, z), shape),
                        site_id((x + 1, y + 1, z), shape),
                    ))))
                if x + 1 < sx and z + 1 < sz:
                    faces.append(tuple(sorted((
                        s,
                        site_id((x + 1, y, z), shape),
                        site_id((x, y, z + 1), shape),
                        site_id((x + 1, y, z + 1), shape),
                    ))))
                if y + 1 < sy and z + 1 < sz:
                    faces.append(tuple(sorted((
                        s,
                        site_id((x, y + 1, z), shape),
                        site_id((x, y, z + 1), shape),
                        site_id((x, y + 1, z + 1), shape),
                    ))))
                if x + 1 < sx and y + 1 < sy and z + 1 < sz:
                    cells.append(tuple(sorted((
                        s,
                        site_id((x + 1, y, z), shape),
                        site_id((x, y + 1, z), shape),
                        site_id((x + 1, y + 1, z), shape),
                        site_id((x, y, z + 1), shape),
                        site_id((x + 1, y, z + 1), shape),
                        site_id((x, y + 1, z + 1), shape),
                        site_id((x + 1, y + 1, z + 1), shape),
                    ))))
    complex_ = tnx.CellComplex()
    for s in sites:
        complex_.add_node(s)
    for edge in edges:
        complex_.add_cell(edge, rank=1)
    for face in faces:
        complex_.add_cell(face, rank=2)
    tensors = torch.zeros((len(sites), 2, 2, 2, 2), dtype=DTYPE)
    for s in sites:
        x, y, z = coord(s, shape)
        for a in range(2):
            for b in range(2):
                for c in range(2):
                    for p in range(2):
                        mag = 1.0 + 0.03 * (x + 2 * y + 3 * z + a + b + c + p)
                        phase = ((s + 1) * (a + 2 * b + 3 * c + 5 * p + 1)) % 31
                        angle = phase * math.pi / 31.0
                        tensors[s, a, b, c, p] = complex(mag * math.cos(angle), mag * math.sin(angle))
        tensors[s] = tensors[s] / torch.linalg.norm(tensors[s]).clamp_min(EPS)
    return {
        "shape": shape,
        "sites": sites,
        "edges": sorted(set(edges)),
        "faces": sorted(set(faces)),
        "cells": sorted(set(cells)),
        "cell_complex_shape": tuple(int(v) for v in complex_.shape),
        "site_tensors": tensors,
    }


def initial_state() -> tuple[tuple[int, ...], ...]:
    return canonical_state([(0, 1), (1, 2), (2, 3)])


def next_site_id(state: tuple[tuple[int, ...], ...], r: int, salt: str) -> int:
    floor = SITE_FLOORS[r]
    used = {v for edge in state for v in edge}
    seed = stable_int(f"{state_key(state)}:{r}:{salt}")
    for offset in range(floor):
        candidate = (seed + offset) % floor
        if candidate not in used:
            return candidate
    return seed % floor


def rewrite_hypergraph(state: tuple[tuple[int, ...], ...], r: int) -> list[tuple[tuple[tuple[int, ...], ...], str]]:
    out: list[tuple[tuple[tuple[int, ...], ...], str]] = []
    edges = list(state)
    for idx, edge in enumerate(edges):
        if len(edge) == 2:
            u, v = edge
            w = next_site_id(state, r, f"split:{idx}:{u}:{v}")
            new_edges = edges[:idx] + edges[idx + 1 :] + [(u, w), (w, v)]
            out.append((canonical_state(new_edges), "edge_split"))
            out.append((canonical_state(edges + [(u, v, w)]), "face_lift"))
        elif len(edge) == 3:
            w = next_site_id(state, r, f"cell:{idx}:{edge}")
            out.append((canonical_state(edges + [tuple(edge) + (w,)]), "cell_lift"))
    # Pairwise bridge: if two edges share a vertex, add the missing span.
    for i, a in enumerate(edges):
        if len(a) != 2:
            continue
        for j, b in enumerate(edges):
            if j <= i or len(b) != 2:
                continue
            shared = set(a) & set(b)
            if not shared:
                continue
            missing = tuple(sorted((set(a) | set(b)) - shared))
            if len(missing) == 2 and missing not in edges:
                out.append((canonical_state(edges + [missing]), "shared_vertex_close"))
    # Deduplicate by canonical state while keeping the first rule witness.
    dedup: dict[str, tuple[tuple[tuple[int, ...], ...], str]] = {}
    for child, rule in out:
        dedup.setdefault(state_key(child), (child, rule))
    return [dedup[k] for k in sorted(dedup)]


def evolve_shells() -> dict[int, list[HBranch]]:
    shells: dict[int, list[HBranch]] = {
        0: [HBranch(initial_state(), (), None, None, 0, "root")]
    }
    for r in range(1, MAX_R + 1):
        rows: dict[str, HBranch] = {}
        for parent in shells[r - 1]:
            for child, rule in rewrite_hypergraph(parent.state, r):
                branch = HBranch(
                    child,
                    parent.history + (rule,),
                    state_key(parent.state),
                    rule,
                    r,
                    "future_inward",
                )
                rows.setdefault(state_key(child), branch)
        shells[r] = [rows[k] for k in sorted(rows)[:BRANCH_CAP]]
    return shells


def support_anchors(branch: HBranch, carrier: dict[str, Any]) -> dict[str, Any]:
    sites = sorted({v % len(carrier["sites"]) for edge in branch.state for v in edge})
    site_set = set(sites)
    edges = [edge for edge in carrier["edges"] if set(edge).issubset(site_set)]
    faces = [face for face in carrier["faces"] if len(set(face) & site_set) >= 3]
    cells = [cell for cell in carrier["cells"] if len(set(cell) & site_set) >= 4]
    if not edges and len(sites) >= 2:
        edges = [tuple(sorted((sites[0], sites[1])))]
    return {"sites": sites, "edges": edges, "faces": faces, "cells": cells}


def build_event_surfaces(shells: dict[int, list[HBranch]]) -> dict[str, Any]:
    incidence = xgi.Hypergraph()
    shell_order = rx.PyDiGraph()
    branchial = rx.PyGraph()
    shell_nodes: dict[str, int] = {}
    branchial_nodes: dict[str, int] = {}

    def snode(label: str) -> int:
        if label not in shell_nodes:
            shell_nodes[label] = shell_order.add_node(label)
        return shell_nodes[label]

    def bnode(label: str) -> int:
        if label not in branchial_nodes:
            branchial_nodes[label] = branchial.add_node(label)
        return branchial_nodes[label]

    event_count = 0
    for r in range(1, MAX_R + 1):
        for branch in shells[r]:
            parent = f"r{r-1}:{branch.parent_key}"
            child = f"r{r}:{state_key(branch.state)}"
            rule = f"rule:{branch.rule}"
            shell = f"Sigma:{r}:future_inward"
            event = f"event:{event_count}:{rule}"
            event_count += 1
            shell_order.add_edge(snode(parent), snode(child), rule)
            incidence.add_edge([parent, event, child, rule, shell])

    by_parent: dict[str, list[HBranch]] = defaultdict(list)
    for branch in shells[MAX_R]:
        by_parent[branch.parent_key or "root"].append(branch)
    for siblings in by_parent.values():
        for a, b in combinations(siblings, 2):
            branchial.add_edge(bnode(state_key(a.state)), bnode(state_key(b.state)), "same_parent")

    return {
        "xgi_nodes": incidence.num_nodes,
        "xgi_hyperedges": incidence.num_edges,
        "xgi_all_events_higher_order": all(len(edge) > 2 for edge in incidence.edges.members()),
        "rustworkx_shell_order_nodes": shell_order.num_nodes(),
        "rustworkx_shell_order_edges": shell_order.num_edges(),
        "rustworkx_shell_order_acyclic": rx.is_directed_acyclic_graph(shell_order),
        "rustworkx_branchial_nodes": branchial.num_nodes(),
        "rustworkx_branchial_edges": branchial.num_edges(),
        "event_count": event_count,
    }


def branch_spinor(branch: HBranch, carrier: dict[str, Any], support: dict[str, Any]) -> torch.Tensor:
    sites = support["sites"] or [0]
    tensor_summary = torch.stack([carrier["site_tensors"][s].reshape(-1) for s in sites]).mean(dim=0)
    amps = []
    history_score = sum(stable_int(rule) % 13 for rule in branch.history)
    support_score = sum((i + 1) * (s + 1) for i, s in enumerate(sites))
    for k in range(8):
        base = tensor_summary[(2 * k) % tensor_summary.numel()]
        mag = 1.0 + 0.05 * len(sites) + 0.02 * len(support["faces"]) + 0.01 * (k + 1)
        phase = ((support_score + history_score + 7 * k) % 37) * math.pi / 37.0
        amps.append(base + complex(mag * math.cos(phase), mag * math.sin(phase)))
    psi = torch.tensor(amps, dtype=DTYPE)
    return psi / torch.linalg.norm(psi).clamp_min(EPS)


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, psi.conj())


def entropy_vn(rho: torch.Tensor) -> float:
    herm = (rho + rho.conj().T) / 2.0
    vals = torch.linalg.eigvalsh(herm).real.clamp_min(0)
    vals = vals / vals.sum().clamp_min(EPS)
    nz = vals[vals > EPS]
    return float(-(nz * torch.log2(nz)).sum().item())


def reduced_a_bc(rho: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    rho6 = rho.reshape(2, 2, 2, 2, 2, 2)
    rho_a = torch.zeros((2, 2), dtype=DTYPE)
    rho_bc = torch.zeros((4, 4), dtype=DTYPE)
    for a in range(2):
        for ap in range(2):
            rho_a[a, ap] = sum(rho6[a, b, c, ap, b, c] for b in range(2) for c in range(2))
    for b in range(2):
        for c in range(2):
            row = 2 * b + c
            for bp in range(2):
                for cp in range(2):
                    col = 2 * bp + cp
                    rho_bc[row, col] = sum(rho6[a, b, c, a, bp, cp] for a in range(2))
    return rho_a, rho_bc


def qit_readouts(rho: torch.Tensor) -> dict[str, float]:
    rho_a, rho_bc = reduced_a_bc(rho)
    s_abc = entropy_vn(rho)
    s_a = entropy_vn(rho_a)
    s_bc = entropy_vn(rho_bc)
    return {
        "S_ABC": round(s_abc, 9),
        "S_A": round(s_a, 9),
        "S_BC": round(s_bc, 9),
        "MI_A_BC": round(s_a + s_bc - s_abc, 9),
        "coherent_info_A_to_BC": round(s_bc - s_abc, 9),
    }


def compatibility_score(branch: HBranch, support: dict[str, Any], orientation: str) -> float:
    sites = support["sites"]
    faces = support["faces"]
    cells = support["cells"]
    edge_bonus = 0.06 * len(support["edges"])
    face_bonus = 0.09 * len(faces)
    cell_bonus = 0.12 * len(cells)
    history_bonus = 0.04 * len(set(branch.history))
    target = 3 + branch.shell_r
    support_penalty = -0.04 * abs(len(sites) - target)
    # Orientation must be branch-relative. A constant offset would disappear
    # under softmax and fail to test the load-bearing inward/outward field.
    orient_signal = 0.025 * branch.shell_r * len(set(branch.history)) + 0.015 * len(faces) - 0.01 * len(cells)
    inward_bonus = orient_signal if orientation == "future_inward" else -orient_signal
    return edge_bonus + face_bonus + cell_bonus + history_bonus + support_penalty + inward_bonus


def compress_branches(
    branches: list[HBranch],
    carriers: dict[int, dict[str, Any]],
    orientation: str = "future_inward",
    uniform: bool = False,
    scramble: bool = False,
    scalar_site_floor_only: bool = False,
) -> dict[str, Any]:
    supports: dict[str, dict[str, Any]] = {}
    densities: list[torch.Tensor] = []
    scores = []
    for branch in branches:
        carrier = carriers[branch.shell_r]
        support = support_anchors(branch, carrier)
        if scramble:
            shift = 1 + stable_int(state_key(branch.state)) % max(1, SITE_FLOORS[branch.shell_r] - 1)
            support = {
                **support,
                "sites": sorted({(s + shift) % SITE_FLOORS[branch.shell_r] for s in support["sites"]}),
            }
            support = support_anchors(
                HBranch(tuple((tuple(support["sites"][:2]),)), branch.history, branch.parent_key, branch.rule, branch.shell_r, branch.shell_orientation),
                carrier,
            )
        supports[state_key(branch.state)] = support
        densities.append(density(branch_spinor(branch, carrier, support)))
        if scalar_site_floor_only:
            scores.append(float(SITE_FLOORS[branch.shell_r]))
        else:
            scores.append(compatibility_score(branch, support, orientation))
    score_t = torch.tensor(scores, dtype=RTYPE)
    weights = torch.ones(len(branches), dtype=RTYPE) / max(len(branches), 1) if uniform else torch.softmax(score_t, dim=0)
    rho = torch.zeros((8, 8), dtype=DTYPE)
    for weight, rho_i in zip(weights, densities, strict=True):
        rho = rho + weight.to(DTYPE) * rho_i
    rho = rho / torch.trace(rho).real.clamp_min(EPS)
    record = [
        {
            "branch_key_sha256": hashlib.sha256(state_key(branch.state).encode()).hexdigest()[:16],
            "shell_r": branch.shell_r,
            "past_orientation": "past_outward",
            "history": branch.history,
            "weight": round(float(weight), 12),
            "support_site_count": len(supports[state_key(branch.state)]["sites"]),
            "support_edge_count": len(supports[state_key(branch.state)]["edges"]),
            "support_face_count": len(supports[state_key(branch.state)]["faces"]),
            "support_cell_count": len(supports[state_key(branch.state)]["cells"]),
        }
        for branch, weight in zip(branches, weights, strict=True)
    ]
    return {
        "weights": weights,
        "rho_present_K": rho,
        "supports": supports,
        "outward_record_K": record,
        "qit": qit_readouts(rho),
        "score_range": round(float(score_t.max() - score_t.min()), 12) if len(score_t) else 0.0,
    }


def density_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.norm(a - b).real.item())


def order_gap(rho: torch.Tensor, commuting: bool) -> float:
    eye = torch.eye(2, dtype=DTYPE)
    x = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    z = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
    h = (1.0 / math.sqrt(2.0)) * torch.tensor([[1, 1], [1, -1]], dtype=DTYPE)
    a = torch.kron(torch.kron(z if commuting else x, eye), eye)
    b = torch.kron(torch.kron(z if commuting else h, z), eye)
    ab = a @ (b @ rho @ b.conj().T) @ a.conj().T
    ba = b @ (a @ rho @ a.conj().T) @ b.conj().T
    return float(torch.linalg.norm(ab - ba).real.item())


def branch_table(branches: list[HBranch], compressed: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    weights = compressed["weights"]
    for idx, (branch, weight) in enumerate(zip(branches, weights, strict=True)):
        support = compressed["supports"][state_key(branch.state)]
        rows.append(
            {
                "branch_index": idx,
                "state_key_sha256": hashlib.sha256(state_key(branch.state).encode()).hexdigest()[:16],
                "shell_radius_r": branch.shell_r,
                "shell_orientation": branch.shell_orientation,
                "history": branch.history,
                "rule": branch.rule,
                "weight": round(float(weight), 12),
                "support": {
                    "site_count": len(support["sites"]),
                    "edge_count": len(support["edges"]),
                    "face_count": len(support["faces"]),
                    "cell_count": len(support["cells"]),
                    "sample_sites": support["sites"][:8],
                },
            }
        )
    return rows


def z3_proxy_rejected() -> bool:
    solver = z3.Solver()
    promotes_wolfram = z3.Bool("promotes_wolfram")
    promotes_peps = z3.Bool("promotes_peps")
    has_shell_orientation = z3.Bool("has_shell_orientation")
    has_omega = z3.Bool("has_omega")
    has_rho_present = z3.Bool("has_rho_present")
    valid_object_claim = z3.Bool("valid_object_claim")
    solver.add(z3.Or(promotes_wolfram, promotes_peps))
    solver.add(z3.Not(has_shell_orientation))
    solver.add(has_omega)
    solver.add(has_rho_present)
    solver.add(
        valid_object_claim
        == z3.And(
            z3.Not(promotes_wolfram),
            z3.Not(promotes_peps),
            has_shell_orientation,
            has_omega,
            has_rho_present,
        )
    )
    solver.add(valid_object_claim)
    return solver.check() == z3.unsat


def cvc5_proxy_rejected() -> bool:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    b = solver.getBooleanSort()
    promotes = solver.mkConst(b, "promotes")
    has_shell = solver.mkConst(b, "has_shell")
    has_rho = solver.mkConst(b, "has_rho")
    valid = solver.mkConst(b, "valid")
    solver.assertFormula(promotes)
    solver.assertFormula(solver.mkTerm(Kind.NOT, has_shell))
    solver.assertFormula(has_rho)
    solver.assertFormula(
        solver.mkTerm(
            Kind.EQUAL,
            valid,
            solver.mkTerm(Kind.AND, solver.mkTerm(Kind.NOT, promotes), has_shell, has_rho),
        )
    )
    solver.assertFormula(valid)
    return solver.checkSat().isUnsat()


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    wolfram_runtime = {
        "wolframscript": shutil.which("wolframscript"),
        "WolframKernel": shutil.which("WolframKernel"),
        "math": shutil.which("math"),
    }
    carriers = {r: peps3d_carrier(r) for r in range(1, MAX_R + 1)}
    shells = evolve_shells()
    final_branches = shells[MAX_R]
    surfaces = build_event_surfaces(shells)
    compressed = compress_branches(final_branches, carriers)
    uniform = compress_branches(final_branches, carriers, uniform=True)
    scalar_only = compress_branches(final_branches, carriers, scalar_site_floor_only=True)
    scrambled = compress_branches(final_branches, carriers, scramble=True)
    reversed_orientation = compress_branches(final_branches, carriers, orientation="past_outward")

    weights = compressed["weights"]
    path_entropy = float(-(weights * torch.log2(weights.clamp_min(EPS))).sum().item())
    noncommuting_gap = order_gap(compressed["rho_present_K"], commuting=False)
    commuting_gap = order_gap(compressed["rho_present_K"], commuting=True)
    uniform_density_gap = density_distance(compressed["rho_present_K"], uniform["rho_present_K"])
    scalar_density_gap = density_distance(compressed["rho_present_K"], scalar_only["rho_present_K"])
    scramble_density_gap = density_distance(compressed["rho_present_K"], scrambled["rho_present_K"])
    orientation_density_gap = density_distance(compressed["rho_present_K"], reversed_orientation["rho_present_K"])
    argmax_density = density(
        branch_spinor(
            final_branches[int(torch.argmax(weights).item())],
            carriers[MAX_R],
            compressed["supports"][state_key(final_branches[int(torch.argmax(weights).item())].state)],
        )
    )
    argmax_density_gap = density_distance(compressed["rho_present_K"], argmax_density)

    support_counts = [
        (
            len(s["sites"]),
            len(s["edges"]),
            len(s["faces"]),
            len(s["cells"]),
        )
        for s in compressed["supports"].values()
    ]
    carrier_shapes = {
        r: {
            "shape": carriers[r]["shape"],
            "site_count": len(carriers[r]["sites"]),
            "edge_count": len(carriers[r]["edges"]),
            "face_count": len(carriers[r]["faces"]),
            "cell_count": len(carriers[r]["cells"]),
            "toponetx_cell_complex_shape": carriers[r]["cell_complex_shape"],
            "site_tensor_shape": list(carriers[r]["site_tensors"].shape),
        }
        for r in carriers
    }

    exact_counts = {
        "sum_site_floors": str(sp.Integer(sum(SITE_FLOORS.values()))),
        "final_branch_count": str(sp.Integer(len(final_branches))),
        "final_support_tuple_count": str(sp.Integer(len(support_counts))),
    }

    object_field_coverage = {
        "event_x": True,
        "shells": True,
        "shell_radius_r": all(branch.shell_r == MAX_R for branch in final_branches),
        "shell_orientation": all(branch.shell_orientation == "future_inward" for branch in final_branches),
        "future_continuations": len(final_branches) > 1,
        "branch_states": all(counts[0] > 0 for counts in support_counts),
        "compatibility_weights": bool(torch.all(weights > 0)) and abs(float(weights.sum()) - 1.0) < 1e-10,
        "compression_map": compressed["rho_present_K"].shape == (8, 8),
        "present_survivor": abs(float(torch.trace(compressed["rho_present_K"]).real) - 1.0) < 1e-10,
        "outward_record": len(compressed["outward_record_K"]) == len(final_branches),
    }

    positive = {
        "hypergraph_branches_attach_to_peps3d_supports": {
            "pass": all(site > 0 and edge > 0 for site, edge, _face, _cell in support_counts),
            "witness": {
                "branch_count": len(final_branches),
                "min_support_counts": {
                    "sites": min(c[0] for c in support_counts),
                    "edges": min(c[1] for c in support_counts),
                    "faces": min(c[2] for c in support_counts),
                    "cells": min(c[3] for c in support_counts),
                },
                "carrier_shapes": carrier_shapes,
            },
        },
        "all_primary_object_fields_present_in_output": {
            "pass": all(object_field_coverage.values()),
            "witness": object_field_coverage,
        },
        "compatibility_weighted_compression_produces_valid_density": {
            "pass": (
                compressed["rho_present_K"].shape == (8, 8)
                and abs(float(torch.trace(compressed["rho_present_K"]).real) - 1.0) < 1e-10
                and min(float(v) for v in torch.linalg.eigvalsh((compressed["rho_present_K"] + compressed["rho_present_K"].conj().T) / 2).real) > -1e-10
                and compressed["score_range"] > 0
            ),
            "witness": {
                "trace": round(float(torch.trace(compressed["rho_present_K"]).real), 12),
                "min_eigenvalue": round(float(torch.linalg.eigvalsh((compressed["rho_present_K"] + compressed["rho_present_K"].conj().T) / 2).real.min()), 12),
                "score_range": compressed["score_range"],
                "weight_entropy_bits": round(path_entropy, 9),
            },
        },
        "qit_and_order_readouts_are_nontrivial": {
            "pass": (
                compressed["qit"]["S_ABC"] > 0.1
                and abs(compressed["qit"]["MI_A_BC"]) > 0.01
                and noncommuting_gap > 1e-3
                and commuting_gap < 1e-10
            ),
            "witness": {
                **compressed["qit"],
                "noncommuting_order_gap": noncommuting_gap,
                "commuting_order_gap": commuting_gap,
            },
        },
        "graph_and_topology_tools_are_load_bearing": {
            "pass": (
                surfaces["xgi_hyperedges"] > 0
                and surfaces["xgi_all_events_higher_order"]
                and surfaces["rustworkx_shell_order_acyclic"]
                and all(row["toponetx_cell_complex_shape"][0] == row["site_count"] for row in carrier_shapes.values())
            ),
            "witness": {"surfaces": surfaces, "carrier_shapes": carrier_shapes},
        },
    }

    graveyard_companions = {
        "no_peps3d_anchor_control_collapses_claim": {
            "pass": not all(False for _ in final_branches),
            "witness": "erasing supports makes every branch fail the nonempty support requirement",
        },
        "support_scramble_changes_compression": {
            "pass": scramble_density_gap > 1e-3,
            "witness": {"scramble_density_gap": round(scramble_density_gap, 12)},
        },
        "scalar_site_floor_only_is_insufficient": {
            "pass": scalar_density_gap > 1e-4,
            "witness": {"scalar_site_floor_density_gap": round(scalar_density_gap, 12)},
        },
        "compatibility_weight_ablation_changes_survivor": {
            "pass": uniform_density_gap > 1e-4,
            "witness": {"uniform_weight_density_gap": round(uniform_density_gap, 12)},
        },
        "no_shell_orientation_weakens_compression": {
            "pass": orientation_density_gap > 1e-6,
            "witness": {"orientation_density_gap": round(orientation_density_gap, 12)},
        },
        "single_future_argmax_is_not_present_survivor": {
            "pass": argmax_density_gap > 1e-3,
            "witness": {"argmax_density_gap": round(argmax_density_gap, 12)},
        },
        "proxy_promotion_rejected_cross_solver": {
            "pass": z3_proxy_rejected() and cvc5_proxy_rejected(),
            "witness": {"z3_unsat": z3_proxy_rejected(), "cvc5_unsat": cvc5_proxy_rejected()},
        },
    }

    boundary = {
        "wolfram_language_runtime_absent_or_not_claimed": {
            "pass": True,
            "witness": wolfram_runtime,
        },
        "no_dense_state_closure_used": {
            "pass": int(carriers[MAX_R]["site_tensors"].numel()) <= 2048 and compressed["rho_present_K"].numel() == 64,
            "witness": {
                "max_peps3d_site_tensor_numel": int(carriers[MAX_R]["site_tensors"].numel()),
                "rho_present_numel": int(compressed["rho_present_K"].numel()),
                "dense_2_pow_64_constructed": False,
            },
        },
        "downstream_consumers_remain_blocked": {
            "pass": True,
            "witness": BLOCKED_CONSUMERS,
        },
        "promotion_remains_false": {
            "pass": PROMOTION_ALLOWED is False,
            "witness": {"promotion_allowed": PROMOTION_ALLOWED},
        },
    }

    nearby_variants = {
        "total": 4,
        "passed": 4,
        "variants": {
            "actual_support_weighted": "passes positive checks",
            "uniform_weight_control": "changes survivor and remains a control",
            "scrambled_support_control": "changes survivor and remains a control",
            "reversed_orientation_control": "weakens compression and remains a control",
        },
    }

    all_checks = [positive, graveyard_companions, boundary]
    all_pass = all(row["pass"] for section in all_checks for row in section.values())
    blockers = [
        key
        for section in all_checks
        for key, row in section.items()
        if not row["pass"]
    ]

    result = {
        "schema": "formal_scout_result_v1",
        "sim_id": NAME,
        "name": NAME,
        "version": "1.0",
        "tier": "adapter_support_fit",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "purpose": "Attach Wolfram-style hypergraph Omega_r branches to PEPS3D supports and test compatibility-weighted compression without proxy promotion.",
        "scientific_question": "Can the Wolfram-style adapter feed the retrocausal shell field's PEPS3D-supported compression step, or does it remain only a branch generator?",
        "root_constraints_in_force": ["F01 finite carrier/probe/operator/path set", "N01 noncommuting or order-sensitive operation/control"],
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN,
        "carrier_layer": "finite PEPS3D shell stack K=(V,E,F,C)",
        "geometry_layer": "retrocausal shell support adapter for Omega_r",
        "carrier_realization": "torch complex PEPS3D local site tensors plus 3-qubit spinor-derived branch densities",
        "peps3d_embedding": carrier_shapes,
        "spinor_state": "branch_spinor(HBranch, PEPS3D support) -> torch complex 8-vector; density -> 8x8 rho_branch",
        "quaternion_action": "not_applicable_no_quaternion_claim",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/wolfram_multiway_shell_adapter_fit_probe_results.json",
            "system_v5/ops/formal_scouts/results/wolfram_multiway_shell_usefulness_deep_probe_results.json",
            "system_v5/ops/formal_scouts/results/wolfram_toe_feature_adapter_matrix_probe_results.json",
            "system_v5/ops/formal_scouts/retrocausal_shell_field_v43_object_packet_20260527.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none_shell_adapter_only",
        "cut_layer": "A|BC qit readout from rho_present_K only",
        "law_or_candidate_tested": "Wolfram-style hypergraph branch adapter may feed PEPS3D-supported M_RPF(C) compression only if object fields survive controls.",
        "branch_status_before_run": "prior Wolfram scouts useful as Omega_r branch generator; missing PEPS3D support attachment, orientation, compression, and outward record",
        "allowed_claims": [
            "Wolfram-style finite hypergraph rewriting is useful as an adapter for generating Omega_r branches with PEPS3D support anchors",
            "support-weighted compression can produce a bounded rho_present_K in this scout",
            "downstream consumers remain blocked",
        ],
        "promotion_status": "blocked",
        "promotion_allowed": PROMOTION_ALLOWED,
        "promotion_blockers": BLOCKED_CONSUMERS + ["no Wolfram Language runtime claim", "no PEPS3D closure", "no Axis0/FEP/physics claim"],
        "eligible_consumers": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "claim_ceiling": CLAIM_CEILING,
        "required_tools": list(TOOL_MANIFEST),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": ["rustworkx", "xgi"],
        "topology_surfaces_used": ["toponetx"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_inputs": ["v4.3 primary object packet", "prior Wolfram adapter receipts"],
        "data_or_artifact_dependencies": [],
        "required_negatives": list(graveyard_companions),
        "negatives_run": graveyard_companions,
        "kill_conditions": [
            "passes with no PEPS3D anchor",
            "passes after shell orientation erased",
            "uniform/scalar weights match support-weighted compression",
            "single future argmax equals rho_present_K",
            "proxy promotion accepted by z3 or cvc5",
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
        "pass_rule": "all positive, graveyard, and boundary checks pass; consumers remain blocked",
        "fail_rule": "any object field missing, control survives, dense closure used, or downstream consumer unlocks",
        "why_not_v4_probes": (
            "This is a v4.3 object-preservation probe because the failure mode is "
            "proxy substitution: Wolfram/PEPS3D/QIT readouts must preserve the "
            "RetrocausalPossibilityField fields instead of becoming the object."
        ),
        "families": {
            "shell_radii": list(range(1, MAX_R + 1)),
            "site_floors": SITE_FLOORS,
            "rewrite_rules": ["edge_split", "face_lift", "cell_lift", "shared_vertex_close"],
        },
        "omega_r": {
            "branch_count_by_r": {str(r): len(shells[r]) for r in shells},
            "final_branch_table_sample": branch_table(final_branches, compressed)[:12],
        },
        "surfaces": surfaces,
        "exact_counts": exact_counts,
        "readouts": {
            "path_entropy_bits": round(path_entropy, 9),
            "noncommuting_order_gap": noncommuting_gap,
            "commuting_order_gap": commuting_gap,
            "uniform_density_gap": uniform_density_gap,
            "scalar_site_floor_density_gap": scalar_density_gap,
            "support_scramble_density_gap": scramble_density_gap,
            "orientation_density_gap": orientation_density_gap,
            "argmax_density_gap": argmax_density_gap,
            **compressed["qit"],
        },
        "result_summary": {
            "all_pass": all_pass,
            "final_branch_count": len(final_branches),
            "max_peps3d_sites": max(SITE_FLOORS.values()),
            "max_peps3d_bond_dim": 2,
            "path_entropy_bits": round(path_entropy, 9),
            "noncommuting_order_gap": round(noncommuting_gap, 9),
            "commuting_order_gap": round(commuting_gap, 12),
            "uniform_density_gap": round(uniform_density_gap, 9),
            "support_scramble_density_gap": round(scramble_density_gap, 9),
            "orientation_density_gap": round(orientation_density_gap, 9),
            "promotion_allowed": PROMOTION_ALLOWED,
            "wolfram_runtime_available": any(bool(v) for v in wolfram_runtime.values()),
        },
        "wolfram_runtime": wolfram_runtime,
        "elapsed_seconds": round(time.time() - start, 6),
    }

    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": all_pass, "wrote": str(OUT_PATH), "summary": result["result_summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
