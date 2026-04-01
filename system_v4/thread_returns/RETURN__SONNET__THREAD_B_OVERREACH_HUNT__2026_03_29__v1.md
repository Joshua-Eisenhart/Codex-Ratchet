# Return Packet: Thread B Overreach Hunt

**Return ID:** RETURN__SONNET__THREAD_B_OVERREACH_HUNT__2026_03_29__v1  
**Model:** Claude Sonnet 4.6 (Thinking)  
**Date:** 2026-03-29  
**Boot Packet:** BOOT__THREAD_B_OVERREACH_HUNT__2026_03_29__v1.md  
**Status:** COMPLETE

---

## 0. Scope

Files audited per boot packet §2:

1. `THREAD_B_STACK_AUDIT.md`
2. `THREAD_B_LANE_HANDOFF_PACKET.md`
3. `THREAD_B_TERM_ADMISSION_MAP.md`
4. `THREAD_B_ENTROPY_SPLIT_VN_MI_EXPORT.md`
5. `THREAD_B_AX1_EXPORT_BLOCK_REVIEW.md`
6. `THREAD_B_AX4_EXPORT_BLOCK_REVIEW.md`

Hunt criterion: any phrase that overstates readiness, permit status, or review status with respect to its actual gated state.

---

## 1. Overreach Findings

### Finding B-01 — Stack Audit header declares itself "current truth"

**File:** `THREAD_B_STACK_AUDIT.md`, line 4  
**Exact phrase:**
> "This is the current truth of the B-thread pipeline state."

**Why overreach:** The word "truth" imports finality that outranks what the file actually is — a review-stage audit of surfaces that are themselves REVIEW_ONLY or DRAFT. An audit document cannot be "truth"; it is an assessment at a point in time, downstream of actual controller verification. The surrounding items-in-review (lexeme candidates not yet accepted, axis export blocks still under controller review) make this claim visibly incorrect.

**Recommendation:** REWRITE  
Replace with: *"This is the current best-effort audit of the B-thread pipeline state as of 2026-03-29. Controller acceptance is required before any surface listed here advances."*

---

### Finding B-02 — "RESOLVED" verdict on lexeme risk used without controller acceptance

**File:** `THREAD_B_STACK_AUDIT.md`, §3, table row 1  
**Exact phrase:**
> "Undeclared lexemes in export wrappers (Warning 1) | **RESOLVED** by `THREAD_B_LEXEME_ADMISSION_CANDIDATES.md` — 4-tier admission chain declared"

**Why overreach:** The handoff packet (§4.1) explicitly states the lexeme registry status is pending controller accept/reject/modify. The collision-check audit passed (0 hard collisions), but the candidates are staged as DRAFT and have not been accepted into any registry. Labeling the original warning as RESOLVED overstates the gate: staging candidates is not resolution; it is preparation for review.

**Recommendation:** FENCE  
Change "RESOLVED" to "STAGED FOR REVIEW — collision check passed, controller acceptance pending." Do not promote to RESOLVED until controller accepts the tier split.

---

### Finding B-03 — "RESOLVED" verdict on preferred-name mismatch used without controller confirmation

**File:** `THREAD_B_STACK_AUDIT.md`, §3, table row 2  
**Exact phrase:**
> "Preferred-name mismatch between axis review surfaces and the shared lexeme owner packet | **RESOLVED** — the owner lexeme packet now uses the preferred axis names `horizontal_lift_loop` and `interaction_picture_equivalence` directly"

**Why overreach:** This calls a naming choice "resolved" when the lexeme packet is still DRAFT (per handoff §3 table, `THREAD_B_LEXEME_ADMISSION_CANDIDATES.md` status = DRAFT). A name can only be resolved once the lexeme is through the registry. The fix was applied internally to a document that has not yet been accepted. The word "RESOLVED" reads as a controller-level closure; it is not.

**Recommendation:** FENCE  
Change "RESOLVED" to "FIX APPLIED — pending registry acceptance." Qualify that the naming is consistent within the draft, not yet formally registered.

---

### Finding B-04 — "RESOLVED" verdict on entropy wrapper text used without controller confirmation

**File:** `THREAD_B_STACK_AUDIT.md`, §3, table row 3  
**Exact phrase:**
> "Over-specified entropy export wrapper text | **RESOLVED** — entropy export docs now depend on the lexeme-admission packet, use thinner object-family skeletons, and defer permit work to later packets"

