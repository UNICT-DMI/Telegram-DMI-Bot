"""/report command"""
from typing import Optional

from telegram import Update, User
from telegram.ext import CallbackContext
from module.shared import check_log, config_map
from module.data.vars import PLACE_HOLDER, TEXT_IDS
from module.utils.multi_lang_utils import get_locale


def report(update: Update, context: CallbackContext) -> None:
    """Called by the /report command.
    Use: /report <word> ...
    Allows the user to report something to the administrators

    Args:
        update: update event
        context: context passed by the handler
    """
    check_log(update, "report")
    chat_id: int = update.message.chat_id
    chat_user: Optional[User] = update.message.from_user
    executed_command: str = update.message.text.split(' ')[0]
    locale: str = update.message.from_user.language_code

    if chat_id < 0:
        context.bot.sendMessage(chat_id=chat_id, text=get_locale(locale, TEXT_IDS.REPORT_ON_GROUP_WARNING_TEXT_ID).replace(PLACE_HOLDER, executed_command))
    elif not chat_user.username:
        context.bot.sendMessage(chat_id=chat_id, text=get_locale(locale, TEXT_IDS.REPORT_NO_USERNAME_WARNING_TEXT_ID).replace(PLACE_HOLDER, executed_command))
    else:
        if context.args:
            message = "⚠ Report ⚠\n"\
                        f"Username: @{chat_user.username}\n"

            if chat_user.first_name is not None:
                message += f"Nome/Name: {chat_user.first_name}\n"
            if chat_user.last_name is not None:
                message += f"Cognome/Surname: {chat_user.last_name}\n"

            message += f"Segnalazione/Content: {' '.join(context.args)}\n"

            context.bot.sendMessage(chat_id=config_map['representatives_group'], text=message)
            context.bot.sendMessage(chat_id=chat_id,
                                    text=get_locale(locale, TEXT_IDS.REPORT_RESPONSE_TEXT_ID).replace(PLACE_HOLDER, message))
        else:
            context.bot.sendMessage(chat_id=chat_id,
                                    text=get_locale(locale, TEXT_IDS.REPORT_WARNING_TEXT_ID))
