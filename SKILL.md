---
name: wwise-sdk-skill
description: Wwise SDK research, resolved against the user's locally installed SDK rather than the web. Fires on an `audiokinetic.com` `library` or `public-library` documentation URL, including a bare URL with no question; a Wwise, Audiokinetic, or WAAPI topic; an `AK`-prefixed symbol or a bare Sound Engine call such as PostEvent or LoadBank; a local Wwise SDK path, header, or CHM Help page. Not for general audio programming or other middleware unless Wwise is named.
license: MIT
---

# Wwise SDK Reference

This skill is **offline**: the installed SDK is the source of truth, and
Audiokinetic's website is never a route to an answer. Audiokinetic blocks
automated access to it, and the local Help package holds the same pages. An API
in one Wwise release is not an API in another, so the inspected installation
decides.

Commands below are written as bare subcommands. Each one runs as
`python <skill>/scripts/wwise_sdk.py <subcommand>`, where `<skill>` is this
skill's own directory, not the user's project. Use the absolute path whenever
the working directory is elsewhere, and `python3` where `python` is absent. The
helper is optional; without it, use the host's file tools in the same order.

## Order Of Operations

Every request runs this chain. Step 1 gates everything else, because every
helper command resolves an SDK root before it does anything:

1. **Resolve the SDK root.** A path the user supplied, then `sdk_roots` in
   `wwise-sdk.config.json`, then `locate`. If none resolves, ask the user for
   the path and stop here. This is the only hard blocker.
2. **Route on what the request carries.**
   - An Audiokinetic documentation URL: run `resolve-url`, then run the
     `search` command it prints. See **Documentation URLs**.
   - Anything else Wwise-specific: see **Research Workflow**.
3. **Answer from what the installed SDK showed**, citing
   `relative/path:line`. See **Answer Gate**.

Run `check` when this is the user's first use, when they ask whether anything
is missing, or when a lookup fails. See **Verifying The Installation**.

## Scope

A mixed question gets a mixed answer: handle the general audio part normally,
and go offline into the SDK only for the Wwise part. A project that already
calls `AkSoundEngine` or ships Wwise integration files counts as naming Wwise,
so its audio questions are Wwise questions.

