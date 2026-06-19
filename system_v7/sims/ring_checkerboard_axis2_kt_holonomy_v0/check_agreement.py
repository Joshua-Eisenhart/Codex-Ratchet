#!/usr/bin/env python3
"""Four-engine agreement adjudicator for ring_checkerboard_axis2_kt_holonomy_v0.

agreement_ok GATES on: (1) cross-engine agreement of the GENUINE discriminator booleans (the
holonomy is nontrivial only around a curved loop; trivial for comoving/trivial/flat loops; open path
gauge-dependent) and (2) the cross-engine agreement of the load-bearing NUMERIC content within a
discretization tolerance (dynamic |U-I|, the flux match, the flat-connection collapse). Reads only
the result JSONs; computes nothing itself; does not self-upgrade the sim.

Unlike the demoted euler sim, this sim has NO by-construction identities to fence off: every test is
a measurement that could have come out flat (a flat/pure-gauge connection around the SAME loop gives
the identity -- that is the outcome that does NOT occur for the curved frame, which is what makes the
holonomy load-bearing). The numeric agreement is gated with a discretization tolerance because the
four engines use distinct float paths (numpy complex division, julia arg/exp link, jax vectorized
prod, torch complex prod) -- they carry distinct float fingerprints but must agree on the physics.
"""

from __future__ import annotations

import json
import pathlib

SIM_ID = "ring_checkerboard_axis2_kt_holonomy_v0"
HERE = pathlib.Path(__file__).resolve().parent
RESULTS = HERE / "results"
OUT = RESULTS / f"{SIM_ID}_agreement_results.json"
LEGS = {
    "exact": RESULTS / f"{SIM_ID}_exact_results.json",
    "julia": RESULTS / f"{SIM_ID}_julia_results.json",
    "jax": RESULTS / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULTS / f"{SIM_ID}_pytorch_results.json",
}

# GATING bools: the discriminator booleans -- could differ if an engine had a real bug.
GATE_TEST_BOOLS = ["dynamic_eulerian_holonomy_nontrivial", "holonomy_equals_enclosed_flux",
                   "direct_lagrangian_holonomy_trivial"]
# LOAD-BEARING control booleans: each can come out the other way (a value-coupled flip).
GATE_CONTROL_BOOLS = ["trivial_loop_holonomy_trivial", "flat_connection_same_loop_trivial",
                      "curvature_load_bearing_curved_nontrivial_flat_trivial",
                      "real_loop_holonomy_matches_flux", "shrink_loop_holonomy_to_identity",
                      "shrink_phase_tracks_flux", "closed_holonomy_gauge_invariant",
                      "open_path_holonomy_gauge_dependent",
                      # grok ODE control: ODE-derived holonomy matches the link-product holonomy AND
                      # the NEGATIVE control flips (flat loop -> ODE phase ~0). This is the genuinely
                      # formula-independent cross-engine route (only ODE legs are not the overlap-product).
                      "ode_geometric_phase_nontrivial", "ode_holonomy_matches_link_product",
                      "ode_flat_loop_trivial", "ode_flips_curved_vs_flat",
                      # THE coordinate-baking resolution rests on flat-connection + ODE (NOT the knob).
                      "coordinate_baking_resolved_by_flat_and_ode"]
# NUMERICS-CONSISTENCY booleans (re-tiered post-audit 2026-06-15): the deepseek colatitude-knob.
# These check link-product correctness across a family + monotone shrink, but the phase=g*Omega/2
# match is an ANALYTIC IDENTITY of the alpha_g formula (not an independent measurement) and the g=0
# endpoint is a STRUCTURAL ZERO (any phi-independent frame -> U=I). They are gated for cross-engine
# agreement but are NOT counted as load-bearing coordinate-baking discriminators.
NUMERICS_CONSISTENCY_BOOLS = ["curvature_knob_g0_degenerate_endpoint_consistent",
                              "curvature_knob_phase_reproduces_g_flux_numerics",
                              "curvature_knob_monotone_in_g",
                              "curvature_knob_linear_slope_matches_half_flux",
                              "curvature_knob_numerics_consistent"]
