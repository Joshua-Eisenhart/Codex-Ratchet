# Layers L9 and up, plus the axes 7-12 engine field

Scope: layer 9 (Axis-0 drive), layer 10 (substrate engines), layer 11
(information/perception), layer 12 (memory), layer 13 (learning), and the
axes 7-12 engine field (Choi-level composition and the G2 numerology probe).
Source tree: `system_v8/axis0_front/`, `system_v8/loop2_world/`,
`system_v8/loop3_senses/`, `system_v8/upper_manifold/`,
`system_v8/exceptional_binding/`, plus the substrate receipts they read
(`system_v8/nested_manifold/`, `system_v8/path_integral/`).

Status ceiling of this dossier: `exists`. It is a documentation compilation,
not a sim. Every "SIM status" cell below reports what the underlying
receipt self-reports, as read this session. None of these sims were rerun
this session, so no cell claims `passes local rerun`. Every source receipt
that gates on it already declares `promotion_allowed: false` and
`formal_admission_allowed: false`; nothing here changes that ceiling.

Column meaning: "Object and formula" is the mathematical object and its
defining expression, quoted or transcribed from the source. "Entropy and
formula" is the entropy or information quantity computed on that object, if
any. "Names" are the descriptive names used in the docs and sims. "Jargon"
is the exact symbol or code identifier a reader will meet in the receipts.
"SIM status (honest)" states classification, `all_pass`, and citation.

---

## Layer 9 — Axis-0 drive

Authority: `system_v8/axis0_front/AXIS0_FRONT_OBJECT_CARD_v0.md`, a
read-only doc-extraction card citing
`system_v7/constraint_core/reference_docs_from_josh/physics_program/JOSHUA_EISENHART_AXIS0_PHYSICS_MODEL_CORE_20260526.md`
section by section. The card's own ceiling is `exists`; it authorises no
sim, no layer, no bridge (card lines 9-16).

| Object and formula | Entropy and formula | Names | Jargon | SIM status (honest) |
|---|---|---|---|---|
| Shell-update Kraus rule (doc §9): `rho_{r-dr}(x) = sum_{h in Omega_r(x)} w_h K_h rho_r(x) K_h^dagger` | `H_Omega(r,x) = -sum_{omega in Omega_r} p_r(omega\|x) log p_r(omega\|x)` (doc §8) | shell-update channel, jk-fuzz compression | `Omega_r`, `w_h`, `K_h`, `rho_present = C({rho_omega})` | `exists` + `runs` (self-reported). Realised on a 3-qubit embedded register, depth-2 Kraus-word enumeration, 5 candidate weight laws. `system_v8/axis0_front/results/r1/receipt.json`, `claim_ceiling`: "scratch_diagnostic / tool_lego_fit_probe ... no physics claim." |
| Counting/Hartley drive, "`S0 = log V`": `dC_t = log\|X_{t+1}\| - log\|X_t\|` (nats) | `dC` is itself a log-cardinality (Hartley) increment; `H_quot = -sum p log p` over `class_counts` is the companion classical entropy | Hartley capacity increment, counting drive, packet-growth drive | `dC`, `G1_counting_dC`, `A_SCHED`, `class_counts`, `total_packets` | `exists` + `runs` (self-reported `all_pass: true`). `system_v8/nested_manifold/results/manifold_one/receipt.json`; also run as one of 10 candidates in `system_v8/axis0_front/results/gradient_tournament_v0/receipt.json`. |
| Unfused Axis-0 vector (doc §24): `A0_raw(r,x) = (Delta_r H_Omega, Delta_r S_B, Delta_r K, log Z_path, order_gap, chirality_sheet, no_message_capacity)` | none fused by design — `Phi0 = projection(A0_raw)`, and doc §24 states "the projection must be discovered, must not be assumed" | pre-projection drive tuple | `A0_raw`, `Phi0`, `Delta_r` | `exists`, partially instantiated. Only 4 of 7 components appear, as proxies, in the `G6_*` candidates of `gradient_tournament_v0.py` (`G6_A0_dC`, `G6_A0_dI_rec`, `G6_A0_unresolved`, `G6_A0_Irec_proxy`); `order_gap`, `chirality_sheet`, `no_message_capacity` are explicitly marked "not computable from this tick data cheaply" in the source and are not built. |

