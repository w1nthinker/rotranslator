# rotranslator
A CLI translator to all supported roblox experience languages/locale.

Adding deepl and roblox support would have required me to add duplicate logic from [rosuite](https://github.com/w1nthinker/rosuite), so use the translate method of that.

## What It Does
- translates to all 21 Roblox locale
- copies the final JSON to your clipboard by default (disabled in batch mode)
- stays open like an AI chat for easy and rappid translation

## Why this?
- Roblox OpenCloud generative_ai translate_text endpoint doesnt support every experience language, [see here](https://x.com/w1nthinker/status/2042958979983134969?s=20)
- DeepL doesnt support thai as an translation target

## Examples
https://github.com/user-attachments/assets/8698ac95-4fcb-4c8d-a357-a7287381da7d

with `--batch` flag

https://github.com/user-attachments/assets/a7a5cad9-b2a8-4170-ac77-6b009aed85c6

## Flags
- `--help` shows you the info of this flags list
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

*Up to 15K characters per API call, batch takes use of this to partition requests.*
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

## Install

### Install with Rokit
To install it globally: `rokit add --global w1nthinker/rotranslator` (**recommended**)

For project realm: `rokit add w1nthinker/rotranslator`

Or manually in `rokit.toml`
```toml
[tools]
rotranslator = { github = "w1nthinker/rotranslator", version = "0.1.0" }
```
Following this after adding it manually:
```bash
rokit install
```

### Install from a GitHub Release
Download the binary for your system from the latest release.
<img width="675" height="297" alt="Bildschirmfoto 2026-04-22 um 21 53 02" src="https://github.com/user-attachments/assets/b1c2302a-3550-404b-bb58-780ba5a01414" />

Run the binary in your terminal:
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

Run tests: *(only when deving)*
```bash
uv run --extra test pytest
```

## Disclaimer

- `rotranslator` is an independent open-source project.
- It is not affiliated with, endorsed by, or sponsored by Google or Roblox.
- It uses the unofficial `googletrans` library and public translation endpoints.
- Translation behavior and availability can change at any time.
- Use it at your own risk.
