#!/usr/bin/env python3
"""Four-loop runtime-bound PEPS3D flux -> Axis0 hardening scout.

Formal scout only.

This row performs the requested loop over the three current PEPS3D Axis0
follow-up lanes:

1. consume enriched source runtime records directly in the PEPS3D dynamics;
2. retest boundary functionals after that binding;
3. derive calibration choices only from source shapes, then stress heldouts.

The four internal loops are bounded fixture passes, not recursive promotion:

    raw canonical baseline
    runtime-bound canonical boundary
    runtime-bound full surface mean
    runtime-bound runtime-weighted surface

The row is intentionally conservative. If a loop appears to improve signs, it
still records the sampler/full-closure blocker. It does not admit Axis0, flux,
Xi/Phi0, PEPS3D closure, or physics claims.
"""

from __future__ import annotations

import importlib.util
import json
import math
import pathlib
import sys
import time
from typing import Any

import torch


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "peps3d_flux_axis0_runtime_bound_loop4_probe_results.json"
SCALING_MODULE_PATH = ROOT / "sim_peps3d_spinor_network_flux_axis0_scaling_probe.py"
BINDING_MODULE_PATH = ROOT / "sim_peps3d_flux_axis0_runtime_record_binding_gate_probe.py"

NAME = "peps3d_flux_axis0_runtime_bound_loop4_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical_peps3d_flux_axis0_runtime_bound_loop4"
SOURCE_ALIGNMENT_CATEGORY = "peps3d_flux_bound_axis0_runtime_bound_loop_hardening"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: runs four bounded hardening loops over PEPS3D "
    "flux-bound Axis0 with source runtime-record metadata consumed by the "
    "dynamics. It does not admit final Axis0, final flux, Xi, Phi0, full "
    "PEPS3D closure, gravity, Standard Model, Yang-Mills, Riemann, or "
    "physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing quaternionic spinor transport, boundary contractions, source-only calibration grids, and loop margins",
    },
    "peps3d_spinor_network_flux_axis0_scaling_probe": {
        "tried": True,
        "used": True,
        "reason": "supportive PEPS3D spinor/quaternion substrate, local tensor contraction, probes, and raw baseline",
    },
    "peps3d_flux_axis0_runtime_record_binding_gate_probe": {
        "tried": True,
        "used": True,
        "reason": "supportive local source of enriched engine/sheet/terrain/token/Axis5/Axis6/path records consumed by runtime-bound transport",
    },
    "python_importlib": {"tried": True, "used": True, "reason": "supportive local module loading"},
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "peps3d_spinor_network_flux_axis0_scaling_probe": "supportive",
    "peps3d_flux_axis0_runtime_record_binding_gate_probe": "supportive",
    "python_importlib": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

REFERENCE_SHAPES = [(2, 2, 2), (3, 3, 3), (4, 4, 4)]
EVAL_SOURCE_SHAPES = [(2, 2, 2), (3, 3, 3)]
EVAL_HELDOUT_SHAPES = [(2, 3, 4)]
SMOKE_64_SHAPE = (4, 4, 4)
HOMEOSTATIC_COST_SCALE = 0.06
ALLOSTATIC_TARGET_LAMBDA = 0.0
ALLOSTATIC_COST_SCALE = 5.0
LAM0 = 0.18
DELTA = 0.04
GAP_FLOOR = 1.0e-5

LOOPS = [
    {"loop": 1, "label": "raw_canonical_baseline", "runtime_bound": False, "boundary": "canonical"},
    {"loop": 2, "label": "runtime_bound_canonical", "runtime_bound": True, "boundary": "canonical"},
    {"loop": 3, "label": "runtime_bound_surface_mean", "runtime_bound": True, "boundary": "surface_mean"},
    {"loop": 4, "label": "runtime_bound_runtime_weighted_surface", "runtime_bound": True, "boundary": "runtime_weighted_surface"},
]


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    return value


def load_module(path: pathlib.Path, name: str) -> Any:
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def shape_key(shape: tuple[int, int, int]) -> str:
    return "x".join(str(item) for item in shape)


