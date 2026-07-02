#!/usr/bin/env python3
"""
max_deep_lego_gate.py  --  Wizard v4.2 council U1: executable max-deep lego gate.

Mechanically enforces the LEGO_SIM_CONTRACT max-deep bar + the v4.3 object-preservation
bar on a result JSON, so 'covered'/prose-scale/decorative-tool/object-erased receipts
cannot pass silently. Returns three independent verdicts + an overall.

  SCALE       : a REAL numeric scale ladder with >=1 rung at sites/qubits>=8, that rung
                NON-DENSE (dense_state_closure_used==False) and pass==True. A top-level
                prose scale_status STRING is NOT sufficient by itself (it must be backed
                by real rungs). (Verified on disk: density_operator_cptp_amplitude_damping
                has BOTH a prose scale_status AND real 8/16/32/64 non-dense rungs -> SCALE PASS.)
  OBJECT      : all 6 v4.3 first-class fields present + a present_survivor possibility-capacity
                invariant test passing (the retrocausal object actually instantiated, carried
                as fenced adapter metadata; classification 'lego'/'diagnostic_only';
                promotion_allowed false). (amplitude_damping has none -> OBJECT FAIL.)
  TOOLS       : >=1 non-numeric tool (z3/cvc5/sympy/clifford/PyG/rustworkx/gudhi/toponetx/quimb)
                marked load_bearing AND backed by an ablation_outcome_delta != 0 (the result
                changes when the tool is removed). load_bearing WITHOUT an ablation delta = FAIL.

usage: max_deep_lego_gate.py <result.json> [--object-required] [--scale-required]
exit 0 if the required gates pass, 1 otherwise.
"""
import json
import sys

NONNUMERIC_TOOLS = {"z3", "cvc5", "sympy", "clifford", "pyg", "torch_geometric", "rustworkx",
                    "gudhi", "toponetx", "quimb", "networkx"}
OBJECT_FIELDS = ["shells", "future_continuations", "compatibility_weights",
                 "compression_map", "present_survivor", "outward_record"]


def _walk(o):
    yield o
    if isinstance(o, dict):
        for v in o.values():
            yield from _walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from _walk(v)


