# AXIS FOUNDATION COMPANION (Overlay-only) — v1.4

DATE_UTC: 2026-01-30T00:00:00Z  
AUTHORITY: NONCANON (overlay / rosetta only)  

**Purpose:** This file is a *Rosetta/overlay* for your axes + Jung/IGT labels.  
It is **not** Thread‑B kernel math. Thread‑B stays “plain math/QIT” with mainstream terms.

**Core rule (unchanged):**
- **Thread‑B** = admissible math objects + sims, with **no axis labels** and no bespoke language.
- **Overlay** = labels (axes/Jung/IGT/topology metaphors) that must *verify* against the Thread‑B kernel, never replace it.

---

## 0) What changed since v1.3

1) **Axis‑4 clarified (again, but sharper):**  
   Axis‑4 is a *split in operator math class* (variance‑order / collapse‑order).  
   “Loop order” is a *derived probe* (it emerges because different math classes generate different stable stage orderings).

2) **Axis‑1 × Axis‑2 clarified (again, but sharper):**  
   Axis‑1 and Axis‑2 are **not “edges”**. Their product defines **Topology4**: four orthogonal base regimes.  
   Edges/adjacency are *derived* (a graph you build on top of Topology4).

3) **Topology4 → Terrain8 pipeline made explicit:**  
   **Terrain8 = Topology4 × Flux2**, where Flux2 is the Axis‑3 “chirality/flux sign” variant.  
   Topology stays the *same* across engine types; **flux direction is what differs**.

4) Added: **S3 / Bloch / Hopf** placement as *derived geometry* (kernel‑compatible when derived, not assumed).

---

## 1) Drift hazards + locks (keep these in your face)

These are the failure modes that repeatedly cause conflation:

### H1 — “sign conflation” across multiple axes
Multiple things feel like “+ / −”:
- Axis‑3: chirality / Berry‑flux sign (topological orientation)
- Axis‑6: left‑vs‑right action / composition sidedness (operator placement)
- Axis‑0: gradient direction (entropy/correlation slope)

**Overlay lock:** never call any of these “positive/negative”.  
Use **distinct words**:
- Axis‑3 → `chirality_sign` or `flux_sign`
- Axis‑6 → `left_action` / `right_action` or `UP/DOWN` (your convention)
- Axis‑0 → `north/south` or `gradient_up/down` (your convention)

### H2 — “Axis‑4 = loop order” (wrong)
Axis‑4 is not “forward vs reverse order.”  
Axis‑4 is “**which operator math class is in play**,” and *that class* implies stable order patterns.

### H3 — “Axis‑1/2 are graph edges” (wrong)
Axis‑1/2 define **base regimes**; graph edges connect regimes later.

### H4 — letting Jung/IGT labels leak into Thread‑B
Thread‑B must remain readable by mainstream math/physics audiences.  
Jung/IGT labels live in overlay only.

---

## 2) Kernel anchors (Thread‑B-safe names you already have)

The bundle’s `MEGA_BATCHES_v1.4_...` defines these as Thread‑B terms / math-carriers:

### Topology4 (kernel form)
- `open_system_eulerian`
- `open_system_lagrangian`
- `closed_system_eulerian`
- `closed_system_lagrangian`

Also defined:
- `M_TOPOLOGY4_V1` (carrier)
- `M_VARIANCE_CLASS_INDUCTIVE_V1`
- `M_VARIANCE_CLASS_DEDUCTIVE_V1`

**Overlay note:** The old labels (Ne/Se/Ni/Si) are *not stable* yet and can be re-mapped later.  
Treat them as **aliases only**, not canon.

---

## 3) Topology4 — what it is (math-first)

Topology4 is the product of two orthogonal splits:

### Split A — system openness (channel class)
- **open_system**: system + environment coupling (CPTP / Lindblad families)
- **closed_system**: isolated evolution (unitary channel families)

### Split B — description frame (representation class)
- **eulerian**: “field / generator fixed in lab frame” description
- **lagrangian**: “co-moving / interaction-picture / trajectory-fixed” description

