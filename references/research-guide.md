# Research And Citation Guide

## Evidence Priority

Use the installed SDK evidence in this order:

1. Public headers and header comments for exact API contracts, signatures,
   parameters, return values, lifecycle, threading, and platform guards.
2. Local `Help/*.chm` documentation for official guides, API reference pages,
   conceptual explanations, and website-equivalent SDK documentation.
3. Shipped samples for intended integration patterns.
4. The complete installed `source` tree, only when needed, for Wwise
   implementation behavior that is not part of the public contract. This source
   package is available only to users with the corresponding source access.
5. Other local content, such as the user's integration code or repository
   documentation, followed only when necessary by clearly labeled inference.

Treat source implementation details as version-specific and potentially
unstable. Do not present them as public API guarantees unless headers or Help
also establish the behavior. If evidence conflicts, report the discrepancy and
use the selected SDK version's public headers for the exact compilable API.

## Searching Well

- Start with an exact symbol in SDK headers, then broaden to related types or
  concepts.
- After headers, search Help and samples before consulting source, project
  files, or other content.
- Search declarations and comments together.
- Inspect overloads, default arguments, macros, typedefs, and platform guards.
- Check callback type definitions and result enums referenced by a signature.
- Search samples using both the API name and its associated feature name.
- Search `Help` after confirming the header contract: `python
  scripts/wwise_sdk.py search QUERY --area help`. The helper searches
  configured, manually extracted `help_roots` first. It then temporarily
  extracts installed CHM files with Windows
  `hh.exe`, 7-Zip (`7z`, `7zz`, or `7za`), or chmlib's `extract_chmLib` when
  available. Temporary output is deleted after the search.
- For maximum portability, manually extract each SDK version's CHM files into
  a separate directory and add that directory to `help_roots` in
  `wwise-sdk.config.json`. The extracted HTML can then be read with normal file
  tools on Windows, macOS, and Linux without a CHM reader.
- When `source` exists, search it recursively as the Wwise implementation
  source tree, including installed Sound Engine, Spatial Audio, Stream Manager,
  platform, and build components. It is not merely a collection of examples.
- Treat `source` as a source-access package. Check that it exists before
  searching and state when implementation evidence is unavailable. Its absence
  does not make the public SDK incomplete or invalid.
- For migrations, run the same search against each SDK separately and label
  every finding with its version.

## Setup Verification

Run `python scripts/wwise_sdk.py check` on first use, when the user asks whether
documentation is missing, or when a Help lookup fails. It reports the SDK
version, installed packages, SDK Help CHM files, Authoring Help languages, CHM
extractor availability, and invalid `help_roots` entries, then exits non-zero
when something is missing.

A non-zero exit means reduced coverage, not a broken setup. Only a missing
`include` directory blocks research. For every other gap, continue with the
available evidence and name the limitation: absent Help removes official guides,
absent `samples` removes shipped usage patterns, absent `source` removes
implementation detail, and an absent extractor requires a pre-extracted
`help_roots` directory.

To make Help lookups persistent, extract once and register the output:

```sh
python scripts/wwise_sdk.py extract-help "/path/to/HelpExtracted" --language zh
```

Use one directory per SDK version, keep it outside this repository, and rely on
`--no-config` when the configuration must stay untouched.

## Official Documentation URLs

Never fetch `audiokinetic.com`. Resolve a provided URL to its local page:

```sh
python scripts/wwise_sdk.py resolve-url "URL"
```

Mapping rules:

| URL part | Meaning |
| --- | --- |
| `id=soundengine_events` | local file `soundengine_events.html` |
| `/zh/`, `/en/`, `/ja/`, `/ko/` | localized Help directory |
| `2025.1.10_9233` | documented version, compare with the local SDK |
| `source=SDK` | SDK documentation rather than Authoring documentation |

SDK pages are stored inside `SDK/Help/**/WwiseSDK-Windows.chm`. Authoring pages
are stored as plain HTML under `Authoring/Help/Contextual Help/<language>/`, or
in directories listed in `help_roots`. Read a resolved CHM page with a glob:

```sh
python scripts/wwise_sdk.py search "QUERY" --area help --glob "soundengine_events.html"
```

Cite resolved pages as `Help/zh/WwiseSDK-Windows.chm!/soundengine_events.html`.
State the local version, and warn when it differs from the documented version.

## Citation Format

Prefer SDK-relative locations:

```text
include/AK/SoundEngine/Common/AkSoundEngine.h:1234-1268
samples/IntegrationDemo/Common/DemoApp.cpp:90
```

Relative paths are portable and avoid leaking the user's home directory. Add
the detected version nearby, for example `Wwise SDK 2025.1.7 build 9143`.

If line numbers come from generated files or differ across package variants,
also include the symbol name. Do not cite only a search-result line when the
relevant contract spans a larger comment and declaration block.

## Answer Quality Checklist

- Is the installed SDK version identified?
- Was the exact signature read rather than recalled?
- Are overload selection and default arguments explained?
- Are relevant return codes, ownership, threading, and lifetime constraints
  included?
- Does the example compile conceptually against the inspected version?
- Are facts distinguished from recommendations?
- Are all citations relative and navigable?
- Are uncertainties and absent packages stated explicitly?

## Safe Quoting

Wwise SDK files are not distributed under this repository's MIT license. Avoid
large excerpts. Quote only the declaration or short comment fragment necessary
for the answer, then cite the user's local copy. Never commit copied headers,
libraries, samples, documentation, or generated SDK indexes to this project.
