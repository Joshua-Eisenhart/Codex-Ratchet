#!/usr/bin/env python3
"""Run proof/graph gates that make Wizard validation more than prose."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "work" / "mmm_wizard_repair" / "runs" / "wizard_proof_manifest_latest"


WEYL_GRAPH_CHECK = r"""
import importlib.util
import json
import pathlib
import sys
p = pathlib.Path.cwd() / 'system_v4/probes/sim_weyl_geometry_graph_proof_alignment.py'
sys.path.insert(0, str(p.parent))
spec = importlib.util.spec_from_file_location('weyl_graph_proof_alignment', p)
if spec is None or spec.loader is None:
    raise SystemExit(2)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
g = m.build_geometry_schedule()
o = m.prove_stage_ordering()
c = m.prove_chirality_sign_separation()
ok = bool(g.get('is_dag') and o.get('forward_order_sat') and o.get('reverse_order_unsat') and c.get('pass'))
print(json.dumps({
    'is_dag': g.get('is_dag'),
    'forward_order_sat': o.get('forward_order_sat'),
    'reverse_order_unsat': o.get('reverse_order_unsat'),
    'chirality_pass': c.get('pass'),
    'operator_sequence_ok': g.get('operator_sequence_ok'),
    'ok': ok,
}, sort_keys=True))
raise SystemExit(0 if ok else 1)
"""


def default_gates() -> list[dict[str, Any]]:
    return [
        {
            "id": "wiki_lproof_gate",
            "kind": "z3_cvc5_harness",
            "command": [
                "python3",
                "/Users/joshuaeisenhart/wiki/wizard/harness-consolidated/probes/harness_precommit.py",
            ],
            "expected_exit": 0,
            "evidence": "Z3/cvc5 harness precommit suite",
        },
        {
            "id": "wizard_receipt_gate",
            "kind": "pytest",
            "command": [
                "python3",
                "-m",
                "pytest",
                str(ROOT / "system_v5/tests/test_wizard_behavior_harness.py"),
                str(ROOT / "system_v5/tests/test_run_wizard_system.py"),
                str(ROOT / "system_v5/tests/test_package_wizard_candidate.py"),
                "-q",
            ],
            "expected_exit": 0,
            "evidence": "Wizard receipt, runner, and package tests",
        },
        {
            "id": "weyl_graph_proof_gate",
            "kind": "graph_z3_import_check",
            "command": ["python3", "-c", WEYL_GRAPH_CHECK],
            "expected_exit": 0,
            "evidence": "Weyl geometry graph/proof non-mutating import check",
            "claim_limit": "Does not prove full QIT graph alignment; operator_sequence_ok may remain false.",
        },
    ]


def _run_gate(gate: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    gate_id = str(gate["id"])
    stdout_path = out_dir / f"{gate_id}.stdout.txt"
    stderr_path = out_dir / f"{gate_id}.stderr.txt"
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(
        [str(part) for part in gate["command"]],
        cwd=str(ROOT),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    expected = int(gate.get("expected_exit", 0))
    return {
        "id": gate_id,
        "kind": gate.get("kind"),
        "ok": proc.returncode == expected,
        "returncode": proc.returncode,
        "expected_exit": expected,
        "evidence": gate.get("evidence"),
        "claim_limit": gate.get("claim_limit", ""),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "stdout_preview": proc.stdout[-2000:],
        "stderr_preview": proc.stderr[-2000:],
    }


def run_manifest(out_dir: Path = DEFAULT_OUT) -> dict[str, Any]:
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    gates = [_run_gate(gate, out_dir) for gate in default_gates()]
    result = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "ok": all(gate["ok"] for gate in gates),
        "out_dir": str(out_dir),
        "gates": gates,
    }
    (out_dir / "proof_validation.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    result = run_manifest(args.out_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