This yields four regimes:

1) **open_system_eulerian**  
   Typical form: Lindblad master equation in a fixed lab frame  
   - generator: fixed (time‑local), bath coupling explicit  
   - expects: stable attractors / mixing toward steady states (depending on Lindblad ops)

2) **open_system_lagrangian**  
   Typical form: interaction picture of an open system  
   - the “moving frame” absorbs part of the dynamics  
   - expects: same physics as (1), but different decomposition; useful for seeing invariants

3) **closed_system_eulerian**  
   Typical form: Schrödinger picture unitary evolution  
   - generator: Hamiltonian in lab frame  
   - expects: reversible flows on state space (no dissipation)

4) **closed_system_lagrangian**  
   Typical form: interaction picture / co-moving unitary orbit  
   - state may appear stationary while the frame evolves  
   - expects: “orbit structure” becomes the object (equivalence under gauge/frame)

**Why this matters:**  
These are *not arbitrary stage names*. They are inequivalent *mathematical regimes* you can point to in a textbook.

---

## 4) S3, Bloch sphere, Hopf tori (where they fit)

This is how “geometry shows up early” without smuggling metric/time primitives.

### Qubit geometry (derived)
- Pure qubit states are rays in ℂ².
- The set of **normalized** state vectors in ℂ² forms **S³**.
- Factoring out the physically irrelevant global phase U(1) gives **CP¹ ≅ S²** (the **Bloch sphere**).

### Hopf fibration (derived)
- The map S³ → S² with S¹ fibers is the **Hopf fibration**.
- Individual fibers are circles; preimages of circles on the Bloch sphere are embedded **tori** in S³ (Hopf/Clifford tori).
- “Nested Hopf tori” are a natural family inside S³ (vary the base circle/latitude ⇒ nested tori).

**Constraint compatibility:**  
This geometry is allowed *as derived structure* once you admit finite-dimensional Hilbert spaces + density matrices + channels (which your kernel already does).  
No metric is assumed as primitive — operational distances can be introduced later via trace distance / fidelity etc.

---

## 5) Terrain8 = Topology4 × Flux2 (the “same topology, different flow” claim)

### Flux2 (Axis‑3) = chirality / Berry‑flux sign
Your existing sim artifact `results_S_SIM_AXIS3_WEYL_HOPF_GRID_V1.json` shows:
- approximate Berry flux ≈ ±6.28315 (≈ ±2π)
- sign labeled as `chirality_plus = 1`, `chirality_minus = -1`

That’s exactly the kind of “orientation flip” you want:
- **same base surface**, opposite flux sign.

### Terrain8 (overlay metaphors)
You’ve been using metaphor names like:
- funnel ↔ cannon (influx vs outflux)
- vortex ↔ spiral
- hill ↔ citadel
- pit ↔ (the “reverse pit”, i.e. source)

**Overlay discipline:** these are *labels*, not proofs.  
They should attach to **measurable invariants** (fixed points, attractors/repellors, cycle structure, monotone sign, Berry flux sign).

### A clean way to map Terrain8 to kernel objects (candidate menu)
Treat each terrain as a **channel family** acting on a qubit Bloch ball:

- Pick 4 base channel families for Topology4 (examples below).
- For each family, define a **flux‑reversal** (chirality_sign flip) that changes the direction of the flow:
  - unitary rotation direction flip (Hamiltonian sign)
  - damping ↔ pumping (jump operator swap σ₋ ↔ σ₊)
  - etc.

**Candidate channel-family mapping (Qubit, testable):**
- Base topology A (closed eulerian): unitary rotation U = exp(-i t (n·σ))
  - flux flip: t↦-t or n↦-n
- Base topology B (open eulerian): amplitude damping (sink) / amplitude pumping (source)
  - flux flip: σ₋ ↔ σ₊
- Base topology C (open): dephasing along an axis
  - flux flip: “opposite winding” in interaction picture (candidate)
