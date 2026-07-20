#!/usr/bin/env python3
"""Build a deterministic integrity manifest for this execution pack."""

from __future__ import annotations

import hashlib
import json
import stat
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXCLUDED = {"MANIFEST.json", "SHA256SUMS"}


def main() -> int:
    files = []
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT).as_posix()
        if path.is_dir() or relative in EXCLUDED or "__pycache__" in path.parts:
            continue
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
            raise ValueError(f"manifest refuses nonregular payload: {relative}")
        raw = path.read_bytes()
        files.append(
            {
                "path": relative,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    manifest = {
        "schema_version": "ratchet.pack-manifest/0.1",
        "pack_id": ROOT.name,
        "file_count": len(files),
        "files": files,
    }
    (ROOT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (ROOT / "SHA256SUMS").write_text(
        "".join(f"{row['sha256']}  {row['path']}\n" for row in files),
        encoding="utf-8",
    )
    print(f"PASS manifest built for {len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

