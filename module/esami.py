# -*- coding: utf-8 -*-

# Telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CallbackQueryHandler

# System libraries
import logging
import sqlite3
import re

# Modules
from module.shared import check_log,send_message

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def esami_button_anno(update: Update, context: CallbackContext, chat_id, message_id):
    message_text = "Seleziona l'anno che ti interessa"

    keyboard = [
        [
            InlineKeyboardButton("1° anno", callback_data="esami_button_anno_1° anno"),
            InlineKeyboardButton("2° anno", callback_data="esami_button_anno_2° anno"),
            InlineKeyboardButton("3° anno", callback_data="esami_button_anno_3° anno"),
        ]
    ]

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=InlineKeyboardMarkup(keyboard))

def esami_button_insegnamento(update: Update, context: CallbackContext, chat_id, message_id):
    context.user_data['esami']['cmd'] = "input_insegnamento" #è in attesa di un messaggio nel formato corretto che imposti il valore del campo insegnamento
    message_text = "Inserire l'insegnamento desiderato nel formato:\n" + \
                   "ins: nome insegnamento\n" + \
                   "Esempio:\n" +\
                   "ins: SisTeMi oPeRaTIvI"

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id)

def esami_button_sessione(update: Update, context: CallbackContext, chat_id, message_id):
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

def esami_handler(update: Update, context: CallbackContext):
    callback_data = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id

    esami_user_data = context.user_data['esami']

    if "anno" in callback_data:
        if callback_data[-7:] not in esami_user_data.keys(): #se non era presente, setta la key di [1° anno|2° anno| 3° anno] a true... 
            esami_user_data[callback_data[-7:]] = True 
        else:
           del esami_user_data[callback_data[-7:]] #... o elmina la key se era già presente
    elif "sessione" in callback_data:
        if 'sessione' + callback_data[22:] not in esami_user_data.keys(): #se non era presente, setta la key di sessione[prima|seconda|terza] a true... 
            esami_user_data['sessione' + callback_data[22:]] = True 
        else:
           del esami_user_data['sessione' + callback_data[22:]] #... o elmina la key se era già presente
    elif "search" in callback_data:
        message_text = esami_cmd(esami_user_data) #ottieni il risultato della query che soddisfa le richieste
        context.bot.editMessageText(chat_id=chat_id, message_id=message_id, text=update.callback_query.message.text) #rimuovi la inline keyboard e lascia il resoconto della query
        send_message(update, context, message_text) #manda il risutato della query suddividendo la stringa in più messaggi
        esami_user_data.clear() #ripulisci il dict
        return
    else:
        logger.error("esami_handler: an error has occurred")

    message_text, inline_keyboard = get_esami_text_inline_keyboard(context)
    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=inline_keyboard)

# eliminate
def esami_button():
    output = "Scrivi /esami inserendo almeno uno dei seguenti parametri: giorno, materia, sessione (prima, seconda, terza, straordinaria)"
    return output

def esami_input_insegnamento(update: Update, context: CallbackContext):
    if context.user_data['esami'].get('cmd', 'null') == "input_insegnamento": #se effettivamente l'user aveva richiesto di modificare l'insegnamento...
        check_log(update, context, "esami_input_insegnamento")
        context.user_data['esami']['insegnamento'] = re.sub(r"^(?!=<[/])[Ii]ns:\s+", "", update.message.text) #ottieni il nome dell'insegnamento e salvalo nel dict
        del context.user_data['esami']['cmd'] #elimina la possibilità di modificare l'insegnamento fino a quando l'apposito button non viene premuto di nuovo
        message_text, inline_keyboard = get_esami_text_inline_keyboard(context)
        context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text, reply_markup=inline_keyboard)

def esami(update: Update, context: CallbackContext):
    check_log(update, context, "esami")

    if 'esami' in context.user_data:
        context.user_data['esami'].clear() #ripulisce il dict dell'user relativo al comando /esami da eventuali dati presenti
    else:
        context.user_data['esami'] = {} #crea il dict che conterrà i dati del comando /esami all'interno della key ['esami'] di user data

    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    if chat_id != user_id: # forza ad eseguire il comando in una chat privata, anche per evitare di inondare un gruppo con i risultati
        context.bot.sendMessage(chat_id=chat_id, text="Questo comando è utilizzabile solo in privato")
        context.bot.sendMessage(chat_id=user_id, text="Dal comando esami che hai eseguito in un gruppo")
    
    message_text, inline_keyboard = get_esami_text_inline_keyboard(context)
    context.bot.sendMessage(chat_id=user_id, text=message_text, reply_markup=inline_keyboard)

