# C1 Witness Redesign Packet
Date: 2026-04-04
Status: working redesign guidance — not a closure claim
Grounded in: `c1_entanglement_object_search_results.json`, `claude-c1-missing-negatives-strict__review.md`

---

## Why MI failed as a sufficient C1 witness

Two independent failures, each complete:

### Failure 1 — MI is not quantum-specific

The fake-coupling control presents a classically correlated separable state
`rho_cc = 0.5|00><00| + 0.5|11><11|` (diagonal, no off-diagonal coherence) to the same
joint 4×4 operator at the same polarity and strength as the real quantum run.

Result across all 16 stages:
- Ti, Fe, Te: `mi_fake = 1.0` (perfect classical MI — matches or exceeds `mi_joint`)
- Fi: `mi_fake ≈ 0.927` (still >> 0)
- `fake_coupling_killed = False` for all 16 stages (0/16 kill rate)

Root cause: MI measures total correlations — both classical and quantum. The classical
initial state already carries MI = 1.0 (measuring one qubit perfectly predicts the other).
The joint operator transforms but does not destroy that classical correlation budget.
MI cannot distinguish whether the initial correlation was quantum or classical.

### Failure 2 — MI is not pairing-specific

The mispair control presents `rho_L` from the current engine type ⊗ `rho_R` from the
chirality-inverted type (Type1 ↔ Type2), then applies the same joint operator.

Result across all 16 stages:
- `mi_mispair ≈ mi_joint` within 0–30% relative deviation for all 16 stages
- Notable: LOSE/Te mi_joint=0.402, mi_mispair=0.529 — mispair exceeds correct pairing
- `mispair_killed = False` for all 16 stages (0/16 kill rate)

Root cause: MI is insensitive to which carrier chirality type contributed rho_L vs rho_R.
The operator processes the joint 4×4 state without penalizing structural mispair.

### What MI still witnesses correctly (preserved, not discarded)

The LOCC ablation is real and should be retained:
- LOCC (local application, then kron): `mi_locc ≈ 0` across all 16 stages (≤ 1e-15)
- Joint minus LOCC gap: 0.15–0.40 bits, consistent across all operators and chirality types
- This confirms the joint 4×4 operators are genuinely non-local — they produce correlations
  that do not arise from local-only operation.

This is a real positive fact. The problem is that MI alone cannot distinguish whether
the non-local correlation is quantum-specific or structural.

---

## Next candidate discriminators

Ranked by: discriminatory precision × implementation cost × current tool availability

---

### Candidate 1 — Concurrence (Wootters, 1998)

**What it would discriminate:** Quantum entanglement vs classical correlation.
For any 2-qubit 4×4 density matrix, concurrence C(rho) = 0 if and only if rho is separable.
This is exact for the 2-qubit case (which is exactly our system).

The fake-coupling state `rho_cc = 0.5|00><00| + 0.5|11><11|` is separable with C = 0.
If the joint 4×4 operators preserve separability of diagonal classical inputs (as dephasing
and mixing channels tend to do), then `C(op_fn_joint(rho_cc)) = 0` while
`C(op_fn_joint(rho_AB_init)) > 0`. This would kill the fake-coupling control.

**Known risk**: If the joint operators ARE fully entangling (map separable inputs to
entangled outputs regardless of initial state), concurrence would also be non-zero for
the fake-coupling control. This is the open empirical question that only running the
probe can resolve. The operator descriptions (ZZ dephasing, YY dephasing, XX rotation,
XZ rotation as 4×4 channels) are consistent with both outcomes depending on their
precise 4×4 form.

**What repo/local tools:** `numpy` only — Wootters formula uses spin-flip matrix
R = rho * (σ_y ⊗ σ_y) * rho* * (σ_y ⊗ σ_y) and eigenvalues of √R.

**Required negatives:**
- Fake-coupling control (should give C = 0 if operators preserve separability)
- Product state / LOCC state (should give C = 0 by construction)
- Mispair control (pairing-specific question — separate from quantum-specific question)

**Classification:** Numerical-only. No graph coupling needed for this step.

**Honest status:** This is the first discriminator to try. It may resolve Failure 1
completely. It does not address Failure 2 (pairing-specificity) unless concurrence
also differs between correct and inverted chirality pairings (not guaranteed).

---

### Candidate 2 — Negativity (partial transpose test)

**What it would discriminate:** Same quantum-specificity question as Candidate 1, but
via a different route. For 2-qubit systems, negativity > 0 ↔ entangled (PPT criterion
is exact for 2⊗2 systems).

Negativity N(rho) = (||rho^{T_B}||_1 - 1) / 2 where rho^{T_B} is the partial transpose.
The separable state rho_cc has non-negative eigenvalues under partial transpose (N = 0).

**Why prefer over concurrence in some cases:** Negativity is more direct (no spin-flip
construction), and generalizes beyond 2-qubit systems if the carrier ladder later expands.

