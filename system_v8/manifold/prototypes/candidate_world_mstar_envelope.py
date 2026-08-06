#!/usr/bin/env python3
"""Run the finite M★ candidate world through independent engine lanes.

The markdown is a candidate specification.  This envelope executes one
bounded exact-small slice of it: a 3-shell x 4 x 4 typed field, retained OB
histories, explicit bracket/control markers, coherent/dephased path sums, and
an exhaustive finite recurrent-basin map.  Each lane computes independently;
the controller compares receipts only after the lanes finish.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / "candidate_world_mstar_config_v1.json"
JULIA_PROJECT = ROOT.parents[2] / "system_v5" / "julia_carrier"
SIM_PY = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
TORCH_PY = Path("/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3")
JULIA = Path("/opt/homebrew/bin/julia")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_stage(name: str, command: list[str], env: dict[str, str], cwd: Path, timeout: float, output_dir: Path) -> dict[str, Any]:
    started = time.monotonic()
    try:
        proc = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout, check=False)
        status = "PASS" if proc.returncode == 0 else "FAIL"
        stdout, stderr = proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        proc = None
        status = "TIMEOUT"
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
    stage = {
        "name": name,
        "command": command,
        "returncode": None if proc is None else proc.returncode,
        "status": status,
        "elapsed_seconds": time.monotonic() - started,
        "stdout": stdout[-8000:],
        "stderr": stderr[-8000:],
    }
    (output_dir / f"{name}.stdout.txt").write_text(stdout, encoding="utf-8")
    (output_dir / f"{name}.stderr.txt").write_text(stderr, encoding="utf-8")
    return stage


def load_receipt(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def lane_source(name: str) -> Path:
    return ROOT / f"candidate_world_mstar_{name}.{'jl' if name == 'julia' else 'py'}"


def numeric(value: Any) -> float:
    return float(value)


def structural_rows(lanes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    keys = ("node_count", "path_count_per_node", "order_sensitive_nodes", "bracket_sensitive_nodes")
    rows = {}
    for key in keys:
        rows[key] = {name: int(payload["structural"][key]) for name, payload in lanes.items()}
    rows["basin_count"] = {name: int(payload["structural"]["basin"]["basin_count"]) for name, payload in lanes.items()}
    rows["subbasin_count"] = {name: int(payload["structural"]["basin"]["subbasin_count"]) for name, payload in lanes.items()}
    rows["chirality_gap_sum"] = {name: numeric(payload["structural"]["chirality_gap_sum"]) for name, payload in lanes.items()}
    return rows


def run(source: Path, output_dir: Path, timeout_seconds: float = 300.0) -> dict[str, Any]:
    source = source.expanduser().resolve(strict=True)
    output_dir = output_dir.expanduser().resolve()
    if output_dir.exists():
        raise ValueError("output directory must be fresh")
    output_dir.mkdir(parents=True)
    lanes_dir = output_dir / "lanes"
    lanes_dir.mkdir()
    source_digest = sha256(source)
    config_digest = sha256(CONFIG)
    common = {
        "MSTAR_SOURCE_MARKDOWN": str(source),
        "MSTAR_CONFIG": str(CONFIG),
        "PYTHONHASHSEED": "0",
        "MPLCONFIGDIR": str(output_dir / "mpl"),
        "NUMBA_CACHE_DIR": str(output_dir / "numba"),
    }
    (output_dir / "mpl").mkdir(); (output_dir / "numba").mkdir()
    stages = []
    commands = {
        "python": [str(SIM_PY), str(ROOT / "candidate_world_mstar_python.py"), "--source-markdown", str(source), "--output", str(lanes_dir / "python.json")],
        "jax": [str(SIM_PY), "-I", str(ROOT / "candidate_world_mstar_jax.py"), "--source-markdown", str(source), "--output", str(lanes_dir / "jax.json")],
        "torch": [str(TORCH_PY), "-I", str(ROOT / "candidate_world_mstar_torch.py"), "--source-markdown", str(source), "--output", str(lanes_dir / "torch.json")],
        "julia": [str(JULIA), "--startup-file=no", f"--project={JULIA_PROJECT}", str(ROOT / "candidate_world_mstar_julia.jl")],
    }
    for name in ("python", "jax", "torch"):
        stages.append(run_stage(name, commands[name], {**os.environ, **common}, ROOT, timeout_seconds, output_dir))
    julia_env = {**os.environ, **common, "JULIA_LOAD_PATH": "@:@stdlib", "JULIA_PROJECT": str(JULIA_PROJECT), "MSTAR_OUTPUT": str(lanes_dir / "julia.json"), "JULIA_DEPOT_PATH": f"{output_dir / 'julia_depot'}:{Path.home() / '.julia'}"}
    (output_dir / "julia_depot").mkdir()
    stages.append(run_stage("julia", commands["julia"], julia_env, ROOT, timeout_seconds, output_dir))

    lane_receipts: dict[str, dict[str, Any]] = {}
    for name in ("python", "jax", "torch", "julia"):
        path = lanes_dir / f"{name}.json"
        if path.is_file():
            lane_receipts[name] = load_receipt(path)
    source_checks = {name: payload.get("source_sha256") == source_digest for name, payload in lane_receipts.items()}
    config_checks = {name: payload.get("config_sha256") == config_digest for name, payload in lane_receipts.items()}
    structural = structural_rows(lane_receipts) if len(lane_receipts) == 4 else {}
    structural_equal = bool(structural) and all(len(set(values.values())) == 1 for key, values in structural.items() if key not in {"chirality_gap_sum"})
    chirality_values = structural.get("chirality_gap_sum", {})
    chirality_max_divergence = (max(chirality_values.values()) - min(chirality_values.values())) if chirality_values else float("inf")
    controls = {name: payload.get("controls", {}) for name, payload in lane_receipts.items()}
    controls_pass = len(controls) == 4 and all(all(bool(value) for value in row.values()) for row in controls.values())
    all_pass = bool(
        len(lane_receipts) == 4
        and all(stage["status"] == "PASS" for stage in stages)
        and all(source_checks.values())
        and all(config_checks.values())
        and structural_equal
        and chirality_max_divergence < 1e-8
        and controls_pass
    )
    receipt = {
        "schema": "codex_ratchet.candidate_world_mstar_envelope.v1",
        "candidate_id": "M-star-dual-gradient-ijk-history-fibre",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "cr_truth_claim": False,
        "controller_reads_engine_results_after_lanes": True,
        "source_path": str(source),
        "source_sha256": source_digest,
        "source_line_count": len(source.read_text(encoding="utf-8").splitlines()),
        "config_path": str(CONFIG),
        "config_sha256": config_digest,
        "engine_mode": "all_three_full_sims",
        "claim_path": "julia_structural_reference_jax_workhorse_pytorch_graph_network",
        "stages": stages,
        "engines": {
            name: {
                "ran": True,
                "source_path": payload.get("source_path"),
                "source_sha256": payload.get("source_sha256"),
                "packages_used": payload.get("packages_used", []),
                "aligned_packages_load_bearing": payload.get("aligned_packages_load_bearing", []),
                "reads_peer_result": payload.get("reads_peer_result"),
                "classification": payload.get("classification"),
                "promotion_allowed": payload.get("promotion_allowed"),
            }
            for name, payload in lane_receipts.items()
        },
        "lane_receipts": lane_receipts,
        "source_digest_checks": source_checks,
        "config_digest_checks": config_checks,
        "structural_comparison": structural,
        "structural_equal": structural_equal,
        "chirality_max_divergence": chirality_max_divergence,
        "controls": controls,
        "controls_pass": controls_pass,
        "all_pass": all_pass,
        "claim_ceiling": "All-three bounded candidate-world execution and cross-lane structural parity only; not CR validation, physical truth, formal admission, or promotion.",
        "blocked_consumers": ["CR admission", "MSS promotion", "physics bridge", "continuum basin claims"],
    }
    (output_dir / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "lanes": sorted(lane_receipts), "structural_equal": structural_equal, "chirality_max_divergence": chirality_max_divergence, "controls_pass": controls_pass, "output": str(output_dir / "receipt.json")}, sort_keys=True))
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-markdown", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=float, default=300.0)
    args = parser.parse_args(argv)
    result = run(args.source_markdown, args.output_dir, args.timeout_seconds)
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
