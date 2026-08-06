"""
A1 — fresh-context audit probe. Question: is `typed_ontology` a producer-chosen
container that selects audit depth, i.e. the same shape as gate_registry's
`claim_kind` (recorded as F1 in the ClaimGate probe lane)?

Method: take every fixture the reference evaluator BLOCKS (exit 1) and build a
variant with the single key `typed_ontology` removed. Nothing else changes: the
numeric values and their key names stay byte-identical, so name_signal
recognition still has the same material to work with.

This file MEASURES. Every disposition below is the evaluator's own exit code,
read off a subprocess this script started. Nothing here writes a status.
"""
import json, subprocess, sys, pathlib, hashlib, copy

HERE = pathlib.Path(__file__).resolve().parent
TO   = HERE.parent
PY   = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
CHK  = TO / "check_carrier_obligations.py"

def run(path):
    p = subprocess.run([PY, str(CHK), str(path)], capture_output=True, text=True, cwd=str(TO))
    try:    det = json.loads(p.stdout)
    except Exception: det = {"unparsed_stdout": p.stdout[:400]}
    return p.returncode, det

def disposition(det):
    r = det.get("result", {})
    if not isinstance(r, dict): return "?"
    if r.get("binding") == "none": return "PARK_no_quantities_declared"
    dd = [x.get("disposition") for x in (r.get("declared") or [])]
    seps = [f"{s.get('id')}:{s.get('outcome')}" for s in (r.get("separations") or [])
            if isinstance(s, dict)]
    if not dd and r.get("suspected"):
        return "PARK_suspected_only(" + str(r.get("suspected_count")) + " name hits)"
    return ",".join(map(str, dd)) + (" | " + ",".join(seps) if seps else "")

out = {"probe": "A1_is_declaration_a_relieving_surface",
       "evaluator": str(CHK.relative_to(TO.parent.parent)),
       "interpreter": PY, "cases": []}

stripped_dir = HERE / "stripped"
stripped_dir.mkdir(exist_ok=True)

for fx in sorted((TO / "fixtures").glob("*.json")):
    ec0, det0 = run(fx)
    if ec0 != 1:            # only fixtures the table actually BLOCKS are at stake
        continue
    try:    doc = json.loads(fx.read_bytes())
    except Exception as e:
        out["cases"].append({"fixture": fx.name, "skipped": f"unparseable: {e}"})
        continue
    if not isinstance(doc, dict) or "typed_ontology" not in doc:
        out["cases"].append({"fixture": fx.name, "baseline_exit": ec0,
                             "skipped": "no typed_ontology key to remove"})
        continue
    var = copy.deepcopy(doc); var.pop("typed_ontology")
    vp = stripped_dir / (fx.stem + "__typed_ontology_removed.json")
    vp.write_text(json.dumps(var, indent=1))
    ec1, det1 = run(vp)
    out["cases"].append({
        "fixture": fx.name,
        "baseline_exit": ec0, "baseline_disposition": disposition(det0),
        "stripped_path": str(vp.relative_to(TO)),
        "stripped_exit": ec1, "stripped_disposition": disposition(det1),
        "numbers_unchanged": {k: var.get(k) for k in var if k != "note"},
        "relieved": bool(ec0 == 1 and ec1 != 1),
    })

blocked = [c for c in out["cases"] if "baseline_exit" in c and c.get("baseline_exit") == 1
           and "skipped" not in c]
out["summary"] = {
    "fixtures_blocked_at_baseline": len(blocked),
    "relieved_by_removing_one_container": sum(1 for c in blocked if c["relieved"]),
    "still_blocked_after_removal": sum(1 for c in blocked if not c["relieved"]),
    "stripped_exit_codes": sorted({c["stripped_exit"] for c in blocked}),
}

# --- second measurement: are the capacity separations reachable at all without
# --- a declaration? Build a receipt whose key NAMES match S_0 and S_1 signals and
# --- whose values invert the required ordering S_0 >= S_1.
inv = {"claim": "support entropy and von Neumann entropy of one state",
       "metrics": {"S_0_bits": 2.0, "von_neumann_entropy_bits": 2.5}}
ip = HERE / "stripped" / "A1_ordering_inverted_no_declaration.json"
ip.write_text(json.dumps(inv, indent=1))
eci, deti = run(ip)
# and the same numbers WITH a declaration
dec = copy.deepcopy(inv)
dec["typed_ontology"] = {
    "carriers": {"rho": {"class": "density_operator", "dimension": 4, "psd": True,
                         "trace": 1.0, "spectrum": [0.4, 0.3, 0.2, 0.1]}},
    "quantities": [{"id": "S_0", "at": "metrics.S_0_bits", "carrier_ref": "rho",
                    "rank_cutoff_contract": {"path": "x", "sha256": "y"}},
                   {"id": "S_vn", "at": "metrics.von_neumann_entropy_bits",
                    "carrier_ref": "rho"}]}
dp = HERE / "stripped" / "A1_ordering_inverted_with_declaration.json"
dp.write_text(json.dumps(dec, indent=1))
ecd, detd = run(dp)
out["ordering_separation_reachability"] = {
    "violation": "S_0 = 2.0 < S_vn = 2.5 on one declared density carrier; the table "
                 "requires S_0 >= S_1 for a fixed state",
    "without_declaration": {"path": str(ip.relative_to(TO)), "exit": eci,
                            "disposition": disposition(deti),
                            "name_signals_matched": (deti.get("result") or {}).get("suspected_count")},
    "with_declaration":    {"path": str(dp.relative_to(TO)), "exit": ecd,
                            "disposition": disposition(detd)},
    "separation_reachable_without_declaration": eci == 1,
}

rp = HERE / "results" / "a1_declaration_is_the_relieving_surface.json"
rp.write_text(json.dumps(out, indent=1))
print(json.dumps(out["summary"], indent=1))
print(json.dumps(out["ordering_separation_reachability"], indent=1))
print("sha256", hashlib.sha256(rp.read_bytes()).hexdigest())
