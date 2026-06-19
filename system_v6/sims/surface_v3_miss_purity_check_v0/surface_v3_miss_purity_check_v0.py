#!/usr/bin/env python3
"""Micro-check for the spinor surface v3 entangled_nonproduct miss.

This packet consumes the committed v3 construction by source hash, recomputes
the entangled pattern's reduced states exactly from that construction, and
adjudicates the alt-view purity-shrinkage explanation.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


SIM_ID = "surface_v3_miss_purity_check_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"

V3_DIR = ROOT / "system_v6" / "sims" / "spinor_network_surface_v3"
V3_JAX_SOURCE = V3_DIR / "spinor_network_surface_v3_jax.py"
V3_ENVELOPE_RESULT = V3_DIR / "results" / "spinor_network_surface_v3_envelope_results.json"
ALT_VIEW_RECEIPT = ROOT / "system_v6" / "receipts" / "altviews_capability_and_surface_miss_20260612.md"

N_SITES = 4
DIM = 2**N_SITES
THETA = 0.31
PHASE = 0.37
GRID = [-1.0, -0.5, 0.0, 0.5, 1.0]
PREDICTED_MISS_CELL = "A33_x00_y00_zm10"
PREDICTED_PLUS_CELL = "A33_x00_y00_zp10"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return to_jsonable(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, complex):
        return {"re": float(value.real), "im": float(value.imag)}
    if isinstance(value, float):
        return float(value) if math.isfinite(value) else str(value)
    return value


def stable_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(to_jsonable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_jsonable(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def a33_rows() -> list[tuple[float, float, float]]:
    return [
        (x, y, z)
        for x in GRID
        for y in GRID
        for z in GRID
        if x * x + y * y + z * z <= 1.000000001
    ]


def cell_token(value: float) -> str:
    sign = "p" if value > 0 else "m" if value < 0 else "0"
    return f"{sign}{int(round(abs(value) * 10))}"


def a33_cell_id(row: tuple[float, float, float]) -> str:
    return "A33_x%s_y%s_z%s" % tuple(cell_token(v) for v in row)


A33_ROWS = a33_rows()
A33_BY_ID = {a33_cell_id(row): row for row in A33_ROWS}


def chart_cell_id(coords: tuple[float, float, float]) -> tuple[str, float]:
    snapped = min(A33_ROWS, key=lambda row: sum((row[idx] - coords[idx]) ** 2 for idx in range(3)))
    residual = math.sqrt(sum((snapped[idx] - coords[idx]) ** 2 for idx in range(3)))
    return a33_cell_id(snapped), residual


def entangled_state(theta: float = THETA, phase: float = PHASE) -> np.ndarray:
    state = np.zeros(DIM, dtype=np.complex128)
    state[0] = math.cos(theta)
    state[15] = math.sin(theta) * np.exp(1.0j * phase)
    return state / np.linalg.norm(state)


def density(psi: np.ndarray) -> np.ndarray:
    return np.outer(psi, np.conjugate(psi))


def reduce_density(rho: np.ndarray, keep: list[int]) -> np.ndarray:
    keep_set = set(keep)
    tensor = np.reshape(rho, [2] * (2 * N_SITES))
    active_n = N_SITES
    for site in sorted(set(range(N_SITES)) - keep_set, reverse=True):
        tensor = np.trace(tensor, axis1=site, axis2=site + active_n)
        active_n -= 1
    dim = 2 ** len(keep)
    return np.reshape(tensor, (dim, dim))


def bloch_coords(rho1: np.ndarray) -> tuple[float, float, float]:
    sigma_x = np.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
    sigma_y = np.asarray([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
    sigma_z = np.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
    return tuple(float(np.real(np.trace(rho1 @ p))) for p in [sigma_x, sigma_y, sigma_z])  # type: ignore[return-value]


def radius(coords: tuple[float, float, float]) -> float:
    return math.sqrt(sum(v * v for v in coords))


def cell_radius_band(cell_id: str) -> dict[str, float]:
    row = A33_BY_ID[cell_id]
    row_radius = radius(row)
    if cell_id in {PREDICTED_MISS_CELL, PREDICTED_PLUS_CELL}:
        return {
            "cell_id": cell_id,
            "row_radius": row_radius,
            "axis_voronoi_min_radius": 0.75,
            "axis_voronoi_max_radius": 1.0,
            "note": "nearest-neighbor A33 pole cell on its axis; boundary to +/-0.5 row is radius 0.75",
        }
    return {
        "cell_id": cell_id,
        "row_radius": row_radius,
        "axis_voronoi_min_radius": max(0.0, row_radius - 0.25),
        "axis_voronoi_max_radius": min(1.0, row_radius + 0.25),
        "note": "generic half-step radial band for A33 grid row",
    }


def load_v3_result() -> dict[str, Any]:
    return json.loads(V3_ENVELOPE_RESULT.read_text(encoding="utf-8"))


def extract_v3_recovery(v3: dict[str, Any]) -> dict[str, Any]:
    structured = v3["pre_registered_structured_prediction"]
    chart = v3.get("chart_recovery") or v3["recoverability_VERDICT"]
    missed = structured["missed_predicted_family_cell_pairs"]
    recovered_pairs = structured["recovered_predicted_family_cell_pairs"]
    return {
        "v3_predicted_entangled_cells": structured["structured_predictions"]["entangled_nonproduct"],
        "v3_missed_predicted_pairs": missed,
        "v3_recovered_predicted_pairs": recovered_pairs,
        "v3_recovered_nonorigin_cell_ids": chart["recovered_nonorigin_cell_ids"],
        "v3_entangled_predicted_plus_recovered": f"entangled_nonproduct:{PREDICTED_PLUS_CELL}" in recovered_pairs,
        "v3_entangled_predicted_minus_recovered": f"entangled_nonproduct:{PREDICTED_MISS_CELL}" in recovered_pairs,
    }


def reduced_rows_for_phase(phase: float) -> list[dict[str, Any]]:
    psi = entangled_state(theta=THETA, phase=phase)
    rho = density(psi)
    rows: list[dict[str, Any]] = []
    for site in range(N_SITES):
        rho1 = reduce_density(rho, [site])
        coords = bloch_coords(rho1)
        cell_id, residual = chart_cell_id(coords)
        eigvals = np.linalg.eigvalsh((rho1 + np.conjugate(rho1.T)) / 2.0)
        purity = float(np.real(np.trace(rho1 @ rho1)))
        rows.append(
            {
                "site": site,
                "rho_re_im": [[[float(z.real), float(z.imag)] for z in row] for row in rho1],
                "eigenvalues": [float(v) for v in eigvals],
                "bloch": coords,
                "bloch_radius": radius(coords),
                "linear_entropy": 1.0 - purity,
                "purity": purity,
                "corrected_cell": cell_id,
                "alignment_residual": residual,
            }
        )
    return rows


def main() -> None:
    v3 = load_v3_result()
    v3_recovery = extract_v3_recovery(v3)
    reduced_rows = reduced_rows_for_phase(PHASE)
    miss_band = cell_radius_band(PREDICTED_MISS_CELL)
    plus_band = cell_radius_band(PREDICTED_PLUS_CELL)

    corrected_cells = sorted({row["corrected_cell"] for row in reduced_rows})
    actual_radius = reduced_rows[0]["bloch_radius"]
    radii_equal = max(abs(row["bloch_radius"] - actual_radius) for row in reduced_rows) <= 1.0e-12
    phase_probe_rows = [
        {
            "phase": phase,
            "corrected_cells": sorted({row["corrected_cell"] for row in reduced_rows_for_phase(phase)}),
            "bloch_radii": [row["bloch_radius"] for row in reduced_rows_for_phase(phase)],
            "bloch_z": [row["bloch"][2] for row in reduced_rows_for_phase(phase)],
        }
        for phase in [0.0, PHASE, math.pi]
    ]
    phase_invariant = len({stable_hash(row["corrected_cells"]) for row in phase_probe_rows}) == 1 and max(
        max(abs(r - actual_radius) for r in row["bloch_radii"]) for row in phase_probe_rows
    ) <= 1.0e-12

    strict_radius_band_explanation = actual_radius < miss_band["axis_voronoi_min_radius"]
    mixed_below_pure_surface = actual_radius < miss_band["row_radius"]
    corrected_cell = corrected_cells[0] if len(corrected_cells) == 1 else "mixed_site_cells"
    corrected_recovered = corrected_cell in v3_recovery["v3_recovered_nonorigin_cell_ids"]
    prediction_label_error = corrected_cell != PREDICTED_MISS_CELL

    payload: dict[str, Any] = {
        "schema": "codex_ratchet.surface_v3_miss_purity_check_v0.results.v1",
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(
            mixed_below_pure_surface
            and corrected_recovered
            and radii_equal
            and phase_invariant
            and prediction_label_error
        ),
        "authority": {
            "surface_v3_commit": "b02444162",
            "alt_view_commit": "731b61933",
            "v3_jax_source_path": rel(V3_JAX_SOURCE),
            "v3_jax_source_sha256": sha256_file(V3_JAX_SOURCE),
            "v3_envelope_result_path": rel(V3_ENVELOPE_RESULT),
            "v3_envelope_result_sha256": sha256_file(V3_ENVELOPE_RESULT),
            "alt_view_receipt_path": rel(ALT_VIEW_RECEIPT),
            "alt_view_receipt_sha256": sha256_file(ALT_VIEW_RECEIPT),
            "committed_v3_entangled_formula": "cos(0.31)|0000> + sin(0.31)exp(i*0.37)|1111>",
        },
        "exact_formula_rows": {
            "single_site_rho": [
                [math.cos(THETA) ** 2, 0.0],
                [0.0, math.sin(THETA) ** 2],
            ],
            "bloch_z_exact_formula": "cos(2*0.31)",
            "bloch_radius_exact_formula": "abs(cos(2*0.31))",
            "bloch_z_value": math.cos(2.0 * THETA),
            "bloch_radius_value": abs(math.cos(2.0 * THETA)),
            "linear_entropy_formula": "1 - (cos(0.31)^4 + sin(0.31)^4)",
            "linear_entropy_value": 1.0 - (math.cos(THETA) ** 4 + math.sin(THETA) ** 4),
        },
        "per_site_reduced_density_matrices": reduced_rows,
        "predicted_minus_z_cell_radius_band": miss_band,
        "predicted_plus_z_cell_radius_band": plus_band,
        "v3_recovery": v3_recovery,
        "adjudication": {
            "prediction_error_not_recovery_error": prediction_label_error and corrected_recovered,
            "reason": "The committed entangled_nonproduct marginal is mixed (radius about 0.813878 < 1) and has z>0; it snaps to +z, not the pre-registered -z miss cell. Under the nearest-neighbor A33 pole-band convention its radius is not below the pole cell's 0.75 radial lower boundary, so the strict radius-band discriminator does not fire by itself.",
            "alt_view_mixed_marginal_confirmed": mixed_below_pure_surface,
            "alt_view_strict_radius_band_explanation_confirmed": strict_radius_band_explanation,
            "corrected_prediction_cell": corrected_cell,
            "corrected_prediction_recovered_by_v3": corrected_recovered,
            "v3_minus_z_miss_reinterpreted_as_prediction_label_error": prediction_label_error and corrected_recovered,
            "v3_plus_z_recovery_pair_present": v3_recovery["v3_entangled_predicted_plus_recovered"],
        },
        "cheap_discriminators": {
            "gauge_mismatch_phase_probe": {
                "phase_rows": phase_probe_rows,
                "phase_invariant_reduced_states": phase_invariant,
                "verdict": "GAUGE_MISMATCH_NOT_SUPPORTED_CHEAP_PHASE_CHECK" if phase_invariant else "GAUGE_MISMATCH_STILL_OPEN",
                "scope": "global |0000> vs |1111> relative phase changes do not change single-site marginals for this committed construction",
            },
            "dark_state_or_dissipative_bias": {
                "verdict": "NOT_RUN_HEAVIER_THAN_MICRO_CHECK",
                "reason": "requires trajectory dynamics beyond this one-packet reduced-state adjudication",
            },
        },
        "TOOL_MANIFEST": {
            "numpy": {
                "used": True,
                "reason": "load-bearing exact finite vector/density construction and partial trace arithmetic",
            },
            "json": {
                "used": True,
                "reason": "supportive consumption of committed v3 result surface and output artifact",
            },
        },
        "TOOL_INTEGRATION_DEPTH": {
            "numpy": "load_bearing",
            "json": "supportive",
        },
        "claim_ceiling": "micro scratch diagnostic only; confirms/demotes the v3 entangled_nonproduct miss interpretation, no surface-doctrine promotion, no engine/admission/physics claim",
        "result_hash": "",
    }
    payload["result_hash"] = stable_hash({k: v for k, v in payload.items() if k != "result_hash"})
    write_json(RESULT_PATH, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": rel(RESULT_PATH)}, sort_keys=True))


if __name__ == "__main__":
    main()
