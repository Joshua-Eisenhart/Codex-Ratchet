#!/usr/bin/env python3
"""Keep the supplied patch's impossible self-hash defect reproducible."""
from __future__ import annotations

import hashlib
from pathlib import Path


PATCH = Path(__file__).resolve().parent.parent / "cbpatch"
MANIFEST = PATCH / "MANIFEST_SHA256.txt"


def main() -> int:
    entries = {}
    for line in MANIFEST.read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        entries[name] = digest
    actual = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    if entries.get("MANIFEST_SHA256.txt") == actual:
        raise AssertionError("expected the supplied self-hash to be non-reproducible")
    if entries.get("MANIFEST_SHA256.txt") != hashlib.sha256(b"").hexdigest():
        raise AssertionError("expected the supplied archive's empty-file self hash")
    print("REPRODUCED supplied manifest self-hash defect")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