Where Wwise is genuinely unnamed and unimplied ("how do I do occlusion in my
game?"), answer as an ordinary audio question, or ask which middleware they
use, and leave the SDK closed.

## Resolve The SDK Root

This skill needs a locally installed Wwise SDK and local file access; the
Python helper is optional. Resolve in this order:

1. A path explicitly supplied by the user.
2. Paths listed in `wwise-sdk.config.json` in this skill's installation
   directory.
3. The optional helper:

   ```sh
   locate
   ```

4. Ask the user for the SDK path if discovery fails.

Accept either the SDK directory itself or a Wwise installation directory that
contains `SDK`. Validate it by checking for `include/AK/AkWwiseSDKVersion.h`.
Cite SDK-relative paths only, so a machine-specific path stays out of answers,
configuration, and the repository unless the user explicitly asks for one.

To inspect a specific installation:

```sh
--sdk-root "/path/to/SDK" info
```

### When No SDK Resolves

This repository does not include the Wwise SDK, and installing the skill does
not install it. Tell the user to open **Wwise Launcher**, install or modify the
desired Wwise version with its SDK component included, then copy
`wwise-sdk.config.example.json` to `wwise-sdk.config.json` and add the installed
SDK path to its `sdk_roots` array. That copy is git-ignored, so it keeps
machine-specific paths out of version control.

`sdk_roots` accepts SDK directories, Wwise installation directories containing
`SDK`, or parent directories containing multiple Wwise installations. The
configuration file is the only place the SDK path comes from; environment
variables are not read.

The optional `help_roots` array contains user-managed directories where CHM
files have already been extracted. Search those directories directly when the
question needs Help content. Keep each extracted directory associated with the
matching SDK version, and label every finding with the version it came from.

## Documentation URLs

An Audiokinetic **documentation** URL resolves offline. A URL qualifies when its
host is `audiokinetic.com` or a subdomain such as `www.audiokinetic.com` **and**
its path contains `library` or `public-library`:

- `https://www.audiokinetic.com/zh/public-library/2025.1.10_9233/?source=SDK&id=...`
- `https://www.audiokinetic.com/library/edge/?source=SDK&id=...`

Such a URL alone is enough to activate this skill; the user does not also need to
write "Wwise" or ask a question. Once the SDK root resolves, the offline route is
the first and only attempt on the URL:

```sh
resolve-url "URL"
```

`resolve-url` prints the local page and the ready-to-run `search` command that
reads it. Run that command. `resolve-url` needs a resolved SDK root, so a
missing root surfaces here as a configuration problem; ask for the SDK path and
stop.

When resolution finds no local page, report which Help package is missing along
with the version information the URL yielded. That report is the answer; the
page stays unquoted rather than reconstructed.

For the URL-to-page mapping rules (`id`, language, version, and `source`
segments), see `references/research-guide.md`.

### Non-Documentation Audiokinetic URLs

Everything else on the site is not Wwise documentation and has no local
counterpart: `/community/` (including Q&A, blog, and forum pages), `/products/`,
`/pricing/`, `/news/`, `/events/`, `/courses/`, and marketing pages.
`resolve-url` rejects these paths on purpose.

For such a URL, say that the link is not documentation, so this skill cannot
resolve it locally, and hand it to the host's normal rules for web links. If the
user actually wants API or concept documentation, ask for the corresponding
`library` or `public-library` link, or search the installed SDK by topic.

## Research Workflow

1. Run `info` or read `include/AK/AkWwiseSDKVersion.h`; state the inspected
   version when version differences matter.
2. Search `include/AK` first for declarations and nearby comments. Read every
   signature and enum value out of these headers rather than recalling them,
   confirming parameters, result codes, ownership rules, thread restrictions,
   platform guards, and deprecation notes, because they
   define the public API contract that the selected SDK can compile against.
3. Search `Help` for the locally installed official SDK documentation
   (`Help/*.chm` and localized variants such as `Help/zh/*.chm` on Windows)
   with `search "QUERY" --area help --fixed`. The
   helper first searches configured `help_roots`, then temporarily extracts
   installed CHM files with `hh.exe`, 7-Zip, or chmlib when available. Prefer
   the user's language when multiple localized files exist. See
   `references/research-guide.md` for manual extraction and platform details.
   Use Help to add official concepts, workflows, and explanations around the
   header contract.
4. Search `samples` for supported integration and usage patterns. Examples
   illustrate intended use but do not override declarations or Help.
5. Search the SDK `source` tree only when implementation detail is necessary
   and the directory exists. It is the Wwise implementation source package,
   installed only for users with source access; its absence still leaves a valid
   SDK, and internal behavior stays distinct from the public API contract.
6. Only after the installed SDK documentation, consult other content such as
   the user's integration code, repository documentation, or clearly labeled
   inference. Where local evidence is missing, say so and stop there.
7. Compare multiple SDK roots explicitly for migration or compatibility
   questions, labelling every finding with the version it came from.

When evidence conflicts, report the discrepancy. For the exact API that can be
compiled, the selected version's public headers take precedence; Help explains
documented behavior, samples demonstrate usage, and source reveals only
version-specific implementation details.

The research is done when every claim in the answer carries a
`relative/path:line` citation from the inspected installation, every overload
and enum member the question touches is accounted for, and every unavailable
package is named. An uncited claim is an unfinished step, not a caveat. Work
through `references/research-guide.md`'s answer quality checklist before
answering.

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

Exit codes separate an empty result from a broken command, so read them before
concluding anything about the SDK:

| Code | Meaning | Next step |
| --- | --- | --- |
| 0 | The command succeeded and printed its findings | Use the output |
| 1 | Nothing to report, or the setup is short something. Covers a `search` with no match, an unresolvable SDK root, a `check` that found gaps, a page whose Help package is absent, and a rejected non-documentation URL | Read the message on stderr, which says which of these happened. A `search` miss means try another query, `--area`, or `--fixed`; the others are setup or scope facts to report |
| 2 | The command itself was wrong: an invalid regular expression, or a bad flag | Fix the command and retry. For a literal symbol, add `--fixed` |

Exit 1 never means the API is absent from the SDK. It means this command found
nothing, which is a claim about the search, not about Wwise.

Example searches:

```sh
search "PostEvent" --area include --fixed --context 4
search "AK::SoundEngine::RegisterGameObj" --area include --fixed
search "AK_InvalidParameter" --area include --fixed
search "PostEvent" --area help --fixed --ignore-case
search "CAkSoundEngine" --area source --fixed --glob "*.cpp"
search "Set(RTPCValue|State|Switch)" --area include --max-results 60
```

If the helper is unavailable, use the host's normal file search tools with the
same search order. See `references/topic-map.md` for likely entry points, and
`references/research-guide.md` for evidence and citation guidance.

## Answer Gate

Prefer this compact structure:

1. Direct answer.
2. Confirmed signature or behavior.
3. Minimal example, if useful, adapted to the inspected version.
4. Version and local citations.
5. Caveats, uncertainties, and absent packages.

`references/research-guide.md` holds the answer quality checklist and the
citation format. Both are the gate the completion criterion above refers to.

## Verifying The Installation

Run the check on first use, when the user asks whether anything is missing, or
when a lookup fails:

```sh
check
```

Report the detected SDK and version, which packages are installed, whether a
CHM extractor exists, and any gap the command lists. Point the user at Wwise
Launcher to install the missing packages.

A missing package is a capability limit, not a failure. Continue working with
what is installed and state plainly which kind of evidence is unavailable:

- No `include`: stop and ask for a valid SDK path. This is the only hard blocker.
- No SDK Help CHM: answer from headers and samples; official guides and
  conceptual pages cannot be quoted.
- No Authoring Help: Authoring documentation URLs cannot be resolved locally.
- No `samples`: no shipped usage patterns to cite.
- No `source`: no implementation detail; the public API contract is unaffected.
- No CHM extractor: Help search requires a pre-extracted `help_roots` directory.

The skill still works with gaps. Answers stay offline: name the absent package
as the limit of the answer.

### Persistently Extracting CHM Help

If the user wants faster or repeated Help access, or the host has no CHM
extractor at query time, extract the CHM once and register the output:

```sh
extract-help "/path/to/HelpExtracted" --language zh
```

This writes the directory into `help_roots` so the extracted HTML can be read
with normal file tools afterwards. Ask the user where to place the output, and
use a separate directory per SDK version, outside this skill's repository. Use
`--no-config` when the user does not want the configuration changed.

## Boundaries

- Keep this skill to Wwise. General game audio, audio programming, and
  non-Wwise middleware are answered normally, without opening the SDK. See
  **Scope**.
- Answer documentation questions offline, from the installed Help package. When
  a page is absent, name the missing package. Audiokinetic's site is not a
  fallback for any of it, so leave `webfetch`, web search, a browser, `curl`,
  and `wget` out of the route even when they are available.
- Treat non-documentation Audiokinetic pages (community, blog, product, pricing)
  as ordinary web links with no local counterpart.
- Keep usernames, absolute home paths, license keys, project secrets, and
  unrelated local files out of the answer.
- Do not copy or publish Wwise SDK headers, libraries, samples, Help files, or
  other proprietary files. Quote only the small fragment needed to explain an
  API, and direct the user to their local installation.
- Keep CHM extraction temporary and local to research. Do not retain, index in
  the repository, or redistribute the extracted HTML.
- Wwise and its SDK remain subject to Audiokinetic's terms; this skill's MIT
  license covers only the skill itself.
