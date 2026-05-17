#!/usr/bin/env python3
"""Side-quest: ask Grok 4.3 to actually build a runnable QIT engine, bypassing the lego stage.

This is NOT for canonical admission. It is to explore what Grok produces when given:
- The architecture (carrier, operators, terrain laws)
- The foundational axioms (a=a iff a~b, finitude, non-commutation)
- Permission to ignore the tool-stage hard gate
- All available tools to draw from
"""
import os
import sys
import time

from openai import OpenAI

prompt = """You are being asked to do something the project's normal doctrine forbids: bypass the lego-tier hard gate and just produce a runnable QIT engine in code. This is NOT for canonical admission to the research repo. This is a side quest to explore what a working engine could look like when built directly, before the tier-build catches up.

You have permission to:
- Skip the placement-lego stage
- Skip 120-pair distinguishability probes
- Skip Q3 (sheet × loop double-flip) closure
- Skip the calibration-before-engine gate
- Pick concrete operator parameterizations without enumerating graveyards
- Produce actual runnable Python, not specs

You must respect three load-bearing constraints:

1. **`a = a iff a ~ b`** — probe-relative identity. The engine's notion of "this state is this state" must be witnessed by an explicit probe family M and a quotient under M-indistinguishability. There is NO absolute reference frame for state identity. Two configurations that are M-indistinguishable for the engine's active probes ARE the same state from the engine's perspective. This must show up in code as a quotient operation, not as exact equality on density matrices.

2. **Finitude** — no continuous limits sneaking in via numerical integration of infinite series, infinite-dimensional Hilbert spaces, real numbers used as continuum surrogates, etc. The engine runs in finite-precision finite-dimensional discrete time. Where standard physics would use a continuous parameter, the engine uses a finite truncation with an explicit truncation-bound observable. The finiteness is load-bearing — observables include finiteness witnesses (e.g., truncation level, discrete time step, finite probe basis size).

3. **Non-commutation** — A∘B ≠ B∘A is the ratchet signature. The engine's evolution must depend on operator-composition order in a measurable way. There exist two operator sequences in the engine such that applying them in different orders produces M-distinguishable end states. This non-commutativity is the engine's mechanism, not a side effect.

ARCHITECTURE CONTEXT:

Carrier: ψ_L (Type 1) ∈ ℂ² and ψ_R (Type 2) ∈ ℂ², ‖ψ‖=1. Hopf coords ψ_s(φ,χ;η) = (e^(i(φ+χ))cos η, e^(i(φ-χ))sin η)ᵀ. Densities ρ_s = ψ_s ψ_s†. Hamiltonians H_L = +H_0, H_R = -H_0 with H_0 a Pauli combination.

4 base operators: Ti (σ_z dephasing CPTP), Te (σ_x dephasing CPTP), Fi (σ_x rotation unitary), Fe (σ_z rotation unitary).

8 terrain laws (Lindbladian generators): Se/Ne/Ni/Si on {L, R}. Example Type 1 Se: X_F^L(ρ_L) = Σ_k D[L_k]ρ_L - i ε [H_L, ρ_L].

16 placements: 4 terrain families × 2 sheets × 2 loops (γ_f inner density-stationary; γ_b outer density-traversing).

You're building a TWO-engine system: one Carnot-class cycle (4-stroke Lindblad with hot+cold baths and unitary work strokes) and one Szilard-class cycle (4-stage: measure + conditional feedback + verify + erase) — running simultaneously on opposite chirality sheets, coupled through whatever cross-sheet mechanism you choose. Treat them as a single QIT engine that has both thermo and info character.

AVAILABLE TOOLS — try to give each a load-bearing role, not decorative:

- pytorch (gradient/autodiff/GPU; could differentiate cycle observables w.r.t. parameters)
- pyg (graph neural net or graph structure on the manifold)
- qutip (Lindblad evolution, mesolve, Qobj)
- qiskit (quantum circuit representation if cycles get compiled to gates)
- clifford (geometric algebra; spinor algebra natively)
- gudhi (persistent homology; could read the cycle topology)
- toponetx (combinatorial complexes; for the discretized manifold)
- xgi (hypergraphs; for multi-engine coupling structure)
- rustworkx (fast graph ops; for adjacency of placements)
- z3 (SMT solver; for combinatorial admissibility under probe family)
- cvc5 (alternate SMT; cross-check)
- sympy (symbolic math; commutator algebra, symbolic operator construction)
- geomstats (geometry on manifolds; for S³ / SO(3) parallel transport)

Each tool getting at least one load-bearing function would demonstrate real multi-tool use. Decorative imports don't count.

DELIVERABLE — produce all of:

1. **One-paragraph design summary**: what does this engine compute, what does it output, what does "running" it look like, why is it truly nonclassical (and not just classical thermodynamics in quantum language).

2. **The three axiom-encodings**:
   - How probe-relative identity is implemented (the quotient operation, the probe family choice).
   - How finitude is encoded (the truncation parameter, the finiteness witness observable).
   - How non-commutation is exposed (which two operator sequences differ in order, what the M-distinguishable difference is).

3. **A tool-usage map**: one paragraph per tool naming the function it serves in the engine. Where a tool isn't load-bearing, say so honestly (don't pad).

4. **The actual Python code**, runnable. Multi-file is fine — write each file as its own block with the filename labeled. The code must:
   - Run end-to-end with one entry-point script
   - Produce output (numerical, structural, or both) that demonstrates the engine ran
   - Show the non-commutation witness (a pair of runs in different operator order whose readouts differ)
   - Show the probe-relative quotient in action (two configurations that are absolutely different but M-equivalent)
   - Show the finiteness witness (the truncation parameter and the observable that confirms finitude is respected)

5. **Expected output**: what the entry-point script prints/produces when run. Be specific about numbers, shapes, or qualitative patterns.

6. **What's truly nonclassical about it** (one paragraph): identify the specific places where the engine's behavior diverges from any classical analog. Be honest — if some parts are quantum-flavored classical, say so.

This is exploration. Be opinionated. Don't ask for clarification. Don't hedge with "depending on choices." Make the choices yourself and explain them briefly. Aim for code I can `python engine.py` and see something interesting happen.
"""

key = os.environ.get("XAI_API_KEY")
if not key:
    print("ERROR: XAI_API_KEY not set.")
    sys.exit(1)

client = OpenAI(api_key=key, base_url="https://api.x.ai/v1")

print("=== Grok 4.3 side-quest: build a runnable QIT engine (streaming) ===\n")
start = time.time()

stream = client.chat.completions.create(
    model="grok-4.3",
    messages=[{"role": "user", "content": prompt}],
    stream=True,
)

total_content = []
for chunk in stream:
    delta = chunk.choices[0].delta.content
    if delta:
        total_content.append(delta)
        print(delta, end="", flush=True)

elapsed = time.time() - start
content = "".join(total_content)
print(f"\n\n=== Done in {elapsed:.1f}s, {len(content)} chars output ===")

# Save the response for follow-up
output_path = "/Users/joshuaeisenhart/grok_engine_output.md"
with open(output_path, "w") as f:
    f.write(content)
print(f"Saved to: {output_path}")
