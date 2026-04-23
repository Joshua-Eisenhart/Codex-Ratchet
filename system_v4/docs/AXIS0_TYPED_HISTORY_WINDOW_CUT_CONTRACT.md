# Axis 0 Typed History-Window Cut Contract

**Date:** 2026-03-31  
**Purpose:** Define the strict cut-side contract for the history-window family that `Xi_hist` is supposed to land in.  
**Scope discipline:** This is a cut-contract packet. It does not replace the `Xi_hist` bridge packet, and it does not claim the final doctrine-level cut is solved.

---

## 1. What This Packet Owns

- [AXIS0_ACTIVE_PACKET_INDEX.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_ACTIVE_PACKET_INDEX.md) is the compact entrypoint for the active `Axis 0` controller, owner, and support packet stack.

This packet owns the minimum cut-side target for the surviving history bridge family:

\[
\Xi_{\mathrm{hist}}: h|_{[t_0,t_1]} \mapsto \{(t,c,w_c,\rho_c(t))\}_{t,c}
\]

but only on the cut side.  
The bridge packet owns how `Xi_hist` emits that family.  
This packet owns what the family must look like to count as a real history-window cut.

---

## 2. Minimum Contract

The typed history-window cut contract is:

\[
\mathcal C_h = \{(t,c,w_c,\rho_c(t))\}_{t,c}
\]

with:

| Object | Meaning | Status |
|---|---|---|
| \(t\) | real sample inside the history window | required |
| \(c\in C\) | typed cut family element at time \(t\) | required |
| \(w_c\) | cut weight or measure factor | required |
| \(\rho_c(t)\in \mathcal D(\mathcal H_A\otimes\mathcal H_B)\) | bipartite cut-state at that sample | required |

This is the minimum honest target for the history pullback

\[
\varphi_0[h]=\frac1T\int_0^T \sum_{c\in C} w_c\, I_c(c;\rho_h(t))\,dt
\]

to mean anything cut-based rather than merely trajectory-based.

---

## 3. Required Conditions

| Requirement | Why it matters | Kill read |
|---|---|---|
| typed history window | the window itself must matter | history is decorative only |
| typed cut family \(c\in C\) | cut semantics must be explicit | hidden or implied cut |
| real bipartite state \(\rho_c(t)\) | QIT quantities must live on a real cut-state | one-state proxy with no bipartite typing |
| weight discipline \(w_c\) | the history pullback must know how cuts are aggregated | ad hoc unweighted list of states |
| kernel compatibility | \(-S(A|B)\), \(I_c\), and \(I(A:B)\) must make sense on the same family | only supports ad hoc unsigned scalar |
| ownership separation | bridge and cut stay distinct | bridge packet silently owns the cut contract |

---

## 4. Safest Current Shape

The safest current shape is not one final formula for \(A_t|B_t\).  
It is a typed family contract:

\[
h|_{[t_0,t_1]} \leadsto \{(t,c,w_c,\rho_c(t))\}_{t,c}
\]

Current strongest interpretation:

- `Xi_hist` owns emission of a history-indexed cut-state family
- this packet owns what makes that family a legitimate history-window cut family
- the exact cut typing inside \(C\) is still open

So the clean live read is:

\[
\text{typed history-window cut contract} = \text{required target, still partially open}
\]

---

## 5. Candidate Cut Typings

| Candidate typing | Current read | Status |
|---|---|---|
| generic \(A_t|B_t\) | safest abstract cut typing | `KEEP` as fallback |
| explicit \(c\in C\) family | strongest canon-backed history form | `KEEP` as strongest target |
| shell-history hybrid typing | live overlap with shell packet | `KEEP` as hybrid route, not base contract |
| raw local `L|R` at each time | control only | `KILL` as sufficient history cut |

---

## 6. What Remains Open

| Open item | Why still open |
|---|---|
| exact family \(C\) | not yet fixed canonically |
| exact map \(t \mapsto \rho_c(t)\) | live bridge surfaces are still synthetic/working |
| exact weighting discipline across cuts | \(w_c\) is required, but not yet uniquely fixed |
| final rank against shell/interior-boundary | history is strongest executably, shell strongest doctrinally |

---

## 7. Safe Combined Read

What is now safe to say:

- history-window cut is the strongest live executable cut family
- it must be typed as a real family \((t,c,w_c,\rho_c(t))\)
- `Xi_hist` remains strongest executably because it can plausibly land in that family
- the contract is stricter now than “history-shaped Axis 0 is plausible”

What is still not safe to say:

- the exact history-window cut family has not been solved
- `Xi_hist` does not uniquely determine the final doctrine-level cut
- the history-side contract outranks shell/interior-boundary doctrinally

---

## 8. Handoff To Owner Packets

- [AXIS0_XI_HIST_STRICT_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_XI_HIST_STRICT_OPTIONS.md)
- [AXIS0_XI_HIST_EMISSION_PACKET.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_XI_HIST_EMISSION_PACKET.md)
- [AXIS0_CUT_TAXONOMY.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_CUT_TAXONOMY.md)
- [AXIS0_KERNEL_BRIDGE_CUT_HANDOFF.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_KERNEL_BRIDGE_CUT_HANDOFF.md)

Shortest handoff:

\[
\text{history-window cut is no longer just named; it now has a typed target contract}
\]

Short plain-text lock: typed history-window cut is no longer just named; it now has a typed target contract.
