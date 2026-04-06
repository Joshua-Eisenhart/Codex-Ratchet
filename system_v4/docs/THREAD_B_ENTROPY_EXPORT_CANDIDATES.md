# Thread B Entropy Export Candidates

**Date:** 2026-03-29
**Status:** SUPERSEDED. Intermediate draft retained for audit context only. Do not cite as active pipeline surface.
**Superseded by:** THREAD_B_ENTROPY_EXPORT_BLOCK_REVIEW.md (review shapes) + THREAD_B_ENTROPY_SPLIT_VN_MI_EXPORT.md (VN+MI thin block)

---

## 1. Scope

This file covers only:

- `von_neumann_entropy`
- `mutual_information`
- `conditional_entropy`
- a deferred later packet for the strongest signed `Ax0` candidate

It does **not**:

- settle bridge or cut doctrine
- claim any term is already `CANONICAL_ALLOWED`
- provide a finished submission packet
- replace the lexeme-admission pass in [THREAD_B_LEXEME_ADMISSION_CANDIDATES.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_LEXEME_ADMISSION_CANDIDATES.md)

---

## 2. Proposed Candidate States

| Term | Candidate export stages now | Candidate permit stub now? | Reason |
|---|---|---|---|
| `von_neumann_entropy` | `MATH_DEF` + `TERM_DEF` | no | stable math term, but no need to push canonical permit beyond diagnostic use yet |
| `mutual_information` | `MATH_DEF` + `TERM_DEF` | deferred to later packet | stable diagnostic family, but permit work should be split from the base term packet |
| `conditional_entropy` | `MATH_DEF` + `TERM_DEF` | no | cut-dependent and bridge-sensitive; premature permit would hide that |
| deferred signed `Ax0` candidate | separate later packet | no in this packet | strongest `Ax0` candidate is still blocked by bridge/cut doctrine and should not sit in the shared entropy batch |

Conservative rule:

- the three less controversial terms can be bound in this shared packet
- this packet should stop at `MATH_DEF` + `TERM_DEF`
- the strongest signed `Ax0` candidate should move to a separate later packet after lexeme validation and cut/bridge discipline checks

---

## 3. Candidate IDs

| Term | Candidate `MATH_DEF` ID | Candidate `TERM_DEF` ID | Candidate later separate-packet ID |
|---|---|---|---|
| `von_neumann_entropy` | `S_MATH_VON_NEUMANN_ENTROPY_V1` | `S_TERM_VON_NEUMANN_ENTROPY_V1` | none |
| `mutual_information` | `S_MATH_MUTUAL_INFORMATION_V1` | `S_TERM_MUTUAL_INFORMATION_V1` | `S_PERMIT_MUTUAL_INFORMATION_V1` |
| `conditional_entropy` | `S_MATH_CONDITIONAL_ENTROPY_V1` | `S_TERM_CONDITIONAL_ENTROPY_V1` | none |
| deferred signed `Ax0` candidate | reserved for separate packet | reserved for separate packet | `S_PERMIT_COHERENT_INFORMATION_V1` reserved only as a later identifier |

---

## 4. Candidate Export Skeletons

These are now intentionally thin. The exact object-level lexemes should be imported only after the lexeme-admission packet is accepted for review. That keeps this surface focused on export shape rather than pretending the coordinate vocabulary is already settled.

### 4.1 `von_neumann_entropy`

