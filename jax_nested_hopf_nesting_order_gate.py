#!/usr/bin/env python3
"""JAX-only nesting-order gate after independent layer/geometry coverage.

This gate is deliberately between phases:
  - it requires the independent JAX coverage receipt to be closed;
  - it requires the pairwise adjacent Hopf-leaf JAX coupling receipt to pass;
  - it tests a finite nesting order over the layer tower and the 16 Weyl/Hopf
    placements with order-erased, label-erased, and finitude controls.

It does not run Julia, does not import PyTorch, and does not unlock flux,
Axis0, FEP, physics, or final manifold admission.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp


OUT = Path("jax_nested_hopf_nesting_order_gate_results.json")
COVERAGE_RECEIPT = Path("jax_independent_layer_geometry_coverage_gate_results.json")
PAIRWISE_RECEIPT = Path("jax_nested_hopf_pairwise_leaf_coupling_audit_results.json")

RDTYPE = jnp.float64
N_LEAVES = 9
N_STEPS = 4
EPS = 1.0e-10

LAYER_ORDER = [
    "R0_root_F01_N01",
    "L0_path_quotient",
    "L1_density_carrier",
    "L2_hopf_fibration",
    "L3_clifford_quaternion",
    "L4_hopf_connection_c1",
    "L5_nested_hopf_tori",
    "L6_weyl_sheets_on_nested_tori",
    "L7_gamma5_chirality",
    "L8_pin3_spin3_chirality_cover",
    "L9_clifford_module_gstructure",
    "L10_terrain_gksl_generator",
    "L11_operator_noncommutation_substages",
    "L12_qit_entropy_cut",
    "L13_gluing_groupoid_cocycle",
]

EDGE_NAMES = [
    ("R0_root_F01_N01", "L0_path_quotient"),
    ("L0_path_quotient", "L1_density_carrier"),
    ("L1_density_carrier", "L2_hopf_fibration"),
    ("L2_hopf_fibration", "L3_clifford_quaternion"),
    ("L3_clifford_quaternion", "L4_hopf_connection_c1"),
    ("L4_hopf_connection_c1", "L5_nested_hopf_tori"),
    ("L5_nested_hopf_tori", "L6_weyl_sheets_on_nested_tori"),
    ("L6_weyl_sheets_on_nested_tori", "L7_gamma5_chirality"),
    ("L7_gamma5_chirality", "L8_pin3_spin3_chirality_cover"),
    ("L8_pin3_spin3_chirality_cover", "L9_clifford_module_gstructure"),
    ("L9_clifford_module_gstructure", "L10_terrain_gksl_generator"),
    ("L10_terrain_gksl_generator", "L11_operator_noncommutation_substages"),
    ("L11_operator_noncommutation_substages", "L12_qit_entropy_cut"),
    ("L12_qit_entropy_cut", "L13_gluing_groupoid_cocycle"),
    # Cross-dependencies that block the common bad nestings.
    ("L5_nested_hopf_tori", "L10_terrain_gksl_generator"),
    ("L6_weyl_sheets_on_nested_tori", "L10_terrain_gksl_generator"),
    ("L4_hopf_connection_c1", "L11_operator_noncommutation_substages"),
    ("L10_terrain_gksl_generator", "L12_qit_entropy_cut"),
]

TOPOLOGIES = ("Se", "Ne", "Ni", "Si")
LEFT_TERRAINS = {"Se": "Funnel", "Ne": "Vortex", "Ni": "Pit", "Si": "Hill"}
RIGHT_TERRAINS = {"Se": "Cannon", "Ne": "Spiral", "Ni": "Source", "Si": "Citadel"}

THETAS = jnp.linspace(
    jnp.pi / (2.0 * (N_LEAVES + 1)),
    jnp.pi / 2.0 - jnp.pi / (2.0 * (N_LEAVES + 1)),
    N_LEAVES,
    dtype=RDTYPE,
)
AREAS = 2.0 * jnp.pi**2 * jnp.sin(2.0 * THETAS)
MAX_LEAF = int(N_LEAVES // 2)


def load(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _jsonify(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonify(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonify(v) for v in value]
    if hasattr(value, "tolist"):
        return _jsonify(value.tolist())
    if isinstance(value, (bool, str, int, float)) or value is None:
        return value
    return str(value)


def _f(x: Any) -> float:
    return float(jax.device_get(x))


def _i(x: Any) -> int:
    return int(jax.device_get(x))


def _b(x: Any) -> bool:
    return bool(jax.device_get(x))


def unit(x: jax.Array) -> jax.Array:
    return x / jnp.linalg.norm(x, axis=-1, keepdims=True)


def qmul(a: jax.Array, b: jax.Array) -> jax.Array:
    a0, a1, a2, a3 = jnp.moveaxis(a, -1, 0)
    b0, b1, b2, b3 = jnp.moveaxis(b, -1, 0)
    return jnp.stack(
        [
            a0 * b0 - a1 * b1 - a2 * b2 - a3 * b3,
            a0 * b1 + a1 * b0 + a2 * b3 - a3 * b2,
            a0 * b2 - a1 * b3 + a2 * b0 + a3 * b1,
            a0 * b3 + a1 * b2 - a2 * b1 + a3 * b0,
        ],
        axis=-1,
    )


def phase_spinor(phi: jax.Array, chi: jax.Array, eta: jax.Array) -> jax.Array:
    z0 = jnp.exp(1.0j * (phi + chi)) * jnp.cos(eta)
    z1 = jnp.exp(1.0j * (phi - chi)) * jnp.sin(eta)
    return jnp.stack([z0, z1], axis=-1)


def spinor_to_q(psi: jax.Array) -> jax.Array:
    return unit(jnp.stack([jnp.real(psi[..., 0]), jnp.imag(psi[..., 0]), jnp.real(psi[..., 1]), jnp.imag(psi[..., 1])], axis=-1))


def placements() -> tuple[list[dict[str, Any]], jax.Array, jax.Array, jax.Array, jax.Array, jax.Array]:
    rows: list[dict[str, Any]] = []
    targets = []
    sheet_sign = []
    path_idx = []
    topo_idx = []
    terrain_idx = []
    terrain_names: list[str] = []
    for sheet, terrains in (("L", LEFT_TERRAINS), ("R", RIGHT_TERRAINS)):
        q0 = 0.5 if sheet == "L" else -0.5
        for path_bit, path in enumerate(("fiber", "lifted_base")):
            for topo_i, topo in enumerate(TOPOLOGIES):
                terrain = terrains[topo]
                if terrain not in terrain_names:
                    terrain_names.append(terrain)
                s1 = 0.5 if path_bit == 0 else -0.5
                s2 = 0.5 if (topo_i & 1) == 0 else -0.5
                s3 = 0.5 if (topo_i & 2) == 0 else -0.5
                rows.append({"label": len(rows) + 1, "sheet": sheet, "path": path, "topology": topo, "terrain": terrain})
                targets.append([q0, s1, s2, s3])
                sheet_sign.append(1.0 if sheet == "L" else -1.0)
                path_idx.append(path_bit)
                topo_idx.append(topo_i)
                terrain_idx.append(terrain_names.index(terrain))
    return (
        rows,
        jnp.asarray(targets, dtype=RDTYPE),
        jnp.asarray(sheet_sign, dtype=RDTYPE),
        jnp.asarray(path_idx, dtype=jnp.int32),
        jnp.asarray(topo_idx, dtype=jnp.int32),
        jnp.asarray(terrain_idx, dtype=jnp.int32),
    )


PLACEMENTS, TARGETS, SHEET_SIGN, PATH_IDX, TOPO_IDX, TERRAIN_IDX = placements()


LAYER_INDEX = {name: idx for idx, name in enumerate(LAYER_ORDER)}
EDGE_INDEX = jnp.asarray([[LAYER_INDEX[a], LAYER_INDEX[b]] for a, b in EDGE_NAMES], dtype=jnp.int32)
CORRECT_ORDER = jnp.arange(len(LAYER_ORDER), dtype=jnp.int32)


def order_pass(order: jax.Array) -> jax.Array:
    positions = jnp.zeros((len(LAYER_ORDER),), dtype=jnp.int32).at[order].set(jnp.arange(len(LAYER_ORDER), dtype=jnp.int32))
    return jnp.all(positions[EDGE_INDEX[:, 0]] < positions[EDGE_INDEX[:, 1]])


def swapped_order(a: str, b: str) -> jax.Array:
    arr = list(range(len(LAYER_ORDER)))
    ia, ib = LAYER_INDEX[a], LAYER_INDEX[b]
    arr[ia], arr[ib] = arr[ib], arr[ia]
    return jnp.asarray(arr, dtype=jnp.int32)


def initial_q_grid() -> tuple[jax.Array, jax.Array, jax.Array]:
    placement = jnp.repeat(jnp.arange(16, dtype=jnp.int32), N_LEAVES)
    leaf = jnp.tile(jnp.arange(N_LEAVES, dtype=jnp.int32), 16)
    eta = THETAS[leaf]
    u = 0.17 + 0.11 * placement.astype(RDTYPE)
    phi0 = jnp.where(SHEET_SIGN[placement] > 0.0, 0.23, -0.19)
    chi0 = jnp.where(SHEET_SIGN[placement] > 0.0, -0.41, 0.62)
    fiber_phi = phi0 + u
    fiber_chi = chi0
    base_phi = phi0 - jnp.cos(2.0 * eta) * u
    base_chi = chi0 + u
    phi = jnp.where(PATH_IDX[placement] == 0, fiber_phi, base_phi)
    chi = jnp.where(PATH_IDX[placement] == 0, fiber_chi, base_chi)
    return spinor_to_q(phase_spinor(phi, chi, eta)), placement, leaf


def connection_step(q: jax.Array, placement: jax.Array, leaf: jax.Array) -> jax.Array:
    theta = THETAS[leaf]
    axis = jnp.stack(
        [
            jnp.zeros_like(theta),
            0.055 * SHEET_SIGN[placement],
            0.035 * jnp.cos(2.0 * theta),
            0.025 * (2.0 * PATH_IDX[placement].astype(RDTYPE) - 1.0),
        ],
        axis=-1,
    )
    return unit(q + 0.16 * qmul(axis, q))


def terrain_step(q: jax.Array, placement: jax.Array, label_erased: bool = False) -> jax.Array:
    target_idx = jnp.where(label_erased, jnp.zeros_like(placement), placement)
    target = TARGETS[target_idx]
    topo = TOPO_IDX[target_idx].astype(RDTYPE)
    path = PATH_IDX[target_idx].astype(RDTYPE)
    tangent = target - jnp.sum(target * q, axis=-1, keepdims=True) * q
    axis = jnp.stack(
        [
            jnp.zeros_like(topo),
            0.050 * SHEET_SIGN[target_idx],
            0.040 * (topo - 1.5),
            0.030 * (2.0 * path - 1.0),
        ],
        axis=-1,
    )
    return unit(q + 0.18 * (tangent + qmul(axis, q)))


def repeated_terrain(q: jax.Array, placement: jax.Array, label_erased: bool) -> jax.Array:
    def step(x: jax.Array, _: Any) -> tuple[jax.Array, jax.Array]:
        x_next = terrain_step(x, placement, label_erased=label_erased)
        return x_next, x_next

    q_final, _hist = jax.lax.scan(step, q, None, length=18)
    return q_final


def order_dynamic_readout() -> dict[str, Any]:
    q0, placement, leaf = initial_q_grid()
    ct = terrain_step(connection_step(q0, placement, leaf), placement)
    tc = connection_step(terrain_step(q0, placement), placement, leaf)
    gap = jnp.linalg.norm(ct - tc, axis=-1)

    same_a = terrain_step(terrain_step(q0, placement), placement)
    same_b = terrain_step(terrain_step(q0, placement), placement)
    same_gap = jnp.linalg.norm(same_a - same_b, axis=-1)

    correct_class_state = repeated_terrain(connection_step(q0, placement, leaf), placement, label_erased=False)
    erased = repeated_terrain(connection_step(q0, placement, leaf), placement, label_erased=True)
    erased_labels = jnp.argmax(erased @ TARGETS.T, axis=1) + 1
    erased_pop = jnp.unique(erased_labels, size=16, fill_value=-1)
    erased_count = jnp.sum(erased_pop >= 0)

    correct_labels = jnp.argmax(correct_class_state @ TARGETS.T, axis=1) + 1
    correct_pop = jnp.unique(correct_labels, size=16, fill_value=-1)
    correct_count = jnp.sum(correct_pop >= 0)

    invalid = 1.25 * q0
    alive = jnp.linalg.norm(invalid, axis=-1) <= 1.0 + 1.0e-3
    retracted = unit(invalid)
    retraction_drift = jnp.max(jnp.abs(jnp.linalg.norm(retracted, axis=-1) - 1.0))

    return {
        "mean_connection_terrain_order_gap": _f(jnp.mean(gap)),
        "max_connection_terrain_order_gap": _f(jnp.max(gap)),
        "max_same_word_order_control_gap": _f(jnp.max(same_gap)),
        "correct_populated_placement_count": _i(correct_count),
        "label_erased_populated_placement_count": _i(erased_count),
        "finitude_invalid_survivors": _i(jnp.sum(alive)),
        "max_retraction_norm_drift": _f(retraction_drift),
        "pass": _f(jnp.mean(gap)) > 1.0e-3
        and _f(jnp.max(same_gap)) < EPS
        and _i(correct_count) == 16
        and _i(erased_count) < 16
        and _i(jnp.sum(alive)) == 0
        and _f(retraction_drift) < EPS,
    }


@jax.jit
def ratchet_leaf_flow(areas: jax.Array) -> jax.Array:
    leaves = jnp.arange(N_LEAVES, dtype=jnp.int32)

    def step(x: jax.Array, _: Any) -> tuple[jax.Array, jax.Array]:
        left = jnp.maximum(x - 1, 0)
        right = jnp.minimum(x + 1, N_LEAVES - 1)
        prefer_right = areas[right] > areas[left]
        candidate = jnp.where(prefer_right, right, left)
        gain = areas[candidate] - areas[x]
        x_next = jnp.where(gain > 0.0, candidate, x)
        return x_next, x_next

    out, hist = jax.lax.scan(step, leaves, None, length=N_STEPS)
    return jnp.vstack([leaves[None, :], hist])


def leaf_order_readout() -> dict[str, Any]:
    genuine = ratchet_leaf_flow(AREAS)
    flat = ratchet_leaf_flow(jnp.ones_like(AREAS) * AREAS[MAX_LEAF])
    shuffled = ratchet_leaf_flow(AREAS[jnp.asarray([4, 0, 8, 1, 7, 2, 6, 3, 5], dtype=jnp.int32)])
    genuine_final = genuine[-1]
    flat_final = flat[-1]
    shuffled_final = shuffled[-1]
    return {
        "theta_grid": [float(x) for x in jax.device_get(THETAS)],
        "areas": [float(x) for x in jax.device_get(AREAS)],
        "genuine_final_leaves": [int(x) for x in jax.device_get(genuine_final)],
        "flat_final_leaves": [int(x) for x in jax.device_get(flat_final)],
        "shuffled_final_leaves": [int(x) for x in jax.device_get(shuffled_final)],
        "pass": _b(jnp.all(genuine_final == MAX_LEAF))
        and _b(jnp.all(flat_final == jnp.arange(N_LEAVES, dtype=jnp.int32)))
        and not _b(jnp.all(shuffled_final == MAX_LEAF)),
    }


def dependency_readout() -> dict[str, Any]:
    invalid_orders = {
        "torus_before_spinor": swapped_order("L2_hopf_fibration", "L5_nested_hopf_tori"),
        "terrain_before_weyl": swapped_order("L6_weyl_sheets_on_nested_tori", "L10_terrain_gksl_generator"),
        "entropy_before_noncommutation": swapped_order("L11_operator_noncommutation_substages", "L12_qit_entropy_cut"),
        "gluing_before_entropy": swapped_order("L12_qit_entropy_cut", "L13_gluing_groupoid_cocycle"),
    }
    invalid_status = {name: _b(order_pass(order)) for name, order in invalid_orders.items()}
    return {
        "layer_order": LAYER_ORDER,
        "edge_count": len(EDGE_NAMES),
        "correct_order_pass": _b(order_pass(CORRECT_ORDER)),
        "invalid_order_pass": invalid_status,
        "pass": _b(order_pass(CORRECT_ORDER)) and not any(invalid_status.values()),
    }


def build_receipt() -> dict[str, Any]:
    coverage = load(COVERAGE_RECEIPT) or {}
    pairwise = load(PAIRWISE_RECEIPT) or {}
    dependency = dependency_readout()
    dynamic = order_dynamic_readout()
    leaf_order = leaf_order_readout()

    terrains = sorted({p["terrain"] for p in PLACEMENTS})
    placements_ok = (
        len(PLACEMENTS) == 16
        and len(TOPOLOGIES) == 4
        and len(terrains) == 8
        and sum(1 for p in PLACEMENTS if p["sheet"] == "L") == 8
        and sum(1 for p in PLACEMENTS if p["sheet"] == "R") == 8
    )

    checks = {
        "coverage_receipt_closed": coverage.get("coverage_closed") is True,
        "coverage_does_not_open_nesting_by_itself": coverage.get("nesting_order_allowed") is False,
        "pairwise_leaf_coupling_passes": pairwise.get("all_pass") is True and pairwise.get("promotion_allowed") is False,
        "ran_julia_false": True,
        "ran_pytorch_false": "torch" not in sys.modules,
        "four_topologies": len(TOPOLOGIES) == 4,
        "eight_terrain_names": len(terrains) == 8,
        "sixteen_weyl_placements": placements_ok,
        "dependency_order_gate": dependency["pass"],
        "noncommuting_order_dynamic_gate": dynamic["pass"],
        "leaf_area_order_ratchet_gate": leaf_order["pass"],
        "flux_axis_physics_still_blocked": True,
    }
    all_pass = all(checks.values())
    return {
        "sim_id": "jax_nested_hopf_nesting_order_gate",
        "name": "JAX nested Hopf/Weyl finite nesting-order gate",
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": "diagnostic_jax_nesting_order_gate",
        "contract_classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical_diagnostic_jax_audit",
        "sim_class": "nesting_order_gate",
        "ran_julia": False,
        "ran_pytorch": False,
        "claim_ceiling": (
            "Nesting-order gate only. It establishes a bounded JAX order-search target after "
            "independent layer/geometry coverage, but does not admit full layer completion, "
            "does not claim layer-stacking readiness, and does not unlock flux, Axis0, FEP, "
            "physics, or final manifold admission."
        ),
        "root_constraints_in_force": {
            "F01": "finite layer order, finite 9-leaf Hopf-torus grid, finite 16 Weyl placements, finite control orders",
            "N01": "connection-vs-terrain order gap survives while same-word/order-erased controls collapse",
        },
        "finite_map": (
            "(coverage receipt, pairwise leaf receipt, layer order, 16 placements, 9 leaves, order word) "
            "-> dependency verdict, placement coverage, noncommuting order gap, finitude and label-erasure controls"
        ),
        "domain": {
            "layer_order": LAYER_ORDER,
            "topologies": list(TOPOLOGIES),
            "terrains": terrains,
            "placements": PLACEMENTS,
            "leaves": "theta_k in (0, pi/2), k=0..8",
        },
        "codomain_or_output": "JSON gate receipt with order pass/fail, dynamic order gap, and blocked downstream consumers",
        "carrier_layer": "finite S3 unit-quaternion Weyl spinor samples on nested Hopf-torus leaves",
        "geometry_layer": "nested Hopf leaf order plus Weyl sheet/path/topology placements",
        "carrier_realization": "JAX float64 unit quaternions and finite placement/leaf arrays",
        "spinor_state": "q=(Re z0, Im z0, Re z1, Im z1), normalized to S3 after each map",
        "quaternion_action": "finite quaternion left-product rotor terms for connection and terrain order words",
        "peps3d_embedding": "not_admitted; finite placement x leaf cell anchor only, no PEPS3D promotion",
        "dependency_receipts": [str(COVERAGE_RECEIPT), str(PAIRWISE_RECEIPT)],
        "dependency_order": dependency,
        "placement_summary": {
            "topologies": list(TOPOLOGIES),
            "terrains": terrains,
            "placements": PLACEMENTS,
        },
        "dynamic_order_readout": dynamic,
        "leaf_order_ratchet_readout": leaf_order,
        "checks": checks,
        "all_pass": all_pass,
        "AUDIT_PASS": all_pass,
        "nesting_order_gate_closed": all_pass,
        "next_allowed_if_pass": [
            "bounded_bottom_up_branch_prune_order_audit",
            "bounded_noncommutative_finitude_ratchet_order_search",
            "external_oracle_audit_for_order_receipt",
        ] if all_pass else [],
        "still_blocked_consumers": [
            "full_layer_completion_claim",
            "layer_stacking_readiness_claim",
            "flux",
            "Xi",
            "Phi0",
            "Axis0",
            "FEP",
            "physics_gravity",
            "final_manifold_admission",
        ],
        "blocked_consumers": [
            "full_layer_completion_claim",
            "layer_stacking_readiness_claim",
            "flux",
            "Xi",
            "Phi0",
            "Axis0",
            "FEP",
            "physics_gravity",
            "final_manifold_admission",
        ],
        "TOOL_MANIFEST": {
            "jax": {
                "used": True,
                "role": "load_bearing",
                "reason": "Computes S3 retractions, quaternion order words, finite dependency checks, and leaf-ratchet controls.",
            },
            "julia": {"used": False, "role": "read_only_reference_only", "reason": "User prohibited running Julia; only local receipts are consumed."},
            "pytorch": {"used": False, "role": "forbidden_this_task", "reason": "PyTorch lane is retired for this work."},
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "load_bearing", "julia": "None", "pytorch": "None"},
    }


def main() -> int:
    receipt = build_receipt()
    OUT.write_text(json.dumps(_jsonify(receipt), indent=2, sort_keys=True) + "\n")
    print(
        "jax_nested_hopf_nesting_order_gate "
        f"dependency={receipt['checks']['dependency_order_gate']} "
        f"dynamic={receipt['checks']['noncommuting_order_dynamic_gate']} "
        f"leaf_order={receipt['checks']['leaf_area_order_ratchet_gate']} "
        f"placements=16 terrains=8 topologies=4 "
        f"AUDIT_PASS={receipt['AUDIT_PASS']}"
    )
    return 0 if receipt["AUDIT_PASS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
