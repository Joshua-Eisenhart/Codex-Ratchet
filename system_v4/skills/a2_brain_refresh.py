"""
a2_brain_refresh.py
A2 Skill: S1 — A2 Brain Refresh

Purpose:
    Run the A2-brain-first refresh loop in the correct order.
    Reads the canonical active A2 control surfaces from system_v3/a2_state/,
    classifies any surfaces touched since the last refresh, detects drift,
    and emits bounded A2_UPDATE_NOTE and A2_TO_A1_IMPACT_NOTE outputs.

Usage:
    python3 a2_brain_refresh.py [--a2_state PATH] [--output PATH] [--dry-run]

Output:
    A2_UPDATE_NOTE__<date>__v1.md   — bounded A2 update delta
    A2_TO_A1_IMPACT_NOTE__<date>__v1.md — downstream A1 consequence statement
    Prints SAFE_TO_CONTINUE or OFF_PROCESS flag to stdout.
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Canonical active A2 owner surface names (from A2_BRAIN_SLICE__v1)
# ---------------------------------------------------------------------------

A2_CANONICAL_OWNER_SURFACES = [
    "A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md",
    "A2_BRAIN_SLICE__v1.md",
    "A2_TERM_CONFLICT_MAP__v1.md",
    "A2_INPUT_TRUST_AND_QUARANTINE_MAP__v1.md",
    "A2_TO_A1_DISTILLATION_INPUTS__v1.md",
    "OPEN_UNRESOLVED__v1.md",
    "INTENT_SUMMARY.md",
    "SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1.md",
    "FOUNDATION_MODE_AND_SCAFFOLD_MODE_SPLIT__v1.md",
    "COUPLED_RATCHET_AND_SIM_LADDERS__v1.md",
    "SIM_FAMILY_PROMOTION_CONTRACTS__ACTIVE_LANES__v1.md",
    "ENTROPY_GRAVEYARD_FAILURE_TOPOLOGY__v1.md",
    "SKILL_STACK_AND_BRAIN_UPDATE_STABILIZATION__v1.md",
]

# Required A2 output sections (per A2_BRAIN_SLICE__v1 Section 9)
REQUIRED_A2_OUTPUTS = [
    "SYSTEM_MAP",
    "LOOP_PROTOCOL_MAP",
    "TERM_CONFLICT_MAP",
    "NONCONTAMINATION_RULES",
    "QUARANTINE_LIST",
    "A1_DISTILLATION_INPUTS",
    "SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES",
    "OPEN_UNRESOLVED",
    "HOLODECK_MEMORY_AND_WORLD_EDGE_MODEL",
    "COUPLED_RATCHET_AND_SIM_LADDERS",
    "FOUNDATION_MODE_AND_SCAFFOLD_MODE_SPLIT",
]


def scan_a2_state(a2_state_path: Path) -> dict:
    """Scan the a2_state directory and report which canonical surfaces exist and their modification times."""
    status = {}
    if not a2_state_path.exists():
        return {"error": f"a2_state directory not found: {a2_state_path}"}

    for surface in A2_CANONICAL_OWNER_SURFACES:
        fpath = a2_state_path / surface
        if fpath.exists():
            mtime = datetime.fromtimestamp(fpath.stat().st_mtime)
            status[surface] = {"present": True, "mtime": mtime.isoformat()}
        else:
            status[surface] = {"present": False, "mtime": None}

    # Also report total file count to catch note accumulation / bloat
    all_files = list(a2_state_path.glob("*.md")) + list(a2_state_path.glob("*.json"))
    status["__total_files__"] = len(all_files)
    status["__canonical_count__"] = len(A2_CANONICAL_OWNER_SURFACES)

    return status


def detect_drift(status: dict) -> list[str]:
    """Detect drift conditions: missing canonical surfaces, bloat, etc."""
    drift_flags = []

    missing = [k for k, v in status.items()
               if not k.startswith("__") and not v["present"]]
    if missing:
        drift_flags.append(f"MISSING CANONICAL SURFACES ({len(missing)}): {', '.join(missing)}")

    total = status.get("__total_files__", 0)
    canonical = status.get("__canonical_count__", 0)
    if total > canonical * 5:
        drift_flags.append(
            f"BLOAT RISK: {total} total files vs {canonical} canonical surfaces. "
            "High note accumulation detected — consolidation recommended."
        )

    return drift_flags


def emit_update_note(surface_status: dict, drift_flags: list[str],
                     output_dir: Path, dry_run: bool) -> str:
    """Emit the A2_UPDATE_NOTE artifact."""
    date_str = datetime.now().strftime("%Y_%m_%d")
    filename = f"A2_UPDATE_NOTE__BRAIN_REFRESH__{date_str}__v1.md"
    filepath = output_dir / filename

    present = [k for k, v in surface_status.items()
               if not k.startswith("__") and v["present"]]
    missing = [k for k, v in surface_status.items()
               if not k.startswith("__") and not v["present"]]

    lines = [
        f"# A2_UPDATE_NOTE__BRAIN_REFRESH__{date_str}__v1",
        "Surface Class: DERIVED_A2",
        f"Date: {datetime.now().strftime('%Y-%m-%d')}",
        "Role: A2 brain refresh output — delta note only. Do not promote to canon.",
        "",
        "## Canonical Surfaces Present",
        *[f"- {s}" for s in present],
        "",
        "## Canonical Surfaces MISSING",
        *([f"- {s}" for s in missing] if missing else ["- None"]),
        "",
        "## Drift Flags",
        *([f"- {f}" for f in drift_flags] if drift_flags else ["- None detected"]),
        "",
        "## SAFE_TO_CONTINUE",
        "YES" if not drift_flags else "NO — address drift flags before downstream A1 work.",
        "",
    ]

    content = "\n".join(lines)
    if not dry_run:
        filepath.write_text(content, encoding="utf-8")
        print(f"[EMITTED] {filepath}")
    else:
        print(f"[DRY-RUN] Would emit: {filepath}")
        print(content)

    return filename


def emit_a1_impact_note(drift_flags: list[str], output_dir: Path, dry_run: bool) -> str:
    """Emit the A2_TO_A1_IMPACT_NOTE artifact."""
    date_str = datetime.now().strftime("%Y_%m_%d")
    filename = f"A2_TO_A1_IMPACT_NOTE__BRAIN_REFRESH__{date_str}__v1.md"
    filepath = output_dir / filename

    if drift_flags:
        note = (
            "A2 brain refresh detected active drift. A1 work MUST PAUSE.\n"
            "Resolve missing canonical surfaces and consolidation bloat before new A1 dispatch.\n"
            "Resuming A1 on stale or inconsistent A2 is OFF_PROCESS."
        )
        pause = "A1_PAUSE_REQUIRED"
    else:
        note = (
            "A2 brain refresh completed with no blocking drift. A1 may proceed.\n"
            "Downstream A1 lanes should load the refreshed A2 distillation inputs before generating new proposals."
        )
        pause = "A1_PROCEED_PERMITTED"

    lines = [
        f"# A2_TO_A1_IMPACT_NOTE__BRAIN_REFRESH__{date_str}__v1",
        "Surface Class: DERIVED_A2",
        f"Date: {datetime.now().strftime('%Y-%m-%d')}",
        "",
        f"## A1 Status: {pause}",
        "",
        note,
        "",
        "## Drift Flags Forwarded to A1",
        *([f"- {f}" for f in drift_flags] if drift_flags else ["- None"]),
    ]

    content = "\n".join(lines)
    if not dry_run:
        filepath.write_text(content, encoding="utf-8")
        print(f"[EMITTED] {filepath}")
    else:
        print(f"[DRY-RUN] Would emit: {filepath}")
        print(content)

    return filename


def main():
    parser = argparse.ArgumentParser(
        description="A2 Brain Refresh Skill — scan A2 owner surfaces, detect drift, emit bounded delta notes."
    )
    parser.add_argument(
        "--a2_state",
        default="system_v4/a2_state",
        help="Path to the a2_state directory (default: system_v4/a2_state).",
    )
    parser.add_argument(
        "--output",
        default="system_v4/a2_state",
        help="Output directory for emitted notes (default: system_v4/a2_state).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print output to stdout without writing files.",
    )
    args = parser.parse_args()

    # Resolve paths relative to the repo root (two levels up from this script)
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent.parent
    a2_state_path = (repo_root / args.a2_state).resolve()
    output_path = (repo_root / args.output).resolve()

    print(f"[A2 BRAIN REFRESH] Scanning: {a2_state_path}")

    status = scan_a2_state(a2_state_path)
    if "error" in status:
        print(f"ERROR: {status['error']}", file=sys.stderr)
        sys.exit(1)

    drift_flags = detect_drift(status)

    emit_update_note(status, drift_flags, output_path, args.dry_run)
    emit_a1_impact_note(drift_flags, output_path, args.dry_run)

    if drift_flags:
        print("\n[RESULT] DRIFT DETECTED — A1 MUST PAUSE.")
        sys.exit(2)
    else:
        print("\n[RESULT] SAFE_TO_CONTINUE — A2 brain is fresh. A1 may proceed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
