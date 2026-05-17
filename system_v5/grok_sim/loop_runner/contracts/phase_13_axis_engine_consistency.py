"""phase_13_axis_engine_consistency.py — engine schedule represents all 4 terrain families.

The 7 axes test specific operators (Ti σ_z dephasing, Te σ_x dephasing, Fi σ_x rotation,
Fe σ_z rotation). The engine schedules should ALSO contain all 4 terrain families — if
the engine only uses Ti and Fe (missing Te and Fi), it's structurally disconnected from
the axis-level dynamics.

This catches engines that have the right size (32 stages) and right vocabulary but
unbalanced terrain coverage (e.g., 16 Ti + 16 Fe but 0 Te + 0 Fi).
"""
EXPECTED_TERRAINS = {"Ti", "Te", "Fi", "Fe"}
EXPECTED_PER_TERRAIN = 8  # 32 stages / 4 terrains = 8 stages per terrain in a balanced schedule


def _get_stages(candidate, name_base):
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


def _analyze_balance(stages, label):
    """Count terrain occurrences and check balance."""
    failures = []
    metrics = {}
    if stages is None:
        return [{"check": f"engine_{label}_stages_accessible",
                 "msg": f"engine_{label.lower()}_stages not accessible"}], {}

    counts = {t: 0 for t in EXPECTED_TERRAINS}
    for s in stages:
        if isinstance(s, dict) and "terrain" in s and s["terrain"] in counts:
            counts[s["terrain"]] += 1
    metrics[f"engine_{label}_terrain_counts"] = counts

    missing_terrains = [t for t, c in counts.items() if c == 0]
    if missing_terrains:
        failures.append({
            "check": f"engine_{label}_all_terrains_present",
            "msg": f"engine_{label.lower()}_stages missing terrains: {missing_terrains}. "
                   f"All 4 terrain families (Ti, Te, Fi, Fe) must appear at least once. "
                   f"Counts: {counts}",
        })

    # Balance check — no terrain should be hugely over- or under-represented
    # Allow ±50% deviation from EXPECTED_PER_TERRAIN
    for t, c in counts.items():
        if c > 0 and (c < EXPECTED_PER_TERRAIN // 2 or c > EXPECTED_PER_TERRAIN * 2):
            failures.append({
                "check": f"engine_{label}_balance_{t}",
                "msg": f"engine_{label.lower()}_stages has {c} `{t}` stages, expected ~{EXPECTED_PER_TERRAIN} "
                       f"(allow [{EXPECTED_PER_TERRAIN//2}, {EXPECTED_PER_TERRAIN*2}]). "
                       f"Unbalanced terrain coverage indicates a non-symmetric schedule.",
            })

    return failures, metrics


def run(candidate):
    failures = []
    metrics = {}

    stages_a, _ = _get_stages(candidate, "engine_a_stages")
    stages_b, _ = _get_stages(candidate, "engine_b_stages")

    for label, stages in [("A", stages_a), ("B", stages_b)]:
        f, m = _analyze_balance(stages, label)
        failures.extend(f)
        metrics.update(m)

    # Cross-engine: A and B should both cover the same terrain space
    if stages_a is not None and stages_b is not None:
        a_terrains = {s.get("terrain") for s in stages_a if isinstance(s, dict)}
        b_terrains = {s.get("terrain") for s in stages_b if isinstance(s, dict)}
        if a_terrains != b_terrains:
            failures.append({
                "check": "engine_terrain_set_match",
                "msg": f"Engine A terrains {a_terrains} != Engine B terrains {b_terrains}. "
                       f"The two engines should cover the same terrain vocabulary; differences "
                       f"would mean the two engines are not structurally comparable on a common substrate.",
            })

    return {
        "pass": len(failures) == 0,
        "failures": failures,
        "metrics": metrics,
        "graveyard_companions": [
            "Engine with only Ti+Fe terrains (no Te/Fi) — fails all_terrains_present",
            "Engine with 28 Ti + 1 of each other — fails balance_Ti",
            "Engine A using {Ti,Te,Fi,Fe} but B using {Ni,Si,Ne,Se} — fails terrain_set_match",
        ],
        "baseline_variants": [
            "single-terrain baseline (32 of same terrain) — fails coverage + balance",
        ],
    }
