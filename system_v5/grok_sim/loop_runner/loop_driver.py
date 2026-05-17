#!/usr/bin/env python3
"""loop_driver.py — full Grok+Opus+Runner loop with goal-stability + formal-sim references.

Each iteration:
  1. Run the fixed runner on the current candidate
  2. Read the receipts
  3. If all phases pass, stop
  4. Else: Opus translates failures to math diagnosis (no regex citations)
  5. Build Teacher prompt with public API contract + current candidate + math diagnosis
     + relevant formal-sim references
  6. Call Grok 4.3
  7. Save new candidate, loop

Roles enforced:
  - Runner owns acceptance (here: subprocess on runner.py)
  - Opus owns translation (math_diagnosis_from_failure)
  - Grok owns generation (xAI API call)
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import shutil
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

THIS_DIR = Path(__file__).parent
SIM_DIR = THIS_DIR.parent
CANDIDATES_DIR = SIM_DIR / "candidates"
RECEIPTS_DIR = THIS_DIR / "receipts"
PROMPTS_DIR = THIS_DIR / "prompts"
PYTHON_BIN = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"
RUNNER = THIS_DIR / "runner.py"

# Repo-relative path for formal-sim references (read-only by Grok)
REPO_ROOT = SIM_DIR.parent.parent  # /Users/joshuaeisenhart/Desktop/Codex Ratchet
FORMAL_SIMS = REPO_ROOT / "system_v4" / "probes"


# Map phase id stem to a human-readable phase name (no phase numbers leaked)
PHASE_HUMAN_NAMES = {
    "00_smoke": "the smoke phase (basic API surface)",
    "01_axioms": "the foundational-axioms phase",
    "02_gstack": "the geometric-stack phase",
    "03_axes": "the 7-axis-decomposition phase",
    "04_smt_cross_check": "the SMT cross-check phase",
    "05_engine_traversal": "the engine-traversal phase",
    "06_tool_integration": "the tool-integration phase",
    "07_engine_coupling": "the engine-coupling phase",
    "08_claim_fence": "the side-quest-fence phase",
    "09_lie_bracket_recompute": "the Lie-bracket recomputation phase",
    "10_entropy_monotonicity": "the entropy-monotonicity phase",
    "11_replay_determinism": "the replay-determinism phase",
    "12_stage_enumeration": "the stage-enumeration phase",
    "13_axis_engine_consistency": "the axis/engine-consistency phase",
    "14_summary_receipt": "the summary-receipt phase",
    "15_szilard_work_extraction": "the information-work-extraction phase",
    "16_axis_as_info_processor": "the axis-as-information-processor phase",
    "17_fisher_information": "the Fisher-information phase",
    "18_iching_hexagram": "the 6-bit-hexagram bijection phase",
    "19_terrain_operations": "the terrain-operation phase",
    "20_16stages_4substages": "the 16-stages × 4-substages enumeration phase",
    "22_probe_quotient_compression": "the probe-quotient compression phase",
    "23_holonomic_gate": "the holonomic-gate phase",
    "24_decoherence_free_subspace": "the decoherence-free-subspace phase",
    "25_petz_recovery": "the Petz-recovery phase",
    "26_unified_ai_tool_surface": "the unified-AI-tool-surface phase",
    "27_prime_scaling": "the prime-resonance scaling phase",
    "28_stage_semantic_uniqueness": "the stage-semantic-uniqueness phase",
    "29_prime_scaling_extreme": "the extended prime-resonance phase",
    "30_stage_trajectory": "the stage-trajectory structure phase",
    "31_constraint_manifold": "the constraint-manifold rank phase",
    "32_axis_cliff": "the axis-cliff-structure phase",
    "33_state_classifier": "the state-classifier capability phase",
    "34_classifier_robustness": "the classifier-robustness phase",
    "35_composability_and_noncommutation": "the composability and non-commutation phase",
    "36_noncommutation_structural_vs_noise": "the structural-vs-noise non-commutation phase",
    "37_interpretability": "the state-interpretability phase",
    "38_explain_confidence_honesty": "the confidence-calibration phase",
    "39_prime_classifier_chain": "the prime/classifier chained-pipeline phase",
    "40_prime_chain_wide": "the wider prime/classifier chain phase",
    "41_factorization_attempt": "the factorization-attempt phase",
    "42_factorization_wide": "the extended-range factorization phase",
    "43_denoise_pipeline": "the in-distribution denoise-pipeline phase",
    "44_denoise_ood": "the out-of-distribution denoise phase",
    "45_universal_denoise": "the open-system (manifold-projection) denoise phase",
    "98_prime_resonance_via_totient": "the prime-resonance via totient phase",
    "46_constraint_manifold_foundation": "the constraint-manifold foundation phase",
    "47_gstack_layered_entropy": "the layered g-stack entropy-restriction phase",
}


def _phase_id_to_human_name(phase_id: str) -> str:
    """Return a human-readable name for a phase id, never leaking the phase number.
    The fallback intentionally does NOT interpolate `phase_id` — that would leak
    the phase number for any contract not present in PHASE_HUMAN_NAMES."""
    if not phase_id:
        return "a required architectural phase"
    return PHASE_HUMAN_NAMES.get(phase_id, "a required architectural phase")


# Map failure categories to formal-sim references
SIM_REFERENCES_BY_FAILURE = {
    "finitude_varies":      ["sim_pytorch_density_entropy_gradient_micro.py", "qit_partial_trace.py"],
    "finitude_stable":      ["sim_pytorch_capability.py"],
    "finitude_witness_int": ["sim_pytorch_capability.py"],
    "noncomm_distinguishable":   ["sim_weyl_a2_su3_noncommutativity.py", "sim_clifford_spinor_double_cover_micro.py"],
    "noncomm_recompute_matches": ["sim_pytorch_density_entropy_gradient_micro.py"],
    "mequiv_must_be_distinct":   ["sim_clifford_spinor_double_cover_micro.py"],
    "mequiv_must_share_class":   ["qit_partial_trace.py"],
    "function_exists_":     [],
    "return_type_":         [],
    # G-stack failures
    "weyl_opposite_signs":  ["sim_clifford_spinor_double_cover_micro.py", "dual_weyl_spinor_engine_sim.py"],
    "weyl_L_z_magnitude":   ["dual_weyl_spinor_engine_sim.py"],
    "weyl_R_z_magnitude":   ["dual_weyl_spinor_engine_sim.py"],
    "hopf_psi_L_at_north":  ["hopf_manifold.py"],
    "hopf_psi_R_at_south":  ["hopf_manifold.py"],
    "flux_nonzero":         ["sim_axis_hopf_geometry.py", "sim_assoc_bundle_canonical_connection_from_hopf.py"],
    "gstack_dependencies":  ["sim_gstack_associated_bundle_shell_local.py"],
    "gstack_layer_":        ["sim_gstack_associated_bundle_shell_local.py"],
    "clifford_products":    ["sim_clifford_spinor_double_cover_micro.py", "sim_clifford_fiber_assoc_symplectic_coupling_canonical.py"],
    # Axis failures
    "axis_below_threshold_": ["sim_both_engines_axes_0_to_7_z3_cvc5_structural_guard.py"],
    "axis_deterministic_":   ["sim_pytorch_density_entropy_gradient_micro.py"],
}


def find_relevant_sim_refs(failures):
    """Map each failure's check id to a list of relevant formal sims.
    Reads either `check` or `_raw_check` so it works on both raw and sanitized failures."""
    refs = set()
    for f in failures:
        check = f.get("_raw_check") or f.get("check", "")
        for prefix, sim_list in SIM_REFERENCES_BY_FAILURE.items():
            if check.startswith(prefix) or prefix in check:
                refs.update(sim_list)
    # Filter to ones that exist in repo
    valid = []
    for sim_name in refs:
        if (FORMAL_SIMS / sim_name).exists():
            valid.append(sim_name)
    return valid


# Opus's diagnostic patterns — translate audit failures to math language (no regex)
def math_diagnosis_from_failure(failure: dict, metrics: dict) -> str:
    """Translate one audit failure into plain-math diagnosis Grok can act on.
    Goal: tell Grok WHY this math goal isn't met. Do NOT mention regex, thresholds,
    or the audit's literal pass criterion."""
    # Accept either a raw failure dict or a sanitized one (with `_raw_check`).
    check = failure.get("_raw_check") or failure.get("check", "")
    msg = failure.get("msg", "")

    if check == "finitude_varies":
        # Extract observed value(s) from msg for honest reporting
        m = re.search(r"\(([\d.eE+-]+)\)", msg)
        observed = m.group(1) if m else "constant"
        return (
            f"`finite_witness(n)` returns {observed} regardless of the truncation "
            f"parameter `n`. A witness that doesn't depend on `n` isn't witnessing "
            f"the finiteness — it's a constant of the dynamics. "
            f"To fix: change the computation so the witness's integer value tracks "
            f"the truncation level. Possible approaches: "
            f"(a) count the number of distinct eigenvalues at threshold scaled by `n`, "
            f"(b) use a step-counter ancilla qubit and project on its |1⟩ population "
            f"after `n` steps, "
            f"(c) make the dynamics weaker per step so saturation happens at large `n`, "
            f"not n=4. The current implementation reaches a 4-dim fixed point too "
            f"quickly — slow the per-step evolution or change the saturating subspace."
        )

    if check == "finitude_stable":
        return (
            "`finite_witness(n)` is non-deterministic — same `n` produces different "
            "values across calls. The witness must be reproducible. Remove any "
            "random initialization; use a fixed seed if randomness is needed."
        )

    if check == "noncomm_distinguishable":
        td = metrics.get("noncommutation", {}).get("trace_distance", "near zero")
        return (
            f"The trace distance between A∘B applied to ρ and B∘A applied to ρ is "
            f"{td}, which is too small to register as genuine non-commutation. "
            f"Common causes: (i) A and B both rotate around the same Pauli axis "
            f"(same generator commutes with itself), (ii) the initial state is in "
            f"the joint eigenspace of A and B, (iii) A and B act on disjoint qubit "
            f"subspaces (tensor-product operators on disjoint factors commute). "
            f"Pick A on σ_x and B on σ_y of the SAME qubit, with an initial state "
            f"that's not a σ_x or σ_y eigenstate."
        )

    if check == "noncomm_recompute_matches":
        return (
            "The trace_distance reported by your `noncomm_pair()` doesn't match what "
            "the runner gets when it independently recomputes the trace distance via "
            "SVD of `rho_seq_AB - rho_seq_BA`. Either the reported value is computed "
            "from different objects than the returned tensors, or there's a "
            "normalization issue. Recompute the trace distance from the ρs you're "
            "actually returning."
        )

    if check == "mequiv_must_be_distinct":
        return (
            "Your M-equivalence demo returns ρ_a and ρ_b that ARE element-wise equal. "
            "The whole point is to show that distinct density matrices can share a "
            "probe-class label. Pick ρ_a and ρ_b that differ in some way the chosen "
            "M_ops can't detect — e.g., differ in a qubit that M_ops doesn't probe."
        )

    if check == "mequiv_must_share_class":
        return (
            "Your M-equivalence demo returns ρ_a and ρ_b whose probe classes (tuples "
            "of expectation values under M_ops) are DIFFERENT. The point is to show "
            "they're the same. Either change which M_ops you use, or change which ρs "
            "you compare. Concrete choice: M_ops should NOT probe the qubit where ρ_a "
            "and ρ_b differ; then their probe classes will agree."
        )

    if check.startswith("function_exists_"):
        fn_name = check.replace("function_exists_", "")
        return (
            f"The required function `{fn_name}` is not exported by your candidate. "
            f"Add a top-level `def {fn_name}(...)` and make sure it returns the "
            f"shape documented in `public_api_contract.md`."
        )

    if check.startswith("return_type_"):
        fn_name = check.replace("return_type_", "")
        return (
            f"`{fn_name}()` exists but returns the wrong type. Check "
            f"`public_api_contract.md` for the expected return shape."
        )

    if check == "phase_execution_crash":
        return (
            "Phase execution itself crashed. The traceback is in the failure message. "
            "Most common cause: candidate raises an exception when one of its required "
            "functions is called. Trace the exception in your candidate."
        )

    # Generic fallback — STRIP raw check id and audit-internal phrasing.
    # Surface only the user-facing math intent of the failure. The stock text
    # itself must NOT mention audit/harness/threshold (that leaks the existence
    # of the hidden checks); it says "math goal not yet met" in plain terms.
    sanitized = _sanitize_failure_msg(msg)
    return (
        f"A required architectural property is not yet satisfied. "
        f"Observed: {sanitized}. "
        f"Identify which of your returned values fails the underlying math; "
        f"refer to `public_api_contract.md` for the intent of each function."
    )


