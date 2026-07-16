# Fresh-context audit findings — root_presentation_packet_v0 (2026-07-10)

Auditor: fresh-context Claude fabrication-auditor (did not build the packet). Builder: codex1 gpt-5.6-sol.
Verdict on the ORIGINAL v0 build: FINDINGS (fabrication present). Preserved per append-only evidence law.

Ranked findings against the original packet.py:
1. ROOT-SMUGGLING (severe): all four candidate presentations were readout views of ONE shared persistently-indexed
   numpy carrier (initial_state/apply_update/recompute); the packet could not demonstrate object-free presentation
   because it never built one. Spec sections 2 + 12 violated by construction.
2. Hardcoded kill: `"root_safe": candidate != "G2"` — a string-identity check; the receipt's stated defeat_reason for
   G2 was fabricated. (G2's N01 failure was real; the kill was overdetermined but mis-attributed.)
3. Three decorative controls guaranteed to pass: carrier_family, topology_locality, entropy_geometry_split.
4. A0 drive witness: real computation, but never attacked by any negative twin — unfalsified within scope.
5. lifecycle_status PROVISIONAL_MSS was a ladder overclaim (schema-passing but not semantically earned).
6. Chain of custody: builder rewrote packet.py in place mid-audit (its own repair loop), fixing 2, 3, 5 — corroborates
   the findings but violates append-only evidence discipline; audited objects must be frozen.

Status after builder's own repair (frozen here as *_postrepair_frozen_*): findings 2, 3, 5 addressed
(representation_root_safe computed; decorative controls -> not_applicable; TESTED_SURVIVOR). Findings 1 and 4 PERSIST
and are the v0.1 harden-round obligations. Finding 6 is a process rule going forward: freeze, then audit.

---

# Second fresh audit — harden round 1 (frozen c39a6aa6...), 2026-07-10 late

Verdict: FINDINGS. Discharged: finding 4 (A0 attack real, both sides reachable, all 4 families flip on balanced stream);
finding 1 in SUBSTANCE (immutable tuple stream, candidate-local builds, no shared carrier — verified by auditor code
inspection and a real divergence point G2 vs rest).

New findings (harden round 2 obligations):
A. root_smuggling control for G1/G3/G4 is a tautological string-tag self-comparison (packet.py:300,614,724) — same
   fabrication species as v0's finding 2, relocated. Cannot fail even if a carrier were shared.
B. resolution control decorative for all 4 candidates (self-pair O_COARSE guard; verdict independent of the coarsened
   stream — empirically shown).
C. G2's death is a STRAWMAN: the shipped quotient unions marks ignoring probe. Auditor built a per-probe
   equivalence-closure G2 in the same grammar; it SURVIVES the obligation. The defeat_reason overclaims generality.
   Per spec section 4.1 this new candidate REOPENS the rung: G2' (probe-respecting quotient) must enter the candidate set.
D. Control padding: root_smuggling==lower_structure and order_commutation==history_memory are pairwise identical
   computations; 9 named families, ~7 independent computations; history_memory lacks its own permute/erase manipulation.

Clean: predecessor lineage, ladder discipline (TESTED_SURVIVOR, scratch_diagnostic, promotion false), byte-stable
reruns, kernel validation real.

---

# Final fresh audit — 0.3 migration (frozen d6168ede...), 2026-07-10 late

Verdict: FINDINGS. Survived direct adversarial attack: V functional (genuine unresolved-count, not disguised entropy),
gradient_freeze / gradient_closure / gradient_obligation_coupling (real flips, freeze does NOT reuse the balanced
stream), CLIMB computation (kernel-gated, not hardcoded in the live path), G2/G2P coupling scoping, receipt counts,
determinism, custody.

Findings:
1. (severe) gradient_injection is decorative/gameable: an object-identity whitelist + inert lexical scan, not the
   referee's behavioral source-attribution test. Killed by three direct falsifiers (renamed clone caught only by
   identity; honest wrapper falsely rejected; monkey-patched constant certified licensed+intrinsic). Ship condition:
   demote to "demo of one hostile instance" + record whitelist-brittleness as a 10th open attack.
2. (minor) drive-license condition 2 (licensed_at_current_rung) asserted True in prose, not computed.
3. (cosmetic) hardcoded survivors/frontier literals feed dead-end intermediate objects (overwritten by the
   kernel-validated computation) — fragility, not live fabrication.

Disposition: demotion applied per the audit's own ship condition (relabel + 10th open attack + condition-2 honesty
marker). No math changes. Harden budget remains exhausted; the injection control's replacement with a real behavioral
source-attribution test is FUTURE WORK gated by a new card.
