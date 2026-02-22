---
title: FlowMind Kernel
owner: lev-core
status: draft
last_reviewed: 2026-02-17
tags:
  - spec
  - flowmind
type: spec
domain: orchestration
module: flowmind
created: 2026-02-03
tier: T1
design_refs:
  - docs/design/core-flowmind.md
  - docs/design/core-sdk.md
  - docs/design/graph-lifecycle-theory.md
code_refs:
  - core/flowmind/src/**
  - core/exec/src/**
validation_gates:
  - gate:flowmind-kernel-invariants
  - gate:parser-accuracy
  - gate:abac-security
---

# FlowMind Kernel Specification

**Status:** DRAFT (Consolidated 2026-02-13)
**Author:** Lev Core Team
**Supersedes:** `spec-router.md`, `spec-router-flowmind-parser.md`, `spec-router-flowmind-ux.md`

**Lifecycle Companions:**
- [docs/specs/spec-sdlc.md](./spec-sdlc.md)
- [docs/plugins/sdlc.md](../plugins/sdlc.md)

## 1. Executive Summary

FlowMind is the **programmable substrate** of the Leviathan OS. It is not just a parser or a router; it is the kernel that classifies intent, enforces policy, and configures the execution environment.

This specification unifies:
1.  **Parser-at-Tip**: Real-time incremental scanning and intent classification (T0-T3).
2.  **Kernel Primitives**: Routing, Confidence Scoring, and TTL management.
3.  **Governance (ABAC)**: Fail-closed policy enforcement.
4.  **Harness Configuration**: Policy-driven runtime definition (Base Dev, Hashline).

---

## 2. Architecture: The FlowMind Kernel

The FlowMind kernel sits between the **User Surface** (CLI/IDE/Voice) and the **Execution Runtime**.

```mermaid
graph TD
    UserInput[User Input (Text/Voice/Code)] -->|Stream| TipScanner
    
    subgraph "Parser-at-Tip"
        TipScanner -->|Chunks| Triage(T0)
        Triage -->|Keywords| FastPath(T1)
        Triage -->|Embeddings| Centroid(T2)
        Triage -->|Fine-Tune| LLM(T3)
    end
    
    subgraph "FlowMind Kernel"
        FastPath & Centroid & LLM -->|Intent + Entities| Translator
        Translator -->|EvaluationContext| ABAC[Policy Engine]
        
        ABAC -->|Load| Policies[Policy YAMLs]
        ABAC -->|Allow/Deny| Decision
    end
    
    subgraph "Execution"
        Decision -->|ExecRequest| SDK[@lev-os/exec]
        SDK -->|Load| HarnessConfig[Harness Policy]
        HarnessConfig -->|Configure| Runtime[Runtime Env]
    end
```

### 2.1 Key Invariants
1.  **Deny by Default**: If no policy allows an action, it is denied.
2.  **Fail-Closed**: If policy evaluation fails, action is denied.
3.  **Provenance**: Every decision emits an immutable audit event.
4.  **Determinism**: Execution is deterministic by default unless explicitly relaxed.

---

## 3. Parser-at-Tip (Triage & Classification)

This layer converts raw streams into structured **FlowMind YAML** intents.

### 3.1 Triage Hierarchy
Detailed in `docs/design/core-flowmind.md`.
-   **T0 (Triage)**: Structural analysis (Size, Media, Code output). <0.1ms.
-   **T1 (Keyword)**: Deterministic regex/patterns. <1ms. High confidence trigger.
-   **T2 (Centroid)**: Embedding similarity (MiniLM-L6). ~3ms. Intent clustering.
-   **T3 (LLM)**: Fine-tuned model (Qwen/FlowMind-7B). ~200ms async. Structured extraction.

### 3.2 Translator
Converts fuzzy classification results into a typed `EvaluationContext` for the kernel. This is the boundary between "Probabilistic AI" and "Deterministic System".

---

## 4. Governance (ABAC Policy Engine)

The core logical engine. Replaces legacy "AVAC" scanner.

### 4.1 Attribute Model
-   **Subject**: `archetype` (e.g., `human-authored`, `llm-generated`, `untrusted`).
-   **Resource**: `capability` (e.g., `shell-exec`, `file-write`, `network-access`).
-   **Action**: `invoke`, `read`, `write`.
-   **Environment**: `scope` (Project, Session, Global).

### 4.2 Policy Schema
Policies are FlowMind declarations stored in `.lev/declaration/policies/`.

```yaml
type: policy
name: shell-exec-guard
spec:
  attaches_to: [capability:shell-exec]
  condition:
    type: denylist
    patterns: ['rm -rf', 'curl | sh']
  effect: deny
```

---

## 5. Runtime Configuration (Harness Policy)

Replaces hardcoded `HarnessType`. Defines the execution environment as a policy.

### 5.1 Harness Schema
Stored in `core/flowmind/policies/*.harness.yaml`.

```yaml
type: harness
extends: base-worker # Optional inheritance
name: dev-standard

capabilities:
  # The "Hashline" Edit capabilities (User Requested)
  edit_format:
    mode: dynamic # Selects best format for model
    options:
      - hashline # 3-char anchor safety (1:a3| code)
      - patch    # Standard diff
      - replace  # String match
    fallback: replace

  safety:
    mode: relaxed # Allows shell, network
    container: false

  tools:
    allow: ['*']
    block: ['system-reset']
```

### 5.2 Base Types
-   **BaseWorker**: Safe, tools=[read, search], memory=none.
-   **Chat**: Extends Base, memory=session, tools=[user-interaction].
-   **Voice**: Extends Chat, latency_constraint=<500ms, streaming=true.
-   **Dev**: Extends Base, tools=[shell, docker], safety=relaxed.

---

## 6. Determinism & UX

### 6.1 Execution Fingerprinting
To ensure reproducibility (Compliance Requirement), all deterministic workflows generate a generic fingerprint:
`SHA256(Inputs + StepOrder + DeterminismSalt)`.

### 6.2 Validation UX
-   **Compile Time**: Detect non-deterministic patterns (e.g., `consensus` w/o explicit override).
-   **Runtime**: Enforce `concurrency=1` loops if determinism is required.

---

## 7. Migration & Consolidation Plan

### 7.1 Deprecation
The following specs are consolidated into this document and will be archived:
-   `spec-router.md`
-   `spec-router-flowmind-parser.md`
-   `spec-router-flowmind-ux.md`
-   `spec-router-chat-voice-reconciliation.md`

### 7.2 Implementation Beads (Tasks)
1.  **Refactor**: Rename `core/router` -> `core/flowmind/kernel`.
2.  **Schema**: Implement `HarnessConfig` loader in `core/exec`.
3.  **Gap Fill**: Implement `Hashline` edit format in `core/tools/editor`.

### 7.3 FlowMind Program Discovery (Two Mechanisms)

FlowMind programs are discovered via two parallel mechanisms, both feeding the same compiler:

**Mechanism 1: Config-Inline**

Any `config.yaml` can embed FlowMind declarations under a `flowmind:` key:

```yaml
# plugins/core-sdlc/config.yaml
flowmind:
  on_proposal_ready:
    classify: true
    attach_plugin: sdlc
    template: path/to/sdlc-proposal.tpl.md
  maxProposalsOnScreen: 3
```

Simple flows are declared inline alongside config. As they grow, they can be extracted to files without changing the resolution contract.

**Mechanism 2: File-Based**

FlowMind programs discovered by filesystem convention:

```
<module>/src/flowmind/*.flow.yaml    # Flow declarations
<module>/src/daemon/*.yaml           # Daemon declarations
<plugin>/flowmind/*.flow.yaml        # Plugin-provided flows
```

Config values can also reference file paths for FlowMind programs:

```yaml
# config.yaml
flowmind:
  conversational_router: src/flowmind/conversational-agent.flow.yaml
  daemon: src/daemon/classifier.yaml
```

**All YAML is technically FlowMind** — FlowMind is a YAML superset. Both discovery mechanisms feed into the same compiler pipeline: parse → compile → execute → emit LevEvent.

**Resolution:** Config cascade discovers `flowmind:` keys + filesystem scan discovers `.flow.yaml` files → both feed into the kernel. Precedence follows the standard config resolution chain (system → project → module → env).

### 7.4 Plugin FlowMind Registration

Plugins declare their FlowMind programs in their `config.yaml`:

```yaml
# plugins/core-sdlc/config.yaml
flowmind:
  programs:
    - src/flowmind/sdlc-proposal.flow.yaml
    - src/flowmind/spec-workflow.flow.yaml
  entities:
    Project: { ... }
    Workstream: { ... }
  templates:
    spec: templates/spec.tpl.md
    proposal: templates/proposal.tpl.md
```

This allows the FlowMind kernel to discover and compose plugin-provided flows alongside core flows. The conversational agent can then route proposals to the appropriate domain plugin based on entity classification.

### 7.5 Playbook Registry (XDG)

Playbooks (formerly "skills") are deterministic FlowMind declarations injected into workers. Auto-generated by modules, compiled by FlowMind.

**XDG-aware config** (`~/.config/lev/config.yaml`):
```yaml
playbook_sources:
  - type: project
    path: '.lev/playbooks'    # project-local, relative path
  - type: user
    path: '${XDG_DATA_HOME}/lev/playbooks'
  - type: plugins
    path: '${HOME}/.agents/plugins/*/playbooks'
```

**Resolution:** Load playbook_sources from config, expand env vars (XDG_DATA_HOME, HOME), glob each source path. Index: `~/.config/lev/playbooks-index.json` (XDG_CONFIG_HOME).
