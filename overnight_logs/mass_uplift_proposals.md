# Mass Tool Uplift Proposals

- tool: `z3`
- pattern: `neg_of_positive_unsat` — Encode the negation of each positive-test claim as a z3 assertion. If the sim's positive claim is truly admissible, the solver must return UNSAT. SAT = counterexample found.
- glob: `classical_baseline_*.py`
- eligible sims: 20
- scanned: 100

STATUS: proposals only. No sims modified. Review then apply.

## Top candidates (by uplift_score)

- **classical_baseline_heat_equation_fd.py** (score 5, hits=['conserved', 'bound'])
- **classical_baseline_holodeck_structure_composition.py** (score 5, hits=['equal', 'identity'])
- **classical_baseline_leviathan_monotone_aggregation.py** (score 5, hits=['monotone', 'cannot'])
- **classical_baseline_bisection.py** (score 4, hits=['bound'])
- **classical_baseline_cellular_automaton.py** (score 4, hits=['bound'])

---

## Proposals

### classical_baseline_heat_equation_fd.py

- path: `system_v4/probes/classical_baseline_heat_equation_fd.py`
- classification: `classical_baseline`
- uplift_score: 5
- admissibility_hits: ['conserved', 'bound']
- positive_claim: `{"peak_diffused": bool(u.max() < 0.5), "spread_positive": bool(u[32+5]>0)}`
- proposed tool: `z3`
- proposed assertion: `Not({"peak_diffused": bool(u.max() < 0.5), "spread_positive": bool(u[32+5]>0)})`
- expected UNSAT reason: positive-test dict asserts: `{"peak_diffused": bool(u.max() < 0.5), "spread_positive": bool(u[32+5]>0)}`. Under pattern `neg_of_positive_unsat`, assert Not(<claim>) in z3. Expected UNSAT if the claim is an admissibility fence; SAT exposes a counterexample that falsifies the fence.
- patch skeleton:

```python
from z3 import Solver, Real, Bool, Not, sat, unsat
def z3_admissibility_fence():
    s = Solver()
    # TODO: translate each positive-test claim into z3 terms,
    # then assert Not(claim). UNSAT => claim is admissibility-closed.
    # SAT   => counterexample exists; sim's 'positive' is not a fence.
    return {'z3_unsat': s.check() == unsat}
```

---

### classical_baseline_holodeck_structure_composition.py

- path: `system_v4/probes/classical_baseline_holodeck_structure_composition.py`
- classification: `classical_baseline`
- uplift_score: 5
- admissibility_hits: ['equal', 'identity']
- positive_claim: `out`
- proposed tool: `z3`
- proposed assertion: `Not(out)`
- expected UNSAT reason: positive-test dict asserts: `out`. Under pattern `neg_of_positive_unsat`, assert Not(<claim>) in z3. Expected UNSAT if the claim is an admissibility fence; SAT exposes a counterexample that falsifies the fence.
- patch skeleton:

```python
from z3 import Solver, Real, Bool, Not, sat, unsat
def z3_admissibility_fence():
    s = Solver()
    # TODO: translate each positive-test claim into z3 terms,
    # then assert Not(claim). UNSAT => claim is admissibility-closed.
    # SAT   => counterexample exists; sim's 'positive' is not a fence.
    return {'z3_unsat': s.check() == unsat}
```

---

### classical_baseline_leviathan_monotone_aggregation.py

- path: `system_v4/probes/classical_baseline_leviathan_monotone_aggregation.py`
- classification: `classical_baseline`
- uplift_score: 5
- admissibility_hits: ['monotone', 'cannot']
- positive_claim: `out`
- proposed tool: `z3`
- proposed assertion: `Not(out)`
- expected UNSAT reason: positive-test dict asserts: `out`. Under pattern `neg_of_positive_unsat`, assert Not(<claim>) in z3. Expected UNSAT if the claim is an admissibility fence; SAT exposes a counterexample that falsifies the fence.
- patch skeleton:

