#!/usr/bin/env python3
"""Run 5 parallel deep audits with Grok 4.3, each on a distinct architectural artifact."""
import os
import sys
import concurrent.futures
import time

from openai import OpenAI

HANDOFF_PATH = "/Users/joshuaeisenhart/Desktop/Codex Ratchet/.claude/worktrees/flamboyant-jackson-4d7f5f/.tmp/qit_engine_architecture_thread_handoff.md"

with open(HANDOFF_PATH) as f:
    handoff = f.read()

shared_context = f"""Background — the work being audited belongs to a constraint-admissibility framework grounded in nominalist principles. Identity is probe-relative; primitive `~` = indistinguishability under active probe family M; claims need (M, admissibility, quotient) triple. Carrier = S³ = ψ_L/ψ_R Weyl spinors over Hopf-fibered base. 4 base operators built from Paulis (Ti σ_z dephasing, Te σ_x dephasing, Fi σ_x rotation, Fe σ_z rotation). 8 terrain laws (Se/Ne/Ni/Si × {{L,R}}). 16 placements = 4 terrain families × 2 sheets × 2 loops (inner γ_f density-stationary, outer γ_b density-traversing).

7 named DoF axes (Ax0 feedback type, Ax1 bath coupling, Ax2 expansion/compression, Ax3 chirality/Z₂, Ax4 inductive/deductive, Ax5 T-vs-F-first, Ax6 UP/DOWN) plus open Ax7? (inner/outer). Ax3 explicitly unresolved per ENGINE_64_SCHEDULE_ATLAS.md. Q3 = unforced (sheet × loop) double-flip z3 probe.

Layer discipline: pure-math sims (executable) ≠ rosetta (read-only labels) ≠ domain (Jungian/thermodynamic/cognitive). Carnot and Szilard are calibration-case rosetta labels for now, not earned engine identities. Cycle-naming by operation sequence; "Engine A/B" rejected as nicknames. Type 1/Type 2 reserved for Weyl chirality sheets ONLY.

Graveyard rule: every candidate survives only with surrounding deaths. Status ladder: exists < runs < passes local rerun < canonical. Tool-stage hard gate: tool sims → tool-integration → lego rows → couplings → emergence → bridges.

Goal of the program: a single big sim made of tiered lego sims, where everything couples together at the limit. Axis independence at the lego layer is FORENSIC (so coupling at higher tiers is readable), not absolute. Mass-coupling is the design point of higher tiers, not a worry."""

