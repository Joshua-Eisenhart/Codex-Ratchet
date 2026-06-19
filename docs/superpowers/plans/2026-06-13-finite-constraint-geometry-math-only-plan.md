# Finite Constraint Geometry Math-Only Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build finite-dimensional state spaces, explicit maps, quotient sets, graph/cell-complex structures, curvature or entropy observables, and trajectory readouts without using project nicknames as mathematical inputs.

**Architecture:** Every packet must declare a finite index set `I`, a finite-dimensional Hilbert space `H`, density matrices `rho_i in D(H)`, maps `E_j: D(H) -> D(H)` or explicitly partial maps with domains, quotient maps `q: I -> Q`, graph or cell-complex structure, observables, and controls. Multi-qubit work must also declare an inverse system: finite survivor sets `X_A subset D(H_A)` for nonempty subsystems `A`, projection maps `p_{A,B} = Tr_{A\B}` for `B subset A`, and compatibility relations `q_B(p_{A,B}(rho_A)) = q_B(rho_B)`. Project-facing words may appear only in a quarantine field named `legacy_project_labels`; they may not appear in formulas, executable keys, validator logic, or pass rules.

**Tech Stack:** Python/JAX, Julia, PyTorch, pytest, repo validators, `scripts/gcm_substrate_check.py`, `scripts/validate_three_engine_sim_result.py`, z3/cvc5 for finite constraints, sympy for symbolic identities, and packet-local validators.

---

## Non-Negotiable Language Rule

Mathematical inputs and outputs must use only standard mathematical names:

```text
finite set
Hilbert space
vector
density matrix
partial trace
partial transpose
eigenvalue
entropy
mutual information
channel
Kraus operator
GKSL generator
unitary
quotient set
equivalence relation
graph
cell complex
connection 1-form
curvature 2-form
holonomy
trajectory
transition matrix
observable
```

The following words are not allowed in computational JSON keys, pass rules, formulas, test names, or validator branch names:

```text
terrain
engine
axis
stage
runtime
shell
flux
readout-name labels from the project vocabulary
```

Those words may appear only in:

```json
{
  "legacy_project_labels": ["labels for human cross-reference only"],
  "legacy_paths": ["pre-existing repo paths whose names cannot be changed in this packet"]
}
```

If a validator finds a banned word outside those quarantine fields, the packet fails.

## Current Mathematical Baseline

Use these existing paths only for their explicit mathematical artifacts:

| Existing path | Mathematical object to consume | Claim ceiling |
|---|---|---|
| `system_v6/sims/gcm_constraint_carve_v1/` | finite 1-qubit candidate set and constraints | scratch evidence |
| `system_v6/sims/gcm_object_id_freeze_v0/` | stable IDs and hashes for the 1-qubit finite object | scratch evidence |
| `system_v6/sims/gcm_geometry_attach_v0/` | maps from IDs to spinors, density matrices, Bloch coordinates | scratch evidence |
| `system_v6/sims/gcm_connection_flux_attach_v0/` | Hopf connection 1-form and curvature 2-form on pure 1-qubit states | scratch evidence |
| `system_v6/sims/gcm_flux_strips_v0/` | strip integrals of the Hopf curvature 2-form | scratch evidence |
| `system_v6/sims/gcm_entropy_family_sweep_v0/` | entropy functions on 1-qubit density matrices | scratch evidence |
| `system_v6/sims/gcm_ring_checkerboard_runner_v1/` | finite transition tables on existing IDs | scratch evidence |
| `system_v6/sims/gcm_constraint_carve_2q_v0/` | finite 2-qubit candidate set and constraints | scratch evidence |
| `system_v6/sims/gcm_geometry_attach_2q_v0/` | provisional 2-qubit geometry; must be rebuilt from density matrices | scratch evidence |
| `system_v6/sims/gcm_ratchet_order_matrix_v0/` | measured noncommutation/order checks for some prior maps | scratch evidence |

Dirty or untracked surfaces at plan creation:

```text
scripts/gcm_substrate_check.py
system_v6/sims/gcm_2q_freeze_and_cut_v0/
system_v6/sims/gcm_ratchet_order_matrix_v1/
system_v6/sims/engine_16_stage_definition_correspondence_v0/
system_v6/sims/manifold_dynamic_chart_v2/
```

The last two paths contain legacy names. They are not valid mathematical sources unless a packet extracts explicit maps, states, observables, and controls from them.

## File Structure

- Create: `system_v6/docs/math_only_packet_contract.md`  
  Responsibility: define the allowed schema for finite state, map, quotient, graph, curvature, entropy, and trajectory packets.

- Create: `scripts/validate_math_only_packet.py`  
  Responsibility: reject computational fields containing project nicknames outside `legacy_project_labels` and `legacy_paths`.

- Modify: `scripts/gcm_substrate_check.py`  
  Responsibility: accept 1-qubit and 2-qubit substrate IDs only when registry hashes and lineage fields match the frozen objects.

- Finish: `system_v6/sims/gcm_2q_freeze_and_cut_v0/`  
  Responsibility: freeze a finite 2-qubit object with density matrices, partial traces, partial transpose spectra, quotient maps, and product/entangled controls.