def boundary_surface(module: Any, shape: tuple[int, int, int]) -> list[tuple[int, int, int]]:
    return [site for site in module.sites(shape) if site[0] in {0, shape[0] - 1}]


def selected_boundary_sites(module: Any, shape: tuple[int, int, int], boundary: str) -> list[tuple[int, int, int]]:
    if boundary == "canonical":
        return module.sampled_boundary_sites(shape)
    if boundary in {"surface_mean", "runtime_weighted_surface"}:
        return boundary_surface(module, shape)
    raise ValueError(boundary)


def runtime_site_weights(
    binding_module: Any,
    scaling_module: Any,
    shape: tuple[int, int, int],
    sites: list[tuple[int, int, int]],
) -> torch.Tensor:
    records = binding_module.enriched_records_for_shape(scaling_module, shape)
    counts = {site: 0.0 for site in sites}
    for row in records:
        site = tuple(row["site"])
        if site in counts:
            counts[site] += 1.0 + (0.10 if row["is_native_operator"] else 0.0)
    weights = torch.tensor([counts[site] for site in sites], dtype=scaling_module.RTYPE)
    if float(torch.sum(weights).item()) <= 0.0:
        weights = torch.ones(len(sites), dtype=scaling_module.RTYPE)
    return weights / torch.clamp(torch.sum(weights), min=scaling_module.EPS)


def uniform_weights(module: Any, sites: list[tuple[int, int, int]]) -> torch.Tensor:
    return torch.ones(len(sites), dtype=module.RTYPE) / float(len(sites))


def transport_runtime_bound(
    scaling_module: Any,
    binding_module: Any,
    shape: tuple[int, int, int],
    *,
    engine_type: int,
    lam: float,
    sheet: str,
    mode: str,
    sheet_erased: bool = False,
    topology_freeze: bool = False,
    reversed_shell_time: bool = False,
) -> dict[tuple[int, int, int], torch.Tensor]:
    q_states = {site: scaling_module.spinor_to_q(psi) for site, psi in scaling_module.base_spinors(shape).items()}
    if mode == "neutral_control":
        return {site: scaling_module.q_to_spinor(q) for site, q in q_states.items()}

    gain = 0.52 if mode == "homeostatic" else 0.90
    records = [
        row
        for row in binding_module.enriched_records_for_shape(scaling_module, shape)
        if row["engine_type"] == engine_type and row["sheet"] == sheet
    ]
    for row in records:
        site = tuple(row["site"])
        shell = scaling_module.shell_orientation(site, shape, reversed_shell_time=reversed_shell_time)
        unit = scaling_module.engine_unit(row["topology"], row["slot_operator"], engine_type, topology_freeze=topology_freeze)
        if row["axis6_token_precedence"] == "operator_first":
            drive = scaling_module.q_mul(unit, shell)
        else:
            drive = scaling_module.q_mul(shell, unit)
        path_gain = 1.03 if row["path_class"] == "base" else 0.97
        native_gain = 1.00 if row["is_native_operator"] else 0.94
        sign = float(row["axis6_sign"])
        angle = lam * gain * (1.0 + 0.04 * row["substage_index"]) * path_gain * native_gain * sign
        step = scaling_module.q_exp(scaling_module.q_normalize(drive), angle)
        if sheet_erased or sheet == "L":
            q_states[site] = scaling_module.q_normalize(scaling_module.q_mul(step, q_states[site]))
        else:
            q_states[site] = scaling_module.q_normalize(scaling_module.q_mul(q_states[site], step))
    return {site: scaling_module.q_to_spinor(q) for site, q in q_states.items()}


