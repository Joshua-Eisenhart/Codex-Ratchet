# Fresh audit verdict: compression_flow_radiated_record_v0

Verdict: GENUINE-WITH-CAVEATS.

Ceiling restated: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. Status language admitted here: first finite compression-flow/radiated-record packet. No canonical, formal-admission, QIT-separation, axis, bridge, or physics claim is admitted.

Audit stance: I did not build this sim. Builder self-checks were not treated as evidence. I read the checklist `/tmp/cfr_pre_audit_checklist_20260610.md`, the build card, sources, result JSONs, blind card, mine receipt, MCT carrier artifacts, and reran independent recomputation for the minimum packet. Repo files were left read-only except this verdict.

## Commands and fresh checks

- Build card byte compare: `cmp -s /tmp/cfr_build_card_20260610.md system_v6/sims/compression_flow_radiated_record_v0/build_card.md` returned `0`.
- Envelope validator: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/compression_flow_radiated_record_v0/results/compression_flow_radiated_record_v0_envelope_results.json --require-pytorch` returned `{"ok": true, ...}`.
- `/tmp/cfr_advisory_crosscheck_20260610.md` was checked for F1 and was absent at audit time.
- Manual recompute was done with a fresh Python packet reading the JSON/source artifacts only. Fresh SMT rerun used z3 and cvc5 from the sim-stack interpreter.

## Per-check results

1. Build-card copy, ceiling, candidate-math fence: PASS. The emitted build card byte-matches `/tmp/cfr_build_card_20260610.md`; the card fences exact conservation/reconstruction as candidate math and pins the ceiling. Result files carry `scratch_diagnostic/false/false`; candidate-math labels are present. Evidence: `build_card.md:3`, `build_card.md:14`, `jax_results.json:112-120`, `jax_results.json:227`, `jax_results.json:356`, `envelope_results.json:128`, `envelope_results.json:418`, `envelope_results.json:482`.

2. Carrier lineage and 384-row support reuse: PASS. CFR points at MCT carrier lineage `f64f2c...` and support hash `5727f...`; MCT PIN hash recomputed from `pin_block_canonical_json` equals `f64f2c...`; MCT support hash recomputed from `state_id|psi` canonical lines equals `5727f...`. Manual count: `2*3*8*8=384`. Row `L:eta0:phi0:chi0` recomputed with norm `0.9999999999994014`, `rho00=0.8535533905927438`, matching emitted `rho00=0.853553390593` within rounding. Evidence: `jax_results.json:4-24`, `mct_dynamic_admissibility_packet_v0_jax.py:48-69`, `mct_dynamic_admissibility_packet_v0_jax.py:155`, `mct_dynamic_admissibility_packet_v0_jax.py:315-329`, `mct_dynamic_admissibility_packet_v0_julia_results.json:13490`, `mct_dynamic_admissibility_packet_v0_julia_results.json:14094`.

3. Exclusion predicates and predicate-gaming controls: PASS with G7 caveat below. Pinned predicates are computed probe-row predicates: `P_density[0] >= 2`, `P_shell != 2`, and `P_phase in {0,1,2,3}`. Original-carrier exclusion counts: 96, 128, 192; each is nonempty proper. Original-carrier exclusion overlaps: c0&c1=32, c0&c2=48, c1&c2=64, triple=16, so the predicates are not disjoint. Trivial predicate control excluded 0 and was flagged. Evidence: `jax_results.json:45-69`, `compression_flow_radiated_record_v0_jax.py:134-143`, `jax_results.json:152-158`.

4. Full cardinality ledger: PASS. Fresh ledger: step 0 `384=288+96`, step 1 `288=192+96`, step 2 `192=96+96`; every defect is 0 and set partition checks held. Telescoping: `384 = P_T 96 + emitted 288`. Injected defect was caught as `1`. Evidence: `jax_results.json:381-417`, `jax_results.json:3046-3055`, `jax_results.json:126-130`.

5. One raw reconstruction by hand: PASS, but by-construction. Fresh set union `P_T union raw_record` reconstructed 384 rows with mismatch 0. Checked final sample `L:eta0:phi0:chi0` and record sample `L:eta2:phi0:chi0` against the carrier row table. Evidence: `jax_results.json:371-377`, `jax_results.json:3046-3055`.

6. Triviality defense A, SMT uniqueness: PARTIAL/EARNED-NARROW. Fresh z3 and cvc5 rerun: full raw record UNSAT; dropped-record control after 42 dropped rows SAT in both solvers; model sample includes omitted row IDs such as `L:eta0:phi0:chi2`, `L:eta1:phi0:chi5`. This is a real row-set coverage flip. Caveat: the solver variables are booleans over row IDs from `all_ids`, and the assertions do not bind canonical row payload hashes inside the solver; the proof is not a payload-level computed-row uniqueness proof. Evidence: `compression_flow_radiated_record_v0_jax.py:452-535`, `jax_results.json:160-224`.

7. Triviality defense B, quotient-mode killed-information ledger: PASS. Fresh quotient-class expansion by class representatives gives raw mismatch 48 and quotient-level mismatch 0. Example class `[2,0,2]`: class size 32, emitted 16, final 16; representative expansion misses 8 raw rows in that class. Killed ledger reports `288 * ln(32) = 998.1319400063212` nats. Evidence: `compression_flow_radiated_record_v0_jax.py:281-313`, `jax_results.json:360-369`, `jax_results.json:3046-3055`.

8. Triviality defense C, erasure and lossy variants: PASS on failure behavior, GAP on charge semantics. Erasure mismatch 288; lossy counts-only mismatch 288; internal erasure ledger does not balance without environment charge. Evidence: `jax_results.json:122-125`, `jax_results.json:142-145`, `jax_results.json:3057-3096`. F1 below names the charge semantics gap.

9. Decorative SMT and solver-proof integrity: PARTIAL. z3 and cvc5 are separately invoked and both polarity checks reran correctly. However, the formulas are simple boolean row-presence formulas over row IDs, not constraints over canonical row payloads/hashes. Treat SMT as earned for finite row-set coverage and dropped-row ambiguity, not as a strong computed-payload proof. Evidence: `compression_flow_radiated_record_v0_jax.py:452-535`.

10. Entropy and ledger-theater check: PASS for named finite-set entropy and conservation arithmetic. `H_live` and `H_record` are named base-e class-distribution entropies under `P_density`; fresh step-0 initial `H_live` matches `ln(12) = 2.484906649788...` as the blind card predicted. Injected violation changes the defect to 1. Erasure charge arithmetic is internally consistent but semantically underpinned; see F1. Evidence: `jax_results.json:26-30`, `jax_results.json:381-417`, `jax_results.json:3057-3090`.

11. Append-only record and hash-chain immutability: PASS for recomputation. Fresh recompute of raw step-0 hash from previous zero hash and 96 entry hashes produced `41d0113914c03390eac69b7e6ba7763d439dd275e981458bb90b5b4eef14e3ff`, matching stored. Quotient step-0 recompute produced `22d97485094a781527dda966bd110ce152d574e071e536d63f33ecf127772f73`, matching stored. Evidence: `compression_flow_radiated_record_v0_jax.py:183-203`, `jax_results.json:381-417`.

12. Record-shuffle and order-sensitivity: PASS, not vacuous. Source checks predicate/step consistency; recorded shuffle changes from 0 to 192 errors. My independent shifted-tag recompute gave 400 errors because it used a harsher deterministic tag shift, but it confirms order tags are load-bearing rather than ignored. Because original exclusion predicates overlap, the blind-lane disjointness warning does not kill G7. Evidence: `/tmp/cfr_blind_expected_20260610.md:280-320`, `compression_flow_radiated_record_v0_jax.py:383-424`, `jax_results.json:146-151`.

13. Boundary-engine language and erasure-baseline framing: PASS with F1 caveat. Build card calls erasure a classical boundary baseline, not a mere failing control, and result variant is named `erasure_boundary_baseline`. No promoted QIT-separation/axis/bridge/physics language appears except explicit negative fences/disallowed-claim strings. Evidence: `build_card.md:14`, `build_card.md:28`, `jax_results.json:3057-3090`.

14. Cross-leg independence and parity-by-copy: CAVEAT. JSON records `reads_peer_result=false` across legs and shared values match. But PyTorch source imports the JAX core and calls `core.build_result()`, then adds a real `torch_geometric` DAG receipt. This is not a pure peer-result read, but it means PyTorch is mostly a wrapper over the JAX computation path. Treat PyTorch as load-bearing only for the append-only DAG/graph check, not independent evidence for ledger/reconstruction/SMT values. Evidence: `envelope_results.json:376`, `envelope_results.json:393`, `envelope_results.json:412`, `compression_flow_radiated_record_v0_pytorch.py:12-16`, `compression_flow_radiated_record_v0_pytorch.py:28-116`.

15. NumPy leakage and control-lane boundary: PASS for this packet. The JAX leg uses `jax.numpy` for entropy/masks; PyTorch uses torch/torch_geometric for graph receipt; no NumPy-only claim path was found in CFR source. Evidence: `jax_results.json:85-101`, `pytorch.py:12-13`, `pytorch.py:55-77`.

16. Source provenance and cited-source discipline: PASS. The build card and result labels preserve the doctrine/math split: owner shell/radiation wording is sourced, exact conservation/reconstruction remain candidate math and not standing doctrine. Evidence: `build_card.md:3`, `build_card.md:14`, `jax_results.json:112-115`.

17. Envelope validator and gate-to-field traceability: PASS with independence caveat. Fresh validator returned `ok:true`; every G1-G8 gate is present and true in envelope, controls fired, shared values match. This validates schema/field presence, not the stronger semantics called out in F1 and the PyTorch/SMT caveats. Evidence: validator command above, `envelope_results.json:528-572`.

18. Minimum manual recomputation packet: PASS with named caveats. Manual packet included full ledger, one carrier row, raw reconstruction, quotient 48 mismatch, one erasure arithmetic line, hash-chain step, fresh z3/cvc5 full UNSAT and dropped SAT model. Caveats: erasure register basis is underpinned; SMT proof is row-set coverage, not payload-hash proof.

## F1. Erasure-charge adjudication

Observed builder charge:

```text
288 * ln(384) = 1713.7850551452655 nats
```

This exactly matches source code charging `total_erased_rows * log2(len(all_ids)) * ln2`, i.e. one 384-state row-ID register per erased row. Evidence: `compression_flow_radiated_record_v0_jax.py:335-371`, `jax_results.json:3057-3061`.

Alternative requested by overseer, using remaining live-set size after each step:

```text
96 * ln(288) + 96 * ln(192) + 96 * ln(96)
= 1486.54118818863 nats
```

Other useful comparator, using pre-step live set:

```text
96 * ln(384) + 96 * ln(288) + 96 * ln(192)
= 1619.6254468561397 nats
```

Blind-card row-register expectation, using emitted-step cardinality:

```text
ln(96) + ln(96) + ln(96)
= 13.693044574403508 nats
```

Decision: arithmetic is correct for a full-support identity register, but the build does not explicitly pin that register basis strongly enough. `record_register_policy="reset_each_step_content_destroyed"` says content is reset; it does not by itself settle whether the erased register state space is full support, current live set, remaining live set, or emitted-step register. This is an additive hardening gap, not a break in the finite set ledger. Required hardening: add an explicit `erasure_register_basis` field and report at least `full_support_identity`, `remaining_live_after_step`, and `emitted_step_register` comparator charges.

## F2. Predicate overlap and G7 adjudication

Pinned predicates:

- `c0_density_x_bin_ge_2`: keep `P_density[0] >= 2`.
- `c1_shell_not_outer_eta`: keep `P_shell != 2`.
- `c2_phase_lower_half`: keep `P_phase in {0,1,2,3}`.

Original-carrier exclusion counts:

```text
c0 excludes 96 / keeps 288
c1 excludes 128 / keeps 256
c2 excludes 192 / keeps 192
c0&c1 overlap 32
c0&c2 overlap 48
c1&c2 overlap 64
triple overlap 16
```

Decision: G7 is load-bearing on this pin. The three exclusion predicates are not effectively disjoint, and step tags are checked against first-hit predicate consistency. The control is not just raw unordered set reconstruction.

## F3. Triviality adjudication

Earned:

- Quotient-mode failure is real: raw mismatch 48, quotient-level mismatch 0, with arithmetic from class representatives and density-class counts.
- Erasure/lossy failure is real: both mismatch 288; erasure internal ledger has 96 defect at each step without environment charge.
- Injected conservation violation is real: defect 1 is caught.
- Raw reconstruction succeeds, but this is decorative/by-construction unless paired with the above defenses.

Earned but narrow:

- SMT full-record UNSAT and dropped-record SAT flip are real and freshly rerun with z3/cvc5. The exhibited SAT model is genuine for omitted row IDs.
- The solver proof is only row-set coverage over boolean row IDs. It is not yet a strong proof over canonical row payloads or payload hashes.

Decorative or overstated:

- Treating PyTorch agreement as an independent third computation for all shared ledger/proof values is overstated. PyTorch adds a real DAG check, but the core values are produced by the imported JAX core.
- Treating the 1713.785 nats charge as semantically settled is overstated until the register basis is pinned.

## Named gaps

1. Erasure register basis is underpinned. Add explicit register semantics plus comparator charge fields.
2. SMT proof does not bind canonical row payloads/hashes. Add payload-hash variables or assertions tying observed IDs to canonical row digests.
3. PyTorch is mostly a JAX-core wrapper. Either mark PyTorch as graph-only for this packet or build a separate PyTorch flow/record computation path for the shared scalar fields.
4. Support hash recomputation depends on MCT's fixed `state_id|psi` line serialization. This is documented in MCT source, but CFR audit surfaces should cite that serialization when claiming carrier hash recomputation.

## Final verdict

GENUINE-WITH-CAVEATS.

The packet genuinely computes a finite 384-row compression-flow/radiated-record diagnostic with exact cardinality conservation, append-only hash-chain recomputation, raw reconstruction, quotient-mode information loss, erasure/lossy failures, and a real dropped-record SAT flip. It is not decorative. It is not promoted. The caveats are bounded and hardening-ready: register-basis semantics, payload-bound SMT, and PyTorch independence.

## Post-Hardening Re-Audit Addendum -- 2026-06-09 PDT

Scope: focused re-audit of the four named-gap closures above. I did not build, audit, or harden this sim. I recomputed the requested checks from source/result artifacts and appended this addendum only; the original verdict text above remains historical.

### Gap 1 -- register basis and charge semantics: CLOSED

Evidence: the envelope pins `erasure_register_basis` to `full_support_identity` for `jax`, `julia`, and `pytorch` (`results/compression_flow_radiated_record_v0_envelope_results.json:449-453`). The source computes and emits all comparator charges in the JAX leg (`compression_flow_radiated_record_v0_jax.py:371-419`) and PyTorch leg (`compression_flow_radiated_record_v0_pytorch.py:376-423`), and the result keeps all three engines byte-equal for the comparator values (`results/compression_flow_radiated_record_v0_envelope_results.json:1001-1021`). The result also states `charge_adjudication: named alternatives preserved; no comparator is promoted as the charge` and labels the headline as `erasure_register_basis=full_support_identity` (`results/compression_flow_radiated_record_v0_envelope_results.json:1077-1107`). The advisory crosscheck is cited as `/tmp/cfr_advisory_crosscheck_20260610.md#D1` (`results/compression_flow_radiated_record_v0_envelope_results.json:1100`).

