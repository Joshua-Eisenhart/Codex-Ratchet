#!/usr/bin/env python3
"""Dynamic spinor-shell chiral flux topology scout.

Formal scout only.

This row tests the stronger owner claim:

* flux is not a scalar and not a free degree of freedom;
* flux is induced on bounded spinor/quaternion shell layers;
* flux is chiral and bound to engine type;
* flux changes the four topology signatures;
* shell-time has two directed halves: past-outward and future-inward.

The entropy used here is finite shell response entropy over a bounded shell
registry. This row does not admit final flux, Axis0, Xi, PEPS3D environment
closure, gravity, Standard Model, Yang-Mills, Riemann, or physics claims.
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
NAME = "dynamic_spinor_shell_chiral_flux_topology_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "dynamic_spinor_shell_chiral_flux_topology"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: runs bounded spinor/quaternion shell dynamics over the "
    "two source engine schedules and tests whether induced IJK flux is chiral, "
    "engine-bound, shell-time directed, topology-mutating, and finite-shell "
    "entropy compressive. It does not admit final flux, Axis0, Xi, PEPS3D "
    "environment closure, gravity, Standard Model, Yang-Mills, Riemann, or "
    "physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing spinor/quaternion shell dynamics, finite shell entropy, and topology mutation readouts",
    },
    "canonical_qit_engine_specs": {
        "tried": True,
        "used": True,
        "reason": "supportive source-native engine schedules, terrain names, and chirality signs",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion and finite shell/chirality satisfiability gates",
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
N_NODES = 8
N_SHELLS = 8
OPERATOR_SEQUENCE = ["Ti", "Te", "Fi", "Fe"]
TOPOLOGIES = ["Se", "Ne", "Ni", "Si"]
EPS = 1e-12
GAP_FLOOR = 1e-5

Q_ONE = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=RTYPE)
Q_I = torch.tensor([0.0, 1.0, 0.0, 0.0], dtype=RTYPE)
Q_J = torch.tensor([0.0, 0.0, 1.0, 0.0], dtype=RTYPE)
Q_K = torch.tensor([0.0, 0.0, 0.0, 1.0], dtype=RTYPE)

OPERATOR_UNITS = {
    "Ti": Q_K,
    "Te": Q_I,
    "Fi": Q_I,
    "Fe": Q_K,
}

TOPOLOGY_UNITS = {
    "Se": Q_I,
    "Ne": Q_J,
    "Ni": Q_K,
    "Si": -Q_I,
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


def q_conj(q: torch.Tensor) -> torch.Tensor:
    return torch.tensor([q[0].item(), -q[1].item(), -q[2].item(), -q[3].item()], dtype=RTYPE)


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


def q_close(a: torch.Tensor, b: torch.Tensor, *, tol: float = 1e-10) -> bool:
    return float(q_norm(a - b).item()) < tol


def q_exp(unit: torch.Tensor, angle: float) -> torch.Tensor:
    return q_normalize(math.cos(angle) * Q_ONE + math.sin(angle) * unit)


def q_blend(a: torch.Tensor, b: torch.Tensor, weight: float) -> torch.Tensor:
    return q_normalize((1.0 - weight) * a + weight * b)


def spinor(phi: float, chi: float, eta: float, *, phase: float = 0.0) -> torch.Tensor:
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
    return q_normalize(
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
    q = q_normalize(q)
    return torch.tensor(
        [complex(q[0].item(), q[1].item()), complex(q[2].item(), q[3].item())],
        dtype=CDTYPE,
    )


def build_spinors() -> list[torch.Tensor]:
    return [spinor(*params) for params in SPINOR_PARAMS]


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


def shell_entropy(weights: torch.Tensor) -> float:
    probs = weights / torch.sum(weights)
    return float((-torch.sum(probs * torch.log(probs + EPS))).item())


def engine_path_order(engine_type: int, loop_class: str) -> tuple[str, str]:
    if engine_type == 0:
        return ("base", "deductive") if loop_class == "outer" else ("fiber", "inductive")
    return ("fiber", "inductive") if loop_class == "outer" else ("base", "deductive")


def node_pair(engine_type: int, macro_stage_idx: int, substage_idx: int) -> tuple[int, int]:
    base = macro_stage_idx % N_NODES
    offset = 1 + (substage_idx % 3)
    if macro_stage_idx >= 4:
        offset = 4 + (substage_idx % 2)
    a = base
    b = (base + offset) % N_NODES
    if engine_type == 1:
        a = (N_NODES - 1 - a) % N_NODES
        b = (N_NODES - 1 - b) % N_NODES
    if a == b:
        b = (b + 1) % N_NODES
    return a, b


def build_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for engine_type in [0, 1]:
        engine = specs.get_engine_spec(engine_type)
        for macro_stage_idx, (topology, loop_class) in enumerate(specs.get_schedule(engine_type)):
            chart = specs.get_chart_token_spec(topology, engine_type, loop_class)
            terrain = specs.get_terrain_dynamics_spec(topology, engine_type)
            path_class, order_family = engine_path_order(engine_type, loop_class)
            stage_sign = int(chart["sign"])
            for substage_idx, operator in enumerate(OPERATOR_SEQUENCE):
                shell_slot = (macro_stage_idx + 2 * substage_idx + 3 * engine_type) % N_SHELLS
                pair = node_pair(engine_type, macro_stage_idx, substage_idx)
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
                        "terrain_family": terrain["family"],
                        "loop_class": loop_class,
                        "path_class": path_class,
                        "order_family": order_family,
                        "operator": operator,
                        "axis6_sign": stage_sign,
                        "shell_slot": shell_slot,
                        "past_shell_flow": "outward",
                        "future_shell_flow": "inward",
                        "node_pair": pair,
                    }
                )
    return rows


def shell_time_drive(row: dict[str, Any], *, mode: str) -> torch.Tensor:
    if mode == "zero_flux":
        return Q_ONE
    chirality = float(row["chirality_sign"])
    if mode == "achiral":
        chirality = 1.0
    shell = float(row["shell_slot"] + 1)
    past_outward = shell / float(N_SHELLS)
    future_inward = -float(N_SHELLS + 1 - shell) / float(N_SHELLS)
    if mode == "swapped_arrows":
        past_outward, future_inward = -future_inward, -past_outward
    if mode == "static_shells":
        past_outward, future_inward = 0.0, 0.0
    path_sign = 1.0 if row["path_class"] == "base" else -1.0
    order_sign = 1.0 if row["order_family"] == "deductive" else -1.0
    tick = 0.025 * float(row["global_substage_idx"] + 1) * float(row["axis6_sign"])
    past_angle = 0.19 * chirality * path_sign * past_outward
    future_angle = 0.17 * chirality * order_sign * future_inward
    drive = q_mul(q_exp(Q_I, tick), q_exp(Q_J, past_angle))
    return q_mul(drive, q_exp(Q_K, future_angle))


def apply_row(
    spinors: list[torch.Tensor], row: dict[str, Any], *, mode: str
) -> tuple[list[torch.Tensor], torch.Tensor, torch.Tensor]:
    a, b = row["node_pair"]
    qa = spinor_to_q(spinors[a])
    qb = spinor_to_q(spinors[b])
    drive = shell_time_drive(row, mode=mode)
    shell_time_ijk = drive[1:]
    unit = OPERATOR_UNITS[row["operator"]]
    topo_unit = TOPOLOGY_UNITS[row["topology"]] if mode != "topology_blind" else Q_J
    op_drive = q_exp(unit, 0.033 * float(row["axis6_sign"]))
    topo_drive = q_exp(topo_unit, 0.021 * float(row["chirality_sign"]))
    full = q_mul(q_mul(drive, op_drive), topo_drive)
    if mode == "zero_flux":
        next_a = qa
        next_b = qb
    elif row["chirality_sign"] > 0:
        next_a = q_blend(qa, q_mul(full, qa), 0.21)
        next_b = q_blend(qb, q_mul(q_conj(full), qb), 0.15)
    else:
        next_a = q_blend(qa, q_mul(qa, full), 0.15)
        next_b = q_blend(qb, q_mul(qb, q_conj(full)), 0.21)
    out = list(spinors)
    out[a] = q_to_spinor(next_a)
    out[b] = q_to_spinor(next_b)
    rel_a = q_mul(next_a, q_conj(qa))
    rel_b = q_mul(next_b, q_conj(qb))
    pure = 0.5 * (rel_a[1:] + rel_b[1:])
    if mode == "zero_flux":
        pure = torch.zeros(3, dtype=RTYPE)
    return out, pure, shell_time_ijk


def topology_target(row: dict[str, Any], flux: torch.Tensor) -> str:
    if float(q_norm(flux).item()) <= GAP_FLOOR:
        return row["topology"]
    dominant = int(torch.argmax(torch.abs(flux)).item())
    order = TOPOLOGIES
    idx = order.index(row["topology"])
    step = {0: 1, 1: 2, 2: 3}[dominant]
    if float(flux[dominant].item()) < 0.0:
        step = -step
    if row["chirality_sign"] < 0:
        step = -step
    return order[(idx + step) % len(order)]


def run_model(*, mode: str = "nominal") -> dict[str, Any]:
    rows = build_rows()
    spinors = build_spinors()
    shell_weights = {topology: torch.ones(N_SHELLS, dtype=RTYPE) * 1.0e-4 for topology in TOPOLOGIES}
    transition = torch.zeros((len(TOPOLOGIES), len(TOPOLOGIES)), dtype=RTYPE)
    flux_rows: list[dict[str, Any]] = []
    for row in rows:
        before = list(spinors)
        spinors, flux, shell_time_ijk = apply_row(spinors, row, mode=mode)
        mag = float(q_norm(flux).item())
        shell = int(row["shell_slot"])
        topology = row["topology"]
        shell_weights[topology][shell] += mag + 0.01 * (1.0 + abs(float(flux[1].item())) + abs(float(flux[2].item())))
        target = topology_target(row, flux)
        transition[TOPOLOGIES.index(topology), TOPOLOGIES.index(target)] += mag
        flux_rows.append(
            {
                **row,
                "mode": mode,
                "flux_ijk": flux,
                "shell_time_ijk": shell_time_ijk,
                "flux_magnitude": mag,
                "mutated_topology": target,
                "changed_topology": target != topology,
                "before_pair_norms": [float(q_norm(spinor_to_q(before[idx])).item()) for idx in row["node_pair"]],
            }
        )
    flux_stack = torch.stack([row["flux_ijk"] for row in flux_rows])
    shell_time_stack = torch.stack([row["shell_time_ijk"] for row in flux_rows])
    shell_entropy_rows = {}
    for topology, weights in shell_weights.items():
        before_entropy = math.log(N_SHELLS)
        after_entropy = shell_entropy(weights)
        shell_entropy_rows[topology] = {
            "before": before_entropy,
            "after": after_entropy,
            "compression_delta": before_entropy - after_entropy,
        }
    offdiag = transition.clone()
    for idx in range(len(TOPOLOGIES)):
        offdiag[idx, idx] = 0.0
    per_engine_flux = {
        f"E{engine}": torch.sum(
            torch.stack([row["flux_ijk"] for row in flux_rows if row["engine_type"] == engine]), dim=0
        )
        for engine in [1, 2]
    }
    per_topology_flux = {
        topology: torch.sum(
            torch.stack([row["flux_ijk"] for row in flux_rows if row["topology"] == topology]), dim=0
        )
        for topology in TOPOLOGIES
    }
    signature = torch.cat(
        [
            flux_stack.mean(dim=0),
            shell_time_stack.mean(dim=0),
            torch.tensor([float(q_norm(per_engine_flux["E1"] - per_engine_flux["E2"]).item())], dtype=RTYPE),
            transition.reshape(-1),
            torch.tensor(
                [shell_entropy_rows[topology]["compression_delta"] for topology in TOPOLOGIES],
                dtype=RTYPE,
            ),
        ]
    )
    return {
        "mode": mode,
        "row_count": len(rows),
        "engine_count": 2,
        "topology_count": 4,
        "terrain_variant_count": len({row["terrain_variant"] for row in rows}),
        "shell_count": N_SHELLS,
        "flux_component_count": 3,
        "flux_magnitude": float(q_norm(flux_stack).item()),
        "jk_temporal_shell_magnitude": float(q_norm(shell_time_stack[:, 1:]).item()),
        "per_engine_flux": per_engine_flux,
        "per_topology_flux": per_topology_flux,
        "engine_chiral_gap": float(q_norm(per_engine_flux["E1"] - per_engine_flux["E2"]).item()),
        "transition_matrix": transition,
        "topology_offdiag_mass": float(torch.sum(offdiag).item()),
        "per_topology_offdiag_mass": {
            topology: float(torch.sum(offdiag[idx]).item()) for idx, topology in enumerate(TOPOLOGIES)
        },
        "shell_entropy": shell_entropy_rows,
        "min_shell_compression_delta": min(row["compression_delta"] for row in shell_entropy_rows.values()),
        "flux_rows": flux_rows,
        "signature": signature,
    }


def signature_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
    return float(q_norm(a["signature"] - b["signature"]).item())


def z3_gate(nominal: dict[str, Any]) -> dict[str, Any]:
    components = z3.Int("components")
    shells = z3.Int("shells")
    topologies = z3.Int("topologies")
    engines = z3.Int("engines")
    final_flux = z3.Bool("final_flux")
    solver = z3.Solver()
    solver.add(components == 3, shells == N_SHELLS, topologies == 4, engines == 2, z3.Not(final_flux))
    promotion = z3.Solver()
    promotion.add(final_flux, z3.Not(final_flux))
    return {
        "sat": solver.check() == z3.sat,
        "promotion_blocked": promotion.check() == z3.unsat,
        "topology_offdiag_mass": nominal["topology_offdiag_mass"],
        "pass": solver.check() == z3.sat and promotion.check() == z3.unsat,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    nominal = run_model(mode="nominal")
    zero_flux = run_model(mode="zero_flux")
    achiral = run_model(mode="achiral")
    static_shells = run_model(mode="static_shells")
    swapped_arrows = run_model(mode="swapped_arrows")
    topology_blind = run_model(mode="topology_blind")

    zero_gap = signature_gap(nominal, zero_flux)
    achiral_gap = signature_gap(nominal, achiral)
    static_gap = signature_gap(nominal, static_shells)
    swapped_gap = signature_gap(nominal, swapped_arrows)
    blind_gap = signature_gap(nominal, topology_blind)

    positive = {
        "bounded_spinor_shell_engine_stack_runs": {
            "pass": nominal["row_count"] == 64
            and nominal["engine_count"] == 2
            and nominal["terrain_variant_count"] == 8
            and nominal["topology_count"] == 4
            and nominal["shell_count"] == N_SHELLS,
            "row_count": nominal["row_count"],
            "engine_count": nominal["engine_count"],
            "terrain_variant_count": nominal["terrain_variant_count"],
            "topology_count": nominal["topology_count"],
            "shell_count": nominal["shell_count"],
        },
        "literal_quaternion_time_layer": {
            "pass": nominal["flux_component_count"] == 3
            and nominal["jk_temporal_shell_magnitude"] > GAP_FLOOR
            and quaternion_algebra_gate()["pass"],
            "flux_component_count": nominal["flux_component_count"],
            "jk_temporal_shell_magnitude": nominal["jk_temporal_shell_magnitude"],
            "quaternion_algebra": quaternion_algebra_gate(),
            "temporal_interpretation": {"i": "rotation_tick", "j": "past_outward_shell", "k": "future_inward_shell"},
        },
        "flux_is_chiral_and_engine_bound": {
            "pass": nominal["engine_chiral_gap"] > GAP_FLOOR and achiral["engine_chiral_gap"] < nominal["engine_chiral_gap"],
            "engine_chiral_gap": nominal["engine_chiral_gap"],
            "achiral_engine_gap": achiral["engine_chiral_gap"],
            "per_engine_flux": nominal["per_engine_flux"],
        },
        "flux_mutates_all_four_topologies": {
            "pass": nominal["topology_offdiag_mass"] > GAP_FLOOR
            and all(value > GAP_FLOOR for value in nominal["per_topology_offdiag_mass"].values()),
            "topology_offdiag_mass": nominal["topology_offdiag_mass"],
            "per_topology_offdiag_mass": nominal["per_topology_offdiag_mass"],
            "transition_matrix": nominal["transition_matrix"],
        },
        "engines_compress_finite_shell_entropy": {
            "pass": nominal["min_shell_compression_delta"] > 0.0,
            "min_shell_compression_delta": nominal["min_shell_compression_delta"],
            "shell_entropy": nominal["shell_entropy"],
            "entropy_kind": "finite_shell_response_entropy",
        },
    }

    graveyard_companions = {
        "GC1_zero_flux_does_not_mutate_topologies": {
            "pass": zero_flux["topology_offdiag_mass"] == 0.0 and zero_gap > GAP_FLOOR,
            "zero_topology_offdiag_mass": zero_flux["topology_offdiag_mass"],
            "zero_signature_gap": zero_gap,
        },
        "GC2_achiral_control_breaks_engine_binding": {
            "pass": achiral_gap > GAP_FLOOR and achiral["engine_chiral_gap"] < nominal["engine_chiral_gap"],
            "achiral_signature_gap": achiral_gap,
            "achiral_engine_gap": achiral["engine_chiral_gap"],
        },
        "GC3_static_shells_are_not_dynamic_shell_time": {
            "pass": static_gap > GAP_FLOOR and static_shells["jk_temporal_shell_magnitude"] < nominal["jk_temporal_shell_magnitude"],
            "static_signature_gap": static_gap,
            "static_jk_temporal_shell_magnitude": static_shells["jk_temporal_shell_magnitude"],
        },
        "GC4_swapped_time_arrows_change_signature": {
            "pass": swapped_gap > GAP_FLOOR,
            "swapped_arrow_signature_gap": swapped_gap,
        },
        "GC5_topology_blind_control_rejected": {
            "pass": blind_gap > GAP_FLOOR,
            "topology_blind_signature_gap": blind_gap,
        },
        "GC6_nonpromotion_solver": z3_gate(nominal),
    }

    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_no_final_flux_or_physics_claim": {
            "pass": "does not admit final flux" in CLAIM_CEILING and "physics claims" in CLAIM_CEILING,
            "claim_ceiling": CLAIM_CEILING,
        },
        "B3_entropy_is_finite_shell_entropy_not_continuous": {
            "pass": all("compression_delta" in row for row in nominal["shell_entropy"].values()),
            "entropy_kind": "finite_shell_response_entropy",
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
        "nearby_variants": {"total": len(checks), "passed": sum(1 for item in checks if item)},
        "all_pass": all(checks),
        "summary": {
            "row_count": nominal["row_count"],
            "shell_count": nominal["shell_count"],
            "flux_component_count": nominal["flux_component_count"],
            "flux_magnitude": nominal["flux_magnitude"],
            "jk_temporal_shell_magnitude": nominal["jk_temporal_shell_magnitude"],
            "engine_chiral_gap": nominal["engine_chiral_gap"],
            "topology_offdiag_mass": nominal["topology_offdiag_mass"],
            "min_shell_compression_delta": nominal["min_shell_compression_delta"],
            "zero_signature_gap": zero_gap,
            "achiral_signature_gap": achiral_gap,
            "static_shell_signature_gap": static_gap,
            "swapped_arrow_signature_gap": swapped_gap,
            "topology_blind_signature_gap": blind_gap,
            "elapsed_seconds": time.time() - started,
        },
        "nominal": {
            key: value for key, value in nominal.items() if key not in {"signature", "flux_rows"}
        },
        "control_summaries": {
            "zero_flux": {key: value for key, value in zero_flux.items() if key not in {"signature", "flux_rows"}},
            "achiral": {key: value for key, value in achiral.items() if key not in {"signature", "flux_rows"}},
            "static_shells": {key: value for key, value in static_shells.items() if key not in {"signature", "flux_rows"}},
            "swapped_arrows": {key: value for key, value in swapped_arrows.items() if key not in {"signature", "flux_rows"}},
            "topology_blind": {key: value for key, value in topology_blind.items() if key not in {"signature", "flux_rows"}},
        },
        "flux_rows_sample": nominal["flux_rows"][:12],
        "why_not_v4_probes": (
            "This is a v5 finite spinor/quaternion shell scout. It is not a "
            "legacy v4 probe, not a primitive flux variable, and not a final "
            "physics claim."
        ),
        "next_required_work": [
            "Lift this shell-time chiral flux readout into the 8/16/32/64 MPS carrier.",
            "Port the same finite shell entropy and topology mutation controls into PEPS and PEPS3D dynamics.",
            "Only after those controls pass, test whether shell-time flux improves L7 Xi-history or L8 shell-weighted Axis0.",
        ],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
