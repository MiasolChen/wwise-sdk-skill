from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).parents[1] / "scripts" / "wwise_sdk.py"
SPEC = importlib.util.spec_from_file_location("wwise_sdk", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
wwise_sdk = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wwise_sdk)


def make_sdk(
    parent: Path,
    nested: bool = False,
    version: tuple[int, int, int, int] = (2025, 1, 7, 9143),
    install_name: str = "Wwise2025",
) -> Path:
    root = parent / install_name / "SDK" if nested else parent / "SDK"
    version_file = root / "include" / "AK" / "AkWwiseSDKVersion.h"
    version_file.parent.mkdir(parents=True)
    major, minor, subminor, build = version
    version_file.write_text(
        f"""\
#define AK_WWISESDK_VERSION_MAJOR {major}
#define AK_WWISESDK_VERSION_MINOR {minor}
#define AK_WWISESDK_VERSION_SUBMINOR {subminor}
#define AK_WWISESDK_VERSION_BUILD {build}
""",
        encoding="utf-8",
    )
    return root


class WwiseSdkTests(unittest.TestCase):
    def setUp(self) -> None:
        """Never let a test read or modify the repository configuration file."""
        guard = mock.patch.object(
            wwise_sdk, "CONFIG_FILE", Path(tempfile.gettempdir()) / "wwise-sdk.absent.json"
        )
        guard.start()
        self.addCleanup(guard.stop)

    def test_normalize_accepts_sdk_and_install_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            install = Path(directory) / "Wwise2025"
            sdk = make_sdk(Path(directory), nested=True)
            self.assertEqual(wwise_sdk.normalize_sdk_root(sdk), sdk.resolve())
            self.assertEqual(wwise_sdk.normalize_sdk_root(install), sdk.resolve())

    def test_discovery_uses_configured_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sdk = make_sdk(root)
            config = root / "wwise-sdk.config.json"
            config.write_text(
                json.dumps({"sdk_roots": [str(sdk)]}),
                encoding="utf-8",
            )
            roots = wwise_sdk.discover_sdk_roots(config_path=config)
            self.assertEqual(roots[0], sdk.resolve())

    def test_configured_relative_path_is_relative_to_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sdk = make_sdk(root)
            config = root / "wwise-sdk.config.json"
            config.write_text('{"sdk_roots": ["SDK"]}', encoding="utf-8")
            self.assertEqual(wwise_sdk.read_configured_roots(config), [sdk])

    def test_config_requires_sdk_roots_array(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "wwise-sdk.config.json"
            config.write_text('{"sdk_roots": "SDK"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, '"sdk_roots" array'):
                wwise_sdk.read_configured_roots(config)

    def test_missing_sdk_message_points_at_example_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "wwise-sdk.config.json"
            with mock.patch.object(wwise_sdk, "CONFIG_FILE", config):
                absent = wwise_sdk.missing_sdk_message()
                self.assertIn("wwise-sdk.config.example.json", absent)
                self.assertIn("--sdk-root", absent)

                config.write_text('{"sdk_roots": []}', encoding="utf-8")
                present = wwise_sdk.missing_sdk_message()
                self.assertNotIn("example", present)
                self.assertIn("sdk_roots", present)


    def test_configured_help_roots_support_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            help_root = root / "extracted-help"
            help_root.mkdir()
            config = root / "wwise-sdk.config.json"
            config.write_text('{"sdk_roots": [], "help_roots": ["extracted-help"]}')
            self.assertEqual(wwise_sdk.read_configured_help_roots(config), [help_root])

    def test_discovery_prefers_latest_version_in_install_parent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            older = make_sdk(
                parent,
                nested=True,
                version=(2024, 1, 9, 100),
                install_name="Wwise-newer-name",
            )
            newer = make_sdk(
                parent,
                nested=True,
                version=(2025, 1, 2, 50),
                install_name="Wwise-older-name",
            )
            config = parent / "wwise-sdk.config.json"
            config.write_text('{"sdk_roots": ["."]}', encoding="utf-8")
            roots = wwise_sdk.discover_sdk_roots(config_path=config)
            self.assertEqual(roots[:2], [newer.resolve(), older.resolve()])

    def test_read_version(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sdk = make_sdk(Path(directory))
            self.assertEqual(wwise_sdk.read_version(sdk), (2025, 1, 7, 9143))
            self.assertEqual(
                wwise_sdk.format_version(wwise_sdk.read_version(sdk)),
                "2025.1.7 build 9143",
            )

    def test_search_merges_overlapping_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "AkExample.h"
            path.write_text("zero\nPostEvent one\nmiddle\nPostEvent two\nend\n", encoding="utf-8")
            pattern = wwise_sdk.compile_pattern("PostEvent", fixed=True, ignore_case=False)
            results = wwise_sdk.search_file(path, pattern, context=1)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0][:2], (1, 5))

    def test_iter_search_files_filters_globs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sdk = make_sdk(Path(directory))
            source = sdk / "include" / "AK" / "Example.cpp"
            source.write_text("PostEvent();", encoding="utf-8")
            files = list(wwise_sdk.iter_search_files(sdk, "include", ["*.cpp"]))
            self.assertEqual(files, [source])

    def test_help_is_a_search_area(self) -> None:
        self.assertIn("help", wwise_sdk.AREA_PATHS)

    def test_iter_help_files_extracts_chm_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sdk = make_sdk(root)
            chm = sdk / "Help" / "zh" / "WwiseSDK-Windows.chm"
            chm.parent.mkdir(parents=True)
            chm.write_bytes(b"fixture")
            destination = root / "extracted"

            def fake_extract(_chm: Path, output: Path, extractor=None) -> None:
                output.mkdir(parents=True)
                (output / "postevent.html").write_text("PostEvent docs", encoding="utf-8")

            with mock.patch.object(wwise_sdk, "extract_chm", side_effect=fake_extract):
                files = list(wwise_sdk.iter_help_files(sdk, destination, []))

            self.assertEqual(len(files), 1)
            self.assertEqual(
                files[0][1], "Help/zh/WwiseSDK-Windows.chm!/postevent.html"
            )

    def test_iter_extracted_help_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            help_root = Path(directory)
            page = help_root / "guide" / "postevent.html"
            page.parent.mkdir()
            page.write_text("PostEvent docs", encoding="utf-8")
            files = list(wwise_sdk.iter_extracted_help_files([help_root], []))
            self.assertEqual(files, [(page, "ConfiguredHelp/0/guide/postevent.html")])

    def test_extract_chm_builds_7z_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            chm = root / "help.chm"
            chm.write_bytes(b"fixture")
            destination = root / "output"
            completed = mock.Mock(returncode=0, stderr="", stdout="")
            with mock.patch.object(wwise_sdk.subprocess, "run", return_value=completed) as run:
                wwise_sdk.extract_chm(chm, destination, ("7z", Path("7z")))
            self.assertEqual(
                run.call_args.args[0],
                ["7z", "x", "-y", f"-o{destination}", str(chm)],
            )

    def test_parse_doc_url_reads_page_language_and_version(self) -> None:
        reference = wwise_sdk.parse_doc_url(
            "https://www.audiokinetic.com/zh/public-library/2025.1.10_9233/"
            "?source=WwiseFundamentalApproach&id=introducing_wwise"
        )
        self.assertEqual(reference.page, "introducing_wwise")
        self.assertEqual(reference.language, "zh")
        self.assertEqual(reference.version, (2025, 1, 10, 9233))
        self.assertEqual(reference.library, "authoring")

    def test_parse_doc_url_detects_sdk_library_and_anchor(self) -> None:
        reference = wwise_sdk.parse_doc_url(
            "https://www.audiokinetic.com/en/public-library/2025.1.8_9170/"
            "?source=SDK&id=soundengine_events#details"
        )
        self.assertEqual(reference.page, "soundengine_events")
        self.assertEqual(reference.library, "sdk")
        self.assertEqual(reference.anchor, "details")

    def test_parse_doc_url_rejects_other_hosts(self) -> None:
        with self.assertRaisesRegex(ValueError, "Not an Audiokinetic"):
            wwise_sdk.parse_doc_url(
                "https://example.com/public-library/?id=soundengine_events"
            )

    def test_parse_doc_url_rejects_lookalike_host(self) -> None:
        with self.assertRaisesRegex(ValueError, "Not an Audiokinetic"):
            wwise_sdk.parse_doc_url(
                "https://audiokinetic.com.evil.test/public-library/?id=soundengine_events"
            )

    def test_parse_doc_url_rejects_non_documentation_paths(self) -> None:
        for url in (
            "https://www.audiokinetic.com/zh/community/",
            "https://www.audiokinetic.com/en/blog/some-post/",
            "https://www.audiokinetic.com/zh/community/?id=soundengine_events",
        ):
            with self.subTest(url=url):
                with self.assertRaisesRegex(ValueError, "Not a Wwise documentation URL"):
                    wwise_sdk.parse_doc_url(url)

    def test_parse_doc_url_accepts_library_path(self) -> None:
        reference = wwise_sdk.parse_doc_url(
            "https://www.audiokinetic.com/library/edge/?source=SDK&id=soundengine_events"
        )
        self.assertEqual(reference.page, "soundengine_events")
        self.assertEqual(reference.library, "sdk")
        self.assertIsNone(reference.version)

    def test_parse_doc_url_reads_page_from_path(self) -> None:
        reference = wwise_sdk.parse_doc_url(
            "https://www.audiokinetic.com/zh/public-library/2025.1.10_9233/"
            "introducing_wwise.html"
        )
        self.assertEqual(reference.page, "introducing_wwise")
        self.assertEqual(reference.language, "zh")

    def test_chm_contains_page(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            chm = Path(directory) / "WwiseSDK-Windows.chm"
            chm.write_bytes(b"\x00binary soundengine_events.html\x00")
            self.assertTrue(wwise_sdk.chm_contains_page(chm, "soundengine_events"))
            self.assertFalse(wwise_sdk.chm_contains_page(chm, "missing_page"))

    def test_iter_local_doc_candidates_finds_authoring_page(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sdk = make_sdk(root, nested=True)
            page = (
                sdk.parent
                / "Authoring"
                / "Help"
                / "Contextual Help"
                / "zh"
                / "introducing_wwise.html"
            )
            page.parent.mkdir(parents=True)
            page.write_text("docs", encoding="utf-8")
            reference = wwise_sdk.parse_doc_url(
                "https://www.audiokinetic.com/zh/public-library/2025.1.8_9170/"
                "?source=WwiseFundamentalApproach&id=introducing_wwise"
            )
            candidates = list(wwise_sdk.iter_local_doc_candidates(sdk, reference))
            self.assertIn(("authoring-html", page), candidates)

    def test_resolve_url_prints_a_runnable_search_command(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sdk = make_sdk(root, nested=True)
            chm = sdk / "Help" / "zh" / "WwiseSDK-Windows.chm"
            chm.parent.mkdir(parents=True)
            chm.write_bytes(b"\x00soundengine_events.html\x00")

            args = argparse.Namespace(
                url=(
                    "https://www.audiokinetic.com/zh/public-library/2025.1.7_9143/"
                    "?source=SDK&id=soundengine_events"
                ),
                sdk_root=str(sdk),
            )
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(wwise_sdk.command_resolve_url(args), 0)

            hint = next(
                line
                for line in output.getvalue().splitlines()
                if line.startswith("Read it with:")
            )
            # The query is a required positional argument, so a hint without one
            # is not runnable. --fixed keeps literal page and anchor names from
            # being parsed as a regular expression.
            self.assertIn('"soundengine_events"', hint)
            self.assertIn("--fixed", hint)

            command = hint.split("search", 1)[1].strip()
            self.assertFalse(command.startswith("--"))

    def test_add_help_root_appends_and_deduplicates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "wwise-sdk.config.json"
            config.write_text(json.dumps({"sdk_roots": ["SDK"]}), encoding="utf-8")
            extracted = root / "HelpExtracted"

            self.assertTrue(wwise_sdk.add_help_root(extracted, config))
            self.assertFalse(wwise_sdk.add_help_root(extracted, config))

            data = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(data["sdk_roots"], ["SDK"])
            self.assertEqual(data["help_roots"], [extracted.as_posix()])

    def test_find_authoring_help_roots(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sdk = make_sdk(Path(directory), nested=True)
            base = sdk.parent / "Authoring" / "Help" / "Contextual Help"
            (base / "en").mkdir(parents=True)
            (base / "zh").mkdir()
            names = [path.name for path in wwise_sdk.find_authoring_help_roots(sdk)]
            self.assertEqual(names, ["en", "zh"])

    def test_check_reports_missing_sdk_help(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sdk = make_sdk(root, nested=True)
            config = root / "wwise-sdk.config.json"
            config.write_text(
                json.dumps({"sdk_roots": [str(sdk)], "help_roots": []}),
                encoding="utf-8",
            )
            args = argparse.Namespace(sdk_root=str(sdk))
            with mock.patch.object(wwise_sdk, "CONFIG_FILE", config), contextlib.redirect_stdout(
                io.StringIO()
            ):
                self.assertEqual(wwise_sdk.command_check(args), 1)

    def test_extract_help_requires_chm_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sdk = make_sdk(root)
            args = argparse.Namespace(
                sdk_root=str(sdk),
                destination=str(root / "out"),
                language=None,
                no_config=True,
            )
            with self.assertRaisesRegex(RuntimeError, "No CHM files found"):
                wwise_sdk.command_extract_help(args)

    def test_extract_help_writes_config_entry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sdk = make_sdk(root)
            chm = sdk / "Help" / "zh" / "WwiseSDK-Windows.chm"
            chm.parent.mkdir(parents=True)
            chm.write_bytes(b"fixture")
            config = root / "wwise-sdk.config.json"
            config.write_text(json.dumps({"sdk_roots": [str(sdk)]}), encoding="utf-8")
            destination = root / "HelpExtracted"

            def fake_extract(_chm: Path, output: Path, extractor=None) -> None:
                output.mkdir(parents=True, exist_ok=True)
                (output / "soundengine_events.html").write_text("docs", encoding="utf-8")

            args = argparse.Namespace(
                sdk_root=str(sdk),
                destination=str(destination),
                language="zh",
                no_config=False,
            )
            with mock.patch.object(wwise_sdk, "CONFIG_FILE", config), mock.patch.object(
                wwise_sdk, "extract_chm", side_effect=fake_extract
            ), mock.patch.object(
                wwise_sdk, "find_chm_extractor", return_value=("7z", Path("7z"))
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(wwise_sdk.command_extract_help(args), 0)

            data = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(data["help_roots"], [destination.as_posix()])
            self.assertTrue(
                (destination / "zh" / "WwiseSDK-Windows" / "soundengine_events.html").is_file()
            )



if __name__ == "__main__":
    unittest.main()