**Why overreach:** The entropy export block (`THREAD_B_ENTROPY_SPLIT_VN_MI_EXPORT.md`) is explicitly REVIEW_ONLY and awaiting controller confirmation per handoff §4.2. "Resolved" implies the problem is gone; the correct state is "reformatted into a thinner review shape." The underlying concern — whether the split is the right call — is explicitly open.

**Recommendation:** FENCE  
Change "RESOLVED" to "REFORMATTED — thinner review shape produced; controller split acceptance is open."

---

### Finding B-05 — "RESOLVED" verdict on axis export wrapper text used without controller confirmation

**File:** `THREAD_B_STACK_AUDIT.md`, §3, table row 5  
**Exact phrase:**
> "Axis export wrapper text | **RESOLVED** — axis export docs now use thinner object-family skeletons, depend on lexeme admission, and defer antecedent/evidence closure to later packets"

**Why overreach:** Same class as B-04. The axis review shapes produced by the lane are REVIEW_ONLY. Whether the axis review shapes are acceptable is still a live controller decision per handoff §4.3 and §4.4. Using "RESOLVED" for what is actually "reformatted to a thinner pending shape" is an overstatement of closure.

**Recommendation:** FENCE  
Change "RESOLVED" to "REFORMATTED — thinner review shapes produced; Ax1 and Ax4 acceptance is still open per handoff §4.3–4.4."

---

### Finding B-06 — Lane Handoff "COMPLETE FOR THIS CYCLE" is ambiguous as a status claim

**File:** `THREAD_B_LANE_HANDOFF_PACKET.md`, §1 heading  
**Exact phrase:**
> "## 1. Lane Status: COMPLETE FOR THIS CYCLE"

**Why borderline overreach:** "COMPLETE" as a status could be read as delivery completion (intended) or as review completion (not warranted). The do-not-smooth section (§8) partially guards against the second reading, but the heading itself is unqualified. In the context of the handoff—where four controller review requests are pending (§4.1–4.4)—"COMPLETE" is accurate only for lane-internal work, not for the review chain that must follow.

**Recommendation:** FENCE  
Add a parenthetical to the heading: *"Lane Status: COMPLETE FOR THIS CYCLE (lane work done; controller reviews §4.1–4.4 still open)"* — or add a one-line clarification immediately below the heading before the prose begins.

---

### Finding B-07 — Handoff §2 table describes Ax1 and Ax4 exports as "Review shape" without surface-level status qualifier

**File:** `THREAD_B_LANE_HANDOFF_PACKET.md`, §2 New Deliverables table  
**Exact phrases:**
> `THREAD_B_AX1_EXPORT_BLOCK_REVIEW.md` | Review shape | "MATH_DEF + TERM_DEF for U/NU branch derivation; unblocks Ax4 antecedent"  
> `THREAD_B_AX4_EXPORT_BLOCK_REVIEW.md` | Review shape | "MATH_DEF + TERM_DEF for loop ordering non-commutativity; backed by 4 sim evidence tokens"

**Why borderline overreach:**  
"Unblocks Ax4 antecedent" (Ax1 row) is operationally accurate — the Ax1 block can now be cited as an antecedent shape. However, the language implies the citation is usable. Until the controller confirms Ax1 is safe as an antecedent (handoff §4.3), this is aspirational framing. Similarly, "backed by 4 sim evidence tokens" (Ax4 row) is true but risks reading as evidence-sufficient. The sim tokens are PASS on a review shape; they are not a canonical promotion signal.

**Recommendation:** FENCE  
Add a parenthetical or footnote to both rows: "unblocks Ax4 antecedent citation (pending controller §4.3 confirmation)" and "backed by 4 sim evidence tokens (tokens are PASS on review shape; not a promotion signal)."

---

### Finding B-08 — Term Admission Map status line reads "CURRENT" without qualification

**File:** `THREAD_B_LANE_HANDOFF_PACKET.md`, §3 table, row for `THREAD_B_TERM_ADMISSION_MAP.md`  
**Exact phrase:**
> `THREAD_B_TERM_ADMISSION_MAP.md` | Term admission states | CURRENT

**Why borderline overreach:** "CURRENT" is accurate as a document-currency label. However, several items within the Term Admission Map are staged as TERM_PERMITTED with explicit evidence gates not yet satisfied (e.g., `loop_order_unitary_first` states "evidence satisfied" in the notes column, implying a higher readiness than the overall pipeline state allows). Read in isolation, the CURRENT label gives no warning that TERM_PERMITTED in the map does not equal usable-in-canon.

