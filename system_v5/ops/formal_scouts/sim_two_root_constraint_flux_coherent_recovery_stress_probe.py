#!/usr/bin/env python3
"""Stress test for the flux-coherent recovery Phi0 candidate.

Formal scout only. The first-rung flux-coherent recovery candidate separated in
a single bounded fixture. This scout tests whether that separation survives a
broader deterministic finite sweep over source/cut parameters, nearby runtime
schedule variants, and carrier-erasing controls.

Candidate under stress:

    E_coh(f) = Phi_Petz(rho_f) - Phi_Petz(Delta_C(rho_f))
    W(f) = E_coh(f) * max(I(A:C|B)_f - I(B:C|A)_f, 0)
    Phi_flux_coh = W(+flux) - W(-flux)

The result is still not a final Xi/Phi0 admission. Passing this scout only
upgrades the candidate from single-fixture first rung to bounded stress-survived
formal evidence.
"""

from __future__ import annotations

import itertools
import json
import math
import pathlib
import time
from typing import Any

import torch
import z3

from sim_two_root_constraint_petz_recovery_phi0_candidate_probe import (
    as_jsonable,
    petz_recover_b_to_bc,
)
from sim_two_root_constraint_quantum_conditional_information_phi0_candidate_probe import (
    CDTYPE,
    I2,
    I4,
    X,
    Z,
    amplitude_down,
    amplitude_up,
    conditional_mutual_information,
    dephase,
    dephase_ab,
    dephase_register_c,
    density,
    erase_register_c,
    negativity_ab,
    normalize_vec,
    spinor,
    unitary,
    zz_entangler,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "two_root_constraint_flux_coherent_recovery_stress_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "flux_coherent_recovery_stress"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: stress-tests the finite flux-coherent recovery Phi0 "
    "candidate across deterministic parameter rows and controls. It does not "
    "admit final Xi, final Phi0, final Axis0, full FEP, Markov blanket "
    "ontology, holography, ER=EPR, or physics."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing deterministic complex-density stress rows, coherent "
            "history registers, Petz recovery, flux-differential readouts, and controls"
        ),
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive nonpromotion and completion fence for stress classification",
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


def stress_parameters() -> list[dict[str, float]]:
    rows = []
    for idx in range(8):
        rows.append(
            {
                "a_phi": 0.12 + 0.07 * idx,
                "a_chi": -0.31 + 0.05 * idx,
                "a_eta": 0.46 + 0.021 * (idx % 4),
                "b_phi": -0.24 + 0.041 * idx,
                "b_chi": 0.39 - 0.033 * idx,
                "b_eta": 0.62 + 0.018 * ((idx + 1) % 4),
                "ent": 0.74 + 0.035 * idx,
                "rz1": 0.23 + 0.017 * idx,
                "q1": 0.13 + 0.008 * (idx % 5),
                "rx2": -0.19 - 0.013 * idx,
                "rz2": -0.18 - 0.011 * idx,
                "q2": 0.09 + 0.006 * (idx % 4),
                "gamma": 0.12 + 0.01 * (idx % 5),
            }
        )
    return rows


def initial_cut_vector(params: dict[str, float], *, entangled: bool) -> torch.Tensor:
    psi_a = spinor(params["a_phi"], params["a_chi"], params["a_eta"])
    psi_b = spinor(params["b_phi"], params["b_chi"], params["b_eta"])
    psi = torch.kron(psi_a, psi_b)
    if entangled:
        psi = zz_entangler(params["ent"]) @ psi
    return normalize_vec(psi)


def instruments(
    params: dict[str, float],
    flux: int,
    *,
    commuting: bool,
    reversed_order: bool,
    row_variant: str,
) -> list[list[torch.Tensor]]:
    if commuting:
        rows = [
            [unitary(Z, flux * params["rz1"])],
            dephase(Z, params["q1"]),
            [unitary(Z, flux * params["rz2"])],
            dephase(Z, params["q2"]),
        ]
    else:
        rows = [
            [unitary(Z, flux * params["rz1"])],
            dephase(X, params["q1"]),
            [unitary(X, flux * params["rx2"])],
            amplitude_down(params["gamma"]) if flux > 0 else amplitude_up(params["gamma"]),
        ]
    if row_variant == "dephase_last":
        rows[-1] = dephase(X if not commuting else Z, min(0.28, params["q2"] + 0.04))
    elif row_variant == "rot_swap" and not commuting:
        rows[0] = [unitary(X, flux * params["rx2"])]
        rows[2] = [unitary(Z, flux * params["rz1"])]
    elif row_variant != "canonical":
        raise ValueError(f"unknown row_variant: {row_variant}")
    return list(reversed(rows)) if reversed_order else rows


