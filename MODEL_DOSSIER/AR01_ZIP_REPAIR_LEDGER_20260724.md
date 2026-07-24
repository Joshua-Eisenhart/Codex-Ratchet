# AR01 zip repair ledger — what needs to be fixed in the recovery pack bundle

**Date:** 2026-07-24
**Subject:** `RATCHET_LLM_AGNOSTIC_RECOVERY_AND_CONTROL_PACK_20260723_v1_PLUS_AR01_AUDIT.zip`
**Companion doc:** `CR_MASTER_MAP_WHAT_EVERYTHING_IS_20260724.md` (my full map of the system)
**Checked against:** the ACTUAL current branch `session/r0-three-engine-probes` at `6ccd79bdf` — not the stale `main` the auditor pinned.

## The one rule that governs every fix

The v1 pack is IMMUTABLE (SHA-256 `10de08d6…`). Nothing below is a patch to v1. Every fix lands in a separately named **v2 candidate** with explicit lineage to the accepted finding, and v2 may not be generated until you disposition the 16 owner decisions (OD-01–OD-16). The pack's own read-first says this; the AR01 audit says this; I agree with both. This ledger is the patch PLAN, not the patch.

## First, the audit's own defect (fix the auditor before the audited)

**A-0. AR01 audited a two-week-stale main.**
The audit pinned `Joshua-Eisenhart/Codex-Ratchet@8744666` — that is `main` as of **2026-07-09**. The working branch `session/r0-three-engine-probes` is **213 commits ahead** and contains almost everything the audit says is missing: `system_v8/`, the three-engine seal, blocking CI, the transport canary, the hostile corpus, the Lev eval seam. Findings derived purely from main's absence of these are artifacts.

*Fix for AR02:* re-pin against the session branch head (or against whatever tree you bind as v8 under OD-09). Separately — and this is a real repo problem the audit exposed, not an audit error — **`main` is what every external auditor sees, and `main` still fronts v6-era content.** Until the branch is merged or `main`'s front-door docs are updated, every future external audit will repeat this mistake. That merge/bind is your call (it IS the OD-09 decision in mechanical form).

---

## Fixes to the v1 pack (for the v2 candidate), ordered by severity

### F-1. Restore the no-primitive root to the compact boot object — BLOCKER

The compact boot files start from finite addresses and probe functions without declaring that individuation, output-equality, update, time, probability, and metric are INSTALLED presumptions. This is the exact door through which nominalist vocabulary wraps a conventional ontology.

