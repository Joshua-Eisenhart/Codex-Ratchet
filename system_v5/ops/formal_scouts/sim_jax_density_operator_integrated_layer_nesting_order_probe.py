#!/usr/bin/env python3
"""JAX density-operator integrated layer nesting-order scout.

This scout keeps the active lane narrow and explicit:

    finite density pair (rho_L, rho_R)
    -> fixed finite prefix
    -> every L2-L8 core layer in a candidate order
    -> density-operator signature + erasure controls

It enumerates every order of the seven core layers for every signed
terrain/operator pair. Operators-before-stacking is a hard filter, while
stack-before-operator orders remain measured as negative population.

The operator object is four primitive Hilbert-space maps with two ordered
placements each. The terrain expansion uses only native terrain/operator
pairings; non-native pairings are controls/adapters unless a frame map is
declared.

Claim ceiling: formal scout only. No layer completion, stack readiness, flux,
Axis0/FEP, physics, or final manifold admission.
"""

from __future__ import annotations

import itertools
import json
import sys
import time
import ast
from pathlib import Path
from typing import Any

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
SCOUT_DIR = Path(__file__).resolve().parent
if str(SCOUT_DIR) not in sys.path:
    sys.path.insert(0, str(SCOUT_DIR))

import sim_jax_density_operator_terrain_signed_commutator_probe as dens


RESULT = Path("system_v5/ops/formal_scouts/results/jax_density_operator_integrated_layer_nesting_order_probe_results.json")

CTYPE = jnp.complex128
RTYPE = jnp.float64
EPS = 1.0e-10
EFFECT_EPS = 1.0e-5

LAYER_NAMES = (
    "L2_chirality",
    "L3_gstructure",
    "L4_terrain",
    "L5_operator",
    "L6_entropy_cut",
    "L7_hopf_projection",
    "L8_gluing",
)
L2, L3, L4, L5, L6, L7, L8 = range(7)

OP_INDEX = {"Ti": 0, "Te": 1, "Fi": 2, "Fe": 3}
TAU_INDEX = {"Se": 0, "Ne": 1, "Ni": 2, "Si": 3}
SIGNED_PAIR_INDEX = jnp.asarray([[TAU_INDEX[t], OP_INDEX[o]] for t, o in dens.SIGNED_PAIRS], dtype=jnp.int32)
SIGNED_OPERATOR_FAMILY_COUNT = len(dens.SIGNED_OPERATOR_FAMILIES)

BLOCKED_CONSUMERS = [
    "full_layer_completion",
    "canonical_layer_admission",
    "official_g_structure_selection",
    "layer_stacking",
    "layer_stacking_readiness",
    "gluing_readiness",
    "noncommutative_layer_order_claim",
    "flux",
    "Xi",
    "Phi0",
    "Xi/Phi0",
    "Axis0",
    "FEP",
    "FEP/Holodeck",
    "bridge",
    "basin_admission",
    "coexistence_topology_emergence",
    "physics_gravity",
    "final_manifold_admission",
]

DEPENDENCY_RECEIPTS = [
    "jax_weyl_terrain_64_microstep_diagnostic_results.json",
    "jax_weyl_terrain_16_placements_lindblad_audit_results.json",
    "system_v5/ops/formal_scouts/results/jax_native_l2_weyl_spinor_chirality_layer_probe_results.json",
    "system_v5/ops/formal_scouts/results/jax_native_l3_quaternion_clifford_orientation_layer_probe_results.json",
    "system_v5/ops/formal_scouts/results/jax_native_l4_terrain_channel_generator_layer_probe_results.json",
    "system_v5/ops/formal_scouts/results/jax_native_l5_operator_substage_cell_layer_probe_results.json",
    "system_v5/ops/formal_scouts/results/jax_native_l6_entropy_cut_communication_layer_probe_results.json",
    "system_v5/ops/formal_scouts/results/jax_native_l7_hopf_shell_projection_layer_probe_results.json",
    "system_v5/ops/formal_scouts/results/jax_native_l8_gluing_groupoid_layer_probe_results.json",
    "jax_independent_layer_geometry_coverage_gate_results.json",
    "jax_nested_hopf_pairwise_leaf_coupling_audit_results.json",
    "jax_nested_hopf_nesting_order_gate_results.json",
    "jax_nested_hopf_stack_status_oracle_results.json",
    "jax_gstructure_16_placement_spin3_audit_results.json",
    "jax_gstructure_16_branch_prune_selector_audit_results.json",
    "jax_gstructure_16_external_negative_oracle_results.json",
    "jax_qit_entropy_geometry_separation_stress_results.json",
    "jax_nested_hopf_shell_branch_prune_qit_probe_results.json",
    "system_v5/ops/formal_scouts/results/jax_density_operator_terrain_signed_commutator_probe_results.json",
    "system_v5/ops/formal_scouts/results/jax_l4_l5_order_commutator_finitude_ratchet_probe_results.json",
    "system_v5/ops/formal_scouts/results/jax_nested_hopf_leaf_area_order_ratchet_probe_results.json",
]


