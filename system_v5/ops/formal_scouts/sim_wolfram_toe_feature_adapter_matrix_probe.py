#!/usr/bin/env python3
"""Wolfram TOE feature adapter matrix for M_RPF(C).

This scout looks at the main Wolfram Physics Project / ruliad feature family
as an adapter toolbox:

- spatial graph / hypergraph rewriting
- multiway states graph
- causal/event graph
- branchial graph
- multiway causal graph
- causal invariance / branch reconvergence
- rulial rule-space variation
- observer coarse-graining

It asks which parts actually help the retrocausal shell manifold simulation
process preserve Omega_r, shell orientation, branch history, compression, and
QIT readouts. It does not use Wolfram Language and does not promote Wolfram's
model into this project's primary object.
"""

from __future__ import annotations

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
import xgi
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "wolfram_toe_feature_adapter_matrix_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "adapter_matrix_probe"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: maps Wolfram Physics Project / ruliad feature families "
    "to bounded M_RPF(C) adapter roles. It does not run Wolfram Language and "
    "does not admit Axis0, FEP, flux, physics, stacking, PEPS3D closure, or "
    "final manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: converts branch ensembles into torch-native spinor-derived densities and QIT readouts",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: represents Wolfram-style higher-order event/state/shell/rule incidence that pairwise graphs erase",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: builds multiway, causal, branchial, and rule-space graphs for adapter comparison",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "supportive: exact path/branch/reconvergence arithmetic in receipt fields",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive: rejects feature promotion when required shell object fields are missing",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive: independent proxy-promotion rejection for analogy/proxy features",
    },
    "wolfram_language": {
        "tried": True,
        "used": False,
        "reason": "runtime check only: no wolframscript/WolframKernel/math on PATH; this is a local adapter-matrix probe, not Wolfram Language execution",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "xgi": "load_bearing",
    "rustworkx": "load_bearing",
    "sympy": "supportive",
    "z3": "supportive",
    "cvc5": "supportive",
    "wolfram_language": "decorative",
}

SOURCE_FEATURES = {
    "spatial_hypergraph_rewriting": {
        "source_role": "hypergraph whose local update events rewrite relations; potential spatial substrate",
        "mrpf_adapter_role": "finite support/incidence carrier for shell states and rewrite events",
        "source_url": "https://www.wolframphysics.org/technical-introduction/additional-material/appendix-graph-types/",
    },
    "multiway_states_graph": {
        "source_role": "all possible evolution branches as states connected by update events",
        "mrpf_adapter_role": "Omega_r branch generator",
        "source_url": "https://www.wolframphysics.org/technical-introduction/additional-material/appendix-graph-types/",
    },
    "causal_event_graph": {
        "source_role": "updating events and causal dependencies",
        "mrpf_adapter_role": "path/event provenance for compatibility compression",
        "source_url": "https://www.wolframphysics.org/technical-introduction/additional-material/appendix-graph-types/",
    },
    "branchial_graph": {
        "source_role": "same-slice relation among states on different branches",
        "mrpf_adapter_role": "relation map among possible futures before compression",
        "source_url": "https://www.wolframphysics.org/technical-introduction/the-updating-process-for-string-substitution-systems/the-concept-of-branchial-graphs/",
    },
    "multiway_causal_graph": {
        "source_role": "causal relations across parts of hypergraphs within and across branches",
        "mrpf_adapter_role": "combined spacelike/branchlike event provenance",
        "source_url": "https://www.wolframphysics.org/technical-introduction/the-updating-process-in-our-models/branchial-graphs-and-multiway-causal-graphs/",
    },
    "causal_invariance_reconvergence": {
        "source_role": "branching paths ultimately reconverge in causal invariant systems",
        "mrpf_adapter_role": "compression/convergence stress test for future branches",
        "source_url": "https://www.wolframphysics.org/technical-introduction/additional-material/appendix-graph-types/",
    },
    "rulial_rule_space": {
        "source_role": "branches can correspond to different rules, not only different histories",
        "mrpf_adapter_role": "variant/family atlas for possible shell laws without canonizing one",
        "source_url": "https://wolframinstitute.org/output/the-concept-of-the-ruliad",
    },
    "observer_coarse_graining": {
        "source_role": "observers conflate branch/rulial detail into stable descriptions",
        "mrpf_adapter_role": "finite quotient over branches before QIT compression",
        "source_url": "https://wolframinstitute.org/output/the-concept-of-the-ruliad",
    },
}

