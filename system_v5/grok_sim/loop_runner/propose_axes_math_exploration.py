#!/usr/bin/env python3
"""propose_axes_math_exploration.py — Grok + Gemini explore provisional choices.

This launcher is for scout work only. The six choices are not canon. They are
propositions that need room to move, split, merge, or die.

The useful output is a working chain proposal or a corpse. Existing legos are
reference examples, not authority rails. They show useful tool patterns, but a
branch may invent a new construction if it keeps the chain explicit, runnable,
and measured against a negative control.

Scope: informal scout only. Outputs land under proposed_formal_sims/.
Audit runs under the codex-ratchet python env (which has qutip).
NO writes to system_v4/probes/.

The six provisional choices, stated as plain math behaviors:

  1 — noisy evolution versus reversible evolution. Lindbladian ℒ(ρ) =
       Σ K_i ρ K_i† − ½{K_i†K_i, ρ} (CPTP) versus unitary ρ̇ = −i[H, ρ].
       Distinguishable by purity change.

  2 — same process in two frames. Lab-frame ρ̇ = L(ρ) versus
       moving-frame ρ̃̇ = V†L(Vρ̃V†)V − i[−K, ρ̃] with K = iV†V̇.
       Distinguishable by presence of geometric potential.

  3 — outer-vs-inner. The carrier/substrate is not canon. A spinor is one
       possible carrier, not the definition. Fiber/base and chirality/flux are
       possible readouts or controls only.

  4 — order of unitary U and CPTP channel E:
       Φ_UEUE = U∘E∘U∘E versus Φ_EUEU = E∘U∘E∘U. Differ iff [U,E] ≠ 0.

  5 — generator family choice: σ_z dephasing
       Lindbladian (κ/2)(σ_z ρ σ_z − ρ) vs σ_x dephasing
       (κ/2)(σ_x ρ σ_x − ρ); σ_x rotation −i[ω σ_x/2, ρ] vs σ_z
       rotation −i[ω σ_z/2, ρ].

  6 — whether damping happens before or after rotation:
       Φ_T ∘ U versus U ∘ Φ_T. Observable Δ(ρ) = Φ_T(U(ρ)) − U(Φ_T(ρ)).

These choices are propositions, not final axes. Do not promote their names.
"""
import concurrent.futures
import argparse
import json
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
RECEIPTS = HERE / "receipts" / "axes_math_exploration"
FOUNDATION_READY_SENTINEL = HERE / "receipts" / "manifold_readiness" / "READY_FOR_AXES.json"
CODEX_PY = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"

CHAIN_REQUIRED_EXPORTS = [
    "build_chain_context",
    "propose_branches",
    "run_branch_probe",
    "main",
]


