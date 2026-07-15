# Skill and Provider Status

Status timestamp: 2026-07-15. Every surface here is advisory/control-plane
only and is structurally forbidden from opening a Ratchet gate.

## Engine skills

The repo-held JAX, Julia, PyTorch, three-engine, and sim-stack skill bodies
match their installed Codex copies. The only observed difference is the
expected source-family preamble: installed copy versus repo-held source. The
environment-coordination copy is byte-identical.

This does not prove every installed skill behavior. The finite code/runtime
roster and its receipts remain the authority for sim integration.

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
