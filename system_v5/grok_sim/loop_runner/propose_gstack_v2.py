#!/usr/bin/env python3
"""propose_gstack_v2.py — extended g-stack with correlation + mutual entropies.

The v1 g-stack only admitted single-state entropies (how-mixed-is-this-rho).
The Hopf-fibered carrier has natural bipartitions (left vs right Weyl;
spinors vs gauge links), so JOINT entropies are first-class measurements.

v2 adds:
  - mutual_information_LR          (I(A:B) = S(A)+S(B)-S(A,B), A=left half, B=right half)
  - mutual_information_spinor_gauge (A=spinor pair, B=gauge pair)
  - correlation_entropy            (a non-MI correlation measure)
  - conditional_entropy_LR         (S(A|B))
  - entanglement_entropy_LR        (S(A) where A=reduced left state)
  - entanglement_entropy_spinor_gauge

Each layer restricts WHICH bipartite entropies remain admissible, in addition
to the prior single-state restrictions.
"""
import concurrent.futures, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import multi_model_loop as mml

CANDIDATES = HERE.parent / "candidates"
PROPOSED = HERE / "proposed_formal_sims"
MANIFOLD = CANDIDATES / "manifold_proposal_gemini_20260514T000643Z.py"


PROMPT = """Propose `build_gstack_over_manifold_v2(manifold_dict) -> dict` — an extended
layered g-stack that includes JOINT/CORRELATION entropies in addition to the
single-state entropies of v1.

## Why this matters

The constraint manifold has natural bipartitions:
  - Bipartition 1 (LR): subsystem A = (Q0, Q1) = left spinor + left gauge link;
                         subsystem B = (Q2, Q3) = right spinor + right gauge link.
  - Bipartition 2 (SG): subsystem A = (Q0, Q2) = spinor pair (ψ_L, ψ_R);
                         subsystem B = (Q1, Q3) = gauge-link pair.

Joint entropies measure how correlated the two halves are, which is the
information-theoretic core of this simulator.

## Admissible-entropy set (must include single-state AND joint)

Single-state (from v1, all well-defined on a 4-qubit density matrix):
  von_neumann, linear_entropy, min_entropy, max_entropy, renyi_2, renyi_inf,
  tsallis_2, purity_inverse

Joint/correlation (new — required at layer 0):
  - mutual_information_LR              I(A_LR : B_LR)
  - mutual_information_SG              I(A_SG : B_SG)
  - correlation_entropy_LR             defined operationally (you choose; e.g. trace_distance(ρ_AB, ρ_A⊗ρ_B))
  - conditional_entropy_LR             S(A_LR | B_LR) = S(A,B) - S(B)
  - entanglement_entropy_LR            S(ρ_A_LR) where ρ_A_LR = partial trace over B
  - entanglement_entropy_SG            S(ρ_A_SG) where ρ_A_SG = partial trace over the gauge pair

## Per-layer restrictions (nested, strict subset)

Layer 0 (density-matrix base):  ALL above (both single-state AND all joint)
Layer 1 (Spin(d) rep):          fewer single-state; ALL joint still in (joint entropies
                                 should survive spinor structure since they don't break it)
Layer 2 (Clifford algebra):     fewer single-state; mutual_info STILL in; conditional
                                 entropy may drop; entanglement entropy STILL in
Layer 3 (matrix realization):   tightest. Only entanglement_entropy_{LR, SG} and
                                 mutual_information_{LR, SG} survive as the
                                 4 minimal joint measurements.

## Required invariant

admissible[k+1] ⊂ admissible[k] (strict). Codex will verify by enumerating sets.

ALSO: at every layer, when an admissible entropy is computed on a non-trivial
4-qubit state, the value must be FINITE. Codex will verify by running each.

## Required helper

`entropy_at(rho_qt, entropy_name) -> float` — must accept all joint-entropy
names AND single-state names, return finite values. For partial-trace-based
entropies, use qutip's ptrace.

## Manifold (substrate)

```python
""" + MANIFOLD.read_text() + """
```

Return ONE python code block with build_gstack_over_manifold_v2() and small
helpers. Bipartition definitions must be EXPLICIT (which qubits go in A vs B).
"""


def main():
    print(f"Prompt: {len(PROMPT)} chars\n")
    results = {"grok": None, "gemini": None}
    def cg():
        t0 = time.time()
        try:
            results["grok"] = mml.gen_grok(PROMPT)
            print(f"  [grok] in {time.time()-t0:.1f}s")
        except Exception as e: print(f"  [grok] failed: {e}")
    def cm():
        t0 = time.time()
        try:
            results["gemini"] = mml.gen_gemini(PROMPT)
            print(f"  [gemini] in {time.time()-t0:.1f}s")
        except Exception as e: print(f"  [gemini] failed: {e}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        f1, f2 = ex.submit(cg), ex.submit(cm)
        f1.result(timeout=1800); f2.result(timeout=1800)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    PROPOSED.mkdir(parents=True, exist_ok=True)
    grok_path = gemini_path = None
    if results["grok"]:
        c = mml.extract_code(results["grok"])
        if c:
            grok_path = PROPOSED / f"sim_proposed_gstack_v2_joint_grok_{ts}.py"
            grok_path.write_text(c); print(f"Saved: {grok_path.name}")
    if results["gemini"]:
        c = mml.extract_code(results["gemini"])
        if c:
            gemini_path = PROPOSED / f"sim_proposed_gstack_v2_joint_gemini_{ts}.py"
            gemini_path.write_text(c); print(f"Saved: {gemini_path.name}")

    if grok_path and gemini_path:
        print(f"\nCodex judging gstack v2 (joint+single-state) proposals...")
        decision_file = Path("/tmp/codex_gstack_v2_decision.txt")
        if decision_file.exists(): decision_file.unlink()
        instr = (
            f"Two `build_gstack_over_manifold_v2()` proposals extending the layered "
            f"g-stack with JOINT/CORRELATION entropies (mutual_info_LR, mutual_info_SG, "
            f"correlation_entropy_LR, conditional_entropy_LR, entanglement_entropy_LR, "
            f"entanglement_entropy_SG) plus all single-state entropies from v1.\n\n"
            f"REQUIRED verification: (1) strict-subset chain across layers 0→1→2→3; "
            f"(2) entropy_at(rho, name) returns finite values for every admissible name "
            f"in each layer on a non-trivial bipartite 4-qubit state; (3) joint entropies "
            f"in layer 3 must include at least entanglement_entropy_LR and "
            f"entanglement_entropy_SG plus mutual_information_LR and mutual_information_SG.\n\n"
            f"Reject any proposal that fails the strict-subset chain, or that returns "
            f"NaN/infinity from entropy_at, or that uses identical formulas for "
            f"different-named entropies.\n\n"
            f"Grok:    {grok_path}\nGemini:  {gemini_path}\n\n"
            f"Write decision to /tmp/codex_gstack_v2_decision.txt:\n"
            f"  Line 1: GROK | GEMINI | REJECT_BOTH\n"
            f"  Lines 2+: layer sizes, which joint entropies survived to layer 3,\n"
            f"            and any failed verifications.\n"
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
