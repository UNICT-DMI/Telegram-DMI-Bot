"""/minigames command — the mini games hub.

Holds the hub itself and the helpers shared across mini games. Each individual game
(e.g. Tris) lives in its own module and plugs into the hub from there.

Settings (under the ``mg_`` callback prefix) are shared by every game and stored per user
in ``minigames_settings``: whether the player is anonymous (on by default) and an optional
custom alias. An anonymous player is shown to opponents under a random alias, or under their
custom alias wrapped in 🥷 when they set one.
"""

import re
from random import choice
from typing import List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from module.data import DbManager
from module.data.vars import TEXT_IDS
from module.shared import check_log, read_md
from module.utils.multi_lang_utils import get_locale

SETTINGS_TABLE = "minigames_settings"
NINJA_ICON = "🥷"  # wraps a custom anonymous alias
MAX_ANON_NAME_LEN = 30
NAME_INPUT_PREFIX = r"^(?!=<[/])[Nn]ick:\s+"  # how the custom alias is typed in
_anonymous_names: List[str] = []


def minigames(update: Update, context: CallbackContext) -> None:
    """Called by /minigames and the "🕹 Mini Games" sticky button. Sends the hub."""
    check_log(update, "minigames")
    locale: str = update.message.from_user.language_code
    context.bot.sendMessage(
        chat_id=update.message.chat_id,
        text=get_locale(locale, TEXT_IDS.MINI_GAMES_HEADER_TEXT_ID),
        reply_markup=InlineKeyboardMarkup(_hub_keyboard(locale)),
    )


def minigames_settings_handler(update: Update, context: CallbackContext) -> None:
    """Called by every mg_* callback. Shows the settings menu and toggles its options."""
    query = update.callback_query
    query.answer()
    locale: str = query.from_user.language_code
    user_id: int = query.from_user.id
    data: str = query.data

    if data == "mg_hub":
        _edit(
            context,
            query,
            get_locale(locale, TEXT_IDS.MINI_GAMES_HEADER_TEXT_ID),
            _hub_keyboard(locale),
        )
        return

    if data == "mg_setname":
        context.user_data.setdefault("minigames", {})["awaiting_name"] = True
        _edit(
            context,
            query,
            get_locale(locale, TEXT_IDS.MINI_GAMES_SET_NAME_PROMPT_TEXT_ID),
            _back_to_settings_keyboard(locale),
        )
        return

    if data == "mg_anon":
        set_anonymous(user_id, not is_anonymous(user_id))

    _show_settings(context, query, locale, user_id)


def minigames_input_name(update: Update, context: CallbackContext) -> None:
    """Store the custom alias the user typed (format ``Nick: <name>``), rejecting '@'."""
    mini_games = context.user_data.get("minigames", {})
    if not mini_games.get("awaiting_name"):
        return
    check_log(update, "minigames_input_name")
    locale: str = update.message.from_user.language_code
    user_id: int = update.message.from_user.id
    name = re.sub(NAME_INPUT_PREFIX, "", update.message.text).strip()

    if not name or "@" in name:
        # keep the flag set so the next message is treated as another attempt
        context.bot.sendMessage(
            chat_id=update.message.chat_id,
            text=get_locale(locale, TEXT_IDS.MINI_GAMES_NAME_INVALID_TEXT_ID),
        )
        return

    mini_games.pop("awaiting_name", None)
    set_anonymous_name(user_id, name[:MAX_ANON_NAME_LEN])
    context.bot.sendMessage(
        chat_id=update.message.chat_id,
        text=get_locale(locale, TEXT_IDS.MINI_GAMES_NAME_SAVED_TEXT_ID),
        reply_markup=InlineKeyboardMarkup(
            _settings_keyboard(
                locale, is_anonymous(user_id), get_anonymous_name(user_id)
            )
        ),
    )


def _show_settings(context: CallbackContext, query, locale: str, user_id: int) -> None:
    _edit(
        context,
        query,
        get_locale(locale, TEXT_IDS.MINI_GAMES_SETTINGS_HEADER_TEXT_ID),
        _settings_keyboard(locale, is_anonymous(user_id), get_anonymous_name(user_id)),
    )


