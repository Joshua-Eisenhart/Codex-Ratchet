#!/usr/bin/env python3
"""propose_axis_lego.py — Grok+Gemini propose standalone math-primitive legos.

NOTE: file name is legacy. The content has been decontaminated. We do NOT propose
"axis" legos. We propose literal-math primitive legos. Each is a candidate formal
sim under `system_v4/probes/` after reviewer promotion.

Usage: propose_axis_lego.py <primitive_key>
       e.g. channel_order, dephasing_dfs, unitary_rotation_purity,
            landauer_bound, path_ordered_phase, loop_readout_independence,
            density_trajectory_rank
"""
import concurrent.futures, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import multi_model_loop as mml

CANDIDATES = HERE.parent / "candidates"
PROPOSED = HERE / "proposed_formal_sims"

# Math-primitive legos. Each is a standalone proposal target.
#
# Retargeted 2026-05-13: the formal corpus under system_v4/probes/ has 4194 .py
# files including 266 hopf, 285 weyl, 174 clifford, 118 gtower, 77 spectral_triple,
# 74 holonomy, 25 chern, 9 dephasing, 8 berry, 7 landauer. The proposer's job is
# to fill GAPS, not duplicate. Saturated themes (loop_readout, path_ordered_phase,
# unitary_rotation_purity, landauer_bound, density_trajectory_rank) are intentionally
# absent below. The remaining keys target thin areas: explicit Kraus channels on
# the 4-qubit carrier, DFS basis identification, probe-equivalence quotient, and
# the two exploration-doc-§12 primitives (A and C) that have no formal counterpart.
PRIMITIVE_SPECS = {
    "channel_order": {
        "slug": "sim_channel_order_trace_distance_micro",
        "name": "Channel-order trace-distance witness",
        "math": (
            "Two CPTP channels A, B on a 4-qubit state with at least one input "
            "ρ where trace_distance(A(B(ρ)), B(A(ρ))) > 0.03. A and B given by "
            "explicit Kraus operators. No persona names."
        ),
        "positive_test": "td(A(B(ρ)), B(A(ρ))) > 0.03 on a non-trivial input",
        "negative_test": "td(A(A(ρ)), A(A(ρ))) == 0 (same channel twice)",
        "boundary_test": "td → 0 as one channel → identity",
    },
    "dephasing_dfs": {
        "slug": "sim_dephasing_fixed_subspace_basis_micro",
        "name": "Dephasing-channel fixed-subspace basis",
        "math": (
            "For dephasing channel D in basis b ∈ {z, x} at strength γ ∈ (0,1], "
            "construct the fixed subspace (DFS) and exhibit a state ρ on it with "
            "||D(ρ) − ρ||_1 < 1e-6. Show purity preserved on DFS, decreased off it."
        ),
        "positive_test": "DFS state invariance error < 1e-6",
        "negative_test": "off-DFS state purity strictly decreases under D",
        "boundary_test": "DFS for z and DFS for x are different subspaces",
    },
    "petz_recovery_quantum": {
        "slug": "sim_petz_recovery_quantum_carrier_micro",
        "name": "Petz dual recovery on 4-qubit carrier (quantum, not classical)",
        "math": (
            "Apply a dephasing channel ε in basis b ∈ {z,x} at strength γ to a "
            "non-trivial 4-qubit ρ_in. Construct Petz dual recovery "
            "ℛ_σ(ρ_out) = σ^{1/2} ε†(σ_out^{-1/2} ρ_out σ_out^{-1/2}) σ^{1/2} "
            "with σ a chosen reference state. Verify recovery strictly reduces "
            "trace distance from input. Existing formal sims (petz_recovery_classical, "
            "pure_lego_petz_recovery) are classical / pure-math; this fills the "
            "quantum-channel gap on the 4-qubit carrier."
        ),
        "positive_test": "td(ℛ(ε(ρ_in)), ρ_in) < td(ε(ρ_in), ρ_in)",
        "negative_test": "identity channel: ℛ ∘ ε = identity → td = 0 within 1e-9",
        "boundary_test": "as γ → 1 (full dephasing), recovery quality degrades but recovered ρ stays PSD",
    },
    "kraus_completeness_witness": {
        "slug": "sim_kraus_completeness_witness_micro",
        "name": "Kraus completeness witness with CPTP scan",
        "math": (
            "Construct an explicit Kraus set {K_i} for a non-trivial 4-qubit "
            "channel. Report ||∑ K_i† K_i − I||_F across (a) the constructed set, "
            "(b) a deliberately-incomplete set (one K_i removed), (c) a Choi-"
            "isomorphism roundtrip ρ → Choi(ε) → ε → ρ_out and reverse. Existing "
            "kraus sims are classical or single-purpose; this fills the "
            "completeness-witness + Choi-roundtrip gap on the 4-qubit carrier."
        ),
        "positive_test": "complete set: ||∑ K†K − I||_F < 1e-9; Choi roundtrip error < 1e-9",
        "negative_test": "incomplete set: ||∑ K†K − I||_F > 0.05",
        "boundary_test": "single-Kraus unitary channel: completeness exact, output purity preserved",
    },
    "nested_constraint_filtration": {
        "slug": "sim_nested_constraint_operator_set_filtration_micro",
        "name": "Nested-constraint operator-set filtration (ratchet toy)",
        "math": (
            "Construct a chain of operator sets O_0 ⊇ O_1 ⊇ ... ⊇ O_n on the 4-qubit "
            "carrier where each O_{k+1} is the subset of O_k surviving an explicit "
            "added constraint C_{k+1} (e.g. Hermitian → traceless → norm-bounded → "
            "commutes-with-given-projector). Report |O_k| at each step. Negative "
            "controls: shuffle constraint order; replace one constraint with its "
            "negation. Source: exploration §12.A."
        ),
        "positive_test": "|O_{k+1}| ≤ |O_k| for every k AND at least one step strictly reduces",
        "negative_test": "shuffled constraint order produces a non-monotone size sequence on at least one input set",
        "boundary_test": "removing the last constraint preserves the prior chain unchanged",
    },
    "flux_mechanism_bakeoff": {
        "slug": "sim_flux_mechanism_observable_bakeoff_micro",
        "name": "Flux/chirality mechanism observable bakeoff",
        "math": (
            "Five candidate flux/chirality realizations applied independently to a "
            "shared starting ρ: (1) Hamiltonian sign flip H → −H, (2) jump-operator "
            "swap L ↔ L†, (3) connection orientation flip A → −A in u1_holonomy "
            "integration, (4) Clifford grade-reversal on the operator basis, "
            "(5) source/sink swap σ_+ ↔ σ_− in ladder kernels. For each candidate, "
            "report a single scalar observable (e.g. trace distance from input "
            "after a fixed cycle). Source: exploration §3.8 + §12.C."
        ),
        "positive_test": "all 5 produce nonzero observables; pairwise observable differences > 0.03 OR at least one merges-with-another is explicitly reported as KILLED",
        "negative_test": "five no-op controls (no flip) all return observable ≈ 0",
        "boundary_test": "two flips composed are not always the identity (composition table is reported, not assumed)",
    },
    "probe_equivalence_class": {
        "slug": "sim_probe_expectation_equivalence_class_micro",
        "name": "Probe-expectation equivalence class witness",
        "math": (
            "Two density matrices ρ_a ≠ ρ_b (element-wise distinct) with identical "
            "tuples (Tr(M_i ρ_a))_i = (Tr(M_i ρ_b))_i over a fixed probe family M. "
            "Operational form of a ~_M b."
        ),
        "positive_test": "max |Tr(M_i ρ_a) − Tr(M_i ρ_b)| < 1e-9 AND ρ_a != ρ_b",
        "negative_test": "expanding M with a new informationally-rich operator breaks the equivalence",
        "boundary_test": "for M = full operator basis, no two distinct states share the class",
    },
}


