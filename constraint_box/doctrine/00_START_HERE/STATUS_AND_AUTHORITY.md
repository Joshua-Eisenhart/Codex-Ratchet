# Status, Authority, and Nonclaims

## Status vocabulary

| Term | Meaning |
|---|---|
| `OWNER_RULE_REPORTED` | A rule stated by the owner and carried here without promotion |
| `PROPOSED` | Design offered for comparison and testing |
| `IMPLEMENTED_LOCAL` | Code exists in this pack |
| `BOUNDED_TESTED_LOCAL` | A named local fixture was executed |
| `OPTIONAL_UNAVAILABLE` | Adapter exists but dependency was absent on this host |
| `OPEN` | Not decided or not implemented |
| `SUPERSEDED_HERE` | Older pack content replaced for this pack only |

## Current evidence

| Item | Status |
|---|---|
| Python core | `IMPLEMENTED_LOCAL` |
| Initial unit/hostile suite | `BOUNDED_TESTED_LOCAL` |
| NumPy profile | `BOUNDED_TESTED_LOCAL` on the packaging host |
| Z3 profile | `IMPLEMENTED_LOCAL`, dependency unavailable on packaging host |
| TLA+ specification | `PROPOSED`, not model-checked in this pack build |
| Pi/agent adapter | contract only; no selected agent harness |
| LevOS adapter | boundary design only |
| CR adapter | finite quotient fixture implemented; full CR not integrated |
| Sim Fleet adapter | worker contract implemented; full engines not integrated |
| Scientific or manifold result | none |

## Nonclaims

This pack does not claim:

- absolute minimal sufficient structure;
- object identity;
- scientific truth;
- a canonical manifold;
- correct 16-stage engine mathematics;
- full LevOS integration;
- full simulation-engine integration;
- a security boundary against a hostile operating-system user;
- that a local hash chain proves authorship;
- that SAT or UNSAT applies beyond the encoded finite contract;
- that a present path-amplitude cancellation deletes individual histories.

`ELIGIBLE` means only that the configured next bounded step may consume an
artifact.  It is not a synonym for true, proven, admitted to CR, or released.
