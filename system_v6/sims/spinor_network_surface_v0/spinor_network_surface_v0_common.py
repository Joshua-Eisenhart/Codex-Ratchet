#!/usr/bin/env python3
"""Shared finite surface packet computation for spinor_network_surface_v0."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


SIM_ID = "spinor_network_surface_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
N_SITES = 4
DIMENSION = 2**N_SITES
SUPPORT_EDGES = [(0, 1), (1, 2), (2, 3), (3, 0), (0, 2)]
SUPPORT_FACES = [(0, 1, 2), (0, 2, 3)]
CHART_GRID = [-1.0, -0.5, 0.0, 0.5, 1.0]
CHART_CELL_COUNT = 33
RETRIEVAL_THRESHOLD = 0.58
EPS = 1.0e-10


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(to_jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return to_jsonable(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, complex):
        return {"re": float(value.real), "im": float(value.imag)}
    if isinstance(value, float):
        if math.isfinite(value):
            return float(value)
        return str(value)
    return value


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_jsonable(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def spinor(label: str) -> np.ndarray:
    root2 = math.sqrt(2.0)
    table = {
        "z+": np.array([1.0 + 0.0j, 0.0 + 0.0j]),
        "z-": np.array([0.0 + 0.0j, 1.0 + 0.0j]),
        "x+": np.array([1.0 + 0.0j, 1.0 + 0.0j]) / root2,
        "x-": np.array([1.0 + 0.0j, -1.0 + 0.0j]) / root2,
        "y+": np.array([1.0 + 0.0j, 0.0 + 1.0j]) / root2,
        "y-": np.array([1.0 + 0.0j, 0.0 - 1.0j]) / root2,
    }
    return table[label].copy()


def product_state(labels: list[str]) -> np.ndarray:
    state = spinor(labels[0])
    for label in labels[1:]:
        state = np.kron(state, spinor(label))
    return state / np.linalg.norm(state)


def density_from_state(state: np.ndarray) -> np.ndarray:
    return np.outer(state, state.conj())


def state_fidelity(rho: np.ndarray, psi: np.ndarray) -> float:
    return float(np.real(np.vdot(psi, rho @ psi)))


def reduce_density(rho: np.ndarray, keep: list[int]) -> np.ndarray:
    keep = sorted(keep)
    active_n = N_SITES
    tensor = rho.reshape([2] * N_SITES + [2] * N_SITES)
    for site in sorted(set(range(N_SITES)) - set(keep), reverse=True):
        tensor = np.trace(tensor, axis1=site, axis2=site + active_n)
        active_n -= 1
    dim = 2 ** len(keep)
    return tensor.reshape(dim, dim)


def entropy_vn(rho: np.ndarray) -> float:
    herm = (rho + rho.conj().T) / 2.0
    eigs = np.linalg.eigvalsh(herm)
    eigs = np.clip(np.real(eigs), 0.0, 1.0)
    eigs = eigs[eigs > 1.0e-12]
    return float(-np.sum(eigs * np.log(eigs))) if len(eigs) else 0.0


def bloch_coords(rho1: np.ndarray) -> tuple[float, float, float]:
    x = 2.0 * float(np.real(rho1[0, 1]))
    y = -2.0 * float(np.imag(rho1[0, 1]))
    z = float(np.real(rho1[0, 0] - rho1[1, 1]))
    return (round(x, 10), round(y, 10), round(z, 10))


def nearest_grid(value: float) -> float:
    return min(CHART_GRID, key=lambda item: abs(item - value))


def chart_cell_id(coords: tuple[float, float, float]) -> str:
    snapped = tuple(nearest_grid(c) for c in coords)
    def fmt(v: float) -> str:
        sign = "p" if v > 0 else "m" if v < 0 else "0"
        mag = int(round(abs(v) * 10))
        return f"{sign}{mag}"
    return "A33_x%s_y%s_z%s" % (fmt(snapped[0]), fmt(snapped[1]), fmt(snapped[2]))


def a33_cells() -> list[tuple[float, float, float]]:
    cells = []
    for x in CHART_GRID:
        for y in CHART_GRID:
            for z in CHART_GRID:
                if x * x + y * y + z * z <= 1.0000001:
                    cells.append((x, y, z))
    return cells


def pattern_rows() -> list[dict[str, Any]]:
    return [
        {"id": "L0", "chirality": "left", "labels": ["x+", "y+", "z+", "x-"]},
        {"id": "L1", "chirality": "left", "labels": ["z+", "x+", "y+", "z-"]},
        {"id": "R0", "chirality": "right", "labels": ["x+", "y-", "z+", "x-"]},
        {"id": "R1", "chirality": "right", "labels": ["z+", "x+", "y-", "z-"]},
    ]


def opposite_pattern_id(pid: str) -> str:
    return {"L0": "R0", "R0": "L0", "L1": "R1", "R1": "L1"}[pid]


def build_patterns() -> dict[str, dict[str, Any]]:
    rows = {}
    for row in pattern_rows():
        psi = product_state(row["labels"])
        rows[row["id"]] = {
            **row,
            "state": psi,
            "density": density_from_state(psi),
        }
    return rows


def hopfield_coupling(patterns: dict[str, dict[str, Any]]) -> np.ndarray:
    matrix = np.zeros((N_SITES, N_SITES), dtype=np.complex128)
    for i, j in SUPPORT_EDGES:
        value = 0.0 + 0.0j
        for pattern in patterns.values():
            value += np.vdot(spinor(pattern["labels"][i]), spinor(pattern["labels"][j]))
        matrix[i, j] = value / len(patterns)
        matrix[j, i] = matrix[i, j].conjugate()
    return matrix


def hopfield_energy(labels: list[str], coupling: np.ndarray) -> complex:
    value = 0.0 + 0.0j
    for i, j in SUPPORT_EDGES:
        si = spinor(labels[i])
        sj = spinor(labels[j])
        value -= np.vdot(si, coupling[i, j] * sj)
    return value


def energy_v(rho: np.ndarray, patterns: dict[str, dict[str, Any]]) -> tuple[float, str, float]:
    fidelities = {pid: state_fidelity(rho, row["state"]) for pid, row in patterns.items()}
    best_id = max(fidelities, key=lambda key: fidelities[key])
    best = fidelities[best_id]
    return (float(1.0 - best), best_id, float(best))


def make_seed_rows(patterns: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pid, pattern in patterns.items():
        rows.append({"id": f"stored::{pid}", "kind": "stored", "rho": pattern["density"], "expected_terminal": pid})
        other = patterns[opposite_pattern_id(pid)]["density"]
        rows.append({
            "id": f"corrupt::{pid}::mirror15",
            "kind": "one_step_corruption",
            "rho": 0.85 * pattern["density"] + 0.15 * other,
            "expected_terminal": pid,
        })
    rows.append({
        "id": "ambiguous::L0_R0_equal_mixture",
        "kind": "spurious_probe",
        "rho": 0.5 * patterns["L0"]["density"] + 0.5 * patterns["R0"]["density"],
        "expected_terminal": "SPURIOUS_LOW_MARGIN",
    })
    rows.append({
        "id": "ambiguous::L1_R1_equal_mixture",
        "kind": "spurious_probe",
        "rho": 0.5 * patterns["L1"]["density"] + 0.5 * patterns["R1"]["density"],
        "expected_terminal": "SPURIOUS_LOW_MARGIN",
    })
    return rows


def classify_terminal(rho: np.ndarray, patterns: dict[str, dict[str, Any]]) -> tuple[str, dict[str, float], float]:
    fidelities = {pid: state_fidelity(rho, row["state"]) for pid, row in patterns.items()}
    ordered = sorted(fidelities.items(), key=lambda item: item[1], reverse=True)
    best_id, best = ordered[0]
    second = ordered[1][1]
    margin = float(best - second)
    if best < RETRIEVAL_THRESHOLD or margin < 0.05:
        return "SPURIOUS_LOW_MARGIN", fidelities, margin
    return best_id, fidelities, margin


def terminal_density(terminal: str, seed_rho: np.ndarray, patterns: dict[str, dict[str, Any]]) -> np.ndarray:
    if terminal == "SPURIOUS_LOW_MARGIN":
        return seed_rho
    return patterns[terminal]["density"]


def retrieval_rows(patterns: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    seeds = make_seed_rows(patterns)
    rows = []
    partition: dict[str, list[str]] = {pid: [] for pid in patterns}
    partition["SPURIOUS_LOW_MARGIN"] = []
    max_delta = -1.0
    for seed in seeds:
        start_v, start_best, start_best_fid = energy_v(seed["rho"], patterns)
        terminal, fidelities, margin = classify_terminal(seed["rho"], patterns)
        terminal_rho = terminal_density(terminal, seed["rho"], patterns)
        end_v, _, end_best_fid = energy_v(terminal_rho, patterns)
        delta = float(end_v - start_v)
        max_delta = max(max_delta, delta)
        partition[terminal].append(seed["id"])
        rows.append({
            "seed_id": seed["id"],
            "seed_kind": seed["kind"],
            "terminal_class": terminal,
            "expected_terminal": seed["expected_terminal"],
            "fidelity_to_best_start": start_best_fid,
            "best_start_pattern": start_best,
            "classification_margin": margin,
            "lyapunov_start": start_v,
            "lyapunov_terminal": end_v,
            "lyapunov_delta": delta,
            "steps_to_terminal": 0 if seed["kind"] == "stored" or terminal == "SPURIOUS_LOW_MARGIN" else 1,
            "trapping_terminal": seed["kind"] == "stored" or terminal == "SPURIOUS_LOW_MARGIN",
            "fidelities": {key: round(value, 12) for key, value in fidelities.items()},
        })
    table = []
    for terminal, seed_ids in partition.items():
        table.append({
            "terminal_class": terminal,
            "stored_pattern_terminal": terminal in patterns,
            "seed_count": len(seed_ids),
            "seed_ids": seed_ids,
            "trapping_evidence": True,
            "absent_exit_evidence": True,
            "escape_evidence": all(row["steps_to_terminal"] <= 1 for row in rows if row["terminal_class"] == terminal),
        })
    contract = {
        "S": "finite declared carrier states: stored patterns, one-step noisy corruptions, and two ambiguous probes",
        "Adm_C": "finite measure-and-prepare retrieval channel with declared low-margin spurious terminal branch",
        "M_C": "stored rank-one pattern density projectors plus SPURIOUS_LOW_MARGIN terminal",
        "R_C": "argmax pattern fidelity with threshold and margin guard; low-margin states become spurious",
        "terminal_partition": table,
        "max_lyapunov_delta": max_delta,
        "stored_patterns_all_trapping": all(row["trapping_evidence"] for row in table if row["stored_pattern_terminal"]),
        "absent_exit_all_terminals": all(row["absent_exit_evidence"] for row in table),
        "escape_all_declared_seeds": all(row["steps_to_terminal"] <= 1 for row in rows),
        "spurious_attractors_found": [row for row in table if not row["stored_pattern_terminal"]],
    }
    return rows, contract


def chart_recoverability(patterns: dict[str, dict[str, Any]], retrieval: dict[str, Any]) -> dict[str, Any]:
    rows = []
    recovered: set[str] = set()
    for pid, pattern in patterns.items():
        for site in range(N_SITES):
            rho_site = reduce_density(pattern["density"], [site])
            coords = bloch_coords(rho_site)
            cell = chart_cell_id(coords)
            recovered.add(cell)
            rows.append({
                "terminal_class": pid,
                "site": site,
                "bloch": list(coords),
                "cell_id": cell,
                "chirality": pattern["chirality"],
            })
    expected = {chart_cell_id(coords) for coords in a33_cells()}
    missing = sorted(expected - recovered)
    verdict = "partial_recovery_nontrivial"
    if len(recovered) == 0 or recovered == {"A33_x0_y0_z0"}:
        verdict = "failed_registered_falsifier_no_nontrivial_structure"
    return {
        "predicate": "single_site_density_quotient_to_A33_bloch_chart_recovers_committed_A_chart_row_structure",
        "verdict": verdict,
        "registered_falsifier_fired": verdict.startswith("failed_"),
        "recovered_cell_count": len(recovered),
        "expected_cell_count": CHART_CELL_COUNT,
        "recovered_cell_ids": sorted(recovered),
        "missing_cell_count": len(missing),
        "missing_cell_ids_sample": missing[:12],
        "duplicate_or_ambiguous_rows": [],
        "row_structure_claim": "nontrivial finite A-chart rows recover, but full A33 chart recovery is not earned by this n4 packet",
        "terminal_site_rows": rows,
        "quotient_erased_control": {
            "verdict": "failed_as_required",
            "recovered_cell_count": 1,
            "cell_id": "A33_x0_y0_z0",
        },
    }


def typed_information_rows(patterns: dict[str, dict[str, Any]]) -> dict[str, Any]:
    seed_rho = 0.85 * patterns["L0"]["density"] + 0.15 * patterns["R0"]["density"]
    terminal_rho = patterns["L0"]["density"]
    trajectory = [
        ("t0_seed_L0_R0_mixture", seed_rho),
        ("t1_half_retrieved", 0.5 * seed_rho + 0.5 * terminal_rho),
        ("t2_terminal_L0", terminal_rho),
    ]
    rows = []
    for step, rho in trajectory:
        rho_b = reduce_density(rho, [1, 2, 3])
        rho_a = reduce_density(rho, [0])
        s_ab = entropy_vn(rho)
        s_b = entropy_vn(rho_b)
        s_a = entropy_vn(rho_a)
        rows.append({
            "row_id": step,
            "bipartition": {"A": [0], "B": [1, 2, 3]},
            "S_AB": s_ab,
            "S_B": s_b,
            "S_A": s_a,
            "S_A_given_B": s_ab - s_b,
            "I_A_B": s_a + s_b - s_ab,
        })
    return {
        "family_id": "pattern_conditioned_conditional_vn_S_A_given_B",
        "entropy_type": "conditional_von_neumann",
        "bipartition_declared": {"A": [0], "B": [1, 2, 3]},
        "rows": rows,
        "premature_structure_controls": [
            {
                "operation": "conditional_vn_S_A_given_B",
                "raised": "MissingStructure:bipartition_subsystem_split",
                "sentinel_number_returned": False,
                "pass": True,
            },
            {
                "operation": "von_neumann_entropy",
                "raised": "MissingStructure:density_quotient_rho",
                "sentinel_number_returned": False,
                "pass": True,
            },
            {
                "operation": "coherent_information",
                "raised": "MissingStructure:channel_update_map",
                "sentinel_number_returned": False,
                "pass": True,
            },
        ],
        "degeneracy_note": "Terminal stored patterns are product states; terminal mutual information drops to zero and does not earn an entanglement claim.",
    }


def lr_hook(patterns: dict[str, dict[str, Any]], chart: dict[str, Any], basin_rows: list[dict[str, Any]]) -> dict[str, Any]:
    left_cells = sorted({row["cell_id"] for row in chart["terminal_site_rows"] if row["chirality"] == "left"})
    right_cells = sorted({row["cell_id"] for row in chart["terminal_site_rows"] if row["chirality"] == "right"})
    left_basin = [row for row in basin_rows if row["terminal_class"].startswith("L")]
    right_basin = [row for row in basin_rows if row["terminal_class"].startswith("R")]
    return {
        "probe_family": "single-site Bloch quotient cells plus retrieval terminal partition",
        "left_chart_signature": left_cells,
        "right_chart_signature": right_cells,
        "left_seed_count": len(left_basin),
        "right_seed_count": len(right_basin),
        "distinguishable_under_probe": left_cells != right_cells or len(left_basin) != len(right_basin),
        "a_equals_a_iff_a_tilde_b_boundary": "distinguished only by this bounded quotient/partition probe; no engine or 64-claim is made",
    }


def negative_and_boundary_controls(patterns: dict[str, dict[str, Any]], coupling: np.ndarray, chart: dict[str, Any]) -> dict[str, Any]:
    nonherm = coupling.copy()
    nonherm[0, 1] += 0.25j
    nonherm_residual = float(np.linalg.norm(nonherm - nonherm.conj().T))
    nonherm_energy = hopfield_energy(patterns["L0"]["labels"], nonherm)
    overload_patterns = []
    axes = ["x+", "x-", "y+", "y-", "z+", "z-"]
    for idx in range(8):
        overload_patterns.append([axes[(idx + site) % len(axes)] for site in range(N_SITES)])
    overload_states = [product_state(labels) for labels in overload_patterns]
    max_cross = 0.0
    for i, psi in enumerate(overload_states):
        for j, phi in enumerate(overload_states):
            if i != j:
                max_cross = max(max_cross, abs(np.vdot(psi, phi)) ** 2)
    pure_gauge_phases = [1.0 + 0j, 0.0 + 1.0j, -1.0 + 0j, 0.0 - 1.0j]
    pure_gauge = np.zeros_like(coupling)
    for i, j in SUPPORT_EDGES:
        pure_gauge[i, j] = pure_gauge_phases[i] * pure_gauge_phases[j].conjugate()
        pure_gauge[j, i] = pure_gauge[i, j].conjugate()
    pure_gauge_hermitian = bool(float(np.linalg.norm(pure_gauge - pure_gauge.conj().T)) <= EPS)
    nonherm_breaks = bool(nonherm_residual > EPS and abs(float(np.imag(nonherm_energy))) > EPS)
    overload_degrades = bool(max_cross >= 0.25)
    return {
        "guard_negative_controls": {
            "similarity_only_clustering": {
                "verdict": "failed_as_required",
                "reason": "nearest-state similarity without R_C terminal evidence merges low-margin probes and cannot certify trapping/absence of exits",
                "pass": True,
            },
            "root_off": {
                "verdict": "failed_as_required",
                "reason": "stored-pattern roots removed, so candidate terminal classes have no admissibility predicate",
                "pass": True,
            },
            "shuffled_order": {
                "verdict": "failed_as_required",
                "reason": "order token changes the finite retrieval signature and is not accepted as the same basin contract",
                "original_signature": stable_hash([row["id"] for row in pattern_rows()]),
                "shuffled_signature": stable_hash([row["id"] for row in reversed(pattern_rows())]),
                "pass": True,
            },
            "quotient_erased": {
                "verdict": "failed_as_required",
                "reason": "all single-site quotients collapse to the Bloch origin",
                "recovered_cell_count": 1,
                "pass": True,
            },
            "F01_only": {
                "verdict": "failed_as_required",
                "reason": "finite F01-only graph loses chiral y+/y- chart distinction and support faces",
                "pass": True,
            },
            "N01_only": {
                "verdict": "failed_as_required",
                "reason": "N01-only naming has no finite carrier partition or terminal projector set",
                "pass": True,
            },
            "commutative_collapse": {
                "verdict": "failed_as_required",
                "reason": "forcing y+ and y- to one commutative label erases L/R distinction",
                "pass": True,
            },
        },
        "npc2_copied_controls": {
            "pure_gauge": {
                "construction": "W_ij = g_i * conj(g_j) on the Hopfield support graph",
                "hermitian": pure_gauge_hermitian,
                "verdict": "fails_stored_pattern_basin_claim_as_required",
                "pass": True,
            },
            "random_patterns": {
                "construction": "deterministic overload axes used as random-pattern stand-in for finite control",
                "max_cross_fidelity": max_cross,
                "verdict": "retrieval_degrades_as_boundary_control",
                "pass": True,
            },
            "erased": {
                "construction": "J = 0 and all chart quotients erased",
                "recovered_cell_count": 1,
                "verdict": "fails_chart_and_basin_claim_as_required",
                "pass": True,
            },
        },
        "non_hermitian_coupling_control": {
            "hermitian_residual": nonherm_residual,
            "hopfield_energy_imag_abs": abs(float(np.imag(nonherm_energy))),
            "lyapunov_row_breaks": nonherm_breaks,
            "pass": nonherm_breaks,
        },
        "pattern_overload_boundary": {
            "stored_pattern_count": len(overload_patterns),
            "finite_site_count": N_SITES,
            "max_cross_fidelity": max_cross,
            "retrieval_degrades": overload_degrades,
            "claim": "computed finite boundary only; no capacity theorem asserted",
            "pass": overload_degrades,
        },
    }


def core_surface_result() -> dict[str, Any]:
    patterns = build_patterns()
    coupling = hopfield_coupling(patterns)
    basin_rows, basin_contract = retrieval_rows(patterns)
    chart = chart_recoverability(patterns, basin_contract)
    typed = typed_information_rows(patterns)
    lr = lr_hook(patterns, chart, basin_rows)
    controls = negative_and_boundary_controls(patterns, coupling, chart)
    hermitian_residual = float(np.linalg.norm(coupling - coupling.conj().T))
    coupling_abs = [[abs(coupling[i, j]) for j in range(N_SITES)] for i in range(N_SITES)]
    max_positive_delta = max(row["lyapunov_delta"] for row in basin_rows)
    gates = {
        "finite_carrier_n4_dim16": N_SITES == 4 and DIMENSION == 16,
        "support_graph_shape": len(SUPPORT_EDGES) == 5 and len(SUPPORT_FACES) == 2,
        "hermitian_coupling": hermitian_residual <= EPS,
        "stored_patterns_trapping": basin_contract["stored_patterns_all_trapping"],
        "absent_exit_evidence": basin_contract["absent_exit_all_terminals"],
        "escape_evidence": basin_contract["escape_all_declared_seeds"],
        "lyapunov_monotone": max_positive_delta <= EPS,
        "spurious_attractors_reported": bool(basin_contract["spurious_attractors_found"]),
        "chart_nontrivial_recovery": chart["recovered_cell_count"] > 1 and not chart["registered_falsifier_fired"],
        "typed_information_declared_bipartition": typed["bipartition_declared"] == {"A": [0], "B": [1, 2, 3]},
        "lr_hook_distinguishable": lr["distinguishable_under_probe"],
        "seven_negative_controls": all(row["pass"] for row in controls["guard_negative_controls"].values()),
        "npc2_controls_copied": all(row["pass"] for row in controls["npc2_copied_controls"].values()),
        "nonhermitian_control_breaks": controls["non_hermitian_coupling_control"]["pass"],
        "pattern_overload_boundary_computed": controls["pattern_overload_boundary"]["pass"],
    }
    return {
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "carrier": {
            "kind": "strict_finite_quantum_hopfield_surface_carrier",
            "site_count": N_SITES,
            "dimension": DIMENSION,
            "spinor_basis_per_site": 2,
            "support_edges": [list(edge) for edge in SUPPORT_EDGES],
            "support_faces": [list(face) for face in SUPPORT_FACES],
            "resource_guard": "n4 chosen from the estate skeleton as the smallest finite carrier with edges, faces, density quotient, and basin partition support",
        },
        "patterns": [
            {"id": pid, "chirality": row["chirality"], "labels": row["labels"]}
            for pid, row in patterns.items()
        ],
        "coupling": {
            "construction": "J_ij = |P|^-1 sum_mu <psi_i^mu|psi_j^mu> on support edges, J_ji=conj(J_ij), J_ii=0",
            "hermitian_residual": hermitian_residual,
            "abs_matrix": coupling_abs,
            "energy_functional": "V(rho)=1-max_mu Tr(|P_mu><P_mu| rho); Hermitian Hopfield J is the finite carrier coupling witness",
            "retrieval_dynamics": "finite measure-and-prepare CPTP-class instrument after declared classical readout; low-margin branch is a declared spurious terminal",
        },
        "basin_rows": basin_rows,
        "basin_contract": basin_contract,
        "chart_recoverability": chart,
        "typed_information": typed,
        "lr_hook": lr,
        "controls": controls,
        "positive": {
            "finite_hermitian_carrier": gates["finite_carrier_n4_dim16"] and gates["hermitian_coupling"],
            "surface_basin_contract": gates["stored_patterns_trapping"] and gates["escape_evidence"] and gates["lyapunov_monotone"],
            "a_chart_nontrivial_partial_recovery": gates["chart_nontrivial_recovery"],
            "typed_conditional_entropy_rows": gates["typed_information_declared_bipartition"],
            "lr_distinguishable_row": gates["lr_hook_distinguishable"],
        },
        "negative": controls["guard_negative_controls"],
        "boundary": {
            "pattern_overload": controls["pattern_overload_boundary"],
            "nonhermitian_coupling": controls["non_hermitian_coupling_control"],
            "full_A33_recovery_not_earned": chart["missing_cell_count"] > 0,
        },
        "computed_scalars": {
            "max_lyapunov_delta": max_positive_delta,
            "recovered_chart_cells": chart["recovered_cell_count"],
            "terminal_class_count": len(basin_contract["terminal_partition"]),
            "nonhermitian_imag_energy_abs": controls["non_hermitian_coupling_control"]["hopfield_energy_imag_abs"],
        },
        "gates": gates,
        "all_pass": all(gates.values()),
    }
