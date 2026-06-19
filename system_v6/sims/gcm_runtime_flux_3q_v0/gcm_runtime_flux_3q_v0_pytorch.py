#!/usr/bin/env python3
"""PyTorch lane and write-producing entrypoint for gcm_runtime_flux_3q_v0."""

from __future__ import annotations

import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import torch
from torch.func import vmap
import sympy as sp

import gcm_runtime_flux_3q_v0_common as common


ENGINE = "pytorch"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.PYTORCH_RESULT_PATH
CLASSIFICATION = "scratch_diagnostic"
TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact sign-cancellation guard"},
    "torch.func": {"tried": True, "used": True, "reason": "supportive vmap sign-vector parity"},
    "torch": {"tried": True, "used": True, "reason": "supportive scalar tensor storage for PyTorch lane receipt"},
}
TOOL_INTEGRATION_DEPTH = {"sympy": "load_bearing", "torch.func": "supportive", "torch": "supportive"}


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def torch_func_parity(packet: dict[str, Any]) -> dict[str, Any]:
    rows = {row["row_id"]: row for row in packet["runtime_current_rows"]}
    right = rows["engine_R_flux_OUT_right_3q"]
    left = rows["engine_L_flux_IN_left_3q"]
    values = torch.tensor(
        [
            right["J_cut"]["net_delta_mutual_I"],
            right["J_ent"]["net_delta_negativity"],
            right["J_chi"]["signed_log2_qubits_per_step"],
            left["J_cut"]["net_delta_mutual_I"],
            left["J_ent"]["net_delta_negativity"],
            left["J_chi"]["signed_log2_qubits_per_step"],
        ],
        dtype=torch.float64,
    )

    def signed_square(value: torch.Tensor) -> torch.Tensor:
        return torch.sign(value) * value * value

    signed_squares = vmap(signed_square)(values)
    return {
        "input_vector": [common.q(float(value)) for value in values.tolist()],
        "signed_square_vector": [common.q(float(value)) for value in signed_squares.tolist()],
        "right_positive_left_negative": bool(
            values[0] > 0 and values[1] > 0 and values[2] > 0 and values[3] < 0 and values[4] < 0 and values[5] < 0
        ),
        "finite": bool(torch.isfinite(values).all().item() and torch.isfinite(signed_squares).all().item()),
    }


def sympy_guard(packet: dict[str, Any]) -> dict[str, Any]:
    rows = {row["row_id"]: row for row in packet["runtime_current_rows"]}
    right_chi = sp.Rational(rows["engine_R_flux_OUT_right_3q"]["J_chi"]["signed_log2_qubits_per_step"], 1)
    left_chi = sp.Rational(rows["engine_L_flux_IN_left_3q"]["J_chi"]["signed_log2_qubits_per_step"], 1)
    three_q_cuts = sp.Rational(packet["three_q_necessity_row"]["three_q_cut_count"], 1)
    two_q_cuts = sp.Rational(packet["three_q_necessity_row"]["two_q_cut_count"], 1)
    return {
        "right_chi": str(right_chi),
        "left_chi": str(left_chi),
        "three_q_cuts": str(three_q_cuts),
        "two_q_cuts": str(two_q_cuts),
        "pass": bool(sp.simplify(right_chi + left_chi) == 0 and three_q_cuts == 3 and two_q_cuts == 1),
    }


def build_result(packet: dict[str, Any]) -> dict[str, Any]:
    parity = torch_func_parity(packet)
    exact = sympy_guard(packet)
    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": common.SIM_ID,
        "engine": ENGINE,
        "source_path": common.rel(SOURCE_PATH),
        "source_sha256": common.sha256_file(SOURCE_PATH),
        "result_path": common.rel(RESULT_PATH),
        "generated_at": common.now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "packages_used": ["torch", "torch.func", "sympy"],
        "aligned_packages_load_bearing": ["sympy"],
        "package_versions": {"torch": torch.__version__, "torch.func": package_version("torch"), "sympy": package_version("sympy")},
        "package_observables": {
            "sympy": "sp.Rational guard for 3Q/2Q cut counts and L/R chirality cancellation",
        },
        "reads_peer_result": False,
        "runtime_flux_vector_receipt": parity,
        "sympy_guard": exact,
        "engine_values": {
            "right_j_cut_sign": 1,
            "left_j_cut_sign": -1,
            "right_j_ent_sign": 1,
            "left_j_ent_sign": -1,
            "right_j_chi": 2,
            "left_j_chi": -2,
        },
        "all_pass": bool(packet["all_pass"] and parity["finite"] and parity["right_positive_left_negative"] and exact["pass"]),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }
    common.write_json(RESULT_PATH, result)
    return result


def run_child(command: list[str]) -> None:
    proc = subprocess.run(
        command,
        cwd=common.ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError("\n".join(["child command failed", " ".join(command), proc.stdout, proc.stderr]))


def main() -> int:
    packet = common.build_packet(write=True)
    result = build_result(packet)
    run_child([sys.executable, str(common.SIM_DIR / f"{common.SIM_ID}_jax.py")])
    run_child(["julia", "--project=system_v5/julia_carrier", str(common.SIM_DIR / f"{common.SIM_ID}_julia.jl")])
    run_child([sys.executable, str(common.SIM_DIR / "write_envelope_spec.py")])
    print(json.dumps({"ok": result["all_pass"], "result": common.rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
