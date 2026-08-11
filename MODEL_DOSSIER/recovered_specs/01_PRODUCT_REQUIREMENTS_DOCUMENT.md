# Product Requirements Document

## Product Name

ClaimGate, internally CDO Trust Gate.

## Customer

1. OSS maintainers receiving AI-generated PRs.
2. AI-heavy startup teams using Cursor, Claude Code, Codex, Copilot, Devin-style agents, or custom coding agents.
3. Security-conscious teams that need auditable evidence before trusting generated changes.

## User Problem

AI PRs often sound more certain than their evidence. Tests can pass while the PR summary overclaims. Reviewers need to know what was claimed, what evidence exists, what remains untested, and what next check has the highest value.

## Core Promise

ClaimGate reviews the claim, not just the code.

It answers:

- What does this PR claim?
- What evidence supports that claim?
- What would falsify it?
- Did required checks run?
- Is the summary overclaiming?
- What should be checked next?
- Should merge be blocked, caveated, or allowed?

## Non-Goals

- Writing code.
- Auto-merging.
- Replacing CI.
- Replacing human code review.
- A full agent framework.
- A general philosophy / reasoning app.

## v0 Acceptance

A maintainer can install locally, run `claimgate verify`, see a deterministic verdict, and use the output as a GitHub required check.
