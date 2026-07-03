# Codex-Ratchet Audit, Source Resolutions & Peak-State Plan
2026-07-01 · claude.ai auditor session · repo: Codex-Ratchet@main (public, 14,208 files)
scratch_diagnostic; promotion_allowed=false

## 1. Two owner-level open items just RESOLVED BY YOUR OWN SOURCE DOCS

### 1a. The two-64s tension — resolved by ENGINE_64_SCHEDULE_ATLAS.md §9–§10
The atlas declares a **three-layer split** that the spec's §7g collapsed:
- **Live runtime 64** = 2 engines × 8 terrains × 4 operator slots (slot space)
- **Chart atlas 64** = 8 terrains × 8 signed operators, an index surface on
  which exactly **16 cells are starred "chart-locked macro-stage occupancies"**
- **Hexagram 64** = optional tag family, fenced from semantics
So both readings were always in the source *as different layers with a
governing split*: 64 is an address/slot space; 16 is the chart-locked stage
set; the 48 unstarred cells are legal addresses, not stages. The atlas even
fences itself: "this document ≠ proof of full 64-state closure."
**Spec edit needed:** §7g should present the three layers and stop implying
all 64 runtime slots are stages. The 11/64 collapse result and the 16-stage
layer then stop competing — they describe different layers.

### 1b. The terrain-level a2 bit — resolved by TERRAIN_LAW_LEDGER.md lines 17–22
The ledger **defines** Ax2: Direct = "lab frame, V_s(u) = I"; Conjugated =
"co-rotating Weyl frame, V_s(u) ≠ I". So a2 on terrains is an **installed
frame flag** — which frame the terrain's dynamics is run/expressed in — not an
intrinsic generator property. This explains, at the source level, every
negative result of the audits: no functional of a generator can read which
frame it is *declared* to run in (P2/P3), and no element maps direct
generators to conjugated ones (P11 result 4) because the bit was never a map.
Consequences, all of which sharpen the ledger honestly:
- The open item "find the generator-level invariant realizing a2" **closes as
  ill-posed**: a2 is installed, readable only operationally through
  dissipation (§7n's 0.22-vs-0 frame sensitivity) — matching v7's own concept
  name "contextuality as installed context independence."
- §7m's XOR is now explicitly an identity over **one measured bit (a1 =
  non-unitality, earned) and one installed bit (a2 = frame flag)** — further
  cementing its admissible-candidate (partly definitional) status.
- The ledger also assigns the operator pairs BY frame ("i-operators native to
  direct," "e-operators native to conjugated," Te/Fe called "conjugated-frame
  ops," lines 21–22, 64, 74–77). Combined with P1, this substantiates §7u
  from source: the ledger's single "frame" concept does two jobs that no
  single group element can do (V_s for dynamics, W for the operator-pair
  image) — the latent conflation P11 resolved is now traceable to specific
  ledger lines. **One paste still wanted:** igt-pattern lines 470–478 (private
  Wiki) to fully discharge §7t's source-reading link.

## 2. Repo state (audited)
- **v7 is the live lane** (`system_v7/sims/`, ~30 sims): serious mathematics
  (contextuality SMT via z3/cvc5, GNVW index, Schmidt cut lattices, 1Q–4Q
  inverse-limit towers) with the **exact/jax/pytorch + check_agreement.py**
  pattern — the same cross-substrate architecture as the engines lane I built,
  independently converged. Sampled runs are GREEN here
  (finite_qca_runner: `"failures": []`).
- **Gate infrastructure is real and self-testing:** axis0_terrain_engine_leap_v0
  is a deliberate *bad-twin fixture* (four documented defects: jargon without
  F01/N01 ancestry, SMT count-tautologies tagged load_bearing, unfenced
  verdict tokens, by-construction engine "independence") with recorded gate
  firings. This is mature negative-testing discipline.
- **Known defect class:** repo-root-relative paths (the bad twin errors when
  run from its own directory). Same class as the bundle's H-3 fix; worth a
  one-line convention (`os.path.dirname(__file__)`) in the v7 sim template.
- **v4 probes** (4,297 files) are the legacy sim mass; treat as archive lane.
- **Leviathan patches:** not in this repo. `lev-os/leviathan` and `LevRatchet`
  are private — unreachable from this session. To audit the patches: zip and
  upload them here, or run the audit from your credentialed Claude Code
  thread. The public traces (hyperlap receipts, admission artifacts in
  system_v5/ops) show the harness *around* Leviathan is real; whether `lev`
  produces a genuine end-to-end signed receipt remains the standing ClaimGate
  blocker from your other project thread.

## 3. What "peak" concretely means for this system, in order
1. **Wire the harnesses into CI** (tooling shipped alongside this report):
   every push runs the bundle harness, the engines cross-substrate validation,
   and the v7 check_agreements. Right now nothing enforces green-on-push; the
   discipline lives in habits and agent contracts. CI makes it structural —
   receipts by machine, which is the ClaimGate thesis applied to this repo.
2. **Land the two source resolutions (§1) in the spec** — they close two of
   the three pending owner decisions with zero new mathematics.
3. **Merge the constraint-core bundle into the repo** as
   `system_v7/constraint_core/` (spec + PURE_MATH_CORE + sims + run_all.py +
   engines/). It currently lives only in chat-thread zips and the Wiki; the
   repo's gates should own it.
4. **Run the Julia leg** on your laptop (first execution — it's the untested
   fourth route) and the 3-qubit scale-up of the engines contract, where the
   batched substrates stop being a formality.
5. **The Leviathan receipt end-to-end** — still the single highest-leverage
   external-authority step for the whole program, unchanged from the
   ClaimGate audits.
6. **The human-expert afternoon** — unchanged from the legitimacy ledger, and
   PURE_MATH_CORE.md is the artifact to hand over.

## 4. Standing corrected ledger after this session
Earned this session: P1–P12 (see PURE_MATH_CORE), the χ₂ sector meter, the
axis-load-bearing fact, cross-substrate GREEN (numpy/JAX/torch), and the two
source resolutions above. Open: charge-specific χ₂ *as an operational reader
of the installed frame through dissipation* (reframed by §1b — no longer
"derive the flag"), the igt-pattern paste, the Julia first run, Leviathan
end-to-end. The ratchet earns canon.
