# -*- coding: utf-8 -*-

# Telegram
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, Filters, MessageHandler, CommandHandler, CallbackQueryHandler, RegexHandler
from telegram.error import (TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError)

# Drive
from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth

# Custom classes
from classes.EasterEgg import EasterEgg
from classes.StringParser import StringParser

# System libraries
from datetime import date, datetime, timedelta
import json
import datetime
import re
import random
import os
import sys
import requests
import sqlite3
import yaml
import logging
from urllib.request import urlopen
from bs4 import BeautifulSoup

from module.lezioni import lezioni_cmd
from module.esami import esami_cmd
from module.professori import prof_cmd
from module.scraper_exams import scrape_exams
from module.scraper_lessons import scrape_lessons
from module.scraper_professors import scrape_prof
from module.scraper_notices import scrape_notices
from module.mensa import *
from module.gitlab import gitlab_handler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# config
with open('config/settings.yaml', 'r') as yaml_config:
    config_map = yaml.load(yaml_config)

# Token of your telegram bot that you created from @BotFather, write it on settings.yml
TOKEN = config_map["token"]
news = ""

def send_message(bot, update, messaggio):
    msg = ""
    righe = messaggio.split('\n')
    for riga in righe:
        if riga.strip() == "" and len(msg) > 3000:
            bot.sendMessage(chat_id=update.message.chat_id, text=msg, parse_mode='Markdown')
            msg = ""
        else:
            msg += riga + "\n"
    bot.sendMessage(chat_id=update.message.chat_id, text=msg, parse_mode='Markdown')


def lezioni(bot, update, args, *m):
    check_log(bot, update, "lezioni")
    message_text = lezioni_cmd(bot, update, args)
    bot.sendMessage(chat_id=update.message.chat_id, text=message_text, parse_mode='Markdown')


def esami(bot, update, args):
    check_log(bot, update, "esami")
    message_text = esami_cmd(args)
    if len(message_text) > 4096:
        send_message(bot, update, message_text)
    else:
        bot.sendMessage(chat_id=update.message.chat_id, text=message_text, parse_mode='Markdown')


def forum(sezione):
    response = urlopen("http://forum.informatica.unict.it/")
    html_doc = response.read()
    s = BeautifulSoup(html_doc, 'html.parser')
    s.prettify()
    dictionary = {}
    for range_limit, main_table in enumerate(s.findAll("div", class_="tborder")):
        if(range_limit >= 3):  # If che limita le sezioni a quelle interessate, evitando di stampare sottosezioni come "News" della categoria "Software"
            break
        for td_of_table in main_table.findAll("td", class_="windowbg3"):
            for span_under in td_of_table.findAll("span", class_="smalltext"):
                for anchor_tags in span_under.find_all('a'):
                    anchor_tags_splitted = anchor_tags.string.split(",")
                    anchor_tags_without_cfu = StringParser.remove_cfu(anchor_tags_splitted[0])

                    if(sezione == anchor_tags_without_cfu.lower()):
                        dictionary[anchor_tags_without_cfu.lower()] = anchor_tags['href']
                        return dictionary

    return False  # Redefine with @Veeenz API


# Commands
CUSicon = {0: "🏋",
           1: "⚽️",
           2: "🏀",
           3: "🏈",
           4: "🏐",
           5: "🏊",
           }


def help_cmd():
    output = "@DMI_Bot risponde ai seguenti comandi: \n\n"
    output += "📖 /esami - linka il calendario degli esami\n"
    output += "🗓 /aulario - linka l\'aulario\n"
    output += "👔 /prof <nome> - es. /prof Barbanera\n"
    output += "🍽 /mensa - orario mensa\n"
    output += "👥 /rappresentanti - elenco dei rappresentanti del DMI\n"
    output += "📚 /biblioteca - orario biblioteca DMI\n"
    output += CUSicon[random.randint(0, 5)] + " /cus sede e contatti\n\n"
    output += "Segreteria orari e contatti:\n"
    output += "/sdidattica - segreteria didattica\n"
    output += "/sstudenti - segreteria studenti\n"
    output += "/cea - CEA\n"
    output += "\nERSU orari e contatti\n"
    output += "/ersu - sede centrale\n"
    output += "/ufficioersu - (ufficio tesserini)\n"
    output += "/urp - URP studenti\n\n"
    output += "~Bot~\n"
    output += "📂 /drive - accedi a drive\n"
    output += "📂 /git - /gitlab - accedi a gitlab\n"
    output += "/disablenews \n"
    output += "/enablenews\n"
    output += "/contributors"
    return output


