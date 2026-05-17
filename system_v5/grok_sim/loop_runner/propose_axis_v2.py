#!/usr/bin/env python3
"""propose_axis_v2.py — propose nonidentity_kraus_channel_pair().

NOTE: file name is legacy. Content is decontaminated. We propose a math primitive:
two CPTP channels A, B (explicit Kraus operators) on the 4-qubit carrier such
that A∘B ≠ B∘A on at least one witness input. No axis/engine/terrain words.
"""
import concurrent.futures, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import multi_model_loop as mml

CANDIDATES = HERE.parent / "candidates"


PROMPT = """Implement `nonidentity_kraus_channel_pair() -> dict` for a 4-qubit carrier.

Two CPTP channels A, B given by explicit Kraus operators on the 16-dim Hilbert
space. There must exist a witness density matrix ρ such that
trace_distance(A(B(ρ)), B(A(ρ))) > 0.03.

Distinctness must come from algebraic non-commutation of the Kraus sets — NOT
from hash distinguishers, index arithmetic, classical-primality multipliers,
or synthetic returns.

## Return shape

```python
{
    "channel_A_kraus": list[qt.Qobj],       # ∑ K†K = I, dims=[[2,2,2,2],[2,2,2,2]]
    "channel_B_kraus": list[qt.Qobj],       # ∑ K†K = I, dims=[[2,2,2,2],[2,2,2,2]]
    "rho_witness_qt": qt.Qobj,              # non-trivial 4-qubit density matrix
    "rho_AB_qt": qt.Qobj,                   # A(B(ρ))
    "rho_BA_qt": qt.Qobj,                   # B(A(ρ))
    "trace_distance_AB_BA": float,          # > 0.03
    "kraus_completeness_A": float,          # ||∑ K†K − I||_F, must be < 1e-9
    "kraus_completeness_B": float,
}
```

## Constraints (binding)

- qutip + numpy. Qobjs use `dims=[[2,2,2,2],[2,2,2,2]]`.
- Each channel applied as ρ ↦ ∑ K_i ρ K_i†.
- Both channels must satisfy Kraus completeness within 1e-9.
- The non-commutation must be witnessed on a non-trivial mixed input, not just a
  computational-basis pure state.
- Deterministic.

## Banned identifiers (auto-reject)

`axis`, `Ax0..Ax6`, `engine`, `engine_stage`, `Engine A/B`, `Type 1/2`,
`gstack`, `g_stack`, `terrain`, `Ti/Te/Fi/Fe` as function/variable names,
`prime_resonance`, `hexagram`, `Carnot`, `Szilard`, `IGT`, `Jung`.

Return ONE python code block with `nonidentity_kraus_channel_pair()` and
small helpers.
"""


def main():
    print(f"Prompt: {len(PROMPT)} chars\n")
    results = {"grok": None, "gemini": None}
    def call_grok():
        t0 = time.time()
        try:
            results["grok"] = mml.gen_grok(PROMPT)
            print(f"  [grok] returned in {time.time()-t0:.1f}s")
        except Exception as e: print(f"  [grok] failed: {e}")
    def call_gemini():
        t0 = time.time()
        try:
            results["gemini"] = mml.gen_gemini(PROMPT)
            print(f"  [gemini] returned in {time.time()-t0:.1f}s")
        except Exception as e: print(f"  [gemini] failed: {e}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        f_g = ex.submit(call_grok); f_m = ex.submit(call_gemini)
        f_g.result(timeout=1800); f_m.result(timeout=1800)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    grok_path = gemini_path = None
    if results["grok"]:
        code = mml.extract_code(results["grok"])
        if code:
            grok_path = CANDIDATES / f"nonidentity_kraus_pair_grok_{ts}.py"
            grok_path.write_text(code); print(f"Saved: {grok_path.name}")
    if results["gemini"]:
        code = mml.extract_code(results["gemini"])
        if code:
            gemini_path = CANDIDATES / f"nonidentity_kraus_pair_gemini_{ts}.py"
            gemini_path.write_text(code); print(f"Saved: {gemini_path.name}")

    if grok_path and gemini_path:
        print(f"\nCodex judging...")
        decision_file = Path("/tmp/codex_nonidentity_kraus_pair_decision.txt")
        if decision_file.exists(): decision_file.unlink()
        instr = (
            f"Two `nonidentity_kraus_channel_pair()` proposals for a 4-qubit carrier. "
            f"For each: (a) verify Kraus completeness ||∑ K†K − I||_F < 1e-9 for A and B, "
            f"(b) compute trace_distance(A(B(ρ)), B(A(ρ))) on the proposed witness — must be > 0.03, "
            f"(c) check no banned identifiers (axis/Ax0-6/engine/engine_stage/terrain/Ti-Te-Fi-Fe-as-names/"
            f"gstack/prime_resonance/Carnot/Szilard/IGT/Jung/hexagram).\n\n"
            f"Grok:    {grok_path}\nGemini:  {gemini_path}\n\n"
            f"Write /tmp/codex_nonidentity_kraus_pair_decision.txt:\n"
            f"  Line 1: GROK | GEMINI | REJECT_BOTH\n"
            f"  Line 2: measured trace distance for chosen proposal\n"
            f"  Lines 3+: any failed checks for either proposal\n"
        )
        t0 = time.time()
        subprocess.run(["codex", "exec", "-c", 'model_reasoning_effort="low"',
                        "-C", str(HERE.parent), "-s", "workspace-write",
                        "--skip-git-repo-check", instr],
                       capture_output=True, text=True, timeout=900)
        print(f"  Codex done in {time.time()-t0:.1f}s")
        if decision_file.exists():
            print(f"\n=== Decision ===\n{decision_file.read_text()}")


if __name__ == "__main__":
    main()
