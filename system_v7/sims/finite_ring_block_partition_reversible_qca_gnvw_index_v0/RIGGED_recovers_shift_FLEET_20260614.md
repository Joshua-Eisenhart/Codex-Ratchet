# RIGGED — the chirality index recovers a hand-inserted shift (do not cite)

**Full-fleet (13/13, codex2 unanimous all 4 efforts, + source trace): RIGGED_RECOVERS_SHIFT.** The `audit_verdict.md` claim "the index is computed from operator-support structure, not by echoing an inserted shift parameter" is **FALSE for the shift rules** and is hereby withdrawn. scratch_diagnostic, promotion_allowed=false (ceiling correct — no overclaim leaked to a registry).

## The defect
For the only rules that carry chirality (`left_shift`/`right_shift`), `image_for()` directly returns `generator(cell-1)`/`generator(cell+1)` — it **hardcodes the displacement** and **never conjugates through the checkerboard QCA `U = U_odd∘U_even`.** So the ±1 "GNVW index" is the rank of a translation put in by hand, not a quantity that emerges from the block-QCA structure. The real claim — *a ring-checkerboard block-QCA can carry chirality* — is **asserted, not demonstrated.**

## Genuine part (held, not collapsed)
The **non-shift** rules (`CZ` finite-depth circuit, `CNOT` brickwork) DO conjugate through real block gates via `circuit_image()` and honestly return index 0 (support genuinely spreads, e.g. `A3_X → {2,3,4}`, ranks balance across the cut). So the conjugation machinery is real **for the trivial-index rules**; only the chirality-bearing shift rules are hand-baked.

## Other findings
- The L/R-sign-opposite and identity=0 "controls" are a deterministic consequence of the hardcoded shift direction — effectively hardcoded, not measured separations.
- The z3/cvc5 SMT is a **literal tautology**: it pins the already-computed signs (`left==-1`, `right==+1`) then asks if two opposite literals can be same-sign (trivially UNSAT). Decorative, not load-bearing.
- **Reversibility tests a DIFFERENT operator than the index:** the reversibility check is on a true mod-8 cyclic permutation on 2^8 states; the index is computed on a lifted 9-site OPEN line (positions 0..8, no wraparound, the lifted odd bond (7,8) replacing the ring bond (7,0)). The proven-reversible object is not the object under test.

## The meta-lesson (why this matters most)
Both the builder AND the fresh-context verify agent declared the GNVW genuine — the verify agent even ran an independent numpy GF(2) re-derivation + a shift+2/+3 falsifier and was confident. **Both were fooled** (the verify agent checked the trivial fact "a shift has index ±1", not the real claim "the block-QCA produces chirality"). Only the **multi-model full-fleet source-trace** caught the rig. A single auditor — even an independent fresh-context Claude one — is NOT the validity barrier. The per-sim full-fleet cross-audit is (completeness-contract box viii, multi-model — this is the proof of why).

## The fix (to make it genuine)
Build an actual **chiral block-QCA** (e.g. a Margolus/partitioned shift assembled from `U_odd∘U_even` block gates) and conjugate the cut-cell Pauli generators **through that block circuit** (the way `circuit_image()` already does for CZ/CNOT), so the ±1 **emerges from support flow** rather than being written down. Then re-run the full-fleet audit. Until then, the ring-checkerboard QCA does NOT have a demonstrated chirality/GNVW invariant.