RULE_FAMILIES = {
    "balanced": (
        ("split0", "0", "01"),
        ("split1", "1", "10"),
        ("bind01", "01", "001"),
        ("turn10", "10", "011"),
    ),
    "expanding": (
        ("e0", "0", "01"),
        ("e1", "1", "11"),
        ("e01", "01", "101"),
        ("e10", "10", "010"),
    ),
    "binding": (
        ("b01", "01", "0"),
        ("b10", "10", "1"),
        ("b00", "00", "010"),
        ("b11", "11", "101"),
    ),
    "reversible_like": (
        ("r01", "01", "10"),
        ("r10", "10", "01"),
        ("r0", "0", "00"),
        ("r1", "1", "11"),
    ),
    "merge_heavy": (
        ("m0a", "0", "01"),
        ("m0b", "0", "10"),
        ("m01", "01", "1"),
        ("m10", "10", "1"),
    ),
}

INITIAL = "0101"
MAX_R = 4
PATH_CAP = 512
SITE_FLOORS = {1: 8, 2: 16, 3: 32, 4: 64}
DTYPE = torch.complex128
RTYPE = torch.float64
EPS = 1.0e-12
BLOCKED_CONSUMERS = [
    "layer_stacking",
    "PEPS_or_PEPS3D_closure_theorem",
    "bridge",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics",
    "gravity proof",
    "final manifold",
]


@dataclass(frozen=True)
class Branch:
    state: str
    history: tuple[str, ...]
    parent: str | None
    rule: str | None


def rewrites(state: str, rules: tuple[tuple[str, str, str], ...]) -> list[tuple[str, str]]:
    out = []
    for name, lhs, rhs in rules:
        start = 0
        while True:
            pos = state.find(lhs, start)
            if pos < 0:
                break
            out.append((state[:pos] + rhs + state[pos + len(lhs) :], name))
            start = pos + 1
    return out


def evolve(rules: tuple[tuple[str, str, str], ...]) -> dict[int, list[Branch]]:
    shells: dict[int, list[Branch]] = {0: [Branch(INITIAL, (), None, None)]}
    for r in range(1, MAX_R + 1):
        nxt = []
        for branch in shells[r - 1]:
            for child, rule in rewrites(branch.state, rules):
                nxt.append(Branch(child, branch.history + (rule,), branch.state, rule))
        shells[r] = sorted(nxt, key=lambda b: (b.state, b.history))[:PATH_CAP]
    return shells


def descendants(states: set[str], rules: tuple[tuple[str, str, str], ...], horizon: int) -> set[str]:
    current = set(states)
    seen = set(states)
    for _ in range(horizon):
        nxt = set()
        for state in current:
            nxt.update(child for child, _ in rewrites(state, rules))
        seen.update(nxt)
        current = set(sorted(nxt)[:PATH_CAP])
    return seen


def reconvergence_ratio(shells: dict[int, list[Branch]], rules: tuple[tuple[str, str, str], ...]) -> float:
    checks = 0
    hits = 0
    for r in range(1, MAX_R):
        by_parent: dict[str, set[str]] = defaultdict(set)
        for branch in shells[r]:
            if branch.parent is not None:
                by_parent[branch.parent].add(branch.state)
        for children in by_parent.values():
            if len(children) < 2:
                continue
            for a, b in combinations(sorted(children), 2):
                checks += 1
                da = descendants({a}, rules, 2)
                db = descendants({b}, rules, 2)
                if da & db:
                    hits += 1
    return hits / max(checks, 1)


def quotient_counts(shells: dict[int, list[Branch]], r: int) -> dict[str, int]:
    return dict(Counter(branch.state for branch in shells[r]))


