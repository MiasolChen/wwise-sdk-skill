---
name: wwise-sdk-skill
description: Use whenever the user provides an Audiokinetic documentation URL under `audiokinetic.com/.../library/` or `.../public-library/`, including a bare URL with no question; do not fetch or search that website, and resolve its documentation page against the locally installed Wwise SDK instead. Other `audiokinetic.com` paths such as `/community/`, `/blog/`, or `/products/` are not documentation and are out of scope. Also use for Wwise, Audiokinetic, WAAPI, Wwise Launcher, SoundBank, Wwise Event, RTPC, Game Object, Wwise Spatial Audio, `AK::` or `Ak` symbols such as PostEvent, RegisterGameObj, SetRTPCValue, LoadBank, AKRESULT, IAkEffectPlugin, or a local Wwise SDK path, header, or CHM Help page. Do NOT use for general audio programming or other middleware unless Wwise is explicitly involved.
license: MIT
compatibility: Requires a locally installed Wwise SDK and local file access. Python 3.9+ is optional.
metadata:
  author: Miasol
  version: "1.1.0"
---

# Wwise SDK Reference

Use the user's installed Wwise SDK as the source of truth. Do not assume that
an API from one Wwise release exists or has the same signature in another.

## Mandatory URL Routing

Only Audiokinetic **documentation** URLs route to this workflow. A URL qualifies
when its host is `audiokinetic.com` or a subdomain such as `www.audiokinetic.com`
**and** its path contains a documentation segment:

- `https://www.audiokinetic.com/zh/public-library/2025.1.10_9233/?source=SDK&id=...`
- `https://www.audiokinetic.com/library/edge/?source=SDK&id=...`

Such a URL alone is enough to activate this skill; the user does not also need to
write "Wwise" or ask a question. The first action must be local resolution:

```sh
python scripts/wwise_sdk.py resolve-url "URL"
```

Do not call `webfetch`, a web-search tool, `curl`, `wget`, a browser tool, or
any other network retrieval method for that URL, even if one is available.
Do not try the website first and fall back to local content only after it
fails. `resolve-url` and the installed SDK Help are the primary route.

After resolving the URL, `resolve-url` prints the exact `search` command for the
matching local page. Run that command to read the page. If local resolution
fails, report the missing local SDK or Help package and the URL/version
information that could be parsed. Do not fetch the website as a fallback and do
not reconstruct its content from memory.

### Non-Documentation Audiokinetic URLs

Everything else on the site is not Wwise documentation and has no local
counterpart: `/community/` (including Q&A, blog, and forum pages), `/products/`,
`/pricing/`, `/news/`, `/events/`, `/courses/`, and marketing pages.
`resolve-url` rejects these paths on purpose.

For such a URL, do not run `resolve-url` and do not invent local evidence. Say
that the link is not documentation, so this skill cannot resolve it locally, and
handle it with the host's normal rules for web links. If the user actually wants
API or concept documentation, ask for the corresponding `library` or
`public-library` link, or search the installed SDK by topic instead.


## When To Use This Skill

Activate only when the request is Wwise-specific. Require at least one explicit
signal:

- The words `Wwise`, `Audiokinetic`, `WAAPI`, or `Wwise Launcher`.
- A Wwise product concept named as such: SoundBank, Wwise Event, RTPC, Switch,
  State, Game Object, Listener, Auxiliary Send, Wwise Spatial Audio, Room,
  Portal, Actor-Mixer, Music Segment, Dynamic Dialogue.
- An SDK symbol, typically `AK::`, `Ak`, `AK_`, or `IAk` prefixed, for example
  `PostEvent`, `RegisterGameObj`, `SetRTPCValue`, `LoadBank`, `AKRESULT`,
  `AkPlayingID`, `IAkEffectPlugin`.