def coherent_history_state_parametric(
    params: dict[str, float],
    *,
    entangled: bool = True,
    commuting: bool = False,
    reversed_order: bool = False,
    flux: int = 1,
    collapse_register: bool = False,
    row_variant: str = "canonical",
) -> tuple[torch.Tensor, list[int], dict[str, Any]]:
    psi0 = initial_cut_vector(params, entangled=entangled)
    rows = instruments(params, flux, commuting=commuting, reversed_order=reversed_order, row_variant=row_variant)
    branch_vectors = []
    branch_probs = []
    for outcomes in itertools.product(*[range(len(row)) for row in rows]):
        k = I2
        for stage, outcome in zip(rows, outcomes):
            k = stage[outcome] @ k
        vec_ab = torch.kron(k, I2) @ psi0
        branch_vectors.append(vec_ab)
        branch_probs.append(float(torch.linalg.vector_norm(vec_ab).square().real.item()))

    if collapse_register:
        vec = normalize_vec(sum(branch_vectors))
        rho = density(vec).reshape(4, 1, 4, 1).reshape(4, 4)
        return rho, [2, 2, 1], {"branch_count": len(branch_vectors), "branch_probs": branch_probs}

    dim_c = len(branch_vectors)
    full = torch.zeros((4 * dim_c,), dtype=CDTYPE)
    for c_idx, vec_ab in enumerate(branch_vectors):
        for ab_idx in range(4):
            full[ab_idx * dim_c + c_idx] = vec_ab[ab_idx]
    full = normalize_vec(full)
    return density(full), [2, 2, dim_c], {"branch_count": dim_c, "branch_probs": branch_probs}


def transform_history(rho: torch.Tensor, dims: list[int], transform: str) -> torch.Tensor:
    if transform == "canonical":
        return rho
    if transform == "dephase_history":
        return dephase_register_c(rho, dims[2])
    if transform == "erase_history":
        return erase_register_c(rho, dims)
    if transform == "classical_ab":
        return dephase_ab(rho, dims[2])
    raise ValueError(f"unknown transform: {transform}")


def petz_metrics(rho: torch.Tensor, dims: list[int]) -> dict[str, float]:
    recovered = petz_recover_b_to_bc(rho, dims)
    defect = float(torch.linalg.matrix_norm(rho - recovered).real.item())
    neg = negativity_ab(rho, dims)
    qci_a_given_b = max(0.0, conditional_mutual_information(rho, dims, middle=1))
    qci_b_given_a = max(0.0, conditional_mutual_information(rho, dims, middle=0))
    return {
        "petz_defect_fro": defect,
        "negativity_AB": neg,
        "I_A_C_given_B": qci_a_given_b,
        "I_B_C_given_A": qci_b_given_a,
        "directional_qci_gap": qci_a_given_b - qci_b_given_a,
        "Phi_Petz": defect * neg,
    }


def evaluate_side(params: dict[str, float], flux: int, transform: str = "canonical", **kwargs: Any) -> dict[str, Any]:
    rho, dims, meta = coherent_history_state_parametric(params, flux=flux, **kwargs)
    rho = transform_history(rho, dims, transform)
    raw = petz_metrics(rho, dims)
    dephased = petz_metrics(dephase_register_c(rho, dims[2]), dims)
    coherent_excess = raw["Phi_Petz"] - dephased["Phi_Petz"]
    weighted_excess = coherent_excess * max(raw["directional_qci_gap"], 0.0)
    return {
        "dims": dims,
        "branch_count": meta["branch_count"],
        "branch_probability_total": sum(meta["branch_probs"]),
        "raw": raw,
        "dephased_baseline": dephased,
        "coherent_recovery_excess": coherent_excess,
        "weighted_coherent_recovery_excess": weighted_excess,
    }


def candidate_value(
    params: dict[str, float],
    transform: str = "canonical",
    flux_erased: bool = False,
    **kwargs: Any,
) -> dict[str, Any]:
    plus = evaluate_side(params, 1, transform=transform, **kwargs)
    minus_flux = 1 if flux_erased else -1
    minus = evaluate_side(params, minus_flux, transform=transform, **kwargs)
    return {
        "Phi_flux_coherent_recovery": plus["weighted_coherent_recovery_excess"]
        - minus["weighted_coherent_recovery_excess"],
        "coherent_excess_flux_gap": plus["coherent_recovery_excess"] - minus["coherent_recovery_excess"],
        "weighted_plus": plus["weighted_coherent_recovery_excess"],
        "weighted_minus": minus["weighted_coherent_recovery_excess"],
    }


