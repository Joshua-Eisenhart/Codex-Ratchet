from __future__ import annotations

from pathlib import Path

from ..semantic import SemanticClaimProfile, SemanticRegistry


def cr_semantic_profile(registry_path: Path) -> SemanticClaimProfile:
    """Build the CR boundary profile from controller-owned registry data."""
    return SemanticClaimProfile(SemanticRegistry.from_path(registry_path))


CR_REQUIRED_OBJECT_TYPES = (
    "CTX",
    "QUOT",
    "DENS",
    "PURE",
    "MIX",
    "HOPF",
    "CHIR",
    "CUT",
    "CORR",
    "PROC",
    "HIST",
    "WHOLE",
)


def cr_whole_state_obligations() -> dict[str, object]:
    """Return requirements, not an assertion that the strata are admitted."""
    return {
        "schema": "constraintbox.cr-whole-state-obligations.v1",
        "status": "PROPOSED",
        "object_type_candidates": list(CR_REQUIRED_OBJECT_TYPES),
        "requirements": [
            "finite carrier declared",
            "nonempty demand packet",
            "explicit restriction maps",
            "plural candidate branches retained",
            "typed metrics not scalarized",
            "relative MSS scope only",
            "whole-state settlement evidence",
            "provider self-verdict ignored",
        ],
        "promotion_allowed": False,
    }