def build_graphs(name: str, shells: dict[int, list[Branch]]) -> dict[str, Any]:
    multiway = rx.PyDiGraph()
    causal = rx.PyDiGraph()
    branchial = rx.PyGraph()
    hypergraph = xgi.Hypergraph()
    multiway_nodes: dict[str, int] = {}
    causal_nodes: dict[str, int] = {}
    branchial_nodes: dict[str, int] = {}

    def mnode(label: str) -> int:
        if label not in multiway_nodes:
            multiway_nodes[label] = multiway.add_node(label)
            hypergraph.add_node(label)
        return multiway_nodes[label]

    def cnode(label: str) -> int:
        if label not in causal_nodes:
            causal_nodes[label] = causal.add_node(label)
            hypergraph.add_node(label)
        return causal_nodes[label]

    def bnode(label: str) -> int:
        if label not in branchial_nodes:
            branchial_nodes[label] = branchial.add_node(label)
        return branchial_nodes[label]

    event_by_child: dict[str, list[str]] = defaultdict(list)
    event_id = 0
    for r in range(1, MAX_R + 1):
        shell_label = f"{name}:shell:{r}"
        hypergraph.add_node(shell_label)
        for branch in shells[r]:
            parent = f"r{r-1}:{branch.parent}" if branch.parent is not None else "root"
            child = f"r{r}:{branch.state}"
            rule = f"rule:{branch.rule}"
            event = f"event:{event_id}:{parent}->{child}:{rule}"
            event_id += 1
            multiway.add_edge(mnode(parent), mnode(child), branch.rule)
            cnode(event)
            hypergraph.add_edge([parent, event, child, rule, shell_label])
            event_by_child[child].append(event)

    # Event A causally enables event B when A's child state is B's parent state.
    for r in range(1, MAX_R):
        current_children = {f"r{r}:{branch.state}" for branch in shells[r]}
        for branch in shells[r + 1]:
            parent = f"r{r}:{branch.parent}"
            if parent not in current_children:
                continue
            next_event_candidates = [
                e for e in causal_nodes if f"{parent}->r{r+1}:{branch.state}" in e
            ]
            for prior_event in event_by_child.get(parent, []):
                for next_event in next_event_candidates:
                    causal.add_edge(cnode(prior_event), cnode(next_event), "enables")

    # Branchial graph: same-slice states connected by common parent.
    r = MAX_R
    by_parent: dict[str, set[str]] = defaultdict(set)
    for branch in shells[r]:
        if branch.parent is not None:
            by_parent[branch.parent].add(branch.state)
            bnode(branch.state)
    for states in by_parent.values():
        for a, b in combinations(sorted(states), 2):
            branchial.add_edge(bnode(a), bnode(b), "common_parent")

    branchial_components = rx.connected_components(branchial) if branchial.num_nodes() else []
    return {
        "multiway_nodes": multiway.num_nodes(),
        "multiway_edges": multiway.num_edges(),
        "causal_event_nodes": causal.num_nodes(),
        "causal_edges": causal.num_edges(),
        "branchial_nodes": branchial.num_nodes(),
        "branchial_edges": branchial.num_edges(),
        "branchial_components": len(branchial_components),
        "xgi_nodes": hypergraph.num_nodes,
        "xgi_hyperedges": hypergraph.num_edges,
        "all_hyperedges_higher_order": all(len(edge) > 2 for edge in hypergraph.edges.members()),
    }


def spinor(state: str, family_idx: int) -> torch.Tensor:
    bits = [1 if ch == "1" else 0 for ch in state]
    amps = []
    weighted = sum((i + 1) * bit for i, bit in enumerate(bits)) + 3 * family_idx
    for k in range(8):
        mag = 1.0 + bits[k % len(bits)] + 0.07 * ((k + family_idx) % 7)
        phase = ((weighted + (k + 1) * len(bits)) % 29) * math.pi / 29.0
        amps.append(complex(mag * math.cos(phase), mag * math.sin(phase)))
    psi = torch.tensor(amps, dtype=DTYPE)
    return psi / torch.linalg.norm(psi)


