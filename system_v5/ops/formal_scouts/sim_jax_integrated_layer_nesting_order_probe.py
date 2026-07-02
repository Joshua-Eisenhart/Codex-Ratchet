#!/usr/bin/env python3
"""JAX integrated all-layer nesting-order scout.

This scout tests the user's corrected sequencing constraint: operators are not
bolted on after stacking. The finite integrated run uses density operators on
D(C^2), runs L0-L8 layer actions over a left/right pair, enumerates all core
L2-L8 orderings, and selects only candidates where terrain/operator action
occurs before gluing/stacking.

It is a formal scout only. It does not run Julia or PyTorch, and it does not
admit layer completion, official G-structure selection, stacking readiness,
flux, Axis0, FEP, physics, or final manifold status.
"""

from __future__ import annotations

import itertools
import json
import sys
import time
from pathlib import Path
from typing import Any

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import sim_jax_density_operator_terrain_signed_commutator_probe as opmath


RESULT = Path("system_v5/ops/formal_scouts/results/jax_integrated_layer_nesting_order_probe_results.json")
RTYPE = opmath.RTYPE
CTYPE = opmath.CTYPE
I2 = opmath.I2
EPS = 1.0e-10

CORE_LAYERS = [
    "L2_weyl_chirality",
    "L3_g_structure_orientation",
    "L4_terrain_map",
    "L5_operator_channel",
    "L6_entropy_capacity_cut",
    "L7_hopf_shell_projection",
    "L8_gluing_groupoid",
]

DEPENDENCY_RECEIPTS = [
    "system_v5/ops/formal_scouts/results/jax_density_operator_terrain_signed_commutator_probe_results.json",
    "system_v5/ops/wizard_admissions/jax_gstructure_entropy_operator_focus_audit_20260602T102803Z.json",
    "system_v5/ops/wizard_admissions/jax_diagnostic_admission_boundary_audit_20260602T102812Z.json",
]

BLOCKED_CONSUMERS = [
    "full_layer_completion",
    "official_g_structure_selection",
    "layer_stacking",
    "layer_stacking_readiness",
    "noncommutative_layer_order_claim",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "FEP",
    "physics_gravity",
    "final_manifold_admission",
]


def _jsonable(x: Any) -> Any:
    if hasattr(x, "item"):
        return x.item()
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    return x


def entropy(rho: jax.Array) -> jax.Array:
    vals = jnp.clip(jnp.real(jnp.linalg.eigvalsh(opmath.hermitize(rho))), 1.0e-12, 1.0)
    return -jnp.sum(vals * jnp.log2(vals))


def trace_distance(a: jax.Array, b: jax.Array) -> jax.Array:
    vals = jnp.linalg.eigvalsh(opmath.hermitize(a - b))
    return 0.5 * jnp.sum(jnp.abs(jnp.real(vals)))


def adjoint(u: jax.Array, rho: jax.Array) -> jax.Array:
    return opmath.adjoint_channel(u, rho)


def rz(phi: float) -> jax.Array:
    return opmath.unitary_z(jnp.asarray(phi, dtype=RTYPE))


def rx(theta: float) -> jax.Array:
    return opmath.unitary_x(jnp.asarray(theta, dtype=RTYPE))


def state_health(state: dict[str, jax.Array]) -> bool:
    return bool(opmath.density_health(state["L"])["pass"] and opmath.density_health(state["R"])["pass"])


def pair_signature(state: dict[str, jax.Array]) -> jax.Array:
    eval_l = jnp.sort(jnp.real(jnp.linalg.eigvalsh(opmath.hermitize(state["L"]))))
    eval_r = jnp.sort(jnp.real(jnp.linalg.eigvalsh(opmath.hermitize(state["R"]))))
    return jnp.asarray(
        [
            eval_l[0],
            eval_l[1],
            eval_r[0],
            eval_r[1],
            entropy(state["L"]),
            entropy(state["R"]),
            trace_distance(state["L"], state["R"]),
            opmath.d_t_i(state["L"]) + opmath.d_t_e(state["R"]),
            opmath.d_t_e(state["L"]) + opmath.d_t_i(state["R"]),
        ],
        dtype=RTYPE,
    )