- A local Wwise SDK path, header, or `Help/*.chm` page.
- An Audiokinetic documentation URL, that is an `audiokinetic.com` link whose
  path contains `library` or `public-library`. A bare URL is sufficient and
  always routes to the local SDK workflow in **Mandatory URL Routing**. Other
  `audiokinetic.com` paths, such as `/community/` or `/blog/`, are not
  documentation and are not a trigger.


See `references/trigger-terms.md` for the full term list.

Do not activate for general audio work that never names Wwise:

- General game audio design, mixing, mastering, loudness, or sound design.
- Generic audio programming: DSP, FFT, convolution, resampling, ring buffers,
  audio callbacks, sample rates, channel layouts.
- Other engines and middleware: FMOD, CRIWARE, Unity `AudioSource` or
  `AudioMixer`, Unreal MetaSounds, Web Audio API, XAudio2, WASAPI, PortAudio.
- Terms that only sound Wwise-related out of context: "spatial audio",
  "occlusion", "reverb", "3D audio", "event", "bus", "attenuation".

Ambiguous cases:

- "How do I do occlusion in my game?" is generic. Answer normally, or ask
  whether the user is using Wwise. Do not open the SDK unprompted.
- "How do I do occlusion in Wwise?" is Wwise-specific. Use this skill.
- If a project clearly integrates Wwise, for example it contains `AkSoundEngine`
  calls or `Wwise` integration files, treat that as an explicit signal.

When a question mixes both, answer the general part normally and use this skill
only for the Wwise-specific part. Do not volunteer that this skill exists for
non-Wwise audio questions.

## Prerequisite: Install The Wwise SDK First

Before using this skill, require the user to download and install the SDK for
their Wwise version through **Wwise Launcher**. This repository does not include
the Wwise SDK, and installing the skill does not install it.

If no local SDK can be found, tell the user to open Wwise Launcher, install or
modify the desired Wwise version, and include its SDK component. Then ask them
to copy `wwise-sdk.config.example.json` to `wwise-sdk.config.json` and add the
installed SDK path to its `sdk_roots` array. That copy is git-ignored, so it
keeps machine-specific paths out of version control. Do not proceed by
guessing API details from memory.

Audiokinetic does not permit automated bot searches or scraping of its
web-based Wwise SDK documentation and uses bot-detection measures. This skill
exists so agents can research the installed SDK locally instead of attempting
to search the official documentation website.

## First Use: Check For Missing Documentation

When the user first uses this skill, asks whether anything is missing, or a
lookup fails, run the check:

```sh
python scripts/wwise_sdk.py check
```

Report the detected SDK and version, which packages are installed, whether a
CHM extractor exists, and any gap the command lists. Ask the user to install
missing packages through Wwise Launcher rather than answering from memory.

A missing package is a capability limit, not a failure. Continue working with
what is installed and state plainly which kind of evidence is unavailable:

- No `include`: stop and ask for a valid SDK path. This is the only hard blocker.
- No SDK Help CHM: answer from headers and samples; official guides and
  conceptual pages cannot be quoted.
- No Authoring Help: Authoring documentation URLs cannot be resolved locally.
- No `samples`: no shipped usage patterns to cite.
- No `source`: no implementation detail; the public API contract is unaffected.
- No CHM extractor: Help search requires a pre-extracted `help_roots` directory.

Do not tell the user that the skill is broken or unusable because of these gaps,
and do not fill them in from memory.

## Persistently Extracting CHM Help

If the user wants faster or repeated Help access, or the host has no CHM
extractor at query time, extract the CHM once and register the output:

```sh
python scripts/wwise_sdk.py extract-help "/path/to/HelpExtracted" --language zh
```

This writes the directory into `help_roots` so the extracted HTML can be read
with normal file tools afterwards. Ask the user where to place the output, use a
separate directory per SDK version, and never place it inside this skill's
repository. Use `--no-config` when the user does not want the configuration
changed.

## Locate The SDK

Resolve the SDK root in this order:

1. A path explicitly supplied by the user.
2. Paths listed in `wwise-sdk.config.json` in this skill's installation
   directory.
3. The optional helper:

   ```sh
   python scripts/wwise_sdk.py locate
   ```

