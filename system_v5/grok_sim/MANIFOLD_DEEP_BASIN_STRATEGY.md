# Geometric Manifold → Deep Basin Admission Strategy

**Authored:** 2026-05-18 by Claude (grok_sim side-quest thread), via 8-worker Sonnet council.
**Status:** Strategy document for owner to hand to Codex / formal_scouts thread.
**Scope:** Does NOT include implementation. Read-only analysis of formal_scouts/ + classifier logic + 3 root manifold receipts.

---

## TL;DR

The root geometric constraint manifold has a **candidate evidence package** worth testing for deep_basin admission. It is currently **blocked before admission**: the receipts don't expose section names that the classifier's `derived_invariant_control` function recognizes, and current formal receipts still own the admission decision. Any structural rename must be treated as a reproduction/anti-smuggling test, not as proof that the evidence was already admitted.

**Closest probe to deep_basin:** [`sim_root_manifold_g_structure_holonomy_chart_invariance_probe.py`](system_v5/ops/formal_scouts/sim_root_manifold_g_structure_holonomy_chart_invariance_probe.py) (Codex's chart-invariance probe, May 18 17:18). It already has gauge-equivalent control SAT, sympy/runtime exact agreement (abs_error=0.0), and 3 distinct graveyard controls. Candidate signals exist, but admission still requires fresh formal reproduction, anti-smuggling review, pair-falsifier pressure, and validator pass.

---

## Hard Blocker (one line)

`derived_invariant_control()` in [the classifier](system_v5/ops/formal_scouts/sim_attractor_basin_success_criteria_receipt_classifier_probe.py:1191-1211) checks if the receipt's section names intersect this set:

```
receipt_rows = {
    "weakened_control_sat",
    "sympy_numpy_crosscheck",
    "dual_independent_encodings_present",
    "z3_cvc5_agree",
    "cross_solver_agreement_tuple",
    "all_4_unsat",
    "invariant_preserving_control",
    "invariant_preserving_proxy_breaking_control",
}
```

**None of these 8 names appear** in any of the 3 root manifold receipts (`positive`, `graveyard_companions`, or `boundary` keys). The function returns `False`. The deep_basin branch (classifier:1328-1338) requires `invariant_control = author_invariant_control AND receipt_invariant_control` — so it short-circuits to `False` regardless of case-card content.

This is the only mechanical classifier blocker identified here. It is not an admission statement: formal reproduction, anti-smuggling review, multi-seed variation, and pair-falsifier pressure remain binding before any deep_basin claim.

---

## Current State (3 root manifold receipts)

| Receipt | Date | Section-name hits | Cross-solver agreement | Sympy crosscheck | Graveyard diversity | Verdict |
|---|---|---|---|---|---|---|
| `root_geometric_constraint_manifold_maturity_pytorch_toolchain_probe` | May 18 15:36 | 0/8 receipt_rows | z3+cvc5 UNSAT in `proof_tool_joint_admission` | sympy commutator (partial) | 11 entries, diverse | Strong, but no receipt_rows match |
| `root_manifold_seed_variation_portability_probe` | May 18 17:30 | 0/8 receipt_rows | `z3_cvc5_operating_admission` (semantic match) | Absent | Boundary fragility documented | Only 4 LB tools |
| `root_manifold_g_structure_holonomy_chart_invariance_probe` | May 18 17:22 | 0/8 receipt_rows | `proof_tool_chart_arithmetic_witness` (semantic match) | **min/max abs_error = 0.0 across 5 charts** | 3 distinct controls (gauge / symmetric / folded) | **Closest to deep_basin** |

**Closest match: chart-invariance probe.** It has:
- `gauge_equivalent_control_sat: "sat"` from both z3 and cvc5 — first `weakened_control_sat` evidence in the set
- `sympy chart-derivative + clifford + e3nn cross-check`: min/max abs_error = 0.0 — strongest `sympy_numpy_crosscheck` evidence
- `lewm_relative_loss_advantage: 0.977` — highest across the 3 receipts
- 13 load-bearing tools, 3 mechanistically-distinct graveyard rejections

The candidate signals are present. The section keys are not enough by themselves; any rename must be treated as a formal reproduction and anti-smuggling test before admission.

---

## The Pattern That Works (D5_Cl22)

Only 2 cases currently pass deep_basin in the classifier. The newer (May 2026), stricter pattern is `D5_Cl22_portability_20260518`:

```python
{
    "method_families": ["z3_boolean_encoding", "z3_bitvec_encoding",
                        "cvc5_boolean_encoding", "cvc5_bitvec_encoding"],
    "independent_methods_required": 4,
    "proxy_pair_control": True,
    "invariant_preserving_control": True,
    "positive_required_terms": ["all_4_unsat", "cross_solver_agreement_tuple",
                                "weakened_control_sat"],
    "claim_ceiling_terms": ["formal scout", "does not admit", "canonical"],
}
```

Receipt structure (the receipt to mimic):
- `positive`: `all_4_unsat`, `cross_solver_agreement_tuple`, `weakened_control_sat`, `encodings` list with 4 entries
- `boundary`: `z3_unsat_both`, `cvc5_unsat_both`, `z3_cvc5_agree`
- `graveyard_companions`: `weakened_control_is_sat_so_unsat_is_not_solver_trivial`, `no_single_solver_or_single_encoding_dependency`

This activates `structural_boundary_control_ok()` via both paths (boundary keys present AND aggregate row present), which is the strongest possible signal.

---

## Phase 1 — Probe-Side Strengthening (Codex territory)

**Target:** [`sim_root_manifold_g_structure_holonomy_chart_invariance_probe.py`](system_v5/ops/formal_scouts/sim_root_manifold_g_structure_holonomy_chart_invariance_probe.py)

### Change 1a (REQUIRED): Add `z3_cvc5_agree` to `boundary` section

**Evidence backing:** `proof_tool_chart_arithmetic_witness.z3.arithmetic_required_unsat_when_denied: "unsat"` AND `proof_tool_chart_arithmetic_witness.cvc5.arithmetic_required_unsat_when_denied: "unsat"` already exist in the current receipt. The two solvers already independently agree.

**The change:** Surface this agreement as a top-level boundary section, not nested inside `proof_tool_chart_arithmetic_witness`. Add to `boundary`:

```python
"z3_cvc5_agree": {
    "pass": True,
    "z3_result": "unsat",
    "cvc5_result": "unsat",
    "claims_tested": ["arithmetic_required_unsat_when_denied", "knockout_required_unsat"],
    "claim": "z3 and cvc5 independently return unsat on the same denial; cross-solver agreement is structural, not solver-specific"
},
```

**Why this is NOT smuggling:** The agreement is empirically present in the current receipt at `proof_tool_chart_arithmetic_witness.z3` and `.cvc5`. The rename surfaces existing evidence; it does not fabricate new evidence.

**Anti-smuggling check:** Before adding the field, grep the probe source for `cvc5.Solver()` and `z3.Solver()` invocations and confirm they use SEPARATE encoding functions (not one shared encoding fed to both backends). If shared, the agreement is cosmetic.

### Change 1b (REQUIRED): Add `weakened_control_sat` to `positive`

**Evidence backing:** `proof_tool_chart_arithmetic_witness.z3.gauge_equivalent_control_sat: "sat"` AND same for cvc5. The weakened control already returns SAT in the current receipt.

**The change:** Surface as a top-level positive section:

```python
"weakened_control_sat": {
    "pass": True,
    "z3_result": "sat",
    "cvc5_result": "sat",
    "control_description": "gauge-equivalent sheet permitting flux symmetry returns SAT — proves UNSAT verdict is not solver-trivial",
    "claim": "weakened control returns SAT in both solvers, ruling out always-UNSAT bug"
},
```

**Anti-smuggling check:** Verify the weakened-control encoding is GENUINELY weaker (drops a constraint), not just a relabeling of the main encoding. Read the probe source's weakened-control function.

### Change 1c (RECOMMENDED SUPPORT-ONLY): Add `sympy_numpy_crosscheck` to `positive`

**Evidence backing:** `math_geometry_tools.sympy_chart_derivative_and_holonomy_order.min_abs_error: 0.0` and `max_abs_error: 0.0` across all 5 charts. Sympy and runtime numpy values agree EXACTLY.

**Boundary:** this is a symbolic-vs-numeric support/control row. It is not nonclassical admission evidence by itself, and NumPy-backed values cannot carry nonclassical or bridge claims without source-native formal_scout reproduction.

**The change:**

```python
"sympy_numpy_crosscheck": {
    "pass": True,
    "min_abs_error": 0.0,
    "max_abs_error": 0.0,
    "n_charts_compared": 5,
    "claim": "sympy symbolic derivative and numpy runtime derivative agree to floating-point exactness across all 5 charts"
},
```

**Anti-smuggling check:** Confirm sympy and numpy are computing the same quantity via INDEPENDENT methods (symbolic vs numeric), not numpy reading from a sympy-derived constant.

### Change 1d (DO NOT ADD): `all_4_unsat`, `cross_solver_agreement_tuple`

**Reason:** The probe currently has 2 solver encodings (z3 Bool, cvc5 Bool), not 4 (no BitVec variants). Adding `all_4_unsat: True` would assert 4 independent encodings exist when only 2 do. This is the canonical smuggling failure mode that S6 (anti-smuggling auditor) flagged as HIGH risk.

If 4-way agreement is desired, ADD the missing BitVec encodings to the probe FIRST (a real implementation change, not a rename). Until then, stick with `z3_cvc5_agree` (2 solvers, 1 encoding).

### Change 1e (DOCTRINE-REQUIRED, optional for classifier): Multi-seed variation

**Why:** The doctrine (`user_attractor_basin_success_doctrine.md`) requires aggregate-across-variations evidence for basin verdict. Single fixture = candidate_basin territory, even if the classifier would mechanically fire deep_basin.

**The change:** Run the 5-chart × 3-phase probe under 5+ random seeds for the underlying ratchet state initialization. Record `min_basin_gap_across_seeds`, `min_holonomy_gap_across_seeds`. Add to `summary`.

**Anti-smuggling check:** Verify the seeds actually change the state initialization, not just downstream randomness. (Per the prior session's iter_90 mishap, a probe with `torch.linspace` initial state is deterministic regardless of seed.)

---

## Phase 2 — External Case Card Authorship

**The author of the probe (Codex/Claude) CANNOT author the case card.** This is the anti-smuggling rule from `feedback_never_author_sim_and_basin_classifier_case_together.md`.

### Authorship Protocol

1. **Owner** dispatches a fresh-context Grok OR Gemini worker with:
   - The updated receipt JSON file (Phase 1 changes applied)
   - The classifier's `CASES` list format (one example entry like `D5_Cl22_portability_20260518` for reference structure)
   - Instructions: write a case card to test whether this receipt routes as a `deep_basin` candidate for formal review; this is not admission.
   - Explicit constraint: **DO NOT READ THE PROBE SOURCE**. Receipt JSON only.

2. **Case card template:**
   ```python
   {
       "id": "<author-lineage>-20260518-root-manifold-chart-invariance-deep-basin",
       "receipt": "root_manifold_g_structure_holonomy_chart_invariance_probe_results.json",
       "claim_under_test": "<authored from receipt content>",
      "expected_label": "candidate_for_formal_review_not_admission",
       "same_source_risk": False,
       "method_families": [<3-7 distinct families drawn from the 13 load-bearing tools>],
       "proxy_pair_control": True,
       "invariant_preserving_control": True,
       "independent_methods_required": 3,
       "positive_required_terms": [<terms that appear in the updated receipt's text_blob>],
       "negative_target_terms": [],
       "claim_ceiling_terms": ["formal scout", "does not admit", "canonical"],
       "rationale": "<author's reasoning>",
   }
   ```

3. **Lineage comment:** Commit the case card with explicit lineage attribution, following the existing pattern at classifier:468-487:
   ```python
   # === Cross-lineage case authored by <Grok|Gemini> from fresh context.
   # === Probe authored by Codex/Claude. Anti-smuggling separation maintained.
   ```

### Anti-smuggling check (before commit)

Run `expected_terms_present(case["positive_required_terms"], all_names, text_blob(receipt))` manually. If any term doesn't resolve, the case was written from imagination rather than the receipt. Re-author.

---

## Phase 3 — Cross-Classification Verification

**Verifier:** A THIRD model (Opus, fresh context) that has NOT seen the probe source NOR authored the case.

### Verification Protocol

The verifier receives:
- The new case card
- The classifier's `classify_case()` function only (not the full classifier file)
- The updated receipt

The verifier returns:
```json
{
  "computed_label": "<label>",
  "axis_scores": {
    "contract_ok": <bool>,
    "all_pass": <bool>,
    "source_independent": <bool>,
    "observable_independent": <bool>,
    "control_pressure": <bool>,
    "invariant_preserving_control": <bool>,
    "claim_ceiling_ok": <bool>,
    "positive_required_terms_present": <bool>
  },
  "verdict_matches_expected": <bool>,
  "attestation": "<reviewer's written reasoning>"
}
```

### Anti-smuggling check

If `axis_scores.author_invariant_control_mismatch` is `True`, **Phase 1 failed** — the rename didn't actually fire `derived_invariant_control`. Re-examine section placement. The `receipt_rows` keys MUST be at the top level of `positive` / `graveyard_companions` / `boundary`, not nested inside another section.

If `verdict_matches_expected` is `False`, the gap is real. Do not commit. Surface the missing axis to the case author for revision.

If `computed_label == "deep_basin"` and ALL axes pass: commit with the attestation as a comment in the case entry. Treat the row as a deep_basin candidate routed for formal review; do not call it admitted until independent formal receipts and doctrine checks pass.

---

## Anti-Smuggling Guards (3 BINDING)

These guards are binding on the entire admission attempt. Violation invalidates the admission.

### Guard 1: Receipt-only case authorship

Case card author MUST NOT have read the probe source. Lineage separation = the model family + session context, not just the model name. Claude (this thread, or any thread that has read the probe source) is **disqualified** from case authorship. Fresh-context Grok or Gemini only.

### Guard 2: No section names added without evidence backing

Phase 1 changes are STRUCTURAL RENAMES, not new evidence. The values in `z3_cvc5_agree`, `weakened_control_sat`, `sympy_numpy_crosscheck` MUST be derived from existing computed quantities, not hardcoded `True`. If a change takes < 5 minutes and adds only the field name with a hardcoded boolean, that's a red flag.

Specifically forbidden:
- Adding `all_4_unsat` while only 2 encodings exist (HIGH smuggling risk, S6 flagged)
- Re-encoding existing pass-flags under classifier-convention names without genuine independent encoding (S6 flagged)
- Section renaming via sed without re-running the probe to verify the new section is populated from the probe's actual execution

### Guard 3: Pair-falsifier required before deep_basin

Per `user_attractor_basin_success_doctrine.md`: deep_basin requires a pair-falsifier (Popper). The doctrine is stronger than the classifier's mechanical check.

**Minimum pair-falsifier:** A SEPARATE PROBE that constructs pairs of manifold states where one passes the maturity verdict and one fails it, distinguished by an INVARIANT independent of the proxy used in the maturity verdict (S4 designed 3 candidate pairs: order-gap vs noncommutativity, G-structure frozen-family gap vs survivor-quotient class count, auto_LiRPA bound width vs feature-trajectory structural rank).

Kill criterion: DS > 0.70 on 50+ pair-type-A pairs. If DS > 0.70, the proxy fails to capture the invariant and the deep_basin candidate route is invalidated. If DS < 0.30, the candidate survives this falsifier; formal admission remains blocked pending independent receipts, validator pass, and doctrine checks.

Without this pair-falsifier probe, the deep_basin admission rests on classifier mechanics alone — which is exactly the failure mode the doctrine prohibits.

---

## What NOT to Do

These are the smuggling-mode failures the council identified. Avoid every one.

1. **Don't rename sections via sed**. Run the probe; the renamed section must be populated from execution.
2. **Don't claim 4-way encoding agreement with 2 encodings**. `all_4_unsat` requires Bool + BitVec × z3 + cvc5 = 4. Until the probe has BitVec encodings, stick with `z3_cvc5_agree` (2-way).
3. **Don't write the case card from the probe author's thread**. Cross-lineage authorship is the anti-smuggling gate. Same model family + session context = same author.
4. **Don't tune `positive_required_terms` to fit the receipt after seeing the probe source**. Case author works from receipt JSON only.
5. **Don't use a hardcoded `True` value for any classifier-convention field**. Values must be derived from probe execution.
6. **Don't pre-declare `expected_label="deep_basin"` and then engineer the rest backwards.** Author the case from receipt content first; the label falls out.
7. **Don't skip the pair-falsifier**. Doctrine requires it. Classifier mechanics are necessary but not sufficient.

---

## Concrete Next Move (single ask for Codex)

Take the chart-invariance probe ([`sim_root_manifold_g_structure_holonomy_chart_invariance_probe.py`](system_v5/ops/formal_scouts/sim_root_manifold_g_structure_holonomy_chart_invariance_probe.py)) and:

1. Add three top-level receipt sections (in the probe's main output dict):
   - `boundary.z3_cvc5_agree` — surfacing existing `proof_tool_chart_arithmetic_witness` agreement
   - `positive.weakened_control_sat` — surfacing existing `gauge_equivalent_control_sat`
   - `positive.sympy_numpy_crosscheck` — surfacing existing `min/max_abs_error = 0.0`

2. Re-run the probe. Verify the receipt now has these top-level keys populated from execution (not hardcoded).

3. Hand the updated receipt JSON to a fresh-context **Grok** or **Gemini** worker (NOT Codex, NOT Claude) for case card authorship per Phase 2.

4. Hand the case card + updated receipt + classifier function to a fresh-context **Opus** worker for verification per Phase 3.

5. If verification passes: commit the case card with cross-lineage attribution. The result is a deep_basin candidate routed for formal review, not admission until independent formal receipts and doctrine checks pass.

6. In parallel, commission the pair-falsifier probe (per Guard 3) to satisfy the doctrine requirement.

---

## Council Provenance

This strategy was synthesized by 8 parallel Sonnet workers + grok_sim thread controller (Claude):

| Worker | Focus | Key finding |
|---|---|---|
| S1 | Classifier logic | Identified the 8-axis deep_basin path; `derived_invariant_control` receipt_rows set |
| S2 | Existing manifold receipts | Chart-invariance probe is closest to deep_basin; evidence present, names wrong |
| S3 | Codex's chart-invariance + ratchet probes | No pair-falsifier; no multi-seed; no cross_solver_agreement_tuple section |
| S4 | Pair-falsifier design | 3 proxy/invariant pairs; DS > 0.70 kill criterion |
| S5 | Tool integration verification | 13/14 tools genuinely load-bearing; sympy `exact_witness` is CNG; auto_LiRPA gate trivially satisfied |
| S6 | Anti-smuggling audit | 3 binding guards: receipt-only authorship, no name-without-evidence, pair-falsifier required |
| S7 | Existing deep_basin pattern | D5_Cl22 is the template; aggregate-UNSAT + cross-method + weakened-control SAT |
| S8 | Concrete delta synthesis | Hard blocker = `derived_invariant_control` returns False; minimum fix = `z3_cvc5_agree` in boundary |

All findings cross-checked. No collapse, no smoothed divergence. Heavy parallel Sonnet fan-out per owner directive.

---

**End of strategy.** Hand to Codex / formal_scouts thread for implementation. Do not implement from grok_sim/ thread — pollution risk.
