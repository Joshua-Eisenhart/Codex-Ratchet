#!/usr/bin/env python3
"""receipts.py — write 10-field side-quest receipts with full provenance.

Schema mirrors the canonical sim receipt schema (operation_sequence, carrier_topology,
observable, pass_fail_predicate, graveyard_companions, baseline_variants,
alternative_formulations, tool_function_needs, lego_coupling_target, claim_ceiling) —
PLUS explicit side-quest fencing fields so this can never be promoted to canonical
admission by accident.

Provenance fields enforce goal-stability: phase_file_sha256, candidate_sha256,
runner_sha256, frozen_manifest_path, git_state, runner_command, timestamp_utc.
If any of these change between runs, the receipt records the change.
"""
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path


SIDE_QUEST_FENCE = {
    "classification": "side_quest_only",
    "admission_scope": "noncanonical_exploration",
    "promotion_allowed": False,
    "claim_ceiling": "side_quest receipt only; no bridge, GStack, axis, QIT, or nonclassical admission",
    "out_of_scope": [
        "no QIT engine admission",
        "no GStack promotion",
        "no axis promotion",
        "no nonclassical admission",
        "no bridge admission",
    ],
}


def _sha256_file(path: Path) -> str:
    """SHA-256 of a file's bytes; '' if file missing."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def _git_state(repo_root: Path) -> dict:
    """Capture git HEAD + dirty flag for repo_root."""
    state = {"head": "", "dirty": None, "branch": ""}
    try:
        head = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=2,
        )
        if head.returncode == 0:
            state["head"] = head.stdout.strip()
        branch = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=2,
        )
        if branch.returncode == 0:
            state["branch"] = branch.stdout.strip()
        status = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain"],
            capture_output=True, text=True, timeout=2,
        )
        if status.returncode == 0:
            state["dirty"] = bool(status.stdout.strip())
    except Exception:
        pass
    return state


def build_frozen_manifest(
    runner_path: Path,
    candidate_path: Path,
    phase_paths: list,
    command_argv: list,
    run_id: str,
) -> dict:
    """Build a frozen manifest hashing runner + candidate + every phase contract.

    Written once per run at the start. If any hash differs from a prior run's
    manifest, a passing phase is NOT silently equivalent.
    """
    receipts_root = runner_path.parent
    repo_root = receipts_root
    # Walk up to find .git
    for _ in range(8):
        if (repo_root / ".git").exists():
            break
        repo_root = repo_root.parent
    phase_hashes = {}
    for pp in phase_paths:
        phase_id = pp.stem.replace("phase_", "")
        phase_hashes[phase_id] = {
            "path": str(pp.relative_to(receipts_root.parent) if pp.is_relative_to(receipts_root.parent) else pp),
            "sha256": _sha256_file(pp),
        }
    return {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "command_argv": list(command_argv),
        "cwd": os.getcwd(),
        "runner": {"path": str(runner_path), "sha256": _sha256_file(runner_path)},
        "candidate": {"path": str(candidate_path), "sha256": _sha256_file(candidate_path)},
        "phases": phase_hashes,
        "receipts_module_sha256": _sha256_file(Path(__file__)),
        "git": _git_state(repo_root),
        "python_version": _python_version(),
    }


def _python_version() -> str:
    import sys
    return sys.version.split()[0]


def make_receipt(
    phase_id: str,
    phase_result: dict,
    candidate_path: Path,
    phase_path: Path = None,
    manifest_path: Path = None,
) -> dict:
    """Build a 10-field receipt with side-quest fencing + provenance.

    Hash chain: receipt records frozen_manifest_sha256 so a downstream verifier
    can confirm the receipt was produced under exactly that manifest. Editing the
    manifest after the fact would invalidate this hash on every receipt that
    references it."""
    now = datetime.now(timezone.utc).isoformat()
    phase_file_str = str(phase_path) if phase_path else f"contracts/phase_{phase_id}.py"
    phase_sha = _sha256_file(phase_path) if phase_path else ""
    cand_sha = _sha256_file(candidate_path) if candidate_path else ""
    manifest_sha = _sha256_file(manifest_path) if manifest_path else ""
    receipt = {
        # 10-field sim-receipt-compatible structure
        "operation_sequence": f"loop_runner_phase_{phase_id}",
        "carrier_topology": "4-qubit Hilbert (16-dim) over Hopf-fibered Weyl carrier",
        "observable": {
            "phase_pass": phase_result.get("pass"),
            "failures": phase_result.get("failures", []),
            "metrics": phase_result.get("metrics", {}),
        },
        "pass_fail_predicate": f"all phase checks pass; see {phase_file_str} for predicates",
        "graveyard_companions": phase_result.get("graveyard_companions", []),
        "baseline_variants": phase_result.get("baseline_variants", []),
        "alternative_formulations": phase_result.get("alternative_formulations", []),
        "tool_function_needs": phase_result.get("tool_function_needs", []),
        "lego_coupling_target": "none (side-quest exploration, not admission)",

        # Nominalist object schema (§1A of .tmp/qit_engine_overall_math_exploration).
        # An "object" is not primitive; it is the survivor equivalence class
        # S_C / ~_M. Phases that don't expose these fields demote to "partial
        # receipt" — the doctrine binding is on the schema, not the value.
        "nominalist": {
            "candidate_set": phase_result.get("candidate_set"),          # X
            "constraint_set": phase_result.get("constraint_set"),        # C
            "probe_family": phase_result.get("probe_family"),            # M
            "distinguishability_relation": phase_result.get("distinguishability_relation"),  # ~_M
            "survivor_classes": phase_result.get("survivor_classes"),    # S_C / ~_M
            "killed_neighbors": phase_result.get("killed_neighbors") or phase_result.get("graveyard_companions", []),
            "claim_ceiling": phase_result.get("claim_ceiling"),
        },

        # side-quest fencing (explicit, non-removable)
        **SIDE_QUEST_FENCE,

        # provenance — fixes goal-stability + replay
        "phase_id": phase_id,
        "phase_file": phase_file_str,
        "phase_file_sha256": phase_sha,
        "candidate_path": str(candidate_path),
        "candidate_sha256": cand_sha,
        "frozen_manifest": str(manifest_path) if manifest_path else None,
        "frozen_manifest_sha256": manifest_sha,
        "timestamp_utc": now,
        "elapsed_s": phase_result.get("elapsed_s"),
    }
    return receipt


def write_receipt(
    run_dir: Path,
    phase_id: str,
    phase_result: dict,
    candidate_path: Path,
    phase_path: Path = None,
    manifest_path: Path = None,
) -> Path:
    """Write a receipt JSON file under run_dir/phase_<id>_results.json."""
    run_dir.mkdir(parents=True, exist_ok=True)
    receipt = make_receipt(phase_id, phase_result, candidate_path, phase_path, manifest_path)
    out = run_dir / f"phase_{phase_id}_results.json"
    out.write_text(json.dumps(receipt, indent=2, default=str))
    return out


def write_frozen_manifest(run_dir: Path, manifest: dict) -> Path:
    """Write the run's frozen manifest under run_dir/_frozen_manifest.json."""
    run_dir.mkdir(parents=True, exist_ok=True)
    out = run_dir / "_frozen_manifest.json"
    out.write_text(json.dumps(manifest, indent=2, default=str))
    return out


