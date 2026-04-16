from __future__ import annotations

import argparse
import json
from pathlib import Path

from system_v4.visualization.exporters.hopf_bundle import export_hopf_bundle
from system_v4.visualization.exporters.transport_s2 import export_transport_s2
from system_v4.visualization.validator import validate_run_dir
from system_v4.visualization.viewers.scrubber_pyvista import open_scrubber


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Visualization replay lane CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export", help="Export a replay run")
    export_parser.add_argument("target", choices=["transport_s2", "hopf_bundle"])
    export_parser.add_argument("--run-id", required=True)
    export_parser.add_argument(
        "--out-dir",
        default="system_v4/probes/a2_state/viz_runs",
    )
    export_parser.add_argument("--steps-per-arc", type=int, default=200)
    export_parser.add_argument("--n-points", type=int, default=128)
    export_parser.add_argument("--fiber-points", type=int, default=32)
    export_parser.add_argument("--fiber-twist", type=float, default=1.0)

    validate_parser = subparsers.add_parser("validate", help="Validate a replay run")
    validate_parser.add_argument("--run", required=True)

    view_parser = subparsers.add_parser("view", help="Open a replay run viewer")
    view_parser.add_argument("--run", required=True)

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "export":
        if args.target == "transport_s2":
            run_dir = export_transport_s2(args.run_id, Path(args.out_dir), steps_per_arc=args.steps_per_arc)
        elif args.target == "hopf_bundle":
            run_dir = export_hopf_bundle(
                args.run_id,
                Path(args.out_dir),
                n_points=args.n_points,
                fiber_points=args.fiber_points,
                fiber_twist=args.fiber_twist,
            )
        else:
            parser.error(f"unsupported export target: {args.target}")
        print(run_dir)
        return 0

    if args.command == "validate":
        report = validate_run_dir(Path(args.run))
        print(json.dumps(report, indent=2))
        return 0 if report["ok"] else 1

    if args.command == "view":
        open_scrubber(Path(args.run))
        return 0

    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
