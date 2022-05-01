# -*- coding: utf-8 -*-
"""/lezioni command"""
import logging
import re
from typing import Tuple, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, CallbackQuery
from telegram.ext import CallbackContext
from module.data import Lesson
from module.shared import check_log, send_message
from module.data.vars import TEXT_IDS, PLACE_HOLDER
from module.utils.multi_lang_utils import get_locale, get_locale_code

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def lezioni(update: Update, context: CallbackContext) -> None:
    """Called by the /lezioni command.
    Shows the options available to execute a lesson query.

    Args:
        update: update event
        context: context passed by the handler
    """
    check_log(update, "lezioni")

    if 'lezioni' in context.user_data:
        context.user_data[
            'lezioni'].clear()  # ripulisce il dict dell'user relativo al comando /lezioni da eventuali dati presenti
    else:
        context.user_data[
            'lezioni'] = {}  # crea il dict che conterrà i dati del comando /lezioni all'interno della key ['lezioni'] di user data

    user_id: int = update.message.from_user.id
    chat_id: int = update.message.chat_id
    locale: str = update.message.from_user.language_code

    if chat_id != user_id:  # forza ad eseguire il comando in una chat privata, anche per evitare di inondare un gruppo con i risultati
        context.bot.sendMessage(chat_id=chat_id, text=get_locale(locale, TEXT_IDS.USE_WARNING_TEXT_ID).replace(PLACE_HOLDER, "/lezioni"))
        context.bot.sendMessage(chat_id=user_id, text=get_locale(locale, TEXT_IDS.GROUP_WARNING_TEXT_ID).replace(PLACE_HOLDER, "/lezioni"))

    message_text, inline_keyboard = get_lezioni_text_InLineKeyboard(locale, context)
    context.bot.sendMessage(chat_id=user_id, text=message_text, reply_markup=inline_keyboard)


def lezioni_handler(update: Update, context: CallbackContext) -> None:
    """Called by any of the buttons in the /lezioni command sub-menus.
    The action will change depending on the button:

    - anno -> adds / removes the selected year from the query parameters
    - giorno -> adds / removes the selected day from the query parameters
    - search -> executes the query with all the selected parametes and shows the result

    Args:
        update: update event
        context: context passed by the handler
    """
    callback_data: Optional[CallbackQuery] = update.callback_query.data
    chat_id: int = update.callback_query.message.chat_id
    message_id: int = update.callback_query.message.message_id
    lezioni_user_data = context.user_data['lezioni']
    locale: str = update.callback_query.from_user.language_code
    if "anno" in callback_data:
        if callback_data[20:] not in lezioni_user_data.keys():
            # se non era presente, setta la key di [1 anno|2 anno| 3 anno] a true...
            lezioni_user_data[callback_data[20:]] = True
        else:
            # ... o elmina la key se era già presente
            del lezioni_user_data[callback_data[20:]]
    elif "giorno" in callback_data:
        if callback_data[22:] not in lezioni_user_data.keys():
            # se non era presente, setta la key del giorno[1|2|3...] a true...
            lezioni_user_data[callback_data[22:]] = True
        else:
            # ... o elmina la key se era già presente
            del lezioni_user_data[callback_data[22:]]
    elif "search" in callback_data:
        message_text = generate_lezioni_text(locale,
                                             lezioni_user_data)  # ottieni il risultato della query che soddisfa le richieste
        context.bot.editMessageText(chat_id=chat_id, message_id=message_id, text=update.callback_query.message.text)
        send_message(update, context,
                     message_text)  # manda il risutato della query suddividendo la stringa in più messaggi
        lezioni_user_data.clear()  # ripulisci il dict
        return
    else:
        logger.error("lezioni_handler: an error has occurred")

    message_text, inline_keyboard = get_lezioni_text_InLineKeyboard(locale, context)
    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=inline_keyboard)


def lezioni_button_anno(update: Update, context: CallbackContext, chat_id, message_id) -> None:
    """Called by one of the buttons of the /lezioni command.
    Allows the user to choose an year among the ones proposed

    Args:
        update: update event
        context: context passed by the handler
        chat_id: id of the chat of the user
        message_id: id of the sub-menu message
    """
    locale: str = get_locale_code(update)
    message_text: str = get_locale(locale, TEXT_IDS.SELECT_YEAR_TEXT_ID)

    keyboard = [[]]
    keyboard.append([
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.YEAR_1ST_TEXT_ID),
                             callback_data="lezioni_button_anno_1 anno"),
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.YEAR_2ND_TEXT_ID),
                             callback_data="lezioni_button_anno_2 anno"),
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.YEAR_3RD_TEXT_ID),
                             callback_data="lezioni_button_anno_3 anno"),
    ])

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id,
                                reply_markup=InlineKeyboardMarkup(keyboard))


def lezioni_button_giorno(update: Update, context: CallbackContext, chat_id, message_id) -> None:
    """Called by one of the buttons of the /lezioni command.
    Allows the user to choose a day among the ones proposed

    Args:
        update: update event
        context: context passed by the handler
        chat_id: id of the chat of the user
        message_id: id of the sub-menu message
    """
    locale: str = get_locale_code(update)
    message_text: str = get_locale(locale, TEXT_IDS.CLASSES_SELECT_DAY_TEXT_ID)

    keyboard = [[]]
    keyboard.append([
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.CLASSES_SELECT_DAY1_TEXT_ID),
                             callback_data="lezioni_button_giorno_1 giorno"),
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.CLASSES_SELECT_DAY2_TEXT_ID),
                             callback_data="lezioni_button_giorno_2 giorno"),
    ])
    keyboard.append([
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.CLASSES_SELECT_DAY3_TEXT_ID),
                             callback_data="lezioni_button_giorno_3 giorno"),
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.CLASSES_SELECT_DAY4_TEXT_ID),
                             callback_data="lezioni_button_giorno_4 giorno"),
    ])
    keyboard.append([
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.CLASSES_SELECT_DAY5_TEXT_ID),
                             callback_data="lezioni_button_giorno_5 giorno"),
    ])

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id,
                                reply_markup=InlineKeyboardMarkup(keyboard))


