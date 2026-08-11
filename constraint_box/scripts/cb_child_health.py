#!/usr/bin/env python3
"""cb_child_health — the deterministic supervisor over council seats.

The owner: "child_health matters most — its verbs are kill, demote,
reroute, shrink, override, block_full, accept_with_reason."

This is NOT a council. It never calls a model and it never asks a model
for a verdict. It reads a wave receipt already produced by a script such
as cb_wave_decision.py (DECISION_RECEIPT.json — the shape every wave
receipt should follow; FOLLOWUP and FAILURE wave receipts are the same
councils/L3/gate shape once those waves exist) and walks its real,
already-recorded fields: seats, collapse, provider_diversity, gate,
structure, provenance, compilation. Each row below issues exactly one
verb, with a named, checkable reason drawn straight from those fields.
No model decides a verb; if a receipt does not carry the fields a check
needs, that check simply produces zero rows — it never guesses.

VERBS, SCOPE, and the field(s) each one is keyed off:

  kill                seat    seats[route][child][slice].ok == False
                               (dead on its final attempt, after the
                               runner's own internal retries)
                      council  every seat in a (route, child) council is
                               dead — live_seats == 0
  demote              seat    seat.ok == True but its answer is missing
                               (ok=true, empty text) or fails the shape
                               contract the prompt itself asked for
                               ("one sentence under 30 words")
  reroute             lane    L3.by_lane[lane]: 0 < live < called — some
                               seats on this lane survived, so the dead
                               ones are worth moving to another lane
                      council  0 < live_seats < MEMBER_FLOOR (imported
                               from cb_wave_decision) — under-populated
                               but not dead; move seats, don't kill it
  shrink              lane    L3.by_lane[lane]: called > 0 and live == 0
                               — fully dead this run, drop it from the
                               active lane pool
                      council  structure.members_per_child exceeds
                               MEMBER_CEILING (owner D1 ruling: "it
                               could be 2-6 llms/skills/formal agents")
  override            council  the route's gate admitted its compiled
                               output (gate[route].admitted == True) yet
                               a deterministic-role child (provenance
                               voice is None — guard.* / lane.* seats,
                               not an MMM voice persona) has live
                               answers sharing no substantive token with
                               that compilation — its verdict was not
                               honored
  block_full          council  collapse.verdict starts with "COLLAPSED"
                               — collapse_check already found the
                               council's members indistinguishable
  accept_with_reason  seat    seat.ok == True and its answer passes the
                               shape contract; the reason names the word
                               count that passed

  cb_child_health.py --dry-run                    # lists verbs+triggers, no receipt needed
  cb_child_health.py                               # runs over the newest DECISION_RECEIPT.json
  cb_child_health.py --receipt <path/to/RECEIPT.json>

promotion_allowed=false.
"""
from __future__ import annotations
import argparse, hashlib, json, sys, time
from pathlib import Path

REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SCRIPTS = REPO / "constraint_box" / "scripts"
RECEIPTS = REPO / "constraint_box" / "receipts"
sys.path.insert(0, str(SCRIPTS))
from cb_wave_decision import MEMBER_FLOOR   # reuse the conformance floor, don't refork it

MEMBER_CEILING = 6      # owner D1: "it could be 2-6 llms/skills/formal agents"
SHAPE_MAX_WORDS = 40    # the seat prompt itself asks for "one sentence under 30 words";
SHAPE_MIN_CHARS = 3     # give slack to 40 before calling it a contract failure

VERBS = ["kill", "demote", "reroute", "shrink", "override", "block_full",
         "accept_with_reason"]

DECLARED_OUTPUT_FIELDS = ("selected_move", "why_now", "operating_boundary",
                           "evidence_boundary", "falsifier")

