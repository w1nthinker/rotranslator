from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence
from typing import Any

from rich.console import Console
from rich.prompt import Prompt
from rich.text import Text

from .clipboard import copy_json
from .config import DEFAULT_CONCURRENCY
from .config import MAX_TEXT_LENGTH
from .config import TOTAL_ROBLOX_LOCALES
from .progress import create_progress
from .translator import BatchTranslator
from .translator import BatchResult


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rotranslator")
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help="Maximum parallel translation tasks.",
    )
    parser.add_argument(
        "--no-copy",
        action="store_true",
        help="Disable clipboard copy.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print compact JSON instead of pretty JSON.",
    )
    parser.add_argument(
        "--meta",
        action="store_true",
        help="Show inline metadata after the JSON output.",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Collect multiple inputs, translate them in parallel, and print each JSON result.",
    )
    return parser


def format_meta(result: BatchResult) -> str:
    percent = (result.translated_count / TOTAL_ROBLOX_LOCALES) * 100
    source = result.source_language or "unknown"
    return f"src={source} time={result.elapsed_seconds:.2f}s translated={percent:.0f}%"


def print_result(console: Console, json_text: str, meta_text: str | None) -> None:
    if not meta_text:
        console.print(json_text)
        return

    lines = json_text.splitlines() or [json_text]
    for line in lines[:-1]:
        console.print(line)

    footer = Text(lines[-1])
    footer.append(f"  {meta_text}", style="dim")
    console.print(footer)


def warn_if_near_limit(console: Console, text: str) -> None:
    if len(text) >= MAX_TEXT_LENGTH - 500:
        console.print(
            f"Warning: input is near the {MAX_TEXT_LENGTH} character googletrans limit.",
            style="yellow",
        )


def batch_confirmation_prompt() -> Text:
    prompt = Text("Add one more input? ")
    prompt.append("[Yes/No]", style="bold")
    prompt.append(" (default: Yes)", style="dim")
    return prompt


def clear_previous_terminal_line(console: Console) -> None:
    if not console.is_terminal:
        return
    console.file.write("\x1b[1A\r\x1b[2K")
    console.file.flush()


def prompt_yes_default(console: Console) -> bool:
    answer = Prompt.ask(
        batch_confirmation_prompt(),
        console=console,
        choices=["yes", "no", "y", "n"],
        case_sensitive=False,
        default="yes",
        show_choices=False,
        show_default=False,
    )
    clear_previous_terminal_line(console)
    return answer.lower() in {"yes", "y"}


def prompt_text(console: Console, prompt: str = "> ") -> str:
    return console.input(prompt)


def collect_batch_inputs(console: Console) -> list[str] | None:
    inputs: list[str] = []

    while True:
        try:
            raw_text = prompt_text(console)
        except EOFError:
            if not inputs:
                console.print()
                return None
            console.print()
            return inputs

        text = raw_text.strip()
        if not text:
            if inputs:
                continue
            continue

        inputs.append(text)
        try:
            if not prompt_yes_default(console):
                return inputs
        except EOFError:
            console.print()
            return inputs


async def translate_one(
    translator: BatchTranslator,
    text: str,
    compact: bool,
    on_progress,
) -> BatchResult:
    return await translator.translate_text(text, compact, on_progress)


def make_progress_callback(progress, task_id: Any):
    async def on_progress(increment: int) -> None:
        progress.update(task_id, advance=increment)

    return on_progress


async def run_translations(
    translator: BatchTranslator,
    texts: Sequence[str],
    compact: bool,
    description: str,
) -> list[BatchResult]:
    progress = create_progress()
    total = TOTAL_ROBLOX_LOCALES * len(texts)

    with progress:
        task_id = progress.add_task(description, total=total)
        on_progress = make_progress_callback(progress, task_id)
        return await asyncio.gather(
            *(translate_one(translator, text, compact, on_progress) for text in texts)
        )


def render_results(console: Console, results: Sequence[BatchResult], show_meta: bool) -> None:
    for index, result in enumerate(results):
        print_result(console, result.json_text, format_meta(result) if show_meta else None)
        if index != len(results) - 1:
            console.print()


def maybe_copy_result(console: Console, result: BatchResult, copy_output: bool) -> None:
    if copy_output and not copy_json(result.json_text):
        console.print("Clipboard unavailable.", style="yellow")


async def process_inputs(
    console: Console,
    translator: BatchTranslator,
    texts: Sequence[str],
    compact: bool,
    show_meta: bool,
    copy_output: bool,
) -> None:
    for text in texts:
        warn_if_near_limit(console, text)

    description = "Translating" if len(texts) == 1 else "Translating batch"
    results = await run_translations(translator, texts, compact, description)
    render_results(console, results, show_meta)
    if len(results) == 1:
        maybe_copy_result(console, results[0], copy_output)


async def run_repl(args: argparse.Namespace) -> int:
    console = Console()
    console.print("Ready. Type text and press Enter. Ctrl+C to quit.")

    async with BatchTranslator(concurrency=max(1, args.concurrency)) as translator:
        while True:
            if args.batch:
                texts = collect_batch_inputs(console)
                if texts is None:
                    return 0
                await process_inputs(
                    console,
                    translator,
                    texts,
                    args.compact,
                    args.meta,
                    False,
                )
                continue

            try:
                raw_text = prompt_text(console)
            except EOFError:
                console.print()
                return 0

            text = raw_text.strip()
            if not text:
                continue

            await process_inputs(
                console,
                translator,
                [text],
                args.compact,
                args.meta,
                not args.no_copy,
            )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return asyncio.run(run_repl(args))
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
