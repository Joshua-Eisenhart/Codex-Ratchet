#!/usr/bin/env python3
"""propose_engine_exploration.py — Grok + Gemini freely propose engine_stage.

Free exploration. The proposer gives both models room to choose their math
approach: which generators, which composition order, which substage cycle,
how engine A and B differ. The CONTRACT (kept hidden from the prompt) is the
clean 16-placement × 64-microstep uniqueness target at
  loop_runner/contracts/contract_engine_16_placement_64_microstep_uniqueness.py.

What they DO see:
  - The engine target (2 engines × 8 stages × 4 substages = 64 microsteps)
  - The math goal (uniqueness within, across, and geometric dependence)
  - The named failure modes (constant output, label shortcuts, mod-n hash,
    number-theory smuggle, input-ignoring)
  - The available manifold legos (paths only, they can import via importlib)
  - NO numeric thresholds, NO specific axis count, NO Phase 32/98 framing

What they DON'T see:
  - The threshold values (TAU_IN, TAU_CROSS, TAU_GEOM)
  - The specific test states (zero4, plus4, max_mixed)
  - The check list

Each proposal is a standalone module under proposed_formal_sims/. The
contract runs against it after writing. Receipts land in a clean dir.

Scope: informal scout only. Outputs go to:
  proposed_formal_sims/sim_proposed_engine_stage_exploration_<pool>_<ts>.py
  receipts/engine_exploration/<ts>/
No writes to system_v4/probes/.
"""
import concurrent.futures
import json
import os
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import multi_model_loop as mml

PROPOSED = HERE / "proposed_formal_sims"
RECEIPTS = HERE / "receipts" / "engine_exploration"
PROBES = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes")
CONTRACT_PATH = HERE / "contracts" / "contract_engine_16_placement_64_microstep_uniqueness.py"
PYTHON_BIN = Path("/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3")


