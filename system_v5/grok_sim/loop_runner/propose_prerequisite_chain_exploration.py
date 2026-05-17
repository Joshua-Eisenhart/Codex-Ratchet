#!/usr/bin/env python3
"""propose_prerequisite_chain_exploration.py.

Grok/Gemini scout the upstream dependency chain before downstream axes/engines.

This is deliberately NOT a generator for axis math or engine_stage code. Its job
is to ask: what must be true first for the manifold to host axes and engines?

Outputs are proposal notes under:
  loop_runner/receipts/prerequisite_chain_exploration/<timestamp>/

No writes to system_v4/probes/. No promotion to canonical evidence.
"""

import concurrent.futures
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import sys

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import multi_model_loop as mml

RECEIPTS = HERE / "receipts" / "prerequisite_chain_exploration"
COMPONENT_MAP = HERE / "COMPONENT_MAP.md"
STATUS = HERE / "proposed_formal_sims" / "MANIFOLD_ASSEMBLY_STATUS.md"
HAND_BUILT = HERE / "proposed_formal_sims" / "sim_proposed_constraint_manifold_assembly_handbuilt.py"


def _read(path: Path, limit: int = 30000) -> str:
    try:
        text = path.read_text()
    except Exception as e:
        return f"[UNREADABLE {path}: {type(e).__name__}: {e}]"
    return text[:limit]


def build_prompt() -> str:
    return f"""You are auditing an exploratory QIT/geometry sidequest.

Do NOT write axis code. Do NOT write engine_stage code. Do NOT claim the
constraint manifold is done.

Task: map the prerequisite chain that must be explored BEFORE axes or engines
are built on this manifold scout.

Source material follows.

===== COMPONENT_MAP.md =====
{_read(COMPONENT_MAP)}

===== MANIFOLD_ASSEMBLY_STATUS.md =====
{_read(STATUS)}

===== handbuilt assembly source excerpt =====
{_read(HAND_BUILT, 22000)}

Return one markdown report with this exact shape:

# Prerequisite Chain Scout

## Claim Ceiling
Say clearly that this is side-quest scouting, not canonical evidence.

## Dependency DAG
List the build order as a DAG from geometry legos to manifold verifier to axes
to engine stages to entropy/prime probes. Include stop conditions.

## OPEN Foundation Items
For each item below, give:
- current status from the files
- why downstream axes/engines depend on it
- smallest useful scout sim or proof-check
- graveyard/negative controls
- what evidence would make it ready enough for downstream work

Items:
1. real `is_constraint_satisfied(state)` gate, not top-level status composition
2. Bridge Xi from geometry/history to rho_AB
3. Ax3 reading: chirality/flux vs inner/fiber and outer/base traversal
4. Connes distance versus geodesic recovery on S2
5. G2 exceptional case policy
6. three-layer entropy bridge / Axis-0 cut state

## Downstream Exploration That Is Allowed Early
Name any safe whole-process exploration that can run before closure without
pretending the foundation is done. It must be corpse-producing or interface
testing, not evidence promotion.

## Downstream Exploration That Is Premature
Name what must be blocked for now, including axes_math_exploration and
engine_stage proposals if they require the unsettled manifold.

## Concrete Next 5 Runs
Give five small, bounded scout runs in order. Each must target exactly one OPEN
foundation item and have a pass/kill/open outcome.

Use status vocabulary SURVIVED / KILLED / OPEN / NOT_YET_TESTED.
"""


def main():
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = RECEIPTS / ts
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt = build_prompt()
    (run_dir / "prompt.md").write_text(prompt)

    results = {}

    def call(pool: str, fn):
        t0 = time.time()
        try:
            out = fn(prompt)
            results[pool] = {
                "ok": True,
                "elapsed_s": round(time.time() - t0, 3),
                "chars": len(out),
                "output": out,
            }
            (run_dir / f"{pool}_report.md").write_text(out)
            print(f"{pool}: returned in {results[pool]['elapsed_s']}s")
        except Exception as e:
            results[pool] = {
                "ok": False,
                "elapsed_s": round(time.time() - t0, 3),
                "error": f"{type(e).__name__}: {str(e)[:300]}",
            }
            print(f"{pool}: failed: {results[pool]['error']}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        futures = [
            ex.submit(call, "grok", mml.gen_grok),
            ex.submit(call, "gemini", mml.gen_gemini),
        ]
        for f in futures:
            f.result(timeout=1800)

    summary = {
        "timestamp_utc": ts,
        "scope": "sidequest_prerequisite_chain_scout",
        "promotion_allowed": False,
        "component_map": str(COMPONENT_MAP),
        "status_file": str(STATUS),
        "reports": {
            pool: {k: v for k, v in data.items() if k != "output"}
            for pool, data in results.items()
        },
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"Summary: {run_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
