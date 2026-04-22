from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Awaitable
from typing import Callable

from googletrans import Translator

from .config import GOOGLE_TARGETS
from .config import GOOGLE_TO_ROBLOX
from .config import RETRY_DELAY_SECONDS
from .config import ROBLOX_LOCALES

ProgressCallback = Callable[[int], Awaitable[None]]


@dataclass(frozen=True)
class BatchResult:
    values: dict[str, str | None]
    json_text: str
    source_language: str | None
    translated_count: int
    elapsed_seconds: float


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
        started_at = time.monotonic()
        results: dict[str, str | None] = {}
        source_language: str | None = None

        async def translate_target(target: str) -> None:
            nonlocal source_language
            roblox_locales = GOOGLE_TO_ROBLOX[target]
            translated_text, detected_source = await self._translate_with_retry(text, target)
            if source_language is None and detected_source:
                source_language = detected_source
            for roblox_locale in roblox_locales:
                results[roblox_locale] = translated_text
            await on_progress(len(roblox_locales))

        gathered = await asyncio.gather(
            *(translate_target(target) for target in GOOGLE_TARGETS),
            return_exceptions=True,
        )

        for target, outcome in zip(GOOGLE_TARGETS, gathered, strict=True):
            if isinstance(outcome, Exception):
                for roblox_locale in GOOGLE_TO_ROBLOX[target]:
                    results.setdefault(roblox_locale, None)

        ordered_values = {locale: results.get(locale) for locale in ROBLOX_LOCALES}
        json_text = json.dumps(
            ordered_values,
            ensure_ascii=False,
            indent=None if compact else 2,
            separators=(",", ":") if compact else None,
        )
        translated_count = sum(value is not None for value in ordered_values.values())
        return BatchResult(
            values=ordered_values,
            json_text=json_text,
            source_language=source_language,
            translated_count=translated_count,
            elapsed_seconds=time.monotonic() - started_at,
        )

    async def _translate_with_retry(
        self,
        text: str,
        target: str,
    ) -> tuple[str | None, str | None]:
        for attempt in range(2):
            try:
                async with self._semaphore:
                    translated = await self._translator.translate(text, src="auto", dest=target)
                return translated.text, translated.src
            except Exception:
                if attempt == 1:
                    return None, None
                await asyncio.sleep(RETRY_DELAY_SECONDS)
