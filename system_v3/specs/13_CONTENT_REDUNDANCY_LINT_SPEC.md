# Content Redundancy Lint Spec (v1)
Status: DRAFT / NONCANON
Date: 2026-02-20

## Purpose
Detect semantic near-duplicates across spec docs beyond owner-collision checks.

## Inputs
- all markdown files in `system_v3/specs/`

## Lint Dimensions
1. Duplicate headings (normalized)
2. Near-duplicate paragraphs (normalized similarity threshold)
3. Repeated requirement prose across non-owner docs
4. Overlapping section intent between owner docs

## Required Output
- `reports/content_redundancy_report.json`

Fields:
- `duplicate_headings[]`
- `near_duplicate_blocks[]`
- `cross_owner_overlap[]`
- `recommended_compactions[]`

## Initial Thresholds
- heading match: exact normalized equality
- paragraph near-duplicate: cosine similarity >= `0.85`
- owner-overlap alert: cosine similarity >= `0.70`

Thresholds are noncanon defaults and may be tuned after first audit run.
