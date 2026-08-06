# Exploratory manifold prototypes

The current primary rough runner is `manifold_ijk_engine_prototype.py`. It is
the source-backed copy of `MANIFOLD_IJK_ENGINE_PROTOTYPE_20260803`: a finite
24-cell ring of fuzzy shells with a local I/J/K cofield, two opposite engine
hands, bounded coherent/incoherent path sums, an effective bracket seam, and a
finite dominant-state basin scan. Its checks are telemetry and deliberately do
not block execution or imply CB admission.

Run it into a disposable directory with the canonical sim-stack interpreter:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 \
  system_v8/manifold/prototypes/manifold_ijk_engine_prototype.py \
  --output-dir /private/tmp/ijk-engine-prototype-run
```

The run writes `RUN_RECEIPT.json`, `RESULT.md`, and `engine_field.svg` only to
the selected output directory. Its claim ceiling is an executed authored
prototype, not a unique manifold derivation, physical result, or validation.

The source copy has a focused three-test smoke suite:

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m unittest \
  discover -s system_v8/manifold/prototypes -p 'test_manifold_ijk_engine_prototype.py'
```

`finite_ijk_path_hopfield_proto.py` remains a smaller composite prototype. It
adds an explicit quotient/MSS toy and a deterministic Hopfield/QCA recurrent
map, but is not a validation or admission path.

The first composite prototype is `finite_ijk_path_hopfield_proto.py`. It is a
small runnable test object, not a validation or admission path.

It creates a finite `(i,j,k)` shell field, sums a finite set of oriented
`open`/`bind` histories, keeps an explicit bracket seam, quotients repeated
component signatures, and attaches a deterministic Hopfield/QCA recurrent
map. The output reports rough basins, shell subbasins, order/bracket
deformation, and a plural minimal frontier.

Run it without modifying the repository results tree:

```bash
python3 system_v8/manifold/prototypes/finite_ijk_path_hopfield_proto.py \
  --output /private/tmp/finite-ijk-prototype.json
```

The prototypes intentionally do not claim a scalar Axis 0. Their fields carry
path entropy, endpoint count, order gap, bracket gap, oriented path amplitude
gap, fuzzy-shell mass, and basin identity at each finite `(i,j,k)` coordinate.
The Hopfield layer is a finite QCA-style recurrent baseline; the separate
PyTorch and Julia/JAX probes remain available for richer density/path-sum
experiments.
