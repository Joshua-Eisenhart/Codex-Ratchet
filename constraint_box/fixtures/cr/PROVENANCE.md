# CR GKSL Fixture Provenance

Status: **passes local rerun**. Claim ceiling: finite S1 acceptance fixture only. `promotion_allowed=false`.

## Source sim run

Command:

```sh
cd /Users/joshuaeisenhart/Codex-Ratchet && /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v7/constraint_core/sims_and_scripts/nonunitality_theorem_sim.py
```

Full stdout:

```text
operators (must all be unital, ||L(I)||=0):
  Ti: ||L(I)|| = 0.00e+00
  Te: ||L(I)|| = 0.00e+00
  Fi: ||L(I)|| = 0.00e+00
  Fe: ||L(I)|| = 0.00e+00
terrains (source-locked non-unital, fused unital):
  t0 [damp ]: ||L(I)|| = 1.4142  NON-UNITAL
  t1 [depol]: ||L(I)|| = 0.0000  unital
  t2 [damp ]: ||L(I)|| = 1.4142  NON-UNITAL
  t3 [proj ]: ||L(I)|| = 0.0000  unital
  t4 [damp ]: ||L(I)|| = 1.4142  NON-UNITAL
  t5 [depol]: ||L(I)|| = 0.0000  unital
  t6 [damp ]: ||L(I)|| = 1.4142  NON-UNITAL
  t7 [proj ]: ||L(I)|| = 0.0000  unital
basis-independence: ||L(I)||=1.4142 vs conjugated ||ULU†(I)||=1.4142
```

Exit code: `0`.

## Derivation and C1-C5 receipt

Command:

```sh
cd /Users/joshuaeisenhart/Codex-Ratchet/constraint_box/fixtures/cr && /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 derive_cr_fixture.py
```

Full stdout:

```json
{
  "C1": {
    "eigenvalues": [
      0.3172344744775748,
      0.6827655255224252
    ],
    "rank": 2,
    "rho": [
      [
        0.675,
        0.052708987084635374
      ],
      [
        0.052708987084635374,
        0.325
      ]
    ],
    "trace": 1.0
  },
  "C2": {
    "dephased": [
      [
        0.675,
        0.0
      ],
      [
        0.0,
        0.325
      ]
    ]
  },
  "C3": {
    "channel_gamma": 0.6,
    "discrete_multiplier": 0.30119421191220214,
    "flow_rate": -1.2,
    "history_signature": [
      8,
      [
        -1,
        0,
        1
      ],
      [
        2,
        2,
        4
      ]
    ],
    "mutated_history_signature": [
      7,
      [
        -1,
        0,
        1
      ],
      [
        2,
        2,
        3
      ]
    ],
    "mutated_rho_eigenvalues": [
      0.28494186832393437,
      0.7150581316760657
    ],
    "rho_offdiag": 0.052708987084635374
  },
  "C4": {
    "distinct_present": [
      -1,
      0,
      1
    ],
    "history_count": 8
  },
  "C5": {
    "dephased_entropy_bits": 0.9097361225311662,
    "population_gap": 0.35000000000000003
  },
  "output": "/Users/joshuaeisenhart/Codex-Ratchet/constraint_box/fixtures/cr/cr_gksl_fixture_v1.json",
  "provenance": {
    "command": "cd /Users/joshuaeisenhart/Codex-Ratchet/constraint_box/fixtures/cr && /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 derive_cr_fixture.py",
    "derivation_script_sha256": "5812df8765e3b811c5d32e75f7f842dddf3e2d21a1e4408b2662e12688eea145",
    "discrete_rate_mapping": {
      "initial": "Frobenius norm of sim.SX, the actual step input",
      "steps": "one matrix-exponential application actually performed"
    },
    "finite_histories_mapping": {
      "chronology_claimed": false,
      "future": "kind (string)",
      "past": "eps",
      "present": "pole",
      "semantic_limit": "keyed terrain-table rows relabeled as a finite triple; no chronology is claimed",
      "source_rows": "sim.terr insertion order"
    },
    "source_sim": "/Users/joshuaeisenhart/Codex-Ratchet/system_v7/constraint_core/sims_and_scripts/nonunitality_theorem_sim.py",
    "source_sim_sha256": "6b6b56f0cc605ce989897f77e3a71ea585e6f5f9a406e2fa1b1fc21f6b67067a"
  }
}
```

Exit code: `0`.

C5 records a population gap of `0.35000000000000003` and `dephased_entropy_bits=0.9097361225311662`, strictly below `0.999`.

## Defect dispositions

- **D-1:** The evolved real matrix is asserted symmetric with `atol=1e-12` and `rtol=0.0`. No symmetrization or silent repair remains.
- **D-2:** `discrete_rate.steps=1` because the derivation performs one finite-duration matrix-exponential propagation. It is no longer derived from the unrelated number of operator generators.
- **D-3:** `discrete_rate.initial` is the Frobenius norm of `sim.SX`, the actual matrix passed into that one-step propagation. It is not bound to the damp-terrain `||L(I)||`; the equal numerical value is coincidental and the artifact says so through `discrete_rate_mapping`.
- **finite_histories mapping:** `past=eps`, `present=pole`, `future=kind (string)`, enumerated from `sim.terr` insertion-order rows. This relabels a keyed terrain table as a finite triple and claims no chronology. The same mapping and `chronology_claimed:false` are embedded in fixture provenance.

## Byte stability

Two independent derivation runs were performed. The first result was saved as `/tmp/cb-found/cr_gksl_fixture_run1.json`; the second rewrote the canonical fixture.

Command:

```sh
cmp /tmp/cb-found/cr_gksl_fixture_run1.json /Users/joshuaeisenhart/Codex-Ratchet/constraint_box/fixtures/cr/cr_gksl_fixture_v1.json
```

Stdout: `(no output)`

Exit code: `0`.

## Estate run: new CR fixture

Command:

```sh
cd /Users/joshuaeisenhart/Codex-Ratchet/constraint_box && PYTHONPATH=src /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  -m constraintbox estate --pack-root . --manifest config/sim_estate_v2.json \
  --fixture fixtures/cr/cr_gksl_fixture_v1.json --tier S1 --mode acceptance \
  --python /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 --enforce
```

Full stdout:

```json
{
  "capabilities": [
    {
      "capability_id": "stdlib_finite",
      "controls": {
        "dispatch": true,
        "mutation": true,
        "positive": true,
        "replay": true
      },
      "elapsed_seconds": 0.1658609160222113,
      "evidence": {
        "controls_not_measured": [
          "severance"
        ],
        "dispatch": [
          "set",
          "math.log2"
        ],
        "observed": {
          "fibre_sizes": [
            2,
            2,
            4
          ],
          "hartley_bits": 3.0,
          "history_count": 8,
          "projection_count": 3
        },
        "runtime": {},
        "stdout_sha256": "c2e410d08a8ed8d4833883bea59579689cf755b4c551823aef3daae0ec6e3a9e"
      },
      "expected_version": "builtin",
      "fixture_sha256": "27df1ad2b3e35ae7cc342963bcfe0fe5a0b1a2599cac4b624ca48f8686e6222f",
      "observed_version": "builtin",
      "reason": "measured_controls_passed_others_not_run",
      "required": true,
      "state": "READY",
      "worker_sha256": "355aedae5ecbb9fe306ede2672ec8f8e9dcee576610190c8b18d03e3998f3257"
    },
    {
      "capability_id": "numpy_density",
      "controls": {
        "dispatch": true,
        "mutation": true,
        "operation": true,
        "positive": true,
        "replay": true,
        "severance": true
      },
      "elapsed_seconds": 0.44239045889116824,
      "evidence": {
        "dispatch": [
          "numpy.asarray",
          "numpy.linalg.eigvalsh",
          "numpy.trace"
        ],
        "observed": {
          "dephased_entropy_bits": 0.9097361225311662,
          "eigenvalues": [
            0.3172344744775748,
            0.6827655255224252
          ],
          "hartley_bits": 1.0,
          "rank": 2,
          "trace": 1.0,
          "von_neumann_bits": 0.9013486588978599
        },
        "operation_severed": "numpy.linalg.eigvalsh",
        "runtime": {
          "dtype": "float64"
        },
        "stdout_sha256": "29c78002a3158167b52b591f9e99151ef4702c9d3116afb7aa5360921ebbf412",
        "version_drift": {
          "expected": "2.5.1",
          "observed": "2.3.4"
        }
      },
      "expected_version": "2.5.1",
      "fixture_sha256": "27df1ad2b3e35ae7cc342963bcfe0fe5a0b1a2599cac4b624ca48f8686e6222f",
      "observed_version": "2.3.4",
      "reason": "installed_version_differs_from_tested_lock",
      "required": true,
      "state": "DRIFT",
      "worker_sha256": "355aedae5ecbb9fe306ede2672ec8f8e9dcee576610190c8b18d03e3998f3257"
    },
    {
      "capability_id": "scipy_channel",
      "controls": {
        "dispatch": true,
        "mutation": true,
        "operation": true,
        "positive": true,
        "replay": true,
        "severance": true
      },
      "elapsed_seconds": 0.9184298319742084,
      "evidence": {
        "dispatch": [
          "scipy.linalg.expm",
          "numpy.matmul"
        ],
        "observed": {
          "column_sum": 1.0,
          "state": [
            0.6505971059561011,
            0.3494028940438989
          ]
        },
        "operation_severed": "scipy.linalg.expm",
        "runtime": {},
        "stdout_sha256": "0578546b1cfa866c3f048a038a11455d0d0cc604c47ce871b04ef6582cc7dda8",
        "version_drift": {
          "expected": "1.18.0",
          "observed": "1.17.1"
        }
      },
      "expected_version": "1.18.0",
      "fixture_sha256": "27df1ad2b3e35ae7cc342963bcfe0fe5a0b1a2599cac4b624ca48f8686e6222f",
      "observed_version": "1.17.1",
      "reason": "installed_version_differs_from_tested_lock",
      "required": true,
      "state": "DRIFT",
      "worker_sha256": "355aedae5ecbb9fe306ede2672ec8f8e9dcee576610190c8b18d03e3998f3257"
    },
    {
      "capability_id": "z3_finite",
      "controls": {
        "dispatch": true,
        "positive": true,
        "replay": true,
        "severance": true
      },
      "elapsed_seconds": 0.3537600829731673,
      "evidence": {
        "controls_not_measured": [
          "mutation"
        ],
        "dispatch": [
          "z3.Solver.add",
          "z3.Solver.check",
          "z3.Solver.model"
        ],
        "observed": {
          "sat": "sat",
          "unsat": "unsat",
          "witness": {
            "x": 0,
            "y": 1
          }
        },
        "runtime": {},
        "stdout_sha256": "80d6aa622c045dac278ca27fdedf959af48ef848e53403ff3803a6a24f9674a8",
        "version_drift": {
          "expected": "5.0.0.0",
          "observed": "4.16.0.0"
        }
      },
      "expected_version": "5.0.0.0",
      "fixture_sha256": "27df1ad2b3e35ae7cc342963bcfe0fe5a0b1a2599cac4b624ca48f8686e6222f",
      "observed_version": "4.16.0.0",
      "reason": "installed_version_differs_from_tested_lock",
      "required": true,
      "state": "DRIFT",
      "worker_sha256": "355aedae5ecbb9fe306ede2672ec8f8e9dcee576610190c8b18d03e3998f3257"
    },
    {
      "capability_id": "cvc5_finite",
      "controls": {
        "dispatch": true,
        "positive": true,
        "replay": true,
        "severance": true
      },
      "elapsed_seconds": 0.33826820831745863,
      "evidence": {
        "controls_not_measured": [
          "mutation"
        ],
        "dispatch": [
          "cvc5.Solver.assertFormula",
          "cvc5.Solver.checkSat"
        ],
        "observed": {
          "sat": "sat",
          "unsat": "unsat"
        },
        "runtime": {},
        "stdout_sha256": "91191fb0818f99dece613bfcbc3456d5911f963d0a2ee5b39ea6f0c6469b9cb3",
        "version_drift": {
          "expected": "1.3.4",
          "observed": "1.3.3"
        }
      },
      "expected_version": "1.3.4",
      "fixture_sha256": "27df1ad2b3e35ae7cc342963bcfe0fe5a0b1a2599cac4b624ca48f8686e6222f",
      "observed_version": "1.3.3",
      "reason": "installed_version_differs_from_tested_lock",
      "required": false,
      "state": "DRIFT",
      "worker_sha256": "355aedae5ecbb9fe306ede2672ec8f8e9dcee576610190c8b18d03e3998f3257"
    },
    {
      "capability_id": "tla_controller",
      "controls": {},
      "elapsed_seconds": 0.0,
      "evidence": {
        "jar_declared": false,
        "java": "/usr/bin/java"
      },
      "expected_version": "1.7.4",
      "fixture_sha256": "27df1ad2b3e35ae7cc342963bcfe0fe5a0b1a2599cac4b624ca48f8686e6222f",
      "observed_version": null,
      "reason": "java_or_TLA2TOOLS_JAR_absent",
      "required": false,
      "state": "UNAVAILABLE",
      "worker_sha256": null
    }
  ],
  "controller_sha256": "ff1fb8d1b9bbd5f52e034e0ad33a62000a50148944844d9032564baadb3256a7",
  "elapsed_seconds": 2.4977276660501957,
  "environment": {
    "distribution_count": 370,
    "expected_lock_sha256": "fc8ad6f3c2d22123c89cb325359ed7beab3b5b258b5fed507d6450a5c4c60aef",
    "missing": [
      "cvc5==1.3.4",
      "numpy==2.5.1",
      "scipy==1.18.0",
      "z3-solver==5.0.0.0"
    ],
    "state": "DRIFT",
    "tested_lock": "requirements/locks/e0-py312-linux.lock",
    "tested_lock_sha256": "fc8ad6f3c2d22123c89cb325359ed7beab3b5b258b5fed507d6450a5c4c60aef",
    "unexpected": [
      "about-time==4.2.1",
      "absl-py==2.4.0",
      "accelerate==1.0.1",
      "aiofiles==25.1.0",
      "aiohappyeyeballs==2.6.1",
      "aiohttp==3.13.5",
      "aiosignal==1.4.0",
      "alembic==1.18.4",
      "alive-progress==3.3.0",
      "annotated-types==0.7.0",
      "anyio==4.13.0",
      "anywidget==0.11.0",
      "appdirs==1.4.4",
      "apsw==3.53.1.0",
      "apswutils==0.1.2",
      "array-api-compat==1.14.0",
      "arro3-core==0.8.0",
      "arviz-base==1.1.0",
      "arviz-plots==1.1.0",
      "arviz-stats==1.1.0",
      "arviz==1.1.0",
      "astroid==4.0.4",
      "asttokens==3.0.1",
      "astunparse==1.6.3",
      "attrs==26.1.0",
      "auto-lirpa==0.7.0",
      "autograd==1.8.0",
      "autoray==0.8.2",
      "bayeux-ml==0.1.15",
      "beartype==0.22.9",
      "beautifulsoup4==4.14.3",
      "bibtexparser==1.4.4",
      "blackjax==1.5",
      "cachetools==6.2.6",
      "certifi==2026.2.25",
      "cffi==2.0.0",
      "charset-normalizer==3.4.7",
      "chex==0.1.91",
      "cirq-aqt==1.6.1",
      "cirq-core==1.6.1",
      "cirq-google==1.6.1",
      "cirq-ionq==1.6.1",
      "cirq-pasqal==1.6.1",
      "cirq-web==1.6.1",
      "cirq==1.6.1",
      "clarabel==0.11.1",
      "click==8.3.2",
      "clifford==1.5.1",
      "cloudpickle==3.1.2",
      "cma==4.4.4",
      "cmap==0.7.2",
      "colorama==0.4.6",
      "colorlog==6.10.1",
      "comm==0.2.3",
      "cons==0.4.7",
      "contourpy==1.3.3",
      "cotengra==0.8.0",
      "cramjam==2.11.0",
      "cryptography==46.0.7",
      "cvc5==1.3.3",
      "cvxpy==1.9.1",
      "cvxpylayers==1.2.0",
      "cycler==0.12.1",
      "cyclopts==4.10.2",
      "cython==3.2.4",
      "cytoolz==1.1.0",
      "datasketch==1.9.0",
      "deap==1.4.3",
      "decorator==5.3.1",
      "deprecated==1.3.1",
      "derivative==0.6.3",
      "diastatic-malt==2.15.2",
      "diffcp==1.1.9",
      "diffrax==0.7.2",
      "diffusers==0.38.0",
      "dill==0.4.1",
      "dimod==0.12.22",
      "distro==1.9.0",
      "dm-haiku==0.0.16",
      "dm-tree==0.1.10",
      "docstring-parser==0.18.0",
      "docutils==0.22.4",
      "donfig==0.8.1.post1",
      "duet==0.2.9",
      "dwave-neal==0.6.0",
      "dwave-samplers==1.8.0",
      "dynamax==1.0.1",
      "dynamiqs==0.3.4",
      "e3nn-jax==0.21.0",
      "e3nn==0.6.0",
      "einops==0.8.2",
      "equinox==0.13.8",
      "et-xmlfile==2.0.0",
      "etils==1.14.0",
      "etuples==0.3.10",
      "evotorch==0.6.1",
      "executing==2.2.1",
      "farama-notifications==0.0.4",
      "fastcore==1.13.2",
      "fastlite==0.2.4",
      "fastparquet==2026.5.0",
      "fastprogress==1.1.6",
      "filelock==3.25.2",
      "flax==0.12.7",
      "flowmc==0.6.0",
      "fonttools==4.62.1",
      "frozendict==2.4.7",
      "frozenlist==1.8.0",
      "fsspec==2026.3.0",
      "galois==0.4.11",
      "gast==0.7.0",
      "geomstats==2.8.0",
      "google-api-core==2.30.3",
      "google-auth==2.49.2",
      "google-crc32c==1.8.0",
      "googleapis-common-protos==1.74.0",
      "graphemeu==0.7.2",
      "graphviz==0.21",
      "grpcio-status==1.71.2",
      "grpcio==1.80.0",
      "gudhi==3.12.0",
      "gymnasium==1.2.3",
      "h11==0.16.0",
      "h5netcdf==1.8.1",
      "h5py==3.16.0",
      "hdbscan==0.8.42",
      "hf-xet==1.5.0",
      "highspy==1.14.0",
      "hoptorch==0.1.4",
      "httpcore==1.0.9",
      "httptools==0.8.0",
      "httpx==0.28.1",
      "huggingface-hub==0.36.0",
      "humanize==4.15.0",
      "hypothesis==6.151.12",
      "icecream==2.2.0",
      "idna==3.11",
      "igraph==1.0.0",
      "immutabledict==4.3.1",
      "importlib-metadata==9.0.0",
      "inferactively-pymdp==1.0.3",
      "iniconfig==2.3.0",
      "ipython-pygments-lexers==1.1.1",
      "ipython==9.14.0",
      "ipywidgets==8.1.8",
      "isort==8.0.1",
      "itsdangerous==2.2.0",
      "jax-dataclasses==1.6.3",
      "jax-md==0.2.29",
      "jax-verify==1.0",
      "jax==0.10.1",
      "jaxga==0.0.2",
      "jaxlib==0.10.1",
      "jaxlie==1.5.0",
      "jaxopt==0.8.5",
      "jaxtyping==0.3.10",
      "jedi==0.20.0",
      "jinja2==3.1.6",
      "jiter==0.14.0",
      "jmp==0.0.4",
      "joblib==1.5.3",
      "jraph==0.0.6.dev0",
      "jsonschema-specifications==2025.9.1",
      "jsonschema==4.26.0",
      "jupyterlab-widgets==3.0.16",
      "kahypar==1.3.7",
      "kingdon==2.1.1",
      "kiwisolver==1.5.0",
      "lazy-loader==0.5",
      "lightning-utilities==0.15.3",
      "lightning==2.6.5",
      "lineax==0.1.1",
      "llvmlite==0.47.0",
      "logical-unification==0.4.7",
      "lxml==6.1.1",
      "mako==1.3.11",
      "markdown-it-py==4.0.0",
      "markupsafe==3.0.3",
      "matplotlib-inline==0.2.2",
      "matplotlib==3.10.8",
      "maude==1.6.0",
      "mccabe==0.7.0",
      "mctx==0.0.71",
      "mdurl==0.1.2",
      "minikanren==1.0.5",
      "ml-collections==1.1.0",
      "ml-dtypes==0.5.4",
      "monty==2026.7.16",
      "moocore==0.2.0",
      "more-itertools==11.0.1",
      "mpmath==1.3.0",
      "msgpack==1.1.2",
      "msgspec==0.21.1",
      "multidict==6.7.1",
      "multimethod==2.0.2",
      "multipledispatch==1.0.0",
      "namex==0.1.0",
      "narwhals==2.24.0",
      "netket==3.21.0",
      "networkx==3.6.1",
      "ninja==1.13.0",
      "numba==0.65.0",
      "numcodecs==0.16.5",
      "numpy-groupies==0.11.3",
      "numpy==2.3.4",
      "numpyro==0.21.0",
      "nutpie==0.16.10",
      "oauthlib==3.3.1",
      "obstore==0.10.0",
      "openai==2.36.0",
      "openpyxl==3.1.5",
      "opt-einsum-fx==0.1.4",
      "opt-einsum==3.4.0",
      "optax==0.2.8",
      "optht==0.2.0",
      "optimistix==0.1.0",
      "optree==0.19.1",
      "optuna==4.8.0",
      "orbax-checkpoint==0.11.40",
      "orjson==3.11.9",
      "oryx==0.2.9",
      "osqp==1.1.1",
      "ott-jax==0.6.0",
      "packaging==26.0",
      "palettable==3.3.3",
      "pandas==2.3.3",
      "parso==0.8.7",
      "patsy==1.0.2",
      "pennylane-lightning==0.44.0",
      "pennylane==0.44.1",
      "pexpect==4.9.0",
      "pgmpy==1.1.2",
      "pillow==12.2.0",
      "pip==26.0.1",
      "platformdirs==4.9.6",
      "plotly==6.9.0",
      "pluggy==1.6.0",
      "plum-dispatch==2.9.0",
      "pooch==1.9.0",
      "prometheus-client==0.25.0",
      "prompt-toolkit==3.0.52",
      "propcache==0.4.1",
      "proto-plus==1.27.2",
      "protobuf==5.29.6",
      "psutil==7.2.2",
      "psygnal==0.15.1",
      "ptyprocess==0.7.0",
      "pure-eval==0.2.3",
      "pyarrow==23.0.1",
      "pyasn1-modules==0.4.2",
      "pyasn1==0.6.3",
      "pycparser==3.0",
      "pydantic-core==2.41.5",
      "pydantic==2.12.5",
      "pydmd==2025.8.1",
      "pygments==2.20.0",
      "pykoopman==1.2.1",
      "pylint==4.0.5",
      "pymatgen-core==2026.7.16",
      "pymatgen==2026.5.4",
      "pymc==6.0.1",
      "pymoo==0.6.1.6",
      "pynndescent==0.6.0",
      "pyparsing==3.3.2",
      "pysindy==2.1.0",
      "pytensor==3.0.4",
      "pytest-mock==3.15.1",
      "pytest-order==1.4.0",
      "pytest==9.0.3",
      "python-dateutil==2.9.0.post0",
      "python-dotenv==1.2.2",
      "python-fasthtml==0.14.2",
      "python-multipart==0.0.29",
      "pytorch-lightning==2.6.5",
      "pytz==2026.1.post1",
      "pyvers==0.2.3",
      "pyvista==0.47.3",
      "pyyaml==6.0.3",
      "qdldl==0.1.9.post1",
      "qiskit==2.4.1",
      "quimb==1.14.0",
      "qutip-jax==0.1.1",
      "qutip==5.2.3",
      "ray==2.54.1",
      "referencing==0.37.0",
      "regex==2026.5.9",
      "requests==2.33.1",
      "ribs==0.10.0",
      "rich-rst==1.3.2",
      "rich==15.0.0",
      "rpds-py==0.30.0",
      "ruamel-yaml==0.19.1",
      "rustworkx==0.17.1",
      "safetensors==0.8.0rc0",
      "scikit-base==1.0.2",
      "scikit-learn==1.8.0",
      "scipy-openblas32==0.3.31.188.0",
      "scipy==1.17.1",
      "scooby==0.11.0",
      "scs==3.2.11",
      "seaborn==0.13.2",
      "sentencepiece==0.2.1",
      "setuptools==81.0.0",
      "simplejson==4.1.1",
      "six==1.17.0",
      "sniffio==1.3.1",
      "sortedcontainers==2.4.0",
      "soupsieve==2.8.4",
      "sparse==0.18.0",
      "sparsediffpy==0.3.0",
      "spglib==2.7.0",
      "sqlalchemy==2.0.49",
      "stack-data==0.6.3",
      "starlette==1.2.0",
      "statsmodels==0.14.6",
      "stevedore==5.7.0",
      "sympy==1.14.0",
      "tabulate==0.10.0",
      "tensordict==0.13.0",
      "tensorflow-probability==0.25.0",
      "tensornetwork==0.4.6",
      "tensorstore==0.1.84",
      "termcolor==3.3.0",
      "texttable==1.7.0",
      "threadpoolctl==3.6.0",
      "tokenizers==0.22.2",
      "tomlkit==0.14.0",
      "toolz==1.1.0",
      "toponetx==0.4.0",
      "torch-ga==0.0.6",
      "torch-geometric==2.7.0",
      "torch==2.11.0",
      "torchdiffeq==0.2.5",
      "torchmetrics==1.9.0",
      "torchode==1.0.1",
      "torchrl==0.13.3",
      "torchtyping==0.1.5",
      "tqdm==4.67.3",
      "traitlets==5.15.1",
      "transformers==4.57.0",
      "treescope==0.1.10",
      "trimesh==4.11.5",
      "typedunits==0.0.2",
      "typeguard==2.13.3",
      "typing-extensions==4.15.0",
      "typing-inspection==0.4.2",
      "tyro==1.0.13",
      "tzdata==2026.1",
      "umap-learn==0.5.12",
      "uncertainties==3.2.3",
      "urllib3==2.6.3",
      "uvicorn==0.48.0",
      "uvloop==0.22.1",
      "vtk==9.6.1",
      "wadler-lindig==0.1.7",
      "watchfiles==1.2.0",
      "wcwidth==0.7.0",
      "websockets==16.0",
      "wheel==0.46.3",
      "widgetsnbextension==4.0.15",
      "wrapt==2.1.2",
      "xarray-einstats==0.10.0",
      "xarray==2026.4.0",
      "xgi==0.10.1",
      "xitorch==0.3.0",
      "xxhash==3.6.0",
      "yarl==1.23.0",
      "z3-solver==4.16.0.0",
      "zarr==3.2.1",
      "zipp==3.23.1"
    ]
  },
  "fixture_sha256": "27df1ad2b3e35ae7cc342963bcfe0fe5a0b1a2599cac4b624ca48f8686e6222f",
  "generated_at_utc": "2026-07-27T09:06:09.882403+00:00",
  "layer_id": "S1",
  "layer_name": "claim-control simulation instruments",
  "manifest_sha256": "90ccb6cc9504ce6efc74603f219b169df43656b4726b75eef2e2373abb15427c",
  "mode": "acceptance",
  "promotion_allowed": false,
  "python_executable": "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3",
  "python_version": "3.13.6",
  "schema": "constraintbox.sim-tier-receipt.v2",
  "state": "DRIFT"
}
```

