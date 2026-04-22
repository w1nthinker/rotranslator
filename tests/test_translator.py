from __future__ import annotations

import asyncio

import pytest

from src.translator import BatchTranslator
from src.translator import estimate_progress_total
from src.translator import split_text_for_translation


class FakeTranslated:
    def __init__(self, text: str, src: str = "en") -> None:
        self.text = text
        self.src = src


class FakeTranslatorClient:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, tuple[str, ...]]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def translate(self, text: str, src: str, dest: str):
        texts = tuple(text) if isinstance(text, list) else (text,)
        self.calls.append((dest, texts))
        response = self.responses[dest]
        if isinstance(response, Exception):
            raise response
        if callable(response):
            return response(texts)
        if isinstance(response, list):
            current = response.pop(0)
            if isinstance(current, Exception):
                raise current
            return current
        return response


async def noop(_: int) -> None:
    return None


@pytest.mark.asyncio
async def test_translate_text_fans_out_shared_targets() -> None:
    translator = BatchTranslator(concurrency=2)
    translator._translator = FakeTranslatorClient(
        {
            "ar": FakeTranslated("ar"),
            "de": FakeTranslated("de"),
            "en": FakeTranslated("same-en"),
            "es": FakeTranslated("same-es"),
            "fr": FakeTranslated("same-fr"),
            "id": FakeTranslated("id"),
            "it": FakeTranslated("it"),
            "ja": FakeTranslated("ja"),
            "ko": FakeTranslated("ko"),
            "pl": FakeTranslated("pl"),
            "pt": FakeTranslated("same-pt"),
            "ru": FakeTranslated("ru"),
            "th": FakeTranslated("th"),
            "tr": FakeTranslated("tr"),
            "vi": FakeTranslated("vi"),
            "zh-cn": FakeTranslated("zh-cn"),
            "zh-tw": FakeTranslated("zh-tw"),
        }
    )

    result = await translator.translate_text("Hello", compact=False, on_progress=noop)

    assert result.values["en-gb"] == "same-en"
    assert result.values["en-us"] == "same-en"
    assert result.values["fr-ca"] == "same-fr"
    assert result.values["fr-fr"] == "same-fr"
    assert result.values["pt-br"] == "same-pt"
    assert result.values["pt-pt"] == "same-pt"
    assert list(result.values.keys())[0] == "ar-001"
    assert list(result.values.keys())[-1] == "zh-tw"
    assert result.source_language == "en"
    assert result.translated_count == 21


@pytest.mark.asyncio
async def test_translate_text_returns_nulls_on_failure() -> None:
    translator = BatchTranslator(concurrency=2)
    translator._translator = FakeTranslatorClient(
        {
            "ar": FakeTranslated("ar"),
            "de": FakeTranslated("de"),
            "en": RuntimeError("boom"),
            "es": FakeTranslated("es"),
            "fr": FakeTranslated("fr"),
            "id": FakeTranslated("id"),
            "it": FakeTranslated("it"),
            "ja": FakeTranslated("ja"),
            "ko": FakeTranslated("ko"),
            "pl": FakeTranslated("pl"),
            "pt": FakeTranslated("pt"),
            "ru": FakeTranslated("ru"),
            "th": FakeTranslated("th"),
            "tr": FakeTranslated("tr"),
            "vi": FakeTranslated("vi"),
            "zh-cn": FakeTranslated("zh-cn"),
            "zh-tw": FakeTranslated("zh-tw"),
        }
    )

    result = await translator.translate_text("Hello", compact=False, on_progress=noop)

    assert result.values["en-gb"] is None
    assert result.values["en-us"] is None
    assert result.translated_count == 19


@pytest.mark.asyncio
async def test_translate_text_retries_once() -> None:
    translator = BatchTranslator(concurrency=1)
    translator._translator = FakeTranslatorClient(
        {
            "ar": [RuntimeError("retry"), FakeTranslated("ar")],
            "de": FakeTranslated("de"),
            "en": FakeTranslated("en"),
            "es": FakeTranslated("es"),
            "fr": FakeTranslated("fr"),
            "id": FakeTranslated("id"),
            "it": FakeTranslated("it"),
            "ja": FakeTranslated("ja"),
            "ko": FakeTranslated("ko"),
            "pl": FakeTranslated("pl"),
            "pt": FakeTranslated("pt"),
            "ru": FakeTranslated("ru"),
            "th": FakeTranslated("th"),
            "tr": FakeTranslated("tr"),
            "vi": FakeTranslated("vi"),
            "zh-cn": FakeTranslated("zh-cn"),
            "zh-tw": FakeTranslated("zh-tw"),
        }
    )

    result = await translator.translate_text("Hello", compact=True, on_progress=noop)

    assert result.values["ar-001"] == "ar"
    assert sum(1 for dest, _ in translator._translator.calls if dest == "ar") == 2


