# Axis 0 Typed Shell Cut Contract

**Date:** 2026-03-31  
**Purpose:** Define the strict cut-side contract for the surviving shell/interior-boundary family.  
**Scope discipline:** This is a cut-contract packet. It does not replace the strict shell bridge packet, and it does not claim the final doctrine-level cut is solved.

---

## 1. What This Packet Owns

- [AXIS0_ACTIVE_PACKET_INDEX.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_ACTIVE_PACKET_INDEX.md) is the compact entrypoint for the current active `Axis 0` packet stack.

This packet owns the minimum cut-side target for the shell family:

\[
\mathcal C_{\mathrm{shell}} = \{(r,w_r,A_r|B_r,\rho_r)\}_r
\]

but only on the cut side.  
The shell bridge packet owns how a future strict `Xi_shell` emits that family.  
This packet owns what the family must look like to count as a real shell/interior-boundary cut.

---

## 2. Minimum Contract

The typed shell cut contract is:

\[
\mathcal C_{\mathrm{shell}} = \{(r,w_r,A_r|B_r,\rho_r)\}_r
\]

with:

| Object | Meaning | Status |
|---|---|---|
| \(r\) | shell or band index | required |
| \(w_r\) | shell weight or measure factor | required |
| \(A_r|B_r\) | typed bipartite shell cut at shell \(r\) | required |
| \(\rho_r\in \mathcal D(\mathcal H_{A_r}\otimes\mathcal H_{B_r})\) | bipartite cut-state at shell \(r\) | required |

This is the minimum honest target for the current strongest shell-family global form

\[
\Phi_0(\rho)=\sum_r w_r\, I_c(A_r\rangle B_r)_{\rho_r}
\]

to mean anything shell-cut based rather than merely shell-labeled.

---

## 3. Required Conditions

| Requirement | Why it matters | Kill read |
|---|---|---|
| typed shell family | shell index must matter as a real family coordinate | shell is decorative only |
| real bipartite cut per shell | each shell term must be a legitimate cut | shell label with no \(A_r|B_r\) |
| real shell cut-state \(\rho_r\) | QIT quantities must live on a shell-indexed bipartite state | one unsigned scalar per shell |
| weight discipline \(w_r\) | shell aggregation must be explicit | ad hoc unweighted list |
| kernel compatibility | \(-S(A_r|B_r)\), \(I_c(A_r\rangle B_r)\), and \(I(A_r:B_r)\) must make sense on the same shell family | only supports ad hoc diagnostics |
| ownership separation | shell bridge and shell cut stay distinct | shell bridge packet silently owns the cut contract |

---

## 4. Safest Current Shape

The safest current shape is not one finished microscopic shell algebra.  
It is a typed family contract:

\[
\{(r,w_r,A_r|B_r,\rho_r)\}_r
\]

Current strongest interpretation:

- the shell/interior-boundary family is the strongest doctrine-facing cut family
- this packet owns what makes that family a legitimate shell cut family
- the exact shell algebra inside \(A_r|B_r\) is still open, with strict option-space now owned in [AXIS0_SHELL_ALGEBRA_STRICT_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_SHELL_ALGEBRA_STRICT_OPTIONS.md)
- the microscopic meaning of the strongest target \(I_r|B_r\) is now narrowed further in [AXIS0_SHELL_BOUNDARY_INTERIOR_MICRO_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_SHELL_BOUNDARY_INTERIOR_MICRO_OPTIONS.md)

So the clean live read is:

\[
\text{typed shell cut contract} = \text{required target, still partially open}
\]

---

## 5. Candidate Cut Typings

| Candidate typing | Current read | Status |
|---|---|---|
| generic \(A_r|B_r\) per shell | safest abstract shell typing | `KEEP` as fallback |
| boundary/interior split \(I_r|B_r\) | strongest doctrine-facing shell typing | `KEEP` as strongest target |
| shell-history hybrid shell slices | live overlap route with history packet | `KEEP` as hybrid route, not base contract |
| raw local `L|R` repeated across shells | control only | `KILL` as sufficient shell cut |

---

## 6. What Remains Open

| Open item | Why still open |
|---|---|
| exact microscopic shell algebra for \(A_r|B_r\) | not yet fixed canonically |
| exact construction of \(\rho_r\) from live geometry/history | bridge surfaces are still working rather than final |
| exact weighting discipline across shells | \(w_r\) is required, but not yet uniquely fixed |
| exact relation to shell-history hybrid route | overlap exists, but ownership split must remain explicit |

---

## 7. Safe Combined Read

What is now safe to say:

- shell/interior-boundary remains the strongest doctrine-facing cut family
- it must be typed as a real family \((r,w_r,A_r|B_r,\rho_r)\)
- a future strict `Xi_shell` must land in that family rather than merely naming shells
- the contract is stricter now than "shell language seems right"

What is still not safe to say:

- the exact shell algebra has not been solved
- shell doctrine has not uniquely determined the final doctrine-level cut
- shell doctrine by itself fixes the executable bridge

---

## 8. Handoff To Owner Packets

- [AXIS0_XI_SHELL_STRICT_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_XI_SHELL_STRICT_OPTIONS.md)
- [AXIS0_SHELL_ALGEBRA_STRICT_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_SHELL_ALGEBRA_STRICT_OPTIONS.md)
- [AXIS0_CUT_TAXONOMY.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_CUT_TAXONOMY.md)
- [AXIS0_KERNEL_BRIDGE_CUT_HANDOFF.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_KERNEL_BRIDGE_CUT_HANDOFF.md)

Shortest handoff:

\[
\text{shell cut is no longer just a family slogan; it now has a typed target contract}
\]

Short plain-text lock: shell cut is no longer just a family slogan; it now has a typed target contract.