Exit code: `1`.

## Estate run: old toy fixture

Command:

```sh
cd /Users/joshuaeisenhart/Codex-Ratchet/constraint_box && PYTHONPATH=src /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  -m constraintbox estate --pack-root . --manifest config/sim_estate_v2.json \
  --fixture fixtures/manifold/manifold_fixture_v1.json --tier S1 --mode acceptance \
  --python /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 --enforce
```

Full stdout:

```json
{
  "capabilities": [
    {
      "capability_id": "stdlib_finite",
      "controls": {
        "dispatch": true,
        "mutation": true,
        "positive": true,
        "replay": true
      },
      "elapsed_seconds": 0.1676541247870773,
      "evidence": {
        "controls_not_measured": [
          "severance"
        ],
        "dispatch": [
          "set",
          "math.log2"
        ],
        "observed": {
          "fibre_sizes": [
            2,
            2
          ],
          "hartley_bits": 2.0,
          "history_count": 4,
          "projection_count": 2
        },
        "runtime": {},
        "stdout_sha256": "21dbe1d6ae8246323ec8ef1afbd31bda4124334354c78c6f22d95f0afddf324d"
      },
      "expected_version": "builtin",
      "fixture_sha256": "bef31abdda024743467a0479de650ffd814764bbbab193709a04b9318c484bed",
      "observed_version": "builtin",
      "reason": "measured_controls_passed_others_not_run",
      "required": true,
      "state": "READY",
      "worker_sha256": "355aedae5ecbb9fe306ede2672ec8f8e9dcee576610190c8b18d03e3998f3257"
    },
    {
      "capability_id": "numpy_density",
      "controls": {
        "dispatch": true,
        "mutation": true,
        "operation": true,
        "positive": true,
        "replay": true,
        "severance": true
      },
      "elapsed_seconds": 0.45483312383294106,
      "evidence": {
        "dispatch": [
          "numpy.asarray",
          "numpy.linalg.eigvalsh",
          "numpy.trace"
        ],
        "observed": {
          "dephased_entropy_bits": 0.8112781244591328,
          "eigenvalues": [
            0.14644660940672627,
            0.8535533905932737
          ],
          "hartley_bits": 1.0,
          "rank": 2,
          "trace": 1.0,
          "von_neumann_bits": 0.6008760366928562
        },
        "operation_severed": "numpy.linalg.eigvalsh",
        "runtime": {
          "dtype": "float64"
        },
        "stdout_sha256": "cac783632208937992330ba1a0d0827cde4e37d9c4b670787dac47cd59e01c06",
        "version_drift": {
          "expected": "2.5.1",
          "observed": "2.3.4"
        }
      },
      "expected_version": "2.5.1",
      "fixture_sha256": "bef31abdda024743467a0479de650ffd814764bbbab193709a04b9318c484bed",
      "observed_version": "2.3.4",
      "reason": "installed_version_differs_from_tested_lock",
      "required": true,
      "state": "DRIFT",
      "worker_sha256": "355aedae5ecbb9fe306ede2672ec8f8e9dcee576610190c8b18d03e3998f3257"
    },
    {
      "capability_id": "scipy_channel",
      "controls": {
        "dispatch": true,
        "mutation": true,
        "operation": true,
        "positive": true,
        "replay": true,
        "severance": true
      },
      "elapsed_seconds": 0.9271840420551598,
      "evidence": {
        "dispatch": [
          "scipy.linalg.expm",
          "numpy.matmul"
        ],
        "observed": {
          "column_sum": 1.0,
          "state": [
            0.7856045319244075,
            0.21439546807559248
          ]
        },
        "operation_severed": "scipy.linalg.expm",
        "runtime": {},
        "stdout_sha256": "a39939ee3395fccb52e2492616ec28e11ddae0612436d47b02bc67420ad55305",
        "version_drift": {
          "expected": "1.18.0",
          "observed": "1.17.1"
        }
      },
      "expected_version": "1.18.0",
      "fixture_sha256": "bef31abdda024743467a0479de650ffd814764bbbab193709a04b9318c484bed",
      "observed_version": "1.17.1",
      "reason": "installed_version_differs_from_tested_lock",
      "required": true,
      "state": "DRIFT",
      "worker_sha256": "355aedae5ecbb9fe306ede2672ec8f8e9dcee576610190c8b18d03e3998f3257"
    },
    {
      "capability_id": "z3_finite",
      "controls": {
        "dispatch": true,
        "positive": true,
        "replay": true,
        "severance": true
      },
      "elapsed_seconds": 0.32278950000181794,
      "evidence": {
        "controls_not_measured": [
          "mutation"
        ],
        "dispatch": [
          "z3.Solver.add",
          "z3.Solver.check",
          "z3.Solver.model"
        ],
        "observed": {
          "sat": "sat",
          "unsat": "unsat",
          "witness": {
            "x": 0,
            "y": 1
          }
        },
        "runtime": {},
        "stdout_sha256": "80d6aa622c045dac278ca27fdedf959af48ef848e53403ff3803a6a24f9674a8",
        "version_drift": {
          "expected": "5.0.0.0",
          "observed": "4.16.0.0"
        }
      },
      "expected_version": "5.0.0.0",
      "fixture_sha256": "bef31abdda024743467a0479de650ffd814764bbbab193709a04b9318c484bed",
      "observed_version": "4.16.0.0",
      "reason": "installed_version_differs_from_tested_lock",
      "required": true,
      "state": "DRIFT",
      "worker_sha256": "355aedae5ecbb9fe306ede2672ec8f8e9dcee576610190c8b18d03e3998f3257"
    },
    {
      "capability_id": "cvc5_finite",
      "controls": {
        "dispatch": true,
        "positive": true,
        "replay": true,
        "severance": true
      },
      "elapsed_seconds": 0.32311212411150336,
      "evidence": {
        "controls_not_measured": [
          "mutation"
        ],
        "dispatch": [
          "cvc5.Solver.assertFormula",
          "cvc5.Solver.checkSat"
        ],
        "observed": {
          "sat": "sat",
          "unsat": "unsat"
        },
        "runtime": {},
        "stdout_sha256": "91191fb0818f99dece613bfcbc3456d5911f963d0a2ee5b39ea6f0c6469b9cb3",
        "version_drift": {
          "expected": "1.3.4",
          "observed": "1.3.3"
        }
      },
      "expected_version": "1.3.4",
      "fixture_sha256": "bef31abdda024743467a0479de650ffd814764bbbab193709a04b9318c484bed",
      "observed_version": "1.3.3",
      "reason": "installed_version_differs_from_tested_lock",
      "required": false,
      "state": "DRIFT",
      "worker_sha256": "355aedae5ecbb9fe306ede2672ec8f8e9dcee576610190c8b18d03e3998f3257"
    },
    {
      "capability_id": "tla_controller",
      "controls": {},
      "elapsed_seconds": 0.0,
      "evidence": {
        "jar_declared": false,
        "java": "/usr/bin/java"
      },
      "expected_version": "1.7.4",
      "fixture_sha256": "bef31abdda024743467a0479de650ffd814764bbbab193709a04b9318c484bed",
      "observed_version": null,
      "reason": "java_or_TLA2TOOLS_JAR_absent",
      "required": false,
      "state": "UNAVAILABLE",
      "worker_sha256": null
    }
  ],
  "controller_sha256": "ff1fb8d1b9bbd5f52e034e0ad33a62000a50148944844d9032564baadb3256a7",
  "elapsed_seconds": 2.458769208053127,
  "environment": {
    "distribution_count": 370,
    "expected_lock_sha256": "fc8ad6f3c2d22123c89cb325359ed7beab3b5b258b5fed507d6450a5c4c60aef",
    "missing": [
      "cvc5==1.3.4",
      "numpy==2.5.1",
      "scipy==1.18.0",
      "z3-solver==5.0.0.0"
    ],
    "state": "DRIFT",
    "tested_lock": "requirements/locks/e0-py312-linux.lock",
    "tested_lock_sha256": "fc8ad6f3c2d22123c89cb325359ed7beab3b5b258b5fed507d6450a5c4c60aef",
    "unexpected": [
      "about-time==4.2.1",
      "absl-py==2.4.0",
      "accelerate==1.0.1",
      "aiofiles==25.1.0",
      "aiohappyeyeballs==2.6.1",
      "aiohttp==3.13.5",
      "aiosignal==1.4.0",
      "alembic==1.18.4",
      "alive-progress==3.3.0",
      "annotated-types==0.7.0",
      "anyio==4.13.0",
      "anywidget==0.11.0",
      "appdirs==1.4.4",
      "apsw==3.53.1.0",
      "apswutils==0.1.2",
      "array-api-compat==1.14.0",
      "arro3-core==0.8.0",
      "arviz-base==1.1.0",
      "arviz-plots==1.1.0",
      "arviz-stats==1.1.0",
      "arviz==1.1.0",
      "astroid==4.0.4",
      "asttokens==3.0.1",
      "astunparse==1.6.3",
      "attrs==26.1.0",
      "auto-lirpa==0.7.0",
      "autograd==1.8.0",
      "autoray==0.8.2",
      "bayeux-ml==0.1.15",
      "beartype==0.22.9",
      "beautifulsoup4==4.14.3",
      "bibtexparser==1.4.4",
      "blackjax==1.5",
      "cachetools==6.2.6",
      "certifi==2026.2.25",
      "cffi==2.0.0",
      "charset-normalizer==3.4.7",
      "chex==0.1.91",
      "cirq-aqt==1.6.1",
      "cirq-core==1.6.1",
      "cirq-google==1.6.1",
      "cirq-ionq==1.6.1",
      "cirq-pasqal==1.6.1",
      "cirq-web==1.6.1",
      "cirq==1.6.1",
      "clarabel==0.11.1",
      "click==8.3.2",
      "clifford==1.5.1",
      "cloudpickle==3.1.2",
      "cma==4.4.4",
      "cmap==0.7.2",
      "colorama==0.4.6",
      "colorlog==6.10.1",
      "comm==0.2.3",
      "cons==0.4.7",
      "contourpy==1.3.3",
      "cotengra==0.8.0",
      "cramjam==2.11.0",
      "cryptography==46.0.7",
      "cvc5==1.3.3",
      "cvxpy==1.9.1",
      "cvxpylayers==1.2.0",
      "cycler==0.12.1",
      "cyclopts==4.10.2",
      "cython==3.2.4",
      "cytoolz==1.1.0",
      "datasketch==1.9.0",
      "deap==1.4.3",
      "decorator==5.3.1",
      "deprecated==1.3.1",
      "derivative==0.6.3",
      "diastatic-malt==2.15.2",
      "diffcp==1.1.9",
      "diffrax==0.7.2",
      "diffusers==0.38.0",
      "dill==0.4.1",
      "dimod==0.12.22",
      "distro==1.9.0",
      "dm-haiku==0.0.16",
      "dm-tree==0.1.10",
      "docstring-parser==0.18.0",
      "docutils==0.22.4",
      "donfig==0.8.1.post1",
      "duet==0.2.9",
      "dwave-neal==0.6.0",
      "dwave-samplers==1.8.0",
      "dynamax==1.0.1",
      "dynamiqs==0.3.4",
      "e3nn-jax==0.21.0",
      "e3nn==0.6.0",
      "einops==0.8.2",
      "equinox==0.13.8",
      "et-xmlfile==2.0.0",
      "etils==1.14.0",
      "etuples==0.3.10",
      "evotorch==0.6.1",
      "executing==2.2.1",
      "farama-notifications==0.0.4",
      "fastcore==1.13.2",
      "fastlite==0.2.4",
      "fastparquet==2026.5.0",
      "fastprogress==1.1.6",
      "filelock==3.25.2",
      "flax==0.12.7",
      "flowmc==0.6.0",
      "fonttools==4.62.1",
      "frozendict==2.4.7",
      "frozenlist==1.8.0",
      "fsspec==2026.3.0",
      "galois==0.4.11",
      "gast==0.7.0",
      "geomstats==2.8.0",
      "google-api-core==2.30.3",
      "google-auth==2.49.2",
      "google-crc32c==1.8.0",
      "googleapis-common-protos==1.74.0",
      "graphemeu==0.7.2",
      "graphviz==0.21",
      "grpcio-status==1.71.2",
      "grpcio==1.80.0",
      "gudhi==3.12.0",
      "gymnasium==1.2.3",
      "h11==0.16.0",
      "h5netcdf==1.8.1",
      "h5py==3.16.0",
      "hdbscan==0.8.42",
      "hf-xet==1.5.0",
      "highspy==1.14.0",
      "hoptorch==0.1.4",
      "httpcore==1.0.9",
      "httptools==0.8.0",
      "httpx==0.28.1",
      "huggingface-hub==0.36.0",
      "humanize==4.15.0",
      "hypothesis==6.151.12",
      "icecream==2.2.0",
      "idna==3.11",
      "igraph==1.0.0",
      "immutabledict==4.3.1",
      "importlib-metadata==9.0.0",
      "inferactively-pymdp==1.0.3",
      "iniconfig==2.3.0",
      "ipython-pygments-lexers==1.1.1",
      "ipython==9.14.0",
      "ipywidgets==8.1.8",
      "isort==8.0.1",
      "itsdangerous==2.2.0",
      "jax-dataclasses==1.6.3",
      "jax-md==0.2.29",
      "jax-verify==1.0",
      "jax==0.10.1",
      "jaxga==0.0.2",
      "jaxlib==0.10.1",
      "jaxlie==1.5.0",
      "jaxopt==0.8.5",
      "jaxtyping==0.3.10",
      "jedi==0.20.0",
      "jinja2==3.1.6",
      "jiter==0.14.0",
      "jmp==0.0.4",
      "joblib==1.5.3",
      "jraph==0.0.6.dev0",
      "jsonschema-specifications==2025.9.1",
      "jsonschema==4.26.0",
      "jupyterlab-widgets==3.0.16",
      "kahypar==1.3.7",
      "kingdon==2.1.1",
      "kiwisolver==1.5.0",
      "lazy-loader==0.5",
      "lightning-utilities==0.15.3",
      "lightning==2.6.5",
      "lineax==0.1.1",
      "llvmlite==0.47.0",
      "logical-unification==0.4.7",
      "lxml==6.1.1",
      "mako==1.3.11",
      "markdown-it-py==4.0.0",
      "markupsafe==3.0.3",
      "matplotlib-inline==0.2.2",
      "matplotlib==3.10.8",
      "maude==1.6.0",
      "mccabe==0.7.0",
      "mctx==0.0.71",
      "mdurl==0.1.2",
      "minikanren==1.0.5",
      "ml-collections==1.1.0",
      "ml-dtypes==0.5.4",
      "monty==2026.7.16",
      "moocore==0.2.0",
      "more-itertools==11.0.1",
      "mpmath==1.3.0",
      "msgpack==1.1.2",
      "msgspec==0.21.1",
      "multidict==6.7.1",
      "multimethod==2.0.2",
      "multipledispatch==1.0.0",
      "namex==0.1.0",
      "narwhals==2.24.0",
      "netket==3.21.0",
      "networkx==3.6.1",
      "ninja==1.13.0",
      "numba==0.65.0",
      "numcodecs==0.16.5",
      "numpy-groupies==0.11.3",
      "numpy==2.3.4",
      "numpyro==0.21.0",
      "nutpie==0.16.10",
      "oauthlib==3.3.1",
      "obstore==0.10.0",
      "openai==2.36.0",
      "openpyxl==3.1.5",
      "opt-einsum-fx==0.1.4",
      "opt-einsum==3.4.0",
      "optax==0.2.8",
      "optht==0.2.0",
      "optimistix==0.1.0",
      "optree==0.19.1",
      "optuna==4.8.0",
      "orbax-checkpoint==0.11.40",
      "orjson==3.11.9",
      "oryx==0.2.9",
      "osqp==1.1.1",
      "ott-jax==0.6.0",
      "packaging==26.0",
      "palettable==3.3.3",
      "pandas==2.3.3",
      "parso==0.8.7",
      "patsy==1.0.2",
      "pennylane-lightning==0.44.0",
      "pennylane==0.44.1",
      "pexpect==4.9.0",
      "pgmpy==1.1.2",
      "pillow==12.2.0",
      "pip==26.0.1",
      "platformdirs==4.9.6",
      "plotly==6.9.0",
      "pluggy==1.6.0",
      "plum-dispatch==2.9.0",
      "pooch==1.9.0",
      "prometheus-client==0.25.0",
      "prompt-toolkit==3.0.52",
      "propcache==0.4.1",
      "proto-plus==1.27.2",
      "protobuf==5.29.6",
      "psutil==7.2.2",
      "psygnal==0.15.1",
      "ptyprocess==0.7.0",
      "pure-eval==0.2.3",
      "pyarrow==23.0.1",
      "pyasn1-modules==0.4.2",
      "pyasn1==0.6.3",
      "pycparser==3.0",
      "pydantic-core==2.41.5",
      "pydantic==2.12.5",
      "pydmd==2025.8.1",
      "pygments==2.20.0",
      "pykoopman==1.2.1",
      "pylint==4.0.5",
      "pymatgen-core==2026.7.16",
      "pymatgen==2026.5.4",
      "pymc==6.0.1",
      "pymoo==0.6.1.6",
      "pynndescent==0.6.0",
      "pyparsing==3.3.2",
      "pysindy==2.1.0",
      "pytensor==3.0.4",
      "pytest-mock==3.15.1",
      "pytest-order==1.4.0",
      "pytest==9.0.3",
      "python-dateutil==2.9.0.post0",
      "python-dotenv==1.2.2",
      "python-fasthtml==0.14.2",
      "python-multipart==0.0.29",
      "pytorch-lightning==2.6.5",
      "pytz==2026.1.post1",
      "pyvers==0.2.3",
      "pyvista==0.47.3",
      "pyyaml==6.0.3",
      "qdldl==0.1.9.post1",
      "qiskit==2.4.1",
      "quimb==1.14.0",
      "qutip-jax==0.1.1",
      "qutip==5.2.3",
      "ray==2.54.1",
      "referencing==0.37.0",
      "regex==2026.5.9",
      "requests==2.33.1",
      "ribs==0.10.0",
      "rich-rst==1.3.2",
      "rich==15.0.0",
      "rpds-py==0.30.0",
      "ruamel-yaml==0.19.1",
      "rustworkx==0.17.1",
      "safetensors==0.8.0rc0",
      "scikit-base==1.0.2",
      "scikit-learn==1.8.0",
      "scipy-openblas32==0.3.31.188.0",
      "scipy==1.17.1",
      "scooby==0.11.0",
      "scs==3.2.11",
      "seaborn==0.13.2",
      "sentencepiece==0.2.1",
      "setuptools==81.0.0",
      "simplejson==4.1.1",
      "six==1.17.0",
      "sniffio==1.3.1",
      "sortedcontainers==2.4.0",
      "soupsieve==2.8.4",
      "sparse==0.18.0",
      "sparsediffpy==0.3.0",
      "spglib==2.7.0",
      "sqlalchemy==2.0.49",
      "stack-data==0.6.3",
      "starlette==1.2.0",
      "statsmodels==0.14.6",
      "stevedore==5.7.0",
      "sympy==1.14.0",
      "tabulate==0.10.0",
      "tensordict==0.13.0",
      "tensorflow-probability==0.25.0",
      "tensornetwork==0.4.6",
      "tensorstore==0.1.84",
      "termcolor==3.3.0",
      "texttable==1.7.0",
      "threadpoolctl==3.6.0",
      "tokenizers==0.22.2",
      "tomlkit==0.14.0",
      "toolz==1.1.0",
      "toponetx==0.4.0",
      "torch-ga==0.0.6",
      "torch-geometric==2.7.0",
      "torch==2.11.0",
      "torchdiffeq==0.2.5",
      "torchmetrics==1.9.0",
      "torchode==1.0.1",
      "torchrl==0.13.3",
      "torchtyping==0.1.5",
      "tqdm==4.67.3",
      "traitlets==5.15.1",
      "transformers==4.57.0",
      "treescope==0.1.10",
      "trimesh==4.11.5",
      "typedunits==0.0.2",
      "typeguard==2.13.3",
      "typing-extensions==4.15.0",
      "typing-inspection==0.4.2",
      "tyro==1.0.13",
      "tzdata==2026.1",
      "umap-learn==0.5.12",
      "uncertainties==3.2.3",
      "urllib3==2.6.3",
      "uvicorn==0.48.0",
      "uvloop==0.22.1",
      "vtk==9.6.1",
      "wadler-lindig==0.1.7",
      "watchfiles==1.2.0",
      "wcwidth==0.7.0",
      "websockets==16.0",
      "wheel==0.46.3",
      "widgetsnbextension==4.0.15",
      "wrapt==2.1.2",
      "xarray-einstats==0.10.0",
      "xarray==2026.4.0",
      "xgi==0.10.1",
      "xitorch==0.3.0",
      "xxhash==3.6.0",
      "yarl==1.23.0",
      "z3-solver==4.16.0.0",
      "zarr==3.2.1",
      "zipp==3.23.1"
    ]
  },
  "fixture_sha256": "bef31abdda024743467a0479de650ffd814764bbbab193709a04b9318c484bed",
  "generated_at_utc": "2026-07-27T09:06:17.606913+00:00",
  "layer_id": "S1",
  "layer_name": "claim-control simulation instruments",
  "manifest_sha256": "90ccb6cc9504ce6efc74603f219b169df43656b4726b75eef2e2373abb15427c",
  "mode": "acceptance",
  "promotion_allowed": false,
  "python_executable": "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3",
  "python_version": "3.13.6",
  "schema": "constraintbox.sim-tier-receipt.v2",
  "state": "DRIFT"
}
```