*Fix:* the boot prompt and `01_OWNER_MODEL/NOMINALIST_CONSTRAINT_MODEL.md` must open with the no-primitive family (OD-02's registry, once you confirm membership) and the rule that any use of these structures is a declared, chargeable presumption. Blocked on OD-01/OD-02.

### F-2. Un-reduce MSS from Pareto settlement — BLOCKER

The pack renders MSS as packet-relative partial orders + non-dominated frontier. That is not the admission rule. MSS is the weakest-minimal-presumption survivor meta-gate for persistent/evolvable structure — still-killable, compositional, presumption-charged; Pareto machinery is at most downstream reporting.

*Fix:* rewrite the MSS section of `07_RATCHET_MANIFOLD_ENGINES/RATCHET_MSS_SETTLEMENT_AND_PURGATORY.md` to state the admission rule, the nested-chain comparison unit, no-maximality, chain-extension-as-progress, and Purgatory/re-merge; demote every Pareto mention to "reporting mechanism, never admission." Blocked on OD-04 for the precise rule statement.

### F-3. De-linearize the manifold presentation — BLOCKER

The pack's `CTX → QUOT → DENS → PURE/MIX → HOPF → CHIR → CUT → CORR → PROC → HIST` chain is a one-way enrichment ladder. The model is nested-simultaneous with downward/backward constraint, geometry and entropy paired at EVERY node, renesting, and branch rivalry.

*Fix:* relabel the chain `MANIFOLD_CANDIDATE_A` everywhere it appears (boot prompt, architecture files, schemas); add the five-kinds table (stratum / Axis-0 field / Ratchet / engine-DOF / governance) as the frame; the actual generative topology ships only after OD-08.

### F-4. Fix Axis 0's authority split — BLOCKER

The pack promotes one Gemini-derived set-union/telemetry tuple to "Current definition" of Axis 0.

*Fix:* split into (a) OWNER-LOCKED role — whole-manifold entropy–geometry gradient/cofield, innate, the drive; homeostatic/exploratory significance; readout Φ₀ late, via cut — and (b) NAMED CANDIDATES for any formula, each with its missing obligations listed (typed carrier, maps, units, uniqueness). The words "current definition" must not appear next to any formula. Blocked on OD-07 only for which candidates to keep listed.

### F-5. Restore ring-checkerboard and spinor/chirality to contested positions — BLOCKER

The pack silently decided OD-05 and OD-06 by placing ring/Hopf after density carriers and chirality as a late branch.

*Fix:* present ring-checkerboard as a live RIVAL literal carrier (branch C of OD-05), and spinor/chirality/orientation as (at least) four distinct roles that must not merge into one layer. No ordering claim until you rule.

### F-6. Add the corrected Axes 4/5/6 to the compact boot files — BLOCKER

The corrections (Axis 4 = induction/heating vs deduction/cooling direction; Axis 5 = magnitude; Axis 6 = TopoOp DOWN / OpTopo UP precedence) exist only in the source appendix; a cold-started model will import a conflicting historical table.

*Fix:* copy the corrected qualitative roles into `00_START_HERE/MODEL_BOOT_PROMPT.md` and the identity checksum, marked owner-source with quantitative bindings open; add an explicit DO-NOT-IMPORT list of the historical axis aliases. Blocked on OD-16 for final wording.

### F-7. Fix the claim-envelope schema's evidence tyranny — BLOCKER (schema bug, mechanically checkable)

`11_SCHEMAS/claim_envelope_v1.proposed.schema.json` REQUIRES LevOS evidence for every claim. Consequence, already observed in the wild: honest non-Lev claims are pressured to fabricate dummy host evidence, and an evidence-import path (`host_evidence_consumed` with `live_lev_consumed: false`) gets laundered into "ran under LevOS."

*Fix:* make evidence lanes CONDITIONAL on claim type via a claim-type matrix (OD-13): Lev evidence required iff the claim is Lev-integrated; independent Julia/JAX iff numerical; solver certificates iff SAT/SMT; and add `live_lev_consumed: true` as the ONLY predicate that supports a "ran under LevOS" claim. This one is schema engineering and can be drafted now, gated on OD-13 for the matrix rows.

### F-8. Rename or fix the 64-slot engine framing — BLOCKER (and a live repo defect, not just a pack defect)

The pack correctly states the checksum (16 positions × 4 bindings = 64 candidate cells, `4^16` assignments). The REPO's packet builds 16 macro rows × 4 chronological substages and, worse, verified this session on the CURRENT branch: `system_v7/sims/qit_full_type1_type2_64_live_v1/qit_full_type1_type2_64_live_v1_common.py` orders Type-1 outer deduction `Se→Ne→Ni→Si` against the checksum's `Ne→Si→Se→Ni` (all four loop orders differ).

*Fix, two parts:*
- Pack side: keep the checksum statement; add an explicit warning that the repo packet is a DIFFERENT typed object whose passes validate nothing about the owner engines.
- Repo side (after OD-10/OD-11): either correct the packet's orders to the checksum and rerun everything downstream of it, or rename it (`sequential_substage_protocol_v1` or similar) and firewall its results from engine-validation claims. Option C (both objects, different names, never shared validation) is the audit's safe state and I endorse it.

### F-9. Close the closed-authorship loop in the deterministic-receipt story — MAJOR (partially already fixed, pack must say so precisely)

The audit found: shared Python semantic builder feeding both "independent" legs, decorative native ops, solvers restating authored thresholds, a validator trusting producer fields, renamed envelopes becoming N/A-ok, `json.loads` collapsing duplicate keys, nonblocking CI.

*Fix — split by actual current status:*
- ALREADY FIXED on the branch (pack/audit must be updated to cite them rather than list as open): validator now RE-DERIVES the JAX leg (`4e3acbca9`); CI is blocking (`69c3dc021`).
- STILL LIVE, independently confirmed by our own hostile corpus: duplicate-key last-wins, NaN recompute, renamed-metric chain-pass — the 3 standing GAPs. The fix is the intake supervisor (dup-key rejection via `object_pairs_hook`, NaN guard, pinned schema) with the corpus as acceptance: 2 GAPs flip to HOLD, 7 HOLDs zero-drift.
- STRUCTURAL, needs a card: shared-semantic-builder independence — the Julia and JAX legs must not consume one Python-authored result object; independence is proven by asymmetric mutation and dependency-kill witnesses (the audit's own proposed instrument, adopted).

### F-10. Correct the LevOS evidence semantics in pack prose — MAJOR

Beyond the schema fix (F-7): every place the pack narrates Lev integration must distinguish three states — evidence-import (`live_lev_consumed: false`), live eval decision (`lev.eval_decision.v1` from an actual `lev eval run`), and the not-yet-existing causally attested runtime. The middle state EXISTS and is verified on the branch; the pack, written against stale evidence, does not know that. Cite the verified seam instead of speculating.

### F-11. Bind v8 or stop saying v8 — MAJOR (owner action, pack follows)

The pack inherits the "v8" label with no content binding; the audit could not locate a v8 root on main (true of main; false of the branch).

*Fix:* after your OD-09 binding (branch/commit/manifest/new assembly — the session branch at `6ccd79bdf` with `system_v8/` is the obvious candidate), the v2 pack carries the binding as a content manifest: exact tree hash, exact file list. Until then, every "v8" in the pack gets marked "owner label, unbound."

### F-12. Keep the control-design directory honestly labeled — MINOR (mostly right already)

`09_CONTROL_DESIGN/` is properly labeled as designs-not-evidence. Two touch-ups: (a) the enforcement ladder must state which rung the CURRENT branch actually occupies (artifact checker + envelope gate + blocking CI — rung 1, approaching rung 2); (b) the "first bounded implementation target" (one exact-small Julia/JAX transaction with mutation/dependency-kill witnesses under strict ticketing) should be cross-referenced to the already-queued repo cards so two build queues don't diverge.

### F-13. Preserve the fourteen things v1 got right — CONSTRAINT ON v2, not a fix

The audit's "must retain" list is correct and any v2 regression against it is a bug: exact engine orders and 16-vs-64 distinction; unreset handoff; both loop types in both engines; IGT casing without moralization; finite-dimension ≠ finite-state ≠ finite-universe; typed equality discipline; noncommutation ≠ nonassociativity; no entropy soup; LLMs propose, never settle; deterministic ≠ true; search ≠ proof oracle; finite namesake ≠ native theorem; LevOS separate and unbypassed; full Gemini thread preserved as provenance only.

---

## Dependency map — what blocks what

| Fix | Blocked on | Can start now? |
|---|---|---|
| F-1 no-primitive boot | OD-01, OD-02 | draft yes, ship no |
| F-2 MSS restoration | OD-04 | draft yes, ship no |
| F-3 de-linearized manifold | OD-08 | relabel-as-candidate: NOW |
| F-4 Axis-0 split | OD-07 | role/candidate split: NOW |
| F-5 ring/spinor contested | OD-05, OD-06 | mark-as-open: NOW |
| F-6 Axes 4/5/6 in boot | OD-16 | copy-with-open-markers: NOW |
| F-7 schema conditionality | OD-13 | schema draft: NOW |
| F-8 64-slot rename/fix | OD-10, OD-11 | pack warning: NOW; repo action: after ruling |
| F-9 closed-loop closure | none (cards exist) | intake supervisor + independence witnesses: NOW |
| F-10 Lev semantics | none | NOW (cite verified seam) |
| F-11 v8 binding | OD-09 | owner act |
| F-12 control-design labels | none | NOW |
| F-13 retain-list | permanent constraint | — |

"NOW" items are safe because they only DEMOTE (candidate labels, open markers, warnings) or fix mechanical bugs — they never select a branch of an owner decision. Everything that would select waits for you.

## The 16 owner decisions, one line each (answer in any order; free-form corrections override the options)

1. **OD-01** root object: installed floor / strict nominalist / two-lane.
2. **OD-02** confirm the no-primitive registry membership.
3. **OD-03** MSS↔probes order: probes-first / MSS-first / co-ratchet fixed point.
4. **OD-04** MSS precise admission rule vs Pareto-as-reporting.
5. **OD-05** ring-checkerboard: native carrier / presentation / both-as-rivals.
6. **OD-06** spinor/chirality/orientation: assign each of the ~four roles.
7. **OD-07** Axis 0: confirm role locks 1–3; keep/kill candidate formulas 4–7.
8. **OD-08** the manifold's actual generative graph (or approve one to test).
9. **OD-09** bind v8 to a concrete tree (session branch at `6ccd79bdf` is the candidate on the table).
10. **OD-10** 64 = candidate cells (A) / runtime substages (B) / both-with-different-names (C).
11. **OD-11** authoritative stage orders → correct or rename the repo packet.
12. **OD-12** build order: gate-first / engines-first / parallel-then-joined (current de facto: parallel).
13. **OD-13** evidence-lane matrix by claim type.
14. **OD-14** confirm NumPy-satellite rule as stated (current statement already wins).
15. **OD-15** engine symbols: order locked, channel bindings as rival candidates (confirm).
16. **OD-16** Axes 4/5/6 corrected meanings: literal-vs-label heating, magnitude without unearned metric, Axis-6 composition convention.

Nothing in this ledger has been executed. v1 stays byte-identical. The NOW-column items await your go; the rest await the decisions.
