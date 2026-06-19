# BUILD CARD: mct_dynamic_admissibility_packet_v0 — the GEOMETRIC M(C,t) front-door packet

One object, one claim, one card. Claim under test: a finite, dynamic admissibility packet
M(C,t) = (S_t, C_t, Probe_t, Val_t, ~_t, Q_t, Adm_t, E_t, Poss_t, H_t, R_t, Var_t, U_t, Ctrl_t, Rec_t)
can be computed — not asserted — with states that are actual spinor samples on nested Hopf shells, probes that are computed binned observables, a quotient in which phi-blindness EMERGES, dynamics from the committed operator/terrain forms, and the five manifold operations as MEASURED behaviors with controls that can fail.

Ceiling (hard): classification = "scratch_diagnostic", promotion_allowed = false, formal_admission_allowed = false. No manifold-admission, axis-level, Axis-0-closure, bridge, IGT, or physics-name claim. (Computed Axis0-gradient ROWS are permitted as readout-only fields per the owner-routed runbook — `axis0_status: "readout_only_no_closure"` — they admit nothing.) This receipt is an M(C,t) packet computation, nothing above it.

## Read first (binding inputs, in order)
1. /Users/joshuaeisenhart/Codex-Ratchet/system_v6/README.md  — intake rules, engine roles, evidence ladder, absence/novelty rules
2. /Users/joshuaeisenhart/Codex-Ratchet/system_v6/receipts/mct_reconciled_spec_20260609.md  — the packet spec + build-card skeleton (§6) + choice points (§3) + fixture semantics
3. /Users/joshuaeisenhart/Codex-Ratchet/system_v6/receipts/mct_mine_adjudication_20260610.md  — gap adjudication + failure fence (§D) + choice-point dispositions (§C)
4. /Users/joshuaeisenhart/Codex-Ratchet/system_v6/receipts/mct_wiki_source_map_20260610.md  — per-requirement source math + conflicts to preserve (§B) + absence findings (§C)
5. /Users/joshuaeisenhart/wiki/projects/codex-ratchet/ring-checkerboard-three-presentations-sim-engine-runbook-2026-06-09.md  — the owner-routed finite support model (three candidate-equivalent presentations + engine roles + the M(C,t) card requirements §"What the M(C,t) card should require"); its claim ceiling binds here too
6. Geometric sources the math comes from (cite, never re-derive doctrine):
   - spinor/Hopf chart + nested tori: /Users/joshuaeisenhart/wiki/raw/articles/system-v5-reference-docs/Formal constraints and geometry.md:78-88, 157-166; system_v6/foundations/working_math_scaffold_20260609.md:25-64, 187-207, 237-245
   - density reduction / fiber-blindness: terrain rosetta strong math.md:3-20 (same dir); terrain math.md:43-49
   - committed operator forms: system_v5/READ ONLY Reference Docs/operator math explicit.md (Ti/Te/Fi/Fe channel/unitary definitions)
   - committed terrain forms: terrain math.md:51-152; system_v6/sims/terrain_generator_sheet_packet/ (reuse its source-locked forms; do NOT rebuild)
   - five operations + W_n update frame: working_math_scaffold_20260609.md:291-301; /Users/joshuaeisenhart/wiki/concepts/field-wide-compression-probe-contract.md:64-102, 123-203, 211-232
   - whole-field readout contract + falsifiers: field-wide-compression-probe-contract.md:123-163, 288-305

