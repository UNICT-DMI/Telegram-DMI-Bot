# -*- coding: utf-8 -*-

# Telegram
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot, ParseMode, InputMediaPhoto
from telegram.ext import Updater, Filters, MessageHandler, CommandHandler, CallbackQueryHandler, RegexHandler, CallbackContext
from telegram.error import (TelegramError, Unauthorized, BadRequest, TimedOut, ChatMigrated, NetworkError)

# Drive
from pydrive.drive import GoogleDrive
from pydrive.auth import GoogleAuth

# Custom classes
from classes.StringParser import StringParser

# System libraries
from datetime import date, datetime, timedelta
import json
import re
import random
import os
import sys
import requests
import sqlite3
import logging
import pytz
from urllib.request import urlopen
from bs4 import BeautifulSoup
import dryscrape
import time
import pandas as pd
import calendar
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

from module.shared import read_md, check_log, config_map
from module.lezioni import lezioni_cmd
from module.esami import esami_cmd
from module.professori import prof_cmd
from module.scraper_exams import scrape_exams
from module.scraper_lessons import scrape_lessons
from module.scraper_professors import scrape_prof
from module.scraper_notices import scrape_notices
from module.gitlab import gitlab_handler
from module.easter_egg_func import *
from module.regolamento_didattico import *
from module.utils.keyboard_utils import get_help_keyboard
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# Token of your telegram bot that you created from @BotFather, write it on settings.yml
TOKEN = config_map["token"]

def send_message(update: Update, context: CallbackContext, messaggio):
    chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id #prova a prendere il chat_id da update.message, altrimenti prova da update.callback_query.message
    msg = ""
    righe = messaggio.split('\n')
    for riga in righe:
        if riga.strip() == "" and len(msg) > 3000:
            try:
                context.bot.sendMessage(chat_id=chat_id, text=msg, parse_mode='Markdown')
                msg = ""
            except:
                logger.error("in: functions.py - send_message: the message is badly formatted")
        else:
            msg += riga + "\n"
    context.bot.sendMessage(chat_id=chat_id, text=msg, parse_mode='Markdown')


def lezioni(update: Update, context: CallbackContext, *m):
    check_log(update, context, "lezioni")
    message_text = lezioni_cmd(update, context, context.args)
    context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text, parse_mode='Markdown')


def get_esami_text_InlineKeyboard(context: CallbackContext) -> (str, InlineKeyboardMarkup): #restituisce una tuple formata da (message_text, InlineKeyboardMarkup)
    keyboard = [[]]

    esami_user_data = context.user_data['esami']
    text_anno = ", ".join([key for key in esami_user_data if "anno" in key]) #stringa contenente gli anni per cui la flag è true
    text_sessione = ", ".join([key for key in esami_user_data if "sessione" in key]).replace("sessione", "") #stringa contenente le sessioni per cui la flag è true
    text_insegnamento = esami_user_data.get("insegnamento", "") #stringa contenente l'insegnamento

    message_text = "Anno: {}\nSessione: {}\nInsegnamento: {}"\
        .format(text_anno if text_anno else "tutti",\
                text_sessione if text_sessione else "tutti",\
                text_insegnamento if text_insegnamento else "tutti")
    keyboard.append([InlineKeyboardButton(" ~ Personalizza la ricerca ~ ", callback_data="_div")])
    keyboard.append(
            [
                InlineKeyboardButton(" Anno ", callback_data="sm_esami_button_anno"),
                InlineKeyboardButton(" Sessione ", callback_data="sm_esami_button_sessione"),
            ]
        )
    keyboard.append(
            [
                InlineKeyboardButton(" Insegnamento ", callback_data="sm_esami_button_insegnamento"),
                InlineKeyboardButton(" Cerca ", callback_data="esami_button_search")
            ]
        )

    return message_text, InlineKeyboardMarkup(keyboard)


