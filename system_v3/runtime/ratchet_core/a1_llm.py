import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

"""A1 LLM interface: generates briefings for the Cursor LLM and validates strategy files.

The Cursor LLM reads the briefing, produces a strategy JSON, saves it,
then the pipeline runs: strategy -> expand -> B -> SIM -> feedback.

Usage:
  python3 a1_llm.py --briefing                     # print state briefing
  python3 a1_llm.py --briefing --run-dir runs/x    # briefing from specific run
  python3 a1_llm.py --validate strategy.json       # check strategy format
"""

import argparse
import json
import os
from pathlib import Path

from state import KernelState
from validator import load_bootpack_rules


def _load_state(run_dir):
    state_file = os.path.join(run_dir, "state.json")
    if os.path.exists(state_file):
        return KernelState.from_json(Path(state_file).read_text())
    return KernelState()


def _load_fuel(repo_root, limit=20):
    fuel_path = Path(repo_root) / "system_v3" / "a2_state" / "fuel_queue.json"
    if not fuel_path.exists():
        return []
    fuel = json.loads(fuel_path.read_text())
    return fuel.get("entries", [])[:limit]


def _load_rosetta(repo_root):
    path = Path(repo_root) / "system_v3" / "a2_state" / "rosetta.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text()).get("mappings", {})


def generate_briefing(run_dir, repo_root, fuel_limit=30):
    """Generate a structured briefing for the Cursor LLM acting as A1."""
    state = _load_state(run_dir)
    fuel = _load_fuel(repo_root, limit=fuel_limit)
    rosetta = _load_rosetta(repo_root)
    rules = load_bootpack_rules()

    lines = []
    lines.append("=" * 60)
    lines.append("A1 BRIEFING — read this, then produce a strategy JSON")
    lines.append("=" * 60)

    # Lexeme set
    lines.append(f"\n## LEXEME SET ({len(rules.lexeme_set)} words)")
    lines.append("These are the ONLY primitive words B accepts:")
    lines.append(", ".join(sorted(rules.lexeme_set)))

    # Derived-only fence
    lines.append(f"\n## DERIVED-ONLY FENCE ({len(rules.derived_only_terms)} words)")
    lines.append("These words CANNOT appear as primitives. Must enter via TERM_DEF:")
    derived_sample = sorted(rules.derived_only_terms)[:30]
    lines.append(", ".join(derived_sample))
    if len(rules.derived_only_terms) > 30:
        lines.append(f"  ... and {len(rules.derived_only_terms) - 30} more")

    # Current survivors
    survivors = [s for s in state.survivor_order if s in state.specs]
    lines.append(f"\n## SURVIVORS ({len(survivors)} specs, {len(state.axioms)} axioms)")
    for sid in survivors[:20]:
        spec = state.specs[sid]
        lines.append(f"  {sid}  kind={spec['kind']}  status={spec.get('status', '?')}")
    if len(survivors) > 20:
        lines.append(f"  ... {len(survivors) - 20} more")

    # Admitted terms
    lines.append(f"\n## ADMITTED TERMS ({len(state.terms)})")
    for term, info in sorted(state.terms.items()):
        lines.append(f"  {term}  binds={info.get('binds', '?')}")
    if not state.terms:
        lines.append("  (none yet)")

    # Graveyard analysis
    lines.append(f"\n## GRAVEYARD ({len(state.graveyard)} items)")
    reasons = {}
    for g in state.graveyard:
        r = g.get("reason", "?")
        reasons[r] = reasons.get(r, 0) + 1
    for r, count in sorted(reasons.items(), key=lambda x: -x[1]):
        lines.append(f"  {r}: {count}")
    recent_dead = state.graveyard[-10:] if state.graveyard else []
    if recent_dead:
        lines.append("  Recent kills:")
        for g in recent_dead:
            lines.append(f"    {g.get('id', '?')} — {g.get('reason', '?')}")

    # Pending evidence
    lines.append(f"\n## PENDING EVIDENCE ({len(state.evidence_pending)} specs)")
    for sid, tokens in sorted(state.evidence_pending.items())[:10]:
        lines.append(f"  {sid} needs: {', '.join(sorted(tokens))}")

    # Rosetta
    lines.append(f"\n## ROSETTA ({len(rosetta)} mappings)")
    for term, info in sorted(rosetta.items())[:10]:
        lines.append(f"  {term} -> {info.get('b_spec_id', '?')}")
    if not rosetta:
        lines.append("  (empty — no terms admitted yet)")

    # Pool (the graveyard workspace — everything starts here)
    dead = {k: v for k, v in state.pool.items() if v["status"] == "DEAD"}
    attempting = {k: v for k, v in state.pool.items() if v["status"] == "ATTEMPTING"}
    resurrected = {k: v for k, v in state.pool.items() if v["status"] == "RESURRECTED"}
    lines.append(f"\n## POOL ({len(state.pool)} total: {len(dead)} dead, {len(attempting)} attempting, {len(resurrected)} resurrected)")
    lines.append("Pick items to try resurrecting. Build chains bottom-up.")
    for cid, c in sorted(dead.items())[:20]:
        needs = ", ".join(c.get("chain_needs", [])) or "none"
        attempts = len(c.get("attempts", []))
        label = c.get("label", "?")
        last_reason = ""
        if c.get("attempts"):
            last_reason = f" (last: {c['attempts'][-1].get('reason', '?')})"
        lines.append(f"  DEAD  {cid:10s} {label:40s} needs=[{needs}] attempts={attempts}{last_reason}")
    if len(dead) > 20:
        lines.append(f"  ... {len(dead) - 20} more dead items")

    # Instructions
    lines.append("\n" + "=" * 60)
    lines.append("STRATEGY FORMAT — produce this JSON:")
    lines.append("=" * 60)
    lines.append("""{
  "terms_to_admit": [
    {
      "term": "entropy",
      "alternatives": [
        {"suffix": "USES_IDENTITY", "objects": "density trace identity", "flaw": "identity is derived-only"}
      ]
    }
  ],
  "compounds_to_try": ["density_entropy"],
  "math_defs": [
    {
      "id": "S_001",
      "objects": "trace density operator channel",
      "alternatives": [
        {"suffix": "BAD", "objects": "trace identity", "flaw": "uses derived-only"}
      ]
    }
  ]
}""")
    lines.append("\nRULES:")
    lines.append("- terms_to_admit: propose TERM_DEF literals (quoted TERM \"...\") with optional competing alternatives.")
    lines.append("- Alternatives should be similar-but-wrong so they die at B fences (derived-only / undefined-term).")
    lines.append("- Build chains: if a concept needs 'trace', make sure trace is admitted first")
    lines.append("- Graveyard grows naturally from alternatives (no extra mechanics required).")
    lines.append("=" * 60)

    return "\n".join(lines)


