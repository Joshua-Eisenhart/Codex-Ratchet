# Deep adversarial blind re-audit — overclaim ledger (2026-06-13)

```yaml
receipt_kind: deep_adversarial_reaudit_ledger
mandate: owner "presume the system is lying and hallucinating; find ways to improve"
method: blind re-audit of EVERY committed audit-claimed packet; codex2 (mass, all-effort, BINDING arbiter) finds true ceiling; perspective-diverse non-codex second-opinion (grok-4.3 / gemini-3.1-pro / gemini-3.5-flash / deepseek-v4-pro / qwen3.7-max) on flagged+heavy; fresh-context collapse-audit synthesis (shared-premise + anti-collapse check)
scale: 221 enumerated / 219 audited / 196 flagged overclaim / ~17 clean ; 425 agents, 34.2M tokens, ~3.9h
unaudited: geo_s1_spinor_hopf_free_v0, geo_s5_terrain_flows_v0 (API socket errors — re-run pending)
status: ADVISORY-VIEWS-FOLDED-INTO-CODEX2-BINDING. codex2 is the sole trusted arbiter (trust rule); seconds are independent lenses; dispute rate ~6/120, all low-stakes label-severity, ZERO mechanism disagreements.
```

## BOTTOM LINE (the nuanced, important result)

The system was **mostly honest at the CEILING LABEL** — the packets' own `classification=scratch_diagnostic` / `promotion_allowed=false` fields are HONEST and the overclaims **almost never break the ceiling**. The overclaim lives in **`audit_verdict.md` PROSE or an ADDENDUM that UPGRADES a correctly-narrowed verdict**, and in two systemic diseases that inflate the **EVIDENCE GRADE inside** that honest ceiling:

1. **"three independent engines agree / max_divergence=0.0"** = **1 independent engine (Julia) + 2 Python legs sharing that packet's own `build_packet()`**. NOT one global builder (each packet ships its own `_envelope.py`) — a recurring DESIGN IDIOM re-instantiated ~45× (40/159 JAX legs verified). The JAX/PyTorch agreement is guaranteed-by-construction.
2. **z3/cvc5 `load_bearing` on a count/identity tautology** (`n==computed AND n==EXPECTED`) ~50× — UNSAT over constants, no free-variable search. (Genuine-SMT exceptions PRESERVED: geo_s1 n01, manifold_ab_weld, twistor, bloch_root — do NOT merge.)

**Practical rule going forward: trust the result-JSON `classification`/`promotion` fields over the `audit_verdict.md` headline prose.**

## MOST DURABLE-IF-WRONG (foundation — taints downstream if cited as load-bearing)
- **[1] gcm_constraint_carve_v1** — claimed: Second-pass audit_verdict.md PROMOTED this to "the first real candidate substrate" and UNLOCKED gcm_object_id freeze + substrate-first enforcement + 10-step-ladder step 2.
  - ACTUAL: scratch_diagnostic fixed-by-construction integer set-membership carve (125 grid -> 16 survivors / 8 probe-signature classes) under one pinned predicate family; 2-of-3 engines share build_packet(); decorative count-SMT; terrain-blindness is a token-string scan,
  - why durable: This is the substrate UNLOCK gate. Memory index treats gcm_constraint_carve_v1 as the passed-Hermes-checkpoint root of the whole GCM tower. If the substrate is a construction artifact, every downstrea
- **[2] gcm_geometry_attach_v0** — claimed: GENUINE-WITH-CAVEATS at weight HIGH: "first nested 1Q geometry attached to frozen GCM object; 8 classes survive density quotient; 2-4-4-4-2 shell pattern" with 3-engine + load-bear
  - ACTUAL: scratch_diagnostic by-construction readout: spinor+density are functions of probe_signature ONLY, and all 8 quotient classes have 2 members sharing IDENTICAL probe_signature, so "survival" is mechanically guaranteed; counts read straight from frozen registry; 
  - why durable: HIGH weight + feeds the geometry/Hopf/flux chain (gcm_connection_flux_attach, gcm_flux_strips, gcm_geometry_attach_2q). The '8 classes survive' headline is the load-bearing geometry result other packe
