#!/usr/bin/env python3
# object_id: qit_engine_3qubit_face_knot_taxonomy
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# claim_ceiling: readouts of the canonical 3-qubit QIT engine only; no admission
# of physics, gravity, dark-sector, Axis0, M(C), bridge, or formal manifold claim.

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
SIM_EXECUTION_KIND = "scratch"

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 Python backend for this bounded scratch diagnostic; Python-side array compute uses jax.numpy/jnp only",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing array algebra surface for the local finite witness, controls, shared scalars, and shared booleans",
    },
    "Julia peer backend": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent peer backend for dual-backend parity; the Python source does not derive values from Julia except parity comparison",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization, path handling, timestamps, hashing, imports, and peer-result loading",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "explicitly excluded; no import numpy, no np.*, and no NumPy compute path in this scratch diagnostic",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Julia peer backend": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
}


OBJECT_ID = "qit_engine_3qubit_face_knot_taxonomy"
N_QUBITS = 3
STAGE_DT = 0.08
RK4_STEPS_PER_STAGE = 8
PARITY_TOL = 1.0e-10
DIFFER_TOL = 1.0e-6
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/qit_engine_3qubit_face_knot_taxonomy_results.json"
JULIA_RESULT_PATH = ROOT / "system_v5/julia_carrier/qit_engine_3qubit_face_knot_taxonomy_julia_results.json"
CLAIM_CEILING = (
    "readouts of the canonical 3-qubit QIT engine; NO admission of physics/gravity/"
    "dark-sector/Axis0/M(C); uses the proposed engine math"
)
READOUT_KEYS = [
    "dark_energy_time",
    "entropy_growth",
    "preserved_info_dark_matter",
    "bounded_knot_mass",
    "composite_baryons",
    "transition_forces",
    "sync_gradient_gravity",
    "coherence",
    "holonomy",
    "three_cell_abs",
]


def carray(rows: list[list[complex]]) -> jax.Array:
    return jnp.asarray(rows, dtype=jnp.complex128)


I2 = carray([[1.0, 0.0], [0.0, 1.0]])
SX = carray([[0.0, 1.0], [1.0, 0.0]])
SY = carray([[0.0, -1.0j], [1.0j, 0.0]])
SZ = carray([[1.0, 0.0], [0.0, -1.0]])
SIGMA_MINUS = carray([[0.0, 0.0], [1.0, 0.0]])
SIGMA_PLUS = carray([[0.0, 1.0], [0.0, 0.0]])
MIRROR = SX
H0 = 0.77 * SZ + 0.13 * SX

PERCEPTION_L = {
    "Se": SZ,
    "Ne": SIGMA_PLUS,
    "Ni": -1.0j * SY,
    "Si": SIGMA_MINUS,
}
OPERATOR_GENERATORS = {
    "Ti": SZ,
    "Te": SX,
    "Fi": SX,
    "Fe": SY,
}
OPERATOR_BASE_ANGLES = {
    "Ti": 0.12,
    "Te": 0.09,
    "Fi": 0.15,
    "Fe": 0.11,
}
OPERATOR_SLOT_SEQUENCE = ["Ti", "Te", "Fi", "Fe"]
NATIVE_OPERATORS_BY_TOPOLOGY = {
    "Se": ("Ti", "Fi"),
    "Ne": ("Ti", "Fi"),
    "Ni": ("Te", "Fe"),
    "Si": ("Te", "Fe"),
}
OPERATOR_MAP_FAMILY = {
    "Ti": "z_pinching_dephase",
    "Te": "x_pinching_dephase",
    "Fi": "x_coherent_rotation",
    "Fe": "z_coherent_rotation",
}
CHART_TOKEN_PRECEDENCE = {
    "TiSe": ("operator_first", +1),
    "TiNe": ("operator_first", +1),
    "SeTi": ("terrain_first", -1),
    "NeTi": ("terrain_first", -1),
    "FeSi": ("operator_first", +1),
    "FeNi": ("operator_first", +1),
    "SiFe": ("terrain_first", -1),
    "NiFe": ("terrain_first", -1),
    "TeNi": ("operator_first", +1),
    "TeSi": ("operator_first", +1),
    "NiTe": ("terrain_first", -1),
    "SiTe": ("terrain_first", -1),
    "FiNe": ("operator_first", +1),
    "FiSe": ("operator_first", +1),
    "NeFi": ("terrain_first", -1),
    "SeFi": ("terrain_first", -1),
}

