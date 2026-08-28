#!/usr/bin/env python3
"""Locate and search a local Wwise SDK without third-party dependencies."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable, Iterator, NamedTuple, Sequence
from urllib.parse import parse_qs, unquote, urlparse


VERSION_FILE = Path("include/AK/AkWwiseSDKVersion.h")
CONFIG_FILE = Path(__file__).resolve().parents[1] / "wwise-sdk.config.json"
TEXT_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".h",
    ".hh",
    ".hpp",
    ".hxx",
    ".htm",
    ".html",
    ".inl",
    ".md",
    ".txt",
    ".xml",
}
AREA_PATHS = {
    "include": ("include/AK",),
    "samples": ("samples",),
    "source": ("source",),
    "help": (),
    "all": ("include/AK", "samples", "source"),
}
VERSION_MACROS = {
    "major": "AK_WWISESDK_VERSION_MAJOR",
    "minor": "AK_WWISESDK_VERSION_MINOR",
    "subminor": "AK_WWISESDK_VERSION_SUBMINOR",
    "build": "AK_WWISESDK_VERSION_BUILD",
}
DOC_LANGUAGES = {"en", "ja", "ko", "zh"}
DOC_PATH_SEGMENTS = {"library", "public-library"}
AUTHORING_HELP = Path("Authoring/Help/Contextual Help")
SDK_HELP = Path("SDK/Help")


class DocReference(NamedTuple):
    """A Wwise documentation page parsed from an official documentation URL."""

    page: str
    language: str
    version: tuple[int, int, int, int] | None
    library: str
    anchor: str


def parse_doc_url(url: str) -> DocReference:
    """Parse an Audiokinetic documentation URL into local lookup information."""
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower().rsplit("@", 1)[-1].split(":", 1)[0]
    if host and host != "audiokinetic.com" and not host.endswith(".audiokinetic.com"):
        raise ValueError(f"Not an Audiokinetic URL: {url}")

    query = parse_qs(parsed.query)
    segments = [unquote(part) for part in parsed.path.split("/") if part]

    if not any(segment.lower() in DOC_PATH_SEGMENTS for segment in segments):
        raise ValueError(
            "Not a Wwise documentation URL. Only documentation paths such as "
            f"/library/ and /public-library/ can be resolved locally: {url}"
        )

    language = next((part for part in segments if part in DOC_LANGUAGES), "en")

    version: tuple[int, int, int, int] | None = None
    for part in segments:
        match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)[._](\d+)", part)
        if match:
            version = tuple(int(value) for value in match.groups())  # type: ignore[assignment]
            break

    page = next(iter(query.get("id", [])), "")
    if not page:
        candidate = next(
            (
                part
                for part in reversed(segments)
                if part.lower() not in DOC_PATH_SEGMENTS
                and part not in DOC_LANGUAGES
                and not re.fullmatch(r"(\d+)\.(\d+)\.(\d+)[._](\d+)|edge", part)
            ),
            "",
        )
        page = candidate[:-5] if candidate.endswith(".html") else candidate
    page = page.split("#", 1)[0].strip()
    if not page:
        raise ValueError(f"Cannot determine a documentation page from: {url}")

    source = next(iter(query.get("source", [])), "")
    library = "sdk" if source.lower().startswith("sdk") else "authoring"
    if page.startswith(("ak_", "class_", "struct_", "namespace")) or source.startswith(
        ("SDK", "Wwise_SDK")
    ):
        library = "sdk"

    return DocReference(
        page=page,
        language=language,
        version=version,
        library=library,
        anchor=unquote(parsed.fragment),
    )


def iter_local_doc_candidates(
    sdk_root: Path, reference: DocReference
) -> Iterator[tuple[str, Path]]:
    """Yield local Help locations that may contain the referenced page."""
    install_root = sdk_root.parent
    languages = [reference.language] + [
        code for code in ("en", "zh", "ja", "ko") if code != reference.language
    ]

    for language in languages:
        authoring = install_root / AUTHORING_HELP / language / f"{reference.page}.html"
        if authoring.is_file():
            yield "authoring-html", authoring

    for help_root in read_configured_help_roots():
        candidate = help_root / f"{reference.page}.html"
        if candidate.is_file():
            yield "extracted-html", candidate
            continue
        if help_root.is_dir():
            for found in sorted(help_root.rglob(f"{reference.page}.html")):
                yield "extracted-html", found

    for language in languages:
        base = sdk_root / "Help" if language == "en" else sdk_root / "Help" / language
        chm = base / "WwiseSDK-Windows.chm"
        if chm.is_file():
            yield "sdk-chm", chm
        for candidate in sorted(base.glob("*.chm")) if base.is_dir() else ():
            if candidate != chm:
                yield "sdk-chm", candidate


def chm_contains_page(chm: Path, page: str) -> bool:
    """Check whether a CHM stores the given page name, without extracting it."""
    try:
        data = chm.read_bytes()
    except OSError:
        return False
    return f"{page}.html".encode("utf-8", "ignore") in data


def normalize_sdk_root(candidate: Path) -> Path | None:
    """Return a validated SDK root from an SDK or Wwise install directory."""
    candidate = candidate.expanduser()
    options = (candidate, candidate / "SDK")
    for option in options:
        if (option / VERSION_FILE).is_file():
            return option.resolve()
    return None


def read_configured_roots(config_path: Path | None = None) -> list[Path]:
    """Read user-supplied SDK paths from the skill's JSON configuration."""
    config_path = CONFIG_FILE if config_path is None else config_path

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in {config_path}: {error}") from error

    roots = data.get("sdk_roots") if isinstance(data, dict) else None
    if not isinstance(roots, list) or not all(isinstance(root, str) for root in roots):
        raise ValueError(f'{config_path} must contain an "sdk_roots" array of strings')

    return [
        path if path.is_absolute() else config_path.parent / path
        for value in roots
        if value.strip()
        for path in (Path(value).expanduser(),)
    ]


