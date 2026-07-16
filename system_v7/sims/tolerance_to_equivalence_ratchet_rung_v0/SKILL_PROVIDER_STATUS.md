# Skill and Provider Status

Status timestamp: 2026-07-15. Every surface here is advisory/control-plane
only and is structurally forbidden from opening a Ratchet gate.

## Engine skills

The code-only ten-skill audit is at
`system_v5/ops/tooling/v8_skill_surface_audit_20260715/`. Its current validator
is green and all seven negative mutations are rejected.

- Repo-held sources: 10/10; active Codex copies: 10/10; Agents copies: 1/10.
- Exact repo/Codex bodies: sim-audit spine, deep-stack stress, environment
  coordination, and tool-status auditor.
- Narrow source-family-preamble parity: JAX, Julia, PyTorch, three-engine, and
  sim-stack maintenance.
- Remaining operational-body drift: Claude bridge only.
- Implementation levels: seven guidance-only, one validator-backed, one
  runner-and-validator, and one tested candidate.
- Nineteen nested routes are source-hash and line bound.

Two bounded live repairs were made: sim-audit-spine now has a repo source and
resolves the active checkout instead of hardcoding the dirty owner checkout;
deep-stack stress now uses the same adjacency-witness language and checkout
runner path in repo and active Codex copies.

This is not an all-skills-updated claim. Agents-home mirroring is not assumed,
repo-only validator payloads remain checkout-routed, and the finite
code/runtime roster plus receipts remain the authority for sim integration.

## Claude bridge candidate

Repo source now exists at system_v5/codex_skills/claude-bridge.

- Fable, fable5, and fable-5 route to Claude Code's moving fable alias.
- Default remains a distinct configured route.
- Explicit full identifiers pass through unchanged.
- Backend identity is accepted only from output modelUsage.
- Inspect-route and dry-run make zero provider calls.
- Prompt/output hashes and false evidence, gate, promotion, admission, release,
  launch, and science fields are mandatory.
- Focused tests: 20 passed plus 17 subtests.

The candidate was not installed into the live Codex or Agents homes. Live
Claude auth/backend compatibility was not rerun, and historical fanout-size
claims were intentionally omitted. The earlier low-budget live smoke remains
an informative provider-budget red, not a gate.

## NVIDIA and xAI

A shared repo-held control now performs dynamic catalog GETs and local quota
preflight without inference.

- NVIDIA NIM: 117 current models; catalog valid. DeepSeek v4 Pro dispatch
  preflight is HOLD because the account/model quota window is unknown.
- xAI: 10 current models; catalog valid. Grok 4.5 dispatch preflight is HOLD
  because the account/model quota window is unknown.

The NVIDIA catalog includes current DeepSeek, MiniMax, Kimi, Qwen, and GLM
families. No universal free-tier rate is hardcoded. The owner account/team
console or observed rate headers must supply an exact model/account limit;
unknown or exhausted quota fails closed. Catalog or provider output can never
serve as simulation, proof, admission, promotion, release, launch, or
scientific evidence.