def esami(update: Update, context: CallbackContext):
    check_log(update, context, "esami")
    if 'esami' in context.user_data: context.user_data['esami'].clear() #ripulisce il dict dell'user relativo al comando /esami da eventuali dati presenti
    else: context.user_data['esami'] = {} #crea il dict che conterrà i dati del comando /esami all'interno della key ['esami'] di user data

    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    if chat_id != user_id: # forza ad eseguire il comando in una chat privata, anche per evitare di inondare un gruppo con i risultati
        context.bot.sendMessage(chat_id=chat_id, text="Questo comando è utilizzabile solo in privato")
        context.bot.sendMessage(chat_id=user_id, text="Dal comando esami che hai eseguito in un gruppo")

    message_text, inline_keyboard = get_esami_text_InlineKeyboard(context)
    context.bot.sendMessage(chat_id=user_id, text=message_text, reply_markup=inline_keyboard)



def esami_input_insegnamento(update: Update, context: CallbackContext):
    if context.user_data['esami'].get('cmd', 'null') == "input_insegnamento": #se effettivamente l'user aveva richiesto di modificare l'insegnamento...
        check_log(update, context, "esami_input_insegnamento")
        context.user_data['esami']['insegnamento'] = re.sub(r"^(?!=<[/])[Ii]ns:\s+", "", update.message.text) #ottieni il nome dell'insegnamento e salvalo nel dict
        del context.user_data['esami']['cmd'] #elimina la possibilità di modificare l'insegnamento fino a quando l'apposito button non viene premuto di nuovo
        message_text, inline_keyboard = get_esami_text_InlineKeyboard(context)
        context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text, reply_markup=inline_keyboard)


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
    output += "👥 /rappresentanti - elenco dei rappresentanti del DMI\n"
    output += "📚 /biblioteca - orario biblioteca DMI\n"
    output += CUSicon[random.randint(0, 5)] + " /cus sede e contatti\n"
    output += "  /cloud - linka le cartelle condivise su cloud\n\n"
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
    output += "/contributors"
    output += "/regolamentodidattico"
    return output


def informative_callback(update: Update, context: CallbackContext):
     # controllo per poter gestire i comandi (/comando) e i messaggi inviati premendo i bottoni (❔ Help)
    if update.message.text[0] == '/':
        cmd = update.message.text.split(' ')[0][1:] #prende solo la prima parola del messaggio (cioè il comando) escludendo lo slash
    else:
        cmd = update.message.text.split(' ')[1].lower() # prende la prima parola dopo l'emoji
    check_log(update, context, cmd)
    message_text = read_md(cmd)
    context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text, parse_mode='Markdown')


def exit_cmd():
    output = "."
    return output


def esami_button():
    output = "Scrivi /esami inserendo almeno uno dei seguenti parametri: giorno, materia, sessione (prima, seconda, terza, straordinaria)"
    return output

def lezioni_button():
    output = "Scrivi /lezioni inserendo almeno uno dei seguenti parametri: giorno, materia"
    return output

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


