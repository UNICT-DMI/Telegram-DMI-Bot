# -*- coding: utf-8 -*-
"""/esami command"""
import logging
import re
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, CallbackQuery
from telegram.ext import CallbackContext
from module.data import Exam
from module.shared import check_log, send_message
from module.data.vars import TEXT_IDS, PLACE_HOLDER
from module.utils.multi_lang_utils import get_locale, get_locale_code

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def esami(update: Update, context: CallbackContext) -> None:
    """Called by the /esami command.
    Shows the options available to execute an exam query.

    Args:
        update: update event
        context: context passed by the handler
    """
    check_log(update, "esami")

    if 'esami' in context.user_data:  # ripulisce il dict dell'user relativo al comando /esami da eventuali dati presenti
        context.user_data['esami'].clear()
    else:  # crea il dict che conterrà i dati del comando /esami all'interno della key ['esami'] di user data
        context.user_data['esami'] = {}

    user_id: int = update.message.from_user.id
    chat_id: int = update.message.chat_id
    locale: str = update.message.from_user.language_code
    if chat_id != user_id:  # forza ad eseguire il comando in una chat privata
        context.bot.sendMessage(chat_id=chat_id,
                                text=get_locale(locale, TEXT_IDS.USE_WARNING_TEXT_ID).replace(PLACE_HOLDER, "/esami"))
        context.bot.sendMessage(chat_id=user_id,
                                text=get_locale(locale, TEXT_IDS.GROUP_WARNING_TEXT_ID).replace(PLACE_HOLDER, "/esami"))

    message_text, inline_keyboard = get_esami_text_inline_keyboard(locale, context)
    context.bot.sendMessage(chat_id=user_id, text=message_text, reply_markup=inline_keyboard)


def esami_handler(update: Update, context: CallbackContext) -> None:
    """Called by any of the buttons in the /esami command sub-menus.
    The action will change depending on the button:

    - anno -> adds / removes the selected year from the query parameters
    - sessione -> adds / removes the selected session from the query parameters
    - search -> executes the query with all the selected parametes and shows the result

    Args:
        update: update event
        context: context passed by the handler
    """
    callback_data: Optional[CallbackQuery] = update.callback_query.data
    chat_id: int = update.callback_query.message.chat_id
    message_id: int = update.callback_query.message.message_id
    locale: str = update.callback_query.from_user.language_code

    esami_user_data = context.user_data['esami']

    if "anno" in callback_data:
        if callback_data[-7:] not in esami_user_data.keys():
            # se non era presente, setta la key di [1° anno|2° anno| 3° anno] a true...
            esami_user_data[callback_data[-7:]] = True
        else:
            # ... o elmina la key se era già presente
            del esami_user_data[callback_data[-7:]]
    elif "sessione" in callback_data:
        if 'sessione' + callback_data[22:] not in esami_user_data.keys():
            # se non era presente, setta la key di sessione[prima|seconda|terza] a true...
            esami_user_data['sessione' + callback_data[22:]] = True
        else:
            # ... o elmina la key se era già presente
            del esami_user_data['sessione' + callback_data[22:]]
    elif "search" in callback_data:
        message_text = generate_esami_text(locale,
                                           esami_user_data)  # ottieni il risultato della query che soddisfa le richieste
        context.bot.editMessageText(chat_id=chat_id, message_id=message_id, text=update.callback_query.message.text)
        send_message(update, context,
                     message_text)  # manda il risutato della query suddividendo la stringa in più messaggi
        esami_user_data.clear()  # ripulisci il dict
        return
    else:
        logger.error("esami_handler: an error has occurred")

    message_text, inline_keyboard = get_esami_text_inline_keyboard(locale, context)
    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=inline_keyboard)


def esami_button_anno(update: Update, context: CallbackContext, chat_id: int, message_id: int) -> None:
    """Called by one of the buttons of the /esami command.
    Allows the user to choose an year among the ones proposed

    Args:
        update: update event
        context: context passed by the handler
        chat_id: id of the chat of the user
        message_id: id of the sub-menu message
    """
    locale: str = get_locale_code(update)
    message_text: str = get_locale(locale, TEXT_IDS.SELECT_YEAR_TEXT_ID)

    keyboard = [[
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.YEAR_1ST_TEXT_ID), callback_data="esami_button_anno_1° anno"),
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.YEAR_2ND_TEXT_ID), callback_data="esami_button_anno_2° anno"),
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.YEAR_3RD_TEXT_ID), callback_data="esami_button_anno_3° anno"),
    ]]

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id,
                                reply_markup=InlineKeyboardMarkup(keyboard))


def esami_button_sessione(update: Update, context: CallbackContext, chat_id: int, message_id: int) -> None:
    """Called by one of the buttons of the /esami command.
    Allows the user to choose a session among the ones proposed

    Args:
        update: update event
        context: context passed by the handler
        chat_id: id of the chat of the user
        message_id: id of the sub-menu message
    """
    locale: str = get_locale_code(update)
    message_text: str = get_locale(locale, TEXT_IDS.EXAMS_SELECT_SESSION_TEXT_ID)

    keyboard = [[]]
    keyboard.append([
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.EXAMS_SESSION_1_TEXT_ID), callback_data="esami_button_sessione_prima"),
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.EXAMS_SESSION_2_TEXT_ID), callback_data="esami_button_sessione_seconda"),
    ])
    keyboard.append([
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.EXAMS_SESSION_3_TEXT_ID), callback_data="esami_button_sessione_terza"),
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.EXAMS_SESSION_4_TEXT_ID), callback_data="esami_button_sessione_straordinaria"),
    ])

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id,
                                reply_markup=InlineKeyboardMarkup(keyboard))