- Create: `system_v6/sims/gcm_entropy_cut_sweep_2q_v0/`  
  Responsibility: compute entropy and information quantities on the frozen 2-qubit object.

- Create: `system_v6/sims/gcm_geometry_attach_2q_v1/`  
  Responsibility: compute actual-state-derived 2-qubit geometry from density matrices.

- Create: `system_v6/sims/gcm_inverse_system_compatibility_v0/`  
  Responsibility: test that accepted higher-qubit density matrices project by partial trace to accepted lower-qubit equivalence classes.

- Create: `system_v6/sims/gcm_order_matrix_explicit_maps_v1/`  
  Responsibility: compute order dependence for named standard maps: dephasing, unitary rotations, partial traces, quotient maps, and finite transition maps.

- Create: `system_v6/sims/gcm_hopf_curvature_under_maps_v0/`  
  Responsibility: test when Hopf connection/curvature quantities are defined after a map, and when a mixed-state connection is required.

- Create: `system_v6/sims/gcm_region_discovery_from_observables_v0/`  
  Responsibility: discover subsets of the finite index set from inequalities, graph components, or cell-complex membership.

- Create: `system_v6/sims/gcm_map_residency_on_regions_v0/`  
  Responsibility: test whether explicit maps preserve, leave, or mix computed regions.

- Create: `system_v6/sims/gcm_transition_trajectories_v0/`  
  Responsibility: run finite trajectories from explicit transition matrices or CPTP maps.

- Create: `system_v6/sims/gcm_3q_state_space_v0/`  
  Responsibility: define `H = (C^2)^{tensor 3}`, compute tripartite invariants, and test compatibility with all 1-qubit and 2-qubit projections.

- Create: `system_v6/sims/gcm_downstream_observables_on_trajectories_v0/`  
  Responsibility: compute scalar/vector functions over trajectories after the transition system exists.

- Create: `system_v6/receipts/gcm_math_only_execution_ledger_20260613.md`  
  Responsibility: record every accepted packet by mathematical object, result path, audit path, ceiling, and blocked consumer.

---

### Task 1: Install A Math-Only Packet Guard

**Files:**
- Create: `system_v6/docs/math_only_packet_contract.md`
- Create: `scripts/validate_math_only_packet.py`

- [ ] **Step 1: Write the contract**

Create `system_v6/docs/math_only_packet_contract.md` with:

```markdown
# Math-Only Packet Contract

Every claim-bearing packet must expose explicit mathematical objects.

Required top-level fields:

- `packet_id`
- `classification`
- `promotion_allowed`
- `formal_admission_allowed`
- `finite_index_set`
- `subsystems`
- `hilbert_space`
- `state_family`
- `maps`
- `projection_maps`
- `compatibility_relations`
- `quotients`
- `graphs_or_cell_complexes`
- `observables`
- `controls`
- `source_registry_hashes`
- `legacy_project_labels`
- `legacy_paths`
- `blocked_consumers`

Project labels are cross-reference text only. They may not determine formulas,
test names, branch names, validator logic, or pass rules.
```

- [ ] **Step 2: Write the validator**

Create `scripts/validate_math_only_packet.py`:

```python
#!/usr/bin/env python3
import json
import sys
from pathlib import Path

BANNED = {
    "terrain",
    "engine",
    "axis",
    "stage",
    "runtime",
    "shell",
    "flux",
}

QUARANTINE_KEYS = {"legacy_project_labels", "legacy_paths"}


def walk(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = path + (str(key),)
            yield child_path, key
            yield from walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, path + (str(index),))
    elif isinstance(value, str):
        yield path, value


def in_quarantine(path):
    return any(part in QUARANTINE_KEYS for part in path)


def find_violations(data):
    violations = []
    for path, text in walk(data):
        if in_quarantine(path):
            continue
        lowered = str(text).lower()
        for word in BANNED:
            if word in lowered:
                violations.append({"path": ".".join(path), "word": word, "text": str(text)})
    return violations


def main(argv):
    if len(argv) != 2:
        print(json.dumps({"ok": False, "error": "usage: validate_math_only_packet.py <result.json>"}))
        return 2
    path = Path(argv[1])
    data = json.loads(path.read_text())
    violations = find_violations(data)
    print(json.dumps({"ok": not violations, "violations": violations}, indent=2, sort_keys=True))
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
```

- [ ] **Step 3: Test the validator**

Run:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
import json
from pathlib import Path