def _sanitize_failure_list(failures: list) -> list:
    """Strip raw check ids from failure dicts before any use in prompts.

    Returns a copy of `failures` with `check` keys replaced by `category` labels
    that describe the math area without exposing audit-internal naming.
    """
    out = []
    for f in failures:
        check = f.get("check", "")
        # Categorize broad math areas without using raw check id
        category = _check_category(check)
        out.append({
            "category": category,
            "msg": _sanitize_failure_msg(f.get("msg", "")),
            # carry the raw check internally so math_diagnosis_from_failure still works
            "_raw_check": check,
        })
    return out


def _check_category(check: str) -> str:
    """Map a check id to a coarse math-area category (safe to show Grok)."""
    if check.startswith("function_exists_"): return "missing_function"
    if check.startswith("return_type_"): return "wrong_return_shape"
    if "noncomm" in check: return "non_commutativity"
    if "mequiv" in check: return "M_equivalence"
    if "finit" in check: return "finiteness_witness"
    if "weyl" in check or "hopf" in check: return "Hopf/Weyl_geometry"
    if "gstack" in check or "clifford" in check: return "G_stack_layer"
    if "axis" in check: return "axis_decomposition"
    if "prime" in check or "factor" in check: return "prime_resonance"
    if "stage" in check: return "stage_structure"
    if "manifold" in check or "rank" in check: return "constraint_manifold"
    if "classif" in check: return "state_classification"
    if "explain" in check or "confidence" in check: return "interpretability"
    if "denoise" in check or "petz" in check: return "channel_recovery"
    if "deterministic" in check or "determinis" in check: return "determinism"
    return "math_property"


