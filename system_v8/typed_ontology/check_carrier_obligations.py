#!/usr/bin/env python3
"""Reference evaluator for system_v8/typed_ontology/carrier_obligations.json.

Its ONLY purpose is to make "machine-checkable" a measured property of the table
rather than an asserted one. It is not a gate. It is wired into no hook and no CI job.

Exit codes (stated because a consumer will read them):
    0  PASS_THIS_TABLE  every declared quantity's carrier predicate held AND was discharged
    1  BLOCK            a declared quantity contradicts its own declared carrier
    2  TABLE_REJECTED   evaluator-side defect: the table is malformed, so nothing is graded
    3  PARK             pending evidence. NOT ADMISSION. Nothing may be cited from a PARK.
    4  NO_INPUT         the table itself was accepted; no receipt was supplied to grade

Two rules copied deliberately from the estate's own record:
  - strict_parse is REUSED, not reimplemented. duplicate_json_key came back once
    because a new file reached for the stdlib default
    (claimgate_plugin/results/purgatory_shape_detectors_v0.json, finding `dup-key`).
  - a malformed table fails CLOSED. A checker that cannot state its own grammar
    must not grade anything.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
TABLE = os.environ.get("CARRIER_OBLIGATIONS_TABLE",
                       os.path.join(HERE, "carrier_obligations.json"))

sys.path.insert(0, REPO)
from claimgate_plugin.intake_supervisor import strict_parse  # noqa: E402

PASS, BLOCK, TABLE_REJECTED, PARK, NO_INPUT = 0, 1, 2, 3, 4

# D1, found by measuring fixture c3: the exit codes are NOT ordered by severity
# (PARK is 3 and BLOCK is 1), so combining outcomes with max() over exit codes
# reported a BLOCK finding as a PARK -- a fail-open in the evaluator itself.
# Severity is now explicit and exit codes are derived from it, never compared.
SEVERITY = {PASS: 0, PARK: 1, BLOCK: 2, NO_INPUT: 3, TABLE_REJECTED: 4}


def worse(a, b):
    return a if SEVERITY[a] >= SEVERITY[b] else b

# Ops this evaluator actually implements. The table's `ops` block is the declared
# vocabulary; anything in the table outside THIS set is an unimplemented op and the
# table is rejected rather than partially scored.
IMPLEMENTED = {
    "carrier_declared", "carrier_field_present", "carrier_assert_true",
    "carrier_numeric_equals", "value_range", "value_is_integer",
    "value_is_log2_of_integer", "cross_quantity_le", "cut_declared",
    "parameter_declared", "preregistered_contract", "distribution_normalized",
    "two_compatible_states", "process_declared", "fibre_nonempty",
    "carrier_class_disjoint_from", "artifact_binding",
}

# Separation ops range over the WHOLE declaration set. Held in a second closed set so a
# quantity predicate can never reach a cross-quantity mechanism by accident.
IMPLEMENTED_SEP = {
    "all_pairs_distinct_carrier_class", "distinct_carrier_refs",
    "requires_declaration_when_equal", "forbid_derivation",
    "value_coincidence_report", "aggregate_components_share_carrier_class",
    "cross_quantity_le",   # delegated to a quantity predicate; see implemented_via
}


# ---------------------------------------------------------------- table integrity

def load_table(path=TABLE):
    """Returns (table, problems). Non-empty problems means fail CLOSED."""
    problems = []
    try:
        with open(path, "rb") as fh:
            t = strict_parse(fh.read())
    except Exception as exc:
        return None, [f"table did not parse: {exc}"]

    declared_ops = set(k for k in (t.get("ops") or {}) if not k.startswith("_"))
    unimplemented = declared_ops - IMPLEMENTED
    if unimplemented:
        problems.append(f"table declares op(s) this evaluator does not implement: "
                        f"{sorted(unimplemented)}")

    qs = t.get("quantities")
    if not isinstance(qs, list) or not qs:
        return t, problems + ["table carries no quantities list"]

    seen = set()
    for q in qs:
        qid = q.get("id")
        if not qid:
            problems.append("a quantity has no id")
            continue
        if qid in seen:
            problems.append(f"duplicate quantity id {qid!r}")
        seen.add(qid)
        for req in ("formula", "required_carrier", "carrier_predicate",
                    "absent_disposition"):
            if not q.get(req):
                problems.append(f"{qid}: missing required field {req!r}")
        if q.get("absent_disposition") not in ("BLOCK", "PARK"):
            problems.append(f"{qid}: absent_disposition "
                            f"{q.get('absent_disposition')!r} outside {{BLOCK, PARK}}")
        clauses = flatten_predicate(q.get("carrier_predicate") or {})
        if not clauses:
            problems.append(f"{qid}: carrier_predicate has no clauses — an empty "
                            f"predicate is a routing target (residual RE-6)")
        for c in clauses:
            op = c.get("op")
            if op not in IMPLEMENTED:
                problems.append(f"{qid}: unknown or unimplemented op {op!r}")

    declared_sep = set(k for k in (t.get("separation_ops") or {}) if not k.startswith("_"))
    unimpl_sep = declared_sep - IMPLEMENTED_SEP
    if unimpl_sep:
        problems.append(f"table declares separation op(s) this evaluator does not "
                        f"implement: {sorted(unimpl_sep)}")

    cs = t.get("capacity_separations") or {}
    gen = cs.get("_the_general_form") or {}
    seps = [gen] + list(cs.get("separations") or [])
    if cs.get("no_scalar_total"):
        seps.append(cs["no_scalar_total"])
    for sep in seps:
        checks = sep.get("checks") or ([{"predicate": sep.get("predicate"),
                                         "id": sep.get("id"),
                                         "on_violation": sep.get("disposition")}]
                                        if sep.get("predicate") else [])
        if not checks:
            problems.append(f"separation {sep.get('id')!r} carries no checkable predicate")
        for chk in checks:
            op = ((chk.get("predicate") or {}).get("op"))
            if op not in IMPLEMENTED_SEP:
                problems.append(f"separation {chk.get('id')!r}: unknown or unimplemented "
                                f"op {op!r}")
            if chk.get("on_violation") not in ("BLOCK", "PARK", "REPORT_ONLY"):
                problems.append(f"separation {chk.get('id')!r}: on_violation "
                                f"{chk.get('on_violation')!r} outside "
                                f"{{BLOCK, PARK, REPORT_ONLY}}")
    return t, problems


def flatten_predicate(pred):
    """Predicates are all_of, or any_of_groups of all_of. Returns every clause."""
    out = []
    for c in pred.get("all_of") or []:
        if isinstance(c, dict) and c.get("op"):
            out.append(c)
    for g in pred.get("any_of_groups") or []:
        for c in (g.get("all_of") or []):
            if isinstance(c, dict) and c.get("op"):
                out.append(c)
    return out


# ---------------------------------------------------------------- receipt access

def at_path(doc, dotted):
    n = doc
    for part in dotted.split("."):
        if isinstance(n, dict) and part in n:
            n = n[part]
        else:
            return None, False
    return n, True


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def log2_of_integer(v, floor):
    if not is_num(v) or v < 0 or v > 60:
        return False
    c = 2.0 ** v
    return abs(c - round(c)) <= max(floor, floor * abs(c))


# ---------------------------------------------------------------- clause evaluation

def eval_clause(c, ctx):
    """Returns (holds, note). holds is True / False / None where None is VACUOUS."""
    op = c["op"]
    carrier = ctx["carrier"]
    val = ctx["value"]
    floors = ctx["floors"]
    floor = floors.get(c.get("floor_ref"), 0.0) if c.get("floor_ref") else 0.0

    if op == "carrier_declared":
        if carrier is None:
            return False, f"no carrier declaration resolves for carrier_ref {ctx['carrier_ref']!r}"
        want = c.get("class")
        got = carrier.get("class")
        if want and got != want:
            return False, f"carrier class is {got!r}, quantity requires {want!r}"
        return True, f"carrier class {got!r}"

    if carrier is None and op in ("carrier_field_present", "carrier_assert_true",
                                  "carrier_numeric_equals", "cut_declared",
                                  "distribution_normalized", "two_compatible_states",
                                  "process_declared", "fibre_nonempty"):
        return False, "carrier absent, so the clause cannot be met"

    if op == "carrier_field_present":
        names = c.get("any_of") or []
        for n in names:
            if n in carrier:
                return True, f"carrier field {n!r} present"
        return False, f"carrier declares none of {names}"

    if op == "carrier_assert_true":
        f = c["field"]
        if carrier.get(f) is not True:
            return False, f"carrier does not assert {f} true (found {carrier.get(f)!r})"
        # D5: an assertion is a producer boolean, the same class refused for artifact
        # discharge. Where the carrier supplies a spectrum, VERIFY the assertion against
        # it rather than taking the boolean. The boolean alone is reported as such.
        if f == "psd":
            spec = carrier.get("spectrum") or carrier.get("eigenvalues")
            if isinstance(spec, list) and spec:
                lo = min((x for x in spec if is_num(x)), default=None)
                if lo is None:
                    return False, "spectrum holds no finite numbers"
                if lo < floors.get("psd_eigenvalue_floor", 0.0):
                    return False, (f"carrier asserts psd true, but its OWN declared "
                                   f"spectrum has minimum eigenvalue {lo}, below the "
                                   f"table-fixed floor "
                                   f"{floors.get('psd_eigenvalue_floor')}. The assertion "
                                   f"is refused by the carrier's own numbers")
                return True, f"psd verified from declared spectrum, min eigenvalue {lo}"
        return True, (f"carrier asserts {f} true (PRODUCER ASSERTION — no spectrum "
                      f"declared to verify it against)")

    if op == "carrier_numeric_equals":
        f, want = c["field"], c["value"]
        got = carrier.get(f)
        if not is_num(got):
            return False, f"carrier field {f!r} is not a finite number ({got!r})"
        if abs(got - want) <= floor:
            return True, f"{f} = {got} within {floor}"
        return False, f"{f} = {got}, required {want} within {floor}"

    if op == "value_range":
        if not is_num(val):
            return False, f"reported value is not a finite number ({val!r})"
        lo, hi = c.get("min"), c.get("max")
        if lo is not None:
            eff = lo + floor            # the sign floors are NEGATIVE, so they relax
            if val < eff:
                return False, (f"value {val} below min {lo} (effective {eff} with "
                               f"table-fixed floor {floor})")
        if hi is not None and val > hi:
            return False, f"value {val} above max {hi}"
        return True, f"value {val} in range (min {lo}, floor {floor})"

    if op == "value_is_integer":
        when = c.get("when") or {}
        cf = when.get("carrier_field_equals")
        if cf:
            if carrier is None or carrier.get(cf["field"]) != cf["value"]:
                return None, (f"VACUOUS: gated on carrier {cf['field']}=={cf['value']!r}, "
                              f"carrier has {None if carrier is None else carrier.get(cf['field'])!r}")
        if not is_num(val):
            return False, f"reported value is not a finite number ({val!r})"
        if abs(val - round(val)) <= floor:
            return True, f"value {val} is integral"
        return False, f"value {val} is not integral within {floor}"

    if op == "value_is_log2_of_integer":
        if not is_num(val):
            return False, f"reported value is not a finite number ({val!r})"
        if log2_of_integer(val, floor):
            return True, f"2**{val} is integral"
        return False, (f"2**{val} = {2.0 ** val if 0 <= val <= 60 else 'out of range'} "
                       f"is not integral — this is not a count capacity")

    if op == "cross_quantity_le":
        other = c.get("other")
        if other == "log2_dimension":
            d = (carrier or {}).get("dimension")
            if not is_num(d) or d <= 0:
                return None, "VACUOUS: carrier declares no positive dimension"
            bound = math.log2(d)
        else:
            ov = ctx["sibling_values"].get(other)
            if ov is None:
                return None, f"VACUOUS: sibling quantity {other!r} absent from this receipt"
            bound = c.get("scale", 1.0) * ov
        if not is_num(val):
            return False, f"reported value is not a finite number ({val!r})"
        if val <= bound + max(floor, 1e-12):
            return True, f"{val} <= {bound}"
        return False, f"{val} > {bound} (scale {c.get('scale', 1.0)} on {other})"

    if op == "cut_declared":
        parts = carrier.get("parts")
        want = c.get("parts", 2)
        if not isinstance(parts, list) or len(parts) != want:
            return False, f"carrier declares {parts!r}, required {want} parts"
        dims = carrier.get("part_dimensions")
        d = carrier.get("dimension")
        if isinstance(dims, list) and is_num(d):
            prod = 1
            for x in dims:
                if not is_num(x):
                    return False, f"part_dimensions holds a non-number: {x!r}"
                prod *= x
            if abs(prod - d) > 1e-9:
                return False, f"part dimensions multiply to {prod}, carrier dimension is {d}"
        return True, f"{want}-part cut declared"

    if op == "parameter_declared":
        got = ctx["declaration"].get(c["field"])
        if is_num(got):
            return True, f"{c['field']} = {got} declared"
        return False, f"{c['field']} not declared as a number (found {got!r})"

    if op == "preregistered_contract":
        f = c["field"]
        if c.get("forbid_receipt_supplied") and (f in ctx["declaration"] or f in (carrier or {})):
            return False, (f"{f!r} is supplied by the receipt. A threshold accepted at "
                           f"verification time IS the s3/s6 relieving slot; refused")
        ref = ctx["declaration"].get(f + "_contract")
        if not isinstance(ref, dict) or not ref.get("sha256") or not ref.get("path"):
            return False, f"no preregistered contract with path+sha256 for {f!r}"
        p = os.path.normpath(os.path.join(REPO, ref["path"]))
        if not p.startswith(REPO + os.sep):
            return False, f"contract path {ref['path']!r} resolves outside the repo"
        if not os.path.exists(p):
            return False, f"contract path {ref['path']!r} does not exist"
        return True, f"contract {ref['path']} pinned by sha256"

    if op == "distribution_normalized":
        p = carrier.get(c["field"])
        if not isinstance(p, list) or not p:
            return False, f"carrier field {c['field']!r} is not a non-empty list"
        s = 0.0
        for x in p:
            if not is_num(x):
                return False, f"probability entry is not a finite number: {x!r}"
            if x < 0:
                return False, f"negative probability entry {x}"
            s += x
        if abs(s - 1.0) <= floor:
            return True, f"p sums to {s}"
        return False, f"p sums to {s}, required 1 within {floor}"

    if op == "two_compatible_states":
        refs = c.get("fields") or []
        states = []
        for r in refs:
            ref = ctx["declaration"].get(r)
            st = ctx["carriers"].get(ref) if ref else None
            if st is None:
                return False, f"{r!r} does not resolve to a declared carrier"
            states.append(st)
        need = set(c.get("require") or [])
        if "same_dim" in need and len({s.get("dimension") for s in states}) != 1:
            return False, f"dimensions differ: {[s.get('dimension') for s in states]}"
        if "both_psd" in need and not all(s.get("psd") is True for s in states):
            return False, "not both states assert psd"
        if "both_trace_one" in need:
            for s in states:
                t = s.get("trace")
                if not is_num(t) or abs(t - 1.0) > floors.get("trace_unit_floor", 0.0):
                    return False, f"a state has trace {t!r}"
        if "support_inclusion" in need and ctx["declaration"].get("support_inclusion") is not True:
            return False, "support_inclusion not asserted; a finite D is unlicensed"
        return True, f"{len(states)} compatible density states"

    if op == "process_declared":
        for f in ("generator_ref", "stationary_state_ref"):
            if not ctx["declaration"].get(f) and not carrier.get(f):
                return False, f"{f!r} not declared"
        return True, "process and stationary state declared"

    if op == "fibre_nonempty":
        for f in ("fibre_cardinality", "relation_cardinality", "section_count"):
            v = carrier.get(f)
            if is_num(v):
                if v >= 1:
                    return True, f"{f} = {v}"
                return False, (f"{f} = {v}. TYPED RELEASE: the release is the fibre "
                               f"DESCRIPTOR, never 1/0 and never arithmetic on an empty fibre")
        return False, "carrier declares no fibre cardinality"

    if op == "carrier_class_disjoint_from":
        others = c.get("others") or []
        mine = ctx["carrier_ref"]
        for o in others:
            oref = ctx["sibling_refs"].get(o)
            if oref is not None and oref == mine:
                if c.get("unless_declared_map") and ctx["declaration"].get("carrier_map"):
                    return True, f"shares carrier with {o} under a declared carrier_map"
                return False, (f"CONFLATION: this quantity and {o} rest on the SAME carrier "
                               f"{mine!r}, but their required carriers are different classes")
        return True, f"carrier disjoint from {others}"

    if op == "artifact_binding":
        # D4, found by measuring fixture c12: an earlier version accepted the producer's
        # own boolean `values_compared: true` as the discharge. That is a literal field the
        # producer wrote -- the exact class recorded in
        # claimgate_plugin/results/controller_literal_verdicts_v0.json. The comparison is
        # now performed HERE, by this process, or the clause fails.
        art = ctx["declaration"].get("artifact")
        if not isinstance(art, dict):
            return False, "no artifact declared, so no obligation is discharged"
        pth, dig, vpath = art.get("path"), art.get("sha256"), art.get("value_path")
        if not pth or not dig or not vpath:
            return False, ("artifact must declare path, sha256 and value_path; the "
                           "value_path is what makes a comparison possible at all")
        p = os.path.normpath(os.path.join(REPO, pth))
        if not p.startswith(REPO + os.sep):
            return False, f"artifact path {pth!r} resolves OUTSIDE the committed tree"
        if not os.path.exists(p):
            return False, f"artifact {pth!r} does not exist"
        import hashlib
        with open(p, "rb") as fh:
            raw = fh.read()
        got = hashlib.sha256(raw).hexdigest()
        if got != dig:
            return False, (f"artifact sha256 mismatch: declared {str(dig)[:16]}..., "
                           f"measured {got[:16]}...")
        try:
            adoc = strict_parse(raw)
        except Exception as exc:
            return False, f"artifact did not strict-parse: {exc}"
        av, ok = at_path(adoc, vpath)
        if not ok:
            return False, f"artifact has no value at {vpath!r}"
        if not is_num(av) or not is_num(val):
            return False, f"artifact value {av!r} or claimed value {val!r} is not a number"
        tol = ctx["floors"].get("log2_integrality_floor", 0.0)
        if abs(av - val) > tol:
            return False, (f"CLAIM DOES NOT MATCH ARTIFACT: receipt claims {val}, "
                           f"artifact {pth}:{vpath} holds {av}")
        return True, (f"artifact {pth} digest verified and {vpath} = {av} compared to the "
                      f"claimed {val} BY THIS PROCESS")

    return False, f"unreachable: op {op!r}"


def eval_predicate(pred, ctx):
    """Group semantics: all_of must all hold; any_of_groups needs ONE whole group."""
    groups = pred.get("any_of_groups")
    if groups:
        notes = []
        for g in groups:
            r = eval_predicate({"all_of": g.get("all_of") or []}, ctx)
            notes.append({"group": g.get("_group"), "result": r})
            if r["outcome"] == "HOLDS":
                # D3, found by measuring fixture c16: discharge was credited whenever ANY
                # clause anywhere in the predicate was artifact_binding, including a group
                # that was never taken. Discharge now follows the group that actually held.
                return {"outcome": "HOLDS", "discharged": r.get("discharged", False),
                        "groups": notes}
        # D6: when EVERY group fails, an unlabelled concatenation attributed the reason to
        # whichever group happened to be first, so an artifact-branch defect was reported
        # as "carrier class is 'record', quantity requires 'probability_map'". Failures now
        # carry the group they came from, and the group with the FEWEST failures -- the one
        # the producer was evidently aiming at -- is reported first.
        per = [(n["group"], n["result"].get("failures") or []) for n in notes]
        per.sort(key=lambda gf: len(gf[1]))
        return {"outcome": "FAILS", "discharged": False, "groups": notes,
                "failures": [dict(f, group=g) for g, fs in per for f in fs]}

    fails, vac, held, discharged = [], [], 0, False
    for c in pred.get("all_of") or []:
        holds, note = eval_clause(c, ctx)
        if holds is None:
            vac.append({"op": c["op"], "why": note})
        elif holds:
            held += 1
            if c["op"] == "artifact_binding":
                discharged = True
        else:
            fails.append({"op": c["op"], "why": note})
    return {"outcome": "FAILS" if fails else "HOLDS", "discharged": discharged,
            "clauses_held": held, "failures": fails, "vacuous": vac}


# ---------------------------------------------------------------- binding

def declared_quantities(receipt):
    blk = receipt.get("typed_ontology") if isinstance(receipt, dict) else None
    if not isinstance(blk, dict):
        return {}, []
    carriers = blk.get("carriers") if isinstance(blk.get("carriers"), dict) else {}
    qs = blk.get("quantities") if isinstance(blk.get("quantities"), list) else []
    return carriers, qs


def suspected_quantities(receipt, table):
    """Name-signal recognition ONLY. Deliberately weak, and PARK-capped by the table."""
    sig = []
    for q in table["quantities"]:
        for s in (q.get("name_signals") or []):
            sig.append((s.lower(), q["id"]))
    hits, stack = [], [("", receipt)]
    while stack:
        pre, node = stack.pop()
        if isinstance(node, dict):
            for k, v in node.items():
                p = f"{pre}.{k}" if pre else k
                if is_num(v):
                    kl = k.lower()
                    for s, qid in sig:
                        if s in kl:
                            hits.append({"path": p, "quantity_id": qid, "value": v})
                            break
                stack.append((p, v))
        elif isinstance(node, list):
            for i, v in enumerate(node[:6]):
                stack.append((f"{pre}[{i}]", v))
    return hits


def eval_separations(table, qtab, floors, decl_by_id, vals, refs, carriers):
    """Cross-quantity capacity separations. Returns (findings, worst_code)."""
    cs = table.get("capacity_separations") or {}
    gen = cs.get("_the_general_form") or {}
    blocks = [gen] + list(cs.get("separations") or []) + \
             ([cs["no_scalar_total"]] if cs.get("no_scalar_total") else [])
    out, worst = [], PASS

    def carrier_class(qid):
        return (qtab.get(qid) or {}).get("required_carrier")

    for sep in blocks:
        checks = sep.get("checks") or ([{"predicate": sep.get("predicate"),
                                         "id": sep.get("id"),
                                         "on_violation": sep.get("disposition")}]
                                        if sep.get("predicate") else [])
        for chk in checks:
            pred = chk.get("predicate") or {}
            op, cid = pred.get("op"), chk.get("id")
            disp = chk.get("on_violation")
            floor = floors.get(pred.get("floor_ref"), 0.0) if pred.get("floor_ref") else 0.0

            if chk.get("implemented_via"):
                out.append({"id": cid, "outcome": "DELEGATED",
                            "to": chk["implemented_via"]})
                continue

            if op == "all_pairs_distinct_carrier_class":
                ids = sorted(refs)
                for i in range(len(ids)):
                    for j in range(i + 1, len(ids)):
                        a, b = ids[i], ids[j]
                        if refs[a] is None or refs[a] != refs[b]:
                            continue
                        if carrier_class(a) == carrier_class(b):
                            continue
                        if pred.get("unless_declared_map") and \
                           (decl_by_id.get(a, {}).get("carrier_map")
                            or decl_by_id.get(b, {}).get("carrier_map")):
                            continue
                        out.append({"id": cid, "outcome": "VIOLATED", "disposition": disp,
                                    "why": f"CONFLATION: {a} (requires {carrier_class(a)}) and "
                                           f"{b} (requires {carrier_class(b)}) both rest on "
                                           f"carrier {refs[a]!r}"})
                        worst = worse(worst, BLOCK if disp == "BLOCK" else PARK)
                continue

            if op == "distinct_carrier_refs":
                # D2: directional. An earlier all-pairs form flagged S_vn and S_alpha
                # sharing one rho, which is legitimate -- same carrier class.
                s = pred.get("subject")
                if s not in refs or refs.get(s) is None:
                    out.append({"id": cid, "outcome": "VACUOUS",
                                "why": f"subject {s!r} not declared"})
                    continue
                for o in (pred.get("others") or []):
                    if o in refs and refs[o] == refs[s]:
                        out.append({"id": cid, "outcome": "VIOLATED", "disposition": disp,
                                    "why": f"{s} and {o} resolve to the same carrier "
                                           f"{refs[s]!r}, and their required carrier classes "
                                           f"differ ({carrier_class(s)} vs {carrier_class(o)})"})
                        worst = worse(worst, BLOCK if disp == "BLOCK" else PARK)
                continue

            if op == "requires_declaration_when_equal":
                s, o = pred.get("subject"), pred.get("other")
                need = pred.get("declaration")
                if s not in vals or o not in vals:
                    out.append({"id": cid, "outcome": "VACUOUS",
                                "why": f"needs both {s} and {o} declared"})
                    continue
                if abs(vals[s] - vals[o]) <= floor:
                    if decl_by_id.get(s, {}).get(need) or \
                       (carriers.get(refs.get(s)) or {}).get(need):
                        out.append({"id": cid, "outcome": "HOLDS",
                                    "why": f"{s} == {o} with {need!r} declared"})
                    else:
                        out.append({"id": cid, "outcome": "VIOLATED", "disposition": disp,
                                    "why": f"{s} = {vals[s]} equals {o} = {vals[o]} and "
                                           f"{need!r} is NOT declared. Equal values under two "
                                           f"capacity names is the conflation itself"})
                        worst = worse(worst, BLOCK if disp == "BLOCK" else PARK)
                else:
                    out.append({"id": cid, "outcome": "HOLDS",
                                "why": f"{s} != {o}, no declaration required"})
                continue

            if op == "forbid_derivation":
                s = pred.get("subject")
                src = decl_by_id.get(s, {}).get("derived_from")
                cls = (carriers.get(src) or {}).get("class") if src else None
                if cls and cls == pred.get("from_carrier_class"):
                    out.append({"id": cid, "outcome": "VIOLATED", "disposition": disp,
                                "why": f"{s} declares derived_from {src!r} of class {cls!r}; "
                                       f"a support count is not a rank"})
                    worst = worse(worst, BLOCK if disp == "BLOCK" else PARK)
                else:
                    out.append({"id": cid, "outcome": "HOLDS",
                                "why": f"{s} declares no derivation from "
                                       f"{pred.get('from_carrier_class')!r}"})
                continue

            if op == "value_coincidence_report":
                subs = pred.get("subjects") or []
                if all(s in vals for s in subs) and len(subs) == 2 and \
                   abs(vals[subs[0]] - vals[subs[1]]) <= floor:
                    out.append({"id": cid, "outcome": "REPORT_ONLY",
                                "why": f"{subs[0]} and {subs[1]} carry equal values "
                                       f"({vals[subs[0]]}). NOT evidence of conflation."})
                else:
                    out.append({"id": cid, "outcome": "NO_COINCIDENCE"})
                continue

            if op == "aggregate_components_share_carrier_class":
                for qid, d in decl_by_id.items():
                    if d.get("role") != "aggregate":
                        continue
                    comps = d.get("components") or []
                    classes = {carrier_class(c) for c in comps}
                    if len(classes) > 1:
                        out.append({"id": cid, "outcome": "VIOLATED", "disposition": disp,
                                    "why": f"aggregate {qid} spans carrier classes "
                                           f"{sorted(str(x) for x in classes)}. The chart is a "
                                           f"TYPED FAMILY, not one scalar total"})
                        worst = worse(worst, BLOCK if disp == "BLOCK" else PARK)
                    else:
                        out.append({"id": cid, "outcome": "HOLDS",
                                    "why": f"aggregate {qid} components share one class"})
                continue

            out.append({"id": cid, "outcome": "NOT_EVALUATED", "op": op})
    return out, worst


def evaluate(receipt, table):
    qtab = {q["id"]: q for q in table["quantities"]}
    floors = {k: v for k, v in (table.get("floors") or {}).items()
              if not k.startswith("_") and is_num(v)}
    carriers, decls = declared_quantities(receipt)

    sibling_values, sibling_refs = {}, {}
    for d in decls:
        qid = d.get("id")
        v, ok = at_path(receipt, d.get("at", "")) if d.get("at") else (d.get("value"), True)
        if qid and ok and is_num(v):
            sibling_values[qid] = v
        if qid:
            sibling_refs[qid] = d.get("carrier_ref")

    results, worst = [], PASS
    for d in decls:
        qid = d.get("id")
        q = qtab.get(qid)
        if q is None:
            results.append({"binding": "DECLARED", "quantity_id": qid,
                            "disposition": "BLOCK",
                            "why": f"{qid!r} is not a quantity in the table; an undeclared "
                                   f"quantity id is not a routing target"})
            worst = worse(worst, BLOCK)
            continue
        val, ok = at_path(receipt, d.get("at", "")) if d.get("at") else (d.get("value"), True)
        if not ok:
            results.append({"binding": "DECLARED", "quantity_id": qid,
                            "disposition": "BLOCK",
                            "why": f"declaration points at {d.get('at')!r}, which does not resolve"})
            worst = worse(worst, BLOCK)
            continue
        ref = d.get("carrier_ref")
        ctx = {"carrier": carriers.get(ref), "carrier_ref": ref, "value": val,
               "floors": floors, "declaration": d, "carriers": carriers,
               "sibling_values": {k: v for k, v in sibling_values.items() if k != qid},
               "sibling_refs": {k: v for k, v in sibling_refs.items() if k != qid}}
        r = eval_predicate(q["carrier_predicate"], ctx)
        if r["outcome"] == "FAILS":
            carrier_missing = ctx["carrier"] is None
            disp = q["absent_disposition"] if carrier_missing else "BLOCK"
            state = "MISSING" if carrier_missing else "CONTRADICTED"
        elif r.get("discharged"):
            disp, state = "PASS_THIS_TABLE", "PRESENT_DISCHARGED"
        else:
            disp, state = "PARK", "PRESENT_UNDISCHARGED"
        results.append({"binding": "DECLARED", "quantity_id": qid, "at": d.get("at"),
                        "value": val, "carrier_state": state, "disposition": disp,
                        "detail": r})
        worst = worse(worst, {"BLOCK": BLOCK, "PARK": PARK, "PASS_THIS_TABLE": PASS}[disp])

    decl_by_id = {d.get("id"): d for d in decls if d.get("id")}
    sep_findings, sep_worst = eval_separations(table, qtab, floors, decl_by_id,
                                              sibling_values, sibling_refs, carriers)
    worst = worse(worst, sep_worst)

    susp = suspected_quantities(receipt, table) if not decls else []
    if susp:
        worst = worse(worst, PARK)

    if not decls and not susp:
        return PARK, {"binding": "none", "declared": [], "suspected": [],
                      "disposition": "PARK",
                      "why": "the receipt declares no quantities, so it asserts none. Not "
                             "clean — UNCITABLE. There is deliberately no permissive fallback."}
    return worst, {"declared": results,
                   "separations": [f for f in sep_findings
                                   if f.get("outcome") in ("VIOLATED", "REPORT_ONLY")]
                                  or f"{len(sep_findings)} separation check(s), none violated",
                   "suspected": susp[:12], "suspected_count": len(susp),
                   "suspected_disposition": "PARK (name recognition cannot carry a BLOCK)"}


def main(argv):
    table, problems = load_table()
    if problems:
        print(json.dumps({"exit": TABLE_REJECTED, "disposition": "TABLE_REJECTED",
                          "problems": problems}, indent=1))
        return TABLE_REJECTED
    if len(argv) < 2:
        print(json.dumps({"exit": NO_INPUT, "disposition": "TABLE_ACCEPTED_NO_INPUT",
                          "quantities": len(table["quantities"]),
                          "separations_checkable": True,
                          "implemented_ops": sorted(IMPLEMENTED),
                          "implemented_separation_ops": sorted(IMPLEMENTED_SEP)}, indent=1))
        return NO_INPUT
    try:
        with open(argv[1], "rb") as fh:
            receipt = strict_parse(fh.read())
    except Exception as exc:
        print(json.dumps({"exit": BLOCK, "disposition": "BLOCK",
                          "why": f"receipt did not parse: {exc}"}, indent=1))
        return BLOCK
    code, det = evaluate(receipt, table)
    print(json.dumps({"exit": code, "receipt": argv[1], "result": det}, indent=1)[:6000])
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
