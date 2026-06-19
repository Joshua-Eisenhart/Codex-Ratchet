# QCA GNVW fix — rig GONE, machinery GENUINE; "emergence" framing overclaims

**Full-fleet (13 dispatched, 11 verdicts, codex2×4 arbiter; byte-identical-image crux probe): the rig is no longer a fabrication-class defect — the GNVW index machinery is genuine — but the "chirality emerges from block-conjugation" framing is hollow for shifts.** scratch_diagnostic, promotion_allowed=false. Status: `passes local rerun`. Supersedes RIGGED_recovers_shift_FLEET_20260614.md.

## Genuinely fixed (vs the prior rig)
- The `generator(cell±1)` hardcode is GONE — shift rules route through `circuit_image` / `apply_swap` over SWAP schedules (all 3 legs reproduce; INDEP_VERIFY confirms true cyclic shifts).
- The lifted 9-site open line is GONE — the index and the reversibility check share the **same** periodic N=8 ring with bond (7,0).
- The z3/cvc5 SMT is honestly **demoted to supportive** (excluded from the load-bearing set; gate hardened to enforce it). JAX stays the genuine load-bearing leg.

## The machinery is genuine (this is correct, per GNVW)
Shifts → index `±k` (scales correctly, saturating at `±N/2` — the right finite-ring ceiling); support-spreading circuits CZ/CNOT → 0. This matches the **GNVW classification theorem**.

## The residual: a FRAMING overclaim, not a fabrication
- The fleet's crux probe shows the SWAP-conjugated shift image is **byte-identical** to the old hardcoded `generator((cell±k)%N)`. So for a shift, "conjugating through the block circuit" adds nothing — a shift's index is trivially its displacement. The k-scaling is collar-locked (collar width = shift steps), so `index=±k` is by construction. **No support-spreading chirality is demonstrated.**
- `real_vs_trivial_flip_confirmed: true` still overstates (it's a literal sign-pin). → relabel honestly.

## Held divergence + its resolution
Arbiter+majority: genuine=PARTIAL (a SWAP-shift IS a legitimate reversible QCA with a real GNVW index). gemini+deepseek: genuine=NO (support-spreading chirality undemonstrated). **Resolution (candidate, worth fleet-confirming): the GNVW theorem says a 1D QCA has nonzero index IFF it is shift-equivalent** — so "chirality = net transport," and there is NO support-spreading chiral QCA to exhibit. gemini/deepseek ask for the impossible; the machinery is genuine; the only fix needed is to drop the "emergence" framing.

## Disposition (stop the treadmill)
The ring-checkerboard QCA carries a **genuine, floor-computable chirality/flux invariant = directional net transport (GNVW index)** — real and meaningful, the "killer invariant." Residual = drop the "emergence from block-conjugation" framing + relabel `real_vs_trivial_flip`. Mechanical, not another full pass. For the ratchet-emergence sim (task 14): the QCA is a usable run-surface, but the ratchet's order-sensitivity comes from **survivor-set-state-dependence** (the earlier discovery), NOT the GNVW chirality.
