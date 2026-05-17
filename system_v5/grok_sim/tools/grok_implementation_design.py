#!/usr/bin/env python3
"""Three parallel Grok 4.3 calls asking how to actually make the QIT engines run.

Each call targets a different implementation layer:
  1. Operator math + integrator (corrected Lindblad forms; concrete physics)
  2. Architecture: 4-cycle stack closure + Szilard-reversed dual-map
  3. Implementation: tool stack, sim runner, end-to-end code skeleton
"""
import os
import sys
import concurrent.futures
import time

from openai import OpenAI

shared_context = """A constraint-admissibility framework with these earned pieces:

CARRIER:
- S³ = {ψ ∈ ℂ²: ‖ψ‖=1}, Weyl spinors ψ_L (Type 1) and ψ_R (Type 2)
- Hopf coords: ψ_s(φ, χ; η) = (e^(i(φ+χ)) cos η, e^(i(φ-χ)) sin η)ᵀ
- Hamiltonians: H_L = +H_0, H_R = -H_0 where H_0 = n_x σ_x + n_y σ_y + n_z σ_z

4 BASE OPERATORS (Pauli-built):
- Ti = σ_z dephasing CPTP, Lindbladian (κ₁/2)(σ_z ρ σ_z - ρ)
- Te = σ_x dephasing CPTP, Lindbladian (κ₂/2)(σ_x ρ σ_x - ρ)
- Fi = σ_x rotation unitary, -i[(ω₃/2)σ_x, ρ]
- Fe = σ_z rotation unitary, -i[(ω₄/2)σ_z, ρ]

8 TERRAIN LAWS (Lindbladian generators):
- Type 1 (left): Se (Funnel) X_F^L, Ne (Vortex) X_V^L, Ni (Pit) X_P^L, Si (Hill) X_H^L
- Type 2 (right): Se (Cannon), Ne (Spiral), Ni (Source), Si (Citadel)
- Example: X_F^L(ρ_L) = Σ_k D[L_k^(F,L)](ρ_L) - i ε_{F,L} [H_L, ρ_L]
- Dissipator: D[L](ρ) = LρL† - ½(L†L ρ + ρ L†L)

16 PLACEMENTS = 4 terrain families × 2 sheets × 2 loops (γ_f inner density-stationary, γ_b outer density-traversing)

OPEN AXES: Ax3 (chirality Z₂ — unresolved); Ax7? (inner/outer maybe-DoF); Q3 (sheet × loop double-flip probe pending).

PRIOR AUDIT (Grok 4.3) FOUND THESE BUGS/GAPS:

1. The proposed Carnot thermal bath operator was MALFORMED: `L_hot = √γ_h σ_- + e^(-βħω/2)` is invalid (adding scalar to operator). Correct form needs TWO Lindblad operators per bath:
   L_↓ = √[γ(n_th + 1)] σ_-     (emission)
   L_↑ = √[γ n_th] σ_+           (absorption)
   n_th = 1/(e^(βħω) − 1)

2. Szilard-reversed is not constructively defined. Forward is measurement + conditional feedback + erasure. Reversed needs explicit Petz-recovery dual-map: CPTP, satisfies recovery relation with forward measurement channel, yields well-defined Lindbladian in continuous-time limit. Currently a placeholder.

3. The proposed 4-cycle stack (2 Carnot ± + 2 Szilard ±) does NOT close. The reverse Carnot consumes work. On a closed manifold without external work reservoir or work-storage DoF, the reverse stroke has nowhere to draw work from. Same for Szilard reversed.

4. Of 8 isolated placement operations, only 3 are honest (Ne/inner = coherent gate, Ni/inner = amplitude damping, Si/inner = non-demolition readout). The 5 outer-loop or Se/inner claims (autonomous error correction, filtered transport, holonomic gate, polarized transport stroke, spatial scan) are aspirational and need additional structure (filtration map, connection form, position observable transport).

5. T∞ is path-dependent under the non-commutativity doctrine A∘B ≠ B∘A — coupling-order choice gives different fixed points.

GOAL TIER STRUCTURE (the "single big sim" is a tier-build limit):
T0 tools → T1 tool-integration → T2 lego sims (single placement) → T3 pairwise coupling → T4 multi-coupling → T4.5 cycle-constraint closure → T5 single cycle (Carnot or Szilard isolated) → T6 dual/quad stack → T7 mass coupling → T∞ family of big sims indexed by coupling order

CURRENT STATE: Tools mostly available (pytorch, qutip, qiskit, clifford, gudhi, toponetx, xgi, rustworkx, z3, cvc5, sympy, geomstats); tool-integration sims being run; lego rows partly written; coupling not started; 4-cycle stack blocked behind calibration + lego closure.

LAYER DISCIPLINE: Sim code stays pure-math (no Se/Ni/Carnot/Szilard/Engine/Type-engine vocabulary in executable). Rosetta labels are read-only mappings applied to lego survivors. Cycle filenames use operation sequence (e.g., carnot_cycle_lindblad_hot_cold_unitary_bound_probe).

You are now asked to PROPOSE THE ACTUAL IMPLEMENTATION."""

