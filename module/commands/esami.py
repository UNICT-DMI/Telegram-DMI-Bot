# -*- coding: utf-8 -*-
"""/esami command"""
import logging
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from module.data import Exam
from module.shared import check_log, send_message

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def esami(update: Update, context: CallbackContext):
    """Called by the /esami command.
    Shows the options available to execute an exam query.

    Args:
        update: update event
        context: context passed by the handler
    """
    check_log(update, "esami")

    if 'esami' in context.user_data:  #ripulisce il dict dell'user relativo al comando /esami da eventuali dati presenti
        context.user_data['esami'].clear()
    else:  #crea il dict che conterrà i dati del comando /esami all'interno della key ['esami'] di user data
        context.user_data['esami'] = {}

    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    if chat_id != user_id:  # forza ad eseguire il comando in una chat privata
        context.bot.sendMessage(chat_id=chat_id, text="Questo comando è utilizzabile solo in privato")
        context.bot.sendMessage(chat_id=user_id, text="Dal comando /esami che hai eseguito in un gruppo")

    message_text, inline_keyboard = get_esami_text_inline_keyboard(context)
    context.bot.sendMessage(chat_id=user_id, text=message_text, reply_markup=inline_keyboard)


def esami_handler(update: Update, context: CallbackContext):
    """Called by any of the buttons in the /esami command sub-menus.
    The action will change depending on the button:

    - anno -> adds / removes the selected year from the query parameters
    - sessione -> adds / removes the selected session from the query parameters
    - search -> executes the query with all the selected parametes and shows the result

    Args:
        update: update event
        context: context passed by the handler
    """
    callback_data = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id

    esami_user_data = context.user_data['esami']

    if "anno" in callback_data:
        if callback_data[-7:] not in esami_user_data.keys():
            #se non era presente, setta la key di [1° anno|2° anno| 3° anno] a true...
            esami_user_data[callback_data[-7:]] = True
        else:
            #... o elmina la key se era già presente
            del esami_user_data[callback_data[-7:]]
    elif "sessione" in callback_data:
        if 'sessione' + callback_data[22:] not in esami_user_data.keys():
            #se non era presente, setta la key di sessione[prima|seconda|terza] a true...
            esami_user_data['sessione' + callback_data[22:]] = True
        else:
            #... o elmina la key se era già presente
            del esami_user_data['sessione' + callback_data[22:]]
    elif "search" in callback_data:
        message_text = generate_esami_text(esami_user_data)  #ottieni il risultato della query che soddisfa le richieste
        context.bot.editMessageText(chat_id=chat_id, message_id=message_id, text=update.callback_query.message.text)
        send_message(update, context, message_text)  #manda il risutato della query suddividendo la stringa in più messaggi
        esami_user_data.clear()  #ripulisci il dict
        return
    else:
        logger.error("esami_handler: an error has occurred")

    message_text, inline_keyboard = get_esami_text_inline_keyboard(context)
    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=inline_keyboard)


def esami_button_anno(update: Update, context: CallbackContext, chat_id: int, message_id: int):
    """Called by one of the buttons of the /esami command.
    Allows the user to choose an year among the ones proposed

    Args:
        update: update event
        context: context passed by the handler
        chat_id: id of the chat of the user
        message_id: id of the sub-menu message
    """
    message_text = "Seleziona l'anno che ti interessa"

    keyboard = [[
        InlineKeyboardButton("1° anno", callback_data="esami_button_anno_1° anno"),
        InlineKeyboardButton("2° anno", callback_data="esami_button_anno_2° anno"),
        InlineKeyboardButton("3° anno", callback_data="esami_button_anno_3° anno"),
    ]]

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=InlineKeyboardMarkup(keyboard))


def esami_button_sessione(update: Update, context: CallbackContext, chat_id: int, message_id: int):
    """Called by one of the buttons of the /esami command.
    Allows the user to choose a session among the ones proposed

    Args:
        update: update event
        context: context passed by the handler
        chat_id: id of the chat of the user
        message_id: id of the sub-menu message
    """
    message_text = "Seleziona la sessione che ti interessa"

    keyboard = [[]]
    keyboard.append([
        InlineKeyboardButton("prima", callback_data="esami_button_sessione_prima"),
        InlineKeyboardButton("seconda", callback_data="esami_button_sessione_seconda"),
    ])
    keyboard.append([
        InlineKeyboardButton("terza", callback_data="esami_button_sessione_terza"),
        InlineKeyboardButton("straordinaria", callback_data="esami_button_sessione_straordinaria"),
    ])

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=InlineKeyboardMarkup(keyboard))