good = {
    "packet_id": "demo",
    "state_family": [{"density_matrix": [[1, 0], [0, 0]]}],
    "legacy_project_labels": ["axis allowed here"],
    "legacy_paths": ["system_v6/sims/engine_legacy_name/"]
}
bad = {
    "packet_id": "demo",
    "maps": [{"engine_stage": "bad key"}]
}
Path("/tmp/math_only_good.json").write_text(json.dumps(good))
Path("/tmp/math_only_bad.json").write_text(json.dumps(bad))
PY
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_math_only_packet.py /tmp/math_only_good.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_math_only_packet.py /tmp/math_only_bad.json
```

Expected:

```text
good JSON returns ok true.
bad JSON returns ok false and reports word "engine".
```

- [ ] **Step 4: Commit**

```bash
git add system_v6/docs/math_only_packet_contract.md scripts/validate_math_only_packet.py
git commit -m "add math-only packet language guard"
```

### Task 2: Stabilize Current Dirty State

**Files:**
- Inspect: `scripts/gcm_substrate_check.py`
- Inspect: `system_v6/sims/gcm_2q_freeze_and_cut_v0/`
- Inspect: `system_v6/sims/gcm_ratchet_order_matrix_v1/`
- Inspect only: `system_v6/sims/engine_16_stage_definition_correspondence_v0/`
- Inspect only: `system_v6/sims/manifold_dynamic_chart_v2/`

- [ ] **Step 1: Record exact dirty state**

```bash
git status --short
git diff -- scripts/gcm_substrate_check.py
find system_v6/sims/gcm_2q_freeze_and_cut_v0 -maxdepth 3 -type f | sort
find system_v6/sims/gcm_ratchet_order_matrix_v1 -maxdepth 3 -type f | sort
```

Expected:

```text
modified helper is visible.
2-qubit freeze/cut packet files are visible.
order-matrix v1 packet files are visible or the packet is marked incomplete.
legacy-named directories are not used as mathematical evidence yet.
```

- [ ] **Step 2: Run existing 2-qubit validator without edits**

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_2q_freeze_and_cut_v0/validate_gcm_2q_freeze_and_cut_v0.py
```

Expected:

```text
Either ok true, or exact failing fields are written into system_v6/sims/gcm_2q_freeze_and_cut_v0/audit_blocker.md before further edits.
```

- [ ] **Step 3: Test helper against positive and negative lineage**

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
import json
from pathlib import Path
from scripts.gcm_substrate_check import gcm_substrate_check

root = Path("/Users/joshuaeisenhart/Codex-Ratchet")
good = json.loads((root / "system_v6/sims/gcm_2q_freeze_and_cut_v0/results/gcm_2q_freeze_and_cut_v0_envelope_results.json").read_text())
bad = json.loads((root / "system_v6/sims/gcm_2q_freeze_and_cut_v0/results/gcm_2q_freeze_and_cut_v0_lineage_free_negative.json").read_text())

print({"good": gcm_substrate_check(good)})
print({"bad": gcm_substrate_check(bad)})
PY
```

Expected:

```text
good returns ok true.
bad returns ok false.
```

- [ ] **Step 4: Commit helper only if green**

```bash
git add scripts/gcm_substrate_check.py
git diff --cached -- scripts/gcm_substrate_check.py
git commit -m "gcm substrate checker accepts 2-qubit lineage"
```

### Task 3: Freeze The 2-Qubit Finite Object

**Files:**
- Modify: `system_v6/sims/gcm_2q_freeze_and_cut_v0/gcm_2q_freeze_and_cut_v0_common.py`
- Modify: `system_v6/sims/gcm_2q_freeze_and_cut_v0/gcm_2q_freeze_and_cut_v0_jax.py`
- Modify: `system_v6/sims/gcm_2q_freeze_and_cut_v0/gcm_2q_freeze_and_cut_v0_julia.jl`
- Modify: `system_v6/sims/gcm_2q_freeze_and_cut_v0/gcm_2q_freeze_and_cut_v0_pytorch.py`
- Modify: `system_v6/sims/gcm_2q_freeze_and_cut_v0/validate_gcm_2q_freeze_and_cut_v0.py`
- Create: `system_v6/sims/gcm_2q_freeze_and_cut_v0/audit_verdict.md`

- [ ] **Step 1: Require this result schema**

The envelope result must contain:

```json
{
  "packet_id": "gcm_2q_freeze_and_cut_v0",
  "classification": "scratch_diagnostic",
  "promotion_allowed": false,
  "formal_admission_allowed": false,
  "finite_index_set": {
    "name": "I_2",
    "cardinality": 544,
    "id_field": "state_id"
  },
  "hilbert_space": {
    "field": "complex",
    "dimension": 4,
    "factorization": [2, 2]
  },
  "state_family": {
    "state_type": "density_matrix",
    "trace_required": 1.0,
    "positive_semidefinite_required": true
  },
  "observables": [
    "trace",
    "min_eigenvalue",
    "rank",
    "purity",
    "partial_trace_A",
    "partial_trace_B",
    "partial_transpose_eigenvalues",
    "negativity"
  ],
  "quotients": [
    "exact_density_matrix_hash",
    "local_spectrum_pair",
    "product_or_not_product"
  ],
  "controls": {
    "product_state_negativity_zero": true,
    "bell_state_negativity_positive": true,
    "lineage_removed_fails": true
  },
  "legacy_project_labels": [],
  "legacy_paths": []
}
```

- [ ] **Step 2: Verify density matrices**

Run:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
import json
import numpy as np
from pathlib import Path

p = Path("system_v6/sims/gcm_2q_freeze_and_cut_v0/results/gcm_2q_freeze_and_cut_v0_envelope_results.json")
data = json.loads(p.read_text())
bad = []
for row in data["state_family"]["rows"]:
    rho = np.array(row["density_matrix"], dtype=np.complex128)
    trace_ok = abs(np.trace(rho) - 1) < 1e-10
    herm_ok = np.linalg.norm(rho - rho.conj().T) < 1e-10
    eig_ok = np.min(np.linalg.eigvalsh(rho)) >= -1e-10
    if not (trace_ok and herm_ok and eig_ok):
        bad.append(row["state_id"])
print({"bad_count": len(bad), "bad_ids": bad[:10]})
raise SystemExit(1 if bad else 0)
PY
```

