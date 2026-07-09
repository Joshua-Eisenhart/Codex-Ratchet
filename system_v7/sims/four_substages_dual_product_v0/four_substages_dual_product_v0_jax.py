#!/usr/bin/env python3
"""Conditional four-substage emergence on the source operator product.

This probe asks a narrow question: after the source has selected the x/z
operator axes and the dephasing/rotation family split, do the four exact QIT
operator classes form a minimal closed one-coordinate-at-a-time cycle?

It does not derive the source premises, sequential engine dynamics, Axis-6
placement, two engine types, personalities, perception, or usefulness.
"""

from __future__ import annotations

import itertools
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp


classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "nonclassical"

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing batched channel action, entropy readout, and structural quotient",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing collision assertion over measured axis/family signatures with erased-coordinate controls",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "independent load-bearing collision-assertion cross-check with the same controls",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_json": "supportive",
}

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
TOL = 1.0e-9
AXIS_NAMES = ("x", "y", "z")
FAMILY_NAMES = ("dephasing", "rotation")


def dephasing_ptm(axis: int, q: float) -> jax.Array:
    values = jnp.full((3,), 1.0 - q, dtype=jnp.float64)
    return jnp.diag(values.at[axis].set(1.0))


def rotation_ptm(axis: int, theta: float) -> jax.Array:
    c, s = jnp.cos(theta), jnp.sin(theta)
    if axis == 0:
        return jnp.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])
    if axis == 1:
        return jnp.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])
    return jnp.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


PROBES = jnp.array(
    [
        [0.51, 0.23, -0.37],
        [-0.42, 0.49, 0.19],
        [0.26, -0.55, 0.31],
        [-0.33, -0.28, 0.58],
        [0.61, -0.17, -0.22],
        [-0.19, 0.36, -0.62],
    ],
    dtype=jnp.float64,
)


def density_from_bloch(v: jax.Array) -> jax.Array:
    x, y, z = v
    return 0.5 * jnp.array(
        [[1.0 + z, x - 1.0j * y], [x + 1.0j * y, 1.0 - z]],
        dtype=jnp.complex128,
    )


def entropy_bits(v: jax.Array) -> jax.Array:
    eigenvalues = jnp.linalg.eigvalsh(density_from_bloch(v))
    safe = jnp.clip(eigenvalues, 1.0e-15, 1.0)
    return -jnp.sum(safe * jnp.log2(safe))


def channel_features(matrices: jax.Array) -> tuple[jax.Array, jax.Array, jax.Array]:
    outputs = jax.vmap(lambda matrix: jax.vmap(lambda v: matrix @ v)(PROBES))(matrices)
    before = jax.vmap(entropy_bits)(PROBES)
    after = jax.vmap(jax.vmap(entropy_bits))(outputs)
    delta_entropy = after - before[None, :]
    orthogonality_error = jax.vmap(
        lambda matrix: jnp.linalg.norm(matrix.T @ matrix - jnp.eye(3))
    )(matrices)
    inferred_axis = jax.vmap(lambda matrix: jnp.argmax(jnp.diag(matrix)))(matrices)
    return delta_entropy, orthogonality_error, inferred_axis


def infer_rows(specs: list[dict]) -> list[dict]:
    matrices = jnp.stack([spec["matrix"] for spec in specs])
    delta_entropy, orthogonality_error, inferred_axis = channel_features(matrices)
    rows = []
    for index, spec in enumerate(specs):
        orth_error = float(orthogonality_error[index])
        max_abs_delta = float(jnp.max(jnp.abs(delta_entropy[index])))
        max_delta = float(jnp.max(delta_entropy[index]))
        family = "rotation" if orth_error < TOL and max_abs_delta < TOL else "dephasing"
        axis = AXIS_NAMES[int(inferred_axis[index])]
        rows.append(
            {
                "name": spec["name"],
                "declared_axis": AXIS_NAMES[spec["axis"]],
                "declared_family": spec["family"],
                "inferred_axis": axis,
                "inferred_family": family,
                "signature": [axis, family],
                "orthogonality_error": orth_error,
                "max_entropy_delta_bits": max_delta,
                "max_abs_entropy_delta_bits": max_abs_delta,
                "density_outputs_valid": bool(
                    jnp.all(
                        jax.vmap(
                            lambda v: jnp.min(jnp.linalg.eigvalsh(density_from_bloch(v)))
                        )(jax.vmap(lambda v: spec["matrix"] @ v)(PROBES))
                        >= -TOL
                    )
                ),
            }
        )
    return rows


