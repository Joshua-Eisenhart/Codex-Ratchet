#!/usr/bin/env python3
"""NumPy control lane for geo_s1_quaternion_model_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "geo_s1_quaternion_model_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_numpy_control.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_numpy_control_results.json"
PIN_SPEC = (
    "geo_s1_quaternion_model_v0|stage:1|model:unit_quaternion|"
    "dictionary:z1=a+bi,z2=c-di for q=a+bi+cj+dk|"
    "hopf_quaternion=q*i*qbar|R=[[0,0,-1],[0,1,0],[1,0,0]]|"
    "complex_hopf=(2Re(z1*conj(z2)),2Im(z1*conj(z2)),|z1|^2-|z2|^2)|"
    "seed_ledger=jax.random.PRNGKey[42017:q_n20000,42018:r_n20000];"
    "torch.Generator.manual_seed[57001:volume_mc_n80000_160000_320000];"
    "numpy.default_rng[777:control_n15000]|"
    "rerun=SIM_PY geo_s1_quaternion_model_v0_{jax,julia,pytorch,numpy_control,envelope}|"
    "classification=scratch_diagnostic"
)
R = np.array([[0.0, 0.0, -1.0], [0.0, 1.0, 0.0], [1.0, 0.0, 0.0]])


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def qmul(q: np.ndarray, r: np.ndarray) -> np.ndarray:
    a, b, c, d = np.moveaxis(q, -1, 0)
    e, f, g, h = np.moveaxis(r, -1, 0)
    return np.stack([a * e - b * f - c * g - d * h, a * f + b * e + c * h - d * g, a * g - b * h + c * e + d * f, a * h + b * g - c * f + d * e], axis=-1)


def qhopf(q: np.ndarray) -> np.ndarray:
    i_unit = np.broadcast_to(np.array([0.0, 1.0, 0.0, 0.0]), q.shape)
    return qmul(qmul(q, i_unit), q * np.array([1.0, -1.0, -1.0, -1.0]))[..., 1:4]


def q_to_z(q: np.ndarray) -> np.ndarray:
    return np.stack([q[..., 0] + 1j * q[..., 1], q[..., 2] - 1j * q[..., 3]], axis=-1)


def complex_hopf(z: np.ndarray) -> np.ndarray:
    z12 = z[..., 0] * np.conj(z[..., 1])
    return np.stack([2.0 * z12.real, 2.0 * z12.imag, np.abs(z[..., 0]) ** 2 - np.abs(z[..., 1]) ** 2], axis=-1)


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(777)
    q = rng.normal(size=(15000, 4))
    q = q / np.linalg.norm(q, axis=1, keepdims=True)
    hq = qhopf(q)
    hc = complex_hopf(q_to_z(q))
    after_r = np.max(np.abs(hq @ R.T - hc))
    skip_r = np.max(np.abs(hq - hc))
    single_method_table = {"invariant": "synthetic_control", "methods": ["numpy_only"], "single_sourced": True, "admitted": False}
    payload = {
        "schema_version": "control_lane_result_v1",
        "sim_id": SIM_ID,
        "engine": "numpy_control",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "all_pass": bool(after_r < 1.0e-8 and skip_r > 0.1 and single_method_table["single_sourced"]),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "claim_path_tools": [],
        "controls": {
            "wrong_convention_skip_R": {"fired": bool(skip_r > 0.1), "measured_deviation": float(skip_r)},
            "single_method_control": {"fired": True, "table": single_method_table},
        },
        "shared_scalars": {"after_R_deviation": float(after_r), "skip_R_deviation": float(skip_r)},
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "engine": "numpy_control", "result_path": str(RESULT_PATH)}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