4. Ask the user for the SDK path if discovery fails.

The user must fill in the configuration file manually, copying
`wwise-sdk.config.example.json` to `wwise-sdk.config.json` first. Its
`sdk_roots` array
accepts SDK directories, Wwise installation directories containing `SDK`, or
parent directories containing multiple Wwise installations. Do not use an
environment variable for the SDK path.

The optional `help_roots` array contains user-managed directories where CHM
files have already been extracted. Search those directories directly when the
question needs Help content. Keep each extracted directory associated with the
matching SDK version and never combine evidence from different releases.

Helper paths such as `scripts/wwise_sdk.py` are relative to this skill's
installation directory, not the user's project. Invoke the script with an
absolute path when the working directory is elsewhere, and use `python3` when
`python` is unavailable on the host.

Accept either the SDK directory itself or a Wwise installation directory that
contains `SDK`. Validate it by checking for
`include/AK/AkWwiseSDKVersion.h`. Never write a machine-specific path into an
answer, configuration, or repository unless the user explicitly requests it.

To inspect a specific installation:

```sh
python scripts/wwise_sdk.py --sdk-root "/path/to/SDK" info
```

## Official Documentation URLs

When the user provides an Audiokinetic documentation URL, including a bare link
with no surrounding request, do not fetch it. The site blocks automated access.
Map it to the local page instead:

```sh
python scripts/wwise_sdk.py resolve-url "URL"
```

The URL carries everything needed for the mapping:

- The path must contain `library` or `public-library`; other paths are not
  documentation and are rejected.
- `id` is the local HTML file name, for example `id=soundengine_events` maps to
  `soundengine_events.html`.
- The path language segment (`en`, `zh`, `ja`, `ko`) selects the localized Help.
- The version segment such as `2025.1.10_9233` is the documented version. Report
  a mismatch with the local SDK instead of assuming the content is identical.
  `library/edge` has no version segment, so compare nothing and state that the
  link targets the latest online documentation.
- `source` distinguishes SDK documentation from Authoring documentation.

SDK pages live inside `SDK/Help/**/WwiseSDK-Windows.chm`. Authoring pages live
under `Authoring/Help/Contextual Help/<language>/` or in extracted directories
listed in `help_roots`. `resolve-url` prints the ready-to-run command for the
page it resolved; it has the shape:

```sh
python scripts/wwise_sdk.py search "QUERY" --area help --fixed --glob "soundengine_events.html"
```

If the page is not installed locally, say so and state which Help package is
missing rather than reconstructing the page from memory.

If `resolve-url` reports that the link is not a documentation URL, the link
points at other website content such as `/community/` or `/blog/`. There is no
local equivalent, so do not substitute one. See **Non-Documentation
Audiokinetic URLs** above.


## Research Workflow

1. Run `info` or read `include/AK/AkWwiseSDKVersion.h`; state the inspected
   version when version differences matter.
2. Search `include/AK` first for declarations and nearby comments. Use headers
   to confirm exact signatures, parameters, result codes, ownership rules,
   thread restrictions, platform guards, and deprecation notes because they
   define the public API contract that the selected SDK can compile against.
3. Search `Help` for the locally installed official SDK documentation
   (`Help/*.chm` and localized variants such as `Help/zh/*.chm` on Windows)
   with `python scripts/wwise_sdk.py search "QUERY" --area help --fixed`. The
   helper first
   searches configured `help_roots`, then temporarily extracts installed CHM
   files with `hh.exe`, 7-Zip, or chmlib when available. Prefer the user's
   language when multiple localized files exist. See `references/research-guide.md`
   for manual extraction and platform details. Use Help to add official
   concepts, workflows, and explanations around the header contract.
4. Search `samples` for supported integration and usage patterns. Examples
   illustrate intended use but do not override declarations or Help.
5. Search the SDK `source` tree only when implementation detail is necessary
   and the directory exists. It is the Wwise implementation source package,
   installed only for users with source access; never treat its absence as an
   invalid SDK, and distinguish internal behavior from the public API contract.
