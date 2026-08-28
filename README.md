# Wwise SDK Skill

An Agent Skill for version-accurate Wwise SDK research using locally installed
headers, samples, Help files, and source code.

[中文](README.zh-CN.md)

> [!IMPORTANT]
> Install the SDK component for your Wwise version through **Wwise Launcher**
> first. This repository does not include the Wwise SDK.

## Features

- Verify API signatures, parameters, and return values from local headers.
- Find practical usage in samples, Help files, and available source code.
- Report the inspected SDK version with relative file and line references.
- Cover Sound Engine, Spatial Audio, plug-ins, WAAPI, callbacks, streaming,
  and other SDK topics.

The Skill uses the installed SDK because Wwise APIs vary between releases and
the official web documentation cannot be reliably accessed by automated agents.
It activates only for Wwise-specific questions and stays out of the way for
general game audio topics.

## Documentation Lookup Order

The Skill uses local evidence in this order:

1. **SDK version and public headers (`include/AK`)**: establish which release is
   being inspected and confirm the exact API contract that can be compiled,
   including signatures, enums, defaults, ownership, and threading constraints.
2. **Local SDK Help**: supplies official explanations, concepts, workflows, and
   API-reference context around the declarations.
3. **Shipped samples**: demonstrate intended integration patterns, but do not
   override the headers or Help.
4. **Installed `source`**: consulted only when implementation details are
   necessary. Internal behavior is version-specific and is not a public API
   guarantee.
5. **Project files or other information**: used only after the installed SDK
   evidence and clearly separated from confirmed SDK facts.

This order matters because the selected version's headers are the definitive
record of what that installation exposes to C++ code. Help is better suited to
meaning and workflow, samples to practical usage, and source to internal
behavior. If these sources disagree, the Skill reports the discrepancy and
uses the installed public headers for the exact compilable API.

## Installation

Clone the repository into a Skill directory supported by your AI tool:

| Tool | Global directory | Project directory |
| --- | --- | --- |
| OpenCode | `~/.config/opencode/skills/wwise-sdk-skills/` | `.opencode/skills/wwise-sdk-skills/` |
| Claude Code | `~/.claude/skills/wwise-sdk-skills/` | `.claude/skills/wwise-sdk-skills/` |
| Codex / Agent Skills | `~/.agents/skills/wwise-sdk-skills/` | `.agents/skills/wwise-sdk-skills/` |

Example for a global OpenCode installation:

```sh
git clone https://github.com/MiasolChen/wwise-sdk-skills ~/.config/opencode/skills/wwise-sdk-skills
```

Windows PowerShell:

```powershell
git clone https://github.com/MiasolChen/wwise-sdk-skills "$HOME\.config\opencode\skills\wwise-sdk-skills"
```

Restart or reload the AI tool after installation.

## Configuration

Open `wwise-sdk.config.json` in the installed Skill directory and add your SDK
path manually:

```json
{
  "sdk_roots": [
    "C:/path/to/Wwise/SDK"
  ],
  "help_roots": []
}
```

Each entry may point to an SDK directory, a Wwise installation containing an
`SDK` directory, or a parent directory containing multiple Wwise installations.
Use forward slashes or escaped backslashes in JSON. The Skill does not read SDK
paths from environment variables.

## First-Time Check

After configuring the SDK path, ask your AI to verify that nothing is missing:

```text
Check my local Wwise SDK setup and report any missing documentation.
```

Or run it directly:

```sh
python scripts/wwise_sdk.py check
```

It reports the detected SDK and version, whether `include`, `samples`, and
`source` exist, which SDK Help CHM files and Authoring Help languages are
installed, whether a CHM extractor is available, and whether every configured
`help_roots` directory exists. Missing items are listed at the end and the
command exits with a non-zero status.

Missing documentation does not break the Skill. As long as `include` is present,
API research keeps working; the gaps only narrow what can be answered. For
example:

| Missing item | Effect |
| --- | --- |
| SDK Help CHM | No official guides or conceptual pages; headers still work. |
| Authoring Help | Authoring documentation URLs cannot be resolved locally. |
| `samples` | No usage examples from shipped integrations. |
| `source` | No implementation detail; the public API contract is unaffected. |
| CHM extractor | Help search needs a pre-extracted `help_roots` directory. |

Install what you need through Wwise Launcher only when you want that capability.

## CHM Help

Both Help workflows are supported:

