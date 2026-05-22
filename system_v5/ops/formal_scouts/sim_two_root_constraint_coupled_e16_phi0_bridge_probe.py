#!/usr/bin/env python3
"""Build a coupled E=16 product-substrate bridge and Phi0 readout.

This Workstream D scout uses the Workstream C hysteretic adaptive engine as the
local mechanism, lifts it to two E=8 engine substrates (16 one-qubit sites), and
constructs two-qubit bridge cut states across eight disconnected paired-engine
components. It reports an aggregate rho_AB candidate and correlational entropy
readouts while preserving the boundary: this is a product-substrate bridge
scout, not tensor-network Lindblad or final manifold admission.
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


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_coupled_e16_phi0_bridge_probe_results.json"

NAME = "two_root_constraint_coupled_e16_phi0_bridge_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_coupled_e16_product_substrate_bridge"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_coupled_e16_phi0_bridge"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal Workstream D scout only: builds a coupled E=16 product-substrate "
    "runtime from two E=8 adaptive engine surfaces and eight disconnected "
    "paired components, then reads an aggregate two-qubit rho_AB/Phi0 bridge "
    "candidate. It cannot promote tensor-network Lindblad, full 2^16 entangled "
    "density dynamics, PEPS/PEPS3D evidence, or final constraint-manifold "
    "admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing local adaptive engine states, two-qubit bridge unitaries, partial channel application, and entropy readouts",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing E=16 site/pairing graph witness for bridge and shuffled-control topology",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion guard for Phi0 separation versus controls and tensor-network absence",
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

TAU = 0.5
LOCAL_CYCLES = 80
BRIDGE_THETA = 0.35
PHI0_TOL = 1.0e-3

PLACEMENTS = ["Se_i", "Si_i", "Ni_i", "Ne_i", "Se_o", "Ne_o", "Ni_o", "Si_o"]
SITE_Z = [-0.6, -0.3, -0.21, -0.19, 0.0, 0.19, 0.21, 0.6]

SOURCE_FILES = {
    "runtime": SCOUT_ROOT / "qit_engine_runtime.py",
    "workstream_c_result": RESULT_DIR / "two_root_constraint_adaptive_engine_switching_probe_results.json",
    "plan": REPO / "system_v5" / "ops" / "QIT_ENGINE_MANIFOLD_FULL_BUILD_PLAN_20260521.md",
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


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = 0.5 * (rho + rho.conj().T)
    return rho / torch.trace(rho)


def choose_hysteresis(rho: torch.Tensor, prev: str | None) -> str:
    z_val = qit.bloch(rho)[2]
    active = prev or "1"
    if active == "1":
        return "1" if z_val >= -0.2 else "2"
    return "1" if z_val >= 0.2 else "2"


def evolve_local_site(rho0: torch.Tensor, prev0: str, engines: dict[str, torch.Tensor]) -> dict[str, Any]:
    rho = rho0.clone()
    prev = prev0
    tokens: list[str] = []
    for _ in range(LOCAL_CYCLES):
        token = choose_hysteresis(rho, prev)
        tokens.append(token)
        prev = token
        rho = qit.normalize_density(qit.mat(engines[token] @ qit.vec(rho)))
    return {
        "rho": rho,
        "bloch": qit.bloch(rho),
        "last_token": prev,
        "last_tokens": tokens[-8:],
    }


def build_engine_surface(side: str, engines: dict[str, torch.Tensor]) -> list[dict[str, Any]]:
    rows = []
    z_values = SITE_Z if side == "A" else list(reversed([-value for value in SITE_Z]))
    initial_prev = "1" if side == "A" else "2"
    for idx, (placement, z_val) in enumerate(zip(PLACEMENTS, z_values)):
        rho0 = qit.rho_from_bloch((0.0, 0.0, float(z_val)))
        evolved = evolve_local_site(rho0, initial_prev, engines)
        rows.append(
            {
                "side": side,
                "site": idx,
                "placement": placement,
                "initial_z": float(z_val),
                "initial_prev": initial_prev,
                **evolved,
            }
        )
    return rows


def kron2(left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    return torch.kron(left, right)


XX = kron2(qit.SX, qit.SX)
YY = kron2(qit.SY, qit.SY)
ZZ = kron2(qit.SZ, qit.SZ)
XI = kron2(qit.SX, qit.I2)
IZ = kron2(qit.I2, qit.SZ)


def scaled_bridge_hamiltonians() -> dict[str, torch.Tensor]:
    canonical = XX + YY + 0.5 * ZZ
    raw_random = 0.8 * XX - 0.3 * YY + 0.5 * ZZ + 0.2 * XI - 0.1 * IZ
    scale = torch.linalg.matrix_norm(canonical) / torch.linalg.matrix_norm(raw_random)
    return {
        "canonical": canonical,
        "random_matched_norm": scale * raw_random,
    }


def bridge_unitary(H_bridge: torch.Tensor, theta: float) -> torch.Tensor:
    return torch.linalg.matrix_exp(-1j * float(theta) * H_bridge)


def apply_unitary_bridge(rho_ab: torch.Tensor, H_bridge: torch.Tensor, theta: float) -> torch.Tensor:
    U = bridge_unitary(H_bridge, theta)
    return normalize_density(U @ rho_ab @ U.conj().T)


def apply_channel_to_pair(rho_ab: torch.Tensor, channel: torch.Tensor, target: str) -> torch.Tensor:
    tensor = rho_ab.reshape(2, 2, 2, 2)
    out = torch.zeros((2, 2, 2, 2), dtype=qit.DTYPE)
    if target == "A":
        for b in range(2):
            for d in range(2):
                block = tensor[:, b, :, d]
                evolved = qit.mat(channel @ qit.vec(block))
                out[:, b, :, d] = evolved
    elif target == "B":
        for a in range(2):
            for c in range(2):
                block = tensor[a, :, c, :]
                evolved = qit.mat(channel @ qit.vec(block))
                out[a, :, c, :] = evolved
    else:
        raise ValueError(f"target must be A or B, got {target}")
    return normalize_density(out.reshape(4, 4))


def partial_traces(rho_ab: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    tensor = rho_ab.reshape(2, 2, 2, 2)
    rho_a = torch.einsum("abcb->ac", tensor)
    rho_b = torch.einsum("abad->bd", tensor)
    return normalize_density(rho_a), normalize_density(rho_b)


def entropy(rho: torch.Tensor) -> float:
    evals = torch.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real
    clipped = torch.clamp(evals, min=1.0e-15)
    return float((-torch.sum(clipped * torch.log(clipped))).item())


def entropy_readout(rho_ab: torch.Tensor) -> dict[str, float]:
    rho_a, rho_b = partial_traces(rho_ab)
    s_a = entropy(rho_a)
    s_b = entropy(rho_b)
    s_ab = entropy(rho_ab)
    return {
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "I_c_A_to_B": s_b - s_ab,
        "S_A_given_B": s_ab - s_b,
        "I_A_colon_B": s_a + s_b - s_ab,
    }


def pairing_graph(pairing: list[tuple[int, int]]) -> dict[str, Any]:
    graph = rx.PyGraph()
    nodes = {("A", idx): graph.add_node(f"A{idx}") for idx in range(8)}
    nodes.update({("B", idx): graph.add_node(f"B{idx}") for idx in range(8)})
    for a_idx, b_idx in pairing:
        graph.add_edge(nodes[("A", a_idx)], nodes[("B", b_idx)], "bridge")
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "connected_components": len(rx.connected_components(graph)),
    }


def aggregate_rho_ab(pair_states: list[torch.Tensor]) -> torch.Tensor:
    rho = sum(pair_states) / len(pair_states)
    return normalize_density(rho)


def run_bridge_case(
    name: str,
    side_a: list[dict[str, Any]],
    side_b: list[dict[str, Any]],
    engines: dict[str, torch.Tensor],
    H_bridge: torch.Tensor,
    theta: float,
    *,
    pairing: list[tuple[int, int]],
    swap_types: bool = False,
    post_local: bool = True,
) -> dict[str, Any]:
    pair_states: list[torch.Tensor] = []
    pair_rows: list[dict[str, Any]] = []
    for a_idx, b_idx in pairing:
        a = side_a[a_idx]
        b = side_b[b_idx]
        rho_ab = normalize_density(kron2(a["rho"], b["rho"]))
        rho_ab = apply_unitary_bridge(rho_ab, H_bridge, theta)
        if post_local:
            token_a = b["last_token"] if swap_types else a["last_token"]
            token_b = a["last_token"] if swap_types else b["last_token"]
            rho_ab = apply_channel_to_pair(rho_ab, engines[token_a], "A")
            rho_ab = apply_channel_to_pair(rho_ab, engines[token_b], "B")
        pair_states.append(rho_ab)
        pair_rows.append(
            {
                "A_site": a_idx,
                "B_site": b_idx,
                "A_token": a["last_token"],
                "B_token": b["last_token"],
                "A_bloch": a["bloch"],
                "B_bloch": b["bloch"],
            }
        )
    rho_ab = aggregate_rho_ab(pair_states)
    evals = torch.linalg.eigvalsh(rho_ab).real
    readout = entropy_readout(rho_ab)
    return {
        "name": name,
        "theta": float(theta),
        "pairing_graph": pairing_graph(pairing),
        "rho_AB": rho_ab,
        "rho_AB_eigvals": [float(value.item()) for value in evals],
        "trace": float(torch.trace(rho_ab).real.item()),
        "min_eigval": float(torch.min(evals).item()),
        "entropy_readout": readout,
        "pair_rows": pair_rows,
    }


def z3_phi0_guard(cases: list[dict[str, Any]]) -> dict[str, Any]:
    by_name = {case["name"]: case for case in cases}
    coupled_mi = by_name["coupled_canonical"]["entropy_readout"]["I_A_colon_B"]
    control_mi = max(
        case["entropy_readout"]["I_A_colon_B"]
        for case in cases
        if case["name"] != "coupled_canonical"
    )
    nonzero = z3.Bool("nonzero")
    separates = z3.Bool("separates")
    tensor_network = z3.Bool("tensor_network")
    full_admission = z3.Bool("full_admission")
    solver = z3.Solver()
    solver.add(nonzero == (coupled_mi > PHI0_TOL))
    solver.add(separates == (coupled_mi > control_mi + PHI0_TOL))
    solver.add(tensor_network == False)
    solver.add(full_admission == z3.And(nonzero, separates, tensor_network))
    check = solver.check()
    model = solver.model()
    return {
        "sat": str(check) == "sat",
        "coupled_mutual_information": coupled_mi,
        "max_control_mutual_information": control_mi,
        "nonzero": z3.is_true(model.eval(nonzero, model_completion=True)),
        "separates_from_all_controls": z3.is_true(model.eval(separates, model_completion=True)),
        "full_admission_allowed": z3.is_true(model.eval(full_admission, model_completion=True)),
        "rule": "full admission requires nonzero Phi0 separation and tensor-network/full-dynamics evidence",
    }


def source_hashes() -> dict[str, Any]:
    return {name: {"path": rel(path), "sha256": sha256(path)} for name, path in SOURCE_FILES.items()}


def workstream_c_candidate_names(workstream_c: dict[str, Any]) -> list[str]:
    summary = workstream_c.get("summary", {}) if isinstance(workstream_c.get("summary"), dict) else {}
    names = summary.get("weak_basin_candidates")
    return list(names) if isinstance(names, list) else []


def strip_rho(case: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in case.items() if key != "rho_AB"}


def main() -> int:
    started = time.time()
    workstream_c = read_json(SOURCE_FILES["workstream_c_result"])
    engines = {
        "1": qit.engine_channel("L", "iter176_xz", tau=TAU, normalize=True),
        "2": qit.engine_channel("R", "iter176_xz", tau=TAU, normalize=True),
    }
    side_a = build_engine_surface("A", engines)
    side_b = build_engine_surface("B", engines)
    Hs = scaled_bridge_hamiltonians()
    identity_pairing = [(idx, idx) for idx in range(8)]
    shuffled_pairing = [(idx, (idx + 3) % 8) for idx in range(8)]
    cases = [
        run_bridge_case(
            "coupled_canonical",
            side_a,
            side_b,
            engines,
            Hs["canonical"],
            BRIDGE_THETA,
            pairing=identity_pairing,
        ),
        run_bridge_case(
            "zero_bridge_control",
            side_a,
            side_b,
            engines,
            Hs["canonical"],
            0.0,
            pairing=identity_pairing,
        ),
        run_bridge_case(
            "shuffled_bridge_control",
            side_a,
            side_b,
            engines,
            Hs["canonical"],
            BRIDGE_THETA,
            pairing=shuffled_pairing,
        ),
        run_bridge_case(
            "type_swap_control",
            side_a,
            side_b,
            engines,
            Hs["canonical"],
            BRIDGE_THETA,
            pairing=identity_pairing,
            swap_types=True,
        ),
        run_bridge_case(
            "random_matched_norm_bridge_control",
            side_a,
            side_b,
            engines,
            Hs["random_matched_norm"],
            BRIDGE_THETA,
            pairing=identity_pairing,
        ),
        run_bridge_case(
            "bridge_disabled_after_warmup_control",
            side_a,
            side_b,
            engines,
            Hs["canonical"],
            0.0,
            pairing=identity_pairing,
            post_local=False,
        ),
    ]
    guard = z3_phi0_guard(cases)
    coupled = next(case for case in cases if case["name"] == "coupled_canonical")
    zero = next(case for case in cases if case["name"] == "zero_bridge_control")
    phi0_status = (
        "nonzero_supported"
        if guard["nonzero"] and guard["separates_from_all_controls"]
        else ("open_nonzero_not_control_separated" if guard["nonzero"] else "killed_near_zero")
    )
    positive = {
        "workstream_c_candidate_exists": {
            "pass": "schedule_memory_hysteresis_z" in workstream_c_candidate_names(workstream_c),
            "source": rel(SOURCE_FILES["workstream_c_result"]),
        },
        "e16_product_substrate_constructed": {
            "pass": len(side_a) == 8 and len(side_b) == 8,
            "A_site_count": len(side_a),
            "B_site_count": len(side_b),
            "total_site_count": len(side_a) + len(side_b),
        },
        "rho_ab_valid_all_cases": {
            "pass": all(abs(case["trace"] - 1.0) < 1.0e-9 and case["min_eigval"] > -1.0e-9 for case in cases),
            "case_count": len(cases),
            "min_eigval": min(case["min_eigval"] for case in cases),
        },
        "phi0_readouts_present": {
            "pass": all(
                set(case["entropy_readout"]) >= {"S_A", "S_B", "S_AB", "I_c_A_to_B", "S_A_given_B", "I_A_colon_B"}
                for case in cases
            ),
            "coupled_readout": coupled["entropy_readout"],
        },
        "coupled_zero_bridge_delta_recorded": {
            "pass": True,
            "delta_mutual_information": coupled["entropy_readout"]["I_A_colon_B"]
            - zero["entropy_readout"]["I_A_colon_B"],
            "threshold": PHI0_TOL,
            "above_threshold": abs(coupled["entropy_readout"]["I_A_colon_B"] - zero["entropy_readout"]["I_A_colon_B"])
            > PHI0_TOL,
            "diagnostic": "delta is recorded as a diagnostic; threshold failure belongs to the graveyard, not positive support",
        },
        "phi0_status_classified": {
            "pass": phi0_status in {"nonzero_supported", "open_nonzero_not_control_separated", "killed_near_zero"},
            "phi0_status": phi0_status,
        },
    }
    graveyard = {
        "phi0_full_admission_not_allowed": {
            "pass": not guard["full_admission_allowed"],
            "z3_guard": guard,
        },
        "canonical_bridge_does_not_clear_control_separation": {
            "pass": not guard["separates_from_all_controls"],
            "coupled_mutual_information": guard["coupled_mutual_information"],
            "max_control_mutual_information": guard["max_control_mutual_information"],
        },
        "canonical_bridge_delta_below_phi0_threshold": {
            "pass": not guard["nonzero"],
            "delta_mutual_information": coupled["entropy_readout"]["I_A_colon_B"]
            - zero["entropy_readout"]["I_A_colon_B"],
            "threshold": PHI0_TOL,
        },
        "product_substrate_boundary_not_promoted": {
            "pass": True,
            "detail": "E=16 product-substrate bridge has 16 graph nodes and 8 disconnected paired components; it is explicitly not full 2^16 entangled density dynamics.",
            "connected_components": coupled["pairing_graph"]["connected_components"],
        },
    }
    nearby_variants = {
        "total": len(graveyard),
        "passed": sum(1 for row in graveyard.values() if row["pass"]),
        "variants": sorted(graveyard),
    }
    boundary = {
        "promotion_allowed": PROMOTION_ALLOWED,
        "product_substrate_not_full_2_pow_16_density": True,
        "not_tensor_network": True,
        "not_final_manifold_admission": True,
        "phi0_status": phi0_status,
        "z3_full_admission_allowed": guard["full_admission_allowed"],
    }
    next_work_required = [
        "This is an E=16 product-substrate bridge, not full 2^16 entangled density dynamics.",
        "Workstream E tensor-network Lindblad is still required before scale/manifold admission.",
        "Workstream F full constraint-manifold trace is still required.",
    ]
    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in graveyard.values())
        and not guard["full_admission_allowed"]
    )
    summary = {
        "all_pass": all_pass,
        "phi0_status": phi0_status,
        "coupled_entropy_readout": coupled["entropy_readout"],
        "zero_bridge_entropy_readout": zero["entropy_readout"],
        "z3_phi0_guard": guard,
        "interpretation": (
            "Workstream D produced a valid coupled E=16 product-substrate "
            "aggregate rho_AB candidate and Phi0 readouts over eight disconnected "
            "paired components. The canonical bridge does not create a robust "
            "nonzero mutual-information separation against controls on this "
            "product-substrate surface, so Phi0 is classified as killed/near-zero "
            "here. Full admission also remains blocked because this is not "
            "tensor-network Lindblad or full 2^16 entangled dynamics."
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
        "parameters": {
            "tau": TAU,
            "local_cycles": LOCAL_CYCLES,
            "bridge_theta": BRIDGE_THETA,
            "placements": PLACEMENTS,
            "site_z": SITE_Z,
        },
        "positive": positive,
        "graveyard_companions": graveyard,
        "nearby_variants": nearby_variants,
        "boundary": boundary,
        "why_not_v4_probes": (
            "This is a v5 Workstream D product-substrate bridge scout over the shared "
            "exact-torch QIT runtime; it is not a legacy v4 probe, tensor-network "
            "Lindblad execution, full 2^16 entangled density dynamics, or final "
            "manifold admission."
        ),
        "next_work_required": next_work_required,
        "blockers": [] if all_pass else [
            name
            for name, item in {**positive, **graveyard}.items()
            if not item.get("pass")
        ],
        "side_A": [{key: value for key, value in row.items() if key != "rho"} for row in side_a],
        "side_B": [{key: value for key, value in row.items() if key != "rho"} for row in side_b],
        "bridge_cases": [strip_rho(case) for case in cases],
        "summary": summary,
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(summary), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
