# Telegram
from telegram import Update
from telegram.ext import CallbackContext

# Modules
from module.shared import check_log, config_map

def report(update: Update, context: CallbackContext):
    check_log(update, context, "report")
    chat_id = update.message.chat_id
    chat_user = update.message.from_user
    executed_command = update.message.text.split(' ')[0]

    if chat_id < 0:
        context.bot.sendMessage(chat_id=chat_id, text="! La funzione %s non è ammessa nei gruppi" % executed_command)
    elif not chat_user.username:
        context.bot.sendMessage(chat_id=chat_id, text="La funzione %s non è ammessa se non si dispone di un username." % executed_command)
    else:
        if  context.args:
            message = "⚠️Segnalazione⚠️\n"

            if chat_user.username is not None:
                message += "Username: @" + chat_user.username + "\n"
            
            if chat_user.first_name is not None:
                message += "Nome: " + chat_user.first_name + "\n"

            if chat_user.last_name is not None:
                message += "Cognome: " + chat_user.last_name + "\n"

            message += "Segnalazione: " + " ".join(context.args) + "\n"

            context.bot.sendMessage(chat_id = config_map['representatives_group'], text = message)
            context.bot.sendMessage(chat_id = chat_id, text = "Resoconto segnalazione: \n" + message + "\n Grazie per la segnalazione, un rappresentante ti contatterà nel minor tempo possibile.")

        else:
            context.bot.sendMessage(chat_id = chat_id, text="Errore. Inserisci la tua segnalazione dopo /report (Ad esempio /report Invasione ingegneri in corso.)")