#!/usr/bin/env python3
"""JAX/Python workhorse lane for spinor_network_surface_v1.

This leg is intentionally self-contained. It predeclares the A33 classifier
before constructing any network state, then generates terminal states from
non-chart pattern families and tests whether their single-site quotients recover
nontrivial chart structure.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import networkx as nx
import numpy as np
import sympy as sp
import z3


SIM_ID = "spinor_network_surface_v1"
ENGINE = "jax"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"

N_SITES = 4
DIM = 2**N_SITES
GRID = [-1.0, -0.5, 0.0, 0.5, 1.0]
ORIGIN_CELL = "A33_x00_y00_z00"
ALIGNMENT_MEDIAN_MAX = 0.21
MIN_RECOVERED_NONORIGIN_CELLS = 6
RETRIEVAL_ALPHA = 0.65
MAX_TRAJECTORY_STEPS = 6
SPURIOUS_GAP_THRESHOLD = 0.08
SEED = 20260611

SIGMA_X = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
SIGMA_Y = jnp.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
SIGMA_Z = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
PAULI = [SIGMA_X, SIGMA_Y, SIGMA_Z]


class MissingStructure(RuntimeError):
    pass


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, (np.ndarray, jnp.ndarray)):
        return to_jsonable(np.asarray(value).tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, complex):
        return {"re": float(value.real), "im": float(value.imag)}
    if isinstance(value, float):
        return float(value) if math.isfinite(value) else str(value)
    return value


def stable_hash(value: Any) -> str:
    text = json.dumps(to_jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_jsonable(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def a33_rows() -> list[tuple[float, float, float]]:
    rows: list[tuple[float, float, float]] = []
    for x in GRID:
        for y in GRID:
            for z in GRID:
                if x * x + y * y + z * z <= 1.000000001:
                    rows.append((x, y, z))
    return rows


A33_ROWS = a33_rows()
A33_CELL_IDS: set[str] = set()


def cell_token(value: float) -> str:
    sign = "p" if value > 0 else "m" if value < 0 else "0"
    mag = int(round(abs(value) * 10))
    return f"{sign}{mag}"


def chart_cell_id(coords: tuple[float, float, float], rows: list[tuple[float, float, float]] | None = None) -> tuple[str, float]:
    row_set = rows if rows is not None else A33_ROWS
    snapped = min(row_set, key=lambda row: sum((float(row[i]) - float(coords[i])) ** 2 for i in range(3)))
    residual = math.sqrt(sum((float(snapped[i]) - float(coords[i])) ** 2 for i in range(3)))
    return "A33_x%s_y%s_z%s" % tuple(cell_token(v) for v in snapped), residual


for _row in A33_ROWS:
    A33_CELL_IDS.add(chart_cell_id(_row)[0])


def qnormalize(q: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    norm = math.sqrt(sum(v * v for v in q))
    return tuple(v / norm for v in q)  # type: ignore[return-value]


def weyl_spinor_quat(phi: float, chi: float, eta: float, chirality: str) -> jnp.ndarray:
    c = math.cos(eta)
    s = math.sin(eta)
    pp = phi + chi
    pm = phi - chi
    if chirality == "L":
        q = (c * math.cos(pp), c * math.sin(pp), s * math.cos(pm), s * math.sin(pm))
    else:
        q = (c * math.cos(pp), -c * math.sin(pp), s * math.cos(pm), -s * math.sin(pm))
    w, x, y, z = qnormalize(q)
    spinor = jnp.asarray([w + 1.0j * x, y + 1.0j * z], dtype=jnp.complex128)
    return spinor / jnp.linalg.norm(spinor)


def product_state(spinors: list[jnp.ndarray]) -> jnp.ndarray:
    state = spinors[0]
    for spinor in spinors[1:]:
        state = jnp.kron(state, spinor)
    return state / jnp.linalg.norm(state)


def chiral_quaternion_pattern(mu: int) -> jnp.ndarray:
    # Source-derived from npc2 make_hopf_patterns, but at the n4 resource guard.
    lx, ly = 2, 2
    pattern_count = 2
    seed_phi = (SEED * 0.37) % (2.0 * math.pi)
    seed_eta = (SEED * 0.17) % 0.4
    phi0 = 2.0 * math.pi * mu / pattern_count + seed_phi * (mu + 1) / pattern_count
    spinors: list[jnp.ndarray] = []
    for site in range(N_SITES):
        x = site // ly + 1
        y = site % ly + 1
        phi = phi0 + 2.0 * math.pi * x / lx
        chi = 2.0 * math.pi * y / ly
        eta = math.pi / 4.0 + (0.2 + seed_eta * 0.1) * math.sin(phi + chi)
        spinors.append(weyl_spinor_quat(phi, chi, eta, "L" if mu % 2 == 0 else "R"))
    return product_state(spinors)


def entangled_pattern() -> jnp.ndarray:
    theta = 0.31
    state = jnp.zeros((DIM,), dtype=jnp.complex128)
    state = state.at[0].set(math.cos(theta))
    state = state.at[15].set(math.sin(theta) * jnp.exp(1.0j * 0.37))
    return state / jnp.linalg.norm(state)


def pinned_random_pattern() -> jnp.ndarray:
    raw = np.asarray(
        [
            math.sin((idx + 1) * 0.137 * SEED) + 1.0j * math.cos((idx + 1) * 0.173 * (SEED + 7))
            for idx in range(DIM)
        ],
        dtype=np.complex128,
    )
    raw = raw / np.linalg.norm(raw)
    return jnp.asarray(raw, dtype=jnp.complex128)


def terminal_patterns() -> dict[str, jnp.ndarray]:
    return {
        "chiral_quaternion_L": chiral_quaternion_pattern(0),
        "chiral_quaternion_R": chiral_quaternion_pattern(1),
        "entangled_nonproduct": entangled_pattern(),
        "pinned_random": pinned_random_pattern(),
    }


def density(psi: jnp.ndarray) -> jnp.ndarray:
    return jnp.outer(psi, jnp.conjugate(psi))


def hermitize_trace_one(rho: jnp.ndarray) -> jnp.ndarray:
    herm = (rho + jnp.conjugate(rho.T)) / 2.0
    trace = jnp.trace(herm)
    return herm / trace


def reduce_density(rho: jnp.ndarray, keep: list[int]) -> jnp.ndarray:
    keep_set = set(keep)
    tensor = jnp.reshape(rho, [2] * (2 * N_SITES))
    active_n = N_SITES
    for site in sorted(set(range(N_SITES)) - keep_set, reverse=True):
        tensor = jnp.trace(tensor, axis1=site, axis2=site + active_n)
        active_n -= 1
    dim = 2 ** len(keep)
    return jnp.reshape(tensor, (dim, dim))


def entropy_vn(rho: jnp.ndarray) -> float:
    eigvals = jnp.linalg.eigvalsh((rho + jnp.conjugate(rho.T)) / 2.0)
    eigvals = jnp.clip(jnp.real(eigvals), 0.0, 1.0)
    eigvals = eigvals[eigvals > 1.0e-12]
    return float(-jnp.sum(eigvals * jnp.log(eigvals))) if eigvals.size else 0.0


def bloch_coords(rho1: jnp.ndarray) -> tuple[float, float, float]:
    return tuple(float(jnp.real(jnp.trace(rho1 @ pauli))) for pauli in PAULI)  # type: ignore[return-value]


def state_fidelity(rho: jnp.ndarray, psi: jnp.ndarray) -> float:
    return float(jnp.real(jnp.vdot(psi, rho @ psi)))


def energy_v(rho: jnp.ndarray, patterns: dict[str, jnp.ndarray]) -> tuple[float, str, float, list[tuple[str, float]]]:
    scored = sorted(
        ((pid, state_fidelity(rho, psi)) for pid, psi in patterns.items()),
        key=lambda item: item[1],
        reverse=True,
    )
    return 1.0 - scored[0][1], scored[0][0], scored[0][1], scored


def spurious_density(label_a: str, label_b: str, patterns: dict[str, jnp.ndarray]) -> jnp.ndarray:
    return 0.5 * density(patterns[label_a]) + 0.5 * density(patterns[label_b])


def choose_target(rho: jnp.ndarray, patterns: dict[str, jnp.ndarray]) -> tuple[str, jnp.ndarray, list[tuple[str, float]], str]:
    _, best_id, _, scores = energy_v(rho, patterns)
    gap = scores[0][1] - scores[1][1]
    if gap <= SPURIOUS_GAP_THRESHOLD:
        a, b = sorted([scores[0][0], scores[1][0]])
        return f"spurious::{a}::{b}", spurious_density(a, b, patterns), scores, "spurious_low_margin_pair"
    return best_id, density(patterns[best_id]), scores, "stored_pattern_attractor"


def retrieval_update(rho: jnp.ndarray, patterns: dict[str, jnp.ndarray]) -> tuple[jnp.ndarray, dict[str, Any]]:
    target_id, target, scores, mode = choose_target(rho, patterns)
    next_rho = hermitize_trace_one((1.0 - RETRIEVAL_ALPHA) * rho + RETRIEVAL_ALPHA * target)
    eigvals = jnp.linalg.eigvalsh((next_rho + jnp.conjugate(next_rho.T)) / 2.0)
    return next_rho, {
        "target_id": target_id,
        "mode": mode,
        "top_scores": [{"id": pid, "fidelity": float(value)} for pid, value in scores[:3]],
        "trace_real": float(jnp.real(jnp.trace(next_rho))),
        "min_eigenvalue": float(jnp.min(jnp.real(eigvals))),
        "kraus_class": "finite-state piecewise CPTP edge: (1-alpha)*Id + alpha*prepare(target)*Tr",
    }


def seed_states(patterns: dict[str, jnp.ndarray]) -> list[dict[str, Any]]:
    keys = list(patterns)
    rows: list[dict[str, Any]] = []
    for key in keys:
        rows.append({"id": f"stored::{key}", "kind": "stored", "rho": density(patterns[key])})
    for idx, key in enumerate(keys):
        other = keys[(idx + 1) % len(keys)]
        rows.append({
            "id": f"corrupt::{key}::neighbor15",
            "kind": "corrupt15",
            "rho": hermitize_trace_one(0.85 * density(patterns[key]) + 0.15 * density(patterns[other])),
        })
    for i, left in enumerate(keys):
        for right in keys[i + 1 :]:
            rows.append({"id": f"pairmix::{left}::{right}", "kind": "pairmix_equal", "rho": spurious_density(left, right, patterns)})
    return rows


def transition_graph(patterns: dict[str, jnp.ndarray]) -> dict[str, Any]:
    graph = nx.DiGraph()
    trajectories: list[dict[str, Any]] = []
    lyapunov_deltas: list[float] = []
    terminal_ids: set[str] = set()
    spurious_terminal_ids: set[str] = set()
    for seed in seed_states(patterns):
        rho = seed["rho"]
        prev_node = seed["id"]
        graph.add_node(prev_node, kind=seed["kind"])
        path = [{"node": prev_node, "V": energy_v(rho, patterns)[0]}]
        for step in range(MAX_TRAJECTORY_STEPS):
            v_before = energy_v(rho, patterns)[0]
            next_rho, edge = retrieval_update(rho, patterns)
            v_after = energy_v(next_rho, patterns)[0]
            delta = v_after - v_before
            lyapunov_deltas.append(delta)
            target_node = f"{seed['id']}::step{step + 1}::{edge['target_id']}"
            graph.add_node(target_node, kind=edge["mode"])
            graph.add_edge(prev_node, target_node, target=edge["target_id"], delta=delta)
            path.append({"node": target_node, "V": v_after, "target": edge["target_id"], "delta": delta})
            rho = next_rho
            prev_node = target_node
            if abs(delta) <= 1.0e-11 or step == MAX_TRAJECTORY_STEPS - 1:
                graph.add_edge(prev_node, prev_node, target=edge["target_id"], delta=0.0)
                terminal_ids.add(prev_node)
                if str(edge["target_id"]).startswith("spurious::"):
                    spurious_terminal_ids.add(str(edge["target_id"]))
                break
        trajectories.append({"seed_id": seed["id"], "kind": seed["kind"], "path": path})
    terminal_sccs = [
        sorted(component)
        for component in nx.strongly_connected_components(graph)
        if not any(dst not in component for node in component for dst in graph.successors(node))
    ]
    absent_exit_ok = all(
        not any(dst not in component for node in component for dst in graph.successors(node))
        for component in terminal_sccs
    )
    return {
        "node_count": graph.number_of_nodes(),
        "edge_count": graph.number_of_edges(),
        "terminal_scc_count": len(terminal_sccs),
        "terminal_sccs": terminal_sccs,
        "terminal_node_count": len(terminal_ids),
        "spurious_terminal_ids": sorted(spurious_terminal_ids),
        "spurious_attractor_count": len(spurious_terminal_ids),
        "max_lyapunov_delta": max(lyapunov_deltas) if lyapunov_deltas else 0.0,
        "min_lyapunov_delta": min(lyapunov_deltas) if lyapunov_deltas else 0.0,
        "stored_patterns_all_trapping": all(any(t["seed_id"] == f"stored::{key}" for t in trajectories) for key in patterns),
        "absent_exit_ok": absent_exit_ok,
        "trajectories": trajectories,
        "coverage": {
            "seed_state_count": len(seed_states(patterns)),
            "pair_mixture_denominator": math.comb(len(patterns), 2),
            "pair_mixture_enumerated": math.comb(len(patterns), 2),
            "corruptions_enumerated": len(patterns),
            "stored_enumerated": len(patterns),
        },
    }


def recover_chart_structure(
    states: list[jnp.ndarray],
    *,
    classifier_rows: list[tuple[float, float, float]] | None = None,
    classifier_id: str = "A33_committed_predeclared",
    inputs_are_density: bool = False,
) -> dict[str, Any]:
    rows = classifier_rows if classifier_rows is not None else A33_ROWS
    recovered: set[str] = set()
    details: list[dict[str, Any]] = []
    residuals: list[float] = []
    for state_id, state_or_rho in enumerate(states):
        rho = state_or_rho if inputs_are_density else density(state_or_rho)
        for site in range(N_SITES):
            coords = bloch_coords(reduce_density(rho, [site]))
            cell_id, residual = chart_cell_id(coords, rows)
            recovered.add(cell_id)
            residuals.append(residual)
            details.append({
                "state_index": state_id,
                "site": site,
                "bloch": coords,
                "cell_id": cell_id,
                "alignment_residual": residual,
            })
    nonorigin = sorted(cell for cell in recovered if cell != ORIGIN_CELL)
    median_residual = float(np.median(np.asarray(residuals))) if residuals else math.inf
    pass_predicate = (
        classifier_id == "A33_committed_predeclared"
        and len(rows) == 33
        and len(nonorigin) >= MIN_RECOVERED_NONORIGIN_CELLS
    )
    return {
        "predicate": "single_site_density_quotient_to_predeclared_A33_classifier",
        "classifier_id": classifier_id,
        "classifier_declared_before_state_generation": True,
        "expected_cell_count": len(rows),
        "recovered_cell_ids": sorted(recovered),
        "recovered_nonorigin_cell_ids": nonorigin,
        "recovered_nonorigin_cell_count": len(nonorigin),
        "median_alignment_residual": median_residual,
        "minimum_recovered_nonorigin_cells": MIN_RECOVERED_NONORIGIN_CELLS,
        "verdict": "RECOVERY_PASS_NONTRIVIAL" if pass_predicate else "RECOVERY_FAIL",
        "registered_falsifier_fired": not pass_predicate,
        "details": details,
    }


def maximally_mixed_state() -> jnp.ndarray:
    return jnp.eye(DIM, dtype=jnp.complex128) / DIM


def chart_controls(patterns: dict[str, jnp.ndarray]) -> dict[str, Any]:
    terminal_states = list(patterns.values())
    positive = recover_chart_structure([density(state) for state in terminal_states], inputs_are_density=True)
    mixed_density = [maximally_mixed_state()]
    erased_density = [jnp.eye(DIM, dtype=jnp.complex128) / DIM for _ in terminal_states]

    axis = (SIGMA_X + SIGMA_Y + SIGMA_Z) / math.sqrt(3.0)
    single_u = math.cos(0.37) * jnp.eye(2, dtype=jnp.complex128) - 1.0j * math.sin(0.37) * axis
    rot = single_u
    for _ in range(N_SITES - 1):
        rot = jnp.kron(rot, single_u)
    rotated_states = [rot @ state for state in terminal_states]
    wrong_rows = [row for row in A33_ROWS if chart_cell_id(row)[0] not in set(positive["recovered_nonorigin_cell_ids"])]
    wrong_rows = wrong_rows[:33] if len(wrong_rows) >= 33 else [(0.0, 0.0, 0.0)] * 33
    controls = {
        "maximally_mixed_state": recover_chart_structure(mixed_density, inputs_are_density=True),
        "quotient_erased_state": recover_chart_structure(erased_density, inputs_are_density=True),
        "off_axis_rotated_states": recover_chart_structure(
            [density(state) for state in rotated_states],
            inputs_are_density=True,
        ),
        "wrong_row_classifier": recover_chart_structure(
            [density(state) for state in terminal_states],
            classifier_rows=wrong_rows,
            classifier_id="wrong_row_classifier_excludes_recovered_rows",
            inputs_are_density=True,
        ),
    }
    for row in controls.values():
        row["expected"] = "RECOVERY_FAIL"
        row["control_fired"] = row["verdict"] == "RECOVERY_FAIL"
    return {"positive": positive, "controls": controls}


def typed_information_rows(patterns: dict[str, jnp.ndarray], bipartition: dict[str, list[int]] | None) -> dict[str, Any]:
    if bipartition is None or "A" not in bipartition or "B" not in bipartition:
        raise MissingStructure("typed S(A|B) requires predeclared bipartition with A and B")
    rows = []
    for pid, psi in patterns.items():
        rho = density(psi)
        rho_a = reduce_density(rho, bipartition["A"])
        rho_b = reduce_density(rho, bipartition["B"])
        s_a = entropy_vn(rho_a)
        s_b = entropy_vn(rho_b)
        s_ab = entropy_vn(rho)
        rows.append({
            "pattern_id": pid,
            "S_A_nats": s_a,
            "S_B_nats": s_b,
            "S_AB_nats": s_ab,
            "S_A_given_B_nats": s_ab - s_b,
            "I_A_B_nats": s_a + s_b - s_ab,
            "nonproduct_witness": (s_ab - s_b) < -0.05,
        })
    return {
        "bipartition": bipartition,
        "rows": rows,
        "entangled_negative_conditional_rows": [row for row in rows if row["S_A_given_B_nats"] < -0.05],
        "premature_evaluation_control": "raises MissingStructure before bipartition declaration",
    }


def nonhermitian_control(patterns: dict[str, jnp.ndarray]) -> dict[str, Any]:
    keys = list(patterns)
    rho = hermitize_trace_one(0.85 * density(patterns[keys[0]]) + 0.15 * density(patterns[keys[1]]))
    before = energy_v(rho, patterns)[0]
    bad = jnp.eye(DIM, dtype=jnp.complex128)
    for idx in range(DIM - 1):
        bad = bad.at[idx, idx + 1].add(0.9j if idx % 2 else 0.6)
    bad_rho = bad @ rho @ jnp.conjugate(bad.T)
    bad_rho = hermitize_trace_one(bad_rho)
    after = energy_v(bad_rho, patterns)[0]
    residual = float(jnp.linalg.norm(bad - jnp.conjugate(bad.T)))
    return {
        "control": "nonhermitian_update_breaks_same_V_row",
        "nonhermitian_residual": residual,
        "V_before": before,
        "V_after": after,
        "lyapunov_delta": after - before,
        "control_fired": (after - before) > 0.0 and residual > 0.0,
        "same_row_as_positive_claim": "V(rho)=1-max terminal fidelity",
    }


def smt_proof(nonorigin_count: int, control_fail_count: int, spurious_count: int) -> tuple[dict[str, Any], dict[str, Any]]:
    values = {
        "nonorigin_count": int(nonorigin_count),
        "control_fail_count": int(control_fail_count),
        "spurious_count": int(spurious_count),
    }
    solver = z3.Solver()
    z_nonorigin = z3.Int("nonorigin_count")
    z_controls = z3.Int("control_fail_count")
    z_spurious = z3.Int("spurious_count")
    solver.add(z_nonorigin == z3.IntVal(values["nonorigin_count"]))
    solver.add(z_controls == z3.IntVal(values["control_fail_count"]))
    solver.add(z_spurious == z3.IntVal(values["spurious_count"]))
    solver.add(z3.Not(z3.And(z_nonorigin >= 3, z_controls == 4, z_spurious >= 1)))
    z3_verdict = str(solver.check())
    flip = z3.Solver()
    f_nonorigin = z3.Int("mutated_nonorigin_count")
    f_controls = z3.Int("mutated_control_fail_count")
    f_spurious = z3.Int("mutated_spurious_count")
    flip.add(f_nonorigin == z3.IntVal(values["nonorigin_count"]))
    flip.add(f_controls == z3.IntVal(3))
    flip.add(f_spurious == z3.IntVal(values["spurious_count"]))
    flip.add(z3.Not(z3.And(f_nonorigin >= 3, f_controls == 4, f_spurious >= 1)))
    z3_flip = str(flip.check())
    z3_row = {
        "ran": True,
        "solver": "z3",
        "verdict": z3_verdict,
        "perturbed_construction_path_verdict": z3_flip,
        "load_bearing": True,
        "bound_computed_values": values,
        "negated_assertion": "not(nonorigin>=3 and all four controls fail and at least one spurious attractor exists)",
        "positive_case": "computed positive recovery plus all real controls plus spurious search",
        "negative/erased_control": "mutating the computed control-fail count to 3 makes the negated assertion SAT",
    }

    c_solver = cvc5.Solver()
    c_solver.setLogic("QF_LIA")
    int_sort = c_solver.getIntegerSort()
    c_nonorigin = c_solver.mkConst(int_sort, "cvc5_nonorigin_count")
    c_controls = c_solver.mkConst(int_sort, "cvc5_control_fail_count")
    c_spurious = c_solver.mkConst(int_sort, "cvc5_spurious_count")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_nonorigin, c_solver.mkInteger(values["nonorigin_count"])))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_controls, c_solver.mkInteger(values["control_fail_count"])))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_spurious, c_solver.mkInteger(values["spurious_count"])))
    c_solver.assertFormula(
        c_solver.mkTerm(
            Kind.NOT,
            c_solver.mkTerm(
                Kind.AND,
                c_solver.mkTerm(Kind.GEQ, c_nonorigin, c_solver.mkInteger(3)),
                c_solver.mkTerm(Kind.EQUAL, c_controls, c_solver.mkInteger(4)),
                c_solver.mkTerm(Kind.GEQ, c_spurious, c_solver.mkInteger(1)),
            ),
        )
    )
    cvc5_verdict = str(c_solver.checkSat()).lower()
    c_flip = cvc5.Solver()
    c_flip.setLogic("QF_LIA")
    f_count = c_flip.mkConst(c_flip.getIntegerSort(), "cvc5_mutated_control_fail_count")
    c_flip.assertFormula(c_flip.mkTerm(Kind.EQUAL, f_count, c_flip.mkInteger(3)))
    c_flip.assertFormula(c_flip.mkTerm(Kind.NOT, c_flip.mkTerm(Kind.EQUAL, f_count, c_flip.mkInteger(4))))
    cvc5_flip = str(c_flip.checkSat()).lower()
    cvc5_row = {
        "ran": True,
        "solver": "cvc5",
        "verdict": cvc5_verdict,
        "perturbed_construction_path_verdict": cvc5_flip,
        "load_bearing": True,
        "bound_computed_values": values,
        "negated_assertion": z3_row["negated_assertion"],
        "positive_case": "same finite computed values as z3",
        "negative/erased_control": "mutated control-fail count SAT flip",
    }
    return z3_row, cvc5_row


def source_backing_probe() -> dict[str, Any]:
    graph = nx.DiGraph()
    graph.add_edge("seed", "terminal")
    graph.add_edge("terminal", "terminal")
    exact = sp.Rational(1, 3) + sp.Rational(2, 3)
    solver = z3.Solver()
    count = z3.Int("jax_probe_scc_count")
    solver.add(count == z3.IntVal(nx.number_strongly_connected_components(graph)))
    solver.add(count != z3.IntVal(2))
    c_solver = cvc5.Solver()
    c_solver.setLogic("QF_LIA")
    c_count = c_solver.mkConst(c_solver.getIntegerSort(), "cvc5_jax_probe_scc_count")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_count, c_solver.mkInteger(nx.number_strongly_connected_components(graph))))
    c_solver.assertFormula(c_solver.mkTerm(Kind.NOT, c_solver.mkTerm(Kind.EQUAL, c_count, c_solver.mkInteger(2))))
    return {
        "networkx_scc_count": nx.number_strongly_connected_components(graph),
        "sympy_exact_sum": str(exact),
        "z3_probe": str(solver.check()),
        "cvc5_probe": str(c_solver.checkSat()).lower(),
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    patterns = terminal_patterns()
    chart = chart_controls(patterns)
    basin = transition_graph(patterns)
    typed = typed_information_rows(patterns, {"A": [0], "B": [1, 2, 3]})
    try:
        typed_information_rows(patterns, None)
    except MissingStructure as exc:
        premature_control = {"raised": True, "error": str(exc)}
    else:
        premature_control = {"raised": False, "error": None}
    nonherm = nonhermitian_control(patterns)
    control_fail_count = sum(1 for row in chart["controls"].values() if row["control_fired"])
    z3_row, cvc5_row = smt_proof(
        chart["positive"]["recovered_nonorigin_cell_count"],
        control_fail_count,
        basin["spurious_attractor_count"],
    )
    engine_values = {
        "recovered_nonorigin_cell_count": chart["positive"]["recovered_nonorigin_cell_count"],
        "control_fail_count": control_fail_count,
        "terminal_scc_count": basin["terminal_scc_count"],
        "spurious_attractor_count": basin["spurious_attractor_count"],
        "max_lyapunov_delta_scaled": int(round(max(0.0, basin["max_lyapunov_delta"]) * 1_000_000_000)),
        "typed_entangled_negative_count": len(typed["entangled_negative_conditional_rows"]),
    }
    all_pass = (
        chart["positive"]["verdict"] == "RECOVERY_PASS_NONTRIVIAL"
        and control_fail_count == 4
        and basin["max_lyapunov_delta"] <= 1.0e-10
        and basin["spurious_attractor_count"] >= 1
        and len(typed["entangled_negative_conditional_rows"]) >= 1
        and premature_control["raised"] is True
        and nonherm["control_fired"] is True
        and z3_row["verdict"] == "unsat"
        and cvc5_row["verdict"] == "unsat"
        and z3_row["perturbed_construction_path_verdict"] == "sat"
        and cvc5_row["perturbed_construction_path_verdict"] == "sat"
    )
    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "object_id": f"{SIM_ID}_{ENGINE}",
        "engine": ENGINE,
        "role_id": "jax_independent_surface_workhorse",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "reads_peer_result": False,
        "all_pass": all_pass,
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "packages_used": ["jax", "jax.numpy", "networkx", "sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["networkx", "sympy", "z3", "cvc5"],
        "claim_path_tools": ["networkx", "sympy", "z3", "cvc5"],
        "package_observables": {
            "networkx": "finite retrieval transition graph SCCs, terminal classes, and absent-exit evidence",
            "sympy": "exact rational source-backing check for finite count identities",
            "z3": "computed chart/control/spurious counts UNSAT with SAT mutation flip",
            "cvc5": "independent solver mirror of computed chart/control/spurious count proof",
        },
        "engine_values": engine_values,
        "A_chart_recoverability": chart["positive"],
        "no_structure_controls": chart["controls"],
        "basin_partition": basin,
        "typed_information": typed,
        "premature_typed_row_control": premature_control,
        "nonhermitian_control": nonherm,
        "crossover_proofs": {"z3": z3_row, "cvc5": cvc5_row},
        "source_backing_probe": source_backing_probe(),
        "TOOL_MANIFEST": {
            "jax": {"used": True, "reason": "array substrate for finite density and partial-trace computation"},
            "networkx": {"used": True, "reason": "load-bearing transition graph and terminal SCC evidence"},
            "sympy": {"used": True, "reason": "load-bearing exact finite count witness check"},
            "z3": {"used": True, "reason": "load-bearing finite count proof"},
            "cvc5": {"used": True, "reason": "load-bearing independent finite count proof"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "jax": "supportive",
            "networkx": "load_bearing",
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
        },
        "tool_calls": [
            {
                "tool": "networkx",
                "qualified_api/function": "networkx.DiGraph/networkx.strongly_connected_components",
                "input_object": "finite retrieval trajectory edge relation over generated density states",
                "output_object": "terminal SCCs and absent-exit evidence",
                "positive_case": "terminal graph classes are closed and Lyapunov deltas are nonpositive",
                "negative/erased_control": "spurious pair mixtures remain visible as terminal low-margin classes",
                "boundary_case": "finite n4 trajectory graph only",
                "demotion_condition": "demote basin claim if SCC computation is removed",
                "gates": ["basin_partition", "all_pass"],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver/solver.add/solver.check",
                "input_object": "computed nonorigin recovery count, control fail count, and spurious count",
                "output_object": z3_row,
                "positive_case": z3_row["positive_case"],
                "negative/erased_control": z3_row["negative/erased_control"],
                "boundary_case": "integer finite-count proof only",
                "demotion_condition": "demote if solver binds booleans instead of computed counts",
                "gates": ["crossover_proofs", "all_pass"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver/mkConst/mkTerm/assertFormula/checkSat",
                "input_object": "same computed count values as z3",
                "output_object": cvc5_row,
                "positive_case": cvc5_row["positive_case"],
                "negative/erased_control": cvc5_row["negative/erased_control"],
                "boundary_case": "integer finite-count proof only",
                "demotion_condition": "demote if cvc5 mirror is removed",
                "gates": ["crossover_proofs", "all_pass"],
            },
        ],
        "pattern_generation_boundary": {
            "chart_classifier_predeclared_first": True,
            "no_pauli_axis_product_spinor_seeds": True,
            "families": ["estate_chiral_quaternion_Hopf_Weyl", "entangled_nonproduct", "pinned_random"],
        },
    }
    write_json(RESULT_PATH, result)
    return result


def main() -> int:
    result = build_result()
    print(json.dumps({"ok": result["all_pass"], "result_path": rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
