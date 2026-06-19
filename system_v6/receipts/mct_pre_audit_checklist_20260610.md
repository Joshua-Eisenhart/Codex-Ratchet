# Adversarial pre-audit checklist: `mct_dynamic_admissibility_packet_v0`

This checklist is for a fresh auditor after the build exists. It is written before outcomes are known. Do not accept builder prose, self-checks, or validator success as evidence for any gate below; open the emitted source and result JSONs and recompute the named rows.

Read first:

- `/tmp/mct_build_card_20260610.md`
- `system_v6/README.md`
- `system_v6/receipts/mct_reconciled_spec_20260609.md`
- `system_v6/receipts/mct_mine_adjudication_20260610.md`
- `system_v6/receipts/mct_wiki_source_map_20260610.md`
- `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/ring-checkerboard-three-presentations-sim-engine-runbook-2026-06-09.md`
- the cited source slices in the build card for Hopf/spinor chart, density/fiber blindness, operator forms, terrain forms, five operations, and field-wide readout controls.

Expected build paths:

- `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_julia.jl`
- `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_jax.py`
- `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_pytorch.py`
- `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_envelope.py`
- `system_v6/sims/mct_dynamic_admissibility_packet_v0/build_card.md`
- `system_v6/sims/mct_dynamic_admissibility_packet_v0/results/*.json`

## 1. Gate G1: support is a computed 384-spinor table, not abstract labels

Open:

- all three leg source files;
- per-leg result JSONs and envelope result JSON;
- `build_card.md`.

Recompute:

- Count the pinned grid by hand: `|S_0| = 2 sheets * 3 eta shells * 8 phi values * 8 chi values = 384`.
- Pick one emitted support row and recompute `psi_s(phi_i, chi_j; eta_k) = (exp(i(phi_i+chi_j))*cos(eta_k), exp(i(phi_i-chi_j))*sin(eta_k))`.
- Check unit norm manually for that row: `|psi_0|^2 + |psi_1|^2 = cos(eta_k)^2 + sin(eta_k)^2 = 1`.
- Recompute `rho = psi psi^dagger` for the same row and verify the emitted complex density entries match within the result tolerance.

Fail condition:

- The main support has any size other than 384, is `{0..7}` or symbolic labels, omits complex spinor entries on disk, omits `rho`, has non-unit samples without a declared tolerance failure, or the envelope claims G1 without all three claim-bearing legs computing or reading the real support table.

## 2. PIN block identity and source-lock check

Open:

- `build_card.md`;
- all leg result JSONs;
- envelope result JSON;
- source files where `PIN_SPEC` or equivalent constants are defined.

Recompute:

- Hash or byte-compare the PIN block dictionaries across Julia, JAX, PyTorch, and envelope outputs.
- Compare the copied `build_card.md` to `/tmp/mct_build_card_20260610.md`.
- Check that the emitted chart agreement/divergence field references the Hopf chart in `Formal constraints and geometry.md:78-88`.

Fail condition:

- PIN blocks differ across legs, `build_card.md` is not a verbatim copy, pinned grid/chart/bin/sheet/control values are edited after the fact, or chart consistency is silently assumed without a recorded agreement/divergence field.

## 3. L/R sheet non-decoration check

Open:

- source code implementing `s in {L,R}`;
- emitted support table;
- emitted full probe row table;
- the source slice `Formal constraints and geometry.md:157-166`.

Recompute:

- Pick matching `(eta_k, phi_i, chi_j)` rows for `L` and `R`.
- Compute the sheet-specific chart transform or sign/conjugation convention from the emitted PIN choice.
- Compare at least one emitted probe row field that is supposed to separate `L` and `R`.

Fail condition:

- `s` is only carried as a label, both sheets produce identical computed spinor/density/probe rows for every matched coordinate, or no emitted probe row separates `L` from `R`.

## 4. Manual `b0` Axis0-gradient row check and ceiling fence

Open:

