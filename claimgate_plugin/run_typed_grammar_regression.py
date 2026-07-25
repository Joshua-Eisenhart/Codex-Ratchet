#!/usr/bin/env python3
"""TYPED-GRAMMAR REGRESSION — the reviewer's eight cases, plus a positive control.

WHY THESE EIGHT. claimgate_plugin/claim_policy_gate.py went through three designs
and each was defeated by a SHAPE trick rather than by defeating a check:

  1. key-name denylist + container allowlist                 -> b7, b8, b9
  2. inverted "every number is a claim" + 22 exempt paths     -> b11 (whole payload
     one level down under an exempt key, because the exemption pruned the SUBTREE
     not the leaf), b12 (top-level array returned 0 without evaluating)
  3. leaf-not-subtree patch                                   -> 12/12 block, but the
     rule is still shape inference from raw JSON and a 22-path raw-number exemption
     list is itself the next loophole list

The durable rule is a TYPED RECEIPT GRAMMAR: a schema ROLE decides what a position
must satisfy, so exemption is a TYPE the evaluator owns rather than a location the
producer can reach. These eight cases are the end-to-end regressions for it.

  1 producer self-exemption        b1_field_only_self_exempt.json
  2 omitted engine metadata        b2_field_only_asserted_number.json
  3 nested object under digest     b11_subtree_under_exempt_path.json
  4 array wrapper                  b12_toplevel_array_wrapper.json
  5 zero-number receipt DECLARING  b13_zero_number_declares_engines/  <- NEW
    engines
  6 fake JAX JSON printer          b4_fake_jax_leg/
  7 decorative JAX import          b5_decorative_jax/
  8 copied Julia value             j2_fake_julia_leg/

CASE 5 WAS AN OPEN BYPASS AND IS NEW HERE. Measured on this branch before the fix,
on a receipt with zero numbers that declared two load-bearing engines:

    claim_policy_gate  exit 0   "no numbers in any claim-bearing container"
    three_engine_seal  exit 0   "exempt (numeric_engine_required=false)"
    claim_verify       VERIFIED
    post_receipt_gate  exit 0,  gate_ledger seq=191 PASS

Not one line of engine code was on disk. The two stages excused each other: the
policy gate exists to refuse the seal's producer exemption, and it never looked,
because its requirement triggered on number COUNT and the count was zero. The fix
in claim_policy_gate.py moves the trigger to ROLE PRESENCE — a declared engine
obliges a witness whether or not a number was recorded — and requires BOTH no
numeric content AND no engine declaration for the exemption.

TWO LANES, AND ONLY ONE OF THEM DECIDES.

  CHAIN (acceptance-bearing).  claimgate_plugin/hooks/post_receipt_gate.sh — the
  fired enforcement path, digest-pinned in gate_integrity_manifest.json. Acceptance
  for all eight is judged here, on the measured exit, the durable ledger line, and
  claim_verify's verdict.

  GRAMMAR (recorded, not acceptance-bearing).  claimgate_plugin/receipt_grammar.py
  with claimgate_plugin/receipt_schema.json. This is the durable rule's own
  evaluator and it is under CONCURRENT AUTHORSHIP: during this session the same
  receipt bytes returned exit 0 and then exit 3 minutes apart as the module was
  edited. So its digest is recorded with every disposition and its exit does not
  set this runner's verdict — with ONE exception that needs no stability: if the
  grammar ADMITS any of the eight, that is a failure in the only direction that
  matters, and it fails the run.

POSITIVE CONTROL, AND WHY IT IS A PAIR. "All eight blocked" is also satisfied by a
gate that blocks everything, so the eight prove nothing on their own.

  p1_no_assertion_no_engine   no typed numerical assertion, no engine declared
                              anywhere -> must be ADMITTED by the chain
  p2_one_typed_measurement    byte-identical apart from EXACTLY ONE added field,
                              .value -> must NOT be admitted

The runner asserts the one-field property before it runs anything, so the split in
verdict cannot later be explained by some other drift between the two files. This
is the isolation design already used by run_numpy_containment_regression.py.

CLASSIFICATION IS MEASURED, NOT DECLARED. Each case is labelled from what the run
actually reported:
  CAN_FAIL          blocked by a check that discriminates on the attack's mechanism
  BY_CONSTRUCTION   blocked for an incidental reason that would hold even if the
                    attack were absent — a correct verdict for the wrong reason
  UNTESTED          not exercised
Case 8 is expected to land BY_CONSTRUCTION: claim_policy_gate resolves every leg
as <stem>_<engine>.py, so probe_julia.jl is reported NO_LEG whether the Julia leg
is real or forged (recorded as F3 in claimgate_plugin/results/
purgatory_engine_witness_v0.json). The runner detects that from the witness verdict
plus the file being present on disk, rather than taking anyone's word for it.

HONEST CEILING. claimgate_plugin/engine_witness.py carries its own header "FAILED
CANDIDATE — PURGATORY. Do NOT import this from any gate", with 11 recorded defects,
and claim_policy_gate.py imports it anyway. So a WITNESSED verdict in either lane
is not evidence for any claim. Every block recorded below therefore rests on either
a file-existence fact (NO_LEG) or a type/role fact, not on the defeated process
controls — the runner records which, per case.

Exit: 0 acceptance met | 1 a case was admitted, the control failed, or isolation
broke | 2 usage. Nonzero is a policy/infra disposition, never a scientific verdict.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BYPASS = REPO / "claimgate_plugin" / "fixtures" / "bypass"
HOOK = REPO / "claimgate_plugin" / "hooks" / "post_receipt_gate.sh"
LEDGER = REPO / "claimgate_plugin" / "results" / "gate_ledger.jsonl"
POLICY_GATE = REPO / "claimgate_plugin" / "claim_policy_gate.py"
CLAIM_VERIFY = REPO / "claimgate_plugin" / "claim_verify.py"
GRAMMAR = REPO / "claimgate_plugin" / "receipt_grammar.py"
GRAMMAR_SCHEMA = REPO / "claimgate_plugin" / "receipt_schema.json"

# Dispositions and verdicts that ADMIT. ADMITTED_PENDING_DEPTH is on this list on
# purpose: post_receipt_gate.sh sets gate_admits=1 on it, so allowing it would let
# a forged receipt through wearing an "audit owed" label.
ADMITTING = {"PASS", "ADMITTED_PENDING_DEPTH", "ADMITTED_FLOOR_PARKED"}
ADMITTING_VERDICTS = {"VERIFIED"}

CASES = [
    (1, "producer self-exemption",
     "b1_field_only_self_exempt.json",
     "engine_contract.numeric_engine_required=false with a reason. three_engine_seal.py:120 "
     "honours it; the policy gate must not, and a declaration that would LOWER the bar is "
     "recorded as an assertion and ignored."),
    (2, "omitted engine metadata",
     "b2_field_only_asserted_number.json",
     "asserts a number and says nothing about engines. Silence was read as 'pure symbolic/SMT/"
     "finite by default'. Omission is PENDING EVIDENCE."),
    (3, "nested object under digest",
     "b11_subtree_under_exempt_path.json",
     "the whole payload one level down under `digest`, which is on the exempt-path list. The "
     "exemption pruned the SUBTREE, not the leaf. A digest position may hold a SCALAR string; "
     "an object there is a type violation and the subtree is still inspected."),
    (4, "array wrapper",
     "b12_toplevel_array_wrapper.json",
     "the receipt wrapped in [ ]. A non-dict document returned 0 without evaluating, so the "
     "wrapper skipped the entire policy."),
    (5, "zero-number receipt DECLARING engines",
     "b13_zero_number_declares_engines/results/probe.json",
     "THE ORDERING DEFECT. Zero numbers, two engines declared load_bearing, no leg on disk. "
     "Measured at exit 0 / ledger seq=191 PASS / claim_verify VERIFIED before the fix, because "
     "the non-finite and witness checks sat behind `if not nums: return 0`."),
    (6, "fake JAX JSON printer",
     "b4_fake_jax_leg/results/probe.json",
     "the leg is `import json; print(json.dumps({...}))`. The old re-derive checked none of "
     "import jax / jaxpr / devices / __version__, so 'the JAX leg re-derived' meant only that "
     "a Python script printed matching JSON."),
    (7, "decorative JAX import",
     "b5_decorative_jax/results/probe.json",
     "`import jax` present, zero JAX operations invoked. Presence alone cannot separate this "
     "from a real leg."),
    (8, "copied Julia value",
     "j2_fake_julia_leg/results/probe.json",
     "probe_julia.jl runs under julia and computes nothing: the numbers are literals inside a "
     "string. This is what 'JAX and Julia agree to 1e-13' was made of before any Julia witness "
     "existed."),
]

CONTROL_ADMIT = "p1_no_assertion_no_engine/results/probe.json"
CONTROL_REJECT = "p2_one_typed_measurement/results/probe.json"
THE_ONE_FIELD = "value"


def sha256(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def chain(receipt: Path) -> dict:
    """Fire the real chain; read its exit and the line it durably recorded."""
    before = len(LEDGER.read_bytes().splitlines()) if LEDGER.exists() else 0
    proc = subprocess.run(["sh", str(HOOK), str(receipt)],
                          capture_output=True, text=True, cwd=str(REPO))
    row = {}
    if LEDGER.exists():
        want = str(receipt.relative_to(REPO)) if receipt.is_relative_to(REPO) else str(receipt)
        for ln in LEDGER.read_bytes().splitlines()[before:]:
            try:
                cand = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if cand.get("receipt_path") == want:
                row = cand
    return {"exit": proc.returncode,
            "disposition": row.get("disposition"),
            "blocking_stage": row.get("blocking_stage"),
            "ledger_seq": row.get("seq"),
            "stages": {s["stage"]: s["exit"] for s in row.get("stages", [])},
            "stage_messages": [l for l in proc.stderr.splitlines()
                               if ":" in l and l.split(":")[0] in
                               ("intake_supervisor", "recompute_veto", "claim_policy_gate",
                                "three_engine_seal", "claim_verify", "ratchet_floor")]}


def policy_detail(receipt: Path) -> dict:
    """claim_policy_gate alone, for the witness verdicts the classification needs."""
    p = subprocess.run([sys.executable, str(POLICY_GATE), str(receipt)],
                       capture_output=True, text=True, cwd=str(REPO))
    out = {"exit": p.returncode, "witness": {}, "message": None}
    i = p.stdout.find("{")
    if i >= 0:
        try:
            d = json.loads(p.stdout[i:])
            out["message"] = d.get("message")
            out["witness"] = (d.get("detail") or {}).get("witness") or {}
        except json.JSONDecodeError:
            pass
    if not out["message"]:
        # the non-object-document path prints only to stderr
        tail = [l for l in (p.stderr or "").splitlines() if l.startswith("claim_policy_gate:")]
        out["message"] = tail[-1] if tail else None
    return out


# What a recorded witness verdict actually rests on. The dispatch and mutation
# controls live in a module its own header calls a FAILED CANDIDATE, so a block
# resting on one of them is weaker than a block resting on a file not existing.
RESTS_ON = {
    "NO_LEG": "a FILE-EXISTENCE fact — the declared leg is not on disk. Independent of every "
              "defeated process control.",
    "NOT_A_JULIA_LEG": "a FILE-TYPE fact — the path is not a .jl source.",
    "ENGINE_UNAVAILABLE": "a TOOLCHAIN fact — the engine is not on PATH.",
    "NOT_PRESENT": "the PRESENCE control — the engine module never loaded.",
    "ENGINE_NEVER_USED": "the DISPATCH control, which fixture b10 defeats with one token "
                         "operation (F4) and which F11 shows also over-blocks real work.",
    "DECORATIVE_IMPORT": "the DISPATCH control, which fixture b10 defeats with one token "
                         "operation (F4) and which F11 shows also over-blocks real work.",
    "DISPATCH_UNMEASURED": "the DISPATCH control reporting no measurement; unmeasured blocks, "
                           "but it does not discriminate this attack from a broken harness.",
    "PRINTS_CONSTANTS": "the MUTATION control, defeated by F5 (any nonzero exit scores as a "
                        "pass) and F6 (a decoy field satisfies it).",
    "DECORATIVE": "the POISON control, defeated by F7 (the poison is greppable) and F8 (a "
                  "decorative `using Printf` satisfies the Julia variant).",
    "MUTATION_INCONCLUSIVE": "the MUTATION control failing to run; inconclusive blocks.",
}


def claim_verify_verdict(receipt: Path):
    p = subprocess.run([sys.executable, str(CLAIM_VERIFY), str(receipt)],
                       capture_output=True, text=True, cwd=str(REPO))
    i = (p.stdout or "").find("{")
    if i < 0:
        return None
    try:
        return json.loads(p.stdout[i:]).get("verdict")
    except json.JSONDecodeError:
        return None


def grammar(receipt: Path) -> dict:
    """The typed grammar lane. RECORDED, not acceptance-bearing — see the header."""
    if not GRAMMAR.exists():
        return {"exit": None, "disposition": "UNTESTED",
                "message": f"{GRAMMAR.relative_to(REPO)} is not present, so the durable rule "
                           f"has no evaluator to measure. UNTESTED is not a pass.",
                "module_sha256": None, "schema_sha256": None}
    p = subprocess.run([sys.executable, str(GRAMMAR), str(receipt)],
                       capture_output=True, text=True, cwd=str(REPO))
    disp, msg = None, None
    i = (p.stdout or "").find("{")
    if i >= 0:
        try:
            d = json.loads(p.stdout[i:])
            disp, msg = d.get("disposition"), d.get("message")
        except json.JSONDecodeError:
            pass
    if disp is None:
        tail = [l for l in (p.stderr or "").splitlines() if l.startswith("receipt_grammar:")]
        msg = tail[-1] if tail else (p.stderr or "").strip()[-200:]
        disp = {0: "pass", 1: "BLOCK", 3: "PARK"}.get(p.returncode, f"exit{p.returncode}")
    return {"exit": p.returncode, "disposition": disp, "message": msg,
            "module_sha256": sha256(GRAMMAR), "schema_sha256": sha256(GRAMMAR_SCHEMA)}


def classify(case_no: int, receipt: Path, ch: dict, pol: dict) -> tuple[str, str]:
    """MEASURED classification. Never a declared expectation."""
    if ch["exit"] == 0 or ch["disposition"] in ADMITTING:
        return "CAN_FAIL", "ADMITTED — the bypass is open end-to-end"
    # A julia verdict of NO_LEG while a .jl leg exists on disk means the block came
    # from leg-path resolution (F3), not from anything about the attack.
    jl = receipt.parent.parent / f"{receipt.stem}_julia.jl"
    jv = (pol["witness"].get("julia") or {}).get("verdict")
    if jv == "NO_LEG" and jl.exists():
        return "BY_CONSTRUCTION", (f"blocked with julia NO_LEG while {jl.name} IS on disk — "
                                  f"claim_policy_gate resolves legs as <stem>_<engine>.py, so "
                                  f"the Julia witness never fired (F3). The verdict is right; "
                                  f"the copied value was never examined.")
    if ch["blocking_stage"] == "claim_policy" or ch["stages"].get("claim_policy", 0) != 0:
        return "CAN_FAIL", ("blocked at the claim-policy stage, which is the stage that reads "
                            "the attack: " + (pol["message"] or "")[:150])
    return "CAN_FAIL", (f"blocked at {ch['blocking_stage']} (stages {ch['stages']})")


def isolation() -> dict:
    """The control pair must differ in exactly one field."""
    a = json.loads((BYPASS / CONTROL_ADMIT).read_bytes())
    b = json.loads((BYPASS / CONTROL_REJECT).read_bytes())
    differing = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
    problems = []
    if differing != [THE_ONE_FIELD]:
        problems.append(f"the control pair differs in {differing}, expected only "
                        f"['{THE_ONE_FIELD}'] — any other drift could explain the verdicts")
    if THE_ONE_FIELD in a:
        problems.append(f"the admit-side control already carries .{THE_ONE_FIELD}")
    if not isinstance(b.get(THE_ONE_FIELD), (int, float)) or isinstance(b.get(THE_ONE_FIELD), bool):
        problems.append(f"the reject-side .{THE_ONE_FIELD} is not a number, so it is not a "
                        f"typed numerical assertion")
    return {"one_field_difference": not problems, "differing_keys": differing,
            "the_one_field": THE_ONE_FIELD, "problems": problems}


def main(argv):
    if not HOOK.exists():
        print(f"run_typed_grammar_regression: usage — hook absent: {HOOK}", file=sys.stderr)
        return 2
    for rel in [c[2] for c in CASES] + [CONTROL_ADMIT, CONTROL_REJECT]:
        if not (BYPASS / rel).exists():
            print(f"run_typed_grammar_regression: usage — fixture absent: {BYPASS / rel}",
                  file=sys.stderr)
            return 2

    failures, rows = [], []
    iso = isolation()
    failures += iso["problems"]
    print(f"  isolation  one-field difference: {iso['one_field_difference']}  "
          f"(differing keys {iso['differing_keys']})")

    print("\n  EIGHT CASES — every one must PARK or BLOCK on the chain")
    for no, name, rel, why in CASES:
        p = BYPASS / rel
        ch = chain(p)
        pol = policy_detail(p)
        verd = claim_verify_verdict(p)
        gr = grammar(p)
        cls, cls_why = classify(no, p, ch, pol)

        admitted_chain = (ch["exit"] == 0 or ch["disposition"] in ADMITTING
                          or verd in ADMITTING_VERDICTS)
        if admitted_chain:
            failures.append(f"case {no} ({name}): ADMITTED by the chain — exit {ch['exit']}, "
                            f"disposition {ch['disposition']}, claim_verify {verd}")
        if gr["exit"] == 0:
            failures.append(f"case {no} ({name}): ADMITTED by the typed grammar (exit 0)")

        rests = {}
        for e, v in (pol["witness"] or {}).items():
            vd = (v or {}).get("verdict")
            alt = p.parent.parent / f"{p.stem}_{e}.jl"
            if vd == "NO_LEG" and alt.exists():
                rests[e] = (f"a PATH-RESOLUTION artefact — {alt.name} IS on disk, but the gate "
                            f"looked for {p.stem}_{e}.py. Nothing about the leg was examined (F3).")
            else:
                rests[e] = RESTS_ON.get(vd, f"verdict {vd!r}")
        if not rests:
            rests = {"_stage": "a TYPE/ROLE fact — no engine witness was reached; the block came "
                               "from what the receipt's own positions are, not from a process "
                               "control."}
        rows.append({"case": no, "name": name, "fixture": str(p.relative_to(REPO)),
                     "mechanism": why, "chain": ch, "claim_verify": verd,
                     "claim_policy_witness": pol["witness"], "block_rests_on": rests,
                     "grammar": gr,
                     "classification": cls, "classification_evidence": cls_why,
                     "admitted": admitted_chain})
        print(f"    {no}. {name}")
        print(f"       chain    exit={ch['exit']}  disposition={ch['disposition']}  "
              f"blocking_stage={ch['blocking_stage']}  claim_verify={verd}")
        print(f"       grammar  exit={gr['exit']}  disposition={gr['disposition']}")
        print(f"       {cls}: {cls_why[:150]}")
        for eng, r in rests.items():
            print(f"       rests on [{eng}] {r[:120]}")

    print("\n  POSITIVE CONTROL — the chain must still admit something")
    ca, cr = BYPASS / CONTROL_ADMIT, BYPASS / CONTROL_REJECT
    adm, rej = chain(ca), chain(cr)
    adm_g, rej_g = grammar(ca), grammar(cr)
    adm_v, rej_v = claim_verify_verdict(ca), claim_verify_verdict(cr)
    if adm["exit"] != 0 or adm["disposition"] not in ADMITTING:
        failures.append(f"the admit-side control was NOT admitted (exit {adm['exit']}, "
                        f"disposition {adm['disposition']}). Eight blocks prove nothing if the "
                        f"gate blocks everything.")
    if rej["exit"] == 0 or rej["disposition"] in ADMITTING or rej_v in ADMITTING_VERDICTS:
        failures.append(f"the reject-side control WAS admitted (exit {rej['exit']}, "
                        f"disposition {rej['disposition']}, claim_verify {rej_v}) — one added "
                        f"typed measurement changed nothing, so the trigger is not the content")
    for label, res, g, v in (("ADMIT  no assertion, no engine", adm, adm_g, adm_v),
                             ("REJECT + one typed measurement", rej, rej_g, rej_v)):
        print(f"    {label}\n       chain    exit={res['exit']}  disposition={res['disposition']}"
              f"  blocking_stage={res['blocking_stage']}  claim_verify={v}")
        print(f"       grammar  exit={g['exit']}  disposition={g['disposition']}")

    grammar_present = GRAMMAR.exists()
    out = {
        "probe": "claimgate_typed_grammar_regression_v1",
        "classification": "tool_lego_fit_probe", "promotion_allowed": False,
        "acceptance": "each of the eight must PARK or BLOCK on the fired chain; none may yield "
                      "VERIFIED, PASS or ADMITTED_PENDING_DEPTH; the typed grammar may not admit "
                      "any of them; the admit-side control must be ADMITTED and its one-field "
                      "sibling must not be",
        "lanes": {
            "chain": {"entry": str(HOOK.relative_to(REPO)), "acceptance_bearing": True,
                      "sha256": sha256(HOOK)},
            "grammar": {"module": str(GRAMMAR.relative_to(REPO)) if grammar_present else None,
                        "acceptance_bearing": False,
                        "module_sha256": sha256(GRAMMAR), "schema_sha256": sha256(GRAMMAR_SCHEMA),
                        "_why_not_acceptance_bearing":
                            "under concurrent authorship — the same receipt bytes returned exit 0 "
                            "and then exit 3 minutes apart during this session as the module was "
                            "edited. Its digest is recorded with every disposition. The one "
                            "direction that still fails the run is the grammar ADMITTING a case."}},
        "witness_ceiling":
            "claimgate_plugin/engine_witness.py is marked FAILED CANDIDATE — PURGATORY in its own "
            "header with 11 recorded defects, and claim_policy_gate.py imports it anyway. No "
            "WITNESSED verdict here is evidence for any claim. Each block below is classified by "
            "what it actually rested on.",
        "isolation": iso,
        "cases": rows,
        "control_admit": {"fixture": str(ca.relative_to(REPO)), "chain": adm,
                          "claim_verify": adm_v, "grammar": adm_g},
        "control_reject": {"fixture": str(cr.relative_to(REPO)), "chain": rej,
                           "claim_verify": rej_v, "grammar": rej_g},
        "counts": {"cases": len(CASES),
                   "non_admitting_on_chain": sum(1 for r in rows if not r["admitted"]),
                   "can_fail": sum(1 for r in rows if r["classification"] == "CAN_FAIL"),
                   "by_construction": sum(1 for r in rows
                                          if r["classification"] == "BY_CONSTRUCTION"),
                   "untested": sum(1 for r in rows if r["classification"] == "UNTESTED")},
        "acceptance_met": not failures, "failures": failures,
    }
    d = REPO / "claimgate_plugin" / "results"
    d.mkdir(exist_ok=True)
    (d / "typed_grammar_regression_v1.json").write_text(json.dumps(out, indent=1) + "\n")

    print(f"\n  counts  {out['counts']}")
    if failures:
        print(f"\nrun_typed_grammar_regression: FAIL — {len(failures)} unmet clause(s)")
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("\nrun_typed_grammar_regression: acceptance met — all eight non-admitting on the fired "
          "chain, none admitted by the typed grammar, and the control pair splits on the one "
          "field between them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
