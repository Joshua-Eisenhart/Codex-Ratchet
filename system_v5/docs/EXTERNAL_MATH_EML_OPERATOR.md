# EXTERNAL MATH — EML Operator (arXiv:2603.21852v2)

Repo-canonical mirror of `~/wiki/concepts/arxiv-2603-21852-eml-operator.md`. Denser. Sim-plan section is repo-only.

## Citation

- Odrzywołek, A. *All elementary functions from a single binary operator.* arXiv:2603.21852v2, 2026-04-04.
- URL: https://arxiv.org/abs/2603.21852

## One-paragraph summary

Odrzywołek defines `eml(x, y) = exp(x) - ln(y)` and claims that the closure of `{eml, 1}` under composition equals the elementary-function repertoire of a scientific calculator (arithmetic, trig, log/exp, algebraic, constants e, pi, i). The result is a continuous-math analogue of NAND/NOR functional completeness. Discovery was by exhaustive small-operator search, not derivation. An empirical section uses depth-bounded `eml`-trees trained by Adam as a symbolic-regression architecture.

## Core object

$$\mathrm{eml}: \mathbb{R} \times \mathbb{R}_{>0} \to \mathbb{R}, \quad \mathrm{eml}(x, y) = e^{x} - \ln(y).$$

Generating set: `G = {eml, 1}`. Expression space: finite binary trees with internal label `eml` and leaves drawn from `G`-composites.

Elementary examples:
- `exp(x) = eml(x, 1)` because `ln(1) = 0`.
- Subtraction, multiplication, division, ln reconstructable as finite `eml`-trees; trig via complex-exp identities (construction details in the paper).

## Claims vs non-claims

Claims: (a) functional completeness of `{eml, 1}` over elementary functions; (b) usability of `eml`-trees as a gradient-trainable symbolic-regression primitive.

Not claimed: depth bounds, numerical conditioning, minimality/uniqueness of `eml`, any invariance group, information-theoretic content, connection to geometry or entropy.

## Tool-capability mapping (Codex Ratchet tool set)

| Tool | Could be load-bearing? | Why |
|---|---|---|
| sympy | **Yes** | Symbolic verification of `eml`-tree identities; simplification; exact depth-by-target tables. |
| z3 / cvc5 | **Yes (conditional)** | Encode `eml`-tree structural equalities under axiomatized exp/ln identities; search for UNSAT of claimed reductions. cvc5's nonlinear-arith theory is the relevant gate. |
| pytorch | **Yes** | Differentiable `eml`-tree training (paper already uses Adam). Natural for depth-vs-precision sweeps. |
| numpy | Baseline | Finite-precision evaluation; conditioning probes. |
| clifford / geomstats / e3nn | No | `eml` has no invariance structure; these tools do not attach. |
| pyg / toponetx / rustworkx / xgi | Weak | Only as tree-graph carriers; not load-bearing for the math itself. |
| gudhi | No | No topological content. |

Load-bearing candidates for sim gates: **sympy** (symbolic closure), **z3/cvc5** (structural UNSAT on false reductions), **pytorch** (expressivity-vs-depth empirics).

## Relation to the 5 self-similar frameworks

- **QIT / Holodeck / IGT / Leviathan:** no connection. Syntactic primitive-basis result; does not touch F01/N01, constraint-admissibility, shell geometry, or strategy dynamics.
- **Scientific Method:** weak connection via expressivity-compression framing. `eml` compresses "many primitives" into one syntactic basis, but not in the information-theoretic / density-matrix sense the project cares about.

## Relation to G-structure tower / constraint-admissibility

`eml` sits outside the G-structure tower — no group acts, no structure is preserved. The project-aligned use is as a **classical_baseline primitive basis** to benchmark structure-adapted primitive bases (Clifford rotor ops, e3nn equivariant ops, TopoNetX gating, PyG message passing) on matched expressivity tasks. Canonical shells should not be built on `eml`.

## Open questions the paper does NOT answer

- Quantitative depth(epsilon, target) bounds.
- Numerical conditioning / finite-precision breakdown region maps.
- Minimality of `{eml, 1}`; existence of alternative single-operator generators.
- Extension to multi-variable calculus / differential operators / forms.
- Any information-theoretic or entropy interpretation.
- Behavior under domain restriction (real-analytic vs algebraic vs transcendental slices).

## Verdict

Narrow but real. Low priority for Codex Ratchet. Useful only as a baseline primitive basis for symbolic-regression sims. Does not unblock any current coupling / shell / admissibility work.

