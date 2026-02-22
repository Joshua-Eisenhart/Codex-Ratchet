from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

THIS_DIR = Path(__file__).resolve().parent
TOOLS_DIR = THIS_DIR.parents[1] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from replay_runner import run_replay  # noqa: E402


def _canonical_json_bytes(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _load_vector(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"vector must be object: {path}")
    return data


def _evaluate(result: dict[str, Any], expected: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    ok = True

    if "expected_final_state_hash" in expected:
        want = str(expected["expected_final_state_hash"])
        have = str(result.get("final_state_hash", ""))
        if have != want:
            ok = False
            reasons.append(f"final_state_hash mismatch: have={have} want={want}")

    if "expected_last_outcome" in expected:
        events = result.get("events", [])
        have = events[-1].get("outcome", "") if events else ""
        want = str(expected["expected_last_outcome"])
        if have != want:
            ok = False
            reasons.append(f"last_outcome mismatch: have={have} want={want}")

    for tag in expected.get("must_contain_tags", []):
        tags = [str(e.get("tag", "")) for e in result.get("events", [])]
        if str(tag) not in tags:
            ok = False
            reasons.append(f"missing expected tag: {tag}")

    return ok, reasons


def run_harness(vectors_dir: Path, output_path: Path) -> dict[str, Any]:
    vector_files = sorted(vectors_dir.glob("*.json"))
    cases: list[dict[str, Any]] = []

    for vector_file in vector_files:
        vector = _load_vector(vector_file)
        test_id = str(vector.get("test_id", vector_file.stem))
        zip_sequence = [Path(p).expanduser().resolve() for p in vector.get("zip_sequence", [])]
        initial_hex = str(vector.get("initial_state_hex", ""))
        compiler_version = str(vector.get("compiler_version", "A0_COMPILER_v1"))
        expected = vector.get("expected", {})

        if not zip_sequence:
            cases.append(
                {
                    "test_id": test_id,
                    "status": "FAIL",
                    "reasons": ["zip_sequence is empty"],
                    "source_vector": str(vector_file),
                }
            )
            continue

        replay = run_replay(zip_sequence, bytes.fromhex(initial_hex) if initial_hex else b"", compiler_version)
        passed, reasons = _evaluate(replay, expected if isinstance(expected, dict) else {})

        cases.append(
            {
                "test_id": test_id,
                "status": "PASS" if passed else "FAIL",
                "reasons": reasons,
                "source_vector": str(vector_file),
                "final_state_hash": replay.get("final_state_hash", ""),
                "decision_trace_hash": replay.get("decision_trace_hash", ""),
                "events_count": len(replay.get("events", [])),
            }
        )

    total = len(cases)
    passed = sum(1 for c in cases if c["status"] == "PASS")
    report = {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "status": "PASS" if total > 0 and passed == total else ("NO_VECTORS" if total == 0 else "FAIL"),
        "cases": cases,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(_canonical_json_bytes(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Semantic ratchet stress harness runner")
    parser.add_argument(
        "--vectors-dir",
        default=str(THIS_DIR / "test_vectors"),
        help="Directory containing vector JSON files",
    )
    parser.add_argument(
        "--out",
        default=str(THIS_DIR / "replay_logs" / "harness_report.json"),
        help="Output report path",
    )
    args = parser.parse_args()

    report = run_harness(Path(args.vectors_dir), Path(args.out))
    print(Path(args.out).resolve())
    print(f"status={report['status']} total={report['total']} passed={report['passed']} failed={report['failed']}")


if __name__ == "__main__":
    main()
