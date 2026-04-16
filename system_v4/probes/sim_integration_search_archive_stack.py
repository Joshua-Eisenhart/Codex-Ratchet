#!/usr/bin/env python3
"""
sim_integration_search_archive_stack.py

Deep integration reference sim for the search/archive bundle:
  pytorch + optuna + pymoo + ribs + deap + evotorch

Claim:
all six tools can operate on one shared search surface instead of being wired
ad hoc one at a time.
  - pytorch defines the weighted target-error objective and behavior measures.
  - optuna runs TPE search over the same 4D surface.
  - deap runs a genetic search over the same 4D surface.
  - evotorch runs SNES over the same 4D surface.
  - pymoo runs a multi-objective front on error vs norm.
  - ribs archives candidates from all search lanes into one shared behavior map.

This is a classical integration baseline: the point is tool-stack discipline,
not a canonical nonclassical witness.
"""

from __future__ import annotations

import json
import logging
import os
import random
from typing import Iterable

import numpy as np
import optuna
import torch
from deap import base, creator, tools
from evotorch import Problem
from evotorch.algorithms import SNES
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem as PymooProblem
from pymoo.optimize import minimize as pymoo_minimize
from pymoo.termination import get_termination
from ribs.archives import GridArchive


classification = "classical_baseline"
divergence_log = (
    "Classical integration baseline: this is a full search/archive tool-stack "
    "reference lane, not a canonical nonclassical witness."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing objective and behavior surface for all search methods",
    },
    "optuna": {
        "tried": True,
        "used": True,
        "reason": "load-bearing TPE search on the shared 4D objective",
    },
    "pymoo": {
        "tried": True,
        "used": True,
        "reason": "load-bearing NSGA-II Pareto front on shared error vs norm objectives",
    },
    "ribs": {
        "tried": True,
        "used": True,
        "reason": "load-bearing shared archive of candidates emitted by all search lanes",
    },
    "deap": {
        "tried": True,
        "used": True,
        "reason": "load-bearing genetic search on the shared 4D objective",
    },
    "evotorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SNES search on the shared 4D objective",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "optuna": "load_bearing",
    "pymoo": "load_bearing",
    "ribs": "load_bearing",
    "deap": "load_bearing",
    "evotorch": "load_bearing",
}


optuna.logging.set_verbosity(optuna.logging.WARNING)
logging.getLogger("evotorch").setLevel(logging.ERROR)
logging.getLogger("evotorch.core").setLevel(logging.ERROR)

TARGET = torch.tensor([1.5, -1.2, 0.8, 1.1], dtype=torch.float32)
WEIGHTS = torch.tensor([1.0, 1.4, 0.8, 1.2], dtype=torch.float32)
BOUNDS = (-2.5, 2.5)


def _to_tensor(x) -> torch.Tensor:
    if isinstance(x, torch.Tensor):
        return x.detach().to(dtype=torch.float32).flatten()
    return torch.tensor(np.asarray(x, dtype=np.float32), dtype=torch.float32).flatten()


def torch_error(x) -> float:
    x_t = _to_tensor(x)
    return float(torch.sum(WEIGHTS * (x_t - TARGET) ** 2).item())


def behavior_measures(x) -> np.ndarray:
    x_t = _to_tensor(x)
    return np.array(
        [
            float(torch.mean(x_t[:2])),
            float(torch.mean(x_t[2:])),
        ],
        dtype=float,
    )


def _archive_candidate_rows(rows: Iterable[np.ndarray]) -> dict[str, object]:
    archive = GridArchive(solution_dim=4, dims=[6, 6], ranges=[BOUNDS, BOUNDS])
    count = 0
    for row in rows:
        x = np.asarray(row, dtype=float)
        archive.add_single(
            solution=x,
            objective=-torch_error(x),
            measures=np.clip(behavior_measures(x), BOUNDS[0], BOUNDS[1]),
        )
        count += 1
    return {
        "coverage": float(archive.stats.coverage),
        "num_elites": int(archive.stats.num_elites),
        "objective_max": float(archive.stats.obj_max),
        "candidate_count": count,
    }


