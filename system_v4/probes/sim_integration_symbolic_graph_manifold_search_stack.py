#!/usr/bin/env python3
"""
sim_integration_symbolic_graph_manifold_search_stack.py

Curated mega-stack reference sim for:
  pytorch + z3 + cvc5 + sympy + clifford + pyg + rustworkx + xgi +
  toponetx + gudhi + datasketch + pynndescent + umap + hdbscan + sklearn +
  optuna + pymoo + ribs + deap + evotorch

Claim:
the solver/topology/manifold feature bank should support a searched control
layer instead of forcing search tools to be integrated ad hoc later.

Positive: clean family bank should admit strong searched recovery.
Negative: collapsed and misaligned bank should resist searched recovery.
Boundary: partially mixed bank should remain recoverable.

This is a classical integration baseline. The point is reusable stack
discipline, not a canonical nonclassical witness.
"""

from __future__ import annotations

import json
import logging
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
import sim_integration_symbolic_graph_manifold_stack as bridge_stack
import sympy as sp
import torch
import umap
import xgi
from clifford import Cl
from cvc5 import Kind
from datasketch import MinHash, MinHashLSH
from deap import base as deap_base, creator, tools
from evotorch import Problem
from evotorch.algorithms import SNES
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


classification = "classical_baseline"
divergence_log = (
    "Classical integration baseline: this is a searched mega-stack witness "
    "built on top of the solver/topology/manifold feature bank."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing tensor feature bank, search objective, and searched feature weighting surface",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing tree-law sanity witness on the direct cycle carrier and in the reused family bank",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT cross-check of the same tree-law witness",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic Laplacian root witness for the direct carrier sanity surface",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing rotor geometry for the direct carrier sanity surface",
    },
    "pyg": {
        "tried": True,
        "used": True,
        "reason": "load-bearing graph tensor surface for direct adjacency and degree sanity",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing graph diameter and component sanity witness",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing hypergraph line-graph witness on the same direct carrier",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing simplicial incidence sanity witness on the same carrier",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Rips reconstruction sanity witness on the same carrier",
    },
    "datasketch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing MinHash/LSH locality witness on searched transformed family descriptors",
    },
    "pynndescent": {
        "tried": True,
        "used": True,
        "reason": "load-bearing approximate neighbor purity witness on searched transformed rows",
    },
    "umap": {
        "tried": True,
        "used": True,
        "reason": "load-bearing searched embedding validation on the transformed family bank",
    },
    "hdbscan": {
        "tried": True,
        "used": True,
        "reason": "load-bearing searched clustering validation on the transformed family bank",
    },
    "sklearn": {
        "tried": True,
        "used": True,
        "reason": "load-bearing ARI, silhouette, and scaling on searched transformed rows",
    },
    "optuna": {
        "tried": True,
        "used": True,
        "reason": "load-bearing TPE search over the shared feature-weighting objective",
    },
    "pymoo": {
        "tried": True,
        "used": True,
        "reason": "load-bearing NSGA-II search over separation score vs regularization cost",
    },
    "ribs": {
        "tried": True,
        "used": True,
        "reason": "load-bearing shared archive over candidate weight vectors emitted by all search lanes",
    },
    "deap": {
        "tried": True,
        "used": True,
        "reason": "load-bearing genetic search over the shared feature-weighting objective",
    },
    "evotorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SNES search over the shared feature-weighting objective",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "clifford": "load_bearing",
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


optuna.logging.set_verbosity(optuna.logging.WARNING)
logging.getLogger("evotorch").setLevel(logging.ERROR)
warnings.filterwarnings(
    "ignore",
    message="n_jobs value 1 overridden to 1 by setting random_state",
    category=UserWarning,
)

BOUNDS = (-2.0, 2.0)
GROUP_SLICES = (
    slice(0, 9),   # graph/topology
    slice(9, 13),  # spectral
    slice(13, 15), # solver
    slice(15, 18), # geometric
)


