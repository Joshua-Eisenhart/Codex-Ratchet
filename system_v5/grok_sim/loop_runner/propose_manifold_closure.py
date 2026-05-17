#!/usr/bin/env python3
"""propose_manifold_closure.py — Grok + Gemini close manifold OPEN items.

Bounded exploration. The constraint: target one of THREE named OPEN items
that block "manifold working." Wide latitude in HOW; tight on WHAT.

The three OPEN items (per the doc):
  Ξ  — Bridge from geometry/history to bipartite ρ_AB. The cut-state
       functional that makes the manifold one geometric object instead
       of a bag of separate lego outputs.
  Q3 — Does Connes distance on the Hopf-bundle spectral triple recover
       geodesic distance on S²? Currently asserted by the lego, not
       verified.
  D3 — Fiber-loop vs base-lifted-loop reading. UNRESOLVED per doc:
       chirality/flux vs outer/inner. The manifold can't host axes
       until this reading is chosen.

Each model picks one OPEN item and produces a concrete numerical closure
attempt. The audit is: does the proposal produce real numbers from real
lego calls, and does the numerical evidence support the claimed closure?

Scope: informal scout. Writes proposals to proposed_formal_sims/.
Receipts under receipts/manifold_closure/<ts>/. NO writes to v4/probes.
"""
import concurrent.futures
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import multi_model_loop as mml

PROPOSED = HERE / "proposed_formal_sims"
RECEIPTS = HERE / "receipts" / "manifold_closure"
CODEX_PY = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"
PROBES = "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes"