def run_optuna(n_trials: int, seed: int) -> dict[str, object]:
    def objective(trial):
        x = [trial.suggest_float(f"x{i}", BOUNDS[0], BOUNDS[1]) for i in range(4)]
        return torch_error(x)

    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=seed),
    )
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    rows = [
        np.array([trial.params.get(f"x{i}", 0.0) for i in range(4)], dtype=float)
        for trial in study.trials
    ]
    return {
        "best_error": float(study.best_value),
        "best_solution": [float(study.best_params[f"x{i}"]) for i in range(4)],
        "candidate_rows": rows,
    }


def run_deap(pop_size: int, n_gen: int, seed: int) -> dict[str, object]:
    random.seed(seed)
    np.random.seed(seed)

    if "FitnessMinSearchArchiveStack" not in creator.__dict__:
        creator.create("FitnessMinSearchArchiveStack", base.Fitness, weights=(-1.0,))
    if "SearchArchiveStackIndividual" not in creator.__dict__:
        creator.create("SearchArchiveStackIndividual", list, fitness=creator.FitnessMinSearchArchiveStack)

    toolbox = base.Toolbox()
    toolbox.register("attr_float", random.uniform, BOUNDS[0], BOUNDS[1])
    toolbox.register(
        "individual",
        tools.initRepeat,
        creator.SearchArchiveStackIndividual,
        toolbox.attr_float,
        n=4,
    )
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", lambda ind: (torch_error(ind),))
    toolbox.register("mate", tools.cxBlend, alpha=0.4)
    toolbox.register("mutate", tools.mutGaussian, mu=0.0, sigma=0.4, indpb=0.4)
    toolbox.register("select", tools.selTournament, tournsize=3)

    population = toolbox.population(n=pop_size)
    for individual in population:
        individual.fitness.values = toolbox.evaluate(individual)

    for _ in range(n_gen):
        offspring = list(map(toolbox.clone, toolbox.select(population, len(population))))
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < 0.7:
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values
        for mutant in offspring:
            if random.random() < 0.3:
                toolbox.mutate(mutant)
                del mutant.fitness.values
        invalid = [ind for ind in offspring if not ind.fitness.valid]
        for individual in invalid:
            individual.fitness.values = toolbox.evaluate(individual)
        population[:] = offspring

    best = tools.selBest(population, 1)[0]
    return {
        "best_error": float(best.fitness.values[0]),
        "best_solution": [float(v) for v in best],
        "candidate_rows": [np.array(ind, dtype=float) for ind in population],
    }


def run_evotorch(iterations: int, popsize: int) -> dict[str, object]:
    def fitness(x):
        return torch.tensor(torch_error(x), dtype=torch.float32)

    problem = Problem(
        "min",
        fitness,
        solution_length=4,
        initial_bounds=BOUNDS,
        dtype=torch.float32,
    )
    searcher = SNES(problem, stdev_init=0.7, popsize=popsize)
    searcher.run(iterations)
    best = searcher.status["best"].values.detach().cpu().numpy().astype(float)
    return {
        "best_error": float(searcher.status["best_eval"]),
        "best_solution": [float(v) for v in best.tolist()],
        "candidate_rows": [best],
    }


class SearchArchiveProblem(PymooProblem):
    def __init__(self):
        super().__init__(
            n_var=4,
            n_obj=2,
            xl=np.full(4, BOUNDS[0], dtype=float),
            xu=np.full(4, BOUNDS[1], dtype=float),
        )

    def _evaluate(self, x, out, *args, **kwargs):
        errors = np.array([torch_error(row) for row in x], dtype=float)
        norms = np.sum(x * x, axis=1)
        out["F"] = np.column_stack([errors, norms])


