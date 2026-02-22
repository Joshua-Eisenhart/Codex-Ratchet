#!/usr/bin/env python3
import hashlib
import json
import os
import sys


def main() -> int:
    target_spec = os.environ.get("TARGET_SPEC", "")
    target_token = os.environ.get("TARGET_TOKEN", "")
    payload = {
        "sim": "sim_term_generic",
        "target_spec": target_spec,
        "target_token": target_token,
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    sys.stdout.write(digest + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
