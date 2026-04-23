"""Shared template for Tier D boundary admissibility probes.

Per system_v5/ops/TIER_D.md, each boundary (D1–D4) produces UNSAT certificates
proving structural impossibility at layer composition boundaries.

Opus-authored symbolic skeleton. Tier D Sonnet workers fill in the
boundary-specific predicates and witness candidates.

Per harness/07 (z3_unsat_primacy): UNSAT is the primary deliverable;
SAT on the positive section is only supporting.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable

# Available under codex-ratchet env
import z3
import sympy as sp


# ============================================================================
# Certificate dataclass
# ============================================================================


@dataclass
class UNSATCertificate:
    """A structural-impossibility proof at a layer boundary.

    Per harness/02: existence (SAT) is contingent; UNSAT is structural.
    """
    boundary: str              # e.g. "g_to_hopf"
    candidate_description: str # what is being excluded
    lower_structure: str       # description of the layer-below structure
    predicate_text: str        # human-readable admissibility predicate
    z3_result: str             # "unsat" | "sat" | "unknown"
    proof_hash: str            # hash of the encoded formula
    interpretation: str        # what the UNSAT means geometrically
    anti_tautology_passed: bool
    anti_tautology_reasoning: str

    def as_dict(self) -> dict:
        return {
            "boundary": self.boundary,
            "candidate_description": self.candidate_description,
            "lower_structure": self.lower_structure,
            "predicate_text": self.predicate_text,
            "z3_result": self.z3_result,
            "proof_hash": self.proof_hash,
            "interpretation": self.interpretation,
            "anti_tautology_passed": self.anti_tautology_passed,
            "anti_tautology_reasoning": self.anti_tautology_reasoning,
        }


@dataclass
class BoundaryAdmissibilityReport:
    """Full report for a single boundary (one of D1–D4)."""
    boundary: str
    positive_admissible: list[dict] = field(default_factory=list)  # SAT witnesses
    negative_unsat: list[UNSATCertificate] = field(default_factory=list)
    boundary_edge: list[dict] = field(default_factory=list)        # edge cases

    def to_result_dict(self) -> dict:
        return {
            "boundary": self.boundary,
            "positive_admissible": self.positive_admissible,
            "negative_unsat": [c.as_dict() for c in self.negative_unsat],
            "boundary_edge": self.boundary_edge,
            "anti_tautology_check": {
                "passed": all(c.anti_tautology_passed for c in self.negative_unsat),
                "reasoning": "; ".join(
                    c.anti_tautology_reasoning for c in self.negative_unsat
                ),
            },
        }


# ============================================================================
# Anti-tautology check helpers
# ============================================================================


def anti_tautology_check(
    *,
    encoding_description: str,
    lower_structure_used: bool,
    witness_is_physical: bool,
    axioms_are_standard: bool,
) -> tuple[bool, str]:
    """Check that an UNSAT result is not a tautology.

    Per harness/07 and TIER_D.md §anti-tautology:
    - UNSAT must reference the lower-layer structure
    - UNSAT must not come from axioms contradictory only for this proof
    - Should have a physically meaningful witness of exclusion
    """
    reasons = []
    if not lower_structure_used:
        reasons.append("UNSAT derivable without lower-layer reference; boundary claim invalid")
    if not axioms_are_standard:
        reasons.append("UNSAT from non-standard axioms added only for this proof; tautology")
    if not witness_is_physical:
        reasons.append("No physically meaningful witness of the exclusion; weak certificate")
    passed = all([lower_structure_used, axioms_are_standard, witness_is_physical])
    reasoning = (
        f"encoding: {encoding_description}; "
        + ("PASS" if passed else "FLAGS: " + "; ".join(reasons))
    )
    return passed, reasoning


def hash_formula(*parts) -> str:
    """Simple content hash for a formula's serialization."""
    import hashlib
    s = "|".join(str(p) for p in parts)
    return hashlib.sha256(s.encode()).hexdigest()[:16]


# ============================================================================
# Z3 encoding helper
# ============================================================================


def solve_with_z3(formula, timeout_ms: int = 10_000) -> str:
    """Run z3 on a formula; return 'unsat' | 'sat' | 'unknown'."""
    s = z3.Solver()
    s.set("timeout", timeout_ms)
    s.add(formula)
    res = s.check()
    return {z3.unsat: "unsat", z3.sat: "sat", z3.unknown: "unknown"}[res]


# ============================================================================
# Boundary-specific skeletons (Tier D workers fill these in)
# ============================================================================


