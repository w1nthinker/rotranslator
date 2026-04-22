from src.config import GOOGLE_TARGETS
from src.config import GOOGLE_TO_ROBLOX
from src.config import ROBLOX_LOCALES
from src.config import ROBLOX_TO_GOOGLE
from src.config import TOTAL_ROBLOX_LOCALES


def test_locale_order_is_stable() -> None:
    assert ROBLOX_LOCALES == (
        "ar-001",
        "de-de",
        "en-gb",
        "en-us",
        "es-es",
        "es-mx",
        "fr-ca",
        "fr-fr",
        "id-id",
        "it-it",
        "ja-jp",
        "ko-kr",
        "pl-pl",
        "pt-br",
        "pt-pt",
        "ru-ru",
        "th-th",
        "tr-tr",
        "vi-vn",
        "zh-cn",
        "zh-tw",
    )


def test_grouped_targets_match_expected_fanout() -> None:
    assert GOOGLE_TO_ROBLOX["en"] == ["en-gb", "en-us"]
    assert GOOGLE_TO_ROBLOX["es"] == ["es-es", "es-mx"]
    assert GOOGLE_TO_ROBLOX["fr"] == ["fr-ca", "fr-fr"]
    assert GOOGLE_TO_ROBLOX["pt"] == ["pt-br", "pt-pt"]


def test_locale_counts_match_contract() -> None:
    assert TOTAL_ROBLOX_LOCALES == 21
    assert len(GOOGLE_TARGETS) == 17
    assert len(ROBLOX_TO_GOOGLE) == 21
