# Telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

# Drive
from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth

# Modules
from module.shared import check_log

# System libraries
import sqlite3

def drive(update: Update, context: CallbackContext):
    check_log(update, context, "drive")
    conn = sqlite3.connect('data/DMI_DB.db')

    settings_file = "config/settings.yaml"
    gauth = GoogleAuth(settings_file=settings_file)
    gauth.CommandLineAuth()
    # gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    chat_id = update.message.chat_id
    id_drive = '0B7-Gi4nb88hremEzWnh3QmN3ZlU'
    
    if chat_id < 0:
        context.bot.sendMessage(chat_id=chat_id, text="La funzione /drive non è ammessa nei gruppi")
    else:
        if conn.execute("SELECT Chat_id FROM 'Chat_id_List' WHERE Chat_id = " + str(chat_id)).fetchone():
            keyboard2 = [[]]

            try:
                file_list = drive.ListFile({'q': "'" + id_drive + "' in parents and trashed=false", 'orderBy': 'folder,title'}).GetList()
            except Exception as error:
                print (str(error))

            number_row = 0
            number_array = 0

            for file1 in file_list:
                if file1['mimeType'] == "application/vnd.google-apps.folder":
                    if number_row >= 3:
                        keyboard2.append([InlineKeyboardButton("🗂 "+file1['title'], callback_data="Drive_" + file1['id'])])
                        number_row = 0
                        number_array += 1
                    else:
                        keyboard2[number_array].append(InlineKeyboardButton("🗂 "+file1['title'], callback_data="Drive_" + file1['id']))
                        number_row += 1
                else:
                    if number_row >= 3:
                        keyboard2.append([InlineKeyboardButton("📃 "+file1['title'], callback_data="Drive_" + file1['id'])])
                        number_row = 0
                        number_array += 1
                    else:
                        keyboard2[number_array].append(InlineKeyboardButton("📃 "+file1['title'], callback_data="Drive_" + file1['id']))
                        number_row += 1

            reply_markup3 = InlineKeyboardMarkup(keyboard2)
            context.bot.sendMessage(chat_id=chat_id, text="DMI UNICT - Appunti & Risorse:", reply_markup=reply_markup3)
        else:
            context.bot.sendMessage(chat_id=chat_id, text="🔒 Non hai i permessi per utilizzare la funzione /drive,\n Utilizzare il comando /request <nome> <cognome> <e-mail> (il nome e il cognome devono essere scritti uniti Es: Di mauro -> Dimauro) ")
    conn.close()
