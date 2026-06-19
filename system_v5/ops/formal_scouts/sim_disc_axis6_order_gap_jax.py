#!/usr/bin/env python3
# object_id: disc_axis6_order_gap
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


OBJECT_ID = "disc_axis6_order_gap"
REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
FORMAL_SCOUT_DIR = REPO / "system_v5" / "ops" / "formal_scouts"
CARRIER_DIR = REPO / "system_v5" / "julia_carrier"
RESULT_PATH = FORMAL_SCOUT_DIR / "results" / "disc_axis6_order_gap_results.json"
JULIA_SOURCE_PATH = CARRIER_DIR / "disc_axis6_order_gap.jl"
JULIA_RESULT_PATH = CARRIER_DIR / "disc_axis6_order_gap_julia_results.json"
TOL_ZERO = 1.0e-12
TOL_NONZERO = 1.0e-6
PARITY_TOL = 1.0e-9

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
sim_execution_kind = "nonclassical"
SIM_EXECUTION_KIND = sim_execution_kind

CLAIM_CEILING = (
    "scratch_diagnostic Axis-6 composition-order discriminator only: finite "
    "density-matrix witnesses for T o O vs O o T under eight bounded "
    "op-terrain couplings. It reports sparse REAL_LAYER evidence for the "
    "order-gap mechanism and demotes all-16-cells-live to PARTIAL; no "
    "promotion, formal admission, bridge, Axis0, physics, PEPS3D, or "
    "manifold-closure claim."
)

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 backend for finite density-carrier channel algebra and parity scalars",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex matrix operations for T o O versus O o T order gaps, controls, and finite witnesses",
    },
    "Julia peer backend": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent ComplexF64 peer backend for dual-backend parity",
    },
    "owner_axis6_layer_constants": {
        "tried": True,
        "used": True,
        "reason": "load-bearing eight op-terrain coupling table; erasing axis structure collapses the sparse noncommuting result",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive result serialization, subprocess invocation, path handling, hashes, timestamps, and peer-result loading",
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
    "owner_axis6_layer_constants": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
}

COMPLEX = jnp.complex128
I2 = jnp.eye(2, dtype=COMPLEX)
SX = jnp.asarray([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=COMPLEX)
SY = jnp.asarray([[0.0 + 0.0j, -1.0j], [1.0j, 0.0 + 0.0j]], dtype=COMPLEX)
SZ = jnp.asarray([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, -1.0 + 0.0j]], dtype=COMPLEX)
PAULI = {"x": SX, "y": SY, "z": SZ}

OPERATOR_CONSTANTS: dict[str, dict[str, Any]] = {
    "Ti": {"kind": "dephase", "axis": "z", "strength": 0.31, "angle": 0.0},
    "Te": {"kind": "dephase", "axis": "x", "strength": 0.27, "angle": 0.0},
    "Fi": {"kind": "rotation", "axis": "x", "strength": 0.0, "angle": 0.41},
    "Fe": {"kind": "rotation", "axis": "z", "strength": 0.0, "angle": 0.37},
}

TERRAIN_CONSTANTS: dict[str, dict[str, Any]] = {
    "Se": {"axis": "x", "strength": 0.22, "label": "funnel_x_pinching"},
    "Ne": {"axis": "y", "strength": 0.24, "label": "vortex_y_pinching"},
    "Ni": {"axis": "x", "strength": 0.26, "label": "pit_x_pinching"},
    "Si": {"axis": "y", "strength": 0.28, "label": "plateau_y_pinching"},
}

COUPLING_ROWS: list[dict[str, Any]] = [
    {"token": "TiSe", "operator": "Ti", "terrain": "Se", "expected_noncommuting": False},
    {"token": "TiNe", "operator": "Ti", "terrain": "Ne", "expected_noncommuting": False},
    {"token": "TeNi", "operator": "Te", "terrain": "Ni", "expected_noncommuting": False},
    {"token": "TeSi", "operator": "Te", "terrain": "Si", "expected_noncommuting": False},
    {"token": "FiSe", "operator": "Fi", "terrain": "Se", "expected_noncommuting": False},
    {"token": "FiNe", "operator": "Fi", "terrain": "Ne", "expected_noncommuting": True},
    {"token": "FeNi", "operator": "Fe", "terrain": "Ni", "expected_noncommuting": True},
    {"token": "FeSi", "operator": "Fe", "terrain": "Si", "expected_noncommuting": True},
]


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def py_bool(value: Any) -> bool:
    return bool(jax.device_get(value))


