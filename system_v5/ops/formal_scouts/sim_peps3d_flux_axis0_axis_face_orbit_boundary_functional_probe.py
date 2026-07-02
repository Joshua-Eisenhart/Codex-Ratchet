#!/usr/bin/env python3
"""Axis/face boundary functional scout for PEPS3D flux-bound Axis0.

Formal scout only.

The prior boundary rows separated x-face sampling from all-x-boundary surface
averaging. This row tests coordinate-carrier face instruments: compare the
three axis-pair face means and the equal six-face boundary mean while consuming
the enriched runtime records in the PEPS3D spinor/quaternion dynamics.

The x/y/z face coordinates are PEPS3D carrier adapters, not root geometry.
The six-face mean is not called an invariant group orbit here; no orbit action
is defined or proven by this row.

The row is intentionally a blocker/hardening receipt. A better face functional
is still a local finite boundary contraction, not full PEPS3D closure.
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
OUT_PATH = RESULT_DIR / "peps3d_flux_axis0_axis_face_orbit_boundary_functional_probe_results.json"
LOOP4_MODULE_PATH = ROOT / "sim_peps3d_flux_axis0_runtime_bound_loop4_probe.py"

NAME = "peps3d_flux_axis0_axis_face_orbit_boundary_functional_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical_peps3d_flux_axis0_axis_face_boundary_functional"
SOURCE_ALIGNMENT_CATEGORY = "peps3d_flux_bound_axis0_axis_face_boundary_functional_control"
PROMOTION_ALLOWED = False
ADMISSION_STATUS = "blocked"
EXPECTED_NONPROMOTION = True
CLAIM_CEILING = (
    "Formal scout only: tests coordinate-carrier axis-pair and six-face equal "
    "boundary-mean functionals for runtime-bound PEPS3D flux-bound Axis0. "
    "These x/y/z faces are adapter/control surfaces, not root geometry, and "
    "no orbit action or sampler invariant is proven. It does not admit final "
    "Axis0, final flux, Xi, Phi0, full PEPS3D closure, gravity, Standard "
    "Model, Yang-Mills, Riemann, or physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing quaternionic spinor boundary contractions, six-face boundary aggregation, and sign/margin checks",
    },
    "peps3d_flux_axis0_runtime_bound_loop4_probe": {
        "tried": True,
        "used": True,
        "reason": "load-bearing consumed receipt/module supplying runtime-bound transport, calibration constants, gradient conventions, and PEPS3D scaling loader",
    },
    "peps3d_spinor_network_flux_axis0_scaling_probe": {
        "tried": True,
        "used": True,
        "reason": "load-bearing consumed receipt/module supplying PEPS3D spinor/quaternion substrate functions through the loop4 module",
    },
    "peps3d_flux_axis0_runtime_record_binding_gate_probe": {
        "tried": True,
        "used": True,
        "reason": "load-bearing consumed receipt/module supplying enriched runtime records consumed by the loop4 transport",
    },
    "python_importlib": {"tried": True, "used": True, "reason": "supportive local module loading"},
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "peps3d_flux_axis0_runtime_bound_loop4_probe": "load_bearing",
    "peps3d_spinor_network_flux_axis0_scaling_probe": "load_bearing",
    "peps3d_flux_axis0_runtime_record_binding_gate_probe": "load_bearing",
    "python_importlib": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

SOURCE_SHAPES = [(2, 2, 2), (3, 3, 3)]
HELDOUT_SHAPES = [(2, 3, 4), (3, 3, 4)]
FUNCTIONALS = ["x_pair_mean", "y_pair_mean", "z_pair_mean", "six_face_equal_boundary_mean"]
AXIS_LABELS = {0: "x", 1: "y", 2: "z"}
GAP_FLOOR = 1.0e-5
BOUNDARY_FUNCTIONAL_DOCTRINE = {
    "coordinate_face_axes_are_carrier_adapters": True,
    "root_geometry_claim": False,
    "orbit_action_defined": False,
    "six_face_mean_is_group_orbit": False,
    "boundary_functional_label": "six_face_equal_boundary_mean",
}


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


def axis_face_groups(
    scaling_module: Any,
    shape: tuple[int, int, int],
    functional: str,
) -> list[dict[str, Any]]:
    if functional == "six_face_equal_boundary_mean":
        axes = [0, 1, 2]
    elif functional.endswith("_pair_mean") and functional[0] in {"x", "y", "z"}:
        axes = [{"x": 0, "y": 1, "z": 2}[functional[0]]]
    else:
        raise ValueError(functional)

    all_sites = scaling_module.sites(shape)
    groups: list[dict[str, Any]] = []
    for axis in axes:
        for side, coord in [("min", 0), ("max", shape[axis] - 1)]:
            sites = [site for site in all_sites if site[axis] == coord]
            groups.append(
                {
                    "axis": AXIS_LABELS[axis],
                    "side": side,
                    "site_count": len(sites),
                    "sites": sites,
                }
            )
    return groups


def group_mean_response(scaling_module: Any, site_rhos: list[torch.Tensor], q_probe: torch.Tensor) -> float:
    effect = scaling_module.response_effect(q_probe)
    values = torch.tensor([scaling_module.response(rho, effect) for rho in site_rhos], dtype=scaling_module.RTYPE)
    return float(torch.mean(values).item())


def boundary_responses_face_orbit(
    loop4: Any,
    scaling_module: Any,
    binding_module: Any,
    shape: tuple[int, int, int],
    *,
    engine_type: int,
    lam: float,
    sheet: str,
    mode: str,
    functional: str,
    sheet_erased: bool = False,
    topology_freeze: bool = False,
    reversed_shell_time: bool = False,
) -> dict[str, Any]:
    transported = loop4.transport_runtime_bound(
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
    groups = axis_face_groups(scaling_module, shape, functional)

    ijk_values = {label: [] for label in ["i", "j", "k"]}
    topology_values = {name: [] for name in scaling_module.TOPOLOGIES}
    for group in groups:
        site_rhos = [scaling_module.site_rho(network, shape, site) for site in group["sites"]]
        for label, q_probe in scaling_module.IJK_PROBES.items():
            ijk_values[label].append(group_mean_response(scaling_module, site_rhos, q_probe))
        for name, q_probe in scaling_module.TOPOLOGY_UNITS.items():
            topology_values[name].append(
                group_mean_response(scaling_module, site_rhos, scaling_module.Q_ONE + 0.70 * q_probe)
            )

    ijk = {label: float(torch.mean(torch.tensor(vals, dtype=scaling_module.RTYPE)).item()) for label, vals in ijk_values.items()}
    topology = {
        name: float(torch.mean(torch.tensor(vals, dtype=scaling_module.RTYPE)).item())
        for name, vals in topology_values.items()
    }
    unique_sites = sorted({site for group in groups for site in group["sites"]})
    return {
        "ijk": ijk,
        "topology": topology,
        "face_group_count": len(groups),
        "unique_site_count": len(unique_sites),
        "face_site_counts": [group["site_count"] for group in groups],
    }


def flux_readout_face_orbit(
    loop4: Any,
    scaling_module: Any,
    binding_module: Any,
    shape: tuple[int, int, int],
    *,
    engine_type: int,
    lam: float,
    mode: str,
    functional: str,
    sheet_erased: bool = False,
    topology_freeze: bool = False,
    reversed_shell_time: bool = False,
) -> dict[str, Any]:
    left = boundary_responses_face_orbit(
        loop4,
        scaling_module,
        binding_module,
        shape,
        engine_type=engine_type,
        lam=lam,
        sheet="L",
        mode=mode,
        functional=functional,
        sheet_erased=sheet_erased,
        topology_freeze=topology_freeze,
        reversed_shell_time=reversed_shell_time,
    )
    right = boundary_responses_face_orbit(
        loop4,
        scaling_module,
        binding_module,
        shape,
        engine_type=engine_type,
        lam=lam,
        sheet="R",
        mode=mode,
        functional=functional,
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
        "face_group_count": left["face_group_count"],
        "unique_site_count": left["unique_site_count"],
        "face_site_counts": left["face_site_counts"],
    }


def finite_fep_face_orbit(
    loop4: Any,
    scaling_module: Any,
    binding_module: Any,
    shape: tuple[int, int, int],
    *,
    engine_type: int,
    lam: float,
    mode: str,
    functional: str,
    target_probs: torch.Tensor,
    target_flux: torch.Tensor,
    cost_scale: float,
) -> float:
    row = flux_readout_face_orbit(
        loop4,
        scaling_module,
        binding_module,
        shape,
        engine_type=engine_type,
        lam=lam,
        mode=mode,
        functional=functional,
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


def gradient_face_orbit(
    loop4: Any,
    scaling_module: Any,
    binding_module: Any,
    shape: tuple[int, int, int],
    *,
    mode: str,
    functional: str,
    target_lambda: float,
    cost_scale: float,
) -> float:
    target = flux_readout_face_orbit(
        loop4,
        scaling_module,
        binding_module,
        shape,
        engine_type=0,
        lam=target_lambda,
        mode=mode,
        functional=functional,
    )
    target_flux = torch.tensor(
        [target["flux_components"]["i"], target["flux_components"]["j"], target["flux_components"]["k"]],
        dtype=scaling_module.RTYPE,
    )
    target_probs = torch.abs(target_flux) + scaling_module.EPS
    if float(torch.sum(target_probs).item()) < 10.0 * scaling_module.EPS:
        target_probs = torch.ones(3, dtype=scaling_module.RTYPE)
    target_probs = target_probs / torch.clamp(torch.sum(target_probs), min=scaling_module.EPS)
    low = finite_fep_face_orbit(
        loop4,
        scaling_module,
        binding_module,
        shape,
        engine_type=0,
        lam=loop4.LAM0 - loop4.DELTA,
        mode=mode,
        functional=functional,
        target_probs=target_probs,
        target_flux=target_flux,
        cost_scale=cost_scale,
    )
    high = finite_fep_face_orbit(
        loop4,
        scaling_module,
        binding_module,
        shape,
        engine_type=0,
        lam=loop4.LAM0 + loop4.DELTA,
        mode=mode,
        functional=functional,
        target_probs=target_probs,
        target_flux=target_flux,
        cost_scale=cost_scale,
    )
    return (high - low) / (2.0 * loop4.DELTA)


def gradients_for_functional(
    loop4: Any,
    scaling_module: Any,
    binding_module: Any,
    functional: str,
    shapes: list[tuple[int, int, int]],
    home_lambda: float,
) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for shape in shapes:
        out[shape_key(shape)] = {
            "homeostatic": gradient_face_orbit(
                loop4,
                scaling_module,
                binding_module,
                shape,
                mode="homeostatic",
                functional=functional,
                target_lambda=home_lambda,
                cost_scale=loop4.HOMEOSTATIC_COST_SCALE,
            ),
            "allostatic": gradient_face_orbit(
                loop4,
                scaling_module,
                binding_module,
                shape,
                mode="allostatic",
                functional=functional,
                target_lambda=loop4.ALLOSTATIC_TARGET_LAMBDA,
                cost_scale=loop4.ALLOSTATIC_COST_SCALE,
            ),
        }
    return out


def sign_status(rows: dict[str, dict[str, float]]) -> dict[str, Any]:
    home = {key: row["homeostatic"] < -GAP_FLOOR for key, row in rows.items()}
    allo = {key: row["allostatic"] > GAP_FLOOR for key, row in rows.items()}
    return {
        "homeostatic_pass": all(home.values()),
        "allostatic_pass": all(allo.values()),
        "homeostatic_by_shape": home,
        "allostatic_by_shape": allo,
    }


def main() -> int:
    started = time.time()
    loop4 = load_module(LOOP4_MODULE_PATH, "peps3d_axis0_runtime_bound_loop4")
    scaling_module = loop4.load_module(loop4.SCALING_MODULE_PATH, "peps3d_axis0_scaling")
    binding_module = loop4.load_module(loop4.BINDING_MODULE_PATH, "peps3d_axis0_runtime_binding")
    home_rule = loop4.runtime_record_cardinality_rule(binding_module, scaling_module)
    home_lambda = float(home_rule["selected_target_lambda"])

    functional_rows: dict[str, Any] = {}
    for functional in FUNCTIONALS:
        source = gradients_for_functional(loop4, scaling_module, binding_module, functional, SOURCE_SHAPES, home_lambda)
        heldout = gradients_for_functional(loop4, scaling_module, binding_module, functional, HELDOUT_SHAPES, home_lambda)
        nominal = flux_readout_face_orbit(
            loop4,
            scaling_module,
            binding_module,
            (3, 3, 3),
            engine_type=0,
            lam=loop4.LAM0,
            mode="allostatic",
            functional=functional,
        )
        erased = flux_readout_face_orbit(
            loop4,
            scaling_module,
            binding_module,
            (3, 3, 3),
            engine_type=0,
            lam=loop4.LAM0,
            mode="allostatic",
            functional=functional,
            sheet_erased=True,
        )
        reversed_shell = flux_readout_face_orbit(
            loop4,
            scaling_module,
            binding_module,
            (3, 3, 3),
            engine_type=0,
            lam=loop4.LAM0,
            mode="allostatic",
            functional=functional,
            reversed_shell_time=True,
        )
        functional_rows[functional] = {
            "source_gradients": source,
            "heldout_gradients": heldout,
            "source_status": sign_status(source),
            "heldout_status": sign_status(heldout),
            "nominal_flux_norm_27": nominal["flux_norm"],
            "sheet_erased_flux_ratio_27": erased["flux_norm"] / max(nominal["flux_norm"], scaling_module.EPS),
            "shell_reversal_jk_gap_27": abs(nominal["jk_norm"] - reversed_shell["jk_norm"]),
            "face_group_count_27": nominal["face_group_count"],
            "unique_site_count_27": nominal["unique_site_count"],
            "face_site_counts_27": nominal["face_site_counts"],
        }

    source_axis_spreads: dict[str, dict[str, float]] = {}
    for shape in SOURCE_SHAPES:
        key = shape_key(shape)
        home_values = [functional_rows[f"{axis}_pair_mean"]["source_gradients"][key]["homeostatic"] for axis in ["x", "y", "z"]]
        allo_values = [functional_rows[f"{axis}_pair_mean"]["source_gradients"][key]["allostatic"] for axis in ["x", "y", "z"]]
        source_axis_spreads[key] = {
            "homeostatic_spread": max(home_values) - min(home_values),
            "allostatic_spread": max(allo_values) - min(allo_values),
        }

    six_face_mean = functional_rows["six_face_equal_boundary_mean"]
    all_functionals_have_chiral_controls = all(
        row["sheet_erased_flux_ratio_27"] < 0.75 and row["shell_reversal_jk_gap_27"] > GAP_FLOOR
        for row in functional_rows.values()
    )
    any_axis_pair_spread = any(
        spread["homeostatic_spread"] > GAP_FLOOR or spread["allostatic_spread"] > GAP_FLOOR
        for spread in source_axis_spreads.values()
    )
    six_face_mean_local_not_closure = (
        six_face_mean["face_group_count_27"] == 6
        and CLASSIFICATION == "formal_scout"
        and PROMOTION_ALLOWED is False
    )

    checks = {
        "P1_axis_face_functional_grid_executed": set(functional_rows) == set(FUNCTIONALS),
        "P2_six_face_mean_uses_six_faces": six_face_mean["face_group_count_27"] == 6,
        "P3_axis_pair_dependence_is_measured": any_axis_pair_spread,
        "P4_source_and_heldout_status_reported": all(
            "source_status" in row and "heldout_status" in row for row in functional_rows.values()
        ),
        "P5_chiral_controls_remain_nontrivial": all_functionals_have_chiral_controls,
        "P6_source_only_runtime_cardinality_rule_reused": home_rule["source_only"]
        and not home_rule["uses_heldout_gradients"]
        and not home_rule["uses_per_shape_constants"],
        "P7_six_face_mean_not_promoted_to_closure": six_face_mean_local_not_closure,
        "P8_nonpromotion_boundary_intact": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
    }

    positive = {
        "axis_face_boundary_grid_executed": {
            "pass": checks["P1_axis_face_functional_grid_executed"] and checks["P2_six_face_mean_uses_six_faces"],
            "functionals": FUNCTIONALS,
            "source_shapes": [shape_key(shape) for shape in SOURCE_SHAPES],
            "heldout_shapes": [shape_key(shape) for shape in HELDOUT_SHAPES],
            "boundary_functional_doctrine": BOUNDARY_FUNCTIONAL_DOCTRINE,
        },
        "runtime_cardinality_rule_reused_without_refit": {
            "pass": checks["P6_source_only_runtime_cardinality_rule_reused"],
            "rule": home_rule,
        },
        "chiral_controls_survive_six_face_mean": {
            "pass": checks["P5_chiral_controls_remain_nontrivial"],
            "sheet_erased_ratios": {
                key: row["sheet_erased_flux_ratio_27"] for key, row in functional_rows.items()
            },
            "shell_reversal_jk_gaps": {
                key: row["shell_reversal_jk_gap_27"] for key, row in functional_rows.items()
            },
        },
    }
    graveyard = {
        "axis_pair_dependence_blocks_axis_agnostic_boundary_claim": {
            "pass": checks["P3_axis_pair_dependence_is_measured"],
            "source_axis_spreads": source_axis_spreads,
        },
        "six_face_mean_is_local_boundary_functional_not_full_peps3d_closure": {
            "pass": checks["P7_six_face_mean_not_promoted_to_closure"],
            "six_face_mean_status": six_face_mean["heldout_status"],
            "why_blocked": "Equal six-face boundary averaging is still a finite local boundary contraction; no orbit action is defined.",
        },
    }
    boundary = {
        "formal_scout_only": {"pass": checks["P8_nonpromotion_boundary_intact"]},
        "admission_status_blocked": {
            "pass": ADMISSION_STATUS == "blocked" and EXPECTED_NONPROMOTION is True,
            "admission_status": ADMISSION_STATUS,
            "expected_nonpromotion": EXPECTED_NONPROMOTION,
        },
        "coordinate_faces_are_adapter_instruments": {
            "pass": BOUNDARY_FUNCTIONAL_DOCTRINE["coordinate_face_axes_are_carrier_adapters"]
            and not BOUNDARY_FUNCTIONAL_DOCTRINE["root_geometry_claim"],
            "doctrine": BOUNDARY_FUNCTIONAL_DOCTRINE,
        },
        "next_admissible_step": {
            "pass": True,
            "step": "Use these axis/face rows as source data for a no-refit boundary functional rule; do not promote sampler invariance.",
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
        "admission_status": ADMISSION_STATUS,
        "expected_nonpromotion": EXPECTED_NONPROMOTION,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "CONSUMED_RECEIPT_DEPTH": {
            "peps3d_flux_axis0_runtime_bound_loop4_probe": "load_bearing",
            "peps3d_spinor_network_flux_axis0_scaling_probe": "load_bearing",
            "peps3d_flux_axis0_runtime_record_binding_gate_probe": "load_bearing",
        },
        "boundary_functional_doctrine": BOUNDARY_FUNCTIONAL_DOCTRINE,
        "positive": as_jsonable(positive),
        "graveyard_companions": as_jsonable(graveyard),
        "boundary": as_jsonable(boundary),
        "functional_rows": as_jsonable(functional_rows),
        "checks": checks,
        "nearby_variants": {
            "passed": sum(1 for row in variants if row["pass"]) + sum(1 for value in checks.values() if value),
            "total": len(variants) + len(checks),
            "failed_checks": [key for key, value in checks.items() if not value],
        },
        "all_pass": all(checks.values()) and all(row["pass"] for row in variants),
        "why_not_final": [
            "Six-face equal boundary averaging is still local finite boundary contraction, not full PEPS3D environment closure.",
            "Coordinate x/y/z face functionals are PEPS3D carrier instruments, not root geometry.",
            "No group orbit, gauge orbit, or manifold orbit action is defined or proven by this row.",
            "Axis-pair dependence remains visible; no axis-agnostic boundary theorem is admitted.",
            "The runtime-cardinality calibration rule is reused without heldout refit but is still not Xi/Phi0.",
        ],
        "divergence_log": [
            "The row compares coordinate-carrier x/y/z pair means and six-face equal boundary mean instead of assuming the original x-boundary sampler.",
            "Axis-pair spread is treated as a blocker for axis-agnostic sampler claims, not as a defect to hide.",
        ],
        "why_not_v4_probes": "This is a v5 PEPS3D flux-bound Axis0 boundary-functional scout, not a legacy v4 probe.",
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
                "six_face_mean_heldout_status": six_face_mean["heldout_status"],
                "axis_spreads": source_axis_spreads,
                "wrote": str(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
