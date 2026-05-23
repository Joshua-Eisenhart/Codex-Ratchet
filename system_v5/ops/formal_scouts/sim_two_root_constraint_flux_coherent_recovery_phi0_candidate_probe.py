#!/usr/bin/env python3
"""Flux-coherent recovery Phi0 bridge candidate.

Formal scout only. This tests a stronger Xi -> rho_AB -> Phi0 candidate after
raw free-energy, QCI, Petz-recovery, and oriented-recovery candidates failed
against beta-zero, collapsed-register, reversed-order, or dephased-history
controls.

Candidate surface:

    E_coh(f) = Phi_Petz(rho_f) - Phi_Petz(Delta_C(rho_f))
    W(f) = E_coh(f) * max(I(A:C|B)_f - I(B:C|A)_f, 0)
    Phi_flux_coh = W(+flux) - W(-flux)

The candidate explicitly treats flux as a manifold-level differential rather
than a per-stage axis setting. It is allowed to fail. A clean failure or a
bounded first-rung separation still does not admit final Xi, final Phi0, full
FEP, or physics.
"""

from __future__ import annotations

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
    coherent_history_state,
    conditional_mutual_information,
    dephase_ab,
    dephase_register_c,
    erase_register_c,
    negativity_ab,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "two_root_constraint_flux_coherent_recovery_phi0_candidate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "flux_coherent_recovery_phi0_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a finite flux-differential coherent Petz-recovery "
    "Phi0 candidate. It does not admit final Xi, final Phi0, final Axis0, full "
    "FEP, Markov blanket ontology, holography, ER=EPR, or physics."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing complex density matrices, coherent history dephasing, "
            "Petz recovery, flux-differential readouts, entropy-derived QCI, and negativity"
        ),
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive dependency and nonpromotion fence for bridge classification",
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
    directional_qci_gap = qci_a_given_b - qci_b_given_a
    return {
        "petz_defect_fro": defect,
        "negativity_AB": neg,
        "I_A_C_given_B": qci_a_given_b,
        "I_B_C_given_A": qci_b_given_a,
        "directional_qci_gap": directional_qci_gap,
        "Phi_Petz": defect * neg,
    }


def evaluate_side(
    name: str,
    flux: int,
    transform: str = "canonical",
    **kwargs: Any,
) -> dict[str, Any]:
    rho, dims, meta = coherent_history_state(flux=flux, **kwargs)
    rho = transform_history(rho, dims, transform)
    raw = petz_metrics(rho, dims)
    dephased = petz_metrics(dephase_register_c(rho, dims[2]), dims)
    coherent_excess = raw["Phi_Petz"] - dephased["Phi_Petz"]
    weighted_excess = coherent_excess * max(raw["directional_qci_gap"], 0.0)
    return {
        "name": name,
        "flux": flux,
        "transform": transform,
        "dims": dims,
        "branch_count": meta["branch_count"],
        "branch_probability_total": sum(meta["branch_probs"]),
        "raw": raw,
        "dephased_baseline": dephased,
        "coherent_recovery_excess": coherent_excess,
        "weighted_coherent_recovery_excess": weighted_excess,
    }


def evaluate_pair(name: str, transform: str = "canonical", flux_erased: bool = False, **kwargs: Any) -> dict[str, Any]:
    plus = evaluate_side(f"{name}_plus", flux=1, transform=transform, **kwargs)
    minus_flux = 1 if flux_erased else -1
    minus = evaluate_side(f"{name}_minus", flux=minus_flux, transform=transform, **kwargs)
    phi = plus["weighted_coherent_recovery_excess"] - minus["weighted_coherent_recovery_excess"]
    return {
        "name": name,
        "transform": transform,
        "flux_erased": flux_erased,
        "plus": plus,
        "minus": minus,
        "Phi_flux_coherent_recovery": phi,
        "coherent_excess_flux_gap": plus["coherent_recovery_excess"] - minus["coherent_recovery_excess"],
        "weighted_plus": plus["weighted_coherent_recovery_excess"],
        "weighted_minus": minus["weighted_coherent_recovery_excess"],
    }