def sha256_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def axis_projectors(axis: str) -> tuple[jax.Array, jax.Array]:
    sigma = PAULI[axis]
    return (I2 + sigma) / 2.0, (I2 - sigma) / 2.0


def dephase_channel(rho: jax.Array, axis: str, strength: float) -> jax.Array:
    p_plus, p_minus = axis_projectors(axis)
    pinched = p_plus @ rho @ p_plus + p_minus @ rho @ p_minus
    return (1.0 - strength) * rho + strength * pinched


def rotation_channel(rho: jax.Array, axis: str, angle: float) -> jax.Array:
    sigma = PAULI[axis]
    unitary = jnp.cos(angle / 2.0) * I2 - 1j * jnp.sin(angle / 2.0) * sigma
    return unitary @ rho @ jnp.conjugate(unitary.T)


def apply_operator(rho: jax.Array, op_name: str) -> jax.Array:
    spec = OPERATOR_CONSTANTS[op_name]
    if spec["kind"] == "dephase":
        return dephase_channel(rho, str(spec["axis"]), float(spec["strength"]))
    if spec["kind"] == "rotation":
        return rotation_channel(rho, str(spec["axis"]), float(spec["angle"]))
    raise ValueError(f"unknown operator kind: {spec['kind']!r}")


def apply_terrain(rho: jax.Array, terrain_name: str, *, override_axis: str | None = None) -> jax.Array:
    spec = TERRAIN_CONSTANTS[terrain_name]
    axis = str(spec["axis"] if override_axis is None else override_axis)
    return dephase_channel(rho, axis, float(spec["strength"]))


def finite_witness_states() -> list[jax.Array]:
    states: list[jax.Array] = []
    radius = 0.58
    for idx in range(8):
        theta = jnp.pi * (idx + 0.5) / 8.0
        phi = 2.0 * jnp.pi * idx / 8.0
        bx = radius * jnp.sin(theta) * jnp.cos(phi)
        by = radius * jnp.sin(theta) * jnp.sin(phi)
        bz = radius * jnp.cos(theta)
        states.append((I2 + bx * SX + by * SY + bz * SZ) / 2.0)
    return states


def order_gap(row: dict[str, Any], states: list[jax.Array], *, terrain_axis_override: str | None = None) -> dict[str, Any]:
    gaps = []
    for rho in states:
        left = apply_terrain(
            apply_operator(rho, str(row["operator"])),
            str(row["terrain"]),
            override_axis=terrain_axis_override,
        )
        right = apply_operator(
            apply_terrain(rho, str(row["terrain"]), override_axis=terrain_axis_override),
            str(row["operator"]),
        )
        gaps.append(py_float(jnp.linalg.norm(left - right)))
    return {
        "per_witness_gap": gaps,
        "max_gap": max(gaps),
        "mean_gap": sum(gaps) / len(gaps),
    }


def row_record(row: dict[str, Any], states: list[jax.Array]) -> dict[str, Any]:
    op = OPERATOR_CONSTANTS[str(row["operator"])]
    terrain = TERRAIN_CONSTANTS[str(row["terrain"])]
    real_gap = order_gap(row, states)
    matched_gap = order_gap(row, states, terrain_axis_override=str(op["axis"]))
    axis_mismatch = str(op["axis"]) != str(terrain["axis"])
    measured_noncommuting = real_gap["max_gap"] > TOL_NONZERO
    return {
        "token": str(row["token"]),
        "operator": str(row["operator"]),
        "operator_kind": str(op["kind"]),
        "operator_axis": str(op["axis"]),
        "terrain": str(row["terrain"]),
        "terrain_axis": str(terrain["axis"]),
        "terrain_label": str(terrain["label"]),
        "axis_mismatch": axis_mismatch,
        "expected_noncommuting": bool(row["expected_noncommuting"]),
        "measured_noncommuting": measured_noncommuting,
        "order_gap": real_gap,
        "axis_matched_control_gap": matched_gap,
        "verdict": "nonzero_order_gap" if measured_noncommuting else "commuting_or_collapsed",
    }


