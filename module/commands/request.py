"""/request command"""
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from module.shared import config_map
from module.data import DbManager


def request(update: Update, context: CallbackContext):
    """Called by the /request command.
    Use: /request <nome> <cognome> <e-mail>
    Allows the user to ask the developers to give him access the the /drive and /gitlab commands

    Args:
        update: update event
        context: context passed by the handler
    """
    chat_id = update.message.chat_id

    if chat_id > 0:
        # if we do not find any chat_id in the db
        if DbManager.count_from(table_name="Chat_id_List", where="Chat_id = ?", where_args=(chat_id,)) == 0:
            message_text = "✉️ Richiesta inviata"
            keyboard = [[]]

            args = tuple(map(lambda e: re.sub(r'<|>', '', e), context.args))
            username = update.message.from_user.username if update.message.from_user.username else "username"

            if len(args) == 3 and re.search(r"^[^ @]+@[^ @]+\.[^ @]+$", args[2]):  # args must be of type ("Nome", "Cognome", "E-mail")
                text_send = f"{' '.join(args)} {username}"
                keyboard.append([InlineKeyboardButton("Accetta", callback_data=f"drive_accept_{chat_id}")])
                context.bot.sendMessage(chat_id=config_map['dev_group_chatid'], text=text_send, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                message_text = "Uso: /request <nome> <cognome> <e-mail>\n(unire nomi o cognomi multipli Es: Di mauro -> Dimauro)"
        else:
            message_text = "Hai già effettuato la richiesta di accesso"
    else:
        message_text = "Non è possibile utilizzare /request in un gruppo"

    context.bot.sendMessage(chat_id=chat_id, text=message_text)


def request_handler(update: Update, context: CallbackContext):
    """Called when a request sent by a user is accepted.
    Adds the user to the database to allow him to use the /drive and /gitlab commands

    Args:
        update: update event
        context: context passed by the handler
    """
    chat_id = update.callback_query.data.replace("drive_accept_", "")  # get the chat id
    values = update.callback_query.message.text.split(" ")  # get all the info from the message
    values.append(chat_id)  # produce an array with ("Nome", "Cognome", "E-mail", "Username", "Chat_id")

    DbManager.insert_into(table_name="Chat_id_List", columns=("Nome", "Cognome", "`E-mail`", "Username", "Chat_id"), values=tuple(values))
    context.bot.sendMessage(chat_id=chat_id, text="🔓 La tua richiesta è stata accettata. Leggi il file README")
    context.bot.sendDocument(chat_id=chat_id, document=open('data/README.pdf', 'rb'))

    context.bot.editMessageText(text=f"Richiesta di {values[0]} {values[1]} estinta",
                                chat_id=config_map['dev_group_chatid'],
                                message_id=update.callback_query.message.message_id)


def add_db(update: Update, context: CallbackContext):
    """Called by the /add_db command. Can only be called in the dev group.
    Use: /add_db <nome> <cognome> <e-mail> <username> <chatid>
    Adds a new user to the database of users allowed to access the /drive and /gitlab commands

    Args:
        update: update event
        context: context passed by the handler
    """
    chat_id = update.message.chat_id

    if chat_id == config_map['dev_group_chatid']:
        args = context.args
        if args is not None and len(args) == 5:  # args must be of type ("Nome", "Cognome", "E-mail", "Username", "Chat_id")
            DbManager.insert_into(table_name="Chat_id_List", columns=("Nome", "Cognome", "`E-mail`", "Username", "Chat_id"), values=tuple(args))
            context.bot.sendMessage(chat_id=args[4], text="🔓 La tua richiesta è stata accettata. Leggi il file README")
            context.bot.sendDocument(chat_id=args[4], document=open('data/README.pdf', 'rb'))
        else:
            context.bot.sendMessage(chat_id=chat_id, text="/add_db <nome> <cognome> <e-mail> <username> <chat_id>")
