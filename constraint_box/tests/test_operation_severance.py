"""The operation control must catch a worker that imports but never computes.

Import severance proves only that a module was reachable. A worker that does
`import numpy`, touches it so the import cannot be optimised away, and then
computes the right answer with stdlib `math` passes every other control:

    positive  - the numbers are correct
    mutation  - it reads the fixture honestly, so a changed fixture changes them
    replay    - it is deterministic
    severance - it dies when numpy is blocked, because it really does import it

Only poisoning the claimed operation separates it from a genuine worker.  The
control passes only for the broker's exact deliberate-severance status and
signal.  Survival, a generic crash, or a poison-aware early exit all fail.

This is bounded evidence for source-pinned adapters.  A public signal inside a
shared hostile process is not a containment boundary.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
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


# Emits a byte-valid numpy_density witness with the correct observed values,
# computed entirely with stdlib math. numpy is imported and touched purely so
# that import severance has something to sever. np.linalg.eigvalsh is never
# called.
FAKE_WORKER = '''\
import json, math, sys

import numpy
_ = numpy.__version__

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

INSPECTING_WORKER = '''\
import json, math, sys

import numpy
_ = numpy.__version__
if not hasattr(numpy.linalg.eigvalsh, "__wrapped__"):
    sys.exit(3)

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

GENERIC_FAILING_WORKER = INSPECTING_WORKER.replace(
    "sys.exit(3)",
    'raise RuntimeError("poison-aware generic failure")',
)


class OperationSeveranceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _manifest(self, pack_root: Path, path: Path) -> Path:
        direct_workers = pack_root / "workers"
        workers = (
            direct_workers
            if (direct_workers / "capability_worker.py").is_file()
            else direct_workers / "estate"
        )
        body = {
            "schema": "constraintbox.sim-estate.v2",
            "status": "PROPOSED",
            "promotion_allowed": False,
            "python": f"{sys.version_info.major}.{sys.version_info.minor}",
            "controller_sha256": digest(Path(estate_module.__file__)),
            "worker_sha256": digest(workers / "capability_worker.py"),
            "import_blocker_sha256": digest(workers / "import_blocker.py"),
            "operation_poisoner_sha256": digest(
                workers / "operation_poisoner.py"
            ),
            "tiers": [
                {
                    "tier_id": "S1",
                    "name": "operation-control",
                    "boot_budget_seconds": 60,
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
        path.write_text(json.dumps(body), encoding="utf-8")
        return path

    def _fake_pack(self) -> Path:
        """A pack root whose worker is the import-only fake."""
        pack = self.root / "fakepack"
        (pack / "workers" / "estate").mkdir(parents=True)
        for name in ("import_blocker.py", "operation_poisoner.py"):
            shutil.copy(WORKERS / name, pack / "workers" / "estate" / name)
        (pack / "workers" / "estate" / "capability_worker.py").write_text(
            FAKE_WORKER, encoding="utf-8"
        )
        return pack

    def _inspecting_pack(self) -> Path:
        pack = self.root / "inspectingpack"
        (pack / "workers" / "estate").mkdir(parents=True)
        for name in ("import_blocker.py", "operation_poisoner.py"):
            shutil.copy(WORKERS / name, pack / "workers" / "estate" / name)
        (pack / "workers" / "estate" / "capability_worker.py").write_text(
            INSPECTING_WORKER, encoding="utf-8"
        )
        return pack

    def _generic_failing_pack(self) -> Path:
        pack = self.root / "genericfailingpack"
        (pack / "workers" / "estate").mkdir(parents=True)
        for name in ("import_blocker.py", "operation_poisoner.py"):
            shutil.copy(WORKERS / name, pack / "workers" / "estate" / name)
        (pack / "workers" / "estate" / "capability_worker.py").write_text(
            GENERIC_FAILING_WORKER, encoding="utf-8"
        )
        return pack

    def test_poison_preserves_common_callable_metadata(self) -> None:
        script = r'''
import inspect
import json
import numpy.linalg
import operation_poisoner

original = numpy.linalg.eigvalsh
before = {
    "name": original.__name__,
    "qualname": original.__qualname__,
    "doc": original.__doc__,
    "module": original.__module__,
    "signature": str(inspect.signature(original)),
}
operation_poisoner.poison("numpy.linalg", "eigvalsh")
poisoned = numpy.linalg.eigvalsh
after = {
    "name": poisoned.__name__,
    "qualname": poisoned.__qualname__,
    "doc": poisoned.__doc__,
    "module": poisoned.__module__,
    "signature": str(inspect.signature(poisoned)),
}
called = False
try:
    poisoned([[1.0, 0.0], [0.0, 1.0]])
except operation_poisoner.OperationSevered:
    called = True
print(json.dumps({
    "before": before,
    "after": after,
    "wrapped_absent": not hasattr(poisoned, "__wrapped__"),
    "call_raised_operation_severed": called,
}, sort_keys=True))
'''
        proc = subprocess.run(
            [sys.executable, "-c", script],
            cwd=WORKERS,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["after"], result["before"])
        self.assertTrue(result["wrapped_absent"])
        self.assertTrue(result["call_raised_operation_severed"])

    def test_genuine_worker_passes_the_operation_control(self) -> None:
        manifest = self._manifest(EXTERNAL_ROOT, self.root / "real.json")
        runner = EstateRunner(EXTERNAL_ROOT, manifest, FIXTURE)
        capability = runner.run_tier("S1", "acceptance").capabilities[0]
        self.assertIn(
            "operation",
            capability.controls,
            "the operation control did not run for numpy_density",
        )
        self.assertTrue(
            capability.controls["operation"],
            "a genuine worker must die when numpy.linalg.eigvalsh is severed",
        )
        self.assertEqual(
            capability.evidence.get("operation_severed"), "numpy.linalg.eigvalsh"
        )
        self.assertEqual(
            capability.evidence["operation_observed_exit_code"], 86
        )
        self.assertEqual(
            capability.evidence["operation_expected_signal_sha256"],
            capability.evidence["operation_observed_signal_sha256"],
        )
        self.assertTrue(
            capability.evidence["operation_poisoner_source_pinned"]
        )
        self.assertIn(
            "not arbitrary hostile-process containment",
            capability.evidence["operation_causality_ceiling"],
        )
        self.assertIs(capability.state, CapabilityState.READY)

    def test_v2_operation_control_requires_current_poisoner_pin(self) -> None:
        manifest = self._manifest(EXTERNAL_ROOT, self.root / "missing-pin.json")
        body = json.loads(manifest.read_text(encoding="utf-8"))
        del body["operation_poisoner_sha256"]
        manifest.write_text(json.dumps(body), encoding="utf-8")

        runner = EstateRunner(EXTERNAL_ROOT, manifest, FIXTURE)
        capability = runner.run_tier("S1", "acceptance").capabilities[0]

        self.assertIs(capability.state, CapabilityState.DRIFT)
        self.assertEqual(
            capability.reason, "worker_source_digest_mismatch"
        )
        self.assertIsNone(
            capability.evidence["expected_operation_poisoner_sha256"]
        )
        self.assertEqual(
            capability.evidence["observed_operation_poisoner_sha256"],
            digest(WORKERS / "operation_poisoner.py"),
        )

    def test_import_only_fake_is_caught(self) -> None:
        pack = self._fake_pack()
        manifest = self._manifest(pack, self.root / "fake.json")
        runner = EstateRunner(pack, manifest, FIXTURE)
        capability = runner.run_tier("S1", "acceptance").capabilities[0]

        # It clears everything an import-only fake can clear.
        self.assertTrue(capability.controls.get("positive"))
        self.assertTrue(capability.controls.get("severance"))

        # And is caught by the one control that asks whether the work happened.
        self.assertFalse(
            capability.controls.get("operation", True),
            "a worker that never calls the operation must fail the control",
        )
        self.assertTrue(capability.evidence.get("operation_never_called"))
        self.assertIs(capability.state, CapabilityState.FAILED)

    def test_metadata_inspecting_fake_is_caught(self) -> None:
        pack = self._inspecting_pack()
        manifest = self._manifest(pack, self.root / "inspecting.json")
        runner = EstateRunner(pack, manifest, FIXTURE)
        capability = runner.run_tier("S1", "acceptance").capabilities[0]

        self.assertFalse(capability.controls["operation"])
        self.assertEqual(
            capability.evidence["operation_observed_exit_code"], 3
        )
        self.assertEqual(
            capability.evidence["operation_severance_cause_unconfirmed"],
            "generic_or_worker_selected_failure",
        )
        self.assertNotIn("operation_severed", capability.evidence)
        self.assertIs(capability.state, CapabilityState.FAILED)

    def test_generic_failure_is_not_operation_evidence(self) -> None:
        pack = self._generic_failing_pack()
        manifest = self._manifest(pack, self.root / "generic-failure.json")
        runner = EstateRunner(pack, manifest, FIXTURE)
        capability = runner.run_tier("S1", "acceptance").capabilities[0]

        self.assertFalse(capability.controls["operation"])
        self.assertEqual(
            capability.evidence["operation_observed_exit_code"], 1
        )
        self.assertEqual(
            capability.evidence["operation_severance_cause_unconfirmed"],
            "generic_or_worker_selected_failure",
        )
        self.assertIn(
            "poison-aware generic failure",
            capability.evidence["operation_stderr"],
        )
        self.assertNotIn("operation_severed", capability.evidence)
        self.assertIs(capability.state, CapabilityState.FAILED)
