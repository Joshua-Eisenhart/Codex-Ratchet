-------------------------- MODULE ClaimGateChain --------------------------
(***************************************************************************)
(* The ClaimGate fired chain, as a state machine.                          *)
(*                                                                         *)
(* WHAT THIS VERIFIES, AND WHAT IT DOES NOT.                               *)
(*                                                                         *)
(* It does NOT verify any scientific claim. A model checker cannot tell you *)
(* whether a spec faithfully describes reality, and an LLM can always write *)
(* a spec that is trivially true. That objection is correct and it is why   *)
(* this module deliberately targets something else:                        *)
(*                                                                         *)
(*   the gate's OWN control flow, which is code we control and can compare  *)
(*   line-by-line against claimgate_plugin/hooks/post_receipt_gate.sh.      *)
(*                                                                         *)
(* The property worth proving is the "skip the gate" move from the          *)
(* four-move threat model: is there ANY reachable path that reaches         *)
(* admission while a required check did not pass? TLC (or the exhaustive    *)
(* BMC in chain_bmc_z3.py) answers that over ALL paths, which no test suite  *)
(* does.                                                                    *)
(*                                                                         *)
(* Mirrors post_receipt_gate.sh exactly, including the two subtleties:      *)
(*   - the seal fails CLOSED on ANY nonzero (1 = rejected, 2 = tooling      *)
(*     error) and both collapse to BLOCK;                                   *)
(*   - claim_verify exit 3 (INSUFFICIENT_DEPTH) is NOT a rejection: the     *)
(*     chain CONTINUES to the floor stage. That continuing path is the one  *)
(*     most worth attacking.                                                *)
(***************************************************************************)
EXTENDS Naturals

CONSTANTS
    \* When TRUE, the corresponding guard is ERASED. Erasing a guard must
    \* make a counterexample appear; if it does not, the guard is decorative.
    EraseIntakeGuard,
    EraseTier0Guard,
    EraseSealGuard,
    EraseVerifyGuard

VARIABLES
    stage,          \* which chain step is next
    intakeOk,       \* intake_supervisor exited 0
    tier0Ok,        \* claimgate.mjs lint-receipt exited 0
    sealOk,         \* three_engine_seal.py exited 0
    verifyCode,     \* claim_verify.py: 0 VERIFIED | 1 REJECTED | 2 IO | 3 DEPTH
    disposition     \* "none" | "ADMIT" | "PARK" | "BLOCK"

vars == <<stage, intakeOk, tier0Ok, sealOk, verifyCode, disposition>>

Stages == {"intake", "tier0", "seal", "verify", "floor", "done"}
Dispositions == {"none", "ADMIT", "PARK", "BLOCK"}

TypeOK ==
    /\ stage \in Stages
    /\ intakeOk \in BOOLEAN
    /\ tier0Ok \in BOOLEAN
    /\ sealOk \in BOOLEAN
    /\ verifyCode \in {0, 1, 2, 3}
    /\ disposition \in Dispositions

Init ==
    /\ stage = "intake"
    /\ intakeOk = FALSE
    /\ tier0Ok = FALSE
    /\ sealOk = FALSE
    /\ verifyCode = 0
    /\ disposition = "none"

(***************************************************************************)
(* Each step is nondeterministic in its OUTCOME (the checker may pass or    *)
(* fail) but deterministic in its CONTROL FLOW (what the shell then does).  *)
(***************************************************************************)

Intake ==
    /\ stage = "intake"
    /\ \E ok \in BOOLEAN :
        /\ intakeOk' = ok
        /\ IF ok \/ EraseIntakeGuard
           THEN /\ stage' = "tier0"
                /\ disposition' = "none"
           ELSE /\ stage' = "done"
                /\ disposition' = "BLOCK"
    /\ UNCHANGED <<tier0Ok, sealOk, verifyCode>>

Tier0 ==
    /\ stage = "tier0"
    /\ \E ok \in BOOLEAN :
        /\ tier0Ok' = ok
        /\ IF ok \/ EraseTier0Guard
           THEN /\ stage' = "seal"
                /\ disposition' = "none"
           ELSE /\ stage' = "done"
                /\ disposition' = "BLOCK"
    /\ UNCHANGED <<intakeOk, sealOk, verifyCode>>

\* Fails CLOSED on ANY nonzero: exit 1 (rejected) and exit 2 (tooling error)
\* both become BLOCK. A tooling error must never become an admission.
Seal ==
    /\ stage = "seal"
    /\ \E ok \in BOOLEAN :
        /\ sealOk' = ok
        /\ IF ok \/ EraseSealGuard
           THEN /\ stage' = "verify"
                /\ disposition' = "none"
           ELSE /\ stage' = "done"
                /\ disposition' = "BLOCK"
    /\ UNCHANGED <<intakeOk, tier0Ok, verifyCode>>

\* exit 0 -> floor; exit 3 (INSUFFICIENT_DEPTH) -> ALSO floor, not a rejection;
\* exit 1 or 2 -> BLOCK.
Verify ==
    /\ stage = "verify"
    /\ \E c \in {0, 1, 2, 3} :
        /\ verifyCode' = c
        /\ IF c = 0 \/ c = 3 \/ EraseVerifyGuard
           THEN /\ stage' = "floor"
                /\ disposition' = "none"
           ELSE /\ stage' = "done"
                /\ disposition' = "BLOCK"
    /\ UNCHANGED <<intakeOk, tier0Ok, sealOk>>

\* Terminal. Depth-pending parks; a fully clean chain admits.
Floor ==
    /\ stage = "floor"
    /\ stage' = "done"
    /\ IF verifyCode = 3
       THEN disposition' = "PARK"
       ELSE disposition' = "ADMIT"
    /\ UNCHANGED <<intakeOk, tier0Ok, sealOk, verifyCode>>

Done == stage = "done" /\ UNCHANGED vars

Next == Intake \/ Tier0 \/ Seal \/ Verify \/ Floor \/ Done

Spec == Init /\ [][Next]_vars

(***************************************************************************)
(* SAFETY PROPERTIES -- the things actually worth proving.                  *)
(***************************************************************************)

\* THE central property: admission requires every upstream check to have passed.
NoAdmitWithoutAllChecks ==
    (disposition = "ADMIT") => (intakeOk /\ tier0Ok /\ sealOk /\ verifyCode = 0)

\* A depth-pending run must PARK, never ADMIT. This is the path that keeps
\* going despite a nonzero exit, so it is the one most worth attacking.
DepthPendingNeverAdmits ==
    (verifyCode = 3) => (disposition # "ADMIT")

\* Fail-closed: a seal tooling error is still a block, never an admission.
SealFailsClosed ==
    (~sealOk /\ stage = "done") => (disposition # "ADMIT")

\* No terminal state without a disposition -- nothing exits silently.
NoSilentExit ==
    (stage = "done") => (disposition # "none")

=============================================================================
