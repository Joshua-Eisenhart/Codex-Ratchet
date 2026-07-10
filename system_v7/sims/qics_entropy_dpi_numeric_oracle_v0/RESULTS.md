# Results

Accepted status: `passes local rerun` as a `scratch_diagnostic` only.
Promotion, formal admission, and stage movement remain false.

## Fresh Run

Command:

```sh
/Users/joshuaeisenhart/Codex-Ratchet/system_v7/sims/qics_entropy_dpi_numeric_oracle_v0/run_all.sh
```

Outcome:

- Producer checks: `11/11` passed.
- Independent validator: passed for both result files.
- Malformed numeric self-test: `8/8` fail-closed cases passed.
- Deterministic rerun: byte-for-byte match.
- QICS solves: `9`, all `optimal`.
- Accepted contraction cases: `6`.
- Invalid controls: `6/6` rejected and excluded.

## Aggregate Metrics

| Metric | Value |
|---|---:|
| Maximum QICS vs spectral absolute error | `8.16396894531835e-10` |
| Maximum fixed-input absolute residual | `1.10977171896565e-09` |
| Minimum direct contraction margin | `0.071557723709512` |
| Minimum QICS contraction margin | `0.0715577238213695` |

## Fixed Cases

| Pair | Input spectral | Input QICS | Map | Mapped spectral | Mapped QICS | Direct margin | QICS margin |
|---|---:|---:|---|---:|---:|---:|---:|
| `qubit_complex_a` | `0.221812117769061` | `0.221812117555605` | pinching | `0.0453036192139408` | `0.0453036192138487` | `0.17650849855512` | `0.176508498341756` |
| `qubit_complex_a` | `0.221812117769061` | `0.221812117555605` | depolarizing | `0.0917512059125421` | `0.0917512050961452` | `0.130060911856519` | `0.13006091245946` |
| `qubit_real_b` | `0.372078474530019` | `0.3720784741597` | pinching | `0.26759596951151` | `0.267595969486595` | `0.104482505018509` | `0.104482504673105` |
| `qubit_real_b` | `0.372078474530019` | `0.3720784741597` | depolarizing | `0.153129719818897` | `0.153129719581904` | `0.218948754711122` | `0.218948754577796` |
| `qutrit_complex_c` | `0.123224872387251` | `0.12322487230933` | pinching | `0.0215389168497651` | `0.0215389168410927` | `0.101685955537486` | `0.101685955468237` |
| `qutrit_complex_c` | `0.123224872387251` | `0.12322487230933` | depolarizing | `0.051667148677739` | `0.0516671484879605` | `0.071557723709512` | `0.0715577238213695` |

## Rejected Controls

- Transposition was rejected in dimensions 2 and 3: minimum Choi eigenvalue
  `-1.0`, despite zero trace-preservation residual.
- Trace scaling by `1.10` was rejected in dimensions 2 and 3: complete
  positivity passed, but the trace-preservation residual was `0.1`; all six
  mapped outputs also failed density-output validation.
- Neither rejected control invoked QICS or contributed to the accepted count.

## Environment Receipt

- Python `3.11.13`
- QICS `1.1.3`
- QICS commit `be18e5ef07258dec9e5db6bb18c1ee9b2003d545`
- QICS tree `84d77a4a74af48a011594baed338b2b5fd68181d`
- NumPy `2.4.6`
- SciPy `1.17.1`
- QICS checkout status: clean

## SHA-256

Both deterministic result files:

```text
5792308a8e6bb001039a3f1938b8bfa5199bbab65c9d7f163c32d7211db68b9c  result.json
5792308a8e6bb001039a3f1938b8bfa5199bbab65c9d7f163c32d7211db68b9c  rerun_result.json
```

Packet sources:

```text
fbf670517cdb9772977f48936a8752dd229231efb2e79f8aa51a6f6f8d415302  spec.json
27c17439afbde76e13395b7675174f1127def071b5c05bf8bfd8f6d14bfe1f8b  qics_entropy_dpi_numeric_oracle_v0.py
b28ed9ccc5bb810df535a7309ec754a8500f39e4df85a2397fe6bba5d52acc35  validate_qics_entropy_dpi_numeric_oracle_v0.py
7f8e3b567d48587b816cfc56a658e679b00aaa59729840af95bbee6633e0acaa  run_all.sh
```

Pinned runtime and distribution metadata:

```text
26ea714a88872c5c389fadf88b8c28bf47f7b9c2c035fe568801f61dad87e2f9  resolved Python executable
b082c52ccbe3b880bae177c35171b52ed6c947f3ad71e3762f2723f60a411de0  NumPy METADATA
b1cd2c784f6e003c6c71af4c5ee57f6370ee467d17b656250d9fd38cf579d7d0  SciPy METADATA
```

QICS source dependencies:

```text
7cf0e3fc46e5687ba61bfa0b8968da8e9a6af44583564403c9eae3f3307bc25b  qics/cones/entropy/quantrelentr.py
49d4181a2cf49766624ca73423aaf8717ca6247b330f61fb4ff08fad661123c3  qics/model.py
9eac436d35721d709dcaddc090eafa8e9c937f07e53fdb3cef390397e4adc75a  qics/solver.py
14858a08ec721234077c922e2fca54de3618adabd7b1f10fb5c2bfb8942f132e  qics/vectorize.py
```

## Boundary

The evidence is limited to this fixed finite packet and the pinned runtime.
The blocked consumers in `spec.json` remain blocked.