def _direct_surface_sanity() -> dict[str, object]:
    _, blades = Cl(2)
    e1 = blades["e1"]
    e2 = blades["e2"]
    e12 = blades["e12"]
    coords = []
    for theta in (0.0, math.pi / 2.0, math.pi, 3.0 * math.pi / 2.0):
        rotor = math.cos(theta / 2.0) + math.sin(theta / 2.0) * e12
        vec = rotor * e1 * ~rotor
        coords.append([float(vec[e1]), float(vec[e2])])
    coords_t = torch.tensor(coords, dtype=torch.float32)

    directed = [(0, 1), (1, 2), (2, 3), (3, 0), (1, 0), (2, 1), (3, 2), (0, 3)]
    edge_index = torch.tensor(directed, dtype=torch.long).t().contiguous()
    data = Data(x=coords_t, edge_index=edge_index)
    dense_adj = to_dense_adj(data.edge_index, max_num_nodes=4)[0]
    degree_pattern = [int(v) for v in pyg_degree(data.edge_index[0], num_nodes=4).tolist()]

    graph = rx.PyGraph()
    nodes = [graph.add_node(i) for i in range(4)]
    for a, b in ((0, 1), (1, 2), (2, 3), (3, 0)):
        graph.add_edge(nodes[a], nodes[b], 1.0)
    diameter = max(
        max(rx.dijkstra_shortest_path_lengths(graph, node, lambda w: w).values())
        for node in nodes
    )

    hypergraph = xgi.Hypergraph()
    hypergraph.add_nodes_from(range(4))
    hypergraph.add_edges_from([[0, 1], [1, 2], [2, 3], [3, 0]])
    line_graph_nodes = int(xgi.convert.to_line_graph(hypergraph).number_of_nodes())

    simplicial = SimplicialComplex([[0, 1], [1, 2], [2, 3], [3, 0]])
    b1 = simplicial.incidence_matrix(rank=1, signed=True)

    simplex_tree = gudhi.RipsComplex(
        points=coords_t.detach().cpu().numpy(),
        max_edge_length=1.5,
    ).create_simplex_tree(max_dimension=1)

    adjacency = sp.Matrix([[int(v) for v in row] for row in dense_adj.tolist()])
    laplacian = sp.diag(*[sum(adjacency.row(i)) for i in range(adjacency.rows)]) - adjacency
    roots = sorted(float(complex(root.evalf()).real) for root in sp.nroots(sp.expand(laplacian.charpoly().as_expr())))

    n, e = Ints("n e")
    z3_solver = Solver()
    z3_solver.add(n == 4, e == 4, e == n - 1)
    z3_status = "sat" if z3_solver.check() == sat else "unsat"

    tm = cvc5.TermManager()
    cvc5_solver = cvc5.Solver(tm)
    cvc5_solver.setLogic("QF_LIA")
    int_sort = tm.getIntegerSort()
    n_term = tm.mkConst(int_sort, "n")
    e_term = tm.mkConst(int_sort, "e")
    cvc5_solver.assertFormula(tm.mkTerm(Kind.EQUAL, n_term, tm.mkInteger(4)))
    cvc5_solver.assertFormula(tm.mkTerm(Kind.EQUAL, e_term, tm.mkInteger(4)))
    cvc5_solver.assertFormula(tm.mkTerm(Kind.EQUAL, e_term, tm.mkTerm(Kind.SUB, n_term, tm.mkInteger(1))))
    cvc5_status = "sat" if cvc5_solver.checkSat().isSat() else "unsat"

    passed = bool(
        degree_pattern == [2, 2, 2, 2]
        and int(diameter) == 2
        and line_graph_nodes == 4
        and [int(v) for v in simplicial.shape] == [4, 4]
        and [int(v) for v in b1.shape] == [4, 4]
        and int(simplex_tree.num_simplices()) == 8
        and all(abs(a - b) <= 1e-4 for a, b in zip(roots, [0.0, 2.0, 2.0, 4.0]))
        and z3_status == "unsat"
        and cvc5_status == "unsat"
    )
    return {
        "degree_pattern": degree_pattern,
        "diameter": float(diameter),
        "line_graph_nodes": line_graph_nodes,
        "toponetx_shape": [int(v) for v in simplicial.shape],
        "gudhi_num_simplices": int(simplex_tree.num_simplices()),
        "sympy_laplacian_roots": roots,
        "z3_tree_status": z3_status,
        "cvc5_tree_status": cvc5_status,
        "pass": passed,
    }


def _build_dataset(mode: str) -> tuple[torch.Tensor, np.ndarray]:
    if mode == "positive":
        jitter_scale = 0.02
        collapse_strength = 0.0
        scramble_rows = False
    elif mode == "boundary":
        jitter_scale = 0.04
        collapse_strength = 0.25
        scramble_rows = False
    elif mode == "negative":
        jitter_scale = 0.02
        collapse_strength = 0.90
        scramble_rows = True
    else:
        raise ValueError(f"unknown mode: {mode}")

    samples = []
    labels = []
    for kind in bridge_stack.FAMILY_ORDER:
        for sample_index in range(bridge_stack.SAMPLES_PER_FAMILY):
            samples.append(bridge_stack._extract_sample(kind, sample_index, jitter_scale))
            labels.append(bridge_stack.FAMILY_LABELS[kind])

    rows = torch.tensor([sample["feature_vector"] for sample in samples], dtype=torch.float32)
    rows = bridge_stack._collapse_rows(rows, collapse_strength, scramble_rows=scramble_rows)
    return rows, np.array(labels, dtype=int)


