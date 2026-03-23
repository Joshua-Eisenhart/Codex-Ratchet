---
id: "A2_2::REFINED::lev_os_skill_system::edf23409db54ac95"
type: "KERNEL_CONCEPT"
layer: "A2_MID_REFINEMENT"
authority: "CROSS_VALIDATED"
---

# lev_os_skill_system
**Node ID:** `A2_2::REFINED::lev_os_skill_system::edf23409db54ac95`

## Description
[AUDITED] Lev-OS skill system pattern from lev-os/agents repo. Skills as named folders with SKILL.md (YAML frontmatter: name, description + markdown instructions). 17+ active skills including lev-intake, lev-plan, lev-research, lev-sdlc, lev-workshop, skill-discovery, work, workflow. Runtime via lev-skills.sh (Python): discover/list/validate/refresh with caching. skills-db/ for categorized library. skill-lock.json for version pinning.

## Outward Relations
- **DEPENDS_ON** → [[instructions]]
- **DEPENDS_ON** → [[agent]]
- **DEPENDS_ON** → [[skill]]
- **DEPENDS_ON** → [[skills]]

## Inward Relations
- [[lev_os_skill_system]] → **REFINED_INTO**
- [[package-lock.json]] → **SOURCE_MAP**
- [[package-lock.json]] → **SOURCE_MAP**
- [[package-lock.json]] → **SOURCE_MAP**
- [[assistant-message-with-thinking-code.json]] → **SOURCE_MAP**
- [[package-lock.json]] → **SOURCE_MAP**
- [[a2-lev-agents-promotion-operator]] → **SKILL_OPERATES_ON**
- [[a2-lev-architecture-fitness-operator]] → **SKILL_OPERATES_ON**
- [[a2-lev-autodev-loop-audit-operator]] → **SKILL_OPERATES_ON**
- [[a2-lev-builder-formalization-proposal-operator]] → **SKILL_OPERATES_ON**
- [[a2-lev-builder-formalization-skeleton-operator]] → **SKILL_OPERATES_ON**
- [[a2-lev-builder-placement-audit-operator]] → **SKILL_OPERATES_ON**