```python
from z3 import Solver, Real, Bool, Not, sat, unsat
def z3_admissibility_fence():
    s = Solver()
    # TODO: translate each positive-test claim into z3 terms,
    # then assert Not(claim). UNSAT => claim is admissibility-closed.
    # SAT   => counterexample exists; sim's 'positive' is not a fence.
    return {'z3_unsat': s.check() == unsat}
```

---

### classical_baseline_bisection.py

- path: `system_v4/probes/classical_baseline_bisection.py`
- classification: `classical_baseline`
- uplift_score: 4
- admissibility_hits: ['bound']
- positive_claim: `{"sqrt2": bool(abs(r-np.sqrt(2))<1e-8)}`
- proposed tool: `z3`
- proposed assertion: `Not({"sqrt2": bool(abs(r-np.sqrt(2))<1e-8)})`
- expected UNSAT reason: positive-test dict asserts: `{"sqrt2": bool(abs(r-np.sqrt(2))<1e-8)}`. Under pattern `neg_of_positive_unsat`, assert Not(<claim>) in z3. Expected UNSAT if the claim is an admissibility fence; SAT exposes a counterexample that falsifies the fence.
- patch skeleton:

```python
from z3 import Solver, Real, Bool, Not, sat, unsat
def z3_admissibility_fence():
    s = Solver()
    # TODO: translate each positive-test claim into z3 terms,
    # then assert Not(claim). UNSAT => claim is admissibility-closed.
    # SAT   => counterexample exists; sim's 'positive' is not a fence.
    return {'z3_unsat': s.check() == unsat}
```

---

### classical_baseline_cellular_automaton.py

- path: `system_v4/probes/classical_baseline_cellular_automaton.py`
- classification: `classical_baseline`
- uplift_score: 4
- admissibility_hits: ['bound']
- positive_claim: `{"rule30_nontrivial": bool(h30.sum()>10), "rule110_nontrivial": bool(h110.sum()>10)}`
- proposed tool: `z3`
- proposed assertion: `Not({"rule30_nontrivial": bool(h30.sum()>10), "rule110_nontrivial": bool(h110.sum()>10)})`
- expected UNSAT reason: positive-test dict asserts: `{"rule30_nontrivial": bool(h30.sum()>10), "rule110_nontrivial": bool(h110.sum()>10)}`. Under pattern `neg_of_positive_unsat`, assert Not(<claim>) in z3. Expected UNSAT if the claim is an admissibility fence; SAT exposes a counterexample that falsifies the fence.
- patch skeleton:

```python
from z3 import Solver, Real, Bool, Not, sat, unsat
def z3_admissibility_fence():
    s = Solver()
    # TODO: translate each positive-test claim into z3 terms,
    # then assert Not(claim). UNSAT => claim is admissibility-closed.
    # SAT   => counterexample exists; sim's 'positive' is not a fence.
    return {'z3_unsat': s.check() == unsat}
```

---

### classical_baseline_cholesky_spd.py

- path: `system_v4/probes/classical_baseline_cholesky_spd.py`
- classification: `classical_baseline`
- uplift_score: 4
- admissibility_hits: ['bound']
- positive_claim: `{"reconstruct": bool(np.allclose(L@L.T, A, atol=1e-8)),             "L_lower_tri": bool(np.allclose(np.triu(L,1), 0))}`
- proposed tool: `z3`
- proposed assertion: `Not({"reconstruct": bool(np.allclose(L@L.T, A, atol=1e-8)),             "L_lower_tri": bool(np.allclose(np.triu(L,1), 0))})`
- expected UNSAT reason: positive-test dict asserts: `{"reconstruct": bool(np.allclose(L@L.T, A, atol=1e-8)),             "L_lower_tri": bool(np.allclose(np.triu(L,1), 0))}`. Under pattern `neg_of_positive_unsat`, assert Not(<claim>) in z3. Expected UNSAT if the claim is an admissibility fence; SAT exposes a counterexample that falsifies the fence.
- patch skeleton:

```python
from z3 import Solver, Real, Bool, Not, sat, unsat
def z3_admissibility_fence():
    s = Solver()
    # TODO: translate each positive-test claim into z3 terms,
    # then assert Not(claim). UNSAT => claim is admissibility-closed.
    # SAT   => counterexample exists; sim's 'positive' is not a fence.
    return {'z3_unsat': s.check() == unsat}
```