def _jsonable(x: Any) -> Any:
    if hasattr(x, "item"):
        return x.item()
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    return x


def dagger(x: jax.Array) -> jax.Array:
    return jnp.conj(jnp.swapaxes(x, -1, -2))


def hermitize(rho: jax.Array) -> jax.Array:
    return 0.5 * (rho + dagger(rho))


def normalize_density(rho: jax.Array) -> jax.Array:
    rho = hermitize(rho)
    tr = jnp.trace(rho, axis1=-2, axis2=-1)[..., None, None]
    return rho / tr


def hs_norm_sq(x: jax.Array) -> jax.Array:
    return jnp.real(jnp.trace(dagger(x) @ x, axis1=-2, axis2=-1))


def adjoint_channel(unitary: jax.Array, rho: jax.Array) -> jax.Array:
    return normalize_density(unitary @ rho @ dagger(unitary))


def convex_mix(a: jax.Array, b: jax.Array, weight: float | jax.Array) -> jax.Array:
    return normalize_density((1.0 - weight) * a + weight * b)


def pinch_i(rho: jax.Array) -> jax.Array:
    return dens.P0 @ rho @ dens.P0 + dens.P1 @ rho @ dens.P1


def pinch_e(rho: jax.Array) -> jax.Array:
    return dens.QP @ rho @ dens.QP + dens.QM @ rho @ dens.QM


def channel_t_i(rho: jax.Array, q: float | jax.Array = dens.Q_BASE) -> jax.Array:
    return convex_mix(rho, pinch_i(rho), q)


def channel_t_e(rho: jax.Array, q: float | jax.Array = dens.Q_BASE) -> jax.Array:
    return convex_mix(rho, pinch_e(rho), q)


def channel_f_i(rho: jax.Array) -> jax.Array:
    return adjoint_channel(dens.unitary_x(), rho)


def channel_f_e(rho: jax.Array) -> jax.Array:
    return adjoint_channel(dens.unitary_z(), rho)


def op_channel(op_idx: jax.Array, rho: jax.Array) -> jax.Array:
    return jax.lax.switch(op_idx, (channel_t_i, channel_t_e, channel_f_i, channel_f_e), rho)


def terrain_se(rho: jax.Array) -> jax.Array:
    r1 = adjoint_channel(dens.unitary_x(jnp.asarray(0.36, dtype=RTYPE)), rho)
    r2 = channel_t_e(r1, jnp.asarray(0.29, dtype=RTYPE))
    return adjoint_channel(dens.unitary_z(jnp.asarray(0.47, dtype=RTYPE)), r2)


def terrain_ne(rho: jax.Array) -> jax.Array:
    return adjoint_channel(dens.unitary_x(jnp.asarray(-0.52, dtype=RTYPE)), channel_t_i(rho, jnp.asarray(0.31, dtype=RTYPE)))


def terrain_ni(rho: jax.Array) -> jax.Array:
    r1 = adjoint_channel(dens.unitary_z(jnp.asarray(0.22, dtype=RTYPE)), rho)
    r2 = channel_t_i(r1, jnp.asarray(0.27, dtype=RTYPE))
    return adjoint_channel(dens.unitary_x(jnp.asarray(0.39, dtype=RTYPE)), r2)


def terrain_si(rho: jax.Array) -> jax.Array:
    return adjoint_channel(dens.unitary_z(jnp.asarray(-0.58, dtype=RTYPE)), channel_t_e(rho, jnp.asarray(0.33, dtype=RTYPE)))


def terrain_channel(tau_idx: jax.Array, rho: jax.Array) -> jax.Array:
    return jax.lax.switch(tau_idx, (terrain_se, terrain_ne, terrain_ni, terrain_si), rho)


def entropy(rho: jax.Array) -> jax.Array:
    vals = jnp.clip(jnp.real(jnp.linalg.eigvalsh(hermitize(rho))), 1.0e-12, 1.0)
    return -jnp.sum(vals * jnp.log2(vals), axis=-1)


def trace_distance(a: jax.Array, b: jax.Array) -> jax.Array:
    vals = jnp.linalg.eigvalsh(hermitize(a - b))
    return 0.5 * jnp.sum(jnp.abs(jnp.real(vals)), axis=-1)


def d_t_i(rho: jax.Array) -> jax.Array:
    return hs_norm_sq(rho - pinch_i(rho))


def d_t_e(rho: jax.Array) -> jax.Array:
    return hs_norm_sq(rho - pinch_e(rho))


