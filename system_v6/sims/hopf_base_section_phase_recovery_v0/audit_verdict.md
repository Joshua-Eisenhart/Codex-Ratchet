# Fresh Independent Audit Verdict: hopf_base_section_phase_recovery_v0

Bottom line: `GENUINE-WITH-CAVEATS` at `scratch_diagnostic` ceiling only. The section-phase claim is mathematically real under a fresh independent pullback/lift recomputation, but the builder packet's own north-section "computed" rows are partially definitional: they set `gamma` from the enclosed-area prediction and compare it back to that same formula. Do not cite this as formal admission, a global section theorem, bridge/axis/physics evidence, or a self-falsifying recovery proof.

Accepted status vocabulary: the packet `exists` on disk and its envelope passes the read-only three-engine validator; it is not `canonical by process`. The sim directory is currently untracked in git, so future citations must either cite this exact workspace state as an uncommitted scratch packet or wait for a committed receipt.

## Independent Recompute

Pinned loop audited: the north-section loop at `eta=pi/6`, so `theta=pi/3`, `beta:0 -> 2*pi`.

Declared section:

```text
s_N(theta,beta) = (cos(theta/2), exp(i beta) sin(theta/2))
```

Fresh scratch SymPy recomputation from the actual section derivative:

```text
A_beta = -i s_N^dagger d_beta s_N = sin(theta/2)^2
horizontal gamma_prime = -A_beta
gamma_integrated = -2*pi*sin(theta/2)^2 = -pi*(1-cos(theta))
theta=pi/3 recovered = -pi/2
theta=pi/3 prediction = -pi/2
mismatch_gap = 0
```

So the recovered U(1) phase matches the enclosed-area/Hopf holonomy prediction when recomputed by genuine lifting through the declared section. A mismatch would have looked like nonzero `gamma_integrated - (-pi*(1-cos(theta)))`; at `theta=pi/3`, the wrong-sign comparison gives a concrete gap of `-pi`, so the comparison is falsifiable in the independent recompute.

Builder caveat: in the packet source, `exact_rows()` computes `area = 2*pi*(1-cos(theta))`, then `gamma = -area/2`, and records both `enclosed_area_prediction` and `computed_recovered_phase` from that same value. The JAX endpoint row also builds `lifted_end = exp(i*gamma)*section_end` and compares it to `exp(i*gamma)`. Those rows are consistency rows, not an independent lift recovery. The SMT rows bind hard-coded scaled integers; the solver flips are real SAT/UNSAT checks, but they do not bind to a section-derived gamma expression.

## Gauge Row

Fresh changed-section recomputation for `s' = exp(i beta) s_N`:

```text
A'_beta = 3/2 - cos(theta)/2 = A_beta + 1
gamma'_integrated = pi*(cos(theta)-3)
gamma' - gamma = -2*pi
```

The gauge shift is correct and computed through the actual changed section in this audit. The builder records the same `-2*pi` shift, but records it as string equality rather than deriving it inside the source row. The convention pin is mostly honest and reopenable:

- section choice: named as `north_section`, with `s_prime=exp(i beta)*s_N`;
- base loop direction/count: named as `beta:0->2*pi` for the north-section one-base loop and separated from the repo lifted-cycle convention;
- orientation: named as positive beta orientation and tied to the S2/S9 sign convention.

Caveat: the pin should be cited as convention-pinned, not convention-free.

## Controls

Contractible loop: independently recomputed as forward plus reverse integral at fixed `theta`, phase `0`. The builder records the same value, but as a prefilled control row.

Area-degenerate boundary: independently recomputed `theta=pi` gives lifted real phase `-2*pi` and `exp(i*phase)=1`. This is a U(1)-identity boundary row, not a new nontrivial holonomy value.

Wrong-gauge / wrong-sign: the packet's z3, cvc5, and Julia Z3 rows do produce `unsat` for the real violation assertion and `sat` for wrong-sign/wrong-gauge flips. They flow through solver computation, but over hard-coded scaled units. They are useful as guardrails, not as proof that the section derivative was bound to the solver.

## Anchor Relation

The committed S9 identity standard remains intact: the committed connection's identity is its holonomy spectrum leaf-by-leaf.

Fresh recompute of the lifted-cycle anchor:

```text
h(eta) = -2*pi*cos(2*eta)
eta in [0, pi/12, pi/6, pi/4, pi/3, pi/2]
=> [-2*pi, -sqrt(3)*pi, -pi, 0, pi, 2*pi]
```

The north-section one-base recovered phases are a different pinned quantity:

```text
[0, -pi/2, -pi, -3*pi/2, -2*pi]
```

Consistency is the convention/continuity relation, not equality row-by-row against the S9 lifted-cycle spectrum. No new holonomy value is found.

## Validators And Boundaries

Fresh commands run:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/hopf_base_section_phase_recovery_v0/results/hopf_base_section_phase_recovery_v0_envelope_results.json
=> {"ok": true, "result_json": "system_v6/sims/hopf_base_section_phase_recovery_v0/results/hopf_base_section_phase_recovery_v0_envelope_results.json"}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v6/sims/hopf_base_section_phase_recovery_v0/hopf_base_section_phase_recovery_v0.py
=> checked=1, violation_total=0
```

`scripts/audit_three_engine_source_claims.py --results-dir ...` was also run and reported `blocked_missing_engine_lane` because this is a Julia+JAX packet under a three-engine audit script. That command writes shared maintenance outputs, so those accidental side effects were restored immediately and are not part of this audit artifact.

The packet-local validator was not rerun in-place because it writes `results/hopf_base_section_phase_recovery_v0_validator_results.json`, violating the requested write boundary. It also has a post-audit idempotence bug: it first accepts an independent `audit_verdict.md` marker, then hard-fails if `audit_verdict.md` exists. After this audit file exists, that validator will fail until the stale hard absence check is repaired.

Current envelope fields support the stated ceiling: `schema_version=three_engine_sim_result_v1`, `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, non-empty tool manifests, `engine_contract.mode=julia_canon_plus_jax_diagnostic`, PyTorch omitted with the scoped reason `no graph/network/autograd claim path`, and no bridge/axis/physics consumers.

## Named Caveats

- C1 `definitional_builder_rows`: the builder's primary north-section rows are formula-consistency rows, not independent section-lift recovery rows.
- C2 `hardcoded_smt_units`: the SMT flips are useful, but the scaled phase units are constants rather than expressions bound to the section derivative.
- C3 `validator_post_audit_drift`: the packet-local validator is not post-audit idempotent after `audit_verdict.md` exists.
- C4 `untracked_packet_boundary`: the whole packet directory is untracked in the current git status.

## Future Citation Rule

Future work may cite this only as: "independently audited scratch diagnostic: the declared north-section pullback gives the expected U(1) phase and gauge shift under explicit convention pins; no new S9 holonomy-spectrum value; builder rows have definitional/falsifiability caveats." Any stronger citation must first repair the builder to compute `A_beta` from `s_N`, bind the SMT rows to that derived expression, make the packet-local validator post-audit idempotent, and commit the packet or cite a committed successor receipt.