---

### classical_baseline_cl3_rotor_pauli_rep.py

- path: `system_v4/probes/classical_baseline_cl3_rotor_pauli_rep.py`
- classification: `classical_baseline`
- uplift_score: 4
- admissibility_hits: ['unitary']
- positive_claim: `out`
- proposed tool: `z3`
- proposed assertion: `Not(out)`
- expected UNSAT reason: positive-test dict asserts: `out`. Under pattern `neg_of_positive_unsat`, assert Not(<claim>) in z3. Expected UNSAT if the claim is an admissibility fence; SAT exposes a counterexample that falsifies the fence.
- patch skeleton:

```python
from z3 import Solver, Real, Bool, Not, sat, unsat
def z3_admissibility_fence():
    s = Solver()
    # TODO: translate each positive-test claim into z3 terms,
    # then assert Not(claim). UNSAT => claim is admissibility-closed.
    # SAT   => counterexample exists; sim's 'positive' is not a fence.
    return {'z3_unsat': s.check() == unsat}
```

---

### classical_baseline_cl6_kron_pauli_rep.py

- path: `system_v4/probes/classical_baseline_cl6_kron_pauli_rep.py`
- classification: `classical_baseline`
- uplift_score: 4
- admissibility_hits: ['commut']
- positive_claim: `out`
- proposed tool: `z3`
- proposed assertion: `Not(out)`
- expected UNSAT reason: positive-test dict asserts: `out`. Under pattern `neg_of_positive_unsat`, assert Not(<claim>) in z3. Expected UNSAT if the claim is an admissibility fence; SAT exposes a counterexample that falsifies the fence.
- patch skeleton:

```python
from z3 import Solver, Real, Bool, Not, sat, unsat
def z3_admissibility_fence():
    s = Solver()
    # TODO: translate each positive-test claim into z3 terms,
    # then assert Not(claim). UNSAT => claim is admissibility-closed.
    # SAT   => counterexample exists; sim's 'positive' is not a fence.
    return {'z3_unsat': s.check() == unsat}
```

---

### classical_baseline_dla_aggregation.py

- path: `system_v4/probes/classical_baseline_dla_aggregation.py`
- classification: `classical_baseline`
- uplift_score: 4
- admissibility_hits: ['bound']
- positive_claim: `{"cluster_grew": bool(g.sum()>5), "seed_still_there": bool(g[30,30]==1)}`
- proposed tool: `z3`
- proposed assertion: `Not({"cluster_grew": bool(g.sum()>5), "seed_still_there": bool(g[30,30]==1)})`
- expected UNSAT reason: positive-test dict asserts: `{"cluster_grew": bool(g.sum()>5), "seed_still_there": bool(g[30,30]==1)}`. Under pattern `neg_of_positive_unsat`, assert Not(<claim>) in z3. Expected UNSAT if the claim is an admissibility fence; SAT exposes a counterexample that falsifies the fence.
- patch skeleton:

```python
from z3 import Solver, Real, Bool, Not, sat, unsat
def z3_admissibility_fence():
    s = Solver()
    # TODO: translate each positive-test claim into z3 terms,
    # then assert Not(claim). UNSAT => claim is admissibility-closed.
    # SAT   => counterexample exists; sim's 'positive' is not a fence.
    return {'z3_unsat': s.check() == unsat}
```

---

### classical_baseline_eulerian_path.py

- path: `system_v4/probes/classical_baseline_eulerian_path.py`
- classification: `classical_baseline`
- uplift_score: 4
- admissibility_hits: ['bound']
- positive_claim: `{"cycle_has_eulerian": bool(_has_eulerian(A))}`
- proposed tool: `z3`
- proposed assertion: `Not({"cycle_has_eulerian": bool(_has_eulerian(A))})`
- expected UNSAT reason: positive-test dict asserts: `{"cycle_has_eulerian": bool(_has_eulerian(A))}`. Under pattern `neg_of_positive_unsat`, assert Not(<claim>) in z3. Expected UNSAT if the claim is an admissibility fence; SAT exposes a counterexample that falsifies the fence.
- patch skeleton:

```python
from z3 import Solver, Real, Bool, Not, sat, unsat
def z3_admissibility_fence():
    s = Solver()
    # TODO: translate each positive-test claim into z3 terms,
    # then assert Not(claim). UNSAT => claim is admissibility-closed.
    # SAT   => counterexample exists; sim's 'positive' is not a fence.
    return {'z3_unsat': s.check() == unsat}
```

---

### classical_baseline_fft_reconstruction.py

- path: `system_v4/probes/classical_baseline_fft_reconstruction.py`
- classification: `classical_baseline`
- uplift_score: 4
- admissibility_hits: ['bound']
- positive_claim: `{"roundtrip": bool(np.allclose(x, y, atol=1e-10))}`
- proposed tool: `z3`
- proposed assertion: `Not({"roundtrip": bool(np.allclose(x, y, atol=1e-10))})`
- expected UNSAT reason: positive-test dict asserts: `{"roundtrip": bool(np.allclose(x, y, atol=1e-10))}`. Under pattern `neg_of_positive_unsat`, assert Not(<claim>) in z3. Expected UNSAT if the claim is an admissibility fence; SAT exposes a counterexample that falsifies the fence.
- patch skeleton:

```python
from z3 import Solver, Real, Bool, Not, sat, unsat
def z3_admissibility_fence():
    s = Solver()
    # TODO: translate each positive-test claim into z3 terms,
    # then assert Not(claim). UNSAT => claim is admissibility-closed.
    # SAT   => counterexample exists; sim's 'positive' is not a fence.
    return {'z3_unsat': s.check() == unsat}
```

---

### classical_baseline_game_of_life.py

- path: `system_v4/probes/classical_baseline_game_of_life.py`
- classification: `classical_baseline`
- uplift_score: 4
- admissibility_hits: ['equal']
- positive_claim: `{"blinker_period2": {"pass": bool(np.array_equal(g2[2,1:4],[1,1,1]))}}`
- proposed tool: `z3`
- proposed assertion: `Not({"blinker_period2": {"pass": bool(np.array_equal(g2[2,1:4],[1,1,1]))}})`
- expected UNSAT reason: positive-test dict asserts: `{"blinker_period2": {"pass": bool(np.array_equal(g2[2,1:4],[1,1,1]))}}`. Under pattern `neg_of_positive_unsat`, assert Not(<claim>) in z3. Expected UNSAT if the claim is an admissibility fence; SAT exposes a counterexample that falsifies the fence.
- patch skeleton:

```python
from z3 import Solver, Real, Bool, Not, sat, unsat
def z3_admissibility_fence():
    s = Solver()
    # TODO: translate each positive-test claim into z3 terms,
    # then assert Not(claim). UNSAT => claim is admissibility-closed.
    # SAT   => counterexample exists; sim's 'positive' is not a fence.
    return {'z3_unsat': s.check() == unsat}
```

---

### classical_baseline_gradient_descent_convex.py

- path: `system_v4/probes/classical_baseline_gradient_descent_convex.py`
- classification: `classical_baseline`
- uplift_score: 4
- admissibility_hits: ['bound']
- positive_claim: `{"convex_min_found": bool(np.allclose(r, [3,-1], atol=1e-5))}`
- proposed tool: `z3`
- proposed assertion: `Not({"convex_min_found": bool(np.allclose(r, [3,-1], atol=1e-5))})`
- expected UNSAT reason: positive-test dict asserts: `{"convex_min_found": bool(np.allclose(r, [3,-1], atol=1e-5))}`. Under pattern `neg_of_positive_unsat`, assert Not(<claim>) in z3. Expected UNSAT if the claim is an admissibility fence; SAT exposes a counterexample that falsifies the fence.
- patch skeleton:

```python
from z3 import Solver, Real, Bool, Not, sat, unsat
def z3_admissibility_fence():
    s = Solver()
    # TODO: translate each positive-test claim into z3 terms,
    # then assert Not(claim). UNSAT => claim is admissibility-closed.
    # SAT   => counterexample exists; sim's 'positive' is not a fence.
    return {'z3_unsat': s.check() == unsat}
```

