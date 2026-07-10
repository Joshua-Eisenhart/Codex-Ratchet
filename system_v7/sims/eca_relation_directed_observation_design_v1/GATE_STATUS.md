# Gate Status

| Gate | Status | Evidence |
|---|---|---|
| Preregistration before search | PASS | commit `68f7c8dcd` |
| Winners frozen before confirmation source | PASS | commits `5f42e344d`, `8615977aa` |
| Complete candidate universe | PASS | 2,500 unique subsets |
| Exact shortlist universe | PASS | 96 unique exact scores |
| Independent shortlist/winner derivation | PASS | controller C9 |
| Cross-runtime train score projection | PASS | all normalized score projections agree |
| Reserved validation fixture universe | PASS | 325 pair-orbit representatives |
| Shared confirmation records | PASS | 2,925/2,925 agree |
| Confirmation implementation controls | PASS | both runtimes green mechanically |
| Candidate exists | FAIL | 0/3 sizes pass |
| Robust design family | FAIL | requires at least 2/3 sizes |
| Reused test confirmation | UNOPENED | opening condition false |
| Learned perception admission | BLOCKED | measurement design failed |
| QIT/engine schedule promotion | BLOCKED | outside packet and unearned |

The generic Python sim-contract linter reports zero violations for
`confirm_jax.py` and `validate_confirmation.py`. The earlier train-only JAX
source still exposes six missing micro-probe registry entries for its declared
load-bearing JAX APIs; this is package-admission registry debt, not evidence
that the exact result passed scientifically.

The confirmation controller deliberately separates `mechanical_all_pass=true`
from `scientific_pass=false`. The overall scientific `all_pass` is false.