- **Temporary extraction:** `search --area help` finds CHM files under the
  selected SDK and extracts them into a temporary directory. It uses `hh.exe`
  on Windows, or an installed `7z`, `7zz`, `7za`, or `extract_chmLib` command
  on any system. The temporary files are deleted after the search.
- **Persistent extraction:** extract the CHM files once into a directory and
  register it in `help_roots`. The AI can then read the extracted HTML directly
  with normal file tools, which is faster and works on every system.

Ask your AI to do the persistent extraction for you:

```text
Extract my Wwise SDK CHM Help into a local directory and add it to help_roots.
```

Or run it directly:

```sh
python scripts/wwise_sdk.py extract-help "C:/Wwise/Wwise2025/HelpExtracted" --language zh
```

The command extracts the CHM files, prints the page count, and appends the
directory to `help_roots` in `wwise-sdk.config.json`. Use `--no-config` to skip
the configuration update, and omit `--language` to extract every language.

Resulting configuration:

```json
{
  "sdk_roots": ["C:/Wwise/Wwise2025/SDK"],
  "help_roots": ["C:/Wwise/Wwise2025/HelpExtracted"]
}
```

Common extraction commands:

```powershell
# Windows with 7-Zip
7z x "C:\Wwise\Wwise2025\SDK\Help\WwiseSDK-Windows.chm" -o"C:\Wwise\Wwise2025\HelpExtracted"
```

```sh
# macOS/Linux with 7-Zip
7zz x /path/to/WwiseSDK-Windows.chm -o/path/to/HelpExtracted

# Linux with chmlib
extract_chmLib /path/to/WwiseSDK-Windows.chm /path/to/HelpExtracted
```

Then add the output directory to `help_roots`. Keep extracted Help directories
separate for each SDK version, and configure only the directories that
correspond to the SDK being researched. Do not add the extracted proprietary
documentation to this repository.

## Usage

Ask your AI tool directly after installation:

```text
Which PostEvent overloads exist in my local Wwise SDK?

How should I register and unregister a Game Object? Cite the local headers.

Compare the Spatial Audio API in two locally installed SDK versions.
```

You may provide a path in the prompt for a one-off query:

```text
Use D:\Wwise\Wwise2025\SDK to explain PostEvent callbacks and cite the relevant header lines.
```

## Official Documentation URLs

Wwise's documentation site blocks automated access, so the Skill maps an
official URL to the matching local page instead of fetching it:

```sh
python scripts/wwise_sdk.py resolve-url "https://www.audiokinetic.com/zh/public-library/2025.1.8_9170/?source=SDK&id=soundengine_events"
```

```text
Page: soundengine_events
Library: sdk
Language: zh
Documentation version: 2025.1.8 build 9170
Local SDK: C:\Wwise\Wwise2025\SDK
Local version: 2025.1.8 build 9170
Local page: Help/zh/WwiseSDK-Windows.chm!/soundengine_events.html
```

The URL's `id` matches the local HTML file name, the language segment selects
the localized Help, and the version segment is compared against your installed
SDK so version differences are reported. Both documentation paths are accepted,
`/public-library/<version>/` and the unversioned `/library/edge/`. You can also
just paste the URL into your prompt and let the AI resolve it. An Audiokinetic
documentation URL by itself is a Skill trigger: the AI should run `resolve-url`
first and must not call a web-fetch or web-search tool for the URL.

Only documentation URLs are in scope. Other pages on the same host, such as
`/community/`, `/blog/`, `/products/`, or `/pricing/`, are not Wwise
documentation and have no local counterpart, so `resolve-url` rejects them
rather than resolving them to an unrelated Help page.

## Optional Python Helper

Python is not required for the Skill. Python 3.9+ is needed only to use the
optional command-line helper:

```sh
python scripts/wwise_sdk.py locate
python scripts/wwise_sdk.py info
python scripts/wwise_sdk.py check
python scripts/wwise_sdk.py extract-help "/path/to/HelpExtracted" --language zh
python scripts/wwise_sdk.py search PostEvent --area include --context 3
python scripts/wwise_sdk.py search PostEvent --area help --ignore-case
python scripts/wwise_sdk.py resolve-url "https://www.audiokinetic.com/en/public-library/2025.1.8_9170/?source=SDK&id=soundengine_events"
```

## License

The original files in this repository are available under the [MIT License](LICENSE).
Wwise and its SDK remain subject to Audiokinetic's applicable license terms.
