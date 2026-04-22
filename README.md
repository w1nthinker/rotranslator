# rotranslator

`rotranslator` is a small terminal app that takes one line of text and translates it into all Roblox locales.

You type something like `Hello world`, and it prints a Roblox-ready JSON object you can paste into your project.

It is made for people who want a fast way to generate Roblox translation JSON from the terminal without setting up a full app or translation pipeline.

## What It Does

- translates to all 21 Roblox locale keys
- only sends 17 unique translation requests internally for better speed
- copies the final JSON to your clipboard by default
- stays open like a REPL so you can translate multiple lines quickly
- can also queue multiple inputs in batch mode

## Install

### Install with Rokit

If you use Rokit, add `rotranslator` from this repository's GitHub Releases.

Example `rokit.toml` shape:

```toml
[tools]
rotranslator = { github = "w1nthinker/rotranslator", version = "0.1.0" }
```

Then install it with:

```bash
rokit install
```

Note: this depends on the GitHub repo and release existing first. If your Rokit version expects slightly different manifest syntax, keep the same GitHub owner/repo and version values and adjust to your installed Rokit format.

### Install from a GitHub Release

Download the binary for your system from the latest release.

Current release asset names:

- `rotranslator-0.1.0-linux-x86_64.zip`
- `rotranslator-0.1.0-macos-x86_64.zip`
- `rotranslator-0.1.0-macos-aarch64.zip`
- `rotranslator-0.1.0-windows-x86_64.zip`

Extract the archive, then run the binary inside:

```bash
./rotranslator
```

### Build from source

Install dependencies:

```bash
uv sync
```

Run from source:

```bash
uv run rotranslator
```

Build a local binary:

```bash
uv run --extra build python scripts/build_binary.py
```

## Basic Example

```text
$ rotranslator
Ready. Type text and press Enter. Ctrl+C to quit.

> Hello world
{
  "ar-001": "...",
  "de-de": "...",
  "en-gb": "Hello world",
  "en-us": "Hello world",
  "...": "..."
}

>
```

## Flags

- `--meta`
  Show detected input language, total time, and translated percent after the JSON.
- `--no-copy`
  Do not copy the final JSON to the clipboard.
- `--compact`
  Print compact JSON instead of pretty JSON.
- `--batch`
  Enter multiple inputs first, then translate them all in parallel.
- `--concurrency 6`
  Set how many translation requests run at once.

## Batch Mode

Batch mode is useful when you want to queue a few strings and translate them together.

Start batch mode:

```bash
uv run rotranslator --batch
```

Flow:

- enter one line
- choose whether to add another
- when you stop, all queued inputs are translated in parallel
- each result prints as its own JSON object
- clipboard copy is off by default in batch mode

## Output Notes

- terminal output is JSON only, unless you enable `--meta`
- clipboard gets only the JSON string
- if one locale fails, its value becomes `null`
- the app keeps running until you exit with `Ctrl+C` or `Ctrl+D`

## Releases

GitHub Actions builds single-file binaries for:

- Linux x86_64
- macOS x86_64
- macOS arm64
- Windows x86_64

Pushing a tag like `v0.1.0` triggers the release workflow and uploads versioned `.zip` archives to the release page.

## Development

Run tests:

```bash
uv run --extra test pytest
```

## Disclaimer

- `rotranslator` is an independent open-source project.
- It is not affiliated with, endorsed by, or sponsored by Google or Roblox.
- It uses the unofficial `googletrans` library and public translation endpoints.
- Translation behavior and availability can change at any time.
- Use it at your own risk.