calls = [
    {
        "name": "1 — Operator math + integrator design",
        "prompt": f"""{shared_context}

Design the actual operator math and integrator setup for running the Carnot-class calibration cycle on Type 1 (ψ_L) — the simplest first cycle.

Be concrete. I want:

1. **The full corrected Lindblad equation** for each of the 4 strokes, written out explicitly:
   - Stroke 1 (hot thermalization): which 2 Lindblad operators, what γ_h, n_th values, what H_L
   - Stroke 2 (adiabatic expansion): what time-dependent H_L(t), what ramp profile, are dissipators switched off
   - Stroke 3 (cold thermalization): mirror of stroke 1
   - Stroke 4 (adiabatic compression): mirror of stroke 2

2. **The Hamiltonian schedule**: pick concrete H_L parameter values. What |n⃗| at hot end vs cold end. What ramp time. What dissipator rates.

3. **The integrator choice**: qutip.mesolve? piecewise analytical? Custom RK4 on Bloch vector? Justify why for this problem.

4. **Numerical tolerances**: integrator atol/rtol, quasi-static condition |dH/dt|/Δ_gap < ε, what ε.

5. **Observable computation**: how exactly to compute Q_hot = ∫_stroke_1 Tr(H ∂_t ρ) dt, W = ∫_strokes_2,4 Tr(∂_t H · ρ) dt, η = W/Q_hot. Including sign conventions and integration scheme.

6. **Initial state**: what is ρ(0)? Hot thermal state? Maximally mixed? Pure ground state? Justify.

7. **Pass condition as code-level predicate**: write the actual boolean test that returns True/False on the result.

8. **Graveyard runs**: list the 7 graveyard companion configurations (4 original + 3 added by the prior audit) and what each graveyard's predicted outcome is.

Give this as a structured engineering spec, not prose. Concrete numbers, explicit equations, runnable schedule. Pretend you're writing this for a graduate student to implement tomorrow.""",
    },
    {
        "name": "2 — Architecture: 4-cycle stack closure + Szilard-reversed dual-map",
        "prompt": f"""{shared_context}

The 4-cycle stack architecture (2 Carnot ± + 2 Szilard ±) has two unresolved gaps that block implementation:

GAP A: The closed-loop pump framing requires a work reservoir or work-storage DoF, but the manifold + 16 placements + 8 terrain laws don't supply one. Without it, the reverse Carnot (consumes work) and reverse Szilard (consumes work to create correlations) have nowhere to draw from.

GAP B: Szilard-reversed is not constructively defined. Forward Szilard = measurement + conditional feedback + erasure. Reversed needs an explicit dual-map / Petz-recovery superoperator that is CPTP, satisfies the recovery relation with the forward measurement channel, and yields a well-defined Lindbladian in continuous-time limit.

Design concrete resolutions for both gaps. I want:

1. **Work reservoir options**, evaluated:
   (a) Add an explicit "work qubit" or "work register" as a new DoF on the carrier. Show what its math is (Hilbert space extension, coupling Hamiltonian, how work flows in/out).
   (b) Use the bundle's connection structure (Hopf U(1) phase) as the work record — argue why or why not it can carry work.
   (c) Abandon closed-loop framing: run cycles as open systems with external work flow not represented inside the sim. Argue what's lost.
   Pick the option that minimizes architectural smuggling and explain why.

2. **Szilard-reversed dual-map**, constructively:
   (a) Forward measurement channel: ρ → Σ_j P_j ρ P_j with outcomes j and probabilities p_j.
   (b) The Petz dual-map: P^σ_ε(X) = σ^(1/2) ε†(σ^(-1/2) X σ^(-1/2)) σ^(1/2) for reference state σ. Specify σ for our case.
   (c) Write the reversed feedback U_j† and reversed erasure (D[σ_+] pumping from ground? or some recovery channel?).
   (d) Verify the reversed schedule is CPTP at each stage and produces W < 0 when run on a state that would give W > 0 in forward.

3. **Concrete operator forms** for all 4 cycles in the stack:
   - Slot 1 Carnot forward: Lindblad + Hamiltonian schedule (you can reference call 1's design)
   - Slot 2 Carnot reversed: how the work reservoir interfaces
   - Slot 3 Szilard forward: measurement Kraus, conditional Ne, erasure
   - Slot 4 Szilard reversed: dual-map version of slot 3

4. **Cross-coupling mechanism**: of the three candidates (shared bath operator across Carnot pair; shared Hamiltonian term across Carnot-Szilard pairs; bundle connection as universal coupler), which is the right starting choice? Specify its math.

5. **Z₂ × Z₂ vs Z₂ question (Q3)**: until Q3 closes, the per-slot DoF count is unknown. Design the cross-coupling so it works under BOTH the Z₂ and Z₂ × Z₂ readings of Q3. If you can't, name which reading the cross-coupling silently commits to.

Be concrete. Math, not prose. Pretend you're answering a thesis defense question on whether this architecture can be built.""",
    },
    {
        "name": "3 — Implementation: tool stack + sim runner + code skeleton",
        "prompt": f"""{shared_context}

Design the actual implementation stack for running the QIT engine calibration sims, end-to-end.

The available tools: pytorch, qutip, qiskit, clifford (geometric algebra), gudhi (topology), toponetx, xgi (hypergraph), rustworkx, z3, cvc5, sympy, geomstats, numpy/scipy (baselines only).

Produce:

1. **Tool selection per task**:
   - Density operator evolution under Lindbladian: qutip or pytorch (custom)?
   - Carrier state representation on S³: which library; what coordinates (Hopf, Bloch, complex 2-vector)?
   - Hamiltonian/operator construction: qutip Qobj, sympy symbolic, or numpy arrays?
   - Quasi-static H(t) ramp: piecewise + qutip.mesolve, or custom integrator?
   - z3 admissibility predicates (the pass/fail check): how are observable values bridged into z3 SMT?
   - Graveyard companion runs: how is the parameter sweep orchestrated (parallel? sequential?)
   - 16-placement enumeration and probe-pair distinguishability: which library?

2. **Code skeleton — give actual Python**. Write the module structure:
   - `sim_runner.py`: orchestrates one sim run, returns receipt JSON
   - `carrier_state.py`: ψ_s representation + Bloch projection
   - `terrain_law.py`: the 8 X_τ^s generators as callable Lindblad-equation builders
   - `loop_field.py`: γ_f and γ_b vector fields on the torus
   - `cycle_schedule.py`: 4-stroke / 4-stage cycle assembly from terrain laws + loop fields
   - `observables.py`: Q, W, η, I, Q_erase, mutual info computation
   - `graveyard.py`: graveyard companion enumeration
   - `admissibility_predicate.py`: z3 wrapping of pass/fail
   - `receipt_writer.py`: 10-field receipt JSON producer

   Give 5-10 line skeleton per module with key class/function signatures. No need for full implementation — just the structural skeleton a graduate student could fill in.

3. **The receipt-JSON schema** — give the actual 10-field JSON template:
```
{{
  "operation_sequence": ...
  "carrier_topology": ...
  "observable": ...
  "pass_fail_predicate": ...
  "graveyard_companions": ...
  "baseline_variants": ...
  "alternative_formulations": ...
  "tool_function_needs": ...
  "lego_coupling_target": ...
  "claim_ceiling": ...
}}
```

4. **Concrete runner orchestration**: how does Codex run a wave of these sims? Parallel? Serial with checkpoints? Where do receipts land?  What's the contract for a sim to claim "passes local rerun" status?

5. **One specific first sim to run** — name it (pure-math filename), say what tier it sits at (T2 lego, T5 single-cycle, etc.), what its receipt should contain, what observable would distinguish pass from fail, and what graveyard companions surround it.

Concrete, runnable, opinionated. No vague "use the right tool" guidance — pick the tool and justify briefly.""",
    },
]


