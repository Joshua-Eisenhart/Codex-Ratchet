#!/usr/bin/env python3
"""propose_manifold_assembly.py — Grok+Gemini propose the constraint-manifold
ASSEMBLY file per the binding COMPONENT_MAP.md.

Per user's standard:
  1. Stop treating primitive sims as manifold progress.
  2. Read manifold docs and existing formal sims (done).
  3. Build a component map (COMPONENT_MAP.md on disk).
  4. ONLY THEN let Grok/Gemini propose wiring. *** this script ***
  5. Codex audits against the component map, not against generic 'passes tests.'

Scope: informal-scout only. Proposals land in
  system_v5/grok_sim/loop_runner/proposed_formal_sims/
NO writes to system_v4/probes/. The 15 named legos there are READ-ONLY.

The contract is THE component map. Grok and Gemini get the full map text in
the prompt; they must produce ONE python module that:
  - references each required object → named lego by file path
  - implements ONLY the missing assembly code per item
  - marks Ax3, Q3 (Connes ↔ geodesic), Q4 (G_2), Bridge Ξ as OPEN
  - carries the nominalist schema (X, C, M, ~_M, survivors, graveyard, ceiling)
  - uses zero contaminated identifiers
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

PROPOSED = HERE / "proposed_formal_sims"
COMPONENT_MAP = HERE / "COMPONENT_MAP.md"


def build_prompt() -> str:
    if not COMPONENT_MAP.exists():
        raise SystemExit(f"missing component map: {COMPONENT_MAP}")
    map_text = COMPONENT_MAP.read_text()
    return f"""You are proposing ONE python module: `sim_proposed_constraint_manifold_assembly.py`.

This module is the ASSEMBLY of the geometric constraint manifold defined in
the binding COMPONENT_MAP below. The map names 10 required manifold objects.
For each, it names the EXISTING formal-sim lego(s) under
`system_v4/probes/` that already implement that object and the
specific assembly code that is MISSING.

## Your job

Implement ONLY the missing assembly code. Do NOT re-implement what the formal
corpus already has. Reference existing legos by their full path; treat them
as READ-ONLY evidence the proposal cites.

The output is ONE python module that exports:

```python
def build_constraint_manifold_assembly() -> dict:
    \"\"\"Returns the assembled constraint manifold dict per the component
    map, with every required object either:
      (a) referenced to an existing lego by file path + brief verification
          that the lego produces what's named in the map, OR
      (b) constructed via the missing-assembly cross-call harness named
          in the map.
    \"\"\"
```

Return shape:
```python
{{
    "carrier": {{"path": "system_v4/probes/sim_hopf_fibration_embedding_classical.py",
                 "object": "S^3 normalized spinor space",
                 "status": "SURVIVED"|"OPEN", "evidence": "..."}},
    "hopf_projection": {{...}},
    "u1_connection": {{...}},
    "curvature_and_chern": {{"c1": <computed value>, ...}},
    "holonomy": {{"loop_omega": ..., "hol_value": ..., ...}},
    "reduction_chain": {{"steps": [...], "z3_unsat_on_reversed": bool, ...}},
    "weyl_spinor_sections": {{"chirality_check_L": ..., "chirality_check_R": ..., ...}},
    "connes_distance": {{"d_value": ..., "geodesic_ranking_agrees": "OPEN", ...}},
    "loop_split": {{"gamma_f_density_change": ..., "gamma_b_density_change": ...,
                   "ax3_status": "OPEN"}},
    "entropy_three_layer": {{"runtime": {{}}, "torus_seat": {{}}, "bipartite_ax0": {{}},
                             "bridge_xi_status": "OPEN"}},
    "is_constraint_satisfied": callable,   # composes the leg's individual checks
    "manifold_open_items": [...],          # honest list of what's OPEN
    "claim_ceiling": str,
}}
```

## Binding constraints

- Nominalist object schema present in the module docstring: X, C, M, ~_M,
  survivors, graveyard, claim ceiling.
- Status vocabulary: SURVIVED / KILLED / OPEN / NOT_YET_TESTED. NOT pass/fail.
- Ax3 is UNRESOLVED per the doc — the proposal MUST mark it OPEN.
- Q3 (Connes ↔ geodesic), Q4 (G_2), Bridge Ξ, Axis-0 cut all stay OPEN.
- Banned identifiers: axis, Ax0..Ax6, engine, engine_stage, Engine A/B,
  Type 1/2, gstack, terrain, Ti/Te/Fi/Fe as function names, prime_resonance,
  hexagram, Carnot, Szilard, IGT, Jung.
