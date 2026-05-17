#!/usr/bin/env python3
"""propose_manifold_foundation_repair.py.

Bounded high-exploration lane for Grok/Gemini.

Each run targets exactly one unresolved manifold-foundation item. Models may
explore many branches inside that target, but they must not jump to named final
machinery, prime probes, or entropy engines as final claims.

Existing legos are references, not authority rails. They show what has worked
and which tools behaved load-bearing, but proposals may invent new constructions
when the chain requires it.
"""

import argparse
import concurrent.futures
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import sys

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import multi_model_loop as mml

RECEIPTS = HERE / "receipts" / "manifold_foundation_repair"
PROPOSED = HERE / "proposed_formal_sims"
HAND_BUILT = HERE / "proposed_formal_sims" / "sim_proposed_constraint_manifold_assembly_handbuilt.py"
COMPONENT_MAP = HERE / "COMPONENT_MAP.md"

TARGETS = {
    "state_gate": "make is_constraint_satisfied(state) more load-bearing beyond density-matrix validity",
    "bridge_xi": "Bridge Xi from geometry/history to rho_AB",
    "ax3_reading": "outer versus inner proposition; substrate/carrier not canonical",
    "connes_geodesic": "Connes distance versus S2 geodesic recovery",
    "g2_policy": "G2 exceptional case policy in the reduction chain",
    "entropy_bridge": "three-layer entropy bridge / candidate cut state",
}


def _read(path: Path, limit: int = 22000) -> str:
    try:
        return path.read_text()[:limit]
    except Exception as e:
        return f"[UNREADABLE {path}: {type(e).__name__}: {e}]"


def build_prompt(target: str) -> str:
    return f"""You are proposing a bounded manifold-foundation repair.

Target: {target} — {TARGETS[target]}

Outer/inner correction:
- Outer versus inner is a proposition, not canon.
- Do not make the carrier canonical.
- A spinor is one possible candidate carrier/substrate, not the definition.
- Do not redefine outer/inner as chirality/flux.
- Do not redefine outer/inner as Hopf fiber/base traversal.
- Fiber/base loop geometry may be used only as a lower-level carrier or
  negative/control geometry if it helps test outer-vs-inner behavior.
- Chirality/flux may be a related readout or constraint, but it is not the
  outer/inner identity.

Hard boundary:
- Do NOT build named final axes.
- Do NOT build a final stage/engine function.
- Do NOT build prime probes.
- Do NOT claim the manifold is done.
- Do NOT write to system_v4/probes.

Language and substance boundary:
- Use plain function and branch names. Do not use project jargon as the
  load-bearing sim object.
- The propositions may split, merge, get renamed, or die. Do not canonize them.
- No toy interiors: shaped constants, labels, fixed thresholds, fake ranks, and
  decorative imports are not evidence.
- A SURVIVED branch needs a measured value computed from a real state/operator
  and a measured negative-control value.

High exploration is wanted, but inside the target. Give 3-5 branch attempts for
this one target. Each branch must name its assumptions, exact lego calls,
observable, negative control, and outcome ceiling.

Tool preference:
- This is the NONCLASSICAL process. The core construction substrate is
  PyTorch complex tensors/autograd plus nonclassical geometry/topology tools.
- NumPy belongs to the classical control lane (for example Carnot baselines).
  Do not use it for the core manifold construction here.
- SymPy belongs to the bridge / semiclassical lane (for example Szilard or
  exact symbolic sanity checks). Do not use it as the primary substrate here.
- Do not import NumPy or SymPy in this scout unless the branch is explicitly
  marked "bridge/control comparison", and never let that branch be the main
  survivor for this nonclassical target.
- Use Clifford / torch_ga for spinor, rotor, chirality, and geometric-product
  claims.
- Use TopoNetX / GUDHI / XGI / PyG / rustworkx for nested topology, incidence,
  persistence, higher-order relations, graph dynamics, and reduction DAGs.
- Use QuTiP only when density-matrix / open-system semantics are genuinely
  load-bearing.
- Use z3/cvc5 only for actual constraint checks.
- G-stack / G-tower may be needed, but it is not assumed. Treat it as a branch
  to test, with a clear observable for whether it is required.
- A SURVIVED branch must contain a real non-null measured value. If the value is
  None/null/missing, mark the branch NOT_YET_TESTED or KILLED.
- Negative controls must report an actual measured control value, not just the
  string "SURVIVED".
- Every unresolved item must preserve the literal token OPEN in main().

How to treat existing formal sims:
- Reference them for prior working patterns and tool examples.
- You do NOT have to import or obey them.
- They are useful examples, not the boundary of possible constructions.
- If a new PyTorch construction is cleaner than stitching old legos, use it.

Source excerpts:

===== COMPONENT_MAP.md =====
{_read(COMPONENT_MAP)}

===== current handbuilt assembly =====
{_read(HAND_BUILT)}

Return ONE python code block for a scout module under proposed_formal_sims.
It must expose:

classification = "classical_baseline"
admission_scope = "informal_scout_proposal"
promotion_allowed = False
claim_ceiling = "foundation repair scout for {target}; not canonical"

def branch_attempts() -> list[dict]:
    # 3-5 branches for this target only.
    ...

def run_branch(branch: dict) -> dict:
    # Execute or honestly mark OPEN/NOT_YET_TESTED.
    # Never return status="SURVIVED" with None/null evidence.
    ...

def main() -> dict:
    # Run all branches, return survivors and corpses.
    ...

Use SURVIVED / KILLED / OPEN / NOT_YET_TESTED.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=sorted(TARGETS), default="bridge_xi")
    args = ap.parse_args()

    RECEIPTS.mkdir(parents=True, exist_ok=True)
    PROPOSED.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = RECEIPTS / f"{args.target}_{ts}"
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt = build_prompt(args.target)
    (run_dir / "prompt.md").write_text(prompt)

    results = {}

    def call(pool, fn):
        t0 = time.time()
        try:
            raw = fn(prompt)
            code = mml.extract_code(raw)
            results[pool] = {"ok": bool(code), "elapsed_s": round(time.time() - t0, 3)}
            (run_dir / f"{pool}_raw.txt").write_text(raw[:12000])
            if code:
                out = PROPOSED / f"sim_proposed_foundation_{args.target}_{pool}_{ts}.py"
                out.write_text(code)
                results[pool]["proposal_path"] = str(out)
        except Exception as e:
            results[pool] = {"ok": False, "elapsed_s": round(time.time() - t0, 3),
                             "error": f"{type(e).__name__}: {str(e)[:300]}"}

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        futs = [ex.submit(call, "grok", mml.gen_grok),
                ex.submit(call, "gemini", mml.gen_gemini)]
        for fut in futs:
            fut.result(timeout=1800)

    summary = {
        "timestamp_utc": ts,
        "target": args.target,
        "target_description": TARGETS[args.target],
        "scope": "bounded_high_exploration_manifold_foundation_only",
        "promotion_allowed": False,
        "results": results,
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"Summary: {run_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
