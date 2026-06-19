# Governance Unification — Three Preserved Designs (gemini alt-view, 2026-06-12)

```yaml
receipt_kind: altview_owner_choice
route: gemini TUI (auto-gemini-3), prompted w/ lane D's adjudication + AGENTS.md + the
  enforcement rules; instructed to preserve alternatives, not pick
decision_owner: the owner — this receipt feeds the synthesis's owner-gate section
context: lane D (e80451d2f) adjudicated the old mechanical stage gate as authoritative
  (active_stage=lego; axis-NAMED v6 work was ceiling-labeled, never unlocked)
```

As an alt-view advisor on this governance transition, I have reviewed the Lane D adjudication, the Agent Contract, and the current enforcement rules. The tension is clear: the **Old Gate** treats names (Axis, Engine) as *unlocked privileges* of rank, while the **New Process** treats them as *descriptive labels* of intent.

Here are three distinct designs for unifying these layers while guarding against the repo's primary threat: **claim-language inflation** (the "Narrative Substitution" risk described in Rule 12).

---

### Design 1: The Semantic Ceiling (Vocabulary-Aware Gate)
In this design, `stage_gate.py` is upgraded to understand "Ceiling Labeled" claims. The gate remains authoritative, but its blocking logic becomes aware of the `claim_ceiling` field in v6 receipts.

*   **How it works:** The gate allows a packet named `axis0_diagnostic` to pass while `active_stage=lego`, provided the receipt explicitly declares a non-promotional ceiling (e.g., `claim_ceiling: scratch_diagnostic` or `axis_named_receipt_only`). If a packet attempts to use an Axis-name without a ceiling label, the gate fires and blocks.
*   **What it unblocks:** It allows researchers to use high-level "intent" names (Axis, Engine) for low-level work (diagnostics, one-step witnesses) without violating the repo's stage laws.
*   **What it risks:** **Semantic Drift.** Over time, "Axis0 Diagnostic" is shortened to "Axis0" in dev-chat, memory files, and eventually the mental model of the agents. This is the "Narrative Substitution" failure mode: the name "Axis" begins to carry the weight of authority even when the ceiling label technically denies it.
*   **Stage-advancement criterion:** Moving `active_stage` from `lego` to `coupling` requires an explicit "Stage-Closure Receipt" that audits the transition from *diagnostic* axis-claims to *substantive* axis-claims.

### Design 2: Nominal Conformity (The Strict Ladder)
This design enforces absolute structural integrity by requiring that all work-in-progress be named according to its *active stage*, regardless of its eventual intent.

*   **How it works:** If the gate is at `lego`, nothing in the `system_v6/sims/` directory can be named `axis` or `engine`. The work currently called `axis0_amendment` would be forcibly renamed to something like `lego_coupling_a0_v0`. Names like "Axis" are reserved exclusively for the `axis` stage.
*   **What it unblocks:** Total clarity and "Search-to-Truth" mapping. If a grep for "Axis" returns a file, you *know* it is an unlocked, promoted, canonical result. There is zero ambiguity.
*   **What it risks:** **Developer Friction and Shadow Naming.** Agents and humans naturally think in terms of the target (Axis). If the repo forbids the name, researchers will use "Shadow Names" in `MEMORY.md`, comments, or private notes (e.g., "This lego-coupling-001 is actually the Axis0 test"). These shadow names are invisible to the audit tools, creating a layer of ungoverned folklore.
*   **Stage-advancement criterion:** A quantitative **Coverage Gate**. The stage moves only when 100% of defined "Lego Families" have fresh, passing, `load_bearing` capability probes.

### Design 3: The Authority Bit (Promotional Decoupling)
This design (the "third way") moves from a **blocking** gate to a **filtering** gate. It decouples the *Name* of the work from its *Authority*.

*   **How it works:** The repository allows any name at any time, but it introduces a mandatory boolean field: `promotion_allowed`. `stage_gate.py` no longer blocks the *execution* or *existence* of Axis-named files. Instead, it regulates a global "Authority Index." Tools like the `visualizer`, `rankers`, and `bridge-builders` are programmed to only "see" or "ingest" results where `promotion_allowed: true`.
*   **What it unblocks:** Maximum exploratory speed. Researchers can ship "Axis" and "Engine" packets daily to the `scratch` tier without triggering gate errors.
*   **What it risks:** **Signal-to-Noise Collapse (The "Sea of Labels").** The repo could fill with thousands of `promotion_allowed: false` packets. The "Authority Index" becomes a tiny, hard-to-find needle in a haystack of "Axis-named" noise. The failure mode is a "False Sense of Progress" where the sheer volume of scratch work obscures the fact that the actual `lego` stage hasn't moved in months.
*   **Stage-advancement criterion:** A **Manual "Stage-Clearance" Audit**. To move past `lego`, a human or a high-rank Agent (Hermes/Owner) must review the "Authority Index" and flip the `active_stage` bit only after confirming that the *intent* of the scratch work has successfully matured into *canonical evidence*.

---

### Advisor Summary for Owner Review

| Feature | Design 1: Semantic Ceiling | Design 2: Nominal Conformity | Design 3: The Authority Bit |
| :--- | :--- | :--- | :--- |
| **Primary Logic** | Vocabulary-aware gate. | Names = Privileges. | Naming is free; Promotion is gated. |
| **User Experience** | "Label it honestly." | "Call it what it is today." | "Explore freely, Promote rarely." |
| **Inflation Guard** | Hard (Ceiling label). | Absolute (Name is blocked). | Soft (Authority filter). |
| **Hardest Failure** | Shorthand/Drift. | Shadow Folklore. | Signal-to-Noise Loss. |

**Recommendation:** Do not pick a winner yet. Design 1 is the most "incremental" and matches the Lane D audit's intuition. Design 2 is the "Old Guard" favorite for absolute safety. Design 3 is the most "Agent-native" for high-velocity parallel exploration.
