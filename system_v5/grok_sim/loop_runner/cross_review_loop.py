#!/usr/bin/env python3
"""cross_review_loop.py — models loop on each other within a single iteration.

Architecture (per iteration):
  Step 1.  A_generator writes a patch for the failing phase
  Step 2.  Codex review audits A's patch → specific findings (NEW: includes the
           list of "currently passing phases that must stay passing")
  Step 3.  B_generator sees A's patch + audit findings, REVISES the patch
  Step 4.  Codex review audits B's revision
  Step 5.  C_generator (or A again) sees B's revision + audit findings, REVISES
  Step 6.  Continue until either:
             a) Codex review returns no P0 AND runner shows improvement
             b) Max sub-iterations hit (default 3)
  Step 7.  Accept the converged candidate; advance to next failing phase

This is models REVIEWING each other's work, not just alternating generation.
Each subsequent generator sees:
  - the prior generator's output (the "current patch attempt")
  - the audit findings on that patch (what Codex flagged)
  - the regression-guard list (what must not be broken)

Goal: converge to a CLEAN patch within each iteration before advancing.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import multi_model_loop as mml
import loop_driver as ld
import lego_miner

CANDIDATES = HERE.parent / "candidates"
PROMPTS = HERE / "prompts"
RUNNER = HERE / "runner.py"
PYTHON_BIN = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"


def run_runner(candidate_path: Path) -> dict:
    return mml.run_runner(candidate_path)


def codex_review(candidate_path: Path) -> dict:
    return mml.codex_review(candidate_path)


def build_cross_review_prompt(
    public_contract: str,
    candidate_code: str,
    failing_phase: str,
    sanitized_failures: list,
    metrics: dict,
    iteration: int,
    sub_iter: int,
    prior_generator: str,
    prior_audit_findings: list,
    passing_phases: list,
):
    """Prompt for a generator that's reviewing the PRIOR generator's patch.

    Key differences from the single-shot prompt:
      - Names the prior generator explicitly ("Grok produced this; here's what
        Codex flagged; you are Gemini, fix the audit findings.")
      - Lists currently-passing phases as preserve-targets (regression guard)
      - Includes the prior audit findings verbatim (sanitized)
    """
    failing_name = ld._phase_id_to_human_name(failing_phase)
    parts = [
        f"# Iter {iteration} sub-iter {sub_iter} — peer review patch",
        "",
        f"You are reviewing and revising a patch produced by **{prior_generator}**.",
        f"The patch targeted: {failing_name}.",
        "",
        "## Public API contract (review)",
        public_contract[:6000],
        "",
        f"## What `{prior_generator}` produced (current candidate code)",
        "```python",
        candidate_code,
        "```",
        "",
        f"## Audit findings (Codex GPT-5.5) on `{prior_generator}`'s patch",
        "These are SPECIFIC defects the prior patch introduced or failed to remove.",
        "Address each finding directly:",
    ]
    for finding in prior_audit_findings[:8]:
        parts.append(f"- {finding}")
    parts.append("")
    parts.append("## Regression guard — these phases ARE PASSING; DO NOT BREAK THEM")
    if passing_phases:
        for ph in passing_phases:
            parts.append(f"- {ld._phase_id_to_human_name(ph)}")
    else:
        parts.append("- (none yet)")
    parts.append("")
    # Inject lego references for the failing phase
    lego_block = lego_miner.mine_for_phase(failing_phase, top_k=3)
    if lego_block:
        parts.append(lego_block)
    # Tool patterns
    tool_block = lego_miner.mine_tool_patterns(candidate_code)
    if tool_block:
        parts.append(tool_block)
    parts.extend([
        "",
        "## Binding constraints (audit catches these every iteration)",
        "- 4-qubit carrier; every Qobj from a 16x16 array uses `dims=[[2,2,2,2],[2,2,2,2]]`.",
        "- NO `is_prime(n)` multipliers in engine-derived outputs.",
        "- NO `(...) % N` hash-style modular distinctness offsets.",
        "- NO `canonical = rho_input` (recovery distance must not be tautologically zero).",
        "- NO closed-form returns where the function signature has `n_steps` or integration-implying parameters.",
        "- NO synthetic Fisher matrix templates ignoring `compute_axis_metrics()` outputs.",
        "- NO decorative `import z3` / `cvc5.Solver()` without load-bearing `checkSat()`/assertions.",
        "- NO snap-to-target recovery (blending toward a precomputed reference state and claiming denoising).",
        "- NO hardcoded efficiency constants (`eff = 0.25` etc).",
        "- NO full-identity projectors masquerading as decoherence-free subspaces.",
        "",
        "## What to do",
        "Revise the candidate to address the audit findings WITHOUT regressing any",
        "passing phase. Return ONE python code block — the complete revised module.",
        "",
        "If a finding cannot be honestly resolved, leave that function raising",
        "NotImplementedError. That is preferable to keeping the cheat.",
    ])
    return "\n".join(parts)


def passing_phase_ids(summary: dict) -> list:
    return [p["phase_id"] for p in summary.get("phases", []) if p["pass"]]


def extract_findings(review_text: str) -> list:
    """Parse Codex review text into discrete finding strings."""
    findings = []
    for line in review_text.split("\n"):
        m = re.match(r"^\s*-\s*\[(P[012])\]\s*(.+)", line)
        if m:
            findings.append(f"[{m.group(1)}] {m.group(2).strip()[:200]}")
    return findings


def converged(review_result: dict) -> bool:
    """A patch has converged when the audit reports no P0 or P1."""
    return not review_result.get("has_p0") and not review_result.get("has_p1")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--max-outer-iters", type=int, default=4,
                    help="how many phase-failures to chase forward")
    ap.add_argument("--max-sub-iters", type=int, default=3,
                    help="how many cross-review rounds per phase failure")
    ap.add_argument("--generators", default="codex,grok,gemini",
                    help="comma-separated generator names; cycles through these as cross-reviewers")
    args = ap.parse_args()

    public_contract = (PROMPTS / "public_api_contract.md").read_text()
    candidate_path = Path(args.candidate).resolve()
    generator_names = [g.strip() for g in args.generators.split(",")]

    for outer in range(1, args.max_outer_iters + 1):
        print(f"\n{'#' * 80}\n# OUTER ITER {outer}  candidate={candidate_path.name}\n{'#' * 80}")
        # 1. Run runner; find failing phase
        result = run_runner(candidate_path)
        if result["exit_code"] == 0:
            print(f"\n✓ ALL PHASES PASSED on outer iter {outer}.")
            print(f"  Final candidate: {candidate_path}")
            return
        failing_phase = None
        for p in result["summary"].get("phases", []):
            if not p["pass"]:
                failing_phase = p["phase_id"]
                break
        if not failing_phase:
            print("no failing phase found"); return
        passing = passing_phase_ids(result["summary"])
        print(f"  Failing phase: {failing_phase}    Passing: {len(passing)} phases")

        # 2. Read failure receipt
        run_dir = Path(result["run_dir"])
        receipt = json.loads((run_dir / f"phase_{failing_phase}_results.json").read_text())
        raw_failures = receipt.get("observable", {}).get("failures", [])
        metrics = receipt.get("observable", {}).get("metrics", {})
        sanitized = ld._sanitize_failure_list(raw_failures)

        # 3. Cross-review loop: gen → audit → gen → audit → ... up to max-sub-iters
        prior_findings = []
        prior_gen_name = "(initial candidate)"
        current_candidate = candidate_path

        for sub in range(1, args.max_sub_iters + 1):
            gen_name = generator_names[(sub - 1) % len(generator_names)]
            print(f"\n  --- sub-iter {sub}: {gen_name} reviewing {prior_gen_name}'s work ---")

            # Build prompt
            candidate_code = current_candidate.read_text()
            if sub == 1:
                # First sub-iter: original single-shot prompt (no prior review yet)
                prompt = mml.build_patch_prompt(public_contract, candidate_code, failing_phase,
                                                 sanitized, metrics, outer, [])
            else:
                prompt = build_cross_review_prompt(
                    public_contract, candidate_code, failing_phase,
                    sanitized, metrics, outer, sub,
                    prior_generator=prior_gen_name,
                    prior_audit_findings=prior_findings,
                    passing_phases=passing,
                )
            print(f"     prompt: {len(prompt)} chars")

            # Generate
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            new_path = CANDIDATES / f"candidate_cross_outer{outer:02d}_sub{sub:02d}_{gen_name}_{ts}.py"
            t0 = time.time()
            try:
                if gen_name == "codex":
                    mml.gen_codex(prompt, write_target=new_path)
                else:
                    resp = mml.GENERATORS[gen_name](prompt)
                    code = mml.extract_code(resp)
                    if not code:
                        print(f"     no code extracted, aborting sub-iter")
                        break
                    new_path.write_text(code)
            except Exception as e:
                print(f"     {gen_name} failed: {type(e).__name__}: {str(e)[:150]}")
                break
            print(f"     {gen_name} produced patch in {time.time()-t0:.1f}s")

            # Audit (Codex review)
            print(f"     codex review on {gen_name}'s patch...")
            t0 = time.time()
            review_result = codex_review(new_path)
            (new_path.with_suffix(".codex_review.txt")).write_text(review_result["review_text"])
            print(f"     review in {time.time()-t0:.1f}s — P0={review_result['has_p0']} P1={review_result['has_p1']}")

            # Convergence?
            if converged(review_result):
                print(f"     ✓ converged (no P0/P1) — accepting {gen_name}'s patch")
                current_candidate = new_path
                break

            # Set up next sub-iter
            prior_findings = extract_findings(review_result["review_text"])
            prior_gen_name = gen_name
            current_candidate = new_path

        # End of sub-iters for this outer iter
        candidate_path = current_candidate
        print(f"\n  outer iter {outer} settled on: {candidate_path.name}")

    print(f"\nReached max outer iters ({args.max_outer_iters}). Last candidate: {candidate_path}")


if __name__ == "__main__":
    main()
