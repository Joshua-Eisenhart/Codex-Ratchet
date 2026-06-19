# audit_verdict — ring_checkerboard_euler_conversion_axis2_frame_v0

```yaml
classification: scratch_diagnostic
promotion_allowed: false
formal_admission_allowed: false
does_not_self_upgrade: true
ladder_reached: passes local rerun   # 4 legs run + agree this session; box viii (FLEET) OPEN
box_viii: OPEN -- needs a MULTI-MODEL FLEET audit (single fresh pipeline is insufficient)
```

## 2026-06-15 box-viii fleet audit DEMOTED the headlines (this correction is the point of box viii)

A fresh-context adversarial audit caught that most "load-bearing" headline tests are
**by-construction identities, not discriminators**. Corrected:

### BY-CONSTRUCTION (forced for ALL inputs — NOT discriminators)
| former headline | why it cannot fail |
|---|---|
| Euler `err = 0.0` | `e^{iθ}=cosθ+i sinθ`: `psi_direct` and `psi_ring_board` are algebraically identical for every input. 4-engine "agreement" = 4 languages confirming one identity. |
| Hopf `err = 1.4e-16` | `psi^dag sigma psi` and the double-angle formula are algebraically equal. |
| Axis-2 `K_direct = 0`, `K_static = 0` | formed via `1j * (...) @ np.zeros((2,2))` — identically zero regardless of any state. Hardcoded, decorative. |
| Axis-2 `K_dynamic = 0.7071 = ‖G‖` | `K_dyn = V_t† G V_t`; `‖V_t† G V_t‖ = ‖G‖` for every unitary `V_t` (norm invariance). Value forced by the choice `G=SZ/2`. |
| finite-gradation `b0 = [1,0,-1]` | grid-induced `sign(cos 2η_k)` at `η = 0, π/4, π/2`. |

### GENUINELY LOAD-BEARING (a measurement/ablation that could have come out otherwise)
| discriminator | result | why it is real |
|---|---|---|
| euler-erase ablation | `delta = 1.0` (every engine) | amplitude-only (cos, no `i sin`) reconstruction genuinely fails — a real ablation flip |
| static basis change alters ρ | `rho_tilde != rho`, `K_static = 0` | a real measured difference; separates basis-change from connection (mild) |
| **no-preferred-center translation automorphism** | `256` edges, automorphism holds; pin → `232` | the strongest survivor: a graph computation that fails if the support is not translation-homogeneous |

`check_agreement.py` gates `agreement_ok` on the genuine discriminators + cross-engine agreement of
the genuine STRUCTURE (support/quotient/edge counts + the discriminator bools). The by-construction
identities are reported under `by_construction_identities` / `by_construction_cross_engine` and are
EXCLUDED from the gate. VERIFIED by perturbation (box-viii fleet, 2026-06-15b): perturbing a pure
by-construction value (`K_dynamic_norm 0.7071->0.5`) does NOT flip `agreement_ok`; perturbing a
genuine discriminator (`translation_is_automorphism True->False`) DOES. (The first fleet pass caught
that an earlier demotion still gated the by-construction values via an undisclosed cross-engine
path; that was fixed this session.)

## What this sim actually earns

Four-engine cross-language agreement on a 96-cell finite ring-checkerboard support, with ONE real
structural finding (the support is translation-homogeneous — no preferred center) and two real
ablations (euler-erase; static-frame). It does NOT earn an Axis-2 frame discriminator (the
direct/static/dynamic `K_t` values are by-construction; a `K_t` **loop holonomy** — `∮K_t` nonzero
in a moving/Eulerian frame, zero in a comoving/Lagrangian frame — would be the real test). No
conversion-identity is "load-bearing": Euler/Hopf are chart identities, true by construction.

## Honest gate + ladder status

- `validate_v7_admission.py` overall **`ok = FALSE`** (6 pass / 2 fail): FAIL `math-only` + `name-math-correlation` (vocabulary blacklist on `euler/axis/ring/checkerboard/frame`). PASS ancestry (F01/N01 lineage), integrity, count-tautology-smt, qubit-ladder-depth, three-engine (N/A), and `two-tier-authority`.
- **`two-tier-authority` passes SPURIOUSLY** -- it accepts this `audit_verdict.md` as the committed audit, but this is the BUILDER's self-assessment (`does_not_self_upgrade: true`). **Box viii is NOT closed.** Closure needs the MULTI-MODEL FLEET (codex2 + grok + gemini via `wizard_child_matrix`); the 2026-06-15b pass was method-diverse but single-model (Claude) -- ADVANCED, not closed.
- The Julia binary (v1.12.6) **re-runs live and reproduces** the agreeing numbers (the fleet re-ran all four legs independently; the four engines carry distinct float fingerprints, not one echoed file).

## To move up
1. Replace the decorative Axis-2 legs with a real `K_t` **loop-holonomy** discriminator.
2. Multi-model FLEET box-viii audit (single pipeline insufficient).
3. `N_chi ≥ 8` to lift the equatorial degeneracy behind the phase split / b0 ladder.
4. Pure-math rename (or invert the blacklist gates to allow-lists) for `math-only`/`name-math`.
