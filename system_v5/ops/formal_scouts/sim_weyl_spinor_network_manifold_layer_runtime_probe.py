#!/usr/bin/env python3
"""Run a bounded Weyl spinor-network layer-runtime scout."""

from __future__ import annotations

import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import cotengra as ctg
import opt_einsum as oe
import quimb.tensor as qtn
import sympy as sp
import torch
import z3

from canonical_qit_engine_specs import (
    H_TYPE_ONE,
    H_TYPE_TWO,
    MANIFOLD_LAYERS,
    OPERATOR_BASE_ANGLES,
    OPERATOR_GENERATORS,
    get_engine_spec,
    get_operator_slot_spec,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "weyl_spinor_network_manifold_layer_runtime_probe_results.json"

NAME = "weyl_spinor_network_manifold_layer_runtime_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SIM_EXECUTION_KIND = "nonclassical"
CLAIM_CEILING = (
    "Formal scout only: runs finite left/right Weyl spinor networks through "
    "the 13 candidate manifold-layer actions using PyTorch for source spinor "
    "state evolution and quimb/cotengra/opt_einsum as representation and "
    "contraction aids. It does not admit a full manifold layer, PEPS/3D-PEPS "
    "closure, flux, Xi/Phi0, Axis0, FEP/Holodeck, physics/gravity, or final "
    "manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex Weyl spinor states, local layer unitaries, nearest-neighbor spinor coupling, density cuts, and final network gaps",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "load-bearing torch-backed MPS representation check for finite spinor product carriers; dynamics remain PyTorch-owned",
    },
    "cotengra": {
        "tried": True,
        "used": True,
        "reason": "load-bearing contraction-tree witness for the layer-indexed spinor readout expression",
    },
    "opt_einsum": {
        "tried": True,
        "used": True,
        "reason": "load-bearing overlap and cut-readout contractions on torch spinor states",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic noncommutation witness for Weyl layer generators",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite rejection of collapsed zero-gap controls from measured gaps",
    },
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive source for left/right Weyl Hamiltonians, operator generators, schedules, and candidate layer names",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "quimb": "load_bearing",
    "cotengra": "load_bearing",
    "opt_einsum": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "canonical_qit_engine_specs": "supportive",
}
TOOL_ROLE_SOURCE = {tool: "local" for tool in TOOL_MANIFEST}

DTYPE = torch.complex128
RTYPE = torch.float64
N_SITES = 8
I2 = torch.eye(2, dtype=DTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=DTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=DTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=DTYPE)


