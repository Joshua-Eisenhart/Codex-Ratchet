# Negative SIMs for Codex-Ratchet: Bounded Lie Brackets, Non‑commutative Limits, and Entropy Loss

## System baseline and harness behavior

The current SIM execution model is organized around a unified runner that enumerates SIM modules, executes them, and aggregates their emitted **evidence tokens** into a unified report artifact. In the active repository, that runner is implemented as `system_v4/probes/run_all_sims.py`. citeturn22view0

The runner’s output is consolidated into `system_v4/probes/a2_state/sim_results/unified_evidence_report.json`, which functions as a canonical “ledger” of PASS/KILL tokens (including per-SIM summaries and the global counts). citeturn23view0

A key design intent (already present in the codebase conceptually) is that the most durable automated checking suites do not only search for “positive witnesses” (things that should work) but also include **structured falsifiers** (things that must fail). The math research below explains why certain “pathological simplifications” are not merely implementation bugs, but **hard impossibility theorems or structural obstructions**.

## Mathematical failure modes

### Bounded Lie-algebra representations and “unit commutators”

A recurring failure mode in bounded/finite-dimensional Lie-algebraic models is attempting to realize **canonical commutation relations** with bounded operators or finite-dimensional matrices “as if” they were a faithful representation of the relevant unbounded operator algebra.

Two closely related obstructions are load-bearing:

1. **Trace obstruction (finite dimension)**  
   In finite dimensions, commutators are **traceless**: for matrices \(A,B\), \(\mathrm{Tr}([A,B]) = \mathrm{Tr}(AB-BA)=0\). This implies no finite-dimensional matrices can satisfy \([A,B]=I\) (or \(iI\)), because \(\mathrm{Tr}(I)=d\neq 0\). This trace logic is explicitly tied to canonical commutation relations in standard expositions of the Stone–von Neumann setting. citeturn16search45turn18search0

2. **Normed-algebra obstruction (bounded operators; Wintner–Wielandt style)**  
   In a unital normed algebra, the unit element cannot be a commutator of two elements—capturing the broader “boundedness” obstruction beyond finite-dimensional trace arguments. citeturn17search0turn18search3

Operationally, if a system tries to “fake” CCR-like behavior with bounded/finite-d operators, it risks one of two pathologies:  
- **silent abelianization** (the bracket collapses, losing the mechanism that generates drift), or  
- **semantic mismatch** (the model asserts an identity-bracket structure that is mathematically impossible under boundedness constraints). citeturn17search0turn16search45

### Non-commutative limits and invalid limit-swaps

Non-commutative dynamics frequently fail when a compiler/simulator **swaps operations that are not interchangeable**, such as:
- “reordering” exponentials as if operators commute, or
- truncating an infinite nested-commutator series outside its convergence/accuracy regime, or
- discarding commutators “early,” then trying to recover effects later by repetition/resummation.

The structural backbone here is the **Baker–Campbell–Hausdorff (BCH)** relationship: products of exponentials in a non-commutative algebra expand into a series involving commutators and nested commutators. Even in simplified cases, non-commutation produces extra factors, and terms like \(\tfrac12[A,B]\) are the first correction beyond the commutative approximation. citeturn15search7turn15search9

Separately, there are legitimate scaling limits where alternating exponentials converge (e.g., the **Trotter product formula**)—but importantly, the correctness conditions are subtle, and “just commute it” is not a valid transformation. citeturn19search0turn19search3

A practical, compiler-relevant failure mode is the **invalid limit swap**:
- take \(\varepsilon\to 0\) first (making a commutator cycle look like identity),  
- then take \(N\to\infty\) by repetition, expecting the same macroscopic effect as if one had kept the non-commutative second-order terms.  
This is exactly the kind of “non-commutative limit” pathology that negative tests should pin down. citeturn15search7turn19search0

### Entropy loss, hidden sinks, and “free purification”

Entropy-related pathologies typically arise from one of three moves:

- **Assuming reversible/unitary-only dynamics can create an entropy gradient** that produces net work/solvency without exporting entropy. This clashes with the basic thermodynamic insight that information erasure (or systematic reduction of uncertainty) has a physical cost in general. citeturn15search8

- **Treating unital mixing as if it can reduce entropy.** For bistochastic (trace-preserving + unital) quantum operations, von Neumann entropy is nondecreasing; this is the quantum analogue of classical doubly-stochastic mixing. citeturn20search6turn21search6

- **Using trace-decreasing maps (postselection) but accounting as if they were trace-preserving.** Postselection can “purify” conditionally, but the cost is hidden in the exponentially shrinking success probability / discarded probability mass. That is an information-theoretic cost, and it is not a free physical entropy erasure. citeturn15search8

These are exactly the kinds of “entropy loss” failure modes that negative SIMs should encode as KILL conditions, because they represent either (a) an impossibility theorem, or (b) a silent mathematical cheat (e.g., non-CPTP behavior smuggled in as if CPTP).

