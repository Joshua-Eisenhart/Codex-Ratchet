# Bounded exact-rational ALCO oracle for the local J3(O) convention.

SetUserPreference("UseColor", false);;

if LoadPackage("ResClasses") <> true then
    Error("ResClasses did not load");
fi;
if LoadPackage("ALCO") <> true then
    Error("ALCO did not load");
fi;

O := OctonionAlgebra(Rationals);;
OBasis := Basis(O);;
J := AlbertAlgebra(Rationals);;

BoolString := function(value)
    if value then
        return "true";
    fi;
    return "false";
end;;

PrintRatLine := function(label, values)
    Print(label, "|", JoinStringsWithSeparator(List(values, String), ","), "\n");
end;;

# Local basis [1,e1,...,e7] to ALCO basis [e1,...,e7,e8=1].
# The one-sign permutation is an octonion isomorphism for the local Fano cycles.
LocalOctToAlco := function(values)
    local coeffs;
    coeffs := [
        values[4], values[2], values[5], values[3],
        values[6], -values[7], values[8], values[1]
    ];
    return LinearCombination(OBasis, coeffs);
end;;

AlcoOctToLocal := function(value)
    local coeffs;
    coeffs := Coefficients(OBasis, value);
    return [
        coeffs[8], coeffs[2], coeffs[4], coeffs[1],
        coeffs[3], coeffs[5], -coeffs[6], coeffs[7]
    ];
end;;

LocalCoordinatesToAlbert := function(values)
    local x01, x02, x12, mat, one;
    one := One(O);
    x01 := LocalOctToAlco(values{[4..11]});
    x02 := LocalOctToAlco(values{[12..19]});
    x12 := LocalOctToAlco(values{[20..27]});
    mat := [
        [values[1] * one, x01, x02],
        [ComplexConjugate(x01), values[2] * one, x12],
        [ComplexConjugate(x02), ComplexConjugate(x12), values[3] * one]
    ];
    return HermitianMatrixToAlbertVector(mat);
end;;

AlbertToLocalCoordinates := function(value)
    local mat;
    mat := AlbertVectorToHermitianMatrix(value);
    return Concatenation(
        [Trace(mat[1][1]) / 2, Trace(mat[2][2]) / 2, Trace(mat[3][3]) / 2],
        AlcoOctToLocal(mat[1][2]),
        AlcoOctToLocal(mat[1][3]),
        AlcoOctToLocal(mat[2][3])
    );
end;;

UnitVector := function(length, position)
    local values;
    values := List([1..length], ignored -> 0);
    values[position] := 1;
    return values;
end;;

MapRoundtripPass := ForAll([1..27], position ->
    AlbertToLocalCoordinates(LocalCoordinatesToAlbert(UnitVector(27, position))) =
        UnitVector(27, position)
);;

LocalFanoCycles := [
    [1,2,3], [1,4,5], [1,7,6], [2,4,6],
    [2,5,7], [3,4,7], [3,6,5]
];;
OctonionMapFanoPass := ForAll(LocalFanoCycles, cycle ->
    AlcoOctToLocal(
        LocalOctToAlco(UnitVector(8, cycle[1] + 1)) *
        LocalOctToAlco(UnitVector(8, cycle[2] + 1))
    ) = UnitVector(8, cycle[3] + 1)
);;

NextState := function(rng)
    rng.state := (1103515245 * rng.state + 12345) mod 2147483648;
    return rng.state;
end;;

NextRational := function(rng)
    local numerator, denominator, denominators;
    denominators := [1,2,3,5,7];
    numerator := (NextState(rng) mod 9) - 4;
    denominator := denominators[(NextState(rng) mod 5) + 1];
    return numerator / denominator;
end;;

SeededVector := function(rng)
    return List([1..27], ignored -> NextRational(rng));
end;;

