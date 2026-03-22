# Cross-Solver SMT Verification Report (v1)

- **generated_utc**: `2026-03-22T10:23:00Z`
- **solvers**: Z3 4.16.0, cvc5 1.3.3
- **framework**: PySMT 0.9.6
- **interpreter**: `.venv_spec_graph`

## Graph Facts Used

| Fact | Value |
|------|-------|
| `kernel_node_count` | 419 |
| `kernel_with_adm` | 419 |
| `promoted_node_count` | 296 |
| `promo_nodes_with_edges` | 296 |
| `promo_nodes_isolated` | 0 |
| `cross_edge_total` | 500 |
| `cross_valid` | 500 |
| `cross_dangling` | 0 |
| `all_layer_node_count` | 10524 |

## Formulas & Results

### Formula 1: Kernel nodes must have admissibility_state

- **Name**: `kernel_admissibility`
- **Expected SAT**: ✅ `True`

**Facts encoded**:

- `kernel_total` = 419
- `kernel_with_adm` = 419

**Solver Results**:

| Solver | Status | Time (ms) | Error |
|--------|--------|-----------|-------|
| Z3 | `SAT` | 602.9 | — |
| cvc5 | `SAT` | 3.723 | — |

**Models**:

Z3 model:
- `kernel_total` = 419
- `kernel_with_adm` = 419

cvc5 model:
- `kernel_total` = 419
- `kernel_with_adm` = 419

**Comparison**:

- Same status: ✅ `True`
- Same model: ✅ `True`
- Faster solver: `cvc5`
- Speed ratio: `161.94x`

---

### Formula 2: Promoted nodes must have >= 1 edge

- **Name**: `promoted_connectivity`
- **Expected SAT**: ✅ `True`

**Facts encoded**:

- `promoted_total` = 296
- `promoted_with_edges` = 296
- `isolated_count` = 0

**Solver Results**:

| Solver | Status | Time (ms) | Error |
|--------|--------|-----------|-------|
| Z3 | `SAT` | 2.499 | — |
| cvc5 | `SAT` | 1.019 | — |

**Models**:

Z3 model:
- `promoted_total` = 296
- `promoted_with_edges` = 296
- `isolated_count` = 0

cvc5 model:
- `promoted_total` = 296
- `promoted_with_edges` = 296
- `isolated_count` = 0

**Comparison**:

- Same status: ✅ `True`
- Same model: ✅ `True`
- Faster solver: `cvc5`
- Speed ratio: `2.45x`

---

### Formula 3: Cross-layer edges must connect existing nodes

- **Name**: `cross_layer_integrity`
- **Expected SAT**: ✅ `True`

**Facts encoded**:

- `cross_total` = 500
- `cross_valid` = 500
- `dangling` = 0

**Solver Results**:

| Solver | Status | Time (ms) | Error |
|--------|--------|-----------|-------|
| Z3 | `SAT` | 2.05 | — |
| cvc5 | `SAT` | 1.072 | — |

**Models**:

Z3 model:
- `cross_total` = 500
- `cross_valid_sym` = 500
- `dangling_count` = 0

cvc5 model:
- `cross_total` = 500
- `cross_valid_sym` = 500
- `dangling_count` = 0

**Comparison**:

- Same status: ✅ `True`
- Same model: ✅ `True`
- Faster solver: `cvc5`
- Speed ratio: `1.91x`

---

## Summary

| Metric | Result |
|--------|--------|
| Formulas tested | 3 |
| All status agree | ✅ |
| All models agree | ✅ |

## Invariant Health

- ✅ **Kernel nodes must have admissibility_state**: HOLDS (verified by both solvers)
- ✅ **Promoted nodes must have >= 1 edge**: HOLDS (verified by both solvers)
- ✅ **Cross-layer edges must connect existing nodes**: HOLDS (verified by both solvers)
