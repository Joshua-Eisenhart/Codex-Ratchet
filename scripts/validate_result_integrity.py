#!/usr/bin/env python3
"""GATE 3 — Result-integrity / pin-drift detector (Class-C, mechanical only).

Detects three integrity defects in committed/working result JSONs WITHOUT
re-running any sim and WITHOUT LLM judgment. Every decision is a deterministic
recompute, a static-source scan, or a read-only ``git`` inspection.

It detects:

  (a) FRAGILE PIN
      A result JSON whose own ``result_sha256``/``source_sha256`` self-pin is
      computed over a body that INCLUDES ``generated_at`` (or another timestamp
      key) AND the sim has no ``*_envelope_results.json`` that independently
      re-pins the result. Such a pin recomputes to a new value on every run, so
      any downstream EXPECTED_*_SHA256 constant that pins it silently rots.
      A self-pin that excludes the timestamp, or whose result is also pinned by
      an envelope, is robust and is NOT flagged.

  (b) WORKING-TREE DRIFT
      A result JSON whose working-tree copy differs from its committed
      (``HEAD``) copy ONLY by ``generated_at`` + key reorder + derived sha
      fields, with every math-bearing value byte-identical after canonical
      normalization. These are re-run artifacts that change no math yet break
      downstream pins. Genuine value changes (a flipped ``ok``, a changed count)
      are reported as ``real_change`` and are NOT counted as drift.

  (c) HARDCODED-PIN EXPOSURE
      Every ``EXPECTED_*_SHA256 = "<64-hex>"`` constant across
      system_v6/sims/*/*.py and scripts/*.py, counted, with the result file
      each constant pins (resolved by matching the literal hex to a stored
      sha / file hash where determinable).

GATE CEILING
------------
This is a STRUCTURAL integrity gate. It proves only that result JSONs are
internally self-consistent w.r.t. their pins and free of math-silent re-run
drift. It does NOT recompute sim math, re-run any engine, verify that a result
is scientifically correct, or grant any status above ``exists``. A clean pass
means "no fragile self-pins, no math-silent working-tree drift, hardcoded pins
inventoried" — nothing about whether the underlying sim is canonical, admitted,
or even ``runs``. Status ladder is untouched: this gate sits below ``runs``.

Output: JSON ``{"ok": bool, "violations": [...], "report": {...}}`` on stdout.
Exit 1 on any violation (fragile pin or working-tree drift); exit 0 otherwise.
Hardcoded-pin exposure is an inventory (reported, never a violation by itself).

Run ``--selftest`` for an in-process deterministic self-check (exit 0/1).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SIMS_DIR = ROOT / "system_v6" / "sims"
SCRIPTS_DIR = ROOT / "scripts"

# Keys excluded from the canonical "math body" of a result: the timestamp and
# any field derived from the body itself (the self-pins).
TIMESTAMP_KEYS = ("generated_at", "timestamp", "generated_at_utc", "run_time", "ran_at")
DERIVED_PIN_KEYS = (
    "result_sha256",
    "source_sha256",
    "result_sha256_without_self",
)

# Canonical serialization used by the sims' own ``stable_sha256`` recipe:
#   json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _stable_sha256(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _is_hex64(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _has_timestamp(body: dict[str, Any]) -> bool:
    return any(k in body for k in TIMESTAMP_KEYS)


def _normalize_math_body(value: Any) -> Any:
    """Drop timestamp + derived-pin keys at every depth and sort, so that two
    documents compare equal iff their math-bearing values agree (order- and
    timestamp-insensitive)."""
    drop = set(TIMESTAMP_KEYS) | set(DERIVED_PIN_KEYS)
    if isinstance(value, dict):
        return {k: _normalize_math_body(v) for k, v in sorted(value.items()) if k not in drop}
    if isinstance(value, list):
        return [_normalize_math_body(v) for v in value]
    return value


# ---------------------------------------------------------------------------
# (a) FRAGILE PIN
# ---------------------------------------------------------------------------
def detect_fragile_pins(result_files: list[Path]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in result_files:
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(doc, dict):
            continue
        # An envelope sibling that re-pins this result makes the self-pin
        # non-fragile (the envelope is the stable cross-file pin).
        has_envelope = any(p.name.endswith("_envelope_results.json") and p.stat().st_size > 0 for p in path.parent.glob("*_envelope_results.json"))
        for key in DERIVED_PIN_KEYS:
            stored = doc.get(key)
            if not _is_hex64(stored):
                continue
            body = {k: v for k, v in doc.items() if k != key}
            if _stable_sha256(body) != stored:
                # Not a recomputable self-pin under the canonical recipe
                # (e.g. a file-hash or a foreign recipe) -> cannot adjudicate
                # fragility mechanically; leave it alone.
                continue
            if not _has_timestamp(body):
                # Self-pin excludes the timestamp -> stable across reruns -> robust.
                continue
            if has_envelope:
                # Result is independently pinned by its envelope -> not fragile.
                continue
            findings.append(
                {
                    "kind": "fragile_pin",
                    "result": _rel(path),
                    "pin_field": key,
                    "stored": stored,
                    "reason": "self-pin hashed over a body that includes a timestamp key and no envelope re-pins it; value rots on every re-run",
                }
            )
    return findings


# ---------------------------------------------------------------------------
# (b) WORKING-TREE DRIFT  (read-only git)
# ---------------------------------------------------------------------------
def _git(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return proc.returncode, proc.stdout


def detect_working_tree_drift() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Returns (drift_findings, real_change_rows). Read-only git only."""
    drift: list[dict[str, Any]] = []
    real: list[dict[str, Any]] = []
    code, out = _git(["status", "--porcelain"])
    if code != 0:
        return drift, real
    for line in out.splitlines():
        if not line.strip():
            continue
        status = line[:2]
        rel_path = line[3:].strip()
        # only modified (not added/deleted/renamed) tracked result JSONs
        if "M" not in status:
            continue
        if "/results/" not in rel_path or not rel_path.endswith(".json"):
            continue
        wt_path = ROOT / rel_path
        c_code, committed = _git(["show", f"HEAD:{rel_path}"])
        if c_code != 0:
            continue
        try:
            committed_doc = json.loads(committed)
            working_doc = json.loads(wt_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        math_identical = _normalize_math_body(committed_doc) == _normalize_math_body(working_doc)
        if math_identical:
            drift.append(
                {
                    "kind": "working_tree_drift",
                    "result": rel_path,
                    "reason": "working-tree copy is math-identical to HEAD; differs only by timestamp/key-order/derived-sha; this breaks any downstream pin",
                }
            )
        else:
            real.append({"result": rel_path, "classification": "real_change"})
    return drift, real


# ---------------------------------------------------------------------------
# (c) HARDCODED-PIN EXPOSURE  (static source scan)
# ---------------------------------------------------------------------------
import re

_EXPECTED_RE = re.compile(
    r'(?P<name>EXPECTED_[A-Z0-9_]*SHA256[A-Z0-9_]*)\s*[:=]\s*[\'"](?P<hex>[0-9a-f]{64})[\'"]'
)


def _index_stored_shas(result_files: list[Path]) -> dict[str, list[str]]:
    """Map every 64-hex value found anywhere in any result JSON -> the result
    file(s) that contain it, so a hardcoded EXPECTED constant can be resolved
    to what it pins."""
    index: dict[str, list[str]] = {}

    def walk(node: Any, sink: set[str]) -> None:
        if isinstance(node, dict):
            for v in node.values():
                walk(v, sink)
        elif isinstance(node, list):
            for v in node:
                walk(v, sink)
        elif _is_hex64(node):
            sink.add(node)

    for path in result_files:
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        sink: set[str] = set()
        walk(doc, sink)
        for h in sink:
            index.setdefault(h, []).append(_rel(path))
    return index


def detect_hardcoded_pins(result_files: list[Path]) -> list[dict[str, Any]]:
    py_files = sorted(SIMS_DIR.glob("*/*.py")) + sorted(SCRIPTS_DIR.glob("*.py"))
    sha_index = _index_stored_shas(result_files)
    pins: list[dict[str, Any]] = []
    for py in py_files:
        try:
            text = py.read_text(encoding="utf-8")
        except Exception:
            continue
        for m in _EXPECTED_RE.finditer(text):
            name = m.group("name")
            hex_val = m.group("hex")
            line_no = text.count("\n", 0, m.start()) + 1
            pins_to = sha_index.get(hex_val, [])
            pins.append(
                {
                    "constant": name,
                    "source": f"{_rel(py)}:{line_no}",
                    "sha256": hex_val,
                    "pins_result_files": pins_to,
                    "resolved": bool(pins_to),
                }
            )
    return pins


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------
def _all_result_files() -> list[Path]:
    return sorted(SIMS_DIR.glob("*/results/*.json"))


def run() -> dict[str, Any]:
    result_files = _all_result_files()
    fragile = detect_fragile_pins(result_files)
    drift, real = detect_working_tree_drift()
    pins = detect_hardcoded_pins(result_files)

    violations = fragile + drift
    report = {
        "fragile_pin_count": len(fragile),
        "fragile_pins": fragile,
        "drifted_count": len(drift),
        "drifted": drift,
        "real_change_count": len(real),
        "real_changes": real,
        "hardcoded_pin_count": len(pins),
        "hardcoded_pins_resolved": sum(1 for p in pins if p["resolved"]),
        "hardcoded_pins": pins,
        "result_files_scanned": len(result_files),
    }
    return {"ok": not violations, "violations": violations, "report": report}


# ---------------------------------------------------------------------------
# self-test (deterministic, in-process; touches no repo files)
# ---------------------------------------------------------------------------
def selftest() -> int:
    failures: list[str] = []

    # --- _stable_sha256 matches the sims' own recipe ---
    body = {"b": 2, "a": 1}
    expect = hashlib.sha256(b'{"a":1,"b":2}').hexdigest()
    if _stable_sha256(body) != expect:
        failures.append("stable_sha256 recipe mismatch")

    # --- fragile-pin: self-pin INCLUDING generated_at, no envelope -> flagged ---
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        # case 1: fragile (incl generated_at, no envelope sibling)
        d1dir = tdp / "frag" / "results"
        d1dir.mkdir(parents=True)
        body1 = {"generated_at": "2026-01-01T00:00:00Z", "x": 1}
        body1["result_sha256"] = _stable_sha256(body1)
        f1 = d1dir / "frag_results.json"
        f1.write_text(json.dumps(body1), encoding="utf-8")
        # case 2: robust — same shape but an envelope re-pins it
        d2dir = tdp / "env" / "results"
        d2dir.mkdir(parents=True)
        body2 = {"generated_at": "2026-01-01T00:00:00Z", "x": 1}
        body2["result_sha256"] = _stable_sha256(body2)
        f2 = d2dir / "env_results.json"
        f2.write_text(json.dumps(body2), encoding="utf-8")
        (d2dir / "env_envelope_results.json").write_text("{}", encoding="utf-8")
        # case 3: robust — self-pin EXCLUDES generated_at
        d3dir = tdp / "robust" / "results"
        d3dir.mkdir(parents=True)
        base3 = {"generated_at": "2026-01-01T00:00:00Z", "x": 1}
        pin3 = _stable_sha256({k: v for k, v in base3.items() if k != "generated_at"})
        body3 = dict(base3, result_sha256=pin3)
        # the recipe used here excludes generated_at, so the stored pin will NOT
        # match the "exclude only self" recompute -> not adjudicated -> not flagged
        f3 = d3dir / "robust_results.json"
        f3.write_text(json.dumps(body3), encoding="utf-8")

        flagged = {f["result"].split("/")[-1] for f in detect_fragile_pins([f1, f2, f3])}
        if "frag_results.json" not in flagged:
            failures.append("fragile-pin: missed genuine fragile self-pin")
        if "env_results.json" in flagged:
            failures.append("fragile-pin: false-positive on envelope-repinned result")
        if "robust_results.json" in flagged:
            failures.append("fragile-pin: false-positive on timestamp-excluding pin")

    # --- drift normalization: timestamp/order/derived-sha differences are math-identical ---
    a = {"generated_at": "T1", "result_sha256": "x" * 64, "b": 2, "a": 1}
    b = {"a": 1, "b": 2, "generated_at": "T2", "result_sha256": "y" * 64}
    if _normalize_math_body(a) != _normalize_math_body(b):
        failures.append("drift-norm: timestamp/order/sha-only diff not seen as math-identical")
    c = {"generated_at": "T1", "a": 1, "b": 2}
    d = {"generated_at": "T2", "a": 1, "b": 3}  # real value change
    if _normalize_math_body(c) == _normalize_math_body(d):
        failures.append("drift-norm: real value change wrongly collapsed to identical")

    # --- hardcoded-pin regex ---
    txt = 'EXPECTED_G0_SHA256 = "' + "a" * 64 + '"\nEXPECTED_REGISTRY_BODY_SHA256: "' + "b" * 64 + '"\n'
    names = {m.group("name") for m in _EXPECTED_RE.finditer(txt)}
    if names != {"EXPECTED_G0_SHA256", "EXPECTED_REGISTRY_BODY_SHA256"}:
        failures.append(f"hardcoded-pin regex mismatch: {names}")

    if failures:
        print(json.dumps({"ok": False, "selftest": "FAIL", "failures": failures}, indent=2))
        return 1
    print(json.dumps({"ok": True, "selftest": "PASS"}, indent=2))
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="GATE 3 result-integrity / pin-drift detector")
    parser.add_argument("--selftest", action="store_true", help="run in-process deterministic self-check and exit")
    parser.add_argument("--json", action="store_true", help="emit full report JSON (default)")
    args = parser.parse_args(argv)

    if args.selftest:
        return selftest()

    out = run()
    print(json.dumps(out, indent=2, sort_keys=True))
    return 1 if out["violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