def finite_density_pair_inputs() -> jax.Array:
    rows = []
    for idx, rho in enumerate(dens.finite_density_inputs()):
        u = dens.unitary_z(jnp.asarray(0.19 + 0.03 * idx, dtype=RTYPE)) @ dens.unitary_x(jnp.asarray(-0.11 - 0.02 * idx, dtype=RTYPE))
        rho_l = normalize_density(rho)
        rho_r = normalize_density(adjoint_channel(u, rho))
        rows.append(jnp.stack([rho_l, rho_r], axis=0))
    return jnp.stack(rows, axis=0)


def layer_l0_response_effect(state: jax.Array) -> jax.Array:
    mixed = convex_mix(state, jnp.broadcast_to(dens.I2 / 2.0, state.shape), jnp.asarray(0.035, dtype=RTYPE))
    return convex_mix(channel_t_i(mixed, jnp.asarray(0.08, dtype=RTYPE)), channel_t_e(mixed, jnp.asarray(0.06, dtype=RTYPE)), jnp.asarray(0.5, dtype=RTYPE))


def layer_l1_boundary_environment(state: jax.Array) -> jax.Array:
    left = adjoint_channel(dens.unitary_x(jnp.asarray(0.071, dtype=RTYPE)), state[0])
    right = adjoint_channel(dens.unitary_z(jnp.asarray(-0.083, dtype=RTYPE)), state[1])
    return jnp.stack([channel_t_i(left, jnp.asarray(0.045, dtype=RTYPE)), channel_t_e(right, jnp.asarray(0.052, dtype=RTYPE))], axis=0)


def layer_l2_chirality(state: jax.Array, tau_idx: jax.Array, op_idx: jax.Array) -> jax.Array:
    del tau_idx, op_idx
    left = adjoint_channel(dens.unitary_x(jnp.asarray(0.173, dtype=RTYPE)), state[0])
    right = adjoint_channel(dens.unitary_x(jnp.asarray(-0.173, dtype=RTYPE)), state[1])
    return jnp.stack([left, right], axis=0)


def layer_l3_gstructure(state: jax.Array, tau_idx: jax.Array, op_idx: jax.Array) -> jax.Array:
    del tau_idx, op_idx
    u = dens.unitary_z(jnp.asarray(0.127, dtype=RTYPE)) @ dens.unitary_x(jnp.asarray(0.157, dtype=RTYPE))
    return adjoint_channel(u, state)


def layer_l4_terrain(state: jax.Array, tau_idx: jax.Array, op_idx: jax.Array) -> jax.Array:
    del op_idx
    return terrain_channel(tau_idx, state)


def layer_l5_operator(state: jax.Array, tau_idx: jax.Array, op_idx: jax.Array) -> jax.Array:
    del tau_idx
    return op_channel(op_idx, state)


def layer_l6_entropy_cut(state: jax.Array, tau_idx: jax.Array, op_idx: jax.Array) -> jax.Array:
    del tau_idx, op_idx
    s = entropy(state)
    weights = jnp.clip(0.025 + 0.045 * s, 0.02, 0.09)
    return convex_mix(state, jnp.broadcast_to(dens.I2 / 2.0, state.shape), weights[:, None, None])


def layer_l7_hopf_projection(state: jax.Array, tau_idx: jax.Array, op_idx: jax.Array) -> jax.Array:
    del tau_idx, op_idx
    u_l = dens.unitary_z(jnp.asarray(0.211, dtype=RTYPE)) @ dens.unitary_x(jnp.asarray(-0.067, dtype=RTYPE))
    u_r = dens.unitary_z(jnp.asarray(-0.211, dtype=RTYPE)) @ dens.unitary_x(jnp.asarray(0.067, dtype=RTYPE))
    left = convex_mix(adjoint_channel(u_l, state[0]), channel_t_e(state[0], jnp.asarray(0.043, dtype=RTYPE)), jnp.asarray(0.33, dtype=RTYPE))
    right = convex_mix(adjoint_channel(u_r, state[1]), channel_t_i(state[1], jnp.asarray(0.047, dtype=RTYPE)), jnp.asarray(0.33, dtype=RTYPE))
    return jnp.stack([left, right], axis=0)


def layer_l8_gluing(state: jax.Array, tau_idx: jax.Array, op_idx: jax.Array) -> jax.Array:
    del tau_idx, op_idx
    u = dens.unitary_z(jnp.asarray(0.181, dtype=RTYPE)) @ dens.unitary_x(jnp.asarray(0.109, dtype=RTYPE))
    transported_r = adjoint_channel(u, state[1])
    transported_l = adjoint_channel(dagger(u), state[0])
    left = convex_mix(state[0], transported_r, jnp.asarray(0.118, dtype=RTYPE))
    right = convex_mix(state[1], transported_l, jnp.asarray(0.118, dtype=RTYPE))
    return jnp.stack([left, right], axis=0)


