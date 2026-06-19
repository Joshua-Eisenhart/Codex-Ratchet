# Source Family Matrix

Use this matrix before porting any skill, agent, or workflow source into Codex.

| Family | Typical Paths | Authority Status | Port Target | Rejection Signs |
|---|---|---|---|---|
| installed Codex skill | `/Users/joshuaeisenhart/.codex-second/skills/*/SKILL.md` | active local Codex behavior | patch installed copy only after repo source or explicit repair | stale trigger, missing validation, contradicts repo authority |
| installed `.agents` skill | `/Users/joshuaeisenhart/.agents/skills/*/SKILL.md` | active local agent behavior and Codex-adjacent workflow source | reference directly, add adapter docs, or mirror only when Codex needs a separate runtime surface | recreating existing `codex-autoresearch`, `tribunal`, or `cdo` behavior as a fake gap |
| repo-held Codex skill | `system_v5/codex_skills/*/SKILL.md` | source candidate until installed | install into `$CODEX_HOME/skills` after validation | unvalidated, no active use case |
| Wizard packet-local skill | `~/wiki/wizard/packet-v4-2-current/skills/*/SKILL.md` | packet-local canonical when manifest-listed | reference or mirror into Codex skill | contradicts `WIZARD_v4_2.md`, not manifest-listed |
| Claude skill | `.claude/skills/*/SKILL.md` | reference only | pattern card, Codex skill, or workflow | claims Claude behavior law, copies route truth |
| Claude agent | `.claude/agents/*.md` | reference only | Codex role card or task prompt template | builder audits itself, unreceipted worker claim |
| Hermes rule/doc | `system_v5/ops/HERMES_RULES.md`, archive Hermes docs, wiki Hermes docs | reference/control-plane pressure | bounded intake skill, workflow, or guardrail | unbounded ingestion, stale boot claim, shared-state mutation |
| Hermes installed skill | `/Users/joshuaeisenhart/.hermes/skills/*/SKILL.md` | active Hermes behavior only | bounded intake source, Codex skill pattern, or reject | Hermes authority copied into Codex, no usage proof |
| Hermes wiki spine | `/Users/joshuaeisenhart/wiki/hermes-current/*.md` | Hermes working spine, reference for Codex | bounded intake read order, wiki route card | treating note existence as proof |
| Hermes wiki receipt | `/Users/joshuaeisenhart/wiki/queries/*.md`, `/Users/joshuaeisenhart/wiki/hermes-current/archive/*.md` | receipt or historical run note | verification pattern, test fixture, or reference | stale receipt treated as current run |
| system_v4 skill spec | `system_v4/skill_specs/*/SKILL.md` | legacy/spec source | modern Codex skill or script | old absolute path, legacy-only graph assumption |
| system_v4 executable operator | `system_v4/skills/*.py` | executable source when tests exist | script, validator, or skill wrapper | no smoke test, hidden write authority |
| Karpathy family | `/Users/joshuaeisenhart/.agents/skills/codex-autoresearch/SKILL.md`, `system_v4/skills/bounded_improve_operator.py`, `system_v4/a1_state/*`, local Karpathy reference repos | active skill plus executable/support patterns | use `$codex-autoresearch` for primary loops; add bounded support wrappers or reference cards only for smaller local mechanics | full-family overclaim, unbounded mutation, pretending autoresearch is missing |
| user correction | current conversation or owner note | highest for current turn | patch current target directly | ambiguous preference or missing artifact target |

Every accepted port needs:

```yaml
source_path:
family:
authority_status:
target_surface:
minimal_test:
promotion_boundary:
```
