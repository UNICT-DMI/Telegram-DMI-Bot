
# Telegram
import telegram
from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

# Drive
from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth

# Modules
from module.shared import read_md, check_log, config_map, TOKEN, CUSicon

# Needed to correctly run functions using globals()
from module.esami import esami_button_anno, esami_button_insegnamento, esami_button_sessione
from module.lezioni import lezioni_button_anno, lezioni_button_giorno, lezioni_button_insegnamento
from module.help import rapp_menu, exit_cmd
from module.aulario import aulario, aulario_subj
# System libraries
import sqlite3
import os
import sys
from datetime import datetime
import json
import random


# TODO: refactor this function (properly)
def callback(update: Update, context: CallbackContext):
    conn = sqlite3.connect('data/DMI_DB.db')
    keyboard2 = [[]]
    icona = ""
    number_row = 0
    number_array = 0

    update.callback_query.data = update.callback_query.data.replace("Drive_", "")

    if len(update.callback_query.data) < 13: # "Accetta" (/request command)

        array_value = update['callback_query']['message']['text'].split(" ")

        try:
            if len(array_value) == 5:
                conn.execute("INSERT INTO 'Chat_id_List' VALUES ("+update.callback_query.data+",'" + array_value[4] + "','" + array_value[1] + "','" + array_value[2] + "','" + array_value[3] + "') ")
                context.bot.sendMessage(chat_id=update.callback_query.data, text="🔓 La tua richiesta è stata accettata. Leggi il file README")
                context.bot.sendDocument(chat_id=update.callback_query.data, document=open('data/README.pdf', 'rb'))

                request_elimination_text = "Richiesta di " + str(array_value[1]) + " " + str(array_value[2]) + " estinta"
                context.bot.editMessageText(text=request_elimination_text, chat_id=config_map['dev_group_chatid'], message_id=update.callback_query.message.message_id)

                context.bot.sendMessage(chat_id=config_map['dev_group_chatid'], text=str(array_value[1]) + " " + str(array_value[2] + str(" è stato inserito nel database")))
            elif len(array_value) == 4:
                conn.execute("INSERT INTO 'Chat_id_List'('Chat_id','Nome','Cognome','Email') VALUES (" + update.callback_query.data + ",'" + array_value[1] + "','" + array_value[2] + "','" + array_value[3] + "')")
                context.bot.sendMessage(chat_id=update.callback_query.data, text="🔓 La tua richiesta è stata accettata. Leggi il file README")
                context.bot.sendDocument(chat_id=update.callback_query.data, document=open('data/README.pdf', 'rb'))

                request_elimination_text = "Richiesta di " + str(array_value[1]) + " " + str(array_value[2]) + " estinta"
                context.bot.editMessageText(text=request_elimination_text, chat_id=config_map['dev_group_chatid'], message_id=update.callback_query.message.message_id)
            else:
                context.bot.sendMessage(chat_id=config_map['dev_group_chatid'], text=str("ERRORE INSERIMENTO: ") + str(update['callback_query']['message']['text']) + " " + str(update['callback_query']['data']))
            conn.commit()
        except Exception as error:
            print(error)
            context.bot.sendMessage(chat_id=config_map['dev_group_chatid'], text=str("ERRORE INSERIMENTO: ") + str(update['callback_query']['message']['text']) + " " + str(update['callback_query']['data']))
    else:
        pid = os.fork()
        if (pid == 0):
            settings_file = "config/settings.yaml"
            gauth2 = GoogleAuth(settings_file=settings_file)
            gauth2.CommandLineAuth()
            # gauth2.LocalWebserverAuth()
            drive2 = GoogleDrive(gauth2)
            bot2 = telegram.Bot(TOKEN)

            file1 = drive2.CreateFile({'id': update.callback_query.data})
            file1.FetchMetadata()
            if file1['mimeType'] == "application/vnd.google-apps.folder":
                file_list2 = None

                try:
                    istance_file = drive2.ListFile({'q': "'"+file1['id']+"' in parents and trashed=false", 'orderBy': 'folder,title'})
                    file_list2 = istance_file.GetList()
                    with open("./logs/debugDrive.txt", "a") as debugfile:
                        debugfile.write("- Log time:\n {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        debugfile.write("- File:\n {}".format(str(json.dumps(file1))))
                        debugfile.write("- IstanceFile:\n {}".format(str(json.dumps(istance_file))))
                        debugfile.write("- FileList:\n {}".format(str(json.dumps(file_list2))))
                        debugfile.write("\n------------\n")
                except Exception as e:
                    with open("./logs/debugDrive.txt", "a") as debugfile:
                        debugfile.write("- Log time:\n {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        debugfile.write("- Error:\n {}".format(e))
                        debugfile.write("\n------------\n")
                    print("- Drive error: {}".format(e))
                    bot2.sendMessage(chat_id=update['callback_query']['from_user']['id'], text="Si è verificato un errore, ci scusiamo per il disagio. Contatta i devs. /help")
                    sys.exit(0)

                formats = {
                	** { "pdf" : "📕 " },
                	** dict.fromkeys([' a', 'b', 'c'], 10),
                	** dict.fromkeys(["doc", "docx", "txt"], "📘 "),
                	** dict.fromkeys(["jpg", "png", "gif"], "📷 "),
                	** dict.fromkeys(["rar", "zip"], "🗄 "),
                	** dict.fromkeys(["out", "exe"], "⚙ "),
                	** dict.fromkeys(["c", "cpp", "h", "py", "java", "js", "html", "php"], "💻 ")
                }

                for file2 in file_list2:
                    file2.FetchMetadata()
                    if file2['mimeType'] == "application/vnd.google-apps.folder":
                        if number_row >= 1:
                            keyboard2.append([InlineKeyboardButton("🗂 "+file2['title'], callback_data="Drive_" + file2['id'])])
                            number_row = 0
                            number_array += 1
                        else:
                            keyboard2[number_array].append(InlineKeyboardButton("🗂 "+file2['title'], callback_data="Drive_" + file2['id']))
                            number_row += 1
                    else:
                        file_format = file2['title'][-5:] # get last 5 characters of strings
                        file_format = file_format.split(".") # split file_format per "."
                        file_format = file_format[len(file_format)-1] # get last element of file_format

                        icona = "📄 "

                        if file_format in formats.keys():
                            icona = formats[file_format]

                        if number_row >= 1:
                            keyboard2.append([InlineKeyboardButton(icona+file2['title'], callback_data="Drive_" + file2['id'])])
                            number_row = 0
                            number_array += 1
                        else:
                            keyboard2[number_array].append(InlineKeyboardButton(icona+file2['title'], callback_data="Drive_" + file2['id']))
                            number_row += 1

                if len(file1['parents']) > 0 and file1['parents'][0]['id'] != '0ADXK_Yx5406vUk9PVA':
                    keyboard2.append([InlineKeyboardButton("🔙", callback_data="Drive_" + file1['parents'][0]['id'])])

                reply_markup3 = InlineKeyboardMarkup(keyboard2)
                bot2.sendMessage(chat_id=update['callback_query']['from_user']['id'], text=file1['title']+":", reply_markup=reply_markup3)

            elif file1['mimeType'] == "application/vnd.google-apps.document":
                bot2.sendMessage(chat_id=update['callback_query']['from_user']['id'], text="Impossibile scaricare questo file poichè esso è un google document, Andare sul seguente link")
                bot2.sendMessage(chat_id=update['callback_query']['from_user']['id'], text=file1['exportLinks']['application/pdf'])

            else:
                try:
                    file_d = drive2.CreateFile({'id': file1['id']})
                    file_d.FetchMetadata()
                    if int(file_d['fileSize']) < 5e+7:
                        file_d.GetContentFile('file/'+file1['title'])
                        file_s = file1['title']
                        filex = open(str("file/" + file_s), "rb")
                        bot2.sendChatAction(chat_id=update['callback_query']['from_user']['id'], action="UPLOAD_DOCUMENT")
                        bot2.sendDocument(chat_id=update['callback_query']['from_user']['id'], document=filex)
                        os.remove(str("file/" + file_s))
                    else:
                        bot2.sendMessage(chat_id=update['callback_query']['from_user']['id'], text="File troppo grande per il download diretto, scarica dal seguente link")
                        # file_d['downloadUrl']
                        bot2.sendMessage(chat_id=update['callback_query']['from_user']['id'], text=file_d['alternateLink'])
                except Exception as e:
                    print("- Drive error: {}".format(e))
                    bot2.sendMessage(chat_id=update['callback_query']['from_user']['id'], text="Impossibile scaricare questo file, contattare gli sviluppatori del bot")
                    open("logs/errors.txt", "a+").write(str(e) + str(file_d['title'])+"\n")

            sys.exit(0)

        os.waitpid(pid, 0)
    conn.close()

def submenu_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    func_name = data[3:len(data)]
    globals()[func_name](
      query,
      context,
      query.message.chat_id,
      query.message.message_id
    )

def generic_button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    message_text = globals()[data]()
    context.bot.editMessageText(
      text=message_text,
      chat_id=query.message.chat_id,
      message_id=query.message.message_id
    )

def md_handler(update: Update, context: CallbackContext):
    query = update.callback_query

    data = query.data.replace("md_", "")
    message_text = read_md(data)

    if data == "help":
        message_text = message_text.replace("<cusicon>", CUSicon[random.randint(0, 5)])

    check_log(update, context, data, 1)

    context.bot.editMessageText(
      text=message_text,
      chat_id=query.message.chat_id,
      message_id=query.message.message_id,
      parse_mode=ParseMode.MARKDOWN
    )

def informative_callback(update: Update, context: CallbackContext):
     # controllo per poter gestire i comandi (/comando) e i messaggi inviati premendo i bottoni (❔ Help)
    if update.message.text[0] == '/':
        cmd = update.message.text.split(' ')[0][1:] #prende solo la prima parola del messaggio (cioè il comando) escludendo lo slash
    else:
        cmd = update.message.text.split(' ')[1].lower() # prende la prima parola dopo l'emoji
    check_log(update, context, cmd)
    message_text = read_md(cmd)
    context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text, parse_mode='Markdown')

def submenu_with_args_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    func_name = data.split('&')[1]
    arg = data.split('&')[2]

    globals()[func_name](
      query,
      context,
      query.message.chat_id,
      query.message.message_id,
      arg
    )


def none_handler(update: Update, context: CallbackContext):
    update.callback_query.answer()