TRIGGER_CATALOG = [
    {"verb": "kill", "scope": "seat",
     "trigger": "seat.ok == False on its final attempt — dead across every retry"},
    {"verb": "kill", "scope": "council",
     "trigger": "every seat in the (route, child) council is dead (live_seats == 0)"},
    {"verb": "demote", "scope": "seat",
     "trigger": "seat.ok == True but the answer is empty or fails the shape "
                f"contract ({SHAPE_MIN_CHARS}-{SHAPE_MAX_WORDS} words)"},
    {"verb": "reroute", "scope": "lane",
     "trigger": "L3.by_lane[lane]: 0 < live < called — partially recoverable"},
    {"verb": "reroute", "scope": "council",
     "trigger": f"0 < live_seats < MEMBER_FLOOR ({MEMBER_FLOOR}) — "
                "under-populated, not dead"},
    {"verb": "shrink", "scope": "lane",
     "trigger": "L3.by_lane[lane]: called > 0 and live == 0 — fully dead this run"},
    {"verb": "shrink", "scope": "council",
     "trigger": f"structure.members_per_child > MEMBER_CEILING ({MEMBER_CEILING})"},
    {"verb": "override", "scope": "council",
     "trigger": "gate[route].admitted == True but a deterministic-role child "
                "(provenance voice is None) has live answers sharing no "
                "substantive token with the compiled output"},
    {"verb": "block_full", "scope": "council",
     "trigger": "collapse.verdict starts with 'COLLAPSED'"},
    {"verb": "accept_with_reason", "scope": "seat",
     "trigger": "seat.ok == True and the answer passes the shape contract"},
]


# ------------------------------------------------------------------ helpers
def newest_decision_receipt() -> Path | None:
    cands = sorted(RECEIPTS.glob("decision_*/DECISION_RECEIPT.json"),
                    key=lambda p: p.stat().st_mtime)
    return cands[-1] if cands else None


def shape_ok(text: str) -> tuple[bool, str]:
    """The contract every seat prompt asked for: one sentence under 30 words."""
    t = text.strip()
    if len(t) < SHAPE_MIN_CHARS:
        return False, f"answer is under {SHAPE_MIN_CHARS} chars"
    words = t.split()
    if len(words) > SHAPE_MAX_WORDS:
        return False, f"{len(words)} words exceeds the shape ceiling of {SHAPE_MAX_WORDS}"
    return True, f"{len(words)} words, within the shape ceiling of {SHAPE_MAX_WORDS}"


# ------------------------------------------------------------------ per-scope passes
def seat_verbs(receipt: dict) -> list[dict]:
    """kill / demote / accept_with_reason — one row per (route, child, slice) seat."""
    out = []
    for route, children in receipt.get("councils", {}).items():
        for child, cdata in children.items():
            seats = cdata.get("seats", {})
            answers = cdata.get("answers", {})
            for slice_, seat in seats.items():
                sid = f"{route}|{child}|{slice_}"
                if not seat.get("ok"):
                    out.append({"scope": "seat", "id": sid, "verb": "kill", "reason":
                        f"seat returned ok=false on its final attempt "
                        f"(lane {seat.get('lane')}, error: "
                        f"{seat.get('error') or 'none recorded'})",
                        "evidence": {"lane": seat.get("lane"),
                                     "family": seat.get("family"),
                                     "error": seat.get("error", "")}})
                    continue
                text = answers.get(slice_, "")
                ok, why = shape_ok(text) if text else (False, "ok=true but text is empty")
                if ok:
                    out.append({"scope": "seat", "id": sid, "verb": "accept_with_reason",
                        "reason": f"seat passed the shape contract: {why}",
                        "evidence": {"lane": seat.get("lane"), "family": seat.get("family")}})
                else:
                    out.append({"scope": "seat", "id": sid, "verb": "demote", "reason":
                        f"seat responded (ok=true) but failed the shape contract: {why}",
                        "evidence": {"lane": seat.get("lane"), "family": seat.get("family"),
                                     "chars": len(text)}})
    return out


