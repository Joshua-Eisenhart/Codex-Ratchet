#!/usr/bin/env python3
"""Boundary-sampler stress for PEPS3D flux-bound Axis0 calibration.

Formal scout only.

The PEPS3D flux-bound Axis0 rows use sampled local shell-boundary
contractions. This row varies the boundary sampler without retuning F_QIT
calibration, then records whether the sign readout is sampler-sensitive.

Sampler sensitivity is evidence against treating the current row as full
PEPS3D closure. A sampler-dependent result can still be a useful scout.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch

import sim_peps3d_flux_axis0_calibration_envelope_stress_probe as calibration


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "peps3d_flux_axis0_boundary_sampler_stress_probe_results.json"

NAME = "peps3d_flux_axis0_boundary_sampler_stress_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical_peps3d_flux_axis0_boundary_sampler_stress"
SOURCE_ALIGNMENT_CATEGORY = "peps3d_flux_bound_axis0_boundary_sampler_sensitivity"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether sampled PEPS3D flux-bound Axis0 signs "
    "are stable under alternate deterministic boundary samplers. It does not "
    "admit final Axis0, Xi, Phi0, flux, PEPS3D closure, gravity, Standard "
    "Model, Yang-Mills, Riemann, or physics claims."
)

TEST_SHAPES = [(2, 2, 2), (3, 3, 3), (4, 4, 4)]
SAMPLERS = ["canonical", "all_boundary", "reverse_stride", "parity", "deterministic_hash"]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing boundary-density contractions, L/R flux readouts, and signed calibration gradients under sampler swaps",
    },
    "peps3d_flux_axis0_calibration_envelope_stress_probe": {
        "tried": True,
        "used": True,
        "reason": "supportive reuse of current calibration constants and gradient construction",
    },
    "peps3d_spinor_network_flux_axis0_scaling_probe": {
        "tried": True,
        "used": True,
        "reason": "supportive reuse of PEPS3D spinor/quaternion flux transport and local contraction functions",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "peps3d_flux_axis0_calibration_envelope_stress_probe": "supportive",
    "peps3d_spinor_network_flux_axis0_scaling_probe": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}


def as_jsonable(value: Any) -> Any:
    return calibration.as_jsonable(value)


def boundary_surface(module: Any, shape: tuple[int, int, int]) -> list[tuple[int, int, int]]:
    return [site for site in module.sites(shape) if site[0] in {0, shape[0] - 1}]


def sampler_sites(module: Any, shape: tuple[int, int, int], sampler: str) -> list[tuple[int, int, int]]:
    surface = boundary_surface(module, shape)
    if sampler == "canonical":
        return module.sampled_boundary_sites(shape)
    if sampler == "all_boundary":
        return surface
    if sampler == "reverse_stride":
        canonical_count = len(module.sampled_boundary_sites(shape))
        if canonical_count >= len(surface):
            return list(reversed(surface))
        stride = max(1, len(surface) // canonical_count)
        return list(reversed(surface))[::stride][:canonical_count]
    if sampler == "parity":
        selected = [site for site in surface if sum(site) % 2 == 0]
        return selected if selected else module.sampled_boundary_sites(shape)
    if sampler == "deterministic_hash":
        canonical_count = len(module.sampled_boundary_sites(shape))
        scored = sorted(surface, key=lambda site: ((17 * site[0] + 31 * site[1] + 43 * site[2]) % 97, site))
        return scored[:canonical_count]
    raise ValueError(sampler)


def boundary_responses_sampled(
    module: Any,
    shape: tuple[int, int, int],
    *,
    engine_type: int,
    lam: float,
    sheet: str,
    mode: str,
    sampler: str,
    sheet_erased: bool = False,
    topology_freeze: bool = False,
    reversed_shell_time: bool = False,
) -> dict[str, Any]:
    transported = module.transport_spinors(
        shape,
        engine_type=engine_type,
        lam=lam,
        sheet=sheet,
        mode=mode,
        sheet_erased=sheet_erased,
        topology_freeze=topology_freeze,
        reversed_shell_time=reversed_shell_time,
    )
    network = module.build_network(shape, transported, sheet="erased" if sheet_erased else sheet)
    selected = sampler_sites(module, shape, sampler)
    site_rhos = [module.site_rho(network, shape, site) for site in selected]
    ijk = {}
    for label, q_probe in module.IJK_PROBES.items():
        effect = module.response_effect(q_probe)
        ijk[label] = sum(module.response(rho, effect) for rho in site_rhos) / len(site_rhos)
    topology = {}
    for name, q_probe in module.TOPOLOGY_UNITS.items():
        effect = module.response_effect(module.Q_ONE + 0.70 * q_probe)
        topology[name] = sum(module.response(rho, effect) for rho in site_rhos) / len(site_rhos)
    return {"ijk": ijk, "topology": topology, "sampled_site_count": len(selected)}


def flux_readout_sampled(
    module: Any,
    shape: tuple[int, int, int],
    *,
    engine_type: int,
    lam: float,
    mode: str,
    sampler: str,
    sheet_erased: bool = False,
    topology_freeze: bool = False,
    reversed_shell_time: bool = False,
) -> dict[str, Any]:
    left = boundary_responses_sampled(
        module,
        shape,
        engine_type=engine_type,
        lam=lam,
        sheet="L",
        mode=mode,
        sampler=sampler,
        sheet_erased=sheet_erased,
        topology_freeze=topology_freeze,
        reversed_shell_time=reversed_shell_time,
    )
    right = boundary_responses_sampled(
        module,
        shape,
        engine_type=engine_type,
        lam=lam,
        sheet="R",
        mode=mode,
        sampler=sampler,
        sheet_erased=sheet_erased,
        topology_freeze=topology_freeze,
        reversed_shell_time=reversed_shell_time,
    )
    flux = {label: right["ijk"][label] - left["ijk"][label] for label in ["i", "j", "k"]}
    topology_delta = {name: right["topology"][name] - left["topology"][name] for name in module.TOPOLOGIES}
    flux_tensor = torch.tensor([flux["i"], flux["j"], flux["k"]], dtype=module.RTYPE)
    topology_tensor = torch.tensor([abs(topology_delta[name]) for name in module.TOPOLOGIES], dtype=module.RTYPE)
    branch_probs = topology_tensor + 0.05 * torch.abs(flux_tensor.mean()) + module.EPS
    branch_probs = branch_probs / torch.clamp(torch.sum(branch_probs), min=module.EPS)
    return {
        "flux_components": flux,
        "flux_norm": float(torch.linalg.vector_norm(flux_tensor).item()),
        "jk_norm": float(torch.linalg.vector_norm(flux_tensor[1:]).item()),
        "topology_delta": topology_delta,
        "topology_mutation_norm": float(torch.linalg.vector_norm(topology_tensor).item()),
        "branch_entropy": module.entropy_from_probs(branch_probs),
        "branch_probs": branch_probs,
        "sampled_site_count": left["sampled_site_count"],
    }


def finite_fep_sampled(
    module: Any,
    shape: tuple[int, int, int],
    *,
    engine_type: int,
    lam: float,
    mode: str,
    sampler: str,
    target_probs: torch.Tensor,
    target_flux: torch.Tensor,
) -> float:
    row = flux_readout_sampled(module, shape, engine_type=engine_type, lam=lam, mode=mode, sampler=sampler)
    flux = torch.tensor([row["flux_components"]["i"], row["flux_components"]["j"], row["flux_components"]["k"]], dtype=module.RTYPE)
    flux_probs = torch.abs(flux) + module.EPS
    flux_probs = flux_probs / torch.clamp(torch.sum(flux_probs), min=module.EPS)
    recovery_error = module.kl_probs(flux_probs, target_probs)
    recovery_gap = float(torch.linalg.vector_norm(flux - target_flux).item())
    compression_gain = math.log(4.0) - row["branch_entropy"]
    cost_scale = 0.06 if mode == "homeostatic" else module.ALLOSTATIC_TRANSITION_COST_SCALE if mode == "allostatic" else 0.0
    transition_cost = cost_scale * lam * lam * (1.0 + row["topology_mutation_norm"])
    recovery_gain = math.exp(-recovery_gap)
    return recovery_error + row["branch_entropy"] + transition_cost - compression_gain - recovery_gain


def gradient_sampled(module: Any, shape: tuple[int, int, int], mode: str, sampler: str) -> float:
    target_lambda = module.HOMEOSTATIC_TARGET_LAMBDA if mode == "homeostatic" else 0.0
    target = flux_readout_sampled(module, shape, engine_type=0, lam=target_lambda, mode=mode, sampler=sampler)
    target_flux = torch.tensor([target["flux_components"]["i"], target["flux_components"]["j"], target["flux_components"]["k"]], dtype=module.RTYPE)
    target_probs = torch.abs(target_flux) + module.EPS
    if float(torch.sum(target_probs).item()) < 10.0 * module.EPS:
        target_probs = torch.ones(3, dtype=module.RTYPE)
    target_probs = target_probs / torch.clamp(torch.sum(target_probs), min=module.EPS)
    values = [
        finite_fep_sampled(
            module,
            shape,
            engine_type=0,
            lam=lam,
            mode=mode,
            sampler=sampler,
            target_probs=target_probs,
            target_flux=target_flux,
        )
        for lam in [0.14, 0.22]
    ]
    return (values[1] - values[0]) / 0.08


def main() -> int:
    started = time.time()
    module = calibration.load_scaling_module()
    rows: list[dict[str, Any]] = []
    for shape in TEST_SHAPES:
        for sampler in SAMPLERS:
            home = gradient_sampled(module, shape, "homeostatic", sampler)
            allo = gradient_sampled(module, shape, "allostatic", sampler)
            nominal = flux_readout_sampled(module, shape, engine_type=0, lam=0.18, mode="allostatic", sampler=sampler)
            erased = flux_readout_sampled(
                module,
                shape,
                engine_type=0,
                lam=0.18,
                mode="allostatic",
                sampler=sampler,
                sheet_erased=True,
            )
            rows.append(
                {
                    "shape": shape,
                    "site_count": math.prod(shape),
                    "sampler": sampler,
                    "sampled_site_count": nominal["sampled_site_count"],
                    "homeostatic_gradient": home,
                    "allostatic_gradient": allo,
                    "homeostatic_pass": home < -module.GAP_FLOOR,
                    "allostatic_pass": allo > module.GAP_FLOOR,
                    "flux_norm": nominal["flux_norm"],
                    "flux_present": nominal["flux_norm"] > module.GAP_FLOOR,
                    "sheet_erased_flux_ratio": erased["flux_norm"] / max(nominal["flux_norm"], module.EPS),
                    "sheet_erasure_collapses": erased["flux_norm"] / max(nominal["flux_norm"], module.EPS) < 0.35,
                }
            )
    failures = [
        f"{row['site_count']}:{row['sampler']}:{kind}"
        for row in rows
        for kind, ok in [("home", row["homeostatic_pass"]), ("allo", row["allostatic_pass"])]
        if not ok
    ]
    sampler_sensitive = len(failures) > 0
    positive = {
        "boundary_sampler_grid_executed": {
            "pass": len(rows) == len(TEST_SHAPES) * len(SAMPLERS),
            "samplers": SAMPLERS,
            "shapes": TEST_SHAPES,
        },
        "flux_witness_present_under_all_samplers": {
            "pass": all(row["flux_present"] for row in rows),
            "flux_norms": {f"{row['site_count']}:{row['sampler']}": row["flux_norm"] for row in rows},
        },
        "sheet_erasure_control_remains_live": {
            "pass": all(row["sheet_erasure_collapses"] for row in rows),
            "ratios": {f"{row['site_count']}:{row['sampler']}": row["sheet_erased_flux_ratio"] for row in rows},
        },
    }
    graveyard = {
        "sampler_invariant_axis0_sign_claim_killed_if_any_fail": {
            "pass": sampler_sensitive,
            "failed_sign_cells": failures,
            "meaning": "At least one alternate boundary sampler changes a required sign, so sampled-boundary closure is not full closure.",
        },
        "canonical_sampler_not_full_environment": {
            "pass": True,
            "canonical_is_one_sampler": True,
            "full_environment_closure": False,
        },
    }
    boundary = {
        "formal_scout_only": {"pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False},
        "sampler_stress_not_axis0_theorem": {"pass": True, "promotion_allowed": PROMOTION_ALLOWED},
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
        "sampler_rows": as_jsonable(rows),
        "stress_outcome": {
            "sampler_sensitive": sampler_sensitive,
            "failed_sign_cells": failures,
            "status": "sampler_sensitive_formal_scout" if sampler_sensitive else "no_sampler_sign_failure_on_grid",
        },
        "nearby_variants": {
            "passed": sum(1 for row in variants if row["pass"]),
            "total": len(variants),
            "failed": [key for section in (positive, graveyard, boundary) for key, row in section.items() if not row["pass"]],
        },
        "all_pass": all(row["pass"] for row in variants),
        "why_not_final": [
            "Boundary sampler changes are still sampled local contractions, not full PEPS3D closure.",
            "Sampler sensitivity blocks treating canonical sampling as environment-independent.",
            "This row does not derive Xi/Phi0, final Axis0, final flux, or physics.",
        ],
        "divergence_log": [
            "Alternate boundary samplers are required graveyard controls.",
            "Flux presence and sheet erasure are separated from F_QIT sign stability.",
        ],
        "why_not_v4_probes": "This is a v5 PEPS3D flux-bound Axis0 boundary-sampler stress scout, not a legacy v4 probe.",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "sampler_sensitive": sampler_sensitive, "failed_sign_cells": failures}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
