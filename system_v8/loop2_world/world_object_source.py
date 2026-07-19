#!/usr/bin/env python3
"""
world_object_source.py -- WORLD ENGINE object source (lane: world_source).

Card authority: system_v8/spinor_jepa/TOURNAMENT_CARD_v0.md incl AMENDMENT v0.1
(occluded-object perception task: world-engine-generated objects with hidden
state; predict masked probe outcomes + maintain belief under occlusion).

Seam authority (read-only, honored as closely as its schema allows):
  lev-main/plugins/sim-eval/evals/cr_cross_engine_parity/receipts/
    world-engine-seam-events.jsonl
  lev-main/core/eval/src/world-engine-seam-receipt.test.ts
Seam event shape mirrored here (the stored JsonlEventStore line shape):
  {id, timestamp, type: "graph.operations_applied", source_entity,
   payload: {operations: [{type: "upsert_entity", timestamp, source,
     entity_id, payload: <entity with claims=[assertion triples], links>}],
     event_id},
   correlation_id, schema_version: 1}
Each claim: {id, kind:"assertion", subject, predicate, object, truth_state,
             evidence_refs, valid_at, created_at}.

Objects: hidden state = (latent 8-bit word w0, dynamical rule r) where r is
drawn from a 4-member family of additive (XOR) cellular automata on 8 cells
with periodic boundary -- the classical linear fragment of the QCA family
(translation-invariant, local, reversibility not asserted). Hidden fields
are WITHHELD from every emitted event.

Views: at each time t the world renders a partial view -- a probe stream
over the 8 bit positions where 2-4 positions are occluded; the occlusion
pattern varies across views. Occluded probes emit outcome "withheld".

Checks (frozen in this file; gates are code; each can fail):
  C1 hidden_state_genuine   -- no single view determines the object
                               (exhaustive consistency count over all 1024
                               candidate hidden states; min count >= 2)
  C2 joint_identifiability  -- all views jointly determine the object up to
                               full-trajectory probe-equivalence class
                               (consistent set == equivalence class, all objs)
  C3 schema_valid           -- every emitted event validates against the
                               declared schema; two negative-control bad
                               events are REJECTED; no hidden-field leak
  C4 dynamics_off_differs   -- a control world with dynamics OFF (frozen
                               word) yields a measurably different view
                               statistic (bit flip-rate on jointly visible
                               positions; |on - off| > 0.05)

promotion_allowed: false. Ceiling: working_sim. Honest negatives kept.
Refuses to reuse an existing outdir.
"""

import json
import os
import random
import sys

# ----------------------------------------------------------------------------
# Frozen parameters (deterministic)
# ----------------------------------------------------------------------------
SEED = 20260719
N_BITS = 8
N_OBJECTS = 64
N_VIEWS = 6                      # times t = 0..5, one view per time
OCCLUDE_MIN, OCCLUDE_MAX = 2, 4  # occluded bits per view
FLIP_RATE_THRESHOLD = 0.05       # C4 threshold, frozen
BASE_TIME = "2026-07-19T00:00:00"
SOURCE = "system_v8/loop2_world/world_object_source"
VIA = "world-object-source-v0"

# QCA-family (classical additive/XOR fragment): rule = tap offsets, periodic.
RULE_FAMILY = {
    0: (-1, 1),      # ECA 90-like
    1: (-1, 0, 1),   # ECA 150-like
    2: (0, 1),       # ECA 102-like
    3: (-1, 0),      # ECA 60-like
}
N_RULES = len(RULE_FAMILY)
HIDDEN_SPACE = [(w, r) for w in range(2 ** N_BITS) for r in range(N_RULES)]

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "results", "world_source")