def _sanitize_failure_msg(msg: str) -> str:
    """Strip audit-internal artifacts from a raw failure message before showing to Grok.

    Removes:
      - explicit check ids embedded as f-strings
      - regex/threshold hints
      - phase numbers and audit-internal jargon
      - "z-score = X" / "Pearson r = X" / "lift +X" / "(need ≥ X)" patterns
    """
    if not msg:
        return "(no message)"
    s = str(msg)
    # Strip "(need ≥ X)" / "(need ≤ X)" / "(need ≥X)" parenthetical thresholds
    s = re.sub(r"\(\s*need\s*[≥≤><=]+\s*[\d.\w]+\s*[^)]*\)", "", s)
    # Strip "z > Nσ" / "z ≥ Nσ" / "z-score = Nσ" style mentions
    s = re.sub(r"[zZ]([-_ ]?score)?\s*[><=]+\s*[+\-]?[\d.]+\s*σ", "[significance value]", s)
    s = re.sub(r"[zZ]([-_ ]?score)?\s*=\s*[+\-]?[\d.]+\s*σ", "[significance value]", s)
    # Strip "Spearman > N" / "Spearman = N" / "Pearson r = N" / "lift +N" / "lift ≥ N"
    s = re.sub(r"\bSpearman\b[^.,;]*?[<>=]+\s*[+\-]?[\d.]+", "[correlation value]", s)
    s = re.sub(r"\bPearson\b[^.,;]*?[=<>]+\s*[+\-]?[\d.]+", "[correlation value]", s)
    s = re.sub(r"\blift\b\s*[+\-]?\s*[\d.]+", "[lift value]", s)
    s = re.sub(r"\blift\b\s*[<>=≥≤]+\s*[+\-]?[\d.]+", "[lift threshold]", s)
    # Strip lines mentioning audit-internal jargon — replace whole clause
    s = re.sub(r"(?i)\b(threshold|regex|audit|harness)\b[^.]*?(?=[.\n]|$)", "", s)
    # Strip explicit "Phase N" mentions (only when followed by a number)
    s = re.sub(r"\bPhase\s+\d+\w*\b", "[a later phase]", s)
    # Strip explicit "(need ≥ X)" without parens but with the "need" keyword
    s = re.sub(r"\bneed\s*[≥≤><=]+\s*[\d.\w]+", "", s)
    # Collapse multiple spaces
    s = re.sub(r"\s+", " ", s)
    return s.strip()[:400]