**Recommendation:** KEEP — but cross-reference  
No change to the label, but add a note row or inline qualifier: "CURRENT — note: TERM_PERMITTED in this map does not equal CANONICAL_ALLOWED; see §7 Do Not Smooth."

---

### Finding B-09 — Term Admission Map notes "evidence emitted" for Ax4 loop terms suggesting higher status

**File:** `THREAD_B_TERM_ADMISSION_MAP.md`, §4 table, rows for `loop_order_unitary_first` and `loop_order_nonunitary_first`  
**Exact phrases:**
> `loop_order_unitary_first` | ... | TERM_PERMITTED | `AX4_LOOP_ORDERING_NONCOMMUTATIVE` evidence satisfied | **Ax4 family — evidence emitted**  
> `loop_order_nonunitary_first` | ... | TERM_PERMITTED | `AX4_UEUE_EUEU_DISTINCT` evidence satisfied | **Ax4 family — evidence emitted**

**Why overreach:** The Notes column says "evidence emitted" and the Evidence column says "evidence satisfied." Together these create a reading of *evidence-closure complete*, which is not the actual gate. The Ax4 review block (§7 Do Not Smooth) explicitly states: "Do not let the evidence tokens (PASS on sim) be read as canonical admission." The term map's "satisfied" language conflicts with the review block's own Do Not Smooth fence. Evidence tokens are emitted (sim ran, PASS recorded); this is not evidence-gate closure for CANONICAL_ALLOWED.

**Recommendation:** REWRITE  
Change "evidence satisfied" → "evidence token emitted (PASS); not yet evidence-gate-closed for canonical use."  
Change "Ax4 family — evidence emitted" → "Ax4 family — sim token emitted; formal promotion gate pending."

---

### Finding B-10 — Entropy Split Export block header cites "Authority" from a review document

**File:** `THREAD_B_ENTROPY_SPLIT_VN_MI_EXPORT.md`, header block  
**Exact phrase:**
> `Authority: THREAD_B_ENTROPY_EXPORT_BLOCK_REVIEW.md §4 (recommended split)`

**Why borderline overreach:** A "recommended split" inside a review document is advisory, not authoritative. Listing it as "Authority" puts review-document advice on the same level as a controller directive or a signed owner packet. The document it cites is itself BACKGROUND CONTEXT per the handoff (§3 table: `THREAD_B_ENTROPY_EXPORT_BLOCK_REVIEW.md` | BACKGROUND CONTEXT — not active preferred surface). An inactive background context document cannot be the authority for a current export block.

**Recommendation:** REWRITE  
Change "Authority:" → "Source recommendation:" or "Rationale source:" and clarify: "THREAD_B_ENTROPY_EXPORT_BLOCK_REVIEW.md §4 recommended this split; controller confirmation is needed to treat the split as authorized."

---

### Finding B-11 — Entropy Split §3 table uses "After this block" language suggesting state advancement

**File:** `THREAD_B_ENTROPY_SPLIT_VN_MI_EXPORT.md`, §3 table  
**Exact phrase:**
> | `von_neumann_entropy` | TERM_PERMITTED | **Still TERM_PERMITTED; MATH_DEF + TERM_DEF wrappers now exist** |  
> | `mutual_information` | TERM_PERMITTED | Same |

**Why borderline overreach:** "After this block" is a column header implying the block executes and changes something. But the block is REVIEW_ONLY and has not been accepted by the controller. "After this block" is premature; the correct framing is "if this block is accepted by controller, these terms will have formal wrappers." The current phrasing makes acceptance implicit.

**Recommendation:** FENCE  
Change column header "After this block" → "If accepted by controller." Change row text: "Still TERM_PERMITTED; MATH_DEF + TERM_DEF wrappers produced in this review shape (controller acceptance required to formalize)."

---

### Finding B-12 — Ax1 Export §4 "What This Unblocks" uses present-tense unblocking language

**File:** `THREAD_B_AX1_EXPORT_BLOCK_REVIEW.md`, §4  
**Exact phrases:**
> "Ax4's `REQUIRES ... CORR AX1_BRANCH_DERIVATION` can now point to `AX1_BRANCH_DERIVATION_REVIEW_0001` instead of informal derivation note"  
> "`unitary_branch` + `proper_cptp_branch` canonicalization path | MATH_DEF wrapper now exists; terms were TERM_PERMITTED without a formal wrapper"