- NO re-encoding of carrier, projection, connection, curvature, Chern form,
  reduction chain, Connes distance, spinor lift, or holonomy. Those are
  READ-ONLY legos. You may import them at the path level (read the named
  file's exported callables) but do not paste their math back into this
  proposal.
- Tests required:
    `run_assembly_check() -> dict` returns SURVIVED if every required-object
        entry has a populated `path` or `evidence` field.
    `run_open_items_honest() -> dict` returns SURVIVED if Ax3, Q3, Q4,
        Bridge Ξ, Axis-0 cut all appear in `manifold_open_items`.
    `run_no_reimplementation_check() -> dict` returns SURVIVED if the
        proposal's source does not contain a from-scratch Hopf, gtower,
        Weyl-as-section, Chern, holonomy, or Connes definition. Use
        textual heuristic on the proposal's own source.
- `main() -> dict` runs all three; aggregates an `all_survived` flag.

## Cost / model usage

Per cumulative wall map (24 reviewer audits), the recurring failure modes
in prior rounds were: tests-designed-to-pass, decorative tools, synthetic
returns, hash distinguishers, shallow negatives. Each of those is rejected
at the reviewer gate. Do not commit them again.

## COMPONENT MAP (binding contract)

```markdown
{map_text}
```

Return ONE python code block with the complete proposed assembly module.
"""


def main():
    if not COMPONENT_MAP.exists():
        print(f"missing {COMPONENT_MAP}"); sys.exit(1)
    prompt = build_prompt()
    print(f"Prompt length: {len(prompt)} chars (component map injected)")
    print(f"Firing Grok 4.3 + Gemini 3.1-pro in parallel...\n")

    results = {"grok": None, "gemini": None}
    def call_grok():
        t0 = time.time()
        try:
            results["grok"] = mml.gen_grok(prompt)
            print(f"  [grok] returned in {time.time()-t0:.1f}s "
                  f"({len(results['grok'])} chars)")
        except Exception as e:
            print(f"  [grok] failed: {type(e).__name__}: {str(e)[:120]}")
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

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    PROPOSED.mkdir(parents=True, exist_ok=True)
    paths = {"grok": None, "gemini": None}
    for pool in ("grok", "gemini"):
        if results[pool]:
            code = mml.extract_code(results[pool])
            if code:
                p = PROPOSED / f"sim_proposed_constraint_manifold_assembly_{pool}_{ts}.py"
                p.write_text(code)
                paths[pool] = p
                print(f"Saved: {p.name}")

    if paths["grok"] and paths["gemini"]:
        print(f"\nCodex auditing AGAINST COMPONENT_MAP.md (not generic pass/fail)...")
        decision_file = Path("/tmp/codex_manifold_assembly_decision.txt")
        if decision_file.exists(): decision_file.unlink()
        instr = (
            f"Two proposals for `sim_proposed_constraint_manifold_assembly.py` — "
            f"the assembly of the geometric constraint manifold per the binding "
            f"contract at {COMPONENT_MAP}.\n\n"
            f"AUDIT AGAINST THE COMPONENT MAP, NOT GENERIC 'PASSES TESTS'. "
            f"For each of the 10 required objects in the map, check:\n"
            f"  (1) Is the named existing lego at system_v4/probes/<path> "
            f"      referenced by file path in the proposal?\n"
            f"  (2) Is the missing-assembly code (only) implemented per the map?\n"
            f"  (3) Are Ax3, Q3 (Connes-geodesic), Q4 (G_2), Bridge Xi, "
            f"      Axis-0 cut all listed as OPEN?\n"
            f"  (4) Does the proposal RE-ENCODE any of the read-only legos "
            f"      (Hopf, gtower, Weyl-as-section, Chern, holonomy, Connes)? "
            f"      That is a REJECTION criterion.\n"
            f"  (5) Banned identifiers present? Reject if so.\n\n"
            f"Grok:    {paths['grok']}\nGemini:  {paths['gemini']}\n\n"
            f"Write decision to {decision_file}:\n"
            f"  Line 1: GROK | GEMINI | REJECT_BOTH\n"
            f"  Lines 2+: per-object map compliance, OPEN-item honesty, "
            f"            any re-encoding violations, any banned identifiers.\n"
        )
        t0 = time.time()
        subprocess.run(
            ["codex", "exec",
             "-c", 'model_reasoning_effort="low"',
             "-C", str(HERE.parent),
             "-s", "workspace-write",
             "--skip-git-repo-check", instr],
            capture_output=True, text=True, timeout=900,
        )
        print(f"  Codex done in {time.time()-t0:.1f}s")
        if decision_file.exists():
            print(f"\n=== Codex decision ===\n{decision_file.read_text()}")


if __name__ == "__main__":
    main()
