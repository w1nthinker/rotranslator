from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from collections.abc import Sequence
from typing import Awaitable
from typing import Callable

from googletrans import Translator

from .config import GOOGLE_TARGETS
from .config import GOOGLE_TO_ROBLOX
from .config import MAX_TEXT_LENGTH
from .config import RETRY_DELAY_SECONDS
from .config import ROBLOX_LOCALES
from .config import ROBLOX_TO_GOOGLE

ProgressCallback = Callable[[int], Awaitable[None]]


@dataclass(frozen=True)
class BatchResult:
    values: dict[str, str | None]
    json_text: str
    source_language: str | None
    translated_count: int
    elapsed_seconds: float


def split_text_for_translation(text: str, max_length: int = MAX_TEXT_LENGTH) -> list[str]:
    if len(text) <= max_length:
        return [text]

    chunks: list[str] = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + max_length, text_length)
        if end == text_length:
            chunks.append(text[start:end])
            break

        split_at = end
        while split_at > start and not text[split_at - 1].isspace():
            split_at -= 1

        if split_at == start:
            split_at = end

        chunks.append(text[start:split_at])
        start = split_at

    return chunks


def estimate_progress_total(texts: Sequence[str]) -> int:
    translation_units = [
        (text_index, chunk_index, chunk_text)
        for text_index, chunks in enumerate(split_text_for_translation(text) for text in texts)
        for chunk_index, chunk_text in enumerate(chunks)
    ]
    return len(_pack_translation_units(translation_units)) * len(GOOGLE_TARGETS)


def _batch_char_count(parts: Sequence[str]) -> int:
    if not parts:
        return 0
    return sum(len(part) for part in parts) + len(parts) - 1


def _pack_translation_units(
    units: Sequence[tuple[int, int, str]],
    max_length: int = MAX_TEXT_LENGTH,
) -> list[list[tuple[int, int, str]]]:
    batches: list[list[tuple[int, int, str]]] = []
    current_batch: list[tuple[int, int, str]] = []

    for unit in units:
        _, _, text = unit
        candidate_parts = [part for _, _, part in current_batch]
        candidate_parts.append(text)

        if current_batch and _batch_char_count(candidate_parts) > max_length:
            batches.append(current_batch)
            current_batch = [unit]
            continue

        current_batch.append(unit)

    if current_batch:
        batches.append(current_batch)

    return batches


class BatchTranslator:
    def __init__(self, concurrency: int) -> None:
        self._concurrency = concurrency
        self._semaphore = asyncio.Semaphore(concurrency)
        self._translator = Translator(service_urls=["translate.googleapis.com"])

    async def __aenter__(self) -> "BatchTranslator":
        await self._translator.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self._translator.__aexit__(exc_type, exc, tb)

    async def translate_text(
        self,
        text: str,
        compact: bool,
        on_progress: ProgressCallback,
    ) -> BatchResult:
        return (await self.translate_texts([text], compact, on_progress))[0]

    async def translate_texts(
        self,
        texts: Sequence[str],
        compact: bool,
        on_progress: ProgressCallback,
    ) -> list[BatchResult]:
        started_at = time.monotonic()
        text_chunks = [split_text_for_translation(text) for text in texts]
        translation_units = [
            (text_index, chunk_index, chunk_text)
            for text_index, chunks in enumerate(text_chunks)
            for chunk_index, chunk_text in enumerate(chunks)
        ]
        translated_chunks = [
            {target: [None] * len(chunks) for target in GOOGLE_TARGETS}
            for chunks in text_chunks
        ]
        source_languages: list[str | None] = [None] * len(texts)

        async def translate_target(target: str) -> None:
            for batch in _pack_translation_units(translation_units):
                translations = await self._translate_many_with_retry(
                    [chunk_text for _, _, chunk_text in batch],
                    target,
                )
                for (text_index, chunk_index, _), (translated_text, detected_source) in zip(
                    batch,
                    translations,
                    strict=True,
                ):
                    translated_chunks[text_index][target][chunk_index] = translated_text
                    if source_languages[text_index] is None and detected_source:
                        source_languages[text_index] = detected_source
                await on_progress(1)

        await asyncio.gather(*(translate_target(target) for target in GOOGLE_TARGETS))

        elapsed_seconds = time.monotonic() - started_at
        results: list[BatchResult] = []
        for text_index, _ in enumerate(texts):
            ordered_values = {}
            for locale in ROBLOX_LOCALES:
                target = ROBLOX_TO_GOOGLE[locale]
                parts = translated_chunks[text_index][target]
                ordered_values[locale] = None if any(part is None for part in parts) else "".join(parts)

            json_text = json.dumps(
                ordered_values,
                ensure_ascii=False,
                indent=None if compact else 2,
                separators=(",", ":") if compact else None,
            )
            translated_count = sum(value is not None for value in ordered_values.values())
            results.append(
                BatchResult(
                    values=ordered_values,
                    json_text=json_text,
                    source_language=source_languages[text_index],
                    translated_count=translated_count,
                    elapsed_seconds=elapsed_seconds,
                )
            )

        return results

    async def _translate_many_with_retry(
        self,
        texts: Sequence[str],
        target: str,
    ) -> list[tuple[str | None, str | None]]:
        for attempt in range(2):
            try:
                async with self._semaphore:
                    translated = await self._translator.translate(list(texts), src="auto", dest=target)
                if not isinstance(translated, list):
                    translated = [translated]
                return [(item.text, item.src) for item in translated]
            except Exception:
                if attempt == 1:
                    return [(None, None) for _ in texts]
                await asyncio.sleep(RETRY_DELAY_SECONDS)