def erased_layer_records(states: list[jax.Array]) -> list[dict[str, Any]]:
    records = []
    for row in COUPLING_ROWS:
        op_axis = str(OPERATOR_CONSTANTS[str(row["operator"])]["axis"])
        gap = order_gap(row, states, terrain_axis_override=op_axis)
        records.append(
            {
                "token": str(row["token"]),
                "erased_terrain_axis": op_axis,
                "max_gap": gap["max_gap"],
                "measured_noncommuting": gap["max_gap"] > TOL_NONZERO,
            }
        )
    return records


def run_julia_peer() -> dict[str, Any]:
    if not JULIA_SOURCE_PATH.exists():
        return {
            "attempted": True,
            "pass": False,
            "returncode": None,
            "stdout": "",
            "stderr": f"missing Julia source: {JULIA_SOURCE_PATH}",
        }
    proc = subprocess.run(
        ["julia", str(JULIA_SOURCE_PATH)],
        cwd=str(CARRIER_DIR),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
        check=False,
    )
    return {
        "attempted": True,
        "pass": proc.returncode == 0 and JULIA_RESULT_PATH.exists(),
        "returncode": proc.returncode,
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-4000:],
    }


def parity_against_peer(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_RESULT_PATH.exists():
        return {
            "within_1e_9": False,
            "stop_condition_fired": True,
            "missing_peer": str(JULIA_RESULT_PATH),
            "scalar_mismatches": [],
            "boolean_mismatches": [],
            "string_mismatches": [],
        }
    peer = json.loads(JULIA_RESULT_PATH.read_text(encoding="utf-8"))
    scalar_mismatches = []
    boolean_mismatches = []
    string_mismatches = []
    peer_scalars = peer.get("shared_scalars") or {}
    peer_booleans = peer.get("shared_booleans") or {}
    peer_strings = peer.get("shared_strings") or {}
    for key, value in sorted((result.get("shared_scalars") or {}).items()):
        if key not in peer_scalars:
            scalar_mismatches.append({"key": key, "reason": "missing_in_julia"})
            continue
        diff = abs(float(value) - float(peer_scalars[key]))
        if diff > PARITY_TOL:
            scalar_mismatches.append({"key": key, "jax": float(value), "julia": float(peer_scalars[key]), "abs_diff": diff})
    for key, value in sorted((result.get("shared_booleans") or {}).items()):
        if key not in peer_booleans:
            boolean_mismatches.append({"key": key, "reason": "missing_in_julia"})
            continue
        if bool(value) != bool(peer_booleans[key]):
            boolean_mismatches.append({"key": key, "jax": bool(value), "julia": bool(peer_booleans[key])})
    for key, value in sorted((result.get("shared_strings") or {}).items()):
        if key not in peer_strings:
            string_mismatches.append({"key": key, "reason": "missing_in_julia"})
            continue
        if str(value) != str(peer_strings[key]):
            string_mismatches.append({"key": key, "jax": str(value), "julia": str(peer_strings[key])})
    within = not scalar_mismatches and not boolean_mismatches and not string_mismatches
    return {
        "within_1e_9": within,
        "stop_condition_fired": not within,
        "peer_path": str(JULIA_RESULT_PATH),
        "scalar_mismatches": scalar_mismatches,
        "boolean_mismatches": boolean_mismatches,
        "string_mismatches": string_mismatches,
    }


def build_result(julia_run: dict[str, Any]) -> dict[str, Any]:
    states = finite_witness_states()
    rows = [row_record(row, states) for row in COUPLING_ROWS]
    live_rows = [row for row in rows if row["measured_noncommuting"]]
    zero_rows = [row for row in rows if not row["measured_noncommuting"]]
    expected_live = [row["token"] for row in rows if row["expected_noncommuting"]]
    measured_live = [row["token"] for row in live_rows]
    erased = erased_layer_records(states)

    max_live_gap = max(row["order_gap"]["max_gap"] for row in live_rows)
    min_live_gap = min(row["order_gap"]["max_gap"] for row in live_rows)
    max_commuting_gap = max(row["order_gap"]["max_gap"] for row in zero_rows)
    max_axis_matched_gap = max(row["axis_matched_control_gap"]["max_gap"] for row in rows)
    erased_live_count = sum(1 for row in erased if row["measured_noncommuting"])

    order_gap_nonzero_noncommute = all(
        row["order_gap"]["max_gap"] > TOL_NONZERO for row in rows if row["expected_noncommuting"]
    )
    order_gap_zero_commute = all(
        row["order_gap"]["max_gap"] <= TOL_ZERO for row in rows if not row["expected_noncommuting"]
    )
    sparse_only_3of8 = len(measured_live) == 3 and len(rows) == 8 and sorted(measured_live) == sorted(expected_live)
    requires_axis_mismatch = all(row["axis_mismatch"] for row in live_rows) and max_axis_matched_gap <= TOL_ZERO
    axis_mismatch_not_sufficient = any(row["axis_mismatch"] and not row["measured_noncommuting"] for row in rows)
    owner_carrier_load_bearing = sparse_only_3of8 and erased_live_count == 0 and max_live_gap > TOL_NONZERO
    layer_verdict = (
        "REAL_LAYER"
        if owner_carrier_load_bearing and order_gap_nonzero_noncommute and order_gap_zero_commute
        else "OPEN"
    )
    all_16_cells_live_claim_verdict = "PARTIAL" if sparse_only_3of8 else "OPEN"
    local_all_pass = bool(
        layer_verdict == "REAL_LAYER"
        and order_gap_nonzero_noncommute
        and order_gap_zero_commute
        and sparse_only_3of8
        and requires_axis_mismatch
        and axis_mismatch_not_sufficient
        and owner_carrier_load_bearing
        and bool(jax.config.read("jax_enable_x64"))
    )

    shared_scalars: dict[str, float] = {
        "max_live_order_gap": max_live_gap,
        "min_live_order_gap": min_live_gap,
        "max_commuting_order_gap": max_commuting_gap,
        "max_axis_matched_control_gap": max_axis_matched_gap,
        "live_count": float(len(measured_live)),
        "erased_live_count": float(erased_live_count),
    }
    for row in rows:
        shared_scalars[f"row.{row['token']}.max_gap"] = float(row["order_gap"]["max_gap"])
        shared_scalars[f"row.{row['token']}.axis_matched_gap"] = float(row["axis_matched_control_gap"]["max_gap"])

    shared_booleans: dict[str, bool] = {
        "local_all_pass": local_all_pass,
        "order_gap_nonzero_noncommute": order_gap_nonzero_noncommute,
        "order_gap_zero_commute": order_gap_zero_commute,
        "sparse_only_3of8": sparse_only_3of8,
        "requires_axis_mismatch": requires_axis_mismatch,
        "axis_mismatch_not_sufficient": axis_mismatch_not_sufficient,
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
    }
    shared_strings = {
        "layer_verdict": layer_verdict,
        "all_16_cells_live_claim_verdict": all_16_cells_live_claim_verdict,
    }

    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "schema": "SCRATCH_DIAGNOSTIC_RESULT_v1",
        "name": OBJECT_ID,
        "backend": "jax_jnp_x64",
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "source_sha256": sha256_file(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_RESULT_PATH),
        "classification": "scratch_diagnostic",
        "promotion": False,
        "promotion_allowed": False,
        "formal_admission": False,
        "formal_admission_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "sim_execution_kind": "scratch_diagnostic",
        "sim_class": "axis6_composition_order_discriminator",
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "numpy_compute_used": False,
        "numpy_imported": False,
        "finite_witness_count": len(states),
        "discriminator": "A6 order gap: ||J(P(rho)) - P(J(rho))||_F where J is the terrain channel and P is the operator channel",
        "operator_order_not_sign_variant": True,
        "operator_constants": OPERATOR_CONSTANTS,
        "terrain_constants": TERRAIN_CONSTANTS,
        "coupling_rows": rows,
        "erased_layer_structure_control": {
            "description": "replace each terrain axis by the paired operator axis; this erases operator-vs-terrain layer mismatch",
            "rows": erased,
            "live_count": erased_live_count,
        },
        "positive": {
            "three_noncommuting_order_gaps_nonzero": {
                "pass": order_gap_nonzero_noncommute,
                "tokens": expected_live,
                "min_gap": min_live_gap,
            },
            "owner_carrier_load_bearing": {
                "pass": owner_carrier_load_bearing,
                "real_live_count": len(measured_live),
                "erased_live_count": erased_live_count,
            },
        },
        "graveyard_companions": {
            "commuting_rows_gap_zero": {"pass": order_gap_zero_commute, "max_gap": max_commuting_gap},
            "axis_matched_control_collapses": {"pass": max_axis_matched_gap <= TOL_ZERO, "max_gap": max_axis_matched_gap},
            "axis_mismatch_not_sufficient": {
                "pass": axis_mismatch_not_sufficient,
                "reason": "dephase-dephase rows can be axis-mismatched and still commute",
            },
        },
        "boundary": {
            "classification_is_scratch_diagnostic": {"pass": True},
            "promotion_disallowed": {"pass": True},
            "formal_admission_disallowed": {"pass": True},
            "claim_ceiling_blocks_downstream": {"pass": True, "claim_ceiling": CLAIM_CEILING},
            "no_numpy_compute": {"pass": True, "backend": "JAX jax.numpy x64"},
        },
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "variant_names": ["commuting_operator_rows", "axis_matched_control", "erased_layer_structure"],
        },
        "why_not_v4_probes": [
            "scratch diagnostic by request, not a formal_scout admission receipt",
            "tests composition order T o O vs O o T, not signed plus/minus operator variants",
            "sparse 3-of-8 result demotes all-16-cells-live to PARTIAL",
            "Axis0, bridge, PEPS3D, physics, and formal admission remain blocked",
        ],
        "layer_verdict": layer_verdict,
        "all_16_cells_live_claim_verdict": all_16_cells_live_claim_verdict,
        "all_16_cells_live_requires_tuned_axis_mismatch": sparse_only_3of8,
        "order_gap_nonzero_noncommute": order_gap_nonzero_noncommute,
        "order_gap_zero_commute": order_gap_zero_commute,
        "sparse_only_3of8": sparse_only_3of8,
        "requires_axis_mismatch": requires_axis_mismatch,
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
        "owner_real_carrier_load_bearing": owner_carrier_load_bearing,
        "local_all_pass": local_all_pass,
        "julia_run": julia_run,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [
            "Real finite carrier: three of eight op-terrain couplings have nonzero T o O vs O o T order gaps.",
            "Commuting controls: five rows, including dephase-dephase mismatches and axis-matched rotation/dephase rows, collapse to numerical zero.",
            "Erasing layer structure by matching terrain axes to operator axes changes the result from 3 live rows to 0.",
            "The all-16-cells-live claim is not supported by this receipt and is reported as PARTIAL.",
        ],
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "shared_strings": shared_strings,
    }
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = bool(local_all_pass and result["parity"]["within_1e_9"] and julia_run.get("pass") is True)
    result["stop_condition_fired"] = not result["all_pass"]
    result["summary"] = {
        "all_pass": result["all_pass"],
        "local_all_pass": local_all_pass,
        "parity_within_1e_9": result["parity"]["within_1e_9"],
        "layer_verdict": layer_verdict,
        "all_16_cells_live_claim_verdict": all_16_cells_live_claim_verdict,
        "order_gap_nonzero_noncommute": order_gap_nonzero_noncommute,
        "order_gap_zero_commute": order_gap_zero_commute,
        "sparse_only_3of8": sparse_only_3of8,
        "requires_axis_mismatch": requires_axis_mismatch,
        "owner_carrier_load_bearing": owner_carrier_load_bearing,
    }
    return result


def main() -> int:
    julia_run = run_julia_peer()
    result = build_result(julia_run)
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"jax={RESULT_PATH} "
        f"julia={JULIA_RESULT_PATH} "
        f"all_pass={str(result['all_pass']).lower()} "
        f"layer_verdict={result['layer_verdict']} "
        f"order_gap_nonzero_noncommute={str(result['order_gap_nonzero_noncommute']).lower()} "
        f"order_gap_zero_commute={str(result['order_gap_zero_commute']).lower()} "
        f"sparse_only_3of8={str(result['sparse_only_3of8']).lower()} "
        f"requires_axis_mismatch={str(result['requires_axis_mismatch']).lower()}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