Hand recompute:

```text
full_support_identity: 288 * ln(384) = 1713.7850551452655 by the source formula 288 * log2(384) * ln2
remaining_live_after_step: 96*ln(288)+96*ln(192)+96*ln(96) = 1486.54118818863
pre_step_live: 96*ln(384)+96*ln(288)+96*ln(192) = 1619.6254468561397
emitted_step_register: 3*ln(96) = 13.693044574403508
```

Note: direct Python `288*math.log(384)` prints `1713.7850551452652`; the emitted/source formula `288*math.log2(384)*ln2` prints `1713.7850551452655`. This is floating evaluation order, not a semantic or arithmetic mismatch.

### Gap 2 -- payload-bound SMT: CLOSED

Evidence: the old row-set proof is retained under `proof_rowset_coverage` in the envelope (`compression_flow_radiated_record_v0_envelope.py:203`) and the leg sources still expose row-set `z3_uniqueness` separately (`compression_flow_radiated_record_v0_jax.py:505-530`, `compression_flow_radiated_record_v0_pytorch.py:509-534`). The new payload-bound proof is not a renamed row-ID boolean check: each observed row asserts presence plus `digest_by_id[state_id] == payload_code[state_id]`, where payload digest is `sha256(canonical_json({state_id,support,probe}))` and the integer code is the first 15 hex digits (`compression_flow_radiated_record_v0_jax.py:67-76`, `compression_flow_radiated_record_v0_jax.py:533-583`; PyTorch mirror `compression_flow_radiated_record_v0_pytorch.py:68-77`, `compression_flow_radiated_record_v0_pytorch.py:537-587`). cvc5 has the same payload-bound structure (`compression_flow_radiated_record_v0_pytorch.py:627-682`).

