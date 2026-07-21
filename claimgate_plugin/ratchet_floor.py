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
        exit 3 = PARKED (unknown keys without --allow-new-keys)
        exit 2 = usage / IO error
    ratchet_floor show [--store ...]

Receipt declares:
    "floor_claims": [
      {"key": "senses.occluded_accuracy", "value": 0.878, "direction": "higher_is_better"},
      {"key": "sim.max_abs_error",        "value": 1.4e-8, "direction": "lower_is_better"}
    ]

Rules (forward-only ratchet):
  - New key: parked unless --allow-new-keys is supplied; then admitted at its first value.
  - Existing key: direction must match the locked direction (else REJECT — tamper).
    higher_is_better: value >= floor to admit; < floor is a REGRESSION -> REJECT.
    lower_is_better:  value <= floor to admit; > floor is a REGRESSION -> REJECT.
  - Admission is atomic: if ANY claim regresses/tampers, NO floor moves.
  - The store + log are append-only and must live OUTSIDE the producing agent's
    write-control (branch-protected / Lev event log), same as the gate registry.

No third-party deps. Python 3.

TRUST_ROOT_BOUNDARY: the store must live on a path the producing agent cannot
write (branch-protected / harness-owned) to be a real trust root. This hash
chain makes tampering detectable after the fact; it cannot prevent a
from-scratch rewrite by whoever can write the store file.
"""
import json, os, sys, hashlib, math

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

def entry_digest(entry):
    payload = {k: v for k, v in entry.items() if k != "prev_entry_sha256"}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

def verify_chain(store):
    for index, entry in enumerate(store.get("log", [])):
        expected = "GENESIS" if index == 0 else entry_digest(store["log"][index - 1])
        if entry.get("prev_entry_sha256") != expected:
            return {"index": index, "expected": expected, "found": entry.get("prev_entry_sha256")}
    return None

def token_similarity(left, right):
    import re
    a = set(t for t in re.split(r"[^a-z0-9]+", left.lower()) if t)
    b = set(t for t in re.split(r"[^a-z0-9]+", right.lower()) if t)
    return len(a & b) / len(a | b) if a | b else 0.0

def nearest_key(key, floors):
    best_key, best_score = None, 0.0
    for existing in floors:
        score = token_similarity(key, existing)
        if score > best_score:
            best_key, best_score = existing, score
    # Rename hints use a conservative normalized-token Jaccard threshold of 0.5.
    return (best_key, best_score) if best_score >= 0.5 else (None, None)

def admit(receipt_path, store_path, allow_new_keys=False):
    try:
        receipt = load(receipt_path, None)
    except Exception as e:
        die(f"bad receipt: {e}")
    if receipt is None:
        die(f"receipt not found: {receipt_path}")
    claims = receipt.get("floor_claims") or []
    store = load(store_path, {"floors": {}, "log": []})
    floors = store["floors"]
    broken = verify_chain(store)
    if broken:
        print(json.dumps({"tool": "ratchet_floor", "receipt": os.path.basename(receipt_path),
                          "verdict": "CHAIN_BROKEN", "chain": broken}, indent=1))
        sys.exit(1)

    decisions, violations, parked = [], [], []
    for c in claims:
        key, val, direction = c.get("key"), c.get("value"), c.get("direction")
        if key is None or not isinstance(val, (int, float)) or isinstance(val, bool) or direction not in ("higher_is_better", "lower_is_better"):
            violations.append({"key": key, "reason": "malformed floor_claim (need key, numeric value, direction)"})
            continue
        if not math.isfinite(val):
            # NaN/Inf poison the floor: NaN comparisons are always False (never
            # "weakens") so a NaN would be admitted and then max/min-poison the key.
            violations.append({"key": key, "reason": f"non-finite value {val} forbidden"})
            continue
        cur = floors.get(key)
        if cur is None:
            if allow_new_keys:
                decisions.append({"key": key, "action": "new", "floor": val, "direction": direction})
            else:
                nearest, similarity = nearest_key(key, floors)
                parked.append({"key": key, "reason": "unknown floor key; pass --allow-new-keys to admit",
                               "nearest_existing_key": nearest, "similarity": similarity})
        elif cur["direction"] != direction:
            violations.append({"key": key, "reason": f"direction '{direction}' != locked '{cur['direction']}' (direction tamper)"})
        elif weakens(direction, val, cur["value"]):
            violations.append({"key": key, "reason": f"REGRESSION: {val} weakens floor {cur['value']} ({direction})",
                               "floor": cur["value"], "claimed": val})
        else:
            newfloor = improves_or_holds_value(direction, val, cur["value"])
            decisions.append({"key": key, "action": "advance" if newfloor != cur["value"] else "hold",
                              "floor": newfloor, "from": cur["value"], "direction": direction})

    verdict = "REJECTED" if violations else ("PARKED" if parked else "ADMITTED")
    report = {"tool": "ratchet_floor", "receipt": os.path.basename(receipt_path),
              "verdict": verdict, "violations": violations, "parked": parked,
              "threshold": 0.5, "decisions": decisions}

    if not violations and not parked:
        # atomic apply: only touch the store when nothing regressed
        prov = {"receipt": os.path.abspath(receipt_path), "sha": sha(receipt_path)}
        for d in decisions:
            floors[d["key"]] = {"value": d["floor"], "direction": d["direction"], **prov}
        entry = {"receipt": os.path.basename(receipt_path), "sha": prov["sha"],
                 "decisions": [{"key": d["key"], "action": d["action"], "floor": d["floor"]} for d in decisions]}
        entry["prev_entry_sha256"] = "GENESIS" if not store["log"] else entry_digest(store["log"][-1])
        store["log"].append(entry)
        with open(store_path, "w") as f:
            json.dump(store, f, indent=1)

    print(json.dumps(report, indent=1))
    sys.exit(1 if violations else (3 if parked else 0))

def verify(store_path):
    store = load(store_path, {"floors": {}, "log": []})
    broken = verify_chain(store)
    if broken:
        print(json.dumps({"tool": "ratchet_floor", "verdict": "CHAIN_BROKEN", "chain": broken}, indent=1))
        sys.exit(1)
    print(json.dumps({"tool": "ratchet_floor", "verdict": "CHAIN_VALID", "entries": len(store.get("log", []))}, indent=1))
    sys.exit(0)

def show(store_path):
    store = load(store_path, {"floors": {}, "log": []})
    print(json.dumps({"floors": store["floors"], "admissions": len(store["log"])}, indent=1))
    sys.exit(0)

def main():
    args = sys.argv[1:]
    if not args:
        die("usage: ratchet_floor admit <receipt.json> [--store f] [--allow-new-keys] | show [--store f] | verify [--store f]")
    store = args[args.index("--store") + 1] if "--store" in args else \
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "ratchet_floor.json")
    cmd = args[0]
    if cmd == "admit":
        rp = next((a for a in args[1:] if not a.startswith("--")), None)
        if not rp:
            die("usage: ratchet_floor admit <receipt.json>")
        admit(rp, store, "--allow-new-keys" in args)
    elif cmd == "show":
        show(store)
    elif cmd == "verify":
        verify(store)
    else:
        die(f"unknown command '{cmd}'")

if __name__ == "__main__":
    main()