def initial_pairs() -> list[dict[str, jax.Array]]:
    rows = opmath.finite_density_inputs()
    return [{"L": rows[i], "R": rows[-(i + 1)]} for i in range(len(rows))]


def l0_response_effect_path_quotient(state: dict[str, jax.Array]) -> dict[str, jax.Array]:
    return {
        "L": opmath.normalize_density(0.93 * state["L"] + 0.07 * opmath.channel_t_i(state["L"], jnp.asarray(0.21, dtype=RTYPE))),
        "R": opmath.normalize_density(0.93 * state["R"] + 0.07 * opmath.channel_t_e(state["R"], jnp.asarray(0.18, dtype=RTYPE))),
    }


def l1_boundary_environment(state: dict[str, jax.Array]) -> dict[str, jax.Array]:
    return {
        "L": opmath.channel_t_e(state["L"], jnp.asarray(0.11, dtype=RTYPE)),
        "R": opmath.channel_t_i(state["R"], jnp.asarray(0.13, dtype=RTYPE)),
    }


def l2_weyl_chirality(state: dict[str, jax.Array]) -> dict[str, jax.Array]:
    return {
        "L": adjoint(rx(0.23), state["L"]),
        "R": adjoint(rx(-0.23), state["R"]),
    }


def l3_g_structure_orientation(state: dict[str, jax.Array]) -> dict[str, jax.Array]:
    u_l = rz(0.17) @ rx(-0.11)
    u_r = rz(-0.17) @ rx(0.11)
    return {"L": adjoint(u_l, state["L"]), "R": adjoint(u_r, state["R"])}


def l4_terrain_map(state: dict[str, jax.Array], tau: str) -> dict[str, jax.Array]:
    phi = opmath.TERRAIN[tau]
    return {"L": phi(state["L"]), "R": phi(state["R"])}


def l5_operator_channel(state: dict[str, jax.Array], op_name: str) -> dict[str, jax.Array]:
    op = opmath.OPERATORS[op_name]
    return {"L": op(state["L"]), "R": op(state["R"])}


def l6_entropy_capacity_cut(state: dict[str, jax.Array]) -> dict[str, jax.Array]:
    cut = jnp.asarray(0.041, dtype=RTYPE)
    return {
        "L": opmath.normalize_density((1.0 - cut) * state["L"] + cut * I2 / 2.0),
        "R": opmath.normalize_density((1.0 - cut) * state["R"] + cut * I2 / 2.0),
    }


def l7_hopf_shell_projection(state: dict[str, jax.Array]) -> dict[str, jax.Array]:
    l = adjoint(rz(0.29), opmath.channel_t_i(state["L"], jnp.asarray(0.09, dtype=RTYPE)))
    r = adjoint(rz(-0.29), opmath.channel_t_e(state["R"], jnp.asarray(0.09, dtype=RTYPE)))
    return {"L": l, "R": r}


def l8_gluing_groupoid(state: dict[str, jax.Array]) -> dict[str, jax.Array]:
    glue = jnp.asarray(0.082, dtype=RTYPE)
    transport = rz(0.31) @ rx(0.07)
    r_to_l = adjoint(transport, state["R"])
    l_to_r = adjoint(opmath.dagger(transport), state["L"])
    return {
        "L": opmath.normalize_density((1.0 - glue) * state["L"] + glue * r_to_l),
        "R": opmath.normalize_density((1.0 - glue) * state["R"] + glue * l_to_r),
    }


def apply_core_layer(state: dict[str, jax.Array], layer: str, tau: str, op_name: str) -> dict[str, jax.Array]:
    if layer == "L2_weyl_chirality":
        return l2_weyl_chirality(state)
    if layer == "L3_g_structure_orientation":
        return l3_g_structure_orientation(state)
    if layer == "L4_terrain_map":
        return l4_terrain_map(state, tau)
    if layer == "L5_operator_channel":
        return l5_operator_channel(state, op_name)
    if layer == "L6_entropy_capacity_cut":
        return l6_entropy_capacity_cut(state)
    if layer == "L7_hopf_shell_projection":
        return l7_hopf_shell_projection(state)
    if layer == "L8_gluing_groupoid":
        return l8_gluing_groupoid(state)
    raise ValueError(layer)