def build_prompt(key: str) -> str:
    spec = PRIMITIVE_SPECS[key]
    return f"""Propose a STANDALONE math-primitive lego for a 4-qubit-carrier simulator.
The proposal is informal-scout output — it will be reviewer-audited before any
promotion to system_v4/probes/. Use literal math names only.

## Primitive under test

{spec["name"]}

## Math the lego must verify

{spec["math"]}

## Tests required

- Positive: {spec["positive_test"]}
- Negative: {spec["negative_test"]}
- Boundary: {spec["boundary_test"]}

## Module shape

ONE python module:
- module docstring naming the math object verified
- TOOL_MANIFEST + TOOL_INTEGRATION_DEPTH dicts. Use qutip + numpy + at least one
  of (clifford, sympy, gudhi, toponetx, cvc5, z3) load-bearingly (not decorative)
- `run_positive() -> dict` — returns metrics, asserts positive test
- `run_negative() -> dict`
- `run_boundary() -> dict`
- `main() -> dict` aggregating all three into a structured receipt

## Constraints

- Qobjs use `dims=[[2,2,2,2],[2,2,2,2]]`.
- Status vocabulary: SURVIVED / KILLED / OPEN / NOT_YET_TESTED — not PASS/FAIL.
- No hash-style distinctness, no classical-primality multipliers, no synthetic
  matrices ignoring inputs, no closed-form returns where integration is implied.
- If a test cannot be honestly satisfied, RAISE — do not fake.

## Banned identifiers (auto-reject if present)

`axis`, `Ax0..Ax6`, `engine`, `engine_stage`, `Engine A/B`, `Type 1/2`,
`gstack`, `g_stack`, `terrain`, `Ti/Te/Fi/Fe` as function or operator-variable
names, `prime_resonance`, `prime_score`, `hexagram`, `Carnot`, `Szilard`, `IGT`,
`Jung`, `MBTI` letter pairs as cognitive-function labels.

Return ONE python code block.
"""