Expected:

```text
bad_count is 0.
```

- [ ] **Step 3: Run validators**

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_2q_freeze_and_cut_v0/validate_gcm_2q_freeze_and_cut_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_math_only_packet.py system_v6/sims/gcm_2q_freeze_and_cut_v0/results/gcm_2q_freeze_and_cut_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/gcm_2q_freeze_and_cut_v0/results/gcm_2q_freeze_and_cut_v0_envelope_results.json
```

Expected:

```text
all validators return ok true.
```

- [ ] **Step 4: Write audit verdict**

Create `system_v6/sims/gcm_2q_freeze_and_cut_v0/audit_verdict.md` with:

```markdown
# Audit Verdict

Accepted ceiling: scratch_diagnostic.

What exists:
- finite set `I_2`;
- `H = C^4`;
- density matrices `rho_i`;
- partial traces `rho_A`, `rho_B`;
- partial transpose spectra;
- negativity;
- quotient maps from explicit invariants.

What does not exist:
- no discovered region law;
- no finite transition system;
- no trajectory readout;
- no claim that a project-facing label has been simulated.
```

- [ ] **Step 5: Commit**

```bash
git add system_v6/sims/gcm_2q_freeze_and_cut_v0/
git commit -m "freeze 2-qubit finite object with cut observables"
```

### Task 4: Compute 2-Qubit Entropy And Information Quantities

**Files:**
- Create: `system_v6/sims/gcm_entropy_cut_sweep_2q_v0/`

- [ ] **Step 1: Implement these observables**

For each `rho_AB in D(C^2 tensor C^2)`, compute:

```text
rho_A = Tr_B(rho_AB)
rho_B = Tr_A(rho_AB)
S_AB = -Tr(rho_AB log rho_AB)
S_A = -Tr(rho_A log rho_A)
S_B = -Tr(rho_B log rho_B)
I_AB = S_A + S_B - S_AB
S_A_given_B = S_AB - S_B
S_B_given_A = S_AB - S_A
I_coherent_A_to_B = S_B - S_AB
I_coherent_B_to_A = S_A - S_AB
negativity = (||rho_AB^(T_B)||_1 - 1) / 2
```

- [ ] **Step 2: Add controls**

Required controls:

```text
rho_AB = rho_A tensor rho_B gives I_AB = 0 and negativity = 0.
Bell state gives S_AB = 0, S_A = S_B = log(2), I_AB = 2 log(2), negativity = 1/2.
maximally mixed state I_4/4 gives S_AB = 2 log(2), S_A = S_B = log(2), I_AB = 0.
```

- [ ] **Step 3: Validate**

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/gcm_entropy_cut_sweep_2q_v0/tests -q
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_entropy_cut_sweep_2q_v0/validate_gcm_entropy_cut_sweep_2q_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_math_only_packet.py system_v6/sims/gcm_entropy_cut_sweep_2q_v0/results/gcm_entropy_cut_sweep_2q_v0_envelope_results.json
```

- [ ] **Step 4: Commit**

```bash
git add system_v6/sims/gcm_entropy_cut_sweep_2q_v0/
git commit -m "compute 2-qubit entropy and information quantities"
```

### Task 5: Rebuild 2-Qubit Geometry From Density Matrices

**Files:**
- Create: `system_v6/sims/gcm_geometry_attach_2q_v1/`

- [ ] **Step 1: Compute actual-state-derived quantities**

For each `rho_AB`, compute:

```text
r_A[i] = Tr(rho_AB (sigma_i tensor I))
r_B[j] = Tr(rho_AB (I tensor sigma_j))
T[i,j] = Tr(rho_AB (sigma_i tensor sigma_j))
eigenvalues(rho_AB)
eigenvalues(rho_A)
eigenvalues(rho_B)
purity_AB = Tr(rho_AB^2)
purity_A = Tr(rho_A^2)
purity_B = Tr(rho_B^2)
trace_distance(rho_m, rho_n) = 1/2 ||rho_m - rho_n||_1
Bures_distance(rho_m, rho_n)
```

- [ ] **Step 2: Reject scalar-only geometry**

The validator must fail if the result lacks:

```text
the full 4x4 density matrix;
both 2x2 reduced density matrices;
the 3-vector r_A;
the 3-vector r_B;
the 3x3 correlation matrix T;
at least one pairwise metric or distance matrix.
```