```text
SPEC_HYP S_MATH_VON_NEUMANN_ENTROPY_V1
SPEC_KIND S_MATH_VON_NEUMANN_ENTROPY_V1 CORR MATH_DEF
REQUIRES S_MATH_VON_NEUMANN_ENTROPY_V1 CORR THREAD_B_LEXEME_COORDINATE_ADMISSION
DEF_FIELD S_MATH_VON_NEUMANN_ENTROPY_V1 CORR OBJECT_FAMILY finite_single_state_entropy
DEF_FIELD S_MATH_VON_NEUMANN_ENTROPY_V1 CORR OPERATIONS trace log
DEF_FIELD S_MATH_VON_NEUMANN_ENTROPY_V1 CORR INVARIANTS basis_independence single_state_mixedness
DEF_FIELD S_MATH_VON_NEUMANN_ENTROPY_V1 CORR DOMAIN finite_single_state
DEF_FIELD S_MATH_VON_NEUMANN_ENTROPY_V1 CORR CODOMAIN scalar
ASSERT S_MATH_VON_NEUMANN_ENTROPY_V1 CORR EXISTS MATH_TOKEN math_von_neumann_entropy
DEF_FIELD S_MATH_VON_NEUMANN_ENTROPY_V1 CORR FORMULA "S(rho) = -Tr(rho log rho)"

SPEC_HYP S_TERM_VON_NEUMANN_ENTROPY_V1
SPEC_KIND S_TERM_VON_NEUMANN_ENTROPY_V1 CORR TERM_DEF
REQUIRES S_TERM_VON_NEUMANN_ENTROPY_V1 CORR S_MATH_VON_NEUMANN_ENTROPY_V1
DEF_FIELD S_TERM_VON_NEUMANN_ENTROPY_V1 CORR TERM "von_neumann_entropy"
DEF_FIELD S_TERM_VON_NEUMANN_ENTROPY_V1 CORR BINDS S_MATH_VON_NEUMANN_ENTROPY_V1
ASSERT S_TERM_VON_NEUMANN_ENTROPY_V1 CORR EXISTS TERM_TOKEN von_neumann_entropy
```

### 4.2 `mutual_information`

```text
SPEC_HYP S_MATH_MUTUAL_INFORMATION_V1
SPEC_KIND S_MATH_MUTUAL_INFORMATION_V1 CORR MATH_DEF
REQUIRES S_MATH_MUTUAL_INFORMATION_V1 CORR THREAD_B_LEXEME_COORDINATE_ADMISSION
DEF_FIELD S_MATH_MUTUAL_INFORMATION_V1 CORR OBJECT_FAMILY finite_bipartite_correlation
DEF_FIELD S_MATH_MUTUAL_INFORMATION_V1 CORR OPERATIONS trace log partial_trace
DEF_FIELD S_MATH_MUTUAL_INFORMATION_V1 CORR INVARIANTS total_correlation unsigned
DEF_FIELD S_MATH_MUTUAL_INFORMATION_V1 CORR DOMAIN finite_bipartite_state
DEF_FIELD S_MATH_MUTUAL_INFORMATION_V1 CORR CODOMAIN scalar
ASSERT S_MATH_MUTUAL_INFORMATION_V1 CORR EXISTS MATH_TOKEN math_mutual_information
DEF_FIELD S_MATH_MUTUAL_INFORMATION_V1 CORR FORMULA "I(A:B) = S(rho_A) + S(rho_B) - S(rho_AB)"

SPEC_HYP S_TERM_MUTUAL_INFORMATION_V1
SPEC_KIND S_TERM_MUTUAL_INFORMATION_V1 CORR TERM_DEF
REQUIRES S_TERM_MUTUAL_INFORMATION_V1 CORR S_MATH_MUTUAL_INFORMATION_V1
DEF_FIELD S_TERM_MUTUAL_INFORMATION_V1 CORR TERM "mutual_information"
DEF_FIELD S_TERM_MUTUAL_INFORMATION_V1 CORR BINDS S_MATH_MUTUAL_INFORMATION_V1
ASSERT S_TERM_MUTUAL_INFORMATION_V1 CORR EXISTS TERM_TOKEN mutual_information
```

### 4.3 `conditional_entropy`

