# Packet 107 Canonical Rerun And Kill Audit

Status: mechanically green; both scientific additions rejected.

## Package Lock

- source: `/Users/joshuaeisenhart/Desktop/107.zip`
- package SHA-256:
  `85144e5bf6077e1a46d7554372f7438f49604f5ea5f035b71e4268b737873cd5`
- ZIP integrity: pass
- members: 469
- delta from packet 102: 462 byte-identical, 3 changed, 4 added, 0 removed

The changed files are `CHANGELOG_HARDENING.md`, `MODEL_LAYER_LEDGER.md`, and
`run_all.py`. The four additions are the UP-135 redshift-fork source/result and
the UP-136 physics-loop-back source/result. The 16-slot chart, four-operator
tables, and all prior engine sources are byte-identical to packet 102.

## Canonical Rerun

The extracted packet was run outside Desktop with:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 run_all.py
```

The harness returned `141 pass / 0 fail / 0 skip`. The retained report is
`run_all_report_canonical_sim_stack.json`, SHA-256
`30d85854c7f12d9109b0993353b10601e9cc8b41c86bc0536e216bd01429bbad`.

This proves that packet 107 is executable in the canonical environment. It
does not independently validate the two new interpretation gates: the harness
only checks their exit codes and self-authored `PASS` strings.

## UP-135: Redshift Fork

The internal arithmetic is reproducible. At the packet's fixed cosmology,
`c H(z)/(2 pi)` rises by about `2.97` from `z=0` to `z=2`; the constant
candidate does not. That makes a useful discriminator, not a forced or
exhaustive fork.

The claimed observational selection is invalid:

1. [Milgrom 2017](https://arxiv.org/abs/1703.06110) says the six
   [Genzel et al. 2017](https://arxiv.org/abs/1703.04310) galaxies strongly
   constrain a rapid rise, discussing roughly `4 a0` at `z about 2` and the
   example `(1+z)^(3/2)`. It also says smaller values are not excluded and the
   data do not reach the asymptotic speed needed for a direct MOND MASR test.
   Packet 107 replaces that qualified argument with its own `ratio > 2.0`
   Boolean and then calls the constant branch selected.
2. [MUSE-DARK III 2026](https://arxiv.org/abs/2604.22613) fits 79 galaxies over
   `0.33 < z < 1.44` and reports `a0(z about 1) = 2.38 +0.12/-0.10 x 10^-10
   m/s^2` at 95% credibility, plus a positive linear coefficient
   `1.59 +0.10/-0.10 x 10^-10 m/s^2` per unit redshift. The paper reports a
   statistically significant increase and says it is faster than `H(z)`.
3. At `z=1`, the packet candidates are `1.906e-10` for total `H`, `1.082e-10`
   for frozen `H0`, and `0.906e-10` for the de Sitter rate. Total `H` is the
   closest of those three but is not admitted: this is a fixed-point comparison,
   not a refit, and the paper itself reports faster evolution.

Verdict: current primary-source evidence contradicts the packet's
constant/de-Sitter selection. It does not establish the packet's total-`H`
candidate either.

## UP-136: Berry `2 pi`

The flat-Lambda-CDM limit `H(z)/H_dS -> 1` as `z -> -1` is correct imported
cosmology. It does not identify three Ratchet layers as one object.

The purported engine holonomy is not gauge-invariant. At the chosen pole,

```text
psi(phi) = (exp(i phi), 0)
```

is one constant projective ray. The packet integrates the connection in one
section and gets `-2 pi`. A gauge with `psi=(1,0)` gives `0`; winding two gives
`-4 pi`. Once the Pancharatnam endpoint phase is included, the gauge-invariant
geometric phase is `0 mod 2 pi` for all three gauges. The packet's half-loop
control also has zero physical geometric phase: its `-pi` connection integral
is canceled by the endpoint phase `+pi`.

This is the distinction developed by [Berry 1984](https://doi.org/10.1098/rspa.1984.0023)
and the open-path treatment of [Samuel and Bhandari 1988](https://doi.org/10.1103/PhysRevLett.60.2339).

Verdict: the reported `2 pi` is the winding of a chosen section over a
projectively constant path. It cannot ground the Unruh/KMS period, Axis0, or
four substages.

## Independent Audit Gates

`run_audit.sh` hashes the packet and all four additions, byte-binds every
extracted addition to the corresponding ZIP member, runs the observational and
geometric-phase audit twice, validates both outputs, and requires byte identity.
The key-closed validator independently recomputes the live ZIP and extraction;
a self-consistent old JSON result is insufficient. Its fail-closed mutation
battery rejects missing hashes/checks, empty schedule impact, non-finite phases,
altered predictions, unbound members, missing source records, admitted
candidates, fake aggregate green, missing controls, promoted classification,
negated verdicts, extra admission claims, changed rationale, integer/Boolean
coercion, float count coercion, and duplicate JSON keys.

- checks: 17/17
- validator mutation controls: 19/19 rejected
- deterministic result SHA-256:
  `068b7f3dc089c734eb8d827b125f597debb1d64a968f8060bbbd85ba7ea333c2`
- UP-135 scientific claim: rejected
- UP-136 scientific claim: rejected
- 64-schedule movement: false

Claude Fable 5 at High effort independently identified the tuned UP-135
threshold, non-exhaustive observational inference, current-data reversal, and
gauge-dependent UP-136 connection integral. The advisory ran for `171.742 s`,
cost `$1.689171`, and remains non-gating. Its output and receipt hashes are
recorded in `receipt.json`.

## Claim Ceiling

`packet_rerun_and_kill_audit_only`.

Packet 107 earns a real `141/0/0` process receipt and two reproducible pieces
of internal arithmetic. It does not earn UP-135, UP-136, Axis0, a
four-substage derivation, the 64-microstep schedule, perception, objects, MMMs,
ontologies, mesh authority, or physics admission.
