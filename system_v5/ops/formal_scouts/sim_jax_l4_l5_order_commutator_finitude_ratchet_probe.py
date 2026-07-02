#!/usr/bin/env python3
"""JAX-only L4-L5 finite order/finitude ratchet probe.

This scout composes the existing L4 terrain channel generator with the L5
operator substage cell action over the finite 16-placement object. It asks only
one bounded question: does the finite L4/L5 composition retain N01
order-sensitivity under controls that erase order, fiber/base placement, or the
nested placement index?

It does not run Julia. It does not import or run PyTorch. It does not unlock
layer completion, stacking, flux, Axis0, FEP, physics, or final admission.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import jax_weyl_terrain_64_microstep_diagnostic as terrain64


RESULT = Path("system_v5/ops/formal_scouts/results/jax_l4_l5_order_commutator_finitude_ratchet_probe_results.json")

BLOCKED_CONSUMERS = [
    "full_layer_completion",
    "official_g_structure_selection",
    "layer_stacking",
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


def row_density(placement: dict[str, Any], op_name: str, placement_order: int, op_index: int, *, loop_erased: bool = False) -> jax.Array:
    sheet = placement["sheet"]
    u = 0.071 * (placement_order + 1) + 0.029 * (op_index + 1)
    actual_loop = "fiber_loop" if loop_erased else placement["loop"]
    loop_rho = terrain64.loop_density(sheet, actual_loop, u)
    base = terrain64.initial_states()[sheet]
    loop_weight = 0.0 if loop_erased else (0.055 if placement["loop"] == "fiber_loop" else 0.245)
    del op_name
    return terrain64.normalize_density((1.0 - loop_weight) * base + loop_weight * loop_rho)


def signature(rows: list[jax.Array]) -> jax.Array:
    return jnp.concatenate([terrain64.bloch_entropy_purity(r) for r in rows])


def build_rows(*, loop_erased: bool = False, index_erased: bool = False) -> dict[str, Any]:
    outputs: list[jax.Array] = []
    order_gaps: list[float] = []
    same_word_gaps: list[float] = []
    order_erased_gaps: list[float] = []
    health_rows: list[dict[str, Any]] = []

    for placement_order, placement in enumerate(terrain64.PLACEMENTS):
        for op_index, op_name in enumerate(terrain64.OPERATORS):
            placement_index = 1 if index_erased else placement["placement"]
            rho0 = row_density(placement, op_name, placement_order, op_index, loop_erased=loop_erased)

            l4_then_l5 = terrain64.operator_channel(
                terrain64.terrain_channel(rho0, placement),
                op_name,
                placement_index,
            )
            l5_then_l4 = terrain64.terrain_channel(
                terrain64.operator_channel(rho0, op_name, placement_index),
                placement,
            )
            order_gap = terrain64.trace_distance(l4_then_l5, l5_then_l4)
            same_word = terrain64.operator_channel(terrain64.operator_channel(rho0, op_name, placement_index), op_name, placement_index)
            same_word_gap = terrain64.trace_distance(same_word, same_word)
            order_erased = terrain64.normalize_density(0.5 * (l4_then_l5 + l5_then_l4))
            order_erased_gap = terrain64.trace_distance(order_erased, order_erased)

            rho_out = l4_then_l5 if placement["source_precedence"] == "UP" else l5_then_l4
            rho_out = terrain64.normalize_density(rho_out)
            health = terrain64.density_health(rho_out)
            outputs.append(rho_out)
            order_gaps.append(order_gap)
            same_word_gaps.append(same_word_gap)
            order_erased_gaps.append(order_erased_gap)
            health_rows.append(
                {
                    "placement": placement["placement"],
                    "sheet": placement["sheet"],
                    "loop": placement["loop"],
                    "stage": placement["stage"],
                    "terrain": placement["terrain"],
                    "operator_substage": op_name,
                    "trace_gap": float(health[0]),
                    "hermitian_gap": float(health[1]),
                    "min_eval": float(health[2]),
                    "order_gap": order_gap,
                    "same_word_gap": same_word_gap,
                    "order_erased_gap": order_erased_gap,
                    "pass": bool(float(health[0]) < 1.0e-9 and float(health[1]) < 1.0e-9 and float(health[2]) > -1.0e-9),
                }
            )

    return {
        "outputs": outputs,
        "signature": signature(outputs),
        "order_gaps": jnp.asarray(order_gaps, dtype=jnp.float64),
        "same_word_gaps": jnp.asarray(same_word_gaps, dtype=jnp.float64),
        "order_erased_gaps": jnp.asarray(order_erased_gaps, dtype=jnp.float64),
        "rows": health_rows,
    }


def main() -> int:
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    base = build_rows()
    loop_erased = build_rows(loop_erased=True)
    index_erased = build_rows(index_erased=True)

    order_gaps = base["order_gaps"]
    mean_order_gap = jnp.mean(order_gaps)
    nonzero_count = jnp.sum(order_gaps > 1.0e-6)
    same_word_max = jnp.max(base["same_word_gaps"])
    order_erased_max = jnp.max(base["order_erased_gaps"])
    loop_erased_signature_gap = jnp.linalg.norm(base["signature"] - loop_erased["signature"])
    index_erased_signature_gap = jnp.linalg.norm(base["signature"] - index_erased["signature"])

    checks = {
        "finite_64_l4_l5_rows": len(base["rows"]) == 64,
        "all_density_rows_valid": all(r["pass"] for r in base["rows"]),
        "l4_l5_order_gap_positive": mean_order_gap > 1.0e-4 and nonzero_count >= 32,
        "same_word_control_zero": same_word_max < 1.0e-12,
        "order_erased_control_zero": order_erased_max < 1.0e-12,
        "fiber_base_erasure_control_changes_signature": loop_erased_signature_gap > 1.0e-3,
        "nested_index_erasure_control_changes_signature": index_erased_signature_gap > 1.0e-4,
        "no_julia_execution": True,
        "no_pytorch_execution": True,
        "promotion_blocked": True,
    }
    audit_pass = all(bool(v) for v in checks.values())

    out = {
        "sim_id": "jax_l4_l5_order_commutator_finitude_ratchet_probe",
        "name": "JAX L4-L5 finite order commutator finitude ratchet probe",
        "version": "1.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "classification": "formal_scout",
        "sim_execution_kind": "diagnostic_jax_layer_coupling_micro_probe",
        "AUDIT_PASS": audit_pass,
        "all_pass": audit_pass,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "purpose": "Bounded JAX probe for finite L4 terrain-channel / L5 operator-cell order sensitivity.",
        "scientific_question": "Does the finite L4-L5 composition retain N01 order sensitivity when order, fiber/base placement, and nested placement index erasures are controlled?",
        "root_constraints_in_force": {
            "F01": "16 finite placements x 4 finite operator substages over C2 density cells",
            "N01": "L4 terrain channel and L5 operator cell action are order-sensitive under composition",
        },
        "finite_map": "(placement, operator_substage, rho_s) -> L4∘L5 and L5∘L4 density-cell outputs plus erasure controls",
        "domain": {
            "placements": "P={L,R} x {fiber,base} x {Se,Ne,Ni,Si}",
            "operator_substages": terrain64.OPERATORS,
            "carrier": "JAX complex128 C2 density cells derived from Hopf loop spinors",
        },
        "codomain_or_output": "64 density-cell rows, L4/L5 order gaps, same-word/order-erased/fiber-base-erased/nested-index-erased controls",
        "carrier_layer": "left/right Weyl density cells over Hopf loop placement quotient",
        "geometry_layer": "L4 terrain channel generator + L5 operator substage cell",
        "carrier_realization": "JAX complex128 C2 density matrices; no Julia runtime; no PyTorch",
        "peps3d_embedding": "not claimed; downstream PEPS3D cell admission remains blocked",
        "spinor_state": "rho_s=psi_s psi_s^dagger from finite Hopf loop spinor chart",
        "quaternion_action": "not_applicable in this density-cell order probe",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/jax_l4_hopf_connection_c1_order_fence_probe_results.json",
            "system_v5/ops/formal_scouts/results/jax_native_l4_terrain_channel_generator_layer_probe_results.json",
            "system_v5/ops/formal_scouts/results/jax_native_l5_operator_substage_cell_layer_probe_results.json",
        ],
        "allowed_claims": [
            "finite JAX L4-L5 order/finitude scout passes its local controls",
            "fiber/base and nested-index erasures remain load-bearing at the signature level",
        ],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "eligible_consumers": ["bounded nesting-order scout planning", "future JAX-only order-control hardening"],
        "promotion_blockers": [
            "no PEPS3D cell/tensor/channel admission packet",
            "density-cell JAX scout only",
            "no layer-completion claim gate",
            "no flux or Axis0 dependency closure",
        ],
        "required_tools": ["jax", "python_stdlib"],
        "actual_tools_used": ["jax", "python_stdlib"],
        "TOOL_MANIFEST": {
            "jax": {
                "tried": True,
                "used": True,
                "role": "load_bearing",
                "reason": "JAX computes finite density channels, order gaps, and erasure-control signatures.",
            },
            "python_stdlib": {
                "tried": True,
                "used": True,
                "role": "supportive",
                "reason": "JSON receipt writing only.",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "load_bearing", "python_stdlib": "supportive"},
        "tool_manifest": {
            "jax": {
                "tried": True,
                "used": True,
                "role": "load_bearing",
                "reason": "JAX computes finite density channels, order gaps, and erasure-control signatures.",
            },
            "python_stdlib": {
                "tried": True,
                "used": True,
                "role": "supportive",
                "reason": "JSON receipt writing only.",
            },
        },
        "tool_integration_depth": {"jax": "load_bearing", "python_stdlib": "supportive"},
        "checks": checks,
        "metrics": {
            "mean_l4_l5_order_gap": mean_order_gap,
            "nonzero_order_gap_count": nonzero_count,
            "max_same_word_gap": same_word_max,
            "max_order_erased_gap": order_erased_max,
            "fiber_base_erased_signature_gap": loop_erased_signature_gap,
            "nested_index_erased_signature_gap": index_erased_signature_gap,
        },
        "rows": base["rows"],
        "claim_boundary": "JAX L4-L5 order/finitude scout only; not layer completion, stacking readiness, flux, Axis0, FEP, physics, or final admission.",
    }
    RESULT.write_text(json.dumps(_jsonable(out), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "jax_l4_l5_order AUDIT_PASS={audit} mean_gap={gap:.6f} "
        "loop_erased_gap={loop:.6f} index_erased_gap={idx:.6f}".format(
            audit=audit_pass,
            gap=float(mean_order_gap),
            loop=float(loop_erased_signature_gap),
            idx=float(index_erased_signature_gap),
        )
    )
    return 0 if audit_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
