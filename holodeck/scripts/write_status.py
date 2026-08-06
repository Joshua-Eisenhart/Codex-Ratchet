#!/usr/bin/env python3
"""Write the independent Holodeck tool/source visibility snapshot."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from holodeck_world.doctor import report


PRODUCT_ROOT = Path(__file__).resolve().parents[1]


def markdown(body: dict[str, object]) -> str:
    rows = body["tool_rows"]
    sources = body["candidate_sources"]
    assert isinstance(rows, list)
    assert isinstance(sources, list)
    lines = [
        "# Holodeck live development status",
        "",
        f"Generated: `{body['generated_at']}`",
        "",
        "Installed tooling, legacy source discovery, and Holodeck integration are separate facts.",
        "",
        "| Tool | Visible | Version | Declared level | Role |",
        "|---|---|---:|---|---|",
    ]
    for row in rows:
        assert isinstance(row, dict)
        lines.append(f"| `{row['id']}` | {row['live_import_visible']} | `{row['live_version']}` | {row['declared_integration_level']} | {row['role']} |")
    lines.extend(["", "## Candidate sources", "", "| Source | Exists | Status | Capability |", "|---|---|---|---|"])
    for row in sources:
        assert isinstance(row, dict)
        lines.append(f"| `{row['path']}` | {row['exists']} | {row['status']} | {row['capability']} |")
    lines.extend(
        [
            "",
            f"QIT bridge: `{body['qit_bridge_state']}`",
            "",
            "No candidate source is promoted to an integrated Holodeck engine by this snapshot.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=PRODUCT_ROOT / "status")
    args = parser.parse_args()
    body = report()
    body["generated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    target = args.output_dir.resolve()
    target.mkdir(parents=True, exist_ok=True)
    (target / "LIVE_DEVELOPMENT_INDEX.json").write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (target / "LIVE_DEVELOPMENT_INDEX.md").write_text(markdown(body), encoding="utf-8")
    print(target / "LIVE_DEVELOPMENT_INDEX.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