- support table;
- Axis0/readout rows in all leg result JSONs and envelope;
- source implementing `b0`;
- ceiling fields in every result JSON.

Recompute:

- For `eta = pi/8`, compute `cos(2 eta) = cos(pi/4) > 0`, so `b0 = +1`.
- For `eta = pi/4`, compute `cos(2 eta) = cos(pi/2) = 0`, so `b0 = 0`.
- For `eta = 3*pi/8`, compute `cos(2 eta) = cos(3pi/4) < 0`, so `b0 = -1`.
- Verify these rows are readout-only and do not feed an Axis0 closure/admission field.

Fail condition:

- Any emitted `b0` value differs from `+1/0/-1` for the pinned eta shells, `axis0_status` is absent or not exactly `readout_only_no_closure`, or any field implies Axis0 closure, axis-level admission, bridge, IGT, physics, or promotion.

## 5. Gate G2: phi-blindness emerges from computed probe rows

Open:

- full probe row table;
- quotient class table;
- source code for density probes, shell probes, loop probes, phase probes, and quotient formation.

Recompute:

- Pick one sheet, one eta shell, and one chi value.
- For all eight `phi_i = 2*pi*i/8`, manually compute that `rho[0,1] = exp(i*2*chi_j) * cos(eta_k) * sin(eta_k)` is independent of `phi_i`.
- With `P_phase` excluded, count quotient classes for this 8-row slice from emitted density/shell/loop probe keys. The class count must be `1` if those keys are identical.
- With `P_phase` included, recount the same 8-row slice using the emitted phase-sensitive key. The class count must flip to more than `1`, subject to the pinned phase bins.

Fail condition:

- Quotient classes are assigned from chart algebra or labels instead of row equality, the no-phase slice does not collapse as computed, the phase-included control does not split, or the result lacks both directions of the flip.

## 6. Gate G3: probes are computed binned observables

Open:

- PIN bin edges;
- full probe row table;
- source code for every probe family: `P_density`, `P_shell`, `P_loop`, `P_order`, `P_phase`;
- result fields naming probe codomains.

Recompute:

- For the row used in checks 1 and 5, compute Bloch vector entries from `rho` and map them through the pinned `P_density` bin edges.
- Verify `P_shell` equals the eta index and `P_phase` is computed from the pinned reference spinor overlap, not from `phi_i` label text.
- Check that `P_loop` preserves the fiber/base distinction required by `terrain math.md:43-49`.

Fail condition:

- Any probe is named but has no full row table, bin edges are missing, probe values are symbolic labels not computed numbers, `P_phase` is not phase-sensitive, or `P_loop` collapses fiber/base distinction.

## 7. Gate G7: SMT is load-bearing on computed rows

Open:

- source code that builds z3 constraints;
- source code that builds cvc5 constraints;
- solver input dumps if emitted;
- `crossover_proofs` in per-leg and envelope results.

Recompute:

- Trace the solver inputs back to emitted computed probe rows, not to handwritten spectra or literal row constants.
- For one same-fiber pair from check 5, manually identify the density-probe-equal and phase-probe-separating row relationship that the solvers should encode.
- Rerun or inspect the two required polarities: computed density rows make a density-probe separator for same-fiber pairs `UNSAT`; erased/scrambled/phase-injected control flips to `SAT`.
- Compare z3 and cvc5 encodings for independent construction: same mathematical obligation is fine; byte-identical copied assertion strings or a shared pre-rendered SMT blob are not.

Fail condition:

- Solvers receive hardcoded literals instead of computed probe rows, either solver is absent, either erased-control polarity is missing or non-flipping, z3/cvc5 verdicts are copied from one another rather than run separately, or SMT output is not load-bearing for `all_pass`/gate status.

## 8. Gate G4: committed operator and terrain dynamics are applied, not named

Open:

- source code applying `Ti/Te/Fi/Fe`;
- source code reusing terrain generator sheet packet forms;
- order-gap result fields;
- control-pair result fields;
- cited operator and terrain source slices.

Recompute:

- For one pinned noncommuting pair, verify the result actually computes both `Phi_T(O(rho))` and `O(Phi_T(rho))` from the same sampled density row.
- For one pinned commuting control pair, verify the same order-gap formula yields zero or declared tolerance-zero.
- Check at least two terrain-generator stage maps are source-locked to `system_v6/sims/terrain_generator_sheet_packet/` forms rather than rebuilt ad hoc.

Fail condition:

- Dynamics are operation labels with no computed arrays, noncommuting and commuting controls do not use the same formula, terrain forms are substituted silently, or order-correctness is not tested separately from content-correctness.

## 9. Gate G5: five operations have named computed quantities

Open:

- result fields for compression, expansion, warping, folding, and reindexing;
- source implementing `U_t`;
- readout registry and contract provenance fields.

Recompute:

- Compression: drop `P_phase` and recount `support_size`, `|Q_t|`, `H_Q`, and `A_Q` from row tables.
- Expansion: add the phase probe and count the split classes.
- Warping: inspect the finite delta update on `E_t` and recompute at least one changed relation row.
- Folding: check `ker(pi) subset ~_t` from quotient classes; recompute `|E_3| = 4` under self-loop erase and `|E_3| = 8` under retain for the sidecar 8-state fixture.
- Reindexing: apply the pinned label permutation to one small table and verify declared invariants are byte-stable while raw labels change.

Fail condition:

- Any operation is reported only as prose, any named computed quantity is absent or unchanged contrary to the declared pass condition, warping/folding/reindexing omit `contract_provenance: "repo_spec_operationalization"`, or sidecar fixture values are missing.

## 10. Gate G6: whole-field readout is relation-dependent

Open:

- `E_t` relation tables;
- relation-ablation, product/null relation, and local-only baseline controls;
- PyTorch graph readout code;
- readout registry.

Recompute:

- Pick the claimed field-wide readout and identify exactly where it depends on `E_t`.
- Recompute the same readout after relation ablation for one emitted time step.
- Recompute the local-only baseline `f(x, probes(x))` for the same support slice and compare to the field-wide readout.

Fail condition:

- The field-wide readout is reproducible from local probe rows alone, relation ablation/product/null relation preserves every claimed field-wide readout, or the PyTorch relation lane is not load-bearing for any relation-sensitive value.

## 11. Gate G8: three-presentation consistency is not relabeling theater

Open:

- flat-grid, spherical-shell, and nested-ring/Hopf-torus presentation tables;
- presentation IDs and support hashes;
- G8 agreement/disagreement result fields;
- presentation-disagreement controls.

Recompute:

- For one chosen support row, locate its flat, spherical, and nested-ring/Hopf keys and verify they refer to the same pinned sample, not three independent relabels.
- Count support rows in each presentation and compare to 384.
- Recompute one shared readout, such as eta shell index or the no-phase quotient slice from check 5, across all three presentations.
- Inspect controls: shell-nesting erasure, flatten spherical to board, and fiber-coordinate drop must break the expected agreement.

Fail condition:

- The three charts are byte-identical arrays with only labels changed, presentation IDs are missing, agreement is asserted without per-readout comparison, or disagreement controls do not break agreement where expected.

## 12. Cross-leg independence and parity-by-copy check

Open:

- all source files;
- all per-leg result JSONs;
- envelope comparison code;
- `engines.*` metadata.

Recompute:

- Compare arrays that should differ by floating-point path or engine representation, especially complex spinor arrays, density arrays, graph tensors, and quotient row tables.
- Verify `reads_peer_result` is `false` for Julia, JAX, and PyTorch.
- Trace each leg to its own computation path and aligned packages: Julia must use more than bare `LinearAlgebra`; JAX must use richer scoped machinery than bare `jnp` for claim-bearing work; PyTorch must use graph/network/autograd machinery such as PyG or a declared adjacency/autograd path for relation claims.

Fail condition:

