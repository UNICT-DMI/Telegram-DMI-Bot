"""Common query callback families"""
import random
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from module.shared import CUSicon, check_log, read_md
# Needed to correctly run functions using globals()
from module.aulario import aulario, aulario_subj
from module.commands.esami import esami_button_anno, esami_button_insegnamento, esami_button_sessione
from module.commands.lezioni import lezioni_button_anno, lezioni_button_giorno, lezioni_button_insegnamento
from module.commands.help import rapp_menu


def submenu_handler(update: Update, context: CallbackContext):
    """Called by "sm_.*" callbacks.
    Opens the requested sub-menu, usually by editing the message and adding an InlineKeyboard

    Args:
        update (:class:`Update`): update event
        context (:class:`CallbackContext`): context passed by the handler
    """
    query = update.callback_query
    data = query.data

    func_name = data[3:len(data)]
    globals()[func_name](query, context, query.message.chat_id, query.message.message_id)


def md_handler(update: Update, context: CallbackContext):
    """Called by any query that needs to show the contents of a markdown file to the user

    Args:
        update (:class:`Update`): update event
        context (:class:`CallbackContext`): context passed by the handler
    """
    query = update.callback_query

    data = query.data.replace("md_", "")
    message_text = read_md(data)

    if data == "help":
        message_text = message_text.replace("<cusicon>", CUSicon[random.randint(0, 5)])

    check_log(update, context, data, 1)

    context.bot.editMessageText(text=message_text, chat_id=query.message.chat_id, message_id=query.message.message_id, parse_mode=ParseMode.MARKDOWN)


def informative_callback(update: Update, context: CallbackContext):
    """Called by any command that needs to show information to the user

    Args:
        update (:class:`Update`): update event
        context (:class:`CallbackContext`): context passed by the handler
    """
    # controllo per poter gestire i comandi (/comando) e i messaggi inviati premendo i bottoni (❔ Help)
    if update.message.text[0] == '/':
        cmd = update.message.text.split(' ')[0][1:]  #prende solo la prima parola del messaggio (cioè il comando) escludendo lo slash
    else:
        cmd = update.message.text.split(' ')[1].lower()  # prende la prima parola dopo l'emoji
    check_log(update, context, cmd)
    message_text = read_md(cmd)
    context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text, parse_mode=ParseMode.MARKDOWN)


def submenu_with_args_handler(update: Update, context: CallbackContext):
    """Called by the aulario.

    Args:
        update (:class:`Update`): update event
        context (:class:`CallbackContext`): context passed by the handler
    """
    query = update.callback_query
    data = query.data
    func_name = data.split('&')[1]
    arg = data.split('&')[2]

    globals()[func_name](query, context, query.message.chat_id, query.message.message_id, arg)


def none_handler(update: Update, context: CallbackContext):
    """Called when the user clicks an unactive button.
    Stops the spinning circle

    Args:
        update (:class:`Update`): update event
        context (:class:`CallbackContext`): context passed by the handler
    """
    update.callback_query.answer()


def exit_handler(update: Update, context: CallbackContext):
    """Called when the user wants to close a sub-menu.
    Reduces the message to a point and removes any inlinekeyboard

    Args:
        update (:class:`Update`): update event
        context (:class:`CallbackContext`): context passed by the handler
    """
    query = update.callback_query
    context.bot.editMessageText(text='.', chat_id=query.message.chat_id, message_id=query.message.message_id)