def build_exploration_prompt() -> str:
    return """Propose a python module exporting:

    def engine_stage(engine_id: str, stage_idx: int,
                     substage_idx: int, input_rho_qt) -> dict

The function applies an information-processing step to a 4-qubit density
matrix and returns a dict with key "output_rho_qt" holding the post-step
4-qubit density matrix (qutip Qobj with dims=[[2,2,2,2],[2,2,2,2]]).

## The engine architecture

Two engine types (engine_id ∈ {"A", "B"}). Eight stages per engine
(stage_idx ∈ 0..7). Four substages per stage (substage_idx ∈ 0..3).
That's 64 microstep outputs total per input state. The structure of those
64 outputs is the engine.

## What "running" means here

The 64 microstep outputs must satisfy three things:

1. UNIQUENESS WITHIN ENGINE: for each engine, the 32 microstep outputs
   are pairwise distinct (no two microsteps produce the same density
   matrix). 8 stages × 4 substages = 32 distinct points.

2. UNIQUENESS ACROSS ENGINES: every output for engine A is distinct from
   every output for engine B. The two engines trace distinguishable
   trajectories.

3. GEOMETRIC DEPENDENCE: the 64 microstep outputs vary nontrivially with
   the INPUT state. Replacing input_rho_qt with a different state must
   produce a different 64-output table. The engine is responding to
   input geometry, not just consuming index labels.

## Honest failure modes (named graveyards)

These will be auto-rejected; do NOT do these:

- Output the same density matrix for all 64 (engine, stage, substage)
  tuples — constant engine, fails uniqueness.
- Make the output depend ONLY on the index tuple (engine_id, stage_idx,
  substage_idx) and ignore input_rho_qt — that's a label shortcut, not
  a physical engine.
- Use `hash(...)`, `% stage_idx`, classical primality, totient, gcd,
  divisors, or any number-theoretic operation to manufacture uniqueness
  — that's a hash bypass, not honest physics.
- Use distinct STRING LABELS as the only difference — uniqueness must
  come from algebraic structure on the carrier.

## Available manifold legos (read-only references, you may import via importlib)

Existing geometry sims under system_v4/probes/. You MAY load and call
these to build your engine if useful. You DO NOT have to.

  sim_hopf_fibration_embedding_classical.py      → hopf(x), rand_S3(n)
  sim_hopf_projection_s3_s2_phase_invariant_survivor_classes.py
                                                  → hopf(psi) [torch]
  sim_hopf_connection_one_form_loop_integral_survivor_classes.py
                                                  → connection_integral(eta, phi_w, chi_w)
  sim_hopf_connection_u1_curvature_base_form_survivor_classes.py
                                                  → main() returns curvature_coeff
  sim_chern_weil_torch_foundation.py             → chern_form_c1(F)
  sim_holonomy_torch_foundation.py               → connection_along_loop(loop, winding),
                                                     holonomy_around_loop(A_loop)
  sim_density_matrix_parallel_transport_holonomy_survivor_classes.py
                                                  → spinor_path(eta, phi_w, chi_w),
                                                    transport_phase(path),
                                                    endpoint_density_gap(path)
  sim_holonomy_group_classifies_gtower_shell.py  → holonomy_rotor(shell, level)
  sim_gtower_full_chain.py                       → classify_complex(M)
  sim_gtower_reduction_chain_composition.py      → tier_trace(M)
  sim_assoc_bundle_weyl_spinor_as_section.py     → su2(axis, angle), spinor_to_s2(psi)
  sim_spectral_triple_connes_distance.py         → connes_distance_points(N, j, k)
  sim_geom_noncomm_z3_unsat_order_swap.py        → run_positive_tests()

You can also use qutip + numpy + scipy + torch directly. You're free to
choose generators, composition rules, sign conventions, substage
patterns. The math approach is yours.

## Honest priors (not constraints, just hints — ignore if you have a
## better idea)

- Engine A and engine B can differ by a global sign on the Hamiltonian,
  by a chirality projection, or by some other involution.
- Substages can cycle through 4 different Pauli rotations on different
  qubits.
- The 8 stages could traverse 8 different operators with the constraint
  that ALL 32 outputs per engine are distinct.

But these are priors. If you have a different way to make 64 microsteps
all unique AND input-dependent, do that.

## Module shape

Return ONE python code block:

```python
\"\"\"sim_proposed_engine_stage_exploration_<your_approach>.py — engine_stage.

Informal scout proposal. NOT canonical evidence.
\"\"\"
import qutip as qt
import numpy as np
# ... (your imports)

classification = "classical_baseline"
admission_scope = "informal_scout_proposal"
promotion_allowed = False
claim_ceiling = "<honest description of what this engine does>"

TOOL_MANIFEST = { ... }              # match the project's tried/used/reason shape
TOOL_INTEGRATION_DEPTH = { ... }     # "load_bearing" / "supportive" / None

def engine_stage(engine_id: str, stage_idx: int,
                 substage_idx: int, input_rho_qt) -> dict:
    ...
    return {"output_rho_qt": rho_out,
            "engine_id": engine_id, "stage_idx": stage_idx,
            "substage_idx": substage_idx,
            # optional: any introspection you want to expose
            }

# Tests
def run_positive() -> dict:
    \"\"\"You define the positive test that's strongest for YOUR
    approach. Common patterns: enumerate all 64 microsteps on a
    non-trivial input, verify pairwise distinct, verify input
    dependence.\"\"\"
    ...

def run_negative() -> dict:
    \"\"\"Run YOUR negative control: e.g. set engine_id = engine_id
    and confirm output is preserved; or replace input with a fixed
    state and confirm outputs collapse appropriately.\"\"\"
    ...

def run_boundary() -> dict:
    \"\"\"Edge case: stage_idx = 0, substage_idx = 0, both engines,
    confirm output is honest.\"\"\"
    ...

def main() -> dict:
    return {"positive": run_positive(),
            "negative": run_negative(),
            "boundary": run_boundary()}
```

## Status vocabulary

Status fields use SURVIVED / KILLED / OPEN / NOT_YET_TESTED. NOT pass/fail.
Banned identifiers in your code: `axis`, `Ax0..Ax6`, `gstack`, `terrain`,
`Ti`/`Te`/`Fi`/`Fe` (as function or string-literal labels),
`prime_resonance`, `hexagram`, `Carnot`, `Szilard`, `IGT`, `Jung`.

Return ONE python code block with the complete module.
"""


