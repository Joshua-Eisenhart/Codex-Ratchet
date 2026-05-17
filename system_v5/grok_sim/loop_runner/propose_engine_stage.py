#!/usr/bin/env python3
"""propose_engine_stage.py — propose ordered_channel_composition_sequence().

NOTE: file name is legacy. Content is decontaminated. We propose a math
primitive: two ordered sequences of CPTP channels (Kraus form) applied to a
shared starting density matrix, producing two trajectories whose endpoint
states differ in trace distance. No engine/stage/Engine A/B language.
"""
import concurrent.futures
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import multi_model_loop as mml

CANDIDATES = HERE.parent / "candidates"


PROMPT = """Implement `ordered_channel_composition_sequence() -> dict` for a 4-qubit carrier.

Two ordered sequences S1, S2 of CPTP channels (each a list of Kraus channels)
applied to a shared starting density matrix ρ_0. Each sequence has L = 8 steps.
At each step the intermediate ρ_k is recorded. The two final ρ_L from S1 and S2
must differ by trace distance > 0.03, AND each intermediate trajectory must
visit L distinct states pairwise (so consecutive states are closer than distant
ones in trace distance, on average).

The distinctness across sequences must come from the order of non-commuting
channels — not from index arithmetic, hash distinguishers, or synthetic returns.

## Return shape

```python
{
    "sequence_1_kraus_lists": list[list[qt.Qobj]],   # L lists of Kraus operators (CPTP each)
    "sequence_2_kraus_lists": list[list[qt.Qobj]],
    "rho_0_qt": qt.Qobj,                              # shared start state, non-trivial
    "trajectory_1_qt": list[qt.Qobj],                 # L+1 states (ρ_0 .. ρ_L)
    "trajectory_2_qt": list[qt.Qobj],
    "endpoint_trace_distance": float,                 # > 0.03
    "intra_trajectory_pairwise_min_td": float,        # > 1e-4 so all states distinct
    "kraus_completeness_max_error": float,            # < 1e-9 across all channels
}
```

## Constraints (binding)

- Qobjs use `dims=[[2,2,2,2],[2,2,2,2]]`.
- Each channel applied as ρ ↦ ∑ K_i ρ K_i† with ∑ K_i†K_i = I (within 1e-9).
- Sequences differ in ORDER of the same or related channel set — the math
  signature is non-commutation, not channel-set identity.
- All states satisfy Tr(ρ) ≈ 1 and PSD within 1e-9.
- Deterministic.
- L = 8 ordered steps per sequence.

## Banned identifiers (auto-reject)

`axis`, `Ax0..Ax6`, `engine`, `engine_stage`, `Engine A/B`, `Type 1/2`, `stage`,
`substage`, `gstack`, `g_stack`, `terrain`, `Ti/Te/Fi/Fe` as function/variable
names, `prime_resonance`, `hexagram`, `Carnot`, `Szilard`, `IGT`, `Jung`.

Return ONE python code block with `ordered_channel_composition_sequence()` and
small helpers.
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
        f_g = ex.submit(call_grok); f_m = ex.submit(call_gemini)
        f_g.result(timeout=1800); f_m.result(timeout=1800)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    grok_path = gemini_path = None
    if results["grok"]:
        c = mml.extract_code(results["grok"])
        if c:
            grok_path = CANDIDATES / f"ordered_channel_seq_grok_{ts}.py"
            grok_path.write_text(c); print(f"Saved Grok: {grok_path.name}")
    if results["gemini"]:
        c = mml.extract_code(results["gemini"])
        if c:
            gemini_path = CANDIDATES / f"ordered_channel_seq_gemini_{ts}.py"
            gemini_path.write_text(c); print(f"Saved Gemini: {gemini_path.name}")

    if grok_path and gemini_path:
        print(f"\nCodex judging ordered_channel_composition_sequence proposals...")
        decision_file = Path("/tmp/codex_ordered_channel_seq_decision.txt")
        if decision_file.exists(): decision_file.unlink()
        instr = (
            f"Two generators proposed `ordered_channel_composition_sequence()` for a 4-qubit carrier. "
            f"For each: (a) verify Kraus completeness < 1e-9 for every channel in both sequences, "
            f"(b) confirm endpoint trace distance > 0.03, (c) confirm intra-trajectory pairwise "
            f"min td > 1e-4, (d) auto-reject if any banned identifier appears "
            f"(axis/Ax0-6/engine/engine_stage/stage/substage/Engine A-B/Type 1-2/terrain/"
            f"Ti-Te-Fi-Fe as names/gstack/prime_resonance/hexagram/Carnot/Szilard/IGT/Jung).\n\n"
            f"Grok:    {grok_path}\nGemini:  {gemini_path}\n\n"
            f"Write decision to /tmp/codex_ordered_channel_seq_decision.txt:\n"
            f"  Line 1: GROK or GEMINI or REJECT_BOTH\n"
            f"  Lines 2+: justification with measured endpoint td and min-pairwise td\n"
        )
        t0 = time.time()
        r = subprocess.run(
            ["codex", "exec",
             "-c", 'model_reasoning_effort="low"',
             "-C", str(HERE.parent), "-s", "workspace-write",
             "--skip-git-repo-check", instr],
            capture_output=True, text=True, timeout=900,
        )
        print(f"Codex finished in {time.time()-t0:.1f}s")
        if decision_file.exists():
            print(f"\n=== Codex decision ===\n{decision_file.read_text()}")


if __name__ == "__main__":
    main()
