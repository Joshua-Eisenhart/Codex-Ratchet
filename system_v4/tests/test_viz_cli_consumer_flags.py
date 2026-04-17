from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_PATH = REPO_ROOT / "system_v4" / "visualization" / "cli.py"
sys.path.insert(0, str(REPO_ROOT))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_accepts_consumer_for_view_best_commands() -> None:
    cli = _load_module(CLI_PATH, "viz_cli")
    parser = cli._build_parser()

    args = parser.parse_args(
        [
            "view-best-report",
            "--root",
            "/tmp/viz_runs_transport",
            "--sim",
            "parallel_transport_s2_classical",
            "--consumer",
            "viewer_surface_smoke",
        ]
    )

    assert args.command == "view-best-report"
    assert args.consumer == "viewer_surface_smoke"


def test_cli_accepts_consumer_for_view_launch_commands() -> None:
    cli = _load_module(CLI_PATH, "viz_cli")
    parser = cli._build_parser()

    args = parser.parse_args(
        [
            "view-launch-run",
            "--run",
            "/tmp/viz_runs_transport/demo_run",
            "--consumer",
            "viewer_surface_smoke",
            "--dry-run",
        ]
    )

    assert args.command == "view-launch-run"
    assert args.consumer == "viewer_surface_smoke"
    assert args.dry_run is True
