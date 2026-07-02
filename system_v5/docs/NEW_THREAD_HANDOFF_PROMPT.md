# NEW-THREAD HANDOFF PROMPT — paste this to start the fresh Wizard thread

---

You are picking up an active research program mid-stream. **Read `system_v5/docs/SESSION_HANDOFF_20260603.md` in full before doing anything** — it is the complete state. This prompt is the orientation; that doc is the detail.

## The one rule that overrides everything
A parallel fan-out of 24 layer-builders last session produced **0–1/24 genuine and 14/24 fabricated-or-smuggled**, caught *only* by fresh adversarial audits. **So: a builder's verdict on its own work is not evidence. Only a fresh-context independent audit makes a result real.** Label every finding by verification status (`AUDIT-CONFIRMED` / `SELF-REPORTED-PENDING` / `FABRICATED`). Never report "done" without the audit. The audit layer is not optional overhead — it is the only honest signal.

## The object
Nominalist constraint-admissibility physics: **F01 (finitude) + N01 (noncommutation) → admissible manifold → geometry layers (Weyl spinors, Hopf, nested Hopf tori, Clifford) assembled in a noncommutative order where the substrate changes the operation → ratchet to a maximally-constrained survivor → DoF emerge.** The owner's frame: **neural networks on exotic non-flat geometry** — flat Euclidean space has infinities + commutation (forbidden); compact non-flat geometry *supplies* finitude + (anti)commutation. Anti-commutation `{Γ_a,Γ_b}=2δ` at Clifford/spinor levels; noncommutation `[A,B]≠0` at geometric levels. **No Bloch — density-operator/Hilbert/spinor/Clifford only.** Immediate goal: **one layer (Weyl L/R nested on nested Hopf tori) done fully right.**

## What is actually established (by verification status)
- **AUDIT-CONFIRMED GENUINE (the only solid result):** the **mixed nesting-chirality cocycle** — opposite-sign L/R Wilson-plaquette winding across shells, controls collapse to ~1e-17, reproduced by two independent authors. It is the decisive "Weyl *on* nested tori, not glued" invariant. Bar ruling (binding): test it by **presence** (opposite sign + collapsing controls), not full-monopole magnitude ≥0.5 — a finite η-band subtends partial solid angle, so |w|<0.5 is structural.
- **THE KEY OPEN PATTERN — the deflation split:** under grok's deflation control (fix one Hopf base, vary only the spin^c lift), the **substrate/holonomy law DEFLATES** (it's ordinary spin^c geometry, not a stacking DOF) while the **mixed cocycle does NOT** (genuine). The program's real question is now: *which claims survive deflation vs collapse to ordinary single-base geometry?*
- **SELF-REPORTED, PENDING AUDIT (do these first):** 9 codex2 just landed — order-null `survives`, ratchet-survivor `deflated`, Hopfield-basin `deflated`, substrate-band `survives`, cocycle 3rd-section `reproduces`, N=64 carrier `reached`, curvature-frame `unifies`, cocycle full-η monopole `present`, neural-on-manifold `nonflat_changes_network`. Outputs in `/tmp/cx_*.out` + `system_v5/julia_carrier/layers/*_results.json`. **Audit each before trusting.** If `full_monopole_present` + `third_section_reproduces` survive audit, the genuine cocycle becomes a 3-construction global topological charge — a major result.
- **CARRIER:** CTMRG is unreliable on structured tensors — **retired.** Use ITensors-MPS / exact dense / QuantumClifford (Clifford levels) / spinor trajectories (dissipation), each with a **contraction-error certificate (Δ < effect, with a number, equal truncation for genuine and control)**.

## The new standard (what "done right" means)
finite-vs-flat (F01) · (anti)commutation-vs-flat, input-dependent not a fixed identity (N01) · topological invariant + wrong-structure flip control · exact/QuantumClifford carrier with error certificate, never CTMRG · scale ladder 8/16/32/64 · neural/attractor dynamics where applicable (honestly fails on small carriers) · **pre-registered bars set by the controller not the builder** · **mandatory fresh adversarial audit.**

## Immediate next steps
1. Fab-audit the 9 self-reported codex2 verdicts (above). 
2. Resolve the contradiction: `substrate-band survives` vs `holonomy law deflates`. 
3. Build the clean **audited deflation map** (genuine vs deflated per core claim) — the program's honest spine. 
4. Harden the cocycle toward canonical (3 audited sections + full-η monopole + curvature unification). 
5. Re-audit the pre-session "genuine_bf" layers (suspect). 
6. **Fix the corrupt repo git** (`bad tree object HEAD` — blocks provenance/commits).

## The open fork (owner decides)
(A) keep fanning out builds (→ fabrication) vs **(B, recommended)** pivot parallelism to verify-and-harden: audit every verdict, carrier-certificate discipline, harden the genuine few instead of minting fakes.

## Infra
codex2: `CODEX_HOME=~/.codex-second codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check -C <repo> -c model_reasoning_effort=xhigh "<prompt>"` (no sub-agents/sleep/interactive). gemini: `gemini -m gemini-2.5-pro -p "..."`. grok: `XAI_API_KEY` set, curl `https://api.x.ai/v1/chat/completions` model `grok-4` (use it to falsify). Julia `--project=system_v5/julia_carrier`; hard-cap wrapper `julia ... & p=$!; ( sleep N && kill -9 $p ) & wait $p` (no gtimeout on macOS; in-script async timers don't preempt). Env python `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3`, x64 first.

**Start by reading the full state doc, then audit the 9 pending verdicts. Do not trust unaudited self-reports.**