audits = [
    {
        "name": "A — Tier-build architecture",
        "prompt": f"""{shared_context}

Audit this tier structure for the lego-to-big-sim construction:

T0 — Tools: single tool calls (pytorch.matmul, z3.solve, qutip.mesolve). All tools independent.
T1 — Tool integration: cross-tool sims (pytorch + z3, qutip + clifford). Tools coupled, axes still isolated.
T2 — Lego sims: single placement primitives (one (X_τ^s, Y_ℓ) tuple, isolated evolution). Each placement in isolation; 5 DoFs per slot held distinct.
T3 — Pairwise coupling: two placements coupled (same sheet, two terrains; same terrain, two loops; etc.). One axis coupled at a time.
T4 — Multi-coupling: 3-5 placements simultaneous; small sub-cycles. Multiple axes coupled; lego identities still readable.
T5 — Cycle sims: full Carnot cycle, full Szilard cycle (each in isolation, both directions). Cycle identity bound; per-cycle axes free.
T6 — Dual/quad stack: 4-cycle stack (2 Carnot ± + 2 Szilard ±), cross-engine coupling. Cycle pairs coupled; sheet/loop/ordering still per-slot.
T7 — Mass coupling: all engines + multiple manifold layers; cross-layer coupling. Most axes coupled simultaneously.
T∞ — Single big sim: everything coupled through one constraint substrate. All independence lifted; emergence is the readout.

The student already holds the doctrine A∘B ≠ B∘A — coupling order is non-commutative and that non-commutativity IS the ratchet signature.

Audit:
1. Are there missing tiers between named ones?
2. Are any tier transitions ambiguous about which axis is coupled?
3. Does the tier structure have dimensionality bombs (where compute cost makes a tier impossible without approximation)?
4. Is the T∞ limit well-defined or path-dependent (different coupling orders → different big sims)?
5. Where do tiers smuggle hidden coupling that the labels don't admit?
6. Is the distinction between "lego sims" (T2) and "tool integration" (T1) load-bearing or smoke?
7. Where would Codex run aground if it tried to skip a tier?

Be a rigorous teacher. Push back hard. No placation.""",
    },
    {
        "name": "B — 16 placement → information-operation assignments",
        "prompt": f"""{shared_context}

The student claims each of the 16 placements is a distinct information-processing operation in isolation. Audit each claim:

| Generator | Loop | Claimed isolated operation | Math signature |
|---|---|---|---|
| Se (D[L_k] + weak H) | inner γ_f | autonomous error correction — relaxation to attractor at fixed configuration | D[L_k]ρ, density invariant along ∂_φ |
| Se | outer γ_b | filtered transport — relaxation while density traverses | D[L_k]ρ along base-lift; off-diagonal phase rotates |
| Ne (unitary -i[H,ρ] + weak D) | inner | local phase rotation at fixed configuration | -i[H,ρ]; coherent gate |
| Ne | outer | holonomic / geometric-phase gate — accumulates U(1) connection along base-lift | -i[H,ρ] on density-traversing path |
| Ni (D[σ_-] pumping + weak H) | inner | amplitude damping to Bloch fixed point | γ D[σ_-]ρ |
| Ni | outer | polarized transport stroke — directional pumping along path | pumping while traversing |
| Si (projective, [K, P_j]=0) | inner | non-demolition readout at fixed configuration | Σ_j P_j ρ P_j form |
| Si | outer | spatial-scan / position-resolved measurement | projective along path |

(Each row × 2 sheets = 16 total.)

Audit each claim:
1. Is the operation label correct given the math signature, or has the label been imported from rosetta?
2. Are any two claimed operations actually equivalent under some probe family (collapsing the 16 count)?
3. Is "autonomous error correction" right for Se/inner, or is it overclaiming (it's actually just thermalization to a Lindblad fixed point — error correction has additional structural requirements)?
4. Is "holonomic gate" right for Ne/outer, or is the U(1) holonomy claim premature without specifying the connection form?
5. Which of the 8 (×2) operations are honest characterizations vs which are aspirational labels?
6. What would the 120-pair distinguishability probe actually test, and would it close this label set?

Push back hard. Don't validate labels just because they sound right.""",
    },
    {
        "name": "C — Carnot + Szilard sim specs",
        "prompt": f"""{shared_context}

Audit these calibration sim specs the student laid out:

CARNOT-CLASS (4-stroke schedule on one sheet, calibration target):
- Stroke 1: D[L_hot]ρ with L_hot = √γ_h σ_- + damping ratio e^(-βħω/2) for hot T → thermalize to T_hot
- Stroke 2: -i[H_a, ρ] quasi-static H_a → H_b → adiabatic expansion (work out)
- Stroke 3: D[L_cold]ρ → thermalize to T_cold
- Stroke 4: -i[H_b, ρ] quasi-static H_b → H_a → adiabatic compression (work in)
Observables: Q_hot = ∫_1 Tr(H ∂_t ρ) dt; Q_cold = ∫_3 Tr(H ∂_t ρ) dt; W = ∫_{{2,4}} Tr(∂_t H · ρ) dt; η = W/Q_hot
Pass: W > 0 AND η ≤ 1 − T_c/T_h (classical Carnot bound)
Graveyards: (1) same-bath (replace L_cold with L_hot → W=0), (2) swapped (D[L_h]→D[L_c]→U_a→U_b, broken alternation), (3) anti-Carnot (D[L_c] first → W<0 refrigerator), (4) trivial (all strokes Se/inner → no work).

SZILARD-CLASS (4-stage schedule with classical measurement record):
- Stage 1: Si projective. ρ → Σ_j P_j ρ P_j, record outcome j with p_j = Tr(P_j ρ) → acquire 1 bit
- Stage 2: Ne conditional on j. ρ → U_j ρ U_j† where U_j extracts work → feedback
- Stage 3: Si verification basis (separate from stage 1) → confirm post-feedback state
- Stage 4: Ni erasure. D[σ_-]ρ at temperature T → bath erasure
Observables: I = -Σ_j p_j ln p_j; W = ⟨H⟩_pre - ⟨H⟩_post stage 2 (branch-averaged); Q_erase = ∫_4 Tr(H ∂_t ρ) dt
Pass: W ≤ k_B T · I (Landauer) AND Q_erase ≥ k_B T · I
Graveyards: (1) no-measurement (skip stage 1, unconditional Ne → W=0), (2) no-feedback (stage 2 = identity → W=0), (3) no-erasure (skip stage 4 → 2nd-law violation across cycles), (4) random-feedback (U_j independent of measurement outcome → W=0).

Audit:
1. Are the operator forms for L_hot and L_cold actually constructive? Is the damping-ratio temperature encoding the right one, or is there a better Lindblad form for thermal baths?
2. Is the quasi-static assumption on stages 2 and 4 (Carnot) admissible in this Lindbladian setup, or does it require additional structural justification?
3. Is the Szilard branch-averaging in stage 2 properly defined — is there a mixed-state representation that handles the measurement record without classical branches?
4. Are the 4 Carnot graveyards sufficient, or are there structurally adjacent variants missing (e.g., 2-stroke instead of 4, or different work-extraction observable)?
5. Are the 4 Szilard graveyards sufficient — what about wrong-measurement-basis as a graveyard (P_j not aligned with H_eigenbasis)?
6. Is the Landauer bound the right pass criterion for Szilard, or is there a tighter classical bound that should pass first as a sanity check?
7. What's missing from the 10-field sim spec contract for either of these?

Be a rigorous physics teacher. Catch operator-form bugs and missing graveyards.""",
    },
    {
        "name": "D — 4-cycle stack architecture",
        "prompt": f"""{shared_context}

Audit the candidate 4-cycle stack architecture for T6 (dual/quad stack):

The stack runs 4 simultaneous cycles on the shared manifold:
- Slot 1: Carnot-class, forward direction. Heat engine. Extracts work, rejects heat (cooling-direction).
- Slot 2: Carnot-class, reversed direction. Refrigerator/heat pump. Consumes work, pumps heat cold→hot (heating-direction).
- Slot 3: Szilard-class, forward direction. Info-to-work converter. Acquires info, erases, entropy increasing.
- Slot 4: Szilard-class, reversed direction. Work-to-info / correlation creator. Injects work, writes information, entropy decreasing.

Slots 1+2 form the closed Carnot pump (thermo). Slots 3+4 form the closed Szilard pump (info). Both pumps run simultaneously, coupled through the shared manifold via some cross-coupling mechanism (TBD: shared bath operator vs shared Hamiltonian term vs bundle connection).

Per-slot DoFs (independent at this tier): chirality sheet (Type 1 / Type 2), stage ordering (inductive / deductive), loop (inner / outer). 4 slots × 3 binary DoFs = 64 configurations of the stack before cross-coupling choice.

Cross-engine observables claimed to exist only under joint operation:
- Intra-pair pump observables: net heat flow within Carnot pair, net info flow within Szilard pair
- Inter-pair coupling: Carnot work output feeding Szilard reversed (information funded by work) and vice versa
- 4-way mutual information across the 4 measurement records
- Joint holonomy across synchronized 4-cycle traversal
- Joint entropy production beyond sum of single-cycle entropies

Audit:
1. Is the "closed-loop pump" framing right? Does Slot 1 + Slot 2 actually close, or does it require an external work reservoir for the refrigerator stroke?
2. Is "Szilard reversed" constructively defined? What is the dual-map / Petz-recovery form of reversed measurement, and does it produce a well-defined Lindbladian?
3. Are the 4 cross-engine observables actually independent, or do some decompose into combinations of others?
4. Is the "shared manifold coupling" specification meaningful, or is it a placeholder that hides a choice?
5. Are there admissible alternative stack configurations that the student should also catalog as graveyards (e.g., 4 Carnots in different directions; 2 Carnots + 2 stabilizer cycles; 2 Szilards + 2 holonomic cycles)?
6. Does the Z₂ × Z₂ reframing of Q3 (sheet × loop = independent Z₂s) affect the stack's per-slot DoF count?
7. Where in this architecture is the student smuggling a commitment that hasn't been earned (e.g., "Carnot + Szilard" as the canonical pair when other pairs work equally)?

Adversarial peer review. Push back on every move that isn't load-bearing.""",
    },
    {
        "name": "E — Codex execution doctrine compliance",
        "prompt": f"""{shared_context}

The student's Codex agent recently completed a receipt-bound work pass and reported:

Completed:
- Repaired XGI hypergraph receipt
- Demoted boundary_flux_to_pauli_admissibility to classical_baseline (was over-claimed)
- Fenced sim_hopf_spinor_density_inner_outer_operator_placement_baseline as classical baseline (not engine/placement admission)
- Added sim_z3_tuple_component_readout_pair_separation: pure-math z3 16-tuple / 120-pair readout separation probe with coordinate-drop graveyards
- Refreshed tool_function_receipt_matrix.json and TOOL_FUNCTION_RECEIPT_MATRIX.md
- Ran verification: 4 sim runs, validate_receipt.py, tool_function_receipt_matrix.py, helper-process-audit-strict, runner-preflight, parallel-runner-dry MINUTES=1
- All validators passed. Dry runner exits green despite existing controller lock.
- 10 commits pushed
- Claude Sonnet scout receipt at /tmp/codex_claude_bridge/...74a2a2feb4b8.receipt.json was superseded by local work

Next planned: sheet-loop double-flip probe with sheet flip + loop flip as independent Z₂ operations, full readout distinguishes identity/single/double flips, graveyards collapse when either coordinate is hidden.

The student remains correct that 4-cycle stack mechanics are blocked behind calibration + placement-lego closure.

Audit Codex's doctrine compliance:
1. Is "fenced as classical baseline" the right move for the old sim_hopf_spinor_density_inner_outer_operator_placement_baseline, or should it be deleted/renamed to remove "engine" from the filename?
2. Are "coordinate-drop graveyards" the right graveyards for a readout-separation probe? What's missing?
3. The claim that the probe is "120-pair readout separation" but in graveyards it tests coordinate hides — is this label-level testing or actual physical-evolution-level testing? Which would force the 120-pair distinguishability claim?
4. Is the dangling Claude scout receipt a real concern (untriaged signal) or noise (correctly superseded)?
5. Does the existing-controller-lock + dry-runner-exits-green count as a real green or is there a hidden state mismatch?
6. The next planned sheet-loop double-flip probe — is its design (with coordinate-hide graveyards) strong enough to close Q3, or will it also classify as pre-admission?
7. Where is Codex drifting from the doctrine in ways the student hasn't caught?

Be a strict reviewer. Catch what the student missed.""",
    },
]


