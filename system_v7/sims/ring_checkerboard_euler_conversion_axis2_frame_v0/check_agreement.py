#!/usr/bin/env python3
"""Four-engine agreement adjudicator for ring_checkerboard_euler_conversion_axis2_frame_v0.

agreement_ok GATES on: (1) cross-engine agreement of the GENUINE structure (support/quotient/edge
counts + the discriminator bools) and (2) the load-bearing discriminators (euler-erase ablation,
static-frame measured diff, no-preferred-center automorphism). It does NOT gate on the
by-construction identities (Euler/Hopf reconstructions, K_direct/K_static/K_dynamic, b0-ladder) --
those are reported under by_construction_identities + by_construction_cross_engine for consistency
only, never as load-bearing. Reads only the result JSONs; computes nothing itself; does not
self-upgrade the sim.
"""

from __future__ import annotations

import json
import pathlib

SIM_ID = "ring_checkerboard_euler_conversion_axis2_frame_v0"
HERE = pathlib.Path(__file__).resolve().parent
RESULTS = HERE / "results"
OUT = RESULTS / f"{SIM_ID}_agreement_results.json"
LEGS = {
    "exact": RESULTS / f"{SIM_ID}_exact_results.json",
    "julia": RESULTS / f"{SIM_ID}_julia_results.json",
    "jax": RESULTS / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULTS / f"{SIM_ID}_pytorch_results.json",
}

# GATING cross-engine checks: genuine structure the engines could compute differently.
EXACT_INT = ["support_count", "density_class_count", "phase_sensitive_class_count",
             "adjacency_edge_count", "center_pin_edge_count"]
EXACT_BOOL = ["phi_blind", "rho_tilde_differs_static", "translation_is_automorphism"]
# NON-GATING (informational only): cross-engine consistency of BY-CONSTRUCTION identities. Four
# languages confirming the same algebraic identity is itself by-construction, so a mismatch here is
# a transcription bug to report, NOT a load-bearing failure. (box-viii fleet 2026-06-15 proved that
# gating on these let a PURE by-construction value, e.g. K_dynamic_norm, flip agreement_ok.)
BY_CONSTRUCTION_LIST = ["b0_ladder"]
BY_CONSTRUCTION_FLOAT_TOL = {"euler_reconstruction_max_err": 1e-9, "hopf_bloch_max_err": 1e-9,
                             "K_direct_norm": 1e-9, "K_static_norm": 1e-9, "K_dynamic_norm": 1e-9}


