# A2 Experiment Tracking (DVC)

This directory holds DVC experiment configurations for the A2 graph pipeline.

## Structure

```
experiments/
├── README.md           # This file
├── params.yaml         # Experiment parameters
└── (future dvc.yaml)   # Pipeline stages when ready
```

## Usage

- **Track a new graph snapshot**: `dvc add system_v4/a2_state/graphs/<graph>.json`
- **Check status**: `dvc status`
- **View tracked files**: `dvc list . system_v4/a2_state/graphs/`

## Tracked Artifacts

All JSON files in `system_v4/a2_state/graphs/` are tracked by DVC.
The `.dvc` metafiles store MD5 hashes for content-addressable versioning.
The actual JSON data is cached in `.dvc/cache/` and excluded from git.
