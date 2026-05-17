"""phase_12_stage_enumeration.py — engines have proper 32-stage enumeration covering all placements.

The 32 stages per engine should represent:
  - 4 terrain families × 2 chirality sheets × 2 loops × 2 directions = 32 distinct placements
  - No duplicate (terrain, sheet, loop, direction) tuples within a single engine

This catches:
  - Engines claiming "32 stages" but with only 8-16 unique placements (rest are repeats)
  - Engines missing one terrain family or one sheet
  - Engines with empty fields (missing direction etc.)
  - Engines with structurally different enumeration that breaks A/B comparison

Looks for stage enumeration in any of these forms:
  - candidate.engine_a_stages (attribute, list)
  - candidate.ENGINE_A_STAGES (attribute, list, capitalized)
  - candidate.get_engine_a_stages() (function returning list)
"""
TERRAIN_FAMILIES = {"Ti", "Te", "Fi", "Fe"}
SHEETS = {"L", "R"}
LOOPS = {"f", "b"}
DIRECTIONS = {"fwd", "rev"}
EXPECTED_PLACEMENTS = 4 * 2 * 2 * 2  # 32


def _get_stages(candidate, name_base):
    """Look up stages list under any of the recognized attribute/function names."""
    for attr in (name_base, name_base.upper(), f"get_{name_base}"):
        if hasattr(candidate, attr):
            val = getattr(candidate, attr)
            if callable(val):
                try:
                    return list(val()), attr
                except Exception:
                    continue
            elif isinstance(val, list):
                return val, attr
    return None, None


def _analyze(stages, label):
    failures = []
    metrics = {}
    if stages is None:
        return [{"check": f"engine_{label}_stages_accessible",
                 "msg": f"candidate does not expose `engine_{label.lower()}_stages` (or ENGINE_{label}_STAGES, "
                        f"or get_engine_{label.lower()}_stages())"}], {}

    metrics[f"engine_{label}_stage_count"] = len(stages)
    if len(stages) != EXPECTED_PLACEMENTS:
        failures.append({
            "check": f"engine_{label}_stage_count_32",
            "msg": f"engine_{label.lower()}_stages has {len(stages)} entries, expected 32 "
                   f"(= 4 terrains × 2 sheets × 2 loops × 2 directions).",
        })

    # Check each stage has the required fields
    placement_tuples = []
    for i, s in enumerate(stages):
        if not isinstance(s, dict):
            failures.append({
                "check": f"engine_{label}_stage_{i}_dict",
                "msg": f"stage {i} is {type(s).__name__}, expected dict",
            })
            continue
        for field in ("terrain", "sheet", "loop", "direction"):
            if field not in s:
                failures.append({
                    "check": f"engine_{label}_stage_{i}_missing_{field}",
                    "msg": f"stage {i} missing `{field}` field",
                })
        # Build placement tuple if all fields present
        t = s.get("terrain"); sh = s.get("sheet"); lp = s.get("loop"); d = s.get("direction")
        if t and sh and lp and d:
            placement_tuples.append((t, sh, lp, d))

    # Vocabulary check — values come from the expected sets
    vocab_violations = {}
    for i, (t, sh, lp, d) in enumerate(placement_tuples):
        if t not in TERRAIN_FAMILIES:
            vocab_violations.setdefault("terrain", set()).add(t)
        if sh not in SHEETS:
            vocab_violations.setdefault("sheet", set()).add(sh)
        if lp not in LOOPS:
            vocab_violations.setdefault("loop", set()).add(lp)
        if d not in DIRECTIONS:
            vocab_violations.setdefault("direction", set()).add(d)
    for axis, vals in vocab_violations.items():
        expected = {"terrain": TERRAIN_FAMILIES, "sheet": SHEETS,
                    "loop": LOOPS, "direction": DIRECTIONS}[axis]
        failures.append({
            "check": f"engine_{label}_vocab_{axis}",
            "msg": f"engine_{label.lower()}_stages contains {axis} values {vals} "
                   f"outside expected vocabulary {expected}.",
        })

    # Uniqueness — all 32 (terrain, sheet, loop, direction) tuples must be distinct
    unique_count = len(set(placement_tuples))
    metrics[f"engine_{label}_unique_placements"] = unique_count
    if placement_tuples and unique_count != len(placement_tuples):
        n_dups = len(placement_tuples) - unique_count
        failures.append({
            "check": f"engine_{label}_unique",
            "msg": f"engine_{label.lower()}_stages has {n_dups} duplicate placement tuples. "
                   f"Each (terrain, sheet, loop, direction) should appear exactly once.",
        })

    # Full coverage — all 32 expected placements must appear
    expected_set = {(t, sh, lp, d)
                    for t in TERRAIN_FAMILIES for sh in SHEETS
                    for lp in LOOPS for d in DIRECTIONS}
    actual_set = set(placement_tuples)
    missing = expected_set - actual_set
    metrics[f"engine_{label}_coverage"] = len(actual_set & expected_set)
    if missing:
        failures.append({
            "check": f"engine_{label}_full_coverage",
            "msg": f"engine_{label.lower()}_stages missing {len(missing)} placements: "
                   f"{sorted(missing)[:5]}{'...' if len(missing) > 5 else ''}. "
                   f"All 32 = 4×2×2×2 must be present.",
        })

    return failures, metrics


def run(candidate):
    failures = []
    metrics = {}

    stages_a, attr_a = _get_stages(candidate, "engine_a_stages")
    stages_b, attr_b = _get_stages(candidate, "engine_b_stages")
    metrics["engine_a_source"] = attr_a
    metrics["engine_b_source"] = attr_b

    for label, stages in [("A", stages_a), ("B", stages_b)]:
        f, m = _analyze(stages, label)
        failures.extend(f)
        metrics.update(m)

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "Engine with only 8 unique placements repeated 4x — fails unique check",
            "Engine missing 'Fe' terrain family — fails full_coverage",
            "Engine using 'inner'/'outer' instead of 'f'/'b' for loop — fails vocab",
            "Engine where stage_count != 32 — fails count check",
        ],
        "baseline_variants": [
            "16-stage baseline (placements × 1 direction) — fails count + missing direction half",
            "32 identical stages — fails unique check",
        ],
    }
