* there is only one primitive substance: constraint on distinguishability.
* Verified Then the downstream identifications are:
    * matter = constraint
    * energy = constraint flow
    * geometry = constraint compatibility
    * dynamics = constraint-respecting transformation
    * information = constraint bookkeeping







**Current Truth**
- `Verified` In the deeper ladder, entropic monism is **not** “everything is entropy.”
- `Verified` The source statement is:

  there is only one primitive substance: **constraint on distinguishability**.

- `Verified` Then the downstream identifications are:
  - matter = constraint
  - energy = constraint flow
  - geometry = constraint compatibility
  - dynamics = constraint-respecting transformation
  - information = constraint bookkeeping

**Actually Broken**
- `Verified` If I restate it as “entropy is the primitive substance,” that is already too sloppy.
- `Verified` The deeper claim is:
  \[
  \text{primitive substance}=\text{constraint on distinguishability}
  \]
  and entropy is a later admissible measure/bookkeeping on that substrate.

**Evidence**
- [Constraints.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/core_docs/a1_refined_Ratchet%20Fuel/constraint%20ladder/Constraints.md) states:
  - “There is only one kind of substance: constraint on distinguishability.”
  - “Everything else is a pattern in how that constraint is organized.”
- [ROOT_CONSTRAINT_EXTENDED_FOUNDATIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/ROOT_CONSTRAINT_EXTENDED_FOUNDATIONS.md) later gives the stronger doctrine language:
  - bounded, ordered constraint is the surviving substance
  - entropic monism is the owner doctrine term for that single-substance stance

**Next Move**
- The clean version is:

  **Entropic monism**
  \[
  \text{one primitive substance}=\text{constraint on distinguishability}
  \]

  **Entropy**
  \[
  \text{a later admissible measure of distinguishability under constraint}
  \]

- So:
  - entropic monism = doctrine name
  - constraint on distinguishability = actual primitive claim
  - entropy = later quantitative language on that claim

It means now: entropic monism in this system means one-substance constraint on distinguishability, not the sloppy claim that generic entropy is primitive.


Entropy tables


**Current Truth**
- `Verified` Yes. The content is right, but some tables got too wide and mixed display math awkwardly inside cells.
- `Verified` The fix is formatting, not substance.

**Actually Broken**
- `Verified` The worst formatting issues are:
  - multiline display equations inside narrow cells
  - repeated long equations that should be factored into named rows
  - inconsistent use of inline vs display math
  - some rows that would read better as separate smaller tables

**Evidence**
- The cleanest way to format this is:
  - keep each table narrow
  - put short equations inline in cells
  - move long equations into a block directly below the table row group when needed
  - split “entropy family,” “sign structure,” and “loop action” into separate tables

**Next Move**
- Use this cleaned version.

**State Objects**

| Object | Math | Standard name | Role |
|---|---|---|---|
| Joint state | \(\rho_{AB}\in\mathcal D(\mathbb C^2\otimes\mathbb C^2)\) | bipartite density matrix | chiral cut-state |
| Left marginal | \(\rho_A=\operatorname{Tr}_B(\rho_{AB})\) | reduced density matrix on \(A\) | subsystem state |
| Right marginal | \(\rho_B=\operatorname{Tr}_A(\rho_{AB})\) | reduced density matrix on \(B\) | subsystem state |
| Bridge | \(\Xi:(\text{geometry/history})\to \rho_{AB}\) | cut-state construction map | geometry-to-entropy interface |

**Entropy Functionals**

| Object | Math | Standard name | Role |
|---|---|---|---|
| Entropy | \(S(\rho)=-\operatorname{Tr}(\rho\log\rho)\) | von Neumann entropy | base entropy functional |
| Joint entropy | \(S(\rho_{AB})\) | entropy of the joint state | total uncertainty |
| Left marginal entropy | \(S(\rho_A)\) | entropy of reduced state \(A\) | local uncertainty |
| Right marginal entropy | \(S(\rho_B)\) | entropy of reduced state \(B\) | local uncertainty |
| Conditional entropy | \(S(A\mid B)_\rho=S(\rho_{AB})-S(\rho_B)\) | conditional entropy | signed cut entropy |
| Mutual information | \(I(A:B)_\rho=S(\rho_A)+S(\rho_B)-S(\rho_{AB})\) | mutual information | unsigned companion |
| Coherent information | \(I_c(A\rangle B)_\rho=S(\rho_B)-S(\rho_{AB})\) | coherent information | signed primitive |

**Sign Structure**

| Quantity | Sign behavior | Role |
|---|---|---|
| \(S(\rho)\) | \(\ge 0\) | unsigned entropy |
| \(I(A:B)_\rho\) | \(\ge 0\) | unsigned correlation |
| \(S(A\mid B)_\rho\) | can be \(<0,=0,>0\) | signed cut entropy |
| \(I_c(A\rangle B)_\rho\) | can be \(<0,=0,>0\) | signed primitive correlation |

**Axis 0 Layer**

| Object | Math | Standard name | Status |
|---|---|---|---|
| Kernel family | \(\Phi_0(\rho_{AB})\) | cut-state entropy family | open family |
| Preferred simple kernel | \(\Phi_0(\rho_{AB})=I_c(A\rangle B)_\rho\) | coherent-information kernel | strongest current signed candidate |
| Companion | \(I(A:B)_\rho\) | mutual-information companion | unsigned diagnostic |
| Global shell form | \(\sum_r w_r I_c(A_r\rangle B_r)_\rho\) | weighted shell-cut coherent information | stronger global candidate |

**Loop Action On Entropy**

| Object | Math | Standard name | Role |
|---|---|---|---|
| First loop channel | \(Fe(Ti(Fe(Ti(\rho_{AB}))))\) | four-step composed channel | first loop algebra |
| Second loop channel | \(Te(Fi(Te(Fi(\rho_{AB}))))\) | four-step composed channel | second loop algebra |
| Signed change under first loop | \(I_c(A\rangle B)_{Fe(Ti(Fe(Ti(\rho_{AB}))))}-I_c(A\rangle B)_\rho\) | coherent-information change | signed response |
| Signed change under second loop | \(I_c(A\rangle B)_{Te(Fi(Te(Fi(\rho_{AB}))))}-I_c(A\rangle B)_\rho\) | coherent-information change | signed response |
| Unsigned change under first loop | \(I(A:B)_{Fe(Ti(Fe(Ti(\rho_{AB}))))}-I(A:B)_\rho\) | mutual-information change | unsigned response |
| Unsigned change under second loop | \(I(A:B)_{Te(Fi(Te(Fi(\rho_{AB}))))}-I(A:B)_\rho\) | mutual-information change | unsigned response |

**Interpretation Rules**

| Statement | Math |
|---|---|
| Entropy is evaluated after the bridge | \((\text{geometry/history})\xrightarrow{\Xi}\rho_{AB}\xrightarrow{S,\ I,\ S(A\mid B),\ I_c}\text{readout}\) |
| The primitive signed quantity is coherent information | \(I_c(A\rangle B)_\rho=S(\rho_B)-S(\rho_{AB})\) |
| The unsigned companion is mutual information | \(I(A:B)_\rho=S(\rho_A)+S(\rho_B)-S(\rho_{AB})\) |
| Engine direction is read by signed change | \(\Delta I_c\) under the loop channel |

It means now: the math is fine; it just needs smaller, cleaner tables with the long expressions split into the right places.