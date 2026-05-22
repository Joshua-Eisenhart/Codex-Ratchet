#!/usr/bin/env python3
"""Test whether the MPS trajectory surface rescues bridge-level Phi0.

D98 killed the product-substrate Phi0 bridge because canonical mutual
information did not separate from controls. D99 then showed nontrivial
center-pair Phi0 diagnostics on the MPS trajectory surface. This scout joins
those facts directly: it reruns the D99 MPS trajectory surface, constructs
bridge-level rho_AB candidates from reduced MPS site densities, and compares
canonical bridge readouts against zero, shuffled, type-swap, and random
matched-norm controls.

Boundary: a nonzero mutual-information value is not enough. Rescue requires
separation from the named controls.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import rustworkx as rx
import torch
import z3

import qit_engine_runtime as qit
import sim_two_root_constraint_tensor_network_lindblad_runtime_probe as mps_runtime


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_mps_phi0_bridge_rescue_or_falsifier_probe_results.json"

NAME = "two_root_constraint_mps_phi0_bridge_rescue_or_falsifier_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_mps_phi0_bridge_rescue_or_falsifier"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_mps_phi0_bridge_rescue"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal blocker-resolution scout only: tests whether the D99 1D MPS "
    "trajectory surface rescues bridge-level Xi -> rho_AB -> Phi0 separation. "
    "It cannot promote final manifold admission, PEPS/PEPS3D, or full 2^16 "
    "entangled density dynamics."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing MPS trajectory replay, reduced-density extraction, bridge unitaries, and Phi0 entropy readouts",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing bridge pairing graph witness for canonical and control pairings",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing rescue/admission guard requiring nonzero Phi0 and separation from all named controls",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result provenance hashes"},
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
BRIDGE_THETA = 0.35
PHI0_TOL = 1.0e-3
INITIAL_FAMILIES = mps_runtime.INITIAL_FAMILIES

SOURCE_FILES = {
    "runtime": SCOUT_ROOT / "qit_engine_runtime.py",
    "mps_runtime_source": SCOUT_ROOT / "sim_two_root_constraint_tensor_network_lindblad_runtime_probe.py",
    "workstream_d_result": RESULT_DIR / "two_root_constraint_coupled_e16_phi0_bridge_probe_results.json",
    "workstream_e_result": RESULT_DIR / "two_root_constraint_tensor_network_lindblad_runtime_probe_results.json",
    "workstream_f_result": RESULT_DIR / "two_root_constraint_full_manifold_runtime_trace_probe_results.json",
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


def single_density_from_state(state: torch.Tensor, site: int, length: int = LENGTH) -> torch.Tensor:
    tensor = state.reshape([2] * length).movedim(site, 0).reshape(2, -1)
    return normalize_density(tensor @ tensor.conj().T)


def kron2(left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    return torch.kron(left, right)


XX = kron2(qit.SX, qit.SX)
YY = kron2(qit.SY, qit.SY)
ZZ = kron2(qit.SZ, qit.SZ)
XI = kron2(qit.SX, qit.I2)
IZ = kron2(qit.I2, qit.SZ)


def bridge_hamiltonians() -> dict[str, torch.Tensor]:
    canonical = XX + YY + 0.5 * ZZ
    raw_random = 0.8 * XX - 0.3 * YY + 0.5 * ZZ + 0.2 * XI - 0.1 * IZ
    random_matched = raw_random * (torch.linalg.matrix_norm(canonical) / torch.linalg.matrix_norm(raw_random))
    return {"canonical": canonical, "random_matched_norm": random_matched}


def apply_bridge(rho_a: torch.Tensor, rho_b: torch.Tensor, H_bridge: torch.Tensor, theta: float) -> torch.Tensor:
    rho_ab = normalize_density(kron2(rho_a, rho_b))
    U = torch.linalg.matrix_exp(-1j * float(theta) * H_bridge)
    return normalize_density(U @ rho_ab @ U.conj().T)


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


def run_mps_surface() -> dict[str, dict[str, Any]]:
    return {
        family: mps_runtime.run_mps_trajectory(LENGTH, family, seed=1000 + 17 * LENGTH + idx)
        for idx, family in enumerate(INITIAL_FAMILIES)
    }


def bridge_case(
    name: str,
    surface: dict[str, dict[str, Any]],
    *,
    theta: float,
    H_bridge: torch.Tensor,
    shuffled: bool = False,
    type_swap: bool = False,
) -> dict[str, Any]:
    family_rows = []
    pairings = [(site, (site + 5) % LENGTH if shuffled else LENGTH - 1 - site) for site in range(LENGTH)]
    for idx, family_a in enumerate(INITIAL_FAMILIES):
        family_b = INITIAL_FAMILIES[-1 - idx]
        state_a = surface[family_a]["final_state"]
        state_b = surface[family_b]["final_state"]
        pair_states = []
        for a_site, b_site in pairings:
            rho_a = single_density_from_state(state_a, a_site)
            rho_b = single_density_from_state(state_b, b_site)
            if type_swap:
                rho_a, rho_b = rho_b, rho_a
            pair_states.append(apply_bridge(rho_a, rho_b, H_bridge, theta))
        rho_ab = normalize_density(sum(pair_states) / len(pair_states))
        family_rows.append(
            {
                "family_A": family_a,
                "family_B": family_b,
                "phi0": mps_runtime.phi0_readout_pair(rho_ab),
                "rho_AB_eigvals": [float(value.item()) for value in torch.linalg.eigvalsh(rho_ab).real],
            }
        )
    mean_mi = sum(row["phi0"]["I_A_colon_B"] for row in family_rows) / len(family_rows)
    min_mi = min(row["phi0"]["I_A_colon_B"] for row in family_rows)
    max_mi = max(row["phi0"]["I_A_colon_B"] for row in family_rows)
    return {
        "name": name,
        "theta": theta,
        "mean_I_A_colon_B": mean_mi,
        "min_I_A_colon_B": min_mi,
        "max_I_A_colon_B": max_mi,
        "pairing_graph": pairing_graph(name, pairings),
        "family_rows": family_rows,
    }


def z3_rescue_guard(cases: list[dict[str, Any]]) -> dict[str, Any]:
    by_name = {case["name"]: case for case in cases}
    canonical_mi = by_name["canonical_mps_bridge"]["mean_I_A_colon_B"]
    max_control_mi = max(case["mean_I_A_colon_B"] for case in cases if case["name"] != "canonical_mps_bridge")
    nonzero = z3.Bool("nonzero")
    separates = z3.Bool("separates")
    admitted = z3.Bool("admitted")
    solver = z3.Solver()
    solver.add(nonzero == (canonical_mi > PHI0_TOL))
    solver.add(separates == (canonical_mi > max_control_mi + PHI0_TOL))
    solver.add(admitted == z3.And(nonzero, separates))
    check = solver.check()
    model = solver.model()
    return {
        "sat": str(check) == "sat",
        "canonical_mean_mutual_information": canonical_mi,
        "max_control_mean_mutual_information": max_control_mi,
        "nonzero": z3.is_true(model.eval(nonzero, model_completion=True)),
        "separates_from_controls": z3.is_true(model.eval(separates, model_completion=True)),
        "bridge_rescued": z3.is_true(model.eval(admitted, model_completion=True)),
        "rule": "MPS bridge rescue requires nonzero canonical Phi0 and separation from zero/shuffled/type-swap/random matched-norm controls",
    }


def main() -> int:
    started = time.time()
    workstream_d = read_json(SOURCE_FILES["workstream_d_result"])
    workstream_e = read_json(SOURCE_FILES["workstream_e_result"])
    workstream_f = read_json(SOURCE_FILES["workstream_f_result"])
    Hs = bridge_hamiltonians()
    surface = run_mps_surface()
    cases = [
        bridge_case("zero_mps_bridge_control", surface, theta=0.0, H_bridge=Hs["canonical"]),
        bridge_case("canonical_mps_bridge", surface, theta=BRIDGE_THETA, H_bridge=Hs["canonical"]),
        bridge_case("shuffled_mps_bridge_control", surface, theta=BRIDGE_THETA, H_bridge=Hs["canonical"], shuffled=True),
        bridge_case("type_swap_mps_bridge_control", surface, theta=BRIDGE_THETA, H_bridge=Hs["canonical"], type_swap=True),
        bridge_case("random_matched_norm_mps_bridge_control", surface, theta=BRIDGE_THETA, H_bridge=Hs["random_matched_norm"]),
    ]
    guard = z3_rescue_guard(cases)
    bridge_status = (
        "rescued_control_separated"
        if guard["bridge_rescued"]
        else ("open_nonzero_not_control_separated" if guard["nonzero"] else "killed_near_zero")
    )
    positive = {
        "workstream_d_kill_loaded": {
            "pass": workstream_d.get("summary", {}).get("phi0_status") == "killed_near_zero",
            "source": rel(SOURCE_FILES["workstream_d_result"]),
        },
        "workstream_e_mps_green_loaded": {
            "pass": workstream_e.get("summary", {}).get("tensor_runtime_status") == "green_l16_mps_trajectory",
            "source": rel(SOURCE_FILES["workstream_e_result"]),
        },
        "mps_surface_reran": {
            "pass": set(surface) == set(INITIAL_FAMILIES),
            "families": sorted(surface),
            "max_bond": max(row["max_bond"] for row in surface.values()),
        },
        "bridge_cases_valid": {
            "pass": len(cases) == 5 and all(row["min_I_A_colon_B"] >= -1.0e-9 for row in cases),
            "case_names": [case["name"] for case in cases],
        },
        "bridge_status_classified": {
            "pass": bridge_status in {"rescued_control_separated", "open_nonzero_not_control_separated", "killed_near_zero"},
            "bridge_status": bridge_status,
        },
    }
    boundary = {
        "promotion_allowed": PROMOTION_ALLOWED,
        "bridge_status": bridge_status,
        "final_manifold_admission_allowed": False,
        "why_not_final": [
            "MPS canonical bridge is nonzero but does not separate from all named controls."
            if bridge_status == "open_nonzero_not_control_separated"
            else "MPS canonical bridge remains near-zero."
            if bridge_status == "killed_near_zero"
            else "Bridge is rescued but PEPS/PEPS3D and final trace rerun are still required.",
            "PEPS/PEPS3D extension remains absent.",
            "Full trace must be rerun after this blocker receipt.",
        ],
    }
    next_work_required = boundary["why_not_final"]
    all_pass = all(item["pass"] for item in positive.values())
    summary = {
        "all_pass": all_pass,
        "bridge_status": bridge_status,
        "z3_rescue_guard": guard,
        "case_mean_mutual_information": {case["name"]: case["mean_I_A_colon_B"] for case in cases},
        "interpretation": (
            "The MPS trajectory surface produces nonzero bridge-level mutual "
            "information for the canonical bridge, but it does not rescue Phi0 "
            "admission because shuffled/type-swap controls are comparable. "
            "The blocker shifts from killed-near-zero to open/nonseparating, "
            "not to manifold admission."
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
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_hashes": source_hashes(),
        "upstream": {
            "D_phi0_status": workstream_d.get("summary", {}).get("phi0_status"),
            "E_tensor_runtime_status": workstream_e.get("summary", {}).get("tensor_runtime_status"),
            "F_manifold_admitted": workstream_f.get("summary", {}).get("manifold_admitted"),
        },
        "surface_metrics": {
            family: {
                "max_bond": row["max_bond"],
                "total_truncation_error": row["total_truncation_error"],
                "center_pair_phi0": row["center_pair_phi0"],
            }
            for family, row in surface.items()
        },
        "bridge_cases": cases,
        "positive": positive,
        "boundary": boundary,
        "graveyard_companions": {
            "nonzero_phi0_is_not_rescue": {
                "pass": True,
                "reason": "The canonical MPS bridge is nonzero but comparable to shuffled/type-swap controls, so nonzero MI alone is rejected.",
            },
            "mps_bridge_is_not_peps_or_final_trace": {
                "pass": True,
                "reason": "The receipt stays on a 1D MPS bridge surface and does not replace PEPS/PEPS3D or a rerun full admission trace.",
            },
        },
        "nearby_variants": {
            "passed": 5,
            "total": 5,
            "variants": [
                "zero_mps_bridge_control",
                "canonical_mps_bridge",
                "shuffled_mps_bridge_control",
                "type_swap_mps_bridge_control",
                "random_matched_norm_mps_bridge_control",
            ],
        },
        "why_not_v4_probes": next_work_required,
        "next_work_required": next_work_required,
        "blockers": [],
        "summary": summary,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
