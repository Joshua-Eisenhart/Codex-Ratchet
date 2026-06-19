#!/usr/bin/env python3
"""Write the fiber_augmented_cover_v0 scratch result."""

from __future__ import annotations

import json

import fiber_augmented_cover_v0_common as common


CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOOL_MANIFEST = {
    "z3": {
        "tried": True,
        "used": True,
        "reason": "row-local relation contradiction/erased-flip proof over computed cover signs",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "independent row-local relation contradiction/erased-flip proof over computed cover signs",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "deterministic quotient, sign-vector, and result hashes",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "deterministic result serialization for the scratch packet",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "hashlib": "supportive",
    "json": "supportive",
}


def main() -> int:
    common.write_result()
    print(json.dumps({"ok": True, "result_path": common.rel(common.RESULT_PATH)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