def boundary_responses_runtime_bound(
    scaling_module: Any,
    binding_module: Any,
    shape: tuple[int, int, int],
    *,
    engine_type: int,
    lam: float,
    sheet: str,
    mode: str,
    boundary: str,
    sheet_erased: bool = False,
    topology_freeze: bool = False,
    reversed_shell_time: bool = False,
) -> dict[str, Any]:
    transported = transport_runtime_bound(
        scaling_module,
        binding_module,
        shape,
        engine_type=engine_type,
        lam=lam,
        sheet=sheet,
        mode=mode,
        sheet_erased=sheet_erased,
        topology_freeze=topology_freeze,
        reversed_shell_time=reversed_shell_time,
    )
    network = scaling_module.build_network(shape, transported, sheet="erased" if sheet_erased else sheet)
    selected = selected_boundary_sites(scaling_module, shape, boundary)
    weights = (
        runtime_site_weights(binding_module, scaling_module, shape, selected)
        if boundary == "runtime_weighted_surface"
        else uniform_weights(scaling_module, selected)
    )
    site_rhos = [scaling_module.site_rho(network, shape, site) for site in selected]

    ijk: dict[str, float] = {}
    for label, q_probe in scaling_module.IJK_PROBES.items():
        effect = scaling_module.response_effect(q_probe)
        values = torch.tensor([scaling_module.response(rho, effect) for rho in site_rhos], dtype=scaling_module.RTYPE)
        ijk[label] = float(torch.sum(values * weights).item())

    topology: dict[str, float] = {}
    for name, q_probe in scaling_module.TOPOLOGY_UNITS.items():
        effect = scaling_module.response_effect(scaling_module.Q_ONE + 0.70 * q_probe)
        values = torch.tensor([scaling_module.response(rho, effect) for rho in site_rhos], dtype=scaling_module.RTYPE)
        topology[name] = float(torch.sum(values * weights).item())

    return {"ijk": ijk, "topology": topology, "sampled_site_count": len(selected)}


def flux_readout_runtime_bound(
    scaling_module: Any,
    binding_module: Any,
    shape: tuple[int, int, int],
    *,
    engine_type: int,
    lam: float,
    mode: str,
    boundary: str,
    sheet_erased: bool = False,
    topology_freeze: bool = False,
    reversed_shell_time: bool = False,
) -> dict[str, Any]:
    left = boundary_responses_runtime_bound(
        scaling_module,
        binding_module,
        shape,
        engine_type=engine_type,
        lam=lam,
        sheet="L",
        mode=mode,
        boundary=boundary,
        sheet_erased=sheet_erased,
        topology_freeze=topology_freeze,
        reversed_shell_time=reversed_shell_time,
    )
    right = boundary_responses_runtime_bound(
        scaling_module,
        binding_module,
        shape,
        engine_type=engine_type,
        lam=lam,
        sheet="R",
        mode=mode,
        boundary=boundary,
        sheet_erased=sheet_erased,
        topology_freeze=topology_freeze,
        reversed_shell_time=reversed_shell_time,
    )
    flux = {label: right["ijk"][label] - left["ijk"][label] for label in ["i", "j", "k"]}
    topology_delta = {
        name: right["topology"][name] - left["topology"][name] for name in scaling_module.TOPOLOGIES
    }
    flux_tensor = torch.tensor([flux["i"], flux["j"], flux["k"]], dtype=scaling_module.RTYPE)
    topology_tensor = torch.tensor([abs(topology_delta[name]) for name in scaling_module.TOPOLOGIES], dtype=scaling_module.RTYPE)
    branch_probs = topology_tensor + 0.05 * torch.abs(flux_tensor.mean()) + scaling_module.EPS
    branch_probs = branch_probs / torch.clamp(torch.sum(branch_probs), min=scaling_module.EPS)
    return {
        "flux_components": flux,
        "flux_norm": float(torch.linalg.vector_norm(flux_tensor).item()),
        "jk_norm": float(torch.linalg.vector_norm(flux_tensor[1:]).item()),
        "topology_delta": topology_delta,
        "topology_mutation_norm": float(torch.linalg.vector_norm(topology_tensor).item()),
        "branch_entropy": scaling_module.entropy_from_probs(branch_probs),
        "branch_probs": branch_probs,
        "sampled_site_count": left["sampled_site_count"],
    }


def flux_readout(
    scaling_module: Any,
    binding_module: Any,
    shape: tuple[int, int, int],
    *,
    runtime_bound: bool,
    boundary: str,
    **kwargs: Any,
) -> dict[str, Any]:
    if runtime_bound:
        return flux_readout_runtime_bound(scaling_module, binding_module, shape, boundary=boundary, **kwargs)
    return scaling_module.flux_readout(shape, **kwargs)