## Negative SIM design principles for this system

A robust Negative SIM in this harness should do three things:

1. **Name a specific hypothesis-to-kill** (a crisp statement that is false under the intended semantics).
2. **Force a pathological condition** (boundedness, commutative collapse, truncation, postselection without cost-accounting), rather than waiting for accidental emergence.
3. **Emit a structured KILL witness** (stable `kill_reason`, reproducible parameterization, and a measured value demonstrating the obstruction).

The existing unified reporting infrastructure is already capable of capturing and aggregating KILL tokens across SIMs into a single ledger artifact (the unified evidence report). citeturn23view0turn22view0

## Five new Negative SIMs designed to fail

These five new Negative SIMs are engineered to “prove the math” by producing KILL tokens only when the targeted pathology is enforced. Each one maps directly to a research-backed failure mode above.

### Bounded commutator cannot equal identity

**SIM file:** `neg_bounded_commutator_identity_sim.py`  
**Core pathology:** bounded/finite-dimensional attempt to realize a “unit commutator” \([A,B]=I\).  
**Why it must fail:** finite-dimensional commutators are traceless; more generally, the unit in a normed algebra cannot be a commutator. citeturn18search0turn17search0turn16search45  
**KILL reason:** `BOUNDED_COMMUTATOR_CANNOT_BE_IDENTITY`  
**What it protects:** prevents a compiler or simulator from “encoding noncommutation” by asserting impossible bounded brackets.

### Unital-only entropy cannot decrease

**SIM file:** `neg_unital_only_entropy_monotone_sim.py`  
**Core pathology:** assuming unital/bistochastic dynamics can reduce von Neumann entropy and thereby create solvency.  
**Why it must fail:** bistochastic quantum operations do not decrease von Neumann entropy. citeturn20search6turn21search6  
**KILL reason:** `UNITAL_CHANNELS_CANNOT_DECREASE_ENTROPY`  
**What it protects:** catches hidden non-unital “sinks” or normalization bugs that masquerade as lawful entropy reduction.

### BCH truncation failure outside small-step regime

**SIM file:** `neg_bch_truncation_failure_sim.py`  
**Core pathology:** treating noncommuting exponentials as if low-order BCH truncations are globally valid.  
**Why it must fail:** BCH is an infinite nested-commutator series; low-order truncations are only accurate in “small step” regimes or special algebraic structures. citeturn15search7turn15search9  
**KILL reason:** `BCH_TRUNCATION_BREAKS_OUTSIDE_RADIUS`  
**What it protects:** prevents “truncate-to-commute” compiler behaviors that silently destroy the noncommutative geometry.

### Commutator-cycle scaling limit collapses under forced commutativity

**SIM file:** `neg_noncommutative_commutator_cycle_limit_sim.py`  
**Core pathology:** discarding commutator cycles in the commutative limit and expecting resummation/repetition to restore the same drift.  
**Why it must fail:** if \([A,B]=0\), the group commutator cycle is the identity exactly; no repetition recovers bracket drift. This is BCH-structure logic applied to a scaling experiment. citeturn15search7turn19search0  
**KILL reason:** `COMMUTATIVE_LIMIT_ERASES_BRACKET_DRIFT`  
**What it protects:** blocks invalid limit-swaps of the form “\(\varepsilon\to 0\)” before “\(N\to\infty\)” in noncommutative constructions.

### Postselection “free purification” hides cost in trace

**SIM file:** `neg_postselection_trace_leak_entropy_sim.py`  
**Core pathology:** repeated projection + renormalization treated as a free physical entropy eraser.  
**Why it must fail:** conditional purification via postselection is trace-decreasing; ignoring the success probability hides a real informational/thermodynamic cost, consistent with the insight behind Landauer-style accounting. citeturn15search8  
**KILL reason:** `POSTSELECTION_ERASURE_COST_HIDDEN_IN_TRACE`  
**What it protects:** catches entropy-loss cheats that rely on non-CPTP postselection being treated as CPTP.

## Deliverables and repository integration status

The deliverables (5 new `_sim.py` files + 5 YAML `problem_specs` with `target_status: KILL`) have been prepared as an offline bundle:

[Download Autopoietic Hub Negative SIMs bundle](sandbox:/mnt/data/Autopoietic_Hub_Negative_SIMS_bundle.zip)

Inside the bundle:
- `system_v4/probes/` contains the five new Negative SIMs.
- `system_v4/research/problem_specs/` contains five YAML specs, each with `target_status: KILL`.
- `INTEGRATION_NOTES.md` describes exactly where to register these SIMs in the unified runner (`run_all_sims.py`) and the expected output JSON filenames.

Direct push/commit to entity["company","GitHub","code hosting platform"] is not available from the connector toolset exposed in this session (all available GitHub connector operations are read-only), so the repository update is provided as a bundle to apply. citeturn22view0turn23view0