#!/usr/bin/env python3
"""Tick r+1 executor for obligation src-1858a5f7dbbb248f:o0.

Executes the compiled Root-Ratchet obligation
DISCRIMINATE_DETERMINISTIC_COMPLETIONS against the live source
finite_contextuality_marginal_gluing_no_global_section_v0, per the kernel:

  O_{r+1} demanded source execution at (h0,h1,p) in {(0,0,0),(1,0,0),(1,1,0)},
  held-out result before selector access, full frontier recomputation,
  killed candidates to Purgatory with deletion witnesses.

Projection semantics (from contextuality_source_locked_extractor.py):
  h0 = variant ordinal (0=peres_mermin signs, 1=control signs)
  h1 = context ordinal parity over ordered CONTEXTS
  p  = that context's sign (+1 -> "1", -1 -> "0")
  o  = the assessment's global_infeasible bit

ANF convention (confirmed against the frozen census): candidate mask m in
0..255 encodes coefficients c_A at bit index A (A a subset bitmask over
x=(h0,h1,p)); f_m(x) = XOR of bits of m at indices A with A subset of
set-bits(x). No promotion; packet-relative kills only.
"""
import hashlib, importlib.util, json, shutil, sys, io, contextlib
from pathlib import Path

V8 = Path(__file__).resolve().parent.parent  # system_v8/
INPUTS = V8 / "inputs"  # hash-bound copies from Pack 177 v2 (inputs/INPUT_HASHES.sha256)
LIVE_SOURCE = (V8.parent / "system_v7" / "sims"
               / "finite_contextuality_marginal_gluing_no_global_section_v0"
               / "finite_contextuality_marginal_gluing_no_global_section_v0_smt.py")
LOCK_SHA = "5cc45b90c41efaf95557e448583bc6125b05bbaa5dc4547f410bddc8cc097a6e"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else V8 / "kernel_tick" / "results" / "tick_r1_run"
HANDLE = "src-1858a5f7dbbb248f"
DEMANDED = [(0, 0, 0), (1, 0, 0), (1, 1, 0)]  # (h0, h1, p) with p=0 meaning sign -1