Exit code: `1`.

## Estate comparison

| capability_id | state on OLD toy fixture | state on NEW CR fixture | same? |
|---|---:|---:|:---:|
| cvc5_finite | DRIFT | DRIFT | yes |
| numpy_density | DRIFT | DRIFT | yes |
| scipy_channel | DRIFT | DRIFT | yes |
| stdlib_finite | READY | READY | yes |
| tla_controller | UNAVAILABLE | UNAVAILABLE | yes |
| z3_finite | DRIFT | DRIFT | yes |

Verbatim reason comparison:

- `cvc5_finite`: old `installed_version_differs_from_tested_lock`; new `installed_version_differs_from_tested_lock`.
- `numpy_density`: old `installed_version_differs_from_tested_lock`; new `installed_version_differs_from_tested_lock`.
- `scipy_channel`: old `installed_version_differs_from_tested_lock`; new `installed_version_differs_from_tested_lock`.
- `stdlib_finite`: old `measured_controls_passed_others_not_run`; new `measured_controls_passed_others_not_run`.
- `tla_controller`: old `java_or_TLA2TOOLS_JAR_absent`; new `java_or_TLA2TOOLS_JAR_absent`.
- `z3_finite`: old `installed_version_differs_from_tested_lock`; new `installed_version_differs_from_tested_lock`.