- [ ] **Step 3: Validate**

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/gcm_geometry_attach_2q_v1/tests -q
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_geometry_attach_2q_v1/validate_gcm_geometry_attach_2q_v1.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_math_only_packet.py system_v6/sims/gcm_geometry_attach_2q_v1/results/gcm_geometry_attach_2q_v1_envelope_results.json
```

- [ ] **Step 4: Commit**

```bash
git add system_v6/sims/gcm_geometry_attach_2q_v1/
git commit -m "compute 2-qubit geometry from density matrices"
```

### Task 6: Build The Finite Inverse-System Compatibility Check

**Files:**
- Create: `system_v6/sims/gcm_inverse_system_compatibility_v0/`

- [ ] **Step 1: Define the mathematical object**

For active subsystem family `S = {{0}, {1}, {0,1}}`, define:

```text
H_{0} = C^2
H_{1} = C^2
H_{0,1} = C^2 tensor C^2
X_{0} subset D(H_{0})
X_{1} subset D(H_{1})
X_{0,1} subset D(H_{0,1})
p_{{0,1},{0}}(rho_01) = Tr_1(rho_01)
p_{{0,1},{1}}(rho_01) = Tr_0(rho_01)
q_0: D(H_0) -> Q_0
q_1: D(H_1) -> Q_1
```

Compatibility means:

```text
q_0(p_{{0,1},{0}}(rho_01)) = q_0(rho_0)
q_1(p_{{0,1},{1}}(rho_01)) = q_1(rho_1)
```

The first version may use exact density-matrix hashes or active Pauli-probe vectors for `q_0` and `q_1`, but it must record which quotient was used.

- [ ] **Step 2: Require this result schema**

The envelope result must contain:

```json
{
  "packet_id": "gcm_inverse_system_compatibility_v0",
  "classification": "scratch_diagnostic",
  "promotion_allowed": false,
  "formal_admission_allowed": false,
  "subsystems": [
    {"name": "0", "hilbert_space_dimension": 2},
    {"name": "1", "hilbert_space_dimension": 2},
    {"name": "0,1", "hilbert_space_dimension": 4}
  ],
  "projection_maps": [
    {"name": "p_01_to_0", "formula": "Tr_1(rho_01)", "domain": "D(C^2 tensor C^2)", "codomain": "D(C^2)"},
    {"name": "p_01_to_1", "formula": "Tr_0(rho_01)", "domain": "D(C^2 tensor C^2)", "codomain": "D(C^2)"}
  ],
  "compatibility_relations": [
    {"name": "compat_01_0", "formula": "q_0(Tr_1(rho_01)) == q_0(rho_0)"},
    {"name": "compat_01_1", "formula": "q_1(Tr_0(rho_01)) == q_1(rho_1)"}
  ],
  "extension_fibers": [
    {"lower_state_id": "must be a real lower survivor ID", "higher_state_ids": ["must contain real compatible 2-qubit survivor IDs"]}
  ],
  "controls": {
    "product_extension_passes": true,
    "perturbed_marginal_fails": true,
    "missing_lower_id_fails": true,
    "lineage_removed_fails": true
  },
  "legacy_project_labels": [],
  "legacy_paths": []
}
```

- [ ] **Step 3: Implement positive and negative cases**

Positive case:

```text
rho_01 = rho_0 tensor rho_1
Tr_1(rho_01) = rho_0
Tr_0(rho_01) = rho_1
```

Negative cases:

```text
replace rho_0 with a different accepted one-qubit density matrix;
remove the lower registry hash;
round one marginal beyond the accepted quotient tolerance;
use a two-qubit row whose partial trace has no lower survivor class.
```

- [ ] **Step 4: Validate**

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/gcm_inverse_system_compatibility_v0/tests -q
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_inverse_system_compatibility_v0/validate_gcm_inverse_system_compatibility_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_math_only_packet.py system_v6/sims/gcm_inverse_system_compatibility_v0/results/gcm_inverse_system_compatibility_v0_envelope_results.json
```

Expected:

```text
all validators return ok true.
negative controls are present in the result JSON.
```

- [ ] **Step 5: Commit**

```bash
git add system_v6/sims/gcm_inverse_system_compatibility_v0/
git commit -m "test finite inverse-system compatibility"
```

### Task 7: Build An Explicit Map Library And Order Matrix

**Files:**
- Create: `system_v6/sims/gcm_order_matrix_explicit_maps_v1/`

- [ ] **Step 1: Define only standard maps**

Allowed maps:

```text
D_z^lambda(rho) = (1-lambda) E_z(rho) + lambda rho
D_x^lambda(rho) = (1-lambda) E_x(rho) + lambda rho
U_z^theta(rho) = exp(-i theta sigma_z / 2) rho exp(i theta sigma_z / 2)
U_x^theta(rho) = exp(-i theta sigma_x / 2) rho exp(i theta sigma_x / 2)
Tr_A(rho_AB)
Tr_B(rho_AB)
q_k: I -> Q_k for each explicit quotient
P_G: finite graph projection when a graph exists
```

No other map may be used unless the packet defines:

```text
domain;
codomain;
Kraus operators or generator;
complete-positivity check;
trace-preservation check;
negative/control condition.
```

- [ ] **Step 2: Compute noncommutation**

For every ordered pair `(A, B)` with matching domain/codomain:

```text
delta(A,B,rho) = norm(A(B(rho)) - B(A(rho)))
```

If domains do not match, record:

```json
{"pair_status": "not_composable"}
```

- [ ] **Step 3: Validate**

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/gcm_order_matrix_explicit_maps_v1/tests -q
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_order_matrix_explicit_maps_v1/validate_gcm_order_matrix_explicit_maps_v1.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_math_only_packet.py system_v6/sims/gcm_order_matrix_explicit_maps_v1/results/gcm_order_matrix_explicit_maps_v1_envelope_results.json
```

- [ ] **Step 4: Commit**

```bash
git add system_v6/sims/gcm_order_matrix_explicit_maps_v1/
git commit -m "compute order matrix for explicit maps"
```

### Task 8: Test Curvature And Holonomy Under Maps

**Files:**
- Create: `system_v6/sims/gcm_hopf_curvature_under_maps_v0/`

- [ ] **Step 1: Use formal differential geometry**

On pure one-qubit spinors:

```text
psi(phi, chi, eta)
  = [exp(i(phi+chi)) cos eta,
     exp(i(phi-chi)) sin eta]^T

A = -i psi^dagger d psi
F = dA
holonomy(gamma) = integral_gamma A
surface_integral(Sigma) = integral_Sigma F
```

- [ ] **Step 2: Classify map output domain**

For each explicit map `E`:

```text
if E(rho) is rank 1 for all tested pure inputs:
  connection_status = "pure_state_connection_defined"
elif a purification rule P(E(rho)) is explicitly supplied:
  connection_status = "purified_connection_defined"
else:
  connection_status = "not_defined_on_mixed_output"
```

- [ ] **Step 3: Controls**

```text
identity map preserves holonomy.
unitary map on pure states preserves pure-state definability.
full dephasing sends generic pure states to mixed states and must not report a pure-state connection unless a purification rule is supplied.
```

- [ ] **Step 4: Validate and commit**

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/gcm_hopf_curvature_under_maps_v0/tests -q
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_hopf_curvature_under_maps_v0/validate_gcm_hopf_curvature_under_maps_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_math_only_packet.py system_v6/sims/gcm_hopf_curvature_under_maps_v0/results/gcm_hopf_curvature_under_maps_v0_envelope_results.json
git add system_v6/sims/gcm_hopf_curvature_under_maps_v0/
git commit -m "classify Hopf curvature under explicit maps"
```

### Task 9: Discover Regions From Observables

**Files:**
- Create: `system_v6/sims/gcm_region_discovery_from_observables_v0/`

- [ ] **Step 1: Define regions only by formulas**

A region is a subset `R subset I_2` defined by one of:

```text
R = {i in I_2 : f(i) <= c}
R = {i in I_2 : c1 <= f(i) <= c2}
R = connected_component(G, v)
R = cell_membership(K, cell_id)
R = equivalence_class(q, value)
```

Each output row must include:

```json
{
  "region_id": "R_000",
  "definition_type": "inequality",
  "formula": "negativity(i) > 0",
  "member_state_ids": [],
  "boundary_edges": []
}
```

- [ ] **Step 2: Allow empty discovery**

The validator must accept:

```text
region_count = 0
```

if no formula-defined subset passes the controls.

- [ ] **Step 3: Validate and commit**

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/gcm_region_discovery_from_observables_v0/tests -q
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_region_discovery_from_observables_v0/validate_gcm_region_discovery_from_observables_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_math_only_packet.py system_v6/sims/gcm_region_discovery_from_observables_v0/results/gcm_region_discovery_from_observables_v0_envelope_results.json
git add system_v6/sims/gcm_region_discovery_from_observables_v0/
git commit -m "discover finite regions from observables"
```

### Task 10: Test Map Residency On Computed Regions

**Files:**
- Create: `system_v6/sims/gcm_map_residency_on_regions_v0/`

- [ ] **Step 1: Define residency**

For map `E_j` and region `R_k`:

```text
preserved_count = |{i in R_k : E_j(rho_i) maps to a state in R_k}|
escaped_count = |{i in R_k : E_j(rho_i) maps to a state outside R_k}|
undefined_count = |{i in R_k : E_j(rho_i) has no finite target ID}|
preservation_rate = preserved_count / |R_k|
```

- [ ] **Step 2: Controls**

```text
identity map preserves every region.
random permutation control destroys nontrivial preservation unless the region is cardinality-trivial.
commuting-map control must match the order matrix.
```

- [ ] **Step 3: Validate and commit**

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/gcm_map_residency_on_regions_v0/tests -q
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_map_residency_on_regions_v0/validate_gcm_map_residency_on_regions_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_math_only_packet.py system_v6/sims/gcm_map_residency_on_regions_v0/results/gcm_map_residency_on_regions_v0_envelope_results.json
git add system_v6/sims/gcm_map_residency_on_regions_v0/
git commit -m "test explicit maps on finite regions"
```

