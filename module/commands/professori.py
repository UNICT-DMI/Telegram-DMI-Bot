# -*- coding: utf-8 -*-
"""/prof command"""
from telegram import Update
from telegram.ext import CallbackContext

from module.data.vars import TEXT_IDS, PLACE_HOLDER
from module.shared import check_log
from module.data import Professor
from module.utils.multi_lang_utils import get_locale


def prof(update: Update, context: CallbackContext) -> None:
    """Called by the /prof command.
    Use: /prof <nomeprofessore> ...
    Shows all the professors that match the request

    Args:
        update: update event
        context: context passed by the handler
    """
    check_log(update, "prof")
    message_text: str = generate_prof_text(update.message.from_user.language_code,context.args)

    message_text_list: list[str] = message_text.split('\n\n')
    professors, total_profs = message_text_list[:-1], message_text_list[-1]

    if len(professors) == 0:
        context.bot.sendMessage(chat_id=update.message.chat_id,
                                text=message_text)
        return

    # 15 professors are like ~3500 characters
    for index in range(0, len(professors), 15):
        message_text = '\n\n'.join(professors[index:index + 15])
        # if this is the last message, we could append the "Total results"
        if len(professors) <= index + 15:
            message_text += '\n\n' + total_profs

        context.bot.sendMessage(chat_id=update.message.chat_id,
                                text=message_text,
                                parse_mode='MarkdownV2',
                                disable_web_page_preview=True)


def generate_prof_text(locale: str, names: list) -> str:
    """Called from the :meth:`prof` method.
    Executes the query and returns the text to send to the user

    Args:
        locale: user's language
        names: list of args passed to the context

    Returns:
        result of the query to send to the user
    """
    if not names:
        return get_locale(locale, TEXT_IDS.PROF_USE_TEXT_ID)

    professors = set()
    names_number = len(names)
    s_names = [names[0]]

    if names_number > 1:
        for name in names[1:-1]:
            s_names.append('{0} '.format(name))

        s_names.append(' {0}'.format(names[names_number - 1]))

    professors.update(Professor.find(where_name=s_names))

    if len(professors) > 0:
        output_str = '\n'.join(map(str, professors))
        output_str += f'\n{get_locale(locale, TEXT_IDS.FOUND_RESULT_TEXT_ID).replace(PLACE_HOLDER, str(len(professors)))}'
    else:
        output_str = get_locale(locale, TEXT_IDS.NO_RESULT_FOUND_TEXT_ID)

    return output_str
