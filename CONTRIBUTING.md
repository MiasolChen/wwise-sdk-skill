# Contributing

Contributions should improve portability, evidence quality, or compatibility
without redistributing Audiokinetic files.

## Development

Requirements:

- Python 3.9 or newer. CI covers 3.9 through 3.13 on Linux, Windows, and macOS.
- A local Wwise SDK only for integration testing.

Run the unit tests:

```sh
python -m unittest discover -s tests -v
```

Run an integration smoke test against your own installation:

```sh
python scripts/wwise_sdk.py --sdk-root "/path/to/SDK" info
python scripts/wwise_sdk.py --sdk-root "/path/to/SDK" search "PostEvent" --fixed --context 1 --max-results 1
```

## Pull Requests

- Keep `SKILL.md` concise; move detailed lookup material into `references`.
- Use only Python's standard library unless a dependency has a compelling,
  documented benefit.
- Add tests for discovery or parsing changes.
- Keep examples free of usernames and machine-specific paths.
- Do not commit SDK headers, libraries, Help files, samples, generated indexes,
  screenshots containing license data, or proprietary project files.
- Describe the operating systems and Wwise versions used for testing.

## Reporting Layout Changes

When a Wwise release changes paths or macros, include:

- The Wwise version and build.
- The affected platform and installed packages.
- The old and new relative paths.
- A minimal synthetic test fixture when possible, not copied SDK content.
