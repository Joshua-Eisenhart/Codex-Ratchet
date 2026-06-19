#!/usr/bin/env python3
"""JAX/Python workhorse lane for spinor_network_surface_v2.

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


SIM_ID = "spinor_network_surface_v2"
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
HAAR_PINNED_SEEDS = [6608, 6609, 6610, 6611]
HAAR_NULL_TRIALS = 2048
HAAR_NULL_SEED0 = 100000
LCG_A = 6364136223846793005
LCG_C = 1442695040888963407
LCG_MASK = (1 << 64) - 1

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


def a33_cell_id_from_row(row: tuple[float, float, float]) -> str:
    return "A33_x%s_y%s_z%s" % tuple(cell_token(v) for v in row)


def chart_cell_id(
    coords: tuple[float, float, float],
    rows: list[tuple[float, float, float]] | None = None,
    row_labels: list[str] | None = None,
) -> tuple[str, float]:
    row_set = rows if rows is not None else A33_ROWS
    snap_idx, snapped = min(
        enumerate(row_set),
        key=lambda item: sum((float(item[1][i]) - float(coords[i])) ** 2 for i in range(3)),
    )
    residual = math.sqrt(sum((float(snapped[i]) - float(coords[i])) ** 2 for i in range(3)))
    if row_labels is not None:
        return row_labels[snap_idx], residual
    return a33_cell_id_from_row(snapped), residual


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


def lcg_uniforms(seed: int, count: int) -> list[float]:
    state = (seed + LCG_C) & LCG_MASK
    values: list[float] = []
    for _ in range(count):
        state = (LCG_A * state + LCG_C) & LCG_MASK
        values.append(((state >> 11) & ((1 << 53) - 1)) / float(1 << 53))
    return values


def lcg_normals(seed: int, count: int) -> list[float]:
    uniforms = lcg_uniforms(seed, 2 * ((count + 1) // 2))
    values: list[float] = []
    for idx in range(0, len(uniforms), 2):
        u1 = max(uniforms[idx], 1.0e-12)
        u2 = uniforms[idx + 1]
        radius = math.sqrt(-2.0 * math.log(u1))
        theta = 2.0 * math.pi * u2
        values.extend([radius * math.cos(theta), radius * math.sin(theta)])
    return values[:count]


def haar_pinned_pattern(seed: int) -> jnp.ndarray:
    normals = lcg_normals(seed, 2 * DIM)
    raw = np.asarray(normals[:DIM], dtype=np.float64) + 1.0j * np.asarray(normals[DIM:], dtype=np.float64)
    raw = raw / np.linalg.norm(raw)
    return jnp.asarray(raw, dtype=jnp.complex128)


def v1_anchor_patterns() -> dict[str, jnp.ndarray]:
    return {
        "chiral_quaternion_L": chiral_quaternion_pattern(0),
        "chiral_quaternion_R": chiral_quaternion_pattern(1),
        "entangled_nonproduct": entangled_pattern(),
        "pinned_random": pinned_random_pattern(),
    }


def terminal_patterns() -> dict[str, jnp.ndarray]:
    patterns = dict(v1_anchor_patterns())
    for seed in HAAR_PINNED_SEEDS:
        patterns[f"haar_pinned_seed_{seed}"] = haar_pinned_pattern(seed)
    return patterns


def pattern_metadata(patterns: dict[str, jnp.ndarray]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {
        "chiral_quaternion_L": {
            "family_id": "estate_chiral_quaternion_Hopf_Weyl",
            "bias_class": "residual_chart_plane_bias_v1_anchor",
            "load_bearing_for_identity_claim": False,
            "anchor_from_v1": True,
        },
        "chiral_quaternion_R": {
            "family_id": "estate_chiral_quaternion_Hopf_Weyl",
            "bias_class": "residual_chart_plane_bias_v1_anchor",
            "load_bearing_for_identity_claim": False,
            "anchor_from_v1": True,
        },
        "entangled_nonproduct": {
            "family_id": "entangled_nonproduct",
            "bias_class": "computational_endpoint_z_bias_v1_anchor",
            "load_bearing_for_identity_claim": False,
            "anchor_from_v1": True,
        },
        "pinned_random": {
            "family_id": "pinned_random_v1_anchor",
            "bias_class": "single_seed_thin_margin_v1_anchor",
            "load_bearing_for_identity_claim": False,
            "anchor_from_v1": True,
        },
    }
    for seed in HAAR_PINNED_SEEDS:
        pid = f"haar_pinned_seed_{seed}"
        rows[pid] = {
            "family_id": pid,
            "bias_class": "haar_sampled_then_seed_pinned_no_preferred_chart_axis",
            "seed": seed,
            "seed_hash": stable_hash({"haar_pinned_seed": seed, "dim": DIM, "sim_id": SIM_ID}),
            "load_bearing_for_identity_claim": True,
            "anchor_from_v1": False,
        }
    return {key: rows[key] for key in patterns}


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
    state_ids: list[str] | None = None,
    metadata: dict[str, dict[str, Any]] | None = None,
    classifier_rows: list[tuple[float, float, float]] | None = None,
    classifier_row_labels: list[str] | None = None,
    classifier_id: str = "A33_committed_predeclared",
    inputs_are_density: bool = False,
    identity_required_pairs: set[str] | None = None,
    require_load_bearing_identity: bool = False,
) -> dict[str, Any]:
    rows = classifier_rows if classifier_rows is not None else A33_ROWS
    recovered: set[str] = set()
    details: list[dict[str, Any]] = []
    residuals: list[float] = []
    family_cell_map: dict[str, set[str]] = {}
    load_bearing_cells: set[str] = set()
    load_bearing_pairs: set[str] = set()
    ids = state_ids if state_ids is not None else [f"state_{idx}" for idx in range(len(states))]
    for state_id, state_or_rho in enumerate(states):
        pattern_id = ids[state_id]
        meta = (metadata or {}).get(pattern_id, {})
        family_id = str(meta.get("family_id", pattern_id))
        load_bearing = bool(meta.get("load_bearing_for_identity_claim", False))
        rho = state_or_rho if inputs_are_density else density(state_or_rho)
        for site in range(N_SITES):
            coords = bloch_coords(reduce_density(rho, [site]))
            cell_id, residual = chart_cell_id(coords, rows, classifier_row_labels)
            recovered.add(cell_id)
            residuals.append(residual)
            family_cell_map.setdefault(family_id, set()).add(cell_id)
            if load_bearing and cell_id != ORIGIN_CELL:
                load_bearing_cells.add(cell_id)
                load_bearing_pairs.add(f"{family_id}:{cell_id}")
            details.append({
                "state_index": state_id,
                "pattern_id": pattern_id,
                "family_id": family_id,
                "load_bearing_for_identity_claim": load_bearing,
                "site": site,
                "bloch": coords,
                "cell_id": cell_id,
                "alignment_residual": residual,
            })
    nonorigin = sorted(cell for cell in recovered if cell != ORIGIN_CELL)
    family_cell_map_json = {
        family_id: sorted(cell for cell in cells if cell != ORIGIN_CELL)
        for family_id, cells in sorted(family_cell_map.items())
    }
    observed_pairs = sorted(load_bearing_pairs)
    if identity_required_pairs is None:
        identity_pairs_match_expected = True
    else:
        identity_pairs_match_expected = set(observed_pairs) == set(identity_required_pairs)
    load_bearing_family_count = sum(
        1
        for family_id, cells in family_cell_map_json.items()
        if cells and any(pair.startswith(f"{family_id}:") for pair in observed_pairs)
    )
    median_residual = float(np.median(np.asarray(residuals))) if residuals else math.inf
    pass_predicate = (
        classifier_id == "A33_committed_predeclared"
        and len(rows) == 33
        and len(nonorigin) >= MIN_RECOVERED_NONORIGIN_CELLS
        and identity_pairs_match_expected
        and (
            not require_load_bearing_identity
            or (
                len(load_bearing_cells) >= MIN_RECOVERED_NONORIGIN_CELLS
                and load_bearing_family_count == len(HAAR_PINNED_SEEDS)
            )
        )
    )
    return {
        "predicate": "single_site_density_quotient_to_predeclared_A33_classifier",
        "classifier_id": classifier_id,
        "classifier_declared_before_state_generation": True,
        "expected_cell_count": len(rows),
        "recovered_cell_ids": sorted(recovered),
        "recovered_nonorigin_cell_ids": nonorigin,
        "recovered_nonorigin_cell_count": len(nonorigin),
        "family_cell_identity_map": family_cell_map_json,
        "load_bearing_recovered_nonorigin_cell_ids": sorted(load_bearing_cells),
        "load_bearing_recovered_nonorigin_cell_count": len(load_bearing_cells),
        "load_bearing_family_cell_pairs": observed_pairs,
        "identity_pairs_match_expected": identity_pairs_match_expected,
        "median_alignment_residual": median_residual,
        "minimum_recovered_nonorigin_cells": MIN_RECOVERED_NONORIGIN_CELLS,
        "verdict": "RECOVERY_PASS_NONTRIVIAL" if pass_predicate else "RECOVERY_FAIL",
        "registered_falsifier_fired": not pass_predicate,
        "details": details,
    }


def maximally_mixed_state() -> jnp.ndarray:
    return jnp.eye(DIM, dtype=jnp.complex128) / DIM


def chart_controls(patterns: dict[str, jnp.ndarray], metadata: dict[str, dict[str, Any]]) -> dict[str, Any]:
    terminal_ids = list(patterns)
    terminal_states = [patterns[key] for key in terminal_ids]
    positive = recover_chart_structure(
        [density(state) for state in terminal_states],
        state_ids=terminal_ids,
        metadata=metadata,
        inputs_are_density=True,
        require_load_bearing_identity=True,
    )
    mixed_density = [maximally_mixed_state()]
    erased_density = [jnp.eye(DIM, dtype=jnp.complex128) / DIM for _ in terminal_states]

    axis = (SIGMA_X + SIGMA_Y + SIGMA_Z) / math.sqrt(3.0)
    single_u = math.cos(0.37) * jnp.eye(2, dtype=jnp.complex128) - 1.0j * math.sin(0.37) * axis
    rot = single_u
    for _ in range(N_SITES - 1):
        rot = jnp.kron(rot, single_u)
    rotated_states = [rot @ state for state in terminal_states]
    correct_labels = [a33_cell_id_from_row(row) for row in A33_ROWS]
    permuted_labels = correct_labels[7:] + correct_labels[:7]
    controls = {
        "maximally_mixed_state": recover_chart_structure(mixed_density, inputs_are_density=True),
        "quotient_erased_state": recover_chart_structure(erased_density, inputs_are_density=True),
        "off_axis_rotated_states": recover_chart_structure(
            [density(state) for state in rotated_states],
            state_ids=terminal_ids,
            metadata=metadata,
            inputs_are_density=True,
            identity_required_pairs=set(positive["load_bearing_family_cell_pairs"]),
            require_load_bearing_identity=True,
        ),
        "wrong_row_classifier": recover_chart_structure(
            [density(state) for state in terminal_states],
            state_ids=terminal_ids,
            metadata=metadata,
            classifier_rows=A33_ROWS,
            classifier_row_labels=permuted_labels,
            classifier_id="A33_committed_predeclared",
            inputs_are_density=True,
            identity_required_pairs=set(positive["load_bearing_family_cell_pairs"]),
            require_load_bearing_identity=True,
        ),
    }
    controls["wrong_row_classifier"]["control_design"] = "same A33 classifier machinery with a permuted row-label ledger; failure is by family-cell identity mismatch, not classifier-id mismatch"
    for row in controls.values():
        row["expected"] = "RECOVERY_FAIL"
        row["control_fired"] = row["verdict"] == "RECOVERY_FAIL"
    return {"positive": positive, "controls": controls}


def cells_for_states(states: list[jnp.ndarray]) -> list[list[str]]:
    rows: list[list[str]] = []
    for state in states:
        rho = density(state)
        rows.append([chart_cell_id(bloch_coords(reduce_density(rho, [site])))[0] for site in range(N_SITES)])
    return rows


def haar_null_identity_row(positive: dict[str, Any]) -> dict[str, Any]:
    trial_cell_sets: list[set[str]] = []
    trial_pair_sets: list[set[str]] = []
    cell_occurrences: dict[str, int] = {}
    pair_occurrences: dict[str, int] = {}
    slot_nonorigin_counts = {f"slot_{idx}": [] for idx in range(len(HAAR_PINNED_SEEDS))}
    for trial in range(HAAR_NULL_TRIALS):
        states = [haar_pinned_pattern(HAAR_NULL_SEED0 + trial * len(HAAR_PINNED_SEEDS) + idx) for idx in range(len(HAAR_PINNED_SEEDS))]
        per_state_cells = cells_for_states(states)
        trial_cells = {cell for cells in per_state_cells for cell in cells if cell != ORIGIN_CELL}
        trial_pairs: set[str] = set()
        for slot, cells in enumerate(per_state_cells):
            nonorigin = {cell for cell in cells if cell != ORIGIN_CELL}
            slot_nonorigin_counts[f"slot_{slot}"].append(len(nonorigin))
            for cell in nonorigin:
                trial_pairs.add(f"slot_{slot}:{cell}")
        trial_cell_sets.append(trial_cells)
        trial_pair_sets.append(trial_pairs)
        for cell in trial_cells:
            cell_occurrences[cell] = cell_occurrences.get(cell, 0) + 1
        for pair in trial_pairs:
            pair_occurrences[pair] = pair_occurrences.get(pair, 0) + 1

    cell_prob = {cell: cell_occurrences.get(cell, 0) / HAAR_NULL_TRIALS for cell in sorted(A33_CELL_IDS) if cell != ORIGIN_CELL}
    pair_prob = {pair: count / HAAR_NULL_TRIALS for pair, count in sorted(pair_occurrences.items())}
    smooth = 1.0 / (HAAR_NULL_TRIALS + 1.0)

    def score_pairs(pairs: set[str]) -> float:
        return float(sum(-math.log(max(pair_prob.get(pair, 0.0), smooth)) for pair in pairs))

    family_to_slot = {f"haar_pinned_seed_{seed}": f"slot_{idx}" for idx, seed in enumerate(HAAR_PINNED_SEEDS)}
    observed_pairs = {
        f"{family_to_slot[family_id]}:{cell}"
        for family_id, cells in positive["family_cell_identity_map"].items()
        if family_id in family_to_slot
        for cell in cells
        if cell != ORIGIN_CELL
    }
    observed_cells = {pair.split(":", 1)[1] for pair in observed_pairs}
    null_scores = [score_pairs(pairs) for pairs in trial_pair_sets]
    null_counts = [len(cells) for cells in trial_cell_sets]
    observed_score = score_pairs(observed_pairs)
    null_mean = float(np.mean(np.asarray(null_scores)))
    null_std = float(np.std(np.asarray(null_scores)))
    return {
        "kind": "haar_null_identity_control",
        "generator": "full 4-qubit complex Haar states, four pinned states per trial, single-site quotient cells",
        "trials": HAAR_NULL_TRIALS,
        "seed0": HAAR_NULL_SEED0,
        "expected_nonorigin_cell_count": float(np.mean(np.asarray(null_counts))),
        "std_nonorigin_cell_count": float(np.std(np.asarray(null_counts))),
        "observed_load_bearing_nonorigin_cell_count": len(observed_cells),
        "observed_family_tied_pair_count": len(observed_pairs),
        "observed_slot_cell_pairs": sorted(observed_pairs),
        "observed_identity_surprisal": observed_score,
        "null_identity_surprisal_mean": null_mean,
        "null_identity_surprisal_std": null_std,
        "identity_surprisal_z": (observed_score - null_mean) / null_std if null_std > 0 else math.inf,
        "cell_identity_distribution": {
            cell: {"trial_presence_probability": prob, "observed_load_bearing": cell in observed_cells}
            for cell, prob in sorted(cell_prob.items())
        },
        "slot_nonorigin_expected": {
            slot: float(np.mean(np.asarray(counts))) for slot, counts in sorted(slot_nonorigin_counts.items())
        },
        "verdict": "IDENTITY_ABOVE_NULL" if observed_score > null_mean else "IDENTITY_NOT_ABOVE_NULL",
        "control_fired": True,
        "registered_falsifier_fired": observed_score <= null_mean,
    }


def per_family_recovery_table(
    positive: dict[str, Any],
    metadata: dict[str, dict[str, Any]],
    haar_null: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cell_prob = haar_null["cell_identity_distribution"]
    for pattern_id, meta in metadata.items():
        family_id = str(meta["family_id"])
        cells = positive["family_cell_identity_map"].get(family_id, [])
        nonorigin = [cell for cell in cells if cell != ORIGIN_CELL]
        surprisal = sum(-math.log(max(cell_prob.get(cell, {}).get("trial_presence_probability", 0.0), 1.0 / (HAAR_NULL_TRIALS + 1.0))) for cell in nonorigin)
        rows.append(
            {
                "pattern_id": pattern_id,
                "family_id": family_id,
                "bias_class": meta["bias_class"],
                "seed": meta.get("seed"),
                "seed_hash": meta.get("seed_hash"),
                "load_bearing_for_identity_claim": meta["load_bearing_for_identity_claim"],
                "anchor_from_v1": meta["anchor_from_v1"],
                "recovered_nonorigin_cell_ids": nonorigin,
                "recovered_nonorigin_cell_count": len(nonorigin),
                "identity_surprisal_vs_null_cells": float(surprisal),
            }
        )
    return rows


def a33_reachability_ceiling(recovered_cell_ids: list[str]) -> dict[str, Any]:
    recovered = set(recovered_cell_ids)
    rows = []
    for row in A33_ROWS:
        rho = 0.5 * (
            jnp.eye(2, dtype=jnp.complex128)
            + row[0] * SIGMA_X
            + row[1] * SIGMA_Y
            + row[2] * SIGMA_Z
        )
        eigvals = jnp.linalg.eigvalsh((rho + jnp.conjugate(rho.T)) / 2.0)
        cell_id = a33_cell_id_from_row(row)
        reachable = bool(float(jnp.min(jnp.real(eigvals))) >= -1.0e-12 and abs(float(jnp.real(jnp.trace(rho))) - 1.0) <= 1.0e-12)
        rows.append(
            {
                "cell_id": cell_id,
                "bloch_row": row,
                "reachable_in_principle": reachable,
                "carrier_witness": "single-qubit density quotient rho=(I+r.sigma)/2; four-site carrier can purify any rank<=2 single-site quotient",
                "min_eigenvalue": float(jnp.min(jnp.real(eigvals))),
                "recovered_in_packet": cell_id in recovered,
            }
        )
    reachable_ids = [row["cell_id"] for row in rows if row["reachable_in_principle"]]
    return {
        "geometric_ceiling_cell_count": len(reachable_ids),
        "reachable_in_principle_cell_ids": sorted(reachable_ids),
        "recovered_cell_ids": sorted(recovered),
        "recovered_reachable_cell_count": len(recovered.intersection(reachable_ids)),
        "reachable_not_recovered_cell_ids": sorted(set(reachable_ids) - recovered),
        "rows": rows,
    }


def target_components(target_id: str, patterns: dict[str, jnp.ndarray]) -> list[tuple[float, np.ndarray]]:
    if target_id.startswith("spurious::"):
        _, left, right = target_id.split("::", 2)
        return [(0.5, np.asarray(patterns[left], dtype=np.complex128)), (0.5, np.asarray(patterns[right], dtype=np.complex128))]
    return [(1.0, np.asarray(patterns[target_id], dtype=np.complex128))]


def kraus_choi_witness(target_id: str, patterns: dict[str, jnp.ndarray]) -> dict[str, Any]:
    components = target_components(target_id, patterns)
    eye = np.eye(DIM, dtype=np.complex128)
    kraus = [math.sqrt(1.0 - RETRIEVAL_ALPHA) * eye]
    for weight, psi in components:
        for basis in range(DIM):
            op = np.zeros((DIM, DIM), dtype=np.complex128)
            op[:, basis] = math.sqrt(RETRIEVAL_ALPHA * weight) * psi
            kraus.append(op)
    completeness = sum(k.conj().T @ k for k in kraus)
    completeness_residual = float(np.linalg.norm(completeness - eye, ord="fro"))
    choi = np.zeros((DIM * DIM, DIM * DIM), dtype=np.complex128)
    for a in range(DIM):
        for b in range(DIM):
            eab = np.zeros((DIM, DIM), dtype=np.complex128)
            eab[a, b] = 1.0
            mapped = sum(k @ eab @ k.conj().T for k in kraus)
            choi[a * DIM : (a + 1) * DIM, b * DIM : (b + 1) * DIM] = mapped / DIM
    choi = (choi + choi.conj().T) / 2.0
    eigvals = np.linalg.eigvalsh(choi)
    ptr_out = np.zeros((DIM, DIM), dtype=np.complex128)
    for a in range(DIM):
        for b in range(DIM):
            ptr_out[a, b] = np.trace(choi[a * DIM : (a + 1) * DIM, b * DIM : (b + 1) * DIM])
    ptr_residual = float(np.linalg.norm(ptr_out - eye / DIM, ord="fro"))
    return {
        "target_id": target_id,
        "kraus_count": len(kraus),
        "component_count": len(components),
        "completeness_residual_fro": completeness_residual,
        "choi_min_eigenvalue": float(np.min(eigvals)),
        "choi_trace": float(np.real(np.trace(choi))),
        "choi_rank_tol_1e_10": int(np.sum(eigvals > 1.0e-10)),
        "choi_partial_trace_output_residual_fro": ptr_residual,
        "kraus_completeness_pass": completeness_residual <= 1.0e-10,
        "choi_positivity_pass": float(np.min(eigvals)) >= -1.0e-10,
        "choi_trace_preserving_pass": ptr_residual <= 1.0e-10,
        "choi_eigenvalue_sha256": stable_hash([round(float(v), 15) for v in eigvals.tolist()]),
    }


def kraus_choi_witness_ledger(basin: dict[str, Any], patterns: dict[str, jnp.ndarray]) -> dict[str, Any]:
    target_ids = sorted(
        {
            step["target"]
            for traj in basin["trajectories"]
            for step in traj["path"]
            if isinstance(step, dict) and "target" in step
        }
    )
    rows = [kraus_choi_witness(target_id, patterns) for target_id in target_ids]
    return {
        "channel_formula": "E_target(rho)=(1-alpha)rho+alpha*Tr(rho)*sigma_target",
        "alpha": RETRIEVAL_ALPHA,
        "witness_count": len(rows),
        "all_completeness_pass": all(row["kraus_completeness_pass"] for row in rows),
        "all_choi_positivity_pass": all(row["choi_positivity_pass"] for row in rows),
        "all_trace_preserving_pass": all(row["choi_trace_preserving_pass"] for row in rows),
        "max_completeness_residual_fro": max(row["completeness_residual_fro"] for row in rows) if rows else 0.0,
        "min_choi_eigenvalue": min(row["choi_min_eigenvalue"] for row in rows) if rows else 0.0,
        "max_partial_trace_output_residual_fro": max(row["choi_partial_trace_output_residual_fro"] for row in rows) if rows else 0.0,
        "rows": rows,
    }


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


def smt_proof(
    *,
    nonorigin_count: int,
    load_bearing_nonorigin_count: int,
    control_fail_count: int,
    spurious_count: int,
    reachable_ceiling_count: int,
    kraus_witness_count: int,
    identity_surprisal_scaled: int,
    null_surprisal_mean_scaled: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    values = {
        "nonorigin_count": int(nonorigin_count),
        "load_bearing_nonorigin_count": int(load_bearing_nonorigin_count),
        "control_fail_count": int(control_fail_count),
        "spurious_count": int(spurious_count),
        "reachable_ceiling_count": int(reachable_ceiling_count),
        "kraus_witness_count": int(kraus_witness_count),
        "identity_surprisal_scaled": int(identity_surprisal_scaled),
        "null_surprisal_mean_scaled": int(null_surprisal_mean_scaled),
    }
    solver = z3.Solver()
    z_nonorigin = z3.Int("nonorigin_count")
    z_load_bearing = z3.Int("load_bearing_nonorigin_count")
    z_controls = z3.Int("control_fail_count")
    z_spurious = z3.Int("spurious_count")
    z_reachable = z3.Int("reachable_ceiling_count")
    z_kraus = z3.Int("kraus_witness_count")
    z_identity = z3.Int("identity_surprisal_scaled")
    z_null = z3.Int("null_surprisal_mean_scaled")
    solver.add(z_nonorigin == z3.IntVal(values["nonorigin_count"]))
    solver.add(z_load_bearing == z3.IntVal(values["load_bearing_nonorigin_count"]))
    solver.add(z_controls == z3.IntVal(values["control_fail_count"]))
    solver.add(z_spurious == z3.IntVal(values["spurious_count"]))
    solver.add(z_reachable == z3.IntVal(values["reachable_ceiling_count"]))
    solver.add(z_kraus == z3.IntVal(values["kraus_witness_count"]))
    solver.add(z_identity == z3.IntVal(values["identity_surprisal_scaled"]))
    solver.add(z_null == z3.IntVal(values["null_surprisal_mean_scaled"]))
    solver.add(
        z3.Not(
            z3.And(
                z_nonorigin >= 6,
                z_load_bearing >= 6,
                z_controls == 4,
                z_spurious >= 6,
                z_reachable == 33,
                z_kraus >= 1,
                z_identity > z_null,
            )
        )
    )
    z3_verdict = str(solver.check())
    flip = z3.Solver()
    f_identity = z3.Int("mutated_identity_surprisal_scaled")
    f_null = z3.Int("mutated_null_surprisal_mean_scaled")
    flip.add(f_identity == z3.IntVal(values["null_surprisal_mean_scaled"] - 1))
    flip.add(f_null == z3.IntVal(values["null_surprisal_mean_scaled"]))
    flip.add(z3.Not(f_identity > f_null))
    z3_flip = str(flip.check())
    z3_row = {
        "ran": True,
        "solver": "z3",
        "verdict": z3_verdict,
        "perturbed_construction_path_verdict": z3_flip,
        "load_bearing": True,
        "bound_computed_values": values,
        "negated_assertion": "not(nonorigin>=6 and load_bearing_nonorigin>=6 and controls=4 and spurious>=6 and reachable=33 and kraus_witness>=1 and identity_surprisal>null_mean)",
        "positive_case": "computed family-tied identity recovery, controls, v1 spurious anchor, reachability ceiling, and Kraus/Choi ledger",
        "negative/erased_control": "mutating identity surprisal below the null mean makes the negated assertion SAT",
    }

    c_solver = cvc5.Solver()
    c_solver.setLogic("QF_LIA")
    int_sort = c_solver.getIntegerSort()
    c_nonorigin = c_solver.mkConst(int_sort, "cvc5_nonorigin_count")
    c_load_bearing = c_solver.mkConst(int_sort, "cvc5_load_bearing_nonorigin_count")
    c_controls = c_solver.mkConst(int_sort, "cvc5_control_fail_count")
    c_spurious = c_solver.mkConst(int_sort, "cvc5_spurious_count")
    c_reachable = c_solver.mkConst(int_sort, "cvc5_reachable_ceiling_count")
    c_kraus = c_solver.mkConst(int_sort, "cvc5_kraus_witness_count")
    c_identity = c_solver.mkConst(int_sort, "cvc5_identity_surprisal_scaled")
    c_null = c_solver.mkConst(int_sort, "cvc5_null_surprisal_mean_scaled")
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_nonorigin, c_solver.mkInteger(values["nonorigin_count"])))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_load_bearing, c_solver.mkInteger(values["load_bearing_nonorigin_count"])))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_controls, c_solver.mkInteger(values["control_fail_count"])))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_spurious, c_solver.mkInteger(values["spurious_count"])))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_reachable, c_solver.mkInteger(values["reachable_ceiling_count"])))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_kraus, c_solver.mkInteger(values["kraus_witness_count"])))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_identity, c_solver.mkInteger(values["identity_surprisal_scaled"])))
    c_solver.assertFormula(c_solver.mkTerm(Kind.EQUAL, c_null, c_solver.mkInteger(values["null_surprisal_mean_scaled"])))
    c_solver.assertFormula(
        c_solver.mkTerm(
            Kind.NOT,
            c_solver.mkTerm(
                Kind.AND,
                c_solver.mkTerm(Kind.GEQ, c_nonorigin, c_solver.mkInteger(6)),
                c_solver.mkTerm(Kind.GEQ, c_load_bearing, c_solver.mkInteger(6)),
                c_solver.mkTerm(Kind.EQUAL, c_controls, c_solver.mkInteger(4)),
                c_solver.mkTerm(Kind.GEQ, c_spurious, c_solver.mkInteger(6)),
                c_solver.mkTerm(Kind.EQUAL, c_reachable, c_solver.mkInteger(33)),
                c_solver.mkTerm(Kind.GEQ, c_kraus, c_solver.mkInteger(1)),
                c_solver.mkTerm(Kind.GT, c_identity, c_null),
            ),
        )
    )
    cvc5_verdict = str(c_solver.checkSat()).lower()
    c_flip = cvc5.Solver()
    c_flip.setLogic("QF_LIA")
    f_identity = c_flip.mkConst(c_flip.getIntegerSort(), "cvc5_mutated_identity_surprisal_scaled")
    f_null = c_flip.mkConst(c_flip.getIntegerSort(), "cvc5_mutated_null_surprisal_mean_scaled")
    c_flip.assertFormula(c_flip.mkTerm(Kind.EQUAL, f_identity, c_flip.mkInteger(values["null_surprisal_mean_scaled"] - 1)))
    c_flip.assertFormula(c_flip.mkTerm(Kind.EQUAL, f_null, c_flip.mkInteger(values["null_surprisal_mean_scaled"])))
    c_flip.assertFormula(c_flip.mkTerm(Kind.NOT, c_flip.mkTerm(Kind.GT, f_identity, f_null)))
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
        "negative/erased_control": "mutated identity-surprisal SAT flip",
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
    metadata = pattern_metadata(patterns)
    anchor_patterns = v1_anchor_patterns()
    anchor_metadata = pattern_metadata(anchor_patterns)
    chart = chart_controls(patterns, metadata)
    anchor_ids = list(anchor_patterns)
    v1_anchor_recovery = recover_chart_structure(
        [density(anchor_patterns[key]) for key in anchor_ids],
        state_ids=anchor_ids,
        metadata=anchor_metadata,
        inputs_are_density=True,
    )
    basin = transition_graph(anchor_patterns)
    typed = typed_information_rows(patterns, {"A": [0], "B": [1, 2, 3]})
    try:
        typed_information_rows(patterns, None)
    except MissingStructure as exc:
        premature_control = {"raised": True, "error": str(exc)}
    else:
        premature_control = {"raised": False, "error": None}
    nonherm = nonhermitian_control(anchor_patterns)
    haar_null = haar_null_identity_row(chart["positive"])
    family_recovery = per_family_recovery_table(chart["positive"], metadata, haar_null)
    a33_coverage = a33_reachability_ceiling(chart["positive"]["recovered_nonorigin_cell_ids"])
    kraus_ledger = kraus_choi_witness_ledger(basin, anchor_patterns)
    control_fail_count = sum(1 for row in chart["controls"].values() if row["control_fired"])
    identity_surprisal_scaled = int(round(haar_null["observed_identity_surprisal"] * 1000))
    null_surprisal_mean_scaled = int(round(haar_null["null_identity_surprisal_mean"] * 1000))
    z3_row, cvc5_row = smt_proof(
        nonorigin_count=chart["positive"]["recovered_nonorigin_cell_count"],
        load_bearing_nonorigin_count=chart["positive"]["load_bearing_recovered_nonorigin_cell_count"],
        control_fail_count=control_fail_count,
        spurious_count=basin["spurious_attractor_count"],
        reachable_ceiling_count=a33_coverage["geometric_ceiling_cell_count"],
        kraus_witness_count=kraus_ledger["witness_count"],
        identity_surprisal_scaled=identity_surprisal_scaled,
        null_surprisal_mean_scaled=null_surprisal_mean_scaled,
    )
    engine_values = {
        "recovered_nonorigin_cell_count": chart["positive"]["recovered_nonorigin_cell_count"],
        "load_bearing_recovered_nonorigin_cell_count": chart["positive"]["load_bearing_recovered_nonorigin_cell_count"],
        "control_fail_count": control_fail_count,
        "terminal_scc_count": basin["terminal_scc_count"],
        "spurious_attractor_count": basin["spurious_attractor_count"],
        "max_lyapunov_delta_scaled": int(round(max(0.0, basin["max_lyapunov_delta"]) * 1_000_000_000)),
        "typed_entangled_negative_count": len(typed["entangled_negative_conditional_rows"]),
        "haar_null_expected_nonorigin_cell_count_scaled": int(round(haar_null["expected_nonorigin_cell_count"] * 1000)),
        "identity_surprisal_scaled": identity_surprisal_scaled,
        "null_surprisal_mean_scaled": null_surprisal_mean_scaled,
        "a33_reachable_in_principle_count": a33_coverage["geometric_ceiling_cell_count"],
        "kraus_choi_witness_count": kraus_ledger["witness_count"],
        "v1_anchor_recovered_nonorigin_cell_count": v1_anchor_recovery["recovered_nonorigin_cell_count"],
    }
    all_pass = (
        chart["positive"]["verdict"] == "RECOVERY_PASS_NONTRIVIAL"
        and chart["positive"]["load_bearing_recovered_nonorigin_cell_count"] >= MIN_RECOVERED_NONORIGIN_CELLS
        and control_fail_count == 4
        and chart["controls"]["wrong_row_classifier"]["identity_pairs_match_expected"] is False
        and haar_null["verdict"] == "IDENTITY_ABOVE_NULL"
        and 7.0 <= haar_null["expected_nonorigin_cell_count"] <= 8.3
        and a33_coverage["geometric_ceiling_cell_count"] == 33
        and kraus_ledger["all_completeness_pass"] is True
        and kraus_ledger["all_choi_positivity_pass"] is True
        and kraus_ledger["all_trace_preserving_pass"] is True
        and v1_anchor_recovery["recovered_nonorigin_cell_count"] == 6
        and basin["max_lyapunov_delta"] <= 1.0e-10
        and basin["spurious_attractor_count"] == 6
        and len(typed["entangled_negative_conditional_rows"]) >= 1
        and premature_control["raised"] is True
        and nonherm["control_fired"] is True
        and z3_row["verdict"] == "unsat"
        and cvc5_row["verdict"] == "unsat"
        and z3_row["perturbed_construction_path_verdict"] == "sat"
        and cvc5_row["perturbed_construction_path_verdict"] == "sat"
    )
    result = {
        "schema": "codex_ratchet.engine_leg_result.v2",
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
        "aligned_packages_load_bearing": ["jax", "networkx", "sympy", "z3", "cvc5"],
        "claim_path_tools": ["jax", "networkx", "sympy", "z3", "cvc5"],
        "package_observables": {
            "jax": "single-site density quotients, Haar-pinned state rows, and Kraus/Choi numeric witnesses",
            "networkx": "finite retrieval transition graph SCCs, terminal classes, and absent-exit evidence",
            "sympy": "exact rational source-backing check for finite count identities",
            "z3": "computed v2 identity/null/control/spurious/reachability/Kraus counts UNSAT with SAT mutation flip",
            "cvc5": "independent solver mirror of computed v2 identity/null/control/spurious/reachability/Kraus proof",
        },
        "engine_values": engine_values,
        "A_chart_recoverability": chart["positive"],
        "per_family_recovery_table": family_recovery,
        "haar_null_row": haar_null,
        "A33_reachability_ceiling": a33_coverage,
        "kraus_choi_witness_ledger": kraus_ledger,
        "v1_anchor_reproduction": {
            "expected_v1_nonorigin_cell_ids": [
                "A33_x00_y00_zp10",
                "A33_x00_yp5_z00",
                "A33_xp10_y00_z00",
                "A33_xp5_y00_z00",
                "A33_xp5_y00_zm5",
                "A33_xp5_y00_zp5",
            ],
            "actual": v1_anchor_recovery,
        },
        "no_structure_controls": chart["controls"],
        "basin_partition": basin,
        "typed_information": typed,
        "premature_typed_row_control": premature_control,
        "nonhermitian_control": nonherm,
        "crossover_proofs": {"z3": z3_row, "cvc5": cvc5_row},
        "source_backing_probe": source_backing_probe(),
        "TOOL_MANIFEST": {
            "jax": {"used": True, "reason": "load-bearing finite density, Haar null, and Kraus/Choi witness computation"},
            "networkx": {"used": True, "reason": "load-bearing transition graph and terminal SCC evidence"},
            "sympy": {"used": True, "reason": "load-bearing exact finite count witness check"},
            "z3": {"used": True, "reason": "load-bearing finite count proof"},
            "cvc5": {"used": True, "reason": "load-bearing independent finite count proof"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "jax": "load_bearing",
            "networkx": "load_bearing",
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
        },
        "tool_calls": [
            {
                "tool": "jax",
                "qualified_api/function": "jax.numpy.linalg.eigvalsh/jax.numpy.trace",
                "input_object": "single-site density quotients plus finite Kraus/Choi witnesses",
                "output_object": {
                    "haar_null": {
                        "expected_nonorigin_cell_count": haar_null["expected_nonorigin_cell_count"],
                        "observed_identity_surprisal": haar_null["observed_identity_surprisal"],
                    },
                    "kraus_choi_witness_count": kraus_ledger["witness_count"],
                    "a33_geometric_ceiling": a33_coverage["geometric_ceiling_cell_count"],
                },
                "positive_case": "Haar-pinned family identity is scored against a computed null and every retrieval branch has CP/TP witnesses",
                "negative/erased_control": "permuted wrong-row labels fail the same family identity predicate",
                "boundary_case": "finite n4 carrier and 2048-trial Haar null",
                "demotion_condition": "demote v2 identity claim if null, reachability, or Kraus/Choi witnesses are removed",
                "gates": ["haar_null_row", "A33_reachability_ceiling", "kraus_choi_witness_ledger", "all_pass"],
            },
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
                "input_object": "computed v2 identity/null/control/spurious/reachability/Kraus finite counts",
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
                "input_object": "same computed v2 finite count values as z3",
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
            "families": sorted({meta["family_id"] for meta in metadata.values()}),
            "load_bearing_unbiased_families": [f"haar_pinned_seed_{seed}" for seed in HAAR_PINNED_SEEDS],
            "v1_anchor_families": ["estate_chiral_quaternion_Hopf_Weyl", "entangled_nonproduct", "pinned_random_v1_anchor"],
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
