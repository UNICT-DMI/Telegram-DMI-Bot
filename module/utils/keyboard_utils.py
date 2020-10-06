from telegram import KeyboardButton, ReplyKeyboardMarkup


def get_help_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton('❔ Help')
        ],
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)