def esami_button_insegnamento(update: Update, context: CallbackContext, chat_id: int, message_id: int) -> None:
    """Called by one of the buttons of the /esami command.
    Allows the user to write the subject they want to search for

    Args:
        update: update event
        context: context passed by the handler
        chat_id: id of the chat of the user
        message_id: id of the sub-menu message
    """
    locale: str = get_locale_code(update)
    context.user_data['esami']['cmd'] = "input_insegnamento"  # attende che venga impostato il campo insegnamento
    message_text = get_locale(locale, TEXT_IDS.EXAMS_USAGE_TEXT_ID)

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id)


def esami_input_insegnamento(update: Update, context: CallbackContext) -> None:
    """Called after :func:`esami_button_insegnamento`.
    Allows the user to input the wanted subject, in the format [Ii]ns: <insegnamento>

    Args:
        update: update event
        context: context passed by the handler
    """
    locale: str = get_locale_code(update)
    if context.user_data['esami'].get('cmd', None) == "input_insegnamento":
        # se effettivamente l'user aveva richiesto di modificare l'insegnamento...
        check_log(update, "esami_input_insegnamento")
        # ottieni il nome dell'insegnamento e salvalo nel dict
        context.user_data['esami']['insegnamento'] = re.sub(r"^(?!=<[/])[Ii]ns:\s+", "", update.message.text)
        # elimina la possibilità di modificare l'insegnamento fino a quando l'apposito button non viene premuto di nuovo
        del context.user_data['esami']['cmd']
        message_text, inline_keyboard = get_esami_text_inline_keyboard(locale, context)
        context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text, reply_markup=inline_keyboard)


def get_esami_text_inline_keyboard(locale: str, context: CallbackContext) -> (str, InlineKeyboardMarkup):
    """Generates the text and the InlineKeyboard for the /esami command, based on the current parameters.

    Args:
        locale: user's language
        context: context passed by the handler

    Returns:
        message_text and InlineKeyboardMarkup to use
    """
    esami_user_data = context.user_data['esami']

    text_anno = ", ".join([key for key in esami_user_data if "anno" in key])  # stringa contenente gli anni
    # stringa contenente le sessioni
    text_sessione = ", ".join([key for key in esami_user_data if "sessione" in key]).replace("sessione", "")
    text_insegnamento = esami_user_data.get("insegnamento", "")  # stringa contenente l'insegnamento

    message_text: str = "{}: {}\n{}: {}\n{}: {}".format(
        get_locale(locale, TEXT_IDS.SEARCH_YEAR_TEXT_ID),
        text_anno if text_anno else "tutti",
        get_locale(locale, TEXT_IDS.SEARCH_SESSION_TEXT_ID),
        text_sessione if text_sessione else "tutti",
        get_locale(locale, TEXT_IDS.SEARCH_COURSE_TEXT_ID),
        text_insegnamento if text_insegnamento else "tutti")

    keyboard = [[]]
    keyboard.append([InlineKeyboardButton(get_locale(locale, TEXT_IDS.SEARCH_HEADER_TEXT_ID), callback_data="NONE")])
    keyboard.append([
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.SEARCH_YEAR_TEXT_ID), callback_data="sm_esami_button_anno"),
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.SEARCH_SESSION_TEXT_ID), callback_data="sm_esami_button_sessione"),
    ])
    keyboard.append([
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.SEARCH_COURSE_TEXT_ID), callback_data="sm_esami_button_insegnamento"),
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.SEARCH_BUTTON_TEXT_ID), callback_data="esami_button_search")
    ])

    return message_text, InlineKeyboardMarkup(keyboard)


def generate_esami_text(locale: str, user_dict: dict) -> str:
    """Called by :meth:`esami` after the search button in the /esami command has been pressed.
    Executes the query and returns the text to send to the user

    Args:
        locale: user's language
        user_dict: dictionary that stores the user selected parameters to use in the query

    Returns:
        result of the query to send to the user
    """
    # stringa contenente le sessioni per cui il dict contiene la key, separate da ", "
    select_sessione = ", ".join([key for key in user_dict if "sessione" in key]).replace("sessione", "")
    # stringa contenente le sessioni per cui il dict contiene la key, separate da " = '[]' and not "
    where_sessione = " = '[]' or not ".join([key for key in user_dict if "sessione" in key]).replace("sessione", "")
    # stringa contenente gli anni per cui il dict contiene la key, separate da "' or anno = '"
    where_anno = "' or anno = '".join([key for key in user_dict if "anno" in key])
    # stringa contenente l'insegnamento, se presente
    where_insegnamento = user_dict.get("insegnamento", "")

    exams = Exam.find(select_sessione, where_sessione, where_anno, where_insegnamento)

    if len(exams) > 0:
        output_str = '\n'.join(map(str, exams))
        output_str += f'\n{get_locale(locale, TEXT_IDS.FOUND_RESULT_TEXT_ID).replace(PLACE_HOLDER, str(len(exams)))}'
    else:
        output_str = get_locale(locale, TEXT_IDS.NO_RESULT_FOUND_TEXT_ID)

    return output_str
