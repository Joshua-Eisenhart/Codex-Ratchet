#!/usr/bin/env python3
"""NumPy oracle/control leg for ratchet_replicator_run_v0."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import ratchet_replicator_core as core

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "classical"

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive oracle/control array checksum over finite token states; Python core carries the ratchet counters",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing shared ratchet loop, record window, novelty summary, motif detection, and result emission",
    },
}

TOOL_INTEGRATION_DEPTH = {"numpy": "supportive", "python_stdlib": "load_bearing"}

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def numpy_observables() -> dict[str, object]:
    cfg = core.load_spec()["run_config"]
    seed_states = np.asarray([(3 * i + 1) % int(cfg["state_modulus"]) for i in range(int(cfg["alphabet_size"]))], dtype=np.int64)
    return {
        "initial_state_checksum": int(np.sum(seed_states) % 1000003),
        "alphabet_size": int(seed_states.shape[0]),
        "state_modulus": int(cfg["state_modulus"]),
    }


def main() -> int:
    RESULTS.mkdir(exist_ok=True)
    payload = core.result_envelope(
        "numpy",
        {
            "source_path": core.rel(Path(__file__)),
            "source_sha256": core.climb.sha256_file(Path(__file__)),
            "packages_used": ["numpy", "python_stdlib"],
            "aligned_packages_load_bearing": ["python_stdlib"],
            "package_observables": {"numpy": numpy_observables()},
            "control_only_tools": ["numpy"],
            "TOOL_MANIFEST": TOOL_MANIFEST,
            "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        },
    )
    out = RESULTS / "ratchet_replicator_run_v0_numpy_results.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"result_path": str(out), "all_pass": payload["all_pass"], "replicator": payload["replicator_verdict"]["verdict"]}, indent=2))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

