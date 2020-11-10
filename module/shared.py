
from telegram import Update
from telegram.ext import CallbackContext
from datetime import date, datetime

import sqlite3
import yaml
import logging
import pytz

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# config
with open('config/settings.yaml', 'r') as yaml_config:
    config_map = yaml.load(yaml_config, Loader=yaml.SafeLoader)


# Token of your telegram bot that you created from @BotFather, write it on settings.yml
TOKEN = config_map["token"]

# Icons
CUSicon = {0: "🏋",
           1: "⚽️",
           2: "🏀",
           3: "🏈",
           4: "🏐",
           5: "🏊",
           }

# keyboard menu
HELP = "❔ Help"
AULARIO = "📆 Aulario"
CLOUD = "☁️ Cloud"
SEGNALAZIONE = "📫 Segnalazione Rappresentanti"

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

def read_md(namefile):
    in_file = open("data/markdown/" + namefile + ".md", "r", encoding="utf8")
    text = in_file.read()
    in_file.close()
    return text

def check_log(update: Update, context: CallbackContext, type, callback=0):
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

def give_chat_id(update: Update, context: CallbackContext):
    update.message.reply_text(str(update.message.chat_id))

def get_year_code(month, day):
    date_time = get_current_date()
    check_new_year = get_checkdate(date_time.year, month, day)
    year = date_time.year
    if date_time > check_new_year:
        year = date_time.year + 1
    return str(year)[-2:]

def get_current_date():
    tz = pytz.timezone('Europe/Rome')
    date_time = datetime.now(tz)
    return date_time

def get_checkdate(year, month, day):
    tz = pytz.timezone('Europe/Rome')
    checkdate = datetime(year= year, month= month, day= day)
    checkdate = tz.localize(checkdate)
    return checkdate

def check_print_old_exams(year_exam):
    date_time = get_current_date()
    ckdate = get_checkdate(date_time.year, 12, 23) # aaaa/12/24 data dal quale vengono prelevati solo gli esami del nuovo anno
    if((year_exam != str(date_time.year)[-2:]) and date_time < ckdate):
        return True
    return False