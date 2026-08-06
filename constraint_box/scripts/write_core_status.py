#!/usr/bin/env python3
"""Write the ConstraintBox-local install and five-tool exercise snapshot."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from constraintbox.core_tools import doctor, exercise


PRODUCT_ROOT = Path(__file__).resolve().parents[1]


def build() -> dict[str, object]:
    return {
        "schema": "constraintbox.core-status.v9",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "doctor": doctor(),
        "exercise": exercise(),
        "scope": "constraintbox_internal_core_only",
        "excluded_runtimes": ["jax", "pytorch", "julia", "java", "tlc", "apalache", "pysindy"],
        "claim_ceiling": "five_tool_install_visibility_and_function_exercise_only",
        "promotion_allowed": False,
    }


def markdown(body: dict[str, object]) -> str:
    doctor_body = body["doctor"]
    exercise_body = body["exercise"]
    assert isinstance(doctor_body, dict)
    assert isinstance(exercise_body, dict)
    rows = doctor_body["rows"]
    assert isinstance(rows, list)
    lines = [
        "# ConstraintBox live core status",
        "",
        f"Generated: `{body['generated_at']}`",
        "",
        "This snapshot is local to ConstraintBox. It is not the external Sim Engines estate.",
        "",
        "| Tool | Installed version | Import visible | Exercised integration |",
        "|---|---:|---|---|",
    ]
    observations = exercise_body["observations"]
    assert isinstance(observations, dict)
    for row in rows:
        assert isinstance(row, dict)
        exercised = "yes" if row["id"] in observations else "no"
        lines.append(f"| `{row['id']}` | `{row['version']}` | {row['import_visible']} | {exercised} |")
    lines.extend(
        [
            "",
            f"Exercise observation SHA-256: `{exercise_body['observation_sha256']}`",
            "",
            "Excluded from the CB core: JAX, PyTorch, Julia, Java/TLC/Apalache, and PySINDy.",
            "",
            "Claim ceiling: installation visibility plus one bounded function exercise per core tool.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=PRODUCT_ROOT / "status")
    args = parser.parse_args()
    body = build()
    target = args.output_dir.resolve()
    target.mkdir(parents=True, exist_ok=True)
    (target / "LIVE_CORE_INDEX.json").write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (target / "LIVE_CORE_INDEX.md").write_text(markdown(body), encoding="utf-8")
    print(target / "LIVE_CORE_INDEX.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
