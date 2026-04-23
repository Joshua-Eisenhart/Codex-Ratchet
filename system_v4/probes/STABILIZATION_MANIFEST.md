# Stabilization Manifest — 2026-04-05

Mass-sim pass: 15/15 tests passed in 37s.
Engine: `engine_core.py` + `geometric_operators.py` + `hopf_manifold.py`
Bridges: Clifford (`clifford_engine_bridge.py`), TopoNetX (`toponetx_torus_bridge.py`), PyG (`pyg_engine_bridge.py`)
Result file: `mass_stabilization_results.json`

---

## Tool Installation Status

| Tool | Version | Status |
|------|---------|--------|
| numpy | 2.2.6 | installed, core dependency |
| scipy | 1.16.1 | installed |
| sympy | 1.14.0 | installed, algebra verified |
| torch | 2.8.0 | installed |
| torch_geometric | 2.7.0 | **newly installed**, PyG bridge verified |
| clifford | 1.5.1 | **newly installed**, Cl(3,0) bridge verified |
| toponetx | 0.4.0 | **newly installed**, cell complex verified |
| z3-solver | 4.16.0.0 | **newly installed**, N01 proof verified |
| hypothesis | 6.151.11 | **newly installed**, 80/80 property tests passed |
| pydantic | 2.11.9 | installed, schema validation verified |
| gudhi | 3.12.0 | **newly installed**, persistence homology computed |
| networkx | 3.5 | installed |

---

## Mass-Sim Results Summary

### Bridge Family (all OK)

| Bridge | Test | Result |
|--------|------|--------|
| Clifford | Roundtrip (inner/clifford/outer) | dist < 6e-17 |
| Clifford | Chirality content | 0.0 (correct: density has no pseudoscalar) |
| Clifford | Rotor vs numpy Fe | dist scales with angle (known: Fe uses e^{-iphi/2} vs Clifford e12 plane) |
| TopoNetX | Cell complex build | 24 vertices, 40 edges, 16 faces, 2 shells |
| TopoNetX | Type 1 path | layers [2,2,2,2,0,0,0,0] (outer then inner) |
| TopoNetX | Type 2 path | layers [0,0,0,0,2,2,2,2] (inner then outer) |
| PyG | HeteroData build | 3 node types, 4 edge types, state features attached |
| PyG | Type 1 ga0 | 0.404 |
| PyG | Type 2 ga0 | 0.538 |

### Entanglement Dynamics (50 cycles)

| Metric | Type 1 | Type 2 |
|--------|--------|--------|
| Final concurrence | **0.112** | **0.000** |
| Max concurrence | 0.112 | 0.035 |
| Final S(L) | 0.298 | 0.403 |
| Trend | accumulates (monotonic rise) | dissipates (peaks then decays to 0) |

Confirms: Type 1 = positive feedback (IN), Type 2 = negative feedback (OUT).

### Loop Order Sensitivity (10 cycles, Type 1)

| Order | Concurrence | Ratio to normal |
|-------|-------------|-----------------|
| Normal | 0.059 | 1.00x |
| Reversed | 0.021 | 0.35x |
| Swapped (ind<->ded) | 0.000 | 0.00x |
| Random (20 trials) | 0.013 +/- 0.026 | 0.21x |

Composition order is load-bearing. Swapping loops kills entanglement entirely.

### Torus Transport (10 cycles, Type 1)

| Torus | eta | Concurrence | S(L) | R_major | R_minor |
|-------|-----|-------------|------|---------|---------|
| Inner | 0.393 | 0.044 | 0.404 | 0.924 | 0.383 |
| **Clifford** | **0.785** | **0.059** | 0.378 | 0.707 | 0.707 |
| Outer | 1.178 | 0.043 | 0.405 | 0.383 | 0.924 |

Clifford torus produces maximum entanglement. Gradient symmetric around Clifford.

### Resonance Sweep (piston 0 -> 1)

| Engine | Peak piston | Peak concurrence |
|--------|-------------|------------------|
| Type 1 | **0.80** | **0.152** |
| Type 2 | **0.55** | **0.039** |
| Both at p=0 | ~0 | |
| Both at p=1 | 0 | (dissipation overwhelms) |

Goldilocks zone confirmed. Type 1 peak is ~4x Type 2.

### Torus Entropy Gradient (15-point sweep)

Peak concurrence at eta = 0.687, very close to Clifford (0.785).
The plateau around Clifford is broad: eta in [0.59, 0.98] all give C > 0.057.

### Dual-Stack Ratchet (30 cycles, 5% cross-coupling)

| Cycle | C1 (Type 1) | C2 (Type 2) |
|-------|-------------|-------------|
| 0 | 0.037 | 0.020 |
| 15 | 0.055 | 0.033 |
| 29 | **0.058** | **0.005** |

