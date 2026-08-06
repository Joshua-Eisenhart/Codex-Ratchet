----------------------------- MODULE ConstraintBox -----------------------------
EXTENDS Naturals

\* This is a bounded safety model of one abstract completed controller-run
\* state token.  The global policy generation may advance before that run and
\* after terminal settlement.  This model does not establish implementation
\* correspondence, actor identity, evidence provenance or validity, decision
\* semantics, retries, leases, release, concurrency, refinement, or liveness.

CONSTANT
  \* @type: Int;
  MaxGeneration

VARIABLES
  \* @type: Str;
  state,
  \* @type: Int;
  policyGeneration,
  \* @type: Int;
  runPolicyGeneration,
  \* @type: Set(Str);
  evidence,
  \* @type: Str;
  disposition

States == {
  "RECEIVED", "NORMALIZED", "PROPOSED", "AUTHORIZED",
  "RUNNING", "OBSERVED", "EVALUATED",
  "ELIGIBLE", "PARKED", "BLOCKED", "HOLD"
}

Terminal == {"ELIGIBLE", "PARKED", "BLOCKED", "HOLD"}

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
  \* This action is disabled while the abstract run is authorized or active.
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

BasicStateDomains ==
  /\ state \in States
  /\ policyGeneration \in 0..MaxGeneration
  /\ runPolicyGeneration \in 0..MaxGeneration
  /\ evidence \in SUBSET {"worker_witness"}
  /\ disposition \in Terminal \cup {"NONE"}
  /\ state \in Terminal => disposition = state
  /\ state \notin Terminal => disposition = "NONE"

NoDispositionAtProposal ==
  state = "PROPOSED" => disposition = "NONE"

NonemptyEvidenceBeforeEligible ==
  disposition = "ELIGIBLE" => evidence /= {}

CapturedGenerationMatchesDuringRun ==
  state \in {"AUTHORIZED", "RUNNING", "OBSERVED", "EVALUATED"}
    => policyGeneration = runPolicyGeneration

Spec == Init /\ [][Next]_vars

=============================================================================