No capability has a new failure reason under the CR fixture. Every state and every reason string matches. The enforced exit `1` in both runs is the known tier-level `DRIFT`, specifically the version-lock reason `installed_version_differs_from_tested_lock` for NumPy, SciPy, Z3, and cvc5. `tla_controller` is `UNAVAILABLE` for the same `java_or_TLA2TOOLS_JAR_absent` reason on both fixtures. No differing state requires diagnosis because there are no state differences.

## Full suite

Command:

```sh
cd /Users/joshuaeisenhart/Codex-Ratchet/constraint_box && PYTHONPATH=src /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  -m unittest discover -s tests 2>&1 | grep -E '^(Ran|OK|FAILED)'
```

Filtered output:

```text
Ran 224 tests in 44.443s
OK
```

Underlying unittest exit code: `0`.

## Git status

Command: `git status --porcelain`

Full stdout:

```text
 M Makefile
 M claimgate_plugin/formal/results/chain_bmc_v0.json
 M claimgate_plugin/results/gate_ledger.head.json
 M claimgate_plugin/results/gate_ledger.jsonl
 M claimgate_plugin/results/legacy_ratchet_regression_v1.json
 M claimgate_plugin/results/numpy_containment_regression_v1.json
 M claimgate_plugin/results/typed_grammar_regression_v1.json
 M claimgate_plugin/run_numpy_containment_regression.py
 M ratchet_contract/gates.py
 M ratchet_contract/results/ratchet_tick.json
 M ratchet_contract/results/ratchet_tick_floors_chain.json
 M ratchet_contract/results/ratchet_tick_floors_v2.json
 M ratchet_contract/results/ratchet_tick_v2.json
 M ratchet_contract/run_ratchet_tick.py
 M scripts/ci_three_engine_seal.py
 M scripts/codex_runtime_env_doctor.py
 M system_v5/julia_carrier/Project.toml
 M system_v6/probes/toolset_expansion_20260610_python_results.json
 M system_v8/tool_ledger/battery_batch1/results/clifford.json
 M system_v8/tool_ledger/battery_batch1/results/numpyro.json
 M system_v8/tool_ledger/battery_batch3/results/blackjax.json
 M system_v8/tool_ledger/battery_batch3/results/cvxpylayers.json
 M system_v8/tool_ledger/battery_batch3/results/equinox.json
 M system_v8/tool_ledger/battery_batch3/results/flax.json
 M system_v8/tool_ledger/battery_batch3/results/igraph.json
 M system_v8/tool_ledger/battery_batch3/results/optax.json
 M system_v8/tool_ledger/battery_batch3/results/torchode.json
 M system_v8/tool_ledger/battery_batch3/results/xitorch.json
 M system_v8/tool_ledger/battery_batch4/results/numba.json
 M system_v8/tool_ledger/battery_batch5/results/pennylane_lightning.json
?? .github/workflows/slop-gate.yml
?? MODEL_DOSSIER/IGT_ENGINE_LAYOUT_EXPLICIT_MATH_20260725.md
?? claimgate_plugin/ci_slop_report.py
?? claimgate_plugin/evals/
?? claimgate_plugin/fixtures/bypass2/
?? claimgate_plugin/fixtures/ratchet/
?? claimgate_plugin/fixtures/slop/
?? claimgate_plugin/fixtures/standing/
?? claimgate_plugin/producer_standing.py
?? claimgate_plugin/results/slop_regression_v1.json
?? claimgate_plugin/run_all_gates.py
?? claimgate_plugin/run_bypass2_regression.py
?? claimgate_plugin/run_slop_regression.py
?? claimgate_plugin/run_standing_regression.py
?? claimgate_plugin/slop_gate.py
?? constraint_box/
?? ratchet_contract/tests/
?? system_v8/julia_optional/
?? system_v8/typed_ontology/
```

Only `constraint_box/fixtures/cr/` is attributable to Lane D. The repository already contains concurrent changes under `ratchet_contract/`, `claimgate_plugin/`, `.github/`, and other paths shown above; this lane did not create, edit, stage, revert, or otherwise alter them. Because `constraint_box/` is currently untracked as a whole, porcelain does not enumerate its nested CR files separately.

## What this fixture does not establish

This fixture does **not** establish scientific validity or canonicity, a theorem or formal proof, general GKSL behavior, chronology or causality for `finite_histories`, broad CR end-to-end integration, environment parity, dependency-version conformance, promotion eligibility, bridge/axis/manifold admission, or canonical-by-process status. Matching the old fixture's estate states establishes consumer compatibility on this local rerun only; it does not validate the source model. The expected `DRIFT` state and nonzero enforced estate exit are not themselves fixture failures.