# ----------------------------------------------------------------------------
# Declared event schema (C3 validates emitted lines against THIS declaration)
# ----------------------------------------------------------------------------
EVENT_SCHEMA = {
    "schema_name": "loop2_world.world_object_probe_event.v0",
    "modeled_on": "lev JsonlEventStore graph.operations_applied line "
                  "(world-engine-seam-events.jsonl)",
    "top_level_required": {
        "id": "str", "timestamp": "str", "type": "str",
        "source_entity": "str", "payload": "dict",
        "correlation_id": "str", "schema_version": "int",
    },
    "top_level_values": {"type": "graph.operations_applied",
                         "schema_version": 1},
    "payload_required": {"operations": "list", "event_id": "str"},
    "operation_required": {"type": "str", "timestamp": "str", "source": "str",
                           "entity_id": "str", "payload": "dict"},
    "operation_values": {"type": "upsert_entity"},
    "entity_required": {"id": "str", "type": "str", "source": "str",
                        "via": "str", "depth": "str", "last_classified": "str",
                        "decay_rate": "int", "claims": "list", "links": "list"},
    "entity_values": {"type": "world_object_probe_outcome", "depth": "L1"},
    "claim_required": {"id": "str", "kind": "str", "subject": "str",
                       "predicate": "str", "object": "str",
                       "truth_state": "str", "evidence_refs": "list",
                       "valid_at": "str", "created_at": "str"},
    "claim_values": {"kind": "assertion", "truth_state": "accepted"},
    "required_predicates": ["has_object_id", "view_index", "probe_position",
                            "probe_outcome", "occluded"],
    "allowed_outcomes": ["0", "1", "withheld"],
    "forbidden_substrings_hidden_leak": ["latent_word", "rule_id",
                                         "hidden_state", "rule_taps"],
}

_TYPES = {"str": str, "int": int, "dict": dict, "list": list}


def validate_event(ev):
    """Return (ok: bool, reason: str). Deterministic code gate, no judgment."""
    s = EVENT_SCHEMA
    if not isinstance(ev, dict):
        return False, "event not a dict"
    for k, tn in s["top_level_required"].items():
        if k not in ev or not isinstance(ev[k], _TYPES[tn]):
            return False, f"top-level field {k} missing/wrong type"
    for k, v in s["top_level_values"].items():
        if ev[k] != v:
            return False, f"top-level {k} != {v!r}"
    pl = ev["payload"]
    for k, tn in s["payload_required"].items():
        if k not in pl or not isinstance(pl[k], _TYPES[tn]):
            return False, f"payload field {k} missing/wrong type"
    if len(pl["operations"]) != 1:
        return False, "payload.operations must have exactly 1 operation"
    op = pl["operations"][0]
    for k, tn in s["operation_required"].items():
        if k not in op or not isinstance(op[k], _TYPES[tn]):
            return False, f"operation field {k} missing/wrong type"
    for k, v in s["operation_values"].items():
        if op[k] != v:
            return False, f"operation {k} != {v!r}"
    ent = op["payload"]
    for k, tn in s["entity_required"].items():
        if k not in ent or not isinstance(ent[k], _TYPES[tn]):
            return False, f"entity field {k} missing/wrong type"
    for k, v in s["entity_values"].items():
        if ent[k] != v:
            return False, f"entity {k} != {v!r}"
    preds = {}
    for cl in ent["claims"]:
        for k, tn in s["claim_required"].items():
            if k not in cl or not isinstance(cl[k], _TYPES[tn]):
                return False, f"claim field {k} missing/wrong type"
        for k, v in s["claim_values"].items():
            if cl[k] != v:
                return False, f"claim {k} != {v!r}"
        if cl["subject"] != ent["id"]:
            return False, "claim subject != entity id"
        preds[cl["predicate"]] = cl["object"]
    for p in s["required_predicates"]:
        if p not in preds:
            return False, f"required predicate {p} missing"
    if preds["probe_outcome"] not in s["allowed_outcomes"]:
        return False, "probe_outcome not in allowed_outcomes"
    if preds["occluded"] == "true" and preds["probe_outcome"] != "withheld":
        return False, "occluded probe leaks an outcome"
    if preds["occluded"] == "false" and preds["probe_outcome"] == "withheld":
        return False, "visible probe withheld"
    raw = json.dumps(ev)
    for bad in s["forbidden_substrings_hidden_leak"]:
        if bad in raw:
            return False, f"hidden-field leak: {bad!r} appears in event"
    return True, "ok"


# ----------------------------------------------------------------------------
# World dynamics
# ----------------------------------------------------------------------------
def step(word_bits, rule_idx):
    taps = RULE_FAMILY[rule_idx]
    n = len(word_bits)
    return tuple(
        (sum(word_bits[(i + o) % n] for o in taps)) % 2 for i in range(n)
    )


def trajectory(w0_int, rule_idx, n_steps, dynamics_on=True):
    bits = tuple((w0_int >> i) & 1 for i in range(N_BITS))
    traj = [bits]
    for _ in range(n_steps - 1):
        traj.append(step(traj[-1], rule_idx) if dynamics_on else traj[-1])
    return traj


