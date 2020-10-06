import sqlite3
import yaml

from telegram import Update
from telegram.ext import CallbackContext
from datetime import date, datetime

# config
with open('config/settings.yaml', 'r') as yaml_config:
    config_map = yaml.load(yaml_config, Loader=yaml.SafeLoader)

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
        conn.execute("INSERT INTO stat_list VALUES (?, ?, ?)", (str(type), str(chat_id), str(today)))
        conn.commit()
        conn.close()

    if (config_map['debug']['disable_chatid_logs'] == 0):
        a_log = open("logs/chatid.txt", "a+")
        r_log = open("logs/chatid.txt", "r+")
        if not str(chat_id) in r_log.read():
            a_log.write(str(chat_id)+"\n")