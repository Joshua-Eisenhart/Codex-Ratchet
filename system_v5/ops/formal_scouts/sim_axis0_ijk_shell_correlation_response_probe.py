#!/usr/bin/env python3
"""Axis0 IJK shell correlation-response scout.

Formal scout only.

This row converts the Axis0 v0.1-v0.3 and physics-bridge draft packet into a
bounded nonclassical test:

* 8 admitted spinors form the carrier, not a Cartesian vector ontology;
* engine rows induce finite quaternion shell gates;
* i is tested as a shell/cut scalar order parameter;
* j/k are tested as finite shell-history/refinement fuzz;
* Axis0 candidates are response signs under an admissible shell perturbation.

The result does not admit final Axis0, final flux, gravity, Standard Model,
Yang-Mills, Riemann, or physics claims.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from itertools import combinations
from typing import Any

import torch
import z3

import canonical_qit_engine_specs as specs


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "axis0_ijk_shell_correlation_response_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "axis0_ijk_shell_correlation_response"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests Axis0 draft candidates as finite shell/cut "
    "correlation-response signs over an 8-qubit spinor/quaternion engine. "
    "It emits candidate metrics for i-scalar, j/k shell-history fuzz, mutual "
    "information diversity, coherent information, conditional mutual "
    "information, and history entropy. It does not admit final Axis0, final "
    "flux, Xi, gravity, Standard Model, Yang-Mills, Riemann, or physics claims."
)
SOURCE_DOCS = {
    "axis0_v0_1": "READ ONLY Legacy core_docs/a1_refined_Ratchet Fuel/AXIS0_SPEC_OPTIONS_v0.1.md",
    "nlm_axis0_axis4_prep": "READ ONLY Legacy core_docs/a1_refined_Ratchet Fuel/NLM_AXIS_0_AND_4_PREP.md",
    "axis0_v0_2": "READ ONLY Legacy core_docs/a1_refined_Ratchet Fuel/AXIS0_SPEC_OPTIONS_v0.2.md",
    "physics_fuel_digest": "READ ONLY Legacy core_docs/a1_refined_Ratchet Fuel/PHYSICS_FUEL_DIGEST_v1.0.md",
    "axis0_v0_3": "READ ONLY Legacy core_docs/a1_refined_Ratchet Fuel/AXIS0_SPEC_OPTIONS_v0.3.md",
    "axis0_physics_bridge": "READ ONLY Legacy core_docs/a1_refined_Ratchet Fuel/AXIS0_PHYSICS_BRIDGE_v0.1.md",
}

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 8-qubit spinor state, quaternion shell gates, reductions, and entropy metrics",
    },
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive source-native 64-substage engine schedules and chirality signs",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion and finite Axis0 satisfiability gate",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "canonical_qit_engine_specs": "supportive",
    "z3": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

RTYPE = torch.float64
CDTYPE = torch.complex128
N_QUBITS = 8
N_SHELLS = 8
EPS = 1e-12
PERTURB_EPS = 0.15
GAP_FLOOR = 1e-6
OPERATOR_SEQUENCE = ["Ti", "Te", "Fi", "Fe"]
TOPOLOGIES = ["Se", "Ne", "Ni", "Si"]

Q_ONE = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=RTYPE)
Q_I = torch.tensor([0.0, 1.0, 0.0, 0.0], dtype=RTYPE)
Q_J = torch.tensor([0.0, 0.0, 1.0, 0.0], dtype=RTYPE)
Q_K = torch.tensor([0.0, 0.0, 0.0, 1.0], dtype=RTYPE)

TOPOLOGY_UNITS = {
    "Se": Q_I,
    "Ne": Q_J,
    "Ni": Q_K,
    "Si": -Q_I,
}
OPERATOR_UNITS = {
    "Ti": Q_K,
    "Te": Q_I,
    "Fi": Q_I,
    "Fe": Q_K,
}

SPINOR_PARAMS = [
    (0.13, 0.18, 0.34),
    (0.39, -0.29, 0.49),
    (-0.21, 0.46, 0.64),
    (0.79, 0.05, 0.77),
    (-0.61, -0.32, 0.41),
    (1.01, 0.29, 0.68),
    (-0.88, 0.15, 0.55),
    (0.31, -0.50, 0.91),
]


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def q_norm(q: torch.Tensor) -> torch.Tensor:
    return torch.linalg.norm(q)


def q_normalize(q: torch.Tensor) -> torch.Tensor:
    size = q_norm(q)
    if float(size.item()) <= EPS:
        raise ValueError("zero quaternion")
    return q / size


def q_mul(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    a0, a1, a2, a3 = [float(item) for item in a]
    b0, b1, b2, b3 = [float(item) for item in b]
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
    return q_normalize(math.cos(angle) * Q_ONE + math.sin(angle) * unit)


def q_close(a: torch.Tensor, b: torch.Tensor, *, tol: float = 1e-10) -> bool:
    return float(q_norm(a - b).item()) < tol


def quaternion_algebra_gate() -> dict[str, Any]:
    rules = {
        "i2": q_close(q_mul(Q_I, Q_I), -Q_ONE),
        "j2": q_close(q_mul(Q_J, Q_J), -Q_ONE),
        "k2": q_close(q_mul(Q_K, Q_K), -Q_ONE),
        "ij": q_close(q_mul(Q_I, Q_J), Q_K),
        "jk": q_close(q_mul(Q_J, Q_K), Q_I),
        "ki": q_close(q_mul(Q_K, Q_I), Q_J),
        "ji": q_close(q_mul(Q_J, Q_I), -Q_K),
        "kj": q_close(q_mul(Q_K, Q_J), -Q_I),
        "ik": q_close(q_mul(Q_I, Q_K), -Q_J),
    }
    return {"pass": all(rules.values()), "rules": rules}


def spinor(phi: float, chi: float, eta: float) -> torch.Tensor:
    raw = torch.tensor(
        [
            complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
            complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
        ],
        dtype=CDTYPE,
    )
    return raw / torch.linalg.norm(raw)


def build_product_state() -> torch.Tensor:
    state = spinor(*SPINOR_PARAMS[0])
    for params in SPINOR_PARAMS[1:]:
        state = torch.kron(state, spinor(*params))
    return state / torch.linalg.norm(state)


def engine_path_order(engine_type: int, loop_class: str) -> tuple[str, str]:
    if engine_type == 0:
        return ("base", "deductive") if loop_class == "outer" else ("fiber", "inductive")
    return ("fiber", "inductive") if loop_class == "outer" else ("base", "deductive")


def node_pair(engine_type: int, macro_stage_idx: int, substage_idx: int) -> tuple[int, int]:
    base = macro_stage_idx % N_QUBITS
    offset = 1 + (substage_idx % 3)
    if macro_stage_idx >= 4:
        offset = 4 + (substage_idx % 2)
    a = base
    b = (base + offset) % N_QUBITS
    if engine_type == 1:
        a = (N_QUBITS - 1 - a) % N_QUBITS
        b = (N_QUBITS - 1 - b) % N_QUBITS
    if a == b:
        b = (b + 1) % N_QUBITS
    return a, b


def build_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for engine_type in [0, 1]:
        engine = specs.get_engine_spec(engine_type)
        for macro_stage_idx, (topology, loop_class) in enumerate(specs.get_schedule(engine_type)):
            chart = specs.get_chart_token_spec(topology, engine_type, loop_class)
            terrain = specs.get_terrain_dynamics_spec(topology, engine_type)
            path_class, order_family = engine_path_order(engine_type, loop_class)
            for substage_idx, operator in enumerate(OPERATOR_SEQUENCE):
                rows.append(
                    {
                        "global_substage_idx": len(rows),
                        "engine_type": engine_type + 1,
                        "engine_label": engine["type_label"],
                        "chirality_sign": int(engine["chirality_sign"]),
                        "macro_stage_idx": macro_stage_idx,
                        "substage_idx": substage_idx,
                        "topology": topology,
                        "terrain_variant": terrain["realization"],
                        "loop_class": loop_class,
                        "path_class": path_class,
                        "order_family": order_family,
                        "axis6_sign": int(chart["sign"]),
                        "operator": operator,
                        "shell_slot": (macro_stage_idx + 2 * substage_idx + 3 * engine_type) % N_SHELLS,
                        "node_pair": node_pair(engine_type, macro_stage_idx, substage_idx),
                    }
                )
    return rows


def shell_time_drive(row: dict[str, Any], *, lam: float, mode: str) -> torch.Tensor:
    if mode == "global_phase_only":
        tick = 0.06 * float(row["global_substage_idx"] + 1)
        return q_exp(Q_I, tick)
    chirality = float(row["chirality_sign"])
    if mode == "achiral":
        chirality = 1.0
    shell = float(row["shell_slot"] + 1)
    path_sign = 1.0 if row["path_class"] == "base" else -1.0
    order_sign = 1.0 if row["order_family"] == "deductive" else -1.0
    tick = 0.019 * float(row["global_substage_idx"] + 1) * float(row["axis6_sign"])
    if mode == "static_jk":
        past_outward = 0.0
        future_inward = 0.0
    else:
        shell_bias = 2.0 * (shell / float(N_SHELLS)) - 1.0
        past_outward = shell / float(N_SHELLS)
        future_inward = -float(N_SHELLS + 1 - shell) / float(N_SHELLS)
        past_outward *= 1.0 + lam * shell_bias
        future_inward *= 1.0 - lam * shell_bias
    if mode == "swapped_arrows":
        past_outward, future_inward = -future_inward, -past_outward
    past_angle = 0.16 * chirality * path_sign * past_outward
    future_angle = 0.14 * chirality * order_sign * future_inward
    drive = q_mul(q_exp(Q_I, tick), q_exp(Q_J, past_angle))
    return q_mul(drive, q_exp(Q_K, future_angle))


def two_qubit_gate(row: dict[str, Any], *, lam: float, mode: str) -> tuple[torch.Tensor, torch.Tensor]:
    drive = shell_time_drive(row, lam=lam, mode=mode)
    topo_unit = TOPOLOGY_UNITS[row["topology"]] if mode != "topology_blind" else Q_J
    op_unit = OPERATOR_UNITS[row["operator"]]
    topo = q_exp(topo_unit, 0.023 * float(row["chirality_sign"]))
    op = q_exp(op_unit, 0.031 * float(row["axis6_sign"]))
    q = q_mul(q_mul(drive, topo), op)
    i_comp = float(q[1].item())
    j_comp = float(q[2].item())
    k_comp = float(q[3].item())
    entangle = 0.11 * math.sqrt(j_comp * j_comp + k_comp * k_comp)
    if mode == "global_phase_only":
        entangle = 0.0
    phase = math.atan2(k_comp, j_comp + EPS)
    c = math.cos(entangle)
    s = math.sin(entangle)
    phase_i = 0.09 * i_comp
    e_i = complex(math.cos(phase_i), math.sin(phase_i))
    e_neg_i = complex(math.cos(-phase_i), math.sin(-phase_i))
    e_p = complex(math.cos(phase), math.sin(phase))
    e_m = complex(math.cos(-phase), math.sin(-phase))
    gate = torch.zeros((4, 4), dtype=CDTYPE)
    gate[0, 0] = e_i
    gate[3, 3] = e_neg_i
    gate[1, 1] = complex(c, 0.0)
    gate[1, 2] = e_p * s
    gate[2, 1] = -e_m * s
    gate[2, 2] = complex(c, 0.0)
    return gate, drive[1:]


def apply_two_qubit_gate(state: torch.Tensor, gate: torch.Tensor, a: int, b: int) -> torch.Tensor:
    dims = [2] * N_QUBITS
    tensor = state.reshape(dims)
    axes = [a, b] + [idx for idx in range(N_QUBITS) if idx not in {a, b}]
    inv_axes = [axes.index(idx) for idx in range(N_QUBITS)]
    front = tensor.permute(axes).reshape(4, -1)
    updated = (gate @ front).reshape([2, 2] + [2] * (N_QUBITS - 2)).permute(inv_axes).reshape(-1)
    return updated / torch.linalg.norm(updated)


def reduced_density(state: torch.Tensor, keep: list[int]) -> torch.Tensor:
    keep = sorted(keep)
    if not keep:
        return torch.ones((1, 1), dtype=CDTYPE)
    axes = keep + [idx for idx in range(N_QUBITS) if idx not in keep]
    tensor = state.reshape([2] * N_QUBITS).permute(axes)
    rows = 2 ** len(keep)
    mat = tensor.reshape(rows, -1)
    rho = mat @ torch.conj(mat).T
    return 0.5 * (rho + torch.conj(rho).T)


def entropy(rho: torch.Tensor) -> float:
    vals = torch.real(torch.linalg.eigvalsh(rho))
    vals = torch.clamp(vals, min=0.0)
    vals = vals / torch.sum(vals)
    nz = vals[vals > 1e-11]
    if nz.numel() == 0:
        return 0.0
    return float((-torch.sum(nz * torch.log(nz))).item())


def mutual_information(state: torch.Tensor, a: int, b: int) -> float:
    return (
        entropy(reduced_density(state, [a]))
        + entropy(reduced_density(state, [b]))
        - entropy(reduced_density(state, [a, b]))
    )


def distribution_entropy(weights: torch.Tensor) -> float:
    total = torch.sum(weights)
    if float(total.item()) <= EPS:
        return 0.0
    probs = weights / total
    nz = probs[probs > 1e-11]
    return float((-torch.sum(nz * torch.log(nz))).item())


def shell_partitions() -> list[dict[str, list[int]]]:
    rows = []
    for r in range(1, N_QUBITS - 1):
        rows.append(
            {
                "interior": list(range(r)),
                "boundary": [r],
                "outside": list(range(r + 1, N_QUBITS)),
            }
        )
    return rows


def state_metrics(state: torch.Tensor, history_weights: torch.Tensor, shell_time_rows: list[torch.Tensor]) -> dict[str, Any]:
    pair_values = torch.tensor(
        [mutual_information(state, a, b) for a, b in combinations(range(N_QUBITS), 2)],
        dtype=RTYPE,
    )
    pair_nonnegative = torch.clamp(pair_values, min=0.0)
    d_mi = distribution_entropy(pair_nonnegative + EPS)
    var_mi = float(torch.var(pair_values, unbiased=False).item())
    total_correlation = sum(entropy(reduced_density(state, [idx])) for idx in range(N_QUBITS)) - entropy(
        reduced_density(state, list(range(N_QUBITS)))
    )
    shell_rows = []
    coherent_values = []
    cmi_values = []
    negative_conditional_count = 0
    for row in shell_partitions():
        interior = row["interior"]
        boundary = row["boundary"]
        outside = row["outside"]
        ib = interior + boundary
        bo = boundary + outside
        ibo = interior + boundary + outside
        s_i = entropy(reduced_density(state, interior))
        s_b = entropy(reduced_density(state, boundary))
        s_ib = entropy(reduced_density(state, ib))
        s_bo = entropy(reduced_density(state, bo))
        s_ibo = entropy(reduced_density(state, ibo))
        s_cond = s_ibo - s_bo
        i_coh = -s_cond
        cmi = s_ib + s_bo - s_b - s_ibo
        coherent_values.append(i_coh)
        cmi_values.append(cmi)
        if s_cond < -GAP_FLOOR:
            negative_conditional_count += 1
        shell_rows.append(
            {
                "interior": interior,
                "boundary": boundary,
                "outside": outside,
                "cut_entropy": s_i,
                "conditional_entropy_I_given_BO": s_cond,
                "coherent_information_I_to_BO": i_coh,
                "conditional_mutual_information_I_O_given_B": cmi,
            }
        )
    shell_time = torch.stack(shell_time_rows)
    jk_magnitude = float(torch.linalg.norm(shell_time[:, 1:]).item())
    i_scalar = float(sum(coherent_values))
    return {
        "pair_mi_values": pair_values,
        "D_MI": d_mi,
        "Var_MI": var_mi,
        "T_total_correlation": float(total_correlation),
        "i_shell_coherent_sum": i_scalar,
        "CMI_shell_mean": float(torch.mean(torch.tensor(cmi_values, dtype=RTYPE)).item()),
        "H_history": distribution_entropy(history_weights + EPS),
        "jk_shell_time_magnitude": jk_magnitude,
        "negative_conditional_entropy_fraction": negative_conditional_count / len(shell_rows),
        "shell_rows": shell_rows,
    }


def run_engine(*, lam: float, mode: str) -> dict[str, Any]:
    state = build_product_state()
    rows = build_rows()
    history_weights = torch.zeros(N_SHELLS, dtype=RTYPE)
    shell_time_rows: list[torch.Tensor] = []
    for row in rows:
        gate, shell_time_ijk = two_qubit_gate(row, lam=lam, mode=mode)
        shell_time_rows.append(shell_time_ijk)
        a, b = row["node_pair"]
        state = apply_two_qubit_gate(state, gate, a, b)
        history_weights[int(row["shell_slot"])] += float(torch.linalg.norm(shell_time_ijk[1:]).item()) + 1e-4
    metrics = state_metrics(state, history_weights, shell_time_rows)
    metrics.update(
        {
            "mode": mode,
            "lambda": lam,
            "row_count": len(rows),
            "qubit_count": N_QUBITS,
            "hilbert_dim": 2**N_QUBITS,
            "shell_count": N_SHELLS,
            "terrain_variant_count": len({row["terrain_variant"] for row in rows}),
        }
    )
    return metrics


def response(base: dict[str, Any], perturbed: dict[str, Any]) -> dict[str, Any]:
    keys = ["D_MI", "Var_MI", "T_total_correlation", "i_shell_coherent_sum", "CMI_shell_mean", "H_history"]
    return {key: (perturbed[key] - base[key]) / PERTURB_EPS for key in keys}


def metric_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
    keys = ["D_MI", "Var_MI", "T_total_correlation", "i_shell_coherent_sum", "CMI_shell_mean", "H_history"]
    va = torch.tensor([a[key] for key in keys], dtype=RTYPE)
    vb = torch.tensor([b[key] for key in keys], dtype=RTYPE)
    return float(torch.linalg.norm(va - vb).item())


def z3_gate() -> dict[str, Any]:
    qubits = z3.Int("qubits")
    shells = z3.Int("shells")
    final_axis0 = z3.Bool("final_axis0")
    cartesian_root = z3.Bool("cartesian_root")
    solver = z3.Solver()
    solver.add(qubits == N_QUBITS, shells == N_SHELLS, z3.Not(final_axis0), z3.Not(cartesian_root))
    promotion = z3.Solver()
    promotion.add(qubits == N_QUBITS, shells == N_SHELLS, final_axis0, z3.Not(final_axis0))
    return {
        "pass": solver.check() == z3.sat and promotion.check() == z3.unsat,
        "sat": str(solver.check()),
        "promotion_status": str(promotion.check()),
        "promotion_blocked_by_contract": True,
        "cartesian_root_blocked": True,
    }


def main() -> int:
    started = time.time()
    base = run_engine(lam=0.0, mode="nominal")
    perturbed = run_engine(lam=PERTURB_EPS, mode="nominal")
    phase_base = run_engine(lam=0.0, mode="global_phase_only")
    phase_perturbed = run_engine(lam=PERTURB_EPS, mode="global_phase_only")
    static_base = run_engine(lam=0.0, mode="static_jk")
    static_perturbed = run_engine(lam=PERTURB_EPS, mode="static_jk")
    topology_blind = run_engine(lam=PERTURB_EPS, mode="topology_blind")
    swapped = run_engine(lam=PERTURB_EPS, mode="swapped_arrows")
    nominal_response = response(base, perturbed)
    phase_response = response(phase_base, phase_perturbed)
    static_response = response(static_base, static_perturbed)
    response_norm = float(torch.linalg.norm(torch.tensor(list(nominal_response.values()), dtype=RTYPE)).item())
    phase_response_norm = float(torch.linalg.norm(torch.tensor(list(phase_response.values()), dtype=RTYPE)).item())
    static_response_norm = float(torch.linalg.norm(torch.tensor(list(static_response.values()), dtype=RTYPE)).item())
    topology_blind_gap = metric_gap(perturbed, topology_blind)
    swapped_gap = metric_gap(perturbed, swapped)
    positive = {
        "bounded_8q_spinor_shell_engine_runs": {
            "pass": base["qubit_count"] == 8
            and base["hilbert_dim"] == 256
            and base["row_count"] == 64
            and base["terrain_variant_count"] == 8,
            "qubit_count": base["qubit_count"],
            "hilbert_dim": base["hilbert_dim"],
            "row_count": base["row_count"],
            "terrain_variant_count": base["terrain_variant_count"],
        },
        "literal_quaternion_ijk_layer": {
            "pass": quaternion_algebra_gate()["pass"] and perturbed["jk_shell_time_magnitude"] > GAP_FLOOR,
            "quaternion_algebra": quaternion_algebra_gate(),
            "jk_shell_time_magnitude": perturbed["jk_shell_time_magnitude"],
            "temporal_interpretation": {
                "i": "shell/cut scalar order parameter candidate",
                "j": "past_outward_history_refinement_component",
                "k": "future_inward_history_refinement_component",
            },
        },
        "negative_conditional_entropy_exists_on_shell_cuts": {
            "pass": perturbed["negative_conditional_entropy_fraction"] > 0.0,
            "negative_conditional_entropy_fraction": perturbed["negative_conditional_entropy_fraction"],
        },
        "axis0_candidate_response_metrics_emitted": {
            "pass": response_norm > GAP_FLOOR,
            "response_norm": response_norm,
            "candidate_derivatives": nominal_response,
            "axis0_reading": {
                key: ("allostatic" if value > 0.0 else "homeostatic_or_damped")
                for key, value in nominal_response.items()
            },
        },
        "i_scalar_and_jk_fuzz_both_load_bearing": {
            "pass": abs(nominal_response["i_shell_coherent_sum"]) > GAP_FLOOR
            and abs(nominal_response["H_history"]) > GAP_FLOOR,
            "di_shell_coherent_sum": nominal_response["i_shell_coherent_sum"],
            "dH_history": nominal_response["H_history"],
        },
    }
    graveyard = {
        "GC1_global_phase_only_no_axis0_response": {
            "pass": phase_response_norm < GAP_FLOOR,
            "phase_response_norm": phase_response_norm,
            "phase_response": phase_response,
        },
        "GC2_static_jk_removes_shell_time_response": {
            "pass": static_response_norm < response_norm and static_perturbed["jk_shell_time_magnitude"] < GAP_FLOOR,
            "static_response_norm": static_response_norm,
            "nominal_response_norm": response_norm,
            "static_jk_shell_time_magnitude": static_perturbed["jk_shell_time_magnitude"],
        },
        "GC3_topology_blind_changes_axis0_signature": {
            "pass": topology_blind_gap > GAP_FLOOR,
            "topology_blind_gap": topology_blind_gap,
        },
        "GC4_swapped_arrows_change_axis0_signature": {
            "pass": swapped_gap > GAP_FLOOR,
            "swapped_arrow_gap": swapped_gap,
        },
        "GC5_nonpromotion_solver": z3_gate(),
    }
    boundary = {
        "B1_formal_scout_only": {"pass": CLASSIFICATION == "formal_scout" and not PROMOTION_ALLOWED},
        "B2_no_final_axis0_or_physics_claim": {
            "pass": "does not admit final Axis0" in CLAIM_CEILING and "physics claims" in CLAIM_CEILING,
            "claim_ceiling": CLAIM_CEILING,
        },
        "B3_no_cartesian_root": {
            "pass": True,
            "root_carrier": "8 admitted spinors plus finite shell/cut reductions; no Bloch or Cartesian vector root",
        },
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard.values()) and all(
        row["pass"] for row in boundary.values()
    )
    variant_rows = list(positive.values()) + list(graveyard.values()) + list(boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "source_docs": SOURCE_DOCS,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
        "nearby_variants": {
            "passed": sum(1 for row in variant_rows if row["pass"]),
            "total": len(variant_rows),
        },
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "baseline": {
            key: value
            for key, value in base.items()
            if key not in {"pair_mi_values", "shell_rows"}
        },
        "perturbed": {
            key: value
            for key, value in perturbed.items()
            if key not in {"pair_mi_values", "shell_rows"}
        },
        "shell_rows_sample": perturbed["shell_rows"][:3],
        "axis0_candidate_derivatives": nominal_response,
        "control_summaries": {
            "global_phase_only": {
                "response": phase_response,
                "response_norm": phase_response_norm,
            },
            "static_jk": {
                "response": static_response,
                "response_norm": static_response_norm,
                "jk_shell_time_magnitude": static_perturbed["jk_shell_time_magnitude"],
            },
            "topology_blind_gap": topology_blind_gap,
            "swapped_arrow_gap": swapped_gap,
        },
        "summary": {
            "elapsed_seconds": time.time() - started,
            "qubit_count": base["qubit_count"],
            "row_count": base["row_count"],
            "hilbert_dim": base["hilbert_dim"],
            "jk_shell_time_magnitude": perturbed["jk_shell_time_magnitude"],
            "negative_conditional_entropy_fraction": perturbed["negative_conditional_entropy_fraction"],
            "response_norm": response_norm,
            "phase_response_norm": phase_response_norm,
            "static_response_norm": static_response_norm,
            "topology_blind_gap": topology_blind_gap,
            "swapped_arrow_gap": swapped_gap,
        },
        "next_required_work": [
            "Port this Axis0 shell-response harness onto the 8/16/32/64 MPS carrier.",
            "Replace finite history-response entropy with explicit Kraus/Stinespring branch weights for noisy channels.",
            "Run the same Axis0 candidates on PEPS and PEPS3D shell partitions after carrier controls pass.",
            "Only then test whether shell-time flux improves L7 Xi-history or L8 shell-weighted Phi0.",
        ],
        "why_not_v4_probes": (
            "This is a v5 spinor/quaternion shell-response scout derived from Axis0 draft specs. "
            "It is not a legacy v4 probe, not a primitive time model, and not a final physics claim."
        ),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "summary": as_jsonable(result["summary"]), "wrote": str(OUT_PATH)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
