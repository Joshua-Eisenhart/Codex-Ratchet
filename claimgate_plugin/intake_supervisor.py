#!/usr/bin/env python3
"""INTAKE SUPERVISOR — the strict parse boundary, fired FIRST in the gate chain.

Closes the three standing hostile GAPs by refusing poisoned bytes BEFORE any
downstream checker can normalize them into a convenient claim:

  duplicate_json_key  ordinary json.loads silently last-wins, so
                      {"all_pass":false,"all_pass":true} becomes true before any
                      validator sees it. Detected at raw parse, every depth.
  nan_values          bare NaN/Infinity literals AND the valid-JSON encodings
                      ("NaN" string, null) inside numeric evidence arrays. The
                      old chain recomputed "mean matches (NaN)" and passed.
  renamed_metric      a locked floor metric that vanished via rename (acc -> acc_v2)
                      must not silently satisfy the floor. Exact registry IDs only;
                      similarity may FLAG but can never SATISFY a locked demand.

Exit: 0 clean | 1 REJECT | 3 PARK | 2 usage.
Nonzero is a policy/infrastructure disposition, never a scientific verdict.

Env: RF_STORE=<floor store json>  (optional; enables the locked-floor check)
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

NONFINITE_TOKENS = {"nan", "inf", "-inf", "+inf", "infinity", "-infinity", "+infinity"}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def strict_parse(raw: bytes):
    """Parse once from raw bytes. Duplicate keys and bare non-finite literals
    are rejected here, before any object exists to normalize."""
    def no_dupes(pairs):
        seen = set()
        for k, _ in pairs:
            if k in seen:
                raise ValueError(f"duplicate key {k!r} at raw parse "
                                 f"(last-wins would have silently chosen one value)")
            seen.add(k)
        return dict(pairs)

    def no_constant(x):
        raise ValueError(f"bare non-finite literal {x!r} at raw parse")

    return json.loads(raw.decode("utf-8"), object_pairs_hook=no_dupes,
                      parse_constant=no_constant)


def poisoned_numeric_arrays(obj, path=""):
    """A numeric evidence array carrying null or a non-finite STRING is poisoned:
    valid JSON, but any recompute over it produces NaN and 'matches'."""
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            hits += poisoned_numeric_arrays(v, f"{path}.{k}")
    elif isinstance(obj, list):
        has_num = any(isinstance(x, (int, float)) and not isinstance(x, bool) for x in obj)
        bad = [x for x in obj
               if x is None or (isinstance(x, str) and x.strip().lower() in NONFINITE_TOKENS)]
        # all-null arrays count too: a recompute over them yields NaN/0 and "matches"
        if bad and (has_num or all(x is None for x in obj)):
            hits.append((path or "<root>", bad[:4], len(obj)))
        for i, v in enumerate(obj):
            hits += poisoned_numeric_arrays(v, f"{path}[{i}]")
    return hits


def all_keys(obj, out=None):
    out = set() if out is None else out
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.add(k)
            all_keys(v, out)
    elif isinstance(obj, list):
        for v in obj:
            all_keys(v, out)
    return out


def locked_floor_check(receipt):
    """Every locked floor metric must be present under its EXACT registered id.
    A near-name is a rename signal, not a substitute."""
    store_path = os.environ.get("RF_STORE")
    if not store_path or not Path(store_path).exists():
        return None
    try:
        floors = json.loads(Path(store_path).read_bytes()).get("floors") or {}
    except Exception:
        return None
    if not floors:
        return None

    keys = all_keys(receipt)
    normed = {_norm(k): k for k in keys}
    for locked in floors:
        if locked in keys:
            continue
        ln = _norm(locked)
        near = [orig for n, orig in normed.items()
                if n != ln and (n.startswith(ln) or ln.startswith(n)) and abs(len(n) - len(ln)) <= 6]
        if near:
            return (1, f"locked floor metric {locked!r} absent; near-name(s) {near} present "
                       f"— a renamed key cannot satisfy a locked demand")
        return (3, f"locked floor metric {locked!r} absent from receipt "
                   f"(missing required metric is PENDING, never satisfied)")
    return None


def main(argv):
    if len(argv) != 2:
        print("usage: intake_supervisor.py <receipt.json>", file=sys.stderr)
        return 2
    p = Path(argv[1])
    if not p.exists():
        print(f"intake_supervisor: REJECT — required artifact absent: {p} "
              f"(a missing artifact is BLOCKED_MISSING, never N/A-ok)", file=sys.stderr)
        return 1

    raw = p.read_bytes()
    try:
        receipt = strict_parse(raw)
    except ValueError as e:
        print(f"intake_supervisor: REJECT — {e}", file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001
        print(f"intake_supervisor: REJECT — unparseable ({e}); failing CLOSED", file=sys.stderr)
        return 1

    if not isinstance(receipt, dict):
        return 0

    hits = poisoned_numeric_arrays(receipt)
    if hits:
        where = "; ".join(f"{pth} contains {bad} (len {n})" for pth, bad, n in hits[:3])
        print(f"intake_supervisor: REJECT — non-finite/null poisoning numeric evidence: {where}. "
              f"A recompute over these 'matches' because NaN propagates.", file=sys.stderr)
        return 1

    floor = locked_floor_check(receipt)
    if floor:
        code, msg = floor
        label = "REJECT" if code == 1 else "PARK"
        print(f"intake_supervisor: {label} — {msg}", file=sys.stderr)
        return code

    print("intake_supervisor: pass — raw bytes clean "
          "(no duplicate keys, no non-finite evidence, locked floors intact)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
