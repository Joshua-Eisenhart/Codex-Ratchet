"""Feedback: reads B's results and updates A2's persistent state.

After B evaluates a batch:
  - Accepted items → add to rosetta as validated B-terms
  - Rejected items → record why, update A2's understanding of the constraint surface
  - Graveyard items → track what can't be expressed yet and why

This is the outbound leg of A1: B→A1→A2.
"""

import json
from pathlib import Path


DEFAULT_A2_STATE = Path(__file__).resolve().parent.parent / "a2_state"


def _resolve_a2_state_dir(a2_state_dir=None):
    if a2_state_dir is None:
        return DEFAULT_A2_STATE
    return Path(a2_state_dir)


def update_rosetta(state, a2_state_dir=None):
    """Update rosetta.json with newly admitted terms."""
    target_dir = _resolve_a2_state_dir(a2_state_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    rosetta_path = target_dir / "rosetta.json"
    if not rosetta_path.exists():
        rosetta_path.write_text(json.dumps({"mappings": {}}, indent=2), encoding="utf-8")

    rosetta = json.loads(rosetta_path.read_text())
    mappings = rosetta.get("mappings", {})
    added = 0

    terms = state.terms if isinstance(state.terms, dict) else {}
    for term_literal, info in terms.items():
        if term_literal not in mappings:
            mappings[term_literal] = {
                "b_spec_id": info.get("spec_id", ""),
                "binds": info.get("binds", ""),
                "state": info.get("state", ""),
                "admitted_cycle": True,
            }
            added += 1

    rosetta["mappings"] = mappings
    rosetta_path.write_text(json.dumps(rosetta, indent=2), encoding="utf-8")
    return added


def record_graveyard_surface(state, a2_state_dir=None):
    """Write a summary of the graveyard — the constraint surface map."""
    from collections import Counter
    reasons = Counter(g.get("reason", "?") for g in state.graveyard)

    surface = {
        "total_graveyard": len(state.graveyard),
        "total_survivors": len(state.survivor_order),
        "ratio": round(len(state.graveyard) / max(1, len(state.graveyard) + len(state.survivor_order)), 3),
        "rejection_reasons": dict(reasons.most_common(20)),
        "blocked_concepts": [],
    }

    for g in state.graveyard:
        gid = g.get("id", "")
        reason = g.get("reason", "")
        if gid.startswith("S_P_") or "DERIVED_ONLY" in reason or "UNDEFINED_TERM" in reason:
            surface["blocked_concepts"].append({
                "id": gid,
                "reason": reason,
            })

    target_dir = _resolve_a2_state_dir(a2_state_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    surface_path = target_dir / "constraint_surface.json"
    surface_path.write_text(json.dumps(surface, indent=2), encoding="utf-8")
    return surface


def run_feedback(state, a2_state_dir=None):
    """Run the full feedback cycle: update rosetta + record surface."""
    rosetta_added = update_rosetta(state, a2_state_dir=a2_state_dir)
    surface = record_graveyard_surface(state, a2_state_dir=a2_state_dir)
    return {
        "rosetta_terms_added": rosetta_added,
        "graveyard_ratio": surface["ratio"],
        "blocked_concepts": len(surface["blocked_concepts"]),
    }
