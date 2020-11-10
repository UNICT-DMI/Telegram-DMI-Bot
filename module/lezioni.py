# -*- coding: utf-8 -*-

# Telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler

# System libraries
import logging

# Modules
from module.shared import check_log, send_message

import sqlite3
import re

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def get_nome_giorno(day) -> str:
    switcher = {
        '1' : 'Lunedì',
        '2' : 'Martedì',
        '3' : 'Mercoledì',
        '4' : 'Giovedì',
        '5' : 'Venerdì'
    }

    return switcher.get(day, "Giorno non valido")

def get_lezioni_text_InLineKeyboard(context: CallbackContext) -> (str, InlineKeyboardMarkup): # restituisce una tuple formata da (message_text, InlineKeyboardMarkup)
    lezioni_user_data = context.user_data['lezioni']
    text_anno         = ", ".join([key for key in lezioni_user_data if "anno" in key]).replace("anno","")       # stringa contenente gli anni per cui la flag è true
    text_giorno       = ", ".join([key for key in lezioni_user_data if "giorno" in key]).replace("giorno","")   # stringa contenente le lezioni per cui la flag è true
    text_insegnamento = lezioni_user_data.get("insegnamento", "") #stringa contenente l'insegnamento

    message_text = "Anno: {}\nGiorno: {}\nInsegnamento: {}"\
        .format(text_anno if text_anno else "tutti",\
                text_giorno if text_giorno else "tutti",\
                text_insegnamento if text_insegnamento else "tutti")

    keyboard = [[]]
    keyboard.append([InlineKeyboardButton(" ~ Personalizza la ricerca ~ ", callback_data="_div")])
    keyboard.append([
        InlineKeyboardButton(" Anno ", callback_data="sm_lezioni_button_anno"),
        InlineKeyboardButton(" Giorno ", callback_data="sm_lezioni_button_giorno"),
    ])
    keyboard.append([
        InlineKeyboardButton(" Insegnamento ", callback_data="sm_lezioni_button_insegnamento"),
        InlineKeyboardButton(" Cerca ", callback_data="lezioni_button_search")
    ])

    return message_text, InlineKeyboardMarkup(keyboard)

def lezioni(update: Update, context: CallbackContext) -> None:
    check_log(update, context, "lezioni")

    if 'lezioni' in context.user_data:
        context.user_data['lezioni'].clear() # ripulisce il dict dell'user relativo al comando /lezioni da eventuali dati presenti
    else:
        context.user_data['lezioni'] = {}    # crea il dict che conterrà i dati del comando /lezioni all'interno della key ['lezioni'] di user data

    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    if chat_id != user_id: # forza ad eseguire il comando in una chat privata, anche per evitare di inondare un gruppo con i risultati
        context.bot.sendMessage(chat_id=chat_id, text="Questo comando è utilizzabile solo in privato")
        context.bot.sendMessage(chat_id=user_id, text="Dal comando lezioni che hai eseguito in un gruppo")
    
    message_text, inline_keyboard = get_lezioni_text_InLineKeyboard(context)
    context.bot.sendMessage(chat_id=user_id, text=message_text, reply_markup=inline_keyboard)

def lezioni_input_insegnamento(update: Update, context: CallbackContext) -> None:
    if context.user_data['lezioni'].get('cmd', 'null') == "input_insegnamento": #se effettivamente l'user aveva richiesto di modificare l'insegnamento...
        check_log(update, context, "lezioni_input_insegnamento")
        context.user_data['lezioni']['insegnamento'] = re.sub(r"^(?!=<[/])[Nn]ome:\s+", "", update.message.text) #ottieni il nome dell'insegnamento e salvalo nel dict
        del context.user_data['lezioni']['cmd'] #elimina la possibilità di modificare l'insegnamento fino a quando l'apposito button non viene premuto di nuovo
        message_text, inline_keyboard = get_lezioni_text_InLineKeyboard(context)
        context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text, reply_markup=inline_keyboard)

def lezioni_handler(update: Update, context: CallbackContext) -> None:
    callback_data = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    lezioni_user_data = context.user_data['lezioni']
    if "anno" in callback_data:
        if callback_data[20:] not in lezioni_user_data.keys(): #se non era presente, setta la key di [1 anno|2 anno| 3 anno] a true... 
            lezioni_user_data[callback_data[20:]] = True 
        else:
           del lezioni_user_data[callback_data[20:]] #... o elmina la key se era già presente
    elif "giorno" in callback_data:
        if callback_data[22:] not in lezioni_user_data.keys(): #se non era presente, setta la key del giorno[1|2|3...] a true... 
            lezioni_user_data[callback_data[22:]] = True 
        else:
           del lezioni_user_data[callback_data[22:]] #... o elmina la key se era già presente
    elif "search" in callback_data:
        message_text = lezioni_cmd(lezioni_user_data) #ottieni il risultato della query che soddisfa le richieste
        context.bot.editMessageText(chat_id=chat_id, message_id=message_id, text=update.callback_query.message.text) #rimuovi la inline keyboard e lascia il resoconto della query
        send_message(update, context, message_text) #manda il risutato della query suddividendo la stringa in più messaggi
        lezioni_user_data.clear() #ripulisci il dict
        return
    else:
        logger.error("lezioni_handler: an error has occurred")

    message_text, inline_keyboard = get_lezioni_text_InLineKeyboard(context)
    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=inline_keyboard)

