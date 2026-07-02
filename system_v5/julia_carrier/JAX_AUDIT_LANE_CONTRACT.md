# JAX Audit-Lane Contract (for the Codex/JAX track)

Status: 2026-06-01. Supersedes "PyTorch-primary / torch-native spinor" strategy. Pairs with the Julia truth
lane in `PLAN.md` (`system_v5/julia_carrier/PLAN.md`). Hand this to codex as the JAX-track contract.

---

## The two lanes (do not blur them)

- **Julia = geometry/QIT TRUTH lane.** Full spinors (Grassmann/CliffordAlgebras), Hopf maps, Weyl/chirality,
  branch/prune futures, attractor basins, interval/constraint proofs. Exact **by construction** (types close;
  DAEs hold the constraints structurally). See `PLAN.md`.
- **JAX = scale/stress/AUDIT lane (this contract).** Huge batched futures, constrained approximations, drift
  tests, counterexample search, invariant audits **against Julia**. JAX corrects constraints **after** each step
  (projection/penalty), so it is the *approximation*, never the spinor truth engine.

**JAX's job is NOT** to be a native spinor engine and NOT to be a PyTorch mirror. It is the batched numerical
stress-tester whose results are audited against the Julia oracle.

---

## JAX toolset (use these, not bare `jax.numpy`)

- `jax.jit`, `jax.vmap`, `lax.scan`, `lax.while_loop` — fast batched futures + traceable pruning loops.
- `jax.custom_jvp` / `jax.custom_vjp` — tangent-space-projected gradients for constrained spinor primitives.
- `diffrax` — ODE/trajectory evolution of the spinor field.
- `optax` or `jaxopt` — constrained search / fitness optimization over survivor futures.
- `equinox` — structured JAX state for fields / shells / branch metadata.
- `lineax` — constrained linear solves when needed.
- `ott-jax` — compare survivor *distributions* / basin transport (NOT as primitive QIT — that's Julia's job).
- `chex` + explicit asserts — shape / dtype / finite / norm / invariant checks inside every test.
- Receipts: JSON for the audit receipt; HDF5/Zarr/NPZ for state snapshots if needed.

---

## Constraint enforcement (the 5 rules — binding for the JAX lane)

1. **Parameterize valid states by construction first.** Prefer variables valid by construction: unit-spinor
   coordinates, rotor parameters, normalized quaternions, chirality-separated blocks. Do not represent a spinor
   as a free `ℂ⁴` and hope.
2. **Project/retract after EVERY JAX step.** Every update ends with `normalize` / `project_even_subalgebra` /
   `project_chirality` / the relevant Hopf/shell retraction — inside `lax.while_loop` or a `custom_vjp` so it
   stays JIT-compatible.
3. **Prune invalid futures, do NOT average them.** Keep a **survivor mask** + a **prune-reason table**. An
   invalid branch must never contaminate entropy, basin statistics, or any aggregate. (Julia does this with
   callbacks/branch-prune/interval rejection; JAX with the mask.)
4. **Compare INVARIANTS, not raw states.** The cross-audit metric set: spinor norm, Hopf invariant / linking
   number, chirality, log-negativity / coherent information, winding number, basin label, prune reason,
   survivor distribution. Never diff raw state vectors.
5. **Divergence rule (how to read a mismatch):**
   - Julia preserves algebra/topology, JAX drifts → **JAX constraint enforcement is wrong** (projection leaking).
   - Both drift → **the model/discretization is wrong** (RK order too low for the Hopf curvature).
   - JAX finds a state Julia rejected → **Julia's constraint/prune gate needs inspection** (counterexample).

---

## The deliverable: a JAX↔Julia constraint-audit harness (NOT another PyTorch mirror)

Run the **same finite future-branch experiment** on both lanes and compare:
- **Julia** = full-spinor branch/prune oracle (EnsembleProblem + `terminate!` callbacks + Attractors basins).
- **JAX** = batched constrained stress-runner (`vmap` over N futures + retraction + survivor mask).
- **Receipt** (JSON) compares, per the §4 invariants: invariant survival, prune basins/reasons, survivor
  distribution. A pass = the two lanes agree on the **integer** invariants (linking/winding/chirality) and on
  which basins survive; a fail routes to the §5 divergence rule.

Concrete first experiment (matches Julia Phase 2): N perturbed unit spinors on S³ → geometric flow → prune on
`|ψ|²≠1` / chirality / fitness → cluster survivors into basins. Julia is exact; JAX is the batched audit; the
receipt compares basin labels + Hopf linking + survivor fractions.

---

## Supersession note (stale docs)

The repo contract still carries **PyTorch-primary / "torch-native spinor"** language. That strategy is
**superseded**: the new contract is **Julia-native Clifford/full-spinor TRUTH lane + JAX constrained numerical
AUDIT lane**. The PyTorch sims are sidelined (not deleted), their work redone in Julia. Docs that still say
"torch-native spinor / PyTorch-primary" need updating to this two-lane framing — owner/codex to update the
authority contract (`AGENTS.md`); this file + `PLAN.md` are the new strategy reference until then.