def lane_verbs(receipt: dict) -> list[dict]:
    """reroute / shrink — one row per lane in L3.by_lane."""
    out = []
    for lane, counts in receipt.get("L3", {}).get("by_lane", {}).items():
        called, live = counts.get("called", 0), counts.get("live", 0)
        if called == 0:
            continue
        if live == 0:
            out.append({"scope": "lane", "id": lane, "verb": "shrink", "reason":
                f"{live}/{called} seats live on this lane this run — fully dead, "
                f"drop it from the active lane pool",
                "evidence": {"called": called, "live": live}})
        elif live < called:
            out.append({"scope": "lane", "id": lane, "verb": "reroute", "reason":
                f"{live}/{called} seats live — partially recoverable, reassign its "
                f"dead seats to another lane on the next dispatch",
                "evidence": {"called": called, "live": live}})
    return out


def council_verbs(receipt: dict) -> list[dict]:
    """kill / reroute / shrink / block_full / override — one row per (route, child)."""
    out = []
    councils = receipt.get("councils", {})
    gate = receipt.get("gate", {})
    provenance = receipt.get("provenance", {})
    members_per_child = receipt.get("structure", {}).get("members_per_child", 0)
    compilation = receipt.get("compilation", {})

    for route, children in councils.items():
        route_admitted = gate.get(route, {}).get("admitted", False)
        comp = compilation.get(route) or {}
        comp_tokens = {w for f in DECLARED_OUTPUT_FIELDS
                       for w in str(comp.get(f, "")).lower().split() if len(w) > 6}

        for child, cdata in children.items():
            cid = f"{route}|{child}"
            seats = cdata.get("seats", {})
            live_seats = sum(1 for s in seats.values() if s.get("ok"))

            if seats and live_seats == 0:
                out.append({"scope": "council", "id": cid, "verb": "kill", "reason":
                    "every seat in this council is dead — it returned nothing "
                    "across every retry",
                    "evidence": {"live_seats": 0, "seats_called": len(seats)}})
            elif 0 < live_seats < MEMBER_FLOOR:
                out.append({"scope": "council", "id": cid, "verb": "reroute", "reason":
                    f"{live_seats} live seats is below the conformance floor of "
                    f"{MEMBER_FLOOR} — reroute its dead seats onto live lanes to "
                    f"restore the floor before re-gating",
                    "evidence": {"live_seats": live_seats, "floor": MEMBER_FLOOR}})

            if members_per_child > MEMBER_CEILING:
                out.append({"scope": "council", "id": cid, "verb": "shrink", "reason":
                    f"{members_per_child} members exceeds the council member "
                    f"ceiling of {MEMBER_CEILING} (owner D1: \"2-6 llms/skills/"
                    f"formal agents\")",
                    "evidence": {"members_per_child": members_per_child,
                                 "ceiling": MEMBER_CEILING}})

            collapse = cdata.get("collapse", {})
            verdict = collapse.get("verdict", "")
            if verdict.startswith("COLLAPSED"):
                out.append({"scope": "council", "id": cid, "verb": "block_full",
                    "reason": f"collapse_check verdict is '{verdict}' — members "
                              f"indistinguishable, block the full council output",
                    "evidence": collapse})

            voice = provenance.get(f"{route}/{child}", {}).get("voice")
            if voice is None:
                answers = cdata.get("answers", {})
                live_tokens = {w for a in answers.values()
                               for w in " ".join(a.split()).lower().split()
                               if len(w) > 6}
                if live_tokens and route_admitted and not (live_tokens & comp_tokens):
                    out.append({"scope": "council", "id": cid, "verb": "override",
                        "reason": "route admitted its compilation but shares no "
                                  "substantive token with this deterministic-role "
                                  "child's live answers — its verdict was not "
                                  "honored by the compilation",
                        "evidence": {"route_admitted": route_admitted,
                                     "child_live_tokens": len(live_tokens)}})
    return out


def build_verbs(receipt: dict) -> list[dict]:
    return seat_verbs(receipt) + lane_verbs(receipt) + council_verbs(receipt)