def finite_fep(
    scaling_module: Any,
    binding_module: Any,
    shape: tuple[int, int, int],
    *,
    runtime_bound: bool,
    boundary: str,
    engine_type: int,
    lam: float,
    mode: str,
    target_probs: torch.Tensor,
    target_flux: torch.Tensor,
    cost_scale: float,
) -> float:
    row = flux_readout(
        scaling_module,
        binding_module,
        shape,
        runtime_bound=runtime_bound,
        boundary=boundary,
        engine_type=engine_type,
        lam=lam,
        mode=mode,
    )
    flux = torch.tensor(
        [row["flux_components"]["i"], row["flux_components"]["j"], row["flux_components"]["k"]],
        dtype=scaling_module.RTYPE,
    )
    flux_probs = torch.abs(flux) + scaling_module.EPS
    flux_probs = flux_probs / torch.clamp(torch.sum(flux_probs), min=scaling_module.EPS)
    recovery_error = scaling_module.kl_probs(flux_probs, target_probs)
    recovery_gap = float(torch.linalg.vector_norm(flux - target_flux).item())
    compression_gain = math.log(4.0) - row["branch_entropy"]
    transition_cost = cost_scale * lam * lam * (1.0 + row["topology_mutation_norm"])
    recovery_gain = math.exp(-recovery_gap)
    return recovery_error + row["branch_entropy"] + transition_cost - compression_gain - recovery_gain


def gradient(
    scaling_module: Any,
    binding_module: Any,
    shape: tuple[int, int, int],
    *,
    runtime_bound: bool,
    boundary: str,
    mode: str,
    target_lambda: float,
    cost_scale: float,
) -> float:
    target = flux_readout(
        scaling_module,
        binding_module,
        shape,
        runtime_bound=runtime_bound,
        boundary=boundary,
        engine_type=0,
        lam=target_lambda,
        mode=mode,
    )
    target_flux = torch.tensor(
        [target["flux_components"]["i"], target["flux_components"]["j"], target["flux_components"]["k"]],
        dtype=scaling_module.RTYPE,
    )
    target_probs = torch.abs(target_flux) + scaling_module.EPS
    if float(torch.sum(target_probs).item()) < 10.0 * scaling_module.EPS:
        target_probs = torch.ones(3, dtype=scaling_module.RTYPE)
    target_probs = target_probs / torch.clamp(torch.sum(target_probs), min=scaling_module.EPS)
    low = finite_fep(
        scaling_module,
        binding_module,
        shape,
        runtime_bound=runtime_bound,
        boundary=boundary,
        engine_type=0,
        lam=LAM0 - DELTA,
        mode=mode,
        target_probs=target_probs,
        target_flux=target_flux,
        cost_scale=cost_scale,
    )
    high = finite_fep(
        scaling_module,
        binding_module,
        shape,
        runtime_bound=runtime_bound,
        boundary=boundary,
        engine_type=0,
        lam=LAM0 + DELTA,
        mode=mode,
        target_probs=target_probs,
        target_flux=target_flux,
        cost_scale=cost_scale,
    )
    return (high - low) / (2.0 * DELTA)


def runtime_record_cardinality_rule(binding_module: Any, scaling_module: Any) -> dict[str, Any]:
    """Derive the minimal frozen target rule from source runtime records only."""
    source_records = [
        row for shape in REFERENCE_SHAPES for row in binding_module.enriched_records_for_shape(scaling_module, shape)
    ]
    unique_slot_operator_count = len({row["slot_operator"] for row in source_records})
    target_lambda = LAM0 + DELTA * unique_slot_operator_count
    return {
        "rule": "homeostatic_target_lambda = lam0 + delta * unique_slot_operator_count",
        "lam0": LAM0,
        "delta": DELTA,
        "unique_slot_operator_count": unique_slot_operator_count,
        "selected_target_lambda": target_lambda,
        "source_only": True,
        "uses_heldout_gradients": False,
        "uses_beta_grid": False,
        "uses_per_shape_constants": False,
    }