### Task 11: Run Finite Transition Trajectories

**Files:**
- Create: `system_v6/sims/gcm_transition_trajectories_v0/`

- [ ] **Step 1: Define transition system**

Use:

```text
V = state IDs or quotient-class IDs
P_j[a,b] = probability that map E_j sends a to b
trajectory = function tau with domain {t in Z : 0 <= t <= T} and codomain V
cycle = repeated vertex sequence
absorbing_set = subset A with no outgoing probability outside A
```

- [ ] **Step 2: Compute time-indexed observables**

For every trajectory:

```text
S_t
I_AB_t
negativity_t
region_id_t
map_id_t
cycle_status_t
```

- [ ] **Step 3: Controls**

```text
identity transition gives constant trajectories.
random transition gives expected loss of region preservation.
map-order shuffle must change trajectories when the order matrix has nonzero commutator norm.
```

- [ ] **Step 4: Validate and commit**

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/gcm_transition_trajectories_v0/tests -q
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_transition_trajectories_v0/validate_gcm_transition_trajectories_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_math_only_packet.py system_v6/sims/gcm_transition_trajectories_v0/results/gcm_transition_trajectories_v0_envelope_results.json
git add system_v6/sims/gcm_transition_trajectories_v0/
git commit -m "run finite transition trajectories"
```

### Task 12: Build The 3-Qubit State-Space Floor

**Files:**
- Create: `system_v6/sims/gcm_3q_state_space_v0/`
- Consume: `system_v6/sims/gcm_inverse_system_compatibility_v0/`

- [ ] **Step 1: Define the carrier**

```text
H_3 = (C^2) tensor (C^2) tensor (C^2)
dim(H_3) = 8
D(H_3) = {rho in M_8(C) : rho >= 0, Tr(rho)=1}
```

- [ ] **Step 2: Compute required tripartite observables**

```text
rho_A, rho_B, rho_C
rho_AB, rho_AC, rho_BC
S_A, S_B, S_C, S_AB, S_AC, S_BC, S_ABC
I(A:B), I(A:C), I(B:C)
I(A:B|C) = S_AC + S_BC - S_C - S_ABC
tripartite_information = I(A:B) + I(A:C) - I(A:BC)
Pauli-string expectation tensor for {I,X,Y,Z}^{tensor 3}
```

- [ ] **Step 3: Require all projection checks**

For each `rho_ABC`, compute:

```text
Tr_C(rho_ABC) = rho_AB_candidate
Tr_B(rho_ABC) = rho_AC_candidate
Tr_A(rho_ABC) = rho_BC_candidate
Tr_{B,C}(rho_ABC) = rho_A_candidate
Tr_{A,C}(rho_ABC) = rho_B_candidate
Tr_{A,B}(rho_ABC) = rho_C_candidate
```

Then require:

```text
q_AB(rho_AB_candidate) is an accepted 2-qubit quotient class;
q_AC(rho_AC_candidate) is an accepted 2-qubit quotient class;
q_BC(rho_BC_candidate) is an accepted 2-qubit quotient class;
q_A(rho_A_candidate) is an accepted 1-qubit quotient class;
q_B(rho_B_candidate) is an accepted 1-qubit quotient class;
q_C(rho_C_candidate) is an accepted 1-qubit quotient class.
```

If any projection has no accepted lower class, the 3-qubit row is not compatible with the finite inverse system.

- [ ] **Step 4: Add exact controls**

```text
product state |000><000| has zero pairwise and tripartite entanglement.
GHZ state has nonzero global correlation with separable two-body reductions.
W state differs from GHZ under reduced two-body spectra.
maximally mixed I_8/8 has zero mutual information across every split.
replace rho_AB with an accepted but wrong 2-qubit quotient class and require compatibility failure.
remove the 2-qubit registry hash and require compatibility failure.
```

- [ ] **Step 5: Validate and commit**

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/gcm_3q_state_space_v0/tests -q
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_3q_state_space_v0/validate_gcm_3q_state_space_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_math_only_packet.py system_v6/sims/gcm_3q_state_space_v0/results/gcm_3q_state_space_v0_envelope_results.json
git add system_v6/sims/gcm_3q_state_space_v0/
git commit -m "build 3-qubit state-space floor"
```

### Task 13: Compute Downstream Observables Only On Trajectories

**Files:**
- Create: `system_v6/sims/gcm_downstream_observables_on_trajectories_v0/`

- [ ] **Step 1: Refuse static inputs**

The validator must fail unless input includes:

```text
trajectory table with T >= 2;
state ID or density matrix at each time;
map ID at each transition;
at least one negative trajectory control.
```

- [ ] **Step 2: Compute only standard functions**

Allowed downstream functions:

```text
Delta S_t = S_{t+1} - S_t
return_indicator_t = 1[v_t in R_0 after leaving R_0]
escape_indicator_t = 1[v_t not in R_0]
commutator_norm_t = ||A(B(rho_t)) - B(A(rho_t))||
information_gain_t = I_AB_{t+1} - I_AB_t
curvature_integral_t only when connection_status is defined
```

