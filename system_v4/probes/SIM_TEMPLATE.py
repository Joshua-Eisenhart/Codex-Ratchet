#!/usr/bin/env python3
"""
SIM TEMPLATE -- All new sims must start from this template.
See system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md for rules.

Harness framing (nominalist constraint-admissibility):
  This sim is a probe, not a proof. It tests which configurations survive
  under constraint set C and probe family M. Survivors remain candidates;
  they are not confirmed. What is excluded under C is the primary signal.

  Status ladder: exists < runs < passes local rerun < canonical by process
  Never report "all pass" without naming which criteria were checked.
  At least one tool outside the numeric baseline must be load-bearing.

Usage:
  1. Copy this file to sim_<your_name>.py
  2. Rename "TEMPLATE" throughout
  3. Name the probe family M and constraint set C for this sim
  4. Implement admission tests, exclusion tests, and boundary probes
  5. Update TOOL_MANIFEST: tried=True for every tool attempted, reason non-empty
  6. Record which tools are load-bearing for the actual admissibility claim
  7. If using Julia/JAX/PyTorch foreign runtimes, fill FOREIGN_RUNTIME_MANIFEST
     and canon_runtime without bypassing this Python receipt layer
  8. Run locally, confirm exit 0, write result JSON, then report status label
"""

import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST -- Document which tools were tried
# =====================================================================

