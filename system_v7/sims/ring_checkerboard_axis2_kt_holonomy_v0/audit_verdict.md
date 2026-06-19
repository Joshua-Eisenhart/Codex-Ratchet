# audit_verdict — ring_checkerboard_axis2_kt_holonomy_v0

```yaml
classification: scratch_diagnostic
promotion_allowed: false
formal_admission_allowed: false
does_not_self_upgrade: true
ladder_reached: passes local rerun   # 4 legs run + agree this session; box viii (FLEET) OPEN
box_viii: OPEN -- needs a MULTI-MODEL FLEET audit (single fresh pipeline is insufficient)
builder: narrow builder (Claude); this is the BUILDER's self-assessment, NOT a fleet closure
```

## What this sim is

The GENUINE Axis-2 discriminator that `ring_checkerboard_euler_conversion_axis2_frame_v0` failed to
earn. That sim's Axis-2 `K_t` test was DEMOTED (box-viii fleet, 2026-06-15) as **by-construction**:
`K_direct = K_static = 0` via `1j * (...) @ np.zeros((2,2))` (identically zero), and
`K_dynamic = ‖V_t† G V_t‖ = ‖G‖` by unitary norm-invariance — none of which could come out
otherwise. Its own `audit_verdict.md` named the fix: "a `K_t` **loop holonomy** — `∮K_t` nonzero in
a moving/Eulerian frame, zero in a comoving/Lagrangian frame — would be the real test." This sim
builds exactly that.

**Object:** the holonomy of the Axis-2 connection `K_t = i V_t† dV_t` around a CLOSED loop of frames
`V(s)`, `s∈[0,1]`, `V(1)=V(0)`. Holonomy `U_loop = P ∏_s exp(-i K(s) ds)`, computed as the
gauge-covariant link product `∏_s ⟨n(s)|n(s+1)⟩/|⟨n(s)|n(s+1)⟩|`. The frame is the sim's own
spin-1/2 Bloch frame `|n(θ,φ)⟩` carried around a loop on the shell/fiber `(θ,φ)` sphere.

## Why it is load-bearing (NOT by-construction)

The holonomy is a **measurement that could have come out flat**. The decisive value-coupled control:
a **FLAT / pure-gauge connection** (`θ=0`, the frame never tilts off the pole, `|n⟩=e^{iφ}|up⟩`)
wound around the **SAME φ-loop, same topology, same winding** gives `|U-I| ~ 1e-13` (the identity),
while the **CURVED** frame (`θ=π/3`, enclosing Berry curvature) gives `|U-I| ~ 1.414`. The nontrivial
holonomy is forced by the **enclosed curvature**, not the loop. A flat connection — the outcome that
does NOT occur for the curved frame — is what makes this a real discriminator.

## Results (this session, all four legs + agreement; `agreement_ok = true`, 0 failures)

| measurement | result | meaning |
|---|---|---|
| DYNAMIC / Eulerian loop (`θ_cap=π/3`) | `|U-I| = 1.4142`, phase `+1.5708` | nontrivial holonomy |
| holonomy phase vs enclosed flux `Ω/2 = +1.5708` | `flux_match_err = 2.31e-7` | equals enclosed curvature flux (Stokes) |
| DIRECT / Lagrangian / comoving (`V=I`) | `|U-I| = 0.0` | trivial (telescopes to `V(1)†V(0)=I`) |
| TRIVIAL loop (zero enclosed area) | `|U-I| = 0.0` | trivial |
| **FLAT connection, SAME loop** | `|U-I| ~ 1e-13` | **anti-by-construction control: curvature is load-bearing** |
| SHRINK loop (`θ_cap: π/3→π/200`) | `|U-I|: 1.41→0.0004`, monotone | holonomy → I continuously, ~ enclosed area |
| KNOB SWEEP holonomy vs `Ω/2` | err `~2e-7` across the whole range | phase tracks enclosed flux continuously, not a fixed number |
| OPEN path (erase the loop) | phase moves under a boundary gauge transform | not gauge-invariant |
| CLOSED loop under the same gauge | phase unchanged | gauge-invariant |

### Four-engine agreement (distinct float fingerprints — not one echoed file)

`dynamic_holonomy_abs_minus_I`: exact `1.4142133990211496`, julia `1.41421339902081`,
jax `1.4142133990208436`, pytorch `1.414213399021136`. Each leg uses a distinct float route
(numpy complex division / julia `arg`+`exp` link / jax vectorized `prod` / torch complex `prod`);
they agree on the physics to a discretization tolerance while carrying independent roundoff.
`flat_connection_holonomy_abs_minus_I`: `6.5e-13 / 1.3e-13 / 1.4e-14 / 6.2e-13` (all machine-zero,
distinct).

## What this sim actually earns

A four-engine cross-language numeric witness that the Axis-2 `K_t` loop-holonomy is
**curvature-coupled**: nontrivial around a loop enclosing Berry curvature (phase = enclosed flux),
trivial for the comoving/Lagrangian, trivial (zero-area), and **flat (pure-gauge, same loop)** frames,
shrinking continuously to identity, with an open path that is not gauge-invariant. The flat-connection
control is the load-bearing discriminator (it could have, but did not, reproduce the nontrivial
holonomy from the loop alone). This is the real Axis-2 frame discriminator the euler sim lacked.

It does NOT earn: `M(C)` admission, Axis0 closure, a QIT engine, a smooth manifold, or any physics.
The half-monopole Berry curvature is the standard spin-1/2 curvature, not a derived object. The
`Ω/2` value is the textbook spin-1/2 geometric phase; the sim does not claim to derive it, only to
measure that the Axis-2 holonomy is curvature-coupled and that the comoving/flat frames are flat.

## To move up / close box viii

1. **Multi-model FLEET box-viii audit** (codex2 + grok + gemini via `wizard_child_matrix`). This
   `audit_verdict.md` is the BUILDER's self-assessment (`does_not_self_upgrade: true`) — box viii is
   NOT closed. The 2026-06-15 build was single-model (Claude); ADVANCED, not closed.
2. Lift the rank-1 (Berry / U(1)) frame to a genuine **non-abelian** Wilczek-Zee `K_t` (degenerate
   subspace, `SU(2)` holonomy) so the path-ordering is non-commutative, not just a U(1) phase.
3. Couple the holonomy to the ring-checkerboard support quotient (the loop currently lives on the
   abstract Bloch sphere, not yet pinned to the finite `(η_k, χ_j)` lattice cells).
```
