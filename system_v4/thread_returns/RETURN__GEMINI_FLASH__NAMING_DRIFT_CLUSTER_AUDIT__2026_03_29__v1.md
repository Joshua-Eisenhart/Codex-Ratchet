# Naming Drift Cluster Audit Return Packet

**Lane ID:** `NAMING_DRIFT_CLUSTER_AUDIT`
**Date:** `2026-03-29`
**Status:** COMPLETE RETURN PACKET

## 1. Executive Summary
This audit identified several naming drift clusters across the `system_v4/docs/` surface. The most significant risks are found in duplicated mapping surfaces with singular/plural filename drift and synonym drift between core concepts (Lexeme vs Term) in the Thread B admission pipeline.

---

## 2. Drift Inventory

| Family | Exact Literal Forms Found | Preferred Form | Risk Level |
|---|---|---|---|
| **Axis Identifier Shorthand** | `AXIS0`, `AXIS1`, `Axis 0`, `Axis 1`, `Axis0`, `Axis1`, `Ax0`, `Ax1`, `Ax3`, `Ax4` | `Ax0`, `Ax1`, etc. (Text); `AXIS0` (Filenames) | **LOW** (Minor stylistic drift) |
| **Bridge Operator Naming** | `XI`, `Xi`, `xi`, `Xi_hist`, `xi_hist`, `XI_HIST`, `Xi_ref`, `Xi_shell`, `Xi_LR` | `Xi` (Formal); `xi` (Literal terms); `Xi_hist` (Executable family) | **LOW** (Consistent across functional families) |
| **Admission Lexeme vs Term** | `Lexeme`, `LEXEME_DEF`, `Term`, `TERM_DEF` | `Lexeme` (Vocabulary); `Term` (Bound math unit) | **MEDIUM** (Potential conceptual confusion in Thread B expansion) |
| **Pipeline Interface Surface** | `handoff`, `export`, `HANDOFF`, `EXPORT`, `Review`, `Audit`, `Inventory` | `export` (Thread boundary); `handoff` (Internal module bridge) | **MEDIUM** (Process ambiguity during handoffs) |
| **Primary Mapping Duplication** | `AXIS_MATH_BRANCHES_MAP.md`, `AXIS_MATH_BRANCH_MAP.md` | `AXIS_MATH_BRANCHES_MAP.md` (Higher detail density) | **HIGH** (Authoritative duplication risk) |
| **Engine Mapping Synonymy** | `64_RUNTIME_ENGINE_TABLE`, `8x8`, `THE_8X8_ENGINE_MAPPING` | `64_RUNTIME_ENGINE_TABLE` (Math primary) | **MEDIUM** (Redundant terminology/surfaces) |
| **Constraint Plurality** | `Constraint`, `Constraints` | `Constraint` (Filename/Class); `Constraints` (Upstream ladder/Rule set) | **LOW** (Linguistic drift) |
| **Topological Regime Naming** | `Topology4`, `Terrain8`, `Stage8`, `Base Regimes` | `Topology4` (Math identifier); `Base Regimes` (Overlay label) | **LOW** (Naming layering) |
| **Quarantine Registry States** | `QUARANTINED`, `quarantine`, `MATH_DEFINED`, `TERM_PERMITTED` | `QUARANTINED` (Formal registry state) | **LOW** (Contextual naming) |

---

## 3. Detailed Cluster Notes

### 3.1 Axis Identifier Drift
*   **Forms:** `AXIS0` is the dominant filename/header form. `Ax0` is the dominant text form. `Axis 0` appears in some older or formal introductory sections.
*   **Risk:** Low. The system is highly readable despite the drift, as long as `Ax0` and `AXIS0` are understood as equivalent.

### 3.2 Bridge/Xi Family Drift
*   **Forms:** Filenames use `AXIS0_XI_...`. Text uses `Xi` or `Xi_hist`. Term tables use `xi_hist` (snake_case literal).
*   **Risk:** Low. The mapping from `XI` to `Xi` to `xi` is clear, but consistency in the literal term table (`xi_hist` vs `Xi_hist` in text) should be maintained to avoid "Undefined Term" errors in automated parsing.

### 3.3 Lexeme vs Term (Thread B)
*   **Findings:** `THREAD_B_LEXEME_ADMISSION_CANDIDATES.md` vs `THREAD_B_TERM_ADMISSION_MAP.md`.
*   **Drift:** The repo uses "Lexeme" to define vocabulary components and "Term" to define bound mathematical units.
*   **Risk:** Medium. While technically distinct, the distinction is subtle and could lead to "Lexeme-term-permit leaks" (as noted in Batch 01) where users treat a defined lexeme as a permitted term.

### 3.4 Mapping Surface Duplication
*   **Findings:** `AXIS_MATH_BRANCHES_MAP.md` and `AXIS_MATH_BRANCH_MAP.md` exist as nearly identical files with slightly different structures.
*   **Risk:** High. These files represent synchronous views of the same logic with a singular/plural naming drift. They both list the 7-axis math branches but with different section headers and emphasis. This creates high risk for conflicting edits.

### 3.5 Pipeline Synonymy
*   **Findings:** The terms `handoff` and `export` are used to describe the transfer of blocks and data.
*   **Risk:** Medium. `EXPORT_BLOCK` is the formal structure for Thread B, but "handoff" is used for Axis 0 internal transitions (e.g., `AXIS0_KERNEL_BRIDGE_CUT_HANDOFF.md`). The risk is that "handoff" might be used for Thread B packets erroneously, bypassing the formal "EXPORT" validation rules.

---

## 4. Final Audit Status
**Audit Status:** COMPLETE
**Policy Change:** NONE (Inventory only)
**Doctrine Change:** NONE

No blocked reports. All documentation files in `system_v4/docs/` were scanned for the identified drift families.