def test_split_text_for_translation_keeps_short_text_intact() -> None:
    assert split_text_for_translation("Hello") == ["Hello"]


def test_split_text_for_translation_splits_long_text_smoothly() -> None:
    text = ("hello " * 3000).strip()
    parts = split_text_for_translation(text, max_length=100)

    assert len(parts) > 1
    assert all(len(part) <= 100 for part in parts)
    assert "".join(parts) == text


@pytest.mark.asyncio
async def test_translate_text_chunks_single_long_input() -> None:
    translator = BatchTranslator(concurrency=2)

    def build_response(texts: tuple[str, ...]) -> list[FakeTranslated]:
        return [FakeTranslated(f"<{part}>") for part in texts]

    translator._translator = FakeTranslatorClient({target: build_response for target in {
        "ar",
        "de",
        "en",
        "es",
        "fr",
        "id",
        "it",
        "ja",
        "ko",
        "pl",
        "pt",
        "ru",
        "th",
        "tr",
        "vi",
        "zh-cn",
        "zh-tw",
    }})

    progress_updates: list[int] = []

    async def record_progress(increment: int) -> None:
        progress_updates.append(increment)

    text = ("chunk " * 3000).strip()
    parts = split_text_for_translation(text)
    result = await translator.translate_text(text, compact=False, on_progress=record_progress)

    assert result.values["en-us"] == "".join(f"<{part}>" for part in parts)
    assert len([call for call in translator._translator.calls if call[0] == "en"]) == len(parts)
    assert sum(progress_updates) == len(parts) * 17


@pytest.mark.asyncio
async def test_translate_texts_batches_multiple_inputs_under_limit() -> None:
    translator = BatchTranslator(concurrency=2)

    def build_response(texts: tuple[str, ...]) -> list[FakeTranslated]:
        return [FakeTranslated(f"tr:{part}") for part in texts]

    translator._translator = FakeTranslatorClient({target: build_response for target in {
        "ar",
        "de",
        "en",
        "es",
        "fr",
        "id",
        "it",
        "ja",
        "ko",
        "pl",
        "pt",
        "ru",
        "th",
        "tr",
        "vi",
        "zh-cn",
        "zh-tw",
    }})

    texts = ["hello", "world", "again"]
    progress_updates: list[int] = []

    async def record_progress(increment: int) -> None:
        progress_updates.append(increment)

    results = await translator.translate_texts(texts, compact=True, on_progress=record_progress)

    en_calls = [texts for dest, texts in translator._translator.calls if dest == "en"]
    assert en_calls == [("hello", "world", "again")]
    assert results[0].values["en-us"] == "tr:hello"
    assert results[1].values["en-us"] == "tr:world"
    assert results[2].values["en-us"] == "tr:again"
    assert sum(progress_updates) == 17


@pytest.mark.asyncio
async def test_translate_texts_starts_new_request_after_limit() -> None:
    translator = BatchTranslator(concurrency=2)

    def build_response(texts: tuple[str, ...]) -> list[FakeTranslated]:
        return [FakeTranslated(part.upper()) for part in texts]

    translator._translator = FakeTranslatorClient({target: build_response for target in {
        "ar",
        "de",
        "en",
        "es",
        "fr",
        "id",
        "it",
        "ja",
        "ko",
        "pl",
        "pt",
        "ru",
        "th",
        "tr",
        "vi",
        "zh-cn",
        "zh-tw",
    }})

    first = "a" * 10000
    second = "b" * 6000
    progress_updates: list[int] = []

    async def record_progress(increment: int) -> None:
        progress_updates.append(increment)

    results = await translator.translate_texts([first, second], compact=True, on_progress=record_progress)

    en_calls = [texts for dest, texts in translator._translator.calls if dest == "en"]
    assert en_calls == [(first,), (second,)]
    assert results[0].values["en-us"] == first.upper()
    assert results[1].values["en-us"] == second.upper()
    assert sum(progress_updates) == 34


def test_estimate_progress_total_uses_chunk_count() -> None:
    short = "hello"
    long = ("chunk " * 3000).strip()
    assert estimate_progress_total([short]) == 17
    assert estimate_progress_total(["hello", "world"]) == 17
    assert estimate_progress_total([long]) == len(split_text_for_translation(long)) * 17
