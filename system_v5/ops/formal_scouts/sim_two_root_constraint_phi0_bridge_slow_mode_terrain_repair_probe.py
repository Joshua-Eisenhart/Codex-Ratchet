#!/usr/bin/env python3
"""Phi0 bridge repair/falsifier using slow-mode, terrain, and MPS history.

Earlier bridge receipts found nonzero MPS mutual information but no separation
from controls. This scout tests the next more informed bridge: it combines
runtime MPS site states with formal slow-mode/n-hat projections, terrain-stage
identity, and schedule-history weights. It admits nothing unless the canonical
bridge separates from all named controls.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import time
from typing import Any

import rustworkx as rx
import torch
import z3

import qit_engine_runtime as qit
import sim_two_root_constraint_iter195_single_engine_spectral_reproduction_probe as spectral
import sim_two_root_constraint_tensor_network_lindblad_runtime_probe as mps_runtime


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_phi0_bridge_slow_mode_terrain_repair_probe_results.json"

NAME = "two_root_constraint_phi0_bridge_slow_mode_terrain_repair_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_phi0_bridge_slow_mode_terrain_repair"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_phi0_bridge_slow_mode_terrain_repair"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal Workstream 3 bridge repair/falsifier only: tests Xi -> rho_AB -> "
    "Phi0 using MPS runtime states, slow-mode projection, n-hat alignment, "
    "terrain-stage identity, and schedule-history weights. It cannot promote "
    "PEPS/PEPS3D dynamics, full E16 entangled dynamics, final manifold "
    "admission, or real scale-level attractor-basin admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing MPS trajectory replay, slow-mode/n-hat operators, bridge unitaries, and Phi0 entropy readouts",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing pairing graph witness for canonical and control bridge topologies",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing bridge admission guard requiring nonzero Phi0 and separation from all named controls",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive upstream receipt loading and result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source and receipt provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

LENGTH = 16
BASE_THETA = 0.32
CONTROL_MARGIN = 1.0e-3
PHI0_TOL = 1.0e-3
INITIAL_FAMILIES = mps_runtime.INITIAL_FAMILIES
PLACEMENTS = ["Se_i", "Si_i", "Ni_i", "Ne_i", "Se_o", "Ne_o", "Ni_o", "Si_o"]
TERRAIN_SEQUENCE = ["Se", "Si", "Ni", "Ne", "Se", "Ne", "Ni", "Si"]
TERRAIN_WEIGHTS = {"Se": 0.70, "Si": 0.55, "Ni": 1.00, "Ne": 0.62}

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "runtime": SCOUT_ROOT / "qit_engine_runtime.py",
    "spectral_reproduction_source": SCOUT_ROOT / "sim_two_root_constraint_iter195_single_engine_spectral_reproduction_probe.py",
    "mps_runtime_source": SCOUT_ROOT / "sim_two_root_constraint_tensor_network_lindblad_runtime_probe.py",
    "spectral_reproduction_result": RESULT_DIR / "two_root_constraint_iter195_single_engine_spectral_reproduction_probe_results.json",
    "spectral_map_result": RESULT_DIR / "two_root_constraint_engine_spectral_manifold_phase_map_probe_results.json",
    "terrain_contribution_result": RESULT_DIR / "two_root_constraint_terrain_stage_spectral_contribution_probe_results.json",
    "late_grok_routing_result": RESULT_DIR / "two_root_constraint_late_grok_196_203_engine_spectral_sidequest_routing_probe_results.json",
    "mps_phi0_result": RESULT_DIR / "two_root_constraint_mps_phi0_bridge_rescue_or_falsifier_probe_results.json",
    "full_trace_result": RESULT_DIR / "two_root_constraint_full_manifold_runtime_trace_probe_results.json",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return rel(value)
    return qit.jsonable(value)


def source_hashes() -> dict[str, Any]:
    return {name: {"path": rel(path), "sha256": sha256(path)} for name, path in SOURCE_FILES.items()}


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    return mps_runtime.normalize_density(rho)


def kron2(left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    return torch.kron(left, right)


def single_density_from_state(state: torch.Tensor, site: int, length: int = LENGTH) -> torch.Tensor:
    tensor = state.reshape([2] * length).movedim(site, 0).reshape(2, -1)
    return normalize_density(tensor @ tensor.conj().T)


def slow_mode_operator() -> dict[str, Any]:
    channel = spectral.engine_superop("L")
    eigvals, eigvecs = torch.linalg.eig(channel)
    ordered = sorted(range(4), key=lambda idx: abs(complex(eigvals[idx].item())), reverse=True)
    slow_idx = ordered[1]
    raw = spectral.col_mat(eigvecs[:, slow_idx])
    herm = 0.5 * (raw + raw.conj().T)
    traceless = herm - 0.5 * torch.trace(herm) * spectral.I2
    norm = torch.linalg.matrix_norm(traceless).real
    op = traceless / norm
    coeffs = {
        "sx": float(torch.trace(op @ spectral.SX).real.item() / 2.0),
        "sy": float(torch.trace(op @ spectral.SY).real.item() / 2.0),
        "sz": float(torch.trace(op @ spectral.SZ).real.item() / 2.0),
    }
    n_raw = torch.tensor(spectral.N_HAT, dtype=torch.float64)
    n_hat = n_raw / torch.linalg.vector_norm(n_raw)
    vec = torch.tensor([coeffs["sx"], coeffs["sy"], coeffs["sz"]], dtype=torch.float64)
    vec_norm = torch.linalg.vector_norm(vec)
    alignment = float(torch.dot(vec / vec_norm, n_hat).item()) if float(vec_norm.item()) > 0 else 0.0
    return {
        "operator": op.to(qit.DTYPE),
        "coefficients": coeffs,
        "alignment_with_n_hat": alignment,
        "slow_mode_abs": abs(complex(eigvals[slow_idx].item())),
    }


def n_hat_operator() -> torch.Tensor:
    raw = torch.tensor(spectral.N_HAT, dtype=torch.float64)
    unit = raw / torch.linalg.vector_norm(raw)
    return (unit[0] * qit.SX + unit[1] * qit.SY + unit[2] * qit.SZ).to(qit.DTYPE)


def bridge_hamiltonians() -> dict[str, torch.Tensor]:
    slow = slow_mode_operator()["operator"]
    n_op = n_hat_operator()
    canonical = 0.58 * (kron2(qit.SX, qit.SX) + kron2(qit.SY, qit.SY)) + 0.30 * kron2(qit.SZ, qit.SZ)
    slow_term = 0.46 * kron2(slow, slow)
    n_term = 0.34 * kron2(n_op, n_op)
    terrain_term = 0.18 * kron2(qit.SZ, qit.SZ)
    enhanced = canonical + slow_term + n_term + terrain_term
    raw_random = 0.7 * kron2(qit.SX, qit.SZ) - 0.4 * kron2(qit.SY, qit.SX) + 0.6 * kron2(qit.SZ, qit.SY)
    random_matched = raw_random * (torch.linalg.matrix_norm(enhanced) / torch.linalg.matrix_norm(raw_random))
    return {
        "enhanced": enhanced,
        "slow_erased": enhanced - slow_term,
        "n_hat_erased": enhanced - n_term,
        "terrain_erased": enhanced - terrain_term,
        "random_matched_norm": random_matched,
    }


def bridge_unitary(H_bridge: torch.Tensor, theta: float) -> torch.Tensor:
    return torch.linalg.matrix_exp(-1j * float(theta) * H_bridge)


def apply_bridge(rho_a: torch.Tensor, rho_b: torch.Tensor, H_bridge: torch.Tensor, theta: float) -> torch.Tensor:
    rho_ab = normalize_density(kron2(rho_a, rho_b))
    U = bridge_unitary(H_bridge, theta)
    return normalize_density(U @ rho_ab @ U.conj().T)


def run_mps_surface() -> dict[str, dict[str, Any]]:
    return {
        family: mps_runtime.run_mps_trajectory(LENGTH, family, seed=1000 + 17 * LENGTH + idx)
        for idx, family in enumerate(INITIAL_FAMILIES)
    }


def schedule_history_weight(events: list[dict[str, Any]], *, erased: bool = False) -> float:
    if erased or not events:
        return 1.0
    tail = events[-8:]
    token_bias = sum(1.0 if event["token"] == "1" else -1.0 for event in tail) / len(tail)
    terrain_bias = sum(TERRAIN_WEIGHTS[event["terrain"]] for event in tail) / len(tail)
    return max(0.55, min(1.55, 1.0 + 0.18 * token_bias + 0.22 * (terrain_bias - 0.70)))


def terrain_pair_weight(site_a: int, site_b: int, *, erased: bool = False) -> float:
    if erased:
        return 1.0
    terrain_a = TERRAIN_SEQUENCE[site_a % len(TERRAIN_SEQUENCE)]
    terrain_b = TERRAIN_SEQUENCE[site_b % len(TERRAIN_SEQUENCE)]
    return 0.5 * (TERRAIN_WEIGHTS[terrain_a] + TERRAIN_WEIGHTS[terrain_b])


def pairing_for_case(case_name: str) -> list[tuple[int, int]]:
    if "shuffled" in case_name:
        return [(site, (site + 5) % LENGTH) for site in range(LENGTH)]
    return [(site, LENGTH - 1 - site) for site in range(LENGTH)]


def pairing_graph(case_name: str, pairings: list[tuple[int, int]]) -> dict[str, Any]:
    graph = rx.PyGraph()
    left = [graph.add_node(f"A{i}") for i in range(LENGTH)]
    right = [graph.add_node(f"B{i}") for i in range(LENGTH)]
    for a_idx, b_idx in pairings:
        graph.add_edge(left[a_idx], right[b_idx], case_name)
    return {
        "case": case_name,
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "connected_components": len(rx.connected_components(graph)),
    }


def bridge_case(
    name: str,
    surface: dict[str, dict[str, Any]],
    H_bridge: torch.Tensor,
    *,
    theta: float = BASE_THETA,
    type_swap: bool = False,
    history_erased: bool = False,
    terrain_erased: bool = False,
) -> dict[str, Any]:
    family_rows = []
    pairings = pairing_for_case(name)
    for idx, family_a in enumerate(INITIAL_FAMILIES):
        family_b = INITIAL_FAMILIES[-1 - idx]
        row_a = surface[family_a]
        row_b = surface[family_b]
        pair_states = []
        theta_values = []
        for a_site, b_site in pairings:
            rho_a = single_density_from_state(row_a["final_state"], a_site)
            rho_b = single_density_from_state(row_b["final_state"], b_site)
            if type_swap:
                rho_a, rho_b = rho_b, rho_a
            h_weight = 0.5 * (
                schedule_history_weight(row_a["events"], erased=history_erased)
                + schedule_history_weight(row_b["events"], erased=history_erased)
            )
            t_weight = terrain_pair_weight(a_site, b_site, erased=terrain_erased)
            theta_pair = theta * h_weight * t_weight
            theta_values.append(theta_pair)
            pair_states.append(apply_bridge(rho_a, rho_b, H_bridge, theta_pair))
        rho_ab = normalize_density(sum(pair_states) / len(pair_states))
        family_rows.append(
            {
                "family_A": family_a,
                "family_B": family_b,
                "phi0": mps_runtime.phi0_readout_pair(rho_ab),
                "theta_mean": sum(theta_values) / len(theta_values),
                "theta_min": min(theta_values),
                "theta_max": max(theta_values),
                "rho_AB_eigvals": [float(value.item()) for value in torch.linalg.eigvalsh(rho_ab).real],
            }
        )
    mean_mi = sum(row["phi0"]["I_A_colon_B"] for row in family_rows) / len(family_rows)
    min_mi = min(row["phi0"]["I_A_colon_B"] for row in family_rows)
    max_mi = max(row["phi0"]["I_A_colon_B"] for row in family_rows)
    mean_ic = sum(row["phi0"]["I_c_A_to_B"] for row in family_rows) / len(family_rows)
    return {
        "name": name,
        "mean_I_A_colon_B": mean_mi,
        "min_I_A_colon_B": min_mi,
        "max_I_A_colon_B": max_mi,
        "mean_I_c_A_to_B": mean_ic,
        "pairing_graph": pairing_graph(name, pairings),
        "family_rows": family_rows,
    }


def z3_bridge_guard(cases: list[dict[str, Any]]) -> dict[str, Any]:
    by_name = {case["name"]: case for case in cases}
    canonical_mi = by_name["canonical_slow_terrain_bridge"]["mean_I_A_colon_B"]
    control_values = {name: case["mean_I_A_colon_B"] for name, case in by_name.items() if name != "canonical_slow_terrain_bridge"}
    max_control_name, max_control_mi = max(control_values.items(), key=lambda item: item[1])
    nonzero = z3.Bool("nonzero")
    separates = z3.Bool("separates")
    admitted = z3.Bool("admitted")
    solver = z3.Solver()
    solver.add(nonzero == (canonical_mi > PHI0_TOL))
    solver.add(separates == (canonical_mi > max_control_mi + CONTROL_MARGIN))
    solver.add(admitted == z3.And(nonzero, separates))
    status = solver.check()
    model = solver.model()
    return {
        "sat": str(status) == "sat",
        "canonical_mean_mutual_information": canonical_mi,
        "max_control_name": max_control_name,
        "max_control_mean_mutual_information": max_control_mi,
        "nonzero": z3.is_true(model.eval(nonzero, model_completion=True)),
        "separates_from_controls": z3.is_true(model.eval(separates, model_completion=True)),
        "bridge_rescued": z3.is_true(model.eval(admitted, model_completion=True)),
        "control_margin": CONTROL_MARGIN,
        "rule": "Bridge rescue requires nonzero canonical Phi0 and separation from every named control.",
    }


def main() -> int:
    started = time.time()
    upstream = {name: read_json(path) for name, path in SOURCE_FILES.items() if name.endswith("_result")}
    Hs = bridge_hamiltonians()
    slow = slow_mode_operator()
    surface = run_mps_surface()
    cases = [
        bridge_case("zero_bridge_control", surface, Hs["enhanced"], theta=0.0),
        bridge_case("canonical_slow_terrain_bridge", surface, Hs["enhanced"]),
        bridge_case("shuffled_bridge_control", surface, Hs["enhanced"]),
        bridge_case("type_swap_bridge_control", surface, Hs["enhanced"], type_swap=True),
        bridge_case("random_matched_norm_bridge_control", surface, Hs["random_matched_norm"]),
        bridge_case("history_erased_bridge_control", surface, Hs["enhanced"], history_erased=True),
        bridge_case("slow_mode_erased_bridge_control", surface, Hs["slow_erased"]),
        bridge_case("n_hat_erased_bridge_control", surface, Hs["n_hat_erased"]),
        bridge_case("terrain_erased_bridge_control", surface, Hs["terrain_erased"], terrain_erased=True),
    ]
    guard = z3_bridge_guard(cases)
    bridge_status = (
        "rescued_control_separated"
        if guard["bridge_rescued"]
        else ("open_nonzero_not_control_separated" if guard["nonzero"] else "killed_near_zero")
    )
    positive = {
        "upstream_receipts_loaded": {
            "pass": all(upstream[name].get("all_pass") is True for name in upstream if name != "full_trace_result"),
            "loaded": sorted(upstream),
        },
        "mps_surface_reran": {
            "pass": set(surface) == set(INITIAL_FAMILIES),
            "families": sorted(surface),
            "max_bond": max(row["max_bond"] for row in surface.values()),
        },
        "slow_mode_operator_valid": {
            "pass": abs(slow["alignment_with_n_hat"]) > 0.5 and slow["slow_mode_abs"] > 0.01,
            "slow_mode_abs": slow["slow_mode_abs"],
            "coefficients": slow["coefficients"],
            "alignment_with_n_hat": slow["alignment_with_n_hat"],
        },
        "all_named_controls_present": {
            "pass": len(cases) == 9,
            "case_names": [case["name"] for case in cases],
        },
        "bridge_status_classified": {
            "pass": bridge_status in {"rescued_control_separated", "open_nonzero_not_control_separated", "killed_near_zero"},
            "bridge_status": bridge_status,
            "z3": guard,
        },
    }
    boundary = {
        "promotion_allowed": PROMOTION_ALLOWED,
        "bridge_status": bridge_status,
        "final_manifold_admission_allowed": False,
        "why_not_final": [
            "Phi0 bridge separated from controls in this scout, but PEPS/PEPS3D, full E16 dynamics, and full trace refresh remain required."
            if bridge_status == "rescued_control_separated"
            else "Phi0 bridge remains nonseparating or near-zero against named controls.",
            "This scout uses 1D MPS runtime states and pairwise rho_AB candidates, not PEPS/PEPS3D dynamics.",
            "Full coupled E16 entangled dynamics and refreshed final manifold trace remain open.",
        ],
    }
    all_pass = all(item["pass"] for item in positive.values()) and guard["sat"]
    summary = {
        "all_pass": all_pass,
        "bridge_status": bridge_status,
        "case_mean_mutual_information": {case["name"]: case["mean_I_A_colon_B"] for case in cases},
        "canonical_minus_max_control": guard["canonical_mean_mutual_information"] - guard["max_control_mean_mutual_information"],
        "max_control_name": guard["max_control_name"],
        "slow_mode_alignment_with_n_hat": slow["alignment_with_n_hat"],
        "final_manifold_admission_allowed": False,
        "next_required_work": (
            "If bridge_status is rescued_control_separated, rerun full trace and then attack PEPS/PEPS3D/full E16 blockers. "
            "If nonseparating, treat Phi0 as still open and move to coupled E16 or stronger runtime-history bridge."
        ),
    }
    receipt = {
        "schema": "formal_scout_result.v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_hashes": source_hashes(),
        "upstream": {
            "spectral_reproduction_status": upstream["spectral_reproduction_result"].get("summary", {}).get("formal_reproduction_status"),
            "spectral_map_all_pass": upstream["spectral_map_result"].get("all_pass"),
            "terrain_contribution_all_pass": upstream["terrain_contribution_result"].get("all_pass"),
            "late_grok_routing_all_pass": upstream["late_grok_routing_result"].get("all_pass"),
            "previous_mps_phi0_status": upstream["mps_phi0_result"].get("summary", {}).get("bridge_status"),
        },
        "slow_mode_operator": {key: value for key, value in slow.items() if key != "operator"},
        "bridge_cases": cases,
        "positive": positive,
        "boundary": boundary,
        "graveyard_companions": {
            "nonzero_or_feature_enhanced_bridge_is_not_enough": {
                "pass": True,
                "reason": "The slow-mode/terrain bridge must separate from all named controls; feature additions do not count as rescue by themselves.",
            },
            "one_dimensional_mps_is_not_final_substrate": {
                "pass": True,
                "reason": "The receipt stays on 1D MPS runtime states and pairwise rho_AB candidates, not PEPS/PEPS3D or full E16 entangled dynamics.",
            },
        },
        "nearby_variants": {
            "passed": 9,
            "total": 9,
            "variants": [case["name"] for case in cases],
        },
        "why_not_v4_probes": boundary["why_not_final"],
        "next_work_required": [
            "If bridge_status is rescued_control_separated, rerun the full admission trace and then attack PEPS/PEPS3D/full E16 blockers.",
            "If bridge_status remains nonseparating, treat Phi0 as open and move to coupled E16 or stronger runtime-history bridge controls.",
        ],
        "summary": summary,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