- [ ] **Step 3: Quarantine project-facing names**

If a project label must be recorded, it goes only here:

```json
{
  "legacy_project_labels": ["human-facing label only, not used by formulas"]
}
```

- [ ] **Step 4: Validate and commit**

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest system_v6/sims/gcm_downstream_observables_on_trajectories_v0/tests -q
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_downstream_observables_on_trajectories_v0/validate_gcm_downstream_observables_on_trajectories_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_math_only_packet.py system_v6/sims/gcm_downstream_observables_on_trajectories_v0/results/gcm_downstream_observables_on_trajectories_v0_envelope_results.json
git add system_v6/sims/gcm_downstream_observables_on_trajectories_v0/
git commit -m "compute downstream observables on finite trajectories"
```

### Task 14: Maintain A Math-Only Execution Ledger

**Files:**
- Create: `system_v6/receipts/gcm_math_only_execution_ledger_20260613.md`

- [ ] **Step 1: Create the ledger**

```markdown
# Math-Only Execution Ledger - 2026-06-13

| Step | Object Built | Hilbert Space | Finite Set | Maps | Observables | Result Path | Audit Path | Ceiling | Blocked Consumers |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1-qubit finite object | `C^2` | `I_1` | none | Bloch vector, entropy | `system_v6/sims/gcm_constraint_carve_v1/results/gcm_constraint_carve_v1_envelope_results.json` | `system_v6/sims/gcm_constraint_carve_v1/audit_verdict.md` | scratch | all trajectory and downstream claims |
```

- [ ] **Step 2: Update after every accepted commit**

Each row must include exact result and audit paths. No row may claim a project-facing label has been simulated unless the mathematical object, maps, trajectories, and controls are named in the same row.

- [ ] **Step 3: Commit separately**

```bash
git add system_v6/receipts/gcm_math_only_execution_ledger_20260613.md
git commit -m "record math-only execution ledger"
```

## Deferred Formal Structures

The attachment proposes valid formal targets after the inverse-system carrier exists. They are not active tasks in this plan.

`G_2` may become an active packet only after a previous packet defines:

```text
W_A: finite survivor ID -> R^7
phi_A in Lambda^3(W_A^*)
g_phi from phi_A
cross_product(x,y) defined by g_phi(cross_product(x,y),z)=phi_A(x,y,z)
allowed linear maps L: W_A -> W_A
```

Required controls for a future `G_2` packet:

```text
known phi_A-preserving map passes;
random GL(7,R) matrix fails phi_A preservation;
associator-visible example is distinguished from associator-erased quotient;
split-octonion control is not silently identified with compact G_2.
```

`Spin(7)` may become active only after a `G_2` packet defines `phi_A` and a one-dimensional extension:

```text
R direct_sum W_A
Omega_A = dt wedge phi_A + star(phi_A)
```

`Spin(8)` may become active only after the packet defines three explicit 8-dimensional real representations and maps among them:

```text
V_8
S_8_plus
S_8_minus
T_V_to_S_plus
T_S_plus_to_S_minus
T_S_minus_to_V
```

`F_4` may become active only after the packet defines a 27-dimensional real target and a Jordan product:

```text
J
dim_R(J) = 27
A circle B = (A B + B A) / 2
```

Until those finite vector spaces, forms, products, maps, and controls exist, these names are blocked future targets and may appear only in planning notes.

## Execution Rules

- Do not use project nicknames in formulas, executable keys, validator branch names, or pass rules.
- Do not treat a file path name as evidence for a mathematical object.
- Do not treat scalar summaries as geometry when the density matrix or map is available.
- Do not compute trajectory observables until a transition system exists.
- Do not compute curvature integrals after a mixed-state map unless a purification or mixed-state connection is explicitly supplied.
- Do not call a downstream scalar function a simulated geometry. It is only a function on states or trajectories.
- Do not add multiple unrelated packets to one commit.
- Do not promote beyond `scratch_diagnostic` without fresh validator output and an audit verdict.

## Self-Review

Spec coverage:

- 2-qubit finite object: Task 3.
- Entropy and information quantities: Task 4.
- Actual-state geometry: Task 5.
- Finite inverse-system compatibility: Task 6.
- Explicit maps and order dependence: Task 7.
- Curvature/holonomy status: Task 8.
- Region discovery: Task 9.
- Map action on regions: Task 10.
- Trajectories: Task 11.
- 3-qubit state space and projection checks: Task 12.
- Downstream trajectory observables: Task 13.
- Durable ledger: Task 14.
- Deferred `G_2`, `Spin(7)`, `Spin(8)`, and `F_4` gates: Deferred Formal Structures.

Placeholder scan:

- No open-marker wording is used for required implementation details.
- Every task names exact paths and commands.

Type consistency:

- `state_id`, `rho_AB`, `rho_A`, `rho_B`, `region_id`, `map_id`, and `trajectory` are used consistently.
- Map domains and codomains must match before composition.
- Curvature quantities are defined only on pure-state lifts or explicitly supplied mixed-state connections.
