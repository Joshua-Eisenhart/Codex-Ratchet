# Win/Lose Pattern Derivation Discriminator Audit Verdict

Verdict: **GENUINE-WITH-CAVEATS**.

Adjudication: **(b) the current b6 constraint encoding is vacuous/weak with respect to the 16 assignment bits**. The result is a genuine finite combinatorics discriminator for balance, duality, documented-table SAT, scrambled-table UNSAT, and cross-engine count agreement, but the equal `drop_b6_relation` count and `full_constraints` count do **not** prove that `b6=-b0*b3` is entailed by balance+duality over the assignment table.

The sign relation is real as a **slot-scaffold metadata identity** under the documented Axis0 polarity convention (`Ne/Ni=+1`, `Se/Si=-1`), loop sign convention (`outer=-1`, `inner=+1`), and Axis6 table (`UP=-1`, `DOWN=+1`). It is not implemented as a predicate over the assignment bits being enumerated.

## Decisive Source Finding

In `system_v6/sims/winlose_pattern_derivation_discriminator/winlose_pattern_derivation_discriminator_jax.py`:

- `axis6_relation_holds(row)` checks row metadata: `AXIS6_SIGN[row["axis6"]] == -B0_SIGN_BY_TOPOLOGY[row["topology"]] * LOOP_SIGN[row["loop"]]`.
- `axis6_scaffold_ok()` checks all slot rows.
- `axis6_relation_ok(bits)` ignores `bits` and returns `axis6_scaffold_ok()`.
- `constraints_ok(bits)` includes `axis6_relation_ok(bits)`, so the b6 clause can only reject the entire static scaffold if a slot row is internally inconsistent. It cannot filter one assignment table but not another.
- Z3 and cvc5 paths have the same shape: if `axis6_scaffold_ok()` is false they assert false; otherwise no b6/table-bit constraint is added.

Therefore `drop_b6_relation=36` and `full_constraints=36` is expected even if the b6 clause is retained, because for this scaffold the clause is a constant true predicate.

## Independent Recompute

I recomputed the finite model space with a clean pure-Python brute-force enumerator over the 16 assignment bits, without importing the sim module.

Result:

- `full_count = 36`
- `drop_b6_count = 36`
- `documented_sat = true`
- `scrambled_sat = false`
- `scrambled_balance = false`
- `scrambled_duality = false`
- `orbit_count = 3`
- `orbit_sizes = [6, 6, 24]`
- documented table orbit key has Type-1 outer/inner WIN intersection size `1`

The 36 count follows from balance plus the declared case-inversion duality. Under simultaneous S4 relabeling of the four topology slots, the models are pairs of two-element Type-1 WIN sets `(outer, inner)`, with orbit invariant `|outer ∩ inner|`. The orbit sizes are:

- intersection `0`: size `6`
- intersection `1`: size `24`
- intersection `2`: size `6`

## b6 Relation Across the 36

All 36 full models sit on the same static slot scaffold, and every slot row satisfies `b6=-b0*b3`. That verifies scaffold consistency, not derivation from the assignment constraints.

Spot checks:

- slot 0: Type-1 `Se` outer `TiSe`, `UP`, `LOSE`; `b0=-1`, `b3=-1`, `b6=-1`; relation holds.
- slot 1: Type-1 `Ne` outer `NeTi`, `DOWN`, `WIN`; `b0=+1`, `b3=-1`, `b6=+1`; relation holds.
- slot 6: Type-1 `Ni` inner `TeNi`, `UP`, `lose`; `b0=+1`, `b3=+1`, `b6=-1`; relation holds.
- slot 13: Type-2 `Ne` inner `TiNe`, `UP`, `win`; `b0=+1`, `b3=+1`, `b6=-1`; relation holds.

## Table Transcription And b0 Grounding

The documented table rows are correctly transcribed from the screenshot receipt for topology, loop, token, Axis6 UP/DOWN, signed operator, and WIN/LOSE result. Checked sources include:

- `system_v6/receipts/screenshots_math_report_20260609.md`, `NeTX.png` section.
- `system_v6/receipts/screenshots_math_report_20260609.md`, `Topology.png` section.
- `system_v6/receipts/screenshots_math_report_20260609.md`, `Outer Malor.png` / Type-2 loop view section.

Where b0 comes from:

- b0 is **not** directly transcribed from those screenshot chart cells.
- b0 comes from the separate Axis0 polarity convention in the v5/v6 axis docs: `Ne/Ni=+1`, `Se/Si=-1`.
- This convention is documented as a local sign encoding / strong symbolic alignment, with Axis0 bridge still open. It is grounded in the chart topology families and the taijitu/Axis0 polarity doctrine, but it is not a screenshot-cell value and not a closed cut-state theorem.

Important caveat: `system_v5/READ ONLY Reference Docs/AXIS_0_1_2_QIT_MATH.md` refers to a companion `AXIS_3_4_5_6_QIT_MATH.md`, but that file is absent in this checkout. That does not break the finite discriminator, but it weakens any claim that the full b6 derivation chain is closed in-repo.

## Scrambled Control

The scrambled control is genuine for this constraint system. Flipping Type-1 `Se` outer from `LOSE` to `WIN` makes:

- Type-1 outer balance become `WIN=3`, `LOSE=1`.
- Se duality fail between Type-1 outer and Type-2 inner.

The existing receipts report `unsat` across Julia/Z3, JAX/Z3, JAX/cvc5, PyTorch/Z3, and PyTorch/cvc5; the independent pure-Python check also rejects the scrambled table.

## Pin / Envelope / Ceiling

Live source hashes match the result pins:

- JAX source: `76a17df82e4bc00b406e099314bc2077fa4ec530c0905391c0f8dce467db910a`
- PyTorch source: `1cfcc3c85257259b3b74ac9e38912e28e49904d2bb6d62c021507c0b411e30c4`
- Julia source: `926d2e6853ce4f72cd4bbbe04473f554a794772be01db3a0c338dbaa09f9ed76`
- Envelope source: `b7d066c32594fe1a17c91b1b1b821e3f9dcd3636934a4747857a93e7fef81c60`

Envelope state:

- `all_pass=true`
- `classification=scratch_diagnostic`
- `promotion_allowed=false`
- `formal_admission_allowed=false`
- `claim_ceiling=scratch diagnostic finite combinatorics discriminator only; no canonical promotion, no bridge claim, no scientific admission`

Git status caveat: the target sim directory is currently untracked in this checkout. That does not invalidate the file-level audit, but it reinforces that this should not be described as canonical or admitted.

## Final Classification

**GENUINE-WITH-CAVEATS**.

The finite discriminator and scrambled negative control are genuine. The b6 count equality does **not** establish "sign law is a theorem" from balance+duality. The correct finding is:

> The documented slot scaffold satisfies `b6=-b0*b3` under the current topology/loop sign conventions, but the implemented b6 clause is constant with respect to table assignments. Current evidence supports scaffold consistency, not a derived sign-law theorem over the 36 assignment models.
