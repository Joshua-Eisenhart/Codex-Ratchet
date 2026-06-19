# S9 registry provenance quote

Source: `system_v6/receipts/round3_discriminator_registry_20260611.md` at registry commit `de44219ed`.

## S9 - Connection/Transport Families

Round-2 basis: `geo_s9_alternative_connections_v0` at `9de3f3633`.
Round-2 split topology from geometry: `C_same_c1_non_hopf_density` co-survives
the `c1=1` topological row and dies at curvature density, holonomy spectrum, and
annular flux.

Round-3 finite space: connection functions matching the committed holonomy at
some leaves or matching topology more tightly than the round-2 alternatives.
Every candidate is represented as `A = dphi + f(eta)dchi`.

| Candidate id | Finite representative | Closeness | Expected teeth row | Cost |
| --- | --- | --- | --- | --- |
| `S9.R3.0_committed_hopf` | `f=cos(2eta)` | control | none; anchor | light-symbolic |
| `S9.R3.1_c1_small_density_bump` | `f=cos(2eta)+epsilon*sin(2eta)^2`, `epsilon in {1/20,-1/20}` | closest same-`c1` density neighbor | curvature density before holonomy | light-symbolic |
| `S9.R3.2_one_leaf_match_pi6` | `f=cos(2eta)+epsilon*(cos(2eta)-1/2)`, `epsilon in {1/10,-1/10}` | matches holonomy at `pi/6` only | expanded holonomy spectrum | light-symbolic |
| `S9.R3.3_one_leaf_match_pi4` | `f=cos(2eta)+epsilon*cos(2eta)`, `epsilon in {1/10,-1/10}` | matches holonomy at `pi/4` only | expanded holonomy spectrum | light-symbolic |
| `S9.R3.4_two_leaf_match_pi6_pi4` | `f=cos(2eta)+epsilon*cos(2eta)*(cos(2eta)-1/2)`, `epsilon in {1/10,-1/10}` | very close leaf-anchor neighbor | annular flux plus off-anchor holonomy | light-symbolic |
| `S9.R3.5_path_ordered_loop_neighbor` | same local `c1` row plus two named quaternionic loop families from the committed transport closure | closest heavy transport neighbor | path-ordered holonomy commutator | heavy-local |

Alias-detection rule: reduce each connection to
`(f_simplified, F=f'(eta), c1, leaf_holonomy_vector
[0,pi/6,pi/4,pi/3,pi/2], annular_flux_vector, validity_class,
path_ordered_loop_signature when scoped)`. For ordinary one-form candidates,
alias requires equality of curvature density and the full leaf-holonomy vector
under the S2/S9 convention map. Equal `c1` is `co_survivor`. Matching one or two
leaf holonomies is `open` until the expanded spectrum and annular flux rows run.

Nearest nontrivial neighbors: small same-`c1` bumps and one/two-leaf matching
families are closer than the round-2 flat/half/random alternatives. The
path-ordered loop neighbor is heavy because it tests transport identity rather
than coefficient identity.
