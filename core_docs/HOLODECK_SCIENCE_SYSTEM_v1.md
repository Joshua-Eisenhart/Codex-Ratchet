# [Exploratory probe synthesis] HOLODECK SCIENCE SYSTEM v1

> **Status**: SPEC — Awaiting SIM Evidence  
> **Date**: 2026-03-25  
> **Depends on**: `proto_ratchet_sim_runner.py`, `fep_ratchet_bridge.py`, `evidence_graph.json`
> **Current implementation note**: `holodeck_fep_engine.py` presently validates the Holodeck pipeline on a synthetic density matrix, not on live engine outputs.

---

## 1. Purpose

The Holodeck Science System bridges the Codex Ratchet QIT engine to external reality modeling.
It generates S³ projection surfaces from density matrix eigenspaces and uses the Free Energy
Principle (FEP) to map sensory data streams to A2 graph concepts.

All operations are:
- **Finite**: d-level Hilbert spaces only (d=4 default, 2-qubit)
- **Falsifiable**: Every claim has a KILL condition
- **Deterministic**: Seeded RNG for reproducibility

---

## 2. S³ Projection Surfaces via Hopf Fibration

### 2.1 Eigenspace Decomposition

Given a 2-qubit density matrix ρ ∈ ℂ^{4×4}:

1. **Diagonalize**: ρ = Σᵢ λᵢ |ψᵢ⟩⟨ψᵢ| where λᵢ ≥ 0, Σλᵢ = 1
2. **Extract eigenvectors**: Each |ψᵢ⟩ ∈ ℂ⁴ decomposes into two 2-qubit amplitudes
3. **Partial trace**: For each eigenstate, take the reduced state on qubit A:
   ρ_A^{(i)} = Tr_B(|ψᵢ⟩⟨ψᵢ|)

### 2.2 Hopf Map: ℂ² → S³ → S²

Each reduced eigenstate ψ = (α, β) ∈ ℂ² with |α|² + |β|² = 1 maps to S³ via:

```
θ = 2·arccos(|α|)           ∈ [0, π]
φ = arg(β) - arg(α)         ∈ [0, 2π)
χ = arg(α) + arg(β)         ∈ [0, 4π)  (fiber coordinate)
```

The Hopf fibration π: S³ → S² projects out the fiber χ, yielding the Bloch sphere point
(θ, φ). The full S³ coordinate (θ, φ, χ) retains the phase information lost by the Bloch
sphere — this is the Holodeck projection surface.

### 2.3 Projection Surface Construction

For a density matrix with 4 eigenvalues {λ₀, λ₁, λ₂, λ₃}:
- Each eigenspace fiber generates one S³ surface patch
- Surface weight = λᵢ (eigenvalue)
- Total surface = weighted union of 4 S³ patches
- **Coherence score** = 1 - S_vN(ρ)/log₂(d), where S_vN = von Neumann entropy

---

## 3. FEP Sensory Mapping to A2 Graph Concepts

### 3.1 Surprise Metric

The FEP surprise for a sensory observation x given internal model is:

```
S_FEP = KL(q(z|x) ∥ p(z)) = Σᵢ q(zᵢ|x) · log(q(zᵢ|x) / p(zᵢ))
```

Where:
- **q(z|x)** = posterior distribution = eigenvalue spectrum of observed density matrix ρ_obs
- **p(z)** = prior distribution = eigenvalue spectrum of model's predicted state ρ_model
- States z are **finite**: exactly d eigenvalues (no continuum limit)

### 3.2 Concept Mapping

Each A2_HIGH_INTAKE graph node represents a concept C with properties.
The Holodeck maps sensory data to concepts via:

1. **Encode**: Sensory stream → density matrix ρ_obs (via correlation matrix of sensor channels)
2. **Compare**: For each candidate concept C, compute S_FEP(ρ_obs ∥ ρ_C)
3. **Select**: Concept with minimal surprise wins (active inference)
4. **Emit**: If S_FEP < threshold → `PASS`, S_FEP > threshold → flag for attention

### 3.3 Thermal Prior Construction

The prior p(z) for a concept with temperature parameter T:

```
p(zᵢ) = exp(-Eᵢ/T) / Z,   Z = Σⱼ exp(-Eⱼ/T)
```

Where Eᵢ = -log(λᵢ) are the "energies" derived from the concept's eigenvalues.
At T→∞: maximally mixed (maximum ignorance).
At T→0: pure state (minimum surprise possible).

