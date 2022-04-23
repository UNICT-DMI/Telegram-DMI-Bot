import os.path
from glob import glob
from os.path import basename
from module.data.vars import TEXT_IDS
import yaml


# Translation Dictionary
translations: dict[str, dict[str, str]] = {}


def get_locale(language_code: str, text_id: TEXT_IDS) -> str:
    language = language_code if language_code in translations else "it"
    if text_id.name in translations[language]:
        return translations[language][text_id.name]
    return translations["it"][text_id.name]


def load_translations() -> None:
    for language_file in glob(os.path.join("data", "translations", "*.yaml")):
        language_name: str = basename(language_file).split(".")[0]
        with open(language_file, 'r', encoding="UTF-8") as language_stream:
            translations[language_name] = yaml.load(language_stream, Loader=yaml.SafeLoader)
        language_stream.close()


def get_regex_multi_lang(text_id: TEXT_IDS) -> str:
    pattern: str = ""
    for language in translations:
        pattern = f'{pattern}{get_locale(language, text_id)}|'
    return f'({pattern[:-1]})'