**Why borderline overreach:** "Can now point to" and "wrapper now exists" are present-tense completions. The block is REVIEW_ONLY. The Ax4 block's REQUIRES line already *does* point to `AX1_BRANCH_DERIVATION_REVIEW_0001` — but that citation is valid only within a review chain. Using "now" implies an actual system-state change has occurred. The wrapper existing as a review shape on disk is not the same as it being a formally registered MATH_DEF. "Canonicalization path" is particularly at risk because it names the road to CANONICAL_ALLOWED.

**Recommendation:** FENCE  
Change "can now point to" → "can point to (as a review-stage antecedent citation, pending controller §4.3 confirmation)."  
Change "MATH_DEF wrapper now exists; terms were TERM_PERMITTED without a formal wrapper" → "MATH_DEF wrapper review shape now exists; formal registration pending controller acceptance."  
Change section header "What This Unblocks" → "What This Stages" or "What This Prepares."

---

### Finding B-13 — Ax4 Export §5 "What This Unblocks" uses present-tense canonicalization path language

**File:** `THREAD_B_AX4_EXPORT_BLOCK_REVIEW.md`, §5  
**Exact phrases:**
> "`loop_order_unitary_first` + `loop_order_nonunitary_first` canonicalization path | MATH_DEF wrapper now exists; terms had evidence tokens but no formal wrapper"  
> "Any Ax4-dependent downstream block | Can cite `AX4_LOOP_ORDERING_REVIEW_0001` as antecedent"

**Why overreach:** Same class as B-12. "Canonicalization path" combined with "wrapper now exists" and "evidence tokens" creates a compound overread: formal wrapper + evidence tokens = canonical path open. The Do Not Smooth section (§7) explicitly warns against exactly this reading, but the §5 framing contradicts it. "Can cite as antecedent" is similarly forward-leaning — any actual citation in a downstream block is still hypothetical until the Ax4 shape is controller-confirmed (handoff §4.4).

**Recommendation:** FENCE  
Change §5 table first row description: "MATH_DEF wrapper review shape now exists; canonicalization path staging prepared (formal path requires controller acceptance + promotion gate)."  
Change second row description: "Can cite as a review-stage antecedent (pending controller §4.4 confirmation)."  
Change section header "What This Unblocks" → "What This Stages" or "What This Prepares."

---

### Finding B-14 — Stack Audit §5 Evidence Token Registry marks AX6 closure as "PROVEN"

**File:** `THREAD_B_STACK_AUDIT.md`, §5 table  
**Exact phrase:**
> | `AX6_CLOSURE_b6=-b0*b3=PASS` | `/tmp/sim_axis6_closure.py` | **PROVEN** (16/16) |

**Why overreach:** "PROVEN" is a strong epistemic claim and the only token in the table using it. All three Ax4 tokens use "EMITTED." A sim run producing 16/16 is strong evidence that should be noted, but labeling it "PROVEN" in the official audit table imports a finality that the controller has not granted. The source file is also in `/tmp/` — a scratch location, not a canonically-registered evidence emitter. "PROVEN" from a `/tmp/` file is an overreach in both word choice and provenance.

**Recommendation:** REWRITE  
Change "PROVEN (16/16)" → "EMITTED (16/16 PASS) — source is /tmp/ scratch; requires promotion to registered evidence emitter before formal proof claim."

---

## 2. Summary Table

| ID | File | Phrase (truncated) | Type | Severity | Action |
|---|---|---|---|---|---|
| B-01 | STACK_AUDIT | "current truth of the B-thread pipeline state" | Status overstatement | HIGH | REWRITE |
| B-02 | STACK_AUDIT §3 | "RESOLVED by THREAD_B_LEXEME...4-tier admission chain declared" | Premature closure | HIGH | FENCE |
| B-03 | STACK_AUDIT §3 | "RESOLVED — owner lexeme packet now uses preferred axis names" | Premature closure | MEDIUM | FENCE |
| B-04 | STACK_AUDIT §3 | "RESOLVED — entropy export docs now...defer permit work" | Premature closure | MEDIUM | FENCE |
| B-05 | STACK_AUDIT §3 | "RESOLVED — axis export docs now use thinner...defer antecedent" | Premature closure | MEDIUM | FENCE |
| B-06 | LANE_HANDOFF §1 | "Lane Status: COMPLETE FOR THIS CYCLE" | Ambiguous completion | LOW | FENCE |
| B-07 | LANE_HANDOFF §2 | "unblocks Ax4 antecedent" / "backed by 4 sim evidence tokens" | Implied sufficiency | MEDIUM | FENCE |
| B-08 | LANE_HANDOFF §3 | `TERM_ADMISSION_MAP` status "CURRENT" (no TERM_PERMITTED warning) | Missing guard | LOW | KEEP + crossref |
| B-09 | TERM_ADMISSION_MAP §4 | "evidence satisfied" / "evidence emitted" on Ax4 loop terms | Evidence-gate collapse | HIGH | REWRITE |
| B-10 | ENTROPY_SPLIT header | "Authority: THREAD_B_ENTROPY_EXPORT_BLOCK_REVIEW.md §4" | Review → authority slip | MEDIUM | REWRITE |
| B-11 | ENTROPY_SPLIT §3 | Column header "After this block" / "wrappers now exist" | Implicit acceptance | MEDIUM | FENCE |
| B-12 | AX1_EXPORT §4 | "can now point to" / "MATH_DEF wrapper now exists" / "unblocks" | Present-tense closure | MEDIUM | FENCE |
| B-13 | AX4_EXPORT §5 | "canonicalization path" / "Can cite as antecedent" / "unblocks" | Compound overread | HIGH | FENCE |
| B-14 | STACK_AUDIT §5 | "PROVEN (16/16)" from /tmp/ source | Provenance + finality | HIGH | REWRITE |