def audit_proposal_with_repo_python(path: Path) -> dict:
    """Run the hidden contract under the repo's sim Python.

    The default shell Python on this machine does not have the SIM/QIT runtime
    dependencies such as QuTiP. Auditing in that interpreter creates false
    import failures instead of testing the proposal's math.
    """
    script = r"""
import importlib.util
import json
import traceback
from pathlib import Path

proposal = Path(__import__("sys").argv[1])
contract_path = Path(__import__("sys").argv[2])

receipt = {"proposal_path": str(proposal), "errors": []}
try:
    spec = importlib.util.spec_from_file_location("_candidate", str(proposal))
    cand = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cand)

    spec2 = importlib.util.spec_from_file_location("_contract", str(contract_path))
    contract = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(contract)

    result = contract.run(cand)
    receipt["contract_pass"] = result.get("pass")
    receipt["failures"] = result.get("failures", [])[:8]
    receipt["metrics"] = result.get("metrics", {})
except Exception as e:
    receipt["contract_pass"] = False
    receipt["errors"].append(f"{type(e).__name__}: {str(e)[:200]}")
    receipt["errors"].append(traceback.format_exc()[:400])

print(json.dumps(receipt, default=str))
"""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(HERE) + os.pathsep + env.get("PYTHONPATH", "")
    cp = subprocess.run(
        [str(PYTHON_BIN), "-c", script, str(path), str(CONTRACT_PATH)],
        cwd=str(HERE.parent.parent.parent),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if cp.returncode != 0:
        return {
            "proposal_path": str(path),
            "contract_pass": False,
            "errors": [f"repo-python audit exited {cp.returncode}", cp.stderr[:400], cp.stdout[:400]],
        }
    try:
        return json.loads(cp.stdout)
    except Exception:
        return {
            "proposal_path": str(path),
            "contract_pass": False,
            "errors": ["repo-python audit produced unparsable JSON", cp.stdout[:400], cp.stderr[:400]],
        }


def main():
    PROPOSED.mkdir(parents=True, exist_ok=True)
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = RECEIPTS / ts
    run_dir.mkdir(parents=True, exist_ok=True)

    prompt = build_exploration_prompt()
    print(f"Prompt length: {len(prompt)} chars")
    print(f"Receipts dir:  {run_dir}")
    print(f"Firing Grok 4.3 + Gemini 3.1-pro in parallel (no model coordination)...\n")

    results = {"grok": None, "gemini": None}

    def call_grok():
        t0 = time.time()
        try:
            results["grok"] = mml.gen_grok(prompt)
            print(f"  [grok]   returned in {time.time()-t0:.1f}s "
                  f"({len(results['grok'])} chars)")
        except Exception as e:
            print(f"  [grok]   failed: {type(e).__name__}: {str(e)[:120]}")

    def call_gemini():
        t0 = time.time()
        try:
            results["gemini"] = mml.gen_gemini(prompt)
            print(f"  [gemini] returned in {time.time()-t0:.1f}s "
                  f"({len(results['gemini'])} chars)")
        except Exception as e:
            print(f"  [gemini] failed: {type(e).__name__}: {str(e)[:120]}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        f_g, f_m = ex.submit(call_grok), ex.submit(call_gemini)
        f_g.result(timeout=1800); f_m.result(timeout=1800)

    proposals = {}
    for pool, raw in results.items():
        if not raw:
            continue
        code = mml.extract_code(raw)
        if not code:
            continue
        out = PROPOSED / f"sim_proposed_engine_stage_exploration_{pool}_{ts}.py"
        out.write_text(code)
        proposals[pool] = out
        print(f"  Saved {pool}: {out.name}")

    # Audit each proposal against the binding contract.
    if not proposals:
        print("\nNo proposals saved. Done.")
        return
    print(f"\nAuditing {len(proposals)} proposal(s) against:")
    print(f"  {CONTRACT_PATH.name}\n")

    summary = {"timestamp_utc": ts,
               "contract": str(CONTRACT_PATH),
               "proposals": {}}

    for pool, p in proposals.items():
        receipt = audit_proposal_with_repo_python(p)
        summary["proposals"][pool] = receipt
        verdict = "PASSED" if receipt.get("contract_pass") else "FAILED"
        print(f"  {pool}: {verdict}")
        if receipt.get("failures"):
            for f in receipt["failures"][:3]:
                print(f"     - {f.get('check')}: {f.get('msg', '')[:120]}")

    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(f"\nSummary: {run_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