def _hub_keyboard(locale: str) -> List[List[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.TRIS_GAME_NAME_TEXT_ID),
                callback_data="ttt_mode",
            )
        ],
        # chess is implemented but still a work in progress, so it is hidden from the hub
        # for now; re-add this button to expose it again
        # [
        #     InlineKeyboardButton(
        #         get_locale(locale, TEXT_IDS.CHESS_GAME_NAME_TEXT_ID),
        #         callback_data="chess_play",
        #     )
        # ],
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.MINI_GAMES_SETTINGS_TEXT_ID),
                callback_data="mg_settings",
            )
        ],
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.CLOSE_KEYBOARD_TEXT_ID),
                callback_data="exit_cmd",
            )
        ],
    ]


def _settings_keyboard(
    locale: str, anonymous: bool, custom_name: Optional[str]
) -> List[List[InlineKeyboardButton]]:
    state = "✅" if anonymous else "❌"
    if custom_name:
        name_label = f"{NINJA_ICON} {custom_name} {NINJA_ICON}"
    else:
        name_label = get_locale(locale, TEXT_IDS.MINI_GAMES_SET_NAME_TEXT_ID)
    return [
        [
            InlineKeyboardButton(
                f"{get_locale(locale, TEXT_IDS.MINI_GAMES_ANONYMOUS_TEXT_ID)} {state}",
                callback_data="mg_anon",
            )
        ],
        [InlineKeyboardButton(name_label, callback_data="mg_setname")],
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.BACK_TO_MENU_KEYBOARD_TEXT_ID),
                callback_data="mg_hub",
            )
        ],
    ]


def _back_to_settings_keyboard(locale: str) -> List[List[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.BACK_TO_MENU_KEYBOARD_TEXT_ID),
                callback_data="mg_settings",
            )
        ]
    ]


def _get_settings(user_id: int) -> Optional[dict]:
    rows = DbManager.select_from(
        table_name=SETTINGS_TABLE, where="user_id = ?", where_args=(user_id,)
    )
    return rows[0] if rows else None


def is_anonymous(user_id: int) -> bool:
    """Whether ``user_id`` plays under an alias. Anonymous by default (no row yet)."""
    row = _get_settings(user_id)
    return bool(row["anonymous"]) if row else True


def get_anonymous_name(user_id: int) -> Optional[str]:
    """The user's custom alias, or None when they never set one."""
    row = _get_settings(user_id)
    return row["name"] if row and row["name"] else None


def set_anonymous(user_id: int, anonymous: bool) -> None:
    _write_settings(user_id, anonymous, get_anonymous_name(user_id))


def set_anonymous_name(user_id: int, name: str) -> None:
    _write_settings(user_id, is_anonymous(user_id), name)


def _write_settings(user_id: int, anonymous: bool, name: Optional[str]) -> None:
    DbManager.delete_from(SETTINGS_TABLE, where="user_id = ?", where_args=(user_id,))
    DbManager.insert_into(
        SETTINGS_TABLE,
        values=(user_id, int(anonymous), name),
        columns=("user_id", "anonymous", "name"),
    )


def anonymous_display_name(user_id: int) -> str:
    """The name an anonymous player is shown under: their 🥷-wrapped custom alias, or a
    random one when they never set a custom alias."""
    custom = get_anonymous_name(user_id)
    if custom:
        return f"{NINJA_ICON} {custom} {NINJA_ICON}"
    return random_anonymous_name()


def random_anonymous_name() -> str:
    """Pick a random alias for an anonymous player (names live in anonymous_names.md)."""
    return choice(_load_anonymous_names())


def _load_anonymous_names() -> List[str]:
    global _anonymous_names  # pylint: disable=global-statement
    if not _anonymous_names:
        _anonymous_names = [
            line.strip()
            for line in read_md("anonymous_names").splitlines()
            if line.strip()
        ]
    return _anonymous_names


def _edit(
    context: CallbackContext,
    query,
    text: str,
    keyboard: List[List[InlineKeyboardButton]],
) -> None:
    context.bot.editMessageText(
        text=text,
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