---

## 4. `attractor_coordinates` Schema Extension

### 4.1 Non-Destructive Extension

Added as an **optional field** on evidence_graph nodes. Existing nodes without this field
remain valid. New Holodeck-generated nodes include it.

```json
{
  "id": "HOLODECK_FEP_001",
  "type": "SpecClaim",
  "name": "HOLODECK_COHERENCE",
  "attractor_coordinates": {
    "s3_theta": 1.2345,
    "s3_phi": 0.6789,
    "s3_chi": 2.3456,
    "fep_surprise": 0.0234,
    "coherence_score": 0.9123,
    "thermal_temperature": 1.0
  },
  "score": 1.0,
  "status": "SOLVED",
  "sim_file": "holodeck_fep_engine.py"
}
```

### 4.2 Field Definitions

| Field | Type | Range | Meaning |
|---|---|---|---|
| `s3_theta` | float | [0, π] | Polar angle on S³ |
| `s3_phi` | float | [0, 2π) | Azimuthal angle on S³ |
| `s3_chi` | float | [0, 4π) | Hopf fiber coordinate |
| `fep_surprise` | float | [0, ∞) | KL divergence surprise metric |
| `coherence_score` | float | [0, 1] | 1 - S_vN/log₂(d) |
| `thermal_temperature` | float | (0, ∞) | Concept thermal parameter |

---

## 5. Integration with Autopoietic Heartbeat

### 5.1 Runner Registration

The Holodeck FEP engine registers in `run_all_sims.py` at **tier T4_ENGINE**:

```python
"T4_ENGINE": [
    ...   # existing entries
    "holodeck_fep_engine.py",
]
```

Result file mapping:
```python
"holodeck_fep_engine.py": "holodeck_fep_results.json"
```

### 5.2 Evidence Token IDs

| Token ID | Condition |
|---|---|
| `E_SIM_HOLODECK_S3_PROJECTION_OK` | All eigenspaces map to valid S³ coordinates |
| `E_SIM_HOLODECK_FEP_SURPRISE_OK` | S_FEP is finite and non-negative for all states |
| `E_SIM_HOLODECK_THERMAL_GRID_OK` | Thermal correlation matrix is positive semi-definite |
| `E_SIM_HOLODECK_COHERENCE_OK` | Coherence score ∈ (0, 1) for non-trivial states |

### 5.3 Heartbeat Cycle

```
run_all_sims.py → holodeck_fep_engine.py
  → Eigendecompose test density matrices
  → Hopf-project eigenspaces to S³
  → Compute FEP surprise metrics
  → Generate thermal correlation grid
  → Emit EvidenceTokens → holodeck_fep_results.json
  → evidence_graph.py ingests tokens on next cycle
```

---

## 6. KILL Conditions

The Holodeck thesis is **dead** if any of the following are demonstrated:

| ID | KILL Condition | Test |
|---|---|---|
| K1 | **Eigenvalue collapse**: All eigenvalues become degenerate (λᵢ = 1/d ∀i) for structured input | If a non-maximally-mixed ρ produces a maximally-mixed eigenspectrum, the projection surface is trivial |
| K2 | **FEP divergence**: S_FEP → ∞ for finite states | KL divergence must remain bounded for any p(z) > 0 |
| K3 | **S³ degeneracy**: All eigenstates map to the same S³ point | Distinct eigenspaces must produce distinct projections |
| K4 | **Coherence below threshold**: coherence_score < 0.01 for all tested states | System cannot distinguish structure from noise |
| K5 | **Thermal grid singularity**: Correlation matrix has negative eigenvalues after regularization | Thermal states must remain valid density matrices |

---

## 7. References

- `system_v4/probes/proto_ratchet_sim_runner.py` — EvidenceToken, density matrix utilities
- `system_v4/probes/fep_ratchet_bridge.py` — FEP ↔ Ratchet bridge (prior art)
- `system_v4/probes/hopf_torus_meta_sim.py` — Hopf fibration via Choi isomorphism
- `system_v4/a2_state/graphs/evidence_graph.json` — Current evidence graph (31 nodes)
- `system_v4/a2_state/graphs/a2_high_intake_graph_v1.json` — A2 concept graph
- `system_v4/probes/run_all_sims.py` — Autopoietic heartbeat runner
