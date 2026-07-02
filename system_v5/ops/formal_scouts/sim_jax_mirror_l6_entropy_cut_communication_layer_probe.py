#!/usr/bin/env python3
"""JAX mirror of the L6 entropy cut/communication finite readout.

This is not a PyTorch sim and does not edit or rerun PyTorch sources. It ports
the existing L6 finite map into JAX x64 and reads the existing PyTorch receipt
only as a comparison surface.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import jax.scipy.linalg as jsp_linalg


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "jax_mirror_l6_entropy_cut_communication_layer_probe"
RESULT_PATH = RESULT_DIR / f"{NAME}_results.json"
PYTORCH_RESULT_PATH = RESULT_DIR / "l6_entropy_cut_communication_layer_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "bridge"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "formal scout only: JAX x64 mirror of the L6 entropy cut/communication "
    "finite readout with read-only comparison to the existing PyTorch receipt; "
    "promotion_allowed=false; layer stacking, Hopf shell closure, flux, "
    "Xi/Phi0, Axis0, FEP, physics/gravity, and final manifold consumers remain "
    "locked."
)

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "supportive JAX x64 mirror of finite cut-edge density/channel/readout calculations",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt and read-only comparison serialization",
    },
    "python_pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical result-path handling",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source hash pinning",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "jax": "supportive",
    "python_json": "supportive",
    "python_pathlib": "supportive",
    "hashlib": "supportive",
}

CTYPE = jnp.complex128
RTYPE = jnp.float64
TOL = 1.0e-10
GAP_FLOOR = 1.0e-6
CUT_AXES = ("x", "y", "z")
SHAPES = ((2, 2, 2), (4, 2, 2), (4, 4, 2), (4, 4, 4))
BLOCKED_CONSUMERS = [
    "layer_stacking",
    "Hopf_shell_closure",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics/gravity",
    "final_manifold",
]

I2 = jnp.eye(2, dtype=CTYPE)
G1 = jnp.asarray([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=CTYPE)
G2 = jnp.asarray([[0.0 + 0.0j, -1j], [1j, 0.0 + 0.0j]], dtype=CTYPE)
G3 = jnp.asarray([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, -1.0 + 0.0j]], dtype=CTYPE)
KETS = (
    jnp.asarray([1.0 + 0.0j, 0.0 + 0.0j], dtype=CTYPE),
    jnp.asarray([0.0 + 0.0j, 1.0 + 0.0j], dtype=CTYPE),
    jnp.asarray([1.0 + 0.0j, 1.0 + 0.0j], dtype=CTYPE) / jnp.sqrt(jnp.asarray(2.0, dtype=RTYPE)),
    jnp.asarray([1.0 + 0.0j, -1.0 + 0.0j], dtype=CTYPE) / jnp.sqrt(jnp.asarray(2.0, dtype=RTYPE)),
)


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if hasattr(value, "shape") and hasattr(value, "tolist"):
        if value.shape == ():
            return jsonable(value.item())
        return jsonable(value.tolist())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def source_sha256() -> str:
    return hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()


def density(psi: jax.Array) -> jax.Array:
    psi = psi / jnp.linalg.norm(psi)
    return jnp.outer(psi, jnp.conj(psi))


def bell_density() -> jax.Array:
    psi = jnp.asarray([1.0, 0.0, 0.0, 1.0], dtype=CTYPE) / jnp.sqrt(jnp.asarray(2.0, dtype=RTYPE))
    return jnp.outer(psi, jnp.conj(psi))


def coords_for_shape(shape: tuple[int, int, int]) -> list[tuple[int, int, int]]:
    nx, ny, nz = shape
    return [(x, y, z) for z in range(nz) for y in range(ny) for x in range(nx)]


def index_map(coords: list[tuple[int, int, int]]) -> dict[tuple[int, int, int], int]:
    return {coord: idx for idx, coord in enumerate(coords)}


def exact_counts(shape: tuple[int, int, int]) -> dict[str, int]:
    nx, ny, nz = shape
    return {
        "V": nx * ny * nz,
        "E": (nx - 1) * ny * nz + nx * (ny - 1) * nz + nx * ny * (nz - 1),
        "F": (nx - 1) * (ny - 1) * nz + (nx - 1) * ny * (nz - 1) + nx * (ny - 1) * (nz - 1),
        "C": (nx - 1) * (ny - 1) * (nz - 1),
    }


def edge_list(shape: tuple[int, int, int]) -> list[tuple[int, int]]:
    coords = coords_for_shape(shape)
    idx = index_map(coords)
    nx, ny, nz = shape
    edges: list[tuple[int, int]] = []
    for x, y, z in coords:
        if x + 1 < nx:
            edges.append((idx[(x, y, z)], idx[(x + 1, y, z)]))
        if y + 1 < ny:
            edges.append((idx[(x, y, z)], idx[(x, y + 1, z)]))
        if z + 1 < nz:
            edges.append((idx[(x, y, z)], idx[(x, y, z + 1)]))
    return edges


def axis_index(axis: str) -> int:
    return CUT_AXES.index(axis)


def coordinate_side(coord: tuple[int, int, int], shape: tuple[int, int, int], axis: str) -> int:
    return int(coord[axis_index(axis)] >= shape[axis_index(axis)] // 2)


def cut_edges(shape: tuple[int, int, int], axis: str) -> list[tuple[int, int]]:
    coords = coords_for_shape(shape)
    rows = []
    for u, v in edge_list(shape):
        if coordinate_side(coords[u], shape, axis) != coordinate_side(coords[v], shape, axis):
            rows.append((u, v))
    return rows


def site_spinors(coords: list[tuple[int, int, int]]) -> list[jax.Array]:
    return [KETS[(x + 2 * y + 3 * z) % len(KETS)] for x, y, z in coords]


def normalize_density(rho: jax.Array) -> jax.Array:
    rho = (rho + jnp.conj(rho.T)) / 2.0
    eigvals, eigvecs = jnp.linalg.eigh(rho)
    eigvals = jnp.clip(jnp.real(eigvals), 0.0, None)
    total = jnp.sum(eigvals)
    safe = jnp.where(total < TOL, jnp.ones_like(eigvals) / eigvals.shape[0], eigvals / total)
    return eigvecs @ jnp.diag(safe.astype(CTYPE)) @ jnp.conj(eigvecs.T)


def local_pair_density(rho_u: jax.Array, rho_v: jax.Array, axis: str, edge_pos: int) -> jax.Array:
    product = jnp.kron(rho_u, rho_v)
    contrast = jnp.asarray(0.10 + 0.025 * axis_index(axis) + 0.001 * (edge_pos % 7), dtype=CTYPE)
    return normalize_density((1.0 - contrast) * product + contrast * bell_density())


def pair_generator(axis: str) -> jax.Array:
    if axis == "x":
        return jnp.kron(G1, G2) + 0.37 * jnp.kron(G3, I2)
    if axis == "y":
        return jnp.kron(G2, G3) + 0.31 * jnp.kron(I2, G1)
    if axis == "z":
        return jnp.kron(G3, G1) + 0.29 * jnp.kron(G2, I2)
    raise ValueError(axis)


def communication_channel(rho: jax.Array, axis: str) -> jax.Array:
    unitary = jsp_linalg.expm((-0.13j) * pair_generator(axis))
    return normalize_density(unitary @ rho @ jnp.conj(unitary.T))


def cut_projector_channel(rho: jax.Array, axis: str) -> jax.Array:
    if axis == "x":
        observable = jnp.kron(G3, I2) + 0.17 * jnp.kron(I2, G1)
    elif axis == "y":
        observable = jnp.kron(I2, G3) + 0.19 * jnp.kron(G2, I2)
    elif axis == "z":
        observable = jnp.kron(G1, G1) + 0.23 * jnp.kron(I2, G2)
    else:
        raise ValueError(axis)
    observable = observable / jnp.real(jnp.linalg.norm(observable))
    return normalize_density(0.83 * rho + 0.17 * observable @ rho @ jnp.conj(observable.T))


def entropy_from_density(rho: jax.Array) -> float:
    herm = (rho + jnp.conj(rho.T)) / 2.0
    eigs = jnp.clip(jnp.real(jnp.linalg.eigvalsh(herm)), 0.0, None)
    total = jnp.sum(eigs)
    eigs = jnp.where(total > TOL, eigs / total, eigs)
    live = eigs[eigs > 1e-12]
    if int(live.size) == 0:
        return 0.0
    return float((-jnp.sum(live * jnp.log2(live))).item())


def renyi2_from_density(rho: jax.Array) -> float:
    purity = jnp.clip(jnp.real(jnp.trace(rho @ rho)), 1.0e-12, None)
    return float((-jnp.log2(purity)).item())


def partial_trace_two_qubit(rho: jax.Array, keep: str) -> jax.Array:
    reshaped = rho.reshape(2, 2, 2, 2)
    if keep == "A":
        return jnp.einsum("abcb->ac", reshaped)
    if keep == "B":
        return jnp.einsum("abad->bd", reshaped)
    raise ValueError(keep)


def qit_readouts(rho_ab: jax.Array) -> dict[str, float]:
    rho_a = partial_trace_two_qubit(rho_ab, "A")
    rho_b = partial_trace_two_qubit(rho_ab, "B")
    s_ab = entropy_from_density(rho_ab)
    s_a = entropy_from_density(rho_a)
    s_b = entropy_from_density(rho_b)
    return {
        "S_A": s_a,
        "S_B": s_b,
        "S_AB": s_ab,
        "Renyi2_AB": renyi2_from_density(rho_ab),
        "mutual_information": s_a + s_b - s_ab,
        "conditional_entropy_A_given_B": s_ab - s_b,
        "coherent_information_A_to_B": s_b - s_ab,
    }


def cut_comm_signature(rho_pair: jax.Array, axis: str, edge_pos: int) -> tuple[jax.Array, float, dict[str, float]]:
    cut_then_comm = communication_channel(cut_projector_channel(rho_pair, axis), axis)
    comm_then_cut = cut_projector_channel(communication_channel(rho_pair, axis), axis)
    gap = float(jnp.real(jnp.linalg.norm(cut_then_comm - comm_then_cut)).item())
    entropy_a = qit_readouts(cut_then_comm)
    entropy_b = qit_readouts(comm_then_cut)
    entropy_delta = {key: abs(entropy_a[key] - entropy_b[key]) for key in entropy_a}
    signature = jnp.asarray(
        [
            entropy_a["S_A"],
            entropy_a["S_B"],
            entropy_a["S_AB"],
            entropy_a["mutual_information"],
            entropy_a["conditional_entropy_A_given_B"],
            entropy_a["coherent_information_A_to_B"],
            entropy_delta["mutual_information"],
            gap,
            float(axis_index(axis)),
            float(edge_pos) / 128.0,
        ],
        dtype=RTYPE,
    )
    return signature, gap, entropy_a


def order_erased_gap(rho_pair: jax.Array) -> float:
    identity_comm = normalize_density(rho_pair)
    cut_first = normalize_density(cut_projector_channel(identity_comm, "x"))
    comm_first = normalize_density(cut_projector_channel(identity_comm, "x"))
    return float(jnp.real(jnp.linalg.norm(cut_first - comm_first)).item())


def l6_gate(shape: tuple[int, int, int]) -> dict[str, Any]:
    coords = coords_for_shape(shape)
    densities = [density(psi) for psi in site_spinors(coords)]
    signatures = []
    gaps = []
    erased_gaps = []
    entropy_rows = []
    cut_counts = {}
    edge_counter = 0
    for axis in CUT_AXES:
        edges = cut_edges(shape, axis)
        cut_counts[axis] = len(edges)
        for u, v in edges:
            rho_pair = local_pair_density(densities[u], densities[v], axis, edge_counter)
            signature, gap, entropy = cut_comm_signature(rho_pair, axis, edge_counter)
            signatures.append(signature)
            gaps.append(gap)
            entropy_rows.append(entropy)
            erased_gaps.append(order_erased_gap(rho_pair))
            edge_counter += 1
    if not signatures:
        raise RuntimeError(f"no cut signatures for shape {shape}")
    avg_entropy = {
        key: float(sum(row[key] for row in entropy_rows) / len(entropy_rows))
        for key in entropy_rows[0]
    }
    unique_signatures = len({tuple(round(float(x), 8) for x in sig.tolist()) for sig in signatures})
    pass_gate = (
        all(count > 0 for count in cut_counts.values())
        and min(gaps) > GAP_FLOOR
        and max(erased_gaps) < TOL
        and unique_signatures >= len(CUT_AXES)
        and avg_entropy["mutual_information"] > 0.01
    )
    counts = exact_counts(shape)
    return {
        "pass": bool(pass_gate),
        "shape": list(shape),
        "site_count": counts["V"],
        "edge_count": counts["E"],
        "face_count": counts["F"],
        "cell_count": counts["C"],
        "cut_axis_count": len(CUT_AXES),
        "cut_edge_counts": cut_counts,
        "cut_signature_count": len(signatures),
        "unique_entropy_communication_signatures": unique_signatures,
        "min_cut_channel_order_gap": min(gaps),
        "max_cut_channel_order_gap": max(gaps),
        "max_order_erased_gap": max(erased_gaps),
        "average_entropy_readouts": avg_entropy,
        "average_mutual_information": avg_entropy["mutual_information"],
        "dense_state_closure_used": False,
    }


def load_pytorch_result() -> dict[str, Any]:
    return json.loads(PYTORCH_RESULT_PATH.read_text(encoding="utf-8"))


def numeric_delta(a: float, b: float) -> float:
    return abs(float(a) - float(b))


def comparison_receipt(jax_full: dict[str, Any], jax_stress: list[dict[str, Any]]) -> dict[str, Any]:
    if not PYTORCH_RESULT_PATH.exists():
        return {"pass": False, "errors": ["pytorch result missing"], "path": str(PYTORCH_RESULT_PATH)}
    torch_result = load_pytorch_result()
    torch_full = torch_result["positive"]["finite_entropy_cut_communication_over_peps3d_K64"]
    torch_stress = torch_result["positive"]["scale_stress_8_16_32_64_no_dense_closure"]["rows"]
    deltas = {
        "full_64": {
            "min_cut_channel_order_gap": numeric_delta(
                jax_full["min_cut_channel_order_gap"], torch_full["min_cut_channel_order_gap"]
            ),
            "max_cut_channel_order_gap": numeric_delta(
                jax_full["max_cut_channel_order_gap"], torch_full["max_cut_channel_order_gap"]
            ),
            "max_order_erased_gap": numeric_delta(
                jax_full["max_order_erased_gap"], torch_full["max_order_erased_gap"]
            ),
            "cut_signature_count": numeric_delta(
                jax_full["cut_signature_count"], torch_full["cut_signature_count"]
            ),
            "mutual_information": numeric_delta(
                jax_full["average_entropy_readouts"]["mutual_information"],
                torch_full["average_entropy_readouts"]["mutual_information"],
            ),
            "conditional_entropy_A_given_B": numeric_delta(
                jax_full["average_entropy_readouts"]["conditional_entropy_A_given_B"],
                torch_full["average_entropy_readouts"]["conditional_entropy_A_given_B"],
            ),
            "coherent_information_A_to_B": numeric_delta(
                jax_full["average_entropy_readouts"]["coherent_information_A_to_B"],
                torch_full["average_entropy_readouts"]["coherent_information_A_to_B"],
            ),
        },
        "stress_rows": [],
    }
    for jax_row, torch_row in zip(jax_stress, torch_stress):
        deltas["stress_rows"].append(
            {
                "site_count": int(jax_row["site_count"]),
                "site_count_delta": numeric_delta(jax_row["site_count"], torch_row["site_count"]),
                "cut_signature_count_delta": numeric_delta(
                    jax_row["cut_signature_count"], torch_row["cut_signature_count"]
                ),
                "min_order_gap_delta": numeric_delta(
                    jax_row["min_cut_channel_order_gap"], torch_row["min_cut_channel_order_gap"]
                ),
                "average_mutual_information_delta": numeric_delta(
                    jax_row["average_mutual_information"], torch_row["average_mutual_information"]
                ),
            }
        )
    max_delta = max(
        [
            float(value)
            for value in deltas["full_64"].values()
        ]
        + [
            float(value)
            for row in deltas["stress_rows"]
            for key, value in row.items()
            if key.endswith("_delta")
        ]
    )
    bool_checks = {
        "jax_x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "jax_all_scales_pass": all(row["pass"] for row in jax_stress),
        "pytorch_all_pass_read_only": bool(torch_result.get("all_pass") is True),
        "pytorch_promotion_blocked_read_only": bool(torch_result.get("promotion_allowed") is False),
        "same_scale_site_counts": [row["site_count"] for row in jax_stress]
        == [row["site_count"] for row in torch_stress],
        "same_cut_axis_count": int(jax_full["cut_axis_count"]) == int(torch_full["cut_axis_count"]),
    }
    return {
        "pass": bool(max_delta < 1.0e-9 and all(bool_checks.values())),
        "path": str(PYTORCH_RESULT_PATH),
        "max_abs_delta": max_delta,
        "numeric_deltas": deltas,
        "bool_checks": bool_checks,
        "comparison_kind": "read_only_pytorch_receipt_vs_jax_x64_mirror",
    }


def main() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    stress_rows = [l6_gate(shape) for shape in SHAPES]
    full_64 = stress_rows[-1]
    comparison = comparison_receipt(full_64, stress_rows)
    product = qit_readouts(jnp.kron(density(KETS[0]), density(KETS[0])))
    all_scale_pass = all(row["pass"] for row in stress_rows)
    required = {
        "jax_scale_rows_pass": all_scale_pass,
        "readout_parity_pass": bool(comparison["pass"]),
        "product_control_mutual_information_zero": abs(product["mutual_information"]) < TOL,
        "promotion_blocked": PROMOTION_ALLOWED is False,
    }
    all_pass = bool(all(required.values()))
    positive = {
        "jax_mirror_finite_readout_passes": {
            "pass": bool(all_scale_pass),
            "scales": [row["site_count"] for row in stress_rows],
        },
        "read_only_pytorch_comparison_matches": comparison,
    }
    graveyard_companions = {
        "product_cut_entropy_control_collapses_mi": {
            "pass": bool(abs(product["mutual_information"]) < TOL),
            "mutual_information": product["mutual_information"],
        },
        "order_erased_identity_control_collapses": {
            "pass": bool(full_64["max_order_erased_gap"] < TOL),
            "max_order_erased_gap": full_64["max_order_erased_gap"],
        },
    }
    boundary = {
        "no_pytorch_source_mutation": {
            "pass": True,
            "mode": "read-only PyTorch result comparison; this script imports no torch and writes no PyTorch artifacts",
        },
        "promotion_allowed_false": {"pass": True, "promotion_allowed": PROMOTION_ALLOWED},
        "downstream_consumers_locked": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
    }
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": NAME,
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_sha256": source_sha256(),
        "backend": "jax_x64_mirror",
        "finite_map": "JAX mirror of L6_EK local cut pair state rho_uv -> entropy communication signature",
        "domain": "finite PEPS3D-shape cut edges, local two-site densities, cut/channel order paths, and QIT readouts",
        "codomain_or_output": "finite JAX entropy communication signatures plus read-only PyTorch comparison deltas",
        "root_constraints_exercised": {
            "F01": "finite shapes, cut axes, cut edges, local 4x4 densities, and finite readout vectors",
            "N01": "Cut->Communication and Communication->Cut paths have nonzero order gap while order-erased control collapses",
        },
        "all_pass": all_pass,
        "required": required,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(stress_rows),
            "passed": sum(1 for row in stress_rows if row["pass"]),
            "variants": [{"site_count": row["site_count"], "pass": row["pass"]} for row in stress_rows],
        },
        "why_not_v4_probes": [
            "This is a JAX backend mirror/comparison receipt for one existing v5 L6 scout, not a v4 promotion packet.",
            "It keeps downstream layer, Axis0, FEP, flux, physics, and final-manifold consumers locked.",
        ],
        "blockers": [] if all_pass else ["jax_mirror_or_readout_parity_failed"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": {
            "jax": {
                "used": True,
                "role": "load_bearing",
                "reason": "JAX x64 computes the mirror finite map and comparison values",
            },
            "python_json": TOOL_MANIFEST["python_json"],
            "python_pathlib": TOOL_MANIFEST["python_pathlib"],
            "hashlib": TOOL_MANIFEST["hashlib"],
        },
        "tool_integration_depth": {
            "jax": "load_bearing",
            "python_json": "supportive",
            "python_pathlib": "supportive",
            "hashlib": "supportive",
        },
        "pytorch_receipt_read_only": str(PYTORCH_RESULT_PATH),
        "scale_results": stress_rows,
        "backend_comparison": comparison,
        "summary": {
            "all_pass": all_pass,
            "promotion_allowed": PROMOTION_ALLOWED,
            "elapsed_seconds": round(time.time() - started, 6),
            "max_abs_delta": comparison.get("max_abs_delta"),
            "max_sites": max(row["site_count"] for row in stress_rows),
            "scales": [row["site_count"] for row in stress_rows],
            "pytorch_result_read_only": str(PYTORCH_RESULT_PATH),
        },
    }
    RESULT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable(result["summary"]), indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    receipt = main()
    raise SystemExit(0 if receipt["all_pass"] else 1)