---

## 3. Keep / Fence / Rewrite Recommendations

### KEEP (no change needed)

- `THREAD_B_TERM_ADMISSION_MAP.md` §1 scope — correctly bounded; explicitly states what the file does not do.
- `THREAD_B_TERM_ADMISSION_MAP.md` §7 Do Not Smooth — well-constructed; no overreach.
- `THREAD_B_LANE_HANDOFF_PACKET.md` §5 "What This Lane Did Not Touch" — correctly delineates scope; no overreach.
- `THREAD_B_LANE_HANDOFF_PACKET.md` §6 Stop Condition — correctly invokes the staging stop rule.
- `THREAD_B_LANE_HANDOFF_PACKET.md` §8 Do Not Smooth — well-constructed; no overreach.
- `THREAD_B_ENTROPY_SPLIT_VN_MI_EXPORT.md` §6 Do Not Smooth — correctly fences all four risks.
- `THREAD_B_AX1_EXPORT_BLOCK_REVIEW.md` §5 / §7 Do Not Smooth — correctly states what the block does not do.
- `THREAD_B_AX4_EXPORT_BLOCK_REVIEW.md` §6 / §7 Do Not Smooth — correctly states what the block does not do.
- All QUARANTINED entries in the Term Admission Map — properly gated; no overreach.

### FENCE (add guards without rewriting meaning)

- B-02: Change "RESOLVED" → "STAGED FOR REVIEW — collision check passed, controller acceptance pending."
- B-03: Change "RESOLVED" → "FIX APPLIED — pending registry acceptance."
- B-04: Change "RESOLVED" → "REFORMATTED — thinner review shape produced; controller split acceptance is open."
- B-05: Change "RESOLVED" → "REFORMATTED — thinner review shapes produced; Ax1 and Ax4 acceptance is still open."
- B-06: Add "(lane work done; controller reviews §4.1–4.4 still open)" to the lane status line.
- B-07: Add "(pending controller §4.3 confirmation)" after "unblocks Ax4 antecedent"; add "(tokens are PASS on review shape; not a promotion signal)" after evidence token mention.
- B-08: Add crossref note pointing to Do Not Smooth on TERM_PERMITTED ≠ CANONICAL_ALLOWED.
- B-11: Change column header "After this block" → "If accepted by controller"; qualify wrapper language.
- B-12: Change "can now point to" / "now exists" / "unblocks" → staged/pending language; rename §4 header to "What This Stages."
- B-13: Change §5 descriptions to review-stage language; rename §5 header to "What This Stages."

### REWRITE (meaning must change to avoid overreach)

- B-01: Drop "truth" from the status line; replace with "best-effort audit … controller acceptance required."
- B-09: Change "evidence satisfied" → "evidence token emitted (PASS); not yet evidence-gate-closed for canonical use."
- B-10: Change "Authority:" → "Rationale source:"; note that the citing document is BACKGROUND CONTEXT and cannot authorize.
- B-14: Change "PROVEN (16/16)" → "EMITTED (16/16 PASS) — /tmp/ source; requires promotion to registered evidence emitter."

---

## 4. Hard Rule Confirmations

- No permit decisions made in this packet.
- No canon promotion made or implied.
- No doctrine ranking changed.
- Review and staging language not promoted to canon.
- All recommendations are fence or rewrite suggestions for the controller; none are self-executing.

---

*End of return packet.*
