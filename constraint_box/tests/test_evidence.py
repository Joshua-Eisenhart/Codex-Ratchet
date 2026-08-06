from __future__ import annotations

import dataclasses
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from constraintbox.evidence import (
    DigestRoute,
    EvidenceError,
    EvidenceRef,
    FileRoute,
    RefKind,
    RequiredReferenceManifest,
    RunSeal,
    SealFailedClosed,
    SealVerdict,
    build_required_manifest,
    observe,
    ref_from_dict,
    required_manifest_from_dict,
    route_table,
    seal_from_dict,
    seal_run,
    verify_seal,
)


def public_digest(body: object) -> str:
    encoded = json.dumps(
        body,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class EvidenceRefTests(unittest.TestCase):
    def test_fresh_ref_carries_no_observation(self) -> None:
        ref = EvidenceRef(kind=RefKind.RECEIPT, ref="a/b.json", route="file")
        self.assertIsNone(ref.exists)
        self.assertIsNone(ref.observed_sha256)
        self.assertIsNone(ref.observed_at_utc)
        self.assertFalse(ref.observed)

    def test_caller_cannot_assert_exists(self) -> None:
        with self.assertRaises(TypeError):
            EvidenceRef(  # type: ignore[call-arg]
                kind=RefKind.RECEIPT, ref="a/b.json", route="file", exists=True
            )

    def test_caller_cannot_assert_observed_digest(self) -> None:
        with self.assertRaises(TypeError):
            EvidenceRef(  # type: ignore[call-arg]
                kind=RefKind.RECEIPT,
                ref="a/b.json",
                route="file",
                observed_sha256="0" * 64,
            )

    def test_exists_cannot_be_written_after_construction(self) -> None:
        ref = EvidenceRef(kind=RefKind.RECEIPT, ref="a/b.json", route="file")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            ref.exists = True  # type: ignore[misc]

    def test_kind_must_be_a_ref_kind(self) -> None:
        with self.assertRaises(EvidenceError):
            EvidenceRef(kind="receipt", ref="a/b.json", route="file")  # type: ignore[arg-type]

    def test_empty_locator_rejected(self) -> None:
        with self.assertRaises(EvidenceError):
            EvidenceRef(kind=RefKind.RECEIPT, ref="   ", route="file")

    def test_empty_route_rejected(self) -> None:
        with self.assertRaises(EvidenceError):
            EvidenceRef(kind=RefKind.RECEIPT, ref="a/b.json", route="")


class RequiredReferenceManifestTests(unittest.TestCase):
    def ref(self, name: str = "a/b.json") -> EvidenceRef:
        return EvidenceRef(kind=RefKind.RECEIPT, ref=name, route="file")

    def test_manifest_is_content_bound_and_round_trips_strictly(self) -> None:
        manifest = build_required_manifest("required-run-1", [self.ref()])
        self.assertIs(type(manifest), RequiredReferenceManifest)
        self.assertEqual(
            manifest.schema,
            "constraintbox.required-reference-manifest.v1",
        )
        self.assertEqual(
            required_manifest_from_dict(
                json.loads(json.dumps(manifest.to_dict()))
            ),
            manifest,
        )

    def test_manifest_rejects_zero_or_duplicate_references(self) -> None:
        with self.assertRaises(EvidenceError):
            build_required_manifest("required-run-1", [])
        with self.assertRaises(EvidenceError):
            build_required_manifest(
                "required-run-1",
                [self.ref(), self.ref()],
            )

    def test_manifest_rejects_observed_or_value_carrying_references(self) -> None:
        observed = ref_from_dict(
            {
                "kind": "receipt",
                "ref": "a/b.json",
                "route": "file",
                "exists": True,
                "observed_sha256": "0" * 64,
                "observed_at_utc": "2026-07-26T12:00:00+00:00",
            }
        )
        with self.assertRaises(EvidenceError):
            build_required_manifest("required-run-1", [observed])

        @dataclasses.dataclass(frozen=True)
        class VerdictCarryingRef(EvidenceRef):
            verdict: str = "PASS"

        with self.assertRaises(EvidenceError):
            build_required_manifest(
                "required-run-1",
                [
                    VerdictCarryingRef(
                        kind=RefKind.RECEIPT,
                        ref="a/b.json",
                        route="file",
                    )
                ],
            )

    def test_manifest_parser_rejects_unknown_fields_and_bad_digest(self) -> None:
        manifest = build_required_manifest("required-run-1", [self.ref()])
        extra = manifest.to_dict()
        extra["verdict"] = "PASS"
        with self.assertRaises(EvidenceError):
            required_manifest_from_dict(extra)

        bad_digest = manifest.to_dict()
        bad_digest["manifest_sha256"] = "0" * 64
        with self.assertRaises(EvidenceError):
            required_manifest_from_dict(bad_digest)


class RouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_file_route_rejects_absolute_and_traversal(self) -> None:
        route = FileRoute(self.root)
        with self.assertRaises(EvidenceError):
            route.locate("/etc/passwd")
        with self.assertRaises(EvidenceError):
            route.locate("../outside.json")

    def test_digest_route_rejects_non_digest(self) -> None:
        route = DigestRoute(self.root)
        with self.assertRaises(EvidenceError):
            route.locate("PASS")
        with self.assertRaises(EvidenceError):
            route.locate("A" * 64)

    def test_route_table_rejects_duplicates(self) -> None:
        with self.assertRaises(EvidenceError):
            route_table(FileRoute(self.root), FileRoute(self.root))


class ObservationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.routes = route_table(FileRoute(self.root))
        self.now = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write(self, name: str, text: str) -> str:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return text

    def test_observation_records_existence_and_digest(self) -> None:
        text = self.write("legs/solver_a.json", '{"leg": "solver_a"}')
        ref = EvidenceRef(kind=RefKind.RECEIPT, ref="legs/solver_a.json", route="file")
        seen = observe(ref, self.routes, now=self.now)
        self.assertTrue(seen.exists)
        self.assertEqual(
            seen.observed_sha256, hashlib.sha256(text.encode("utf-8")).hexdigest()
        )
        self.assertEqual(seen.observed_at_utc, self.now.isoformat())
        self.assertIsNone(ref.exists)

    def test_observation_records_absence(self) -> None:
        ref = EvidenceRef(kind=RefKind.RECEIPT, ref="legs/gone.json", route="file")
        seen = observe(ref, self.routes, now=self.now)
        self.assertFalse(seen.exists)
        self.assertIsNone(seen.observed_sha256)

    def test_unregistered_route_raises(self) -> None:
        ref = EvidenceRef(kind=RefKind.RECEIPT, ref="legs/solver_a.json", route="smtp")
        with self.assertRaises(EvidenceError):
            observe(ref, self.routes, now=self.now)

    def test_content_addressed_blob_must_hash_to_its_name(self) -> None:
        store = self.root / "cas"
        store.mkdir()
        name = "b" * 64
        (store / name).write_text("not the named content", encoding="utf-8")
        routes = route_table(DigestRoute(store))
        ref = EvidenceRef(kind=RefKind.ARTIFACT, ref=name, route="digest")
        with self.assertRaises(EvidenceError):
            observe(ref, routes, now=self.now)


class SealTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.routes = route_table(FileRoute(self.root))
        self.now = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)
        self.target = self.root / "legs" / "solver_a.json"
        self.target.parent.mkdir(parents=True, exist_ok=True)
        self.target.write_text(
            json.dumps({"leg": "solver_a", "verdict": "PASS"}), encoding="utf-8"
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def ref(self, locator: str = "legs/solver_a.json") -> EvidenceRef:
        return EvidenceRef(kind=RefKind.RECEIPT, ref=locator, route="file")

    def manifest(
        self,
        *refs: EvidenceRef,
        manifest_id: str = "required-run-1",
    ) -> RequiredReferenceManifest:
        return build_required_manifest(
            manifest_id,
            list(refs) if refs else [self.ref()],
        )

    def seal(self) -> RunSeal:
        return seal_run("run-1", self.manifest(), self.routes, now=self.now)

    def test_seal_records_what_it_observed(self) -> None:
        seal = self.seal()
        self.assertEqual(seal.schema, "constraintbox.run-seal.v2")
        self.assertEqual(seal.required_manifest_id, "required-run-1")
        self.assertRegex(seal.required_manifest_sha256 or "", r"^[0-9a-f]{64}$")
        self.assertEqual(len(seal.refs), 1)
        sealed_ref = seal.refs[0]
        self.assertTrue(sealed_ref.exists)
        self.assertEqual(
            sealed_ref.observed_sha256,
            hashlib.sha256(self.target.read_bytes()).hexdigest(),
        )
        self.assertFalse(seal.promotion_allowed)

    def test_seal_fails_closed_on_unresolvable_ref(self) -> None:
        manifest = self.manifest(self.ref("legs/absent.json"))
        with self.assertRaises(SealFailedClosed):
            seal_run("run-1", manifest, self.routes, now=self.now)

    def test_required_manifest_fails_closed_on_zero_refs(self) -> None:
        with self.assertRaises(EvidenceError):
            build_required_manifest("required-run-1", [])

    def test_seal_rejects_an_embedded_verdict_value(self) -> None:
        with self.assertRaises(EvidenceError) as caught:
            build_required_manifest(
                "required-run-1",
                [{"obligation_id": "o1", "verdict": "PASS"}],  # type: ignore[list-item]
            )
        self.assertIn("not an EvidenceRef", str(caught.exception))

    def test_seal_rejects_a_ref_subclass_carrying_a_verdict(self) -> None:
        @dataclasses.dataclass(frozen=True)
        class VerdictCarryingRef(EvidenceRef):
            verdict: str = "PASS"

        smuggled = VerdictCarryingRef(
            kind=RefKind.RECEIPT, ref="legs/solver_a.json", route="file"
        )
        self.assertEqual(smuggled.verdict, "PASS")
        with self.assertRaises(EvidenceError):
            build_required_manifest("required-run-1", [smuggled])

    def test_sealed_ref_has_no_slot_a_value_could_occupy(self) -> None:
        seal = self.seal()
        self.assertIs(type(seal.refs[0]), EvidenceRef)
        self.assertEqual(
            set(seal.refs[0].to_dict()),
            {"kind", "ref", "route", "exists", "observed_sha256", "observed_at_utc"},
        )

    def test_sealed_document_carries_the_locator_not_the_verdict(self) -> None:
        seal = self.seal()
        document = json.dumps(seal.to_dict())
        self.assertIn("legs/solver_a.json", document)
        self.assertNotIn("PASS", document)
        self.assertIn("PASS", self.target.read_text(encoding="utf-8"))

    def test_run_seal_constructor_rejects_non_ref_members(self) -> None:
        with self.assertRaises(EvidenceError):
            RunSeal(
                schema="constraintbox.run-seal.v2",
                run_id="run-1",
                sealed_at_utc=self.now.isoformat(),
                refs=({"verdict": "PASS"},),  # type: ignore[arg-type]
                seal_sha256="0" * 64,
            )

    def test_seal_rejects_duplicate_references(self) -> None:
        with self.assertRaises(EvidenceError):
            build_required_manifest(
                "required-run-1",
                [self.ref(), self.ref()],
            )

    def test_seal_rejects_empty_run_id(self) -> None:
        with self.assertRaises(EvidenceError):
            seal_run("  ", self.manifest(), self.routes, now=self.now)

    def test_seal_rejects_a_forged_manifest_digest(self) -> None:
        manifest = self.manifest()
        forged = dataclasses.replace(manifest, manifest_sha256="0" * 64)
        with self.assertRaises(EvidenceError):
            seal_run("run-1", forged, self.routes, now=self.now)


class VerifyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.routes = route_table(FileRoute(self.root))
        self.now = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)
        self.target = self.root / "legs" / "solver_a.json"
        self.target.parent.mkdir(parents=True, exist_ok=True)
        self.target.write_text(json.dumps({"leg": "solver_a"}), encoding="utf-8")
        self.manifest = build_required_manifest(
            "required-run-1",
            [
                EvidenceRef(
                    kind=RefKind.RECEIPT,
                    ref="legs/solver_a.json",
                    route="file",
                )
            ],
        )
        self.seal = seal_run(
            "run-1",
            self.manifest,
            self.routes,
            now=self.now,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_unchanged_target_verifies_sealed(self) -> None:
        result = verify_seal(
            self.seal,
            self.routes,
            required_manifest=self.manifest,
        )
        self.assertIs(result.verdict, SealVerdict.SEALED)
        self.assertIs(result.refs[0].verdict, SealVerdict.SEALED)

    def test_mutated_target_verifies_ref_changed(self) -> None:
        self.target.write_text(json.dumps({"leg": "solver_a", "n": 2}), encoding="utf-8")
        result = verify_seal(
            self.seal,
            self.routes,
            required_manifest=self.manifest,
        )
        self.assertIs(result.verdict, SealVerdict.REF_CHANGED)
        self.assertNotEqual(
            result.refs[0].current_sha256, result.refs[0].ref.observed_sha256
        )

    def test_deleted_target_verifies_ref_missing(self) -> None:
        self.target.unlink()
        result = verify_seal(
            self.seal,
            self.routes,
            required_manifest=self.manifest,
        )
        self.assertIs(result.verdict, SealVerdict.REF_MISSING)

    def test_tampered_seal_digest_verifies_malformed(self) -> None:
        tampered = dataclasses.replace(self.seal, run_id="run-2")
        result = verify_seal(
            tampered,
            self.routes,
            required_manifest=self.manifest,
        )
        self.assertIs(result.verdict, SealVerdict.MALFORMED)
        self.assertIn("does not match", result.reason)

    def test_unregistered_route_at_verify_is_malformed_not_sealed(self) -> None:
        result = verify_seal(
            self.seal,
            {},
            required_manifest=self.manifest,
        )
        self.assertIs(result.verdict, SealVerdict.MALFORMED)
        self.assertIn("unregistered evidence route", result.reason)

    def test_unobserved_ref_in_a_hand_built_seal_is_malformed(self) -> None:
        hand_built = seal_from_dict(
            {
                "schema": "constraintbox.run-seal.v1",
                "run_id": "run-1",
                "sealed_at_utc": self.now.isoformat(),
                "refs": [
                    {"kind": "receipt", "ref": "legs/solver_a.json", "route": "file"}
                ],
                "seal_sha256": "0" * 64,
            }
        )
        result = verify_seal(
            hand_built,
            self.routes,
            required_manifest=self.manifest,
        )
        self.assertIs(result.verdict, SealVerdict.MALFORMED)
        self.assertIn("legacy seal", result.reason)

    def test_missing_outranks_changed(self) -> None:
        other = self.root / "legs" / "jax.json"
        other.write_text(json.dumps({"leg": "jax"}), encoding="utf-8")
        manifest = build_required_manifest(
            "required-run-2",
            [
                EvidenceRef(kind=RefKind.RECEIPT, ref="legs/solver_a.json", route="file"),
                EvidenceRef(kind=RefKind.RECEIPT, ref="legs/jax.json", route="file"),
            ],
        )
        seal = seal_run(
            "run-2",
            manifest,
            self.routes,
            now=self.now,
        )
        self.target.write_text("mutated", encoding="utf-8")
        other.unlink()
        result = verify_seal(
            seal,
            self.routes,
            required_manifest=manifest,
        )
        self.assertIs(result.verdict, SealVerdict.REF_MISSING)

    def test_round_trip_through_json_still_verifies(self) -> None:
        reloaded = seal_from_dict(json.loads(json.dumps(self.seal.to_dict())))
        self.assertEqual(reloaded, self.seal)
        reloaded_manifest = required_manifest_from_dict(
            json.loads(json.dumps(self.manifest.to_dict()))
        )
        self.assertIs(
            verify_seal(
                reloaded,
                self.routes,
                required_manifest=reloaded_manifest,
            ).verdict,
            SealVerdict.SEALED,
        )

    def test_v2_seal_without_controller_manifest_fails_closed(self) -> None:
        result = verify_seal(self.seal, self.routes)
        self.assertIs(result.verdict, SealVerdict.MALFORMED)
        self.assertIn("required-reference manifest", result.reason)

    def test_v2_seal_parser_rejects_unknown_top_and_ref_fields(self) -> None:
        top_level = self.seal.to_dict()
        top_level["verdict"] = "PASS"
        with self.assertRaises(EvidenceError):
            seal_from_dict(top_level)

        ref_level = self.seal.to_dict()
        ref_level["refs"][0]["verdict"] = "PASS"
        with self.assertRaises(EvidenceError):
            seal_from_dict(ref_level)

    def test_deleted_ref_and_recomputed_public_self_hash_is_malformed(self) -> None:
        second = self.root / "legs" / "cvc5.json"
        second.write_text(json.dumps({"leg": "cvc5"}), encoding="utf-8")
        manifest = build_required_manifest(
            "required-run-2",
            [
                EvidenceRef(
                    kind=RefKind.RECEIPT,
                    ref="legs/solver_a.json",
                    route="file",
                ),
                EvidenceRef(
                    kind=RefKind.RECEIPT,
                    ref="legs/cvc5.json",
                    route="file",
                ),
            ],
        )
        seal = seal_run("run-2", manifest, self.routes, now=self.now)

        forged_body = seal.to_dict()
        forged_body["refs"] = forged_body["refs"][:1]
        self_hash_body = {
            key: value
            for key, value in forged_body.items()
            if key not in {"seal_sha256", "promotion_allowed"}
        }
        forged_body["seal_sha256"] = public_digest(self_hash_body)
        forged = seal_from_dict(forged_body)

        result = verify_seal(
            forged,
            self.routes,
            required_manifest=manifest,
        )
        self.assertIs(result.verdict, SealVerdict.MALFORMED)
        self.assertIn("references differ", result.reason)

    def test_verify_seal_rejects_a_non_seal(self) -> None:
        with self.assertRaises(EvidenceError):
            verify_seal(  # type: ignore[arg-type]
                {"run_id": "run-1"},
                self.routes,
                required_manifest=self.manifest,
            )

    def test_ref_from_dict_rejects_a_non_boolean_exists(self) -> None:
        with self.assertRaises(EvidenceError):
            ref_from_dict(
                {
                    "kind": "receipt",
                    "ref": "legs/solver_a.json",
                    "route": "file",
                    "exists": "yes",
                }
            )


class DigestRouteSealTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = Path(self.temp.name) / "cas"
        self.store.mkdir(parents=True)
        self.routes = route_table(DigestRoute(self.store))
        self.now = datetime(2026, 7, 26, 12, 0, tzinfo=timezone.utc)
        payload = b'{"leg": "jax"}'
        self.payload = payload
        self.name = hashlib.sha256(payload).hexdigest()
        (self.store / self.name).write_bytes(payload)
        self.manifest = build_required_manifest(
            "required-run-3",
            [
                EvidenceRef(
                    kind=RefKind.ARTIFACT,
                    ref=self.name,
                    route="digest",
                )
            ],
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_content_addressed_seal_and_verify(self) -> None:
        seal = seal_run(
            "run-3",
            self.manifest,
            self.routes,
            now=self.now,
        )
        self.assertIs(
            verify_seal(
                seal,
                self.routes,
                required_manifest=self.manifest,
            ).verdict,
            SealVerdict.SEALED,
        )
        (self.store / self.name).write_bytes(b'{"leg": "jax", "n": 2}')
        self.assertIs(
            verify_seal(
                seal,
                self.routes,
                required_manifest=self.manifest,
            ).verdict,
            SealVerdict.REF_CHANGED,
        )

    def test_forged_digest_route_name_mismatch_is_malformed(self) -> None:
        wrong_name = "0" * 64
        (self.store / wrong_name).write_bytes(self.payload)
        manifest = build_required_manifest(
            "required-forged-cas",
            [
                EvidenceRef(
                    kind=RefKind.ARTIFACT,
                    ref=wrong_name,
                    route="digest",
                )
            ],
        )
        observed = ref_from_dict(
            {
                "kind": "artifact",
                "ref": wrong_name,
                "route": "digest",
                "exists": True,
                "observed_sha256": self.name,
                "observed_at_utc": self.now.isoformat(),
            }
        )
        seal_body = {
            "schema": "constraintbox.run-seal.v2",
            "run_id": "run-forged-cas",
            "sealed_at_utc": self.now.isoformat(),
            "refs": [observed.to_dict()],
            "required_manifest_id": manifest.manifest_id,
            "required_manifest_sha256": manifest.manifest_sha256,
        }
        forged = RunSeal(
            schema=seal_body["schema"],
            run_id=seal_body["run_id"],
            sealed_at_utc=seal_body["sealed_at_utc"],
            refs=(observed,),
            seal_sha256=public_digest(seal_body),
            required_manifest_id=manifest.manifest_id,
            required_manifest_sha256=manifest.manifest_sha256,
        )
        result = verify_seal(
            forged,
            self.routes,
            required_manifest=manifest,
        )
        self.assertIs(result.verdict, SealVerdict.MALFORMED)
        self.assertIn("does not hash to its name", result.refs[0].reason)


if __name__ == "__main__":
    unittest.main()
