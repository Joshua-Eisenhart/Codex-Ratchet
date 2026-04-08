/-
  Entropy Monotonicity & Cardinality Bounds

  Extends ShellNesting.lean with quantitative results:
  1. Cardinality is nonincreasing under valid constraint layers
  2. Kill layers strictly decrease cardinality
  3. Repeated application on a finite domain reaches a fixed point

  Model: We define cardinality by recursive counting over `Fin n`.
  No Mathlib — pure Lean 4 core.

  Depends on: ShellNesting.lean for ConstraintLayer, IsValidLayer, PredSubset
-/
import RatchetProofs.ShellNesting

-- ============================================================
-- Section 1: Cardinality on Fin n by recursion
-- ============================================================

/-- Count how many elements of `Fin n` satisfy a Bool predicate. -/
def predCard : (n : Nat) → (p : Fin n → Bool) → Nat
  | 0, _ => 0
  | k + 1, p =>
    let rest := predCard k (fun (i : Fin k) => p (Fin.castSucc i))
    if p ⟨k, Nat.lt_succ_of_le (Nat.le_refl k)⟩ then rest + 1 else rest

/-- predCard is bounded by n. -/
theorem predCard_le_n (n : Nat) (p : Fin n → Bool) :
    predCard n p ≤ n := by
  induction n with
  | zero => simp [predCard]
  | succ k ih =>
    simp only [predCard]
    have := ih (fun i => p (Fin.castSucc i))
    split <;> omega

/-- Monotonicity for Bool predicates: if p implies q pointwise, predCard p ≤ predCard q. -/
theorem predCard_mono (n : Nat)
    (p q : Fin n → Bool)
    (h : ∀ x : Fin n, p x = true → q x = true) :
    predCard n p ≤ predCard n q := by
  induction n with
  | zero => simp [predCard]
  | succ k ih =>
    simp only [predCard]
    have ih_applied := ih
      (fun i => p (Fin.castSucc i))
      (fun i => q (Fin.castSucc i))
      (fun i hi => h (Fin.castSucc i) hi)
    split
    · rename_i hp
      have hq : q ⟨k, _⟩ = true := h _ hp
      simp [hq]; omega
    · split
      · omega
      · exact ih_applied

-- ============================================================
-- Section 2: Cardinality nonincreasing
-- ============================================================

/-- Turn a decidable Prop-predicate into Bool for counting. -/
abbrev boolOf {n : Nat} (p : Fin n → Prop) [DecidablePred p] : Fin n → Bool :=
  fun i => decide (p i)

/-- A valid constraint layer on `Fin n` can only decrease or maintain cardinality. -/
theorem cardinality_nonincreasing {n : Nat}
    (f : ConstraintLayer (Fin n))
    (hf : IsValidLayer f)
    (s : Fin n → Prop) [DecidablePred s] [DecidablePred (f s)] :
    predCard n (boolOf (f s)) ≤ predCard n (boolOf s) := by
  apply predCard_mono
  intro x hx
  simp [boolOf, decide_eq_true_eq] at *
  exact hf s x hx

-- ============================================================
-- Section 3: Strict decrease at kill layers
-- ============================================================

