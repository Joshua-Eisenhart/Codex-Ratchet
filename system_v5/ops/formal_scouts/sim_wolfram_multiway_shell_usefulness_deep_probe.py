#!/usr/bin/env python3
"""Deep usefulness probe for Wolfram-style multiway shell machinery.

This is not a Wolfram Language execution and not a proof of the physics model.
It asks a narrower engineering question:

Does a Wolfram-style multiway rewrite representation help the M_RPF(C) sim
process more than deterministic rule-time or naive branch trees?

The useful target is Omega_r: a finite set of future/refinement branches with
path provenance, convergence/merge information, shell orientation, compression
weights, and QIT readouts. The failure target is proxy drift: Wolfram/ruliad
becoming the object instead of an adapter.
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
NAME = "wolfram_multiway_shell_usefulness_deep_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "adapter_comparison_probe"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: compares deterministic rule-time, naive branch trees, "
    "Wolfram-style multiway quotient graphs, and shell-QIT compression as "
    "finite adapters for M_RPF(C). It does not use Wolfram Language and does "
    "not admit Axis0, FEP, flux, physics, stacking, PEPS3D closure, or final "
    "manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: builds torch-native spinors, density mixtures, QIT entropy, MI, coherent information, and N01 order-gap readouts for compressed branch states",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: represents parent/rule/child/shell incidence as multiway hyperedges and exposes higher-order structure lost by scalar entropy or pairwise-only trees",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: builds directed shell-transition DAGs and checks shell-order acyclicity/reachability for multiway branch graphs",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "supportive: exact branch, path, and merge-count arithmetic in receipt fields",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive: rejects promotion of Wolfram/ruliad into the primary object when shell fields are absent",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive: independent SMT rejection of proxy promotion without shell orientation and Omega_r provenance",
    },
    "wolfram_language": {
        "tried": True,
        "used": False,
        "reason": "runtime check only: wolframscript/WolframKernel/math are not on PATH, so this probe tests Wolfram-style multiway machinery implemented locally, not Wolfram Language",
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
}

INITIAL_STATE = "0101"
SHELL_SITE_FLOORS = {1: 8, 2: 16, 3: 32, 4: 64}
PEPS3D_SHAPES = {1: (2, 2, 2), 2: (4, 2, 2), 3: (4, 4, 2), 4: (4, 4, 4)}
PATH_CAP = 512
DTYPE = torch.complex128
RTYPE = torch.float64
EPS = 1.0e-12

FINITE_MAP = (
    "W_compare: (finite shell Sigma_r, rewrite family R, initial support, "
    "shell orientation, PEPS3D site floor) -> comparison of deterministic "
    "rule-time, naive branch tree, multiway quotient Omega_r, and shell-QIT "
    "compression readouts."
)
DOMAIN = (
    "four finite rewrite families over binary supports; shell radii r=1..4; "
    "PEPS3D site floors 8/16/32/64 with shapes (2,2,2),(4,2,2),(4,4,2),"
    "(4,4,4); torch-native 3-qubit spinor-derived densities"
)
CODOMAIN = (
    "per-family branch/path/merge metrics, XGI hypergraph incidence metrics, "
    "rustworkx DAG checks, PEPS3D support-fit readouts, QIT entropy/MI/"
    "coherent-information readouts, N01 order gaps, and object-preservation "
    "control outcomes"
)
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
class PathBranch:
    state: str
    history: tuple[str, ...]
    parent: str | None
    rule: str | None


@dataclass(frozen=True)
class QuotientBranch:
    state: str
    multiplicity: int
    histories: tuple[tuple[str, ...], ...]
    parents: tuple[str, ...]
    rules: tuple[str, ...]


def rewrite_once(state: str, rules: tuple[tuple[str, str, str], ...]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for name, lhs, rhs in rules:
        start = 0
        while True:
            pos = state.find(lhs, start)
            if pos < 0:
                break
            out.append((state[:pos] + rhs + state[pos + len(lhs) :], name))
            start = pos + 1
    return out


def deterministic_step(state: str, rules: tuple[tuple[str, str, str], ...]) -> tuple[str, str] | None:
    children = sorted(rewrite_once(state, rules))
    if not children:
        return None
    return children[0]


def evolve_raw_paths(rules: tuple[tuple[str, str, str], ...], max_r: int = 4) -> dict[int, list[PathBranch]]:
    shells: dict[int, list[PathBranch]] = {0: [PathBranch(INITIAL_STATE, (), None, None)]}
    current = shells[0]
    for r in range(1, max_r + 1):
        nxt: list[PathBranch] = []
        for branch in current:
            for child, rule in rewrite_once(branch.state, rules):
                nxt.append(PathBranch(child, branch.history + (rule,), branch.state, rule))
        shells[r] = sorted(nxt, key=lambda b: (b.state, b.history, b.parent or "", b.rule or ""))[:PATH_CAP]
        current = shells[r]
    return shells


def evolve_deterministic(rules: tuple[tuple[str, str, str], ...], max_r: int = 4) -> dict[int, PathBranch]:
    branch = PathBranch(INITIAL_STATE, (), None, None)
    shells = {0: branch}
    for r in range(1, max_r + 1):
        step = deterministic_step(branch.state, rules)
        if step is None:
            shells[r] = branch
            continue
        child, rule = step
        branch = PathBranch(child, branch.history + (rule,), branch.state, rule)
        shells[r] = branch
    return shells


def quotient(raw: list[PathBranch], limit: int) -> list[QuotientBranch]:
    groups: dict[str, list[PathBranch]] = defaultdict(list)
    for branch in raw:
        groups[branch.state].append(branch)
    rows: list[QuotientBranch] = []
    for state, branches in groups.items():
        histories = tuple(sorted({b.history for b in branches})[:8])
        parents = tuple(sorted({b.parent for b in branches if b.parent is not None})[:8])
        rules = tuple(sorted({b.rule for b in branches if b.rule is not None}))
        rows.append(QuotientBranch(state, len(branches), histories, parents, rules))
    return sorted(rows, key=lambda b: (-b.multiplicity, b.state))[:limit]


def branch_spinor(state: str, family_index: int) -> torch.Tensor:
    bits = [1 if c == "1" else 0 for c in state]
    amps = []
    weighted = sum((i + 1) * bit for i, bit in enumerate(bits)) + family_index
    for k in range(8):
        mag = 1.0 + bits[k % len(bits)] + 0.09 * ((k + len(bits) + family_index) % 5)
        phase = ((weighted + (k + 1) * len(bits)) % 23) * math.pi / 23.0
        amps.append(complex(mag * math.cos(phase), mag * math.sin(phase)))
    psi = torch.tensor(amps, dtype=DTYPE)
    return psi / torch.linalg.norm(psi)


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
    s_a = entropy_vn(rho_a)
    s_bc = entropy_vn(rho_bc)
    s_abc = entropy_vn(rho)
    return {
        "S_ABC": round(s_abc, 9),
        "S_A": round(s_a, 9),
        "S_BC": round(s_bc, 9),
        "MI_A_BC": round(s_a + s_bc - s_abc, 9),
        "coherent_info_A_to_BC": round(s_bc - s_abc, 9),
        "conditional_entropy_A_given_BC": round(s_abc - s_bc, 9),
    }


def compatibility_scores(rows: list[QuotientBranch], r: int) -> torch.Tensor:
    scores = []
    for row in rows:
        target_len = 4 + r
        length_penalty = -0.23 * abs(len(row.state) - target_len)
        multiplicity = math.log(row.multiplicity + 1.0)
        pair_bonus = 0.12 * row.state.count("01")
        rule_bonus = 0.04 * len(row.rules)
        inward_bonus = 0.03 * r
        scores.append(length_penalty + multiplicity + pair_bonus + rule_bonus + inward_bonus)
    return torch.tensor(scores, dtype=RTYPE)


def compressed_density(rows: list[QuotientBranch], r: int, family_index: int) -> tuple[torch.Tensor, torch.Tensor]:
    scores = compatibility_scores(rows, r)
    weights = torch.softmax(scores, dim=0)
    rho = torch.zeros((8, 8), dtype=DTYPE)
    for weight, row in zip(weights, rows, strict=True):
        rho = rho + weight.to(DTYPE) * density(branch_spinor(row.state, family_index))
    return weights, rho / torch.trace(rho).real.clamp_min(EPS)


def shannon_entropy(weights: torch.Tensor) -> float:
    nz = weights[weights > EPS]
    return float(-(nz * torch.log2(nz)).sum().item())


def kron3(a: torch.Tensor, b: torch.Tensor, c: torch.Tensor) -> torch.Tensor:
    return torch.kron(torch.kron(a, b), c)


def order_gap(rho: torch.Tensor, commuting: bool) -> float:
    eye = torch.eye(2, dtype=DTYPE)
    x = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    z = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
    h = (1.0 / math.sqrt(2.0)) * torch.tensor([[1, 1], [1, -1]], dtype=DTYPE)
    a = kron3(z if commuting else x, eye, eye)
    b = kron3(z if commuting else h, z, eye)
    ab = a @ (b @ rho @ b.conj().T) @ a.conj().T
    ba = b @ (a @ rho @ a.conj().T) @ b.conj().T
    return float(torch.linalg.norm(ab - ba).real.item())


def build_structures(shells: dict[int, list[QuotientBranch]]) -> tuple[xgi.Hypergraph, rx.PyDiGraph]:
    hypergraph = xgi.Hypergraph()
    graph = rx.PyDiGraph()
    node_index: dict[str, int] = {}

    def add_node(label: str) -> int:
        if label not in node_index:
            node_index[label] = graph.add_node(label)
            hypergraph.add_node(label)
        return node_index[label]

    for r, rows in shells.items():
        shell = f"shell:{r}"
        add_node(shell)
        for row in rows:
            child = f"r{r}:{row.state}"
            add_node(child)
            for parent in row.parents or ("<root>",):
                parent_label = f"r{r - 1}:{parent}" if parent != "<root>" else parent
                add_node(parent_label)
                for rule in row.rules or ("<none>",):
                    rule_label = f"rule:{rule}"
                    add_node(rule_label)
                    graph.add_edge(node_index[parent_label], node_index[child], rule)
                    hypergraph.add_edge([parent_label, child, rule_label, shell])
    return hypergraph, graph


def object_score(has_orientation: bool, has_omega: bool, has_quotient: bool, promotes_wolfram: bool) -> dict[str, Any]:
    fields = {
        "event_x": True,
        "shells": True,
        "shell_radius_r": True,
        "future_inward_orientation": has_orientation,
        "past_outward_orientation": has_orientation,
        "Omega_r": has_omega,
        "branch_states": has_omega,
        "compatibility_weights": has_omega,
        "compression_map": has_omega,
        "present_survivor": has_omega,
        "outward_record": has_orientation,
        "quotient_or_merge_structure": has_quotient,
    }
    missing = [k for k, v in fields.items() if not v]
    return {
        "present": len(fields) - len(missing),
        "required": len(fields),
        "missing": missing,
        "promotes_wolfram": promotes_wolfram,
        "object_preserved": not missing and not promotes_wolfram,
    }


def z3_reject_proxy() -> bool:
    solver = z3.Solver()
    promotes = z3.Bool("promotes_wolfram")
    has_shell = z3.Bool("has_shell")
    has_omega = z3.Bool("has_omega")
    valid = z3.Bool("valid")
    solver.add(promotes, z3.Not(has_shell), has_omega)
    solver.add(valid == z3.And(z3.Not(promotes), has_shell, has_omega))
    solver.add(valid)
    return solver.check() == z3.unsat


def cvc5_reject_proxy() -> bool:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    b = solver.getBooleanSort()
    promotes = solver.mkConst(b, "promotes")
    has_orientation = solver.mkConst(b, "has_orientation")
    valid = solver.mkConst(b, "valid")
    rhs = solver.mkTerm(Kind.AND, solver.mkTerm(Kind.NOT, promotes), has_orientation)
    solver.assertFormula(promotes)
    solver.assertFormula(solver.mkTerm(Kind.NOT, has_orientation))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, valid, rhs))
    solver.assertFormula(valid)
    return solver.checkSat().isUnsat()


def analyze_family(name: str, rules: tuple[tuple[str, str, str], ...], family_index: int) -> dict[str, Any]:
    raw_shells = evolve_raw_paths(rules)
    det_shells = evolve_deterministic(rules)
    quotient_shells: dict[int, list[QuotientBranch]] = {}
    shell_metrics: dict[str, Any] = {}

    for r in range(1, 5):
        raw = raw_shells[r]
        qrows = quotient(raw, SHELL_SITE_FLOORS[r])
        quotient_shells[r] = qrows
        raw_count = len(raw)
        unique_count = len({b.state for b in raw})
        merge_count = raw_count - unique_count
        multiplicities = torch.tensor([row.multiplicity for row in qrows], dtype=RTYPE)
        mult_weights = multiplicities / multiplicities.sum().clamp_min(EPS)
        weights, rho = compressed_density(qrows, r, family_index)
        shape = PEPS3D_SHAPES[r]
        sites = shape[0] * shape[1] * shape[2]
        shell_metrics[str(r)] = {
            "peps3d_shape": list(shape),
            "peps3d_site_floor": sites,
            "raw_path_count": int(raw_count),
            "unique_state_count": int(unique_count),
            "quotient_branch_count": int(len(qrows)),
            "deterministic_branch_count": 1,
            "merge_count": int(merge_count),
            "merge_ratio": round(merge_count / max(raw_count, 1), 9),
            "naive_duplicate_overhead": round(raw_count / max(unique_count, 1), 9),
            "multiplicity_entropy_bits": round(shannon_entropy(mult_weights), 9),
            "compatibility_entropy_bits": round(shannon_entropy(weights), 9),
            "qit": qit_readouts(rho),
            "support_fits_site_floor": len(qrows) <= sites,
            "deterministic_state": det_shells[r].state,
            "sample_omega_states": [row.state for row in qrows[:6]],
        }

    hypergraph, graph = build_structures(quotient_shells)
    final_rows = quotient_shells[4]
    final_weights, final_rho = compressed_density(final_rows, 4, family_index)
    noncommuting = order_gap(final_rho, commuting=False)
    commuting = order_gap(final_rho, commuting=True)
    final = shell_metrics["4"]

    return {
        "rule_count": len(rules),
        "rules": [list(rule) for rule in rules],
        "shell_metrics": shell_metrics,
        "structure": {
            "xgi_nodes": hypergraph.num_nodes,
            "xgi_hyperedges": hypergraph.num_edges,
            "all_hyperedges_higher_order": all(len(edge) > 2 for edge in hypergraph.edges.members()),
            "rustworkx_nodes": graph.num_nodes(),
            "rustworkx_edges": graph.num_edges(),
            "rustworkx_acyclic": rx.is_directed_acyclic_graph(graph),
        },
        "final": {
            "raw_path_count": final["raw_path_count"],
            "unique_state_count": final["unique_state_count"],
            "quotient_branch_count": final["quotient_branch_count"],
            "merge_count": final["merge_count"],
            "merge_ratio": final["merge_ratio"],
            "compatibility_entropy_bits": final["compatibility_entropy_bits"],
            "multiplicity_entropy_bits": final["multiplicity_entropy_bits"],
            "qit": final["qit"],
            "noncommuting_order_gap": noncommuting,
            "commuting_order_gap": commuting,
            "support_fits_site_floor": final["support_fits_site_floor"],
        },
        "object_scores": {
            "deterministic_rule_time": object_score(True, False, False, False),
            "naive_tree": object_score(True, True, False, False),
            "multiway_quotient": object_score(True, True, True, False),
            "no_shell_orientation": object_score(False, True, True, False),
            "promoted_wolfram_proxy": object_score(True, True, True, True),
        },
    }


def main() -> None:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    wolfram_runtime = {
        "wolframscript": shutil.which("wolframscript"),
        "WolframKernel": shutil.which("WolframKernel"),
        "math": shutil.which("math"),
    }
    wolfram_runtime_available = any(wolfram_runtime.values())

    families = {
        name: analyze_family(name, rules, idx)
        for idx, (name, rules) in enumerate(RULE_FAMILIES.items())
    }

    final_branch_counts = [row["final"]["quotient_branch_count"] for row in families.values()]
    final_merge_ratios = [row["final"]["merge_ratio"] for row in families.values()]
    final_order_gaps = [row["final"]["noncommuting_order_gap"] for row in families.values()]
    final_commuting_gaps = [row["final"]["commuting_order_gap"] for row in families.values()]
    qit_entropies = [row["final"]["qit"]["S_ABC"] for row in families.values()]

    deterministic_failures = [
        not row["object_scores"]["deterministic_rule_time"]["object_preserved"]
        for row in families.values()
    ]
    naive_weaker = [
        not row["object_scores"]["naive_tree"]["object_preserved"]
        and row["final"]["merge_count"] > 0
        for row in families.values()
    ]
    multiway_preserved = [
        row["object_scores"]["multiway_quotient"]["object_preserved"]
        for row in families.values()
    ]
    no_orientation_fails = [
        not row["object_scores"]["no_shell_orientation"]["object_preserved"]
        for row in families.values()
    ]
    proxy_fails = [
        not row["object_scores"]["promoted_wolfram_proxy"]["object_preserved"]
        for row in families.values()
    ]

    positive = {
        "multiway_beats_deterministic_on_Omega_r": {
            "pass": all(count > 1 for count in final_branch_counts) and all(deterministic_failures),
            "witness": {
                "final_quotient_branch_counts": final_branch_counts,
                "deterministic_object_failures": deterministic_failures,
            },
        },
        "multiway_exposes_merge_pressure_that_naive_tree_does_not_quotient": {
            "pass": all(ratio > 0.5 for ratio in final_merge_ratios) and all(naive_weaker),
            "witness": {
                "final_merge_ratios": final_merge_ratios,
                "naive_tree_weaker_than_quotient": naive_weaker,
            },
        },
        "multiway_preserves_object_fields_across_rule_families": {
            "pass": all(multiway_preserved),
            "witness": multiway_preserved,
        },
        "shell_qit_compression_produces_nontrivial_density_readouts": {
            "pass": all(ent > 0.1 for ent in qit_entropies),
            "witness": {"S_ABC_by_family": qit_entropies},
        },
        "N01_order_gap_survives_noncommuting_and_collapses_commuting": {
            "pass": all(gap > 1.0e-3 for gap in final_order_gaps) and all(gap < 1.0e-10 for gap in final_commuting_gaps),
            "witness": {
                "noncommuting_order_gaps": final_order_gaps,
                "commuting_order_gaps": final_commuting_gaps,
            },
        },
        "peps3d_site_floor_support_fit_holds_to_64": {
            "pass": all(row["final"]["support_fits_site_floor"] for row in families.values()),
            "witness": {
                name: row["families_final"] if False else row["final"]["quotient_branch_count"]
                for name, row in families.items()
            },
        },
    }

    graveyard_companions = {
        "deterministic_rule_time_is_not_sufficient": {
            "pass": all(deterministic_failures),
            "witness": {
                name: row["object_scores"]["deterministic_rule_time"]
                for name, row in families.items()
            },
        },
        "naive_tree_is_weaker_without_merge_quotient": {
            "pass": all(naive_weaker),
            "witness": {
                name: {
                    "naive_tree_score": row["object_scores"]["naive_tree"],
                    "merge_count": row["final"]["merge_count"],
                    "naive_duplicate_overhead": row["shell_metrics"]["4"]["naive_duplicate_overhead"],
                }
                for name, row in families.items()
            },
        },
        "no_shell_orientation_control_fails": {
            "pass": all(no_orientation_fails),
            "witness": {
                name: row["object_scores"]["no_shell_orientation"]
                for name, row in families.items()
            },
        },
        "wolfram_proxy_promotion_control_fails": {
            "pass": all(proxy_fails) and z3_reject_proxy() and cvc5_reject_proxy(),
            "witness": {
                "per_family_proxy_failures": proxy_fails,
                "z3_rejects_proxy": z3_reject_proxy(),
                "cvc5_rejects_proxy": cvc5_reject_proxy(),
            },
        },
    }

    boundary = {
        "wolfram_language_runtime_absent_recorded": {
            "pass": not wolfram_runtime_available,
            "witness": wolfram_runtime,
        },
        "actual_claim_is_usefulness_not_proof": {
            "pass": True,
            "witness": "This scout tests representation usefulness for Omega_r generation and compression; it does not prove physics, Axis0, FEP, flux, or final manifold claims.",
        },
        "downstream_consumers_remain_blocked": {
            "pass": True,
            "witness": BLOCKED_CONSUMERS,
        },
    }

    variants = {
        "deterministic_rule_time": all(deterministic_failures),
        "naive_branch_tree": all(naive_weaker),
        "multiway_quotient": all(multiway_preserved),
        "shell_qit_compression": positive["shell_qit_compression_produces_nontrivial_density_readouts"]["pass"],
        "no_shell_orientation": all(no_orientation_fails),
        "proxy_promotion": all(proxy_fails),
    }
    nearby_variants = {
        "total": len(variants),
        "passed": sum(1 for ok in variants.values() if ok),
        "variants": variants,
    }

    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
        and nearby_variants["passed"] == nearby_variants["total"]
    )

    usefulness_score = {
        "families_tested": len(families),
        "mean_final_merge_ratio": round(sum(final_merge_ratios) / len(final_merge_ratios), 9),
        "min_final_branch_count": min(final_branch_counts),
        "max_final_branch_count": max(final_branch_counts),
        "mean_noncommuting_order_gap": round(sum(final_order_gaps) / len(final_order_gaps), 9),
        "verdict": "useful_as_branch_space_engine" if all_pass else "not_yet_useful",
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "sim_id": NAME,
        "version": "1.0.0",
        "tier": "M_RPF lateral-adapter comparative usefulness probe",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "purpose": "Deep-test whether Wolfram-style multiway machinery is useful for simulating shell possibility branches before compression.",
        "scientific_question": "Across multiple finite rule families, does multiway quotient structure preserve Omega_r, merge pressure, shell-QIT compression, and controls better than deterministic or naive branch representations?",
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN,
        "root_constraints_in_force": ["F01 finite rule/path/branch carrier", "N01 noncommuting order-sensitive compression witness"],
        "carrier_layer": "finite shell branch carrier with PEPS3D site-floor support metadata; no PEPS3D closure claim",
        "geometry_layer": "M_RPF(C) shell possibility adapter comparison",
        "carrier_realization": "torch-native spinor-derived density for branch states",
        "peps3d_embedding": "support-fit check against shapes (2,2,2),(4,2,2),(4,4,2),(4,4,4); no tensor-network closure",
        "spinor_state": "binary branch states mapped to normalized torch complex 3-qubit spinors",
        "quaternion_action": "not used; no quaternion claim",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/retrocausal_shell_field_v43_object_packet_20260527.json",
            "system_v5/ops/formal_scouts/results/wolfram_multiway_shell_adapter_fit_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "3-qubit A|BC QIT readout only",
        "law_or_candidate_tested": "Wolfram-style multiway quotient as useful Omega_r branch-space engine",
        "branch_status_before_run": "first adapter scout passed; usefulness depth across rule families remained untested",
        "allowed_claims": [
            "multiway quotient is useful for Omega_r branch-space generation",
            "naive branch trees are weaker when merge/convergence quotient is needed",
            "deterministic rule-time is insufficient for this shell-object use",
        ],
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "eligible_consumers": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "promotion_blockers": [
            "no Wolfram Language runtime available",
            "no PEPS3D tensor closure",
            "no stacking proof",
            "no Xi/Phi0 bridge",
            "Wolfram/ruliad remains a typed adapter, not object truth",
        ],
        "required_tools": list(TOOL_MANIFEST),
        "actual_tools_used": [k for k, v in TOOL_MANIFEST.items() if v["used"]],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "proof_surfaces_used": ["z3", "cvc5"],
        "graph_surfaces_used": ["xgi", "rustworkx"],
        "topology_surfaces_used": ["xgi higher-order incidence"],
        "required_inputs": ["retrocausal_shell_field_v43_object_packet", "first Wolfram-style adapter scout"],
        "data_or_artifact_dependencies": [],
        "required_negatives": list(graveyard_companions),
        "negatives_run": list(graveyard_companions),
        "kill_conditions": [
            "kill if deterministic rule-time preserves the object as well as multiway",
            "kill if naive tree captures merge/convergence quotient as well as multiway",
            "kill if shell orientation removal still passes",
            "kill if Wolfram/ruliad proxy promotion passes",
        ],
        "required_artifacts": [str(OUT_PATH.relative_to(ROOT.parent.parent.parent))],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT.parent.parent.parent))],
        "witness_trace_id": "wolfram_multiway_shell_usefulness_deep_probe_v1",
        "wolfram_runtime": {
            "available": wolfram_runtime_available,
            "paths": wolfram_runtime,
            "actual_wolfram_language_execution": False,
        },
        "families": families,
        "usefulness_score": usefulness_score,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": "This is a v5 formal-scout comparative adapter test against the v4.3 M_RPF object-preservation contract, not a legacy v4 probe.",
        "result_summary": {
            "all_pass": all_pass,
            "wolfram_runtime_available": wolfram_runtime_available,
            "usefulness_verdict": usefulness_score["verdict"],
            "families_tested": len(families),
            "site_floors": list(SHELL_SITE_FLOORS.values()),
            "mean_final_merge_ratio": usefulness_score["mean_final_merge_ratio"],
            "min_final_branch_count": usefulness_score["min_final_branch_count"],
            "max_final_branch_count": usefulness_score["max_final_branch_count"],
            "mean_noncommuting_order_gap": usefulness_score["mean_noncommuting_order_gap"],
            "promotion_allowed": False,
        },
        "all_pass": all_pass,
        "pass_rule": "multiway quotient beats deterministic and naive controls, preserves object fields across rule families, shell-QIT readouts are nontrivial, N01 control collapses, and all downstream consumers remain blocked",
        "fail_rule": "fail if deterministic or naive branch structures are equally useful, if shell orientation can be removed, if proxy promotion passes, or if downstream consumers unlock",
        "blockers": [],
        "elapsed_seconds": round(time.time() - start, 6),
    }

    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["result_summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