def esami_button_insegnamento(update: Update, context: CallbackContext, chat_id: int, message_id: int):
    """Called by one of the buttons of the /esami command.
    Allows the user to write the subject they want to search for

    Args:
        update: update event
        context: context passed by the handler
        chat_id: id of the chat of the user
        message_id: id of the sub-menu message
    """
    context.user_data['esami']['cmd'] = "input_insegnamento"  # attende che venga impostato il campo insegnamento
    message_text = "Inserire l'insegnamento desiderato nel formato:\n"\
                   "ins: nome insegnamento\n"\
                   "Esempio:\n"\
                   "ins: SisTeMi oPeRaTIvI"

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id)


def esami_input_insegnamento(update: Update, context: CallbackContext):
    """Called after :func:`esami_button_insegnamento`.
    Allows the user to input the wanted subject, in the format [Ii]ns: <insegnamento>

    Args:
        update: update event
        context: context passed by the handler
    """
    if context.user_data['esami'].get('cmd', None) == "input_insegnamento":
        #se effettivamente l'user aveva richiesto di modificare l'insegnamento...
        check_log(update, "esami_input_insegnamento")
        #ottieni il nome dell'insegnamento e salvalo nel dict
        context.user_data['esami']['insegnamento'] = re.sub(r"^(?!=<[/])[Ii]ns:\s+", "", update.message.text)
        #elimina la possibilità di modificare l'insegnamento fino a quando l'apposito button non viene premuto di nuovo
        del context.user_data['esami']['cmd']
        message_text, inline_keyboard = get_esami_text_inline_keyboard(context)
        context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text, reply_markup=inline_keyboard)


def get_esami_text_inline_keyboard(context: CallbackContext) -> (str, InlineKeyboardMarkup):
    """Generates the text and the InlineKeyboard for the /esami command, based on the current parameters.

    Args:
        update: update event
        context: context passed by the handler

    Returns:
        message_text and InlineKeyboardMarkup to use
    """
    esami_user_data = context.user_data['esami']

    text_anno = ", ".join([key for key in esami_user_data if "anno" in key])  # stringa contenente gli anni
    # stringa contenente le sessioni
    text_sessione = ", ".join([key for key in esami_user_data if "sessione" in key]).replace("sessione", "")
    text_insegnamento = esami_user_data.get("insegnamento", "")  # stringa contenente l'insegnamento

    message_text = "Anno: {}\nSessione: {}\nInsegnamento: {}"\
        .format(text_anno if text_anno else "tutti",\
                text_sessione if text_sessione else "tutti",\
                text_insegnamento if text_insegnamento else "tutti")

    keyboard = [[]]
    keyboard.append([InlineKeyboardButton(" ~ Personalizza la ricerca ~ ", callback_data="NONE")])
    keyboard.append([
        InlineKeyboardButton(" Anno ", callback_data="sm_esami_button_anno"),
        InlineKeyboardButton(" Sessione ", callback_data="sm_esami_button_sessione"),
    ])
    keyboard.append([
        InlineKeyboardButton(" Insegnamento ", callback_data="sm_esami_button_insegnamento"),
        InlineKeyboardButton(" Cerca ", callback_data="esami_button_search")
    ])

    return message_text, InlineKeyboardMarkup(keyboard)


def generate_esami_text(user_dict: dict) -> str:
    """Called by :meth:`esami` after the search button in the /esami command has been pressed.
    Executes the query and returns the text to send to the user

    Args:
        user_dict: dictionary that stores the user selected parameters to use in the query

    Returns:
        result of the query to send to the user
    """
    #stringa contenente le sessioni per cui il dict contiene la key, separate da ", "
    select_sessione = ", ".join([key for key in user_dict if "sessione" in key]).replace("sessione", "")
    #stringa contenente le sessioni per cui il dict contiene la key, separate da " = '[]' and not "
    where_sessione = " = '[]' or not ".join([key for key in user_dict if "sessione" in key]).replace("sessione", "")
    #stringa contenente gli anni per cui il dict contiene la key, separate da "' or anno = '"
    where_anno = "' or anno = '".join([key for key in user_dict if "anno" in key])
    #stringa contenente l'insegnamento, se presente
    where_insegnamento = user_dict.get("insegnamento", "")

    exams = Exam.find(select_sessione, where_sessione, where_anno, where_insegnamento)

    if len(exams) > 0:
        output_str = '\n'.join(map(str, exams))
        output_str += "\nRisultati trovati: " + str(len(exams))
    else:
        output_str = "Nessun risultato trovato :(\n"

    return output_str
