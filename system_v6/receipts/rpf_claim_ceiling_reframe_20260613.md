# RPF claim-ceiling reframe — "chiral entropic future-compression" is an OVERCLAIM; the EARNED floor is a lookahead/boundary-value separation (2026-06-13)

```yaml
receipt_kind: claim_ceiling_reframe
status: DRAFT for owner review — NOT committed, NOT promoted
ceiling: scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false
subject: retrocausal_possibility_field v0..v3 (+ v4 irreducibility discriminator)
verified_this_session:
  - read rpf_v3 source + results JSON (full)
  - read rpf_v0 audit_verdict.md, wizard v4.3 full verdict, the EARNED_WITH_CAVEAT commit b8fbe9e84
  - fresh local rerun of v4 irreducibility sim (exit 0, ok:true) — result reproduced
interpreter: /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
```

## Bottom line

Five+ independent adjudicators now AGREE, and they converge: the name **"chiral entropic future-compression" / "retrocausal" is an OVERCLAIM** for what the rpf sims compute. The OpenRouter panel (qwen3.7-max, kimi-k2.6, deepseek-v4-flash) judged it UNANIMOUSLY an overclaim — "epistemic holism, not retrocausal influence; computational scope, not causal direction"; grok-4.3 ruled the acceptance gate **necessary-but-not-sufficient**; the wizard v4.3 full run exited **EARNED_WITH_CAVEAT**. These are not a decorative split — they make the same structural move from independent starting points, so the convergence is the signal.

The honest, audited, scratch_diagnostic floor that the computation DOES earn is narrow and real: **global co-admissibility selection over a future-possibility field is probe-distinguishable from any forward/greedy sequential selection** — a genuine lookahead / boundary-value separation. Everything past that (entropy arrow, chirality, future-conditioning, backward influence) is the owner's **interpretive frame**, honest as a research direction but NOT demonstrated by the sim.

There is one finding here that sharpens the verdict beyond what the panel saw: **the single decisive discriminator has already been built and run, and it came back essentially negative.** See §3.

---

## 1. The EARNED floor (rpf_v0..v3) — what the computation genuinely establishes

**Claim (earned, scratch_diagnostic):** On a trivial finite carrier, a **global co-admissibility selection** over a future-possibility field is **provably DISTINCT from any forward/greedy sequential selection** — a real lookahead / boundary-value separation — with **compatibility derived from a boolean admissibility constraint C** (not a similarity metric) and **orientation derived from measured fiber cardinality** (not a stored label).

Concretely, in `retrocausal_possibility_field_v3` (`system_v6/sims/retrocausal_possibility_field_v3/`):
- The global compressor's survivor is `b8` (joint co-adm-pair-count = 2). The single-anchor forward selector AND the strongest full-history forward selector both return `b2` (count 1). The separation survives against the *strongest* forward variant, not just a weak tie-break control. (`ACCEPTANCE_GATE.retrocausal_earned=true`, `independent_divergence_search.global_beats_full_history_forward=true`.)
- Compatibility C = `(a_p+a_q even) AND (|b_p-b_q|<=1)` — a boolean partition, not v1/v2's `1/(1+L1)` weight. Negative controls fire: dropping the parity clause moves the survivor `b8→b2` (`parity_clause_is_load_bearing=true`); the uniform all-True relation collapses the probe (`uniform_correctly_kills_the_probe=true`).
- Orientation INWARD/OUTWARD is a computed function of measured fiber cardinality (many-to-one → INWARD, injective → OUTWARD); reversing the cardinality flips the label end-to-end (`orientation_is_emergent=true`).
- Shell ordering is load-bearing: moving a branch between shells with the union unchanged moves the survivor `b8→b2` (`shell_reassignment_moves_survivor=true`) — not a relabeled flat-union (the rpf_v0 caveat is closed at v3).

**What this floor is in plain, provider-neutral terms:** it is a real, audited **lookahead / boundary-value optimization separation** — a global optimum over the whole possibility field that a myopic forward pass cannot reach. The sim's own `claim_ceiling` already says this exactly: *"a COMPUTATIONAL separation (global optimum vs forward greedy), NOT literal backward causation."* This floor is genuine and survived a fresh-context reimplementation audit (EARNED, per commit b8fbe9e84).

---

## 2. What is NOT earned by the computation — the interpretive overlay

These four are **interpretive mappings to the owner physics model**, honest as a research frame, but **NOT demonstrated by any rpf sim**:

| Interpretive term | Why the sim does not earn it |
|---|---|
| **entropy ARROW** | No entropy quantity is computed or monotone; the "compression" is an argmax over a static pair-count, not a thermodynamic gradient. |
| **CHIRALITY** | "Inward/outward" is a derived cardinality label on a finite map; nothing handed-ness/parity-violating is exhibited. The orientation flips freely under reversal — it is a *direction tag*, not a chiral asymmetry. |
| **future-CONDITIONING** | The convergent OpenRouter reading: the global optimum is **epistemic holism / computational scope** (the optimizer sees the whole field), not a present that is *conditioned on* a selected future. Static constraints over the field fully encode the result. |
| **retrocausal / backward INFLUENCE** | Forward-causally explicable as a boundary-value problem / lookahead. No probe shows the future configuration altering present selection *beyond* what the static constraint set already encodes. |

The panel's words for the gap: **"epistemic holism, not retrocausal influence; computational scope, not causal direction."** grok-4.3's words: the "differs from forward selection" gate is **necessary-but-not-sufficient** — a forward Markov kernel *with hidden state* could also beat naive forward selection, so beating it does not establish backward causation.

