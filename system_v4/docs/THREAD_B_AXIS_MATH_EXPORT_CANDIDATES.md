# Thread B Axis Math Export Candidates

**Date:** 2026-03-29
**Status:** DRAFT candidate `MATH_DEF` and `TERM_DEF` items for the first stable axis-math vocabulary set. These are staged for review only and should be read downstream of [THREAD_B_LEXEME_ADMISSION_CANDIDATES.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/THREAD_B_LEXEME_ADMISSION_CANDIDATES.md).

---

## 1. Scope

This packet covers four early-stable axis-math families that are currently source-locked and probe-backed:

- `Ax3`: Manifold Path Class (Fiber vs Base-Lift)
- `Ax5`: Operator Generator Class (Dissipative vs Coherent)
- `Ax2`: Representation Frame (Direct vs Interaction Picture)
- `Ax4`: Loop Ordering (Deductive vs Inductive; still derived and review-only here)

---

## 2. Candidate Items

### A. Axis 3: Manifold Path Class

| Field | Candidate Value |
|---|---|
| **ID** | `S_MATH_AX3_PATH_CLASS_DEF` |
| **Kind** | `MATH_DEF` |
| **Object family** | finite realized path-class family |
| **Logic** | `path_class = (d(rho)/du == 0) ? INNER : OUTER` |
| **Invariant** | `density_stationarity_on_fiber` |
| **Dependency** | lexeme admission packet plus favored-geometry realization |

| Field | Candidate Value |
|---|---|
| **ID** | `S_TERM_AX3_LOOP_FAMILY` |
| **Kind** | `TERM_DEF` |
| **Term** | `axis3_path_class` |
| **Binds** | `S_MATH_AX3_PATH_CLASS_DEF` |

---

### B. Axis 5: Operator Generator Class

| Field | Candidate Value |
|---|---|
| **ID** | `S_MATH_AX5_GENERATOR_CLASS_DEF` |
| **Kind** | `MATH_DEF` |
| **Object family** | finite generator-class family |
| **Logic** | `class = (-i[H, rho]) ? COHERENT : DISSIPATIVE` |
| **Invariant** | `von_neumann_entropy_preservation` |
| **Dependency** | lexeme admission packet plus admitted QIT basin |

| Field | Candidate Value |
|---|---|
| **ID** | `S_TERM_AX5_KERNEL_TYPE` |
| **Kind** | `TERM_DEF` |
| **Term** | `axis5_operator_class` |
| **Binds** | `S_MATH_AX5_GENERATOR_CLASS_DEF` |

---

### C. Axis 2: Representation Frame

| Field | Candidate Value |
|---|---|
| **ID** | `S_MATH_AX2_REPRESENTATION_FRAME_DEF` |
| **Kind** | `MATH_DEF` |
| **Object family** | finite frame-rotation family |
| **Logic** | `V(u) = exp(-i H_s u)` where `H_s = +/- H_0` |
| **Invariant** | `interaction_picture_equivalence` |
| **Dependency** | lexeme admission packet plus favored Weyl working layer |

| Field | Candidate Value |
|---|---|
| **ID** | `S_TERM_AX2_FRAME_ROTATION` |
| **Kind** | `TERM_DEF` |
| **Term** | `axis2_frame_class` |
| **Binds** | `S_MATH_AX2_REPRESENTATION_FRAME_DEF` |

---

### D. Axis 4: Loop Ordering (Commutation)

| Field | Candidate Value |
|---|---|
| **ID** | `S_MATH_AX4_LOOP_COMMUTATION_DEF` |
| **Kind** | `MATH_DEF` |
| **Object family** | finite ordered-channel family |
| **Logic** | `[U, E] != 0` -> `(U o E o U o E) != (E o U o E o U)` |
| **Invariant** | `intermediate_entropy_trajectory_differentiation` |
| **Dependency** | lexeme admission packet plus later Ax1 support packet and later probe closure |

| Field | Candidate Value |
|---|---|
| **ID** | `S_TERM_AX4_LOOP_ORDER` |
| **Kind** | `TERM_DEF` |
| **Term** | `axis4_loop_order` |
| **Binds** | `S_MATH_AX4_LOOP_COMMUTATION_DEF` |

---

## 3. Rejection Risks

- **Lexeme Inflation**: concrete coordinate vocabulary still depends on the lexeme-admission packet and should not be re-expanded here.
- **Dependency Nesting**: `Ax4` depends on later support work for the `U` and `E` branches from `Ax1`.
- **Ax0 Absence**: Axis 0 is omitted for now due to the high-complexity bridge requirement.
- **Probe Closure Drift**: this packet should not pretend the later Ax4 probe packet or broader axis export closure is already finished.

---

## 4. Next Step

Promote these candidates only into a thinner `EXPORT_BLOCK v1` review shape similar to the cleaned entropy batch:

1. depend on the lexeme-admission packet
2. stop at `MATH_DEF + TERM_DEF`
3. keep probe and support closure in later packets
