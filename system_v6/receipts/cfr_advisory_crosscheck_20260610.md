# CFR advisory crosscheck 20260610

## Raw response: xAI grok-4.3

```text
P1. 384-96=288 (total emitted); per-step: |input|=|survivors|+|excluded| (conservation).

P2. \(\ln 384\) nats per erasure; total \(288\ln 384\).

P3. No (ambiguity within classes); multiplicity of assignments per class consistent with observed class counts and known survivors.

P4. Order affects tagged record (hence reconstructability) iff predicates overlap; irrelevant if disjoint.

Final answer: 384-96=288; ln384/288ln384; no (class mult.); overlap vs disjoint
```

## Raw response: Gemini 3.1 Pro Preview

```text
**P1. Relation and Conservation Identity**
*   **Exact Relation:** The total number of emitted rows equals the difference between the initial set size and the final survivor set size: $384 - 96 = 288$ total emitted rows.
*   **Per-step Conservation Identity:** For any step $i \in \{1, 2, 3\}$, let $S_{i-1}$ be the input set, $S_i$ be the survivor set, and $E_i$ be the set of excluded elements (emitted rows). The identity is: $|S_{i-1}| = |S_i| + |E_i|$, with the sets satisfying $S_{i-1} = S_i \cup E_i$ and $S_i \cap E_i = \emptyset$.

**P2. Thermodynamic Cost (Landauer)**
*   **Single Erasure:** Erasing a register holding one of 384 equiprobable states requires a minimum entropy reduction of $\ln(384)$ nats. 
*   **Total for 288 Erasures:** The total minimum thermodynamic cost is $288 \ln(384)$ nats (approximately $1713.8$ nats).

**P3. Reconstruction and Candidate Histories**
*   **Is exact reconstruction possible?** Because the 384 elements are the entire partitioned domain ($24 \times 16 = 384$), the *initial set itself* is trivially known (it is all 384 elements). However, exact reconstruction of the *exclusion history* (identifying exactly which element was excluded at which specific step) is **not possible in general**. The final 96 survivors reveal exactly *which* 288 elements were excluded, but not *when*.
*   **What determines the number of consistent candidates?** The number of valid exclusion histories is determined by the combinatorics of distributing the known excluded elements of each class among the steps that recorded that class. For each class $c$, if $E_c$ elements were excluded in total, and the record shows $k_{c,i}$ exclusions of class $c$ at step $i$, the number of consistent histories is the product of multinomial coefficients over all 24 classes: 
  $$ \prod_{c=1}^{24} \frac{|E_c|!}{k_{c,1}! \cdot k_{c,2}! \cdot k_{c,3}!} $$

**P4. Order of Filter Steps**
*   The order of the 3 filter steps affects reconstructability and the contents of the order-tagged record if and only if the exclusion predicates of the steps **overlap (intersect)** on the domain. 
*   If predicates overlap, an element satisfying multiple predicates will be excluded and logged by the *first* matching filter in the sequence, making the record highly dependent on step order. 
*   If the predicates are strictly **disjoint** (mutually exclusive), the order does not matter; each excluded element can only trigger one specific predicate, guaranteeing the same elements are logged to the same steps regardless of the sequence.
```

## Build values used after blind responses

```text
support=384
P_T=96
emitted=288
raw mismatch=0
quotient raw mismatch=48
quotient-level mismatch=0
injected defect caught=1
erasure charge=1713.7850551452655 nats
288 * ln(384) = 1713.7850551452652 nats
```

Formula check: `288 * ln(384)` matches the supplied build erasure charge to the shown precision. Both outside models confirm `ln(384)` per identity-register erasure and `288 ln(384)` total. No outside model proposed log2 of remaining live set per step, so no alternative was computed under that conditional.

## Diff table

