# -*- coding: utf-8 -*-
"""/prof command"""
from telegram import Update
from telegram.ext import CallbackContext
from module.shared import check_log, send_message
from module.data import Professor


def prof(update: Update, context: CallbackContext):
    """Called by the /prof command.
    Use: /prof <nomeprofessore> ...
    Shows all the professors that match the request

    Args:
        update: update event
        context: context passed by the handler
    """
    check_log(update, "prof")
    message_text = generate_prof_text(context.args)
    if len(message_text) > 4096:
        send_message(update, context, message_text)
    else:
        context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text, parse_mode='Markdown')


def generate_prof_text(names: list) -> str:
    """Called from the :meth:`prof` method.
    Executes the query and returns the text to send to the user

    Args:
        names: list of args passed to the context

    Returns:
        result of the query to send to the user
    """
    if not names:
        return "La sintassi del comando è: /prof <nomeprofessore>\n"

    professors = set()
    names_number = len(names)
    s_names = [].append(names[0])

    if names_number > 1:
        for name in names[1:-1]:
            s_names.append('{0} '.format(name))
           
        s_names.append(' {0}'.format(names[names_number - 1]))

    professors.update(Professor.find(where_name=s_names))

    if len(professors) > 0:
        output_str = '\n'.join(map(str, professors))
        output_str += "\nRisultati trovati: " + str(len(professors))
    else:
        output_str = "Nessun risultato trovato :(\n"

    return output_str