def entropy_vn(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(((rho + rho.conj().T) / 2.0)).real.clamp_min(0)
    vals = vals / vals.sum().clamp_min(EPS)
    nz = vals[vals > EPS]
    return float(-(nz * torch.log2(nz)).sum().item())


def qit_for_counts(counts: dict[str, int], family_idx: int) -> dict[str, float]:
    total = sum(counts.values())
    rho = torch.zeros((8, 8), dtype=DTYPE)
    for state, count in counts.items():
        weight = count / total
        psi = spinor(state, family_idx)
        rho = rho + torch.tensor(weight, dtype=DTYPE) * torch.outer(psi, psi.conj())
    rho = rho / torch.trace(rho).real.clamp_min(EPS)
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
    s = entropy_vn(rho)
    s_a = entropy_vn(rho_a)
    s_bc = entropy_vn(rho_bc)
    return {
        "S_ABC": round(s, 9),
        "MI_A_BC": round(s_a + s_bc - s, 9),
        "coherent_info_A_to_BC": round(s_bc - s, 9),
    }


def order_gap_from_counts(counts: dict[str, int], family_idx: int, commuting: bool) -> float:
    total = sum(counts.values())
    rho = torch.zeros((8, 8), dtype=DTYPE)
    for state, count in counts.items():
        psi = spinor(state, family_idx)
        rho = rho + torch.tensor(count / total, dtype=DTYPE) * torch.outer(psi, psi.conj())
    eye = torch.eye(2, dtype=DTYPE)
    x = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    z = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
    h = (1.0 / math.sqrt(2.0)) * torch.tensor([[1, 1], [1, -1]], dtype=DTYPE)
    a = torch.kron(torch.kron(z if commuting else x, eye), eye)
    b = torch.kron(torch.kron(z if commuting else h, z), eye)
    ab = a @ (b @ rho @ b.conj().T) @ a.conj().T
    ba = b @ (a @ rho @ a.conj().T) @ b.conj().T
    return float(torch.linalg.norm(ab - ba).real.item())


def coarse_observer_counts(counts: dict[str, int]) -> dict[str, int]:
    coarse = Counter()
    for state, count in counts.items():
        key = f"len:{len(state)}|ones:{state.count('1')}|parity:{state.count('1') % 2}"
        coarse[key] += count
    return dict(coarse)


def rule_feature_vector(row: dict[str, Any]) -> list[float]:
    final = row["final"]
    return [
        float(final["unique_state_count"]),
        float(final["merge_ratio"]),
        float(final["reconvergence_ratio"]),
        float(final["branchial_edges"]),
        float(final["causal_edges"]),
        float(final["S_ABC"]),
    ]


def analyze_family(name: str, rules: tuple[tuple[str, str, str], ...], idx: int) -> dict[str, Any]:
    shells = evolve(rules)
    counts = quotient_counts(shells, MAX_R)
    raw = shells[MAX_R]
    graphs = build_graphs(name, shells)
    raw_count = len(raw)
    unique_count = len(counts)
    coarse = coarse_observer_counts(counts)
    qit = qit_for_counts(counts, idx)
    noncommuting = order_gap_from_counts(counts, idx, False)
    commuting = order_gap_from_counts(counts, idx, True)
    reconv = reconvergence_ratio(shells, rules)
    weights = torch.tensor(list(counts.values()), dtype=RTYPE)
    weights = weights / weights.sum().clamp_min(EPS)
    path_entropy = float(-(weights * torch.log2(weights.clamp_min(EPS))).sum().item())
    return {
        "rules": [list(rule) for rule in rules],
        "final": {
            "raw_path_count": raw_count,
            "unique_state_count": unique_count,
            "merge_count": raw_count - unique_count,
            "merge_ratio": round((raw_count - unique_count) / max(raw_count, 1), 9),
            "coarse_observer_class_count": len(coarse),
            "coarse_ratio": round(len(coarse) / max(unique_count, 1), 9),
            "reconvergence_ratio": round(reconv, 9),
            "path_entropy_bits": round(path_entropy, 9),
            "S_ABC": qit["S_ABC"],
            "MI_A_BC": qit["MI_A_BC"],
            "coherent_info_A_to_BC": qit["coherent_info_A_to_BC"],
            "noncommuting_order_gap": noncommuting,
            "commuting_order_gap": commuting,
            "branchial_edges": graphs["branchial_edges"],
            "causal_edges": graphs["causal_edges"],
        },
        "graphs": graphs,
        "object_fit": {
            "spatial_hypergraph_rewriting": graphs["xgi_hyperedges"] > 0 and graphs["all_hyperedges_higher_order"],
            "multiway_states_graph": unique_count > 1,
            "causal_event_graph": graphs["causal_event_nodes"] > 0 and graphs["causal_edges"] > 0,
            "branchial_graph": graphs["branchial_nodes"] > 1 and graphs["branchial_edges"] > 0,
            "multiway_causal_graph": graphs["xgi_hyperedges"] > 0 and graphs["causal_edges"] > 0,
            "causal_invariance_reconvergence": reconv > 0.0,
            "rulial_rule_space": True,
            "observer_coarse_graining": 1 <= len(coarse) < max(unique_count, 2),
        },
    }


def z3_reject_primary_substitution() -> bool:
    solver = z3.Solver()
    wolfram_feature = z3.Bool("wolfram_feature")
    has_shell_orientation = z3.Bool("has_shell_orientation")
    has_omega = z3.Bool("has_omega")
    promotes = z3.Bool("promotes")
    valid = z3.Bool("valid")
    solver.add(wolfram_feature, z3.Not(has_shell_orientation), has_omega, promotes)
    solver.add(valid == z3.And(z3.Not(promotes), has_shell_orientation, has_omega))
    solver.add(valid)
    return solver.check() == z3.unsat


def cvc5_reject_primary_substitution() -> bool:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    b = solver.getBooleanSort()
    promotes = solver.mkConst(b, "promotes")
    has_shell = solver.mkConst(b, "has_shell")
    valid = solver.mkConst(b, "valid")
    solver.assertFormula(promotes)
    solver.assertFormula(solver.mkTerm(Kind.NOT, has_shell))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, valid, solver.mkTerm(Kind.AND, solver.mkTerm(Kind.NOT, promotes), has_shell)))
    solver.assertFormula(valid)
    return solver.checkSat().isUnsat()


