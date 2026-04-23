/-
  Shell Nesting Invariant: S₀ ⊇ S₁ ⊇ S₂ ⊇ ...
  If a family is killed at layer k, no layer j > k can revive it.

  Model: constraint layers as predicate transformers (α → Prop) → (α → Prop).
  A "set" is just a predicate. Subset is pointwise implication.
  Zero dependencies — pure Lean 4 core.
-/

-- A constraint layer transforms a predicate (survivor set) to another predicate
def ConstraintLayer (α : Type) := (α → Prop) → (α → Prop)

-- Subset as pointwise implication
def PredSubset {α : Type} (p q : α → Prop) : Prop :=
  ∀ x : α, p x → q x

-- A layer is valid if it only removes elements (output ⊆ input)
def IsValidLayer {α : Type} (f : ConstraintLayer α) : Prop :=
  ∀ s : α → Prop, PredSubset (f s) s

-- Shell nesting: composing valid layers preserves the subset ordering
theorem shell_nesting_preserved {α : Type}
    (f g : ConstraintLayer α)
    (hf : IsValidLayer f) (hg : IsValidLayer g) :
    IsValidLayer (f ∘ g) := by
  intro s x hx
  have h1 : (g s) x := hf (g s) x hx
  exact hg s x h1

-- Irreversibility: once killed at layer f, no valid layer g on top can revive it
theorem once_killed_stays_killed {α : Type}
    (f : ConstraintLayer α)
    (_hf : IsValidLayer f)
    (x : α) (s : α → Prop)
    (hkill : ¬ (f s) x) :
    ∀ g : ConstraintLayer α, IsValidLayer g → ¬ (g (f s)) x := by
  intro g hg hx
  exact hkill (hg (f s) x hx)

-- N-fold composition of valid layers is still valid (by induction on the list)
theorem nfold_valid {α : Type}
    (layers : List (ConstraintLayer α))
    (hall : ∀ f, f ∈ layers → IsValidLayer f) :
    IsValidLayer (layers.foldr (· ∘ ·) id) := by
  induction layers with
  | nil =>
    intro s x hx
    exact hx
  | cons f rest ih =>
    intro s x hx
    simp [List.foldr] at hx
    have hf : IsValidLayer f := hall f (List.mem_cons_self f rest)
    have hrest : ∀ g, g ∈ rest → IsValidLayer g := fun g hg =>
      hall g (List.mem_cons_of_mem f hg)
    have ih_valid := ih hrest
    have h1 : (rest.foldr (· ∘ ·) id) s x := hf _ x hx
    exact ih_valid s x h1
