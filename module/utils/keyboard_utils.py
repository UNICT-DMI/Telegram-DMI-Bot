from telegram import KeyboardButton, ReplyKeyboardMarkup
from module.shared import HELP, AULARIO, SEGNALAZIONE, CLOUD

def get_help_keyboard() -> ReplyKeyboardMarkup:
    kb = [
            [KeyboardButton(HELP), KeyboardButton(SEGNALAZIONE)],
            [KeyboardButton(AULARIO), KeyboardButton(CLOUD)],  
         ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)
