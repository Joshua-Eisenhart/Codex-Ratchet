# Repository Deep Audit: Five Advanced Constraint-Manifold Seams

**Date:** 2026-07-22  
**Requested output:** `REPOSITORY_DEEP_AUDIT_2026-07-22.md`  
**Primary repository:** `Joshua-Eisenhart/Codex-Ratchet`  
**Active base:** `session/r0-three-engine-probes` at `0c6ea14b9c20223aa5231a0abf9afa59f7b4ac08`  
**Additive whole-state draft:** PR #3, `agent/july22-n3-whole-state-ratchet` at `80b05258e262484f193e75ab822c15ed23f91368`  
**Lev repository:** `lev-os/leviathan`, `main` at `1efe47f4b41878ebbc1eed8e87da8e3c80a2e5a9`  
**Audit method:** repository content and commit identity through the GitHub connector, plus a fresh local replay of the exact PR #3 N=3 source carried in Pack 190.

## Executive result

The requested five mechanisms are not five completed parts of one running manifold. The repository contains several real prerequisites, one bounded whole-state calibration, and one useful Claim-submission substrate. None of the five requested advanced seams is complete end to end.

| Mechanism | Exact requested seam | Verdict | Strongest thing that really runs |
|---|---|---:|---|
| 1 | Nested-shell coefficient maps \(\Pi_{AB}:C^k(K_A;\mathbb Z_{n_A})\to C^k(K_B;\mathbb Z_{n_B})\), with \(n_B\mid n_A\), coboundary naturality, and composition | **NO** | A fixed \(\mathbb Z_5\) triangle obstruction/edge-removal renest; separate fixed-\(N\) cycle and grid-refinement sweeps |
| 2 | Boundary-cochain stress \(d_{uv}\mapsto E_{\mathrm{stress}}\mapsto W'\mapsto L'\), followed by whole-state resettlement | **NO** | Static or state-recomputed graph Laplacians, a fixed Hodge operator with PyG smoothing, and graph data passed once through the three-engine estate |
| 3 | Exact/localized \(N>3\) factor-graph settlement by Markov-blanket boundary messages | **NO** | Dense fixed-\(N=3\), \(8\times8\) density evolution; isolated PyG message-passing demonstrations |
| 4 | Node-local pressure field \(\lambda(v)\) parameterizing a covariant CPTP family, with all-\(\lambda\) TP/CP proof and restriction naturality | **NO** for the requested seam; **PARTIAL** for fixed/authored CPTP families | Analytically CPTP dephasing, depolarizing, and unitary channels; one global Hartley-drive scaling of GKSL dissipation in the larger sim |
| 5 | Semantic ClaimGate binding of logical claims to independently executed, content-digested evidence, immune to tautologies and new-key renames | **NO** | Deterministic shape/provenance gates; an honest red adversarial corpus; Lev `lev.done` hashes submitted payload bytes and appends evidence, but full Claim admission is still an execution-ready task |

This is not a finding that the proposals are mathematically impossible. It is a repository-state finding: adjacent pieces must not be renamed as the integrated mechanism.

## Evidence and status rules

The audit uses four labels:

- **implemented:** the typed map is in executable source and an appropriate test or receipt exercises it;
- **partial:** a genuine strict sub-map runs, but one or more defining arrows or invariants of the requested mechanism are absent;
- **adjacent:** a library or experiment performs related mathematics without being connected to the requested seam;
- **absent:** no executable implementation of the requested typed map was found at the frozen refs.

No claim is promoted merely because an installed library could implement it. A committed source without its claimed result receipt is reported as source, not as a fresh result. A design task is not counted as implementation. No snippet below contains an ellipsis; every quoted code block is a complete lexical unit or a complete bounded ledger object.

## Fresh replay performed for this audit

The Pack-190 copy of PR #3 was rerun on 2026-07-22:

```text
CPython 3.12.13
NumPy 2.3.5
12/12 unit tests: PASS
26/26 campaign checks: PASS
receipt SHA-256: 20972558fafa6e95e8f5cb5fc416b0f06ef9884ea443806d17723f20d818f676
```

The replay proves the bounded N=3 code remains deterministic. It does not enlarge its claim ceiling.

---

## Mechanism 1

**MECHANISM NAME:** Multi-Resolution \(\mathbb Z_n\) Cochain Projections & Ring Homomorphisms

### REPOSITORY PATHS AND COMMITS

Audit refs:

- Active branch `session/r0-three-engine-probes`: `0c6ea14b9c20223aa5231a0abf9afa59f7b4ac08`.
- Draft PR #3 head `agent/july22-n3-whole-state-ratchet`: `80b05258e262484f193e75ab822c15ed23f91368`.
- PR #3 implementation commit: `397c3e6886b2e12f28a0a14977760e6b5b96823a`.
- PR #3 receipt commit: `199c0df6cad6724f8e65263fe50dd0d66246325c`.

Direct and adjacent assets:

| Path | Frozen content identity | What it actually contains |
|---|---|---|
| `whole_manifold/n3_whole_state/manifold_sim.py` | PR head `80b05258…`; blob `87146b1ef5b05d80d70d2663cd2d5596431fecc9` | A single-modulus triangle obstruction evaluated modulo 5 and an authored edge-removal renest. |
| `whole_manifold/n3_whole_state/test_sim.py` | PR head; blob `b91e4a95d74b7382a3c599ca42df0a09e648d7cd` | Tests only the fixed \(\mathbb Z_5\) torn-triangle/path case. |
| `whole_manifold/n3_whole_state/results/receipt.json` | Receipt commit `199c0df6…`; blob `b4cfa148b17390bee8e795464457884a3c9019fb` | Records obstruction 2 for the triangle and obstruction 0 after deleting its third edge. |
| `system_v7/sims/finite_cycle_z_n_holonomy_section_lift_discriminator_v0/finite_cycle_z_n_holonomy_section_lift_discriminator_v0_exact.py` | Active branch; blob `dc80afbe459a267c51f063784be111ea14ad76f0` | Independent fixed-\(N\) cycle calculations for \(N=2,3,4,6,12\); no maps between those rings. |
| `system_v7/sims/finite_cycle_z_n_holonomy_section_lift_discriminator_v0/results/finite_cycle_z_n_holonomy_section_lift_discriminator_v0_exact_results.json` | Active branch; blob `40db3b392a080c41aa28c5658d7f0d0535189339` | Scratch receipt, explicitly evidence-ineligible and circular. |
| `system_v7/sims/finite_cycle_z_n_holonomy_section_lift_discriminator_v0/FLEET_VERDICT_20260615.md` | Active branch; blob `154d8ee9cf826e28891a03069ef62ff2a14cc944` | Demotes the result to a finite obstruction sanity check; finite fibre versus larger quotient remains open. |
| `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_core.py` | Active branch; blob `fe28b6d68a17f75e23cb1ed3edb0e9afd127243b` | Separate \(N=2,4,8,16,32,64\) Hopf-torus grids and convergence curves; no coefficient projections between grids. |
| `system_v6/sims/geo_s7_discrete_refinement_v0/audit_verdict.md` | Active branch; blob `a2fd049853acf7d8f911e013a7a83a44eb6da981` | Audits finite-grid convergence, cover counts, flux, and Stokes checks; it does not claim nested \(\mathbb Z_n\) cochain functoriality. |
| `MODEL_DOSSIER/10_GEMINI_FORMAL_PROPOSALS_POST_07_22.md` | PR head; blob `400d949e87d2d8e2c9699d985797e3507eff96a2` | Correctly labels finite cohomological gluing as candidate mathematics and the PR's \(\mathbb Z_5\) result as bounded calibration. |

### FORMAL OBJECTS & TYPED DOMAINS

For nested finite cell complexes \(i_{BA}:K_B\hookrightarrow K_A\), choose coefficient rings

\[
R_A=\mathbb Z/n_A\mathbb Z,
\qquad
R_B=\mathbb Z/n_B\mathbb Z,
\qquad n_B\mid n_A.
\]

The canonical coefficient reduction is the surjective unital ring homomorphism

\[
q_{AB}:R_A\to R_B,
\qquad
q_{AB}([x]_{n_A})=[x]_{n_B}.
\]

The divisibility hypothesis is load-bearing: without \(n_B\mid n_A\), the displayed map is not well-defined on residue classes. It induces a componentwise cochain map

\[
(q_{AB})_\#:C^k(K_B;R_A)\to C^k(K_B;R_B).
\]

Composed with cellular pullback

\[
i_{BA}^{*}:C^k(K_A;R_A)\to C^k(K_B;R_A),
\]

the cross-resolution shell projection is

\[
\Pi_{AB}=(q_{AB})_\#\circ i_{BA}^{*}:
C^k(K_A;R_A)\to C^k(K_B;R_B).
\]

A valid implementation must verify coboundary naturality

\[
\delta_B\Pi_{AB}=\Pi_{AB}\delta_A
\]

and, for \(n_C\mid n_B\mid n_A\), functorial composition

\[
\Pi_{BC}\circ\Pi_{AB}=\Pi_{AC}.
\]

If two shells meet at \(K_{AB}\), first declare a common coefficient ring

\[
R_{AB}=\mathbb Z_{n_{AB}},
\qquad n_{AB}\mid n_A,
\qquad n_{AB}\mid n_B,
\]

and the corresponding reductions into that common codomain. Exact boundary matching is then

\[
(q_{A\to AB})_\#r_A(c_A)
=
(q_{B\to AB})_\#r_B(c_B).
\]

None of these typed maps exists in the audited code.

Actual PR #3 types are only

\[
\texttt{edges}\subseteq V\times V,
\qquad
\texttt{cochain}:E\to\mathbb Z,
\qquad
\texttt{modulus}\in\mathbb N,
\]

with one arithmetic expression reduced modulo `modulus`. The code does not construct residue-class objects or enforce that cochain values belong to a declared coefficient ring.

The older finite-cycle script implements, independently for each \(N\),

\[
g\in(\mathbb Z_N)^m,
\qquad
H_N(g)=\sum_{e=1}^{m}g_e\pmod N,
\]

and searches for

\[
\phi:V\to\mathbb Z_N,
\qquad
\phi(i+1)-\phi(i)=g_i\pmod N.
\]

It never computes \(q_{AB}(g^{(n_A)})\), compares projected holonomy, or checks a divisibility-chain commuting diagram.

### EXECUTABLE IMPLEMENTATION (yes/no)

**No.**

There are executable adjacent pieces:

- a fixed \(\mathbb Z_5\) triangle obstruction in PR #3;
- independent fixed-\(N\) cycle obstruction checks;
- independent finite-grid refinement/convergence runs.

There is no executable multi-resolution cochain-projection system and no nested-shell ring-homomorphism settlement.

### RUNTIME / TEST ARTIFACTS & RECEIPTS

PR #3's receipt reports:

- torn triangle cochain \((1,1,0)\) modulo 5;
- obstruction \(1+1-0=2\bmod5\);
- rejection of the torn triangle;
- deletion of edge \((0,2)\);
- automatic obstruction 0 for the resulting path;
- structural charge 1;
- full candidate re-settlement and admission;
- `all_checks_pass: true`.

This is a topology-changing finite calibration, not multi-resolution projection.

The older cycle receipt was generated on `2026-06-15T03:44:29Z` and reports agreement between a closed-form holonomy check and explicit section propagation for \(N=2,3,4,6,12\). Its own binding status is:

```json
{
  "classification": "scratch_diagnostic",
  "evidence_eligible": false,
  "evidence_ineligible_reason": "CIRCULAR (fleet wlgj6haef 6/6): definitional restatement of the standard obstruction theorem; cannot back an evidence_grade row. Finite obstruction sanity check only.",
  "promotion_allowed": false,
  "formal_admission_allowed": false
}
```

The fleet verdict states that the finite fibre-versus-larger-finite-quotient question remains unresolved. `geo_s7_discrete_refinement_v0` evaluates independent grids at \(N=2,4,8,16,32,64\), with exact cover counts and numerical convergence tests. It does not define maps from an \(N=64\) cochain to \(N=32,16,8,4,2\).

### KNOWN GAPS, STRESS HOLES, OR CONFLICTS

