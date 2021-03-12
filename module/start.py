# Telegram
from telegram import Update
from telegram.ext import CallbackContext

# Modules 
from module.shared import read_md
from module.utils.keyboard_utils import get_help_keyboard

def start(update: Update, context: CallbackContext):
    reply_keyboard = get_help_keyboard()
    message_text = read_md("start")
    context.bot.sendMessage(chat_id=update.message.chat_id,
                            text=message_text,
                            reply_markup=reply_keyboard)