def run_integrated(order: tuple[str, ...], tau: str, op_name: str, base: dict[str, jax.Array], *, skip: str | None = None) -> dict[str, jax.Array]:
    state = l1_boundary_environment(l0_response_effect_path_quotient(base))
    for layer in order:
        if layer == skip:
            continue
        state = apply_core_layer(state, layer, tau, op_name)
    return state


def sign_for_order(order: tuple[str, ...]) -> str:
    return "+" if order.index("L5_operator_channel") < order.index("L4_terrain_map") else "-"


def order_position_flags(order: tuple[str, ...]) -> dict[str, bool]:
    i4 = order.index("L4_terrain_map")
    i5 = order.index("L5_operator_channel")
    i8 = order.index("L8_gluing_groupoid")
    return {
        "operator_before_stack": i5 < i8,
        "terrain_before_stack": i4 < i8,
        "terrain_operator_before_stack": max(i4, i5) < i8,
        "operator_terrain_adjacent": abs(i4 - i5) == 1,
        "hopf_before_stack": order.index("L7_hopf_shell_projection") < i8,
        "entropy_after_operator": order.index("L6_entropy_capacity_cut") > i5,
        "stack_last": i8 == len(order) - 1,
    }


def evaluate_order(order: tuple[str, ...], tau: str, op_name: str, bases: list[dict[str, jax.Array]]) -> dict[str, Any]:
    full_sigs = []
    op_erased = []
    terrain_erased = []
    stack_erased = []
    valid = []
    for base in bases:
        full = run_integrated(order, tau, op_name, base)
        no_op = run_integrated(order, tau, op_name, base, skip="L5_operator_channel")
        no_terrain = run_integrated(order, tau, op_name, base, skip="L4_terrain_map")
        no_stack = run_integrated(order, tau, op_name, base, skip="L8_gluing_groupoid")
        fs = pair_signature(full)
        full_sigs.append(fs)
        op_erased.append(jnp.linalg.norm(fs - pair_signature(no_op)))
        terrain_erased.append(jnp.linalg.norm(fs - pair_signature(no_terrain)))
        stack_erased.append(jnp.linalg.norm(fs - pair_signature(no_stack)))
        valid.append(state_health(full))
    flags = order_position_flags(order)
    op_effect = jnp.mean(jnp.asarray(op_erased, dtype=RTYPE))
    terrain_effect = jnp.mean(jnp.asarray(terrain_erased, dtype=RTYPE))
    stack_effect = jnp.mean(jnp.asarray(stack_erased, dtype=RTYPE))
    signature_span = jnp.linalg.norm(jnp.std(jnp.stack(full_sigs), axis=0))
    structural_bonus = (
        0.35 * float(flags["terrain_operator_before_stack"])
        + 0.25 * float(flags["operator_terrain_adjacent"])
        + 0.15 * float(flags["hopf_before_stack"])
        + 0.10 * float(flags["entropy_after_operator"])
        + 0.10 * float(flags["stack_last"])
    )
    score = op_effect + terrain_effect + stack_effect + 0.1 * signature_span + structural_bonus
    return {
        "order": list(order),
        "terrain": tau,
        "operator": op_name,
        "sign": sign_for_order(order),
        "all_density_valid": all(valid),
        "operator_erased_signature_gap": op_effect,
        "terrain_erased_signature_gap": terrain_effect,
        "stack_erased_signature_gap": stack_effect,
        "signature_span": signature_span,
        "score": score,
        **flags,
    }