def d1_g_to_hopf_template() -> BoundaryAdmissibilityReport:
    """D1: G-stack → Hopf admissibility.

    Question: which Hopf fibration classes are UNSAT on non-E-class
    root systems (e.g. A-class, non-simply-laced)?

    Expected UNSAT certificates (≥2):
    - Hopf winding w=1 (S¹→S³) on trivial root system (rank 0)
    - Hopf winding on non-simply-connected G-stack carrier
    """
    rpt = BoundaryAdmissibilityReport(boundary="g_to_hopf")
    # TODO(Tier D worker D1): fill in positive SAT witness for E6 + w=1
    # TODO(Tier D worker D1): encode UNSAT for trivial root system + w=1
    # TODO(Tier D worker D1): encode UNSAT for non-simply-connected carrier
    return rpt


def d2_hopf_to_weyl_template() -> BoundaryAdmissibilityReport:
    """D2: Hopf → Weyl admissibility.

    Question: which chirality choices (left/right) are UNSAT on given
    Hopf fibration winding?

    Expected UNSAT certificates (≥2):
    - Both chiralities simultaneously on winding w=0 (trivial)
    - Mismatched chirality-winding (handedness clash)
    """
    rpt = BoundaryAdmissibilityReport(boundary="hopf_to_weyl")
    # TODO(Tier D worker D2)
    return rpt


def d3_weyl_to_flux_template() -> BoundaryAdmissibilityReport:
    """D3: Weyl → Flux admissibility.

    Question: which flux orientations are UNSAT without spinor carrier?

    Expected UNSAT certificates (≥2):
    - Non-zero flux without any spinor carrier (no Weyl layer)
    - Radial flux with left chirality on winding requiring right-chirality
    """
    rpt = BoundaryAdmissibilityReport(boundary="weyl_to_flux")
    # TODO(Tier D worker D3)
    return rpt


def d4_flux_to_pauli_template() -> BoundaryAdmissibilityReport:
    """D4: Flux → Pauli admissibility.

    Question: which Pauli axes (X/Y/Z) are UNSAT without flux orientation?

    Expected UNSAT certificates (≥2):
    - Pauli-X on radial flux (orthogonality violation)
    - Pauli-Y without any flux orientation
    """
    rpt = BoundaryAdmissibilityReport(boundary="flux_to_pauli")
    # TODO(Tier D worker D4)
    return rpt


# ============================================================================
# SIM_TEMPLATE compliance boilerplate
# ============================================================================


# Tier D workers copy the below into their boundary_<name>_admissibility.py
# and fill in the TODO blocks. This template file is imported by each worker;
# does NOT run standalone (no results written).

CANONICAL_HEADER_EXAMPLE = '''
"""boundary_<pair>_admissibility — Tier D UNSAT certificates."""
from __future__ import annotations
import json
from pathlib import Path
from system_v4.probes._boundary_admissibility_template import (
    BoundaryAdmissibilityReport, UNSATCertificate,
    anti_tautology_check, hash_formula, solve_with_z3, d1_g_to_hopf_template,
)

classification = "canonical"

TOOL_MANIFEST = {
    "z3": {"tried": True, "used": True, "reason": "load-bearing SMT encoding of admissibility predicate"},
    "cvc5": {"tried": True, "used": False, "reason": "alternate SMT; cross-check only"},
    "sympy": {"tried": True, "used": True, "reason": "symbolic pre-encoding before z3 lowering"},
}

TOOL_INTEGRATION_DEPTH = {
    "z3": "load_bearing",
    "sympy": "load_bearing",
    "cvc5": "supportive",
}


def run_positive_tests() -> dict:
    """SAT: at least one admissible composition (supporting, not main)."""
    # TODO: encode admissible case, assert z3 returns sat
    return {"passed": True, "witnesses": []}


def run_negative_tests() -> dict:
    """UNSAT: ≥2 exclusion certificates. MAIN deliverable."""
    rpt = d1_g_to_hopf_template()  # or d2/d3/d4
    # TODO: fill in rpt.negative_unsat with UNSATCertificate instances
    return {"passed": len(rpt.negative_unsat) >= 2, "report": rpt.to_result_dict()}


def run_boundary_tests() -> dict:
    """Edge cases (degenerate windings, trivial root systems)."""
    # TODO
    return {"passed": True, "cases": []}


def main() -> dict:
    result = {
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    out = Path(__file__).parent / "a2_state/sim_results" / (Path(__file__).stem + "_results.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
'''
