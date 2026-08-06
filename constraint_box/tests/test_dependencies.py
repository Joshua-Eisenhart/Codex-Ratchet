from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from constraintbox import cli, dependencies


class DependencyTests(unittest.TestCase):
    def make_project(
        self,
        root: Path,
        *,
        locks: dict[str, str],
        project_dependencies: str = "",
        extras: str = "",
        source: str = "",
    ) -> None:
        lock_root = root / "requirements" / "locks"
        lock_root.mkdir(parents=True)
        for name, body in locks.items():
            (lock_root / name).write_text(body, encoding="utf-8")
        (root / "pyproject.toml").write_text(
            "[project]\n"
            'name = "fixture"\n'
            f"dependencies = [{project_dependencies}]\n"
            f"{extras}",
            encoding="utf-8",
        )
        source_root = root / "src" / "constraintbox"
        source_root.mkdir(parents=True)
        (source_root / "fixture.py").write_text(source, encoding="utf-8")

    def invoke(self, *arguments: str) -> tuple[int, str]:
        output = io.StringIO()
        code = 0
        with patch.object(sys, "argv", ["constraintbox", *arguments]):
            with contextlib.redirect_stdout(output):
                try:
                    cli.main()
                except SystemExit as exc:
                    code = int(exc.code)
        return code, output.getvalue()

    def test_lock_parsing_records_unpinned_line(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "e0-py312-linux.lock"
            path.write_text(
                "# retained comment\n\nnumpy==2.5.1\nnot-pinned>=1\n",
                encoding="utf-8",
            )
            declarations, invalid = dependencies.parse_lock(path)
        self.assertEqual(len(declarations), 1)
        self.assertEqual(declarations[0]["distribution"], "numpy")
        self.assertEqual(declarations[0]["required_spec"], "==2.5.1")
        self.assertEqual(len(invalid), 1)
        self.assertEqual(invalid[0]["line"], 4)
        self.assertIn("not pinned", invalid[0]["reason"])

    def test_pep503_name_normalization(self):
        self.assertEqual(dependencies.normalize_name("z3-solver"), "z3-solver")
        self.assertEqual(dependencies.normalize_name("Z3_solver"), "z3-solver")
        self.assertEqual(dependencies.normalize_name("Z3...Solver"), "z3-solver")

    def test_constructed_states_and_no_network_latest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_project(
                root,
                locks={
                    "e0-py312-linux.lock": (
                        "same==2.0\nbehind==2.0\nahead==2.0\n"
                        "missing==2.0\nodd==release-two\n"
                    )
                },
                source="import mystery_mod\n",
            )
            report = dependencies.scan(
                root,
                installed_versions={
                    "same": "2.0",
                    "behind": "1.9",
                    "ahead": "2.1",
                    "odd": "release-one",
                    "mystery-dist": "4.0",
                },
                package_map={"mystery_mod": ["mystery-dist"]},
                stdlib_modules=sys.stdlib_module_names,
                host_platform="darwin",
                host_python="3.13.6",
                host_machine="arm64",
            )
        states = {
            row["normalized_name"]: row["state"]
            for row in report["rows"]
        }
        self.assertEqual(states["same"], "OK")
        self.assertEqual(states["behind"], "BEHIND")
        self.assertEqual(states["ahead"], "AHEAD")
        self.assertEqual(states["missing"], "MISSING")
        self.assertEqual(states["odd"], "UNKNOWN")
        self.assertEqual(states["mystery-dist"], "UNDECLARED")
        for row in report["rows"]:
            self.assertIsNone(row["latest"])
            self.assertIsNone(row["latest_source"])
            self.assertTrue(row["latest_reason"])

    def test_extra_ranges_and_duplicate_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_project(
                root,
                locks={
                    "e0-py312-linux.lock": "numpy==2.5\n",
                    "e1-py312-linux.lock": "numpy==2.4\n",
                },
                extras=(
                    '\n[project.optional-dependencies]\n'
                    'gate = ["numpy>=2", "low>=2"]\n'
                ),
            )
            report = dependencies.scan(
                root,
                installed_versions={"numpy": "2.9", "low": "1.5"},
                package_map={},
                stdlib_modules=sys.stdlib_module_names,
                host_platform="darwin",
                host_python="3.13.6",
                host_machine="arm64",
            )
        numpy_rows = [
            row for row in report["rows"] if row["normalized_name"] == "numpy"
        ]
        self.assertEqual(len(numpy_rows), 3)
        extra_numpy = next(row for row in numpy_rows if row["source_kind"] == "extra")
        self.assertEqual(extra_numpy["state"], "OK")
        self.assertEqual(extra_numpy["extra"], "gate")
        low = next(row for row in report["rows"] if row["normalized_name"] == "low")
        self.assertEqual(low["state"], "BEHIND")
        self.assertEqual(report["row_strategy"], dependencies.ROW_STRATEGY)

    def test_unresolved_import_is_not_undeclared(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_project(
                root,
                locks={"e0-py312-linux.lock": "numpy==2.0\n"},
                source="import no_distribution\nfrom . import local\nimport sys\n",
            )
            report = dependencies.scan(
                root,
                installed_versions={"numpy": "2.0"},
                package_map={},
                stdlib_modules=sys.stdlib_module_names,
            )
        self.assertIn("no_distribution", report["unresolved_imports"])
        self.assertNotIn("local", report["unresolved_imports"])
        self.assertFalse(
            any(row["state"] == "UNDECLARED" for row in report["rows"])
        )

    def test_exit_code_mapping_and_precedence(self):
        def report(*states: str) -> dict[str, object]:
            return {"rows": [{"state": state} for state in states]}

        self.assertEqual(dependencies.exit_code_for(report("OK")), 0)
        self.assertEqual(dependencies.exit_code_for(report("MISSING")), 1)
        self.assertEqual(dependencies.exit_code_for(report("BEHIND")), 1)
        self.assertEqual(dependencies.exit_code_for(report("UNKNOWN")), 1)
        self.assertEqual(dependencies.exit_code_for(report("AHEAD")), 3)
        self.assertEqual(dependencies.exit_code_for(report("UNDECLARED")), 3)
        self.assertEqual(
            dependencies.exit_code_for(
                report("AHEAD", "UNDECLARED", "AHEAD", "BEHIND")
            ),
            1,
        )
        self.assertEqual(
            set(dependencies.EXIT_CODES.values()),
            {0, 1, 2, 3},
        )

    def test_missing_locks_directory_is_controlled_exit_two(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "pyproject.toml").write_text(
                '[project]\nname = "fixture"\ndependencies = []\n',
                encoding="utf-8",
            )
            with self.assertRaises(dependencies.DependencyScanError):
                dependencies.scan(root)
            scan = dependencies.scan
            with patch.object(
                cli.dependencies,
                "scan",
                side_effect=lambda: scan(root),
            ):
                code, output = self.invoke("deps", "--check")
        self.assertEqual(code, 2)
        self.assertIn("missing locks directory", output)

    def test_limitations_are_in_report_and_json(self):
        report = {
            "schema": "constraintbox.dependencies.v1",
            "row_strategy": dependencies.ROW_STRATEGY,
            "rows": [
                {
                    "distribution": "numpy",
                    "installed": "2.9",
                    "required_spec": "==2.5",
                    "state": "AHEAD",
                    "compare_method": "pep440",
                    "cross_platform_lock": True,
                    "source": "e0-py312-linux.lock",
                }
            ],
            "unresolved_imports": [],
            "invalid_declarations": [],
            "limitations": {
                "lock_environment": "resolved for linux/py3.12",
                "host_environment": "measured darwin/arm64 Python 3.13.6",
                "cross_platform_warning": (
                    "AHEAD/BEHIND may reflect the platform split."
                ),
                "latest": "Latest was not measured.",
            },
        }
        rendered = dependencies.render_table(report)
        self.assertIn("Limitations:", rendered)
        self.assertIn("linux/py3.12", rendered)
        with patch.object(cli.dependencies, "scan", return_value=report):
            report_code, report_output = self.invoke("deps", "--report")
            json_code, json_output = self.invoke("deps", "--json")
        self.assertEqual(report_code, 3)
        self.assertIn("Limitations:", report_output)
        self.assertEqual(json_code, 3)
        parsed = json.loads(json_output)
        self.assertTrue(parsed["limitations"])
        self.assertIn("platform split", parsed["limitations"]["cross_platform_warning"])

    def test_check_is_one_summary_line(self):
        report = {
            "rows": [{"state": "AHEAD"}],
            "limitations": {"warning": "measured limitation"},
        }
        with patch.object(cli.dependencies, "scan", return_value=report):
            code, output = self.invoke("deps", "--check")
        self.assertEqual(code, 3)
        self.assertEqual(len(output.splitlines()), 1)
        self.assertIn("AHEAD=1", output)

    def test_report_and_check_are_mutually_exclusive(self):
        parser = cli.build_parser()
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                parser.parse_args(["deps", "--report", "--check"])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