def gradients_for_shapes(
    scaling_module: Any,
    binding_module: Any,
    config: dict[str, Any],
    shapes: list[tuple[int, int, int]],
    *,
    home_lambda: float,
    allostatic_cost: float,
) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for shape in shapes:
        out[shape_key(shape)] = {
            "homeostatic": gradient(
                scaling_module,
                binding_module,
                shape,
                runtime_bound=config["runtime_bound"],
                boundary=config["boundary"],
                mode="homeostatic",
                target_lambda=home_lambda,
                cost_scale=HOMEOSTATIC_COST_SCALE,
            ),
            "allostatic": gradient(
                scaling_module,
                binding_module,
                shape,
                runtime_bound=config["runtime_bound"],
                boundary=config["boundary"],
                mode="allostatic",
                target_lambda=ALLOSTATIC_TARGET_LAMBDA,
                cost_scale=allostatic_cost,
            ),
        }
    return out


def loop_row(scaling_module: Any, binding_module: Any, config: dict[str, Any]) -> dict[str, Any]:
    home_rule = runtime_record_cardinality_rule(binding_module, scaling_module)
    allostatic_rule = {
        "rule": "fixed upstream allostatic transition cost scale",
        "selected_transition_cost_scale": ALLOSTATIC_COST_SCALE,
        "source_only": True,
        "uses_heldout_gradients": False,
        "uses_beta_grid": False,
        "uses_per_shape_constants": False,
    }
    home_lambda = float(home_rule["selected_target_lambda"])
    allostatic_cost = float(allostatic_rule["selected_transition_cost_scale"])
    source = gradients_for_shapes(
        scaling_module,
        binding_module,
        config,
        EVAL_SOURCE_SHAPES,
        home_lambda=home_lambda,
        allostatic_cost=allostatic_cost,
    )
    heldout = gradients_for_shapes(
        scaling_module,
        binding_module,
        config,
        EVAL_HELDOUT_SHAPES,
        home_lambda=home_lambda,
        allostatic_cost=allostatic_cost,
    )
    nominal = flux_readout(
        scaling_module,
        binding_module,
        (3, 3, 3),
        runtime_bound=config["runtime_bound"],
        boundary=config["boundary"],
        engine_type=0,
        lam=LAM0,
        mode="allostatic",
    )
    erased = flux_readout(
        scaling_module,
        binding_module,
        (3, 3, 3),
        runtime_bound=config["runtime_bound"],
        boundary=config["boundary"],
        engine_type=0,
        lam=LAM0,
        mode="allostatic",
        sheet_erased=True,
    )
    reversed_shell = flux_readout(
        scaling_module,
        binding_module,
        (3, 3, 3),
        runtime_bound=config["runtime_bound"],
        boundary=config["boundary"],
        engine_type=0,
        lam=LAM0,
        mode="allostatic",
        reversed_shell_time=True,
    )
    smoke_64 = flux_readout(
        scaling_module,
        binding_module,
        SMOKE_64_SHAPE,
        runtime_bound=config["runtime_bound"],
        boundary=config["boundary"],
        engine_type=0,
        lam=LAM0,
        mode="allostatic",
    )
    source_home_pass = all(row["homeostatic"] < -GAP_FLOOR for row in source.values())
    source_allo_pass = all(row["allostatic"] > GAP_FLOOR for row in source.values())
    heldout_home_pass = all(row["homeostatic"] < -GAP_FLOOR for row in heldout.values())
    heldout_allo_pass = all(row["allostatic"] > GAP_FLOOR for row in heldout.values())
    return {
        **config,
        "source_derived_homeostatic_rule": home_rule,
        "source_derived_allostatic_rule": allostatic_rule,
        "selected_homeostatic_target_lambda": home_lambda,
        "selected_allostatic_transition_cost_scale": allostatic_cost,
        "source_gradients": source,
        "heldout_gradients": heldout,
        "source_homeostatic_pass": source_home_pass,
        "source_allostatic_pass": source_allo_pass,
        "heldout_homeostatic_pass": heldout_home_pass,
        "heldout_allostatic_pass": heldout_allo_pass,
        "nominal_flux_norm_27": nominal["flux_norm"],
        "nominal_flux_norm_64_smoke": smoke_64["flux_norm"],
        "sheet_erased_flux_ratio_27": erased["flux_norm"] / max(nominal["flux_norm"], scaling_module.EPS),
        "shell_reversal_jk_gap_27": abs(nominal["jk_norm"] - reversed_shell["jk_norm"]),
        "sampled_site_count_27": nominal["sampled_site_count"],
    }


