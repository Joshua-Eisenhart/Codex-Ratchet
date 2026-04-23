# Return Packet: Ax1-Ax4 Chain Attack

**Lane ID:** `AX1_AX4_CHAIN_ATTACK`
**Model:** `OPUS`
**Date:** `2026-03-29`
**Status:** RETURN PACKET

## 1. Weakest Links in the Derivation

- **Circular/Missing Primitive Dependency for Ax4:** `THREAD_B_AX4_EXPORT_BLOCK_REVIEW.md` asserts `DERIVED_FROM Ax3_loop_type Ax1_branch_class engine_composition_rule`. However, `AXIS_PRIMITIVE_DERIVED.md` does not list `engine_composition_rule` under primitive axes. Furthermore, `AXIS_PRIMITIVE_DERIVED.md` defines "Engine type" as derived from `Ax3 × Ax4`. This risks a circular derivation (Ax4 requires engine rule, engine type requires Ax4) or relies on an undocumented root primitive rule.
- **Lack of Empirical Evidence Anchors in Ax1:** While Ax4 binds successfully to explicit `sim_Ax4_commutation.py` evidence tokens, the Ax1 block relies solely on a logical consistency check (64-address audit) and lacks an empirical probe anchor. It demands acceptance purely on structural deduction, which makes the base of the chain brittle.
- **Depth and Cascade Risk:** The chain requires `Ax0 × Ax2 → Ax1` and `Ax1 × Ax3 → Ax4`. A single fault in the Ax2 direct/conjugated classification will silently invert the entire Ax4 loop ordering structure, as Ax4 has no independent geometric anchor beyond its antecedents.

## 2. Ambiguous Terms

- `engine_composition_rule`: Used formally in the Ax4 MATH_DEF but completely undefined in the primitive/derived ledger. It operates as a ghost axiom.
- `unitary_branch` and `proper_cptp_branch`: `AXIS_PRIMITIVE_DERIVED.md` emphasizes that Ax1 is a "transition/dynamics axis, not a position axis" and identifies "graph edges". Yet the Ax1 review block statically binds these branch terms to sets of terrains (e.g., `NU class: Ne, Si`), implicitly treating them as set constraints rather than traversal edges. This conflates terrain identity with transition mechanics.
- `UEUE` / `EUEU` shorthand: In the Ax4 block, "E" is used as shorthand for "U class: Se/Ni (dissipative)", and "U" is used for "NU class: Ne/Si (unitary)". This is highly ambiguous notation (E = U-class; U = NU-class) that risks severe semantic drift if decoupled from the immediate block context.

## 3. Missing Evidence or Fences

- **Ax1 Generator-Family Evidence Fence:** `THREAD_B_TERM_ADMISSION_MAP.md` strictly dictates that `unitary_branch` and `proper_cptp_branch` require "generator-family evidence if promoted as kernel vocabulary". The `THREAD_B_AX1_EXPORT_BLOCK_REVIEW.md` block fails to include an `ASSERT S_MATH_AX1_BRANCH_CLASS CORR EVIDENCE ...` line satisfying this requirement.
- **Missing Antecedent Fence in Ax4 for Engine Rule:** The Ax4 block cites `engine_composition_rule` in its `DERIVED_FROM` assertion but lacks a corresponding `REQUIRES BLOCK CORR ENGINE_COMPOSITION_RULE` or `REQUIRES ... CORR LEXEME engine_composition_rule`.
- **Ax1 Bridge/Cut Decoupling Fence:** The Ax1 block notes in plaintext (Section 5) that it "Does not resolve the bridge/cut open issue", but this critical quarantine is missing from the formal `EXPORT_BLOCK` syntax as a `NOTE:` or explicit constraint.

## 4. Safety Assessment for REVIEW_ONLY

**Safe as REVIEW_ONLY? YES.**

Both blocks are strictly compliant with `REVIEW_ONLY` quarantine. They do not leak into `CANONICAL_ALLOWED`, they explicitly maintain their status as derived (not primitive), and they successfully isolate the proposed term definitions from live doctrine. 

However, they are **un-promotable** in their current state. The firewall must hold until the circular `engine_composition_rule` dependency is formalized and Ax1 binds to the required generator-family evidence tokens. The controller is advised to reject promotion of this chain until these gaps are closed.