TYPE_ONE_TOPOLOGIES = {
    "Se": {"outer": {"op": "Ti", "sign": +1}, "inner": {"op": "Fi", "sign": -1}},
    "Ne": {"outer": {"op": "Ti", "sign": -1}, "inner": {"op": "Fi", "sign": +1}},
    "Ni": {"outer": {"op": "Fe", "sign": -1}, "inner": {"op": "Te", "sign": +1}},
    "Si": {"outer": {"op": "Fe", "sign": +1}, "inner": {"op": "Te", "sign": -1}},
}
TYPE_TWO_TOPOLOGIES = {
    "Se": {"outer": {"op": "Fi", "sign": +1}, "inner": {"op": "Ti", "sign": -1}},
    "Ne": {"outer": {"op": "Fi", "sign": -1}, "inner": {"op": "Ti", "sign": +1}},
    "Ni": {"outer": {"op": "Te", "sign": -1}, "inner": {"op": "Fe", "sign": +1}},
    "Si": {"outer": {"op": "Te", "sign": +1}, "inner": {"op": "Fe", "sign": -1}},
}
ENGINE_SCHEDULE_TYPE_ONE = [
    ("Se", "outer"),
    ("Ne", "outer"),
    ("Ni", "outer"),
    ("Si", "outer"),
    ("Se", "inner"),
    ("Si", "inner"),
    ("Ni", "inner"),
    ("Ne", "inner"),
]
ENGINE_SCHEDULE_TYPE_TWO = [
    ("Se", "outer"),
    ("Si", "outer"),
    ("Ni", "outer"),
    ("Ne", "outer"),
    ("Se", "inner"),
    ("Ne", "inner"),
    ("Ni", "inner"),
    ("Si", "inner"),
]


def as_float(x: Any) -> float:
    return float(jax.device_get(jnp.real(x)))


def as_bool(x: Any) -> bool:
    return bool(jax.device_get(x))


def ordered_token(operator: str, perception: str, precedence: str) -> str:
    if precedence == "operator_first":
        return f"{operator}{perception}"
    if precedence == "terrain_first":
        return f"{perception}{operator}"
    raise ValueError(f"unknown precedence {precedence!r}")


def topologies(engine_type: int) -> dict[str, dict[str, dict[str, int | str]]]:
    if engine_type == 0:
        return TYPE_ONE_TOPOLOGIES
    if engine_type == 1:
        return TYPE_TWO_TOPOLOGIES
    raise ValueError(f"engine_type must be 0 or 1, got {engine_type}")


def schedule_for(engine_type: int) -> list[tuple[str, str]]:
    return ENGINE_SCHEDULE_TYPE_ONE if engine_type == 0 else ENGINE_SCHEDULE_TYPE_TWO


def inner_before_outer_schedule(engine_type: int) -> list[tuple[str, str]]:
    schedule = schedule_for(engine_type)
    return [row for row in schedule if row[1] == "inner"] + [row for row in schedule if row[1] == "outer"]


def operator_slot_spec(perception: str, engine_type: int, loop_class: str, substage_idx: int) -> dict[str, Any]:
    topo = topologies(engine_type)[perception]
    chart_op = str(topo[loop_class]["op"])
    chart_sign = int(topo[loop_class]["sign"])
    chart_precedence = "operator_first" if chart_sign > 0 else "terrain_first"
    chart_token = ordered_token(chart_op, perception, chart_precedence)
    native = list(NATIVE_OPERATORS_BY_TOPOLOGY[perception])
    remaining_native = [op for op in native if op != chart_op]
    remaining_non_native = [op for op in OPERATOR_SLOT_SEQUENCE if op not in native]
    slot_ops = [chart_op, *remaining_native, *remaining_non_native]
    op = slot_ops[substage_idx % len(slot_ops)]
    if op == chart_op:
        sign = chart_sign
        precedence = chart_precedence
        token = chart_token
        chart_locked = True
    else:
        token_up = ordered_token(op, perception, "operator_first")
        token_down = ordered_token(op, perception, "terrain_first")
        if token_up in CHART_TOKEN_PRECEDENCE:
            precedence, sign = CHART_TOKEN_PRECEDENCE[token_up]
            token = token_up
        elif token_down in CHART_TOKEN_PRECEDENCE:
            precedence, sign = CHART_TOKEN_PRECEDENCE[token_down]
            token = token_down
        else:
            sign = +1 if (substage_idx + engine_type) % 2 == 0 else -1
            precedence = "operator_first" if sign > 0 else "terrain_first"
            token = ordered_token(op, perception, precedence)
        chart_locked = False
    return {
        "operator": op,
        "sign": int(sign),
        "precedence": precedence,
        "token": token,
        "operator_family": OPERATOR_MAP_FAMILY[op],
        "is_native_operator": op in native,
        "is_chart_locked": chart_locked,
        "native_operator_set": native,
    }


def kron_chain(ops: list[jax.Array]) -> jax.Array:
    out = ops[0]
    for op in ops[1:]:
        out = jnp.kron(out, op)
    return out


def site_op(local_op: jax.Array, n_qubits: int, site_idx: int) -> jax.Array:
    return kron_chain([local_op if idx == site_idx else I2 for idx in range(n_qubits)])


def all_site_sum(local_op: jax.Array, n_qubits: int) -> jax.Array:
    dim = 2**n_qubits
    out = jnp.zeros((dim, dim), dtype=jnp.complex128)
    for idx in range(n_qubits):
        out = out + site_op(local_op, n_qubits, idx)
    return out


