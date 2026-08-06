#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
EXTERNAL_ROOT = REPO_ROOT / "external_sim_estate" / "legacy_estate_v2"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock(name: str) -> tuple[str, str]:
    path = ROOT / "requirements" / "locks" / name
    return path.relative_to(ROOT).as_posix(), digest(path)


def main() -> None:
    controller = ROOT / "src" / "constraintbox" / "estate.py"
    worker = EXTERNAL_ROOT / "workers" / "capability_worker.py"
    blocker = EXTERNAL_ROOT / "workers" / "import_blocker.py"
    poisoner = EXTERNAL_ROOT / "workers" / "operation_poisoner.py"
    s1_lock, s1_sha = lock("e0-py312-linux.lock")
    s2_lock, s2_sha = lock("e1-py312-linux.lock")
    s3_lock, s3_sha = lock("e2-py312-linux.lock")
    body = {
        "schema": "constraintbox.sim-estate.v2",
        "status": "PROPOSED",
        "promotion_allowed": False,
        "controller_sha256": digest(controller),
        "worker_sha256": digest(worker),
        "import_blocker_sha256": digest(blocker),
        "operation_poisoner_sha256": digest(poisoner),
        "tier_note": (
            "S1-S4 are sim-engine installation tiers. They are not "
            "ConstraintBox authority levels or manifold layers."
        ),
        "tiers": [
            {
                "tier_id": "S1",
                "name": "claim-control simulation instruments",
                "boot_budget_seconds": 12,
                "tested_lock": s1_lock,
                "tested_lock_sha256": s1_sha,
                "capabilities": [
                    {"id": "stdlib_finite", "required": True, "locked_version": "builtin"},
                    {"id": "numpy_density", "required": True, "locked_version": "2.5.1"},
                    {"id": "scipy_channel", "required": True, "locked_version": "1.18.0"},
                    {"id": "z3_finite", "required": True, "locked_version": "5.0.0.0"},
                    {"id": "cvc5_finite", "required": False, "locked_version": "1.3.4"},
                    {
                        "id": "tla_controller",
                        "required": False,
                        "locked_version": "1.7.4",
                        "artifact_sha1": "bee4a54f3ee3d4afc347c3240ec2d9e93b075104",
                    },
                ],
            },
            {
                "tier_id": "S2",
                "name": "local manifold and engine workhorses",
                "boot_budget_seconds": 45,
                "tested_lock": s2_lock,
                "tested_lock_sha256": s2_sha,
                "capabilities": [
                    {"id": "jax_density", "required": True, "locked_version": "0.11.0"},
                    {"id": "diffrax_flow", "required": True, "locked_version": "0.7.2"},
                    {"id": "quimb_tensor", "required": True, "locked_version": "1.14.0"},
                    {"id": "cotengra_path", "required": True, "locked_version": "0.8.2"},
                    {"id": "julia_density", "required": False, "locked_version": None},
                ],
            },
            {
                "tier_id": "S3",
                "name": "IGT FEP and scientific-field satellites",
                "boot_budget_seconds": 60,
                "tested_lock": s3_lock,
                "tested_lock_sha256": s3_sha,
                "capabilities": [
                    {"id": "pysindy_law", "required": True, "locked_version": "2.1.0"},
                    {"id": "pydmd_rate", "required": True, "locked_version": "2025.8.1"},
                    {"id": "pymdp_fep", "required": True, "locked_version": "1.0.3"},
                    {"id": "pykoopman_rate", "required": False, "locked_version": None},
                    {"id": "torch_density", "required": False, "locked_version": None},
                    {"id": "dimod_anneal", "required": False, "locked_version": None},
                ],
            },
            {
                "tier_id": "S4",
                "name": "cloud GPU acceleration and parity",
                "boot_budget_seconds": 90,
                "required_capability_sets": [
                    ["nvidia_device", "jax_cuda_parity"],
                    ["nvidia_device", "torch_cuda_parity"],
                ],
                "capabilities": [
                    {"id": "nvidia_device", "required": False, "locked_version": None},
                    {"id": "jax_cuda_parity", "required": False, "locked_version": "0.11.0"},
                    {"id": "torch_cuda_parity", "required": False, "locked_version": None},
                    {"id": "cuquantum_tensor", "required": False, "locked_version": None},
                    {"id": "reactant_julia_gpu", "required": False, "locked_version": None},
                ],
            },
        ],
    }
    target = EXTERNAL_ROOT / "sim_estate_v2.json"
    target.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
