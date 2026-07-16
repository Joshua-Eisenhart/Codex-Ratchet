import Mathlib.Analysis.Complex.Basic
import Mathlib.Data.Matrix.Reflection
import Mathlib.Tactic

namespace LeanMicroCoreV0

open Complex Matrix

abbrev PauliMatrix := Matrix (Fin 2) (Fin 2) ℂ

def sigmaX : PauliMatrix := !![0, 1; 1, 0]
def sigmaY : PauliMatrix := !![0, -I; I, 0]
def sigmaZ : PauliMatrix := !![1, 0; 0, -1]

def commutator (A B : PauliMatrix) : PauliMatrix := A * B - B * A

macro "pauli_expand" : tactic =>
  `(tactic| (ext i j
             fin_cases i <;> fin_cases j
             <;> simp [commutator, sigmaX, sigmaY, sigmaZ, Matrix.mul_apply,
                       Complex.ext_iff]
             <;> ring))

theorem pauli_xy_commutator :
    commutator sigmaX sigmaY = ((2 : ℂ) * I) • sigmaZ := by
  pauli_expand

theorem pauli_yz_commutator :
    commutator sigmaY sigmaZ = ((2 : ℂ) * I) • sigmaX := by
  pauli_expand

theorem pauli_zx_commutator :
    commutator sigmaZ sigmaX = ((2 : ℂ) * I) • sigmaY := by
  pauli_expand

#print axioms pauli_xy_commutator
#print axioms pauli_yz_commutator
#print axioms pauli_zx_commutator

end LeanMicroCoreV0