def canonical_specs() -> list[dict]:
    return [
        {"name": "Ti", "axis": 2, "family": "dephasing", "matrix": dephasing_ptm(2, 1.0)},
        {"name": "Fe", "axis": 2, "family": "rotation", "matrix": rotation_ptm(2, math.pi / 4)},
        {"name": "Fi", "axis": 0, "family": "rotation", "matrix": rotation_ptm(0, math.pi / 4)},
        {"name": "Te", "axis": 0, "family": "dephasing", "matrix": dephasing_ptm(0, 1.0)},
    ]


def parameter_variant_specs() -> list[dict]:
    rows = []
    for axis, pinch_name, rotate_name in ((2, "Ti", "Fe"), (0, "Te", "Fi")):
        for q in (0.35, 0.8):
            rows.append(
                {
                    "name": f"{pinch_name}_q{q}",
                    "axis": axis,
                    "family": "dephasing",
                    "matrix": dephasing_ptm(axis, q),
                }
            )
        for theta in (0.37, 0.91):
            rows.append(
                {
                    "name": f"{rotate_name}_theta{theta}",
                    "axis": axis,
                    "family": "rotation",
                    "matrix": rotation_ptm(axis, theta),
                }
            )
    return rows


def one_coordinate_apart(left: tuple[str, str], right: tuple[str, str]) -> bool:
    return sum(a != b for a, b in zip(left, right)) == 1


def hamiltonian_cycles(vertices: list[tuple[str, str]], allow_diagonal: bool = False) -> list[list[tuple[str, str]]]:
    if len(vertices) < 3:
        return []
    start = vertices[0]
    cycles = []
    for tail in itertools.permutations(vertices[1:]):
        cycle = (start, *tail)
        pairs = list(zip(cycle, cycle[1:] + cycle[:1]))
        if all(allow_diagonal or one_coordinate_apart(a, b) for a, b in pairs):
            cycles.append(list(cycle))
    return cycles


def unoriented_cycle_key(cycle: list[tuple[str, str]]) -> tuple:
    enc = ["|".join(vertex) for vertex in cycle]
    variants = []
    for seq in (enc, list(reversed(enc))):
        variants.extend(tuple(seq[i:] + seq[:i]) for i in range(len(seq)))
    return min(variants)


def collision_truth(signatures: list[tuple[int, int]]) -> bool:
    return any(left == right for left, right in itertools.combinations(signatures, 2))


def z3_collision_verdict(signatures: list[tuple[int, int]]) -> str:
    import z3

    solver = z3.Solver()
    left_index, right_index = z3.Ints("left_index right_index")

    def select(values: list[int], index):
        term = z3.IntVal(values[-1])
        for position in reversed(range(len(values) - 1)):
            term = z3.If(index == position, z3.IntVal(values[position]), term)
        return term

    axes = [axis for axis, _ in signatures]
    families = [family for _, family in signatures]
    solver.add(
        0 <= left_index,
        left_index < len(signatures),
        0 <= right_index,
        right_index < len(signatures),
        left_index < right_index,
        select(axes, left_index) == select(axes, right_index),
        select(families, left_index) == select(families, right_index),
    )
    return str(solver.check())


def cvc5_collision_verdict(signatures: list[tuple[int, int]]) -> str:
    import cvc5
    from cvc5 import Kind

    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    integer = solver.getIntegerSort()
    left_index = solver.mkConst(integer, "left_index")
    right_index = solver.mkConst(integer, "right_index")

    def select(values: list[int], index):
        term = solver.mkInteger(values[-1])
        for position in reversed(range(len(values) - 1)):
            condition = solver.mkTerm(Kind.EQUAL, index, solver.mkInteger(position))
            term = solver.mkTerm(Kind.ITE, condition, solver.mkInteger(values[position]), term)
        return term

    axes = [axis for axis, _ in signatures]
    families = [family for _, family in signatures]
    constraints = [
        solver.mkTerm(Kind.LEQ, solver.mkInteger(0), left_index),
        solver.mkTerm(Kind.LT, left_index, solver.mkInteger(len(signatures))),
        solver.mkTerm(Kind.LEQ, solver.mkInteger(0), right_index),
        solver.mkTerm(Kind.LT, right_index, solver.mkInteger(len(signatures))),
        solver.mkTerm(Kind.LT, left_index, right_index),
        solver.mkTerm(Kind.EQUAL, select(axes, left_index), select(axes, right_index)),
        solver.mkTerm(Kind.EQUAL, select(families, left_index), select(families, right_index)),
    ]
    solver.assertFormula(solver.mkTerm(Kind.AND, *constraints))
    return str(solver.checkSat()).lower()


