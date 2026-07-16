universe u v w

namespace LeanMicroCoreV0

/-- Two states are indistinguishable when every declared probe gives the same observation. -/
def ProbeIndistinguishable
    {State : Type u} {Probe : Type v} {Observation : Type w}
    (observe : Probe → State → Observation) (a b : State) : Prop :=
  ∀ p, observe p a = observe p b

theorem probeIndistinguishable_refl
    {n m : Nat} {Observation : Type w}
    (observe : Fin m → Fin n → Observation) (a : Fin n) :
    ProbeIndistinguishable observe a a := by
  intro p
  rfl

theorem probeIndistinguishable_symm
    {n m : Nat} {Observation : Type w}
    (observe : Fin m → Fin n → Observation) {a b : Fin n}
    (hab : ProbeIndistinguishable observe a b) :
    ProbeIndistinguishable observe b a := by
  intro p
  exact (hab p).symm

theorem probeIndistinguishable_trans
    {n m : Nat} {Observation : Type w}
    (observe : Fin m → Fin n → Observation) {a b c : Fin n}
    (hab : ProbeIndistinguishable observe a b)
    (hbc : ProbeIndistinguishable observe b c) :
    ProbeIndistinguishable observe a c := by
  intro p
  exact (hab p).trans (hbc p)

/-- Probe indistinguishability is an equivalence relation under the declared probe family. -/
theorem probeIndistinguishable_equivalence
    {n m : Nat} {Observation : Type w}
    (observe : Fin m → Fin n → Observation) :
    Equivalence (ProbeIndistinguishable observe) :=
  ⟨probeIndistinguishable_refl observe,
    probeIndistinguishable_symm observe,
    probeIndistinguishable_trans observe⟩

#print axioms probeIndistinguishable_equivalence

end LeanMicroCoreV0