CONTROL_CASES: dict[str, dict[str, Any]] = {
    "product": {"entangled": False},
    "commuting": {"commuting": True},
    "reversed_order": {"reversed_order": True},
    "dephased_history": {"transform": "dephase_history"},
    "history_erased": {"transform": "erase_history"},
    "classical_ab": {"transform": "classical_ab"},
    "collapsed_register": {"collapse_register": True},
    "flux_erased": {"flux_erased": True},
    "runtime_dephase_last": {"row_variant": "dephase_last"},
    "runtime_rotation_swap": {"row_variant": "rot_swap"},
}


def evaluate_stress_row(index: int, params: dict[str, float]) -> dict[str, Any]:
    canonical = candidate_value(params)
    controls = {name: candidate_value(params, **kwargs) for name, kwargs in CONTROL_CASES.items()}
    control_values = {key: value["Phi_flux_coherent_recovery"] for key, value in controls.items()}
    max_control_name, max_control_phi = max(control_values.items(), key=lambda item: item[1])
    canonical_phi = canonical["Phi_flux_coherent_recovery"]
    margin = canonical_phi - max_control_phi
    return {
        "index": index,
        "params": params,
        "canonical": canonical,
        "controls": controls,
        "max_control_name": max_control_name,
        "max_control_phi": max_control_phi,
        "canonical_phi": canonical_phi,
        "canonical_minus_max_control": margin,
        "survives": canonical_phi > 0.001 and margin > 0.001,
    }


def classify_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    margins = [row["canonical_minus_max_control"] for row in rows]
    canonical_values = [row["canonical_phi"] for row in rows]
    max_control_names = sorted({row["max_control_name"] for row in rows})
    survive_count = sum(1 for row in rows if row["survives"])
    control_fail_counts = {
        name: sum(1 for row in rows if row["canonical_phi"] > row["controls"][name]["Phi_flux_coherent_recovery"])
        for name in CONTROL_CASES
    }
    runtime_variant_controls_fire = (
        control_fail_counts["runtime_dephase_last"] == len(rows)
        and control_fail_counts["runtime_rotation_swap"] == len(rows)
    )
    carrier_controls_fire = (
        control_fail_counts["product"] == len(rows)
        and control_fail_counts["collapsed_register"] == len(rows)
        and control_fail_counts["history_erased"] == len(rows)
    )
    destructive_controls_fire = (
        control_fail_counts["commuting"] == len(rows)
        and control_fail_counts["dephased_history"] == len(rows)
        and control_fail_counts["flux_erased"] == len(rows)
    )
    robust = (
        survive_count == len(rows)
        and min(margins) > 0.001
        and min(canonical_values) > 0.001
        and runtime_variant_controls_fire
        and carrier_controls_fire
        and destructive_controls_fire
    )
    status = "bounded_stress_survived_not_final" if robust else "stress_demoted_or_open"
    return {
        "status": status,
        "bounded_stress_survives": robust,
        "row_count": len(rows),
        "survive_count": survive_count,
        "min_margin": min(margins),
        "mean_margin": sum(margins) / len(margins),
        "min_canonical_phi": min(canonical_values),
        "mean_canonical_phi": sum(canonical_values) / len(canonical_values),
        "max_control_names": max_control_names,
        "control_fail_counts": control_fail_counts,
        "runtime_variant_controls_fire": runtime_variant_controls_fire,
        "carrier_controls_fire": carrier_controls_fire,
        "destructive_controls_fire": destructive_controls_fire,
    }


def z3_nonpromotion(classification_row: dict[str, Any]) -> dict[str, Any]:
    finite_stress = z3.Bool("finite_stress_rows")
    flux_differential = z3.Bool("flux_differential")
    coherent_history = z3.Bool("coherent_history")
    bounded_stress = z3.Bool("bounded_stress")
    final_phi0 = z3.Bool("final_phi0")
    promoted = z3.Bool("promoted")

    s = z3.Solver()
    s.add(finite_stress, flux_differential, coherent_history)
    s.add(bounded_stress == bool(classification_row["bounded_stress_survives"]))
    s.add(final_phi0 == False)
    s.add(promoted == z3.And(finite_stress, flux_differential, coherent_history, bounded_stress, final_phi0))

    premature = z3.Solver()
    for assertion in s.assertions():
        premature.add(assertion)
    premature.add(promoted)

    progress = z3.Solver()
    for assertion in s.assertions():
        progress.add(assertion)
    progress.add(finite_stress, flux_differential, coherent_history)

    return {
        "pass": premature.check() == z3.unsat and progress.check() == z3.sat,
        "premature_promotion_status": str(premature.check()),
        "bounded_progress_status": str(progress.check()),
        "final_phi0": False,
    }