def read_md(namefile):
    in_file = open("data/markdown/" + namefile + ".md", "r")
    text = in_file.read()
    in_file.close()
    return text


def informative_callback(bot, update, cmd):
    check_log(bot, update, cmd)
    message_text = read_md(cmd)
    bot.sendMessage(chat_id=update.message.chat_id, text=message_text, parse_mode='Markdown')


def exit_cmd():
    output = "."
    return output


def esami_button():
    output = "Scrivi /esami inserendo almeno uno dei seguenti parametri: giorno, materia, sessione (prima, seconda, terza, straordinaria)"
    return output


def lezioni_button():
    output = "Scrivi /lezioni inserendo almeno uno dei seguenti parametri: giorno, materia"
    return output


def mesami_url():
    url = "http://web.dmi.unict.it/Didattica/Laurea%20Magistrale%20in%20Informatica%20LM-18/Calendario%20degli%20Esami"
    return url


def aulario_url():
    url = 'http://aule.dmi.unict.it/aulario/roschedule.php'
    return url

# Easter egg
def prof_sticker_id():
    db = sqlite3.connect('data/DMI_DB.db')
    i = db.execute("SELECT * FROM 'stickers' ORDER BY RANDOM() LIMIT 1").fetchone()[0]

    db.close()

    return i


def forum_cmd(text):
    text = text.replace("/forum ", "")
    dict_url_sezioni = forum(text)
    if not (dict_url_sezioni == False):
        for titoli in dict_url_sezioni:
            output = StringParser.starts_with_upper(titoli) + ": " + str(dict_url_sezioni[titoli])
    else:
        output = "La sezione non e' stata trovata."
    return output


