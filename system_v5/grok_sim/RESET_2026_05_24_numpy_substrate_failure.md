# grok_sim reset — 2026-05-24 — NumPy substrate failure

> **AUTHORITATIVE EXTENSION (owner audit, 2026-05-24, post-gate):**
> the substrate-violation gate at `tools/grok_sim_substrate_violation_gate.py`
> scanned iter_283 through iter_304 and found **13 hard-block iters**
> (`iter_292`–`iter_304`), **3 adapter/control iters** (`iter_287`–`iter_289`),
> and **6 aligned-candidate sources** (`iter_283`–`iter_286`, `iter_290`,
> `iter_291`) — all with boundary-vocabulary issues that need repair.
>
> **The full audit is at `GROK_SIM_SUBSTRATE_VIOLATION_AUDIT_20260524.md` —
> that document is authoritative.** This reset doc is preserved for trail.
> The scope below is WIDER than originally declared here.

**Reset declaration:** `iter_292` through `iter_304` are quarantined as
failed substrate experiments (originally declared as `iter_300`–`iter_304`;
extended to `iter_292`–`iter_304` by owner audit). `iter_287`–`iter_289`
are adapter/control only, not root substrate. **These iterations are not
evidence; they are question-generators or negative controls only.**

## What failed

The iter chain `iter_300` → `iter_304` was run on the wrong substrate:
dense NumPy density-matrix / Kraus-channel fixtures on 4–8 qubits, with
`numpy` declared `load_bearing` in every `tool_manifest`. NumPy IS the
numeric baseline. The project spec requires at least one tool *outside*
the numeric baseline to be load-bearing. The chain violated that gate.

## Specific failures (owner audit, 2026-05-24)

1. **Boundary guard red.** Receipts carry `classification: formal_scout`
   with NumPy load-bearing depth. The repo's own
   `scripts/grok_sim_boundary_guard.py` flags this class of output.

2. **NumPy dense-matrix is not the manifold.** Density matrices may be
   admitted as *readouts* later; they are not the root geometric object.
   Root sims must be spinor/quaternion-first.

3. **Pauli/Kraus fixtures are not the manifold.** Dense Hilbert vectors
   with Pauli operators and simple Kraus channels cannot validate flux,
   Axis 0, Weyl-sheet chirality, shell time, or engine-bound topology
   mutation. They are conceptual sketches.

4. **`iter_304` hidden self-reference.** The allostatic scenario used
   `identity_engine` as regulator → σ_ref = regularize(ρ_0). That IS the
   same file's ablation A1, which I called a "bad universal rule"
   elsewhere. The "principled rule" was scenario-label-driven, not
   derived. P9 (random σ_ref fails to separate) is a negative control
   only; it does not prove the chosen rule was derived from probe/history
   evidence.

5. **`all_pass=True` over the wrong object.** Correct receipt over the
   wrong substrate is still not a correct sim.

## What is quarantined (extended per owner gate audit)

**Authoritative classification: see `GROK_SIM_SUBSTRATE_VIOLATION_AUDIT_20260524.md`**

Summary from the gate scan:

**hard_block** (question-generator-only; not evidence; not source baseline):
- iter_292 axis0_candidates_correlation_response
- iter_293 axis0_shell_partition_ladder_6qubit
- iter_294 axis0_boundary_bookkeeping_step4
- iter_295 axis0_jk_fuzz_path_entropy
- iter_296 axis0_candidates_mated_same_fixture
- iter_297 axis0_on_chiral_shell_flux_carrier
- iter_298 axis0_multi_seed_polarity_stability
- iter_299 audit_remediated_axis0_baseline
- iter_300 axis0_fep_signed_free_energy_gradient
- iter_301 peps3d_chiral_flux_axis0_fep_gradient
- iter_302 peps3d_lr_chiral_owner_controls
- iter_303 bakeoff_A0_candidates_separated_controls
- iter_304 sigma_ref_rule_candidate_A_validation

**adapter_control** (chart/readout only; Pauli/Bloch primitive or NumPy fixture):
- iter_287 layer4_real_mps_spinor_chain_quimb (pure-PyTorch fallback)
- iter_288 layer4b_peps_2d_spinor_lattice
- iter_289 layer4c_peps3d_spinor_block

