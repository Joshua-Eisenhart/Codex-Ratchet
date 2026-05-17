#!/usr/bin/env python3
"""Run Grok 4.3 as a teacher auditing the QIT engine architecture work."""
import os
import sys

from openai import OpenAI

HANDOFF_PATH = "/Users/joshuaeisenhart/Desktop/Codex Ratchet/.claude/worktrees/flamboyant-jackson-4d7f5f/.tmp/qit_engine_architecture_thread_handoff.md"

with open(HANDOFF_PATH) as f:
    handoff = f.read()

thread_corrections = """
Recent thread corrections applied AFTER the handoff doc was written (the doc has not been patched yet):

1. **Type 1 / Type 2 reserved for Weyl chirality sheets only** (ψ_L, ψ_R). Never used for engine identity. The handoff's §8 currently says "Type 1 / Type 2 = chiral mirrors with opposite Hamiltonian signs and opposite loop assignments" — this is correct for chirality but the line is easy to misread as engine labeling.

2. **Engine identity is independent from direction.** Any engine schedule can run forward or reversed:
   - Carnot forward = heat engine (extracts work, cooling-direction)
   - Carnot reversed = refrigerator / heat pump (consumes work, heating-direction)
   - Szilard forward = info-to-work converter (entropy increasing)
   - Szilard reversed = work-to-info / correlation creator (entropy decreasing)

3. **The dual-stack architecture is 4 cycles, not 2 engines.** The candidate stack runs 2 Carnot (±) + 2 Szilard (±) simultaneously, forming two closed-loop pumps (one thermo, one info), coupled through the shared manifold. Cross-engine observables emerge only under joint operation.

4. **Cycles are labeled by their operation sequence in pure-math vocabulary, NOT by Engine A/B nicknames.** Following the broader naming discipline that labels are definitions, not nicknames. Sim filenames like `carnot_cycle_lindblad_hot_cold_unitary_bound_probe` are correct; "Engine A" is not.

5. **The 16-placement count is structural, not operationally closed.** The 120-pair pairwise distinguishability sweep has not been run. Until it does, "16 distinct information-processing classes" is provisional.

6. **Q3 (sheet × loop double-flip z3 probe) is the unforced bottleneck.** This probe determines whether Ax3 (chirality) absorbs the inner/outer choice or whether inner/outer is a separate DoF (Ax7?). Every coupling sim that touches chirality inherits this ambiguity until Q3 lands.

7. **Cycle identity, direction, chirality sheet, stage ordering (inductive/deductive), and loop (inner/outer) are five INDEPENDENT DoFs per engine slot.** Do not collapse any pair.

8. **Codex is currently running a long-duration campaign** based on a goal prompt that encodes the doctrine: pure-math legos with no rosetta jargon, 10-field sim spec contract, graveyard discipline, Carnot+Szilard calibration BEFORE QIT engine mechanics, 4-cycle stack held back until calibration + placement-lego closure.
"""

teacher_prompt = f"""You are a rigorous teacher auditing a graduate student's research architecture. The student is working on a constraint-admissibility framework grounded in nominalist principles (identity is probe-relative, primitive `~` is indistinguishability under active probe family M, claims need M + admissibility + quotient triple).

Your job:
1. Identify what's structurally sound (be specific — name the pieces that hold up).
2. Identify what's collapsed, confused, or insufficiently distinguished (the failure modes the student has shown a tendency toward).
3. Identify what the student is overclaiming (where they treat hypothesis-level convergence as earned).
4. Identify what the student is underclaiming (where the architecture is doing more than they realize).
5. Name the single most important next concrete step.

Be unflinching where pushback is earned. Don't placate. Don't smooth over divergent surviving readings. Where the architecture preserves real divergence (multiple admissible interpretations), name what would force resolution. Where the architecture has covertly committed to one reading, surface the commitment.

The student has been corrected several times in-thread for: collapsing inductive/deductive onto inner/outer; mapping inner to "unconscious"; importing rosetta jargon into pure-math sim code; treating cross-scale Rosetta convergence as proven when it's hypothesis; conflating engine identity with direction; using Type 1/2 as engine labels rather than reserving them for Weyl chirality.

Below is the architecture handoff document the student wrote (note: it has not yet been patched to reflect the thread corrections — see the corrections list after it).

==================== ARCHITECTURE HANDOFF DOC ====================

{handoff}

==================== POST-HANDOFF THREAD CORRECTIONS ====================

{thread_corrections}

==================== END CONTEXT ====================

Audit the work. Be a teacher — rigorous, encouraging where the student has earned it, honest about where the work is shallow or smoothed-over. End with the single most important next concrete step.
"""

key = os.environ.get("XAI_API_KEY")
if not key:
    print("ERROR: XAI_API_KEY not set.")
    sys.exit(1)

client = OpenAI(api_key=key, base_url="https://api.x.ai/v1")

print("=== Grok 4.3 teacher-audit on QIT architecture (streaming) ===\n")

for chunk in client.chat.completions.create(
    model="grok-4.3",
    messages=[{"role": "user", "content": teacher_prompt}],
    stream=True,
):
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="", flush=True)
print()