def run_call(call):
    """Run one Grok 4.3 call."""
    key = os.environ["XAI_API_KEY"]
    client = OpenAI(api_key=key, base_url="https://api.x.ai/v1")
    start = time.time()
    resp = client.chat.completions.create(
        model="grok-4.3",
        messages=[{"role": "user", "content": call["prompt"]}],
    )
    elapsed = time.time() - start
    return {
        "name": call["name"],
        "response": resp.choices[0].message.content,
        "elapsed": elapsed,
        "tokens_in": resp.usage.prompt_tokens,
        "tokens_out": resp.usage.completion_tokens,
        "cost_ticks": resp.usage.__dict__.get("cost_in_usd_ticks", "n/a"),
    }


def main():
    key = os.environ.get("XAI_API_KEY")
    if not key:
        print("ERROR: XAI_API_KEY not set.")
        sys.exit(1)

    print(f"Spawning {len(calls)} parallel Grok 4.3 implementation-design calls...\n")
    start = time.time()

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(calls)) as executor:
        future_to_call = {executor.submit(run_call, c): c for c in calls}
        for future in concurrent.futures.as_completed(future_to_call):
            result = future.result()
            results.append(result)
            ticks = result['cost_ticks']
            cost_str = f"${ticks/1e9:.4f}" if isinstance(ticks, int) else "n/a"
            print(f"[done in {result['elapsed']:.1f}s, {result['tokens_in']} in / {result['tokens_out']} out, {cost_str}] {result['name']}")

    print(f"\nAll {len(results)} calls done in {time.time() - start:.1f}s wall-clock.\n")
    print("=" * 100)

    call_order = {c["name"]: i for i, c in enumerate(calls)}
    results.sort(key=lambda r: call_order[r["name"]])

    for r in results:
        print(f"\n\n{'=' * 100}")
        print(f"CALL {r['name']}")
        print(f"{'=' * 100}\n")
        print(r["response"])


if __name__ == "__main__":
    main()
