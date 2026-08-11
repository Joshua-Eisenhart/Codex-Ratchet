from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from constraintbox.intake import canonical_json
from constraintbox.ledger import HashChainLedger


class StrictReceiptConsumerChainTests(unittest.TestCase):
    def _case(self, module: str, tamper: str | None = None) -> tuple[int, dict, str]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "artifacts"
            root.mkdir()
            (root / "evidence").mkdir()
            artifact = root / "evidence" / "evidence.txt"
            artifact.write_text("controlled evidence\n", encoding="utf-8")
            ledger_path = root / "flow.jsonl"
            ledger = HashChainLedger(ledger_path)
            ledger.append({"terminal": "ELIGIBLE", "artifact": "evidence.txt"})
            ledger.append({"terminal": "RELEASED", "artifact": "evidence.txt"})
            if tamper == "chain":
                rows = ledger_path.read_text(encoding="utf-8").splitlines()
                row = json.loads(rows[0])
                row["record"]["terminal"] = "BLOCKED"
                rows[0] = json.dumps(row, sort_keys=True, separators=(",", ":"))
                ledger_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
            elif tamper == "duplicate":
                rows = ledger_path.read_text(encoding="utf-8").splitlines()
                ledger_path.write_text("\n".join([rows[0], rows[0]]) + "\n", encoding="utf-8")
            receipt = {
                "schema": "strict-chain-control.v1",
                "artifacts": [{"path": "evidence/evidence.txt", "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest()}],
                "ledger": {
                    "path": str(ledger_path),
                    "head_path": str(ledger.head_path),
                    "retained_head_sha256": ledger.head_path.read_text(encoding="ascii").strip(),
                },
            }
            receipt_path = root / "RECEIPT.json"
            receipt_path.write_bytes(canonical_json(receipt) + b"\n")
            output = Path(directory) / "result.json"
            command = [sys.executable, "-m", f"constraintbox.{module}"]
            if module.endswith("_v2"):
                command += ["--artifact-root", str(root), "--receipt", str(receipt_path)]
            else:
                command += ["--run-root", str(root), "--receipt", str(receipt_path), "--strict-cleanliness"]
            command += ["--output", str(output)]
            if module.endswith("_v2"):
                command += ["--expected-receipt-sha256", hashlib.sha256(receipt_path.read_bytes()).hexdigest()]
            completed = subprocess.run(command, capture_output=True, text=True, check=False)
            return completed.returncode, json.loads(output.read_text(encoding="utf-8")), completed.stdout + completed.stderr

    def test_v1_positive_and_chain_negative_specific_reason(self) -> None:
        code, result, output = self._case("strict_receipt_consumer")
        self.assertEqual(code, 0, output)
        self.assertTrue(result["passed"])
        code, result, output = self._case("strict_receipt_consumer", "chain")
        self.assertEqual(code, 1, output)
        self.assertTrue(any(item.startswith("invalid-ledger-chain:") for item in result["defects"]))

    def test_v2_positive_and_duplicate_chain_negative_specific_reason(self) -> None:
        code, result, output = self._case("strict_receipt_consumer_v2")
        self.assertEqual(code, 0, output)
        self.assertTrue(result["integrity_pass"])
        code, result, output = self._case("strict_receipt_consumer_v2", "duplicate")
        self.assertEqual(code, 1, output)
        self.assertTrue(any(item.startswith("invalid-ledger-chain:") for item in result["defects"]))


if __name__ == "__main__":
    unittest.main()
