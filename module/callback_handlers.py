"""Common query callback families"""
from typing import Optional

from telegram import ParseMode, Update, CallbackQuery
from telegram.ext import CallbackContext

from module.data.vars import ON_DEMAND_TEXTS
from module.shared import CUSicon, check_log, read_md
# Needed to correctly run functions using globals()
from module.commands.aulario import aulario
from module.commands.esami import esami_button_anno, esami_button_insegnamento, esami_button_sessione
from module.commands.lezioni import lezioni_button_anno, lezioni_button_giorno, lezioni_button_insegnamento
from module.commands.help import help_back_to_menu, help_dip_cdl, help_rapp_menu, help_segr, help_ersu, help_misc, help_projects_acknowledgements
from module.utils.multi_lang_utils import get_on_demand_text


def submenu_handler(update: Update, context: CallbackContext) -> None:
    """Called by sm_.* callbacks.
    Opens the requested sub-menu, usually by editing the message and adding an InlineKeyboard

    Args:
        update: update event
        context: context passed by the handler
    """
    query = update.callback_query
    data = query.data

    func_name = data[3:len(data)]
    globals()[func_name](query, context, query.message.chat_id, query.message.message_id)


def localization_handler(update: Update, context: CallbackContext) -> None:
    """Called by any query that needs to show a localized text to the user

    Args:
        update: update event
        context: context passed by the handler
    """
    locale: str = update.callback_query.from_user.language_code
    query: Optional[CallbackQuery] = update.callback_query
    data: str = query.data.replace("localization_", "")
    message_text: str = get_on_demand_text(locale, data)
    check_log(update, data, is_query=True)
    context.bot.editMessageText(text=message_text, chat_id=query.message.chat_id, message_id=query.message.message_id, parse_mode=ParseMode.MARKDOWN)


def md_handler(update: Update, context: CallbackContext) -> None:
    """Called by any query that needs to show the contents of a markdown file to the user

    Args:
        update: update event
        context: context passed by the handler
    """
    query = update.callback_query

    data = query.data.replace("md_", "")
    message_text = read_md(data)

    check_log(update, data, is_query=True)

    context.bot.editMessageText(text=message_text, chat_id=query.message.chat_id, message_id=query.message.message_id, parse_mode=ParseMode.MARKDOWN)


def informative_callback(update: Update, context: CallbackContext) -> None:
    """Called by any command that needs to show information to the user

    Args:
        update: update event
        context: context passed by the handler
    """
    locale: str = update.message.from_user.language_code
    # controllo per poter gestire i comandi (/comando) e i messaggi inviati premendo i bottoni (❔ Help)
    if update.message.text[0] == '/':
        cmd = update.message.text.split(' ')[0][1:]  #prende solo la prima parola del messaggio (cioè il comando) escludendo lo slash
        if cmd.find('@') != -1:
            cmd = cmd.split('@')[0]
    else:
        cmd = update.message.text.split(' ')[1].lower()  # prende la prima parola dopo l'emoji
    if cmd in ON_DEMAND_TEXTS.values():
        index_key: int = list(ON_DEMAND_TEXTS.values()).index(cmd)
        message_text: str = get_on_demand_text(locale, list(ON_DEMAND_TEXTS.keys())[index_key])
    else:
        if cmd == "report":
            cmd = "segnalazione" 
        message_text = read_md(cmd)
    check_log(update, cmd)
    if_disable_preview = True if cmd == 'cloud' else False
    context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=if_disable_preview)


def none_handler(update: Update, context: CallbackContext) -> None:
    """Called when the user clicks an unactive button.
    Stops the spinning circle

    Args:
        update: update event
        context: context passed by the handler
    """
    update.callback_query.answer()


def exit_handler(update: Update, context: CallbackContext) -> None:
    """Called when the user wants to close a sub-menu.
    Removes the message from the user's chat

    Args:
        update: update event
        context: context passed by the handler
    """
    query = update.callback_query
    context.bot.deleteMessage(chat_id=query.message.chat_id, message_id=query.message.message_id)