Fresh z3 rerun from source using the sim-stack interpreter:

```text
payload full record: UNSAT, observed_rows_bound=384
payload dropped record: SAT, observed_rows_bound=342
exhibited dropped model sample: L:eta0:phi0:chi2, L:eta0:phi1:chi4, L:eta0:phi3:chi4, L:eta0:phi3:chi6, L:eta0:phi6:chi0, L:eta0:phi7:chi2, L:eta1:phi0:chi5, L:eta1:phi2:chi5
payload digest sample includes L:eta0:phi0:chi0 -> 0c6c862049d7dc7b448d6667c012f7c772ccd4773900e8be957d02de9c8f036e
```

The envelope reports the same z3/cvc5 payload flip with payload digest samples (`results/compression_flow_radiated_record_v0_envelope_results.json:520-715`).

### Gap 3 -- PyTorch independence: CLOSED

Evidence: PyTorch imports `cvc5`, `torch`, `torch_geometric.utils.degree`, and `z3`; there is no JAX-core import (`compression_flow_radiated_record_v0_pytorch.py:14-18`). A static grep for `import .*jax`, `from .*jax`, `compression_flow_radiated_record_v0_jax`, `core.build_result`, and `jax_core` in the PyTorch source found only the emitted `imports_jax_core: False` receipt line. The source computes predicate masks with torch tensors (`compression_flow_radiated_record_v0_pytorch.py:150-162`), builds live/emitted/survivor ledgers through torch index tensors (`compression_flow_radiated_record_v0_pytorch.py:232-302`), computes erasure/comparator scalars locally (`compression_flow_radiated_record_v0_pytorch.py:360-424`), and records the independence receipt (`compression_flow_radiated_record_v0_pytorch.py:960-978`; result lines `results/compression_flow_radiated_record_v0_pytorch_results.json:706-724`).

