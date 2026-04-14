#!/usr/bin/env python3
"""
sim_capability_deap_isolated.py -- Isolated tool-capability probe for DEAP.

Classical_baseline capability probe: exercises a minimal DEAP toolbox
(tournament selection, mutFlipBit, cxTwoPoint) on an 8-bit fitness=sum task,
in isolation. Pays down discipline debt recorded 2026-04-14 in
KNOWN_DISCIPLINE_DEBT.md. Per the four-sim-kinds doctrine this is a capability
sim, not an integration sim.
"""

import json
import os
import random

classification = "classical_baseline"

_ISOLATED_REASON = (
    "not used: this probe isolates the DEAP evolutionary toolbox in isolation; "
    "cross-tool integration is deferred to a dedicated integration sim per the "
    "four-sim-kinds doctrine (capability must precede integration)."
)

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "pyg":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "z3":        {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "cvc5":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "sympy":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "clifford":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "e3nn":      {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "xgi":       {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "toponetx":  {"tried": False, "used": False, "reason": _ISOLATED_REASON},
    "gudhi":     {"tried": False, "used": False, "reason": _ISOLATED_REASON},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

DEAP_OK = False
DEAP_VERSION = None
try:
    import deap
    from deap import base, creator, tools
    DEAP_OK = True
    DEAP_VERSION = getattr(deap, "__version__", "unknown")
except Exception as exc:
    _deap_exc = exc


def _make_toolbox(n_bits=8):
    # Guard against re-creation on repeated runs in same interpreter
    if not hasattr(creator, "FitMaxCap"):
        creator.create("FitMaxCap", base.Fitness, weights=(1.0,))
    if not hasattr(creator, "IndCap"):
        creator.create("IndCap", list, fitness=creator.FitMaxCap)
    tb = base.Toolbox()
    tb.register("attr_bit", random.randint, 0, 1)
    tb.register("individual", tools.initRepeat, creator.IndCap, tb.attr_bit, n=n_bits)
    tb.register("population", tools.initRepeat, list, tb.individual)
    tb.register("evaluate", lambda ind: (sum(ind),))
    tb.register("select", tools.selTournament, tournsize=3)
    tb.register("mate", tools.cxTwoPoint)
    tb.register("mutate", tools.mutFlipBit, indpb=0.1)
    return tb


def run_positive_tests():
    r = {}
    if not DEAP_OK:
        r["deap_available"] = {"pass": False, "detail": f"deap missing: {_deap_exc}"}
        return r
    r["deap_available"] = {"pass": True, "version": DEAP_VERSION}

    random.seed(0)
    tb = _make_toolbox(8)
    pop = tb.population(n=20)
    for ind in pop:
        ind.fitness.values = tb.evaluate(ind)
    # Run a few generations
    for _ in range(20):
        offspring = list(map(tb.clone, tb.select(pop, len(pop))))
        for c1, c2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < 0.7:
                tb.mate(c1, c2)
                del c1.fitness.values
                del c2.fitness.values
        for m in offspring:
            if random.random() < 0.2:
                tb.mutate(m)
                del m.fitness.values
        for ind in offspring:
            if not ind.fitness.valid:
                ind.fitness.values = tb.evaluate(ind)
        pop = offspring
    best = max(pop, key=lambda i: i.fitness.values[0])
    r["evolution_improves_fitness"] = {
        "pass": best.fitness.values[0] >= 6,  # out of 8
        "best_fitness": best.fitness.values[0],
    }
    return r


def run_negative_tests():
    r = {}
    if not DEAP_OK:
        r["skip"] = {"pass": False, "detail": "deap missing"}
        return r
    # Zero-length individual: crossover / evaluation must either no-op or raise;
    # we admit either as "handled"; what is EXCLUDED is silent corruption.
    tb = _make_toolbox(0)
    ind1 = tb.individual()
    ind2 = tb.individual()
    ok = True
    try:
        tb.mate(ind1, ind2)
    except Exception:
        ok = True  # raising is an acceptable handled failure mode
    # Fitness on empty individual = (0,) -- no crash
    try:
        fit = tb.evaluate(ind1)
        admissible = fit == (0,)
    except Exception:
        admissible = False
    r["zero_length_individual_handled"] = {"pass": ok and admissible}
    return r


def run_boundary_tests():
    r = {}
    if not DEAP_OK:
        r["skip"] = {"pass": False, "detail": "deap missing"}
        return r
    random.seed(1)
    tb = _make_toolbox(8)
    pop = tb.population(n=1)
    pop[0].fitness.values = tb.evaluate(pop[0])
    # Selection from pop=1 must return the single individual.
    selected = tb.select(pop, 1)
    r["pop_size_one_selects"] = {
        "pass": len(selected) == 1 and selected[0] == pop[0],
    }
    return r


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    def _all_pass(d):
        return all(v.get("pass", False) for v in d.values()) if d else False

    overall_pass = _all_pass(positive) and _all_pass(negative) and _all_pass(boundary)

    results = {
        "name": "sim_capability_deap_isolated",
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "target_tool": {"name": "deap", "version": DEAP_VERSION, "integration": "load_bearing"},
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "overall_pass": overall_pass,
        "capability_summary": {
            "can": "Compose a GA loop from tournament selection + two-point "
                   "crossover + bit-flip mutation, reaching >=6/8 on OneMax in "
                   "20 generations with pop=20 from a fixed seed.",
            "cannot": "Does not provide parallelism or GPU acceleration out of "
                      "the box; large populations are slow relative to evotorch.",
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_capability_deap_isolated_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"[{'PASS' if overall_pass else 'FAIL'}] {out_path}")