def lezioni_button_insegnamento(update: Update, context: CallbackContext, chat_id, message_id) -> None:
    """Called by one of the buttons of the /lezioni command.
    Allows the user to write the subject they want to search for

    Args:
        update: update event
        context: context passed by the handler
        chat_id: id of the chat of the user
        message_id: id of the sub-menu message
    """
    locale: str = get_locale_code(update)
    context.user_data['lezioni'][
        'cmd'] = "input_insegnamento"  # è in attesa di un messaggio nel formato corretto che imposti il valore del campo insegnamento
    message_text = get_locale(locale, TEXT_IDS.CLASSES_USAGE_TEXT_ID)
    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id)


def lezioni_input_insegnamento(update: Update, context: CallbackContext) -> None:
    """Called after :func:`lezioni_button_insegnamento`.
    Allows the user to input the wanted subject, in the format [Nn]ome: <insegnamento>

    Args:
        update: update event
        context: context passed by the handler
    """
    locale: str = get_locale_code(update)
    if context.user_data['lezioni'].get('cmd',
                                        'null') == "input_insegnamento":  # se effettivamente l'user aveva richiesto di modificare l'insegnamento...
        check_log(update, "lezioni_input_insegnamento")
        context.user_data['lezioni']['insegnamento'] = re.sub(r"^(?!=<[/])[Nn]ome:\s+", "",
                                                              update.message.text)  # ottieni il nome dell'insegnamento e salvalo nel dict
        del context.user_data['lezioni'][
            'cmd']  # elimina la possibilità di modificare l'insegnamento fino a quando l'apposito button non viene premuto di nuovo
        message_text, inline_keyboard = get_lezioni_text_InLineKeyboard(locale, context)
        context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text, reply_markup=inline_keyboard)


def get_lezioni_text_InLineKeyboard(locale: str, context: CallbackContext) -> Tuple[str, InlineKeyboardMarkup]:
    """Generates the text and the InlineKeyboard for the /lezioni command, based on the current parameters.

    Args:
        locale: user's language
        context: context passed by the handler

    Returns:
        message_text and InlineKeyboardMarkup to use
    """
    lezioni_user_data = context.user_data['lezioni']
    # stringa contenente gli anni per cui la flag è true
    text_anno = ", ".join([key for key in lezioni_user_data if "anno" in key]).replace("anno", "")
    # stringa contenente le lezioni per cui la flag è true
    text_giorno = ", ".join(
        [Lesson.INT_TO_DAY[key.replace(" giorno", "")] for key in lezioni_user_data if "giorno" in key])
    # stringa contenente l'insegnamento
    text_insegnamento = lezioni_user_data.get("insegnamento", "")

    message_text: str = "{}: {}\n{}: {}\n{}: {}" \
        .format(get_locale(locale, TEXT_IDS.SEARCH_YEAR_TEXT_ID),
                text_anno if text_anno else "tutti",
                get_locale(locale, TEXT_IDS.SEARCH_DAY_TEXT_ID),
                text_giorno if text_giorno else "tutti",
                get_locale(locale, TEXT_IDS.SEARCH_COURSE_TEXT_ID),
                text_insegnamento if text_insegnamento else "tutti")

    keyboard = [[]]
    keyboard.append([InlineKeyboardButton(get_locale(locale, TEXT_IDS.SEARCH_HEADER_TEXT_ID), callback_data="_div")])
    keyboard.append([
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.SEARCH_YEAR_TEXT_ID), callback_data="sm_lezioni_button_anno"),
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.SEARCH_DAY_TEXT_ID), callback_data="sm_lezioni_button_giorno"),
    ])
    keyboard.append([
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.SEARCH_COURSE_TEXT_ID), callback_data="sm_lezioni_button_insegnamento"),
        InlineKeyboardButton(get_locale(locale, TEXT_IDS.SEARCH_BUTTON_TEXT_ID), callback_data="lezioni_button_search")
    ])

    return message_text, InlineKeyboardMarkup(keyboard)


def generate_lezioni_text(locale: str, user_dict) -> str:
    """Called by :meth:`lezioni` after the search button in the /lezioni command has been pressed.
    Executes the query and returns the text to send to the user

    Args:
        locale: user's language
        user_dict: dictionary that stores the user selected parameters to use in the query

    Returns:
        result of the query to send to the user
    """
    # stringa contenente i giorni per cui il dict contiene la key, separati da " = '[]' and not "
    where_giorno = " or giorno_settimana = ".join([key.replace("giorno", "") for key in user_dict if "giorno" in key])
    # stringa contenente gli anni per cui il dict contiene la key, separate da "' or anno = '"
    where_anno = " or anno = ".join([key.replace(" anno", "") for key in user_dict if "anno" in key])
    # stringa contenente l'insegnamento, se presente
    where_nome = user_dict.get("insegnamento", "")

    lessons = Lesson.find(where_anno=where_anno, where_giorno=where_giorno, where_nome=where_nome)
    if len(lessons) > 0:
        output_str = '\n'.join(map(str, lessons))
        output_str += f'\n{get_locale(locale, TEXT_IDS.FOUND_RESULT_TEXT_ID).replace(PLACE_HOLDER, str(len(lessons)))}'
    else:
        output_str = get_locale(locale, TEXT_IDS.NO_RESULT_FOUND_TEXT_ID)

    return output_str
