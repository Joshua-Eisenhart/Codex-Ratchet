#!/usr/bin/env python3
"""
sim_integration_deap_clifford_rotor_evolution.py

DEAP GA evolving Clifford rotor parameters (4-float genome = scalar, e12, e13, e23 coefficients).
Fitness = ||R ∘ probe ∘ ~R - target||_clifford (Clifford norm of residual).

Claims:
- GA converges clifford distance < 0.1 in 20 generations

Both DEAP (evolutionary search) and clifford (rotor geometry/norm) are load_bearing.
classification="canonical"
"""

import json
import math
import os
import random

import numpy as np

classification = "canonical"

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not used: the search is evolutionary over plain Python genomes, with no torch tensors or autograd"},
    "pyg": {"tried": False, "used": False, "reason": "not used: rotor evolution does not involve graph message-passing or edge-index structure"},
    "z3": {"tried": False, "used": False, "reason": "not used: this sim optimizes a continuous rotor fit, not a SAT/SMT proof obligation"},
    "cvc5": {"tried": False, "used": False, "reason": "not used: same reason as z3; there is no solver-driven constraint proof here"},
    "sympy": {"tried": False, "used": False, "reason": "not used: rotor fitness is evaluated numerically through clifford operations, not symbolic algebra"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing: clifford provides the Cl(3) multivector basis, rotor sandwich product, and residual norm that define the optimization target"},
    "geomstats": {"tried": False, "used": False, "reason": "not used: the search space is handled directly as rotor coefficients, not as a Riemannian manifold problem"},
    "e3nn": {"tried": False, "used": False, "reason": "not used: there is no equivariant neural architecture in the rotor-evolution loop"},
    "rustworkx": {"tried": False, "used": False, "reason": "not used: no graph routing or reduction structure is present in this sim"},
    "xgi": {"tried": False, "used": False, "reason": "not used: the search problem has no hypergraph structure"},
    "toponetx": {"tried": False, "used": False, "reason": "not used: no cell-complex topology is computed in the rotor GA"},
    "gudhi": {"tried": False, "used": False, "reason": "not used: persistent homology is unrelated to the rotor residual objective"},
    "deap": {"tried": True, "used": True, "reason": "load-bearing: DEAP supplies the evolutionary loop, mutation, crossover, and selection that actually drives convergence of the rotor genome"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": "load_bearing",
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
    "deap": "load_bearing",
}

divergence_log = (
    "Canonical integration sim: DEAP drives the rotor search over genomes, while "
    "clifford defines the underlying Cl(3) rotor geometry and residual norm; both "
    "are required for the claimed convergence behavior."
)

# --- Imports ---
try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    from deap import base, creator, tools, algorithms
    TOOL_MANIFEST["deap"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["deap"]["reason"] = "not installed"

try:
    import torch  # noqa
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric  # noqa
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import *  # noqa
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy  # noqa
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    import geomstats  # noqa
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx  # noqa
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi  # noqa
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi  # noqa
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# CLIFFORD GEOMETRY SETUP
# =====================================================================

# Cl(3): 3D Clifford algebra, grade-2 bivectors span rotation planes
_layout, _blades = Cl(3)
_e1 = _blades["e1"]
_e2 = _blades["e2"]
_e3 = _blades["e3"]
_e12 = _blades["e12"]
_e13 = _blades["e13"]
_e23 = _blades["e23"]
_scalar = _layout.scalar

# Known optimal rotor for each target (used in positive and boundary tests)
# Rotation of e1 -> e2: R = cos(pi/4)*1 - sin(pi/4)*e12, sign convention from sandbox
_KNOWN_ROTORS = {
    "e1_to_e2": {
        "probe": _e1,
        "target": _e2,
        "genome": [math.cos(math.pi / 4), -math.sin(math.pi / 4), 0.0, 0.0],
    },
    "e1_to_e3": {
        "probe": _e1,
        "target": _e3,
        "genome": [math.cos(math.pi / 4), 0.0, -math.sin(math.pi / 4), 0.0],
    },
    "e2_to_e3": {
        "probe": _e2,
        "target": _e3,
        "genome": [math.cos(math.pi / 4), 0.0, 0.0, -math.sin(math.pi / 4)],
    },
}


def rotor_from_genome(genome):
    """Build a normalized Clifford rotor from [w, e12, e13, e23] genome."""
    w, t12, t13, t23 = genome
    mv = w * _scalar + t12 * _e12 + t13 * _e13 + t23 * _e23
    n = abs(mv)
    if n < 1e-10:
        return _scalar  # degenerate: return identity
    return mv / n


def clifford_distance(genome, probe_mv, target_mv):
    """Compute ||R ∘ probe ∘ ~R - target||_clifford."""
    R = rotor_from_genome(genome)
    result = R * probe_mv * ~R
    return float(abs(result - target_mv))


def run_deap_evolution(probe_mv, target_mv, pop_size=60, n_gen=20, seed=42):
    """
    Run DEAP GA to evolve a Clifford rotor (4-float genome) minimizing
    clifford_distance(genome, probe, target).

    Returns dict with convergence history and final best distance.
    """
    random.seed(seed)
    np.random.seed(seed)

    # DEAP setup — use unique type names to avoid registration conflicts
    if "FitnessMinRotor" not in creator.__dict__:
        creator.create("FitnessMinRotor", base.Fitness, weights=(-1.0,))
    if "RotorIndividual" not in creator.__dict__:
        creator.create("RotorIndividual", list, fitness=creator.FitnessMinRotor)

    toolbox = base.Toolbox()
    toolbox.register("attr_float", random.uniform, -1.0, 1.0)
    toolbox.register(
        "individual",
        tools.initRepeat,
        creator.RotorIndividual,
        toolbox.attr_float,
        n=4,
    )
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    def evaluate(ind):
        d = clifford_distance(list(ind), probe_mv, target_mv)
        return (d,)

    toolbox.register("evaluate", evaluate)
    toolbox.register("mate", tools.cxBlend, alpha=0.5)
    toolbox.register("mutate", tools.mutGaussian, mu=0.0, sigma=0.3, indpb=0.4)
    toolbox.register("select", tools.selTournament, tournsize=3)

    pop = toolbox.population(n=pop_size)

    # Evaluate initial population
    fitnesses = list(map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    history = []
    for gen in range(n_gen):
        offspring = toolbox.select(pop, len(pop))
        offspring = list(map(toolbox.clone, offspring))

        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < 0.7:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values

        for mutant in offspring:
            if random.random() < 0.3:
                toolbox.mutate(mutant)
                del mutant.fitness.values

        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = list(map(toolbox.evaluate, invalid_ind))
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        pop[:] = offspring
        best = min(ind.fitness.values[0] for ind in pop)
        history.append(best)

    best_ind = tools.selBest(pop, 1)[0]
    final_dist = best_ind.fitness.values[0]

    return {
        "final_distance": final_dist,
        "history": history,
        "best_genome": list(best_ind),
        "n_generations": n_gen,
        "pop_size": pop_size,
    }


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- Test 1: e1 -> e2 rotation, GA must converge < 0.1 in 20 gens ---
    task = _KNOWN_ROTORS["e1_to_e2"]
    run = run_deap_evolution(task["probe"], task["target"], pop_size=60, n_gen=20)
    results["e1_to_e2_convergence"] = {
        "final_distance": run["final_distance"],
        "pass": run["final_distance"] < 0.1,
        "history_last5": run["history"][-5:],
        "n_gen": run["n_gen"] if "n_gen" in run else 20,
    }

    # --- Test 2: e1 -> e3 rotation ---
    task2 = _KNOWN_ROTORS["e1_to_e3"]
    run2 = run_deap_evolution(task2["probe"], task2["target"], pop_size=60, n_gen=20, seed=123)
    results["e1_to_e3_convergence"] = {
        "final_distance": run2["final_distance"],
        "pass": run2["final_distance"] < 0.1,
        "history_last5": run2["history"][-5:],
    }

    # --- Test 3: e2 -> e3 rotation ---
    task3 = _KNOWN_ROTORS["e2_to_e3"]
    run3 = run_deap_evolution(task3["probe"], task3["target"], pop_size=60, n_gen=20, seed=999)
    results["e2_to_e3_convergence"] = {
        "final_distance": run3["final_distance"],
        "pass": run3["final_distance"] < 0.1,
        "history_last5": run3["history"][-5:],
    }

    # --- Test 4: Known-optimal genome achieves near-zero clifford distance ---
    for label, task in _KNOWN_ROTORS.items():
        d = clifford_distance(task["genome"], task["probe"], task["target"])
        results[f"known_optimal_{label}"] = {
            "clifford_distance": d,
            "pass": d < 1e-10,
            "rationale": "Known analytical rotor must achieve machine-epsilon clifford distance",
        }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    # --- Negative 1: Identity rotor applied to e1 vs target e2 has distance = sqrt(2) ---
    # abs(e1 - e2) = sqrt(2) ~= 1.414 because ||e_i||=1 and e1 perp e2 in Clifford norm
    identity_genome = [1.0, 0.0, 0.0, 0.0]
    d = clifford_distance(identity_genome, _e1, _e2)
    results["identity_rotor_e1_vs_e2_far"] = {
        "clifford_distance": d,
        "pass": d > 1.0,
        "rationale": (
            "Identity rotor leaves e1 unchanged; clifford distance from e2 equals "
            "||e1-e2||=sqrt(2)~=1.414 (perpendicular basis vectors), must exceed 1.0"
        ),
    }

    # --- Negative 2: Zero-vector genome collapses to identity (degenerate case) ---
    zero_genome = [0.0, 0.0, 0.0, 0.0]
    d_zero = clifford_distance(zero_genome, _e1, _e2)
    results["zero_genome_treated_as_identity"] = {
        "clifford_distance": d_zero,
        "pass": d_zero > 1.0,
        "rationale": (
            "Degenerate zero-norm genome falls back to scalar identity; "
            "result equals ||e1-e2||=sqrt(2)~=1.414, must exceed 1.0 confirming fallback"
        ),
    }

    # --- Negative 3: Random genome population has mean distance >> 0 initially ---
    rng = np.random.default_rng(7)
    random_distances = [
        clifford_distance(list(rng.uniform(-1, 1, 4)), _e1, _e2)
        for _ in range(50)
    ]
    mean_dist = float(np.mean(random_distances))
    results["random_genome_mean_distance_high"] = {
        "mean_distance": mean_dist,
        "pass": mean_dist > 0.5,
        "rationale": (
            "Random rotor parameters should not accidentally approach target; "
            "mean clifford distance over 50 random genomes must exceed 0.5"
        ),
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    # --- Boundary 1: Self-rotation probe==target has distance = 0 ---
    d_self = clifford_distance([1.0, 0.0, 0.0, 0.0], _e1, _e1)
    results["self_rotation_zero_distance"] = {
        "clifford_distance": d_self,
        "pass": d_self < 1e-10,
        "rationale": "Identity rotor applied to self-target must yield exactly zero clifford distance",
    }

    # --- Boundary 2: GA on e1->e2 task converges strictly better than random baseline ---
    # Random genomes give mean distance ~1.35; GA must achieve final < 0.05 (much better)
    run_boundary = run_deap_evolution(_e1, _e2, pop_size=80, n_gen=25, seed=0)
    results["ga_beats_random_baseline"] = {
        "final_distance": run_boundary["final_distance"],
        "random_mean_baseline": 1.35,
        "pass": run_boundary["final_distance"] < 0.05,
        "rationale": (
            "GA with 80 individuals and 25 generations on e1->e2 task must achieve "
            "clifford distance < 0.05, well below random baseline ~1.35"
        ),
    }

    # --- Boundary 3: Rotor normalization - any nonzero genome gives unit rotor after normalization ---
    test_genomes = [
        [2.0, 0.0, 0.0, 0.0],
        [0.1, 0.1, 0.1, 0.1],
        [1.0, 1.0, 0.0, 0.0],
    ]
    norms = []
    for g in test_genomes:
        R = rotor_from_genome(g)
        # R * ~R should have scalar part = 1.0
        RRr = R * ~R
        scalar_part = float(RRr.value[0])
        norms.append(abs(scalar_part - 1.0))
    max_norm_err = max(norms)
    results["rotor_normalization_unit_constraint"] = {
        "max_norm_error": max_norm_err,
        "pass": max_norm_err < 1e-10,
        "rationale": "Normalized rotor R must satisfy R*~R = 1 (unit rotor constraint in Cl(3))",
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    all_checks = {}
    for section, data in [("positive", positive), ("negative", negative), ("boundary", boundary)]:
        for k, v in data.items():
            if isinstance(v, dict) and "pass" in v:
                all_checks[f"{section}.{k}"] = v["pass"]

    all_pass = all(all_checks.values())

    results = {
        "name": "sim_integration_deap_clifford_rotor_evolution",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_checks": all_checks,
        "all_pass": all_pass,
        "overall_pass": all_pass,
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(
        out_dir, "sim_integration_deap_clifford_rotor_evolution_results.json"
    )
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")
    for k, v in all_checks.items():
        print(f"  {'PASS' if v else 'FAIL'}: {k}")
