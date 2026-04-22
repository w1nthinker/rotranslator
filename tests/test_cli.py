from __future__ import annotations

from rich.console import Console

from src.cli import batch_confirmation_prompt
from src.cli import format_meta
from src.cli import print_result
from src.cli import warn_if_near_limit
from src.translator import BatchResult


def make_result() -> BatchResult:
    return BatchResult(
        values={"en-us": "Hello"},
        json_text='{"en-us": "Hello"}',
        source_language="en",
        translated_count=21,
        elapsed_seconds=1.25,
    )


def test_format_meta_contains_expected_fields() -> None:
    assert format_meta(make_result()) == "src=en time=1.25s translated=100%"


def test_print_result_appends_meta_to_closing_line() -> None:
    console = Console(record=True, force_terminal=False, color_system=None)
    print_result(console, '{\n  "en-us": "Hello"\n}', "src=en time=1.25s translated=100%")
    output = console.export_text()
    assert '}  src=en time=1.25s translated=100%' in output


def test_warn_if_near_limit_prints_warning() -> None:
    console = Console(record=True, force_terminal=False, color_system=None)
    warn_if_near_limit(console, "x" * 14_600)
    assert "googletrans limit" in console.export_text()


def test_batch_confirmation_prompt_mentions_default_yes() -> None:
    assert "default: Yes" in batch_confirmation_prompt().plain
