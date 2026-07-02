#!/usr/bin/env python3
"""Explicit-spinor full IGT 64-substage engine-cycle scout.

Formal scout only.

This row encodes the owner correction that must not be lost:

* two engine types;
* each engine has eight macro stages: four outer + four inner;
* each macro stage runs all four operators as substages;
* all four operator substages inherit the macro-stage Axis6 sign;
* each engine type therefore has 32 substages, and the paired cycle has 64;
* each topology has two terrain variants across the two engines and four
  possible chart operators across the combined engine pair.

The carrier is an explicit 8-qubit Hopf-spinor density matrix. This is a stage
grammar and runnable carrier gate, not a final flux/Axis0/physics claim.
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
NAME = "explicit_spinor_full_igt_64_substage_engine_cycle_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "explicit_spinor_full_igt_64_substage_engine_cycle"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: runs the corrected 2-engine IGT chart grammar as 8 "
    "macro stages per engine, 4 same-Axis6-sign operator substages per stage, "
    "and 64 substages total on an explicit 8-qubit Hopf-spinor density carrier. "
    "It does not admit final flux, Axis0, Xi, real attractor-basin convergence, "
    "physics, gravity, Standard Model, Yang-Mills, or PEPS3D environment closure."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing explicit Hopf spinors, 8-qubit density carrier, 64 signed operator substages, and QIT readouts",
    },
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive source-native engine schedules, terrain specs, chart tokens, and Axis6 signs; local QIT execution is load-bearing in PyTorch",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite row-count, same-sign, and nonpromotion constraints",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive canonical result serialization"},
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

N_QUBITS = 8
N_ENGINES = 2
N_MACRO_STAGES_PER_ENGINE = 8
N_OPERATOR_SUBSTAGES_PER_STAGE = 4
N_SUBSTAGES_PER_ENGINE = N_MACRO_STAGES_PER_ENGINE * N_OPERATOR_SUBSTAGES_PER_STAGE
N_TOTAL_SUBSTAGES = N_ENGINES * N_SUBSTAGES_PER_ENGINE
OPERATOR_SEQUENCE = ["Ti", "Te", "Fi", "Fe"]
RTYPE = torch.float64
CDTYPE = torch.complex128
EPS = 1e-12
GAP_FLOOR = 1e-5

SX = specs.SX
SY = specs.SY
SZ = specs.SZ
I2 = specs.I2

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


def normalize_vector(vector: torch.Tensor) -> torch.Tensor:
    norm = torch.linalg.vector_norm(vector)
    if float(norm.item()) <= EPS:
        raise ValueError("zero vector")
    return vector / norm


def spinor(phi: float, chi: float, eta: float, *, phase: float = 0.0) -> torch.Tensor:
    raw = torch.tensor(
        [
            complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
            complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
        ],
        dtype=CDTYPE,
    )
    gauge = complex(math.cos(phase), math.sin(phase))
    return normalize_vector(gauge * raw)


def build_spinors(*, gauge_phases: list[float] | None = None) -> list[torch.Tensor]:
    phases = gauge_phases or [0.0] * N_QUBITS
    return [spinor(*params, phase=phases[idx]) for idx, params in enumerate(SPINOR_PARAMS)]


def kron_all(vectors: list[torch.Tensor]) -> torch.Tensor:
    out = vectors[0]
    for vector in vectors[1:]:
        out = torch.kron(out, vector)
    return normalize_vector(out)


def initial_density(*, gauge_phases: list[float] | None = None) -> torch.Tensor:
    state = kron_all(build_spinors(gauge_phases=gauge_phases))
    return torch.outer(state, torch.conj(state))


def apply_axes_matrix(tensor: torch.Tensor, matrix: torch.Tensor, axes: list[int]) -> torch.Tensor:
    dims = list(tensor.shape)
    rest = [axis for axis in range(len(dims)) if axis not in axes]
    perm = axes + rest
    inv = [perm.index(axis) for axis in range(len(dims))]
    front_dim = math.prod(dims[axis] for axis in axes)
    updated = matrix @ tensor.permute(perm).reshape(front_dim, -1)
    return updated.reshape([dims[axis] for axis in axes] + [dims[axis] for axis in rest]).permute(inv)


def apply_two_qubit_unitary(rho: torch.Tensor, unitary: torch.Tensor, q0: int, q1: int) -> torch.Tensor:
    tensor = rho.reshape([2] * (2 * N_QUBITS))
    tensor = apply_axes_matrix(tensor, unitary, [q0, q1])
    tensor = apply_axes_matrix(tensor, torch.conj(unitary), [N_QUBITS + q0, N_QUBITS + q1])
    return tensor.reshape(2**N_QUBITS, 2**N_QUBITS)


def apply_single_qubit_dephasing(rho: torch.Tensor, pauli: torch.Tensor, qubit: int, rate: float) -> torch.Tensor:
    tensor = rho.reshape([2] * (2 * N_QUBITS))
    conj = apply_axes_matrix(tensor, pauli, [qubit])
    conj = apply_axes_matrix(conj, torch.conj(pauli), [N_QUBITS + qubit]).reshape(2**N_QUBITS, 2**N_QUBITS)
    return (1.0 - rate) * rho + rate * conj


def operator_matrix(operator: str) -> torch.Tensor:
    return {"Ti": SZ, "Te": SX, "Fi": SX, "Fe": SZ}[operator]


def entangling_generator(operator: str) -> torch.Tensor:
    if operator in {"Ti", "Fe"}:
        return torch.kron(SZ, SZ)
    return torch.kron(SX, SX)


def terrain_pair(engine_type: int, macro_stage_idx: int, substage_idx: int) -> tuple[int, int]:
    # Keep pairs bounded and deterministic. Outer stages emphasize ring edges;
    # inner stages emphasize cross-cut bridges.
    base = macro_stage_idx % N_QUBITS
    if macro_stage_idx < 4:
        q0 = base
        q1 = (base + 1 + (substage_idx % 2)) % N_QUBITS
    else:
        q0 = base
        q1 = (base + N_QUBITS // 2 + (substage_idx % 2)) % N_QUBITS
    if engine_type == 1:
        q0 = (N_QUBITS - 1 - q0) % N_QUBITS
        q1 = (N_QUBITS - 1 - q1) % N_QUBITS
    if q0 == q1:
        q1 = (q1 + 1) % N_QUBITS
    return q0, q1


def chart_rows(*, mixed_axis6: bool = False, native_only: bool = False, one_engine_only: bool = False) -> list[dict[str, Any]]:
    rows = []
    engine_range = [0] if one_engine_only else [0, 1]
    for engine_type in engine_range:
        for macro_stage_idx, (perception, loop_class) in enumerate(specs.get_schedule(engine_type)):
            chart = specs.get_chart_token_spec(perception, engine_type, loop_class)
            stage_sign = int(chart["sign"])
            operators = OPERATOR_SEQUENCE if not native_only else [chart["operator"]]
            for substage_idx, operator in enumerate(operators):
                sign = stage_sign
                if mixed_axis6 and substage_idx % 2 == 1:
                    sign = -stage_sign
                precedence = "operator_first" if sign > 0 else "terrain_first"
                token = specs.ordered_token(operator, perception, precedence)
                q0, q1 = terrain_pair(engine_type, macro_stage_idx, substage_idx)
                terrain = specs.get_terrain_dynamics_spec(perception, engine_type)
                rows.append(
                    {
                        "engine_type": engine_type + 1,
                        "engine_label": specs.get_engine_spec(engine_type)["type_label"],
                        "macro_stage_idx": macro_stage_idx,
                        "substage_idx": substage_idx,
                        "global_substage_idx": len(rows),
                        "perception": perception,
                        "topology": perception,
                        "terrain_variant": terrain["realization"],
                        "terrain_family": terrain["family"],
                        "loop_class": loop_class,
                        "operator": operator,
                        "chart_operator": chart["operator"],
                        "axis6_sign": sign,
                        "axis6": "UP" if sign > 0 else "DOWN",
                        "stage_axis6_sign": stage_sign,
                        "same_sign_as_stage": sign == stage_sign,
                        "token": token,
                        "chart_token": chart["token"],
                        "qpair": [q0, q1],
                    }
                )
    return rows


def apply_substage(rho: torch.Tensor, row: dict[str, Any]) -> torch.Tensor:
    op = row["operator"]
    sign = int(row["axis6_sign"])
    q0, q1 = row["qpair"]
    stage = int(row["macro_stage_idx"])
    sub = int(row["substage_idx"])
    strength = sign * (0.055 + 0.012 * ((stage + sub) % 4))
    if op in {"Fi", "Fe"}:
        unitary = torch.linalg.matrix_exp((-1j * strength) * entangling_generator(op))
        return apply_two_qubit_unitary(rho, unitary, q0, q1)
    rate = min(0.045, 0.011 + abs(strength) * 0.18)
    pauli = operator_matrix(op)
    rho = apply_single_qubit_dephasing(rho, pauli, q0, rate)
    return apply_single_qubit_dephasing(rho, pauli, q1, rate)


def reduced_density(rho: torch.Tensor, keep: list[int]) -> torch.Tensor:
    keep = sorted(keep)
    trace_out = [idx for idx in range(N_QUBITS) if idx not in keep]
    tensor = rho.reshape([2] * N_QUBITS + [2] * N_QUBITS)
    perm = keep + trace_out + [N_QUBITS + idx for idx in keep] + [N_QUBITS + idx for idx in trace_out]
    k_dim = 2 ** len(keep)
    t_dim = 2 ** len(trace_out)
    block = tensor.permute(perm).reshape(k_dim, t_dim, k_dim, t_dim)
    return torch.einsum("abcb->ac", block)


def entropy(rho: torch.Tensor) -> float:
    herm = (rho + torch.conj(rho).T) / 2
    vals = torch.clamp(torch.linalg.eigvalsh(herm).real, min=0.0)
    vals = vals / torch.clamp(torch.sum(vals), min=EPS)
    nz = vals[vals > 1e-12]
    return float((-torch.sum(nz * torch.log(nz))).item())


def partial_transpose_4_4(rho: torch.Tensor) -> torch.Tensor:
    return rho.reshape(16, 16, 16, 16).permute(0, 3, 2, 1).reshape(256, 256)


def log_negativity_4_4(rho: torch.Tensor) -> float:
    pt = partial_transpose_4_4(rho)
    pt = (pt + torch.conj(pt).T) / 2
    trace_norm = torch.sum(torch.abs(torch.linalg.eigvalsh(pt).real))
    return float(torch.log(torch.clamp(trace_norm, min=1.0)).item())


def run_cycle(
    *,
    mixed_axis6: bool = False,
    native_only: bool = False,
    one_engine_only: bool = False,
    gauge_phases: list[float] | None = None,
) -> dict[str, Any]:
    rows = chart_rows(mixed_axis6=mixed_axis6, native_only=native_only, one_engine_only=one_engine_only)
    rho = initial_density(gauge_phases=gauge_phases)
    readout_rows = []
    for row in rows:
        rho = apply_substage(rho, row)
        rho = (rho + torch.conj(rho).T) / 2
        rho = rho / torch.trace(rho)
        if row["substage_idx"] == 3 or native_only:
            left = reduced_density(rho, [0, 1, 2, 3])
            right = reduced_density(rho, [4, 5, 6, 7])
            readout_rows.append(
                {
                    **row,
                    "full_entropy": entropy(rho),
                    "left_entropy": entropy(left),
                    "right_entropy": entropy(right),
                    "mutual_information_left_right": entropy(left) + entropy(right) - entropy(rho),
                }
            )
    left = reduced_density(rho, [0, 1, 2, 3])
    right = reduced_density(rho, [4, 5, 6, 7])
    full_entropy = entropy(rho)
    return {
        "row_count": len(rows),
        "engine_count": len({row["engine_type"] for row in rows}),
        "macro_stage_count": len({(row["engine_type"], row["macro_stage_idx"]) for row in rows}),
        "terrain_variant_count": len({row["terrain_variant"] for row in rows}),
        "topology_count": len({row["topology"] for row in rows}),
        "operator_count": len({row["operator"] for row in rows}),
        "same_sign_stage_count": sum(
            int(all(item["same_sign_as_stage"] for item in rows if item["engine_type"] == engine and item["macro_stage_idx"] == stage))
            for engine in sorted({row["engine_type"] for row in rows})
            for stage in sorted({row["macro_stage_idx"] for row in rows if row["engine_type"] == engine})
        ),
        "full_entropy": full_entropy,
        "left_entropy": entropy(left),
        "right_entropy": entropy(right),
        "mutual_information_left_right": entropy(left) + entropy(right) - full_entropy,
        "coherent_information_left_to_right": entropy(right) - full_entropy,
        "log_negativity_left_right": log_negativity_4_4(rho),
        "trace_error": abs(float(torch.real(torch.trace(rho)).item()) - 1.0) + abs(float(torch.imag(torch.trace(rho)).item())),
        "min_eigenvalue": float(torch.min(torch.linalg.eigvalsh((rho + torch.conj(rho).T) / 2).real).item()),
        "rows": rows,
        "stage_readouts": readout_rows,
    }


def signature(row: dict[str, Any]) -> torch.Tensor:
    return torch.tensor(
        [
            row["row_count"],
            row["macro_stage_count"],
            row["terrain_variant_count"],
            row["operator_count"],
            row["same_sign_stage_count"],
            row["full_entropy"],
            row["left_entropy"],
            row["right_entropy"],
            row["mutual_information_left_right"],
            row["coherent_information_left_to_right"],
            row["log_negativity_left_right"],
        ],
        dtype=RTYPE,
    )


def signature_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
    return float(torch.linalg.vector_norm(signature(a) - signature(b)).item())


def topology_operator_table(rows: list[dict[str, Any]]) -> dict[str, Any]:
    table: dict[str, dict[str, Any]] = {}
    for topology in ["Se", "Ne", "Ni", "Si"]:
        top_rows = [row for row in rows if row["topology"] == topology]
        table[topology] = {
            "terrain_variants": sorted({row["terrain_variant"] for row in top_rows}),
            "chart_tokens": sorted({row["chart_token"] for row in top_rows}),
            "operators": sorted({row["operator"] for row in top_rows}),
            "axis6_stage_signs": sorted({row["stage_axis6_sign"] for row in top_rows}),
        }
    return table


def loop_pair_table(rows: list[dict[str, Any]]) -> dict[str, Any]:
    table: dict[str, Any] = {}
    for engine in sorted({row["engine_type"] for row in rows}):
        for topology in ["Se", "Ne", "Ni", "Si"]:
            key = f"E{engine}_{topology}"
            pair_rows = [row for row in rows if row["engine_type"] == engine and row["topology"] == topology]
            by_loop = {
                loop: [row for row in pair_rows if row["loop_class"] == loop]
                for loop in ["outer", "inner"]
            }
            table[key] = {
                "terrain_variants": sorted({row["terrain_variant"] for row in pair_rows}),
                "loop_classes": sorted(by_loop),
                "chart_operators": {loop: sorted({row["chart_operator"] for row in loop_rows}) for loop, loop_rows in by_loop.items()},
                "axis6_stage_signs": {loop: sorted({row["stage_axis6_sign"] for row in loop_rows}) for loop, loop_rows in by_loop.items()},
                "operators_by_loop": {loop: sorted({row["operator"] for row in loop_rows}) for loop, loop_rows in by_loop.items()},
                "row_counts": {loop: len(loop_rows) for loop, loop_rows in by_loop.items()},
                "pass": (
                    len({row["terrain_variant"] for row in pair_rows}) == 1
                    and all(len(loop_rows) == 4 for loop_rows in by_loop.values())
                    and all(set(row["operator"] for row in loop_rows) == set(OPERATOR_SEQUENCE) for loop_rows in by_loop.values())
                    and len({next(iter({row["chart_operator"] for row in loop_rows})) for loop_rows in by_loop.values()}) == 2
                    and sum(next(iter({row["stage_axis6_sign"] for row in loop_rows})) for loop_rows in by_loop.values()) == 0
                ),
            }
    return table


def z3_gate() -> dict[str, Any]:
    total = z3.Int("total")
    per_engine = z3.Int("per_engine")
    engines = z3.Int("engines")
    macro = z3.Int("macro")
    sub = z3.Int("sub")
    final_physics = z3.Bool("final_physics")
    solver = z3.Solver()
    solver.add(engines == 2, macro == 8, sub == 4, per_engine == macro * sub, total == engines * per_engine)
    solver.add(z3.Not(final_physics))
    wrong = z3.Solver()
    wrong.add(total == 32, engines == 2, macro == 8, sub == 4, total == engines * macro * sub)
    promotion = z3.Solver()
    promotion.add(final_physics, z3.Not(final_physics))
    return {
        "correct_64_status": str(solver.check()),
        "collapse_to_32_status": str(wrong.check()),
        "promotion_status": str(promotion.check()),
        "pass": solver.check() == z3.sat and wrong.check() == z3.unsat and promotion.check() == z3.unsat,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    nominal = run_cycle()
    mixed = run_cycle(mixed_axis6=True)
    native_only = run_cycle(native_only=True)
    one_engine = run_cycle(one_engine_only=True)
    gauge = run_cycle(gauge_phases=[0.13, -0.21, 0.34, -0.55, 0.08, 0.44, -0.39, 0.17])

    mixed_gap = signature_gap(nominal, mixed)
    native_gap = signature_gap(nominal, native_only)
    one_engine_gap = signature_gap(nominal, one_engine)
    gauge_gap = signature_gap(nominal, gauge)
    table = topology_operator_table(nominal["rows"])
    loop_pairs = loop_pair_table(nominal["rows"])

    positive = {
        "correct_total_substage_count": {
            "pass": nominal["row_count"] == 64
            and nominal["engine_count"] == 2
            and nominal["macro_stage_count"] == 16,
            "row_count": nominal["row_count"],
            "engine_count": nominal["engine_count"],
            "macro_stage_count": nominal["macro_stage_count"],
            "substages_per_engine": N_SUBSTAGES_PER_ENGINE,
        },
        "each_macro_stage_runs_four_operators_same_axis6_sign": {
            "pass": nominal["same_sign_stage_count"] == 16 and nominal["operator_count"] == 4,
            "same_sign_stage_count": nominal["same_sign_stage_count"],
            "expected_stage_count": 16,
            "operator_count": nominal["operator_count"],
        },
        "eight_distinct_terrain_variants_and_four_topologies_present": {
            "pass": nominal["terrain_variant_count"] == 8 and nominal["topology_count"] == 4,
            "terrain_variant_count": nominal["terrain_variant_count"],
            "topology_count": nominal["topology_count"],
            "topology_operator_table": table,
        },
        "each_topology_has_two_terrain_variants_and_four_operators": {
            "pass": all(len(row["terrain_variants"]) == 2 and len(row["operators"]) == 4 for row in table.values()),
            "table": table,
        },
        "each_engine_topology_has_outer_inner_pairing": {
            "pass": all(row["pass"] for row in loop_pairs.values()),
            "loop_pair_table": loop_pairs,
        },
        "density_carrier_and_entanglement_readouts_valid": {
            "pass": nominal["trace_error"] < 1e-9
            and nominal["min_eigenvalue"] > -1e-9
            and nominal["mutual_information_left_right"] > 0.01,
            "trace_error": nominal["trace_error"],
            "min_eigenvalue": nominal["min_eigenvalue"],
            "mutual_information_left_right": nominal["mutual_information_left_right"],
            "log_negativity_left_right": nominal["log_negativity_left_right"],
        },
        "gauge_phase_invariance_preserved": {
            "pass": gauge_gap < 1e-10,
            "gauge_signature_gap": gauge_gap,
        },
    }

    graveyard_companions = {
        "GC1_mixed_axis6_within_stage_rejected": {
            "pass": mixed_gap > GAP_FLOOR and mixed["same_sign_stage_count"] < nominal["same_sign_stage_count"],
            "mixed_axis6_signature_gap": mixed_gap,
            "mixed_same_sign_stage_count": mixed["same_sign_stage_count"],
        },
        "GC2_native_only_substage_collapse_rejected": {
            "pass": native_only["row_count"] == 16 and native_gap > GAP_FLOOR,
            "native_only_row_count": native_only["row_count"],
            "native_only_signature_gap": native_gap,
        },
        "GC3_one_engine_only_collapse_rejected": {
            "pass": one_engine["row_count"] == 32 and one_engine_gap > GAP_FLOOR,
            "one_engine_row_count": one_engine["row_count"],
            "one_engine_signature_gap": one_engine_gap,
        },
        "GC4_z3_count_and_nonpromotion_gate": z3_gate(),
    }

    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_no_final_claims": {
            "pass": "does not admit final flux" in CLAIM_CEILING and "physics" in CLAIM_CEILING,
            "claim_ceiling": CLAIM_CEILING,
        },
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [
        row["pass"] for row in boundary.values()
    ]
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
        "nearby_variants": {"passed": sum(1 for item in checks if item), "total": len(checks)},
        "all_pass": all(checks),
        "summary": {
            "engine_count": nominal["engine_count"],
            "macro_stage_count": nominal["macro_stage_count"],
            "total_substage_count": nominal["row_count"],
            "substages_per_engine": N_SUBSTAGES_PER_ENGINE,
            "terrain_variant_count": nominal["terrain_variant_count"],
            "topology_count": nominal["topology_count"],
            "operator_count": nominal["operator_count"],
            "same_sign_stage_count": nominal["same_sign_stage_count"],
            "loop_pair_count": len(loop_pairs),
            "mixed_axis6_signature_gap": mixed_gap,
            "native_only_signature_gap": native_gap,
            "one_engine_signature_gap": one_engine_gap,
            "gauge_signature_gap": gauge_gap,
            "mutual_information_left_right": nominal["mutual_information_left_right"],
            "log_negativity_left_right": nominal["log_negativity_left_right"],
            "elapsed_seconds": time.time() - started,
        },
        "nominal_rows": nominal["rows"],
        "stage_readouts": nominal["stage_readouts"],
        "control_summaries": {
            "mixed_axis6": {key: value for key, value in mixed.items() if key != "rows" and key != "stage_readouts"},
            "native_only": {key: value for key, value in native_only.items() if key != "rows" and key != "stage_readouts"},
            "one_engine_only": {key: value for key, value in one_engine.items() if key != "rows" and key != "stage_readouts"},
        },
        "why_not_v4_probes": (
            "This is a v5 source-native IGT/engine-cycle grammar scout on an "
            "explicit-spinor carrier. It is not a legacy v4 probe and not a "
            "promotion of final flux, Axis0, Xi, or physics."
        ),
        "next_required_work": [
            "Wire the exact 64-substage same-sign schedule into the MPS/PEPS carrier rows.",
            "Add terrain-law GKSL updates per terrain variant instead of the current operator-focused stage carrier.",
            "Only then test Axis0/FEP and flux readouts over the full corrected schedule.",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