def get_esami_text_inline_keyboard(context: CallbackContext) -> (str, InlineKeyboardMarkup): # restituisce una tuple formata da (message_text, InlineKeyboardMarkup)
    esami_user_data = context.user_data['esami']

    text_anno     = ", ".join([key for key in esami_user_data if "anno" in key])                             # stringa contenente gli anni per cui la flag è true
    text_sessione = ", ".join([key for key in esami_user_data if "sessione" in key]).replace("sessione", "") # stringa contenente le sessioni per cui la flag è true
    text_insegnamento = esami_user_data.get("insegnamento", "")                                              # stringa contenente l'insegnamento

    message_text = "Anno: {}\nSessione: {}\nInsegnamento: {}"\
        .format(text_anno if text_anno else "tutti",\
                text_sessione if text_sessione else "tutti",\
                text_insegnamento if text_insegnamento else "tutti")

    keyboard = [[]]
    keyboard.append([InlineKeyboardButton(" ~ Personalizza la ricerca ~ ", callback_data="_div")])
    keyboard.append([
        InlineKeyboardButton(" Anno ", callback_data="sm_esami_button_anno"),
        InlineKeyboardButton(" Sessione ", callback_data="sm_esami_button_sessione"),
    ])
    keyboard.append([
        InlineKeyboardButton(" Insegnamento ", callback_data="sm_esami_button_insegnamento"),
        InlineKeyboardButton(" Cerca ", callback_data="esami_button_search")
    ])

    return message_text, InlineKeyboardMarkup(keyboard)

def esami_output(item):

	output = "*Insegnamento:* " + item["insegnamento"]
	output += "\n*Docenti:* " + item["docenti"]

	for session in ("prima", "seconda", "terza", "straordinaria"):
		if session in item.keys():
			appeals = item[session]
			appeals = str(appeals)			
			appeals = re.sub(r"(?P<ora>([01]?\d|2[0-3]):[0-5][0-9])(?P<parola>\w)", r"\g<ora> - \g<parola>", appeals) #aggiunge un - per separare orario e luogo dell'esame
			appeals = appeals.split("', '") # separa i vari appelli della sessione

			for i, appeal in enumerate(appeals):
				appeals[i] = re.sub(r"[\['\]]", "", appeal) # rimuove eventuali caratteri [ ' ] rimasti in ogni appello
				appeals[i] = re.sub(r"(?P<link>https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*))", r"[link](\g<link>)", appeals[i]) # cattura eventuali link e li rende inoffensivi per il markdown
				appeals[i] = re.sub(r"_(?![^(]*[)])", " ", appeals[i]) # rimuove eventuali caratteri _ rimasti che non siano nei link

			if "".join(appeals) != "":
				output += "\n*" + session.title() + ":*\n" + "\n".join(appeals)

	output += "\n*CDL:* " + item["cdl"]
	output += "\n*Anno:* " + item["anno"] + "\n"

	return output

def esami_cmd(user_dict):
	output_str = []
 	
	select_sessione = ", ".join([key for key in user_dict if "sessione" in key]).replace("sessione", "") #stringa contenente le sessioni per cui il dict contiene la key, separate da ", " 	
	where_sessione = " = '[]' or not ".join([key for key in user_dict if "sessione" in key]).replace("sessione", "") #stringa contenente le sessioni per cui il dict contiene la key, separate da " = '[]' and not " 
	where_anno = "' or anno = '".join([key for key in user_dict if "anno" in key]) #stringa contenente gli anni per cui il dict contiene la key, separate da "' or anno = '"	
	where_insegnamento = user_dict.get("insegnamento", "")  #stringa contenente l'insegnamento, se presente

	if not select_sessione:
		select_sessione = "prima, seconda, terza, straordinaria"

	if where_sessione:
		where_sessione = f"and (not {where_sessione} = '[]')"
	else:
		where_sessione = ""

	if where_anno:
		where_anno = f"and (anno = '{where_anno}')"
	else:
		where_anno = ""

	query = f"""SELECT anno, cdl, docenti, insegnamento, {select_sessione} 
				FROM exams
				WHERE insegnamento LIKE ? {where_sessione} {where_anno}"""

	conn = sqlite3.connect('data/DMI_DB.db')
	conn.row_factory = dict_factory
	cur = conn.cursor()
	try:
		cur.execute(query, ('%'+ where_insegnamento+'%',))
	except Exception as e:
		print("The following exams query could not be executed (command \\esami)")
		print(query) #per controllare cosa è andato storto
		print("[error]: " + str(e))

	for item in cur.fetchall():
		output_str.append(esami_output(item))

	return check_output(output_str)

def check_output(output) -> str:
	if len(output):
		output_str = '\n'.join(output)
		output_str += "\nRisultati trovati: " + str(len(output))
	else:
		output_str = "Nessun risultato trovato :(\n"

	return output_str

def dict_factory(cursor, row) -> dict:
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d