# Skill, Claude Bridge, NVIDIA, and xAI Status

Status timestamp: 2026-07-15. These are advisory/control-plane surfaces. None can open G0-G10 or decide a Ratchet tooth.

## Claude bridge

| Check | Result | Boundary |
|---|---|---|
| Claude Code installed | PASS | `/usr/local/bin/claude`, version `2.1.210` |
| `.codex` skill structure | PASS | `quick_validate.py` and Python compilation pass |
| `.agents` skill structure | PASS | `quick_validate.py` and Python compilation pass |
| Fable 5 dynamic route | PARTIAL | `fable5` resolves through moving alias `fable`; receipt backend truth was `claude-fable-5` |
| Bounded completion | RED | Requested cap `$0.05`; provider stopped with `error_max_budget_usd` after reporting `$0.2322` |
| Ratchet gate authority | FORBIDDEN | Bridge output is external advisory evidence only |

Receipt: `/tmp/codex_claude_bridge_v8/20260715T204450Z-v8-fable-alias-smoke-f5bd91c5fef3.receipt.json`.

The alias, authentication, and backend route work. The task did not complete within the requested provider-side cap. `--max-budget-usd` is therefore a stop condition, not a hard pre-dispatch spending guarantee.

The installed copies are behaviorally unequal. `/Users/joshuaeisenhart/.codex/skills/claude-bridge` has timeout/fallback/fanout and richer receipt guidance that `/Users/joshuaeisenhart/.agents/skills/claude-bridge` lacks. A broad copy was not performed: the correct repair is to generate both from one canonical manifest and parity-test behavior, not silently overwrite one live surface.

## Skill estate

Machine inventory: `/tmp/codex_skill_agent_inventory_v8.json`.

| Surface | Count | Current interpretation |
|---|---:|---|
| Primary Codex installed skills | 91 | Installed inventory, not all behaviorally verified |
| Agents installed skills | 73 | Separate live surface |
| Repo Codex skills | 15 | Owner/repo source family |
| System-v4 skill specs | 84 | Historical/specification surface |
| Hermes installed/archive skills | 202 | Intake candidates, not automatically admitted |
| Claude agents detected | 0 | Preserved red against current inventory expectation |

No Codex skill is missing by name from the inventory comparison, but behavioral parity is red for `jax-sim`, `julia-sim`, `pytorch-sim`, and `three-engine-sim`. The repo `codex-ratchet-tool-status-auditor` also contains references/scripts absent from installed copies. `python3 -m pytest -q system_v5/tests/test_codex_skill_agent_inventory.py` produced one pass and one failure because the inventory reports zero Claude agents.

The safe update order is:

1. choose one owner manifest per skill;
2. classify repo, installed Codex, Agents, Claude, Hermes, and wiki surfaces by authority;
3. generate mirrors mechanically;
4. run structural and behavioral vectors;
5. admit only an explicitly reviewed delta.

“Update all skills” is not currently green because blind synchronization would erase meaningful surface differences.

## NVIDIA NIM API

| Check | Result |
|---|---|
| `NVIDIA_API_KEY` present in the current process | PASS |
| Authenticated zero-inference `/v1/models` probe | PASS |
| Models returned | 116 |
| Completion/inference probe | NOT RUN |
| Ratchet gate authority | FORBIDDEN |

The authenticated catalog currently includes these notable Chinese model IDs:

- `deepseek-ai/deepseek-v4-flash`
- `deepseek-ai/deepseek-v4-pro`
- `minimaxai/minimax-m2.7`
- `minimaxai/minimax-m3`
- `moonshotai/kimi-k2.6`
- `qwen/qwen3-next-80b-a3b-instruct`
- `qwen/qwen3.5-122b-a10b`
- `qwen/qwen3.5-397b-a17b`
- `z-ai/glm-5.2`

Official NVIDIA documentation describes free Developer Program access for prototyping, but does not define one universal hourly allowance. NVIDIA says the hosted rate varies by model and traffic and the account catalog is authoritative. A 40 requests-per-minute personal free-tier ceiling is commonly reported in current NVIDIA forum guidance; this is not an hourly guarantee and must be discovered/recorded per account and model.

Before advisory fanout, add a local token-bucket ledger keyed by provider, account, exact model ID, quota window, and observed 429/reset metadata. On unknown quota or catalog drift, HOLD the advisory dispatch; never relax a Ratchet gate.

## xAI API

| Check | Result |
|---|---|
| `XAI_API_KEY` present in the current process | PASS |
| Authenticated zero-inference `/v1/models` probe | PASS |
| Models returned | 10 |
| Current text IDs observed | `grok-4.20-0309-*`, `grok-4.3`, `grok-4.5`, `grok-build-0.1` |
| Completion/inference probe | NOT RUN |
| Ratchet gate authority | FORBIDDEN |

xAI documents per-model RPS and TPM limits that scale with account spend tier. The team console, not a hard-coded prose value, is the authority. xAI's Management API can additionally impose per-key QPS/QPM/TPM and spending limits; those controls should be configured before any autonomous advisory campaign.

## Required provider envelope

Every future provider receipt should record exact requested alias, resolved alias, backend model ID, endpoint, request hash, output hash, timestamps, usage/cost, quota metadata, return code, and pricing/catalog snapshot hash. Provider artifacts must use a schema and directory that deterministic Ratchet validators explicitly reject as gate input.

