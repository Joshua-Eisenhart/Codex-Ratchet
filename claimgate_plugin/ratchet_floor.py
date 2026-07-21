#!/usr/bin/env python3
"""
ratchet_floor — the enforceable core of "constraints only tighten."

The gap both inventories found: Lev DECLARES ratchet-forward (`c4_ratchet,
fail_closed`) but nothing compares a new value against a prior floor and rejects
weakening — `constrain` just appends. CR has the ratchet CONCEPT (MSS, forward-
only) but validates each receipt in isolation, so a later run silently reporting
a WORSE number is admitted. This gate is where CR's concept meets Lev's durable
log: a monotone floor per metric that a new claim may improve or equal, never weaken.

    ratchet_floor admit <receipt.json> [--store ratchet_floor.json]
        exit 0 = admitted (floors advanced or held)
        exit 1 = REJECTED (a claim weakens a floor, or flips a locked direction)
        exit 2 = usage / IO error
    ratchet_floor show [--store ...]

Receipt declares:
    "floor_claims": [
      {"key": "senses.occluded_accuracy", "value": 0.878, "direction": "higher_is_better"},
      {"key": "sim.max_abs_error",        "value": 1.4e-8, "direction": "lower_is_better"}
    ]

Rules (forward-only ratchet):
  - New key: admitted at its first value; direction LOCKED at first admission.
  - Existing key: direction must match the locked direction (else REJECT — tamper).
    higher_is_better: value >= floor to admit; < floor is a REGRESSION -> REJECT.
    lower_is_better:  value <= floor to admit; > floor is a REGRESSION -> REJECT.
  - Admission is atomic: if ANY claim regresses/tampers, NO floor moves.
  - The store + log are append-only and must live OUTSIDE the producing agent's
    write-control (branch-protected / Lev event log), same as the gate registry.

No third-party deps. Python 3.
"""
import json, os, sys, hashlib

EPS = 1e-12

def die(msg, code=2):
    sys.stderr.write(f"ratchet_floor: {msg}\n"); sys.exit(code)

def load(path, default):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)

def sha(path):
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]
    except Exception:
        return None

def weakens(direction, new, floor):
    if direction == "higher_is_better":
        return new < floor - EPS
    if direction == "lower_is_better":
        return new > floor + EPS
    return None  # unknown direction

def improves_or_holds_value(direction, new, floor):
    # the new floor after admitting: the better of the two (ratchet forward)
    if direction == "higher_is_better":
        return max(new, floor)
    return min(new, floor)

def admit(receipt_path, store_path):
    try:
        receipt = load(receipt_path, None)
    except Exception as e:
        die(f"bad receipt: {e}")
    if receipt is None:
        die(f"receipt not found: {receipt_path}")
    claims = receipt.get("floor_claims") or []
    store = load(store_path, {"floors": {}, "log": []})
    floors = store["floors"]

    decisions, violations = [], []
    for c in claims:
        key, val, direction = c.get("key"), c.get("value"), c.get("direction")
        if key is None or not isinstance(val, (int, float)) or direction not in ("higher_is_better", "lower_is_better"):
            violations.append({"key": key, "reason": "malformed floor_claim (need key, numeric value, direction)"})
            continue
        cur = floors.get(key)
        if cur is None:
            decisions.append({"key": key, "action": "new", "floor": val, "direction": direction})
        elif cur["direction"] != direction:
            violations.append({"key": key, "reason": f"direction '{direction}' != locked '{cur['direction']}' (direction tamper)"})
        elif weakens(direction, val, cur["value"]):
            violations.append({"key": key, "reason": f"REGRESSION: {val} weakens floor {cur['value']} ({direction})",
                               "floor": cur["value"], "claimed": val})
        else:
            newfloor = improves_or_holds_value(direction, val, cur["value"])
            decisions.append({"key": key, "action": "advance" if newfloor != cur["value"] else "hold",
                              "floor": newfloor, "from": cur["value"], "direction": direction})

    verdict = "REJECTED" if violations else "ADMITTED"
    report = {"tool": "ratchet_floor", "receipt": os.path.basename(receipt_path),
              "verdict": verdict, "violations": violations, "decisions": decisions}

    if not violations:
        # atomic apply: only touch the store when nothing regressed
        prov = {"receipt": os.path.abspath(receipt_path), "sha": sha(receipt_path)}
        for d in decisions:
            floors[d["key"]] = {"value": d["floor"], "direction": d["direction"], **prov}
        store["log"].append({"receipt": os.path.basename(receipt_path), "sha": prov["sha"],
                             "decisions": [{"key": d["key"], "action": d["action"], "floor": d["floor"]} for d in decisions]})
        with open(store_path, "w") as f:
            json.dump(store, f, indent=1)

    print(json.dumps(report, indent=1))
    sys.exit(1 if violations else 0)

def show(store_path):
    store = load(store_path, {"floors": {}, "log": []})
    print(json.dumps({"floors": store["floors"], "admissions": len(store["log"])}, indent=1))
    sys.exit(0)

def main():
    args = sys.argv[1:]
    if not args:
        die("usage: ratchet_floor admit <receipt.json> [--store f] | show [--store f]")
    store = args[args.index("--store") + 1] if "--store" in args else \
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "ratchet_floor.json")
    cmd = args[0]
    if cmd == "admit":
        rp = next((a for a in args[1:] if not a.startswith("--")), None)
        if not rp:
            die("usage: ratchet_floor admit <receipt.json>")
        admit(rp, store)
    elif cmd == "show":
        show(store)
    else:
        die(f"unknown command '{cmd}'")

if __name__ == "__main__":
    main()