def solver_gate(rows: list[dict]) -> dict:
    axis_code = {"x": 0, "z": 1}
    family_code = {"dephasing": 0, "rotation": 1}
    full = [(axis_code[row["inferred_axis"]], family_code[row["inferred_family"]]) for row in rows]
    erase_axis = [(0, family) for _, family in full]
    erase_family = [(axis, 0) for axis, _ in full]
    verdicts = {
        "full": {
            "collision_expected": False,
            "python_collision": collision_truth(full),
            "z3": z3_collision_verdict(full),
            "cvc5": cvc5_collision_verdict(full),
        },
        "erase_axis": {
            "collision_expected": True,
            "python_collision": collision_truth(erase_axis),
            "z3": z3_collision_verdict(erase_axis),
            "cvc5": cvc5_collision_verdict(erase_axis),
        },
        "erase_family": {
            "collision_expected": True,
            "python_collision": collision_truth(erase_family),
            "z3": z3_collision_verdict(erase_family),
            "cvc5": cvc5_collision_verdict(erase_family),
        },
    }
    verdicts["polarity"] = "collision assertion: full UNSAT; erased-coordinate controls SAT"
    verdicts["pass"] = bool(
        verdicts["full"]["z3"] == "unsat"
        and "unsat" in verdicts["full"]["cvc5"]
        and verdicts["erase_axis"]["z3"] == "sat"
        and "sat" in verdicts["erase_axis"]["cvc5"]
        and "unsat" not in verdicts["erase_axis"]["cvc5"]
        and verdicts["erase_family"]["z3"] == "sat"
        and "sat" in verdicts["erase_family"]["cvc5"]
        and "unsat" not in verdicts["erase_family"]["cvc5"]
    )
    return verdicts