# ----------------------------------------------------------------------------
# Seam-style event emission
# ----------------------------------------------------------------------------
def make_event(idx, object_id, view, pos, outcome, occluded):
    ts = f"{BASE_TIME}.{idx:06d}Z"  # deterministic, monotone
    eid = f"world-object:{object_id}:view:{view}:probe:{pos}"

    def claim(pred, obj):
        return {
            "id": f"{eid}:claim:{pred}", "kind": "assertion", "subject": eid,
            "predicate": pred, "object": obj, "truth_state": "accepted",
            "evidence_refs": [], "valid_at": ts, "created_at": ts,
        }

    entity = {
        "id": eid, "type": "world_object_probe_outcome", "source": SOURCE,
        "via": VIA, "depth": "L1", "last_classified": ts, "decay_rate": 0,
        "claims": [
            claim("has_object_id", object_id),
            claim("view_index", str(view)),
            claim("probe_position", str(pos)),
            claim("probe_outcome", outcome),
            claim("occluded", "true" if occluded else "false"),
        ],
        "links": [],
    }
    return {
        "id": f"ge-worldsource-{idx:06d}",
        "timestamp": ts,
        "type": "graph.operations_applied",
        "source_entity": SOURCE,
        "payload": {
            "operations": [{
                "type": "upsert_entity", "timestamp": ts, "source": SOURCE,
                "entity_id": eid, "payload": entity,
            }],
            "event_id": f"evt-worldsource-{idx:06d}",
        },
        "correlation_id": f"world-object-source:{object_id}",
        "schema_version": 1,
    }


def render_world(objects, masks, dynamics_on):
    """Emit one event per (object, view, position). Returns event list."""
    events = []
    idx = 0
    for object_id, (w0, rule) in objects:
        traj = trajectory(w0, rule, N_VIEWS, dynamics_on=dynamics_on)
        for v in range(N_VIEWS):
            occluded_set = masks[object_id][v]
            for pos in range(N_BITS):
                occ = pos in occluded_set
                outcome = "withheld" if occ else str(traj[v][pos])
                events.append(
                    make_event(idx, object_id, v, pos, outcome, occ))
                idx += 1
    return events


# ----------------------------------------------------------------------------
# Log parsing (checks consume the emitted artifact, not internal arrays)
# ----------------------------------------------------------------------------
def parse_log(path):
    """-> {object_id: {view: {pos: outcome_str}}}"""
    out = {}
    with open(path) as fh:
        for line in fh:
            ev = json.loads(line)
            ent = ev["payload"]["operations"][0]["payload"]
            preds = {c["predicate"]: c["object"] for c in ent["claims"]}
            oid = preds["has_object_id"]
            v = int(preds["view_index"])
            pos = int(preds["probe_position"])
            out.setdefault(oid, {}).setdefault(v, {})[pos] = \
                preds["probe_outcome"]
    return out


def consistent_hidden_states(view_constraints):
    """view_constraints: {view: {pos: '0'/'1'}} (withheld already dropped).
    Exhaustive over the full 1024-state hidden space."""
    survivors = []
    for (w0, rule) in HIDDEN_SPACE:
        traj = trajectory(w0, rule, N_VIEWS, dynamics_on=True)
        ok = True
        for v, posmap in view_constraints.items():
            for pos, val in posmap.items():
                if str(traj[v][pos]) != val:
                    ok = False
                    break
            if not ok:
                break
        if ok:
            survivors.append((w0, rule))
    return survivors


def equivalence_class(w0, rule):
    """Hidden states probe-indistinguishable under the FULL unoccluded probe
    family over the horizon (identical full trajectories)."""
    ref = trajectory(w0, rule, N_VIEWS, dynamics_on=True)
    return [(w, r) for (w, r) in HIDDEN_SPACE
            if trajectory(w, r, N_VIEWS, dynamics_on=True) == ref]