def read_configured_help_roots(config_path: Path | None = None) -> list[Path]:
    """Read user-supplied directories containing extracted CHM files."""
    config_path = CONFIG_FILE if config_path is None else config_path

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in {config_path}: {error}") from error

    roots = data.get("help_roots", []) if isinstance(data, dict) else None
    if not isinstance(roots, list) or not all(isinstance(root, str) for root in roots):
        raise ValueError(f'{config_path} must contain a "help_roots" array of strings')

    return [
        path if path.is_absolute() else config_path.parent / path
        for value in roots
        if value.strip()
        for path in (Path(value).expanduser(),)
    ]


def discover_sdk_roots(
    explicit: Path | None = None, config_path: Path | None = None
) -> list[Path]:

    """Find validated SDK roots, preserving priority and removing duplicates."""
    candidates: list[Path] = []
    if explicit is not None:
        candidates.append(explicit)
    candidates.extend(read_configured_roots(config_path))

    roots: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        direct = normalize_sdk_root(candidate)
        options: Iterable[Path]
        if direct is not None:
            options = (direct,)
        elif candidate.is_dir():
            try:
                discovered = [
                    root
                    for child in candidate.iterdir()
                    if child.is_dir()
                    for root in (normalize_sdk_root(child),)
                    if root is not None
                ]
                options = sorted(discovered, key=read_version, reverse=True)
            except OSError:
                options = ()
        else:
            options = ()

        for root in options:
            key = os.path.normcase(str(root))
            if key not in seen:
                seen.add(key)
                roots.append(root)
    return roots


def read_version(sdk_root: Path) -> tuple[int, int, int, int]:
    text = (sdk_root / VERSION_FILE).read_text(encoding="utf-8", errors="replace")
    values: dict[str, int] = {}
    for key, macro in VERSION_MACROS.items():
        match = re.search(rf"^\s*#\s*define\s+{macro}\s+(\d+)", text, re.MULTILINE)
        if match is None:
            raise ValueError(f"Missing {macro} in {VERSION_FILE.as_posix()}")
        values[key] = int(match.group(1))
    return values["major"], values["minor"], values["subminor"], values["build"]


def format_version(version: tuple[int, int, int, int]) -> str:
    major, minor, subminor, build = version
    return f"{major}.{minor}.{subminor} build {build}"