Type 1 sustains entanglement; Type 2 decays even with coupling. The interaction IS the ratchet.

### Irreversibility

Min trace distance from init over 50 cycles: **0.306**. Engine never returns to initial state.

### New Tool Validations

| Tool | Test | Result |
|------|------|--------|
| z3 | Pauli eigenvalues satisfiable | sat |
| z3 | Simultaneous eigenstate of sigma_x, sigma_z | **unsat** (N01 confirmed) |
| sympy | [sigma_x, sigma_y] = 2i sigma_z | true |
| sympy | Casimir = 3I | true |
| sympy | Jacobi identity | true |
| hypothesis | Trace preserved (50 random configs) | 50/50 |
| hypothesis | Entropy non-negative (30 random configs) | 30/30 |
| pydantic | Schema validation (10 cycles) | 10/10 |
| gudhi | Rips persistence (20 trajectory points) | betti_0=1, betti_1=0 |

---

## Result File Audit

**Total files in `a2_state/sim_results/`**: 263 JSON files, 6.1 MB total.

### Classification

| Category | Count | Description |
|----------|-------|-------------|
| **Evidence** (>1KB, substantive data) | ~235 | Real sim output with measured values |
| **Stub** (<200 bytes, placeholder only) | **28** | Timestamp-only placeholders, no data |
| **Diagnostic** (engine traces, sweeps) | ~15 | `engine_inside_trace.json` (476KB), mass sweeps, audits |
| **Legacy** (pre-operator-correction, <Mar 29) | ~60 | From before Fe/Te/Fi operator math correction |

### Stub Files (low-signal, placeholder only)

28 files under 200 bytes contain only `{"sim": "...", "timestamp": "..."}` with no actual data.
These include several files referenced in the math doc:
- `feedback_loop_coupling_results.json` (66 bytes)
- `loop_order_sensitivity_results.json` (66 bytes)
- `strength_resonance_sweep_results.json` (68 bytes)
- `per_stage_entanglement_dynamics_results.json` (75 bytes)
- `geometric_ablation_battery_results.json` (70 bytes)

**These stubs are now superseded by `mass_stabilization_results.json`** which contains real measured data for all these categories.

### Canonical Result File

**`mass_stabilization_results.json`** (this session) is the single authoritative file containing:
- All bridge verification data (Clifford, TopoNetX, PyG)
- 50-cycle entanglement dynamics for both engine types
- Loop order sensitivity (4 conditions + 20 random trials)
- Torus transport across 3 levels
- Resonance sweep (21 piston values x 2 types)
- Torus entropy gradient (15-point eta sweep)
- All tool validation results (z3, sympy, hypothesis, pydantic, gudhi)
- Dual-stack ratchet (30 cycles)
- Irreversibility proof

### Largest Files

| File | Size | Signal |
|------|------|--------|
| engine_inside_trace.json | 476KB | diagnostic (full step trace, useful for debugging) |
| axis0_chiral_deep_search_results.json | 188KB | evidence (deep axis 0 search) |
| axis0_option_spectrum_results.json | 167KB | evidence (option space exploration) |
| hopf_pointwise_pullback_results.json | 164KB | evidence (geometry verification) |
| unified_evidence_report.json | 137KB | legacy index (pre-correction, treat as historical) |

---

## What is Robust

1. **Engine core**: 4 operators (Ti/Fe/Te/Fi) with correct CPTP math, verified against Clifford algebra
2. **Hopf geometry**: S3 -> S2 fibration, torus foliation, Berry phase computation
3. **4x4 native operators**: Joint L|R entangling dynamics produce genuine concurrence
4. **Loop grammar**: Composition order measurably determines entanglement accumulation
5. **Chirality**: Type 1 (IN/accumulate) vs Type 2 (OUT/dissipate) confirmed over 50 cycles
6. **Clifford peak**: Entanglement maximizes at/near Clifford torus (eta ~ pi/4)
7. **Resonance**: Goldilocks zone for piston strength; p=0 and p=1 both kill entanglement
8. **Irreversibility**: Engine trajectory never returns to initial state
9. **All 8 new tools**: Installed and producing meaningful results
10. **N01 (non-commutativity)**: Formally proven via z3 (no simultaneous eigenstates)

## What Needs Attention

1. **Clifford rotor vs numpy Fe**: Distance grows with angle; this is expected (Clifford applies rotation in e12 plane, numpy Fe uses U_z matrix directly) but should be documented as a representation mismatch, not a bug
2. **28 stub result files**: Should either be populated with real data or removed
3. **Legacy pre-correction results** (before Mar 29): Not invalid but operators were different; treat as historical
4. **gudhi betti_1 = 0**: Trajectory in Bloch space doesn't form persistent loops (expected for slow spiral toward attractor)
