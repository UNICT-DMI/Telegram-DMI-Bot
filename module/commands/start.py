"""/start command"""
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import CallbackContext

from module.data.vars import TEXT_IDS
from module.shared import AULARIO, CLOUD, HELP, SEGNALAZIONE, read_md
from module.utils.multi_lang_utils import get_locale


def start(update: Update, context: CallbackContext):
    """Called by the /start command.
    Sends a welcome message

    Args:
        update: update event
        context: context passed by the handler
    """
    reply_keyboard = get_help_keyboard()
    message_text = get_locale(update.message.from_user.language_code, TEXT_IDS.START_TEXT_ID)
    context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text, reply_markup=reply_keyboard)


def get_help_keyboard() -> ReplyKeyboardMarkup:
    """Generates the reply keyboard shown at the bottom of the screen

    Returns:
        reply keyboard
    """
    kb = [
        [KeyboardButton(HELP), KeyboardButton(SEGNALAZIONE)],
        [KeyboardButton(AULARIO), KeyboardButton(CLOUD)],
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)
