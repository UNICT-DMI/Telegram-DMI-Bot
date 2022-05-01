import os.path
import random
from glob import glob
from os.path import basename

from telegram import Update

from module.data.vars import TEXT_IDS, ON_DEMAND_TEXTS, PLACE_HOLDER, ON_DEMAND_FILL
import yaml


# Translation Dictionary
from module.shared import read_md, CUSicon

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


def get_on_demand_text(locale: str, text_id_name: str) -> str:
    message_text: str = get_locale(locale, TEXT_IDS[text_id_name])
    if text_id_name in ON_DEMAND_TEXTS:
        dynamic_text: str = read_md(ON_DEMAND_TEXTS[text_id_name])
        if text_id_name in ON_DEMAND_FILL:
            # list is an ordered data structure, iterating is guaranteed to be ordered
            fills: list[str] = dynamic_text.split("\n")
            for fill in fills:
                if not fill:
                    continue
                replacement: str = fill.split(":", 1)[1]
                if ON_DEMAND_FILL[text_id_name] == "multi":
                    replacement = replacement.replace("|", "\n")
                message_text = message_text.replace(PLACE_HOLDER, replacement, 1)
        else:
            message_text = f'{message_text}\n{dynamic_text}'
    if text_id_name == "HELP_ALL_COMMANDS_TOOLTIP_ID":
        message_text = message_text.replace("<cusicon>", CUSicon[random.randint(0, 5)])
    return message_text

def get_locale_code(update: Update) -> str:
    return update.message.from_user.language_code if update.message.from_user.language_code else update.from_user.language_code