# GATING numeric: load-bearing measured values, agreed across engines to a discretization tol.
GATE_FLOAT_TOL = {
    "enclosed_solid_angle": 1e-9,        # analytic, identical
    "expected_holonomy_phase": 1e-9,     # analytic
    "dynamic_holonomy_abs_minus_I": 1e-3,  # ~1.414, discretization-limited
    "dynamic_holonomy_phase": 1e-4,        # ~pi/2
    "flux_match_err": 1e-4,                # all ~2e-7
    "direct_holonomy_abs_minus_I": 1e-6,   # all ~0
    "flat_connection_holonomy_abs_minus_I": 1e-6,  # all ~1e-13 (the anti-by-construction control)
    # deepseek colatitude-knob (NUMERICS-CONSISTENCY tier): slope -> Omega/2 and the g=0 structural
    # zero. NOTE: these agree across engines because they share the same alpha_g/overlap-product
    # formula (correlated), NOT because they are independent measurements.
    "curvature_knob_flux_max_err": 1e-4,           # all ~2e-7 (analytic identity of alpha_g)
    "curvature_knob_g0_abs_U_minus_I": 1e-6,       # all ~0 (STRUCTURAL ZERO: phi-independent frame)
    "curvature_knob_linear_slope": 1e-3,           # all ~1.5708 (slope = Omega/2, analytic consequence)
    # grok ODE: the GENUINELY formula-independent cross-engine route (distinct integrators, same physics)
    "ode_geometric_phase": 1e-6,                   # all ~-1.5704263 (distinct ODE integrators)
    "ode_vs_link_match_err": 1e-4,                 # all ~3.70e-4 (adiabatic 1/B residual)
    "ode_geometric_phase_flat_loop": 1e-4,         # all ~0 (negative control: flat loop -> trivial)
}


