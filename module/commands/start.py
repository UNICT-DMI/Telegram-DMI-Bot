"""/start command"""
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import CallbackContext

from module.data.vars import TEXT_IDS
from module.utils.multi_lang_utils import get_locale


def start(update: Update, context: CallbackContext) -> None:
    """Called by the /start command.
    Sends a welcome message

    Args:
        update: update event
        context: context passed by the handler
    """
    reply_keyboard: ReplyKeyboardMarkup = get_help_keyboard(update.message.from_user.language_code)
    message_text: str = get_locale(update.message.from_user.language_code, TEXT_IDS.START_TEXT_ID)
    context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text, reply_markup=reply_keyboard)


def get_help_keyboard(locale: str) -> ReplyKeyboardMarkup:
    """Generates the reply keyboard shown at the bottom of the screen

    Returns:
        reply keyboard
    """
    kb = [
        [
            KeyboardButton(get_locale(locale, TEXT_IDS.HELP_KEYBOARD_TEXT_ID)),
            KeyboardButton(get_locale(locale, TEXT_IDS.REPORT_TO_KEYBOARD_TEXT_ID))
        ],
        [
            KeyboardButton(get_locale(locale, TEXT_IDS.AULARIO_KEYBOARD_TEXT_ID)),
            KeyboardButton(get_locale(locale, TEXT_IDS.CLOUD_KEYBOARD_TEXT_ID))
        ],
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)
