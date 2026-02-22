import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

#!/usr/bin/env python3

def main():
    # Minimal determinism check: finite arithmetic over small integers.
    total = 0
    for i in range(10):
        total += i
    if total != 45:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