PROMPT = f"""Close ONE manifold OPEN item. PYTORCH-FIRST NONCLASSICAL LANE.

This is the nonclassical engine lane. The project runs three SEPARATE
sim processes: classical (numpy / Carnot), semi-classical bridge (sympy /
Szilard), and nonclassical (pytorch / this lane). The substrates must
stay separated; this prompt binds the nonclassical lane.

Substrate binding (HARD):

  Core required, pytorch-first:
    torch       — density matrices, differentiable geometry, tensor
                  maps, gradients, entropy, trace distance, holonomy-
                  style numeric transport. DEFAULT SUBSTRATE.
    qutip       — Kraus maps, Lindblad evolution, channels, mesolve,
                  trace/purity semantics. Load-bearing for quantum
                  channels, NOT the primary substrate.
    clifford    — spinors, rotors, geometric product, Dirac/Clifford
                  boundary claims. Required for advanced clifford
                  topologies the manifold needs.
    z3          — finite admissibility fences, UNSAT proofs,
                  structural exclusion.
    cvc5        — second SMT/proof lane for temporal/assume-guarantee
                  contracts.

  Topology / manifold tools (use when claim requires):
    gudhi       — persistent homology, topology of sampled manifolds
    toponetx    — combinatorial/topological cell/simplicial structure
    xgi         — hypergraph and higher-order relation structure
    rustworkx   — DAGs, reduction graphs, dependency skeletons

  Equivariance / geometry:
    e3nn        — SO(3)/equivariant structure
    geomstats   — manifold metrics / geodesic comparisons

  Supportive ONLY — do NOT use as default substrate:
    sympy       — symbolic sanity checks only (sympy is the bridge
                  lane's substrate, not this one)
    numpy       — low-level fallback only (numpy is the classical
                  lane's substrate, not this one)

If you write a density matrix, prefer torch. If you write a channel,
qutip Kraus form. If you compute holonomy / Chern form / curvature,
use the existing torch foundations. If you reach for numpy or sympy
for a load-bearing operation, you've drifted into the wrong lane.

The goal is to make "manifold working" stop being a scout-claim and
start being a numerically-verified property. You may pick from:

  Ξ  — Bridge: from a geometric state on the 4-qubit Hopf carrier to a
       bipartite density matrix ρ_AB. The cut on (A, B) is YOUR choice
       (e.g. A = q0+q1, B = q2+q3, or A = Weyl-left, B = Weyl-right).
       Produce a callable bridge_xi(state) → ρ_AB and verify it returns
       a valid 4-qubit density matrix that depends non-trivially on
       inputs. Bonus: report S(A|B), I(A:B), I_c(A⟩B) on the produced
       ρ_AB and confirm I_c is signed (can be negative on entangled
       inputs).

  Q3 — Connes ↔ geodesic check. Compute Connes distance via
       sim_spectral_triple_connes_distance.connes_distance_points(N, j, k)
       for several point pairs (j, k) on a discretized S². Compute the
       great-circle (geodesic) distance on S² for the same pairs.
       Verify whether the two rankings agree (same monotone order) or
       diverge. Report ranking-agreement fraction and the smallest
       counterexample pair if any.

  D3 — fiber vs base-lifted reading. Build both γ_f(u) and γ_b(u) on a
       fixed (φ₀, χ₀, η₀); compute ρ(u) along each; verify ρ_f(u) is
       u-stationary within 1e-9 AND ρ_b(u) is u-traversing. Then go
       further: probe whether THIS distinction also picks out a
       chirality (Weyl-L vs Weyl-R) projector — i.e. is the
       inner/outer split equivalent to a chirality split on the
       associated bundle E = S³ ×_SU(2) ℂ²? Report numerical
       evidence either way.

## Hard constraints

- USE EXISTING LEGOS via importlib.util.spec_from_file_location. Paths
  (note which are torch-substrate vs qutip vs other):

  torch substrate (preferred):
    {PROBES}/sim_holonomy_torch_foundation.py
    {PROBES}/sim_chern_weil_torch_foundation.py
    {PROBES}/sim_density_matrix_parallel_transport_holonomy_survivor_classes.py
    {PROBES}/sim_hopf_projection_s3_s2_phase_invariant_survivor_classes.py
    {PROBES}/sim_hopf_connection_one_form_loop_integral_survivor_classes.py

  qutip substrate (channels / Kraus):
    {PROBES}/sim_assoc_bundle_weyl_spinor_as_section.py
    {PROBES}/sim_lego_coherent_info_advanced.py
    {PROBES}/sim_lego_entropy_bipartite_cut.py

  clifford substrate (geometric algebra):
    look for sim_clifford_*.py under {PROBES}/

  spectral triple / z3:
    {PROBES}/sim_spectral_triple_connes_distance.py

  embedding (classical_baseline, use ONLY for sanity reference, NOT
  as a load-bearing substrate for nonclassical claims):
    {PROBES}/sim_hopf_fibration_embedding_classical.py

- Real numbers from real lego calls. NO hardcoded constants for results.
- If a lego call raises, report the trace; do NOT substitute a fake.
- Density matrices: torch tensors by default. qutip Qobjs with
  dims=[[2,2,2,2],[2,2,2,2]] when crossing into channel semantics.
- Status vocabulary: SURVIVED / KILLED / OPEN / NOT_YET_TESTED.
- Banned identifiers: `axis`, `Ax0..Ax6`, `gstack`, `terrain`, `Ti/Te/Fi/Fe`
  as function names, `prime_resonance`, `Carnot` (that's the classical
  lane's name, not ours), `Szilard` (bridge lane's, not ours), `IGT`,
  `Jung`, `outer_loop`, `inner_loop`, `Type 1/2`.

## Module shape

```python
\"\"\"sim_proposed_manifold_close_<item>_<approach>.py — closure attempt.\"\"\"
classification = "classical_baseline"
admission_scope = "informal_scout_proposal"
promotion_allowed = False
claim_ceiling = "<what you actually proved or did not prove>"
TARGETED_OPEN_ITEM = "<one of: Bridge_Xi | Connes_Geodesic_Q3 | D3_Reading>"

TOOL_MANIFEST = {{ ... }}
TOOL_INTEGRATION_DEPTH = {{ ... }}

# Your closure callables (depends on which item you chose):
def bridge_xi(state) -> "qt.Qobj":       # if you chose Ξ
def connes_vs_geodesic_check() -> dict:  # if you chose Q3
def d3_reading() -> dict:                # if you chose D3

def main() -> dict:
    \"\"\"Returns dict with status SURVIVED/KILLED/OPEN/NOT_YET_TESTED for
    the closure attempt, evidence values, and honest claim ceiling.\"\"\"
    ...
```

## What makes a SURVIVED closure

- Ξ: returns a valid 4-qubit density matrix (Hermitian, Tr=1, PSD within
  1e-9) that VARIES under input variation (3 different inputs → 3
  different ρ_AB with pairwise trace distance > 0.03), AND I_c on one
  input is signed (≥ 0 for product state, < 0 possible for entangled).

- Q3: report the ranking-agreement fraction. SURVIVED if ≥ 0.95
  (agreement is the empirical claim, not asserted). KILLED if < 0.5
  (Connes and geodesic disagree most pairs). OPEN otherwise.

- D3: SURVIVED if ρ_f(u) shows |ρ_f(u₁)−ρ_f(u₂)|₁ < 1e-9 for sampled
  u₁,u₂ AND ρ_b(u) shows |ρ_b(u₁)−ρ_b(u₂)|₁ > 0.03 for at least one
  pair AND the chirality probe yields a concrete same-or-different
  verdict (with the numerical evidence).

Wide latitude in HOW. Tight on WHAT.

Return ONE python code block with the complete module.
"""