EmitCase := function(label, seed, xValues, yValues, zValues)
    local x, y, z, product, uxY, uyX, mpX, mpY, fundamentalLeft,
          fundamentalRight;
    x := LocalCoordinatesToAlbert(xValues);
    y := LocalCoordinatesToAlbert(yValues);
    z := LocalCoordinatesToAlbert(zValues);
    product := x * y;
    uxY := JordanQuadraticOperator(x, y);
    uyX := JordanQuadraticOperator(y, x);
    mpX := GenericMinimalPolynomial(x);
    mpY := GenericMinimalPolynomial(y);
    fundamentalLeft := JordanQuadraticOperator(uxY, z);
    fundamentalRight := JordanQuadraticOperator(
        x,
        JordanQuadraticOperator(y, JordanQuadraticOperator(x, z))
    );

    Print("CASE|", label, "|", seed, "\n");
    PrintRatLine("X", xValues);
    PrintRatLine("Y", yValues);
    PrintRatLine("Z", zValues);
    PrintRatLine("PRODUCT", AlbertToLocalCoordinates(product));
    PrintRatLine("U_X_Y", AlbertToLocalCoordinates(uxY));
    PrintRatLine("U_Y_X", AlbertToLocalCoordinates(uyX));
    PrintRatLine("MINPOLY_X", mpX);
    PrintRatLine("MINPOLY_Y", mpY);
    Print("TRACE_X|", Trace(x), "\n");
    Print("TRACE_Y|", Trace(y), "\n");
    Print("TRACE_U_X_Y|", Trace(uxY), "\n");
    Print("DET_X|", Determinant(x), "\n");
    Print("DET_Y|", Determinant(y), "\n");
    Print("DET_U_X_Y|", Determinant(uxY), "\n");
    Print("CAYLEY_HAMILTON_X|", BoolString(ValuePol(mpX, x) = Zero(J)), "\n");
    Print("CAYLEY_HAMILTON_Y|", BoolString(ValuePol(mpY, y) = Zero(J)), "\n");
    Print("U_UNIT_IDENTITY|", BoolString(JordanQuadraticOperator(x, One(J)) = x^2), "\n");
    Print("U_HOMOGENEITY|", BoolString(JordanQuadraticOperator(2*x, y) = 4*uxY), "\n");
    Print("U_DETERMINANT_IDENTITY|", BoolString(Determinant(uxY) = Determinant(x)^2 * Determinant(y)), "\n");
    Print("FUNDAMENTAL_FORMULA|", BoolString(fundamentalLeft = fundamentalRight), "\n");
    Print("ENDCASE\n");
end;;

Print("ALCO_ORACLE_V1\n");
Print("META|gap_version|", GAPInfo.Version, "\n");
Print("META|alco_version|", PackageInfo("ALCO")[1].Version, "\n");
Print("META|resclasses_version|", PackageInfo("ResClasses")[1].Version, "\n");
Print("META|field|Rationals\n");
Print("META|albert_dimension|", Dimension(J), "\n");
Print("META|albert_rank|", JordanRank(J), "\n");
Print("META|albert_degree|", JordanDegree(J), "\n");
Print("META|coordinate_roundtrip_pass|", BoolString(MapRoundtripPass), "\n");
Print("META|octonion_map_fano_pass|", BoolString(OctonionMapFanoPass), "\n");
Print("BOUNDARY|simple_eja_4_8_is_fail|", BoolString(SimpleEuclideanJordanAlgebra(4,8) = fail), "\n");
Print("MAP|local_imaginary_to_alco|e1:e2,e2:e4,e3:e1,e4:e3,e5:e5,e6:-e6,e7:e7\n");

for seed in [7,29,101,20260709] do
    rng := rec(state := seed);
    EmitCase(Concatenation("seed_", String(seed)), seed,
        SeededVector(rng), SeededVector(rng), SeededVector(rng));
od;

killX := List([1..27], ignored -> 0);;
killY := List([1..27], ignored -> 0);;
killZ := List([1..27], ignored -> 0);;
killX[5] := 1;;
killY[22] := 1;;
killZ[1] := 1;;
EmitCase("kill_fano_e1_e2", -1, killX, killY, killZ);

Print("END_ORACLE\n");
QUIT_GAP(0);
