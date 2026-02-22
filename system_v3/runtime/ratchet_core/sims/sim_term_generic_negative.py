import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

#!/usr/bin/env python3
import hashlib
import json
import os
import sys


def main() -> int:
    target_spec = os.environ.get("TARGET_SPEC", "")
    target_token = os.environ.get("TARGET_TOKEN", "")
    payload = {
        "sim": "sim_term_generic_negative",
        "target_spec": target_spec,
        "target_token": target_token,
        "mode": "NEGATIVE",
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    sys.stdout.write(digest + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