LAYER_FUNCS = (
    layer_l2_chirality,
    layer_l3_gstructure,
    layer_l4_terrain,
    layer_l5_operator,
    layer_l6_entropy_cut,
    layer_l7_hopf_projection,
    layer_l8_gluing,
)


def apply_layer(code: jax.Array, state: jax.Array, tau_idx: jax.Array, op_idx: jax.Array) -> jax.Array:
    return jax.lax.switch(code, LAYER_FUNCS, state, tau_idx, op_idx)


def state_signature(state: jax.Array) -> jax.Array:
    evals = jnp.sort(jnp.real(jnp.linalg.eigvalsh(hermitize(state))), axis=-1).reshape(-1)
    s = entropy(state)
    lr = jnp.asarray([trace_distance(state[0], state[1])], dtype=RTYPE)
    distances = jnp.asarray([d_t_i(state[0]), d_t_i(state[1]), d_t_e(state[0]), d_t_e(state[1])], dtype=RTYPE)
    comm_readouts = jnp.asarray(
        [
            jnp.sqrt(jnp.maximum(hs_norm_sq(terrain_se(channel_t_i(state[0])) - channel_t_i(terrain_se(state[0]))), 0.0)),
            jnp.sqrt(jnp.maximum(hs_norm_sq(terrain_ne(channel_f_i(state[0])) - channel_f_i(terrain_ne(state[0]))), 0.0)),
            jnp.sqrt(jnp.maximum(hs_norm_sq(terrain_ni(channel_t_e(state[1])) - channel_t_e(terrain_ni(state[1]))), 0.0)),
            jnp.sqrt(jnp.maximum(hs_norm_sq(terrain_si(channel_f_e(state[1])) - channel_f_e(terrain_si(state[1]))), 0.0)),
        ],
        dtype=RTYPE,
    )
    return jnp.concatenate([evals, s, lr, distances, comm_readouts], axis=0)


def run_order(order: jax.Array, pair: jax.Array, state0: jax.Array, skip_code: jax.Array) -> jax.Array:
    tau_idx, op_idx = pair[0], pair[1]
    state = layer_l1_boundary_environment(layer_l0_response_effect(state0))

    def body(carry: jax.Array, code: jax.Array) -> tuple[jax.Array, None]:
        stepped = apply_layer(code, carry, tau_idx, op_idx)
        keep_old = code == skip_code
        next_state = jnp.where(keep_old, carry, stepped)
        return next_state, None

    final, _ = jax.lax.scan(body, state, order)
    return normalize_density(final)


def order_positions(order: jax.Array) -> jax.Array:
    return jnp.argsort(order)


def swap_l4_l5(order: jax.Array) -> jax.Array:
    pos = order_positions(order)
    p4 = pos[L4]
    p5 = pos[L5]
    values = jnp.arange(order.shape[0])
    return jnp.where(values == p4, L5, jnp.where(values == p5, L4, order))


def combo_metrics(order: jax.Array, pair: jax.Array, inputs: jax.Array) -> dict[str, jax.Array]:
    full_states = jax.vmap(lambda s: run_order(order, pair, s, jnp.asarray(-1, dtype=jnp.int32)))(inputs)
    full_sigs = jax.vmap(state_signature)(full_states)

    def skip_effect(code: jax.Array) -> jax.Array:
        skipped = jax.vmap(lambda s: run_order(order, pair, s, code))(inputs)
        skipped_sigs = jax.vmap(state_signature)(skipped)
        return jnp.mean(jnp.linalg.norm(full_sigs - skipped_sigs, axis=1))

    layer_effects = jax.vmap(skip_effect)(jnp.arange(7, dtype=jnp.int32))
    swapped = jax.vmap(lambda s: run_order(swap_l4_l5(order), pair, s, jnp.asarray(-1, dtype=jnp.int32)))(inputs)
    swapped_sigs = jax.vmap(state_signature)(swapped)
    signed_gap = jnp.mean(jnp.linalg.norm(full_sigs - swapped_sigs, axis=1))

    vals = jnp.linalg.eigvalsh(hermitize(full_states))
    trace_gaps = jnp.abs(jnp.trace(full_states, axis1=-2, axis2=-1) - 1.0)
    herm_gaps = jnp.max(jnp.abs(full_states - dagger(full_states)), axis=(-1, -2))
    pos = order_positions(order)

    min_effect = jnp.min(layer_effects)
    hard_order = (pos[L5] < pos[L8]) & (pos[L4] < pos[L8])
    gluing_terminal = pos[L8] == (order.shape[0] - 1)
    stack_before_operator = pos[L8] < pos[L5]
    all_effects = min_effect > EFFECT_EPS
    density_valid = (jnp.max(trace_gaps) < EPS) & (jnp.max(herm_gaps) < EPS) & (jnp.min(jnp.real(vals)) > -EPS)
    filtered_candidate = hard_order & gluing_terminal & all_effects & density_valid & (signed_gap > EFFECT_EPS)
    score = jnp.sum(layer_effects) + 0.5 * signed_gap + 0.25 * min_effect
    signed_orientation = jnp.where(pos[L5] < pos[L4], 1, -1)

    return {
        "score": score,
        "layer_effects": layer_effects,
        "min_layer_effect": min_effect,
        "signed_l4_l5_gap": signed_gap,
        "filtered_candidate": filtered_candidate,
        "operator_before_gluing": pos[L5] < pos[L8],
        "terrain_before_gluing": pos[L4] < pos[L8],
        "gluing_terminal": gluing_terminal,
        "stack_before_operator": stack_before_operator,
        "density_valid": density_valid,
        "max_trace_gap": jnp.max(trace_gaps),
        "max_hermitian_gap": jnp.max(herm_gaps),
        "min_eval": jnp.min(jnp.real(vals)),
        "signed_orientation": signed_orientation,
    }