- One leg reads or echoes another leg's result JSON, claim-bearing arrays are byte-identical where independent computation should produce different serialization/rounding/path metadata, aligned package use is absent, or the envelope treats cross-engine agreement as proof rather than smoke test.

## 13. NumPy baseline leakage check

Open:

- all Python imports and result metadata;
- NumPy baseline/control output fields;
- envelope claim path fields;
- source code for quotient, support, dynamics, and graph readouts.

Recompute:

- For every claim-bearing value listed in `all_pass`, gates G1-G8, `crossover_proofs`, `divergence`, and operation readouts, trace at least one non-NumPy computation path through Julia/JAX/PyTorch.
- Identify NumPy-only values and verify they are marked baseline/control/supportive only.

Fail condition:

- Any claim-bearing value has only a NumPy computation path, NumPy baseline values are promoted into `all_pass`, or NumPy is treated as a fourth evidence engine for nonclassical/QIT/admissibility claims.

## 14. Control circularity check

Open:

- all control definitions and outputs;
- source code for relation ablation, local-only baseline, phase-probe-included control, shell/fiber erasures, wrong-order update, invalid fold, label shuffle, drop-F01, and drop-N01.

Recompute:

- For each control, identify the exact upstream dependency it is supposed to break.
- Manually inspect whether the measured readout uses that dependency before the control is applied.
- Recompute one relation-ablation readout and one phase-probe-included readout from raw rows.

Fail condition:

- A control cannot fail by construction, the ablated dependency was never used in the readout, local-only baseline is identical to the main pipeline, phase-probe-included control does not flip phi-blindness, or drop-F01/drop-N01 do not flip `Adm_t`.

## 15. Ceiling and status-language check

Open:

- every result JSON;
- envelope result;
- any generated report fields;
- `build_card.md`.

Recompute:

- Check exact ceiling fields: `classification == "scratch_diagnostic"`, `promotion_allowed == false`, `formal_admission_allowed == false`, and `axis0_status == "readout_only_no_closure"`.
- Search result keys and string values for forbidden promotion language: `canonical`, `admitted`, `formal_admission`, `Axis0 closure`, `axis closure`, `bridge`, `IGT`, `physics`, `manifold admission`, `QIT-engine admission`, unless the field explicitly negates or fences the phrase.

Fail condition:

- Any required ceiling field is missing or has a stronger value, any field implies admission/promotion/Axis0 closure/bridge/physics status, or validator success is described as canonical or formal admission.

## 16. Envelope validator and gate-to-field traceability

Open:

- envelope source;
- envelope result JSON;
- validator output if emitted;
- result fields mapping G1-G8 and controls.

Recompute:

- Run the repository validator on the envelope result with `--require-pytorch`.
- For every gate G1-G8, trace the gate claim to at least one named computed result field and then to source code that computes it.
- Verify every listed control has a fired/not-fired value and a flip/fail measurement, not just a boolean label.

Fail condition:

- Validator fails, any gate has no named computed receipt field, any control listed in the build card is absent or not fired, or an `all_pass` field is true while a required gate/control field is missing.

## 17. Source-provenance and absence/conflict preservation check

Open:

- source path/source hash fields;
- `contract_provenance` fields;
- `Var_t` or variant ledger;
- sections B/C of `mct_wiki_source_map_20260610.md`;
- section D of `mct_mine_adjudication_20260610.md`.

Recompute:

- Match every source-backed math claim to a cited source path and line/slice from the card or source map.
- Check that unresolved conflicts are preserved: static M(C) vs dynamic M(C,t), chart relation vs build order, older strong wording vs v6 ceiling, terrain/operator near axis surfaces vs geometry-on-manifold layer, and live ring-checkerboard readings.
- Confirm binned observables are labeled as implementation bins, and warping/folding/reindexing measured contracts are labeled repo-spec operationalization rather than wiki closure.

Fail condition:

- The build claims wiki support for absent phrases/contracts, smooths over preserved conflicts, treats ring-checkerboard as a settled theorem, omits variant/conflict ledger fields, or reclassifies implementation choices as standing source math.

