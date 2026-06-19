#!/usr/bin/env python3
"""Agreement adjudicator for region_discovery_from_observables_v0.

This script reads the exact and JAX result JSONs only. It does not recompute the
regions and does not promote the sim. agreement_ok gates on both legs passing
their own tests/controls and on exact equality of the finite quotient structure
fingerprints and value-change controls.
"""

from __future__ import annotations

import json
from pathlib import Path

SIM_ID = "region_discovery_from_observables_v0"
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
OUT = RESULTS / f"{SIM_ID}_agreement_results.json"
LEGS = {
    "exact": RESULTS / f"{SIM_ID}_exact_results.json",
    "jax": RESULTS / f"{SIM_ID}_jax_results.json",
}

GATE_TEST_BOOLS = [
    "no_terrain_labels_consumed_in_region_computation",
    "nonuniversal_threshold_relation",
    "discovers_inequality_regions",
    "discovers_connected_components",
    "cell_membership_total",
    "equivalence_classes_cover_probe_quotient",
]

GATE_CONTROL_BOOLS = [
    "label_shuffle_structure_invariant",
    "label_shuffle_display_names_changed",
    "observable_perturbation_changes_region_membership",
    "value_change_control_moves_boundaries",
    "value_change_changes_component_count",
    "value_change_not_label_change",
]

GATE_INVARIANTS = [
    "grid_shape",
    "n_probe_cells",
    "equivalence_relation_name",
    "threshold_signature_name",
    "base_n_signatures",
    "base_n_components",
    "base_component_sizes",
    "base_boundary_edges_count",
    "base_structure_hash",
    "label_shuffle_structure_hash",
    "perturbed_n_signatures",
    "perturbed_n_components",
    "perturbed_component_sizes",
    "perturbed_boundary_edges_count",
    "perturbed_structure_hash",
    "value_changed_cell_ids",
    "value_changed_cell_coords_xy",
    "boundary_edge_symmetric_difference_count",
]


def main() -> int:
    failures: list[str] = []
    legs = {}
    for name, path in LEGS.items():
        if not path.exists():
            failures.append(f"{name}: missing result JSON {path.name}")
            continue
        legs[name] = json.loads(path.read_text())

    for name, obj in legs.items():
        if obj.get("classification") != "scratch_diagnostic":
            failures.append(f"{name}: classification={obj.get('classification')}")
        if obj.get("promotion_allowed") is not False:
            failures.append(f"{name}: promotion_allowed not false")
        if obj.get("formal_admission_allowed") is not False:
            failures.append(f"{name}: formal_admission_allowed not false")
        if obj.get("all_tests_pass") is not True:
            failures.append(f"{name}: all_tests_pass not true")
        if obj.get("all_controls_pass") is not True:
            failures.append(f"{name}: all_controls_pass not true")

    tests = {name: obj.get("tests", {}) for name, obj in legs.items()}
    controls = {name: obj.get("controls", {}) for name, obj in legs.items()}
    invariants = {name: obj.get("invariants", {}) for name, obj in legs.items()}
    ref = "exact" if "exact" in invariants else next(iter(invariants), None)

    for key in GATE_TEST_BOOLS:
        vals = {name: tests[name].get(key) for name in tests}
        if len(set(json.dumps(v, sort_keys=True) for v in vals.values())) > 1:
            failures.append(f"test bool {key}: disagreement {vals}")
        if not vals or not all(vals.values()):
            failures.append(f"test bool {key}: not true in every leg {vals}")

    for key in GATE_CONTROL_BOOLS:
        vals = {name: controls[name].get(key) for name in controls}
        if len(set(json.dumps(v, sort_keys=True) for v in vals.values())) > 1:
            failures.append(f"control bool {key}: disagreement {vals}")
        if not vals or not all(vals.values()):
            failures.append(f"control bool {key}: not true in every leg {vals}")

    invariant_agreement = {"consistent": True, "mismatches": []}
    if ref:
        for key in GATE_INVARIANTS:
            base = invariants[ref].get(key)
            for name in invariants:
                value = invariants[name].get(key)
                if value != base:
                    invariant_agreement["consistent"] = False
                    msg = f"{key}: {name}={value!r} vs {ref}={base!r}"
                    invariant_agreement["mismatches"].append(msg)
                    failures.append(f"invariant {msg}")

    load_bearing_discriminators = {
        "label_shuffle_structure_invariant_all_legs": all(
            controls[name].get("label_shuffle_structure_invariant") for name in controls
        ),
        "value_change_moves_boundaries_all_legs": all(
            controls[name].get("value_change_control_moves_boundaries") for name in controls
        ),
        "observable_perturbation_changes_membership_all_legs": all(
            controls[name].get("observable_perturbation_changes_region_membership") for name in controls
        ),
        "same_structure_hash_across_exact_and_jax": bool(
            invariant_agreement["consistent"]
            and ref
            and invariants[ref].get("base_structure_hash") == invariants[ref].get("label_shuffle_structure_hash")
        ),
        "perturbed_structure_differs_from_base": bool(
            ref and invariants[ref].get("base_structure_hash") != invariants[ref].get("perturbed_structure_hash")
        ),
    }
    for key, ok in load_bearing_discriminators.items():
        if not ok:
            failures.append(f"discriminator {key} not satisfied")

    n_legs = len(legs)
    agreement_ok = (not failures) and n_legs == 2
    if n_legs < 2:
        failures.append(f"only {n_legs}/2 legs present")

    result = {
        "schema": "codex_ratchet.agreement_result.v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "agreement_ok": agreement_ok,
        "legs_present": sorted(legs.keys()),
        "n_legs": n_legs,
        "agreed_invariants": invariants.get(ref, {}),
        "invariant_agreement": invariant_agreement,
        "load_bearing_discriminators": load_bearing_discriminators,
        "equivalence_relation": {
            "name": invariants.get(ref, {}).get("equivalence_relation_name"),
            "threshold_signature_name": invariants.get(ref, {}).get("threshold_signature_name"),
            "explicit_not_universal": all(tests[name].get("nonuniversal_threshold_relation") for name in tests),
        },
        "anti_fabrication": {
            "no_by_construction_tests": "the value-change control recomputes regions after changing o0 data values; if no threshold cells crossed or boundaries moved, the leg exits nonzero",
            "label_shuffle_is_invariance_only": "display-name permutation is checked separately and cannot satisfy the value-change boundary movement gate",
            "label_shuffle_could_fail": "the structure hash is a projection of the SAME label-carrying discovery onto structural keys (cells/membership/edges/signature_code); a label leak into any structural field flips the hash under a shuffle, so label_shuffle_structure_invariant is not by-construction",
            "no_terrain_labels_runtime_checked": "no_terrain_labels_consumed_in_region_computation is computed at runtime by discovering the same observables under two different label maps and comparing the structural projection byte-for-byte; it is not a hardcoded literal and flips to False if labels contaminate the region computation",
        },
        "failures": failures,
        "honest_scope": {
            "earns": "two-leg local agreement that finite L12 region discovery can be computed from observable threshold readouts alone: inequality regions, A4 connected components, cell memberships, and quotient equivalence classes agree exactly; label shuffling preserves structure; real o0 value perturbation moves boundaries.",
            "does_not_earn": "formal L12 admission, smooth manifold result, terrain-labeled segmentation, canonical promotion, or any claim beyond scratch_diagnostic.",
        },
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "agreement_ok": agreement_ok,
        "n_legs": n_legs,
        "legs": sorted(legs.keys()),
        "failures": failures,
    }, indent=2))
    return 0 if agreement_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