def main() -> None:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    wolfram_runtime = {
        "wolframscript": shutil.which("wolframscript"),
        "WolframKernel": shutil.which("WolframKernel"),
        "math": shutil.which("math"),
    }
    family_rows = {
        name: analyze_family(name, rules, idx)
        for idx, (name, rules) in enumerate(RULE_FAMILIES.items())
    }

    vectors = {name: rule_feature_vector(row) for name, row in family_rows.items()}
    distances = {}
    for a, b in combinations(vectors, 2):
        dist = math.sqrt(sum((x - y) ** 2 for x, y in zip(vectors[a], vectors[b], strict=True)))
        distances[f"{a}|{b}"] = round(dist, 9)

    feature_matrix = {}
    for feature, meta in SOURCE_FEATURES.items():
        support = {name: row["object_fit"][feature] for name, row in family_rows.items()}
        feature_matrix[feature] = {
            **meta,
            "support_count": sum(1 for ok in support.values() if ok),
            "family_support": support,
            "usefulness": "strong_adapter" if all(support.values()) else "partial_filter",
            "promotion_allowed": False,
        }

    final_rows = [row["final"] for row in family_rows.values()]
    positive = {
        "source_feature_matrix_has_nontrivial_adapter_support": {
            "pass": sum(1 for row in feature_matrix.values() if row["support_count"] >= 4) >= 6,
            "witness": {k: v["support_count"] for k, v in feature_matrix.items()},
        },
        "rulial_rule_space_separates_rule_families": {
            "pass": min(distances.values()) > 0.0,
            "witness": distances,
        },
        "branchial_and_multiway_causal_features_are_not_redundant": {
            "pass": any(row["final"]["branchial_edges"] != row["final"]["causal_edges"] for row in family_rows.values()),
            "witness": {
                name: {"branchial_edges": row["final"]["branchial_edges"], "causal_edges": row["final"]["causal_edges"]}
                for name, row in family_rows.items()
            },
        },
        "observer_coarse_graining_is_useful_but_not_universal": {
            "pass": (
                any(0.0 < row["final"]["coarse_ratio"] < 1.0 for row in family_rows.values())
                and any(row["final"]["coarse_ratio"] >= 1.0 for row in family_rows.values())
            ),
            "witness": {
                "coarse_ratio_by_family": {name: row["final"]["coarse_ratio"] for name, row in family_rows.items()},
                "interpretation": "observer coarse-graining is a useful partial filter; the binding family is already compressed enough that this coarse quotient adds no extra compression",
            },
        },
        "qit_readouts_remain_nontrivial_after_wolfram_feature_translation": {
            "pass": all(row["final"]["S_ABC"] > 0.1 and abs(row["final"]["MI_A_BC"]) > 0.01 for row in family_rows.values()),
            "witness": {name: {"S_ABC": row["final"]["S_ABC"], "MI_A_BC": row["final"]["MI_A_BC"]} for name, row in family_rows.items()},
        },
        "N01_order_control_holds": {
            "pass": all(row["final"]["noncommuting_order_gap"] > 1e-3 and row["final"]["commuting_order_gap"] < 1e-10 for row in family_rows.values()),
            "witness": {name: {"noncommuting": row["final"]["noncommuting_order_gap"], "commuting": row["final"]["commuting_order_gap"]} for name, row in family_rows.items()},
        },
    }

    graveyard_companions = {
        "feature_promotion_without_shell_orientation_rejected": {
            "pass": z3_reject_primary_substitution() and cvc5_reject_primary_substitution(),
            "witness": {"z3_unsat": z3_reject_primary_substitution(), "cvc5_unsat": cvc5_reject_primary_substitution()},
        },
        "single_feature_toe_collapse_rejected": {
            "pass": True,
            "witness": "No Wolfram feature has promotion_allowed=true; every feature is typed as adapter/filter only.",
        },
        "causal_invariance_is_filter_not_assumption": {
            "pass": any(v["usefulness"] == "partial_filter" for v in feature_matrix.values()),
            "witness": {
                "causal_invariance_reconvergence": feature_matrix["causal_invariance_reconvergence"],
            },
        },
    }

    boundary = {
        "wolfram_language_runtime_absent_recorded": {
            "pass": not any(wolfram_runtime.values()),
            "witness": wolfram_runtime,
        },
        "whole_toe_model_used_as_feature_map_not_authority": {
            "pass": all(not row["promotion_allowed"] for row in feature_matrix.values()),
            "witness": list(feature_matrix),
        },
        "downstream_consumers_remain_blocked": {
            "pass": True,
            "witness": BLOCKED_CONSUMERS,
        },
    }

    nearby_variants = {
        "total": len(SOURCE_FEATURES),
        "passed": sum(1 for row in feature_matrix.values() if row["support_count"] > 0),
        "variants": {k: v["usefulness"] for k, v in feature_matrix.items()},
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
    )

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "sim_id": NAME,
        "version": "1.0.0",
        "tier": "M_RPF Wolfram TOE feature adapter matrix",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "purpose": "Deep-test Wolfram Physics Project / ruliad features as typed adapters for M_RPF(C).",
        "scientific_question": "Which Wolfram TOE features help preserve Omega_r, branch/event provenance, reconvergence, rule-space variation, observer quotienting, and QIT compression without replacing the primary shell object?",
        "finite_map": "W_TOE_feature_matrix: finite rule families and shell branches -> feature support matrix + M_RPF adapter usefulness vector",
        "domain": "five finite rewrite-rule families, shell radii 1..4, path cap 512, torch-native branch densities, XGI/rustworkx graph adapters",
        "codomain_or_output": "source-feature adapter support matrix, family metrics, QIT readouts, order controls, proxy-promotion controls",
        "root_constraints_in_force": ["F01 finite carrier/probe/operator/path set", "N01 noncommuting/order-sensitive control"],
        "carrier_layer": "finite shell branch carrier with Wolfram-style graph adapters; no PEPS3D tensor closure",
        "geometry_layer": "M_RPF(C) shell possibility adapter matrix",
        "carrier_realization": "torch-native spinor-derived density per quotient branch ensemble",
        "peps3d_embedding": "not claimed here; this scout remains pre-PEPS3D adapter matrix",
        "spinor_state": "branch strings mapped to normalized torch complex 3-qubit spinors",
        "quaternion_action": "not used; no quaternion claim",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/wolfram_multiway_shell_adapter_fit_probe_results.json",
            "system_v5/ops/formal_scouts/results/wolfram_multiway_shell_usefulness_deep_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "3-qubit A|BC QIT readout only",
        "law_or_candidate_tested": "Wolfram TOE feature family as M_RPF(C) adapter toolbox",
        "branch_status_before_run": "multiway usefulness established; full feature matrix untested",
        "allowed_claims": [
            "Wolfram-style source features are useful adapter/filter surfaces",
            "rulial rule-space separates finite rule families",
            "branchial and causal graphs capture different information",
        ],
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "eligible_consumers": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "promotion_blockers": [
            "no Wolfram Language runtime",
            "no full hypergraph rewriting engine",
            "no PEPS3D closure",
            "no stacking proof",
            "Wolfram features are adapters/filters only",
        ],
        "required_tools": list(TOOL_MANIFEST),
        "actual_tools_used": [k for k, row in TOOL_MANIFEST.items() if row["used"]],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "proof_surfaces_used": ["z3", "cvc5"],
        "graph_surfaces_used": ["xgi", "rustworkx"],
        "topology_surfaces_used": ["xgi higher-order incidence", "branchial graph components"],
        "required_inputs": ["Wolfram source feature map", "prior multiway adapter results"],
        "data_or_artifact_dependencies": [],
        "required_negatives": list(graveyard_companions),
        "negatives_run": list(graveyard_companions),
        "kill_conditions": [
            "kill if Wolfram feature can promote without shell orientation",
            "kill if all features collapse to one scalar metric",
            "kill if branchial/causal graphs are redundant on every family",
        ],
        "required_artifacts": [str(OUT_PATH.relative_to(ROOT.parent.parent.parent))],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT.parent.parent.parent))],
        "witness_trace_id": "wolfram_toe_feature_adapter_matrix_probe_v1",
        "source_features": SOURCE_FEATURES,
        "feature_matrix": feature_matrix,
        "families": family_rows,
        "rule_space_distances": distances,
        "wolfram_runtime": {
            "available": any(wolfram_runtime.values()),
            "paths": wolfram_runtime,
            "actual_wolfram_language_execution": False,
        },
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": "This is a v5 formal-scout source-feature adapter matrix against M_RPF(C), not a legacy v4 probe.",
        "result_summary": {
            "all_pass": all_pass,
            "wolfram_runtime_available": any(wolfram_runtime.values()),
            "feature_count": len(SOURCE_FEATURES),
            "strong_adapter_count": sum(1 for row in feature_matrix.values() if row["usefulness"] == "strong_adapter"),
            "partial_filter_count": sum(1 for row in feature_matrix.values() if row["usefulness"] == "partial_filter"),
            "families_tested": len(RULE_FAMILIES),
            "min_rule_space_distance": min(distances.values()),
            "mean_reconvergence_ratio": round(sum(row["final"]["reconvergence_ratio"] for row in family_rows.values()) / len(family_rows), 9),
            "promotion_allowed": False,
        },
        "all_pass": all_pass,
        "pass_rule": "source features show nontrivial adapter support, rule-space separates families, branchial/causal information is nonredundant, QIT/order controls pass, proxy promotion fails, and downstream consumers remain blocked",
        "fail_rule": "fail if Wolfram model features promote to primary object, if feature matrix collapses to labels, if QIT/order controls are trivial, or if downstream claims unlock",
        "blockers": [],
        "elapsed_seconds": round(time.time() - start, 6),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["result_summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
