# ConstraintBox live core status

Generated: `2026-08-06T20:32:35.634607+00:00`

This snapshot is local to ConstraintBox. It is not the external Sim Engines estate.

| Tool | Installed version | Import visible | Exercised integration |
|---|---:|---|---|
| `python.z3` | `4.16.0.0` | True | yes |
| `python.cvc5` | `1.3.3` | True | yes |
| `python.sympy` | `1.14.0` | True | yes |
| `python.rustworkx` | `0.17.1` | True | yes |
| `python.maude` | `1.6.0` | True | yes |

Exercise observation SHA-256: `5c09bc21101c77c76f209ef34ce2154b89d1745419ef28493553bc16e76296b9`

Excluded from the CB core: JAX, PyTorch, Julia, Java/TLC/Apalache, and PySINDy.

Claim ceiling: installation visibility plus one bounded function exercise per core tool.