6. Only after the installed SDK documentation, consult other content such as
   the user's integration code, repository documentation, or clearly labeled
   inference. Never use general knowledge to replace missing local evidence.
7. Compare multiple SDK roots explicitly for migration or compatibility
   questions. Never blend evidence from different versions.

When evidence conflicts, report the discrepancy. For the exact API that can be
compiled, the selected version's public headers take precedence; Help explains
documented behavior, samples demonstrate usage, and source reveals only
version-specific implementation details.

### Using `search` Correctly

Two defaults decide whether a search returns the truth:

- **`query` is a regular expression.** Pass `--fixed` for any literal symbol,
  which covers almost every SDK identifier: `AK::SoundEngine`, `operator[]`,
  `AkInitSettings*`, `AK_IMPLEMENT_PLUGIN_FACTORY`. Without `--fixed` these
  either fail as invalid patterns or match the wrong text. Reserve bare regex
  for deliberate patterns such as `Set(RTPCValue|State|Switch)`.
- **`--max-results` defaults to 20 and truncates silently.** Raise it when
  enumerating overloads, enum members, or call sites. A truncated result set
  looks identical to a complete one, so treat hitting the limit as unfinished
  evidence rather than a finding.

Example searches:

```sh
python scripts/wwise_sdk.py search "PostEvent" --area include --fixed --context 4
python scripts/wwise_sdk.py search "AK::SoundEngine::RegisterGameObj" --area include --fixed
python scripts/wwise_sdk.py search "AK_InvalidParameter" --area include --fixed
python scripts/wwise_sdk.py search "PostEvent" --area help --fixed --ignore-case
python scripts/wwise_sdk.py search "CAkSoundEngine" --area source --fixed --glob "*.cpp"
python scripts/wwise_sdk.py search "Set(RTPCValue|State|Switch)" --area include --max-results 60
```

If the helper is unavailable, use the host's normal file search tools with the
same search order. See `references/topic-map.md` for likely entry points,
`references/trigger-terms.md` for the terms that make a request Wwise-specific,
and `references/research-guide.md` for evidence and citation guidance.

## Answer Requirements

- Confirm exact signatures and enum values from the installed headers. Never
  reconstruct them from memory.
- Cite evidence as `relative/path:line` or `relative/path:start-end` so the
  result remains useful on another machine.
- Separate facts found in the SDK from recommendations or inference.
- Include a minimal usage example when it helps, adapted to the inspected SDK
  version rather than copied blindly from a different release.
- Mention lifecycle, ownership, threading, callback, and return-value concerns
  when the local comments make them relevant.
- If evidence is missing or ambiguous, say what was searched and what could
  not be confirmed.
- Do not expose usernames, absolute home paths, license keys, project secrets,
  or unrelated local files.

## Boundaries

- Do not activate for general game audio, audio programming, or non-Wwise
  middleware questions. See the activation rules above and
  `references/trigger-terms.md`.
- Do not search, scrape, or fetch Audiokinetic's web-based SDK documentation.
  The site uses bot detection and does not permit automated bot access. Explain
  this restriction and use the local SDK instead.
- Do not treat non-documentation Audiokinetic pages, such as community, blog,
  product, or pricing pages, as SDK documentation, and do not answer them from
  local Help content.
- Do not copy or publish Wwise SDK headers, libraries, samples, Help files, or
  other proprietary files. Quote only the small fragment needed to explain an
  API and direct the user to their local installation.
- CHM extraction must be temporary and used only for local research. Do not
  retain, index in the repository, or redistribute the extracted HTML.
- Do not claim that this skill or its MIT license applies to Wwise. Wwise and
  its SDK remain subject to Audiokinetic's terms.

## Response Shape

Prefer this compact structure:

1. Direct answer.
2. Confirmed signature or behavior.
3. Minimal example, if useful.
4. Version and local citations.
5. Caveats or unresolved points.
