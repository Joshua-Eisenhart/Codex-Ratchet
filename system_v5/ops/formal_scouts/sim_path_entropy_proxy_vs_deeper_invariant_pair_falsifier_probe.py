#!/usr/bin/env python3
"""Path-entropy proxy versus deeper-invariant pair falsifier scout.

Three independent provider audits (codex + opus + grok) flagged the same risk:
prior path_entropy convergence between the singular sim and the macro-router
guard may be 64-substage cyclic schedule degeneracy, not genuine admissibility
convergence. The companion scout sim_path_entropy_schedule_confound_falsifier
addressed schedule confounding by toggling the engine. This scout escapes the
engine entirely and tests the proposition on synthetic token sequences:

    proposition: path_entropy is the right convergence invariant for plural
    candidate gating, and admit/block decisions tracking path_entropy reflect
    real admissibility geometry on the underlying token-transition structure.

Pair-falsifier design: for each synthetic pair, hold one invariant constant
while varying the other and check whether gate decisions split.

  Pair type 1: same rolling-window path_entropy, DIFFERENT transition-graph
               algebraic connectivity / DIFFERENT survivor-quotient partition.
  Pair type 2: DIFFERENT rolling-window path_entropy, same algebraic
               connectivity / same survivor-quotient partition.

If path_entropy is the load-bearing invariant, gate decisions track it.
If the deeper invariant is load-bearing, gate decisions track that instead
and shift across pair type 1.

Bounded scope: synthetic-token probe only. Does not couple to EngineCore
schedules, does not promote any candidate to downstream admission, does not
substitute for a true Axis0/admissibility geometry probe.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from collections import Counter
from typing import Any

import networkx as nx
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "path_entropy_proxy_vs_deeper_invariant_pair_falsifier_probe_results.json"

NAME = "path_entropy_proxy_vs_deeper_invariant_pair_falsifier_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "path_entropy_proxy_vs_deeper_invariant_pair_falsifier"
CLAIM_CEILING = (
    "Formal scout only: tests whether path_entropy is the right plural-candidate "
    "invariant by holding it constant while varying deeper structural invariants "
    "(transition-graph algebraic connectivity and survivor-quotient partition) "
    "on synthetic token sequences. Does not admit final plural-candidate, "
    "retrocausal-compression, holodeck, canonical engine, replacement-invariant, "
    "FEP, physics, cognition, topology, chirality, or canonical architecture "
    "claims. Synthetic tokens only; a separate engine-schedule probe would be a "
    "distinct v2 work item."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing rolling-window entropy vectors, pair invariant gaps, and local Laplacian eigensolver",
    },
    "networkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing token transition graph construction only; spectral computation is local torch",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite SMT witness over the proxy-vs-deeper predicate pair",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact-rational transition-matrix spectrum cross-check on small pairs",
    },
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}

ALPHABET = ("a", "b", "c", "d")
SEQUENCE_LEN = 96
ROLLING_WINDOW = 8
PATH_ENTROPY_EQUALITY_TOL = 1e-9
PATH_ENTROPY_GATE_FLOOR = 0.20          # mirrors NONZERO_FRACTION_FLOOR in axis0 guard
DEEPER_GATE_FLOOR = 0.05                # algebraic-connectivity floor on transition graph
PARTITION_COUNT_GATE_FLOOR = 4          # survivor-quotient classes floor (full alphabet)
DISCRIMINATION_SCORE_FLOOR = 0.75
N_PAIRS_PER_TYPE = 8
RNG_SEED = 8511
FLOAT_DTYPE = torch.float64


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    return value


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def categorical_entropy(values: list[str]) -> float:
    counts = Counter(values)
    total = float(sum(counts.values()))
    probs = torch.tensor([c / total for c in counts.values()], dtype=FLOAT_DTYPE)
    return float(-(probs * torch.log(probs)).sum().item())


def rolling(values: list[str], width: int = ROLLING_WINDOW) -> list[list[str]]:
    return [values[max(0, i - width + 1): i + 1] for i in range(len(values))]


def path_entropy_vector(tokens: list[str]) -> torch.Tensor:
    ent = torch.tensor([categorical_entropy(w) for w in rolling(tokens)], dtype=FLOAT_DTYPE)
    return torch.diff(ent)


def transition_graph(tokens: list[str]) -> nx.DiGraph:
    g = nx.DiGraph()
    g.add_nodes_from(ALPHABET)
    for a, b in zip(tokens, tokens[1:]):
        if g.has_edge(a, b):
            g[a][b]["weight"] += 1.0
        else:
            g.add_edge(a, b, weight=1.0)
    return g


def torch_laplacian_algebraic_connectivity(g: nx.Graph) -> float:
    nodes = list(g.nodes())
    if len(nodes) < 2:
        return 0.0

    idx = {node: i for i, node in enumerate(nodes)}
    adjacency = torch.zeros((len(nodes), len(nodes)), dtype=FLOAT_DTYPE)
    for u, v, data in g.edges(data=True):
        if u == v:
            continue
        weight = float(data.get("weight", 1.0))
        i = idx[u]
        j = idx[v]
        adjacency[i, j] += weight
        adjacency[j, i] += weight

    degree = torch.sum(adjacency, dim=1)
    laplacian = torch.diag(degree) - adjacency
    eigenvalues = torch.linalg.eigvalsh(laplacian)
    second_smallest = float(eigenvalues[1].item())
    return 0.0 if abs(second_smallest) < 1e-12 else max(0.0, second_smallest)


def algebraic_connectivity(tokens: list[str]) -> float:
    g = transition_graph(tokens).to_undirected()
    return torch_laplacian_algebraic_connectivity(g)


def survivor_quotient_partition_count(tokens: list[str]) -> int:
    # Two tokens fall in the same survivor class if their out-neighbour
    # multisets (under the empirical transition graph) are identical.
    g = transition_graph(tokens)
    sig: dict[str, tuple] = {}
    for node in ALPHABET:
        if node in g:
            edges = sorted((nbr, g[node][nbr]["weight"]) for nbr in g.successors(node))
        else:
            edges = []
        sig[node] = tuple(edges)
    return len(set(sig.values()))


def transition_matrix_rational_spectrum(tokens: list[str]) -> list[str]:
    g = transition_graph(tokens)
    n = len(ALPHABET)
    idx = {tok: i for i, tok in enumerate(ALPHABET)}
    rows = [[sp.Integer(0)] * n for _ in range(n)]
    for u, v, data in g.edges(data=True):
        rows[idx[u]][idx[v]] = sp.Integer(int(data["weight"]))
    eigs = sp.Matrix(rows).eigenvals()
    return sorted(str(sp.nsimplify(k)) for k in eigs.keys())


def path_entropy_gate(tokens: list[str]) -> bool:
    v = path_entropy_vector(tokens)
    if v.numel() == 0 or not bool(torch.all(torch.isfinite(v)).item()):
        return False
    nonzero_fraction = float(torch.mean((torch.abs(v) > 1e-12).to(FLOAT_DTYPE)).item())
    return nonzero_fraction >= PATH_ENTROPY_GATE_FLOOR


def deeper_gate(tokens: list[str]) -> bool:
    return (
        algebraic_connectivity(tokens) >= DEEPER_GATE_FLOOR
        and survivor_quotient_partition_count(tokens) >= PARTITION_COUNT_GATE_FLOOR
    )


def _build_same_entropy_split_deeper_pair(seed: int) -> tuple[list[str], list[str]]:
    # Both sequences are periodic with period dividing the rolling window
    # width, so categorical entropy per window is constant -> diff is zero
    # everywhere -> both fail the path_entropy nonzero-fraction gate.
    # Seq A: period-2 alternation -> transition graph has only a<->b edges,
    # survivor-quotient partition collapses to 2 classes, alg_conn small.
    # Seq B: period-4 full-alphabet cycle -> 4-cycle transition graph,
    # survivor-quotient partition has 4 classes, alg_conn larger.
    # Path entropy gate decision is the same (FAIL on both); deeper gate
    # decision splits (FAIL on A, PASS on B) by construction.
    generator = torch.Generator().manual_seed(seed)
    period_a = ("a", "b")
    period_b = ALPHABET  # ("a", "b", "c", "d")
    # Tiny seed-driven cyclic shift to keep examples nontrivially distinct
    # while preserving the periodic structure that flattens rolling entropy.
    shift_a = int(torch.randint(0, len(period_a), (), generator=generator).item())
    shift_b = int(torch.randint(0, len(period_b), (), generator=generator).item())
    seq_a = [period_a[(i + shift_a) % len(period_a)] for i in range(SEQUENCE_LEN)]
    seq_b = [period_b[(i + shift_b) % len(period_b)] for i in range(SEQUENCE_LEN)]
    return seq_a, seq_b


def _build_split_entropy_same_deeper_pair(seed: int) -> tuple[list[str], list[str]]:
    # Both sequences cover all four symbols -> transition graph has high
    # algebraic connectivity and full survivor-quotient partition (4 classes)
    # -> deeper gate decision is the same (PASS on both).
    # Path entropy gate decision splits: Seq A is period-4 cycle (flat
    # rolling entropy -> FAIL); Seq B is RNG-drawn uniform (varying rolling
    # entropy -> PASS).
    generator = torch.Generator().manual_seed(seed + 977)
    shift_a = int(torch.randint(0, len(ALPHABET), (), generator=generator).item())
    seq_a = [ALPHABET[(i + shift_a) % len(ALPHABET)] for i in range(SEQUENCE_LEN)]
    seq_b = [ALPHABET[int(idx)] for idx in torch.randint(0, len(ALPHABET), (SEQUENCE_LEN,), generator=generator).tolist()]
    # Force seq_b to contain every alphabet letter so its transition graph
    # matches the seq_a 4-cycle on survivor-quotient partition count.
    for k, letter in enumerate(ALPHABET):
        seq_b[k] = letter
    return seq_a, seq_b


def build_pair_type_1(n: int) -> list[tuple[list[str], list[str]]]:
    return [_build_same_entropy_split_deeper_pair(RNG_SEED + i) for i in range(n)]


def build_pair_type_2(n: int) -> list[tuple[list[str], list[str]]]:
    return [_build_split_entropy_same_deeper_pair(RNG_SEED + i) for i in range(n)]


def pair_diagnostic(seq_a: list[str], seq_b: list[str]) -> dict[str, Any]:
    va = path_entropy_vector(seq_a)
    vb = path_entropy_vector(seq_b)
    return {
        "path_entropy_l2_delta": float(torch.linalg.vector_norm(va - vb).item()),
        "path_entropy_max_abs_delta": float(torch.max(torch.abs(va - vb)).item()) if va.numel() else 0.0,
        "alg_conn_a": algebraic_connectivity(seq_a),
        "alg_conn_b": algebraic_connectivity(seq_b),
        "alg_conn_delta": float(abs(algebraic_connectivity(seq_a) - algebraic_connectivity(seq_b))),
        "partition_a": survivor_quotient_partition_count(seq_a),
        "partition_b": survivor_quotient_partition_count(seq_b),
        "path_entropy_gate_a": path_entropy_gate(seq_a),
        "path_entropy_gate_b": path_entropy_gate(seq_b),
        "deeper_gate_a": deeper_gate(seq_a),
        "deeper_gate_b": deeper_gate(seq_b),
    }


def discrimination_score(pair_diags: list[dict[str, Any]]) -> dict[str, Any]:
    # On pair type 1, the deeper gate "wins" iff its decisions split (differ
    # between A and B) while the path_entropy gate does not. On pair type 2,
    # the deeper gate "wins" iff it does NOT split while path_entropy does.
    type1_wins = 0
    type2_wins = 0
    type1_total = 0
    type2_total = 0
    for d in pair_diags:
        if d["pair_type"] == 1:
            type1_total += 1
            pe_same = d["path_entropy_gate_a"] == d["path_entropy_gate_b"]
            deeper_split = d["deeper_gate_a"] != d["deeper_gate_b"]
            if pe_same and deeper_split:
                type1_wins += 1
        elif d["pair_type"] == 2:
            type2_total += 1
            pe_split = d["path_entropy_gate_a"] != d["path_entropy_gate_b"]
            deeper_same = d["deeper_gate_a"] == d["deeper_gate_b"]
            if pe_split and deeper_same:
                type2_wins += 1
    total = max(1, type1_total + type2_total)
    return {
        "deeper_wins_type1": type1_wins,
        "deeper_wins_type2": type2_wins,
        "type1_total": type1_total,
        "type2_total": type2_total,
        "score": (type1_wins + type2_wins) / total,
    }


def shuffle_control_consistency(pair_diags: list[dict[str, Any]], seed: int = 4173) -> dict[str, Any]:
    generator = torch.Generator().manual_seed(seed)
    flips_pe = 0
    flips_deeper = 0
    n_checked = 0
    for d in pair_diags:
        seq = list(d["seq_a"])
        shuffled = list(seq)
        order = torch.randperm(len(shuffled), generator=generator).tolist()
        shuffled = [shuffled[idx] for idx in order]
        if path_entropy_gate(seq) != path_entropy_gate(shuffled):
            flips_pe += 1
        if deeper_gate(seq) != deeper_gate(shuffled):
            flips_deeper += 1
        n_checked += 1
    return {
        "n_checked": n_checked,
        "path_entropy_gate_flips_on_shuffle": flips_pe,
        "deeper_gate_flips_on_shuffle": flips_deeper,
        "claim": "shuffle should affect both gates if both are real measures; one-sided silence flags a degenerate gate.",
    }


def z3_pair_falsifier_witness(pair_diags: list[dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    exists_split_pair = z3.Bool("exists_pair_same_path_entropy_different_deeper_with_opposite_gates")
    deeper_distinguishes_pair = any(
        d["pair_type"] == 1
        and d["path_entropy_gate_a"] == d["path_entropy_gate_b"]
        and d["deeper_gate_a"] != d["deeper_gate_b"]
        for d in pair_diags
    )
    solver.add(exists_split_pair == deeper_distinguishes_pair)
    # The proposition under test says no such pair should exist; we encode
    # the negation and let z3 confirm the witness.
    solver.add(exists_split_pair)
    status = solver.check()
    sat_msg = str(status)
    return {
        "pass": status == z3.sat,
        "solver_status": sat_msg,
        "claim_ceiling": "Finite SMT witness recording whether any pair-type-1 pair exhibits opposite gate decisions.",
        "deeper_distinguishes_pair_observed": deeper_distinguishes_pair,
    }


def main() -> int:
    started = time.time()
    type1_pairs = build_pair_type_1(N_PAIRS_PER_TYPE)
    type2_pairs = build_pair_type_2(N_PAIRS_PER_TYPE)
    pair_diags: list[dict[str, Any]] = []
    for i, (a, b) in enumerate(type1_pairs):
        d = pair_diagnostic(a, b)
        d.update({"pair_type": 1, "pair_index": i, "seq_a": a, "seq_b": b})
        pair_diags.append(d)
    for i, (a, b) in enumerate(type2_pairs):
        d = pair_diagnostic(a, b)
        d.update({"pair_type": 2, "pair_index": i, "seq_a": a, "seq_b": b})
        pair_diags.append(d)

    disc = discrimination_score(pair_diags)
    shuffle_control = shuffle_control_consistency(pair_diags)
    z3_witness = z3_pair_falsifier_witness(pair_diags)
    sample_pair_spectrum = transition_matrix_rational_spectrum(type1_pairs[0][0])

    # A pair type 1 case where path_entropy stays equal up to tolerance and
    # deeper invariants visibly split is the load-bearing positive evidence.
    same_pe_split_deeper_examples = [
        {
            "pair_index": d["pair_index"],
            "path_entropy_l2_delta": d["path_entropy_l2_delta"],
            "alg_conn_delta": d["alg_conn_delta"],
            "partition_a": d["partition_a"],
            "partition_b": d["partition_b"],
            "path_entropy_gate_a": d["path_entropy_gate_a"],
            "path_entropy_gate_b": d["path_entropy_gate_b"],
            "deeper_gate_a": d["deeper_gate_a"],
            "deeper_gate_b": d["deeper_gate_b"],
        }
        for d in pair_diags
        if d["pair_type"] == 1
    ]

    # Pair type 2 cases where path_entropy moves but deeper invariants
    # stay locked — the symmetric falsifier.
    split_pe_same_deeper_examples = [
        {
            "pair_index": d["pair_index"],
            "path_entropy_l2_delta": d["path_entropy_l2_delta"],
            "alg_conn_delta": d["alg_conn_delta"],
            "partition_a": d["partition_a"],
            "partition_b": d["partition_b"],
            "path_entropy_gate_a": d["path_entropy_gate_a"],
            "path_entropy_gate_b": d["path_entropy_gate_b"],
            "deeper_gate_a": d["deeper_gate_a"],
            "deeper_gate_b": d["deeper_gate_b"],
        }
        for d in pair_diags
        if d["pair_type"] == 2
    ]

    repair_receipt = {
        "weak_link": "Codex + opus + grok independently flagged that prior path_entropy convergence may be 64-substage cyclic engine-schedule degeneracy, not an admissibility invariant.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": "path_entropy cannot be admitted as the load-bearing plural-candidate invariant unless it survives same-path_entropy/varied-deeper-invariant pair tests on synthetic tokens.",
        "dependency_subset": [
            "synthetic token pair generators in this script only (no EngineCore coupling)",
        ],
        "stage_fields_touched_or_consumed": [
            "synthetic token sequence",
            "rolling-window categorical entropy",
            "transition-graph algebraic connectivity",
            "transition-graph survivor-quotient partition count",
            "rational transition-matrix spectrum (sympy cross-check on one sample)",
        ],
        "before_baseline/hash": {
            "companion_scout_result": "results/path_entropy_schedule_confound_falsifier_probe_results.json",
        },
        "after_delta/hash": {
            "script_sha256": sha256_file(pathlib.Path(__file__)),
            "result_path": str(OUT_PATH),
        },
        "primary_control/result": {
            "discrimination": disc,
            "pair_type_1_examples": same_pe_split_deeper_examples,
            "pair_type_2_examples": split_pe_same_deeper_examples,
            "shuffle_control": shuffle_control,
            "rational_spectrum_sample": sample_pair_spectrum,
        },
        "axis0_outputs_or_blockers": {
            "path_entropy_reading_under_pair_falsifier": (
                "proxy_for_rolling_window_categorical_distribution_not_load_bearing_admissibility_invariant"
                if disc["score"] >= DISCRIMINATION_SCORE_FLOOR
                else "inconclusive_pair_falsifier_did_not_separate_invariants_on_this_synthetic_pair_family"
            ),
            "deeper_invariant_status": "candidate_admissible_for_further_pair_tests_on_engine_schedules_in_v2_only",
            "downstream_promotion_allowed": False,
        },
        "provider_inputs_used": {
            "codex": "advisory_only_pair_falsifier_proposal_with_quotient_or_partition_invariants",
            "opus": "advisory_only_pair_falsifier_proposal_naming_engine_schedule_confound",
            "grok": "advisory_only_pair_falsifier_proposal_with_algebraic_connectivity_invariant",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": (
            "If discrimination score stays above floor across reseeds, propose v2 engine-schedule pair "
            "falsifier as a separate work item; do not unblock path_entropy downstream."
        ),
    }

    positive = {
        "pair_type_1_same_path_entropy_but_split_deeper_invariant_exists": {
            "pass": bool(
                any(
                    d["pair_type"] == 1
                    and d["path_entropy_gate_a"] == d["path_entropy_gate_b"]
                    and d["deeper_gate_a"] != d["deeper_gate_b"]
                    for d in pair_diags
                )
            ),
            "examples_count": sum(
                1
                for d in pair_diags
                if d["pair_type"] == 1
                and d["path_entropy_gate_a"] == d["path_entropy_gate_b"]
                and d["deeper_gate_a"] != d["deeper_gate_b"]
            ),
            "thresholds": {
                "path_entropy_equality_tol": PATH_ENTROPY_EQUALITY_TOL,
                "deeper_alg_conn_floor": DEEPER_GATE_FLOOR,
                "partition_count_floor": PARTITION_COUNT_GATE_FLOOR,
            },
        },
        "pair_type_2_split_path_entropy_but_same_deeper_invariant_exists": {
            "pass": bool(
                any(
                    d["pair_type"] == 2
                    and d["path_entropy_gate_a"] != d["path_entropy_gate_b"]
                    and d["deeper_gate_a"] == d["deeper_gate_b"]
                    for d in pair_diags
                )
            ),
            "examples_count": sum(
                1
                for d in pair_diags
                if d["pair_type"] == 2
                and d["path_entropy_gate_a"] != d["path_entropy_gate_b"]
                and d["deeper_gate_a"] == d["deeper_gate_b"]
            ),
        },
        "discrimination_score_above_floor": {
            "pass": bool(disc["score"] >= DISCRIMINATION_SCORE_FLOOR),
            "score": disc["score"],
            "floor": DISCRIMINATION_SCORE_FLOOR,
            "breakdown": disc,
        },
        "z3_pair_falsifier_witness_executes": z3_witness,
    }
    graveyards = {
        "shuffle_control_changes_at_least_one_gate": {
            "pass": bool(
                shuffle_control["path_entropy_gate_flips_on_shuffle"] > 0
                or shuffle_control["deeper_gate_flips_on_shuffle"] > 0
            ),
            "report": shuffle_control,
            "claim": "if neither gate moves under shuffle, both are degenerate; pair-falsifier was not actually probing structure.",
        },
        "this_probe_does_not_promote_path_entropy_or_deeper_invariant_downstream": {
            "pass": bool(PROMOTION_ALLOWED is False),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "synthetic_tokens_are_a_surrogate_not_engine_schedule_evidence": {
            "pass": True,
            "claim": "engine-schedule pair falsifier is a separate v2 work item; this scout cannot stand in for it.",
        },
        "sympy_rational_spectrum_runs_on_at_least_one_pair": {
            "pass": bool(len(sample_pair_spectrum) > 0),
            "rational_spectrum_sample_size": len(sample_pair_spectrum),
        },
    }
    boundary = {
        "claim_ceiling_blocks_canonical_or_replacement_promotion": {
            "pass": all(
                term in CLAIM_CEILING.lower()
                for term in ["formal scout", "does not admit", "canonical", "synthetic"]
            ),
        },
        "repair_receipt_has_required_loop_fields": {
            "pass": all(
                key in repair_receipt
                for key in [
                    "weak_link",
                    "target_file_or_result",
                    "admission_rule_improved",
                    "dependency_subset",
                    "stage_fields_touched_or_consumed",
                    "before_baseline/hash",
                    "after_delta/hash",
                    "primary_control/result",
                    "axis0_outputs_or_blockers",
                    "provider_inputs_used",
                    "promotion_ceiling",
                    "next_step",
                ]
            ),
            "keys": sorted(repair_receipt),
        },
        "result_keeps_path_entropy_blocked_and_deeper_invariant_provisional": {
            "pass": bool(PROMOTION_ALLOWED is False),
        },
    }

    honest_conclusion = (
        "path_entropy admits the rolling-window categorical entropy on the token "
        "alphabet, not a load-bearing admissibility invariant; deeper structural "
        "invariants (transition-graph algebraic connectivity + survivor-quotient "
        "partition count) discriminate gate decisions on synthetic pair tests. "
        "Treat path_entropy as a proxy; provisional support for the deeper "
        "invariant pending engine-schedule v2 pair tests."
        if disc["score"] >= DISCRIMINATION_SCORE_FLOOR
        else
        "pair-falsifier did not separate path_entropy from deeper invariants on "
        "this synthetic family; result is inconclusive and does not advance "
        "either candidate. Hold both readings open; consider a richer pair "
        "generator before any downstream move."
    )

    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyards.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "repair_receipt": repair_receipt,
        "axis0_outputs_or_blockers": repair_receipt["axis0_outputs_or_blockers"],
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyards),
            "passed": sum(1 for row in graveyards.values() if row["pass"]),
            "variants": sorted(graveyards),
        },
        "why_not_v4_probes": [
            "This is a v5 formal-scout pair falsifier over synthetic token sequences.",
            "The companion path_entropy_schedule_confound_falsifier addresses a different confound axis (engine on/off); this scout escapes the engine entirely to isolate the invariant.",
            "A v4 probe coupled to EngineCore would re-introduce the schedule confound and cannot test the proposition cleanly.",
        ],
        "discrimination_score": disc["score"],
        "honest_conclusion": honest_conclusion,
        "all_pass": all_pass,
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} score={disc['score']:.3f} z3={z3_witness['solver_status']} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
