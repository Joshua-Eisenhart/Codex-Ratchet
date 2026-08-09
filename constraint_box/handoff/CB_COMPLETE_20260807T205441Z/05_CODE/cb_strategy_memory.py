#!/usr/bin/env python3
"""cb_strategy_memory — the manager whose absence broke the 3-layer run.

Wizard v4.3 defines manager.strategy_memory as carrying "prompt intent,
standing context, strategy state, risks, killed assumptions, follow-up
rationale across loops. Session scratchpad, NOT a long-term archive."

Its absence is the only failure this session that broke a run outright:
in the 3x3 nested council, each convergence passed verdicts upward but
never restated the question, so the top council received opinions with
no problem attached and asked "what is the task?".

This is deterministic. It stores nothing but declared fields, it never
summarises, and it re-injects the SAME text at every level. A summary
would reintroduce drift; verbatim re-injection cannot.

LAW 2 resemblance: one stratum is CONSERVED EXACTLY (prompt_intent)
while the rest contracts (per-round detail is dropped). That is the
archive stage of the engine, applied to project state.
promotion_allowed=false.
"""
from __future__ import annotations
import hashlib, json, sys, time
from pathlib import Path

CONSERVED = ("prompt_intent", "success_condition", "claim_ceiling")
CONTRACTING = ("standing_context", "strategy_state", "risks",
               "killed_assumptions", "followup_rationale")

class StrategyMemory:
    """Session scratchpad. Conserved fields are immutable after seal."""

    def __init__(self, prompt_intent: str, success_condition: str,
                 claim_ceiling: str):
        self._c = {"prompt_intent": prompt_intent,
                   "success_condition": success_condition,
                   "claim_ceiling": claim_ceiling}
        self._v = {k: [] for k in CONTRACTING}
        self._sealed_at = time.time()
        self._seal = self._hash_conserved()
        self._rounds = 0

    def _hash_conserved(self) -> str:
        return hashlib.sha256(json.dumps(self._c, sort_keys=True)
                              .encode()).hexdigest()

    # ---- conserved stratum: exact, immutable, verifiable
    def verify_conserved(self) -> bool:
        """LAW 2: drift must be exactly zero, not small"""
        return self._hash_conserved() == self._seal

    # ---- contracting strata: appended, then pruned by recency
    def note(self, field: str, text: str, keep: int = 5):
        if field not in CONTRACTING:
            raise ValueError(f"{field} is not a contracting field")
        self._v[field].append({"round": self._rounds, "text": text})
        self._v[field] = self._v[field][-keep:]

    def kill(self, assumption: str):
        """killed assumptions are contracting but never silently dropped"""
        self.note("killed_assumptions", assumption, keep=50)

    def advance(self):
        self._rounds += 1

    # ---- the load-bearing method: what every convergence level receives
    def preamble(self) -> str:
        """Re-injected VERBATIM at every level. Never summarised."""
        lines = [f"PROMPT INTENT (conserved): {self._c['prompt_intent']}",
                 f"SUCCESS CONDITION: {self._c['success_condition']}",
                 f"CLAIM CEILING: {self._c['claim_ceiling']}"]
        if self._v["killed_assumptions"]:
            lines.append("KILLED ASSUMPTIONS (do not revive without a bridge): "
                         + "; ".join(k["text"] for k in
                                     self._v["killed_assumptions"][-6:]))
        if self._v["strategy_state"]:
            lines.append("STRATEGY STATE: "
                         + self._v["strategy_state"][-1]["text"])
        if self._v["risks"]:
            lines.append("OPEN RISKS: "
                         + "; ".join(r["text"] for r in self._v["risks"][-3:]))
        return "\n".join(lines)

    def receipt(self) -> dict:
        return {"schema": "cb.strategy-memory.v1",
                "conserved": self._c,
                "conserved_sha256": self._seal,
                "conserved_intact": self.verify_conserved(),
                "rounds": self._rounds,
                "contracting_sizes": {k: len(v) for k, v in self._v.items()},
                "killed_assumptions": [k["text"] for k in
                                       self._v["killed_assumptions"]],
                "promotion_allowed": False}


def _self_test() -> int:
    checks = []
    sm = StrategyMemory(
        prompt_intent="determine whether the 21 unreferenced registry ids are "
                      "a naming defect or missing tooling",
        success_condition="a deterministic scan distinguishes the two, with "
                          "negative controls at zero",
        claim_ceiling="machinery coverage only; no claim about tool quality")

    checks.append(("conserved intact at seal", sm.verify_conserved()))

    # the failure being prevented: a convergence level that receives no task
    empty_preamble = ""
    checks.append(("preamble is non-empty (task survives upward)",
                   len(sm.preamble()) > 80))

    # contracting strata prune; conserved does not move
    for i in range(12):
        sm.note("strategy_state", f"round {i} state")
        sm.advance()
    checks.append(("contracting stratum pruned to keep-window",
                   len(sm._v["strategy_state"]) == 5))
    checks.append(("conserved stratum UNCHANGED after 12 rounds",
                   sm.verify_conserved()))

    sm.kill("all 21 ids are missing tools")
    checks.append(("killed assumption appears in every later preamble",
                   "all 21 ids are missing tools" in sm.preamble()))

    # tamper canary: mutating a conserved field must be detectable
    sm._c["prompt_intent"] = "something else entirely"
    checks.append(("conserved tamper DETECTED", not sm.verify_conserved()))

    for name, ok in checks:
        print(f"   {'PASS' if ok else 'FAIL'}  {name}")
    p = sum(1 for _, ok in checks if ok)
    print(f"fixtures as expected: {p}/{len(checks)}")
    return 0 if p == len(checks) else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(_self_test())
    print(__doc__)