def main() -> int:
    canonical = infer_rows(canonical_specs())
    variants = infer_rows(parameter_variant_specs())
    expected = {
        "Ti": ["z", "dephasing"],
        "Te": ["x", "dephasing"],
        "Fi": ["x", "rotation"],
        "Fe": ["z", "rotation"],
    }
    inferred = {row["name"]: row["signature"] for row in canonical}
    canonical_ok = inferred == expected and all(row["density_outputs_valid"] for row in canonical)
    signatures = [tuple(row["signature"]) for row in canonical]
    unique_signatures = sorted(set(signatures))
    variant_signatures = sorted({tuple(row["signature"]) for row in variants})

    cycles = hamiltonian_cycles(unique_signatures)
    diagonal_cycles = hamiltonian_cycles(unique_signatures, allow_diagonal=True)
    unoriented = {unoriented_cycle_key(cycle) for cycle in cycles}
    operator_for = {tuple(value): name for name, value in expected.items()}
    operator_cycles = [[operator_for[vertex] for vertex in cycle] for cycle in cycles]
    missing_cell_cycles = hamiltonian_cycles(unique_signatures[:-1])

    erase_axis_count = len({family for _, family in unique_signatures})
    erase_family_count = len({axis for axis, _ in unique_signatures})
    add_y_count = len({(axis, family) for axis in ("x", "y", "z") for family in FAMILY_NAMES})
    smt = solver_gate(canonical)

    all_pass = bool(
        canonical_ok
        and len(unique_signatures) == 4
        and variant_signatures == unique_signatures
        and len(cycles) == 2
        and len(unoriented) == 1
        and not missing_cell_cycles
        and len(diagonal_cycles) > len(cycles)
        and erase_axis_count == 2
        and erase_family_count == 2
        and add_y_count == 6
        and smt["pass"]
    )

    result = {
        "schema": "codex_ratchet.four_substages_dual_product_v0.jax.v1",
        "sim_id": "four_substages_dual_product_v0_jax",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "stage_movement_allowed": False,
        "accepted_status_label": "passes local rerun" if all_pass else "runs",
        "sim_execution_kind": sim_execution_kind,
        "claim": "conditional 2-axis x 2-family operator product has four structural cells and one MSS square cycle up to reversal",
        "source_premises": {
            "pauli_bloch_operator_axes": ["x", "z"],
            "operator_families": ["dephasing", "rotation"],
            "axis6": "precedence wrapper around the same four maps; not an extra operator identity and not implemented here",
        },
        "canonical_rows": canonical,
        "canonical_inference_matches_source": canonical_ok,
        "structural_signature_count": len(unique_signatures),
        "structural_signatures": [list(signature) for signature in unique_signatures],
        "parameter_variant_rows": variants,
        "parameter_variant_quotient_count": len(variant_signatures),
        "mss_product_cycle": {
            "adjacency": "one coordinate changes per edge",
            "oriented_cycles_anchored_at_first_vertex": [[list(v) for v in cycle] for cycle in cycles],
            "operator_cycles": operator_cycles,
            "oriented_cycle_count": len(cycles),
            "unoriented_cycle_count": len(unoriented),
            "minimal_cycle_length": len(cycles[0]) if cycles else None,
        },
        "controls": {
            "erase_axis_structural_count": erase_axis_count,
            "erase_family_structural_count": erase_family_count,
            "remove_one_cell_closed_cycle_count": len(missing_cell_cycles),
            "allow_diagonal_jump_cycle_count": len(diagonal_cycles),
            "add_y_axis_structural_count": add_y_count,
            "interpretation": "four depends on the source-restricted x/z axes, the two family split, completeness, and one-coordinate MSS adjacency",
        },
        "dual_solver_collision_gate": smt,
        "jax": {
            "ran": True,
            "version": jax.__version__,
            "x64": bool(jax.config.jax_enable_x64),
            "devices": [device.platform for device in jax.devices()],
            "source_path": str(Path(__file__).resolve()),
            "packages_used": ["jax", "jax.numpy", "z3", "cvc5"],
            "aligned_packages_load_bearing": ["jax", "z3", "cvc5"],
            "reads_peer_result": False,
        },
        "tool_calls": [
            {
                "tool": "jax",
                "function": "jax.vmap + jax.numpy.linalg.eigvalsh",
                "input_object": "source operator PTMs x finite density probes",
                "output_object": "inferred axis/family signatures and entropy deltas",
                "positive_case": "four source cells inferred",
                "negative_control": "erased coordinate collapses the quotient",
                "boundary_case": "parameter variants quotient to the same structural cells",
                "demotion_condition": "inference mismatch or nonphysical density output",
                "gates": ["canonical_inference_matches_source", "structural_signature_count"],
            },
            {
                "tool": "z3/cvc5",
                "function": "finite collision-existence assertion",
                "input_object": "measured axis/family signature pairs",
                "output_object": "full UNSAT and erased-coordinate SAT verdicts",
                "positive_case": "full product has no collision",
                "negative_control": "axis/family erasures introduce a collision",
                "boundary_case": "finite four-row product",
                "demotion_condition": "solvers disagree or control does not flip",
                "gates": ["dual_solver_collision_gate", "all_pass"],
            },
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": "conditional structural emergence only; no sequential engine or architecture admission",
        "eligible_consumers": ["engine_dual_ratchet_substage_emergence_v0 candidate design"],
        "blocked_consumers": [
            "16x4 engine admission",
            "Type-1/Type-2 uniqueness",
            "Axis0 alignment",
            "perception or object formation",
            "personality or useful-work claims",
        ],
        "all_pass": all_pass,
    }

    RESULTS.mkdir(parents=True, exist_ok=True)
    result_path = RESULTS / "four_substages_dual_product_v0_jax_results.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "result_path": str(result_path),
        "canonical_match": canonical_ok,
        "structural_cells": len(unique_signatures),
        "oriented_mss_cycles": len(cycles),
        "unoriented_mss_cycles": len(unoriented),
        "erase_axis": erase_axis_count,
        "erase_family": erase_family_count,
        "add_y_axis": add_y_count,
        "dual_solver_gate": smt["pass"],
        "all_pass": all_pass,
    }, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