**aligned_candidate** (source baseline only; receipt boundary still needs repair):
- iter_283 strict_quaternion_algebra
- iter_284 layer1_effect_algebra_laws_quaternion
- iter_285 layer2_sic_weyl_heisenberg_quaternion
- iter_286 layer3_two_site_spinor_network_quaternion
- iter_290 quaternionic_boundary_flux_chiral_shells
- iter_291 emergent_rotation_axes_time_as_ticks

All 22 iters in scope (iter_283–iter_304) have **boundary-vocabulary
issues** — they use `classification: formal_scout` and / or "formal scout"
claim-ceiling text in grok_sim receipts. That vocabulary is wrong for
grok_sim; future iters must use sidequest-local vocabulary.

These files remain in `iters/` for traceability. Their result JSONs in
`results/` are not to be cited as evidence. The `classification:
formal_scout` field in those payloads is invalid; ignore it.

## What is salvaged

Only the question, not the implementation:

> Can Axis 0 be represented as a signed QIT/FEP entropy gradient
> relative to a basin/reference selected by finite probe/history
> dynamics?

The next informal sim must test this inside the actual
spinor/quaternion/PEPS3D manifold — not as a dense-matrix toy.

## Forward discipline (binding for next informal iters)

- **PyTorch-native.** No NumPy load-bearing path.
- **No primitive Bloch / Pauli / Cartesian axes.** Spinor/quaternion
  state construction first.
- **Explicit L/R spinor or Weyl-sheet split.** Not a label on positions.
- **Dynamic spinor shells.** Shell time as I/J/K components.
- **Flux derived as engine-bound L/R spinor-shell boundary current.**
  Not assumed; emerges from network dynamics.
- **Four topology families must be actively mutated by flux/engine
  behavior.** Topology-freeze is a control, not a default.
- **Axis 0 computed as QIT/FEP signed entropy-gradient over the derived
  flux/manifold history.** Not as a standalone dense-matrix KL toy.
- **PEPS / PEPS3D used when sheets, shell topology, and boundary
  contractions are required.** Density matrices only as *admitted
  readouts* AFTER the spinor-shell network exists.
- **Regulator must be DERIVED from probe/history evidence, not declared
  by author.** Identity/self-reference is a control, not the main
  allostatic rule.

## Separation rule (reaffirmed)

- The informal grok_sim line may read formal sims as suggestions.
- Formal sims may read informal sims as suggestions.
- **Neither side may use the other's results as evidence.**
- **Neither side should write into the other's evidence surface.**
- Outputs of `iter_300`–`iter_304` especially must not be promoted; they
  violate both boundary hygiene AND substrate correctness.

## What is killed

- NumPy dense-matrix Axis 0 as evidence.
- Pauli/Kraus toy channels as manifold validation.
- `classification: formal_scout` in `grok_sim` for outputs that violate
  the substrate gate.
- Any claim that `iter_300`–`iter_304` make Candidate A load-bearing.
- Any scale claim based on 4q/8q dense Hilbert fixtures.
- Any regulator rule where the author declares the basin.

## Concrete next work (owner-directed)

1. Quarantine `iter_300`–`iter_304` (DONE — this file).
2. Write this reset doc (DONE — this file).
3. **Build a fresh PyTorch spinor-shell scout** (NOT STARTED — awaiting
   owner confirmation):
   - finite spinor states (torch tensors, autograd)
   - quaternion multiplication primitives
   - L/R sheet split (structural, not labeled)
   - dynamic shell-time update with I/J/K components
   - engine schedule (multi-substage CPTP cycle, not single-shot)
   - flux as derived L/R boundary current
   - Axis 0 as signed FEP gradient over the resulting history
4. **Add regulator-selection controls** (NOT STARTED):
   - correct regulator selected from probe/history evidence
   - wrong regulator fails
   - ambiguous multi-regulator case
   - no-fixed-point / limit-cycle / NESS case
   - identity/self-reference as control, not main allostatic rule
5. **Only after that, scale to PEPS3D** (NOT STARTED).

## Status of Candidate A math

The math definition
```
A0 = d/dλ [D(ρ(λ) || σ_ref) + C_transition]
```
may still point at the right object. But the receipts in
`iter_300`–`iter_304` are inadmissible. The math must be re-tested on
the correct substrate, with a regulator-selection rule that is derived
from probe/history evidence, before any claim about Candidate A is
load-bearing.
