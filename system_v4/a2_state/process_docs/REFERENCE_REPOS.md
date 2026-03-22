# Reference Repository Catalog

Read-only pattern libraries stored at `~/GitHub/reference/`.
These are **not** part of Codex Ratchet — they are third-party code studied by the A2 refinery for design patterns.

## License Status

| Repo | License | Safe to Study | Safe to Fork/Modify |
|------|---------|--------------|---------------------|
| karpathy/nanoGPT | MIT | ✅ | ✅ |
| karpathy/minbpe | MIT | ✅ | ✅ |
| karpathy/llm.c | MIT | ✅ | ✅ |
| karpathy/autoresearch | No license file | ✅ study | ⚠️ no explicit permission |
| karpathy/llm-council | No license file | ✅ study | ⚠️ no explicit permission |
| deepmind/alphageometry | Apache 2.0 | ✅ | ✅ |
| aiming-lab/AutoResearchClaw | MIT | ✅ | ✅ |
| ellisk42/dreamcoder-ec | MIT | ✅ | ✅ |
| Z3Prover/z3 | MIT (Microsoft) | ✅ | ✅ |

**7 of 9 are fully open source (MIT/Apache).** The two without license files (autoresearch, llm-council) are fine to read/study but should not be forked without checking with Karpathy first.

## What Each Repo Teaches the A2 Refinery

| Repo | Pattern | V4 Use |
|------|---------|--------|
| **autoresearch** | Bounded self-improvement loop: read → hypothesize → test → keep/revert | CEGIS-style refinery iteration |
| **nanoGPT** | Small visible core (1 file, clear loop) | Design philosophy for A2 tooling |
| **minbpe** | Compression as abstraction discovery | Hash/compression thinking for memory |
| **llm.c** | Extreme legibility (1000 lines, one file, C) | Kernel simplicity reference |
| **llm-council** | Multi-view deliberation with structured disagreement | Cross-perspective synthesis in A2-2 |
| **alphageometry** | Disciplined search + aggressive pruning + cached partials | Graph mining promotion gates |
| **AutoResearchClaw** | Autonomous research agent with multi-tool orchestration | Science engine pipeline design |
| **dreamcoder-ec** | Solve → discover reusable primitives → compress search | Abstraction learning for A2-1 kernel |
| **z3** | SAT/SMT constraint satisfaction / hard rejection | Fail-closed admission guards |

## Disk Location

```
~/GitHub/reference/
├── karpathy/
│   ├── autoresearch/
│   ├── nanoGPT/
│   ├── minbpe/
│   ├── llm.c/
│   └── llm-council/
├── deepmind/
│   └── alphageometry/
└── other/
    ├── AutoResearchClaw/
    ├── dreamcoder-ec/
    └── z3/
```

## Rules
1. **Do not copy code** from these repos into Codex Ratchet without checking the license.
2. **Do study patterns** — the A2 refinery extracts design patterns, not code.
3. **MIT/Apache repos** (7 of 9) can be freely forked and modified if needed later.
4. These repos are **not version-controlled** by Codex Ratchet. They live separately.

---

## Additional Reference Orgs (Standing Instruction: Use Freely)

| Org | URL | What to Use |
|-----|-----|-------------|
| **lev-os** | https://github.com/lev-os | Skill patterns (`agents/skills/`), agent orchestration, `lev-skills.sh` runtime, `agentping`, `leviathan` AI-native OS |
| **pi-mono** | https://github.com/badlogic/pi-mono | Agentic tooling packages, session scheduling. Downloaded at `~/GitHub/pi-mono/` + copies at `work/audit_tmp/pi-mono/` |

### Active lev-os Repos
- `leviathan` — AI-native OS via cognitive dataflow orchestration (TypeScript)
- `agents` — Personal agent dotfiles with **skill system** (skills/, skills-db/, skill-discovery)
- `agentping` — Human-in-the-loop primitives for AI agents
- `lev-content` — Docs, skills, prompts, and assets for Lev ecosystem
- `lev-agentfs` — Agent filesystem (Rust fork of turso agentfs)
- `agent-lease` — Git hooks that force validation before commits

**Standing instruction:** All reference repos (above table + lev-os + pi-mono) may be freely consulted for design patterns, architectural reference, and skill building.
