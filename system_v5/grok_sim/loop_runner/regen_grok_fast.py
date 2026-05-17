#!/usr/bin/env python3
"""regen_grok_fast.py — Grok regen using grok-code-fast-1 (faster, smaller prompt)."""
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from openai import OpenAI

CANDIDATES = HERE.parent / "candidates"
PROMPTS = HERE / "prompts"


def _load_key(var):
    r = subprocess.run(["zsh", "-i", "-l", "-c", f'printf %s "${var}"'],
                       capture_output=True, text=True, timeout=10)
    return r.stdout.strip()


def main():
    contract = (PROMPTS / "public_api_contract.md").read_text()
    prompt = (
        "You are re-implementing a quantum-information simulator module. An earlier "
        "implementation contained test-tuned cheats (classical primality sieves "
        "embedded in 'engine-derived' scores, hardcoded magic numbers calibrated to "
        "specific pass thresholds, synthetic matrices ignoring their inputs, "
        "snap-to-target operations claiming to be channel recovery). Your task is "
        "to re-derive every function from the architectural intent in the contract, "
        "with no test-tuning.\n\n"
        "Constraints:\n"
        "- 4-qubit Hopf-spinor carrier (16-dim Hilbert). Use `dims=[[2,2,2,2],[2,2,2,2]]`\n"
        "  on every Qobj built from a 16x16 array.\n"
        "- numpy + qutip + torch are primary tools. cvc5/z3/clifford/sympy/gudhi/toponetx\n"
        "  must each be used in a load-bearing way (not decorative imports).\n"
        "- NEVER use `if is_prime(n):` as a multiplier in engine outputs. NEVER use\n"
        "  hash-style modular arithmetic to force pairwise distinctness. NEVER return\n"
        "  the input itself as 'canonical' for a compression function.\n"
        "- For complex types, use `torch.complex128` explicitly on tensors; do NOT set\n"
        "  it as torch default dtype (torch rejects that).\n"
        "- If you don't know how to honestly implement a function, leave a stub that\n"
        "  raises NotImplementedError. That is better than a cheat.\n\n"
        "Return one Python code block — the complete module.\n\n"
        "## Contract\n\n"
        + contract
    )
    print(f"Prompt: {len(prompt)} chars")
    key = _load_key("XAI_API_KEY")
    client = OpenAI(api_key=key, base_url="https://api.x.ai/v1", timeout=600)
    t0 = time.time()
    try:
        resp = client.chat.completions.create(
            model="grok-code-fast-1",
            messages=[{"role": "user", "content": prompt}],
            timeout=600,
        )
    except Exception as e:
        print(f"FAIL: {type(e).__name__}: {str(e)[:200]}")
        return
    text = resp.choices[0].message.content
    print(f"Grok-code-fast in {time.time()-t0:.1f}s ({len(text)} chars)")
    m = re.search(r"```python\s*\n(.*?)```", text, re.DOTALL)
    if not m:
        m = re.search(r"```\s*\n(.*?)```", text, re.DOTALL)
    if m:
        out = CANDIDATES / "candidate_grok_regen.py"
        out.write_text(m.group(1))
        print(f"Saved: {out}")
    else:
        (CANDIDATES / "candidate_grok_regen_raw.txt").write_text(text)
        print("No code block; raw saved")


if __name__ == "__main__":
    main()
