"""Timeouts are absence of control evidence, never successful controls."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import constraintbox.estate as estate_module
from constraintbox.estate import CapabilityState, EstateRunner


PACK_ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_ROOT = PACK_ROOT.parent / "external_sim_estate" / "legacy_estate_v2"
WORKERS = EXTERNAL_ROOT / "workers"
FIXTURE = EXTERNAL_ROOT / "fixtures" / "manifold_fixture_v1.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


HANGING_WORKER = '''\
import json, math, sys, time

if any(type(finder).__name__ == "BlockedImport" for finder in sys.meta_path):
    time.sleep(10)

import numpy

try:
    numpy.linalg.eigvalsh([[1.0, 0.0], [0.0, 1.0]])
except Exception:
    time.sleep(10)

fixture = json.loads(open(sys.argv[2]).read())
rho = fixture["rho"]
a, b = rho[0]
c, d = rho[1]
tr = a + d
gap = math.sqrt(max(0.0, tr * tr - 4.0 * (a * d - b * c)))
eigs = sorted(((tr - gap) / 2.0, (tr + gap) / 2.0))
dephased = sorted([a, d])


def entropy(items):
    return -sum(v * math.log2(v) for v in items if v > 1e-15)


rank = sum(v > 1e-12 for v in eigs)
print(json.dumps({
    "schema": "constraintbox.capability-witness.v1",
    "capability_id": "numpy_density",
    "version": numpy.__version__,
    "dispatch": ["numpy.asarray", "numpy.linalg.eigvalsh", "numpy.trace"],
    "runtime": {"dtype": "float64"},
    "observed": {
        "trace": tr,
        "eigenvalues": eigs,
        "rank": rank,
        "hartley_bits": math.log2(rank),
        "von_neumann_bits": entropy(eigs),
        "dephased_entropy_bits": entropy(dephased),
    },
}, sort_keys=True, separators=(",", ":")))
'''

TIMED_OUT_SOLVER_WORKER = '''\
import importlib.metadata
import json
import sys
import time

import z3

fixture = json.loads(open(sys.argv[2]).read())
if (
    fixture["rho"][0][1] == 0.125
    and len(fixture["finite_histories"]) == 3
):
    time.sleep(10)

x, y = z3.Ints("x y")
sat_solver = z3.Solver()
sat_solver.add(x >= 0, x <= 1, y >= 0, y <= 1, x != y)
sat_status = sat_solver.check()
model = sat_solver.model()
unsat_solver = z3.Solver()
unsat_solver.add(x == y, x != y)
unsat_status = unsat_solver.check()
print(json.dumps({
    "schema": "constraintbox.capability-witness.v1",
    "capability_id": "z3_finite",
    "version": importlib.metadata.version("z3-solver"),
    "dispatch": ["z3.Solver.add", "z3.Solver.check", "z3.Solver.model"],
    "runtime": {},
    "observed": {
        "sat": str(sat_status),
        "unsat": str(unsat_status),
        "witness": {"x": model[x].as_long(), "y": model[y].as_long()},
    },
}, sort_keys=True, separators=(",", ":")))
'''


class EstateTimeoutTests(unittest.TestCase):
    def test_real_exit_124_is_not_a_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            worker = Path(temp) / "exit_124.py"
            worker.write_text("raise SystemExit(124)\n", encoding="utf-8")
            runner = EstateRunner(
                PACK_ROOT,
                EXTERNAL_ROOT / "sim_estate_v2.json",
                FIXTURE,
            )
            runner.worker = worker
            code, _stdout, _stderr, _elapsed, timed_out = runner._run_worker(
                "numpy_density", FIXTURE, 1
            )

        self.assertEqual(code, 124)
        self.assertFalse(timed_out)

    def test_timed_out_controls_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pack = root / "pack"
            workers = pack / "workers" / "estate"
            workers.mkdir(parents=True)
            for name in ("import_blocker.py", "operation_poisoner.py"):
                shutil.copy(WORKERS / name, workers / name)
            (workers / "capability_worker.py").write_text(
                HANGING_WORKER, encoding="utf-8"
            )
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema": "constraintbox.sim-estate.v1",
                        "status": "PROPOSED",
                        "promotion_allowed": False,
                        "python": (
                            f"{sys.version_info.major}.{sys.version_info.minor}"
                        ),
                        "controller_sha256": digest(Path(estate_module.__file__)),
                        "worker_sha256": digest(
                            workers / "capability_worker.py"
                        ),
                        "import_blocker_sha256": digest(
                            workers / "import_blocker.py"
                        ),
                        "tiers": [
                            {
                                "tier_id": "S1",
                                "name": "timeout-control",
                                "boot_budget_seconds": 1,
                                "capabilities": [
                                    {
                                        "id": "numpy_density",
                                        "required": True,
                                        "locked_version": None,
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            runner = EstateRunner(pack, manifest, FIXTURE)
            row = runner.run_tier("S1", "acceptance").capabilities[0]

        self.assertTrue(row.controls["positive"])
        self.assertTrue(row.controls["mutation"])
        self.assertTrue(row.controls["replay"])
        self.assertTrue(row.controls["dispatch"])
        self.assertFalse(row.controls["severance"])
        self.assertFalse(row.controls["operation"])
        self.assertEqual(
            row.evidence["controls_timed_out"], ["operation", "severance"]
        )
        self.assertNotIn("operation_never_called", row.evidence)
        self.assertIs(row.state, CapabilityState.FAILED)
        self.assertEqual(row.reason, "one_or_more_controls_failed")

    def test_timed_out_solver_mutation_is_measured_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pack = root / "pack"
            workers = pack / "workers" / "estate"
            workers.mkdir(parents=True)
            for name in ("import_blocker.py", "operation_poisoner.py"):
                shutil.copy(WORKERS / name, workers / name)
            (workers / "capability_worker.py").write_text(
                TIMED_OUT_SOLVER_WORKER, encoding="utf-8"
            )
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema": "constraintbox.sim-estate.v1",
                        "status": "PROPOSED",
                        "promotion_allowed": False,
                        "python": (
                            f"{sys.version_info.major}.{sys.version_info.minor}"
                        ),
                        "controller_sha256": digest(Path(estate_module.__file__)),
                        "worker_sha256": digest(
                            workers / "capability_worker.py"
                        ),
                        "import_blocker_sha256": digest(
                            workers / "import_blocker.py"
                        ),
                        "tiers": [
                            {
                                "tier_id": "S1",
                                "name": "solver-timeout-control",
                                "boot_budget_seconds": 1,
                                "capabilities": [
                                    {
                                        "id": "z3_finite",
                                        "required": True,
                                        "locked_version": None,
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            runner = EstateRunner(pack, manifest, FIXTURE)
            row = runner.run_tier("S1", "acceptance").capabilities[0]

        self.assertIn("mutation", row.controls)
        self.assertFalse(row.controls["mutation"])
        self.assertEqual(row.evidence["controls_timed_out"], ["mutation"])
        self.assertNotIn(
            "mutation", row.evidence.get("controls_not_measured", [])
        )
        self.assertIs(row.state, CapabilityState.FAILED)
        self.assertEqual(row.reason, "one_or_more_controls_failed")


if __name__ == "__main__":
    unittest.main()