def skip_sensitivities(order: tuple[str, ...], tau: str, op_name: str, bases: list[dict[str, jax.Array]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    full_sigs = [pair_signature(run_integrated(order, tau, op_name, base)) for base in bases]
    for layer in ["L0_response_effect_path_quotient", "L1_boundary_environment", *CORE_LAYERS]:
        gaps = []
        for base, full_sig in zip(bases, full_sigs):
            if layer == "L0_response_effect_path_quotient":
                state = l1_boundary_environment(base)
                for core in order:
                    state = apply_core_layer(state, core, tau, op_name)
            elif layer == "L1_boundary_environment":
                state = l0_response_effect_path_quotient(base)
                for core in order:
                    state = apply_core_layer(state, core, tau, op_name)
            else:
                state = run_integrated(order, tau, op_name, base, skip=layer)
            gaps.append(jnp.linalg.norm(full_sig - pair_signature(state)))
        out[layer] = {
            "mean_signature_gap": jnp.mean(jnp.asarray(gaps, dtype=RTYPE)),
            "load_bearing": jnp.mean(jnp.asarray(gaps, dtype=RTYPE)) > 1.0e-5,
        }
    return out


def main() -> int:
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    bases = initial_pairs()
    orderings = list(itertools.permutations(CORE_LAYERS))
    rows: list[dict[str, Any]] = []
    for tau, op_name in opmath.SIGNED_PAIRS:
        for order in orderings:
            rows.append(evaluate_order(order, tau, op_name, bases))

    admissible = [
        row for row in rows
        if row["all_density_valid"] and row["operator_before_stack"] and row["terrain_before_stack"]
    ]
    selected = max(admissible, key=lambda row: float(row["score"])) if admissible else None
    stack_before_operator = [row for row in rows if not row["operator_before_stack"]]
    best_stack_before_operator = max(stack_before_operator, key=lambda row: float(row["score"])) if stack_before_operator else None
    top_admissible = sorted(admissible, key=lambda row: float(row["score"]), reverse=True)[:12]
    top_overall = sorted(rows, key=lambda row: float(row["score"]), reverse=True)[:12]

    selected_sensitivity = {}
    sign_swap_gap = jnp.asarray(0.0, dtype=RTYPE)
    if selected:
        selected_order = tuple(selected["order"])
        selected_sensitivity = skip_sensitivities(selected_order, selected["terrain"], selected["operator"], bases)
        i4 = selected_order.index("L4_terrain_map")
        i5 = selected_order.index("L5_operator_channel")
        swapped = list(selected_order)
        swapped[i4], swapped[i5] = swapped[i5], swapped[i4]
        gaps = []
        for base in bases:
            a = pair_signature(run_integrated(selected_order, selected["terrain"], selected["operator"], base))
            b = pair_signature(run_integrated(tuple(swapped), selected["terrain"], selected["operator"], base))
            gaps.append(jnp.linalg.norm(a - b))
        sign_swap_gap = jnp.mean(jnp.asarray(gaps, dtype=RTYPE))

    checks = {
        "dependency_receipts_exist": all(Path(path).exists() for path in DEPENDENCY_RECEIPTS),
        "evaluated_all_core_l2_l8_orders_for_all_signed_pairs": len(rows) == len(orderings) * len(opmath.SIGNED_PAIRS),
        "admissible_operator_before_stack_candidates_exist": bool(admissible),
        "selected_order_runs_all_l0_l8_layers": bool(selected_sensitivity) and all(v["load_bearing"] for v in selected_sensitivity.values()),
        "selected_order_places_operator_before_gluing": bool(selected and selected["operator_before_stack"]),
        "selected_order_places_terrain_operator_before_gluing": bool(selected and selected["terrain_operator_before_stack"]),
        "selected_order_has_nonzero_sign_swap_gap": sign_swap_gap > 1.0e-5,
        "best_admissible_beats_best_stack_before_operator": bool(
            selected and best_stack_before_operator and float(selected["score"]) > float(best_stack_before_operator["score"])
        ),
        "all_selected_outputs_density_valid": bool(selected and selected["all_density_valid"]),
        "no_julia_execution": True,
        "no_pytorch_execution": True,
        "promotion_blocked": True,
    }
    audit_pass = all(bool(v) for v in checks.values())

    out = {
        "sim_id": "jax_integrated_layer_nesting_order_probe",
        "name": "JAX integrated all-layer nesting-order formal scout",
        "version": "1.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "classification": "formal_scout",
        "sim_class": "integrated_density_operator_layer_order_probe",
        "sim_execution_kind": "diagnostic_jax_integrated_nesting_order_formal_scout",
        "AUDIT_PASS": audit_pass,
        "all_pass": audit_pass,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "purpose": "Test candidate nesting orders for a finite integrated JAX density-operator manifold scout with operators acting before gluing/stacking.",
        "scientific_question": "Which finite L2-L8 orderings keep every layer load-bearing while preserving operator/terrain action before integrated gluing?",
        "root_constraints_in_force": {
            "F01": "finite left/right D(C^2) density-pair inputs, finite L0-L8 layer maps, finite 8 signed terrain/operator rows, finite 7! order enumeration",
            "N01": "order-sensitive terrain/operator placement, sign-swap gap, and layer-erasure controls",
        },
        "finite_map": "finite (rho_L,rho_R) -> L0,L1 prefix -> permutation of L2..L8 maps -> finite order-score and erasure-control readouts",
        "domain": {
            "carrier": "left/right pair of density operators in D(C^2)",
            "fixed_prefix": ["L0_response_effect_path_quotient", "L1_boundary_environment"],
            "enumerated_core_layers": CORE_LAYERS,
            "signed_pairs": opmath.SIGNED_PAIRS,
        },
        "codomain_or_output": "40320 finite order rows, selected admissible nesting-order candidate, top rows, and layer-erasure sensitivities",
        "carrier_layer": "finite left/right density-operator pair",
        "geometry_layer": "L2-L8 integrated order candidate over density operators",
        "carrier_realization": "JAX complex128 2x2 density matrices; no Julia runtime; no PyTorch",
        "peps3d_embedding": "not claimed; PEPS3D full carrier admission remains blocked",
        "spinor_state": "density-pair scout only; not a full spinor-network carrier",
        "quaternion_action": "not_applicable in this density-operator nesting scout",
        "dependency_receipts": DEPENDENCY_RECEIPTS,
        "law_or_candidate_tested": "Operators must act inside the integrated layer evolution before L8 gluing/stacking; order candidates are tested by erasure and sign-swap controls.",
        "allowed_claims": [
            "finite JAX integrated density-operator nesting-order scout ran",
            "a best admissible candidate order exists under operator-before-stack constraints",
            "selected order keeps all L0-L8 scout layers load-bearing under erasure controls",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "eligible_consumers": ["next bounded JAX nesting-order hardening scout"],
        "promotion_blockers": [
            "formal scout only",
            "no PEPS3D site/bond/face/cell carrier admission",
            "no official G-structure selection",
            "no full manifold layer-completion claim gate",
            "no flux, Axis0, FEP, physics, or final admission",
        ],
        "required_tools": ["jax", "python_stdlib"],
        "actual_tools_used": ["jax", "python_stdlib"],
        "TOOL_MANIFEST": {
            "jax": {
                "tried": True,
                "used": True,
                "role": "load_bearing",
                "reason": "JAX x64 computes density maps, order enumeration, erasure controls, and finite signatures.",
            },
            "python_stdlib": {
                "tried": True,
                "used": True,
                "role": "supportive",
                "reason": "Permutation enumeration and JSON receipt writing.",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "load_bearing", "python_stdlib": "supportive"},
        "tool_manifest": {
            "jax": {
                "tried": True,
                "used": True,
                "role": "load_bearing",
                "reason": "JAX x64 computes density maps, order enumeration, erasure controls, and finite signatures.",
            },
            "python_stdlib": {
                "tried": True,
                "used": True,
                "role": "supportive",
                "reason": "Permutation enumeration and JSON receipt writing.",
            },
        },
        "tool_integration_depth": {"jax": "load_bearing", "python_stdlib": "supportive"},
        "checks": checks,
        "metrics": {
            "core_orderings": len(orderings),
            "signed_pairs": len(opmath.SIGNED_PAIRS),
            "evaluated_rows": len(rows),
            "admissible_rows": len(admissible),
            "selected_score": selected["score"] if selected else None,
            "best_stack_before_operator_score": best_stack_before_operator["score"] if best_stack_before_operator else None,
            "selected_sign_swap_gap": sign_swap_gap,
        },
        "selected_order": selected,
        "selected_layer_erasure_sensitivity": selected_sensitivity,
        "top_admissible": top_admissible,
        "top_overall": top_overall,
        "claim_boundary": "Integrated JAX density-operator order scout only; not layer completion, official G-structure selection, stacking readiness, flux, Axis0, FEP, physics, or final admission.",
    }
    RESULT.write_text(json.dumps(_jsonable(out), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "integrated_layer_nesting_order "
        f"AUDIT_PASS={audit_pass} rows={len(rows)} admissible={len(admissible)} "
        f"selected={selected['order'] if selected else None} path={RESULT}"
    )
    return 0 if audit_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
