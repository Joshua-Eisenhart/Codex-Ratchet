#!/usr/bin/env python3
"""
Validator for retrocausal_possibility_field_carrier_grounded_v0.

Re-derives the load-bearing facts FRESH from the sim module + the frozen M(C) carrier
rather than trusting the stored result booleans. Asserts:

  1. The carrier is the REAL frozen M(C): 16 survivors loaded from the carve result,
     each a genuine PSD trace-1 density matrix, with the carve provenance sha present.
  2. The observable-sign classes under C=(sigma_x,sigma_z) RE-DERIVE the carve's 8
     quotient classes (the quotient is reproduced from the carrier, not stipulated).
  3. THE ACCEPTANCE GATE: re-run the three selectors fresh; the global compressor
     survivor differs from BOTH forward greedy selectors (retrocausal_earned).
  4. THE HARD ACCEPTANCE -- CONSTRAINT SURGERY: re-run with C and C'=C+sigma_y; assert
     the carrier digest is byte-identical (held rigidly fixed) AND the present survivor
     MOVES. Independently recompute the global survivor under each probe family.
  5. The canonical partition matches the deterministic lexicographic-first selection
     rule (not hand-tuned).
  6. The uniform (empty observable family) control collapses the earned probe.
  7. The ceiling is scratch_diagnostic / promotion_allowed=false /
     formal_admission_allowed=false, and the result JSON's stored facts match the
     fresh recomputation.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys

SIM_DIR = os.path.dirname(os.path.abspath(__file__))
MODULE_PATH = os.path.join(SIM_DIR, "retrocausal_possibility_field_carrier_grounded_v0.py")
RESULT_PATH = os.path.join(SIM_DIR, "results", "retrocausal_possibility_field_carrier_grounded_v0_results.json")


def load_module():
    spec = importlib.util.spec_from_file_location("rpf_carrier_grounded_v0", MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    errors: list[str] = []
    checks: dict[str, bool] = {}

    def require(name: str, cond: bool) -> None:
        checks[name] = bool(cond)
        if not cond:
            errors.append(name)

    m = load_module()

    # --- fresh recomputation from the module + frozen carrier ---
    carrier = m.load_frozen_carrier()
    shells = m.CANONICAL_SHELLS_OUTER_TO_INNER

    # 1. real frozen M(C) carrier
    require("carrier_16_survivors", carrier["carve_survivor_count"] == 16 and len(carrier["branch_ids"]) == 16)
    require("all_density_matrices_valid_recomputed", bool(carrier["all_density_matrices_valid"]))
    # re-verify validity directly (don't trust the loader flag)
    revalid = all(
        m.is_valid_density_matrix(m.rho_of(carrier, b)) for b in carrier["branch_ids"]
    )
    require("density_matrices_revalidated_directly", revalid)
    require("carve_provenance_sha_present", bool(carrier.get("carve_result_sha256")))

    # 2. observable-sign classes reproduce the carve's 8 quotient classes
    classes_C = m.signature_classes(carrier, m.PROBE_FAMILY_C)
    require("observable_sign_classes_reproduce_8_quotient",
            len(classes_C) == 8 == carrier["carve_quotient_class_count"])

    # 3. acceptance gate (fresh)
    fwd = m.forward_single_anchor(carrier, shells, m.PROBE_FAMILY_C)
    fwd_h = m.forward_full_history(carrier, shells, m.PROBE_FAMILY_C)
    glob = m.global_compressor(carrier, shells, m.PROBE_FAMILY_C)
    differs_single = fwd["present_survivor"] != glob["present_survivor"]
    differs_hist = fwd_h["present_survivor"] != glob["present_survivor"]
    require("global_differs_from_single_anchor_forward", differs_single)
    require("global_differs_from_full_history_forward", differs_hist)
    require("retrocausal_earned_recomputed", differs_single and differs_hist)

    # 4. HARD ACCEPTANCE -- constraint surgery (fresh, independently recomputed)
    glob_C = m.global_compressor(carrier, shells, m.PROBE_FAMILY_C)
    glob_Cp = m.global_compressor(carrier, shells, m.PROBE_FAMILY_C_SURGERY)
    # carrier digest must be byte-identical before/after (only the probe family changed)
    coords_before = sorted([carrier["branch_states"][b]["bloch_coord"] for b in carrier["branch_ids"]])
    digest_before = m.sha256_text(m.canonical_json(coords_before))
    coords_after = sorted([carrier["branch_states"][b]["bloch_coord"] for b in carrier["branch_ids"]])
    digest_after = m.sha256_text(m.canonical_json(coords_after))
    require("carrier_held_rigidly_fixed", digest_before == digest_after
            and digest_before == carrier["carrier_bloch_digest"])
    require("coadm_relation_changed_under_surgery",
            len(m.signature_classes(carrier, m.PROBE_FAMILY_C))
            != len(m.signature_classes(carrier, m.PROBE_FAMILY_C_SURGERY)))
    require("CONSTRAINT_SURGERY_MOVES_SURVIVOR",
            glob_C["present_survivor"] != glob_Cp["present_survivor"])

    # 5. canonical partition deterministic-rule match
    canonical = m.select_canonical_partition(carrier)
    require("canonical_partition_matches_deterministic_rule",
            bool(canonical["frozen_matches_recomputed_canonical"]))

    # 6. uniform (empty observable family) control collapses the probe
    uniform = m.uniform_observable_control(carrier, shells)
    require("uniform_observable_kills_probe", bool(uniform["degenerate_correctly_kills_probe"]))

    # 7. ceiling + stored-result consistency
    if not os.path.exists(RESULT_PATH):
        require("result_json_exists", False)
    else:
        with open(RESULT_PATH, "r", encoding="utf-8") as f:
            res = json.load(f)
        require("result_json_exists", True)
        require("classification_scratch_diagnostic", res.get("classification") == "scratch_diagnostic")
        require("promotion_allowed_false", res.get("promotion_allowed") is False)
        require("formal_admission_allowed_false", res.get("formal_admission_allowed") is False)
        require("stored_all_invariants_hold", res.get("all_invariants_hold") is True)
        # stored facts match the fresh recomputation
        require("stored_surgery_survivor_before_matches",
                res.get("constraint_surgery_present_survivor_before") == glob_C["present_survivor"])
        require("stored_surgery_survivor_after_matches",
                res.get("constraint_surgery_present_survivor_after") == glob_Cp["present_survivor"])
        require("stored_global_survivor_matches",
                res.get("ACCEPTANCE_GATE", {}).get("present_survivor_global") == glob["present_survivor"])
        require("stored_constraint_surgery_moves_survivor",
                res.get("constraint_surgery_moves_survivor") is True)

    ok = not errors
    print(json.dumps({
        "ok": ok,
        "validator": "retrocausal_possibility_field_carrier_grounded_v0",
        "present_survivor_global_C": glob["present_survivor"],
        "present_survivor_forward_single_C": fwd["present_survivor"],
        "present_survivor_global_Cprime": glob_Cp["present_survivor"],
        "constraint_surgery_moves_survivor": glob_C["present_survivor"] != glob_Cp["present_survivor"],
        "observable_sign_class_count_C": len(classes_C),
        "checks": checks,
        "errors": errors,
    }, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