Fresh PyTorch recompute of the first ledger step from source:

```text
step=0
predicate_id=c0_density_x_bin_ge_2
P_t_size=384
P_t_plus_1_size=288
Delta_R_t_size=96
cardinality_defect=0
conservation_pass=true
```

The torch mask receipt recomputed `96 -> 288`, `96 -> 192`, `96 -> 96` for the three steps, and the raw hash-chain heads recomputed as `41d0113914c03390eac69b7e6ba7763d439dd275e981458bb90b5b4eef14e3ff`, `f78beccf9623dd94a9316e03132616bb250e85ee5b0186e02b356db207138b47`, `20d5517a287c8f351a396e4001927cf8a9b789029788c6c4a6ff1a5ce15c8961`.

### Gap 4 -- carrier-hash citation: CLOSED

Evidence: the CFR envelope includes `carrier_support_hash_recomputation_citation` for all three engines (`compression_flow_radiated_record_v0_envelope.py:187-191`). The JAX citation names `system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_jax.py`, line range `315-329`, and serialization `state_id|psi0_real|psi0_imag|psi1_real|psi1_imag, joined with newlines plus final newline` (`results/compression_flow_radiated_record_v0_envelope_results.json:120-136`). The cited MCT JAX source actually appends those fields and hashes `"\n".join(canonical_lines) + "\n"` (`system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_jax.py:315-329`). The PyTorch MCT citation likewise points to `382-396`, where the same serialization is built and hashed (`system_v6/sims/mct_dynamic_admissibility_packet_v0/mct_dynamic_admissibility_packet_v0_pytorch.py:382-396`).

