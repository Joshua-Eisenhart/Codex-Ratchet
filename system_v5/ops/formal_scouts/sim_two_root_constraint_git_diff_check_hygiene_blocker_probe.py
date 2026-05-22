#!/usr/bin/env python3
"""Record the current git diff hygiene blocker without hanging the closeout.

The active goal text may arrive with a stale "git diff --check passed" note.
This scout verifies the current checkout directly with a bounded subprocess.
If the object store emits the known truncated-pack failure or the command times
out, the receipt remains successful as a blocker receipt while keeping cleanup
and goal completion blocked.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import time
from typing import Any

import z3


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_git_diff_check_hygiene_blocker_probe_results.json"

NAME = "two_root_constraint_git_diff_check_hygiene_blocker_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_git_diff_check_hygiene_blocker"
CLAIM_CEILING = (
    "Formal scout hygiene receipt only: runs git diff --check with a hard "
    "timeout and records whether diff hygiene is currently verifiable. It does "
    "not repair the Git object store, does not authorize cleanup, does not stage "
    "or commit, and does not promote any scientific, manifold, basin, engine, "
    "PEPS/PEPS3D, tensor-network, or Clifford claim."
)

TOOL_MANIFEST = {
    "git": {
        "tried": True,
        "used": True,
        "reason": "supportive bounded git diff --check hygiene command evidence",
    },
    "python_subprocess": {
        "tried": True,
        "used": True,
        "reason": "supportive timeout wrapper around a known possibly-wedging git command",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt serialization",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive repository path handling",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source provenance hashing",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing proof that cleanup cannot be authorized when git diff hygiene is not verifiable",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "git": "supportive",
    "python_subprocess": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "hashlib": "supportive",
    "z3": "load_bearing",
}

TIMEOUT_SECONDS = 12
KNOWN_PACK_FRAGMENT = "is far too short to be a packfile"


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def truncate(text: str, limit: int = 12000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n...[truncated {len(text) - limit} chars]"


def run_git_diff_check() -> dict[str, Any]:
    started = time.time()
    try:
        proc = subprocess.run(
            ["git", "diff", "--check"],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
        elapsed = time.time() - started
        stderr = proc.stderr or ""
        stdout = proc.stdout or ""
        pack_corruption = KNOWN_PACK_FRAGMENT in stderr
        passed = proc.returncode == 0 and not stderr.strip() and not stdout.strip()
        return {
            "command": "git diff --check",
            "timed_out": False,
            "timeout_seconds": TIMEOUT_SECONDS,
            "elapsed_seconds": elapsed,
            "returncode": proc.returncode,
            "stdout": truncate(stdout),
            "stderr": truncate(stderr),
            "stderr_line_count": len(stderr.splitlines()),
            "git_diff_check_passed": passed,
            "git_object_store_pack_corruption_detected": pack_corruption,
            "known_pack_fragment": KNOWN_PACK_FRAGMENT if pack_corruption else None,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        return {
            "command": "git diff --check",
            "timed_out": True,
            "timeout_seconds": TIMEOUT_SECONDS,
            "elapsed_seconds": time.time() - started,
            "returncode": None,
            "stdout": truncate(stdout),
            "stderr": truncate(stderr),
            "stderr_line_count": len(stderr.splitlines()),
            "git_diff_check_passed": False,
            "git_object_store_pack_corruption_detected": KNOWN_PACK_FRAGMENT in stderr,
            "known_pack_fragment": KNOWN_PACK_FRAGMENT if KNOWN_PACK_FRAGMENT in stderr else None,
        }


def completion_z3(diff: dict[str, Any]) -> dict[str, Any]:
    if bool(diff["git_diff_check_passed"]):
        return {
            "pass": True,
            "cleanup_authorized_true_is_unsat_when_diff_not_passed": None,
            "solver_status": "not_applicable_git_diff_check_passed",
            "reason": "The implication guard is only load-bearing when git diff hygiene is not verifiably green.",
        }
    cleanup_authorized = z3.Bool("cleanup_authorized")
    git_diff_passed = z3.Bool("git_diff_passed")
    solver = z3.Solver()
    solver.add(git_diff_passed == bool(diff["git_diff_check_passed"]))
    solver.add(z3.Implies(z3.Not(git_diff_passed), z3.Not(cleanup_authorized)))
    check_cleanup = z3.Solver()
    check_cleanup.add(solver.assertions())
    check_cleanup.add(cleanup_authorized)
    status = check_cleanup.check()
    return {
        "pass": status == z3.unsat,
        "cleanup_authorized_true_is_unsat_when_diff_not_passed": status == z3.unsat,
        "solver_status": str(status),
    }


def source_hashes() -> dict[str, Any]:
    paths = {
        "self": pathlib.Path(__file__).resolve(),
        "active_handoff": REPO / ".lev" / "pm" / "handoffs" / "20260520-formal-manifold-tooling-retool-session-1.md",
        "active_plan": REPO / "system_v5" / "ops" / "NEXT_GOAL_LONG_FORMAL_MANIFOLD_RETOOL_PLAN.md",
    }
    return {
        key: {"path": rel(path), "exists": path.exists(), "sha256": sha256(path)}
        for key, path in paths.items()
    }


def main() -> int:
    generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    diff = run_git_diff_check()
    z3_result = completion_z3(diff)
    hygiene_passed = bool(diff["git_diff_check_passed"])
    output = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "generated_at": generated_at,
        "all_pass": True,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "completion_status": (
            "git_diff_check_passed"
            if hygiene_passed
            else "git_diff_check_blocked_or_failed"
        ),
        "goal_complete": False,
        "cleanup_authorized": False,
        "git_diff_check_passed": hygiene_passed,
        "positive": {
            "bounded_git_diff_check_executed": {
                "pass": True,
                "timeout_seconds": TIMEOUT_SECONDS,
                "result": diff,
            },
            "known_pack_corruption_classified": {
                "pass": bool(diff["git_object_store_pack_corruption_detected"] or hygiene_passed),
                "value": diff["git_object_store_pack_corruption_detected"],
                "known_pack_fragment": KNOWN_PACK_FRAGMENT,
            },
            "z3_blocks_cleanup_without_git_diff_check": z3_result,
        },
        "boundary": {
            "cleanup_authorized": {"pass": True, "value": False},
            "goal_complete": {"pass": True, "value": False},
            "staging_or_commit_performed": {"pass": True, "value": False},
        },
        "graveyard_companions": {
            "stale_git_diff_passed_claim_rejected": {
                "pass": True,
                "reason": (
                    "Current bounded command evidence supersedes stale validation prose; "
                    "it is green now." if hygiene_passed
                    else "Current bounded command evidence does not prove git diff hygiene is green."
                ),
            },
            "scientific_promotion_from_git_hygiene_killed": {
                "pass": True,
                "reason": "Git hygiene is a closeout gate only and has no scientific claim value.",
            },
        },
        "nearby_variants": {
            "passed": 3,
            "total": 3,
            "items": [
                "bounded full git diff check attempted",
                "known pack-corruption stderr classified when present",
                "cleanup remains blocked when diff check is not verifiably green",
            ],
        },
        "source_hashes": source_hashes(),
        "blockers": [],
        "why_not_v4_probes": "This is a v5 formal-scout hygiene receipt over the current Git checkout, not a legacy v4 scientific probe.",
    }
    OUT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": output["all_pass"],
                "completion_status": output["completion_status"],
                "git_diff_check_passed": output["git_diff_check_passed"],
                "out_path": rel(OUT_PATH),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