| Item | Blind sheet | Build values | xAI | Gemini |
|---|---|---:|---|---|
| P1 total emitted | AGREE: telescoping total is `384 - |P_terminal|`; with `P_T=96`, emitted is 288. | AGREE: `384 - 96 = 288`; emitted=288. | AGREE | AGREE |
| P1 per-step conservation | AGREE: `|P_t| = |P_{t+1}| + |Delta R_t|`. | AGREE by raw mismatch=0 and emitted ledger. | AGREE | AGREE |
| P2 identity erasure charge | DIVERGE vs outside/build: blind sheet states a step-register baseline `sum_t ln |Delta R_t|`, depends on builder pin. | AGREE with outside: `288 * ln(384) = 1713.7850551452655` nats. | AGREE with build; DIVERGE from blind baseline. | AGREE with build; DIVERGE from blind baseline. |
| P3 quotient raw reconstruction | AGREE directionally: quotient class record is underdetermined inside classes; exact raw reconstruction fails unless ambiguity factor is 1. | AGREE: quotient raw mismatch=48, quotient-level mismatch=0. | AGREE: says no exact reconstruction in general. | PARTIAL/DIVERGE: says initial 384 set is trivially known, then shifts to exclusion history; does not match the build's raw-mismatch framing cleanly. |
| P3 candidate count determinant | AGREE: product of classwise combinatorial ambiguity factors using class capacities, terminal survivors, and emitted class counts. | CONSISTENT: quotient raw mismatch=48 depends on chosen predicates/counts. | AGREE but underspecified. | PARTIAL: gives a per-class multinomial over step histories, not the blind sheet's raw emitted-set ambiguity formula. |
| P4 order effect | AGREE: overlap/order can matter; disjoint predicates make order irrelevant. | No direct scalar value supplied except injected defect caught=1. | AGREE | AGREE |
| raw mismatch | Blind predicts raw reconstruction succeeds by construction. | AGREE: raw mismatch=0. | NO-ANSWER | NO-ANSWER |
| quotient raw mismatch | Blind predicts raw reconstruction fails in quotient mode unless ambiguity factor is 1; exact count depends on builder pin. | AGREE: quotient raw mismatch=48. | NO-ANSWER on value; AGREE on failure mode. | NO-ANSWER on value; PARTIAL on failure mode. |
| quotient-level mismatch | Blind expects quotient-level reconstruction succeeds. | AGREE: quotient-level mismatch=0. | NO-ANSWER | NO-ANSWER |
| injected defect caught | Blind expects injected conservation violation catch. | AGREE: injected defect caught=1. | NO-ANSWER | NO-ANSWER |

## Divergences quoted both sides

### D1: Erasure accounting

Blind sheet:

> `Q_env_total_nats = sum_t ln(2) * log2 |Delta R_t|`
> `                 = sum_t ln |Delta R_t|`
> `This total is depends_on_builder_pin through |Delta R_t|.`

Build values:

> `erasure charge=1713.7850551452655 nats`
> `288 * ln(384) = 1713.7850551452652 nats`

xAI:

> `P2. \(\ln 384\) nats per erasure; total \(288\ln 384\).`

Gemini:

> `Erasing a register holding one of 384 equiprobable states requires a minimum entropy reduction of $\ln(384)$ nats.`
> `The total minimum thermodynamic cost is $288 \ln(384)$ nats (approximately $1713.8$ nats).`

Status: unresolved DIVERGENCE between blind-sheet step-register baseline and outside/build identity-register accounting.

### D2: Gemini P3 framing

Blind sheet:

> `If the emitted record carries only quotient class IDs, raw-row reconstruction is underdetermined inside each class.`
> `N_consistent = product_i binom(n_i - l_i, m_i)`

Build values:

> `quotient raw mismatch=48`
> `quotient-level mismatch=0`

Gemini:

> `Because the 384 elements are the entire partitioned domain (24 × 16 = 384), the initial set itself is trivially known (it is all 384 elements). However, exact reconstruction of the exclusion history ... is not possible in general.`
> `The final 96 survivors reveal exactly which 288 elements were excluded, but not when.`

Status: unresolved PARTIAL/DIVERGENCE. Gemini answered a history-reconstruction reading, while the blind sheet/build values track quotient raw-row reconstruction ambiguity.

### D3: Candidate-count formula shape

Blind sheet:

> `N_consistent = product_i binom(n_i - l_i, m_i)`
> `record-only upper/count-vector form = product_i binom(n_i, m_i)`

Gemini:

> `the product of multinomial coefficients over all 24 classes:`
> `prod_c |E_c|! / (k_c,1! * k_c,2! * k_c,3!)`

xAI:

> `multiplicity of assignments per class consistent with observed class counts and known survivors.`

Status: xAI is underspecified but directionally aligned; Gemini gives a step-history allocation count, not the blind sheet's raw-set ambiguity count.
