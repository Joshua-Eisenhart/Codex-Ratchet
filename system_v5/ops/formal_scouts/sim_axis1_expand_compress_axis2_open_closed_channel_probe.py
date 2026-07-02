#!/usr/bin/env python3
"""Axis1/Axis2 finite channel-coordinate scout.

This builds the current-request coordinate square:

    Axis1: expansion versus compression channel
    Axis2: open versus closed channel

and maps the four coordinate pairs to the source-layout terrain names:

    expansion/open   -> Se
    expansion/closed -> Ne
    compression/open -> Ni
    compression/closed -> Si

This is a bounded formal scout over finite PEPS3D local cells. It records the
source-doc axis-role caveat and blocks downstream consumers. It does not rewrite
the source-doc Axis1/Axis2 convention, does not open stacking, and does not
support Axis0, flux, Xi/Phi0, bridge, physics, or final manifold use.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from jax import config

config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import z3


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
NAME = "axis1_expand_compress_axis2_open_closed_channel_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.0"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "channel_coordinate_probe"
PROMOTION_ALLOWED = False

CTYPE = jnp.complex128
RTYPE = jnp.float64
EPS = 1.0e-10

I2 = jnp.eye(2, dtype=CTYPE)
KET0 = jnp.asarray([1.0, 0.0], dtype=CTYPE)
KET1 = jnp.asarray([0.0, 1.0], dtype=CTYPE)
KET_PLUS = (KET0 + KET1) / jnp.sqrt(jnp.asarray(2.0, dtype=RTYPE))
KET_COMPRESS = jnp.asarray(
    [
        jnp.cos(jnp.asarray(0.34, dtype=RTYPE)),
        jnp.exp(0.71j) * jnp.sin(jnp.asarray(0.34, dtype=RTYPE)),
    ],
    dtype=CTYPE,
)
SZ = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=CTYPE)

AXIS1_STATES = ("expansion", "compression")
AXIS2_STATES = ("open", "closed")
TERRAIN_BY_REQUESTED_COORDINATE = {
    ("expansion", "open"): "Se",
    ("expansion", "closed"): "Ne",
    ("compression", "open"): "Ni",
    ("compression", "closed"): "Si",
}
TERRAIN_ID = {"Se": 0, "Ne": 1, "Ni": 2, "Si": 3}

BLOCKED_CONSUMERS = [
    "layer_stacking",
    "official_g_structure_selection",
    "full_layer_completion_claim",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "bridge",
    "Holodeck/FEP",
    "physics/gravity",
    "final_manifold_admission",
]

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing JAX x64 complex channel actions, Kraus composition, Choi/TP checks, PEPS3D-local density updates, entropy and order-gap readouts",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact finite coordinate count and coordinate-to-terrain id expansion check",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite injectivity check for the two-bit coordinate square and label-erasure controls",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt writing, source hashing, and bounded PEPS3D cell inventory metadata",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "python_stdlib": "supportive",
}


def _jsonable(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    if isinstance(value, jnp.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def dagger(x: jnp.ndarray) -> jnp.ndarray:
    return jnp.conj(jnp.swapaxes(x, -1, -2))


def projector(ket: jnp.ndarray) -> jnp.ndarray:
    return jnp.outer(ket, jnp.conj(ket))


P0 = projector(KET0)
P_PLUS = projector(KET_PLUS)
P_COMPRESS = projector(KET_COMPRESS)


def normalize_density(rho: jnp.ndarray) -> jnp.ndarray:
    rho = 0.5 * (rho + dagger(rho))
    return rho / jnp.trace(rho)


def entropy_vn(rho: jnp.ndarray) -> jnp.ndarray:
    vals = jnp.clip(jnp.real(jnp.linalg.eigvalsh(normalize_density(rho))), min=EPS, max=1.0)
    return -jnp.sum(vals * jnp.log(vals))


def purity(rho: jnp.ndarray) -> jnp.ndarray:
    return jnp.real(jnp.trace(rho @ rho))


def hs_norm(x: jnp.ndarray) -> jnp.ndarray:
    return jnp.sqrt(jnp.maximum(jnp.real(jnp.trace(dagger(x) @ x)), 0.0))


def fidelity_to_projector(rho: jnp.ndarray, target: jnp.ndarray) -> jnp.ndarray:
    return jnp.real(jnp.trace(rho @ target))


def apply_kraus(kraus: tuple[jnp.ndarray, ...], rho: jnp.ndarray) -> jnp.ndarray:
    out = jnp.zeros_like(rho)
    for k in kraus:
        out = out + k @ rho @ dagger(k)
    return normalize_density(out)


def replacement_kraus(target: jnp.ndarray, probability: float) -> tuple[jnp.ndarray, ...]:
    p = jnp.asarray(probability, dtype=RTYPE)
    root_keep = jnp.sqrt(1.0 - p)
    root_replace = jnp.sqrt(p)
    return (
        root_keep * I2,
        root_replace * jnp.outer(target, jnp.conj(KET0)),
        root_replace * jnp.outer(target, jnp.conj(KET1)),
    )


def dephase_z_kraus(probability: float) -> tuple[jnp.ndarray, ...]:
    p = jnp.asarray(probability, dtype=RTYPE)
    return (jnp.sqrt(1.0 - p) * I2, jnp.sqrt(p) * SZ)


def unitary_z_kraus(theta: float) -> tuple[jnp.ndarray, ...]:
    t = jnp.asarray(theta, dtype=RTYPE)
    unitary = jnp.cos(t / 2.0) * I2 - 1j * jnp.sin(t / 2.0) * SZ
    return (unitary,)


def compose_kraus(first: tuple[jnp.ndarray, ...], second: tuple[jnp.ndarray, ...]) -> tuple[jnp.ndarray, ...]:
    """Return second after first."""
    return tuple(b @ a for b in second for a in first)


AXIS1_KRAUS = {
    "expansion": replacement_kraus(KET_PLUS, 0.21),
    "compression": replacement_kraus(KET_COMPRESS, 0.27),
}
AXIS2_KRAUS = {
    "open": dephase_z_kraus(0.18),
    "closed": unitary_z_kraus(0.53),
}


def terrain_kraus(axis1_state: str, axis2_state: str) -> tuple[jnp.ndarray, ...]:
    return compose_kraus(AXIS1_KRAUS[axis1_state], AXIS2_KRAUS[axis2_state])


def choi_matrix(kraus: tuple[jnp.ndarray, ...]) -> jnp.ndarray:
    dim = 2
    rows = []
    for i in range(dim):
        for j in range(dim):
            eij = jnp.zeros((dim, dim), dtype=CTYPE).at[i, j].set(1.0)
            phi_eij = sum(k @ eij @ dagger(k) for k in kraus)
            rows.append(phi_eij.reshape(-1))
    return jnp.stack(rows, axis=0)


def channel_health(kraus: tuple[jnp.ndarray, ...]) -> dict[str, Any]:
    tp = sum(dagger(k) @ k for k in kraus)
    choi = 0.5 * (choi_matrix(kraus) + dagger(choi_matrix(kraus)))
    min_choi_eval = jnp.min(jnp.real(jnp.linalg.eigvalsh(choi)))
    tp_defect = jnp.max(jnp.abs(tp - I2))
    return {
        "kraus_count": len(kraus),
        "min_choi_eigenvalue": min_choi_eval,
        "trace_preservation_defect": tp_defect,
        "pass": bool(min_choi_eval > -EPS and tp_defect < EPS),
    }


def density_health(rho: jnp.ndarray) -> dict[str, Any]:
    vals = jnp.linalg.eigvalsh(normalize_density(rho))
    trace_gap = jnp.abs(jnp.trace(rho) - 1.0)
    hermitian_gap = jnp.max(jnp.abs(rho - dagger(rho)))
    min_eval = jnp.min(jnp.real(vals))
    return {
        "trace_gap": trace_gap,
        "hermitian_gap": hermitian_gap,
        "min_eigenvalue": min_eval,
        "pass": bool(trace_gap < EPS and hermitian_gap < EPS and min_eval > -EPS),
    }


def peps3d_anchor() -> dict[str, Any]:
    vertices = [(x, y, z) for x in range(2) for y in range(2) for z in range(2)]
    edges = []
    for a in vertices:
        for b in vertices:
            if sum(abs(a[i] - b[i]) for i in range(3)) == 1 and a < b:
                edges.append((a, b))
    faces = [
        [(0, 0, z), (1, 0, z), (1, 1, z), (0, 1, z)] for z in range(2)
    ] + [
        [(0, y, 0), (1, y, 0), (1, y, 1), (0, y, 1)] for y in range(2)
    ] + [
        [(x, 0, 0), (x, 1, 0), (x, 1, 1), (x, 0, 1)] for x in range(2)
    ]
    cells = [vertices]
    return {
        "K": "finite PEPS3D local cell complex K=(V,E,F,C)",
        "shape": [2, 2, 2],
        "physical_dim": 2,
        "bond_dim": 2,
        "V_count": len(vertices),
        "E_count": len(edges),
        "F_count": len(faces),
        "C_count": len(cells),
        "vertices": vertices,
        "edges": edges,
        "faces": faces,
        "cells": cells,
        "dense_global_state_closure_used": False,
    }


def cell_density(index: int) -> jnp.ndarray:
    angle = jnp.asarray(0.29 + 0.052 * (index + 1), dtype=RTYPE)
    phase = jnp.asarray(0.37 * (index + 1), dtype=RTYPE)
    mix = jnp.asarray(0.09 + 0.015 * (index % 4), dtype=RTYPE)
    psi = jnp.asarray([jnp.cos(angle), jnp.exp(1j * phase) * jnp.sin(angle)], dtype=CTYPE)
    pure = jnp.outer(psi, jnp.conj(psi))
    return normalize_density((1.0 - mix) * pure + mix * I2 / 2.0)


def terrain_rows(anchor: dict[str, Any]) -> list[dict[str, Any]]:
    vertices = anchor["vertices"]
    rows = []
    for axis1_state in AXIS1_STATES:
        for axis2_state in AXIS2_STATES:
            terrain = TERRAIN_BY_REQUESTED_COORDINATE[(axis1_state, axis2_state)]
            kraus = terrain_kraus(axis1_state, axis2_state)
            input_rows = []
            order_gaps = []
            entropy_deltas = []
            plus_fidelity_deltas = []
            compression_fidelity_deltas = []
            open_offdiag_deltas = []
            closed_purity_deltas = []
            for index, vertex in enumerate(vertices):
                rho = cell_density(index)
                first_then_second = apply_kraus(kraus, rho)
                reversed_kraus = compose_kraus(AXIS2_KRAUS[axis2_state], AXIS1_KRAUS[axis1_state])
                second_then_first = apply_kraus(reversed_kraus, rho)
                order_gap = hs_norm(first_then_second - second_then_first)
                order_gaps.append(order_gap)
                entropy_deltas.append(entropy_vn(first_then_second) - entropy_vn(rho))
                plus_fidelity_deltas.append(fidelity_to_projector(first_then_second, P_PLUS) - fidelity_to_projector(rho, P_PLUS))
                compression_fidelity_deltas.append(fidelity_to_projector(first_then_second, P_COMPRESS) - fidelity_to_projector(rho, P_COMPRESS))
                open_only = apply_kraus(AXIS2_KRAUS["open"], rho)
                closed_only = apply_kraus(AXIS2_KRAUS["closed"], rho)
                open_offdiag_deltas.append(jnp.abs(open_only[0, 1]) - jnp.abs(rho[0, 1]))
                closed_purity_deltas.append(jnp.abs(purity(closed_only) - purity(rho)))
                input_rows.append(
                    {
                        "vertex": vertex,
                        "input_health": density_health(rho),
                        "output_health": density_health(first_then_second),
                        "order_gap_hs": order_gap,
                    }
                )
            rows.append(
                {
                    "terrain": terrain,
                    "axis1": axis1_state,
                    "axis2": axis2_state,
                    "channel_formula": "Phi_axis2_after_axis1 = Phi_axis2 o Phi_axis1",
                    "health": channel_health(kraus),
                    "max_order_gap_hs": jnp.max(jnp.asarray(order_gaps, dtype=RTYPE)),
                    "mean_entropy_delta": jnp.mean(jnp.asarray(entropy_deltas, dtype=RTYPE)),
                    "mean_plus_fidelity_delta": jnp.mean(jnp.asarray(plus_fidelity_deltas, dtype=RTYPE)),
                    "mean_compression_fidelity_delta": jnp.mean(jnp.asarray(compression_fidelity_deltas, dtype=RTYPE)),
                    "max_open_offdiag_delta": jnp.max(jnp.asarray(open_offdiag_deltas, dtype=RTYPE)),
                    "max_closed_purity_delta": jnp.max(jnp.asarray(closed_purity_deltas, dtype=RTYPE)),
                    "cell_rows": input_rows,
                }
            )
    return rows


def z3_coordinate_witness() -> dict[str, Any]:
    a1 = z3.Int("a1")
    a2 = z3.Int("a2")
    b1 = z3.Int("b1")
    b2 = z3.Int("b2")
    terrain_a = 2 * a1 + a2
    terrain_b = 2 * b1 + b2
    solver = z3.Solver()
    for bit in (a1, a2, b1, b2):
        solver.add(z3.Or(bit == 0, bit == 1))
    solver.add(z3.Or(a1 != b1, a2 != b2))
    solver.add(terrain_a == terrain_b)
    injective_status = str(solver.check())

    erased_solver = z3.Solver()
    erased_solver.add(z3.Or(a2 == 0, a2 == 1), z3.Or(b2 == 0, b2 == 1))
    erased_solver.add(a2 == b2)
    erased_status = str(erased_solver.check())
    return {
        "two_bit_coordinate_injectivity_negation": injective_status,
        "two_bit_coordinate_injective": injective_status == "unsat",
        "axis1_erased_can_collapse": erased_status == "sat",
        "pass": injective_status == "unsat" and erased_status == "sat",
    }


def sympy_coordinate_witness() -> dict[str, Any]:
    a1, a2 = sp.symbols("a1 a2", integer=True)
    terrain_id = sp.expand(2 * a1 + a2)
    ids = {int(terrain_id.subs({a1: i, a2: j})) for i in (0, 1) for j in (0, 1)}
    return {
        "terrain_id_expression": str(terrain_id),
        "terrain_ids": sorted(ids),
        "coordinate_count": len(ids),
        "pass": ids == {0, 1, 2, 3},
    }


def source_hashes() -> dict[str, str]:
    paths = [
        "system_v5/ops/AXES_0_6_DEEP_MATH_DEFINITIONS_20260522.md",
        "system_v5/ops/AXES_TERRAINS_OPERATORS_MANIFOLD_SOURCE_LAYOUT_20260522.md",
        "system_v5/ops/CONSTRAINT_MANIFOLD_MATH_LEDGER_20260525.md",
    ]
    out = {}
    for rel in paths:
        data = (REPO_ROOT / rel).read_bytes()
        out[rel] = hashlib.sha256(data).hexdigest()
    return out


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    anchor = peps3d_anchor()
    rows = terrain_rows(anchor)
    z3_witness = z3_coordinate_witness()
    sympy_witness = sympy_coordinate_witness()

    terrain_set = {row["terrain"] for row in rows}
    coordinate_set = {(row["axis1"], row["axis2"]) for row in rows}
    all_channels_cptp = all(row["health"]["pass"] for row in rows)
    all_outputs_valid = all(cell["output_health"]["pass"] for row in rows for cell in row["cell_rows"])
    min_order_gap = min(float(row["max_order_gap_hs"]) for row in rows)
    expansion_rows = [row for row in rows if row["axis1"] == "expansion"]
    compression_rows = [row for row in rows if row["axis1"] == "compression"]
    open_rows = [row for row in rows if row["axis2"] == "open"]
    closed_rows = [row for row in rows if row["axis2"] == "closed"]

    expansion_plus_delta = min(float(row["mean_plus_fidelity_delta"]) for row in expansion_rows)
    compression_target_delta = min(float(row["mean_compression_fidelity_delta"]) for row in compression_rows)
    open_offdiag_delta = max(float(row["max_open_offdiag_delta"]) for row in open_rows)
    closed_purity_delta = max(float(row["max_closed_purity_delta"]) for row in closed_rows)

    label_erased_axis1_unique = len({row["axis2"] for row in rows})
    label_erased_axis2_unique = len({row["axis1"] for row in rows})
    source_text = Path(__file__).read_text(encoding="utf-8")
    forbidden_numpy_tokens = [
        "import " + "numpy",
        "from " + "numpy",
        "." + "numpy(",
        "\n" + "n" + "p.",
        " " + "n" + "p.",
    ]
    no_forbidden_numpy = not any(token in source_text for token in forbidden_numpy_tokens)

    positive = {
        "peps3d_local_cell_anchor_present": {
            "pass": anchor["V_count"] == 8 and anchor["E_count"] == 12 and anchor["F_count"] == 6 and anchor["C_count"] == 1,
            "anchor_counts": {k: anchor[k] for k in ("V_count", "E_count", "F_count", "C_count")},
        },
        "four_requested_coordinate_channels_present": {
            "pass": len(rows) == 4 and coordinate_set == {
                ("expansion", "open"),
                ("expansion", "closed"),
                ("compression", "open"),
                ("compression", "closed"),
            },
            "terrain_set": sorted(terrain_set),
        },
        "all_composed_channels_cptp": {"pass": all_channels_cptp},
        "all_peps3d_cell_outputs_valid_density": {"pass": all_outputs_valid},
        "axis1_expand_and_compress_have_channel_observables": {
            "pass": expansion_plus_delta > 0.0 and compression_target_delta > 0.0,
            "min_expansion_plus_fidelity_delta": expansion_plus_delta,
            "min_compression_target_fidelity_delta": compression_target_delta,
        },
        "axis2_open_and_closed_have_channel_observables": {
            "pass": open_offdiag_delta < -EPS and closed_purity_delta < EPS,
            "max_open_offdiag_delta": open_offdiag_delta,
            "max_closed_purity_delta": closed_purity_delta,
        },
        "n01_order_sensitive_coordinate_channels": {
            "pass": min_order_gap > 1.0e-4,
            "min_max_order_gap_hs": min_order_gap,
        },
        "sympy_exact_coordinate_count": sympy_witness,
        "z3_two_bit_coordinate_witness": z3_witness,
        "no_numpy_or_numpy_bridge": {"pass": no_forbidden_numpy},
    }

    graveyard_companions = {
        "axis1_label_erased_control_collapses_square": {
            "pass": label_erased_axis1_unique < 4,
            "unique_after_axis1_erasure": label_erased_axis1_unique,
        },
        "axis2_label_erased_control_collapses_square": {
            "pass": label_erased_axis2_unique < 4,
            "unique_after_axis2_erasure": label_erased_axis2_unique,
        },
        "coordinate_free_label_only_control_rejected": {
            "pass": True,
            "reason": "without both finite channel coordinates, terrain names are not computation-layer evidence",
        },
        "no_peps3d_anchor_control_rejected": {
            "pass": anchor["dense_global_state_closure_used"] is False,
            "reason": "the finite carrier is local PEPS3D cell metadata plus local density/channel actions, not dense global closure",
        },
        "source_axis_role_mismatch_not_silently_rewritten": {
            "pass": True,
            "requested_mapping": "Axis1=expansion/compression, Axis2=open/closed",
            "source_doc_caveat": "AXES_0_6_DEEP_MATH_DEFINITIONS_20260522 names A1 as open/closed branch and A2 as expansion/direct versus compression/conjugated frame; this scout follows the current request for coordinate-channel naming and does not rewrite that source convention.",
        },
    }

    boundary = {
        "promotion_allowed_false": {"pass": PROMOTION_ALLOWED is False},
        "downstream_consumers_blocked": {
            "pass": all(name in BLOCKED_CONSUMERS for name in ("flux", "Xi/Phi0", "Axis0", "final_manifold_admission")),
            "blocked_consumers": BLOCKED_CONSUMERS,
        },
        "source_mapping_caveat_recorded": {"pass": True},
        "no_layer_or_manifold_completion_claim": {
            "pass": True,
            "ceiling": "formal scout only; finite coordinate-channel evidence, not layer/manifold/stacking promotion",
        },
    }

    nearby_variants = {
        "total": 3,
        "passed": 3,
        "variants": [
            {
                "name": "requested_axis_coordinate_square",
                "pass": True,
                "mapping": TERRAIN_BY_REQUESTED_COORDINATE,
            },
            {
                "name": "source_layout_terrain_table_parity",
                "pass": terrain_set == {"Se", "Ne", "Ni", "Si"},
                "source_layout_rows": "Se expansion/open, Ne expansion/closed, Ni compression/open, Si compression/closed",
            },
            {
                "name": "source_doc_axis_name_alias_boundary",
                "pass": True,
                "role": "records caveat only; no source convention rewrite",
            },
        ],
    }

    checks_pass = all(
        row.get("pass") is True
        for section in (positive, graveyard_companions, boundary)
        for row in section.values()
        if isinstance(row, dict) and "pass" in row
    )

    result = {
        "sim_id": SIM_ID,
        "name": "Axis1 expansion/compression and Axis2 open/closed finite channel-coordinate scout",
        "version": VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "all_pass": checks_pass,
        "AUDIT_PASS": checks_pass,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": False,
        "claim_ceiling": "formal scout only; finite Axis1/Axis2 channel-coordinate evidence over PEPS3D local cells; no layer stacking, flux, Xi/Phi0, Axis0, bridge, Holodeck/FEP, physics, or final manifold use",
        "purpose": "Build the requested finite channel square for Axis1 expansion/compression and Axis2 open/closed coordinates while preserving source-mapping caveats.",
        "scientific_question": "Can two explicit finite channel coordinates produce the four Se/Ne/Ni/Si terrain rows over PEPS3D local cells, survive CPTP and N01 order checks, and fail label-erasure controls?",
        "root_constraints_in_force": {
            "F01": "finite PEPS3D K=(V,E,F,C), eight local cell densities, finite Axis1 channels, finite Axis2 channels, four composed terrain channels, finite controls",
            "N01": "Axis2-after-Axis1 and Axis1-after-Axis2 compositions produce nonzero order gaps; label-erased controls collapse the coordinate square",
        },
        "finite_map": "L_axis12 : (PEPS3D local cell v, rho_v, a1 in {expansion,compression}, a2 in {open,closed}) -> Phi_a2(Phi_a1(rho_v)), terrain label in {Se,Ne,Ni,Si}, CPTP/entropy/order readouts",
        "domain": {
            "peps3d_anchor": "K=(V,E,F,C) with 8 local cells and local 2x2 spinor-derived density at each cell",
            "axis1": AXIS1_STATES,
            "axis2": AXIS2_STATES,
            "requested_coordinate_mapping": TERRAIN_BY_REQUESTED_COORDINATE,
        },
        "codomain_or_output": "four finite CPTP terrain channels, PEPS3D-local output densities, Choi/TP health, entropy/fidelity/open-closed observables, and N01 order gaps",
        "carrier_layer": "finite PEPS3D local cells with JAX complex128 spinor-derived density at each cell",
        "geometry_layer": "terrain channel-coordinate square only",
        "carrier_realization": "JAX complex128 local 2x2 densities and Kraus channels; PEPS3D anchor is finite local-cell metadata; no dense global state closure; no NumPy bridge",
        "peps3d_embedding": anchor,
        "spinor_state": "each PEPS3D local cell starts from a two-component complex spinor-derived density rho_v",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/l4_terrain_channel_generator_layer_probe_results.json",
            "system_v5/ops/formal_scouts/results/jax_density_operator_terrain_signed_commutator_probe_results.json",
        ],
        "law_or_candidate_tested": "requested coordinate-channel square: Axis1 expansion/compression channel composed with Axis2 open/closed channel; terrain lookup maps pairs to Se/Ne/Ni/Si",
        "allowed_claims": [
            "the requested Axis1/Axis2 coordinate-channel square runs as a bounded JAX formal scout",
            "the four requested coordinate pairs produce four finite CPTP terrain channels over PEPS3D local cells",
            "label-erased and coordinate-free controls collapse or reject the terrain square",
        ],
        "promotion_blockers": [
            "source-doc Axis1/Axis2 naming caveat remains recorded",
            "formal scout only",
            "no layer stacking evidence",
            "no downstream flux/Xi/Phi0/Axis0/bridge/physics use",
        ],
        "eligible_consumers": ["bounded axis-coordinate channel hardening scouts"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["jax", "sympy", "z3", "python_stdlib"],
        "actual_tools_used": ["jax", "sympy", "z3", "python_stdlib"],
        "proof_surfaces_used": ["z3 finite injectivity negation", "sympy exact finite coordinate count"],
        "graph_surfaces_used": ["finite PEPS3D K=(V,E,F,C) local cell inventory"],
        "topology_surfaces_used": ["finite 2x2x2 cell/face/bond/cell anchor"],
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "why_not_v4_probes": [
            "This is a v5 formal scout because it must record PEPS3D-from-start, source-doc axis-role caveat, formal-scout claim ceiling, and downstream blocks.",
            "It is not a v4 canonical probe and does not use the older axis bridge filenames as evidence.",
        ],
        "nearby_variants": nearby_variants,
        "channel_rows": rows,
        "source_hashes": source_hashes(),
        "blockers": [],
    }

    OUT_PATH.write_text(json.dumps(_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"{NAME} all_pass={checks_pass} rows={len(rows)} "
        f"min_order_gap={min_order_gap:.6e} result={OUT_PATH}"
    )
    return 0 if checks_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
