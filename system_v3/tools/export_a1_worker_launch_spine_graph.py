#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import networkx as nx

from a1_worker_launch_spine_models import load_a1_worker_launch_spine


def main() -> int:
    parser = argparse.ArgumentParser(description="Export one A1 worker launch spine as GraphML through the local spec-object stack.")
    parser.add_argument("--spine-json", required=True)
    parser.add_argument("--out-graphml", required=True)
    args = parser.parse_args()

    out_path = Path(args.out_graphml)
    if not out_path.is_absolute():
        raise SystemExit("non_absolute_out_graphml")

    spine = load_a1_worker_launch_spine(Path(args.spine_json))
    graph = spine.to_graph()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(graph, out_path)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
