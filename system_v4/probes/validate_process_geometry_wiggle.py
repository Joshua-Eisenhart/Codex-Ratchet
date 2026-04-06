#!/usr/bin/env python3
"""
validate_process_geometry_wiggle.py
==================================

Mechanical validator for the exploratory process/geometry wiggle probe.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROBE_RESULTS = ROOT.parent / "a2_state" / "sim_results"
OUTPUT_PATH = ROOT / "a2_state" / "sim_results" / "process_geometry_wiggle_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    probe = load_json(PROBE_RESULTS / "process_geometry_wiggle.json")
    process = probe["process_wiggle"]
    geometry = probe["geometry_wiggle"]

    r10 = process["r=1.0"]
    r07 = process["r=0.7"]
    r04 = process["r=0.4"]
    r02 = process["r=0.2"]
    rows = [r10, r07, r04, r02]

    gates = [
        gate(
            probe["schema"] == "PROCESS_GEOMETRY_WIGGLE_v1"
            and "Exploratory process/geometry wiggle" in probe["note"]
            and set(process.keys()) == {"r=1.0", "r=0.7", "r=0.4", "r=0.2"}
            and set(geometry.keys()) == {"overlaps", "norms"},
            "PG1_process_geometry_surface_is_explicit_and_exploratory",
            {
                "schema": probe["schema"],
                "note": probe["note"],
                "process_keys": sorted(process.keys()),
                "geometry_keys": sorted(geometry.keys()),
            },
        ),
        gate(
            all(row["overlaps"]["ax4_endpoint_vs_ax6_endpoint"] == 0.0 for row in rows)
            and all(row["overlaps"]["ax4_path_vs_ax6_path"] == 0.0 for row in rows)
            and all(row["overlaps"]["ax4_path_vs_ax6_endpoint"] == 0.0 for row in rows)
            and all(row["norms"]["ax4_endpoint"] < 1e-12 for row in rows)
            and all(row["norms"]["ax4_path"] < 1e-11 for row in rows),
            "PG2_ax4_process_observables_stay_effectively_dead_across_the_r_sweep",
            {
                key: {
                    "overlaps": row["overlaps"],
                    "ax4_norms": {
                        "ax4_endpoint": row["norms"]["ax4_endpoint"],
                        "ax4_path": row["norms"]["ax4_path"],
                    },
                }
                for key, row in process.items()
            },
        ),
        gate(
            all(row["norms"]["ax6_endpoint"] > 0.12 for row in rows)
            and all(row["norms"]["ax6_path"] > 0.95 for row in rows[1:])
            and r10["norms"]["ax6_path"] > r10["norms"]["ax6_endpoint"]
            and r07["norms"]["ax6_path"] > r07["norms"]["ax6_endpoint"]
            and r04["norms"]["ax6_path"] > r04["norms"]["ax6_endpoint"]
            and r02["norms"]["ax6_path"] > r02["norms"]["ax6_endpoint"]
            and r10["norms"]["ax6_endpoint"] > r07["norms"]["ax6_endpoint"] > r04["norms"]["ax6_endpoint"] > r02["norms"]["ax6_endpoint"]
            and r10["norms"]["ax6_path"] < r07["norms"]["ax6_path"] < r04["norms"]["ax6_path"] < r02["norms"]["ax6_path"],
            "PG3_ax6_path_records_dominate_endpoints_and_strengthen_as_r_drops",
            {
                key: {
                    "ax6_endpoint": row["norms"]["ax6_endpoint"],
                    "ax6_path": row["norms"]["ax6_path"],
                }
                for key, row in process.items()
            },
        ),
        gate(
            geometry["overlaps"]["ax0_vs_generic_curvature"] > 0.6
            and geometry["overlaps"]["ax0_vs_torus_extrinsic_transport"] > 0.6
            and geometry["overlaps"]["ax0_vs_torus_curvature_scalar"] < 1e-12
            and geometry["norms"]["generic_curvature"] < 0.05
            and geometry["norms"]["torus_extrinsic_transport"] > 0.4
            and geometry["norms"]["torus_curvature_scalar"] == 1.0,
            "PG4_torus_curvature_scalar_decouples_from_ax0_while_other_geometry_proxies_do_not",
            {
                "overlaps": geometry["overlaps"],
                "norms": geometry["norms"],
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    payload = {
        "name": "process_geometry_wiggle_validation",
        "timestamp": datetime.now(UTC).isoformat(),
        "passed_gates": passed,
        "total_gates": len(gates),
        "score": passed / len(gates) if gates else 0.0,
        "gates": gates,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    if args.pretty:
        print("=" * 72)
        print("PROCESS GEOMETRY WIGGLE VALIDATION")
        print("=" * 72)
        for item in gates:
            status = "PASS" if item["pass"] else "FAIL"
            print(f"{status:<5} {item['name']}")
        print()
        print(f"passed_gates: {passed}/{len(gates)}")
        print(f"score: {payload['score']:.6f}")
        print(f"validation_results: {OUTPUT_PATH}")
    else:
        print(json.dumps(payload, indent=2))

    return 0 if passed == len(gates) else 1


if __name__ == "__main__":
    raise SystemExit(main())