def callback(bot, update):
    conn = sqlite3.connect('data/DMI_DB.db')
    keyboard2 = [[]]
    icona = ""
    number_row = 0
    number_array = 0

    update.callback_query.data = update.callback_query.data.replace("Drive_", "")
    # print('Callback query data: ' + str(update.callback_query.data))
    if len(update.callback_query.data) < 13:
        #conn.execute("DELETE FROM 'Chat_id_List'")
        array_value = update['callback_query']['message']['text'].split(" ")
        try:
            if len(array_value) == 4:
                array_value.insert(0, "None")

            if len(array_value) == 5:
                conn.execute("INSERT INTO 'Chat_id_List' VALUES ("+update.callback_query.data+",'" + array_value[4] + "','" + array_value[1] + "','" + array_value[2] + "','" + array_value[3] + "') ")
                bot.sendMessage(chat_id=update.callback_query.data, text="🔓 La tua richiesta è stata accettata. Leggi il file README")
                bot.sendDocument(chat_id=update.callback_query.data, document=open('data/README.pdf', 'rb'))

                request_elimination_text = "Richiesta di " + str(array_value[1]) + " " + str(array_value[2]) + " estinta"
                bot.editMessageText(text=request_elimination_text, chat_id=config_map['dev_group_chatid'], message_id=update.callback_query.message.message_id)

                bot.sendMessage(chat_id=config_map['dev_group_chatid'], text=str(array_value[1]) + " " + str(array_value[2] + str(" è stato inserito nel database")))

            elif len(array_value) == 4:
                conn.execute("INSERT INTO 'Chat_id_List'('Chat_id','Nome','Cognome','Email') VALUES (" + update.callback_query.data + ",'" + array_value[1] + "','" + array_value[2] + "','" + array_value[3] + "')")
                bot.sendMessage(chat_id=update.callback_query.data, text="🔓 La tua richiesta è stata accettata. Leggi il file README")
                bot.sendDocument(chat_id=update.callback_query.data, document=open('data/README.pdf', 'rb'))

            else:
                bot.sendMessage(chat_id=config_map['dev_group_chatid'], text=str("ERRORE INSERIMENTO: ") + str(update['callback_query']['message']['text']) + " " + str(update['callback_query']['data']))
            conn.commit()
        except Exception as error:
            print(error)
            bot.sendMessage(chat_id=config_map['dev_group_chatid'], text=str("ERRORE INSERIMENTO: ") + str(update['callback_query']['message']['text']) + " " + str(update['callback_query']['data']))

        text = ""

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
            if file1['mimeType'] == "application/vnd.google-apps.folder":
                file_list2 = None

                try:
                    istance_file = drive2.ListFile({'q': "'"+file1['id']+"' in parents and trashed=false", 'orderBy': 'folder,title'})
                    file_list2 = istance_file.GetList()
                    with open("./logs/debugDrive.txt", "a") as debugfile:
                        debugfile.write("- Log time:\n {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        debugfile.write("- File:\n {}".format(str(json.dumps(file1))))
                        debugfile.write("- IstanceFile:\n {}".format(str(json.dumps(istance_file))))
                        debugfile.write("- FileList:\n {}".format(str(json.dumps(file_list2))))
                        debugfile.write("\n------------\n")
                except Exception as e:
                    with open("./logs/debugDrive.txt", "a") as debugfile:
                        debugfile.write("- Log time:\n {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
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



def request(bot, update):
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
                bot.sendMessage(chat_id=config_map['dev_group_chatid'], text=text_send, reply_markup=reply_markup2)
            else:
                message_text = "Errore compilazione /request:\n Forma esatta: /request <nome> <cognome> <e-mail> (il nome e il cognome devono essere scritti uniti Es: Di mauro -> Dimauro)"
        else:
            message_text = "Hai già effettuato la richiesta di accesso"
    else:
        message_text = "Non è possibile utilizzare /request in un gruppo"

    bot.sendMessage(chat_id=chat_id, text=message_text)
    conn.close()


def add_db(bot, update):
    conn = sqlite3.connect('data/DMI_DB.db')
    chat_id = update.message.chat_id

    if (config_map['dev_group_chatid'] != 0 and chat_id == config_map['dev_group_chatid']):
        # /add nome cognome e-mail username chatid
        array_value = update.message.text.split(" ")
        if len(array_value) == 6:
            conn.execute("INSERT INTO 'Chat_id_List' VALUES (" + array_value[5] + ",'" + array_value[4] + "','" + array_value[1] + "','" + array_value[2] + "','" + array_value[3] + "') ")
            bot.sendMessage(chat_id=array_value[5], text="🔓 La tua richiesta è stata accettata. Leggi il file README")
            bot.sendDocument(chat_id=array_value[5], document=open('data/README.pdf', 'rb'))
            conn.commit()
        elif len(array_value) == 5:
            conn.execute("INSERT INTO 'Chat_id_List'('Chat_id','Nome','Cognome','Email') VALUES (" + array_value[4] + ",'" + array_value[1] + "','" + array_value[2] + "','" + array_value[3] + "')")
            bot.sendMessage(chat_id=int(array_value[4]), text="🔓 La tua richiesta è stata accettata. Leggi il file README")
            bot.sendDocument(chat_id=int(array_value[4]), document=open('data/README.pdf', 'rb'))
            conn.commit()
        else:
            bot.sendMessage(chat_id=chat_id, text="/adddb <nome> <cognome> <e-mail> <username> <chat_id>")
    conn.close()


def drive(bot, update):
    check_log(bot, update, "drive")
    conn = sqlite3.connect('data/DMI_DB.db')

    settings_file = "config/settings.yaml"
    gauth = GoogleAuth(settings_file=settings_file)
    gauth.CommandLineAuth()
    # gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    chat_id = update.message.chat_id
    id_drive = '0B7-Gi4nb88hremEzWnh3QmN3ZlU'
    if chat_id < 0:
        bot.sendMessage(chat_id=chat_id, text="La funzione /drive non è ammessa nei gruppi")
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
            bot.sendMessage(chat_id=chat_id, text="DMI UNICT - Appunti & Risorse:", reply_markup=reply_markup3)
        else:
            bot.sendMessage(chat_id=chat_id, text="🔒 Non hai i permessi per utilizzare la funzione /drive,\n Utilizzare il comando /request <nome> <cognome> <e-mail> (il nome e il cognome devono essere scritti uniti Es: Di mauro -> Dimauro) ")
    conn.close()


# CallbackQueryHandler
def button_handler(bot, update):
    query = update.callback_query
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    data = query.data

    # Submenu
    if data.startswith("sm_"):
        func_name = data[3:len(data)]
        globals()[func_name](bot, chat_id, message_id)

    elif data == "esami_button" or data == "lezioni_button" or data == "help_cmd" or data == "exit_cmd":
        message_text = globals()[data]()
        bot.editMessageText(
            text=message_text, chat_id=chat_id, message_id=message_id)

    elif data.startswith("Drive_"):
        callback(bot, update)

    elif data.startswith('git_'):
        gitlab_handler(bot, update, data.replace('git_', ''))

    elif (data == "mensa_help"):
        mensa_cmd(bot, update.callback_query)

    elif data.startswith("mensa_weekend"):
        mensa_weekend(bot, update)

    elif data.startswith("mensa_"):
        mensa_subscription(bot, update)

    elif data == "enablenews" or data == "disablenews":
        globals()[data](bot, query)

    # Simple text
    elif data != "_div":
        message_text = read_md(data)
        check_log(bot, update, data, 1)
        bot.editMessageText(
            text=message_text, chat_id=chat_id, message_id=message_id)


def help(bot, update):
    check_log(bot, update, "help")
    chat_id = update.message.chat_id
    keyboard = [[]]
    message_text = "@DMI_Bot risponde ai seguenti comandi:"

    keyboard.append([InlineKeyboardButton(" ~ Dipartimento e CdL ~ ", callback_data="_div")])

    keyboard.append(
        [
            InlineKeyboardButton("📖 Esami (Triennale)",    callback_data="esami_button"),
            InlineKeyboardButton("📖 Esami (Magistrale)",   url=mesami_url()),
            InlineKeyboardButton("🗓 Aulario",              url=aulario_url()),
            InlineKeyboardButton("Lezioni",                 callback_data="lezioni_button")
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton("🍽 Mensa",                                callback_data="mensa_help"),
            InlineKeyboardButton("👥 Rappresentanti",                       callback_data="sm_rapp_menu"),
            InlineKeyboardButton("📚 Biblioteca",                           callback_data="biblioteca"),
            InlineKeyboardButton(CUSicon[random.randint(0, 5)] + " CUS",    callback_data="cus")
        ]
    )

    keyboard.append([InlineKeyboardButton(" ~ Segreteria orari e contatti ~ ", callback_data="_div")])

    keyboard.append(
        [
            InlineKeyboardButton("Seg. Didattica",  callback_data="sdidattica"),
            InlineKeyboardButton("Seg. Studenti",   callback_data="sstudenti"),
            InlineKeyboardButton("CEA",             callback_data="cea")
        ]
    )

    keyboard.append([InlineKeyboardButton(" ~ ERSU orari e contatti ~ ", callback_data="_div")])

    keyboard.append(
        [
            InlineKeyboardButton("ERSU",          callback_data="ersu"),
            InlineKeyboardButton("Ufficio ERSU",  callback_data="ufficioersu"),
            InlineKeyboardButton("URP",           callback_data="urp")
        ]
    )

    keyboard.append([InlineKeyboardButton(" ~ Bot e varie ~ ", callback_data="_div")])

    keyboard.append(
        [
            InlineKeyboardButton("Iscriviti alle news",     callback_data="enablenews"),
            InlineKeyboardButton("Disiscriviti dalle news", callback_data="disablenews")
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton("📂 Drive",     callback_data="drive"),
            InlineKeyboardButton("📂 GitLab",     callback_data="gitlab"),
            InlineKeyboardButton("Contributors", callback_data="contributors"),
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton("Tutti i comandi", callback_data="help_cmd"),
            InlineKeyboardButton("Chiudi",          callback_data="exit_cmd")
        ]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.sendMessage(chat_id=chat_id, text=message_text, reply_markup=reply_markup)


def rapp_menu(bot, chat_id, message_id):
    keyboard = [[]]
    message_text = "Quali rappresentanti vuoi contattare?"

    keyboard.append(
        [
            InlineKeyboardButton("Rapp. DMI",         callback_data="rappresentanti_dmi"),
            InlineKeyboardButton("Rapp. Informatica", callback_data="rappresentanti_informatica"),
            InlineKeyboardButton("Rapp. Matematica",  callback_data="rappresentanti_matematica"),
        ]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)


def smonta_portoni(bot, update):
    check_log(bot, update, "smonta_portoni")
    message_text = EasterEgg.get_smonta_portoni()
    bot.sendMessage(chat_id=update.message.chat_id, text=message_text)


def santino(bot, update):
    chat_id = update.message.chat_id
    if (chat_id == -1001031103640 or chat_id == config_map['dev_group_chatid']):
        check_log(bot, update, "santino")
        message_text = EasterEgg.get_santino()
        bot.sendMessage(chat_id=update.message.chat_id, text=message_text)


def bladrim(bot, update):
    check_log(bot, update, "bladrim")
    message_text = EasterEgg.get_bladrim()
    bot.sendMessage(chat_id=update.message.chat_id, text=message_text)


def prof_sticker(bot, update):
    check_log(bot, update, "prof_sticker")
    bot.sendSticker(chat_id=update.message.chat_id, sticker=prof_sticker_id())


def lei_che_ne_pensa_signorina(bot, update):
    check_log(bot, update, "leiCheNePensaSignorina")
    message_text = EasterEgg.get_lei_che_ne_pensa_signorina()
    bot.sendMessage(chat_id=update.message.chat_id, text=message_text)


def prof(bot, update, args):
    check_log(bot, update, "prof")
    message_text = prof_cmd(args)
    if len(message_text) > 4096:
        send_message(bot, update, message_text)
    else:
        bot.sendMessage(chat_id=update.message.chat_id, text=message_text, parse_mode='Markdown')


def forum_bot(bot, update):
    check_log(bot, update, "forum_bot")
    message_text = forum_cmd(update.message.text)
    bot.sendMessage(chat_id=update.message.chat_id, text=message_text)


def get_short_link(url):
    post_url = 'https://www.googleapis.com/urlshortener/v1/url?key={}'.format(config_map['shortener_key'])
    payload = {'longUrl': url}
    headers = {'content-type': 'application/json'}
    r = requests.post(post_url, data=json.dumps(payload), headers=headers)
    return r.json()['id']


def shortit(message):
    url_regex = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
    urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message)
    news = url_regex.sub('{URL}', message)
    urls.reverse()
    updated_message = ''
    for word in news.split(" "):
        if word == '{URL}':
            word = get_short_link(urls.pop())
        updated_message += word+' '
    return updated_message


def news_(bot, update):
    if (config_map['spamnews_news_chatid'] != 0 and update.message.chat_id == config_map['spamnews_news_chatid']):
        global news
        news = update.message.text.replace("/news ", "")
        news = update.message.text.replace("/news", "")
#		news = shortit(news)
        bot.sendMessage(chat_id=update.message.chat_id, text="News Aggiornata!")

def spamnews(bot, update):
    if (config_map['spamnews_news_chatid'] != 0 and update.message.chat_id == config_map['spamnews_news_chatid']):
        chat_ids = open('logs/chatid.txt', 'r').read()
        chat_ids = chat_ids.split("\n")
        list_chat_ids = chat_ids

        for chat_id in chat_ids:
            try:
                # This command is rarely used. Only for IMPORTANT news. It is right to spam in groups
                if not "+" in chat_id:
                    bot.sendMessage(chat_id=chat_id, text=news)
            except Unauthorized:
                logger.error('Unauthorized id. Trying to remove from the chat_id list...' + str(chat_id))
                list_chat_ids.remove(chat_id)
            except Exception as error:
                if "Group migrated to supergroup" in str(error):
                    logger.error(str(error) + " (" + str(chat_id) + ")")
                    new_chat_id = str(error).replace("Group migrated to supergroup. New chat id: ", "")
                    new_chat_id = new_chat_id.replace("\n", "")
                    list_chat_ids.remove(chat_id)
                    list_chat_ids.append(new_chat_id)
                else:
                    open("logs/errors.txt", "a+").write(str(error) + " " + str(chat_id)+"\n")

        list_chat_ids = '\n'.join(list_chat_ids)
        list_chat_ids = list_chat_ids.replace("\n\n", "\n")
        open('logs/chatid.txt', 'w').write(list_chat_ids)

        spam_channel(bot, news)

        bot.sendMessage(chat_id=update.message.chat_id, text="News spammata!")


def disablenews(bot, update):
    check_log(bot, update, "disablenews")

    chat_ids = open('logs/chatid.txt', 'r').read()
    chat_id = update.message.chat_id

    if not ("+"+str(chat_id)) in chat_ids:
        chat_ids = chat_ids.replace(str(chat_id), "+"+str(chat_id))
        message_test = "News disabilitate!"
        open('logs/chatid.txt', 'w').write(chat_ids)
    else:
        message_test = "News già disabilitate!"

    bot.sendMessage(chat_id=update.message.chat_id, text=message_test)


def enablenews(bot, update):
    check_log(bot, update, "enablenews")

    chat_ids = open('logs/chatid.txt', 'r').read()
    chat_id = update.message.chat_id

    if ("+"+str(chat_id)) in chat_ids:
        chat_ids = chat_ids.replace("+"+str(chat_id), str(chat_id))
        message_text = "News abilitate!"
        open('logs/chatid.txt', 'w').write(chat_ids)
    else:
        message_text = "News già abilitate!"

    bot.sendMessage(chat_id=update.message.chat_id, text=message_text)


def stats_gen(bot, update, days):
    conn = sqlite3.connect('data/DMI_DB.db')
    chat_id = update.message.chat_id
    query = ""
    text = ""

    if days == 0:
        text += "Record Globale:\n"
        query = "SELECT Type, count(chat_id) FROM stat_list GROUP BY Type ORDER BY Type;"
    else:
        text += "Record di "+str(days)+" giorni:\n"
        query = "SELECT Type, count(chat_id) FROM stat_list WHERE DateCommand > '"+ str(date.today()-timedelta(days=days)) + "' GROUP BY Type ORDER BY Type;"

    for row in conn.execute(query):
        if str(row[0]) != "leiCheNePensaSignorina" and str(row[0]) != "smonta_portoni" and str(row[0]) != "santino" and str(row[0]) != "bladrim" and str(row[0]) != "prof_sticker":
            text += str(row[1]) + ": " + str(row[0]) + "\n"
    bot.sendMessage(chat_id=chat_id, text=text)
    conn.close()

def stats(bot, update):
    if(len(update['message']['text'].split(' ')) == 2):
        days = int(update['message']['text'].split(' ')[1])
        if(days <= 0):
            days = 30
    else:
        days = 30
    stats_gen(bot, update, days)


def stats_tot(bot, update):
    stats_gen(bot, update, 0)


def check_log(bot, update, type, callback=0):
    if callback:
        update = update.callback_query

    chat_id = update.message.chat_id
    if (config_map['debug']['disable_db'] == 0):
        today = str(date.today())
        conn = sqlite3.connect('data/DMI_DB.db')
        conn.execute("INSERT INTO stat_list VALUES ('"+ str(type) + "',"+str(chat_id)+",'"+str(today)+" ')")
        conn.commit()
        conn.close()

    if (config_map['debug']['disable_chatid_logs'] == 0):
        a_log = open("logs/chatid.txt", "a+")
        r_log = open("logs/chatid.txt", "r+")
        if not str(chat_id) in r_log.read():
            a_log.write(str(chat_id)+"\n")


def give_chat_id(bot, update):
    update.message.reply_text(str(update.message.chat_id))


def send_log(bot, update):
    if(config_map['dev_group_chatid'] != 0 and update.message.chat_id == config_map['dev_group_chatid']):
        bot.sendDocument(chat_id=config_map['dev_group_chatid'], document=open('logs/logs.txt', 'rb'))


def send_chat_ids(bot, update):
    if(config_map['dev_group_chatid'] != 0 and update.message.chat_id == config_map['dev_group_chatid']):
        bot.sendDocument(chat_id=config_map['dev_group_chatid'], document=open('logs/chatid.txt', 'rb'))


def send_errors(bot, update):
    if(config_map['dev_group_chatid'] != 0 and update.message.chat_id == config_map['dev_group_chatid']):
        bot.sendDocument(chat_id=config_map['dev_group_chatid'], document=open('logs/errors.txt', 'rb'))


def spam_channel(bot, message):
    try:
        bot.sendMessage(chat_id=config_map['news_channel'], text=message, parse_mode='HTML')
    except Exception as error:
        open("logs/errors.txt", "a+").write("{} {}\n".format(error, config_map['news_channel']))


def avviso(bot, job):
    scrape_notices()

    if os.path.isfile("data/avviso.dat"):
        testo = open("data/avviso.dat").read()
        if testo != "":
            chat_ids = open("logs/chatid.txt", "r").read()
            chat_ids = chat_ids.split("\n")
            for chat_id in chat_ids:
                try:
                    # Ignore chat_id with disabled news. Ignore chat_id groups.
                    if not chat_id.startswith(("+", "-")):
                        bot.sendMessage(chat_id=chat_id, text=testo, parse_mode='HTML')
                except Exception as error:
                    open("logs/errors.txt", "a+").write(str(error) + " " + str(chat_id)+"\n")

            spam_channel(bot, testo)

        os.remove("data/avviso.dat")


def updater_lep(bot, job):
    scrape_lessons()
    scrape_exams()
    scrape_prof()


def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text="Benvenuto! Questo bot è stato realizzato dagli studenti del Corso di Laurea in Informatica al fine di suppotare gli studenti del DMI! Per scoprire cosa puoi fare usa /help")


def mensa_cmd(bot, update):
    check_log(bot, update, "mensa")
    mensa(bot, update)


def mensa_plus_cmd(bot, update):
    check_log(bot, update, "mensa_plus")
    mensa_plus(bot, update)


def newscommand(bot, update):
    check_log(bot, update, "avvisi")
    global news
    if news == "":
        bot.sendMessage(chat_id=update.message.chat_id, text="Non ho nulla da mostrarti.")
    else:
        bot.sendMessage(chat_id=update.message.chat_id, text=news)


def git(bot, update):
    check_log(bot, update, "gitlab")

    chat_id = update.message.chat_id
    executed_command = update.message.text.split(' ')[0]

    if chat_id < 0:
        bot.sendMessage(chat_id=chat_id, text="❗️ La funzione %s non è ammessa nei gruppi" % executed_command)
    else:
        db = sqlite3.connect('data/DMI_DB.db')

        if db.execute("SELECT Chat_id FROM 'Chat_id_List' WHERE Chat_id = %s" % chat_id).fetchone():
            gitlab_handler(bot, update)
        else:
            bot.sendMessage(chat_id=chat_id, text="🔒 Non hai i permessi per utilizzare la funzione %s\nUtilizzare il comando /request <nome> <cognome> <e-mail> (il nome e il cognome devono essere scritti uniti Es: Di Mauro -> DiMauro)" % executed_command)

        db.close()

def report(bot, update, args):
    check_log(bot, update, "report")
    chat_id = update.message.chat_id
    chat_username = update.message.from_user.username
    executed_command = update.message.text.split(' ')[0]


    if chat_id < 0:
        bot.sendMessage(chat_id=chat_id, text="! La funzione %s non è ammessa nei gruppi" % executed_command)
    elif not chat_username:
        bot.sendMessage(chat_id=chat_id, text="La funzione %s non è ammessa se non si dispone di un username." % executed_command)
    else:
        if  args:
            db = sqlite3.connect('data/DMI_DB.db')
            message = "⚠️Segnalazione⚠️\n"
            if db.execute("SELECT Chat_id FROM 'Chat_id_List' WHERE Chat_id = %s" %chat_id).fetchone():
                name = db.execute("SELECT Username,Nome,Cognome FROM 'Chat_id_List' WHERE Chat_id = %s" %chat_id)
                row = name.fetchone()

                message += "Username: @" + row[1] + "\n" + "Nome: " + row[2] + "\n" + "Cognome: " + row[3] + "\n" + " ".join(args)
                bot.sendMessage(chat_id = config_map['representatives_group'], text = message)
                bot.sendMessage(chat_id = chat_id, text = "Resoconto segnalazione: \n" + message + "\n Grazie per la segnalazione, un rappresentante ti contatterà nel minor tempo possibile.")

                db.close()
            else:
                bot.sendMessage(chat_id=chat_id, text="🔒 Non hai i permessi per utilizzare la funzione %s\nUtilizzare il comando /request <nome> <cognome> <e-mail> (il nome e il cognome devono essere scritti uniti Es: Di Mauro -> DiMauro)" % executed_command)

        else:
            bot.sendMessage(chat_id = chat_id, text="Errore. Inserisci la tua segnalazione dopo /report (Ad esempio /report Invasione ingegneri in corso.)")
