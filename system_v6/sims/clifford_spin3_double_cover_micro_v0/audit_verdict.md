# Audit Verdict - clifford_spin3_double_cover_micro_v0

Bottom line: **GENUINE-WITH-CAVEATS**. This is an exact finite witness of the standard Spin(3) -> SO(3) double cover on the pinned Cl(3,0) carrier, not a discovery claim and not an O6/engine/coupling result.

## Verdict

- Repo vocabulary: `GENUINE-WITH-CAVEATS`.
- Evidence ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, `claim_ceiling=tool_function_micro_only`.
- Citation-safe claim: the packet witnesses, with exact rational/surd rows and SMT-bound finite flags, that `R(theta)` and `R(theta+2pi)` differ by rotor sign while inducing the same computed SO(3) vector sandwich action, with exact `2pi=-1` and exact `4pi=1` closure.

## Checked

- Build card scope matched: fixed finite `Cl(3,0)`, pinned angles, `R=cos(theta/2)-sin(theta/2)B`, double-cover rows, single-cover control, non-rotor controls, SMT sign/control bindings, envelope, validators, and O6 fence.
- Fresh reruns were done in `/tmp/codex_audit_clifford_spin3` to respect the repo write boundary. Julia, JAX, envelope, packet-local validator, and generic three-engine validator all exited 0.
- Independent no-write recompute from the repo source gave:
  - `action_pi_over_2 = [[0,-1,0],[1,0,0],[0,0,1]]`
  - `action_5pi_over_2 = [[0,-1,0],[1,0,0],[0,0,1]]`
  - `actions_equal=true`
  - `rotor_sign_flip=true`
  - `theta_2pi_is_minus_one=true`
  - `theta_4pi_is_one=true`
  - non-unit even candidate `1 + (1/2)e12` rejected by rotor predicate with reverse product `5/4`.

## Adjudication

- Double-cover rows: pass. Julia and JAX independently compute identical SO(3) action matrices for `theta=pi/2` and `theta+2pi=5pi/2`, while the sparse rotors are exact negatives of each other. The `2pi` and `4pi` boundary rows are exact.
- Definitional-vs-discovered lens: pass with the right ceiling. The sign flip is a theorem of the Clifford rotor construction; this packet's value is the exact finite witness at pinned angles, not a discovered new structure.
- Single-cover control: pass. The SO(3) matrix representation cannot distinguish `theta` from `theta+2pi` on the checked row, while the rotor coefficients remain distinct.
- Non-rotor predicate control: pass. The non-unit even multivector fails unit reverse product, and the odd unit element fails even-grade Spin(3) membership.
- Fence: pass. O6 appears only as background context: `o6_720_coupling_candidate=background_only_not_claimed`; engine/coupling, lego promotion, and physics promotion are all `not_claimed`.
- Exactness and proofs: pass. Claim path uses exact rationals/surds, Julia `Rad2`, SymPy exact expressions, Julia Z3, Python z3, and cvc5. SMT bindings report positive violation `unsat` and erased-sign flip control `sat`.

## Caveats

- G1 - Two scoped engines, not all-three: PyTorch is honestly omitted because no graph/network/autograd claim is scoped. Do not cite this as an all-three engine result.
- G2 - Standard theorem witness: cite as an exact finite witness of known Spin(3) double-cover mechanics, not as a discovered double-cover phenomenon.
- G3 - Micro-only relevance: O6 relevance is context only. This packet does not establish an O6 720-coupling, engine coupling, bridge, axis, or physics claim.
- G4 - Validator placement: the packet-local validator was rerun in a temp copy because the live repo audit file is auditor-owned and the packet validator intentionally treats any `audit_verdict.md` as a builder-boundary failure.

## Future-Citation Rule

Allowed citation:

> `clifford_spin3_double_cover_micro_v0` is a `scratch_diagnostic` exact finite Cl(3,0) witness of the standard Spin(3) double-cover row: `R(theta+2pi)=-R(theta)` with identical computed SO(3) sandwich action and exact `4pi` closure.

Forbidden citation:

> This packet discovers a new double-cover mechanism, proves an O6 720-coupling, supplies an engine/coupling result, or counts as an all-three-engine envelope.