def _passing_phase_summary(phase_summary: dict) -> list:
    """Build per-phase "what's working" strings from the runner's summary."""
    out = []
    for entry in phase_summary.get("phases", []):
        if entry.get("pass"):
            out.append(f"- Phase `{entry['phase_id']}` passes — KEEP its functions stable.")
    return out


def build_teacher_prompt(public_contract: str, candidate_code: str, failures: list,
                          metrics: dict, relevant_sims: list, iteration: int,
                          phase_id: str = None, phase_summary: dict = None) -> str:
    """Build the patch-request prompt for Grok. Hidden audit internals stay hidden.

    `phase_id` lets the prompt name the failing phase abstractly (e.g. "the prime-resonance
    phase") without leaking phase numbers or check ids. `phase_summary` gives a list of
    already-passing phases so Grok knows what to preserve.
    """
    failing_phase_descr = _phase_id_to_human_name(phase_id) if phase_id else \
                          "a required architectural phase"
    parts = [
        f"# Iteration {iteration} — patch request",
        "",
        f"Your candidate module did not pass {failing_phase_descr}.",
        "",
        "## Public API contract (review)",
        public_contract,
        "",
        "## What's working (preserve these)",
    ]
    if phase_summary:
        parts.extend(_passing_phase_summary(phase_summary))

    # Surface passing items based on metrics
    if metrics.get("mequivalence", {}).get("are_distinct") and metrics["mequivalence"].get("share_probe_class"):
        parts.append("- M-equivalence: ρ_a and ρ_b distinct AND share probe class. KEEP this working.")
    if metrics.get("noncommutation", {}).get("trace_distance", 0) > 1e-3:
        td = metrics["noncommutation"]["trace_distance"]
        parts.append(f"- Non-commutation: trace_distance = {td:.4f}. KEEP this working.")

    parts.append("")
    parts.append("## What needs fixing")
    for f in failures:
        diag = math_diagnosis_from_failure(f, metrics)
        # Do NOT echo the raw check id; the diagnosis already names the math problem.
        parts.append(f"- {diag}")

    # P1 fix: sim-reference filenames (e.g. `sim_clifford_spinor_double_cover_micro.py`)
    # are informationally equivalent to the raw check_id for the failure category they
    # encode. We do NOT emit specific sim filenames to Grok — instead, point to the
    # canonical pattern directory and let the candidate-side reason about which patterns
    # apply. Keep the count internally for telemetry but don't ship the names.
    if relevant_sims:
        parts.append("")
        parts.append("## Reference patterns")
        parts.append(f"- This iteration's failure category has {len(relevant_sims)} canonical "
                     f"pattern(s) under `system_v4/probes/` that may inform the fix. Do not "
                     f"assume specific filenames; read `public_api_contract.md` for the math intent.")

    parts.append("")
    parts.append("## Smallest next move")
    parts.append("Modify ONLY the function(s) flagged above. Do not rewrite the whole module. "
                 "Keep all other function signatures intact — the runner imports them by name.")
    parts.append("")
    parts.append("## Current candidate (modify and return as one ```python ... ``` block)")
    parts.append("```python")
    parts.append(candidate_code)
    parts.append("```")
    parts.append("")
    parts.append("Return ONE python code block — the full revised candidate.")
    return "\n".join(parts)