PROMPT = """Propose a python module that explores PROVISIONAL GEOMETRIC CHOICES
BY BUILDING A FULL PREREQUISITE CHAIN FIRST.

Do NOT jump straight to named final machinery. That is the failure mode being
corrected. Each explored choice must be a branch from the foundation upward:

  Step 0: import/read existing geometry legos
  Step 1: construct or reference a manifold state object
  Step 2: evaluate/carry the manifold gate and OPEN foundation dependencies
  Step 3: choose one provisional distinction to test
  Step 4: run a minimal observable probe for that branch
  Step 5: only if the branch survives, optionally show how it would feed a
          later composition interface

The output can explore along the whole process, but it must show the chain.
Branches are expected. Corpses are useful.

Language rule:
- Do not use project jargon as the sim's load-bearing object.
- Use plain names for functions and branches: "unitary_vs_noisy",
  "same_map_different_frame", "outer_vs_inner_candidate",
  "order_matters_for_channel", "generator_family_choice",
  "damping_before_or_after_rotation".
- The six choices are propositions. They can be split, merged, renamed, or
  killed by the evidence. Do not call them canonical.
- Do not claim named project doctrine was built. Keep the output in plain math
  behavior and measured observables.

Substance rule:
- No toy interior that only returns shaped constants, labels, ranks, or fixed
  thresholds.
- Every SURVIVED branch needs a measured value computed from a real state or
  operator, plus a measured negative-control value.
- If a branch only demonstrates "code shape" or produces a null/constant output,
  mark it KILLED or NOT_YET_TESTED.

Tool preference:
- This is the NONCLASSICAL process. Build the core branch with PyTorch complex
  tensors/autograd plus nonclassical geometry/topology tools.
- NumPy belongs to the classical control lane (for example Carnot baselines).
  Do not use it for the core branch construction here.
- SymPy belongs to the bridge / semiclassical lane (for example Szilard bridge
  or exact symbolic sanity checks). Do not use it as the primary substrate here.
- Do not import NumPy or SymPy in this scout unless the branch is explicitly
  marked "bridge/control comparison", and never let that branch be the main
  survivor for this nonclassical target.
- Use Clifford / torch_ga for spinor, rotor, chirality, and geometric-product
  claims.
- Use TopoNetX / GUDHI / XGI / PyG / rustworkx for nested topology, incidence,
  persistence, higher-order relations, graph dynamics, and reduction DAGs.
- Use QuTiP when density-matrix/open-system semantics are load-bearing.
- Use z3/cvc5 only for real constraint checks.
- G-stack / G-tower may be needed, but it is not assumed. Treat it as a branch
  to test, with a clear observable for whether it is required.
- A SURVIVED branch must contain a real non-null measured value. If the value is
  None/null/missing, mark the branch NOT_YET_TESTED or KILLED.
- Negative controls must report an actual measured control value, not just the
  string "SURVIVED".
- Every unresolved item must preserve the literal token OPEN in main().

Existing formal sims are references, not limits. You may cite them as prior
working examples, but do not just stitch them if a cleaner PyTorch construction
gets the branch further.

Carrier: 4 qubits, Hilbert dim 16, qutip Qobjs with
  dims=[[2,2,2,2],[2,2,2,2]].

## Provisional choices to explore

### Choice 1 — noisy evolution versus reversible evolution
Choice between Lindbladian dissipator dynamics
  ℒ(ρ) = Σ_k K_k ρ K_k† − ½{K_k†K_k, ρ}   (proper CPTP, Σ K_k†K_k = I)
and unitary dynamics
  ρ̇ = −i[H, ρ]   (purity-preserving).
Distinguishable by purity Tr(ρ²) change.

### Choice 2 — same process in two frames
Same generator L, but evolved in either the lab frame
  ρ̇ = L(ρ)
or a moving frame transformed by unitary V(t)
  ρ̃̇ = V†L(Vρ̃V†)V − i[−K, ρ̃],   K = iV†V̇.
The −i[K, ρ̃] term is the geometric/Berry potential.

### Choice 3 — outer versus inner
Outer/inner is a provisional distinction. The substrate is not canon.
A spinor is an allowed candidate carrier, not the definition.
Do NOT substitute chirality/flux for this choice.
Do NOT substitute Hopf fiber/base traversal for this choice.

Allowed construction shape:
  choose a candidate carrier/substrate explicitly.
  inner branch: operation/readout acts through the internal relation of that
                carrier.
  outer branch: operation/readout acts through the external embedding, ambient
                action, or outer/exterior construction of that carrier.

Minimal observable:
  produce two density/state evolutions or two spinor readouts from the same
  starting ψ, one inner and one outer, and measure a nonzero distinguishability
  under a negative control that collapses the outer/inner choice.

Fiber/base Hopf geometry may appear only as carrier geometry or control data.
Chirality/flux may appear only as a related readout or constraint. Neither is
the identity of the outer/inner proposition.

### Choice 4 — order of two maps
Given a unitary U and a CPTP map E, the channel ordering choice is
  Φ_UEUE = U ∘ E ∘ U ∘ E   versus   Φ_EUEU = E ∘ U ∘ E ∘ U.
Differ iff [U, E] ≠ 0. Trace distance between them measures the
non-commutation magnitude.

### Choice 5 — generator family choice
A 4-way selection over single-qubit generators acting on one chosen qubit
of the 4-qubit carrier:
  family 0: σ_z dephasing,    Kraus {√(1−q) I, √q · σ_z}
  family 1: σ_x dephasing,    Kraus {√(1−q) I, √q · σ_x}
  family 2: σ_x rotation,     U_x(θ) = exp(−iθ σ_x/2)   (unitary)
  family 3: σ_z rotation,     U_z(θ) = exp(−iθ σ_z/2)   (unitary)

### Choice 6 — whether damping happens before or after rotation
Given a dissipator T and a unitary U, the precedence choice is
  "dissipator first":  ρ ↦ T(U ρ U†)
  "unitary first":     ρ ↦ U T(ρ) U†
Commutator observable: Δ(ρ) = T(U ρ U†) − U T(ρ) U†.

## Required exports

```python
classification       = "classical_baseline"
admission_scope      = "informal_scout_proposal"
promotion_allowed    = False
claim_ceiling        = "branch-chain scout only; manifold OPEN items carried"
TOOL_MANIFEST        = { ... }   # tried/used/reason per tool
TOOL_INTEGRATION_DEPTH = { ... } # "load_bearing"/"supportive"/None

OPEN_FOUNDATION_ITEMS = [...]

def build_chain_context() -> dict:
    # load/reference the foundation legos and return state, gate status,
    # OPEN dependencies, and usable callables. If a lego cannot be invoked,
    # return NOT_YET_TESTED/KILLED, never hardcode.
    ...

def propose_branches(context: dict) -> list[dict]:
    # return multiple branch readings. Each branch must name:
    # - prerequisite assumptions
    # - which OPEN items it depends on
    # - minimal observable
    # - negative controls / graveyard
    # - stop condition
    ...

def run_branch_probe(branch: dict, context: dict) -> dict:
    # run the smallest concrete probe for exactly one branch.
    # Return SURVIVED/KILLED/OPEN/NOT_YET_TESTED.
    ...

def optional_stage_interface(branch_result: dict, context: dict) -> dict:
    # optional. Demonstrate how a surviving branch might feed a future
    # stage/microstep interface WITHOUT claiming engine evidence.
    ...

def main() -> dict:
    # returns the chain context, branch list, branch probe results, corpses,
    # and claim ceiling. This is the primary artifact.
```

If you include a later-composition interface, it is only an OPTIONAL sketch and
must be marked NOT_YET_TESTED unless it is built from a branch_result that
survived the chain probe. The chain artifact is more important than an interface
function.

## Honest priors (use if helpful)

- branch A can test inner relation versus outer/exterior embedding
- branch B can test a spinor carrier without making it canonical
- branch C can use Hopf fiber/base only as a carrier/control and keep the
  proposition identified as outer/inner
- a branch may die; record it as KILLED with the exact observable
- a branch may stay OPEN; record the missing evidence and next scout

## Status vocabulary

SURVIVED / KILLED / OPEN / NOT_YET_TESTED. NOT pass/fail.

## Naming rule

Do not use project-specific labels from older runs. Use plain math names:
dephasing_z, dephasing_x, rotation_x, rotation_z, noisy_evolution,
reversible_evolution, same_map_different_frame, outer_vs_inner_candidate,
order_matters_for_channel, damping_before_or_after_rotation.

Return ONE python code block with the complete module + tests. The tests must
exercise the chain:
- run_positive: at least one branch with real upstream context
- run_negative: one corpse branch or fake-foundation control
- run_boundary: one OPEN item carried without promotion
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--require-closed-foundation",
        action="store_true",
        help="fail closed unless the manifold-readiness sentinel exists",
    )
    args = ap.parse_args()

    foundation_ready = FOUNDATION_READY_SENTINEL.exists()
    if args.require_closed_foundation and not foundation_ready:
        print("BLOCKED: --require-closed-foundation was set, but the manifold-readiness sentinel is missing.")
        print(f"Missing readiness sentinel: {FOUNDATION_READY_SENTINEL}")
        return

    PROPOSED.mkdir(parents=True, exist_ok=True)
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = RECEIPTS / ts
    run_dir.mkdir(parents=True, exist_ok=True)
    foundation_notice = {
        "foundation_ready": foundation_ready,
        "readiness_sentinel": str(FOUNDATION_READY_SENTINEL),
        "claim_ceiling": (
            "axes exploration may proceed as sidequest scouting, but outputs are "
            "not evidence that the manifold is complete and must carry OPEN "
            "foundation dependencies"
        ),
        "open_foundation_items": [
            "real is_constraint_satisfied(state) gate",
            "Bridge Xi from geometry/history to rho_AB",
            "outer versus inner proposition; substrate/carrier not canonical",
            "Connes distance versus geodesic recovery",
            "G2 exceptional case policy",
            "three-layer entropy bridge / candidate cut state",
        ],
    }
    (run_dir / "foundation_scope.json").write_text(json.dumps(foundation_notice, indent=2))
    if not foundation_ready:
        print("FOUNDATION OPEN: running axes exploration as scout-only work.")
        print("Outputs must not claim manifold completion or downstream evidence.")
        print(f"Scope receipt: {run_dir / 'foundation_scope.json'}")
    print(f"Prompt length: {len(PROMPT)} chars")
    print(f"Receipts dir:  {run_dir}\n")

    results = {"grok": None, "gemini": None}

    def call_grok():
        t0 = time.time()
        try:
            results["grok"] = mml.gen_grok(PROMPT)
            print(f"  [grok]   returned in {time.time()-t0:.1f}s "
                  f"({len(results['grok'])} chars)")
        except Exception as e:
            print(f"  [grok]   failed: {type(e).__name__}: {str(e)[:120]}")

    def call_gemini():
        t0 = time.time()
        try:
            results["gemini"] = mml.gen_gemini(PROMPT)
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
            (run_dir / f"{pool}_raw_empty.txt").write_text(
                f"Model returned nothing for pool {pool}.\n")
            continue
        code = mml.extract_code(raw)
        if not code:
            # Save raw for inspection
            (run_dir / f"{pool}_raw_no_code_block.txt").write_text(raw[:8000])
            print(f"  [{pool}] no code block extracted; raw saved")
            continue
        out = PROPOSED / f"sim_proposed_axes_math_{pool}_{ts}.py"
        out.write_text(code)
        proposals[pool] = out
        print(f"  Saved {pool}: {out.name}")

    summary = {
        "timestamp_utc": ts,
        "scope": "branched_chain_axis_exploration",
        "foundation_ready": foundation_ready,
        "promotion_allowed": False,
        "proposals": {},
    }

    if not proposals:
        print("\nNo proposals saved.")
        (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
        return

    print(f"\nAuditing {len(proposals)} proposal(s) as branched chain scouts...")
    for pool, p in proposals.items():
        # Run a chain-shape audit under codex-ratchet python. The 16x64 engine
        # contract is intentionally NOT the primary gate here; these proposals
        # are only allowed to sketch stage interfaces after the chain is built.
        script = (
            "import sys, json, importlib.util, traceback\n"
            f"spec = importlib.util.spec_from_file_location('cand', '{p}')\n"
            "cand = importlib.util.module_from_spec(spec)\n"
            "try: spec.loader.exec_module(cand)\n"
            "except Exception as e:\n"
            "    print(json.dumps({'load_error': type(e).__name__ + ': ' + str(e)[:200]}))\n"
            "    sys.exit()\n"
            f"required = {CHAIN_REQUIRED_EXPORTS!r}\n"
            "missing = [name for name in required if not hasattr(cand, name)]\n"
            "audit = {'missing_exports': missing, 'ran_main': False, 'status_terms': {}, 'shape_pass': False}\n"
            "try:\n"
            "    if hasattr(cand, 'main'):\n"
            "        result = cand.main()\n"
            "        audit['ran_main'] = True\n"
            "        text = json.dumps(result, default=str)\n"
            "        audit['status_terms'] = {k: text.count(k) for k in ['SURVIVED','KILLED','OPEN','NOT_YET_TESTED']}\n"
            "        audit['has_branches'] = 'branch' in text.lower()\n"
            "        audit['has_open_foundation'] = 'OPEN' in text and ('foundation' in text.lower() or 'Bridge' in text or 'Connes' in text)\n"
            "        audit['has_claim_ceiling'] = 'claim' in text.lower() or hasattr(cand, 'claim_ceiling')\n"
            "        audit['shape_pass'] = (not missing and audit['has_branches'] and audit['has_open_foundation'])\n"
            "        audit['result_excerpt'] = text[:2000]\n"
            "    print(json.dumps(audit, default=str))\n"
            "except Exception as e:\n"
            "    audit['main_error'] = type(e).__name__ + ': ' + str(e)[:200]\n"
            "    print(json.dumps(audit, default=str))\n"
        )
        try:
            r = subprocess.run(
                [CODEX_PY, "-c", script],
                capture_output=True, text=True, timeout=300,
            )
            stdout = r.stdout.strip()
            try:
                parsed = json.loads(stdout.splitlines()[-1] if stdout else "{}")
            except json.JSONDecodeError:
                parsed = {"stdout": stdout[:1000], "stderr": r.stderr[:500]}
        except Exception as e:
            parsed = {"runner_error": f"{type(e).__name__}: {str(e)[:200]}"}
        summary["proposals"][pool] = {"path": str(p), "audit": parsed}
        verdict = "SHAPE_OK" if parsed.get("shape_pass") else "NEEDS_REVISION"
        print(f"  {pool}: {verdict}")
        if parsed.get("missing_exports"):
            print(f"     missing exports: {parsed['missing_exports']}")
        if parsed.get("main_error"):
            print(f"     main error: {parsed['main_error'][:160]}")

    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(f"\nSummary: {run_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