def _group_weights(params) -> torch.Tensor:
    params_t = torch.tensor(np.asarray(params, dtype=np.float32), dtype=torch.float32)
    scalars = 0.25 + 2.0 * torch.sigmoid(params_t)
    expanded = torch.empty(18, dtype=torch.float32)
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


def _signature_tokens(row: np.ndarray, topk: int = 6) -> set[str]:
    indices = np.argsort(-np.abs(row))[:topk]
    return {f"d{int(idx)}:{row[int(idx)]:.1f}" for idx in indices}


def _lsh_precision(x_np: np.ndarray, labels: np.ndarray) -> float:
    lsh = MinHashLSH(threshold=0.7, num_perm=64)
    minhashes = []
    for idx, row in enumerate(x_np):
        mh = MinHash(num_perm=64)
        for token in sorted(_signature_tokens(row)):
            mh.update(token.encode("utf-8"))
        lsh.insert(f"p{idx}", mh)
        minhashes.append(mh)

    scores = []
    for idx, mh in enumerate(minhashes):
        matches = [int(key[1:]) for key in lsh.query(mh) if key != f"p{idx}"]
        if not matches:
            continue
        same = sum(labels[j] == labels[idx] for j in matches)
        scores.append(same / len(matches))
    return float(np.mean(scores)) if scores else 0.0


def _nn_purity(x_np: np.ndarray, labels: np.ndarray) -> float:
    index = NNDescent(x_np, n_neighbors=6, random_state=0)
    neighbors, _ = index.query(x_np, k=6)
    scores = []
    for idx, row in enumerate(neighbors):
        local = [nbr for nbr in row.tolist() if nbr != idx]
        if not local:
            continue
        same = sum(labels[nbr] == labels[idx] for nbr in local)
        scores.append(same / len(local))
    return float(np.mean(scores)) if scores else 0.0


def _cluster_metrics(x_np: np.ndarray, labels: np.ndarray) -> dict[str, float]:
    scaled = StandardScaler().fit_transform(x_np)
    embedding = umap.UMAP(
        n_components=2,
        n_neighbors=6,
        min_dist=0.0,
        metric="euclidean",
        random_state=0,
    ).fit_transform(scaled)

    predicted = hdbscan.HDBSCAN(min_cluster_size=4, min_samples=2).fit_predict(embedding)
    assigned_mask = predicted != -1
    assigned_fraction = float(np.mean(assigned_mask))
    cluster_count = len(set(predicted.tolist()) - {-1})
    ari = float(adjusted_rand_score(labels, predicted))

    silhouette = -1.0
    if assigned_mask.sum() >= 4 and len(set(predicted[assigned_mask].tolist())) >= 2:
        silhouette = float(silhouette_score(embedding[assigned_mask], predicted[assigned_mask]))

    purity_mass = 0
    purity_total = 0
    for cluster in sorted(set(predicted.tolist()) - {-1}):
        members = [idx for idx, value in enumerate(predicted) if value == cluster]
        if not members:
            continue
        label_counts: dict[int, int] = {}
        for member in members:
            label_counts[int(labels[member])] = label_counts.get(int(labels[member]), 0) + 1
        purity_mass += max(label_counts.values())
        purity_total += len(members)
    cluster_purity = float(purity_mass / purity_total) if purity_total else 0.0

    return {
        "assigned_fraction": assigned_fraction,
        "cluster_count": float(cluster_count),
        "ari": ari,
        "silhouette": silhouette,
        "cluster_purity": cluster_purity,
    }


def _validate_candidate(rows: torch.Tensor, labels: np.ndarray, params) -> dict[str, float]:
    transformed = _transform_rows(rows, params)
    x_np = transformed.detach().cpu().numpy()
    return {
        "lsh_precision": _lsh_precision(x_np, labels),
        "knn_purity": _nn_purity(x_np, labels),
        **_cluster_metrics(x_np, labels),
        "objective_score": _objective_score(rows, labels, params),
    }


def _candidate_measures(params) -> np.ndarray:
    weights = _group_weights(params).detach().cpu().numpy()
    graph_weight = float(np.mean(weights[GROUP_SLICES[0]]))
    manifold_weight = float(np.mean(weights[GROUP_SLICES[3]]))
    return np.array(
        [
            min(max((graph_weight - 0.25) / 2.0, 0.0), 1.0),
            min(max((manifold_weight - 0.25) / 2.0, 0.0), 1.0),
        ],
        dtype=float,
    )


def _archive_candidates(rows: torch.Tensor, labels: np.ndarray, candidates: list[np.ndarray]) -> dict[str, object]:
    archive = GridArchive(solution_dim=4, dims=[6, 6], ranges=[(0.0, 1.0), (0.0, 1.0)])
    for params in candidates:
        archive.add_single(
            solution=np.asarray(params, dtype=float),
            objective=_objective_score(rows, labels, params),
            measures=_candidate_measures(params),
        )
    return {
        "coverage": float(archive.stats.coverage),
        "num_elites": int(archive.stats.num_elites),
        "objective_max": float(archive.stats.obj_max),
        "candidate_count": len(candidates),
    }