1. No shell-indexed coefficient-ring functor \(A\mapsto\mathbb Z_{n_A}\).
2. No test or guard requiring \(n_B\mid n_A\).
3. No implemented \(q_{AB}([x]_{n_A})=[x]_{n_B}\).
4. No cochain projection commuting with coboundary.
5. No functorial composition test across three resolutions.
6. No cup-product or ring-operation preservation test.
7. No cross-resolution boundary comparison.
8. No test that projected holonomy agrees with directly computed coarse holonomy.
9. The finite-cycle \(N\)-sweep treats every \(N\) as an independent experiment.
10. The Hopf-torus refinement suite compares convergence to continuum targets rather than finite coefficient-ring projections.
11. PR #3's `Diagram.obstruction()` returns zero for every non-triangle graph. Its path renest therefore passes because the only tested obstruction is bypassed after deleting an edge; this is not a general proof that the path cochain is a compatible nested section.
12. Values stored in `cochain` are ordinary Python integers; only the final triangle sum is reduced modulo \(n\).
13. No falsifier mutates a projection by one residue while holding the fine cochain fixed.
14. No non-divisor control, such as an attempted canonical \(\mathbb Z_6\to\mathbb Z_4\) reduction, is required to block.
15. No connection exists between this seam and the whole candidate's density-state restrictions.

### SOURCE CODE / LEDGER SNIPPET

Complete PR #3 `Diagram` implementation:

```python
@dataclass(frozen=True)
class Diagram:
    diagram_id: str
    edges: tuple[tuple[int, int], ...]
    modulus: int
    cochain: Mapping[tuple[int, int], int]
    parent_diagram: str | None = None
    structural_charge: int = 0

    def obstruction(self) -> int:
        triangle = {(0, 1), (1, 2), (0, 2)}
        if set(self.edges) != triangle:
            return 0
        a01 = int(self.cochain[(0, 1)])
        a12 = int(self.cochain[(1, 2)])
        a02 = int(self.cochain[(0, 2)])
        return (a01 + a12 - a02) % self.modulus

    def compatible(self) -> bool:
        return self.obstruction() == 0
```

Complete bounded fixed-\(N\) cycle functions:

```python
def holonomy(g, N):
    return sum(g) % N


def section_exists_formula(g, N):
    return holonomy(g, N) == 0


def section_exists_search(g, N):
    """Explicit independent solve: does phi: nodes->Z_N exist with
    phi[(i+1)%m] - phi[i] == g[i] (mod N) for every edge i (incl wraparound)?
    Fix phi[0]=0, propagate forward, then check the wraparound edge closes."""
    m = len(g)
    phi = [0] * m
    for i in range(m - 1):
        phi[i + 1] = (phi[i] + g[i]) % N
    closes = ((phi[0] - phi[m - 1]) % N) == (g[m - 1] % N)
    return closes


def sheets_over_basepoint(g, N):
    """number of distinct phases the basepoint is reachable with = |<H>| in Z_N."""
    H = holonomy(g, N)
    return N // gcd(N, H) if H != 0 else 1


def analyze(g, N):
    H = holonomy(g, N)
    sa = section_exists_formula(g, N)
    sb = section_exists_search(g, N)
    s = sheets_over_basepoint(g, N)
    no_global_section = not sa
    return {
        "g": list(g), "N": N, "holonomy": H,
        "section_exists_formula": sa, "section_exists_search": sb,
        "methods_agree": sa == sb,
        "sheets_over_basepoint": s,
        "bare_quotient_erases_a_distinction": s > 1,
        "no_global_section": no_global_section,
    }
```

Complete bounded topology receipt extraction:

```json
{
  "renesting": {
    "diagram_from": "triangle_z5_torn",
    "diagram_to": "path_z5_renested",
    "from": "H_native_torn",
    "structural_charge": 1,
    "to": "H_native_renested"
  },
  "rows": [
    {
      "candidate_id": "H_native_torn",
      "diagram_id": "triangle_z5_torn",
      "proposal_kind": "topology_control",
      "admitted": false,
      "topology": {
        "cochain": {"0-1": 1, "0-2": 0, "1-2": 1},
        "compatible": false,
        "edges": [[0, 1], [1, 2], [0, 2]],
        "modulus": 5,
        "obstruction": 2,
        "parent_diagram": null,
        "structural_charge": 0
      }
    },
    {
      "candidate_id": "H_native_renested",
      "diagram_id": "path_z5_renested",
      "proposal_kind": "renest_remove_incompatible_cycle_edge",
      "admitted": true,
      "topology": {
        "cochain": {"0-1": 1, "1-2": 1},
        "compatible": true,
        "edges": [[0, 1], [1, 2]],
        "modulus": 5,
        "obstruction": 0,
        "parent_diagram": "triangle_z5_torn",
        "structural_charge": 1
      }
    }
  ],
  "checks": {
    "incompatible_cycle_rejected": true,
    "renesting_reprocessed_and_admitted": true
  }
}
```

---

## Mechanism 2

**MECHANISM NAME:** Discrete Graph-Stress Backreaction & Metric Updating

### REPOSITORY PATHS AND COMMITS

| Path | Frozen content identity | What it actually contains |
|---|---|---|
| `whole_manifold/n3_whole_state/manifold_sim.py` | PR head `80b05258…`; blob `87146b1…` | Static topology obstruction and scalar `structural_charge`; no graph weights or Laplacian. |
| `whole_manifold/n3_whole_state/results/receipt.json` | Receipt commit `199c0df6…`; blob `b4cfa148…` | Structural charge appears only as one Pareto objective. |
| `system_v4/probes/entropic_curvature_lattice_sim.py` | Active branch; blob `fc85b4963dabae5df5471231a84563597a1b6b6d` | Recomputes state-similarity weights, forms \(L=D-W\), and evaluates \(K=L\Phi\). It does not compute cochain discrepancy or feed curvature/stress back into \(W\). |
| `system_v4/probes/sim_gtower_laplacian_spectrum.py` | Active branch; blob `ac1083a91b600094bcf8b1a6c54a2dfa63200fbf` | Static weights authored from group-dimension differences; spectral analysis only. |
| `system_v4/probes/sim_compound_autograd_topo_mp.py` | Active branch; blob `0707b5f768d398bac6401f74ab1b99969f6661e8` | Fixed Hodge Laplacian plus learned mean-message-passing smoothing; optimizes a cochain, not graph geometry. |
| `system_v8/engine_estate/results/integration/receipt.json` | Active branch | Real Torch \(\to\) JAX \(\to\) Julia graph-weight dataflow, but graph-derived `p0` is based on out-degree and never updated by topological stress. |
| `MODEL_DOSSIER/CURRENT_LAYER_MATH_pack186.md` | Active branch; blob `d3bd2d3a136c149023bd3588497039bd56f256be` | Describes a capacity-weighted differential \(d_N=W_e^{1/2}\partial W_v^{-1/2}\) and \(L_N=d_N^*d_N\); capacities derive from complete extensions, not boundary-cochain stress. |

The result paths generated by these older sources were checked on the active branch:

- `system_v4/probes/a2_state/sim_results/entropic_curvature_lattice_results.json`
- `system_v4/probes/a2_state/sim_results/sim_gtower_laplacian_spectrum_results.json`
- `system_v4/probes/a2_state/sim_results/sim_compound_autograd_topo_mp_results.json`

All three returned repository 404. Their sources exist; committed result ledgers at those declared paths do not.

### FORMAL OBJECTS & TYPED DOMAINS

The requested mechanism starts with

\[
G=(V,E,W),
\qquad
W=(w_{uv})\in\mathbb R_{\ge0}^{V\times V},
\qquad W=W^\top,
\]

\[
D(W)=\operatorname{diag}(W\mathbf1),
\qquad
L(W)=D(W)-W.
\]

For local cochains

\[
c_u\in C^1(U_u;\mathbb Z_n),
\qquad
c_v\in C^1(U_v;\mathbb Z_n),
\]

define their cut discrepancy on \(U_{uv}=U_u\cap U_v\):

\[
d_{uv}=r_{u,uv}c_u-r_{v,uv}c_v
\in C^1(U_{uv};\mathbb Z_n).
\]

A declared cyclic metric is required to turn a residue into real stress:

\[
\|[a]_n\|_{\mathrm{cyc}}=\min_{k\in\mathbb Z}|a+kn|.
\]

An edge-local stress can then be defined without smoothing:

\[
s_{uv}=\sum_{e\in U_{uv}^{(1)}}\|d_{uv}(e)\|_{\mathrm{cyc}}^2
\in\mathbb R_{\ge0}.
\]

Node stress is

\[
E_{\mathrm{stress}}(v)=\sum_{u:\{u,v\}\in E}s_{uv}.
\]

A symmetric exact update corresponding to the proposed backreaction is, for example,

\[
w'_{uv}=w_{uv}+\alpha s_{uv}=w'_{vu},
\qquad \alpha\ge0,
\]

followed by

\[
D'=\operatorname{diag}(W'\mathbf1),
\qquad
L'=D'-W'.
\]

