# SELECTION RATIONALE

## Why this parent batch was selected now

- `BATCH_sims_hygiene_residue_artifacts__v1` is the immediate next bounded residual family after the proof-family handoff
- the parent batch is already source-bounded and narrow enough for second-pass reduction without reopening raw source
- the strongest reusable value is not the artifacts themselves; it is the closure discipline around them

## What this refinement pass keeps

- the artifact-only hygiene shell
- pycache lineage without source promotion
- exclusion-vs-accounting separation
- pycache-vs-platform-noise split
- integrity metadata vs simulation evidence separation
- the contradiction between the hygiene pass's closure claim and the later one-file coverage correction

## What this refinement pass excludes

- no inflation of `.pyc` files into latent unbatched runner sources
- no flattening of `.DS_Store` and pycache into one artifact class
- no use of size or sha metadata as if it were evidence
- no smoothing of the later closure-correction batch into "the hygiene pass already finished everything"
