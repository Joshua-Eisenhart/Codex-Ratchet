# Package Inventory: .venv_spec_graph
**Date**: 2026-03-22
**Environment**: `/home/ratchet/Desktop/Codex Ratchet/.venv_spec_graph`

## Executive Summary
The `.venv_spec_graph` environment contains **232** total packages. It represents a heavy-duty research and verification stack, incorporating advanced topological analysis, formal verification (SMT), and machine learning (GNN).

## Stack Categorization

### 1. Base Stack (Core Infrastructure)
*Core data science, graph theory, and utility libraries.*
- **Top Packages**: `numpy`, `networkx`, `pandas`, `scipy`, `matplotlib`, `scikit-learn`, `pydantic`, `igraph`, `sympy`, `requests`, `PyYAML`, `GitPython`.
- **Count**: ~25 packages.

### 2. Phase 1 (Dev & Testing)
*Testing frameworks, linters, and developer utilities.*
- **Top Packages**: `pytest`, `black`, `coverage`, `anybadge`, `tabulate`, `tqdm`, `rich`, `ipython`, `ipywidgets`, `click`, `typer`.
- **Count**: ~30 packages.

### 3. Phase 2 (Logic, Verification & Advanced Analysis)
*Tools for formal methods, GNNs, and topological data analysis.*
- **Top Packages**: `egglog`, `crosshair-tool`, `dvc`, `gudhi`, `leidenalg`, `z3-solver`, `cvc5`, `mutmut`, `hypothesis`, `PySMT`, `TopoNetX`, `torch`, `torch-geometric`, `kingdon`, `clifford`, `pyRankMCDA`, `dotmotif`, `hypernetx`.
- **Count**: ~35 packages.

### 4. Transitive Dependencies
*Lower-level libraries required by the above stacks.*
- **Examples**: `attrs`, `certifi`, `charset-normalizer`, `idna`, `packaging`, `six`, `typing-extensions`, `urllib3`, `aiohttp`, `fsspec`.
- **Count**: ~142 packages.

## Flags & Observations

### ⚠️ Large Packages
- **`torch` (2.10.0)**: Machine learning backend, typically >500MB.
- **`z3-solver` & `cvc5`**: SMT solvers with heavy binary components.
- **`gudhi`**: Large C++ based topological library.

### 🔍 Unexpected / Out-of-Scope Packages
- **Web/Async Stack**: `Hypercorn`, `starlette`, `aiohttp`. (Indicates potential web service or API components).
- **Task Queue Stack**: `celery`, `amqp`, `kombu`, `billiard`. (Suggests background processing capabilities).
- **Database/Graph DB**: `SQLAlchemy`, `py2neo`. (Indicates potential SQL or Neo4j integration).
- **Connectomics**: `neuprint-python`. (Very specific to brain mapping; may be a vestigial or highly specialized dependency).

## Conclusion
The environment is healthy but significantly "heavier" than a standard data science stack, primarily due to the inclusion of `torch`, multiple SMT solvers, and topological tools. No critical conflicts were identified.