def main():
    PROPOSED.mkdir(parents=True, exist_ok=True)
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = RECEIPTS / ts
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"Prompt: {len(PROMPT)} chars · run: {run_dir}\n")

    results = {"grok": None, "gemini": None}

    def call_grok():
        t0 = time.time()
        try:
            results["grok"] = mml.gen_grok(PROMPT)
            print(f"  grok   returned {time.time()-t0:.1f}s ({len(results['grok'])} chars)")
        except Exception as e:
            print(f"  grok   failed: {type(e).__name__}: {str(e)[:120]}")

    def call_gemini():
        t0 = time.time()
        try:
            results["gemini"] = mml.gen_gemini(PROMPT)
            print(f"  gemini returned {time.time()-t0:.1f}s ({len(results['gemini'])} chars)")
        except Exception as e:
            print(f"  gemini failed: {type(e).__name__}: {str(e)[:120]}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        f_g, f_m = ex.submit(call_grok), ex.submit(call_gemini)
        f_g.result(timeout=1800); f_m.result(timeout=1800)

    proposals = {}
    summary = {"timestamp_utc": ts, "proposals": {}}
    for pool, raw in results.items():
        if not raw:
            (run_dir / f"{pool}_empty.txt").write_text("model returned nothing")
            continue
        code = mml.extract_code(raw)
        if not code:
            (run_dir / f"{pool}_no_code.txt").write_text(raw[:6000])
            continue
        out = PROPOSED / f"sim_proposed_manifold_close_{pool}_{ts}.py"
        out.write_text(code)
        proposals[pool] = out
        print(f"  saved {pool}: {out.name}")

    # Quick smoke audit: load + call main() under codex-ratchet python.
    for pool, p in proposals.items():
        script = (
            "import sys, json, importlib.util, traceback\n"
            f"spec = importlib.util.spec_from_file_location('cand', '{p}')\n"
            "cand = importlib.util.module_from_spec(spec)\n"
            "try:\n"
            "    spec.loader.exec_module(cand)\n"
            "    targeted = getattr(cand, 'TARGETED_OPEN_ITEM', None)\n"
            "    r = cand.main() if hasattr(cand,'main') else None\n"
            "    out = {'targeted': targeted, 'main_returned': bool(r), 'status_field': (r.get('status') if isinstance(r, dict) else None)}\n"
            "    # surface a few top-level numeric keys for visibility\n"
            "    if isinstance(r, dict):\n"
            "        out['top_keys'] = list(r.keys())[:12]\n"
            "    print(json.dumps(out, default=str))\n"
            "except Exception as e:\n"
            "    print(json.dumps({'error': type(e).__name__ + ': ' + str(e)[:300]}))\n"
        )
        try:
            r = subprocess.run([CODEX_PY, "-c", script],
                               capture_output=True, text=True, timeout=120)
            out_lines = r.stdout.strip().splitlines()
            parsed = json.loads(out_lines[-1]) if out_lines else {"stderr": r.stderr[:400]}
        except Exception as e:
            parsed = {"runner_error": f"{type(e).__name__}: {str(e)[:200]}"}
        summary["proposals"][pool] = {"path": str(p), "smoke": parsed}
        print(f"  {pool}: targeted={parsed.get('targeted')} status={parsed.get('status_field')} keys={parsed.get('top_keys')}")

    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(f"\nsummary: {run_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
