#!/usr/bin/env python3
"""propose_manifold.py — targeted Grok+Gemini proposals for build_constraint_manifold().

Asks both for a fresh implementation of the manifold-foundation primitive. Codex
picks the better one. Writes both proposals + Codex decision to disk for review.
"""
import concurrent.futures
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import multi_model_loop as mml

CANDIDATES = HERE.parent / "candidates"


PROMPT = """Implement `pauli_basis_with_u1_connection() -> dict` for a 4-qubit carrier.

Literal-math contract: the function returns a Hermitian operator basis on the
16-dim Hilbert space together with a U(1) connection 1-form discretized as a
16×16 Hermitian operator. No persona/role names, no axis indices, no engine
labels, no terrain words. Only math objects.

## Function to implement

```python
def pauli_basis_with_u1_connection() -> dict:
    \"\"\"Construct a Hermitian operator basis on the 4-qubit carrier plus a
    discretized U(1) connection operator producing nontrivial holonomy.\"\"\"
```

Return shape:
```python
{
    "carrier_dim": 16,
    "operator_basis_qt": list[qt.Qobj],     # ≥6 Hermitian operators, dims=[[2,2,2,2],[2,2,2,2]]
    "u1_connection_qt": qt.Qobj,            # 16×16 Hermitian connection operator A
    "is_on_basis_span": callable,           # (rho_qt) -> bool; True for |0000⟩⟨0000|
                                            # and any state reachable by exp(-iαH)ρexp(+iαH)
                                            # with H in operator_basis_qt
    "holonomy_witness_phase": float,        # ∮ A on a concrete closed loop, must be nonzero
}
```

## Constraints (binding)

- qutip + numpy. Every Qobj uses `dims=[[2,2,2,2],[2,2,2,2]]`.
- `u1_connection_qt` must give a nonzero `holonomy_witness_phase` for at least
  one concrete closed loop in parameter space.
- `is_on_basis_span(rho)` returns True for ρ = |0000⟩⟨0000| and for any state
  produced by conjugation with `exp(-iαH)` where H is in `operator_basis_qt`.
- No hash-style distinctness, no classical-primality multipliers, no trivial
  identity verifiers.

## Banned identifiers

No `axis`, `Ax0..Ax6`, `engine`, `engine_stage`, `Engine A/B`, `Type 1/2`,
`gstack`, `g_stack`, `terrain`, `Ti/Te/Fi/Fe` (as function names — the math is
named directly via `dephasing_channel`/`unitary_rotation_channel` in sibling
primitives), `prime_resonance`, `hexagram`, `Carnot`, `Szilard`, `IGT`, `Jung`.

## Output

ONE python code block: imports, the `pauli_basis_with_u1_connection()` function,
and any private helpers. No other primitives.
"""


def main():
    print(f"Prompt: {len(PROMPT)} chars")
    print(f"Calling Grok 4.3 and Gemini 3.1-pro in parallel...\n")
    results = {"grok": None, "gemini": None}
    def call_grok():
        t0 = time.time()
        try:
            results["grok"] = mml.gen_grok(PROMPT)
            print(f"  [grok] returned in {time.time()-t0:.1f}s ({len(results['grok'])} chars)")
        except Exception as e:
            print(f"  [grok] failed: {type(e).__name__}: {str(e)[:120]}")
    def call_gemini():
        t0 = time.time()
        try:
            results["gemini"] = mml.gen_gemini(PROMPT)
            print(f"  [gemini] returned in {time.time()-t0:.1f}s ({len(results['gemini'])} chars)")
        except Exception as e:
            print(f"  [gemini] failed: {type(e).__name__}: {str(e)[:120]}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        f_g = ex.submit(call_grok)
        f_m = ex.submit(call_gemini)
        f_g.result(timeout=1800)
        f_m.result(timeout=1800)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    grok_path = gemini_path = None
    if results["grok"]:
        code = mml.extract_code(results["grok"])
        if code:
            grok_path = CANDIDATES / f"pauli_basis_u1_connection_grok_{ts}.py"
            grok_path.write_text(code)
            print(f"\nSaved Grok proposal: {grok_path.name}")
    if results["gemini"]:
        code = mml.extract_code(results["gemini"])
        if code:
            gemini_path = CANDIDATES / f"pauli_basis_u1_connection_gemini_{ts}.py"
            gemini_path.write_text(code)
            print(f"Saved Gemini proposal: {gemini_path.name}")

    if grok_path and gemini_path:
        print(f"\nCodex (GPT-5.5 LOW) judging both proposals...")
        decision_file = Path("/tmp/codex_manifold_decision.txt")
        if decision_file.exists(): decision_file.unlink()
        instr = (
            "Two generators produced `pauli_basis_with_u1_connection()` for a 4-qubit carrier. "
            "Pick the more honest. Reject either if it: returns a trivial identity verifier, "
            "uses hash-style distinctness, produces operators with wrong qutip dims, gives a zero "
            "holonomy phase on the witness loop, or smuggles in banned identifiers "
            "(axis/Ax0-6/engine/gstack/terrain/Ti/Te/Fi/Fe as function names/prime_resonance/Carnot/Szilard/IGT/hexagram).\n\n"
            f"Grok proposal:    {grok_path}\n"
            f"Gemini proposal:  {gemini_path}\n\n"
            "Write your decision to /tmp/codex_manifold_decision.txt:\n"
            "  Line 1: GROK or GEMINI or REJECT_BOTH\n"
            "  Lines 2+: short justification, plus the witness holonomy phase value reported.\n"
        )
        t0 = time.time()
        r = subprocess.run(
            ["codex", "exec",
             "-c", 'model_reasoning_effort="low"',
             "-C", str(HERE.parent),
             "-s", "workspace-write",
             "--skip-git-repo-check",
             instr],
            capture_output=True, text=True, timeout=900,
        )
        print(f"Codex finished in {time.time()-t0:.1f}s (exit {r.returncode})")
        if decision_file.exists():
            print(f"\n=== Codex decision ===\n{decision_file.read_text()}\n")
        else:
            print("Codex did not write a decision file. Last stdout 600 chars:")
            print(r.stdout[-600:])


if __name__ == "__main__":
    main()
