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

    def test_discovery_accepts_sdk_install_and_parent_directories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sdk = make_sdk(root, nested=True)
            install = sdk.parent

            # Both the SDK directory and the installation that contains it
            # normalise to the same root.
            self.assertEqual(wwise_sdk.normalize_sdk_root(sdk), sdk.resolve())
            self.assertEqual(wwise_sdk.normalize_sdk_root(install), sdk.resolve())

            # A configured path may be absolute or relative to the config file.
            config = root / "wwise-sdk.config.json"
            config.write_text(json.dumps({"sdk_roots": [str(sdk)]}), encoding="utf-8")
            self.assertEqual(wwise_sdk.discover_sdk_roots(config_path=config)[0], sdk.resolve())

            config.write_text('{"sdk_roots": ["Wwise2025/SDK"]}', encoding="utf-8")
            self.assertEqual(wwise_sdk.read_configured_roots(config), [sdk])

            # A malformed array is a configuration error, not a silent empty list.
            config.write_text('{"sdk_roots": "SDK"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, '"sdk_roots" array'):
                wwise_sdk.read_configured_roots(config)

    def test_version_is_read_and_formatted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sdk = make_sdk(Path(directory))
            version = wwise_sdk.read_version(sdk)
            self.assertEqual(version, (2025, 1, 7, 9143))
            self.assertEqual(wwise_sdk.format_version(version), "2025.1.7 build 9143")


    def test_missing_sdk_is_reported_not_raised(self) -> None:
        """The CLI must exit 1 with a usable remedy in either config state."""
        for label, write_config in (("absent", False), ("present", True)):
            with self.subTest(config=label), tempfile.TemporaryDirectory() as directory:
                config = Path(directory) / "wwise-sdk.config.json"
                if write_config:
                    config.write_text('{"sdk_roots": []}', encoding="utf-8")

                errors = io.StringIO()
                with mock.patch.object(wwise_sdk, "CONFIG_FILE", config):
                    with contextlib.redirect_stderr(errors):
                        status = wwise_sdk.main(["locate"])
                    message = errors.getvalue()

                    # Exit 1 means "nothing to report", not a crash.
                    self.assertEqual(status, 1)
                    self.assertRegex(message, r"sdk_roots|--sdk-root")

                    # Without a config file the remedy is to copy the example;
                    # with one, it is to fill in the array already there.
                    if write_config:
                        self.assertNotIn("example", message)
                    else:
                        self.assertIn("wwise-sdk.config.example.json", message)

    def test_help_roots_are_read_and_appended_without_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "wwise-sdk.config.json"

            # Entries may be relative to the configuration file.
            existing = root / "extracted-help"
            existing.mkdir()
            config.write_text('{"sdk_roots": [], "help_roots": ["extracted-help"]}')
            self.assertEqual(wwise_sdk.read_configured_help_roots(config), [existing])

            # Registering a directory is idempotent and leaves sdk_roots alone.
            config.write_text(json.dumps({"sdk_roots": ["SDK"]}), encoding="utf-8")
            extracted = root / "HelpExtracted"
            self.assertTrue(wwise_sdk.add_help_root(extracted, config))
            self.assertFalse(wwise_sdk.add_help_root(extracted, config))

            data = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(data["sdk_roots"], ["SDK"])
            self.assertEqual(data["help_roots"], [extracted.as_posix()])


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

    def test_search_selects_files_and_merges_overlapping_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sdk = make_sdk(Path(directory))

            # A glob narrows the files searched within an area.
            source = sdk / "include" / "AK" / "Example.cpp"
            source.write_text("PostEvent();", encoding="utf-8")
            self.assertEqual(
                list(wwise_sdk.iter_search_files(sdk, "include", ["*.cpp"])), [source]
            )

            # Two hits close together report as one block, not two.
            path = Path(directory) / "AkExample.h"
            path.write_text("zero\nPostEvent one\nmiddle\nPostEvent two\nend\n", encoding="utf-8")
            pattern = wwise_sdk.compile_pattern("PostEvent", fixed=True, ignore_case=False)
            results = wwise_sdk.search_file(path, pattern, context=1)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0][:2], (1, 5))

    def test_search_finds_help_in_chm_and_extracted_directories(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sdk = make_sdk(root)
            self.assertIn("help", wwise_sdk.AREA_PATHS)

            # An installed CHM is extracted on demand and labelled by archive.
            chm = sdk / "Help" / "zh" / "WwiseSDK-Windows.chm"
            chm.parent.mkdir(parents=True)
            chm.write_bytes(b"fixture")

            def fake_extract(_chm: Path, output: Path, extractor=None) -> None:
                output.mkdir(parents=True)
                (output / "postevent.html").write_text("PostEvent docs", encoding="utf-8")

            with mock.patch.object(wwise_sdk, "extract_chm", side_effect=fake_extract):
                files = list(wwise_sdk.iter_help_files(sdk, root / "extracted", []))
            self.assertEqual(
                [label for _, label in files],
                ["Help/zh/WwiseSDK-Windows.chm!/postevent.html"],
            )

            # A pre-extracted help_roots directory is read directly.
            help_root = root / "configured"
            page = help_root / "guide" / "postevent.html"
            page.parent.mkdir(parents=True)
            page.write_text("PostEvent docs", encoding="utf-8")
            self.assertEqual(
                list(wwise_sdk.iter_extracted_help_files([help_root], [])),
                [(page, "ConfiguredHelp/0/guide/postevent.html")],
            )


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

    def test_parse_doc_url_reads_page_language_version_and_library(self) -> None:
        cases = (
            (
                "https://www.audiokinetic.com/zh/public-library/2025.1.10_9233/"
                "?source=WwiseFundamentalApproach&id=introducing_wwise",
                dict(
                    page="introducing_wwise",
                    language="zh",
                    version=(2025, 1, 10, 9233),
                    library="authoring",
                    anchor="",
                ),
            ),
            (
                "https://www.audiokinetic.com/en/public-library/2025.1.8_9170/"
                "?source=SDK&id=soundengine_events#details",
                dict(page="soundengine_events", library="sdk", anchor="details"),
            ),
            # `library/edge` tracks the latest docs, so it carries no version.
            (
                "https://www.audiokinetic.com/library/edge/?source=SDK&id=soundengine_events",
                dict(page="soundengine_events", library="sdk", version=None),
            ),
            # The page can come from the path instead of an `id` parameter.
            (
                "https://www.audiokinetic.com/zh/public-library/2025.1.10_9233/"
                "introducing_wwise.html",
                dict(page="introducing_wwise", language="zh"),
            ),
        )
        for url, expected in cases:
            with self.subTest(url=url):
                reference = wwise_sdk.parse_doc_url(url)
                for field, value in expected.items():
                    self.assertEqual(getattr(reference, field), value, field)

    def test_parse_doc_url_rejects_non_documentation_urls(self) -> None:
        cases = (
            ("https://example.com/public-library/?id=x", "Not an Audiokinetic"),
            # A lookalike host must not pass a prefix or substring check.
            ("https://audiokinetic.com.evil.test/public-library/?id=x", "Not an Audiokinetic"),
            ("https://www.audiokinetic.com/zh/community/", "Not a Wwise documentation URL"),
            ("https://www.audiokinetic.com/en/blog/some-post/", "Not a Wwise documentation URL"),
            (
                "https://www.audiokinetic.com/zh/community/?id=soundengine_events",
                "Not a Wwise documentation URL",
            ),
        )
        for url, message in cases:
            with self.subTest(url=url):
                with self.assertRaisesRegex(ValueError, message):
                    wwise_sdk.parse_doc_url(url)

    def test_url_resolves_to_a_local_page(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            sdk = make_sdk(Path(directory), nested=True)

            # A page name is matched inside the CHM without extracting it.
            chm = sdk / "Help" / "zh" / "WwiseSDK-Windows.chm"
            chm.parent.mkdir(parents=True)
            chm.write_bytes(b"\x00binary soundengine_events.html\x00")
            self.assertTrue(wwise_sdk.chm_contains_page(chm, "soundengine_events"))
            self.assertFalse(wwise_sdk.chm_contains_page(chm, "missing_page"))

            # Authoring pages ship as plain HTML beside the SDK, not in a CHM.
            authoring = (
                sdk.parent / "Authoring" / "Help" / "Contextual Help" / "zh"
                / "introducing_wwise.html"
            )
            authoring.parent.mkdir(parents=True)
            authoring.write_text("docs", encoding="utf-8")
            reference = wwise_sdk.parse_doc_url(
                "https://www.audiokinetic.com/zh/public-library/2025.1.8_9170/"
                "?source=WwiseFundamentalApproach&id=introducing_wwise"
            )
            self.assertIn(
                ("authoring-html", authoring),
                list(wwise_sdk.iter_local_doc_candidates(sdk, reference)),
            )

            # The printed command must be runnable: `search` takes a required
            # positional query, and --fixed stops a literal page name from
            # being read as a regular expression.
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
            self.assertIn('"soundengine_events"', hint)
            self.assertIn("--fixed", hint)
            self.assertFalse(hint.split("search", 1)[1].strip().startswith("--"))

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

    def test_extract_help_needs_chm_files_and_registers_the_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sdk = make_sdk(root)
            destination = root / "HelpExtracted"
            args = argparse.Namespace(
                sdk_root=str(sdk),
                destination=str(destination),
                language="zh",
                no_config=True,
            )

            # An SDK with no Help package cannot be extracted.
            with self.assertRaisesRegex(RuntimeError, "No CHM files found"):
                wwise_sdk.command_extract_help(args)

            chm = sdk / "Help" / "zh" / "WwiseSDK-Windows.chm"
            chm.parent.mkdir(parents=True)
            chm.write_bytes(b"fixture")
            config = root / "wwise-sdk.config.json"
            config.write_text(json.dumps({"sdk_roots": [str(sdk)]}), encoding="utf-8")

            def fake_extract(_chm: Path, output: Path, extractor=None) -> None:
                output.mkdir(parents=True, exist_ok=True)
                (output / "soundengine_events.html").write_text("docs", encoding="utf-8")

            args.no_config = False
            with mock.patch.object(wwise_sdk, "CONFIG_FILE", config), mock.patch.object(
                wwise_sdk, "extract_chm", side_effect=fake_extract
            ), mock.patch.object(
                wwise_sdk, "find_chm_extractor", return_value=("7z", Path("7z"))
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(wwise_sdk.command_extract_help(args), 0)

            # The extracted directory is registered so later searches reuse it.
            data = json.loads(config.read_text(encoding="utf-8"))
            self.assertEqual(data["help_roots"], [destination.as_posix()])
            self.assertTrue(
                (destination / "zh" / "WwiseSDK-Windows" / "soundengine_events.html").is_file()
            )



if __name__ == "__main__":
    unittest.main()
