from __future__ import annotations

import argparse
import json
from pathlib import Path

from system_v4.visualization.action_bundle import write_action_bundle
from system_v4.visualization.action_commands import collect_action_commands, render_action_commands
from system_v4.visualization.action_plan import collect_action_plan, render_action_plan
from system_v4.visualization.action_runner import collect_bundle_steps, render_bundle_steps, run_bundle_step
from system_v4.visualization.batch_reporting import (
    collect_batch_report,
    collect_multi_batch_report,
    render_batch_report,
    render_dedupe_report,
    render_multi_batch_report,
    render_multi_dedupe_report,
)
from system_v4.visualization.best_run_viewer import (
    collect_best_viewer_launch,
    launch_best_viewer,
    render_best_viewer_launch,
)
from system_v4.visualization.comparison import compare_run_dirs
from system_v4.visualization.exporters.hopf_bundle import export_hopf_bundle
from system_v4.visualization.exporters.hopf_torus_atlas import export_hopf_torus_atlas
from system_v4.visualization.exporters.synthetic_atlas import export_synthetic_atlas
from system_v4.visualization.exporters.transport_s2 import export_transport_s2
from system_v4.visualization.inspection import inspect_run_dir
from system_v4.visualization.reporting import render_comparison_report, render_run_report
from system_v4.visualization.status import collect_status_report, render_status_report
from system_v4.visualization.triage import collect_triage_report, render_triage_report
from system_v4.visualization.validator import validate_run_dir
from system_v4.visualization.viewers.scrubber_pyvista import open_scrubber
from system_v4.visualization.viewer_launcher import collect_viewer_launch, launch_viewer, render_viewer_launch


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Visualization replay lane CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export", help="Export a replay run")
    export_parser.add_argument("target", choices=["transport_s2", "hopf_bundle", "synthetic_atlas", "hopf_torus_atlas"])
    export_parser.add_argument("--run-id", required=True)
    export_parser.add_argument(
        "--out-dir",
        default="system_v4/probes/a2_state/viz_runs",
    )
    export_parser.add_argument("--steps-per-arc", type=int, default=200)
    export_parser.add_argument("--n-points", type=int, default=128)
    export_parser.add_argument("--fiber-points", type=int, default=32)
    export_parser.add_argument("--fiber-twist", type=float, default=1.0)
    export_parser.add_argument("--frame-count", type=int, default=9)
    export_parser.add_argument("--n-theta1", type=int, default=8)
    export_parser.add_argument("--n-theta2", type=int, default=8)

    validate_parser = subparsers.add_parser("validate", help="Validate a replay run")
    validate_parser.add_argument("--run", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect replay run capabilities and overlays")
    inspect_parser.add_argument("--run", required=True)

    compare_parser = subparsers.add_parser("compare", help="Compare two replay runs")
    compare_parser.add_argument("--left", required=True)
    compare_parser.add_argument("--right", required=True)

    report_parser = subparsers.add_parser("report", help="Render a human-readable replay report")
    report_group = report_parser.add_mutually_exclusive_group(required=True)
    report_group.add_argument("--run")
    report_group.add_argument("--left")
    report_parser.add_argument("--right")

    batch_parser = subparsers.add_parser("batch-report", help="Render a human-readable report for many replay runs")
    batch_parser.add_argument("--root", action="append", required=True)

    batch_json_parser = subparsers.add_parser("batch-inspect", help="Inspect many replay runs as JSON")
    batch_json_parser.add_argument("--root", action="append", required=True)

    dedupe_parser = subparsers.add_parser("dedupe-report", help="Render replay-equivalent duplicate groups")
    dedupe_parser.add_argument("--root", action="append", required=True)

    dedupe_json_parser = subparsers.add_parser("dedupe-inspect", help="Inspect replay-equivalent duplicate groups as JSON")
    dedupe_json_parser.add_argument("--root", action="append", required=True)

    triage_parser = subparsers.add_parser("triage-report", help="Render safe keep/archive/re-export recommendations")
    triage_parser.add_argument("--root", action="append", required=True)

    triage_json_parser = subparsers.add_parser("triage-inspect", help="Inspect keep/archive/re-export recommendations as JSON")
    triage_json_parser.add_argument("--root", action="append", required=True)

    status_parser = subparsers.add_parser("status-report", help="Render a compact operator brief across replay runs")
    status_parser.add_argument("--root", action="append", required=True)

    status_json_parser = subparsers.add_parser("status-inspect", help="Inspect a compact operator brief as JSON")
    status_json_parser.add_argument("--root", action="append", required=True)

    action_plan_parser = subparsers.add_parser("action-plan-report", help="Render a safe keep/now/later action plan")
    action_plan_parser.add_argument("--root", action="append", required=True)

    action_plan_json_parser = subparsers.add_parser("action-plan-inspect", help="Inspect a safe keep/now/later action plan as JSON")
    action_plan_json_parser.add_argument("--root", action="append", required=True)

    action_commands_parser = subparsers.add_parser("action-commands-report", help="Render exact dry-run commands for the action plan")
    action_commands_parser.add_argument("--root", action="append", required=True)

    action_commands_json_parser = subparsers.add_parser("action-commands-inspect", help="Inspect exact dry-run commands for the action plan as JSON")
    action_commands_json_parser.add_argument("--root", action="append", required=True)

    action_bundle_parser = subparsers.add_parser("action-bundle-write", help="Write a dry-run shell script and JSON bundle for the action plan")
    action_bundle_parser.add_argument("--root", action="append", required=True)
    action_bundle_parser.add_argument("--out-dir", required=True)
    action_bundle_parser.add_argument("--prefix", default="viz_action_bundle")

    bundle_steps_parser = subparsers.add_parser("action-bundle-steps-report", help="Render named steps from a written action bundle")
    bundle_steps_parser.add_argument("--bundle", required=True)

    bundle_steps_json_parser = subparsers.add_parser("action-bundle-steps-inspect", help="Inspect named steps from a written action bundle as JSON")
    bundle_steps_json_parser.add_argument("--bundle", required=True)

    bundle_step_run_parser = subparsers.add_parser("action-bundle-step-run", help="Run one selected step from a written action bundle")
    bundle_step_run_parser.add_argument("--bundle", required=True)
    bundle_step_run_parser.add_argument("--step-id", required=True)
    bundle_step_run_parser.add_argument("--allow-archive", action="store_true")
    bundle_step_run_parser.add_argument("--dry-run", action="store_true")

    view_parser = subparsers.add_parser("view", help="Open a replay run viewer")
    view_parser.add_argument("--run", required=True)
    view_parser.add_argument("--off-screen-smoke", action="store_true")

    view_launch_parser = subparsers.add_parser("view-launch-report", help="Render the isolated viewer launch command")
    view_launch_parser.add_argument("--run", required=True)
    view_launch_parser.add_argument("--consumer")
    view_launch_parser.add_argument("--off-screen-smoke", action="store_true")
    view_launch_parser.add_argument("--python-executable")

    view_launch_json_parser = subparsers.add_parser("view-launch-inspect", help="Inspect the isolated viewer launch command as JSON")
    view_launch_json_parser.add_argument("--run", required=True)
    view_launch_json_parser.add_argument("--consumer")
    view_launch_json_parser.add_argument("--off-screen-smoke", action="store_true")
    view_launch_json_parser.add_argument("--python-executable")

    view_launch_run_parser = subparsers.add_parser("view-launch-run", help="Run the viewer through the isolated PyVista environment")
    view_launch_run_parser.add_argument("--run", required=True)
    view_launch_run_parser.add_argument("--consumer")
    view_launch_run_parser.add_argument("--off-screen-smoke", action="store_true")
    view_launch_run_parser.add_argument("--dry-run", action="store_true")
    view_launch_run_parser.add_argument("--python-executable")

    view_best_parser = subparsers.add_parser("view-best-report", help="Render the isolated viewer launch for the current best run of a sim family")
    view_best_parser.add_argument("--root", action="append", required=True)
    view_best_parser.add_argument("--sim", required=True)
    view_best_parser.add_argument("--consumer")
    view_best_parser.add_argument("--off-screen-smoke", action="store_true")
    view_best_parser.add_argument("--python-executable")

    view_best_json_parser = subparsers.add_parser("view-best-inspect", help="Inspect the isolated viewer launch for the current best run of a sim family as JSON")
    view_best_json_parser.add_argument("--root", action="append", required=True)
    view_best_json_parser.add_argument("--sim", required=True)
    view_best_json_parser.add_argument("--consumer")
    view_best_json_parser.add_argument("--off-screen-smoke", action="store_true")
    view_best_json_parser.add_argument("--python-executable")

    view_best_run_parser = subparsers.add_parser("view-best-run", help="Run the isolated viewer for the current best run of a sim family")
    view_best_run_parser.add_argument("--root", action="append", required=True)
    view_best_run_parser.add_argument("--sim", required=True)
    view_best_run_parser.add_argument("--consumer")
    view_best_run_parser.add_argument("--off-screen-smoke", action="store_true")
    view_best_run_parser.add_argument("--dry-run", action="store_true")
    view_best_run_parser.add_argument("--python-executable")

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
        elif args.target == "synthetic_atlas":
            run_dir = export_synthetic_atlas(
                args.run_id,
                Path(args.out_dir),
                frame_count=args.frame_count,
            )
        elif args.target == "hopf_torus_atlas":
            run_dir = export_hopf_torus_atlas(
                args.run_id,
                Path(args.out_dir),
                frame_count=args.frame_count,
                n_theta1=args.n_theta1,
                n_theta2=args.n_theta2,
            )
        else:
            parser.error(f"unsupported export target: {args.target}")
        print(run_dir)
        return 0

    if args.command == "validate":
        report = validate_run_dir(Path(args.run))
        print(json.dumps(report, indent=2))
        return 0 if report["ok"] else 1

    if args.command == "inspect":
        report = inspect_run_dir(Path(args.run))
        print(json.dumps(report, indent=2))
        return 0 if report["validation_ok"] else 1

    if args.command == "compare":
        report = compare_run_dirs(Path(args.left), Path(args.right))
        print(json.dumps(report, indent=2))
        return 0 if report["validation_ok"]["left"] and report["validation_ok"]["right"] else 1

    if args.command == "report":
        if args.run:
            print(render_run_report(Path(args.run)))
            return 0
        if not args.right:
            parser.error("--report with --left also requires --right")
        print(render_comparison_report(Path(args.left), Path(args.right)))
        return 0

    if args.command == "batch-report":
        roots = [Path(root) for root in args.root]
        if len(roots) == 1:
            print(render_batch_report(roots[0]))
        else:
            print(render_multi_batch_report(roots))
        return 0

    if args.command == "batch-inspect":
        roots = [Path(root) for root in args.root]
        report = collect_batch_report(roots[0]) if len(roots) == 1 else collect_multi_batch_report(roots)
        print(json.dumps(report, indent=2))
        return 0

    if args.command == "dedupe-report":
        roots = [Path(root) for root in args.root]
        if len(roots) == 1:
            print(render_dedupe_report(roots[0]))
        else:
            print(render_multi_dedupe_report(roots))
        return 0

    if args.command == "dedupe-inspect":
        roots = [Path(root) for root in args.root]
        report = collect_batch_report(roots[0]) if len(roots) == 1 else collect_multi_batch_report(roots)
        print(json.dumps({
            "roots": report["roots"],
            "root_count": report["root_count"],
            "duplicate_groups": report["duplicate_groups"],
        }, indent=2))
        return 0

    if args.command == "triage-report":
        print(render_triage_report([Path(root) for root in args.root]))
        return 0

    if args.command == "triage-inspect":
        report = collect_triage_report([Path(root) for root in args.root])
        print(json.dumps(report, indent=2))
        return 0

    if args.command == "status-report":
        print(render_status_report([Path(root) for root in args.root]))
        return 0

    if args.command == "status-inspect":
        report = collect_status_report([Path(root) for root in args.root])
        print(json.dumps(report, indent=2))
        return 0

    if args.command == "action-plan-report":
        print(render_action_plan([Path(root) for root in args.root]))
        return 0

    if args.command == "action-plan-inspect":
        report = collect_action_plan([Path(root) for root in args.root])
        print(json.dumps(report, indent=2))
        return 0

    if args.command == "action-commands-report":
        print(render_action_commands([Path(root) for root in args.root]))
        return 0

    if args.command == "action-commands-inspect":
        report = collect_action_commands([Path(root) for root in args.root])
        print(json.dumps(report, indent=2))
        return 0

    if args.command == "action-bundle-write":
        result = write_action_bundle(
            [Path(root) for root in args.root],
            Path(args.out_dir),
            prefix=args.prefix,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "action-bundle-steps-report":
        print(render_bundle_steps(Path(args.bundle)))
        return 0

    if args.command == "action-bundle-steps-inspect":
        print(json.dumps(collect_bundle_steps(Path(args.bundle)), indent=2))
        return 0

    if args.command == "action-bundle-step-run":
        result = run_bundle_step(
            Path(args.bundle),
            args.step_id,
            allow_archive=args.allow_archive,
            dry_run=args.dry_run,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    if args.command == "view":
        result = open_scrubber(
            Path(args.run),
            off_screen=args.off_screen_smoke,
            show=not args.off_screen_smoke,
        )
        if args.off_screen_smoke:
            print(json.dumps(result, indent=2))
        return 0

    if args.command == "view-launch-report":
        print(
            render_viewer_launch(
                Path(args.run),
                consumer=args.consumer,
                off_screen_smoke=args.off_screen_smoke,
                python_executable=Path(args.python_executable) if args.python_executable else None,
            )
        )
        return 0

    if args.command == "view-launch-inspect":
        print(
            json.dumps(
                collect_viewer_launch(
                    Path(args.run),
                    consumer=args.consumer,
                    off_screen_smoke=args.off_screen_smoke,
                    python_executable=Path(args.python_executable) if args.python_executable else None,
                ),
                indent=2,
            )
        )
        return 0

    if args.command == "view-launch-run":
        result = launch_viewer(
            Path(args.run),
            consumer=args.consumer,
            off_screen_smoke=args.off_screen_smoke,
            dry_run=args.dry_run,
            python_executable=Path(args.python_executable) if args.python_executable else None,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    if args.command == "view-best-report":
        print(
            render_best_viewer_launch(
                [Path(root) for root in args.root],
                args.sim,
                consumer=args.consumer,
                off_screen_smoke=args.off_screen_smoke,
                python_executable=Path(args.python_executable) if args.python_executable else None,
            )
        )
        return 0

    if args.command == "view-best-inspect":
        print(
            json.dumps(
                collect_best_viewer_launch(
                    [Path(root) for root in args.root],
                    args.sim,
                    consumer=args.consumer,
                    off_screen_smoke=args.off_screen_smoke,
                    python_executable=Path(args.python_executable) if args.python_executable else None,
                ),
                indent=2,
            )
        )
        return 0

    if args.command == "view-best-run":
        result = launch_best_viewer(
            [Path(root) for root in args.root],
            args.sim,
            consumer=args.consumer,
            off_screen_smoke=args.off_screen_smoke,
            dry_run=args.dry_run,
            python_executable=Path(args.python_executable) if args.python_executable else None,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["launch_result"]["ok"] else 1

    parser.error(f"unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
