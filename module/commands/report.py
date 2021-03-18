"""/report command"""
from telegram import Update
from telegram.ext import CallbackContext
from module.shared import check_log, config_map


def report(update: Update, context: CallbackContext):
    """Called by the /report command.
    Use: /report <word> ...
    Allows the user to report something to the administrators

    Args:
        update: update event
        context: context passed by the handler
    """
    check_log(update, "report")
    chat_id = update.message.chat_id
    chat_user = update.message.from_user
    executed_command = update.message.text.split(' ')[0]

    if chat_id < 0:
        context.bot.sendMessage(chat_id=chat_id, text=f"! La funzione {executed_command} non è ammessa nei gruppi")
    elif not chat_user.username:
        context.bot.sendMessage(chat_id=chat_id, text=f"La funzione {executed_command} non è ammessa se non si dispone di un username.")
    else:
        if context.args:
            message = "⚠️Segnalazione⚠️\n"\
                        f"Username: @{chat_user.username}\n"

            if chat_user.first_name is not None:
                message += f"Nome: {chat_user.first_name}\n"
            if chat_user.last_name is not None:
                message += f"Cognome: {chat_user.last_name}\n"

            message += f"Segnalazione: {' '.join(context.args)}\n"

            context.bot.sendMessage(chat_id=config_map['representatives_group'], text=message)
            context.bot.sendMessage(chat_id=chat_id,
                                    text=f"Resoconto segnalazione: \n{message}"
                                    "\n Grazie per la segnalazione, un rappresentante ti contatterà nel minor tempo possibile.")
        else:
            context.bot.sendMessage(chat_id=chat_id,
                                    text="Errore. Inserisci la tua segnalazione dopo /report (Ad esempio /report Invasione ingegneri in corso.)")
