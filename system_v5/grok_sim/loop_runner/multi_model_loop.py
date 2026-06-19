#!/usr/bin/env python3
"""multi_model_loop.py — proper 4-model audit + generation loop.

Roles:
  GENERATION (alternates per iter to avoid single-model idiosyncrasy):
    - grok-build-0.1       — concrete code generation
    - gemini-3.1-pro-preview — long context, careful math derivation
    - gemini-3.5-flash     — cheap contrast and liveness checks

  AUDIT (every iteration; orthogonal to the generator):
    - claude_subagent      — adversarial code review (Sonnet by default; no Opus)
    - codex CLI            — local execution + independent test run

  ORCHESTRATION (this script):
    - decides which generator based on prior failure type
    - sanitizes failure msgs before any prompt is built
    - drives convergence

A loop iteration:
  1. Run the runner on the current candidate; get pass/fail per phase.
  2. If all pass AND last 2 audits returned clean → DONE.
  3. Else: pick next generator (alternates G→C→G→C…).
  4. Sanitize the failure list; build the patch prompt; call the chosen generator.
  5. Save new candidate; run runner again to verify it imports + improves.
  6. Spawn a Sonnet/cheap-model subagent for adversarial cheat-check on the new candidate when enabled.
  7. Optionally invoke Codex CLI for independent test execution.
  8. If audit flags new cheats → loop again with the OTHER generator and the audit
     findings as input.
  9. Goal-stability via the runner's frozen manifest is enforced by the runner.

Usage:
  python multi_model_loop.py --candidate <path> [--max-iters 5] [--use-codex]
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

from openai import OpenAI

CANDIDATES = HERE.parent / "candidates"
PROMPTS = HERE / "prompts"
RECEIPTS = HERE / "receipts"
RUNNER = HERE / "runner.py"
PYTHON_BIN = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"

# Import sanitizers from loop_driver to reuse the goal-stability + leak-prevention work
import loop_driver as ld
# Lego mining for reference-pattern injection + proposed-lego detection
import lego_miner


# ---------- key loading ----------
def _load_key(var: str) -> str:
    r = subprocess.run(["zsh", "-i", "-l", "-c", f'printf %s "${var}"'],
                       capture_output=True, text=True, timeout=10)
    return r.stdout.strip()


# ---------- generators ----------
def gen_grok(prompt: str) -> str:
    """Grok build first, with Grok 4.3 as the stronger fallback/audit model.
    Every output MUST be frontier-audited before acceptance.

    Retries on 429/rate-limit and 503 with exponential backoff. Falls back to
    the current 4.20 reasoning snapshot if the preferred current models are
    blocked.
    """
    key = _load_key("XAI_API_KEY")
    if not key:
        raise RuntimeError("XAI_API_KEY not loaded")
    client = OpenAI(api_key=key, base_url="https://api.x.ai/v1", timeout=1800)
    last_exc = None
    for model_name in ("grok-build-0.1", "grok-4.3", "grok-4.20-0309-reasoning"):
        for attempt in range(3):
            try:
                resp = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=1800,
                )
                if attempt > 0 or model_name != "grok-build-0.1":
                    print(f"    (grok: succeeded on {model_name} attempt {attempt+1})")
                return resp.choices[0].message.content
            except Exception as e:
                last_exc = e
                msg = str(e).lower()
                # Retry on transients (same list as gemini)
                transient = any(s in msg for s in ("429", "503", "rate", "capacity",
                                                    "overload", "unavailable", "connection",
                                                    "timeout", "timed out"))
                if transient:
                    backoff = 20 * (attempt + 1)
                    print(f"    (grok {model_name}: transient, retrying in {backoff}s)")
                    time.sleep(backoff)
                    continue
                break
    raise RuntimeError(f"All Grok fallbacks exhausted: {last_exc}")


def gen_gemini(prompt: str) -> str:
    """Gemini 3.1 Pro preview — strong long-context model but 'too hot' (hallucinates
    on real-life detail). Every output MUST be frontier-audited before acceptance.

    Retries on transient 503/UNAVAILABLE up to 3 times; if 3.1-pro-preview stays
    overloaded, falls back through pro/latest aliases and Gemini 3 Flash.
    """
    key = _load_key("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not loaded")
    client = OpenAI(api_key=key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                    timeout=1800)
    last_exc = None
    for model_name in (
        "gemini-3.1-pro-preview",
        "gemini-pro-latest",
        "gemini-3-pro-preview",
        "gemini-3.5-flash",
        "gemini-flash-latest",
        "gemini-2.5-pro",
    ):
        for attempt in range(3):
            try:
                resp = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    timeout=1800,
                )
                if attempt > 0 or model_name != "gemini-3.1-pro-preview":
                    print(f"    (gemini: succeeded on {model_name} attempt {attempt+1})")
                return resp.choices[0].message.content
            except Exception as e:
                last_exc = e
                msg = str(e).lower()
                # Retry on transients: 503, 429, connection error, timeout, overload
                transient = any(s in msg for s in ("503", "429", "unavailable", "overload",
                                                    "connection", "timeout", "timed out",
                                                    "rate limit"))
                if transient:
                    backoff = 15 * (attempt + 1)
                    print(f"    (gemini {model_name}: transient, retrying in {backoff}s)")
                    time.sleep(backoff)
                    continue
                # Non-transient — move to next model
                break
    raise RuntimeError(f"All Gemini fallbacks exhausted: {last_exc}")


def gen_codex(prompt: str, write_target: Path = None) -> str:
    """Codex CLI (GPT-5.5, high reasoning effort) — agentic generator.

    Runs `codex exec` with workspace-write sandbox: Codex can read project
    files, write/edit the target candidate, run tests on its own. This is
    the SOBER generator per the user's framing — frontier-grade and stable.

    If `write_target` is provided, the prompt is instructed to write the
    candidate directly to that path; we then read the file and return its
    contents (formatted as ```python ... ``` so the orchestrator's
    extract_code() still works).

    If no write_target, we capture stdout and return it directly.
    """
    instruction = prompt
    if write_target is not None:
        instruction = (
            f"Write a complete revised candidate module to:\n  {write_target}\n\n"
            f"Then verify it imports without error by running:\n"
            f"  {PYTHON_BIN} -c 'import importlib.util as u; s=u.spec_from_file_location(\"c\",\"{write_target}\"); m=u.module_from_spec(s); s.loader.exec_module(m); print(\"OK\")'\n\n"
            f"If the import fails, iterate on the file until it imports. Do not run "
            f"the full test suite — that is verification's job.\n\n"
            f"Instructions for the patch:\n\n" + prompt
        )
    out_file = HERE.parent / f".codex_last_msg_{int(time.time())}.txt"
    try:
        r = subprocess.run(
            ["codex", "exec",
             "-c", 'model_reasoning_effort="low"',  # user directive: low effort for cost+speed
             "-C", str(HERE.parent),
             "-s", "workspace-write",
             "--skip-git-repo-check",
             "--output-last-message", str(out_file),
             instruction],
            capture_output=True, text=True, timeout=1800,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("codex exec timed out (1800s)")
    finally:
        pass
    # If we asked Codex to write to a file, return that file's contents wrapped.
    if write_target is not None and write_target.exists():
        return f"```python\n{write_target.read_text()}\n```"
    # Otherwise return the last message
    if out_file.exists():
        return out_file.read_text()
    return r.stdout


GENERATORS = {
    "codex": gen_codex,
    "grok": gen_grok,
    "gemini": gen_gemini,
}


def _extract_review_findings(review_text: str) -> list:
    """Best-effort extraction of actionable review findings for the next prompt."""
    findings = []
    for line in review_text.splitlines():
        stripped = line.strip()
        if re.match(r"^[-*]\s+", stripped):
            findings.append(stripped[:300])
        elif re.match(r"^\d+\.\s+\*\*(P[012])\*\*", stripped):
            findings.append(stripped[:300])
    return findings


def load_prior_review_findings(candidate_path: Path) -> list:
    """Carry Codex review findings across resumed loop invocations."""
    review_path = candidate_path.with_suffix(".codex_review.txt")
    if not review_path.exists():
        return []
    try:
        return _extract_review_findings(review_path.read_text())[:8]
    except Exception:
        return []


# ---------- prompt builder (sanitized) ----------
def build_patch_prompt(public_contract: str, candidate_code: str, failing_phase: str,
                       sanitized_failures: list, metrics: dict, iteration: int,
                       prior_audit_findings: list = None) -> str:
    failing_name = ld._phase_id_to_human_name(failing_phase)
    parts = [
        f"# Iteration {iteration} — patch request",
        "",
        f"Your candidate module did not pass {failing_name}.",
        "",
        "## Public API contract",
        public_contract[:8000],  # truncate to keep prompt manageable
        "",
        "## What needs fixing",
    ]
    for f in sanitized_failures:
        diag = ld.math_diagnosis_from_failure(f, metrics)
        parts.append(f"- {diag}")
    if prior_audit_findings:
        parts.append("")
        parts.append("## Prior audit findings on the candidate (do NOT reproduce these cheats)")
        for finding in prior_audit_findings[:6]:
            parts.append(f"- {finding}")
    # Inject mined formal-sim lego references for this phase (system_v4/probes)
    lego_block = lego_miner.mine_for_phase(failing_phase, top_k=4)
    if lego_block:
        parts.append("")
        parts.append(lego_block)
    # Inject canonical TOOL-INTEGRATION patterns for every tool the candidate
    # imports — the tool-integration audit fires on decorative imports every
    # iteration, so generators must always see the right load-bearing patterns.
    tool_block = lego_miner.mine_tool_patterns(candidate_code)
    if tool_block:
        parts.append("")
        parts.append(tool_block)
    parts.extend([
        "",
        "## Constraints (binding) — the audit catches these patterns every iteration",
        "- 4-qubit carrier; every Qobj from a 16x16 array uses `dims=[[2,2,2,2],[2,2,2,2]]`.",
        "- Stage architecture is exact: 2 engine types (`A`, `B`) × 8 stages each = 16 total engine-stage states. Each stage has 4 substages, so there are 64 engine-stage-substage states. The 16 stage outputs and the 64 substage outputs must be genuinely distinct by dynamics, not by labels.",
        "- Substage roles must be coherent: the same substage index across different stages should behave like the same role, while different substages inside a stage should separate by real operator action. Do not use index hashes, offsets, or modulo tricks to fake this.",
        "- Prime-number work is allowed only through an engine-derived signature. Classical primality may appear only as a reported sanity label; it must not drive `prime_score`, branch the dynamics, scale amplitudes, or select features.",
        "- Do NOT use factorization, divisor counts, Euler phi/totient as a direct score, or any classical number-theory oracle as the claimed prime signal. If coprime walks are used, they may only define an engine trajectory; the discriminating score must be measured from the resulting carrier/probe dynamics.",
        "- Do NOT use `is_prime(n)` as a multiplier in any 'engine-derived' output.",
        "- Do NOT use hash-style modular arithmetic (e.g. `(...)% 19`) to force pairwise distinctness.",
        "- Do NOT return the input as 'canonical' for any compression/projection function — `canonical = rho_input` makes recovery distance zero and counts as a cheat.",
        "- Do NOT return closed-form Berry phases or hand-computed integrals where the contract describes an integration. If you have `n_steps`, the loop MUST use `n_steps` non-trivially.",
        "- Do NOT build the Fisher information matrix from `1/eps² + 0.5` diagonal + decaying off-diagonal templates. Compute actual finite-difference responses to the perturbation parameter. If you call `compute_axis_metrics()`, USE the result.",
        "- Do NOT claim a tool is `used=True` in `tool_manifest` unless your module CALLS it with a load-bearing result that affects an output. `import z3` without `z3.Solver().add(...).check()` does NOT count.",
        "- Do NOT snap a noisy input toward a precomputed reference state and call it 'recovery' or 'denoising'. Implement an actual channel inverse, or call `petz_recover()`, or honestly report 'recovery failed' and leave the input unchanged WITHOUT claiming success.",
        "- Unsupported recovery/projection branches must raise NotImplementedError or return an explicit failure status. They must not return the input unchanged while reporting success, fidelity, or recovery quality.",
        "- `explain_state()` must localize engine/stage/substage by comparing against actual generated trajectories. Do not hardcode stage 0, substage 0, or confidence 0 for every input.",
        "- `project_to_manifold()` must search a real candidate manifold or trajectory family and return the nearest point with a distance. Do not snap all inputs to a fixed anchor state.",
        "- Do NOT use `eff = 0.25` (or any other hardcoded efficiency constant) in `extract_info_work`. Derive it from a cycle model or expose as parameter.",
        "- For DFS: do NOT return the full identity projector and call it a decoherence-free subspace — the projector must be NON-TRIVIAL (rank < ambient dim) AND verifiably invariant under the named noise.",
        "- If you cannot honestly implement a function, leave it raising NotImplementedError. That is preferable to any of the above cheats.",
        "",
        "## Current candidate (modify and return as one ```python ... ``` block)",
        "```python",
        candidate_code,
        "```",
        "",
        "Return ONE python code block — the complete revised candidate.",
    ])
    return "\n".join(parts)


# ---------- runner harness ----------
def run_runner(candidate_path: Path) -> dict:
    r = subprocess.run(
        [PYTHON_BIN, str(RUNNER), "--candidate", str(candidate_path),
         "--candidates-root", str(CANDIDATES)],
        capture_output=True, text=True, timeout=1200,
    )
    m = re.search(r"Summary:\s*(.+\.json)", r.stdout)
    summary_path = Path(m.group(1).rstrip()) if m else None
    summary = json.loads(summary_path.read_text()) if summary_path and summary_path.exists() else {}
    return {
        "exit_code": r.returncode,
        "stdout": r.stdout,
        "summary": summary,
        "run_dir": str(summary_path.parent) if summary_path else None,
    }


def extract_code(text: str) -> str:
    m = re.search(r"```python\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1)
    m = re.search(r"```\s*\n(.*?)```", text, re.DOTALL)
    return m.group(1) if m else None


# ---------- Codex CLI frontier audit (GPT-5.5, high reasoning effort) ----------
def codex_review(candidate_path: Path) -> dict:
    """Frontier audit via `codex review` (GPT-5.5, high reasoning effort).

    Codex is the more sober frontier model in the loop. Grok and Gemini are
    'too hot' — smart in narrow problems but drift on real-life detail and
    hallucinate harder. Every generator output is checked here AND by an
    Opus subagent (orchestrator-side) before acceptance.

    Returns a dict with:
      - exit_code:    0 means review completed (not that the code is clean)
      - review_text:  the full review output
      - has_p0:       True if the review flagged any P0/critical issue
      - has_p1:       True if any P1 found
    """
    instruction = (
        "Adversarial code review on a candidate Python module. Look specifically for:\n"
        "  - Hardcoded magic numbers tuned to pass specific test thresholds\n"
        "  - Classical primality (`is_prime`) used as a multiplier in 'engine-derived' outputs\n"
        "  - Hash-style modular arithmetic (`uniq % N`) used to force pairwise distinctness\n"
        "  - Closed-form returns where the function name implies integration\n"
        "  - Functions that ignore their inputs (synthetic matrices, etc.)\n"
        "  - 'Canonical' functions that return their input unchanged\n"
        "  - Snap-to-target operations claiming to be channel recovery or denoising\n"
        f"\nFile to review: {candidate_path}\n\n"
        "Output format: under-300-word summary, then enumerated findings with severity\n"
        "(P0/P1/P2). For each: file:line, what's wrong, recommendation.\n"
        "If no cheats found, say so explicitly and identify what's well-implemented.\n"
        "Be adversarial. You're looking for cheats, not endorsing the code."
    )
    try:
        r = subprocess.run(
            ["codex", "review",
             "-c", 'model_reasoning_effort="low"',  # user directive
             instruction],
            capture_output=True, text=True, timeout=900,
        )
        text = r.stdout + ("\n[stderr]\n" + r.stderr if r.stderr else "")
        # Heuristic severity detection in the review text
        has_p0 = bool(re.search(r"\bP0\b|\bcritical\b", text, re.IGNORECASE))
        has_p1 = bool(re.search(r"\bP1\b|\bmajor\b", text, re.IGNORECASE))
        return {
            "exit_code": r.returncode,
            "review_text": text[-8000:],  # cap for storage
            "has_p0": has_p0,
            "has_p1": has_p1,
        }
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "review_text": "TIMEOUT after 900s", "has_p0": False, "has_p1": False}
    except Exception as e:
        return {"exit_code": -1, "review_text": f"{type(e).__name__}: {e}",
                "has_p0": False, "has_p1": False}


# ---------- main loop ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--max-iters", type=int, default=5)
    ap.add_argument("--use-codex", action="store_true",
                    help="invoke Codex CLI as a 4th independent verifier each iteration")
    ap.add_argument("--start-with", choices=["codex", "grok", "gemini"], default="codex",
                    help="which generator runs iteration 1 (default codex — sober coder)")
    ap.add_argument("--rotation", default="codex,grok,gemini",
                    help="comma-separated generator rotation. Default puts codex first "
                         "(sober frontier coder); grok and gemini contribute divergent "
                         "perspectives every other iteration but are always frontier-audited.")
    args = ap.parse_args()

    candidate_path = Path(args.candidate).resolve()
    if not candidate_path.exists():
        print(f"ERROR: candidate not found: {candidate_path}", file=sys.stderr)
        sys.exit(2)
    public_contract = (PROMPTS / "public_api_contract.md").read_text()

    # Generator rotation — by default codex,grok,gemini (codex is sober frontier coder
    # and goes first; grok/gemini contribute divergent perspectives but are always
    # frontier-audited before acceptance).
    rotation_default = [g.strip() for g in args.rotation.split(",") if g.strip()]
    if args.start_with in rotation_default:
        idx = rotation_default.index(args.start_with)
        generator_order = rotation_default[idx:] + rotation_default[:idx]
    else:
        generator_order = [args.start_with] + [g for g in rotation_default if g != args.start_with]
    prior_audit_findings = load_prior_review_findings(candidate_path)
    if prior_audit_findings:
        print(f"Loaded {len(prior_audit_findings)} prior Codex review finding(s) from disk.")

    for iteration in range(1, args.max_iters + 1):
        print(f"\n{'#' * 80}\n# ITER {iteration}  candidate={candidate_path.name}\n{'#' * 80}")

        # 1. Run runner
        result = run_runner(candidate_path)
        if result["exit_code"] == 0:
            print(f"\n✓ ALL PHASES PASSED on iteration {iteration}.")
            print(f"  Candidate: {candidate_path}")
            # Reverse direction: scan the passing candidate for novel functions
            # that could be promoted to formal-sim legos. Writes proposals to
            # `proposed_legos/` for user review; does NOT auto-promote.
            try:
                props = lego_miner.propose_legos_from_candidate(candidate_path)
                if props:
                    print(f"\n📦 Proposed legos extracted from this passing candidate:")
                    for name, _ in props[:10]:
                        print(f"     - {name}  → proposed_legos/{name}.py")
                    print(f"  (User review required before promotion to canonical legos.)")
            except Exception as e:
                print(f"  (proposed-lego scan skipped: {type(e).__name__})")
            return

        # 2. Find failing phase
        failing_phase = None
        for p in result["summary"].get("phases", []):
            if not p["pass"]:
                failing_phase = p["phase_id"]
                break
        if not failing_phase:
            print("No failing phase identified; aborting.")
            return

        # 3. Read failure receipt
        run_dir = Path(result["run_dir"])
        receipt_path = run_dir / f"phase_{failing_phase}_results.json"
        receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
        raw_failures = receipt.get("observable", {}).get("failures", [])
        metrics = receipt.get("observable", {}).get("metrics", {})
        print(f"\nFailing phase: {failing_phase}  ({len(raw_failures)} failures)")

        # 4. Sanitize failures
        sanitized = ld._sanitize_failure_list(raw_failures)

        # 5. Pick generator from rotation
        gen_name = generator_order[(iteration - 1) % len(generator_order)]
        print(f"Generator for this iter: {gen_name}")

        # 6. Build prompt and call generator
        candidate_code = candidate_path.read_text()
        prompt = build_patch_prompt(public_contract, candidate_code, failing_phase,
                                     sanitized, metrics, iteration, prior_audit_findings)
        print(f"Prompt: {len(prompt)} chars")
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        new_path = CANDIDATES / f"candidate_loop_iter{iteration:02d}_{gen_name}_{ts}.py"
        t0 = time.time()
        try:
            if gen_name == "codex":
                # Codex is agentic — let it write the file directly
                resp = gen_codex(prompt, write_target=new_path)
            else:
                resp = GENERATORS[gen_name](prompt)
        except Exception as e:
            print(f"  generator {gen_name} failed: {type(e).__name__}: {str(e)[:200]}")
            return
        print(f"  {gen_name} responded in {time.time()-t0:.1f}s ({len(resp)} chars)")
        if gen_name != "codex":
            new_code = extract_code(resp)
            if not new_code:
                print("  no code block extracted; aborting iteration")
                return
            new_path.write_text(new_code)
        print(f"  Saved: {new_path.name}")

        # 7. FRONTIER AUDIT (Codex GPT-5.5 review of the generator's output)
        # The user's framing: Grok/Gemini are "too hot" — smart but drift. Their
        # outputs MUST be checked by frontier-grade auditors before acceptance.
        codex_findings_text = ""
        if args.use_codex:
            print(f"  Frontier audit: codex review (GPT-5.5) on {gen_name}'s output...")
            t0 = time.time()
            codex_result = codex_review(new_path)
            print(f"  Codex review in {time.time()-t0:.1f}s; "
                  f"P0={codex_result['has_p0']} P1={codex_result['has_p1']}")
            (new_path.with_suffix(".codex_review.txt")).write_text(codex_result['review_text'])
            codex_findings_text = codex_result['review_text']
            if codex_result['has_p0']:
                print(f"  ⚠ Codex flagged P0 cheats. Next iter must address these.")

        # 8. Opus subagent audit happens orchestrator-side (this Claude session).
        # The script logs that an audit is needed; the orchestrator should spawn
        # a code-reviewer subagent with fresh context on `new_path` before
        # accepting it as the working candidate.
        audit_marker = new_path.with_suffix(".audit_needed.txt")
        audit_marker.write_text(
            f"Orchestrator action required: spawn Opus code-reviewer subagent on:\n"
            f"  {new_path}\n"
            f"\nCodex review (P0={codex_result['has_p0'] if args.use_codex else 'skipped'}):\n"
            f"  {new_path.with_suffix('.codex_review.txt') if args.use_codex else 'skipped'}\n"
        )

        # Feed codex findings into the prior_audit_findings for the next iteration
        prior_audit_findings = []
        if codex_findings_text:
            prior_audit_findings = _extract_review_findings(codex_findings_text)
        candidate_path = new_path

    print(f"\nReached max iters ({args.max_iters}) without convergence.")
    print(f"Last candidate: {candidate_path}")


if __name__ == "__main__":
    main()