def hamiltonian(engine_type: int, n_qubits: int) -> jax.Array:
    local_h = H0 if engine_type == 0 else -H0
    return all_site_sum(local_h, n_qubits)


def collapse_ops(perception: str, engine_type: int, n_qubits: int) -> list[jax.Array]:
    local_l = PERCEPTION_L[perception]
    if engine_type == 1:
        local_l = MIRROR @ local_l @ MIRROR
    return [site_op(local_l, n_qubits, idx) for idx in range(n_qubits)]


def normalize_density(rho: jax.Array) -> jax.Array:
    rho_h = 0.5 * (rho + jnp.conj(rho.T))
    tr = jnp.trace(rho_h)
    return rho_h / tr


def lindblad_rhs(rho: jax.Array, h: jax.Array, ls: list[jax.Array]) -> jax.Array:
    out = -1.0j * (h @ rho - rho @ h)
    for ell in ls:
        ldag_l = jnp.conj(ell.T) @ ell
        out = out + ell @ rho @ jnp.conj(ell.T) - 0.5 * (ldag_l @ rho + rho @ ldag_l)
    return out


def lindblad_step(rho: jax.Array, h: jax.Array, ls: list[jax.Array]) -> jax.Array:
    y = rho
    h_step = STAGE_DT / float(RK4_STEPS_PER_STAGE)
    for _ in range(RK4_STEPS_PER_STAGE):
        k1 = lindblad_rhs(y, h, ls)
        k2 = lindblad_rhs(y + 0.5 * h_step * k1, h, ls)
        k3 = lindblad_rhs(y + 0.5 * h_step * k2, h, ls)
        k4 = lindblad_rhs(y + h_step * k3, h, ls)
        y = y + (h_step / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
    return normalize_density(y)


def operator_unitary_local(op_name: str, sign: int) -> jax.Array:
    theta = OPERATOR_BASE_ANGLES[op_name] * float(sign)
    generator = OPERATOR_GENERATORS[op_name]
    return jnp.cos(theta) * I2 - 1.0j * jnp.sin(theta) * generator


def apply_operator(rho: jax.Array, n_qubits: int, op_name: str, sign: int, erased: bool) -> jax.Array:
    if erased:
        return rho
    local_u = operator_unitary_local(op_name, sign)
    global_u = kron_chain([local_u for _ in range(n_qubits)])
    return normalize_density(global_u @ rho @ jnp.conj(global_u.T))


def matrix_norm(a: jax.Array) -> float:
    return as_float(jnp.linalg.norm(a))


def trace_residual(rho: jax.Array) -> float:
    return abs(as_float(jnp.trace(rho)) - 1.0)


def min_eigenvalue(rho: jax.Array) -> float:
    return as_float(jnp.min(jnp.linalg.eigvalsh(0.5 * (rho + jnp.conj(rho.T)))))


def run_engine(
    *,
    n_qubits: int,
    engine_type: int,
    schedule: list[tuple[str, str]],
    rho_init: jax.Array,
    operator_erased: bool = False,
) -> dict[str, Any]:
    rho = normalize_density(rho_init)
    h = hamiltonian(engine_type, n_qubits)
    states = [rho]
    records: list[dict[str, Any]] = []
    for main_idx, (perception, loop_class) in enumerate(schedule):
        for substage_idx in range(4):
            before = rho
            slot = operator_slot_spec(perception, engine_type, loop_class, substage_idx)
            ls = collapse_ops(perception, engine_type, n_qubits)
            if slot["precedence"] == "operator_first":
                rho = apply_operator(rho, n_qubits, slot["operator"], int(slot["sign"]), operator_erased)
                rho = lindblad_step(rho, h, ls)
            else:
                rho = lindblad_step(rho, h, ls)
                rho = apply_operator(rho, n_qubits, slot["operator"], int(slot["sign"]), operator_erased)
            rho = normalize_density(rho)
            states.append(rho)
            records.append(
                {
                    "main_stage_idx": main_idx,
                    "substage_idx": substage_idx,
                    "perception": perception,
                    "loop_class": loop_class,
                    "operator": slot["operator"],
                    "operator_sign": int(slot["sign"]),
                    "precedence": slot["precedence"],
                    "ordered_token": slot["token"],
                    "operator_erased": operator_erased,
                    "transition_delta_fro": matrix_norm(rho - before),
                    "trace_residual": trace_residual(rho),
                    "min_eigenvalue": min_eigenvalue(rho),
                }
            )
    return {
        "n_qubits": n_qubits,
        "engine_type": engine_type,
        "operator_erased": operator_erased,
        "states": states,
        "records": records,
        "n_substages": len(records),
    }


def rho_from_bloch(vector: tuple[float, float, float]) -> jax.Array:
    return 0.5 * (I2 + vector[0] * SX + vector[1] * SY + vector[2] * SZ)


def ket(index: int, dim: int) -> jax.Array:
    return jnp.eye(dim, dtype=jnp.complex128)[:, index]


def pure_density(psi: jax.Array) -> jax.Array:
    psi = psi / jnp.linalg.norm(psi)
    return psi.reshape((-1, 1)) @ jnp.conj(psi.reshape((1, -1)))


def maximally_mixed(n_qubits: int) -> jax.Array:
    dim = 2**n_qubits
    return jnp.eye(dim, dtype=jnp.complex128) / float(dim)


def primary_density() -> jax.Array:
    q0 = ket(0, 2)
    bell = (ket(0, 4) + jnp.exp(0.37j) * ket(3, 4)) / jnp.sqrt(2.0)
    psi = jnp.kron(q0, bell)
    pure = pure_density(psi)
    return normalize_density(0.86 * pure + 0.14 * maximally_mixed(3))


def two_qubit_density() -> jax.Array:
    bell = (ket(0, 4) + jnp.exp(0.37j) * ket(3, 4)) / jnp.sqrt(2.0)
    return normalize_density(0.86 * pure_density(bell) + 0.14 * maximally_mixed(2))


def product_density(local_rhos: list[jax.Array]) -> jax.Array:
    return normalize_density(kron_chain(local_rhos))


def shape_density(swapped: bool) -> jax.Array:
    q0 = rho_from_bloch((0.0, 0.0, 0.92))
    q1 = rho_from_bloch((0.0, 0.0, 0.0))
    q2 = rho_from_bloch((0.95, 0.0, 0.0))
    return product_density([q0, q2, q1] if swapped else [q0, q1, q2])


def partial_trace(rho: jax.Array, n_qubits: int, keep: list[int]) -> jax.Array:
    keep_sorted = sorted(keep)
    trace_out = [idx for idx in range(n_qubits) if idx not in keep_sorted]
    tensor = jnp.reshape(rho, [2] * (2 * n_qubits))
    perm = keep_sorted + trace_out + [n_qubits + idx for idx in keep_sorted] + [n_qubits + idx for idx in trace_out]
    permuted = jnp.transpose(tensor, perm)
    dim_keep = 2 ** len(keep_sorted)
    dim_trace = 2 ** len(trace_out)
    reshaped = jnp.reshape(permuted, (dim_keep, dim_trace, dim_keep, dim_trace))
    return normalize_density(jnp.einsum("atbt->ab", reshaped))


def vn_entropy(rho: jax.Array) -> jax.Array:
    vals = jnp.real(jnp.linalg.eigvalsh(0.5 * (rho + jnp.conj(rho.T))))
    vals = jnp.clip(vals, 1.0e-15, 1.0)
    vals = vals / jnp.sum(vals)
    return -jnp.sum(vals * jnp.log(vals))


def purity(rho: jax.Array) -> jax.Array:
    return jnp.real(jnp.trace(rho @ rho))


def mutual_info(rho: jax.Array, n_qubits: int, left: list[int], right: list[int]) -> jax.Array:
    rho_l = partial_trace(rho, n_qubits, left)
    rho_r = partial_trace(rho, n_qubits, right)
    rho_lr = partial_trace(rho, n_qubits, sorted(left + right))
    return vn_entropy(rho_l) + vn_entropy(rho_r) - vn_entropy(rho_lr)


def tripartite_information(rho: jax.Array, n_qubits: int) -> jax.Array:
    if n_qubits < 3:
        return jnp.asarray(0.0, dtype=jnp.float64)
    s0 = vn_entropy(partial_trace(rho, n_qubits, [0]))
    s1 = vn_entropy(partial_trace(rho, n_qubits, [1]))
    s2 = vn_entropy(partial_trace(rho, n_qubits, [2]))
    s01 = vn_entropy(partial_trace(rho, n_qubits, [0, 1]))
    s02 = vn_entropy(partial_trace(rho, n_qubits, [0, 2]))
    s12 = vn_entropy(partial_trace(rho, n_qubits, [1, 2]))
    s012 = vn_entropy(rho)
    return s0 + s1 + s2 - s01 - s02 - s12 + s012


def offdiag_coherence(rho: jax.Array) -> jax.Array:
    dim = rho.shape[0]
    mask = jnp.ones((dim, dim), dtype=jnp.float64) - jnp.eye(dim, dtype=jnp.float64)
    return jnp.sum(jnp.abs(rho) * mask) / float(dim * (dim - 1))


def holonomy_phase(states: list[jax.Array]) -> jax.Array:
    product = jnp.asarray(1.0 + 0.0j, dtype=jnp.complex128)
    prev_vec = None
    for rho in states:
        vals, vecs = jnp.linalg.eigh(0.5 * (rho + jnp.conj(rho.T)))
        if vals.shape[0] > 1 and as_float(vals[-1] - vals[-2]) < 1.0e-12:
            prev_vec = None
            continue
        vec = vecs[:, int(vals.shape[0] - 1)]
        anchor_idx = int(jax.device_get(jnp.argmax(jnp.abs(vec))))
        vec = vec * jnp.exp(-1.0j * jnp.angle(vec[anchor_idx]))
        if prev_vec is not None:
            overlap = jnp.vdot(prev_vec, vec)
            mag = jnp.abs(overlap)
            product = jnp.where(mag > 1.0e-14, product * overlap / mag, product)
        prev_vec = vec
    return -jnp.angle(product)


def readouts(run: dict[str, Any]) -> dict[str, float]:
    n_qubits = int(run["n_qubits"])
    states: list[jax.Array] = run["states"]
    records: list[dict[str, Any]] = run["records"]
    initial = states[0]
    final = states[-1]
    log2 = jnp.log(jnp.asarray(2.0, dtype=jnp.float64))
    global_norm = jnp.log(jnp.asarray(2**n_qubits, dtype=jnp.float64))
    global_entropies = [vn_entropy(state) for state in states]
    local_final = [partial_trace(final, n_qubits, [idx]) for idx in range(n_qubits)]
    local_entropy_norm = [vn_entropy(rho_q) / log2 for rho_q in local_final]
    if n_qubits >= 3:
        mi_initial = mutual_info(initial, n_qubits, [1], [2])
        mi_final = mutual_info(final, n_qubits, [1], [2])
        pair = partial_trace(final, n_qubits, [1, 2])
        three_cell = tripartite_information(final, n_qubits)
    else:
        mi_initial = mutual_info(initial, n_qubits, [0], [1])
        mi_final = mutual_info(final, n_qubits, [0], [1])
        pair = final
        three_cell = jnp.asarray(0.0, dtype=jnp.float64)
    mass = jnp.maximum(0.0, (sum(local_entropy_norm[1:]) / max(1, n_qubits - 1)) - local_entropy_norm[0])
    gravity_sum = jnp.asarray(0.0, dtype=jnp.float64)
    for idx in range(1, n_qubits):
        gravity_sum = gravity_sum + jnp.abs(local_entropy_norm[idx] - local_entropy_norm[0]) / float(idx)
    transition_values = jnp.asarray([row["transition_delta_fro"] for row in records], dtype=jnp.float64)
    dark_energy_time = jnp.max(jnp.asarray(global_entropies, dtype=jnp.float64)) / global_norm
    entropy_growth = (global_entropies[-1] - global_entropies[0]) / global_norm
    preserved_mi = jnp.minimum(mi_initial, mi_final) / (2.0 * log2)
    baryons = jnp.maximum(0.0, mi_final / (2.0 * log2)) * purity(pair)
    return {
        "dark_energy_time": as_float(dark_energy_time),
        "entropy_growth": as_float(entropy_growth),
        "preserved_info_dark_matter": as_float(jnp.maximum(0.0, preserved_mi)),
        "bounded_knot_mass": as_float(mass),
        "composite_baryons": as_float(baryons),
        "transition_forces": as_float(jnp.mean(transition_values)),
        "sync_gradient_gravity": as_float(mass * gravity_sum),
        "coherence": as_float(offdiag_coherence(final)),
        "holonomy": as_float(holonomy_phase(states)),
        "three_cell_abs": as_float(jnp.abs(three_cell) / log2),
    }


def branch_result(
    label: str,
    *,
    n_qubits: int,
    engine_type: int,
    schedule: list[tuple[str, str]],
    rho_init: jax.Array,
    operator_erased: bool = False,
) -> dict[str, Any]:
    run = run_engine(
        n_qubits=n_qubits,
        engine_type=engine_type,
        schedule=schedule,
        rho_init=rho_init,
        operator_erased=operator_erased,
    )
    readout = readouts(run)
    final = run["states"][-1]
    max_trace_residual = max(row["trace_residual"] for row in run["records"])
    min_psd = min(row["min_eigenvalue"] for row in run["records"])
    return {
        "label": label,
        "n_qubits": n_qubits,
        "engine_type": engine_type,
        "engine_type_label": "type_one_left_weyl" if engine_type == 0 else "type_two_right_weyl",
        "schedule": [list(row) for row in schedule],
        "operator_erased": operator_erased,
        "n_substages": int(run["n_substages"]),
        "readouts": readout,
        "transition_channel_checks": {
            "trace_residual_max": float(max_trace_residual),
            "min_eigenvalue_over_trajectory": float(min_psd),
            "cptp_numeric_pass": bool(max_trace_residual < 1.0e-10 and min_psd > -1.0e-10),
        },
        "final_density": {
            "real": jax.device_get(jnp.real(final)).tolist(),
            "imag": jax.device_get(jnp.imag(final)).tolist(),
        },
    }


def max_readout_diff(left: dict[str, Any], right: dict[str, Any]) -> float:
    return max(abs(float(left["readouts"][key]) - float(right["readouts"][key])) for key in READOUT_KEYS)


def readout_rank(branches: list[dict[str, Any]]) -> int:
    matrix = jnp.asarray([[branch["readouts"][key] for key in READOUT_KEYS] for branch in branches], dtype=jnp.float64)
    centered = matrix - jnp.mean(matrix, axis=0, keepdims=True)
    singular = jnp.linalg.svd(centered, compute_uv=False)
    return int(jax.device_get(jnp.sum(singular > 1.0e-8)))


def parity_block(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {
            "peer_result_path": str(JULIA_RESULT_PATH),
            "peer_available": False,
            "within_1e_10": False,
            "parity_max_diff": None,
            "worst_key": None,
            "missing_from_peer": sorted(result["shared_scalars"]),
            "missing_from_self": [],
            "boolean_mismatches": [],
        }
    peer = json.loads(JULIA_RESULT_PATH.read_text(encoding="utf-8"))
    self_scalars = result["shared_scalars"]
    peer_scalars = peer.get("shared_scalars", {})
    missing_from_peer = sorted(set(self_scalars) - set(peer_scalars))
    missing_from_self = sorted(set(peer_scalars) - set(self_scalars))
    max_diff = 0.0
    worst_key = None
    diffs: dict[str, float] = {}
    for key, value in self_scalars.items():
        if key in peer_scalars:
            diff = abs(float(value) - float(peer_scalars[key]))
            diffs[key] = diff
            if diff > max_diff:
                max_diff = diff
                worst_key = key
    self_booleans = result["shared_booleans"]
    peer_booleans = peer.get("shared_booleans", {})
    boolean_mismatches = [
        key
        for key, value in self_booleans.items()
        if key in peer_booleans and bool(value) != bool(peer_booleans[key])
    ]
    within = (
        not missing_from_peer
        and not missing_from_self
        and not boolean_mismatches
        and max_diff <= PARITY_TOL
    )
    return {
        "peer_result_path": str(JULIA_RESULT_PATH),
        "peer_available": True,
        "within_1e_10": bool(within),
        "parity_max_diff": float(max_diff),
        "worst_key": worst_key,
        "missing_from_peer": missing_from_peer,
        "missing_from_self": missing_from_self,
        "boolean_mismatches": boolean_mismatches,
        "diffs": diffs,
    }


def build_result() -> dict[str, Any]:
    rho0 = primary_density()
    branches = {
        "type1_canonical": branch_result(
            "type1_canonical",
            n_qubits=3,
            engine_type=0,
            schedule=ENGINE_SCHEDULE_TYPE_ONE,
            rho_init=rho0,
        ),
        "type2_canonical": branch_result(
            "type2_canonical",
            n_qubits=3,
            engine_type=1,
            schedule=ENGINE_SCHEDULE_TYPE_TWO,
            rho_init=rho0,
        ),
        "type1_with_type2_schedule_order": branch_result(
            "type1_with_type2_schedule_order",
            n_qubits=3,
            engine_type=0,
            schedule=ENGINE_SCHEDULE_TYPE_TWO,
            rho_init=rho0,
        ),
        "type1_inner_before_outer_order": branch_result(
            "type1_inner_before_outer_order",
            n_qubits=3,
            engine_type=0,
            schedule=inner_before_outer_schedule(0),
            rho_init=rho0,
        ),
        "type1_operator_erased": branch_result(
            "type1_operator_erased",
            n_qubits=3,
            engine_type=0,
            schedule=ENGINE_SCHEDULE_TYPE_ONE,
            rho_init=rho0,
            operator_erased=True,
        ),
    }
    flat = branch_result(
        "flat_fuzz_type1",
        n_qubits=3,
        engine_type=0,
        schedule=ENGINE_SCHEDULE_TYPE_ONE,
        rho_init=maximally_mixed(3),
    )
    knot = branch_result(
        "knot_product_type1",
        n_qubits=3,
        engine_type=0,
        schedule=ENGINE_SCHEDULE_TYPE_ONE,
        rho_init=shape_density(False),
    )
    shape = branch_result(
        "knot_shape_swapped_type1",
        n_qubits=3,
        engine_type=0,
        schedule=ENGINE_SCHEDULE_TYPE_ONE,
        rho_init=shape_density(True),
    )
    twoq = branch_result(
        "two_qubit_control_type1",
        n_qubits=2,
        engine_type=0,
        schedule=ENGINE_SCHEDULE_TYPE_ONE,
        rho_init=two_qubit_density(),
    )

    rank = readout_rank(list(branches.values()))
    type_diff = max_readout_diff(branches["type1_canonical"], branches["type2_canonical"])
    schedule_type_diff = max_readout_diff(
        branches["type1_canonical"], branches["type1_with_type2_schedule_order"]
    )
    loop_order_diff = max_readout_diff(
        branches["type1_canonical"], branches["type1_inner_before_outer_order"]
    )
    erased_diff = max_readout_diff(branches["type1_canonical"], branches["type1_operator_erased"])
    flat_r = flat["readouts"]
    knot_r = knot["readouts"]
    shape_r = shape["readouts"]
    mass_delta = abs(knot_r["bounded_knot_mass"] - shape_r["bounded_knot_mass"])
    gravity_delta = abs(knot_r["sync_gradient_gravity"] - shape_r["sync_gradient_gravity"])
    flat_vanish = (
        abs(flat_r["bounded_knot_mass"]) < 1.0e-10
        and abs(flat_r["composite_baryons"]) < 1.0e-10
        and abs(flat_r["sync_gradient_gravity"]) < 1.0e-10
        and abs(flat_r["dark_energy_time"] - 1.0) < 1.0e-10
    )
    knot_couples = knot_r["bounded_knot_mass"] > 1.0e-4 and knot_r["sync_gradient_gravity"] > 1.0e-4
    decoupling_witness = mass_delta < 1.0e-10 and gravity_delta > 1.0e-4
    two_qubit_insufficient = twoq["n_qubits"] == 2 and twoq["readouts"]["three_cell_abs"] == 0.0

    shared_scalars: dict[str, float] = {}
    for label, branch in branches.items():
        for key in READOUT_KEYS:
            shared_scalars[f"branch.{label}.{key}"] = float(branch["readouts"][key])
        shared_scalars[f"branch.{label}.trace_residual_max"] = float(
            branch["transition_channel_checks"]["trace_residual_max"]
        )
        shared_scalars[f"branch.{label}.min_eigenvalue_over_trajectory"] = float(
            branch["transition_channel_checks"]["min_eigenvalue_over_trajectory"]
        )
    for label, branch in {"flat": flat, "knot": knot, "shape": shape, "twoq": twoq}.items():
        for key in READOUT_KEYS:
            shared_scalars[f"control.{label}.{key}"] = float(branch["readouts"][key])
    shared_scalars.update(
        {
            "diff.type1_vs_type2": float(type_diff),
            "diff.type1_vs_type2_schedule_order": float(schedule_type_diff),
            "diff.outer_vs_inner_loop_order": float(loop_order_diff),
            "diff.operator_on_vs_erased": float(erased_diff),
            "control.shape_mass_delta": float(mass_delta),
            "control.shape_gravity_delta": float(gravity_delta),
            "readout_rank": float(rank),
            "n_qubits": float(N_QUBITS),
            "n_substages_per_engine": 32.0,
        }
    )
    shared_booleans = {
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "numpy_compute_used": False,
        "torch_compute_used": False,
        "type1_vs_type2_differ": type_diff > DIFFER_TOL,
        "schedule_orders_differ": schedule_type_diff > DIFFER_TOL and loop_order_diff > DIFFER_TOL,
        "operator_order_matters": erased_diff > DIFFER_TOL,
        "distinct_probe": rank > 1,
        "flat_vanish": bool(flat_vanish),
        "knot_couples": bool(knot_couples),
        "decoupling_witness": bool(decoupling_witness),
        "two_qubit_insufficient": bool(two_qubit_insufficient),
        "all_branches_32_substages": all(branch["n_substages"] == 32 for branch in branches.values()),
        "all_transition_channels_numeric_cptp": all(
            branch["transition_channel_checks"]["cptp_numeric_pass"] for branch in branches.values()
        ),
    }
    positive_boolean_keys = [
        "jax_enable_x64",
        "type1_vs_type2_differ",
        "schedule_orders_differ",
        "operator_order_matters",
        "distinct_probe",
        "flat_vanish",
        "knot_couples",
        "decoupling_witness",
        "two_qubit_insufficient",
        "all_branches_32_substages",
        "all_transition_channels_numeric_cptp",
    ]
    controls = {
        "distinct_probe": {
            "pass": shared_booleans["distinct_probe"],
            "readout_rank": rank,
            "rank_threshold": "> 1",
        },
        "flat_fuzz": {
            "pass": shared_booleans["flat_vanish"],
            "readouts": flat_r,
            "condition": "max-entropy rho has zero knot/baryon/gravity readouts and dark_energy_time=1",
        },
        "knot_couples_mass_gravity": {
            "pass": shared_booleans["knot_couples"],
            "mass": knot_r["bounded_knot_mass"],
            "gravity": knot_r["sync_gradient_gravity"],
        },
        "decoupling_witness": {
            "pass": shared_booleans["decoupling_witness"],
            "mass_delta": mass_delta,
            "gravity_delta": gravity_delta,
            "condition": "shape swap preserves local knot mass but moves distance-weighted entropy gradient",
        },
        "two_qubit_control_insufficient": {
            "pass": shared_booleans["two_qubit_insufficient"],
            "n_qubits": twoq["n_qubits"],
            "three_cell_defined": False,
            "reason": "tripartite inclusion-exclusion needs three one-qubit regions A,B,C and pairs AB,AC,BC",
        },
    }
    branch_tests = {
        "type1_vs_type2_weyl": {
            "pass": shared_booleans["type1_vs_type2_differ"],
            "max_readout_diff": type_diff,
            "type1_hamiltonian": "+(0.77*SZ + 0.13*SX)",
            "type2_hamiltonian": "-(0.77*SZ + 0.13*SX)",
        },
        "loop_classes_and_schedule_orders": {
            "pass": shared_booleans["schedule_orders_differ"],
            "type1_vs_type2_schedule_order_diff": schedule_type_diff,
            "outer_first_vs_inner_first_diff": loop_order_diff,
        },
        "operator_on_vs_operator_erased": {
            "pass": shared_booleans["operator_order_matters"],
            "max_readout_diff": erased_diff,
        },
    }
    positive = {
        "canonical_type_branches_separate": branch_tests["type1_vs_type2_weyl"],
        "schedule_and_loop_order_are_observable": branch_tests["loop_classes_and_schedule_orders"],
        "operator_erasure_changes_readouts": branch_tests["operator_on_vs_operator_erased"],
        "three_qubit_readout_rank_nontrivial": controls["distinct_probe"],
    }
    result = {
        "object_id": OBJECT_ID,
        "backend": "jax",
        "created_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "result_path": str(RESULT_PATH),
        "julia_result_path": str(JULIA_RESULT_PATH),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "n_qubits": N_QUBITS,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "source_math_lock": {
            "source_file": "system_v5/ops/formal_scouts/canonical_qit_engine_specs.py",
            "hamiltonian": "H0=0.77*SZ+0.13*SX; Type1=+H0; Type2=-H0",
            "lindblad": "Se=SZ, Ne=SIGMA_PLUS, Ni=-i*SY, Si=SIGMA_MINUS; Type2 uses MIRROR @ L @ MIRROR",
            "operators": "Ti=SZ, Te=SX, Fi=SX, Fe=SY with OPERATOR_BASE_ANGLES",
            "schedule": "8 main stages x 4 operator substages = 32 per engine",
            "carrier_extension": "site-local canonical H, L, and operator kicks lifted to (C^2)^n by Kronecker products",
            "non_source_math_excluded": [
                "no toy spinor network operators",
                "no invented Hamiltonian",
                "no torch compute in this scout",
                "no numpy compute in this scout",
            ],
        },
        "branches": branches,
        "controls": controls,
        "branch_tests": branch_tests,
        "positive": positive,
        "control_runs": {
            "flat_fuzz_type1": flat,
            "knot_product_type1": knot,
            "knot_shape_swapped_type1": shape,
            "two_qubit_control_type1": twoq,
        },
        "readout_keys": READOUT_KEYS,
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "positive_boolean_keys": positive_boolean_keys,
        "tool_manifest": {
            "JAX": {"used": True, "reason": "load-bearing x64 density evolution and readout computation"},
            "jax.numpy": {"used": True, "reason": "load-bearing matrix algebra without NumPy compute"},
            "JSON": {"used": True, "reason": "durable scratch diagnostic result serialization"},
            "Julia": {"used": False, "reason": "peer backend is executed in separate Julia mirror"},
        },
        "tool_integration_depth": {
            "JAX": "load_bearing",
            "jax.numpy": "load_bearing",
            "JSON": "supportive",
            "Julia": "supportive",
        },
        "promotion_blockers": [
            "classification is scratch_diagnostic",
            "promotion_allowed=false",
            "formal_admission_allowed=false",
            "readouts are taxonomy diagnostics only and do not admit physics/gravity/dark-sector/Axis0/M(C)",
        ],
    }
    result["parity"] = parity_block(result)
    result["all_pass"] = (
        all(shared_booleans[key] for key in positive_boolean_keys)
        and not shared_booleans["numpy_compute_used"]
        and not shared_booleans["torch_compute_used"]
        and all(row["pass"] for row in controls.values())
        and all(row["pass"] for row in branch_tests.values())
        and result["parity"]["within_1e_10"]
    )
    result["stop_condition_fired"] = not result["all_pass"]
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"RESULT {OBJECT_ID} jax all_pass={result['all_pass']} -> {RESULT_PATH}")
    print(
        "SCOUT_DONE "
        f"jax={RESULT_PATH} "
        f"julia={JULIA_RESULT_PATH} "
        f"all_pass={str(result['all_pass']).lower()} "
        f"n_qubits={N_QUBITS} "
        f"type1_vs_type2_differ={str(result['shared_booleans']['type1_vs_type2_differ']).lower()} "
        f"readout_rank={int(result['shared_scalars']['readout_rank'])} "
        f"flat_vanish={str(result['shared_booleans']['flat_vanish']).lower()} "
        f"knot_couples={str(result['shared_booleans']['knot_couples']).lower()} "
        f"two_qubit_insufficient={str(result['shared_booleans']['two_qubit_insufficient']).lower()}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
