import hashlib
import json
import unittest
from pathlib import Path

from constraintbox import estate


class EstateSourcePinsCurrentTest(unittest.TestCase):
    def test_estate_source_pins_are_present_and_current(self):
        box_root = Path(__file__).resolve().parents[1]
        manifest_path = (
            box_root.parent
            / "external_sim_estate"
            / "legacy_estate_v2"
            / "sim_estate_v2.json"
        )
        with manifest_path.open(encoding="utf-8") as stream:
            manifest = json.load(stream)
        controller_source = Path(estate.__file__).resolve()
        external_root = manifest_path.parent
        pin_sources = {
            "controller_sha256": controller_source,
            "import_blocker_sha256": (
                external_root / "workers" / "import_blocker.py"
            ),
            "worker_sha256": (
                external_root / "workers" / "capability_worker.py"
            ),
            "operation_poisoner_sha256": (
                external_root / "workers" / "operation_poisoner.py"
            ),
        }

        for pin, source_path in pin_sources.items():
            with self.subTest(pin=pin, source_path=source_path):
                self.assertIn(
                    pin,
                    manifest,
                    f"missing estate source pin {pin!r} for file {source_path}",
                )
                expected = manifest[pin]
                observed = hashlib.sha256(source_path.read_bytes()).hexdigest()
                self.assertEqual(
                    expected,
                    observed,
                    (
                        f"stale estate source pin {pin!r} for file {source_path}: "
                        f"expected {expected}, observed {observed}"
                    ),
                )
