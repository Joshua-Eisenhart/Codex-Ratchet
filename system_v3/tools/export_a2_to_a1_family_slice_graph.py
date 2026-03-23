#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import networkx as nx

from a2_to_a1_family_slice_models import load_family_slice


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Export one A2_TO_A1_FAMILY_SLICE_v1 into GraphML.")
    parser.add_argument("--family-slice-json", required=True)
    parser.add_argument("--out-graphml", required=True)
    args = parser.parse_args(argv)

    family_slice_json = Path(args.family_slice_json)
    out_graphml = Path(args.out_graphml)
    if not family_slice_json.is_absolute():
        raise SystemExit("non_absolute_family_slice_json")
    if not out_graphml.is_absolute():
        raise SystemExit("non_absolute_out_graphml")

    family_slice = load_family_slice(family_slice_json)
    graph = family_slice.to_graph()
    out_graphml.parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(graph, out_graphml)
    result = {
        "schema": "A2_TO_A1_FAMILY_SLICE_GRAPH_EXPORT_v1",
        "family_slice_json": str(family_slice_json),
        "out_graphml": str(out_graphml),
        "graph_summary": family_slice.graph_summary(),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