The sign and physical meaning of this update must be declared: `+` makes stressed cuts more strongly coupled, while `-` weakens them and requires a positivity projection. The whole candidate must be resettled using \(L'\), not merely report \(s_{uv}\) as telemetry.

Actual nearby implementations are:

1. State-similarity graph:

   \[
   w_{ij}=\max(1-\tfrac12\|\rho_i-\rho_j\|_1,0.01),
   \qquad L=D-W,
   \qquad K=L\Phi.
   \]

2. Static G-tower graph:

   \[
   w_{ij}=|\dim G_i-\dim G_j|
   \]

   with two authored weight-1 exceptions.

3. Fixed Hodge cochain optimization:

   \[
   L_1=B_1^\top B_1+B_2B_2^\top,
   \]

   \[
   \min_x\|L_1\operatorname{MP}_\theta(x)\|^2+
   (\|\operatorname{MP}_\theta(x)\|^2-1)^2.
   \]

4. PR #3 uses only \(\texttt{structural\_charge}\in\{0,1\}\) as a Pareto coordinate. It does not mutate a metric.

### EXECUTABLE IMPLEMENTATION (yes/no)

**No.**

The repository has executable graph Laplacians, state-derived weights, Hodge operators, message passing, and a recent three-engine graph-weight handoff. It lacks the requested cochain-stress-to-graph-metric backreaction loop.

### RUNTIME / TEST ARTIFACTS & RECEIPTS

PR #3 proves only that a structural charge can participate as a fifth Pareto objective. It does not establish a graph update.

`system_v8/engine_estate/results/integration/receipt.json` is the strongest recent graph-related execution receipt:

- all 10 checks pass;
- Torch constructs graph-derived weights;
- JAX selects \(\gamma^*=0.9396825396825397\) from a 64-value entropy sweep;
- Julia integrates the GKSL system;
- final chained entropy agrees with the NumPy control to \(1.5099\times10^{-14}\);
- claim ceiling is “working-sim estate probe; not canonical, not proof-level.”

Its graph distribution is

\[
p_0=(0.15,0.15,0.15,0.10,0.15,0.15,0.15),
\]

derived from graph out-degree. No boundary cochain, stress, or \(W\mapsto W'\) update appears. The older graph/Laplacian sources have no committed result JSON at their own declared output paths on the audited branch.

### KNOWN GAPS, STRESS HOLES, OR CONFLICTS

1. No implemented \(d_{uv}=r_uc_u-r_vc_v\).
2. No declared norm converting modular discrepancy into nonnegative stress.
3. No `E_stress` function or edge-local stress matrix.
4. No \(W\mapsto W'\) update.
5. No recomputation of \(D'\) and \(L'\) after a stress event.
6. No whole-candidate re-settlement after metric mutation.
7. No symmetry or nonnegativity tests for updated weights.
8. No test that zero discrepancy leaves \(W\) unchanged.
9. No injected-discrepancy control showing only the intended edge changes.
10. No \(\alpha=0\) deletion control or comparison of positive versus negative response.
11. No stability or boundedness test across repeated feedback iterations.
12. No coupling between PR #3's `structural_charge` and an edge.
13. `entropic_curvature_lattice_sim.py` floors every edge at `0.01`; that is an explicit smoothing heuristic.
14. The same script computes \(K=L\Phi\) but never uses \(K\) to modify \(W\).
15. Its empirical dynamics is local amplitude damping, not graph backreaction.
16. `sim_gtower_laplacian_spectrum.py` uses frozen authored weights.
17. `sim_compound_autograd_topo_mp.py` explicitly calls the PyG step “load-bearing smoothing”; it learns a cochain/readout state while holding \(L_1\) fixed.
18. Pack 186's capacity weights are recomputed from extension counts, not boundary-cochain mismatch.
19. The three-engine integration chain carries graph data forward once; it does not close feedback from Julia output or residuals back into Torch's graph.

### SOURCE CODE / LEDGER SNIPPET

Complete state-weight and Laplacian functions:

```python
def compute_potentials(states):
    """Negentropy potential Φ_i = log(d) - S(ρ_i) for each node."""
    potentials = []
    for rho in states:
        d = rho.shape[0]
        S = von_neumann_entropy(rho)
        phi = np.log2(d) - S
        potentials.append(phi)
    return np.array(potentials)


def compute_mi_weights(states, rng):
    """Ring lattice: each node connected to 2 nearest neighbors with trace-distance weights."""
    n = len(states)
    W = np.zeros((n, n))
    for i in range(n):
        for offset in [-1, 1]:
            j = (i + offset) % n
            diff = states[i] - states[j]
            td = 0.5 * np.linalg.norm(diff, 'nuc')
            W[i, j] = max(1.0 - td, 0.01)
    return W


def graph_laplacian(W):
    """Standard graph Laplacian L = D - W."""
    D = np.diag(np.sum(W, axis=1))
    return D - W
```

Complete static G-tower graph construction:

```python
GTOWER_EDGES = [
    (0, 1, 6),
    (1, 2, 1),
    (2, 3, 6),
    (3, 4, 1),
    (4, 5, 13),
    (5, 6, 31),
]

N_NODES = 7


def _build_adjacency_matrix():
    """Build the symmetric weighted adjacency matrix W for the G-tower graph."""
    W = np.zeros((N_NODES, N_NODES))
    for src, tgt, w in GTOWER_EDGES:
        W[src, tgt] = w
        W[tgt, src] = w
    return W


def _build_laplacian(W):
    """Graph Laplacian L = D - W."""
    D = np.diag(W.sum(axis=1))
    L = D - W
    return L
```

Complete fixed-Hodge optimization function:

```python
def run():
    B1, B2, edges = build_complex()
    E = B1.shape[1]

    L1 = torch.tensor(B1.T @ B1 + B2 @ B2.T, dtype=torch.float32)
    ei = edge_edge_index_from_B2(B2)

    torch.manual_seed(0)
    x = torch.randn(E, 1, requires_grad=True)
    mp = HigherOrderMP()
    opt = torch.optim.Adam([x] + list(mp.parameters()), lr=5e-2)

    losses = []
    for step in range(400):
        opt.zero_grad()
        x_mp = mp(x, ei)
        harm = (L1 @ x_mp).pow(2).sum()
        norm_pen = (x_mp.pow(2).sum() - 1.0).pow(2)
        loss = harm + norm_pen
        loss.backward()
        opt.step()
        losses.append(float(loss))

    with torch.no_grad():
        x_final = mp(x, ei)
        residual = float((L1 @ x_final).pow(2).sum())
        norm = float(x_final.pow(2).sum())

    improved = losses[0] > losses[-1]

    x2 = torch.randn(E, 1, requires_grad=True)
    opt2 = torch.optim.Adam([x2], lr=5e-2)
    for _ in range(200):
        opt2.zero_grad()
        ((torch.eye(E) @ x2).pow(2).sum() + (x2.pow(2).sum()-1).pow(2)).backward()
        opt2.step()
    neg_norm = float(x2.pow(2).sum())

    return {
        "positive": {
            "loss_start": losses[0], "loss_end": losses[-1],
            "improved": improved, "residual": residual, "norm": norm,
            "E": E, "num_2cells": B2.shape[1],
        },
        "negative": {"identity_laplacian_norm": neg_norm,
                     "collapses_as_expected": neg_norm < 0.2 or abs(neg_norm-1)<0.2},
        "boundary": {"num_steps": len(losses)},
        "ablations": {
            "ablate_toponetx_breaks_claim": True,
            "ablate_pyg_breaks_claim": True,
            "ablate_pytorch_breaks_claim": True,
        },
        "PASS": bool(improved),
    }
```

Exact bounded PR receipt objective declaration:

```json
[
  {"direction": "min", "name": "system_dephasing_trace_distance"},
  {"direction": "min", "name": "max_fragment_root_fidelity"},
  {"direction": "min", "name": "conditional_mutual_information_E1_E2_given_S"},
  {"direction": "max", "name": "min_fragment_guessing_probability"},
  {"direction": "min", "name": "structural_charge"}
]
```

The decisive audit conclusion is: fixed-\(N\) obstruction, finite-grid refinement, static/recomputed graph Laplacians, Hodge message passing, and structural-charge telemetry are prerequisites, not the requested integrated mechanisms.

---

## Mechanism 3

**MECHANISM NAME:** Localized Factor-Graph Message Passing for \(N>3\)

### REPOSITORY PATHS AND COMMITS

Audited repository: `Joshua-Eisenhart/Codex-Ratchet`  
Audited branch: `session/r0-three-engine-probes`  
Branch tip: `0c6ea14b9c20223aa5231a0abf9afa59f7b4ac08`

Current bounded graph micro:

| Path | Content identity | Standing |
|---|---|---|
| `system_v4/probes/sim_integration_networkx_pyg_graph_roundtrip_micro.py` | Active blob `350d9b41e2c5ba15ac353a39dd21380f54f71c4d`; introduced by commit `53496f3e0ea1b3bec9d399d994aef94b1f8ea035` | Three-node incoming-neighbor sum only |
| `system_v4/probes/a2_state/sim_results/sim_integration_networkx_pyg_graph_roundtrip_micro_results.json` | Active blob `4b5604d41019cb9360f87f1b82e0e8e5216a27e3`; receipt commit `5e191744f945d172dd48cab59d6f3db450d0c258` | 6/6 bounded micro receipt |

Historical integrated graph model:

| Path | Content identity | Standing |
|---|---|---|
| `system_v4/probes/sim_gnn_cascade_integrated.py` | Active blob `19eb5621858e51fd858401c097c3f8c02a60bb4c`; receipt-bound historical blob `5fed67974f462a5a80ae58e31751f5b14e4150e5` | Complete-bipartite aggregate, not localized |
| `system_v4/probes/a2_state/sim_results/gnn_cascade_integrated_results.json` | Historical blob `c773bee4a09b5f869b1186e50d1fa97a05465e60` at commit `c6c81ea0c344485fa536a1b1bcd8c1b0ccaaf684`; absent at active tip | Historical receipt does not bind the changed active source |

Current engine-estate graph probe:

| Path | Content identity | Standing |
|---|---|---|
| `system_v8/engine_estate/results/torch/receipt.json` | Active blob `f150cc2ed704def72be5f1776faf6d8e7bcae793` | Nine capacity graphs, PyG validation, fixed-point partition agreement |
| `MODEL_DOSSIER/05_ENGINE_STAGES_LOOPS_CYCLES.md` | Active tip | Explicitly says the PyTorch graph drive is not a dynamical engine |

Current whole-manifold draft:

- PR: `Joshua-Eisenhart/Codex-Ratchet#3`
- Base: `0c6ea14b9c20223aa5231a0abf9afa59f7b4ac08`
- Head: `80b05258e262484f193e75ab822c15ed23f91368`
- Principal implementation commit: `397c3e6886b2e12f28a0a14977760e6b5b96823a`

| Path | Content identity | Standing |
|---|---|---|
| `whole_manifold/n3_whole_state/manifold_sim.py` | PR-head blob `87146b1ef5b05d80d70d2663cd2d5596431fecc9` | Dense three-qubit global state |
| `whole_manifold/n3_whole_state/results/receipt.json` | Blob `b4cfa148b17390bee8e795464457884a3c9019fb` | 26/26 N=3 receipt |

### FORMAL OBJECTS & TYPED DOMAINS

The requested mechanism requires a finite factor graph

\[
G=(V\sqcup F,E),
\qquad
E\subseteq V\times F,
\qquad |V|>3,
\]

with node state spaces \(X_v\), factor scopes \(\partial\alpha\subseteq V\), and local Markov blankets

\[
B_v=
\left\{
u\in V\setminus\{v\}:
\exists\alpha\in F,
\ \{u,v\}\subseteq\partial\alpha
\right\}.
\]

For the patch \(U_v=\{v\}\cup B_v\), define the accessible separator vertex set and its induced separator complex

\[
S_{uv}=U_u\cap U_v,
\qquad
K_{uv}=K[U_u]\cap K[U_v],
\]

where \(K[U]\) denotes the declared cell/simplicial subcomplex induced by \(U\).

A compressed boundary receipt should inhabit a declared finite type such as

\[
r_{u\to v}\in R_{uv}=C^k(K_{uv};\mathbb Z_{n_{uv}}).
\]

A localized message map has type

\[
\mu_{u\to v}:
X_u\times\prod_{w\in B_u\setminus\{v\}}R_{wu}
\longrightarrow R_{uv},
\]

and a local settlement update has type

\[
\psi_v:X_v\times\prod_{u\in B_v}R_{uv}\longrightarrow X_v.
\]

A settled candidate requires a fixed point

\[
x_v^\star=\psi_v\!\left(x_v^\star,(\mu_{u\to v}^\star)_{u\in B_v}\right)
\quad\forall v,
\]

plus explicit global compatibility or reconstruction. Local convergence does not by itself establish an inverse-limit global section.

The current bounded PyG micro implements instead

\[
\operatorname{SumMessage}:
\mathbb R^{|V|\times1}\times
\{0,\ldots,|V|-1\}^{2\times|E|}
\longrightarrow\mathbb R^{|V|\times1},
\]

\[
x'_v=\sum_{u:(u,v)\in E}x_u.
\]

It has no factor-potential type, boundary-cochain type, Markov-blanket object, or global reconstruction operation.

PR #3 uses one global carrier

\[
\rho\in\mathcal D(\mathbb C^8)
\]

and obtains subsystem states by dense partial traces

\[
\rho_A=\operatorname{Tr}_{\bar A}\rho.
\]

That is a valid N=3 whole-state calculation, not localized factor-graph settlement.

### EXECUTABLE IMPLEMENTATION (yes/no)

**No.** Executable adjacent pieces are:

1. a three-node NetworkX-to-PyG incoming-sum micro;
2. a historical complete-bipartite terrain/shell/operator graph;
3. fixed-point partition propagation on nine capacity graphs;
4. dense three-qubit whole-state settlement in PR #3.

None implements \(N>3\) Markov-blanket settlement using compressed boundary-cochain receipts.

### RUNTIME / TEST ARTIFACTS & RECEIPTS

#### Current NetworkX/PyG micro

The active receipt reports 6/6 passing checks:

- forward-cycle expected/output: \([3,1,2]\);
- reverse-edge output: \([2,3,1]\);
- isolated-node expected/output: \([0,5,0]\);
- empty graph: zero nodes and edge-index shape \([2,0]\);
- classification: `canonical`;
- claim ceiling: `tool_tool_micro_integration_only`.

The introducing commit limits the result to exact node mapping, directed-edge orientation, isolated-node handling, and incoming-neighbor sums. It claims neither graph learning nor whole-manifold coupling.

#### Historical `CascadeGNN`

The receipt at commit `c6c81ea0c344485fa536a1b1bcd8c1b0ccaaf684` reports:

- 6/6 checks; positive 4/4; negative 1/1; boundary 1/1;
- `n_terrain=4`, `n_shell=4`, `n_operator=3`, `n_layers=3`;
- shell-effect conditional-information difference \(0.625633955001831\);
- maximum terrain-state difference \(0.7621855139732361\);
- valid local density matrices in all three layers;
- gradients through the message layers.

Two shell parameters had exactly zero recorded gradient: `shell_L4.depol_p` and `shell_L6.depol_p`. The result is historical because its path is absent at the active tip and the active source blob differs from its receipt-bound source.

#### Current engine-estate graph probe

`system_v8/engine_estate/results/torch/receipt.json` reports:

- Python 3.13.6;
- torch 2.11.0;
- torch-geometric 2.7.0;
- 13/13 checks;
- `Data.validate()` succeeds across nine capacity graphs;
- `MaxProp` fixed-point partitions exactly agree with pure-Python union-find on all nine graphs;
- claim ceiling: `working-sim estate probe; not canonical, not proof-level`;
- promotion false.

This validates capacity-graph tooling, not a dynamical multi-node engine field.

#### PR #3

The fresh replay confirms 26/26 checks for a dense N=3 carrier. Its \(\mathbb Z_5\) cochain is a topology/renesting control and is never passed as a local message between blankets.

### KNOWN GAPS, STRESS HOLES, OR CONFLICTS

1. No \(N>3\) whole-manifold execution.
2. No `MarkovBlanket` or equivalent typed API.
3. No variable-to-factor and factor-to-variable message types.
4. No local factor potentials.
5. No compressed boundary-cochain receipt schema.
6. No local fixed-point settlement plus separate global reconstruction validation.
7. No sparse/treewidth scaling benchmark against dense global evaluation.
8. Historical `CascadeGNN` uses complete-bipartite terrain-to-shell and terrain-to-operator links.
9. Every `CascadeGNN` shell receives the same aggregate terrain information; locality is not preserved.
10. PR #3 reshapes and traces one dense \(8\times8\) density matrix and is fixed to three qubits.
11. Its cochain control is not attached to a graph-message payload.
12. No injected boundary-message corruption test exists.
13. No test proves changing data outside \(B_v\) leaves \(v\)'s update unchanged.
14. No localized-versus-dense exact comparison exists on a tractable \(N>3\) case.
15. The historical GNN receipt is absent at the active branch and binds an older source blob.
16. The dossier explicitly prevents promotion of the current graph drive to a dynamical-engine claim.

### SOURCE CODE / LEDGER SNIPPET

Complete current PyG primitive and graph conversion:

```python
class SumMessage(MessagePassing):
    def __init__(self):
        super().__init__(aggr="add")

    def forward(self, x, edge_index):
        return self.propagate(edge_index, x=x)

    def message(self, x_j):
        return x_j


def build_cycle_graph():
    graph = nx.DiGraph()
    graph.add_node("a", feature=1.0)
    graph.add_node("b", feature=2.0)
    graph.add_node("c", feature=3.0)
    graph.add_edges_from([("a", "b"), ("b", "c"), ("c", "a")])
    return graph


def networkx_incoming_sum(graph):
    return {
        node: sum(float(graph.nodes[src]["feature"]) for src in graph.predecessors(node))
        for node in graph.nodes
    }


def graph_to_pyg(graph, *, node_order=None):
    order = list(node_order or graph.nodes)
    if len(set(order)) != len(order) or set(order) != set(graph.nodes):
        raise ValueError("node_order must contain each NetworkX node exactly once")

    index = {node: idx for idx, node in enumerate(order)}
    edge_pairs = []
    for src, dst in graph.edges:
        edge_pairs.append([index[src], index[dst]])
    if edge_pairs:
        edge_index = torch.tensor(edge_pairs, dtype=torch.long).t().contiguous()
    else:
        edge_index = torch.empty((2, 0), dtype=torch.long)

    x = torch.tensor([[float(graph.nodes[node]["feature"])] for node in order])
    data = Data(x=x, edge_index=edge_index, num_nodes=len(order))
    data.validate(raise_on_error=True)
    return data, index
```

Complete historical all-to-all graph construction:

```python
def _build_edge_indices(self):
    """Build all edge index tensors for the hetero graph."""
    n_t = self.n_terrain
    n_o = self.n_operator
    n_s = self.n_shell

    t_src = torch.arange(n_t).repeat_interleave(n_s)
    s_dst = torch.arange(n_s).repeat(n_t)
    t_to_s_ei = torch.stack([t_src, s_dst])

    s_src = torch.arange(n_s).repeat_interleave(n_t)
    t_dst = torch.arange(n_t).repeat(n_s)
    s_to_t_ei = torch.stack([s_src, t_dst])

    t_src2 = torch.arange(n_t).repeat_interleave(n_o)
    o_dst = torch.arange(n_o).repeat(n_t)
    t_to_o_ei = torch.stack([t_src2, o_dst])

    o_src = torch.arange(n_o).repeat_interleave(n_t)
    t_dst2 = torch.arange(n_t).repeat(n_o)
    o_to_t_ei = torch.stack([o_src, t_dst2])

    return t_to_s_ei, s_to_t_ei, t_to_o_ei, o_to_t_ei
```

Complete PR #3 dense partial trace:

```python
def partial_trace(rho: Array, keep: Sequence[int], dims: Sequence[int] = (2, 2, 2)) -> Array:
    """Trace out all factors not in ``keep``; retained factors keep input order."""

    keep_tuple = tuple(keep)
    if tuple(sorted(keep_tuple)) != keep_tuple:
        raise ValueError("keep must be in ascending subsystem order")
    n = len(dims)
    arr = np.asarray(rho, dtype=complex).reshape(tuple(dims) + tuple(dims))
    live_dims = list(dims)
    for axis in sorted(set(range(n)) - set(keep_tuple), reverse=True):
        arr = np.trace(arr, axis1=axis, axis2=axis + len(live_dims))
        live_dims.pop(axis)
    d = int(np.prod(live_dims, dtype=int)) if live_dims else 1
    return hermitize(arr.reshape((d, d)))
```

The strict result is: sparse graph primitives and one dense N=3 whole-state model exist, but localized \(N>3\) factor-graph settlement remains an implementation candidate.

---

## Mechanism 4

**MECHANISM NAME:** Parameterized Covariant CPTP Fibre Channels

### REPOSITORY PATHS AND COMMITS

The repository contains three relevant but presently separate implementation families: a globally drive-scaled GKSL evolution, fixed CPTP channel banks with Choi tests, and PR #3's fixed-parameter three-node instruments. None currently implements a node-local pressure field derived from the nested manifold and proved natural across restriction fibres.

Repository: `Joshua-Eisenhart/Codex-Ratchet`  
Audited branch: `session/r0-three-engine-probes`  
Observed branch commit: `0c6ea14b9c20223aa5231a0abf9afa59f7b4ac08`

| Path | Blob / commit | What it actually supplies |
|---|---|---|
| `system_v8/deep_integration/manifold_qit_engines_full.py` | blob `4d12d140ff24edf4dd8979aecb0cb8566d46135f` | A real two-engine QuTiP tick loop in which one global Hartley-derived scalar rescales a GKSL jump rate. |
| `system_v8/deep_integration/results/full_sim/receipt.json` | blob `fb77803163818c914af4f189f5403672dfad03e8` | The 60-tick scratch-ceiling receipt for that loop. |
| `system_v8/upper_manifold/axis8_field_v0.py` | blob `fb5bd1decbfdaf174331079164fb09bd4588129a` | Eight fixed channel generators, Choi checks, and pairwise order comparisons. |
| `system_v8/upper_manifold/results/axis8_field_v0_results.json` | blob `b83e05ff18a7053d11d4b6e480efa0f58dffd311` | CPTP and order-gap receipts for the fixed channel bank. |
| `MODEL_DOSSIER/04_LAYERS_L9_UP_AND_FIELD.md` | active branch | Explicitly says the relevant substrates have not yet been merged into one field implementation. |
| `system_v4/probes/sim_pure_lego_channels_choi_lindblad.py` | blob `25f849a60eec41f685bf8effb20b877695c79c25`, introduced at commit `243c5770906e58b9a47d2faf37675702020fc858` | Fixed Kraus/Lindblad/Choi calibration with completeness, dilation, fixed-point, and SMT checks. |
| `system_v4/probes/a2_state/sim_results/pure_lego_channels_choi_lindblad_results.json` | blob `e5a54b2c1804e78620568e64e23cfda114649f7f` | Receipt for that fixed-channel calibration. |

Draft PR #3 head: `80b05258e262484f193e75ab822c15ed23f91368`  
Local audited checkout: `work/n3_whole_manifold_sim/`  
Relevant source blob: `87146b1ef5b05d80d70d2663cd2d5596431fecc9`  
Relevant test blob: `b91e4a95d74b7382a3c599ca42df0a09e648d7cd`  
Committed receipt blob: `b4cfa148b17390bee8e795464457884a3c9019fb`

PR #3 supplies fixed dephasing and depolarizing Kraus families plus state-dependent competition among four schedule hypotheses. It does not supply a pressure-indexed channel field or a proof of covariance across subsystem restrictions.

### FORMAL OBJECTS & TYPED DOMAINS

The mechanism requested by the interrogation protocol is not merely “a channel with a tunable number.” It requires a field of channel parameters derived from local combinatorial pressure and a naturality law tying those channels to the nested restriction system.

Let \(V(G)\) be the node set of the current nesting diagram, let \(\mathfrak M_G\) be its settled whole-manifold state space, and let \(\Lambda_v\) be the admissible parameter space at node \(v\). The missing pressure-to-parameter map has type

\[
P_v:\mathfrak M_G\longrightarrow\Lambda_v,
\qquad
x\longmapsto\lambda(v;x).
\]

A parameterized local quantum channel must then be a map

\[
\Phi_v:\Lambda_v\longrightarrow
\operatorname{CPTP}\!\left(\mathcal B(\mathcal H_v),\mathcal B(\mathcal H_v)\right).
\]

Equivalently, for each admissible \(\lambda\in\Lambda_v\), there must exist Kraus operators

\[
K_{v,a}(\lambda)\in\mathcal B(\mathcal H_v),
\qquad
\Phi_{v,\lambda}(\rho)
=\sum_a K_{v,a}(\lambda)\rho K_{v,a}(\lambda)^\dagger,
\]

with the completeness identity

\[
\sum_aK_{v,a}(\lambda)^\dagger K_{v,a}(\lambda)=I_v
\qquad\text{for every admitted }\lambda.
\]

For a subsystem inclusion \(B\subseteq A\), write

\[
C_{AB}:\mathcal B(\mathcal H_A)\to\mathcal B(\mathcal H_B),
\qquad
C_{AB}(\rho_A)=\operatorname{Tr}_{A\setminus B}(\rho_A).
\]

Its restriction to density operators maps \(\mathcal D(\mathcal H_A)\) into \(\mathcal D(\mathcal H_B)\).

The required coarse-graining covariance is the commuting square

\[
C_{AB}\circ\Phi_{A,\lambda_A}
=\Phi_{B,\lambda_B}\circ C_{AB},
\]

where the parameters themselves must be compatible with restriction, for example through an explicitly declared map \(r_{AB}:\Lambda_A\to\Lambda_B\) satisfying

\[
\lambda_B=r_{AB}(\lambda_A)
\quad\text{and}\quad
r_{BC}\circ r_{AB}=r_{AC}
\qquad(C\subseteq B\subseteq A).
\]

Without that parameter-consistency law, separately CPTP local maps do not constitute a covariant channel over the inverse system.

The strongest current partial implementation uses the packet-derived scalar

\[
\lambda_t=\frac{\Delta C_t}{\overline{\Delta C}},
\]

where \(\Delta C_t\) is a Hartley-capacity increment, and rescales the dissipative term of a GKSL generator:

\[
\mathcal L_{e,k,\lambda_t}(\rho)
=-i[H_{e,k},\rho]
+\lambda_t\gamma_{e,k}
\left(
J_{e,k}\rho J_{e,k}^\dagger
-\frac12\{J_{e,k}^\dagger J_{e,k},\rho\}
\right).
\]

For \(\lambda_t\gamma_{e,k}\ge 0\), this is a legitimate parameterized GKSL generator and

\[
\Phi_{e,k,\lambda_t}^{\Delta t}=e^{\Delta t\mathcal L_{e,k,\lambda_t}}
\]

is CPTP. But \(\lambda_t\) is one global packet scalar shared by the engines. It is not a node-local function of multi-shell cochain discrepancy, extension-fibre pressure, graph stress, or a survivor-Laplacian gradient. No restriction-naturality equation is tested.

PR #3's dephasing and depolarizing channels have the standard forms

\[
\Phi_{\mathrm{deph},p}^{(A)}(\rho)
=(1-p)\rho+pA\rho A,
\qquad A\in\{X,Y,Z\},\quad 0\le p\le1,
\]

and

\[
\Phi_{\mathrm{dep},p}(\rho)
=\left(1-\frac{3p}{4}\right)\rho
+\frac p4(X\rho X+Y\rho Y+Z\rho Z).
\]

These are valid CPTP families at fixed \(p\). In the current code, however, their strengths are authored stage constants rather than values generated by a typed pressure map \(P_v\).

One further distinction is load-bearing. PR #3's `H_select` selects an operator after directly inspecting the simulator's current density matrix. Although every selected branch is CPTP, the state-dependent selector is not automatically a single linear CPTP map on an unknown physical input. A physical realization would require an explicit quantum instrument

\[
\mathcal I_y:\mathcal B(\mathcal H)\to\mathcal B(\mathcal H),
\qquad
\mathcal I_y\ \text{CP and trace-nonincreasing},
\]

with

\[
\sum_y\mathcal I_y\ \text{CPTP}.
\]

Channel selection must then depend on the explicit measurement outcome \(y\), and \(y\) must remain in the enlarged classical-quantum state and receipt. Merely retaining a selector label after `candidate_selection_key(..., rho)` has inspected \(\rho\) is insufficient; without a measurement realization, that code remains a simulator policy rather than a physical instrument.

### EXECUTABLE IMPLEMENTATION (yes/no)

**No for the mechanism as requested. Partial components are executable.**

What is executable now:

1. A real GKSL loop with a nonnegative global drive scalar derived from packet Hartley increments.
2. Fixed CPTP channel banks with normalized Choi-state tests and noncommuting-order comparisons.
3. Fixed-parameter dephasing/depolarizing channels in the three-node whole-state simulation.
4. State-dependent selection among individually valid channel candidates.

What is not executable now:

1. A local pressure field \(\lambda:V(G)\to\Lambda\) computed from multi-shell combinatorial discrepancies.
2. A map from cochain stress or survivor-graph stress into Kraus/Lindblad parameters.
3. A tested natural transformation connecting those channels across every restriction \(C_{AB}\).
4. A parameter-family proof or sweep establishing CPTP for all values the pressure law can produce.
5. An explicit instrument record making adaptive operator selection a well-typed quantum operation.

Accordingly, the current code supports the status **executed calibration / partial implementation**, not **repository implementation of parameterized covariant CPTP fibre channels**.

### RUNTIME / TEST ARTIFACTS & RECEIPTS

#### Global Hartley-scaled GKSL loop

`system_v8/deep_integration/results/full_sim/receipt.json` records:

| Field | Value |
|---|---:|
| Schema | `ratchet.v8.deep_integration.full_sim.v0` |
| Python | `3.13.6` |
| QuTiP | `5.2.3` |
| NumPy | `2.3.4` |
| Ticks | `60` |
| Step size | `0.35` |
| Checks | `23/23` |
| Minimum state eigenvalue | `3.891246178717822e-15` |
| Maximum trace error | `3.3306690738754696e-16` |
| Promotion | `false` |
| Formal claim | `false` |

This is substantive evidence that the implemented global drive modulation preserves sampled density-matrix positivity and unit trace over 60 ticks. It is not a universal parameter-family proof and does not test restriction covariance.

#### Axis-8 fixed channel bank

`system_v8/upper_manifold/results/axis8_field_v0_results.json` records:

- eight fixed channels;
- maximum trace-preservation defect `1.136456079282149e-15`;
- minimum normalized-Choi eigenvalue `2.3267465210995387e-5`;
- all 64 ordered pair compositions CPTP under the implemented checks;
- noncommuting order gaps from `0.07238` to `0.943079`;
- QuTiP agreement for three selected pairs;
- 14 measured order-response clusters;
- scratch/calibration standing rather than proof standing.

This establishes a useful finite channel reservoir and order sensitivity. It does not make the channels pressure-responsive.

#### Fixed Lego-channel calibration

`system_v4/probes/a2_state/sim_results/pure_lego_channels_choi_lindblad_results.json` records:

- ten fixed channel cases;
- complete positivity, trace preservation, and Kraus-completeness checks passing;
- maximum round-trip error `4.440892098500626e-16`;
- three fixed-point checks;
- a Stinespring-dilation check;
- four Z3 checks;
- elapsed time `0.182` seconds;
- baseline/calibration claim ceiling.

This is independent evidence that the fixed channel constructions are numerically coherent. It does not evaluate a continuum or finite grid of pressure-indexed parameter values.

#### PR #3 three-node whole-state simulation

Fresh local replay on 2026-07-22 used Python `3.12.13` and NumPy `2.3.5`. It passed 12/12 unit tests and 26/26 receipt checks. Its receipt includes:

| Check | Value |
|---|---:|
| Minimum sampled Spohn production | `-1.9984014443252818e-15` |
| Minimum sampled DPI drop | `-2.8033131371785203e-15` |
| Maximum invariant marginal error | `6.661338147750939e-16` |
| Fresh receipt SHA-256 | `20972558fafa6e95e8f5cb5fc416b0f06ef9884ea443806d17723f20d818f676` |

The tiny negative minima are within floating-point tolerance. The replay does not contain a per-stage normalized Choi receipt, a parameter grid, or a restriction-naturality test.

### KNOWN GAPS, STRESS HOLES, OR CONFLICTS

1. **No typed multi-shell pressure object.** The repository does not define whether pressure is a 0-cochain, 1-cochain divergence, fibre-capacity gradient, Laplacian residual, or another typed object.
2. **No node field.** There is no implemented \(\lambda:V(G)\to\Lambda\).
3. **Global rather than local drive.** The existing \(\Delta C_t/\overline{\Delta C}\) scalar is packet-wide and shared across both engines.
4. **No M1/M2 weld.** Cochain discrepancy and graph stress do not feed channel parameters.
5. **No restriction covariance test.** No executable check evaluates \(C_{AB}\circ\Phi_A=\Phi_B\circ C_{AB}\).
6. **No parameter consistency maps.** The code does not define \(r_{AB}:\Lambda_A\to\Lambda_B\).
7. **No family-wide Choi proof.** Fixed parameter points are checked; the admitted parameter domain is not.
8. **No family-wide Kraus-completeness sweep.** Boundary and adversarial parameter values are absent.
9. **No extreme-pressure controls.** Negative, zero, maximal, discontinuous, and singular pressure cases are not jointly specified and tested.
10. **Separate channel estates.** The global GKSL loop, Axis-8 channel bank, Lego channels, and PR #3 instruments are not one canonical implementation.
11. **Authored stage strengths.** PR #3 uses stage-dependent constants such as `0.22 + 0.025*i` and angles such as `0.13 + 0.011*i`; these are not ratcheted from pressure.
12. **Adaptive-selection linearity hole.** Choosing the best channel as a function of \(\rho\) does not, by itself, define a linear CPTP superoperator.
13. **Missing physical selector instrument.** The adaptive branch needs CP trace-nonincreasing outcome maps whose sum is CPTP, selection conditioned on an actual instrument outcome, and retention of that classical outcome. A post hoc selector label alone is insufficient.
14. **No modulation deletion witness.** There is no ablation showing that removing pressure responsiveness changes a declared whole-manifold obligation.
15. **No pressure-permutation control.** Shuffling pressure labels across nodes has not been required to degrade the correct result.
16. **No zero-pressure identity/base-channel proof.** The intended limit at \(\lambda=0\) is not defined across all channel families.
17. **No equal-shell naturality control.** Identical coarse/fine pressures are not used to verify the commuting square.
18. **Exogenous rather than feedback parameter sweeps.** Existing upper-manifold JAX sweeps do not close the loop from engine receipt to manifold pressure to new channel.
19. **Sampled physicality is narrower than family physicality.** Positive sampled states do not prove the entire generated channel family CPTP.
20. **The dossier itself preserves the gap.** `MODEL_DOSSIER/04_LAYERS_L9_UP_AND_FIELD.md` says the relevant substrates have not yet been merged.

The principal semantic conflict is therefore not “CPTP channels absent” versus “CPTP channels present.” Fixed CPTP maps and a globally scaled GKSL loop are present. The stronger claim that *local combinatorial manifold pressure covariantly parameterizes every engine fibre channel* is absent.

### SOURCE CODE / LEDGER SNIPPET

The existing global drive-scaled implementation is:

```python
def engine_step(rho, st, which, scale):
    """One qutip mesolve step of one engine on its sheet, gamma scaled by drive."""
    H = embed(sheet_h(st), which)
    g_eff = st["gamma"] * scale
    c_ops = [embed(np.sqrt(g_eff) * JUMP[st["a"]], which)] if g_eff > 0 else []
    res = qt.mesolve(H, rho, [0.0, DT], c_ops=c_ops)
    return res.states[-1]
```

Its enclosing loop shows that the same packet-derived scalar is applied before each engine's stage and that the inter-engine coupling is a separate unitary:

```python
for t in range(t_start, t_start + n_ticks):
    dC = 0.0 if mode == "freeze" else dC_ticks[t]
    scale = dC / dC_mean
    stL, stR = lorder[t % 8], rorder[t % 8]
    rho = engine_step(rho, stL, "L", scale)
    rho = engine_step(rho, stR, "R", scale)
    if couple:
        rho = U_COUPLE * rho * U_COUPLE.dag()
```

PR #3's fixed Kraus constructors are:

```python
def dephase_kraus(axis: Array, strength: float) -> tuple[Array, Array]:
    p = float(np.clip(strength, 0.0, 1.0))
    return np.sqrt(1.0 - p) * I2, np.sqrt(p) * axis

def depolarizing_kraus(strength: float) -> tuple[Array, Array, Array, Array]:
    p = float(np.clip(strength, 0.0, 1.0))
    return (
        np.sqrt(1.0 - 3.0 * p / 4.0) * I2,
        np.sqrt(p / 4.0) * X,
        np.sqrt(p / 4.0) * Y,
        np.sqrt(p / 4.0) * Z,
    )
```

The adaptive hypothesis code is:

```python
def stage_transform(
    rho: Array,
    stage: Stage,
    hypothesis: str,
    selected_operator: str | None = None,
) -> tuple[Array, str | tuple[str, ...]]:
    if hypothesis == "H_native":
        return apply_stage_map(rho, stage, stage.native_operator), stage.native_operator
    if hypothesis == "H_select":
        if selected_operator is None:
            trials = [(op, apply_stage_map(rho, stage, op)) for op in OPERATORS]
            selected_operator, selected_state = max(
                trials, key=lambda item: candidate_selection_key(item[1], rho)
            )
            return selected_state, selected_operator
        return apply_stage_map(rho, stage, selected_operator), selected_operator
    if hypothesis == "H_all4":
        out = rho
        for op in OPERATORS:
            out = apply_stage_map(out, stage, op)
        return out, OPERATORS
    if hypothesis == "H_mix":
        outputs = [apply_stage_map(rho, stage, op) for op in OPERATORS]
        return hermitize(sum(outputs) / len(outputs)), OPERATORS
    raise KeyError(hypothesis)
```

Each branch is executable. The missing object is the natural, pressure-indexed family connecting those branches to the nested restriction geometry. The strict result is therefore: **real CPTP machinery plus a real globally driven GKSL partial implementation, but no local multi-shell-pressure covariant channel field.**

---

## Mechanism 5

**MECHANISM NAME:** ClaimGate Semantic Witness Binding & Registry Enforcement

This mechanism spans two repositories and several distinct authority levels: Codex-Ratchet's deterministic gates and floor, and Lev's non-final Claim-submission/runtime-admission boundary. They must not be collapsed into one supposedly completed gate.

### REPOSITORY PATHS AND COMMITS

#### Codex-Ratchet

Repository: `Joshua-Eisenhart/Codex-Ratchet`  
Audited branch: `session/r0-three-engine-probes`  
Observed branch commit: `0c6ea14b9c20223aa5231a0abf9afa59f7b4ac08`

| Path | Blob SHA |
|---|---|
| `claimgate/claimgate.py` | `1a28f4309a1059980ce183df5f7bfe3542087dd1` |
| `claimgate/results/first_sweep.json` | `5c34dc5760466b62f8d88d6dc096f0631030ce48` |
| `claimgate_plugin/claimgate.mjs` | `7c5867c69237989721bcdd6152deb6998addd63b` |
| `claimgate_plugin/claim_verify.py` | `0d0c24f73f55cfe3d7ae4da312efa80b88779b66` |
| `claimgate_plugin/gate_registry.json` | `e39c46b65cb4f260f5173cf349b667cca6639592` |
| `claimgate_plugin/ratchet_floor.py` | `56faf0bcaea3246d5d148e255f3d18e7967e8e66` |
| `claimgate_plugin/stress_manifest.json` | `8765fb71d658cd168164dd97965e23d7528dddf9` |
| `claimgate_plugin/stress/CROSS_MODEL_STRESS_LEDGER.md` | `70e492492e6f7387cb8831011c2118abf5013f0b` |
| `claimgate_plugin/stress/holes/smt_clean_tautology_admitted_by_both_gates.json` | `9bb59cacd46c2154c16fe5105e7c2dfbafde9e0f` |
| `claimgate_plugin/stress/holes/floor_renamed_key/receipt.json` | `088209bb74c875b34a5eb500a49658cb3f665230` |
| `claimgate_plugin/LEV_WIRING.md` | `04b39b805734ad6d99d1aa4dc550f1025fd94a78` |

Commit `0c6ea14b9c20223aa5231a0abf9afa59f7b4ac08` adds fired-side enforcement hooks:

- `claimgate_plugin/hooks/install_git_hooks.sh`
- `claimgate_plugin/hooks/pre_commit_gate_receipts.sh`

The pre-commit hook runs the post-receipt gate over staged JSON receipts. Exit codes `0` and `3` allow the commit, while exit `1` blocks it. Tooling failures warn and allow the commit. This improves routine invocation; it does not repair the semantic-witness holes below.

Draft PR #3 has head `80b05258e262484f193e75ab822c15ed23f91368` and base `0c6ea14b9c20223aa5231a0abf9afa59f7b4ac08`. Its N=3/reconciliation changes do not repair these ClaimGate holes.

#### Leviathan

Repository: `lev-os/leviathan`  
Audited branch: `main`  
Observed main commit: `1efe47f4b41878ebbc1eed8e87da8e3c80a2e5a9`

| Path | Blob SHA |
|---|---|
| `.lev/pm/tasks/claim-admission-v1/dna.yaml` | `16684cb588a42efd657a93a537e0610570408e10` |
| `.lev/pm/tasks/claim-admission-v1/execution.yaml` | `6e88e54b740156aa66b0922011144294f4439816` |
| `core/domain/src/claim.ts` | `97aa8649bd556ad8ee3b95e3e1c5bd6662ccdd21` |
| `core/exec/src/handlers/done.ts` | `b799c2aa2b818cfb143f03433df699c13be9b398` |
| `core/exec/src/handlers/done.test.ts` | `c14a20faca159c63e02e28a3b9e1f73d30cf6cb3` |
| `core/exec/src/execution/dispatch/shared.ts` | `72c3ed954926e642484efefa96fae9ef92acf8ff` |
| `core/eval/src/proof-bundle.ts` | `9fb7f226317a3535ce223146450fc4ebab783f2f` |
| `core/telemetry/src/evidence-validation.ts` | `eb249f26775558b091265a183c195ae6e2f78f9b` |

The intended implementation path is absent on audited `main`:

```text
core/exec/src/claim/claim-admission.ts
```

GitHub returned `NOT_FOUND` for that path. Commit `5a37c9e4bd2b0acaba2195e13a02fb3a60cd68e4` introduced or updated the current task and `lev.done` assurance surfaces. Its recorded validation is:

```text
lev task validate claim-admission-v1 ready=true
```

That establishes specification readiness, not runtime implementation.

Merged PR #223 contains `docs/_inbox/20260619-claimgate-leviathan-convergence.md`. It is explicitly draft/noncanonical and proposes ClaimGate as a plugin consuming core execution/evaluation evidence, rather than a second verdict authority. It is not an executable admission implementation.

No GitHub-visible active branch or PR was found implementing the current semantic-binding patch. A local/unpushed Lev patch may exist, but it cannot be counted as repository evidence.

### FORMAL OBJECTS & TYPED DOMAINS

#### Codex structural gate

Let

\[
\mathcal R=\{\text{JSON receipt objects}\},
\qquad
\mathcal P=\{\text{external gate registries and policies}\},
\qquad
\mathcal E=\{\text{execution environments}\}.
\]

The effective verification map is

\[
G:\mathcal R\times\mathcal P\times\mathcal E
\longrightarrow
\{\mathrm{VERIFIED},\mathrm{REJECTED},\mathrm{INSUFFICIENT\_DEPTH},\mathrm{ERROR}\}
\times\mathrm{EvidenceRefs}.
\]

The gate checks structural consistency, declared status, controls, preregistration, same-receipt recomputation, and registered external commands. It does not establish semantic entailment:

\[
\text{execution receipt}\models\text{claim}.
\]

There is no implemented typed witness

\[
W=(\varphi,\beta_{\mathrm{sem}},\mathcal A,d_{\mathcal A},\nu),
\]

where \(\varphi\) is the claim; \(\beta_{\mathrm{sem}}\) maps its symbols to concrete measured quantities; \(\mathcal A\) is a content-addressed execution artifact; \(d_{\mathcal A}=\operatorname{SHA256}(\mathcal A)\); and \(\nu\) is an independent verifier result or protected attestation.

#### Ratchet floor

The floor state is

\[
\mathcal S=(F,L),
\]

where

\[
F:K\rightharpoonup
\mathbb R\times
\{\text{higher-is-better},\text{lower-is-better}\}
\times\mathrm{Provenance}
\]

is a partial map from claim keys to retained floors, and \(L\) is a hash-linked transition log. Its transition is

\[
T:\mathcal S\times\mathcal R\times\{\mathrm{allowNew},\mathrm{denyNew}\}
\to
\mathcal S\times\{\mathrm{ADMITTED},\mathrm{REJECTED},\mathrm{PARKED}\}.
\]

This enforces monotonic numeric floors for stable keys. It does not establish semantic identity between renamed keys.

#### Leviathan Claim schema

The current domain type is effectively

\[
\mathrm{Claim}=
(\mathrm{schemaId},\mathrm{summary},[(id,type,value,[evidenceRef])]).
\]

The exact interface is:

```ts
export interface ClaimRow {
  readonly id: string;
  readonly type: string;
  readonly value: unknown;
  readonly evidence_refs: readonly string[];
}

export interface Claim {
  readonly schema_id: typeof CLAIM_SCHEMA_ID;
  readonly summary: string;
  readonly claims: readonly ClaimRow[];
}
```

The current non-final submission operation is

\[
D:\mathrm{DoneSubmissionInput}\times\mathrm{DoneDeps}
\to\mathrm{DoneCommandResult}.
\]

For submitted bytes \(b\), it computes \(d=\operatorname{SHA256}(b)\). The actual evidence-reference shape is approximately

\[
E=(
\mathrm{artifactRef},
\mathrm{executionId},
\mathrm{invocationId},
\mathrm{label}=\texttt{"lev.done:"}\mathbin\Vert d
),
\]

while \(d\) is also returned separately as `data.claim_digest`. The digest is not a dedicated `EvidenceRef` field.

The intended but absent admission map is

\[
A:\mathrm{ClaimBytes}\times\mathrm{RuntimeBinding}\times\mathrm{Contract}\times\mathrm{EvidenceStore}
\to
\mathrm{AdmittedClaim}\sqcup\mathrm{ValidationErrors}.
\]

### EXECUTABLE IMPLEMENTATION (yes/no)

**No for end-to-end semantic witness binding.** Codex has several executable structural gates; Lev has a real non-final byte-submission operation. The map that binds claim meaning to independent execution evidence is absent.

#### Executable Codex pieces

`claimgate/claimgate.py` is a deterministic Python validator with six broad checks:

1. classification;
2. promotion label;
3. verdict/pass consistency;
4. controls and control-copy checks;
5. nonnegative mutual information;
6. preregistration.

It is a structural receipt gate, not theorem-to-execution binding.

`claimgate_plugin/claimgate.mjs` is an executable Node validator. Its provenance rule can be satisfied by a nonempty sibling value under keys containing tokens such as:

```text
raw
data
source_path
sha256
detail
evidence
```

It does not necessarily resolve the artifact, calculate its digest, or replay it. Its recomputation rule can recompute a declared value from a raw array in the same receipt. An absent recomputation contract is generally a note, not a rejection.

`claimgate_plugin/claim_verify.py` is an executable tier dispatcher:

- Tier 0 invokes the structural gate.
- Tier 1 performs same-receipt recomputation.
- Tiers 2 and 3 execute commands from external `gate_registry.json`.
- Tier 4 checks an audit token, auditor identity, and evaluation deck.
- A sibling audit file is hashed before tiers run, preventing a tier process from silently generating or replacing it during verification.

This correctly prevents the receipt from authoring its own tier command. It does not bind the registered gate's output to the claim through a cryptographic semantic envelope.

`claimgate_plugin/ratchet_floor.py` executes the floor transition and hash-chain write. An unknown key normally `PARK`s with exit code `3`. Under `--allow-new-keys`, it is admitted without passing through the rename detector.

The fired-side pre-commit hook makes accidental omission harder. It remains best-effort on tooling failure and does not solve semantic vacancy.

#### Executable Lev piece

`core/exec/src/handlers/done.ts`:

- reads inline content or bytes from the exact declared answer path;
- computes full SHA-256 over submitted bytes;
- optionally checks `expected_content_hash`;
- appends an execution-ledger evidence reference;
- emits a non-final result;
- explicitly sets `next_action: "await_claim_admission"`.

The runtime admission described by `claim-admission-v1` is absent. That task requires authenticated execution, invocation, subject, contract ref/digest, immutable payload ref/digest, resolved evidence, and non-final admission semantics. It names `core/exec/src/claim/**` as the build surface, but its principal implementation file is missing.

### RUNTIME / TEST ARTIFACTS & RECEIPTS

Selected aggregate fields from `claimgate/results/first_sweep.json` are:

| Field | Value |
|---|---:|
| `total` | 109 |
| `admit` | 62 |
| `reject` | 47 |

This is a committed repository artifact dated by surrounding documentation to 2026-07-20; it was not freshly rerun in this connector audit.

The committed stress result is intentionally red:

```text
17 cases
13 ok
4 failures
trusted: false
verdict: GATE_REJECTED
```

The four failing routes expose three substantive hole classes:

1. canonical classification can avoid required controls and preregistration;
2. a semantically vacant SMT tautology is accepted as a mechanism proof;
3. a renamed floor key bypasses the existing floor under `--allow-new-keys`.

The repository correctly records these as failures. Changing their expectations merely to obtain green would delete the evidence.

`claimgate/README.md` records a working Lev wrapper invocation using both `--until` and `--verifier`:

```text
execId=473cd6c1e00e
event=exec.gate.run
branch=fail
exit=1
```

A prior bare `--verifier` invocation without `--until` did not execute the verifier and produced a placeholder `passed:true`:

```text
execId=4b834881e6b2
```

`claimgate_plugin/LEV_WIRING.md` records local July 22 checks using:

```text
core/poly/bin/lev orchestration claimgate-steering consume
```

It reports a good recomputed fixture reaching `host_consumed`, a bad overclaim refused, and a real `cut_dependent_entropy.json` exit-3 path conditionally reaching `host_reviewed_failed`. These are Codex-side ledgers about a live Lev checkout; the corresponding implementation was not independently located on current GitHub `lev-os/leviathan/main`, so they are not promoted to a fresh main-branch receipt.

`core/exec/src/handlers/done.test.ts` covers successful non-final artifact recording, digest mismatch before ledger append, and incorrect payload path before ledger append. Its successful test confirms the handler does not invoke admission, sealing, or lease mutation. No fresh Lev test execution was performed in this connector-only audit.

### KNOWN GAPS, STRESS HOLES, OR CONFLICTS

#### Hole 1: an SMT tautology is accepted as a mechanism proof

Complete failing fixture:

```json
{
  "receipt_id": "sim-clean-smt",
  "verdict": "PASS",
  "pass": true,
  "preregistered": {
    "trace_irreversibility_proof": "z3 UNSAT proves partial trace irreversible"
  },
  "checks": {
    "trace_irreversibility_proof": {
      "verdict": "PASS",
      "pass": true,
      "smt_encoding": "forall k, A, B: (recover(k) == A and recover(k) == B) implies (A == B)",
      "z3_role": "load_bearing",
      "solver_output": "unsat",
      "interpretation": "solver confirmed recovery cannot yield two states -> irreversibility of partial trace mechanism"
    }
  },
  "classification": "canonical"
}
```

Both Python and Node gates admit it. The formula states only the single-valuedness of a function:

\[
f(k)=A\land f(k)=B\implies A=B.
\]

It proves neither irreversibility of partial trace nor nonexistence of a recovery channel. The missing object is

\[
\beta_{\mathrm{sem}}:\{\text{symbols in formula}\}
\to
\{\text{actual encoded channel, dimensions, states, constraints, receipts}\}.
\]

No present gate checks that `recover`, \(A\), \(B\), and \(k\) denote the claimed QIT mechanism.

#### Hole 2: canonical classification can avoid stronger rigor checks

Complete admitted fixture:

```json
{
  "classification": "canonical",
  "verdict": "CONFIRMED",
  "promotion_allowed": false,
  "tool_manifest": {
    "monte_carlo_estimator": {
      "tried": true,
      "used": true,
      "reason": "standard"
    },
    "bootstrap_resampler": {
      "tried": true,
      "used": false,
      "reason": "unnecessary"
    }
  },
  "engines_ran": {
    "mean_engine": true,
    "variance_engine": true
  },
  "notes": [
    "Estimated expected value of random walk."
  ],
  "engine_values": {
    "preregistered_hypothesis": "The expected value will be zero.",
    "preregistration_timestamp": "2025-01-01T00:00:00Z",
    "locked_prediction": 0.0
  },
  "result": 0.02,
  "schema_version": "1.3"
}
```

Controlling function:

```python
HIGH_TIER_STATUS_LABELS = {"passes local rerun", "canonical by process"}


def requires_control_rigor(receipt):
    """Only receipts claiming a status above bare 'exists/runs' owe controls +
    a preregistration reference. Bare scratch/tool-fit probes do not."""
    label = str(receipt.get("accepted_status_label", "")).strip().lower()
    return label in HIGH_TIER_STATUS_LABELS or receipt.get("promotion_allowed") is True
```

`classification: "canonical"` does not activate this predicate. The semantic force of the label and the executable rigor trigger disagree.

#### Hole 3: `--allow-new-keys` permits a floor-key rename bypass

Attack receipt:

```json
{
  "floor_claims": [
    {
      "key": "gk.accuracy",
      "value": 0.8,
      "direction": "higher_is_better"
    }
  ]
}
```

Existing floor state:

```json
{
  "floors": {
    "gk.acc": {
      "value": 0.9,
      "direction": "higher_is_better",
      "receipt": "/private/tmp/claude-501/-Users-joshuaeisenhart-Codex-Ratchet/4e94deaf-efb4-4f21-8416-8c730d026545/scratchpad/gate_stress/floor/seed.json",
      "sha": "2c3e2fa39207a140"
    }
  },
  "log": [
    {
      "receipt": "seed.json",
      "sha": "2c3e2fa39207a140",
      "decisions": [
        {
          "key": "gk.acc",
          "action": "new",
          "floor": 0.9
        }
      ],
      "prev_entry_sha256": "GENESIS"
    }
  ]
}
```

Complete rename detector:

```python
def token_similarity(left, right):
    import re
    a = set(t for t in re.split(r"[^a-z0-9]+", left.lower()) if t)
    b = set(t for t in re.split(r"[^a-z0-9]+", right.lower()) if t)
    return len(a & b) / len(a | b) if a | b else 0.0

def nearest_key(key, floors):
    best_key, best_score = None, 0.0
    for existing in floors:
        score = token_similarity(key, existing)
        if score > best_score:
            best_key, best_score = existing, score
    return (best_key, best_score) if best_score >= 0.5 else (None, None)
```

Complete decisive branch:

```python
        cur = floors.get(key)
        if cur is None:
            if allow_new_keys:
                decisions.append({"key": key, "action": "new", "floor": val, "direction": direction})
            else:
                nearest, similarity = nearest_key(key, floors)
                parked.append({"key": key, "reason": "unknown floor key; pass --allow-new-keys to admit",
                               "nearest_existing_key": nearest, "similarity": similarity})
```

Two weaknesses compose:

- `gk.acc` and `gk.accuracy` have token-Jaccard similarity \(1/3<0.5\);
- under `--allow-new-keys`, `nearest_key` is never called.

The renamed key can establish a new floor of `0.8` while `gk.acc=0.9` remains untouched.

#### Hole 4: an external gate result is not cryptographically bound to its claim

Complete registered-tier function:

```python
def _registered_tier(tier_key, receipt, root, reg):
    v = (receipt.get("verification") or {}).get(tier_key)
    if isinstance(v, dict) and "cmd" in v:
        return "FAIL", None, f"receipt declared its own {tier_key}.cmd — producer-authored verification is forbidden (policy must be external)"
    kind = reg["claim_kinds"].get(receipt.get("claim_kind"))
    if not kind:
        return "SKIP", None, f"claim_kind '{receipt.get('claim_kind')}' names no {tier_key} gate"
    gate_name = kind.get(f"{tier_key}_gate")
    if not gate_name:
        return "SKIP", None, f"claim_kind declares no {tier_key} gate"
    gate = reg["gates"].get(gate_name)
    if not gate:
        return "ERROR", gate_name, "registry gate missing"
    rc, out, err = run(gate["cmd"], root)
    if rc is None:
        return "ERROR", gate_name, err[:200]
    rp = gate.get("result_path")
    expect = gate.get("expect", {})
    if rp and expect:
        full = os.path.join(root, rp)
        if not os.path.exists(full):
            return "FAIL", gate_name, f"gate produced no result at {rp}"
        try:
            produced = load(full)
        except Exception as e:
            return "ERROR", rp, str(e)[:120]
        for k, want in expect.items():
            if produced.get(k) != want:
                return "FAIL", rp, f"{k}={produced.get(k)} != {want}"
        return "PASS", rp, f"{gate_name}: {', '.join(f'{k}={want}' for k, want in expect.items())}"
    return ("PASS" if rc == 0 else "FAIL"), gate_name, f"{gate_name} exit {rc}"
```

This correctly externalizes the gate command and re-reads its result file. It does not verify that:

- the result digest is linked to the submitted claim digest;
- the result was freshly produced for this invocation;
- its inputs equal the claim's referenced inputs;
- the command/policy version digest is recorded;
- the artifact is independent of the producer;
- result symbols correspond semantically to claim symbols.

A stale or unrelated result at the configured path can satisfy the expected key/value check unless the invoked command independently prevents it.

#### Hole 5: registry trust is still producer-writable

`gate_registry.json` explicitly records that the registry, decks, and evaluation material reside in the producer-writable repository and immutability is not self-enforced. Moving policy outside a receipt is useful; repository co-location is not an independent trust root.

#### Hole 6: the floor chain is tamper-evident, not full semantic provenance

`ratchet_floor.py` records a hash-linked log and a truncated 16-hex receipt SHA-256 prefix. It does not bind stable key meaning, claim schema, independent verifier, executable contract, or the full numerical evidence chain.

#### Hole 7: `lev.done` binds bytes, not claim semantics

Hashing helper:

```ts
export function stableHash(value: string): string {
  return createHash('sha256').update(value).digest('hex');
}
```

Complete operation:

```ts
export async function runDoneOperation(
  input: DoneSubmissionInput,
  dependencies: DoneOperationDependencies,
): Promise<DoneCommandResult> {
  const claim = claimContent(input, dependencies);
  const digest = stableHash(claim.content);
  if (input.expected_content_hash && input.expected_content_hash !== digest) {
    throw new DoneOperationError('DONE_DIGEST_MISMATCH', 'Claim content digest does not match');
  }
  const evidenceRef: EvidenceRef = {
    kind: 'artifact',
    ref: claim.ref,
    execution_id: dependencies.runtime.execution_id,
    invocation_id: dependencies.runtime.invocation_id,
    label: `lev.done:${digest}`,
  };
  const ledgerResult = await writeExecRunLedger(dependencies.ledger, {
    kind: 'append',
    input: {
      execution_id: dependencies.runtime.execution_id,
      invocation_id: dependencies.runtime.invocation_id,
      evidence_ref: evidenceRef,
      appended_at: dependencies.now(),
    },
  });
  if (!ledgerResult.accepted) {
    throw new DoneOperationError('DONE_LEDGER_REJECTED', 'Execution ledger rejected lev.done evidence');
  }
  const data: DoneOperationResult = {
    operation_id: LEV_DONE_OPERATION_ID,
    state: 'non_final',
    final: false,
    claim_ref: claim.ref,
    claim_digest: digest,
    validation_errors: [],
    next_action: 'await_claim_admission',
    ...(ledgerResult.receipt_id ? { receipt_ref: ledgerResult.receipt_id } : {}),
  };
  return {
    success: true,
    data,
    evidence: {
      artifact_refs: [claim.ref],
      ...(ledgerResult.receipt_id ? { receipt_refs: [ledgerResult.receipt_id] } : {}),
      execution_id: dependencies.runtime.execution_id,
      correlation_id: dependencies.runtime.invocation_id,
    },
  };
}
```

This is a sound non-final submission operation. It deliberately does not admit or prove the claim. Missing bindings include:

- path payload bytes are not parsed and passed through `isClaim` in this handler;
- claim-row `evidence_refs` are not resolved and hashed;
- `claim_contract_digest` is required in runtime state but not compared with actual contract bytes here;
- that contract digest is not carried into this ledger append/result;
- subject and generation identities are not bound;
- no semantic map links claim expressions to receipt quantities;
- no independent numerical verifier output is attached;
- no settlement or sealing occurs.

#### Hole 8: Lev proof bundles are adjacent, not integrated at Claim submission

`core/eval/src/proof-bundle.ts` can hash `files_touched` and `artifact_refs` and requires proof-backed receipt, trace, decision, claim-verdict, and durable-evidence references. `core/telemetry/src/evidence-validation.ts` validates evidence structure, durability, and status. These are useful components, but the present Claim path does not ensure every semantic claim row is covered by one specific hashed numerical witness. The absent claim-admission runtime is the expected integration boundary.

### SOURCE CODE / LEDGER SNIPPET

In addition to the complete fixtures and functions above, the following complete task-ledger acceptance block is the authoritative description of the missing Lev slice:

```yaml
acceptance:
  - "Bare lev done returns the active lev.claim.v1 contract, declared answer path, and remediation without evaluation or finality."
  - "Inline, declared-answer-path, CLI, SDK, and MCP submissions route through one deterministic Claim-admission function."
  - "Valid Claims bind the authenticated execution, invocation, subject, contract ref/digest, immutable payload ref/digest, and resolved evidence refs."
  - "Missing or invalid Claims produce typed validation errors and a bounded same-session nudge; exhaustion holds and escalates without killing evidence or reporting success."
  - "Pane DONE text, exit zero, stale identities, wrong paths, mutated bytes, or model-authored validation cannot produce an admitted Claim."
  - "Runtime Claim and admission records use existing core/config-resolved XDG and execution-ledger routes; project .lev remains authored state only."
```

### CRYPTOGRAPHIC BINDING VERDICT

Codex-Ratchet has structural validation, same-receipt recomputation, externally registered command selection, result-file key/value inspection, audit-file pinning, and floor-history hash chaining. It does **not** have

\[
\operatorname{claim}
\longleftrightarrow
\operatorname{semantic\ witness}
\longleftrightarrow
\operatorname{independent\ immutable\ execution}.
\]

Lev currently has partial byte-level binding:

\[
\operatorname{SHA256}(\text{submitted bytes})
\longleftrightarrow
(\text{execution ID},\text{invocation ID},\text{artifact ref}).
\]

The intended complete admission binding is not implemented. A minimum commitment payload should bind at least

\[
\begin{aligned}
d_{\mathrm{admission}}=\operatorname{SHA256}(&
\mathrm{domainTag}\parallel
\mathrm{canonicalizationVersion}\parallel
\mathrm{claimSchemaDigest}\parallel
\mathrm{canonicalClaimBytes}\parallel
\mathrm{contractDigest}\parallel
\mathrm{executionId}\parallel
\mathrm{invocationId}\parallel
\mathrm{subjectRef}\\
&\parallel\mathrm{policyDigest}\parallel
\mathrm{verifierCommandDigest}\parallel
\mathrm{sourceArtifactManifestDigest}\parallel
\mathrm{receiptArtifactDigest}\parallel
\mathrm{semanticWitnessMapDigest}\parallel
\mathrm{verifierResultDigest}).
\end{aligned}
\]

Every field must use canonical length-delimited or otherwise unambiguous domain-separated serialization. This digest is only a commitment; authenticity and independence additionally require a protected signer/attestation or an append-only trust root outside the producer's write authority.

The semantic witness must be typed:

\[
\beta_{\mathrm{sem}}:\mathrm{ClaimSymbol}\to
(\mathrm{ArtifactDigest},\mathrm{DataSelector},\mathrm{OperatorEncoding},\mathrm{Units},\mathrm{Transformation},\mathrm{VerifierAssertion}).
\]

For SMT claims, admission must additionally require that the formula references the actual claimed operators/dimensions and that a binding mutation or countermodel breaks admission.

### STATUS

| Component | Status |
|---|---|
| Codex structural ClaimGate | Executable repository fact |
| Codex tier dispatcher | Executable repository fact |
| Codex external registry | Active configuration consumed by the executable tier dispatcher; producer-writable trust boundary |
| Ratchet floor | Executable, vulnerable to allowed key-renaming |
| Stress ledger | Executed calibration with intentional red result |
| Semantic SMT witness binding | Absent |
| End-to-end claim-to-independent-receipt digest binding | Absent |
| Fired-side pre-commit enforcement | Active repository fix; does not repair semantic holes |
| Lev `lev.done` byte binding | Executable repository fact |
| Lev `claim-admission-v1` task | Validated implementation specification |
| Lev claim-admission runtime | Absent on audited `main` |
| Local ClaimGate/Lev wiring described in Codex | Repository ledger; not independently verified on Lev GitHub main |
| Active GitHub PR fixing these holes | None found |

The strict conclusion is:

> ClaimGate catches useful structural and numerical inconsistencies, and Lev records a SHA-256 digest association between submitted bytes and an execution/invocation context. Neither repository currently enforces typed cryptographic semantic-witness binding between a claim's meaning and an independent numerical execution receipt. The committed stress suite already demonstrates this through the admitted SMT tautology and `--allow-new-keys` floor-rename bypass.

---

## Cross-Mechanism Integration Verdict

The five requested mechanisms are not five independent features. They form one proposed feedback chain:

\[
\begin{aligned}
&\text{multi-resolution boundary cochain}\xrightarrow{\text{restriction}}
\text{boundary discrepancy}\xrightarrow{\text{local energy}}
E_{\mathrm{stress}}\\
&\xrightarrow{\text{weight update}}
(W',L')\xrightarrow{\text{localized settlement}}
\text{updated survivor neighbourhoods}\\
&\xrightarrow{P_v}
\lambda(v)\xrightarrow{\Phi_{v,\lambda(v)}}
\text{engine/instrument outcomes}\xrightarrow{\beta_{\mathrm{sem}}}
\text{typed semantic witness}\\
&\xrightarrow{\text{ClaimGate}}
\text{admission, hold, or counterexample}\xrightarrow{\text{Ratchet}}
\text{plural whole-manifold frontier and possible renesting}.
\end{aligned}
\]

The repository contains real components at several points in this chain, but it does not presently execute this chain as one closed loop.

| Link | Current repository state | Strict verdict |
|---|---|---|
| Nested-shell cochain restriction | Hard-coded fixed-modulus \(\mathbb Z_5\) triangle-obstruction control; no cross-resolution ring map | Partial |
| Discrepancy to graph stress | Nearby Laplacian/energy calculations, no direct cochain-stress backreaction | Absent as requested |
| Graph stress to localized settlement | Sparse graph libraries and dense \(N=3\) settlement exist separately | Absent for \(N>3\) |
| Local pressure to channel parameters | Global Hartley-scaled GKSL and fixed CPTP banks | Partial, not local/covariant |
| Instrument receipt to semantic ClaimGate | Structural gates, receipt recomputation, floor, and Lev byte digest exist | Partial; semantic binding absent |
| Claim result to whole-manifold Ratchet renesting | Specifications and proposal surfaces exist | Not wired end to end |

### What the fresh three-node replay establishes

The fresh PR #3 replay is not a toy in the sense of being inert prose: it performs dense joint-state evolution, exact partial traces, finite schedule competition, information/thermodynamic checks, and whole-state settlement on its declared \(N=3\) carrier. It passed its own 12 tests and 26 receipt checks.

It does **not** establish the more advanced architecture requested here because it does not:

- vary coefficient rings across nested shells;
- derive local graph stress from cochain mismatch;
- scale beyond three nodes through localized message passing;
- turn that pressure into restriction-covariant channel families;
- bind the mathematical meaning of its output claims to an independent immutable witness;
- feed a rejected or admitted witness back into a renesting comparison of whole diagrams.

The correct status is therefore **real bounded calibration of a dense three-node partial manifold**, not **complete whole-manifold implementation**.

## Minimum Executable Closure Contract

The following is the smallest serious next implementation that would connect the five mechanisms without claiming more than it proves.

### Gate M1 — Multi-resolution cochain transport

Implement a finite diagram of coefficient modules or rings with explicitly valid maps. For the canonical unital reduction

\[
q_{AB}:\mathbb Z_{n_A}\to\mathbb Z_{n_B},
\qquad [x]_{n_A}\mapsto[x]_{n_B},
\]

the direction and divisibility condition \(n_B\mid n_A\) are sufficient and load-bearing. The implementation must reject maps in the opposite direction or between incompatible moduli unless a different, explicitly typed morphism is supplied.

Required tests:

1. identity: \(\Pi_{AA}=\mathrm{id}\);
2. composition: \(\Pi_{BC}\circ\Pi_{AB}=\Pi_{AC}\);
3. additive preservation;
4. multiplicative preservation when the declared morphisms are ring maps;
5. coboundary naturality: \(\Pi_{AB}(\delta c)=\delta(\Pi_{AB}c)\);
6. gauge-class invariance;
7. an explicit non-divisor or otherwise invalid-map negative control;
8. a changed-resolution case where the result cannot be reproduced by the present hard-coded fixed-modulus \(\mathbb Z_5\) triangle control.

If the physics only needs additive phase transport, the object should be honestly typed as a group/module homomorphism rather than mislabeled as a ring homomorphism.

### Gate M2 — Stress backreaction

Define a common cut modulus \(n_{uv}\) satisfying \(n_{uv}\mid n_u\) and \(n_{uv}\mid n_v\). A typed cross-shell discrepancy is

\[
d_{uv}
=(q_{u\to uv})_\#r_{u,uv}c_u
-(q_{v\to uv})_\#r_{v,uv}c_v
\in C^1(U_{uv};\mathbb Z_{n_{uv}}).
\]

Use the representative-independent cyclic norm

\[
\lVert[a]_{n_{uv}}\rVert_{\mathrm{cyc}}
=\min_{k\in\mathbb Z}|a+kn_{uv}|
\]

to define edge-local stress

\[
s_{uv}
=\sum_{e\in U_{uv}^{(1)}}
\lVert d_{uv}(e)\rVert_{\mathrm{cyc}}^2,
\qquad s_{uv}=s_{vu}\ge0.
\]

A positivity-preserving candidate update is

\[
w'_{uv}=w_{uv}\exp(\eta\alpha s_{uv}),
\qquad
\alpha\ge0,
\qquad
\eta\in\{-1,+1\},
\]

followed by \(L'=D(W')-W'\). The sign is not a cosmetic choice: \(\eta=+1\) strengthens a stressed cut, while \(\eta=-1\) weakens it. Both must remain candidates until common whole-settlement probes establish which interpretation better satisfies the declared demands. Using edge-local \(s_{uv}\) preserves defect localization; a node-aggregate bridge \(B_{uv}(E_u,E_v)\) would need separate symmetry and localization proofs.

Required tests:

1. zero mismatch gives zero update;
2. an injected boundary defect localizes stress at the correct vertices/edges;
3. \(\alpha=0\) returns the base graph bit-for-bit;
4. vertex relabeling commutes with the update;
5. \(W'=W'^\top\), \(w'_{uv}\ge0\), \(L'\mathbf1=0\), and \(L'\succeq0\);
6. deleting backreaction changes a declared settlement result;
7. permuting stress among edges/cuts degrades or changes the expected result.

### Gate M3 — Localized settlement

Start with an \(N=4\) pairwise tree, where exact sum-product settlement can be compared with a dense oracle. With node potentials \(\psi_u(x_u)\), edge potentials \(\psi_{uv}(x_u,x_v)\), and every original factor assigned exactly once, the standard message is

\[
m_{u\to v}(x_v)
=\sum_{x_u}
\psi_u(x_u)\psi_{uv}(x_u,x_v)
\prod_{w\in N(u)\setminus\{v\}}
m_{w\to u}(x_u),
\]

and, where topological information is required, an attached compressed cochain class \([c(K_{uv})]\). A junction-tree generalization is allowed only after declaring bags, separators, the running-intersection property, and a one-to-one factor-to-bag assignment that prevents double counting.

Required tests:

1. exact agreement with dense settlement on an \(N=4\) tree;
2. message-size scaling by separator/boundary size rather than total Hilbert dimension;
3. deterministic update-order invariance on the tree;
4. a cut-edge contradiction produces an empty global section or zero declared amplitude;
5. an intentionally insufficient boundary statistic fails against the dense oracle;
6. loopy graphs remain `HOLD` unless a convergence/approximation claim and error bound are separately earned.

### Gate M4 — Pressure-indexed covariant channels

Define the pressure type, parameter domain, and parameter restriction maps before connecting them to the existing channel banks. Then test

\[
\sum_aK_{v,a}(\lambda)^\dagger K_{v,a}(\lambda)=I
\quad\text{and}\quad
C_{AB}\Phi_{A,\lambda_A}=\Phi_{B,r_{AB}(\lambda_A)}C_{AB}
\]

over every admitted discrete parameter or a justified covering grid plus analytic bounds.

Required tests:

1. Choi positivity and trace preservation at all discrete parameters or all grid boundaries/critical points;
2. Kraus completeness independently of sampled input states;
3. zero-pressure/base-channel behavior;
4. maximal-pressure and discontinuity controls;
5. restriction naturality at every declared cut;
6. pressure-label permutation control;
7. deletion witness for pressure modulation;
8. adaptive choices represented by CP trace-nonincreasing instrument branches whose sum is CPTP, with selection driven by the actual outcome and the outcome record retained.

### Gate M5 — Claim semantics and immutable witness binding

Add a canonical admission envelope containing full digests, not prefixes, and a typed semantic map

\[
\beta_{\mathrm{sem}}:\mathrm{ClaimSymbol}\to
(\mathrm{artifactDigest},\mathrm{dataSelector},\mathrm{operator},\mathrm{units},\mathrm{transform},\mathrm{assertion}).
\]

The verifier must resolve content-addressed bytes and independently recompute the declared assertion. A canonical, domain-separated, length-delimited commitment should bind claim schema/canonicalization version, claim, contract, subject, execution/invocation identities, policy, verifier, source-artifact manifest, numerical receipt, semantic map, and verifier result. A protected signer/attestation or append-only trust root is additionally required; hashing alone does not establish authenticity or independence.

Required tests:

1. rename or alias an existing floor key and verify rejection unless an authenticated schema migration declares the equivalence; a genuinely new canonical key must remain possible through that migration path;
2. replace a mechanism witness by a tautology and verify rejection when the tautology is offered as evidence for the stronger mechanism claim;
3. mutate a numerical receipt byte and verify digest failure;
4. reuse a valid receipt where claim, context, contract, or freshness obligations differ and verify rejection, while preserving exact provenance-bound re-offer when those identities remain valid;
5. change units or symbol mapping without a verified equivalence/conversion and verify semantic failure;
6. change verifier command/policy and verify digest failure;
7. require an independent or protected trust root for policy and verifier material;
8. ensure a held claim cannot be promoted by exit zero, pane text, or model-authored status.

## Ratchet Disposition of the Five Mechanisms

The Ratchet should not choose one scalar winner across these mechanisms. It should preserve a plural frontier with typed obligations:

\[
F_{t+1}=\operatorname{ND}_{\preceq_{D_t}}
\left(
\operatorname{settle}(F_t\cup P_t)
\right),
\]

where \(P_t\) contains proposed implementations and \(D_t\) contains the currently declared demands. Incomparability is a retained result, not a solver failure.

For this audit, the frontier is:

| Candidate surface | Retain? | Why |
|---|---:|---|
| Hard-coded fixed-modulus \(\mathbb Z_5\) triangle-obstruction control | Yes | It is executable and supplies the base fixed-resolution control. |
| Multi-resolution coefficient diagram | `PARK_REOFFER` | Formal typing and executable laws are absent. |
| Existing Laplacian/energy code | Yes | Useful control and substrate, but not claimed as backreaction. |
| Cochain-stress metric update | `PARK_REOFFER` | Direct bridge and physicality controls are absent. |
| Dense \(N=3\) settlement | Yes | Freshly executable oracle/calibration. |
| Localized \(N>3\) settlement | `PARK_REOFFER` | No message schema or dense-oracle comparison. |
| Global Hartley-scaled GKSL loop | Yes | Real executable partial coupling. |
| Local covariant CPTP field | `PARK_REOFFER` | Local pressure map and naturality absent. |
| Existing ClaimGate/floor and Lev `lev.done` | Yes | Useful enforcement components with known ceilings. |
| Semantic cryptographic witness binding | `PARK_REOFFER` | Explicit red-team counterexamples remain live. |

This disposition preserves working code as defaults while preventing it from being renamed as completion of stronger mechanisms. A later implementation can beat a default through common probes; nothing here is declared absolutely minimal or final.

## Direct Answers for Gemini

1. **Multi-resolution \(\mathbb Z_n\) cochain projections:** no executable cross-resolution system was found. A hard-coded fixed-modulus \(\mathbb Z_5\) triangle-obstruction control exists. The canonical reduction \(\mathbb Z_{n_A}\to\mathbb Z_{n_B}\) is mathematically valid when its direction is correct and \(n_B\mid n_A\); those laws are not yet represented or tested in the repository.
2. **Discrete graph-stress backreaction:** no direct cochain-discrepancy-to-\(W/L\) update was found. Related Laplacian and energy tools exist without the requested feedback law.
3. **Localized \(N>3\) message passing:** no whole-manifold Markov-blanket settlement was found. Sparse graph primitives exist, while the strongest whole-state settlement is dense and \(N=3\).
4. **Parameterized covariant CPTP fibre channels:** fixed CPTP families and a globally Hartley-scaled GKSL loop run. Local multi-shell pressure modulation and restriction covariance do not.
5. **ClaimGate semantic witness binding:** structural gates, numerical recomputation, audit pins, floor chaining, and Lev byte digests exist. Full typed cryptographic binding from claim meaning to independent immutable numerical evidence does not; committed counterexamples demonstrate the gap.

## Final Claim Ceiling

This audit establishes repository state, mathematical typing constraints, a fresh replay of PR #3's declared three-node checks, and concrete falsifying tests for the five proposed seams. It does not establish that the five seams have been implemented, that the full entropic-geometric constraint manifold runs as one distributed object, or that downstream physical claims follow from these software components.

All source excerpts reproduced in this document are complete functions, fixtures, or contiguous ledger blocks for the point being audited; no ellipsis placeholders were inserted into quoted code. Repository paths, branch heads, blob identifiers, runtime versions, tolerances, and conflicts are retained so Gemini can distinguish source fact from proposal.
