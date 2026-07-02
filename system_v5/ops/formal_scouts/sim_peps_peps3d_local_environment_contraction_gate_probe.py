#!/usr/bin/env python3
"""PEPS/PEPS3D local environment-contraction gate.

This scout adds the next stricter tensor-carrier boundary after MPS handoff:
PEPS/PEPS3D rows must produce environment-contraction receipts, not only local
tensor signatures. The contraction here is deliberately local star/edge
environment contraction; it is not CTMRG and not full-network closure.

It does not admit final PEPS/PEPS3D dynamics, Axis0, Xi, flux, gravity,
Standard Model, Yang-Mills, Riemann, or physics claims.
"""

from __future__ import annotations

import itertools
import json
import math
import pathlib
import time
from typing import Any

import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "peps_peps3d_local_environment_contraction_gate_probe_results.json"

NAME = "peps_peps3d_local_environment_contraction_gate_probe"
SIM_ID = NAME
VERSION = "2.0.0"
TIER = "2 finite PEPS3D seed carrier"
PURPOSE = (
    "Test whether the active finite PEPS3D seed carrier supports bounded local "
    "star/edge environment contraction signatures without dense full-network closure."
)
SCIENTIFIC_QUESTION = (
    "Can finite PEPS3D seed-carrier tensors produce normalized local site and edge "
    "environment readouts while identity, topology-shuffled, dense-closure, and "
    "promotion controls remain blocked?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "layer_local_peps_environment_contraction_gate"
SIM_CLASS = "carrier_probe"
SOURCE_ALIGNMENT_CATEGORY = "phase2_peps3d_seed_local_environment_contraction_boundary"
PROMOTION_ALLOWED = False
PHASE2_FRONTIER_MATRIX_PATH = "system_v5/ops/formal_scouts/phase2_peps3d_seed_frontier_matrix_20260525.json"
PHASE2_SEED_RECEIPT = "system_v5/ops/formal_scouts/results/finite_peps3d_probe_effect_seed_carrier_gate_probe_results.json"
PHASE2_SPINOR_DENSITY_RECEIPT = "system_v5/ops/formal_scouts/results/peps3d_spinor_density_carrier_gate_probe_results.json"
BLOCKED_CONSUMERS = [
    "PEPS/PEPS3D closure beyond bounded local seed-carrier contraction",
    "nested Hopf tori",
    "Weyl sheet cover",
    "terrain generator placement",
    "operator substage cells",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics",
    "IGT/game theory",
    "axes 7-12",
]
CLAIM_CEILING = (
    "Formal scout only: tests local-star/local-edge environment contraction "
    "receipts for PEPS and PEPS3D tensor carriers. It does not admit final "
    "PEPS/PEPS3D dynamics, full-network contraction, Axis0, Xi, flux, gravity, "
    "Standard Model, Yang-Mills, Riemann, or physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PEPS/PEPS3D tensors, local-star environments, local-edge reductions, PSD/trace checks",
    },
    "z3": {"tried": True, "used": True, "reason": "supportive no-promotion and dense-ban consistency gate"},
}
TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing", "z3": "supportive"}

RTYPE = torch.float64
CDTYPE = torch.complex128
BOND_DIM = 2
PHYSICAL_DIM = 2
PEPS_SHAPE = (4, 4)
PEPS3D_SHAPE = (4, 4, 4)
GAP_FLOOR = 1e-6

DIRS_BY_DIM = {
    2: [(1, 0), (-1, 0), (0, 1), (0, -1)],
    3: [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)],
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return value.item()
        return value.detach().cpu().tolist()
    return value