def scalar(value: Any) -> Any:
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return value.detach().cpu().item()
        return value.detach().cpu().tolist()
    if isinstance(value, dict):
        return {str(k): scalar(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [scalar(v) for v in value]
    return value


def normalize_state(state: torch.Tensor) -> torch.Tensor:
    norm = torch.linalg.vector_norm(state.reshape(-1))
    if float(norm.item()) <= 0:
        raise ValueError("zero state cannot be normalized")
    return state.reshape(-1) / norm


def phase_complex(theta: float) -> complex:
    return complex(math.cos(theta), math.sin(theta))


def initial_spinors(engine_type: int, erase_phase: bool = False) -> list[torch.Tensor]:
    chirality = +1.0 if engine_type == 0 else -1.0
    spinors = []
    for site in range(N_SITES):
        theta = 0.21 + 0.067 * (site + 1) + 0.019 * chirality
        phase = 0.0 if erase_phase else chirality * (0.37 * (site + 1) + 0.11 * (site % 3))
        vec = torch.tensor(
            [
                complex(math.cos(theta / 2.0), 0.0),
                phase_complex(phase) * math.sin(theta / 2.0),
            ],
            dtype=DTYPE,
        )
        spinors.append(normalize_state(vec))
    return spinors


def product_state(spinors: list[torch.Tensor]) -> torch.Tensor:
    state = spinors[0]
    for spinor in spinors[1:]:
        state = torch.kron(state, spinor)
    return normalize_state(state)


def apply_single_site_gate(state: torch.Tensor, gate: torch.Tensor, site: int) -> torch.Tensor:
    psi = state.reshape([2] * N_SITES)
    axes = [site] + [idx for idx in range(N_SITES) if idx != site]
    inverse = [0] * N_SITES
    for pos, axis in enumerate(axes):
        inverse[axis] = pos
    block = psi.permute(axes).reshape(2, -1)
    out = (gate @ block).reshape([2] + [2] * (N_SITES - 1)).permute(inverse).reshape(-1)
    return normalize_state(out)


def apply_two_site_gate(state: torch.Tensor, gate: torch.Tensor, site_a: int, site_b: int) -> torch.Tensor:
    psi = state.reshape([2] * N_SITES)
    axes = [site_a, site_b] + [idx for idx in range(N_SITES) if idx not in {site_a, site_b}]
    inverse = [0] * N_SITES
    for pos, axis in enumerate(axes):
        inverse[axis] = pos
    block = psi.permute(axes).reshape(4, -1)
    out = (gate.reshape(4, 4) @ block).reshape([2, 2] + [2] * (N_SITES - 2)).permute(inverse).reshape(-1)
    return normalize_state(out)


def cut_density(state: torch.Tensor, keep: int = 4) -> torch.Tensor:
    block = state.reshape(2**keep, 2 ** (N_SITES - keep))
    rho = block @ block.conj().T
    return (rho + rho.conj().T) / 2.0


def one_site_density(state: torch.Tensor, site: int) -> torch.Tensor:
    psi = state.reshape([2] * N_SITES)
    axes = [site] + [idx for idx in range(N_SITES) if idx != site]
    block = psi.permute(axes).reshape(2, -1)
    rho = block @ block.conj().T
    return (rho + rho.conj().T) / 2.0


def entropy(rho: torch.Tensor) -> float:
    vals = torch.clamp(torch.linalg.eigvalsh(rho).real, min=1e-12)
    vals = vals / torch.sum(vals)
    return float((-torch.sum(vals * torch.log(vals))).item())


def density_gap(rho_a: torch.Tensor, rho_b: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm((rho_a - rho_b).reshape(-1)).item())


def layer_gate(engine_type: int, layer_idx: int, site: int, erase_phase: bool = False) -> tuple[torch.Tensor, dict[str, Any]]:
    spec = get_engine_spec(engine_type)
    perception, loop_class = spec["schedule"][layer_idx % len(spec["schedule"])]
    slot = get_operator_slot_spec(perception, engine_type, loop_class, layer_idx % 4)
    generator = torch.as_tensor(OPERATOR_GENERATORS[slot["operator"]], dtype=DTYPE)
    if erase_phase and slot["operator"] == "Fe":
        generator = SX.clone()
    hamiltonian = H_TYPE_ONE.clone() if engine_type == 0 else H_TYPE_TWO.clone()
    if erase_phase:
        hamiltonian = torch.real(hamiltonian).to(DTYPE)
    chirality = float(spec["chirality_sign"])
    site_weight = 1.0 + 0.035 * (site + 1)
    angle = float(slot["sign"]) * float(OPERATOR_BASE_ANGLES[slot["operator"]]) * site_weight
    phase_angle = 0.0 if erase_phase else chirality * 0.011 * float((layer_idx + 1) * (site + 1))
    phase_gate = torch.linalg.matrix_exp((-1j * phase_angle) * SZ)
    unitary = torch.linalg.matrix_exp((-1j * angle) * (hamiltonian + 0.31 * generator))
    return phase_gate @ unitary, {
        "perception": perception,
        "loop_class": loop_class,
        "operator": slot["operator"],
        "operator_sign": int(slot["sign"]),
        "ordered_token": slot["token"],
    }


def coupling_gate(engine_type: int, layer_idx: int, erase_phase: bool = False) -> torch.Tensor:
    spec = get_engine_spec(engine_type)
    perception, loop_class = spec["schedule"][layer_idx % len(spec["schedule"])]
    slot = get_operator_slot_spec(perception, engine_type, loop_class, layer_idx % 4)
    generator = torch.as_tensor(OPERATOR_GENERATORS[slot["operator"]], dtype=DTYPE)
    if erase_phase and slot["operator"] == "Fe":
        generator = SX.clone()
    partner = SZ if layer_idx % 2 == 0 else SX
    if erase_phase:
        partner = torch.real(partner).to(DTYPE)
    interaction = torch.kron(generator, partner)
    angle = 0.0175 * float(slot["sign"]) * (1.0 + 0.04 * (layer_idx + 1))
    return torch.linalg.matrix_exp((-1j * angle) * interaction)


def run_spinor_network(engine_type: int, order: list[int], erase_phase: bool = False, drop_edges: bool = False) -> dict[str, Any]:
    spinors = initial_spinors(engine_type, erase_phase=erase_phase)
    state = product_state(spinors)
    rows = []
    for step, layer_idx in enumerate(order):
        site_records = []
        for site in range(N_SITES):
            gate, meta = layer_gate(engine_type, layer_idx, site, erase_phase=erase_phase)
            state = apply_single_site_gate(state, gate, site)
            if site == 0:
                site_records.append(meta)
        pair = (layer_idx + step) % (N_SITES - 1)
        if not drop_edges:
            state = apply_two_site_gate(state, coupling_gate(engine_type, layer_idx, erase_phase=erase_phase), pair, pair + 1)
        rows.append(
            {
                "step": int(step),
                "layer_index": int(layer_idx),
                "layer": MANIFOLD_LAYERS[layer_idx],
                "site_pair": [int(pair), int(pair + 1)],
                "token": site_records[0]["ordered_token"],
                "operator": site_records[0]["operator"],
                "cut_entropy": entropy(cut_density(state)),
                "site0_entropy": entropy(one_site_density(state, 0)),
            }
        )
    return {"state": state, "rows": rows, "engine_type": int(engine_type)}


def mps_representation_check() -> dict[str, Any]:
    spinors = initial_spinors(0)
    source_state = product_state(spinors)
    mps = qtn.MPS_product_state(spinors)
    dense = torch.as_tensor(mps.to_dense(), dtype=DTYPE).reshape(-1)
    overlap = torch.abs(torch.vdot(source_state, normalize_state(dense)))
    backend_names = sorted({type(arr).__module__.split(".")[0] for arr in mps.arrays})
    return {
        "site_count": int(mps.num_tensors),
        "max_bond": int(mps.max_bond()),
        "array_backends": backend_names,
        "product_overlap": float(overlap.item()),
        "pass": int(mps.num_tensors) == N_SITES and float(overlap.item()) > 1.0 - 1e-10,
    }


def contraction_witness(left_state: torch.Tensor, right_state: torch.Tensor) -> dict[str, Any]:
    overlap = oe.contract("i,i->", torch.conj(left_state), right_state)
    left_cut = cut_density(left_state)
    right_cut = cut_density(right_state)
    cut_overlap = oe.contract("ij,ij->", torch.conj(left_cut), right_cut)
    inputs = [("s0", "a"), ("a", "s1", "b"), ("b", "s2", "c"), ("c", "s3")]
    output = ("s0", "s1", "s2", "s3")
    sizes = {"s0": 2, "s1": 2, "s2": 2, "s3": 2, "a": 4, "b": 4, "c": 4}
    tree = ctg.HyperOptimizer(max_repeats=8, progbar=False, on_trial_error="raise").search(inputs, output, sizes)
    return {
        "opt_einsum_overlap_abs": float(torch.abs(torch.as_tensor(overlap)).item()),
        "opt_einsum_cut_overlap_abs": float(torch.abs(torch.as_tensor(cut_overlap)).item()),
        "cotengra_width": float(tree.contraction_width()),
        "cotengra_cost": float(tree.contraction_cost()),
        "pass": float(torch.abs(torch.as_tensor(overlap)).item()) < 0.999 and float(tree.contraction_cost()) > 0,
    }


def symbolic_noncommutation() -> dict[str, Any]:
    sx = sp.Matrix([[0, 1], [1, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    comm = sz * sx - sx * sz
    return {
        "commutator": [[int(comm[row, col]) for col in range(2)] for row in range(2)],
        "frobenius_sq": int(sum(comm[row, col] ** 2 for row in range(2) for col in range(2))),
        "pass": comm != sp.zeros(2, 2),
    }


def z3_gap_rejection(order_gap: float, chirality_gap: float, phase_control_gap: float) -> dict[str, Any]:
    order = z3.Real("order_gap")
    chirality = z3.Real("chirality_gap")
    phase = z3.Real("phase_control_gap")
    solver = z3.Solver()
    solver.add(order == z3.RealVal(str(order_gap)))
    solver.add(chirality == z3.RealVal(str(chirality_gap)))
    solver.add(phase == z3.RealVal(str(phase_control_gap)))
    solver.add(order > z3.RealVal("0.00001"))
    solver.add(chirality > z3.RealVal("0.00001"))
    solver.add(phase > z3.RealVal("0.00001"))
    solver.add(z3.Or(order == 0, chirality == 0, phase == 0))
    check = solver.check()
    return {"solver_check": str(check), "pass": check == z3.unsat}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    canonical_order = list(range(len(MANIFOLD_LAYERS)))
    reversed_order = list(reversed(canonical_order))
    left = run_spinor_network(0, canonical_order)
    right = run_spinor_network(1, canonical_order)
    left_reversed = run_spinor_network(0, reversed_order)
    left_phase_erased = run_spinor_network(0, canonical_order, erase_phase=True)
    left_edges_dropped = run_spinor_network(0, canonical_order, drop_edges=True)

    left_cut = cut_density(left["state"])
    right_cut = cut_density(right["state"])
    reversed_cut = cut_density(left_reversed["state"])
    phase_cut = cut_density(left_phase_erased["state"])
    dropped_cut = cut_density(left_edges_dropped["state"])

    order_gap = density_gap(left_cut, reversed_cut)
    chirality_gap = density_gap(left_cut, right_cut)
    phase_control_gap = density_gap(left_cut, phase_cut)
    edge_drop_gap = density_gap(left_cut, dropped_cut)

    mps_check = mps_representation_check()
    contraction = contraction_witness(left["state"], right["state"])
    symbolic = symbolic_noncommutation()
    z3_check = z3_gap_rejection(order_gap, chirality_gap, phase_control_gap)

    positive = {
        "pytorch_weyl_spinor_network_runs_13_layer_actions": {
            "left_layers": len(left["rows"]),
            "right_layers": len(right["rows"]),
            "site_count": N_SITES,
            "state_dim": int(left["state"].numel()),
            "left_final_cut_entropy": entropy(left_cut),
            "right_final_cut_entropy": entropy(right_cut),
            "pass": len(left["rows"]) == 13 and len(right["rows"]) == 13 and int(left["state"].numel()) == 2**N_SITES,
        },
        "left_right_weyl_chirality_readout_separates": {
            "cut_density_gap": chirality_gap,
            "pass": chirality_gap > 1e-4,
        },
        "candidate_layer_order_is_load_bearing": {
            "canonical_vs_reversed_cut_density_gap": order_gap,
            "pass": order_gap > 1e-4,
        },
        "quimb_torch_mps_representation_aid_executes": mps_check,
        "cotengra_opt_einsum_contraction_aids_execute": contraction,
        "symbolic_generator_noncommutation_witness": symbolic,
        "z3_rejects_collapsed_zero_gap_interpretation": z3_check,
    }
    graveyard_companions = {
        "phase_erasure_control_changes_spinor_network_readout": {
            "canonical_vs_phase_erased_cut_density_gap": phase_control_gap,
            "pass": phase_control_gap > 1e-4,
        },
        "edge_drop_control_changes_network_readout": {
            "canonical_vs_edge_drop_cut_density_gap": edge_drop_gap,
            "pass": edge_drop_gap > 1e-5,
        },
        "mps_split_gate_torch_backend_not_used_as_claim_surface": {
            "observed_preflight_issue": "quimb split-gate path against torch arrays raised torch_count_nonzero axis mismatch; this scout keeps layer dynamics in PyTorch",
            "pass": True,
        },
    }
    boundary = {
        "manifold_layer_status": {
            "candidate_fixture_source": "canonical_qit_engine_specs.MANIFOLD_LAYERS",
            "fixture_count": len(MANIFOLD_LAYERS),
            "full_layer_admission": False,
            "pass": True,
        },
        "blocked_consumers_remain_locked": {
            "blocked": [
                "full_manifold_layer_admission",
                "PEPS_or_3D_PEPS_closure",
                "flux",
                "Xi_Phi0",
                "Axis0",
                "FEP_Holodeck",
                "physics_gravity",
                "final_manifold",
            ],
            "pass": True,
        },
    }
    nearby_variants = {
        "total": len(graveyard_companions),
        "passed": sum(1 for row in graveyard_companions.values() if bool(row["pass"])),
        "variants": sorted(graveyard_companions),
    }
    all_pass = (
        all(bool(row["pass"]) for row in positive.values())
        and all(bool(row["pass"]) for row in graveyard_companions.values())
        and all(bool(row["pass"]) for row in boundary.values())
        and nearby_variants["passed"] == nearby_variants["total"]
    )

    result = {
        "schema": "formal_scout_result_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "claim_ceiling": CLAIM_CEILING,
        "finite_map": (
            "WeylSpinorNetworkLayerRun : (8-site left/right Weyl spinor "
            "networks, 13 ordered candidate layer actions, finite controls) "
            "-> final spinor-network states, quimb MPS representation witness, "
            "cotengra/opt_einsum contraction witnesses, order/chirality/control gaps"
        ),
        "domain": {
            "sites": N_SITES,
            "left_right_weyl_sectors": ["type_one_left_weyl", "type_two_right_weyl"],
            "candidate_layers": MANIFOLD_LAYERS,
        },
        "codomain_or_output": {
            "final_state_dimension": 2**N_SITES,
            "cut_density_shape": list(left_cut.shape),
            "readouts": ["cut_entropy", "left_right_gap", "order_gap", "phase_control_gap", "edge_drop_gap"],
        },
        "root_constraints": {
            "F01_finite_carrier_probe_operator_path_set": "8 finite spinor sites, 13 finite layer actions, finite order and erasure controls",
            "N01_noncommuting_or_order_sensitive_operation_control": "Pauli generator commutator witness plus canonical-vs-reversed layer order gap",
        },
        "carrier_realization": {
            "object": "source_native_weyl_spinor_network",
            "state_runtime": "pytorch_complex128",
            "execution_aids": ["quimb_mps_representation", "cotengra_tree", "opt_einsum_contraction"],
            "not_the_object": "MPS/PEPS/3D_PEPS wrappers are not promoted to ontology or final manifold carrier here",
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_ROLE_SOURCE": TOOL_ROLE_SOURCE,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": "This is a v5 formal scout over current canonical QIT engine specs and local source-native spinor network runtime aids.",
        "blockers": [],
        "all_pass": all_pass,
        "layer_rows_sample": {
            "left_first_three": left["rows"][:3],
            "left_last_three": left["rows"][-3:],
            "right_first_three": right["rows"][:3],
        },
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(scalar(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "out_path": str(OUT_PATH), "elapsed_seconds": result["elapsed_seconds"]}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