def flip_rate(log):
    """Fraction of bit flips between consecutive views on jointly visible
    positions, computed from an event log."""
    flips = 0
    pairs = 0
    for oid, views in log.items():
        for v in range(N_VIEWS - 1):
            a, b = views[v], views[v + 1]
            for pos in range(N_BITS):
                if a[pos] != "withheld" and b[pos] != "withheld":
                    pairs += 1
                    if a[pos] != b[pos]:
                        flips += 1
    return flips / pairs if pairs else float("nan"), pairs


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    if os.path.exists(OUTDIR):
        print(f"REFUSE-TO-REUSE: outdir already exists: {OUTDIR}",
              file=sys.stderr)
        sys.exit(2)
    os.makedirs(OUTDIR)

    rng = random.Random(SEED)

    # Sample 64 distinct hidden states (latent word 0..255 x rule 0..3).
    objects = []
    seen = set()
    while len(objects) < N_OBJECTS:
        w0 = rng.randrange(2 ** N_BITS)
        rule = rng.randrange(N_RULES)
        if (w0, rule) in seen:
            continue
        seen.add((w0, rule))
        objects.append((f"obj-{len(objects):03d}", (w0, rule)))

    # Occlusion masks: per object, per view, 2-4 occluded positions;
    # pattern varies across views (enforced: not all views share one mask).
    masks = {}
    for oid, _ in objects:
        while True:
            per_view = []
            for _ in range(N_VIEWS):
                k = rng.randint(OCCLUDE_MIN, OCCLUDE_MAX)
                per_view.append(frozenset(rng.sample(range(N_BITS), k)))
            if len(set(per_view)) >= 2:
                masks[oid] = per_view
                break

    # Render both worlds with the SAME objects and masks.
    on_path = os.path.join(OUTDIR, "events_dynamics_on.jsonl")
    off_path = os.path.join(OUTDIR, "events_dynamics_off.jsonl")
    ev_on = render_world(objects, masks, dynamics_on=True)
    ev_off = render_world(objects, masks, dynamics_on=False)
    for path, evs in ((on_path, ev_on), (off_path, ev_off)):
        with open(path, "w") as fh:
            for ev in evs:
                fh.write(json.dumps(ev) + "\n")

    checks = {}
    findings = []

    # ---- C3 schema validation (run first: later checks consume the log) ----
    n_bad = 0
    first_bad = None
    for ev in ev_on + ev_off:
        ok, reason = validate_event(ev)
        if not ok:
            n_bad += 1
            first_bad = first_bad or reason
    # Negative controls: the validator MUST reject these (check can fail).
    bad1 = make_event(999990, "obj-bad", 0, 0, "1", False)
    del bad1["correlation_id"]
    bad2 = make_event(999991, "obj-bad", 0, 1, "1", False)
    ent2 = bad2["payload"]["operations"][0]["payload"]
    ent2["claims"].append({
        "id": ent2["id"] + ":claim:latent_word", "kind": "assertion",
        "subject": ent2["id"], "predicate": "latent_word", "object": "170",
        "truth_state": "accepted", "evidence_refs": [],
        "valid_at": "x", "created_at": "x"})
    nc1_ok, nc1_reason = validate_event(bad1)
    nc2_ok, nc2_reason = validate_event(bad2)
    schema_pass = (n_bad == 0) and (not nc1_ok) and (not nc2_ok)
    checks["schema_valid"] = {
        "pass": schema_pass,
        "events_validated": len(ev_on) + len(ev_off),
        "events_rejected": n_bad,
        "first_rejection_reason": first_bad,
        "negative_control_missing_field_rejected": not nc1_ok,
        "negative_control_missing_field_reason": nc1_reason,
        "negative_control_hidden_leak_rejected": not nc2_ok,
        "negative_control_hidden_leak_reason": nc2_reason,
    }

    # ---- Parse the emitted artifact ----
    log_on = parse_log(on_path)
    log_off = parse_log(off_path)

    # ---- C1: no single view determines the object ----
    single_counts = []
    for oid, views in log_on.items():
        for v in range(N_VIEWS):
            constraints = {v: {p: o for p, o in views[v].items()
                               if o != "withheld"}}
            single_counts.append(len(consistent_hidden_states(constraints)))
    c1_min = min(single_counts)
    checks["hidden_state_genuine"] = {
        "pass": c1_min >= 2,
        "criterion": "min over (object,view) of consistent hidden states >= 2",
        "single_view_consistent_min": c1_min,
        "single_view_consistent_mean": round(
            sum(single_counts) / len(single_counts), 3),
        "single_view_consistent_max": max(single_counts),
        "candidate_space_size": len(HIDDEN_SPACE),
        "n_single_views_tested": len(single_counts),
    }

    # ---- C2: joint identifiability up to probe-equivalence class ----
    obj_map = dict(objects)
    n_exact = 0
    n_class = 0
    n_fail = 0
    joint_sizes = []
    class_sizes = []
    fail_examples = []
    for oid, views in log_on.items():
        constraints = {v: {p: o for p, o in views[v].items()
                           if o != "withheld"} for v in range(N_VIEWS)}
        survivors = set(consistent_hidden_states(constraints))
        w0, rule = obj_map[oid]
        eq = set(equivalence_class(w0, rule))
        joint_sizes.append(len(survivors))
        class_sizes.append(len(eq))
        if survivors == {(w0, rule)}:
            n_exact += 1
        elif survivors == eq:
            n_class += 1
        else:
            n_fail += 1
            if len(fail_examples) < 3:
                fail_examples.append({"object": oid,
                                      "survivors": len(survivors),
                                      "class": len(eq)})
    checks["joint_identifiability"] = {
        "pass": n_fail == 0,
        "criterion": "all views jointly cut consistent set to exactly the "
                     "full-trajectory probe-equivalence class",
        "objects": len(log_on),
        "exactly_identified": n_exact,
        "identified_up_to_equivalence_class_only": n_class,
        "not_identified": n_fail,
        "fail_examples": fail_examples,
        "joint_consistent_max": max(joint_sizes),
        "equivalence_class_max": max(class_sizes),
    }
    if n_class > 0:
        findings.append(
            f"C2 note: {n_class} object(s) identified only up to a "
            f"probe-equivalence class of size > 1 (probe-relative identity, "
            f"kept, not smoothed)")

    # ---- C4: dynamics OFF produces different view statistics ----
    fr_on, pairs_on = flip_rate(log_on)
    fr_off, pairs_off = flip_rate(log_off)
    diff = abs(fr_on - fr_off)
    checks["dynamics_off_differs"] = {
        "pass": diff > FLIP_RATE_THRESHOLD,
        "criterion": f"|flip_rate_on - flip_rate_off| > {FLIP_RATE_THRESHOLD}",
        "flip_rate_dynamics_on": round(fr_on, 6),
        "flip_rate_dynamics_off": round(fr_off, 6),
        "abs_difference": round(diff, 6),
        "visible_pairs_on": pairs_on,
        "visible_pairs_off": pairs_off,
    }

    all_pass = all(c["pass"] for c in checks.values())

    receipt = {
        "lane": "world_source",
        "sim_id": "world_object_source_v0",
        "classification": "world_engine_object_source",
        "card_authority": "system_v8/spinor_jepa/TOURNAMENT_CARD_v0.md "
                          "AMENDMENT v0.1 (occluded-object perception)",
        "seam_authority": [
            "lev-main/plugins/sim-eval/evals/cr_cross_engine_parity/receipts/"
            "world-engine-seam-events.jsonl",
            "lev-main/core/eval/src/world-engine-seam-receipt.test.ts",
        ],
        "seed": SEED,
        "python": sys.version.split()[0],
        "parameters": {
            "n_bits": N_BITS, "n_objects": N_OBJECTS, "n_views": N_VIEWS,
            "occlude_min": OCCLUDE_MIN, "occlude_max": OCCLUDE_MAX,
            "rule_family": {str(k): list(v) for k, v in RULE_FAMILY.items()},
            "rule_family_note": "additive (XOR) cellular automata, periodic "
                                "boundary -- classical linear fragment of the "
                                "QCA family; no quantum claim made",
            "hidden_space_size": len(HIDDEN_SPACE),
        },
        "files": {
            "events_dynamics_on": on_path,
            "events_dynamics_off": off_path,
            "events_per_file": len(ev_on),
        },
        "event_schema": EVENT_SCHEMA,
        "checks": checks,
        "all_pass": all_pass,
        "findings": findings,
        "promotion_allowed": False,
        "claim_ceiling": "working_sim; object source only -- no perception, "
                         "belief, or carrier claim is made here",
    }
    receipt_path = os.path.join(OUTDIR, "receipt.json")
    with open(receipt_path, "w") as fh:
        json.dump(receipt, fh, indent=2)

    print(json.dumps({
        "lane": "world_source",
        "file": os.path.abspath(__file__),
        "receipt": receipt_path,
        "all_pass": all_pass,
        "checks": {k: v["pass"] for k, v in checks.items()},
        "detail": {
            "single_view_consistent_min": c1_min,
            "objects_exactly_identified": n_exact,
            "objects_class_only": n_class,
            "objects_not_identified": n_fail,
            "flip_rate_on": round(fr_on, 4),
            "flip_rate_off": round(fr_off, 4),
            "events_emitted": len(ev_on) + len(ev_off),
        },
        "findings": findings,
    }, indent=2))


if __name__ == "__main__":
    main()
