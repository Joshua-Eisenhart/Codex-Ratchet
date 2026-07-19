#!/usr/bin/env python3
"""Replay the complete active Pack 183 mathematics twice in process."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from base_mss_engine import run as run_base
from common import digest, write_json
from nesting_ratchet import run as run_nesting
from source_packets import run as run_source
from verify_active_results import validate
from whole_feedback_ratchet import run as run_whole


def one_replay():
    source = run_source()
    base = run_base(source)
    nesting = run_nesting(source, base)
    whole = run_whole(source, base)
    checks = validate(source, base, nesting, whole)
    return source, base, nesting, whole, checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archived-source", type=Path, required=True)
    parser.add_argument("--archived-base", type=Path, required=True)
    parser.add_argument("--archived-nesting", type=Path, required=True)
    parser.add_argument("--archived-whole", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    first = one_replay()
    second = one_replay()
    names = ("source", "base", "nesting", "whole")
    archived_paths = (
        args.archived_source, args.archived_base, args.archived_nesting, args.archived_whole,
    )
    replay_rows = {}
    checks = {}
    for index, (name, path) in enumerate(zip(names, archived_paths)):
        archived = json.loads(path.read_text(encoding="utf-8"))
        first_result = first[index]
        second_result = second[index]
        replay_rows[name] = {
            "archived_result_digest": archived["result_digest"],
            "first_result_digest": first_result["result_digest"],
            "second_result_digest": second_result["result_digest"],
            "archived_canonical_digest": digest(archived),
            "first_canonical_digest": digest(first_result),
            "second_canonical_digest": digest(second_result),
        }
        checks[f"{name}_result_digest_stable"] = (
            archived["result_digest"] == first_result["result_digest"] == second_result["result_digest"]
        )
        checks[f"{name}_byte_semantics_stable"] = (
            digest(archived) == digest(first_result) == digest(second_result)
        )
    checks["first_semantic_validation"] = all(first[-1].values())
    checks["second_semantic_validation"] = all(second[-1].values())
    result = {
        "schema": "ratchet.pack183.deterministic-replay.v1",
        "replays": replay_rows,
        "checks": checks,
        "all_pass": all(checks.values()),
    }
    result["result_digest"] = digest(result)
    write_json(args.output, result)
    print(json.dumps({
        "all_pass": result["all_pass"],
        "checks": len(checks),
        "failed_checks": sorted(name for name, value in checks.items() if not value),
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