def run_pymoo(pop_size: int, n_gen: int, seed: int) -> dict[str, object]:
    result = pymoo_minimize(
        SearchArchiveProblem(),
        NSGA2(pop_size=pop_size),
        get_termination("n_gen", n_gen),
        seed=seed,
        verbose=False,
    )
    front_x = np.atleast_2d(result.X).astype(float)
    front_f = np.atleast_2d(result.F).astype(float)
    return {
        "front_size": int(len(front_x)),
        "min_error": float(np.min(front_f[:, 0])),
        "min_norm": float(np.min(front_f[:, 1])),
        "candidate_rows": [row for row in front_x],
    }


def run_positive_tests() -> dict[str, object]:
    optuna_run = run_optuna(n_trials=24, seed=42)
    deap_run = run_deap(pop_size=28, n_gen=10, seed=42)
    evotorch_run = run_evotorch(iterations=12, popsize=36)
    pymoo_run = run_pymoo(pop_size=28, n_gen=15, seed=42)
    archive = _archive_candidate_rows(
        list(optuna_run["candidate_rows"])
        + list(deap_run["candidate_rows"])
        + list(evotorch_run["candidate_rows"])
        + list(pymoo_run["candidate_rows"])
    )

    return {
        "optuna_best_error": optuna_run["best_error"],
        "deap_best_error": deap_run["best_error"],
        "evotorch_best_error": evotorch_run["best_error"],
        "pymoo_front_size": pymoo_run["front_size"],
        "pymoo_min_error": pymoo_run["min_error"],
        "archive_coverage": archive["coverage"],
        "archive_num_elites": archive["num_elites"],
        "archive_objective_max": archive["objective_max"],
        "pass": bool(
            optuna_run["best_error"] < 1.0
            and deap_run["best_error"] < 0.2
            and evotorch_run["best_error"] < 0.2
            and pymoo_run["front_size"] >= 5
            and pymoo_run["min_error"] < 0.2
            and archive["coverage"] >= 0.25
            and archive["objective_max"] > -0.2
        ),
    }


def run_negative_tests() -> dict[str, object]:
    zero = np.zeros(4, dtype=float)
    zero_error = torch_error(zero)
    degenerate_archive = _archive_candidate_rows([zero for _ in range(12)])

    return {
        "zero_candidate_error": zero_error,
        "degenerate_archive_coverage": degenerate_archive["coverage"],
        "degenerate_archive_num_elites": degenerate_archive["num_elites"],
        "pass": bool(
            zero_error > 3.0
            and degenerate_archive["coverage"] < 0.05
            and degenerate_archive["num_elites"] == 1
        ),
    }


def run_boundary_tests() -> dict[str, object]:
    optuna_run = run_optuna(n_trials=8, seed=7)
    deap_run = run_deap(pop_size=16, n_gen=5, seed=7)
    evotorch_run = run_evotorch(iterations=6, popsize=24)
    pymoo_run = run_pymoo(pop_size=18, n_gen=8, seed=7)
    archive = _archive_candidate_rows(
        list(optuna_run["candidate_rows"])
        + list(deap_run["candidate_rows"])
        + list(evotorch_run["candidate_rows"])
        + list(pymoo_run["candidate_rows"])
    )

    best_single = min(
        optuna_run["best_error"],
        deap_run["best_error"],
        evotorch_run["best_error"],
    )
    return {
        "best_single_method_error": best_single,
        "pymoo_front_size": pymoo_run["front_size"],
        "archive_coverage": archive["coverage"],
        "pass": bool(
            best_single < 1.0
            and pymoo_run["front_size"] >= 3
            and archive["coverage"] >= 0.08
        ),
    }


if __name__ == "__main__":
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    overall_pass = bool(positive["pass"] and negative["pass"] and boundary["pass"])

    results = {
        "name": "sim_integration_search_archive_stack",
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_bundle": "search_archive_stack",
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "overall_pass": overall_pass,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_integration_search_archive_stack_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, default=str)
    print(f"overall_pass={results['overall_pass']} -> {out_path}")