---

### classical_baseline_gram_schmidt.py

- path: `system_v4/probes/classical_baseline_gram_schmidt.py`
- classification: `classical_baseline`
- uplift_score: 4
- admissibility_hits: ['bound']
- positive_claim: `{"orthonormal": bool(np.allclose(Q.T@Q, np.eye(5), atol=1e-8))}`
- proposed tool: `z3`
- proposed assertion: `Not({"orthonormal": bool(np.allclose(Q.T@Q, np.eye(5), atol=1e-8))})`
- expected UNSAT reason: positive-test dict asserts: `{"orthonormal": bool(np.allclose(Q.T@Q, np.eye(5), atol=1e-8))}`. Under pattern `neg_of_positive_unsat`, assert Not(<claim>) in z3. Expected UNSAT if the claim is an admissibility fence; SAT exposes a counterexample that falsifies the fence.
- patch skeleton:

```python
from z3 import Solver, Real, Bool, Not, sat, unsat
def z3_admissibility_fence():
    s = Solver()
    # TODO: translate each positive-test claim into z3 terms,
    # then assert Not(claim). UNSAT => claim is admissibility-closed.
    # SAT   => counterexample exists; sim's 'positive' is not a fence.
    return {'z3_unsat': s.check() == unsat}
```

---

### classical_baseline_group_reps_s3_d4.py

- path: `system_v4/probes/classical_baseline_group_reps_s3_d4.py`
- classification: `classical_baseline`
- uplift_score: 4
- admissibility_hits: ['bound']
- positive_claim: `{"s3_order_6": bool(len(S3)==6), "s3_closure": bool(closure)}`
- proposed tool: `z3`
- proposed assertion: `Not({"s3_order_6": bool(len(S3)==6), "s3_closure": bool(closure)})`
- expected UNSAT reason: positive-test dict asserts: `{"s3_order_6": bool(len(S3)==6), "s3_closure": bool(closure)}`. Under pattern `neg_of_positive_unsat`, assert Not(<claim>) in z3. Expected UNSAT if the claim is an admissibility fence; SAT exposes a counterexample that falsifies the fence.
- patch skeleton:

```python
from z3 import Solver, Real, Bool, Not, sat, unsat
def z3_admissibility_fence():
    s = Solver()
    # TODO: translate each positive-test claim into z3 terms,
    # then assert Not(claim). UNSAT => claim is admissibility-closed.
    # SAT   => counterexample exists; sim's 'positive' is not a fence.
    return {'z3_unsat': s.check() == unsat}
```

---

### classical_baseline_hamming_code.py

- path: `system_v4/probes/classical_baseline_hamming_code.py`
- classification: `classical_baseline`
- uplift_score: 4
- admissibility_hits: ['equal']
- positive_claim: `{"corrected": {"pass": bool(np.array_equal(cw,cw_fix)), "err_i": int(err_i)}}`
- proposed tool: `z3`
- proposed assertion: `Not({"corrected": {"pass": bool(np.array_equal(cw,cw_fix)), "err_i": int(err_i)}})`
- expected UNSAT reason: positive-test dict asserts: `{"corrected": {"pass": bool(np.array_equal(cw,cw_fix)), "err_i": int(err_i)}}`. Under pattern `neg_of_positive_unsat`, assert Not(<claim>) in z3. Expected UNSAT if the claim is an admissibility fence; SAT exposes a counterexample that falsifies the fence.
- patch skeleton:

```python
from z3 import Solver, Real, Bool, Not, sat, unsat
def z3_admissibility_fence():
    s = Solver()
    # TODO: translate each positive-test claim into z3 terms,
    # then assert Not(claim). UNSAT => claim is admissibility-closed.
    # SAT   => counterexample exists; sim's 'positive' is not a fence.
    return {'z3_unsat': s.check() == unsat}
```

---

### classical_baseline_henon_map.py

