----------------------------- MODULE ConstraintBox -----------------------------
EXTENDS Naturals, TLC

CONSTANTS Requests, MaxGeneration

States == {
  "RECEIVED", "NORMALIZED", "PROPOSED", "AUTHORIZED",
  "RUNNING", "OBSERVED", "EVALUATED",
  "ELIGIBLE", "PARKED", "BLOCKED", "HOLD"
}

Terminal == {"ELIGIBLE", "PARKED", "BLOCKED", "HOLD"}

VARIABLES state, policyGeneration, runPolicyGeneration, evidence, disposition

vars == <<state, policyGeneration, runPolicyGeneration, evidence, disposition>>

Init ==
  /\ state = "RECEIVED"
  /\ policyGeneration = 0
  /\ runPolicyGeneration = 0
  /\ evidence = {}
  /\ disposition = "NONE"

Normalize ==
  /\ state = "RECEIVED"
  /\ state' = "NORMALIZED"
  /\ UNCHANGED <<policyGeneration, runPolicyGeneration, evidence, disposition>>

Propose ==
  /\ state = "NORMALIZED"
  /\ state' = "PROPOSED"
  /\ UNCHANGED <<policyGeneration, runPolicyGeneration, evidence, disposition>>

Authorize ==
  /\ state = "PROPOSED"
  /\ state' = "AUTHORIZED"
  /\ runPolicyGeneration' = policyGeneration
  /\ UNCHANGED <<policyGeneration, evidence, disposition>>

StartRun ==
  /\ state = "AUTHORIZED"
  /\ state' = "RUNNING"
  /\ UNCHANGED <<policyGeneration, runPolicyGeneration, evidence, disposition>>

Observe ==
  /\ state = "RUNNING"
  /\ state' = "OBSERVED"
  /\ evidence' = {"worker_witness"}
  /\ UNCHANGED <<policyGeneration, runPolicyGeneration, disposition>>

Evaluate ==
  /\ state = "OBSERVED"
  /\ state' = "EVALUATED"
  /\ UNCHANGED <<policyGeneration, runPolicyGeneration, evidence, disposition>>

Settle(d) ==
  /\ state = "EVALUATED"
  /\ d \in Terminal
  /\ state' = d
  /\ disposition' = d
  /\ UNCHANGED <<policyGeneration, runPolicyGeneration, evidence>>

PolicyChange ==
  \* Once authorization captures a generation, a policy change cannot race
  \* between authorization and worker start.
  /\ state \notin {"AUTHORIZED", "RUNNING", "OBSERVED", "EVALUATED"}
  /\ policyGeneration < MaxGeneration
  /\ policyGeneration' = policyGeneration + 1
  /\ UNCHANGED <<state, runPolicyGeneration, evidence, disposition>>

TerminalHold ==
  /\ state \in Terminal
  /\ UNCHANGED vars

Next ==
  \/ Normalize
  \/ Propose
  \/ Authorize
  \/ StartRun
  \/ Observe
  \/ Evaluate
  \/ \E d \in Terminal : Settle(d)
  \/ PolicyChange
  \/ TerminalHold

TypeInvariant ==
  /\ state \in States
  /\ policyGeneration \in Nat
  /\ runPolicyGeneration \in Nat
  /\ disposition \in Terminal \cup {"NONE"}

NoProposalSelfAdmission ==
  state = "PROPOSED" => disposition = "NONE"

EvidenceBeforeEligibility ==
  disposition = "ELIGIBLE" => evidence /= {}

FrozenPolicyDuringRun ==
  state \in {"RUNNING", "OBSERVED", "EVALUATED"}
    => policyGeneration = runPolicyGeneration

Spec == Init /\ [][Next]_vars

=============================================================================