/-- Strict monotonicity for Bool predicates. -/
theorem predCard_strict (n : Nat)
    (p q : Fin n → Bool)
    (himp : ∀ x : Fin n, q x = true → p x = true)
    (x : Fin n) (hp : p x = true) (hnq : q x = false) :
    predCard n q < predCard n p := by
  induction n with
  | zero => exact absurd x.isLt (Nat.not_lt_zero _)
  | succ k ih =>
    simp only [predCard]
    by_cases hx : x.val = k
    · -- x is the last element
      have hxeq : x = ⟨k, Nat.lt_succ_of_le (Nat.le_refl k)⟩ := Fin.ext hx
      have hp_last : p ⟨k, _⟩ = true := hxeq ▸ hp
      have hnq_last : q ⟨k, _⟩ = false := hxeq ▸ hnq
      rw [hp_last, hnq_last]; simp
      exact Nat.lt_succ_of_le (predCard_mono k _ _ (fun i hi => himp (Fin.castSucc i) hi))
    · -- x is not the last element
      have hxlt : x.val < k := by have := x.isLt; omega
      let x' : Fin k := ⟨x.val, hxlt⟩
      have hx_eq : Fin.castSucc x' = x := Fin.ext (by simp [Fin.castSucc, x'])
      have hp' : (fun i => p (Fin.castSucc i)) x' = true := by
        show p (Fin.castSucc x') = true; rw [hx_eq]; exact hp
      have hnq' : (fun i => q (Fin.castSucc i)) x' = false := by
        show q (Fin.castSucc x') = false; rw [hx_eq]; exact hnq
      have ih_applied := ih
        (fun i => p (Fin.castSucc i))
        (fun i => q (Fin.castSucc i))
        (fun i hi => himp (Fin.castSucc i) hi)
        x' hp' hnq'
      split <;> split
      · omega
      · rename_i hql _; exact absurd (himp _ hql) (by simp_all)
      · omega
      · omega

/-- Strict decrease: if layer `f` kills element `x` from set `s`, cardinality drops. -/
theorem strict_decrease_at_kill {n : Nat}
    (f : ConstraintLayer (Fin n))
    (hf : IsValidLayer f)
    (s : Fin n → Prop) [DecidablePred s] [DecidablePred (f s)]
    (x : Fin n) (hx : s x) (hkill : ¬ (f s) x) :
    predCard n (boolOf (f s)) < predCard n (boolOf s) := by
  apply predCard_strict
  · intro y hy; simp [boolOf, decide_eq_true_eq] at *; exact hf s y hy
  · simp [boolOf, decide_eq_true_eq]; exact hx
  · simp [boolOf, decide_eq_false_iff_not]; exact hkill

-- ============================================================
-- Section 4: Fixed-point theorem
-- ============================================================

/-- Apply a constraint layer `k` times. -/
def iterLayer {α : Type} (f : ConstraintLayer α) : Nat → ConstraintLayer α
  | 0 => id
  | k + 1 => f ∘ (iterLayer f k)

/-- A nonincreasing Nat sequence bounded by `bound` stabilizes within `bound` steps. -/
theorem nat_seq_stabilizes (seq : Nat → Nat) (bound : Nat)
    (hbound : ∀ k, seq k ≤ bound)
    (hmono : ∀ k, seq (k + 1) ≤ seq k) :
    ∃ N, seq (N + 1) = seq N := by
  induction bound generalizing seq with
  | zero =>
    refine ⟨0, ?_⟩
    have h0 : seq 0 = 0 := Nat.le_zero.mp (hbound 0)
    have h1 : seq 1 = 0 := Nat.le_zero.mp (hbound 1)
    rw [h0, h1]
  | succ b ih =>
    by_cases h0 : seq 1 = seq 0
    · exact ⟨0, h0⟩
    · -- seq 1 < seq 0, so the shifted sequence is bounded by b
      have hmono0 : seq 1 ≤ seq 0 := hmono 0
      have hlt : seq 1 < seq 0 := Nat.lt_of_le_of_ne hmono0 h0
      have hshift_bound : ∀ k, (fun i => seq (i + 1)) k ≤ b := by
        intro k
        simp only []
        have hle_1 : seq (k + 1) ≤ seq 1 := by
          induction k with
          | zero => exact Nat.le_refl _
          | succ m ihm => exact Nat.le_trans (hmono (m + 1)) ihm
        have hle_b : seq 1 ≤ b := by
          have := hbound 0; omega
        exact Nat.le_trans hle_1 hle_b
      have hshift_mono : ∀ k, (fun i => seq (i + 1)) (k + 1) ≤ (fun i => seq (i + 1)) k :=
        fun k => hmono (k + 1)
      have ⟨N, hN⟩ := ih (fun i => seq (i + 1)) hshift_bound hshift_mono
      exact ⟨N + 1, hN⟩

/-- Fixed-point theorem: iterating a valid layer on `Fin n` eventually stabilizes
    in cardinality. -/
theorem fixed_point_cardinality {n : Nat}
    (f : ConstraintLayer (Fin n))
    (hf : IsValidLayer f)
    (s : Fin n → Prop) [DecidablePred s]
    [diter : ∀ k, DecidablePred ((iterLayer f k) s)] :
    ∃ N, predCard n (boolOf (iterLayer f (N + 1) s)) =
         predCard n (boolOf (iterLayer f N s)) := by
  apply nat_seq_stabilizes (fun k => predCard n (boolOf (iterLayer f k s))) n
  · intro k; exact predCard_le_n n _
  · intro k
    apply predCard_mono
    intro x hx
    simp [boolOf, decide_eq_true_eq] at *
    exact hf _ x hx

-- ============================================================
-- Section 5: Entropy monotonicity (chain of layers)
-- ============================================================

/-- Entropy monotonicity: applying a chain of valid layers
    can only decrease or maintain cardinality. -/
theorem entropy_monotone_chain {n : Nat}
    (layers : List (ConstraintLayer (Fin n)))
    (hall : ∀ f, f ∈ layers → IsValidLayer f)
    (s : Fin n → Prop) [DecidablePred s]
    [DecidablePred ((layers.foldr (· ∘ ·) id) s)] :
    predCard n (boolOf ((layers.foldr (· ∘ ·) id) s)) ≤ predCard n (boolOf s) := by
  apply predCard_mono
  intro x hx
  simp [boolOf, decide_eq_true_eq] at *
  exact nfold_valid layers hall s x hx