def main() -> int:
    legs = {}
    failures = []
    # canonical legs (exact+jax+julia) are REQUIRED; pytorch is an OPTIONAL fourth validation leg
    # (sidelined per project canon). A missing pytorch result is noted, not a failure.
    canonical = {"exact", "jax", "julia"}
    for name, path in LEGS.items():
        if not path.exists():
            if name in canonical:
                failures.append(f"{name}: canonical result JSON missing ({path.name})")
            continue
        legs[name] = json.loads(path.read_text())

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
    tst = {n: legs[n]["tests"] for n in legs}
    ctl = {n: legs[n]["controls"] for n in legs}
    ref = "exact" if "exact" in inv else next(iter(inv), None)

    # GATING: discriminator booleans agree across engines AND are True in every engine
    for key in GATE_TEST_BOOLS:
        vals = {n: tst[n].get(key) for n in tst}
        if len(set(json.dumps(v) for v in vals.values())) > 1:
            failures.append(f"test bool {key}: disagreement {vals}")
        if not all(vals.values()):
            failures.append(f"test bool {key}: not True in every engine {vals}")
    for key in GATE_CONTROL_BOOLS:
        vals = {n: ctl[n].get(key) for n in ctl}
        if len(set(json.dumps(v) for v in vals.values())) > 1:
            failures.append(f"control bool {key}: disagreement {vals}")
        if not all(vals.values()):
            failures.append(f"control bool {key}: not True in every engine {vals}")
    # numerics-consistency bools: gated for cross-engine agreement, tracked as a separate (lower) tier
    for key in NUMERICS_CONSISTENCY_BOOLS:
        vals = {n: ctl[n].get(key) for n in ctl}
        if len(set(json.dumps(v) for v in vals.values())) > 1:
            failures.append(f"numerics-consistency bool {key}: disagreement {vals}")
        if not all(vals.values()):
            failures.append(f"numerics-consistency bool {key}: not True in every engine {vals}")

    # GATING: load-bearing numeric values agree across engines within a discretization tolerance
    numeric_agreement = {"consistent": True, "mismatches": []}
    if ref:
        for key, tol in GATE_FLOAT_TOL.items():
            base = inv[ref].get(key)
            for n in inv:
                v = inv[n].get(key)
                if v is None or base is None or abs(v - base) > tol:
                    numeric_agreement["consistent"] = False
                    numeric_agreement["mismatches"].append(f"{key}: {n}={v} vs {ref}={base} (tol {tol})")
                    failures.append(f"numeric {key}: {n}={v} vs {ref}={base} exceeds tol {tol}")

    agreed = inv[ref] if ref else {}

    # the headline load-bearing discriminators, read from the (now agreed) per-engine results
    load_bearing_discriminators = {
        # the dynamic (Eulerian) loop enclosing curvature has NONtrivial holonomy in every engine
        "dynamic_eulerian_loop_nontrivial_all_engines": all(tst[n].get("dynamic_eulerian_holonomy_nontrivial") for n in tst),
        # ... and its phase equals the enclosed Berry flux (Stokes), not a free number
        "holonomy_equals_enclosed_flux_all_engines": all(tst[n].get("holonomy_equals_enclosed_flux") for n in tst),
        # comoving / Lagrangian frame -> trivial
        "direct_comoving_trivial_all_engines": all(tst[n].get("direct_lagrangian_holonomy_trivial") for n in tst),
        # the ANTI-BY-CONSTRUCTION control: a FLAT connection around the SAME loop is trivial in every
        # engine -> the nontrivial holonomy is forced by the enclosed CURVATURE, not the loop topology
        "flat_connection_same_loop_trivial_all_engines": all(ctl[n].get("flat_connection_same_loop_trivial") for n in ctl),
        "curvature_load_bearing_all_engines": all(ctl[n].get("curvature_load_bearing_curved_nontrivial_flat_trivial") for n in ctl),
        # shrink the loop -> holonomy -> I continuously
        "shrink_loop_to_identity_all_engines": all(ctl[n].get("shrink_loop_holonomy_to_identity") for n in ctl),
        # open path -> not gauge-invariant; closed loop -> gauge-invariant
        "open_path_gauge_dependent_all_engines": all(ctl[n].get("open_path_holonomy_gauge_dependent") for n in ctl),
        "closed_loop_gauge_invariant_all_engines": all(ctl[n].get("closed_holonomy_gauge_invariant") for n in ctl),
        # grok ODE: the geometric phase from integrating the actual Schrodinger ODE around the loop
        # (no solid-angle reference) MATCHES the link-product holonomy in every engine AND flips to ~0
        # for a flat loop (negative control). This is the GENUINE coordinate-baking resolver -- the
        # ODE legs are the only formula-independent cross-engine route (not the overlap-product).
        "ode_matches_link_product_all_engines": all(ctl[n].get("ode_holonomy_matches_link_product") for n in ctl),
        "ode_geometric_phase_nontrivial_all_engines": all(ctl[n].get("ode_geometric_phase_nontrivial") for n in ctl),
        "ode_flat_loop_trivial_all_engines": all(ctl[n].get("ode_flat_loop_trivial") for n in ctl),
        "ode_flips_curved_vs_flat_all_engines": all(ctl[n].get("ode_flips_curved_vs_flat") for n in ctl),
        # coordinate-baking resolved by flat-connection + ODE (NOT the self-authored colatitude knob)
        "coordinate_baking_resolved_all_engines": all(ctl[n].get("coordinate_baking_resolved_by_flat_and_ode") for n in ctl),
    }
    # numerics-consistency tier (re-tiered post-audit): the deepseek colatitude-knob. Agreed across
    # engines but NOT a load-bearing coordinate-baking discriminator (analytic identity + structural zero).
    numerics_consistency_checks = {
        "curvature_knob_numerics_consistent_all_engines": all(ctl[n].get("curvature_knob_numerics_consistent") for n in ctl),
        "curvature_knob_g0_degenerate_endpoint_all_engines": all(ctl[n].get("curvature_knob_g0_degenerate_endpoint_consistent") for n in ctl),
    }
    for k, ok in load_bearing_discriminators.items():
        if not ok:
            failures.append(f"discriminator {k} not satisfied")

    # ENGINE PRESENCE (re-tiered post-audit 2026-06-15): per project canon the CANONICAL engines are
    # exact (numpy reference) + jax + julia. PyTorch is SIDELINED -- it runs a real distinct route
    # (complex-tensor + tree-reduction ODE) and contributes to agreement WHEN present, but it is an
    # OPTIONAL fourth validation leg, NOT a required co-gater. The gate requires the three canonical
    # engines present and agreeing; a missing pytorch no longer flips agreement_ok to False.
    n_engines = len(inv)
    CANONICAL_ENGINES = ("exact", "jax", "julia")
    missing_canonical = [e for e in CANONICAL_ENGINES if e not in inv]
    if missing_canonical:
        failures.append(f"missing canonical engine(s) {missing_canonical}; canon path (exact+jax+julia) not complete")
    pytorch_present = "pytorch" in inv
    agreement_ok = (not failures)

    result = {
        "schema": "codex_ratchet.agreement_result.v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "agreement_ok": agreement_ok,
        "engines_present": sorted(inv.keys()),
        "n_engines": n_engines,
        "canonical_engines": list(CANONICAL_ENGINES),
        "canonical_engines_complete": not missing_canonical,
        "pytorch_optional_leg_present": pytorch_present,
        "agreed_invariants": agreed,
        "numeric_agreement": numeric_agreement,
        "load_bearing_discriminators": load_bearing_discriminators,
        "numerics_consistency_checks": numerics_consistency_checks,
        "by_construction_identities": {
            "load_bearing_controls_are_value_coupled": "the LOAD-BEARING controls (flat-connection same loop -> I, ODE-vs-link match + flat-loop flip) are value-coupled measurements that could come out the other way and do not.",
            "knob_g0_is_a_structural_zero": "POST-AUDIT (2026-06-15, 5 sonnet lenses): the deepseek colatitude-knob g=0 endpoint IS a by-construction structural zero -- alpha_g = 2*asin(sqrt(0)*sin(theta_cap/2)) = 0 -> sin(alpha_g/2)=0 -> the frame is phi-independent ([1,0] for all phi) -> U=I by sin(0)=0 for ANY constant frame (verified: a random constant frame also gives |U-I|=0). The phase=g*Omega/2 match is an ANALYTIC IDENTITY of the alpha_g formula (sin^2(alpha_g/2)=g*sin^2(theta_cap/2)), not an independent measurement. The knob is therefore re-tiered to NUMERICS-CONSISTENCY and is NOT counted among the load-bearing coordinate-baking discriminators."
        },
        "coordinate_baking_controls": {
            "fleet_flag": "the real fleet flagged that the Bloch frame V(theta,phi) is coordinate-hand-crafted, so the monopole flux Omega/2 might be baked into the GAUGE/coordinate choice rather than measuring enclosed dynamical CURVATURE.",
            "resolved_by": "RESOLVED by two value-coupled controls: (1) the phi-DEPENDENT flat-connection control (theta=0 winding around the SAME loop, same link rule -> |U-I|~6e-13 while the curved frame gives ~1.41) -- this is a phi-dependent flat frame (NOT a degenerate constant frame), so its triviality is forced by zero enclosed CURVATURE not by phi-independence; and (2) the grok ODE control -- integrating the actual time-dependent Schrodinger ODE i dpsi/dt=H(t)psi around the loop (NO solid-angle reference) MATCHES the link-product holonomy in magnitude (~3.7e-4 adiabatic 1/B residual) AND flips to ~0 for a flat loop (theta_cap=0). The ODE legs are the ONLY formula-independent cross-engine route (distinct integrators: numpy expm-loop, jax lax.scan, torch tree-reduction, julia sequential Rodrigues; agree to ~1e-6).",
            "deepseek_curvature_knob_NOT_a_resolver": "the deepseek colatitude-knob does NOT resolve coordinate-baking: phase=g*Omega/2 is an analytic identity of alpha_g and g=0 is a structural zero. It is a numerics-consistency check (link-product reproduces a family; catches a wrong frame formula -- alpha_g=g*theta_cap gives 0.421 at g=0.5 instead of 0.785) but it stays within the same hand-crafted Bloch-frame family. Re-tiered post-audit."
        },
        "cross_engine_independence_scope": {
            "numeric_agreement_is_correlated_for_holonomy_legs": "POST-AUDIT honesty: the four engines (exact/julia/jax/pytorch) all compute the holonomy via the SAME overlap-product / link-phase formula in distinct float paths (numpy complex division, julia arg/exp, jax vectorized prod, torch complex prod). Their NUMERIC agreement on the holonomy and knob legs reflects the same math in distinct float fingerprints (genuinely distinct -- e.g. flat-connection |U-I| spans ~1.4e-14 to ~6.5e-13 -- but CORRELATED through shared formula authorship), NOT four independent algorithmic derivations. The agreement of the discriminator BOOLEANS is real cross-language confirmation; the only genuinely formula-INDEPENDENT cross-engine route is the ODE (distinct integrators).",
        },
        "failures": failures,
        "honest_scope": {
            "earns": "four-engine (numpy/julia/jax/pytorch) cross-language AGREEMENT on the discriminator booleans that the Axis-2 K_t loop-holonomy is CURVATURE-COUPLED: a closed frame loop enclosing Berry curvature has nontrivial holonomy U_loop != I with phase magnitude = enclosed flux Omega/2 (matches Stokes to ~2e-7), while the comoving/Lagrangian, trivial (zero-area), and FLAT (pure-gauge, same loop) frames give the identity, the loop shrinks continuously to identity, and an open path is not gauge-invariant. The two load-bearing coordinate-baking resolvers are the phi-DEPENDENT flat-connection control and the formula-INDEPENDENT ODE control (matches link product + flips flat->0). This is the GENUINE Axis-2 frame discriminator the euler sim (ring_checkerboard_euler_conversion_axis2_frame_v0) failed to earn -- its K_direct/K_static=0 via @zeros and K_dynamic=||G|| were by-construction.",
            "does_not_earn": "M(C) admission, Axis0 closure, QIT engine, smooth manifold, or physics. The half-monopole Berry curvature is the standard spin-1/2 curvature, not a derived object. The deepseek colatitude-knob is a numerics-consistency check, NOT a coordinate-baking resolver (re-tiered post-audit 2026-06-15: phase=g*Omega/2 is an analytic identity, g=0 a structural zero). The four-engine NUMERIC agreement on the holonomy legs is correlated (same formula, distinct float paths); only the ODE is formula-independent across engines. Needs a fresh MULTI-MODEL FLEET box-viii audit (single fresh pipeline is insufficient -- a near-identical sibling was caught rigged only by the full fleet).",
        },
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"agreement_ok": agreement_ok, "n_engines": n_engines,
                      "engines": sorted(inv.keys()), "failures": failures}, indent=2))
    return 0 if agreement_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