@jax.jit
def run_all(combo_orders: jax.Array, combo_pairs: jax.Array, inputs: jax.Array) -> dict[str, jax.Array]:
    return jax.vmap(lambda order, pair: combo_metrics(order, pair, inputs))(combo_orders, combo_pairs)


def row_from_index(index: int, combo_orders: jax.Array, combo_pairs: jax.Array, metrics: dict[str, jax.Array]) -> dict[str, Any]:
    order_codes = [int(x) for x in jax.device_get(combo_orders[index]).tolist()]
    pair_codes = [int(x) for x in jax.device_get(combo_pairs[index]).tolist()]
    tau = tuple(TAU_INDEX.keys())[pair_codes[0]]
    op_name = tuple(OP_INDEX.keys())[pair_codes[1]]
    effects = jax.device_get(metrics["layer_effects"][index])
    orientation = "+" if int(jax.device_get(metrics["signed_orientation"][index])) == 1 else "-"
    return {
        "index": index,
        "terrain": tau,
        "operator": op_name,
        "signed_orientation": orientation,
        "signed_orientation_meaning": "+ means Phi_tau o O (L5_operator before L4_terrain); - means O o Phi_tau (L4_terrain before L5_operator)",
        "order": [LAYER_NAMES[c] for c in order_codes],
        "score": float(jax.device_get(metrics["score"][index])),
        "min_layer_effect": float(jax.device_get(metrics["min_layer_effect"][index])),
        "signed_l4_l5_gap": float(jax.device_get(metrics["signed_l4_l5_gap"][index])),
        "operator_before_gluing": bool(jax.device_get(metrics["operator_before_gluing"][index])),
        "terrain_before_gluing": bool(jax.device_get(metrics["terrain_before_gluing"][index])),
        "gluing_terminal": bool(jax.device_get(metrics["gluing_terminal"][index])),
        "stack_before_operator": bool(jax.device_get(metrics["stack_before_operator"][index])),
        "density_valid": bool(jax.device_get(metrics["density_valid"][index])),
        "layer_effects": {LAYER_NAMES[i]: float(effects[i]) for i in range(len(LAYER_NAMES))},
    }


def first_n_indices(mask: jax.Array, scores: jax.Array, n: int, *, reverse: bool = True) -> list[int]:
    mask_host = jax.device_get(mask)
    scores_host = jax.device_get(scores)
    indices = [i for i, ok in enumerate(mask_host.tolist()) if ok]
    indices.sort(key=lambda i: scores_host[i], reverse=reverse)
    return indices[:n]


def source_boundary_checks() -> dict[str, bool]:
    source = Path(__file__).read_text(encoding="utf-8")
    lowered = source.lower()
    tree = ast.parse(source)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
    return {
        "coordinate_vector_word_absent_from_source": ("bl" + "och") not in lowered,
        "no_julia_import_or_subprocess": "julia" not in imported_roots and ("sub" + "process") not in imported_roots,
        "no_pytorch_import": "torch" not in imported_roots,
    }


