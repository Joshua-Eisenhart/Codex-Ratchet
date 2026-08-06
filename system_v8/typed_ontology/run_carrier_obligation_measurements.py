#!/usr/bin/env python3
"""Runs check_carrier_obligations.py over the fixtures and over the real system_v8
receipt corpus, recording the MEASURED exit code of each subprocess.

Every exit code in the output file came from a process this script started and whose
returncode it read. Nothing is written by hand.
"""
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
CHECKER = os.path.join(HERE, "check_carrier_obligations.py")
CODE = {0: "PASS_THIS_TABLE", 1: "BLOCK", 2: "TABLE_REJECTED", 3: "PARK",
        4: "NO_INPUT"}

EXPECT = {
    "c1_declared_svn_honest": "PARK",
    "c2_declared_svn_negative_repo_value": "BLOCK",
    "c3_sep1b_capacity_conflation": "BLOCK",
    "c4_sep3a_one_carrier_two_classes": "BLOCK",
    "c5_receipt_supplied_rank_cutoff": "BLOCK",
    "c6_kappa_ext_not_log2_of_integer": "BLOCK",
    "c7_design4_defeating_payload": "PARK",
    "c8_empty_object": "PARK",
    "c9_kappa_empty_fibre": "BLOCK",
    "c10_iab_no_cut": "BLOCK",
    "c11_sigma_prod_no_carrier": "PARK",
    "c12_hshannon_record_artifact": "PASS_THIS_TABLE",
    "c13_duplicate_key": "BLOCK",
    "c14_hshannon_above_capacity": "BLOCK",
    "c15_sep2b_s0_derived_from_pair_field": "BLOCK",
    "c16_sep4_scalar_total": "BLOCK",
    "c17_s0_preregistered_contract_ok": "PARK",
    "c18_s0_above_dimension": "BLOCK",
    "c19_artifact_outside_tree": "BLOCK",
    "c20_claim_artifact_mismatch": "BLOCK",
    "c21_artifact_digest_mismatch": "BLOCK",
    "c22_producer_boolean_only": "BLOCK",
    "c23_psd_asserted_spectrum_refutes": "BLOCK",
}


def run(path=None, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    cmd = [PY, CHECKER] + ([path] if path else [])
    p = subprocess.run(cmd, capture_output=True, text=True, env=e, cwd=REPO)
    try:
        out = json.loads(p.stdout)
    except Exception:
        out = {"stdout_head": p.stdout[:300], "stderr_head": p.stderr[:600]}
    return p.returncode, out


def main():
    rec = {"schema": "cr.carrier_obligation_measurement.v1",
           "classification": "tool_lego_fit_probe",
           "promotion_allowed": False,
           "claim_ceiling": "measured exit codes of a reference evaluator. Not a gate, "
                            "wired into no hook and no CI job.",
           "interpreter": PY,
           "python_version": sys.version.split()[0]}

    # 1. table integrity, no input
    rc, out = run()
    rec["table_integrity"] = {"measured_exit_code": rc, "disposition": CODE.get(rc),
                              "detail": out}

    # 2. FAIL-CLOSED control: a table declaring an op the evaluator does not implement
    bad = os.path.join(HERE, "fixtures", "_malformed_table_control.json")
    with open(os.path.join(HERE, "carrier_obligations.json")) as fh:
        t = json.load(fh)
    t["quantities"][0]["carrier_predicate"]["all_of"].append({"op": "trust_the_producer"})
    with open(bad, "w") as fh:
        json.dump(t, fh)
    rc, out = run(os.path.join(HERE, "fixtures", "c1_declared_svn_honest.json"),
                  env={"CARRIER_OBLIGATIONS_TABLE": bad})
    rec["fail_closed_control"] = {
        "what": "a copy of the table with an unimplemented op injected into a predicate",
        "measured_exit_code": rc, "disposition": CODE.get(rc),
        "problems": (out.get("problems") or [])[:3],
        "why_it_matters": "a checker that cannot state its own grammar must not grade "
                          "anything. RE-6 in the table."}

    # 3. fixtures
    fx, mism = [], []
    for p in sorted(glob.glob(os.path.join(HERE, "fixtures", "c*.json"))):
        name = os.path.basename(p)[:-5]
        rc, out = run(p)
        got = CODE.get(rc, str(rc))
        want = EXPECT.get(name)
        row = {"fixture": name, "measured_exit_code": rc, "disposition": got,
               "preregistered_expectation": want,
               "agrees": (want == got) if want else None}
        res = out.get("result") or {}
        first = (res.get("declared") or [{}])[0] if isinstance(res, dict) else {}
        row["first_declared"] = {k: first.get(k) for k in
                                ("quantity_id", "carrier_state", "disposition")}
        det = first.get("detail") or {}
        fails = det.get("failures") or []
        if fails:
            row["first_failure"] = fails[0]
        seps = res.get("separations") if isinstance(res, dict) else None
        if isinstance(seps, list) and seps:
            row["separation_findings"] = seps
        if isinstance(res, dict) and not res.get("declared"):
            row["no_declaration_path"] = {"disposition": res.get("disposition"),
                                          "why": res.get("why") or out.get("why")}
        fx.append(row)
        if want and want != got:
            mism.append(row)
    rec["fixtures"] = fx
    rec["fixture_count"] = len(fx)
    rec["fixtures_agreeing_with_preregistered_expectation"] = sum(
        1 for r in fx if r["agrees"])
    rec["fixture_mismatches"] = mism

    # 4. the real corpus
    corpus, hist = [], {}
    for p in sorted(glob.glob(os.path.join(REPO, "system_v8", "**", "*.json"),
                              recursive=True)):
        if "/typed_ontology/" in p:
            continue
        rc, out = run(p)
        d = CODE.get(rc, str(rc))
        hist[d] = hist.get(d, 0) + 1
        res = out.get("result") or {}
        corpus.append({"path": os.path.relpath(p, REPO), "measured_exit_code": rc,
                       "disposition": d,
                       "suspected_count": res.get("suspected_count")
                       if isinstance(res, dict) else None})
    rec["real_corpus"] = {
        "files_measured": len(corpus),
        "disposition_histogram": hist,
        "receipts_with_at_least_one_suspected_quantity": sum(
            1 for c in corpus if (c["suspected_count"] or 0) > 0),
        "top_suspected": sorted([c for c in corpus if (c["suspected_count"] or 0) > 0],
                                key=lambda c: -(c["suspected_count"] or 0))[:12],
        "blocked": [c for c in corpus if c["disposition"] == "BLOCK"][:12],
    }

    outp = os.path.join(HERE, "check_carrier_obligations_run.json")
    with open(outp, "w") as fh:
        json.dump(rec, fh, indent=1)
    print(json.dumps({"wrote": os.path.relpath(outp, REPO),
                      "table_integrity_exit": rec["table_integrity"]["measured_exit_code"],
                      "fail_closed_exit": rec["fail_closed_control"]["measured_exit_code"],
                      "fixtures": rec["fixture_count"],
                      "agreeing": rec["fixtures_agreeing_with_preregistered_expectation"],
                      "mismatches": [m["fixture"] for m in mism],
                      "corpus": rec["real_corpus"]["files_measured"],
                      "corpus_histogram": hist}, indent=1))
    return 0 if not mism else 1


if __name__ == "__main__":
    sys.exit(main())