def help(update: Update, context: CallbackContext):
    check_log(update, context, "help")
    chat_id = update.message.chat_id
    keyboard = [[]]
    message_text = "@DMI_Bot risponde ai seguenti comandi:"

    keyboard.append([InlineKeyboardButton(" ~ Dipartimento e CdL ~ ", callback_data="_div")])

    keyboard.append(
        [
            InlineKeyboardButton("📖 Esami (link)",        callback_data="md_esami_link"),
            InlineKeyboardButton("🗓 Aulario",              callback_data="sm_aulario"),
            InlineKeyboardButton("Orari lezioni (link)",    callback_data="md_lezioni_link")
        ]
    )

    keyboard.append(
        [InlineKeyboardButton("Regolamento Didattico", callback_data="regolamentodidattico_button")]
    )

    keyboard.append(
        [
            InlineKeyboardButton("👥 Rappresentanti",                       callback_data="sm_rapp_menu"),
            InlineKeyboardButton("📚 Biblioteca",                           callback_data="md_biblioteca"),
            InlineKeyboardButton(CUSicon[random.randint(0, 5)] + " CUS",    callback_data="md_cus"),
            InlineKeyboardButton("☁️ Cloud",                                 callback_data="md_cloud")
        ]
    )

    keyboard.append([InlineKeyboardButton(" ~ Segreteria orari e contatti ~ ", callback_data="_div")])

    keyboard.append(
        [
            InlineKeyboardButton("Seg. Didattica",  callback_data="md_sdidattica"),
            InlineKeyboardButton("Seg. Studenti",   callback_data="md_sstudenti"),
            InlineKeyboardButton("CEA",             callback_data="md_cea")
        ]
    )

    keyboard.append([InlineKeyboardButton(" ~ ERSU orari e contatti ~ ", callback_data="_div")])

    keyboard.append(
        [
            InlineKeyboardButton("ERSU",          callback_data="md_ersu"),
            InlineKeyboardButton("Ufficio ERSU",  callback_data="md_ufficioersu"),
            InlineKeyboardButton("URP",           callback_data="md_urp")
        ]
    )

    keyboard.append([InlineKeyboardButton(" ~ Bot e varie ~ ", callback_data="_div")])

    keyboard.append(
        [
            InlineKeyboardButton("📂 Drive",     callback_data="md_drive"),
            InlineKeyboardButton("📂 GitLab",    callback_data="md_gitlab"),
            InlineKeyboardButton("Contributors", callback_data="md_contributors"),
        ]
    )

    keyboard.append(
        [
            InlineKeyboardButton("Tutti i comandi", callback_data="help_cmd"),
            InlineKeyboardButton("Chiudi",          callback_data="exit_cmd")
        ]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.sendMessage(chat_id=chat_id, text=message_text, reply_markup=reply_markup)


def rapp_menu(update: Update, context: CallbackContext, chat_id, message_id):
    keyboard = [[]]
    message_text = "Quali rappresentanti vuoi contattare?"

    keyboard.append(
        [
            InlineKeyboardButton("Rapp. DMI",         callback_data="md_rappresentanti_dmi"),
            InlineKeyboardButton("Rapp. Informatica", callback_data="md_rappresentanti_informatica"),
            InlineKeyboardButton("Rapp. Matematica",  callback_data="md_rappresentanti_matematica"),
        ]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)


def prof(update: Update, context: CallbackContext):
    check_log(update, context, "prof")
    message_text = prof_cmd(context.args)
    if len(message_text) > 4096:
        send_message(update, context, message_text)
    else:
        context.bot.sendMessage(chat_id=update.message.chat_id, text=message_text, parse_mode='Markdown')


def stats_gen(update: Update, context: CallbackContext, days):
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
    context.bot.sendMessage(chat_id=chat_id, text=text)
    conn.close()

def stats(update: Update, context: CallbackContext):
    if(len(update['message']['text'].split(' ')) == 2):
        days = int(update['message']['text'].split(' ')[1])
        if(days <= 0):
            days = 30
    else:
        days = 30
    stats_gen(update, context, days)

def stats_tot(update: Update, context: CallbackContext):
    stats_gen(update, context, 0)

def give_chat_id(update: Update, context: CallbackContext):
    update.message.reply_text(str(update.message.chat_id))


def send_log(update: Update, context: CallbackContext):
    if(config_map['dev_group_chatid'] != 0 and update.message.chat_id == config_map['dev_group_chatid']):
        context.bot.sendDocument(chat_id=config_map['dev_group_chatid'], document=open('logs/logs.txt', 'rb'))


def send_chat_ids(update: Update, context: CallbackContext):
    if(config_map['dev_group_chatid'] != 0 and update.message.chat_id == config_map['dev_group_chatid']):
        context.bot.sendDocument(chat_id=config_map['dev_group_chatid'], document=open('logs/chatid.txt', 'rb'))


def send_errors(update: Update, context: CallbackContext):
    if(config_map['dev_group_chatid'] != 0 and update.message.chat_id == config_map['dev_group_chatid']):
        context.bot.sendDocument(chat_id=config_map['dev_group_chatid'], document=open('logs/errors.txt', 'rb'))

def updater_lep(context):
    year_exam = get_year_code(11 , 30) # aaaa/12/01 (cambio nuovo anno esami) data dal quale esami del vecchio a nuovo anno coesistono
    scrape_exams("1" + str(year_exam), delete= True) # flag che permette di eliminare tutti gli esami presenti in tabella exams
    if(check_print_old_exams(year_exam)):
        scrape_exams("1" + str(int(year_exam) - 1))
    scrape_lessons("1" + str(get_year_code(9 , 20))) # aaaa/09/21 (cambio nuovo anno lezioni) data dal quale vengono prelevate le lezioni del nuovo anno
    scrape_prof()

def check_print_old_exams(year_exam):
    date_time = get_current_date()
    ckdate = get_checkdate(date_time.year, 12, 23) # aaaa/12/24 data dal quale vengono prelevati solo gli esami del nuovo anno
    if((year_exam != str(date_time.year)[-2:]) and date_time < ckdate):
        return True
    return False

def get_checkdate(year, month, day):
    tz = pytz.timezone('Europe/Rome')
    checkdate = datetime(year= year, month= month, day= day)
    checkdate = tz.localize(checkdate)
    return checkdate

def get_current_date():
    tz = pytz.timezone('Europe/Rome')
    date_time = datetime.now(tz)
    return date_time

def get_year_code(month, day):
    date_time = get_current_date()
    check_new_year = get_checkdate(date_time.year, month, day)
    year = date_time.year
    if date_time > check_new_year:
        year = date_time.year + 1
    return str(year)[-2:]

def start(update: Update, context: CallbackContext):
    reply_keyboard = get_help_keyboard()
    message_text = read_md("start")
    context.bot.sendMessage(chat_id=update.message.chat_id,
                            text=message_text,
                            reply_markup=reply_keyboard)

def git(update: Update, context: CallbackContext):
    check_log(update, context, "gitlab")

    chat_id = update.message.chat_id
    executed_command = update.message.text.split(' ')[0]

    if chat_id < 0:
        context.bot.sendMessage(chat_id=chat_id, text="❗️ La funzione %s non è ammessa nei gruppi" % executed_command)
    else:
        db = sqlite3.connect('data/DMI_DB.db')

        if db.execute("SELECT Chat_id FROM 'Chat_id_List' WHERE Chat_id = %s" % chat_id).fetchone():
            gitlab_handler(update, context)
        else:
            context.bot.sendMessage(chat_id=chat_id, text="🔒 Non hai i permessi per utilizzare la funzione %s\nUtilizzare il comando /request <nome> <cognome> <e-mail> (il nome e il cognome devono essere scritti uniti Es: Di Mauro -> DiMauro)" % executed_command)

        db.close()

def report(update: Update, context: CallbackContext):
    check_log(update, context, "report")
    chat_id = update.message.chat_id
    chat_username = update.message.from_user.username
    executed_command = update.message.text.split(' ')[0]


    if chat_id < 0:
        context.bot.sendMessage(chat_id=chat_id, text="! La funzione %s non è ammessa nei gruppi" % executed_command)
    elif not chat_username:
        context.bot.sendMessage(chat_id=chat_id, text="La funzione %s non è ammessa se non si dispone di un username." % executed_command)
    else:
        if  context.args:
            db = sqlite3.connect('data/DMI_DB.db')
            message = "⚠️Segnalazione⚠️\n"
            if db.execute("SELECT Chat_id FROM 'Chat_id_List' WHERE Chat_id = %s" %chat_id).fetchone():
                name = db.execute("SELECT Username,Nome,Cognome FROM 'Chat_id_List' WHERE Chat_id = %s" %chat_id)
                row = name.fetchone()

                if row[0] is None:
                    message += "Nome: " + row[1] + "\n" + "Cognome: " + row[2] + "\n" + " ".join(context.args)
                else:
                    message += "Username: @" + row[0] + "\n" + "Nome: " + row[1] + "\n" + "Cognome: " + row[2] + "\n" + " ".join(context.args)
                context.bot.sendMessage(chat_id = config_map['representatives_group'], text = message)
                context.bot.sendMessage(chat_id = chat_id, text = "Resoconto segnalazione: \n" + message + "\n Grazie per la segnalazione, un rappresentante ti contatterà nel minor tempo possibile.")

                db.close()
            else:
                context.bot.sendMessage(chat_id=chat_id, text="🔒 Non hai i permessi per utilizzare la funzione %s\nUtilizzare il comando /request <nome> <cognome> <e-mail> (il nome e il cognome devono essere scritti uniti Es: Di Mauro -> DiMauro)" % executed_command)

        else:
            context.bot.sendMessage(chat_id = chat_id, text="Errore. Inserisci la tua segnalazione dopo /report (Ad esempio /report Invasione ingegneri in corso.)")

def updater_schedule(context):
    session = dryscrape.Session()
    aulario_url = read_md("aulario")
    session.visit(aulario_url)
    time.sleep(0.5)

    response = session.body()
    soup = BeautifulSoup(response,'lxml')

    tables = pd.read_html(response)
    print("Schedule loaded")
    days = {}
    for k,table in enumerate(tables):
        rooms = table.iloc[:,0]
        schedule = table.iloc[:,1:]
        subjects = {}
        for c in schedule:
            for i,row in enumerate(table[c]):
                if not pd.isnull(row):
                    r = row[:20] + rooms[i]
                    if not r in subjects:
                        subjects[r] = {}

                        subjects[r]["subj"] = row.replace('[]','').replace('[','(').replace(']',')')
                        subjects[r]["times"] = []
                        subjects[r]['room'] = rooms[i]
                    if c[-1] == "1":
                        c = c[:3] + "30"
                    subjects[r]['times'].append(c)
        days[k] = subjects
    with open("data/json/subjs.json", "w+") as outfile:
        json.dump(days, outfile)

def get_json(file):
    try:
        json_file = open('data/json/{0}.json'.format(file),'r')
    except:
        logger.error("subjs.json still does not exist")
        return False
    return json.load(json_file)

def create_calendar(days,year=None,month=None):
    today = date.today()
    if year == None:
        year = today.year
    if month == None:
        month = today.month
    keyboard = []
    keyboard.append([InlineKeyboardButton("🗓 {0} {1}".format(calendar.month_name[month],str(year)),callback_data = "NULL")])
    week = ['L','M','M','G','V','S','D']
    row = []
    for w in week:
        row.append(InlineKeyboardButton(w,callback_data = "NULL"))
    keyboard.append(row)
    my_cal = calendar.monthcalendar(year,month)
    diff = 0
    for week in my_cal:
        row = []
        empty = True
        for day in week:
            if day < today.day and (day == 0 or month == today.month) :
                row.append(InlineKeyboardButton(" ",callback_data = "NULL"))
            else:
                curr = date(year,month,day)
                diff = (curr - today).days
                if diff < days:
                    empty = False
                    row.append(InlineKeyboardButton(str(day),callback_data = "cal_{0}".format(diff)))
                else:
                    row.append(InlineKeyboardButton(" ",callback_data = "NULL"))
        if not empty:
            keyboard.append(row)
    row = []
    if today.month < month or today.year < year:
        row.append(InlineKeyboardButton("◀️ {0}".format(calendar.month_name[((month-2)%12)+1]),callback_data="m_p_{0}_{1}_{2}".format(year,month,days)))
    if diff < days:
        row.append(InlineKeyboardButton("{0} ▶️".format(calendar.month_name[((month)%12)+1]),callback_data="m_n_{0}_{1}_{2}".format(year,month,days)))
    keyboard.append(row)
    return(InlineKeyboardMarkup(keyboard))


def aulario(update: Update, context: CallbackContext, chat_id=None, message_id=None):
    if not chat_id:
        chat_id = update.message.chat_id
    json_data = get_json("subjs")
    keys =  [k for k in json_data.keys()]
    reply_markup = create_calendar(len(keys))
    text = "Seleziona la data della lezione che ti interessa."
    if message_id:
        context.bot.editMessageText(text = text, reply_markup = reply_markup , chat_id = chat_id, message_id = message_id)
    else:
        context.bot.sendMessage(text = text, reply_markup = reply_markup , chat_id = chat_id)

def aulario_subj(update: Update, context: CallbackContext, chat_id, message_id, day):
    json_data = get_json("subjs")
    if json_data[day]:
        text = "Quale lezione devi seguire?"
        keyboard = get_subjs_keyboard(0,day,json_data)
        keyboard.append([InlineKeyboardButton('Indietro ❌', callback_data = 'sm_aulario')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        context.bot.deleteMessage(chat_id = chat_id,  message_id = message_id)
        context.bot.sendMessage(text = text, reply_markup = reply_markup, chat_id = chat_id)
    elif json_data[day] == {}:
        text = "Nessuna lezione programmata per questo giorno"
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Indietro ❌', callback_data = 'sm_aulario')]])
        context.bot.deleteMessage(chat_id = chat_id,  message_id = message_id)
        context.bot.sendMessage(text = text, reply_markup = reply_markup, chat_id = chat_id)

def get_subjs_keyboard(page,day,data):
    keyboard = []
    keys = data[day]
    subjs = [k for k in keys]
    t_subjs = subjs
    if day == '0':
        t_subjs = []
        for s in subjs:
            t = keys[s]['times'][-1]
            h = t.split(':')[0]
            m = t.split(':')[1]
            now = datetime.now()
            last = now.replace(hour = int(h), minute = int(m), second = 0, microsecond = 0)
            if now < last:
                t_subjs.append(s)
    for s in t_subjs[page*5:(page*5)+5]:
        keyboard.append([InlineKeyboardButton(data[day][s]["subj"],callback_data = 'sb_{0}_{1}'.format(day,s))])
    arrows = []
    if page != 0:
        arrows.append(InlineKeyboardButton('◀️',callback_data = 'pg_{0}_{1}_l'.format(day,page)))
    if len(t_subjs) > page*5+5:
        arrows.append(InlineKeyboardButton('▶️',callback_data = 'pg_{0}_{1}_r'.format(day,page)))
    keyboard.append(arrows)
    return keyboard
# Callback Query Handlers

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
    check_log(update, context, data, 1)

    context.bot.editMessageText(
      text=message_text,
      chat_id=query.message.chat_id,
      message_id=query.message.message_id,
      parse_mode=ParseMode.MARKDOWN
    )


def esami_handler(update: Update, context: CallbackContext):
    callbackData = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    esami_user_data = context.user_data['esami']
    if "anno" in callbackData:
        if callbackData[-7:] not in esami_user_data.keys(): #se non era presente, setta la key di [1° anno|2° anno| 3° anno] a true...
            esami_user_data[callbackData[-7:]] = True
        else:
           del esami_user_data[callbackData[-7:]] #... o elmina la key se era già presente
    elif "sessione" in callbackData:
        if 'sessione' + callbackData[22:] not in esami_user_data.keys(): #se non era presente, setta la key di sessione[prima|seconda|terza] a true...
            esami_user_data['sessione' + callbackData[22:]] = True
        else:
           del esami_user_data['sessione' + callbackData[22:]] #... o elmina la key se era già presente
    elif "search" in callbackData:
        message_text = esami_cmd(esami_user_data) #ottieni il risultato della query che soddisfa le richieste
        context.bot.editMessageText(chat_id=chat_id, message_id=message_id, text=update.callback_query.message.text) #rimuovi la inline keyboard e lascia il resoconto della query
        send_message(update, context, message_text) #manda il risutato della query suddividendo la stringa in più messaggi
        esami_user_data.clear() #ripulisci il dict
        return
    else:
        logger.error("esami_handler: an error has occurred")

    message_text, inline_keyboard = get_esami_text_InlineKeyboard(context)
    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=inline_keyboard)


def esami_button_sessione(update: Update, context: CallbackContext, chat_id, message_id):
    keyboard = [[]]
    message_text = "Seleziona la sessione che ti interessa"

    keyboard.append(
        [
            InlineKeyboardButton("prima", callback_data="esami_button_sessione_prima"),
            InlineKeyboardButton("seconda", callback_data="esami_button_sessione_seconda"),
        ]
    )
    keyboard.append(
        [
            InlineKeyboardButton("terza", callback_data="esami_button_sessione_terza"),
            InlineKeyboardButton("straordinaria", callback_data="esami_button_sessione_straordinaria"),
        ]
    )

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=InlineKeyboardMarkup(keyboard))


def esami_button_insegnamento(update: Update, context: CallbackContext, chat_id, message_id):
    context.user_data['esami']['cmd'] = "input_insegnamento" #è in attesa di un messaggio nel formato corretto che imposti il valore del campo insegnamento
    message_text = "Inserire l'insegnamento desiderato nel formato:\n" + \
                   "ins: nome insegnamento\n" + \
                   "Esempio:\n" +\
                   "ins: SisTeMi oPeRaTIvI"

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id)