---

## 3. The single decisive discriminator — and the load-bearing finding: it ALREADY RAN, essentially NEGATIVE

**The discriminator (kimi/grok/panel converge on this exact test):** the *irreducibility* test — does the future configuration alter present selection **beyond** what the static constraints encode? Operationalized as: the global selection's output-sequence measure μ, **TV-distance to the best-fit forward hidden-state Markov kernel** (alphabet ≤ measured fiber size N_f), must stay above a threshold (~0.05). If a bounded-width *forward* process reproduces μ, the strong global/retrocausal reading is killed; only if no forward kernel can is the lookahead irreducible.

**The finding (preserve this — do not collapse):** this discriminator is **already built and run** as `retrocausal_possibility_field_v4_irreducibility` (`system_v6/sims/retrocausal_possibility_field_v4_irreducibility/`). Fresh local rerun this session: exit 0, `ok:true`. Its verdict is **BORDERLINE / FAMILY-DEPENDENT, leaning NEGATIVE**:
- Primary symmetric family (k=2,2,2, n=27): `tv_infimum = 0.0468 < 0.05` → **REDUCIBLE** (a width-N_f forward Markov chain reproduces it).
- Family-sensitivity sweep: **1 of 7** independent families is irreducible; **6 of 7** are reducible. `verdict_is_family_dependent=true`.
- Negative control is reducible (tv → ~0) in **every** family — so the test discriminates.
- The sim's own conclusion: *"rpf_v3's global-vs-greedy separation is NOT robustly irreducible to a forward+bounded-hidden-state (width-N_f) model ... the strong 'retrocausal/global' reading is NOT earned by this discriminator. It survives only on specially-structured families, which is exactly the necessary-not-sufficient gap the audit named."*

**Consequence for the reframe:** the discriminator is not a *pending upgrade path* — it has fired, and on the primary carrier it lands on the REDUCIBLE side of the line. The lookahead separation of §1 stands (that result is robust); but the *upgrade from lookahead to irreducible/future-conditioned* is **not** carried by v4 on this carrier. Any future attempt to upgrade the floor must either (a) exhibit a carrier family where irreducibility is robust (not a hand-picked 1-of-7), with a pre-registered, family-independent threshold and a stated draw process, or (b) accept that on trivial finite carriers the separation is a forward-reducible lookahead and stop there. The honest status today is the latter.

---

## 4. The naming rule (binding for any downstream citation of these sims)

- **Sim-earned name:** call it **"global future-conditioned constraint selection (lookahead-separated from greedy)"** — or equivalently "global co-admissibility selection," "boundary-value / lookahead separation." This is the only name the computation supports.
- **Owner's interpretive frame (explicitly NOT sim-earned):** reserve **"chiral entropic future-compression," "retrocausal," "future-conditioning," "backward influence"** for the owner's research interpretation. These may be used only with an attached caveat that they are an *interpretive mapping to the physics model, not demonstrated by the sim*.
- Do not use "retrocausal" as bare shorthand in titles, commit subjects, or status rows without the caveat — the EARNED_WITH_CAVEAT commit b8fbe9e84 already uses "chiral entropic future-compression" as the corrected frame; this receipt holds that the *frame* itself is interpretive, and the irreducibility evidence (§3) leans against upgrading it.

---

## 5. Blocked downstream consumers (carried from the sim results, unchanged)

Axis0 claim; flux claim; physics claim; formal manifold admission; "this trivial carrier is THE retrocausal field of the real model"; "global-vs-greedy separation demonstrates literal backward causation"; "the boolean constraint C is a physical co-admissibility law"; "computational irreducibility = literal backward causation"; "width-N_f forward irreducibility generalizes beyond this family."

---

## 6. Citations

- Panel: OpenRouter 5-model (qwen3.7-max, kimi-k2.6, deepseek-v4-flash) — UNANIMOUS overclaim verdict; "epistemic holism, not retrocausal influence; computational scope, not causal direction."
- grok-4.3: acceptance gate necessary-but-not-sufficient (forward hidden-state kernel could beat naive forward).
- Wizard v4.3 full run: `system_v6/receipts/rpf_retrocausal_not_earned_wizard_verdict_20260613.md` (EARNED on field-instantiation + shell-ordering axes; NOT earned on the retrocausal axis at the v1/v2 stage).
- rpf_v3 sim + result: `system_v6/sims/retrocausal_possibility_field_v3/retrocausal_possibility_field_v3.py`, `.../results/retrocausal_possibility_field_v3_results.json` (`object_statement_sha256: 02f813d355b5812e1021eb023e5aca7c6006c00dcfc060cf94ff727b7cb8dd78`).
- rpf_v4 irreducibility discriminator + result (the decisive test, already run): `system_v6/sims/retrocausal_possibility_field_v4_irreducibility/results/retrocausal_possibility_field_v4_irreducibility_results.json` (`tv_infimum=0.046783625730994205`, `verdict_is_family_dependent=true`, `irreducible_to_forward_hidden_state=false`).
- rpf_v0 audit: `system_v6/sims/retrocausal_possibility_field_v0/audit_verdict.md`.
- EARNED_WITH_CAVEAT commit: `b8fbe9e84`.

## 7. Ceiling

scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false. The §1 lookahead/boundary-value separation is a genuine, audited computational result. "Chiral entropic future-compression" / "retrocausal" remain the owner's interpretive frame, explicitly not sim-earned — and the §3 irreducibility discriminator, having already run, leans AGAINST upgrading that frame on the present carrier. This is a DRAFT for owner review. Do not commit; do not promote.
