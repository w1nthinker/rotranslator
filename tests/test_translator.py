from __future__ import annotations

import asyncio

import pytest

from src.translator import BatchTranslator


class FakeTranslated:
    def __init__(self, text: str, src: str = "en") -> None:
        self.text = text
        self.src = src


class FakeTranslatorClient:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses
        self.calls: list[str] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def translate(self, text: str, src: str, dest: str):
        self.calls.append(dest)
        response = self.responses[dest]
        if isinstance(response, Exception):
            raise response
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
    assert translator._translator.calls.count("ar") == 2
