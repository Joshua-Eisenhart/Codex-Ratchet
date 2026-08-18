#!/usr/bin/env python3
"""Run constraint_path_mass.v1 and write a durable receipt."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


BOX = Path(__file__).resolve().parents[2]
MERGED_SRC = BOX / "integrated_system" / "runtime" / "controller_src"
SRC = MERGED_SRC if MERGED_SRC.is_dir() else BOX / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from constraintbox.constraint_path_mass import (
    ConstraintPathMassRequest,
    PathMassError,
    default_reference_fixture_path,
    replay_receipt,
    write_receipt,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="constraint_path_mass.v1")
    parser.add_argument(
        "--out",
        type=Path,
        default=BOX / "receipts" / "constraint_path_mass" / "v1" / "result.json",
    )
    parser.add_argument(
        "--jax-python",
        type=Path,
        default=Path(os.environ["CB_JAX_PYTHON"])
        if "CB_JAX_PYTHON" in os.environ
        else None,
        help="explicit external interpreter for the optional JAX crossing",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        default=None,
        help="contained Mini-Lev reference-policy fixture",
    )
    parser.add_argument(
        "--require-jax",
        action="store_true",
        help="HOLD unless the declared external JAX crossing passes",
    )
    parser.add_argument(
        "--replay",
        type=Path,
        default=None,
        help="re-run a stored receipt and compare the exact bounded result",
    )
    args = parser.parse_args()
    try:
        if args.replay is not None:
            result = replay_receipt(
                args.replay,
                jax_interpreter=args.jax_python,
                fixture_path=args.fixture,
            )
            print(json.dumps(result, sort_keys=True))
            return 0 if result["status"] == "PASS" else 2
        request = ConstraintPathMassRequest(
            jax_interpreter=args.jax_python,
            fixture_path=args.fixture or default_reference_fixture_path(),
            require_jax=args.require_jax,
        )
        receipt = write_receipt(args.out, request)
    except PathMassError as exc:
        print(json.dumps({"status": "REFUSE", "reason": str(exc)}, sort_keys=True))
        return 3
    print(
        json.dumps(
            {
                "status": receipt["status"],
                "receipt_sha256": receipt["receipt_sha256"],
                "out": str(args.out),
                "n_paths": receipt["generator"]["n_paths"],
                "class_count": receipt["baseline"]["class_count"],
                "disposition": receipt["disposition"],
                "smt_real": receipt["smt"]["real_memory"]["z3"],
                "smt_erased": receipt["smt"]["erased_memory"]["z3"],
                "jax": receipt["jax_crossing"],
            },
            sort_keys=True,
        )
    )
    return 0 if receipt["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
