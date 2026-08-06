from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        return 2
    source = Path(sys.argv[1])
    target = Path(sys.argv[2])
    value = json.loads(source.read_text(encoding="utf-8"))
    target.write_text(
        json.dumps(
            {"schema": "constraintbox.worker.echo.v1", "observation": value},
            sort_keys=True,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