- **[3] gcm_2q_freeze_and_cut_v0** — claimed: audit_verdict 'MATH UNLOCK CONFIRMED'; envelope mode all_three_full_sims; z3/cvc5 load_bearing; entangled-vs-product separation presented as discovery.
  - ACTUAL: scratch_diagnostic: GENUINE stored-matrix recompute core (negativity 0.25/0, recompute to 5.8e-13) but only 1 of 3 engines (Julia) independently reconstructs rho; count-tautology SMT; entangled-vs-product is a relabel of two CONSTRUCTED families (purification 
  - why durable: This is the entanglement-into-the-tower claim (memory: 'the probe quotient is WHAT ADMITS entanglement'). If the separation is by-construction relabeling, the headline QIT result is hollow. codex2+qwe
- **[4] gcm_runtime_flux_3q_v0** — claimed: first runtime/QIT flux on 3Q surface; L/R opposition signs + time-reversal flip as controls; all_pass=true.
  - ACTUAL: scratch_diagnostic R-side current only; L is reverse_current_row(R) (deep-copy + negate) so J_cut_L+J_cut_R=0 BY CONSTRUCTION; L is value-identical to time_reversal row; SMT asserts hardcoded l_chi=-2/r_chi=+2 literals. L/R doctrine signature = BY_CONSTRUCTION
  - why durable: Chirality L=-2/R=+2 is a memory-indexed deep result (GNVW chirality). The v0 'opposition' is an artifact of negating one row. Its v1 sibling REPAIRS this (independent generators, opposition DISAPPEARS
- **[5] system_v6/sims/g2_forced_vs_installed_discriminator** — claimed: audit_verdict 'the discriminator is not decorative'; the SMT 'installed-not-forced' seven-unit-closure split (O SAT / H UNSAT) presented as a Fano/Cayley-Dickson closure proof.
  - ACTUAL: scratch_diagnostic: dim Der(O)=14 etc. is GENUINE computed rank/nullity across 3 real backends. BUT the headline H/O closure split is PURE PIGEONHOLE on Distinct() over (n-1) imaginary slots (probe: zero closure clauses still gives H=UNSAT, O=SAT); closure pre
  - why durable: Memory: 'non-associativity is INSTALLED not forced' is a DECISIVE root-axiom finding, 3-model panel-cleared. The discriminator's SMT is a cardinality tautology; only the dim-count is real. If cited as

## CLEAN CORE (~17 survived adversarial re-audit — the model for honest packets)
- compression_flow_radiated_record_v0 — overclaim=false, genuine-with-caveats. PyTorch independence genuinely repaired (no JAX import), payload-bound SMT is computed (sha256 digests from live carrier ro
- system_v6/sims/ecd05_instruction_machine_v0 — overclaim=false. C(18,3)=816 vs 16^3=4096 combinatorial death is reproducible and honestly scoped; definition-sensitivity (schedule-locked baseline ties) 
- system_v6/sims/gcm_constraint_carve_floor_v0 — overclaim=false. 24-state toy finite filter sanity check; correctly self-limited; no SMT, no multi-engine claim; numbers reproduce; by-construction weakn
- system_v6/sims/gcm_3q_freeze_and_cuts_v0 — overclaim=false, genuine-with-caveats. scratch_diagnostic 3Q attachment surface, runtime-flux blocked; CKW margin 3/16 reproduces; single-engine numpy (no fa
- system_v6/sims/gcm_4q_freeze_and_cuts_v0 — overclaim=false. 546 survivors/9 classes verified against upstream carve; stored rho_left/rho_right recompute to 0.0 delta over 3822 pairs; single-engine num
- system_v6/sims/gcm_object_id_freeze_v0 — overclaim=false, genuine-with-caveats. Deterministic SHA-256 ID-registry over the audited carve; tamper controls are REAL polarity flips (codex2 forged registr
- axis_independence_discriminators_036 — overclaim=false, genuine-with-caveats. Medium-strength class-level 3x3 independence under named pins; raw-dominance explicitly NOT claimed (Axis-0 row violation 
- axis0_amendment_light_sweep_v0 — overclaim=false. scratch_diagnostic; honestly self-reports old-commit drift, non-independent Julia/JAX mirrors, and aggregate-only SMT scope as DECISIVE caveats; pytes
- geo_s1_exact_closure_v0 — overclaim=false, genuine-with-caveats. v2 rebuild materially fixed all v1 failures (sign pin, two-CAS independence, crossing signs, honest table); SMT label slightly overstat
- geo_network_shell_coordinate_v0 — overclaim=false. Z3 SMT is genuine (binds runtime z_values + degree weights, erased-weights flips to SAT); Manifolds.jl load-bearing (real Sphere(2)/Torus(2) objects)
- geo_s2_negative_models_v0 — overclaim=false. Negative-model selectivity correctly scoped; by-construction negatives are appropriate for a selectivity suite (not exceeding ceiling); SMT binds computed 
- geo_s3_density_observable_v0 — overclaim=false. No structural-consensus (independent local build_result per leg, reads_peer_result=false verified); decorative-SMT caveat does not raise the ceiling bec
- gcm_nested_manifold_schema_v0 — overclaim=false. Honest presence/shape checker; self-limits to schema carriage; local weaknesses (untested-bypass, by-construction tests, tautological gap report) are n
- system_v6/sims/ecd05 + the freeze/cut family + the negative-model/selectivity suites form the clean core. Also clean: geo_s6_stacked_flows_hopf_v0 (overclaim=false — PyTorch independently computes lea
- system_v6/sims/z4_syndrome_record_v0 — overclaim=false. Same label defensible with an added by-construction caveat that is non-blocking; each leg builds its own table (reads_peer_result=false verified
- gcm_runtime_flux_3q_v1 — overclaim=false, genuine-with-caveats. The REPAIRED sibling of the rank-4 overclaim: independent L/R generators (max|R-reflect(L)|=0.86), and the doctrine KILL (J_cut/J_ent bo

## RECOMMENDED UNIFORM CORRECTIONS (owner-scoped — NOT yet applied)
1. Relabel `engine_contract.mode=all_three_full_sims` -> `julia_independent + 2 shared-payload verifiers` across the ~45 affected packets; demote the JAX/PyTorch "agreement" from independence evidence to construction-consistency.
2. Demote count-tautology z3/cvc5 `load_bearing` -> `supportive` across the ~50 affected; PRESERVE the genuine-SMT exceptions.
3. Correct the FOUNDATION audit_verdict prose/addenda: gcm_constraint_carve_v1 substrate-UNLOCK over-promotion; gcm_geometry_attach_v0 "8 classes survive"; gcm_2q_freeze_and_cut entanglement-separation; gcm_runtime_flux_3q_v0 L=reverse(R) (cite v1 instead); g2_forced_vs_installed SMT (keep only the genuine dim-count).
4. ADDENDUM-upgrade meta-pattern: where an addendum upgraded a correctly-narrowed verdict to EARNED, revert to the narrowed verdict (the first audit was right).

## LIVE DISPUTES (codex2 vs second — do NOT auto-merge, per anti-collapse)
- round3_s9_alias_pass_v0: codex2 decorative-smt/DEMOTE vs grok-4.3 disputes the demotion.
- geo_union_rule_k_leaves_v0: codex2 decorative-smt vs deepseek genuine-with-caveats.
- geo_s7_discrete_refinement_v0: codex2 structural-consensus/DEMOTE vs deepseek genuine-with-caveats.

---

## Collapse-audit + synthesis (verbatim, fresh-context)

# Collapse-Audit + Synthesis Receipt — system_v6 sim audit corpus

**Auditor:** fresh-context collapse-audit (did not author the per-packet audits). **Date:** 2026-06-13.
**Source-verified** (not taken on trust): per-packet `_envelope.py` distinctness; `gcm_constraint_carve_2q_v0_common.py:913-914`; `scripts/validate_three_engine_sim_result.py:4`; the three flagged disputes at `round3_s9.../jax.py:217-219`, `geo_union_rule.../python.py:342-343`, `geo_s7.../jax.py:142-144`; 40/159 JAX legs call a shared common builder.

## 1. Shared-premise verdict
| Premise | Real disease or over-counted split? |
|---|---|
| structural-consensus (`build_packet()` shared) | **REAL, not over-counted.** No single cross-packet builder — each packet has its own `_envelope.py`. Same *idiom* recurs in ~45 packets (40/159 JAX legs verified). Each flag stands on its own per-packet call. |
| decorative-smt (count/identity tautology) | **REAL, one shape repeated ~50×.** Verified `n==computed AND n==EXPECTED` at carve_2q:913-914. Not a fabricated split. |
| Genuine-SMT exceptions | **CORRECTLY PRESERVED** (geo_s1 n01, manifold_ab_weld, twistor, bloch_root T2/T4). Do NOT merge into the decorative bucket — that would be the false collapse. |
| validator green = math holds | **FALSE upstream premise**, auditors flagged correctly (validator: "does not prove the math"). |
| audit_verdict.md vs result-JSON | **Overclaim lives in PROSE/ADDENDA**, not the honest `scratch_diagnostic`/`promotion=false` fields. |

## 2. Codex2-vs-second disputes (PRESERVE — do not auto-merge)
- **A. round3_s9_alias_pass_v0** — both agree SMT decorative; FORK on whether disclosed-decorative-SMT *demotes the label* (codex2: yes) or is a *named caveat* (grok arbiter: no). SymPy core genuine in both.
- **B. geo_union_rule_k_leaves_v0** — decorative-SMT-dominant (codex2) vs genuine-SymPy-core-rescues (deepseek). Math identical.
- **C. geo_s7_discrete_refinement_v0** — convergence claim "genuinely supported" (deepseek) vs structurally hollow (codex2). Mechanics concurred.
- ~6 forks total / ~120 packets, all **label-severity**, **zero mechanism disagreements**.

## 3. Ranked overclaim ledger (top of full ledger)
1. **gcm_constraint_carve_v1** — substrate UNLOCK over-promoted by addendum (taints whole GCM tower).
2. **gcm_geometry_attach_v0** — HIGH-weight by-construction "8 classes survive".
3. **gcm_2q_freeze_and_cut_v0** — entanglement separation = constructed-family relabel.
4. **gcm_runtime_flux_3q_v0** — L=reverse(R), doctrine-void (v1 repairs it).
5. **g2_forced_vs_installed** — non-assoc SMT is cardinality pigeonhole; only dim-count genuine.
6–7. **SYSTEMIC**: `all_three_full_sims` (1 indep engine + 2 shared verifiers) and `load_bearing` count-SMT (~95 packets combined). Inflate evidence grade, rarely break ceiling.
8. **ecd06 v0/v1/v2** — SURVIVES/DIES via baseline-excluded-by-construction.
9. **discrete_axis3/5/axes12, axis0_contender_heavy** — by-construction axis readouts.
10. **geo_s1 exact ADDENDUM upgrades** — first NARROWED verdict was honest; addendum EARNED-upgrade unsupported.

## 4. Uniform remediation (no new audits needed)
- Relabel `all_three_full_sims` → `one-independent-engine (Julia) + two shared-payload verifiers`.
- Demote count/identity `z3/cvc5 load_bearing` → `supportive` (keep the ~5 genuine-SMT exceptions load_bearing).
- Treat result-JSON `classification`/`promotion_allowed` as ground truth; treat `audit_verdict.md` headlines and addenda as suspect.

## 5. Genuinely-clean (~17)
compression_flow_radiated_record_v0 · ecd05_instruction_machine_v0 · gcm_constraint_carve_floor_v0 · gcm_3q/4q_freeze_and_cuts_v0 · gcm_object_id_freeze_v0 · gcm_runtime_flux_3q_v1 · axis_independence_discriminators_036 · axis0_amendment_light_sweep_v0 · geo_s1_exact_closure_v0 · geo_network_shell_coordinate_v0 · geo_s2_negative_models_v0 · geo_s3_density_observable_v0 · geo_s6_stacked_flows_hopf_v0 · gcm_nested_manifold_schema_v0 · z4_syndrome_record_v0 · retrocausal_possibility_field_v4_irreducibility · round3_s6s7_alias_pass_v0.