---

## Proposed Sim-Lego Atomization Plan (Phase 3)

Pattern: carrier → structure object → reduction → admissibility → distinguishability probe → chirality → coupling. `eml` has limited structure, so several stages are intentionally stubbed "N/A" rather than invented.

Filename prefix `eml_` — no collisions checked in `system_v4/probes/` on 2026-04-14.

All proposed legos MUST start from `system_v4/probes/SIM_TEMPLATE.py`, set classification field, carry full TOOL_MANIFEST, positive/negative/boundary sections, and at least one load-bearing non-numeric tool.

| # | Proposed filename | Atomization stage | classification | load_bearing tool | Positive test | Negative test | Boundary test |
|---|---|---|---|---|---|---|---|
| 1 | `eml_01_operator_identity_sympy.py` | carrier | classical_baseline | sympy | `eml(x,1)` simplifies symbolically to `exp(x)` | `eml(x,1)` does NOT equal `exp(x)+1` (sympy `simplify` distinguishes) | Domain boundary y->0+ : ln singularity flagged |
| 2 | `eml_02_tree_closure_enumeration.py` | structure object | classical_baseline | sympy | Depth<=3 `eml`-trees over `{1}` reproduce `exp`, `-ln`, `e-1` | Depth<=3 does NOT reach `sin` (must fail) | Depth cutoff reported honestly |
| 3 | `eml_03_reduction_to_target_z3.py` | reduction | classical_baseline | z3 | Encode candidate `eml`-tree = target; z3 returns SAT for claimed reductions | UNSAT for a fabricated false reduction | Nonlinear-arith timeout regime recorded |
| 4 | `eml_04_admissibility_conditioning_numpy.py` | admissibility | classical_baseline | numpy (sympy supportive) | Forward eval of `eml`-tree for `exp` agrees to 1e-10 on x in [-5,5] | Precision loss >1e-3 outside [-20,20] documented | Overflow boundary recorded, not hidden |
| 5 | `eml_05_distinguishability_depth_probe_pytorch.py` | distinguishability probe | classical_baseline | pytorch | Trainable depth-`d` `eml`-tree fits `sin` on [-pi,pi] to RMSE<1e-2 at some d | Depth-1 tree CANNOT fit `sin` (negative control) | RMSE-vs-depth curve reported, no cherry-pick |
| 6 | `eml_06_chirality_xy_asymmetry.py` | chirality | classical_baseline | sympy | `eml(x,y) != eml(y,x)` symbolically (asymmetric-by-construction) | A symmetric variant `exp(x)-ln(x)` lacks two-argument structure | Swap-invariance fails; logged as non-chirality-in-geometry-sense |
| 7 | `eml_07_coupling_vs_clifford_rotor_baseline.py` | coupling | classical_baseline | pytorch (clifford supportive) | Matched-parameter comparison: `eml`-tree vs Cl(3) rotor-op net on a 3D-rotation regression task | `eml` basis underperforms rotor basis on equivariant target (expected) | Parameter-count, depth, training-budget matched and disclosed |
| 8 | `eml_08_canonical_gate_nonequivariance_z3.py` | admissibility (exclusion) | classical_baseline | z3 | z3 UNSAT: no finite `eml`-tree over `{1}` is SO(3)-equivariant in a formalized sense | A Clifford rotor expression IS equivariant (positive control, separate sim) | UNSAT witness extracted and stored |

Notes:

- All 8 are `classical_baseline`. None are `canonical`. `eml` is not an admitted shell primitive; it is only a baseline yardstick.
- No Axis-0 / Phi0 / rho_AB / Xi linkage proposed. That would be an unsupported leap.
- Legos 3 and 8 are the most load-bearing for the project's methodology: they use UNSAT to *exclude* false claims (claimed reductions that aren't, equivariance that cannot exist in this basis). These are the legos worth doing even if the symbolic-regression lane stays cold.
- Legos 5 and 7 are the empirical counterweight; they are useful only if the project decides to benchmark primitive bases against each other.
- Lego 6 is a naming-hygiene exercise: the paper's asymmetry in `(x,y)` is NOT chirality in the geometric sense, and the sim's job is to refuse that conflation.

## Next actions

- Owner review of framings and priorities.
- If approved, Hermes/Codex may author legos 1, 3, 8 first (cheapest and most load-bearing for the exclusion lane). Legos 5, 7 only if the symbolic-regression benchmarking lane is activated.
- Do NOT author before explicit launch authorization per the setup-vs-launch-mode rule.
