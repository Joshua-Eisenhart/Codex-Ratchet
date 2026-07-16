import Mathlib.Analysis.Complex.Basic
import Mathlib.Data.Matrix.Reflection

namespace LeanMicroCoreV0

open Complex Matrix

abbrev ComplexMatrix2 := Matrix (Fin 2) (Fin 2) ℂ

def associatorA : ComplexMatrix2 := !![1, 2; 0, -1]
def associatorB : ComplexMatrix2 := !![I, 1; 3, 0]
def associatorC : ComplexMatrix2 := !![0, -I; 1, 2]

/-- Concrete associative control: the associator of three named complex 2x2 matrices vanishes. -/
theorem concrete_matrix_associator_vanishes :
    (associatorA * associatorB) * associatorC -
        associatorA * (associatorB * associatorC) = 0 := by
  rw [mul_assoc, sub_self]

#print axioms concrete_matrix_associator_vanishes

end LeanMicroCoreV0
