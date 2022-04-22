from module.data.translations.it import italian_language
from module.data.translations.en import english_language


# Translation Dictionary
translations: dict[str, dict[int, str]] = {
    "it": italian_language,
    "en": english_language
}


def get_locale(language_code: str, text_id: int) -> str:
    language = language_code if language_code in translations else "it"
    if text_id in translations[language]:
        return translations[language][text_id]
    return translations["it"][text_id]