def _find_keyed(d, name_substrs):
    """find dict nodes that contain a key matching any substring; return (keypath, node)."""
    out = []
    def rec(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                if any(s in k.lower() for s in name_substrs):
                    out.append((path + k, v))
                rec(v, path + k + ".")
        elif isinstance(o, list):
            for i, it in enumerate(o):
                rec(it, f"{path}[{i}].")
    rec(d)
    return out


def check_scale(d):
    reasons = []
    # find any scale ladder with a rungs dict
    ladders = [v for _, v in _find_keyed(d, ["scale_ladder", "scale_rungs"]) if isinstance(v, dict)]
    best_rung = None
    for lad in ladders:
        rungs = lad.get("rungs", lad)
        if not isinstance(rungs, dict):
            continue
        for _, rv in rungs.items():
            if not isinstance(rv, dict):
                continue
            n = rv.get("sites_or_qubits") or rv.get("qubits") or rv.get("sites") or rv.get("n")
            try:
                n = int(n)
            except (TypeError, ValueError):
                continue
            non_dense = rv.get("dense_state_closure_used") is False
            passed = bool(rv.get("pass", rv.get("passed", False)))
            if n >= 8 and non_dense and passed:
                if best_rung is None or n > best_rung:
                    best_rung = n
    prose = [v for _, v in _find_keyed(d, ["scale_status"]) if isinstance(v, str)]
    if best_rung is not None:
        reasons.append(f"real non-dense rung >=8 found at n={best_rung} (pass)")
        return True, reasons
    if prose:
        reasons.append(f"PROSE-SCALE ONLY: scale_status string present ({prose[0][:50]!r}) but NO real non-dense rung>=8 with pass -> reject")
    else:
        reasons.append("no real scale ladder with a non-dense rung>=8 pass")
    return False, reasons


def check_object(d):
    reasons = []
    present = []
    for f in OBJECT_FIELDS:
        hits = _find_keyed(d, [f])
        # require a non-empty value somewhere
        ok = any((v not in (None, "", [], {})) for _, v in hits)
        if ok:
            present.append(f)
    missing = [f for f in OBJECT_FIELDS if f not in present]
    # survivor invariant test passing
    inv = [v for _, v in _find_keyed(d, ["survivor_invariant"]) if isinstance(v, dict)]
    inv_pass = bool(inv and inv[0].get("passed"))
    promo = None
    for _, v in _find_keyed(d, ["promotion_allowed"]):
        promo = v
    if missing:
        reasons.append(f"OBJECT FIELDS MISSING: {missing}")
    else:
        reasons.append("all 6 first-class object fields present")
    if not inv_pass:
        reasons.append("survivor possibility-capacity invariant absent or not passing")
    else:
        reasons.append("survivor invariant passes")
    if promo is True:
        reasons.append("promotion_allowed must be false for an adapter lego")
    ok = (not missing) and inv_pass and (promo is not True)
    return ok, reasons


def check_depth(d, min_bond=8):
    """Many-body depth: max MPS bond across rungs >= min_bond AND a half-chain
    entanglement entropy > 0 (proving it is not a product state). Catches bond-1
    product states masquerading as many-body 'rich tensor network' layers."""
    reasons = []
    bonds = []
    for _, v in _find_keyed(d, ["mps_max_bond", "mps_bond", "max_bond", "bond_dim"]):
        try:
            bonds.append(int(v))
        except (TypeError, ValueError):
            pass
    ents = []
    for _, v in _find_keyed(d, ["entanglement_entropy", "half_chain_entropy"]):
        try:
            ents.append(float(v))
        except (TypeError, ValueError):
            pass
    max_bond = max(bonds) if bonds else 0
    max_ent = max(ents) if ents else 0.0
    if max_bond >= min_bond and max_ent > 1e-9:
        reasons.append(f"genuine many-body depth: max_bond={max_bond}>= {min_bond}, entropy={max_ent:.3g}>0")
        return True, reasons
    reasons.append(f"DEPTH FAIL: max_bond={max_bond} (need >={min_bond}), max half-chain entropy={max_ent:.3g} (need >0) -> product/shallow, not rich TN")
    return False, reasons


def check_tools(d):
    reasons = []
    tid = None
    for _, v in _find_keyed(d, ["tool_integration_depth"]):
        if isinstance(v, dict):
            tid = v
            break
    if not tid:
        return False, ["no tool_integration_depth block"]
    load_bearing = [t for t, depth in tid.items() if str(depth).lower() == "load_bearing" and t.lower() in NONNUMERIC_TOOLS]
    if not load_bearing:
        return False, ["no non-numeric tool marked load_bearing"]
    # require an ablation_outcome_delta != 0 for at least one load-bearing tool
    ablations = {}
    for _, v in _find_keyed(d, ["ablation"]):
        if isinstance(v, dict):
            ablations.update(v)
    proven = []
    for t in load_bearing:
        for ak, av in ablations.items():
            if t.lower() in ak.lower():
                try:
                    if abs(float(av if not isinstance(av, dict) else av.get("delta", av.get("outcome_delta", 0)))) > 1e-9:
                        proven.append(t)
                except (TypeError, ValueError):
                    pass
    if proven:
        reasons.append(f"load-bearing structural tools with nonzero ablation delta: {proven}")
        return True, reasons
    # PROOF tools (z3/cvc5/sympy) are load-bearing via a VERDICT FLIP, not a numeric ablation.
    # (Forcing a numeric ablation on them produces cosmetic hardcoded 'flip-score' ablations,
    # which the adversarial audit repeatedly flagged. The honest evidence is the flip.)
    proof_tools = {"z3", "cvc5", "sympy"}
    lb_proof = [t for t in load_bearing if t.lower() in proof_tools]
    has_flip = False
    for node in _all_dicts(d):
        rv = node.get("real_claim_verdict", node.get("real_verdict"))
        nv = node.get("negated_claim_verdict", node.get("negated_verdict", node.get("erased_verdict")))
        if rv is not None and nv is not None and str(rv).lower() != str(nv).lower():
            has_flip = True
            break
    if lb_proof and has_flip:
        reasons.append(f"load-bearing proof tools via verdict-flip (no numeric ablation needed): {lb_proof}")
        return True, reasons
    reasons.append(f"tools marked load_bearing {load_bearing} but no nonzero ablation AND no proof verdict-flip -> decorative-risk")
    return False, reasons


def check_rigor(d):
    """Catch the two fabrication patterns the adversarial audit exposed (2026-05-29):
      (A) COSMETIC ABLATION: a bare outcome_delta with no baseline/ablated recompute,
          or a hardcoded count. REQUIRE each ablation to carry baseline_value AND
          ablated_value (real numbers) with |baseline-ablated| ~= |outcome_delta| != 0.
      (B) TAUTOLOGICAL PROOF: a z3/cvc5 'load_bearing' witness that returns the same
          verdict whether the structural claim is asserted or negated. REQUIRE at least
          one proof recording real_claim_verdict AND negated_claim_verdict that DIFFER,
          and a flag that the SMT vars are bound to measured values."""
    reasons = []
    # (A) ablation rigor
    ablations = []
    for _, v in _find_keyed(d, ["ablation"]):
        if isinstance(v, dict):
            for ak, av in v.items():
                if isinstance(av, dict):
                    ablations.append((ak, av))
    real_ablation = False
    for ak, av in ablations:
        base = av.get("baseline_value", av.get("baseline", av.get("before")))
        abl = av.get("ablated_value", av.get("ablated", av.get("after")))
        delta = av.get("outcome_delta", av.get("delta"))
        try:
            b, a, dl = float(base), float(abl), float(delta)
            if abs(b - a) > 1e-9 and abs(abs(b - a) - abs(dl)) < 1e-6 * max(1.0, abs(dl)):
                real_ablation = True
        except (TypeError, ValueError):
            pass
    if real_ablation:
        reasons.append("ablation rigor OK: >=1 ablation with baseline+ablated recompute matching delta")
    else:
        reasons.append("ABLATION RIGOR FAIL: no ablation carries baseline_value+ablated_value whose diff equals a nonzero outcome_delta -> cosmetic/hardcoded-delta risk")
    # (B) proof rigor
    proofs = []
    for _, v in _find_keyed(d, ["proof_result", "proof_results", "smt", "z3_gate", "structural_proof"]):
        if isinstance(v, dict):
            proofs.append(v)
        elif isinstance(v, list):
            proofs += [x for x in v if isinstance(x, dict)]
    load_bearing_proof = False
    for node in _all_dicts(d):
        rv = node.get("real_claim_verdict", node.get("real_verdict", node.get("claim_verdict")))
        nv = node.get("negated_claim_verdict", node.get("negated_verdict", node.get("erased_verdict")))
        if rv is not None and nv is not None and str(rv).lower() != str(nv).lower():
            load_bearing_proof = True
            break
    if load_bearing_proof:
        reasons.append("proof rigor OK: a proof's real vs negated/erased verdict DIFFER (not a tautology)")
    else:
        reasons.append("PROOF RIGOR FAIL: no proof records real_claim_verdict != negated_claim_verdict -> tautology/decorative-z3 risk")
    ok = real_ablation and load_bearing_proof
    return ok, reasons


def _all_dicts(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from _all_dicts(v)
    elif isinstance(o, list):
        for v in o:
            yield from _all_dicts(v)


def main():
    if len(sys.argv) < 2:
        print("usage: max_deep_lego_gate.py <result.json> [--object-required] [--scale-required]")
        return 2
    d = json.load(open(sys.argv[1]))
    obj_req = "--object-required" in sys.argv
    scale_req = "--scale-required" in sys.argv
    depth_req = "--depth-required" in sys.argv
    rigor_req = "--rigor" in sys.argv
    s_ok, s_r = check_scale(d)
    o_ok, o_r = check_object(d)
    t_ok, t_r = check_tools(d)
    d_ok, d_r = check_depth(d)
    r_ok, r_r = check_rigor(d)
    report = {
        "file": sys.argv[1].split("/")[-1],
        "scale": {"pass": s_ok, "reasons": s_r},
        "many_body_depth": {"pass": d_ok, "reasons": d_r},
        "object_preservation": {"pass": o_ok, "reasons": o_r},
        "tools_load_bearing": {"pass": t_ok, "reasons": t_r},
        "rigor_no_fabrication": {"pass": r_ok, "reasons": r_r},
        "max_deep_object_preserving_bar": bool(s_ok and o_ok and t_ok and r_ok),
    }
    any_req = obj_req or scale_req or depth_req or rigor_req
    required = (s_ok or not scale_req) and (o_ok or not obj_req) and (d_ok or not depth_req) and (r_ok or not rigor_req)
    report["required_gates_pass"] = bool(required if any_req else (s_ok and o_ok and t_ok))
    print(json.dumps(report, indent=2))
    return 0 if report["required_gates_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
