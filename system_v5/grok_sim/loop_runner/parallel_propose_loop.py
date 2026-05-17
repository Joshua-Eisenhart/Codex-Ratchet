#!/usr/bin/env python3
"""parallel_propose_loop.py — Grok+Gemini propose in parallel, Codex picks.

Roles:
  Grok (4.3)         — hot generator. Hallucinates freely. Proposes patches.
  Gemini (3.1-pro)   — hot generator. Hallucinates freely. Proposes patches.
  Codex (GPT-5.5)    — sober judge. Picks the better of the two proposals,
                       or notes which is closer to a real fix. Does NOT
                       generate primary code.

Per outer iteration:
  1. Run runner. Find failing phase + failure count.
  2. Build a SHORT prompt (failing phase + math intent + lego refs).
  3. Send the SAME prompt to Grok and Gemini in parallel (one shot each).
  4. Codex compares the two proposals on:
     - Does it actually address the failing-phase math?
     - Does it avoid the known cheats?
     - Does it preserve the currently-passing phases?
     Codex picks the better one OR rejects both.
  5. Apply Codex's pick. Re-run runner.
  6. Did we advance? (Passed the failing phase, OR reduced its failure count,
     OR reached a deeper phase.) If yes: keep candidate. If no: try again
     with feedback or give up on this phase.

Advance metric — NOT "no audit findings." We advance whenever the runner shows
forward motion. Audit findings become future-iteration work, not blockers.
"""
import argparse
import concurrent.futures
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

# Ordered list of phases by file name — used to measure "advance"
def all_phase_ids():
    contracts = sorted((HERE / "contracts").glob("phase_*.py"))
    return [p.stem.replace("phase_", "") for p in contracts]


def position_in_order(phase_id: str) -> int:
    order = all_phase_ids()
    try:
        return order.index(phase_id)
    except ValueError:
        return -1


def build_propose_prompt(public_contract: str, candidate_code: str, failing_phase: str,
                          sanitized_failures: list, metrics: dict, passing_phases: list) -> str:
    """Short prompt for Grok+Gemini. Names the failing phase abstractly,
    lists currently-passing phases as a preserve-list."""
    failing_name = ld._phase_id_to_human_name(failing_phase)
    parts = [
        f"# Patch the candidate for {failing_name}",
        "",
        "## What the audit observed (math-level)",
    ]
    for f in sanitized_failures:
        parts.append(f"- {ld.math_diagnosis_from_failure(f, metrics)}")
    parts.append("")
    parts.append("## Phases currently passing — must remain passing")
    for ph in passing_phases:
        parts.append(f"- {ld._phase_id_to_human_name(ph)}")
    parts.append("")
    # Lego refs
    lego_block = lego_miner.mine_for_phase(failing_phase, top_k=3)
    if lego_block:
        parts.append(lego_block)
    tool_block = lego_miner.mine_tool_patterns(candidate_code)
    if tool_block:
        parts.append(tool_block)
    parts.extend([
        "",
        "## Hard rules",
        "- 4-qubit carrier; Qobjs use `dims=[[2,2,2,2],[2,2,2,2]]`.",
        "- NO classical-primality multipliers, hash-style distinctness, identity canonicals,",
        "  closed-form Berry phases, synthetic Fisher matrices, decorative z3/cvc5,",
        "  snap-to-target denoising, hardcoded thermodynamic efficiency.",
        "- If you can't honestly implement, raise NotImplementedError (don't cheat).",
        "",
        "## Current candidate",
        "```python",
        candidate_code,
        "```",
        "",
        "Return ONE python code block with the revised candidate.",
    ])
    return "\n".join(parts)


def build_judge_prompt(grok_path: Path, gemini_path: Path, failing_phase: str) -> str:
    """Codex sees both proposals and is asked to pick or merge."""
    return (
        "You are the sober judge. Two hallucinator-class generators (Grok-4.3 and "
        "Gemini-3.1-pro) each produced a patch for the same failing phase: "
        f"{ld._phase_id_to_human_name(failing_phase)}.\n\n"
        f"Grok's proposal:    {grok_path}\n"
        f"Gemini's proposal:  {gemini_path}\n\n"
        "Compare the two files head-to-head. For the function(s) targeted by the "
        "failing phase, decide which proposal is CLOSER to an honest implementation. "
        "Reject either if it cheats (classical-primality multiplier, hash-style "
        "distinctness, identity canonical, closed-form Berry, synthetic Fisher, "
        "decorative tools, snap-to-target, hardcoded efficiency).\n\n"
        "Write your decision to a file at /tmp/codex_judge_decision.txt with:\n"
        "  Line 1: GROK or GEMINI or REJECT_BOTH\n"
        "  Lines 2+: 5-15 lines of reasoning\n"
        "After writing the decision file, also run a small validation: import the "
        "winning candidate and confirm it imports without error, then write the "
        "import status to /tmp/codex_judge_import_status.txt.\n"
        "Do not edit either proposal file. Read-only comparison + write the decision."
    )