# ------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipt", default="",
                    help="path to a wave receipt JSON; defaults to the newest "
                         "decision_*/DECISION_RECEIPT.json under constraint_box/receipts/")
    ap.add_argument("--dry-run", action="store_true",
                    help="list the verbs and their triggers WITHOUT needing a receipt")
    a = ap.parse_args()
    t0 = time.time()

    if a.dry_run:
        print("child_health — DRY RUN, no receipt read\n")
        print(f"{'verb':<20}{'scope':<10}trigger")
        for row in TRIGGER_CATALOG:
            print(f"{row['verb']:<20}{row['scope']:<10}{row['trigger']}")
        print(f"\n{len(TRIGGER_CATALOG)} triggers defined across {len(VERBS)} verbs: "
              f"{VERBS}")
        print(f"MEMBER_FLOOR={MEMBER_FLOOR} (imported from cb_wave_decision)  "
              f"MEMBER_CEILING={MEMBER_CEILING}  "
              f"SHAPE={SHAPE_MIN_CHARS}-{SHAPE_MAX_WORDS} words")
        return 0

    rpath = Path(a.receipt) if a.receipt else newest_decision_receipt()
    if rpath is None or not rpath.is_file():
        print(f"REFUSED: no receipt found "
              f"({'given path missing: ' + str(rpath) if a.receipt else 'no decision_*/DECISION_RECEIPT.json under ' + str(RECEIPTS)})")
        return 2

    receipt = json.loads(rpath.read_text())
    verbs = build_verbs(receipt)

    print(f"child_health over {rpath}")
    print(f"source schema: {receipt.get('schema', '<none>')}\n")

    by_scope: dict[str, list[dict]] = {}
    for v in verbs:
        by_scope.setdefault(v["scope"], []).append(v)
    for scope in ("seat", "lane", "council"):
        rows = by_scope.get(scope, [])
        print(f"{scope.upper()}  ({len(rows)} rows)")
        for v in rows:
            print(f"   {v['verb']:<18}{v['id']:<52}{v['reason'][:90]}")
        print()

    tally = {verb: 0 for verb in VERBS}
    for v in verbs:
        tally[v["verb"]] += 1
    print("VERB TALLY")
    for verb in VERBS:
        print(f"   {verb:<20}{tally[verb]}")

    # Second-resolution timestamps collide: two runs in the same second wrote the
    # same path and the later one silently replaced the earlier. A receipt that can
    # be overwritten without trace is not a receipt.
    stamp = time.strftime("%Y%m%dT%H%M%SZ")
    tag = hashlib.sha256(str(rpath).encode()).hexdigest()[:8]
    out_dir = RECEIPTS / f"child_health_{stamp}_{tag}"
    n = 1
    while out_dir.exists():
        n += 1
        out_dir = RECEIPTS / f"child_health_{stamp}_{tag}_{n}"
    out_dir.mkdir(parents=True)
    (out_dir / "CHILD_HEALTH_RECEIPT.json").write_text(json.dumps({
        "schema": "cb.child-health.v1",
        "source_receipt": str(rpath),
        "source_schema": receipt.get("schema"),
        "verbs": verbs,
        "tally": tally,
        "constants": {"MEMBER_FLOOR": MEMBER_FLOOR, "MEMBER_CEILING": MEMBER_CEILING,
                      "SHAPE_MIN_CHARS": SHAPE_MIN_CHARS, "SHAPE_MAX_WORDS": SHAPE_MAX_WORDS},
        "wall_seconds": round(time.time() - t0, 1),
        "promotion_allowed": False,
        "claim_ceiling": "deterministic verb issuance over one already-produced wave "
                         "receipt's seats, lanes and councils; child_health does not "
                         "judge whether any council's answer was correct, only whether "
                         "it arrived in a checkable shape and a live seat produced it"},
        indent=1, sort_keys=True))
    print(f"\nRECEIPT {out_dir.name}/CHILD_HEALTH_RECEIPT.json ({time.time()-t0:.1f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