def main():
    if len(sys.argv) < 2:
        print(f"Usage: propose_axis_lego.py <primitive_key>")
        print(f"Available keys: {sorted(PRIMITIVE_SPECS)}")
        sys.exit(1)
    key = sys.argv[1]
    if key not in PRIMITIVE_SPECS:
        print(f"Unknown primitive '{key}'. Available: {sorted(PRIMITIVE_SPECS)}")
        sys.exit(1)

    spec = PRIMITIVE_SPECS[key]
    print(f"\nProposing primitive: {spec['name']}\n")
    prompt = build_prompt(key)
    print(f"Prompt: {len(prompt)} chars")
    print(f"Calling Grok + Gemini in parallel...\n")

    results = {"grok": None, "gemini": None}
    def cg():
        t0 = time.time()
        try:
            results["grok"] = mml.gen_grok(prompt)
            print(f"  [grok] returned in {time.time()-t0:.1f}s")
        except Exception as e: print(f"  [grok] failed: {e}")
    def cm():
        t0 = time.time()
        try:
            results["gemini"] = mml.gen_gemini(prompt)
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
            grok_path = PROPOSED / f"{spec['slug']}_grok_{ts}.py"
            grok_path.write_text(c); print(f"Saved: {grok_path.name}")
    if results["gemini"]:
        c = mml.extract_code(results["gemini"])
        if c:
            gemini_path = PROPOSED / f"{spec['slug']}_gemini_{ts}.py"
            gemini_path.write_text(c); print(f"Saved: {gemini_path.name}")

    if grok_path and gemini_path:
        print(f"\nCodex (GPT-5.5 LOW) judging {spec['slug']} proposals...")
        decision_file = Path(f"/tmp/codex_{spec['slug']}_decision.txt")
        if decision_file.exists(): decision_file.unlink()
        instr = (
            f"Two informal-scout proposals for {spec['slug']}. "
            f"The lego must verify: {spec['math']}. "
            f"Tests required: positive ({spec['positive_test']}), "
            f"negative ({spec['negative_test']}), "
            f"boundary ({spec['boundary_test']}).\n\n"
            f"Auto-reject any proposal containing banned identifiers: axis, Ax0..Ax6, engine, "
            f"engine_stage, Engine A/B, Type 1/2, gstack, terrain, Ti/Te/Fi/Fe as function "
            f"names, prime_resonance, hexagram, Carnot, Szilard, IGT, Jung. Reject if it cheats "
            f"(synthetic returns, hash distinctness, decorative tools, hardcoded test results, "
            f"closed-form where integration claimed).\n\n"
            f"Grok:    {grok_path}\nGemini:  {gemini_path}\n\n"
            f"Write decision to {decision_file}:\n"
            f"  Line 1: GROK | GEMINI | REJECT_BOTH\n"
            f"  Lines 2+: justification, plus the measured positive-test value.\n"
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