def esami_button_anno(update: Update, context: CallbackContext, chat_id, message_id):
    keyboard = [[]]
    message_text = "Seleziona l'anno che ti interessa"

    keyboard.append(
        [
            InlineKeyboardButton("1° anno", callback_data="esami_button_anno_1° anno"),
            InlineKeyboardButton("2° anno", callback_data="esami_button_anno_2° anno"),
            InlineKeyboardButton("3° anno", callback_data="esami_button_anno_3° anno"),
        ]
    )

    context.bot.editMessageText(text=message_text, chat_id=chat_id, message_id=message_id, reply_markup=InlineKeyboardMarkup(keyboard))

def calendar_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    day = data.split("_")[1]
    aulario_subj(update,context,chat_id,message_id,day)


def month_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    d = data.split("_")
    direction = d[1]
    year = int(d[2])
    month = int(d[3])
    days = int(d[4])
    if direction == 'n':
        if month < 12:
            month += 1
        else:
            month = 1
            year += 1
    elif direction == 'p':
        if month > 1:
            month -= 1
        else:
            month = 12
            year -= 1

    context.bot.editMessageReplyMarkup(reply_markup = create_calendar(days,year,month), chat_id = chat_id, message_id = message_id)


def subjects_arrow_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    day = data.split('_')[1]
    page = int(data.split('_')[2])
    arrows = []
    json_data = get_json("subjs")
    keys = json_data[day]
    subjs = [k for k in keys]
    if data[-1] == 'r':
        page+=1
    elif data[-1] == 'l':
        page-=1
    keyboard = get_subjs_keyboard(page,day,json_data)
    keyboard.append(arrows)
    keyboard.append([InlineKeyboardButton('Indietro ❌', callback_data = 'sm_aulario')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.editMessageReplyMarkup(chat_id = query.message.chat_id,message_id=query.message.message_id,reply_markup = reply_markup)

def subjects_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    json_data = get_json("subjs")
    d = data.split("_")
    day = d[1]
    s = d[2]
    hours = json_data[day][s]['times']
    start = hours[0]
    end = hours[-1]
    if end[3:] == '30':
        end = "{0}:00".format(int(end[:2])+1)
    else:
        end = end[:3]+'30'
    h = "{0} - {1}".format(start,end)
    room = json_data[day][s]['room']
    sub = json_data[day][s]['subj']
    text = "{0} Ore: {1}: {2}".format(sub,h,room)
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Indietro ❌', callback_data = 'sm&aulario_subj&{0}'.format(day))]])
    photo = create_map(sub,h,room)
    context.bot.deleteMessage(chat_id = chat_id,message_id = message_id)
    if not photo:
        context.bot.sendMessage(text = text, reply_markup = reply_markup, chat_id = chat_id)
    else:
        context.bot.sendPhoto(photo = photo, reply_markup = reply_markup, chat_id = chat_id)

def create_map(sub,h,room):
    data = get_json("room_coordinates")
    if room in data:
        b1_path = 'data/img/mappa.jpg'
        b1_img = Image.open(b1_path)
        draw = ImageDraw.Draw(b1_img)
        font = ImageFont.truetype("data/fonts/arial.ttf",30)
        draw.text((30,860),"{0} Ore: {1}: ".format(sub,h),fill = 'black', font = font)
        coord = data[room]
        x = coord[0]
        y = coord[1]
        w = coord[2]
        z = coord[3]
        draw.rectangle((x, y, w, z), outline ='red', width = 5)
        bio = BytesIO()
        bio.name = 'image.jpeg'
        b1_img.save(bio, 'JPEG')
        bio.seek(0)
        return bio
    else:
        return None

def submenu_with_args_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    func_name = data.split('&')[1]
    arg = data.split('&')[2]
    globals()[func_name](
      query,
      context,
      query.message.chat_id,
      query.message.message_id,
      arg
    )
