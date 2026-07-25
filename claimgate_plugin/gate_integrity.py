#!/usr/bin/env python3
"""GATE SELF-INTEGRITY — hash the gate's own load-bearing sources and compare
against a manifest.  Closes threat-move #1 (EDIT THE CHECK) only partially, and
the partiality is the most important thing in this file.

Fired by: CI and/or the pre-commit chain.  Pure stdlib on purpose — the integrity
check must run where numpy/numba/z3 are absent, and must not import anything a
tampering agent could shadow.

=============================================================================
READ THIS BEFORE TRUSTING THIS FILE
=============================================================================
This script CANNOT prevent an agent from editing the gate.  An agent that edits
a gate source AND runs ``--update`` AND commits both in one commit produces a
green tree.  That is not a bug in this script; it is a property of where the
script lives.  A check that lives inside the thing it checks can be edited by
whoever can edit the thing it checks.

So do not read a passing run as "the gate is intact".  Read it as "no ONE-SIDED
edit happened".  Those are different claims.

  TIER A — IN-REPO CONTROLS.  The agent CAN write these.
  Effect: RAISE COST and CREATE A DETECTABLE TRACE.  Effect: never PREVENTION.
    * this file, and claimgate_plugin/gate_integrity_manifest.json
    * the self-hash of this file (it hashes itself; see role "self")
    * chain-reference coverage: the chain must not call a script this file
      does not hash (blocks "add an unhashed helper and put the logic there")
    * --audit-cochange: flags commits that touch a gate source AND the manifest
      together, which is the exact signature of the one-commit defeat
    * the hostile-control battery, the formal BMC models, the CI job that runs
      any of the above
  Every one of these is defeated by: edit source -> run --update -> commit both.
  --audit-cochange does not stop that commit.  It makes it visible afterwards,
  and only to someone who actually runs the audit.

  TIER B — GITHUB-SETTINGS CONTROLS.  The agent CANNOT write these; they are
  not files in this tree.  Effect: ACTUAL PREVENTION.
    * REQUIRED STATUS CHECK pinned by name in branch protection / an org
      ruleset.  This is the strongest single control, and the reason is
      non-obvious: if the agent deletes or renames the job, the required check
      never reports, so the PR sits permanently at "expected — waiting for
      status" instead of going green.  Neutering the workflow stops being a
      bypass and becomes a self-inflicted block.
    * CODEOWNERS on .github/ and claimgate_plugin/, with "require review from
      Code Owners" ON and self-approval OFF.  Forces a human on every gate
      edit, which is what actually breaks the one-commit defeat.
    * BLOCKED FORCE-PUSH + required linear history, so history holding the
      trace cannot be rewritten.
    * NO direct pushes to the protected branch (PR-only), so the pre-merge
      checks cannot be sidestepped.
    * THE EXPECTED DIGEST HELD OUTSIDE THIS REPO.  Pass it with
      --expect-digest.  When supplied, the in-repo manifest is IGNORED for the
      verdict, so editing or deleting the manifest changes nothing.  This is
      the only way this script becomes prevention rather than cost.  The pin
      must live somewhere the agent cannot write: a reusable workflow in
      another repo, an org ruleset, a signed tag, or a human's terminal.

  MEASURED STATE OF TIER B IN THIS REPO, 2026-07-24:
    branch protection on main .......... ABSENT (GitHub API: 404 Branch not protected)
    CODEOWNERS ......................... ABSENT (no .github/CODEOWNERS)
    required status checks ............. ABSENT (no protection object to hold them)
  Therefore, as of that date, NOTHING here prevents move #1.  Tier A is all
  that exists, and Tier A is detection.  Do not restate this file as a control
  until the Tier-B rows above read PRESENT.

Exit codes:
  0  clean
  1  INTEGRITY MISMATCH — drift, missing source, missing manifest, digest
     mismatch against --expect-digest, or a chain reference this file does not
     hash.  Fails CLOSED: a check that cannot check must block, not wave through.
  2  usage / IO error
  4  CO-CHANGE FINDING (--audit-cochange only) — kept distinct from 1 because it
     is a review-required signal about history, not drift in the working tree.
Nonzero is a policy/infrastructure disposition, never a scientific verdict.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_REL = "claimgate_plugin/gate_integrity_manifest.json"
SCHEMA = "claimgate.gate_integrity.manifest.v1"

# (repo-relative path, role, enforcing?)
# "enforcing" = this file being weakened weakens what actually blocks a claim.
# Non-enforcing rows are still hashed: drift there is worth seeing, but it does
# not by itself mean the gate stopped gating.
GATE_SOURCES: tuple[tuple[str, str, bool], ...] = (
    ("claimgate_plugin/hooks/post_receipt_gate.sh", "chain-entry", True),
    ("claimgate_plugin/hooks/pre_commit_gate_receipts.sh", "fired-side", True),
    ("claimgate_plugin/intake_supervisor.py", "chain-tier", True),
    ("claimgate_plugin/recompute_veto.py", "chain-tier", True),
    ("claimgate_plugin/three_engine_seal.py", "chain-tier", True),
    ("claimgate_plugin/claim_verify.py", "chain-tier", True),
    ("claimgate_plugin/ratchet_floor.py", "chain-tier", True),
    ("claimgate_plugin/claimgate.mjs", "chain-tier", True),
    ("claimgate_plugin/rules_ratchet.json", "chain-rules", True),
    # Added 2026-07-24 after the coverage check flagged it as an unhashed limb: the
    # chain invokes it from the EXIT trap and a failed ledger write is reported as a
    # non-clean admission, so weakening it weakens what blocks a claim.
    ("claimgate_plugin/gate_ledger.py", "chain-ledger", True),
    ("claimgate_plugin/orphan_receipt_detector.py", "detector", True),
    ("claimgate_plugin/fixtures/hostile/run_hostile_controls.sh", "control-battery", True),
    ("claimgate_plugin/gate_integrity.py", "self", True),
    ("scripts/ci_three_engine_seal.py", "ci-enforcing", True),
    (".github/workflows/three-engine-seal.yml", "ci-enforcing", True),
    ("claimgate_plugin/formal/chain_bmc_z3.py", "formal", False),
    ("claimgate_plugin/formal/chain_bmc_cvc5.py", "formal", False),
    (".github/workflows/ci.yml", "ci-nonenforcing", False),
    (".github/workflows/ratchet-ci.yml", "ci-nonenforcing", False),
)

# Files whose text is scanned for "does the chain call something unhashed?".
CHAIN_CALLERS = (
    "claimgate_plugin/hooks/post_receipt_gate.sh",
    "claimgate_plugin/hooks/pre_commit_gate_receipts.sh",
    "scripts/ci_three_engine_seal.py",
    ".github/workflows/three-engine-seal.yml",
)

# $script_dir/../foo.py  |  claimgate_plugin/foo.py  |  scripts/foo.py
_REF_PATTERNS = (
    re.compile(r"\$script_dir/\.\./([A-Za-z0-9_./-]+\.(?:py|sh|mjs))"),
    re.compile(r"\$repo/(claimgate_plugin/[A-Za-z0-9_./-]+\.(?:py|sh|mjs))"),
    re.compile(r"\b((?:claimgate_plugin|scripts)/[A-Za-z0-9_./-]+\.(?:py|sh|mjs))"),
)

# Referenced-but-deliberately-unhashed: advisory only, cannot change a verdict.
COVERAGE_EXEMPT = {
    "claimgate_plugin/suggest.mjs",  # advisory advise(); output+exit discarded by design
}


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _digest_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _entry(root: Path, rel: str, role: str, enforcing: bool) -> dict | None:
    p = root / rel
    if not p.is_file():
        return None
    data = p.read_bytes()
    return {
        "sha256": _digest_bytes(data),
        "bytes": len(data),
        "exec": bool(os.stat(p).st_mode & 0o111),
        "role": role,
        "enforcing": enforcing,
    }


def scan_sources(root: Path) -> tuple[dict[str, dict], list[str]]:
    """Return (entries, missing_paths) from what is actually on disk now."""
    entries: dict[str, dict] = {}
    missing: list[str] = []
    for rel, role, enforcing in GATE_SOURCES:
        e = _entry(root, rel, role, enforcing)
        if e is None:
            missing.append(rel)
        else:
            entries[rel] = e
    return entries, missing


def rollup_digest(entries: dict[str, dict], enforcing_only: bool = False) -> str:
    """Order-independent digest over path+sha256. Never includes itself."""
    h = hashlib.sha256()
    for rel in sorted(entries):
        if enforcing_only and not entries[rel].get("enforcing"):
            continue
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(entries[rel]["sha256"].encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def chain_reference_coverage(root: Path) -> list[str]:
    """Scripts the chain invokes that GATE_SOURCES does not hash.

    Blocks the obvious escape: leave every hashed file untouched, add a NEW
    helper, move the weakening into it.
    """
    hashed = {rel for rel, _, _ in GATE_SOURCES}
    uncovered: set[str] = set()
    for caller in CHAIN_CALLERS:
        p = root / caller
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for pat in _REF_PATTERNS:
            for m in pat.finditer(text):
                ref = m.group(1)
                if not ref.startswith(("claimgate_plugin/", "scripts/")):
                    ref = f"claimgate_plugin/{ref}"
                if ref in hashed or ref in COVERAGE_EXEMPT:
                    continue
                if (root / ref).is_file():
                    uncovered.add(ref)
    return sorted(uncovered)


def build_manifest(root: Path) -> tuple[dict, list[str]]:
    entries, missing = scan_sources(root)
    manifest = {
        "schema": SCHEMA,
        "algo": "sha256",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_by": "claimgate_plugin/gate_integrity.py --update",
        "sources_digest": rollup_digest(entries),
        "enforcing_digest": rollup_digest(entries, enforcing_only=True),
        "entry_count": len(entries),
        "missing_at_generation": sorted(missing),
        "prevention_note": (
            "IN-REPO manifest. An agent that edits a source and reruns --update in the "
            "same commit produces a matching manifest. This file raises cost and leaves "
            "a trace; it does not prevent. Prevention requires GitHub-settings controls "
            "(required status check pinned by name, CODEOWNERS on .github/ and "
            "claimgate_plugin/, blocked force-push) or an out-of-repo digest pin passed "
            "via --expect-digest. See the module docstring."
        ),
        "entries": entries,
    }
    return manifest, missing


def load_manifest(path: Path) -> dict | None:
    try:
        obj = json.loads(path.read_bytes())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return obj if isinstance(obj, dict) else None


def verify(root: Path, manifest_path: Path, expect_digest: str | None) -> tuple[int, list[str], str]:
    """Compare disk against the manifest and/or an external digest pin."""
    findings: list[str] = []
    entries, missing = scan_sources(root)
    live_all = rollup_digest(entries)
    live_enf = rollup_digest(entries, enforcing_only=True)

    for rel in missing:
        findings.append(
            f"MISSING SOURCE {rel} — a deleted gate source is the strongest neuter; "
            f"absent is BLOCKED_MISSING, never N/A-ok"
        )

    for rel in chain_reference_coverage(root):
        findings.append(
            f"UNHASHED CHAIN REFERENCE {rel} — the chain invokes it but GATE_SOURCES "
            f"does not hash it; add it to GATE_SOURCES or the gate has an unwatched limb"
        )

    # External pin is authoritative and manifest-independent.
    if expect_digest:
        want = expect_digest.strip().lower()
        if want != live_all:
            findings.append(
                f"EXTERNAL PIN MISMATCH — --expect-digest {want} != live sources_digest {live_all}"
            )
        if not manifest_path.is_file():
            print(
                "gate_integrity: note — in-repo manifest absent, but an external pin was "
                "supplied, so the verdict does not depend on it.",
                file=sys.stderr,
            )
        return (1 if findings else 0), findings, live_all

    manifest = load_manifest(manifest_path)
    if manifest is None:
        findings.append(
            f"MANIFEST ABSENT OR UNPARSEABLE {manifest_path.name} — deleting the manifest "
            f"is itself the neuter move, so this FAILS CLOSED. Regenerate with --update "
            f"only as a conscious, reviewed re-baseline."
        )
        return 1, findings, live_all

    if manifest.get("schema") != SCHEMA:
        findings.append(f"MANIFEST SCHEMA {manifest.get('schema')!r} != {SCHEMA!r}")

    recorded = manifest.get("entries")
    if not isinstance(recorded, dict):
        findings.append("MANIFEST has no usable 'entries' object")
        return 1, findings, live_all

    for rel in sorted(set(recorded) | set(entries)):
        want = recorded.get(rel)
        got = entries.get(rel)
        if want is None:
            findings.append(
                f"UNRECORDED SOURCE {rel} — present on disk and in GATE_SOURCES but "
                f"absent from the manifest"
            )
            continue
        if got is None:
            continue  # already reported as MISSING SOURCE
        if want.get("sha256") != got["sha256"]:
            findings.append(
                f"DRIFT {rel} [{got['role']}"
                f"{', enforcing' if got['enforcing'] else ''}] "
                f"manifest={str(want.get('sha256'))[:16]}… live={got['sha256'][:16]}… "
                f"({want.get('bytes')} -> {got['bytes']} bytes)"
            )
        elif want.get("exec") != got["exec"]:
            findings.append(
                f"MODE CHANGE {rel} exec {want.get('exec')} -> {got['exec']} (content identical)"
            )

    # Rollup cross-check: catches a hand-edited entry table whose rollup was not updated.
    for key, live in (("sources_digest", live_all), ("enforcing_digest", live_enf)):
        rec = manifest.get(key)
        if isinstance(rec, str) and rec.strip().lower() != live:
            findings.append(f"ROLLUP MISMATCH {key} manifest={rec[:16]}… live={live[:16]}…")

    return (1 if findings else 0), findings, live_all


def audit_cochange(root: Path, since: str | None) -> tuple[int, list[str]]:
    """Flag commits whose file set is the signature of the one-commit defeat.

    Two patterns, both reported, neither prevented:
      SOURCE+MANIFEST  a gate source and the manifest moved together — exactly
                       what "edit the check, then rebaseline it" looks like.
      MANIFEST-ONLY    the manifest moved with no source change — a digest
                       pre-load, or a stale rebaseline.
    A legitimate reviewed re-baseline looks identical. That is the point: the
    signature is reviewable, not decidable, so this reports rather than judges.
    """
    rng = f"{since}..HEAD" if since else "HEAD"
    try:
        proc = subprocess.run(
            ["git", "log", "--format=%x1e%H%x1f%s", "--name-only", rng],
            cwd=root, capture_output=True, text=True, check=False,
        )
    except OSError as exc:
        return 2, [f"git unavailable: {exc}"]
    if proc.returncode != 0:
        return 2, [f"git log failed: {(proc.stderr or '').strip()[:200]}"]

    sources = {rel for rel, _, _ in GATE_SOURCES}
    findings: list[str] = []
    for block in proc.stdout.split("\x1e"):
        block = block.strip("\n")
        if not block:
            continue
        head, _, rest = block.partition("\n")
        sha, _, subject = head.partition("\x1f")
        files = {ln.strip() for ln in rest.splitlines() if ln.strip()}
        touched = sorted(files & sources)
        manifest_touched = MANIFEST_REL in files
        if touched and manifest_touched:
            findings.append(
                f"SOURCE+MANIFEST {sha[:12]} {subject[:60]} :: {', '.join(touched)}"
            )
        elif manifest_touched:
            findings.append(f"MANIFEST-ONLY  {sha[:12]} {subject[:60]}")
    return (4 if findings else 0), findings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Gate self-integrity: hash the gate's own sources, compare to a manifest.",
        epilog="A pass means no one-sided edit. It does NOT mean the gate is intact. "
               "See the module docstring for what actually prevents move #1.",
    )
    ap.add_argument("--root", type=Path, default=None, help="repo root (default: parent of this file)")
    ap.add_argument("--manifest", type=Path, default=None, help=f"default: {MANIFEST_REL}")
    ap.add_argument("--update", action="store_true", help="regenerate the manifest (conscious re-baseline)")
    ap.add_argument("--expect-digest", default=None,
                    help="authoritative out-of-repo sources_digest pin; when given, the "
                         "in-repo manifest is ignored for the verdict")
    ap.add_argument("--emit-digest", action="store_true",
                    help="print the live sources_digest and exit 0 (use as gate_source_digest "
                         "in the durable ledger line orphan_receipt_detector.py demands)")
    ap.add_argument("--audit-cochange", action="store_true",
                    help="scan git history for source+manifest co-change commits (exit 4 on findings)")
    ap.add_argument("--since", default=None, help="revision floor for --audit-cochange")
    args = ap.parse_args(argv)

    root = (args.root or repo_root()).resolve()
    manifest_path = args.manifest or (root / MANIFEST_REL)

    if args.emit_digest:
        entries, _ = scan_sources(root)
        print(rollup_digest(entries))
        return 0

    if args.audit_cochange:
        code, findings = audit_cochange(root, args.since)
        rng = f"{args.since}..HEAD" if args.since else "HEAD (full history)"
        print(f"gate_integrity co-change audit over {rng}")
        for f in findings:
            print(f"  {f}")
        if code == 4:
            print(f"\n{len(findings)} commit(s) carry the co-change signature. This is DETECTION, "
                  f"not prevention: each needs a human to say whether it was a reviewed "
                  f"re-baseline or move #1.")
        elif code == 0:
            print("  no source+manifest co-change and no manifest-only commit found.")
        return code

    if args.update:
        manifest, missing = build_manifest(root)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=1, sort_keys=False) + "\n",
                                 encoding="utf-8")
        print(f"gate_integrity: manifest written {manifest_path}")
        print(f"  entries          {manifest['entry_count']}")
        print(f"  sources_digest   {manifest['sources_digest']}")
        print(f"  enforcing_digest {manifest['enforcing_digest']}")
        for rel in missing:
            print(f"  MISSING (not recorded) {rel}", file=sys.stderr)
        uncovered = chain_reference_coverage(root)
        for rel in uncovered:
            print(f"  UNHASHED CHAIN REFERENCE {rel} — add to GATE_SOURCES", file=sys.stderr)
        print("\n  WARNING: updating this manifest in the SAME commit as a gate-source edit is "
              "exactly the one-commit defeat of this check. --audit-cochange will flag it. "
              "Pin sources_digest outside the repo (--expect-digest) if you need the check to "
              "be prevention rather than cost.", file=sys.stderr)
        return 0

    code, findings, live = verify(root, manifest_path, args.expect_digest)
    print(f"gate_integrity: {len(GATE_SOURCES)} declared source(s), live sources_digest {live[:16]}…")
    if code == 0:
        print("CLEAN — every declared gate source matches its recorded digest.")
        print("Scope of this result: no ONE-SIDED edit. NOT a claim that the gate is intact; "
              "a source+manifest co-update in one commit also reads CLEAN here.")
        return 0
    for f in findings:
        print(f"FINDING {f}", file=sys.stderr)
    print(f"\ngate_integrity: MISMATCH — {len(findings)} finding(s). Failing closed.", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
