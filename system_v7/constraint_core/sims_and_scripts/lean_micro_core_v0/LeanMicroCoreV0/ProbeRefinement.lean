import LeanMicroCoreV0.ProbeIndistinguishability

universe w

namespace LeanMicroCoreV0

/-- A finite family of probes on a finite state type. -/
structure ProbeFamily (stateCount : Nat) (Observation : Type w) where
  probeCount : Nat
  observe : Fin probeCount → Fin stateCount → Observation

namespace ProbeFamily

def indistinguishable
    {stateCount : Nat} {Observation : Type w}
    (family : ProbeFamily stateCount Observation)
    (a b : Fin stateCount) : Prop :=
  ProbeIndistinguishable family.observe a b

/-- `fine` refines `coarse` when fine-indistinguishability implies coarse-indistinguishability. -/
def Refines
    {stateCount : Nat} {Observation : Type w}
    (coarse fine : ProbeFamily stateCount Observation) : Prop :=
  ∀ a b, fine.indistinguishable a b → coarse.indistinguishable a b

theorem refines_refl
    {stateCount : Nat} {Observation : Type w}
    (family : ProbeFamily stateCount Observation) :
    Refines family family := by
  intro a b hab
  exact hab

theorem refines_trans
    {stateCount : Nat} {Observation : Type w}
    {coarse middle fine : ProbeFamily stateCount Observation}
    (hcm : Refines coarse middle) (hmf : Refines middle fine) :
    Refines coarse fine := by
  intro a b hab
  exact hcm a b (hmf a b hab)

/-- Probe-family refinement satisfies the two preorder laws: reflexivity and transitivity. -/
theorem probeFamilyRefinement_isPreorder
    {stateCount : Nat} {Observation : Type w} :
    (∀ family : ProbeFamily stateCount Observation, Refines family family) ∧
      (∀ coarse middle fine : ProbeFamily stateCount Observation,
        Refines coarse middle → Refines middle fine → Refines coarse fine) :=
  ⟨refines_refl, fun _ _ _ hcm hmf => refines_trans hcm hmf⟩

#print axioms probeFamilyRefinement_isPreorder

end ProbeFamily
end LeanMicroCoreV0