def validate_strategy(path):
    """Check a strategy JSON file for format issues."""
    data = json.loads(Path(path).read_text())
    issues = []
    required = ["terms_to_admit", "compounds_to_try", "math_defs"]
    for key in required:
        if key not in data:
            issues.append(f"missing key: {key}")
        elif not isinstance(data[key], list):
            issues.append(f"{key} must be a list")
    if "probes" in data and not isinstance(data["probes"], list):
        issues.append("probes must be a list (if present)")
    for mdef in data.get("math_defs", []):
        if "id" not in mdef:
            issues.append(f"math_def missing 'id': {mdef}")
        if "objects" not in mdef:
            issues.append(f"math_def missing 'objects': {mdef}")
    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--briefing", action="store_true")
    parser.add_argument("--validate", type=str, default=None)
    parser.add_argument("--fuel-limit", type=int, default=30)
    parser.add_argument("--run-dir", default=os.path.join("runs", "ratchet_v2"))
    args = parser.parse_args()

    repo_root = str(Path(__file__).resolve().parents[3])

    if args.briefing:
        print(generate_briefing(args.run_dir, repo_root, fuel_limit=args.fuel_limit))
    if args.validate:
        issues = validate_strategy(args.validate)
        if issues:
            print("ISSUES:")
            for i in issues:
                print(f"  - {i}")
        else:
            print("VALID")


if __name__ == "__main__":
    main()
