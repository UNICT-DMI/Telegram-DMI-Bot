# Telegram
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

# Modules
from module.shared import config_map

# System libraries
import sqlite3
import re

def request(update: Update, context: CallbackContext):
    conn = sqlite3.connect('data/DMI_DB.db')
    chat_id = update.message.chat_id

    if chat_id > 0:
        # if we do not find any chat_id in the db
        if not conn.execute("SELECT Chat_id FROM Chat_id_List WHERE Chat_id = " + str(chat_id)).fetchone():
            message_text = "✉️ Richiesta inviata"
            keyboard = [[]]

            username = ""
            if update['message']['from_user']['username']:
                username = update['message']['from_user']['username']

            update.message.text = re.sub('<|>', '', update.message.text)

            if len(update.message.text.split(" ")) == 4 and "@" in update.message.text.split(" ")[3] and "." in update.message.text.split()[3]:
                text_send = str(update.message.text) + " " + username
                keyboard.append([InlineKeyboardButton("Accetta", callback_data="Drive_"+str(chat_id))])
                reply_markup2 = InlineKeyboardMarkup(keyboard)
                context.bot.sendMessage(chat_id=config_map['dev_group_chatid'], text=text_send, reply_markup=reply_markup2)
            else:
                message_text = "Errore compilazione /request:\n Forma esatta: /request <nome> <cognome> <e-mail> (il nome e il cognome devono essere scritti uniti Es: Di mauro -> Dimauro)"
        else:
            message_text = "Hai già effettuato la richiesta di accesso"
    else:
        message_text = "Non è possibile utilizzare /request in un gruppo"

    context.bot.sendMessage(chat_id=chat_id, text=message_text)
    conn.close()

def add_db(update: Update, context: CallbackContext):
    conn = sqlite3.connect('data/DMI_DB.db')
    chat_id = update.message.chat_id

    if (config_map['dev_group_chatid'] != 0 and chat_id == config_map['dev_group_chatid']):
        # /add nome cognome e-mail username chatid
        array_value = update.message.text.split(" ")
        if len(array_value) == 6:
            conn.execute("INSERT INTO 'Chat_id_List' VALUES (" + array_value[5] + ",'" + array_value[4] + "','" + array_value[1] + "','" + array_value[2] + "','" + array_value[3] + "') ")
            context.bot.sendMessage(chat_id=array_value[5], text="🔓 La tua richiesta è stata accettata. Leggi il file README")
            context.bot.sendDocument(chat_id=array_value[5], document=open('data/README.pdf', 'rb'))
            conn.commit()
        elif len(array_value) == 5:
            conn.execute("INSERT INTO 'Chat_id_List'('Chat_id','Nome','Cognome','Email') VALUES (" + array_value[4] + ",'" + array_value[1] + "','" + array_value[2] + "','" + array_value[3] + "')")
            context.bot.sendMessage(chat_id=int(array_value[4]), text="🔓 La tua richiesta è stata accettata. Leggi il file README")
            context.bot.sendDocument(chat_id=int(array_value[4]), document=open('data/README.pdf', 'rb'))
            conn.commit()
        else:
            context.bot.sendMessage(chat_id=chat_id, text="/adddb <nome> <cognome> <e-mail> <username> <chat_id>")
    conn.close()