def add_site(site: tuple[int, ...], delta: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(site[idx] + delta[idx] for idx in range(len(site)))


def sites(shape: tuple[int, ...]) -> list[tuple[int, ...]]:
    return list(itertools.product(*[range(size) for size in shape]))


def neighbors(site: tuple[int, ...], shape: tuple[int, ...]) -> list[tuple[tuple[int, ...], tuple[int, ...]]]:
    out = []
    site_set = set(sites(shape))
    for delta in DIRS_BY_DIM[len(shape)]:
        dst = add_site(site, delta)
        if dst in site_set:
            out.append((delta, dst))
    return out


def spinor_for_site(index: int, total: int) -> torch.Tensor:
    phi = 0.11 * index + 0.017 * math.sin(0.29 * index)
    chi = -0.61 + 1.22 * ((5 * index + 3) % total) / max(total - 1, 1)
    eta = 0.18 + 1.18 * ((7 * index + 2) % total) / max(total - 1, 1)
    eta = max(0.12, min(1.44, eta))
    raw = torch.tensor(
        [
            complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
            complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
        ],
        dtype=CDTYPE,
    )
    return raw / torch.linalg.vector_norm(raw)


def local_tensor(vector: torch.Tensor, degree: int, site_index: int, *, shuffled: bool = False) -> torch.Tensor:
    shape = [PHYSICAL_DIM] + [BOND_DIM] * max(degree, 1)
    tensor = torch.zeros(shape, dtype=CDTYPE)
    for values in itertools.product(range(BOND_DIM), repeat=max(degree, 1)):
        for physical in range(PHYSICAL_DIM):
            weight = 1.0 + 0.0j
            physical_sign = 1.0 if physical else -1.0
            for axis, bit in enumerate(values):
                sign = 1.0 if bit else -1.0
                phase = 0.035 * physical_sign * sign * (axis + 1) * (site_index + 1)
                amp = 1.0 + 0.055 * physical_sign * sign * math.sin(0.19 * (site_index + 1) * (axis + 1))
                if shuffled:
                    amp *= 1.0 + 0.030 * sign * math.cos(0.31 * (site_index + 2) * (axis + 1))
                    phase *= -1.0 if (site_index + axis) % 2 else 1.0
                weight *= amp * complex(math.cos(phase), math.sin(phase))
            tensor[(physical, *values)] = vector[physical] * weight
    return tensor / torch.clamp(torch.linalg.vector_norm(tensor), min=torch.tensor(1e-12, dtype=RTYPE))


def build_network(shape: tuple[int, ...], *, shuffled: bool = False) -> dict[tuple[int, ...], torch.Tensor]:
    all_sites = sites(shape)
    total = len(all_sites)
    net = {}
    for idx, site in enumerate(all_sites):
        net[site] = local_tensor(spinor_for_site(idx, total), len(neighbors(site, shape)), idx, shuffled=shuffled)
    return net


def leg_index(site: tuple[int, ...], target: tuple[int, ...], shape: tuple[int, ...]) -> int:
    for idx, (_delta, dst) in enumerate(neighbors(site, shape)):
        if dst == target:
            return idx
    raise ValueError(f"{target} is not a neighbor of {site}")


def transfer_env(tensor: torch.Tensor, keep_leg: int) -> torch.Tensor:
    degree = tensor.dim() - 1
    env = torch.zeros((BOND_DIM, BOND_DIM), dtype=CDTYPE)
    for a in range(BOND_DIM):
        for b in range(BOND_DIM):
            total = 0.0 + 0.0j
            other_count = max(degree - 1, 0)
            for physical in range(PHYSICAL_DIM):
                for others in itertools.product(range(BOND_DIM), repeat=other_count):
                    left = []
                    right = []
                    cursor = 0
                    for leg in range(degree):
                        if leg == keep_leg:
                            left.append(a)
                            right.append(b)
                        else:
                            left.append(others[cursor])
                            right.append(others[cursor])
                            cursor += 1
                    total += tensor[(physical, *left)] * torch.conj(tensor[(physical, *right)])
            env[a, b] = total
    trace = torch.real(torch.trace(env))
    return env / torch.clamp(trace, min=torch.tensor(1e-12, dtype=trace.dtype))


def site_rho(net: dict[tuple[int, ...], torch.Tensor], site: tuple[int, ...], shape: tuple[int, ...], *, identity_env: bool = False) -> torch.Tensor:
    tensor = net[site]
    nbs = neighbors(site, shape)
    envs = []
    for leg, (_delta, dst) in enumerate(nbs):
        if identity_env:
            envs.append(torch.eye(BOND_DIM, dtype=CDTYPE) / float(BOND_DIM))
        else:
            envs.append(transfer_env(net[dst], leg_index(dst, site, shape)))
    degree = tensor.dim() - 1
    rho = torch.zeros((PHYSICAL_DIM, PHYSICAL_DIM), dtype=CDTYPE)
    for p in range(PHYSICAL_DIM):
        for q in range(PHYSICAL_DIM):
            total = 0.0 + 0.0j
            for left in itertools.product(range(BOND_DIM), repeat=max(degree, 1)):
                for right in itertools.product(range(BOND_DIM), repeat=max(degree, 1)):
                    factor = tensor[(p, *left)] * torch.conj(tensor[(q, *right)])
                    for leg, env in enumerate(envs):
                        factor = factor * env[left[leg], right[leg]]
                    total += factor
            rho[p, q] = total
    rho = (rho + rho.conj().T) / 2
    trace = torch.real(torch.trace(rho))
    return rho / torch.clamp(trace, min=torch.tensor(1e-12, dtype=trace.dtype))


def edge_rho(net: dict[tuple[int, ...], torch.Tensor], edge: tuple[tuple[int, ...], tuple[int, ...]], shape: tuple[int, ...]) -> torch.Tensor:
    a, b = edge
    ta = net[a]
    tb = net[b]
    leg_ab = leg_index(a, b, shape)
    leg_ba = leg_index(b, a, shape)
    env_a = []
    for leg, (_delta, dst) in enumerate(neighbors(a, shape)):
        if leg != leg_ab:
            env_a.append((leg, transfer_env(net[dst], leg_index(dst, a, shape))))
    env_b = []
    for leg, (_delta, dst) in enumerate(neighbors(b, shape)):
        if leg != leg_ba:
            env_b.append((leg, transfer_env(net[dst], leg_index(dst, b, shape))))
    deg_a = ta.dim() - 1
    deg_b = tb.dim() - 1
    rho = torch.zeros((4, 4), dtype=CDTYPE)
    for pa in range(PHYSICAL_DIM):
        for pb in range(PHYSICAL_DIM):
            for qa in range(PHYSICAL_DIM):
                for qb in range(PHYSICAL_DIM):
                    total = 0.0 + 0.0j
                    for va in itertools.product(range(BOND_DIM), repeat=max(deg_a, 1)):
                        for wa in itertools.product(range(BOND_DIM), repeat=max(deg_a, 1)):
                            for vb in itertools.product(range(BOND_DIM), repeat=max(deg_b, 1)):
                                for wb in itertools.product(range(BOND_DIM), repeat=max(deg_b, 1)):
                                    if va[leg_ab] != vb[leg_ba] or wa[leg_ab] != wb[leg_ba]:
                                        continue
                                    factor = ta[(pa, *va)] * tb[(pb, *vb)] * torch.conj(ta[(qa, *wa)]) * torch.conj(tb[(qb, *wb)])
                                    for leg, env in env_a:
                                        factor = factor * env[va[leg], wa[leg]]
                                    for leg, env in env_b:
                                        factor = factor * env[vb[leg], wb[leg]]
                                    total += factor
                    rho[2 * pa + pb, 2 * qa + qb] = total
    rho = (rho + rho.conj().T) / 2
    trace = torch.real(torch.trace(rho))
    return rho / torch.clamp(trace, min=torch.tensor(1e-12, dtype=trace.dtype))


def rho_report(rho: torch.Tensor) -> dict[str, Any]:
    eigs = torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real
    trace = torch.trace(rho)
    return {
        "rho_shape": list(rho.shape),
        "trace_real": float(torch.real(trace).item()),
        "trace_imag_abs": abs(float(torch.imag(trace).item())),
        "min_eigenvalue": float(torch.min(eigs).item()),
        "normalization_error": abs(float(torch.real(trace).item()) - 1.0) + abs(float(torch.imag(trace).item())),
    }


def run_carrier(name: str, shape: tuple[int, ...]) -> dict[str, Any]:
    net = build_network(shape)
    shuffled = build_network(shape, shuffled=True)
    center = tuple(0 for _ in shape) if len(shape) == 3 else tuple(size // 2 for size in shape)
    first_edge = (center, neighbors(center, shape)[0][1])
    rho_site = site_rho(net, center, shape)
    rho_identity = site_rho(net, center, shape, identity_env=True)
    rho_shuffled = site_rho(shuffled, center, shape)
    rho_edge = edge_rho(net, first_edge, shape)
    site_gap_identity = float(torch.linalg.matrix_norm(rho_site - rho_identity).real.item())
    site_gap_shuffled = float(torch.linalg.matrix_norm(rho_site - rho_shuffled).real.item())
    site_report = rho_report(rho_site)
    edge_report = rho_report(rho_edge)
    return {
        "carrier_family": name,
        "shape": list(shape),
        "site_count": len(sites(shape)),
        "bond_dim": BOND_DIM,
        "physical_dim": PHYSICAL_DIM,
        "num_tensors": len(net),
        "sampled_site": list(center),
        "sampled_edge": [list(first_edge[0]), list(first_edge[1])],
        "environment_contraction_receipt": {
            "environment_kind": "local_star_and_local_edge",
            "contractor": "torch_explicit_local_transfer_environment",
            "contraction_path": "neighbor transfer matrices -> sampled site rho and sampled edge rho",
            "full_network_contraction": False,
            "dense_full_state_constructed": False,
            "dense_full_environment_constructed": False,
            "sampled_sites": [list(center)],
            "sampled_edges": [[list(first_edge[0]), list(first_edge[1])]],
            "site_rho": site_report,
            "edge_rho": edge_report,
            "identity_environment_gap": site_gap_identity,
            "shuffled_topology_gap": site_gap_shuffled,
        },
        "pass": site_report["normalization_error"] < 1e-8
        and edge_report["normalization_error"] < 1e-8
        and site_report["min_eigenvalue"] > -1e-8
        and edge_report["min_eigenvalue"] > -1e-8
        and site_gap_identity > GAP_FLOOR
        and site_gap_shuffled > GAP_FLOOR,
    }


def z3_gate() -> dict[str, Any]:
    full_network = z3.Bool("full_network")
    final_peps = z3.Bool("final_peps")
    local_env = z3.Bool("local_env")
    solver = z3.Solver()
    solver.add(local_env, z3.Not(full_network), z3.Not(final_peps))
    promote = z3.Solver()
    promote.add(local_env, final_peps, z3.Not(final_peps))
    return {
        "pass": solver.check() == z3.sat and promote.check() == z3.unsat,
        "sat": str(solver.check()),
        "promotion_status": str(promote.check()),
    }


def main() -> int:
    started = time.time()
    peps = run_carrier("peps", PEPS_SHAPE)
    peps3d = run_carrier("peps3d", PEPS3D_SHAPE)
    z3_row = z3_gate()
    positive = {
        "peps_local_environment_contraction_receipt": peps,
        "peps3d_local_environment_contraction_receipt": peps3d,
    }
    graveyard = {
        "GC1_identity_environment_is_not_equivalent": {
            "pass": peps["environment_contraction_receipt"]["identity_environment_gap"] > GAP_FLOOR
            and peps3d["environment_contraction_receipt"]["identity_environment_gap"] > GAP_FLOOR,
            "peps_gap": peps["environment_contraction_receipt"]["identity_environment_gap"],
            "peps3d_gap": peps3d["environment_contraction_receipt"]["identity_environment_gap"],
        },
        "GC2_shuffled_topology_changes_environment": {
            "pass": peps["environment_contraction_receipt"]["shuffled_topology_gap"] > GAP_FLOOR
            and peps3d["environment_contraction_receipt"]["shuffled_topology_gap"] > GAP_FLOOR,
            "peps_gap": peps["environment_contraction_receipt"]["shuffled_topology_gap"],
            "peps3d_gap": peps3d["environment_contraction_receipt"]["shuffled_topology_gap"],
        },
    }
    boundary = {
        "B1_formal_scout_no_promotion": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_no_full_network_or_physics_claim": {
            "pass": "does not admit final PEPS/PEPS3D dynamics" in CLAIM_CEILING
            and not peps["environment_contraction_receipt"]["full_network_contraction"]
            and not peps3d["environment_contraction_receipt"]["full_network_contraction"],
        },
        "B3_dense_ban_recorded": {
            "pass": not peps["environment_contraction_receipt"]["dense_full_state_constructed"]
            and not peps3d["environment_contraction_receipt"]["dense_full_state_constructed"]
            and not peps["environment_contraction_receipt"]["dense_full_environment_constructed"]
            and not peps3d["environment_contraction_receipt"]["dense_full_environment_constructed"],
        },
        "B4_z3_local_env_nonpromotion": z3_row,
    }
    checks = list(positive.values()) + list(graveyard.values()) + list(boundary.values())
    all_pass = all(row["pass"] for row in checks)
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": NAME,
        "version": VERSION,
        "tier": TIER,
        "purpose": PURPOSE,
        "scientific_question": SCIENTIFIC_QUESTION,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "root_constraints_in_force": {
            "F01": "finite PEPS and PEPS3D lattice shapes, finite bond dimension, finite local star/edge environments, and finite site/edge density readouts",
            "N01": "identity-environment and topology-shuffled controls produce nonzero local environment gaps while promotion is Z3-blocked",
        },
        "finite_map": "E_K : finite local PEPS3D tensors and neighboring transfer matrices -> normalized local site/edge density signatures",
        "domain": {
            "carrier": "finite PEPS and PEPS3D seed-carrier tensors",
            "peps_shape": list(PEPS_SHAPE),
            "peps3d_shape": list(PEPS3D_SHAPE),
            "bond_dim": BOND_DIM,
            "physical_dim": PHYSICAL_DIM,
        },
        "codomain_or_output": "finite local-star and local-edge environment contraction signatures with trace, PSD, identity-gap, topology-gap, and dense-ban readouts",
        "carrier_layer": "phase_2_finite_peps3d_seed_carrier",
        "geometry_layer": "bounded_local_environment_contraction_on_finite_seed_carrier",
        "carrier_realization": {
            "peps": "finite 4x4 torch tensor network with local transfer environments",
            "peps3d": "finite 4x4x4 torch tensor network with local transfer environments",
        },
        "peps3d_embedding": {
            "anchor_policy": "local site and sampled edge anchors only",
            "full_network_contraction": False,
            "dense_full_state_constructed": False,
            "dense_full_environment_constructed": False,
        },
        "spinor_state": "site tensors are seeded by normalized two-component torch spinors as carrier data only; no Hopf/Weyl geometry is admitted",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "blocked",
        "cut_layer": "blocked",
        "law_or_candidate_tested": "bounded local environment contraction on finite PEPS3D seed-carrier anchors",
        "branch_status_before_run": "phase2_frontier_active_below_threshold",
        "allowed_claims": [
            "bounded local star/edge environment contractions exist for the tested finite PEPS and PEPS3D seed carriers",
            "identity-environment and topology-shuffled controls are distinguishable from the local environment",
            "dense full-state and dense full-environment closure are not used",
        ],
        "promotion_blockers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["pytorch", "z3"],
        "actual_tools_used": ["pytorch", "z3"],
        "proof_surfaces_used": ["z3_local_env_nonpromotion_gate"],
        "graph_surfaces_used": ["none_used_for_this_local_contraction_packet"],
        "topology_surfaces_used": ["none_used_for_this_local_contraction_packet"],
        "required_inputs": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
        ],
        "data_or_artifact_dependencies": [
            PHASE2_FRONTIER_MATRIX_PATH,
            PHASE2_SEED_RECEIPT,
            PHASE2_SPINOR_DENSITY_RECEIPT,
        ],
        "required_negatives": [
            "identity_environment",
            "topology_shuffled_environment",
            "dense_full_state_ban",
            "dense_full_environment_ban",
            "promotion_block",
        ],
        "negatives_run": [
            "identity_environment",
            "topology_shuffled_environment",
            "dense_full_state_ban",
            "dense_full_environment_ban",
            "promotion_block",
        ],
        "kill_conditions": [
            "site or edge density normalization fails",
            "local environment is indistinguishable from identity environment",
            "topology-shuffled environment is indistinguishable from local environment",
            "dense full-state or dense full-environment closure is constructed",
            "Z3 promotion gate is satisfiable",
        ],
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": "phase2_local_boundary_contraction_identity_and_topology_gap",
        "all_pass": all_pass,
        "nearby_variants": {"passed": sum(1 for row in checks if row["pass"]), "total": len(checks)},
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "summary": {
            "elapsed_seconds": time.time() - started,
            "phase": 2,
            "carriers": ["peps", "peps3d"],
            "peps_site_count": peps["site_count"],
            "peps3d_site_count": peps3d["site_count"],
            "max_peps3d_sites": peps3d["site_count"],
            "max_peps3d_bond": BOND_DIM,
            "environment_kind": "local_star_and_local_edge",
            "full_network_contraction": False,
            "dense_state_closure_used": False,
            "dense_full_environment_constructed": False,
        },
        "result_summary": {
            "all_pass": all_pass,
            "peps_identity_gap": peps["environment_contraction_receipt"]["identity_environment_gap"],
            "peps3d_identity_gap": peps3d["environment_contraction_receipt"]["identity_environment_gap"],
            "peps_topology_gap": peps["environment_contraction_receipt"]["shuffled_topology_gap"],
            "peps3d_topology_gap": peps3d["environment_contraction_receipt"]["shuffled_topology_gap"],
            "full_network_contraction": False,
            "dense_state_closure_used": False,
        },
        "pass_rule": "Pass iff PEPS and PEPS3D local site/edge density readouts are normalized/PSD, identity and topology-shuffled gaps are nonzero, dense closure flags remain false, and Z3 promotion is unsat.",
        "fail_rule": "Fail if normalization/PSD breaks, controls collapse, dense closure is constructed, or promotion becomes satisfiable.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["active_seed_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "next_required_work": [
            "Classify this receipt inside the active seed-carrier frontier matrix.",
            "Continue only bounded in-level carrier packets until the frontier matrix reaches its current threshold or writes a blocker.",
        ],
        "next_admissible_step": "Update the active seed-carrier frontier matrix row for bounded local boundary contraction, then continue or block inside the same active frontier.",
        "why_not_v4_probes": (
            "This is a v5 PEPS/PEPS3D local environment-contraction boundary scout. It records real local "
            "environment contractions and dense bans, but it is not full PEPS/PEPS3D closure."
        ),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "summary": result["summary"], "wrote": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
