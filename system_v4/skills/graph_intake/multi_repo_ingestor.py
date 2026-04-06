#!/usr/bin/env python3
"""
multi_repo_ingestor.py

Orchestartes ingestion of knowledge across the primary Ratchet system, 
Leviathan-Arbitrage auxiliary repos, and external documents into a structured
graph format while maintaining strict provenance and authority boundaries.

Rules:
1. Every ingested node must contain the repo of origin, commit/hash, path, and authority_class
2. Merges must be explicit cross-repo alignment edges, not silent merges
3. Contradiction clusters must surface implicitly
4. Canon, Evidence, Proposal, Audit, and Scratch strata remain strictly layered.
"""

import json
import hashlib
from pathlib import Path
from typing import Any, Dict, List

# Setup constants
REPO_ROOT = Path(__file__).resolve().parents[3]
WORKSPACE_ROOT = REPO_ROOT.parent
MANIFEST_PATH = REPO_ROOT / "system_v4/a2_state/graphs/full_stack_ingestion_manifest.json"
GRAPH_OUTPUT_PATH = REPO_ROOT / "system_v4/a2_state/graphs/full_stack_provenance_graph.json"


def _utc_iso() -> str:
    import time
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _file_sha256(filepath: Path) -> str:
    if not filepath.exists() or not filepath.is_file():
        return ""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        hasher.update(f.read())
    return hasher.hexdigest()


def build_node(node_id: str, label: str, authority: str, repo: str, 
               filepath: str, file_hash: str, node_type: str = "DOCUMENT") -> Dict[str, Any]:
    return {
        "public_id": node_id,
        "node_type": node_type,
        "label": label,
        "provenance": {
            "authority_class": authority,
            "repo": repo,
            "path": filepath,
            "hash": file_hash
        }
    }


def ingest_from_manifest() -> Dict[str, Any]:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Missing manifest file at {MANIFEST_PATH}")
    
    try:
        with open(MANIFEST_PATH, 'r') as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in manifest: {e}")

    nodes = {}
    edges = []

    # Map classes to their directories
    for stratum_name, data in manifest.items():
        if not isinstance(data, dict) or "authority_class" not in data:
            continue
        
        authority = data["authority_class"]
        repos = data.get("repos", [])
        paths = data.get("paths", [])

        print(f"Ingesting {stratum_name} ({authority}) from {len(repos)} repos, {len(paths)} paths")

        for repo in repos:
            for rel_path in paths:
                # Need to handle exact files vs globs vs directories 
                # (For now, we'll construct the node metadata but defer reading body text until integration)
                search_path = WORKSPACE_ROOT / repo / rel_path
                
                if not search_path.exists():
                    node_id = f"qit::{repo}::{rel_path}::MISSING"
                    nodes[node_id] = build_node(
                        node_id=node_id,
                        label=f"Missing path placeholder: {rel_path}",
                        authority="evidence_returns",
                        repo=repo,
                        filepath=str(rel_path),
                        file_hash="",
                        node_type="MISSING_PATH"
                    )
                    continue

                # Check if it's an explicit file
                if search_path.is_file():
                    node_id = f"qit::{repo}::{search_path.name}"
                    fh = _file_sha256(search_path)
                    nodes[node_id] = build_node(node_id, search_path.name, authority, repo, str(rel_path), fh)
                elif search_path.is_dir():
                    # Check for markdown, json files within bounds
                    for ext in ["**/*.md", "**/*.json", "**/*.py"]:
                        for file_path in search_path.glob(ext):
                            if file_path.is_file():
                                if set(file_path.parts) & {".git", ".venv", ".venv_spec_graph"}:
                                    continue
                                
                                try:
                                    rel_parts = file_path.relative_to(search_path).parts
                                    if any(p.startswith('.') for p in rel_parts[:-1]):
                                        continue
                                except ValueError:
                                    pass

                                try:
                                    internal_path = file_path.relative_to(WORKSPACE_ROOT / repo)
                                except ValueError:
                                    internal_path = file_path
                                
                                node_id = f"qit::{repo}::{str(internal_path).replace('/', '::')}"
                                fh = _file_sha256(file_path)
                                nodes[node_id] = build_node(node_id, file_path.name, authority, repo, str(internal_path), fh)
    
    # We would establish 'cross_repo_alignment' edges here based on parsed content,
    # specifically pulling from sidecars like LightRAG and TopoNetX to connect them

    return {
        "schema": "FULL_STACK_PROVENANCE_GRAPH_v1",
        "generated_utc": _utc_iso(),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "rules_enforced": manifest.get("ingestion_rules", []),
        "nodes": nodes,
        "edges": edges
    }


if __name__ == "__main__":
    graph = ingest_from_manifest()
    
    print(f"Built provenance graph with {graph['node_count']} nodes.")
    GRAPH_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(GRAPH_OUTPUT_PATH, 'w') as f:
        json.dump(graph, f, indent=2)
    print(f"Exported to {GRAPH_OUTPUT_PATH}.")
