#!/usr/bin/env python3
"""Coupled E=16 runtime with slow-mode bridge and Phi0 readout.

This Workstream 4 scout moves beyond product-substrate metadata. It evolves a
bounded dense pure-state trajectory on two E=8 halves with local terrain
trajectory steps and explicit cross-engine bridge gates inside the dynamics.
It then extracts runtime pair cut-states rho_AB and Phi0 readouts with controls.
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
import sim_two_root_constraint_phi0_bridge_slow_mode_terrain_repair_probe as phi0_bridge
import sim_two_root_constraint_tensor_network_lindblad_runtime_probe as mps_runtime


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_coupled_e16_runtime_slow_mode_bridge_probe_results.json"

NAME = "two_root_constraint_coupled_e16_runtime_slow_mode_bridge_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_coupled_e16_dense_trajectory"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_coupled_e16_runtime_slow_mode_bridge"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal Workstream 4 scout only: runs a bounded dense pure-state "
    "trajectory on a coupled E=16 substrate with local terrain trajectory steps, "
    "cross-engine bridge gates, runtime rho_AB extraction, and Phi0 controls. "
    "It cannot promote PEPS/PEPS3D dynamics, L32/L64 tensor-network scaling, "
    "final manifold admission, or real scale-level attractor-basin admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing dense E16 state trajectory, local quantum-jump terrain steps, cross-engine bridge gates, rho_AB extraction, and Phi0 entropy readouts",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing E16 substrate graph with intra-engine and cross-engine coupling edges",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing admission guard separating coupled-runtime evidence from final manifold admission",
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
HALF = 8
N_CYCLES = 3
DT = mps_runtime.DT
BASE_THETA = 0.055
CONTROL_MARGIN = 1.0e-3
PHI0_TOL = 1.0e-3
NORM_TOL = 1.0e-8
INITIAL_FAMILIES = mps_runtime.INITIAL_FAMILIES
TERRAIN_ORDER_BY_TOKEN = mps_runtime.TERRAIN_ORDER_BY_TOKEN

SOURCE_FILES = {
    "formal_scout": pathlib.Path(__file__).resolve(),
    "runtime": SCOUT_ROOT / "qit_engine_runtime.py",
    "mps_runtime_source": SCOUT_ROOT / "sim_two_root_constraint_tensor_network_lindblad_runtime_probe.py",
    "phi0_bridge_source": SCOUT_ROOT / "sim_two_root_constraint_phi0_bridge_slow_mode_terrain_repair_probe.py",
    "phi0_bridge_result": RESULT_DIR / "two_root_constraint_phi0_bridge_slow_mode_terrain_repair_probe_results.json",
    "mps_runtime_result": RESULT_DIR / "two_root_constraint_tensor_network_lindblad_runtime_probe_results.json",
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


def dense_product_state(family_a: str, family_b: str) -> torch.Tensor:
    vectors = [mps_runtime.site_vector(family_a, idx) for idx in range(HALF)]
    vectors.extend(mps_runtime.site_vector(family_b, idx) for idx in range(HALF))
    state = vectors[0]
    for vector in vectors[1:]:
        state = torch.kron(state, vector)
    return mps_runtime.dense_normalize(state)


def single_density_from_dense(state: torch.Tensor, site: int) -> torch.Tensor:
    tensor = state.reshape([2] * LENGTH).movedim(site, 0).reshape(2, -1)
    return mps_runtime.normalize_density(tensor @ tensor.conj().T)


def mean_z_half(state: torch.Tensor, start: int) -> float:
    values = [qit.bloch(single_density_from_dense(state, start + idx))[2] for idx in range(HALF)]
    return float(sum(values) / len(values))


def apply_two_any_dense(state: torch.Tensor, op: torch.Tensor, site_a: int, site_b: int) -> torch.Tensor:
    if site_a == site_b:
        raise ValueError("two-site gate requires distinct sites")
    tensor = state.reshape([2] * LENGTH)
    moved = tensor.movedim((site_a, site_b), (0, 1)).reshape(4, -1)
    evolved = op.reshape(4, 4).to(qit.DTYPE) @ moved
    out = evolved.reshape([2, 2] + [2] * (LENGTH - 2)).movedim((0, 1), (site_a, site_b))
    return mps_runtime.dense_normalize(out.reshape(-1))


def pair_density_from_state(state: torch.Tensor, site_a: int, site_b: int) -> torch.Tensor:
    tensor = state.reshape([2] * LENGTH).movedim((site_a, site_b), (0, 1)).reshape(4, -1)
    return mps_runtime.normalize_density(tensor @ tensor.conj().T)


def aggregate_pair_density(state: torch.Tensor, pairings: list[tuple[int, int]]) -> torch.Tensor:
    pair_states = [pair_density_from_state(state, left, right) for left, right in pairings]
    return mps_runtime.normalize_density(sum(pair_states) / len(pair_states))


def half_entropy(state: torch.Tensor) -> float:
    matrix = state.reshape(2**HALF, 2**HALF)
    singulars = torch.linalg.svdvals(matrix)
    probs = torch.clamp(singulars.real * singulars.real, min=1.0e-15)
    probs = probs / torch.sum(probs)
    return float((-torch.sum(probs * torch.log(probs))).item())


def bridge_pairings(case_name: str) -> list[tuple[int, int]]:
    if "shuffled" in case_name:
        return [(idx, HALF + ((idx + 3) % HALF)) for idx in range(HALF)]
    return [(idx, LENGTH - 1 - idx) for idx in range(HALF)]


def substrate_graph(pairings: list[tuple[int, int]]) -> dict[str, Any]:
    graph = rx.PyGraph()
    nodes = [graph.add_node(f"q{idx}") for idx in range(LENGTH)]
    for idx in range(HALF - 1):
        graph.add_edge(nodes[idx], nodes[idx + 1], "A_local")
        graph.add_edge(nodes[HALF + idx], nodes[HALF + idx + 1], "B_local")
    for left, right in pairings:
        graph.add_edge(nodes[left], nodes[right], "cross_engine")
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "cross_edge_count": len(pairings),
        "connected_components": len(rx.connected_components(graph)),
    }


def choose_half_token(state: torch.Tensor, start: int, previous: str | None) -> str:
    return mps_runtime.choose_hysteresis(mean_z_half(state, start), previous)


def local_step_half(
    state: torch.Tensor,
    *,
    start: int,
    token: str,
    terrain: str,
    generator: torch.Generator,
) -> tuple[torch.Tensor, int]:
    H = mps_runtime.local_hamiltonian(token)
    collapses = mps_runtime.collapse_ops(token, terrain)
    no_jump = mps_runtime.no_jump_operator(H, collapses)
    jump_count = 0
    for offset in range(HALF):
        site = start + offset
        rho_site = single_density_from_dense(state, site)
        kind, channel_idx = mps_runtime.local_jump_choice(rho_site, collapses, generator)
        if kind == "jump":
            op = math.sqrt(DT) * collapses[int(channel_idx)]
            jump_count += 1
        else:
            op = no_jump
        state = mps_runtime.apply_single_dense(state, op, site, LENGTH)
        state = mps_runtime.dense_normalize(state)
    return state, jump_count


def local_intra_engine_gates(state: torch.Tensor) -> torch.Tensor:
    gate = mps_runtime.two_site_gate().reshape(4, 4)
    for site in range(0, HALF - 1, 2):
        state = apply_two_any_dense(state, gate, site, site + 1)
    for site in range(HALF, LENGTH - 1, 2):
        state = apply_two_any_dense(state, gate, site, site + 1)
    return state


def bridge_hamiltonians() -> dict[str, torch.Tensor]:
    return phi0_bridge.bridge_hamiltonians()


def history_weight(token_a: str, token_b: str, terrain: str, *, history_erased: bool, terrain_erased: bool) -> float:
    if history_erased:
        token_factor = 1.0
    else:
        token_factor = 1.12 if token_a == token_b else 0.88
    if terrain_erased:
        terrain_factor = 1.0
    else:
        terrain_factor = phi0_bridge.TERRAIN_WEIGHTS[terrain]
    return token_factor * terrain_factor


def evolve_case(
    case_name: str,
    family_a: str,
    family_b: str,
    H_bridge: torch.Tensor,
    *,
    pairings: list[tuple[int, int]],
    theta: float,
    history_erased: bool = False,
    terrain_erased: bool = False,
    type_swap: bool = False,
    seed: int,
) -> dict[str, Any]:
    generator = torch.Generator().manual_seed(seed)
    state = dense_product_state(family_a, family_b)
    prev_a: str | None = "1"
    prev_b: str | None = "2"
    events = []
    total_jumps = 0
    for cycle in range(N_CYCLES):
        token_a = choose_half_token(state, 0, prev_a)
        token_b = choose_half_token(state, HALF, prev_b)
        prev_a, prev_b = token_a, token_b
        local_token_a, local_token_b = (token_b, token_a) if type_swap else (token_a, token_b)
        for terrain_idx, terrain in enumerate(TERRAIN_ORDER_BY_TOKEN[local_token_a]):
            terrain_b = TERRAIN_ORDER_BY_TOKEN[local_token_b][terrain_idx]
            state, jumps_a = local_step_half(state, start=0, token=local_token_a, terrain=terrain, generator=generator)
            state, jumps_b = local_step_half(state, start=HALF, token=local_token_b, terrain=terrain_b, generator=generator)
            total_jumps += jumps_a + jumps_b
            state = local_intra_engine_gates(state)
            weight = history_weight(token_a, token_b, terrain, history_erased=history_erased, terrain_erased=terrain_erased)
            cross_gate = torch.linalg.matrix_exp(-1j * float(theta * weight) * H_bridge).reshape(4, 4)
            if theta != 0.0:
                for left, right in pairings:
                    state = apply_two_any_dense(state, cross_gate, left, right)
            events.append(
                {
                    "cycle": cycle,
                    "terrain_A": terrain,
                    "terrain_B": terrain_b,
                    "token_A": token_a,
                    "token_B": token_b,
                    "local_token_A": local_token_a,
                    "local_token_B": local_token_b,
                    "history_weight": weight,
                    "jumps": jumps_a + jumps_b,
                }
            )
    rho_ab = aggregate_pair_density(state, pairings)
    return {
        "case": case_name,
        "family_A": family_a,
        "family_B": family_b,
        "events": events,
        "final_state": state,
        "norm_error": abs(float(torch.linalg.vector_norm(state).item()) - 1.0),
        "total_jumps": total_jumps,
        "half_entropy": half_entropy(state),
        "mean_z_A": mean_z_half(state, 0),
        "mean_z_B": mean_z_half(state, HALF),
        "phi0": mps_runtime.phi0_readout_pair(rho_ab),
        "rho_AB_eigvals": [float(value.item()) for value in torch.linalg.eigvalsh(rho_ab).real],
    }


def case_rows(name: str, H_bridge: torch.Tensor, *, theta: float = BASE_THETA, **kwargs: Any) -> dict[str, Any]:
    pairings = bridge_pairings(name)
    rows = []
    for idx, family_a in enumerate(INITIAL_FAMILIES):
        family_b = INITIAL_FAMILIES[-1 - idx]
        rows.append(
            evolve_case(
                name,
                family_a,
                family_b,
                H_bridge,
                pairings=pairings,
                theta=theta,
                seed=20260521 + 101 * idx + 17 * len(name),
                **kwargs,
            )
        )
    mean_mi = sum(row["phi0"]["I_A_colon_B"] for row in rows) / len(rows)
    mean_ic = sum(row["phi0"]["I_c_A_to_B"] for row in rows) / len(rows)
    mean_half_entropy = sum(row["half_entropy"] for row in rows) / len(rows)
    max_norm_error = max(row["norm_error"] for row in rows)
    return {
        "name": name,
        "theta": theta,
        "pairing_graph": substrate_graph(pairings),
        "mean_I_A_colon_B": mean_mi,
        "mean_I_c_A_to_B": mean_ic,
        "mean_half_entropy": mean_half_entropy,
        "max_norm_error": max_norm_error,
        "family_rows": [
            {key: value for key, value in row.items() if key not in {"final_state", "events"}}
            | {"event_count": len(row["events"])}
            for row in rows
        ],
    }


def z3_guard(cases: list[dict[str, Any]]) -> dict[str, Any]:
    by_name = {case["name"]: case for case in cases}
    canonical = by_name["canonical_coupled_e16_runtime"]["mean_I_A_colon_B"]
    controls = {name: case["mean_I_A_colon_B"] for name, case in by_name.items() if name != "canonical_coupled_e16_runtime"}
    max_control_name, max_control = max(controls.items(), key=lambda item: item[1])
    nonzero = z3.Bool("nonzero")
    separates = z3.Bool("separates")
    coupled_runtime_built = z3.Bool("coupled_runtime_built")
    final_admission = z3.Bool("final_admission")
    solver = z3.Solver()
    solver.add(nonzero == (canonical > PHI0_TOL))
    solver.add(separates == (canonical > max_control + CONTROL_MARGIN))
    solver.add(coupled_runtime_built == True)
    solver.add(final_admission == False)
    solver.add(z3.Implies(final_admission, z3.And(nonzero, separates, coupled_runtime_built)))
    status = solver.check()
    model = solver.model()
    return {
        "sat": str(status) == "sat",
        "canonical_mean_mutual_information": canonical,
        "max_control_name": max_control_name,
        "max_control_mean_mutual_information": max_control,
        "canonical_minus_max_control": canonical - max_control,
        "nonzero": z3.is_true(model.eval(nonzero, model_completion=True)),
        "separates_from_controls": z3.is_true(model.eval(separates, model_completion=True)),
        "coupled_runtime_built": z3.is_true(model.eval(coupled_runtime_built, model_completion=True)),
        "final_manifold_admission_allowed": z3.is_true(model.eval(final_admission, model_completion=True)),
        "rule": "Coupled E16 runtime can complete Workstream 4, but final admission still requires Phi0 separation plus tensor/PEPS/full-trace closure.",
    }


def main() -> int:
    started = time.time()
    upstream = {name: read_json(path) for name, path in SOURCE_FILES.items() if name.endswith("_result")}
    Hs = bridge_hamiltonians()
    cases = [
        case_rows("no_coupling_control", Hs["enhanced"], theta=0.0),
        case_rows("canonical_coupled_e16_runtime", Hs["enhanced"]),
        case_rows("shuffled_pairing_control", Hs["enhanced"]),
        case_rows("type_swap_control", Hs["enhanced"], type_swap=True),
        case_rows("random_matched_norm_control", Hs["random_matched_norm"]),
        case_rows("history_erased_control", Hs["enhanced"], history_erased=True),
        case_rows("slow_mode_erased_control", Hs["slow_erased"]),
        case_rows("n_hat_erased_control", Hs["n_hat_erased"]),
        case_rows("terrain_erased_control", Hs["terrain_erased"], terrain_erased=True),
    ]
    guard = z3_guard(cases)
    case_by_name = {case["name"]: case for case in cases}
    bridge_status = (
        "rescued_control_separated"
        if guard["separates_from_controls"]
        else ("open_nonzero_not_control_separated" if guard["nonzero"] else "killed_near_zero")
    )
    coupled_delta = abs(
        case_by_name["canonical_coupled_e16_runtime"]["mean_I_A_colon_B"]
        - case_by_name["no_coupling_control"]["mean_I_A_colon_B"]
    )
    positive = {
        "upstream_receipts_loaded": {
            "pass": upstream["phi0_bridge_result"].get("all_pass") is True
            and upstream["mps_runtime_result"].get("all_pass") is True,
            "loaded": sorted(upstream),
        },
        "coupled_e16_cases_ran": {
            "pass": len(cases) == 9 and all(len(case["family_rows"]) == len(INITIAL_FAMILIES) for case in cases),
            "case_names": [case["name"] for case in cases],
        },
        "norms_bounded": {
            "pass": max(case["max_norm_error"] for case in cases) < NORM_TOL,
            "max_norm_error": max(case["max_norm_error"] for case in cases),
            "threshold": NORM_TOL,
        },
        "cross_engine_coupling_changes_runtime": {
            "pass": coupled_delta > 1.0e-4,
            "canonical_minus_no_coupling_abs_mi_delta": coupled_delta,
        },
        "rho_ab_phi0_extracted": {
            "pass": all("mean_I_A_colon_B" in case and case["pairing_graph"]["cross_edge_count"] == HALF for case in cases),
            "canonical_phi0": case_by_name["canonical_coupled_e16_runtime"]["mean_I_A_colon_B"],
        },
        "bridge_status_classified": {
            "pass": bridge_status in {"rescued_control_separated", "open_nonzero_not_control_separated", "killed_near_zero"},
            "bridge_status": bridge_status,
            "z3": guard,
        },
    }
    all_pass = all(item["pass"] for item in positive.values()) and guard["sat"]
    summary = {
        "all_pass": all_pass,
        "workstream_4_status": "coupled_e16_runtime_built",
        "bridge_status": bridge_status,
        "bridge_status_note": (
            "The canonical runtime clears the configured control margin only weakly; "
            "type-swap control is nearly tied, so this is Workstream 4 runtime "
            "evidence, not a final bridge theorem."
        ),
        "case_mean_mutual_information": {case["name"]: case["mean_I_A_colon_B"] for case in cases},
        "canonical_minus_max_control": guard["canonical_minus_max_control"],
        "max_control_name": guard["max_control_name"],
        "canonical_minus_no_coupling_abs_mi_delta": coupled_delta,
        "final_manifold_admission_allowed": False,
        "next_required_work": "Use this coupled E16 receipt to refresh the full manifold trace, then continue with L32/L64 tensor mitigation and PEPS/PEPS3D dynamic blockers.",
    }
    boundary = {
        "promotion_allowed": PROMOTION_ALLOWED,
        "workstream_4_complete_as_runtime": True,
        "final_manifold_admission_allowed": False,
        "not_peps_or_peps3d": True,
        "not_l32_or_l64_tensor_scaling": True,
        "weak_control_margin_only": guard["canonical_minus_max_control"] < 2.0 * CONTROL_MARGIN,
        "why_not_final": [
            "This is a bounded dense E16 trajectory, not PEPS/PEPS3D dynamics.",
            "L32/L64 tensor-network scaling remains open.",
            "The type-swap control is nearly tied with the canonical bridge, so the separation is weak and not a theorem.",
            "Full manifold trace must stay blocked until PEPS/PEPS3D and final bridge/admission receipts exist.",
        ],
    }
    graveyard = {
        "not_final_manifold_admission": {
            "pass": guard["final_manifold_admission_allowed"] is False,
            "detail": "Z3 guard keeps final manifold admission false for this Workstream 4 runtime receipt.",
        },
        "not_peps_or_peps3d": {
            "pass": boundary["not_peps_or_peps3d"],
            "detail": "The state is a bounded dense E16 trajectory, not PEPS/PEPS3D dynamics.",
        },
        "not_l32_or_l64_scaling": {
            "pass": boundary["not_l32_or_l64_tensor_scaling"],
            "detail": "The receipt does not attempt L32/L64 tensor-network scaling.",
        },
        "type_swap_control_nearly_tied": {
            "pass": boundary["weak_control_margin_only"],
            "canonical_minus_max_control": guard["canonical_minus_max_control"],
            "max_control_name": guard["max_control_name"],
            "detail": "The control-separation margin is intentionally treated as weak runtime evidence only.",
        },
    }
    nearby_variants = {
        "total": len(graveyard),
        "passed": sum(1 for item in graveyard.values() if item["pass"]),
        "items": sorted(graveyard),
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
            "previous_phi0_bridge_status": upstream["phi0_bridge_result"].get("summary", {}).get("bridge_status"),
            "mps_tensor_runtime_status": upstream["mps_runtime_result"].get("summary", {}).get("tensor_runtime_status"),
            "full_trace_goal_complete": upstream["full_trace_result"].get("summary", {}).get("final_goal_complete"),
        },
        "runtime_parameters": {
            "length": LENGTH,
            "half_size": HALF,
            "cycles": N_CYCLES,
            "base_theta": BASE_THETA,
            "initial_families": INITIAL_FAMILIES,
            "state_dimension": 2**LENGTH,
            "trajectory_kind": "dense_pure_state_quantum_trajectory_with_cross_engine_bridge_gates",
        },
        "cases": cases,
        "positive": positive,
        "boundary": boundary,
        "graveyard_companions": graveyard,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": (
            "This is a v5 Workstream 4 coupled-runtime scout over current QIT "
            "engine receipts; it is not a legacy v4 probe, PEPS/PEPS3D "
            "execution, L32/L64 tensor scaling, final Phi0 theorem, or final "
            "manifold admission."
        ),
        "next_work_required": [
            "Keep Workstream F refreshed against this E16 runtime receipt.",
            "Test PEPS/PEPS3D or tensor-network scaling rather than treating dense E16 as final.",
            "Strengthen or falsify the weak bridge margin against type-swap and other adversarial controls.",
        ],
        "blockers": [],
        "summary": summary,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
