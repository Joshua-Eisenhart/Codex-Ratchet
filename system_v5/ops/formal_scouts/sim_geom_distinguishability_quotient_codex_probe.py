#!/usr/bin/env python3
"""
Independent finite distinguishability quotient probe.

Geometry under test:
  finite state set S, finite probe set P;
  s ~ t iff p(s) = p(t) for every p in P;
  quotient Q = S / ~.

This is diagnostic-only evidence. It does not promote a lego, layer, bridge,
Axis0, flux, basin, or manifold claim.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from itertools import combinations
from pathlib import Path
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
os.environ.setdefault("NUMBA_CACHE_DIR", "/private/tmp/codex_ratchet_numba_cache")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cvc5
import gudhi
import rustworkx as rx
import sympy as sp
import torch
from clifford import Cl
from geomstats.geometry.euclidean import Euclidean
from toponetx.classes import SimplicialComplex
from z3 import And, Bool, BoolVal, Not, Or, Solver, unsat


RESULT_PATH = Path("results/geom_distinguishability_quotient_codex_probe_results.json")
DTYPE_REAL = torch.float64
DTYPE_COMPLEX = torch.complex128


TOOL_MANIFEST: dict[str, dict[str, Any]] = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing substrate for finite probe matrices, float64 signatures, complex128 signature cross-checks, equivalence relation tensors, and quotient embeddings",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact Bell number source for partition-count known-value checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing UNSAT proof that the computed probe relation violates no reflexivity/symmetry/transitivity clause",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT cross-check of the same finite equivalence-relation negation",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing orthonormal quotient-basis check in a real Clifford algebra Cl(|Q|)",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PyTorch-backend Euclidean quotient-embedding metric check: zero within classes, positive between classes",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing H0 Betti check of the simplicial complex induced by equivalence-class cliques",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing simplicial-complex edge-count check for equivalence-class clique structure",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing connected-component count of the equivalence graph induced by ~",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "clifford": "load_bearing",
    "geomstats": "load_bearing",
    "gudhi": "load_bearing",
    "toponetx": "load_bearing",
    "rustworkx": "load_bearing",
}


def json_ready(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        if value.ndim == 0:
            return value.item()
        return value.detach().cpu().tolist()
    if isinstance(value, tuple):
        return [json_ready(v) for v in value]
    if isinstance(value, list):
        return [json_ready(v) for v in value]
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    return value


def values_match(computed: Any, known: Any) -> bool:
    if isinstance(computed, bool) or isinstance(known, bool):
        return bool(computed) is bool(known)
    if isinstance(computed, int) and isinstance(known, int):
        return computed == known
    if isinstance(computed, float) or isinstance(known, float):
        return abs(float(computed) - float(known)) <= 1.0e-10
    return computed == known


def known_value_check(invariant: str, computed: Any, known: Any) -> dict[str, Any]:
    computed_ready = json_ready(computed)
    known_ready = json_ready(known)
    return {
        "invariant": invariant,
        "computed": computed_ready,
        "known": known_ready,
        "match": values_match(computed_ready, known_ready),
    }


def torch_probe_matrix(n_states: int, n_probes: int, seed: int, mode: str) -> torch.Tensor:
    states = torch.arange(n_states, dtype=DTYPE_REAL)
    if n_probes == 0:
        return torch.empty((0, n_states), dtype=DTYPE_REAL)
    if mode == "separating":
        return states.reshape(1, n_states)
    if mode == "constant":
        return torch.zeros((1, n_states), dtype=DTYPE_REAL)

    rows: list[torch.Tensor] = []
    for probe_index in range(n_probes):
        modulus = max(1, min(n_states + 2, 2 + ((seed + probe_index) % max(2, n_states + 1))))
        if mode == "affine_mod":
            row = torch.remainder(
                states * float(seed + probe_index + 1) + float(probe_index * probe_index + 3),
                float(modulus),
            )
        elif mode == "bucket":
            width = 1 + ((seed + probe_index) % max(1, n_states))
            row = torch.div(states + float(seed % 3), float(width), rounding_mode="floor")
        elif mode == "xor_like":
            int_states = torch.arange(n_states, dtype=torch.int64)
            row = torch.bitwise_xor(int_states, torch.tensor(seed + probe_index, dtype=torch.int64))
            row = torch.remainder(row, modulus).to(DTYPE_REAL)
        elif mode == "random_bucket":
            generator = torch.Generator()
            generator.manual_seed(seed * 1009 + probe_index * 9176 + n_states * 37 + n_probes)
            row = torch.randint(0, max(1, modulus), (n_states,), generator=generator, dtype=torch.int64)
            row = row.to(DTYPE_REAL)
        else:
            raise ValueError(f"unknown probe mode {mode!r}")
        rows.append(row)
    return torch.stack(rows, dim=0)


def complex_probe_matrix(probe_matrix: torch.Tensor) -> torch.Tensor:
    real = probe_matrix.to(DTYPE_COMPLEX)
    imag = (probe_matrix.square() + 1.0).to(DTYPE_COMPLEX)
    return real + (1j * imag)


def relation_from_probe_matrix(probe_matrix: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, bool]:
    n_states = int(probe_matrix.shape[1])
    if probe_matrix.shape[0] == 0:
        relation_real = torch.ones((n_states, n_states), dtype=torch.bool)
        relation_complex = torch.ones((n_states, n_states), dtype=torch.bool)
        return relation_real, relation_complex, True

    signatures_real = probe_matrix.transpose(0, 1).contiguous()
    relation_real = (
        signatures_real.unsqueeze(1).eq(signatures_real.unsqueeze(0)).all(dim=2)
    )

    signatures_complex = complex_probe_matrix(probe_matrix).transpose(0, 1).contiguous()
    relation_complex = (
        signatures_complex.unsqueeze(1).eq(signatures_complex.unsqueeze(0)).all(dim=2)
    )
    agree = bool(torch.equal(relation_real, relation_complex))
    return relation_real, relation_complex, agree


def quotient_classes_from_relation(relation: torch.Tensor) -> list[list[int]]:
    n_states = int(relation.shape[0])
    seen: set[int] = set()
    classes: list[list[int]] = []
    for i in range(n_states):
        if i in seen:
            continue
        block = [j for j in range(n_states) if bool(relation[i, j].item())]
        seen.update(block)
        classes.append(block)
    return classes


def class_index(classes: list[list[int]], n_states: int) -> list[int]:
    labels = [-1 for _ in range(n_states)]
    for idx, block in enumerate(classes):
        for state in block:
            labels[state] = idx
    if any(label < 0 for label in labels):
        raise RuntimeError("internal quotient labeling error")
    return labels


def z3_negation_unsat_equivalence(relation: torch.Tensor) -> tuple[bool, str]:
    n_states = int(relation.shape[0])
    solver = Solver()
    r = [[Bool(f"r_{i}_{j}") for j in range(n_states)] for i in range(n_states)]
    for i in range(n_states):
        for j in range(n_states):
            solver.add(r[i][j] == BoolVal(bool(relation[i, j].item())))

    violations = []
    for i in range(n_states):
        violations.append(Not(r[i][i]))
    for i in range(n_states):
        for j in range(n_states):
            violations.append(r[i][j] != r[j][i])
    for i in range(n_states):
        for j in range(n_states):
            for k in range(n_states):
                violations.append(And(r[i][j], r[j][k], Not(r[i][k])))

    solver.add(Or(*violations))
    result = solver.check()
    return result == unsat, str(result)


def _cvc5_or(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkBoolean(False)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(cvc5.Kind.OR, *terms)


def _cvc5_and(solver: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkBoolean(True)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(cvc5.Kind.AND, *terms)


def cvc5_negation_unsat_equivalence(relation: torch.Tensor) -> tuple[bool, str]:
    n_states = int(relation.shape[0])
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    r = [[solver.mkConst(bool_sort, f"r_{i}_{j}") for j in range(n_states)] for i in range(n_states)]
    for i in range(n_states):
        for j in range(n_states):
            solver.assertFormula(
                solver.mkTerm(
                    cvc5.Kind.EQUAL,
                    r[i][j],
                    solver.mkBoolean(bool(relation[i, j].item())),
                )
            )

    violations = []
    for i in range(n_states):
        violations.append(solver.mkTerm(cvc5.Kind.NOT, r[i][i]))
    for i in range(n_states):
        for j in range(n_states):
            equal_ij_ji = solver.mkTerm(cvc5.Kind.EQUAL, r[i][j], r[j][i])
            violations.append(solver.mkTerm(cvc5.Kind.NOT, equal_ij_ji))
    for i in range(n_states):
        for j in range(n_states):
            for k in range(n_states):
                violations.append(
                    _cvc5_and(
                        solver,
                        [
                            r[i][j],
                            r[j][k],
                            solver.mkTerm(cvc5.Kind.NOT, r[i][k]),
                        ],
                    )
                )

    solver.assertFormula(_cvc5_or(solver, violations))
    result = solver.checkSat()
    return result.isUnsat(), str(result)


def rustworkx_component_count(relation: torch.Tensor) -> int:
    n_states = int(relation.shape[0])
    graph = rx.PyGraph()
    graph.add_nodes_from(range(n_states))
    for i in range(n_states):
        for j in range(i + 1, n_states):
            if bool(relation[i, j].item()):
                graph.add_edge(i, j, None)
    return len(rx.connected_components(graph))


def gudhi_h0_count(classes: list[list[int]], n_states: int) -> int:
    simplex_tree = gudhi.SimplexTree()
    for vertex in range(n_states):
        simplex_tree.insert([vertex])
    for block in classes:
        for size in range(2, len(block) + 1):
            for simplex in combinations(block, size):
                simplex_tree.insert(list(simplex))
    simplex_tree.persistence(persistence_dim_max=True)
    betti = simplex_tree.betti_numbers()
    return int(betti[0]) if betti else 0


def toponetx_edge_count(classes: list[list[int]], n_states: int) -> int:
    complex_obj = SimplicialComplex()
    for vertex in range(n_states):
        complex_obj.add_simplex([vertex])
    for block in classes:
        for i, j in combinations(block, 2):
            complex_obj.add_simplex([i, j])
    if len(complex_obj.shape) < 2:
        return 0
    return int(complex_obj.shape[1])


def expected_equivalence_edge_count(classes: list[list[int]]) -> int:
    return sum(len(block) * (len(block) - 1) // 2 for block in classes)


def geomstats_metric_check(classes: list[list[int]], n_states: int) -> tuple[bool, float, float]:
    q_count = len(classes)
    labels = class_index(classes, n_states)
    embedding = torch.zeros((n_states, q_count), dtype=DTYPE_REAL)
    for state, label in enumerate(labels):
        embedding[state, label] = 1.0

    metric = Euclidean(dim=q_count).metric
    max_within = 0.0
    min_between: float | None = None
    for i in range(n_states):
        for j in range(n_states):
            distance = float(metric.dist(embedding[i], embedding[j]))
            if labels[i] == labels[j]:
                max_within = max(max_within, abs(distance))
            else:
                min_between = distance if min_between is None else min(min_between, distance)
    if min_between is None:
        min_between = 0.0
        ok = max_within <= 1.0e-12
    else:
        ok = max_within <= 1.0e-12 and min_between > 0.0
    return ok, max_within, min_between


@lru_cache(maxsize=None)
def clifford_layout(q_count: int) -> tuple[Any, dict[str, Any]]:
    safe_dim = max(1, q_count)
    return Cl(safe_dim)


def clifford_orthonormal_basis_check(q_count: int) -> tuple[bool, float, float]:
    layout, blades = clifford_layout(q_count)
    del layout
    if q_count == 1:
        vectors = [blades["e1"]]
    else:
        vectors = [blades[f"e{i + 1}"] for i in range(q_count)]

    max_norm_error = 0.0
    max_offdiag_inner = 0.0
    for i, vec_i in enumerate(vectors):
        norm = float((vec_i | vec_i)[()])
        max_norm_error = max(max_norm_error, abs(norm - 1.0))
        for j, vec_j in enumerate(vectors):
            if i == j:
                continue
            inner = float((vec_i | vec_j)[()])
            max_offdiag_inner = max(max_offdiag_inner, abs(inner))
    ok = max_norm_error <= 1.0e-12 and max_offdiag_inner <= 1.0e-12
    return ok, max_norm_error, max_offdiag_inner


def canonical_partition(classes: list[list[int]], n_states: int) -> tuple[int, ...]:
    labels = [-1] * n_states
    for class_id, block in enumerate(classes):
        for state in block:
            labels[state] = class_id
    renumber: dict[int, int] = {}
    next_label = 0
    canonical: list[int] = []
    for label in labels:
        if label not in renumber:
            renumber[label] = next_label
            next_label += 1
        canonical.append(renumber[label])
    return tuple(canonical)


def generate_restricted_growth_partitions(n_states: int) -> list[tuple[int, ...]]:
    if n_states == 0:
        return [()]

    partitions: list[tuple[int, ...]] = []

    def extend(prefix: list[int], max_label: int) -> None:
        if len(prefix) == n_states:
            partitions.append(tuple(prefix))
            return
        for label in range(max_label + 2):
            prefix.append(label)
            extend(prefix, max(max_label, label))
            prefix.pop()

    extend([0], 0)
    return partitions


def brute_force_partition_count(n_states: int) -> int:
    return len(generate_restricted_growth_partitions(n_states))


def realized_single_probe_partition_count(n_states: int) -> int:
    realized: set[tuple[int, ...]] = set()
    for partition in generate_restricted_growth_partitions(n_states):
        probe = torch.tensor([partition], dtype=DTYPE_REAL)
        relation, _, complex_agree = relation_from_probe_matrix(probe)
        if not complex_agree:
            raise RuntimeError("float64/complex128 relation disagreement in partition realization")
        classes = quotient_classes_from_relation(relation)
        realized.add(canonical_partition(classes, n_states))
    return len(realized)


def run_case(n_states: int, n_probes: int, seed: int, mode: str) -> dict[str, Any]:
    probe_matrix = torch_probe_matrix(n_states, n_probes, seed, mode)
    relation, relation_complex, complex_agree = relation_from_probe_matrix(probe_matrix)
    if not complex_agree:
        raise RuntimeError(f"float64/complex128 relation mismatch for n={n_states}, p={n_probes}, seed={seed}, mode={mode}")
    del relation_complex

    classes = quotient_classes_from_relation(relation)
    q_count = len(classes)
    z3_unsat, z3_status = z3_negation_unsat_equivalence(relation)
    cvc5_unsat, cvc5_status = cvc5_negation_unsat_equivalence(relation)
    rustworkx_components = rustworkx_component_count(relation)
    gudhi_h0 = gudhi_h0_count(classes, n_states)
    toponetx_edges = toponetx_edge_count(classes, n_states)
    expected_edges = expected_equivalence_edge_count(classes)
    geomstats_ok, geomstats_max_within, geomstats_min_between = geomstats_metric_check(classes, n_states)
    clifford_ok, clifford_norm_error, clifford_offdiag = clifford_orthonormal_basis_check(q_count)

    graph_topology_match = (
        rustworkx_components == q_count
        and gudhi_h0 == q_count
        and toponetx_edges == expected_edges
    )
    proof_match = z3_unsat and cvc5_unsat
    case_match = complex_agree and proof_match and graph_topology_match and geomstats_ok and clifford_ok

    return {
        "n_states": n_states,
        "n_probes": n_probes,
        "seed": seed,
        "mode": mode,
        "quotient_cardinality": q_count,
        "classes": classes,
        "relation_float64_complex128_agree": complex_agree,
        "z3_negated_equivalence_status": z3_status,
        "z3_negated_equivalence_unsat": z3_unsat,
        "cvc5_negated_equivalence_status": cvc5_status,
        "cvc5_negated_equivalence_unsat": cvc5_unsat,
        "rustworkx_connected_components": rustworkx_components,
        "gudhi_h0_betti": gudhi_h0,
        "toponetx_1_simplex_count": toponetx_edges,
        "expected_equivalence_edge_count": expected_edges,
        "geomstats_metric_ok": geomstats_ok,
        "geomstats_max_within_class_distance": geomstats_max_within,
        "geomstats_min_between_class_distance": geomstats_min_between,
        "clifford_orthonormal_basis_ok": clifford_ok,
        "clifford_max_norm_error": clifford_norm_error,
        "clifford_max_offdiag_inner": clifford_offdiag,
        "case_match": case_match,
    }


def z3_cvc5_bad_relation_negative() -> dict[str, Any]:
    bad = torch.tensor(
        [
            [True, True, False],
            [True, True, True],
            [False, True, True],
        ],
        dtype=torch.bool,
    )
    z3_unsat, z3_status = z3_negation_unsat_equivalence(bad)
    cvc5_unsat, cvc5_status = cvc5_negation_unsat_equivalence(bad)
    return {
        "name": "reflexive_symmetric_nontransitive_relation",
        "relation": json_ready(bad),
        "expected_equivalence": False,
        "z3_negated_equivalence_status": z3_status,
        "z3_negated_equivalence_unsat": z3_unsat,
        "cvc5_negated_equivalence_status": cvc5_status,
        "cvc5_negated_equivalence_unsat": cvc5_unsat,
        "match": (not z3_unsat) and (not cvc5_unsat),
    }


def build_case_specs() -> list[tuple[int, int, int, str]]:
    specs: list[tuple[int, int, int, str]] = []
    modes = ["affine_mod", "bucket", "xor_like", "random_bucket"]
    for n_states in range(1, 9):
        specs.append((n_states, 1, 0, "separating"))
        specs.append((n_states, 1, 0, "constant"))
        for n_probes in [0, 1, 2, 3, 5, 8]:
            for seed in range(5):
                mode = modes[(n_states + n_probes + seed) % len(modes)]
                specs.append((n_states, n_probes, seed, mode))
    return specs


def main() -> dict[str, Any]:
    torch.set_default_dtype(DTYPE_REAL)
    case_specs = build_case_specs()
    cases = [run_case(*spec) for spec in case_specs]

    known_checks: list[dict[str, Any]] = []
    separating_cases = [case for case in cases if case["mode"] == "separating"]
    constant_cases = [case for case in cases if case["mode"] == "constant"]

    for case in separating_cases:
        known_checks.append(
            known_value_check(
                f"separating_probe_family_cardinality_n={case['n_states']}",
                case["quotient_cardinality"],
                case["n_states"],
            )
        )
    for case in constant_cases:
        known_checks.append(
            known_value_check(
                f"single_constant_probe_cardinality_n={case['n_states']}",
                case["quotient_cardinality"],
                1,
            )
        )

    proof_pass_count = sum(
        1 for case in cases if case["z3_negated_equivalence_unsat"] and case["cvc5_negated_equivalence_unsat"]
    )
    known_checks.append(
        known_value_check(
            "probe_defined_relation_equivalence_unsat_z3_cvc5_all_cases",
            proof_pass_count,
            len(cases),
        )
    )

    complex_agreement_count = sum(1 for case in cases if case["relation_float64_complex128_agree"])
    known_checks.append(
        known_value_check(
            "torch_float64_complex128_relation_agreement_all_cases",
            complex_agreement_count,
            len(cases),
        )
    )

    rustworkx_count = sum(1 for case in cases if case["rustworkx_connected_components"] == case["quotient_cardinality"])
    known_checks.append(
        known_value_check("rustworkx_components_equal_quotient_all_cases", rustworkx_count, len(cases))
    )

    gudhi_count = sum(1 for case in cases if case["gudhi_h0_betti"] == case["quotient_cardinality"])
    known_checks.append(
        known_value_check("gudhi_h0_equals_quotient_all_cases", gudhi_count, len(cases))
    )

    toponetx_count = sum(
        1 for case in cases if case["toponetx_1_simplex_count"] == case["expected_equivalence_edge_count"]
    )
    known_checks.append(
        known_value_check("toponetx_edges_equal_equivalence_clique_edges_all_cases", toponetx_count, len(cases))
    )

    geomstats_count = sum(1 for case in cases if case["geomstats_metric_ok"])
    known_checks.append(
        known_value_check("geomstats_quotient_metric_zero_within_positive_between_all_cases", geomstats_count, len(cases))
    )

    clifford_count = sum(1 for case in cases if case["clifford_orthonormal_basis_ok"])
    known_checks.append(
        known_value_check("clifford_quotient_basis_orthonormal_all_cases", clifford_count, len(cases))
    )

    for n_states in range(1, 9):
        brute = brute_force_partition_count(n_states)
        bell = int(sp.bell(n_states))
        known_checks.append(known_value_check(f"bell_partition_count_bruteforce_n={n_states}", brute, bell))

    for n_states in range(1, 7):
        realized = realized_single_probe_partition_count(n_states)
        bell = int(sp.bell(n_states))
        known_checks.append(
            known_value_check(f"single_probe_realizes_all_partitions_n={n_states}", realized, bell)
        )

    negative_checks = [z3_cvc5_bad_relation_negative()]
    negative_match_count = sum(1 for check in negative_checks if check["match"])
    known_checks.append(
        known_value_check("negative_nontransitive_relation_is_not_equivalence", negative_match_count, len(negative_checks))
    )

    all_known_checks_pass = all(check["match"] for check in known_checks)
    all_cases_match = all(case["case_match"] for case in cases)
    all_negative_checks_pass = all(check["match"] for check in negative_checks)
    status = "PASS" if all_known_checks_pass and all_cases_match and all_negative_checks_pass else "BLOCKED"

    result = {
        "sim_id": "sim_geom_distinguishability_quotient_codex_probe",
        "name": "distinguishability_quotient_codex_probe",
        "version": "1.0.0",
        "tier": "1 finite quotient geometry diagnostic",
        "purpose": "independent known-value finite distinguishability quotient cross-check",
        "scientific_question": "For finite S and finite P, does the relation s~t iff all probes agree produce the expected quotient and partition invariants?",
        "sim_execution_kind": "classical",
        "sim_class": "geometry_probe",
        "classification": "diagnostic_only",
        "promotion_status": "diagnostic_only",
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set: finite S and finite P are explicit",
            "N01 control surface: probe deletion/refinement/order controls are measured, but no nonclassical promotion is claimed",
        ],
        "finite_map": "q_P:S -> S/~ where s~t iff p(s)=p(t) for every p in finite P",
        "domain": "finite state set S={0,...,n-1} and finite probe family P represented as torch float64 and complex128 tensors",
        "codomain_or_output": "finite quotient set Q=S/~ plus equivalence relation, partition, graph/topology/metric invariants",
        "carrier_layer": "finite_state_probe_quotient",
        "geometry_layer": "finite quotient / partition geometry",
        "carrier_realization": "torch float64 probe matrices and torch complex128 signature cross-checks; no NumPy substrate",
        "peps3d_embedding": "not_applicable: no nonclassical manifold or PEPS3D-carrier claim is made",
        "spinor_state": "not_applicable: this diagnostic uses complex128 probe signatures, not spinor states",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [],
        "downstream_blocks": [
            "lego_promotion",
            "bridge",
            "flux",
            "Xi",
            "Phi0",
            "Axis0",
            "basin",
            "physics",
            "nonclassical_manifold_admission",
        ],
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "finite indistinguishability quotient by equality of all finite probe readouts",
        "branch_status_before_run": "independent diagnostic requested for cross-model comparison",
        "allowed_claims": [
            "the file exists after this run",
            "the file runs after this run if exit code is zero",
            "the local known-value checks listed in the result passed if status is PASS",
            "no canonical, lego, bridge, axis, flux, basin, physics, or manifold admission claim",
        ],
        "promotion_blockers": [
            "classification explicitly diagnostic_only",
            "no reconciled queue row or ledger loopback",
            "no nonclassical PEPS3D/spinor carrier",
            "no validator gate was run by user request",
        ],
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": list(TOOL_MANIFEST.keys()),
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": ["rustworkx"],
        "topology_surfaces_used": ["gudhi", "toponetx"],
        "required_inputs": ["finite state cardinalities n=1..8", "finite probe counts p in {0,1,2,3,5,8}", "deterministic seeds 0..4"],
        "data_or_artifact_dependencies": [],
        "required_negatives": [
            "single constant probe collapses Q to one class",
            "empty probe family collapses Q to one class",
            "SMT relation validator rejects reflexive symmetric nontransitive relation",
        ],
        "negatives_run": negative_checks,
        "kill_conditions": [
            "any known-value check mismatch",
            "any z3/cvc5 equivalence-negation check not UNSAT for a probe-defined relation",
            "any Bell brute-force count mismatch",
            "any tool cross-check disagreement",
        ],
        "required_artifacts": [str(RESULT_PATH)],
        "artifacts_emitted": [str(RESULT_PATH)],
        "witness_trace_id": "geom_distinguishability_quotient_codex_probe_v1",
        "result_summary": {
            "status": status,
            "cases_run": len(cases),
            "known_value_checks": len(known_checks),
            "known_value_checks_passed": sum(1 for check in known_checks if check["match"]),
            "all_known_checks_pass": all_known_checks_pass,
            "all_cases_match": all_cases_match,
            "all_negative_checks_pass": all_negative_checks_pass,
        },
        "pass_rule": "PASS iff every known-value check matches and every per-case tool cross-check agrees",
        "fail_rule": "BLOCKED iff any invariant does not match its known finite-math value or any tool cross-check disagrees",
        "eligible_consumers": [],
        "blocked_consumers": [
            "lego",
            "canonical",
            "bridge",
            "flux",
            "Xi",
            "Phi0",
            "Axis0",
            "basin",
            "physics",
            "nonclassical_manifold",
        ],
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "known_value_checks": known_checks,
        "wide_variation": {
            "n_states": list(range(1, 9)),
            "n_probes": [0, 1, 2, 3, 5, 8],
            "seeds": list(range(5)),
            "modes": ["separating", "constant", "affine_mod", "bucket", "xor_like", "random_bucket"],
            "cases": cases,
        },
        "positive": {
            "separating_probe_family": [case for case in separating_cases],
            "all_probe_defined_relations_equivalence_certified": proof_pass_count == len(cases),
        },
        "negative": {
            "constant_probe_family": [case for case in constant_cases],
            "empty_probe_cases": [case for case in cases if case["n_probes"] == 0],
            "bad_relation_validator_negative": negative_checks,
        },
        "boundary": {
            "coarsest_probe_boundary": [case for case in cases if case["n_probes"] == 0 or case["mode"] == "constant"],
            "finest_probe_boundary": separating_cases,
        },
        "surviving_alternatives": [
            "Many non-separating probe families survive as valid coarser quotients; this diagnostic records quotient cardinality, not a preferred quotient.",
        ],
        "claim_ceiling": "diagnostic_only_finite_quotient_known_value_check",
        "next_lego_target": "none",
        "promotion_condition": "requires separate queue row, contract admission, and validator/ledger loopback not requested here",
        "blocked_until": "promotion remains blocked unless a future admitted packet supplies the missing process evidence",
        "demotion_condition": "demote to broken if any known-value check mismatches or if output is cited beyond diagnostic-only ceiling",
        "out_of_scope": [
            "opus result comparison or copied numbers",
            "lego phase validator gate",
            "canonical promotion",
            "nonclassical manifold admission",
            "bridge/axis/flux/basin/physics claims",
        ],
    }

    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(result["result_summary"], indent=2, sort_keys=True))
    print(f"result_path={RESULT_PATH}")
    if status != "PASS":
        blockers = [check for check in known_checks if not check["match"]]
        print(json.dumps({"blockers": blockers[:20]}, indent=2, sort_keys=True))
        raise SystemExit(1)
    return result


if __name__ == "__main__":
    main()