**What repo/local tools:** `numpy` only — partial transpose is a reshape + transpose
operation; negativity is sum of negative eigenvalues.

**Required negatives:** Same as Candidate 1.

**Classification:** Numerical-only. Natural companion to Candidate 1.

**Honest status:** Equivalent in discriminatory power to Candidate 1 for 2⊗2 systems.
Recommend implementing both in the same handoff to cross-validate.

---

### Candidate 3 — Chirality-conditioned entanglement gap (pairing-specific)

**What it would discriminate:** Failure 2 — whether the joint operator's entanglement
production is sensitive to correct vs inverted chirality pairing.

Definition: `Δ_C = C(rho_joint_correct) - C(rho_joint_mispair)` normalized.
If correct pairing produces systematically higher concurrence than inverted pairing,
this gap is a structural carrier discriminator.

**This is a separate question from Failure 1.** Even after concurrence kills the fake-coupling
control, it might not distinguish correct from inverted chirality pairing. Candidate 3
measures that residual gap.

**What repo/local tools:** `numpy` only — builds directly on Candidate 1.

**Required negatives:**
- Scrambled chirality assignment (non-canonical Type1/Type2 pair — not just inverted,
  but random assignment)
- Same-type pairing (Type1⊗Type1, Type2⊗Type2) as a degenerate control

**Classification:** Numerical-only, but structurally more coupled to the engine geometry
than Candidates 1 and 2.

**Honest status:** Depends on Candidate 1 as a prerequisite. Cannot be meaningfully
interpreted if concurrence itself fails Failure 1.

---

### Candidate 4 — Coherent information I(A>B) (quantum channel quality)

**What it would discriminate:** One-way quantum capacity of the joint operator channel.
I(A>B) = S(B) - S(AB) can be negative for separable states and positive only when
quantum information is preserved. This goes beyond entanglement witnessing into
channel-theoretic territory.

**What repo/local tools:** `numpy` only — requires von Neumann entropy of rho_B and rho_AB.
`get_mutual_information` already computes these components; coherent info reuses them.

**Required negatives:** Same fake-coupling and mispair controls.

**Classification:** Numerical-only, but conceptually heavier. Makes a claim about
the quantum channel, not just the output state.

**Honest status:** This is the right long-run direction if concurrence succeeds.
Not the first implementation target — adds conceptual overhead without clearing the
immediate Failure 1 question first.

---

### Candidate 5 — Graph-coupled concurrence artifact (future)

**What it would discriminate:** Once Candidates 1–2 establish quantum-specific witnessing,
attaching concurrence to the graph writeback layer (which now works at 8 hits, 50%
admissibility) would elevate C1 from numerical-only to graph-coupled.

**What repo/local tools:** `PyG` writeback (confirmed working), `numpy` for concurrence.

**Classification:** Graph-coupled. Not numerical-only.

**Honest status:** This is a Tier-upgrade move, not the immediate fix. Cannot be reached
without Candidates 1–2 first resolving Failure 1.

---

## Recommendation: next single bounded implementation handoff

**Target:** Implement concurrence and negativity as companion witnesses inside
`sim_c1_entanglement_object_search.py`, running the same fake-coupling and mispair
controls already in place.

**Scope:**
- Add `get_concurrence(rho: np.ndarray) -> float` using Wootters formula
- Add `get_negativity(rho: np.ndarray) -> float` via partial transpose
- Compute both on `rho_AB_joint`, `rho_AB_fake`, `rho_AB_mispair` per stage
- Add new fields to per-stage JSON: `concurrence_joint`, `concurrence_fake`,
  `concurrence_mispair`, `negativity_joint`, `negativity_fake`, `negativity_mispair`
- Add kill booleans: `fake_coupling_concurrence_killed`, `mispair_concurrence_killed`
- Do not remove existing MI fields or LOCC ablation
- Do not redesign the probe structure

**Why bounded:** `numpy` only, no new packages, no structural redesign, additive to
existing JSON contract, retains all existing negative controls.

**What this handoff resolves (if concurrence kills fake-coupling control):**
- C1 gets a quantum-specific positive witness
- C1 `keep_but_open` status upgrades to `admitted` for the quantum-specificity dimension

**What remains open regardless:**
- Pairing-specificity (Failure 2) — needs Candidate 3 as a follow-up
- Proof surface — no z3 guard yet
- Graph artifact — deferred to Candidate 5 path

**What this handoff reveals (if concurrence also fails fake-coupling control):**
- The joint operators ARE fully entangling from separable inputs
- The discriminator problem is deeper — coherent information or geometric conditioning needed
- Next handoff would need to characterize operator entangling power explicitly before
  a new witness strategy can be proposed

---

## Current C1 promotion status

`keep_but_open` — correct classification. The LOCC ablation is real. The gap is real.
The failure of MI is a scientific finding, not a code bug. The next bounded step is
empirically decidable within the current tool stack.
