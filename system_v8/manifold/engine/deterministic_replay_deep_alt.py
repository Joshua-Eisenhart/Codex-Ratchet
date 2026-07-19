#!/usr/bin/env python3
"""Double in-process replay for the redundant deep alt lane."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from chirality_layer_alt import run as run_chirality
from common import digest, write_json
from connection_layer_alt import run as run_connection
from history_layer_alt import run as run_history
from persistence_layer_alt import run as run_persistence
from verify_deep_alt import run as run_verify
from whole_manifold_v2_alt import run as run_whole


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def one_replay(source_path: Path):
    root_results = source_path.parent
    source = load_json(source_path)
    base = load_json(root_results / "base_mss.json")
    nesting = load_json(root_results / "nesting.json")
    prior_whole = load_json(root_results / "whole_manifold.json")
    connection = run_connection(source, prior_whole)
    history = run_history(source, connection)
    persistence = run_persistence(source, history)
    chirality = run_chirality(source, persistence)
    whole = run_whole(source, base, nesting, prior_whole, connection, history, persistence, chirality)
    verification = run_verify(source, connection, history, persistence, chirality, whole)
    return {
        "connection": connection,
        "history": history,
        "persistence": persistence,
        "chirality": chirality,
        "whole": whole,
        "verification": verification,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    first = one_replay(args.source)
    second = one_replay(args.source)
    archived_paths = {
        "connection": args.prior / "connection_alt.json",
        "history": args.prior / "history_alt.json",
        "persistence": args.prior / "persistence_alt.json",
        "chirality": args.prior / "chirality_alt.json",
        "whole": args.prior / "whole_manifold_v2_alt.json",
        "verification": args.prior / "verification_alt.json",
    }
    rows = {}
    checks = {}
    for name, path in archived_paths.items():
        archived = load_json(path)
        rows[name] = {
            "archived_result_digest": archived["result_digest"],
            "first_result_digest": first[name]["result_digest"],
            "second_result_digest": second[name]["result_digest"],
            "archived_canonical_digest": digest(archived),
            "first_canonical_digest": digest(first[name]),
            "second_canonical_digest": digest(second[name]),
        }
        checks[f"{name}_result_digest_stable"] = (
            archived["result_digest"] == first[name]["result_digest"] == second[name]["result_digest"]
        )
        checks[f"{name}_byte_semantics_stable"] = (
            digest(archived) == digest(first[name]) == digest(second[name])
        )
    checks["first_verification_passes"] = first["verification"]["all_pass"] is True
    checks["second_verification_passes"] = second["verification"]["all_pass"] is True
    result = {
        "schema": "ratchet.pack183.deep.deterministic-replay-alt.v1",
        "replays": rows,
        "checks": checks,
        "all_pass": all(checks.values()),
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "double in-process replay of redundant deep alt receipts only",
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
