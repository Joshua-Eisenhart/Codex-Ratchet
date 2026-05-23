#!/usr/bin/env python3
"""Oriented recovery-asymmetry Phi0 bridge candidate.

Formal scout only. This tests the natural repair after the Petz-recovery
candidate failed against a near reversed-order control: make the readout
explicitly oriented by comparing forward and reversed finite history dynamics.

Candidate surface:

    Delta_Petz(history) = ||rho_ABC - R_Petz(rho_AB)||_F
    A_rec = Delta_Petz(forward) - Delta_Petz(reversed)
    Phi_oriented = A_rec * mean_negativity(AB)

The candidate is allowed to fail. A clean failure still narrows the Axis0/Phi0
search space without promoting final Xi, final Phi0, full FEP, or physics.
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
    evaluate_case as evaluate_petz_case,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "two_root_constraint_oriented_recovery_phi0_candidate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "oriented_recovery_phi0_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests a finite oriented Petz-recovery asymmetry Phi0 "
    "candidate. It does not admit final Xi, final Phi0, final Axis0, full FEP, "
    "Markov blanket ontology, holography, ER=EPR, or physics."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite forward/reverse recovery readouts and tensor-backed inherited Petz calculations",
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


def evaluate_pair(name: str, transform: str = "canonical", **kwargs: Any) -> dict[str, Any]:
    forward = evaluate_petz_case(f"{name}_forward", transform=transform, **kwargs)
    reversed_case = evaluate_petz_case(f"{name}_reversed", transform=transform, reversed_order=True, **kwargs)
    defect_asym = forward["petz_defect_fro"] - reversed_case["petz_defect_fro"]
    phi_asym = forward["Phi_Petz"] - reversed_case["Phi_Petz"]
    qci_asym = forward["I_A_C_given_B"] - reversed_case["I_A_C_given_B"]
    mean_negativity = 0.5 * (forward["negativity_AB"] + reversed_case["negativity_AB"])
    mean_qci = 0.5 * (forward["I_A_C_given_B"] + reversed_case["I_A_C_given_B"])
    phi_oriented = defect_asym * mean_negativity
    phi_oriented_qci = phi_oriented * mean_qci
    return {
        "name": name,
        "transform": transform,
        "forward": {
            key: forward[key]
            for key in ["petz_defect_fro", "I_A_C_given_B", "I_c_A_to_B", "negativity_AB", "Phi_Petz"]
        },
        "reversed": {
            key: reversed_case[key]
            for key in ["petz_defect_fro", "I_A_C_given_B", "I_c_A_to_B", "negativity_AB", "Phi_Petz"]
        },
        "defect_asymmetry": defect_asym,
        "abs_defect_asymmetry": abs(defect_asym),
        "phi_petz_asymmetry": phi_asym,
        "qci_asymmetry": qci_asym,
        "mean_negativity_AB": mean_negativity,
        "mean_QCI": mean_qci,
        "Phi_oriented": phi_oriented,
        "Phi_oriented_qci": phi_oriented_qci,
    }


def classify_cases(cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    canonical = cases["canonical"]["Phi_oriented"]
    controls = {key: row["Phi_oriented"] for key, row in cases.items() if key != "canonical"}
    max_control_name, max_control_phi = max(controls.items(), key=lambda item: item[1])
    min_control_name, min_control_phi = min(controls.items(), key=lambda item: item[1])

    canonical_minus_commuting = canonical - cases["commuting"]["Phi_oriented"]
    canonical_minus_erased = canonical - cases["history_erased"]["Phi_oriented"]
    canonical_minus_dephased = canonical - cases["dephased_history"]["Phi_oriented"]
    canonical_minus_product = canonical - cases["product"]["Phi_oriented"]
    canonical_minus_opposite_flux = canonical - cases["opposite_flux"]["Phi_oriented"]
    canonical_minus_classical = canonical - cases["classical_ab"]["Phi_oriented"]
    canonical_minus_collapsed = canonical - cases["collapsed_register"]["Phi_oriented"]
    canonical_minus_max = canonical - max_control_phi

    orientation_signal_measured = abs(cases["canonical"]["defect_asymmetry"]) > 0.005
    noncommuting_path_sensitive = abs(canonical_minus_commuting) > 0.001
    history_register_load_bearing = abs(canonical_minus_erased) > 0.001
    entanglement_condition_load_bearing = abs(canonical_minus_product) > 0.001
    collapsed_register_rejected = abs(canonical_minus_collapsed) > 0.001
    control_separated = canonical_minus_max > 0.02
    first_rung_survives = (
        control_separated
        and orientation_signal_measured
        and noncommuting_path_sensitive
        and history_register_load_bearing
    )
    status = "first_rung_control_separated_not_final" if first_rung_survives else "open_or_killed_nonseparating"
    return {
        "status": status,
        "first_rung_survives": first_rung_survives,
        "control_separated": control_separated,
        "orientation_signal_measured": orientation_signal_measured,
        "noncommuting_path_sensitive": noncommuting_path_sensitive,
        "history_register_load_bearing": history_register_load_bearing,
        "entanglement_condition_load_bearing": entanglement_condition_load_bearing,
        "collapsed_register_rejected": collapsed_register_rejected,
        "canonical_phi": canonical,
        "max_control_name": max_control_name,
        "max_control_phi": max_control_phi,
        "min_control_name": min_control_name,
        "min_control_phi": min_control_phi,
        "canonical_minus_max_control": canonical_minus_max,
        "canonical_minus_commuting": canonical_minus_commuting,
        "canonical_minus_history_erased": canonical_minus_erased,
        "canonical_minus_dephased_history": canonical_minus_dephased,
        "canonical_minus_product": canonical_minus_product,
        "canonical_minus_opposite_flux": canonical_minus_opposite_flux,
        "canonical_minus_classical_ab": canonical_minus_classical,
        "canonical_minus_collapsed_register": canonical_minus_collapsed,
        "canonical_defect_asymmetry": cases["canonical"]["defect_asymmetry"],
    }


def z3_nonpromotion(classification_row: dict[str, Any]) -> dict[str, Any]:
    finite = z3.Bool("finite_forward_reverse_cut")
    noncommuting = z3.Bool("noncommuting_paths")
    oriented_recovery = z3.Bool("oriented_recovery")
    first_rung = z3.Bool("first_rung")
    final_phi0 = z3.Bool("final_phi0")
    promoted = z3.Bool("promoted")

    s = z3.Solver()
    s.add(finite, noncommuting, oriented_recovery)
    s.add(first_rung == bool(classification_row["first_rung_survives"]))
    s.add(final_phi0 == False)
    s.add(promoted == z3.And(finite, noncommuting, oriented_recovery, first_rung, final_phi0))

    premature = z3.Solver()
    for assertion in s.assertions():
        premature.add(assertion)
    premature.add(promoted)

    progress = z3.Solver()
    for assertion in s.assertions():
        progress.add(assertion)
    progress.add(finite, noncommuting, oriented_recovery)

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
        "opposite_flux": evaluate_pair("opposite_flux", flux=-1),
        "dephased_history": evaluate_pair("dephased_history", transform="dephase_history"),
        "history_erased": evaluate_pair("history_erased", transform="erase_history"),
        "classical_ab": evaluate_pair("classical_ab", transform="classical_ab"),
        "collapsed_register": evaluate_pair("collapsed_register", collapse_register=True),
    }
    classification_row = classify_cases(cases)
    nonpromotion = z3_nonpromotion(classification_row)

    positive = {
        "oriented_recovery_surface_built": {
            "pass": all(math.isfinite(row["Phi_oriented"]) for row in cases.values()),
            "case_names": sorted(cases),
            "canonical_components": {
                key: cases["canonical"][key]
                for key in [
                    "defect_asymmetry",
                    "phi_petz_asymmetry",
                    "qci_asymmetry",
                    "mean_negativity_AB",
                    "mean_QCI",
                    "Phi_oriented",
                ]
            },
        },
        "orientation_signal_measured": {
            "pass": classification_row["orientation_signal_measured"],
            "canonical_defect_asymmetry": classification_row["canonical_defect_asymmetry"],
        },
        "noncommuting_path_difference_measured": {
            "pass": classification_row["noncommuting_path_sensitive"],
            "canonical_minus_commuting": classification_row["canonical_minus_commuting"],
        },
        "history_register_signal_measured": {
            "pass": classification_row["history_register_load_bearing"],
            "canonical_minus_history_erased": classification_row["canonical_minus_history_erased"],
            "canonical_minus_collapsed_register": classification_row["canonical_minus_collapsed_register"],
        },
        "candidate_status_classified": {
            "pass": True,
            "classification": classification_row,
        },
        "z3_nonpromotion_guard": nonpromotion,
    }

    if classification_row["first_rung_survives"]:
        graveyard_companions = {
            "first_rung_is_not_final_phi0": {
                "pass": True,
                "summary": "The oriented recovery candidate separates in this bounded fixture but still has no final Xi/Phi0 admission.",
            },
            "full_stress_not_run": {
                "pass": True,
                "summary": "This scout does not provide scale, tensor-carrier, broad seed, or full source-runtime stress.",
            },
            "holography_and_physics_not_admitted": {
                "pass": True,
                "summary": "No physical, holographic, or ER=EPR claim follows from a finite oriented recovery readout.",
            },
            "markov_blanket_ontology_not_admitted": {
                "pass": True,
                "summary": "The recovery asymmetry is a finite quantum-history diagnostic, not a classical Markov blanket ontology.",
            },
        }
    else:
        graveyard_companions = {
            "candidate_not_control_separated": {
                "pass": not classification_row["control_separated"],
                "summary": "The canonical oriented recovery candidate does not beat all controls by the admission margin.",
            },
            "oriented_recovery_not_sufficient_for_admission": {
                "pass": True,
                "summary": "Forward/reverse Petz asymmetry is not enough to admit Phi0 without control separation.",
            },
            "dephased_or_flux_control_blocks_admission": {
                "pass": classification_row["max_control_name"] in {"dephased_history", "opposite_flux", "product"},
                "summary": "A dephased-history, opposite-flux, or product control is too large for admission.",
            },
            "holography_and_physics_not_admitted": {
                "pass": True,
                "summary": "No physical, holographic, or ER=EPR claim follows from a killed/open finite oriented recovery readout.",
            },
        }

    boundary = {
        "final_xi_phi0_not_admitted": {
            "pass": nonpromotion["premature_promotion_status"] == "unsat",
            "summary": "The candidate is either killed/open or first-rung only; final Phi0 remains false in the dependency fence.",
        },
        "formal_scout_only": {
            "pass": True,
            "summary": "The receipt is nonpromotional and remains under the formal-scout claim ceiling.",
        },
        "full_fep_not_admitted": {
            "pass": True,
            "summary": "This is a finite QIT/FEP-adjacent recovery diagnostic, not full FEP or a classical Markov-chain replacement.",
        },
    }
    nearby_variants = {
        "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        "total": len(graveyard_companions),
        "variants": sorted(graveyard_companions),
    }
    why_not_v4_probes = {
        "pass": True,
        "reason": "This is a v5 formal-scout candidate classifier over a finite oriented recovery bridge, not a canonical v4 physics probe.",
    }
    open_gaps = [
        "final Xi/Phi0 remains open",
        "scale, seed, tensor-carrier, and stress controls are not closed by this candidate",
        "full FEP, Markov blanket ontology, holography, ER=EPR, and physics remain unadmitted",
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