- path: `system_v4/probes/classical_baseline_henon_map.py`
- classification: `classical_baseline`
- uplift_score: 4
- admissibility_hits: ['bound']
- positive_claim: `{"bounded_attractor": {"pass": bool(np.all(np.abs(tr)<10))}}`
- proposed tool: `z3`
- proposed assertion: `Not({"bounded_attractor": {"pass": bool(np.all(np.abs(tr)<10))}})`
- expected UNSAT reason: positive-test dict asserts: `{"bounded_attractor": {"pass": bool(np.all(np.abs(tr)<10))}}`. Under pattern `neg_of_positive_unsat`, assert Not(<claim>) in z3. Expected UNSAT if the claim is an admissibility fence; SAT exposes a counterexample that falsifies the fence.
- patch skeleton:

```python
from z3 import Solver, Real, Bool, Not, sat, unsat
def z3_admissibility_fence():
    s = Solver()
    # TODO: translate each positive-test claim into z3 terms,
    # then assert Not(claim). UNSAT => claim is admissibility-closed.
    # SAT   => counterexample exists; sim's 'positive' is not a fence.
    return {'z3_unsat': s.check() == unsat}
```

---

### classical_baseline_holodeck_carrier_equality.py

- path: `system_v4/probes/classical_baseline_holodeck_carrier_equality.py`
- classification: `classical_baseline`
- uplift_score: 4
- admissibility_hits: ['equal']
- positive_claim: `out`
- proposed tool: `z3`
- proposed assertion: `Not(out)`
- expected UNSAT reason: positive-test dict asserts: `out`. Under pattern `neg_of_positive_unsat`, assert Not(<claim>) in z3. Expected UNSAT if the claim is an admissibility fence; SAT exposes a counterexample that falsifies the fence.
- patch skeleton:

```python
from z3 import Solver, Real, Bool, Not, sat, unsat
def z3_admissibility_fence():
    s = Solver()
    # TODO: translate each positive-test claim into z3 terms,
    # then assert Not(claim). UNSAT => claim is admissibility-closed.
    # SAT   => counterexample exists; sim's 'positive' is not a fence.
    return {'z3_unsat': s.check() == unsat}
```

---

### classical_baseline_holodeck_reduction_quotient.py

- path: `system_v4/probes/classical_baseline_holodeck_reduction_quotient.py`
- classification: `classical_baseline`
- uplift_score: 4
- admissibility_hits: ['equal']
- positive_claim: `out`
- proposed tool: `z3`
- proposed assertion: `Not(out)`
- expected UNSAT reason: positive-test dict asserts: `out`. Under pattern `neg_of_positive_unsat`, assert Not(<claim>) in z3. Expected UNSAT if the claim is an admissibility fence; SAT exposes a counterexample that falsifies the fence.
- patch skeleton:

```python
from z3 import Solver, Real, Bool, Not, sat, unsat
def z3_admissibility_fence():
    s = Solver()
    # TODO: translate each positive-test claim into z3 terms,
    # then assert Not(claim). UNSAT => claim is admissibility-closed.
    # SAT   => counterexample exists; sim's 'positive' is not a fence.
    return {'z3_unsat': s.check() == unsat}
```

---

### classical_baseline_igt_admissibility_dominance.py

- path: `system_v4/probes/classical_baseline_igt_admissibility_dominance.py`
- classification: `classical_baseline`
- uplift_score: 4
- admissibility_hits: ['admissib']
- positive_claim: `{"col2_dominated": {"pass": 2 in d}}`
- proposed tool: `z3`
- proposed assertion: `Not({"col2_dominated": {"pass": 2 in d}})`
- expected UNSAT reason: positive-test dict asserts: `{"col2_dominated": {"pass": 2 in d}}`. Under pattern `neg_of_positive_unsat`, assert Not(<claim>) in z3. Expected UNSAT if the claim is an admissibility fence; SAT exposes a counterexample that falsifies the fence.
- patch skeleton:

```python
from z3 import Solver, Real, Bool, Not, sat, unsat
def z3_admissibility_fence():
    s = Solver()
    # TODO: translate each positive-test claim into z3 terms,
    # then assert Not(claim). UNSAT => claim is admissibility-closed.
    # SAT   => counterexample exists; sim's 'positive' is not a fence.
    return {'z3_unsat': s.check() == unsat}
```

---

