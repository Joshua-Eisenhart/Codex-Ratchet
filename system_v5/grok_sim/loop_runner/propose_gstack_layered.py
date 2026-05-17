#!/usr/bin/env python3
"""propose_gstack_layered.py — Grok+Gemini propose build_gstack_over_manifold().

Layered g-stack on top of the constraint manifold. Each successive layer
restricts the admissible entropy set MORE. Base layer = density-matrix
geometry; each nested layer narrows what entropies can run on it.
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


PROMPT = """Propose `build_gstack_over_manifold(manifold_dict) -> dict` — the layered
g-stack constructed ON TOP of the geometric constraint manifold. Each layer
restricts the admissible entropy set MORE than the prior layer (nested
restrictions). This is the structure under which axes will eventually run.

## Concrete construction

Input: the dict returned by `build_constraint_manifold()` (provided below as
context). Build a sequence of 4 nested layers, each with:

  - `name`: short identifier
  - `parent_layer_index`: int (or None for base)
  - `admissible_entropies`: a set/list of entropy *types* allowed at this layer.
    Use the symbolic names: "von_neumann", "linear_entropy", "renyi_2",
    "renyi_inf", "min_entropy", "max_entropy", "tsallis_2", "purity_inverse".
  - `entropy_admissibility_check(rho_qt, entropy_name) -> bool`: True iff
    the named entropy of rho is well-defined AND finite AND within the layer's
    bounds.
  - `tangent_subspace_qt`: list of Hermitian generators (Qobjs) that act
    WITHIN this layer (subset of the manifold's tangent generators that this
    layer preserves).

## Layer ordering (binding — nested restrictions)

Layer 0 (base):       density-matrix geometry. Admissible: ALL listed entropies
                       are well-defined on a 4-qubit density matrix.
Layer 1 (Spin(d) rep): Spinor structure imposed. Admissible: a subset of
                       layer 0 (e.g. exclude entropies that don't respect
                       spinor double cover, or that require non-spinor
                       observables).
Layer 2 (Clifford alg): Clifford algebra Cl(d) structure. Admissible: subset
                        of layer 1. Restrict to entropies compatible with
                        Clifford grading.
Layer 3 (matrix realization): tightest restriction. Admissible: subset of
                              layer 2. Only entropies that depend on the
                              explicit matrix form survive.

## Required invariant (verified at runtime)

`admissible_entropies[k+1] ⊂ admissible_entropies[k]` for every k. If your
proposal does not satisfy this strict-subset relation, it's wrong. Codex will
verify this by enumerating the four sets.

## Hard constraints

- Use qutip + numpy. Qobjs use dims=[[2,2,2,2],[2,2,2,2]].
- Each `entropy_admissibility_check` must ACTUALLY compute or reference the
  entropy in question. No hardcoded `return True` for the base layer.
- Reject proposals that smuggle entropies INTO higher layers that the base
  doesn't admit — restrictions are monotone DOWN, never adding.
- NO decorative tools — if your manifest claims a tool is load-bearing, USE it.
- Tangent subspaces at higher layers must be subsets of the base manifold's
  tangents.

## Return shape

```python
{
    "manifold_ref": manifold_dict,     # echo input
    "layers": [
        {
            "index": 0, "name": "density_matrix_base", "parent_layer_index": None,
            "admissible_entropies": [...],
            "entropy_admissibility_check": callable,
            "tangent_subspace_qt": [G0, G1, ..., G6],
        },
        {
            "index": 1, "name": "spin_d_rep", "parent_layer_index": 0,
            "admissible_entropies": [strict subset],
            "entropy_admissibility_check": callable,
            "tangent_subspace_qt": [subset of layer 0's tangents],
        },
        # ... layer 2 and 3 ...
    ],
    "entropy_at": callable,            # (rho_qt, entropy_name) -> float | None
    "is_layered_consistent": callable, # -> bool: verifies strict-subset chain
}
```

## Manifold (the substrate; already accepted)

```python
""" + MANIFOLD.read_text() + """
```

Return ONE python code block with the complete `build_gstack_over_manifold()`
function and small helpers. Do NOT include other primitives.
"""


def main():
    print(f"Prompt: {len(PROMPT)} chars")
    print(f"Calling Grok + Gemini in parallel for build_gstack_over_manifold()...\n")
    results = {"grok": None, "gemini": None}
    def cg():
        t0 = time.time()
        try:
            results["grok"] = mml.gen_grok(PROMPT)
            print(f"  [grok] returned in {time.time()-t0:.1f}s")
        except Exception as e: print(f"  [grok] failed: {e}")
    def cm():
        t0 = time.time()
        try:
            results["gemini"] = mml.gen_gemini(PROMPT)
            print(f"  [gemini] returned in {time.time()-t0:.1f}s")
        except Exception as e: print(f"  [gemini] failed: {e}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(cg); f2 = ex.submit(cm)
        f1.result(timeout=1800); f2.result(timeout=1800)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    PROPOSED.mkdir(parents=True, exist_ok=True)
    grok_path = gemini_path = None
    if results["grok"]:
        c = mml.extract_code(results["grok"])
        if c:
            grok_path = PROPOSED / f"sim_proposed_gstack_layered_grok_{ts}.py"
            grok_path.write_text(c); print(f"Saved: {grok_path.name}")
    if results["gemini"]:
        c = mml.extract_code(results["gemini"])
        if c:
            gemini_path = PROPOSED / f"sim_proposed_gstack_layered_gemini_{ts}.py"
            gemini_path.write_text(c); print(f"Saved: {gemini_path.name}")

    if grok_path and gemini_path:
        print(f"\nCodex (GPT-5.5 LOW) judging gstack layered proposals...")
        decision_file = Path("/tmp/codex_gstack_layered_decision.txt")
        if decision_file.exists(): decision_file.unlink()
        instr = (
            f"Two proposals for `build_gstack_over_manifold(manifold_dict)` — a layered "
            f"g-stack on top of the constraint manifold. Each layer must restrict admissible "
            f"entropies STRICTLY MORE than the prior (subset chain). Pick the more honest:\n\n"
            f"Grok:    {grok_path}\nGemini:  {gemini_path}\n\n"
            f"REQUIRED verification you must run: import the manifold, call build_constraint_manifold(), "
            f"pass it to each proposal's build_gstack_over_manifold(), and check that "
            f"layers[k+1].admissible_entropies is a STRICT SUBSET of layers[k].admissible_entropies "
            f"for k in 0,1,2. Reject any proposal where this fails.\n\n"
            f"Also test: pass a non-trivial 4-qubit rho through entropy_at(rho, name) for each "
            f"name in layer 0's admissible_entropies; reject if any returns NaN/infinity.\n\n"
            f"Write decision to /tmp/codex_gstack_layered_decision.txt:\n"
            f"  Line 1: GROK | GEMINI | REJECT_BOTH\n"
            f"  Lines 2+: justification with the actual admissible-set sizes per layer\n"
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
