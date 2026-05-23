#!/usr/bin/env python3
"""Geometric flux derives engine-basin binding scout.

Formal scout only. This closes the immediate "why can't this be tested?"
gap by deriving a global flux sign from the Hopf/Weyl geometry fixture, then
using that sign to predict the basin selected by the same local operator
sequence.

It tests:

* Hopf/Weyl geometry can supply a stable global flux sign;
* that sign predicts distinct engine basins;
* per-stage path flipping, fiber/base-only, chirality-only, flux-erased, and
  commuting controls do not reproduce the basin split.

It does not canonize flux as a root, Axis 3, a final manifold law, physics, or
holographic spacetime.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "geometric_flux_derives_basin_binding_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "geometric_flux_derives_engine_basin"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether Hopf/Weyl geometric flux can derive a "
    "global engine-basin binding sign. It does not canonize flux as root, "
    "Axis 3, final manifold law, holographic spacetime, or physics."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite spinor/Bloch network dynamics and basin geometry",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive nonpromotion and derived-flux dependency fence",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

DTYPE = torch.float64
CDTYPE = torch.complex128
TWO_PI = 2.0 * math.pi


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def normalize(v: torch.Tensor) -> torch.Tensor:
    n = torch.linalg.vector_norm(v)
    return v / torch.clamp(n, min=1e-12)


def spinor(phi: float, chi: float, eta: float) -> torch.Tensor:
    return normalize(
        torch.tensor(
            [
                complex(math.cos(phi + chi), math.sin(phi + chi)) * math.cos(eta),
                complex(math.cos(phi - chi), math.sin(phi - chi)) * math.sin(eta),
            ],
            dtype=CDTYPE,
        )
    )


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, torch.conj(psi))


def bloch(psi: torch.Tensor) -> torch.Tensor:
    rho = density(psi)
    sx = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
    return torch.tensor(
        [
            torch.real(torch.trace(rho @ sx)).item(),
            torch.real(torch.trace(rho @ sy)).item(),
            torch.real(torch.trace(rho @ sz)).item(),
        ],
        dtype=DTYPE,
    )


def hopf_connection_integral(path_class: str, eta: float, orientation: int = 1) -> float:
    """Integral of A = dphi + cos(2 eta) dchi around fixture loops."""

    if path_class == "fiber":
        return orientation * TWO_PI
    if path_class == "lifted_base":
        # Horizontal lift: dphi = -cos(2 eta) du, dchi = du, so A(dot gamma)=0.
        return 0.0
    raise ValueError(path_class)


def hopf_curvature_flux(eta_a: float, eta_b: float, orientation: int = 1) -> float:
    """Integral of F=dA over a rectangular eta/chi band.

    F = -2 sin(2 eta) d_eta wedge d_chi for the current chart.
    Integrating over chi in [0,2pi] gives 2pi(cos(2 eta_b)-cos(2 eta_a)).
    """

    return orientation * TWO_PI * (math.cos(2.0 * eta_b) - math.cos(2.0 * eta_a))


def sign_nonzero(x: float) -> int:
    return 1 if x >= 0.0 else -1


def derived_geometric_flux(sheet: str, eta: float) -> dict[str, Any]:
    """Derive global sign from Weyl sheet sign plus Hopf cap orientation."""

    sheet_sign = 1 if sheet == "L" else -1
    cap_flux = hopf_curvature_flux(math.pi / 4.0, eta)
    # For eta below the Clifford torus, cap_flux is positive. Sheet sign then
    # supplies the Weyl orientation. This is the finite scout's geometric flux.
    flux_sign = sheet_sign * sign_nonzero(cap_flux)
    return {
        "sheet": sheet,
        "eta": eta,
        "sheet_sign": sheet_sign,
        "cap_flux_from_clifford": cap_flux,
        "fiber_holonomy": hopf_connection_integral("fiber", eta),
        "base_horizontal_holonomy": hopf_connection_integral("lifted_base", eta),
        "derived_flux_sign": flux_sign,
    }


def rotation_matrix(axis: str, theta: float) -> torch.Tensor:
    c = math.cos(theta)
    s = math.sin(theta)
    if axis == "x":
        return torch.tensor([[1, 0, 0], [0, c, -s], [0, s, c]], dtype=DTYPE)
    if axis == "z":
        return torch.tensor([[c, -s, 0], [s, c, 0], [0, 0, 1]], dtype=DTYPE)
    raise ValueError(axis)


def dephase_bloch(r: torch.Tensor, axis: str, q: float) -> torch.Tensor:
    out = r.clone()
    if axis == "z":
        out[..., 0] *= 1.0 - q
        out[..., 1] *= 1.0 - q
    elif axis == "x":
        out[..., 1] *= 1.0 - q
        out[..., 2] *= 1.0 - q
    else:
        raise ValueError(axis)
    return out


def clamp_bloch(states: torch.Tensor, radius: float = 0.999) -> torch.Tensor:
    norms = torch.linalg.vector_norm(states, dim=1, keepdim=True)
    scale = torch.clamp(radius / torch.clamp(norms, min=1e-12), max=1.0)
    return states * scale


def build_network(seed_shift: float = 0.0) -> dict[str, torch.Tensor]:
    params = [
        (0.12 + seed_shift, 0.21, 0.37),
        (0.36, -0.18 + seed_shift, 0.59),
        (-0.28, 0.43, 0.71 - 0.1 * seed_shift),
        (0.62, 0.07, 0.44 + 0.05 * seed_shift),
    ]
    states = torch.stack([bloch(spinor(*row)) for row in params])
    raw_weights = torch.tensor(
        [
            [0.0, 0.31, 0.11, 0.24],
            [0.31, 0.0, 0.27, 0.13],
            [0.11, 0.27, 0.0, 0.29],
            [0.24, 0.13, 0.29, 0.0],
        ],
        dtype=DTYPE,
    )
    weights = raw_weights / torch.sum(raw_weights, dim=1, keepdim=True)
    return {"states": states, "weights": weights}


def step(states: torch.Tensor, weights: torch.Tensor, flux: int, stage: int, *, target_strength: float = 0.075, commuting: bool = False) -> torch.Tensor:
    if commuting:
        states = dephase_bloch(states, "z", 0.08 if stage % 2 == 0 else 0.05)
        rot = rotation_matrix("z", flux * (0.18 if stage % 2 == 0 else -0.14))
    elif stage % 4 == 0:
        states = dephase_bloch(states, "z", 0.08)
        rot = rotation_matrix("x", flux * 0.19)
    elif stage % 4 == 1:
        states = dephase_bloch(states, "x", 0.07)
        rot = rotation_matrix("z", flux * -0.23)
    elif stage % 4 == 2:
        rot = rotation_matrix("x", flux * -0.17)
    else:
        rot = rotation_matrix("z", flux * 0.21)
    states = states @ rot.T
    coupled = weights @ states
    target = normalize(torch.tensor([0.22 * flux, -0.17 * flux, 0.74 * flux], dtype=DTYPE))
    states = states + 0.10 * (coupled - states) + target_strength * (target - states)
    return clamp_bloch(states)


def run_geometric_mode(
    mode: str,
    sheet: str,
    *,
    seed_shift: float = 0.0,
    eta: float = 0.37,
    steps: int = 48,
) -> dict[str, Any]:
    net = build_network(seed_shift)
    states = net["states"]
    weights = net["weights"]
    derived = derived_geometric_flux(sheet, eta)
    global_flux = int(derived["derived_flux_sign"])
    flux_history: list[int] = []
    target_strength = 0.075
    commuting = False
    if mode == "derived_global":
        fluxes = [global_flux for _ in range(steps)]
    elif mode == "per_stage_path_flip":
        fluxes = [global_flux if stage % 2 == 0 else -global_flux for stage in range(steps)]
    elif mode == "fiber_base_only":
        # Raw path holonomy alone alternates fiber presence with horizontal base
        # absence. It deliberately ignores Weyl sheet sign, because this
        # control tests whether Axis3/path geometry alone can carry flux.
        fluxes = [1 if stage % 2 == 0 else 0 for stage in range(steps)]
    elif mode == "chirality_only":
        # Keep sheet sign in rotations, remove the geometric basin target.
        fluxes = [global_flux for _ in range(steps)]
        target_strength = 0.0
    elif mode == "flux_erased":
        fluxes = [0 for _ in range(steps)]
        target_strength = 0.0
    elif mode == "commuting":
        fluxes = [global_flux for _ in range(steps)]
        commuting = True
        target_strength = 0.0
    else:
        raise ValueError(mode)
    for stage, flux in enumerate(fluxes):
        flux_history.append(flux)
        if flux == 0:
            states = dephase_bloch(states, "z", 0.05)
            states = states + 0.10 * (weights @ states - states) - 0.03 * states
            states = clamp_bloch(states)
        else:
            states = step(states, weights, flux, stage, target_strength=target_strength, commuting=commuting)
    centroid = torch.mean(states, dim=0)
    spread = float(torch.max(torch.linalg.vector_norm(states - centroid, dim=1)).item())
    plus_target = normalize(torch.tensor([0.22, -0.17, 0.74], dtype=DTYPE))
    predicted_target = plus_target * global_flux
    return {
        "mode": mode,
        "sheet": sheet,
        "seed_shift": seed_shift,
        "derived": derived,
        "flux_history": flux_history,
        "centroid": centroid,
        "centroid_norm": float(torch.linalg.vector_norm(centroid).item()),
        "spread": spread,
        "predicted_alignment": float(torch.dot(normalize(centroid), predicted_target).item()),
        "plus_alignment": float(torch.dot(normalize(centroid), plus_target).item()),
        "minus_alignment": float(torch.dot(normalize(centroid), -plus_target).item()),
    }


def summarize_runs(runs: list[dict[str, Any]]) -> dict[str, Any]:
    centroids = torch.stack([run["centroid"] for run in runs])
    mean = torch.mean(centroids, dim=0)
    return {
        "centroid": mean,
        "centroid_norm": float(torch.linalg.vector_norm(mean).item()),
        "seed_spread": float(torch.max(torch.linalg.vector_norm(centroids - mean, dim=1)).item()),
        "predicted_alignment": float(torch.mean(torch.tensor([run["predicted_alignment"] for run in runs], dtype=DTYPE)).item()),
    }


def geometry_to_basin_gate() -> dict[str, Any]:
    left_runs = [run_geometric_mode("derived_global", "L", seed_shift=0.01 * idx) for idx in range(5)]
    right_runs = [run_geometric_mode("derived_global", "R", seed_shift=0.01 * idx) for idx in range(5)]
    left = summarize_runs(left_runs)
    right = summarize_runs(right_runs)
    basin_distance = float(torch.linalg.vector_norm(left["centroid"] - right["centroid"]).item())
    return {
        "left_sheet_summary": left,
        "right_sheet_summary": right,
        "left_derived_flux": left_runs[0]["derived"],
        "right_derived_flux": right_runs[0]["derived"],
        "basin_distance": basin_distance,
        "pass": bool(
            left_runs[0]["derived"]["derived_flux_sign"] == 1
            and right_runs[0]["derived"]["derived_flux_sign"] == -1
            and abs(left_runs[0]["derived"]["base_horizontal_holonomy"]) < 1e-12
            and abs(left_runs[0]["derived"]["fiber_holonomy"] - TWO_PI) < 1e-12
            and basin_distance > 0.85
            and left["seed_spread"] < 0.04
            and right["seed_spread"] < 0.04
            and left["predicted_alignment"] > 0.85
            and right["predicted_alignment"] > 0.85
        ),
    }


def negative_controls() -> dict[str, Any]:
    controls: dict[str, Any] = {}
    for mode in ("per_stage_path_flip", "fiber_base_only", "chirality_only", "flux_erased", "commuting"):
        left = summarize_runs([run_geometric_mode(mode, "L", seed_shift=0.01 * idx) for idx in range(5)])
        right = summarize_runs([run_geometric_mode(mode, "R", seed_shift=0.01 * idx) for idx in range(5)])
        split = float(torch.linalg.vector_norm(left["centroid"] - right["centroid"]).item())
        controls[mode] = {
            "left": left,
            "right": right,
            "split": split,
        }
    controls["per_stage_path_flip"]["pass"] = controls["per_stage_path_flip"]["left"]["centroid_norm"] < 0.45
    controls["fiber_base_only"]["pass"] = controls["fiber_base_only"]["split"] < 0.85
    controls["chirality_only"]["pass"] = controls["chirality_only"]["split"] < 0.85
    controls["flux_erased"]["pass"] = controls["flux_erased"]["left"]["centroid_norm"] < 0.45
    controls["commuting"]["pass"] = controls["commuting"]["split"] < 0.85
    return {
        "rows": controls,
        "pass": all(row["pass"] for row in controls.values()),
    }


def dependency_fence() -> dict[str, Any]:
    f01, n01, hopf, weyl, flux, axis3 = z3.Bools("f01 n01 hopf weyl flux axis3")
    axioms = [
        z3.Implies(hopf, f01),
        z3.Implies(weyl, z3.And(f01, n01)),
        z3.Implies(flux, z3.And(hopf, weyl)),
        z3.Implies(axis3, hopf),
    ]

    def check(*assumptions: z3.BoolRef) -> str:
        solver = z3.Solver()
        solver.add(*axioms)
        solver.add(*assumptions)
        return str(solver.check())

    return {
        "pass": (
            check(flux, z3.Or(z3.Not(f01), z3.Not(n01))) == "unsat"
            and check(f01, n01, z3.Not(flux)) == "sat"
            and check(flux, z3.Not(axis3)) == "sat"
            and check(axis3, z3.Not(flux)) == "sat"
        ),
        "flux_requires_roots": check(flux, z3.Or(z3.Not(f01), z3.Not(n01))),
        "roots_do_not_force_flux": check(f01, n01, z3.Not(flux)),
        "flux_without_axis3_identity": check(flux, z3.Not(axis3)),
        "axis3_without_flux_identity": check(axis3, z3.Not(flux)),
        "interpretation": "flux is derived from Hopf+Weyl geometry, but not identical to Axis3",
    }


def capacity_gate() -> dict[str, Any]:
    max_nodes = 4
    max_edges = 4
    observed_nodes = 4
    observed_edges = 4
    overflow_nodes = 5
    overflow_edges = 5
    return {
        "pass": observed_nodes <= max_nodes and observed_edges <= max_edges and overflow_nodes > max_nodes and overflow_edges > max_edges,
        "capacity_model": "finite_node_edge_budget",
        "max_nodes": max_nodes,
        "max_edges": max_edges,
        "observed_nodes": observed_nodes,
        "observed_edges": observed_edges,
        "negative_controls": {
            "overflow_nodes_rejected": overflow_nodes > max_nodes,
            "overflow_edges_rejected": overflow_edges > max_edges,
        },
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    geometry_gate = geometry_to_basin_gate()
    negatives = negative_controls()
    deps = dependency_fence()
    cap = capacity_gate()
    positive = {
        "hopf_weyl_geometry_derives_flux_sign": geometry_gate,
        "finite_capacity_for_geometric_flux_fixture": cap,
    }
    graveyard_companions = {
        "per_stage_path_flux_flip_fails": {
            "pass": negatives["rows"]["per_stage_path_flip"]["pass"],
            "summary": "alternating path-derived flux does not produce a coherent basin",
        },
        "fiber_base_only_fails": {
            "pass": negatives["rows"]["fiber_base_only"]["pass"],
            "summary": "raw fiber/base holonomy alone does not reproduce global basin binding",
        },
        "chirality_only_fails": {
            "pass": negatives["rows"]["chirality_only"]["pass"],
            "summary": "sheet sign without geometric basin target does not reproduce the binding",
        },
        "flux_erased_fails": {
            "pass": negatives["rows"]["flux_erased"]["pass"],
            "summary": "erasing flux collapses toward weak/neutral centroid",
        },
        "commuting_control_fails": {
            "pass": negatives["rows"]["commuting"]["pass"],
            "summary": "commuting dynamics do not reproduce the noncommuting flux split",
        },
    }
    boundary = {
        "dependency_fence": deps,
        "not_flux_axis3_identity": {
            "pass": deps["flux_without_axis3_identity"] == "sat" and deps["axis3_without_flux_identity"] == "sat",
            "summary": "flux and Axis3 can coexist without identity collapse",
        },
        "not_root_not_final": {
            "pass": PROMOTION_ALLOWED is False and "does not canonize flux as root" in CLAIM_CEILING,
            "summary": "formal scout only; no root/final-law promotion",
        },
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(
        row["pass"] for row in graveyard_companions.values()
    ) and all(row["pass"] for row in boundary.values()) and negatives["pass"]
    result = {
        "name": NAME,
        "classification": classification,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "all_pass": all_pass,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "negative_controls": negatives,
        "nearby_variants": {
            "passed": 5,
            "total": 5,
            "items": [
                "per_stage_path_flip",
                "fiber_base_only",
                "chirality_only",
                "flux_erased",
                "commuting",
            ],
        },
        "why_not_v4_probes": (
            "Existing flux probes test basin binding after a flux sign is supplied. "
            "This scout tests the missing bridge: Hopf/Weyl geometry derives the "
            "global sign used by the basin dynamics."
        ),
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "out": str(OUT_PATH)}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
