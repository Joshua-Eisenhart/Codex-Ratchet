"""Bounded smoke test for the six-worker nested graph chain."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

import pytest


WORKER_CHAIN = [
    "A2IntakeWorker",
    "A2ContradictionWorker",
    "A2KernelPromotionWorker",
    "A1RosettaWorker",
    "A1StrippedWorker",
    "A1CartridgeWorker",
]

WORKER_MODULE_CANDIDATES = [
    "system_v5.workers",
    "system_v5.worker_chain",
    "system_v5.nested_graph_workers",
    "system_v5.pipeline",
    "system_v5.a2_workers",
    "system_v5.a1_workers",
]


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_temp_repo(temp_root: Path) -> Path:
    repo_root = temp_root / "repo"
    a2_state = repo_root / "system_v5" / "a2_state"
    a1_state = repo_root / "system_v5" / "a1_state"
    docs_dir = repo_root / "docs"

    docs_dir.mkdir(parents=True, exist_ok=True)
    a2_state.mkdir(parents=True, exist_ok=True)
    a1_state.mkdir(parents=True, exist_ok=True)

    source_doc = docs_dir / "tiny_source.md"
    source_doc.write_text(
        "\n".join(
            [
                "# Tiny Source",
                "",
                "This doc seeds the smoke chain.",
                "It mentions a simple kernel and a rosetta mapping.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    _write_json(
        a2_state / "doc_index.json",
        {
            "schema": "A2_DOC_INDEX_v1",
            "documents": [
                {
                    "path": str(source_doc.relative_to(repo_root)),
                    "layer": "SOURCE",
                    "canon_status": "READ_ONLY_SOURCE",
                    "size_bytes": source_doc.stat().st_size,
                }
            ],
        },
    )
    _write_json(
        a2_state / "rosetta.json",
        {
            "version": 1,
            "mappings": {
                "kernel": {
                    "b_spec_id": "S_TERM_KERNEL",
                    "binds": "S_L0_MATH",
                    "state": "TERM_PERMITTED",
                    "admitted_cycle": True,
                }
            },
        },
    )
    return repo_root


def _load_worker_class(class_name: str):
    for module_name in WORKER_MODULE_CANDIDATES:
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue
        worker_cls = getattr(module, class_name, None)
        if worker_cls is not None:
            return worker_cls
    pytest.skip(f"{class_name} is not available in any known system_v5 module path")


def _construct_worker(worker_cls, repo_root: Path):
    init_attempts = [
        {"repo_root": repo_root},
        {"workspace": repo_root},
        {"root": repo_root},
        {"repo": repo_root},
        {"base_dir": repo_root},
        {"root_dir": repo_root},
        {"path": repo_root},
        {"repo_root": str(repo_root)},
        {"workspace": str(repo_root)},
        {"root": str(repo_root)},
        {"repo": str(repo_root)},
        {"base_dir": str(repo_root)},
        {"root_dir": str(repo_root)},
        {"path": str(repo_root)},
        {},
    ]
    last_error: Exception | None = None
    for kwargs in init_attempts:
        try:
            return worker_cls(**kwargs)
        except TypeError as exc:
            last_error = exc
    raise AssertionError(f"Could not construct {worker_cls.__name__}: {last_error}")


def _run_worker(worker, input_value: Any) -> Any:
    for method_name in ("run", "process", "execute", "__call__"):
        method = getattr(worker, method_name, None)
        if method is None:
            continue
        try:
            return method(input_value)
        except TypeError:
            try:
                return method()
            except TypeError:
                continue
    raise AssertionError(f"{type(worker).__name__} exposes no runnable method")


def _nodes_from_result(result: Any) -> list[Any]:
    def _coerce_nodes(value: Any) -> list[Any]:
        if isinstance(value, dict):
            return list(value.values())
        if isinstance(value, (list, tuple, set)):
            return list(value)
        return []

    if result is None:
        return []
    if isinstance(result, dict):
        for key in ("nodes", "node_ids", "ids"):
            nodes = _coerce_nodes(result.get(key))
            if nodes:
                return nodes
        return []
    for attr in ("nodes", "node_ids", "ids"):
        nodes = _coerce_nodes(getattr(result, attr, None))
        if nodes:
            return nodes
    graph = getattr(result, "graph", None)
    if graph is not None and hasattr(graph, "nodes"):
        try:
            return list(graph.nodes)
        except TypeError:
            return []
    return []


def test_nested_graph_worker_chain_smoke(tmp_path: Path) -> None:
    repo_root = _build_temp_repo(tmp_path)
    workers = [_construct_worker(_load_worker_class(name), repo_root) for name in WORKER_CHAIN]

    before_files = {path.relative_to(repo_root) for path in repo_root.rglob("*") if path.is_file()}
    stage_input: Any = None
    observed_nodes: list[list[Any]] = []

    for worker in workers:
        result = _run_worker(worker, stage_input)
        nodes = _nodes_from_result(result)
        assert nodes, f"{type(worker).__name__} returned no nodes"
        observed_nodes.append(nodes)
        stage_input = result

    assert all(nodes for nodes in observed_nodes), "every stage should yield at least one node"

    after_files = {path.relative_to(repo_root) for path in repo_root.rglob("*") if path.is_file()}
    created_files = after_files - before_files
    assert created_files, "worker chain did not write any new artifacts"
    assert all(not path.is_absolute() for path in created_files), "created artifacts escaped the temp repo layout"
    assert any(path.parts[:2] == ("system_v5", "a2_state") for path in created_files), "A2 stages did not write into system_v5/a2_state"
    assert any(path.parts[:2] == ("system_v5", "a1_state") for path in created_files), "A1 stages did not write into system_v5/a1_state"

    a2_state = repo_root / "system_v5" / "a2_state"
    a1_state = repo_root / "system_v5" / "a1_state"

    assert (a2_state / "doc_index.json").exists()
    assert (a2_state / "rosetta.json").exists()
    assert any(path.is_file() for path in a2_state.iterdir()), "A2 outputs were not written inside the temp repo layout"
    assert any(path.is_file() for path in a1_state.iterdir()), "A1 outputs were not written inside the temp repo layout"
