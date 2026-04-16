#!/usr/bin/env python3
"""
sim_integration_equivariant_symbolic_graph_manifold_search_stack.py

Curated mega-stack extension for:
  pytorch + z3 + cvc5 + sympy + clifford + e3nn + geomstats + pyg +
  rustworkx + xgi + toponetx + gudhi + datasketch + pynndescent + umap +
  hdbscan + sklearn + optuna + pymoo + ribs + deap + evotorch

Claim:
the searched solver/topology/manifold stack should also admit equivariant and
Riemannian geometry features in the same reusable lane instead of bolting them
on later.
"""

from __future__ import annotations

import json
import math
import os
import random
import warnings

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex-mpl")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
os.makedirs(os.environ["NUMBA_CACHE_DIR"], exist_ok=True)

import cvc5
import gudhi
import hdbscan
import numpy as np
import optuna
import rustworkx as rx
import sim_integration_symbolic_graph_manifold_search_stack as base_stack
import sim_integration_symbolic_graph_manifold_stack as bridge_stack
import sympy as sp
import torch
import umap
import xgi
from clifford import Cl
from cvc5 import Kind
from datasketch import MinHash, MinHashLSH
from deap import base as deap_base, creator, tools
from e3nn import o3
from evotorch import Problem
from evotorch.algorithms import SNES
from geomstats.geometry.hypersphere import Hypersphere
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem as PymooProblem
from pymoo.optimize import minimize as pymoo_minimize
from pymoo.termination import get_termination
from pynndescent import NNDescent
from ribs.archives import GridArchive
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler
from toponetx.classes import SimplicialComplex
from torch_geometric.data import Data
from torch_geometric.utils import degree as pyg_degree
from torch_geometric.utils import to_dense_adj
from z3 import Ints, Solver, sat

import geomstats.backend as gs


