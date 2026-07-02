#!/usr/bin/env python3
"""
recheck_proof.py -- close the hole the Wizard councils found (2026-05-29): the
field-checking gates (per_sim_contract.py, max_deep_lego_gate.py --rigor) validate
JSON fields, NOT computation. A hand-typed JSON with real_measured==control_measured,
bound_to_measured:false, and hand-typed sat/unsat verdicts PASSES them. This checker
catches that, two ways:

  STRUCTURAL (always): for each proof, the emitted real_measured and control_measured
    must (a) be present, (b) DIFFER (identical inputs cannot honestly flip a deterministic
    verdict), (c) bound_to_measured must be true, (d) real_claim_verdict != negated.
    For each ablation: baseline_value != ablated_value and |diff| == |outcome_delta|.

  PROVENANCE (with --rerun <sim.py>): re-execute the sim and confirm the freshly produced
    proof verdicts / ablation values / scale rungs MATCH the committed JSON. A hand-edited
    or hand-typed result cannot survive a real re-run.

usage: recheck_proof.py <result.json> [--rerun <sim.py>] [--python <interp>]
exit 0 iff structural (and, if --rerun, provenance) checks pass.
"""
import json
import subprocess
import sys
import tempfile


def _find(d, *subs):
    out = []

    def rec(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                if any(s in k.lower() for s in subs):
                    out.append((path + k, v))
                rec(v, path + k + ".")
        elif isinstance(o, list):
            for i, it in enumerate(o):
                rec(it, f"{path}[{i}].")
    rec(d)
    return out


def _proof_nodes(d):
    nodes = []
    for o in _all(d):
        if isinstance(o, dict) and ("real_claim_verdict" in o or "real_verdict" in o):
            nodes.append(o)
    return nodes


def _all(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from _all(v)
    elif isinstance(o, list):
        for v in o:
            yield from _all(v)


def structural(d):
    findings = []
    proofs = _proof_nodes(d)
    if not proofs:
        findings.append(("proof", False, "no proof node with a real/negated verdict"))
    for i, p in enumerate(proofs):
        rv = p.get("real_claim_verdict", p.get("real_verdict"))
        nv = p.get("negated_claim_verdict", p.get("negated_verdict"))
        rm = p.get("real_measured")
        cm = p.get("control_measured")
        bound = p.get("bound_to_measured")
        tag = p.get("claim", f"proof[{i}]")
        if str(rv).lower() == str(nv).lower():
            findings.append((tag, False, f"verdicts do not differ ({rv}=={nv}) -> tautology"))
        if bound is not True:
            findings.append((tag, False, f"bound_to_measured is not true ({bound}) -> not bound to real numbers"))
        if rm is None or cm is None:
            findings.append((tag, False, "missing real_measured/control_measured -> cannot be a real flip"))
        elif json.dumps(rm, sort_keys=True) == json.dumps(cm, sort_keys=True):
            findings.append((tag, False, f"real_measured == control_measured ({rm}) -> identical inputs cannot honestly flip a verdict"))
        else:
            findings.append((tag, True, "real!=control, bound, verdicts differ"))
    # ablations
    abls = [v for _, v in _find(d, "ablation") if isinstance(v, dict)]
    flat = {}
    for a in abls:
        for k, val in a.items():
            if isinstance(val, dict) and ("baseline_value" in val or "ablated_value" in val):
                flat[k] = val
    if not flat:
        findings.append(("ablation", False, "no ablation with baseline_value/ablated_value"))
    for k, val in flat.items():
        b, a = val.get("baseline_value"), val.get("ablated_value")
        dl = val.get("outcome_delta", val.get("delta"))
        try:
            b, a, dl = float(b), float(a), float(dl)
            if abs(b - a) < 1e-12:
                findings.append((k, False, f"baseline==ablated ({b}) -> no real ablation effect"))
            elif abs(abs(b - a) - abs(dl)) > 1e-6 * max(1.0, abs(dl)):
                findings.append((k, False, f"|baseline-ablated|={abs(b-a)} != |delta|={abs(dl)}"))
            else:
                findings.append((k, True, "real baseline!=ablated matching delta"))
        except (TypeError, ValueError):
            findings.append((k, False, f"non-numeric baseline/ablated/delta: {b},{a},{dl}"))
    ok = all(f[1] for f in findings)
    return ok, findings


def _key_numbers(d):
    """extract a stable signature of the proof verdicts + ablation values + scale rungs."""
    sig = {"verdicts": [], "ablations": [], "rungs": []}
    for p in _proof_nodes(d):
        sig["verdicts"].append((str(p.get("real_claim_verdict", p.get("real_verdict"))),
                                str(p.get("negated_claim_verdict", p.get("negated_verdict")))))
    for _, v in _find(d, "ablation"):
        if isinstance(v, dict):
            for k, val in v.items():
                if isinstance(val, dict) and "baseline_value" in val:
                    sig["ablations"].append((k, round(float(val.get("baseline_value", 0)), 6),
                                             round(float(val.get("ablated_value", 0)), 6)))
    for _, v in _find(d, "scale_ladder", "scale_rungs"):
        if isinstance(v, dict):
            rungs = v.get("rungs", v)
            if isinstance(rungs, dict):
                for rk, rv in rungs.items():
                    if isinstance(rv, dict):
                        sig["rungs"].append((str(rk), bool(rv.get("pass", rv.get("passed")))))
    sig["verdicts"].sort(); sig["ablations"].sort(); sig["rungs"].sort()
    return sig


def provenance(d, sim_py, interp):
    """re-run the sim, find its fresh result, compare key numbers."""
    import os
    before = _key_numbers(d)
    sim_abs = os.path.abspath(sim_py)
    simdir = os.path.dirname(sim_abs) or "."
    r = subprocess.run([interp, os.path.basename(sim_abs)], capture_output=True, text=True,
                       timeout=1200, cwd=simdir)
    if r.returncode != 0:
        return False, [f"sim re-run FAILED rc={r.returncode}: {(r.stderr or r.stdout)[-300:]}"]
    # find the freshest result the sim wrote (scan its dir for *_results.json mentioning object_id)
    import glob
    import os
    simdir = "/".join(sim_py.split("/")[:-1]) or "."
    oid = None
    for _, v in _find(d, "object_id"):
        oid = v
        break
    cands = sorted(glob.glob(f"{simdir}/results/*results.json"), key=os.path.getmtime, reverse=True)
    fresh = None
    for c in cands:
        try:
            cd = json.load(open(c))
        except Exception:
            continue
        if oid and any(vv == oid for _, vv in _find(cd, "object_id")):
            fresh = cd
            break
    if fresh is None:
        return False, ["could not locate the sim's fresh result after re-run (no matching object_id)"]
    after = _key_numbers(fresh)
    if before == after:
        return True, ["fresh re-run reproduces the committed proof/ablation/scale numbers"]
    return False, [f"MISMATCH after re-run: committed={before} fresh={after}"]


def main():
    if len(sys.argv) < 2:
        print("usage: recheck_proof.py <result.json> [--rerun <sim.py>] [--python <interp>]")
        return 2
    d = json.load(open(sys.argv[1]))
    interp = sys.argv[sys.argv.index("--python") + 1] if "--python" in sys.argv else sys.executable
    s_ok, findings = structural(d)
    print(f"RECHECK: {sys.argv[1].split('/')[-1]}")
    print("  STRUCTURAL:")
    for tag, ok, why in findings:
        print(f"    [{'PASS' if ok else 'FAIL'}] {tag}: {why}")
    p_ok = True
    if "--rerun" in sys.argv:
        sim = sys.argv[sys.argv.index("--rerun") + 1]
        p_ok, pf = provenance(d, sim, interp)
        print("  PROVENANCE (re-run):")
        for line in pf:
            print(f"    [{'PASS' if p_ok else 'FAIL'}] {line}")
    overall = s_ok and p_ok
    print(f"  recheck_pass={overall}")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
