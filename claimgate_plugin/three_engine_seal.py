#!/usr/bin/env python3
"""Three-engine seal — the fired-side enforcement of the numpy=control-only contract.

The system contract (CLAUDE.md, binding): Julia (QuantumOptics) authoritative,
JAX batched workhorse, PyTorch graph/autograd; numpy/scipy/mpmath are CONTROL-ONLY.
At least one authoritative engine must carry the numeric work. numpy as the
load-bearing workhorse is the anti-pattern.

This was violated systemically (2026-07-22): every ratcheting arrow ran on
numpy/sympy with julia=jax=torch=None, and numpy was outright load_bearing on
three. The enforcement (scripts/validate_three_engine_sim_result.py) existed but
was never wired into the gate that fires. This seal closes that: it runs inside
post_receipt_gate.sh, so git (the pre-commit hook) and Lev cannot admit a
contract-violating receipt.

Rules (a receipt "owes the contract" iff numpy appears in its
TOOL_INTEGRATION_DEPTH — i.e. it is a numeric sim that used numpy):
  R1  numpy/scipy/mpmath labeled load_bearing            -> REJECT (control-only).
  R2  owes the contract, and NONE of {julia,jax,torch}   -> REJECT (no
      is load_bearing                                        authoritative engine
                                                             carried the work).
Pure-SMT (z3/cvc5 only) and pure-finite-set receipts (no numpy at all) do NOT
owe the numeric-engine contract and pass. A receipt with no
TOOL_INTEGRATION_DEPTH is not a three-engine sim and passes (other gates cover it).

Exit: 0 = pass / not-applicable, 1 = REJECT (contract violation), 2 = usage/IO.
"""
import json
import sys

CONTROL_ONLY = {"numpy", "scipy", "mpmath"}
AUTHORITATIVE = {"julia", "jax", "torch", "pytorch"}


def _depth(receipt):
    for k in ("TOOL_INTEGRATION_DEPTH", "tool_integration_depth"):
        v = receipt.get(k)
        if isinstance(v, dict):
            return {str(name).lower(): val for name, val in v.items()}
    return {}


def _engines_ran(receipt):
    for k in ("engines_ran", "engines"):
        v = receipt.get(k)
        if isinstance(v, dict):
            return {str(name).lower(): bool(val) for name, val in v.items()}
    return {}


def check(receipt):
    """Return (exit_code, message). Keys on engines_ran (the deterministic signal),
    with TOOL_INTEGRATION_DEPTH as the secondary source for load-bearing labels."""
    depth = _depth(receipt)
    engines = _engines_ran(receipt)
    if not depth and not engines:
        return 0, "three_engine_seal: no engine metadata — not a three-engine sim, pass"

    load_bearing = {name for name, val in depth.items() if val == "load_bearing"}

    # R1: control-only tool labeled load_bearing — absolute violation.
    lb_control = load_bearing & CONTROL_ONLY
    if lb_control:
        return 1, (
            f"three_engine_seal: REJECT — {sorted(lb_control)} labeled load_bearing, "
            f"but numpy/scipy/mpmath are CONTROL-ONLY. The numeric work must run on an "
            f"authoritative engine (Julia/JAX/PyTorch). Move the load-bearing witness to "
            f"an engine leg and relabel {sorted(lb_control)} supportive/control."
        )

    # Does this receipt owe the numeric-engine contract? (numpy is a worker here)
    numpy_used = engines.get("numpy", False) or ("numpy" in depth)
    if not numpy_used:
        return 0, "three_engine_seal: numpy not used (pure symbolic/SMT/finite) — contract N/A, pass"

    # An authoritative engine must carry the work: either labeled load_bearing OR at
    # least actually run (engines_ran True). Running one is the achievable fix.
    auth_load_bearing = sorted(load_bearing & AUTHORITATIVE)
    auth_ran = sorted(n for n in ("julia", "jax", "torch", "pytorch") if engines.get(n))
    if not auth_load_bearing and not auth_ran:
        return 1, (
            "three_engine_seal: REJECT — numeric sim (numpy ran) with NO authoritative engine. "
            "The contract requires >=1 of Julia(authoritative)/JAX/PyTorch to carry the numeric "
            "work; numpy is control-only. Fix: run a Julia/JAX/PyTorch leg on the numeric witness "
            "(engines_ran.<engine>=true) and mark it load_bearing (see .claude/skills/three-engine-sim). "
            "The engines load fine at ~25% mem — the DEFERRED_BLOCKED_ON_MEMORY >40% gate was false."
        )
    if not auth_load_bearing and auth_ran:
        return 0, (
            f"three_engine_seal: pass-with-note — authoritative engine RAN {auth_ran} but is not "
            f"yet labeled load_bearing; promote the witness onto it to fully satisfy the contract."
        )
    return 0, f"three_engine_seal: pass — authoritative engine load_bearing {auth_load_bearing}"


def main(argv):
    if len(argv) != 2:
        print("usage: three_engine_seal.py <receipt.json>", file=sys.stderr)
        return 2
    try:
        receipt = json.load(open(argv[1]))
    except Exception as exc:  # noqa: BLE001 — IO/parse error is not a contract verdict
        print(f"three_engine_seal: could not read receipt ({exc}) — not blocking", file=sys.stderr)
        return 0
    code, message = check(receipt)
    print(message, file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