def run_optuna(rows: torch.Tensor, labels: np.ndarray, n_trials: int, seed: int) -> dict[str, object]:
    def objective(trial):
        params = np.array([trial.suggest_float(f"x{i}", BOUNDS[0], BOUNDS[1]) for i in range(4)], dtype=float)
        return _objective_score(rows, labels, params)

    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=seed),
    )
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    candidate_rows = [
        np.array([trial.params.get(f"x{i}", 0.0) for i in range(4)], dtype=float)
        for trial in study.trials
    ]
    best = np.array([study.best_params[f"x{i}"] for i in range(4)], dtype=float)
    return {
        "best_score": float(study.best_value),
        "best_solution": [float(v) for v in best.tolist()],
        "candidate_rows": candidate_rows,
    }


def run_deap(rows: torch.Tensor, labels: np.ndarray, pop_size: int, n_gen: int, seed: int) -> dict[str, object]:
    random.seed(seed)
    np.random.seed(seed)

    if "FitnessMaxSymbolicGraphManifoldSearch" not in creator.__dict__:
        creator.create("FitnessMaxSymbolicGraphManifoldSearch", deap_base.Fitness, weights=(1.0,))
    if "SymbolicGraphManifoldSearchIndividual" not in creator.__dict__:
        creator.create(
            "SymbolicGraphManifoldSearchIndividual",
            list,
            fitness=creator.FitnessMaxSymbolicGraphManifoldSearch,
        )

    toolbox = deap_base.Toolbox()
    toolbox.register("attr_float", random.uniform, BOUNDS[0], BOUNDS[1])
    toolbox.register(
        "individual",
        tools.initRepeat,
        creator.SymbolicGraphManifoldSearchIndividual,
        toolbox.attr_float,
        n=4,
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
    return {
        "best_score": float(best.fitness.values[0]),
        "best_solution": [float(v) for v in best],
        "candidate_rows": [np.array(ind, dtype=float) for ind in population],
    }


def run_evotorch(rows: torch.Tensor, labels: np.ndarray, iterations: int, popsize: int) -> dict[str, object]:
    def fitness(x):
        return torch.tensor(_objective_score(rows, labels, x), dtype=torch.float32)

    problem = Problem(
        "max",
        fitness,
        solution_length=4,
        initial_bounds=BOUNDS,
        dtype=torch.float32,
    )
    searcher = SNES(problem, stdev_init=0.6, popsize=popsize)
    searcher.run(iterations)
    best = searcher.status["best"].values.detach().cpu().numpy().astype(float)
    return {
        "best_score": float(searcher.status["best_eval"]),
        "best_solution": [float(v) for v in best.tolist()],
        "candidate_rows": [best],
    }


class SearchBridgeProblem(PymooProblem):
    def __init__(self, rows: torch.Tensor, labels: np.ndarray):
        self.rows = rows
        self.labels = labels
        super().__init__(
            n_var=4,
            n_obj=2,
            xl=np.full(4, BOUNDS[0], dtype=float),
            xu=np.full(4, BOUNDS[1], dtype=float),
        )

    def _evaluate(self, x, out, *args, **kwargs):
        scores = np.array([_objective_score(self.rows, self.labels, row) for row in x], dtype=float)
        penalties = np.array([float(np.mean(np.abs(_group_weights(row).detach().cpu().numpy() - 1.0))) for row in x], dtype=float)
        out["F"] = np.column_stack([-scores, penalties])


def run_pymoo(rows: torch.Tensor, labels: np.ndarray, pop_size: int, n_gen: int, seed: int) -> dict[str, object]:
    result = pymoo_minimize(
        SearchBridgeProblem(rows, labels),
        NSGA2(pop_size=pop_size),
        get_termination("n_gen", n_gen),
        seed=seed,
        verbose=False,
    )
    front_x = np.atleast_2d(result.X).astype(float)
    front_f = np.atleast_2d(result.F).astype(float)
    max_score = float(np.max(-front_f[:, 0]))
    return {
        "front_size": int(len(front_x)),
        "max_score": max_score,
        "candidate_rows": [row for row in front_x],
    }


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
            and result["assigned_fraction"] >= 0.95
            and result["cluster_count"] == 3.0
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
            and result["assigned_fraction"] >= 0.90
            and result["cluster_count"] == 3.0
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
    overall_pass = bool(
        direct_surface["pass"] and positive["pass"] and negative["pass"] and boundary["pass"]
    )
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
        "sim_integration_symbolic_graph_manifold_search_stack_results.json",
    )
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, sort_keys=True)
    print(f"overall_pass={results['overall_pass']} -> {out_path}")


if __name__ == "__main__":
    main()