TOOL_MANIFEST = {
    # --- Computation layer ---
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    # --- Foreign runtime / Canon layer ---
    "julia": {"tried": False, "used": False, "reason": ""},
    "jax": {"tried": False, "used": False, "reason": ""},
    "dlpack": {"tried": False, "used": False, "reason": ""},
    "pythoncall": {"tried": False, "used": False, "reason": ""},
    # --- Proof layer ---
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    # --- Symbolic layer ---
    "sympy": {"tried": False, "used": False, "reason": ""},
    # --- Geometry layer ---
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    # --- Graph layer ---
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    # --- Topology layer ---
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

# Record actual integration depth, not just import presence.
# Each entry should be one of:
# - "load_bearing"  : the result materially depends on this tool
# - "supportive"    : useful cross-check/helper but not decisive
# - "decorative"    : present only at manifest/import level (avoid this)
TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "julia": None,
    "jax": None,
    "dlpack": None,
    "pythoncall": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

# Foreign runtime manifest keeps Julia/JAX/PyTorch bridge work compatible with
# the existing Python probe/result surface. Import success is not integration;
# fill these entries only when an actual bridge or runtime call is made.
FOREIGN_RUNTIME_MANIFEST = {
    "julia": {
        "tried": False,
        "used": False,
        "integration_depth": None,
        "reason": "",
    },
    "jax": {
        "tried": False,
        "used": False,
        "integration_depth": None,
        "reason": "",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "integration_depth": None,
        "reason": "",
    },
    "dlpack": {
        "tried": False,
        "used": False,
        "integration_depth": None,
        "reason": "",
    },
}

# Canon runtime contract for probes that call Julia-owned algebra/proof/basin
# artifacts. See system_v5/docs/JULIA_CANON_RUNTIME_CONTRACT.md.
CANON_RUNTIME = {
    "semantic_owner": "not_scoped",          # usually "julia" when used
    "accelerators": [],                     # e.g. ["pytorch", "jax"]
    "tensor_exchange": "not_scoped",       # dlpack|typed_binary|not_scoped
    "forbidden_exchange": [".numpy()", "np.asarray", "pickle", "csv", "pandas"],
    "algebra_artifact_path": "not_scoped",
    "algebra_artifact_sha256": "not_scoped",
    "table_version": "not_scoped",
    "bracket_policy": "not_scoped",
    "proof_surface": "not_scoped",
    "proof_promotion": "not_promoted_until_certified",
    "promotion_blockers": [],
}

# Try importing each tool
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import *  # noqa: F401,F403
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp  # noqa: F401
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi  # noqa: F401
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# ADMISSION TESTS
# Probe family M: [name the probes used here]
# Constraint set C: [name the constraints being tested]
#
# Which configurations survive under C? State these results as:
#   "candidate X survived probe M under constraint C"
#   "candidate X is admissible under C" (not "test passes")
#
# Each admission test requires:
#   - Multiple candidate states (not just one)
#   - Expected admissibility value from theory or prior constraint analysis
#   - Cross-check against a second probe or method
#   - A surviving-alternatives note: what else could be admitted?
# =====================================================================

def run_positive_tests():
    results = {}
    # Under probe family M, which states are admitted by constraint C?
    # Record: candidate, probe output, admissibility status, surviving alternatives
    # Preferred language: "survived", "admitted", "indistinguishable under M"
    # Avoid: "passes", "works", "confirms", "proves"
    return results


# =====================================================================
# EXCLUSION TESTS (mandatory — primary signal)
# Constraint set C: [same as above]
#
# What does C exclude? Exclusion is the primary proof form here.
# Use z3 UNSAT where possible: structural impossibility is stronger
# than empirical absence.
#
# Each exclusion test requires:
#   - A configuration that should be excluded under C
#   - Evidence of exclusion (UNSAT, failed probe, boundary violation)
#   - Why this exclusion matters for the admissibility claim
#   - Whether the exclusion is formal (z3/cvc5 UNSAT) or empirical
# =====================================================================

def run_negative_tests():
    results = {}
    # Under constraint set C, which configurations are excluded?
    # Record: candidate, exclusion evidence, exclusion type (formal/empirical)
    # Preferred language: "excluded under C", "UNSAT under C", "inadmissible"
    # Avoid: "fails", "wrong", "broken", "negative"
    return results


# =====================================================================
# BOUNDARY PROBES
# Probe family M: [same as above]
#
# Where does probe family M fail to distinguish candidates?
# These are the edges of the admissibility region — where the
# constraint surface becomes thin and the probe loses resolution.
#
# Each boundary probe requires:
#   - A configuration near the boundary of admissibility under C
#   - What M returns at this boundary
#   - Whether the boundary is sharp (formal) or gradient (empirical)
#   - Numerical precision analysis if relevant
# =====================================================================

def run_boundary_tests():
    results = {}
    # Where does M fail to distinguish? Where does C become ambiguous?
    # Record: configuration, probe output at boundary, boundary type
    # Note: boundary indistinguishability is a result, not a failure
    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    # Harness status discipline:
    #   classification "classical_baseline" = numpy-era, not canonical by process
    #   classification "canonical" = torch-native + template-compliant + load-bearing tool
    #   Never set "canonical" without: SIM_TEMPLATE conformance + tool manifest with
    #   non-empty reasons + at least one load-bearing non-baseline tool + passes local rerun
    #
    # Result keys use existing names for parser compatibility.
    # Nominalist framing: "positive" = admitted configurations under C
    #                     "negative" = excluded configurations under C
    #                     "boundary" = boundary probes where M loses resolution
    results = {
        "name": "TEMPLATE -- RENAME THIS",
        # probe_family: name the active probe family M for this sim
        "probe_family": "M_UNNAMED",
        # constraint_set: name the active constraint set C for this sim
        "constraint_set": "C_UNNAMED",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "foreign_runtime_manifest": FOREIGN_RUNTIME_MANIFEST,
        "canon_runtime": CANON_RUNTIME,
        "positive": run_positive_tests(),   # admitted configurations under C
        "negative": run_negative_tests(),   # excluded configurations under C
        "boundary": run_boundary_tests(),   # boundary probes (M indistinguishable)
        "classification": "classical_baseline",  # or "canonical" — see rules above
        # surviving_alternatives: what other candidates remain admissible?
        # Do not leave empty if any alternatives exist.
        "surviving_alternatives": [],
        # Claim ceiling fields bind this receipt to one safe promotion boundary.
        # Use "none" for next_lego_target when no lego target is unlocked.
        "claim_ceiling": "classical_baseline_only",
        "next_lego_target": "none",
        "promotion_condition": "requires a separate reconciled queue row before lego/coupling use",
        "blocked_until": "exact parent receipts, queue row, result JSON, and ledger loopback are reconciled",
        "demotion_condition": "demote if any named criterion fails or if the result claims outside the stated ceiling",
        "out_of_scope": [
            "no lego promotion from this template result alone",
            "no bridge, axis, engine, emergence, Tier D, or scientific coupling claim",
        ],
        # all_pass: True only if all admission tests survived AND
        #           all exclusion tests confirmed exclusion AND
        #           criteria are named explicitly below
        "all_pass": False,
        "criteria_checked": [],  # list exactly which criteria C1/C2/etc were checked
    }

    # Update TOOL_MANIFEST entries: tried=True for each tool attempted; used=True
    # only for tools that actually affect the result. Every tried/used tool needs
    # a non-empty reason.
    # Update TOOL_INTEGRATION_DEPTH: "load_bearing" / "supportive" / None

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "TEMPLATE_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
