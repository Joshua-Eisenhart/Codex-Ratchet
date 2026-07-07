#!/usr/bin/env python3
"""engine_object_formation_scorecard -- a UNIFIED objective scorecard for the QIT engine stages/terrains, built on
the discipline in the owner's Lev object-formation mesh package (leviathan_object_formation_mesh_package_20260706):

  1. MEASUREMENT / VERDICT SEPARATION. The Lev dynamics-provider lane forbids an instrument from emitting
     pass/true/formed/admitted: "SINDy/Koopman propose dynamics evidence. Deterministic adapters convert it to
     measurements. Eval decides." So this file is split in two, cleanly:
        - measure_*  : PURE INSTRUMENTS. They read the measurements the two objective-target sims already emitted
          (re-identification + PySINDy dynamics-ID) and convert them to a formation-loss surface. They emit
          NUMBERS ONLY -- never a verdict.
        - eval_formation : a SEPARATE named policy that reads the emitted measurements and decides. The policy is
          explicit and lives OUTSIDE the instrument, so the pass criterion cannot be tuned by editing the measure.
     This is the structural fix for the gate-tuning cascade (UP-72b/72c): a gate the instrument does not contain
     cannot be relaxed after a fail.

  2. OBJECTHOOD IS A FORMATION LOSS, NOT A BOOLEAN (Lev 04_loss_functions gives the SHAPE):
        formation_loss = handling_loss + convergence_loss + (recall/anti-key/attention terms, N/A for engines)
     and the two objective targets already built map onto two of those components:
        - convergence_loss  <- engine_reidentification_objective (convergence across independent probe paths)
        - handling_loss     <- engine_dynamics_id_arbiter (cheaper to predict under handling = external SINDy fit)
     ATTRIBUTION, STATED HONESTLY (per auditor): this is an ADAPTATION of the Lev loss surface to the engine
     domain, not a literal port. The Lev TS formationLoss() uses a handling term tiered on a before/after
     `handlingLossDelta` trend; a closed engine has no before/after handling episodes, so the handling component
     here is an ENGINE-DOMAIN PROXY: max(0, 1 - heldout_R^2) from the external arbiter ("cheaper to predict under
     handling" rendered as external-fit quality). The convergence term keeps the Lev form 5*(1 - rate) exactly.
     So: Lev supplies the loss STRUCTURE (additive components, convergence as 5*(1-rate)); the handling term is a
     domain proxy, labelled as such, not claimed as the literal TS formula.

QUARANTINE_EXPLORATORY. classification="scratch_diagnostic". promotion_allowed=False.
NOT about Lev -- the mesh package supplies the MEASUREMENT DISCIPLINE; the objects measured are the QIT engines.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REID = os.path.join(HERE, "engine_reidentification_objective_sim_results.json")
SINDY = os.path.join(HERE, "engine_dynamics_id_arbiter_sim_results.json")

# ---- the Lev object-formation policy (SEPARATE from the instruments; the eval layer, not the measurement) ----
# forbidden instrument outputs, quoted from docs/09_dynamics_provider_lane.md -- an instrument that emits any of
# these is not a measurement, it is a smuggled verdict.
FORBIDDEN_INSTRUMENT_OUTPUTS = ("pass", "true", "formed", "admitted", "object_exists")

# ---------------------------------- PURE INSTRUMENTS (emit numbers only) ----------------------------------

def measure_convergence_loss(reid):
    """convergence_loss from the re-identification measurements. Lev loss doc: loss falls as convergence rate
    rises. convergence rate = fraction of stages that re-identify across independent (never-seen) probe paths.
    Emits the loss component AND the raw control evidence -- NO verdict."""
    rate = reid["real_reidentification_rate_novel_probes"]
    return {
        "convergence_rate": rate,                                   # k/n across independent probe paths
        "convergence_loss": 5.0 * (1.0 - rate),                     # Lev form: 5*(1 - rate)
        "negative_control_result": {                                # the control that must flip (evidence, not verdict)
            "shuffled_mean_rate": reid["shuffled_control_mean_rate"],
            "shuffled_max_rate": reid["shuffled_control_max_rate"],
            "chance_rate": reid["chance_rate"],
            "separation_real_minus_shuffled": reid["separation_real_minus_shuffled"],
        },
        "objects_that_failed_convergence": reid["stages_that_failed_reid"],
    }

def measure_handling_loss(sindy):
    """handling_loss (ENGINE-DOMAIN PROXY) from the PySINDy dynamics-ID measurements. The Lev loss doc's intent is
    'an object is more object-like as it gets cheaper to predict under handling'; its literal TS term is tiered on
    a before/after handlingLossDelta trend, which a closed engine (no handling episodes) does not have. So here
    cheaper-to-predict is rendered as external-fit quality: handling_loss per terrain = max(0, 1 - heldout_R^2)
    (0 for a perfect external fit, grows as the fit fails). This is a proxy for the Lev term, not the TS formula.
    NO verdict emitted."""
    per = []
    for pt in sindy["per_terrain"]:
        r2 = pt["real_r2"]
        per.append({
            "t": pt["t"],
            "heldout_error_proxy_1_minus_r2": 1.0 - r2,
            "handling_loss": max(0.0, 1.0 - r2),
            "control_sensitivity_shuffled_time_r2": pt["shuffled_time_r2"],   # the negative control, per terrain
        })
    return {
        "per_terrain": per,
        "handling_loss_mean": sum(p["handling_loss"] for p in per) / len(per),
        "real_beats_shuffled_every_terrain": sindy["real_beats_shuffled_every_terrain"],
    }

def formation_loss_surface(conv, hand):
    """Compose the two components into the Lev formation-loss surface. Recall/anti-key/attention terms are N/A for
    a closed engine (no external sources, no memory cache), and are recorded as such rather than faked."""
    return {
        "convergence_loss": conv["convergence_loss"],
        "handling_loss_mean": hand["handling_loss_mean"],
        "recall_loss": None, "anti_key_penalty": None, "attention_leak_penalty": None,  # N/A for a closed engine
        "formation_loss_defined_components_sum": conv["convergence_loss"] + hand["handling_loss_mean"],
    }

# ---------------------------------- SEPARATE POLICY EVAL (decides) ----------------------------------

def eval_formation(conv, hand):
    """The eval layer -- SEPARATE from the instruments above. It reads the emitted measurements and decides.
    ATTRIBUTION (per auditor): the criterion here is the NEGATIVE-CONTROL section of docs/09_dynamics_provider
    _lane.md ('shuffled-time trace breaks dynamics model', 'constant/seed prior loses on heldout ticks'), applied
    to BOTH lanes -- NOT the object-formation.policy.yaml `requiredControls` list (single-pipeline replay, hash-only
    identity, anti-key ingress, attention-weight leakage), which concern a multi-source mesh with memory and do
    not apply to a closed engine. So: both independent negative controls must break. No formation-loss threshold
    is picked here (the loss is REPORTED, a measurement surface for a downstream GatePolicy, per the Lev loss doc)."""
    conv_control_flips = (conv["negative_control_result"]["shuffled_max_rate"]
                          < conv["convergence_rate"])                       # real beats every scramble
    hand_control_flips = hand["real_beats_shuffled_every_terrain"]          # real beats shuffled-time each terrain
    both_controls_flip = bool(conv_control_flips and hand_control_flips)
    return {"convergence_control_flips": conv_control_flips,
            "handling_control_flips": hand_control_flips,
            "BOTH_INDEPENDENT_CONTROLS_FLIP": both_controls_flip}

def main():
    if not (os.path.exists(REID) and os.path.exists(SINDY)):
        print("MISSING measurement inputs; run engine_reidentification_objective + engine_dynamics_id_arbiter first")
        sys.exit(2)
    reid = json.load(open(REID)); sindy = json.load(open(SINDY))

    conv = measure_convergence_loss(reid)
    hand = measure_handling_loss(sindy)
    surface = formation_loss_surface(conv, hand)
    verdict = eval_formation(conv, hand)

    out = {"classification": "scratch_diagnostic", "promotion_allowed": False,
           "discipline": "Lev object-formation mesh package: measurement/verdict separation + objecthood-as-loss",
           "convergence_lane": conv, "handling_lane": hand,
           "formation_loss_surface": surface, "policy_eval": verdict}
    path = __file__.replace(".py", "_results.json"); json.dump(out, open(path, "w"), indent=1)

    print("OBJECT-FORMATION SCORECARD -- two independent external targets composed into one formation-loss surface.")
    print("  discipline (Lev mesh pkg): instruments emit MEASUREMENTS; a SEPARATE policy eval decides.\n")
    print("  INSTRUMENT: convergence lane (re-identification across never-seen probe paths)")
    print(f"    convergence_rate {conv['convergence_rate']:.3f}  -> convergence_loss {conv['convergence_loss']:.3f}")
    print(f"    negative control: shuffled max {conv['negative_control_result']['shuffled_max_rate']:.3f} vs chance {conv['negative_control_result']['chance_rate']:.3f}")
    print("  INSTRUMENT: handling lane (external PySINDy dynamics-ID under handling)")
    print(f"    handling_loss_mean {hand['handling_loss_mean']:.3f}  (per-terrain 1-R^2; t3 projective is the outlier)")
    print(f"\n  FORMATION-LOSS SURFACE (reported, not gated): defined-components sum = {surface['formation_loss_defined_components_sum']:.3f}")
    print(f"    convergence_loss {surface['convergence_loss']:.3f} + handling_loss_mean {surface['handling_loss_mean']:.3f}")
    print(f"    (recall/anti-key/attention terms N/A for a closed engine)")
    print("\n  SEPARATE POLICY EVAL (the ONLY verdict; criterion = both independent controls flip):")
    print(f"    convergence control flips: {verdict['convergence_control_flips']}")
    print(f"    handling control flips   : {verdict['handling_control_flips']}")
    print(f"    BOTH INDEPENDENT CONTROLS FLIP: {verdict['BOTH_INDEPENDENT_CONTROLS_FLIP']}")
    if verdict["BOTH_INDEPENDENT_CONTROLS_FLIP"]:
        print("PASS engine_object_formation_scorecard")
    print("ALL_GATES:", "PASS" if verdict["BOTH_INDEPENDENT_CONTROLS_FLIP"] else "FAIL", "->", path)
    sys.exit(0 if verdict["BOTH_INDEPENDENT_CONTROLS_FLIP"] else 1)

if __name__ == "__main__":
    main()
