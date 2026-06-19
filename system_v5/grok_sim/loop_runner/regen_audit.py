#!/usr/bin/env python3
"""regen_audit.py — independent re-derivation of compromised functions.

Calls Grok (via x.ai) and Gemini (via Google's OpenAI-compatible endpoint) with
ONLY the public API contract. No prior candidate code is shown. The models must
derive implementations from the math intent alone.

The 11 functions targeted are the ones the Opus audit (OPUS_AUDIT_2026_05_13.md)
flagged as P0/P1 cheats: prime_resonance, engine_stage, fisher_information_matrix,
holonomic_gate, flux_holonomy, probe_quotient_compress, denoise_pipeline,
classify_state, explain_state, signature_to_density_matrix, project_to_manifold.

Run: python3 regen_audit.py
Outputs: candidates/candidate_grok_regen.py + candidates/candidate_gemini_regen.py
"""
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

from openai import OpenAI

CANDIDATES_DIR = HERE.parent / "candidates"
PROMPTS_DIR = HERE / "prompts"

TARGET_FUNCTIONS = [
    "prime_resonance(n: int) -> dict",
    "engine_stage(engine_id: str, stage_idx: int, substage_idx: int, input_rho_qt) -> dict",
    "fisher_information_matrix(theta_perturbation: float = 0.01) -> dict",
    "holonomic_gate(loop_angle: float, n_steps: int = 64) -> dict",
    "flux_holonomy() -> float",
    "probe_quotient_compress(input_rho_qt) -> dict",
    "denoise_pipeline(rho_noisy_qt) -> dict",
    "classify_state(rho_qt) -> dict",
    "explain_state(rho_qt) -> dict",
    "signature_to_density_matrix(sig_vec) -> qt.Qobj",
    "project_to_manifold(rho_qt) -> dict",
]


def _load_key(var: str) -> str:
    """Same loader as loop_driver: interactive login shell."""
    r = subprocess.run(
        ["zsh", "-i", "-l", "-c", f'printf %s "${var}"'],
        capture_output=True, text=True, timeout=10,
    )
    return r.stdout.strip()


def build_regen_prompt() -> str:
    contract = (PROMPTS_DIR / "public_api_contract.md").read_text()
    parts = [
        "# Independent re-derivation request",
        "",
        "An adversarial code review found that an earlier implementation of the functions",
        "below contained TEST-TUNED CHEATS — hardcoded magic numbers calibrated to specific",
        "pass thresholds, classical-primality sieves embedded in 'engine-derived' scores,",
        "synthetic matrices that ignore their inputs, snap-to-target operations claiming to",
        "be channel recovery, and hash-based distinctness offsets.",
        "",
        "Your task: re-derive these functions from the architectural intent in the public",
        "API contract below. **Do not** look at, reference, or replicate any prior",
        "implementation. **Do not** introduce classical sieves (e.g. `is_prime(n)` as a",
        "multiplier in 'engine-derived' outputs). **Do not** use hash-style modular",
        "arithmetic to force pairwise distinctness — distinctness must emerge from the",
        "architecture's actual operators.",
        "",
        "## Functions to re-derive",
        "",
    ]
    for sig in TARGET_FUNCTIONS:
        parts.append(f"- `{sig}`")
    parts.extend([
        "",
        "## Public API contract",
        "",
        contract,
        "",
        "## Output format",
        "",
        "Return ONE python code block — a complete module that implements all the",
        "functions above PLUS the other API functions referenced by the contract",
        "(`run_engine`, `compute_axis_metrics`, `mequivalence_demo`, `finite_witness`,",
        "`noncomm_pair`, `gstack_layers`, `weyl_chirality_probe`, `tool_manifest`,",
        "`sidequest_claim_boundary`, `axis_transform`, `terrain_operation`,",
        "`extract_info_work` or `extract_szilard_work`, `stage_to_hexagram`,",
        "`decoherence_free_subspace`, `petz_recover`, `ai_tool_surface`).",
        "",
        "Use numpy, qutip, torch, and the other tools the contract names. Be honest:",
        "if you can't derive an honest implementation of a function, leave it with a",
        "stub that raises NotImplementedError — that is preferable to a cheat.",
    ])
    return "\n".join(parts)


def call_grok(prompt: str, api_key: str) -> str:
    client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1", timeout=1800)
    resp = client.chat.completions.create(
        model="grok-4.3",
        messages=[{"role": "user", "content": prompt}],
        timeout=1800,
    )
    return resp.choices[0].message.content


def call_gemini(prompt: str, api_key: str) -> str:
    # Gemini exposes an OpenAI-compatible endpoint
    client = OpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )
    resp = client.chat.completions.create(
        model="gemini-3.1-pro-preview",
        messages=[{"role": "user", "content": prompt}],
        timeout=600,
    )
    return resp.choices[0].message.content


def extract_code(text: str) -> str:
    m = re.search(r"```python\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1)
    m = re.search(r"```\s*\n(.*?)```", text, re.DOTALL)
    return m.group(1) if m else None


def main():
    prompt = build_regen_prompt()
    print(f"Prompt length: {len(prompt)} chars")

    target = sys.argv[1] if len(sys.argv) > 1 else "both"

    if target in ("grok", "both"):
        print("\n=== Grok regeneration ===")
        xai_key = _load_key("XAI_API_KEY")
        if not xai_key:
            print("XAI_API_KEY not found — skipping Grok")
        else:
            t0 = time.time()
            try:
                resp = call_grok(prompt, xai_key)
                print(f"Grok responded in {time.time()-t0:.1f}s ({len(resp)} chars)")
                code = extract_code(resp)
                if code:
                    out = CANDIDATES_DIR / "candidate_grok_regen.py"
                    out.write_text(code)
                    print(f"Saved: {out}")
                else:
                    print("Couldn't extract code block from Grok response.")
                    (CANDIDATES_DIR / "candidate_grok_regen_raw.txt").write_text(resp)
            except Exception as e:
                print(f"Grok call failed: {type(e).__name__}: {str(e)[:200]}")

    if target in ("gemini", "both"):
        print("\n=== Gemini regeneration ===")
        gemini_key = _load_key("GEMINI_API_KEY")
        if not gemini_key:
            print("GEMINI_API_KEY not found — skipping Gemini")
        else:
            t0 = time.time()
            try:
                resp = call_gemini(prompt, gemini_key)
                print(f"Gemini responded in {time.time()-t0:.1f}s ({len(resp)} chars)")
                code = extract_code(resp)
                if code:
                    out = CANDIDATES_DIR / "candidate_gemini_regen.py"
                    out.write_text(code)
                    print(f"Saved: {out}")
                else:
                    print("Couldn't extract code block from Gemini response.")
                    (CANDIDATES_DIR / "candidate_gemini_regen_raw.txt").write_text(resp)
            except Exception as e:
                print(f"Gemini call failed: {type(e).__name__}: {str(e)[:200]}")


if __name__ == "__main__":
    main()
