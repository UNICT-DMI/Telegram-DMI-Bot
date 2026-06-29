"""/minigames command — the mini games hub.

Holds the hub itself and the helpers shared across mini games. Each individual game
(e.g. Tris) lives in its own module and plugs into the hub from there.
"""

from typing import List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from module.data.vars import TEXT_IDS
from module.shared import check_log
from module.utils.multi_lang_utils import get_locale


def minigames(update: Update, context: CallbackContext) -> None:
    """Called by /minigames and the "🕹 Mini Games" sticky button. Sends the hub."""
    check_log(update, "minigames")
    locale: str = update.message.from_user.language_code
    context.bot.sendMessage(
        chat_id=update.message.chat_id,
        text=get_locale(locale, TEXT_IDS.MINI_GAMES_HEADER_TEXT_ID),
        reply_markup=InlineKeyboardMarkup(_hub_keyboard(locale)),
    )


def _hub_keyboard(locale: str) -> List[List[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.TRIS_GAME_NAME_TEXT_ID),
                callback_data="ttt_mode",
            )
        ],
        [
            InlineKeyboardButton(
                get_locale(locale, TEXT_IDS.CLOSE_KEYBOARD_TEXT_ID),
                callback_data="exit_cmd",
            )
        ],
    ]


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