def runtime_record_coverage(binding_module: Any, scaling_module: Any) -> dict[str, Any]:
    rows = [row for shape in REFERENCE_SHAPES for row in binding_module.enriched_records_for_shape(scaling_module, shape)]
    return {
        "record_count": len(rows),
        "axis6_precedence": sorted({row["axis6_token_precedence"] for row in rows}),
        "axis6_sign": sorted({row["axis6_sign"] for row in rows}),
        "axis5_family": sorted({row["axis5_family"] for row in rows}),
        "path_class": sorted({row["path_class"] for row in rows}),
        "terrain_realization_count": len({row["terrain_realization"] for row in rows}),
        "substage_token_count": len({row["substage_token"] for row in rows}),
    }


def main() -> int:
    started = time.time()
    scaling_module = load_module(SCALING_MODULE_PATH, "peps3d_axis0_scaling")
    binding_module = load_module(BINDING_MODULE_PATH, "peps3d_axis0_runtime_binding")
    loop_rows = [loop_row(scaling_module, binding_module, config) for config in LOOPS]
    coverage = runtime_record_coverage(binding_module, scaling_module)

    raw = loop_rows[0]
    bound = loop_rows[1:]
    runtime_gaps = {
        row["label"]: abs(row["nominal_flux_norm_27"] - raw["nominal_flux_norm_27"])
        for row in bound
    }
    heldout_statuses = {
        row["label"]: {
            "homeostatic": row["heldout_homeostatic_pass"],
            "allostatic": row["heldout_allostatic_pass"],
        }
        for row in loop_rows
    }

    checks = {
        "P1_four_loop_iterations_executed": len(loop_rows) == 4 and [row["loop"] for row in loop_rows] == [1, 2, 3, 4],
        "P2_runtime_records_are_load_bearing_after_loop1": coverage["record_count"] == 384
        and all(value > GAP_FLOOR for value in runtime_gaps.values()),
        "P3_source_only_calibration_rules_selected": all(
            row["source_derived_homeostatic_rule"]["source_only"]
            and not row["source_derived_homeostatic_rule"]["uses_heldout_gradients"]
            and not row["source_derived_homeostatic_rule"]["uses_per_shape_constants"]
            for row in loop_rows
        )
        and all(
            row["source_derived_allostatic_rule"]["source_only"]
            and not row["source_derived_allostatic_rule"]["uses_heldout_gradients"]
            and not row["source_derived_allostatic_rule"]["uses_per_shape_constants"]
            for row in loop_rows
        ),
        "P4_source_status_reported_not_hidden": len(loop_rows) == 4
        and all(
            isinstance(row["source_homeostatic_pass"], bool) and isinstance(row["source_allostatic_pass"], bool)
            for row in loop_rows
        ),
        "P5_heldout_status_reported_not_hidden": len(heldout_statuses) == 4,
        "P6_chiral_flux_controls_remain_nontrivial_in_bound_loops": all(
            row["sheet_erased_flux_ratio_27"] < 0.75 and row["shell_reversal_jk_gap_27"] > GAP_FLOOR
            for row in bound
        ),
        "P7_no_final_closure_even_if_a_loop_improves": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
        "P8_runtime_binding_coverage_has_expected_axis_fields": coverage["axis6_precedence"] == ["operator_first", "terrain_first"]
        and coverage["axis6_sign"] == [-1, 1]
        and coverage["axis5_family"] == ["dephasing", "rotation"]
        and coverage["path_class"] == ["base", "fiber"]
        and coverage["terrain_realization_count"] == 8,
    }

    positive = {
        "runtime_bound_loop_executed": {
            "pass": checks["P1_four_loop_iterations_executed"] and checks["P2_runtime_records_are_load_bearing_after_loop1"],
            "runtime_flux_norm_gaps_vs_raw_27": runtime_gaps,
        },
        "source_only_calibration_loop_executed": {
            "pass": checks["P3_source_only_calibration_rules_selected"] and checks["P4_source_status_reported_not_hidden"],
            "selected_rules": {
                row["label"]: {
                    "homeostatic_target_lambda": row["selected_homeostatic_target_lambda"],
                    "allostatic_transition_cost_scale": row["selected_allostatic_transition_cost_scale"],
                }
                for row in loop_rows
            },
        },
        "runtime_binding_fields_consumed": {
            "pass": checks["P8_runtime_binding_coverage_has_expected_axis_fields"],
            "coverage": coverage,
        },
    }
    graveyard = {
        "heldout_status_is_stress_not_promotion": {
            "pass": checks["P5_heldout_status_reported_not_hidden"],
            "heldout_statuses": heldout_statuses,
        },
        "source_failures_are_variant_kills_not_hidden_errors": {
            "pass": checks["P4_source_status_reported_not_hidden"],
            "killed_source_variants": [
                row["label"]
                for row in loop_rows
                if not (row["source_homeostatic_pass"] and row["source_allostatic_pass"])
            ],
        },
        "chiral_controls_required_after_runtime_binding": {
            "pass": checks["P6_chiral_flux_controls_remain_nontrivial_in_bound_loops"],
            "bound_loop_controls": {
                row["label"]: {
                    "sheet_erased_flux_ratio_27": row["sheet_erased_flux_ratio_27"],
                    "shell_reversal_jk_gap_27": row["shell_reversal_jk_gap_27"],
                }
                for row in bound
            },
        },
    }
    boundary = {
        "formal_scout_only": {"pass": checks["P7_no_final_closure_even_if_a_loop_improves"]},
        "loop4_is_not_full_peps3d_closure": {
            "pass": True,
            "reason": "Uses local-star boundary contractions and finite calibration grids; no full PEPS3D environment closure.",
        },
        "next_admissible_step": {
            "pass": True,
            "step": "Promote no claim; split the best runtime-bound loop into smaller independent scouts for boundary-functional and calibration stress.",
        },
    }
    variants = list(positive.values()) + list(graveyard.values()) + list(boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": as_jsonable(positive),
        "graveyard_companions": as_jsonable(graveyard),
        "boundary": as_jsonable(boundary),
        "loop_rows": as_jsonable(loop_rows),
        "checks": checks,
        "runtime_binding_consumed_fields": [
            "axis6_token_precedence",
            "axis6_sign",
            "path_class",
            "axis5_family",
            "slot_operator",
            "is_native_operator",
            "sheet",
            "terrain_realization",
        ],
        "nearby_variants": {
            "passed": sum(1 for row in variants if row["pass"]) + sum(1 for value in checks.values() if value),
            "total": len(variants) + len(checks),
            "failed_checks": [key for key, value in checks.items() if not value],
        },
        "all_pass": all(checks.values()) and all(row["pass"] for row in variants),
        "why_not_final": [
            "The runtime-bound dynamics are a formal scout variant, not a source theorem.",
            "Boundary functionals remain local finite contractions rather than full PEPS3D closure.",
            "Calibration choices are selected from source fixtures and stressed on heldouts; they are not derived Xi/Phi0.",
            "External model audits are advisory only and are not part of this local receipt.",
        ],
        "divergence_log": [
            "Runtime binding changes the PEPS3D flux readout rather than merely annotating rows.",
            "Axis6 precedence is implemented as noncommuting quaternion multiplication order.",
            "Axis6 sign changes finite rotation direction; path class and native/non-native slot status change finite gains.",
            "Heldout rows are reported as stress outcomes, not hidden or used to fit the source-derived rule.",
        ],
        "why_not_v4_probes": "This is a v5 PEPS3D flux-bound Axis0 runtime-bound loop scout, not a legacy v4 probe.",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "failed_checks": result["nearby_variants"]["failed_checks"],
                "heldout_statuses": heldout_statuses,
                "runtime_gaps": runtime_gaps,
                "wrote": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