def sha256_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha256_json(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


_census_spec = importlib.util.spec_from_file_location(
    "_census", INPUTS / "census" / "source_balanced_completion_ratchet.py")
_census = importlib.util.module_from_spec(_census_spec)
_census_spec.loader.exec_module(_census)


def anf_eval(mask, x):
    """Authoritative ANF evaluation delegated to the pack's own census code."""
    return _census.eval_anf(mask, {"h0": x[0], "h1": x[1], "p": x[2]})


def main():
    if OUT.exists():
        raise SystemExit(f"refusing to reuse output: {OUT}")
    OUT.mkdir(parents=True)
    # 1. hash-lock and isolate the source
    live_sha = sha256_file(LIVE_SOURCE)
    assert live_sha == LOCK_SHA, f"live source drifted: {live_sha}"
    iso = OUT / "isolated_source"
    (iso / "results").mkdir(parents=True)
    src = iso / LIVE_SOURCE.name
    shutil.copyfile(LIVE_SOURCE, src)
    assert sha256_file(src) == LOCK_SHA
    spec = importlib.util.spec_from_file_location("_tick_ctx_src", src)
    mod = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(mod)
    context_ids = list(mod.CONTEXTS)
    variants = {0: ("peres_mermin", dict(mod.PM_SIGNS)), 1: ("control", dict(mod.CTRL_SIGNS))}

    # 2. baseline fresh assessments; must reproduce the original projection's o bits
    baseline = {}
    for v, (name, signs) in variants.items():
        a = mod.assess(signs)
        baseline[name] = {"global_infeasible": bool(a["global_infeasible"]),
                          "all_marginals_feasible": bool(a["all_marginals_feasible"])}
    assert baseline["peres_mermin"]["global_infeasible"] is True
    assert baseline["control"]["global_infeasible"] is False

    # 3. HELD-OUT executions at demanded cells (write raw receipt before any
    #    candidate/selector evaluation)
    executions = []
    for (h0, h1, p) in DEMANDED:
        vname, base_signs = variants[h0]
        want_sign = 1 if p == 1 else -1
        target = next(cid for i, cid in enumerate(context_ids)
                      if (i & 1) == h1 and base_signs[cid] != want_sign)
        signs = dict(base_signs)
        signs[target] = want_sign
        a = mod.assess(signs)
        o = 1 if a["global_infeasible"] else 0
        executions.append({
            "demanded_cell": {"h0": h0, "h1": h1, "p": p},
            "variant": vname,
            "modified_context": target,
            "sign_assignment": signs,
            "per_context_marginals": a["per_context_marginals"],
            "all_marginals_feasible": bool(a["all_marginals_feasible"]),
            "global_infeasible": bool(a["global_infeasible"]),
            "outcome_o": o,
        })
    heldout_receipt = {
        "schema_version": "ratchet.tick.heldout-execution/0.1",
        "handle": HANDLE,
        "source_sha256": f"sha256:{LOCK_SHA}",
        "baseline": baseline,
        "executions": executions,
        "selector_access_before_this_write": False,
    }
    (OUT / "heldout_execution_receipt.json").write_text(json.dumps(heldout_receipt, indent=2, sort_keys=True) + "\n")

    # 4. only NOW load the frozen frontier and obligation (selector access)
    fuel = json.loads((INPUTS / "receipts" / "fuel_obligations.json").read_text())
    src_entry = next(s for s in fuel["sources"] if s["handle"] == HANDLE)
    ob = next(o for o in src_entry["obligations"]
              if o["kind"] == "DISCRIMINATE_DETERMINISTIC_COMPLETIONS")
    tables = json.loads((INPUTS / "receipts" / "normalized_source_tables.json").read_text())
    rows = next(s["rows"] for s in tables["sources"] if s["handle"] == HANDLE)
    old_rows = [((int(r["h0"]), int(r["h1"]), int(r["p"])), int(r["o"])) for r in rows]
    # cross-check against the raw source-locked bundle receipt
    bundle = json.loads((INPUTS / "receipts" / "02_contextuality_source_locked.json").read_text())
    raw = sorted(((int(r["history"][0]), int(r["history"][1]), int(r["probe"])), int(r["outcome"]))
                 for r in bundle["projection"]["records"])
    assert sorted(old_rows) == raw, "normalized table disagrees with raw bundle projection"

    # 5. reproduce F_r independently: all 256 ANF masks vs the 12 original rows
    survivors_r = sorted(m for m in range(256)
                         if all(anf_eval(m, x) == o for x, o in old_rows))
    frozen_frontier = sorted(set(
        m for c in ob["candidate_discriminating_contexts"]
        for m in c["zero_survivors"] + c["one_survivors"]))
    assert survivors_r == frozen_frontier, (survivors_r, frozen_frontier)

    # cross-check the obligation's predicted splits against independent ANF eval
    for c in ob["candidate_discriminating_contexts"]:
        x = tuple(c["context"])
        for m in c["zero_survivors"]:
            assert anf_eval(m, x) == 0
        for m in c["one_survivors"]:
            assert anf_eval(m, x) == 1

    # 6. apply held-out outcomes: full recomputation over ALL rows (old + new)
    new_rows = [((e["demanded_cell"]["h0"], e["demanded_cell"]["h1"], e["demanded_cell"]["p"]),
                 e["outcome_o"]) for e in executions]
    all_rows = old_rows + new_rows
    survivors_r1 = sorted(m for m in range(256)
                          if all(anf_eval(m, x) == o for x, o in all_rows))
    killed = sorted(set(survivors_r) - set(survivors_r1))
    purgatory = []
    for m in killed:
        witness = next({"context": list(x), "observed_outcome": o,
                        "candidate_prediction": anf_eval(m, x)}
                       for x, o in new_rows if anf_eval(m, x) != o)
        purgatory.append({"candidate_mask": m, "status": "PARKED_PURGATORY",
                          "deletion_witness": witness,
                          "reoffer_rule": "universally eligible after material context change"})

    # continuation-conflict check on the augmented data (relation residual)
    by_ctx = {}
    for x, o in all_rows:
        by_ctx.setdefault(x, set()).add(o)
    conflicts = sorted([list(x) for x, os_ in by_ctx.items() if len(os_) > 1])

    tick = {
        "schema_version": "ratchet.tick/0.1",
        "kernel": "K_r=(D_r,G_r,Pi_r,{preceq_i},C_r,H_r); O_{r+1}=Compile(Delta_r,C_r,H_r)",
        "handle": HANDLE,
        "family_id": "finite_contextuality_marginal_gluing_no_global_section_v0",
        "obligation_id": ob["obligation_id"],
        "predecessor_bindings": {
            "fuel_obligations_sha256": f"sha256:{sha256_json(fuel)}",
            "source_sha256": f"sha256:{LOCK_SHA}",
            "heldout_receipt_sha256": f"sha256:{sha256_json(heldout_receipt)}",
        },
        "D_r_row_count": len(old_rows),
        "D_r1_row_count": len(all_rows),
        "new_records": [{"history": [str(x[0]), str(x[1])], "probe": str(x[2]),
                         "outcome": str(o)} for x, o in new_rows],
        "F_r_deterministic_survivors": survivors_r,
        "F_r1_deterministic_survivors": survivors_r1,
        "killed_to_purgatory": purgatory,
        "continuation_conflicts_after": conflicts,
        "retained_state_changed": survivors_r1 != survivors_r,
        "delta_r1_pressure_vector": {
            "continuation_conflict_contexts": len(conflicts),
            "heldout_candidate_kills": len(killed),
            "surviving_deterministic_completions": len(survivors_r1),
        },
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": ("packet-relative deterministic-completion discrimination for one "
                          "anonymous source; no scientific, physical, or canonical claim"),
    }
    (OUT / "tick_receipt.json").write_text(json.dumps(tick, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "F_r": survivors_r, "heldout_outcomes": [e["outcome_o"] for e in executions],
        "F_r1": survivors_r1, "killed": killed,
        "retained_state_changed": tick["retained_state_changed"],
        "receipt": str(OUT / "tick_receipt.json"),
    }, indent=2))


if __name__ == "__main__":
    main()