### The section-9 shell-update slot

The doc specifies a structural slot for the drive, not a numeric law: the
drive is meant to enter the history weights `w_h` or the admissible set
`Omega_r`, never a scalar rate multiplier (doc §9: "The state is not one
selected branch. The state is the weighted field of possible
continuations..."). `r1_history_weight_coupling.py` tests this directly: it
builds five candidate `w_h` laws (`W1_capacity`, `W2_surprise`,
`W3_growth`, `W4_uniform`, `W5_scalar_baseline`, where `W5` is the current
v8 stand-in, a scalar GKSL rate `gamma_t = GAMMA_BASE * dC_t / log 4`) and
reports, per candidate, correlation with both classical and quantum-cut
observables plus a shuffled-drive control.

### The OPEN drive-to-quantum coupling (~0.02-0.05), three independent negatives

The front card's own gap ledger (GAP-3) states the doc "does not state a
law by which a change in the possibility drive must move the cut
observables." Three separately-run, separately-authored sims each measure
this coupling and each find it weak, at the same order of magnitude:

1. `system_v8/nested_manifold/results/manifold_one/receipt.json`,
   `data.drive_correlations`: `dH_quot = 0.796` (classical, strong) versus
   `dS_L = 0.0155`, `dS_LR = 0.0188`, `dPhi0 = -0.0359` (quantum cut, weak).
2. `system_v8/axis0_front/results/r1/receipt.json`, `summary`: best
   candidate by cut-coupling is `W3_growth` at
   `rms_cut_correlation = 0.0445`, against the `W5` scalar-baseline's
   `0.0436` — the §9 history-weight mechanism this rung was built to test
   does not clearly beat the scalar-rate stand-in it replaces. A second
   caveat: `W3_growth`'s own shuffled-drive control does not collapse
   (`shuffle_collapsed_for_best: false`; shuffled rms `0.162` exceeds the
   real `0.044`), which is itself an unresolved oddity in the control, not
   only in the effect.
3. `system_v8/axis0_front/results/gradient_tournament_v0/receipt.json`,
   `findings[1]`: "No candidate reaches above-null predictive power on
   quantum-sensitive event proxies (stage transitions) after S_LR control
   ... Sharpens GAP-3." `best_per_event_class.stage_transition` is `null`.

A fourth, partial data point sits alongside these without being a strict
fourth negative of the same kind: the front card's mapping table cites
`system_v8/unified/results/manifold_unified_v1/receipt.json` passing
`l9_drive_quantum_corr_gt_0_3` and `l9_drive_ablation_kills_local_effect`
(`drive_ablation.active_mean = 0.0338`, `ablated_max = 0.0`), with a pooled
`k2_corr = 0.930` that the card flags as "dominated by classical
observables" — the doc's demand to measure `log Z_path` and `I_c`
separately (§16) is only partly honoured there.

### GAP list (from the front card, §6 of that card)

- GAP-1: the weight law `w_h` is undefined by the doc — §8/§9 name the
  slot, not the formula.
- GAP-2: "rising ceiling minus carrier capacity" appears nowhere in the
  source doc (0 grep hits for "ceiling" as a drive mechanism); the nearest
  documented constructs are `H_Omega` growth (§8), capacity growth in the
  open regime (§12), and `area(Sigma_r) ∝ r^2` (§13).
- GAP-3: the coupling from drive into the quantum cut is unspecified (see
  above).
- GAP-4: `Phi0 = projection(A0_raw)` is explicitly undiscovered by owner
  statement (§24).
- GAP-5: the shell-clock functional `i(r) = G(rho_Br)` has seven candidate
  `G`s listed in §7 and no selection among them.

---

## Layer 10 — substrate engines

The layers above and below share three separately-built numerical
substrates. They are not merged into one shared engine object; each is
independently CPTP-certified via its own Choi matrices and cross-checked
against qutip on spot ticks.

| Object and formula | Entropy and formula | Names | Jargon | SIM status (honest) |
|---|---|---|---|---|
| `stage64` 16-channel bank: 4 families x {L,R} x {f+1,f-1}; each a 2-qubit CPTP superoperator `S = (SD @ SU)` or `(SU @ SD)` depending on `f` sign, `theta = kappa * DT * (2*bit-1)`, `L_op = sqrt(GAM0*(1+2*bit)) * kron(sd, I2)` | none intrinsic to the channel; downstream sims compute von Neumann / Choi entropy on states pushed through it | stage channel bank, L-side operating generators | `stage64`, `L_STAGES`, `STAGE_CH[(p,bit)]`, `DT/LAM/GAM0/TD = 0.5/0.7/0.05/0.5`, `k1_commutator_norms` | `exists` + `runs` (self-reported). `system_v8/nested_manifold/results/stage64/receipt.json`; each of 16 channels independently Choi-certified (`choi_min_eigenvalue` in [-5.97e-16, -1.50e-16], `trace_preserving_deviation` in [0, 4.4e-16]). Reused, by the sims' own statement, with "no new parameter tuning," by `engine_processor_v0.py`, `loop2_world/perception_intelligence_v0.py`, `loop3_senses/*`, and `path_integral/planner_v0.py`. |
| `manifold_one` 5-stage tick loop (GROW, PROPAGATE, FLUX, NEST, LOCK): GKSL RK4 integrator (`evolve_tick`, 8 substeps) plus a Schur-eliminated 6-level outer correction (`L_eff = L_II - L_IO @ L_OO^-1 @ L_OI`) | `H_quot` (classical quotient entropy), `S_L`/`S_R`/`S_LR` (von Neumann cut entropies), `negativity` (PPT witness, transiently positive, max `0.000606`) | nested-manifold tick loop, rung-A/B/C composition | `ManifoldState`, `I_rec`, `cond_L_OO`, `M_tick` | `exists` + `runs` (self-reported `all_pass: true`, `K1`-`K7` all true). `system_v8/nested_manifold/results/manifold_one/receipt.json`, `claim_ceiling`: "no new physics claim, no uniqueness/optimality claim." |
| `axis8_field_v0` exact-Liouvillian substrate (torch float64/complex128): 8 base TERR channels (damp/depol/proj x polarity), `S = expm(L * t)` via `torch.linalg.matrix_exp` — an independent numerical route from RK4 | Choi entropy, unitality defect `\|\|C(I) - I\|\|` | engine-field Liouvillian substrate | `TERR`, `dissipator_super`, `liouvillian(ti)`, Choi `J` | `exists` + `runs` (self-reported `verdict: PASS`). `system_v8/upper_manifold/results/axis8_field_v0_results.json`; base recompute `tp_defect_max = 1.14e-15`, `cp_min_eig = 2.33e-5`; 3-pair qutip cross-check agrees on spectrum and entropy. |

---

## Layer 11 — information / perception (occlusion decoupling)

Card authority: `system_v8/spinor_jepa/TOURNAMENT_CARD_v0.md` AMENDMENT
v0.1 (occluded-object perception task) plus
`system_v8/loop3_senses/LOOP3_FOUNDATION_CARD.md` binding correction 1
(fail-closed visibility sanity gate before any carrier scaling).

| Object and formula | Entropy and formula | Names | Jargon | SIM status (honest) |
|---|---|---|---|---|
| World object source: hidden state `(w0 in 0..255, rule in 0..3)`, additive/XOR cellular-automaton family, 6 views, 2-4 occluded positions per view | hidden space `\|HIDDEN_SPACE\| = 1024` (10 bits max) | occluded-object world source | `HIDDEN_SPACE`, `RULE_FAMILY`, `world_source` | `exists` + `runs`, `all_pass: true` (self-reported). `system_v8/loop2_world/results/world_source/receipt.json`. C1 (hidden-state genuinely underdetermined per single view) min consistent count `4`; C2 (joint identifiability) `64/64` objects exactly identified; C4 (dynamics-off differs) flip-rate `0.490` on versus `0.0` off. |
| Occluded-bit prediction: engine (2-qubit `rho_fast`, 15-Pauli readout) vs classical twin (ID3 automaton-feature tree) vs JEPA-proto vs exact Bayes-filter ceiling | belief persistence: Holevo `chi(unprobed bit; register)` | occluded-bit prediction task, loop-1 redundancy retest | `rho_fast`, phi (complementarity), ARI (JEPA cluster check) | `exists` + `runs`, `all_pass: false` (self-reported, red check named). `system_v8/loop2_world/results/intelligence/receipt.json`. Occluded accuracy: engine `0.5364`, twin `0.6006`, JEPA `0.5948`, computed chance `0.4956`, Bayes ceiling `0.8776`. `belief_persistence_holevo_above_permutation_null` is `false` (`0.00428` bits vs null p95 `0.00436`, just under). Complementarity `phi = 0.0298` ("partially independent"), against loop-1's own earlier `phi = 0.756` ("largely redundant") on a task without hidden-state stakes. |
| Occlusion decoupling: `occlusion-free accuracy - occluded accuracy`, per lane | n/a (an accuracy-gap diagnostic, not an entropy) | occlusion decoupling | occlusion-free acc, "the regime where the twin was being held back" | Same receipt, `findings`. Twin: `0.6006 -> 0.9096` (`+0.309`) when occlusion is removed. Engine: `0.5364 -> 0.5131` (`-0.023`, slightly worse without occlusion). The raw two-qubit register's accuracy is close to flat with respect to whether occlusion is present at all; the twin's is not. |
| Visibility sanity gate G1-G5 (fail-closed, LOOP3 binding correction 1): G1 raw-view predictive info, G2 conditional-channel separation, G3 Holevo-chi-above-shuffle, G4 full-visibility Pauli-probe-above-chance, G5 carrier-comparison eligibility only | G3: categorical Holevo `chi(full 8-bit word O; rho_k)` | visibility sanity gate, fail-closed senses gate | `G1`-`G5`, `fix_v1` | `exists` + `runs`. Base run and v1/v2/v3 iterations, `system_v8/loop3_senses/results/visibility_sanity_gate*/`. v1 and v2 each caught a red G3 (v2 also red G4/G5); diagnosis both times: "G3 maps to update," fixed with a 0.5 view-local residual added to the persistent density after each view; `fix_v1` rerun to `all_pass: true` each time. Latest: `visibility_sanity_gate_v3/fix_v1/receipt.json`, `all_pass: true`. |
| `loop2_retest_fixed_senses`: the fixed encoder rerun, before slow memory was added | Holevo `chi` as above | fixed-senses retest | — | `exists` + `runs`, `all_pass: false` (self-reported). `system_v8/loop3_senses/results/loop2_retest_fixed_senses/receipt.json`. Fixed occluded accuracy `0.5131` versus twin `0.6006`; belief persistence `0.003473` bits versus permutation p95 `0.003874` (still below). Finding, verbatim: "the classical twin matches or beats the fixed QIT engine on the held-out occluded task." This result is the direct predecessor to layer 12's `m_slow` register. |

---

## Layer 12 — memory (m_slow belief 0.878)

State definition (`LOOP3_FOUNDATION_CARD.md` binding correction 2):
`Z_t = (rho_fast, m_slow, W_jepa, G_nesting, H_history)` — slow memory must
survive the fast density's reconvergence.

| Object and formula | Entropy and formula | Names | Jargon | SIM status (honest) |
|---|---|---|---|---|
| `m_slow`: normalised posterior over 1024 `(word, rule)` hypotheses, updated only from the quantum-Pauli-readout distance to each hypothesis's candidate emission, never from raw visible bits | `log_posterior += -0.5 * \|\|readout - candidate\|\|^2 / sigma^2`; sigma calibrated label-free from median nearest-neighbour candidate-readout separation; `m_slow_summary` packs bit marginals, rule marginals, normalised entropy, max, effective fraction | quantum-readout-fed Bayesian register, slow memory | `m_slow`, `QuantumReadoutBayes`, `sigma` | `exists` + `runs`, `all_pass: false` (self-reported, one red check named). `system_v8/loop3_senses/results/senses_v2_slow_memory/receipt.json`; `classification: scratch_diagnostic`, `promotion_status: diagnostic_only`, `accepted_status_label: exists`. |
| Headline result: `m_slow` occluded-bit accuracy | belief-persistence mutual information `I(O; m_slow)` | m_slow occluded-bit accuracy | `occluded_accuracy`, `belief_persistence_mutual_information_bits` | Same receipt. `occluded_accuracy = 0.8775510204081632` (≈0.878), CI95 `[0.850, 0.905]` (5000-draw object bootstrap) — above twin (`0.6006`), chance (`0.4956`), and a same-architecture slow-reset ablation (`0.6327`, `m_slow` reset to uniform every view). `I(O; m_slow) = 0.6768` bits versus permutation-null p95 `0.0862` bits (about 8x). |
| Honest negative: the deliberately-unmasked leak sentinel | `sentinel_slow_changed_count` versus `sentinel_changed_count` | leak-sentinel control | `positive_unmask_sentinel_*` | Leaking one target bit changes `rho_fast` and the joint feature on `343/343` test slots, but changes `m_slow` itself on only `123/343`. The receipt's own fail-closed check `deliberately_unmasked_leak_sentinel_changes_fast_and_slow` is `false` — this is the specific red check behind `all_pass: false` above. |
| `carrier_tournament_v1`: 5-lane comparison against a preregistered frozen falsifier | — | carrier tournament, frozen falsifier | `oracle_exact_filter`, `classical_fst_hmm`, `torch_gru`, `senses_v2_anchor`, `product_single_qubit_per_stage` | `exists` + `runs`, `all_pass: true` on the sim's own integrity/fairness/scientific checks (self-reported) — but that `all_pass` covers the diagnostic running cleanly, not the substantive carrier claim. `system_v8/loop3_senses/results/carrier_tournament_v1/receipt.json`. Occluded accuracy: oracle `0.866`, `classical_fst_hmm` `0.840`, `torch_gru` `0.542`, `senses_v2_anchor` (the layer-12 quantum register) `0.878`, product-qubit control `0.475` (≈ chance `0.496`). Falsifier rule: "if a fair matched classical sequential lane matches or beats the anchor within paired object-bootstrap CI, the quantum carrier has not earned minimal status." Neither classical lane does (`classical_fst_hmm` paired diff `+0.038`, CI `[0.009, 0.066]`, excludes zero; `torch_gru` diff `+0.335`) — the falsifier does not trigger — and the tournament's verdict is still `minimal_status_earned: false`, `status: WORKING_SIM_CARRIER_RESULT_ONLY`. A first attempt (`carrier_tournament_v1_attempt1_fatal/receipt.json`) failed outright: `TournamentError: product lane produced a nonphysical qubit`. |

---

## Layer 13 — learning (planner)

| Object and formula | Entropy and formula | Names | Jargon | SIM status (honest) |
|---|---|---|---|---|
| Finite path-integral min-`G` planner: paths = enumerated admitted probe-order words (exact permutations when `\|visible\| <= 6`, else length-`r` samples up to 4096); `G(pi) = sum_t S(rho_t \|\| goal)`; select `argmin G` | Umegaki relative entropy `S(rho\|\|sigma) = Tr[rho (log rho - log sigma)]`, bits | finite path-integral planner, min-G order selection | `G(pi)`, `umegaki_bits`, `admitted_words`, `canonical_goal_rho` | `exists` + `runs`, `promotion_allowed: false`. `system_v8/path_integral/results/planner_v0/receipt.json` and `results/planner_v1/receipt.json` (script `planner_v1_harder.py`). |
| Three-way comparator: min-`G` planner vs MCTS (`mctx`, Gumbel MuZero, 64 simulations, information-gain objective) vs random probe order (50 draws) | information gain = posterior entropy drop | planner vs MCTS vs random, ceiling gate | `mctx`, `R_FOR_WORDS`, `TASK_STILL_EASY` | v0: all three arms `acc_mean = 1.0` over 20 episodes (`ig_mean ~ 5e-35`) — a ceiling effect, no discrimination possible. v1 ("harder" world: 128 objects, 14-bit hidden state, 8 views, 4-6 bits occluded/view, `R_FOR_WORDS = 2` = 60% of v0's probe budget): still all three arms `acc_mean = 1.0`; a preregistered `ceiling_gate` (threshold `0.95`) fired and the receipt's own verdict is `TASK_STILL_EASY`, honestly, rather than a discrimination claim. |
| Order-sensitivity witness: fraction of admitted words with `G(forward) != G(reversed)` | — | path-order sensitivity | `v8_fraction_G_fwd_neq_rev`, `v1_fraction_G_fwd_neq_rev` | Genuine positive, both runs. v0: `6624/6624` words differ (`100%`). v1: `1282/1420` differ (`90.3%`), consistent in order of magnitude with the "v7 reported 240/256" figure (`93.75%`) the script cites for comparison. Controls behave as required in both runs: a commuting-generator control collapses order-sensitivity to exactly `0.0`; a uniform-weight-`G` control matches the random arm within `0.05`. |
| Process caveat on the v1 receipt | — | verifier note | — | `system_v8/path_integral/results/planner_v1/VERIFIER_NOTE.md` flags that an earlier v1 draft did not enforce the 60%-probe-budget premise inside the accuracy metric itself, alongside the ceiling-gate firing. This session's reading of `planner_v1_harder.py` finds `R_FOR_WORDS = 2` threaded into the word-admission calls the three-way comparison uses — but this was not independently rerun this session, so whether the receipt on disk is the corrected run or the flagged one is not settled by reading alone. Stated honestly rather than resolved either way. |

---

## Field 7-12 — the Choi composition field, and the G2 numerology probe

`system_v8/upper_manifold/axis8_field_v0.py` extends
`system_v7/.../upper_manifold_mirror_axes_field_sim.py` axis 7 (engines as
objects, read on Choi matrices) into axis 8: whether the *relation*
between engine-objects — channel composition `C_i . C_j` — is itself
load-bearing.

| Object and formula | Entropy and formula | Names | Jargon | SIM status (honest) |
|---|---|---|---|---|
| Base 8-channel mirror recompute (axis 7): 8 TERR channels, clustered by `(unitality_defect, choi_entropy, PPT)` | Choi entropy `-sum w log2 w` on normalised Choi eigenvalues | engine-as-object mirror | `TERR`, base kind clusters | `exists` + `runs`, self-reported `verdict: PASS`. 3 base kinds recovered (damp: 4 members, depol: 2, proj: 2), matching the seed's TERR partition; CPTP valid (`tp_defect_max = 1.14e-15`, `cp_min_eig = 2.33e-5`); identity control exact (`max gap 0.0`). |
| 64 ordered compositions `C_i . C_j` (axis 8 = relations between engine-objects) | non-commutation witness: `order_gap(i,j) = \|\|Choi(C_i.C_j) - Choi(C_j.C_i)\|\|_F` over 28 unordered pairs | axis-8 relations, engine-field composition test | `order_gap`, `Spearman(gen_comm, order_gap)` | `exists` + `runs`. All 64 compositions CPTP-valid. `order_gap` ranges `[0.0724, 0.9431]`, mean `0.470`, `order_blind: false` — composition is order-sensitive under this generator family. `Spearman(generator-commutator norm, order gap) = 0.573`; `0` near-commuting generator pairs were found below `1e-6`, so this correlation is not validated at the near-zero edge case. |
| Kind classification of the 64 compositions against the 3 base clusters | same `(unitality_defect, choi_entropy, PPT)` invariant tuple, tolerance-clustered | new-kind clusters | `n_new_kind_clusters` | `0/64` compositions stay inside a base kind; `64/64` are new-kind instances, tolerance-clustering into `14` new kind clusters (member counts from 2 to 12). 3-pair qutip cross-check agrees on spectrum and entropy. `system_v8/upper_manifold/results/axis8_field_v0_results.json`. |
| G2 axes-binding numerology test: `Der(O)` solved as the exact null space of the Leibniz constraint on octonion structure constants (14-dimensional, matching `g2`), tested for orbit-alignment with the manifold's own 7-axis stage partitions | orbit-alignment score `= mean(same-class alignment) - mean(cross-class alignment)`, not an entropy | G2 axes-binding numerology test | `Der(O)`, orbit-alignment score, `g2_percentile_vs_controls` | `exists` + `runs`, `classification: tool_lego_fit_probe`, `promotion_allowed: false`, mechanical `all_pass: true`. `system_v8/exceptional_binding/results/g2_axes_binding_v0_receipt.json`. Verdict: `NUMEROLOGY_NOT_REJECTED_AS_SUCH` (`g2_percentile_vs_controls = 65.0`, against a preregistered 95th-percentile bar for the positive verdict). The scrambled-axis-identity control scores `-0.0233`, essentially level with the real G2 score `-0.0256` and not below it — undermining even the weak reading, since scrambling which axis is which barely moved the result. `F4` / Choi-level axes 7-12 are explicitly out of scope for this v0 (own text: "F4 / Choi-level axes 7-12 explicitly OUT OF SCOPE for v0; follow-up only"). |

---

## Honest OPEN items (owner-facing)

1. **Drive-to-quantum coupling (GAP-3) — OPEN.** Three independently
   authored sims each measure the Axis-0 drive against quantum cut
   observables and each land at the same weak order of magnitude,
   `~0.02-0.05`, versus a strong classical coupling (`~0.8`) on the same
   trajectories:
   - `system_v8/nested_manifold/results/manifold_one/receipt.json` —
     `dS_L=0.0155, dS_LR=0.0188, dPhi0=-0.0359` vs `dH_quot=0.796`.
   - `system_v8/axis0_front/results/r1/receipt.json` — best candidate
     `rms_cut_correlation=0.0445` vs scalar-baseline `0.0436` (no clear
     separation), and that candidate's own shuffle control does not
     collapse.
   - `system_v8/axis0_front/results/gradient_tournament_v0/receipt.json`
     — no candidate beats scalar entropy above-null on the
     quantum-sensitive `stage_transition` event class.
   The doc specifies the structural slot (§9: drive enters `w_h`/`Omega_r`)
   but not the numeric law, and the front card is explicit that this is a
   research target, not a bug: GAP-1 (weight law undefined) and GAP-2
   ("ceiling minus capacity" is not in the source doc) sit directly
   upstream of GAP-3.

2. **Phi0 projection (GAP-4) — OPEN by the owner's own doc statement.**
   `system_v8/axis0_front/AXIS0_FRONT_OBJECT_CARD_v0.md` §24, quoting the
   source doc directly: "`Phi0 = projection(A0_raw)`. The projection must
   be discovered. It must not be assumed." No sim in this tree closes this;
   `A0_raw`'s 7-tuple is only 4/7 instantiated, as proxies, in
   `gradient_tournament_v0.py`'s `G6_*` candidates, and the doc itself
   states no final Phi0 theorem is closed (§23).

3. **G2 numerology — NOT rejected, but not confirmed either.**
   `system_v8/exceptional_binding/results/g2_axes_binding_v0_receipt.json`:
   preregistered rule was `G2_ORGANIZES_AXES_CANDIDATE` if
   `g2_percentile_vs_controls >= 95.0`, else
   `NUMEROLOGY_NOT_REJECTED_AS_SUCH`. The run landed at `65.0` — inside the
   random-control band, not near the bar — and the scrambled-axis-identity
   control (`-0.0233`) is not below the real G2 score (`-0.0256`), which
   weakens the weak reading further: scrambling which manifold axis maps
   to which octonion basis vector barely changed the alignment score. The
   owner's own epistemic label on the hypothesis, quoted in the receipt:
   "the numbers just match and that is about it." `F4` / axes 7-12 at the
   Choi level are explicitly out of scope for this v0 — so the "axes 7-12"
   half of the owner's hypothesis has not been tested at all yet, in
   either direction.

Two further honest negatives sit close to these three and are surfaced in
full above, not just here: the layer-12 leak-sentinel control shows `m_slow`
moves on only `123/343` test slots when the target bit is deliberately
unmasked (`system_v8/loop3_senses/results/senses_v2_slow_memory/receipt.json`,
the specific red check behind that receipt's `all_pass: false`); and the
layer-13 planner comparator hit a ceiling effect on both the original and
the "harder" world (`system_v8/path_integral/results/planner_v0/` and
`results/planner_v1/`), so no planner-vs-MCTS-vs-random discrimination
claim is earned even though the order-sensitivity machinery underneath it
checks out.
