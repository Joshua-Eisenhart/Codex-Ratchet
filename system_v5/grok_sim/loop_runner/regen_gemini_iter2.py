#!/usr/bin/env python3
"""regen_gemini_iter2.py — second iteration on Gemini's candidate.

Feeds Gemini's prior output back to it along with the qutip-dimension error.
Preserves the architectural choices Gemini made; only fixes the API miss.
"""
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from openai import OpenAI

CANDIDATES = HERE.parent / "candidates"


def _load_key(var: str) -> str:
    r = subprocess.run(["zsh", "-i", "-l", "-c", f'printf %s "${var}"'],
                       capture_output=True, text=True, timeout=10)
    return r.stdout.strip()


def main():
    prior_code = (CANDIDATES / "candidate_gemini_regen.py").read_text()
    prompt = (
        "# Second iteration — fix the qutip-dimension API miss\n\n"
        "Your prior implementation (below) is architecturally clean — no test-tuned\n"
        "cheats, no classical sieves embedded in 'engine-derived' scores. Keep all\n"
        "those choices.\n\n"
        "However it has a qutip API miss: many Qobjs are constructed with\n"
        "`dims=[[16],[16]]` (flat 16-dim) when the architecture's 4-qubit carrier\n"
        "requires `dims=[[2,2,2,2],[2,2,2,2]]` (tensor product). qutip raises\n"
        "`TypeError: incompatible dimensions` when these are mixed.\n\n"
        "Fix: ensure every Qobj you build from a 16x16 array uses\n"
        "`qt.Qobj(matrix, dims=[[2,2,2,2],[2,2,2,2]])`. Also remove the\n"
        "`torch.set_default_dtype(torch.complex128)` line — torch rejects complex\n"
        "default dtypes; use `torch.float64` instead and cast to complex tensors\n"
        "explicitly where needed.\n\n"
        "Do NOT change the architectural logic (prime_resonance using totient,\n"
        "engine_stage's sequential composition, etc.). Only fix the API issues so\n"
        "the module imports and the 4-qubit Qobjs interoperate.\n\n"
        "Return ONE python code block — the complete revised module.\n\n"
        "## Prior code (fix the API issues only)\n\n"
        f"```python\n{prior_code}\n```\n"
    )
    print(f"Prompt length: {len(prompt)} chars")
    key = _load_key("GEMINI_API_KEY")
    if not key:
        print("GEMINI_API_KEY not found"); return
    client = OpenAI(api_key=key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                    timeout=1800)
    t0 = time.time()
    resp = client.chat.completions.create(
        model="gemini-2.5-pro",
        messages=[{"role": "user", "content": prompt}],
        timeout=1800,
    )
    text = resp.choices[0].message.content
    print(f"Gemini iter2 in {time.time()-t0:.1f}s ({len(text)} chars)")
    m = re.search(r"```python\s*\n(.*?)```", text, re.DOTALL)
    if not m:
        m = re.search(r"```\s*\n(.*?)```", text, re.DOTALL)
    if m:
        out = CANDIDATES / "candidate_gemini_regen_v2.py"
        out.write_text(m.group(1))
        print(f"Saved: {out}")
    else:
        print("No code block found")
        (CANDIDATES / "candidate_gemini_regen_v2_raw.txt").write_text(text)


if __name__ == "__main__":
    main()
