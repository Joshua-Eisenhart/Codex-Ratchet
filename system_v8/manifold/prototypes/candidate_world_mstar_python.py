#!/usr/bin/env python3
"""Independent Python lane for the finite M★ candidate world.

The lane consumes only the declared finite configuration and the candidate
markdown's digest.  It does not read another engine's result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import finite_ijk_path_hopfield_proto as model


SOURCE_DEFAULT = Path("/Users/joshuaeisenhart/Desktop/DEEP_RICH_CR_CANDIDATE_WORLD_20260803.md")
CONFIG = Path(__file__).with_name("candidate_world_mstar_config_v1.json")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def interference_l1(path_result: dict) -> float:
    coherent: dict[int, complex] = {}
    incoherent: dict[int, float] = {}
    for history in path_result["histories"]:
        endpoint = tuple(history["endpoint"])
        amplitude = complex(history["amplitude"]["real"], history["amplitude"]["imag"])
        coherent[endpoint] = coherent.get(endpoint, 0j) + amplitude
        incoherent[endpoint] = incoherent.get(endpoint, 0.0) + abs(amplitude) ** 2
    coherent_weights = {key: abs(value) ** 2 for key, value in coherent.items()}
    coherent_total = sum(coherent_weights.values())
    incoherent_total = sum(incoherent.values())
    return sum(
        abs(coherent_weights.get(key, 0.0) / coherent_total - incoherent.get(key, 0.0) / incoherent_total)
        for key in set(coherent_weights) | set(incoherent)
    )


def run(source: Path, output: Path) -> dict:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    result = model.run()
    node_values = list(result["axis0_field"].values())
    left_paths = [model.path_sum(node, -1) for node in model.nodes()]
    right_paths = [model.path_sum(node, 1) for node in model.nodes()]
    left_total = [complex(row["amplitude"]["real"], row["amplitude"]["imag"]) for row in left_paths]
    right_total = [complex(row["amplitude"]["real"], row["amplitude"]["imag"]) for row in right_paths]
    left_interference = [interference_l1(row) for row in left_paths]
    right_interference = [interference_l1(row) for row in right_paths]
    basin = {
        "basin_count": result["attractors"]["basin_count"],
        "basin_sizes": result["attractors"]["basin_sizes"],
        "subbasin_count": result["attractors"]["subbasin_count"],
        "basin_recurrence": result["features"]["basin_recurrence"],
    }
    # The existing finite prototype is the reference implementation of the
    # exact-small relational/path/basin slice.  Add source/config provenance
    # without changing its measurements.
    result.update(
        {
            "schema": "codex_ratchet.candidate_world_mstar.python_lane.v1",
            "candidate_id": config["candidate_id"],
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "reads_peer_result": False,
            "source_path": str(source),
            "source_sha256": sha256(source),
            "source_line_count": len(source.read_text(encoding="utf-8").splitlines()),
            "config_path": str(CONFIG),
            "config_sha256": sha256(CONFIG),
            "engine": "python_reference",
            "packages_used": ["finite_ijk_path_hopfield_proto", "json", "hashlib"],
            "aligned_packages_load_bearing": ["finite relational/path/basin reference"],
            "tool_calls": {
                "finite_path_sum": {
                    "qualified_api": "finite_ijk_path_hopfield_proto.path_sum",
                    "positive_case": "8 retained OB histories per node",
                    "negative_control": "coherent endpoint weights versus dephased endpoint weights",
                    "boundary_case": "path_depth=3 exact enumeration",
                    "gates": ["coherent_vs_dephased_path_difference", "path_count"],
                },
                "hopfield_attractor": {
                    "qualified_api": "finite_ijk_path_hopfield_proto.hopfield_attractor",
                    "positive_case": "finite binary state family enters a recurrent class",
                    "negative_control": "basin-null comparison remains a separate future lane",
                    "boundary_case": "4-bit exhaustive basin map",
                    "gates": ["basin_recurrence", "basin_count"],
                },
            },
            "hands": {
                "left": {
                    "path_count_per_node": left_paths[0]["path_count"],
                    "path_interference_l1_sum": sum(left_interference),
                    "path_interference_l1_min": min(left_interference),
                    "total_amplitude": [{"real": x.real, "imag": x.imag} for x in left_total],
                },
                "right": {
                    "path_count_per_node": right_paths[0]["path_count"],
                    "path_interference_l1_sum": sum(right_interference),
                    "path_interference_l1_min": min(right_interference),
                    "total_amplitude": [{"real": x.real, "imag": x.imag} for x in right_total],
                },
            },
            "structural": {
                "node_count": result["axis0_field"]["node_count"],
                "path_count_per_node": left_paths[0]["path_count"],
                "basin": basin,
                "order_sensitive_nodes": result["deformation"]["order_sensitive_nodes"],
                "bracket_sensitive_nodes": result["deformation"]["bracket_sensitive_nodes"],
                "chirality_gap_sum": result["deformation"]["chirality_plus_minus_gap_sum"],
            },
            "controls": {
                "coherent_vs_dephased": sum(left_interference + right_interference) > 1e-12,
                "opposed_hands_distinguished": result["deformation"]["chirality_plus_minus_gap_sum"] > 1e-12,
                "order_retention": result["features"]["order_retention"],
                "bracket_seam": result["features"]["bracket_seam"],
                "basin_recurrence": result["features"]["basin_recurrence"],
            },
            "claim_ceiling": config["claim_ceiling"],
        }
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-markdown", type=Path, default=SOURCE_DEFAULT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    source = args.source_markdown.expanduser().resolve(strict=True)
    result = run(source, args.output.expanduser().resolve())
    print(
        json.dumps(
            {
                "engine": result["engine"],
                "nodes": result["axis0_field"]["node_count"],
                "basins": result["attractors"]["basin_count"],
                "subbasins": result["attractors"]["subbasin_count"],
                "order_sensitive_nodes": result["deformation"]["order_sensitive_nodes"],
                "bracket_sensitive_nodes": result["deformation"]["bracket_sensitive_nodes"],
                "chirality_gap_sum": result["deformation"]["chirality_plus_minus_gap_sum"],
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
