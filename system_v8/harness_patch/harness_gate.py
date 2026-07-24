#!/usr/bin/env python3
"""ClaimGate at the HARNESS level — one gate, every adapter.

Speaks Lev's abstract-hooks lifecycle events, so the same policy covers
claude-code / cursor / openclaw / codex / pi / grok instead of one hook file
per vendor. Emits an events.jsonl line + a receipt, which are exactly what
`lev triggers dispatch <events.jsonl> --receipt <receipt.json>` consumes
(verified CLI contract, not invented).

Usage
  harness_gate.py mint  --claim "<sentence>" --ceiling "<ceiling>" --tools Bash,Write --roots .
  harness_gate.py pre   --tool Bash --path system_v8/x.py
  harness_gate.py post  --receipt <path.json>

Exit codes: 0 sealed/admitted | 3 pending or parked | 1 blocked.
Nonzero is infrastructure/policy, never a scientific verdict.

Enforcement level E2 (supervised execution). It may say "admission control".
It may never say "bypass prevented" — the model still holds a shell.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE = HERE / "results" / "run_ticket.json"
EVENTS = HERE / "results" / "events.jsonl"
PROTECTED_ROOTS = [Path.home() / "lev-main"]
SELF_VERDICT_FIELDS = ["pass", "all_pass", "approved", "promotion_allowed", "solved", "certified"]


def _emit(event: str, payload: dict) -> None:
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    with EVENTS.open("a") as f:
        f.write(json.dumps({"schema": "abstract-hooks@1.0.0",
                            "event": event, "payload": payload}) + "\n")


def _digest(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16] if p.exists() else "absent"


# ----------------------------------------------------------------- task_start
def mint(a) -> int:
    ticket = {
        "ticket_id": "tkt_" + secrets.token_hex(6),
        # nonce generated HERE (the broker), not by the candidate process.
        # A nonce the worker can author is decorative.
        "nonce": secrets.token_hex(16),
        "claim_sentence": a.claim,
        "claim_ceiling": a.ceiling,
        "allowed_tools": [t.strip() for t in a.tools.split(",") if t.strip()],
        "allowed_write_roots": [str(Path(r).resolve()) for r in a.roots.split(",")],
        "policy_digest": _digest(HERE / "gate_policy.yaml"),
        "enforcement_level": "E2_SUPERVISED_EXECUTION",
        "immutable": True,
    }
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(ticket, indent=1))
    _emit("task_start", {"ticket_id": ticket["ticket_id"], "claim": a.claim})
    print(json.dumps({"verdict": "TICKET_MINTED", "ticket_id": ticket["ticket_id"]}))
    return 0


# -------------------------------------------------------------- pre_tool_use
def pre(a) -> int:
    if not STATE.exists():
        return _pre_out("PENDING_EVIDENCE", "no run ticket; mint one at task_start", a)
    t = json.loads(STATE.read_text())

    if a.tool not in t["allowed_tools"]:
        return _pre_out("BLOCKED_INVALID", f"tool {a.tool!r} outside ticket scope", a)

    if a.path:
        # canonicalize FIRST: resolves .., symlinks, case variants
        target = Path(os.path.expanduser(a.path)).resolve()
        for prot in PROTECTED_ROOTS:
            pr = prot.resolve()
            if target == pr or pr in target.parents:
                return _pre_out("BLOCKED_INVALID",
                                f"write into protected root {pr} (resolved from {a.path!r})", a)
        if not any(target == Path(r) or Path(r) in target.parents
                   for r in t["allowed_write_roots"]):
            return _pre_out("BLOCKED_INVALID", f"{target} outside allowed write roots", a)

    return _pre_out("ROUTE_SEALED", "within ticket scope", a)


def _pre_out(verdict: str, reason: str, a) -> int:
    _emit("pre_tool_use", {"tool": a.tool, "path": a.path, "verdict": verdict, "reason": reason})
    # NOTE: never emits PASS. ROUTE_SEALED means "eligible to run", not "admitted".
    print(json.dumps({"verdict": verdict, "reason": reason,
                      "note": "route seal only; not a scientific verdict"}))
    return {"ROUTE_SEALED": 0, "PENDING_EVIDENCE": 3, "PARKED_POLICY": 3}.get(verdict, 1)


# ------------------------------------------------------------- post_tool_use
def _strict_load(raw: bytes):
    """Parse ONCE from raw bytes: reject duplicate keys and non-finite numbers
    BEFORE object construction. Ordinary json.loads silently last-wins a
    duplicate key, which is how {"all_pass":false,"all_pass":true} gets in."""
    def no_dupes(pairs):
        seen = set()
        for k, _ in pairs:
            if k in seen:
                raise ValueError(f"duplicate key {k!r} rejected at raw parse")
            seen.add(k)
        return dict(pairs)

    def no_nonfinite(x):
        raise ValueError(f"non-finite number {x!r} rejected at raw parse")

    return json.loads(raw.decode("utf-8"), object_pairs_hook=no_dupes,
                      parse_constant=no_nonfinite)


def post(a) -> int:
    p = Path(a.receipt)
    if not p.exists():
        return _post_out("BLOCKED", f"required artifact absent: {p} (missing is not N/A-ok)", a)
    raw = p.read_bytes()
    raw_digest = hashlib.sha256(raw).hexdigest()[:16]     # hashed BEFORE canonicalization
    try:
        r = _strict_load(raw)
    except ValueError as e:
        return _post_out("BLOCKED", f"strict intake: {e}", a)

    present = [f for f in SELF_VERDICT_FIELDS if f in r]
    if any(r.get(f) is True for f in present):
        return _post_out("BLOCKED",
                         f"producer self-verdict asserted true: {present}; the gate computes its own state", a)

    if not r.get("classification"):
        return _post_out("PENDING_EXTERNAL_CHECK", "no classification field", a)

    return _post_out("ADMITTED_WITHIN_CEILING",
                     f"envelope sound; raw_digest={raw_digest}; ceiling={r.get('claim_ceiling', 'unstated')}", a)


def _post_out(verdict: str, reason: str, a) -> int:
    _emit("validation_pass" if verdict.startswith("ADMITTED") else "validation_fail",
          {"receipt": a.receipt, "verdict": verdict, "reason": reason})
    print(json.dumps({"verdict": verdict, "reason": reason,
                      "final": False,
                      "note": "CR-side admission only. Lev decides. "
                              "live_lev_consumed=false is evidence-import, not host execution."}))
    return {"ADMITTED_WITHIN_CEILING": 0}.get(verdict, 3 if "PENDING" in verdict or "PARKED" in verdict else 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("mint"); m.add_argument("--claim", required=True)
    m.add_argument("--ceiling", default="unstated"); m.add_argument("--tools", default="Bash")
    m.add_argument("--roots", default="."); m.set_defaults(fn=mint)
    q = sub.add_parser("pre"); q.add_argument("--tool", required=True)
    q.add_argument("--path", default=None); q.set_defaults(fn=pre)
    s = sub.add_parser("post"); s.add_argument("--receipt", required=True); s.set_defaults(fn=post)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