def parallel_propose(prompt: str) -> tuple:
    """Call Grok and Gemini in parallel. Returns (grok_code, gemini_code).
    Either may be None if the call fails."""
    results = {"grok": None, "gemini": None}
    def call_grok():
        try: results["grok"] = mml.gen_grok(prompt)
        except Exception as e: print(f"  grok failed: {type(e).__name__}: {str(e)[:120]}")
    def call_gemini():
        try: results["gemini"] = mml.gen_gemini(prompt)
        except Exception as e: print(f"  gemini failed: {type(e).__name__}: {str(e)[:120]}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        f_g = ex.submit(call_grok)
        f_m = ex.submit(call_gemini)
        f_g.result(timeout=1800)
        f_m.result(timeout=1800)
    return results["grok"], results["gemini"]


def codex_judge(grok_path: Path, gemini_path: Path, failing_phase: str) -> str:
    """Returns 'grok', 'gemini', or 'reject'."""
    decision_file = Path("/tmp/codex_judge_decision.txt")
    if decision_file.exists():
        decision_file.unlink()
    instruction = build_judge_prompt(grok_path, gemini_path, failing_phase)
    try:
        r = subprocess.run(
            ["codex", "exec",
             "-c", 'model_reasoning_effort="low"',
             "-C", str(HERE.parent),
             "-s", "workspace-write",
             "--skip-git-repo-check",
             instruction],
            capture_output=True, text=True, timeout=900,
        )
    except Exception as e:
        print(f"  codex judge failed: {type(e).__name__}: {str(e)[:120]}")
        return "grok"   # default to grok if judge crashes
    if decision_file.exists():
        first = decision_file.read_text().split("\n")[0].strip().upper()
        if "GROK" in first: return "grok"
        if "GEMINI" in first: return "gemini"
        if "REJECT" in first: return "reject"
    # Fallback heuristic
    return "grok"


def advance_score(summary: dict) -> tuple:
    """Returns (deepest_passed_phase_position, count_failing_at_first_failure).
    Higher position = further along. Lower failing-count = closer to passing."""
    phases = summary.get("phases", [])
    last_pass_pos = -1
    first_fail_count = 0
    for p in phases:
        if p["pass"]:
            last_pass_pos = position_in_order(p["phase_id"])
        else:
            # Could read receipt for failure count, but use 1 as placeholder
            first_fail_count = 1
            break
    return last_pass_pos, first_fail_count


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--max-iters", type=int, default=4)
    args = ap.parse_args()

    public_contract = (PROMPTS / "public_api_contract.md").read_text()
    candidate_path = Path(args.candidate).resolve()

    for it in range(1, args.max_iters + 1):
        print(f"\n{'#' * 80}\n# ITER {it}  candidate={candidate_path.name}\n{'#' * 80}")
        result = mml.run_runner(candidate_path)
        if result["exit_code"] == 0:
            print(f"\n✓ ALL PHASES PASSED. Final: {candidate_path}")
            return
        failing_phase = None
        for p in result["summary"].get("phases", []):
            if not p["pass"]:
                failing_phase = p["phase_id"]; break
        if not failing_phase:
            print("no failing phase"); return
        passing = [p["phase_id"] for p in result["summary"].get("phases", []) if p["pass"]]
        before_score = advance_score(result["summary"])
        print(f"  Failing phase: {failing_phase}  Passing: {len(passing)} phases  pos={before_score[0]}")

        # Build prompt
        run_dir = Path(result["run_dir"])
        receipt = json.loads((run_dir / f"phase_{failing_phase}_results.json").read_text())
        raw_failures = receipt.get("observable", {}).get("failures", [])
        metrics = receipt.get("observable", {}).get("metrics", {})
        sanitized = ld._sanitize_failure_list(raw_failures)
        candidate_code = candidate_path.read_text()
        prompt = build_propose_prompt(public_contract, candidate_code, failing_phase,
                                       sanitized, metrics, passing)
        print(f"  Prompt: {len(prompt)} chars; calling Grok + Gemini in parallel...")

        t0 = time.time()
        grok_resp, gemini_resp = parallel_propose(prompt)
        print(f"  Both proposals returned in {time.time()-t0:.1f}s")

        # Save proposals
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        grok_path = gemini_path = None
        if grok_resp:
            code = mml.extract_code(grok_resp)
            if code:
                grok_path = CANDIDATES / f"candidate_proposal_iter{it:02d}_grok_{ts}.py"
                grok_path.write_text(code)
                print(f"  Grok proposal: {grok_path.name}")
        if gemini_resp:
            code = mml.extract_code(gemini_resp)
            if code:
                gemini_path = CANDIDATES / f"candidate_proposal_iter{it:02d}_gemini_{ts}.py"
                gemini_path.write_text(code)
                print(f"  Gemini proposal: {gemini_path.name}")

        # Codex judges
        if grok_path and gemini_path:
            print(f"  Codex judging...")
            t0 = time.time()
            decision = codex_judge(grok_path, gemini_path, failing_phase)
            print(f"  Codex decision in {time.time()-t0:.1f}s: {decision}")
            if decision == "grok":
                new_candidate = grok_path
            elif decision == "gemini":
                new_candidate = gemini_path
            else:
                print(f"  Both rejected. Keeping current candidate.")
                continue
        elif grok_path:
            print(f"  Only Grok succeeded — using Grok proposal")
            new_candidate = grok_path
        elif gemini_path:
            print(f"  Only Gemini succeeded — using Gemini proposal")
            new_candidate = gemini_path
        else:
            print(f"  Both generators failed; aborting iter")
            continue

        # Did we advance? Check by running runner on new candidate
        print(f"  Validating advancement via runner on {new_candidate.name}...")
        new_result = mml.run_runner(new_candidate)
        if new_result["exit_code"] == 0:
            print(f"  ✓ ALL PASSING after this iteration!")
            candidate_path = new_candidate
            return
        after_score = advance_score(new_result["summary"])
        advanced = after_score[0] > before_score[0]
        print(f"  pos_before={before_score[0]} pos_after={after_score[0]}  advanced={advanced}")
        if advanced:
            candidate_path = new_candidate
            print(f"  → advanced; new baseline = {new_candidate.name}")
        else:
            # No advance — keep best so far. Could retry, but for now just continue.
            print(f"  → no advance; keeping prior candidate")

    print(f"\nReached max-iters ({args.max_iters}). Final: {candidate_path}")


if __name__ == "__main__":
    main()