def extract_code(text: str) -> str:
    m = re.search(r"```python\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1)
    m = re.search(r"```\s*\n(.*?)```", text, re.DOTALL)
    return m.group(1) if m else None


def run_runner(candidate_path: Path) -> dict:
    """Run runner.py on the candidate, return parsed summary."""
    r = subprocess.run(
        [PYTHON_BIN, str(RUNNER), "--candidate", str(candidate_path)],
        capture_output=True, text=True, timeout=600,
    )
    # Parse the summary file
    # The runner outputs "Summary: <path>" — grep that
    m = re.search(r"Summary:\s*(.+\.json)", r.stdout)
    summary_path = Path(m.group(1).rstrip()) if m else None
    summary = {}
    if summary_path and summary_path.exists():
        summary = json.loads(summary_path.read_text())
    return {
        "stdout": r.stdout,
        "stderr": r.stderr,
        "exit_code": r.returncode,
        "summary_path": str(summary_path) if summary_path else None,
        "summary": summary,
        "run_dir": str(summary_path.parent) if summary_path else None,
    }


def read_phase_receipt(run_dir: Path, phase_id: str) -> dict:
    p = run_dir / f"phase_{phase_id}_results.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _load_key_from_shell(var_name: str = "XAI_API_KEY") -> str:
    """Run an interactive login zsh and read `var_name` from its environment.

    This is more robust than sourcing ~/.zshrc directly: keys may live in
    ~/.zshenv, ~/.zprofile, a plugin loader, or anywhere else the user's
    interactive shell pulls from. An interactive login shell triggers the
    full startup chain.

    The value is returned to the caller for use in the API client; it is NOT
    printed, logged, or persisted.
    """
    import subprocess
    try:
        # `zsh -i -l -c 'printf %s "$VAR"'` runs an interactive (-i) login (-l)
        # shell, which sources all the user's startup files exactly as a
        # terminal would, then prints the var with no formatting.
        r = subprocess.run(
            ["zsh", "-i", "-l", "-c", f'printf %s "${var_name}"'],
            capture_output=True, text=True, timeout=10,
        )
        return r.stdout.strip()
    except Exception:
        return ""


# Back-compat alias for the older function name
_load_key_from_zshrc = _load_key_from_shell


def call_grok(prompt: str, client: OpenAI) -> str:
    resp = client.chat.completions.create(
        model="grok-4.3",
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--max-iters", type=int, default=4)
    args = ap.parse_args()

    api_key = os.environ.get("XAI_API_KEY") or _load_key_from_zshrc()
    if not api_key:
        print("ERROR: XAI_API_KEY not set and not found in ~/.zshrc", file=sys.stderr)
        sys.exit(2)
    client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

    candidate_path = Path(args.candidate).resolve()
    if not candidate_path.exists():
        print(f"ERROR: candidate not found: {candidate_path}", file=sys.stderr)
        sys.exit(2)

    public_contract = (PROMPTS_DIR / "public_api_contract.md").read_text()

    for iteration in range(1, args.max_iters + 1):
        print(f"\n{'#' * 100}\n# LOOP DRIVER iteration {iteration}\n{'#' * 100}\n")
        print(f"Candidate: {candidate_path.name}")

        # 1. Run the runner
        result = run_runner(candidate_path)
        print(result["stdout"])

        if result["exit_code"] == 0:
            print(f"\n🎯 ALL PHASES PASSED at iteration {iteration}. Candidate: {candidate_path}")
            return

        # 2. Find the failing phase + read its receipt
        run_dir = Path(result["run_dir"]) if result["run_dir"] else None
        if not run_dir:
            print("No run dir — can't continue.")
            return

        failing_phase = None
        for p in result["summary"]["phases"]:
            if not p["pass"]:
                failing_phase = p["phase_id"]
                break
        if not failing_phase:
            print("No failing phase found in summary.")
            return

        receipt = read_phase_receipt(run_dir, failing_phase)
        raw_failures = receipt.get("observable", {}).get("failures", [])
        metrics = receipt.get("observable", {}).get("metrics", {})
        print(f"\nFailing phase: {failing_phase}  failures: {len(raw_failures)}")

        # Sanitize failures before any use downstream — strip raw check ids and
        # audit-internal phrasing. The diagnosis function reads `_raw_check`
        # internally to keep targeted diagnoses working.
        failures = _sanitize_failure_list(raw_failures)

        # 3. Build Teacher prompt (phase-aware + sanitized — no audit internals leak)
        candidate_code = candidate_path.read_text()
        relevant_sims = find_relevant_sim_refs(failures)  # works on _raw_check too
        prompt = build_teacher_prompt(public_contract, candidate_code, failures, metrics,
                                       relevant_sims, iteration,
                                       phase_id=failing_phase,
                                       phase_summary=result["summary"])

        # 4. Call Grok
        print(f"\nCalling Grok 4.3 (relevant sim refs: {relevant_sims})...")
        t0 = time.time()
        try:
            response = call_grok(prompt, client)
        except Exception as e:
            print(f"Grok call failed: {e}")
            return
        print(f"Grok response in {time.time() - t0:.1f}s ({len(response)} chars)")

        new_code = extract_code(response)
        if not new_code:
            print("Couldn't extract code block from Grok response.")
            return

        # 5. Save new candidate
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        new_name = f"candidate_iter_{iteration:02d}_{ts}.py"
        new_path = CANDIDATES_DIR / new_name
        new_path.write_text(new_code)
        print(f"Saved: {new_path.name}")

        candidate_path = new_path

    print(f"\nReached max iters ({args.max_iters}) without convergence. Last candidate: {candidate_path}")


if __name__ == "__main__":
    main()