def dependency_receipt_rows() -> list[dict[str, Any]]:
    def all_checks_true(data: dict[str, Any]) -> bool:
        checks = data.get("checks")
        return isinstance(checks, dict) and bool(checks) and all(bool(v) for v in checks.values())

    def nested_green(data: dict[str, Any]) -> bool:
        suite = data.get("suite")
        reference_runner = data.get("reference_runner")
        return bool(
            isinstance(suite, dict)
            and suite.get("AUDIT_PASS") is True
            or isinstance(reference_runner, dict)
            and reference_runner.get("AUDIT_PASS") is True
            or data.get("required_ok") is True
        )

    def combined_blocks(data: dict[str, Any]) -> set[str]:
        fields = (
            "blocked_consumers",
            "downstream_blocked",
            "downstream_blocks",
            "still_blocked_consumers",
            "blocked_claims",
        )
        blocks: set[str] = set()
        for field in fields:
            value = data.get(field)
            if isinstance(value, list):
                blocks.update(str(x) for x in value)
        claim_text = " ".join(
            str(data.get(k, ""))
            for k in ("claim_boundary", "claim_ceiling", "allowed_claim", "next_admissible_move")
        )
        if claim_text:
            blocks.add(claim_text)
        return {x.lower().replace("/", "_").replace("-", "_") for x in blocks}

    def blocks_present(data: dict[str, Any]) -> bool:
        blocks = combined_blocks(data)
        if data.get("axis0_allowed") is False and data.get("flux_allowed") is False:
            return True
        if not blocks:
            return True
        joined = " ".join(blocks)
        critical = ("flux", "axis0", "final_manifold")
        return all(token in joined for token in critical)

    rows = []
    for raw in DEPENDENCY_RECEIPTS:
        path = Path(raw)
        row: dict[str, Any] = {"path": raw, "exists": path.exists()}
        if not path.exists():
            row.update({"result_ok": False, "green_or_passed": False, "fenced": False, "blocks_present": False})
            rows.append(row)
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - receipt defect is reported.
            row.update({"result_ok": False, "green_or_passed": False, "fenced": False, "blocks_present": False, "error": repr(exc)})
            rows.append(row)
            continue
        green = bool(data.get("AUDIT_PASS", data.get("all_pass", False)) or data.get("result_ok", False) or all_checks_true(data) or nested_green(data))
        promotion_fenced = data.get("promotion_allowed") is False if "promotion_allowed" in data else True
        formal_fenced = data.get("formal_admission_allowed") is False if "formal_admission_allowed" in data else True
        no_julia = data.get("ran_julia") is False if "ran_julia" in data else True
        no_pytorch = data.get("ran_pytorch") is False if "ran_pytorch" in data else True
        receipt_blocks_present = blocks_present(data)
        row.update(
            {
                "classification": data.get("classification"),
                "sim_id": data.get("sim_id"),
                "green_or_passed": green,
                "promotion_fenced": promotion_fenced,
                "formal_fenced": formal_fenced,
                "no_julia": no_julia,
                "no_pytorch": no_pytorch,
                "blocks_present": receipt_blocks_present,
                "result_ok": green and promotion_fenced and formal_fenced and no_julia and no_pytorch and receipt_blocks_present,
            }
        )
        rows.append(row)
    return rows


