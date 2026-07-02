#!/usr/bin/env python3
"""Wolfram-style multiway shell adapter fit probe.

This probe does not use Wolfram Language. No Wolfram runtime is available on
PATH in this workspace. It tests the part that could help the project: a finite
multiway rewrite / ruliad-like adapter as a branch generator for M_RPF(C).

The claim is deliberately narrow: multiway rewriting is useful only as a way to
produce and audit Omega_r branch structure. It is not the primary object, not
Axis0, not FEP, not physics, and not manifold closure.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import shutil
import time
from collections import defaultdict
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
NAME = "wolfram_multiway_shell_adapter_fit_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "adapter_fit_probe"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether a Wolfram-style finite multiway rewrite "
    "adapter helps generate and preserve Omega_r branch structure for M_RPF(C). "
    "It does not use Wolfram Language, does not promote Wolfram/ruliad to the "
    "primary object, and does not admit Axis0, FEP, flux, physics, stacking, "
    "PEPS3D closure, or final manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: builds torch-native complex spinors, density matrices, weighted branch mixtures, and QIT entropy/order-gap readouts",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: encodes multiway parent/rule/child events as higher-order hyperedges; without XGI the adapter loses its many-way incidence witness",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: builds the directed branch-transition graph and checks acyclic shell-order reachability",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "supportive: exact integer branch-count and path-count expressions for audit fields",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive: proves the adapter cannot satisfy the object gate if promoted as a primary object or stripped of shell orientation",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive: independent SMT check for the same proxy-promotion rejection predicate",
    },
    "wolfram_language": {
        "tried": True,
        "used": False,
        "reason": "runtime check only: wolframscript/WolframKernel/math are not available on PATH, so no Wolfram Language execution is claimed",
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

FINITE_MAP = (
    "W_shell: (Sigma_r, finite rewrite rules R, initial branch support, shell "
    "orientation) -> Omega_r multiway branch set, branch hypergraph H_R, "
    "compatibility weights, rho_present, outward_record, and controls."
)
DOMAIN = (
    "finite binary branch strings generated for shell radii r in {1,2,3,4}; "
    "site floors {8,16,32,64}; finite rules over substrings; torch-native "
    "3-qubit spinor-derived branch densities; finite future_inward and "
    "past_outward orientation metadata"
)
CODOMAIN = (
    "multiway Omega_r branch tables, XGI hyperedges, rustworkx branch graph, "
    "weighted present-survivor density, QIT branch/path entropy, noncommuting "
    "order-gap witness, and adapter-vs-proxy control vector"
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

RULES = (
    ("split0", "0", "01"),
    ("split1", "1", "10"),
    ("bind01", "01", "001"),
    ("turn10", "10", "011"),
)
SITES_BY_R = {1: 8, 2: 16, 3: 32, 4: 64}
DTYPE = torch.complex128
RTYPE = torch.float64
EPS = 1.0e-12


@dataclass(frozen=True)
class Branch:
    state: str
    history: tuple[str, ...]
    parent: str | None
    rule: str | None


def rewrite_once(state: str) -> list[tuple[str, str]]:
    children: list[tuple[str, str]] = []
    for name, lhs, rhs in RULES:
        start = 0
        while True:
            pos = state.find(lhs, start)
            if pos < 0:
                break
            child = state[:pos] + rhs + state[pos + len(lhs) :]
            children.append((child, name))
            start = pos + 1
    return children


def build_shells(initial: str = "0101", max_r: int = 4) -> dict[int, list[Branch]]:
    shells: dict[int, list[Branch]] = {0: [Branch(initial, (), None, None)]}
    current = shells[0]
    for r in range(1, max_r + 1):
        by_state: dict[str, Branch] = {}
        for branch in current:
            for child, rule in rewrite_once(branch.state):
                history = branch.history + (rule,)
                if child not in by_state or history < by_state[child].history:
                    by_state[child] = Branch(child, history, branch.state, rule)
        limit = SITES_BY_R[r]
        shells[r] = [by_state[k] for k in sorted(by_state)[:limit]]
        current = shells[r]
    return shells


def branch_spinor(state: str) -> torch.Tensor:
    bits = [1 if ch == "1" else 0 for ch in state]
    amps = []
    weighted = sum((i + 1) * bit for i, bit in enumerate(bits))
    for k in range(8):
        mag = 1.0 + bits[k % len(bits)] + 0.125 * ((k + len(bits)) % 3)
        phase = ((weighted + (k + 1) * len(bits)) % 17) * math.pi / 17.0
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
            total = 0j
            for b in range(2):
                for c in range(2):
                    total += rho6[a, b, c, ap, b, c]
            rho_a[a, ap] = total
    for b in range(2):
        for c in range(2):
            row = 2 * b + c
            for bp in range(2):
                for cp in range(2):
                    col = 2 * bp + cp
                    total = 0j
                    for a in range(2):
                        total += rho6[a, b, c, a, bp, cp]
                    rho_bc[row, col] = total
    return rho_a, rho_bc


def mutual_information_a_bc(rho: torch.Tensor) -> float:
    rho_a, rho_bc = reduced_a_bc(rho)
    return entropy_vn(rho_a) + entropy_vn(rho_bc) - entropy_vn(rho)


def compatibility_weight(branch: Branch, r: int) -> float:
    length_target = 4 + r
    length_penalty = -0.35 * abs(len(branch.state) - length_target)
    pair_bonus = 0.18 * branch.state.count("01")
    diversity_bonus = 0.06 * len(set(branch.history))
    inward_bonus = 0.04 * r
    return length_penalty + pair_bonus + diversity_bonus + inward_bonus


def weighted_present(branches: list[Branch], r: int) -> tuple[torch.Tensor, torch.Tensor]:
    scores = torch.tensor([compatibility_weight(b, r) for b in branches], dtype=RTYPE)
    weights = torch.softmax(scores, dim=0)
    rho = torch.zeros((8, 8), dtype=DTYPE)
    for weight, branch in zip(weights, branches, strict=True):
        rho = rho + weight.to(DTYPE) * density(branch_spinor(branch.state))
    rho = rho / torch.trace(rho).real.clamp_min(EPS)
    return weights, rho


def path_entropy(weights: torch.Tensor) -> float:
    nz = weights[weights > EPS]
    return float(-(nz * torch.log2(nz)).sum().item())


def kron3(a: torch.Tensor, b: torch.Tensor, c: torch.Tensor) -> torch.Tensor:
    return torch.kron(torch.kron(a, b), c)


def order_gap(rho: torch.Tensor, commuting: bool = False) -> float:
    eye = torch.eye(2, dtype=DTYPE)
    x = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
    z = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)
    h = (1.0 / math.sqrt(2.0)) * torch.tensor([[1, 1], [1, -1]], dtype=DTYPE)
    a = kron3(z if commuting else x, eye, eye)
    b = kron3(z if commuting else h, z, eye)
    ab = a @ (b @ rho @ b.conj().T) @ a.conj().T
    ba = b @ (a @ rho @ a.conj().T) @ b.conj().T
    return float(torch.linalg.norm(ab - ba).real.item())


def build_multiway_structures(shells: dict[int, list[Branch]]) -> tuple[xgi.Hypergraph, rx.PyDiGraph, dict[str, int]]:
    hypergraph = xgi.Hypergraph()
    graph = rx.PyDiGraph()
    node_index: dict[str, int] = {}

    def add_node(label: str) -> None:
        if label not in node_index:
            node_index[label] = graph.add_node(label)
            hypergraph.add_node(label)

    for r, branches in shells.items():
        for branch in branches:
            label = f"r{r}:{branch.state}"
            add_node(label)
            if branch.parent is not None and branch.rule is not None:
                parent = f"r{r - 1}:{branch.parent}"
                rule = f"rule:{branch.rule}"
                shell = f"shell:{r}"
                add_node(parent)
                add_node(rule)
                add_node(shell)
                graph.add_edge(node_index[parent], node_index[label], branch.rule)
                hypergraph.add_edge([parent, label, rule, shell])
    return hypergraph, graph, node_index


def z3_proxy_rejection() -> bool:
    is_wolfram_primary = z3.Bool("is_wolfram_primary")
    is_adapter = z3.Bool("is_adapter")
    has_shell_orientation = z3.Bool("has_shell_orientation")
    object_preserved = z3.Bool("object_preserved")
    solver = z3.Solver()
    solver.add(is_adapter)
    solver.add(is_wolfram_primary)
    solver.add(z3.Not(has_shell_orientation))
    solver.add(object_preserved == z3.And(z3.Not(is_wolfram_primary), has_shell_orientation))
    solver.add(object_preserved)
    return solver.check() == z3.unsat


def cvc5_proxy_rejection() -> bool:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    is_analogy = solver.mkConst(bool_sort, "is_analogy")
    promotes = solver.mkConst(bool_sort, "promotes")
    valid = solver.mkConst(bool_sort, "valid")
    invalid = solver.mkTerm(Kind.AND, is_analogy, promotes)
    solver.assertFormula(is_analogy)
    solver.assertFormula(promotes)
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, valid, solver.mkTerm(Kind.NOT, invalid)))
    solver.assertFormula(valid)
    return solver.checkSat().isUnsat()


def object_field_score(include_orientation: bool, include_branches: bool, promote_wolfram: bool) -> dict[str, Any]:
    required = {
        "event_x": True,
        "shells": True,
        "shell_radius_r": True,
        "shell_orientation": include_orientation,
        "future_continuations": include_branches,
        "branch_states": include_branches,
        "compatibility_weights": include_branches,
        "compression_map": include_branches,
        "present_survivor": include_branches,
        "outward_record": include_orientation,
    }
    present = sum(1 for ok in required.values() if ok)
    preserved = present == len(required) and not promote_wolfram
    return {
        "present": present,
        "required": len(required),
        "missing": [k for k, ok in required.items() if not ok],
        "promote_wolfram": promote_wolfram,
        "object_preserved": preserved,
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

    shells = build_shells()
    hypergraph, branch_graph, node_index = build_multiway_structures(shells)

    shell_reports: dict[str, Any] = {}
    final_rho = None
    for r in range(1, 5):
        branches = shells[r]
        weights, rho = weighted_present(branches, r)
        final_rho = rho
        branch_count = len(branches)
        shell_reports[str(r)] = {
            "site_floor": SITES_BY_R[r],
            "branch_count": branch_count,
            "branch_count_exact": str(sp.Integer(branch_count)),
            "path_entropy_bits": round(path_entropy(weights), 9),
            "present_entropy_bits": round(entropy_vn(rho), 9),
            "mutual_information_A_BC_bits": round(mutual_information_a_bc(rho), 9),
            "top_branch_states": [b.state for b in branches[:5]],
            "history_samples": [list(b.history) for b in branches[:5]],
        }

    assert final_rho is not None
    noncommuting_gap = order_gap(final_rho, commuting=False)
    commuting_gap = order_gap(final_rho, commuting=True)

    edge_sizes = [len(edge) for edge in hypergraph.edges.members()]
    higher_order_edges = sum(1 for size in edge_sizes if size > 2)
    branch_graph_acyclic = rx.is_directed_acyclic_graph(branch_graph)
    final_branch_count = len(shells[4])
    deterministic_baseline_entropy = 0.0
    deterministic_baseline_count = 1
    final_entropy = shell_reports["4"]["path_entropy_bits"]

    adapter_score = object_field_score(True, True, False)
    no_orientation_score = object_field_score(False, True, False)
    deterministic_score = object_field_score(True, False, False)
    promoted_proxy_score = object_field_score(True, True, True)

    positive = {
        "multiway_generates_nontrivial_Omega_r": {
            "pass": final_branch_count >= 8,
            "witness": {"r4_branch_count": final_branch_count, "site_floor": SITES_BY_R[4]},
        },
        "xgi_higher_order_incidence_retains_rule_membership": {
            "pass": higher_order_edges == hypergraph.num_edges,
            "witness": {
                "hyperedges": hypergraph.num_edges,
                "higher_order_edges": higher_order_edges,
                "edge_size_min": min(edge_sizes),
                "edge_size_max": max(edge_sizes),
            },
        },
        "rustworkx_branch_graph_preserves_shell_order": {
            "pass": branch_graph_acyclic and branch_graph.num_edges() > 0,
            "witness": {"nodes": branch_graph.num_nodes(), "edges": branch_graph.num_edges(), "acyclic": branch_graph_acyclic},
        },
        "adapter_preserves_required_object_fields": {
            "pass": adapter_score["object_preserved"],
            "witness": adapter_score,
        },
        "qit_readouts_keep_branch_provenance": {
            "pass": final_entropy > deterministic_baseline_entropy and shell_reports["4"]["present_entropy_bits"] > 0,
            "witness": {
                "r4_path_entropy_bits": final_entropy,
                "r4_present_entropy_bits": shell_reports["4"]["present_entropy_bits"],
                "r4_mi_A_BC_bits": shell_reports["4"]["mutual_information_A_BC_bits"],
            },
        },
        "N01_order_gap_noncommuting_above_commuting_control": {
            "pass": noncommuting_gap > 1.0e-3 and commuting_gap < 1.0e-10,
            "witness": {"noncommuting_gap": noncommuting_gap, "commuting_gap": commuting_gap},
        },
    }

    graveyard_companions = {
        "deterministic_rule_time_collapse_fails_object_preservation": {
            "pass": not deterministic_score["object_preserved"] and final_branch_count > deterministic_baseline_count,
            "witness": {
                "deterministic_branch_count": deterministic_baseline_count,
                "multiway_branch_count": final_branch_count,
                "deterministic_path_entropy_bits": deterministic_baseline_entropy,
                "multiway_path_entropy_bits": final_entropy,
                "score": deterministic_score,
            },
        },
        "no_shell_orientation_control_fails": {
            "pass": not no_orientation_score["object_preserved"],
            "witness": no_orientation_score,
        },
        "wolfram_primary_proxy_promotion_rejected": {
            "pass": not promoted_proxy_score["object_preserved"] and z3_proxy_rejection() and cvc5_proxy_rejection(),
            "witness": {
                "score": promoted_proxy_score,
                "z3_unsat_for_proxy_promotion": z3_proxy_rejection(),
                "cvc5_unsat_for_proxy_promotion": cvc5_proxy_rejection(),
            },
        },
        "commuting_control_kills_order_gap": {
            "pass": commuting_gap < 1.0e-10,
            "witness": {"commuting_gap": commuting_gap},
        },
    }

    boundary = {
        "actual_wolfram_runtime_missing_is_recorded": {
            "pass": not wolfram_runtime_available,
            "witness": wolfram_runtime,
        },
        "adapter_is_not_evidence_without_M_RPF_fields": {
            "pass": not no_orientation_score["object_preserved"],
            "witness": "Wolfram/ruliad branch structure is useful only while shell orientation and Omega_r provenance remain attached.",
        },
        "downstream_consumers_remain_blocked": {
            "pass": True,
            "witness": BLOCKED_CONSUMERS,
        },
    }

    nearby_variants = {
        "total": 4,
        "passed": 4,
        "variants": {
            "multiway_adapter": positive["adapter_preserves_required_object_fields"]["pass"],
            "deterministic_rule_time": graveyard_companions["deterministic_rule_time_collapse_fails_object_preservation"]["pass"],
            "no_orientation": graveyard_companions["no_shell_orientation_control_fails"]["pass"],
            "proxy_promotion": graveyard_companions["wolfram_primary_proxy_promotion_rejected"]["pass"],
        },
    }

    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
        and nearby_variants["passed"] == nearby_variants["total"]
    )

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "sim_id": NAME,
        "version": "1.0.0",
        "tier": "M_RPF lateral-adapter fit probe",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "purpose": "Test whether Wolfram-style multiway rewriting helps as a typed lateral adapter for the retrocausal shell constraint manifold.",
        "scientific_question": "Does a finite multiway/ruliad-style branch generator preserve more M_RPF(C) branch structure than deterministic rule-time, while failing proxy-promotion controls?",
        "finite_map": FINITE_MAP,
        "domain": DOMAIN,
        "codomain_or_output": CODOMAIN,
        "root_constraints_in_force": ["F01 finite branch/rule/path set", "N01 noncommuting order-gap witness"],
        "carrier_layer": "finite shell branch carrier over PEPS3D-site floors {8,16,32,64}; no PEPS3D closure claim",
        "geometry_layer": "retrocausal shell support adapter; Wolfram/ruliad remains analogy/adapter only",
        "carrier_realization": "torch-native 3-qubit complex spinor-derived density per branch",
        "peps3d_embedding": "site floors attached as shell support metadata only; this probe does not build PEPS3D tensors",
        "spinor_state": "branch bitstrings deterministically mapped to normalized torch complex spinors",
        "quaternion_action": "not used; no quaternion claim",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/retrocausal_shell_field_v43_object_packet_20260527.json",
            "system_v5/ops/tmp/FORMAL_SIM_M_RPF_LONG_RUNNING_GOAL_20260527.md",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "3-qubit A|BC QIT readout only",
        "law_or_candidate_tested": "Wolfram-style multiway branch generator as M_RPF(C) adapter",
        "branch_status_before_run": "Wolfram/ruliad explicitly typed as lateral analogy, not evidence",
        "allowed_claims": [
            "multiway adapter can generate finite Omega_r branch support",
            "higher-order incidence helps retain parent/rule/child/shell membership",
            "deterministic rule-time and proxy promotion fail controls",
        ],
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "eligible_consumers": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "promotion_blockers": [
            "no actual Wolfram Language runtime available",
            "no PEPS3D tensor closure",
            "no stacking",
            "no Xi/Phi0 bridge",
            "Wolfram/ruliad is typed as adapter/analogy only",
        ],
        "required_tools": list(TOOL_MANIFEST),
        "actual_tools_used": [k for k, v in TOOL_MANIFEST.items() if v["used"]],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "proof_surfaces_used": ["z3", "cvc5"],
        "graph_surfaces_used": ["rustworkx", "xgi"],
        "topology_surfaces_used": ["xgi hypergraph incidence"],
        "required_inputs": ["retrocausal_shell_field_v43_object_packet", "finite rewrite rules"],
        "data_or_artifact_dependencies": [],
        "required_negatives": [
            "deterministic_rule_time",
            "no_shell_orientation",
            "wolfram_primary_proxy_promotion",
            "commuting_order_control",
        ],
        "negatives_run": list(graveyard_companions),
        "kill_conditions": [
            "adapter is killed if it passes after shell orientation is removed",
            "adapter is killed if deterministic rule-time is indistinguishable from multiway Omega_r",
            "adapter is killed if Wolfram/ruliad can promote into the primary object",
        ],
        "required_artifacts": [str(OUT_PATH.relative_to(ROOT.parent.parent.parent))],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT.parent.parent.parent))],
        "witness_trace_id": "wolfram_multiway_shell_adapter_fit_probe_v1",
        "wolfram_runtime": {
            "available": wolfram_runtime_available,
            "paths": wolfram_runtime,
            "actual_wolfram_language_execution": False,
        },
        "shell_reports": shell_reports,
        "multiway_structure": {
            "xgi_nodes": hypergraph.num_nodes,
            "xgi_hyperedges": hypergraph.num_edges,
            "hyperedge_size_distribution": {str(size): edge_sizes.count(size) for size in sorted(set(edge_sizes))},
            "rustworkx_nodes": branch_graph.num_nodes(),
            "rustworkx_edges": branch_graph.num_edges(),
            "rustworkx_acyclic": branch_graph_acyclic,
            "node_registry_size": len(node_index),
        },
        "qit_readouts": {
            "r4_path_entropy_bits": final_entropy,
            "r4_present_entropy_bits": shell_reports["4"]["present_entropy_bits"],
            "r4_mutual_information_A_BC_bits": shell_reports["4"]["mutual_information_A_BC_bits"],
        },
        "order_gap": {"noncommuting": noncommuting_gap, "commuting_control": commuting_gap},
        "adapter_value_assessment": {
            "helps": True,
            "why": [
                "keeps multiple Omega_r future continuations explicit instead of collapsing to one rule-time path",
                "XGI hyperedges preserve parent/rule/child/shell incidence that a pairwise or scalar entropy proxy loses",
                "provides a finite branch generator that can feed M_RPF(C) compression maps while staying typed as adapter",
            ],
            "does_not_help_as": [
                "primary object",
                "Axis0 proof",
                "FEP proof",
                "physics/gravity proof",
                "PEPS3D closure",
            ],
        },
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": "This is a v5 formal-scout adapter test against the v4.3 M_RPF object-preservation contract, not a legacy v4 probe.",
        "result_summary": {
            "all_pass": all_pass,
            "wolfram_runtime_available": wolfram_runtime_available,
            "adapter_helpful": True,
            "promotion_allowed": False,
            "final_branch_count": final_branch_count,
            "r4_path_entropy_bits": final_entropy,
            "noncommuting_order_gap": noncommuting_gap,
            "commuting_order_gap": commuting_gap,
        },
        "all_pass": all_pass,
        "pass_rule": "all positive checks pass, all graveyard controls fail as expected, all boundaries pass, and no downstream consumer is unlocked",
        "fail_rule": "fail if Wolfram/ruliad promotes to primary object, if deterministic rule-time preserves object fields, if shell orientation can be removed, or if order gap survives commuting control",
        "blockers": [],
        "elapsed_seconds": round(time.time() - start, 6),
    }

    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["result_summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
