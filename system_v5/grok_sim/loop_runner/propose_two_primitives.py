#!/usr/bin/env python3
"""propose_two_primitives.py — Grok+Gemini propose axis_transform + terrain_operation in parallel.

4 parallel API calls total (each gen × each function). Codex picks 1 winner per function.
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
MANIFOLD = CANDIDATES / "manifold_proposal_gemini_20260514T000643Z.py"


PROMPT_AXIS = """Implement `axis_transform(axis_index: int, input_rho_qt) -> dict` for a
4-qubit Hopf-fibered Weyl-carrier simulator. The geometric constraint manifold is built;
axes are DoFs IN this manifold and your output MUST stay on it.

## Key rule

Use the tangent generators from `build_constraint_manifold()['axis_dof_map']`. Apply
exp(-i α G_i / 2) to the input where G_i is the tangent generator for axis i. This
keeps the output on the manifold (unitary flow along a tangent stays tangent).

## Return shape

```python
{
    "axis_index": int,
    "output_rho_qt": qt.Qobj,            # 4-qubit, dims=[[2,2,2,2],[2,2,2,2]]
    "info_change_bits": float,            # ΔS in bits
    "trace_distance_from_input": float,
    "fingerprint": list[float],           # probe expectations on output (≥4-vector)
}
```

## Constraints

- The 7 axes (i=0..6) must produce GENUINELY DISTINCT outputs (pairwise td > 0.03 on a
  non-trivial input). Distinctness from architecture, NOT hash.
- Each output must be on the manifold (`is_constraint_satisfied(output) == True`).
- Deterministic.

## Manifold module (already accepted)

```python
""" + MANIFOLD.read_text() + """
```

Return ONE python code block with just `axis_transform()` and any small helpers.
"""


PROMPT_TERRAIN = """Implement `terrain_operation(terrain: str, input_rho_qt, strength: float = 0.5) -> dict`
for the 4-qubit carrier with manifold constraint. There are 4 terrains:
- Ti: σ_z dephasing dissipator. operator_type="dissipator". purity can decrease.
- Te: σ_x dephasing dissipator. operator_type="dissipator". purity can decrease.
- Fi: σ_x rotation unitary. operator_type="unitary". purity preserved within 1e-6.
- Fe: σ_z rotation unitary. operator_type="unitary". purity preserved within 1e-6.

## Return shape

```python
{
    "terrain": str,
    "operator_type": str,                # "dissipator" or "unitary"
    "output_rho_qt": qt.Qobj,            # 4-qubit, dims=[[2,2,2,2],[2,2,2,2]]
    "info_change_bits": float,
    "purity_input": float,
    "purity_output": float,
    "trace_distance_from_input": float,
}
```

## Hard constraints

- Ti/Te are dissipators (Lindblad-channel implementation; purity allowed to decrease).
- Fi/Fe are unitaries (single qutip operator U; purity = Tr(ρ²) preserved within 1e-6).
- All 4 must produce DISTINCT outputs on a non-trivial input (pairwise td > 0.03).
- Ti and Te affect different bases (Ti destroys Z-basis coherence, Te destroys X-basis).
- Fi and Fe rotate around DIFFERENT axes; commutator [Fi-action, Fe-action] != 0.
- Qobjs use `dims=[[2,2,2,2],[2,2,2,2]]`.
- NO hardcoded magic numbers tuned to pass thresholds.

Return ONE python code block with just `terrain_operation()` and any helpers.
"""


def call(prompt, generator_name):
    if generator_name == "grok":
        return mml.gen_grok(prompt)
    elif generator_name == "gemini":
        return mml.gen_gemini(prompt)


def main():
    targets = [
        ("axis_transform", PROMPT_AXIS),
        ("terrain_operation", PROMPT_TERRAIN),
    ]
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    results = {}  # (target, generator) -> (path or None)

    print(f"Calling Grok + Gemini in parallel for axis_transform AND terrain_operation (4 calls total)...\n")
    def call_and_save(target_name, gen_name, prompt):
        t0 = time.time()
        try:
            resp = call(prompt, gen_name)
            print(f"  [{gen_name} / {target_name}] returned in {time.time()-t0:.1f}s ({len(resp)} chars)")
            code = mml.extract_code(resp)
            if code:
                path = CANDIDATES / f"{target_name}_proposal_{gen_name}_{ts}.py"
                path.write_text(code)
                results[(target_name, gen_name)] = path
                return path
        except Exception as e:
            print(f"  [{gen_name} / {target_name}] failed: {type(e).__name__}: {str(e)[:100]}")
            results[(target_name, gen_name)] = None
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        futs = []
        for target_name, prompt in targets:
            for gen_name in ("grok", "gemini"):
                futs.append(ex.submit(call_and_save, target_name, gen_name, prompt))
        for f in concurrent.futures.as_completed(futs):
            f.result()

    # Codex judges each function separately
    for target_name, _ in targets:
        grok_path = results.get((target_name, "grok"))
        gemini_path = results.get((target_name, "gemini"))
        if not (grok_path and gemini_path):
            print(f"\nMissing proposal for {target_name}; skipping judge")
            continue
        print(f"\nCodex judging {target_name}...")
        decision_file = Path(f"/tmp/codex_{target_name}_decision.txt")
        if decision_file.exists(): decision_file.unlink()
        instr = (
            f"Two generators proposed `{target_name}()` for a manifold-aware 4-qubit simulator.\n"
            f"Pick the more honest one. Check for: hash-style modular distinctness, classical-primality\n"
            f"sieves, hardcoded thresholds, index-arithmetic signatures, decorative tool claims,\n"
            f"and adherence to the function's stated semantics (manifold tangency for axis_transform;\n"
            f"correct dissipator/unitary type for terrain_operation).\n\n"
            f"Grok:    {grok_path}\nGemini:  {gemini_path}\n\n"
            f"Write decision to /tmp/codex_{target_name}_decision.txt:\n"
            f"  Line 1: GROK or GEMINI or REJECT_BOTH\n"
            f"  Lines 2+: justification.\n"
        )
        t0 = time.time()
        r = subprocess.run(
            ["codex", "exec",
             "-c", 'model_reasoning_effort="low"',
             "-C", str(HERE.parent), "-s", "workspace-write",
             "--skip-git-repo-check", instr],
            capture_output=True, text=True, timeout=900,
        )
        print(f"  Codex done in {time.time()-t0:.1f}s")
        if decision_file.exists():
            print(f"\n=== Codex decision on {target_name} ===\n{decision_file.read_text()}\n")
        else:
            print(f"  No decision file written. stdout tail:\n  {r.stdout[-400:]}")


if __name__ == "__main__":
    main()