def iter_search_files(sdk_root: Path, area: str, globs: Sequence[str]) -> Iterator[Path]:
    for relative_area in AREA_PATHS[area]:
        base = sdk_root / relative_area
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            if globs:
                relative = path.relative_to(sdk_root).as_posix()
                if not any(fnmatch.fnmatch(path.name, item) or fnmatch.fnmatch(relative, item) for item in globs):
                    continue
            elif path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            yield path


def find_chm_extractor() -> tuple[str, Path] | None:
    """Find an available CHM extractor on Windows, macOS, or Linux."""
    found = shutil.which("hh.exe") or shutil.which("hh")
    if found:
        return "hh", Path(found)
    windows = os.environ.get("WINDIR")
    candidate = Path(windows) / "System32" / "hh.exe" if windows else None
    if candidate and candidate.is_file():
        return "hh", candidate
    for command in ("7z", "7zz", "7za"):
        found = shutil.which(command)
        if found:
            return "7z", Path(found)
    found = shutil.which("extract_chmLib")
    return ("chmlib", Path(found)) if found else None


def extract_chm(
    chm: Path,
    destination: Path,
    extractor: tuple[str, Path] | None = None,
) -> None:
    """Extract one CHM with an available platform tool."""
    selected = extractor or find_chm_extractor()
    if selected is None:
        raise RuntimeError(
            "Cannot read CHM Help: install 7-Zip or chmlib, or extract the CHM "
            f"manually and add the output directory to {CONFIG_FILE}."
        )
    kind, executable = selected
    destination.mkdir(parents=True, exist_ok=True)
    commands = {
        "hh": [str(executable), "-decompile", str(destination), str(chm)],
        "7z": [str(executable), "x", "-y", f"-o{destination}", str(chm)],
        "chmlib": [str(executable), str(chm), str(destination)],
    }
    result = subprocess.run(
        commands[kind],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Failed to extract {chm.name}: {detail or result.returncode}")


def iter_extracted_help_files(
    help_roots: Sequence[Path], globs: Sequence[str]
) -> Iterator[tuple[Path, str]]:
    """Yield searchable files from user-managed extracted Help directories."""
    for index, root in enumerate(help_roots):
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            relative = path.relative_to(root).as_posix()
            label = f"ConfiguredHelp/{index}/{relative}"
            if globs and not any(
                fnmatch.fnmatch(path.name, item) or fnmatch.fnmatch(label, item)
                for item in globs
            ):
                continue
            yield path, label


def iter_help_files(
    sdk_root: Path, destination: Path, globs: Sequence[str]
) -> Iterator[tuple[Path, str]]:
    """Extract installed SDK CHM files and yield searchable local HTML files."""
    help_root = sdk_root / "Help"
    if not help_root.is_dir():
        return
    for index, chm in enumerate(sorted(help_root.rglob("*.chm"))):
        relative_chm = chm.relative_to(sdk_root).as_posix()
        extracted = destination / str(index)
        extract_chm(chm, extracted)
        for path in sorted(extracted.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            inner = path.relative_to(extracted).as_posix()
            label = f"{relative_chm}!/{inner}"
            if globs and not any(
                fnmatch.fnmatch(path.name, item) or fnmatch.fnmatch(label, item)
                for item in globs
            ):
                continue
            yield path, label


def search_file(
    path: Path, pattern: re.Pattern[str], context: int
) -> list[tuple[int, int, list[str]]]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    matching = [index for index, line in enumerate(lines) if pattern.search(line)]
    if not matching:
        return []

    ranges: list[tuple[int, int]] = []
    for index in matching:
        start = max(0, index - context)
        end = min(len(lines), index + context + 1)
        if ranges and start <= ranges[-1][1]:
            ranges[-1] = (ranges[-1][0], max(ranges[-1][1], end))
        else:
            ranges.append((start, end))
    return [(start + 1, end, lines[start:end]) for start, end in ranges]


def compile_pattern(query: str, fixed: bool, ignore_case: bool) -> re.Pattern[str]:
    expression = re.escape(query) if fixed else query
    return re.compile(expression, re.IGNORECASE if ignore_case else 0)


def require_sdk(explicit: str | None) -> Path:
    roots = discover_sdk_roots(Path(explicit) if explicit else None)
    if not roots:
        raise RuntimeError(
            f"No Wwise SDK found. Add its path to {CONFIG_FILE} or pass --sdk-root."
        )
    return roots[0]


def command_locate(args: argparse.Namespace) -> int:
    roots = discover_sdk_roots(Path(args.sdk_root) if args.sdk_root else None)
    if not roots:
        print(
            f"No Wwise SDK found. Add its path to {CONFIG_FILE} or pass --sdk-root.",
            file=sys.stderr,
        )
        return 1
    selected = roots if args.all else roots[:1]
    for root in selected:
        try:
            version = format_version(read_version(root))
        except (OSError, ValueError) as error:
            version = f"unknown version: {error}"
        print(f"{root}\t{version}")
    return 0


def command_info(args: argparse.Namespace) -> int:
    root = require_sdk(args.sdk_root)
    print(f"SDK root: {root}")
    print(f"Version: {format_version(read_version(root))}")
    for name in ("include", "samples", "source", "Help"):
        print(f"{name}: {'yes' if (root / name).exists() else 'no'}")
    return 0


def command_search(args: argparse.Namespace) -> int:
    root = require_sdk(args.sdk_root)
    try:
        pattern = compile_pattern(args.query, args.fixed, args.ignore_case)
    except re.error as error:
        print(f"Invalid regular expression: {error}", file=sys.stderr)
        return 2

    match_count = 0

    def print_matches(path: Path, relative: str) -> bool:
        nonlocal match_count
        for start, end, lines in search_file(path, pattern, args.context):
            location = str(start) if start == end else f"{start}-{end}"
            print(f"{relative}:{location}")
            for line_number, line in enumerate(lines, start=start):
                print(f"{line_number:>6} | {line}")
            print()
            match_count += 1
            if args.max_results and match_count >= args.max_results:
                return True
        return False

    for path in iter_search_files(root, args.area, args.glob):
        if print_matches(path, path.relative_to(root).as_posix()):
            return 0

    if args.area in ("help", "all"):
        help_roots = read_configured_help_roots()
        for path, relative in iter_extracted_help_files(help_roots, args.glob):
            if print_matches(path, relative):
                return 0

        with tempfile.TemporaryDirectory(prefix="wwise-sdk-help-") as directory:
            try:
                for path, relative in iter_help_files(root, Path(directory), args.glob):
                    if print_matches(path, relative):
                        return 0
            except RuntimeError as error:
                if not help_roots:
                    raise
                print(f"Warning: {error}", file=sys.stderr)
    return 0 if match_count else 1


def command_resolve_url(args: argparse.Namespace) -> int:
    reference = parse_doc_url(args.url)
    root = require_sdk(args.sdk_root)
    local_version = read_version(root)

    print(f"Page: {reference.page}")
    print(f"Library: {reference.library}")
    print(f"Language: {reference.language}")
    if reference.anchor:
        print(f"Anchor: {reference.anchor}")
    print(
        "Documentation version: "
        + (format_version(reference.version) if reference.version else "unspecified")
    )
    print(f"Local SDK: {root}")
    print(f"Local version: {format_version(local_version)}")
    if reference.version and reference.version != local_version:
        print("Warning: the URL version differs from the local SDK version.")

    matches: list[tuple[str, str]] = []
    for kind, path in iter_local_doc_candidates(root, reference):
        if kind == "sdk-chm":
            if not chm_contains_page(path, reference.page):
                continue
            relative = path.relative_to(root).as_posix()
            matches.append((kind, f"{relative}!/{reference.page}.html"))
        else:
            matches.append((kind, str(path)))

    if not matches:
        print(
            f"No local page named {reference.page}.html was found. This page may "
            "belong to a Help package that is not installed. Install it through "
            "Wwise Launcher, or extract the CHM files and add the output "
            f"directories to help_roots in {CONFIG_FILE}.",
            file=sys.stderr,
        )
        return 1

    primary_kind, primary = matches[0]
    print(f"Local page: {primary}")
    for _, alternate in matches[1:]:
        print(f"Also available: {alternate}")

    if primary_kind == "sdk-chm":
        print(
            "Read it with: python scripts/wwise_sdk.py search "
            f'"{reference.anchor or reference.page}" --area help --glob '
            f'"{reference.page}.html"'
        )
    return 0


def find_authoring_help_roots(sdk_root: Path) -> list[Path]:
    """Return installed Authoring contextual Help directories for an SDK."""
    base = sdk_root.parent / AUTHORING_HELP
    if not base.is_dir():
        return []
    return [path for path in sorted(base.iterdir()) if path.is_dir()]


def command_check(args: argparse.Namespace) -> int:
    """Report installed documentation, tooling, and configuration gaps."""
    roots = discover_sdk_roots(Path(args.sdk_root) if args.sdk_root else None)
    missing: list[str] = []

    if not roots:
        print(f"Configuration: {CONFIG_FILE}")
        print("SDK: none configured")
        print(
            f"Action: add your Wwise SDK path to sdk_roots in {CONFIG_FILE}.",
            file=sys.stderr,
        )
        return 1

    print(f"Configuration: {CONFIG_FILE}")
    extractor = find_chm_extractor()
    print(
        "CHM extractor: "
        + (f"{extractor[0]} ({extractor[1]})" if extractor else "not found")
    )
    help_roots = read_configured_help_roots()
    if help_roots:
        for help_root in help_roots:
            state = "ok" if help_root.is_dir() else "missing directory"
            print(f"Configured help_roots: {help_root} ({state})")
            if not help_root.is_dir():
                missing.append(f"help_roots entry does not exist: {help_root}")
    else:
        print("Configured help_roots: none")

    if not extractor and not help_roots:
        missing.append(
            "No CHM extractor and no help_roots. Install 7-Zip or chmlib, or run "
            "extract-help to create an extracted Help directory."
        )

    for root in roots:
        print()
        print(f"SDK: {root}")
        try:
            print(f"Version: {format_version(read_version(root))}")
        except (OSError, ValueError) as error:
            print(f"Version: unknown ({error})")
            missing.append(f"Cannot read the SDK version in {root}")

        for name in ("include", "samples", "source"):
            present = (root / name).is_dir()
            print(f"{name}: {'yes' if present else 'no'}")
            if name == "include" and not present:
                missing.append(
                    f"Missing public headers in {root / name}. API research is "
                    "not possible for this SDK root."
                )
            elif name == "samples" and not present:
                missing.append("No samples: shipped usage patterns cannot be cited.")
            elif name == "source" and not present:
                missing.append(
                    "No source package: implementation detail is unavailable. The "
                    "public API contract is unaffected."
                )

        chm_files = sorted((root / "Help").rglob("*.chm")) if (root / "Help").is_dir() else []
        if chm_files:
            for chm in chm_files:
                print(f"SDK Help: {chm.relative_to(root).as_posix()}")
        else:
            print("SDK Help: none")
            missing.append(
                f"No SDK Help CHM in {root / 'Help'}: official guides and "
                "conceptual pages cannot be quoted. Headers still work."
            )

        authoring = find_authoring_help_roots(root)
        if authoring:
            for path in authoring:
                count = len([item for item in path.rglob("*.html") if item.is_file()])
                print(f"Authoring Help: {path.name} ({count} pages)")
        else:
            print("Authoring Help: none")
            missing.append(
                "No Authoring contextual Help: Authoring documentation URLs "
                "cannot be resolved locally."
            )

    print()
    if missing:
        print("Reduced capability (the skill still works):")
        for item in missing:
            print(f"- {item}")
        print(
            "These gaps only limit which evidence can be cited. Install the "
            "packages you need through Wwise Launcher."
        )
        return 1
    print("No documentation gaps detected.")
    return 0


def command_extract_help(args: argparse.Namespace) -> int:
    """Extract SDK CHM files into a directory and register it in help_roots."""
    root = require_sdk(args.sdk_root)
    help_root = root / "Help"
    chm_files = sorted(help_root.rglob("*.chm")) if help_root.is_dir() else []
    if not chm_files:
        raise RuntimeError(f"No CHM files found in {help_root}")

    if args.language:
        wanted = args.language.lower()
        chm_files = [
            chm
            for chm in chm_files
            if (chm.parent.name.lower() == wanted)
            or (wanted == "en" and chm.parent == help_root)
        ]
        if not chm_files:
            raise RuntimeError(f"No CHM files found for language '{args.language}'")

    destination = Path(args.destination).expanduser()
    if not destination.is_absolute():
        destination = (Path.cwd() / destination).resolve()

    extractor = find_chm_extractor()
    if extractor is None:
        raise RuntimeError(
            "No CHM extractor found. Install 7-Zip (7z, 7zz, or 7za) or chmlib, "
            "or extract the CHM manually and add the directory to help_roots in "
            f"{CONFIG_FILE}."
        )

    for chm in chm_files:
        language = "en" if chm.parent == help_root else chm.parent.name
        output = destination / language / chm.stem
        extract_chm(chm, output, extractor)
        pages = len([item for item in output.rglob("*.html") if item.is_file()])
        print(f"Extracted {chm.relative_to(root).as_posix()} -> {output} ({pages} pages)")

    if args.no_config:
        print(f"Add this directory to help_roots in {CONFIG_FILE}: {destination}")
        return 0

    added = add_help_root(destination)
    print(
        f"{'Added' if added else 'Already present in'} help_roots "
        f"({CONFIG_FILE}): {destination}"
    )
    return 0


def add_help_root(directory: Path, config_path: Path | None = None) -> bool:
    """Add a directory to help_roots, keeping existing configuration intact."""
    config_path = CONFIG_FILE if config_path is None else config_path
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        data = {}
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in {config_path}: {error}") from error
    if not isinstance(data, dict):
        raise ValueError(f"{config_path} must contain a JSON object")

    data.setdefault("sdk_roots", [])
    existing = data.get("help_roots", [])
    if not isinstance(existing, list):
        raise ValueError(f'{config_path} must contain a "help_roots" array of strings')

    value = directory.as_posix()
    normalized = {os.path.normcase(str(item)) for item in existing}
    if os.path.normcase(value) in normalized:
        return False

    data["help_roots"] = [*existing, value]
    config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sdk-root", help="SDK directory or Wwise installation directory"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    locate = subparsers.add_parser("locate", help="discover local SDK installations")
    locate.add_argument("--all", action="store_true", help="print every discovered SDK")
    locate.set_defaults(func=command_locate)

    info = subparsers.add_parser("info", help="show SDK version and available content")
    info.set_defaults(func=command_info)

    search = subparsers.add_parser("search", help="search SDK text files with line numbers")
    search.add_argument("query", help="regular expression, or literal text with --fixed")
    search.add_argument("--area", choices=AREA_PATHS, default="include")
    search.add_argument(
        "--glob", action="append", default=[], help="file glob; may be repeated"
    )
    search.add_argument("--context", type=int, default=2, help="context lines")
    search.add_argument("--fixed", action="store_true", help="treat query as literal text")
    search.add_argument("--ignore-case", action="store_true")
    search.add_argument("--max-results", type=int, default=20)
    search.set_defaults(func=command_search)

    resolve = subparsers.add_parser(
        "resolve-url",
        help="map an Audiokinetic documentation URL to local Help pages",
    )
    resolve.add_argument("url", help="official Wwise documentation URL")
    resolve.set_defaults(func=command_resolve_url)

    check = subparsers.add_parser(
        "check",
        help="report installed documentation, tooling, and configuration gaps",
    )
    check.set_defaults(func=command_check)

    extract = subparsers.add_parser(
        "extract-help",
        help="extract SDK CHM files and register the output in help_roots",
    )
    extract.add_argument("destination", help="directory to extract the Help into")
    extract.add_argument(
        "--language", help="extract only one language, such as en, zh, ja, or ko"
    )
    extract.add_argument(
        "--no-config",
        action="store_true",
        help="do not modify the configuration file",
    )
    extract.set_defaults(func=command_extract_help)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "context", 0) < 0:
        parser.error("--context must be zero or greater")
    if getattr(args, "max_results", 0) < 0:
        parser.error("--max-results must be zero or greater")
    try:
        return args.func(args)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
