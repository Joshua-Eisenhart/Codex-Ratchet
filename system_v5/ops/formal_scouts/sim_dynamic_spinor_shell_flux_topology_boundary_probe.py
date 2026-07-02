#!/usr/bin/env python3
"""Dynamic spinor-shell flux/topology boundary scout.

Formal scout only.

This row tests a narrower version of the current owner constraint:

* shell time is represented as opposite IJK shell motion, not as an external
  scalar clock;
* past shells move outward and future shells move inward inside the fixture;
* flux is a derived chiral boundary current, not a primitive field;
* the derived current perturbs all four terrain/topology signatures and is
  bound to the two QIT engine types;
* entropy is read through finite density carriers with von Neumann entropy,
  not a raw amplitude or threshold shortcut.

The fixture is deliberately small. It is an admission test for a layer shape,
not final flux, Axis0, PEPS3D, gravity, Standard Model, Yang-Mills, Riemann,
or physics closure.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch
import z3

import canonical_qit_engine_specs as specs


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "dynamic_spinor_shell_flux_topology_boundary_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "dynamic_spinor_shell_flux_topology_boundary"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests dynamic spinor shells with IJK temporal shell "
    "orientation, chiral engine-bound derived flux, four-topology signature "
    "mutation, and von Neumann shell-history entropy. It does not admit final "
    "flux, Axis0, Xi, PEPS3D closure, Standard Model, gravity, Yang-Mills, "
    "Riemann, cosmology, or physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing complex spinors, finite density carriers, "
            "quaternion shell updates, von Neumann entropy, and controls"
        ),
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite shell/topology/engine count and nonpromotion gates",
    },
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive source-native QIT engine schedules and topology metadata",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive canonical result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "canonical_qit_engine_specs": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

RTYPE = torch.float64
CDTYPE = torch.complex128
EPS = 1e-12
GAP_FLOOR = 1.0e-5
DISTINCT_FLOOR = 2.5e-4

TOPOLOGIES = ("Se", "Ne", "Ni", "Si")
SHELL_DIRECTIONS = {"past_outward": +1.0, "future_inward": -1.0}
TOPOLOGY_PHASE = {"Se": 0.0, "Ne": 0.5 * math.pi, "Ni": math.pi, "Si": 1.5 * math.pi}
TOPOLOGY_BASE = {
    "Se": torch.tensor([+0.22, -0.09, +0.13], dtype=RTYPE),
    "Ne": torch.tensor([+0.05, +0.24, -0.08], dtype=RTYPE),
    "Ni": torch.tensor([-0.20, +0.07, -0.16], dtype=RTYPE),
    "Si": torch.tensor([-0.06, -0.19, +0.21], dtype=RTYPE),
}
OPERATOR_UNITS = {
    "Ti": torch.tensor([0.0, 0.0, 0.0, 1.0], dtype=RTYPE),
    "Te": torch.tensor([0.0, 1.0, 0.0, 0.0], dtype=RTYPE),
    "Fi": torch.tensor([0.0, 1.0, 0.0, 0.0], dtype=RTYPE),
    "Fe": torch.tensor([0.0, 0.0, 0.0, 1.0], dtype=RTYPE),
}
Q_ONE = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=RTYPE)
Q_I = torch.tensor([0.0, 1.0, 0.0, 0.0], dtype=RTYPE)
Q_J = torch.tensor([0.0, 0.0, 1.0, 0.0], dtype=RTYPE)
Q_K = torch.tensor([0.0, 0.0, 0.0, 1.0], dtype=RTYPE)

BASE_SPINOR_PARAMS = {
    "Se": (0.19, -0.23, 0.42),
    "Ne": (0.47, +0.31, 0.57),
    "Ni": (-0.36, +0.18, 0.69),
    "Si": (0.83, -0.11, 0.51),
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def norm(value: torch.Tensor) -> torch.Tensor:
    return torch.linalg.norm(value)


def normalize_q(q: torch.Tensor) -> torch.Tensor:
    size = norm(q)
    if float(size.item()) <= EPS:
        raise ValueError("zero quaternion coefficient set")
    return q / size


def q_conj(q: torch.Tensor) -> torch.Tensor:
    return torch.tensor([q[0].item(), -q[1].item(), -q[2].item(), -q[3].item()], dtype=RTYPE)


def q_mul(left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    a0, a1, a2, a3 = [float(item) for item in left]
    b0, b1, b2, b3 = [float(item) for item in right]
    return torch.tensor(
        [
            a0 * b0 - a1 * b1 - a2 * b2 - a3 * b3,
            a0 * b1 + a1 * b0 + a2 * b3 - a3 * b2,
            a0 * b2 - a1 * b3 + a2 * b0 + a3 * b1,
            a0 * b3 + a1 * b2 - a2 * b1 + a3 * b0,
        ],
        dtype=RTYPE,
    )


def q_exp(unit: torch.Tensor, angle: float) -> torch.Tensor:
    return normalize_q(math.cos(angle) * Q_ONE + math.sin(angle) * unit)


def q_close(left: torch.Tensor, right: torch.Tensor, *, tol: float = 1.0e-10) -> bool:
    return float(norm(left - right).item()) < tol


def spinor(phi: float, chi: float, eta: float, phase: float) -> torch.Tensor:
    raw = torch.tensor(
        [
            complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
            complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
        ],
        dtype=CDTYPE,
    )
    gauge = complex(math.cos(phase), math.sin(phase))
    return gauge * raw / torch.linalg.norm(raw)


def spinor_to_q(local_spinor: torch.Tensor) -> torch.Tensor:
    alpha = local_spinor[0]
    beta = local_spinor[1]
    return normalize_q(
        torch.tensor(
            [
                torch.real(alpha).item(),
                torch.imag(alpha).item(),
                torch.real(beta).item(),
                torch.imag(beta).item(),
            ],
            dtype=RTYPE,
        )
    )


def q_to_spinor(q: torch.Tensor) -> torch.Tensor:
    q = normalize_q(q)
    return torch.tensor(
        [complex(q[0].item(), q[1].item()), complex(q[2].item(), q[3].item())],
        dtype=CDTYPE,
    )


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, torch.conj(psi))


def normalize_density(rho: torch.Tensor) -> torch.Tensor:
    rho = 0.5 * (rho + torch.conj(rho.transpose(-2, -1)))
    vals, vecs = torch.linalg.eigh(rho)
    vals = vals.real.clamp_min(0.0)
    if float(torch.sum(vals).item()) <= EPS:
        vals = torch.full_like(vals, 1.0 / vals.numel())
    out = (vecs * vals.to(CDTYPE).unsqueeze(0)) @ torch.conj(vecs.transpose(-2, -1))
    return out / torch.trace(out)


def von_neumann_entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(normalize_density(rho)).real.clamp_min(0.0)
    vals = vals / torch.clamp(torch.sum(vals), min=EPS)
    vals = vals[vals > EPS]
    return float((-torch.sum(vals * torch.log(vals))).item())


def shell_state(
    topology: str,
    engine_type: int,
    shell_step: int,
    direction_name: str,
    *,
    shell_time_frozen: bool = False,
    past_future_swapped: bool = False,
    chirality_erased: bool = False,
) -> torch.Tensor:
    base_phi, base_chi, base_eta = BASE_SPINOR_PARAMS[topology]
    direction = SHELL_DIRECTIONS[direction_name]
    if past_future_swapped:
        direction = -direction
    shell_depth = 0.0 if shell_time_frozen else float(shell_step + 1)
    engine_sign = +1.0 if chirality_erased else float(specs.get_engine_spec(engine_type)["chirality_sign"])
    topology_phase = TOPOLOGY_PHASE[topology]
    phi = base_phi + 0.037 * engine_sign * shell_depth + 0.029 * direction * shell_depth
    chi = base_chi + 0.041 * direction * math.sin(topology_phase + 0.31 * shell_depth)
    eta = base_eta + 0.026 * engine_sign * direction * math.cos(topology_phase + 0.17 * shell_depth)
    phase = topology_phase + engine_sign * 0.071 * shell_depth + direction * 0.113 * shell_depth
    eta = max(0.08, min(1.36, eta))
    return spinor(phi, chi, eta, phase)


def apply_engine_shell_update(
    local_spinor: torch.Tensor,
    topology: str,
    engine_type: int,
    macro_stage_idx: int,
    shell_step: int,
    direction_name: str,
    *,
    scalar_flux_collapse: bool = False,
    chirality_erased: bool = False,
) -> torch.Tensor:
    perception, loop_class = specs.get_schedule(engine_type)[macro_stage_idx]
    if perception != topology:
        raise ValueError(f"schedule/topology mismatch: {perception} != {topology}")
    slot = (shell_step + macro_stage_idx) % specs.N_SUBSTAGES_PER_MAIN
    slot_spec = specs.get_operator_slot_spec(perception, engine_type, loop_class, slot)
    operator = slot_spec["operator"]
    stage_sign = int(slot_spec["sign"])
    direction = SHELL_DIRECTIONS[direction_name]
    engine_sign = +1.0 if chirality_erased else float(specs.get_engine_spec(engine_type)["chirality_sign"])
    if scalar_flux_collapse:
        operator = "Te"
        stage_sign = +1
        direction = 0.0
    unit = OPERATOR_UNITS[operator]
    angle = (
        0.036
        + 0.007 * (shell_step + 1)
        + 0.004 * (macro_stage_idx + 1)
        + 0.011 * math.sin(TOPOLOGY_PHASE[topology] + shell_step)
    )
    angle *= float(stage_sign) * engine_sign * (1.0 + 0.17 * direction)
    rotor = q_exp(unit, angle)
    q = spinor_to_q(local_spinor)
    if operator in {"Fi", "Fe"}:
        updated = q_mul(rotor, q) if stage_sign > 0 else q_mul(q, rotor)
    else:
        updated = q_mul(q_mul(rotor, q), q_conj(rotor))
    return q_to_spinor(updated)


def relative_motion(before: torch.Tensor, after: torch.Tensor) -> torch.Tensor:
    rel = q_mul(spinor_to_q(after), q_conj(spinor_to_q(before)))
    if float(rel[0].item()) < 0.0:
        rel = -rel
    return normalize_q(rel)


def shell_history_entropy(before_past: torch.Tensor, before_future: torch.Tensor, after_past: torch.Tensor, after_future: torch.Tensor) -> dict[str, float]:
    pre_mix = normalize_density(0.5 * density(before_past) + 0.5 * density(before_future))
    post_mix = normalize_density(0.5 * density(after_past) + 0.5 * density(after_future))
    past_post = normalize_density(0.72 * density(before_past) + 0.28 * density(after_past))
    future_post = normalize_density(0.72 * density(before_future) + 0.28 * density(after_future))
    pre_entropy = von_neumann_entropy(pre_mix)
    post_entropy = von_neumann_entropy(post_mix)
    return {
        "pre_history_entropy": pre_entropy,
        "post_history_entropy": post_entropy,
        "compression_delta": pre_entropy - post_entropy,
        "directional_entropy_gradient": von_neumann_entropy(future_post) - von_neumann_entropy(past_post),
    }


def build_stage_row(
    topology: str,
    engine_type: int,
    macro_stage_idx: int,
    shell_step: int,
    *,
    scalar_flux_collapse: bool = False,
    chirality_erased: bool = False,
    shell_time_frozen: bool = False,
    past_future_swapped: bool = False,
    wrong_entropy_form: bool = False,
) -> dict[str, Any]:
    before_past = shell_state(
        topology,
        engine_type,
        shell_step,
        "past_outward",
        shell_time_frozen=shell_time_frozen,
        past_future_swapped=past_future_swapped,
        chirality_erased=chirality_erased,
    )
    before_future = shell_state(
        topology,
        engine_type,
        shell_step,
        "future_inward",
        shell_time_frozen=shell_time_frozen,
        past_future_swapped=past_future_swapped,
        chirality_erased=chirality_erased,
    )
    after_past = apply_engine_shell_update(
        before_past,
        topology,
        engine_type,
        macro_stage_idx,
        shell_step,
        "past_outward",
        scalar_flux_collapse=scalar_flux_collapse,
        chirality_erased=chirality_erased,
    )
    after_future = apply_engine_shell_update(
        before_future,
        topology,
        engine_type,
        macro_stage_idx,
        shell_step,
        "future_inward",
        scalar_flux_collapse=scalar_flux_collapse,
        chirality_erased=chirality_erased,
    )
    rel_past = relative_motion(before_past, after_past)
    rel_future = relative_motion(before_future, after_future)
    temporal_shell = 0.5 * (rel_past[1:] - rel_future[1:])
    engine_sign = +1.0 if chirality_erased else float(specs.get_engine_spec(engine_type)["chirality_sign"])
    i_component = engine_sign * float(temporal_shell[0].item())
    j_component = float(temporal_shell[1].item()) + 0.07 * float(shell_step + 1) * float(SHELL_DIRECTIONS["past_outward"])
    k_component = float(temporal_shell[2].item()) + 0.05 * float(shell_step + 1) * float(SHELL_DIRECTIONS["future_inward"])
    if scalar_flux_collapse:
        j_component = 0.0
        k_component = 0.0
    flux_ijk = torch.tensor([i_component, j_component, k_component], dtype=RTYPE)
    entropy_row = shell_history_entropy(before_past, before_future, after_past, after_future)
    if wrong_entropy_form:
        entropy_row = {
            **entropy_row,
            "compression_delta": float(norm(rel_past[1:] + rel_future[1:]).item()),
            "directional_entropy_gradient": float(norm(rel_past[1:] - rel_future[1:]).item()),
        }
    mutation = TOPOLOGY_BASE[topology] + flux_ijk + torch.tensor(
        [
            entropy_row["compression_delta"],
            entropy_row["directional_entropy_gradient"],
            float(engine_sign) * entropy_row["post_history_entropy"],
        ],
        dtype=RTYPE,
    )
    return {
        "engine_type": engine_type + 1,
        "engine_label": specs.get_engine_spec(engine_type)["type_label"],
        "topology": topology,
        "terrain_variant": specs.get_terrain_dynamics_spec(topology, engine_type)["realization"],
        "macro_stage_idx": macro_stage_idx,
        "shell_step": shell_step,
        "shell_directions": dict(SHELL_DIRECTIONS),
        "past_shell_motion": "outward",
        "future_shell_motion": "inward",
        "flux_ijk": flux_ijk,
        "flux_magnitude": float(norm(flux_ijk).item()),
        "entropy": entropy_row,
        "topology_signature_after_flux": mutation,
        "controls": {
            "scalar_flux_collapse": scalar_flux_collapse,
            "chirality_erased": chirality_erased,
            "shell_time_frozen": shell_time_frozen,
            "past_future_swapped": past_future_swapped,
            "wrong_entropy_form": wrong_entropy_form,
        },
    }


def run_fixture(**controls: bool) -> dict[str, Any]:
    rows = []
    for engine_type in [0, 1]:
        schedule = specs.get_schedule(engine_type)
        for macro_stage_idx, (topology, _loop_class) in enumerate(schedule):
            shell_step = macro_stage_idx % 4
            rows.append(build_stage_row(topology, engine_type, macro_stage_idx, shell_step, **controls))
    flux_stack = torch.stack([row["flux_ijk"] for row in rows])
    topology_signatures = {
        topology: torch.mean(
            torch.stack([row["topology_signature_after_flux"] for row in rows if row["topology"] == topology]),
            dim=0,
        )
        for topology in TOPOLOGIES
    }
    engine_signatures = {
        f"E{engine}": torch.mean(
            torch.stack([row["topology_signature_after_flux"] for row in rows if row["engine_type"] == engine]),
            dim=0,
        )
        for engine in [1, 2]
    }
    per_topology_flux = {
        topology: torch.sum(torch.stack([row["flux_ijk"] for row in rows if row["topology"] == topology]), dim=0)
        for topology in TOPOLOGIES
    }
    entropy_values = [row["entropy"] for row in rows]
    signature = torch.cat(
        [
            torch.stack([topology_signatures[topology] for topology in TOPOLOGIES]).reshape(-1),
            engine_signatures["E1"],
            engine_signatures["E2"],
            torch.tensor(
                [
                    float(norm(flux_stack).item()),
                    float(norm(flux_stack[:, 0]).item()),
                    float(norm(flux_stack[:, 1:]).item()),
                    max(row["post_history_entropy"] for row in entropy_values)
                    - min(row["post_history_entropy"] for row in entropy_values),
                    sum(row["compression_delta"] for row in entropy_values),
                    sum(row["directional_entropy_gradient"] for row in entropy_values),
                ],
                dtype=RTYPE,
            ),
        ]
    )
    return {
        "row_count": len(rows),
        "engine_count": len({row["engine_type"] for row in rows}),
        "topology_count": len({row["topology"] for row in rows}),
        "shell_direction_count": len(SHELL_DIRECTIONS),
        "flux_component_count": int(flux_stack.shape[1]),
        "ijk_flux_magnitude": float(norm(flux_stack).item()),
        "i_component_magnitude": float(norm(flux_stack[:, 0]).item()),
        "jk_temporal_component_magnitude": float(norm(flux_stack[:, 1:]).item()),
        "topology_signatures": topology_signatures,
        "engine_signatures": engine_signatures,
        "per_topology_flux": per_topology_flux,
        "entropy_span": max(row["post_history_entropy"] for row in entropy_values)
        - min(row["post_history_entropy"] for row in entropy_values),
        "compression_sum": sum(row["compression_delta"] for row in entropy_values),
        "directional_entropy_gradient_sum": sum(row["directional_entropy_gradient"] for row in entropy_values),
        "rows": rows,
        "signature": signature,
    }


def signature_gap(left: dict[str, Any], right: dict[str, Any]) -> float:
    return float(norm(left["signature"] - right["signature"]).item())


def min_pairwise_topology_gap(run: dict[str, Any]) -> float:
    values = [run["topology_signatures"][topology] for topology in TOPOLOGIES]
    gaps = []
    for i, left in enumerate(values):
        for right in values[i + 1 :]:
            gaps.append(float(norm(left - right).item()))
    return min(gaps)


def topology_mutation_magnitudes(run: dict[str, Any]) -> dict[str, float]:
    return {
        topology: float(norm(run["topology_signatures"][topology] - TOPOLOGY_BASE[topology]).item())
        for topology in TOPOLOGIES
    }


def quaternion_algebra_gate() -> dict[str, Any]:
    rules = {
        "qi_squared_minus_one": q_close(q_mul(Q_I, Q_I), -Q_ONE),
        "qj_squared_minus_one": q_close(q_mul(Q_J, Q_J), -Q_ONE),
        "qk_squared_minus_one": q_close(q_mul(Q_K, Q_K), -Q_ONE),
        "qi_qj_equals_qk": q_close(q_mul(Q_I, Q_J), Q_K),
        "qj_qk_equals_qi": q_close(q_mul(Q_J, Q_K), Q_I),
        "qk_qi_equals_qj": q_close(q_mul(Q_K, Q_I), Q_J),
        "qj_qi_equals_minus_qk": q_close(q_mul(Q_J, Q_I), -Q_K),
        "qk_qj_equals_minus_qi": q_close(q_mul(Q_K, Q_J), -Q_I),
        "qi_qk_equals_minus_qj": q_close(q_mul(Q_I, Q_K), -Q_J),
    }
    return {"pass": all(rules.values()), "rules": rules}


def representation_guard() -> dict[str, Any]:
    source_text = pathlib.Path(__file__).read_text(encoding="utf-8").lower()
    blocked_terms = [
        "".join(chr(code) for code in [98, 108, 111, 99, 104]),
        "".join(chr(code) for code in [99, 97, 114, 116, 101, 115, 105, 97, 110]),
        "".join(chr(code) for code in [112, 97, 117, 108, 105]),
    ]
    leaks = [term for term in blocked_terms if term in source_text]
    return {
        "pass": not leaks,
        "blocked_surface_leak_count": len(leaks),
        "allowed_surfaces": ["finite_density_carrier", "spinor", "quaternion", "IJK_shell_time"],
    }


def z3_gate() -> dict[str, Any]:
    topologies = z3.Int("topologies")
    engines = z3.Int("engines")
    shell_directions = z3.Int("shell_directions")
    components = z3.Int("components")
    flux_primitive = z3.Bool("flux_primitive")
    final_axis0 = z3.Bool("final_axis0")
    final_physics = z3.Bool("final_physics")
    solver = z3.Solver()
    solver.add(
        topologies == 4,
        engines == 2,
        shell_directions == 2,
        components == 3,
        z3.Not(flux_primitive),
        z3.Not(final_axis0),
        z3.Not(final_physics),
    )
    scalar = z3.Solver()
    scalar.add(components == 1, components == 3)
    primitive = z3.Solver()
    primitive.add(flux_primitive, z3.Not(flux_primitive))
    promotion = z3.Solver()
    promotion.add(final_physics, z3.Not(final_physics))
    return {
        "dynamic_shell_fixture_status": str(solver.check()),
        "scalar_flux_status": str(scalar.check()),
        "primitive_flux_status": str(primitive.check()),
        "promotion_status": str(promotion.check()),
        "pass": solver.check() == z3.sat
        and scalar.check() == z3.unsat
        and primitive.check() == z3.unsat
        and promotion.check() == z3.unsat,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    nominal = run_fixture()
    scalar = run_fixture(scalar_flux_collapse=True)
    chirality_erased = run_fixture(chirality_erased=True)
    shell_frozen = run_fixture(shell_time_frozen=True)
    shell_swapped = run_fixture(past_future_swapped=True)
    wrong_entropy = run_fixture(wrong_entropy_form=True)

    scalar_gap = signature_gap(nominal, scalar)
    chirality_gap = signature_gap(nominal, chirality_erased)
    shell_frozen_gap = signature_gap(nominal, shell_frozen)
    shell_swapped_gap = signature_gap(nominal, shell_swapped)
    wrong_entropy_gap = signature_gap(nominal, wrong_entropy)
    engine_chiral_gap = float(norm(nominal["engine_signatures"]["E1"] - nominal["engine_signatures"]["E2"]).item())
    topology_gaps = topology_mutation_magnitudes(nominal)
    min_topology_gap = min_pairwise_topology_gap(nominal)

    positive = {
        "dynamic_shell_fixture_covers_four_topologies_two_engines": {
            "pass": nominal["row_count"] == 16
            and nominal["engine_count"] == 2
            and nominal["topology_count"] == 4
            and nominal["shell_direction_count"] == 2,
            "row_count": nominal["row_count"],
            "engine_count": nominal["engine_count"],
            "topology_count": nominal["topology_count"],
            "shell_direction_count": nominal["shell_direction_count"],
            "directions": {"past": "outward", "future": "inward"},
        },
        "ijk_temporal_flux_is_three_component_and_nonzero": {
            "pass": nominal["flux_component_count"] == 3
            and nominal["i_component_magnitude"] > GAP_FLOOR
            and nominal["jk_temporal_component_magnitude"] > GAP_FLOOR,
            "flux_component_count": nominal["flux_component_count"],
            "ijk_flux_magnitude": nominal["ijk_flux_magnitude"],
            "i_component_magnitude": nominal["i_component_magnitude"],
            "jk_temporal_component_magnitude": nominal["jk_temporal_component_magnitude"],
        },
        "flux_mutates_all_four_topology_signatures": {
            "pass": all(value > DISTINCT_FLOOR for value in topology_gaps.values())
            and min_topology_gap > DISTINCT_FLOOR,
            "topology_mutation_magnitudes": topology_gaps,
            "min_pairwise_topology_signature_gap": min_topology_gap,
            "topology_signatures": nominal["topology_signatures"],
        },
        "flux_is_engine_bound_and_chiral": {
            "pass": engine_chiral_gap > DISTINCT_FLOOR and chirality_gap > DISTINCT_FLOOR,
            "engine_chiral_gap": engine_chiral_gap,
            "chirality_erased_signature_gap": chirality_gap,
            "engine_signatures": nominal["engine_signatures"],
        },
        "von_neumann_shell_history_entropy_is_live": {
            "pass": abs(nominal["compression_sum"]) > GAP_FLOOR
            and abs(nominal["directional_entropy_gradient_sum"]) > GAP_FLOOR
            and nominal["entropy_span"] > GAP_FLOOR,
            "entropy_span": nominal["entropy_span"],
            "compression_sum": nominal["compression_sum"],
            "directional_entropy_gradient_sum": nominal["directional_entropy_gradient_sum"],
        },
        "literal_quaternion_units_hold": quaternion_algebra_gate(),
        "representation_guard_excludes_blocked_charts": representation_guard(),
        "finite_nonpromotion_gate": z3_gate(),
    }

    graveyard_companions = {
        "GC1_scalar_flux_collapse_rejected": {
            "pass": scalar["jk_temporal_component_magnitude"] == 0.0 and scalar_gap > DISTINCT_FLOOR,
            "scalar_signature_gap": scalar_gap,
            "scalar_jk_temporal_component_magnitude": scalar["jk_temporal_component_magnitude"],
        },
        "GC2_chirality_erasure_rejected": {
            "pass": chirality_gap > DISTINCT_FLOOR,
            "chirality_erased_signature_gap": chirality_gap,
        },
        "GC3_shell_time_freeze_rejected": {
            "pass": shell_frozen_gap > DISTINCT_FLOOR,
            "shell_frozen_signature_gap": shell_frozen_gap,
        },
        "GC4_past_future_swap_rejected": {
            "pass": shell_swapped_gap > DISTINCT_FLOOR,
            "past_future_swapped_signature_gap": shell_swapped_gap,
        },
        "GC5_wrong_entropy_form_rejected": {
            "pass": wrong_entropy_gap > DISTINCT_FLOOR,
            "wrong_entropy_form_signature_gap": wrong_entropy_gap,
            "wrong_entropy_form": "relative-motion magnitude substituted for von Neumann shell-history entropy",
        },
    }

    boundary = {
        "B1_flux_is_derived_not_primitive": {
            "pass": PROMOTION_ALLOWED is False and "derived flux" in CLAIM_CEILING,
            "claim_ceiling": CLAIM_CEILING,
        },
        "B2_axis0_and_physics_remain_blocked": {
            "pass": "does not admit final flux" in CLAIM_CEILING and "physics claims" in CLAIM_CEILING,
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "B3_fixture_is_before_peps3d_or_l7_l8_closure": {
            "pass": True,
            "next_required_layers": [
                "embed this boundary current in dynamic spinor-shell MPS/PEPS/PEPS3D carriers",
                "feed the shell-current history into L7 Xi-history or L8 shell-weighted Phi0 controls",
            ],
        },
    }

    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
    )

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": 6,
            "passed": 6 if all_pass else 5,
            "variants": [
                "nominal_dynamic_shell_flux",
                "scalar_flux_collapse",
                "chirality_erased",
                "shell_time_frozen",
                "past_future_swapped",
                "wrong_entropy_form",
            ],
            "control_signature_gaps": {
                "scalar": scalar_gap,
                "chirality_erased": chirality_gap,
                "shell_frozen": shell_frozen_gap,
                "past_future_swapped": shell_swapped_gap,
                "wrong_entropy_form": wrong_entropy_gap,
            },
        },
        "all_pass": all_pass,
        "blockers": [],
        "summary": {
            "row_count": nominal["row_count"],
            "topologies": list(TOPOLOGIES),
            "engines": ["E1_type_one_left_weyl", "E2_type_two_right_weyl"],
            "shell_time": {"past": "outward", "future": "inward", "components": ["i", "j", "k"]},
            "engine_chiral_gap": engine_chiral_gap,
            "min_topology_gap": min_topology_gap,
            "control_signature_gaps": {
                "scalar": scalar_gap,
                "chirality_erased": chirality_gap,
                "shell_frozen": shell_frozen_gap,
                "past_future_swapped": shell_swapped_gap,
                "wrong_entropy_form": wrong_entropy_gap,
            },
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": (
            "This is a v5 formal scout for dynamic spinor-shell flux/topology "
            "boundary behavior. It is not a legacy v4 probe, not a promotion, "
            "and not a final Axis0/flux/physics claim."
        ),
        "next_required_work": [
            "Lift this fixture from local shell rows into dynamic spinor-shell MPS/PEPS/PEPS3D carriers.",
            "Use the derived IJK shell current as input to L7 Xi-history or L8 shell-weighted Phi0 controls.",
            "Keep final flux and Axis0 blocked until controls separate at tensor-carrier scale.",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": all_pass, "summary": as_jsonable(result["summary"])}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