## PIN block (FROZEN — identical dict across all engine legs, status fields per terrain-packet convention)
- carrier_chart (PINNED from the owner-routed runbook): psi_s(phi_i, chi_j; eta_k) = ( e^{i(phi_i+chi_j)} cos(eta_k), e^{i(phi_i-chi_j)} sin(eta_k) ), unit norm in C^2. Builder MUST check consistency with the chart in `Formal constraints and geometry.md:78-88` and record agreement/divergence in the result (never silently substitute).
- L/R sheet realization (FLAGGED GAP — pin, don't decorate): the runbook formula as written does not depend on s, so without a pinned realization the sheets are decorative labels (a G1 failure). PIN how s in {L,R} enters, source-locked to the left/right Weyl fields of `Formal constraints and geometry.md:157-166` (e.g. chirality-conjugate chart or sign convention on chi), status PINNED-CHOICE with the source quoted; the two sheets must be separable by at least one computed probe row.
- grid (PINNED-CHOICE, annotation: ring-checkerboard = eta-shell rings x (phi,chi) checkerboard, used here ONLY as finite shell/grid discretization vocabulary; the ring-checkerboard mapping question stays OPEN with all four live readings preserved (nested Hopf tori / 64-cell division-algebra carrier / engine-stage microstate board / separate pre-geometric grid — pre-ai-rosetta provenance doc:313-317); this build does not close that doctrine):
  eta_k in {pi/8, pi/4, 3*pi/8} (3 nested shells); phi_i = 2*pi*i/8, chi_j = 2*pi*j/8, i,j = 0..7; |S_0| = 2*3*8*8 = 384 spinor samples.
- rho = psi psi^dagger computed per sample; Bloch vector computed; entropies base e.
- probe families (each a finite map to a finite codomain). Provenance note: the wiki defines finite probe/readout families, expectation values Tr(O rho), and the probe-equivalence quotient — it does NOT define the phrase "binned observables" (wiki-lane absence finding, mct_wiki_source_map §C). This build IMPLEMENTATION-BINS finite probe/readouts into finite codomains; that is implementation vocabulary, pinned here, not standing wiki math. Pin exact bin edges in PIN_SPEC:
  P_density (binned Bloch components), P_shell (eta index), P_loop (loop class: fiber/inner vs lifted-base/outer — the probe must preserve the fiber/base distinction of terrain math.md:43-49, not only base-loop), P_order (order-gap norm bins), P_phase (a phase-sensitive NON-density probe, e.g. binned Re/Im overlap with a pinned reference spinor — this is the probe whose PRESENCE/ABSENCE makes phi-blindness emerge or not).
- Axis0-gradient READOUT ROWS (readout-only, owner-routed via the runbook; NO Axis0 closure): compute eta_k and b0 = sign(cos(2*eta_k)) per sample as named finite functionals. PIN the boundary policy: at eta = pi/4, cos(2*eta) = 0, so b0 takes values in {-1, 0, +1} with 0 = boundary shell (PINNED-CHOICE; gives inner/boundary/outer gradient rows). Result field `axis0_status: "readout_only_no_closure"`. Any comparison to feedback-polarity language only under explicitly named functionals; no Ne/Ni/Se/Si claim fields.
- support_table_hash (sha256 of the canonical spinor table) and presentation IDs for the three charts (flat / spherical-shell / nested-ring) emitted in every leg's result.
- choice points (from adjudication §C — adopt; do not re-litigate):
  representation_mode = carrier_retained (main) + quotient_materialized (side branch, both reported)
  constraint_form = state_predicate (main) + probe_row_predicate (transported view)
  fixed root C + explicit C_t view; any active-constraint update is its own logged U_t operation
  folding = equivalence-respecting default; aggregation branch ONLY with explicit aggregation + killed-information ledger
  relation updates = finite delta (E union Delta+) \ Delta-
  entropy objects NAMED EVERY TIME: H_Q (class-distribution entropy), A_Q (avg ambiguity), support_size, possibility_mass — never an unnamed H
  self_loop_policy: compute BOTH erase and retain; emit both values; default = owner_pending
  ratchet pass condition: emit BOTH literal_table_diff AND non_isomorphic_diff; pass_condition field = "owner_pending"
  8-state cycle fixture (spec §5) runs as a SIDECAR operation-semantics control only — never the main support.

## Build gates (the failure fence — an abstract skeleton MUST fail these)
G1. Main state support is the computed 384-spinor table (complex entries on disk in results), NOT {0..7} or symbolic labels.
G2. phi-blindness EMERGES: apply global phase shifts alpha in a pinned set to all samples; show every P_density/P_shell/P_loop row is bit-identical (classes collapse) while P_phase separates the same pairs. The quotient Q_t is computed from probe rows, and the blindness appears ONLY when P_phase is excluded from the active family. Both directions reported.
G3. Probe rows are computed numbers binned by pinned edges; emit the full row table. A probe named but not computed = build failure.
G4. Dynamics: apply the committed Ti/Te/Fi/Fe channel/unitary forms and at least two terrain-generator stage maps from the source-locked terrain packet to the spinor/density samples; measure Phi_T(O(rho)) vs O(Phi_T(rho)) order gaps (nonzero for a pinned noncommuting pair, zero for a pinned commuting control pair).
G5. Five operations as measured behaviors on the geometric support, each with a named computed quantity that changes/preserves exactly as declared. Provenance split (preserve, do not smooth): compression/expansion measurement contracts are WIKI-sourced (field-wide-compression-probe-contract.md:165-203); the warping/folding/reindexing pass/fail mechanics are a REPO-SPEC OPERATIONALIZATION (mct_reconciled_spec_20260609.md:133-185) — the wiki names these three operations but contains no measured contract for them under those names (wiki-lane absence finding §C). Result fields for those three must carry `contract_provenance: "repo_spec_operationalization"`; this build does not claim wiki closure for them:
   compression (drop P_phase from active family): support_size of Q_t drops / A_Q rises; H_Q reported (direction per spec §121-132, both H_Q and A_Q named)
   expansion (add a probe): classes split; counts reported
   warping (delta update on E_t): named relation rows change; ablation gap computed
   folding (equivalence-respecting pi): ker(pi) subset ~_t checked by computation; |E| under both self-loop policies (the sidecar fixture must reproduce spec values |E_3| = 4 erase / 8 retain)
   reindexing (pinned label permutation): every declared invariant byte-stable; non-invariant raw labels change.
G6. Whole-field readout: at least one E_t-dependent readout (relation-ablation gap, connectedness/transport ledger, or order-commutator) must CHANGE under relation ablation, and the local-only baseline must NOT reproduce the field-wide readout. If relation ablation, product/null relation, and local-only controls preserve every claimed readout, the packet FAILS the field-wide contract (field-wide-compression-probe-contract.md:123-163, 288-305).
G8. Three-presentation consistency (runbook target, candidate-equivalence NOT assumed): compute the flat-grid chart, spherical-shell chart, and nested-ring/Hopf-torus chart of the SAME pinned support; they must agree on finite support counts, adjacency, shell/eta gradient rows, quotient classes, and phi-blindness under density probes. Disagreement controls must break agreement where expected: erase shell nesting, flatten spherical to board, drop the fiber coordinate. Report agreement/disagreement per readout; equivalence stays a build target, never a settled-theorem claim.
G7. SMT is load-bearing on COMPUTED values: z3 AND cvc5 each receive the computed probe rows (not hardcoded literals) and derive the phi-blindness separation claim — real computed rows -> UNSAT for a density-probe separator of same-fiber pairs; ERASED control (phase probe injected / rows scrambled) -> SAT. Both solver verdicts recorded separately. A hardcoded-spectrum SMT = decorative = build failure.

## Controls that can fail (each must actually fire)
drop-F01 / drop-N01 (constraint ablation flips Adm_t), wrong-order update, invalid fold attempt (rejected or fully ledgered), relation-ablation, local-only baseline, product/null relation, label-shuffle null, commuting-pair zero-gap, phase-probe-included control (phi-blindness must NOT appear — the flip), shell-nesting erasure, fiber-coordinate erasure, flat/spherical/ring presentation-disagreement controls (G8).

## Engines (three-engine claim-bearing mode, README roles)
Engines are independent evidence backends — do NOT map the three presentations one-to-one onto engines (runbook rule); each claim-bearing readout is computed by Julia and cross-checked. Julia = canon (QuantumOptics states/channels, Graphs.jl for relation/fold checks, Z3.jl; values are the reference; same env pattern as terrain_generator_sheet_packet). JAX = batched sweep over the 384-sample grid, probe families, alpha shifts, Axis0-gradient rows (rich packages per jax-sim skill, never bare jnp; z3+cvc5 python here). PyTorch = the E_t relation graph lane: graph construction, relation ablation, transport/connectedness readouts (torch_geometric or adjacency autograd machinery; scoped, never arbiter). NumPy = flat-checkerboard BASELINE/CONTROL lane only (v6 README control-lane rule + runbook ceiling): flat grids, cell IDs, adjacency arrays, row-equality quotient fixtures, expected values; NO NumPy-only claim path for any QIT/nonclassical/admitted readout. Identical PIN block in all legs. Like-for-like shared scalars only (same named observable compared across legs; never aggregates over different observables). Evidence ladder: Julia canon value -> exact/symbolic confirmation where available -> z3+cvc5 derive-in-solver -> cross-engine agreement as smoke test only.

## Files to create (exactly these; one folder, atomic)
system_v6/sims/mct_dynamic_admissibility_packet_v0/
  mct_dynamic_admissibility_packet_v0_julia.jl
  mct_dynamic_admissibility_packet_v0_jax.py
  mct_dynamic_admissibility_packet_v0_pytorch.py
  mct_dynamic_admissibility_packet_v0_envelope.py
  build_card.md            (copy of this card, verbatim)
  results/*.json           (per-leg results + envelope result)
Do NOT create audit_verdict.md (fresh-audit lane writes it). Do NOT edit any existing file anywhere.

## Acceptance (builder self-check is NOT evidence; these will be re-run mechanically)
- all three legs run standalone, exit 0, fresh result JSONs
- envelope passes scripts validator: python scripts/validate_three_engine_sim_result.py <envelope_result> --require-pytorch -> ok:true
- PIN blocks byte-identical across legs; every gate G1-G8 has a named computed receipt field; every control listed above fired and its flip/fail is recorded with values; both owner_pending fields emitted; sidecar fixture reproduces |E_3| = 4/8; support_table_hash + three presentation IDs + axis0_status="readout_only_no_closure" present in results; L/R sheets separable by a computed probe row
- result JSON carries classification/promotion/formal_admission ceiling fields exactly as pinned above

## DISPOSITIONS — 2026-06-10

- `pass_condition`: derived default under current doctrine is `non_isomorphic_diff`. Provenance: `derived_default_under_current_doctrine: (1) root axiom a=a iff a~b — identity is probe-relative, not label-primitive, so literal table inequality tests label identity; (2) reindexing is a manifold operation defined as label change preserving all declared invariants — under the literal criterion a pure relabeling would count as ratchet advance, inconsistent within the packet; (3) the label-shuffle null control exists to kill label-level claims. literal_table_diff retained as diagnostic row only. Disposition, not owner lock.`
- `self_loop_policy_default`: derived default under current doctrine is `retain`. Provenance: `derived_default_under_current_doctrine: (1) N01 makes order/history load-bearing where probes preserve it; the no-silent-erasure discipline comes from quotient-pushforward semantics plus killed-information ledger discipline (standing: system_v6/receipts/mct_reconciled_spec_20260609.md); the current owner correction (2026-06-09) identifies the correct interpretation as radiated outward record rather than destroyed information — doctrine-level sources mapped in system_v6/receipts/shell_flow_radiated_information_mine_20260610.md (restatement at doctrine level; exact conservation/reconstruction math not on file there, candidate formalization pending its own build) — erasing a fold-produced self-loop without a ledger silently drops the record that a relation existed between the now-identified states; (2) the quotient pushforward of an edge set naturally retains self-loops — erasure is an extra lossy step (reconciled spec frames retain as the pushforward value, |E_3|=8); (3) the whole-field contract requires edge-transport ledgers, which retention preserves. erase remains available only as an explicitly-ledgered lossy branch. Disposition, not owner lock.`