def run_audit(audit):
    """Run one Grok 4.3 audit. Returns dict with name, response, elapsed."""
    key = os.environ["XAI_API_KEY"]
    client = OpenAI(api_key=key, base_url="https://api.x.ai/v1")
    start = time.time()
    resp = client.chat.completions.create(
        model="grok-4.3",
        messages=[{"role": "user", "content": audit["prompt"]}],
    )
    elapsed = time.time() - start
    return {
        "name": audit["name"],
        "response": resp.choices[0].message.content,
        "elapsed": elapsed,
        "tokens_in": resp.usage.prompt_tokens,
        "tokens_out": resp.usage.completion_tokens,
    }


def main():
    key = os.environ.get("XAI_API_KEY")
    if not key:
        print("ERROR: XAI_API_KEY not set.")
        sys.exit(1)

    print(f"Spawning {len(audits)} parallel Grok 4.3 audits...\n")
    start = time.time()

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(audits)) as executor:
        future_to_audit = {executor.submit(run_audit, a): a for a in audits}
        for future in concurrent.futures.as_completed(future_to_audit):
            result = future.result()
            results.append(result)
            print(f"[done in {result['elapsed']:.1f}s, {result['tokens_in']} in / {result['tokens_out']} out] {result['name']}")

    print(f"\nAll {len(results)} audits done in {time.time() - start:.1f}s wall-clock.\n")
    print("=" * 100)

    # Sort results back into original audit order for readable output
    audit_order = {a["name"]: i for i, a in enumerate(audits)}
    results.sort(key=lambda r: audit_order[r["name"]])

    for r in results:
        print(f"\n\n{'=' * 100}")
        print(f"AUDIT {r['name']}")
        print(f"{'=' * 100}\n")
        print(r["response"])


if __name__ == "__main__":
    main()