### Byte-stability and validator

The nine audited claim values remain unchanged and identical across all three engines: `support_size=384`, `P_T_size=96`, `total_emitted_rows=288`, `raw_reconstruction_mismatch_count=0`, `quotient_raw_reconstruction_mismatch_count=48`, `quotient_level_mismatch_count=0`, `max_conservation_defect=0`, `injected_conservation_defect=1`, `erasure_environment_charge_nats=1713.7850551452655` (`results/compression_flow_radiated_record_v0_envelope_results.json:1023-1068`). The per-step raw ledger recomputed from JAX and PyTorch source is still `384 -> 288 + 96`, `288 -> 192 + 96`, `192 -> 96 + 96`, with zero defect at each step. The hash-chain heads are unchanged: raw `41d0113914c03390eac69b7e6ba7763d439dd275e981458bb90b5b4eef14e3ff`, `f78beccf9623dd94a9316e03132616bb250e85ee5b0186e02b356db207138b47`, `20d5517a287c8f351a396e4001927cf8a9b789029788c6c4a6ff1a5ce15c8961`; quotient `22d97485094a781527dda966bd110ce152d574e071e536d63f33ecf127772f73`, `47568442b576625e2aad3a92283d5ed9436c2cc3e40d88c54cfdbb977287d06a`, `03269d23d26369cfcc41bf50a0735c7862505adf9a861945399ddc34ce3e65de`.

Fresh command:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/compression_flow_radiated_record_v0/results/compression_flow_radiated_record_v0_envelope_results.json --require-pytorch
```

Result: `{"ok": true, "result_json": "system_v6/sims/compression_flow_radiated_record_v0/results/compression_flow_radiated_record_v0_envelope_results.json"}`.

Runtime doctor also returned `ok=True install_state=stable_observed` for `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`.

### Stale-surface check

Searches for stale hardening-gap language found no current source/result field implying the gaps remain open. The only remaining open-gap wording is the original historical verdict above this addendum, which is intentionally preserved append-only. Current result/source surfaces pin the register basis, bind payload digests in SMT, remove the PyTorch JAX-core wrapper, and cite the MCT `state_id|psi` serialization.

GENUINE-WITH-CAVEATS sustained. Ceiling restated: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`; candidate-math labels remain intact; admitted status language remains "first finite compression-flow/radiated-record packet"; no canonical, formal-admission, QIT-separation, axis, bridge, or physics claim is admitted.