```text
SPEC_HYP S_MATH_CONDITIONAL_ENTROPY_V1
SPEC_KIND S_MATH_CONDITIONAL_ENTROPY_V1 CORR MATH_DEF
REQUIRES S_MATH_CONDITIONAL_ENTROPY_V1 CORR THREAD_B_LEXEME_COORDINATE_ADMISSION
DEF_FIELD S_MATH_CONDITIONAL_ENTROPY_V1 CORR OBJECT_FAMILY finite_bipartite_cut_state
DEF_FIELD S_MATH_CONDITIONAL_ENTROPY_V1 CORR OPERATIONS trace log partial_trace
DEF_FIELD S_MATH_CONDITIONAL_ENTROPY_V1 CORR INVARIANTS signed cut_dependent
DEF_FIELD S_MATH_CONDITIONAL_ENTROPY_V1 CORR DOMAIN finite_bipartite_cut_state
DEF_FIELD S_MATH_CONDITIONAL_ENTROPY_V1 CORR CODOMAIN scalar
ASSERT S_MATH_CONDITIONAL_ENTROPY_V1 CORR EXISTS MATH_TOKEN math_conditional_entropy
DEF_FIELD S_MATH_CONDITIONAL_ENTROPY_V1 CORR FORMULA "S(A|B) = S(rho_AB) - S(rho_B)"

SPEC_HYP S_TERM_CONDITIONAL_ENTROPY_V1
SPEC_KIND S_TERM_CONDITIONAL_ENTROPY_V1 CORR TERM_DEF
REQUIRES S_TERM_CONDITIONAL_ENTROPY_V1 CORR S_MATH_CONDITIONAL_ENTROPY_V1
DEF_FIELD S_TERM_CONDITIONAL_ENTROPY_V1 CORR TERM "conditional_entropy"
DEF_FIELD S_TERM_CONDITIONAL_ENTROPY_V1 CORR BINDS S_MATH_CONDITIONAL_ENTROPY_V1
ASSERT S_TERM_CONDITIONAL_ENTROPY_V1 CORR EXISTS TERM_TOKEN conditional_entropy
```

### 4.4 Deferred Signed-Cut Packet

The strongest signed `Ax0` candidate should be exported only in a separate later packet:

- [THREAD_B_SIGNED_AX0_DEFERRED_PACKET.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_SIGNED_AX0_DEFERRED_PACKET.md)

It remains downstream of bridge and cut doctrine and should not be bundled into the shared entropy batch just to make the batch look complete.

---

## 5. Evidence Notes

| Term | Least-arbitrary current evidence anchor | Why |
|---|---|---|
| `von_neumann_entropy` | none yet | no direct need to canon-permit beyond math/term staging |
| `mutual_information` | `E_SIM_AXIS0_TRAJ_CORR_METRICS` | existing trajectory correlation emitter already reports MI-related metrics |
| `conditional_entropy` | none yet | cut-typing and bridge doctrine are still too open |
| deferred signed `Ax0` candidate | `E_SIM_AXIS0_HISTORYOP_REC_ID_V1` | history-facing Axis-0 evidence is the least arbitrary current fit for the strongest signed candidate |

Evidence rule:

- use current evidence anchors only as provisional later-permit anchors
- do not infer canonical adequacy from mere metric presence
- `conditional_entropy` stays term-bound but unpermitted until cut/bridge typing stabilizes
- the deferred signed-cut packet should be exported only in the separate later packet above

---

## 6. Main Rejection Risks

| Risk | Why it matters here |
|---|---|
| `SCHEMA_FAIL` | malformed field order, missing asserts, or invalid container shape |
| `UNDEFINED_TERM_USE` | using non-bootstrap lexemes before the lexeme-admission packet is accepted |
| `GLYPH_NOT_PERMITTED` | formulas with unsupported glyphs or stray symbols |
| `DERIVED_ONLY_PRIMITIVE_USE` | treating the deferred signed `Ax0` candidate as if it were primitive admissibility rather than a downstream cut-state functional |

Conservative mitigation:

- keep formulas simple and ASCII-clean
- route object-level vocabulary through the lexeme-admission packet first
- keep the deferred signed candidate and `conditional_entropy` explicitly cut-dependent

---

## 7. Do Not Smooth

- Do not paste these as if they were ready-to-submit kernel artifacts.
- Do not reattach permit stubs to this packet just to make it look more complete.
- Do not hide cut dependence inside generic entropy vocabulary.
- Do not let the deferred signed `Ax0` candidate jump ahead of bridge/cut doctrine just because it is the strongest current candidate.