def lezioni_button_giorno(update: Update, context: CallbackContext, chat_id, message_id) -> None:
    message_text = "Seleziona il giorno che ti interessa"

    keyboard = [[]]
    keyboard.append([
        InlineKeyboardButton("Lunedì",  callback_data="lezioni_button_giorno_1 giorno"),
        InlineKeyboardButton("Martedì", callback_data="lezioni_button_giorno_2 giorno"),
    ])
    keyboard.append([
        InlineKeyboardButton("Mercoledì", callback_data="lezioni_button_giorno_3 giorno"),
        InlineKeyboardButton("Giovedì",   callback_data="lezioni_button_giorno_4 giorno"),
    ])
    keyboard.append([
        InlineKeyboardButton("Venerdì", callback_data="lezioni_button_giorno_5 giorno"),
    ])

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=InlineKeyboardMarkup(keyboard))

def lezioni_button_insegnamento(update: Update, context: CallbackContext, chat_id, message_id) -> None:
    context.user_data['lezioni']['cmd'] = "input_insegnamento" # è in attesa di un messaggio nel formato corretto che imposti il valore del campo insegnamento
    message_text = "Inserire il nome della materia nel formato:\n" + \
                   "nome: nome insegnamento\n" + \
                   "Esempio:\n" +\
                   "nome: SisTeMi oPeRaTIvI"

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id)

def lezioni_button_anno(update: Update, context: CallbackContext, chat_id, message_id) -> None:
    message_text = "Seleziona l'anno che ti interessa"

    keyboard = [[]]
    keyboard.append([
        InlineKeyboardButton("Primo anno",   callback_data="lezioni_button_anno_1 anno"), #check here to change the received text
        InlineKeyboardButton("Secondo anno", callback_data="lezioni_button_anno_2 anno"),
        InlineKeyboardButton("Terzo anno",   callback_data="lezioni_button_anno_3 anno"),
    ])

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=InlineKeyboardMarkup(keyboard))

def lezioni_cmd(user_dict) -> str:
    output_str = []

    where_giorno = " or giorno_settimana = ".join([key.replace("giorno", "") for key in user_dict if "giorno" in key])  # stringa contenente i giorni per cui il dict contiene la key, separati da " = '[]' and not "
    where_anno = " or anno = ".join([key.replace(" anno", "") for key in user_dict if "anno" in key])                   # stringa contenente gli anni per cui il dict contiene la key, separate da "' or anno = '"
    where_insegnamento = user_dict.get("insegnamento", "")                                                              # stringa contenente l'insegnamento, se presente

    if where_giorno:
        where_giorno = f"and (giorno_settimana = {where_giorno})"
    else:
        where_giorno = ""

    if where_anno:
        where_anno = f"and (anno = {where_anno})"
    else:
        where_anno = ""

    query = f"""SELECT nome, giorno_settimana, ora_inizio, ora_fine, aula, anno 
				FROM lessons
				WHERE nome LIKE ? {where_giorno} {where_anno}"""

    conn = sqlite3.connect("data/DMI_DB.db")
    conn.row_factory = dict_factory
    cur = conn.cursor()

    try:
        cur.execute(query, ('%' + where_insegnamento + '%',))
    except Exception as e:
        print("The following lessons query could not be executed (command \\lezioni)")
        print(query)  # per controllare cosa è andato storto
        print("[error]: " + str(e))

    for item in cur.fetchall():
        output_str.append(lezioni_output(item))

    return check_output(output_str)

def lezioni_output(item) -> str:
    output = "*Insegnamento:* " + item["nome"]
    output += "\n*Giorno:* " + get_nome_giorno(item["giorno_settimana"])
    output += "\n*Ora:* " + item["ora_inizio"] + "-" + item["ora_fine"]
    output += "\n*Anno:* " + str(item["anno"])
    output += "\n*Aula:* " + str(item["aula"]) + "\n"
    return output

def dict_factory(cursor, row) -> dict:
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def check_output(output) -> str:
    if len(output):
        output_str = "\n".join(output)
        output_str += "\nRisultati trovati: " + str(len(output))
    else:
        output_str = "Nessun risultato trovato :(\n"

    return output_str
