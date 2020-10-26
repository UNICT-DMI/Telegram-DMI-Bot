# Telegram
from telegram import Update
from telegram.ext import CallbackContext

# System libraries
import sqlite3
from datetime import date, timedelta

def stats(update: Update, context: CallbackContext):
    if(len(update['message']['text'].split(' ')) == 2):
        days = int(update['message']['text'].split(' ')[1])
        if(days <= 0):
            days = 30
    else:
        days = 30
    stats_gen(update, context, days)

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

def stats_tot(update: Update, context: CallbackContext):
    stats_gen(update, context, 0)