def classify_cases(cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    canonical = cases["canonical"]["Phi_flux_coherent_recovery"]
    controls = {key: row["Phi_flux_coherent_recovery"] for key, row in cases.items() if key != "canonical"}
    max_control_name, max_control_phi = max(controls.items(), key=lambda item: item[1])
    min_control_name, min_control_phi = min(controls.items(), key=lambda item: item[1])

    canonical_minus_max = canonical - max_control_phi
    canonical_minus_commuting = canonical - cases["commuting"]["Phi_flux_coherent_recovery"]
    canonical_minus_reversed = canonical - cases["reversed_order"]["Phi_flux_coherent_recovery"]
    canonical_minus_dephased = canonical - cases["dephased_history"]["Phi_flux_coherent_recovery"]
    canonical_minus_erased = canonical - cases["history_erased"]["Phi_flux_coherent_recovery"]
    canonical_minus_product = canonical - cases["product"]["Phi_flux_coherent_recovery"]
    canonical_minus_classical = canonical - cases["classical_ab"]["Phi_flux_coherent_recovery"]
    canonical_minus_collapsed = canonical - cases["collapsed_register"]["Phi_flux_coherent_recovery"]
    canonical_minus_flux_erased = canonical - cases["flux_erased"]["Phi_flux_coherent_recovery"]

    flux_differential_signal_measured = canonical > 0.006
    coherent_history_excess_measured = abs(cases["canonical"]["coherent_excess_flux_gap"]) > 0.003
    noncommuting_path_control_rejected = canonical_minus_commuting > 0.006
    reversed_order_control_rejected = canonical_minus_reversed > 0.003
    dephased_history_control_rejected = canonical_minus_dephased > 0.006
    history_erased_control_rejected = canonical_minus_erased > 0.006
    entanglement_condition_load_bearing = canonical_minus_product > 0.006
    collapsed_register_rejected = canonical_minus_collapsed > 0.006
    flux_erased_control_rejected = canonical_minus_flux_erased > 0.006
    control_separated = canonical_minus_max > 0.003
    first_rung_survives = (
        control_separated
        and flux_differential_signal_measured
        and coherent_history_excess_measured
        and noncommuting_path_control_rejected
        and reversed_order_control_rejected
        and dephased_history_control_rejected
        and history_erased_control_rejected
        and entanglement_condition_load_bearing
        and collapsed_register_rejected
        and flux_erased_control_rejected
    )
    status = "first_rung_control_separated_not_final" if first_rung_survives else "open_or_killed_nonseparating"
    return {
        "status": status,
        "first_rung_survives": first_rung_survives,
        "control_separated": control_separated,
        "flux_differential_signal_measured": flux_differential_signal_measured,
        "coherent_history_excess_measured": coherent_history_excess_measured,
        "noncommuting_path_control_rejected": noncommuting_path_control_rejected,
        "reversed_order_control_rejected": reversed_order_control_rejected,
        "dephased_history_control_rejected": dephased_history_control_rejected,
        "history_erased_control_rejected": history_erased_control_rejected,
        "entanglement_condition_load_bearing": entanglement_condition_load_bearing,
        "collapsed_register_rejected": collapsed_register_rejected,
        "flux_erased_control_rejected": flux_erased_control_rejected,
        "canonical_phi": canonical,
        "max_control_name": max_control_name,
        "max_control_phi": max_control_phi,
        "min_control_name": min_control_name,
        "min_control_phi": min_control_phi,
        "canonical_minus_max_control": canonical_minus_max,
        "canonical_minus_commuting": canonical_minus_commuting,
        "canonical_minus_reversed_order": canonical_minus_reversed,
        "canonical_minus_dephased_history": canonical_minus_dephased,
        "canonical_minus_history_erased": canonical_minus_erased,
        "canonical_minus_product": canonical_minus_product,
        "canonical_minus_classical_ab": canonical_minus_classical,
        "canonical_minus_collapsed_register": canonical_minus_collapsed,
        "canonical_minus_flux_erased": canonical_minus_flux_erased,
        "canonical_coherent_excess_flux_gap": cases["canonical"]["coherent_excess_flux_gap"],
    }


def z3_nonpromotion(classification_row: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite_flux_history_cut")
    noncommuting = z3.Bool("noncommuting_paths")
    flux_differential = z3.Bool("flux_differential")
    coherent_history = z3.Bool("coherent_history")
    first_rung = z3.Bool("first_rung")
    final_phi0 = z3.Bool("final_phi0")
    promoted = z3.Bool("promoted")

    s = z3.Solver()
    s.add(finite, noncommuting, flux_differential, coherent_history)
    s.add(first_rung == bool(classification_row["first_rung_survives"]))
    s.add(final_phi0 == False)
    s.add(promoted == z3.And(finite, noncommuting, flux_differential, coherent_history, first_rung, final_phi0))

    premature = z3.Solver()
    for assertion in s.assertions():
        premature.add(assertion)
    premature.add(promoted)

    progress = z3.Solver()
    for assertion in s.assertions():
        progress.add(assertion)
    progress.add(finite, noncommuting, flux_differential, coherent_history)

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
    cases = {
        "canonical": evaluate_pair("canonical"),
        "product": evaluate_pair("product", entangled=False),
        "commuting": evaluate_pair("commuting", commuting=True),
        "reversed_order": evaluate_pair("reversed_order", reversed_order=True),
        "dephased_history": evaluate_pair("dephased_history", transform="dephase_history"),
        "history_erased": evaluate_pair("history_erased", transform="erase_history"),
        "classical_ab": evaluate_pair("classical_ab", transform="classical_ab"),
        "collapsed_register": evaluate_pair("collapsed_register", collapse_register=True),
        "flux_erased": evaluate_pair("flux_erased", flux_erased=True),
    }
    classification_row = classify_cases(cases)
    nonpromotion = z3_nonpromotion(classification_row)

    positive = {
        "flux_coherent_recovery_surface_built": {
            "pass": all(math.isfinite(row["Phi_flux_coherent_recovery"]) for row in cases.values()),
            "case_names": sorted(cases),
            "canonical_components": {
                key: cases["canonical"][key]
                for key in [
                    "Phi_flux_coherent_recovery",
                    "coherent_excess_flux_gap",
                    "weighted_plus",
                    "weighted_minus",
                ]
            },
        },
        "flux_differential_signal_measured": {
            "pass": classification_row["flux_differential_signal_measured"],
            "canonical_phi": classification_row["canonical_phi"],
            "canonical_minus_flux_erased": classification_row["canonical_minus_flux_erased"],
        },
        "coherent_history_excess_measured": {
            "pass": classification_row["coherent_history_excess_measured"],
            "canonical_coherent_excess_flux_gap": classification_row["canonical_coherent_excess_flux_gap"],
            "canonical_minus_dephased_history": classification_row["canonical_minus_dephased_history"],
            "canonical_minus_history_erased": classification_row["canonical_minus_history_erased"],
        },
        "noncommuting_path_control_rejected": {
            "pass": classification_row["noncommuting_path_control_rejected"],
            "canonical_minus_commuting": classification_row["canonical_minus_commuting"],
        },
        "entanglement_and_register_controls_rejected": {
            "pass": classification_row["entanglement_condition_load_bearing"]
            and classification_row["collapsed_register_rejected"],
            "canonical_minus_product": classification_row["canonical_minus_product"],
            "canonical_minus_collapsed_register": classification_row["canonical_minus_collapsed_register"],
        },
        "candidate_first_rung_control_separated": {
            "pass": classification_row["first_rung_survives"],
            "classification": classification_row,
        },
        "z3_nonpromotion_guard": nonpromotion,
    }

    if classification_row["first_rung_survives"]:
        graveyard_companions = {
            "first_rung_is_not_final_phi0": {
                "pass": True,
                "summary": (
                    "Flux-coherent recovery separates in the bounded fixture, "
                    "but it still has no broad stress, scale, or final Xi/Phi0 admission."
                ),
            },
            "full_stress_not_run_for_flux_recovery": {
                "pass": True,
                "summary": "The scout does not provide multi-seed stress, tensor scaling, or full source-runtime stress.",
            },
            "holography_and_physics_not_admitted": {
                "pass": True,
                "summary": "The readout remains a finite QIT formal scout, not a holographic or physics claim.",
            },
        }
    else:
        graveyard_companions = {
            "candidate_not_control_separated": {
                "pass": True,
                "summary": "The candidate failed first-rung control separation.",
                "classification": classification_row,
            },
            "flux_coherent_recovery_not_sufficient_for_admission": {
                "pass": True,
                "summary": "Flux-differential coherent recovery did not admit final Phi0.",
            },
            "holography_and_physics_not_admitted": {
                "pass": True,
                "summary": "The readout remains a finite QIT formal scout, not a holographic or physics claim.",
            },
        }

    boundary = {
        "final_xi_phi0_not_admitted": {
            "pass": True,
            "summary": "No final Xi/Phi0 admission is made by this scout.",
        },
        "formal_scout_only": {
            "pass": not PROMOTION_ALLOWED and CLASSIFICATION == "formal_scout",
            "claim_ceiling": CLAIM_CEILING,
        },
        "full_fep_not_admitted": {
            "pass": True,
            "summary": "Finite flux-coherent recovery does not admit a full FEP or Markov-blanket ontology.",
        },
    }
    nearby_variants = {
        "total": 8,
        "passed": sum(
            1
            for key in [
                "product",
                "commuting",
                "reversed_order",
                "dephased_history",
                "history_erased",
                "classical_ab",
                "collapsed_register",
                "flux_erased",
            ]
            if classification_row["canonical_phi"] > cases[key]["Phi_flux_coherent_recovery"]
        ),
        "variants": {
            key: cases[key]["Phi_flux_coherent_recovery"]
            for key in [
                "product",
                "commuting",
                "reversed_order",
                "dephased_history",
                "history_erased",
                "classical_ab",
                "collapsed_register",
                "flux_erased",
            ]
        },
    }
    why_not_v4_probes = {
        "pass": True,
        "reason": "This is a candidate-level v5 QIT bridge scout, not a canonical v4 promoted probe.",
    }
    open_gaps = [
        "bounded first-rung separation needs broad stress before any Xi/Phi0 admission",
        "full tensor scaling and environment contraction remain open",
        "full coupled source-aligned runtime remains open beyond bounded E16 first-rung evidence",
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
        "cases": cases,
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
                "max_control_name": classification_row["max_control_name"],
                "canonical_minus_max_control": classification_row["canonical_minus_max_control"],
                "out": str(OUT_PATH),
            },
            indent=2,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
