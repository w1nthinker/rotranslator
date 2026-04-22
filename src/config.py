from __future__ import annotations

DEFAULT_CONCURRENCY = 6
MAX_TEXT_LENGTH = 15_000
RETRY_DELAY_SECONDS = 0.75

ROBLOX_TO_GOOGLE = {
    "ar-001": "ar",
    "de-de": "de",
    "en-gb": "en",
    "en-us": "en",
    "es-es": "es",
    "es-mx": "es",
    "fr-ca": "fr",
    "fr-fr": "fr",
    "id-id": "id",
    "it-it": "it",
    "ja-jp": "ja",
    "ko-kr": "ko",
    "pl-pl": "pl",
    "pt-br": "pt",
    "pt-pt": "pt",
    "ru-ru": "ru",
    "th-th": "th",
    "tr-tr": "tr",
    "vi-vn": "vi",
    "zh-cn": "zh-cn",
    "zh-tw": "zh-tw",
}

ROBLOX_LOCALES = tuple(ROBLOX_TO_GOOGLE.keys())

GOOGLE_TO_ROBLOX: dict[str, list[str]] = {}
for roblox_locale, google_locale in ROBLOX_TO_GOOGLE.items():
    GOOGLE_TO_ROBLOX.setdefault(google_locale, []).append(roblox_locale)

GOOGLE_TARGETS = tuple(GOOGLE_TO_ROBLOX.keys())
TOTAL_ROBLOX_LOCALES = len(ROBLOX_LOCALES)