- Base topology D (open): depolarizing / isotropic contraction vs bounded expansion (candidate)

**Important:** This is a *menu of candidates*, not a commitment.  
The ratchet + sims decide which mapping survives.

---

## 6) Axis‑4 (variance‑order) — what it means operationally

Axis‑4 is the split between two operator math classes:

- **Inductive class:** “spread / explore first, then constrain”
- **Deductive class:** “constrain first, then spread / refine”

In kernel terms this is about the **order** of noncommuting operations:
- mixing / diffusion channels
- constraint / instrument / projection channels
- generator placement (left vs right action)

### Existing evidence surface (from your old sims)
In `results_S_SIM_AXIS4_SEQ_ALL_BIDIR_V1.json` (same seed/params):
- for every SEQ01..SEQ04, reversing the order **increased purity** and **decreased VN entropy** (for both Type‑1 and Type‑2 parameterizations).

Interpretation (overlay-level):
- the “reverse” order behaves like the **deductive** variance-order class in that harness.
- the “forward” order behaves like the **inductive** variance-order class in that harness.

**Crucial:** this means “loop order” is not arbitrary — it is a *symptom* of the math class.

---

## 7) Jung judging functions → operator roles (overlay mapping)

You want four “judging operators” that can be expressed in mainstream math/QIT.

A workable kernel-friendly *operator-role* basis:

1) **Constraint operator** (instrument / projection / coarse-graining)  
   - reduces degrees of freedom / collapses variance

2) **Generator operator** (Hamiltonian / Lindbladian generator / flow driver)  
   - produces structured evolution (may preserve entropy, or not, depending on class)

3) **Coupling operator** (bath coupling / mixing / diffusion)  
   - expands accessible microstates; increases variance in many regimes

4) **Selection operator** (filter / threshold / coarse equivalence class selection)  
   - chooses a stable equivalence class under probes

Now map Jung judging labels (overlay only) onto these roles:
- Ti / Te / Fi / Fe become names for the four operator roles, *not* extra ontology.

### “8 judging ops” (your requested split)
You asked for “4 base judging ops + a handedness variant”.

A clean way to do that without “positive/negative”:
- Base 4 roles (above)
- Variant = **Axis‑6 sidedness**:
  - left_action vs right_action (or UP vs DOWN)

So you get 8 operator variants:
- constraint_L / constraint_R
- generator_L / generator_R
- coupling_L / coupling_R
- selection_L / selection_R

(And **Axis‑3 chirality** is a separate split — don’t mix them.)

---

## 8) IGT loop structure (overlay; keep it testable)

What you’re asserting:

- Both engine types share the same 4 base topologies (Topology4).
- The engines differ by flux direction (Axis‑3).
- Each engine has two loops (outer/inner), and each loop visits the 4 bases.

Overlay structure (engine schematic):
- Outer loop: low impedance
- Inner loop: high impedance
- Each loop: 4 topologies
- Total: Stage8 = (outer/inner) × Topology4

Axis‑4 then shows up as:
- which loop is inductive vs deductive (variance-order class)
- and/or which direction around the 4 bases is stable in that loop

**Where this becomes testable:**  
Choose a concrete candidate mapping (Topology4 + Flux2 + Axis‑4 class), then run:
- stability tests (fixed points, attractor basins)
- entropy/purity monotone direction
- Berry flux sign consistency (if using Weyl/Hopf geometry)

---

## 9) What to do next (no new canon, just clean next steps)

1) Keep Thread‑B kernel clean:
   - ratchet only mainstream terms: open_system_eulerian, unitary, lindblad_generator, chirality, berry_phase, etc.

2) Keep overlay flexible:
   - treat Ne/Se/Ni/Si labels as provisional
   - treat funnel/vortex/citadel/etc as provisional
   - keep everything anchored to kernel tokens + sim evidence

3) Use sims to decide the mapping:
   - your existing evidence already supports the “flux sign” and “variance-order split” scaffolding.
   - next is choosing which channel families are the right Topology4 basis.

---