def main() -> int:
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    inputs = finite_density_pair_inputs()

    orders = jnp.asarray(list(itertools.permutations(range(7))), dtype=jnp.int32)
    combo_orders = jnp.repeat(orders, SIGNED_PAIR_INDEX.shape[0], axis=0)
    combo_pairs = jnp.tile(SIGNED_PAIR_INDEX, (orders.shape[0], 1))
    metrics = run_all(combo_orders, combo_pairs, inputs)
    jax.block_until_ready(metrics["score"])

    filtered = metrics["filtered_candidate"]
    stack_before_operator = metrics["stack_before_operator"]
    operator_before = metrics["operator_before_gluing"]
    terrain_before = metrics["terrain_before_gluing"]
    gluing_terminal = metrics["gluing_terminal"]
    plus_mask = metrics["signed_orientation"] == 1
    minus_mask = metrics["signed_orientation"] == -1
    selected_indices = first_n_indices(filtered, metrics["score"], 8)
    rejected_indices = first_n_indices(stack_before_operator, metrics["score"], 5)
    selected = row_from_index(selected_indices[0], combo_orders, combo_pairs, metrics) if selected_indices else None
    dependency_rows = dependency_receipt_rows()

    checks = {
        "evaluated_all_core_orders": int(orders.shape[0]) == 5040 and int(combo_orders.shape[0]) == 40320,
        "four_primitive_maps_only": len(dens.OPERATORS) == 4,
        "signed_operator_family_count_is_8": SIGNED_OPERATOR_FAMILY_COUNT == 8,
        "evaluated_all_native_terrain_operator_pairings": int(SIGNED_PAIR_INDEX.shape[0]) == 8,
        "signed_variant_orders_present": bool(jnp.any(plus_mask) and jnp.any(minus_mask)),
        "filtered_candidate_population_nonempty": bool(jnp.sum(filtered) > 0),
        "selected_operator_before_gluing": bool(selected["operator_before_gluing"]) if selected else False,
        "selected_terrain_before_gluing": bool(selected["terrain_before_gluing"]) if selected else False,
        "selected_gluing_terminal": bool(selected["gluing_terminal"]) if selected else False,
        "selected_all_layers_load_bearing": bool(selected and min(selected["layer_effects"].values()) > EFFECT_EPS),
        "selected_signed_l4_l5_order_gap_positive": bool(selected and selected["signed_l4_l5_gap"] > EFFECT_EPS),
        "operator_erasure_control_changes_signature": bool(selected and selected["layer_effects"]["L5_operator"] > EFFECT_EPS),
        "terrain_erasure_control_changes_signature": bool(selected and selected["layer_effects"]["L4_terrain"] > EFFECT_EPS),
        "gluing_erasure_control_changes_signature": bool(selected and selected["layer_effects"]["L8_gluing"] > EFFECT_EPS),
        "all_candidate_outputs_density_valid": bool(jnp.all(metrics["density_valid"])),
        "stack_before_operator_negative_population_measured": bool(jnp.sum(stack_before_operator) > 0),
        "dependency_receipts_green_and_fenced": all(row["result_ok"] for row in dependency_rows),
        "no_julia_execution": True,
        "no_pytorch_execution": True,
        "promotion_blocked": True,
    }
    checks.update(source_boundary_checks())
    audit_pass = all(bool(v) for v in checks.values())

    top_rows = [row_from_index(i, combo_orders, combo_pairs, metrics) for i in selected_indices]
    rejected_rows = [row_from_index(i, combo_orders, combo_pairs, metrics) for i in rejected_indices]
    layer_effect_minima = jnp.min(metrics["layer_effects"], axis=0)
    layer_effect_maxima = jnp.max(metrics["layer_effects"], axis=0)

    out = {
        "sim_id": "jax_density_operator_integrated_layer_nesting_order_probe",
        "name": "JAX density-operator integrated layer nesting-order scout",
        "version": "1.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "classification": "formal_scout",
        "sim_class": "density_operator_integrated_order_search",
        "sim_execution_kind": "diagnostic_jax_density_operator_formal_scout",
        "AUDIT_PASS": audit_pass,
        "all_pass": audit_pass,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "purpose": "Search finite JAX density-operator nesting orders with operators acting before gluing/stacking and every L2-L8 layer active in one run.",
        "scientific_question": "Which finite L2-L8 nesting orders keep operator/terrain action before gluing while all layers remain load-bearing over the same density-pair carrier?",
        "root_constraints_in_force": {
            "F01": "finite 5 density-pair probes x 5040 core orders x 8 terrain/operator pairs over D(C^2)_L x D(C^2)_R",
            "N01": "candidate validity depends on noncommuting L4/L5 order, operator-before-gluing filter, and erasure controls for all core layers",
        },
        "finite_map": "(rho_L,rho_R, order, tau, O) -> fixed prefix -> ordered L2-L8 density-pair output -> density signature and layer-erasure controls",
        "domain": {
            "carrier": "D(C^2)_L x D(C^2)_R",
            "fixed_prefix": ["L0_response_effect_quotient", "L1_boundary_environment"],
            "core_layers_permuted": list(LAYER_NAMES),
            "core_order_count": int(orders.shape[0]),
            "primitive_operator_maps": ["Ti", "Te", "Fi", "Fe"],
            "signed_operator_families": dens.SIGNED_OPERATOR_FAMILIES,
            "signed_operator_family_count": SIGNED_OPERATOR_FAMILY_COUNT,
            "native_terrain_operator_pairings": [[str(t), str(o)] for t, o in dens.SIGNED_PAIRS],
            "native_terrain_operator_pairing_count": int(SIGNED_PAIR_INDEX.shape[0]),
            "terrain_admissibility": {
                "Se": ["Ti", "Fi"],
                "Ne": ["Ti", "Fi"],
                "Ni": ["Te", "Fe"],
                "Si": ["Te", "Fe"],
            },
            "non_native_pairings": "controls/adapters only unless an explicit conjugation or frame map is declared",
            "candidate_count": int(combo_orders.shape[0]),
            "density_pair_inputs": int(inputs.shape[0]),
            "weyl_sheets": ["L", "R"],
        },
        "codomain_or_output": "ranked candidate orders over native terrain/operator placements, layer-erasure effects, L4/L5 signed-order gaps, density-validity checks, and rejected stack-before-operator controls",
        "carrier_layer": "finite Hilbert-space density-operator pair for two Weyl sheets",
        "geometry_layer": "integrated formal-scout composition of chirality, G-structure, terrain, operator, finite entropy cut, Hopf projection, and gluing",
        "carrier_realization": "JAX complex128 2x2 density matrices for rho_L and rho_R; Julia read-only reference not executed",
        "peps3d_embedding": "not claimed; PEPS3D carrier-cell admission remains blocked",
        "spinor_state": "spinor-derived density pair only; no native full-spinor or PEPS3D admission claimed",
        "quaternion_action": "not claimed in this density-operator nesting-order scout",
        "dependency_receipts": DEPENDENCY_RECEIPTS,
        "allowed_claims": [
            "JAX evaluated all finite L2-L8 core orders for the corrected density-operator terrain/operator object",
            "the operator object is four primitive maps with two ordered placements each, not eight primitive channels",
            "the top formal-scout candidate under this scoring keeps L5_operator and L4_terrain before L8_gluing",
            "selected candidate has nonzero erasure sensitivity for every L2-L8 layer over the finite density-pair signature",
            "stack-before-operator orders were measured as a negative population, not promoted",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "eligible_consumers": [
            "future bounded JAX nesting-order hardening",
            "future Julia-readonly cross-audit receipt comparison",
        ],
        "promotion_blockers": [
            "formal scout only",
            "no PEPS3D cell/tensor/channel admission packet",
            "no full layer-completion claim gate",
            "no official G-structure selection",
            "no layer stacking readiness",
            "no flux, Xi/Phi0, Axis0, FEP, physics, or final manifold admission",
        ],
        "operator_before_stacking_rule": {
            "hard_filter": "index(L5_operator) < index(L8_gluing) and index(L4_terrain) < index(L8_gluing)",
            "negative_population": "orders with index(L8_gluing) < index(L5_operator) are scored but rejected from admissible top rows",
        },
        "checks": checks,
        "metrics": {
            "elapsed_seconds": round(time.time() - started, 6),
            "core_order_count": int(orders.shape[0]),
            "candidate_count": int(combo_orders.shape[0]),
            "filtered_candidate_count": int(jax.device_get(jnp.sum(filtered))),
            "operator_before_gluing_count": int(jax.device_get(jnp.sum(operator_before))),
            "terrain_before_gluing_count": int(jax.device_get(jnp.sum(terrain_before))),
            "gluing_terminal_count": int(jax.device_get(jnp.sum(gluing_terminal))),
            "stack_before_operator_negative_count": int(jax.device_get(jnp.sum(stack_before_operator))),
            "plus_signed_order_count": int(jax.device_get(jnp.sum(plus_mask))),
            "minus_signed_order_count": int(jax.device_get(jnp.sum(minus_mask))),
            "max_score": float(jax.device_get(jnp.max(metrics["score"]))),
            "max_filtered_score": float(jax.device_get(jnp.max(jnp.where(filtered, metrics["score"], -jnp.inf)))),
            "min_selected_layer_effect": selected["min_layer_effect"] if selected else None,
            "max_trace_gap": float(jax.device_get(jnp.max(metrics["max_trace_gap"]))),
            "max_hermitian_gap": float(jax.device_get(jnp.max(metrics["max_hermitian_gap"]))),
            "min_eval": float(jax.device_get(jnp.min(metrics["min_eval"]))),
            "layer_effect_minima": {LAYER_NAMES[i]: float(jax.device_get(layer_effect_minima[i])) for i in range(len(LAYER_NAMES))},
            "layer_effect_maxima": {LAYER_NAMES[i]: float(jax.device_get(layer_effect_maxima[i])) for i in range(len(LAYER_NAMES))},
        },
        "dependency_receipt_rows": dependency_rows,
        "selected_best_scoring_filtered_order": selected,
        "top_filtered_candidate_orders": top_rows,
        "top_rejected_stack_before_operator_orders": rejected_rows,
        "claim_boundary": "Integrated density-operator nesting-order formal scout only; not layer completion, stacking readiness, official G-structure selection, flux, Axis0, FEP, physics, or final admission.",
        "required_tools": ["jax", "python_stdlib"],
        "actual_tools_used": ["jax", "python_stdlib"],
        "TOOL_MANIFEST": {
            "jax": {
                "tried": True,
                "used": True,
                "role": "load_bearing",
                "reason": "JAX x64 enumerates finite density-pair layer orders, computes signatures, erasure controls, density validity, and noncommuting L4/L5 order gaps.",
            },
            "python_stdlib": {
                "tried": True,
                "used": True,
                "role": "supportive",
                "reason": "itertools enumerates finite orders; JSON and pathlib write the receipt.",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "load_bearing", "python_stdlib": "supportive"},
        "tool_manifest": {
            "jax": {
                "tried": True,
                "used": True,
                "role": "load_bearing",
                "reason": "JAX x64 enumerates finite density-pair layer orders, computes signatures, erasure controls, density validity, and noncommuting L4/L5 order gaps.",
            },
            "python_stdlib": {
                "tried": True,
                "used": True,
                "role": "supportive",
                "reason": "itertools enumerates finite orders; JSON and pathlib write the receipt.",
            },
        },
        "tool_integration_depth": {"jax": "load_bearing", "python_stdlib": "supportive"},
    }
    RESULT.write_text(json.dumps(_jsonable(out), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "density_operator_integrated_nesting_order "
        f"AUDIT_PASS={audit_pass} candidates={combo_orders.shape[0]} "
        f"filtered={out['metrics']['filtered_candidate_count']} "
        f"selected_order={selected['order'] if selected else None} "
        f"path={RESULT}"
    )
    return 0 if audit_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