def write_run_hash(run_dir: Path) -> Path:
    """After all receipts are written, compute a single hash over (manifest_sha,
    sorted-receipt-shas) and write _run_hash.txt. A verifier can recompute this
    to confirm no receipt or manifest in the run has been modified post-hoc.
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = run_dir / "_frozen_manifest.json"
    receipts = sorted([p for p in run_dir.iterdir()
                       if p.is_file() and p.name.startswith("phase_")
                       and p.name.endswith("_results.json")])
    h = hashlib.sha256()
    h.update(_sha256_file(manifest).encode())
    for r in receipts:
        h.update(_sha256_file(r).encode())
    out = run_dir / "_run_hash.txt"
    out.write_text(h.hexdigest() + "\n")
    return out


def check_manifest_drift(prior_manifest_path: Path, current_manifest: dict) -> list:
    """Compare current manifest against a prior one; return list of drift entries.

    Each entry: {field, prior, current}. Empty list = no drift.
    """
    if not prior_manifest_path.exists():
        return []
    try:
        prior = json.loads(prior_manifest_path.read_text())
    except Exception:
        return []
    drift = []
    for k in ("runner", "candidate", "receipts_module_sha256"):
        if prior.get(k) != current_manifest.get(k):
            drift.append({"field": k, "prior": prior.get(k), "current": current_manifest.get(k)})
    prior_phases = prior.get("phases", {})
    curr_phases = current_manifest.get("phases", {})
    for pid in set(prior_phases) | set(curr_phases):
        if prior_phases.get(pid, {}).get("sha256") != curr_phases.get(pid, {}).get("sha256"):
            drift.append({
                "field": f"phases.{pid}.sha256",
                "prior": prior_phases.get(pid, {}).get("sha256"),
                "current": curr_phases.get(pid, {}).get("sha256"),
            })
    return drift