classification = "classical_baseline"
divergence_log = (
    "Classical integration baseline: this extends the searched symbolic graph "
    "manifold stack with equivariant and Riemannian geometry features."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing feature tensors and searched weighting surface"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing tree-law witness on direct and sampled carriers"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent SMT cross-check of the same witness"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing Laplacian spectral witness on the direct carrier"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing rotor coordinates for direct and sampled carriers"},
    "e3nn": {"tried": True, "used": True, "reason": "load-bearing spherical-harmonic equivariant features on lifted carrier points"},
    "geomstats": {"tried": True, "used": True, "reason": "load-bearing hypersphere geodesic features on the same lifted carrier points"},
    "pyg": {"tried": True, "used": True, "reason": "load-bearing graph tensor surface for direct adjacency and degree signatures"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing graph diameter and component sanity witness"},
    "xgi": {"tried": True, "used": True, "reason": "load-bearing hypergraph line-graph witness"},
    "toponetx": {"tried": True, "used": True, "reason": "load-bearing simplicial incidence witness"},
    "gudhi": {"tried": True, "used": True, "reason": "load-bearing Rips reconstruction witness"},
    "datasketch": {"tried": True, "used": True, "reason": "load-bearing MinHash/LSH locality witness on transformed rows"},
    "pynndescent": {"tried": True, "used": True, "reason": "load-bearing approximate neighbor purity witness"},
    "umap": {"tried": True, "used": True, "reason": "load-bearing searched embedding of the transformed bank"},
    "hdbscan": {"tried": True, "used": True, "reason": "load-bearing searched clustering on the transformed bank"},
    "sklearn": {"tried": True, "used": True, "reason": "load-bearing ARI, silhouette, and scaling metrics"},
    "optuna": {"tried": True, "used": True, "reason": "load-bearing TPE search over the shared weighting objective"},
    "pymoo": {"tried": True, "used": True, "reason": "load-bearing NSGA-II search over score vs regularization"},
    "ribs": {"tried": True, "used": True, "reason": "load-bearing shared archive across all search lanes"},
    "deap": {"tried": True, "used": True, "reason": "load-bearing genetic search over the shared weighting objective"},
    "evotorch": {"tried": True, "used": True, "reason": "load-bearing SNES search over the shared weighting objective"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "clifford": "load_bearing",
    "e3nn": "load_bearing",
    "geomstats": "load_bearing",
    "pyg": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "datasketch": "load_bearing",
    "pynndescent": "load_bearing",
    "umap": "load_bearing",
    "hdbscan": "load_bearing",
    "sklearn": "load_bearing",
    "optuna": "load_bearing",
    "pymoo": "load_bearing",
    "ribs": "load_bearing",
    "deap": "load_bearing",
    "evotorch": "load_bearing",
}

warnings.filterwarnings(
    "ignore",
    message="n_jobs value 1 overridden to 1 by setting random_state",
    category=UserWarning,
)
optuna.logging.set_verbosity(optuna.logging.WARNING)

BOUNDS = (-2.0, 2.0)
EXTRA_SLICES = (
    slice(18, 20),  # e3nn norms
    slice(20, 23),  # geomstats geodesic features
)
GROUP_SLICES = base_stack.GROUP_SLICES + EXTRA_SLICES


def _lift_to_s2(coords: torch.Tensor, sample_index: int) -> torch.Tensor:
    z = 0.18 * torch.sin(torch.arange(coords.shape[0], dtype=torch.float32) + float(sample_index))
    xyz = torch.cat([coords, z.unsqueeze(1)], dim=1)
    return xyz / torch.linalg.norm(xyz, dim=1, keepdim=True)


def _equivariant_geom_features(kind: str, sample_index: int, jitter_scale: float) -> list[float]:
    coords, edges, _ = bridge_stack._shape_spec(kind, sample_index, jitter_scale)
    xyz = _lift_to_s2(coords, sample_index)

    harmonics = o3.spherical_harmonics([1, 2], xyz, normalize=True)
    l1_norm = float(torch.linalg.norm(harmonics[:, :3], dim=1).mean().item())
    l2_norm = float(torch.linalg.norm(harmonics[:, 3:], dim=1).mean().item())

    sphere = Hypersphere(dim=2)
    gs_xyz = gs.array(xyz.detach().cpu().numpy())
    edge_dists = [float(sphere.metric.dist(gs_xyz[a], gs_xyz[b])) for a, b in edges]
    pairwise = []
    for i in range(xyz.shape[0]):
        for j in range(i + 1, xyz.shape[0]):
            pairwise.append(float(sphere.metric.dist(gs_xyz[i], gs_xyz[j])))
    mean_edge_dist = float(np.mean(edge_dists))
    max_pairwise_dist = float(np.max(pairwise))
    std_pairwise_dist = float(np.std(pairwise))
    return [l1_norm, l2_norm, mean_edge_dist, max_pairwise_dist, std_pairwise_dist]


def _direct_surface_sanity() -> dict[str, object]:
    base = base_stack._direct_surface_sanity()

    _, blades = Cl(2)
    e1 = blades["e1"]
    e2 = blades["e2"]
    e12 = blades["e12"]
    coords = []
    for theta in (0.0, math.pi / 2.0, math.pi, 3.0 * math.pi / 2.0):
        rotor = math.cos(theta / 2.0) + math.sin(theta / 2.0) * e12
        vec = rotor * e1 * ~rotor
        coords.append([float(vec[e1]), float(vec[e2])])
    xyz = torch.tensor([[x, y, 0.0] for x, y in coords], dtype=torch.float32)
    xyz = xyz / torch.linalg.norm(xyz, dim=1, keepdim=True)

    y1 = o3.spherical_harmonics("1o", xyz, normalize=True)
    e3nn_opposite = bool(torch.allclose(y1[0], -y1[2], atol=1e-5))

    sphere = Hypersphere(dim=2)
    gs_xyz = gs.array(xyz.detach().cpu().numpy())
    adjacent = float(sphere.metric.dist(gs_xyz[0], gs_xyz[1]))
    opposite = float(sphere.metric.dist(gs_xyz[0], gs_xyz[2]))
    geomstats_ok = abs(adjacent - (math.pi / 2.0)) <= 1e-4 and abs(opposite - math.pi) <= 1e-4

    base.update(
        {
            "e3nn_opposite_harmonics": e3nn_opposite,
            "geomstats_adjacent_distance": adjacent,
            "geomstats_opposite_distance": opposite,
        }
    )
    base["pass"] = bool(base["pass"] and e3nn_opposite and geomstats_ok)
    return base


def _build_dataset(mode: str) -> tuple[torch.Tensor, np.ndarray]:
    rows, labels = base_stack._build_dataset(mode)
    if mode == "positive":
        jitter_scale = 0.02
    elif mode == "boundary":
        jitter_scale = 0.04
    else:
        jitter_scale = 0.02

    extras = []
    for kind in bridge_stack.FAMILY_ORDER:
        for sample_index in range(bridge_stack.SAMPLES_PER_FAMILY):
            extras.append(_equivariant_geom_features(kind, sample_index, jitter_scale))
    extra_rows = torch.tensor(extras, dtype=torch.float32)
    return torch.cat([rows, extra_rows], dim=1), labels


def _group_weights(params) -> torch.Tensor:
    params_t = torch.tensor(np.asarray(params, dtype=np.float32), dtype=torch.float32)
    scalars = 0.25 + 2.0 * torch.sigmoid(params_t)
    expanded = torch.empty(23, dtype=torch.float32)
    for group_index, group_slice in enumerate(GROUP_SLICES):
        expanded[group_slice] = scalars[group_index]
    return expanded


def _transform_rows(rows: torch.Tensor, params) -> torch.Tensor:
    weights = _group_weights(params)
    weighted = rows * weights
    mean = weighted.mean(dim=0, keepdim=True)
    std = weighted.std(dim=0, keepdim=True) + 1e-6
    return (weighted - mean) / std


def _objective_score(rows: torch.Tensor, labels: np.ndarray, params) -> float:
    transformed = _transform_rows(rows, params)
    labels_t = torch.tensor(labels.tolist(), dtype=torch.long)
    centroids = []
    within = 0.0
    for label in sorted(set(labels.tolist())):
        cluster = transformed[labels_t == label]
        centroid = cluster.mean(dim=0)
        within += float(torch.mean((cluster - centroid) ** 2).item())
        centroids.append(centroid)
    between_terms = []
    for i in range(len(centroids)):
        for j in range(i + 1, len(centroids)):
            between_terms.append(float(torch.linalg.norm(centroids[i] - centroids[j]).item()))
    between = float(np.mean(between_terms))
    regularization = float(torch.mean(torch.abs(_group_weights(params) - 1.0)).item())
    return between - within - 0.08 * regularization


def _validate_candidate(rows: torch.Tensor, labels: np.ndarray, params) -> dict[str, float]:
    transformed = _transform_rows(rows, params)
    x_np = transformed.detach().cpu().numpy()
    return {
        "lsh_precision": base_stack._lsh_precision(x_np, labels),
        "knn_purity": base_stack._nn_purity(x_np, labels),
        **base_stack._cluster_metrics(x_np, labels),
        "objective_score": _objective_score(rows, labels, params),
    }


def _candidate_measures(params) -> np.ndarray:
    weights = _group_weights(params).detach().cpu().numpy()
    equivariant_weight = float(np.mean(weights[EXTRA_SLICES[0]]))
    manifold_weight = float(np.mean(weights[EXTRA_SLICES[1]]))
    return np.array(
        [
            min(max((equivariant_weight - 0.25) / 2.0, 0.0), 1.0),
            min(max((manifold_weight - 0.25) / 2.0, 0.0), 1.0),
        ],
        dtype=float,
    )


def _archive_candidates(rows: torch.Tensor, labels: np.ndarray, candidates: list[np.ndarray]) -> dict[str, object]:
    archive = GridArchive(solution_dim=6, dims=[6, 6], ranges=[(0.0, 1.0), (0.0, 1.0)])
    for params in candidates:
        params = np.asarray(params, dtype=float)
        archive.add_single(
            solution=params,
            objective=_objective_score(rows, labels, params),
            measures=_candidate_measures(params),
        )
    return {
        "coverage": float(archive.stats.coverage),
        "num_elites": int(archive.stats.num_elites),
        "objective_max": float(archive.stats.obj_max),
    }


def run_optuna(rows: torch.Tensor, labels: np.ndarray, n_trials: int, seed: int) -> dict[str, object]:
    def objective(trial):
        params = np.array([trial.suggest_float(f"x{i}", BOUNDS[0], BOUNDS[1]) for i in range(6)], dtype=float)
        return _objective_score(rows, labels, params)

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    candidate_rows = [np.array([trial.params.get(f"x{i}", 0.0) for i in range(6)], dtype=float) for trial in study.trials]
    best = np.array([study.best_params[f"x{i}"] for i in range(6)], dtype=float)
    return {"best_score": float(study.best_value), "best_solution": [float(v) for v in best.tolist()], "candidate_rows": candidate_rows}


def run_deap(rows: torch.Tensor, labels: np.ndarray, pop_size: int, n_gen: int, seed: int) -> dict[str, object]:
    random.seed(seed)
    np.random.seed(seed)
    if "FitnessMaxEquivariantSymbolicGraphManifoldSearch" not in creator.__dict__:
        creator.create("FitnessMaxEquivariantSymbolicGraphManifoldSearch", deap_base.Fitness, weights=(1.0,))
    if "EquivariantSymbolicGraphManifoldSearchIndividual" not in creator.__dict__:
        creator.create(
            "EquivariantSymbolicGraphManifoldSearchIndividual",
            list,
            fitness=creator.FitnessMaxEquivariantSymbolicGraphManifoldSearch,
        )
    toolbox = deap_base.Toolbox()
    toolbox.register("attr_float", random.uniform, BOUNDS[0], BOUNDS[1])
    toolbox.register(
        "individual",
        tools.initRepeat,
        creator.EquivariantSymbolicGraphManifoldSearchIndividual,
        toolbox.attr_float,
        n=6,
    )
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", lambda ind: (_objective_score(rows, labels, ind),))
    toolbox.register("mate", tools.cxBlend, alpha=0.4)
    toolbox.register("mutate", tools.mutGaussian, mu=0.0, sigma=0.35, indpb=0.5)
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
    return {"best_score": float(best.fitness.values[0]), "best_solution": [float(v) for v in best], "candidate_rows": [np.array(ind, dtype=float) for ind in population]}


def run_evotorch(rows: torch.Tensor, labels: np.ndarray, iterations: int, popsize: int) -> dict[str, object]:
    def fitness(x):
        return torch.tensor(_objective_score(rows, labels, x), dtype=torch.float32)

    problem = Problem("max", fitness, solution_length=6, initial_bounds=BOUNDS, dtype=torch.float32)
    searcher = SNES(problem, stdev_init=0.6, popsize=popsize)
    searcher.run(iterations)
    best = searcher.status["best"].values.detach().cpu().numpy().astype(float)
    return {"best_score": float(searcher.status["best_eval"]), "best_solution": [float(v) for v in best.tolist()], "candidate_rows": [best]}


class EquivariantSearchBridgeProblem(PymooProblem):
    def __init__(self, rows: torch.Tensor, labels: np.ndarray):
        self.rows = rows
        self.labels = labels
        super().__init__(n_var=6, n_obj=2, xl=np.full(6, BOUNDS[0], dtype=float), xu=np.full(6, BOUNDS[1], dtype=float))

    def _evaluate(self, x, out, *args, **kwargs):
        scores = np.array([_objective_score(self.rows, self.labels, row) for row in x], dtype=float)
        penalties = np.array([float(np.mean(np.abs(_group_weights(row).detach().cpu().numpy() - 1.0))) for row in x], dtype=float)
        out["F"] = np.column_stack([-scores, penalties])


def run_pymoo(rows: torch.Tensor, labels: np.ndarray, pop_size: int, n_gen: int, seed: int) -> dict[str, object]:
    result = pymoo_minimize(
        EquivariantSearchBridgeProblem(rows, labels),
        NSGA2(pop_size=pop_size),
        get_termination("n_gen", n_gen),
        seed=seed,
        verbose=False,
    )
    front_x = np.atleast_2d(result.X).astype(float)
    front_f = np.atleast_2d(result.F).astype(float)
    return {"front_size": int(len(front_x)), "max_score": float(np.max(-front_f[:, 0])), "candidate_rows": [row for row in front_x]}


def _best_solution(candidates: list[dict[str, object]]) -> np.ndarray:
    best = max(candidates, key=lambda row: float(row["best_score"]))
    return np.array(best["best_solution"], dtype=float)


def _run_case(mode: str, seed: int) -> dict[str, object]:
    rows, labels = _build_dataset(mode)
    optuna_run = run_optuna(rows, labels, n_trials=14, seed=seed)
    deap_run = run_deap(rows, labels, pop_size=18, n_gen=6, seed=seed)
    evotorch_run = run_evotorch(rows, labels, iterations=8, popsize=24)
    pymoo_run = run_pymoo(rows, labels, pop_size=16, n_gen=8, seed=seed)

    best_params = _best_solution([optuna_run, deap_run, evotorch_run])
    validation = _validate_candidate(rows, labels, best_params)
    archive = _archive_candidates(
        rows,
        labels,
        list(optuna_run["candidate_rows"])
        + list(deap_run["candidate_rows"])
        + list(evotorch_run["candidate_rows"])
        + list(pymoo_run["candidate_rows"]),
    )
    result = {
        "optuna_best_score": optuna_run["best_score"],
        "deap_best_score": deap_run["best_score"],
        "evotorch_best_score": evotorch_run["best_score"],
        "pymoo_front_size": pymoo_run["front_size"],
        "pymoo_max_score": pymoo_run["max_score"],
        "archive_coverage": archive["coverage"],
        "archive_num_elites": archive["num_elites"],
        "archive_objective_max": archive["objective_max"],
        **validation,
    }
    if mode == "positive":
        result["pass"] = bool(
            result["optuna_best_score"] >= 5.0
            and result["deap_best_score"] >= 5.0
            and result["evotorch_best_score"] >= 5.0
            and result["pymoo_front_size"] >= 1
            and result["pymoo_max_score"] >= 5.0
            and result["archive_coverage"] >= 0.15
            and result["ari"] >= 0.95
            and result["cluster_purity"] >= 0.95
            and result["knn_purity"] >= 0.95
            and result["lsh_precision"] >= 0.95
        )
    elif mode == "boundary":
        result["pass"] = bool(
            result["optuna_best_score"] >= 3.0
            and result["deap_best_score"] >= 3.0
            and result["evotorch_best_score"] >= 3.0
            and result["pymoo_front_size"] >= 1
            and result["pymoo_max_score"] >= 3.0
            and result["archive_coverage"] >= 0.10
            and result["ari"] >= 0.90
            and result["cluster_purity"] >= 0.90
            and result["knn_purity"] >= 0.90
            and result["lsh_precision"] >= 0.90
        )
    else:
        result["pass"] = bool(
            result["optuna_best_score"] <= 1.5
            and result["deap_best_score"] <= 1.5
            and result["evotorch_best_score"] <= 1.5
            and result["pymoo_max_score"] <= 1.5
            and result["ari"] <= 0.35
            and result["cluster_purity"] <= 0.60
            and result["knn_purity"] <= 0.60
            and result["lsh_precision"] <= 0.60
        )
    return result


def run_positive_tests() -> dict[str, object]:
    return _run_case("positive", seed=42)


def run_negative_tests() -> dict[str, object]:
    return _run_case("negative", seed=17)


def run_boundary_tests() -> dict[str, object]:
    return _run_case("boundary", seed=7)


def main() -> None:
    direct_surface = _direct_surface_sanity()
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    overall_pass = bool(direct_surface["pass"] and positive["pass"] and negative["pass"] and boundary["pass"])
    results = {
        "classification": classification,
        "divergence_log": divergence_log,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "direct_surface": direct_surface,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "overall_pass": overall_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(
        out_dir,
        "sim_integration_equivariant_symbolic_graph_manifold_search_stack_results.json",
    )
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, sort_keys=True)
    print(f"overall_pass={results['overall_pass']} -> {out_path}")


if __name__ == "__main__":
    main()