def section_passes(section: Any) -> bool:
    if isinstance(section, dict):
        return all(not isinstance(row, dict) or bool(row.get("pass", True)) for row in section.values())
    return False


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [evaluate_stress_row(index, params) for index, params in enumerate(stress_parameters())]
    classification_row = classify_rows(rows)
    nonpromotion = z3_nonpromotion(classification_row)

    positive = {
        "stress_rows_executed": {
            "pass": len(rows) == 8 and all(math.isfinite(row["canonical_phi"]) for row in rows),
            "row_count": len(rows),
        },
        "canonical_stress_margin_measured": {
            "pass": classification_row["survive_count"] > 0,
            "min_margin": classification_row["min_margin"],
            "mean_margin": classification_row["mean_margin"],
            "survive_count": classification_row["survive_count"],
        },
        "negative_controls_fire_across_rows": {
            "pass": classification_row["carrier_controls_fire"] and classification_row["destructive_controls_fire"],
            "control_fail_counts": classification_row["control_fail_counts"],
        },
        "runtime_variant_controls_executed": {
            "pass": classification_row["runtime_variant_controls_fire"],
            "max_control_names": classification_row["max_control_names"],
        },
        "stress_status_classified": {
            "pass": True,
            "classification": classification_row,
        },
        "z3_nonpromotion_guard": nonpromotion,
    }

    if classification_row["bounded_stress_survives"]:
        graveyard_companions = {
            "stress_survival_is_not_final_phi0": {
                "pass": True,
                "summary": "The candidate survived this bounded deterministic stress sweep but remains nonpromotional.",
            },
            "full_scale_tensor_runtime_still_missing": {
                "pass": True,
                "summary": "This scout does not close L64/PEPS/PEPS3D, full runtime, or final manifold admission.",
            },
            "holography_and_physics_not_admitted": {
                "pass": True,
                "summary": "The readout remains finite QIT formal evidence, not a holographic or physics claim.",
            },
        }
    else:
        graveyard_companions = {
            "stress_demotes_first_rung_candidate": {
                "pass": True,
                "summary": "The bounded deterministic stress sweep demoted the first-rung candidate.",
                "classification": classification_row,
            },
            "holography_and_physics_not_admitted": {
                "pass": True,
                "summary": "The readout remains finite QIT formal evidence, not a holographic or physics claim.",
            },
        }

    boundary = {
        "final_xi_phi0_not_admitted": {
            "pass": True,
            "summary": "Bounded stress survival is not final Xi/Phi0 admission.",
        },
        "formal_scout_only": {
            "pass": not PROMOTION_ALLOWED and CLASSIFICATION == "formal_scout",
            "claim_ceiling": CLAIM_CEILING,
        },
        "full_runtime_and_tensor_scaling_not_admitted": {
            "pass": True,
            "summary": "This scout does not close full coupled runtime or tensor-scaling convergence.",
        },
    }
    nearby_variants = {
        "total": len(CONTROL_CASES),
        "passed": sum(1 for count in classification_row["control_fail_counts"].values() if count == len(rows)),
        "variants": classification_row["control_fail_counts"],
    }
    why_not_v4_probes = {
        "pass": True,
        "reason": "This is a bounded v5 formal-scout stress test for a candidate bridge, not a canonical v4 promoted probe.",
    }
    open_gaps = [
        "survived bounded deterministic stress still needs full runtime and tensor-scaling stress",
        "final Xi/Phi0 remains open",
        "final manifold/basin admission remains blocked",
    ]

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "stress_rows": rows,
        "candidate_classification": classification_row,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": why_not_v4_probes,
        "open_gaps": open_gaps,
        "blockers": [],
        "all_pass": all(section_passes(section) for section in (positive, graveyard_companions, boundary))
        and nearby_variants["passed"] == nearby_variants["total"],
        "runtime_seconds": time.time() - start,
        "generated_at": time.time(),
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "status": classification_row["status"],
                "survive_count": classification_row["survive_count"],
                "min_margin": classification_row["min_margin"],
                "out": str(OUT_PATH),
            },
            indent=2,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