def main() -> int:
    legs = {}
    failures = []
    for name, path in LEGS.items():
        if not path.exists():
            failures.append(f"{name}: result JSON missing ({path.name})")
            continue
        legs[name] = json.loads(path.read_text())

    # every present leg must pass its own suites + carry the right ceiling
    for name, obj in legs.items():
        if not obj.get("all_tests_pass"):
            failures.append(f"{name}: all_tests_pass false")
        if not obj.get("all_controls_pass"):
            failures.append(f"{name}: all_controls_pass false")
        if obj.get("classification") != "scratch_diagnostic":
            failures.append(f"{name}: classification {obj.get('classification')}")
        if obj.get("promotion_allowed") is not False:
            failures.append(f"{name}: promotion_allowed not false")

    inv = {n: legs[n]["invariants"] for n in legs}
    ref = "exact" if "exact" in inv else next(iter(inv), None)

    # GATING: genuine cross-engine agreement (these could differ if an engine had a real bug)
    for key in EXACT_INT + EXACT_BOOL:
        vals = {n: inv[n].get(key) for n in inv}
        if len(set(json.dumps(v, sort_keys=True) for v in vals.values())) > 1:
            failures.append(f"{key}: disagreement {vals}")
    # NON-GATING: by-construction cross-engine consistency -- reported, NEVER appended to failures
    by_construction_cross_engine = {"consistent": True, "mismatches": []}
    for key in BY_CONSTRUCTION_LIST:
        vals = {n: inv[n].get(key) for n in inv}
        if len(set(json.dumps(v, sort_keys=True) for v in vals.values())) > 1:
            by_construction_cross_engine["consistent"] = False
            by_construction_cross_engine["mismatches"].append({key: vals})
    for key, tol in BY_CONSTRUCTION_FLOAT_TOL.items():
        base = inv[ref][key]
        for n in inv:
            if abs(inv[n][key] - base) > tol:
                by_construction_cross_engine["consistent"] = False
                by_construction_cross_engine["mismatches"].append(f"{key}: {n}={inv[n][key]} vs {ref}={base}")

    agreed = inv[ref] if ref else {}

    # BY-CONSTRUCTION IDENTITIES: forced for ALL inputs (Euler's formula; psi^dag sigma psi vs the
    # double-angle formula; norm is unitarily invariant; K formed by @zeros). These are NOT
    # discriminators -- they cannot fail. Reported only for cross-language consistency. (box-viii
    # fleet audit 2026-06-15 caught these mislabelled as load-bearing.)
    deltas = [legs[n].get("ablation_outcome_delta", {}).get("delta", 0.0) for n in legs]
    # CATEGORY 1 -- BY-CONSTRUCTION IDENTITIES: forced for ALL inputs; cannot fail; reported for
    # cross-language consistency only. box-viii L6 fleet (2026-06-15, 5/6 real children) ADDED the
    # euler-erase ablation here: cos-only reconstruction breaks normalization for every input, so
    # delta=1.0 is a complex-vs-real representation tautology, NOT a state discriminator.
    by_construction_identities = {
        "euler_reconstruction_is_algebraic_identity": agreed.get("euler_reconstruction_max_err", 1) < 1e-9,
        "hopf_doubleangle_is_algebraic_identity": agreed.get("hopf_bloch_max_err", 1) < 1e-9,
        "axis2_K_direct_zero_by_construction": agreed.get("K_direct_norm", 1) < 1e-9,
        "axis2_K_static_zero_by_construction": agreed.get("K_static_norm", 1) < 1e-9,
        "axis2_K_dynamic_is_unitary_norm_invariance": abs(agreed.get("K_dynamic_norm", 0) - 0.7071067811865476) < 1e-9,
        "finite_gradation_b0_is_grid_induced_sign_cos2eta": agreed.get("b0_ladder") == [1, 0, -1],
        "euler_erase_cos_only_breaks_norm_all_inputs": all(d > 0.1 for d in deltas),
    }
    # CATEGORY 2 -- STATIC STRUCTURAL INVARIANTS: true for the CHOSEN grid regardless of the spinor
    # state. box-viii L6 (gemini + run-it): these flip only by hand-editing the structural bool, NOT
    # by perturbing a physical/state quantity -- "perturbation flips the gate" is NECESSARY but NOT
    # SUFFICIENT for state-discrimination. They GATE (a real consistency check) but are NOT claimed as
    # state discriminators.
    static_structural_invariants = {
        "translation_is_a_grid_automorphism": agreed.get("translation_is_automorphism") is True,
        "center_pin_breaks_grid_adjacency": agreed.get("center_pin_edge_count") != agreed.get("adjacency_edge_count"),
    }
    # CATEGORY 3 -- STATE-SENSITIVE DISCRIMINATORS (CONTESTED, held not resolved): the only candidates
    # that vary with the spinor STATE. box-viii L6 the fleet CONTESTS even these (deepseek: static-
    # basis-change ~ basis artifact; grok: phi-blind ~ tautology of the chosen quotient). So this sim
    # earns AT MOST 1-2 contested state-discriminators -- the GENUINE Axis-2 measurement is the
    # separate K_t loop-holonomy sim (ring_checkerboard_axis2_kt_holonomy_v0).
    state_sensitive_discriminators_contested = {
        "static_basis_change_alters_rho": agreed.get("rho_tilde_differs_static") is True,
        "phi_blind_density_phase_probe_splits": (agreed.get("phi_blind") is True
            and agreed.get("phase_sensitive_class_count", 0) > agreed.get("density_class_count", 0)),
    }
    for cat in (static_structural_invariants, state_sensitive_discriminators_contested):
        for k, ok in cat.items():
            if not ok:
                failures.append(f"consistency check {k} not satisfied")

    n_engines = len(inv)
    agreement_ok = (not failures) and n_engines == 4
    if n_engines < 4:
        failures.append(f"only {n_engines}/4 engines present; three-engine+canon path not complete")

    result = {
        "schema": "codex_ratchet.agreement_result.v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "agreement_ok": agreement_ok,
        "engines_present": sorted(inv.keys()),
        "n_engines": n_engines,
        "agreed_invariants": agreed,
        "by_construction_identities": by_construction_identities,
        "by_construction_cross_engine": by_construction_cross_engine,
        "static_structural_invariants": static_structural_invariants,
        "state_sensitive_discriminators_contested": state_sensitive_discriminators_contested,
        "failures": failures,
        "honest_scope": {
            "earns": "four-engine (numpy/julia/jax/pytorch) cross-language AGREEMENT on all invariants of a 96-cell finite support, in THREE honestly-separated categories. The 6-model box-viii fleet (2026-06-15) demoted this sim's claimed content TWICE: (cat1) by-construction algebraic identities incl. the euler-erase ablation (cos-only breaks norm for ALL inputs); (cat2) STATIC GRID-TOPOLOGY invariants (translation-automorphism, center-pin) that flip only by hand-editing a bool, not by a state perturbation -- NOT state discriminators; (cat3) at most 1-2 CONTESTED state-sensitive candidates (static-basis-change, phi-blind/phase-split), which the fleet itself disputes.",
            "does_not_earn": "NO uncontested genuine state-discriminator, and NO Axis-2 frame discriminator (the real test is the separate K_t loop-holonomy sim ring_checkerboard_axis2_kt_holonomy_v0). 'perturbation flips the gate' is NECESSARY but NOT SUFFICIENT for state-discrimination (box-viii L6, qwen+run-it). No M(C), Axis0, QIT engine, manifold, or physics. box viii = ADVANCED_NOT_CLOSED.",
        },
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"agreement_ok": agreement_ok, "n_engines": n_engines, "engines": sorted(inv.keys()), "failures": failures}, indent=2))
    return 0 if agreement_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
